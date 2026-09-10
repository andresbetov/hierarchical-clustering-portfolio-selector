## 1. Rama y baseline

- [x] 1.1 Crear la rama `feat/threshold-recalibration` desde `develop` limpio y verificar que `./init.sh` pasa en verde antes de tocar código
- [x] 1.2 Registrar `feat-042` en `feature_list.json` (deps `[feat-041]`, estado `in-progress`) y verificar que es el único feature abierto

## 2. Decisión permanente

- [x] 2.1 Redactar `docs/adr/007-*.md` con contexto, alternativas (mantener / 0.3-0.27 / top-K por sleeve), decisión y consecuencias, y añadir su fila al índice `docs/adr/README.md`; verificar que el índice lista 007 como Aceptado

## 3. Implementación

- [x] 3.1 Cambiar los defaults en `portfolio_engine/core/config.py:52-53` a `0.3`/`0.27` y verificar que `python -c "from portfolio_engine.core.config import PortfolioConfig; ..."` reporta los nuevos valores
- [x] 3.2 Actualizar la tabla de configuración en `README.md:42-43` y añadir entrada `Changed` en `CHANGELOG.md (Unreleased)`; verificar con `grep` que no quedan referencias a los defaults antiguos en docs
- [x] 3.3 Actualizar los pinnings `test_config.py:27,77` a `0.3` citando feat-042 y verificar que el resto de la suite que usa thresholds explícitos sigue intacta (`git diff` en tests solo donde se justifica)

## 4. Tests nuevos

- [x] 4.1 Añadir test de contrato de los defaults recalibrados (construcción, `replace`-pattern, validación de rangos intacta) y verificar que pasa con `pytest tests/test_config.py`
- [x] 4.2 Añadir test de regresión walk-forward sintético CI-safe (panel de 6 activos con dispersión donde HRP ≥ equal en mediana con thresholds recalibrados) y verificar que falla con los defaults antiguos y pasa con los nuevos

## 5. Verificación y cierre

- [x] 5.1 Ejecutar `./init.sh` fresco en la sesión y verificar exit 0 (pytest + ruff + pyright + compileall), más `openspec validate` del change en verde
- [x] 5.2 Actualizar `feature_list.json` (done + evidencia), `progress.md` y `session-handoff.md`, hacer commit Conventional Commits en la rama y verificar `git status` limpio; presentar el diff al usuario y esperar validación — sin push (veto explícito)
