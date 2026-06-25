#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="${PYTHON_BIN:-python3}"
fi

if ! "$PYTHON" -m pytest --version >/dev/null 2>&1; then
  echo "pytest is not available. Run npm run setup first." >&2
  exit 1
fi

PYTHONPATH=. "$PYTHON" -m pytest backend/tests -q
