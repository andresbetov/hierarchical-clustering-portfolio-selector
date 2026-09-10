# Spec delta: system-verification (feat-053, MODIFIED)

## MODIFIED Requirements

### Requirement: Simplex-invarianza de todos los asignadores

Para cualquier matriz de covarianza simétrica positiva-definida generada aleatoriamente (n entre 2 y 25), los pesos resultantes de HRP, min-variance y risk-parity con bounds factibles SHALL pertenecer al simplex (positivos o cero donde aplique por método, suma 1), con verificación final dura respetada.

#### Scenario: covarianzas PD arbitrarias

- **WHEN** hypothesis genera covarianzas PD variadas y corre cada asignador
- **THEN** ningún run produce NaN, infinito, negatividad fuera de contrato o desvío de suma
