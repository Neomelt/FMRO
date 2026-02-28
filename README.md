# FMRO

Find Much Robot Offer.

FMRO is now a Python-first local crawler + web dashboard for robotics internship hunting.

## Current Architecture

- `pc/` Python crawler, local SQLite storage, CLI, Streamlit web UI
- `backend/` legacy Kotlin backend (kept for reference)
- `docs/` product and engineering notes
- `infra/` legacy schema/migration assets

## Quick Start (Current)

```bash
cd pc
UV_CACHE_DIR=/tmp/uv-cache uv sync --extra dev
UV_CACHE_DIR=/tmp/uv-cache uv run fmro db init
UV_CACHE_DIR=/tmp/uv-cache uv run fmro crawl run --config companies.yaml
UV_CACHE_DIR=/tmp/uv-cache uv run streamlit run fmro_pc/web/app.py
```

Open the Streamlit URL shown in terminal (usually `http://localhost:8501`).

## CLI Examples

```bash
cd pc
UV_CACHE_DIR=/tmp/uv-cache uv run fmro jobs list --unapplied --sort updated_at
UV_CACHE_DIR=/tmp/uv-cache uv run fmro jobs mark-applied --id 42
UV_CACHE_DIR=/tmp/uv-cache uv run fmro export csv --out output/jobs.csv
UV_CACHE_DIR=/tmp/uv-cache uv run fmro export md --out output/jobs.md
```

## CI/CD

- CI: `FMRO/.github/workflows/ci.yml`
- Release: `FMRO/.github/workflows/release.yml`

## Publish to GitHub

```bash
./scripts/publish_to_github.sh Neomelt FMRO
```
