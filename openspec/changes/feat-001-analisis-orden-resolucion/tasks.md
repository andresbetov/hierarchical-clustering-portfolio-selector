# Tasks: feat-001-analisis-orden-resolucion

## 1. Construcción del grafo de dependencias

- [x] 1.1 Listar los 28 hallazgos como nodos y catalogar aristas candidatas (de auditoría §8 hipótesis + análisis de código); verificar cada arista con evidencia `file:line`; registrar aristas rechazadas por cercanía temática sin dependencia real — verificar: tabla en docs/orden-de-resolucion.md §3
- [x] 1.2 Detectar ciclos/dependencias bidireccionales; resolver el micro-ciclo M1↔M8 con inversión contract-first (design D3) — verificar: sección "verificación anti-ciclos" con método documentado

## 2. Ordenamiento topológico y desempates

- [x] 2.1 Ejecutar ordenamiento topológico del DAG validado contra capas Infraestructura→Datos→Dominio→Asignación→Metodología→Arquitectura→Validación — verificar: ordenación total 1..28 válida
- [x] 2.2 Resolver pares intercambiables con criterio de trascendencia (validez > reproducibilidad > mantenibilidad > higiene) y registrar cada desempate con caso concreto — verificar: log de desempates ≥4 casos en §5

## 3. Artefacto principal

- [x] 3.1 Escribir `docs/orden-de-resolucion.md`: DAG mermaid, tabla hallazgo→predecesores→sucesores→justificación, secuencia total numerada con justificación ítem a ítem ("X antes que Y porque Z"), verificación de cobertura 28/28 — verificar: documento completo y contrastable contra auditoría §3
- [x] 3.2 Registrar secuencia en `feature_list.json` como feat-002..feat-027 con dependencies explícitas hacia ids previos y descripción del tramo que cubre cada uno — verificar: JSON válido, deps solo hacia anteriores, cobertura exacta 28 hallazgos

## 4. Cierre de sesión

- [x] 4.1 Actualizar `progress.md` (Current State, What's Done = feat-001 con evidencia, What's Next = feat-002) y `session-handoff.md` — verificar: ambos archivos reflejan la secuencia aprobada
- [x] 4.2 Ejecutar `./init.sh` en esta sesión justo antes de marcar done; exit 0; capturar output como evidence en tracker; commits convencionales en rama `feat/resolution-order-analysis` — verificar: output init.sh + git log limpio

## 5. Definition of Done (gate)

- [x] 5.1 Los 28 hallazgos aparecen exactamente una vez en la ordenación; toda arista cita file:line; sin ciclos; desempates justificados; init.sh fresco verde; repo reiniciable — verificar: checklist cruzado vs specs/resolution-planning
