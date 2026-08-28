## Context

Ver proposal.md (Why) y el delta de `system-verification` (What). Estado relevante: `conftest.py:11-40` construye paneles con `np.random.default_rng(abs(hash(ticker)) % 2**32)` (línea 23); el resto del panel es determinista dado el RNG (drift fijo, holes, NaN colas). Los asserts de la suite son invariantes (no dependen del valor exacto del panel), por eso el defecto nunca rompió tests — es un defecto de reproducibilidad, no de corrección funcional. `_build_panel` está en `__all__` de conftest y es importable con cwd=tests.

## Goals / Non-Goals

**Goals:**
- Mismo commit ⇒ mismos paneles en cualquier proceso/intérprete (independencia de PYTHONHASHSEED).
- Test de regresión que verifica el contrato vía subprocesos reales con seeds saladas distintas.
- Cero cambios en la forma/distribución estadística de los paneles dentro de un mismo proceso respecto al comportamiento vigente (los valores cambian — ya no dependen del salting — pero la estructura y magnitud se preservan).

**Non-Goals:**
- No migrar los `np.random.seed`/`default_rng` explícitos de otros tests (ya son estables por literal).
- No cambiar conftest más allá de la derivación de seed.

## Decisions

**D1 — `zlib.crc32(ticker.encode())` como derivación estable.** CRC32 es determinista entre procesos y versiones de Python, suficiente entropía para decenas de tickers, y stdlib puro. Alternativas descartadas: `hashlib.sha256(...)` + truncado (más verboso, misma garantía práctica), seed por índice de enumeración (depende del orden del dict — estable aquí, pero acoplado a la estructura del spec), `random.Random(ticker)` con seed por string (internamente usa el string sin salting — viable, pero menos explícito).

**D2 — Test vía subprocesos reales:** `subprocess.run([sys.executable, "-c", ...], env={... PYTHONHASHSEED: 1|999}, cwd="tests")` que importa `conftest`, construye el panel y lo imprime en base64; el test compara ambos outputs. Alternativa descartada: assert estático de que la línea no usa `hash` (frágil, no verifica comportamiento).

**D3 — Sin cambio de asserts existentes:** el resto de la suite sigue verde con los nuevos paneles (los asserts son invariantes por diseño de feat-021).

## Risks / Trade-offs

- [Subproceso añade ~1s al runtime de la suite] → Mitigación: un solo test con dos subprocesos ligeros (construcción de un panel de 20 filas).
- [Los paneles cambian de valores respecto a corridas anteriores] → esperado y deseado (ahora sí estables); la red feat-021 no pinea valores de paneles, solo invariantes.
- [`sys.executable` bajo `uv run pytest`] → apunta al venv del proyecto con numpy/pandas disponibles; verificado en el arranque del test (si el subproceso fallara, el test lo reporta como error explícito).

## Migration Plan

Sin migración: cambio interno al harness de tests. Rollback = revert del commit.
