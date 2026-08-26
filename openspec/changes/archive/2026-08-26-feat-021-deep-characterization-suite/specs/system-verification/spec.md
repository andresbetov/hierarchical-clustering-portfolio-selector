# system-verification Specification (delta)

## Purpose

Garantizar que el sistema sostiene propiedades algebraicas transversales bajo entradas arbitrarias válidas (generadas, no ejemplos fijos), y que la composición completa del pipeline es verificable de extremo a extremo sin red.

## ADDED Requirements

### Requirement: Simplex-invarianza de todos los asignadores

Para cualquier matriz de covarianza simétrica positiva-definida generada aleatoriamente (n entre 2 y 30), los pesos resultantes de HRP, min-variance y risk-parity con bounds factibles SHALL pertenecer al simplex (positivos o cero donde aplique por método, suma 1), con verificación final dura respetada.

#### Scenario: covarianzas PD arbitrarias
- **WHEN** hypothesis genera covarianzas PD variadas y corre cada asignador
- **THEN** ningún run produce NaN, infinito, negatividad fuera de contrato o desvío de suma

### Requirement: Composición end-to-end offline verificable

La secuencia completa fetch→filter→align→cluster→allocate→summary SHALL ejecutarse sin red mediante inyección del proveedor batch, y SHALL producir resultados consistentes con los contratos unitarios de cada etapa (universo no-vacío si hay solapamiento suficiente, matrices cuadradas simétricas, pesos en simplex post-constraints).

#### Scenario: panel sintético multi-ticker
- **WHEN** el batch se parchea con un panel de 6 tickers con huecos de calendario distintos, colas NaN y un ticker plano
- **THEN** main() completa retornando universo filtrado coherente, matrices válidas y pesos dentro de bounds; no existe ruta silenciosa

### Requirement: Determinismo semilla-estable

La suite completa SHALL ser determinista: hypothesis configurado con derandomize para reproducibilidad CI idéntica corrida-a-corrida.

#### Scenario: doble corrida idéntica
- **WHEN** la suite de propiedades corre dos veces en el mismo commit
- **THEN** genera exactamente el mismo conjunto de ejemplos y resultados
