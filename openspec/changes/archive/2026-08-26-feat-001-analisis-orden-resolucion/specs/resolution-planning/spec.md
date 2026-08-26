# resolution-planning Specification (delta)

## Purpose

Define el contrato de la capacidad que gobierna cómo se deriva, valida y registra el orden de resolución de hallazgos de auditoría técnica, garantizando que cada decisión de secuenciación sea trazable, acíclica y ejecutable como features con dependencias explícitas.

## ADDED Requirements

### Requirement: Inventario completo de hallazgos

El artefacto de orden de resolución SHALL cubrir exactamente una vez cada hallazgo del inventario de auditoría (28 ítems: C1-C4, A1-A7, M1-M10, B1-B7), sin omisiones ni duplicados.

#### Scenario: Cobertura total verificable
- **WHEN** se contrasta la secuencia final contra el inventario de `docs/auditoria-tecnica.md` §3
- **THEN** los 28 ids aparecen exactamente una vez y el conteo coincide sin faltantes ni repetidos

### Requirement: Aristas solo por dependencia técnica real

Cada arista del grafo SHALL representar una dependencia técnica verificable — un cambio modifica el comportamiento o los datos que otro consumo consume — citada con evidencia `file:line`, y SHALL NO existir por cercanía temática.

#### Scenario: Arista descartada
- **WHEN** una arista candidata carece de evidencia de dependencia técnica real
- **THEN** se descarta y se documenta en el registro de aristas evaluadas junto al motivo del rechazo

#### Scenario: Arista aceptada
- **WHEN** una arista declara que el consumidor lee datos/comportamiento modificado por el predecesor
- **THEN** la tabla de dependencias cita la evidencia `file:line` correspondiente a ambos extremos

### Requirement: Grafo dirigido acíclico

El grafo de dependencias SHALL ser un DAG. La detección de ciclos SHALL documentarse explícitamente y todo par con dependencia bidireccional SHALL descomponerse en sub-tareas rompibles o fusionarse en un solo feature.

#### Scenario: Verificación anti-ciclos
- **WHEN** se completa el ordenamiento topológico
- **THEN** existe una ordenación lineal válida y el documento declara el método de verificación usado

### Requirement: Desempate por trascendencia

Cuando dos hallazgos no tienen dependencia mutua, su orden relativo SHALL resolverse con el criterio de trascendencia: validez de resultados > reproducibilidad > mantenibilidad > higiene. Todo desempate aplicado SHALL quedar registrado con el caso concreto y el nivel del criterio invocado.

#### Scenario: Par sin dependencia mutua
- **WHEN** A y B son intercambiables topológicamente
- **THEN** el documento justifica el orden elegido citando qué dimensión del criterio decide y por qué

### Requirement: Secuencia executable como features

La secuencia final SHALL registrarse en `feature_list.json` como features `feat-002`..`feat-0NN` con campo `dependencies` apuntando únicamente a ids previos ya declarados, respetando la regla de un feature activo a la vez.

#### Scenario: Registro trazable
- **WHEN** se consulta cualquier feature derivado en `feature_list.json`
- **THEN** sus `dependencies` refieren a features que le preceden en la secuencia aprobada y ningún feature depende de uno posterior

### Requirement: Agrupación verificable en aislado

Cada agrupación de hallazgos contiguos en un feature SHALL poder pasar la verificación del proyecto (`./init.sh`) de forma aislada tras completarse únicamente sus dependencias declaradas.

#### Scenario: Feature con dependencias satisfechas
- **WHEN** un feature derivado se ejecuta después de que todos sus `dependencies` estén en estado `done`
- **THEN** la verificación del proyecto pasa sin requerir trabajo de features no precedentes en la secuencia
