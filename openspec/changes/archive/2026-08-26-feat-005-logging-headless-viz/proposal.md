# Proposal: feat-005-logging-headless-viz

## Why

Dos defectos de runtime afectan cada corrida y el CI que feat-004 acaba de crear. Logging: `configure_logging` (core/logging_utils.py) configura el logger RAIZ y aborta si ya hay handlers — captura ruido de terceros, ignora `LOG_LEVEL` (el flag que el propio `make run-debug` exporta y nunca fue leído) y colide con pytest-caplog. Viz: `plt.show(block=False)`/`plt.pause` en `_finalize_plot` y `plt.show()` bloqueante al final del pipeline no son headless-safe — cualquier corrida sin display produce warnings o comportamientos indeterminados; además `pipeline.py` importa pyplot directamente solo para ese show final, violando la separación app/viz.

## What Changes

- `core/logging_utils.py`: logger de paquete `"portfolio_engine"` con handler propio a stderr, `propagate=False`, idempotente por deduplicación; nivel = param explícito > `LOG_LEVEL` env > INFO
- `viz/reporting.py`: guard de backend Agg cuando no hay display y el usuario no forzó `MPLBACKEND`; helper `finalize_report_show(show)` para cerrar o mostrar figuras según entorno
- `app/pipeline.py`: eliminar dependencia directa de pyplot; el show final delega en reporting
- `tests/test_viz_headless.py` (nuevo): decisiones de backend/log-level testeables con monkeypatch, independientes del backend real del proceso
- Fuera de scope: restyling de gráficas, migración estructural de reportes (feat-023), print_* textuales

## Capabilities

### New Capabilities
- `runtime-diagnostics`: contrato del comportamiento de diagnóstico en runtime — configuración de logging predecible e idempotente bajo el namespace del paquete, y ciclo de vida de figuras seguro tanto con como sin display.

### Modified Capabilities
Ninguna.

## Impact

- **Artefactos**: logging_utils.py, reporting.py, pipeline.py, test nuevo
- **Riesgo**: bajo — sin lógica de dominio tocada; suite valida 16 passed + nuevos tests
