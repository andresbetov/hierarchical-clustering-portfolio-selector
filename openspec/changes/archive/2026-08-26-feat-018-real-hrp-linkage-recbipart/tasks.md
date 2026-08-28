# Tasks: feat-018-real-hrp-linkage-recbipart

## 1. Núcleo HRP

- [x] 1.1 portfolio/hrp.py: _leaf_order + _cluster_ivp + calculate_hrp_weights (linkage single, sin inversión) — verificar: ruff+pyright
- [x] 1.2 Guard entrada: cov finita/simétrica; ValueError ruidoso — verificar

## 2. Integración contrato+pipeline

- [x] 2.1 enum + default "hrp" en config; pipeline branch end-to-end sin pruning; constraints feat-014 aplicadas — verificar: flujo
- [x] 2.2 ADR 003 + README tabla method default — verificar: docs

## 3. Tests y cierre

- [x] 3.1 tests/test_hrp.py: analítico [0.8,0.2], invarianza permutación, duplicados, suma/positividad, contraste risk_parity jerárquico — verificar: crece verde
- [x] 3.2 Gates completos + tracker done + progress/handoff + commits + archive + PR merge
