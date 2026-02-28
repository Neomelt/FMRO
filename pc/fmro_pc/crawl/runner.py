from __future__ import annotations

from dataclasses import dataclass, field

from sqlmodel import Session

from fmro_pc.config import CompaniesConfig, SourceConfig, select_sources
from fmro_pc.crawl.browser import PlaywrightFetcher
from fmro_pc.crawl.fetcher import StaticFetcher
from fmro_pc.crawl.normalize import matches_source_filters, normalize_job
from fmro_pc.parsers.registry import get_parser
from fmro_pc.storage.repository import UpsertStats, upsert_jobs


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


def run_crawl(
    session: Session,
    config: CompaniesConfig,
    *,
    source_key: str | None = None,
    limit: int | None = None,
    force_dynamic: bool = False,
) -> CrawlSummary:
    sources = select_sources(config, source_key=source_key, only_enabled=True)
    source_summaries: list[SourceRunSummary] = []

    dynamic_fetcher = PlaywrightFetcher()
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
                            f"dynamic fetch failed for {url}: {exc}; falling back to static"
                        )

                if page is None:
                    try:
                        page = static_fetcher.fetch(url, headers=headers)
                    except Exception as exc:
                        source_summary.errors.append(f"static fetch failed for {url}: {exc}")
                        source_summary.parse_failures += 1
                        continue

                source_summary.pages_fetched += 1

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
            source_summaries.append(source_summary)

    return CrawlSummary(
        source_count=len(sources),
        sources=source_summaries,
    )
