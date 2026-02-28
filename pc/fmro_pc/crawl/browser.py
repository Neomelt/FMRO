from __future__ import annotations

from bs4 import BeautifulSoup

from fmro_pc.crawl.fetcher import FetchedPage


class PlaywrightFetcher:
    """Optional dynamic page fetcher.

    This module intentionally keeps the dependency optional.
    Install with: `pip install .[dynamic]`
    """

    def __init__(self, timeout_ms: int = 20_000) -> None:
        self.timeout_ms = timeout_ms

    def fetch(self, url: str) -> FetchedPage:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is not installed. Install optional dependency with `.[dynamic]`."
            ) from exc

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            response = page.goto(url, wait_until="networkidle", timeout=self.timeout_ms)
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
