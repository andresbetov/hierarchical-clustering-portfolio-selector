## 1. Setup

- [x] 1.1 Crear la rama `feat/report-json-core` desde `develop` limpio y verificar `./init.sh` verde antes de tocar código
- [x] 1.2 Registrar feat-043 como `in-progress` en `feature_list.json` y verificar que es el único feature abierto

## 2. TDD rojo

- [x] 2.1 Crear `tests/test_report_json.py` con los tests de contrato (sanitizador round-trip, parseo estricto con parse_constant, escritura single-file, fingerprint determinista, envelope) y verificar que fallan por import error del módulo inexistente `portfolio_engine.app.report_json`
- [x] 2.2 Capturar el output rojo en la evidencia (nº de failures esperado por grupo)

## 3. Implementación

- [x] 3.1 Implementar `sanitize_json_payload` en `portfolio_engine/app/report_json.py` (np.ndarray→tolist, np.generic→item ANTES de checks float, no-finito→None, tuple→list, Path→str, date/datetime/np.datetime64→ISO-8601, recursión dict/list) y verificar el grupo de tests de sanitización en verde
- [x] 3.2 Implementar `dump_technical_report(payload, path)` (mkdir parents=True, json.dump con allow_nan=False + indent=2 + sort_keys, overwrite) y verificar el grupo de escritura en verde
- [x] 3.3 Implementar `config_fingerprint(config, tickers, window_start, window_end)` (sha256 16hex de json.dumps canonico de asdict + universo ordenado + span + engine_version via importlib.metadata) y verificar el grupo de fingerprint en verde
- [x] 3.4 Implementar `build_report_envelope(tickers, config, window_start, window_end, generated_at)` (schema_version=1, run_id derivado del fingerprint, ISO-8601 UTC) y añadir exports en `portfolio_engine/app/__init__.py`; verificar el grupo de envelope + ruff import-order en verde

## 4. Verificación del change

- [x] 4.1 Ejecutar `./init.sh` fresco en la sesión y registrar en la evidencia el TOTAL % de cobertura combinada (debe SUBIR respecto a 85.37% por el módulo nuevo ~100% cubierto) + ruff + pyright + compileall en verde
- [x] 4.2 Ejecutar `openspec validate feat-report-json-core --type change` y `openspec validate --all`; verificar que la red feat-021 no cambió (git diff cero en test_hrp/test_properties/test_walk_forward salvo lo justificado) y que ningún archivo del motor fue tocado (git diff --stat sin portfolio_engine/{app/pipeline,core,portfolio,data,validation,viz})

## 5. Cierre

- [x] 5.2 Actualizar `feature_list.json` (feat-043 done + evidencia con TOTAL %), `progress.md` y `session-handoff.md`; commit Conventional Commits en la rama; verificar `git status` limpio y presentar diff al usuario — sin push hasta su validación (regla de la sesión)
