# Design: feat-007-risk-free-single-source

## Context

Un solo parámetro, dos fuentes, 150 bps de divergencia silenciosa. El caller interno (pipeline) ya pasa config.risk_free_rate.

## Goals / Non-Goals

**Goals:** fuente única; fallo ruidoso ante omisión; prueba del contrato offline.
**Non-Goals:** congelar/validar PortfolioConfig (feat-013); serie temporal de tasas reales (diferida — decision-log); tocar cálculo de Sharpe (C3 corrige guards).

## Decisions

### D1 — Parámetro requerido sobre default-dinámico
Alternativa era `risk_free_rate: float | None = None` leyendo config dentro del fetcher: oculta el acoplamiento y añade import cruzado. Un binding TypeError es el contrato más explícito posible.
*Descartada*: mantener 0.03 y "documentar" — normaliza la divergencia.

### D2 — Test por binding-time
`pytest.raises(TypeError)` sin ejecutar cuerpo → cero red en CI. La firma ES la spec.

## Risks / Trade-offs

- Callers externos imaginarios romperían: paquete no publicado, aceptado.
