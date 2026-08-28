# Session Handoff

## Current Objective

- Goal: v0.1.0 "estable y correcta" — DAG feat-028..041 registrado (commit 27580a7)
- Current status: rama `feat/covariance-estimator` (feat-033 lista para PR) · suite 170 passed · CP1 cerrado, CP2 en curso (2/6)
- Next: feat-034 `feat/linkage-parameter` (ADR 006: single default + ward/average)

## Completed This Session

- feat-033: estimador de covarianza parametrizable (ADR 005) — enum validado {sample, ledoit_wolf, oas}, seam `estimate_covariance` consumida por pipeline + walk-forward, default sample bit a bit, paridad sklearn 1e-12; +11 tests + E2E ledoit_wolf; specs sincronizadas; change archivado

## Verification Evidence

| Check | Command | Result | Notes |
|---|---|---|---|
| TDD | tests nuevos pre-impl | rojo | import error (seam inexistente) + param inexistente |
| suite | `./init.sh` | ✓ 170 passed (159+11) | ruff cazó 2 I001 (corregidos), pyright 0 |
| red feat-021 | git diff tests caracterización | 0 | sample bit a bit por construcción (D4) |
| specs | validate + sync + archive | ✓ 11/11 | 2 deltas ADDED sincronizados |

## Decisions Made

- ADR 005: default `sample` en v0.1.0 (single-flip discipline); flip a `ledoit_wolf` en v0.2.0 condicionado a evidencia WF (benchmarks feat-035)
- D2: import sklearn a nivel de módulo en core/metrics (dep declarada, honesto)
- D3: degeneración (n_rows<=1) → matriz NaN sin invocar sklearn

## Blockers / Risks

- feat-034 (ADR 006) debe preservar snapshot bit a bit con default `single` (red feat-021)
- Hallazgo feat-028 sigue abierto: chart 4 full-universe con precios crudos de longitud desigual (candidata a absorberse en feat-037)
- feat-033 requiere PR → develop (squash) antes de abrir feat-034

## Next Session Startup

1. PR de feat-033 → CI verde ×3 → squash merge → borrar rama
2. feat-034: rama `feat/linkage-parameter`, ADR 006 previo, TDD snapshot single
3. Rutina: TDD rojo → fix → ./init.sh fresco → evidencia en feature_list.json

## Lecciones consolidadas del proyecto

1. Los heredocs fuzzy python son no-op silenciosos — SOLO Edit/Write tools para código fuente
2. TDD de caracterización atrapó 6 defectos reales durante la ejecución (incl. 3 en la racha final)
3. Severidad ≠ orden: las dependencias técnicas mandan; el flip HRP único demostró el valor del DAG
4. OpenSpec validate es pre-commit del diseño: deltas deben matchear specs main exactos
