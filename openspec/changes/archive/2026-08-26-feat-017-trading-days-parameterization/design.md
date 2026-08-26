# Design: feat-017-trading-days-parameterization

## Context

B4 vive en los kernels jit; el patrón de parámetros requeridos desde config ya es ley (A2/A4). Última pieza antes del keystone HRP.

## Goals / Non-Goals

**Goals:** constante parametrizada y validada; cadena fetcher→metrics completa.
**Non-Goals:** detección automática de calendario (diferida); sesiones por-ticker (over-engineering para un solo mercado).

## Decisions

### D1 — Parámetro en kernel, no global module-level
Argumento explícito mantiene pureza (mismos kernels reutilizables con distintas constantes) y evita re-jit por closure.
### D2 — Rango [1,366]
366 cubre bisiesto completo; >1 evita sqrt/mean degenerados.

## Risks / Trade-offs

- Firma del fetcher crece a 4 params — contrato coherente, único caller interno
