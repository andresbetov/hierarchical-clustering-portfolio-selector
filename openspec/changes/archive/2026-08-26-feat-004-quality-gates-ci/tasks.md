# Tasks: feat-004-quality-gates-ci

## 1. Toolchain en el manifiesto

- [x] 1.1 pyproject: añadir `[dependency-groups] dev` (ruff>=0.12, pyright pinned) + `[tool.ruff]` (select E/F/W/I, line-length 120, excludes) + `[tool.pyright]` (basic; include portfolio_engine/scripts) — verificar: archivos válidos
- [x] 1.2 `uv lock && uv sync` — verificar: dev group instalado, lock actualizado determinista

## 2. Entradas de ejecución

- [x] 2.1 Makefile targets `lint`/`types` + help — verificar: `make lint` y `make types` exit 0 (tras hallazgos resueltos)
- [x] 2.2 init.sh corre lint+types cuando hay uv (fail-fast preservado) — verificar: ./init.sh muestra ruff+pyright pasando

## 3. Hallazgos reales de linters

- [x] 3.1 Correr `uv run ruff check .`; registrar hallazgos; fix solo triviales (noqa con racional donde aplique, ej allocation.py `_ = correlation_matrix`) — verificar: ruff verde
- [x] 3.2 Correr `uv run pyright`; misma política — verificar: pyright verde o hallazgos escalados documentados

## 4. CI servidor + conveniencia local

- [x] 4.1 `.github/workflows/ci.yml`: push develop/main + PR develop; matriz ["3.11","3.13"]; steps checkout→setup-uv→sync frozen→ruff→pyright→pytest→compileall — verificar: yaml parsea (actionlint si disponible o revisión manual)
- [x] 4.2 `.pre-commit-config.yaml` (ruff mirror pinned + hygiene) + docs CONTRIBUTING/README badge — verificar: config yaml válido

## 5. Cierre

- [ ] 5.1 Verificación fresca completa (`make lint`, `make types`, `make test`, `./init.sh`); tracker feat-004 done+evidence; progress/handoff; commits convencionales; archive change
