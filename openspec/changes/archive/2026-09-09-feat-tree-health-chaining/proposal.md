# Proposal: feat-tree-health-chaining (feat-048)

## Why

El linkage `single` (default, ADR-006) tiende al encadenamiento: pelar un activo a la vez en vez de formar grupos genuinos. Un árbol encadenado deja el orden de hojas casi arbitrario y la bisección por conteo del HRP degenera en cortes "1 vs resto" sin sentido económico — mismos activos, pesos distintos solo por el orden. El dendrograma (gráfica 8) hoy no es testeable ni agregable; profundidad máxima + tasa de acreción lo convierten en números comparables entre linkages, universos y folds, dando el criterio para el flip a `ward` diferido a v0.2.0.

## What Changes

- Función pura nueva `tree_diagnostics(covariance_matrix, linkage_method) -> dict` en `portfolio_engine/app/report_json.py` (append-only, sin tocar `hrp.py`): recomputa `Z` vía el seam público `build_hrp_linkage` (+ `_leaf_order` con import privado documentado) y devuelve `max_depth` (camino raíz→hoja más largo contando fusiones, NUNCA altura del eje Y), `chaining_rate` (fusiones con exactamente un hijo hoja / (n−1)), `chaining_flag` (`depth > ceil(log2 n)+2` o `rate > 0.60`, umbrales heurísticos del catálogo §8), `leaf_order` (orden quasi-diagonal del motor) y umbrales eco para auditabilidad.
- Guards del épico: `n<2` → métricas `None` + `reason` sin elevar (pre-chequeo, sin try/except ancho); `n==2` → depth 1, rate 0.0 (fusión hoja-hoja, sin acreción), flag False explícito (no patológico); errores de programador (método inválido, covarianza no cuadrada/no-finita/asimétrica) propagan el `ValueError` del seam (fail loud).
- **Corrección decidida por usuario**: `chaining_rate` cuenta EXACTAMENTE-un-lado-hoja (verificación empírica: la lectura ≥1-hoja tiene piso 0.5 y marca 0.818 en el patrón sano). Pines: cadena → `depth==n−1`, `rate==(n−2)/(n−1)`, flag True; balanceado → depth mínimo, rate 0.0, flag False.
- La aproximación ward-sobre-distancia-precomputada (nota SciPy: ward exige euclidiana) se documenta, no se "arregla" (criterio: finitud).
- Exports en `portfolio_engine/app/__init__.py`. Scope cortado: sin cofenética/balance/gap (§10: la altura es causalmente irrelevante para la bisección por conteo), sin flip de default, sin diagnóstico por fold.

## Capabilities

### New Capabilities

(none — se extiende la capability existente)

### Modified Capabilities

- `technical-report`: +1 requirement ADDED (salud del árbol jerárquico) con scenarios de cadena pura, balanceado, degenerados y método inválido.

## Impact

- `portfolio_engine/app/report_json.py`: solo append + `__all__`; `hrp.py` diff cero.
- `tests/test_report_json.py`: nueva clase `TestTreeDiagnostics` (TDD rojo primero).
- `feature_list.json` (feat-048 + errata de definición), `progress.md`, `session-handoff.md`: trackers en la rama.
- Sin cambios en `core/`, `portfolio/`, `data/`, `validation/`, `viz/`, `pipeline.py`, `cli.py`, `config.py`.
