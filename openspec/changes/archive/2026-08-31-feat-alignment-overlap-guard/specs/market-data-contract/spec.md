## ADDED Requirements

### Requirement: Guard de solapamiento por ratio en alineación
`align_prices_to_common_calendar` SHALL excluir con warning nombrado (ticker + coverage) a tickers cuya cobertura < `minimum_overlap_ratio` contra el span común (unión de fechas), preservando sin truncar la historia del resto. Con `ratio=1.0` el comportamiento SHALL ser bit-a-bit idéntico al inner-join vigente. Tras exclusión, el guard `MIN_COMMON_ROWS=2` SHALL seguir aplicándose; manejo por-ticker completo (union+forward-fill) queda explícitamente diferido a v0.2.0.

#### Scenario: delisted/IPO trunca silenciosamente sin guard
- **WHEN** A/B tienen 250 filas comunes y C solo 125 (50% solapa) con `minimum_overlap_ratio=0.9`
- **THEN** C es excluido con warning nombrado, `aligned` contiene solo A/B con 250 filas (no 125) y matrices posteriores no contienen C

#### Scenario: invariancia sin delistings
- **WHEN** todos los tickers solapan >=0.9 (universo 12 large-caps nominal)
- **THEN** `aligned` es idéntico bit-a-bit al resultado pre-guard (mismo `frame.dropna` + orden ascendente)

#### Scenario: calendarios disjuntos aún falla ruidoso
- **WHEN** tras filtrado por ratio la intersección de supervivientes tiene <2 filas
- **THEN** lanza `ValueError` con `too small|intersection` (mismo que `MIN_COMMON_ROWS`) en lugar de matriz degenerada

### Requirement: Chart 4 full-universe alineado
`generate_complete_analysis_report` SHALL construir la matriz full-universe de chart 4 sobre calendario común (mismo guard), no sobre `historical_prices` crudos de longitudes distintas.

#### Scenario: chart 4 no crashea con IPO
- **WHEN** un ticker del universo tiene historia 50% más corta y se genera el reporte completo
- **THEN** chart 4 se genera sin `ValueError: lengths differ` y usa el universo superviviente del guard
