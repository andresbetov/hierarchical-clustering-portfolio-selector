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

La volatilidad anualizada y la covarianza/correlación SHALL usar el mismo estimador muestral (ddof=1); no SHALL NO coexistir ddof distinto en la misma cadena estadística.

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
