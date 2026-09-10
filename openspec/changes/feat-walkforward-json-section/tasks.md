# Tasks: feat-walkforward-json-section (feat-049)

## 1. Rama y registro (en la rama)

- [x] 1.1 Crear la rama `feat/walkforward-json-section` desde `develop` limpio
- [x] 1.2 Actualizar feat-049 a `in-progress` en `feature_list.json` ANTES de implementar

## 2. Análisis previo (subagentes, completado)

- [x] 2.1 Entendimiento + mapeo (propósito, checklist, rulings firmes, file:line de seams)
- [x] 2.2 Búsqueda externa verificable (L1 two-way, zero-embed, GIPS chain-break, H&F-7 p90, Perold drift≠turnover + top-5)

## 3. OpenSpec (change `feat-walkforward-json-section`)

- [x] 3.1 `proposal.md` (modified capability `technical-report`)
- [x] 3.2 `specs/technical-report/spec.md` (+1 ADDED, 7 scenarios)
- [x] 3.3 `design.md` (8 decisiones + shape + tests + riesgos + no-goals)
- [x] 3.4 `tasks.md` + change valid + `--all` 14/14

## 4. TDD rojo

- [x] 4.1 Clase `TestWalkForwardSection` (13 tests); rojo 11 ImportError; verde incluye evaluate real + churn + median/p90 + strict-JSON

## 5. Implementación (append-only en `report_json.py`)

- [x] 5.1 `walk_forward_section(report)` + helpers + exports (deep-copy benchmarks tras review)
- [x] 5.2 Grupo en verde + gates (`./init.sh` exit 0)

## 6. Verificación del change

- [x] 6.1 `./init.sh` fresco: 348 passed, TOTAL 88.19%
- [x] 6.2 Motor intocado (`walk_forward.py` diff cero) + `--all` 14/14

## 7. Cierre (todo en la rama)

- [x] 7.1 Validación en bucle hasta APPROVE final (code + process + final)
- [x] 7.2 Trackers EN la rama; commit atómico; luego push → PR → CI → squash → archive
