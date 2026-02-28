from __future__ import annotations

from typing import Literal

from sqlmodel import Session

from fmro_pc.models import JobPosting
from fmro_pc.storage.repository import (
    list_jobs,
    mark_job_applied,
    set_job_bookmark,
    set_job_note,
)

JobListSort = Literal["posted_at", "updated_at"]


def query_jobs(
    session: Session,
    *,
    city: str | None = None,
    keyword: str | None = None,
    platform: str | None = None,
    unapplied: bool = False,
    include_inactive: bool = False,
    sort: JobListSort = "posted_at",
    limit: int = 50,
) -> list[JobPosting]:
    return list_jobs(
        session,
        city=city,
        keyword=keyword,
        platform=platform,
        unapplied_only=unapplied,
        active_only=not include_inactive,
        sort=sort,
        limit=limit,
    )


def mark_applied(session: Session, *, job_id: int) -> JobPosting:
    row = mark_job_applied(session, job_id=job_id)
    if row is None:
        raise ValueError(f"job id={job_id} not found")
    return row


def set_bookmark(session: Session, *, job_id: int, enabled: bool) -> JobPosting:
    row = set_job_bookmark(session, job_id=job_id, bookmarked=enabled)
    if row is None:
        raise ValueError(f"job id={job_id} not found")
    return row


def set_note(session: Session, *, job_id: int, text: str) -> JobPosting:
    row = set_job_note(session, job_id=job_id, note=text)
    if row is None:
        raise ValueError(f"job id={job_id} not found")
    return row
