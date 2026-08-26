# Design: feat-003-project-manifests-lockfile

## Context

feat-002 dejó la suite real (16 passed) como red de verificación. El lock actual se resolvió bajo `requires-python>=3.13`; bajar el piso a 3.10 fuerza re-resolución universal. Entorno local: Python 3.14 del sistema vía uv-managed venv.

## Goals / Non-Goals

**Goals:** identidad honesta, lock determinista versionado, piso 3.10 sin romper la suite local.
**Non-Goals:** entrypoints (feat-006), CI matrix real (feat-004 decidirá 3.10-3.12 runners), pruning numba (feat-022), charts/.gitignore D5.

## Decisions

### D1 — scipy se mantiene como excepción documentada
Quitarla obligaría a re-resolver el lock ahora y otra vez en feat-018 (churn doble); la spec `project-packaging` permite una única excepción con consumo previsto registrado.
*Alternativa descartada*: dependencias-sync estricto — deja feat-018 con re-lock redundante.

### D2 — piso 3.10, lock universal
`uv` resuelve locks válidos para todo el rango declarado; la suite corre en el intérprete local y feat-004 añadirá la matriz real de CI. No fijamos `uv python pin` (innecesario: resolución universal ya cubre).

### D3 — verificación mínima del re-lock
Gate: `uv sync --frozen` tras regenerar + `make test` 16 passed + `./init.sh` exit 0. Si numba/matplotlib cambian de versión mayor en la nueva resolución para cubrir 3.10, la suite delata regresiones de import/behavior básicas; kernels pesados siguen siendo riesgo conocido (feat-022).

## Risks / Trade-offs

- Lock más conservador (versiones compatibles con 3.10) puede bajar pins vs los actuales de 3.13 → aceptado; determinismo > novedad
- `uv sync --frozen` fallará si alguien edita pyproject sin re-lock: comportamiento deseado (protege el contrato)
