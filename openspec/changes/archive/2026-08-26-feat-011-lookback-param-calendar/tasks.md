# Tasks: feat-011-lookback-param-calendar

## 1. Ventana y contrato

- [x] 1.1 data_fetch.py: `_resolve_window(today, lookback_years)` pura + firma con lookback requerido + log de bounds — verificar: ruff+pyright verdes
- [x] 1.2 config.py: lookback_years=5; pipeline.py pasa config.lookback_years — verificar: grep hardcode 5*365 = 0

## 2. Tests de contrato y fechas

- [x] 2.1 test_data_fetch_contract.py: TypeError segundo requerido + introspección firmas; tests puros ventana (normal/bisiesto-clamp/invalid) — verificar: suite crece verde
- [x] 2.2 Gates completos + tracker done+evidence + progress/handoff + commits + archive
