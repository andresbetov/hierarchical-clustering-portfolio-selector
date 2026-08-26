> **ESTADO (2026-08-26): EJECUTADO COMPLETO** — los 28 hallazgos aquí inventariados fueron resueltos y mergeados vía el DAG de feat-001..027. Este documento es snapshot histórico de la auditoría inicial: los números de línea citados corresponden a `develop@d55c2d5` y NO reflejan el árbol actual. Estado vivo del proyecto: `README.md` y `progress.md`.

# Knowledge Base — Auditoría Arquitectónica y Técnica

**Proyecto:** `hierarchical-clustering-portfolio-selector`  
**Fecha de auditoría:** 2026-08-26  
**Rama auditada:** `develop` (`d55c2d5`)  
**Auditor:** Muse Spark (análisis estático + revisión extendida de buenas prácticas 2025-2026)  
**Propósito del documento:** Source of truth para falencias, restricciones, discrepancias y roadmap. Consumido por agentes (`AGENTS.md`), `openspec/` y planificación en `feature_list.json`. Actualizar tras cada feature `done`.

> **Convención de referencias:** `ruta:línea` (ej. `portfolio_engine/core/metrics.py:28`). Toda afirmación técnica es trazable a código o a fuente externa citada en §8.

---

## Índice

1. [Propósito declarado vs implementado](#1-propósito-declarado-vs-implementado)
2. [Mapa de arquitectura actual](#2-mapa-de-arquitectura-actual)
3. [Matriz de hallazgos por criticidad](#3-matriz-de-hallazgos-por-criticidad)
   - [3.1 CRÍTICO](#31-crítico--rompe-pipeline-o-invalida-resultados)
   - [3.2 ALTO](#32-alto--invalida-reproducibilidad-o-deuda-metodológica)
   - [3.3 MEDIO](#33-medio--calidad-mantenibilidad-arquitectura)
   - [3.4 BAJO](#34-bajo--higiene-docs-ux)
4. [Discrepancias documentales](#4-discrepancias-documentales)
5. [Restricciones estructurales](#5-restricciones-estructurales)
6. [Brechas vs Buenas Prácticas](#6-brechas-vs-buenas-prácticas)
7. [Deuda técnica cuantificada](#7-deuda-técnica-cuantificada)
8. [Roadmap priorizado](#8-roadmap-priorizado)
9. [Anexos](#9-anexos)

---

## 1. Propósito declarado vs implementado

| Dimensión | Declarado (`README.md:2-9`) | Implementado (`portfolio_engine/app/pipeline.py:38`) |
|---|---|---|
| **Objetivo** | Pasar de universo amplio a cartera interpretable sin discrecionalidad, con 7 gráficas diagnósticas | Pipeline lineal `download → filter → correlation/cov → select → allocate → plot`. Sin backtest, turnover, costos, ni validación out-of-sample. |
| **Clustering** | "Agrupación por similitud para evitar duplicar exposiciones" (`README.md:21`) | Greedy por umbral `portfolio_engine/portfolio/selection.py:50` que elige 1 activo por cluster via scoring compuesto. No es HRP (ver C1). |
| **Asignación** | `risk_parity` con límites `0.05-0.30` (`README.md:40`) | `calculate_risk_parity_weights` iterativo plano + `clip` no iterativo (`allocation.py:114`). `target_volatility 0.15` existe pero no se aplica (`config.py:26`, `README.md:43`). |
| **Reproducibilidad** | `uv sync` + `uv run pytest` (`README.md:103`) | `uv` no instalado en imagen base, `uv.lock` no versionado (`.gitignore:16`), `make test` roto (`Makefile:17`). |
| **Interpretación** | Secuencial por embudo (`README.md:46`) | Correcto, pero métrica Sharpe de portafolio en `viz/reporting.py:309` asume correlación 0 → lectura engañosa. |

**Veredicto:** el valor "estructura robusta" se cumple parcialmente; el valor "reproducible y auditable" no. El título *hierarchical clustering* es nominal, no metodológico.

---

## 2. Mapa de arquitectura actual

```
portfolio_engine/
├── core/
│   ├── config.py:1           PortfolioConfig (mutable, sin validación)
│   ├── metrics.py:1          log-returns, anualización, corr/cov, distancia 1-|corr|
│   └── logging_utils.py:1    configure_logging (early-return si handlers existen)
├── data/
│   └── data_fetch.py:15      download_and_calculate_metrics (loop yfinance Ticker, 5*365 días)
├── portfolio/
│   ├── selection.py:50       perform_hierarchical_clustering (greedy) + select_optimal_diversified_portfolio (scoring)
│   └── allocation.py:34      5 métodos (equal, inv_vol, risk_parity, max_sharpe, min_var) + clip
├── viz/
│   └── reporting.py:1        7 plotters + print_* (plt.show block=False)
└── app/
    └── pipeline.py:38        main() + generate_complete_analysis_report() (orquesta + grafica + guarda)

scripts/assets-investment.py:1  entrypoint con sys.path.insert
tests/
├── test_metrics.py:1          11 tests sintéticos
└── test_integration.py:1      6 tests pipeline sintético
```

**Flujo de datos:** `ticker list → yfinance history → compute_logarithmic_returns → annualized metrics → apply_asset_filters → construct_returns_matrix → correlation/cov → distance → greedy clustering → composite score → risk_parity → clip → 7 PNG`.

**Dependencias:** `pyproject.toml:5` `numpy, numba, matplotlib, seaborn, yfinance, scipy, pytest`. `scipy` no usado.

---

## 3. Matriz de hallazgos por criticidad

> **Criterio de severidad:** CRÍTICO = pipeline falla o resultado financieramente inválido. ALTO = no reproducible o sesgo metodológico. MEDIO = deuda mantenibilidad. BAJO = higiene.

### 3.1 CRÍTICO — rompe pipeline o invalida resultados

#### C1 — Implementación HRP ficticia

- **Ubicación:** `portfolio_engine/portfolio/selection.py:50-80` `portfolio_engine/core/metrics.py:141` `pyproject.toml:11`
- **Descripción:** `perform_hierarchical_clustering` fusiona el par más cercano `< threshold` iterativamente. No construye dendrograma, no hace `quasi-diagonalization`, no hace `recursive bisection`. `compute_correlation_distance_matrix:141` = `1 - abs(corr)` ; la literatura HRP usa `d = sqrt(0.5*(1-corr))` sin `abs` y `linkage` (`single/ward`). `scipy` declarado pero `grep scipy --include=*.py` vacío.
- **Evidencia:** Código `for i in range(n): for j in range(i+1,n): if assignments[i]!=assignments[j] and dist[i,j] < min_dist` es `O(n³)` y dependiente del orden de fusión; no produce árbol. Con `n=400` (S&P500) el costo cuadrático documentado en [Fast HRP 2026](https://doi.org/10.1007/s10479-026-07149-2) se dispara.
- **Impacto:** Portfolio no jerárquico; con universo correlacionado (ej. 12 large-cap US) puede seleccionar 1 solo cluster. No comparable a benchmarks académicos.
- **Fix canónico:** `from scipy.cluster.hierarchy import linkage; from scipy.spatial.distance import squareform` → `link = linkage(squareform(distance), 'single')` → `sortIx = getQuasiDiag(link)` → `recBipart(cov, sortIx)` (De Prado 2016, Palomar 12.3). Añadir `HERC` como alternativa (Raffinot 2017).

#### C2 — yfinance frágil + ineficiente

- **Ubicación:** `portfolio_engine/data/data_fetch.py:15-67`
- **Descripción:** Loop secuencial `for ticker in tickers: yf.Ticker(ticker).history(start,end, auto_adjust=False)` descarga 12× en serie sin batch, sin retry, sin rate-limit. `price_history["Adj Close"].values:47` asume columna existe. Desde `yfinance 0.2.51` el default es `auto_adjust=True` (sin `Adj Close`, OHLC ya ajustado) — el código fija `False` y sobrevive hoy, pero cualquier omisión del flag levanta `KeyError` (issues [#2255](https://github.com/ranaroussi/yfinance/issues/2255), [#2197](https://github.com/ranaroussi/yfinance/issues/2197)). `except Exception: continue:64` silencia fallos. No valida `price_history.empty`. Ventana `end=today-1, start=end-5*365:28` ignora calendario bursátil y bisiestos.
- **Impacto:** Si 1 ticker falla por `YFRateLimitError`, se ignora y `pipeline.py:61` retorna `filtered_metrics={}` → reporte vacío sin error. No hay cache → cada corrida 12 requests.
- **Fix:** `yf.download(tickers, auto_adjust=False, progress=False, group_by="ticker")` batch, fallback `if "Adj Close" not in df.columns: use Close`, `if df.empty: continue`, `tenacity.retry`, cache `parquet` en `data/cache/` con `duckdb`, parametrizar `lookback_years` via `PortfolioConfig`.

#### C3 — Riesgo numérico: división por cero e inconsistencia ddof

- **Ubicación:** `portfolio_engine/core/metrics.py:28-35` `portfolio_engine/portfolio/allocation.py:64`
- **Descripción:** `calculate_sharpe_ratio:34` `return (ret-rf)/vol` sin guard → `vol=0` ⇒ `inf`. `calculate_annualized_volatility:28` usa `np.std(ddof=0)` poblacional; `calculate_covariance_matrix:114` usa `/(N-1)` muestral. `calculate_correlation_matrix:71` pone `1.0` en diagonal aunque `std=0` (activo precio plano) → matriz no PSD. `calculate_risk_parity_weights:65` `scaling = target/risk_contrib` divide por 0 si `marginal_risk=0`.
- **Impacto:** Sharpe `inf` pasa filtro `apply_asset_filters:37` (`inf > 0.5` true) y contamina selección. Matriz corrupta rompe `max_sharpe`/`min_var` (`LinAlgError`).
- **Fix:** `if vol < 1e-12: return 0.0` o `np.nan`; unificar `ddof=1` en vol; en corr, si `std==0: corr[i,j]=np.nan` excepto diagonal `1.0` sólo si varianza >0; en risk_parity `risk_contrib = np.maximum(risk_contrib, 1e-12)`.

#### C4 — Constraints de peso violados tras renormalizar

- **Ubicación:** `portfolio_engine/portfolio/allocation.py:114-121` `portfolio_engine/portfolio/allocation.py:180`
- **Descripción:** `apply_weight_constraints` hace `clip → /sum` una sola pasada. Ejemplo: 5 activos, pesos `risk_parity=[0.6,0.1,0.1,0.1,0.1]`, `max=0.30,min=0.05` → clip `[0.30,0.10,0.10,0.10,0.10]` suma 0.70 → `/0.70` → `[0.428,0.142,0.142,0.142,0.142]` → `0.428 > max`.
- **Impacto:** `README.md:40-41` promete `0.05-0.30` pero entrega fuera de rango; breach de mandato.
- **Fix:** Loop iterativo `while any(w>max+eps or w<min-eps): w=np.clip(w,min,max); w/=w.sum()` o QP `scipy.optimize.minimize` con `bounds` y `constraints sum=1`.

---

### 3.2 ALTO — invalida reproducibilidad o deuda metodológica

#### A1 — `target_portfolio_volatility` muerto

- **Ubicación:** `portfolio_engine/core/config.py:26` `README.md:43` `portfolio_engine/portfolio/allocation.py:124`
- **Descripción:** Param `0.15` documentado como "no se aplica como restricción activa". Ningún método escala a vol target.
- **Fix:** Implementar `vol = sqrt(w^T Cov w); w *= target_vol/vol` tras `apply_weight_constraints`, o eliminar param + ADR explicando por qué.

#### A2 — `risk_free_rate` inconsistente

- **Ubicación:** `portfolio_engine/data/data_fetch.py:15` default `0.03` vs `portfolio_engine/core/config.py:20` `0.045`. `pipeline.py:50` pasa `config.risk_free_rate` pero uso directo de `download_and_calculate_metrics` usa `0.03`.
- **Impacto:** Sharpe difiere 150 bps según entrypoint.
- **Fix:** Eliminar default del fetcher, exigir `risk_free_rate: float` posicional desde `PortfolioConfig` (Single Source of Truth).

#### A3 — Matrices sin alineación temporal

- **Ubicación:** `portfolio_engine/core/metrics.py:121-138` `portfolio_engine/app/pipeline.py:75-77`
- **Descripción:** `construct_returns_matrix` hace `np.array(list).T` asumiendo longitudes idénticas y calendario idéntico. `price_dates:48-50` se captura pero nunca se usa para join. Si un ticker suspende o tiene IPO reciente, longitudes difieren → `ValueError` o desalineación silenciosa (retornos de días distintos comparados).
- **Fix:** `pd.DataFrame({k: pd.Series(v, index=dates[k]) for k,v in prices.items()}).sort_index().dropna()` → `intersection` (o `union` + forward-fill según política) antes de `compute_log_returns`.

#### A4 — Ventana 5 años hardcodeada

- **Ubicación:** `portfolio_engine/data/data_fetch.py:28-29`
- **Descripción:** `timedelta(days=5*365)` ignora bisiestos (1825 vs 1826-1827 días) y fines de semana; `end=today-1` puede ser sábado. No parametrizable, no testeable con fechas fijas.
- **Fix:** `lookback_years: int = 5` en `PortfolioConfig`, usar `relativedelta` o `pd.offsets.BDay`, exponer en `scripts/assets-investment.py:21` y `config.yaml`.

#### A5 — Sharpe de portafolio erróneo en reporte

- **Ubicación:** `portfolio_engine/viz/reporting.py:308-310`
- **Descripción:** `portfolio_sharpe = ret / sqrt(sum((w*v)^2))` asume correlación 0. Debe ser `sqrt(w^T Cov w)`.
- **Fix:** `port_var = calculate_portfolio_variance(weights, cov)` (ya existe `allocation.py:34`) → `sharpe = (w·ret - rf)/sqrt(port_var)`.

#### A6 — Metadata de proyecto rota

- **Ubicación:** `pyproject.toml:1-13`
- **Descripción:** `name=xai-financial-predictor-engine` ≠ repo; `requires-python>=3.13` excluye 3.10-3.12 (CI estándar); `scipy` fantasma; `seaborn` usado pero sin pin estricto; sin `uv.lock`; sin `[tool.pytest]`, `[tool.ruff]`, `[tool.pyright]`.
- **Fix:** Renombrar a `hierarchical-clustering-portfolio-selector`, `requires-python>=3.10`, pin `numpy==2.*`, `scipy>=1.11`, commitear `uv.lock` (quitar de `.gitignore:16`), añadir tool configs (ver §6).

#### A7 — Harness de verificación roto

- **Ubicación:** `Makefile:17` `CONTRIBUTING.md:81` `init.sh:14`
- **Descripción:** `make test` → `uv run python tests/smoke_test.py` no existe (existen `test_metrics.py`, `test_integration.py`). `init.sh` tolera `exit 5` (sin tests = verde).
- **Fix:** `test: uv run pytest -q` + `pytest.ini` con `testpaths = tests`.

---

### 3.3 MEDIO — calidad, mantenibilidad, arquitectura

| ID | Hallazgo | Ubicación | Recomendación |
|---|---|---|---|
| **M1** | Config mutable sin validación. `sharpe_weight+div_weight+pen_weight` debe =1.0 pero no se valida; sin tipos. | `config.py:1-29` | `@dataclass(frozen=True)` o `pydantic.BaseModel` con `model_validator`; exponer `config/default.yaml` + override `env`. |
| **M2** | Distancia `1-abs(corr)` colapsa correlación negativa. Literatura HRP sin `abs`; negativa = diversificadora debe separarse. `README.md:22` habla de baja correlación pero código premia `abs`. | `metrics.py:141-152` `selection.py:103` | ADR: elegir métrica; exponer `distance_metric: "signed" \| "abs" \| "angular"` . |
| **M3** | Pipeline mezcla orquestación + cálculo + reporte. `generate_complete_analysis_report:103` hace todo → no testeable sin red. | `pipeline.py:38-214` | Separar capas `data` → `domain` → `app` → `viz` (ver `Quanto` arch). Inyección de `DataProvider` mockeable. |
| **M4** | Logging frágil `if root.handlers: return:12` ignora `level` si pytest ya configuró. | `logging_utils.py:7-19` | `logging.getLogger("portfolio_engine")` con `StreamHandler`; `dictConfig` + `LOG_LEVEL` env. |
| **M5** | Visualización no headless-safe `plt.show(block=False)+pause:20-23`. Falla en CI sin display; no fija `Agg`. | `reporting.py:10-25` `pipeline.py:203` | `matplotlib.use("Agg")` si `MPLBACKEND` ausente; eliminar `show` cuando `save_plots=True`. |
| **M6** | Numba sobreuso en funciones triviales `mean*252` `metrics.py:10`. Añade peso y `.nbc` cache. | `metrics.py:1-21` | Benchmark; limitar `jit` a `correlation/covariance` o eliminar. `numba` opcional. |
| **M7** | Entrypoint con `sys.path.insert` | `scripts/assets-investment.py:5` | `pyproject.toml [project.scripts]` `portfolio=portfolio_engine.cli:main`. |
| **M8** | Tests débiles (11 tests, solo sintéticos, sin bordes). No casos `1 activo`, `0 filtrados`, `matriz singular`, `bounds` | `tests/test_metrics.py:17` `test_integration.py:47` | Añadir `test_selection.py`, `test_allocation.py`, `test_constraints.py`, `hypothesis`, `pytest-mock` para yfinance. |
| **M9** | Sin control calidad: no `ruff`, `pyright`, `pre-commit`, `CI` | raíz | Añadir `[tool.ruff]`, `[tool.pyright]`, `.pre-commit-config.yaml`, `ci.yml` (uv sync → ruff → pyright → pytest). |
| **M10** | `calculate_inverse_volatility_weights:48` divide por 0 si `vol=0` sin guard. | `allocation.py:48-50` | `vol = np.maximum(vol, 1e-12)` |

---

### 3.4 BAJO — higiene, docs, UX

| ID | Hallazgo | Detalle |
|---|---|---|
| **B1** | `.gitignore:16` ignora `uv.lock` → no reproducible. `charts/*.png` ignorado pero `scripts/charts/*.png` committeado. | Versionar `uv.lock`; ignorar `charts/` completo o documentar. |
| **B2** | Universo hardcodeado 12 tickers US large-cap `scripts/assets-investment.py:21` sin diversificación sectorial ni `universe.yaml`. | Extraer a `config/universe.yaml`. |
| **B3** | `openspec/` vacío, `config.yaml` fuerza `es` pero código/comentarios mixto `en/es`. Sin `CHANGELOG`, `ADR`. | Crear `docs/adr/001-yfinance-vs-alternativa.md`. |
| **B4** | Anualización `252` hardcodeada `metrics.py:24,30`. No param para crypto `365`. | `trading_days_per_year` en `PortfolioConfig`. |
| **B5** | `np.linalg.inv` inestable `allocation.py:89,102`. HRP evita inversión pero `max_sharpe`/`min_var` la reintroducen sin shrinkage. | Usar `np.linalg.solve`/`pinv` + `LedoitWolf`. |
| **B6** | Look-ahead in-sample: métricas, clustering y pesos sobre misma ventana sin `TimeSeriesSplit` | Walk-forward + purging (De Prado). |
| **B7** | `portfolio_engine/core/__init__.py:1` docstring vacío vs estructura `README.md:110` | Sincronizar. |

---

## 4. Discrepancias documentales

| # | Documento | Declarado | Realidad | Severidad |
|---|---|---|---|---|
| D1 | `README.md:43` | `target_portfolio_volatility` existe | No aplicado en optimización | ALTA |
| D2 | `pyproject.toml:2` + `Makefile:4` | `name=xai-financial-predictor-engine` | Repo `hierarchical-clustering-portfolio-selector` | MEDIA |
| D3 | `CONTRIBUTING.md:81` | "`make test` apunta a archivo inexistente, usa `uv run pytest`" | `Makefile:17` sigue roto | MEDIA |
| D4 | `README.md:103` vs `init.sh:14` | `uv run pytest` como verificación | `init.sh` acepta `exit 5` (sin tests = verde) | BAJA |
| D5 | `README.md:18` vs `.gitignore:13` | "El script escribe en `charts/`; ejemplos en `scripts/charts/`" | `charts/` ignorado, `scripts/charts` versionado → incoherencia | BAJA |
| D6 | `CONTRIBUTING.md:70` | "aún no tiene hook commitlint" | Trabajo declarado sin issue/tracking | BAJA |
| D7 | `progress.md:30` | "scipy no usado" reconocido como hallazgo | Sigue en `pyproject.toml:11` | BAJA |

---

## 5. Restricciones estructurales

| Categoría | Restricción | Consecuencia |
|---|---|---|
| **Mercado** | Solo `yfinance` equities US, sin survivorship bias handling, sin delistings | Backtest sesgado; no portable a crypto/forex/ETF multi-asset |
| **Ejecución** | Single-thread, sin persistencia, re-descarga 5 años cada corrida | Latencia + costo rate-limit; no trazable |
| **Posicionamiento** | `long-only`, `fully-invested`, `allocation.py:151` `1 activo → 1.0`, sin `short/leverage/turnover` | No expresa tesis direccional ni controla costos |
| **Modelo riesgo** | Vol histórica sample, sin `EWMA/GARCH/shrinkage/factor model` | Cov ruidosa, HRP sensible (Trucíos 2026) |
| **Validación** | Sin backtest, sin `quantstats/pyfolio` tear sheet, sin `VaR/CVaR` | Sharpe reporte diagnóstico, no out-of-sample (`README.md:98` lo admite) |
| **Escalabilidad** | Greedy `O(n³)` | No escala a `n>100` (S&P500) |

---

## 6. Brechas vs Buenas Prácticas

### 6.1 Metodología quant — HRP/HERC

**Literatura 2025-26 revisada:**
- Salas-Molina et al. 2025 — métricas basadas en correlación superan no-correlación; HRP supera MVO en bull/sideways, pierde en bear.
- Salas-Molina & Nin 2026 (Fast HRP) — clustering `O(n²)` cuello de botella; ranking por correlación reduce tiempo manteniendo performance hasta `n≈400`; `recursive bisection` domina allocation, no el dendrograma.
- Trucíos 2026 — HRC no supera risk-based tradicional out-of-sample y es sensible a estimador de covarianza.
- Palomar 12.3 — HRP = `linkage → quasiDiag → recBipart` con `inverse-variance` por cluster; `1/N` jerárquico difícil de batir; HERC con `drawdown-at-risk` mejora.

**Brecha del repo:**
| Esperado | Actual | Gap |
|---|---|---|
| 3 pasos HRP + `LedoitWolf`/`OAS` shrinkage | Greedy + sample cov | Metodológico |
| `linkage ∈ {single,ward,complete}` + `distance` param | `1-abs(corr)` fijo | Flexibilidad |
| Walk-forward purged CV + benchmark `1/N`/`IVP` | In-sample único | Validación |
| `VaR/CVaR` y drawdown | Solo Sharpe diagnóstico | Risk |

**Práctica correcta:**
```python
from sklearn.covariance import LedoitWolf
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform
cov = LedoitWolf().fit(returns).covariance_
dist = np.sqrt(0.5*(1 - corr))  # sin abs
link = linkage(squareform(dist), method='single')
sort_ix = get_quasi_diag(link)  # De Prado
weights = get_rec_bipart(cov, sort_ix)  # inverse-variance recursivo
```

### 6.2 Arquitectura Python quant 2025

**Referentes:** [osquant Python Tooling 2025](https://osquant.com/papers/python-tooling-in-2025/), [QuantResearch_Opcode](https://github.com/adityacosmos24/QuantResearch_Opcode), [Quanto](https://github.com/skyliquid22/Quanto), [Dyson 7 Pillars](https://dredyson.com/how-to-organize-your-algorithmic-trading-projects-like-a-pro-quant-a-complete-step-by-step-guide-to-building-a-bulletproof-hft-codebase-python-backtesting-pipeline-and-financial-modeling-workflow-that-actually-scales/).

| Pilar | Esperado 2025 | Estado repo | Fix |
|---|---|---|---|
| **Package mgmt** | `uv` + `uv.lock` versionado + `pyproject.toml` único | `pyproject` mínimo, `uv` no instalado, `uv.lock` ignorado | `uv sync && git add uv.lock`, `[project.scripts]` |
| **Lint/Format** | `ruff` (lint+format) en `pyproject.toml` | Ausente | `[tool.ruff] line-length=100` |
| **Types** | `pyright` estricto + `pandas-stubs` | Ausente | `[tool.pyright] typeCheckingMode=strict` |
| **Tests** | `pytest` + `testpaths`, `hypothesis`, `ci.yml` | `test_*` sin config, `make test` roto | `pytest.ini` + `pre-commit` |
| **Estructura** | `src/`, `data/raw|processed`, `config/`, `notebooks/` efímero | `portfolio_engine/` + `scripts/` con hack path | `src/portfolio_engine`, `config/universe.yaml` |
| **Separación** | `Research ≠ Execution` con manifests determinísticos (`Quanto`) | `pipeline.py` monolito | Capas `data/domain/app/viz` + `DataProvider` protocol |
| **Repro** | `MLflow`/`weights` + semillas + `data lineage` | Sin tracking | `mlflow` o `json` manifest por corrida |

**Template `pyproject.toml` recomendado (extracto):**
```toml
[project]
name = "hierarchical-clustering-portfolio-selector"
requires-python = ">=3.10"
dependencies = ["numpy>=1.26","scipy>=1.11","pandas>=2.2","yfinance>=0.2.40","matplotlib>=3.8","seaborn>=0.13","numba>=0.60"]

[dependency-groups]
dev = ["pytest>=8.4","ruff>=0.8","pyright>=1.1","pandas-stubs","hypothesis","pytest-mock"]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --strict-markers"

[tool.pyright]
typeCheckingMode = "strict"
```

### 6.3 Data engineering & reproducibilidad

| Principio (Dyson/Quanto) | Estado |
|---|---|
| Raw inmutable, procesado versionado | No — `data_fetch` escribe dict volátil |
| Calendar `union/intersection` + `dropna` | No — `construct_returns_matrix` asume longitudes iguales |
| Validación esquema (`pandera`/`great_expectations`) | No |
| Cache `parquet` + `duckdb` + lineage | No |

---

## 7. Deuda técnica cuantificada

| Métrica | Valor |
|---|---|
| **LOC** `portfolio_engine/` | ~900 líneas (core 153, data 77, selection 162, allocation 190, pipeline 215, viz 384) |
| **Tests** | 17 asserts en 2 archivos, cobertura estimada <40% (sin `selection`/`allocation` edge cases) |
| **Dependencias fantasma** | 1 (`scipy`) |
| **Params muertos** | 1 (`target_volatility`) |
| **Defaults inconsistentes** | 1 (`risk_free_rate`) |
| **Complejidad ciclomática hotspot** | `perform_hierarchical_clustering` `while + for i + for j` (3 niveles) |
| **Deuda documental** | 7 discrepancias (§4) |
| **Riesgo numérico** | 4 divisiones sin guard |

**Costo de no corregir:** cada feature nuevo amplifica riesgo de Sharpe `inf`, pesos fuera de bounds y comparabilidad nula con literatura.

---

## 8. Roadmap priorizado

> **Regla `AGENTS.md`:** 1 feature a la vez en `develop`, evidencia `./init.sh` fresca antes de `done`, PR `feat/* → develop`.

### Fase 0 — Higiene (1 sprint, sin riesgo funcional)

| Task | Criterio done |
|---|---|
| Fix `Makefile:17` → `uv run pytest -q` | `make test` verde |
| Renombrar `pyproject.toml:2`, `requires-python>=3.10`, commitear `uv.lock` | `uv sync --frozen` reproducible |
| Añadir `[tool.ruff]`, `[tool.pyright]`, `[tool.pytest]`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml` | CI `ruff+pyright+pytest+compileall` verde |
| `matplotlib.use("Agg")` + eliminar `plt.show(block=False)` en modo `save` | `pytest` headless verde |
| `scripts/assets-investment.py` → `pyproject [project.scripts]` | `uv run portfolio` funciona |

### Fase 1 — Corrección numérica (CRÍTICO)

| Task | Validación |
|---|---|
| Guards `vol=0`, `ddof=1`, `risk_contrib` floor, `inverse_vol` floor | `test_metrics::test_zero_vol` → `sharpe==0`, `corr` con `nan` |
| Alineación temporal `pd.DataFrame` + `dropna` | `test_returns_matrix::test_misaligned_dates` |
| Single source `risk_free_rate` | `test_config::test_rf_consistency` |
| `apply_weight_constraints` iterativo + test bounds | `test_constraints::test_clip_renorm` |
| `portfolio_sharpe` con `cov` | `test_reporting::test_sharpe_with_cov` |

### Fase 2 — HRP real (metodología)

| Task | Entregable |
|---|---|
| `scipy linkage + quasiDiag + recBipart` + `LedoitWolf` | `portfolio_engine/portfolio/hrp.py` + `test_hrp.py` |
| Param `distance_metric`, `linkage`, `cov_estimator` | `PortfolioConfig` validado + `config/default.yaml` |
| Benchmarks `equal`, `inverse_vol`, `1/N hierarchical` | `notebooks/benchmark_hrp.ipynb` con 3 escenarios (bull/side/side) |

### Fase 3 — Robustez data

| Task | Entregable |
|---|---|
| `yfinance.download` batch + retry + fallback `Close` | `data/yfinance_provider.py` |
| Cache `parquet` + `duckdb` + `universe.yaml` | `data/cache/` + `config/universe.yaml` |
| Walk-forward purged CV | `portfolio_engine/backtest/walk_forward.py` |

### Fase 4 — Producto

| Task | Entregable |
|---|---|
| Vol-target scaling + turnover/costs | `allocation.py` + `analytics/metrics.py` |
| `quantstats` tear sheet + `VaR/CVaR` | `viz/tearsheet.py` |
| CLI `portfolio run --config X --universe Y` + ADR | `docs/adr/001-risk-parity-vs-max-sharpe.md` |

**Dependencias:** Fase 1 bloquea 2-4 (resultados inválidos sin guards).

---

## 9. Anexos

### 9.1 Checklist de verificación por feature

```bash
./init.sh  # uv sync + pytest + compileall
make test  # tras Fase 0
uv run ruff check . && uv run ruff format --check .
uv run pyright
```

### 9.2 Glosario

- **HRP:** Hierarchical Risk Parity (De Prado 2016) — 3 pasos, evita invertir `Cov`.
- **HERC:** Hierarchical Equal Risk Contribution — variante con `risk contribution` igual por cluster.
- **LedoitWolf:** Shrinkage de covarianza para estimador estable.
- **Quasi-diagonalization:** Reordenar `Cov` para que activos similares queden contiguos.

### 9.3 Fuentes

1. Salas-Molina et al., *An Empirical Evaluation of Distance Metrics in HRP*, Springer 2025 — https://link.springer.com/article/10.1007/s10614-025-10848-w
2. Salas-Molina & Nin, *Fast HRP methods*, 2026 — https://doi.org/10.1007/s10479-026-07149-2
3. Trucíos, *Hierarchical risk clustering vs traditional risk-based portfolios*, Empirical Econ 2026 — https://bishtref.com/articles/10.1007/s00181-026-02900-x
4. Palomar, *Portfolio Optimization* 12.3 Hierarchical Clustering — https://bookdown.org/palomar/portfoliooptimizationbook/12.3-hierarchical-clustering-based-portfolios.html
5. yfinance `Adj Close` breaking change — [#2255](https://github.com/ranaroussi/yfinance/issues/2255) [#2197](https://github.com/ranaroussi/yfinance/issues/2197) [PR #2147](https://github.com/ranaroussi/yfinance/pull/2147)
6. osquant — *Python Tooling in 2025* (uv+ruff+pyright+pytest) — https://osquant.com/papers/python-tooling-in-2025/
7. QuantResearch_Opcode / Quanto — arquitectura `Research ≠ Execution` — https://github.com/adityacosmos24/QuantResearch_Opcode

### 9.4 Cómo mantener este documento

- **Cuándo:** tras cada `feat/*` mergeado a `develop` y en cada auditoría trimestral.
- **Quién:** owner del feature actualiza §3 con `Fixed`/`WontFix` + evidencia `./init.sh` output en `feature_list.json:evidence`.
- **Dónde:** `docs/knowledge-base.md` versionado; `progress.md` referencia delta; `session-handoff.md` apunta a próximo paso del roadmap.
- **No duplicar:** `feature_list.json` es source of truth de estado; este doc es diagnóstico, no tracker.

---

*Generado 2026-08-26 — re-ejecutar `grep -R "scipy\|Adj Close" --include="*.py"` y `python3 -m compileall` para validar vigencia antes de planificar siguiente feature.*
