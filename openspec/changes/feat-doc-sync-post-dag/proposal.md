# Proposal: feat-doc-sync-post-dag

## Why

El DAG de auditoría está completo (27/27 features mergeados) pero la documentación de entrada aún describe el estado pre-HRP en puntos clave: README asigna pesos "con risk_parity", instruye correr via scripts legacy, oculta filas de configuración nuevas y duplica otra, niega la validación OOS que feat-026 ya entrega; AGENTS.md lista checks obsoletos de init.sh; CONTRIBUTING usa ejemplos muertos; y el decision-log tiene decisiones resueltas sin marcar. Un lector externo recibirá una imagen falsa del producto.

## What Changes

- README: tagline/methodología reflejan HRP jerárquico + distancia firmada + walk-forward; ejecución vía `portfolio-run` + `config/universe.yaml`; tabla de config deduplicada y completa; limitaciones honestas (OOS existe, costos/turnover diferidos); árbol de estructura con módulos nuevos
- AGENTS.md: checks reales de init.sh (sync/pytest/ruff/pyright/compileall); DoD con 4 gates; tagline ajustada
- CONTRIBUTING: ejemplos actualizados (sin `make test once fixed`, sin vol-target, floor 3.10)
- decision-log: banner de completitud + secciones Strangler/prop-test marcadas ejecutadas
- docs históricos (auditoría/orden): SOLO banner de estado no-invasivo al inicio — contenido histórico intacto por regla
- progress.md / session-handoff.md: consolidación final post-DAG

## Capabilities

### New Capabilities
Ninguna — sincronización documental pura sobre capacidades existentes.
