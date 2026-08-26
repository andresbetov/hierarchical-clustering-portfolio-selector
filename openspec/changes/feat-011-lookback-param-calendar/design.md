# Design: feat-011-lookback-param-calendar

## Context

A3 dejó alineación por calendario y fetcher con `risk_free_rate` requerido. El bloque temporal restante: ventana hardcodeada (5*365), end=today-1 sin conciencia de calendario bursátil explícita (Yahoo recorta igual, benigno — se conserva conducta).

## Goals / Non-Goals

**Goals:** lookback paramétrico vía config; años-calendario exactos; pure/testeabilidad de la lógica de fechas; contrato coherente con rf (ambos requeridos).
**Non-Goals:** dia-hábil para `end` (Yahoo ya limita a sesiones; behavior preservado); cache parquet; constante 252 (feat-017); congelar config (feat-013).

## Decisions

### D1 — replace-year sobre relativedelta
`end.replace(year=end.year - N)` es stdlib puro. dateutil (relativedelta) viaja transitivamente por pandas pero declararlo solo para un clamp Feb-29 es peso innecesario.
*Alternativa descartada:* `dateutil.relativedelta(years=-N)` — maneja el clamp automáticamente pero exige dependencia explícita nueva en pyproject.

### D2 — Clamp determinista a 28-feb
Solo dispara si `.replace()` lanza ValueError (único caso posible: day=29→año no-bisiesto). Comportamiento documentado en spec, testeado.

### D3 — Segundo parámetro requerido (no None-default)
Coherencia total con A2/D1-de-feat-007: cualquier default local = doble fuente. TypeError en binding es la spec ejecutable. Único caller interno (`pipeline`) pasa desde config → cero ruptura real.

### D4 — Pureza loggeable
`_resolve_window` no toca red ni estado global; pipeline logea bounds resueltos para trazabilidad del reporte (auditoría pedía "conservar window" implícito en reproducibilidad).

## Risks / Trade-offs

- Ventana cambia numéricamente vs 5*365 (hasta +2 días) — objetivo mismo del fix
- Config mutable recibe atributo antes de freeze: risk documented feat-013 lo congela con validación >0
