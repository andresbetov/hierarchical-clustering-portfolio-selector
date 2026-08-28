## MODIFIED Requirements

### Requirement: Sharpe reportado con covarianza real

El Sharpe de cartera mostrado en el resumen SHALL calcularse como (w·μ − rf)/sqrt(wᵀΣw) usando la matriz de covarianza alineada; la fórmula legacy sqrt(Σ(wᵢσᵢ)²) SHALL desaparecer del código de reporte. La matriz de covarianza entregada al resumen SHALL estar rebanada al subconjunto exacto del portfolio seleccionado — mismas dimensiones y mismo orden de tickers que el vector de pesos — en todas las rutas de asignación, incluida la ruta legacy con pruning por cluster (M < N). El pipeline SHALL preparar ese rebanado antes de invocar al módulo de reporte; el reporte SHALL NOT recibir matrices de dimensión distinta a los pesos.

#### Scenario: correlación cero equivale a legacy
- **WHEN** la covarianza es diagonal (ρ=0)
- **THEN** el Sharpe nuevo coincide con el cálculo por suma cuadrática de riesgos

#### Scenario: correlación positiva reduce el Sharpe
- **WHEN** dos activos con ρ=0.9 y pesos iguales comparan contra su versión ρ=0
- **THEN** la volatilidad de cartera con ρ=0.9 es mayor y el Sharpe resultante menor

#### Scenario: ruta legacy con pruning M<N
- **WHEN** un método de asignación distinto de hrp selecciona M activos de un universo filtrado de N (M < N) y se genera el reporte completo
- **THEN** el reporte se genera sin excepción y el Sharpe del resumen coincide con el cálculo manual wᵀΣw sobre la covarianza rebanada a los M activos seleccionados
