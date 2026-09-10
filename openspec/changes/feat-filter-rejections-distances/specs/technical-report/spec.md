## ADDED Requirements

### Requirement: Diagnóstico de exclusiones del filtro con distancias al umbral

El reporte técnico SHALL poder incluir, para cada ticker solicitado del universo, un motivo de clasificación del embudo de filtrado y sus distancias firmadas al umbral. Los motivos de rechazo por métrica no finita o por umbral SHALL usar exactamente la misma nomenclatura que el filtro de producción. `d_sharpe` SHALL ser `sharpe − minimum_sharpe_threshold` y `d_vol` SHALL ser `maximum_volatility_threshold − vol` (negativa = excluido por esa vía); las distancias SHALL ser `null` cuando la métrica correspondiente no es finita o el motivo es de ingesta. Los conteos SHALL sumar exactamente el tamaño del universo solicitado. La clasificación de un superviviente SHALL ser distinguible de la de un excluido y reproducir el criterio del filtro de producción con el mismo orden de guardias (no-finito primero, luego Sharpe, luego volatilidad).

#### Scenario: excluido por poco queda cuantificado

- **WHEN** un ticker con Sharpe 0.28 frente a un mínimo de 0.30 entra al diagnóstico
- **THEN** su motivo es `below_min_sharpe`, `d_sharpe ≈ −0.02` y `d_vol` es positiva (no es su causa)

#### Scenario: activo plano sin distancias

- **WHEN** un ticker tiene Sharpe no finito (activo con varianza nula) y volatilidad 0.0
- **THEN** su motivo es `sharpe_non_finite` con ambas distancias `null`, nunca 0

#### Scenario: ticker sin métricas

- **WHEN** un ticker del universo pedido no aparece entre las métricas producidas por la ingesta
- **THEN** su motivo es `ingestion_rejected` con distancias `null`, y los conteos siguen cuadrando

#### Scenario: podado por calendario

- **WHEN** un ticker pasa ambos umbrales con métricas finitas pero no está en el conjunto final superviviente
- **THEN** su motivo es `overlap_pruned` (única capa de exclusión restante dentro de la corrida) y sus distancias reflejan su holgura

#### Scenario: superviviente legible

- **WHEN** un ticker está en el conjunto final
- **THEN** su motivo es `kept` con ambas distancias positivas calculadas (detección de "casi pasa" cuando `|d| < 0.05`)

#### Scenario: conteos consistentes

- **WHEN** se agrega el diagnóstico completo para un universo pedido
- **THEN** `kept + rechazados == |universo pedido|` y ningún ticker pedido queda sin clasificar
