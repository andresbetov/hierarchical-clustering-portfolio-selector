# Proposal: feat-025-docs-consolidation-adrs

## Why

Tres ADRs ya emitidos (001-004) viven en `docs/adr/` sin índice navegable; el README no menciona el pipeline HRP default ni los solvers estables; y la coherencia de idioma declarada en `openspec/config.yaml` (artifacts en es) convive con READMEs mixtos. B3 consolida documentación para lectores externos.

## What Changes

- `docs/adr/README.md`: índice de ADRs con estado y resumen de una línea
- `README.md`: sección Metodología actualizada (HRP default, distancia firmada, annualización paramétrica); fila `distance_metric` añadida a tabla de configuración; enlace a ADRs
- `CONTRIBUTING.md`: referencia a ADR como vehículo de decisiones metodológicas
- Fuera de scope: traducción completa del código a español (los identifiers permanecen en inglés — convención), CHANGELOG generado (diferido hasta primera release tag)

## Capabilities

### New Capabilities
Ninguna — consolidación documental sobre capacidades existentes.
