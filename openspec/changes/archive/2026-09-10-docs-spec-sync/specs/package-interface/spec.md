# Spec delta: package-interface (feat-053, MODIFIED + ADDED)

## MODIFIED Requirements

### Requirement: Entrypoint de consola estable

El proyecto SHALL exponer `portfolio-run` como console-script apuntando a una función `main` dentro del paquete que ejecuta el análisis estándar y SHALL honrar todos los flags (`--universe`, `--method`, `--covariance-estimator`, `--linkage`, `--save`, `--show`, `--refresh-cache`, `--walk-forward`) sin requerir directorio particular; el wrapper `scripts/assets-investment.py` SHALL permanecer delegante.

#### Scenario: invocación desde CLI

- **WHEN** se ejecuta `uv run portfolio-run` en un entorno con acceso a datos
- **THEN** corre el pipeline estándar generando reporte y figuras, sin requerir directorio de trabajo particular ni variables extra

### Requirement: Legado delega, no duplica

El script histórico bajo `scripts/` SHALL ser un wrapper que solo importa e invoca `portfolio_engine.cli.main()` (el logging lo configura el CLI) y SHALL NOT contener manipulación manual de `sys.path` ni configuración de logging.

#### Scenario: script sigue operativo

- **WHEN** se inspecciona `scripts/assets-investment.py`
- **THEN** su cuerpo se limita a importar `main` e invocarlo bajo `if __name__ == "__main__"`

### Requirement: Contrato CLI completo

`portfolio_engine.cli._build_parser` SHALL exponer flags `--universe` (PATH, default `config/universe.yaml`), `--method` (choices `WEIGHT_ALLOCATION_METHODS`, default `hrp`, dest `weight_allocation_method`), `--covariance-estimator` (choices `COVARIANCE_ESTIMATORS`, default `sample`), `--linkage` + alias `--linkage-method` (choices `LINKAGE_METHODS`, default `single`, dest `linkage_method`), `--save`/`--no-save` (BooleanOptionalAction, default `True`), `--show`/`--no-show` (BooleanOptionalAction, default `False`), `--refresh-cache` (store_true, default `False`), `--walk-forward` (store_true, default `False`). Cada enum invalido SHALL fallar en parsing con `SystemExit` 2 listando `choices`. `main(argv, universe_path)` SHALL propagar parsed values a `PortfolioConfig(...)` y a `generate_complete_analysis_report(save_plots=args.save, show_plots=args.show, provider=YFinanceProvider(cache_dir=Path("data/cache"), refresh_cache=args.refresh_cache), run_walk_forward=args.walk_forward)` preservando la rama legada `universe_path` que bypassa parsing con `refresh=False` y `run_walk_forward=False`.

#### Scenario: flag propagation con provider monkeypatcheado

- **WHEN** `cli.main(argv=["--method","risk_parity","--covariance-estimator","ledoit_wolf","--linkage","ward","--no-save","--show"])` corre con `generate_complete_analysis_report` y `load_universe` monkeypatcheados (captura `config`/`provider`/`save_plots`/`show_plots`)
- **THEN** `captured["config"].weight_allocation_method=="risk_parity"` y `captured["config"].covariance_estimator=="ledoit_wolf"` y `captured["config"].linkage_method=="ward"` y `captured["save_plots"] is False` y `captured["show_plots"] is True` y `captured["provider"].refresh_cache is False` (por defecto) ; con `--refresh-cache` el provider refleja `True`

#### Scenario: --help documenta todos los flags

- **WHEN** se obtiene `parser.format_help()` o se invoca con `--help`
- **THEN** el texto contiene `--universe` y `--method` y `--covariance-estimator` y `--linkage` y `--save` y `--show` y `--refresh-cache` y `--walk-forward`

#### Scenario: enum invalido rechazado en parsing

- **WHEN** se parsea `--method risk_parit` (typo) o `--linkage centroid`
- **THEN** `SystemExit` 2 y mensaje menciona choices permitidos

#### Scenario: legada universe_path preservada

- **WHEN** se invoca `main(universe_path="config/universe.yaml")`
- **THEN** no se parsea `argv`, el provider tiene `refresh_cache==False`, el walk-forward queda apagado y el universo cargado es el del path legado

## ADDED Requirements

### Requirement: Flag --walk-forward opt-in

`_build_parser` SHALL exponer `--walk-forward` (store_true, default `False`) con help que documente el propósito OOS; `main` SHALL reenviarlo como `run_walk_forward` a `generate_complete_analysis_report`.

#### Scenario: opt-in propaga

- **WHEN** `cli.main(argv=["--walk-forward"])` corre con `generate_complete_analysis_report` monkeypatcheado
- **THEN** el reporte recibe `run_walk_forward=True`
