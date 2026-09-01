# Session Handoff

## Current Objective

- Goal: v0.1.0 "estable y correcta" — DAG feat-028..041 registrado (commit 27580a7)
- Current status: rama `feat/walk-forward-production-parity` (feat-035 lista para PR) · suite 182 passed · CP1 cerrado, CP2 en curso (4/6)
- Next: feat-036 `fix/sharpe-convention-unification` (ln(1+rf) coherente con log-returns + addendum ADR 003)

## Completed This Session

- feat-035: paridad productiva del walk-forward — filtros por fold (reuso apply_asset_filters), benchmarks ex-ante equal/ivp con pesos auditables, 6 medianas en to_dict; validación iterativa con subagente adversarial (1 defecto real cazado: guard NaN-blind → fix + test regresión); spec sincronizada; change archivado

## Verification Evidence

| Check | Command | Result | Notes |
|---|---|---|---|
| TDD | 3 tests nuevos pre-impl | rojo | sin filtrado ni benchmarks |
| suite | `./init.sh` | ✓ 182 passed (177+5) | gates verdes |
| review adversarial | subagente general | 1 MEDIO (NaN-blind) + 5 notas | fix aplicado + hardening isfinite + import muerto fuera |
| specs | validate + sync + archive | ✓ 11/11 | MODIFIED + ADDED en out-of-sample-validation |
| asserts existentes | git diff tests | 3 líneas removidas | solo fixtures D6 (umbrales relajados), asserts intactos |

## Decisions Made

- D1: reuso literal de apply_asset_filters por fold (paridad real, no reimplementación)
- D2: weight_vector con ceros para excluidos (log_test intacto, feat-029 preservado)
- D3: benchmarks sobre supervivientes (universo invertible ex-ante, comparación justa) — DeMiguel 2007/bestfolio
- D4: fold.benchmarks con "weights" auditables + 6 medianas en to_dict
- D6: fixtures existentes con umbrales relajados (intención original preservada, asserts intactos)

## Blockers / Risks

- Hallazgo feat-028 sigue abierto: chart 4 full-universe con precios crudos de longitud desigual (candidata a absorberse en feat-037)
- feat-036 cambiará valores de Sharpe con rf≠0 → actualizar asserts que pinen numeradores con rf (red feat-021)
- feat-035 requiere PR → develop (squash) antes de abrir feat-036

## Next Session Startup

1. PR de feat-035 → CI verde ×3 → squash merge → borrar rama
2. feat-036: rama `fix/sharpe-convention-unification`, OpenSpec propose→apply→archive, TDD con rf=0 invariante + ln(1.045) exacto
3. Rutina: TDD rojo → fix → ./init.sh fresco → evidencia en feature_list.json

## Lecciones consolidadas del proyecto

1. Los heredocs fuzzy python son no-op silenciosos — SOLO Edit/Write tools para código fuente
2. TDD de caracterización atrapó 6 defectos reales durante la ejecución (incl. 3 en la racha final)
3. Severidad ≠ orden: las dependencias técnicas mandan; el flip HRP único demostró el valor del DAG
4. OpenSpec validate es pre-commit del diseño: deltas deben matchear specs main exactos
