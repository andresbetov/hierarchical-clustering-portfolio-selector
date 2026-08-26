# Design: feat-021-deep-characterization-suite

## Context

129 tests unitarios verdes; feat-012 ya definió el patrón de parcheo del batch boundary. Red requerida ANTES de tocar hrp.py/allocation internals (feat-022/023).

## Goals / Non-Goals

**Goals:** propiedades algebraicas cross-module con hypothesis derandomized; E2E offline completo; cero duplicación de asserts unitarios.
**Non-Goals:** coverage formal %, benchmarks perf, mock de yfinance UI-level.

## Decisions

### D1 — Generación de covarianzas via A·Aᵀ escalado
Estrategia: matrices aleatorias A (n×n) → Σ=A·Aᵀ + escala diag ⇒ simétrica PD por construcción. Universos n∈[2,30] cubren single/chain/cuasi-block realismo.
### D2 — derandomize=True
CI determinista obliga a que "verde" signifique lo mismo siempre. Trade-off: menos diversidad por corrida — aceptado (propiedad de ejemplo mínimo sigue operando localmente).
### D3 — E2E hereda fixture monkeypatch
`conftest.py` expone `patched_batch` parametrizable por spec-dict; reutiliza el shape MultiIndex(Ticker,Field) validado en feat-012. Sin FixtureFactory exótico.
### D4 — Health-checks de integración pinnnean composición, no valores
No assertar pesos exactos en E2E (frágil); assertar invarianzas y coherencia entre etapas (las fórmulas exactas viven en tests unitarios).

## Risks / Trade-offs

- hypothesis puede descubrir violaciones latentes reales → si aparece contra-caso válido: es un bug del motor, se corrige aquí mismo (esta es la misión)
- Runtime por volumen de ejemplos acotado con max_examples moderados
