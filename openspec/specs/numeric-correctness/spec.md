# numeric-correctness Specification

## Purpose
Garantizar que las magnitudes numéricas del motor tengan semántica definida ante casos degenerados: indefinidos se representan como NaN y quedan excluidos de forma visible, los estimadores muestrales son consistentes entre sí, y las iteraciones numéricas no divergen silenciosamente.

## Requirements

### Requirement: Sharpe indefinido para varianza nula

`calculate_sharpe_ratio` SHALL retornar NaN cuando la volatilidad anualizada sea menor o igual al piso épsilon, y SHALL NOT producir infinitos.

#### Scenario: activo con precio plano
- **WHEN** un activo tiene volatilidad anualizada 0
- **THEN** su Sharpe es NaN y nunca inf

### Requirement: Exclusión visible de métricas no finitas

El filtro de activos SHALL excluir cualquier ticker cuyas métricas usadas por decisión (Sharpe, volatilidad) no sean finitas, registrando en el log el ticker y el motivo de exclusión.

#### Scenario: filtro nombrando excluidos
- **WHEN** el universo contiene un activo con Sharpe NaN
- **THEN** el warning incluye ese ticker y las matrices posteriores no lo contienen

### Requirement: Consistencia muestral ddof

La volatilidad anualizada y la covarianza/correlación SHALL usar el mismo estimador muestral (ddof=1); no SHALL NO coexistir ddof distinto en la misma cadena estadística.

#### Scenario: verificación exacta
- **WHEN** se calcula la volatilidad anualizada sobre una serie conocida
- **THEN** coincide exactamente con std(ddof=1)*sqrt(252)

### Requirement: Correlación honesta ante varianza cero

En la matriz de correlación, la diagonal SHALL ser 1.0 solo cuando la varianza propia sea positiva; activos planos producen NaN en toda su fila/columna.

#### Scenario: matriz con un activo plano
- **WHEN** un activo tiene retornos idénticos constantes
- **THEN** su fila, columna y diagonal contienen NaN, y los demás pares permanecen finitos

### Requirement: Risk-parity protegida contra degeneración

Las contribuciones de riesgo en cada iteración SHALL tener piso épsilon y los factores de escalado SHALL estar acotados; si se agotan las iteraciones sin alcanzar tolerancia, SHALL emitirse warning antes de devolver pesos normalizados finitos.

#### Scenario: covarianza singular por duplicados
- **WHEN** dos activos tienen columnas idénticas en la covarianza
- **THEN** los pesos resultantes son finitos, suman 1 y el proceso termina sin excepción
