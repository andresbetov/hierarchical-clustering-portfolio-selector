## Why

`walk_forward.py` computa los retornos OOS con el artificio `np.log(matrix[test_idx] / np.roll(matrix[test_idx], 1, axis=0))[1:]`: `np.roll` fabrica para la primera fila `log(P[0]/P[último])` — un valor contra un precio FUTURO dentro de la propia ventana de test — y luego lo descarta con `[1:]`. Resultado: cada fold pierde el retorno del primer día del test (n retornos = test_rows−1) y el comentario que justifica el truco es engañoso. Es el bug P0-2 del plan v0.1.0 y la segunda feature del DAG feat-028..041 (feat-029).

## What Changes

- `portfolio_engine/validation/walk_forward.py` computará los retornos de la ventana de test sobre el tramo extendido `[test_start−1, test_end)`: el retorno del primer día del test usa el último precio previo a la ventana (día del embargo, información pasada conocida) — leak-free y con exactamente `test_rows` retornos por fold.
- Se elimina `np.roll` y el comentario engañoso.
- Test de regresión analítico: bundle con retornos idénticos por activo y un spike exactamente en el primer día del test verifica que la mediana OOS incluya ese retorno (el valor pre-fix lo excluye).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `out-of-sample-validation`: el requirement "Evaluación OOS con pesos ex-ante" se extiende para exigir que la serie OOS cubra TODOS los días de la ventana de test (`test_rows` retornos), con el retorno del primer día calculado contra el último precio previo a la ventana.

## Impact

- Código: `portfolio_engine/validation/walk_forward.py` (único cambio de producción esperado).
- Tests: `tests/test_walk_forward.py` (nuevo caso analítico).
- Sin cambios de API pública, sin dependencias nuevas, sin cambios de configuración.
