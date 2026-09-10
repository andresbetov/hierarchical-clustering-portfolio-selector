# Spec delta: technical-report (feat-048)

## ADDED Requirements

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
