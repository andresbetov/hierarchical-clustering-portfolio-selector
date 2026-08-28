## ADDED Requirements

### Requirement: Seam de estimación de covarianza con paridad sklearn

`estimate_covariance(returns_matrix, method)` SHALL ser la única vía de cómputo de covarianza para el pipeline y el walk-forward. Con `method="sample"` SHALL retornar exactamente la matriz de `calculate_covariance_matrix` (bit a bit); con `method="ledoit_wolf"`/`"oas"` SHALL retornar la matriz shrinkage del estimador homónimo de scikit-learn con paridad numérica 1e-12, y su condition number SHALL ser menor o igual al de la covarianza muestral sobre los mismos datos. Entradas degeneradas (menos de 2 observaciones) SHALL producir la matriz NaN completa sin invocar a sklearn.

#### Scenario: sample bit a bit
- **WHEN** se estima con method="sample" sobre una matriz de retornos cualquiera
- **THEN** el resultado es idéntico al de calculate_covariance_matrix

#### Scenario: paridad shrinkage con sklearn
- **WHEN** se estima con method="ledoit_wolf" (o "oas") sobre retornos sintéticos
- **THEN** la matriz coincide con sklearn.covariance.LedoitWolf (u OAS) a tolerancia 1e-12

#### Scenario: degeneración sin sklearn
- **WHEN** la matriz de retornos tiene 1 fila o menos
- **THEN** se devuelve la matriz NaN completa (misma semántica que sample) sin error
