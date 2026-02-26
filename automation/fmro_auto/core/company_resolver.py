"""Resolve company names to backend company IDs (find or create)."""
from __future__ import annotations

import logging
import re
from typing import Any

from fmro_auto.core.api_client import FMROClient

logger = logging.getLogger(__name__)

# Common suffixes to strip when fuzzy-matching Chinese company names
_STRIP_SUFFIXES = re.compile(
    r"(有限公司|股份有限公司|科技|集团|技术|信息|智能|有限责任公司|控股|（.*?）|\(.*?\))$"
)


def _normalize_name(name: str) -> str:
    """Normalize a company name for fuzzy matching."""
    n = name.strip()
    # Strip common Chinese corporate suffixes iteratively
    for _ in range(5):
        prev = n
        n = _STRIP_SUFFIXES.sub("", n).strip()
        if n == prev:
            break
    return n.lower()


class CompanyResolver:
    """Look up a company by name; create it if not found."""

    def __init__(self, api_client: FMROClient) -> None:
        self._api = api_client
        self._cache: dict[str, str] = {}  # normalized_name -> id string
        self._loaded = False

    def _load_companies(self) -> None:
        """Fetch all companies from backend and populate cache."""
        try:
            companies = self._api.list_companies()
            for c in companies:
                key = _normalize_name(c["name"])
                self._cache[key] = str(c["id"])
            self._loaded = True
        except Exception as e:
            logger.warning("Failed to load companies: %s", e)

    def resolve(self, company_name: str) -> str:
        """Return the company ID for *company_name*, creating if needed."""
        if not self._loaded:
            self._load_companies()

        key = _normalize_name(company_name)

        # Exact match on normalized name
        if key in self._cache:
            return self._cache[key]

        # Substring match: "大疆" should match "深圳市大疆创新科技"
        for cached_key, cid in self._cache.items():
            if key in cached_key or cached_key in key:
                self._cache[key] = cid
                return cid

        # No match — create a new company
        try:
            created = self._api.create_company(name=company_name.strip())
            cid = str(created["id"])
            self._cache[key] = cid
            logger.info("Created company '%s' -> id=%s", company_name, cid)
            return cid
        except Exception as e:
            logger.error("Failed to create company '%s': %s", company_name, e)
            raise
