"""Generic company career page adapter -- web via Playwright."""
from __future__ import annotations

from typing import Any

from fmro_auto.adapters.base import ScrapedJob, WebAdapter


class CareerPageAdapter(WebAdapter):
    PLATFORM_NAME = "career_page"
    SOURCE_TYPE = "career_page"

    def scrape(self, **kwargs: Any) -> list[ScrapedJob]:
        raise NotImplementedError("CareerPageAdapter.scrape() is a Phase 2 feature.")
