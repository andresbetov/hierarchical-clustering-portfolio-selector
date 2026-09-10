# Design: docs-spec-sync (feat-053)

Cada decisión alinea texto con comportamiento ya verificado en código/tests; ninguna cambia comportamiento.

1. **Dykstra, no clamp iterativo** (`numeric-correctness`): el código implementa proyecciones cíclicas sobre simplex + semiespacios de bounds con acumuladores y verificación final dura (`allocation.py:245-319`); el propio ADR 003 ordena este cambio de texto.
2. **Fórmula Sharpe ya sincronizada**: `(w·μ − ln(1+rf))/sqrt(wᵀΣ)` con Σ diaria anualizada — fijada en sesión feat-052; el delta solo corrige el texto de constraints.
3. **configuration-contract**: eliminar `target_portfolio_volatility` (ADR 001; `config.py` no lo tiene); enumerar las validaciones reales (`risk_free_rate`, `maximum_volatility_threshold`, scoring, min/max, lookback, trading_days, overlap, 4 enums); dispatch: 5 legacy 1:1, `hrp` lanza ruteo (`allocation.py:371-382`), else inalcanzable lanza.
4. **package-interface**: añadir `--walk-forward` (store_true, default `False`, reenviado como `run_walk_forward`; legacy lo fuerza off); wrapper solo importa e invoca `cli.main()` (el logging lo configura el CLI).
5. **quality-gates**: "85% TOTAL combinado de coverage.py (líneas+branches)" en requirement y scenarios; el umbral compara el total, no branch-only.
6. **project-packaging**: retirar el scenario transitorio de scipy (cerrado: consumida en `selection.py`/`hrp.py`); reemplazar por "sin dependencias fantasma".
7. **runtime-diagnostics**: carve-out Darwin — en macOS se respeta el backend nativo (`reporting.py:24-25`, test en `test_viz_headless.py:30`).
8. **system-verification**: rango n 2–25 (iguala `SIZE_STRATEGY` en `test_properties.py:31`).
9. **technical-report**: la serie in-sample se construye para cómputo pero NO se serializa (solo `series_n_obs`/`tail`/`drawdown`); pesos finales in-sample explícitamente fuera de contrato (gap en roadmap v0.2.0).
10. **verification-harness**: literal `uv run python -m pytest` (comando real de `init.sh:17`).
11. **quant-docs**: requirement del trade-off Dykstra-vs-HRP que el purpose ya promete.
12. **ADR**: "ADR 008 (pendiente)" como futuro supersesor de Dykstra; actualizar refs `file:line` del addendum 003 y del índice (mantenimiento de punteros, no edición de decisiones).
13. **Docs de proceso**: baselines vigentes, comandos y gates alineados a `init.sh`/CI reales; refs muertas del tracker anotadas a `git log`; `scripts/charts/` ya regenerado en feat-052.
14. **Sin código ni tests**: verificación = `openspec validate docs-spec-sync` + `openspec validate --all` + `./init.sh` + greps anti-regresión. El sync a specs vivas se aplica en el archive según el flujo del repo.
