# Hierarchical Clustering Portfolio Selector

[![CI](https://github.com/andresbetov/hierarchical-clustering-portfolio-selector/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/andresbetov/hierarchical-clustering-portfolio-selector/actions/workflows/ci.yml)

Pipeline cuantitativo para construir carteras de renta variable con enfoque de diversificación jerárquica. El motor descarga precios ajustados en lote, alinea calendarios entre activos, filtra por calidad riesgo-retorno, reduce redundancia con clustering sobre distancia firmada y asigna pesos con Hierarchical Risk Parity (sin invertir la covarianza) bajo límites de concentración verificados.

## Resumen ejecutivo

Este proyecto resuelve un problema concreto: pasar de un universo amplio de activos a una cartera interpretable, reproducible y validada temporalmente sin decisiones discrecionales. El valor no es predecir precios sino estructurar una selección robusta donde activos redundantes pierden prioridad frente a fuentes de riesgo genuinamente distintas.

El flujo termina en artefactos accionables: pesos por activo (todos los supervivientes del filtro con HRP), resumen ejecutivo con Sharpe calculado sobre covarianza real, siete gráficas de diagnóstico y un motor opcional de validación walk-forward out-of-sample.

## Instalación y ejecución

```bash
uv sync
uv run portfolio-run
```

El universo vive en `config/universe.yaml` (un ticker por entrada; cámbialo para analizar otro mercado). La ejecución genera el resumen en consola y las figuras del reporte en `charts/`; `scripts/charts/` conserva ejemplos históricos. El entrypoint legacy `uv run scripts/assets-investment.py` delega en el mismo código.

## Metodología de selección

Cinco etapas encadenadas, cada una con contrato testado:

1. **Ingesta** — descarga batch de precios ajustados con reintentos acotados; rechazos nombrados por ticker (`data/provider.py` + `data/data_fetch.py`).
2. **Alineación** — intersección de calendarios antes de cualquier estadística; una fila comparada contra fecha ajena es imposible.
3. **Filtrado** — Sharpe mínimo y volatilidad máxima; métricas no finitas se excluyen nombrando el motivo.
4. **Clustering + asignación HRP** — distancia firmada `sqrt(0.5·(1-corr))` (los hedges nunca se fusionan con gemelos), linkage → quasi-diagonalization → bisección recursiva por varianza inversa. Sin inversión de matrices.
5. **Constraints** — límites 0.05–0.30 satisfechos simultáneamente mediante proyecciones cíclicas (Dykstra), con verificación final dura.

Opcionalmente, `portfolio_engine/validation/walk_forward.py` evalúa el motor out-of-sample: pesos fijados en la ventana de entrenamiento, aplicados congelada sobre ventanas futuras separadas por embargo.

Las decisiones metodológicas están versionadas como ADRs en [docs/adr/](docs/adr/README.md).

## Configuración clave por defecto

`PortfolioConfig` es inmutable y validado en construcción (contrato en `openspec/specs/configuration-contract`). Parámetros que gobiernan directamente el resultado:

| Grupo | Parámetro | Valor |
| --- | --- | --- |
| Filtrado | `minimum_sharpe_threshold` | `0.5` |
| Filtrado | `maximum_volatility_threshold` | `0.25` |
| Clustering | `maximum_correlation_threshold` | `0.65` |
| Clustering | `distance_metric` | `signed` |
| Datos | `lookback_years` | `5` |
| Datos | `trading_days_per_year` | `252` |
| Riesgo | `risk_free_rate` | `0.045` |
| Asignación | `weight_allocation_method` | `hrp` |
| Asignación | `minimum_single_asset_weight` | `0.05` |
| Asignación | `maximum_single_asset_weight` | `0.30` |

Métodos alternativos disponibles vía config: `equal`, `inverse_volatility`, `risk_parity`, `max_sharpe`, `min_variance`.

## Cómo interpretar los resultados

La lectura es secuencial. Si el universo filtrado cae demasiado, los umbrales son duros para ese conjunto de activos. Con HRP, el número final de asignados tiende a ser mayor que en el flujo legacy porque la distancia firmada fusiona menos pares. Si los pesos quedan pegados a los límites, la estructura de riesgo obligó a usar las restricciones; en universos pequeños el mandato se relaja con aviso CRITICAL explícito en el log.

Para juzgar robustez usa el walk-forward (ver sección Validación): sus medianas OOS dicen más que cualquier Sharpe in-sample.

## Validación fuera de muestra

```python
from portfolio_engine.validation import walk_forward_evaluate

report = walk_forward_evaluate(prices, dates, config, train_rows=250, test_rows=60, embargo_days=5)
print(report.to_dict())
```

Por ventana: pesos fijados solo con datos de entrenamiento (alineación → estadísticas → HRP), aplicados congelados sobre la ventana posterior separada por embargo. El reporte expone retorno/volatilidad/Sharpe OOS por fold y agregados por mediana. Sin costos ni turnover todavía — úsalo como contraste direccional, no como P&L esperado.

## Gráficas del reporte

| # | Gráfica | Decisión que habilita |
|---|---|---|
| 1 | Evolución histórica normalizada | liderazgo y dispersión sin sesgo nominal |
| 2 | Perfil riesgo-retorno | eficiencia de riesgo vs tasa libre |
| 3 | Dashboard de métricas | calidad relativa pre-filtro |
| 4 | Matrices correlación/covarianza | redundancia estructural |
| 5 | Efecto del filtrado | impacto del embudo |
| 6 | Correlación filtrada | qué queda tras el embudo |
| 7 | Resumen de cartera óptima | lectura ejecutiva con Sharpe honesto (wᵀΣw) |

Ejemplos generados en `scripts/charts/`.

## Supuestos y limitaciones

Depende de datos de `yfinance`: los resultados cambian con fecha de consulta, universo y disponibilidad. No es pronóstico ni recomendación de inversión.

- **Existe** validación out-of-sample (walk-forward con embargo) desde feat-026.
- **Pendiente**: costos de transacción, turnover control, modelado intraperíodo de pesos — diferidos explícitamente (decision-log).
- El clustering legacy greedy sigue operativo para métodos no-HRP y reproducibilidad de composiciones previas.

## Reproducibilidad y verificación

```bash
make lint    # ruff
make types   # pyright
make test    # pytest (154 tests)
./init.sh    # los 4 gates completos
```

Determinismo: cerraduras versionadas (`uv.lock`), proveedor inyectable para tests offline, hypothesis derandomized en propiedades y semillas fijas en fixtures. Cada decisión metodológica tiene ADR; cada feature ejecutado, change OpenSpec archivado.

## Estructura del proyecto

```
config/universe.yaml          # Universo externalizado
docs/
├── adr/                      # Decisiones metodológicas versionadas (+ índice)
├── auditoria-tecnica.md      # Auditoría original (histórico)
└── orden-de-resolucion.md    # DAG de resolución (histórico)
portfolio_engine/
├── core/       # Config inmutable validada, métricas vectorizadas, logging
├── data/       # Provider protocol, ingesta batch yfinance, universo YAML
├── portfolio/  # Filtrado, selección legacy, HRP (hrp.py), asignación+constraints
├── validation/ # Walk-forward OOS con embargo
├── viz/        # Gráficas y summary metrics (canvas confinado aquí)
└── app/        # Orquestación con provider inyectable
scripts/         # Entrypoint legacy wrapper
tests/           # Unitarios + propiedades (hypothesis) + E2E offline
```
