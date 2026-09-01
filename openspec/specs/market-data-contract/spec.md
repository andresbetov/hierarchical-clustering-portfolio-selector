# market-data-contract Specification

## Purpose
Definir de dónde provienen los insumos del análisis (tasa libre de riesgo, precios, calendario) y garantizar que cada uno tenga exactamente una fuente autoritativa, de modo que entradas divergentes sean imposibles o fallas ruidosas.

## Requirements

### Requirement: Tasa libre de riesgo sin default local

`download_and_calculate_metrics` SHALL exigir `risk_free_rate` como parámetro obligatorio sin valor por defecto; SHALL NOT existir ninguna constante de tasa fuera de `PortfolioConfig`, y la ruta del pipeline SHALL tomarla exclusivamente de ahí.

#### Scenario: uso directo sin tasa falla ruidoso
- **WHEN** se invoca el fetcher sin pasar `risk_free_rate`
- **THEN** lanza `TypeError` en el binding (antes de ejecutar descarga alguna)

#### Scenario: pipeline usa la config
- **WHEN** `main()` corre con una `PortfolioConfig`
- **THEN** el Sharpe por activo se calcula con `config.risk_free_rate` (0.045), nunca un default enterrado

### Requirement: Alineación temporal antes de estadística multivariada

Toda matriz de retornos que alimente correlación, covarianza, clustering o asignación SHALL construirse sobre el calendario común (intersección) de los tickers involucrados, ordenado ascendente. La falta de densidad mínima (menos de 2 fechas comunes) SHALL fallar ruidosamente con `ValueError`, y la longitud desigual de series sin alinear SHALL ser rechazada explícitamente en vez de apilarse por posición.

#### Scenario: ticker con historial más corto
- **WHEN** un ticker del universo carece de fechas presentes en otros
- **THEN** las matrices usan solo filas con todas las series presentes y ninguna fila se compara contra fecha ajena

#### Scenario: calendarios disjuntos
- **WHEN** no existe solapamiento suficiente entre series
- **THEN** se levanta `ValueError` describiendo la intersección vacía en lugar de producir matrices degeneradas

#### Scenario: equal-length legacy intacto
- **WHEN** se llama `construct_returns_matrix` con arrays de igual longitud como antes
- **THEN** su comportamiento y shapes son idénticos a los previos al change

### Requirement: Ventana explícita y calendario-precisa

La ventana de descarga SHALL derivarse de un parámetro `lookback_years` requerido (sin default local en el proveedor) interpretado en años calendario exactos — no en múltiplos de 365 días. El cálculo de fechas SHALL vivir en una función pura testeable sin red, y el 29-febrero como fecha límite SHALL resolverse al 28 del mes en años objetivo no bisiestos en lugar de fallar.

#### Scenario: ventana de cinco años cruza bisiesto
- **WHEN** la fecha fin es 29-feb-2024 y lookback_years=5
- **THEN** la fecha inicio resuelve a 28-feb-2019 sin excepción

#### Scenario: uso directo sin lookback falla ruidoso
- **WHEN** se invoca el fetcher sin pasar `lookback_years`
- **THEN** lanza `TypeError` en el binding, antes de cualquier descarga

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

### Requirement: Guard de solapamiento por ratio en alineación
`align_prices_to_common_calendar` SHALL excluir con warning nombrado (ticker + coverage) a tickers cuya cobertura < `minimum_overlap_ratio` contra el span común (unión de fechas), preservando sin truncar la historia del resto. Con `ratio=1.0` el comportamiento SHALL ser bit-a-bit idéntico al inner-join vigente. Tras exclusión, el guard `MIN_COMMON_ROWS=2` SHALL seguir aplicándose; manejo por-ticker completo (union+forward-fill) queda explícitamente diferido a v0.2.0.

#### Scenario: delisted/IPO trunca silenciosamente sin guard
- **WHEN** A/B tienen 250 filas comunes y C solo 125 (50% solapa) con `minimum_overlap_ratio=0.9`
- **THEN** C es excluido con warning nombrado, `aligned` contiene solo A/B con 250 filas (no 125) y matrices posteriores no contienen C

#### Scenario: invariancia sin delistings
- **WHEN** todos los tickers solapan >=0.9 (universo 12 large-caps nominal)
- **THEN** `aligned` es idéntico bit-a-bit al resultado pre-guard (mismo `frame.dropna` + orden ascendente)

#### Scenario: calendarios disjuntos aún falla ruidoso
- **WHEN** tras filtrado por ratio la intersección de supervivientes tiene <2 filas
- **THEN** lanza `ValueError` con `too small|intersection` (mismo que `MIN_COMMON_ROWS`) en lugar de matriz degenerada

### Requirement: Chart 4 full-universe alineado
`generate_complete_analysis_report` SHALL construir la matriz full-universe de chart 4 sobre calendario común (mismo guard), no sobre `historical_prices` crudos de longitudes distintas.

#### Scenario: chart 4 no crashea con IPO
- **WHEN** un ticker del universo tiene historia 50% más corta y se genera el reporte completo
- **THEN** chart 4 se genera sin `ValueError: lengths differ` y usa el universo superviviente del guard
