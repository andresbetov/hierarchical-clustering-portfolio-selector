## Context

Ver `proposal.md`. Estado: módulo `report_json.py` con sanitizador/escritor/fingerprint/envelope (feat-043) y diagnóstico de exclusiones (feat-044); capability `technical-report` con 5 requirements vivos. Seams del motor verificados: `create_portfolio_covariance_matrix` (`allocation.py:13-31`, solo usa `.keys()` de los dicts), `calculate_portfolio_variance` (`allocation.py:34-35`), `_resolve_effective_bounds` (`allocation.py:203-230`, loggea CRITICAL al relajar), `calculate_hrp_weights` (`hrp.py:93-166`, determinista, n=1→[1.0] sin linkage), `VOL_FLOOR_EPS` (`metrics.py:19`), tolerancia de suma `_WEIGHT_SUM_TOLERANCE=1e-9` (`config.py:35`). Fuente externa aplicada: fórmulas DR/RC/HHI con guards numéricos (patrón DiversificationAnalyzer: port_vol==0 → DR 1.0/RC zeros — aquí más estricto: None honesto según catálogo §6).

## Goals / Non-Goals

**Goals:**

- Función pura sin entanglement de pipeline/CLI; reutilizar los 4 seams probados del motor (single source, cero duplicación de fórmulas).
- Rebanado de covarianza SIEMPRE por nombres de ticker (invariancia de orden garantizada, regla feat-028).
- Telemetría Dykstra honesta: recompute bit-idéntico solo donde es posible; None+razón donde no.

**Non-Goals:**

- ENB por PCA (§10 del catálogo: primer O(N³), sin accionabilidad).
- Cambios en `allocation.py`/`hrp.py`/`config.py`; exposición de vectores crudos legacy.
- Integración pipeline/CLI (feat-050); DR/RC por fold de walk-forward.

## Decisions

- **Parámetro `covariance_tickers` añadido a la firma** (enmienda del registro del épico): para rebanar por nombres se necesita el orden de filas de la covarianza; sin él, la ruta legacy M<N sería indefendible. Firma: `allocation_diagnostics(weights, covariance_matrix, covariance_tickers, config, raw_weights=None)`. El tracker se enmienda con la nota.
- **Rebanado reutilizando `create_portfolio_covariance_matrix`** (patrón feat-028, single source): se le llama con los pesos como `optimal_portfolio` y un dict sintético `{t: None}` en orden `covariance_tickers` (la función solo usa `.keys()`). Alternativa inline `np.ix_` descartada: duplicaría la lógica de slice ya testada. Error nombrado si un ticker de pesos no está en `covariance_tickers`.
- **Semántica de `raw_weights`**: provisto → se usa para CUALQUIER método (el caller es la fuente honesta); None + método `hrp` → recompute determinista `calculate_hrp_weights(cov_usada, linkage_method)` (bit-idéntico al motor por ser puro y determinista — pin de test); None + no-HRP → `None` (el vector pre-Dykstra legacy no está expuesto; fabricarlo es deshonesto). Si el método es `hrp` pero el recompute no es fiel (covarianza ya rebanada, N≠M) y no hay `raw_weights` → también `None` (documentado: solo la ruta HRP del pipeline cumple N==M).
- **`_resolve_effective_bounds` importado privado** (precedente `_leaf_order`/feat-048): CRITICAL duplicado al relajar es efecto conocido y documentado; los tests lo asumen (caplog no lo aserte como fallo).
- **Convención NaN para pesos no finitos** (catálogo §4): HHI=NaN (el sanitizador lo convierte a `null`), DR/RC/spread `None`; verificación de Σw ANTES de elevar con la tolerancia del motor (`_WEIGHT_SUM_TOLERANCE`).
- **Dispersión RC con ddof=0** (poblacional): N=1 → 0.0 definido sin ramas especiales; max_over_equal = max(RC)/(1/N) = 1.0 para N=1.

## Risks / Trade-offs

- [Riesgo] Drift de fórmulas si el motor cambia → Mitigación: pines analíticos exactos (equal→0.25; DR identidad n=1; ΣRC==1) + recompute bit-idéntico pineado (l1==0 cuando los bounds no muerden).
- [Riesgo] CRITICAL duplicado en cada diagnóstico de universo relajado → documentado como efecto conocido (mismo patrón que el warning duplicado descartado en feat-044).
- [Trade-off] RC como dict por ticker (legible) vs vector (compacto) → dict: el JSON es contrato de lectura, no de rendimiento.
- [Riesgo] Cobertura del gate: ramas nuevas (slice, degenerados, recompute) cubren ~100% con TDD → TOTAL % debe sostenerse o subir (baseline 86.21%).

## Migration Plan

1. En la rama `feat/allocation-diagnostics` (ya creada, feat-045 in-progress en rama): TDD rojo → implementación → verde → validación pre-push con subagentes (regla del usuario) → trackers en rama → commit → push/PR/merge → archive vía rama chore.
2. Rollback: revert de 1 función + tests + export; additive puro.

## Open Questions

Ninguna: firma (con enmienda documentada), semántica de raw_weights y política de degenerados quedaron bloqueados contra el registro del épico y los seams verificados.
