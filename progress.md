# Session Progress Log

## Current State

**Last Updated:** 2026-08-28
**Branch:** `feat/linkage-parameter` — DAG v0.1.0 en curso (feat-028..034 done, CP1 cerrado, CP2 en curso)
**Active Feature:** feat-034 (cerrada en esta sesión); siguiente: feat-035

Hito v0.1.0 en marcha. **CP1 "Estable" COMPLETO** · CP2 "Correcta" en curso: plataforma (032), cov estimator (033, ADR 005) y linkage (034, ADR 006) cerrados; siguiente feat-035 (walk-forward con paridad productiva + benchmarks). Suite 177 passed.

## Status

### What's Done (hito v0.1.0 — Fase A / CP1)

- [x] **feat-034** (2026-08-28): linkage parametrizable (ADR 006) — `linkage_method ∈ {single, ward, average}` validado en config; `calculate_hrp_weights(cov, linkage_method)` propaga a scipy (ValueError pre-scipy para desconocidos); default single snapshot-compatible; +7 tests (ward 3 bloques con adyacencia intra-bloque, average, snapshot bit a bit); suite 170→177; specs configuration-contract + numeric-correctness sincronizadas; change `2026-08-28-feat-linkage-parameter` archivado
- [x] **feat-033** (2026-08-28): estimador de covarianza parametrizable (ADR 005) — `covariance_estimator ∈ {sample, ledoit_wolf, oas}` validado en config; seam `estimate_covariance` en core/metrics consumida por pipeline y walk-forward; sample bit a bit (red feat-021 intacta), shrinkage con paridad sklearn 1e-12; +11 tests + E2E offline ledoit_wolf; suite 159→170; specs configuration-contract + numeric-correctness sincronizadas; change `2026-08-28-feat-covariance-estimator` archivado
- [x] **feat-032** (2026-08-28): breaking plataforma — `requires-python>=3.11` (drop 3.10, EOL 2026-10-31/SPEC 0) + `scikit-learn>=1.8` (para feat-033); CI matrix 3.11/3.12/3.13; uv.lock re-resuelto (sklearn 1.9.0, threadpoolctl, narwhals; scipy 1.15.3 fuera por resolución exclusiva 3.10); `uv sync --frozen` + import verificados; CHANGELOG breaking; change `2026-08-28-chore-python-floor-311-sklearn` archivado
- [x] **feat-031** (2026-08-28): sync documental pre-release — specs merged corregidas (`hrp` en el set de métodos de configuration-contract, errata SHANL, doble negación en numeric-correctness, rango 3.11-3.13 en project-packaging); feat-018 tasks.md cerrado retroactivo; CHANGELOG.md inicial (Keep a Changelog); progress.md consolidado; change `2026-08-28-docs-spec-sync-pre-release` archivado (skip_specs documental)
- [x] **feat-030** (2026-08-28): fix determinismo de fixtures — `abs(hash(ticker))` salado por PYTHONHASHSEED → `zlib.crc32(ticker.encode())`; +1 test de subprocesos (bytes idénticos seeds 1 vs 999); suite 158→159; spec `system-verification` sincronizada; PR #34
- [x] **feat-029** (2026-08-28): fix walk-forward primer retorno — `np.roll`+`[1:]` omitía el primer día del test; ventana extendida `[test_start−1, test_end)` leak-free; +1 test analítico (0.52/60·252 exacto); suite 157→158; spec `out-of-sample-validation` sincronizada; PR #33
- [x] **feat-028** (2026-08-28): fix crash ruta legacy del reporte — covarianza N×N sin rebanar con M<N; rebanado en pipeline reutilizando `create_portfolio_covariance_matrix`; +3 tests; suite 154→157; spec `numeric-correctness` sincronizada; PR #32

### What's Done (DAG histórico feat-001..027 — 27/27, cerrado 2026-08-26)

Motor HRP jerárquico real (feat-018), walk-forward anti-fuga (feat-026), arquitectura por capas con provider seam (feat-023), universo YAML (feat-024), ADRs 001-004, specs OpenSpec 11 capacidades, CI 4 gates, 154 tests. Detalle por feature en `feature_list.json:evidence`. Auditoría original: `docs/auditoria-tecnica.md` (histórico).

### What's In Progress

- [ ] —

### What's Next (DAG v0.1.0 — Fase B/D)

1. feat-035 `feat/walk-forward-production-parity` (filtros por fold + benchmarks 1/N e IVP) → feat-036 `fix/sharpe-convention` → feat-037 `feat/alignment-overlap-guard`
2. Fase D: feat-038 cache parquet → feat-039 CLI+dendrograma → feat-040 cobertura → feat-041 release v0.1.0

## Process Deviations (transparencia)

- **feat-024 se implementó sin artifacts OpenSpec previos** (proposal/design/tasks ausentes): flujo saltado en la racha. La impl pasó gates/tests, pero viola el workflow propio. Corrección de proceso: ninguna feature posterior repite esto; verificado contra feat-025+.
- tasks.md de feat-024 perdido por rm accidental del directorio pre-archive; la evidencia vive en esta nota y en el commit.

## Blockers / Risks

- **Hallazgo feat-028 (fuera de scope, propuesto como feature nueva)**: `generate_complete_analysis_report` chart 4 re-cálcula matrices full-universe con `construct_returns_matrix` sobre `historical_prices` crudos (longitudes por-ticker propias); con datos reales yfinance cualquier ticker con calendario distinto (suspensión, IPO, delisting) lanza ValueError. Candidata: feature de alineación full-universe para charts (emparentada con feat-037; evaluar si se absorbe en feat-037 o se abre aparte).
- pyright baja a `basic`: strict es progresión futura (registrar como feature dedicado si se quiere formalizar).
- aviso cosmético Node20→24 en GitHub Actions (bump futuro).

## Evidence of Completion

- feat-031: `openspec validate --specs` 11/11 · `grep SHANL openspec/` = 0 · set de métodos en spec == enum código (6) · `./init.sh` exit 0 con 159 passed · CHANGELOG.md con formato Keep a Changelog
- feat-028..030: evidencia completa por feature en `feature_list.json:evidence` (rojo TDD → verde → init.sh fresco → spec sincronizada → PR squash)

## Decisions Made

- feat-031 declarado `skip_specs: true` (cambio puramente documental: las specs se corrigen para reflejar comportamiento YA implementado — precedente feat-025)
- CHANGELOG arranca con `[Unreleased]` + placeholder `[0.1.0]` que feat-041 completará y fechará al tag
- `project-packaging` actualizado a 3.11-3.13 en feat-031 para que feat-032 solo implemente lo que la spec ya declara
