# project-packaging Specification

## Purpose
Garantizar que los manifiestos del proyecto declaren identidad, rango de intérpretes y dependencias de forma honesta y reproducible: clonar el repo y sincronizar debe producir el mismo entorno en cualquier máquina soportada.

## Requirements

### Requirement: Identidad coherente

El `name` del paquete en `pyproject.toml` SHALL coincidir con el nombre del repositorio, para que herramientas de distribución, entrypoints futuros y CI no requieran mapeos especiales.

#### Scenario: Identidad verificable
- **WHEN** se inspecciona pyproject.toml tras el change
- **THEN** el name es `hierarchical-clustering-portfolio-selector`

### Requirement: Lockfile versionado

`uv.lock` SHALL estar bajo control de versiones y SHALL NO figurar en `.gitignore`; `uv sync --frozen` SHALL reproducir el entorno declarado.

#### Scenario: Entorno determinista
- **WHEN** un clon limpio ejecuta `uv sync --frozen`
- **THEN** la instalación resuelve exactamente las versiones del lock sin reclaculación

### Requirement: Rango de Python honesto

`requires-python` SHALL declarar un piso alcanzable por CI estándar (`>=3.11` — Python 3.10 alcanza EOL 2026-10-31 y el ecosistema científico lo retira por SPEC 0) y la matriz de CI SHALL cubrir 3.11-3.13; el lockfile SHALL ser válido para todo el rango declarado.

#### Scenario: Resolución universal
- **WHEN** se regenera `uv.lock` con el nuevo `requires-python`
- **THEN** la resolución cubre 3.11-3.13 y la suite pasa en el intérprete local

### Requirement: Dependencias justificadas

Cada dependencia de runtime SHALL corresponder a un uso actual del código o a un feature inmediato del DAG que la consumirá; la condición de "fantasma" SHALL documentarse como excepción temporal, no persistir.

#### Scenario: scipy en transición
- **WHEN** se audita `dependencies` durante este change
- **THEN** `scipy` permanece con su consumo previsto registrado (feat-018 HRP) — única excepción permitida hasta ese feature
