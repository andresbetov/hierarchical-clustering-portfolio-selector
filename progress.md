# Session Progress Log

## Current State

**Last Updated:** 2026-08-26
**Branch:** `feat/quality-gates-ci` (desde `develop@723b139`, post PR #7)
**Active Feature:** feat-004 quality-gates-ci → **done**

Fase Higiene (posiciones 1-4 del DAG) completa. Los cuatro gates corren localmente vía `./init.sh` y en CI servidor sobre develop/main con matriz Python 3.11/3.13.

## Status

### What's Done

- [x] feat-001 orden de resolución (PR #5) · feat-002 suite real (PR #6) · feat-003 manifests+lock (PR #7)
- [x] **feat-004**: dev-deps pinned (ruff 0.16.4, pyright 1.1.411); configs ruff(E,F,W,I/l120)+pyright(basic); Makefile lint/types; init.sh ejecuta los 4 gates; ci.yml matriz; pre-commit opt-in; badge CI; 18 hallazgos ruff y 21 de pyright resueltos (todos mecánicos, registrados)

### What's In Progress

- [ ] —

### What's Next

1. PR de esta rama → develop
2. `feat-005` logging-and-headless-viz (M4+M5, posiciones 5-6): logger por paquete + backend Agg — dep única feat-004 ✓
3. Luego feat-006 (M7 entrypoint) paralelizable tras merge
4. Regla vigente: features complejos (016/018/021/023) leen docs/decision-log-feat001.md

## Blockers / Risks

- pyright baja a `basic`: strict es progresión futura (registrar como feature dedicado si se quiere formalizar)
- scipy sigue siendo excepción documentada hasta feat-018

## Evidence of Completion

- [x] make lint "All checks passed!" · make types 0 errors · make test 16 passed · ./init.sh exit 0 (los 4 gates visibles)

## Decisions Made

- Implicit-Optional (`str = None`) modernizado a `X | None` en firmas: cambio de tipado puro, cero comportamiento
- `float(...)` en métricas de data_fetch + `np.asarray(dtype=float64)` para `.values`: contrato más fuerte del dict de métricas
- Reglas ruff minimalistas (E,F,W,I) — endurecer queda como progresión explícita
- pre-commit opt-in: CI es la autoridad enforcing

## Files Modified This Session

- `pyproject.toml` (dev group + tool.ruff + tool.pyright), `uv.lock`, `Makefile`, `init.sh`
- `.github/workflows/ci.yml` (nuevo), `.pre-commit-config.yaml` (nuevo)
- `CONTRIBUTING.md` (gates), `README.md` (badge), fixes menores en portfolio_engine (tiping signatures)
- tracker/progress/handoff + openspec change feat-004

## Notes for Next Session

- PR → develop; luego feat-005 con flujo openspec completo
