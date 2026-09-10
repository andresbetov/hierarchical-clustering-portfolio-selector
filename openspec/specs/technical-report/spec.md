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

### Requirement: Salud del árbol jerárquico con profundidad y acreción

El reporte técnico SHALL poder incluir la salud del árbol de clustering usado por la asignación: `max_depth` (camino raíz→hoja más largo contando fusiones sobre la matriz de linkage `Z`, NUNCA la altura del eje Y), `chaining_rate` (fracción de fusiones con exactamente un hijo hoja sobre `n−1`: acreción-singleton; un par inicial hoja-hoja no cuenta como acreción), `chaining_flag` (verdadero si `max_depth > ceil(log2(n))+2` o `chaining_rate > 0.60`; umbrales heurísticos del catálogo §8) y `leaf_order` (el orden de hojas del motor, comparable a máquina con el dendrograma). Con menos de 2 activos las métricas SHALL ser `null` con motivo sin elevar; con exactamente 2 activos SHALL reportarse profundidad 1, tasa 0.0 (la única fusión es hoja-hoja: sin acreción posible) y bandera falsa explícita (no patológico). Un método de linkage inválido o una covarianza inválida SHALL fallar con error (propagación del motor, fail loud). La aproximación de Ward sobre distancia precomputada (no euclidiana) SHALL documentarse; su criterio de aceptación es finitud, no corrección geométrica.

#### Scenario: cadena pura encadenada

- **WHEN** una covarianza de 4 activos con escalas anidadas entra con linkage `single`
- **THEN** `max_depth == 3 == n−1`, `chaining_rate == 2/3 == (n−2)/(n−1)` y `chaining_flag` es verdadero

#### Scenario: árbol balanceado sano

- **WHEN** una estructura de 8 activos perfectamente balanceada entra al diagnóstico
- **THEN** `max_depth == 3 == ceil(log2(8))`, `chaining_rate == 0.0` y `chaining_flag` es falso, con `leaf_order` igual al orden del motor

#### Scenario: patrón de 3 bloques sin bandera

- **WHEN** la covarianza sintética de 12 activos en 3 bloques (patrón del dendrograma) entra con `single`
- **THEN** `max_depth <= ceil(log2(12))+2`, `chaining_flag` es falso y `leaf_order` coincide con `_leaf_order(Z, 12)`

#### Scenario: degenerados a null sin elevar

- **WHEN** la covarianza tiene menos de 2 activos
- **THEN** las métricas son `null` con `reason`, sin excepción al caller

#### Scenario: dos activos por construcción

- **WHEN** la covarianza es 2×2 válida
- **THEN** profundidad 1, tasa 0.0 (la única fusión es hoja-hoja: sin acreción posible) y bandera falsa (construcción, no patología)

#### Scenario: método inválido falla nombrado

- **WHEN** el método no pertenece al enum del motor
- **THEN** el diagnóstico propaga el `ValueError` del seam antes de SciPy

#### Scenario: ward finito con aproximación documentada

- **WHEN** el patrón de 3 bloques entra con linkage `ward`
- **THEN** todas las salidas son finitas y el docstring documenta la aproximación ward-sobre-precomputada

#### Scenario: sección sobrevive a JSON estricto

- **WHEN** la salida se vuelca con el sanitizador del reporte
- **THEN** el documento parsea con parser estricto y `leaf_order` es lista de enteros

### Requirement: Sección walk-forward con detalle por fold y deriva

El reporte técnico SHALL poder incluir la validación walk-forward consumiendo `WalkForwardReport.to_dict()` verbatim para los agregados (las medianas de la sección SHALL ser idénticas a las del reporte; `to_dict` NO se modifica). El detalle por fold SHALL exponer índice, posiciones de train/test (como listas), tickers, pesos, retorno/volatilidad/Sharpe OOS, `mandate_relaxed` y benchmarks, preservando los folds inválidos tal cual (sin sintetizar). La deriva entre folds válidos consecutivos (ordenados por índice) SHALL ser `l1 = Σ|w_k − w_{k−1}|` sobre vectores embebidos en cero sobre la unión de tickers del par, en [0,2] para carteras long-only totalmente invertidas; SHALL reportar `median_l1`, `p90_l1` (cuantil lineal), `pairs_computed/pairs_possible` y la etiqueta `drift-not-turnover`. Un fold inválido SHALL romper la cadena sin interpolación. Con menos de 2 folds válidos la deriva SHALL ser `null` con motivo. La deriva JAMÁS SHALL anualizarse ni multiplicarse por bps.

#### Scenario: agregados idénticos al reporte

- **WHEN** un `WalkForwardReport` entra a la sección
- **THEN** `section["aggregates"] == report.to_dict()` exacto, llave por llave

#### Scenario: deriva cero con pesos idénticos

- **WHEN** dos folds válidos consecutivos tienen los mismos pesos
- **THEN** su `l1 == 0.0` y la mediana sobre un solo par equals ese valor

#### Scenario: mover 10 puntos da L1 0.20

- **WHEN** dos folds válidos difieren en 10 puntos de peso (0.10 de A a B)
- **THEN** su `l1 == 0.20` exacto (dos vías: sale 0.10, entra 0.10)

#### Scenario: fold inválido rompe la cadena

- **WHEN** un fold inválido se intercala entre dos válidos
- **THEN** `pairs_computed < pairs_possible`, el par roto se informa y ningún valor se interpola

#### Scenario: un solo fold sin deriva

- **WHEN** el reporte tiene un único fold (válido o no)
- **THEN** la deriva es `null` con `reason` y `pairs_possible == 0`

#### Scenario: posiciones serializables

- **WHEN** los folds llevan posiciones como tuplas `(inicio, fin-exclusivo)`
- **THEN** la sección las expone como listas `[inicio, fin]` y el documento vuelca a JSON estricto

#### Scenario: benchmarks preservados sin sintetizar

- **WHEN** un fold trae benchmarks equal/ivp y otro es inválido con `{}` 
- **THEN** la sección los reproduce tal cual (dict completo vs `{}`), sin fabricar valores

### Requirement: Ensamblador del reporte con emisión fail-safe

El sistema SHALL componer el reporte técnico mediante `build_technical_report` puro a partir de las secciones verificadas (envelope, exclusiones, asignación, riesgo in-sample, árbol) más `walk_forward: None` como placeholder presente-con-null (feat-051 lo llena con la sección real). `generate_complete_analysis_report` SHALL aceptar `report_path` keyword-only default `None` (sin escribir nada por defecto) y `run_walk_forward` reservado default `False`; con `report_path` fijado SHALL construir y volcar el JSON tras el log final, y cualquier fallo del reporte SHALL degradarse a un warning nombrado sin romper el run (la tupla de retorno intacta). La consola SHALL permanecer intacta salvo una línea `logger.info` de escritura. `cli.main` SHALL pasar `report_path="reports/technical-report.json"` (el JSON siempre se emite; `--no-save` gobierna solo los plots).

#### Scenario: E2E offline emite JSON estricto completo

- **WHEN** el pipeline corre offline con `report_path` fijado
- **THEN** existe un solo JSON que parsea estricto, con envelope (`schema_version == 1`, fingerprint equals recompute independiente) y las 6 secciones con sus keys, `walk_forward` null

#### Scenario: default no escribe nada

- **WHEN** el pipeline corre sin `report_path`
- **THEN** no se crea ningún archivo ni directorio `reports/` y el retorno es la 4-tupla intacta

#### Scenario: fallo del reporte no rompe el run

- **WHEN** la escritura del reporte eleva (inyectado en test)
- **THEN** se loggea warning nombrado, el run completa y retorna la 4-tupla

#### Scenario: --no-save emite JSON igual

- **WHEN** el pipeline corre con `save_plots=False` y `report_path` fijado
- **THEN** el JSON se emite (el flag gobierna solo plots) y ningún PNG se escribe
