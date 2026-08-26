# market-data-contract Specification (delta)

## ADDED Requirements

### Requirement: Ventana explícita y calendario-precisa

La ventana de descarga SHALL derivarse de un parámetro `lookback_years` requerido (sin default local en el proveedor) interpretado en años calendario exactos — no en múltiplos de 365 días. El cálculo de fechas SHALL vivir en una función pura testeable sin red, y el 29-febrero como fecha límite SHALL resolverse al 28 del mes en años objetivo no bisiestos en lugar de fallar.

#### Scenario: ventana de cinco años cruza bisiesto
- **WHEN** la fecha fin es 29-feb-2024 y lookback_years=5
- **THEN** la fecha inicio resuelve a 28-feb-2019 sin excepción

#### Scenario: uso directo sin lookback falla ruidoso
- **WHEN** se invoca el fetcher sin pasar `lookback_years`
- **THEN** lanza `TypeError` en el binding, antes de cualquier descarga
