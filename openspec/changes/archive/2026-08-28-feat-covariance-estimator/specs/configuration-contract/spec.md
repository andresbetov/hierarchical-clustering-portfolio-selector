## ADDED Requirements

### Requirement: Estimador de covarianza validado

`PortfolioConfig` SHALL exponer `covariance_estimator` con valores {sample, ledoit_wolf, oas} (default `sample` según ADR 005) y SHALL rechazar cualquier otro valor en construcción con `ValueError` descriptivo.

#### Scenario: valor inválido
- **WHEN** se construye con covariance_estimator="shrinkage_otro"
- **THEN** ValueError enumera los valores permitidos

#### Scenario: default sin cambio
- **WHEN** se construye sin especificar covariance_estimator
- **THEN** el campo vale "sample"
