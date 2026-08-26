# Proposal: feat-001-analisis-orden-resolucion

## Why

`docs/auditoria-tecnica.md` inventaria 28 hallazgos (C1-C4, A1-A7, M1-M10, B1-B7) pero no define en qué orden resolverlos ni por qué ese orden. La literatura de secuenciación (topología de deuda técnica por fan-in, Keyhole Infrastructure→Data→Application, WSJF/RIVER) demuestra que resolver deuda en orden incorrecto amplifica inestabilidad en vez de reducirla: cambiar un componente central sin red de verificación previa garantiza regresiones ocultas. Antes de ejecutar cualquier fix, el proyecto necesita la secuencia justificada como artefacto verificable.

## What Changes

- Crear `docs/orden-de-resolucion.md`: DAG de dependencias entre los 28 hallazgos (aristas verificadas con evidencia `file:line`), secuencia cronológica total 1..28 con justificación por ítem, log de desempates y verificación de ausencia de ciclos.
- Registrar la secuencia resultante en `feature_list.json` como `feat-002`..`feat-027`, cada uno con campo `dependencies` explícito apuntando a ids previos.
- Actualizar `progress.md` y `session-handoff.md` con la secuencia aprobada como What's Next.
- No se modifica ningún código de producto (`portfolio_engine/`) — este change es exclusivamente de planificación.

## Capabilities

### New Capabilities
- `resolution-planning`: capacidad de planificación de resolución que define cómo se deriva, verifica y registra el orden de ejecución de hallazgos de auditoría. Cubre: reglas de dependencia (arista solo si es dependencia técnica real), criterio de desempate por trascendencia, validez del DAG y trazabilidad hacia features ejecutables.

### Modified Capabilities

Ninguna — no hay specs existentes bajo `openspec/specs/`.

## Impact

- **Artefactos**: +3 (`docs/orden-de-resolucion.md`, delta spec de `resolution-planning`, entradas feat-002+ en tracker)
- **Código de producto**: sin cambios
- **Riesgo**: bajo — solo planificación; el riesgo principal (orden erróneo) es precisamente lo que mitiga
- **Siguiente fase**: `feat-002` arranca la Fase Higiene del roadmap de auditoría

## Non-goals

- Implementar cualquier fix de los hallazgos C/A/M/B
- Reescribir `docs/auditoria-tecnica.md` (solo referenciarlo)
- Elegir stack o dependencias nuevas (decisión de cada feature futuro)
