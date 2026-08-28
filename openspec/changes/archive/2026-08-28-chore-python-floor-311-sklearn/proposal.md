## Why

Feat-033 (estimador de covarianza, ADR 005) necesita scikit-learn, y las versiones vigentes del ecosistema científico exigen Python ≥3.11 (scikit-learn ≥1.8; SPEC 0 retira 3.10, que llega a EOL el 2026-10-31). El repo declara `requires-python>=3.10` y su matriz CI solo cubre 3.11/3.13 — incompatible con la dependencia entrante. La spec `project-packaging` ya declara el contrato objetivo (>=3.11, matriz 3.11-3.13) desde feat-031; esta feature lo implementa. Es feat-032 del DAG v0.1.0 y es un **BREAKING** (drop de Python 3.10).

## What Changes

- `pyproject.toml`: `requires-python = ">=3.11"`; nueva dependencia `scikit-learn>=1.8`; `[tool.ruff] target-version = "py311"`.
- `.github/workflows/ci.yml`: matriz `["3.11", "3.12", "3.13"]`.
- `uv.lock` re-resuelto (entran scikit-learn + joblib + threadpoolctl + narwhals).
- `CHANGELOG.md`: entrada breaking en Unreleased.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

(none — el contrato ya está declarado en `project-packaging` desde feat-031; esta feature lo implementa sin cambiar comportamiento especificado)

## Impact

- Manifiestos: `pyproject.toml`, `uv.lock`, `.github/workflows/ci.yml`, `CHANGELOG.md`.
- Sin cambios de código de runtime; el import de sklearn se usará en feat-033.
- Breaking: instalaciones con Python 3.10 dejan de ser soportadas.
