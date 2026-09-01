# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- DAG v0.1.0 registrado en `feature_list.json` (feat-028..feat-041) con dependencias explícitas hacia CP1/CP2/CP3 (chore(project): register v0.1.0 DAG).
- feat-032: dependencia `scikit-learn>=1.8` (consumida por el estimador de covarianza de feat-033/ADR 005).
- feat-033: `covariance_estimator ∈ {sample, ledoit_wolf, oas}` (ADR 005) — seam `estimate_covariance` consumida por el pipeline y el walk-forward; default `sample` (sin cambio silencioso), shrinkage con paridad sklearn a 1e-12; flip de default a `ledoit_wolf` diferido a v0.2.0 con evidencia walk-forward.
- feat-034: `linkage_method ∈ {single, ward, average}` (ADR 006) — propagado a `scipy.cluster.hierarchy.linkage` desde config; default `single` (De Prado, snapshot-compatible); flip a `ward` candidato para v0.2.0.
- feat-035: walk-forward con paridad productiva — filtros Sharpe/vol de producción aplicados por fold de train (universo ex-ante), benchmarks ex-ante `equal` (1/N) e `ivp` (inverse-volatility) sobre el mismo universo y los mismos retornos OOS, 6 medianas nuevas en `to_dict()`; guard NaN-blind corregido (folds con riesgo muestral degenerado/NaN quedan inválidos, nunca válidos-con-NaN); disciplina temporal documentada (embargo 5d dentro de la práctica 5-20d, purga implícita 1d).

### Changed

- feat-031: specs merged sincronizadas con el código (`hrp` en el set de métodos de `configuration-contract`, doble negación corregida en `numeric-correctness`, rango de Python 3.11-3.13 en `project-packaging`); CHANGELOG inicial; `progress.md` consolidado.

### Removed

- feat-032: soporte de Python 3.10 (EOL 2026-10-31; SPEC 0) — **BREAKING**: `requires-python` sube a `>=3.11` y la matriz CI pasa a 3.11/3.12/3.13.

### Fixed

- feat-028: crash en la ruta legacy del reporte (métodos ≠ `hrp` con pruning M<N recibían la covarianza N×N sin rebanar; ahora el pipeline entrega la covarianza rebanada al portfolio seleccionado) — PR #32.
- feat-029: el walk-forward omitía el retorno del primer día de la ventana de test (`np.roll` + `[1:]`); ahora cada fold produce exactamente `test_rows` retornos con el primero calculado contra el precio previo a la ventana (leak-free) — PR #33.
- feat-030: los paneles sintéticos de tests dependían del salting de `PYTHONHASHSEED` (`hash(ticker)`); ahora usan `zlib.crc32` — el mismo commit produce fixtures byte-idénticos en cualquier proceso — PR #34.

## [0.1.0]

Primera versión funcional y confiable — pendiente de liberación al cerrar el DAG v0.1.0 (feat-028..feat-041). Incluirá los fixes de Fase A (reporte legacy, walk-forward, determinismo de fixtures), la parametrización metodológica de Fase B (covariance estimator ADR 005, linkage ADR 006, walk-forward con paridad productiva y benchmarks, convención Sharpe, guard de solapamiento) y el cierre de producto de Fase D (cache parquet, CLI argparse + dendrograma, cobertura con umbral, release).
