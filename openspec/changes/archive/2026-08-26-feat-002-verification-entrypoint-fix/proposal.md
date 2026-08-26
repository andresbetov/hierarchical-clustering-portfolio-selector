# Proposal: feat-002-verification-entrypoint-fix

## Why

`Makefile:17` ejecuta `uv run python tests/smoke_test.py`, un archivo que no existe — `make test` falla siempre y está documentado como roto en `CONTRIBUTING.md:81`. Además, `init.sh:14` detecta pytest con el intérprete del sistema (`python3 -c "import pytest"`), no con el del proyecto: hoy `uv sync` instala pytest en `.venv` pero la verificación lo saltea igual (observado 2026-08-26 tras instalar uv). Sin verificación real, ningún fix posterior es demostrable.

## What Changes

- `Makefile`: target `test` apunta a `uv run pytest -q` (fuente de verdad declarada ya en CONTRIBUTING/README)
- `pyproject.toml`: sección `[tool.pytest.ini_options]` con `testpaths = ["tests"]`
- `init.sh`: cuando existe `uv`, ejecutar `uv run pytest || [ $? -eq 5 ]`; el fallback con python3 del sistema queda solo para entornos sin uv
- `CONTRIBUTING.md:81`: eliminar la nota "make test apunta a archivo inexistente" (deja de ser cierta)
- No se tocan dependencias ni nombres de paquete (scope de feat-003)

## Capabilities

### New Capabilities
- `verification-harness`: contrato de comportamiento del comando único de verificación (`make test` / pytest dentro de `init.sh`) — qué debe ejecutar, qué significa éxito y cuándo la ausencia de tests no es fallo.

### Modified Capabilities
Ninguna — no hay specs previas de esta capacidad.

## Impact

- **Artefactos**: Makefile, pyproject.toml, init.sh, CONTRIBUTING.md
- **Código de producto**: sin cambios (`portfolio_engine/` intacto)
- **Riesgo**: mínimo; primera corrida REAL de pytest (17 asserts existentes) puede revelar fallos preexistentes — si ocurren, son hallazgos válidos a registrar, no bloqueo del fix
