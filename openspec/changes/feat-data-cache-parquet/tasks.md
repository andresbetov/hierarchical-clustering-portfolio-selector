## 1. Contratos y validación (rojo primero)

- [x] 1.1 Módulo `data/cache.py` con `CACHE_VERSION`, `_cache_key`, `_cache_path`, lectura corrupción->warning+unlink y escritura atómica `mkstemp+os.replace` (`snappy`) — verificar: tests `test_provider_cache.py` en rojo pre-impl (contador `_fetch_batch` 2 tras segunda llamada, `ValueError` import, etc.)
- [x] 1.2 `tests/test_provider_cache.py`: hit evita red, `refresh` fuerza, offline desde cache idéntico, determinismo hash orden/trading_days, corrupción+atomic, `cache_dir=None` bypass, `0 tickers` sin FS — verificar: 5-7 tests en rojo con `ImportError`/`TypeError` pre-impl
- [x] 1.3 `tests/test_cli.py`: flag `--refresh-cache` (`store_true`, default `False`, `help`) y propagation a `YFinanceProvider.refresh_cache` con `tmp_path` inyectado — verificar: `parse_args` rojo pre-impl

## 2. Implementación operativa

- [x] 2.1 `pyproject.toml` `pyarrow>=14` + `uv lock` + `uv sync --frozen` verde (3.11-3.13). `data/cache/.gitkeep` + `.gitignore: data/cache/* + !data/cache/.gitkeep` (check `git check-ignore` match). Verificar: `uv lock --check` y `import pyarrow` OK
- [x] 2.2 `data/provider.py`: `YFinanceProvider(cache_dir: Path|None=None, refresh_cache: bool=False, use_cache: bool|None=None)` con key ventana resuelta (`_resolve_window`), hit recomputa métricas desde parquet sin tocar `_fetch_batch`, grace `pyarrow`/`OSError`/`ArrowInvalid`, `mkdir parents`, filename solo hash, `0 tickers` early-return — verificar: hit 1 llamada, refresh 2, corrupto refetch, `252!=365` key distinta, `cache_dir=None` sin archivo
- [x] 2.3 `app/pipeline.py` `generate_complete_analysis_report(..., provider=None)` forward a `main`; `cli.py` `_build_parser()`+`main(argv=None)` con `--refresh-cache`/`--universe`, construcción `YFinanceProvider(cache_dir=Path("data/cache"), refresh_cache=...)` — verificar: `cli --help` documenta flags, `cli --refresh-cache` fuerza 2ª llamada, import sin side-effect

## 3. Verificación integral y cierre

- [x] 3.1 Suite completa `./init.sh` exit 0 (200+ tests) + `openspec validate --specs --changes --strict` — output registrado como evidence
- [x] 3.2 `CHANGELOG.md` Unreleased (Added cache), `README.md` sección operativa cache si aplica, `progress.md` actualizado — verificar: docs sincronizadas y repo `git status` limpio
