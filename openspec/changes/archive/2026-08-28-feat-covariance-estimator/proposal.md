## Why

Toda la cadena jerárquica consume la covarianza muestral sin alternativa. La literatura (Trucíos 2026; Palomar 12.3; skfolio) demuestra que los métodos jerárquicos son sensibles al estimador de covarianza y expone shrinkage (LedoitWolf/OAS) como práctica estándar. La auditoría original difería "LedoitWolf transversal formal" (B5); feat-032 ya incorporó scikit-learn como dependencia. Es feat-033 del DAG v0.1.0, primera feature metodológica de CP2, gobernada por ADR 005.

## What Changes

- Nuevo campo validado `PortfolioConfig.covariance_estimator ∈ {sample, ledoit_wolf, oas}` (default `sample` — sin cambio silencioso; flip a `ledoit_wolf` diferido a v0.2.0 con evidencia walk-forward).
- Seam única `estimate_covariance(returns_matrix, method)` en `core/metrics.py`: `sample` = matriz vigente bit a bit; `ledoit_wolf`/`oas` = `sklearn.covariance` shrinkage; degeneración (n_rows ≤ 1) conserva la semántica sample (matriz NaN, sin llamar a sklearn).
- `pipeline.main` y `walk_forward_evaluate` consumen el estimador desde config.
- Export público en `portfolio_engine/__init__.py`.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `configuration-contract`: nuevo parámetro `covariance_estimator` validado en construcción (enum cerrado, default `sample`).
- `numeric-correctness`: contrato del seam de estimación — `sample` bit a bit con la matriz vigente, shrinkage con paridad exacta contra sklearn y condition number no peor que sample.

## Impact

- Código: `core/config.py`, `core/metrics.py`, `app/pipeline.py`, `validation/walk_forward.py`, `__init__.py`.
- Docs: ADR 005 (aceptado), README tabla de configuración, CHANGELOG Unreleased.
- Tests: `test_config.py`, `test_metrics.py` (o archivo dedicado `test_covariance_estimator.py`), `test_pipeline_e2e.py` (E2E offline con ledoit_wolf).
- Sin cambios de API destructivos: los consumidores existentes de `calculate_covariance_matrix` siguen intactos.
