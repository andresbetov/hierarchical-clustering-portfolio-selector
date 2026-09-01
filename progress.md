# Session Progress Log

## Current State

**Last Updated:** 2026-08-31
**Branch:** `feat/alignment-overlap-guard` — DAG v0.1.0 en curso (feat-028..037 done, CP1 cerrado, CP2 en curso)
**Active Feature:** feat-037 (cerrada en esta sesión); siguiente: feat-038

Hito v0.1.0 en marcha. **CP1 "Estable" COMPLETO** · CP2 "Correcta" en curso: plataforma (032), cov estimator (033), linkage (034), walk-forward paridad+benchmarks (035), convención Sharpe log (036) y overlap guard (037) cerrados; siguiente Fase D (cache parquet). Suite 203 passed.

## Status

### What's Done (hito v0.1.0 — Fase A / CP1)

- [x] **feat-037** (2026-08-31): guard de solapamiento — `minimum_overlap_ratio=0.9` validado (0,1], `align_prices_to_common_calendar` con post-DataFrame `notna().mean()` sobre unión, warning nombrado (ticker+ratio), `MIN_COMMON_ROWS` sobre supervivientes + `n==0` ValueError, chart 4 full-universe alineado con mismo guard; pipeline pruning de `filtered_metrics` para coherencia dimensional; 14 tests nuevos (50% excluido, 1.0 bit-identical, frontera 0.9, 1 survivor, 0 survivors, hueco, orden, warning) + validación config (0/1.0/1.0001) y revisión adversarial (3 ALTA: ruff walrus, pyright cast, chart 4 crash) corregidos; suite 187→203; specs `market-data-contract` + `configuration-contract` sincronizadas; change `2026-08-31-feat-alignment-overlap-guard` archivado
- [x] **feat-036** (2026-08-31): coherencia logarítmica del Sharpe — `excess = return_log − ln(1+rf)` vía `math.log1p` en 6 call-sites y propiedad `risk_free_rate_log` (single source); `rf=0` invariante, `rf=0.045` pin `0.044016885416774`; pinnings migrados a `(ret-log1p(rf))/vol` rel 1e-12 + robustez `rf<=-1 → nan` y `VOL_FLOOR_EPS` unificado en `walk_forward._oos_metrics`; addendum ADR 003 2026-09-01 (Dykstra post-hoc euclídea vs varianza jerárquica, `n=5,max=0.30` cuantificado); suite 182→187; specs `numeric-correctness` + `quant-docs` sincronizadas; change `2026-08-31-fix-sharpe-convention` archivado
- [x] **feat-035** (2026-08-28): walk-forward con paridad productiva — filtros de producción por fold de train (reuso literal de apply_asset_filters), benchmarks ex-ante equal/ivp sobre el mismo universo y los mismos retornos OOS (pesos auditable por fold), 6 medianas nuevas en to_dict; guard NaN-blind corregido tras revisión adversarial con subagente (+test de regresión test_rows=1); suite 177→182; spec `out-of-sample-validation` sincronizada (MODIFIED + ADDED); change `2026-08-28-feat-walk-forward-production-parity` archivado
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

1. Fase D: feat-038 cache parquet → feat-039 CLI+dendrograma → feat-040 cobertura → feat-041 release v0.1.0

## Process Deviations (transparencia)

- **feat-024 se implementó sin artifacts OpenSpec previos** (proposal/design/tasks ausentes): flujo saltado en la racha. La impl pasó gates/tests, pero viola el workflow propio. Corrección de proceso: ninguna feature posterior repite esto; verificado contra feat-025+.
- tasks.md de feat-024 perdido por rm accidental del directorio pre-archive; la evidencia vive en esta nota y en el commit.

## Blockers / Risks

- pyright baja a `basic`: strict es progresión futura (registrar como feature dedicado si se quiere formalizar).
- aviso cosmético Node20→24 en GitHub Actions (bump futuro).

## Evidence of Completion

- feat-037: `openspec validate --specs` 12/12 (market-data-contract + configuration-contract) · guard post-DataFrame con `notna().mean()` sobre unión · `./init.sh` 203 passed · ruff/pyright/compileall verdes · revisión adversarial (2 subagentes) con 3 ALTA (ruff/pyright/chart4) corregidos
- feat-036: `openspec validate --specs` 12/12 (`quant-docs` nueva) · `grep -rn log1p` 6+ call-sites migrados · `./init.sh` 187 passed · ruff/pyright/compileall verdes · revisión adversarial (3 subagentes) con 1 ALTA (F401) corregida
- feat-031: `openspec validate --specs` 11/11 · `grep SHANL openspec/` = 0 · set de métodos en spec == enum código (6) · `./init.sh` exit 0 con 159 passed · CHANGELOG.md con formato Keep a Changelog
- feat-028..030: evidencia completa por feature en `feature_list.json:evidence` (rojo TDD → verde → init.sh fresco → spec sincronizada → PR squash)

## Decisions Made

- feat-037: guard post-DataFrame (B) con `notna().mean()` sobre unión; `minimum_overlap_ratio` en config (0.9) + param en función con default idéntico; chart 4 full-universe alineado con mismo guard (absorbe blocker progress.md:45)
- feat-036: híbrida A+B sin ciclo — `config.risk_free_rate_log` usa `math.log1p` directo; helper `risk_free_log_rate` para float-only sites; duplicación intencional documentada en `design.md:D1`; addendum ADR 003 fechado 2026-09-01 (no supersede) cuantifica `n=5,max=0.30`
- feat-031 declarado `skip_specs: true` (cambio puramente documental: las specs se corrigen para reflejar comportamiento YA implementado — precedente feat-025)
- CHANGELOG arranca con `[Unreleased]` + placeholder `[0.1.0]` que feat-041 completará y fechará al tag
- `project-packaging` actualizado a 3.11-3.13 en feat-031 para que feat-032 solo implemente lo que la spec ya declara
