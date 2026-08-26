# Tasks: feat-009-numeric-guards-metrics

## 1. Kernels numéricos (core/metrics)

- [x] 1.1 VOL_FLOOR_EPS + sharpe NaN-guard + volatilidad ddof=1 manual numba — verificar: ruff+pyright
- [x] 1.2 correlation diagonal condicionada a varianza>0 — verificar: caso activo plano

## 2. Selección y asignación protegidas

- [x] 2.1 apply_asset_filters excluye non-finitos nombrando ticker+motivo (caplog-testeable) — verificar: flujo
- [x] 2.2 risk_parity piso+cap+warnings no-convergencia; import VOL_FLOOR_EPS — verificar: cov singular produce pesos finitos suma≈1

## 3. Tests y cierre

- [x] 3.1 test_metrics ampliado (~10): expectativa exacta ddof=1, patrones NaN corr, filtros nombrados, rp degenerada; update expectativa legacy vol — verificar: suite crece verde
- [x] 3.2 Gates completos + tracker done + progress/handoff + commits + archive
