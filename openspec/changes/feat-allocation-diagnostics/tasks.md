## 1. Rama y registro (en la rama)

- [x] 1.1 Crear la rama `feat/allocation-diagnostics` desde `develop` limpio y verificar baseline verde
- [x] 1.2 Cambiar a la rama correcta y actualizar feat-045 a `in-progress` en `feature_list.json` ANTES de implementar (regla del usuario)

## 2. TDD rojo

- [x] 2.1 Añadir `TestAllocationDiagnostics` a `tests/test_report_json.py` con pines analíticos (equal→HHI 0.25/N_eff 4.0; N=1→identidad; Σw violado→error nombrado; slice M<N≡cálculo directo en 3×3; ΣRC==1; invariancia de orden; telemetría Dykstra; no-HRP→null; degenerados→None/NaN; serialización estricta) y verificar rojo por `AttributeError` de `allocation_diagnostics` inexistente, registrando el nº de failures (15, /tmp/red045.log)
- [x] 2.2 `openspec validate feat-allocation-diagnostics --type change` en verde

## 3. Implementación

- [x] 3.1 Implementar `allocation_diagnostics(weights, covariance_matrix, covariance_tickers, config, raw_weights=None)` en `report_json.py`: rebanado por `create_portfolio_covariance_matrix` con error nombrado ante ticker faltante; HHI/N_eff con guard Σw±1e-9; DR/RC/spread con guard `VOL_FLOOR_EPS`; `raw_vs_constrained` con semántica raw_weights/hrp-recompute/no-HRP-None vía `_resolve_effective_bounds`; export en `portfolio_engine/app/__init__.py`
- [x] 3.2 Grupo completo en verde + ruff + pyright en la iteración de gate

## 4. Verificación del change

- [x] 4.1 `./init.sh` fresco con TOTAL % de cobertura combinada registrado (86.91% ≥ 86.21%) y suite completa verde (286 passed)
- [x] 4.2 Motor intocado (`git diff develop` sin archivos en core/portfolio/data/validation/viz/pipeline ni motor tests) + `openspec validate --all` verde

## 5. Cierre (todo en la rama)

- [x] 5.1 Validación pre-push con subagentes especializados (regla del usuario): reviewer código CONDITIONAL-APPROVE (MAJOR-1 guard forma raw_weights + MAJOR-2 pines engine round-trip/n=3 — implementados; +7 MINOR: long-only, NaN-raw, umbral 1e-12, max_over_equal, len-check, docstring, __all__) y auditor proceso APPROVE (higiene trackers corregida en 5.2)
- [x] 5.2 Actualizar `feature_list.json` (done + evidencia), `progress.md` y `session-handoff.md` DENTRO de la rama; commit Conventional Commits; `git status` limpio — luego push/PR/CI/merge y archive vía rama chore
