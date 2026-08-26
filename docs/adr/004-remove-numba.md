# ADR 004 — Eliminación de numba a favor de NumPy vectorizado

**Estado:** Aceptado · **Fecha:** 2026-08-26 · **Feature:** feat-022 (M6 de `docs/auditoria-tecnica.md`)

> **Nota de proceso:** este ADR fue citado por el commit de feat-022 pero no llegó a escribirse entonces; se materializa aquí como parte del feature siguiente tras detectarlo. La deuda se corrige, no se oculta.

## Contexto

7 kernels `@jit` recorrían `core/metrics.py` (+ residuales en allocation/selection) para tamaños de universo decenas–centenas × ~1250 días — muy por debajo del umbral n≈400 donde la literatura justifica alternativas tipo Fast-HRP.

## Opciones evaluadas

1. **Poda parcial** (mantener jit en corr/cov): duplicaba superficies de bugs y conservaba el peso.
2. **Eliminación total + vectorización NumPy** ✅ — warm-up JIT dominaba runtime; `.nbc`/instalación/tipado desaparecen.

## Decisión

Numba removida de dependencias y código; kernels vectorizados (`np.log`, `np.std(ddof=1)`, `(X-X̄)ᵀ(X-X̄)/(n-1)`, `outer(std,std)`); greedy clustering con búsqueda vectorizada del par mínimo.

## Verificación

Snapshot numérico pre/post idéntico en fixtures estrella (1e-12); suite completa 139+1skip verde SIN modificar un assert — protegido por feat-021.

## Re-introducción

Hot paths reales para n>400 tras perf measurement formal; o bloqueos específicos de numba sobre alguna versión del intérprete.
