## Context

Ver proposal.md (Why) y `openspec/specs/project-packaging/spec.md` (contrato ya declarado en feat-031). Estado actual: `pyproject.toml` con `requires-python>=3.10`, deps sin sklearn; CI matrix `["3.11", "3.13"]`; `uv.lock` universal generado por uv; entorno local Python 3.14 (uv sync respeta requires-python al re-resolver). scikit-learn 1.8/1.9 soportan Python 3.11-3.14 (release notes oficiales) y traen joblib/threadpoolctl/narwhals como dependencias instalables.

## Goals / Non-Goals

**Goals:**
- Piso de Python alineado con el ecosistema (>=3.11) y matriz CI completa 3.11-3.13.
- sklearn disponible y versionado en el lock sin conflictos con numpy/scipy existentes.
- `uv sync --frozen` reproducible desde clon limpio.

**Non-Goals:**
- NO consumir sklearn desde código de runtime todavía (feat-033 lo hará con su ADR 005).
- NO tocar dependencias existentes ni versiones de numpy/scipy.
- NO cambiar comportamiento del motor.

## Decisions

**D1 — `scikit-learn>=1.8` (no pin superior).** El rango abierto deja a uv resolver la última compatible por Python; el lock congela la exacta. Alternativa descartada: `>=1.7,<1.8` para mantener 3.10 — rechazada porque 3.10 muere en 2026-10 y heredaría un pin obsoleto en semanas.

**D2 — skip_specs: true.** El contrato ya vive en `project-packaging` (feat-031); este change es implementación de plataforma, no cambio de comportamiento especificado.

**D3 — Re-lock con `uv lock` universal.** Mantiene el lock multi-versión (3.11-3.14) para que CI (3.11-3.13) y local (3.14) resuelvan del mismo archivo. Se verifica con `uv sync --frozen` en local y CI ×3.

**D4 — `target-version = "py311"` en ruff.** Consistencia del lint con el nuevo piso; no altera resultados del código actual (sin sintaxis 3.11 exclusiva en el árbol).

## Risks / Trade-offs

- [Resolución de sklearn arrastra versiones nuevas de joblib/threadpoolctl] → Mitigación: lock congela todo; gates y suite completa verifican que nada se rompe (sklearn aún no se importa en runtime).
- [CI 3.12 nueva en la matriz puede exponer fallas latentes] → Mitigación: la suite ya corre en 3.11/3.13; 3.12 es runtime soportado estándar del ecosistema; si fallara, se registra y decide antes de merge.
- [Usuarios con 3.10 quedan fuera] → esperado: breaking documentado en CHANGELOG y commit (`chore!:` + BREAKING CHANGE footer).
- [Re-lock cambia hashes de paquetes ya presentes (ruido de diff)] → Mitigación: revisar `git diff --stat uv.lock` y confirmar que solo se añaden sklearn/joblib/threadpoolctl/narwhals y sus versiones.

## Migration Plan

Usuarios: instalar Python ≥3.11 y re-sincronizar (`uv sync`). Rollback: revert del commit restaura 3.10 y quita sklearn (ningún código depende de él aún).
