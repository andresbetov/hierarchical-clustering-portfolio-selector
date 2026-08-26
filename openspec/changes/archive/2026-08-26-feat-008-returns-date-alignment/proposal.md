# Proposal: feat-008-returns-date-alignment

## Why

`construct_returns_matrix` apila series por posición (`np.array(list).T`) sin usar los índices de fecha que el fetcher captura y devuelve (A3, auditoría): si un ticker abre con retraso o falta un día de boda, las filas comparadas corresponden a fechas distintas — correlaciones/covarianzas falsas sin ningún error. Este es el defecto fundacional del bloque de datos: C3 (guards), C4, y feat-018 (HRP real) consumen matrices que hoy no garantizan alineación temporal.

## What Changes

- `pyproject.toml`: declarar `pandas>=2.0` como dependencia runtime explícita (ya existía transitivamente vía yfinance)
- `core/metrics.py`:
  - nueva `align_prices_to_common_calendar(prices, dates) -> dict[str, np.ndarray]` — intersección de calendarios via pandas DataFrame inner-join, orden ascendente; `ValueError` si la intersección tiene <2 filas o si algún array/index difieren en longitud
  - guard en `construct_returns_matrix`: longitudes desiguales ⇒ `ValueError` con detalle (antes: silencio)
- `app/pipeline.py`: la sección estadística consume primero la alineación (`filtered_prices` + `filtered_dates`); charts siguen usando series completas
- `tests/test_alignment.py` (nuevo): ~7 casos offline deterministas (calendarios desfasados, ticker corto, disjuntos totales, densidad mínima, preservación de orden, equal-length legacy intacto)
- Fuera de scope: outer/ffill para backtests (diferido a B6), descarga/validación del fetcher (feat-012)

## Capabilities

### Modified Capabilities
- `market-data-contract`: añade requisito de alineación temporal por calendario común antes de cualquier estadística multivariada. (Modified — los requirements previos se mantienen intactos.)

## Impact

- **Artefactos**: metrics.py, pipeline.py, pyproject, uv.lock (pandas sube a directa), test nuevo
- **Riesgo medio-bajo**: cambia NUMÉRICAMENTE resultados cuando haya solapamientos imperfectos (ese es exactamente el objetivo); suite actual usa longitudes iguales ⇒ verdes por diseño
