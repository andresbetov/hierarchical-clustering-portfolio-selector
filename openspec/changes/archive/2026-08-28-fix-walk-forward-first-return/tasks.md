## 1. TDD — regresión en rojo

- [x] 1.1 Escribir test analítico en `tests/test_walk_forward.py`: bundle de 3 activos con retornos idénticos, spike 0.5 en el primer día del test y 0.02 en el segundo; verificar que pre-fix el retorno OOS excluye el spike (rojo: mediana != 0.52/60·252)
- [x] 1.2 Verificar que el test anti-fuga y los tests de `_iter_walk_windows` existentes siguen verdes antes del fix (línea base sin regresión)

## 2. Fix de producción

- [x] 2.1 Reemplazar el bloque `np.roll`+`[1:]` por ventana extendida `[test_start−1, test_end)` con diff logarítmico directo en `walk_forward.py` y verificar que el test 1.1 pasa (verde, valor exacto 0.52/60·252)

## 3. Verificación integral

- [x] 3.1 Correr `./init.sh` completo y verificar exit 0 con suite verde (157 tests + nuevos) — output registrado como evidencia
- [x] 3.2 Verificar que la red feat-021/feat-026 no tuvo asserts modificados y que `make lint` / `make types` pasan sin hallazgos nuevos
