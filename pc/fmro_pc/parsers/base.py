from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from fmro_pc.config import SourceConfig
from fmro_pc.crawl.fetcher import FetchedPage


@dataclass
class ParsedJob:
    title: str
    apply_url: str
    source_url: str
    location: str | None = None
    employment_type: str | None = None
    posted_at: datetime | None = None
    deadline_at: datetime | None = None
    salary_text: str | None = None
    description_text: str | None = None
    tags: list[str] = field(default_factory=list)


class Parser(Protocol):
    def parse(self, page: FetchedPage, source: SourceConfig) -> list[ParsedJob]: ...
