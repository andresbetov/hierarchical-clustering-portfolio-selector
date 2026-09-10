# Proposal: chore-coverage-gate — feat-040

## Why

La suite offline es verde (230 passed) pero sin medición de cobertura: una regresión que deja sin probar un módulo crítico no se detecta. `pyproject.toml:16` declara `pytest>=9.0.3` en `[project].dependencies` (runtime) cuando es herramienta de desarrollo, y `pyproject.toml:29` `dev` no lo contiene — residuo del arranque. `Makefile:25` y `.github/workflows/ci.yml:34` ejecutan `pytest` sin `pytest-cov`, por lo que `make test` nunca reporta cobertura ni falla bajo umbral. Se requiere gate de cobertura (baseline 87% línea / 85% branch medido post-039) y higiene de dependencias para que `uv sync --frozen` siga reproducible sin `pytest` en runtime.

## What Changes

- **Higiene:** mover `pytest>=9.0.3` de `[project].dependencies` a `[dependency-groups].dev|test` y añadir `pytest-cov>=6.0` (trae `coverage>=7.16`). Re-lock `uv.lock` (transitivos `coverage`, `execnet` si aplica).
- **Config cobertura:** `pyproject.toml` añadir `[tool.coverage.run]` (`source = ["portfolio_engine"]`, `branch = true`, `omit = ["*/tests/*"]`), `[tool.coverage.report]` (`show_missing = true`, `fail_under = 85`, `precision = 1`, `exclude_lines` para `pragma: no cover` etc.), `[tool.coverage.html/xml]`, y extender `[tool.pytest.ini_options].addopts` de `"-q"` a `"-q --cov=portfolio_engine --cov-report=term-missing --cov-report=html --cov-report=xml --cov-branch --cov-fail-under=85"` (branch + umbral 85 medido).
- **Makefile:** `test: uv run python -m pytest --cov=...` (explícito) con `test-no-cov` escape hatch, `clean` borra `htmlcov/.coverage/coverage.xml`.
- **CI:** `.github/workflows/ci.yml:34` espeja flags de cobertura y añade `upload-artifact htmlcov` opcional; mantiene `uv sync --frozen` (dev groups default).
- **Docs:** `.gitignore` ya cubre `.coverage/htmlcov/`; `README` `230 tests` y `CHANGELOG` Unreleased update si aplica.

## Capabilities

### New Capabilities
- `coverage-gate`: Gate de cobertura línea+rama 85% en `addopts` + `tool.coverage.*` + Makefile/CI.

### Modified Capabilities
- `project-packaging`: Dependencias justificadas (pytest solo dev).
- `quality-gates`: Harness ejecuta todos los gates incluyendo cobertura.
- `verification-harness`: Target `test` reporta cobertura y falla bajo umbral.

## Impact

- Código: `pyproject.toml`, `uv.lock`, `Makefile`, `.github/workflows/ci.yml`, `README.md` si needed.
- Docs: `CHANGELOG.md` hygiene note.
- Tests: existentes 230 passed deben pasar con ` --cov-fail-under=85`; ningún nuevo test funcional (gate meta).
- Riesgos: umbral 85% exacto sobre branch (87% línea) — caída a 84% fallará (intencionado). Si se añade código sin tests, gate rojo fuerza tests. `uv sync --frozen` debe seguir instalando `dev` (default-groups).
