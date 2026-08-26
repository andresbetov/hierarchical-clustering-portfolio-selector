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
