# market-data-contract Specification (delta)

## ADDED Requirements

### Requirement: Alineación temporal antes de estadística multivariada

Toda matriz de retornos que alimente correlación, covarianza, clustering o asignación SHALL construirse sobre el calendario común (intersección) de los tickers involucrados, ordenado ascendente. La falta de densidad mínima (menos de 2 fechas comunes) SHALL fallar ruidosamente con `ValueError`, y la longitud desigual de series sin alinear SHALL ser rechazada explícitamente en vez de apilarse por posición.

#### Scenario: ticker con historial más corto
- **WHEN** un ticker del universo carece de fechas presentes en otros
- **THEN** las matrices usan solo filas con todas las series presentes y ninguna fila se compara contra fecha ajena

#### Scenario: calendarios disjuntos
- **WHEN** no existe solapamiento suficiente entre series
- **THEN** se levanta `ValueError` describiendo la intersección vacía en lugar de producir matrices degeneradas

#### Scenario: equal-length legacy intacto
- **WHEN** se llama `construct_returns_matrix` con arrays de igual longitud como antes
- **THEN** su comportamiento y shapes son idénticos a los previos al change
