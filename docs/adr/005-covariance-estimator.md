# ADR 005 — Estimador de covarianza parametrizable con scikit-learn

**Estado:** Aceptado · **Fecha:** 2026-08-28 · **Feature:** feat-033 (B5-extra, Fase B del DAG v0.1.0)

## Contexto

Toda la cadena jerárquica (HRP, solvers cuadráticos, risk-parity, reporte) consume la covarianza muestral (ddof=1). La literatura reciente demuestra que los métodos jerárquicos son sensibles al estimador de covarianza: Trucíos 2026 (Empirical Economics) reporta que HRC no supera a las estrategias risk-based tradicionales out-of-sample y atribuye parte de la brecha a la estimación; Palomar (12.3) y skfolio exponen estimadores shrinkage como práctica estándar. La auditoría original (B5) difería "LedoitWolf transversal formal" explícitamente — esta feature lo cierra de forma parametrizable.

## Opciones evaluadas

1. **scikit-learn como dependencia** ✅ `sklearn.covariance.LedoitWolf` / `OAS` — implementación de referencia (BSD, mantenida, testeada contra la literatura; `(1−s)·cov + s·μ·I` con shrinkage óptimo). sklearn ya entró como dependencia en feat-032 (floor Python ≥3.11). Costo: dependencia pesada ya pagada y justificada por el DAG.
2. **Implementación propia de LedoitWolf** (~40 líneas) — preserva minimalismo de deps, pero duplica código numérico delicado con riesgo de divergencias sutiles; el test de paridad contra sklearn sería obligatorio de todos modos.
3. **No parametrizar (sample siempre)** — congela la brecha metodológica conocida (Trucíos 2026).

## Decisión

- Nuevo campo validado `PortfolioConfig.covariance_estimator ∈ {sample, ledoit_wolf, oas}`.
- Seam única `estimate_covariance(returns_matrix, method)` en `core/metrics.py`, consumida por `pipeline.main` y `walk_forward_evaluate`.
- **Default `sample` en v0.1.0**: la red de caracterización feat-021 pina números exactos y el contrato "sin cambio silencioso" del repo exige un solo flip por versión; `ledoit_wolf` queda disponible y recomendado para corridas de investigación.
- **Flip del default a `ledoit_wolf` diferido a v0.2.0**, condicionado a evidencia walk-forward (benchmarks feat-035) que muestre mejora medible — siguiendo el patrón single-flip de ADR 002/003.

## Consecuencias

- `sample` produce exactamente la matriz vigente (bit a bit) — cero regresión para el comportamiento default.
- `ledoit_wolf`/`oas` devuelven matrices shrinkage: mejor condicionadas (condition number ≤ sample), con efectos en HRP/weights solo cuando el usuario lo pide.
- El walk-forward hereda el estimador de la config — comparaciones OOS entre estimadores quedan habilitadas para el estudio que decidirá el flip en v0.2.0.

## Detalle de implementación relevante

Degeneración (n_rows ≤ 1) conserva la semántica sample: matriz NaN completa, sin llamar a sklearn (que no tolera NaN/degenerados). La validación del enum ocurre en `__post_init__` igual que `weight_allocation_method` y `distance_metric`.
