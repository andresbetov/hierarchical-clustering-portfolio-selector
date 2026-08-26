# Decision Log — feat-001 (contexto para feat-002..027)

> **ESTADO: EJECUCIÓN COMPLETA (2026-08-26)** — las 27 features del DAG se ejecutaron y mergeaaron. Este documento queda como registro histórico de decisiones diferidas y sus resoluciones; las filas marcadas ✅ apuntan al ADR/PR que las cerró. No abrir nuevas entradas aquí: usar ADRs directos.

**Creado:** 2026-08-26 · **Propósito:** preservar decisiones y opciones evaluadas durante el análisis de ordenamiento que NO quedaron en disco (viven/vivían solo en la sesión conversacional). Es complemento de:
- `docs/auditoria-tecnica.md` (hallazgos y fixes canónicos)
- `docs/orden-de-resolucion.md` (DAG con aristas file:line y rechazadas §3.2)
- `openspec/changes/archive/2026-08-26-feat-001-analisis-orden-resolucion/design.md` (D1-D4)

## ⚠️ Regla de citación

Las citas `file:line` de los documentos anteriores se basan en el árbol de `develop@d55c2d5`. Los primeros features las harán rotir. Al proponer cualquier feature posterior: **citar funciones/módulos, no números de línea**, releer el código actual y nunca copiar líneas del archive sin verificar.

## Opciones evaluadas que NO están en disco

### Para feat-018 (Real HRP) — ✅ RESUELTO en ADR 003 (2026-08-26)
- **scipy implementación propia** elegida (riskfolio-lib sigue descartado; puerta abierta si n>400 exige perf).
- Quasi-diag por expansión recursiva del árbol; bisección-split clásico.
- Linkage 'single' hardcodeado — Ward/completa diferidas como parámetros comparativos futuros.
- Ver también docs/adr/003-hrp-adoption.md.

### Racional para feat-016 (distancia de correlación) — ✅ RESUELTO en ADR 002 (PR #20)
`d = sqrt(0.5*(1-corr))` firmada CONFIRMADA como default: correlación negativa es diversificadora y *separa* activos en el dendrograma. La fórmula legacy `1-abs(corr)` sigue disponible vía `distance_metric="abs"`.

## Registro de decisiones diferidas (where-decide)

| Feature | Decisión pendiente | Alternativas |
|---|---|---|
| feat-015 | vol-target implementar o eliminar | ✅ ELIMINAR (ADR 001): incompatible con mandato long-only fully-invested |
| feat-016 | distancia firmada vs abs | ✅ SIGNED default (ADR 002, PR #20) |
| feat-018 | biblioteca / variante quasiDiag | ✅ scipy propia + bisection-split (ADR 003, PR #22) |
| feat-019 | solve/pinv/LedoitWolf | ✅ SOLVE sin inv + PD-repair jitter; LedoitWolf sigue diferida hasta Fase 4 (PR #23) |
| feat-021 | librería prop tests | ✅ hypothesis derandomize + fixtures propios (PR #25); pytest-mock no hizo falta con provider seam |

## Bordes de módulos para feat-023 (Strangler) — ✅ EJECUTADO (PR #27)

1. ✅ `MarketDataProvider` Protocol en data/provider.py (inyección vía pipeline.main(provider=...))
2. ⏭️ Separación física domain/ diferida: el boundary lógico existe (app sin canvas ni transporte) y el churn de mover archivos no se justificó aún
3. ⏭️ Reporter interface para viz — diferida
4. ✅ Ejecutado tras tests de caracterización feat-021, como estaba planificado

---
*Cerrado 2026-08-26 con la ejecución completa del DAG. Decisiones nuevas → ADR directo.*
