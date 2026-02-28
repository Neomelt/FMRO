from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


class JobPosting(SQLModel, table=True):
    __tablename__ = "job_postings"
    __table_args__ = (UniqueConstraint("fingerprint", name="uq_job_postings_fingerprint"),)

    id: int | None = Field(default=None, primary_key=True)

    source_platform: str = Field(index=True)
    source_company_key: str = Field(index=True)
    company_name: str = Field(index=True)

    title: str = Field(index=True)
    location: str | None = Field(default=None, index=True)
    employment_type: str | None = None

    posted_at: datetime | None = Field(default=None, index=True)
    deadline_at: datetime | None = Field(default=None, index=True)

    apply_url: str
    source_url: str

    salary_text: str | None = None
    description_text: str | None = None
    tags: str | None = None

    fingerprint: str = Field(index=True)

    is_active: bool = Field(default=True, index=True)
    bookmarked: bool = Field(default=False, index=True)
    applied: bool = Field(default=False, index=True)
    notes: str | None = None

    last_seen_at: datetime = Field(default_factory=utcnow, index=True)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow, index=True)
