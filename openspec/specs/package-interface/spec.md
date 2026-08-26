# package-interface Specification

## Purpose
Garantizar que el proyecto se comporte como un paquete Python de primera clase: instalable de forma reproducible, con punto de entrada de consola estable, y sin requerir hacks de `sys.path` para importarse desde cualquier contexto gestionado por uv.

## Requirements

### Requirement: Construcción wheel determinista

El paquete SHALL declarar `[build-system]` con backend pinned y SHALL construir un wheel que contenga el paquete `portfolio_engine` completo.

#### Scenario: uv sync instala el proyecto
- **WHEN** un clon limpio ejecuta `uv sync`
- **THEN** la salida incluye la instalación del propio paquete (además de dependencias) y `import portfolio_engine` funciona en el venv sin hacks de path

### Requirement: Entrypoint de consola estable

El proyecto SHALL exponer `portfolio-run` como console-script apuntando a una función `main` sin argumentos dentro del paquete, que ejecuta el análisis estándar documentado.

#### Scenario: invocación desde CLI
- **WHEN** se ejecuta `uv run portfolio-run` en un entorno con acceso a datos
- **THEN** corre el pipeline estándar generando reporte y figuras, sin requerir directorio de trabajo particular ni variables extra

### Requirement: Legado delega, no duplica

El script histórico bajo `scripts/` SHALL ser un wrapper que delegue en el entrypoint del paquete y SHALL NOT contener manipulación manual de `sys.path`.

#### Scenario: script sigue operativo
- **WHEN** se inspecciona `scripts/assets-investment.py`
- **THEN** su cuerpo se limita a configurar logging e invocar `portfolio_engine.cli.main()`

### Requirement: Identidad inspeccionable por runtime

La distribución SHALL poder resolverse vía `importlib.metadata` (nombre y entry-points), permitiendo tests verificar el packaging como comportamiento y no como texto en pyproject.

#### Scenario: metadatos consultables
- **WHEN** un test consulta los entry-points del grupo `console_scripts` del paquete instalado
- **THEN** existe `portfolio-run` con valor `portfolio_engine.cli:main`

### Requirement: Proveedor de mercado inyectable

La orquestación SHALL aceptar un proveedor de datos opcional que implemente el Protocol `MarketDataProvider` (método `fetch_metrics` con la firma contractual); por defecto SHALL construir el adaptador yfinance interno. La orquestación SHALL NOT importar módulos de transporte directamente.

#### Scenario: inyección offline
- **WHEN** main() corre con un FakeProvider sintético
- **THEN** el pipeline completa sin tocar red ni patching del interno

#### Scenario: compatibilidad de legado
- **WHEN** código existente llama download_and_calculate_metrics
- **THEN** la función delega al adaptador con comportamiento idéntico

### Requirement: Límite de canvas en orquestación

El módulo app/pipeline SHALL remain libre de imports de matplotlib/pyplot; toda interacción de dibujo vive bajo viz/.

#### Scenario: verificación estática continua
- **WHEN** se inspeccionan los imports de app/pipeline.py
- **THEN** no existe referencia a matplotlib o pyplot
