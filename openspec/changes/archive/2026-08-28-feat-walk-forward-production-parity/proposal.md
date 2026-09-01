## Why

El walk-forward valida hoy solo el núcleo HRP: `walk_forward_evaluate` NO aplica los filtros Sharpe/vol de producción por fold de train (pipeline.py:76-81 sí lo hace), y el reporte no expone benchmarks — sin comparación contra 1/N e IVP la lectura del Sharpe mediano OOS es engañosa (skfolio: "naive allocation (1/N, inverse-vol) tends to outperform MVO out-of-sample", DeMiguel 2007; práctica 2026: "Equal weight is in the list deliberately. If your clever criterion cannot beat 1/N... you should believe it"). Es feat-035, la feature central de CP2: convierte la validación en la evaluación de la ESTRATEGIA productiva completa con lectura honesta contra benchmarks ex-ante.

## What Changes

- **Paridad productiva por fold**: cada fold de train computa métricas por activo (retorno/vol anualizados, Sharpe) y aplica `apply_asset_filters` con los umbrales de config — el universo invertible del fold deriva exclusivamente del train (ex-ante), con rejections nombradas en el log. Los pesos del fold cubren solo los supervivientes; los tickers excluidos reciben peso 0 en el vector alineado (sin desalinear `log_test @ weight_vector`).
- **Benchmarks ex-ante comparables**: `WalkForwardFold.benchmarks` expone `equal` (1/N sobre supervivientes) e `ivp` (inverse-volatility con vols de train) con retorno/vol/Sharpe OOS computados sobre los MISMOS retornos del fold (misma ventana extendida feat-029). `WalkForwardReport.to_dict()` añade las medianas `median_oos_{return,volatility,sharpe}_{equal,ivp}`.
- **Documentación de la disciplina temporal**: docstring y README declaran embargo=5d (práctica 5-20 días para estrategias diarias) y purga implícita=1d (horizonte de la etiqueta = retorno diario; el embargo excede el solape).
- Folds sin supervivientes quedan inválidos (warning nombrado), consistente con el manejo vigente de degenerados.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `out-of-sample-validation`: el requirement "Evaluación OOS con pesos ex-ante" se extiende con los filtros de producción por fold; se AÑADE el requirement de benchmarks ex-ante comparables con agregados en el reporte.

## Impact

- Código: `portfolio_engine/validation/walk_forward.py` (loop del fold + dataclasses + to_dict).
- Tests: `tests/test_walk_forward.py` (nuevos casos ex-ante/benchmarks; fixtures existentes con umbrales relajados para preservar su intención original — asserts intactos).
- Docs: README (sección Validación), CHANGELOG.
- Sin cambios de API destructivos: `walk_forward_evaluate` mantiene firma; `WalkForwardFold` gana campo con default.
