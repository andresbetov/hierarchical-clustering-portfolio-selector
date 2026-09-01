## Why

Rate-limiting de yfinance activo desde 2025 (issues #2280/#2422/#2526 — `YFRateLimitError: Too Many Requests`) hace que corridas repetidas fallen intermitentemente incluso con retry batch de 3 intentos (`data_fetch.py:61-87`). Cada `main()` exige red exitosa; sin caché, CI offline evita el problema a costa de no probar ingestion real, pero el uso productivo repite el fetch de 5 años/12 tickers a cada corrida. La comunidad mitiga con `yfinance-cache`/`requests_cache`, pero `requests_cache` es incompatible con `curl_cffi.Session` usado por yfinance 0.2.58+ (`#2486`) y el caché interno `tkr-tz.db` introduce flakiness adicional. Se requiere caché local operativo mínimo: parquets en `data/cache/*.parquet` con key determinista por universo+ventana+trading_days e invalidación por cambio de key.

## What Changes

- Nueva dependencia `pyarrow>=14` (parquet `snappy`, soporta 3.11-3.13 y `pandas>=2.0` ya declarado).
- Nuevo módulo `portfolio_engine/data/cache.py` con helpers puros: `CACHE_VERSION="v1"`, `_cache_key(tickers,start,end,trading_days)` (`hashlib.sha256` 16 hex sobre `sorted(upper)+start.isoformat()+end.isoformat()+trading_days+v1`), `_cache_path`, lectura/escritura atómica (`mkstemp+pq.write_table+os.replace`, corrige corrupción con warning+unlink, graceful si pyarrow ausente).
- `portfolio_engine/data/provider.py`: `YFinanceProvider(cache_dir: Path|None=None, refresh_cache: bool=False, use_cache: bool|None)` — cuando `use_cache` es `None` el default es `cache_dir is not None`; `cache_dir=None` fuerza bypass. Intercepta en `fetch_metrics` por encima de retry: hit válido → recomputa `asset_metrics` desde parquet sin tocar `_fetch_batch`; `--refresh-cache` ignora hit; miss/empty/corrupto → `download_and_calculate_metrics` + escritura atómica solo si bundle no vacío. Casos borde: `0 tickers` early-return sin FS, `mkdir parents` lazy, `PermissionError` degradado a warning, filename solo hash (sin traversal).
- `portfolio_engine/app/pipeline.py`: `generate_complete_analysis_report(..., provider=None)` acepta provider inyectado (forward a `main`) para que reporte también use cache.
- `portfolio_engine/cli.py`: `argparse` con `--refresh-cache` (`store_true`) + `--universe` (ya previsto feat-039) — factory `_build_parser()` no side-effect al importar; `main(argv=None)` construye `YFinanceProvider(cache_dir=Path("data/cache"), refresh_cache=args.refresh_cache)` y lo pasa a pipeline.
- `data/cache/.gitkeep` + `.gitignore: data/cache/`; CI permanece offline (`use_cache` falso por defecto sin `cache_dir` explícito — tests usan `tmp_path` y `use_cache=False` bypass).

## Capabilities

### New Capabilities
- `data-cache`: Caché parquet operativo con key determinista, atomic write y degradación graceful.

### Modified Capabilities
- `market-data-contract`: Ingesta con caché opcional (hit evita red, `--refresh-cache` fuerza re-descarga, corrupción fallback).

## Impact

- Código: `data/cache.py` nuevo, `data/provider.py`, `app/pipeline.py`, `cli.py`, `pyproject.toml`, `.gitignore`, `data/cache/.gitkeep`.
- Docs: `CHANGELOG.md`, `progress.md`.
- Tests: `tests/test_provider_cache.py` (hit evita `_fetch_batch`, `refresh` fuerza, offline desde cache, determinismo hash, atomic/corruption, permisos) + `tests/test_cli.py` flag.
- Riesgos: hash colisión <2^-64 despreciable; ventana `_resolve_window` diaria invalida cache diario (intencionado spec — no TTL); `pyarrow` import lazy evita crash si ausente.
