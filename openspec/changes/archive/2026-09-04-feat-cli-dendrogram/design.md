# Design: feat-039 CLI args and dendrogram

## Context

El pipeline post `feat-038` es estable (216 passed) pero operativo vía `PortfolioConfig()` defaults. La superficie CLI debe exponer los 3 parámetros metodológicos clave (`method`, `covariance_estimator`, `linkage_method`) ya validados en `config.py:11-33` y los 2 flags de render (`save`/`show`) para que `generate_complete_analysis_report` sea driveable desde `uv run portfolio-run --help` sin editar código. El dendrograma es requirement natural: De Prado 2016 y skfolio lo muestran por defecto; hoy `hrp.py:90-96` calcula `linkage` pero no lo expone, y `reporting.py:70-87` ya resuelve headless `Agg`.

Background: `feat-006` difirió argparse; `ADR 005/006` fijaron defaults sample/single; `feat-038` añadió `_build_parser` pure factory + `main(argv=None)` test injection.

## Goals / Non-Goals

**Goals:**
- CLI flags con `choices` autovalidados y `dest` mapeado a campos `PortfolioConfig` (single source de validación sigue en `__post_init__`, argparse da error temprano amigable).
- Dendrograma headless que reutiliza exactamente la misma distancia firmada y `linkage_method` (geometría idéntica a pesos HRP), con hojas en orden quasi-diagonal verificable.
- Pipeline genera 8 charts sin romper headless CI ni `n=1/2` edge cases.

**Non-Goals:**
- No nuevo ADR (no decisión metodológica, solo exposición).
- No flip de defaults (siguen `hrp`/`sample`/`single`).
- No HERC, no vol-target, no pyright strict (v0.2.0).

## Decisions

### D1: Flag naming y `dest` mapping
- `--method` → `weight_allocation_method` (corto, spec tracker dice `--method`), `choices=WEIGHT_ALLOCATION_METHODS`, `default="hrp"`. Se añade alias `--weight-allocation-method` opcional? No para v0.1.0: solo `--method` para satisfacer tracker literal; si se añade alias, usar `parser.add_argument("--method", "--weight-allocation-method", dest=...)` — pero priorizar simplicidad: solo `--method` documentado, test valida ese.
- `--covariance-estimator` → `covariance_estimator`, `choices=COVARIANCE_ESTIMATORS`, `default="sample"`.
- `--linkage` + `--linkage-method` → `linkage_method`, `choices=LINKAGE_METHODS`, `default="single"`. Se registran ambos flags apuntando al mismo `dest` para compatibilidad tracker vs recomendación best-practice (`--linkage-method` canónico). argparse permite `add_argument("--linkage", "--linkage-method", dest="linkage_method", ...)`.
- `--universe` keep `type=str`, `metavar="PATH"`.
- `--refresh-cache` keep `store_true` `False`.
- `--save`/`--no-save` y `--show`/`--no-show` vía `action=argparse.BooleanOptionalAction` con defaults `True`/`False` reproduciendo `pipeline.py:193` actuales (`save_plots=True, show_plots=False`). Esto introduce `--no-save`/`--no-show` visibles en --help — intencionado, profesional 2025-26 pattern.

Alternativa `store_true` solo descartada: no permitiría CLI desactivar save sin env var; `BooleanOptionalAction` es 3.9+ disponible en `requires-python>=3.11`.

### D2: Dendrogram seam single-source
Extraer en `hrp.py`:
```python
def _correlations_from_cov(cov): ... # ya existe hrp:133
def build_hrp_linkage(covariance_matrix, linkage_method="single") -> np.ndarray:
    # valida linkage_method, cov square finite symmetric diag>0 (mismos guards que calculate_hrp_weights:64-76)
    # distancia = sqrt(max(0.5*(1 - _correlations_from_cov(cov)), 0)), fill_diagonal 0
    # condensed = squareform(distance, checks=False)
    # return linkage(condensed, method=linkage_method)
```
`calculate_hrp_weights` llama a `build_hrp_linkage` y luego `_leaf_order`. `viz/reporting.py:plot_hrp_dendrogram` importa `build_hrp_linkage` — una sola construcción de distancia/linkage. Evita drift si fórmula cambia.

Alternativa recomputar distancia en viz descartada (duplicación).

### D3: `plot_hrp_dendrogram` signature y headless
```python
def plot_hrp_dendrogram(
    covariance_matrix: np.ndarray,
    linkage_method: str,
    tickers: list[str],
    save_path: str | None = None,
    show_plot: bool = True,
) -> None:
```
- Guard `n = cov.shape[0]`: `n==0` warning + return; `n==1` bar trivial + _finalize_plot; `n==2` linkage degenerado `[[0,1,distance[0,1],2]]` o skip (elegir skip con warning + _finalize_plot para no mentir).
- `figsize=(max(12, int(0.6*n)+8), 6)` escala con n (12 large-cap → ~15, 25 → 20+), `leaf_rotation=90`, `leaf_font_size=max(8, 10 - n*0.08)`.
- `linkage_matrix = build_hrp_linkage(cov, linkage_method)`; `scipy.cluster.hierarchy.dendrogram(linkage_matrix, labels=tickers, leaf_rotation=90, color_threshold=None)`; `plt.title("HRP Dendrogram ({method})")`, `tight_layout`, `_finalize_plot`.
- Orden verificable: `dendro = dendrogram(..., no_plot=True); assert dendro["leaves"] == _leaf_order(Z,n) == leaves_list(Z)`.

Ubicación `viz/reporting.py` para respetar `app/pipeline SHALL NOT import matplotlib` (`package-interface` spec). Pipeline invoca `plot_hrp_dendrogram` con `try: plot_hrp_dendrogram(covariance_matrix, config.linkage_method, list(filtered_metrics.keys()), f"charts/{CHART_FILENAMES['hrp_dendrogram']}" if save_plots else None, show_plot=show_plots) except Exception as exc: logger.warning("Dendrogram skipped: %s", exc)` — nunca rompe reporte.

### D4: Pipeline 8 charts
`CHART_FILENAMES["hrp_dendrogram"] = "hrp_dendrogram.png"` (nombre descriptivo corto). Log `Report generated: plots=8`. `generate_complete_analysis_report` sigue retornando 4-tuple (no ampliar por compat tests). `main` no cambia firma.

### D5: Exports y __all__
`portfolio_engine/__init__.py` añade `from .portfolio.hrp import build_hrp_linkage` y `from .viz.reporting import plot_hrp_dendrogram`, ambos a `__all__`.

## Risks / Trade-offs

- `ward` sobre distancia correlación (no euclídea) puede emitir `ClusterWarning`/`ValueError` si scipy valida — `build_hrp_linkage` no oculta warning, test con ward usa `average`/`single` para estabilidad y tolera warning con `pytest.warns` si aparece.
- `BooleanOptionalAction` expone `--no-*` flags que no estaban en tracker literal `--save/--show` — se acepta como mejora estandar 2025; tests verifican que `--help` contiene `--save` y `--show`.
- Tamaño PNG para n=12 con Agg es ~100KB; CI artifact no se publica (charts ignorado).

## Migration

Backward compat: `main(universe_path=...)` legada sigue bypassando parsing (spec `test_cli_refresh_cache_propagates_to_provider` valida). `PortfolioConfig()` default intacto. `CHART_FILENAMES` adición no rompe callers que indexan claves existentes.

## Open Questions

- ¿Exponer también `--distance-metric` como flag? No en feat-039 tracker — diferido v0.2.0.
