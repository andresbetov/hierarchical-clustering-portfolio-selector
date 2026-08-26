# Design: feat-008-returns-date-alignment

## Context

Matrices actuales se apilan por posición. `price_dates` existe por ticker pero solo alimenta charts. pandas ya viaja transitivamente vía yfinance.

## Goals / Non-Goals

**Goals:** intersección de calendario como fuente de toda matriz multivariada; fallos ruidosos; legacy equal-length intacto.
**Non-Goals:** outer/ffill (B6), validación del fetcher (feat-012), EWMA/shrinkage (C1/feat-019), performance (feat-022).

## Decisions

### D1 — inner-join como único modo hoy
Corrección > cobertura: mejor perder filas que mezclar fechas. Outer+ffill introduce look-ahead sutil y es decisión de backtest (diferida a B6 con rationale en decision-log).

### D2 — implementación via pandas DataFrame inner
`pd.DataFrame({t: pd.Series(v, index=pd.DatetimeIndex(d))})` → `.dropna(how="any")` = intersección natural, código mínimo y estándar de la industria. NumPy puro sería reinventar join + sort + dedupe.
*Alternativa descartada:* intersection manual por sets de int64 timestamps — más código frágil sin beneficio (pandas ya declarado).

### D3 — guard separado del aligner
`construct_returns_matrix` NO cambia firma: lanza ValueError si longitudes difieren (para que nadie apile sin alinear ni saberlo). El aligner devuelve dict recortado; pipeline lo pasa tal cual. Tests existentes igual-longitud no necesitan cambios.

### D4 — densidad mínima = 2 filas comunes
Menos de 2 => retornos degenerados. Constante visible `MIN_COMMON_ROWS = 2`.

## Risks / Trade-offs

- Universos reales con historiales dispares producirán matrices más cortas — esperado y auditable vía logging (rows antes/después)
- dtype index: DatetimeIndex normalizado a ns; tz-aware serían convertidos por pandas — los índices de yfinance son tz-naive; documentado en docstring
