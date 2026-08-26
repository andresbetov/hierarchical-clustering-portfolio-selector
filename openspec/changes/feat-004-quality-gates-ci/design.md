# Design: feat-004-quality-gates-ci

## Context

Stack actual tras feat-002/003: suite real (16 passed), lock universal versionado, Python 3.10+. El código tiene deuda tipada histórica (funciones sin anotar, numba) — el gate debe nacer verde sin reescribirlo (lección del fan-in: tocar centro sin red = riesgo).

## Goals / Non-Goals

**Goals:** gates verdes hoy, ejecución automática local+CI, toolchain reproducible, hallazgos reales documentados.
**Non-Goals:** ruff format masivo, pyright strict, refactor de dominio, cobertura de tests (M8/feat-021).

## Decisions

### D1 — Rort selecion de reglas pragmática
`select = ["E","F","W","I"]` + line-length 120 (respeta estilo existente). Excluye: `ruff format` (reescribiría ~900 líneas = contaminación del diff de M9); UP/SIM/B (cientos de fixes, otro feature). Endurecer queda registrado como progresión futura.
*Alternativa descartada*: estricto-inmediato — el gate que falla constantemente se ignora en dos sprints.

### D2 — pyright basic + include acotado
`include=["portfolio_engine","scripts"]`; tests fuera por diseño: los fixtures pytest generan ruido no accionable en basic y su calidad se aborda en feat-021. Stub-less deps (yfinance) fluyen como Any — aceptado explícitamente.

### D3 — init.sh extiende su contrato
Los cuatro gates corren secuencialmente con fail-fast (`set -e`). pyright one-time descarga node (~1 vez por entorno); costo justificado porque es EL comando anti-"done falso" del harness. Makefile expone cada gate individualmente para debugging.

### D4 — CI matrix 3.11+3.13 sin sesgo de desarrollo
Dos puntos cubren ambas líneas base del rango 3.10-3.13+. setup-uv@v6 official action; steps orderados sync-frozen → lint → types → test → compileall (falla rápido en lo barato primero).

### D5 — Pre-commit opt-in
`.pre-commit-config.yaml` versión-pinned de mirrors-ruff + hygiene básica; docs explican `pre-commit install`. CI es la autoridad; pre-commit es conveniencia local.

## Risks / Trade-offs

- Hallazgos reales al correr linters primera vez → si triviales, fix + registro; si estructurales, pausa y escalar (guardrail apply)
- Lock crece (tools transitive deps) → aceptado: determinismo > ligereza
- pyright bajo pytest/nodes ausente en runner se resuelve solo (pip package embebe node)
