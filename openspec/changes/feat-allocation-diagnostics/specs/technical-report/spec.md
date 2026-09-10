## ADDED Requirements

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
