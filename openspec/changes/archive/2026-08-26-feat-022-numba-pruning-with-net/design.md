# Design: feat-022-numba-pruning-with-net

## Context

Escala real del proyecto: universos de decenas (hasta ~centenas) × ~1250 días de retornos. La red feat-021 pinnea semántica exacta.

## Goals / Non-Goals

**Goals:** eliminar numba y sus costes; vectorizar con paridad; conservar firmas.
**Non-Goals:** optimizar agresivamente para n>400 (condición de re-introducción); ParPyet/etc.; micro-benchmarks formales.

## Decisions

### D1 — Eliminación total sobre poda parcial
Dos implementaciones coexistentes duplican superficie de bugs. Vectorizado puro: `np.log(p[1:]/p[:-1])`, `np.std(ddof=1)`, `(X-X̄)ᵀ(X-X̄)/(n-1)` con `outer(std,std)` normalización. Cada una menos líneas que su versión jit loop.
*Alternativa descartada:* mantener jit solo en corr/cov — los tamaños no lo justifican y mantiene el peso.

### D2 — Reglas de clamps replicadas
Pisos EPS/`max()` repiten exactamente las mismas constantes/umbrales: `VOL_FLOOR_EPS`, floors mínimos para varianza cero, diagonal honesta condicional, clip [-1,1] ya existente en HRP path interno (no aquí).

### D3 — Verificación por suite completa + snapshot numerico local
Antes/después: correr test_metrics numeric-snapshot script inline (imprimir valores en fixtures estrella) para comparar drift; además la red completa. Sin cifras formales.

## Risks / Trade-offs

- Drift flotante mínimo posible por orden de suma distinto (lin vs matmul) — tolerancias tests 1e-9..1e-12 absorben
- `numba` removido puede romper usuarios externos hipotéticos — paquete pre-publicación
