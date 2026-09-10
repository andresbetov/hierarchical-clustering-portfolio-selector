# Catálogo de datos técnicos para el usuario — 9 diagnósticos

> Estado: implementado como reporte JSON (`reports/technical-report.json`, `schema_version: 1`;
> épico feat-043..051 cerrado). Define **qué** información recibe quien ejecuta el
> pipeline — pesos más expediente — **por qué** importa, **cómo** leerla y **de dónde** sale.
> Alcance convergido tras bucle de validación: investigación externa (foros, tearsheets, literatura HRP) →
> veto de factibilidad → veto de valor/duplicación → arbitraje → re-evaluación adversarial.
> Seis de los nueve son entregables incluso sobre el tag `v0.1.0` congelado, como capa consumidora externa,
> sin modificar el motor. Costes/turnover, series mensuales rodantes y ENB por PCA quedan excluidos
> (ver §10).

Cómo leer cada ficha: **Definición** (intuitiva + formal) · **Propósito** (pregunta que responde) ·
**Efecto** (qué decisión cambia, con números observados del proyecto) · **Por qué es útil aquí** ·
**Cómo leerlo** (sano / vigilancia / degenerado) · **Origen y cómputo** (file:line verificados, coste) ·
**Guards y caveats** (prohibiciones) · **Referencias verificables** (conceptuales, sin URLs).

Números del proyecto citados: filtro 12→4 (JPM 25.6%, ABBV 23.5%, MRK 20.9%, WMT topado 30.0%);
walk-forward 16 folds (train 250 / test 60 / embargo 5) con mediana OOS HRP 0.772 vs igual 0.777;
caso degenerado 15 ETFs → solo GLD 100%; defaults vigentes Sharpe≥0.3, vol≤0.27 (feat-042/ADR-007).

---

## 1. Tabla walk-forward por fold — Sharpe, retorno y volatilidad fuera de muestra de HRP frente a igual e inverso-volatilidad, más tasa de acierto

### Definición

Intuitiva: congela la cartera que habrías elegido solo con el pasado y mira cómo se habría comportado en
las semanas siguientes que aún no habías visto, fold a fold, comparada contra dos repartos ingenuos sobre
exactamente los mismos activos y los mismos días futuros.
Formal: para cada fold `f` con ventana `[train | embargo | test]`, pesos `w_f` fijados solo con `train`,
serie diaria fuera de muestra `r_{f,t} = (log-retornos del test) · w_f`, de longitud `test_rows`:
`ret_f = mean(r_f) · 252`; `vol_f = std(r_f, ddof=1) · sqrt(252)`;
`sharpe_f = (ret_f − ln(1+rf)) / vol_f`.
Agregados: `mediana_sharpe = mediana({sharpe_f válidos})` (igual para retorno y volatilidad);
`tasa_acierto = media(ret_f > 0)` sobre folds válidos. Cada fold expone además `equal` (1/N sobre
supervivientes del fold) e `inverso-volatilidad` (pesos proporcionales a `1/vol_train`) puntuados sobre la
misma `r` fuera de muestra.

### Propósito

¿Generaliza la estrategia productiva completa fuera de muestra o solo se ve bien dentro de muestra? ¿Bate de
forma estable al reparto ingenuo 1/N en mediana, y en cuántos regímenes temporales gana o pierde?

### Efecto

Cambia la decisión de desplegar, simplificar o recalibrar. Ejemplo observado: mediana `HRP 0.772` frente
a `igual 0.777` es empate técnico — veredicto: sin evidencia de superioridad sobre 1/N en ese universo;
se mantiene HRP por estructura, sin promesa de exceso de Sharpe. Un fold con `sharpe_HRP < sharpe_igual`
sistemático en caídas decide a favor del benchmark simple para ese régimen.

### Por qué es útil aquí

Única validación temporal con paridad productiva real: cada fold reaplica los filtros del pipeline vivo
solo sobre `train` (universo ex-ante), con embargo de 5 días que excede el horizonte de 1 día de la
etiqueta. Sin esta tabla, el Sharpe `wᵀΣw` es diagnóstico, no evidencia.

### Cómo leerlo

Sano: `válidos/totales ≥ 0.8`, `relajados = 0`, `tasa_acierto > 0.5` con mediana positiva, y signo
`HRP − igual` estable entre folds. Orientativo: mediana `< 0` destruye valor; `0–0.5` débil; `0.5–1.0`
aceptable sin costos; `> 1.0` sostenido fuerte y sospechoso sin costos. Degenerado: mayoría inválidos,
medianas `None`, `relajados > 0` (universos de 1–3 activos), o folds de un activo (comparación trivial).

### Origen y cómputo

Existe en `portfolio_engine/validation/walk_forward.py`: ventanas en `45–78`; dataclass por fold en
`81–94`; medianas en `167–196` (`to_dict` en `179–196`); filtro ex-ante por fold en `107–141`; guard de
riesgo degenerado en `144–164`; bucle fijar-en-train/puntuar-congelado en `199–312` (retornos del test con
precio previo en `262–264`, benchmarks en `273–284`). Coste `O(F · (N·T + N²))`, determinista.
El detalle por fold vive en `report.folds` y se expone en `walk_forward.folds` del JSON (`report_json.py`, `walk_forward_section`; feat-049).

### Guards y caveats

`N = 0` en train → fold inválido, excluido con sus benchmarks. Serie con `< 2` retornos o Sharpe no
finito → inválido, nunca válido-con-`None`. Ruta legacy `M < N`: covarianza recortada al subconjunto.
Prohibido tocar el `test` para elegir universo/pesos/umbrales; prohibido leerlo como PnL (sin costos);
prohibido comparar folds con distinto `N` sin mirar el universo; embargo `0` solo para tests.

### Referencias verificables

López de Prado, *Advances in Financial Machine Learning* (purga/embargo); Bailey–López de Prado
(Sharpe deflactado, medianas vs in-sample); DeMiguel–Garlappi–Uppal 2007 (1/N como benchmark);
práctica `skfolio` de validación temporal con benchmarks ex-ante; `quantstats` como vocabulario de
tearsheet (conceptual).

---

## 2. Curva de drawdown, caída máxima y Calmar — diagnóstico dentro de muestra

### Definición

Intuitiva: cuánto habría caído la cartera desde su último máximo con pesos fijos, y cuántos años de esa
caída compensa el retorno anual. Formal: `r_t` retorno log diario con pesos fijos `w`,
`P_t = exp(cumsum(r_t))`, `Peak_t = max_{s≤t} P_s`, `DD_t = P_t / Peak_t − 1 ≤ 0`;
`Caída_máxima = min_t DD_t`; `Calmar = ret_anualizado / |Caída_máxima|`; si `|Caída_máxima| ≤ EPS`,
`Calmar = None` (nunca infinito). Etiqueta obligatoria: dentro de muestra, no predictivo.

### Propósito

¿Qué dolor secuencial esconde un Sharpe aceptable? Igual Sharpe y volatilidad pueden coexistir con caídas
máximas muy distintas; la curva muestra duración y forma de la peor racha.

### Efecto

Cambia dimensionamiento y tolerancia, no la selección. Ejemplo: 4 supervivientes con WMT al 30% pueden
dar Sharpe razonable con caída `-20%` y Calmar `≈ 0.6` — eso prohíbe venderla como defensiva. Calmar
`< 0.5` con caída `> 25%` recomienda reducir tamaño o ensanchar universo antes de tocar el asignador.

### Por qué es útil aquí

El resumen calcula Sharpe honesto `wᵀΣw` pero ignora el orden temporal; el dendrograma muestra jerarquía
pero no dolor realizado. Es el único diagnóstico de trayectoria que conecta la concentración Dykstra con
pérdida realizada. No valida generalización (eso lo hace §1).

### Cómo leerlo

Sano (5 años, diario): caída `-10%` a `-20%`, recuperaciones en meses, Calmar `> 1.0`. Gris: `-20%` a
`-30%` o Calmar `0.5–1.0`. Degenerado: caída `> 30%`, Calmar `< 0.5` o negativo, curva plana con salto
vertical (artefacto de un activo), `Calmar = None` (serie constante), o curva que nunca baja de `-3%`
en 5 años de renta variable (error de datos, no excelencia).

### Origen y cómputo

Implementado en feat-046 (`drawdown_metrics` en `report_json.py`; serie `exp(cumsum)`, maxDD + Calmar). Origen que era punto de inserción:
matriz de retornos `pipeline.py:131–133`, pesos `allocation.py:398–435`, serie `r_t` como en
`walk_forward.py:262–266` pero in-sample alineada (`metrics.py:183–260`); Sharpe de referencia en
`reporting.py:348–387`. Coste `O(T)`. Novena figura diagnóstica como máximo, nunca insumo de pesos.

### Guards y caveats

`N = 0` → sin curva (matrices vacías `pipeline.py:93–105`); `N = 1` (caso GLD 100%) → curva del único
activo, Calmar no mide diversificación. Prohibido optimizar contra la caída mínima in-sample
(sobreajuste); prohibido mezclar log/simples en `P_t`; prohibido comparar Calmar in-sample con Sharpe
mediano OOS como la misma evidencia.

### Referencias verificables

`quantstats` (drawdown/Calmar como estándar de facto, conceptual); López de Prado (diagnóstico in-sample
vs validación con embargo; riesgo de seleccionar sobre el propio drawdown); Bailey–López de Prado
(escepticismo ante ratios sin ajuste por ensayos).

---

## 3. Motivos de exclusión por ticker y distancia al umbral

### Definición

Intuitiva: para cada ticker fuera de la cartera, etiqueta legible del porqué y a cuánto quedó del corte.
Formal: `d_sharpe_i = sharpe_i − S_min`, `d_vol_i = V_max − vol_i` (negativa = excluido por esa vía);
motivos `∈ {sharpe_no_finito, vol_no_finita, sharpe_bajo_minimo, vol_sobre_maximo, sin_precios_usables,
cobertura_calendario_baja, poda_por_solape}`; métricas no finitas sin distancia (categoría propia).

### Propósito

¿El embudo `12 → 4` es selectividad sana o umbrales duros para este universo? ¿Qué ticker rescataría un
movimiento pequeño del umbral y cuál está lejos de cualquier corte razonable?

### Efecto

Cambia el umbral o el universo, nunca los pesos. Ejemplo: excluido con `d_sharpe = −0.02` se rescata
bajando el corte a `0.25` (N 4→5, alivio al tope de WMT); con `d_vol = −0.08` incluirlo importa riesgo
no deseado. Todo-muy-negativo con `N = 1` prohíbe forzar diversificación tocando Dykstra: se cambia
universo o se acepta un activo.

### Por qué es útil aquí

Tres capas de exclusión (ingesta, calendario, filtro) hoy solo viven en logs; tabularlas evita confundir
«dato malo» con «activo malo». Sin distancias, no se sabe si el resultado es robusto o accidente de borde.

### Cómo leerlo

Sano: 3–6 supervivientes con holguras (`d_sharpe > +0.1`, `d_vol > +0.02`), excluidos repartidos entre
causas, algún «casi pasa» (`|d| < 0.05`). Frágil: superviviente con `|d| < 0.03` (sensible a la fecha de
consulta). Degenerado: `N = 0` (aborto), `N = 1` (100% + relajación crítica), o una sola causa para
todos (umbral unilateral o régimen adverso).

### Origen y cómputo

Riesgo-retorno en `selection.py:19–80` (motivos `52–63`, aviso agregado `68–79`); ingesta en
`data_fetch.py:142–226` (extracción `90–139`, rechazos `191–217`); calendario en `metrics.py:183–260`
(guard `225–239`); orquestación en `pipeline.py:84–105,110–122`; umbrales en `config.py:52–53`.
Distancias derivables de `asset_metrics` ya retornado, `O(N)`. Visualización cercana: gráfica 5
(`reporting.py:288–345`).

### Guards y caveats

No-finitos se excluyen antes de puntuar y nunca entran a corr/cov/HRP; HRP con matriz no finita falla
ruidoso (`hrp.py:104–118`). Legacy `M < N`: covarianza recortada (`allocation.py:13–31`); prohibido
reinyectar excluidos en pesos o en el test walk-forward. Prohibido apilar series sin alinear
(`metrics.py:151–177`). `N = 1` asigna 100% por diseño (`allocation.py:346–349,420–422`).

### Referencias verificables

López de Prado (cribado ex-ante sin información futura); `skfolio` (pre-selección antes de asignación
jerárquica); `quantstats` (vocabulario de tablas por activo, conceptual).

---

## 4. Concentración: índice HHI y número efectivo de activos

### Definición

Intuitiva: qué parte de la cartera vive en pocos nombres. Formal, long-only totalmente invertido:

$$\mathrm{HHI} = \sum_{i=1}^{N} w_i^2, \qquad N_{\mathrm{eff}} = 1 / \mathrm{HHI}$$

$1/N \le \mathrm{HHI} \le 1$; $1 \le N_{\mathrm{eff}} \le N$.

### Propósito

¿Diversificada por pesos o apuesta concentrada con decorado? $N=4$ puede ser $N_{\mathrm{eff}} \approx 4$
(reparto) o $\approx 1.3$ (un líder + relleno).

### Efecto

Decide relajar/endurecer filtro y caps. Observado (12→4): JPM 25.6%, ABBV 23.5%, MRK 20.9%, WMT 30.0%
→ $\mathrm{HHI} \approx 0.254$, $N_{\mathrm{eff}} \approx 3.93$: casi equiponderada pese al cap, sin
acción. Contrapunto: $\mathrm{HHI} \to 0.5$ ($N_{\mathrm{eff}} \approx 2$) → bajar `maximum_single_asset_weight`,
subir el filtro o aceptar el universo.

### Por qué es útil aquí

HRP asigna sobre todo lo filtrado sin pruning; con $N$ pequeño los bounds mandan más que la jerarquía.
HHI/$N_{\mathrm{eff}}$ distingue "HRP repartió" de "Dykstra empujó contra el cap". En el degenerado
(GLD 100%): $\mathrm{HHI}=1.0$ — el reporte es un rechazo del universo, no una asignación.

### Cómo leerlo

Sano: $\mathrm{HHI} \approx 1/N$; con $N=4$–$6$ y caps 0.05–0.30, $[0.17, 0.30]$ normal. Vigilancia:
$\mathrm{HHI} > 0.35$ o $N_{\mathrm{eff}} < N/2$. Degenerado: $\mathrm{HHI} > 0.5$ o $=1.0$: ir a huella y
walk-forward antes de operar.

### Origen y cómputo

Emitido en feat-045 (`allocation_diagnostics` en `report_json.py`). Origen que era lugar natural: junto a `_portfolio_summary_metrics` (`reporting.py:348–387`) y
`print_portfolio_summary` (`reporting.py:633–655`), desde `portfolio_weights` (`pipeline.py:139–154`).
Coste $O(N)$. Legacy $M<N$: HHI sobre el subconjunto rebanado (`allocation.py:13–31`), como ya hace
`pipeline.py:294–298`.

### Guards y caveats

$N=0$ → `None`, nunca 0. $N=1$ → $1.0$ por definición (`allocation.py:346–349,420–422`). Verificar
$\sum w = 1 \pm 10^{-9}$ antes de elevar; peso no finito → HHI `NaN`, nunca `inf`
(`VOL_FLOOR_EPS`, `metrics.py:19,62–63`).

### Referencias verificables

Herfindahl (1950)/Hirschman (1945); Meucci (2009) *Risk and Asset Allocation*; Roncalli,
*Introduction to Risk Parity and Budgeting*; `skfolio` (`Herfindahl`/`EffectiveNumberAssets`,
conceptual).

---

## 5. Huella de reproducibilidad (universo, span, hash de config, versiones, commit)

### Definición

Intuitiva: el DNI de la ejecución. Formal:

$$\mathcal{F} = (\mathcal{U}, [t_0, t_1], h(\theta), \mathcal{V}, c)$$

$\mathcal{U}$ tickers ordenados, $[t_0,t_1]$ ventana resuelta, $h(\theta)$ hash de la config efectiva,
$\mathcal{V}$ versiones fijadas, $c$ commit. Sin fórmula financiera; $h$ p. ej. SHA-256 truncado del
dataclass congelado serializado canónicamente.

### Propósito

¿A qué universo, fechas, parámetros y código corresponde este pantallazo de pesos? Sin $\mathcal{F}$,
comparar Sharpes entre fechas es peras con manzanas.

### Efecto

Decide invalidar o confiar. Ejemplos: 12→4 con 0.3/0.27 no es comparable al antiguo 0.5/0.25 sin anotar
$h(\theta)$ (2 líneas mueven $N$ 4→6 y el gap WF −0.005→+0.070); si $[t_0,t_1]$ se desplaza un día, la
key del parquet cambia y el re-run descarga de nuevo.

### Por qué es útil aquí

Ingesta de `yfinance` + `date.today()` móvil: piezas dispersas (universo externalizado, ventana pura,
key determinista, lock versionado) pero sin huella unificada. Publicarla en consola + gráfica 7 vuelve
auditable el Sharpe honesto.

### Cómo leerlo

Sano: 12 tickers, span 5 años terminando ayer, $h(\theta)$ = defaults/HRP-single/sample/0.05–0.30,
lock + commit con `./init.sh` verde. Degenerado: supervivientes $\le 1$, filas comunes $<2$
(`MIN_COMMON_ROWS`), o $h(\theta)$ ausente → resultado no citable.

### Origen y cómputo

Ensamblaje $O(1)$: universo `config/universe.yaml:4–16` vía `data/universe.py:13–46`; span
`data_fetch.py:24–39` vía `provider.py:73,97`; hash en `config_fingerprint` (`report_json.py`, feat-043) desde (`config.py:43–92`, patrón de
`_cache_key` en `data/cache.py:32–43`); versiones `pyproject.toml:3–16` + `uv.lock`; commit fuera del
paquete (punto de emisión `cli.py:101–108`). La key de caché no sustituye a $h(\theta)$ (excluye
thresholds/método/linkage); `rf` distinto comparte parquet pero debe diferir en $h(\theta)$.

### Guards y caveats

$N=0$: huella válida con `filtered=0`. El span nominal no es el efectivo (intersección interior,
guard 0.9, `metrics.py:183–260`, pruneo `pipeline.py:116–129`). Re-ejecutar mañana mueve el span:
pinear con span impreso para citar.

### Referencias verificables

Lockfile + `uv sync --frozen` (`README.md:107–118`); De Prado (embargo/purga, `walk_forward.py:1–17`);
disclaimers research-only que exigen trazabilidad (precedente feat-041).

---

## 6. Ratio de diversificación (Choueifaty) y dispersión de risk-contributions

### Definición

Intuitiva: cuánto baja el riesgo por combinar en vez de sumar. Formal, $\sigma_i = \sqrt{\Sigma_{ii}}$,
$\sigma_p = \sqrt{w^T\Sigma w}$:

$$\mathrm{DR} = \frac{\sum_i w_i \sigma_i}{\sigma_p}, \qquad
\mathrm{RC}_i = \frac{w_i (\Sigma w)_i}{\sigma_p^2}, \quad \sum_i \mathrm{RC}_i = 1$$

Dispersión útil: $\mathrm{std}(\mathrm{RC})$, $\max\mathrm{RC}-\min\mathrm{RC}$, $\max\mathrm{RC}/(1/N)$.

### Propósito

(1) ¿Diversifica de verdad (DR>1) o reparte entre gemelos (DR≈1)? (2) ¿El riesgo está equilibrado
($\mathrm{RC}_i \approx 1/N$) o un nombre manda con peso modesto?

### Efecto

Decide aceptar los pesos HRP+Dykstra o intervenir. Ejemplo: 12→4 con HHI≈0.254 parece equiponderada,
pero si $\mathrm{DR} \approx 1.05$ y $\mathrm{RC}_{\mathrm{WMT}} \approx 0.45$, hay 1 fuente de riesgo +
relleno: la acción es revisar `linkage_method` (ADR-006), estimador (ADR-005) o universo, no el cap.
El empate OOS 0.772 vs 0.777 es coherente con DR bajo: el motor no encontró diversificación explotable,
y creerle evita sobreoperar.

### Por qué es útil aquí

Detector del aplanamiento Dykstra (Addendum ADR-003 2026-09-01): la proyección (`allocation.py:245–319`,
aplicada en `426–431` tras `hrp.py:93–166`) devuelve lo euclídeamente próximo al HRP puro, no varianza
jerárquica. Caso canónico $n=5$, $\max=0.30$: $[0.45,0.13×4]\to[0.30,0.175×4]$ — el ratio intra-cluster
deja de ser $1/\mathrm{var}$ ($\alpha = 1 - V_L/(V_L+V_R)$, `hrp.py:154–156`); firma: DR cae y
$\mathrm{std}(\mathrm{RC})$ se comprime a pesos iguales pero no a riesgo igual. Sin DR/RC se confunde
"pesos aplanados" con "riesgo equilibrado".

### Cómo leerlo

Sano ($N=4$–$6$ long-only): $\mathrm{DR} \gtrsim 1.2$–$1.5$ (techo $\sqrt{N}$ incorrelacionado) y
$\mathrm{RC}_i \in [0.5/N, 1.5/N]$. Vigilancia: $\mathrm{DR} < 1.15$ con HHI bajo (falsa
diversificación); $\mathrm{RC}_i > 2/N$ (concentrado en riesgo pese al cap). Degenerado: $N=1$ →
$\mathrm{DR}=1$, $\mathrm{RC}=[1]$; $\sigma_p \le 10^{-12}$ → indefinidos.

### Origen y cómputo

Ingredientes existentes: $\sigma_p^2$ en `allocation.py:34–35` y `reporting.py:365–368` (con fallback
advertido `369–375`); $\sigma_i$ de `sqrt(diag(cov))` (patrón `hrp.py:169–176`); $(\Sigma w)_i$, $\mathrm{RC}_i$
como `allocation.py:80–81` (con `VOL_FLOOR_EPS`). Calcular tras `constrained` (`allocation.py:427–431`,
gemelo `384–389`) con la **covarianza rebanada al subconjunto** (`allocation.py:13–31`,
`pipeline.py:294–298`; $N\times N$ con vector $M<N$ rompe el producto — bug feat-028). Coste $O(N^2)$;
por fold sobre `cov_train` (`walk_forward.py:241`) despreciable. Comparar pre vs post-Dykstra
(`raw_weights`, `hrp.py:122–130`) para cuantificar el aplanamiento.

### Guards y caveats

$N=0$ → `None`. $N=1$ → convención, sin cocientes. NaN-no-inf (`metrics.py:19,62–63`;
`hrp.py:111–118` rechaza covarianza no finita/asimétrica/diag$\le 0$). Citar siempre el estimador
(`config.py:60`); DR$\ge 1$ vale long-only.

### Referencias verificables

Choueifaty–Coignard (2008) *Toward Maximum Diversification*; Meucci (2009); Roncalli
(*Risk Parity and Budgeting*); `skfolio` (`DiversificationRatio`, `RiskContribution`, conceptual).

---

## 7. Riesgo de cola in-sample: Sortino y VaR/CVaR 95% históricos

### Definición

Intuitiva: cuánto exceso por unidad de pérdida y cuánto se pierde cuando el día sale mal. Formal, sobre
retornos log diarios in-sample, tenencia diaria, sin costes, objetivo $T = \ln(1+rf)$ ($rf=0.045$,
$T \approx 0.0440$):
`DownsideDev_anual = sqrt(mean(min(0, r_t − T/252)²)) · sqrt(252)`;
`Sortino = (mean(r_t)·252 − T) / DownsideDev_anual`;
`VaR_95_diario = −cuantil_5%(r_t)`; `CVaR_95_diario = −mean(r_t | r_t ≤ cuantil_5%)`.
Etiqueta obligatoria: diagnóstico, in-sample, diario, sin costes.

### Propósito

¿El Sharpe esconde asimetría a la baja? Igual Sharpe con distinta cola: una concentra pérdidas grandes
poco frecuentes. Separa eficiencia media de dolor realizado.

### Efecto

Sortino persistentemente < Sharpe o CVaR grande vs vol diaria → endurecer filtro, exigir margen al
Sharpe o rechazar la asignación pese al Sharpe sano; Sortino ≈ Sharpe + CVaR contenido → mantener
defaults. Referencia: con `vol_anual = 0.27`, `vol_diaria ≈ 0.017`; `CVaR_95 ≈ 0.030` = en el 5% peor
la pérdida duplica la desviación típica — el Sharpe WF `≈ 0.77` no autoriza a ignorarlo (mide
media/vol, no cola).

### Por qué es útil aquí

Todo el flujo optimiza dispersión simétrica (varianza), nunca asimetría: una HRP diversificada por
varianza inversa puede cargar cola izquierda común que la distancia firmada no penaliza. Único
contrapeso de cola al optimismo in-sample antes de las medianas OOS.

### Cómo leerlo

Sano: `Sortino ≥ Sharpe`, `CVaR/|VaR| ∈ [1.0, 1.6]`, `CVaR_diario ≤ 1.5·vol_diaria`. Degenerado:
`Sortino < 0` con Sharpe positivo, `CVaR/|VaR| > 2.0`, `CVaR > 2.5·vol_diaria`. Orientativo: con
250–1250 días el cuantil 5% tiene 12–62 puntos; comparar solo dentro del mismo periodo.

### Origen y cómputo

Implementado en feat-046 (`tail_risk_metrics` en `report_json.py`). Origen que era inserción: métricas `metrics.py:43–67`, resumen `reporting.py:348–387`,
matriz alineada `pipeline.py:131–133` (`metrics.py:183–260`); serie = matriz·pesos constreñidos,
`quantile`/`mean` NumPy + máscara `minimum(0,·)`: `O(T)`. Mostrar en gráfica 7 y consola
(`reporting.py:633–654`), nunca en el optimizador.

### Guards y caveats

`N = 0/1` o `N < 2` → `NaN` con motivo, nunca 0/inf. `test_rows = 60` inválido para VaR por fold
(3 puntos): **solo in-sample**. Prohibido coser serie OOS continua entre embargo
(`walk_forward.py:227–268`); sin P&L con costes (diferidos); no anualizar VaR/CVaR con `sqrt(252)`
(cola no gaussiana).

### Referencias verificables

Sharpe 1966/1994; Sortino–Price 1994; López de Prado cap. 7 (embargo/purga) y 16 (HRP);
`quantstats.stats.sortino/value_at_risk/cvar_hist`, `skfolio` VaR/CVaR (conceptos).

---

## 8. Salud del árbol jerárquico: profundidad máxima y bandera de encadenamiento

### Definición

Intuitiva: ¿el dendrograma es un árbol equilibrado (grupos genuinos) o una cadena (un activo pelado a la
vez)? Formal, sobre la matriz de linkage SciPy `Z` (`(n−1)×4`): `profundidad_max` = camino raíz→hoja
más largo contando fusiones; `tasa_encadenamiento` = fusiones con exactamente un hijo hoja / `(n−1)`
(acreción-singleton por XOR sobre columnas 0–1 de `Z`; implementado así en feat-048 tras verificar
que la lectura ≥1-hoja tiene piso 0.5); `bandera = (profundidad_max > techo) o (tasa > umbral)`,
`techo ≈ ceil(log2(n)) + 2`. Excluidos: cofenética y balance por altura — HRP bisecta por conteo sobre
el orden de hojas, la altura es causalmente irrelevante.

### Propósito

¿Está `single` encadenando, volviendo el orden de hojas arbitrario y la bisección sin sentido económico?

### Efecto

Bandera activa bajo `single` → re-ejecutar con `average`/`ward` y comparar medianas WF + escalar;
inactiva → mantener `single` (snapshot-compatible). Ejemplo: con `n = 6`, equilibrado da
`profundidad ≈ 3`, `tasa ≈ 0.0`; cadena pura da `5` y `4/5` — mismos 6 activos, pesos distintos
solo por el orden. En `n = 1` no hay árbol que juzgar.

### Por qué es útil aquí

El chaining de `single` es el motivo documentado de parametrizar el linkage (flip a `ward` diferido a
evidencia WF). El dendrograma (gráfica 8) no es testeable ni agregable por fold; profundidad + tasa lo
convierten en números comparables entre linkages, folds y universos — donde más distorsiona la cadena
es en universos filtrados pequeños.

### Cómo leerlo

Sano: `profundidad ≤ ceil(log2(n)) + 1`, `tasa < 0.30`. Gris: rango intermedio — repetir con otro
linkage. Degenerado: `profundidad ≈ n−1`, `tasa > 0.60` (escalera). Para `n = 6`: sano `≤ 4`, cadena
`5`; para `n = 12`: sano `≤ 5`, cadena `11`. Nunca usar la altura del eje Y como salud.

### Origen y cómputo

Única fuente en `hrp.py:57–90` (`build_hrp_linkage`, distancia firmada, `squareform`, `linkage`);
orden iterativo en `hrp.py:23–42`; bisección por conteo en `hrp.py:140–156` (prueba de irrelevancia de
la altura); dendrograma reutiliza el seam en `reporting.py:479–610`; métodos en `config.py:30–33,62–63`.
Función pura `salud_arbol(Z)` en una pasada, `O(n)`. Bordes cubiertos: `n = 1` retorna 1.0 sin
clustering (`hrp.py:122–123`), `n = 2` bisección directa (`hrp.py:125–130`), placeholder `n < 2`
(`reporting.py:520–528`).

### Guards y caveats

`N = 0/1`: indefinido (`NaN` + motivo), no `0`. `n = 2`: profundidad 1, tasa 0.0 (la única
fusión es hoja-hoja: sin acreción posible), bandera falsa explícita (no patológico). No comparar profundidades brutas entre distinto `n` sin normalizar por `log2(n)`.
`ward` en SciPy asume euclidiana: aplicado sobre distancia precomputada, documentar la aproximación.

### Referencias verificables

De Prado 2016 (tree clustering, quasi-diagonalization, bisección; `single` original); docs
`scipy.cluster.hierarchy.linkage/dendrogram`; López de Prado cap. clustering/HRP; `skfolio` (Ward por
estabilidad), `pyhrp` (comparativa), Papenbrock (pros/contras); nota interna: orden de hojas, no altura.

---

## 9. Deriva entre períodos: distancia L1 entre pesos de folds válidos consecutivos

### Definición

Intuitiva: cuánto se mueve la cartera si se re-estimara en cada ventana. Formal, vectores embebidos
sobre el universo completo (supervivientes con peso, excluidos `0`):
`deriva_L1(k) = ||w_k − w_{k−1}||_1 = Σ_i |w_k,i − w_{k−1},i| ∈ [0, 2]`.
Semideriva `= deriva_L1/2` (= peso que entra). Etiqueta obligatoria: `drift-not-turnover`.

### Propósito

¿Son estables las re-estimaciones o cada ventana propone otra cartera? Sharpe alto con deriva alta =
señal inestable: indistinguible de rotación afortunada, sin extrapolación de costes.

### Efecto

Deriva baja + Sharpe `≈ 0.77` en 16 folds → mantener re-estimación y pasar a modelar costes; deriva
alta (`mediana ≈ 0.60` ≈ rotar 30 puntos por período) → sospechar churn o chaining: probar
`average`/`ward`, endurecer filtros o alargar entrenamiento. Escala: mover 10 puntos da `L1 = 0.20`;
entrar/salir al mínimo inyecta `≥ 0.10`; referencia sana `0.15–0.25` (distancia-a-igual `0.137`
observada con `N = 6` sin caps).

### Por qué es útil aquí

Los pesos por fold ya viven embebidos con ceros (diseño que alinea columnas de test): L1 comparable
aunque cambien supervivientes. Cierra el triángulo: Sharpe mediano (cuánto), benchmarks ex-ante
(contra qué), deriva (a qué precio de estabilidad). Sin ella, el gap `+0.070` podría leerse como
habilidad exigiendo rotación impagable.

### Cómo leerlo

Sano: `mediana ≤ 0.25` con `n ≈ 6` y 16/16 válidos. Vigilar: `[0.25, 0.50]` o `p90 > 0.70` (mirar
coincidencia con cambios de supervivientes). Degenerado: `> 0.60` sostenida o dientes de sierra
(churn o flip de árbol). Leer siempre junto a `n_k` y bandera del fold: L1 alta con `n` estable →
árbol; con `n` saltando → filtro.

### Origen y cómputo

Vectores y folds existen; la distancia no se agrega. Folds en `walk_forward.py:82–94`; embebido
`249–256`; ventanas `45–78` (defaults `199–206`); medianas `175–196`; relajación `allocation.py:203–230`.
Función pura sobre `report.folds`: válidos con Sharpe finito, orden por índice,
`L1 = |w_k − w_{k−1}|.sum()` NumPy, serie + mediana + `p90` + rupturas — `O(F·M)` despreciable.
Junto a medianas OOS, nunca dentro de `_oos_metrics`.

### Guards y caveats

Inválidos rompen la cadena (sin interpolar; informar pares/posibles). Solape de trains la subestima
(190/250 compartidos: cota inferior). Churn inyecta saltos mecánicos (anotar `Δn` y tickers).
Nunca anualizar ni multiplicar por bps (P&L neto falso, excluido del repo). `N = 0/1`: `NaN` con
motivo + `mandate_relaxed` cuando aplique.

### Referencias verificables

López de Prado (purga/embargo, solape; inestabilidad de la inversa como motivación HRP); DeMiguel
2009 (benchmarks ex-ante del reporte); `quantstats`, `skfolio.walk_forward` (conceptos).

---

## 10. Excluidos deliberadamente (y por qué)

- **Costes de transacción / P&L neto / turnover vivo**: sin `w_{t-1}` ni `bps` configurado es fábula;
  el backlog v0.2.0 ya lo reserva. Solo la deriva §9 (telemetría honesta) entra en v1.
- **Correlación cofenética, balance por altura, gap intra-inter**: HRP bisecta por conteo sobre el
  orden de hojas — la altura es causalmente irrelevante; el gap exige un corte plano que HRP no define.
- **Sharpe rodante**: duplica dashboard + tendencias + medianas WF; invita a sobreinterpretar ruido
  in-sample.
- **Heatmap mensual**: mismos píxeles que las tendencias, más gruesos; estacionalidad sobre 2–5 años es ruido.
- **ENB por PCA**: sin accionabilidad ("¿y si da 2.3?"), primer `O(N³)` del path HRP, confunde apuestas
  PCA con apuestas HRP.
- **Sensibilidad al estimador (sample vs LedoitWolf)**: correcto pero v0.2.0 — es la puerta de evidencia
  del flip ADR-005; entra como estudio, no como diagnóstico v1. Sensibilidad al linkage standalone se
  elimina (ADR-006 la declara de baja señal; vive como brazo secundario de ese estudio).
- **Tabla Top-N**: duplica la gráfica 7 (barras ya ordenadas); solo escalares HHI/N-eff (§4).
