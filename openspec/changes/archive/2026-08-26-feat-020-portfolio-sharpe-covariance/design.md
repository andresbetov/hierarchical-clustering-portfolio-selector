# Design: feat-020-portfolio-sharpe-covariance

## Context

Depende feat-008 (Σ alineada) y feat-014/19 (pesos finitos). El wrapper `plot_optimal_portfolio_analysis` es llamado solo desde pipeline, que ya retorna covariance_matrix — el cableado es directo.

## Goals / Non-Goals

**Goals:** Sharpe honesto con Σ; función pura testeable; firmas compatibles.
**Non-Goals:** regenerar PNGs históricos (snapshots); tear sheets (Fase 4); VaR/CVaR.

## Decisions

### D1 — Función pura única
`_portfolio_summary_metrics` centraliza retorno/vol/sharpe para que plotter y futuros consumers (CLI JSON output) no diverjan.
### D2 — Firmas aditivas
Nuevo parámetro opcional-al-final `covariance_matrix=None`: None degrada a la fórmula diagonal con warning (compat scripts), pero pipeline SIEMPRE pasa la matriz — en la práctica el warning es red defensiva, no ruta normal.
### D3 — Docstring advierte interpretación
El panel será ejecutivo correcto; sigue sin sustituir backtest (README ya lo aclara).

## Risks / Trade-offs

- Sharpe reportado baja numéricamente vs histórico — corrección esperada y motivación del change
