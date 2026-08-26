# Design: feat-023-layered-architecture-strangler

## Context

Net de feat-021 (140 tests: unitarios + propiedades + E2E) protege la cirugía. El punto de costura ya existía naturalmente (fetch batch), ahora formalizado como Protocol.

## Goals / Non-Goals

**Goals:** Protocol+Adapter; inyección en main(); FakeProvider testeable sin monkeypatch; compat pública 100%.
**Non-Goals:** mover ficheros (M3 churn); Reporter interface viz (diferida); caching provider; múltiples proveedores concretos.

## Decisions

### D1 — typing.Protocol structural
No exige herencia explícita: cualquier objeto con fetch_metrics califica. Compatible mypy/pyright basic. Runtime ligero.
### D2 — Adapter delega, no duplica
YFinanceProvider.fetch_metrics llama a las funciones module-level existentes (batch/retry/extracción). Cero lógica nueva = cero riesgo semántico; tests del boundary interno siguen aplicando.
### D3 — main() default-constructs
`provider=None → YFinanceProvider()` mantiene todas las rutas actuales byte-compatibles; scripts/cli/report no cambian.
### D4 — MetricsBundle = tuple hoy
Protocol retorna la misma tupla que download_and_calculate_metrics: dataclasses sería más "bonito" pero rompe consumidores. Mantener tuple documentado.

## Risks / Trade-offs

- Protocol sin checks runtime: error de firma salta al primer call — aceptado (tests cubren ambas rutas)
- Doble capa delegación añade un frame stack trivial
