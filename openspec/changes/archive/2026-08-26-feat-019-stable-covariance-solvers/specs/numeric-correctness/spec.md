# numeric-correctness Specification (delta)

## ADDED Requirements

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
