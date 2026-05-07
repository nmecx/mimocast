#!/usr/bin/env bash
# Quickstart: install in editable mode, run the mock demo, print outputs.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$HERE")"

cd "$ROOT"

python -m pip install -e ".[dev]" --quiet

python -m mimocast run \
  "$HERE/sample_doc.md" \
  --mock \
  --dry-run \
  --max-sections 4 \
  --out "$HERE/out"

echo
echo "Slides + audio written to: $HERE/out/"
