# Design: feat-026-walk-forward-validation

## Context

Motor completo estable con inyección de provider (feat-023); HRP default (feat-018); métricas honestas (feat-020). Los pesos HRP pueden violar el cap en universos reducidos → relajación CRITICAL ya documentada (feat-021): walk-forward hereda esa política por ventana y cuenta folds relajados.

## Goals / Non-Goals

**Goals:** motor sin fuga; embargo explícito; métricas OOS puras; integración composición sobre provider.
**Non-Goals:** costos/turnover (fase siguiente explicitada), gráficos walk-forward, CV combinatorio/purged-Kfold full (diferida), CLI.

## Decisions

### D1 — Generador puro de rangos sobre índices, no fechas
La alineación previa ya fija calendario común; ventanas operan sobre posiciones 0..N-1. Testeable exhaustivamente; fechas solo para reporting.
### D2 — Re-uso de funciones de dominio existentes
Cada fold llama `construct_returns_matrix`, correlación/covarianza, `calculate_hrp_weights` — ninguna copia del motor dentro de validación: si el motor cambia, la validación cambia (buena propiedad para validador).
### D3 — Retornos OOS = Σ wᵢ · rᵢ,t sobre test
Aproximación buy-and-hold-within-window con rebalanceo implícito fold-a-fold; se documenta que no modela intraperiodo drift de pesos (estándar de primera iteración).
### D4 — Reporte dataclass serializable a dict
`to_dict()` para futura salida JSON/CLI sin romper API.

## Risks / Trade-offs

- Fold corto (~test=60 filas) da vol anualizada ruidosa; mediana mitiga, documentado
- Nº assets variable por fold (filtros de ese tramo) — manejar dictas de tickers válidos por fold
