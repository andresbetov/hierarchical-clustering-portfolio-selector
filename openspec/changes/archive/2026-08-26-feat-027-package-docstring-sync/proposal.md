# Proposal: feat-027-package-docstring-sync

## Why

B7 cierra el DAG: docstrings y superficie exportada deben reflejar la arquitectura final (HRP default, provider seam, capas validation/universe). El `__init__.py` carece de docstring de paquete; módulos clave describen estado pre-feat-018.

## What Changes

- `portfolio_engine/__init__.py`: docstring de paquete (qué es, método default, cómo correr, link ADRs); exportar `calculate_hrp_weights`, `load_universe`, `walk_forward_evaluate`
- Docstrings sincronizados en `data_fetch.py` (batch flow), `hrp.py` ya correcto, `selection.py` nota legacy-path
- Fuera de scope: traducciones, restructuring

## Capabilities

### Modified Capabilities
- `package-interface`: la docstring del paquete es parte del contrato de onboarding — debe reflejar defaults reales.
