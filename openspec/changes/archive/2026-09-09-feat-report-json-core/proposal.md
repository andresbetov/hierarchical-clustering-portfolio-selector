## Why

El pipeline entrega sus resultados solo como consola y PNGs: un consumidor técnico (script, notebook, CI) no puede leer los resultados de una corrida ni compararlos entre corridas sin re-analizar el programa. La ausencia de un reporte machine-readable es el primer bloqueo del épico feat-043..051 (docs/diagnostics-catalog.md): sin nucleo de serialización, fingerprint y envelope versionado no existe contrato sobre el que integrar las secciones de diagnósticos posteriores.

## What Changes

- Nuevo módulo `portfolio_engine/app/report_json.py` con cuatro piezas puras: `sanitize_json_payload` (ndarray→list, np.generic→escalar Python, no-finito→None, tuple→list, Path→str, date/datetime→ISO-8601), `dump_technical_report` (un solo archivo por corrida, `json.dump(allow_nan=False)`), `config_fingerprint` (sha256 16-hex de la configuración canónica + universo ordenado + span + engine_version), `build_report_envelope` (schema_version=1 ausente-tolerante, run_id derivado del fingerprint).
- Exports públicos del módulo desde `portfolio_engine/app/__init__.py` (capa de orquestación; el `__init__` del paquete se completa en feat-050).
- Sin integración en pipeline/CLI (eso es feat-050/051): cero cambios de comportamiento en la corrida actual.

## Capabilities

### New Capabilities

- `technical-report`: contrato de salida machine-readable — sanitizador JSON estricto (null = no-finito/indefinido, nunca NaN/Infinity tokens), envelope versionado con fingerprint determinista, escritor single-file. El resto del épico (rejections, allocation, risk, tree, walk-forward, integración, CLI) acrecenta requirements ADDED sobre esta misma capability en changes posteriores.

### Modified Capabilities

(Ninguna — los specs existentes no cambian.)

## Impact

- Código: 1 módulo nuevo (~60 stmts) + `app/__init__.py` exports; cero cambios en el motor (pipeline, allocation, hrp, selection, walk_forward intocados — red feat-021 diff 0).
- Tests: `tests/test_report_json.py` nuevo (TDD rojo→verde).
- Dependencias: ninguna nueva (stdlib `json`, `math`, `hashlib`, `dataclasses`, `importlib.metadata`).
- Sin cambio en default de corrida: nada escribe `reports/` todavía.
