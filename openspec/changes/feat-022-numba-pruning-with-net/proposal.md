# Proposal: feat-022-numba-pruning-with-net

## Why

M6 identificó uso injustificado de numba: kernels triviales jiteados, warm-up por proceso, artefactos `.nbc`, peso de instalación y fricción de tipado — con precondición declarada "si n<1000 eliminar". El universo objetivo (decenas–centenas de tickers × ~1250 días) está muy por debajo; el warm-up JIT domina cualquier ganancia en runtime a esa escala. feat-021 ya desplegó la red de caracterización (propiedades + E2E) que protege esta reescritura semánticamente.

## What Changes

- `core/metrics.py`: **todas las decoraciones `@jit` eliminadas**; kernels reescritos como NumPy vectorizado con semántica idéntica pinneada (honest diagonal, ddof=1, NaN propagation, firmas públicas intactas)
- `pyproject.toml`: dependencia `numba` eliminada; `uv lock/sync` limpia el entorno
- `Makefile`: limpieza `.nbc/.nbi` simplificable pero se conservan entradas defensivas
- ADR 004 (docs/adr/004-remove-numba.md): decisión, medición cualitativa de escala, condiciones de reintroducción (n>400 hot paths)
- Tests existentes actúan como red — no se escriben tests nuevos salvo que la reescritura exponga hueco real
- Fuera de scope: optimizaciones adicionales de performance, PyPy, hilos

## Capabilities

### Modified Capabilities
Ninguna requiere cambios de requisitos: `numeric-correctness`/`system-verification` siguen sosteniéndose — es exactamente su propósito. Referencia: decision-log feat-001 marca M6 resuelta.
