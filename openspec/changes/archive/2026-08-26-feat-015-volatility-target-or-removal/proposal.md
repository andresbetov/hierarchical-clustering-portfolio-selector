# Proposal: feat-015-volatility-target-or-removal

## Why

`target_portfolio_volatility` es un parámetro muerto desde su creación (discrepancia D1, README lo admite explícitamente). Analizado contra las restricciones estructurales del producto (auditoría §5): el mandato actual es long-only fully-invested con suma=1 y bounds por activo — bajo esas condiciones un vol-target scaling real exige leverage o shorts, fuera del alcance declarado. Implementarlo medio (solo log diagnóstico) duplicaría lo que feat-020 entregará correctamente con covarianza alineada.

## What Changes

- **Decisión ADR** (`docs/adr/001-volatility-target-removal.md`): eliminar el parámetro; documentar por qué el vol-targeting requiere leverage y bajo qué condiciones re-introducirse
- `core/config.py`: campo y regla de validación eliminados
- `README.md`: fila de la tabla eliminada junto a la nota "no se aplica" (discrepancia D1 cerrada)
- `tests/test_config.py`: regresión que documenta la remoción (el atributo ya no existe)
- Fuera de scope: reporte ex-ante de vol de cartera (feat-020/A5), cualquier mecanismo de leverage

## Capabilities

### New Capabilities
- Ninguna — decisión de simplificación registrada como ADR versionado.
