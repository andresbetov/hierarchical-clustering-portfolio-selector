## 1. ADR y contrato de config (rojo primero)

- [x] 1.1 Escribir ADR 005 + índice docs/adr/README.md — verificar: ADR con estado Aceptado y opciones evaluadas
- [x] 1.2 Test config: covariance_estimator="otro" rechazado con ValueError; default "sample"; replace() preserva — verificar: test falla pre-impl (param no existe)

## 2. Seam de estimación

- [x] 2.1 Test de contrato de la seam (paridad sklearn 1e-12, sample bit a bit, degeneración NaN, condition number ≤) — verificar: rojo pre-impl (función inexistente)
- [x] 2.2 Implementar `estimate_covariance` en core/metrics.py + enum/validación en config.py + consumo en pipeline.py y walk_forward.py + export __init__ — verificar: tests 1.2 y 2.1 verdes

## 3. E2E y cierre

- [x] 3.1 Test E2E offline con covariance_estimator="ledoit_wolf" (weights finitos suma 1) y red feat-021 intacta sin asserts modificados — verificar: verde
- [x] 3.2 `./init.sh` completo exit 0 + README tabla + CHANGELOG Unreleased — output registrado como evidencia
