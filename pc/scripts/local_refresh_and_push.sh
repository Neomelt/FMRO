#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

UV_CACHE_DIR=${UV_CACHE_DIR:-/tmp/uv-cache}

echo "[1/4] Try cookie-based crawl first (no manual login)..."
uv run fmro crawl run --config companies.yaml --db data/fmro_pc.db --dynamic --engine auto || true

echo "[2/4] Fallback live crawl only when needed..."
uv run fmro jobs list --db data/fmro_pc.db --limit 1 >/tmp/fmro_jobs_count.txt || true
if grep -q "No jobs found" /tmp/fmro_jobs_count.txt; then
  echo "Cookie crawl returned no jobs, falling back to live mode."
  uv run fmro crawl live --config companies.yaml --db data/fmro_pc.db --source boss_robot_search || true
  uv run fmro crawl live --config companies.yaml --db data/fmro_pc.db --source liepin_robot_search || true
  uv run fmro crawl live --config companies.yaml --db data/fmro_pc.db --source shixiseng_robot_search || true
else
  echo "Cookie crawl has data, skip live login flow."
fi

echo "[3/4] Export snapshots..."
uv run fmro export csv --db data/fmro_pc.db --out output/jobs.csv
uv run fmro export md --db data/fmro_pc.db --out output/jobs.md

echo "[4/5] Commit snapshots..."
git add data/fmro_pc.db output/jobs.csv output/jobs.md
if git diff --cached --quiet; then
  echo "No snapshot changes."
  exit 0
fi

git commit -m "chore(snapshot): refresh local crawl data"

echo "[5/5] Push..."
git push

echo "Done. GitHub Action will publish updated pages."