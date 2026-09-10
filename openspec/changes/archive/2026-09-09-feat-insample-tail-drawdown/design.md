# Design: feat-insample-tail-drawdown (feat-046)

## Contexto y decisiones previas

- Épico JSON (feat-043 core, feat-044 exclusiones, feat-045 asignación); convenciones: funciones puras en `portfolio_engine/app/report_json.py`, `raise ValueError` nombrado ante error de programador, `None` + `reason` ante degenerado válido, imports function-local para seams privados, `__all__` extendido.
- feat-036 unificó el Sharpe a coherencia-log (`risk_free_log_rate = log1p(rf)`); feat-028 fijó el rebanado de covarianza; walk-forward (`validation/walk_forward.py:252-264`) fija el patrón serie = `log(P[1:]/P[:-1]) @ w` y la política `len<2 → None`.
- Catálogo §7 (cola) + §2 (drawdown); descripciones de `feature_list.json:feat-046`.

## Decisiones de diseño (con respaldo de los 4 análisis)

1. **Objetivo downside `T/252` con `T = ln(1+rf)` vía `risk_free_log_rate`** (function-local, `core/metrics.py:22-32`). El texto `rf/252` de la feature se registra como errata: mezcla simple/log y rompería el pin 1e-12 (~4e-06 de diferencia con rf=0.045). Respaldo: análisis externo (coherencia aditiva en log) + entendimiento (feat-036).
2. **Numerador Calmar/Sortino/ann_ret = `mean*T`** (proyecto-coherente, spec-literal `ret_anualizado`), NO CAGR geométrico. Desviación documentada del estándar externo moderno (`exp(mean*252)−1`): en este reporte todos los numeradores (Sharpe feat-036, Sortino) usan `mean*T` sobre log-retornos; un Calmar geométrico sería el único inconsistente del documento. El bucle de validación deberá ratificar o revertir.
3. **Firma `portfolio_return_series(prices_alineados, weights) -> np.ndarray`** (contrato literal del tracker; la sugerencia `list` de síntesis se descarta: el sanitizador ya maneja ndarray y la serie alimenta cómputo NumPy). NO re-alinea dentro: la re-alineación con `minimum_overlap_ratio=1.0` es contrato del caller (feat-050); aquí regression-test de integración con `align_prices_to_common_calendar` real (contraejemplo 0.9 verificado en el tracker).
4. **`drawdown_metrics(serie, trading_days=252)`**: keyword explícito con default = default del motor; los tests siempre lo pasan explícito. `tail_risk_metrics(serie, risk_free_rate, trading_days=252)` simétrico.
5. **Cualquier no-finito en la serie → todo `None` + `reason`** (literal del tracker: "len<2 o no-finito → todo None+motivo"). Se descarta el "drop silencioso" de síntesis: recortar la muestra fabricaría una serie más limpia; null+motivo es honesto. Excepción pineada: sin downside, VaR/CVaR sí se computan (spec scenario).
6. **`np.quantile(..., method="linear")` literal** (NumPy 2.x del lock 2.4.6/2.5.2; `interpolation=` fue removido en 2.0 → sería `TypeError`). Sin fallback: el lock es la garantía.
7. **Solo dependencias: `risk_free_log_rate` + `VOL_FLOOR_EPS` + `compute_logarithmic_returns` + `calculate_annualized_return`** (imports function-local, patrón del módulo). La serie usa el seam público por activo (corrección por construcción, cero drift); Sortino/drawdown usan `calculate_annualized_return` para `mean*T` (un solo dialecto de anualización en el reporte).
8. **Invariante CVaR refinado**: `cvar >= var` (firmado) SIEMPRE; `cvar >= |var|` solo cuando VaR ≥ 0 (cola real de pérdidas). El "SIEMPRE" del tracker se acota aquí con la prueba (`mean(cola) ≤ q05`); el scenario del spec lo pinea en ambas formas.
9. **Downside sobre N total** (`mean` incluye ceros, NO solo días malos — Sortino-Forsey 1996, quantstats `sum/len`).
10. **Legacy M<N**: `portfolio_return_series` acepta pesos de subconjunto y los embebe en cero sobre el universo de precios (patrón `_embed` walk-forward.py:252-256); `tail/drawdown` no saben de tickers (solo serie).
11. **Shapes de salida**: dicts planos con etiquetas `frequency:"daily"`, `sample:"in-sample"`, `costs:"no-costs"` + `n_obs`/`n_tail` (cola) para reproducibilidad; degenerado = métricas `None` + `"reason"`.

## Riesgos y mitigaciones

- Pin 1e-12 frágil ante BLAS: usar `rel=1e-12` en analíticos exactos (constantes, diagonales) y `abs` donde haya redondeo de quantile; quantile lineal sobre series fijas es determinista bit a bit.
- `np.quantile` con `method=` en NumPy del lock: verificado por mapeo (2.4.6/2.5.2); test de método pineado lo cubre.
- Curva no serializada (scope): `drawdown_metrics` NO devuelve la serie DD (solo escalares); documentado en docstring.

## No-goals (§10 del catálogo)

VaR por fold OOS, VaR paramétrico/Cornish-Fisher, curva de drawdown en JSON, Sortino en consola, turnover/costes.
