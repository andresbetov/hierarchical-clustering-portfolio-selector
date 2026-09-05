## MODIFIED Requirements

### Requirement: Dependencias justificadas
Cada dependencia de runtime SHALL corresponder a un uso actual del código o a un feature inmediato del DAG que la consumirá; la condición de "fantasma" SHALL documentarse como excepción temporal, no persistir. Herramientas de dev/test (pytest, pytest-cov, ruff, pyright, hypothesis) SHALL vivir exclusivamente en `[dependency-groups].dev` y SHALL NOT aparecer en `[project].dependencies`.

#### Scenario: dependencias dev aisladas
- **WHEN** se inspecciona `pyproject.toml` tras el change
- **THEN** `pytest` y `pytest-cov` están en `[dependency-groups].dev` y no en `[project].dependencies`, y `uv sync --frozen` instala el proyecto + dev reproduciblemente

#### Scenario: scipy en transición
- **WHEN** se audita `dependencies` durante este change
- **THEN** `scipy` permanece con su consumo previsto registrado (feat-018 HRP) — única excepción permitida hasta ese feature
