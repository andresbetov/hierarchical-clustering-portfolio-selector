# market-data-contract Specification (delta)

## Purpose

Definir de dónde provienen los insumos del análisis (tasa libre de riesgo, precios, calendario) y garantizar que cada uno tenga exactamente una fuente autoritativa, de modo que entradas divergentes sean imposibles o fallas ruidosas.

## ADDED Requirements

### Requirement: Tasa libre de riesgo sin default local

`download_and_calculate_metrics` SHALL exigir `risk_free_rate` como parámetro obligatorio sin valor por defecto; SHALL NOT existir ninguna constante de tasa fuera de `PortfolioConfig`, y la ruta del pipeline SHALL tomarla exclusivamente de ahí.

#### Scenario: uso directo sin tasa falla ruidoso
- **WHEN** se invoca el fetcher sin pasar `risk_free_rate`
- **THEN** lanza `TypeError` en el binding (antes de ejecutar descarga alguna)

#### Scenario: pipeline usa la config
- **WHEN** `main()` corre con una `PortfolioConfig`
- **THEN** el Sharpe por activo se calcula con `config.risk_free_rate` (0.045), nunca un default enterrado
