"""Liepin (猎聘) adapter -- web via Playwright."""
from __future__ import annotations

from typing import Any

from fmro_auto.adapters.base import ScrapedJob, WebAdapter


class LiepinAdapter(WebAdapter):
    PLATFORM_NAME = "liepin"
    SOURCE_TYPE = "liepin"

    def scrape(self, **kwargs: Any) -> list[ScrapedJob]:
        raise NotImplementedError("LiepinAdapter.scrape() is a Phase 2 feature.")
