# Tasks: feat-insample-tail-drawdown (feat-046)

## 1. Rama y registro (en la rama)

- [x] 1.1 Crear la rama `feat/insample-tail-drawdown` desde `develop` limpio y verificar baseline verde (296 passed)
- [x] 1.2 Actualizar feat-046 a `in-progress` en `feature_list.json` ANTES de implementar (regla del usuario)

## 2. Análisis previo (subagentes, completado)

- [x] 2.1 Entendimiento profundo (estado, propósito, checklist de aceptación, ambigüedades D1-D4)
- [x] 2.2 Búsqueda externa verificable (Sortino/VaR-CVaR/drawdown-Calmar/etiquetas/serie + top-5)
- [x] 2.3 Mapeo de interacciones ([DEPENDENCY] solo `risk_free_log_rate` + `VOL_FLOOR_EPS`; resto [CONTEXT]; [MODIFY] solo `report_json.py` + tests)
- [x] 2.4 Síntesis → blueprint (rulings D1-D6, firmas, keys, lista TDD)

## 3. OpenSpec (change `feat-insample-tail-drawdown`)

- [x] 3.1 `proposal.md` (modified capability `technical-report`)
- [x] 3.2 `specs/technical-report/spec.md` (+1 ADDED, 7 scenarios)
- [x] 3.3 `design.md` (11 decisiones con respaldo + riesgos + no-goals)
- [ ] 3.4 `tasks.md` (este archivo) + `openspec validate feat-insample-tail-drawdown --type change` en verde

## 4. TDD rojo → verde (26 tests, clase `TestInsampleTailDrawdown`)

- [x] 4.1 Tests escritos primero y rojo verificado (14 failures `ImportError`); tras correcciones propias (expectativas `|VaR|`, serie constante bajo target, fechas ISO, dict de fechas) + 11 tests de mutantes/guards → 26 en verde
- [x] 4.2 Regression-test de re-align con `align_prices_to_common_calendar` real: pata 1.0 (serie == common−1) + pata contraejemplo 0.9 (excluye superviviente 8/10)

## 5. Implementación (append-only en `report_json.py`)

- [x] 5.1 `portfolio_return_series(prices_alineados, weights) -> np.ndarray` (log-diffs por clave vía seam público @ w; weight-sin-precios → `ValueError`; price-sin-weight zero-embed M<N; vacío/ragged/trading n/a → nombrados) + export
- [x] 5.2 `tail_risk_metrics(serie, risk_free_rate, trading_days=252)` (`T/252` vía `risk_free_log_rate`; downside/N-total; `quantile method="linear"`; CVaR inclusivo; jamás escalar; `len<2`/no-finito/rf-no-finito → None+reason; sin downside → Sortino null + VaR numérico; `trading_days<=0` → nombrado)
- [x] 5.3 `drawdown_metrics(serie, trading_days=252)` (`exp(cumsum)` con guard de overflow; maxDD≤0; `mean*T/|maxDD|`; flat → calmar None; negativo legal; degenerados → None+reason) + exports en `__all__` y `app/__init__.py`
- [x] 5.4 Grupo de tests en verde (26/26) + ruff + pyright en la iteración de gate (`./init.sh` exit 0)

## 6. Verificación del change

- [x] 6.1 `./init.sh` fresco con TOTAL % de cobertura (87.61% ≥ 86.94%) y suite completa verde (322 passed)
- [x] 6.2 Motor intocado (`git diff develop` sin archivos en core/portfolio/data/validation/viz/pipeline/cli) + `openspec validate --all` verde (14/14)

## 7. Cierre (todo en la rama)

- [x] 7.1 Validación pre-push con subagentes (código APPROVE + proceso CONDITIONAL→fixes→re-verify→4 doc-MINOR→final APPROVE)
- [x] 7.2 `feature_list.json` (done + evidencia), `progress.md`, `session-handoff.md` EN la rama; commit atómico Conventional Commits; luego push → PR → CI → squash → archive vía rama chore
