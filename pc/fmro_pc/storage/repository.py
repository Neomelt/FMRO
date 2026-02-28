from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import or_
from sqlmodel import Session, select

from fmro_pc.crawl.normalize import NormalizedJob
from fmro_pc.models import JobPosting


def utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass
class UpsertStats:
    inserted: int = 0
    updated: int = 0
    deactivated: int = 0
    duplicates_skipped: int = 0


def upsert_jobs(
    session: Session,
    jobs: list[NormalizedJob],
    *,
    source_key: str,
    seen_at: datetime | None = None,
) -> UpsertStats:
    timestamp = seen_at or utcnow()
    stats = UpsertStats()

    unique_jobs: dict[str, NormalizedJob] = {}
    for job in jobs:
        if job.fingerprint in unique_jobs:
            stats.duplicates_skipped += 1
            continue
        unique_jobs[job.fingerprint] = job

    fingerprints = list(unique_jobs)
    existing: dict[str, JobPosting] = {}
    if fingerprints:
        rows = session.exec(
            select(JobPosting).where(JobPosting.fingerprint.in_(fingerprints))
        ).all()
        existing = {row.fingerprint: row for row in rows}

    for fingerprint, job in unique_jobs.items():
        record = job.to_record()
        if fingerprint in existing:
            current = existing[fingerprint]
            current.source_platform = record["source_platform"]
            current.source_company_key = record["source_company_key"]
            current.company_name = record["company_name"]
            current.title = record["title"]
            current.location = record["location"]
            current.employment_type = record["employment_type"]
            current.posted_at = record["posted_at"]
            current.deadline_at = record["deadline_at"]
            current.apply_url = record["apply_url"]
            current.source_url = record["source_url"]
            current.salary_text = record["salary_text"]
            current.description_text = record["description_text"]
            current.tags = record["tags"]
            current.is_active = True
            current.last_seen_at = timestamp
            current.updated_at = timestamp
            session.add(current)
            stats.updated += 1
            continue

        session.add(
            JobPosting(
                **record,
                is_active=True,
                last_seen_at=timestamp,
                created_at=timestamp,
                updated_at=timestamp,
            )
        )
        stats.inserted += 1

    active_rows = session.exec(
        select(JobPosting).where(
            JobPosting.source_company_key == source_key,
            JobPosting.is_active.is_(True),
        )
    ).all()

    seen_fingerprints = set(fingerprints)
    for row in active_rows:
        if row.fingerprint in seen_fingerprints:
            continue
        row.is_active = False
        row.updated_at = timestamp
        session.add(row)
        stats.deactivated += 1

    session.commit()
    return stats


def list_jobs(
    session: Session,
    *,
    city: str | None = None,
    keyword: str | None = None,
    platform: str | None = None,
    active_only: bool = True,
    sort: str = "posted_at",
    limit: int = 100,
) -> list[JobPosting]:
    stmt = select(JobPosting)

    if active_only:
        stmt = stmt.where(JobPosting.is_active.is_(True))

    if city:
        stmt = stmt.where(JobPosting.location.is_not(None), JobPosting.location.ilike(f"%{city}%"))

    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                JobPosting.title.ilike(pattern),
                JobPosting.company_name.ilike(pattern),
                JobPosting.description_text.ilike(pattern),
            )
        )

    if platform:
        stmt = stmt.where(JobPosting.source_platform == platform)

    sort_fields = {
        "posted_at": JobPosting.posted_at,
        "last_seen_at": JobPosting.last_seen_at,
        "updated_at": JobPosting.updated_at,
        "created_at": JobPosting.created_at,
        "title": JobPosting.title,
        "company": JobPosting.company_name,
    }
    sort_column = sort_fields.get(sort)
    if sort_column is None:
        supported = ", ".join(sorted(sort_fields))
        raise ValueError(f"unsupported sort field '{sort}'. Supported: {supported}")

    if sort in {"title", "company"}:
        stmt = stmt.order_by(sort_column.asc())
    else:
        stmt = stmt.order_by(sort_column.desc())

    if limit > 0:
        stmt = stmt.limit(limit)

    return list(session.exec(stmt).all())


def export_jobs_csv(
    session: Session,
    out_path: str | Path,
    *,
    city: str | None = None,
    keyword: str | None = None,
    platform: str | None = None,
) -> int:
    jobs = list_jobs(
        session,
        city=city,
        keyword=keyword,
        platform=platform,
        active_only=True,
        sort="updated_at",
        limit=0,
    )

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "id",
        "company_name",
        "title",
        "location",
        "source_platform",
        "apply_url",
        "source_url",
        "salary_text",
        "posted_at",
        "is_active",
        "bookmarked",
        "applied",
        "notes",
        "updated_at",
    ]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in jobs:
            writer.writerow(
                {
                    "id": row.id,
                    "company_name": row.company_name,
                    "title": row.title,
                    "location": row.location or "",
                    "source_platform": row.source_platform,
                    "apply_url": row.apply_url,
                    "source_url": row.source_url,
                    "salary_text": row.salary_text or "",
                    "posted_at": row.posted_at.isoformat() if row.posted_at else "",
                    "is_active": row.is_active,
                    "bookmarked": row.bookmarked,
                    "applied": row.applied,
                    "notes": row.notes or "",
                    "updated_at": row.updated_at.isoformat() if row.updated_at else "",
                }
            )

    return len(jobs)
