## MODIFIED Requirements

### Requirement: Determinismo semilla-estable

La suite completa SHALL ser determinista: hypothesis configurado con derandomize para reproducibilidad CI idéntica corrida-a-corrida. Los fixtures sintéticos SHALL derivar sus semillas de funciones estables entre procesos — independientes del salting de `PYTHONHASHSEED` — de modo que el mismo commit produzca los MISMOS paneles en cualquier intérprete; `hash()` de strings SHALL NOT usarse como fuente de seed.

#### Scenario: doble corrida idéntica
- **WHEN** la suite de propiedades corre dos veces en el mismo commit
- **THEN** genera exactamente el mismo conjunto de ejemplos y resultados

#### Scenario: paneles idénticos bajo distintas PYTHONHASHSEED
- **WHEN** el constructor de paneles sintéticos corre en dos procesos con `PYTHONHASHSEED` distintos
- **THEN** ambos procesos producen paneles byte-idénticos
