# ADR 007 — Recalibración de thresholds del filtro (Sharpe 0.5→0.3, vol 0.25→0.27)

**Estado:** Aceptado · **Fecha:** 2026-09-09 · **Feature:** feat-042 (sobre tag v0.1.0)

## Contexto

El filtro de producción (`minimum_sharpe_threshold=0.5`, `maximum_volatility_threshold=0.25`) admite muy pocos supervivientes en la ventana 2021-2026: 12→4 en la muestra completa y N≤3 en 10/16 folds walk-forward (con relajación del mandato a `1/N`). Con N tan bajo el HRP colapsa hacia 1/N por álgebra (a N=2 HRP *es* IVP por definición; a N≤3 los bounds se relajan a la igualdad) y la validación OOS no puede distinguir al motor de los benchmarks (gap HRP−EQ −0.005, empate técnico).

## Opciones evaluadas

1. **Recalibrar a 0.3/0.27** ✅ — valores exactos del experimento vía A (15 tickers candidatos + 12 actuales, 4 combos, caché local): el combo D (universo actual + relajados) da N=6, L1-vs-equal 0.137, sin caps, 16/16 folds válidos y gap WF HRP−EQ **+0.070, único positivo** (0.489 vs 0.419 vs 0.380 IVP). El combo C (universo-15 + relajados) da el mejor showcase mecánico (L1 0.265, 8 supervivientes) pero sigue perdiendo vs 1/N (−0.061). El combo B (universo-15 + actuales) degenera a N=1 con HRP −0.400: cambiar solo el universo empeora.
2. **Mantener 0.5/0.25** — preserva snapshots y pinnings, pero congela el empate HRP≈1/N y 10/16 folds relajados como estado permanente.
3. **0.3/0.28 (más margen sobre XLE 0.2577 / XLK 0.2591)** — descartado por el usuario: ningún experimento lo respalda; cambiar valores invalida la evidencia medida.
4. **Top-K por sleeve en vez de umbral global** — preservaría bloques por construcción, pero introduce política de selección nueva sin evidencia; diferido a futuro feature.

## Decisión

- Defaults `minimum_sharpe_threshold=0.3`, `maximum_volatility_threshold=0.27` en `PortfolioConfig`; overrides explícitos y validación de rangos intactos; CLI sin cambios (no expone parámetros estructurales por diseño).
- Tests que pinan el default anterior se actualizan citando feat-042; regresión WF sintética CI-safe fija HRP ≥ equal bajo los nuevos defaults.

## Consecuencias

- Embudo productivo viable (N=6 en universo actual, 16/16 folds sin degenerar, 5/16 relajados vs 10/16).
- Sharpe absoluto in-sample baja (0.1833 → 0.1709): trade-off consciente, las medianas OOS mandan sobre el in-sample (README).
- Reversión trivial (2 líneas); thresholds futuros se re-evalúan con evidencia walk-forward, nunca por inspección visual.
- Números del experimento vía A (`/tmp/compare_universes.py`, no versionado por higiene del repo): A 12+PROD gap −0.005; B 15+PROD gap −0.400 (N=1); C 15+REL gap −0.061 (L1 0.265); D 12+REL gap +0.070.
