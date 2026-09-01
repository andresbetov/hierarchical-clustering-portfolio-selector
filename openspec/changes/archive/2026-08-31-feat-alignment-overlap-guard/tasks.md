## 1. Contratos y validación (rojo primero)

- [x] 1.1 `core/config.py`: campo `minimum_overlap_ratio=0.9` validado `(0,1]` con mensaje `must be within (0, 1]` — verificar: `ValueError` para 0, 1.0001, -0.1; `1.0` válido
- [x] 1.2 `core/metrics.py`: guard post-DataFrame con `notna().mean()` sobre unión, exclusión `ratio < threshold`, `logger.warning` nombrado, `MIN_COMMON_ROWS` sobre supervivientes + `n==0` ValueError, chart 4 sin crash — verificar: tests 1.x en rojo pre-impl (tickers 50% no excluidos, truncamiento a 125 filas, `ValueError: lengths differ` en chart 4)

## 2. Alineación con guard y pipeline

- [x] 2.1 Implementar guard en `align_prices_to_common_calendar(..., minimum_overlap_ratio=0.9)` + propagación `config.minimum_overlap_ratio` desde `pipeline.main` y `walk_forward_evaluate` + chart 4 alineado vía `align` — verificar: test 50% excluido preserva 250 filas para supervivientes, `1.0` bit-a-bit idéntico, `0` supervivientes ValueError, hueco intercalado 1 día no excluye
- [x] 2.2 Actualizar `tests/test_alignment.py:test_short_ticker_trims_everyone` para reflejar nuevo contrato (o parametrizar con threshold) y añadir tests de frontera `0.90` retenido / `0.89` excluido + orden preservado — verificar: suite verde sin modificar asserts fuera de contrato

## 3. Verificación integral y cierre

- [x] 3.1 Suite completa `./init.sh` exit 0 + `openspec validate --specs` — output registrado como evidencia
- [x] 3.2 README (config tabla + metodología), CHANGELOG Unreleased — verificar: docs sincronizadas
