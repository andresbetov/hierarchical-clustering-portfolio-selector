# Tasks: feat-020-portfolio-sharpe-covariance

## 1. Cálculo honesto

- [x] 1.1 viz/reporting.py: `_portfolio_summary_metrics` pura (wᵀΣw) + plotter firma+consumo; warning si cov=None — verificar: ruff+pyright
- [x] 1.2 pipeline.py pasa covariance_matrix al plotter — verificar: flujo

## 2. Tests y cierre

- [x] 2.1 tests/test_reporting_sharpe.py: ρ=0 equivale legacy; ρ=0.9 > vol y menor Sharpe vs ρ=0; 2 activos analítico — verificar: crece verde
- [x] 2.2 Gates + tracker done + commits + archive + PR merge
