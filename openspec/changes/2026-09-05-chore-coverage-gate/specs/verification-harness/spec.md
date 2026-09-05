## MODIFIED Requirements

### Requirement: Target test ejecuta la suite real
El target `test` del Makefile SHALL ejecutar pytest **con cobertura** sobre la suite offline declarada en `tests/` (`--cov=portfolio_engine --cov-report=term-missing --cov-report=html --cov-report=xml --cov-branch --cov-fail-under=85`) y SHALL NO referenciar archivos inexistentes; un target `test-no-cov` SHALL existir como escape hatch (`--no-cov -q`).

#### Scenario: make test con suite presente
- **WHEN** un desarrollador ejecuta `make test` en un entorno sincronizado (deps instaladas)
- **THEN** pytest corre los tests de `tests/` con reporte de cobertura `TOTAL ... 85%` y el exit code refleja su resultado real (0 verde, distinto de 0 si fallan tests o cobertura <85)

### Requirement: Harness local ejecuta todos los gates
Cuando uv está disponible, `init.sh` SHALL ejecutar — además de sync, pytest y compileall — los gates lint y types; **pytest heredará `addopts` con cobertura** cuando `pytest-cov` esté instalado, de lo contrario degradará sin gate pero sin romper `compileall`.

#### Scenario: sesión de agente con uv
- **WHEN** un agente ejecuta `./init.sh` antes de marcar done
- **THEN** ningún gate queda silenciosamente omitido si sus herramientas están instaladas por uv, y el reporte de cobertura aparece en el log de pytest si disponible

## ADDED Requirements

### Requirement: Artefactos de cobertura ignorados
`.gitignore` SHALL listar `.coverage` y `htmlcov/` y `coverage.xml`, de modo que artefactos de cobertura nunca se commiteen.

#### Scenario: artefactos no versionados
- **WHEN** se genera `htmlcov/` o `.coverage` tras `make test`
- **THEN** `git status` permanece limpio (ignorado)
