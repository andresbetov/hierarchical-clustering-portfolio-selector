# Proposal: feat-walkforward-json-section (feat-049)

## Why

Las medianas OOS del walk-forward son un veredicto sin expediente: ocultan en qué regímenes gana/pierde HRP frente a 1/N, cómo cambian los supervivientes por fold y, sobre todo, a qué precio de estabilidad (¿el +0.070 exige una rotación impagable?). Sin detalle por fold + deriva L1, el triángulo cuánto/contra-qué/a-qué-precio queda sin cerrar en el reporte JSON.

## What Changes

- Función pura nueva `walk_forward_section(report) -> dict` en `portfolio_engine/app/report_json.py` (append-only, sin tocar `walk_forward.py`): (a) agregados **verbatim** de `WalkForwardReport.to_dict()` (identidad pineada); (b) detalle por fold (índice, posiciones train/test como listas, tickers, pesos, OOS return/vol/sharpe, `mandate_relaxed`, benchmarks equal/ivp tal cual); (c) deriva §9 sobre folds VÁLIDOS consecutivos (válido = `oos_sharpe` no-None y finito): pesos embebidos en cero sobre la unión del par, `l1 = Σ|Δ| ∈ [0,2]`, `median_l1` (`np.median`), `p90_l1` (`quantile method="linear"`, H&F-7, precedente VaR), `pairs_computed/pairs_possible`, `broken_pairs`, etiqueta `drift-not-turnover` (telemetría de estabilidad, jamás anualizada ni ×bps; L1 = 2× turnover-equiv one-way, documentado).
- Fold inválido rompe la cadena (sin interpolación, precedente GIPS); <2 folds válidos → deriva `None` + `reason`.
- Exports en `portfolio_engine/app/__init__.py`. Scope cortado: sin CLI/flag (feat-051), sin invocar `walk_forward_evaluate`, sin CPCV/DSR/PBO, sin turnover modelado.

## Capabilities

### New Capabilities

(none — se extiende la capability existente)

### Modified Capabilities

- `technical-report`: +1 requirement ADDED (sección walk-forward con detalle por fold y deriva) con scenarios de identidad, pines de deriva, cadena rota y degenerados.

## Impact

- `portfolio_engine/app/report_json.py`: solo append + `__all__`; `walk_forward.py` diff cero (se consume, no se modifica).
- `tests/test_report_json.py`: nueva clase `TestWalkForwardSection` (TDD rojo primero, bundles sintéticos offline).
- `feature_list.json` (feat-049), `progress.md`, `session-handoff.md`: trackers en la rama.
- Sin cambios en `core/`, `portfolio/`, `data/`, `validation/`, `viz/`, `pipeline.py`, `cli.py`, `config.py`.
