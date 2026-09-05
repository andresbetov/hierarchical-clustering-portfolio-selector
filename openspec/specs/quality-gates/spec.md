# quality-gates Specification

## Purpose
Garantizar que los gates de calidad estática corran en todos los ciclos donde una regresión puede nacer: edición local (init.sh/Makefile) y revisión en servidor (CI sobre push/PR a develop). Un gate que no corre automáticamente no protege nada.

## Requirements

### Requirement: Lint determinista y descubrible

El proyecto SHALL tener lint configurado desde `pyproject.toml` mediante ruff con reglas declaradas explícitamente, ejecutable vía `make lint` y vía `uv run ruff check .` indistintamente.

#### Scenario: make lint verde
- **WHEN** el árbol no viola las reglas declaradas
- **THEN** `make lint` termina exit 0 sin output de errores

### Requirement: Type-check básico obligatorio

El proyecto SHALL mantener pyright en modo `basic` en verde, limitado al código del paquete (`portfolio_engine/`, `scripts/`); `make types` SHALL ser la entrada canónica.

#### Scenario: regresión tipada detectable
- **WHEN** un cambio introduce un error detectable en modo basic dentro del paquete
- **THEN** `make types` falla y bloquea la verificación

### Requirement: Harness local ejecuta todos los gates
Cuando uv está disponible, `init.sh` SHALL ejecutar — además de sync, pytest y compileall — los gates lint y types; **pytest heredará `addopts` con cobertura** cuando `pytest-cov` esté instalado, de lo contrario degradará sin gate pero sin romper `compileall`.

#### Scenario: sesión de agente con uv
- **WHEN** un agente ejecuta `./init.sh` antes de marcar done
- **THEN** ningún gate queda silenciosamente omitido si sus herramientas están instaladas por uv, y el reporte de cobertura aparece en el log de pytest si disponible

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

### Requirement: Gate de cobertura 85 branch
La configuración de cobertura SHALL medir `portfolio_engine` con `branch = true`, `source = ["portfolio_engine"]`, `fail_under = 85` en `pyproject.toml`, y `addopts` SHALL incluir `--cov=portfolio_engine --cov-report=term-missing --cov-report=html --cov-report=xml --cov-branch --cov-fail-under=85`.

#### Scenario: harness reporta cobertura
- **WHEN** se ejecuta `make test` o `uv run pytest` sin args (hereda `addopts`)
- **THEN** el reporte muestra `TOTAL ... 85%` (branch) y el exit code es 0 si ≥85, distinto de 0 si <85
