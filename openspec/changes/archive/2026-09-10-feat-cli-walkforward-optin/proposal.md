# Proposal: feat-cli-walkforward-optin (feat-051)

## Why

El épico JSON está completo salvo su última milla: la sección walk-forward existe como función pura (feat-049) y el ensamblador la deja en `null` (feat-050), pero ningún CLI la enciende — la validación OOS, la única evidencia de generalización, no llega al reporte. Se cablea como opt-in explícito (costosa por diseño: reestima por ventana) más el cierre documental del épico.

## What Changes

- `cli.py`: flag `--walk-forward` (`store_true`, default `False`, help documenta propósito OOS + opt-in + coste); `cli.main` reenvía `run_walk_forward=args.walk_forward` (ruta legacy lo fuerza a `False` literal, patrón `refresh=False`); la ruta legacy sigue advirtiendo argv-ignorado (test pineado, branch hits=0 hoy).
- `generate_complete_analysis_report`/`_emit_technical_report`: con flag on, `walk_forward_evaluate(historical_prices, price_dates, config)` con defaults de firma (250/60/5, sin flags de ventana), sin re-fetch; fallo → `walk_forward={"skipped": reason}` + warning nombrado (run y JSON válidos); éxito → `walk_forward_section(report)` verbatim (convenciones feat-049, sin segundo dialecto). Consola sin líneas nuevas salvo la de feat-050.
- Docs: README sección `Reporte tecnico JSON` (path fijo, schema 1, flag opt-in, in-sample vs OOS + historia "JSON siempre se emite"); CHANGELOG `Added` (una bala por feature visible); catálogo: header a implementado-con-estado + sync §8 (XOR acreción, n==2 rate 0.0, ejemplo n=6); counts stales (README tests, CONTRIBUTING baseline).
- Scope cortado: sin flags de ventana, sin pretty-print, sin path alternativo, sin auto-enable.

## Capabilities

### New Capabilities

(none — se extiende la capability existente)

### Modified Capabilities

- `technical-report`: MODIFIED requirement del ensamblador (opt-in walk-forward + dialecto skipped) con scenarios de flag on/off/corto/fallido.
