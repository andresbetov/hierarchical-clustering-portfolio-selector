# Proposal: feat-014-iterative-weight-bounds

## Why

`apply_weight_constraints` (allocation.py:114-121) hace `clip → renormalizar` UNA sola pasada: tras renormalizar, los pesos pueden volver a violar los límites (ejemplo de auditoría: [0.60, 0.10×4] con max=0.30 produce 0.43 > max). El resultado final viola el mandato declarado en README (límites 0.05–0.30) — es un CRÍTICO: la cartera entregada puede concentrarse más allá del tope.

## What Changes

- `allocation.py`: reescritura de `apply_weight_constraints` como algoritmo iterativo tipo water-filling:
  - precondición de viabilidad (`n·min ≤ 1 ≤ n·max`, sino `ValueError`)
  - conjuntos explícitos `fixed_low/fixed_high`; redistribución proporcional solo entre libres
  - fallback uniforme si la suma libre ≈0; máx 50 iteraciones + warning si no converge
  - verificación final dura (bounds ±1e-9, suma=±1e-9)
- `tests/test_allocation_bounds.py` (nuevo): ejemplo exacto de auditoría, identidad cuando ya cumple, casos de saturación (todos al max/min), inviabilidad, estrés con 100 semillas (~8 tests)
- Fuera de scope: vol-target scaling (feat-015 lo inserta alrededor de este punto único), optimizador QP completo (decision-log)

## Capabilities

### Modified Capabilities
- `numeric-correctness`: añade requisito — los constraints de pesos SHALL satisfacerse simultáneamente en el resultado final, mediante fijación iterativa con redistribución, y SHALL fallar ruidosamente si los bounds son inviables para el número de activos.
