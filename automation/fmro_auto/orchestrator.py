"""CLI orchestrator: run one or more platform adapters."""
from __future__ import annotations

import argparse
import logging
import sys

from fmro_auto.core.api_client import FMROClient
from fmro_auto.core.browser import BrowserManager
from fmro_auto.core.company_resolver import CompanyResolver
from fmro_auto.core.config import settings

ADAPTER_MAP = {
    "liepin": "fmro_auto.adapters.liepin.LiepinAdapter",
    "shixiseng": "fmro_auto.adapters.shixiseng.ShixisengAdapter",
}


def _import_adapter(dotted_path: str):
    """Import an adapter class from a dotted module path."""
    module_path, class_name = dotted_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def main() -> None:
    parser = argparse.ArgumentParser(description="FMRO Crawler Orchestrator")
    parser.add_argument(
        "--adapters",
        nargs="+",
        choices=list(ADAPTER_MAP.keys()) + ["all"],
        default=["all"],
        help="Which adapters to run (default: all)",
    )
    parser.add_argument("--keyword", default=None, help="Search keyword")
    parser.add_argument("--max-pages", type=int, default=None, help="Max pages to scrape")
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    )
    logger = logging.getLogger("orchestrator")

    keyword = args.keyword or settings.search_keywords[0]
    max_pages = args.max_pages or settings.scrape_max_pages

    adapter_names = args.adapters
    if "all" in adapter_names:
        adapter_names = list(ADAPTER_MAP.keys())

    logger.info("Starting crawl: adapters=%s keyword='%s' max_pages=%d",
                adapter_names, keyword, max_pages)

    total_scraped = 0
    total_submitted = 0

    with FMROClient() as api:
        resolver = CompanyResolver(api)
        browser = BrowserManager()

        for name in adapter_names:
            dotted = ADAPTER_MAP.get(name)
            if not dotted:
                logger.error("Unknown adapter: %s", name)
                continue

            adapter_cls = _import_adapter(dotted)
            adapter = adapter_cls(api_client=api, browser_manager=browser)
            adapter.resolver = resolver

            logger.info("Running %s adapter...", name)
            try:
                jobs = adapter.scrape(keyword=keyword, max_pages=max_pages)
                total_scraped += len(jobs)
                submitted = adapter.submit_results(jobs, confidence=0.7)
                total_submitted += submitted
                logger.info("%s: scraped=%d submitted=%d", name, len(jobs), submitted)
            except Exception as e:
                logger.error("%s adapter failed: %s", name, e)

    logger.info("Crawl complete: total_scraped=%d total_submitted=%d",
                total_scraped, total_submitted)
    print(f"\nDone: {total_scraped} jobs scraped, {total_submitted} submitted to review queue.")


if __name__ == "__main__":
    main()
