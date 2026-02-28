from __future__ import annotations

from urllib.parse import urljoin

from bs4.element import Tag

from fmro_pc.config import SourceConfig
from fmro_pc.crawl.fetcher import FetchedPage
from fmro_pc.parsers.base import ParsedJob


class LiepinParser:
    def parse(self, page: FetchedPage, source: SourceConfig) -> list[ParsedJob]:
        jobs: list[ParsedJob] = []
        seen: set[str] = set()

        for anchor in page.soup.find_all("a", href=True):
            href = anchor.get("href", "").strip()
            if not href:
                continue
            if "/job/" not in href and "liepin.com/job/" not in href:
                continue

            title = self._pick_title(anchor)
            if not title:
                continue

            apply_url = urljoin(page.url, href)
            if apply_url in seen:
                continue
            seen.add(apply_url)

            container_text = " ".join(anchor.get_text(" ", strip=True).split())
            location = self._pick_location(anchor)
            jobs.append(
                ParsedJob(
                    title=title,
                    apply_url=apply_url,
                    source_url=page.url,
                    location=location,
                    description_text=container_text or None,
                    tags=[source.platform],
                )
            )

        return jobs

    def _pick_title(self, anchor: Tag) -> str | None:
        title = anchor.get("title")
        if title:
            return " ".join(title.split())
        text = " ".join(anchor.get_text(" ", strip=True).split())
        return text if len(text) >= 3 else None

    def _pick_location(self, anchor: Tag) -> str | None:
        parent = anchor.parent
        if parent is None:
            return None
        text = " ".join(parent.get_text(" ", strip=True).split())
        cities = ["北京", "上海", "深圳", "杭州", "广州", "成都", "苏州", "南京", "武汉", "西安"]
        for city in cities:
            if city in text:
                return city
        return None
