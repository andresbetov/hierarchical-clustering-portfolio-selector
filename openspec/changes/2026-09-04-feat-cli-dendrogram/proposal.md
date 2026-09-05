# Proposal: feat-039 CLI args and dendrogram

## Why

El pipeline productivo está completo (HRP signed default, shrinkage, benchmarks walk-forward, cache parquet) pero su superficie operativa sigue mínima: `cli.py:17-31` expone solo `--universe` y `--refresh-cache`, y los 7 plots de `pipeline.py:37-45` no incluyen la visualización jerárquica más natural — el dendrograma del linkage real HRP (`hrp.py:96`), hoy ausente pese a que skfolio/pyhrp lo incluyen por defecto. El `argparse` fue diferido explícitamente por `docs/decision-log-feat001.md` (feat-006 delegó en wrapper) y debe cerrarse como último feature de producto antes de cobertura y release.

Sin CLI parametrizable, cada cambio de `weight_allocation_method`/`covariance_estimator`/`linkage_method` (`config.py:11-33`) exige editar `PortfolioConfig` en código; sin dendrograma, la jerarquía queda opaca y `README.md:77` promete 7 gráficos cuando el método jerárquico merece 8.

## What Changes

- **CLI argparse completo** en `portfolio_engine/cli.py:17`: flags `--universe` (ya), `--method` (choices `WEIGHT_ALLOCATION_METHODS`, dest `weight_allocation_method`), `--covariance-estimator` (choices `COVARIANCE_ESTIMATORS`), `--linkage` + alias `--linkage-method` (choices `LINKAGE_METHODS`, dest `linkage_method`), `--save/--no-save` y `--show/--no-show` vía `argparse.BooleanOptionalAction` (defaults `True`/`False` reproduciendo `pipeline.py:193` actuales), `--refresh-cache`. Todos propagados a `PortfolioConfig` y `generate_complete_analysis_report(save_plots, show_plots, provider)`. `main(argv=None, universe_path=None)` conserva compatibilidad legada (`universe_path` bypassa parsing, `refresh=False`).
- **Dendrograma HRP** en `portfolio_engine/viz/reporting.py`: nueva `plot_hrp_dendrogram(covariance_matrix, linkage_method, tickers, save_path, show_plot)` que reutiliza exactamente la construcción de distancia firmada (`0.5*(1-corr)`, `sqrt`, `squareform`, `linkage`) vía seam `build_hrp_linkage` extraído en `portfolio_engine/portfolio/hrp.py:51` (single source, sin duplicar `hrp:90-96`). Manejo `n<2` sin linkage (warning, no crash), `n>=3` vía `scipy.cluster.hierarchy.dendrogram` con `labels=tickers`, `leaf_rotation=90`, `figsize` escalado por `n`, headless `Agg` vía `_apply_backend_guard` + `_finalize_plot`. Orden de hojas == `leaves_list(Z)` == `_leaf_order(Z,n)` (quasi-diagonal).
- **Pipeline** `portfolio_engine/app/pipeline.py:37` añade 8º entrada `hrp_dendrogram` a `CHART_FILENAMES`, invoca el plot tras `optimal_portfolio_analysis` sobre `covariance_matrix` filtrada, log `plots=8`, `try/except` si `cov` degenerada o `n<2`.
- **Exports** `portfolio_engine/__init__.py:52` expone `plot_hrp_dendrogram` y `build_hrp_linkage` en `__all__`.
- **Specs** deltas `package-interface` (CLI contract + dendrogram export) y `runtime-diagnostics` (dendrogram diagnostic + headless).

## Capabilities

### New Capabilities
- `cli-contract`: Contrato CLI completo con validación `choices` y propagación a config/reporte.
- `hrp-dendrogram`: Visualización jerárquica del linkage HRP con orden quasi-diagonal.

### Modified Capabilities
- `package-interface`: Entrypoint estable ahora documenta todos los flags y exporta dendrograma.
- `runtime-diagnostics`: Canvas confinado incluye dendrograma headless.

## Impact

- Código: `cli.py`, `portfolio/hrp.py` (seam), `viz/reporting.py` (nuevo plot), `app/pipeline.py`, `__init__.py`.
- Docs: `README.md:77-86` (tabla 8 gráficos), `CHANGELOG.md` Unreleased.
- Tests: `tests/test_cli.py` (flag parsing + propagation por flag) + nueva `tests/test_dendrogram.py` (headless PNG, leaf order, n=1/2, --help).
- Riesgos: `ward` sobre distancia correlación (no euclídea) genera warning scipy — tests toleran; `BooleanOptionalAction` introduce `--no-*` visibles en --help (intencionado).
