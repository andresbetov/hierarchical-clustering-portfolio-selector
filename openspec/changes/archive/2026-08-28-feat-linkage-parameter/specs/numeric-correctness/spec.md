## ADDED Requirements

### Requirement: Linkage HRP parametrizable con default retrocompatible

`calculate_hrp_weights(covariance_matrix, linkage_method)` SHALL aceptar {single, ward, average} y propagarlos a `scipy.cluster.hierarchy.linkage`; con `linkage_method="single"` (default) los pesos SHALL ser idénticos bit a bit a los del comportamiento vigente. Un método desconocido SHALL lanzar `ValueError`. Para cualquier método válido, los pesos finales SHALL ser estrictamente positivos, finitos y sumar exactamente 1 antes de constraints.

#### Scenario: default single bit a bit
- **WHEN** se invoca calculate_hrp_weights sin linkage_method sobre una covarianza conocida
- **THEN** los pesos coinciden exactamente con los del snapshot vigente (red feat-021)

#### Scenario: ward sobre bloques de correlación
- **WHEN** se invoca con linkage_method="ward" sobre un universo sintético de 3 bloques de correlación
- **THEN** los pesos son finitos, estrictamente positivos y suman 1, y activos del mismo bloque quedan adyacentes en el orden de hojas

#### Scenario: método desconocido
- **WHEN** se invoca con linkage_method="centroid"
- **THEN** ValueError antes de llamar a scipy
