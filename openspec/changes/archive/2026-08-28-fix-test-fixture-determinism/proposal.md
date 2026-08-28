## Why

`tests/conftest.py:23` siembra el RNG de los paneles sintéticos con `abs(hash(ticker)) % 2**32`; `hash()` de strings en Python está salado por `PYTHONHASHSEED`, así que el mismo commit produce paneles distintos según el proceso (verificado: seeds 1351879992 vs 2685522666 con `PYTHONHASHSEED=1`/`999`). La afirmación "semillas fijas en fixtures" (`README.md:103`) y el requirement de determinismo de `system-verification` son falsos en la práctica. Es el bug P0-3 del plan v0.1.0 (feat-030).

## What Changes

- `tests/conftest.py` derivará la seed por ticker con `zlib.crc32(ticker.encode())` — función estable entre procesos e independiente del salting del intérprete.
- Nuevo test de contrato en `tests/test_fixture_determinism.py`: construye el panel en subprocesos con `PYTHONHASHSEED=1` y `PYTHONHASHSEED=999` y exige bytes idénticos.
- La afirmación de `README.md` ("semillas fijas en fixtures") queda verdadera sin cambios adicionales.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `system-verification`: el requirement "Determinismo semilla-estable" se extiende para cubrir el determinismo entre procesos (independencia de `PYTHONHASHSEED`), no solo corrida-a-corrida dentro del mismo proceso.

## Impact

- Código: `tests/conftest.py` (una línea de derivación de seed).
- Tests: `tests/test_fixture_determinism.py` (nuevo, 2 subprocesos Python con seeds distintas).
- Sin cambios de API pública, sin dependencias nuevas, sin cambios de configuración.
