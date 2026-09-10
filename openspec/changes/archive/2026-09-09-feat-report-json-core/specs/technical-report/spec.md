## Purpose

El sistema SHALL producir un reporte técnico machine-readable por corrida: JSON estricto (conforme a RFC 8259 sin tokens NaN/Infinity), versionado por schema, con fingerprint determinista de su configuración, de modo que un consumidor técnico pueda leer, comparar y auditar resultados sin re-analizar el programa.

## ADDED Requirements

### Requirement: Sanitización JSON estricta

La serialización del reporte SHALL emitir JSON conforme a RFC 8259: todo valor numérico no finito (nan, inf, -inf) SHALL convertirse a `null` antes de serializar, y el volcado SHALL fallar con error ante cualquier token no-JSON si alguno escapara al sanitizador. `null` significa "no finito o indefinido", nunca "cero". Los contenedores numpy (arrays y escalares), tuplas, Path y fechas SHALL convertirse a sus equivalentes JSON-nativos (list, float/int/bool, str, ISO-8601).

#### Scenario: payload envenenado serializa a JSON estricto

- **WHEN** se serializa un payload conteniendo ndarray 2-D, np.int64, np.float32, nan, inf, np.bool_, Path y date
- **THEN** el texto resultante se parsea con un parser estricto que rechaza las constantes NaN/Infinity/-Infinity y todos los valores no finitos quedan como `null`

#### Scenario: null no se confunde con cero

- **WHEN** una métrica es indefinida (por ejemplo Sharpe ante varianza nula)
- **THEN** el campo toma el valor `null` y el consumidor puede distinguirlo de un `0.0` legítimo

### Requirement: Escritura single-file determinista

La escritura del reporte SHALL producir exactamente un archivo JSON por corrida en la ruta indicada, creando el directorio destino si no existe, y sobrescribiendo el contenido previo. La escritura SHALL ser la única salida de archivo del reporte (no JSON Lines, no archivo por sección).

#### Scenario: segunda corrida sobrescribe

- **WHEN** se escribe dos veces un reporte en la misma ruta
- **THEN** existe un solo archivo y su contenido es el de la última escritura

### Requirement: Fingerprint determinista de configuración

El reporte SHALL incluir un fingerprint de configuración derivado de forma determinista (hash truncado de la serialización canónica de la configuración + universo ordenado + ventana de datos resuelta + versión del engine). Construcciones idénticas de configuración SHALL producir el mismo fingerprint y el cambio de cualquier parámetro de configuración SHALL cambiarlo. El identificador de corrida SHALL derivarse del fingerprint (prohibido el uso de aleatoriedad tipo uuid).

#### Scenario: misma configuración produce mismo fingerprint

- **WHEN** se construyen dos fingerprints desde la misma configuración, universo y ventana
- **THEN** ambos producen la misma cadena hex truncada

#### Scenario: cambio de parámetro cambia fingerprint

- **WHEN** se altera cualquier campo de configuración (umbrales de filtro, método de asignación, estimador, linkage, tasa libre)
- **THEN** el fingerprint cambia

### Requirement: Envelope versionado ausente-tolerante

Todo reporte SHALL abrir con un envelope que declare `schema_version` entera (inicia en 1), fingerprint, timestamp de generación en ISO-8601, universo ordenado y ventana de datos. Las secciones de diagnóstico aún no implementadas SHALL poder estar ausentes del documento sin invalidarlo: un consumidor de un artefacto intermedio ve menos claves sin error de esquema.

#### Scenario: envelope mínimo válido

- **WHEN** se serializa un reporte solo con envelope (sin secciones de diagnóstico)
- **THEN** `schema_version == 1` y el documento parsea como JSON estricto con las claves del envelope presentes
