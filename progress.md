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
- [x] **feat-005**: logging aislado+idempotente, LOG_LEVEL funcional, guard Agg, pipeline sin pyplot, 14 tests contrato — PR #9
- [x] **feat-006**: paquete instalable + entrypoint portfolio-run — PR #10, CI verde x2
- [x] **feat-007**: risk_free_rate requerido sin default; market-data-contract creada — PR #11
- [x] **feat-008**: alineación por calendario común (inner join) + guard loud + pandas explícita + 8 tests — PR #12

### What's In Progress

- [ ] —

### What's Next

1. PR de esta rama → develop
2. **Siguiente del DAG**: feat-011 lookback-param-calendar (A4, pos 10; deps feat-008 ✓) o feat-009 numeric-guards (C3, pos 11; deps feat-008 ✓) o feat-013 frozen-config (M1, pos 14; dep feat-002 ✓) — tres desbloqueados; elegir uno por sesión
3. Luego: feat-010→M10, feat-012→C2, feat-014→C4, y así hasta HRP real (feat-018)
4. Regla vigente: features complejos leen docs/decision-log-feat001.md
4. Regla vigente: features complejos (016/018/021/023) leen docs/decision-log-feat001.md

## Blockers / Risks

- pyright baja a `basic`: strict es progresión futura (registrar como feature dedicado si se quiere formalizar)
- scipy sigue siendo excepción documentada hasta feat-018

## Evidence of Completion

- [x] uv sync instala el proyecto ("Built hierarchical-clustering-portfolio-selector"); import desde cwd externo OK
- [x] entrypoint resuelto: portfolio-run -> portfolio_engine.cli:main (importlib.metadata)
- [x] suite 35 passed (+2 contrato A2) · gates verdes · grep 0.03 fuente=0

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

## Decisions Made

- hatchling vs setuptools/flit: config mínimo, estándar en análisis numérico flat-layout
- Edición TOML corrupta cazada por build failure en vivo: dependencies quedó dentro de project.scripts — reordenado canónico; lección: validar estructura completa tras inserts multi-sección
- pythonpath=["."] se conserva belt-and-suspenders pese a instalación real

## Notes for Next Session

- PR → develop; luego feat-007 abre Fase D (integridad de datos)
