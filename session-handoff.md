# Session Handoff

## Current Objective

- Goal: v0.1.0 "estable y correcta" — DAG feat-028..041 registrado (commit 27580a7)
- Current status: rama `fix/test-fixture-determinism` (feat-030 lista para PR) · suite 159 passed
- Next: feat-031 `docs/spec-sync-pre-release` (cierra CP1 "Estable": specs + CHANGELOG inicial + limpieza progress/handoff)

## Completed This Session

- feat-030: fix determinismo de fixtures. TDD rojo (subprocesos PYTHONHASHSEED=1 vs 999 → paneles distintos) → verde (bytes idénticos con `zlib.crc32`); +1 test de contrato; spec `system-verification` sincronizada; change archivado
- feat-028 (PR #32) y feat-029 (PR #33) mergeadas a develop en sesiones previas

## Verification Evidence

| Check | Command | Result | Notes |
|---|---|---|---|
| suite | `./init.sh` | ✓ 159 passed (158+1) | rojo pre-fix: AssertionError bytes distintos bajo seeds saladas |
| gates | ruff / pyright / compileall | ✓ / ✓ / ✓ | ruff cazó import muerto (corregido en la misma feature) |
| red feat-021/026 | git diff tests existentes | 0 asserts modificados | solo conftest.py cambia; invariantes sostenidos con paneles nuevos |
| openspec | validate + archive + validate --specs | ✓ 11 specs OK | delta MODIFIED sincronizado en system-verification |

## Decisions Made

- D1: `zlib.crc32(ticker.encode())` como derivación estable de seed (stdlib, determinista entre procesos)
- D2: test vía subprocesos reales con env PYTHONHASHSEED distinto (comportamiento, no estática)

## Blockers / Risks

- Hallazgo feat-028 sigue abierto: chart 4 full-universe con `construct_returns_matrix` sobre precios crudos de longitud desigual (candidata a absorberse en feat-037)
- feat-030 requiere PR → develop (squash) antes de abrir feat-031
- feat-031 debe cerrar CP1: sync configuration-contract (+hrp, SHANL), CHANGELOG inicial KaC, limpiar progress.md duplicado, session-handoff actualizado

## Next Session Startup

1. PR de feat-030 → CI verde → squash merge → borrar rama
2. feat-031: rama `docs/spec-sync-pre-release`, OpenSpec propose→apply→archive
3. Rutina: TDD rojo → fix → ./init.sh fresco → evidencia en feature_list.json

## Lecciones consolidadas del proyecto

1. Los heredocs fuzzy python son no-op silenciosos — SOLO Edit/Write tools para código fuente
2. TDD de caracterización atrapó 6 defectos reales durante la ejecución (incl. 3 en la racha final)
3. Severidad ≠ orden: las dependencias técnicas mandan; el flip HRP único demostró el valor del DAG
4. OpenSpec validate es pre-commit del diseño: deltas deben matchear specs main exactos
