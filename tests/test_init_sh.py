"""Contract tests for `init.sh`, the single local verification gate.

`init.sh` decides whether a feature can be marked done, so it must never
report success on an incomplete verification. Two specs constrain it and
these tests pin both:

- `quality-gates`: "ningún gate queda silenciosamente omitido si sus
  herramientas están instaladas por uv" — so a gate whose tool is missing
  after `uv sync --frozen` must FAIL, not skip.
- `verification-harness`: "WHEN el entorno no tiene uv ni pytest
  instalable THEN init.sh continúa con compileall y termina exit 0
  (comportamiento bootstrap preservado)" — so a missing uv must still
  exit 0.

The script is exercised as a subprocess with a stubbed `uv` on PATH and
run from an empty directory, so there is no real dependency sync, no real
pytest recursion, and no compileall walk over the repository. Precedent
for subprocess-level tests: `test_fixture_determinism.py`.
"""

from __future__ import annotations

import shutil
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
INIT_SH = REPO_ROOT / "init.sh"

# A PATH with no `uv`: uv lives outside /usr/bin and /bin on the supported
# environments, so this yields a genuinely uv-less environment while keeping
# a real python3 for compileall.
NO_UV_PATH = "/usr/bin:/bin"

STUB_TEMPLATE = """#!/bin/bash
# Stub uv: sync succeeds, pytest is instant, gate availability is configurable.
case "$1 $2" in
  "run python")
      if [ "${{3:-}}" = "-m" ] && [ "${{4:-}}" = "pytest" ]; then
          echo "367 passed"
          exit 0
      fi
      exit 1 ;;                       # any module probe: not installed
  "run ruff")     {ruff} ;;
  "run pyright")  {pyright} ;;
  "sync --frozen") echo "Resolved 56 packages" ; exit 0 ;;
esac
exit 0
"""

requires_bash = pytest.mark.skipif(shutil.which("bash") is None, reason="requires bash")


def run_init(tmp_path: Path, *, uv_available: bool, ruff: str, pyright: str) -> subprocess.CompletedProcess:
    """Run a copy of init.sh from an empty directory with a stubbed uv."""
    workdir = tmp_path / "work"
    workdir.mkdir()
    script = workdir / "init.sh"
    shutil.copy2(INIT_SH, script)
    script.chmod(script.stat().st_mode | stat.S_IEXEC)

    path = NO_UV_PATH
    if uv_available:
        bindir = tmp_path / "bin"
        bindir.mkdir()
        stub = bindir / "uv"
        stub.write_text(STUB_TEMPLATE.format(ruff=ruff, pyright=pyright))
        stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
        path = f"{bindir}:{NO_UV_PATH}"

    return subprocess.run(
        ["bash", str(script)],
        cwd=workdir,
        env={"PATH": path, "HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_init_sh_exists_and_is_executable() -> None:
    assert INIT_SH.is_file(), "init.sh must stay at the repo root"
    assert INIT_SH.stat().st_mode & stat.S_IXUSR, "init.sh must remain executable"


@requires_bash
def test_all_gates_present_exits_zero(tmp_path: Path) -> None:
    """Happy path: uv, pytest, ruff and pyright all available."""
    result = run_init(tmp_path, uv_available=True, ruff="exit 0", pyright="exit 0")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Verification Complete" in result.stdout
    for gate in ("Lint (ruff)", "Type check (pyright)"):
        assert gate in result.stdout, f"{gate} never ran"


@requires_bash
def test_missing_ruff_fails_instead_of_skipping(tmp_path: Path) -> None:
    """quality-gates: a gate tool missing after a completed sync must not be skipped."""
    result = run_init(tmp_path, uv_available=True, ruff="exit 127", pyright="exit 0")
    assert result.returncode != 0, "a skipped lint gate must not report success"
    assert "Verification Complete" not in result.stdout
    assert "lint gate did not run" in result.stderr


@requires_bash
def test_missing_pyright_fails_instead_of_skipping(tmp_path: Path) -> None:
    """Same contract for the types gate."""
    result = run_init(tmp_path, uv_available=True, ruff="exit 0", pyright="exit 127")
    assert result.returncode != 0, "a skipped types gate must not report success"
    assert "Verification Complete" not in result.stdout
    assert "types gate did not run" in result.stderr


@requires_bash
def test_missing_uv_still_exits_zero_for_bootstrap(tmp_path: Path) -> None:
    """verification-harness: the bootstrap path without uv must be preserved."""
    result = run_init(tmp_path, uv_available=False, ruff="exit 0", pyright="exit 0")
    assert result.returncode == 0, "uv-less bootstrap behaviour is spec-required"
    assert "uv not found" in result.stdout
    assert "Checking syntax (compileall)" in result.stdout
    assert "Verification Complete" in result.stdout
