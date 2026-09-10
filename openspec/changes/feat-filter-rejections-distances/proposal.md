## Why

El embudo de filtrado (12→4 observado) es hoy invisible para el consumidor del reporte técnico: los motivos de exclusión solo viven en logs (`selection.py:68-73`) y las distancias al umbral no se computan en ninguna parte. La práctica audit-ready estándar (matriz accept/reject con motivo específico y conteos por etapa — EU JTPF, audit-trails de screening) exige que cada exclusión sea legible, trazable y distinguible entre "eliminado por mucho" y "casi pasa". Es el segundo bloqueo del épico feat-043..051 y consume el requisito de §3 del catálogo (docs/diagnostics-catalog.md).

## What Changes

- Función pura `compute_filter_rejections(requested_tickers, asset_metrics, filtered_metrics, closing_prices, config)` en `portfolio_engine/app/report_json.py`: para cada ticker pedido clasifica motivo (`ingestion_rejected`, `sharpe_non_finite`, `vol_non_finite`, `below_min_sharpe`, `above_max_vol`, `overlap_pruned`, `kept`) con los slugs EXACTOS de `selection.py:53,56,59,62`, y distancias firmadas `d_sharpe = sharpe − minimum_sharpe_threshold`, `d_vol = maximum_volatility_threshold − vol` (None cuando la métrica no es finita o el motivo no las admite).
- Export en `portfolio_engine/app/__init__.py`.
- Sin integración en pipeline/CLI (feat-050): cero cambios de comportamiento en la corrida actual.

## Capabilities

### New Capabilities

(Ninguna — la capability `technical-report` ya existe desde feat-043.)

### Modified Capabilities

(Ninguna en sentido MODIFIED — se acrecenta con un requirement ADDED a la capability existente `technical-report`: diagnóstico de exclusiones del filtro con distancias al umbral y conteos consistentes.)

## Impact

- Código: +1 función pura en `report_json.py` (~40 stmts) + export; cero cambios en el motor (`selection.py`/`data_fetch.py`/`metrics.py` intocados, red feat-021 diff 0).
- Tests: nuevas clases en `tests/test_report_json.py` (TDD rojo→verde).
- Dependencias: ninguna nueva. Warning duplicado conocido: `apply_asset_filters` NO se re-ejecuta — la clasificación se deriva por inferencia pura del mismo orden de guardias (verificado contra selection.py:47-63), sin duplicar logs.
