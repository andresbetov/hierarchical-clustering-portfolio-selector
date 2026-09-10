# Tasks: feat-report-assembler (feat-050)

## 1. Rama y registro (en la rama)

- [x] 1.1 Rama `feat/report-assembler-integration` desde `develop` limpio
- [x] 1.2 feat-050 a `in-progress` en `feature_list.json` ANTES de implementar

## 2. Análisis previo (subagentes, completado)

- [x] 2.1 Entendimiento + mapeo con blueprint (firma, placeholder, kwargs, warning, .gitignore/Makefile, tests)
- [x] 2.2 Patrones externos (OTel/MLflow fail-safe, Stripe aditivo, PEP 3102, atomic-write descartado con razón)

## 3. OpenSpec (change `feat-report-assembler`)

- [x] 3.1 `proposal.md` (modified capability `technical-report`)
- [x] 3.2 `specs/technical-report/spec.md` (+1 ADDED, 4 scenarios)
- [x] 3.3 `design.md` (10 decisiones + shape + tests + riesgos)
- [x] 3.4 `tasks.md` + change valid + `--all` 14/14

## 4. TDD rojo

- [x] 4.1 `tests/test_report_assembler.py` (10 tests); rojo 8 failures; bugs propios: naming-trap optimal/portfolio_weights, import en funcion ajena, schema en envelope, fakes sin kwarg

## 5. Implementación

- [x] 5.1 `build_technical_report` + `_risk_section` + `_resolve_report_window` + exports
- [x] 5.2 kwargs keyword-only + helper `_emit_technical_report` (N=0 fluye al punto unico; main() intacto) + fail-safe
- [x] 5.3 `cli.main` 1 linea + 3 fakes + `.gitignore reports/` + `make clean reports/*.json`
- [x] 5.4 Grupo en verde (10/10) + gates (`./init.sh` exit 0; F401 cazado)

## 6. Verificación

- [x] 6.1 `./init.sh` fresco: 358 passed, TOTAL 88.92%
- [x] 6.2 Diff acotado (core/portfolio/data/validation/viz intactos) + `--all` 14/14

## 7. Cierre (todo en la rama)

- [x] 7.1 Validación en bucle hasta APPROVE final (code + process + final)
- [x] 7.2 Trackers EN la rama; commit atómico; push → PR → CI → squash → archive
