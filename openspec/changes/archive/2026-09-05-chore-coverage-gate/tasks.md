## 1. Higiene de dependencias (baseline medido)

- [x] 1.1 Medir baseline con `uv run pytest --cov=portfolio_engine --cov-report=term-missing --cov-branch` sobre 230 tests: verificar 85% branch / 87% línea (1509 stmts). Registrar `TOTAL 85%` en evidence. (Ya medido 2026-09-05: 85 branch, 87 line).
- [x] 1.2 `pyproject.toml` mover `pytest>=9.0.3` de `[project].dependencies` a `[dependency-groups].dev` y añadir `pytest-cov>=6.0` (+ `coverage` transitivo), mantener `ruff/pyright/hypothesis` en dev, `uv lock --check`/`uv sync --frozen` reproducible y `uv run pytest --version` ok en 3.11-3.13. Verificar `grep -c pytest pyproject.toml` runtime 0, dev >=2.

## 2. Configuración de cobertura (gate)

- [x] 2.1 `pyproject.toml` añadir `[tool.coverage.run]` (`source = ["portfolio_engine"]`, `branch = true`, `omit = ["*/tests/*"]`), `[tool.coverage.report]` (`show_missing = true`, `fail_under = 85`, `precision = 1`), `[tool.coverage.html/xml]`, y extender `[tool.pytest.ini_options].addopts` de `"-q"` a `"-q --cov=portfolio_engine --cov-report=term-missing --cov-report=html --cov-report=xml --cov-branch --cov-fail-under=85"`.
- [x] 2.2 `Makefile` `test:` explicita cobertura con `uv run python -m pytest --cov=portfolio_engine --cov-report=term-missing --cov-report=html --cov-report=xml --cov-branch --cov-fail-under=85`, añadir `test-no-cov: uv run python -m pytest -q --no-cov`, ampliar `clean` con `htmlcov/.coverage/coverage.xml`. Verificar `make test` reporta cobertura y falla con `--cov-fail-under=90` (gate activo).
- [x] 2.3 `.github/workflows/ci.yml` espejar gate: `Test suite with coverage gate` con mismos flags + `Publish coverage` + `upload-artifact htmlcov`, mantener `uv sync --frozen` y matrix 3.11/12/13. Verificar `grep --cov .github/workflows/ci.yml` y `uv lock --check` en CI.

## 3. Verificación y cierre

- [x] 3.1 Suite completa `./init.sh` exit 0: `230 passed` + cobertura `85%` branch `87%` line, `All checks passed!`, `pyright 0`, `compileall OK`, sin `.coverage` commiteado (gitignore), `htmlcov` generado. Verificar `uv run pytest --cov=portfolio_engine` verde con umbral 85.
- [x] 3.2 Specs `openspec validate --all` (project-packaging + quality-gates + verification-harness) + `README` `230 tests` intacto + `CHANGELOG` Unreleased hygiene note si aplica.
