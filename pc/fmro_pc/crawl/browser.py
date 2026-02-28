from __future__ import annotations

import time

from bs4 import BeautifulSoup

from fmro_pc.crawl.fetcher import FetchedPage


class PlaywrightFetcher:
    """Optional dynamic page fetcher.

    This module intentionally keeps the dependency optional.
    Install with: `pip install .[dynamic]`
    """

    def __init__(self, timeout_ms: int = 20_000, scroll_rounds: int = 4) -> None:
        self.timeout_ms = timeout_ms
        self.scroll_rounds = scroll_rounds

    def _auto_scroll(self, page) -> None:
        for _ in range(self.scroll_rounds):
            page.mouse.wheel(0, 4000)
            page.wait_for_timeout(800)

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> FetchedPage:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is not installed. Install optional dependency with `.[dynamic]`."
            ) from exc

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(extra_http_headers=headers or None)
            page = context.new_page()

            response = None
            last_exc = None
            for _ in range(2):
                try:
                    response = page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=self.timeout_ms,
                    )
                    self._auto_scroll(page)
                    page.wait_for_load_state("networkidle", timeout=self.timeout_ms)
                    last_exc = None
                    break
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    time.sleep(1)

            if last_exc is not None:
                browser.close()
                raise RuntimeError(f"dynamic fetch retry failed: {last_exc}")

            html = page.content()
            final_url = page.url
            status_code = response.status if response else 200
            browser.close()

        return FetchedPage(
            url=final_url,
            html=html,
            soup=BeautifulSoup(html, "html.parser"),
            status_code=status_code,
            dynamic=True,
        )
