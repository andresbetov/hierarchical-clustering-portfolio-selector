# Tasks: feat-008-returns-date-alignment

## 1. Dependencia explícita

- [x] 1.1 pyproject: pandas>=2.0 en dependencies; uv lock/sync — verificar: lock actualizado, sin paquetes nuevos inesperados

## 2. Implementación

- [x] 2.1 metrics.py: align_prices_to_common_calendar(prices, dates) inner-join + MIN_COMMON_ROWS=2 + ValueError en guard de construct_returns_matrix — verificar: ruff+pyright verdes
- [x] 2.2 pipeline.py: estadística multivariada consume aligner(filtered_prices, filtered_dates); charts intactos — verificar: flujo completo sin red no-ejecutable se cubre por tests

## 3. Tests deterministas

- [x] 3.1 tests/test_alignment.py: casos calendario desfasado/ticker corto/disjuntos/min densidad/orden/legacy equal-length — verificar: suite verde crece
- [x] 3.2 Gates completos + tracker done + progress/handoff + commits + archive
