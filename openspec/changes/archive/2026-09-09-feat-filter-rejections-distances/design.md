## Context

Ver `proposal.md`. Estado: feat-043 ya entregó el módulo `report_json.py` (sanitizador, escritor, fingerprint, envelope) con capability `technical-report` viva (4 requirements). El filtro de producción clasifica en este orden exacto (`selection.py:47-63`): sharpe no finito → vol no finita → sharpe < mínimo → vol > máximo; supervivientes pasan. Los motivos solo se loggean, nunca se retornan. Investigación externa aplicada: matriz accept/reject audit-ready con motivos específicos, consistencia (dos tickers que fallan el mismo umbral reciben el mismo motivo) y conteos por etapa (EU JTPF; SFDR audit-trail por decisión; OIG exclusion screening).

## Goals / Non-Goals

**Goals:**

- Clasificación por inferencia pura (sin re-ejecutar el filtro): mismo orden de guardias que `selection.py:47-63`, slugs idénticos, cero duplicación de logs.
- Distancias firmadas exactas con flotantes del config (no re-cortados).
- Prueba de equivalencia con el filtro de producción sobre el panel sintético (la razón derivada == la que `apply_asset_filters` registra).

**Non-Goals:**

- Desambiguar sub-motivos de ingesta (`batch_failed_or_empty` vs `no_usable_prices` de `data_fetch.py:188,193` — solo logs, Single label `ingestion_rejected`).
- Ratios de solape por ticker (capa calendario: `metrics.py:226-239`, propios de otra sección futura del reporte).
- Integración en pipeline/CLI (feat-050). Cambios en `selection.py`/`data_fetch.py`.

## Decisions

- **Inferencia pura sin re-ejecutar `apply_asset_filters`** (enmienda del reviewer aplicada parcialmente): el orden de guardias es determinista y esta función lo replica; re-ejecutar duplicaría el warning `selection.py:69-73` en cada corrida con exclusiones. El contrato exige equivalencia de razón (test), que es la garantía real contra drift. Alternativa descartada: parámetro `info` opcional en `apply_asset_filters` — rompería la firma usada por walk-forward (`walk_forward.py:135-140`) y los 15+ call-sites de tests.
- **`closing_prices` en la firma** (según registro del épico): usada para el guard de ingesta (ticker pedido sin métricas y sin precios = `ingestion_rejected`); mantiene la firma del tracker estable para feat-050.
- **Distancias como flotantes firmados exactos, no banderas**: `|d| < 0.05` ("casi pasa") es criterio de lectura del catálogo §3, no un campo extra — el consumidor lo computa; duplicarían información.
- **Métrica no finita → ambas distancias `null`** (no solo la correspondiente): el catálogo §3 define "métricas no finitas sin distancia (categoría propia)"; mezclar una distancia finita con un motivo no-finito invitaría a leer holgura donde no la hay.

## Risks / Trade-offs

- [Riesgo] Drift entre la inferencia y el filtro real si `apply_asset_filters` cambia su orden → Mitigación: test de equivalencia con panel sintético (razón derivada == razón loggeada, pinnings exactos por slug); si el filtro cambia, este test grita antes que el JSON mienta.
- [Trade-off] `ingestion_rejected` no distingue causa de ingesta → asumido: los sub-motivos son log-only y fabricarlos aquí sería inventar datos; documentado como Non-goal.
- [Riesgo] Cobertura: ramas nuevas (7 motivos) cubren ~100% con TDD → TOTAL % debe sostenerse o subir (baseline 85.60%).

## Migration Plan

1. En la rama `feat/filter-rejections-distances` (ya creada con feat-044 in-progress): TDD rojo → implementación → verde → trackers en la rama → commit.
2. Rollback: revert de 1 función + tests + export; additive puro.

## Open Questions

Ninguna: firma, slugs y política de distancias quedaron bloqueados en el registro del épico y confirmados contra `selection.py:47-63`.
