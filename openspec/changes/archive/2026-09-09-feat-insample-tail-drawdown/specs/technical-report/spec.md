# Spec delta: technical-report (feat-046)

## ADDED Requirements

### Requirement: Diagnóstico de riesgo in-sample con serie, cola y drawdown

El reporte técnico SHALL poder incluir el riesgo in-sample de la asignación final: la serie de log-retornos diarios de la cartera (`portfolio_return_series`), las métricas de cola (`tail_risk_metrics`: Sortino log-coherente y VaR/CVaR95 históricos diarios) y las métricas de drawdown (`drawdown_metrics`: caída máxima y Calmar). La serie SHALL construirse como matriz de log-retornos por activo en orden de claves por el vector de pesos en el mismo orden; cualquier mismatch de claves SHALL fallar con error nombrado. El objetivo diario del Sortino SHALL ser `ln(1+rf)/trading_days` (coherencia-log con el Sharpe del proyecto) y la desviación downside SHALL dividirse por el N total (días sin caída cuentan como cero); sin días de caída, Sortino SHALL ser `null` con motivo mientras VaR/CVaR siguen numéricos. `VaR_95_daily` SHALL ser `-cuantil(r, 0.05)` con interpolación lineal y `CVaR_95_daily` SHALL ser `-media(r | r ≤ q05)` (cola inclusiva); SHALL cumplirse siempre `CVaR ≥ VaR` en forma firmada, y `CVaR ≥ |VaR|` cuando el VaR es no negativo (cola real de pérdidas); VaR/CVaR JAMÁS SHALL anualizarse. `max_drawdown` SHALL ser `≤ 0` siempre y `calmar` SHALL ser `retorno_anualizado(media*T)/|maxDD|`; ante serie plana `calmar` SHALL ser `null`, nunca infinito; un Calmar negativo es legal y SHALL reportarse numérico. Ante serie con menos de 2 observaciones o cualquier valor no finito, todas las métricas SHALL ser `null` con motivo (nunca 0 ni inf). La serie SHALL construirse como matriz de log-retornos por activo en orden de claves por el vector de pesos en el mismo orden; un peso SIN precios alineados SHALL fallar con error nombrado (las series con precio sin peso se embeben en cero, ruta legacy M<N). Toda sección SHALL llevar etiquetas de proveniencia in-sample/diario/sin-costes. La curva de drawdown NO se serializa (solo escalares).

#### Scenario: serie analítica exacta

- **WHEN** precios de 2 activos con 3 observaciones y pesos conocidos entran al constructor de serie
- **THEN** la serie equals `log(P[1:]/P[:-1]) @ w` en orden de claves dentro de tolerancia 1e-12

#### Scenario: peso sin precios falla nombrado

- **WHEN** los pesos contienen un ticker sin serie de precios alineados
- **THEN** el constructor falla con `ValueError` nombrado en lugar de alinear silenciosamente (las series con precio pero sin peso se embeben en cero: ruta legacy M<N, no es mismatch)

#### Scenario: serie constante con rf=0.045 usa ln(1.045)

- **WHEN** una serie constante entra a `tail_risk_metrics` con `risk_free_rate=0.045`
- **THEN** el numerador del Sortino usa `ln(1.045)` y el objetivo diario es `ln(1.045)/252` dentro de tolerancia 1e-12

#### Scenario: sin downside Sortino null pero VaR numérico

- **WHEN** todos los retornos superan el objetivo diario
- **THEN** `sortino_ratio` y `downside_deviation_annual` son `null` con motivo y `var_95_daily`/`cvar_95_daily` son numéricos con `cvar >= var` en forma firmada (la forma `cvar >= |var|` vale cuando el VaR es no negativo, i.e. cola real de pérdidas)

#### Scenario: degenerados a null con motivo

- **WHEN** la serie tiene menos de 2 observaciones o contiene no-finitos, o es plana para drawdown
- **THEN** las métricas afectadas son `null` con `reason` (serie plana: `max_drawdown == 0.0` y `calmar_ratio` null), nunca 0 ni inf ni token inválido

#### Scenario: drawdown pinneado y Calmar con signo legal

- **WHEN** una serie fija con caída y recuperación entra a `drawdown_metrics`
- **THEN** `max_drawdown == min(P/running_max(P) − 1) ≤ 0` exacto y `calmar_ratio == mean*T/|maxDD|` (negativo si el retorno anualizado es negativo)

#### Scenario: sección sobrevive a JSON estricto

- **WHEN** las tres salidas se vuelcan con el sanitizador del reporte
- **THEN** el documento parsea con parser estricto (sin NaN/Infinity) y los `null` no se confunden con ceros
