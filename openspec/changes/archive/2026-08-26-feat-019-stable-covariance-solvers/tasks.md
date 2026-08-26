# Tasks: feat-019-stable-covariance-solvers

## 1. Solvers

- [x] 1.1 _ensure_positive_definite helper (cholesky test + jitter progresivo loggeado) — verificar: pyright
- [x] 1.2 max_sharpe/min_variance via np.linalg.solve; fallback igual-weights conservado nombrado — verificar: ruff+pyright

## 2. Tests y cierre

- [x] 2.1 Equivalencia analítica diagonal PD; colinealidad severa finita+normalizada; fallback path con cov nula (warning); min-var denominador exacto — verificar: crece verde
- [x] 2.2 Gates + tracker done + progress/handoff + commits + archive + PR merge
