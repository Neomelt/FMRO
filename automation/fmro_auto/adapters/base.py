"""Abstract base classes for platform adapters."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from fmro_auto.core.api_client import FMROClient
from fmro_auto.core.browser import BrowserManager
from fmro_auto.core.device import DeviceManager


@dataclass
class ScrapedJob:
    """A single job posting scraped from a platform."""

    company_name: str
    title: str
    source_platform: str
    location: str | None = None
    source_url: str | None = None
    apply_url: str | None = None
    deadline: str | None = None
    status: str = "open"
    extra: dict[str, str] = field(default_factory=dict)

    def to_review_payload(self) -> dict[str, str]:
        payload: dict[str, str] = {
            "companyName": self.company_name,
            "title": self.title,
            "status": self.status,
            "sourcePlatform": self.source_platform,
        }
        if self.location:
            payload["location"] = self.location
        if self.source_url:
            payload["sourceUrl"] = self.source_url
        if self.apply_url:
            payload["applyUrl"] = self.apply_url
        if self.deadline:
            payload["deadlineAt"] = self.deadline
        if self.extra:
            payload.update(self.extra)
        return payload


class PlatformAdapter(ABC):
    """Base class for all platform adapters."""

    PLATFORM_NAME: str = "unknown"
    SOURCE_TYPE: str = "unknown"

    def __init__(self, api_client: FMROClient):
        self.api = api_client
        self.logger = logging.getLogger(f"adapter.{self.PLATFORM_NAME}")

    @abstractmethod
    def scrape(self, **kwargs: Any) -> list[ScrapedJob]:
        ...

    def submit_results(self, jobs: list[ScrapedJob], confidence: float = 0.5) -> int:
        submitted = 0
        for job in jobs:
            try:
                self.api.submit_to_review_queue(
                    source_type=self.SOURCE_TYPE,
                    payload=job.to_review_payload(),
                    confidence=confidence,
                )
                submitted += 1
                self.logger.info("Submitted: %s @ %s", job.title, job.company_name)
            except Exception as e:
                self.logger.error("Failed to submit %s: %s", job.title, e)
        return submitted


class WebAdapter(PlatformAdapter, ABC):
    """Adapter for web-based platforms using Playwright."""

    def __init__(self, api_client: FMROClient, browser_manager: BrowserManager):
        super().__init__(api_client)
        self.browser = browser_manager


class AppAdapter(PlatformAdapter, ABC):
    """Adapter for mobile app platforms using uiautomator2."""

    def __init__(self, api_client: FMROClient, device_manager: DeviceManager):
        super().__init__(api_client)
        self.device = device_manager
