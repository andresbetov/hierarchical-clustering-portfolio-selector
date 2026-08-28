# numeric-correctness Specification

## Purpose
Garantizar que las magnitudes numéricas del motor tengan semántica definida ante casos degenerados: indefinidos se representan como NaN y quedan excluidos de forma visible, los estimadores muestrales son consistentes entre sí, y las iteraciones numéricas no divergen silenciosamente.

## Requirements

### Requirement: Sharpe indefinido para varianza nula

`calculate_sharpe_ratio` SHALL retornar NaN cuando la volatilidad anualizada sea menor o igual al piso épsilon, y SHALL NOT producir infinitos.

#### Scenario: activo con precio plano
- **WHEN** un activo tiene volatilidad anualizada 0
- **THEN** su Sharpe es NaN y nunca inf

### Requirement: Exclusión visible de métricas no finitas

El filtro de activos SHALL excluir cualquier ticker cuyas métricas usadas por decisión (Sharpe, volatilidad) no sean finitas, registrando en el log el ticker y el motivo de exclusión.

#### Scenario: filtro nombrando excluidos
- **WHEN** el universo contiene un activo con Sharpe NaN
- **THEN** el warning incluye ese ticker y las matrices posteriores no lo contienen

### Requirement: Consistencia muestral ddof

La volatilidad anualizada y la covarianza/correlación SHALL usar el mismo estimador muestral (ddof=1); SHALL NOT coexistir ddof distinto en la misma cadena estadística.

#### Scenario: verificación exacta
- **WHEN** se calcula la volatilidad anualizada sobre una serie conocida
- **THEN** coincide exactamente con std(ddof=1)*sqrt(252)

### Requirement: Correlación honesta ante varianza cero

En la matriz de correlación, la diagonal SHALL ser 1.0 solo cuando la varianza propia sea positiva; activos planos producen NaN en toda su fila/columna.

#### Scenario: matriz con un activo plano
- **WHEN** un activo tiene retornos idénticos constantes
- **THEN** su fila, columna y diagonal contienen NaN, y los demás pares permanecen finitos

### Requirement: Risk-parity protegida contra degeneración

Las contribuciones de riesgo en cada iteración SHALL tener piso épsilon y los factores de escalado SHALL estar acotados; si se agotan las iteraciones sin alcanzar tolerancia, SHALL emitirse warning antes de devolver pesos normalizados finitos.

#### Scenario: covarianza singular por duplicados
- **WHEN** dos activos tienen columnas idénticas en la covarianza
- **THEN** los pesos resultantes son finitos, suman 1 y el proceso termina sin excepción

### Requirement: Piso épsilon en asignación inverse-volatility

`calculate_inverse_volatility_weights` SHALL aplicar el piso épsilon compartido (`VOL_FLOOR_EPS`) a las volatilidades antes de invertirlas, de modo que ninguna volatilidad degenerada produzca pesos infinitos.

#### Scenario: volatilidad cero entre activos
- **WHEN** una volatilidad de entrada es 0 y otra positiva
- **THEN** los pesos resultantes son finitos, estrictamente positivos y suman 1

### Requirement: Bounds de peso satisfechos simultáneamente en el resultado final

`apply_weight_constraints` SHALL retornar pesos donde TODOS los activos cumplan min≤w≤max y la suma sea 1, aplicando fijación iterativa de violadores a su límite con redistribución proporcional entre los no fijados.

#### Scenario: ejemplo canónico del audit
- **WHEN** los pesos previos son [0.60, 0.10, 0.10, 0.10, 0.10] con min=0.05/max=0.30
- **THEN** el resultado final respeta max en todos los componentes (ninguno >0.30) y suma 1

#### Scenario: entrada ya válida
- **WHEN** todos los pesos están dentro de bounds
- **THEN** el vector retorna sin cambios numéricos relevantes

### Requirement: Inviabilidad declarada ruidosamente

Si el número de activos hace imposible satisfacer ambos bounds (n·min>1 o n·max<1), la función SHALL lanzar `ValueError` describiendo la condición, SHALL NO devolver un vector violador "mejor esfuerzo".

#### Scenario: dos activos con max=0.30
- **WHEN** n=2 y max=0.30 ⇒ n·max=0.6<1
- **THEN** ValueError explica que ningún vector sumando 1 puede respetar el tope

### Requirement: Terminación garantizada y verificada

El algoritmo SHALL terminar en un número acotado de iteraciones; si el presupuesto se agota sin converger SHALL advertir y SHALL verificar/lanzar sobre las condiciones finales en lugar de retornar silenciosamente una violación.

#### Scenario: presupuesto agotado
- **WHEN** el bucle alcanza su máximo de iteraciones con violación residual mayor a la tolerancia
- **THEN** existe un warning en el log y se lanza error con el detalle de la violación final

### Requirement: Semántica de signo en la distancia de clustering

En modo signed la distancia SHALL ser creciente con -corr (correlación negativa produce distancia máxima, nunca fusión); en modo abs se conserva el comportamiento histórico 1-|corr|. La conversión del umbral de equivalencia SHALL preservar la semántica del usuario "fusionar si corr supera el umbral" independientemente del modo.

#### Scenario: negativos jamás fusionados (signed)
- **WHEN** dos activos tienen corr=-0.9 y el modo es signed
- **THEN** su distancia excede el umbral equivalente a corr=0.65 y no se fusionan

#### Scenario: gemelos positivos sí fusionados
- **WHEN** dos activos tienen corr=+0.9 y threshold=0.65
- **THEN** su distancia queda bajo el umbral convertido y se fusionan

### Requirement: Bisección determinista sin inversión de matrices

El asignador HRP SHALL construir pesos usando únicamente diagonales de slices covarianza (sin np.linalg.inv), SHALL ser determinista para entradas idénticas, y sus pesos finales SHALL ser estrictamente positivos y sumar exactamente 1 antes de aplicar constraints.

#### Scenario: dos activos varianzas conocidas
- **WHEN** cov = diag(0.01, 0.04) para [A, B]
- **THEN** los pesos sin constraints son exactamente [0.8, 0.2] (inverse-variance a través de las bisecciones)

#### Scenario: invarianza permutación
- **WHEN** se reordenan columnas/filas de la misma covarianza
- **THEN** el multiset de pesos es idéntico entre ambas corridas

### Requirement: Solvers cuadráticos sin inversión explícita

Los métodos max_sharpe y min_variance SHALL resolver sistemas lineales vía `np.linalg.solve` sobre la covarianza; SHALL NOT computar `np.linalg.inv` de la matriz completa.

#### Scenario: equivalencia analítica en PD bien condicionada
- **WHEN** se corre min_variance con cov diagonal conocida
- **THEN** los pesos coinciden con la fórmula cerrada inverse-variance normalizada

### Requirement: Reparación determinista ante no-PD

Ante covarianza no positiva-definida, SHALL intentarse reparación determinista por jitter diagonal progresivo (documentado en el log) antes del fallback equal-weights por `LinAlgError`, que SHALL permanecer como última red con warning nombrado.

#### Scenario: covarianza semidefinida con columna duplicada
- **WHEN** dos activos tienen retornos idénticos y se pide min_variance
- **THEN** los pesos resultantes son finitos, suman 1 y existe log de la reparación o del fallback

### Requirement: Sharpe reportado con covarianza real

El Sharpe de cartera mostrado en el resumen SHALL calcularse como (w·μ − rf)/sqrt(wᵀΣw) usando la matriz de covarianza alineada; la fórmula legacy sqrt(Σ(wᵢσᵢ)²) SHALL desaparecer del código de reporte. La matriz de covarianza entregada al resumen SHALL estar rebanada al subconjunto exacto del portfolio seleccionado — mismas dimensiones y mismo orden de tickers que el vector de pesos — en todas las rutas de asignación, incluida la ruta legacy con pruning por cluster (M < N). El pipeline SHALL preparar ese rebanado antes de invocar al módulo de reporte; el reporte SHALL NOT recibir matrices de dimensión distinta a los pesos.

#### Scenario: correlación cero equivale a legacy
- **WHEN** la covarianza es diagonal (ρ=0)
- **THEN** el Sharpe nuevo coincide con el cálculo por suma cuadrática de riesgos

#### Scenario: correlación positiva reduce el Sharpe
- **WHEN** dos activos con ρ=0.9 y pesos iguales comparan contra su versión ρ=0
- **THEN** la volatilidad de cartera con ρ=0.9 es mayor y el Sharpe resultante menor

#### Scenario: ruta legacy con pruning M<N
- **WHEN** un método de asignación distinto de hrp selecciona M activos de un universo filtrado de N (M < N) y se genera el reporte completo
- **THEN** el reporte se genera sin excepción y el Sharpe del resumen coincide con el cálculo manual wᵀΣw sobre la covarianza rebanada a los M activos seleccionados

### Requirement: Paridad semántica tras de-jit

La reescritura vectorizada de los kernels SHALL preservar bit-a-bit el contrato vigente: Sharpe NaN bajo piso épsilon, volatilidad muestral ddof=1, diagonal condicionada a varianza>0, propagación NaN en distancias y firmas públicas intactas — verificado por la suite de caracterización existente sin modificaciones a asserts salvo drift real.

#### Scenario: red de regresión verde
- **WHEN** los kernels reescritos corren bajo la suite completa (unitarios + propiedades + E2E)
- **THEN** no se modifica ningún assert y toda la verificación pasa

### Requirement: Seam de estimación de covarianza con paridad sklearn

`estimate_covariance(returns_matrix, method)` SHALL ser la única vía de cómputo de covarianza para el pipeline y el walk-forward. Con `method="sample"` SHALL retornar exactamente la matriz de `calculate_covariance_matrix` (bit a bit); con `method="ledoit_wolf"`/`"oas"` SHALL retornar la matriz shrinkage del estimador homónimo de scikit-learn con paridad numérica 1e-12, y su condition number SHALL ser menor o igual al de la covarianza muestral sobre los mismos datos. Entradas degeneradas (menos de 2 observaciones) SHALL producir la matriz NaN completa sin invocar a sklearn.

#### Scenario: sample bit a bit
- **WHEN** se estima con method="sample" sobre una matriz de retornos cualquiera
- **THEN** el resultado es idéntico al de calculate_covariance_matrix

#### Scenario: paridad shrinkage con sklearn
- **WHEN** se estima con method="ledoit_wolf" (o "oas") sobre retornos sintéticos
- **THEN** la matriz coincide con sklearn.covariance.LedoitWolf (u OAS) a tolerancia 1e-12

#### Scenario: degeneración sin sklearn
- **WHEN** la matriz de retornos tiene 1 fila o menos
- **THEN** se devuelve la matriz NaN completa (misma semántica que sample) sin error

### Requirement: Linkage HRP parametrizable con default retrocompatible

`calculate_hrp_weights(covariance_matrix, linkage_method)` SHALL aceptar {single, ward, average} y propagarlos a `scipy.cluster.hierarchy.linkage`; con `linkage_method="single"` (default) los pesos SHALL ser idénticos bit a bit a los del comportamiento vigente. Un método desconocido SHALL lanzar `ValueError`. Para cualquier método válido, los pesos finales SHALL ser estrictamente positivos, finitos y sumar exactamente 1 antes de constraints.

#### Scenario: default single bit a bit
- **WHEN** se invoca calculate_hrp_weights sin linkage_method sobre una covarianza conocida
- **THEN** los pesos coinciden exactamente con los del snapshot vigente (red feat-021)

#### Scenario: ward sobre bloques de correlación
- **WHEN** se invoca con linkage_method="ward" sobre un universo sintético de 3 bloques de correlación
- **THEN** los pesos son finitos, estrictamente positivos y suman 1, y activos del mismo bloque quedan adyacentes en el orden de hojas

#### Scenario: método desconocido
- **WHEN** se invoca con linkage_method="centroid"
- **THEN** ValueError antes de llamar a scipy
