## Context

Ver proposal.md (Why), ADR 005 (decisión) y los deltas (What). Estado: `core/metrics.py` ya tiene `calculate_covariance_matrix` (sample, ddof=1) y `_validate_observations_matrix` que devuelve la matriz NaN para n_rows ≤ 1; `pipeline.py:112` y `walk_forward.py:134` llaman a `calculate_covariance_matrix` directamente; sklearn 1.9.0 disponible desde feat-032. `_validate_observations_matrix` retorna `(matrix, 0, n_assets)` en degeneración — la seam debe reutilizarla para conservar la semántica.

## Goals / Non-Goals

**Goals:**
- Un solo punto de cómputo de covarianza consumido por pipeline y walk-forward.
- Default `sample` bit a bit con el comportamiento vigente (red feat-021 intacta).
- Shrinkage delegado a sklearn con paridad verificada.

**Non-Goals:**
- NO cambiar el default (v0.1.0; flip en v0.2.0 con evidencia WF — ADR 005).
- NO tocar `calculate_covariance_matrix` ni sus consumidores legacy (sigue siendo la base del modo sample).
- NO introducir estimadores adicionales (graphical lasso, EWMA) en este change.

## Decisions

**D1 — Seam en `core/metrics.py`** (capa compartida), no en `portfolio/`: pipeline y validation ya importan de core; evita dependencia de validation sobre portfolio. Alternativa descartada: módulo nuevo `portfolio/covariance.py` — split innecesario para una función.

**D2 — Import sklearn a nivel de módulo.** sklearn es dependencia runtime declarada; el import de módulo (~0.5s) es aceptable y honesto. Alternativa descartada: import perezoso dentro de la rama shrinkage — micro-optimización que oscurece el contrato de deps.

**D3 — Degeneración primero, sklearn después.** `estimate_covariance` valida con `_validate_observations_matrix`; si `n_rows == 0` retorna la matriz NaN directamente (sklearn no tolera NaN/degenerados y su comportamiento ahí no es contrato). Después del guard, la matriz es finita (contrato upstream: filtros excluyen no-finitos).

**D4 — Default `sample` con dispatch explícito.** `if method == "sample": return calculate_covariance_matrix(...)` garantiza identidad bit a bit por construcción; las ramas shrinkage llaman `LedoitWolf().fit(X).covariance_` / `OAS().fit(X).covariance_`. El enum cerrado en config hace inalcanzable un method desconocido en la seam (raise documentado, patrón feat-013).

**D5 — Tests:** paridad contra sklearn con fixture determinista (seed fija), condition number vía `np.linalg.cond`, E2E offline con `ledoit_wolf` sobre el provider sintético de feat-021 (weights finitos suma 1, sin tocar asserts existentes).

## Risks / Trade-offs

- [sklearn centra los retornos antes de shrink → para retornos ya centrados el resultado difiere del shrink naive] → Mitigación: el contrato es paridad contra sklearn, no contra fórmula manual; el test de paridad usa el mismo input para ambos.
- [Import de sklearn en métricas enlentece arranque del CLI] → aceptado en D2; si molesta en práctica, se mueve a lazy sin cambiar contrato.
- [Condición number no siempre baja estrictamente con OAS] → el requirement pide ≤ (no <); con matrices bien condicionadas ambos coinciden aprox.
- [Walk-forward con shrinkage cambia pesos OOS] → solo cuando el usuario configura el estimador; el default conserva los resultados vigentes.

## Migration Plan

Sin migración (paramétrico, default retrocompatible). Rollback = revert del commit. Flip de default en v0.2.0 documentado en ADR 005 como single-flip con evidencia WF.
