# Proposal: feat-004-quality-gates-ci

## Why

Ningún gate de calidad estático existe: sin lint ni type-check, las regresiones se detectan solo si la suite cubre el camino (y no la cubre — M8 lo documenta). El workflow GitHub definido en CONTRIBUTING no tiene verificación en el servidor: el merge decide un humano, no la evidencia. feat-002/003 dejaron suite y lock determinista; este change añade las capas faltantes del stack 2025 (ruff + pyright + CI) antes de que los features de dominio (C3/C1) necesiten protección real.

## What Changes

- `pyproject.toml`: `[dependency-groups] dev` (ruff, pyright pinned); `[tool.ruff]` (E,F,W,I; line-length 120; excludes caches); `[tool.pyright]` (basic, include src paths)
- `Makefile`: targets `lint` (`uv run ruff check .`) y `types` (`uv run pyright`); help actualizado
- `init.sh`: cuando hay uv, corre lint+types además de pytest — el agente ya no puede declarar done con linters rojos
- `.github/workflows/ci.yml`: push a develop/main y PRs → matriz Python 3.11/3.13 sobre ubuntu-latest: `uv sync --frozen`, ruff, pyright, pytest, compileall
- `.pre-commit-config.yaml`: hooks ruff (+trivial hygiene), instalación local documentada como opt-in
- `CONTRIBUTING.md`: sección Setup gana comandos lint/types; README gana badge CI
- Fuera de scope: reformat masivo (ruff format), endurecer pyright a strict, refactor de código salvo hallazgos triviales

## Capabilities

### New Capabilities
- `quality-gates`: contrato de los gates de calidad estática — qué herramientas corren, contra qué alcance, qué significan sus resultados, dónde deben pasar (local vía init.sh/Makefile y servidor vía CI).

### Modified Capabilities
- `project-packaging`: los manifiestos ahora incluyen grupos de dev-dependencies pinned — la spec existente ("lockfile versionado") cubre implícitamente su reproducibilidad. No cambia requirements observables → solo referencia.

## Impact

- **Artefactos**: pyproject, uv.lock (regenerado por nuevas dev-deps), Makefile, init.sh, ci.yml (nuevo), pre-commit (nuevo), docs
- **Código**: sin cambios lógicos; solo micro-fixes derivados de hallazgos reales de ruff/pyright (registrados)
- **Riesgo**: pyright primera corrida descarga runtime node (one-time); hallazgos reales pueden exceder lo trivial → si ocurren, se pausa y se registra, no se absorbe silenciosamente
