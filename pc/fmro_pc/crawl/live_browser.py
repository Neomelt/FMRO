from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from fmro_pc.config import CompaniesConfig, SourceConfig, select_sources
from fmro_pc.crawl.normalize import matches_source_filters, normalize_job
from fmro_pc.parsers.base import ParsedJob
from fmro_pc.storage.repository import UpsertStats, upsert_jobs


@dataclass
class LiveSourceResult:
    source_key: str
    extracted: int
    normalized: int
    upsert: UpsertStats
    errors: list[str]


def _extract_jobs_for_source(page, source: SourceConfig) -> list[ParsedJob]:
    platform = source.platform

    if platform == "boss_zhipin":
        script = """
() => {
  const selectors = [
    'a[href*="/job_detail/"]',
    '.job-card-wrapper a',
    '.job-list-box a',
    'a[ka*="job"]',
    'a[href*="zhipin.com"]'
  ];
  const selected = selectors.flatMap(s => Array.from(document.querySelectorAll(s)));
  const anchors = Array.from(new Set(selected));
  return anchors.map(a => {
    const card = a.closest('li,div,section,article') || a.parentElement;
    const title = (a.getAttribute('title') || a.textContent || '').trim();
    const text = (card?.textContent || '').trim();
    let href = a.href || a.getAttribute('href') || '';
    const jid = a.getAttribute('data-jid') || a.dataset?.jid || '';
    if (!href && jid) {
      href = `https://www.zhipin.com/job_detail/${jid}.html`;
    }
    return { title, href, text };
  });
}
"""
    elif platform == "liepin":
        script = """
() => {
  const selectors = [
    'a[href*="/job/"]',
    '.job-card a',
    '.job-list-item a',
    'a[data-nick="job-detail"]',
    'a[href*="liepin.com/job"]'
  ];
  const selected = selectors.flatMap(s => Array.from(document.querySelectorAll(s)));
  const anchors = Array.from(new Set(selected));
  return anchors.map(a => {
    const card = a.closest('li,div,section,article') || a.parentElement;
    const title = (a.getAttribute('title') || a.textContent || '').trim();
    const text = (card?.textContent || '').trim();
    const href = a.href || a.getAttribute('href') || '';
    return { title, href, text };
  });
}
"""
    elif platform == "shixiseng":
        script = """
() => {
  const cards = Array.from(document.querySelectorAll('a[href*="/intern/"]'));
  return cards.map(a => {
    const card = a.closest('li,div,section,article') || a.parentElement;
    const title = (a.getAttribute('title') || a.textContent || '').trim();
    const text = (card?.textContent || '').trim();
    const href = a.href || a.getAttribute('href') || '';
    return { title, href, text };
  });
}
"""
    else:
        script = """
() => {
  const cards = Array.from(document.querySelectorAll('a[href]'));
  return cards.map(a => {
    const card = a.closest('li,div,section,article') || a.parentElement;
    const title = (a.getAttribute('title') || a.textContent || '').trim();
    const text = (card?.textContent || '').trim();
    const href = a.href || a.getAttribute('href') || '';
    return { title, href, text };
  });
}
"""

    rows = page.evaluate(script)
    parsed: list[ParsedJob] = []
    seen: set[str] = set()
    for row in rows:
        title = (row.get("title") or "").strip()
        href = (row.get("href") or "").strip()
        if len(title) < 4 or not href:
            continue
        if href in seen:
            continue
        seen.add(href)

        parsed.append(
            ParsedJob(
                title=title,
                apply_url=urljoin(page.url, href),
                source_url=page.url,
                description_text=(row.get("text") or "").strip() or None,
                tags=[source.platform],
            )
        )
    return parsed


def crawl_live(
    session,
    config: CompaniesConfig,
    *,
    source_key: str | None = None,
    max_scroll_rounds: int = 8,
) -> list[LiveSourceResult]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright not installed. Run: uv sync --extra dynamic") from exc

    sources = select_sources(config, source_key=source_key, only_enabled=True)
    results: list[LiveSourceResult] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        for source in sources:
            errors: list[str] = []
            page = context.new_page()
            page.goto(source.entry_urls[0], wait_until="domcontentloaded", timeout=30000)
            prompt = (
                f"[{source.key}] 请在浏览器中确认已登录并看到职位列表，"
                "完成后回终端按 Enter 开始抓取..."
            )
            input(prompt)

            for _ in range(max_scroll_rounds):
                page.mouse.wheel(0, 4500)
                page.wait_for_timeout(700)

            extracted = _extract_jobs_for_source(page, source)

            normalized = []
            for job in extracted:
                try:
                    item = normalize_job(job, source)
                    if matches_source_filters(item, source):
                        normalized.append(item)
                except Exception as exc:  # noqa: BLE001
                    errors.append(str(exc))

            if extracted and not normalized:
                preview = ", ".join(job.title[:20] for job in extracted[:5])
                errors.append(f"all extracted jobs were filtered out, sample titles: {preview}")

            upsert = upsert_jobs(session, normalized, source_key=source.key)
            results.append(
                LiveSourceResult(
                    source_key=source.key,
                    extracted=len(extracted),
                    normalized=len(normalized),
                    upsert=upsert,
                    errors=errors,
                )
            )
            page.close()

        browser.close()

    return results
