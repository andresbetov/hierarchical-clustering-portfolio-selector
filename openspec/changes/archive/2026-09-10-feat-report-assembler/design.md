# Design: feat-report-assembler (feat-050)

## Decisiones (síntesis de los 2 análisis + rulings propios)

1. **Firma `build_technical_report(requested_tickers, asset_metrics, filtered_metrics, closing_prices, price_dates, covariance_matrix, covariance_tickers, weights, config, window_start, window_end, generated_at) -> dict`** (pura, sin reloj/IO; `generated_at`/ventana los resuelve el pipeline).
2. **Ventana honesta**: min/max ISO (`str(d)[:10]`, tolera DatetimeIndex/np.datetime64/listas) sobre la unión de `price_dates`; vacía → `"unknown"`. `generated_at = datetime.now(timezone.utc).isoformat()` en pipeline.
3. **Placeholder `"walk_forward": None`** (literal del tracker; feat-051 llena la misma key; null = "opt-in apagado", distinto de ausente).
4. **Serie**: `{t: closing[t] for t in filtered}` + fechas → `align_prices_to_common_calendar(..., 1.0)` → `portfolio_return_series`; `ValueError` (p. ej. universo vacío) → `logger.warning` + serie `[]` → secciones tail/drawdown null bien formadas (degradación por sección, precedente dendrograma). Sin este guard, un skew abortaría las 5 secciones sanas.
5. **Allocation con `raw_weights=None` siempre** (el motor solo devuelve constrained; HRP auto-recomputa, legacy → None por contrato feat-045). Tree sobre la cov completa filtrada + `config.linkage_method` (cualquier método ADR-006).
6. **Emisión**: kwargs keyword-only tras `provider` (`report_path: str | Path | None = None`, `run_walk_forward: bool = False` reservado con `logger.debug`); helper `_emit_technical_report` (punto único de emisión: N=0 fluye al mismo punto pues los charts hacen skip y las secciones degradan a null — `main()` intacto, sin segundo call-site); `try/except Exception → warning "Technical report JSON skipped: %s" # noqa: BLE001 / else → info "Technical report JSON written: path=%s"`. `except Exception` (nunca bare: preserva KeyboardInterrupt; `ValueError` estrecho filtraría OSError de disco — rechazado con respaldo OTel/MLflow). Desviación documentada del cap de +15 líneas en pipeline.py: el helper centraliza (~35) con call-site de 2 líneas; la alternativa (duplicar el bloque o reestructurar el early-exit de `main`) es peor ingeniería.
7. **Sin reescritura atómica de `dump_`** (decisión documentada): ventana de crash mínima, sidecar regenerable; no churnear feat-043 cerrada por un MINOR externo.
8. **CLI**: 1 línea (`report_path="reports/technical-report.json"`); JSON siempre (producto del épico), `--no-save` solo plots (decisión explícita del tracker, pineada). Fakes de test_cli aceptan `report_path`.
9. **Shape risk**: `{"series_n_obs": int|None, "tail": {...}, "drawdown": {...}}` (meta + secciones; `series_n_obs None` si degradada).
10. **Tests** en `tests/test_report_assembler.py` (nuevo archivo) vía `patched_batch` real (4 tickers, rows=800): default-nada, E2E-estricto+fingerprint, placeholder, fallo-inyectado, no-save-emite, tuplas intactas (8/4), legacy no aplica aquí (HRP default), universo-vacío-válido, cli-escribe (chdir tmp), fakes-compatibles (suite test_cli verde sin tocar asserts).

## Riesgos

- `patched_batch` rows=800: 4 supervivientes esperados (drift +0.08%/día); si el filtro deja N<4 los tests usan lo que haya (asserts sobre estructura, no N fijo) salvo fingerprint (independiente de N).
- `reports/` ignorado: el test E2E usa `tmp_path`; el test CLI usa `monkeypatch.chdir(tmp)`.
- `run_walk_forward=True` hoy: debug + `walk_forward None` (feat-051 lo cablea; sin NotImplemented para no romper callers futuros).
