# Spec delta: runtime-diagnostics (feat-053, MODIFIED)

## MODIFIED Requirements

### Requirement: Ciclo de vida de figuras seguro por entorno

Cuando no exista display disponible y el usuario no haya forzado `MPLBACKEND`, el backend SHALL resolverse a Agg antes de cualquier import de pyplot/seaborn del paquete — salvo en macOS (darwin), donde se respeta el backend nativo; el cierre de figuras SHALL ser determinista: guardar+cerrar cuando no hay show, mostrar-no-bloqueante cuando lo hay.

#### Scenario: corrida en CI sin display

- **WHEN** `generate_complete_analysis_report(save_plots=True, show_plots=False)` corre sin DISPLAY
- **THEN** las figuras se guardan y cierran sin warnings interactivos y el proceso termina limpio

#### Scenario: macOS respeta backend nativo

- **WHEN** `_resolve_backend` corre en darwin sin DISPLAY
- **THEN** retorna None (no fuerza Agg)
