# package-interface Specification (delta)

## ADDED Requirements

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
