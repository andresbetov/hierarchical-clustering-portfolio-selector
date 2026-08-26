# numeric-correctness Specification (delta)

## ADDED Requirements

### Requirement: Sharpe reportado con covarianza real

El Sharpe de cartera mostrado en el resumen SHALL calcularse como (w·μ − rf)/sqrt(wᵀΣw) usando la matriz de covarianza alineada; la fórmula legacy sqrt(Σ(wᵢσᵢ)²) SHALL desaparecer del código de reporte.

#### Scenario: correlación cero equivale a legacy
- **WHEN** la covarianza es diagonal (ρ=0)
- **THEN** el Sharpe nuevo coincide con el cálculo por suma cuadrática de riesgos

#### Scenario: correlación positiva reduce el Sharpe
- **WHEN** dos activos con ρ=0.9 y pesos iguales comparan contra su versión ρ=0
- **THEN** la volatilidad de cartera con ρ=0.9 es mayor y el Sharpe resultante menor
