# Proposal: feat-009-numeric-guards-metrics

## Why

Cuatro defectos numéricos interactúan en cadena (C3, crítico): Sharpe sin guard produce `inf` que cruza el filtro silenciosamente; la volatilidad anual usa ddof=0 mientras la covarianza interna usa ddof=1 (estimadores mezclados); la diagonal de correlación es 1.0 aunque el activo sea plano; y risk-parity divide por contribuciones sin piso — una covarianza casi-singular explota o diverge sin aviso. Sobre estos números se construyen clustering, selección y asignación: datos corruptos arriba significan cartera inválida abajo.

## What Changes

- `core/metrics.py`: constante `VOL_FLOOR_EPS`; `_resolve_window` intocado; `calculate_annualized_volatility` ddof=1 con cálculo manual numba-compatible; `calculate_sharpe_ratio` → NaN si vol≤ε; `calculate_correlation_matrix` diagonal condicionada a varianza>0
- `portfolio/selection.py`: `apply_asset_filters` excluye activos con métricas no-finitas, loggeando ticker+motivo
- `portfolio/allocation.py`: `calculate_risk_parity_weights` piso épsilon sobre contribuciones + cap de factores [0.1,10] + warning al agotar iteraciones sin converger
- `tests/test_metrics.py`: expectativa vol ddof=1 exacta; nuevos casos activo plano (sharpe/corr),NaN-pattern; suite risk-parity singular/convergencia; filtro nombrando excluidos (~10 tests)
- Fuera de scope:inverse-vol floor (feat-010 inmediato siguiente, reutiliza VOL_FLOOR_EPS); HRP real (feat-018); shrinkage (feat-019)

## Capabilities

### New Capabilities
- `numeric-correctness`: contrato del dominio numérico del motor — divisiones protegidas con semántica definida (NaN para indefinidos), estimadores muestrales consistentes, y exclusiones de activos visibles con motivo.
