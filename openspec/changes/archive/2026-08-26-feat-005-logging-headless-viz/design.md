# Design: feat-005-logging-headless-viz

## Context

Suite 16 passed + 4 gates + CI verdes. `make run-debug` ya exporta LOG_LEVEL pero nadie lo lee (discrepancia nueva detectada en análisis). pipeline.py:4 importa pyplot solo para el show final.

## Goals / Non-Goals

**Goals:** logging predecible/isolado, backend determinista sin display, app sin pyplot, decisiones testeables puras.
**Non-Goals:** restyle de figuras, formatter JSON/estructurado, métricas de observabilidad, migración de reportes (feat-023).

## Decisions

### D1 — Logger de paquete, no root
`logging.getLogger("portfolio_engine")` cubre automáticamente a todos los módulos (`portfolio_engine.app.pipeline` etc. son hijos por jerarquía de nombres). Handler propio StreamHandler(stderr) con formato existente; `propagate=False` aísla de caplog/ruido global. Idempotencia: si ya existe handler marcado (attributo interno), solo se ajusta nivel.
*Alternativa descartada*: seguir en root — es exactamente el defecto M4.

### D2 — Guard de backend al frente del único importador
Tras eliminar pyplot de pipeline, `viz/reporting.py` es el único módulo que importa pyplot/seaborn; guard líneas arriba dentro del archivo garantiza orden. Regla: Agg SOLO si (`DISPLAY` ausente) AND (`MPLBACKEND` no forzado) AND plataforma no-mac (macOS usa backends nativos sin X11). Función pura `_resolve_backend(env)` para testear con monkeypatch.

### D3 — finalize_report_show unifica cierre/show
Único punto que decide mostrar vs cerrar todas las figuras pendientes; pipeline lo invoca al final. En headless show=True cae a close-all (regresión segura).

### D4 — Tests puros sobre decisiones, no sobre canvas
test_viz_headless.py valida `_resolve_backend` (env permutations), `_resolve_level` (param/env/inválido) y la idempotencia del logger con caplog presente — nada dibuja realmente → determinista en cualquier runner.

## Risks / Trade-offs

- Usuarios interactivos con DISPLAY no notan cambios (rama show intacta)
- Silenciar ruido raíz puede ocultar warnings de libs en stdout — aceptado: logs propios ya salen por stderr
