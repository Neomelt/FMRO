from __future__ import annotations

from urllib.parse import urljoin

from fmro_pc.config import SourceConfig
from fmro_pc.crawl.fetcher import FetchedPage
from fmro_pc.parsers.base import ParsedJob


class GenericHtmlParser:
    """A lightweight parser that treats qualifying links as candidate jobs."""

    def parse(self, page: FetchedPage, source: SourceConfig) -> list[ParsedJob]:
        jobs: list[ParsedJob] = []
        seen: set[tuple[str, str]] = set()

        for anchor in page.soup.find_all("a", href=True):
            title = " ".join(anchor.get_text(" ", strip=True).split())
            if len(title) < 3:
                continue

            href = anchor["href"].strip()
            if href.startswith("javascript:"):
                continue

            apply_url = urljoin(page.url, href)
            key = (title.lower(), apply_url)
            if key in seen:
                continue
            seen.add(key)

            container_text = " ".join(anchor.parent.get_text(" ", strip=True).split())
            jobs.append(
                ParsedJob(
                    title=title,
                    apply_url=apply_url,
                    source_url=page.url,
                    description_text=container_text or None,
                    tags=[source.platform],
                )
            )

        return jobs
