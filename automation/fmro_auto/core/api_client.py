"""Typed HTTP client for the FMRO backend REST API."""
from __future__ import annotations

from typing import Any

import httpx

from fmro_auto.core.config import settings


class FMROClient:
    """Synchronous client for the FMRO backend API."""

    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self._base_url = (base_url or settings.fmro_api_base_url).rstrip("/")
        self._timeout = timeout or settings.fmro_api_timeout
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers={"Content-Type": "application/json"},
        )

    # -- Health -----------------------------------------------------------
    def health(self) -> dict[str, Any]:
        resp = self._client.get("/health")
        resp.raise_for_status()
        return resp.json()

    # -- Companies --------------------------------------------------------
    def list_companies(self) -> list[dict[str, Any]]:
        resp = self._client.get("/api/v1/companies")
        resp.raise_for_status()
        return resp.json()

    # -- Jobs -------------------------------------------------------------
    def list_jobs(self, company_id: int | None = None) -> list[dict[str, Any]]:
        params = {}
        if company_id is not None:
            params["companyId"] = str(company_id)
        resp = self._client.get("/api/v1/jobs", params=params)
        resp.raise_for_status()
        return resp.json()

    # -- Review Queue -----------------------------------------------------
    def list_review_queue(self, status: str = "pending") -> list[dict[str, Any]]:
        resp = self._client.get("/api/v1/review-queue", params={"status": status})
        resp.raise_for_status()
        return resp.json()

    def submit_to_review_queue(
        self,
        source_type: str,
        payload: dict[str, str],
        confidence: float | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "sourceType": source_type,
            "payload": payload,
        }
        if confidence is not None:
            body["confidence"] = confidence
        resp = self._client.post("/api/v1/review-queue", json=body)
        resp.raise_for_status()
        return resp.json()

    # -- Lifecycle --------------------------------------------------------
    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> FMROClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
