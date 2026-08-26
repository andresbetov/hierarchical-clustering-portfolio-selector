# Proposal: feat-017-trading-days-parameterization

## Why

La constante de anualización `252` está enterrada dentro de los kernels numba (`calculate_annualized_return/volatility`, metrics.py:28,47): activos con otro calendario (crypto 365, mercados con sesiones distintas) son imposibles sin editar código. Coherente con el contrato de datos: la constante debe ser un parámetro explícito con fuente única en config (patrón A2/A4).

## What Changes

- `core/metrics.py`: kernels aceptan `trading_days: int`; docstrings actualizados
- `core/config.py`: campo `trading_days_per_year: int = 252` validado [1,366]
- `data_fetch.py`: 4º parámetro requerido; pipeline lo pasa desde config
- Tests: expectativas exactas con custom days + contrato de firma
- Fuera de scope: detección automática de calendario (decisión diferida decision-log)

## Capabilities

### Modified Capabilities
- `configuration-contract`: nuevo campo validado.
- `market-data-contract`: anualización usa días configurados.
