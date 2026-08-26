# Proposal: feat-026-walk-forward-validation

## Why

Todo el motor evalúa in-sample sobre la misma ventana que entrena y asigna (B6). El Sharpe reportado — ahora calculado honestamente con covarianza real tras feat-020 — sigue siendo una estimación sin valicación temporal. El walk-forward con re-entrenamiento por ventanas y embargo entre train/test es la mínima validación out-of-sample defendible según De Prado.

## What Changes

- `portfolio_engine/validation/walk_forward.py` (nuevo):
  - `_iter_walk_windows(n_rows, window_train, window_test, embargo_days)` generador puro de rangos (train_slice, test_slice) con embargo entre boundaries
  - `walk_forward_evaluate(prices_by_ticker, dates, config) -> WalkForwardReport` — por ventana: re-alinea, re-filtra, re-clusteriza/assigna HRP en TRAIN; computa retornos ponderados OOS en TEST con pesos fijados ex-ante
  - dataclass `WalkForwardReport` con per-fold metrics + agregados (median_return_oos, median_vol, median_sharpe, fraction_positive_folds)
  - comporbage determinista: NO emplea información futura — pesos de cada fold provienen exclusivamente del slice entrenamiento
- Integración vía composición existente: opera sobre diccionarios fecha→precios ya alineados por el proveedor inyectable (feat-023)
- Tests: función pura de ventanas (edge exhaustivo), motor completo con SyntheticProvider reducido determinista (~8 folds), aserción embargo estricto, métricas OOS coherentes
- Fuera de scope: costos de transacción y turnover control (fase siguiente), visualización walk-forward, integración CLI

## Capabilities

### New Capabilities
- `out-of-sample-validation`: contrato de validación temporal del motor — generación de ventanas sin fuga, evaluación OOS de asignaciones fijadas ex-ante, agregación estadística transparente de pliegues.
