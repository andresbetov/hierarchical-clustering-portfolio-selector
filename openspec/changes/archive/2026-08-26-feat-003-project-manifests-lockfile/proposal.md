# Proposal: feat-003-project-manifests-lockfile

## Why

Tres defectos de manifiesto bloquean reproducibilidad y packaging (auditoría B1+A6): `uv.lock` está en `.gitignore` así que ningún entorno es determinista; el paquete se llama `xai-financial-predictor-engine` cuando el repo es `hierarchical-clustering-portfolio-selector`; y `requires-python>=3.13` excluye los intérpretes estándar de CI (3.10-3.12). Con la suite real verde (feat-002), este es el momento seguro para tocar manifiestos.

## What Changes

- `.gitignore`: eliminar la línea `uv.lock` y versionar el lockfile
- `pyproject.toml`: name → `hierarchical-clustering-portfolio-selector`; `requires-python = ">=3.10"`
- `uv.lock`: regenerado para el nuevo rango de Python (`uv lock` + `uv sync`)
- Fuera de scope: `[project.scripts]` (feat-006), configs ruff/pyright/CI (feat-004), eliminar `numba` (feat-022)

## Capabilities

### New Capabilities
- `project-packaging`: contrato de identidad y entorno del proyecto — nombre coherente con el repo, rango de Python soportado declarado honestamente, lockfile versionado como fuente de entornos deterministas, dependencias declaradas justificadas.

### Modified Capabilities
Ninguna.

## Impact

- **Artefactos**: .gitignore, pyproject.toml, uv.lock (nuevo en control de versiones)
- **Código**: sin cambios; suite debe seguir 16 passed tras regenerar resolución
- **Riesgo medio**: cambiar el piso de Python invalida la resolución previa — mitigado con re-lock + suite completa como gate; numba/matplotlib pueden resolver versiones distintas para cubrir 3.10
