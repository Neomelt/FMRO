#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

UV_CACHE_DIR=${UV_CACHE_DIR:-/tmp/uv-cache}

echo "[1/4] Run local live crawl (you may be prompted for login confirmation)..."
uv run fmro crawl live --config companies.yaml --db data/fmro_pc.db --source boss_robot_search || true
uv run fmro crawl live --config companies.yaml --db data/fmro_pc.db --source liepin_robot_search || true
uv run fmro crawl live --config companies.yaml --db data/fmro_pc.db --source shixiseng_robot_search || true

echo "[2/4] Export snapshots..."
uv run fmro export csv --db data/fmro_pc.db --out output/jobs.csv
uv run fmro export md --db data/fmro_pc.db --out output/jobs.md

echo "[3/4] Commit snapshots..."
git add data/fmro_pc.db output/jobs.csv output/jobs.md
if git diff --cached --quiet; then
  echo "No snapshot changes."
  exit 0
fi

git commit -m "chore(snapshot): refresh local crawl data"

echo "[4/4] Push..."
git push

echo "Done. GitHub Action will publish updated pages."