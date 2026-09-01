## Why

El motor calcula retornos anualizados como `mean(log_returns)*252` (`core/metrics.py:24`) — escala logarítmica — pero resta `risk_free_rate` aritmético (`0.045`) en 6 puntos: `calculate_sharpe_ratio`, `data_fetch`, `allocation:max_sharpe`, `reporting:_portfolio_summary_metrics`, `walk_forward:_train_survivors` y `_oos_metrics`. La mezcla introduce un sesgo sistemático `rf - ln(1+rf) = 0.00098` (2.18% relativo) para el default y 30% para `rf=1.0`. Con `rf` pequeño la aproximación es tolerable, pero el pipeline es log-end-to-end (correlación/covarianza/HRP sobre matriz log) y la trazabilidad exige coherencia dimensional explícita. Además, `docs/adr/003` declara que Dykstra post-hoc "se aplica al final" sin advertir que altera el balance de riesgo `inverse-variance por cluster` del HRP — es una elección consciente de mandato, no propiedad del método, y debe documentarse.

## What Changes

- **Coherencia logarítmica del Sharpe**: nuevo helper `risk_free_log_rate(rf)` / `math.log1p(rf)` y propiedad derivada `PortfolioConfig.risk_free_rate_log` (`ln(1+rf)`, single source, `log1p` estable para `rf << 1`). Todos los numeradores de Sharpe pasan a `annual_return - rf_log`. Invariante: `rf=0 → rf_log=0` (tests existentes sin cambios de valor); `rf=0.045 → rf_log=0.0440168854` pinneado. Seis call-sites migrados; `walk_forward._oos_metrics` unificado para usar `calculate_sharpe_ratio` + `VOL_FLOOR_EPS` en lugar de `>0` genérico.
- **ADR 003 Addendum 2026-09-01** (fechado, no supersede): declara que Dykstra post-hoc minimiza distancia euclídea al vector HRP puro, no varianza jerárquica; cuando un bound muerde, la redistribución deja de respetar `alpha=1-VarL/(VarL+VarR)` y aplana jerarquía (cuantificado). Motiva por qué no se hace constraining intra-bisección (Pfitzinger & Katzke 2017: acopla config a `hrp.py:104-120`, rompe `sin inversión` y auditabilidad).
- Tests actualizan pinnings que calculaban `(ret - rf_arith)/vol` a `(ret - log1p(rf))/vol`; `rf=0` permanece invariante como regression guard.

## Capabilities

### New Capabilities
- `quant-docs`: Documentación cuantitativa verificable del addendum ADR y convención log.

### Modified Capabilities
- `numeric-correctness`: Requisito de coherencia logarítmica del Sharpe — el exceso SHALL usar `rf_log = ln(1+rf)` para coherencia dimensional con retornos log anualizados.

## Impact

- **Código**: `core/config.py` (@property), `core/metrics.py` (helper + `calculate_sharpe_ratio` impl), `data/data_fetch.py`, `portfolio/allocation.py`, `viz/reporting.py`, `validation/walk_forward.py`, `core/__init__.py` exports.
- **Docs**: `docs/adr/003-hrp-adoption.md` (addendum), `docs/adr/README.md` (fecha addendum), `CHANGELOG.md`.
- **Tests**: `tests/test_metrics.py`, `tests/test_reporting_sharpe.py`, `tests/test_walk_forward.py`, `tests/test_pipeline_e2e.py`, `tests/test_solvers.py` donde aplique — solo pinnings numéricos con `rf != 0`.
- **Riesgo**: Cambio de contrato numérico (breaking en 0.045): Sharpe sube ~0.005 para vol 0.18. Mitigado por `rf=0` invariante y pinnings exactos rel 1e-12. No cambia firmas públicas.
