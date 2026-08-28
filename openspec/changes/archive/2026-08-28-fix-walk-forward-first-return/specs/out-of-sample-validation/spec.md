## MODIFIED Requirements

### Requirement: Evaluación OOS con pesos ex-ante

Para cada ventana, los pesos SHALL derivarse exclusivamente del slice de entrenamiento (alineación→stats→HRP) y aplicarse SIN recalculo sobre el slice de test; los retornos OOS combinan precios de test con esos pesos. La serie de retornos OOS de un fold SHALL cubrir todos los días de la ventana de test — exactamente `test_rows` retornos — donde el retorno del primer día de test SHALL calcularse contra el último precio previo a la ventana (información pasada); SHALL NOT usarse el truco de re-desplazamiento circular que omite ese primer retorno ni precios futuros de la propia ventana.

#### Scenario: sin mirada al futuro
- **WHEN** se evalúa cualquier fold
- **THEN** mutar el slice de test no altera los pesos resultantes del mismo fold

#### Scenario: primer día del test incluido
- **WHEN** el retorno del primer día de la ventana de test es distinto de los demás y los retornos son idénticos entre activos
- **THEN** el retorno OOS anualizado del fold incluye exactamente ese primer retorno (media sobre `test_rows` observaciones, no `test_rows−1`)
