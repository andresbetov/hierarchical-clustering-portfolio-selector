## 1. TDD — regresiones en rojo

- [x] 1.1 Test paridad de filtros: bundle con activo "malo en train temprano / bueno después" — verificar rojo pre-impl: fold 0 hoy INCLUYE al activo malo (pesos == universo completo)
- [x] 1.2 Test benchmarks: claves nuevas en to_dict + activos idénticos hacen coincidir medianas engine/equal/ivp + benchmarks inmunes a mutación OOS — verificar rojo pre-impl (claves inexistentes)
- [x] 1.3 Test fold sin supervivientes → inválido con warning — verificar rojo pre-impl (hoy sin filtros nunca ocurre)

## 2. Implementación

- [x] 2.1 Métricas por fold desde columnas de train + `apply_asset_filters` (umbrales de config) → supervivientes; fold sin supervivientes → ValueError (D1/D7) — verificar: test 1.1 y 1.3 verdes en la parte de filtrado
- [x] 2.2 Vector de pesos con ceros en excluidos (D2) + benchmarks equal/ivp ex-ante sobre supervivientes con mismos retornos OOS (D3/D5) + `benchmarks` en fold y 6 medianas en `to_dict` (D4) — verificar: tests 1.1 y 1.2 verdes completos

## 3. Validación iterativa y cierre

- [x] 3.1 Revisión de implementation con subagente (leakage, alineación de columnas, edge cases n=1/n=0, contratos existentes) — hallazgos corregidos y re-verificados
- [x] 3.2 Fixtures existentes ajustados a umbrales relajados (D6, asserts intactos) + suite completa `./init.sh` exit 0 — output registrado como evidencia
- [x] 3.3 README (sección Validación: paridad + benchmarks + disciplina embargo/purga) + CHANGELOG — verificar: docs sincronizadas
