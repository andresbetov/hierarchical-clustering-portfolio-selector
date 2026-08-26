# configuration-contract Specification

## Purpose
La configuración del motor SHALL ser un objeto inmutable, construido por un único punto validado, donde todo estado inválido es imposible de crear (falla en construcción) y ningún consumidor puede mutarla después.

## Requirements

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

### Requirement: Métrica de distancia de correlación validada

`PortfolioConfig` SHALL exponer `distance_metric` con valores {signed, abs} (default signed según ADR 002) y SHALL rechazar cualquier otro valor en construcción.

#### Scenario: valor inválido
- **WHEN** se construye con distance_metric="euclidean"
- **THEN** ValueError enumera los valores permitidos

### Requirement: Días de trading configurables y validados

`PortfolioConfig` SHALL exponer `trading_days_per_year` (default 252) validado dentro de [1, 366]; los kernels de anualización SHALL recibirlo como parámetro explícito y SHALL NOT contener la constante enterrada.

#### Scenario: calendario alternativo
- **WHEN** se configura trading_days_per_year=365 para un universo crypto
- **THEN** retorno/volatilidad anualizados usan exactamente 365 en su fórmula

#### Scenario: valor inválido
- **WHEN** se construye con trading_days_per_year=0
- **THEN** ValueError descriptivo

### Requirement: Ruta end-to-end HRP sin pruning intermedio

Con method=hrp, la orquestación SHALL asignar pesos sobre TODO el universo filtrado mediante linkage→quasi-diag→bisección, omitiendo la selección por scoring compuesto; los bounds de feat-014 SHANL aplicarse al vector final igual que en los demás métodos.

#### Scenario: flujo hrp del pipeline
- **WHEN** main() corre con config default
- **THEN** los pesos provienen de calculate_hrp_weights y todos los tickers filtrados aparecen en el resultado con peso > 0
