# Tasks: feat-013-frozen-validated-config

## 1. Contrato

- [x] 1.1 core/config.py frozen dataclass + __post_init__ con reglas completas + WEIGHT_ALLOCATION_METHODS público — verificar: ruff+pyright
- [x] 1.2 allocation.py: dispatch exhaustivo sin fallback muerto — verificar: grep else-warning = 0

## 2. Consumidores y tests

- [x] 2.1 test_integration fixture → kwargs; scripts/cli intactos (atributos) — verificar: suite
- [x] 2.2 tests/test_config.py: default válido, FrozenInstanceError, cada regla ValueError, replace-pattern legal — verificar: crece verde
- [x] 2.3 Gates + tracker done + progress/handoff + commits + archive + PR merge
