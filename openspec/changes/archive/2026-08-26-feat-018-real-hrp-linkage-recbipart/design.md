# Design: feat-018-real-hrp-linkage-recbipart

## Context

Todas las dependencias del DAG resueltas: matrices alineadas y finitas, config frozen con distance_metric firmado default. La distancia 1-|corr| greedy muere reemplazada en la ruta HRP; los métodos legacy siguen operativos para comparaciones.

## Goals / Non-Goals

**Goals:** HRP canónico 3 pasos; ruta end-to-end propia; determinismo; expectativas analíticas exactas.
**Non-Goals:** HERC (diferida), linkage paramétrico (decision-log), seriation avanzada, remotion del path legacy.

## Decisions

### D1 — scipy linkage 'single', implementación propia de quasi-diag + bisección
linkage de scipy es estándar probado. Quasi-diag/bisección son ~40 líneas recursivas claras (docstring advierte profundidad); riskfolio-lib queda descartado por weight/learning-curve (decision-log) con puerta abierta si universos >400 exigen perf.
### D2 — Covarianza sobre universo filtrado completo
El reporte necesita optimal_portfolio={ticker: metrics} para todos los tickers hrp-escogidos: asignación da pesos a TODOS, así que optimal_portfolio = dict(filtered_metrics) completo (reportes/pipeline compatibles sin cambios).
### D3 — Default flip a "hrp"
Patrón single-flip ya validado en feat-016. README tabla actualizada; legacy methods preservados.
### D4 — Constraints feat-014 al final
HRP respeta jerarquía pero puede violar mandato bounds → mismo punto único de normalización Dykstra que el resto. Warning-only no: verificación dura heredada.
### D5 — Recursión vs iterativo
Recursión legible; docstring nota límite práctico ~1e3 activos (profundidad cadena). Universo objetivo decenas-centenas.

## Risks / Trade-offs

- Composición de carteras cambia vs risk_parity legacy — motivo central del change
- Bisección asume cov quasi-diagonal aproximada tras seriation — estándar del método
