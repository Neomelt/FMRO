#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/publish_to_github.sh Neomelt FMRO

OWNER="${1:-Neomelt}"
REPO="${2:-FMRO}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -n "${GITHUB_TOKEN:-}" ]; then
  echo "GITHUB_TOKEN detected, attempting to create repo via API..."
  curl -fsS -X POST "https://api.github.com/user/repos" \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -d "{\"name\":\"${REPO}\",\"private\":false}" || true
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

rsync -a --exclude '.git' "$ROOT_DIR/" "$TMP_DIR/$REPO/"
cd "$TMP_DIR/$REPO"

git init -b main >/dev/null
git add .
git commit -m "Initial FMRO import" >/dev/null

git remote add origin "git@github.com:${OWNER}/${REPO}.git"
git push -u origin main

echo "Done: pushed FMRO to git@github.com:${OWNER}/${REPO}.git"
