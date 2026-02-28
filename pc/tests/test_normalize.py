from fmro_pc.config import SourceConfig
from fmro_pc.crawl.normalize import matches_source_filters, normalize_job
from fmro_pc.parsers.base import ParsedJob


def _source(**overrides):
    base = {
        "key": "acme",
        "company_name": "ACME",
        "enabled": True,
        "platform": "career_page",
        "entry_urls": ["https://example.com/jobs"],
        "mode": "static",
        "parser": "generic_html",
        "include_keywords": [],
        "exclude_keywords": [],
        "city_allowlist": [],
        "crawl_depth": 1,
    }
    base.update(overrides)
    return SourceConfig.model_validate(base)


def test_normalize_job_cleans_fields_and_generates_fingerprint() -> None:
    source = _source()
    parsed = ParsedJob(
        title="  Robotics Intern  ",
        apply_url="  https://example.com/job/1  ",
        source_url="https://example.com/jobs",
        location="  Shanghai ",
        description_text="  Python + perception ",
        tags=["intern", "robotics", "intern"],
    )

    normalized = normalize_job(parsed, source)

    assert normalized.company_name == "ACME"
    assert normalized.title == "Robotics Intern"
    assert normalized.location == "Shanghai"
    assert normalized.apply_url == "https://example.com/job/1"
    assert normalized.source_url == "https://example.com/jobs"
    assert normalized.tags == "intern,robotics"
    assert len(normalized.fingerprint) == 64


def test_filters_respect_include_exclude_and_city() -> None:
    source = _source(
        include_keywords=["robot"],
        exclude_keywords=["senior"],
        city_allowlist=["Shanghai"],
    )
    parsed = ParsedJob(
        title="Robot Intern",
        apply_url="https://example.com/job/2",
        source_url="https://example.com/jobs",
        location="Shanghai",
        description_text="Entry level robotics role",
    )
    normalized = normalize_job(parsed, source)

    assert matches_source_filters(normalized, source) is True

    blocked = ParsedJob(
        title="Senior Robot Architect",
        apply_url="https://example.com/job/3",
        source_url="https://example.com/jobs",
        location="Shanghai",
        description_text="senior role",
    )
    blocked_normalized = normalize_job(blocked, source)

    assert matches_source_filters(blocked_normalized, source) is False
