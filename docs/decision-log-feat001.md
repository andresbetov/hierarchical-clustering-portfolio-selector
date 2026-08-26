# Decision Log — feat-001 (contexto para feat-002..027)

**Creado:** 2026-08-26 · **Propósito:** preservar decisiones y opciones evaluadas durante el análisis de ordenamiento que NO quedaron en disco (viven/vivían solo en la sesión conversacional). Es complemento de:
- `docs/auditoria-tecnica.md` (hallazgos y fixes canónicos)
- `docs/orden-de-resolucion.md` (DAG con aristas file:line y rechazadas §3.2)
- `openspec/changes/archive/2026-08-26-feat-001-analisis-orden-resolucion/design.md` (D1-D4)

## ⚠️ Regla de citación

Las citas `file:line` de los documentos anteriores se basan en el árbol de `develop@d55c2d5`. Los primeros features las harán rotir. Al proponer cualquier feature posterior: **citar funciones/módulos, no números de línea**, releer el código actual y nunca copiar líneas del archive sin verificar.

## Opciones evaluadas que NO están en disco

### Para feat-018 (Real HRP) — ✅ RESUELTO en ADR 003 (2026-08-26)
- **scipy implementación propia** elegida (riskfolio-lib sigue descartado; puerta abierta si n>400 exige perf).
- Quasi-diag por expansión recursiva del árbol; bisección-split clásico.
- Linkage 'single' hardcodeado — Ward/completa diferidas como parámetros comparativos futuros.
- Ver también docs/adr/003-hrp-adoption.md.

### Racional para feat-016 (distancia de correlación) — argumento a conservar
`d = sqrt(0.5*(1-corr))` firmada probablemente CORRECTA: correlación negativa es diversificadora y debe *separar* activos en el dendrograma. La actual `1-abs(corr)` (metrics.py `compute_correlation_distance_matrix`) trata -0.9 como cercano, lo cual contradice la tesis de diversificación del README. El ADR debe partir de este análisis, no desde cero.

## Registro de decisiones diferidas (where-decide)

| Feature | Decisión pendiente | Alternativas |
|---|---|---|
| feat-015 | vol-target implementar o eliminar | ✅ ELIMINAR (ADR 001): incompatible con mandato long-only fully-invested |
| feat-016 | distancia firmada vs abs | ✅ SIGNED default (ADR 002, PR #20) |
| feat-018 | biblioteca / variante quasiDiag | ver opciones arriba |
| feat-019 | solve/pinv/LedoitWolf | shrinkage primero (cov ruidosa es raíz de sensibilidad HRP según Trucíos 2026) |
| feat-021 | librería prop tests | hypothesis; pytest-mock para fetcher |

## Bordes de módulos tentativos para feat-023 (Strangler)

Sketch no escrito en ningún design anterior:
1. `DataProvider` Protocol con método `fetch(universe, lookback) -> AlignedPrices`
2. Después separar `domain/` (metrics+selection+allocation puros, sin IO ni matplotlib)
3. Último mover `viz/` detrás de interfaz Reporter; app queda como composición
4. Cada paso tras tests de caracterización de feat-021 — no antes

---
*Actualizable en cada feature: agregar filas a where-decide cuando surjan nuevas decisiones diferidas.*
