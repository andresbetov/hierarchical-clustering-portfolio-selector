# Spec delta: numeric-correctness (feat-053, MODIFIED)

## MODIFIED Requirements

### Requirement: Bounds de peso satisfechos simultáneamente en el resultado final

`apply_weight_constraints` SHALL retornar pesos donde TODOS los activos cumplan min≤w≤max y la suma sea 1, mediante proyecciones cíclicas de Dykstra sobre el simplex y los semiespacios de bounds (con acumuladores por restricción) y una verificación final dura que lanza en vez de devolver un vector violado.

#### Scenario: ejemplo canónico del audit

- **WHEN** los pesos previos son [0.60, 0.10, 0.10, 0.10, 0.10] con min=0.05/max=0.30
- **THEN** el resultado final respeta max en todos los componentes (ninguno >0.30) y suma 1

#### Scenario: entrada ya válida

- **WHEN** todos los pesos están dentro de bounds
- **THEN** el vector retorna sin cambios numéricos relevantes
