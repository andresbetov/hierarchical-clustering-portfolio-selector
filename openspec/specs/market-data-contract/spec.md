# market-data-contract Specification

## Purpose
Definir de dónde provienen los insumos del análisis (tasa libre de riesgo, precios, calendario) y garantizar que cada uno tenga exactamente una fuente autoritativa, de modo que entradas divergentes sean imposibles o fallas ruidosas.

## Requirements

### Requirement: Tasa libre de riesgo sin default local

`download_and_calculate_metrics` SHALL exigir `risk_free_rate` como parámetro obligatorio sin valor por defecto; SHALL NOT existir ninguna constante de tasa fuera de `PortfolioConfig`, y la ruta del pipeline SHALL tomarla exclusivamente de ahí.

#### Scenario: uso directo sin tasa falla ruidoso
- **WHEN** se invoca el fetcher sin pasar `risk_free_rate`
- **THEN** lanza `TypeError` en el binding (antes de ejecutar descarga alguna)

#### Scenario: pipeline usa la config
- **WHEN** `main()` corre con una `PortfolioConfig`
- **THEN** el Sharpe por activo se calcula con `config.risk_free_rate` (0.045), nunca un default enterrado

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

### Requirement: Ventana explícita y calendario-precisa

La ventana de descarga SHALL derivarse de un parámetro `lookback_years` requerido (sin default local en el proveedor) interpretado en años calendario exactos — no en múltiplos de 365 días. El cálculo de fechas SHALL vivir en una función pura testeable sin red, y el 29-febrero como fecha límite SHALL resolverse al 28 del mes en años objetivo no bisiestos en lugar de fallar.

#### Scenario: ventana de cinco años cruza bisiesto
- **WHEN** la fecha fin es 29-feb-2024 y lookback_years=5
- **THEN** la fecha inicio resuelve a 28-feb-2019 sin excepción

#### Scenario: uso directo sin lookback falla ruidoso
- **WHEN** se invoca el fetcher sin pasar `lookback_years`
- **THEN** lanza `TypeError` en el binding, antes de cualquier descarga
