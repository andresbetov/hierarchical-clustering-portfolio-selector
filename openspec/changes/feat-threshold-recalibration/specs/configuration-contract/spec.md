## ADDED Requirements

### Requirement: Defaults de filtrado recalibrados

El constructor por defecto SHALL usar `minimum_sharpe_threshold == 0.3` y `maximum_volatility_threshold == 0.27`. Los overrides explícitos SHALL seguir respetándose sin cambios y la validación de rangos existente SHALL permanecer intacta.

#### Scenario: defaults recalibrados

- **WHEN** se construye `PortfolioConfig()` sin overrides
- **THEN** `minimum_sharpe_threshold == 0.3` y `maximum_volatility_threshold == 0.27`

#### Scenario: overrides explícitos intactos

- **WHEN** se construye con thresholds explícitos (p. ej. `minimum_sharpe_threshold=0.5`)
- **THEN** se usan los valores dados y la validación de rangos aplica igual que antes
