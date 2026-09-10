# Proposal: docs-spec-sync (feat-053)

## Why

La auditoría post-showcase encontró specs vivas que contradicen el código: Dykstra descrito como clamp iterativo, `target_portfolio_volatility` eliminado aún en contrato, superficie CLI sin `--walk-forward`, "85% branch" cuando el umbral es TOTAL combinado, scenario scipy transitorio ya cerrado, carve-out Darwin ausente, rango de propiedades 2–30 vs 2–25, serie in-sample descrita como serializada, comando del harness y purpose de quant-docs sin requirement. Las specs son el contrato: cuando mienten, el revisor pierde confianza.

## What Changes

- Sync de erratas en 10 specs vivas (8 MODIFIED + 2 ADDED): texto alineado al comportamiento real verificado; **cero cambios de comportamiento, cero código, cero tests nuevos**.
- Docs de proceso en la misma rama: CONTRIBUTING (baseline 367/89.18%, pyarrow, gates, pre-commit), AGENTS (5 pasos), pyproject (comentario TOTAL combinado), Makefile (.PHONY/help), ADR (renumerar a ADR 008 futuro + refs), catálogo (refs, mapeo 9→6, umbral 12→6), refs muertas del tracker.

## Capabilities

### New Capabilities

(none — sync de erratas sobre capacidades existentes)

### Modified Capabilities

- `numeric-correctness`, `configuration-contract`, `package-interface`, `quality-gates`, `project-packaging`, `runtime-diagnostics`, `system-verification`, `technical-report`, `verification-harness`, `quant-docs`: corrección de texto al comportamiento real; sin cambio de comportamiento.
