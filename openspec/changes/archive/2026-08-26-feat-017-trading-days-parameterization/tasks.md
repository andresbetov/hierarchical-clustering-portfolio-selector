# Tasks: feat-017-trading-days-parameterization

## 1. Constante paramétrica

- [x] 1.1 metrics kernels con trading_days param — verificar: grep "* 252" = 0 en fuente
- [x] 1.2 config campo+validación; data_fetch 4º requerido; pipeline pasa valor — verificar: pyright

## 2. Tests y cierre

- [x] 2.1 Expectativas custom (365 crypto, 252 legacy) + TypeError binding + validación config — verificar: suite crece verde
- [x] 2.2 Gates + tracker done + commits + archive + PR merge
