# verification-harness Specification (delta)

## Purpose

Garantizar que el proyecto tenga un comando único de verificación confiable: `make test` ejecuta la suite offline real del proyecto y `init.sh` la incorpora cuando el entorno lo permite, de modo que ningún cambio se marque done sin evidencia ejecutada.

## ADDED Requirements

### Requirement: Target test ejecuta la suite real

El target `test` del Makefile SHALL ejecutar pytest sobre la suite offline declarada en `tests/` y SHALL NO referenciar archivos inexistentes.

#### Scenario: make test con suite presente
- **WHEN** un desarrollador ejecuta `make test` en un entorno sincronizado (deps instaladas)
- **THEN** pytest corre los tests de `tests/` y el exit code refleja su resultado real (0 verde, distinto de 0 si fallan)

### Requirement: Configuración explícita de testpaths

La configuración de pytest SHALL declarar explícitamente `testpaths = ["tests"]` desde `pyproject.toml`, evitando descubrimiento accidental fuera de la suite.

#### Scenario: Invocación directa de pytest
- **WHEN** cualquiera ejecuta `uv run pytest` sin argumentos
- **THEN** solo se recolectan tests bajo `tests/`

### Requirement: init.sh prefiere el intérprete del proyecto

Cuando `uv` está disponible, `init.sh` SHALL ejecutar pytest vía `uv run pytest`; el chequeo con python3 del sistema queda como fallback exclusivo de entornos sin uv. La ausencia total de tests (exit 5) SHALL seguir tratándose como no-fallo para bootstrap.

#### Scenario: uv disponible
- **WHEN** `uv sync` instaló pytest en `.venv` y se ejecuta `./init.sh`
- **THEN** la suite corre vía `uv run pytest` y el output muestra resultados reales de tests, no el salto "pytest not installed"

#### Scenario: sin uv y sin pytest del sistema
- **WHEN** el entorno no tiene uv ni pytest instalable
- **THEN** init.sh continúa con compileall y termina exit 0 (comportamiento bootstrap preservado)
