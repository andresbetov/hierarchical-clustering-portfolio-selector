# numeric-correctness Specification (delta)

## ADDED Requirements

### Requirement: Bisección determinista sin inversión de matrices

El asignador HRP SHALL construir pesos usando únicamente diagonales de slices covarianza (sin np.linalg.inv), SHALL ser determinista para entradas idénticas, y sus pesos finales SHALL ser estrictamente positivos y sumar exactamente 1 antes de aplicar constraints.

#### Scenario: dos activos varianzas conocidas
- **WHEN** cov = diag(0.01, 0.04) para [A, B]
- **THEN** los pesos sin constraints son exactamente [0.8, 0.2] (inverse-variance a través de las bisecciones)

#### Scenario: invarianza permutación
- **WHEN** se reordenan columnas/filas de la misma covarianza
- **THEN** el multiset de pesos es idéntico entre ambas corridas
