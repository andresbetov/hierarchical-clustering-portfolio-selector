## Context

Ver proposal.md (Why), ADR 006 (decisión) y los deltas (What). Estado: `hrp.py:86` llama `linkage(condensed, method="single")`; `calculate_optimal_portfolio_weights_hrp` (allocation.py) y `walk_forward.py` invocan `calculate_hrp_weights(covariance_matrix)` sin linkage. La red feat-021 pina los pesos del default (analítico [0.8, 0.2], invarianza-permutación). `scipy.cluster.hierarchy.linkage` acepta nativamente `single|ward|average` sobre la misma matriz condensada.

## Goals / Non-Goals

**Goals:**
- Un solo parámetro `linkage_method` fluyendo config → pipeline/WF → scipy.
- Default `single` bit a bit con el snapshot vigente (red feat-021 intacta sin tocar asserts).
- ward/average operativos y testeables sobre universos de bloques de correlación.

**Non-Goals:**
- NO cambiar el default (single-flip discipline; flip a `ward` diferido a v0.2.0 — ADR 006).
- NO tocar quasi-diagonalización ni bisección (solo el método de linkage).
- NO exponer `complete`/`centroid`/otros en v0.1.0 (set cerrado, ampliable en v0.2.0).

## Decisions

**D1 — Parámetro con default en `calculate_hrp_weights`** (`linkage_method="single"`), no solo en config: los callers directos (tests, usuarios de la API) siguen compilando sin cambios; el default en la firma coincide con el default de config. Alternativa descartada: parámetro obligatorio — rompe la API pública sin necesidad.

**D2 — Validación doble:** config valida en `__post_init__` (contract-first); `calculate_hrp_weights` valida defensivamente y lanza `ValueError` antes de tocar scipy (patrón feat-013: fail loud, sin estado intermedio).

**D3 — Threading mínimo:** `calculate_optimal_portfolio_weights_hrp(filtered_metrics, covariance_matrix, config)` ya recibe config → pasa `config.linkage_method`; `walk_forward_evaluate` igual. Sin nuevos parámetros en firmas públicas más allá del default en `calculate_hrp_weights`.

**D4 — Test de adyacencia de bloques con ward:** universo de 6 activos en 3 bloques (ρ=0.9 intra-bloque, ρ≈0 inter-bloque, cov construida por cholesky desde retornos sintéticos); assert: pares del mismo bloque adyacentes en el orden de hojas resultante (via `_leaf_order` o verificación de distancias quasi-diagonales). Complementa los asserts de simplex.

## Risks / Trade-offs

- [ward con muchas distancias empatadas puede reordenar hojas de forma no única] → Mitigación: el test usa bloques bien separados (ρ=0.9 vs 0.05) para evitar empates; asserts de adyacencia toleran permutación interna del bloque.
- [Average puede producir árboles desbalanceados en bloques] → solo se testea validez (finitos, suma 1), no topología.
- [Snapshot default] → cubierto por la suite existente sin modificaciones (D1).

## Migration Plan

Sin migración (paramétrico, default retrocompatible). Rollback = revert del commit. Flip de default en v0.2.0 documentado en ADR 006, evaluado junto con ADR 005 sobre evidencia walk-forward conjunta.
