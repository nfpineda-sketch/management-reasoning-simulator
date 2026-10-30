# P2J-4 · Barorreflejo directo y recertificación de la FC del paciente completo

- **Fecha:** 2026-10-30. **Rama:** `phase-2-clinical-core-shadow`. **Base:** `789b6f4` (P2J-3, cerrado).
- **Congelamiento:** `5eb3fe3` (digest `81ab565e…`), antes de leer cualquier recuento de supervivientes.
  - Antes del congelamiento sólo se imprimieron booleanos estructurales: sondas A–D, pruebas AST, reconstrucción
    exacta y no regresión de una unidad.
  - Una prueba de rutas de código sobre una región sintética de dos supervivientes imprimió sólo las claves de la
    salida. Encontró un fallo: el recálculo de P2J-3 pasaba la versión pública del filtro a su función de soporte. Se
    corrigió antes del congelamiento.
- **Números:** `docs/revision/P2J4_baroreflex.json`. Generador de los bloques: `python -m clinical_core.baroreflex_report`.
- **Alcance:** sólo sombra. Sin integración en tiempo de ejecución, migración GI ni de otra familia, aprobación final
  del barorreflejo ni de los latentes de FC, calibración de FR, recalibración de conciencia, colapso ni ajuste al
  motor heredado.

## Resumen

- **Núcleo.** Se añade el barorreflejo directo:
  - señal = max(0, (MAP_set − PAM) / MAP_set), leída sobre la PAM que resuelve el propio estado;
  - el impulso es ganancia × señal y se suma al objetivo simpático después de los términos agudo, de deuda,
    hipoxemia e hipoglucemia;
  - vale 0 a partir de MAP_set y nunca es negativo;
  - está apagado por defecto (ganancia 0, sin MAP_set): el golden sólo cambia en sus entradas de PARAMETERS y
    Contracts v2 queda idéntico;
  - el perfil rechaza una ganancia sin punto de ajuste, un punto de ajuste ≤ 0 y el barorreflejo junto al término
    de presión relativa (1 − pressure_rel). Ese término sigue en 0 en todo perfil primario de FC.
- **Temporalidad: ACYCLIC_SAME_STEP.** El impulso del minuto t lee la PAM del estado ya resuelto en t. Ni el gasto ni
  la presión ni ningún contribuyente leen el impulso o la FC, así que no hay bucle algebraico, ni solver, ni retraso
  nuevo.
- **Sondas A–D: se cumplen las cuatro.** Con PAM baja y sin déficit sólo actúa el barorreflejo; con PAM alta y
  déficit sólo actúa el impulso agudo; con ambos actúan los dos; sin ninguno, ninguno. Con PAM 117 sobre MAP_set 80
  el barorreflejo vale 0, nunca negativo.
- **Región presión / tono (P2J-3) recalculada en el código vivo: idéntica.** Unidades, filtro primario A–I, soporte
  y clases de demanda iguales al registro.
- **Fisiología previa: idéntica.** En las 654 unidades × 4 escenarios, encender el barorreflejo dejó iguales las
  filas sin FC (presión, gasto, aporte, déficit, D, lactato, FR, sangrado, GR, cristaloide) y los estados de L3 salvo
  el impulso, BloodState incluido. La FC reconstruida es igual a la del núcleo en los 12 puntos primarios.
- **Recertificación (filas candidatas: tono × demanda × superviviente lactato × combinación latente × punto del
  barorreflejo):**
  - **Demanda 1,0:**
    - entran 12 744 filas;
    - rechaza la llegada ±5 a 10 620 (BAROREFLEX_REJECTION);
    - A–F no rechazan ninguna de las compatibles con la llegada;
    - sobreviven **2124**.
  - **Demanda 1,1:**
    - entran 353 808 filas;
    - rechaza la llegada a 147 420;
    - entre las 206 388 compatibles con la llegada, E rechaza 1104 y F 432 (A, B, C y D, ninguna);
    - sobreviven **204 852**.
- **Lo que manda es la llegada.** El barorreflejo sube la FC de llegada, porque ambos casos llegan por debajo de
  todo MAP_set (57m 65 mmHg, 72f 75 mmHg). Sólo caben las combinaciones latentes con margen hasta el techo de 124 + 5
  y 112 + 5.
  - A demanda 1,0 sobrevive sólo la combinación de techo 150 (llegada sin barorreflejo 126,9 en 57m), en
    80/0,25, 80/0,5, 90/0,25 y 100/0,25. La de techo 175 llega a 128,6 y ninguna ganancia positiva le cabe.
  - A demanda 1,1 nunca sobreviven las dos combinaciones que llegan a 128,3–128,5.
- **E y F aparecen sólo con ganancia 1,5 y demanda 1,1:**
  - E · 72f (MAP_set 90 / 100, g = 0,5 y 1): tras la adecuación el tono se relaja (T → 1 / (1 + g s0)), la PAM baja y
    el barorreflejo vuelve a subir la FC, así que deja de cumplirse FC120 ≤ FC90 ≤ FC60. Es una interacción tono ×
    barorreflejo, no un fallo estructural.
  - F · 57m (MAP_set 100, g = 0,5 y 1): residual > 15.
- **Ninguna rama de tono queda incompatible con la FC.** Las tres ganancias g sobreviven en ambas demandas.
- **Doble conteo: STRUCTURALLY_DISTINCT_BUT_CORRELATED** con los tres MAP_set. La correlación es 0,94–0,95. Hay
  minutos con sólo el barorreflejo positivo: 7 % con MAP_set 80, 22 % con 90 y 37 % con 100. No hay violaciones de
  signo.
- **Identificabilidad:**
  - MAP_set y ganancia: POORLY_IDENTIFIED. Ningún nivel se vacía, pero los conjuntos supervivientes difieren.
  - Interacción con las combinaciones latentes: COUPLED según la regla (ver §14 sobre la lectura del código a demanda
    1,0).
  - Interacción con g: UNCOUPLED en los puntos admisibles, aunque con recuentos distintos con ganancia 1,5.
- **Veredicto: BAROREFLEX_HR_RECERTIFICATION_SATISFIED.** Nada aprobado.
- **Recomendación según la regla congelada: RR_NEXT.** Se lleva como incertidumbre la región superviviente (MAP_set,
  ganancia) junto con g y la demanda.

## 1. Decisiones docentes registradas (generado)

<!-- generado:decisiones -->
- **llegada**: authored minute-0 HR 57m 124 and 72f 112 bpm, +-5 bpm, no residual offset, no wider tolerance, no case-specific MAP_set or gain, no change of the intrinsic grid; all candidates failing arrival stops with BAROREFLEX_INCOMPATIBLE_WITH_ARRIVAL_HR
- **contribución**: baroreflex_drive = baroreflex_to_sympathetic_gain x baroreflex_signal, added to the sympathetic target alongside the acute effective-deficit and the accumulated-debt drives; never derived from tau_D, the tone gain, the acute-deficit gain, the arrival HR or the legacy HR
- **fecha**: 2026-10-30
- **doble conteo**: clinical audit (correlation, joint and single positivity, contribution shares, ranking changes); correlation is not rejected by itself; STRUCTURALLY_DISTINCT_BUT_CORRELATED / FUNCTIONALLY_REDUNDANT_IN_CURRENT_CASES / PATHOLOGICAL_DOUBLE_COUNTING with no correlation threshold
- **ganancia del barorreflejo**: 0 DIAGNOSTIC_NO_BAROREFLEX_REFERENCE; 0.25 / 0.5 / 1.0 / 1.5 primary exploratory support; none approved; the range is not extended after outcomes
- **reglas de FC A–F**: P2I-2AK A-F repeated unchanged for every arrival-compatible candidate
- **región latente de FC**: only P2I-2AK's surviving latent HR combinations, demand 1.0 and 1.1 separately; the HR grid is not reopened; no combination selected
- **MAP_set**: 80 / 90 / 100 mmHg: exploratory common physiological reference candidates; not case-specific, individualized, approved or fitted to the arrival pressures; no value added after outcomes
- **término antiguo**: the 1 - relative_pressure contribution (PRESSURE_TERM_DIAGNOSTIC_ONLY) never active together with the baroreflex; retired from the primary HR physiology; no duplicate pressure signals
- **ortogonalidad**: structural probes A-D before any clinical evaluation; no numeric gain approval from them
- **presión / tono**: P2J-3 A-I must not change (HR feeds no pressure or output); any change stops the package
- **región presión / tono**: P2J-3 accepted (PRESSURE_TONE_OBSERVABLE_FILTER_SATISFIED); its primary region carried as the current primary uncertainty: tone gain g 0.25 / 0.5 / 1.0, afterload a = 0.3 provisional, demand 1.0 and 1.1; none FACULTY_APPROVED; g 1.5 / 2.0 never in the primary baroreflex surface; g and a not further identified in this package
- **alcance**: shadow only; no runtime integration, GI or second-family migration, final baroreflex or HR latent approval, RR calibration, consciousness recalibration, collapse activation or legacy fitting
- **señal**: MAP is the pressure signal: baroreflex_signal = max(0, (MAP_set - MAP) / MAP_set); 0 at or above MAP_set, positive below it, approaching 1 as MAP approaches 0, never negative (unlike the old 1 - relative_pressure term, which could go negative and cancel acute / debt drive)
- **temporalidad**: the baroreflex at minute t reads the pressure already resolved at t and adds to HR without changing pressure in that step; no algebraic pressure <-> HR loop; if HR fed output or pressure the package stops
- **fisiología previa**: BloodState, output, pressure, DO2, effective deficit, D, lactate and RR unchanged exactly
<!-- /generado:decisiones -->

## 2. Señal, temporalidad y término antiguo (generado)

<!-- generado:senal -->
- **Señal y contribución:** baroreflex_signal = max(0, (MAP_set - MAP) / MAP_set), MAP = (SBP + 2 DBP) / 3 of the state as derive reports it (derived.mean_arterial_pressure, derived.baroreflex_signal); baroreflex_drive = baroreflex_to_sympathetic_gain x signal (derived.baroreflex_drive), added to the sympathetic target after the other terms; the target stays max(0, ...) and the drive keeps the common rise-at-once / tau 5 min decay
- **Temporalidad:** ACYCLIC_SAME_STEP. integration.step resolves every channel of minute t (blood, V, Hb, P, T, D) and the auxiliary lactate and demand, then sets the drive from sympathetic_target on that end state: the baroreflex reads MAP(t) of the same state derive reports at t, and HR(t) = intrinsic + saturated increment of drive(t). _perfusion (output, pressure, delivery) and every contributor read no drive and no HR, so HR(t) never reaches pressure at t or later: no algebraic loop, no solver, no added lag. The drive's existing memory (rises at once, decays with tau 5 min, KD-S2) is common to all its terms, not a baroreflex time constant.
- **Término de presión relativa:** RETIRED_FROM_PRIMARY_HR. Every P2J-4 profile carries hr_primary.PRIMARY_HR_CALIBRATION (sympathetic_per_pressure_deficit = 0), and the core refuses a profile with a baroreflex gain and a non-zero relative-pressure gain (CoreProfile). The common default keeps 1.0 with the baroreflex off, so the shadow baseline and the goldens stay identical; it never meets the baroreflex.
- **MAP_set:** 80, 90, 100 mmHg (EXPLORATORY_COMMON_REFERENCE).
- **Ganancias:** 0 (DIAGNOSTIC_NO_BAROREFLEX_REFERENCE), 0.25 (PRIMARY_EXPLORATORY_SUPPORT), 0.5 (PRIMARY_EXPLORATORY_SUPPORT), 1 (PRIMARY_EXPLORATORY_SUPPORT), 1.5 (PRIMARY_EXPLORATORY_SUPPORT).
<!-- /generado:senal -->

## 3. Sondas estructurales A–D (generado)

<!-- generado:sondas -->
| sonda | qué | PAM | impulso agudo | impulso barorreflejo | objetivo | cumple |
|---|---|---|---|---|---|---|
| A | low MAP, effective deficit 0 | 53.3 | 0.000 | 0.467 | 0.467 | sí |
| B | MAP >= MAP_set, effective deficit > 0 | 116.7 | 0.375 | 0.000 | 0.375 | sí |
| C | low MAP, effective deficit > 0 | 53.3 | 0.375 | 0.467 | 0.842 | sí |
| D | MAP >= MAP_set, effective deficit 0 | 116.7 | 0.000 | 0.000 | 0.000 | sí |

PAM 116.7 mmHg sobre MAP_set 80: impulso del barorreflejo 0.000, nunca negativo: sí. Sondas a MAP_set 100; ganancias sintéticas, sin valor clínico.
<!-- /generado:sondas -->

## 4. Orden y clases de rechazo (generado)

<!-- generado:orden -->
SUPPORT → DOMAIN → SIMULATION → ARRIVAL → A → B → F → E → C → D

Clases de rechazo: A: HR_ENVELOPE_REJECTION; ARRIVAL: BAROREFLEX_REJECTION; B: HR_ENVELOPE_REJECTION; C: HR_ENVELOPE_REJECTION; D: HR_ENVELOPE_REJECTION; DOMAIN: DOMAIN_REJECTION; E: HR_ENVELOPE_REJECTION; F: HR_ENVELOPE_REJECTION; SIMULATION: SIMULATION_REJECTION; SUPPORT: HR_PRIOR_REGION_REJECTION.

A candidate row is (tone gain g, demand, lactate survivor of P2J-3's primary filter at that g and demand, P2I-2AK surviving latent HR combination at that demand, baroreflex point (MAP_set, gain)). Its rules read L1, L3 and L3's two counterfactuals, which depend on the P3 set and the two cases' lactate-side points only, so a row's verdict is its (P3 set, 57m point, 72f point) HR unit's verdict; rows are counted with that multiplicity. SUPPORT is the latent region (combinations outside P2I-2AK's survivors never enter; counted per combination). DOMAIN is analytic (MAP_set > 0, gain >= 0, ceiling above both intrinsic rates, g primary, a = 0.3, the profile constructible); SIMULATION a run that stops or an HR missing; ARRIVAL the authored +-5 window for both cases (BAROREFLEX_REJECTION: every entering combination is arrival-compatible without the baroreflex, P2I-2AK); A-F hr_envelope_filter.failures unchanged. Every rule is read for every row; the first failure in ORDER is counted, every failure too.

When no row survives ARRIVAL at any primary baroreflex point, demand and tone gain, the package stops with BAROREFLEX_INCOMPATIBLE_WITH_ARRIVAL_HR (A-F still read, for the record). When rows pass ARRIVAL but none passes A-F, NOT_READY with NO_PRIMARY_SURVIVOR (the 'widespread failure of the certified HR A-F').
<!-- /generado:orden -->

## 5. Región que entra: P2J-3 y P2I-2AK (generado)

<!-- generado:region -->
- Combinaciones latentes de P2I-2AK que entran: demanda 1,0: 2; demanda 1,1: 9 (iguales a su grupo de llegada: sí).
- HR_PRIOR_REGION_REJECTION (combinaciones de la malla de 450 que nunca entran): 1,0: 448; 1,1: 441.
- P2J-3 recalculado en el código vivo: demand_class: sí; primary: sí; support: sí; units: sí.

| ganancia de tono | demanda | supervivientes P2J-3 (filas lactato) |
|---|---|---|
| 0.25 | 1 | 216 |
| 0.25 | 1.1 | 1092 |
| 0.5 | 1 | 181 |
| 0.5 | 1.1 | 1092 |
| 1 | 1 | 134 |
| 1 | 1.1 | 1092 |
<!-- /generado:region -->

## 6. Filtro por punto (generado)

<!-- generado:filtro -->
| tono · demanda · punto | entran | sobreviven | primera falla | combinaciones que sobreviven |
|---|---|---|---|---|
| 0.25 · 1 · MAP_set 100 · ganancia 0.25 | 432 | **216** | llegada ±5 (barorreflejo): 216 | [0] |
| 0.25 · 1 · MAP_set 100 · ganancia 0.5 | 432 | **0** | llegada ±5 (barorreflejo): 432 | — |
| 0.25 · 1 · MAP_set 100 · ganancia 1 | 432 | **0** | llegada ±5 (barorreflejo): 432 | — |
| 0.25 · 1 · MAP_set 100 · ganancia 1.5 | 432 | **0** | llegada ±5 (barorreflejo): 432 | — |
| 0.25 · 1 · MAP_set 80 · ganancia 0.25 | 432 | **216** | llegada ±5 (barorreflejo): 216 | [0] |
| 0.25 · 1 · MAP_set 80 · ganancia 0.5 | 432 | **216** | llegada ±5 (barorreflejo): 216 | [0] |
| 0.25 · 1 · MAP_set 80 · ganancia 1 | 432 | **0** | llegada ±5 (barorreflejo): 432 | — |
| 0.25 · 1 · MAP_set 80 · ganancia 1.5 | 432 | **0** | llegada ±5 (barorreflejo): 432 | — |
| 0.25 · 1 · MAP_set 90 · ganancia 0.25 | 432 | **216** | llegada ±5 (barorreflejo): 216 | [0] |
| 0.25 · 1 · MAP_set 90 · ganancia 0.5 | 432 | **0** | llegada ±5 (barorreflejo): 432 | — |
| 0.25 · 1 · MAP_set 90 · ganancia 1 | 432 | **0** | llegada ±5 (barorreflejo): 432 | — |
| 0.25 · 1 · MAP_set 90 · ganancia 1.5 | 432 | **0** | llegada ±5 (barorreflejo): 432 | — |
| 0.25 · 1 · referencia (ganancia 0) | 432 | **432** | ninguna | [0, 1] |
| 0.25 · 1.1 · MAP_set 100 · ganancia 0.25 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 0.25 · 1.1 · MAP_set 100 · ganancia 0.5 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 0.25 · 1.1 · MAP_set 100 · ganancia 1 | 9828 | **4368** | llegada ±5 (barorreflejo): 5460 | [0, 5, 6, 7] |
| 0.25 · 1.1 · MAP_set 100 · ganancia 1.5 | 9828 | **1092** | llegada ±5 (barorreflejo): 8736 | [0] |
| 0.25 · 1.1 · MAP_set 80 · ganancia 0.25 | 9828 | **7644** | llegada ±5 (barorreflejo): 2184 | [0, 1, 2, 3, 5, 6, 7] |
| 0.25 · 1.1 · MAP_set 80 · ganancia 0.5 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 0.25 · 1.1 · MAP_set 80 · ganancia 1 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 0.25 · 1.1 · MAP_set 80 · ganancia 1.5 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 0.25 · 1.1 · MAP_set 90 · ganancia 0.25 | 9828 | **7644** | llegada ±5 (barorreflejo): 2184 | [0, 1, 2, 3, 5, 6, 7] |
| 0.25 · 1.1 · MAP_set 90 · ganancia 0.5 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 0.25 · 1.1 · MAP_set 90 · ganancia 1 | 9828 | **5460** | llegada ±5 (barorreflejo): 4368 | [0, 2, 5, 6, 7] |
| 0.25 · 1.1 · MAP_set 90 · ganancia 1.5 | 9828 | **3276** | llegada ±5 (barorreflejo): 6552 | [0, 5, 6] |
| 0.25 · 1.1 · referencia (ganancia 0) | 9828 | **9828** | ninguna | [0, 1, 2, 3, 4, 5, 6, 7, 8] |
| 0.5 · 1 · MAP_set 100 · ganancia 0.25 | 362 | **181** | llegada ±5 (barorreflejo): 181 | [0] |
| 0.5 · 1 · MAP_set 100 · ganancia 0.5 | 362 | **0** | llegada ±5 (barorreflejo): 362 | — |
| 0.5 · 1 · MAP_set 100 · ganancia 1 | 362 | **0** | llegada ±5 (barorreflejo): 362 | — |
| 0.5 · 1 · MAP_set 100 · ganancia 1.5 | 362 | **0** | llegada ±5 (barorreflejo): 362 | — |
| 0.5 · 1 · MAP_set 80 · ganancia 0.25 | 362 | **181** | llegada ±5 (barorreflejo): 181 | [0] |
| 0.5 · 1 · MAP_set 80 · ganancia 0.5 | 362 | **181** | llegada ±5 (barorreflejo): 181 | [0] |
| 0.5 · 1 · MAP_set 80 · ganancia 1 | 362 | **0** | llegada ±5 (barorreflejo): 362 | — |
| 0.5 · 1 · MAP_set 80 · ganancia 1.5 | 362 | **0** | llegada ±5 (barorreflejo): 362 | — |
| 0.5 · 1 · MAP_set 90 · ganancia 0.25 | 362 | **181** | llegada ±5 (barorreflejo): 181 | [0] |
| 0.5 · 1 · MAP_set 90 · ganancia 0.5 | 362 | **0** | llegada ±5 (barorreflejo): 362 | — |
| 0.5 · 1 · MAP_set 90 · ganancia 1 | 362 | **0** | llegada ±5 (barorreflejo): 362 | — |
| 0.5 · 1 · MAP_set 90 · ganancia 1.5 | 362 | **0** | llegada ±5 (barorreflejo): 362 | — |
| 0.5 · 1 · referencia (ganancia 0) | 362 | **362** | ninguna | [0, 1] |
| 0.5 · 1.1 · MAP_set 100 · ganancia 0.25 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 0.5 · 1.1 · MAP_set 100 · ganancia 0.5 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 0.5 · 1.1 · MAP_set 100 · ganancia 1 | 9828 | **4368** | llegada ±5 (barorreflejo): 5460 | [0, 5, 6, 7] |
| 0.5 · 1.1 · MAP_set 100 · ganancia 1.5 | 9828 | **1068** | llegada ±5 (barorreflejo): 8736, F · residual a los 120: 24 | [0] |
| 0.5 · 1.1 · MAP_set 80 · ganancia 0.25 | 9828 | **7644** | llegada ±5 (barorreflejo): 2184 | [0, 1, 2, 3, 5, 6, 7] |
| 0.5 · 1.1 · MAP_set 80 · ganancia 0.5 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 0.5 · 1.1 · MAP_set 80 · ganancia 1 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 0.5 · 1.1 · MAP_set 80 · ganancia 1.5 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 0.5 · 1.1 · MAP_set 90 · ganancia 0.25 | 9828 | **7644** | llegada ±5 (barorreflejo): 2184 | [0, 1, 2, 3, 5, 6, 7] |
| 0.5 · 1.1 · MAP_set 90 · ganancia 0.5 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 0.5 · 1.1 · MAP_set 90 · ganancia 1 | 9828 | **5460** | llegada ±5 (barorreflejo): 4368 | [0, 2, 5, 6, 7] |
| 0.5 · 1.1 · MAP_set 90 · ganancia 1.5 | 9828 | **3084** | llegada ±5 (barorreflejo): 6552, E · descenso tras la adecuación: 192 | [0, 5, 6] |
| 0.5 · 1.1 · referencia (ganancia 0) | 9828 | **9828** | ninguna | [0, 1, 2, 3, 4, 5, 6, 7, 8] |
| 1 · 1 · MAP_set 100 · ganancia 0.25 | 268 | **134** | llegada ±5 (barorreflejo): 134 | [0] |
| 1 · 1 · MAP_set 100 · ganancia 0.5 | 268 | **0** | llegada ±5 (barorreflejo): 268 | — |
| 1 · 1 · MAP_set 100 · ganancia 1 | 268 | **0** | llegada ±5 (barorreflejo): 268 | — |
| 1 · 1 · MAP_set 100 · ganancia 1.5 | 268 | **0** | llegada ±5 (barorreflejo): 268 | — |
| 1 · 1 · MAP_set 80 · ganancia 0.25 | 268 | **134** | llegada ±5 (barorreflejo): 134 | [0] |
| 1 · 1 · MAP_set 80 · ganancia 0.5 | 268 | **134** | llegada ±5 (barorreflejo): 134 | [0] |
| 1 · 1 · MAP_set 80 · ganancia 1 | 268 | **0** | llegada ±5 (barorreflejo): 268 | — |
| 1 · 1 · MAP_set 80 · ganancia 1.5 | 268 | **0** | llegada ±5 (barorreflejo): 268 | — |
| 1 · 1 · MAP_set 90 · ganancia 0.25 | 268 | **134** | llegada ±5 (barorreflejo): 134 | [0] |
| 1 · 1 · MAP_set 90 · ganancia 0.5 | 268 | **0** | llegada ±5 (barorreflejo): 268 | — |
| 1 · 1 · MAP_set 90 · ganancia 1 | 268 | **0** | llegada ±5 (barorreflejo): 268 | — |
| 1 · 1 · MAP_set 90 · ganancia 1.5 | 268 | **0** | llegada ±5 (barorreflejo): 268 | — |
| 1 · 1 · referencia (ganancia 0) | 268 | **268** | ninguna | [0, 1] |
| 1 · 1.1 · MAP_set 100 · ganancia 0.25 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 1 · 1.1 · MAP_set 100 · ganancia 0.5 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 1 · 1.1 · MAP_set 100 · ganancia 1 | 9828 | **4368** | llegada ±5 (barorreflejo): 5460 | [0, 5, 6, 7] |
| 1 · 1.1 · MAP_set 100 · ganancia 1.5 | 9828 | **684** | llegada ±5 (barorreflejo): 8736, F · residual a los 120: 408 | [0] |
| 1 · 1.1 · MAP_set 80 · ganancia 0.25 | 9828 | **7644** | llegada ±5 (barorreflejo): 2184 | [0, 1, 2, 3, 5, 6, 7] |
| 1 · 1.1 · MAP_set 80 · ganancia 0.5 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 1 · 1.1 · MAP_set 80 · ganancia 1 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 1 · 1.1 · MAP_set 80 · ganancia 1.5 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 1 · 1.1 · MAP_set 90 · ganancia 0.25 | 9828 | **7644** | llegada ±5 (barorreflejo): 2184 | [0, 1, 2, 3, 5, 6, 7] |
| 1 · 1.1 · MAP_set 90 · ganancia 0.5 | 9828 | **6552** | llegada ±5 (barorreflejo): 3276 | [0, 2, 3, 5, 6, 7] |
| 1 · 1.1 · MAP_set 90 · ganancia 1 | 9828 | **5460** | llegada ±5 (barorreflejo): 4368 | [0, 2, 5, 6, 7] |
| 1 · 1.1 · MAP_set 90 · ganancia 1.5 | 9828 | **2364** | llegada ±5 (barorreflejo): 6552, E · descenso tras la adecuación: 912 | [0, 5, 6] |
| 1 · 1.1 · referencia (ganancia 0) | 9828 | **9828** | ninguna | [0, 1, 2, 3, 4, 5, 6, 7, 8] |
<!-- /generado:filtro -->

## 7. Soporte por dimensión (generado)

<!-- generado:soporte -->
| dimensión | nivel | entran | sobreviven |
|---|---|---|---|
| demanda | 1 | 12744 | 2124 |
| demanda | 1.1 | 353808 | 204852 |
| ganancia | 0.25 | 91638 | 67113 |
| ganancia | 0.5 | 91638 | 59499 |
| ganancia | 1 | 91638 | 49140 |
| ganancia | 1.5 | 91638 | 31224 |
| MAP_set | 80 | 122184 | 82962 |
| MAP_set | 90 | 122184 | 68223 |
| MAP_set | 100 | 122184 | 55791 |
| ganancia de tono | 0.25 | 123120 | 69660 |
| ganancia de tono | 0.5 | 122280 | 69304 |
| ganancia de tono | 1 | 121152 | 68012 |

Ramas de tono incompatibles con la FC tras reconectar el barorreflejo: ninguna.
<!-- /generado:soporte -->

## 8. Clasificación cruzada demanda × tono × MAP_set × ganancia (generado)

<!-- generado:cruce -->
Filas supervivientes por MAP_set / ganancia del barorreflejo.

| demanda · tono | 80/0.25 | 80/0.5 | 80/1 | 80/1.5 | 90/0.25 | 90/0.5 | 90/1 | 90/1.5 | 100/0.25 | 100/0.5 | 100/1 | 100/1.5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 · 0.25 | 216 | 216 | 0 | 0 | 216 | 0 | 0 | 0 | 216 | 0 | 0 | 0 |
| 1 · 0.5 | 181 | 181 | 0 | 0 | 181 | 0 | 0 | 0 | 181 | 0 | 0 | 0 |
| 1 · 1 | 134 | 134 | 0 | 0 | 134 | 0 | 0 | 0 | 134 | 0 | 0 | 0 |
| 1.1 · 0.25 | 7644 | 6552 | 6552 | 6552 | 7644 | 6552 | 5460 | 3276 | 6552 | 6552 | 4368 | 1092 |
| 1.1 · 0.5 | 7644 | 6552 | 6552 | 6552 | 7644 | 6552 | 5460 | 3084 | 6552 | 6552 | 4368 | 1068 |
| 1.1 · 1 | 7644 | 6552 | 6552 | 6552 | 7644 | 6552 | 5460 | 2364 | 6552 | 6552 | 4368 | 684 |
<!-- /generado:cruce -->

## 9. Observables de FC de los supervivientes (generado)

<!-- generado:observables -->
Sobre las trayectorias únicas de los supervivientes primarios (mediana [rango]), bpm.

| lectura | 57m | 72f |
|---|---|---|
| FC de llegada | 124.0 [120.4–128.8] | 111.7 [107.5–116.3] |
| FC sin tratamiento a los 120 | 141.0 [129.0–154.4] | 130.3 [116.2–150.0] |
| beneficio 1.ª unidad | 11.8 [3.6–44.2] | 14.0 [4.2–40.8] |
| beneficio 2.ª unidad | 11.8 [4.7–35.2] | 0.7 [0.0–4.9] |
| FC definitivo 60 | 104.0 [62.7–120.6] | 100.4 [80.4–106.6] |
| FC definitivo 90 | 101.1 [61.0–112.8] | 100.1 [80.1–105.3] |
| FC definitivo 120 | 100.4 [60.3–110.1] | 100.0 [80.0–105.0] |
| taquicardia residual (120 − intrínseca) | 2.0 [0.3–15.0] | 0.3 [0.0–6.4] |
| FC máxima | 141.0 [129.0–154.4] | 130.3 [116.2–150.0] |
| incremento por déficit agudo (sin tratamiento 120, sin saturar) | 27.2 [6.3–106.0] | 18.7 [4.0–75.4] |
| incremento por deuda (sin tratamiento 120, sin saturar) | 25.0 [6.3–101.7] | 10.7 [2.7–46.1] |
| incremento por barorreflejo (sin tratamiento 120, sin saturar) | 7.4 [2.6–25.3] | 5.0 [1.2–18.6] |
| efecto del barorreflejo en la FC de llegada | 2.2 [0.6–9.2] | 1.8 [0.4–7.8] |
| efecto del barorreflejo sin tratamiento a los 120 | 3.3 [0.5–17.1] | 3.0 [0.5–14.8] |
| efecto del barorreflejo tras el manejo definitivo a los 120 | 0.6 [0.0–9.6] | 0.0 [0.0–5.7] |
<!-- /generado:observables -->

## 10. Efecto del barorreflejo en la FC: llegada, sin tratamiento y definitivo (generado)

<!-- generado:incrementos -->
FC(punto) − FC(sin barorreflejo), mismo candidato (mediana [rango]), bpm, sobre los supervivientes del punto.

| punto | caso | llegada | sin tratamiento 120 | definitivo 120 |
|---|---|---|---|---|
| MAP_set 100 · ganancia 0.25 | 57m | 1.5 [1.1–2.0] | 1.8 [0.6–3.4] | 0.8 [0.2–1.9] |
| MAP_set 100 · ganancia 0.25 | 72f | 1.5 [1.2–1.6] | 1.7 [0.8–2.9] | 0.4 [0.0–1.2] |
| MAP_set 100 · ganancia 0.5 | 57m | 3.3 [2.1–4.0] | 4.0 [1.4–6.7] | 1.6 [0.5–3.8] |
| MAP_set 100 · ganancia 0.5 | 72f | 3.0 [2.4–3.2] | 3.6 [1.5–5.8] | 0.9 [0.2–2.4] |
| MAP_set 100 · ganancia 1 | 57m | 7.3 [4.2–7.8] | 9.7 [2.7–12.6] | 3.3 [1.0–7.6] |
| MAP_set 100 · ganancia 1 | 72f | 6.2 [5.3–6.4] | 8.8 [4.4–11.3] | 1.8 [0.4–4.8] |
| MAP_set 100 · ganancia 1.5 | 57m | 6.0 [6.0–6.0] | 4.0 [3.8–4.1] | 4.9 [1.5–9.6] |
| MAP_set 100 · ganancia 1.5 | 72f | 7.8 [7.8–7.8] | 7.0 [6.3–7.4] | 2.5 [0.5–5.7] |
| MAP_set 80 · ganancia 0.25 | 57m | 0.8 [0.6–1.1] | 1.5 [0.5–3.0] | 0.0 [0.0–0.8] |
| MAP_set 80 · ganancia 0.25 | 72f | 0.4 [0.4–0.5] | 1.2 [0.5–2.2] | 0.0 [0.0–0.0] |
| MAP_set 80 · ganancia 0.5 | 57m | 1.6 [1.1–2.1] | 3.1 [1.0–5.9] | 0.0 [0.0–1.6] |
| MAP_set 80 · ganancia 0.5 | 72f | 0.9 [0.7–0.9] | 2.3 [1.0–4.4] | 0.0 [0.0–0.0] |
| MAP_set 80 · ganancia 1 | 57m | 3.5 [2.2–4.2] | 6.2 [2.2–11.3] | 0.0 [0.0–3.3] |
| MAP_set 80 · ganancia 1 | 72f | 1.7 [1.4–1.9] | 4.9 [1.9–8.6] | 0.0 [0.0–0.0] |
| MAP_set 80 · ganancia 1.5 | 57m | 5.2 [3.3–6.2] | 8.9 [3.1–16.1] | 0.0 [0.0–4.9] |
| MAP_set 80 · ganancia 1.5 | 72f | 2.6 [2.1–2.8] | 7.1 [2.8–12.6] | 0.0 [0.0–0.0] |
| MAP_set 90 · ganancia 0.25 | 57m | 1.2 [0.8–1.6] | 1.6 [0.6–3.2] | 0.2 [0.0–1.4] |
| MAP_set 90 · ganancia 0.25 | 72f | 1.0 [0.8–1.1] | 1.5 [0.6–2.6] | 0.0 [0.0–0.6] |
| MAP_set 90 · ganancia 0.5 | 57m | 2.6 [1.7–3.2] | 3.7 [1.3–6.3] | 0.4 [0.0–2.8] |
| MAP_set 90 · ganancia 0.5 | 72f | 2.0 [1.7–2.2] | 3.1 [1.3–5.2] | 0.0 [0.0–1.3] |
| MAP_set 90 · ganancia 1 | 57m | 5.5 [3.3–6.2] | 8.0 [2.5–12.0] | 0.9 [0.0–5.7] |
| MAP_set 90 · ganancia 1 | 72f | 4.2 [3.7–4.4] | 7.0 [3.6–10.1] | 0.0 [0.0–2.6] |
| MAP_set 90 · ganancia 1.5 | 57m | 8.0 [4.9–9.2] | 11.2 [3.5–17.1] | 1.3 [0.0–8.4] |
| MAP_set 90 · ganancia 1.5 | 72f | 6.2 [5.4–6.5] | 10.4 [5.2–14.8] | 0.0 [0.0–3.8] |
<!-- /generado:incrementos -->

## 11. El barorreflejo en los escenarios B1–B7 (generado)

<!-- generado:escenarios -->
Señal del barorreflejo (mediana [rango]) y contribución sin saturar por unidad de ganancia (25 bpm × señal; la contribución es la ganancia por ese valor), por MAP_set, sobre las unidades que entran.

**B1 · llegada**

| caso | MAP_set | min 0 | min 15 | min 30 | min 60 | min 90 | min 120 |
|---|---|---|---|---|---|---|---|
| 57m | 100 | 0.35 [0.35–0.35]; 8.7 [8.7–8.7] bpm | — | — | — | — | — |
| 57m | 80 | 0.18 [0.18–0.18]; 4.6 [4.6–4.6] bpm | — | — | — | — | — |
| 57m | 90 | 0.27 [0.27–0.27]; 6.9 [6.9–6.9] bpm | — | — | — | — | — |
| 72f | 100 | 0.26 [0.26–0.26]; 6.5 [6.5–6.5] bpm | — | — | — | — | — |
| 72f | 80 | 0.07 [0.07–0.07]; 1.9 [1.9–1.9] bpm | — | — | — | — | — |
| 72f | 90 | 0.18 [0.18–0.18]; 4.4 [4.4–4.4] bpm | — | — | — | — | — |

**B2 · hemorragia sin tratamiento (L1)**

| caso | MAP_set | min 0 | min 15 | min 30 | min 60 | min 90 | min 120 |
|---|---|---|---|---|---|---|---|
| 57m | 100 | 0.35 [0.35–0.35]; 8.7 [8.7–8.7] bpm | 0.38 [0.37–0.38]; 9.4 [9.2–9.6] bpm | 0.41 [0.39–0.42]; 10.2 [9.7–10.6] bpm | 0.48 [0.43–0.50]; 11.9 [10.9–12.6] bpm | 0.55 [0.48–0.59]; 13.8 [12.0–14.7] bpm | 0.65 [0.53–0.67]; 16.1 [13.4–16.9] bpm |
| 57m | 80 | 0.18 [0.18–0.18]; 4.6 [4.6–4.6] bpm | 0.22 [0.21–0.23]; 5.5 [5.2–5.8] bpm | 0.26 [0.24–0.28]; 6.5 [5.9–7.0] bpm | 0.35 [0.29–0.38]; 8.6 [7.3–9.5] bpm | 0.44 [0.35–0.48]; 11.0 [8.8–12.1] bpm | 0.56 [0.42–0.59]; 13.9 [10.5–14.8] bpm |
| 57m | 90 | 0.27 [0.27–0.27]; 6.9 [6.9–6.9] bpm | 0.31 [0.30–0.32]; 7.7 [7.4–7.9] bpm | 0.34 [0.32–0.36]; 8.6 [8.0–9.0] bpm | 0.42 [0.37–0.45]; 10.5 [9.3–11.2] bpm | 0.50 [0.42–0.54]; 12.6 [10.6–13.5] bpm | 0.61 [0.48–0.64]; 15.2 [12.1–16.0] bpm |
| 72f | 100 | 0.26 [0.26–0.26]; 6.5 [6.5–6.5] bpm | 0.28 [0.27–0.29]; 7.0 [6.7–7.2] bpm | 0.30 [0.28–0.32]; 7.5 [7.0–7.9] bpm | 0.34 [0.30–0.37]; 8.5 [7.5–9.3] bpm | 0.38 [0.33–0.43]; 9.5 [8.2–10.8] bpm | 0.44 [0.36–0.50]; 11.0 [8.9–12.4] bpm |
| 72f | 80 | 0.07 [0.07–0.07]; 1.9 [1.9–1.9] bpm | 0.10 [0.09–0.11]; 2.5 [2.2–2.7] bpm | 0.12 [0.10–0.14]; 3.1 [2.5–3.6] bpm | 0.17 [0.13–0.22]; 4.3 [3.2–5.4] bpm | 0.22 [0.16–0.29]; 5.6 [4.0–7.3] bpm | 0.30 [0.20–0.37]; 7.5 [4.9–9.3] bpm |
| 72f | 90 | 0.18 [0.18–0.18]; 4.4 [4.4–4.4] bpm | 0.20 [0.19–0.21]; 5.0 [4.7–5.2] bpm | 0.22 [0.20–0.24]; 5.5 [5.0–6.0] bpm | 0.27 [0.22–0.30]; 6.6 [5.6–7.6] bpm | 0.31 [0.25–0.37]; 7.7 [6.3–9.3] bpm | 0.38 [0.29–0.44]; 9.4 [7.1–11.0] bpm |

**B3 · cristaloide (L2)**

| caso | MAP_set | min 0 | min 15 | min 30 | min 60 | min 90 | min 120 |
|---|---|---|---|---|---|---|---|
| 57m | 100 | 0.35 [0.35–0.35]; 8.7 [8.7–8.7] bpm | 0.18 [0.14–0.23]; 4.5 [3.4–5.8] bpm | 0.17 [0.11–0.23]; 4.1 [2.7–5.9] bpm | 0.23 [0.18–0.30]; 5.7 [4.4–7.4] bpm | 0.30 [0.26–0.39]; 7.5 [6.4–9.6] bpm | 0.37 [0.33–0.48]; 9.3 [8.3–12.1] bpm |
| 57m | 80 | 0.18 [0.18–0.18]; 4.6 [4.6–4.6] bpm | 0.00 [0.00–0.04]; 0.0 [0.0–1.0] bpm | 0.00 [0.00–0.04]; 0.0 [0.0–1.1] bpm | 0.04 [0.00–0.12]; 0.9 [0.0–3.0] bpm | 0.12 [0.07–0.23]; 3.1 [1.8–5.8] bpm | 0.22 [0.16–0.36]; 5.4 [4.1–8.9] bpm |
| 57m | 90 | 0.27 [0.27–0.27]; 6.9 [6.9–6.9] bpm | 0.09 [0.04–0.15]; 2.2 [1.0–3.7] bpm | 0.07 [0.01–0.15]; 1.8 [0.3–3.7] bpm | 0.14 [0.09–0.22]; 3.6 [2.2–5.5] bpm | 0.22 [0.17–0.32]; 5.5 [4.3–7.9] bpm | 0.30 [0.26–0.43]; 7.6 [6.4–10.7] bpm |
| 72f | 100 | 0.26 [0.26–0.26]; 6.5 [6.5–6.5] bpm | 0.14 [0.10–0.20]; 3.5 [2.6–4.9] bpm | 0.13 [0.08–0.20]; 3.2 [2.0–5.0] bpm | 0.17 [0.13–0.22]; 4.4 [3.3–5.6] bpm | 0.22 [0.19–0.29]; 5.5 [4.7–7.2] bpm | 0.27 [0.22–0.36]; 6.7 [5.5–8.9] bpm |
| 72f | 80 | 0.07 [0.07–0.07]; 1.9 [1.9–1.9] bpm | 0.00 [0.00–0.00]; 0.0 [0.0–0.0] bpm | 0.00 [0.00–0.00]; 0.0 [0.0–0.0] bpm | 0.00 [0.00–0.03]; 0.0 [0.0–0.8] bpm | 0.02 [0.00–0.11]; 0.6 [0.0–2.7] bpm | 0.09 [0.03–0.20]; 2.1 [0.7–4.9] bpm |
| 72f | 90 | 0.18 [0.18–0.18]; 4.4 [4.4–4.4] bpm | 0.05 [0.00–0.11]; 1.1 [0.1–2.7] bpm | 0.03 [0.00–0.11]; 0.8 [0.0–2.8] bpm | 0.08 [0.04–0.14]; 2.1 [0.9–3.4] bpm | 0.13 [0.10–0.21]; 3.3 [2.4–5.2] bpm | 0.19 [0.13–0.29]; 4.7 [3.4–7.2] bpm |

**B4 · GR antes de la hemostasia (L3 sin hemostasia)**

| caso | MAP_set | min 0 | min 15 | min 30 | min 60 | min 90 | min 120 |
|---|---|---|---|---|---|---|---|
| 57m | 100 | 0.35 [0.35–0.35]; 8.7 [8.7–8.7] bpm | 0.27 [0.24–0.32]; 6.7 [6.1–7.9] bpm | 0.22 [0.17–0.32]; 5.6 [4.2–8.0] bpm | 0.13 [0.03–0.30]; 3.1 [0.6–7.5] bpm | 0.15 [0.06–0.33]; 3.8 [1.4–8.2] bpm | 0.18 [0.09–0.36]; 4.6 [2.2–8.9] bpm |
| 57m | 80 | 0.18 [0.18–0.18]; 4.6 [4.6–4.6] bpm | 0.08 [0.06–0.15]; 2.1 [1.4–3.7] bpm | 0.03 [0.00–0.15]; 0.7 [0.0–3.7] bpm | 0.00 [0.00–0.12]; 0.0 [0.0–3.1] bpm | 0.00 [0.00–0.16]; 0.0 [0.0–4.0] bpm | 0.00 [0.00–0.20]; 0.0 [0.0–4.9] bpm |
| 57m | 90 | 0.27 [0.27–0.27]; 6.9 [6.9–6.9] bpm | 0.19 [0.16–0.24]; 4.7 [4.0–6.0] bpm | 0.14 [0.08–0.24]; 3.4 [1.9–6.1] bpm | 0.03 [0.00–0.22]; 0.7 [0.0–5.5] bpm | 0.06 [0.00–0.25]; 1.5 [0.0–6.3] bpm | 0.09 [0.00–0.29]; 2.3 [0.0–7.2] bpm |
| 72f | 100 | 0.26 [0.26–0.26]; 6.5 [6.5–6.5] bpm | 0.22 [0.19–0.28]; 5.5 [4.8–7.1] bpm | 0.16 [0.12–0.27]; 4.1 [3.0–6.7] bpm | 0.07 [0.00–0.19]; 1.6 [0.0–4.7] bpm | 0.09 [0.02–0.21]; 2.3 [0.5–5.3] bpm | 0.11 [0.05–0.24]; 2.9 [1.2–5.9] bpm |
| 72f | 80 | 0.07 [0.07–0.07]; 1.9 [1.9–1.9] bpm | 0.02 [0.00–0.10]; 0.6 [0.0–2.6] bpm | 0.00 [0.00–0.09]; 0.0 [0.0–2.1] bpm | 0.00 [0.00–0.00]; 0.0 [0.0–0.0] bpm | 0.00 [0.00–0.01]; 0.0 [0.0–0.4] bpm | 0.00 [0.00–0.05]; 0.0 [0.0–1.2] bpm |
| 72f | 90 | 0.18 [0.18–0.18]; 4.4 [4.4–4.4] bpm | 0.13 [0.10–0.20]; 3.3 [2.5–5.1] bpm | 0.07 [0.02–0.19]; 1.8 [0.6–4.7] bpm | 0.00 [0.00–0.10]; 0.0 [0.0–2.4] bpm | 0.00 [0.00–0.12]; 0.0 [0.0–3.1] bpm | 0.02 [0.00–0.15]; 0.4 [0.0–3.8] bpm |

**B5 · manejo definitivo (L3)**

| caso | MAP_set | min 0 | min 15 | min 30 | min 60 | min 90 | min 120 |
|---|---|---|---|---|---|---|---|
| 57m | 100 | 0.35 [0.35–0.35]; 8.7 [8.7–8.7] bpm | 0.27 [0.24–0.32]; 6.7 [6.1–7.9] bpm | 0.22 [0.17–0.32]; 5.6 [4.2–8.0] bpm | 0.13 [0.02–0.30]; 3.1 [0.6–7.4] bpm | 0.13 [0.03–0.30]; 3.2 [0.7–7.5] bpm | 0.13 [0.03–0.30]; 3.3 [0.8–7.6] bpm |
| 57m | 80 | 0.18 [0.18–0.18]; 4.6 [4.6–4.6] bpm | 0.08 [0.06–0.15]; 2.1 [1.4–3.7] bpm | 0.03 [0.00–0.15]; 0.7 [0.0–3.7] bpm | 0.00 [0.00–0.12]; 0.0 [0.0–3.0] bpm | 0.00 [0.00–0.13]; 0.0 [0.0–3.2] bpm | 0.00 [0.00–0.13]; 0.0 [0.0–3.3] bpm |
| 57m | 90 | 0.27 [0.27–0.27]; 6.9 [6.9–6.9] bpm | 0.19 [0.16–0.24]; 4.7 [4.0–6.0] bpm | 0.14 [0.08–0.24]; 3.4 [1.9–6.1] bpm | 0.03 [0.00–0.22]; 0.7 [0.0–5.5] bpm | 0.03 [0.00–0.22]; 0.8 [0.0–5.6] bpm | 0.04 [0.00–0.23]; 0.9 [0.0–5.7] bpm |
| 72f | 100 | 0.26 [0.26–0.26]; 6.5 [6.5–6.5] bpm | 0.22 [0.19–0.28]; 5.5 [4.8–7.1] bpm | 0.16 [0.12–0.27]; 4.1 [3.0–6.7] bpm | 0.06 [0.00–0.19]; 1.6 [0.0–4.7] bpm | 0.07 [0.00–0.19]; 1.7 [0.0–4.7] bpm | 0.07 [0.00–0.19]; 1.8 [0.0–4.8] bpm |
| 72f | 80 | 0.07 [0.07–0.07]; 1.9 [1.9–1.9] bpm | 0.02 [0.00–0.10]; 0.6 [0.0–2.6] bpm | 0.00 [0.00–0.09]; 0.0 [0.0–2.1] bpm | 0.00 [0.00–0.00]; 0.0 [0.0–0.0] bpm | 0.00 [0.00–0.00]; 0.0 [0.0–0.0] bpm | 0.00 [0.00–0.00]; 0.0 [0.0–0.0] bpm |
| 72f | 90 | 0.18 [0.18–0.18]; 4.4 [4.4–4.4] bpm | 0.13 [0.10–0.20]; 3.3 [2.5–5.1] bpm | 0.07 [0.02–0.19]; 1.8 [0.6–4.7] bpm | 0.00 [0.00–0.10]; 0.0 [0.0–2.4] bpm | 0.00 [0.00–0.10]; 0.0 [0.0–2.5] bpm | 0.00 [0.00–0.10]; 0.0 [0.0–2.6] bpm |

- **B6 · hipotensión aislada (sonda A):** PAM 53.3, impulso agudo 0.000, impulso del barorreflejo 0.467; cumple: sí.
- **B7 · déficit de oxígeno aislado (sonda B):** PAM 116.7, impulso agudo 0.375, impulso del barorreflejo 0.000; cumple: sí.
<!-- /generado:escenarios -->

## 12. Doble conteo (generado)

<!-- generado:doble_conteo -->
**Clase: STRUCTURALLY_DISTINCT_BUT_CORRELATED** (estructuralmente distintas pero correlacionadas). Sondas A–D: sí.

| MAP_set | minutos | correlación | ambas > 0 | sólo barorreflejo | sólo déficit agudo | ninguna | violaciones de signo | clase |
|---|---|---|---|---|---|---|---|---|
| 100 | 158268 | 0.939 | 62.8 % | 37.1 % | 0.0 % | 0.1 % | 0 | STRUCTURALLY_DISTINCT_BUT_CORRELATED |
| 80 | 158268 | 0.951 | 60.6 % | 7.4 % | 2.1 % | 29.8 % | 0 | STRUCTURALLY_DISTINCT_BUT_CORRELATED |
| 90 | 158268 | 0.951 | 62.7 % | 22.4 % | 0.0 % | 14.9 % | 0 | STRUCTURALLY_DISTINCT_BUT_CORRELATED |

Participación en el objetivo simpático (L1 + L3, supervivientes del punto; mediana [rango]):

| punto | déficit agudo | deuda | barorreflejo |
|---|---|---|---|
| MAP_set 100 · ganancia 0.25 | 0.68 [0.15–0.91] | 0.21 [0.04–0.82] | 0.08 [0.02–0.20] |
| MAP_set 100 · ganancia 0.5 | 0.61 [0.14–0.87] | 0.19 [0.04–0.80] | 0.14 [0.05–0.33] |
| MAP_set 100 · ganancia 1 | 0.34 [0.11–0.52] | 0.27 [0.08–0.76] | 0.34 [0.09–0.50] |
| MAP_set 100 · ganancia 1.5 | 0.17 [0.14–0.20] | 0.63 [0.54–0.73] | 0.20 [0.13–0.27] |
| MAP_set 80 · ganancia 0.25 | 0.71 [0.16–0.94] | 0.23 [0.04–0.82] | 0.02 [0.01–0.09] |
| MAP_set 80 · ganancia 0.5 | 0.67 [0.15–0.92] | 0.21 [0.04–0.81] | 0.07 [0.03–0.17] |
| MAP_set 80 · ganancia 1 | 0.62 [0.13–0.89] | 0.18 [0.04–0.79] | 0.14 [0.05–0.29] |
| MAP_set 80 · ganancia 1.5 | 0.55 [0.12–0.86] | 0.16 [0.04–0.77] | 0.20 [0.08–0.38] |
| MAP_set 90 · ganancia 0.25 | 0.69 [0.16–0.92] | 0.23 [0.04–0.82] | 0.04 [0.02–0.15] |
| MAP_set 90 · ganancia 0.5 | 0.65 [0.14–0.89] | 0.20 [0.04–0.81] | 0.11 [0.04–0.26] |
| MAP_set 90 · ganancia 1 | 0.54 [0.12–0.84] | 0.17 [0.04–0.78] | 0.27 [0.07–0.41] |
| MAP_set 90 · ganancia 1.5 | 0.15 [0.11–0.49] | 0.53 [0.09–0.75] | 0.35 [0.10–0.51] |

Cambios de orden atribuibles al barorreflejo (frente a la referencia sin barorreflejo):

| demanda · tono · punto | supervivientes de la referencia perdidos | pares discordantes 57m | pares discordantes 72f |
|---|---|---|---|
| 1 · 0.25 · MAP_set 100 · ganancia 0.25 | 18 | 0.0 % | 0.0 % |
| 1 · 0.25 · MAP_set 100 · ganancia 0.5 | 36 | 0.0 % | 1.0 % |
| 1 · 0.25 · MAP_set 100 · ganancia 1 | 36 | 0.0 % | 9.1 % |
| 1 · 0.25 · MAP_set 100 · ganancia 1.5 | 36 | 0.0 % | 9.7 % |
| 1 · 0.25 · MAP_set 80 · ganancia 0.25 | 18 | 0.0 % | 0.0 % |
| 1 · 0.25 · MAP_set 80 · ganancia 0.5 | 18 | 0.0 % | 0.0 % |
| 1 · 0.25 · MAP_set 80 · ganancia 1 | 36 | 0.0 % | 1.0 % |
| 1 · 0.25 · MAP_set 80 · ganancia 1.5 | 36 | 0.0 % | 9.1 % |
| 1 · 0.25 · MAP_set 90 · ganancia 0.25 | 18 | 0.0 % | 0.0 % |
| 1 · 0.25 · MAP_set 90 · ganancia 0.5 | 36 | 0.0 % | 0.0 % |
| 1 · 0.25 · MAP_set 90 · ganancia 1 | 36 | 0.0 % | 9.1 % |
| 1 · 0.25 · MAP_set 90 · ganancia 1.5 | 36 | 0.0 % | 9.7 % |
| 1 · 0.5 · MAP_set 100 · ganancia 0.25 | 18 | 0.0 % | 0.0 % |
| 1 · 0.5 · MAP_set 100 · ganancia 0.5 | 36 | 0.0 % | 1.9 % |
| 1 · 0.5 · MAP_set 100 · ganancia 1 | 36 | 0.0 % | 9.1 % |
| 1 · 0.5 · MAP_set 100 · ganancia 1.5 | 36 | 0.0 % | 9.1 % |
| 1 · 0.5 · MAP_set 80 · ganancia 0.25 | 18 | 0.0 % | 0.0 % |
| 1 · 0.5 · MAP_set 80 · ganancia 0.5 | 18 | 0.0 % | 0.0 % |
| 1 · 0.5 · MAP_set 80 · ganancia 1 | 36 | 0.0 % | 0.3 % |
| 1 · 0.5 · MAP_set 80 · ganancia 1.5 | 36 | 0.0 % | 7.4 % |
| 1 · 0.5 · MAP_set 90 · ganancia 0.25 | 18 | 0.0 % | 0.0 % |
| 1 · 0.5 · MAP_set 90 · ganancia 0.5 | 36 | 0.0 % | 0.0 % |
| 1 · 0.5 · MAP_set 90 · ganancia 1 | 36 | 0.0 % | 9.1 % |
| 1 · 0.5 · MAP_set 90 · ganancia 1.5 | 36 | 0.0 % | 9.7 % |
| 1 · 1 · MAP_set 100 · ganancia 0.25 | 18 | 0.0 % | 0.0 % |
| 1 · 1 · MAP_set 100 · ganancia 0.5 | 36 | 0.0 % | 5.2 % |
| 1 · 1 · MAP_set 100 · ganancia 1 | 36 | 0.0 % | 9.1 % |
| 1 · 1 · MAP_set 100 · ganancia 1.5 | 36 | 0.0 % | 9.1 % |
| 1 · 1 · MAP_set 80 · ganancia 0.25 | 18 | 0.0 % | 0.0 % |
| 1 · 1 · MAP_set 80 · ganancia 0.5 | 18 | 0.0 % | 0.0 % |
| 1 · 1 · MAP_set 80 · ganancia 1 | 36 | 0.0 % | 0.6 % |
| 1 · 1 · MAP_set 80 · ganancia 1.5 | 36 | 0.0 % | 5.2 % |
| 1 · 1 · MAP_set 90 · ganancia 0.25 | 18 | 0.0 % | 0.0 % |
| 1 · 1 · MAP_set 90 · ganancia 0.5 | 36 | 0.0 % | 1.0 % |
| 1 · 1 · MAP_set 90 · ganancia 1 | 36 | 0.0 % | 9.1 % |
| 1 · 1 · MAP_set 90 · ganancia 1.5 | 36 | 0.0 % | 9.1 % |
| 1.1 · 0.25 · MAP_set 100 · ganancia 0.25 | 273 | 1.3 % | 0.5 % |
| 1.1 · 0.25 · MAP_set 100 · ganancia 0.5 | 273 | 3.6 % | 1.1 % |
| 1.1 · 0.25 · MAP_set 100 · ganancia 1 | 455 | 11.4 % | 3.5 % |
| 1.1 · 0.25 · MAP_set 100 · ganancia 1.5 | 728 | 19.1 % | 5.2 % |
| 1.1 · 0.25 · MAP_set 80 · ganancia 0.25 | 182 | 1.0 % | 0.4 % |
| 1.1 · 0.25 · MAP_set 80 · ganancia 0.5 | 273 | 2.6 % | 0.9 % |
| 1.1 · 0.25 · MAP_set 80 · ganancia 1 | 273 | 7.8 % | 3.2 % |
| 1.1 · 0.25 · MAP_set 80 · ganancia 1.5 | 273 | 14.7 % | 4.5 % |
| 1.1 · 0.25 · MAP_set 90 · ganancia 0.25 | 182 | 1.1 % | 0.4 % |
| 1.1 · 0.25 · MAP_set 90 · ganancia 0.5 | 273 | 3.1 % | 0.9 % |
| 1.1 · 0.25 · MAP_set 90 · ganancia 1 | 364 | 9.5 % | 3.4 % |
| 1.1 · 0.25 · MAP_set 90 · ganancia 1.5 | 546 | 16.7 % | 5.1 % |
| 1.1 · 0.5 · MAP_set 100 · ganancia 0.25 | 273 | 1.3 % | 0.4 % |
| 1.1 · 0.5 · MAP_set 100 · ganancia 0.5 | 273 | 3.3 % | 0.9 % |
| 1.1 · 0.5 · MAP_set 100 · ganancia 1 | 455 | 10.6 % | 3.5 % |
| 1.1 · 0.5 · MAP_set 100 · ganancia 1.5 | 730 | 18.5 % | 5.1 % |
| 1.1 · 0.5 · MAP_set 80 · ganancia 0.25 | 182 | 1.1 % | 0.3 % |
| 1.1 · 0.5 · MAP_set 80 · ganancia 0.5 | 273 | 2.4 % | 0.7 % |
| 1.1 · 0.5 · MAP_set 80 · ganancia 1 | 273 | 7.4 % | 2.8 % |
| 1.1 · 0.5 · MAP_set 80 · ganancia 1.5 | 273 | 14.6 % | 4.3 % |
| 1.1 · 0.5 · MAP_set 90 · ganancia 0.25 | 182 | 1.2 % | 0.4 % |
| 1.1 · 0.5 · MAP_set 90 · ganancia 0.5 | 273 | 2.9 % | 0.7 % |
| 1.1 · 0.5 · MAP_set 90 · ganancia 1 | 364 | 8.9 % | 3.3 % |
| 1.1 · 0.5 · MAP_set 90 · ganancia 1.5 | 562 | 15.7 % | 5.1 % |
| 1.1 · 1 · MAP_set 100 · ganancia 0.25 | 273 | 1.1 % | 0.4 % |
| 1.1 · 1 · MAP_set 100 · ganancia 0.5 | 273 | 2.9 % | 0.9 % |
| 1.1 · 1 · MAP_set 100 · ganancia 1 | 455 | 9.5 % | 3.7 % |
| 1.1 · 1 · MAP_set 100 · ganancia 1.5 | 762 | 17.7 % | 4.9 % |
| 1.1 · 1 · MAP_set 80 · ganancia 0.25 | 182 | 0.9 % | 0.3 % |
| 1.1 · 1 · MAP_set 80 · ganancia 0.5 | 273 | 1.9 % | 0.8 % |
| 1.1 · 1 · MAP_set 80 · ganancia 1 | 273 | 6.7 % | 2.5 % |
| 1.1 · 1 · MAP_set 80 · ganancia 1.5 | 273 | 13.8 % | 4.1 % |
| 1.1 · 1 · MAP_set 90 · ganancia 0.25 | 182 | 1.0 % | 0.3 % |
| 1.1 · 1 · MAP_set 90 · ganancia 0.5 | 273 | 2.5 % | 0.8 % |
| 1.1 · 1 · MAP_set 90 · ganancia 1 | 364 | 7.9 % | 3.1 % |
| 1.1 · 1 · MAP_set 90 · ganancia 1.5 | 622 | 14.7 % | 5.0 % |
<!-- /generado:doble_conteo -->

## 13. Identificabilidad (generado)

<!-- generado:identificabilidad -->
- **MAP_set:** POORLY_IDENTIFIED (supervivientes por nivel: 100: 4659, 80: 6933, 90: 5695).
- **Ganancia del barorreflejo:** POORLY_IDENTIFIED (supervivientes por nivel: 0.25: 5622, 0.5: 4968, 1: 4095, 1.5: 2602).
- **Interacción con las combinaciones latentes (ganancias aguda y de deuda, intrínseca, techo):** demanda 1: UNCOUPLED; demanda 1.1: COUPLED.
- **Interacción con la ganancia de tono g:** demanda 1: UNCOUPLED; demanda 1.1: UNCOUPLED.

Frozen, on the primary survivors only (the gain-0 reference never counts). For a quantity with levels (MAP_set: 80 / 90 / 100; gain: 0.25 / 0.5 / 1 / 1.5), the survivor set of a level is the set of (tone gain, demand, HR unit, latent combination, other baroreflex coordinate) it keeps. WELL_CONSTRAINED when exactly one level keeps survivors; PARTIALLY_CONSTRAINED when at least one level is emptied and two or more keep survivors; POORLY_IDENTIFIED when no level is emptied but the sets differ; NON_IDENTIFIABLE when every level keeps the same set. Interactions are read the same way on the admissible baroreflex points: COUPLED when the set of (MAP_set, gain) points a latent combination (acute / debt gains, intrinsic rates, ceiling) or a tone gain keeps differs across combinations or tone gains, UNCOUPLED when it is the same.
<!-- /generado:identificabilidad -->

## 14. Lectura de la identificabilidad

- **MAP_set y ganancia: POORLY_IDENTIFIED.**
  - Ningún nivel se vacía si se juntan ambas demandas.
  - A demanda 1,0, en cambio, sólo sobreviven ganancias ≤ 0,5 con MAP_set 80 y 0,25 con 90 y 100. Si la demanda 1,0
    fuera la única, MAP_set y ganancia quedarían más acotados. Es una lectura, no una regla.
- **Interacción con las combinaciones latentes:**
  - El registro dice UNCOUPLED a demanda 1,0 y COUPLED a 1,1.
  - El texto congelado de la regla compara el conjunto de puntos que conserva cada combinación. A 1,0, la combinación
    de techo 175 no conserva ninguno y la de techo 150 conserva cuatro, así que según el texto también es COUPLED.
  - El código omite las combinaciones que no sobreviven en ningún punto. Se declara en §16 y en TD-101; el módulo
    congelado no se cambia.
  - El acoplamiento es el esperable: el incremento del barorreflejo en la llegada tiene que caber en el margen que
    dejan las ganancias aguda y de deuda y la intrínseca de cada combinación.
- **Interacción con g:** los mismos puntos admisibles en las tres ganancias; con ganancia 1,5 los recuentos bajan al
  subir g, por E (72f) y F (57m).
- **Compuesto observable:** el efecto del barorreflejo en la FC en llegada, sin tratamiento a los 120 y tras el
  manejo definitivo está en §10. Tras el manejo definitivo es casi nulo con MAP_set 80 y crece con MAP_set 100.

## 15. No regresión (generado)

<!-- generado:no_regresion -->
- Corridas de validación con el barorreflejo encendido: 654 unidades × 4 escenarios; FC reconstruida igual a la del núcleo: sí; filas sin FC iguales (presión, gasto, aporte, déficit, D, lactato, FR, sangrado, GR, cristaloide): sí; estados de L3 iguales salvo el impulso (BloodState y todos los canales): sí; el barorreflejo movió el impulso en 654 de 654.
- Puntos validados contra el núcleo: MAP_set 100 · ganancia 0.25, MAP_set 100 · ganancia 0.5, MAP_set 100 · ganancia 1, MAP_set 100 · ganancia 1.5, MAP_set 80 · ganancia 0.25, MAP_set 80 · ganancia 0.5, MAP_set 80 · ganancia 1, MAP_set 80 · ganancia 1.5, MAP_set 90 · ganancia 0.25, MAP_set 90 · ganancia 0.5, MAP_set 90 · ganancia 1, MAP_set 90 · ganancia 1.5.
- Referencia sin barorreflejo frente al diagnóstico de FC de P2J-3: g0.25 x1: 432 filas, fallas ninguna; g0.25 x1.1: 9828 filas, fallas ninguna; g0.5 x1: 362 filas, fallas ninguna; g0.5 x1.1: 9828 filas, fallas ninguna; g1 x1: 268 filas, fallas ninguna; g1 x1.1: 9828 filas, fallas ninguna.
<!-- /generado:no_regresion -->

## 16. Veredicto y eficiencia (generado)

<!-- generado:veredicto -->
**BAROREFLEX_HR_RECERTIFICATION_SATISFIED**

- impulso simpático nunca negativo: sí
- región latente igual a la de P2I-2AK: sí
- nada aprobado: sí
- término de presión relativa en 0: sí
- resultados de presión / tono A–I de P2J-3 recalculados iguales: sí
- FC reconstruida igual a la del núcleo: sí
- la referencia sin barorreflejo reproduce el diagnóstico de FC de P2J-3: sí
- señal nunca negativa y estructuralmente distinta: sí
- fisiología previa igual con y sin barorreflejo (filas y estados): sí
- Parámetros aprobados: 0.

**Recomendación: RR_NEXT**.
<!-- /generado:veredicto -->

<!-- generado:eficiencia -->
P2J-3 recalculado: 1326 trayectorias de sangre y 364 contrafactuales en caché, 1648 grupos. FC: 2616 corridas completas sin barorreflejo, 2616 de validación con barorreflejo y 1308 de estados; 266760 series de FC reconstruidas sin correr el núcleo. Barrido cartesiano: no; FC o PA heredadas leídas: no.
<!-- /generado:eficiencia -->

## 17. Recomendación: FR / respuesta ventilatoria a continuación

La regla congelada da **RR_NEXT**:

- ninguna rama de tono queda sin supervivientes;
- el doble conteo no es redundante;
- ningún nivel de MAP_set ni de ganancia se vacía;
- ambas demandas conservan supervivientes.

El sistema integrado shock → T / presión → barorreflejo → FC es coherente:

- la FC no alimenta la presión, así que reconectar no movió la región de P2J-3;
- la señal es no negativa y distinta del déficit agudo;
- los supervivientes cumplen la llegada y A–F.

Se lleva como incertidumbre la región superviviente (§8): demanda 1,0 con 80/0,25, 80/0,5, 90/0,25 y 100/0,25;
demanda 1,1 con los doce puntos, más estrechos con ganancia 1,5. Van junto con g = 0,25 / 0,5 / 1, a = 0,3 y las
combinaciones latentes que conservan margen de llegada.

Hay dos lecturas para la docencia, que no bloquean:

- **La llegada ±5 decide casi todo el recorte.** Con la tolerancia y la malla intrínseca fijadas, el barorreflejo
  sólo cabe en las combinaciones con margen. Si se quisiera admitir ganancias mayores, haría falta revisar la malla
  latente o la tolerancia, y eso está fuera de este paquete.
- **El rechazo por E con ganancia 1,5** muestra que la relajación del tono tras la adecuación y el barorreflejo
  interactúan. Si la docencia quiere un barorreflejo fuerte, convendría decidir si E debe admitir esa leve
  re-aceleración.

FR no se inicia.

## 18. Limitaciones

- **Pruebas previas al congelamiento:** booleanos estructurales y una prueba de rutas de código sobre dos
  supervivientes sintéticos que sólo imprimió claves; el fallo que encontró se corrigió antes de congelar.
- **Clasificador de interacción latente:** omite las combinaciones sin ningún superviviente (§14). Según el texto de
  la regla, a demanda 1,0 la interacción es COUPLED, no UNCOUPLED. No afecta al veredicto ni a la recomendación.
- **Validación contra el núcleo:** cada unidad compara un solo punto del barorreflejo y una sola combinación,
  rotando por los doce puntos y las combinaciones; los demás puntos se reconstruyen. La reconstrucción usa
  `derived.baroreflex_drive`, la misma función que el núcleo.
- **B3 y B4:** salen de las trayectorias de sangre en caché de P2J-3, reconstruidas al tono (exactas en P2J-2 y
  P2J-3). Dan la señal y la contribución sin saturar, no la FC saturada. B1 es sólo el minuto 0. B6 y B7 son las
  sondas A y B, sin curso temporal.
- **Medianas y rangos:** de los observables y los incrementos se calculan sobre las trayectorias únicas de los
  supervivientes, sin ponderar por filas de lactato.
- **Doble conteo:** se mide sobre los minutos con pulso de L1 y L3 de todas las unidades que entran, sin ponderar.
  Los cambios de orden se miden sobre la FC sin tratamiento a los 120.
- **Término de presión relativa:** el perfil común conserva 1,0 con el barorreflejo apagado, para que la línea base
  en sombra y los goldens sigan idénticos. Nunca convive con el barorreflejo.
- **Memoria del impulso:** sube al instante y decae con τ 5 min. Es común a todos sus términos; no es una constante
  propia del barorreflejo.
