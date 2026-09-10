# Tasks: docs-spec-sync (feat-053)

## 1. Rama y registro (en la rama)

- [x] 1.1 Rama `docs/spec-sync` desde `develop` limpio (post-merge #80)
- [x] 1.2 feat-053 a `in-progress` en `feature_list.json` ANTES de implementar; feat-052 a `done` con evidencia de merge

## 2. OpenSpec (change `docs-spec-sync`)

- [x] 2.1 `proposal.md` (sync de erratas, 0 cambios de comportamiento)
- [x] 2.2 `design.md` (14 decisiones documentadas)
- [x] 2.3 `specs/*/spec.md` (10 deltas: 8 MODIFIED + 2 ADDED)
- [x] 2.4 `openspec validate docs-spec-sync` verde (+2 fixes de scenarios)

## 3. Fase 1 — docs de proceso

- [x] 3.1 CONTRIBUTING (baseline 367/89.18%, pyarrow runtime, gates, pre-commit)
- [x] 3.2 AGENTS (5 pasos de verificación)
- [x] 3.3 pyproject comentario TOTAL combinado (+ `init.sh` a `uv sync --frozen`)
- [x] 3.4 Makefile .PHONY + help
- [x] 3.5 .pre-commit comando unificado
- [x] 3.6 ADR index + addendum 003 (ADR 008 futuro + refs)
- [x] 3.7 diagnostics-catalog (6 refs, mapeo 9 fichas→6 secciones, umbral 12→6)
- [x] 3.8 feature_list refs podadas + typo ADR002
- [x] 3.9 scripts/charts regenerado en feat-052 (8 PNG verificados)

## 4. Fase 2 — archive + sync a specs vivas

- [ ] 4.1 Rama `chore/archive-docs-spec-sync`; aplicar deltas a las 10 specs
- [ ] 4.2 `openspec validate --all` 13/13

## 5. Verificación

- [x] 5.1 `./init.sh` fresco (367 passed, TOTAL 89.18%, con `uv sync --frozen`)
- [x] 5.2 Greps anti-regresión (sin vol-target en specs vivas, sin "fijación iterativa", sin "85% branch" en quality-gates, sin "233 tests" en docs vivos)

## 6. Cierre (todo en la rama)

- [ ] 6.1 Trackers (feat-053 done con evidencia, progress, handoff)
- [ ] 6.2 Commit atómico; push → PR → CI → squash → archive del change
