from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

from fmro_pc.config import SourceConfig
from fmro_pc.crawl.dedupe import build_fingerprint
from fmro_pc.parsers.base import ParsedJob


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.strip().split())
    return cleaned or None


def _clean_tags(tags: list[str]) -> str | None:
    unique = sorted({tag.strip() for tag in tags if tag.strip()})
    if not unique:
        return None
    return ",".join(unique)


@dataclass
class NormalizedJob:
    source_platform: str
    source_company_key: str
    company_name: str
    title: str
    location: str | None
    employment_type: str | None
    posted_at: datetime | None
    deadline_at: datetime | None
    apply_url: str
    source_url: str
    salary_text: str | None
    description_text: str | None
    tags: str | None
    fingerprint: str

    def to_record(self) -> dict:
        return asdict(self)


def normalize_job(parsed: ParsedJob, source: SourceConfig) -> NormalizedJob:
    title = _clean_text(parsed.title)
    if not title:
        raise ValueError("parsed job title is required")

    apply_url = _clean_text(parsed.apply_url)
    source_url = _clean_text(parsed.source_url)

    if not apply_url and not source_url:
        raise ValueError("either apply_url or source_url is required")

    final_apply_url = apply_url or source_url or ""
    final_source_url = source_url or final_apply_url

    fingerprint = build_fingerprint(
        company_name=source.company_name,
        title=title,
        apply_url=apply_url,
        location=parsed.location,
        source_url=final_source_url,
    )

    return NormalizedJob(
        source_platform=source.platform,
        source_company_key=source.key,
        company_name=source.company_name,
        title=title,
        location=_clean_text(parsed.location),
        employment_type=_clean_text(parsed.employment_type),
        posted_at=parsed.posted_at,
        deadline_at=parsed.deadline_at,
        apply_url=final_apply_url,
        source_url=final_source_url,
        salary_text=_clean_text(parsed.salary_text),
        description_text=_clean_text(parsed.description_text),
        tags=_clean_tags(parsed.tags),
        fingerprint=fingerprint,
    )


def matches_source_filters(job: NormalizedJob, source: SourceConfig) -> bool:
    haystack = " ".join(
        value
        for value in [
            job.title.lower(),
            (job.description_text or "").lower(),
            (job.location or "").lower(),
        ]
        if value
    )

    if source.include_keywords:
        include_keywords = [item.lower() for item in source.include_keywords]
        if not any(keyword in haystack for keyword in include_keywords):
            return False

    if source.exclude_keywords:
        exclude_keywords = [item.lower() for item in source.exclude_keywords]
        if any(keyword in haystack for keyword in exclude_keywords):
            return False

    if source.city_allowlist and job.location:
        cities = [city.lower() for city in source.city_allowlist]
        if not any(city in job.location.lower() for city in cities):
            return False

    if source.city_allowlist and not job.location:
        return False

    return True
