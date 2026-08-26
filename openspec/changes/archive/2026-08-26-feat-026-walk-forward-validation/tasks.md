# Tasks: feat-026-walk-forward-validation

## 1. Generador de ventanas

- [x] 1.1 `_iter_walk_windows(n, train, test, embargo)` puro + guard insuficiencia — verificar: unit
- [x] 1.2 Tests edge exhaustivos (embargo 0/N, train>test, boundary) — verificar: crece verde

## 2. Motor OOS

- [x] 2.1 walk_forward.py: evaluación fold-a-fold ex-ante weights + exclusión degenerados + WalkForwardReport dataclass to_dict — verificar: ruff+pyright
- [x] 2.2 Tests integración con synthetic bundle determinista (2 factor-blocks, ~600 días): pesos ex-ante, embargo sanity, agregados coherentes — verificar: suite crece verde

## 3. Cierre

- [x] 3.1 Gates completos + tracker done + progress/handoff + commits + archive + PR merge
