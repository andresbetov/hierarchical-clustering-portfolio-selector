# Proposal: feat-012-yfinance-batch-hardening

## Why

La capa de descarga (C2) falla de tres formas silenciosas: descarga serial ticker-a-ticker (12 requests, rate-limit-prone), `except Exception: continue` que hace indistinguible un fallo de un éxito vacío, y dependencia ciega de la columna "Adj Close" (drift documentado de yfinance desde 0.2.51 — issues #2255/#2197). El pipeline puede terminar con universo vacío sin ningún indicio de por qué.

## What Changes

- `data_fetch.py`:
  - descarga batch única vía `_fetch_batch(tickers, start, end)` sobre `yf.download(group_by="ticker", auto_adjust=False, progress=False)`
  - helper puro `_extract_adjusted_close(panel, ticker) -> (values, index) | None` con política: `Adj Close` → si ausente, `Close` + warning nombrado → si nada, rechazo nombrado
  - validación: frame vacío o serie toda-NaN ⇒ rechazo nombrado; `dropna()` con log de recortes
  - reintentos acotados (3 intentos, backoff 1s/2s) solo ante excepciones de la llamada batch, con log por intento
  - todos los rechazos se acumulan y emiten en UN warning agregado al final
- `tests/test_data_fetch_contract.py`: ampliado con ~8 casos offline via monkeypatch de `_fetch_batch` (frames sintéticos, fallos transitorios, fallback de columna)
- Nueva dependencia: **ninguna** — retry manual stdlib (tenacity diferida a decision-log)

## Capabilities

### Modified Capabilities
- `market-data-contract`: añade requisitos de ingesta robusta — batch explícito, columna primaria con fallback nombrado, rechazos agregados con nombre, reintentos acotados ante errores transitorios.
