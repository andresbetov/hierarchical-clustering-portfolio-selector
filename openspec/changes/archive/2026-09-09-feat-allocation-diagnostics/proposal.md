## Why

El reporte técnico carece del diagnóstico de asignación: concentración real (HHI/N_eff), la prueba del producto (ratio de diversificación de Choueifaty + reparto del riesgo) y la telemetría del aplanamiento Dykstra que el Addendum ADR-003 admite. Es §4+§6 del catálogo (docs/diagnostics-catalog.md), el tercer bloqueo del épico feat-043..051: sin DR/RC un producto HRP no puede verificar que la jerarquía diversificó algo, y sin raw-vs-constrained el aplastamiento de los bounds 0.05–0.30 es invisible.

## What Changes

- Función pura `allocation_diagnostics(weights, covariance_matrix, covariance_tickers, config, raw_weights=None)` en `portfolio_engine/app/report_json.py`: HHI=Σw² y N_eff=1/HHI (guard Σw==1±1e-9, N=0→None, N=1→1.0, peso no finito→NaN); DR=Σ(wᵢσᵢ)/σ_p y RCᵢ=wᵢ(Σw)ᵢ/σ_p² con dispersión (std, max-min, max/(1/N)) — covarianza SIEMPRE rebanada al subconjunto de pesos reutilizando `create_portfolio_covariance_matrix` (regla feat-028); `raw_vs_constrained` con recompute determinista de `calculate_hrp_weights` solo para método `hrp` (l1, max_weight_drop, n_weights_changed, bounds efectivos + mandate_relaxed vía `_resolve_effective_bounds`).
- Export en `portfolio_engine/app/__init__.py`.
- Sin integración en pipeline/CLI (feat-050): cero cambios de comportamiento en la corrida actual.

## Capabilities

### New Capabilities

(Ninguna — se acrecenta la capability existente `technical-report`.)

### Modified Capabilities

(Ninguna en sentido MODIFIED — requirement ADDED a la capability existente `technical-report`: diagnóstico de asignación con concentración, diversificación y desvío de restricciones.)

## Impact

- Código: +1 función pura en `report_json.py` (~70 stmts) + export; cero cambios en el motor (`allocation.py`/`hrp.py`/`config.py` intocados — red feat-021 diff 0; imports de `calculate_portfolio_variance`/`create_portfolio_covariance_matrix`/`_resolve_effective_bounds`/`calculate_hrp_weights` reutilizan código probado, import privado de `_resolve_effective_bounds` documentado).
- Tests: `TestAllocationDiagnostics` en `tests/test_report_json.py` (TDD rojo→verde).
- Dependencias: ninguna nueva.
