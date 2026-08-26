# configuration-contract Specification (delta)

## MODIFIED Requirements

### Requirement: Enum de métodos de asignación incluye HRP

`WEIGHT_ALLOCATION_METHODS` SHALL incluir `hrp`; el default SHALL ser `hrp` (ADR 003); el valor sigue validado en construcción y cualquier otro método no listado sigue rechazado.

#### Scenario: default jerárquico
- **WHEN** se construye PortfolioConfig sin overrides
- **THEN** weight_allocation_method == "hrp"

## ADDED Requirements

### Requirement: Ruta end-to-end HRP sin pruning intermedio

Con method=hrp, la orquestación SHALL asignar pesos sobre TODO el universo filtrado mediante linkage→quasi-diag→bisección, omitiendo la selección por scoring compuesto; los bounds de feat-014 SHANL aplicarse al vector final igual que en los demás métodos.

#### Scenario: flujo hrp del pipeline
- **WHEN** main() corre con config default
- **THEN** los pesos provienen de calculate_hrp_weights y todos los tickers filtrados aparecen en el resultado con peso > 0
