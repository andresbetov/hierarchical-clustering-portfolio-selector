## Purpose

Documentación cuantitativa de convenciones y trade-offs del motor (Sharpe log, Dykstra vs HRP) para trazabilidad `grep log1p` y auditoría.

## ADDED Requirements

### Requirement: Convención Sharpe log coherente
El motor SHALL usar exceso logarítmico `excess = annual_return_log - ln(1+rf)` para coherencia dimensional con retornos `mean(log)*252`. La conversión SHALL ser `math.log1p(rf)` (estable para `rf << 1`). `rf=0` SHALL producir `excess` idéntico pre/post-fix; `rf=0.045` SHALL producir `excess` con `rf_log=0.044016885416774` exacto. Los pinnings numéricos relevantes SHALL migrar a `(ret - log1p(rf))/vol`.

#### Scenario: rf cero invariante
- **WHEN** se calcula Sharpe con `rf=0` y cualquier retorno log anualizado
- **THEN** el resultado coincide bit-a-bit con el cálculo pre-fix (log1p(0)=0)

#### Scenario: rf 0.045 coherente
- **WHEN** se calcula Sharpe con `rf=0.045` y `ret=0.10, vol=0.15`
- **THEN** excess = `0.10 - ln(1.045)` (≈0.055983) y Sharpe ≈0.37322, no `(0.10-0.045)/0.15=0.3666`

