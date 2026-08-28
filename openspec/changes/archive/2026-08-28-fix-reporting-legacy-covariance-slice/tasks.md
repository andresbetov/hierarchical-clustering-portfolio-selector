## 1. TDD — regresión en rojo

- [x] 1.1 Escribir test E2E offline de ruta legacy (risk_parity) con pruning M<N que invoca `generate_complete_analysis_report` con provider sintético y verificar que FALLA con error de broadcasting antes del fix (rojo registrado en evidencia)
- [x] 1.2 Escribir test unitario del resumen: `_portfolio_summary_metrics` con covarianza rebanada M×M produce Sharpe == cálculo manual wᵀΣw y verificar que el caso M<N hoy no puede construirse sin crash (rojo/contrato documentado)

## 2. Fix de producción

- [x] 2.1 Rebanar la covarianza en `pipeline.py` reutilizando `create_portfolio_covariance_matrix` antes de `plot_optimal_portfolio_analysis` y verificar que el test 1.1 pasa (verde)

## 3. Verificación integral

- [x] 3.1 Correr `./init.sh` completo y verificar exit 0 con suite verde (154 tests + nuevos) — output registrado como evidencia
- [x] 3.2 Verificar que la red feat-021 no tuvo asserts modificados y que `make lint` / `make types` pasan sin hallazgos nuevos
