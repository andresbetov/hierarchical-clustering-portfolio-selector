## Context

`core/metrics.py:179` es el único seam de alineación. Hoy construye `pd.DataFrame(columns).sort_index()` (outer union) y `dropna(how="any")` (inner join) sin medir cobertura por ticker. `core/config.py` no tiene `minimum_overlap_ratio`. `pipeline.py:106` y `validation/walk_forward.py:220` llaman a `align` sin parámetro; chart 4 (`pipeline.py:214`) ni siquiera alinea y crashea con `ValueError: lengths differ`. La suite `tests/test_alignment.py` (8 tests) documenta el truncamiento silencioso.

## Goals / Non-Goals

**Goals:**
- Excluir tickers con cobertura `< threshold` contra el span común, preservando 100% de filas para supervivientes; `1.0` bit-a-bit idéntico al vigente.
- Warning nombrado con ticker + ratio + threshold; orden de inserción preservado.
- Chart 4 alineado con mismo guard, sin `ValueError`.

**Non-Goals:**
- No `union+forward-fill` por-ticker (diferido v0.2.0).
- No re-ordenar columnas alfabéticamente.
- No cambiar `MIN_COMMON_ROWS=2` (sigue tras filtrado).

## Decisions

**D1 — Guard post-`DataFrame` con ratio sobre unión (opción B híbrida).**
`frame_before = DataFrame(columns).sort_index()` → `ratios = {t: frame_before[t].notna().mean() for t in frame_before.columns}` → `excluded = [t for t,r in ratios.items() if r < threshold]` → `frame_before.drop(columns=excluded)` → `frame = frame_before[ survivors ].dropna(how="any")`. Mide solape real (tail NaN de IPO vs hueco intercalado 1 día ≈0.99), coincide con literatura (excluir ticker ruidoso >> truncar a todos). Costo `O(T·N)` despreciable (12×1250).

**D2 — Single source `config.minimum_overlap_ratio` + parámetro explícito en función.**
`config.py: minimum_overlap_ratio=0.9` validado `(0,1]` + `def align(..., minimum_overlap_ratio=0.9)`. `pipeline` y `walk_forward` propagan `config.minimum_overlap_ratio`; tests unitarios llaman `align(..., 0.5)` sin config. Evita `None` sentinel; frozen config garantiza valor.

**D3 — `MIN_COMMON_ROWS` sobre supervivientes, `n==0` → `ValueError` nombrado distinto de intersección vacía.**
Si `len(survivors)==0` → `ValueError("No tickers survive overlap filter...")` (evita `StopIteration` en `next(iter(...))`). Si `1` superviviente → retornar 1 columna sin exigir `dropna` de 2 filas (no hay intersección); test `1 fila` existente se mantiene para `n>=2`.

**D4 — Chart 4 reutiliza `align` antes de `construct_returns_matrix`.**
`generate_complete_analysis_report` construye `aligned_full = align_prices_to_common_calendar(historical_prices, price_dates, config.minimum_overlap_ratio)` y luego `construct_returns_matrix(aligned_full)`. Mismo universo superviviente, coherente y sin crash; documentado como absorción de `progress.md:45` en `feat-037`.

## Risks / Trade-offs

- **Test `test_short_ticker_trims_everyone` (B 75% ratio) espera truncamiento:** con `0.9` B sería excluido (< single source). Mitigación: test parametrizado o nuevo test que pinnee exclusión 50% preserva 100% filas (ver tasks 1.1).
- **Zona horaria mixta:** `DatetimeIndex` tz-aware vs naive alinea como columnas distintas → ratios 0. Mitigación: documentar que `data_fetch` garantiza naive (ya lo hace `data_fetch.py:138`).
- **Performance:** `DataFrame` extra despreciable; no forward-fill.

## Migration Plan

Sin migración: `align` mantiene firma con default, `config` añade campo con default. Rollback = revert. `outer+ffill` diferido v0.2.0.
