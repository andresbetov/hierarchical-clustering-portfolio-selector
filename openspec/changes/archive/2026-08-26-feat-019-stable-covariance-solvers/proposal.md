# Proposal: feat-019-stable-covariance-solvers

## Why

`calculate_maximum_sharpe_weights` y `calculate_minimum_variance_weights` construyen `np.linalg.inv(cov)` explícitamente (allocation.py:89,102) — el patrón que la auditoría marca como fuente clásica de inestabilidad (B5): errores de estimación se amplifican al invertir, y covarianzas casi-singulares (activos gemelos) producen pesos explosivos antes del fallback. Los sistemas lineales equivalentes se resuelven de forma estable sin formar nunca la inversa.

## What Changes

- `portfolio/allocation.py`: reescritura de ambos métodos sobre `np.linalg.solve`; denominador min-variance vía `1ᵀ·solve(Σ,1)`; `LinAlgError → equal-weights` conservado con warning nombrado
- helper `_ensure_positive_definite(cov)`: test de Cholesky + jitter diagonal progresivo documentado (repara singularidad leve en vez de rendirse)
- Tests (`tests/test_allocation_bounds.py` ampliado o nuevo archivo): equivalencia analítica con inverse-exacto en PD bien condicionada, estabilidad bajo colinealidad severa, finitud siempre
- Fuera de scope: shrinkage Ledoit-Wolf transversal (diferida explícitamente — decision-log); HRP ya no usa inversión por diseño

## Capabilities

### Modified Capabilities
- `numeric-correctness`: los solvers cuadráticos SHALL resolver sistemas lineales (nunca construir inversas explícitas), con reparación numérica determinista ante covarianza no-PD y fallback nombrado a equal-weights.
