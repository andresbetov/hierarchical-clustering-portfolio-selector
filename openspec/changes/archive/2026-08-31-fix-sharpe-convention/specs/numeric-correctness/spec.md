## MODIFIED Requirements

### Requirement: Sharpe indefinido para varianza nula
`calculate_sharpe_ratio` SHALL retornar NaN cuando la volatilidad anualizada sea menor o igual al piso épsilon, y SHALL NOT producir infinitos. El exceso SHALL calcularse como `annual_return_log - ln(1+rf)` con `math.log1p(rf)` para coherencia dimensional con retornos log anualizados; `rf=0` SHALL ser invariante.

#### Scenario: activo con precio plano
- **WHEN** un activo tiene volatilidad anualizada 0
- **THEN** su Sharpe es NaN y nunca inf

#### Scenario: rf cero invariante
- **WHEN** se calcula Sharpe con `rf=0`
- **THEN** el resultado coincide con el cálculo aritmético previo (log1p(0)=0)

