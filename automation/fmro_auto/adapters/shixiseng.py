"""Shixiseng (实习僧) adapter -- web via Playwright."""
from __future__ import annotations

from typing import Any

from fmro_auto.adapters.base import ScrapedJob, WebAdapter


class ShixisengAdapter(WebAdapter):
    PLATFORM_NAME = "shixiseng"
    SOURCE_TYPE = "shixiseng"

    def scrape(self, **kwargs: Any) -> list[ScrapedJob]:
        raise NotImplementedError("ShixisengAdapter.scrape() is a Phase 2 feature.")
