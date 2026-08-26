# Tasks: feat-005-logging-headless-viz

## 1. Logging (M4)

- [x] 1.1 Reescribir core/logging_utils.py: logger de paquete, handler propio stderr, propagate=False, idempotente, nivel param>LOG_LEVEL>INFO, env inválido advierte — verificar: make types sin error nuevo
- [x] 1.2 Confirmar compatibilidad API pública: configure_logging exportada y firma retrocompatible (level opcional) — verificar: scripts/assets-investment.py sin cambios

## 2. Viz headless (M5)

- [x] 2.1 viz/reporting.py: guard Agg por entorno al tope + helpers _resolve_backend/_resolve_level/finalize_report_show — verificar: ruff+pyright verdes
- [x] 2.2 app/pipeline.py: eliminar import pyplot; show final delega a reporting — verificar: grep pyplot en app/ vacío

## 3. Tests del contrato

- [x] 3.1 tests/test_viz_headless.py: _resolve_backend permutations, _resolve_level cascada/inválido, idempotencia logger con caplog — verificar: suite crece verde
- [x] 3.2 Suite completa verde en CI-like local: make test + LOG_LEVEL=DEBUG smoke de configure — verificar: DEBUG visible una sola vez sin duplicados

## 4. Cierre

- [ ] 4.1 Gates completos + tracker feat-005 done+evidence + progress/handoff + commits + archive change — verificar: init.sh exit 0, git limpio
