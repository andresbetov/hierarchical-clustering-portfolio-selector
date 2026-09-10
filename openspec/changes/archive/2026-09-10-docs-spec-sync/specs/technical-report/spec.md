# Spec delta: technical-report (feat-053, ADDED)

## ADDED Requirements

### Requirement: Serie in-sample para cómputo, no para serialización

La serie de log-retornos diarios de la cartera SHALL construirse para derivar `tail` y `drawdown`, pero el JSON SHALL exponer solo `series_n_obs`, `tail` y `drawdown` (ni la serie `portfolio_return_series` ni la curva de drawdown se serializan).

#### Scenario: sin serie en el payload

- **WHEN** se inspecciona el JSON emitido
- **THEN** no existe clave `portfolio_return_series`; existen `series_n_obs`, `tail` y `drawdown`

### Requirement: Pesos finales in-sample fuera de contrato

El contrato SHALL NOT exigir el vector final de pesos in-sample en el reporte (gap registrado en roadmap v0.2.0); la asignación queda cubierta por diagnósticos (HHI/DR/RC, telemetría Dykstra) y por los pesos por fold de `walk_forward`.

#### Scenario: sin vector de pesos finales

- **WHEN** se inspecciona `allocation_diagnostics`
- **THEN** existen diagnósticos y telemetría, pero ninguna clave con el vector final de pesos in-sample
