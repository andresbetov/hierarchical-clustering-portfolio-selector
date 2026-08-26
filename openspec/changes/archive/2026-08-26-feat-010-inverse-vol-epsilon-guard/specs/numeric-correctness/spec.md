# numeric-correctness Specification (delta)

## ADDED Requirements

### Requirement: Piso épsilon en asignación inverse-volatility

`calculate_inverse_volatility_weights` SHALL aplicar el piso épsilon compartido (`VOL_FLOOR_EPS`) a las volatilidades antes de invertirlas, de modo que ninguna volatilidad degenerada produzca pesos infinitos.

#### Scenario: volatilidad cero entre activos
- **WHEN** una volatilidad de entrada es 0 y otra positiva
- **THEN** los pesos resultantes son finitos, estrictamente positivos y suman 1
