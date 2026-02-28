from __future__ import annotations

from pathlib import Path
from typing import Literal

import typer
import yaml
from pydantic import ValidationError

from fmro_pc.config import CompaniesConfig, load_companies_config
from fmro_pc.crawl.runner import run_crawl
from fmro_pc.database import init_db, resolve_db_path, session_scope
from fmro_pc.parsers.registry import PARSER_REGISTRY, get_parser
from fmro_pc.services.export import export_csv, export_markdown
from fmro_pc.services.jobs import mark_applied, query_jobs, set_bookmark, set_note

app = typer.Typer(help="FMRO PC crawler", no_args_is_help=True)

sources_app = typer.Typer(help="Inspect or validate companies sources")
crawl_app = typer.Typer(help="Run crawling pipeline")
jobs_app = typer.Typer(help="Query and update stored jobs")
export_app = typer.Typer(help="Export jobs")
db_app = typer.Typer(help="Database helpers")
auth_app = typer.Typer(help="Auth/session helpers for cookie capture")

app.add_typer(sources_app, name="sources")
app.add_typer(crawl_app, name="crawl")
app.add_typer(jobs_app, name="jobs")
app.add_typer(export_app, name="export")
app.add_typer(db_app, name="db")
app.add_typer(auth_app, name="auth")


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
    engine: Literal["auto", "scrapling", "static"] = typer.Option(
        "auto",
        "--engine",
        help="Static fetch engine when not dynamic: auto|scrapling|static",
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
            engine=engine,
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
    unapplied: bool = typer.Option(False, "--unapplied", help="Show only unapplied jobs"),
    include_inactive: bool = typer.Option(
        False, "--include-inactive", help="Show inactive jobs too"
    ),
    sort: Literal["posted_at", "updated_at"] = typer.Option(
        "posted_at",
        "--sort",
        help="Sort field: posted_at|updated_at",
    ),
    limit: int = typer.Option(50, "--limit", min=1),
) -> None:
    init_db(db)

    with session_scope(db) as session:
        rows = query_jobs(
            session,
            city=city,
            keyword=keyword,
            platform=platform,
            unapplied=unapplied,
            include_inactive=include_inactive,
            sort=sort,
            limit=limit,
        )

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


@jobs_app.command("mark-applied")
def jobs_mark_applied(
    id: int = typer.Option(..., "--id", min=1, help="Job ID"),
    db: Path = typer.Option(None, "--db", help="SQLite database path"),
) -> None:
    init_db(db)

    with session_scope(db) as session:
        try:
            row = mark_applied(session, job_id=id)
        except ValueError as exc:
            typer.secho(str(exc), fg=typer.colors.RED)
            raise typer.Exit(code=1) from exc

    typer.echo(f"Job {row.id} marked as applied.")


@jobs_app.command("bookmark")
def jobs_bookmark(
    id: int = typer.Option(..., "--id", min=1, help="Job ID"),
    on: bool = typer.Option(True, "--on/--off", help="Toggle bookmark state"),
    db: Path = typer.Option(None, "--db", help="SQLite database path"),
) -> None:
    init_db(db)

    with session_scope(db) as session:
        try:
            row = set_bookmark(session, job_id=id, enabled=on)
        except ValueError as exc:
            typer.secho(str(exc), fg=typer.colors.RED)
            raise typer.Exit(code=1) from exc

    state = "bookmarked" if row.bookmarked else "unbookmarked"
    typer.echo(f"Job {row.id} {state}.")


@jobs_app.command("note")
def jobs_note(
    id: int = typer.Option(..., "--id", min=1, help="Job ID"),
    text: str = typer.Option(..., "--text", help="Note text"),
    db: Path = typer.Option(None, "--db", help="SQLite database path"),
) -> None:
    init_db(db)

    with session_scope(db) as session:
        try:
            row = set_note(session, job_id=id, text=text)
        except ValueError as exc:
            typer.secho(str(exc), fg=typer.colors.RED)
            raise typer.Exit(code=1) from exc

    typer.echo(f"Job {row.id} note updated.")


@export_app.command("csv")
def export_csv_command(
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
        row_count = export_csv(
            session,
            out_path=out,
            city=city,
            keyword=keyword,
            platform=platform,
        )

    typer.echo(f"Exported {row_count} row(s) to {out}")


@export_app.command("md")
def export_markdown_command(
    out: Path = typer.Option(..., "--out", help="Output Markdown path"),
    db: Path = typer.Option(None, "--db", help="SQLite database path"),
    city: str | None = typer.Option(None, "--city", help="Filter by city substring"),
    keyword: str | None = typer.Option(
        None, "--keyword", help="Keyword in title/company/description"
    ),
    platform: str | None = typer.Option(None, "--platform", help="Filter by source platform"),
    unapplied: bool = typer.Option(False, "--unapplied", help="Export only unapplied jobs"),
) -> None:
    init_db(db)

    with session_scope(db) as session:
        row_count = export_markdown(
            session,
            out_path=out,
            city=city,
            keyword=keyword,
            platform=platform,
            unapplied=unapplied,
        )

    typer.echo(f"Exported {row_count} row(s) to {out}")


@auth_app.command("capture-cookie")
def auth_capture_cookie(
    source: str = typer.Option(..., "--source", help="Source key in companies.yaml"),
    config: Path = typer.Option(Path("companies.yaml"), "--config", help="Path to companies.yaml"),
) -> None:
    cfg = _load_config_or_exit(config)
    target = next((s for s in cfg.sources if s.key == source), None)
    if target is None:
        typer.secho(f"source '{source}' not found", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    login_url = target.entry_urls[0]

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        typer.secho("Playwright not installed. Run: uv sync --extra dynamic", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Opening browser for source={source}")
    typer.echo(f"Please login manually in the opened page: {login_url}")
    typer.echo("After login completed, return to terminal and press Enter.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(login_url, wait_until="domcontentloaded")
        input()
        cookies = context.cookies()
        browser.close()

    domain_keys = ["zhipin.com", "liepin.com", "shixiseng.com"]
    pick_domain = next((d for d in domain_keys if d in login_url), None)

    parts: list[str] = []
    for item in cookies:
        domain = item.get("domain", "")
        if pick_domain and pick_domain not in domain:
            continue
        name = item.get("name", "").strip()
        value = item.get("value", "").strip()
        if name and value:
            parts.append(f"{name}={value}")

    if not parts:
        typer.secho("No usable cookies captured. Try login again.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    cookie_line = "; ".join(parts)
    cookie_path = config.parent / "cookies.local.yaml"
    raw = {}
    if cookie_path.exists():
        raw = yaml.safe_load(cookie_path.read_text(encoding="utf-8")) or {}
    if "cookies" not in raw or not isinstance(raw.get("cookies"), dict):
        raw["cookies"] = {}
    raw["cookies"][source] = cookie_line
    dumped = yaml.safe_dump(raw, sort_keys=False, allow_unicode=True)
    cookie_path.write_text(dumped, encoding="utf-8")

    typer.secho(f"Cookie saved to {cookie_path}", fg=typer.colors.GREEN)
    typer.echo("You can now run crawl with --dynamic.")


if __name__ == "__main__":
    app()
