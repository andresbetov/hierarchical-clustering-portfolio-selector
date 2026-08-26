# numeric-correctness Specification (delta)

## ADDED Requirements

### Requirement: Semántica de signo en la distancia de clustering

En modo signed la distancia SHALL ser creciente con -corr (correlación negativa produce distancia máxima, nunca fusión); en modo abs se conserva el comportamiento histórico 1-|corr|. La conversión del umbral de equivalencia SHALL preservar la semántica del usuario "fusionar si corr supera el umbral" independientemente del modo.

#### Scenario: negativos jamás fusionados (signed)
- **WHEN** dos activos tienen corr=-0.9 y el modo es signed
- **THEN** su distancia excede el umbral equivalente a corr=0.65 y no se fusionan

#### Scenario: gemelos positivos sí fusionados
- **WHEN** dos activos tienen corr=+0.9 y threshold=0.65
- **THEN** su distancia queda bajo el umbral convertido y se fusionan
