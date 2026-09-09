## Context

Ver `proposal.md` (Why) para la motivación y la evidencia walk-forward. Estado pre-change: `PortfolioConfig` fijaba `minimum_sharpe_threshold=0.5` y `maximum_volatility_threshold=0.25` (`portfolio_engine/core/config.py:52-53`); `pipeline.main` y `walk_forward_evaluate` consumen ambos valores dinámicamente desde el config, y `reporting.py` los lee para las líneas de referencia de las gráficas. Restricción: el CLI no expone parámetros estructurales por diseño (scope bloqueado en solo-defaults).

## Goals / Non-Goals

**Goals:**

- Cambiar los 2 defaults con reversión trivial y evidencia citada.
- Mantener verde toda la suite salvo los pinnings que fijan el default anterior, que se actualizan documentando la causa.
- Fijar el nuevo comportamiento con tests de contrato + regresión sintética CI-safe.

**Non-Goals:**

- Nuevo universo por defecto, flags CLI para thresholds, flips de `covariance_estimator`/`linkage`, costos/turnover (todo a futuros features).

## Decisions

- **Recalibrar defaults a 0.3/0.27 en vez de mantener o usar 0.3/0.28.** Los valores 0.3/0.27 son exactamente los del experimento vía A (gap WF HRP−EQ +0.070, N=6, 16/16 folds válidos); cualquier otro par invalidaría la evidencia medida. Alternativa 0.3/0.28 (más margen sobre XLE 0.2577/XLK 0.2591) descartada por el usuario: sin evidencia que la respalde.
- **Regresión walk-forward sintética en vez de test con datos reales.** CI es offline (caché deshabilitado, `cache_dir=None`); se construye un panel sintético estilo `conftest.py` con 6 activos y dispersión donde el filtro relajado admite N=6 y HRP ≥ equal en mediana. Alternativa con `yfinance` descartada: no determinista y sin red en CI.
- **Actualizar pinnings `test_config.py:27,77` en vez de congelarlos.** Pinean el default anterior (`== 0.5`); con el cambio quedan rojos por diseño. Se actualizan a `0.3` citando feat-042 (regla anti-relajación silenciosa de la red feat-021).
- **ADR-007 como entregable del change.** La recalibración es reversible con alternativas reales, luego califica como ADR (Límites de `AGENTS.md`) y documenta la evidencia que un diff de 2 líneas no puede portar.

## Risks / Trade-offs

- [Riesgo] El panel sintético admite más activos con 0.3 y algún E2E con defaults cambia de N → Mitigación: actualizar el assert documentando causa; prohibido relajar aserciones sin motivo.
- [Riesgo] Ventanas futuras donde 0.3/0.27 vuelvan a filtrar en exceso (régimen distinto al 2021-2026) → Mitigación: el test de regresión fija el mecanismo sobre panel sintético controlado, no sobre una ventana histórica concreta; la evidencia con datos reales queda citada en el ADR, no pineada en tests.
- [Trade-off] Sharpe absoluto in-sample baja (0.1833 → 0.1709 en universo actual) a cambio de N viable y edge OOS; documentado en el ADR como decisión consciente (el README ya declara que las medianas OOS mandan sobre el Sharpe in-sample).

## Migration Plan

1. Rama `feat/threshold-recalibration` desde `develop`; implementar por `tasks.md`; `./init.sh` fresco + `openspec validate`.
2. Commit Conventional Commits, PR → `develop`, squash, borrar rama. **Sin push hasta validación del usuario** (veto explícito de esta sesión).
3. Rollback: revert de 2 líneas en `config.py` (+ pinnings); sin migración de datos (la key de caché no incluye thresholds y los bundles se re-filtran).

## Open Questions

Ninguna: thresholds, scope y estrategia de tests quedaron bloqueados con el usuario antes de implementar.
