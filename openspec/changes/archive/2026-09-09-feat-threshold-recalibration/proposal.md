## Why

El filtro de producción admite muy pocos supervivientes con los thresholds actuales (12→4 en la ventana completa 2021-2026 y N≤3 en 10/16 folds walk-forward con relajación del mandato), lo que colapsa el HRP hacia 1/N y deja al motor sin jerarquía que explotar. La evidencia walk-forward del experimento vía A demuestra que recalibrar a 0.3/0.27 restaura N=6 con dispersión real y es la única configuración donde el HRP bate a 1/N en mediana OOS (+0.070).

## What Changes

- `PortfolioConfig.minimum_sharpe_threshold`: default `0.5` → `0.3`.
- `PortfolioConfig.maximum_volatility_threshold`: default `0.25` → `0.27`.
- Actualización de la tabla de configuración en `README.md` y entrada `Changed` en `CHANGELOG.md` (`Unreleased`).
- Actualización de los pinnings de tests que fijan el default anterior (`test_config.py`) y nuevo test de contrato de los defaults recalibrados.
- Nuevo test de regresión walk-forward sintético (CI-safe, sin red) donde HRP ≥ equal en mediana con thresholds recalibrados.

## Capabilities

### New Capabilities

(Ninguna — la capacidad de filtrado ya existe.)

### Modified Capabilities

- `configuration-contract`: cambian los defaults de `minimum_sharpe_threshold` y `maximum_volatility_threshold`, que son REQUIREMENTS observables del contrato de configuración (gobiernan el embudo filtrado y, por tanto, el universo invertible del pipeline y del walk-forward).

## Impact

- Código: `portfolio_engine/core/config.py` (2 líneas); consumidores (`pipeline.py`, `walk_forward.py`, `reporting.py`) leen el config dinámicamente, sin cambios.
- Tests: pinnings de default en `test_config.py`; el resto de la suite usa thresholds explícitos y queda intacta.
- Docs: `README.md` (tabla), `CHANGELOG.md`, ADR-007 (decisión metodológica permanente).
- Sin cambios de API, dependencias ni esquema de caché (la key de caché no incluye thresholds; los bundles cached se re-filtran con los nuevos valores).
