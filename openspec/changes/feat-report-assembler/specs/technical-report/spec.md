# Spec delta: technical-report (feat-050)

## ADDED Requirements

### Requirement: Ensamblador del reporte con emisión fail-safe

El sistema SHALL componer el reporte técnico mediante `build_technical_report` puro a partir de las secciones verificadas (envelope, exclusiones, asignación, riesgo in-sample, árbol) más `walk_forward: None` como placeholder presente-con-null (feat-051 lo llena con la sección real). `generate_complete_analysis_report` SHALL aceptar `report_path` keyword-only default `None` (sin escribir nada por defecto) y `run_walk_forward` reservado default `False`; con `report_path` fijado SHALL construir y volcar el JSON tras el log final, y cualquier fallo del reporte SHALL degradarse a un warning nombrado sin romper el run (la tupla de retorno intacta). La consola SHALL permanecer intacta salvo una línea `logger.info` de escritura. `cli.main` SHALL pasar `report_path="reports/technical-report.json"` (el JSON siempre se emite; `--no-save` gobierna solo los plots).

#### Scenario: E2E offline emite JSON estricto completo

- **WHEN** el pipeline corre offline con `report_path` fijado
- **THEN** existe un solo JSON que parsea estricto, con envelope (`schema_version == 1`, fingerprint equals recompute independiente) y las 6 secciones con sus keys, `walk_forward` null

#### Scenario: default no escribe nada

- **WHEN** el pipeline corre sin `report_path`
- **THEN** no se crea ningún archivo ni directorio `reports/` y el retorno es la 4-tupla intacta

#### Scenario: fallo del reporte no rompe el run

- **WHEN** la escritura del reporte eleva (inyectado en test)
- **THEN** se loggea warning nombrado, el run completa y retorna la 4-tupla

#### Scenario: --no-save emite JSON igual

- **WHEN** el pipeline corre con `save_plots=False` y `report_path` fijado
- **THEN** el JSON se emite (el flag gobierna solo plots) y ningún PNG se escribe
