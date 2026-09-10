# Design: feat-tree-health-chaining (feat-048)

## Contexto y decisiones previas

- Épico JSON (043/044/045/046); convenciones: append-only en `report_json.py`, `ValueError` nombrado vs `None+reason`, imports function-local, `__all__` + `app/__init__.py`.
- Seams: `build_hrp_linkage(cov, method)` (`hrp.py:57-90`, valida enum pre-scipy + cuadrada/finita/simétrica/diag>0 + `n<2 → ValueError`), `_leaf_order(Z, n)` (`hrp.py:23-42`, DFS iterativo, `n==1 → [0]`), invariante runtime-diagnostics `dendrogram == _leaf_order == leaves_list`.
- Catálogo §8; ADR-006 (enum `single|ward|average`, default `single`); nota SciPy ward-euclidiana; CPCC excluido (§10, Sokal-Rohlf: preserva alturas, no usabilidad de bisección).
- **Decisión de usuario 2026-09-10**: `chaining_rate` = exactamente-un-lado-hoja (verificación empírica del piso 0.5 bajo ≥1-hoja).

## Decisiones de diseño

1. **Firma `tree_diagnostics(covariance_matrix, linkage_method="single") -> dict`**: default = default del motor; sin config nueva (el caller feat-050 pasa `config.linkage_method`).
2. **Recompute de `Z` dentro** (no se acepta Z externa): el diagnóstico audita el linkage que el motor construiría con esos inputs; coste O(n²) trivial con n≤12. Determinista (sin aleatoriedad en el seam).
3. **Profundidad por DP sobre filas en orden** (validez SciPy: hijos siempre definidos antes): `depth[hoja]=0`; fila `i` (cluster `n+i`): `1+max(depth[c1], depth[c2])`; respuesta `depth[2n−2]`. Recorrido iterativo (sin recursión). NUNCA `Z[:,2]`.
4. **Acreción**: fila cuenta si `(c1<n) != (c2<n)` (XOR: exactamente un lado hoja). Tamaños de columna 3 innecesarios (solo las hojas tienen tamaño 1 ⇒ chequeo por id ≡ por tamaño; se documenta).
5. **Pre-chequeo `n<2 → None+reason`** ANTES del seam (sin try/except ancho que trague errores de método/covarianza). `n` de `shape[0]` tras `asarray`+chequeo cuadrado (no-cuadrada → `ValueError` nombrado propio antes del seam).
6. **`n==2 → flag False` explícito** (tasa 0.0: la única fusión es hoja-hoja; el gate documenta que 2 activos jamás se marcan; catálogo: no patológico).
7. **Umbrales eco en la salida** (`depth_threshold`, `rate_threshold`): auditabilidad máquina (precedente `effective_bounds` feat-045). Etiquetados heurísticos en docstring (sin fuente literaria para +2/0.60; anclas exactas sí: caterpillar↔n−1, balanceado↔ceil(log2 n), Fischer 2021/Sackin/Colless como contexto).
8. **`leaf_order` = `_leaf_order(Z, n)`** (el orden que HRP realmente usa), como lista de ints JSON-nativa; test pinea igualdad con `leaves_list` (invariante runtime-diagnostics).
9. **Ward**: sin validación extra; test de finitud sobre 3 bloques; docstring cita la aproximación (SciPy Note 2 + Murtagh-Legendre 2014).
10. **Sackin/profundidad-media NO se añaden** (scope: el tracker fija 4 salidas; L_inf basta como veto barato; §10 excluye métricas sin accionabilidad directa).
11. **Método inválido/cov inválida → propagan** (fail loud del seam; sin envoltura propia salvo cuadratura).

## Keys de salida

`linkage_method, n_assets, max_depth, depth_threshold, chaining_rate, rate_threshold, chaining_flag, leaf_order, reason` (métricas `None` + `reason="n_assets<2"` en degenerado; `reason=None` en ok).

## Tests (TDD)

`TestTreeDiagnostics`: red por `ImportError` (registrar nº); cadena-4 anidada (depth 3, rate 2/3, flag); balanceado-8 a mano (depth 3, rate 0, flag, leaf_order==_leaf_order==leaves_list); 12-bloques rng42 (depth≤6, flag False, leaf==_leaf_order); n=1 y n=0 (None+reason, no raise); n=2 (1/0.0/False); método inválido (`ValueError` match linkage_method); ward-3-bloques finito; strict-JSON round-trip; export-surface.

## Riesgos

- Fragilidad 1e-12: nula (enteros + comparaciones exactas; `approx` solo donde haya float de linkage — depth/rate son exactos salvo división (n−2)/(n−1): usar `==` con fracción o `approx`).
- rng42 estable (lock versionado; patrón ya usado en test_dendrogram).
- `leaves_list` importado en tests desde `scipy.cluster.hierarchy` (público).
