# Design: feat-walkforward-json-section (feat-049)

## Contexto y decisiones previas

- Épico JSON (043/044/045/046/048); convenciones: append-only, `None+reason`, imports function-local, `__all__` + `app/__init__.py`.
- Seams: `WalkForwardFold` (`walk_forward.py:81-94`), `WalkForwardReport.to_dict()` (`:179-196`, 14 keys), `_median_or_none` (`:97-99`, `np.median` sobre finitos), `_embed` (`:252-256`), test bundles (`test_walk_forward.py:13-42`).
- Catálogo §1 (tabla por fold) + §9 (deriva: L1∈[0,2], 10pts→0.20, `drift-not-turnover`, jamás anualizar/bps, inválidos rompen cadena).
- Análisis externo: L1 dos-vías estándar (coste ∝ trade; one-way = L1/2, TV distance); zero-embed honesto vs intersección (la intersección esconde entradas/salidas); GIPS 4.A.5 (no enlazar a través de rupturas); p90 H&F Tipo 7 (`method="linear"`, precedente VaR feat-046); Perold 1988 (drift ≠ turnover implementable).

## Decisiones de diseño

1. **Firma `walk_forward_section(report) -> dict`**, duck-typing en runtime (sin `isinstance`; anotación vía `TYPE_CHECKING`): el caller (feat-051) pasa el objeto real; la estructura interna del motor es input de confianza (como `to_dict`).
2. **Shape**: `{"aggregates": dict(report.to_dict()), "folds": [...], "drift": {...}}`. Copia superficial del dict (los escalares son inmutables; no se recomputa nada).
3. **Fila por fold**: `index, train_positions/test_positions` (tupla→lista explícita; el sanitizador es segunda red), `tickers` (lista tal cual), `weights` (dict tal cual, orden preservado), `oos_return/oos_volatility/oos_sharpe` (tal cual, `None` incluidos), `mandate_relaxed`, `benchmarks` (dict tal cual, `{}` en inválidos).
4. **Válido = `oos_sharpe is not None and finite`** (`to_dict` cuenta `is not None`; el motor garantiza finito-o-None; el `isfinite` solo blinda folds artesanales).
5. **Deriva**: pares `(folds[i], folds[i+1])` adyacentes por índice con ambos válidos; universo = unión ordenada (`sorted(set(a)|set(b))`); `l1 = Σ|get(t,0)−get(t,0)|`; `median = np.median`, `p90 = np.quantile(v,0.9,method="linear")` (1 par ⇒ ambos equals l1); `pairs_possible = max(0, n_folds−1)` (slots de cadena), `pairs_computed`, `broken_pairs: [[i,j]]`, `label: "drift-not-turnover"`, docstring con L1=2×one-way + Perold.
6. **<2 válidos → `{"median_l1":None,"p90_l1":None,"pairs_computed":0,"pairs_possible":max(0,n−1),"broken_pairs":[],"label":"drift-not-turnover","reason"}`** (kebab-case, convención del épico): `need-2-valid-folds` si hay <2 válidos; `all-pairs-broken` si hay ≥2 válidos pero ningún par adyacente computable (p. ej. alternancia válido/inválido: la ruptura misma es la señal).
7. **Sin validación de pesos** (suma-1/long-only): los folds del motor la garantizan (Dykstra); validar estructura interna es scope ajeno. Documentado: L1∈[0,2] vale long-only.
8. **Tests**: hand-built `WalkForwardFold/Report` (precisión de pines) + 1 integración vía `walk_forward_evaluate` real con ventanas chicas (train=30/test=10/embargo=2) sobre panel sintético + strict-JSON round-trip + export-surface + identidad de agregados.

## Riesgos

- `np.quantile` con 1 valor: devuelve el valor (p90==mediana==l1) — pineado.
- `sorted()` en unión: determinista; el orden no afecta L1 (suma conmutativa).
- Benchmarks con floats numpy: el sanitizador los maneja (feat-043); test strict-JSON lo cubre.
- `to_dict` futuro con más keys: la copia las hereda (identidad preservada por construcción).

## No-goals

CLI/flag (feat-051), invocar el evaluador aquí, CPCV/DSR/PBO (v0.2.0), turnover modelado, benchmarks recalculados.
