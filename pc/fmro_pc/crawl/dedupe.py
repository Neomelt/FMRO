from __future__ import annotations

import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TRACKING_QUERY_KEYS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "spm",
    "from",
    "fromid",
    "sessionid",
}


def _normalize_token(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())


def _canonicalize_url(value: str | None) -> str:
    token = _normalize_token(value)
    if not token:
        return ""

    try:
        split = urlsplit(token)
    except Exception:
        return token

    if not split.scheme or not split.netloc:
        return token

    host = split.netloc.lower()
    if host.startswith("www."):
        host = host[4:]

    path = split.path.rstrip("/") or "/"

    pairs = parse_qsl(split.query, keep_blank_values=False)
    kept = []
    for key, val in pairs:
        k = key.lower()
        if k in _TRACKING_QUERY_KEYS:
            continue
        kept.append((k, val.strip()))

    query = urlencode(sorted(kept), doseq=True)
    return urlunsplit((split.scheme.lower(), host, path, query, ""))


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
    apply_url_norm = _canonicalize_url(apply_url)

    if apply_url_norm:
        payload = "|".join([company_norm, title_norm, apply_url_norm])
    else:
        location_norm = _normalize_token(location)
        source_url_norm = _canonicalize_url(source_url)
        payload = "|".join([company_norm, title_norm, location_norm, source_url_norm])

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
