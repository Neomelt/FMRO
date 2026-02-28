from __future__ import annotations

from dataclasses import dataclass, field

from sqlmodel import Session

from fmro_pc.config import CompaniesConfig, SourceConfig, select_sources
from fmro_pc.crawl.browser import PlaywrightFetcher
from fmro_pc.crawl.fetcher import ScraplingFetcher, StaticFetcher
from fmro_pc.crawl.normalize import matches_source_filters, normalize_job
from fmro_pc.parsers.registry import get_parser
from fmro_pc.storage.repository import UpsertStats, upsert_jobs

RISK_PLATFORMS = {"boss_zhipin", "liepin", "shixiseng"}
BLOCK_HINTS = [
    "验证码",
    "安全验证",
    "行为验证",
    "访问受限",
    "滑动验证",
    "人机验证",
    "请完成验证",
    "captcha",
]


@dataclass
class SourceRunSummary:
    source_key: str
    pages_fetched: int = 0
    parse_failures: int = 0
    jobs_extracted: int = 0
    jobs_normalized: int = 0
    jobs_filtered_out: int = 0
    upsert: UpsertStats = field(default_factory=UpsertStats)
    errors: list[str] = field(default_factory=list)


@dataclass
class CrawlSummary:
    source_count: int
    sources: list[SourceRunSummary]

    @property
    def total_pages_fetched(self) -> int:
        return sum(item.pages_fetched for item in self.sources)

    @property
    def total_jobs_extracted(self) -> int:
        return sum(item.jobs_extracted for item in self.sources)

    @property
    def total_jobs_normalized(self) -> int:
        return sum(item.jobs_normalized for item in self.sources)

    @property
    def total_jobs_inserted(self) -> int:
        return sum(item.upsert.inserted for item in self.sources)

    @property
    def total_jobs_updated(self) -> int:
        return sum(item.upsert.updated for item in self.sources)

    @property
    def total_jobs_deactivated(self) -> int:
        return sum(item.upsert.deactivated for item in self.sources)

    @property
    def total_failures(self) -> int:
        return sum(item.parse_failures + len(item.errors) for item in self.sources)


def _should_use_dynamic(source: SourceConfig, force_dynamic: bool) -> bool:
    if force_dynamic:
        return True
    return source.mode == "dynamic"


def _looks_like_block_page(html: str) -> bool:
    content = html.lower()
    return any(hint in content for hint in BLOCK_HINTS)


def _has_cookie_header(source: SourceConfig) -> bool:
    headers = source.request_headers or {}
    return any(key.lower() == "cookie" and value.strip() for key, value in headers.items())


def run_crawl(
    session: Session,
    config: CompaniesConfig,
    *,
    source_key: str | None = None,
    limit: int | None = None,
    force_dynamic: bool = False,
    engine: str = "auto",
) -> CrawlSummary:
    if engine not in {"auto", "scrapling", "static"}:
        raise ValueError("engine must be one of: auto, scrapling, static")

    sources = select_sources(config, source_key=source_key, only_enabled=True)
    source_summaries: list[SourceRunSummary] = []

    dynamic_fetcher = PlaywrightFetcher()
    scrapling_fetcher = ScraplingFetcher()
    with StaticFetcher() as static_fetcher:
        for source in sources:
            source_summary = SourceRunSummary(source_key=source.key)
            parser = get_parser(source.parser)
            urls = source.entry_urls[:limit] if limit and limit > 0 else source.entry_urls

            normalized_jobs = []
            for url in urls:
                use_dynamic = _should_use_dynamic(source, force_dynamic)
                page = None

                headers = source.request_headers or None

                if use_dynamic:
                    try:
                        page = dynamic_fetcher.fetch(url, headers=headers)
                    except Exception as exc:
                        source_summary.errors.append(
                            f"dynamic fetch failed for {url}: {exc}; falling back"
                        )

                if page is None and engine in {"auto", "scrapling"}:
                    try:
                        page = scrapling_fetcher.fetch(url, headers=headers)
                    except Exception as exc:
                        source_summary.errors.append(
                            f"scrapling fetch failed for {url}: {exc}; falling back"
                        )

                if page is None and engine in {"auto", "static"}:
                    try:
                        page = static_fetcher.fetch(url, headers=headers)
                    except Exception as exc:
                        source_summary.errors.append(f"static fetch failed for {url}: {exc}")
                        source_summary.parse_failures += 1
                        continue

                if page is None:
                    source_summary.parse_failures += 1
                    source_summary.errors.append(f"no fetch engine succeeded for {url}")
                    continue

                source_summary.pages_fetched += 1

                if _looks_like_block_page(page.html):
                    source_summary.errors.append(
                        f"blocked by anti-bot for {url} (captcha/verification detected)"
                    )
                    source_summary.parse_failures += 1
                    continue

                try:
                    parsed_jobs = parser.parse(page, source)
                except Exception as exc:
                    source_summary.errors.append(f"parse failed for {url}: {exc}")
                    source_summary.parse_failures += 1
                    continue

                source_summary.jobs_extracted += len(parsed_jobs)
                for parsed_job in parsed_jobs:
                    try:
                        normalized = normalize_job(parsed_job, source)
                    except ValueError:
                        source_summary.parse_failures += 1
                        continue

                    if not matches_source_filters(normalized, source):
                        source_summary.jobs_filtered_out += 1
                        continue

                    normalized_jobs.append(normalized)

            source_summary.jobs_normalized = len(normalized_jobs)
            source_summary.upsert = upsert_jobs(
                session,
                normalized_jobs,
                source_key=source.key,
            )

            if (
                source.platform in RISK_PLATFORMS
                and source_summary.jobs_extracted == 0
                and not _has_cookie_header(source)
            ):
                source_summary.errors.append(
                    "no jobs extracted; this platform often needs login Cookie in request_headers"
                )

            source_summaries.append(source_summary)

    return CrawlSummary(
        source_count=len(sources),
        sources=source_summaries,
    )
