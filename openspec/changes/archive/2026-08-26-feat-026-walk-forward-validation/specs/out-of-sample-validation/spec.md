# out-of-sample-validation Specification (delta)

## Purpose

Garantizar que las métricas de validación del motor provengan exclusivamente de información pasada: pesos fijados sobre ventanas de entrenamiento, evaluados sobre ventanas posteriores separadas por embargo, sin ninguna ruta de fuga temporal.

## ADDED Requirements

### Requirement: Ventanas walk-forward sin fuga

El generador de ventanas SHALL producir pares (train, test) donde train precede estrictamente a test con un gap de `embargo_days` filas entre boundary, cubriendo la serie sin solapamientos internos y fallando ruidosamente si los parámetros no producen al menos una ventana completa.

#### Scenario: embargo respetado
- **WHEN** se generan ventanas con embargo_days=5
- **THEN** ningún índice del slice de test aparece en el slice de entrenamiento ni en el margen

#### Scenario: parámetros insuficientes
- **WHEN** train+test+embargo exceden los datos disponibles
- **THEN** ValueError descriptivo antes de iterar

### Requirement: Evaluación OOS con pesos ex-ante

Para cada ventana, los pesos SHALL derivarse exclusivamente del slice de entrenamiento (alineación→stats→HRP) y aplicarse SIN recalculo sobre el slice de test; los retornos OOS combinan precios de test con esos pesos.

#### Scenario: sin mirada al futuro
- **WHEN** se evalúa cualquier fold
- **THEN** mutar el slice de test no altera los pesos resultantes del mismo fold

### Requirement: Agregación transparente de folds

El reporte SHALL exponer métricas por fold y agregados (mediana de retorno/vol anualizadas, Sharpe mediano, fracción de folds positivos), calculadas solo sobre folds completos válidos.

#### Scenario: fold degenerado excluido
- **WHEN** un fold produce varianza nula o universo vacío
- **THEN** se marca inválido, se loggea y se excluye de los agregados
