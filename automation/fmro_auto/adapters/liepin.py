"""Liepin (猎聘) adapter -- web scraping via Scrapling."""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote_plus

from fmro_auto.adapters.base import ScrapedJob, WebAdapter
from fmro_auto.core.config import settings
from fmro_auto.core.scrape_utils import normalize_location, random_delay, safe_text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CSS selectors (update here when Liepin changes their DOM)
# ---------------------------------------------------------------------------
SELECTORS = {
    "job_card": ".job-list-item, .sojob-item-main, [class*='job-card']",
    "title": ".job-title-box .ellipsis-1, .job-info h3, [class*='job-title'], [class*='job-name']",
    "company": ".company-name, .company-name-box a, [class*='company-name']",
    "location": ".job-labels-tag, .job-area, [class*='location'], [class*='city']",
    "salary": ".job-salary, [class*='salary']",
    "link": "a[href*='/job/'], a[href*='/a/']",
    "next_page": ".ant-pagination-next:not(.ant-pagination-disabled), a[class*='next']",
}

BASE_URL = "https://www.liepin.com"
SEARCH_URL = BASE_URL + "/zhaopin/?key={keyword}&currentPage={page}"


class LiepinAdapter(WebAdapter):
    PLATFORM_NAME = "liepin"
    SOURCE_TYPE = "liepin"

    def scrape(self, **kwargs: Any) -> list[ScrapedJob]:
        keyword = kwargs.get("keyword", settings.search_keywords[0])
        max_pages = kwargs.get("max_pages", settings.scrape_max_pages)

        from scrapling.fetchers import StealthyFetcher

        jobs: list[ScrapedJob] = []
        seen_titles: set[str] = set()

        for page_num in range(max_pages):
            url = SEARCH_URL.format(keyword=quote_plus(keyword), page=page_num)
            logger.info("Fetching Liepin page %d: %s", page_num, url)

            try:
                page = StealthyFetcher.fetch(url, headless=settings.browser_headless)
            except Exception as e:
                logger.error("Failed to fetch Liepin page %d: %s", page_num, e)
                break

            cards = page.css(SELECTORS["job_card"])
            if not cards:
                logger.warning("No job cards found on page %d, stopping.", page_num)
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

        logger.info("Liepin scrape complete: %d jobs found", len(jobs))
        return jobs


def _parse_card(card: Any) -> ScrapedJob | None:
    """Parse a single Liepin job card element into a ScrapedJob."""
    title = safe_text(card, SELECTORS["title"])
    company = safe_text(card, SELECTORS["company"])

    if not title or not company:
        return None

    location_raw = safe_text(card, SELECTORS["location"])
    location = normalize_location(location_raw) if location_raw else None

    # Try to extract the job detail URL
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
        source_platform="liepin",
        location=location,
        source_url=source_url,
        apply_url=source_url,
    )
