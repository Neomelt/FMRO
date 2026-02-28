from __future__ import annotations

from pathlib import Path

import typer
from pydantic import ValidationError

from fmro_pc.config import CompaniesConfig, load_companies_config
from fmro_pc.crawl.runner import run_crawl
from fmro_pc.database import init_db, resolve_db_path, session_scope
from fmro_pc.parsers.registry import PARSER_REGISTRY, get_parser
from fmro_pc.storage.repository import export_jobs_csv, list_jobs

app = typer.Typer(help="FMRO PC crawler", no_args_is_help=True)

sources_app = typer.Typer(help="Inspect or validate companies sources")
crawl_app = typer.Typer(help="Run crawling pipeline")
jobs_app = typer.Typer(help="List stored jobs")
export_app = typer.Typer(help="Export jobs")
db_app = typer.Typer(help="Database helpers")

app.add_typer(sources_app, name="sources")
app.add_typer(crawl_app, name="crawl")
app.add_typer(jobs_app, name="jobs")
app.add_typer(export_app, name="export")
app.add_typer(db_app, name="db")


def _load_config_or_exit(path: Path) -> CompaniesConfig:
    try:
        return load_companies_config(path)
    except (FileNotFoundError, ValueError, ValidationError) as exc:
        typer.secho(f"Config error: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "..."


@db_app.command("init")
def db_init(
    db: Path = typer.Option(None, "--db", help="SQLite database path"),
) -> None:
    init_db(db)
    typer.echo(f"Database initialized at {resolve_db_path(db)}")


@sources_app.command("list")
def sources_list(
    config: Path = typer.Option(Path("companies.yaml"), "--config", help="Path to companies.yaml"),
    all_sources: bool = typer.Option(False, "--all", help="Include disabled sources"),
) -> None:
    cfg = _load_config_or_exit(config)
    sources = cfg.sources if all_sources else [source for source in cfg.sources if source.enabled]

    if not sources:
        typer.echo("No sources found.")
        return

    typer.echo("KEY                   ENABLED  PLATFORM      MODE     PARSER         URLS")
    for source in sources:
        typer.echo(
            f"{source.key:20} {str(source.enabled):7}  "
            f"{source.platform:12} {source.mode:8} {source.parser:14} {len(source.entry_urls)}"
        )


@sources_app.command("validate")
def sources_validate(
    config: Path = typer.Option(Path("companies.yaml"), "--config", help="Path to companies.yaml"),
) -> None:
    cfg = _load_config_or_exit(config)

    errors: list[str] = []
    for source in cfg.sources:
        try:
            get_parser(source.parser)
        except ValueError as exc:
            errors.append(f"[{source.key}] {exc}")

    if errors:
        typer.secho("Validation failed:", fg=typer.colors.RED)
        for error in errors:
            typer.echo(f"- {error}")
        raise typer.Exit(code=1)

    available_parsers = ", ".join(sorted(PARSER_REGISTRY))
    typer.secho(
        f"OK: {len(cfg.sources)} source(s) validated. Available parsers: {available_parsers}",
        fg=typer.colors.GREEN,
    )


@crawl_app.command("run")
def crawl_run(
    config: Path = typer.Option(Path("companies.yaml"), "--config", help="Path to companies.yaml"),
    db: Path = typer.Option(None, "--db", help="SQLite database path"),
    source: str | None = typer.Option(None, "--source", help="Single source key to crawl"),
    limit: int | None = typer.Option(None, "--limit", min=1, help="Max entry URLs per source"),
    dynamic: bool = typer.Option(
        False, "--dynamic", help="Force dynamic fetch mode for all sources"
    ),
) -> None:
    cfg = _load_config_or_exit(config)
    init_db(db)

    with session_scope(db) as session:
        summary = run_crawl(
            session,
            cfg,
            source_key=source,
            limit=limit,
            force_dynamic=dynamic,
        )

    typer.echo("Crawl run complete")
    typer.echo(f"- sources scanned: {summary.source_count}")
    typer.echo(f"- pages fetched: {summary.total_pages_fetched}")
    typer.echo(f"- jobs extracted: {summary.total_jobs_extracted}")
    typer.echo(f"- jobs normalized: {summary.total_jobs_normalized}")
    typer.echo(f"- jobs inserted: {summary.total_jobs_inserted}")
    typer.echo(f"- jobs updated: {summary.total_jobs_updated}")
    typer.echo(f"- jobs deactivated: {summary.total_jobs_deactivated}")
    typer.echo(f"- failures: {summary.total_failures}")

    for source_summary in summary.sources:
        typer.echo(
            f"  [{source_summary.source_key}] pages={source_summary.pages_fetched} "
            f"extracted={source_summary.jobs_extracted} "
            f"normalized={source_summary.jobs_normalized} "
            f"inserted={source_summary.upsert.inserted} updated={source_summary.upsert.updated} "
            f"deactivated={source_summary.upsert.deactivated} "
            f"dupes={source_summary.upsert.duplicates_skipped}"
        )
        for error in source_summary.errors:
            typer.echo(f"    ! {error}")


@jobs_app.command("list")
def jobs_list(
    db: Path = typer.Option(None, "--db", help="SQLite database path"),
    city: str | None = typer.Option(None, "--city", help="Filter by city substring"),
    keyword: str | None = typer.Option(
        None, "--keyword", help="Keyword in title/company/description"
    ),
    platform: str | None = typer.Option(None, "--platform", help="Filter by source platform"),
    include_inactive: bool = typer.Option(
        False, "--include-inactive", help="Show inactive jobs too"
    ),
    sort: str = typer.Option(
        "posted_at",
        "--sort",
        help="Sort field: posted_at,last_seen_at,updated_at,created_at,title,company",
    ),
    limit: int = typer.Option(50, "--limit", min=1),
) -> None:
    init_db(db)

    with session_scope(db) as session:
        try:
            rows = list_jobs(
                session,
                city=city,
                keyword=keyword,
                platform=platform,
                active_only=not include_inactive,
                sort=sort,
                limit=limit,
            )
        except ValueError as exc:
            typer.secho(str(exc), fg=typer.colors.RED)
            raise typer.Exit(code=1) from exc

    if not rows:
        typer.echo("No jobs found.")
        return

    typer.echo("ID  COMPANY         TITLE                    LOCATION     PLATFORM    UPDATED")
    for row in rows:
        updated = row.updated_at.date().isoformat() if row.updated_at else "-"
        typer.echo(
            f"{str(row.id):4} "
            f"{_truncate(row.company_name, 15):15} "
            f"{_truncate(row.title, 30):30} "
            f"{_truncate(row.location or '-', 15):15} "
            f"{_truncate(row.source_platform, 12):12} "
            f"{updated}"
        )


@export_app.command("csv")
def export_csv(
    out: Path = typer.Option(..., "--out", help="Output CSV path"),
    db: Path = typer.Option(None, "--db", help="SQLite database path"),
    city: str | None = typer.Option(None, "--city", help="Filter by city substring"),
    keyword: str | None = typer.Option(
        None, "--keyword", help="Keyword in title/company/description"
    ),
    platform: str | None = typer.Option(None, "--platform", help="Filter by source platform"),
) -> None:
    init_db(db)

    with session_scope(db) as session:
        row_count = export_jobs_csv(
            session,
            out_path=out,
            city=city,
            keyword=keyword,
            platform=platform,
        )

    typer.echo(f"Exported {row_count} row(s) to {out}")


if __name__ == "__main__":
    app()
