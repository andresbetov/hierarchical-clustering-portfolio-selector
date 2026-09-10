# Session Progress Log

## Current State

**Last Updated:** 2026-09-09
**Branch:** `feat/allocation-diagnostics` — feat-045 done local con validación pre-push (regla del usuario). `develop @ 13672b7` base.

Hito v0.1.0 en marcha. **CP1 "Estable" COMPLETO** · **CP2 "Correcta" COMPLETO** (032-037) · **Fase D CLI+dendrograma COMPLETO** · **feat-040 cobertura COMPLETO**: gate 85% TOTAL combinado de coverage.py (líneas+branches). Épico JSON en curso: suite `./init.sh` **262 passed + cobertura TOTAL 86.21%** `All checks passed!` `pyright 0` `openspec validate --all` 14/14.

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

### What's Done (Fase D — CLI + Dendrograma)

- [x] **feat-039** (2026-09-04): CLI operativo completo — `_build_parser` con `--method` (choices 6, dest `weight_allocation_method` default `hrp`), `--covariance-estimator` (3, `sample`), `--linkage/--linkage-method` (3, `single`), `--save/--no-save` (`BooleanOptionalAction` True), `--show/--no-show` (False), `--universe` metavar PATH, `--refresh-cache`; `main(argv, universe_path)` propaga a `PortfolioConfig` + `generate_complete_analysis_report(save_plots, show_plots, provider)` con legacy `universe_path` warning + bypass; **seam** `build_hrp_linkage` en `hrp.py` (single source distancia firmada `sqrt(0.5*(1-corr))`, valida `LINKAGE_METHODS` pre-scipy, `n<2` ValueError) y refactor `calculate_hrp_weights` snapshot bit-identical; **viz** `plot_hrp_dendrogram` en `reporting.py` (headless `Agg` + `_finalize_plot`, `n=0/1/2` guards, `tickers/cov` mismatch guard, `width capped 40`, `WAYLAND_DISPLAY` headless fix, iterative `_leaf_order` sin recursion limit); **pipeline** `CHART_FILENAMES["hrp_dendrogram"]` + `plot_hrp_dendrogram` tras `optimal_portfolio_analysis` en `try/except` warning, log `plots=8`; **exports** `build_hrp_linkage`+`plot_hrp_dendrogram` en `__init__.py` + `__all__`; tests `test_cli.py` +7 (method/cov/linkage/save_show/help/propagate/defaults) + `test_dendrogram.py` +7 (importable, linkage valid, guard n1, leaf order, 12-block quasi-diagonal, n1/n2/no-crash, pipeline E2E 8º PNG); **validación**: `./init.sh` 230 passed (216+14), `All checks passed!`, `pyright 0 errors`, `compileall OK`, `openspec validate --all` 13/13 (package-interface + runtime-diagnostics), 2 iteraciones revisión subagentes (5 HIGH + 3 MEDIUM corregidos: mismatch guard, legacy argv warning, leaf recursion, width cap, WAYLAND); `README` 7→8, `CHANGELOG` Added, `tasks.md` 9/9.

### What's Done (Fase D — Cobertura)

- [x] **feat-040** (2026-09-05): higiene dev + gate 85% branch — `pyproject.toml` mover `pytest>=9.0.3` de `[project.dependencies]` a `[dependency-groups].dev` + `pytest-cov>=6.0` (`coverage 7.16.0`), `[tool.coverage.run]` `branch = true` + `source = ["portfolio_engine"]` + `omit tests`, `[tool.coverage.report]` `fail_under = 85` + `addopts` `--cov=portfolio_engine --cov-report=term-missing --cov-report=html --cov-report=xml --cov-branch --cov-fail-under=85`; `Makefile:test` gate explícito `-q --cov ... --cov-branch --cov-fail-under=85` + `test-no-cov` escape hatch + `clean` `htmlcov/.coverage/coverage.xml`; `.github/workflows/ci.yml` `Test suite with coverage gate` + `Publish coverage` + `upload-artifact htmlcov` en matrix 3.11-3.13 con `uv sync --frozen`; `.gitignore` `coverage.xml`; baseline medido 2026-09-05: `TOTAL 1509 stmts 85.37% branch / 87% line (230 tests)`; `uv lock --check` OK; `make test` gate activo (85 pass / 90 fail); `openspec` 14/14 (project-packaging + quality-gates + verification-harness).

### What's In Progress

_Ningún feature abierto: **feat-045 done local** (rama `feat/allocation-diagnostics`, validación pre-push aplicada, sin push). Siguiente tras su merge: feat-046._

### What's Done (post-hito)

- [x] **feat-050** ensamblador keystone (ciclo completo en rama `feat/report-assembler-integration`): 2 subagentes pre-análisis + OpenSpec valid (+1 ADDED, 4 scenarios, 10 decisiones) + TDD 8→10 tests (naming-trap, envelope, fakes) + `build_technical_report` + emisión fail-safe punto único (N=0 incluido; main intacto) + CLI + gitignore/clean + exports; bucle con APPROVE final; suite 358 passed, TOTAL 88.92%; core/portfolio/data/validation/viz diff cero
- [x] **feat-049** sección walk-forward (ciclo completo en rama `feat/walkforward-json-section`): 2 subagentes pre-análisis + OpenSpec valid (+1 ADDED, 7 scenarios) + TDD 11→13 tests (evaluate real) + `walk_forward_section` append-only (agregados verbatim, deriva con broken_pairs; walk_forward.py intacto); bucle con APPROVE final; suite 348 passed, TOTAL 88.19%; motor diff 0; PR #71 squash-mergeado + change archivado (PR #72)
- [x] **feat-048** salud del árbol (ciclo completo en rama `feat/tree-health-depth-chaining`): 3 subagentes + hallazgo propio (piso 0.5 de ≥1-hoja → usuario decidió acreción exacta) + OpenSpec valid (+1 ADDED, 8 scenarios) + TDD 10→13 tests (n==2 rate 0.0) + `tree_diagnostics` append-only (hrp.py intacto); bucle con APPROVE final; suite 335 passed, TOTAL 88.01%; motor diff 0; PR #68 squash-mergeado + change archivado (PR #69)
- [x] **feat-046** riesgo in-sample (ciclo completo en rama `feat/insample-tail-drawdown`): 4 subagentes pre-análisis + OpenSpec change valid (+1 ADDED, 7 scenarios, 11 decisiones) + TDD 14→26 tests + 3 funciones puras (serie/tail/drawdown, seams públicos); bucle validación con APPROVE final; suite 322 passed, TOTAL 87.61%; motor diff 0; PR #65 squash-mergeado a develop + change archivado (PR #66)
- [x] **fix-045a** hardening post-cierre feat-045 (rama `fix/allocation-diagnostics-hardening`, orden del usuario, TODO en la rama): análisis externo verificable (HHI/Choueifaty/Dykstra/JSON-null) + análisis profundo (6/6 scenarios, 8 MINOR) → docstring contratos + guard duplicados + guard varianza pre-sqrt + colapso asarray + 10 tests; bucle verificación (APPROVE → CONDITIONAL → fixes → APPROVE final); suite 296 passed, TOTAL 86.94%; motor diff 0; PR #63 squash-mergeado a develop (37385ac), CI verde
- [x] **feat-045** diagnóstico de asignación (flujo OpenSpec en rama): `allocation_diagnostics` con HHI/N_eff, DR/RC+spread (rebanado feat-028) y telemetría Dykstra (recompute determinista + raw_weights); validación pre-push: MAJOR-1/2 corregidos (guard forma + pines engine round-trip y n=3) + 7 MINOR; suite 286 passed, TOTAL 86.91%; motor diff 0
- [x] **feat-044** motivos de exclusión + distancias (flujo OpenSpec en rama): `compute_filter_rejections` con orden de guardias de `selection.py:47-63`, slugs idénticos, distancias firmadas; TDD rojo 10→verde 10+equivalencia; suite 256 passed, TOTAL 86.20%; motor diff 0; fixture bugs cazados por el test de equivalencia (2x realineado)
- [x] **feat-043** report_json core (flujo OpenSpec completo, 4 artefactos valid): sanitizador JSON-estricto, escritor single-file, fingerprint sha256-16hex, envelope schema_version=1; TDD rojo 34 failures→verde 13 tests; suite 246 passed, cobertura TOTAL 85.60%; motor diff 0; gates cazaron ruff F841/I001 + pyright is_dataclass (2 iteraciones)

### What's Done (post-hito)

- [x] **feat-042** recalibrar thresholds (10/10 tasks): config 0.3/0.27, ADR-007 Aceptado, 233 passed, change valid; PR #53 squash-mergeado a develop (d1b7da3), change archivado 2026-09-09-feat-threshold-recalibration + spec configuration-contract sincronizada
- [x] **docs/diagnostics-catalog.md** (9 diagnósticos con file:line verificados) mergeado a develop (936dc5e)
- [x] **Pre-gates del épico JSON** (2026-09-09): 0A merge catálogo + 0B archive de feat-042 (`openspec validate --all` 12/12)

### What's Next (épico Reporte técnico JSON — feat-043..051, registrado en feature_list.json)

Orquestación completa (2 oleadas + revisión hostil con cobertura real medida): el gate es el **total combinado** de coverage.py (85.37% = (1313+339)/(1509+426); branch-only real 79.58%; slack ≈ 7 unidades) — cada feature registra el TOTAL % en su evidencia.

1. **feat-043** report_json core (sanitizador JSON-estricto, escritor single-file, fingerprint sha256, envelope `schema_version=1` ausente-tolerante; run_id derivado, uuid4 prohibido) — capability nueva `technical-report`
2. **feat-044/045/046/048/049** (paralelizables tras 043, merge serial): rejections+distancias (firma con requested_tickers+closing_prices), HHI/DR/RC+raw-vs-constrained, serie in-sample+Sortino/VaR/CVaR+maxDD/Calmar (re-align con `minimum_overlap_ratio=1.0` — contraejemplo del guard 0.9 verificado), tree health, sección WF pura (consume to_dict, nunca lo modifica)
3. **feat-050** ensamblador+integración (kwargs `report_path=None` default escribe nada; CLI pasa reports/technical-report.json; 3 fakes de test_cli.py:54,151,189 deben aceptar report_path; .gitignore reports/ + Makefile clean)
4. **feat-051** flag `--walk-forward` opt-in + docs (incluye corrección terminológica del gate en CONTRIBUTING)

Correcciones del reviewer incorporadas al tracker: feature 047 original absorbida por 046; arista 049→050 añadida; firma de 044 exige universo pedido; reason-slugs idénticos a selection.py:53-62; deuda preexistente documentada (cli.py:82, pipeline.py:252-255, reporting.py:498-507 — hits=0, fuera de scope).

## Process Deviations (transparencia)

- **feat-024 se implementó sin artifacts OpenSpec previos** (proposal/design/tasks ausentes): flujo saltado en la racha. La impl pasó gates/tests, pero viola el workflow propio. Corrección de proceso: ninguna feature posterior repite esto; verificado contra feat-025+.
- tasks.md de feat-024 perdido por rm accidental del directorio pre-archive; la evidencia vive en esta nota y en el commit.

## Blockers / Risks

- pyright baja a `basic`: strict es progresión futura (registrar como feature dedicado si se quiere formalizar).
- aviso cosmético Node20→24 en GitHub Actions (bump futuro).
- Terminología del gate corregida (PR #54): el umbral 85 compara contra el TOTAL combinado de coverage.py, no "85% branch" (historial feat-040 usa la etiqueta antigua — registro histórico, no corregido retroactivamente).

## Evidence of Completion

- feat-042: TDD rojo (`0.5 == 0.3`, `relaxed 1 == 0`) → verde · `./init.sh` exit 0 233 passed (230+3: contrato + 2 WF) cobertura 85.37% · `openspec validate` change + `--all` 13/13 · ADR-007 Aceptado · rama `feat/threshold-recalibration` sin push (veto)
- feat-041: hito CERRADO 2026-09-09 · local `./init.sh` exit 0 (230 passed, 85.37% branch, ruff/pyright verdes) · PR #51 squash-mergeado a develop (633efa6) con CI verde matriz 3.11/3.12/3.13 · tag `v0.1.0` → 633efa6 pusheado · GitHub Release publicado · `charts/` baseline 8 PNG trackeado
- feat-040: `openspec validate --all` 14/14 (project-packaging + quality-gates + verification-harness) · `./init.sh` exit 0 230 passed 85.37% branch (87% line) `TOTAL 1509 stmts` + `All checks passed!` + `pyright 0` + `compileall OK` · `make test` gate 85 pass / 90 fail · `uv lock --check` OK · branch `chore/coverage-gate`
- feat-039: `openspec validate --all` 13/13 (package-interface CLI + runtime-diagnostics dendrograma) · `./init.sh` exit 0 230 passed (216+14: 7 CLI +7 dendrograma) + `All checks passed!` + `pyright 0 errors` + `compileall OK` · branch `feat/cli-dendrogram` · revisión 2 subagentes (5 HIGH corregidos: mismatch, legacy, recursion, width, WAYLAND) + evidencia fresca 2026-09-04 · `tasks.md` 9/9 · `README` 7→8 + `CHANGELOG` Added
- feat-037: `openspec validate --specs` 12/12 (market-data-contract + configuration-contract) · guard post-DataFrame con `notna().mean()` sobre unión · `./init.sh` 203 passed · ruff/pyright/compileall verdes · revisión adversarial (2 subagentes) con 3 ALTA (ruff/pyright/chart4) corregidos
- feat-036: `openspec validate --specs` 12/12 (`quant-docs` nueva) · `grep -rn log1p` 6+ call-sites migrados · `./init.sh` 187 passed · ruff/pyright/compileall verdes · revisión adversarial (3 subagentes) con 1 ALTA (F401) corregida
- feat-031: `openspec validate --specs` 11/11 · `grep SHANL openspec/` = 0 · set de métodos en spec == enum código (6) · `./init.sh` exit 0 con 159 passed · CHANGELOG.md con formato Keep a Changelog
- feat-028..030: evidencia completa por feature en `feature_list.json:evidence` (rojo TDD → verde → init.sh fresco → spec sincronizada → PR squash)

## Decisions Made

- feat-040: `fail_under = 85` branch (87 line) baseline 2026-09-05: `85.37% branch` deja 0.37% slack branch, 2% slack line; `branch = true` captura else no testeados; `pytest` solo en dev (PEP 735 flat dev, `uv sync --frozen` default-groups), gate cuádruple (`pyproject addopts` + `tool.coverage.report` + `Makefile` + `CI`) documentado como single source `85` en `pyproject.toml:65`.
- feat-039: `BooleanOptionalAction` para `--save/--no-save` y `--show/--no-show` (defaults `True`/`False` reproduciendo `pipeline.py:193`); `--linkage/--linkage-method` alias mismo `dest` (compat tracker + best-practice); `build_hrp_linkage` single-source distancia/pasarela (evita drift), `_leaf_order` iterativo (sin recursion limit 1e3), width capped 40, `WAYLAND_DISPLAY` headless, tickers/cov mismatch guard en dendrograma.
- feat-037: guard post-DataFrame (B) con `notna().mean()` sobre unión; `minimum_overlap_ratio` en config (0.9) + param en función con default idéntico; chart 4 full-universe alineado con mismo guard (absorbe blocker progress.md:45)
- feat-036: híbrida A+B sin ciclo — `config.risk_free_rate_log` usa `math.log1p` directo; helper `risk_free_log_rate` para float-only sites; duplicación intencional documentada en `design.md:D1`; addendum ADR 003 fechado 2026-09-01 (no supersede) cuantifica `n=5,max=0.30`
- feat-031 declarado `skip_specs: true` (cambio puramente documental: las specs se corrigen para reflejar comportamiento YA implementado — precedente feat-025)
- feat-041 declarado sin change OpenSpec por el mismo precedente (mecánica de release docs-only); CHANGELOG `[0.1.0] - 2026-09-09` con links compare/tag; `develop → main` pendiente de indicación del usuario
- CHANGELOG `[0.1.0] - 2026-09-09` publicado por feat-041 (contenido `Unreleased` movido + `Unreleased` fresco + links); placeholder previo eliminado
- `project-packaging` actualizado a 3.11-3.13 en feat-031 para que feat-032 solo implemente lo que la spec ya declara
