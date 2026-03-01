from __future__ import annotations

from urllib.parse import urljoin

from bs4.element import Tag

from fmro_pc.config import SourceConfig
from fmro_pc.crawl.fetcher import FetchedPage
from fmro_pc.parsers._common import clean_text, infer_city, looks_like_job_title
from fmro_pc.parsers.base import ParsedJob


class ShiXiSengParser:
    def parse(self, page: FetchedPage, source: SourceConfig) -> list[ParsedJob]:
        jobs: list[ParsedJob] = []
        seen: set[str] = set()

        for anchor in page.soup.find_all("a", href=True):
            href = anchor.get("href", "").strip()
            if not href:
                continue
            if "/intern/" not in href and "shixiseng.com/intern/" not in href:
                continue

            title = self._pick_title(anchor)
            if not looks_like_job_title(title):
                continue

            apply_url = urljoin(page.url, href)
            if apply_url in seen:
                continue
            seen.add(apply_url)

            parent_text = anchor.parent.get_text(" ", strip=True) if anchor.parent else ""
            container_text = clean_text(parent_text)
            location = self._pick_location(anchor)
            jobs.append(
                ParsedJob(
                    title=title,
                    apply_url=apply_url,
                    source_url=page.url,
                    location=location,
                    employment_type="intern",
                    description_text=container_text or None,
                    tags=[source.platform],
                )
            )

        return jobs

    def _pick_title(self, anchor: Tag) -> str | None:
        candidates = [
            clean_text(anchor.get("title")),
            clean_text(anchor.get("aria-label")),
            clean_text(anchor.get("data-title")),
            clean_text(anchor.get("data-name")),
        ]

        for value in candidates:
            if value and not self._has_bad_chars(value):
                return value

        return clean_text(anchor.get_text(" ", strip=True))

    def _has_bad_chars(self, value: str) -> bool:
        return any("\ue000" <= ch <= "\uf8ff" for ch in value) or "�" in value or "□" in value

    def _pick_location(self, anchor: Tag) -> str | None:
        parent = anchor.parent
        if parent is None:
            return None
        return infer_city(parent.get_text(" ", strip=True))
