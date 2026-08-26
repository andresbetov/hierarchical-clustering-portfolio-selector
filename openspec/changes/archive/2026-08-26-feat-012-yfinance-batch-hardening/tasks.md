# Tasks: feat-012-yfinance-batch-hardening

## 1. Núcleo de ingesta

- [x] 1.1 data_fetch.py: `_fetch_batch` (yf.download batch, lazy import) + retry loop acotado con backoff y logs — verificar: ruff+pyright
- [x] 1.2 `_extract_adjusted_close` puro: Adj Close→Close-fallback-nombrado→rechazo; manejo MultiIndex/flat; dropna con log — verificar: tipos
- [x] 1.3 Rewire `download_and_calculate_metrics`: un batch, extracción per-ticker, rechazos agregados en 1 warning, dicts en orden original — verificar: flujo sin lógica muerta

## 2. Tests offline

- [x] 2.1 Monkeypatch `_fetch_batch`: multi-success / fallback Close / sin columnas / frame vacío / transitorio 2 fallos+éxito (3 calls) / fallo total vacío sin raise / NaN colas recortadas con log / passthrough rf-lookback — verificar: suite crece verde
- [x] 2.2 Gates completos + tracker done + progress/handoff + commits + archive + PR merge
