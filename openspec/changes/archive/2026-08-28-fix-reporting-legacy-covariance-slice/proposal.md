## Why

La ruta legacy del reporte (métodos de asignación distintos de `hrp`) crashea cuando el clustering reduce el portfolio a M < N activos: `pipeline.py` pasa la covarianza N×N del universo filtrado a `plot_optimal_portfolio_analysis`, que la usa en `weight_vector @ cov @ weight_vector` con un vector de pesos de dimensión M — error de broadcasting. El default `hrp` (M == N, sin pruning) oculta el defecto, y ningún test cubre la ruta legacy del reporte. Es el bug P0-1 del plan v0.1.0 y la primera feature del DAG feat-028..041.

## What Changes

- `portfolio_engine/app/pipeline.py` rebanará la matriz de covarianza al subconjunto exacto del portfolio seleccionado (reutilizando `create_portfolio_covariance_matrix`, ya existente en `portfolio_engine/portfolio/allocation.py`) antes de pasarla al módulo de reporte.
- Test de regresión E2E offline de la ruta legacy (`risk_parity`) con pruning M<N: el reporte completo se genera sin excepción y el Sharpe del resumen coincide con el cálculo manual `wᵀΣw` sobre la covarianza rebanada.
- La firma pública de `plot_optimal_portfolio_analysis` no cambia: recibe la covarianza ya alineada en dimensiones.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `numeric-correctness`: el requirement "Sharpe reportado con covarianza real" se extiende para exigir que la matriz de covarianza entregada al resumen esté rebanada al subconjunto del portfolio seleccionado (dimensiones iguales a los pesos), en todas las rutas de asignación.

## Impact

- Código: `portfolio_engine/app/pipeline.py` (único cambio de producción esperado).
- Tests: `tests/test_reporting_sharpe.py` y/o `tests/test_pipeline_e2e.py` (nuevo caso E2E legacy con pruning).
- Sin cambios de API pública, sin dependencias nuevas, sin cambios de configuración.
