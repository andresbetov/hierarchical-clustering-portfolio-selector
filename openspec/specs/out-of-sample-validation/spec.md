# out-of-sample-validation Specification

## Purpose
Garantizar que las métricas de validación del motor provengan exclusivamente de información pasada: pesos fijados sobre ventanas de entrenamiento, evaluados sobre ventanas posteriores separadas por embargo, sin ninguna ruta de fuga temporal.

## Requirements

### Requirement: Ventanas walk-forward sin fuga

El generador de ventanas SHALL producir pares (train, test) donde train precede estrictamente a test con un gap de `embargo_days` filas entre boundary, cubriendo la serie sin solapamientos internos y fallando ruidosamente si los parámetros no producen al menos una ventana completa.

#### Scenario: embargo respetado
- **WHEN** se generan ventanas con embargo_days=5
- **THEN** ningún índice del slice de test aparece en el slice de entrenamiento ni en el margen

#### Scenario: parámetros insuficientes
- **WHEN** train+test+embargo exceden los datos disponibles
- **THEN** ValueError descriptivo antes de iterar

### Requirement: Evaluación OOS con pesos ex-ante

Para cada ventana, los pesos SHALL derivarse exclusivamente del slice de entrenamiento (alineación→stats→HRP) y aplicarse SIN recalculo sobre el slice de test; los retornos OOS combinan precios de test con esos pesos. La serie de retornos OOS de un fold SHALL cubrir todos los días de la ventana de test — exactamente `test_rows` retornos — donde el retorno del primer día de test SHALL calcularse contra el último precio previo a la ventana (información pasada); SHALL NOT usarse el truco de re-desplazamiento circular que omite ese primer retorno ni precios futuros de la propia ventana.

#### Scenario: sin mirada al futuro
- **WHEN** se evalúa cualquier fold
- **THEN** mutar el slice de test no altera los pesos resultantes del mismo fold

#### Scenario: primer día del test incluido
- **WHEN** el retorno del primer día de la ventana de test es distinto de los demás y los retornos son idénticos entre activos
- **THEN** el retorno OOS anualizado del fold incluye exactamente ese primer retorno (media sobre `test_rows` observaciones, no `test_rows−1`)

### Requirement: Agregación transparente de folds

El reporte SHALL exponer métricas por fold y agregados (mediana de retorno/vol anualizadas, Sharpe mediano, fracción de folds positivos), calculadas solo sobre folds completos válidos.

#### Scenario: fold degenerado excluido
- **WHEN** un fold produce varianza nula o universo vacío
- **THEN** se marca inválido, se loggea y se excluye de los agregados
