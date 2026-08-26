# ADR 001 — Eliminación de `target_portfolio_volatility`

**Estado:** Aceptado · **Fecha:** 2026-08-26 · **Feature:** feat-015 (A1 de `docs/auditoria-tecnica.md`)

## Contexto

`target_portfolio_volatility = 0.15` existía en configuración sin ningún consumidor (discrepancia D1; el README lo documentaba como "no se aplica"). Decidir: implementarlo, dejarlo como diagnóstico, o eliminarlo.

## Opciones evaluadas

1. **Implementar scaling real** `w *= target_vol / sqrt(wᵀΣw)` después del punto único de constraints (feat-014): rompe el mandato estructural del producto — long-only fully-invested con suma=1 y bounds 0.05–0.30 por activo. Alcanzar un vol target requiere apalancamiento o posiciones short, ambos fuera del alcance declarado.
2. **Diagnóstico informativo** (loggear vol ex-ante vs target sin escalar): valor parcial; su lugar correcto es el reporte con covarianza alineada que feat-020 (A5) construye — duplicarlo aquí sería trabajo muerto.
3. **Eliminar el parámetro** ✅ — honestidad de config, cero consumidores afectados (verificado por grep), la discrepancia D1 se cierra.

## Decisión

Se elimina `target_portfolio_volatility` de `PortfolioConfig`. La volatilidad ex-ante de cartera se reportará vía cálculo basado en covarianza en feat-020.

## Condiciones de re-introducción

- El producto soporte leverage explícito (suma ≠ 1) o sleeves short → un mecanismo de vol-targeting tendría sentido y volvería como feature propio con diseño (probablemente overlay sobre los pesos constraint-satisfechos).
- Se introduzca un benchmark con presupuesto de riesgo distinto de fully-invested.
