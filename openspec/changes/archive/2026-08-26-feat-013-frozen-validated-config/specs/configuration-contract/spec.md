# configuration-contract Specification (delta)

## Purpose

La configuración del motor SHALL ser un objeto inmutable, construido por un único punto validado, donde todo estado inválido es imposible de crear (falla en construcción) y ningún consumidor puede mutarla después.

## ADDED Requirements

### Requirement: Inmutabilidad estructural

Post-construcción, cualquier intento de asignar un atributo SHALL fallar con `FrozenInstanceError`; los nombres de campos SHALL preservar la API histórica para que consumidores existentes no cambien.

#### Scenario: mutación rechazada
- **WHEN** se intenta `config.minimum_sharpe_threshold = -10` tras construir
- **THEN** se lanza `FrozenInstanceError`

### Requirement: Validación al construir

`__post_init__` SHALL validar y rechazar con `ValueError`: pesos de scoring que no sumen 1±1e-9; tasas y vol-target fuera de [0,1]; `minimum_single_asset_weight > maximum_single_asset_weight`; lookback < 1; método fuera del set {equal, inverse_volatility, risk_parity, max_sharpe, min_variance}.

#### Scenario: typo de método
- **WHEN** se construye con `weight_allocation_method="risk_parit"`
- **THEN** ValueError descriptivo — el fallback silencioso runtime queda eliminado

### Requirement: Dispatch sin red de seguridad muerta

El dispatcher de asignación SHALL cubrir exactamente el enum validado y SHALL NOT contener rama de fallback para métodos desconocidos (imposibles por contrato).

#### Scenario: código sin rama muerta
- **WHEN** se inspecciona el dispatch
- **THEN** cada método mapea 1:1 a su función y no existe else-fallback genérico
