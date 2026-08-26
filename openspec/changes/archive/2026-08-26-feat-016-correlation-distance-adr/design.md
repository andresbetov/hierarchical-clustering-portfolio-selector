# Design: feat-016-correlation-distance-adr

## Context

Dependencia del DAG: M2 debe decidirse ANTES de C1 (feat-018 consume la métrica). Config frozen ya estable (feat-013). Correlaciones contienen NaN legítimos (feat-009): el kernel los propaga sin branch especial — comparaciones con NaN son False en numba y sqrt(1-nan)=nan.

## Goals / Non-Goals

**Goals:** métrica paramétrica; default signed; umbral semánticamente estable entre modos; tests pin de comportamiento.
**Non-Goals:** reescribir clustering greedy (feat-018 lo sustituye por HRP real); otras métricas (angular/entropy → decisión-log si surgen).

## Decisions

### D1 — Signed como default
Teoría: diversificación = separar fuentes de riesgo comunes; |corr| trata un hedge perfecto como gemelo. ADR 002 documenta contra-argumento (estabilidad histórica) y lo rechaza para código pre-1.0 de investigación donde la corrección metodológica manda.
*Alternativa descartada:* abs default "por compatibilidad" — congela el defecto semántico que el feature existe para corregir.

### D2 — Umbral convertido, no expuesto crudo
Fórmulas: signed t_d=sqrt(0.5(1-t)); abs t_d=1-t. Función pura `_resolve_distance_threshold(threshold, metric)` testeable. UX intacta: el usuario sigue pensando en correlaciones.

### D3 — Flag entero dentro del kernel numba
Strings vía argumento funcionan en numba moderno pero int es universal y evita overhead. Wrapper hace el mapping desde str.

## Risks / Trade-offs

- Portfolios previos cambian composición al regenerar — esperado y motivo del cambio
- Threshold equivalente en signed es más conservador (fusiona menos) → carteras con más activos típicamente; comportamiento superior para diversificación
