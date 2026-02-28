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


class ScraplingFetcher:
    def __init__(self) -> None:
        self._default_headers = {
            "User-Agent": (
                "FMRO-PC/0.1 (+https://github.com/;"
                " scrapling crawler for personal company source ingestion)"
            )
        }

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> FetchedPage:
        try:
            from scrapling import Fetcher
        except ImportError as exc:
            raise RuntimeError(
                "Scrapling is not available. Install dependencies with `uv sync --extra dynamic`."
            ) from exc

        request_headers = dict(self._default_headers)
        if headers:
            request_headers.update(headers)

        fetcher = Fetcher()
        response = fetcher.get(url, headers=request_headers, follow_redirects=True)
        status_code = int(getattr(response, "status", 0) or 0)
        if status_code >= 400:
            raise RuntimeError(f"scrapling returned status {status_code} for {url}")

        body = getattr(response, "body", b"")
        if isinstance(body, bytes):
            html = body.decode("utf-8", errors="ignore")
        else:
            html = str(body)

        final_url = str(getattr(response, "url", url))
        soup = BeautifulSoup(html, "html.parser")
        return FetchedPage(
            url=final_url,
            html=html,
            soup=soup,
            status_code=status_code or 200,
            dynamic=False,
        )


class StaticFetcher:
    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self._default_headers = {
            "User-Agent": (
                "FMRO-PC/0.1 (+https://github.com/;"
                " static crawler for personal company source ingestion)"
            )
        }
        self._client = httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=True,
            headers=self._default_headers,
        )

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> FetchedPage:
        request_headers = dict(self._default_headers)
        if headers:
            request_headers.update(headers)
        response = self._client.get(url, headers=request_headers)
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
