# Design: chore-coverage-gate

## Context

Post `feat-039` la suite es 230 tests, cobertura medida con `pytest-cov 7.1.0` + `coverage 7.16.0`: `87%` línea, `85%` branch+rama (`1509 stmts, 196 miss, 428 branch, 68 br-part` en `portfolio_engine` 18 archivos). El repo no mide cobertura: `pyproject.toml:56` solo `-q`, `Makefile:25` bare, `ci.yml:34` bare, y `pytest` en runtime contamina wheel. `feat-040` es último gate antes de `feat-041` release; debe fijar umbral levemente por debajo o igual a baseline real para no ser brittle, y mover `pytest` a dev sin romper `uv sync --frozen`.

## Goals / Non-Goals

**Goals:**
- Gate 85% (branch) en `addopts` y `[tool.coverage.report] fail_under` con `branch = true`, `show_missing = true`.
- Higiene: `pytest` y `pytest-cov` solo en `dev` (PEP 735), `uv.lock` re-freeze reproducible, `uv run pytest` sigue encontrando `pytest` vía default-groups.
- `make test` reporta cobertura y falla bajo umbral; `make test-no-cov` escape hatch.
- CI espeja cobertura y publica `htmlcov` artifact.

**Non-Goals:**
- No subir a 100% ni usar diff-cover; no cambiar `pyright` a strict; no añadir `codecov` upload en v0.1.0.

## Decisions

### D1: Dónde poner pytest y pytest-cov (PEP 735)
Mover `pytest>=9.0.3` de `[project].dependencies` a `[dependency-groups].dev` junto a `pytest-cov>=6.0`, `ruff`, `pyright`, `hypothesis`. Flat `dev` es suficiente para repo pequeño (no split `test`+include-group). `uv add --group dev` actualiza lock; `uv sync --frozen` instala `dev` por default (`default-groups` implícito, no setear `tool.uv.default-groups = []`). Verificación: `uv lock --check` + `uv sync --frozen` + `uv run pytest --version` en CI 3.11-3.13.

Alternativa `optional-dependencies` descartada: publica a PyPI, no deseado.

### D2: Config cobertura (única fuente de verdad)
Añadir en `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["portfolio_engine"]
branch = true
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
show_missing = true
skip_empty = true
precision = 1
fail_under = 85
exclude_lines = [
  "pragma: no cover",
  "raise NotImplementedError",
  "if TYPE_CHECKING:",
  "if __name__ == .__main__.:",
  "@(abc\\.)?abstractmethod",
]

[tool.coverage.html]
directory = "htmlcov"

[tool.coverage.xml]
output = "coverage.xml"

[tool.pytest.ini_options]
addopts = "-q --cov=portfolio_engine --cov-report=term-missing --cov-report=html --cov-report=xml --cov-branch --cov-fail-under=85"
```

¿Por qué duplicar `fail_under` en ambos lugares? `pytest-cov` CLI `--cov-fail-under` overridea `tool.coverage.report.fail_under` si ambos existen, pero tener ambos evita silent pass si alguien borra `addopts`. Se documenta que `addopts` es gate primario, `tool.coverage.report` es fallback local `coverage report`.

Se elige `85` sobre branch (87 sin branch). Branch habilitado (`branch = true` + `--cov-branch`) captura else no testeados; caída esperada 20-30 pts al habilitar ya absorbida (baseline 85 con branch, no 60). `source` restringe a `portfolio_engine` (tests excluidos).

### D3: Makefile
Cambiar:

```make
test:
	uv run python -m pytest --cov=portfolio_engine --cov-report=term-missing --cov-report=html --cov-report=xml --cov-branch --cov-fail-under=85

test-no-cov:
	uv run python -m pytest -q --no-cov

clean: rm -rf htmlcov .coverage coverage.xml coverage.json ...
```

No se delega solo a `addopts` para visibilidad en `make` logs y para que `make test` siga gateando aunque `addopts` sea sobreescrito con `PYTEST_ADDOPTS=""`. Se mantiene `-q` dentro de `addopts` pero Makefile lo repite explícito.

### D4: CI
`.github/workflows/ci.yml` cambiar `Test suite` a mismo comando que `Makefile:test` (o simplemente `uv run python -m pytest` confiará en `addopts` + `uv sync --frozen` con dev). Preferimos explícito en CI para logs claros, y añadir upload:

```yaml
- name: Test suite with coverage gate
  run: uv run python -m pytest --cov=portfolio_engine --cov-report=term-missing --cov-report=xml --cov-report=html --cov-branch --cov-fail-under=85
- name: Publish coverage
  if: always()
  run: uv run coverage report --format=markdown >> $GITHUB_STEP_SUMMARY || true
- uses: actions/upload-artifact@v4
  with: { name: coverage-html-${{ matrix.python-version}}, path: htmlcov }
```

Mantener `uv sync --frozen` (no `--no-dev`), `strategy.fail-fast false`, matrix 3.11-3.13.

### D5: Threshold 85
Baseline medido 2026-09-05 con 230 tests: 85 branch, 87 line. Fijar `85` deja 0 slack branch (estricto) y 2 slack line. Alternativa 84 daría slack pero pospone gate. Se elige 85 exacto; si futura contribución añade código sin tests y coverage cae a 84, gate rojo forzará tests (intencionado). Ratchet upward semanal permitido.

## Risks / Trade-offs

- `branch = true` baja 2pts (87→85) pero honesto; si suite futura añade viz branches no cubiertas, caerá rápido.
- `uv sync --frozen` con dev groups: requiere `uv.lock` re-frozen localmente antes de CI, si no CI falla con “lock mismatch”.
- `.gitignore` ya tiene `.coverage/htmlcov`, no se commitea `coverage.xml` (subir como artifact).

## Migration

Backward compat: `uv sync` sin `--frozen` resuelve nuevo lock; `pip install -e .` sin dev no instala pytest (correcto, wheel no lleva pytest). `make test-no-cov` para loops rápidos locales.

## Open Questions

- ¿Subir a 86 tras stabilización? Diferir a v0.2.0.
