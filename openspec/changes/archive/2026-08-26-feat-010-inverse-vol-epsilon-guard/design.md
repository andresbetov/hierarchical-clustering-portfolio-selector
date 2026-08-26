# Design: feat-010-inverse-vol-epsilon-guard

## Context

Último divisor sin protección tras feat-009 (sharpe, corr, risk-parity). Reutiliza `VOL_FLOOR_EPS` — cero superficies nuevas.

## Goals / Non-Goals

**Goals:** rama inverse-vol inmune a vol=0.
**Non-Goals:** reescribir otros métodos; caps de factores (solo aplica a risk-parity iterativa).

## Decisions

### D1 — piso pre-inversión sobre mutación semántica
`np.maximum(vols, EPS)` conserva el ranking relativo entre vols sanas y da al activo degenerado el peso máximo-eps proporcional... En la práctica: su inverso sería enorme; se comporta como "peso dominante pero finito" análogo al diseño de risk-parity. Consistente con contract: inf proscrito, NaN ya filtrado aguas arriba por feat-009 (los no-finitos nunca llegan aquí desde pipeline).

### D2 — test mínimo determinista
Un caso cubre el contrato (0 y positiva → finitos, positivos, suma 1). Matemática simple no requiere exhaustive.

## Risks / Trade-offs

- Ninguno relevante: cambio de 1 línea + test
