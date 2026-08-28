## Context

Ver proposal.md (Why) y el delta de `out-of-sample-validation` (What). Estado relevante: `walk_forward.py:144-146` construye `log_test` con `np.roll` + `[1:]`; `_iter_walk_windows` garantiza `test_start = train_end + embargo_days` con `test_start >= train_rows >= 2`, por lo que la fila `test_start − 1` (último día del embargo, o último de train si embargo=0) siempre existe y es información estrictamente pasada respecto al test. La red feat-026 (anti-fuga y agregados) pina el contrato ex-ante; el test anti-fuga depende de las posiciones, no del conteo de retornos.

## Goals / Non-Goals

**Goals:**
- Cada fold produce exactamente `test_rows` retornos OOS, incluido el retorno del primer día.
- Cero información futura: el primer retorno usa solo el precio previo a la ventana.
- Cambio de producción confinado al bloque de cálculo de retornos de test.

**Non-Goals:**
- No tocar `_iter_walk_windows`, HRP de entrenamiento, constraints ni agregados del reporte.
- No cambiar firmas públicas de `walk_forward_evaluate` ni de `WalkForwardReport`.

## Decisions

**D1 — Ventana extendida `[test_start−1, test_end)` con diff logarítmico directo.** `np.log(extended[1:] / extended[:-1])` produce exactamente `test_rows` retornos; el primero es `log(P[test_start]/P[test_start−1])`. Alternativa descartada: indexar `matrix[test_idx − 1]` para el primer retorno y concatenar — más código, mismo resultado.

**D2 — Mantener la guarda de degeneración** (`len == 0 or std <= 0`): ahora `len == test_rows` siempre, la guarda queda como defensa para vol plana.

**D3 — Test analítico con columnas idénticas:** retornos idénticos entre activos hacen que el retorno del portfolio sea el del activo (pesos suman 1), independientemente del HRP; spike en el primer día del test (0.5) + segundo día 0.02 y resto 0 dan mediana OOS = 0.52/60·252 post-fix vs 0.02/59·252 pre-fix — rojo/verde por valor exacto, sin depender de pesos internos.

## Risks / Trade-offs

- [Precio previo al test pertenece al embargo] → Mitigación: es información pasada por construcción de `_iter_walk_windows`; el test anti-fuga de feat-026 (mutación OOS no altera pesos) sigue como gate.
- [Fold 0 con embargo=0] → `test_start − 1` es el último día de train; el retorno del primer día de test usa ese cierre — correcto y documentado en el docstring.
- [Cambio de valores agregados respecto a corridas históricas] → esperado y deseado (el bug subestimaba el retorno OOS); se registra en CHANGELOG Unreleased.

## Migration Plan

Sin migración: cambio interno de cómputo de retornos, sin API pública ni config. Rollback = revert del commit.
