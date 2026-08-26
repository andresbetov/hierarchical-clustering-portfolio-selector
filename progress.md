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
### What's Done (racha feat-011..014)

- [x] **feat-011** A4: ventana calendario exacta `_resolve_window` pura + lookback requerido sin default (+6 tests) — PR #13
- [x] **feat-009** C3: ε-floor, Sharpe NaN para vol degenerada, ddof=1 consistente, corr diagonal honesta, filtros nombrando excluidos, risk-parity protegida (+13 tests) — PR #14 · capability `numeric-correctness`
- [x] **feat-010** M10: piso ε en inverse-vol reutilizando helper compartido (+1 test) — PR #15
- [x] **feat-012** C2: batch único yf.download, fallback Adj→Close nombrado, rechazos agregados, retry stdlib acotado (+7 tests offline vía monkeypatch del boundary) — PR #16
- [x] **feat-013** M1: config frozen dataclass validada, enum público, dispatch sin fallback muerto (+10 tests; fixture integración migrada a kwargs) — PR #17 · capability `configuration-contract`
- [x] **feat-014** C4: Dykstra cíclico {≥min}{≤max}{simplex} — bounds simultáneos garantizados; 2 bugs propios cazados por TDD (+8 tests, estrés 100 seeds) — PR #18

## What's Next

### What's Done (esta racha feat-019..020)

- [x] **feat-019** B5: solvers cuadráticos via np.linalg.solve sin inv explícita; _ensure_positive_definite cholesky+jitter determinista loggeado; zero-trace irreparable por contrato (+7 tests) — PR #23
- [x] **feat-020** A5: Sharpe reporte con wTΣw real; fallback diagonal solo defensivo con warning (+6 tests: ρ=0 equivalencia legacy, ρ=1 identidad analítica) — PR #24

## What's Next

1. `feat-021` deep-characterization-suite (M8, posición 22): tests caracterización del estado final + hypothesis + fixtures HRP — red para M6/M3
2. `feat-022` numba-pruning y `feat-023` layered-architecture — ambos tras la red de feat-021
3. Node20→24 actions bump cosmico pendiente
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
