# Spec delta: verification-harness (feat-053, MODIFIED)

## MODIFIED Requirements

### Requirement: init.sh prefiere el intérprete del proyecto

Cuando `uv` está disponible, `init.sh` SHALL ejecutar pytest vía `uv run python -m pytest`; el chequeo con python3 del sistema queda como fallback exclusivo de entornos sin uv. La ausencia total de tests (exit 5) SHALL seguir tratándose como no-fallo para bootstrap.

#### Scenario: uv disponible

- **WHEN** `uv sync` instaló pytest en `.venv` y se ejecuta `./init.sh`
- **THEN** la suite corre vía `uv run python -m pytest` y el output muestra resultados reales de tests, no el salto "pytest not installed"

#### Scenario: sin uv y sin pytest del sistema

- **WHEN** el entorno no tiene uv ni pytest instalable
- **THEN** init.sh continúa con compileall y termina exit 0 (comportamiento bootstrap preservado)
