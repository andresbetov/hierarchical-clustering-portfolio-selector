# Design: feat-014-iterative-weight-bounds

## Context

feat-009 deja pesos finitos; este feature garantiza bounds simultáneos. feat-015 insertará el vol-target alrededor de ESTE punto único de normalización.

## Goals / Non-Goals

**Goals:** bounds+suma exactos siempre; inviabilidad ruidosa; determinismo total (sin aleatoriedad).
**Non-Goals:** optimizador QP con costos; integration con turnover; vol-target (A1/feat-015).

## Decisions

### D1 — Water-filling por fijación explícita vs proyección matemática
Fijar violadores a su bound y redistribuir proporcionalmente entre libres es el algoritmo estándar (análogo a proyección en simplex acotado). Proyección euclídea completa (QP) es más "óptima" pero innecesaria para garantizar unMANDATO de bounds.
*Alternativa descartada:* scipy.optimize SLSQP — dependencia de tuning, lentitud, sin necesidad.

### D2 — Sets de fijación + capital contable
Libres = índices no fijados. Capital fijo = Σbounds de fijados; libre = 1-capital_fijo se reparte proporcional a pesos libres actuales (escalado), o uniforme si su suma ≈0. Esto preserva máximo posible la señal original del método de asignación.

### D3 — Tolerancias coherentes
eps interno 1e-12, verificación final ±1e-9, suma normalizada final a exactly-1 en double precision (división). Convergencia típica <5 iteraciones; budget 50 generoso.

### D4 — Viabilidad como precondición ruidosa
Config valida valores individuales pero n depende del runtime → check aquí. Mensaje sugiere solución (ajustar min/max o universo).

## Risks / Trade-offs

- Penaliza señal original cuando hay saturación masiva (muchos al max) — comportamiento esperado bajo mandato
- Cambio numérico en TODAS las salidas históricas del weight allocation cuando había violaciones — ese es el propósito
