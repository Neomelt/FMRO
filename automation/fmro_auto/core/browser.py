"""Playwright browser manager for headless web scraping."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from fmro_auto.core.config import settings

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manage a Playwright Chromium browser instance."""

    def __init__(self, headless: bool | None = None):
        self._headless = headless if headless is not None else settings.browser_headless
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    def start(self) -> Browser:
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self._headless,
            slow_mo=settings.browser_slow_mo,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        logger.info("Browser started (headless=%s)", self._headless)
        return self._browser

    @property
    def browser(self) -> Browser:
        if self._browser is None:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._browser

    def new_context(self, **kwargs: Any) -> BrowserContext:
        defaults = {
            "viewport": {"width": 1280, "height": 800},
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
            "user_agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        defaults.update(kwargs)
        return self.browser.new_context(**defaults)

    def new_page(self, context: BrowserContext | None = None) -> Page:
        ctx = context or self.new_context()
        return ctx.new_page()

    def screenshot_page(self, page: Page, name: str = "page") -> Path:
        out = Path(settings.output_dir) / f"{name}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out), full_page=True)
        logger.info("Page screenshot saved: %s", out)
        return out

    def stop(self) -> None:
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
        logger.info("Browser stopped")

    def __enter__(self) -> BrowserManager:
        self.start()
        return self

    def __exit__(self, *args: Any) -> None:
        self.stop()
