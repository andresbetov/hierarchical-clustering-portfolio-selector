## 1. Fundamento y contratos

- [x] 1.1 Escribir helper `risk_free_log_rate(rf)` y `@property risk_free_rate_log` en `core/config.py` + `core/metrics.py` y test `rf=0` invariante / `rf=0.045` pin `0.044016885416774` — verificar: `pytest -k test_sharpe` rojo→verde
- [x] 1.2 Actualizar pinnings en `tests/test_metrics.py:54` y `tests/test_reporting_sharpe.py` a `(ret - log1p(rf))/vol` — verificar: `pytest` rojo→verde con tolerancia `rel=1e-12`

## 2. Migración de call-sites (6)

- [x] 2.1 Migrar `data/data_fetch.py:203`, `portfolio/allocation.py:153` y `viz/reporting.py:377,138` a `rf_log` — verificar: `pytest` + spot check visual `rf_log` en reporting
- [x] 2.2 Migrar `validation/walk_forward.py:131,154` (`_train_survivors` y `_oos_metrics`) a `rf_log` y unificar `_oos_metrics` para usar `calculate_sharpe_ratio` + `VOL_FLOOR_EPS` — verificar: `tests/test_walk_forward.py` rojo→verde (feat-029 pin 2.184 recalculado si aplica)

## 3. Documentación y cierre

- [x] 3.1 Escribir Addendum fechado en `docs/adr/003-hrp-adoption.md` (Dykstra post-hoc euclídea vs varianza jerárquica, Pfitzinger & Katzke trade-off, cuantificación `n=5,max=0.30`) — verificar: `docs/adr/README.md` actualizado
- [x] 3.2 Actualizar `CHANGELOG.md` (breaking en rf≠0), `README.md` sección Sharpe/log, y `tests/test_pipeline_e2e.py` + `tests/test_solvers.py` pinnings restantes — verificar: `grep -rn log1p.*risk_free` muestra 6+ call-sites y suite verde
