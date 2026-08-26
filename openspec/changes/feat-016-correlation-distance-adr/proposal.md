# Proposal: feat-016-correlation-distance-adr

## Why

La distancia de clustering `d = 1-|corr|` (metrics.py) colapsa el signo: un activo con correlación -0.9 (diversificador ideal) queda a distancia 0.1 de uno con +0.9 y se fusionan en el mismo cluster — lo contrario a la tesis de diversificación del proyecto (auditoría M2). La decisión es PREVIA obligatoria a feat-018 (HRP real consume la métrica): cambiarla después significaría migrar dos veces.

## What Changes

- **ADR 002** (`docs/adr/002-correlation-distance-choice.md`): decisión firmada como default (`sqrt(0.5·(1-corr))`), abs conservada como opción; racional contra el colapso de signo
- `core/metrics.py`: kernel `compute_correlation_distance_matrix(matrix, metric_code)` numba-compatible con flag entero; wrapper público acepta `"signed"|"abs"`
- `core/config.py`: campo `distance_metric: str = "signed"` validado contra enum público
- `portfolio/selection.py`: umbral convertido POR MÉTRICA para preservar semántica del usuario ("fusionar si corr > threshold"): signed ⇒ `sqrt(0.5(1-t))`; abs ⇒ `1-t`
- `tests/test_config.py` +`tests/test_metrics.py`: conversión de umbrales, distancias extremas por signo, contraste de clustering firmado-vs-abs
- **Cambio de comportamiento documentado**: default firmado altera resultados de clustering respecto al histórico — aceptado pre-1.0, single-change-before-HRP

## Capabilities

### Modified Capabilities
- `configuration-contract`: nuevo campo validado con enum.
- `numeric-correctness`: la matriz de distancia respeta la semántica del signo elegido.

## Impact

- **Riesgo medio**: resultados de clustering cambian por diseño; cubierto por tests pin y ADR.
