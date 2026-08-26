# Índice de Architecture Decision Records

| ADR | Título | Estado | Resumen |
|-----|--------|--------|---------|
| [001](001-volatility-target-removal.md) | Eliminación de `target_portfolio_volatility` | Aceptado | El vol-targeting exige leverage, incompatible con el mandato long-only fully-invested; reintroducible si cambia |
| [002](002-correlation-distance-choice.md) | Distancia de correlación firmada como default | Aceptado | `sqrt(0.5·(1-corr))` reemplaza `1-\|corr\|`: los hedges (corr negativa) jamás se fusionan con gemelos positivos |
| [003](003-hrp-adoption.md) | Adopción de HRP como método default | Aceptado | Los 3 pasos canónicos con scipy; sin inversión de covarianza; flip de default del motor |
| [004](004-remove-numba.md) | Eliminación de numba por NumPy vectorizado | Aceptado | Escala n≪1000: warm-up JIT dominaba; paridad verificada bit-a-bit con la red feat-021 |

## Convención

Nuevo ADR = archivo incremental `00N-titulo.md`, estado inicial "Propuesto", promovido a "Aceptado" tras revisión. Los ADRs no se editan retroactivamente — una corrección crea un nuevo ADR que supersede al anterior.
