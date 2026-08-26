# configuration-contract Specification (delta)

## ADDED Requirements

### Requirement: Métrica de distancia de correlación validada

`PortfolioConfig` SHALL exponer `distance_metric` con valores {signed, abs} (default signed según ADR 002) y SHALL rechazar cualquier otro valor en construcción.

#### Scenario: valor inválido
- **WHEN** se construye con distance_metric="euclidean"
- **THEN** ValueError enumera los valores permitidos
