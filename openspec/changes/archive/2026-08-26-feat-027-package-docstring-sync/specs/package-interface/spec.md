# package-interface Specification (delta)

## ADDED Requirements

### Requirement: Docstring de paquete reflector del estado real

El docstring de `portfolio_engine/__init__.py` SHALL describir el método de asignación default vigente (hrp), la distancia firmada, la validación walk-forward disponible y los ADRs de referencia; la superficie exportada SHALL incluir los entrypoints canónicos (calculate_hrp_weights, load_universe, walk_forward_evaluate).

#### Scenario: onboarding coherente
- **WHEN** un lector abre __init__.py tras el DAG completo
- **THEN** la documentación coincide con comportamiento y exports reales
