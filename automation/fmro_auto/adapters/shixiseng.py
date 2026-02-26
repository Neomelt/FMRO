"""Shixiseng (实习僧) adapter -- web scraping via Scrapling."""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote_plus

from fmro_auto.adapters.base import ScrapedJob, WebAdapter
from fmro_auto.core.config import settings
from fmro_auto.core.scrape_utils import normalize_location, random_delay, safe_text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CSS selectors (update here when Shixiseng changes their DOM)
# ---------------------------------------------------------------------------
SELECTORS = {
    "job_card": ".intern-wrap .intern_item, .intern-wrap .intern-item, [class*='intern-item']",
    "title": ".intern-detail__job a, .intern_position a, [class*='job-name'], [class*='position']",
    "company": ".intern-detail__company a, .intern_company, [class*='company-name']",
    "location": ".intern-detail__address, .intern_city, [class*='city']",
    "stipend": ".intern-detail__salary, .intern_salary, [class*='salary'], [class*='stipend']",
    "link": "a[href*='/intern/'], a[href*='/job/']",
    "next_page": ".pagination .next:not(.disabled), a.next, [class*='next-page']",
}

BASE_URL = "https://www.shixiseng.com"
SEARCH_URL = BASE_URL + "/interns?keyword={keyword}&city=%E5%85%A8%E5%9B%BD&page={page}"


class ShixisengAdapter(WebAdapter):
    PLATFORM_NAME = "shixiseng"
    SOURCE_TYPE = "shixiseng"

    def scrape(self, **kwargs: Any) -> list[ScrapedJob]:
        keyword = kwargs.get("keyword", settings.search_keywords[0])
        max_pages = kwargs.get("max_pages", settings.scrape_max_pages)

        from scrapling.fetchers import StealthyFetcher

        jobs: list[ScrapedJob] = []
        seen_titles: set[str] = set()

        for page_num in range(1, max_pages + 1):
            url = SEARCH_URL.format(keyword=quote_plus(keyword), page=page_num)
            logger.info("Fetching Shixiseng page %d: %s", page_num, url)

            try:
                page = StealthyFetcher.fetch(url, headless=settings.browser_headless)
            except Exception as e:
                logger.error("Failed to fetch Shixiseng page %d: %s", page_num, e)
                break

            cards = page.css(SELECTORS["job_card"])
            if not cards:
                logger.warning("No intern cards found on page %d, stopping.", page_num)
                break

            logger.info("Found %d cards on page %d", len(cards), page_num)

            for card in cards:
                job = _parse_card(card)
                if job and job.title not in seen_titles:
                    seen_titles.add(job.title)
                    jobs.append(job)

            # Check for next page
            next_btn = page.css(SELECTORS["next_page"])
            if not next_btn:
                logger.info("No next page button found, stopping.")
                break

            random_delay(settings.scrape_delay_seconds, settings.scrape_delay_seconds + 2)

        logger.info("Shixiseng scrape complete: %d jobs found", len(jobs))
        return jobs


def _parse_card(card: Any) -> ScrapedJob | None:
    """Parse a single Shixiseng intern card into a ScrapedJob."""
    title = safe_text(card, SELECTORS["title"])
    company = safe_text(card, SELECTORS["company"])

    if not title or not company:
        return None

    location_raw = safe_text(card, SELECTORS["location"])
    location = normalize_location(location_raw) if location_raw else None

    # Extract detail URL
    source_url = None
    try:
        link = card.css(SELECTORS["link"])
        if link:
            href = link[0].attrib.get("href", "")
            if href.startswith("/"):
                source_url = BASE_URL + href
            elif href.startswith("http"):
                source_url = href
    except Exception:
        pass

    return ScrapedJob(
        company_name=company,
        title=title,
        source_platform="shixiseng",
        location=location,
        source_url=source_url,
        apply_url=source_url,
    )
