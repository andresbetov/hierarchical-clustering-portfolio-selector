# Proposal: feat-020-portfolio-sharpe-covariance

## Why

El resumen ejecutivo de la cartera (viz/reporting.py:308-310) computa el Sharpe como `ret / sqrt(Σ(wᵢσᵢ)²)` — asume correlación cero entre activos. Para una cartera con correlaciones típicas ~0.5-0.9 eso subestima la volatilidad de cartera y infla el Sharpe reportado: exactamente la métrica que el usuario usa para juzgar (A5, auditoría). El motor ya tiene `calculate_portfolio_variance` (allocation.py:34) — el plotter simplemente nunca lo usó.

## What Changes

- `viz/reporting.py`: función pura `_portfolio_summary_metrics(weights, expected_returns, cov, risk_free) -> dict` — retorno, volatilidad `sqrt(wᵀΣw)`, Sharpe; usada por `plot_optimal_portfolio_analysis` (firma +parámetro `covariance_matrix`)
- `app/pipeline.py`: pasa la matriz al plotter (ya disponible)
- Tests (`tests/test_reporting_sharpe.py`): comparación numérica contra cálculo manual wᵀΣw, caso ρ=0 equivalencia legacy, ρ=1 divergencia esperada, 2-activos analítico
- Fuera de scope: regenerar PNGs históricos de scripts/charts (snapshots — no se reescriben retroactivamente)

## Capabilities

### Modified Capabilities
- `numeric-correctness`: el Sharpe reportado SHALL derivarse de la varianza de cartera real (wᵀΣw), no de la suma cuadrática de riesgos individuales.
