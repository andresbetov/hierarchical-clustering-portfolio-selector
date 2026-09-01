## ADDED Requirements

### Requirement: Ratio de solapamiento validado
`PortfolioConfig` SHALL exponer `minimum_overlap_ratio: float = 0.9` validado en `(0, 1]` (exclusivo 0, inclusivo 1) y SHALL rechazar fuera de rango en construcción con `ValueError`.

#### Scenario: cero excluido
- **WHEN** se construye con `minimum_overlap_ratio=0`
- **THEN** `ValueError` `must be within (0, 1]`

#### Scenario: uno inclusivo
- **WHEN** se construye con `minimum_overlap_ratio=1.0`
- **THEN** construcción válida (exige solape perfecto, igual a inner join actual)

#### Scenario: fuera de rango superior
- **WHEN** se construye con `minimum_overlap_ratio=1.0001`
- **THEN** `ValueError`
