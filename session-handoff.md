# Session Handoff

## Current Objective

- Goal: v0.1.0 "estable y correcta" — DAG feat-028..041 registrado (commit 27580a7)
- Current status: rama `feat/linkage-parameter` (feat-034 lista para PR) · suite 177 passed · CP1 cerrado, CP2 en curso (3/6)
- Next: feat-035 `feat/walk-forward-production-parity` (filtros por fold + benchmarks 1/N e IVP — la feature más grande de CP2)

## Completed This Session

- feat-034: linkage parametrizable (ADR 006) — {single, ward, average}, default single snapshot-compatible; ValueError pre-scipy; propagación config→HRP→pipeline→WF; +7 tests; specs sincronizadas; change archivado

## Verification Evidence

| Check | Command | Result | Notes |
|---|---|---|---|
| TDD | tests nuevos pre-impl | rojo | 7 failures (param inexistente) |
| suite | `./init.sh` | ✓ 177 passed (170+7) | gates verdes |
| red feat-021 | git diff tests caracterización | solo adiciones | snapshot single bit a bit |
| specs | validate + sync + archive | ✓ 11/11 | 2 deltas ADDED sincronizados |

## Decisions Made

- ADR 006: default `single` en v0.1.0; flip a `ward` candidato v0.2.0 evaluado junto con ADR 005 (evidencia WF conjunta)
- D1: parámetro con default en `calculate_hrp_weights` (API pública no rompe); D2: doble validación (config + función, fail loud pre-scipy)
- D4: test de adyacencia intra-bloque con ward vía `_leaf_order` (topología verificada, no solo simplex)

## Blockers / Risks

- feat-035 (deps 029/033/034 satisfechas): debe aplicar apply_asset_filters por fold de train, añadir benchmarks equal/ivp al WalkForwardReport y documentar embargo 5d/purga 1d — mantener el test anti-fuga intacto
- Hallazgo feat-028 sigue abierto: chart 4 full-universe con precios crudos de longitud desigual (candidata a absorberse en feat-037)
- feat-034 requiere PR → develop (squash) antes de abrir feat-035

## Next Session Startup

1. PR de feat-034 → CI verde ×3 → squash merge → borrar rama
2. feat-035: rama `feat/walk-forward-production-parity`, OpenSpec propose→apply→archive (design obligatorio: universos variables por fold + benchmarks)
3. Rutina: TDD rojo → fix → ./init.sh fresco → evidencia en feature_list.json

## Lecciones consolidadas del proyecto

1. Los heredocs fuzzy python son no-op silenciosos — SOLO Edit/Write tools para código fuente
2. TDD de caracterización atrapó 6 defectos reales durante la ejecución (incl. 3 en la racha final)
3. Severidad ≠ orden: las dependencias técnicas mandan; el flip HRP único demostró el valor del DAG
4. OpenSpec validate es pre-commit del diseño: deltas deben matchear specs main exactos
