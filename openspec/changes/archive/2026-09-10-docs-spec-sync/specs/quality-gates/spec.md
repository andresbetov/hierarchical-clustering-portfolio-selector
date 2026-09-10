# Spec delta: quality-gates (feat-053, MODIFIED)

## MODIFIED Requirements

### Requirement: CI en servidor para develop/main

Un workflow GitHub Actions SHALL correr sobre push a develop/main y PRs hacia develop, ejecutando sync-frozen, ruff, pyright y pytest **con gate de cobertura** (`--cov=portfolio_engine --cov-branch --cov-fail-under=85`) bajo una matriz de versiones Python soportadas por el lock, y SHALL publicar resumen y artifact `htmlcov`.

#### Scenario: PR rojo bloquea

- **WHEN** un PR introduce código que viola lint, types, tests o hace caer cobertura bajo el 85% TOTAL combinado
- **THEN** el check correspondiente falla y es visible como requerimiento del merge

### Requirement: Gate de cobertura 85 TOTAL combinado

La configuración de cobertura SHALL medir `portfolio_engine` con `branch = true`, `source = ["portfolio_engine"]`, `fail_under = 85` en `pyproject.toml`, y `addopts` SHALL incluir `--cov=portfolio_engine --cov-report=term-missing --cov-report=html --cov-report=xml --cov-branch --cov-fail-under=85`. El umbral 85 aplica al TOTAL combinado de coverage.py (líneas+branches), no a branch-only.

#### Scenario: harness reporta cobertura

- **WHEN** se ejecuta `make test` o `uv run pytest` sin args (hereda `addopts`)
- **THEN** el reporte muestra `TOTAL ... 85%` (combinado) y el exit code es 0 si ≥85, distinto de 0 si <85
