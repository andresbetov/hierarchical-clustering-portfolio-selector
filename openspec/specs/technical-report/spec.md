# technical-report Specification

## Purpose
El sistema SHALL producir un reporte técnico machine-readable por corrida: JSON estricto (conforme a RFC 8259 sin tokens NaN/Infinity), versionado por schema, con fingerprint determinista de su configuración, de modo que un consumidor técnico pueda leer, comparar y auditar resultados sin re-analizar el programa.

## Requirements

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

### Requirement: Diagnóstico de exclusiones del filtro con distancias al umbral

El reporte técnico SHALL poder incluir, para cada ticker solicitado del universo, un motivo de clasificación del embudo de filtrado y sus distancias firmadas al umbral. Los motivos de rechazo por métrica no finita o por umbral SHALL usar exactamente la misma nomenclatura que el filtro de producción. `d_sharpe` SHALL ser `sharpe − minimum_sharpe_threshold` y `d_vol` SHALL ser `maximum_volatility_threshold − vol` (negativa = excluido por esa vía); AMBAS distancias SHALL ser `null` cuando cualquiera de las métricas no es finita o el motivo es de ingesta (incluida la ausencia de precios para el ticker). Los conteos SHALL sumar exactamente el tamaño del universo solicitado (tickers duplicados se deduplican). La clasificación de un superviviente SHALL ser distinguible de la de un excluido y reproducir el criterio del filtro de producción con el mismo orden de guardias (no-finito primero, luego Sharpe, luego volatilidad); en la frontera exacta (sharpe == mínimo, vol == máxima) el ticker SHALL clasificarse como superviviente, igual que el filtro con comparadores estrictos. Umbrales de configuración no finitos (configuración patológica) SHALL serializar como `null` vía el sanitizador, nunca como token inválido.

#### Scenario: excluido por poco queda cuantificado

- **WHEN** un ticker con Sharpe 0.28 frente a un mínimo de 0.30 entra al diagnóstico
- **THEN** su motivo es `below_min_sharpe`, `d_sharpe ≈ −0.02` y `d_vol` es positiva (no es su causa)

#### Scenario: activo plano sin distancias

- **WHEN** un ticker tiene Sharpe no finito (activo con varianza nula) y volatilidad 0.0
- **THEN** su motivo es `sharpe_non_finite` con ambas distancias `null`, nunca 0

#### Scenario: ticker sin métricas

- **WHEN** un ticker del universo pedido no aparece entre las métricas producidas por la ingesta
- **THEN** su motivo es `ingestion_rejected` con distancias `null`, y los conteos siguen cuadrando

#### Scenario: podado por calendario

- **WHEN** un ticker pasa ambos umbrales con métricas finitas pero no está en el conjunto final superviviente
- **THEN** su motivo es `overlap_pruned` (única capa de exclusión restante dentro de la corrida) y sus distancias reflejan su holgura

#### Scenario: superviviente legible

- **WHEN** un ticker está en el conjunto final
- **THEN** su motivo es `kept` con ambas distancias positivas calculadas (detección de "casi pasa" cuando `|d| < 0.05`)

#### Scenario: conteos consistentes

- **WHEN** se agrega el diagnóstico completo para un universo pedido
- **THEN** `kept + rechazados == |universo pedido|` y ningún ticker pedido queda sin clasificar

### Requirement: Diagnóstico de asignación con concentración, diversificación y desvío de restricciones

El reporte técnico SHALL poder incluir el diagnóstico de la asignación final: HHI = Σw² y N efectivo = 1/HHI con el mandato Σw == 1 ± 1e-9 verificado antes de elevar; ratio de diversificación DR = Σ(wᵢ·σᵢ)/σ_p y contribuciones de riesgo RCᵢ = wᵢ·(Σw)ᵢ/σ_p² (ΣRC SHALL ser 1) con su dispersión, calculados SIEMPRE sobre la covarianza rebanada al subconjunto de pesos (regla feat-028: la covarianza del universo completo con un vector de subconjunto es inválida); y la telemetría raw-vs-constrained del solucionador de límites (distancia L1, caída máxima de peso, nº de pesos alterados, bounds efectivos y bandera de relajación). El universo vacío SHALL producir secciones `null`, nunca ceros. Un activo único SHALL producir HHI=1.0, DR=1.0, RC=[1.0] por identidad. `raw_vs_constrained` SHALL calcularse cuando el método es HRP con recompute determinista (bit-idéntico al motor) o cuando se proveen los pesos crudos explícitamente, y SHALL ser `null` para métodos no-HRP sin pesos crudos. Ante cualquier métrica degenerada (σ_p bajo el piso numérico, pesos no finitos) las secciones afectadas SHALL ser `null`/NaN, nunca `inf`.

#### Scenario: cartera equiponderada cuantificada

- **WHEN** 4 activos con pesos 25% cada uno entran al diagnóstico con una covarianza definida positiva
- **THEN** HHI == 0.25, N efectivo == 4.0, y ΣRC == 1 dentro de la tolerancia

#### Scenario: activo único por identidad

- **WHEN** un solo activo con peso 100% entra al diagnóstico
- **THEN** HHI == 1.0, N efectivo == 1.0, DR == 1.0 y su contribución de riesgo es 1.0

#### Scenario: violación del mandato de inversión

- **WHEN** los pesos no suman 1 dentro de la tolerancia del motor (1e-9)
- **THEN** el diagnóstico falla con error nombrado en lugar de fabricar números

#### Scenario: covarianza mayor que la cartera se rebanada

- **WHEN** el diagnóstico recibe una covarianza N×N del universo filtrado con pesos de un subconjunto M<N (ruta legacy)
- **THEN** DR y RC se computan sobre la submatriz M×M correspondiente a los pesos, coincidiendo con el cálculo directo sobre esa submatriz

#### Scenario: telemetría del solucionador de límites

- **WHEN** el método es HRP y se proveen los pesos crudos pre-restricción (o el recompute determinista está disponible)
- **THEN** el diagnóstico expone la distancia L1 crudo-vs-restringido, la caída máxima de peso, el nº de pesos alterados, los bounds efectivos y si el mandato fue relajado

#### Scenario: método no jerárquico sin pesos crudos

- **WHEN** el método de asignación no es HRP y no se proveen pesos crudos
- **THEN** `raw_vs_constrained` es `null` (el vector pre-restricción de los optimizadores legacy no está expuesto; fabricarlo sería deshonesto) y el método queda declarado en la sección

### Requirement: Diagnóstico de riesgo in-sample con serie, cola y drawdown

El reporte técnico SHALL poder incluir el riesgo in-sample de la asignación final: la serie de log-retornos diarios de la cartera (`portfolio_return_series`), las métricas de cola (`tail_risk_metrics`: Sortino log-coherente y VaR/CVaR95 históricos diarios) y las métricas de drawdown (`drawdown_metrics`: caída máxima y Calmar). La serie SHALL construirse como matriz de log-retornos por activo en orden de claves por el vector de pesos en el mismo orden; cualquier mismatch de claves SHALL fallar con error nombrado. El objetivo diario del Sortino SHALL ser `ln(1+rf)/trading_days` (coherencia-log con el Sharpe del proyecto) y la desviación downside SHALL dividirse por el N total (días sin caída cuentan como cero); sin días de caída, Sortino SHALL ser `null` con motivo mientras VaR/CVaR siguen numéricos. `VaR_95_daily` SHALL ser `-cuantil(r, 0.05)` con interpolación lineal y `CVaR_95_daily` SHALL ser `-media(r | r ≤ q05)` (cola inclusiva); SHALL cumplirse siempre `CVaR ≥ VaR` en forma firmada, y `CVaR ≥ |VaR|` cuando el VaR es no negativo (cola real de pérdidas); VaR/CVaR JAMÁS SHALL anualizarse. `max_drawdown` SHALL ser `≤ 0` siempre y `calmar` SHALL ser `retorno_anualizado(media*T)/|maxDD|`; ante serie plana `calmar` SHALL ser `null`, nunca infinito; un Calmar negativo es legal y SHALL reportarse numérico. Ante serie con menos de 2 observaciones o cualquier valor no finito, todas las métricas SHALL ser `null` con motivo (nunca 0 ni inf). La serie SHALL construirse como matriz de log-retornos por activo en orden de claves por el vector de pesos en el mismo orden; un peso SIN precios alineados SHALL fallar con error nombrado (las series con precio sin peso se embeben en cero, ruta legacy M<N). Toda sección SHALL llevar etiquetas de proveniencia in-sample/diario/sin-costes. La curva de drawdown NO se serializa (solo escalares).

#### Scenario: serie analítica exacta

- **WHEN** precios de 2 activos con 3 observaciones y pesos conocidos entran al constructor de serie
- **THEN** la serie equals `log(P[1:]/P[:-1]) @ w` en orden de claves dentro de tolerancia 1e-12

#### Scenario: peso sin precios falla nombrado

- **WHEN** los pesos contienen un ticker sin serie de precios alineados
- **THEN** el constructor falla con `ValueError` nombrado en lugar de alinear silenciosamente (las series con precio pero sin peso se embeben en cero: ruta legacy M<N, no es mismatch)

#### Scenario: serie constante con rf=0.045 usa ln(1.045)

- **WHEN** una serie constante entra a `tail_risk_metrics` con `risk_free_rate=0.045`
- **THEN** el numerador del Sortino usa `ln(1.045)` y el objetivo diario es `ln(1.045)/252` dentro de tolerancia 1e-12

#### Scenario: sin downside Sortino null pero VaR numérico

- **WHEN** todos los retornos superan el objetivo diario
- **THEN** `sortino_ratio` y `downside_deviation_annual` son `null` con motivo y `var_95_daily`/`cvar_95_daily` son numéricos con `cvar >= var` en forma firmada (la forma `cvar >= |var|` vale cuando el VaR es no negativo, i.e. cola real de pérdidas)

#### Scenario: degenerados a null con motivo

- **WHEN** la serie tiene menos de 2 observaciones o contiene no-finitos, o es plana para drawdown
- **THEN** las métricas afectadas son `null` con `reason` (serie plana: `max_drawdown == 0.0` y `calmar_ratio` null), nunca 0 ni inf ni token inválido

#### Scenario: drawdown pinneado y Calmar con signo legal

- **WHEN** una serie fija con caída y recuperación entra a `drawdown_metrics`
- **THEN** `max_drawdown == min(P/running_max(P) − 1) ≤ 0` exacto y `calmar_ratio == mean*T/|maxDD|` (negativo si el retorno anualizado es negativo)

#### Scenario: sección sobrevive a JSON estricto

- **WHEN** las tres salidas se vuelcan con el sanitizador del reporte
- **THEN** el documento parsea con parser estricto (sin NaN/Infinity) y los `null` no se confunden con ceros
