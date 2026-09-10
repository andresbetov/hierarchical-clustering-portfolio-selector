# Spec delta: project-packaging (feat-053, MODIFIED)

## MODIFIED Requirements

### Requirement: Sin dependencias fantasma

Cada dependencia de runtime SHALL corresponder a un uso actual del código; las herramientas de dev/test SHALL vivir solo en `[dependency-groups].dev`.

#### Scenario: dependencias dev aisladas

- **WHEN** se inspecciona `pyproject.toml` tras el change
- **THEN** `pytest` y `pytest-cov` están en `[dependency-groups].dev` y no en `[project].dependencies`, y `uv sync --frozen` instala el proyecto + dev reproduciblemente

#### Scenario: sin dependencias fantasma

- **WHEN** se audita `dependencies`
- **THEN** cada dependencia de runtime corresponde a un uso actual (`scipy` consumida en `selection.py`/`hrp.py`; la excepción transitoria de feat-018 queda cerrada) y no persiste ninguna excepción temporal
