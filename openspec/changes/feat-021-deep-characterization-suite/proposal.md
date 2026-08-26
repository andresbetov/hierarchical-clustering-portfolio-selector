# Proposal: feat-021-deep-characterization-suite

## Why

Los tests actuales (129) cubren contratos unitarios pieza-a-pieza, pero M8 exige la RED que proteja los reworks próximos (M6 pruning numba en feat-022, M3 layered-architecture en feat-023): propiedades de sistema invarianzantes y composición end-to-end offline. Sin esa red, refactorizar el centro de alto fan-in es apuesta a ciegas.

## What Changes

- `pyproject.toml`: `hypothesis` en dev group
- `tests/test_properties.py` (nuevo): propiedades hypothesis sobre las garantías matemáticas del motor — simplex-invariantes de Dykstra/HRP/solvers para covarianzas PD arbitrarias, finitud ante inputs degenerados aleatorios, monotonicidad estructural de alineación
- `tests/test_pipeline_e2e.py` (nuevo): composición end-to-end determinista sin red (monkeypatch `_fetch_batch` con panel sintético multi-ticker con huecos + colas NaN) → asserts de contrato completo: filtrado no-vacío, matrices cuadradas simétricas, pesos HRP simplex, reportes generados
- `conftest.py` (nuevo): fixture compartido `_patch_fetch_batch` reutilizable
- Fuera de scope: mock de caplog-ordering ya resuelto; cobertura formal % (sin coverage.xml aún)

## Capabilities

### New Capabilities
- `system-verification`: capacidad que define qué propiedades transversales el sistema debe sostener bajo entradas arbitrarias válidas — invarianzas algebraicas de asignadores/pesos y composición pipeline verificable sin red.
