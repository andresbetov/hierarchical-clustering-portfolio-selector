## Context

Ver proposal.md (Why) y el delta de `out-of-sample-validation` (What). Estado: `walk_forward.py:128-150` computa el fold sin filtrar (daily_train sobre TODOS los tickers → cov → HRP → constraints → weight_vector len(tickers)); `log_test` tiene columnas de todos los tickers (ventana extendida feat-029). `apply_asset_filters(asset_metrics, closing_prices, minimum_sharpe, maximum_volatility)` (selection.py:19-80) exige `closing_prices[ticker]` por activo, excluye no-finitos nombrando ticker+motivo y retorna `(filtered_metrics, filtered_prices)`. `calculate_inverse_volatility_weights(asset_volatilities)` (allocation.py:46-50) floorea vols en `VOL_FLOOR_EPS` y normaliza. Fuentes: skfolio (1/N e IVP como estrategias de primera clase; DeMiguel 2007), bestfolio (benchmarks ex-ante sobre las mismas ventanas OOS: "si tu criterio no bate a 1/N, créelo"), disciplina walk-forward (pesos congelados del train, sin peeking).

## Goals / Non-Goals

**Goals:**
- El WF evalúa la estrategia productiva completa (filtros → HRP) por fold, ex-ante.
- Benchmarks equal/ivp ex-ante sobre el mismo universo de supervivientes y los mismos retornos OOS.
- Agregados comparables en `to_dict` (medianas por benchmark).

**Non-Goals:**
- NO cambiar el pipeline productivo ni `apply_asset_filters`.
- NO añadir costos de transacción ni turnover (v0.2.0, diferido explícito).
- NO benchmarks adicionales (min-var, random) ni parametrización de benchmarks.

## Decisions

**D1 — Reuso literal de `apply_asset_filters` por fold.** Misma semántica de producción (paridad real, no reimplementación): métricas por activo desde columnas del train (retorno/vol anualizados con `trading_days_per_year`, Sharpe con rf efectivo del reporte) + precios del slice. Los rejections ya se loguean nombrados. Alternativa descartada: filtro propio simplificado — divergiría del contrato de producción (exactamente lo que esta feature elimina).

**D2 — Vector de pesos sobre el universo completo con ceros en excluidos.** `log_test` tiene columnas de todos los tickers; el vector del motor (y de los benchmarks) se construye mapeando supervivientes→peso y resto→0.0 — sin rebanar `log_test` (que alteraría el retorno del primer día de feat-029) ni desalinear columnas. `fold.tickers` conserva el universo completo (documentación del fold); `fold.weights` contiene SOLO supervivientes.

**D3 — Benchmarks sobre supervivientes, no sobre el universo crudo.** Comparación justa: motor y benchmarks enfrentan el mismo universo invertible ex-ante del fold (1/N sobre supervivientes; ivp con vols de train de supervivientes). Alternativa descartada: 1/N sobre todos los tickers — compararía contra una estrategia que el mandato de filtros no permitiría ejecutar.

**D4 — Estructura de datos: `benchmarks: dict[str, dict]` por fold** (default `{}`; folds inválidos sin benchmarks) donde cada entrada expone `"weights"` (dict ticker→peso, solo supervivientes — observable y auditable), `"return"`, `"volatility"` y `"sharpe"` (float|None en degenerados) + 6 claves nuevas en `to_dict` (`median_oos_{return,volatility,sharpe}_{equal,ivp}`) reutilizando `_median_or_none` (ya filtra None). Alternativa descartada: 6 campos planos por fold — firma rígida que dificulta benchmarks futuros; alternativas sin weights — no auditable ex-ante.

**D5 — Métricas de benchmark idénticas al motor**: mismo helper de agregación (media/std ddof=1 anualizados, Sharpe con rf efectivo) sobre `log_test @ bench_vector`; degenerados → benchmark None excluido de medianas, espejo del motor.

**D6 — Fixtures existentes con umbrales relajados** (`minimum_sharpe_threshold=-10`, `maximum_volatility_threshold=10`): los bundles sintéticos tienen Sharpe marginal (~0.64) que con el filtro por fold haría los tests flakes; al relajar, todos los tickers sobreviven y los tests conservan su intención original con asserts intactos. Los tests NUEVOS usan umbrales activos para ejercitar el filtrado.

**D7 — Fold sin supervivientes = inválido** (ValueError dentro del try existente): warning nombrado, excluido de agregados — consistente con degenerados vigentes.

## Risks / Trade-offs

- [Doble cómputo de retornos diarios de train (métricas de filtro + construct_returns_matrix de supervivientes)] → costo O(fold) despreciable a escala del repo; gana claridad (el filtro consume el mismo contrato que producción).
- [Universos variables por fold hacen los agregados menos comparables entre corridas con umbrales distintos] → inherente a la paridad productiva; `relaxed_folds` y el log de rejections documentan la variación.
- [ivp con vol de train degenerada (vol=0)] → `calculate_inverse_volatility_weights` floorea en eps por contrato (M10); el motor ya habría invalidado el fold si la covarianza lo es.
- [Sharpe marginal en bundles de tests antiguos] → mitigado por D6 (umbrales relajados en fixtures, asserts intactos).

## Migration Plan

Sin migración: `walk_forward_evaluate` mantiene firma; `WalkForwardFold.benchmarks` tiene default `{}`. Resultados con umbrales por-default pasan a reflejar filtros (cambio deseado: paridad productiva). Rollback = revert del commit.
