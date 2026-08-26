# Tasks: feat-023-layered-architecture-strangler

## 1. Costura

- [x] 1.1 data/provider.py: MarketDataProvider Protocol + YFinanceProvider adapter (delegación pura) — verificar: ruff+pyright
- [x] 1.2 app/pipeline.py: provider param inyectable; cero imports transporte — verificar: grep yfinance en app = 0

## 2. Consumidores e inyección

- [x] 2.1 Legacy delegate intacto; cli/scripts sin cambios — verificar: suite legacy verde
- [x] 2.2 test_pipeline_e2e migrado a FakeProvider injection; test statico anti-canvas — verificar: crece verde
- [x] 2.3 Gates completos + tracker done + progress/handoff + commits + archive + PR merge
