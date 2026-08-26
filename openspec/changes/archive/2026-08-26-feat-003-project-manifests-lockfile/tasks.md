# Tasks: feat-003-project-manifests-lockfile

## 1. Manifiestos

- [x] 1.1 `.gitignore`: eliminar línea `uv.lock` — verificar: `git check-ignore uv.lock` vacío tras crear el lock
- [x] 1.2 `pyproject.toml`: name → hierarchical-clustering-portfolio-selector; requires-python = ">=3.10" — verificar: campos en archivo
- [x] 1.3 Regenerar resolución: `uv lock` + `uv sync` — verificar: lock creado y sincronizado sin conflictos

## 2. Verificación del entorno nuevo

- [x] 2.1 `uv sync --frozen` reproduce el lock sin re-resolver — verificar: output "Audited/Checked" sin cambios
- [x] 2.2 Suite completa sobre la nueva resolución: `make test` → 16 passed — verificar: consola
- [x] 2.3 `./init.sh` exit 0 completo (sync frozen + pytest + compileall) — verificar: output

## 3. Cierre

- [ ] 3.1 Stage de uv.lock + manifiestos; commit convencional build(chore); tracker feat-003 done con evidence; progress/handoff actualizados — verificar: git status limpio, machine-check tracker schema intacto
