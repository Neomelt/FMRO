from __future__ import annotations

from pathlib import Path

from sqlmodel import Session

from fmro_pc.storage.repository import export_jobs_csv, export_jobs_markdown


def export_csv(
    session: Session,
    *,
    out_path: Path,
    city: str | None = None,
    keyword: str | None = None,
    platform: str | None = None,
) -> int:
    return export_jobs_csv(
        session,
        out_path=out_path,
        city=city,
        keyword=keyword,
        platform=platform,
    )


def export_markdown(
    session: Session,
    *,
    out_path: Path,
    city: str | None = None,
    keyword: str | None = None,
    platform: str | None = None,
    unapplied: bool = False,
) -> int:
    return export_jobs_markdown(
        session,
        out_path=out_path,
        city=city,
        keyword=keyword,
        platform=platform,
        unapplied_only=unapplied,
    )
