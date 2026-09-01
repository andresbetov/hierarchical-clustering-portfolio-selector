## Why

`align_prices_to_common_calendar` hace `DataFrame(columns).dropna(how="any")` — inner join silencioso. Un ticker IPO/delisted a mitad de ventana fuerza `len(frame)=overlap` para todo el universo. Con 12 large-caps el impacto es bajo, pero en universos amplios (S&P500, 5 años) un 50% de historia perdida sesga covarianza, Sharpe y HRP, y `generate_complete_analysis_report` chart 4 ni siquiera alinea (crash `ValueError: lengths differ` con cualquier suspensión). La literatura de survivorship bias (p. ej., yfinance delistings, CRSP) exige excluir el ticker ruidoso, no truncar a todos.

## What Changes

- Nuevo campo `PortfolioConfig.minimum_overlap_ratio: float = 0.9` validado en `(0,1]` (exclusivo 0, inclusivo 1).
- Guard dentro de `align_prices_to_common_calendar(prices, dates, minimum_overlap_ratio=0.9)`: después de construir `frame_before = DataFrame(columns).sort_index()` (outer union), calcular cobertura `notna().mean()` sobre la unión, excluir con `ratio < threshold` y `logger.warning` nombrado (`excluded`, `ratios`, `threshold`), reconstruir `frame = frame_before[ survivors ].dropna(how="any")` preservando orden de inserción. Validar `MIN_COMMON_ROWS` sobre supervivientes; `n_survivors==0` → `ValueError` nombrado distinto.
- `pipeline.main` y `walk_forward_evaluate` propagan `config.minimum_overlap_ratio`; `generate_complete_analysis_report` chart 4 pasa por `align` antes de `construct_returns_matrix` (mismo universo superviviente, coherente y sin crash).

## Capabilities

### New Capabilities
- `calendar-alignment`: Guard de solapamiento por ratio en alineación (exclusión con warning, preservación de historia, invariancia sin delistings).

### Modified Capabilities
- `configuration-contract`: Nuevo parámetro `minimum_overlap_ratio` validado.
- `market-data-contract`: Alineación con guard de solapamiento y chart 4 alineado.

## Impact

- Código: `core/config.py`, `core/metrics.py`, `app/pipeline.py`, `validation/walk_forward.py`.
- Docs: `CHANGELOG.md`, `progress.md`.
- Tests: `tests/test_alignment.py` (nuevos: 50% excluido preserva 100% filas, límite 0.9, 1 superviviente, 0 supervivientes, hueco intercalado), `tests/test_pipeline_e2e.py` (chart 4 no crashea).
- Sin dependencia nueva, sin cambio de API destructivo (parámetro con default preserva `bit a bit` sin delistings).
