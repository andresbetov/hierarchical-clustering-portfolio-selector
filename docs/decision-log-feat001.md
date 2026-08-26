# Decision Log — feat-001 (contexto para feat-002..027)

**Creado:** 2026-08-26 · **Propósito:** preservar decisiones y opciones evaluadas durante el análisis de ordenamiento que NO quedaron en disco (viven/vivían solo en la sesión conversacional). Es complemento de:
- `docs/auditoria-tecnica.md` (hallazgos y fixes canónicos)
- `docs/orden-de-resolucion.md` (DAG con aristas file:line y rechazadas §3.2)
- `openspec/changes/archive/2026-08-26-feat-001-analisis-orden-resolucion/design.md` (D1-D4)

## ⚠️ Regla de citación

Las citas `file:line` de los documentos anteriores se basan en el árbol de `develop@d55c2d5`. Los primeros features las harán rotir. Al proponer cualquier feature posterior: **citar funciones/módulos, no números de línea**, releer el código actual y nunca copiar líneas del archive sin verificar.

## Opciones evaluadas que NO están en disco

### Para feat-018 (Real HRP) — decisión NO final hasta su ADR
- **scipy vs riskfolio-lib**: se evaluó internamente usar `riskfolio-lib`. Se descartó *para empezar* porque: añade dependencia pesada, `scipy` ya está declarado en pyproject (pasaría de fantasma a usado), y el control fino de los 3 pasos (linkage→quasiDiag→recBipart) sirve como aprendizaje verificable contra la literatura. **Opción válida a re-abrir** si scipy da problemas de dendrograma/linkage custom.
- **Formas de quasi-diagonalization**: variante bisection-split vs dendrogram-split del split factor (Palomar 12.3 documenta ambas). Sin decisión aún — resolver en design de feat-018, bias inicial hacia bisection-split (De Prado clásico).
- **Linkage default**: single (De Prado original). Ward/completa quedan como parámetro comparativo, no como primera implementación.

### Racional para feat-016 (distancia de correlación) — argumento a conservar
`d = sqrt(0.5*(1-corr))` firmada probablemente CORRECTA: correlación negativa es diversificadora y debe *separar* activos en el dendrograma. La actual `1-abs(corr)` (metrics.py `compute_correlation_distance_matrix`) trata -0.9 como cercano, lo cual contradice la tesis de diversificación del README. El ADR debe partir de este análisis, no desde cero.

## Registro de decisiones diferidas (where-decide)

| Feature | Decisión pendiente | Alternativas |
|---|---|---|
| feat-015 | vol-target implementar o eliminar | eliminar = config honesta mínima; escalar = más representable; decidir por complejidad marginal |
| feat-016 | distancia firmada vs abs | ver racional arriba; exponer parametrizada |
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
