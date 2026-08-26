# Tasks: feat-022-numba-pruning-with-net

## 1. Reescritura vectorizada

- [x] 1.1 metrics.py sin @jit: kernels numpy puro, firmas intactas — verificar: grep jit/numba=0 en portfolio_engine
- [x] 1.2 pyproject sin numba; uv lock/sync — verificar: import numba falla en venv

## 2. Verificación de paridad

- [x] 2.1 Snapshot numérico pre/post (script inline sobre fixtures estrella) + suite completa verde SIN modificar asserts — verificar: 140+ pasan
- [x] 2.2 ADR 004 + decision-log M6 resuelta — verificar: docs

## 3. Cierre

- [x] 3.1 Gates completos + tracker done + commits + archive + PR merge
