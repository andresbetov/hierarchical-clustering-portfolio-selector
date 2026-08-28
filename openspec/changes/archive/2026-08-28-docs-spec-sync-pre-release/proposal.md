## Why

El cierre de la Fase A del DAG v0.1.0 (feat-028..030) deja el plano documental desincronizado: la spec merged `configuration-contract` lista 5 métodos sin `hrp` (default desde feat-018), contiene la errata `SHANL`, `numeric-correctness` tiene una doble negación rota, el change archivado feat-018 quedó con tasks sin marcar, no existe CHANGELOG, `progress.md` arrastra secciones duplicadas de sesiones antiguas y la spec `project-packaging` describe un rango de Python que feat-032 va a corregir (3.10 está a EOL en 2026-10-31). Es la feature feat-031 del DAG y cierra CP1 "Estable".

## What Changes

- Corrección de las specs merged: `configuration-contract` (set de 6 métodos con `hrp`; errata `SHANL`), `numeric-correctness` (doble negación), `project-packaging` (rango de Python 3.11-3.13 y matriz CI, en preparación de feat-032).
- Marcado de los boxes de `tasks.md` del change archivado feat-018 (evidencia de cierre retroactiva).
- Creación de `CHANGELOG.md` inicial en formato Keep a Changelog (sección `Unreleased` + `[0.1.0]` placeholder con Added/Changed/Fixed, fechas ISO).
- Limpieza de `progress.md`: un solo bloque "What's Next", sin secciones duplicadas ni restos de sesiones antiguas; `session-handoff.md` ya quedó al día en feat-030.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

(none — cambio puramente documental: las specs se corrigen para reflejar comportamiento YA implementado, no cambia ningún requirement)

## Impact

- Archivos: `openspec/specs/{configuration-contract,numeric-correctness,project-packaging}/spec.md`, `openspec/changes/archive/2026-08-26-feat-018-*/tasks.md`, `CHANGELOG.md` (nuevo), `progress.md`.
- Sin cambios de código, sin dependencias, sin cambios de comportamiento.
