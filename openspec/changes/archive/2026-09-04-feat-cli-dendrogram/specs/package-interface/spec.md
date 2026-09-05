## ADDED Requirements

### Requirement: Contrato CLI completo

`portfolio_engine.cli._build_parser` SHALL exponer flags `--universe` (PATH, default `config/universe.yaml`), `--method` (choices `WEIGHT_ALLOCATION_METHODS`, default `hrp`, dest `weight_allocation_method`), `--covariance-estimator` (choices `COVARIANCE_ESTIMATORS`, default `sample`), `--linkage` + alias `--linkage-method` (choices `LINKAGE_METHODS`, default `single`, dest `linkage_method`), `--save`/`--no-save` (BooleanOptionalAction, default `True`), `--show`/`--no-show` (BooleanOptionalAction, default `False`), `--refresh-cache` (store_true, default `False`). Cada enum invalido SHALL fallar en parsing con `SystemExit` 2 listando `choices`. `main(argv, universe_path)` SHALL propagar parsed values a `PortfolioConfig(...)` y a `generate_complete_analysis_report(save_plots=args.save, show_plots=args.show, provider=YFinanceProvider(cache_dir=Path("data/cache"), refresh_cache=args.refresh_cache))` preservando la rama legada `universe_path` que bypassa parsing con `refresh=False`.

#### Scenario: flag propagation con provider monkeypatcheado
- **WHEN** `cli.main(argv=["--method","risk_parity","--covariance-estimator","ledoit_wolf","--linkage","ward","--no-save","--show"])` corre con `generate_complete_analysis_report` y `load_universe` monkeypatcheados (captura `config`/`provider`/`save_plots`/`show_plots`)
- **THEN** `captured["config"].weight_allocation_method=="risk_parity"` y `captured["config"].covariance_estimator=="ledoit_wolf"` y `captured["config"].linkage_method=="ward"` y `captured["save_plots"] is False` y `captured["show_plots"] is True` y `captured["provider"].refresh_cache is False` (por defecto) ; con `--refresh-cache` el provider refleja `True`

#### Scenario: --help documenta todos los flags
- **WHEN** se obtiene `parser.format_help()` o se invoca con `--help`
- **THEN** el texto contiene `--universe` y `--method` y `--covariance-estimator` y `--linkage` y `--save` y `--show` y `--refresh-cache`

#### Scenario: enum invalido rechazado en parsing
- **WHEN** se parsea `--method risk_parit` (typo) o `--linkage centroid`
- **THEN** `SystemExit` 2 y mensaje menciona choices permitidos

#### Scenario: legada universe_path preservada
- **WHEN** se invoca `main(universe_path="config/universe.yaml")`
- **THEN** no se parsea `argv`, el provider tiene `refresh_cache==False` y el universo cargado es el del path legado

### Requirement: Export de dendrograma en superficie del paquete

`portfolio_engine` SHALL exportar `plot_hrp_dendrogram` (`viz/reporting.py`) y `build_hrp_linkage` (`portfolio/hrp.py`) vía `__init__.py` y `__all__`, importables sin side-effect headless.

#### Scenario: importable sin path hacks
- **WHEN** `from portfolio_engine import plot_hrp_dendrogram, build_hrp_linkage`
- **THEN** import succeed sin tocar red ni requerir `MPLBACKEND`

## MODIFIED Requirements

### Requirement: Entrypoint de consola estable
El proyecto SHALL exponer `portfolio-run` como console-script apuntando a una función `main` dentro del paquete que ejecuta el análisis estándar y SHALL honrar todos los flags (`--method`, `--covariance-estimator`, `--linkage`, `--save`, `--show`, `--refresh-cache`) sin requerir directorio particular; el wrapper `scripts/assets-investment.py` SHALL permanecer delegante.

#### Scenario: invocación desde CLI
- **WHEN** se ejecuta `uv run portfolio-run` en un entorno con acceso a datos
- **THEN** corre el pipeline estándar generando reporte y figuras, sin requerir directorio de trabajo particular ni variables extra
