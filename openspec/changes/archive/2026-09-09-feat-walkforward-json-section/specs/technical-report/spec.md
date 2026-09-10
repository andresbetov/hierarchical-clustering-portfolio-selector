# Spec delta: technical-report (feat-049)

## ADDED Requirements

### Requirement: Sección walk-forward con detalle por fold y deriva

El reporte técnico SHALL poder incluir la validación walk-forward consumiendo `WalkForwardReport.to_dict()` verbatim para los agregados (las medianas de la sección SHALL ser idénticas a las del reporte; `to_dict` NO se modifica). El detalle por fold SHALL exponer índice, posiciones de train/test (como listas), tickers, pesos, retorno/volatilidad/Sharpe OOS, `mandate_relaxed` y benchmarks, preservando los folds inválidos tal cual (sin sintetizar). La deriva entre folds válidos consecutivos (ordenados por índice) SHALL ser `l1 = Σ|w_k − w_{k−1}|` sobre vectores embebidos en cero sobre la unión de tickers del par, en [0,2] para carteras long-only totalmente invertidas; SHALL reportar `median_l1`, `p90_l1` (cuantil lineal), `pairs_computed/pairs_possible` y la etiqueta `drift-not-turnover`. Un fold inválido SHALL romper la cadena sin interpolación. Con menos de 2 folds válidos la deriva SHALL ser `null` con motivo. La deriva JAMÁS SHALL anualizarse ni multiplicarse por bps.

#### Scenario: agregados idénticos al reporte

- **WHEN** un `WalkForwardReport` entra a la sección
- **THEN** `section["aggregates"] == report.to_dict()` exacto, llave por llave

#### Scenario: deriva cero con pesos idénticos

- **WHEN** dos folds válidos consecutivos tienen los mismos pesos
- **THEN** su `l1 == 0.0` y la mediana sobre un solo par equals ese valor

#### Scenario: mover 10 puntos da L1 0.20

- **WHEN** dos folds válidos difieren en 10 puntos de peso (0.10 de A a B)
- **THEN** su `l1 == 0.20` exacto (dos vías: sale 0.10, entra 0.10)

#### Scenario: fold inválido rompe la cadena

- **WHEN** un fold inválido se intercala entre dos válidos
- **THEN** `pairs_computed < pairs_possible`, el par roto se informa y ningún valor se interpola

#### Scenario: un solo fold sin deriva

- **WHEN** el reporte tiene un único fold (válido o no)
- **THEN** la deriva es `null` con `reason` y `pairs_possible == 0`

#### Scenario: posiciones serializables

- **WHEN** los folds llevan posiciones como tuplas `(inicio, fin-exclusivo)`
- **THEN** la sección las expone como listas `[inicio, fin]` y el documento vuelca a JSON estricto

#### Scenario: benchmarks preservados sin sintetizar

- **WHEN** un fold trae benchmarks equal/ivp y otro es inválido con `{}` 
- **THEN** la sección los reproduce tal cual (dict completo vs `{}`), sin fabricar valores
