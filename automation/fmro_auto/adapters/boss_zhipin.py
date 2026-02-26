"""Boss Zhipin (BOSS直聘) adapter -- mobile app via uiautomator2."""
from __future__ import annotations

from typing import Any

from fmro_auto.adapters.base import AppAdapter, ScrapedJob


class BossZhipinAdapter(AppAdapter):
    PLATFORM_NAME = "boss_zhipin"
    SOURCE_TYPE = "boss_zhipin"
    PACKAGE_NAME = "com.hpbr.bosszhipin"

    def scrape(self, **kwargs: Any) -> list[ScrapedJob]:
        raise NotImplementedError("BossZhipinAdapter.scrape() is a Phase 2 feature.")
