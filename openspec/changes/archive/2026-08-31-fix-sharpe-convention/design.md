## Context

Actualmente 6 call-sites restan `rf` aritmético a retornos log anualizados (`mean(log)*252`): `core/metrics:calculate_sharpe_ratio`, `data/data_fetch:download_and_calculate_metrics`, `portfolio/allocation:calculate_maximum_sharpe_weights`, `viz/reporting:_portfolio_summary_metrics` + línea visual, y `validation/walk_forward: _train_survivors` + `_oos_metrics`. `PortfolioConfig.risk_free_rate=0.045` es single source aritmética validada en `[0,1]`. No existe `rf_log`. La suite pinea 4 valores con `rf != 0`. `walk_forward._oos_metrics` duplica la fórmula sin `VOL_FLOOR_EPS`.

## Goals / Non-Goals

**Goals:**
- Coherencia dimensional log: todos los numeradores Sharpe usan `ln(1+rf)` vía `math.log1p`.
- Single source `config.risk_free_rate_log` + helper `metrics.risk_free_log_rate` para call-sites sin config.
- `rf=0` invariante; `rf=0.045` pin exacto `0.044016885416774`.
- Dykstra post-hoc documentado como trade-off consciente.

**Non-Goals:**
- No cambiar `rf` almacenado (sigue aritmético `0.045` para legibilidad/API).
- No volver a `rf=0` default ni cambiar `trading_days`.
- No reimplementar risk parity/min variance (no usan rf).

## Decisions

**D1 — Híbrida A+B: `@property risk_free_rate_log` (config) + helper `risk_free_log_rate(rf)` (metrics).**
- `config.py: @property def risk_free_rate_log(self)->float: return math.log1p(self.risk_free_rate)` — single source para pipeline/reporting/walk_forward que tienen config. Usa `math.log1p` directo para evitar ciclo `config -> metrics`.
- `metrics.py: def risk_free_log_rate(rf: float) -> float` — wrapper inverso para `data_fetch` (solo recibe float) y testeable directo; delega a `math.log1p` con guard `rf<=-1 → nan` para "never inf".
- Duplicación intencional mínima (dos `log1p`) documentada para evitar import circular; alternativa `core/risk_free.py` compartido descartada por sobrediseño.
- Trade-off: `frozen=True` impide `cached_property` sin truco `object.__setattr__`; coste `log1p` ~50ns despreciable.

**D2 — Migrar los 6 call-sites a `rf_log`.**
1. `core/metrics:calculate_sharpe_ratio` — acepta `risk_free_rate` aritmética pero convierte internamente vía helper (mantiene firma, no rompe callers).
2. `data/data_fetch:200` — convierte el float recibido antes de `calculate_sharpe_ratio`.
3. `portfolio/allocation:153` — `excess = expected_returns - math.log1p(risk_free_rate)` (o helper) antes de solve.
4. `viz/reporting:377` — `excess = portfolio_return - math.log1p(risk_free_rate)` + línea visual `ln(1+rf)` coherente.
5. `validation/walk_forward: _train_survivors:131` y `_oos_metrics:154` — convierten `rf` a `rf_log` y unifican `_oos_metrics` para llamar `calculate_sharpe_ratio` + `VOL_FLOOR_EPS`.

Decisión: `calculate_sharpe_ratio` sigue recibiendo `rf` aritmético (API estable) y hace `log1p` dentro — evita cambiar 6 firmas. Alternativa de cambiar firma a `rf_log` descartada: rompe compatibilidad `provider.fetch_metrics(tickers, 0.045, ...)` de tests.

**D3 — `walk_forward._oos_metrics` unificado.**
Usa `calculate_sharpe_ratio` y guarda `VOL_FLOOR_EPS` en lugar de `>0` genérico, eliminando la duplicación `H-11`.

**D4 — Addendum ADR 003, no supersede.**
Formato fechado `Addendum 2026-09-01` (convención `docs/adr/README.md:12`). Declara que Dykstra minimiza distancia euclídea, no varianza jerárquica; cuantifica ejemplo `n=5,max=0.30` donde dispersión se reduce; motiva por qué no intra-bisección (acopla config a `hrp.py:104-120`, rompe `sin inversión` y auditabilidad).

**D5 — Tests: `rf=0` invariante + `rf=0.045` exacto.**
Todos los pinnings con `rf != 0` migran a `(ret - log1p(rf))/vol` con `rel=1e-12`; `rf=0` permanecen como regression guard.

## Risks / Trade-offs

- **Cambio de contrato numérico (breaking en rf≠0):** Sharpe sube ~0.005 para vol 0.18. Mitigado por `CHANGELOG.md` y `rf=0` invariante. No cambia firmas.
- **Doble cómputo `log1p`:** despreciable (<0.1% tiempo total, dominado por yfinance/linkage).
- **Spec `quant-docs` nueva:** añade capacidad documental; no retrocede numeric-correctness salvo el addendum de coherencia.
