# Proposal: feat-010-inverse-vol-epsilon-guard

## Why

`calculate_inverse_volatility_weights` (allocation.py:48-50) divide `1.0/vol` sin piso: una volatilidad cero (activo plano que sobrevivió por alguna ruta) produce `inf` y renormaliza a un peso degenerado. Mismo patrón de defecto que feat-009 corrigió — este feature reutiliza el ε-floor introducido (`VOL_FLOOR_EPS`) en la rama inverse-volatility.

## What Changes

- `allocation.py`: `calculate_inverse_volatility_weights` aplica `np.maximum(vols, VOL_FLOOR_EPS)` antes de invertir
- `tests/test_numeric_guards.py`: caso vol con cero → pesos finitos suman 1
- Fuera de scope: cambios a otros métodos (ya cubiertos o futuros)

## Capabilities

### Modified Capabilities
- `numeric-correctness`: la regla de piso épsilon se extiende al método inverse-volatility de asignación.
