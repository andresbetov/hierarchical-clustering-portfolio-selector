# Design: feat-006-package-console-entrypoint

## Context

Identidad ya correcta (feat-003); suite 30 passed; el venv nunca instaló el proyecto (sin build-system). scripts/assets-investment.py mantiene la secuencia canónica: config default → reporte con 7 plots → resumen consola.

## Goals / Non-Goals

**Goals:** paquete instalable via hatchling; entrypoint `portfolio-run`; script legacy como wrapper; metadata testeable.
**Non-Goals:** argparse/flags (--config/--universe → Fase 4 + feat-024), src-layout (feat-023), Docker/wheel publishing.

## Decisions

### D1 — hatchling sobre setuptools
Config mínimo: dos líneas de wheel target. setuptools exigiría más ceremonia (setup.cfg legacy o configuración equivalente) y es más lento.
*Alternativa descartada:* flit — menos estándar en repos de análisis numérico con flat layout.

### D2 — cli.py dentro del paquete, no en scripts/
Módulo importable `portfolio_engine.cli` permite entry-point directo y tests sin ejecutar pipeline. La función `main()` replica exactamente la conducta del script actual (mismo universo hardcodeado hasta feat-024): cero drift de comportamiento en la transición.

### D3 — `pythonpath=["."]` se conserva
Tras instalar el paquete sería redundante para pytest, pero elimina una clase entera de fallos si alguien corre pytest fuera de contexto uv (p.ej. interprete del sistema). Belt-and-suspenders barato; nota añadida en pyproject comment? — no, comentarios de decisión viven aquí y en decision-log.

### D4 — Verificación por metadatos, no por texto
Los asserts usan `importlib.metadata`: nombre resuelto == "hierarchical-clustering-portfolio-selector" y entry-point exacto. Si alguien rompe packaging, suite falla aunque pyproject "parezca bien".

## Risks / Trade-offs

- hatchling entra al lock (+~1 dep build) — aceptado, es infraestructura
- `uv run portfolio-run` con red descarga datos reales: por diseño el test NUNCA invoca main(), solo su existencia/firma
