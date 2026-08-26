# configuration-contract Specification (delta)

## ADDED Requirements

### Requirement: Días de trading configurables y validados

`PortfolioConfig` SHALL exponer `trading_days_per_year` (default 252) validado dentro de [1, 366]; los kernels de anualización SHALL recibirlo como parámetro explícito y SHALL NOT contener la constante enterrada.

#### Scenario: calendario alternativo
- **WHEN** se configura trading_days_per_year=365 para un universo crypto
- **THEN** retorno/volatilidad anualizados usan exactamente 365 en su fórmula

#### Scenario: valor inválido
- **WHEN** se construye con trading_days_per_year=0
- **THEN** ValueError descriptivo
