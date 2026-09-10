# Spec delta: quant-docs (feat-053, ADDED)

## ADDED Requirements

### Requirement: Trade-off Dykstra vs HRP documentado

La documentación cuantitativa SHALL explicar que la proyección Dykstra post-hoc minimiza distancia euclídea al vector HRP puro y no preserva el balance jerárquico de riesgo (ADR 003 addendum).

#### Scenario: trade-off localizable

- **WHEN** se busca "Dykstra" en la documentación del motor
- **THEN** existe la explicación del trade-off con referencia al ADR 003
