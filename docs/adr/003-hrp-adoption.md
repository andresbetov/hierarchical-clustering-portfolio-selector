# ADR 003 — Adopción de HRP como método de asignación por defecto

**Estado:** Aceptado · **Fecha:** 2026-08-26 · **Feature:** feat-018 (C1, keystone del DAG)

## Contexto

La cartera histórica se construyó con greedy-threshold clustering + selección por scoring + risk_parity plano — nada de eso es HRP, pese al nombre del proyecto. feat-008/009/012/013/016 cerraron las precondiciones: matrices alineadas y finitas, config validada, distancia firmada decidida.

## Opciones evaluadas

1. **Implementación propia con scipy.linkage** ✅ — control total de los 3 pasos canónicos (linkage single → quasi-diagonalization → recursive bisection), ~150 líneas auditables, `scipy` pasa de dependencia fantasma a consumida. Universos objetivo (decenas–centenas) están lejos del threshold n≈400 donde Fast-HRP justificaría alternativas.
2. **riskfolio-lib** — descartada por peso de dependencia y opacidad para aprendizaje/auditoría; puerta abierta si crece la escala (ver `docs/decision-log-feat001.md`).
3. **Mantener greedy + risk_parity** — congela el gap metodológico crítico (C1).

## Decisión

- Nuevo módulo `portfolio_engine/portfolio/hrp.py` con los 3 pasos; sin `np.linalg.inv` (solo diagonales de slices).
- `"hrp"` entra al enum y se convierte en **default** de `weight_allocation_method` (patrón single-flip ya aplicado en ADR 002). Los métodos legacy permanecen operativos.
- Ruta end-to-end propia en pipeline: HRP asigna sobre todo el universo filtrado, omitiendo el pruning por scoring.
- Constraints de bounds (feat-014, Dykstra) se aplican al final igual que en los demás métodos.

## Consecuencias

- **Composición de carteras cambia** respecto a risk_parity: ahora respeta jerarquía de correlaciones con bisección por varianza inversa. Es el propósito central.
- Los tests pinnean expectativas analíticas exactas (2 activos → inverse-variance puro) e invarianza-permutación del multiset de pesos.
- HERC, linkage paramétrico y métricas alternativas quedan diferidas (decision-log).

---

### Addendum 2026-09-01 — Interacción HRP × Dykstra post-hoc (feat-036, no supersede)

La fase Dykstra de `portfolio/allocation.py:243` aplicada tras `hrp.py:122` (`calculate_optimal_portfolio_weights_hrp:422-425`) encuentra el vector factible euclídeamente más próximo a los pesos HRP puros, **no** el vector factible de mínima varianza jerárquica. Cuando un bound muerde (ej. `max=0.30` en universo concentrado `n=5`), la redistribución deja de respetar `alpha = 1 - VarL/(VarL+VarR)` de `hrp.py:118` y aplana la jerarquía: el ratio intra-cluster ya no es `1/var` y la dispersión de pesos se reduce (ej. `n=5, max=0.30` → pesos `~[0.45,0.13,0.13,0.13,0.13]` proyectados a `~[0.30,0.175,0.175,0.175,0.175]`). *Elección consciente:* se prioriza estabilidad de mandato long-only fully-invested (`min 5% / max 30%` + `sum=1` determinista, testeable y compartido con todos los métodos, `allocation.py:243-317`) sobre pureza de paridad de riesgo.

No se implementó constraining **intra-bisección** (variante Pfitzinger & Katzke 2017, donde cada bisección respeta bounds re-escalando `alpha` bajo tope). Motivos: (i) acopla `config` a `hrp.py:104-120` convirtiéndolo en solver con estado de bounds por rama, (ii) pierde la garantía `sin inversión` y la auditabilidad de ~150 líneas, (iii) dificulta los invariantes `2 activos → [0.8,0.2]` e invarianza-permutación (`spec:numeric-correctness`). La alternativa post-hoc es estándar industria, reversible y verificable; si el walk-forward demuestra que la distorsión euclídea degrada Sharpe/vol vs. HRP acotado intra-nodo, se promoverá **ADR 007** que superseda este addendum. `spec:numeric-correctness` debe actualizarse de `fijación iterativa` a `proyección alternante de Dykstra` cuando se documente.

