from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


class SourceConfig(BaseModel):
    key: str
    company_name: str
    enabled: bool = True
    platform: str = "career_page"
    entry_urls: list[str]
    mode: Literal["auto", "static", "dynamic"] = "auto"
    parser: str = "generic_html"
    include_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    city_allowlist: list[str] = Field(default_factory=list)
    request_headers: dict[str, str] = Field(default_factory=dict)
    crawl_depth: int = Field(default=1, ge=1)
    notes: str | None = None

    @field_validator("key", "company_name", "platform", "parser")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value cannot be blank")
        return normalized

    @field_validator("entry_urls")
    @classmethod
    def validate_entry_urls(cls, values: list[str]) -> list[str]:
        if not values:
            raise ValueError("entry_urls must contain at least one URL")

        normalized: list[str] = []
        for value in values:
            url = value.strip()
            if not (url.startswith("http://") or url.startswith("https://")):
                raise ValueError(f"invalid URL: {value}")
            normalized.append(url)
        return normalized

    @field_validator("request_headers")
    @classmethod
    def validate_request_headers(cls, values: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for key, val in values.items():
            k = key.strip()
            v = val.strip()
            if not k or not v:
                continue
            normalized[k] = v
        return normalized


class CompaniesConfig(BaseModel):
    sources: list[SourceConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_source_keys(self) -> CompaniesConfig:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for source in self.sources:
            if source.key in seen:
                duplicates.add(source.key)
            seen.add(source.key)

        if duplicates:
            dupes = ", ".join(sorted(duplicates))
            raise ValueError(f"duplicate source keys: {dupes}")
        return self


def _normalize_cookie_map(raw: dict) -> dict[str, str]:
    cookies = raw.get("cookies", {})
    if not isinstance(cookies, dict):
        return {}

    normalized: dict[str, str] = {}
    for key, value in cookies.items():
        k = str(key).strip()
        v = str(value).strip()
        if k and v:
            normalized[k] = v
    return normalized


def _load_cookie_overrides(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return _normalize_cookie_map(raw)


def _load_cookie_overrides_json(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    return _normalize_cookie_map(raw)


def _apply_cookie_overrides(config: CompaniesConfig, overrides: dict[str, str]) -> CompaniesConfig:
    if not overrides:
        return config

    sources: list[SourceConfig] = []
    for source in config.sources:
        cookie = overrides.get(source.key)
        if not cookie:
            sources.append(source)
            continue

        headers = dict(source.request_headers)
        if not any(k.lower() == "cookie" for k in headers):
            headers["Cookie"] = cookie
        sources.append(source.model_copy(update={"request_headers": headers}))

    return CompaniesConfig(sources=sources)


def load_companies_config(path: str | Path = "companies.yaml") -> CompaniesConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"companies config not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    try:
        config = CompaniesConfig.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"invalid companies config: {exc}") from exc

    json_cookie_path = config_path.parent / "cookies.json"
    local_cookie_path = config_path.parent / "cookies.local.yaml"

    cookie_overrides = _load_cookie_overrides_json(json_cookie_path)
    local_overrides = _load_cookie_overrides(local_cookie_path)
    cookie_overrides.update(local_overrides)

    return _apply_cookie_overrides(config, cookie_overrides)


def select_sources(
    config: CompaniesConfig,
    source_key: str | None = None,
    only_enabled: bool = True,
) -> list[SourceConfig]:
    sources = config.sources
    if source_key:
        sources = [source for source in sources if source.key == source_key]
        if not sources:
            raise ValueError(f"source '{source_key}' was not found in companies config")

    if only_enabled:
        sources = [source for source in sources if source.enabled]

    return sources
