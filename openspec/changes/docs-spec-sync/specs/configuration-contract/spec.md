# Spec delta: configuration-contract (feat-053, MODIFIED + ADDED)

## MODIFIED Requirements

### Requirement: Validación al construir

`__post_init__` SHALL validar y rechazar con `ValueError`: pesos de scoring que no sumen 1±1e-9 o salgan de [0,1]; `risk_free_rate` fuera de [0,1]; `maximum_volatility_threshold <= 0`; `minimum_single_asset_weight > maximum_single_asset_weight`; `lookback_years < 1`; `trading_days_per_year` fuera de [1, 366]; `minimum_overlap_ratio` fuera de (0, 1]; método, distancia, estimador o linkage fuera de sus enums. (`target_portfolio_volatility` fue eliminado por ADR 001 y SHALL NOT reaparecer en el contrato.)

#### Scenario: typo de método

- **WHEN** se construye con `weight_allocation_method="risk_parit"`
- **THEN** ValueError descriptivo — el fallback silencioso runtime queda eliminado

### Requirement: Dispatch sin red de seguridad muerta

El dispatcher de asignación SHALL cubrir los cinco métodos legacy (`equal`, `inverse_volatility`, `risk_parity`, `max_sharpe`, `min_variance`) con mapeo 1:1 a su función; `hrp` SHALL lanzar un error de ruteo hacia la vía jerárquica; la rama else (inalcanzable por contrato de construcción) SHALL lanzar `ValueError` — SHALL NOT existir fallback silencioso.

#### Scenario: código sin rama muerta

- **WHEN** se inspecciona el dispatch
- **THEN** cada método legacy mapea 1:1 a su función, `hrp` rechaza con mensaje de ruteo y no existe fallback genérico silencioso

## ADDED Requirements

### Requirement: Ventana temporal parametrizada

`lookback_years` SHALL defaultear a 5 y aceptar solo enteros >= 1; `trading_days_per_year` SHALL defaultear a 252 dentro de [1, 366]; `minimum_overlap_ratio` SHALL defaultear a 0.9 dentro de (0, 1].

#### Scenario: lookback inválido

- **WHEN** se construye con `lookback_years=0`
- **THEN** ValueError descriptivo
