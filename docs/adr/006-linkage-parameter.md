# ADR 006 — Método de linkage parametrizable en HRP

**Estado:** Aceptado · **Fecha:** 2026-08-28 · **Feature:** feat-034 (C1-extra, Fase B del DAG v0.1.0)

## Contexto

`calculate_hrp_weights` usa `linkage(method="single")` hardcodeado — fiel al paper original (De Prado 2016), pero el single-linkage sufre *chaining*: cadenas largas que agrupan activos no relacionados (documentado por skfolio, pyhrp y la literatura 2025-26). skfolio fija Ward como default por estabilidad; pyhrp documenta la comparativa; Papenbrock resume pros/contras por método. El DAG v0.1.0 difería "HERC/linkage paramétrico" explícitamente (decision-log feat-025); esta feature cierra la parte de linkage.

## Opciones evaluadas

1. **Parametrizar `{single, ward, average}` con default `single`** ✅ — expone el método sin cambiar comportamiento (patrón single-flip del repo); De Prado sigue siendo el default de referencia y la red feat-021 pina snapshots numéricos.
2. **Flip inmediato a Ward como default** — más estable en la literatura, pero rompe el contrato "sin cambio silencioso" y los snapshots sin evidencia walk-forward propia; queda como candidata para el flip de v0.2.0 junto al estimador de covarianza (ADR 005).
3. **No exponer** — congela el chaining conocido como única opción.

## Decisión

- Nuevo campo validado `PortfolioConfig.linkage_method ∈ {single, ward, average}` (default `single`).
- `calculate_hrp_weights(covariance_matrix, linkage_method="single")` valida y propaga a `scipy.cluster.hierarchy.linkage`; default retrocompatible.
- `pipeline` (ruta HRP end-to-end) y `walk_forward_evaluate` pasan el valor desde config.
- Flip de default (candidato: `ward`) diferido a v0.2.0, evaluado junto con el flip de `covariance_estimator` (ADR 005) sobre evidencia walk-forward conjunta.

## Consecuencias

- Default `single`: pesos idénticos a los vigentes (snapshot feat-021 intacto).
- `ward`/`average`: árbol más balanceado ante universos con bloques de correlación; efectos en pesos solo bajo petición explícita.
- Nota metodológica: HRP usa el orden de hojas, no la altura del árbol — la literatura coincide en que la asignación es relativamente estable entre linkages; la exposición permite estudiarlo en el propio walk-forward.

## Detalle de implementación relevante

La validación del enum ocurre en `__post_init__` (config) y defensivamente en `calculate_hrp_weights` (fail loud, patrón feat-013). El resto del algoritmo (quasi-diagonalización por orden de hojas y bisección por varianza inversa) no cambia.
