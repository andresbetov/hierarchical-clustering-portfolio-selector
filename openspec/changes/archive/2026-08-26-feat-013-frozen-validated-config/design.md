# Design: feat-013-frozen-validated-config

## Context

Último feature antes del bloque metodológico (M2→C1). Todo consumidor accede por atributo; el fixture mutante de integración es el único escritor conocido.

## Goals / Non-Goals

**Goals:** frozen dataclass API-preservante; validación completa al construir; dispatch sin fallback; fixtures migradas.
**Non-Goals:** YAML/env loading (Fase 4); nuevos campos (M2/B4 los añaden sobre este contrato); pydantic (peso injustificado).

## Decisions

### D1 — dataclass stdlib con __post_init__
10 campos, reglas simples: validación explícita legible supera magia de librerías. Mensajes de error nombran campo+valor+regla.
*Alternativa descartada:* pydantic v2 — startup cost y modelo de errores distinto para beneficio que no se ejerce aún.

### D2 — Enum cerrado de métodos con tupla pública
`WEIGHT_ALLOCATION_METHODS` como constante pública de módulo (documentación ejecutable y reutilizable por CLI futuro).

### D3 — Eliminar else-fallback en dispatcher
Cambiar except-branch por exhaustiva if/elif sobre enum. Si mañana se añade método nuevo, la config lo valida y el dispatcher lo incorpora explícitamente — sin rutas muertas.

## Risks / Trade-offs

- Scripts/tests legacy que mutaban configuración fallarán — exactamente el contrato; único caso en repo es el fixture de integración
- Frozen no previene mutar arrays contenidos (no hay) ni swap completo vía replace (dataclasses.replace crea nueva instancia → patrón legal para overrides)
