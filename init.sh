#!/bin/bash
set -e

echo "=== Harness Initialization ==="

if command -v uv >/dev/null 2>&1; then
  echo "=== Syncing dependencies with uv ==="
  uv sync --frozen
else
  echo "=== uv not found — skipping uv sync (install uv to enable full sync) ==="
fi

echo "=== Running pytest (offline) ==="
if command -v uv >/dev/null 2>&1; then
  # Prefer the project interpreter: uv sync puts pytest in .venv, system python3 may not see it.
  # exit 5 = no tests collected — not a failure for harness bootstrap.
  uv run python -m pytest || [ $? -eq 5 ]

  echo "=== Lint (ruff) ==="
  # Fail loud, never skip. ruff is a dev dependency (pyproject.toml
  # [dependency-groups].dev), so a completed `uv sync --frozen` must have
  # installed it. Skipping here would let ./init.sh report success without
  # running the lint gate, which the quality-gates spec forbids: "ningún gate
  # queda silenciosamente omitido si sus herramientas están instaladas por uv".
  if uv run ruff --version >/dev/null 2>&1; then
    uv run ruff check .
  else
    echo "ERROR: ruff is not runnable after 'uv sync --frozen', so the lint gate did not run." >&2
    echo "       Refusing to report success on an incomplete verification." >&2
    echo "       Fix: run 'uv sync --frozen' and confirm ruff lands in .venv." >&2
    exit 1
  fi

  echo "=== Type check (pyright) ==="
  # Same reasoning as ruff: a dev dependency that must be present after a
  # completed sync, so a missing one is a broken environment, not a skip.
  if uv run pyright --version >/dev/null 2>&1; then
    uv run pyright
  else
    echo "ERROR: pyright is not runnable after 'uv sync --frozen', so the types gate did not run." >&2
    echo "       Refusing to report success on an incomplete verification." >&2
    echo "       Fix: run 'uv sync --frozen' and confirm pyright lands in .venv." >&2
    exit 1
  fi
elif python3 -c "import pytest" 2>/dev/null; then
  # exit 5 = no tests collected — not a failure for harness bootstrap
  python3 -m pytest || [ $? -eq 5 ]
else
  echo "pytest not installed — skipping pytest (run 'uv sync' or 'pip install pytest' to enable)"
fi

echo "=== Checking syntax (compileall) ==="
python3 -m compileall -q -x '(^|/)(\.?venv|env|node_modules|build|dist|__pycache__)(/|$)' .

echo "=== Verification Complete ==="
echo ""
echo "Next steps:"
echo "1. Read feature_list.json to see current feature state"
echo "2. Pick ONE unfinished feature to work on"
echo "3. Implement only that feature"
echo "4. Re-run ./init.sh before claiming done (fresh evidence)"
