# Tasks: feat-cli-walkforward-optin (feat-051)

## 1. Rama y registro (en la rama)

- [x] 1.1 Rama `feat/cli-walkforward-optin-docs` desde `develop` (@be8c2d1 limpio)
- [x] 1.2 feat-051 a `in-progress` en `feature_list.json` ANTES de implementar

## 2. Análisis previo (subagentes, completado)

- [x] 2.1 Entendimiento + mapeo con blueprint (firma, skipped-dialecto, legacy-off, argv-warning, MODIFIED mechanics, docs edits)
- [x] 2.2 Patrones externos (store_true opt-in, Perold/PBO coste, GIPS disclaimer, Keep-a-Changelog, JUnit/GX skipped, coverage TOTAL)

## 3. OpenSpec (change `feat-cli-walkforward-optin`)

- [x] 3.1 `proposal.md` (modified capability `technical-report`)
- [x] 3.2 `specs/technical-report/spec.md` (MODIFIED con requirement completo + 7 scenarios)
- [x] 3.3 `design.md` (8 decisiones + tests + riesgos)
- [x] 3.4 `tasks.md` + change valid + `--all` 14/14

## 4. TDD rojo

- [x] 4.1 Tests CLI (4) + ensamblador (4); rojo 7 failures; verde 29/29 en ambos archivos

## 5. Implementación

- [x] 5.1 Flag `--walk-forward` + forwards (normal + legacy off literal)
- [x] 5.2 `_evaluate_walk_forward_section` (defaults, ValueError/genérico → skipped, sección verbatim)
- [x] 5.3 Docs (README sección + counts, CHANGELOG Added, catálogo header + §8 sync, CONTRIBUTING baseline)
- [x] 5.4 Grupo en verde + gates (`./init.sh` exit 0; I001 cazado 2x)

## 6. Verificación

- [x] 6.1 `./init.sh` fresco: 365 passed, TOTAL 89.18%
- [x] 6.2 Diff acotado (core/portfolio/data/validation/viz intactos) + `--all` 14/14

## 7. Cierre (todo en la rama)

- [x] 7.1 Validación en bucle hasta APPROVE final (2x CONDITIONAL + final)
- [x] 7.2 Trackers EN la rama; commit atómico; push → PR → CI → squash → archive + cierre del épico
