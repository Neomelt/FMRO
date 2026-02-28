from __future__ import annotations

import hashlib


def _normalize_token(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())


def build_fingerprint(
    *,
    company_name: str,
    title: str,
    apply_url: str | None,
    location: str | None,
    source_url: str | None,
) -> str:
    company_norm = _normalize_token(company_name)
    title_norm = _normalize_token(title)
    apply_url_norm = _normalize_token(apply_url)

    if apply_url_norm:
        payload = "|".join([company_norm, title_norm, apply_url_norm])
    else:
        location_norm = _normalize_token(location)
        source_url_norm = _normalize_token(source_url)
        payload = "|".join([company_norm, title_norm, location_norm, source_url_norm])

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
