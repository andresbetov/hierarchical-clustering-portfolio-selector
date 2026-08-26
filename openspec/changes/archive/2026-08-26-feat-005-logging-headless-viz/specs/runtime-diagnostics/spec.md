# runtime-diagnostics Specification (delta)

## Purpose

Garantizar que la salida de diagnóstico (logs) y el ciclo de vida de figuras se comporten de forma predecible e idempotente en los tres entornos donde corre el proyecto: interactivo con display, CI sin display, y sesiones de agente/pytest que configuran handlers ajenos.

## ADDED Requirements

### Requirement: Logging aislado bajo el namespace del paquete

La configuración de logging SHALL operar sobre el logger `"portfolio_engine"` (que cubre todos sus módulos hijos) con handler dedicado y `propagate=False`, y SHALL NO configurar el logger raíz ni depender de su estado.

#### Scenario: import bajo pytest
- **WHEN** los módulos del paquete se importan dentro de una sesión pytest con caplog activo
- **THEN** no se añaden handlers al logger raíz ni se altera su comportamiento

### Requirement: Idempotencia por deduplicación

Llamar `configure_logging` más de una vez SHALL resultar en exactamente un handler propio del paquete, preservando el nivel vigente; re-invocaciones con nivel explícito distinto SHALL actualizar el nivel.

#### Scenario: doble invocación
- **WHEN** `configure_logging()` se llama dos veces seguidas
- **THEN** el logger tiene un único StreamHandler propio y ningún duplicado de output

### Requirement: Resolución de nivel param > env > default

El nivel efectivo SHALL resolverse como: parámetro explícito de `configure_logging`; si no, variable de entorno `LOG_LEVEL` (insensible a mayúsculas); si no, INFO. Un valor inválido en env SHALL advertir y caer al default sin fallar el proceso.

#### Scenario: make run-debug funcional
- **WHEN** se ejecuta con `LOG_LEVEL=DEBUG` y sin parámetro explícito
- **THEN** el logger del paquete queda a nivel DEBUG

### Requirement: Ciclo de vida de figuras seguro por entorno

Cuando no exista display disponible y el usuario no haya forzado `MPLBACKEND`, el backend SHALL resolverse a Agg antes de cualquier import de pyplot/seaborn del paquete; el cierre de figuras SHALL ser determinista: guardar+cerrar cuando no hay show, mostrar-no-bloqueante cuando lo hay.

#### Scenario: corrida en CI sin display
- **WHEN** `generate_complete_analysis_report(save_plots=True, show_plots=False)` corre sin DISPLAY
- **THEN** las figuras se guardan y cierran sin warnings interactivos y el proceso termina limpio

### Requirement: Capa app sin canvas

La orquestación (`app/pipeline.py`) SHALL NOT importar matplotlib directamente; todo acceso a pyplot vive bajo `viz/`.

#### Scenario: verificación estática del límite
- **WHEN** se inspecciona `app/pipeline.py` tras el change
- **THEN** no contiene imports de matplotlib ni llamadas a pyplot
