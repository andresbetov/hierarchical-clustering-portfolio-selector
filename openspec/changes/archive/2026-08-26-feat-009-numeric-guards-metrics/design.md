# Design: feat-009-numeric-guards-metrics

## Context

Depende feat-008 (matrices alineadas — los guards se prueban sobre series coherentes). Los kernels corr/cov/vol están @jit nopython: las soluciones deben ser numba-compatibles. Sharpe/filtros/risk-parity son python puro.

## Goals / Non-Goals

**Goals:** semántica NaN para indefinidos; exclusión nombrada; ddof consistente; risk-parity robusta con aviso de no-convergencia.
**Non-Goals:** shrinkage/cov estimators (feat-019); reemplazo del clustering greedy (feat-018); inverse-vol guard (feat-010, siguiente PR, reutiliza constante); HRP entero.

## Decisions

### D1 — NaN sobre 0/inf para indefinidos
Sharpe de activo plano es matemáticamente indefinido. NaN propaga honestamente y el filtro (que ahora también chequea isfinite) lo excluye **nombrándolo** — visible en log. Alternativa 0.0 ocultaría el problema dentro del scoring.
*Descartado:* clip a ±1e6 — inventa ranking falso entre planos.

### D2 — ddof=1 manual dentro del kernel numba
numba no soporta `np.std(..., ddof=)`. Cálculo manual: mean → sum((x-mean)^2)/(n-1) → sqrt * sqrt(252). La cov interna ya era /(N-1): cadena queda muestral consistente. Test exacto contra np.std(ddof=1).

### D3 — Diagonal condicionada
`corr[i,i] = 1.0 if std_i>0 else nan`. Consecuencia distancia `1-|nan|=nan`: el futuro aligner/línea de filtrado previo ya removió planos — la rama NaN es red de seguridad determinista, no flujo normal.

### D4 — Estabilización risk-parity por caps, no regularización
Piso ε en rc + cap [0.1,10] en scaling factors impide explosión sin introducir ridge/shrinkage (territorio feat-019). Warning al agotar max_iterations hace visible el fracaso silencioso actual.

## Risks / Trade-offs

- Universos reales podrían perder activos nuevos al excluir non-finitos — exactamente lo deseado (antes entraban corruptos)
- Cambio ddof mueve vol ~0.8% relativo en muestras grandes — tests update explícito
