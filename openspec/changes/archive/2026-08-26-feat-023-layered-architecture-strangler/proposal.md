# Proposal: feat-023-layered-architecture-strangler

## Why

La orquestación (`app/pipeline.py:main`) conoce la capa de transporte: llama `download_and_calculate_metrics` directamente, acoplando el dominio a yfinance (M3). El boundary de red vive en `_fetch_batch` pero la INYECCIÓN no existe — cada test offline depende de monkeypatch del interno. El Strangler Fig protegido por la red feat-021 introduce el Protocol como costura (seam) arquitectónica sin big-bang.

## What Changes

- `portfolio_engine/data/provider.py` (nuevo): `MarketDataProvider` Protocol (`fetch_metrics(tickers, risk_free_rate, lookback_years, trading_days_per_year) -> MetricsBundle`) + adaptador `YFinanceProvider` que encapsula TODA la lógica actual del fetcher
- `data/data_fetch.py`: funciones existentes delegan en el adapter (compatibilidad pública intacta)
- `app/pipeline.py`: `main(tickers, config=None, provider=None)` — None construye `YFinanceProvider()` por defecto; el flujo deja de importar transporte
- E2E migrado a inyección con `FakeProvider` (sin monkeypatch); tests de batch-boundary se conservan (cubren el adapter internamente)
- Fuera de scope: mover archivos de sitio (churn>beneficio), Reporter interface para viz (diferida), reemplazo real del proveedor

## Capabilities

### Modified Capabilities
- `package-interface`: nueva frontera expuesta — Protocol inyectable que desacopla orquestación de transporte.
