# Proposal: feat-insample-tail-drawdown (feat-046)

## Why

El reporte técnico JSON diagnostica concentración (HHI), diversificación (DR/RC) y el embudo de filtros, pero es ciego a dos dimensiones: la asimetría a la baja de la serie in-sample (un HRP diversificado por varianza puede cargar cola izquierda común que la distancia firmada no penaliza) y el dolor secuencial realizado (igual Sharpe/vol pueden coexistir con caídas máximas muy distintas). Sin Sortino + VaR/CVaR95 + maxDD/Calmar, el Sharpe honesto `wᵀΣw` es optimismo in-sample sin contrapeso antes de leer las medianas OOS.

## What Changes

- Tres funciones puras nuevas en `portfolio_engine/app/report_json.py` (capa app, sin tocar motor/config/pipeline):
  - `portfolio_return_series(prices_alineados, weights) -> np.ndarray`: serie log diaria in-sample = matriz de log-retornos por clave @ vector de pesos en el mismo orden; `ValueError` nombrado ante mismatch de claves; ruta legacy M<N con pesos embebidos en cero (patrón `_embed` de walk-forward).
  - `tail_risk_metrics(serie, risk_free_rate, trading_days=252) -> dict`: Sortino log-coherente (objetivo `ln(1+rf)` vía `risk_free_log_rate`, feat-036), VaR95/CVaR95 históricos diarios (`method="linear"` pineado, inclusivo, jamás anualizados), etiquetas in-sample/daily/no-costs + `n_obs`/`n_tail`.
  - `drawdown_metrics(serie, trading_days=252) -> dict`: `P=exp(cumsum)`, `max_drawdown=min(DD)≤0`, `calmar=mean*T/|maxDD|` (convención del proyecto), `None` ante serie plana (nunca `inf`), Calmar negativo legal.
- Política de degenerados del épico: `len<2` o cualquier no-finito → todo `None` + `reason` (nunca 0/inf); sin downside → Sortino/DD `None` con motivo pero VaR/CVaR numéricos.
- La RE-ALINEACIÓN con `minimum_overlap_ratio=1.0` sobre las claves finales es contrato del caller (feat-050); aquí se pinea con test de regresión vía `align_prices_to_common_calendar` real.
- Exports en `portfolio_engine/app/__init__.py`. Scope cortado: sin VaR por fold OOS, sin VaR paramétrico/Cornish-Fisher, sin curva serializada (solo escalares), sin consola.

## Capabilities

### New Capabilities

(none — se extiende la capability existente)

### Modified Capabilities

- `technical-report`: +1 requirement ADDED (diagnóstico de riesgo in-sample: serie + cola + drawdown) con scenarios de pines analíticos, degenerados y serialización estricta.

## Impact

- `portfolio_engine/app/report_json.py`: solo append + `__all__` (cuerpos existentes intactos).
- `tests/test_report_json.py`: nueva clase de tests (TDD rojo primero).
- `feature_list.json` (feat-046), `progress.md`, `session-handoff.md`: trackers en la rama.
- Sin cambios en `core/`, `portfolio/`, `data/`, `validation/`, `viz/`, `pipeline.py`, `cli.py`, `config.py`.
