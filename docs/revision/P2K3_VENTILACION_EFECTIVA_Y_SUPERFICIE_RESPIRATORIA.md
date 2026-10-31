# P2K-3 · Ventilación efectiva desacoplada de la FR y superficie de decisión respiratoria

- **Fecha:** 2026-10-31. **Rama:** `phase-2-clinical-core-shadow`. **Base:** `cbec249` (P2K-2, cerrado).
- **Congelamiento:** `75dc218` (digest `38e30b84…`), antes de contar cualquier candidato de llegada o leer
  cualquier trayectoria respiratoria clínica.
- **Recongelamiento tras la revisión adversarial:** `bb6d81e` (digest `23f1673f…`). Sólo cambia la maquinaria (§17);
  los soportes, las tolerancias, las referencias y los criterios son los mismos. La reevaluación da los mismos números
  en la llegada, R1–R4, el paquete A–I, la validación y el veredicto.
  - Antes de congelar sólo se leyeron entradas y sondas sintéticas: el gas de llegada del banco, las ganancias
    implícitas que da la docencia y las sondas A–I.
  - Las rutas de código se probaron sobre un almacén sintético y sobre una corrida real de la que sólo se imprimieron
    booleanos: la igualdad factorización = núcleo, la igualdad aguas arriba y la reproducción de P2K-2. Esa corrida
    usó sólo el candidato de validación predeclarado.
- **Números:** `docs/revision/P2K3_ventilation_surface.json`. Generador de los bloques:
  `python -m clinical_core.ventilation_surface_report`.
- **Alcance:** sólo sombra. Sin aprobación de FR, de carga ácida ni de ganancia de ventilación. Sin envolvente ni
  filtro tardío, sin recalibrar conciencia, sin colapso, sin ventilación mecánica, sin migraciones ni integración en
  tiempo de ejecución, sin ajuste a la FR heredada.

## Resumen

- **Qué cambia.** En P2K-2, W era proporcional a FR / FR intrínseca. Por eso una FR intrínseca de 12–16 implicaba una
  PaCO2 en reposo de hasta unos 74 mmHg (FREQUENCY_TO_VENTILATION_OVERCONSTRAINT). La candidata P2K-3 usa el mapeo de
  la docencia:
  - capacidad ventilatoria = eficiencia × (1 + ganancia ácido → ventilación × carga ácida);
  - W = capacidad / (demanda / demanda basal del paciente);
  - PaCO2 = 40 / W.

  La FR sigue la estructura de P2K-2 y la PaCO2 de llegada se predice, nunca se ancla. La carga ácida mueve la FR y,
  por separado, recluta ventilación (volumen corriente implícito): un impulsor común, no una identidad.
- **Dónde vive.** En un módulo de fisiología nuevo, `clinical_core/ventilation.py`, que ningún paso del núcleo lee.
  `derived.py`, `integration.py`, `state.py` y `acid_base.py` no cambian: sus huellas son las de `cbec249`. Toda
  corrida por defecto, el golden y todo registro cerrado quedan iguales por construcción. El W de P2K-2 se conserva en
  `derived.respiration` sólo para reproducir su registro cerrado; en la candidata P2K-3 queda reemplazado.
- **Desacople, probado:**
  - W no lee ningún nombre de FR, de FR intrínseca, de impulso, de lactato, de D ni del canal W (prueba estática, §4);
  - en 48 corridas completas, cambiar la ganancia de frecuencia o la FR intrínseca sobre los mismos estados deja W,
    PaCO2 y pH idénticos;
  - sin carga y con la demanda basal, W = 1 y PaCO2 = 40 para toda FR intrínseca (sonda H).
  - **Las sondas A–I pasan todas.**
- **Llegada (analítica):**
  - FR: 9 de 45 combinaciones (igual que P2K-2);
  - PaCO2: 4 de las 5 ganancias comunes (0,03–0,06). Con 0,08, 57m queda en 26,0 y 72f en 29,9;
  - en conjunto: 36 de 225 (324 de 2025 con los nueve pares B/τ, que la llegada no lee);
  - pH diagnóstico: PH_CONSISTENT en ambos casos con 0,04 y 0,05; con 0,03 los dos quedan apenas fuera (−0,03); con
    0,06, 57m queda fuera (+0,036). No filtra.
- **Clínica (R1–R4):**
  - la PaCO2 en reposo implícita ya no depende de la FR intrínseca: es 40 en todas. Con el mapeo de P2K-2, sobre los
    mismos candidatos de FR, iba de 39 a 73;
  - en R4 la PaCO2 a 120 min se acerca a 40 en todas las combinaciones (57m 35,3 [30,6–38,7]; 72f 37,2 [34,3–39,3]);
  - la caída precoz de la FR de 72f sigue siendo posible, y es ácida, no por lactato;
  - el lactato y la FR se mueven en sentidos opuestos al menos un minuto en la mayoría de las combinaciones
    (259 118 de 313 794);
  - pH 6,96–7,42: ningún valor fuera del rango plausible 6,8–7,8 y ningún rechazo. El mínimo, 6,96, es una acidemia
    grave en la esquina extrema sin tratamiento (R1 57m).
- **Previo intacto.** En los siete dominios (BloodState, gasto, presión/tono, DO2/déficit, D, lactato, FC/barorreflejo)
  las filas y los estados son iguales con la candidata y sin ella. P2K-1, P2K-2 y la región de P2J-3 se reproducen.
- **Veredicto: RR_VENTILATION_DECISION_SURFACE_READY.** Nada se aprueba. Se pide a la docencia un juego pequeño de
  envolventes observables (§14), que no se aplican.

## 1. Decisiones docentes registradas (generado)

<!-- generado:decisiones -->
- **carga ácida**: the untreated burden is not forced to rise (production and clearance coexist; it may fall when clearance exceeds production); B 13.4 / 19.4 / 28 and tau 60 / 120 / 240 kept, none approved, no extension
- **PaCO2 de llegada**: 57m 31, 72f 33 at +/- 3 mmHg (ARRIVAL_PACO2_TOLERANCE_PROVISIONAL): 28-34 and 30-36; one common ventilation gain; zero common survivors is a stop, never a wider tolerance
- **pH de llegada**: 57m 7.37, 72f 7.40; pH derived from HCO3 and PaCO2, never tuned; +/- 0.03 diagnostic only (PH_CONSISTENT / PH_INCONSISTENT), never a filter (it would count the same HCO3 / PaCO2 twice)
- **FR de llegada**: 57m 26 +/- 3, 72f 24 +/- 3; patient-specific intrinsic RR, common drive gain, no residual offset
- **P2K-2**: P2K-2 accepted and closed: the acid burden explicit and independent of lactate and D, lactate -> RR retired in the candidate, no D -> RR, an explicit drive, PaCO2 and pH causal, RR and W distinguishable; numeric RR calibration NOT authorized
- **fecha**: 2026-10-31
- **paquete de decisión**: LOW / median / HIGH for nine observables, prepared, never approved; no late hard filter
- **eficiencia ventilatoria**: 1 for the GI cases as a STRUCTURAL_REFERENCE; no clinical efficiency grid; below 1 only in synthetic probes; not a universal constant (future mechanics, dead space or fatigue families may replace it)
- **problema**: FREQUENCY_TO_VENTILATION_OVERCONSTRAINT: W proportional to RR / intrinsic RR made a low intrinsic RR (12-16) imply a resting PaCO2 up to about 74 mmHg once the burden resolved; intrinsic RR 12 and 16 are not removed to hide it
- **mapeo de la ventilación efectiva**: ventilatory_capacity = ventilation_efficiency x (1 + acid_to_ventilation_gain x metabolic_acid_burden); W = ventilatory_capacity / metabolic_demand; W = 1 matches the BASELINE metabolic CO2 demand, above 1 relative hyperventilation, below 1 relative hypoventilation
- **no regresión**: BloodState, output, pressure / tone, DO2 / deficit, D, lactate and HR / baroreflex unchanged; an upstream change stops the package
- **PaCO2**: PaCO2 = PaCO2_reference / W = PaCO2_reference x demand / capacity; PaCO2_reference 40 mmHg COMMON_REFERENCE_PROVISIONAL, not FACULTY_APPROVED; at no burden, demand 1 and efficiency 1 it is 40 independently of intrinsic RR (intentional)
- **referencias y tolerancias**: HCO3_reference 24 and PaCO2_reference 40 COMMON_REFERENCE_PROVISIONAL; arrival RR +/- 3 ARRIVAL_RR_TOLERANCE_PROVISIONAL; none FACULTY_APPROVED; unchanged after outcomes
- **FR**: P2K-2's RR structure kept: intrinsic RR 12 / 16 / 20 per patient, the frozen drive-gain support, S = 25 semantics; no range changed
- **alcance**: shadow only: no runtime integration, GI or second-family migration, final RR / acid / ventilation-gain approval, hard respiratory envelope, consciousness recalibration, collapse activation, mechanical ventilation or legacy fitting
- **impulsor común**: the acid burden drives RR (frequency) and, independently, effective ventilation recruitment (W): two responses to one driver, never an identity; RR must not determine W
- **soporte respiratorio**: spontaneous breathing only: no NIV, invasive ventilation, PEEP, modes, fatigue, mechanics or tidal-volume state; FUTURE_RESPIRATORY_GENERALIZATION
- **incertidumbre previa**: carry only dimensions that reach the acid / respiratory physiology: demand (causal), tone g (small, through output and deficit); MAP_set, the baroreflex and the HR latent region have no path
- **ganancia ácido → ventilación**: 0.03 / 0.04 / 0.05 / 0.06 / 0.08 per mEq/L, EXPLORATORY, not FACULTY_APPROVED, built from the authored arrival gases (57m about 0.043, 72f about 0.050); no value added after results
<!-- /generado:decisiones -->

## 2. Lo que representa la candidata (generado)

<!-- generado:semantica -->
| magnitud | definición |
|---|---|
| burden | P2K-2 unchanged: A' = A + (B / tau) x effective deficit - A / tau, never forced to rise |
| candidate | the P2K-2 profile with its three gains declared, plus ventilation.VentilationCandidate(gain); the core's step, derive and arrival state never read it, so no core file changes |
| capacity | ventilation.ventilatory_capacity = efficiency x (1 + acid_to_ventilation_gain x A): the implicit tidal-volume / effective-ventilation recruitment by the acid burden; no tidal-volume state |
| demand | BASELINE_RELATIVE: the metabolic demand is the minute's oxygen demand over the patient's baseline demand (which carries the 1.0 / 1.1 demand class), as in P2K-2: W = 1 is the ventilation of the patient's own baseline CO2 production, so the demand class reaches W only through the deficit and the burden. The absolute demand index is the alternative, reported analytically as a sensitivity (it would make the 1.1 class 10 % hypercapnic at rest), never used |
| efficiency | the profile's ventilation_efficiency, 1 in every clinical evaluation (structural reference) |
| frequency_drive | RR - intrinsic RR: the drive's share of the rate |
| old_mapping | P2K-2 (derived.alveolar_ventilation): W = efficiency x (RR / intrinsic RR) / (demand / baseline), PaCO2 = PaCO2_rest / W with PaCO2_rest anchored to the authored arrival PaCO2; kept in derived.respiration only to reproduce the closed P2K-2 record, SUPERSEDED in the P2K-3 candidate |
| paco2 | PaCO2 = 40 / W (the profile's paco2_reference_mmhg): predicted at arrival, never anchored to the authored PaCO2, which only filters (+/- 3) |
| ph | pH = 6.1 + log10(HCO3 / (0.03 PaCO2)) (derived.carbonic_ph); HCO3 = arrival HCO3 - (A - A0) (P2K-2) |
| recruitment | 1 + acid_to_ventilation_gain x A: the ventilation side's response to the same burden |
| rr | P2K-2 unchanged: drive = acid_to_drive_gain x A, RR = intrinsic + S (1 - exp(-drive / S)), S = 25 |
| w | ventilation.effective_ventilation = capacity / (aux.oxygen_demand / anchors.metabolic_demand_baseline); 0 without breathing (no pulse); no RR, intrinsic RR, drive gain, lactate, D or W-channel term |

**Estados:** acid_to_ventilation_gain = EXPLORATORY; approved = none FACULTY_APPROVED; arrival_paco2_tolerance = ARRIVAL_PACO2_TOLERANCE_PROVISIONAL; arrival_rr_tolerance = ARRIVAL_RR_TOLERANCE_PROVISIONAL; bicarbonate_reference = COMMON_REFERENCE_PROVISIONAL; demand = BASELINE_RELATIVE; paco2_reference = COMMON_REFERENCE_PROVISIONAL; ph_tolerance = DIAGNOSTIC_ONLY; tidal_volume = IMPLICIT; ventilation_efficiency = STRUCTURAL_REFERENCE.

**FUTURE_RESPIRATORY_GENERALIZATION** (nada de esto se agrega en P2K-3):
- fatigue: a fatigue state would cap or erode the recruitment over time
- hypoxaemic_drive: HYPOXEMIC_DRIVE_DEFERRED (P2K-2); a term would add to the drive
- invasive: NOT_MODELED
- mechanics: a mechanics family would lower ventilation_efficiency (compliance, resistance, dead space)
- modes: NOT_MODELED
- niv: NOT_MODELED
- override: a mechanical ventilator would set the capacity (and RR) directly, bypassing the drive
- peep: NOT_MODELED
- status: FUTURE_RESPIRATORY_GENERALIZATION: none of these is a GI blocker; the recruitment mapping is the minimal abstraction for spontaneously breathing GI patients
- tidal_volume: an explicit tidal-volume / dead-space state would replace the recruitment term (capacity = minute ventilation x (1 - dead-space fraction) over the baseline)
<!-- /generado:semantica -->

## 3. Soportes, referencias y tolerancias congelados (generado)

<!-- generado:soportes -->
Predeclared before any count. RR side: P2K-2's frozen supports (intrinsic RR 12 / 16 / 20 per patient, drive gain 1 to 4 at ratio sqrt 2, common), S = 25. Acid side: B 13.4 / 19.4 / 28 x tau 60 / 120 / 240 (P2K-2), never forced to rise. Ventilation side: the faculty's common gain 0.03 / 0.04 / 0.05 / 0.06 / 0.08 per mEq/L, efficiency 1, PaCO2 reference 40, the baseline-relative demand. Arrival: RR within +/- 3 of the authored RR (P2K-2's analytic test), then the predicted PaCO2 40 / (1 + gain x A0) within the faculty's window per case; pH diagnostic only. Factorized: the burden per (B, tau) and deficit trajectory, RR per (drive gain, intrinsic RR), W / PaCO2 / pH per ventilation gain; no product of dimensions an output does not read.

- **Ganancia ácido → ventilación (común):** 0,03, 0,04, 0,05, 0,06, 0,08 por mEq/L (EXPLORATORY). Ganancias que reproducirían exactamente la PaCO2 de autor: 57m 0,0433; 72f 0,0505 (las de la docencia: 57m 0,043; 72f 0,050).
- **FR (de P2K-2, sin cambio):** FR intrínseca 12, 16, 20 rpm por paciente; ganancia de frecuencia 1,000, 1,414, 2,000, 2,828, 4,000; S = 25.
- **Carga ácida (de P2K-2, sin cambio):** B 13,4, 19,4, 28,0 mEq/L × τ 60, 120, 240 min; nunca se exige que suba.
- **Referencias:** HCO3 24 mEq/L y PaCO2 40 mmHg (COMMON_REFERENCE_PROVISIONAL); eficiencia ventilatoria 1 (STRUCTURAL_REFERENCE).
- **Tolerancias de llegada:** FR ± 3 rpm (26 y 24); PaCO2 ± 3 mmHg (57m 28–34 mmHg; 72f 30–36 mmHg); pH ± 0,03 sólo diagnóstico.
- **Lecturas diagnósticas congeladas (no filtran):** pH plausible 6,8–7,8; pregunta 3: FR a ≤ 3 rpm de la intrínseca y PaCO2 a ≤ 5 mmHg de 40.
<!-- /generado:soportes -->

## 4. La FR ya no determina W (generado)

<!-- generado:desacople -->
**Prueba estática** (lo que leen las funciones de W y las asignaciones de W en `ventilated_respiration`):

| función o asignación | nombres que lee |
|---|---|
| `effective_ventilation` | `capacity`, `demand_ratio`, `float` |
| `paco2_from_ventilation` | `float`, `reference`, `ventilation` |
| `return.capacity` | `capacity` |
| `return.demand_ratio` | `demand_ratio` |
| `return.efficiency` | `profile`, `ventilation_efficiency` |
| `return.paco2` | `paco2` |
| `return.paco2_reference` | `paco2_reference_mmhg`, `profile` |
| `return.ph` | `base`, `bicarbonate`, `carbonic_ph`, `paco2` |
| `return.recruitment` | `recruitment` |
| `return.ventilation` | `ventilation` |
| `ventilated_respiration.capacity` | `acid_burden`, `acid_to_ventilation_gain`, `base`, `candidate`, `profile`, `ventilation_efficiency`, `ventilatory_capacity` |
| `ventilated_respiration.demand_ratio` | `anchors`, `aux`, `metabolic_demand_baseline`, `oxygen_demand`, `state` |
| `ventilated_respiration.paco2` | `paco2_from_ventilation`, `paco2_reference_mmhg`, `profile`, `ventilation` |
| `ventilated_respiration.recruitment` | `acid_burden`, `acid_to_ventilation_gain`, `base`, `candidate`, `ventilation_recruitment` |
| `ventilated_respiration.ventilation` | `R`, `capacity`, `demand_ratio`, `effective_ventilation`, `pulse_present`, `state` |
| `ventilation_recruitment` | `burden`, `float`, `gain` |
| `ventilatory_capacity` | `burden`, `efficiency`, `float`, `gain`, `ventilation_recruitment` |

Nombres prohibidos encontrados: ninguno (prohibidos: la FR, la FR intrínseca, el impulso y sus parámetros, el lactato, D y el canal W).

**En el núcleo completo** (48 corridas con la candidata): recalculada sobre los mismos estados con otra ganancia de frecuencia, W, PaCO2 y pH idénticos: sí (la FR sí cambió: sí); con otra FR intrínseca, idénticos: sí; en orden inverso, idénticos: sí.
<!-- /generado:desacople -->

## 5. Sondas estructurales A–I (generado)

<!-- generado:sondas -->
Synthetic, structural only: P2K-2's neutral probe arrival (no deficit; HCO3 20, so A0 = 4; intrinsic RR 16) and probe profile (drive gain 2, B 19.4, tau 120, efficiency 1), ventilation gain 0.05. A: burden 4 -> 8. B: RR alone (drive gain 2 -> 4, and S 25 -> 15) at burden 8. C: intrinsic RR 12 / 16 / 20 at burden 8. D: ventilation gain 0.03 -> 0.08 at burden 8. E: lactate alone. F: D alone. G: efficiency 0.5 with a high RR (drive gain 4, burden 8), and a 20-minute course with efficiency 1 -> 0.5 while the burden rises 4 -> 10. H: burden 0 at the baseline demand, every intrinsic RR, drive gain and ventilation gain. I: demand ratio 1.25 at burden 8, and the burden whose recruitment compensates it. W channel: state W +/- 0.5. Not candidates, not clinical values.

Llegada de la sonda: carga 4,0, FR 22,8, W 1,20, PaCO2 33,3, pH 7,401.

| sonda | resultado | pasa |
|---|---|---|
| A · sube la carga 4 → 8 | FR 22,8 → 27,8; W 1,20 → 1,40; PaCO2 33,3 → 28,6 | sí |
| B · cambia sólo la FR (ganancia 2 → 4; S 25 → 15) | FR 27,8 → 34,0 y 25,8; W 1,40 y 1,40 | sí |
| C · cambia sólo la FR intrínseca (12 / 16 / 20) | FR 23,8 / 27,8 / 31,8; W 1,40 / 1,40 / 1,40; PaCO2 28,6 / 28,6 / 28,6 | sí |
| D · carga fija, ganancia de ventilación 0,03 → 0,08 | W 1,24 → 1,64; PaCO2 32,3 → 24,4; FR 27,8 = 27,8 | sí |
| E · cambia sólo el lactato | lactato 1,0 → 5,0; FR, W y PaCO2 sin cambio | sí |
| F · cambia sólo D | D 0 → 40; FR, W y PaCO2 sin cambio | sí |
| G · eficiencia 0,5 con FR alta | FR 34,0 (igual con eficiencia 1); W 1,40 → 0,70; PaCO2 28,6 → 57,1. Curso de 20 min (eficiencia 1 → 0,5, carga 4 → 10): FR 22,8 → 29,8, PaCO2 33,3 → 53,3 | sí |
| H · sin carga, demanda basal | 75 combinaciones (FR intrínseca × ganancia de frecuencia × ganancia de ventilación): W = 1 en todas: sí; PaCO2 = 40 en todas: sí; FR = intrínseca: sí | sí |
| I · demanda × 1,25 con la misma carga | W 1,40 → 1,12; PaCO2 28,6 → 35,7; FR sin cambio; la carga que compensa por reclutamiento: 15,0 mEq/L | sí |
| canal W ± 0,5 | FR, W y PaCO2 sin cambio | sí |
| sin pulso | FR 0, W 0, sin PaCO2 | sí |
<!-- /generado:sondas -->

## 6. Superficie de llegada: FR, PaCO2 y pH (generado)

<!-- generado:llegada -->
**FR (prueba analítica de P2K-2, ± 3):** 9 de 45 combinaciones (ganancia de frecuencia, FR intrínseca 57m, FR intrínseca 72f) compatibles: (1,000, 20, 20); (1,414, 16, 16); (1,414, 16, 20); (1,414, 20, 16); (1,414, 20, 20); (2,000, 16, 16); (2,828, 12, 12); (2,828, 12, 16); (4,000, 12, 12).

**PaCO2 (± 3) y pH diagnóstico (± 0,03) por ganancia común de ventilación:**

| ganancia | reclutamiento 57m | PaCO2 57m | pH 57m (error) | reclutamiento 72f | PaCO2 72f | pH 72f (error) | compatible |
|---|---|---|---|---|---|---|---|
| 0,03 | 1,201 | 33,3 (2,3) | 7,338 (−0,032, PH_INCONSISTENT) | 1,126 | 35,5 (2,5) | 7,369 (−0,031, PH_INCONSISTENT) | sí |
| 0,04 | 1,268 | 31,5 (0,5) | 7,362 (−0,008, PH_CONSISTENT) | 1,168 | 34,2 (1,2) | 7,385 (−0,015, PH_CONSISTENT) | sí |
| 0,05 | 1,335 | 30,0 (−1,0) | 7,384 (0,014, PH_CONSISTENT) | 1,210 | 33,1 (0,1) | 7,400 (0,000, PH_CONSISTENT) | sí |
| 0,06 | 1,402 | 28,5 (−2,5) | 7,406 (0,036, PH_INCONSISTENT) | 1,252 | 31,9 (−1,1) | 7,415 (0,015, PH_CONSISTENT) | sí |
| 0,08 | 1,536 | 26,0 (−5,0) | 7,445 (0,075, PH_INCONSISTENT) | 1,336 | 29,9 (−3,1) | 7,443 (0,043, PH_INCONSISTENT) | no |

Entre paréntesis, la diferencia con la PaCO2 de autor (31 y 33) y con el pH de autor (7,37 y 7,40). El pH no filtra: contaría dos veces el mismo HCO3 y la misma PaCO2.

**Superficie conjunta de llegada (FR, luego PaCO2):**

| | lo que lee la llegada | con el soporte ácido (× 9 pares B/τ) |
|---|---|---|
| total | 225 | 2025 |
| compatibles por FR | 45 | 405 |
| compatibles por PaCO2 | 180 | 1620 |
| compatibles en conjunto | **36** | **324** |

Soporte entre los compatibles en conjunto (sin elegir una combinación):

- **FR intrínseca 57m:** 12 (12), 16 (12), 20 (12).
- **FR intrínseca 72f:** 12 (8), 16 (16), 20 (12).
- **ganancia de frecuencia:** 1 (4), 1,414 (16), 2 (4), 2,828 (8), 4 (4).
- **ganancia de ventilación:** 0,03 (9), 0,04 (9), 0,05 (9), 0,06 (9), 0,08 (0).
- **B:** 13,4 (108), 19,4 (108), 28 (108).
- **τ:** 60 (108), 120 (108), 240 (108).
- B y τ: la llegada no los lee (la carga de llegada es la del HCO3 de autor); cada par se lleva con cada candidato compatible en conjunto.

Rechazos analíticos en la llegada: 0. Sensibilidad a la semántica de la demanda (índice absoluto, no usado): con la demanda 1,1 serían compatibles las ganancias 0,06, 0,08; con 1,0, 0,03, 0,04, 0,05, 0,06.
<!-- /generado:llegada -->

## 7. Escenarios clínicos R1–R4 (generado)

<!-- generado:reconstruccion -->
The P2J-3 region recomputed with P2J-3's own functions and the deficit, D and lactate of every unique (scenario, blood set, lactate-side point) rebuilt as P2K-1 / P2K-2 did (acid_base.reconstruct). The burden per (B, tau) is the core's acid_burden_after_minute (acid_base.burden_series); RR is the core's algebra per (drive gain, intrinsic RR); W, PaCO2 and pH the ventilation module's algebra per ventilation gain at efficiency 1 and the baseline demand. Each observable is read over the factors it depends on only (RR never multiplied by the ventilation gain, W never by the drive gain or intrinsic RR). Validated against full core runs with the candidate declared (every upstream row equal to the run without it).

Mediana [rango] a la ganancia de tono intermedia g = 0,5. La FR y su parte de impulso se leen sobre (trayectoria, B/τ, ganancia de frecuencia, FR intrínseca); el reclutamiento, W, la PaCO2 y el pH sobre (trayectoria, B/τ, ganancia de ventilación); la carga y el HCO3 sobre (trayectoria, B/τ). Eficiencia ventilatoria 1 y razón de demanda 1 en todas. Las otras ganancias de tono están en el JSON.

**R1 · hemorragia sin tratamiento (L1) · 57m · demanda 1** (18 trayectorias; FR intrínseca 12, 16, 20; ganancia de frecuencia 1,00, 1,41, 2,00, 2,83, 4,00; ganancia de ventilación 0,03, 0,04, 0,05, 0,06; eficiencia 1)

| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | demanda | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 26,1 [23,9–28,4] | 9,1 [5,9–16,4] | 6,7 | 17,3 | 1,301 [1,201–1,402] | 1,30 [1,20–1,40] | 30,8 [28,5–33,3] | 7,37 [7,34–7,41] | 4,4 | 60 | 0,40 | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 15 | 26,3 [23,6–29,9] | 9,5 [5,7–17,9] | 6,9 [6,4–7,8] | 17,1 [16,2–17,6] | 1,318 [1,193–1,470] | 1,32 [1,19–1,47] | 30,4 [27,2–33,5] | 7,37 [7,32–7,41] | 4,7 | 73 | 0,44 [0,43–0,44] | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 30 | 26,7 [23,5–31,0] | 9,9 [5,6–19,0] | 7,1 [6,3–9,0] | 16,9 [15,0–17,7] | 1,322 [1,190–1,537] | 1,32 [1,19–1,54] | 30,3 [26,0–33,6] | 7,36 [7,30–7,41] | 5,0 | 86 [86–86] | 0,48 [0,46–0,48] | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 60 | 27,6 [23,6–32,9] | 10,3 [5,7–20,9] | 7,8 [6,4–11,2] | 16,2 [12,8–17,6] | 1,337 [1,193–1,674] | 1,34 [1,19–1,67] | 29,9 [23,9–33,5] | 7,36 [7,25–7,41] | 6,1 | 118 [115–118] | 0,56 [0,52–0,56] | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 90 | 28,1 [23,9–34,1] | 11,6 [5,9–22,1] | 8,6 [6,7–13,5] | 15,4 [10,5–17,3] | 1,388 [1,200–1,812] | 1,39 [1,20–1,81] | 28,8 [22,1–33,3] | 7,35 [7,19–7,41] | 7,5 [7,4–7,5] | 153 [148–154] | 0,64 [0,57–0,65] | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 120 | 29,0 [24,0–35,0] | 12,3 [6,0–23,0] | 9,6 [6,8–15,8] | 14,4 [8,2–17,2] | 1,420 [1,205–1,950] | 1,42 [1,21–1,95] | 28,2 [20,5–33,2] | 7,33 [7,10–7,40] | 9,4 [9,2–9,4] | 194 [184–195] | 0,72 [0,63–0,73] | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |

**R1 · hemorragia sin tratamiento (L1) · 72f · demanda 1** (18 trayectorias; FR intrínseca 12, 16, 20; ganancia de frecuencia 1,00, 1,41, 2,00, 2,83, 4,00; ganancia de ventilación 0,03, 0,04, 0,05, 0,06; eficiencia 1)

| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | demanda | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 23,9 [21,3–25,5] | 7,1 [3,9–12,2] | 4,2 | 19,8 | 1,189 [1,126–1,252] | 1,19 [1,13–1,25] | 33,7 [31,9–35,5] | 7,39 [7,37–7,42] | 3,4 | 20 | 0,15 | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 15 | 23,8 [20,7–25,7] | 7,0 [3,5–12,5] | 4,1 [3,8–4,3] | 19,9 [19,7–20,2] | 1,180 [1,113–1,259] | 1,18 [1,11–1,26] | 33,9 [31,8–36,0] | 7,39 [7,37–7,42] | 3,3 | 25 | 0,19 [0,18–0,19] | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 30 | 23,7 [20,2–26,3] | 7,0 [3,3–13,2] | 4,1 [3,5–4,7] | 19,9 [19,3–20,5] | 1,180 [1,105–1,280] | 1,18 [1,10–1,28] | 33,9 [31,2–36,2] | 7,39 [7,36–7,42] | 3,3 | 31 [31–31] | 0,23 [0,21–0,23] | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 60 | 23,9 [19,9–28,1] | 7,3 [3,2–15,2] | 4,3 [3,4–5,9] | 19,7 [18,1–20,6] | 1,192 [1,101–1,352] | 1,19 [1,10–1,35] | 33,6 [29,6–36,3] | 7,39 [7,35–7,42] | 3,5 | 47 [45–48] | 0,31 [0,27–0,31] | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 90 | 24,6 [20,4–30,3] | 8,4 [3,4–17,5] | 4,8 [3,6–7,5] | 19,2 [16,5–20,4] | 1,217 [1,108–1,451] | 1,22 [1,11–1,45] | 32,9 [27,6–36,1] | 7,39 [7,33–7,42] | 4,0 [3,9–4,0] | 68 [62–69] | 0,39 [0,32–0,40] | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 120 | 25,4 [21,0–32,4] | 9,1 [3,6–19,5] | 5,6 [3,9–9,4] | 18,4 [14,6–20,1] | 1,244 [1,118–1,565] | 1,24 [1,12–1,57] | 32,1 [25,6–35,8] | 7,38 [7,29–7,42] | 4,9 [4,6–4,9] | 94 [83–95] | 0,47 [0,38–0,48] | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |

**R2 · cristaloide (L2) · 57m · demanda 1** (181 trayectorias; FR intrínseca 12, 16, 20; ganancia de frecuencia 1,00, 1,41, 2,00, 2,83, 4,00; ganancia de ventilación 0,03, 0,04, 0,05, 0,06; eficiencia 1)

| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | demanda | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 26,1 [23,9–28,4] | 9,1 [5,9–16,4] | 6,7 | 17,3 | 1,301 [1,201–1,402] | 1,30 [1,20–1,40] | 30,8 [28,5–33,3] | 7,37 [7,34–7,41] | 4,4 | 60 | 0,40 | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/181 |
| 15 | 26,1 [23,3–29,2] | 9,1 [5,4–17,2] | 6,6 [6,1–7,3] | 17,4 [16,7–17,9] | 1,299 [1,184–1,438] | 1,30 [1,18–1,44] | 30,8 [27,8–33,8] | 7,37 [7,33–7,41] | 4,6 | 70 [69–70] | 0,25 [0,23–0,28] | 1,00 | cristaloide 300 mL; GR 0,0 U; hemostasia 0/181 |
| 30 | 25,9 [22,6–29,3] | 8,6 [4,9–17,3] | 6,4 [5,4–7,3] | 17,6 [16,7–18,6] | 1,279 [1,162–1,441] | 1,28 [1,16–1,44] | 31,3 [27,8–34,4] | 7,38 [7,33–7,41] | 4,9 | 77 [76–78] | 0,25 [0,22–0,29] | 1,00 | cristaloide 400 mL; GR 0,0 U; hemostasia 0/181 |
| 60 | 25,7 [21,8–30,2] | 8,6 [4,3–18,2] | 6,2 [4,7–8,1] | 17,8 [15,9–19,3] | 1,283 [1,140–1,488] | 1,28 [1,14–1,49] | 31,2 [26,9–35,1] | 7,38 [7,32–7,41] | 5,7 [5,6–5,7] | 94 [91–98] | 0,32 [0,30–0,38] | 1,00 | cristaloide 400 mL; GR 0,0 U; hemostasia 0/181 |
| 90 | 26,1 [21,8–31,6] | 9,3 [4,2–19,6] | 6,5 [4,7–9,6] | 17,5 [14,4–19,3] | 1,292 [1,140–1,574] | 1,29 [1,14–1,57] | 31,0 [25,4–35,1] | 7,37 [7,29–7,41] | 6,6 [6,5–6,8] | 115 [112–123] | 0,41 [0,37–0,48] | 1,00 | cristaloide 400 mL; GR 0,0 U; hemostasia 0/181 |
| 120 | 26,7 [22,1–33,1] | 9,8 [4,5–21,1] | 6,9 [5,0–11,6] | 17,1 [12,4–19,0] | 1,312 [1,150–1,695] | 1,31 [1,15–1,69] | 30,5 [23,6–34,8] | 7,37 [7,24–7,41] | 7,8 [7,7–8,1] | 142 [137–153] | 0,49 [0,44–0,57] | 1,00 | cristaloide 400 mL; GR 0,0 U; hemostasia 0/181 |

**R2 · cristaloide (L2) · 72f · demanda 1** (181 trayectorias; FR intrínseca 12, 16, 20; ganancia de frecuencia 1,00, 1,41, 2,00, 2,83, 4,00; ganancia de ventilación 0,03, 0,04, 0,05, 0,06; eficiencia 1)

| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | demanda | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 23,9 [21,3–25,5] | 7,1 [3,9–12,2] | 4,2 | 19,8 | 1,189 [1,126–1,252] | 1,19 [1,13–1,25] | 33,7 [31,9–35,5] | 7,39 [7,37–7,42] | 3,4 | 20 | 0,15 | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/181 |
| 15 | 23,4 [20,1–25,3] | 6,7 [3,2–12,1] | 3,9 [3,5–4,1] | 20,1 [19,9–20,5] | 1,169 [1,104–1,247] | 1,17 [1,10–1,25] | 34,2 [32,1–36,2] | 7,40 [7,37–7,42] | 3,3 | 23 [22–23] | 0,03 [0,01–0,05] | 1,00 | cristaloide 300 mL; GR 0,0 U; hemostasia 0/181 |
| 30 | 22,6 [18,6–25,0] | 6,1 [2,6–11,7] | 3,5 [2,7–3,9] | 20,5 [20,1–21,3] | 1,152 [1,081–1,237] | 1,15 [1,08–1,24] | 34,7 [32,3–37,0] | 7,40 [7,37–7,42] | 3,3 [3,2–3,3] | 23 [15–24] | 0,03 [0,00–0,06] | 1,00 | cristaloide 400 mL; GR 0,0 U; hemostasia 0/181 |
| 60 | 21,9 [16,7–24,9] | 5,1 [1,8–11,4] | 3,0 [1,8–3,8] | 21,0 [20,2–22,2] | 1,128 [1,055–1,229] | 1,13 [1,06–1,23] | 35,4 [32,5–37,9] | 7,40 [7,37–7,42] | 3,2 [3,0–3,2] | 27 [18–30] | 0,10 [0,08–0,14] | 1,00 | cristaloide 400 mL; GR 0,0 U; hemostasia 0/181 |
| 90 | 22,0 [16,5–25,1] | 5,1 [1,7–11,8] | 3,1 [1,7–4,0] | 20,9 [20,0–22,3] | 1,132 [1,052–1,240] | 1,13 [1,05–1,24] | 35,3 [32,3–38,0] | 7,40 [7,37–7,42] | 3,3 [2,9–3,4] | 35 [25–41] | 0,18 [0,14–0,24] | 1,00 | cristaloide 400 mL; GR 0,0 U; hemostasia 0/181 |
| 120 | 22,6 [17,0–27,8] | 5,8 [1,9–14,9] | 3,4 [2,0–5,7] | 20,6 [18,3–22,0] | 1,150 [1,060–1,339] | 1,15 [1,06–1,34] | 34,8 [29,9–37,7] | 7,40 [7,35–7,42] | 3,5 [3,0–3,8] | 48 [37–58] | 0,26 [0,21–0,34] | 1,00 | cristaloide 400 mL; GR 0,0 U; hemostasia 0/181 |

**R3 · GR sin hemostasia · 57m · demanda 1** (18 trayectorias; FR intrínseca 12, 16, 20; ganancia de frecuencia 1,00, 1,41, 2,00, 2,83, 4,00; ganancia de ventilación 0,03, 0,04, 0,05, 0,06; eficiencia 1)

| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | demanda | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 26,1 [23,9–28,4] | 9,1 [5,9–16,4] | 6,7 | 17,3 | 1,301 [1,201–1,402] | 1,30 [1,20–1,40] | 30,8 [28,5–33,3] | 7,37 [7,34–7,41] | 4,4 | 60 | 0,40 | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 15 | 26,0 [23,3–29,1] | 9,0 [5,4–17,1] | 6,6 [6,1–7,2] | 17,4 [16,8–17,9] | 1,297 [1,184–1,431] | 1,30 [1,18–1,43] | 30,8 [27,9–33,8] | 7,37 [7,33–7,41] | 4,6 | 69 | 0,22 [0,22–0,23] | 1,00 | cristaloide 0 mL; GR 0,5 U; hemostasia 0/18 |
| 30 | 25,7 [22,3–28,4] | 8,1 [4,6–16,4] | 6,3 [5,1–6,7] | 17,7 [17,3–18,9] | 1,265 [1,154–1,400] | 1,26 [1,15–1,40] | 31,6 [28,6–34,7] | 7,38 [7,34–7,41] | 4,9 | 73 [73–74] | 0,03 [0,03–0,04] | 1,00 | cristaloide 0 mL; GR 1,0 U; hemostasia 0/18 |
| 60 | 23,9 [19,4–27,3] | 6,9 [2,9–15,3] | 4,8 [3,1–5,9] | 19,2 [18,1–20,9] | 1,200 [1,093–1,353] | 1,20 [1,09–1,35] | 33,3 [29,6–36,6] | 7,39 [7,35–7,42] | 5,0 | 30 [29–31] | 0,00 | 1,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/18 |
| 90 | 22,6 [16,8–26,4] | 6,0 [1,8–14,1] | 3,7 [1,9–5,2] | 20,3 [18,8–22,1] | 1,150 [1,056–1,312] | 1,15 [1,06–1,31] | 34,8 [30,5–37,9] | 7,40 [7,36–7,42] | 4,4 | 11 | 0,00 | 1,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/18 |
| 120 | 21,5 [15,0–25,7] | 4,2 [1,1–13,0] | 2,9 [1,1–4,6] | 21,1 [19,4–22,9] | 1,127 [1,034–1,275] | 1,13 [1,03–1,27] | 35,5 [31,4–38,7] | 7,40 [7,36–7,42] | 3,8 | 4 | 0,00 | 1,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/18 |

**R3 · GR sin hemostasia · 72f · demanda 1** (18 trayectorias; FR intrínseca 12, 16, 20; ganancia de frecuencia 1,00, 1,41, 2,00, 2,83, 4,00; ganancia de ventilación 0,03, 0,04, 0,05, 0,06; eficiencia 1)

| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | demanda | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 23,9 [21,3–25,5] | 7,1 [3,9–12,2] | 4,2 | 19,8 | 1,189 [1,126–1,252] | 1,19 [1,13–1,25] | 33,7 [31,9–35,5] | 7,39 [7,37–7,42] | 3,4 | 20 | 0,15 | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 15 | 23,3 [20,0–25,2] | 6,6 [3,2–11,9] | 3,8 [3,4–4,1] | 20,2 [19,9–20,6] | 1,167 [1,103–1,243] | 1,17 [1,10–1,24] | 34,3 [32,2–36,3] | 7,40 [7,37–7,42] | 3,3 | 19 [19–20] | 0,00 | 1,00 | cristaloide 0 mL; GR 0,5 U; hemostasia 0/18 |
| 30 | 22,5 [18,5–24,8] | 5,9 [2,5–11,4] | 3,4 [2,7–3,8] | 20,6 [20,2–21,3] | 1,146 [1,080–1,228] | 1,15 [1,08–1,23] | 34,9 [32,6–37,0] | 7,40 [7,37–7,42] | 3,2 | 11 | 0,00 | 1,00 | cristaloide 0 mL; GR 1,0 U; hemostasia 0/18 |
| 60 | 20,7 [16,2–24,3] | 4,3 [1,6–10,4] | 2,6 [1,6–3,4] | 21,4 [20,6–22,4] | 1,103 [1,048–1,201] | 1,10 [1,05–1,20] | 36,3 [33,3–38,2] | 7,40 [7,38–7,42] | 2,8 | 4 | 0,00 | 1,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/18 |
| 90 | 19,8 [14,6–23,9] | 3,7 [1,0–9,4] | 2,0 [1,0–3,0] | 22,0 [21,0–23,0] | 1,085 [1,029–1,178] | 1,09 [1,03–1,18] | 36,9 [34,0–38,9] | 7,40 [7,38–7,41] | 2,4 | 1 | 0,00 | 1,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/18 |
| 120 | 19,4 [13,6–23,4] | 2,5 [0,6–8,5] | 1,6 [0,6–2,6] | 22,4 [21,4–23,4] | 1,071 [1,018–1,157] | 1,07 [1,02–1,16] | 37,3 [34,6–39,3] | 7,40 [7,38–7,41] | 2,1 | 1 | 0,00 | 1,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/18 |

**R4 · manejo definitivo (L3) · 57m · demanda 1** (18 trayectorias; FR intrínseca 12, 16, 20; ganancia de frecuencia 1,00, 1,41, 2,00, 2,83, 4,00; ganancia de ventilación 0,03, 0,04, 0,05, 0,06; eficiencia 1)

| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | demanda | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 26,1 [23,9–28,4] | 9,1 [5,9–16,4] | 6,7 | 17,3 | 1,301 [1,201–1,402] | 1,30 [1,20–1,40] | 30,8 [28,5–33,3] | 7,37 [7,34–7,41] | 4,4 | 60 | 0,40 | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 15 | 26,0 [23,3–29,1] | 9,0 [5,4–17,1] | 6,6 [6,1–7,2] | 17,4 [16,8–17,9] | 1,297 [1,184–1,431] | 1,30 [1,18–1,43] | 30,8 [27,9–33,8] | 7,37 [7,33–7,41] | 4,6 | 69 | 0,22 [0,22–0,23] | 1,00 | cristaloide 0 mL; GR 0,5 U; hemostasia 0/18 |
| 30 | 25,7 [22,3–28,4] | 8,1 [4,6–16,4] | 6,3 [5,1–6,7] | 17,7 [17,3–18,9] | 1,265 [1,154–1,400] | 1,26 [1,15–1,40] | 31,6 [28,6–34,7] | 7,38 [7,34–7,41] | 4,9 | 73 [73–74] | 0,03 [0,03–0,04] | 1,00 | cristaloide 0 mL; GR 1,0 U; hemostasia 0/18 |
| 60 | 23,9 [19,4–27,3] | 6,9 [2,9–15,3] | 4,8 [3,1–5,9] | 19,2 [18,1–20,9] | 1,200 [1,093–1,353] | 1,20 [1,09–1,35] | 33,3 [29,6–36,6] | 7,39 [7,35–7,42] | 5,0 | 30 [29–31] | 0,00 | 1,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 18/18 |
| 90 | 22,6 [16,8–26,4] | 6,0 [1,8–14,1] | 3,7 [1,9–5,2] | 20,3 [18,8–22,1] | 1,150 [1,056–1,312] | 1,15 [1,06–1,31] | 34,8 [30,5–37,9] | 7,40 [7,36–7,42] | 4,4 | 11 | 0,00 | 1,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 18/18 |
| 120 | 21,5 [15,0–25,7] | 4,2 [1,1–13,0] | 2,9 [1,1–4,6] | 21,1 [19,4–22,9] | 1,127 [1,034–1,275] | 1,13 [1,03–1,27] | 35,5 [31,4–38,7] | 7,40 [7,36–7,42] | 3,8 | 4 | 0,00 | 1,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 18/18 |

**R4 · manejo definitivo (L3) · 72f · demanda 1** (18 trayectorias; FR intrínseca 12, 16, 20; ganancia de frecuencia 1,00, 1,41, 2,00, 2,83, 4,00; ganancia de ventilación 0,03, 0,04, 0,05, 0,06; eficiencia 1)

| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | demanda | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 23,9 [21,3–25,5] | 7,1 [3,9–12,2] | 4,2 | 19,8 | 1,189 [1,126–1,252] | 1,19 [1,13–1,25] | 33,7 [31,9–35,5] | 7,39 [7,37–7,42] | 3,4 | 20 | 0,15 | 1,00 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 15 | 23,3 [20,0–25,2] | 6,6 [3,2–11,9] | 3,8 [3,4–4,1] | 20,2 [19,9–20,6] | 1,167 [1,103–1,243] | 1,17 [1,10–1,24] | 34,3 [32,2–36,3] | 7,40 [7,37–7,42] | 3,3 | 19 [19–20] | 0,00 | 1,00 | cristaloide 0 mL; GR 0,5 U; hemostasia 0/18 |
| 30 | 22,5 [18,5–24,8] | 5,9 [2,5–11,4] | 3,4 [2,7–3,8] | 20,6 [20,2–21,3] | 1,146 [1,080–1,228] | 1,15 [1,08–1,23] | 34,9 [32,6–37,0] | 7,40 [7,37–7,42] | 3,2 | 11 | 0,00 | 1,00 | cristaloide 0 mL; GR 1,0 U; hemostasia 0/18 |
| 60 | 20,7 [16,2–24,3] | 4,3 [1,6–10,4] | 2,6 [1,6–3,4] | 21,4 [20,6–22,4] | 1,103 [1,048–1,201] | 1,10 [1,05–1,20] | 36,3 [33,3–38,2] | 7,40 [7,38–7,42] | 2,8 | 4 | 0,00 | 1,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 18/18 |
| 90 | 19,8 [14,6–23,9] | 3,7 [1,0–9,4] | 2,0 [1,0–3,0] | 22,0 [21,0–23,0] | 1,085 [1,029–1,178] | 1,09 [1,03–1,18] | 36,9 [34,0–38,9] | 7,40 [7,38–7,41] | 2,4 | 1 | 0,00 | 1,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 18/18 |
| 120 | 19,4 [13,6–23,4] | 2,5 [0,6–8,5] | 1,6 [0,6–2,6] | 22,4 [21,4–23,4] | 1,071 [1,018–1,157] | 1,07 [1,02–1,16] | 37,3 [34,6–39,3] | 7,40 [7,38–7,41] | 2,1 | 1 | 0,00 | 1,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 18/18 |

**R1 · hemorragia sin tratamiento (L1) · 57m · demanda 1,1** (37 trayectorias; FR intrínseca 12, 16, 20; ganancia de frecuencia 1,00, 1,41, 2,00, 2,83, 4,00; ganancia de ventilación 0,03, 0,04, 0,05, 0,06; eficiencia 1)

| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | demanda | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 26,1 [23,9–28,4] | 9,1 [5,9–16,4] | 6,7 | 17,3 | 1,301 [1,201–1,402] | 1,30 [1,20–1,40] | 30,8 [28,5–33,3] | 7,37 [7,34–7,41] | 4,4 | 60 | 0,50 | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 15 | 26,5 [23,9–30,5] | 9,9 [5,9–18,5] | 7,1 [6,7–8,4] | 16,9 [15,6–17,3] | 1,336 [1,201–1,507] | 1,34 [1,20–1,51] | 29,9 [26,5–33,3] | 7,36 [7,31–7,41] | 5,2 | 64 | 0,54 [0,53–0,54] | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 30 | 27,2 [23,9–32,0] | 10,5 [5,9–20,0] | 7,5 [6,7–10,1] | 16,5 [13,9–17,3] | 1,341 [1,202–1,604] | 1,34 [1,20–1,60] | 29,8 [24,9–33,3] | 7,36 [7,28–7,41] | 5,8 | 68 | 0,58 [0,56–0,58] | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 60 | 28,3 [24,1–33,9] | 11,2 [6,0–21,9] | 8,5 [6,9–13,0] | 15,5 [11,0–17,1] | 1,381 [1,206–1,780] | 1,38 [1,21–1,78] | 29,0 [22,5–33,2] | 7,35 [7,21–7,40] | 6,9 | 77 [77–77] | 0,65 [0,61–0,66] | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 90 | 29,0 [24,2–35,0] | 12,3 [6,2–23,0] | 9,6 [7,1–15,7] | 14,4 [8,3–16,9] | 1,423 [1,212–1,942] | 1,42 [1,21–1,94] | 28,1 [20,6–33,0] | 7,33 [7,11–7,40] | 8,0 [7,9–8,0] | 87 [86–88] | 0,73 [0,67–0,75] | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 120 | 29,8 [24,5–36,1] | 13,2 [6,4–23,6] | 10,8 [7,3–18,2] | 13,2 [5,8–16,7] | 1,458 [1,220–2,094] | 1,46 [1,22–2,09] | 27,4 [19,1–32,8] | 7,32 [6,97–7,40] | 9,0 [8,9–9,1] | 99 [97–100] | 0,82 [0,73–0,83] | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |

**R1 · hemorragia sin tratamiento (L1) · 72f · demanda 1,1** (37 trayectorias; FR intrínseca 12, 16, 20; ganancia de frecuencia 1,00, 1,41, 2,00, 2,83, 4,00; ganancia de ventilación 0,03, 0,04, 0,05, 0,06; eficiencia 1)

| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | demanda | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 23,9 [21,3–25,5] | 7,1 [3,9–12,2] | 4,2 | 19,8 | 1,189 [1,126–1,252] | 1,19 [1,13–1,25] | 33,7 [31,9–35,5] | 7,39 [7,37–7,42] | 3,4 | 20 | 0,25 | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 15 | 24,0 [21,1–26,7] | 7,3 [3,7–13,7] | 4,3 [4,1–4,9] | 19,7 [19,1–19,9] | 1,200 [1,122–1,297] | 1,20 [1,12–1,30] | 33,3 [30,8–35,7] | 7,39 [7,36–7,42] | 3,3 | 22 | 0,29 [0,28–0,29] | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 30 | 24,1 [21,1–28,0] | 7,6 [3,7–15,1] | 4,5 [4,0–5,8] | 19,5 [18,2–20,0] | 1,205 [1,121–1,346] | 1,20 [1,12–1,35] | 33,2 [29,7–35,7] | 7,39 [7,35–7,42] | 3,3 | 24 | 0,33 [0,31–0,33] | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 60 | 24,8 [21,3–30,4] | 8,6 [3,8–17,6] | 5,1 [4,2–7,6] | 18,9 [16,4–19,8] | 1,226 [1,125–1,457] | 1,23 [1,13–1,46] | 32,6 [27,4–35,5] | 7,38 [7,32–7,42] | 3,5 | 30 [29–30] | 0,40 [0,36–0,41] | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 90 | 25,7 [21,4–32,6] | 9,7 [4,0–19,7] | 5,8 [4,3–9,7] | 18,2 [14,3–19,7] | 1,257 [1,129–1,579] | 1,26 [1,13–1,58] | 31,8 [25,3–35,4] | 7,38 [7,29–7,41] | 3,8 [3,8–3,9] | 36 [35–37] | 0,48 [0,42–0,49] | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 120 | 26,4 [21,6–34,4] | 10,4 [4,1–21,2] | 6,6 [4,5–11,8] | 17,4 [12,2–19,5] | 1,287 [1,135–1,708] | 1,29 [1,13–1,71] | 31,1 [23,4–35,2] | 7,37 [7,24–7,41] | 4,4 [4,3–4,4] | 44 [42–45] | 0,56 [0,47–0,58] | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |

**R2 · cristaloide (L2) · 57m · demanda 1,1** (444 trayectorias; FR intrínseca 12, 16, 20; ganancia de frecuencia 1,00, 1,41, 2,00, 2,83, 4,00; ganancia de ventilación 0,03, 0,04, 0,05, 0,06; eficiencia 1)

| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | demanda | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 26,1 [23,9–28,4] | 9,1 [5,9–16,4] | 6,7 | 17,3 | 1,301 [1,201–1,402] | 1,30 [1,20–1,40] | 30,8 [28,5–33,3] | 7,37 [7,34–7,41] | 4,4 | 60 | 0,50 | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/444 |
| 15 | 26,3 [23,6–30,0] | 9,6 [5,7–18,0] | 6,9 [6,4–8,0] | 17,1 [16,0–17,6] | 1,320 [1,192–1,479] | 1,32 [1,19–1,48] | 30,3 [27,0–33,5] | 7,37 [7,32–7,41] | 5,1 | 63 | 0,36 [0,32–0,40] | 1,10 | cristaloide 300 mL; GR 0,0 U; hemostasia 0/444 |
| 30 | 26,4 [23,1–30,7] | 9,5 [5,2–18,7] | 6,8 [5,9–8,6] | 17,2 [15,4–18,1] | 1,312 [1,176–1,517] | 1,31 [1,18–1,52] | 30,5 [26,4–34,0] | 7,37 [7,31–7,41] | 5,8 | 66 [65–66] | 0,35 [0,30–0,41] | 1,10 | cristaloide 400 mL; GR 0,0 U; hemostasia 0/444 |
| 60 | 26,6 [22,5–32,1] | 9,8 [4,8–20,1] | 7,0 [5,4–10,2] | 17,0 [13,8–18,6] | 1,313 [1,161–1,611] | 1,31 [1,16–1,61] | 30,5 [24,8–34,5] | 7,37 [7,28–7,41] | 6,7 [6,7–6,8] | 72 [70–73] | 0,42 [0,37–0,49] | 1,10 | cristaloide 400 mL; GR 0,0 U; hemostasia 0/444 |
| 90 | 27,2 [22,6–33,3] | 10,3 [4,9–21,3] | 7,4 [5,4–12,0] | 16,6 [12,0–18,6] | 1,330 [1,163–1,721] | 1,33 [1,16–1,72] | 30,1 [23,2–34,4] | 7,36 [7,23–7,41] | 7,5 [7,4–7,6] | 79 [77–81] | 0,50 [0,45–0,58] | 1,10 | cristaloide 400 mL; GR 0,0 U; hemostasia 0/444 |
| 120 | 27,8 [23,1–34,3] | 11,2 [5,3–22,3] | 8,1 [5,9–14,0] | 15,9 [10,0–18,1] | 1,366 [1,178–1,840] | 1,37 [1,18–1,84] | 29,3 [21,7–34,0] | 7,35 [7,17–7,41] | 8,3 [8,1–8,5] | 87 [84–90] | 0,57 [0,54–0,67] | 1,10 | cristaloide 400 mL; GR 0,0 U; hemostasia 0/444 |

**R2 · cristaloide (L2) · 72f · demanda 1,1** (444 trayectorias; FR intrínseca 12, 16, 20; ganancia de frecuencia 1,00, 1,41, 2,00, 2,83, 4,00; ganancia de ventilación 0,03, 0,04, 0,05, 0,06; eficiencia 1)

| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | demanda | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 23,9 [21,3–25,5] | 7,1 [3,9–12,2] | 4,2 | 19,8 | 1,189 [1,126–1,252] | 1,19 [1,13–1,25] | 33,7 [31,9–35,5] | 7,39 [7,37–7,42] | 3,4 | 20 | 0,25 | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/444 |
| 15 | 23,8 [20,7–26,1] | 7,0 [3,5–13,0] | 4,1 [3,8–4,6] | 19,9 [19,4–20,2] | 1,185 [1,113–1,274] | 1,19 [1,11–1,27] | 33,7 [31,4–35,9] | 7,39 [7,37–7,42] | 3,3 | 21 | 0,14 [0,09–0,18] | 1,10 | cristaloide 300 mL; GR 0,0 U; hemostasia 0/444 |
| 30 | 23,4 [19,5–26,2] | 6,8 [2,9–13,1] | 4,0 [3,1–4,6] | 20,0 [19,4–20,9] | 1,171 [1,094–1,278] | 1,17 [1,09–1,28] | 34,2 [31,3–36,6] | 7,39 [7,36–7,42] | 3,2 | 22 [22–23] | 0,13 [0,08–0,19] | 1,10 | cristaloide 400 mL; GR 0,0 U; hemostasia 0/444 |
| 60 | 23,2 [18,2–27,3] | 6,5 [2,4–14,3] | 3,8 [2,5–5,3] | 20,2 [18,7–21,5] | 1,167 [1,075–1,318] | 1,17 [1,08–1,32] | 34,3 [30,3–37,2] | 7,39 [7,36–7,42] | 3,3 [3,2–3,3] | 25 [23–26] | 0,20 [0,15–0,26] | 1,10 | cristaloide 400 mL; GR 0,0 U; hemostasia 0/444 |
| 90 | 23,4 [18,1–29,0] | 6,8 [2,4–16,2] | 4,0 [2,5–6,5] | 20,0 [17,5–21,5] | 1,177 [1,075–1,391] | 1,18 [1,07–1,39] | 34,0 [28,8–37,2] | 7,39 [7,34–7,42] | 3,4 [3,3–3,5] | 28 [26–31] | 0,27 [0,22–0,34] | 1,10 | cristaloide 400 mL; GR 0,0 U; hemostasia 0/444 |
| 120 | 24,1 [19,0–31,0] | 7,7 [2,8–18,1] | 4,4 [2,9–8,1] | 19,6 [15,9–21,1] | 1,198 [1,087–1,484] | 1,20 [1,09–1,48] | 33,4 [27,0–36,8] | 7,39 [7,32–7,42] | 3,7 [3,5–3,9] | 33 [30–36] | 0,34 [0,30–0,43] | 1,10 | cristaloide 400 mL; GR 0,0 U; hemostasia 0/444 |

**R3 · GR sin hemostasia · 57m · demanda 1,1** (91 trayectorias; FR intrínseca 12, 16, 20; ganancia de frecuencia 1,00, 1,41, 2,00, 2,83, 4,00; ganancia de ventilación 0,03, 0,04, 0,05, 0,06; eficiencia 1)

| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | demanda | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 26,1 [23,9–28,4] | 9,1 [5,9–16,4] | 6,7 | 17,3 | 1,301 [1,201–1,402] | 1,30 [1,20–1,40] | 30,8 [28,5–33,3] | 7,37 [7,34–7,41] | 4,4 | 60 | 0,50 | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/91 |
| 15 | 26,3 [23,6–29,9] | 9,5 [5,7–17,9] | 6,9 [6,4–7,9] | 17,1 [16,1–17,6] | 1,319 [1,193–1,474] | 1,32 [1,19–1,47] | 30,3 [27,1–33,5] | 7,37 [7,32–7,41] | 5,1 | 63 | 0,33 [0,32–0,36] | 1,10 | cristaloide 0 mL; GR 0,5 U; hemostasia 0/91 |
| 30 | 26,1 [22,9–30,0] | 9,1 [5,1–18,0] | 6,6 [5,7–7,9] | 17,4 [16,1–18,3] | 1,298 [1,171–1,476] | 1,30 [1,17–1,48] | 30,8 [27,1–34,2] | 7,37 [7,32–7,41] | 5,8 | 65 [65–65] | 0,17 [0,14–0,21] | 1,10 | cristaloide 0 mL; GR 1,0 U; hemostasia 0/91 |
| 60 | 24,7 [20,3–28,2] | 7,4 [3,3–16,2] | 5,4 [3,6–6,5] | 18,6 [17,5–20,4] | 1,232 [1,107–1,390] | 1,23 [1,11–1,39] | 32,5 [28,8–36,1] | 7,39 [7,34–7,42] | 6,2 [6,0–6,4] | 41 [34–47] | 0,00 | 1,10 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/91 |
| 90 | 23,0 [17,4–27,0] | 6,3 [2,1–15,0] | 4,2 [2,1–5,7] | 19,8 [18,3–21,9] | 1,167 [1,064–1,344] | 1,17 [1,06–1,34] | 34,3 [29,8–37,6] | 7,39 [7,35–7,42] | 4,8 [4,5–5,1] | 15 [12–17] | 0,00 | 1,10 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/91 |
| 120 | 21,9 [15,4–26,2] | 4,8 [1,3–13,9] | 3,2 [1,3–5,1] | 20,8 [18,9–22,7] | 1,137 [1,039–1,303] | 1,14 [1,04–1,30] | 35,2 [30,7–38,5] | 7,40 [7,36–7,42] | 3,4 [3,1–3,6] | 5 [4–7] | 0,00 | 1,10 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/91 |

**R3 · GR sin hemostasia · 72f · demanda 1,1** (91 trayectorias; FR intrínseca 12, 16, 20; ganancia de frecuencia 1,00, 1,41, 2,00, 2,83, 4,00; ganancia de ventilación 0,03, 0,04, 0,05, 0,06; eficiencia 1)

| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | demanda | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 23,9 [21,3–25,5] | 7,1 [3,9–12,2] | 4,2 | 19,8 | 1,189 [1,126–1,252] | 1,19 [1,13–1,25] | 33,7 [31,9–35,5] | 7,39 [7,37–7,42] | 3,4 | 20 | 0,25 | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/91 |
| 15 | 23,7 [20,6–25,7] | 7,0 [3,4–12,5] | 4,1 [3,7–4,3] | 19,9 [19,7–20,3] | 1,179 [1,111–1,260] | 1,18 [1,11–1,26] | 33,9 [31,8–36,0] | 7,39 [7,37–7,42] | 3,3 | 21 | 0,06 [0,04–0,08] | 1,10 | cristaloide 0 mL; GR 0,5 U; hemostasia 0/91 |
| 30 | 22,8 [19,0–25,1] | 6,3 [2,7–11,9] | 3,6 [2,9–4,0] | 20,4 [20,0–21,1] | 1,156 [1,087–1,241] | 1,16 [1,09–1,24] | 34,6 [32,2–36,8] | 7,40 [7,37–7,42] | 3,2 [3,1–3,2] | 15 [14–17] | 0,00 | 1,10 | cristaloide 0 mL; GR 1,0 U; hemostasia 0/91 |
| 60 | 21,2 [16,5–24,5] | 4,6 [1,7–10,8] | 2,8 [1,7–3,5] | 21,2 [20,5–22,3] | 1,112 [1,052–1,213] | 1,11 [1,05–1,21] | 36,0 [33,0–38,0] | 7,40 [7,38–7,42] | 2,5 [2,5–2,6] | 5 [5–6] | 0,00 | 1,10 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/91 |
| 90 | 20,0 [14,8–24,1] | 3,9 [1,0–9,9] | 2,2 [1,1–3,1] | 21,8 [20,9–22,9] | 1,090 [1,032–1,188] | 1,09 [1,03–1,19] | 36,7 [33,7–38,8] | 7,40 [7,38–7,42] | 1,9 [1,9–2,0] | 2 | 0,00 | 1,10 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/91 |
| 120 | 19,5 [13,7–23,6] | 2,6 [0,6–8,9] | 1,7 [0,6–2,8] | 22,3 [21,2–23,4] | 1,076 [1,019–1,166] | 1,08 [1,02–1,17] | 37,2 [34,3–39,3] | 7,40 [7,38–7,41] | 1,5 [1,5–1,6] | 1 | 0,00 | 1,10 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/91 |

**R4 · manejo definitivo (L3) · 57m · demanda 1,1** (91 trayectorias; FR intrínseca 12, 16, 20; ganancia de frecuencia 1,00, 1,41, 2,00, 2,83, 4,00; ganancia de ventilación 0,03, 0,04, 0,05, 0,06; eficiencia 1)

| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | demanda | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 26,1 [23,9–28,4] | 9,1 [5,9–16,4] | 6,7 | 17,3 | 1,301 [1,201–1,402] | 1,30 [1,20–1,40] | 30,8 [28,5–33,3] | 7,37 [7,34–7,41] | 4,4 | 60 | 0,50 | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/91 |
| 15 | 26,3 [23,6–29,9] | 9,5 [5,7–17,9] | 6,9 [6,4–7,9] | 17,1 [16,1–17,6] | 1,319 [1,193–1,474] | 1,32 [1,19–1,47] | 30,3 [27,1–33,5] | 7,37 [7,32–7,41] | 5,1 | 63 | 0,33 [0,32–0,36] | 1,10 | cristaloide 0 mL; GR 0,5 U; hemostasia 0/91 |
| 30 | 26,1 [22,9–30,0] | 9,1 [5,1–18,0] | 6,6 [5,7–7,9] | 17,4 [16,1–18,3] | 1,298 [1,171–1,476] | 1,30 [1,17–1,48] | 30,8 [27,1–34,2] | 7,37 [7,32–7,41] | 5,8 | 65 [65–65] | 0,17 [0,14–0,21] | 1,10 | cristaloide 0 mL; GR 1,0 U; hemostasia 0/91 |
| 60 | 24,7 [20,3–28,2] | 7,4 [3,3–16,2] | 5,4 [3,6–6,5] | 18,6 [17,5–20,4] | 1,232 [1,107–1,390] | 1,23 [1,11–1,39] | 32,5 [28,8–36,1] | 7,39 [7,34–7,42] | 6,2 [6,0–6,4] | 41 [34–47] | 0,00 | 1,10 | cristaloide 0 mL; GR 2,0 U; hemostasia 91/91 |
| 90 | 23,0 [17,4–27,0] | 6,3 [2,1–15,0] | 4,2 [2,1–5,7] | 19,8 [18,3–21,9] | 1,167 [1,064–1,344] | 1,17 [1,06–1,34] | 34,3 [29,8–37,6] | 7,39 [7,35–7,42] | 4,8 [4,5–5,1] | 15 [12–17] | 0,00 | 1,10 | cristaloide 0 mL; GR 2,0 U; hemostasia 91/91 |
| 120 | 21,9 [15,4–26,2] | 4,8 [1,3–13,9] | 3,2 [1,3–5,1] | 20,8 [18,9–22,7] | 1,137 [1,039–1,303] | 1,14 [1,04–1,30] | 35,2 [30,7–38,5] | 7,40 [7,36–7,42] | 3,4 [3,1–3,6] | 5 [4–6] | 0,00 | 1,10 | cristaloide 0 mL; GR 2,0 U; hemostasia 91/91 |

**R4 · manejo definitivo (L3) · 72f · demanda 1,1** (91 trayectorias; FR intrínseca 12, 16, 20; ganancia de frecuencia 1,00, 1,41, 2,00, 2,83, 4,00; ganancia de ventilación 0,03, 0,04, 0,05, 0,06; eficiencia 1)

| min | FR | FR − intrínseca | carga A | HCO3 | reclutamiento | W | PaCO2 | pH | lactato | D | déficit | demanda | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 23,9 [21,3–25,5] | 7,1 [3,9–12,2] | 4,2 | 19,8 | 1,189 [1,126–1,252] | 1,19 [1,13–1,25] | 33,7 [31,9–35,5] | 7,39 [7,37–7,42] | 3,4 | 20 | 0,25 | 1,10 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/91 |
| 15 | 23,7 [20,6–25,7] | 7,0 [3,4–12,5] | 4,1 [3,7–4,3] | 19,9 [19,7–20,3] | 1,179 [1,111–1,260] | 1,18 [1,11–1,26] | 33,9 [31,8–36,0] | 7,39 [7,37–7,42] | 3,3 | 21 | 0,06 [0,04–0,08] | 1,10 | cristaloide 0 mL; GR 0,5 U; hemostasia 0/91 |
| 30 | 22,8 [19,0–25,1] | 6,3 [2,7–11,9] | 3,6 [2,9–4,0] | 20,4 [20,0–21,1] | 1,156 [1,087–1,241] | 1,16 [1,09–1,24] | 34,6 [32,2–36,8] | 7,40 [7,37–7,42] | 3,2 [3,1–3,2] | 15 [14–17] | 0,00 | 1,10 | cristaloide 0 mL; GR 1,0 U; hemostasia 0/91 |
| 60 | 21,2 [16,5–24,5] | 4,6 [1,7–10,8] | 2,8 [1,7–3,5] | 21,2 [20,5–22,3] | 1,112 [1,052–1,213] | 1,11 [1,05–1,21] | 36,0 [33,0–38,0] | 7,40 [7,38–7,42] | 2,5 [2,5–2,6] | 5 [5–6] | 0,00 | 1,10 | cristaloide 0 mL; GR 2,0 U; hemostasia 91/91 |
| 90 | 20,0 [14,8–24,1] | 3,9 [1,0–9,9] | 2,2 [1,1–3,1] | 21,8 [20,9–22,9] | 1,090 [1,032–1,188] | 1,09 [1,03–1,19] | 36,7 [33,7–38,8] | 7,40 [7,38–7,42] | 1,9 [1,9–2,0] | 2 | 0,00 | 1,10 | cristaloide 0 mL; GR 2,0 U; hemostasia 91/91 |
| 120 | 19,5 [13,7–23,6] | 2,6 [0,6–8,9] | 1,7 [0,6–2,8] | 22,3 [21,2–23,4] | 1,076 [1,019–1,166] | 1,08 [1,02–1,17] | 37,2 [34,3–39,3] | 7,40 [7,38–7,41] | 1,5 [1,5–1,6] | 1 | 0,00 | 1,10 | cristaloide 0 mL; GR 2,0 U; hemostasia 91/91 |
<!-- /generado:reconstruccion -->

## 8. Preguntas fisiológicas clave (generado)

<!-- generado:preguntas -->
1. **¿La FR intrínseca baja implica hipercapnia en reposo?** No. Sin carga y con la demanda basal, la PaCO2 es 40 mmHg para toda FR intrínseca y toda ganancia de ventilación: sí. Con el mapeo de P2K-2, sobre los mismos candidatos de FR, era 57m 46,3 [40,1–73,5]; 72f 43,9 [39,4–66,6] mmHg.
2. **¿La PaCO2 vuelve hacia 40 al aclararse la carga?** En R4, a los 120 min la PaCO2 está tan o más cerca de 40 que a la llegada en 23544 de 23544 combinaciones; PaCO2 a 120: 57m 35,3 [30,6–38,7]; 72f 37,2 [34,3–39,3] mmHg (distancia a 40: 57m 4,7 [1,3–9,4]; 72f 2,8 [0,7–5,7]). Sin tratamiento (R1), a 120: 57m 27,7 [19,0–33,2]; 72f 31,4 [23,2–35,8] mmHg. Sonda H: sin carga y con la demanda basal, W = 1 y PaCO2 = 40 a toda FR intrínseca.
3. **¿La FR puede acercarse a una intrínseca baja con una PaCO2 razonable?** Estructuralmente sí: al aclararse la carga, la FR tiende a la intrínseca y la PaCO2 a 40, sin que una dependa de la otra (sonda H). En R4 a los 120 min, con la intrínseca más baja de cada caso (57m 12, 72f 12), la FR sigue 57m 8,8 [3,0–14,0]; 72f 5,1 [1,6–9,0] rpm sobre ella; a ≤ 3 rpm: 57m 18 de 5886; 72f 1962 de 5886; además con la PaCO2 a ≤ 5 mmHg de 40: 57m 72 de 23544; 72f 7848 de 23544.
4. **¿Sigue siendo posible la caída precoz leve de la FR de 72f sin lactato?** Sí: en 4599 de 10395 combinaciones (B 13,4: 3465 de 3465; B 19,4: 1134 de 3465; B 28: 0 de 3465); profundidad 0,00 [0,00–1,54] rpm. Mecanismo: el aclaramiento A0 / τ supera a la producción (B / τ) × d0 cuando B × d0 < A0; el lactato no llega a ningún término de la FR (sonda E).
5. **¿El lactato y la FR pueden moverse en sentidos opuestos?** Sí, al menos un minuto en 259118 de 313794 combinaciones.
6. **¿La FR y la PaCO2 pueden reflejar respuestas distintas de frecuencia y de reclutamiento?** En las trayectorias GI (eficiencia 1, demanda basal) las dos siguen a la misma carga: se mueven en sentidos opuestos en 1255176 de 1255176 combinaciones y en el mismo sentido en 0 de 1255176. Sus magnitudes dependen de ganancias distintas (§11: la FR no reacciona a la de ventilación ni la PaCO2 a la de frecuencia). Pueden disociarse cuando cambian la eficiencia o la demanda: curso de la sonda G sí, sonda I sí, sondas B y D sí.
- **Tras la reanimación (R4):** 15 min después de la hemostasia la FR sigue 5,4 [1,2–15,7] rpm sobre la intrínseca (≥ 1 rpm en 38259 de 38259); el minuto de la hemostasia no mueve la FR más que otro minuto en 38259 de 38259, ni la PaCO2 en 23544 de 23544.
<!-- /generado:preguntas -->

## 9. Identificabilidad (generado)

<!-- generado:identificabilidad -->
| magnitud | clase | detalle |
|---|---|---|
| FR intrínseca 57m | POORLY_IDENTIFIED | valores que sobreviven: 12, 16, 20 |
| FR intrínseca 72f | POORLY_IDENTIFIED | valores que sobreviven: 12, 16, 20 |
| ganancia ácido → FR | POORLY_IDENTIFIED | valores que sobreviven: 1,000, 1,414, 2,000, 2,828, 4,000 |
| ganancia ácido → ventilación | PARTIALLY_CONSTRAINED | valores que sobreviven: 0,030, 0,040, 0,050, 0,060 |
| B (escala déficit → ácido) | NON_IDENTIFIABLE | no authored observation after arrival; the arrival burden is the authored HCO3's |
| τ de aclaramiento ácido | NON_IDENTIFIABLE | as B |

**Compuestos observables en la llegada** (sobre los candidatos compatibles en conjunto):

| caso | incremento de FR | reclutamiento | PaCO2 predicha | pH predicho |
|---|---|---|---|---|
| 57m | 7,9 [5,9–16,4] (POORLY_IDENTIFIED) | 1,301 [1,201–1,402] (PARTIALLY_CONSTRAINED) | 30,8 [28,5–33,3] (PARTIALLY_CONSTRAINED) | 7,373 [7,338–7,406] (POORLY_IDENTIFIED) |
| 72f | 5,3 [3,9–12,2] (POORLY_IDENTIFIED) | 1,189 [1,126–1,252] (PARTIALLY_CONSTRAINED) | 33,7 [31,9–35,5] (PARTIALLY_CONSTRAINED) | 7,393 [7,369–7,415] (PARTIALLY_CONSTRAINED) |

Frozen. The arrival RR and PaCO2 (+/- 3, provisional) are the only authored respiratory constraints; pH is derived from them. A latent parameter is WELL_CONSTRAINED when one value survives jointly, PARTIALLY_CONSTRAINED when some but not all do, POORLY_IDENTIFIED when every value survives in some joint combination although the arrival reads it (a trade-off with another parameter), NON_IDENTIFIABLE when the arrival does not read it (B, tau: no authored observation after arrival). A composite is WELL_CONSTRAINED when its spread over the joint survivors is at most its tolerance half-width (RR 3, PaCO2 3, pH 0.03; the recruitment through the PaCO2 it implies), PARTIALLY_CONSTRAINED when at most the full window, POORLY_IDENTIFIED above, NON_IDENTIFIABLE without survivors. No best set.
<!-- /generado:identificabilidad -->

## 10. Dependencias de la incertidumbre previa (generado)

<!-- generado:dependencias -->
| magnitud a 120 min (mediana por tabla) | demanda 1,0 vs 1,1: diferencia | tono g: dispersión |
|---|---|---|
| carga mEq/L | 0,65 [0,10–1,23] | 0,07 [0,01–0,26] |
| FR rpm | 0,63 [0,10–1,63] | 0,08 [0,01–0,27] |
| PaCO2 mmHg | 0,54 [0,14–1,53] | 0,08 [0,01–0,28] |
| pH  | 0,0035 [0,0000–0,0186] | 0,0004 [0,0000–0,0035] |

| dimensión | vía | estado |
|---|---|---|
| demanda 1,0 / 1,1 | demand -> effective deficit -> acid burden -> drive (RR) and recruitment (W) -> PaCO2 / pH; the baseline-relative W reads no demand class directly | causal; se lleva |
| ganancia de tono g | g -> T -> output -> delivery -> deficit -> acid burden | causal pequeña; se lleva |
| MAP_set | NONE | P2J-4 rows_equal: the baroreflex moves only the sympathetic drive; no deficit, burden, RR or W term reads it |
| ganancia del barorreflejo | NONE | as MAP_set |
| región latente de FC | NONE | HR reaches no output, delivery, deficit, D, lactate or burden (P2I-2AG, P2J-1) |

Se multiplican sólo: demand, tone_gain.
<!-- /generado:dependencias -->

## 11. Paquete de decisión observable A–I (generado)

<!-- generado:paquete -->
Preparado, **no aprobado** (PREPARED_NOT_APPROVED). Bajo / mediana / alto sobre trayectorias × B/τ × los candidatos compatibles en conjunto que lee cada observable. Sensibilidad: diferencia entre la mayor y la menor mediana al agrupar por cada factor («sin vía»: el observable no lee ese factor).

**A · FR a 120 min sin tratamiento · 57m.** La carga ácida de una hemorragia no controlada mueve la frecuencia; cuánto sube a los 120 min depende de su producción y aclaramiento (B, τ), de la ganancia de frecuencia y de la FR intrínseca.

| observable | bajo | mediana | alto | n | FR intrínseca | ganancia de frecuencia | ganancia de ventilación | B / τ | demanda | tono g |
|---|---|---|---|---|---|---|---|---|---|---|
| 57m | 24,0 | 29,5 | 36,2 | 8910 | 2,25 | 3,74 | sin vía | 7,23 | 0,86 | 0,08 |

**B · FR a 120 min sin tratamiento · 72f.** Como A, con la carga y el déficit de llegada menores de 72f; una caída precoz es posible si el aclaramiento supera a la producción.

| observable | bajo | mediana | alto | n | FR intrínseca | ganancia de frecuencia | ganancia de ventilación | B / τ | demanda | tono g |
|---|---|---|---|---|---|---|---|---|---|---|
| 72f | 20,9 | 26,1 | 34,7 | 10395 | 0,35 | 2,12 | sin vía | 6,07 | 1,03 | 0,30 |

**C · PaCO2 / pH a 120 min sin tratamiento · 57m.** La hiperventilación compensadora por reclutamiento (ganancia común de ventilación) baja la PaCO2 al subir la carga; el pH sigue al HCO3 y a la PaCO2.

| observable | bajo | mediana | alto | n | FR intrínseca | ganancia de frecuencia | ganancia de ventilación | B / τ | demanda | tono g |
|---|---|---|---|---|---|---|---|---|---|---|
| 57m | 19,0 | 27,7 | 33,2 | 5940 | sin vía | sin vía | 5,82 | 7,10 | 0,73 | 0,12 |
| 57m · pH | 6,961 | 7,322 | 7,405 | 5940 | sin vía | sin vía | 0,0915 | 0,2578 | 0,0178 | 0,0026 |

**D · PaCO2 / pH a 120 min sin tratamiento · 72f.** Como C, para 72f.

| observable | bajo | mediana | alto | n | FR intrínseca | ganancia de frecuencia | ganancia de ventilación | B / τ | demanda | tono g |
|---|---|---|---|---|---|---|---|---|---|---|
| 72f | 23,2 | 31,4 | 35,8 | 5940 | sin vía | sin vía | 4,50 | 6,13 | 1,00 | 0,25 |
| 72f · pH | 7,230 | 7,376 | 7,415 | 5940 | sin vía | sin vía | 0,0620 | 0,0743 | 0,0109 | 0,0024 |

**E · respuesta de la FR al cristaloide (FR120 − FR0, R2).** El cristaloide restaura por un tiempo la precarga y la entrega; baja el déficit, con él la producción, y la FR sigue a la carga.

| observable | bajo | mediana | alto | n | FR intrínseca | ganancia de frecuencia | ganancia de ventilación | B / τ | demanda | tono g |
|---|---|---|---|---|---|---|---|---|---|---|
| 57m | −2,8 | 1,0 | 6,6 | 100602 | 0,44 | 0,53 | sin vía | 5,15 | 1,15 | 0,10 |
| 57m · FR a 120 min | 22,1 | 27,5 | 34,3 | 100602 | 2,02 | 3,17 | sin vía | 5,23 | 1,10 | 0,06 |
| 72f | −5,5 | −0,2 | 6,0 | 117369 | 0,14 | 0,19 | sin vía | 3,79 | 1,36 | 0,19 |
| 72f · FR a 120 min | 16,9 | 23,6 | 31,1 | 117369 | 1,78 | 1,00 | sin vía | 3,60 | 1,54 | 0,16 |

**F · respuesta de la FR a los GR sin hemostasia (FR120 − FR0, R3).** Los GR restauran el contenido de oxígeno; sin hemostasia el déficit puede volver.

| observable | bajo | mediana | alto | n | FR intrínseca | ganancia de frecuencia | ganancia de ventilación | B / τ | demanda | tono g |
|---|---|---|---|---|---|---|---|---|---|---|
| 57m | −12,4 | −4,1 | −1,2 | 17658 | 2,85 | 3,59 | sin vía | 4,77 | 0,35 | 0,14 |
| 57m · FR a 120 min | 15,0 | 21,8 | 26,3 | 17658 | 2,73 | 3,44 | sin vía | 6,14 | 0,38 | 0,12 |
| 72f | −10,0 | −3,6 | −1,2 | 20601 | 3,05 | 4,09 | sin vía | 3,65 | 0,22 | 0,05 |
| 72f · FR a 120 min | 13,6 | 19,5 | 23,6 | 20601 | 4,83 | 3,72 | sin vía | 3,65 | 0,10 | 0,02 |

**G · FR a 120 min tras el manejo definitivo (R4).** Con hemostasia y reanimación el déficit termina y la carga se aclara en τ; la FR baja hacia la intrínseca.

| observable | bajo | mediana | alto | n | FR intrínseca | ganancia de frecuencia | ganancia de ventilación | B / τ | demanda | tono g |
|---|---|---|---|---|---|---|---|---|---|---|
| 57m | 15,0 | 21,8 | 26,3 | 17658 | 2,74 | 3,44 | sin vía | 6,18 | 0,38 | 0,11 |
| 72f | 13,6 | 19,5 | 23,6 | 20601 | 4,83 | 3,72 | sin vía | 3,65 | 0,10 | 0,02 |

**H · PaCO2 / pH a 120 min tras el manejo definitivo (R4).** Al aclararse la carga se apaga el reclutamiento y la PaCO2 vuelve hacia 40 mientras se recupera el HCO3.

| observable | bajo | mediana | alto | n | FR intrínseca | ganancia de frecuencia | ganancia de ventilación | B / τ | demanda | tono g |
|---|---|---|---|---|---|---|---|---|---|---|
| 57m | 30,6 | 35,3 | 38,7 | 11772 | sin vía | sin vía | 2,92 | 4,93 | 0,27 | 0,06 |
| 57m · pH | 7,359 | 7,398 | 7,415 | 11772 | sin vía | sin vía | 0,0355 | 0,0124 | 0,0009 | 0,0003 |
| 72f | 34,3 | 37,2 | 39,3 | 11772 | sin vía | sin vía | 1,75 | 3,21 | 0,16 | 0,03 |
| 72f · pH | 7,382 | 7,402 | 7,415 | 11772 | sin vía | sin vía | 0,0204 | 0,0025 | 0,0000 | 0,0000 |

**I · FR residual sobre la intrínseca a 120 min tras la reanimación adecuada (R4).** La parte de la FR que todavía mueve la carga no aclarada.

| observable | bajo | mediana | alto | n | FR intrínseca | ganancia de frecuencia | ganancia de ventilación | B / τ | demanda | tono g |
|---|---|---|---|---|---|---|---|---|---|---|
| 57m | 1,1 | 4,7 | 14,0 | 17658 | 5,26 | 6,97 | sin vía | 4,87 | 0,63 | 0,29 |
| 72f | 0,6 | 2,6 | 9,0 | 20601 | 3,17 | 4,28 | sin vía | 3,65 | 0,15 | 0,04 |
<!-- /generado:paquete -->

## 12. Factorización y no regresión (generado)

<!-- generado:no_regresion -->
Validación contra el núcleo: 48 corridas completas con el candidato de validación (ganancia de frecuencia 2,0, FR intrínseca 16 / 16, B 19,4, τ 120, ganancia de ventilación 0,05) y las mismas 48 sin él.

- Módulo de ventilación = álgebra factorizada en cada estado: sí (diferencia máxima 0); razón de demanda 1 en todos los estados: sí; FR del núcleo = FR del módulo: sí.
- Fisiología previa, filas y estados con la candidata iguales a sin ella:

| dominio | igual |
|---|---|
| BloodState | sí |
| gasto | sí |
| presión / tono | sí |
| DO2 / déficit efectivo | sí |
| D | sí |
| lactato | sí |
| FC / barorreflejo | sí |

- Todo el estado salvo la carga ácida igual: sí; FR por defecto = la de P2K-1: sí.
- P2K-1 recalculado igual a su registro: sí; región de P2J-3 recalculada igual: demand_class sí, primary sí, support sí, units sí.
- P2K-2 reproducido en vivo: compatibilidad de llegada sí, sondas sí, tablas aguas arriba sí.
- Archivos del núcleo y módulo de P2K-2 con sus huellas de `cbec249`: `acid_base.py` sí, `derived.py` sí, `integration.py` sí, `state.py` sí.
- Rechazos: ANALYTIC_REJECTION 0, SIMULATION_REJECTION 0. Valores: pH 6,961–7,415 (fuera de 6,8–7,8: 0); PaCO2 mínima 19,0 mmHg; W mínima 1,018; W o PaCO2 no positivas: 0.
<!-- /generado:no_regresion -->

## 13. Veredicto (generado)

<!-- generado:veredicto -->
**RR_VENTILATION_DECISION_SURFACE_READY**

| criterio | se cumple |
|---|---|
| la FR no determina W | sí |
| la FR intrínseca no determina la PaCO2 en reposo | sí |
| el lactato y D siguen retirados como controladores | sí |
| la FR de llegada se reproduce | sí |
| la PaCO2 de llegada se reproduce con una ganancia común | sí |
| el pH es coherente | sí |
| trayectorias propias de un paciente | sí |
| la factorización es válida | sí |
| fisiología previa intacta | sí |
| nada aprobado | sí |

**Envolventes observables que se piden a la docencia (no se aplican en P2K-3):**
- FR a 120 min sin tratamiento, por caso (A, B): una envolvente educativa BAJO–ALTO, o ninguna
- PaCO2 / pH a 120 min sin tratamiento, por caso (C, D): una envolvente, o ninguna
- FR, PaCO2 y pH a 120 min tras el manejo definitivo (G, H): envolventes, o ninguna
- FR residual sobre la intrínseca tras la reanimación adecuada (I): una envolvente, o ninguna
- si las respuestas de la FR al cristaloide y a los GR (E, F) se acotan o sólo se informan

**Otras decisiones que se piden:**
- confirmar la semántica de la demanda relativa a la basal en W (el índice absoluto haría hipercápnica en reposo a la clase 1,1)
- mantener la ganancia de ventilación EXPLORATORY sobre su soporte conjunto, o adoptar una (no se propone ningún valor)
- las envolventes de arriba, si el veredicto es READY; ninguna se aplica en P2K-3
<!-- /generado:veredicto -->

## 14. Eficiencia (generado)

<!-- generado:eficiencia -->
P2J-3 recalculado: 1326 trayectorias de sangre y 364 contrafactuales. 5364 trayectorias de déficit reconstruidas una vez; la carga se integra para 9 pares (B, τ); la FR es álgebra de la carga para 6 (57m) y 7 (72f) pares (ganancia, FR intrínseca) y W / PaCO2 / pH para 4 ganancias de ventilación. Las tablas y el paquete A–I no las cruzan; sólo las preguntas 3 y 6, que por definición piden la relación entre FR y PaCO2, recorren los dos lados (con los conjuntos de la PaCO2 calculados una vez por ganancia). La llegada se resolvió analíticamente (2025 combinaciones con el soporte ácido). Corridas completas del núcleo: 96 (validación). Barrido cartesiano: no; FR heredada leída: no.
<!-- /generado:eficiencia -->

## 15. Lo que se pide a la docencia

Ninguna de estas decisiones la toma la IA. Todo lo anterior es EXPLORATORY o PROVISIONAL.

1. **Semántica de la demanda en W.** P2K-3 usa la demanda relativa a la basal del paciente (BASELINE_RELATIVE). Así,
   W = 1 es la ventilación que corresponde a su propia producción basal de CO2, y la clase de demanda 1,0 / 1,1 llega a
   W sólo por el déficit y la carga. Con el índice absoluto, la clase 1,1 quedaría un 10 % hipercápnica en reposo y la
   llegada aceptaría otras ganancias (0,06 y 0,08 en lugar de 0,03–0,06; §6). Se pide confirmar.
2. **Envolventes observables para el próximo paquete numérico** (no se aplican aquí; §11 da las distribuciones):
   - FR a 120 min sin tratamiento, por caso (A, B);
   - PaCO2 / pH a 120 min sin tratamiento, por caso (C, D);
   - FR, PaCO2 y pH a 120 min tras el manejo definitivo (G, H);
   - FR residual sobre la intrínseca tras la reanimación adecuada (I);
   - si las respuestas de la FR al cristaloide y a los GR (E, F) se acotan o sólo se informan.

   En las trayectorias certificadas, R3 (GR sin hemostasia) y R4 coinciden a los 120 min en 10 de 12 tablas. Con los
   GR el déficit efectivo ya es 0, haya o no hemostasia. Por eso F y G no se separan a esa hora. Si la docencia quiere
   distinguirlos, la envolvente tendría que ser de otro observable o de otra hora.
3. **Ganancia ácido → ventilación.** Sobreviven 0,03, 0,04, 0,05 y 0,06 (PARTIALLY_CONSTRAINED). Se pide mantenerla
   EXPLORATORY sobre ese soporte o adoptar un valor; no se propone ninguno. El pH diagnóstico es consistente en los dos
   casos sólo con 0,04 y 0,05; no se usó para filtrar.
4. **FR intrínseca y ganancia de frecuencia.** Siguen POORLY_IDENTIFIED: todos sus valores sobreviven en alguna
   combinación (la cresta de P2K-2). Sólo una observación posterior a la llegada (las envolventes del punto 2) puede
   acotarlas.

## 16. Limitaciones

- **Sólo sombra y fuera del núcleo en ejecución.** La candidata P2K-3 se evalúa con
  `ventilation.ventilated_respiration`. `derive()` sigue informando la FR, y `derived.respiration` conserva el W de
  P2K-2. Una integración futura tendría que adoptar uno de los dos explícitamente; hoy no hay autorización para eso.
- **La llegada no lee B ni τ.** Siguen NON_IDENTIFIABLE. Las distribuciones tardías dependen sobre todo de ellos
  (§11: B/τ es la mayor sensibilidad en casi todos los observables).
- **El pH es una lectura derivada.** La tolerancia de ± 0,03 es diagnóstica; con ± 3 mmHg de PaCO2 el pH predicho
  puede quedar fuera aunque la PaCO2 esté dentro. Eso se informa, no se filtra.
- **Las bandas de la pregunta 3** (FR a ≤ 3 rpm de la intrínseca, PaCO2 a ≤ 5 mmHg de 40) son lecturas
  diagnósticas congeladas, no envolventes. A los 120 min la carga de 57m todavía no se aclaró, así que esa lectura es
  casi siempre «no» para 57m.
- **En las trayectorias GI la FR y la PaCO2 siempre se mueven en sentidos opuestos**: eficiencia 1 y demanda basal,
  con una sola carga que las mueve. La disociación (FR alta con PaCO2 alta) sólo aparece si cambian la eficiencia o la
  demanda, que hoy sólo cambian las sondas sintéticas. No hay mecánica, fatiga, espacio muerto ni volumen corriente
  explícitos (FUTURE_RESPIRATORY_GENERALIZATION).
- **R3 y R4 casi coinciden a los 120 min** en la fisiología previa certificada (§15, punto 2). P2K-3 hereda esa
  propiedad; no la introduce.
- **La PaCO2 mínima de 19 mmHg** aparece en la esquina extrema de R1 57m: la mayor carga a los 120 min con la mayor
  ganancia de ventilación compatible (0,06), porque PaCO2 = 40 / (1 + ganancia × carga). Es posible en una acidosis
  metabólica grave con compensación máxima, pero ninguna envolvente la acota todavía.

## 17. Revisión adversarial

Una revisión independiente, de sólo lectura, sobre `e243b05`, con el foco que pidió la docencia. Confirmó cada
hallazgo con una sonda o una mutación fuera del repositorio. Sin hallazgos de severidad alta.

- **Limpios** (con evidencia):
  - ni la FR ni la FR intrínseca llegan a W, PaCO2 o pH;
  - W no es el impulso con otro nombre;
  - la ganancia de ventilación no se ajustó y es común;
  - la PaCO2 de referencia no figura como aprobada;
  - el pH no filtra;
  - no se fuerza la subida de la carga;
  - el lactato y D no vuelven;
  - no hay volumen corriente explícito;
  - los archivos del núcleo tienen las huellas de `cbec249`;
  - no se lee la FR heredada;
  - no se multiplican MAP_set, el barorreflejo ni la FC;
  - los conteos de llegada, recalculados, coinciden.
- **M1 (media), corregido.** En una parada temprana, los criterios no evaluados contaban como fallidos, así que el
  bloqueante nombrado era el equivocado. Ahora la parada nombra el criterio que falló y lista los no evaluados.
  Prueba de regresión: la parada de PaCO2 nombra ARRIVAL_PACO2_REPRODUCED y la de un archivo del núcleo,
  UPSTREAM_UNCHANGED.
- **M2 (media), corregido.** La validación contra el núcleo comprobaba una copia del álgebra, no la que generó las
  tablas. Ahora `evaluate` y `validate` usan las mismas funciones por serie, y además se comprueba el pulso de la
  trayectoria contra el del núcleo.
- **B1, corregido.** La pregunta 1 recorría la FR intrínseca sin usarla. Ahora se calcula con el módulo sobre estados
  del núcleo con cada FR intrínseca declarada.
- **B2, corregido.** La prueba estática no veía asignaciones aumentadas, anidadas ni anotadas, ni el `return`. Ahora
  las ve; hay pruebas con mutaciones.
- **B3, corregido.** Los conjuntos de dirección de la PaCO2 se recalculaban dentro del bucle de FR. Además, «sin
  producto» no era literal para las preguntas 3 y 6, que cruzan FR y PaCO2 por definición; el registro y §14 lo dicen
  ahora.
- **B4, corregido en el texto.** El resumen ahora dice «al menos un minuto». El pH mínimo de 6,96 se describe como
  acidemia grave dentro del rango plausible, no como «sin valores patológicos». El comentario de `PH_PLAUSIBLE` ya no
  habla de una parada.
- **B5, declarado.** `paco2_reference_mmhg` cambia de papel en la candidata: es la PaCO2 con W = 1, no el respaldo de
  la PaCO2 de llegada de P2K-2 (`ventilation.STATUS`, TD-104 (7)).

Estas correcciones cambian el digest, así que P2K-3 se recongeló (`bb6d81e`) después de ver los resultados, como en
P2K-2. Ningún rango, candidato, tolerancia, referencia ni criterio cambió. Antes del recongelamiento, una corrida del
análisis corregido coincidió con el registro de `e243b05` en todo valor de llegada, reconstrucción, paquete,
validación y veredicto; la reevaluación oficial es idéntica a esa corrida.
