## 1. Corrección de specs merged

- [x] 1.1 `configuration-contract`: set de métodos {equal, inverse_volatility, risk_parity, max_sharpe, min_variance, hrp} y errata SHANL→SHALL — verificar: grep SHANL = 0 y set == enum del código
- [x] 1.2 `numeric-correctness`: corregir doble negación "no SHALL NO coexistir" — verificar: openspec validate --specs
- [x] 1.3 `project-packaging`: rango de Python honesto >=3.11 y matriz CI 3.11-3.13 (preparación feat-032) — verificar: openspec validate --specs

## 2. Históricos y CHANGELOG

- [x] 2.1 Marcar todos los boxes de `openspec/changes/archive/2026-08-26-feat-018-*/tasks.md` (cierre retroactivo con nota) — verificar: 0 boxes sin marcar en ese archivo
- [x] 2.2 Crear `CHANGELOG.md` formato Keep a Changelog (Unreleased con Added/Changed/Fixed de feat-028..031 y lista 0.1.0 pendiente) — verificar: formato canónico (secciones, fechas ISO)

## 3. Limpieza del tracker de sesión

- [x] 3.1 Reescribir `progress.md`: un solo bloque What's Next (feat-032..041), sin secciones duplicadas ni restos de sesiones antiguas, preservando Blockers/Risks y Process Deviations — verificar: grep "What's Next" cuenta == 1
- [x] 3.2 Verificación integral: `./init.sh` exit 0 (docs-only, sin regresión) + `openspec validate --specs` — output registrado como evidencia
