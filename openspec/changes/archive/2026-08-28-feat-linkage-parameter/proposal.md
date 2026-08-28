## Why

El HRP usa `linkage(method="single")` hardcodeado — fiel a De Prado 2016, pero expuesto al *chaining* documentado por la literatura (skfolio fija Ward por estabilidad; pyhrp compara métodos; Papenbrock resume trade-offs). El DAG v0.1.0 difería el linkage paramétrico (decision-log feat-025). Es feat-034, gobernada por ADR 006.

## What Changes

- Nuevo campo validado `PortfolioConfig.linkage_method ∈ {single, ward, average}` (default `single` — sin cambio silencioso; flip a `ward` candidato para v0.2.0 junto al estimador de covarianza).
- `calculate_hrp_weights(covariance_matrix, linkage_method="single")`: valida el método y lo propaga a `scipy.cluster.hierarchy.linkage`; default retrocompatible (bit a bit con el snapshot feat-021).
- `pipeline` (ruta HRP end-to-end) y `walk_forward_evaluate` pasan `config.linkage_method`.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `configuration-contract`: nuevo parámetro `linkage_method` validado en construcción (enum cerrado, default `single`).
- `numeric-correctness`: contrato del HRP — el linkage SHALL ser parametrizable con default `single` bit a bit con el comportamiento vigente; métodos alternativos SHALL producir pesos válidos del simplex.

## Impact

- Código: `core/config.py`, `portfolio/hrp.py`, `portfolio/allocation.py` (paso de config), `app/pipeline.py`, `validation/walk_forward.py`.
- Docs: ADR 006 (aceptado), README tabla de configuración, CHANGELOG Unreleased.
- Tests: `test_config.py`, `test_hrp.py` (ward/average sobre universos de bloques de correlación), red feat-021 intacta con default.
- Sin cambios de API destructivos: la firma de `calculate_hrp_weights` gana un parámetro con default.
