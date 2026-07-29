#!/usr/bin/env bash
# Fail when a Python app stack exists but pytest is missing from deps, config, or CI.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EX_PYPROJECT="$ROOT/examples/python/pyproject.toml"
ROOT_PYPROJECT="$ROOT/pyproject.toml"
CI_WORKFLOW="$ROOT/.github/workflows/ci.yml"

# Prefer examples/python Golden Path; else root pyproject for product apps (TakeIn SMS).
if [ -f "$EX_PYPROJECT" ]; then
  PYPROJECT="$EX_PYPROJECT"
  MODE="examples"
elif [ -f "$ROOT_PYPROJECT" ]; then
  PYPROJECT="$ROOT_PYPROJECT"
  MODE="root"
else
  echo "Python pytest workflow check skipped (no pyproject.toml)"
  exit 0
fi

ERRORS=0

fail() {
  echo "FAIL: $1"
  ERRORS=$((ERRORS + 1))
}

if ! grep -qE 'pytest' "$PYPROJECT"; then
  fail "$PYPROJECT must declare pytest in dependencies"
fi

if ! grep -qE '^\[tool\.pytest\.ini_options\]' "$PYPROJECT"; then
  fail "$PYPROJECT must define [tool.pytest.ini_options]"
fi

if [ ! -f "$CI_WORKFLOW" ]; then
  fail ".github/workflows/ci.yml missing"
elif ! grep -qE 'pytest' "$CI_WORKFLOW"; then
  fail ".github/workflows/ci.yml must run pytest when Python stack is present"
fi

if [ "$MODE" = "examples" ]; then
  if ! grep -qE 'python-test.*uv run pytest|uv run pytest' "$ROOT/scripts/feature-gate.sh"; then
    fail "scripts/feature-gate.sh must run uv run pytest for the python stack"
  fi
fi

if [ "$ERRORS" -gt 0 ]; then
  echo "$ERRORS python pytest workflow check(s) failed"
  exit 1
fi

echo "Python pytest workflow check passed ($MODE)"
