# AGENTS.md

Harness para desarrollo asistido por agentes en `hierarchical-clustering-portfolio-selector` — pipeline cuantitativo Python (clustering jerárquico con distancia firmada + asignación Hierarchical Risk Parity por defecto).

## Startup Workflow

Antes de escribir código:

1. **Confirmar directorio** con `pwd` (raíz del repo)
2. **Leer este archivo** completo
3. **Leer docs del proyecto**: `README.md`, `CONTRIBUTING.md` y `openspec/config.yaml` si existe un change activo
4. **Ejecutar `./init.sh`** y confirmar que pasa; si falla, reparar el entorno antes de añadir scope
5. **Leer `feature_list.json`** para ver el feature activo y su Definition of Done
6. **Revisar commits recientes** con `git log --oneline -5` y `git branch --show-current` (debe ser una rama desde `develop`)

## Working Rules

- **Un feature a la vez / One feature at a time**: toma exactamente un feature en `not-started`/`in-progress` de `feature_list.json`; no abras segundo sin cerrar el anterior
- **Verificación obligatoria — evidencia fresca**: no marques done sin haber ejecutado `./init.sh` (o los comandos de la sección Verification) **en esta misma sesión, justo antes de marcar done**. "Pasó hace 2 horas" no es evidencia.
- **Actualizar artefactos**: antes de cerrar sesión, actualiza `progress.md` y `feature_list.json` (y `session-handoff.md` si la sesión es larga)
- **Mantener scope**: no modifiques archivos ajenos al feature activo; si surge otro hallazgo, regístralo en `progress.md` → Blockers/Risks y proponlo como siguiente feature
- **Flujo Git**: ramas desde `develop` (`feat/` `fix/` `chore/` `docs/` `refactor/`), PR hacia `develop`, squash merge, borrar rama tras merge. `develop` → `main` solo cuando lo indique el usuario (`CONTRIBUTING.md`)
- **OpenSpec cuando aplique**: si el feature tiene `openspec/changes/<id>/`, `tasks.md` es el checklist; `feature_list.json` refleja el estado de ejecución
- **Dejar estado limpio**: la siguiente sesión debe poder ejecutar `./init.sh` sin pasos manuales

## Required Artifacts

- `feature_list.json` — tracker de features (source of truth de estado)
- `progress.md` — log de continuidad entre sesiones
- `init.sh` — entrypoint único de verificación (tests + compile check)
- `session-handoff.md` — handoff para sesiones largas (opcional)
- `CONTRIBUTING.md` — workflow Git y Conventional Commits
- `openspec/` — specs y changes cuando el feature requiere diseño previo

## Definition of Done

Un feature está done solo cuando todo esto es cierto:

- [ ] Comportamiento objetivo implementado y acotado al scope del feature
- [ ] Verificación ejecutada **en esta sesión** y en verde: `./init.sh` (lint + types + pytest + compileall) — output registrado en `feature_list.json:evidence` o `progress.md`
- [ ] `feature_list.json` actualizado a `done` con evidencia y sin dependencias pendientes
- [ ] `progress.md` y `session-handoff.md` al día
- [ ] Repo reiniciable: `git status` limpio salvo artefactos intencionales y `./init.sh` pasa de nuevo

## End of Session

Antes de cerrar:

1. Actualizar `progress.md` (Current State, What's Done/In Progress/Next, Evidence)
2. Actualizar `feature_list.json` (status + evidence del feature)
3. Si aplica, actualizar `session-handoff.md` con blockers, archivos tocados y siguiente paso recomendado
4. Commit con mensaje Conventional Commits en la rama del feature
5. Dejar el repo de forma que `./init.sh` pase inmediatamente

## Verification Commands

```bash
# Verificación completa (recomendado) — úsalo al inicio y justo antes de marcar done
./init.sh
```

Checks que ejecuta `init.sh` (en este orden, fail-fast):

- `uv sync` — sincroniza deps desde lock versionado
- `uv run python -m pytest || [ $? -eq 5 ]` — suite offline (exit 5 = sin tests, no es fallo)
- `uv run ruff check .` — lint estático
- `uv run pyright` — type-check básico
- `python3 -m compileall -q ...` — chequeo de sintaxis

Sin `uv` disponible degrada a fallbacks documentados dentro del propio script.

Alternativa directa: `make lint && make types && make test`.

## Escalation

- **Decisión arquitectónica** (ej. cambiar fuente de datos, introducir optimizador convexo, exponer API): consulta `README.md: Metodología` y `CONTRIBUTING.md`; si es cross-cutting y reversible, propone ADR u OpenSpec `design.md` antes de implementar
- **Requisito ambiguo**: revisa `openspec/specs/` y `README.md: Como interpretar los resultados`; si sigue ambiguo, pregunta al usuario
- **Tests fallando repetidamente**: registra en `progress.md` → Blockers/Risks, marca el feature `blocked` y pide revisión humana
- **Ambigüedad de scope**: relee `feature_list.json` (description + dependencies) y el `tasks.md` del change si existe

## Límites explícitos

- **C4 diagrams**: no se usan en este repo (pipeline estático sin boundaries app/components ni decisión static/SSR). Solo introducir si se discute arquitectura de despliegue o separación app/components real.
- **ADRs**: solo para una decisión arquitectónica reversible y con alternativas (ej. `yfinance` vs otra fuente, `risk_parity` vs `max_sharpe`). No para detalles transitorios (color de botón, nombre de variable).
