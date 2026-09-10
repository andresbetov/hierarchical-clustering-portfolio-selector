# Spec delta: technical-report (feat-051, MODIFIED)

## MODIFIED Requirements

### Requirement: Ensamblador del reporte con emisión fail-safe

El sistema SHALL componer el reporte técnico mediante `build_technical_report` puro a partir de las secciones verificadas (envelope, exclusiones, asignación, riesgo in-sample, árbol) más la sección walk-forward. `generate_complete_analysis_report` SHALL aceptar `report_path` keyword-only default `None` (sin escribir nada por defecto) y `run_walk_forward` default `False`; con `report_path` fijado SHALL construir y volcar el JSON tras el log final, y cualquier fallo del reporte SHALL degradarse a un warning nombrado sin romper el run (la tupla de retorno intacta). Con `run_walk_forward` activo SHALL ejecutar `walk_forward_evaluate` sobre el bundle ya desempaquetado con sus defaults (sin re-fetch) y SHALL serializar `walk_forward_section(report)` verbatim; si la evaluación falla SHALL emitirse `walk_forward: {"skipped": "<motivo>"}` con warning nombrado, run y JSON válidos. Sin el flag, `walk_forward` SHALL ser `null` (opt-in apagado). La consola SHALL permanecer intacta salvo una línea `logger.info` de escritura. `cli.main` SHALL pasar `report_path="reports/technical-report.json"` (el JSON siempre se emite; `--no-save` gobierna solo los plots) y SHALL exponer `--walk-forward` opt-in (default off) reenviado como `run_walk_forward` (la ruta legacy lo fuerza a off).

#### Scenario: E2E offline emite JSON estricto completo

- **WHEN** el pipeline corre offline con `report_path` fijado
- **THEN** existe un solo JSON que parsea estricto, con envelope (`schema_version == 1`, fingerprint equals recompute independiente) y las secciones con sus keys

#### Scenario: default no escribe nada

- **WHEN** el pipeline corre sin `report_path`
- **THEN** no se crea ningún archivo ni directorio `reports/` y el retorno es la 4-tupla intacta

#### Scenario: fallo del reporte no rompe el run

- **WHEN** la escritura del reporte eleva (inyectado en test)
- **THEN** se loggea warning nombrado, el run completa y retorna la 4-tupla

#### Scenario: --no-save emite JSON igual

- **WHEN** el pipeline corre con `save_plots=False` y `report_path` fijado
- **THEN** el JSON se emite (el flag gobierna solo plots) y ningún PNG se escribe

#### Scenario: walk-forward opt-in cableado

- **WHEN** el pipeline corre con `run_walk_forward=True` sobre bundle largo offline
- **THEN** `walk_forward.median_oos_sharpe` es no-null (vía agregados verbatim), hay filas por fold y `drift.median_l1` computado

#### Scenario: bundle corto degrada a skipped con motivo

- **WHEN** el bundle no alcanza filas para una ventana (p. ej. 20 filas)
- **THEN** `walk_forward == {"skipped": "<motivo>"}`, el JSON parsea estricto y el run retorna exit 0

#### Scenario: flag apagado deja null

- **WHEN** el pipeline corre con `report_path` pero sin opt-in
- **THEN** `walk_forward` es `null` y `schema_version` permanece 1
