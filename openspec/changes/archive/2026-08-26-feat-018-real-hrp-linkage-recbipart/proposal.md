# Proposal: feat-018-real-hrp-linkage-recbipart

## Why

El clustering actual (C1) es greedy por umbral con selección de representante — no es HRP. El proyecto se llama *hierarchical clustering portfolio selector* pero nunca implementó la metodología que anuncia. Con todas las dependencias del DAG satisfechas (alineación A3, guards C3, contrato de datos C2, config validada M1, distancia firmada M2), es el momento diseñado para el reemplazo: HRP real de López de Prado (2016) — linkage, quasi-diagonalization, recursive bisection — que asigna sin invertir la covarianza.

## What Changes

- `portfolio_engine/portfolio/hrp.py` (nuevo):
  - `_leaf_order(link)` — quasi-diagonalización por expansión recursiva del árbol scipy
  - `_cluster_ivp(cov_slice)` — portfolio de varianza inversa dentro de un clúster
  - `calculate_hrp_weights(cov, tickers_order) -> np.ndarray` — bisección recursiva top-down
- `portfolio/allocation.py`: `"hrp"` añadido a `WEIGHT_ALLOCATION_METHODS`
- `core/config.py`: default `weight_allocation_method="hrp"` (**cambio deliberado**, ADR 003)
- `app/pipeline.py`: rama dedicada — con hrp, el universo filtrado completo pasa directo al asignador jerárquico (sin pruning representativo); luego constraints de feat-014 aplican como al resto
- `docs/adr/003-hrp-adoption.md`: scipy-vs-riskfolio (decisión-log), flip de default, interacción con bounds
- Tests (`tests/test_hrp.py`): caso analítico exacto 2 activos, invarianza permutación (multiset de pesos), duplicados degenerados, contraste vs risk-parity en estructura jerárquica sintética (~8 tests)
- Fuera de scope: HERC variants, linkage paramétrico (decision-log), cambios a viz

## Capabilities

### Modified Capabilities
- `configuration-contract`: nuevo método válido en enum; nuevo default.
- `numeric-correctness`: el asignador jerárquico hereda las garantías de finitud y de verificación final.
