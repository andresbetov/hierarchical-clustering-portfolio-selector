# Design: feat-001-analisis-orden-resolucion

## Context

`docs/auditoria-tecnica.md` §3 inventaria 28 hallazgos con severidad y fix canónico; su §8 propone un roadmap en fases como hipótesis no validada. El código real se restringe a `portfolio_engine/` (core/data/portfolio/viz/app) — todas las aristas verificables viven ahí. Restricción de proceso: un feature activo a la vez (`AGENTS.md`) y verificación única vía `./init.sh`.

## Goals / Non-Goals

**Goals:**
- Derivar el orden por dependencias técnicas reales, no por la agrupación de severidad del inventario (severidad ≠ orden: un CRÍTICO puede depender de un ALTO previo)
- Producir una ordenación total justificada ítem a ítem, executable como cadena de features
- Dejar registro auditable: cada decisión (arista aceptada/rechazada, desempate) con evidencia

**Non-Goals:**
- Estimar esfuerzo/calendario (los features derivados quedan sin estimación)
- Reordenar o editar los hallazgos originales
- Definir implementación técnica de fixes futuros

## Decisions

### D1 — Metodología: topología de deuda + secuenciación por capas
Adoptar el modelo periferia→centro por fan-in (JavaCodeGeeks 2026) combinado con el encadenado Infrastructure→Data→Application (Keyhole 2026): primero verificación/infraestructura, después integridad de datos, luego corrección numérica del dominio, asignación, metodología HRP y por último refactors arquitectónicos protegidos por tests.
*Alternativa descartada*: ordenar por severidad del inventario (atacar C1-C4 primero). Descartada porque C1 (HRP) consume matrices alineadas (A3) y estadísticas con guards (C3): hacerlo primero optimiza sobre datos corruptos.

### D2 — Aristas duras vs blandas
Solo las dependencias duras entran al DAG; las blandas (mismo archivo, conveniencia) se registran como notas sin forzar precedencia. Regla: arista dura ⟺ el consumidor lee datos/comportamiento que el predecesor modifica.

### D3 — Micro-ciclo config↔tests resuelto contract-first
M1 (congelar/config validar) y M8 (tests profundos) tienen apariencia circular: tests quieren API estable, M1 quiere red de seguridad. Se rompe definiendo M1 como hardening de contrato (mantiene accesos a atributos existentes — cambio preservativo) antes de los rewrites que lo consumen (C4, M2, B4); M8 queda después del asentamiento del motor porque sus tests codifican contratos finales. Registre explícitamente esta inversión en el log de desempates.

### D4 — Agrupación contigua en features
Un feature = tramo contiguo de la ordenación total. Garantiza que ningún feature requiera algo fuera de su pasada por `./init.sh` y mantiene 1-feature-a-la-time nativo. Resultado esperado: feat-002..feat-027 (27 features).

## Risks / Trade-offs

- **Subjetividad en desempates**: mitigada con criterio jerárquico fijo (validez > reproducibilidad > mantenibilidad > higiene) y log público de casos
- **DAG sobresimplificado**: 28 nodos con ~35 aristas candidatas; rechazar aristas débiles es parte del deliverable para que el error sea detectable
- **La secuencia puede reordenarse tras feat-002+**: si la ejecución revela dependencia oculta, se actualiza este documento y el tracker en el feature afectado, no retroactivamente en silencio
