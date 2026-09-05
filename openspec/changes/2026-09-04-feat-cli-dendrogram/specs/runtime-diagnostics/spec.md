## ADDED Requirements

### Requirement: Dendrograma HRP como diagnóstico jerárquico

`portfolio_engine.viz.reporting.plot_hrp_dendrogram` SHALL renderizar el dendrograma del linkage real HRP (`scipy.cluster.hierarchy.dendrogram` sobre `build_hrp_linkage(cov, linkage_method)` reutilizando la distancia firmada `sqrt(0.5*(1-corr))`), con `labels=tickers` en orden original, `leaf_rotation=90`, `color_threshold` por defecto de scipy, `figsize` escalado por `n`, y lifecycle `_finalize_plot(save_path, show_plot)` (headless `Agg` → `savefig` dpi 300 `bbox_inches tight` luego `close`; interactivo → `show(block=False)`). SHALL estar confinado a `viz/` (`app/pipeline` SHALL NOT importar `matplotlib`/`pyplot`). Para `n<2` SHALL no invocar `linkage`/`dendrogram` y SHALL emitir `warning` nombrado, retornando tras `_finalize_plot` sin excepción.

#### Scenario: headless genera PNG con hojas quasi-diagonales
- **WHEN** `plot_hrp_dendrogram(cov_3x3, "single", ["A","B","C"], save_path=tmp_path/"dend.png", show_plot=False)` donde `cov` induce 3 bloques y `build_hrp_linkage` produce `Z`
- **THEN** el PNG existe, `st_size>1000`, y `dendrogram(Z, no_plot=True)["leaves"] == _leaf_order(Z, n) == leaves_list(Z)` (mismo orden quasi-diagonal que `calculate_hrp_weights`)

#### Scenario: n=1 y n=2 sin crash headless
- **WHEN** `plot_hrp_dendrogram(cov_1x1, "single", ["A"], save_path=..., show_plot=False)` o `cov_2x2`
- **THEN** no lanza, PNG se genera (1: barra/dummy, 2: U mínima o skip con warning) y backend permanece `agg` sin `PendingDeprecationWarning`

#### Scenario: pipeline genera 8 charts sin ValueError
- **WHEN** `generate_complete_analysis_report` corre con provider sintético (filtered n>=3) y `save_plots=True`
- **THEN** se crea `charts/hrp_dendrogram.png` además de los 7 previos, `logs plots=8`, y ninguna excepción `ValueError` por dimensiones o `n<2` detiene el reporte (dendrogram skipped con warning si aplica)

## MODIFIED Requirements

### Requirement: Capa app sin canvas
La orquestación (`app/pipeline.py`) SHALL NOT importar matplotlib directamente; todo acceso a pyplot (incluido `dendrogram`) vive bajo `viz/`.

#### Scenario: verificación estática del límite
- **WHEN** se inspecciona `app/pipeline.py` tras el change
- **THEN** no contiene imports de matplotlib ni llamadas a pyplot
