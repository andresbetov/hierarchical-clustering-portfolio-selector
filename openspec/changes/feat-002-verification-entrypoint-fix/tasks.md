# Tasks: feat-002-verification-entrypoint-fix

## 1. Configuración pytest

- [x] 1.1 Añadir `[tool.pytest.ini_options]` con `testpaths = ["tests"]` en pyproject.toml — verificar: `uv run pytest` recolecta solo tests/

## 2. Entradas de verificación

- [x] 2.1 Makefile target `test:` → `uv run python -m pytest -q`; actualizar texto de `make help` — verificar: `make test` verde
- [x] 2.2 init.sh: bloque pytest usa `uv run python -m pytest || [ $? -eq 5 ]` cuando uv existe; fallback python3 solo si no hay uv — verificar: `./init.sh` muestra resultados reales de tests
- [x] 2.3 CONTRIBUTING.md: eliminar nota obsoleta de make test roto (:81) y dejar `uv run pytest` / `make test` como equivalentes — verificar: sin referencias a smoke_test

## 3. Verificación y cierre

- [x] 3.1 Suite REAL en verde por primera vez: `make test` + `./init.sh` (exit 0) en esta sesión; capturar output — verificar: N tests passed visible en consola/evidence — NOTA: primera corrida real reveló ModuleNotFoundError portfolio_engine (paquete nunca instalable); resuelto in-scope con pythonpath=["."] en pytest config
- [x] 3.2 Actualizar tracker (feat-002 done + evidence), progress.md, session-handoff.md; commit convencional — verificar: git log limpio, status sin sobrantes
