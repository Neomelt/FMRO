from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fmro_pc.database import init_db, session_scope
from fmro_pc.models import JobPosting
from fmro_pc.storage.repository import (
    export_jobs_markdown,
    list_jobs,
    mark_job_applied,
    set_job_bookmark,
    set_job_note,
)


def _seed_job(
    *,
    session,
    fingerprint: str,
    title: str,
    company_name: str = "ACME",
    applied: bool = False,
    bookmarked: bool = False,
    notes: str | None = None,
    updated_at: datetime | None = None,
) -> JobPosting:
    now = updated_at or datetime.now(UTC)
    job = JobPosting(
        source_platform="career_page",
        source_company_key="acme",
        company_name=company_name,
        title=title,
        location="Shanghai",
        apply_url=f"https://example.com/jobs/{fingerprint}",
        source_url="https://example.com/jobs",
        fingerprint=fingerprint,
        applied=applied,
        bookmarked=bookmarked,
        notes=notes,
        posted_at=now - timedelta(days=1),
        last_seen_at=now,
        created_at=now,
        updated_at=now,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def _db_path(tmp_path: Path) -> Path:
    db_path = tmp_path / "fmro-test.db"
    init_db(db_path)
    return db_path


def test_job_status_and_note_updates(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)

    with session_scope(db_path) as session:
        job = _seed_job(session=session, fingerprint="fp-1", title="Robotics Intern")
        assert job.id is not None
        job_id = job.id

        applied_row = mark_job_applied(session, job_id=job_id)
        bookmarked_row = set_job_bookmark(session, job_id=job_id, bookmarked=True)
        noted_row = set_job_note(session, job_id=job_id, note="Tailor resume for controls")

        assert applied_row is not None
        assert bookmarked_row is not None
        assert noted_row is not None
        assert noted_row.applied is True
        assert noted_row.bookmarked is True
        assert noted_row.notes == "Tailor resume for controls"


def test_list_jobs_unapplied_filter_and_updated_sort(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)

    with session_scope(db_path) as session:
        now = datetime.now(UTC)
        _seed_job(
            session=session,
            fingerprint="fp-applied",
            title="Applied Role",
            applied=True,
            updated_at=now,
        )
        _seed_job(
            session=session,
            fingerprint="fp-old",
            title="Older Unapplied",
            updated_at=now - timedelta(days=1),
        )
        _seed_job(
            session=session,
            fingerprint="fp-new",
            title="Newer Unapplied",
            updated_at=now + timedelta(minutes=5),
        )

        rows = list_jobs(
            session,
            unapplied_only=True,
            sort="updated_at",
            limit=10,
        )

        assert [row.title for row in rows] == ["Newer Unapplied", "Older Unapplied"]


def test_export_markdown_shape(tmp_path: Path) -> None:
    db_path = _db_path(tmp_path)
    output = tmp_path / "output" / "jobs.md"

    with session_scope(db_path) as session:
        _seed_job(
            session=session,
            fingerprint="fp-md-1",
            title="Robotics Intern",
            company_name="ACME",
            notes="Reach out to recruiter",
        )
        _seed_job(
            session=session,
            fingerprint="fp-md-2",
            title="Perception Engineer",
            company_name="Beta Labs",
            applied=True,
        )

        row_count = export_jobs_markdown(session, out_path=output)

    content = output.read_text(encoding="utf-8")

    assert row_count == 2
    assert content.startswith("# FMRO Jobs")
    assert "Total jobs: 2" in content
    assert "## ACME - Robotics Intern" in content
    assert "## Beta Labs - Perception Engineer" in content
    assert "- Note: Reach out to recruiter" in content
