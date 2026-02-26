#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

cd "$BACKEND_DIR"

if [ -f "./gradlew" ]; then
  exec ./gradlew run
fi

if command -v gradle >/dev/null 2>&1; then
  exec gradle run
fi

echo "No Gradle runtime found. Install Gradle or add Gradle Wrapper files under backend/."
echo "Temporary workaround: run with an installed Gradle (e.g., sdkman/apt) then retry."
exit 1
