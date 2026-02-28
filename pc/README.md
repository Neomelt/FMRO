# FMRO PC Crawler

PC-first Python crawler and local job data tool for FMRO.

This module is intentionally isolated under `FMRO/pc` and does not depend on `android/` or `backend/`.

## Features in this milestone

- Typer CLI entrypoint: `fmro`
- Source config loader from `companies.yaml`
- SQLModel SQLite persistence and `db init`
- Crawl pipeline with:
  - static fetcher (`httpx` + `BeautifulSoup`)
  - optional Playwright dynamic fallback stub
  - parser interface + `generic_html` adapter
  - normalization + fingerprint dedupe + upsert
- Commands:
  - `fmro sources list`
  - `fmro sources validate`
  - `fmro crawl run`
  - `fmro jobs list`
  - `fmro export csv`
- Basic tests for dedupe and normalize

## Quickstart

1. Install dependencies

```bash
cd /home/neomelt/FMRO/pc
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

2. Validate source config

```bash
fmro sources validate --config companies.yaml
fmro sources list --config companies.yaml
```

3. Initialize database

```bash
fmro db init
```

4. Run crawl

```bash
fmro crawl run --config companies.yaml
```

5. Query jobs

```bash
fmro jobs list --keyword python --limit 20
fmro jobs list --city Shanghai --platform career_page
```

6. Export CSV

```bash
fmro export csv --out output/jobs.csv
```

## Optional dynamic crawl support (Playwright)

```bash
pip install -e .[dynamic]
playwright install chromium
```

Then run:

```bash
fmro crawl run --dynamic
```

## Project layout

```text
pc/
  pyproject.toml
  companies.yaml
  README.md
  fmro_pc/
    cli/main.py
    config.py
    database.py
    models.py
    crawl/
    parsers/
    storage/
  tests/
```
