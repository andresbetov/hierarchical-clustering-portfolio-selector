## 1. Manifiestos

- [x] 1.1 `pyproject.toml`: requires-python >=3.11, `scikit-learn>=1.8` en dependencies, ruff target-version py311 — verificar: `uv sync` re-resuelve sin error
- [x] 1.2 `.github/workflows/ci.yml`: matriz ["3.11", "3.12", "3.13"] — verificar: YAML válido y jobs esperados

## 2. Lock y reproducción

- [x] 2.1 `uv lock` universal (entran scikit-learn + joblib + threadpoolctl + narwhals) — verificar: diff de uv.lock contiene exactamente esas adiciones
- [x] 2.2 `uv sync --frozen` desde estado limpio + `uv run python -c "import sklearn; print(sklearn.__version__)"` — verificar: reproduce sin re-resolver e importa

## 3. Documentación y verificación integral

- [x] 3.1 CHANGELOG Unreleased: entrada breaking (drop python 3.10) — verificar: texto en formato KaC
- [x] 3.2 `./init.sh` completo exit 0 con suite verde + gates — output registrado como evidencia
