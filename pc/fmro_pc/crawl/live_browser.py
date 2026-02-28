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


def _safe_eval_rows(page, script: str) -> list[dict]:
    last_exc = None
    for _ in range(3):
        try:
            page.wait_for_load_state("domcontentloaded", timeout=5000)
            rows = page.evaluate(script)
            if isinstance(rows, list):
                return rows
            return []
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            page.wait_for_timeout(400)
    raise RuntimeError(f"evaluate failed after retries: {last_exc}")


def _extract_jobs_for_source(page, source: SourceConfig) -> list[ParsedJob]:
    platform = source.platform

    if platform == "boss_zhipin":
        script = """
() => {
  const rows = [];

  const anchorSelectors = [
    'a[href*="/job_detail/"]',
    '.job-card-wrapper a',
    '.job-list-box a',
    'a[ka*="job"]',
    'a[href*="zhipin.com"]'
  ];
  const pickedAnchors = anchorSelectors.flatMap(
    s => Array.from(document.querySelectorAll(s))
  );
  const anchors = Array.from(new Set(pickedAnchors));
  for (const a of anchors) {
    const card = a.closest('li,div,section,article') || a.parentElement;
    const title = (a.getAttribute('title') || a.textContent || '').trim();
    const text = (card?.textContent || '').trim();
    let href = a.href || a.getAttribute('href') || '';
    const jid = a.getAttribute('data-jid') || a.dataset?.jid || '';
    if (!href && jid) href = `https://www.zhipin.com/job_detail/${jid}.html`;
    rows.push({ title, href, text });
  }

  const cardSelectors = ['.job-card-wrapper', '.search-job-result li', 'li.job-card-wrapper'];
  const pickedCards = cardSelectors.flatMap(
    s => Array.from(document.querySelectorAll(s))
  );
  const cards = Array.from(new Set(pickedCards));
  for (const card of cards) {
    const titleEl = card.querySelector('[class*="title"], [class*="job-name"], h2, h3, a');
    const title = (titleEl?.getAttribute('title') || titleEl?.textContent || '').trim();
    const linkEl = card.querySelector('a[href]');
    const href = (linkEl?.href || linkEl?.getAttribute('href') || '').trim();
    const text = (card.textContent || '').trim();
    rows.push({ title, href, text });
  }

  return rows;
}
"""
    elif platform == "liepin":
        script = """
() => {
  const rows = [];

  const anchorSelectors = [
    'a[href*="/job/"]',
    '.job-card a',
    '.job-list-item a',
    'a[data-nick="job-detail"]',
    'a[href*="liepin.com/job"]'
  ];
  const pickedAnchors = anchorSelectors.flatMap(
    s => Array.from(document.querySelectorAll(s))
  );
  const anchors = Array.from(new Set(pickedAnchors));
  for (const a of anchors) {
    const card = a.closest('li,div,section,article') || a.parentElement;
    const title = (a.getAttribute('title') || a.textContent || '').trim();
    const text = (card?.textContent || '').trim();
    const href = a.href || a.getAttribute('href') || '';
    rows.push({ title, href, text });
  }

  const cardSelectors = ['.job-list-item', '.job-card-pc-container', '.job-card'];
  const pickedCards = cardSelectors.flatMap(
    s => Array.from(document.querySelectorAll(s))
  );
  const cards = Array.from(new Set(pickedCards));
  for (const card of cards) {
    const titleEl = card.querySelector('[class*="title"], [class*="job"], h2, h3, a');
    const title = (titleEl?.getAttribute('title') || titleEl?.textContent || '').trim();
    const linkEl = card.querySelector('a[href]');
    const href = (linkEl?.href || linkEl?.getAttribute('href') || '').trim();
    const text = (card.textContent || '').trim();
    rows.push({ title, href, text });
  }

  return rows;
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

    rows = _safe_eval_rows(page, script)
    if platform == "boss_zhipin" and not rows:
        fallback_script = """
() => {
  const selectors = '[class*="job-name"], [class*="job-title"], h2, h3';
  const titles = Array.from(document.querySelectorAll(selectors));
  return titles.map(el => {
    const card = el.closest('li,div,section,article') || el.parentElement;
    const title = (el.textContent || '').trim();
    const linkEl = card?.querySelector('a[href]');
    const href = (linkEl?.href || linkEl?.getAttribute('href') || '').trim();
    const text = (card?.textContent || '').trim();
    return { title, href, text };
  });
}
"""
        rows = _safe_eval_rows(page, fallback_script)

    parsed: list[ParsedJob] = []
    seen: set[str] = set()
    for row in rows:
        title = (row.get("title") or "").strip()
        href = (row.get("href") or "").strip()
        if len(title) < 4:
            continue

        apply_url = urljoin(page.url, href) if href else page.url
        dedupe_key = f"{title}|{apply_url}"
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        parsed.append(
            ParsedJob(
                title=title,
                apply_url=apply_url,
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
            all_extracted: list[ParsedJob] = []
            normalized: list = []
            page = context.new_page()

            try:
                seed_url = source.entry_urls[0]
                page.goto(seed_url, wait_until="domcontentloaded", timeout=30000)
                prompt = (
                    f"[{source.key}] 请在浏览器中确认已登录并看到职位列表，"
                    "完成后回终端按 Enter 开始抓取..."
                )
                input(prompt)

                for url in source.entry_urls:
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    except Exception as exc:  # noqa: BLE001
                        errors.append(f"goto failed for {url}: {exc}")
                        continue

                    for _ in range(max_scroll_rounds):
                        page.mouse.wheel(0, 4500)
                        page.wait_for_timeout(700)

                    batch = _extract_jobs_for_source(page, source)
                    all_extracted.extend(batch)
                    if not batch:
                        title = page.title()
                        errors.append(f"no rows extracted on {url} (page title: {title})")

                for job in all_extracted:
                    try:
                        item = normalize_job(job, source)
                        if matches_source_filters(item, source):
                            normalized.append(item)
                    except Exception as exc:  # noqa: BLE001
                        errors.append(str(exc))

                if all_extracted and not normalized:
                    preview = ", ".join(job.title[:20] for job in all_extracted[:5])
                    errors.append(f"all extracted jobs were filtered out, sample titles: {preview}")

            except Exception as exc:  # noqa: BLE001
                errors.append(f"live crawl fatal error: {exc}")
            finally:
                page.close()

            upsert = upsert_jobs(session, normalized, source_key=source.key)
            results.append(
                LiveSourceResult(
                    source_key=source.key,
                    extracted=len(all_extracted),
                    normalized=len(normalized),
                    upsert=upsert,
                    errors=errors,
                )
            )

        browser.close()

    return results
