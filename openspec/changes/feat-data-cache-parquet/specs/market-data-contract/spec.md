## ADDED Requirements

### Requirement: Caché parquet con key determinista y degradación graceful

`YFinanceProvider` SHALL ofrecer caché local opcional en `data/cache/*.parquet` con key `hashlib.sha256(sorted(upper(tickers))+start.isoformat()+end.isoformat()+trading_days+CACHE_VERSION)` truncada 16 hex + prefijo `v1_`. Hit válido SHALL evitar `_fetch_batch` (segunda llamada idéntica con `use_cache=True` y sin `--refresh-cache` no invoca red). `--refresh-cache` SHALL ignorar hit y forzar re-descarga + overwrite atómico. Socket sin red desde cache SHALL producir bundle idéntico a la corrida que pobló el cache. Corrupción (`ArrowInvalid`/`OSError`/`ValueError`) SHALL degradar a warning+`unlink`+fallback a red sin propagar excepción. Ausencia de `pyarrow` o `cache_dir=None`/`use_cache=False` SHALL bypass sin tocar FS.

#### Scenario: segunda llamada misma key no toca red
- **WHEN** `provider=YFinanceProvider(cache_dir=tmp_path)` hace dos `fetch_metrics` idénticos con `_fetch_batch` espiado
- **THEN** el contador de llamadas queda en 1 tras la segunda y solo 1 parquet `v1_*.parquet` existe

#### Scenario: refresh fuerza re-descarga
- **WHEN** existe cache poblado y segunda llamada usa `refresh_cache=True` (o CLI `--refresh-cache`)
- **THEN** contador sube a 2 y `mtime` del parquet avanza

#### Scenario: corrida sin red desde cache idéntica
- **WHEN** cache poblado y siguiente `fetch_metrics` usa `_fetch_batch` que levanta `AssertionError("no network")`
- **THEN** retorna sin excepción y `historical_prices` es `allclose` al bundle original

#### Scenario: corrupción degradada
- **WHEN** el parquet contiene bytes corruptos y se llama `fetch_metrics`
- **THEN** se emite warning con "cache corrupt", el archivo corrupto es eliminado y se refetchtea con éxito (contador 1, parquet reescrito válido)

#### Scenario: tickers orden invariante y trading_days en key
- **WHEN** se calcula `_cache_key(["WMT","AAPL"],start,end,252)` vs `["AAPL","WMT"]` y `252` vs `365`
- **THEN** orden permutado da misma key; cambio de `trading_days` da key distinta

#### Scenario: bypass sin cache mantiene contrato
- **WHEN** `cache_dir=None` o `pyarrow` ausente y se invoca `fetch_metrics`
- **THEN** no se crea archivo y el comportamiento es idéntico al legacy (retry 3, etc.)

## MODIFIED Requirements

### Requirement: Ingesta con caché opcional
La ingesta batch con `auto_adjust=False`, fallback `Adj Close→Close`, rechazos agregados y reintentos sigue vigente; el caché SHALL envolverla sin alterar su semantica cuando está deshabilitado.

#### Scenario: suite offline verde sin tocar red
- **WHEN** `pytest` corre con `use_cache` deshabilitado (default `cache_dir=None` o tests con `tmp_path` vacío)
- **THEN** la suite permanece offline y verde sin crear `data/cache/*.parquet` en el repo
