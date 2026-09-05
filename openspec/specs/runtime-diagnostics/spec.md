# runtime-diagnostics Specification

## Purpose
Garantizar que la salida de diagnóstico (logs) y el ciclo de vida de figuras se comporten de forma predecible e idempotente en los tres entornos donde corre el proyecto: interactivo con display, CI sin display, y sesiones de agente/pytest que configuran handlers ajenos.

## Requirements

### Requirement: Logging aislado bajo el namespace del paquete

La configuración de logging SHALL operar sobre el logger `"portfolio_engine"` (que cubre todos sus módulos hijos) con handler dedicado y `propagate=False`, y SHALL NO configurar el logger raíz ni depender de su estado.

#### Scenario: import bajo pytest
- **WHEN** los módulos del paquete se importan dentro de una sesión pytest con caplog activo
- **THEN** no se añaden handlers al logger raíz ni se altera su comportamiento

### Requirement: Idempotencia por deduplicación

Llamar `configure_logging` más de una vez SHALL resultar en exactamente un handler propio del paquete, preservando el nivel vigente; re-invocaciones con nivel explícito distinto SHALL actualizar el nivel.

#### Scenario: doble invocación
- **WHEN** `configure_logging()` se llama dos veces seguidas
- **THEN** el logger tiene un único StreamHandler propio y ningún duplicado de output

### Requirement: Resolución de nivel param > env > default

El nivel efectivo SHALL resolverse como: parámetro explícito de `configure_logging`; si no, variable de entorno `LOG_LEVEL` (insensible a mayúsculas); si no, INFO. Un valor inválido en env SHALL advertir y caer al default sin fallar el proceso.

#### Scenario: make run-debug funcional
- **WHEN** se ejecuta con `LOG_LEVEL=DEBUG` y sin parámetro explícito
- **THEN** el logger del paquete queda a nivel DEBUG

### Requirement: Ciclo de vida de figuras seguro por entorno

Cuando no exista display disponible y el usuario no haya forzado `MPLBACKEND`, el backend SHALL resolverse a Agg antes de cualquier import de pyplot/seaborn del paquete; el cierre de figuras SHALL ser determinista: guardar+cerrar cuando no hay show, mostrar-no-bloqueante cuando lo hay.

#### Scenario: corrida en CI sin display
- **WHEN** `generate_complete_analysis_report(save_plots=True, show_plots=False)` corre sin DISPLAY
- **THEN** las figuras se guardan y cierran sin warnings interactivos y el proceso termina limpio

### Requirement: Capa app sin canvas
La orquestación (`app/pipeline.py`) SHALL NOT importar matplotlib directamente; todo acceso a pyplot (incluido `dendrogram`) vive bajo `viz/`.

#### Scenario: verificación estática del límite
- **WHEN** se inspecciona `app/pipeline.py` tras el change
- **THEN** no contiene imports de matplotlib ni llamadas a pyplot

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
