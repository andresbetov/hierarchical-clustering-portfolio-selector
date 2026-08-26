# ADR 002 — Distancia de correlación firmada como default del clustering

**Estado:** Aceptado · **Fecha:** 2026-08-26 · **Feature:** feat-016 (M2 de `docs/auditoria-tecnica.md`)

## Contexto

El clustering de selección usaba `d = 1 - |corr|`. El `abs()` colapsa el signo: activos con correlación -0.9 (hedge/diversificador ideal) quedan a distancia 0.1 de gemelos con +0.9 y se fusionan — contrário a la tesis de diversificación del proyecto.

## Opciones evaluadas

1. **Mantener abs por compatibilidad** — congela el defecto semántico; los resultados históricos heredan el error.
2. **Firmada como default** ✅ `d = sqrt(0.5·(1-corr))` — estándar HRP (De Prado 2016, Palomar 12.3). Correlación negativa ⇒ distancia máxima ⇒ jamás fusionados.
3. **Otras métricas** (angular, entropía) — evaluadas en literatura (Salas-Molina 2025: métricas basadas en correlación superan no-correlación); no aportan sobre la firmada para este caso.

## Decisión

`distance_metric = "signed"` default; `"abs"` disponible explícitamente para reproducir comportamiento histórico.

## Detalle de implementación relevante

El umbral de configuración (`maximum_correlation_threshold`) se interpreta en **términos de correlación**, y se convierte internamente a distancia según modo:

| Modo | Conversión | Efecto en threshold=0.65 |
|---|---|---|
| signed | `sqrt(0.5·(1-t))` ≈ 0.4183 | solo fusiona pares con corr > 0.65 |
| abs | `1-t` = 0.35 | idem, pero \|±0.65\| ambos |

## Consecuencia de comportamiento

Los resultados de clustering cambian respecto al histórico (firmada es más conservadora: fusiona menos). Decidido deliberadamente antes de feat-018 para un único cambio de semántica, no dos.
