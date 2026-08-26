# market-data-contract Specification (delta)

## ADDED Requirements

### Requirement: Descarga batch explícita

El proveedor SHALL descargar el universo completo en una única llamada batch con ajuste de precios solicitado explícitamente (`auto_adjust=False`), y SHALL NO emitir un request secuencial por ticker.

#### Scenario: universo completo
- **WHEN** se solicitan N tickers
- **THEN** se realiza una sola llamada batch que sirve a todos, independientemente de cuántos fallen después en extracción

### Requirement: Columna primaria con fallback nombrado

La extracción SHALL preferir `Adj Close`; si la columna no existe SHALL usar `Close` emitiendo warning con el nombre del ticker; si ninguna existe SHALL rechazar el ticker con motivo nombrado.

#### Scenario: proveedor sin Adj Close
- **WHEN** el frame devuelto solo contiene `Close`
- **THEN** los valores provienen de `Close` y existe un warning identificando al ticker

### Requirement: Rechazos agregados y con nombre

Todo frame vacío, serie toda-NaN o sin columna utilizable SHALL ser rechazado; los rechazos del batch SHALL acumularse y emitirse en un único log que incluya ticker y motivo. Si todos son rechazados, la función SHALL retornar estructuras vacías sin excepción.

#### Scenario: todos rechazados
- **WHEN** ningún ticker produce datos utilizables
- **THEN** se retornan dicts vacíos y existe un log nombrando cada rechazo

### Requirement: Reintentos acotados ante fallos transitorios

Los errores de la llamada batch SHALL reintentarse hasta un máximo fijo con backoff creciente, registrando cada intento; agotados los intentos SHALL resultar en retorno vacío con log, no en excepción propagada.

#### Scenario: fallo transitorio
- **WHEN** la llamada falla dos veces y triunfa en la tercera
- **THEN** el resultado contiene los datos y el historial muestra tres intentos
