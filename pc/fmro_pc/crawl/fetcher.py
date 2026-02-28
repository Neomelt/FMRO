from __future__ import annotations

from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup


@dataclass
class FetchedPage:
    url: str
    html: str
    soup: BeautifulSoup
    status_code: int
    dynamic: bool = False


class StaticFetcher:
    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self._client = httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "FMRO-PC/0.1 (+https://github.com/;"
                    " static crawler for personal company source ingestion)"
                )
            },
        )

    def fetch(self, url: str) -> FetchedPage:
        response = self._client.get(url)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        return FetchedPage(
            url=str(response.url),
            html=html,
            soup=soup,
            status_code=response.status_code,
            dynamic=False,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> StaticFetcher:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
