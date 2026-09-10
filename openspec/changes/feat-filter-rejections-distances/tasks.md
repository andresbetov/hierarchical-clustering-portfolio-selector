## 1. Rama y registro (en la rama)

- [x] 1.1 Crear la rama `feat/filter-rejections-distances` desde `develop` limpio y verificar `./init.sh` verde antes de tocar código
- [x] 1.2 Cambiar a la rama correcta y actualizar feat-044 a `in-progress` en `feature_list.json` ANTES de implementar (regla de flujo del usuario)

## 2. TDD rojo

- [x] 2.1 Añadir `TestFilterRejections` a `tests/test_report_json.py` con los 7 motivos + distancias exactas + conteos + equivalencia con `apply_asset_filters`; verificar rojo por `ImportError`/`AttributeError` de `compute_filter_rejections` inexistente y registrar el nº de failures
- [x] 2.2 Revisión del change `openspec validate feat-filter-rejections-distances --type change` en verde

## 3. Implementación

- [x] 3.1 Implementar `compute_filter_rejections(requested_tickers, asset_metrics, filtered_metrics, closing_prices, config)` en `report_json.py` con el orden de guardias de `selection.py:47-63` (sharpe_non_finite → vol_non_finite → below_min_sharpe → above_max_vol → overlap_pruned → kept; ingestion_rejected fuera del loop) y distancias firmadas; export en `portfolio_engine/app/__init__.py`
- [x] 3.2 Verificar el grupo completo en verde + ruff + pyright en la iteración de gate

## 4. Verificación del change

- [x] 4.1 `./init.sh` fresco en la sesión con TOTAL % de cobertura combinada registrado (≥ 85.60%) y suite completa verde
- [x] 4.2 Verificar motor intocado: `git diff develop --stat` sin archivos en core/portfolio/data/validation/viz/pipeline ni motor tests (red feat-021 diff 0); `openspec validate --all` verde

## 5. Cierre (todo en la rama)

- [x] 5.1 Actualizar `feature_list.json` (feat-044 done + evidencia con TOTAL %), `progress.md` y `session-handoff.md` DENTRO de la rama (regla del usuario); commit Conventional Commits; `git status` limpio y diff presentado al usuario — sin push hasta su validación
