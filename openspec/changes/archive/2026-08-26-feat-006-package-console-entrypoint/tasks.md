# Tasks: feat-006-package-console-entrypoint

## 1. Packaging real

- [x] 1.1 pyproject: [build-system] hatchling pinned + wheel target flat + [project.scripts] portfolio-run — verificar: campos presentes
- [x] 1.2 `uv lock && uv sync`: proyecto se instala a sí mismo en el venv — verificar: salida incluye instalación de hierarchical-clustering-portfolio-selector
- [x] 1.3 Import sin hacks: `uv run python -c "import portfolio_engine"` desde cualquier cwd con venv activo — verificar: exit 0

## 2. Entrypoint y wrapper

- [x] 2.1 Crear portfolio_engine/cli.py main() replicando conducta del script (universo default, reporte, summary) — verificar: ruff+pyright verdes
- [x] 2.2 scripts/assets-investment.py → wrapper delegando; sys.path hack eliminado — verificar: grep sys.path vacío en scripts/

## 3. Tests de identidad (sin red)

- [x] 3.1 tests/test_cli.py: importlib.metadata resuelve dist+entrypoint console_scripts exacto; firma main callable — verificar: suite crece verde
- [x] 3.2 Gates completos: make lint/types/test + ./init.sh exit 0 — verificar: outputs

## 4. Cierre

- [ ] 4.1 README/CONTRIBUTING documentan uv run portfolio-run; tracker feat-006 done+evidence; progress/handoff; commits; archive change
