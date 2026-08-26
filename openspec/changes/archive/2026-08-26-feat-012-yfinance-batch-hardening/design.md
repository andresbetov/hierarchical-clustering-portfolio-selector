# Design: feat-012-yfinance-batch-hardening

## Context

Dependencias previas resueltas: rf/lookback requeridos (feat-007/011), alineación posterior (feat-008). yfinance 1.7.0 en lock; pandas explícita desde feat-008.

## Goals / Non-Goals

**Goals:** un request batch; rechazos nombrados agregados; fallback de columna; retry acotado; todo testeable offline via monkeypatch.
**Non-Goals:** parquet cache/duckdb (diferida — decision-log); tenacity (D1); threading tuning del batch (defaults); rate-limit sophisticated strategy.

## Decisions

### D1 — Retry manual stdlib sobre tenacity
3 intentos con backoff [1,2]s cubre el caso transitorio real (YFRateLimitError puntual). tenacity es una dependencia runtime nueva para una política trivial; se reintroducirá si las estrategias crecen (decision-log: diferida).
*Alternativa descartada:* backoff exponencial sin tope / decorador genérico — más máquina para el mismo contrato.

### D2 — Extracción como función pura
`_extract_adjusted_close(panel, ticker)` no toca red ni estado: Frame in → (values,index) | None+motivo. Los tests construyen DataFrames sintéticos de 5 filas — deterministas en cualquier runner.

### D3 — NaN trimming honesto
`dropna()` sobre la serie elegida + log del conteo recortado por ticker: el proveedor ensucia colas (parciales intradía); mejor recortar visible que propagar NaN a retornos.

### D4 — Grupo de columnas tolerante a shapes de yfinance
Batch devuelve MultiIndex (ticker, field) cuando hay >1 ticker y flat para 1. `_extract_adjusted_close` maneja ambos (get_level_values check) — evita branch frágil en caller.

## Risks / Trade-offs

- Backoff fijo podría dormirse ante rate-limit largo: aceptado, 3 intentos máximo — failures visibles en log final
- batch grupal puede reintentar TODO por fallo de UNO: correcto a nivel transport (la extracción per-ticker sigue filtrando individualmente)
