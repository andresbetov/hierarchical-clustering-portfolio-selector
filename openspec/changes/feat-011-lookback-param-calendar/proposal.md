# Proposal: feat-011-lookback-param-calendar

## Why

La ventana de descarga está enterrada en `data_fetch.py:28-29`: `timedelta(days=5*365)` hardcodeado con tres defectos — no parametrizable, aritméticamente mentiroso (1825 días ignora bisiestos de un quinquenio real: 1826/1827), y acoplada al mismo bloque temporal que la alineación (por eso A3→A4 según DAG). Además el default local recrearía el patrón doble-fuente que feat-007 eliminó para risk_free_rate.

## What Changes

- `data_fetch.py`: nueva función pura `_resolve_window(today, lookback_years) -> tuple[date, date]` (año-calendario vía replace, clamp Feb-29→Feb-28); firma `download_and_calculate_metrics(ticker_symbols, risk_free_rate, lookback_years)` — lookback **requerido sin default** (misma filosofía del contrato)
- `core/config.py`: atributo `lookback_years = 5` (mutable hasta feat-013)
- `app/pipeline.py`: pasa `config.lookback_years` al fetcher; log incluye ventanas resueltas
- `tests/test_data_fetch_contract.py`: extiende contractos — TypeError por segundo requerido, introspección, y tests puros de `_resolve_window` (año normal, span bisiesto→no-bisiesto clamp, lookback inválido)
- Fuera de scope: constante 252 anualización (feat-017/B4), parquet cache (diferida), validación batch yfinance (feat-012)

## Capabilities

### Modified Capabilities
- `market-data-contract`: añade requisito "ventana explícita y calendario-precisa" — la ventana SHALL derivarse de un parámetro requerido en años calendario y SHALL NOT existir como constante enterrada.
