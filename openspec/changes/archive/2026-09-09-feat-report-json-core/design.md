## Context

Ver `proposal.md` para la motivación. Estado del código: no existe ningún módulo de serialización JSON (grep `import json` en `portfolio_engine/` = 0 hits); el patrón existente a imitar es `WalkForwardReport.to_dict()` (`validation/walk_forward.py:179-196`): construir dict de primitivos primero, serializar después, con cast explícito `float(...)` en fronteras numpy. El key de caché (`data/cache.py:32-43`) ya demuestra el patrón sha256-canonical-sort en el repo pero EXCLUYE thresholds/método/linkage — no es reutilizable como fingerprint. Investigación externa aplicada: RFC 8785 (canonización: sort de claves determinista, sin whitespace en la forma canonical), Python docs (`allow_nan=False` lanza ValueError — uso como fail-fast; `parse_constant` para el test de parseo estricto), y la práctica común de sanitizadores recursive (ndarray→tolist, np.generic→item, NaN→None).

## Goals / Non-Goals

**Goals:**
- Módulo puro sin entanglement con pipeline/CLI: mergeable en verde y cubierto ~100% por TDD.
- JSON estricto garantizado por doble defensa: sanitizador previo + `allow_nan=False` como red.
- Fingerprint determinista con canonización simple (sort de claves) suficiente para comparabilidad interna.

**Non-Goals:**

- Integración en `generate_complete_analysis_report` o CLI (feat-050/051).
- Commit hash en el fingerprint (vive fuera del paquete; Non-goal documentado del épico).
- RFC 8785 completo (formato de números ECMAScript) — solo sort de claves + floats repr round-trip: suficiente para que dos corridas del MISMO código produzcan bytes comparables; la interoperabilidad cross-implementation no es objetivo de v1.
- Secciones de diagnóstico (rejections/allocation/risk/tree/walk-forward: features 044-049).

## Decisions

- **Sanitizador recursivo propio sobre stdlib** en vez de NumpyEncoder de `json.JSONEncoder`: el `default=` hook no intercepta floats finitos con NaN internos ni ordena el recorrido; el sanitizador previo permite garantizar null-before-dump y testear la conversión por tipo de forma aislada. Alternativa descartada: dependencia externa (orjson/numpy-json) — viola la política de deps mínimas del repo (stdlib-only) y el CI offline.
- **`np.generic → .item()` ANTES del check `isinstance(float)`**: `np.float64` subclasifica `float`, así que un check de float genérico convertiría el ndarray al pasar por `.tolist()` pero dejaría escalares como np.float64; `.item()` primero devuelve nativos puros.
- **Fingerprint: sha256 de `json.dumps(asdict(config), sort_keys=True)` + universo + span + engine_version, truncado a 16 hex** — mismo largo que `_cache_key` (patrón del repo), pero preimagen completa (la key de caché no cubre thresholds). Alternativa RFC 8785 estricta descartada para v1: no hay consumers cross-language del fingerprint y el número-formatting ES6 no aporta aquí; documentado para no reclamar compliance que no hay.
- **`run_id` derivado del fingerprint** (no uuid4): el proyecto pinea determinismo (feat-030, spec system-verification); un uuid rompería el contrato "misma corrida = mismo id" y ensuciaría diffs entre corridas idénticas.
- **Escritura overwrite-in-place con `mkdir(parents=True, exist_ok=True)`** (no atómica tipo cache parquet): el reporte es diagnóstico de corrida, no dato de ingesta — si dos corridas pisan, la última gana y eso es lo esperado; la complejidad atómica no paga aquí.
- **Exports solo en `app/__init__.py`**: el paquete completo (`portfolio_engine/__init__.py`) recibe los exports en feat-050 junto con la integración — evita ampliar la superficie pública dos veces y respeta el orden del DAG (043 es prerequisito, no consumible end-user aún).

## Risks / Trade-offs

- [Riesgo] Un consumidor futuro serializa algo no-nativo no contemplado (ej. np.datetime64 crudo) → Mitigación: sanitizador con rama genérica date/datetime/datetime64→ISO + test del payload envenenado como red de regresión; el fail-fast de `allow_nan=False` convierte cualquier fuga en error visible en CI, no en JSON inválido silencioso.
- [Trade-off] Precisión completa en JSON (float repr round-trip) vs legibilidad humana → decidido: el JSON es para máquinas (precisión completa); el redondeo vive en consola/PNG (ya existe).
- [Riesgo] Cobertura del gate (85% TOTAL, slack ~7 unidades): el módulo nace con TDD cubriendo todas las ramas del sanitizador → el total SUBE al merge; verificar TOTAL % en la evidencia, no solo passed.

## Migration Plan

1. Rama `feat/report-json-core` desde develop; TDD rojo (`tests/test_report_json.py` con import error) → implementación → verde.
2. `./init.sh` fresco con TOTAL % de cobertura registrado; `openspec validate` del change; commit Conventional Commits; PR a develop (push con validación del usuario).
3. Rollback: revert de 1 módulo + 1 test file + exports (todo additive, sin consumidores).

## Open Questions

Ninguna: scope, firma de sanitizador, política de run_id y ubicación de exports quedaron bloqueados con el usuario en el registro del épico (feat-043 en feature_list.json).
