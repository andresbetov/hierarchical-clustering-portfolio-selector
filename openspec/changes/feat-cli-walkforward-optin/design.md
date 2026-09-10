# Design: feat-cli-walkforward-optin (feat-051)

## Decisiones (análisis previos + rulings)

1. **Flag `--walk-forward` (`store_true`, default `False`)** tras `--refresh-cache` en `_build_parser`; help documenta propósito OOS + opt-in + coste ("diagnostic-only, refits per window"). `store_true` (no `--no-` negado: BooleanOptionalAction solo donde la negación se usa). Lista de flags en `test_cli.py` + `"--walk-forward"`.
2. **Forward**: ruta normal `run_walk_forward=args.walk_forward`; ruta legacy literal `False` (patrón `refresh=False`); test del warning argv (`main(universe_path, argv)` → caplog "overrides" + kwargs forzados).
3. **Pipeline**: en `_emit_technical_report`, reemplazar el `debug` por lógica real: `if run_walk_forward: try: report = walk_forward_evaluate(historical_prices, price_dates, config); section = walk_forward_section(report) except ValueError as exc → {"skipped": str} / except Exception → {"skipped": str}` (dos ramas: el mensaje de filas insuficientes es ValueError esperado; resto imprevisto; ambas warning "Walk-forward skipped: %s" + payload válido) `else: None`; `payload["walk_forward"] = section` post-build (builder puro intacto).
4. **Dialecto skipped**: `{"skipped": "<reason-str>"}` top-level (tracker-literal; JUnit/GX: skip-con-motivo ≠ null/omitido; sin choque con la shape de sección: `"skipped"` jamás ocurre en ella; drift-None+reason vive un nivel más adentro).
5. **Panel corto (20 filas)**: `evaluate` ELEVA `ValueError("Not enough rows")` fuera del try por-fold → rama skipped real (no sintética). Panel plano-largo → sección válida con `valid_folds=0` (NO skipped: distinguir en tests).
6. **Sin re-fetch**: el bundle (`historical_prices`, `price_dates`) ya está desempaquetado; `evaluate` realinea internamente; caché intacta. Coste O(F·(N·T+N²)) segundos en 12×1250 — dentro del run CLI opt-in.
7. **Docs**: README sección tras OOS (`:64-73`) con path/schema/flag/horizontes/disclaimer backtest (GIPS: teórico≠real, in-sample por defecto); CHANGELOG `Added` una bala por feature visible del épico (043/044/045/046/048/049/050/051); catálogo header → implementado-con-estado + sync §8 (XOR + n==2 0.0 + ejemplo n=6); counts (README 358, CONTRIBUTING baseline — la terminología TOTAL ya está bien tras PR #54).
8. **Tests** (`test_report_assembler.py` + `test_cli.py`): parser default/parse/help; propagate on/off vía monkeypatch; legacy fuerza off + warning; E2E largo (≥560 filas, 4 tickers) sección real; corto → skipped; plano-largo → válida-no-skipped; raise ValueError/genérico → skipped (monkeypatch); default → null; schema 1 invariante.

## Riesgos

- E2E largo con rows=800: ventanas 250/60/5 → folds reales; filtros con drift +0.08% dejan supervivientes (probado en feat-050 E2E).
- `evaluate` dentro de `_emit` corre DESPUÉS del log final: el tiempo extra solo afecta runs opt-in.
- `walk_forward_section` sobre report vacío (0 folds): agregados ceros/None + drift None+reason — válido, pineado por test plano.
