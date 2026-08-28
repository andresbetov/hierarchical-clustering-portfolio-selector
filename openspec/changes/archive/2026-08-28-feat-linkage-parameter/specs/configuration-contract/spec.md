## ADDED Requirements

### Requirement: Método de linkage validado

`PortfolioConfig` SHALL exponer `linkage_method` con valores {single, ward, average} (default `single` según ADR 006) y SHALL rechazar cualquier otro valor en construcción con `ValueError` descriptivo.

#### Scenario: valor inválido
- **WHEN** se construye con linkage_method="centroid"
- **THEN** ValueError enumera los valores permitidos

#### Scenario: default sin cambio
- **WHEN** se construye sin especificar linkage_method
- **THEN** el campo vale "single"
