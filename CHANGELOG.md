# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- DAG v0.1.0 registrado en `feature_list.json` (feat-028..feat-041) con dependencias explícitas hacia CP1/CP2/CP3 (chore(project): register v0.1.0 DAG).

### Fixed

- feat-028: crash en la ruta legacy del reporte (métodos ≠ `hrp` con pruning M<N recibían la covarianza N×N sin rebanar; ahora el pipeline entrega la covarianza rebanada al portfolio seleccionado) — PR #32.
- feat-029: el walk-forward omitía el retorno del primer día de la ventana de test (`np.roll` + `[1:]`); ahora cada fold produce exactamente `test_rows` retornos con el primero calculado contra el precio previo a la ventana (leak-free) — PR #33.
- feat-030: los paneles sintéticos de tests dependían del salting de `PYTHONHASHSEED` (`hash(ticker)`); ahora usan `zlib.crc32` — el mismo commit produce fixtures byte-idénticos en cualquier proceso — PR #34.

### Changed

- feat-031: specs merged sincronizadas con el código (`hrp` en el set de métodos de `configuration-contract`, doble negación corregida en `numeric-correctness`, rango de Python 3.11-3.13 en `project-packaging`); CHANGELOG inicial; `progress.md` consolidado.

## [0.1.0]

Primera versión funcional y confiable — pendiente de liberación al cerrar el DAG v0.1.0 (feat-028..feat-041). Incluirá los fixes de Fase A (reporte legacy, walk-forward, determinismo de fixtures), la parametrización metodológica de Fase B (covariance estimator ADR 005, linkage ADR 006, walk-forward con paridad productiva y benchmarks, convención Sharpe, guard de solapamiento) y el cierre de producto de Fase D (cache parquet, CLI argparse + dendrograma, cobertura con umbral, release).
