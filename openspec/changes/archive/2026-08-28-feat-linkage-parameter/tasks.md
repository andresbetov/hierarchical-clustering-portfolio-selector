## 1. ADR y contrato de config (rojo primero)

- [x] 1.1 Escribir ADR 006 + índice docs/adr/README.md — verificar: ADR con estado Aceptado y opciones evaluadas
- [x] 1.2 Test config: linkage_method="centroid" rechazado; default "single"; replace() preserva — verificar: rojo pre-impl (param no existe)

## 2. HRP con linkage paramétrico

- [x] 2.1 Tests en test_hrp.py: ward sobre 3 bloques de correlación (finitos, suma 1, adyacencia intra-bloque); average válido; método desconocido ValueError — verificar: rojo pre-impl (param no existe)
- [x] 2.2 Implementar: LINKAGE_METHODS + campo en config.py; firma y propagación en hrp.py; paso de config en allocation.py (ruta HRP), pipeline.py y walk_forward.py — verificar: tests 1.2 y 2.1 verdes

## 3. Verificación integral y cierre

- [x] 3.1 Red feat-021 intacta con default single (cero asserts modificados) + `./init.sh` completo exit 0 — output registrado como evidencia
- [x] 3.2 README tabla + CHANGELOG Unreleased — verificar: documentación sincronizada
