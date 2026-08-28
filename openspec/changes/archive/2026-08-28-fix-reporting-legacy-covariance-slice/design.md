## Context

Ver proposal.md (Why) y el delta de `numeric-correctness` (What). Estado relevante: `pipeline.py:241-250` pasa `covariance_matrix` (N×N, orden del universo filtrado) a `plot_optimal_portfolio_analysis`; en la ruta legacy `optimal_portfolio` tiene M < N activos y `reporting.py:440-446` ejecuta `weight_vector @ cov @ weight_vector` (M vs N×N). El helper `create_portfolio_covariance_matrix(optimal_portfolio, full_covariance_matrix, all_filtered_metrics)` ya existe en `allocation.py:13-31` y rebanada por índice sobre el orden de `all_filtered_metrics` — el mismo orden con que `pipeline.py` construye la covarianza filtrada. La red feat-021 (154 tests) pina el comportamiento de la ruta default `hrp`, donde el rebanado es identidad.

## Goals / Non-Goals

**Goals:**
- Reporte legacy libre de crash para todo método ≠ hrp con M < N.
- Sharpe del resumen consistente con la covarianza rebanada al portfolio real.
- Cambio de producción confinado al punto único de orquestación (pipeline).

**Non-Goals:**
- No tocar la ruta default `hrp` más allá de pasar por el rebanado identidad (cero cambio de comportamiento; red feat-021 intacta sin tocar asserts).
- No cambiar la firma pública de `plot_optimal_portfolio_analysis` ni su lógica interna.
- No refactorizar el módulo de reporte ni añadir defensa redundante en viz.

## Decisions

**D1 — Rebanar en `pipeline.py`, no en `reporting.py`.** El pipeline es el dueño de la preparación de datos (patrón de capas: app prepara domain data para viz); reporte permanece renderer puro. Alternativa descartada: rebanar dentro de `plot_optimal_portfolio_analysis` exigiría pasar `all_filtered_metrics` u orden de tickers al módulo viz — acoplamiento peor y firma pública rota.

**D2 — Reutilizar `create_portfolio_covariance_matrix`** como única fuente de verdad de la semántica ticker→índice (ya testada en la suite de allocation). No escribir un slicer nuevo.

**D3 — Firma pública intacta:** `plot_optimal_portfolio_analysis(covariance_matrix=...)` recibe ahora la matriz ya rebanada; los callers directos (wrapper legacy `scripts/assets-investment.py` delega en cli) no requieren cambios.

**D4 — Verificar el rebanado con el cálculo manual** en el test E2E (Sharpe == (w·μ−rf)/sqrt(wᵀΣ_M w) sobre la covarianza rebanada), no con asserts sobre PNG: mantiene el test independiente de matplotlib.

## Risks / Trade-offs

- [Orden de tickers entre pesos y columnas de la covarianza rebanada] → Mitigación: ambos derivan del orden de `filtered_metrics.keys()`; el test E2E pinea la igualdad contra el cálculo manual, que fallaría ante cualquier desorden.
- [Regresión en ruta default hrp] → Mitigación: el rebanado con M == N es identidad; la red feat-021 corre sin modificar asserts como gate obligatorio.
- [E2E con matplotlib en CI] → Mitigación: guard Agg ya establecido (feat-005); asserts sobre valores numéricos, no sobre figuras.

## Migration Plan

Sin migración: cambio interno de preparación de datos, sin API pública, config ni dependencias nuevas. Rollback = revert del commit (comportamiento previo restaurado por construcción).
