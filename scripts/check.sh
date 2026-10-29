#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$ROOT/.venv/bin/python" "$ROOT/backend/manage.py" check
"$ROOT/.venv/bin/python" -m pytest --junitxml="$ROOT/artifacts/backend-tests.xml"
"$ROOT/.venv/bin/ruff" check "$ROOT/backend"
"$ROOT/.venv/bin/ruff" format --check "$ROOT/backend"
(cd "$ROOT/frontend" && npm run build && npm audit)
