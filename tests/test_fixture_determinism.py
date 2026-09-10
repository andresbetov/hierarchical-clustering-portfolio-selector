"""feat-030 contract test: synthetic panels are PYTHONHASHSEED-independent."""

import os
import subprocess
import sys

PANEL_SCRIPT = """
import base64
import sys

sys.path.insert(0, ".")
import conftest

spec = {"AAAA": {}, "BBBB": {"days_missing": [3]}, "CCCC": {"flat": True}}
panel = conftest._build_panel(spec, rows=20, start="2024-01-01")
print(base64.b64encode(panel.to_numpy().tobytes()).decode())
"""


def _panel_bytes_under_seed(pythonhashseed: int) -> str:
    env = {**os.environ, "PYTHONHASHSEED": str(pythonhashseed)}
    proc = subprocess.run(
        [sys.executable, "-c", PANEL_SCRIPT],
        capture_output=True,
        text=True,
        cwd="tests",
        env=env,
        timeout=60,
    )
    assert proc.returncode == 0, f"subprocess failed: {proc.stderr}"
    return proc.stdout.strip()


class TestFixtureDeterminism:
    def test_panel_identical_across_pythonhashseed(self):
        """The same commit must produce byte-identical synthetic panels no
        matter how the interpreter salts string hashes (feat-030)."""
        panel_seed_1 = _panel_bytes_under_seed(1)
        panel_seed_999 = _panel_bytes_under_seed(999)

        assert panel_seed_1, "panel bytes must not be empty"
        assert panel_seed_1 == panel_seed_999


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
