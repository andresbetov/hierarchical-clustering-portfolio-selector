## MODIFIED Requirements

### Requirement: Evaluación OOS con pesos ex-ante

Para cada ventana, los pesos SHALL derivarse exclusivamente del slice de entrenamiento (alineación→stats→filtros de producción→HRP) y aplicarse SIN recalculo sobre el slice de test; los retornos OOS combinan precios de test con esos pesos. La serie de retornos OOS de un fold SHALL cubrir todos los días de la ventana de test — exactamente `test_rows` retornos — donde el retorno del primer día de test SHALL calcularse contra el último precio previo a la ventana (información pasada); SHALL NOT usarse el truco de re-desplazamiento circular que omite ese primer retorno ni precios futuros de la propia ventana.

El universo invertible de cada fold SHALL derivar exclusivamente de métricas del slice de entrenamiento: los filtros de Sharpe/volatilidad de producción (`apply_asset_filters` con los umbrales de config) se aplican por fold, los pesos cubren solo los supervivientes y los excluidos reciben peso exactamente 0 sin desalinear el cómputo de retornos. Un fold sin supervivientes SHALL marcarse inválido con warning nombrado.

#### Scenario: sin mirada al futuro
- **WHEN** se evalúa cualquier fold
- **THEN** mutar el slice de test no altera los pesos resultantes del mismo fold

#### Scenario: primer día del test incluido
- **WHEN** el retorno del primer día de la ventana de test es distinto de los demás y los retornos son idénticos entre activos
- **THEN** el retorno OOS anualizado del fold incluye exactamente ese primer retorno (media sobre `test_rows` observaciones, no `test_rows−1`)

#### Scenario: universo por fold derivado del train
- **WHEN** un activo no supera los filtros del slice de entrenamiento de un fold pero sí los de un fold posterior
- **THEN** queda fuera de los pesos del primer fold y dentro de los del posterior, aunque su retorno de test del primer fold sea alto

## ADDED Requirements

### Requirement: Benchmarks ex-ante comparables en el reporte

El reporte SHALL exponer por fold benchmarks `equal` (1/N) e `ivp` (inverse-volatility) cuyos pesos se fijan exclusivamente con información de entrenamiento (conteo de supervivientes para equal; volatilidades de train para ivp) sobre el MISMO universo de supervivientes que el motor, aplicados congelados sobre los mismos retornos OOS del fold. `to_dict` SHALL añadir las medianas de retorno/volatilidad/Sharpe de ambos benchmarks, excluyendo folds inválidos igual que el motor.

#### Scenario: activos idénticos hacen coincidir motor y benchmarks
- **WHEN** todos los activos supervivientes tienen retornos idénticos entre sí
- **THEN** las medianas OOS de retorno del motor, equal e ivp coinciden (cualquier combinación convexa de columnas idénticas reproduce el retorno del activo)

#### Scenario: pesos de benchmarks inmunes a mutación OOS
- **WHEN** se muta el slice de test de un fold
- **THEN** los pesos ex-ante de los benchmarks de ese fold no cambian (solo información de train los define); las métricas OOS sí reflejan la mutación — medir el test es su propósito
