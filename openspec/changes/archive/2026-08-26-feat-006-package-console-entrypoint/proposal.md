# Proposal: feat-006-package-console-entrypoint

## Why

El proyecto nunca fue instalable: sin `[build-system]`, `uv sync` instala las dependencias pero no el propio paquete — consecuencia visible del hack `sys.path.insert` en `scripts/assets-investment.py:5` y motivo por el que la suite necesitó `pythonpath=["."]` (feat-002). Además el nombre con guión impide importarlo como módulo. M7 convierte al proyecto en paquete real con entrypoint de consola, cerrando la Fase Higiene.

## What Changes

- `pyproject.toml`: `[build-system]` hatchling; `[tool.hatch.build.targets.wheel] packages=["portfolio_engine"]`; `[project.scripts] portfolio-run = "portfolio_engine.cli:main"`
- `portfolio_engine/cli.py` (nuevo): `main()` sin argumentos ejecuta el análisis estándar (universo default, config default, reporte 7 plots, resumen) — exactamente lo que hace hoy el script; sin argparse (diferido a Fase 4, ver decision-log)
- `scripts/assets-investment.py`: thin wrapper delegando en `cli.main()`; hack sys.path eliminado
- `tests/test_cli.py` (nuevo): identidad de distribución resoluble + entry-point console_scripts apunta a cli:main + firma importable
- README/CONTRIBUTING documentan `uv run portfolio-run`
- Fuera de scope: CLI argparse/universe.yaml (Fase 4), reorganización src-layout (feat-023)

## Capabilities

### New Capabilities
- `package-interface`: contrato del paquete como unidad instalable y ejecutable — construcción wheel determinista, punto de entrada de consola estable e invocable sin hacks de path, identidad de distribución inspeccionable.

### Modified Capabilities
- `verification-harness`: `uv sync` ahora también instala el proyecto; `pythonpath=["."]` pasa a ser redundante pero se conserva como cinturón para pytest — no cambia requirements observables; referencia.

## Impact

- **Artefactos**: pyproject (build-system+scripts), cli.py (nuevo), script legacy reducido, test nuevo, uv.lock (hatchling entra)
- **Riesgo**: bajo; primera vez que sync instala el paquete — gates validan
