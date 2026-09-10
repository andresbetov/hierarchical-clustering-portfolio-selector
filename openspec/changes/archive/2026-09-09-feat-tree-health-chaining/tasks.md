# Tasks: feat-tree-health-chaining (feat-048)

## 1. Rama y registro (en la rama)

- [x] 1.1 Crear la rama `feat/tree-health-depth-chaining` desde `develop` limpio y verificar baseline verde (322 passed)
- [x] 1.2 Actualizar feat-048 a `in-progress` en `feature_list.json` ANTES de implementar + errata de definición (decisión de usuario: acreción exactamente-un-lado)

## 2. Análisis previo (subagentes, completado)

- [x] 2.1 Entendimiento (seams hrp.py, patrón test_dendrogram, invariante runtime-diagnostics, checklist, riesgos singleton/flag-n2)
- [x] 2.2 Búsqueda externa verificable (chaining Sibson/Manning, Sackin/Colless, anatomía Z SciPy, ward-euclidiana, CPCC excluido + top-5)
- [x] 2.3 Mapeo ([DEPENDENCY] `build_hrp_linkage` + `_leaf_order`; resto [CONTEXT]; [MODIFY] solo `report_json.py` + tests)
- [x] 2.4 Hallazgo propio verificado empíricamente: piso 0.5 de ≥1-hoja → pregunta al usuario → acreción exacta decidida

## 3. OpenSpec (change `feat-tree-health-chaining`)

- [x] 3.1 `proposal.md` (modified capability `technical-report`)
- [x] 3.2 `specs/technical-report/spec.md` (+1 ADDED, 8 scenarios)
- [x] 3.3 `design.md` (11 decisiones + keys + tests + riesgos)
- [x] 3.4 `tasks.md` (este archivo) + `openspec validate feat-tree-health-chaining --type change` en verde

## 4. TDD rojo

- [x] 4.1 Clase `TestTreeDiagnostics` (13 tests); rojo 10 failures (9 ImportError + 1 export); bug propio: n==2 rate 0.0 no 1.0 (XOR; spec/tracker corregidos)

## 5. Implementación (append-only en `report_json.py`)

- [x] 5.1 `tree_diagnostics(covariance_matrix, linkage_method="single")` (pre-chequeo n<2; square/ragged nombrados; recompute Z; DP profundidad; XOR acreción; carve-out n==2; umbrales eco; leaf_order del motor; guards trading n/a) + exports + tests de mutantes (thresholds, depth-fire n=8, fail-loud, precedencia)
- [x] 5.2 Grupo en verde (13/13) + ruff (2×E501 docstring cazados) + pyright en la iteración de gate

## 6. Verificación del change

- [x] 6.1 `./init.sh` fresco con TOTAL % (88.01% ≥ 87.61%) y suite verde (335 passed)
- [x] 6.2 Motor intocado (`hrp.py` diff cero; sin archivos en core/portfolio/data/validation/viz/pipeline/cli) + `openspec validate --all` verde (14/14)

## 7. Cierre (todo en la rama)

- [x] 7.1 Validación pre-push con subagentes en bucle hasta APPROVE final (code-CONDITIONAL + process-CONDITIONAL -> fixes -> APPROVE)
- [x] 7.2 `feature_list.json` (done + evidencia), `progress.md`, `session-handoff.md` EN la rama; commit atómico; luego push → PR → CI → squash → archive vía rama chore
