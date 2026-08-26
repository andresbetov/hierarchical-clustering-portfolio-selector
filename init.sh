#!/bin/bash
set -e

echo "=== Harness Initialization ==="

if command -v uv >/dev/null 2>&1; then
  echo "=== Syncing dependencies with uv ==="
  uv sync
else
  echo "=== uv not found — skipping uv sync (install uv to enable full sync) ==="
fi

echo "=== Running pytest (offline) ==="
if python3 -c "import pytest" 2>/dev/null; then
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
