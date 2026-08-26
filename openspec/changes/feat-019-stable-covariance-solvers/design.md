# Design: feat-019-stable-covariance-solvers

## Context

feat-014 dejó constraints robustos; feat-009 el piso ε. Los dos métodos cuadráticos legacy siguen con inv explícita. Shrinkage transversal (cov_estimator plumbing) se separó deliberadamente en decision-log: aquí solo estabilización de solvers.

## Goals / Non-Goals

**Goals:** solve en vez de inv; reparación PD determinista; fallback nombrado; equivalencia analítica demostrada.
**Non-Goals:** LedoitWolf/OAS (diferida); HRP (ya sin inversión); QP general; reordenar métodos.

## Decisions

### D1 — solve directo, jitter progresivo solo si Cholesky falla
`np.linalg.solve(Σ, b)` usa LAPACK factorization — estabilidad óptima estándar. `_ensure_positive_definite`: intenta cholesky; ante fallo añade `jitter_k = eps_scale * trace/n * 10^k` (k=0..3) re-testeando; log de cada reparación. Determinista y acotado.
*Alternativa descartada:* pinv incondicional — silencia más de lo que reporta y no preserva estructura PD cuando existe.

### D2 — Min-variance denominador via identidad solve
`denom = onesᵀ·solve(Σ,ones)`: una factorización sirve numerator+denominator → menos operaciones flotantes que calcular Σ⁻¹ completo para luego contraer.

### D3 — Fallback equal-weights conservado
La red final permanece (contrato C3-style: warning nombrado). La reparación D1 la torna casi-inalcanzable pero su existencia es parte del contrato defensivo.

## Risks / Trade-offs

- Jitter cambia numéricamente resultados en casos casi-singulares — preferible a explosión infinita; visible en log
- No elimina la sensibilidad a μ estimadas del max_sharpe (limitación metodológica documentada, no resolvible aquí)
