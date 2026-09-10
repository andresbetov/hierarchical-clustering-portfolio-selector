# Proposal: feat-report-assembler (feat-050)

## Why

Cinco secciones puras verificadas (043/044/045/046/048 + 049 lista) viven sin ensamblar: hoy ningún run produce el JSON. El keystone las compone en `build_technical_report` y lo emite opt-in desde `generate_complete_analysis_report` sin cambiar consola, tuplas ni defaults — el reporte pasa de capacidad probada a entregable real.

## What Changes

- `build_technical_report(...)` pura en `report_json.py`: envelope + filter_rejections + allocation (cov rebanada internamente, `raw_weights=None` — el motor no expone raw) + risk (serie reconstruida con re-align 1.0; fallo de serie → secciones null + warning, no aborta sección) + tree (cov completa filtrada + linkage) + `walk_forward: None` (placeholder; feat-051 lo llena).
- `generate_complete_analysis_report` gana kwargs keyword-only `report_path=None`, `run_walk_forward=False` (reservado, debug-log); con `report_path` construye+volca tras el log final, en `try/except Exception` con warning nombrado (el reporte jamás rompe el run) + `logger.info` de escritura; 8-tupla/4-tupla intactas; `report_path` jamás a `main`.
- `cli.main` pasa `report_path="reports/technical-report.json"` (JSON siempre emitido; `--no-save` gobierna solo plots); 3 fakes de `test_cli.py` aceptan el kwarg.
- `.gitignore` ignora `reports/`; `make clean` borra `reports/*.json`; exports en `portfolio_engine/__init__.py`.

## Capabilities

### New Capabilities

(none — se extiende la capability existente)

### Modified Capabilities

- `technical-report`: +1 requirement ADDED (ensamblador + emisión con fail-safe) con scenarios de E2E, default-silencioso, fallo que no rompe y `--no-save`.
