# Session Progress Log

## Current State

**Last Updated:** 2026-08-26
**Branch:** `feat/logging-headless-viz` (desde `develop@382a482`, post PR #8)
**Active Feature:** feat-005 logging-and-headless-viz → **done**

Fase Higiene posiciones 1-6 completas. CI verde en primera corrida (matriz 3.11/3.13, run 32996200798). Suite 16→30 passed con tests de contrato runtime. `make run-debug` ahora funciona de verdad (LOG_LEVEL era ignorado).

## Status

### What's Done

- [x] feat-001 orden de resolución (PR #5) · feat-002 suite real (PR #6) · feat-003 manifests+lock (PR #7)
- [x] **feat-004**: dev-deps pinned; ruff(E,F,W/I/l120)+pyright(basic); Makefile lint/types; init.sh 4 gates; ci.yml matriz; pre-commit opt-in — 18+21 hallazgos mecánicos resueltos · PR #8 mergeada
- [x] **feat-005**: logging de paquete aislado (propagate=False, idempotente, LOG_LEVEL funcional), guard Agg determinista + finalize_report_show, pipeline sin pyplot, 14 tests de contrato nuevos

### What's In Progress

- [ ] —

### What's Next

1. PR de esta rama → develop
2. `feat-006` package-console-entrypoint (M7, posición 7): [project.scripts] sobre identidad feat-003 — cierra Fase Higiene (1-7)
3. Luego Fase D datos: A2→A3→A4→C3→M10→C2 (feat-007..012)
4. Regla vigente: features complejos leen docs/decision-log-feat001.md
4. Regla vigente: features complejos (016/018/021/023) leen docs/decision-log-feat001.md

## Blockers / Risks

- pyright baja a `basic`: strict es progresión futura (registrar como feature dedicado si se quiere formalizar)
- scipy sigue siendo excepción documentada hasta feat-018

## Evidence of Completion

- [x] CI primera corrida verde en ambos jobs de matriz (run 32996200798) tras merge feat-004
- [x] make lint/types/test verdes · ./init.sh exit 0 · suite 30 passed · smoke DEBUG/idempotencia/env-inválido OK

## Decisions Made

- Logger "portfolio_engine" propietario vs root: aislamiento de caplog/ruido; idempotencia por deduplicación (tagged handler)
- getLevelName(int)→string hallado por TDD: ints retornan directo, strings por lookup — documentado inline
- Guard Agg SOLO si no-DISPLAY && !MPLBACKEND && !darwin; función pura testeable + noqa E402 justificados
- `float(...)` en métricas de data_fetch + `np.asarray(dtype=float64)` para `.values`: contrato más fuerte del dict de métricas
- Reglas ruff minimalistas (E,F,W,I) — endurecer queda como progresión explícita
- pre-commit opt-in: CI es la autoridad enforcing

## Files Modified This Session

- `pyproject.toml` (dev group + tool.ruff + tool.pyright), `uv.lock`, `Makefile`, `init.sh`
- `.github/workflows/ci.yml` (nuevo), `.pre-commit-config.yaml` (nuevo)
- `CONTRIBUTING.md` (gates), `README.md` (badge), fixes menores en portfolio_engine (tiping signatures)
- tracker/progress/handoff + openspec change feat-004

## Notes for Next Session

- PR → develop; luego feat-006 y arranca Fase D (datos)
