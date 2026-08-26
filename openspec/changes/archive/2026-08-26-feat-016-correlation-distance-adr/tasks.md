# Tasks: feat-016-correlation-distance-adr

## 1. ADR y config

- [x] 1.1 docs/adr/002: opciones, decisión signed-default, conversión de umbral por métrica — verificar: completo
- [x] 1.2 config: distance_metric="signed" + enum público DISTANCE_METRICS + validación — verificar: pyright

## 2. Kernel y selección

- [x] 2.1 metrics.py kernel flag entero + wrapper str; selection.py `_resolve_distance_threshold` puro — verificar: ruff+pyright
- [x] 2.2 Tests: extremos firmados (±0.9), conversión umbral, contraste clustering signed-vs-abs, config inválido — verificar: suite crece verde

## 3. Cierre

- [x] 3.1 Gates + tracker done + progress/handoff + commits + archive + PR merge
