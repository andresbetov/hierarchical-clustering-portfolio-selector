# Proposal: feat-013-frozen-validated-config

## Why

`PortfolioConfig` es una bolsa de atributos mutable sin validación (M1): nada impide pesos que no sumen 1, límites invertidos, lookback inválido o un typo en el método de asignación que caería silenciosamente al fallback runtime. Cualquier módulo puede mutar la configuración a mitad de pipeline. La decisión contract-first del DAG (diseño D3 de feat-001) exige congelar la API ANTES de que M2/B4/C1/C4 añadan nuevos campos — evitando migrar consumidores dos veces.

## What Changes

- `core/config.py`: reescritura como `@dataclass(frozen=True)` con los mismos nombres de campo (acceso por atributo preservado — cero cambios en consumidores); validación explícita en `__post_init__`
- Reglas: pesos scoring suman 1±1e-9; tasas/vol-target en [0,1]; `min_weight ≤ max_weight`; lookback ≥ 1; método ∈ {equal, inverse_volatility, risk_parity, max_sharpe, min_variance}
- `allocation.py`: fallback runtime "unknown method → risk_parity" eliminado (la validez nace en el constructor)
- `tests/test_integration.py`: fixture mutante migrada a constructor por kwargs
- `tests/test_config.py` (nuevo): inmutabilidad + cada regla de validación (~8 casos)
- Fuera de scope: carga desde YAML/env (Fase 4), freeze de nuevos campos M2/B4

## Capabilities

### New Capabilities
- `configuration-contract`: contrato de la configuración — tipos exactos, rangos, interdependencias y estados válidos; construcción validada como único punto de entrada; inmutabilidad garantizada post-construcción.
