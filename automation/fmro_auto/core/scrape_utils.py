"""Shared scraping utility functions."""
from __future__ import annotations

import logging
import random
import re
import time

logger = logging.getLogger(__name__)


def random_delay(min_sec: float = 1.0, max_sec: float = 3.0) -> None:
    """Sleep for a random duration between *min_sec* and *max_sec*."""
    duration = random.uniform(min_sec, max_sec)
    logger.debug("Sleeping %.1fs", duration)
    time.sleep(duration)


_CITY_SUFFIX = re.compile(r"[市区县]$")


def normalize_location(raw: str) -> str:
    """Normalize a Chinese city/location string.

    Examples:
        "北京市" -> "北京"
        "  上海  " -> "上海"
        "广州市·天河区" -> "广州·天河"
    """
    parts = re.split(r"[·\-/]", raw.strip())
    cleaned = [_CITY_SUFFIX.sub("", p.strip()) for p in parts if p.strip()]
    return "·".join(cleaned) if cleaned else raw.strip()


def safe_text(element: object, selector: str, default: str = "") -> str:
    """Safely extract text from a Scrapling element via CSS selector.

    Works with Scrapling Adaptor objects that support ``.css()`` method.
    Returns *default* on any error.
    """
    try:
        result = element.css(f"{selector}::text").get()  # type: ignore[union-attr]
        return result.strip() if result else default
    except Exception:
        return default
