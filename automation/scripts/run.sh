#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

ACTION="${1:-shell}"

cd "$AUTO_DIR"

case "$ACTION" in
  build)
    echo "Building automation image..."
    docker compose build
    ;;
  smoke)
    echo "Running smoke tests..."
    docker compose run --rm automation python -m pytest tests/test_smoke.py -v
    ;;
  test)
    echo "Running all tests..."
    docker compose run --rm automation python -m pytest tests/ -v
    ;;
  crawl)
    shift
    echo "Running crawler orchestrator..."
    docker compose run --rm automation python -m fmro_auto.orchestrator "$@"
    ;;
  shell)
    echo "Launching automation shell..."
    docker compose run --rm automation bash
    ;;
  *)
    echo "Usage: $0 {build|smoke|test|crawl|shell}"
    exit 1
    ;;
esac
