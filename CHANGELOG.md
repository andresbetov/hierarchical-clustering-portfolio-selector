# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Reporte técnico JSON machine-readable (`reports/technical-report.json`, `schema_version: 1`, fingerprint determinista): núcleo estricto + envelope (feat-043), exclusiones con distancias (feat-044), asignación HHI/DR/RC + telemetría Dykstra (feat-045), riesgo in-sample serie/cola/drawdown (feat-046), salud del árbol depth-chaining (feat-048), sección walk-forward + deriva L1 (feat-049), ensamblador keystone con emisión fail-safe en el pipeline/CLI (feat-050) y opt-in `--walk-forward` (feat-051).
- README orientado a showcase: reescritura en inglés + espejo `README.es.md`, tabla CLI, diagrama de flujo, resultados in-sample/out-of-sample con snapshot de la corrida en `docs/results/technical-report-2026-09-10.json`, sección del harness de agentes y referencias metodológicas.

### Changed

- feat-042: recalibración de thresholds del filtro (ADR 007) — `minimum_sharpe_threshold` 0.5→0.3, `maximum_volatility_threshold` 0.25→0.27; evidencia walk-forward (única configuración donde HRP bate a 1/N en mediana OOS); revierte en 2 líneas.

### Fixed

- Gráfica 7 (resumen de cartera): la volatilidad `sqrt(wᵀΣw)` SHALL anualizarse con `trading_days_per_year` antes de calcular el Sharpe. La covarianza del pipeline es diaria y los retornos anualizados, así que el Sharpe reportado estaba inflado ~√252 (en la corrida 2026-09-10: 14.84 con vol diaria vs 0.94 anualizado; la gráfica commiteada anterior mostraba 14.48 en otra corrida); `test_reporting_sharpe.py` alineado al contrato de unidades + 2 regresiones (`test_daily_covariance_is_annualized`, `test_trading_days_parameter_controls_annualization`).

## [0.1.0] - 2026-09-09

Primera versión estable y correcta del pipeline HRP: ingesta batch con caché, filtros de calidad, clustering con distancia firmada, asignación HRP con constraints verificados, 8 gráficas de diagnóstico y validación walk-forward out-of-sample.

### Added

- DAG v0.1.0 registrado en `feature_list.json` (feat-028..feat-041) con dependencias explícitas hacia CP1/CP2/CP3 (chore(project): register v0.1.0 DAG).
- feat-032: dependencia `scikit-learn>=1.8` (consumida por el estimador de covarianza de feat-033/ADR 005).
- feat-033: `covariance_estimator ∈ {sample, ledoit_wolf, oas}` (ADR 005) — seam `estimate_covariance` consumida por el pipeline y el walk-forward; default `sample` (sin cambio silencioso), shrinkage con paridad sklearn a 1e-12; flip de default a `ledoit_wolf` diferido a v0.2.0 con evidencia walk-forward.
- feat-034: `linkage_method ∈ {single, ward, average}` (ADR 006) — propagado a `scipy.cluster.hierarchy.linkage` desde config; default `single` (De Prado, snapshot-compatible); flip a `ward` candidato para v0.2.0.
- feat-035: walk-forward con paridad productiva — filtros Sharpe/vol de producción aplicados por fold de train (universo ex-ante), benchmarks ex-ante `equal` (1/N) e `ivp` (inverse-volatility) sobre el mismo universo y los mismos retornos OOS, 6 medianas nuevas en `to_dict()`; guard NaN-blind corregido (folds con riesgo muestral degenerado/NaN quedan inválidos, nunca válidos-con-NaN); disciplina temporal documentada (embargo 5d dentro de la práctica 5-20d, purga implícita 1d).
- feat-037: guard de solapamiento en alineación — `minimum_overlap_ratio=0.9` (config validado `(0,1]`), exclusión con warning nombrado (ticker + coverage) contra el span común, `1.0` bit-a-bit idéntico, `0` supervivientes `ValueError`; chart 4 full-universe alineado con mismo guard.
- feat-038: caché parquet operativo — `YFinanceProvider(cache_dir, refresh_cache, use_cache)` con key determinista `sha256(sorted(upper(tickers))+start+end+trading_days+v1)` (16 hex), escritura atómica `mkstemp+snappy+os.replace`, degradación graceful (`pyarrow` ausente/corrupción `OSError`/`ArrowInvalid` → `warning+unlink+fallback`); `data/cache/*.parquet` en `.gitignore` + `.gitkeep`; CLI `--refresh-cache`/`--universe` con `_build_parser()`; `generate_complete_analysis_report(provider=)` forward; CI permanece offline (default `cache_dir=None`).
- feat-039: CLI operativo completo — `portfolio_run --method {equal,inverse_volatility,risk_parity,max_sharpe,min_variance,hrp}` (default `hrp`), `--covariance-estimator {sample,ledoit_wolf,oas}` (default `sample`), `--linkage/--linkage-method {single,ward,average}` (default `single`), `--save/--no-save` (default `True`), `--show/--no-show` (default `False`) vía `argparse.BooleanOptionalAction`; propagados a `PortfolioConfig` y `generate_complete_analysis_report(save_plots, show_plots)` con `legada universe_path` preservada; 8º gráfico `hrp_dendrogram.png` vía `plot_hrp_dendrogram` sobre `build_hrp_linkage` (distancia firmada `sqrt(0.5*(1-corr))`, `scipy.cluster.hierarchy.dendrogram`, orden quasi-diagonal `leaves_list == _leaf_order`, headless `Agg` + `n=1/2` guard).
- feat-040: gate de cobertura 85% branch (87% línea) — `pytest` movido de `[project].dependencies` a `[dependency-groups].dev` + `pytest-cov>=6.0` (`coverage 7.16.0`), `[tool.coverage.run]` `branch = true` + `source = ["portfolio_engine"]`, `[tool.coverage.report]` `fail_under = 85` + `addopts` `--cov=portfolio_engine --cov-branch --cov-fail-under=85` con reportes `term-missing/html/xml`; `Makefile:test` gate explícito + `test-no-cov` escape hatch; `ci.yml` publica `coverage` y artifact `htmlcov` en matrix 3.11-3.13; baseline medido 2026-09-05: `TOTAL 1509 stmts 85.37% branch / 87% line (230 tests)`; `.gitignore` `coverage.xml`.

### Changed

- feat-031: specs merged sincronizadas con el código (`hrp` en el set de métodos de `configuration-contract`, doble negación corregida en `numeric-correctness`, rango de Python 3.11-3.13 en `project-packaging`); CHANGELOG inicial; `progress.md` consolidado.
- feat-036: coherencia logarítmica del Sharpe — **BREAKING si `risk_free_rate ≠ 0`**: exceso `return_log − ln(1+rf)` vía `math.log1p` en los 6 call-sites (`core/metrics`, `data/data_fetch` vía helper, `portfolio/allocation:max_sharpe`, `viz/reporting` resumen + línea visual, `validation/walk_forward` train y OOS) y propiedad `PortfolioConfig.risk_free_rate_log` (single source); ADR 003 Addendum 2026-09-01 (Dykstra post-hoc euclídea vs varianza jerárquica).

### Removed

- feat-032: soporte de Python 3.10 (EOL 2026-10-31; SPEC 0) — **BREAKING**: `requires-python` sube a `>=3.11` y la matriz CI pasa a 3.11/3.12/3.13.

### Fixed

- feat-036: pinnings numéricos migrados a `(ret - log1p(rf))/vol` con `rf=0` invariante; `walk_forward._oos_metrics` unificado a `calculate_sharpe_ratio` + `VOL_FLOOR_EPS`.
- feat-028: crash en la ruta legacy del reporte (métodos ≠ `hrp` con pruning M<N recibían la covarianza N×N sin rebanar; ahora el pipeline entrega la covarianza rebanada al portfolio seleccionado) — PR #32.
- feat-029: el walk-forward omitía el retorno del primer día de la ventana de test (`np.roll` + `[1:]`); ahora cada fold produce exactamente `test_rows` retornos con el primero calculado contra el precio previo a la ventana (leak-free) — PR #33.
- feat-030: los paneles sintéticos de tests dependían del salting de `PYTHONHASHSEED` (`hash(ticker)`); ahora usan `zlib.crc32` — el mismo commit produce fixtures byte-idénticos en cualquier proceso — PR #34.

[unreleased]: https://github.com/andresbetov/hierarchical-clustering-portfolio-selector/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/andresbetov/hierarchical-clustering-portfolio-selector/releases/tag/v0.1.0
