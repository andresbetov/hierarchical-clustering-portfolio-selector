# Contributing

Git workflow and commit conventions for this repository. These rules apply to
every change, including agent-assisted sessions.

## Workflow: GitHub Flow con rama `develop`

Dos reglas gobiernan todo: **`main` es siempre deployable** y **`develop` es la rama de integración.**

1. Create a short-lived branch from the latest `develop`
2. Do the work — one logical change per branch
3. Verify locally: `./init.sh` (lint + types + pytest + compileall) must pass completely
4. Open a pull request targeting `develop`, then delete the branch after merge

`develop` acumula los cambios. Solo cuando lo decidas se mergea `develop` → `main`
(PR de `develop` a `main`); no hay merge automático a `main`.

Hotfixes follow the normal flow (`fix/...`) — there is no special ceremony.

## Branch naming

Lowercase, hyphen-separated, prefixed with the change type (mirrors Conventional
Commit types):

| Prefix      | Purpose                        | Example                    |
| ----------- | ------------------------------ | -------------------------- |
| `feat/`     | New feature                    | `feat/risk-parity-tuning`  |
| `fix/`      | Bug fix                        | `fix/correlation-distance` |
| `chore/`    | Tooling, maintenance           | `chore/update-deps`        |
| `docs/`     | Documentation only             | `docs/contributing-guide`  |
| `refactor/` | Restructure, no behavior change| `refactor/extract-metrics` |

If using OpenSpec, branch names should reference the matching change id under
`openspec/changes/` (e.g., `feat/vol-overlay` → `openspec/changes/feat-vol-overlay/`).

## Commits: Conventional Commits 1.0.0

```
<type>[optional scope]: description

[optional body]

[optional footer(s)]
```

Allowed types: `feat fix docs style refactor perf test build ci chore revert`

- Subject in imperative mood ("add", not "added"), no trailing period,
  full header ≤ 72 characters
- Body (optional) explains *why*, separated from the subject by a blank line
- Breaking changes: append `!` before the colon and/or a `BREAKING CHANGE:`
  footer

Examples:

```
feat(portfolio): add risk parity weight constraints

fix(metrics): correct annualized volatility scaling

chore!: drop python 3.11 support

BREAKING CHANGE: runtime floor raised to python >= 3.11 (wheel matrix 3.11-3.13)
```

SemVer mapping: `feat` → MINOR · `fix` → PATCH · `!` / `BREAKING CHANGE` → MAJOR.

## Decisiones metodológicas

Las decisiones arquitectónicas o metodológicas (fuente de datos, optimizador,
distancia de clustering, dependencias pesadas) se versionan como ADRs en
`docs/adr/` — una decisión = un archivo incremental, nunca editado retroactivamente.

## Setup y verificación

**Prerrequisitos:** `python >=3.11` (`pyproject.toml:requires-python`, CI matrix `3.11/3.12/3.13`), `uv` (`astral-sh/setup-uv@v6`), opcional `pyarrow>=14` para cache `data/cache/*.parquet`.

```bash
uv sync --frozen       # instalación reproducible desde uv.lock (dev incluye ruff/pyright/pytest/pytest-cov/hypothesis)
uv run pytest          # suite completa (offline) — hereda --cov-fail-under=85 desde pyproject.toml (equivale a make test)
make test              # gate explícito: -q --cov=portfolio_engine --cov-report=term-missing/html/xml --cov-branch --cov-fail-under=85 (85% branch / 87% line, 1509 stmts, 230 tests)
make test-no-cov       # escape hatch rápido sin cobertura (--no-cov)
make lint              # ruff static checks (también corre en ./init.sh)
make types             # pyright type checks (también corre en ./init.sh)
make run               # pipeline completo (requiere red, yfinance)
```

Los cinco gates (lint, types, test con cobertura 85% branch, `coverage report/html/xml`, compileall) corren automáticamente en CI
(push a develop/main y PRs) y localmente vía `./init.sh`. CI publica resumen `coverage report --format=markdown` en `$GITHUB_STEP_SUMMARY` y artifact `htmlcov` por versión de Python. Fuente única del umbral: `pyproject.toml: [tool.coverage.report] fail_under = 85` espejado en `addopts` + `Makefile` + `ci.yml` (`branch = true`). Opcional: hooks de
pre-commit con `uv tool install pre-commit && pre-commit install`.
