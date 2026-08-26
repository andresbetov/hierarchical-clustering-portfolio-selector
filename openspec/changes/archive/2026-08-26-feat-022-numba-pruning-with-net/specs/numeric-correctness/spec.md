# numeric-correctness Specification (delta)

## ADDED Requirements

### Requirement: Paridad semántica tras de-jit

La reescritura vectorizada de los kernels SHALL preservar bit-a-bit el contrato vigente: Sharpe NaN bajo piso épsilon, volatilidad muestral ddof=1, diagonal condicionada a varianza>0, propagación NaN en distancias y firmas públicas intactas — verificado por la suite de caracterización existente sin modificaciones a asserts salvo drift real.

#### Scenario: red de regresión verde
- **WHEN** los kernels reescritos corren bajo la suite completa (unitarios + propiedades + E2E)
- **THEN** no se modifica ningún assert y toda la verificación pasa
