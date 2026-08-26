# Proposal: feat-007-risk-free-single-source

## Why

La tasa libre de riesgo vive en dos fuentes con valores distintos: `data_fetch.py:15` tiene default `0.03` mientras `PortfolioConfig.risk_free_rate = 0.045`. La ruta del pipeline pasa el valor de config (correcto), pero cualquier uso directo del fetcher hereda silenciosamente 0.03 — Sharpe desplazado ~150 bps sin error visible. Un parámetro de negocio con default divergente es la definición exacta de doble fuente de verdad.

## What Changes

- `data_fetch.py`: firma `download_and_calculate_metrics(ticker_symbols: list, risk_free_rate: float)` — **requerido, sin default**; única fuente de verdad pasa a ser `PortfolioConfig`
- `tests/test_data_fetch_contract.py` (nuevo): llama sin el argumento y espera `TypeError` (binding falla antes de tocar red — testeable offline)
- Fuera de scope: validación/congelación de config (feat-013), serie histórica de tasas (decisión diferida registrada)

## Capabilities

### New Capabilities
- `market-data-contract`: contrato de los datos de mercado y su provenance — de dónde deben venir los insumos (tasa, calendario, alineación) y qué garantiza el proveedor. Capacidad que los features A3/A4/C2 ampliarán.

### Modified Capabilities
Ninguna.

## Impact

- **Artefactos**: data_fetch.py (una línea), test nuevo
- **Riesgo**: mínimo; el único caller interno ya pasa la tasa desde config
