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

chore!: drop python 3.12 support

BREAKING CHANGE: runtime floor lowered to python >= 3.10 (wheel matrix extended)
```

SemVer mapping: `feat` → MINOR · `fix` → PATCH · `!` / `BREAKING CHANGE` → MAJOR.

> Nota: a diferencia de `andresbetov-portfolio` (Node/pnpm + commitlint + husky),
> este repo es Python/uv y aún no tiene hook de commitlint. La convención se
> respeta manualmente hasta configurar validación automática.

## Decisiones metodológicas

Las decisiones arquitectónicas o metodológicas (fuente de datos, optimizador,
distancia de clustering, dependencias pesadas) se versionan como ADRs en
`docs/adr/` — una decisión = un archivo incremental, nunca editado retroactivamente.

## Setup y verificación

```bash
uv sync
uv run pytest          # suite completa (offline) — equivalente a make test
make lint              # ruff static checks (también corre en ./init.sh)
make types             # pyright type checks (también corre en ./init.sh)
make run               # pipeline completo (requiere red, yfinance)
```

Los cuatro gates (lint, types, test, compileall) corren automáticamente en CI
(push a develop/main y PRs) y localmente vía `./init.sh`. Opcional: hooks de
pre-commit con `uv tool install pre-commit && pre-commit install`.
