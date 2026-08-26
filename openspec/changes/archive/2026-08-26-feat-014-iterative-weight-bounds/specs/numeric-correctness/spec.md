# numeric-correctness Specification (delta)

## ADDED Requirements

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
