# FMRO Python Refactor Plan (PC Crawler First)

## Goal

Rebuild FMRO as a **PC-first Python crawler + local data tool**.

- No Android dependency
- No always-on backend dependency
- Manual company-source maintenance
- One-click crawl + filter/sort/export workflow

This plan is designed so Claude Code (or any coding agent) can implement it step by step.

---

## Product Scope (v1)

### In Scope

1. Manage company career-page sources via local config (`companies.yaml`)
2. Crawl and normalize job postings into one schema
3. Store data in SQLite
4. Query/filter/sort locally (CLI first)
5. Export to CSV/Markdown
6. Mark status fields like `bookmarked`, `applied`, `notes`

### Out of Scope (for v1)

- Android app
- Cloud deployment
- Multi-user auth
- Auto scheduler service
- Complex distributed crawling

---

## Recommended Python Stack

### Core

- **Python 3.11+**
- **uv** or **poetry** for package management
- **Typer** for CLI
- **Pydantic v2** for data models and validation
- **SQLModel** (or SQLAlchemy + Alembic) for SQLite persistence

### Crawling

- **requests + BeautifulSoup4 + selectolax** for static pages
- **Playwright (python)** for dynamic JS-rendered pages
- **httpx** for robust HTTP client + timeout/retry control
- Optional: **tenacity** for retry logic

### Export / Table UX

- **pandas** for CSV convenience (optional)
- **tabulate** or **rich** for terminal table display

### Why not Scrapy first?

Scrapy is great, but for this project’s manually-maintained source list and mixed static/dynamic pages, a custom modular pipeline with Playwright fallback is usually faster to ship and easier to control.

If scale grows (hundreds/thousands of sources), migrate to Scrapy later.

---

## Target Repository Layout

Create under `FMRO/pc/`:

```text
pc/
  pyproject.toml
  README.md
  .env.example
  companies.yaml
  migrations/
  fmro_pc/
    __init__.py
    config.py
    logging.py
    models/
      schema.py
      db.py
    sources/
      base.py
      parser_registry.py
      common_extractors.py
      adapters/
        generic_html.py
        boss_zhipin.py
        liepin.py
        shixiseng.py
        custom_company_template.py
    crawl/
      runner.py
      fetcher.py
      browser.py
      dedupe.py
      normalize.py
    storage/
      repository.py
    services/
      job_query.py
      export_service.py
    cli/
      main.py
      commands/
        crawl.py
        jobs.py
        sources.py
        export.py
  tests/
    test_normalize.py
    test_dedupe.py
    test_query_filters.py
```

---

## Unified Job Schema

Use one canonical schema (`JobPosting`) with at least:

- `id` (db pk)
- `source_platform` (boss_zhipin/liepin/shixiseng/career_page/...)
- `source_company_key` (from companies config)
- `company_name`
- `title`
- `location`
- `employment_type` (intern/fulltime/campus/...)
- `posted_at` (nullable)
- `deadline_at` (nullable)
- `apply_url` (required)
- `source_url` (listing/detail source)
- `salary_text` (nullable)
- `description_text` (nullable)
- `tags` (json/text)
- `fingerprint` (dedupe key, indexed unique)
- `is_active` (bool)
- `bookmarked` (bool)
- `applied` (bool)
- `notes` (text)
- `last_seen_at`
- `created_at`, `updated_at`

### Dedupe Fingerprint

Generate deterministic key from normalized:

`company_name + title + apply_url`

Fallback chain for URL absence:

`company_name + title + location + source_url`

---

## companies.yaml Design

```yaml
sources:
  - key: xiaomi_career
    company_name: Xiaomi
    enabled: true
    platform: career_page
    entry_urls:
      - "https://careers.mi.com/..."
    mode: auto   # auto|static|dynamic
    parser: generic_html
    include_keywords: ["robot", "slam", "perception", "embedded", "intern"]
    exclude_keywords: ["senior architect"]
    city_allowlist: ["Beijing", "Shanghai", "Shenzhen"]
    crawl_depth: 1
    notes: "manual maintained"
```

---

## CLI Commands (MVP)

Implement with Typer:

- `fmro sources list`
- `fmro sources validate`
- `fmro crawl run [--source KEY] [--limit N] [--dynamic]`
- `fmro jobs list [--city] [--keyword] [--platform] [--unapplied] [--sort posted_at]`
- `fmro jobs mark-applied --id ID`
- `fmro jobs bookmark --id ID --on/--off`
- `fmro jobs note --id ID --text "..."`
- `fmro export csv --out output/jobs.csv`
- `fmro export md --out output/jobs.md`

---

## Crawl Pipeline Design

### Step Flow

1. Load enabled sources from `companies.yaml`
2. For each source:
   - choose fetch mode (`static` requests / `dynamic` playwright)
   - fetch listing page(s)
   - parse with registered adapter
3. Normalize to unified schema
4. Generate fingerprint + dedupe
5. Upsert to SQLite
6. Mark stale items (`is_active=false`) if not seen in current run
7. Print run summary

### Run Summary Fields

- sources scanned
- pages fetched
- parse success/failure count
- jobs extracted
- jobs inserted
- jobs updated
- jobs deactivated

---

## Migration Strategy from Existing FMRO

Keep existing directories untouched (`android/`, `backend/`) and add new PC module.

### Phased Migration

1. Create `pc/` skeleton and local DB models
2. Port useful normalization and crawler ideas from Kotlin backend
3. Reuse current platform naming conventions (`boss_zhipin`, `liepin`, etc.)
4. Keep old project as reference until Python version reaches parity
5. Optional: archive Android path later

---

## Implementation Milestones

### M1: Foundation (Day 1)

- project skeleton
- CLI entrypoint
- SQLite models + migrations
- config loader (`companies.yaml`)

### M2: Crawl Core (Day 2-3)

- static fetcher + dynamic fetcher
- parser interface + generic parser
- dedupe + upsert
- run summary output

### M3: Query UX (Day 4)

- filter/sort list command
- bookmark/applied/notes commands

### M4: Export + Quality (Day 5)

- CSV/Markdown export
- tests for normalize/dedupe/query
- README with quickstart and examples

### M5: Optional UI (Later)

- Streamlit local dashboard (search/filter/edit status)

---

## Open-Source Framework Option Matrix

### Option A (Recommended now): Typer + SQLModel + Playwright

- Fast to build
- Simple architecture
- Good enough for dozens/hundreds of sources

### Option B: Scrapy + Playwright plugin

- Better at large-scale crawling
- More framework overhead
- Better when crawl volume grows significantly

### Option C: FastAPI local service + simple web UI

- Better interactive UX early
- Slightly heavier than CLI-first

Current recommendation: **Option A first, evolve to B if needed**.

---

## Acceptance Criteria (v1 Done)

1. `fmro crawl run` can crawl at least 3 configured sources successfully
2. Data persists to SQLite with stable dedupe (no duplicate explosion)
3. `fmro jobs list` supports keyword + city + platform filtering
4. Can mark `applied/bookmarked` and attach notes
5. Can export valid CSV and Markdown files
6. Full setup + command usage documented in `pc/README.md`

---

## Claude Code Execution Prompt (copy-ready)

```text
Implement the FMRO Python PC crawler module under FMRO/pc following docs/PYTHON_REFACTOR_PLAN.md.

Requirements:
1) Use Python 3.11+, Typer CLI, Pydantic v2, SQLModel (SQLite), Playwright fallback for dynamic pages.
2) Deliver MVP commands: sources list/validate, crawl run, jobs list/filter, mark-applied, bookmark, note, export csv/md.
3) Add tests for dedupe/normalize/query filters.
4) Keep existing android/ and backend/ untouched.
5) Write clear README with quickstart and command examples.

Implement milestone by milestone and keep commits small.
```

---

## Notes

- This plan intentionally optimizes for **ship speed and practical maintainability**.
- Start with a reliable CLI pipeline first; GUI/cloud can come after data quality is stable.
