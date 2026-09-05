## MODIFIED Requirements

### Requirement: CI en servidor para develop/main
Un workflow GitHub Actions SHALL correr sobre push a develop/main y PRs hacia develop, ejecutando sync-frozen, ruff, pyright y pytest **con gate de cobertura** (`--cov=portfolio_engine --cov-branch --cov-fail-under=85`) bajo una matriz de versiones Python soportadas por el lock, y SHALL publicar resumen y artifact `htmlcov`.

#### Scenario: PR rojo bloquea
- **WHEN** un PR introduce código que viola lint, types, tests o hace caer cobertura bajo 85% branch
- **THEN** el check correspondiente falla y es visible como requerimiento del merge

### Requirement: Toolchain pinned en el lock
Las herramientas de gates (ruff, pyright, pytest, pytest-cov, hypothesis) SHALL vivir en `[dependency-groups] dev` con versión acotada, heredando la reproducibilidad del lockfile versionado.

#### Scenario: misma versión local y CI
- **WHEN** cualquier entorno ejecuta `uv sync --frozen`
- **THEN** obtiene exactamente las versiones de tools del lock, eliminando desviaciones "funciona en mi máquina"

## ADDED Requirements

### Requirement: Gate de cobertura 85 branch
La configuración de cobertura SHALL medir `portfolio_engine` con `branch = true`, `source = ["portfolio_engine"]`, `fail_under = 85` en `pyproject.toml`, y `addopts` SHALL incluir `--cov=portfolio_engine --cov-report=term-missing --cov-report=html --cov-report=xml --cov-branch --cov-fail-under=85`.

#### Scenario: harness reporta cobertura
- **WHEN** se ejecuta `make test` o `uv run pytest` sin args (hereda `addopts`)
- **THEN** el reporte muestra `TOTAL ... 85%` (branch) y el exit code es 0 si ≥85, distinto de 0 si <85
