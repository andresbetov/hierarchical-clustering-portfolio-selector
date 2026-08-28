## 1. TDD — regresión en rojo

- [x] 1.1 Escribir `tests/test_fixture_determinism.py`: construir el panel en subprocesos con PYTHONHASHSEED=1 y PYTHONHASHSEED=999 y verificar que pre-fix los bytes difieren (rojo registrado)
- [x] 1.2 Verificar que la suite existente sigue verde con los paneles vigentes (línea base sin regresión)

## 2. Fix de producción

- [x] 2.1 Reemplazar `abs(hash(ticker)) % 2**32` por `zlib.crc32(ticker.encode())` en `tests/conftest.py` y verificar que el test 1.1 pasa (verde: bytes idénticos)

## 3. Verificación integral

- [x] 3.1 Correr `./init.sh` completo y verificar exit 0 con suite verde (158 tests + nuevos) — output registrado como evidencia
- [x] 3.2 Verificar que la red feat-021/feat-026 no tuvo asserts modificados y que `make lint` / `make types` pasan sin hallazgos nuevos
