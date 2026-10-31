# P2K-2 · Carga ácida metabólica y núcleo de ventilación efectiva

- **Fecha:** 2026-10-31. **Rama:** `phase-2-clinical-core-shadow`. **Base:** `81ed6b8` (P2K-1, cerrado).
- **Congelamiento:** `57b0ddc` (digest `23aa0a38…`), antes de leer cualquier trayectoria respiratoria clínica.
- **Recongelamiento tras la revisión adversarial:** `0863d75` (digest `7540ee76…`). Los rangos, los candidatos y los criterios son los
  mismos. Cambian la prueba de cierre, el anclaje de la eficiencia ventilatoria, una comprobación de E1, la clase de
  identificabilidad de la eficiencia y una comprobación de la validación (§15). Los números de los escenarios no
  cambian.
  - Antes de congelar sólo se leyeron entradas: el gas de llegada del banco, los déficits efectivos de llegada del
    registro de P2K-1 y las sondas sintéticas.
  - Las rutas de código se probaron sobre un almacén sintético y una corrida real de la que sólo se imprimieron
    booleanos de igualdad aguas arriba.
- **Números:** `docs/revision/P2K2_acid_base.json`. Generador de los bloques: `python -m clinical_core.acid_base_report`.
- **Alcance:** sólo sombra. Sin aprobación ni envolvente de FR, sin filtro numérico, sin recalibrar conciencia, sin
  colapso, sin ventilación mecánica, sin migraciones ni integración en tiempo de ejecución, sin ajuste a la FR heredada.

## Resumen

- **Qué entra en el núcleo (desactivado por defecto).**
  - Una carga ácida metabólica con dinámica propia:
    - llegada max(0, 24 − HCO3) con el HCO3 del banco;
    - producción por el déficit efectivo de oxígeno y aclaramiento de primer orden;
    - sin la regla de «no repagar con déficit» de D.
  - Un impulso respiratorio que lee sólo esa carga.
  - La FR como FR intrínseca más una respuesta suave y saturable al impulso.
  - W como ventilación alveolar efectiva relativa a la necesidad: eficiencia × FR / FR intrínseca.
  - PaCO2 algebraica en W, anclada a la PaCO2 de autor, y pH de HCO3 y PaCO2.
  - En la fisiología candidata el lactato, D y el canal W no llegan a la FR.
  - El perfil por defecto conserva la FR de P2K-1, sólo para que los registros cerrados y el golden sigan
    reproducibles.
  - La prueba AST muestra que P2K-2 cambió los tres archivos del núcleo sólo con sus inserciones declaradas:
    - su contenido queda fijado por digest;
    - cada comprobación insertada sólo lanza un error, o actúa bajo exactamente `acid_base_active(profile)` con uno de
      sus dos cuerpos permitidos.
- **Llegada.**
  - La carga de llegada sale del HCO3 (57m 6,7; 72f 4,2 mEq/L), nunca del lactato.
  - La PaCO2 es exacta por construcción.
  - El pH derivado difiere del de autor en −0,0004 (57m) y +0,0010 (72f), dentro del redondeo del HCO3 del banco.
- **Superficie.**
  - De 405 combinaciones predeclaradas, la llegada (± 3 rpm, provisional) deja **9 de 45** tríos comunes (ganancia,
    FR intrínseca de cada caso).
  - Forman una cresta: más FR intrínseca va con menos ganancia. Cada valor de ganancia y de FR intrínseca aparece en
    algún trío compatible.
- **Sondas A–H:** todas se comportan como pide la docencia.
  - El lactato solo y D solo no mueven la FR.
  - La carga que se aclara baja la FR con el lactato alto.
  - Con eficiencia baja, una FR alta deja W ≤ 1 y la PaCO2 sube pese a la taquipnea (E1, dentro del núcleo: PaCO2 59
    mmHg con FR 27,8).
  - La revisión encontró que antes una eficiencia constante se cancelaba con el anclaje; ahora el anclaje de llegada
    se lee a la eficiencia de referencia 1.
- **Trayectorias.**
  - Sin tratamiento, la carga sube y la FR con ella cuando B es alto. Con B = 28 nunca baja en ninguna trayectoria de
    ningún caso; con B = 13,4 baja al principio, porque la carga de llegada supera la que sostiene el déficit de
    llegada.
  - La bradipnea precoz de 72f ya no sale del lactato. Aparece sólo si el aclaramiento ácido supera la producción
    (B × d0 < A0), es de 1,5 rpm como máximo y desaparece con B = 28.
  - Tras la reanimación, la carga se aclara poco a poco: la FR baja hacia la intrínseca sin normalizarse de golpe y
    la PaCO2 sube.
- **Hallazgo principal para la docencia: la PaCO2 en reposo implícita.**
  - Con volumen corriente constante (W ∝ FR), la llegada de autor (FR 26 y 24 con PaCO2 31 y 33) sólo da una
    recuperación eucápnica (≈ 40 mmHg) con FR intrínseca ≈ 20.
  - Con 12 o 16 la PaCO2 en reposo implícita es de 44 a 74 mmHg. A los 120 min de R4 la PaCO2 llega a 55,4–56,2 en
    72f y a 52,6–54,9 en 57m, con pH 7,24–7,26.
  - W = 1 es la eupnea del paciente a su FR intrínseca, y sólo es eucapnia si esa PaCO2 en reposo es normal: 6 de los
    9 tríos compatibles la dan hipercápnica.
  - No es un fallo del álgebra ni un valor imposible. Es la consecuencia de suponer que toda la hiperventilación de
    llegada es frecuencia, y la docencia decide qué hacer (§13).
- **Dependencias.**
  - La demanda y la ganancia de tono llegan a la carga por el déficit: a los 120 min, 0,65 mEq/L de mediana por
    demanda y 0,07 por tono.
  - MAP_set, el barorreflejo y la región latente de FC no llegan y no se multiplican.
- **Veredicto: ACID_BASE_RR_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION.**
  - Es el veredicto de los criterios congelados y queda condicionado a la decisión de §13.1 (FR intrínseca y volumen
    corriente). Varios criterios se cumplen por construcción (§14).
  - Nada aprobado, ninguna envolvente filtra nada y el paquete de decisión queda preparado sin filtrar.

## 1. Decisiones docentes registradas (generado)

<!-- generado:decisiones -->
- **dinámica de la carga**: dA/dt = production from the effective oxygen deficit - clearance; more deficit never less production, no deficit no new production, gradual clearance, the burden may fall while a deficit lasts, never below 0; D's no-repayment rule is not copied
- **parámetros de producción y aclaramiento**: explicit exploratory deficit_to_acid_gain and acid_clearance_tau, independent of the debt and lactate parameters; a small range predeclared before clinical outcomes, from dimensional consistency, the authored arrival burden, the current deficit trajectories, synthetic probes and no instantaneous normalization; no legacy RR fitting, no final value
- **estado de carga ácida**: a new common state, metabolic_acid_burden: a time-varying metabolic acid / bicarbonate-deficit burden, not lactate, not D, not pH; burden = max(0, HCO3_reference - HCO3), HCO3_reference 24 mEq/L COMMON_REFERENCE_PROVISIONAL, not FACULTY_APPROVED; the arrival burden from the bank's HCO3 (57m 17.3, 72f 19.8), never from lactate
- **llegada**: 57m RR 26, 72f RR 24 against the HCO3-derived burden; the drive range is built before arrival compatibility is counted; common acid-to-drive physiology, patient-specific intrinsic RR, no residual offset; mismatch at +/- 3 breaths/min, ARRIVAL_RR_TOLERANCE_PROVISIONAL, not a measurement error; zero common candidates is a stop, never a wider tolerance
- **incertidumbre que se lleva**: MAP_set 80 / 90 / 100 and the baroreflex gain conditional on demand (1.0: 0.25, 0.5; 1.1: 0.25, 0.5, 1.0, 1.5) carried, not collapsed, not selected; nothing FACULTY_APPROVED
- **P2K-1**: P2K-1 accepted and closed: RR_STRUCTURE_NOT_READY - ACID_BASE_STATE_REQUIRED is a genuine structural blocker; RR is not calibrated numerically on the direct lactate -> RR proxy
- **D**: D is oxygen-delivery debt and never drives RR directly; deficit -> acid burden -> drive is the metabolic path
- **fecha**: 2026-10-31
- **impulso respiratorio**: drive from the acid burden only; no new drivers for D, lactate, pressure or HR; explicit acid_to_respiratory_drive_gain, no value approved; hypoxaemic drive audited, numerically deferred
- **impulso, FR y W**: respiratory drive (central command), RR (observable frequency) and W (effective alveolar ventilation relative to metabolic need) are three quantities, never aliases; mechanics preserved, no support, no fatigue in the GI cases, so RR and W correlate, but the structure lets them diverge
- **parada temprana**: algebraic non-uniqueness, unstable acid / ventilation feedback, evaluation-order dependence, impossible pH / PaCO2 or an upstream regression stops the package; no parameter hides a structural problem
- **eficiencia ventilatoria**: effective ventilation rises with RR in the spontaneous GI cases, with an explicit ventilation_efficiency so a high RR does not guarantee a high W; 1 for the GI cases as a STRUCTURAL REFERENCE, below 1 only in synthetic probes; no mechanics / fatigue grid
- **impulso hipoxémico**: HYPOXEMIC_DRIVE_DEFERRED: no new gain; the GI cases are not hypoxaemic; the architecture allows a later term
- **FR intrínseca**: intrinsic RR 12 / 16 / 20 per patient, EXPLORATORY, not FACULTY_APPROVED; the two patients may differ; no case-specific acid-drive gain; no value added after outcomes
- **lactato**: once the acid burden is active, the lactate concentration drives no RR; lactate stays a biomarker; a guard proves lactate alone, with burden and ventilation fixed, leaves RR unchanged
- **canales L, G y N**: L, G and N are not added as RR drivers for the GI cases: GENERALIZATION_PATH_RESERVED
- **PaCO2**: algebraic from W, higher W lower PaCO2, anchored to each patient's authored arrival PaCO2 (57m 31, 72f 33) so minute 0 is exact by construction; no PaCO2 time constant in P2K-2
- **pH**: pH from HCO3 and PaCO2 by the bicarbonate / CO2 relation, never a tuned state; arrival 57m 7.37 and 72f 7.40 within source rounding, the exact error reported, no offset
- **FR**: RR from the patient-specific intrinsic RR plus the non-negative drive, continuous and monotone, smoothly saturating; no lactate or D term; no hard clip as the primary physiology
- **alcance**: shadow only: no runtime integration, GI or second-family migration, final RR / acid approval, hard RR envelope, consciousness recalibration, collapse activation, mechanical-ventilation calibration or legacy fitting
- **soporte respiratorio**: spontaneous breathing, room air except FiO2 where represented, no NIV or invasive ventilation: the mechanical override is not a GI blocker; no NIV / mode / PEEP in P2K-2: FUTURE_GENERALIZATION_REQUIREMENT; FiO2 acts through oxygenation and delivery
- **fisiología aguas arriba**: BloodState, output, pressure / tone, DO2 / effective deficit, D, lactate and HR / baroreflex are reused and must not change; only respiratory outputs may
- **W**: W = effective alveolar ventilation relative to metabolic ventilatory need: 1 matches it, below 1 relative hypoventilation, above 1 relative hyperventilation; not the drive
- **fuga semántica de W**: the old W use (W > 0 multiplying part of RR, W < 0 scaling it) is a SEMANTIC_LEAK retired in the candidate: drive -> RR, drive + efficiency -> W, W -> PaCO2, never W -> drive
<!-- /generado:decisiones -->

## 2. Lo que el núcleo representa ahora (generado)

<!-- generado:semantica -->
| magnitud | definición |
|---|---|
| acid_burden | aux.metabolic_acid_burden (mEq/L), a dynamic state: arrival = max(0, HCO3_reference - arrival HCO3); each minute A' = A + deficit_to_acid_gain x effective_deficit - A / acid_clearance_tau (derived.acid_burden_after_minute, integration._acid_burden); never below 0 (tau >= 1) |
| bicarbonate | HCO3 = arrival HCO3 - (A - arrival A) = HCO3_reference - A below the reference |
| clearance | first-order, always on: the burden falls whenever A / tau exceeds the production, also while a deficit lasts; no no-repayment rule |
| default | off by default: the three gains None leave every default run, the golden and every closed record unchanged; the candidate is the profile with the three gains declared |
| drive | respiratory_drive = acid_to_drive_gain x A (breaths/min-equivalent): the burden only |
| paco2 | PaCO2 = PaCO2_rest / W, PaCO2_rest = arrival PaCO2 x the arrival W at the reference efficiency 1 (the model's arrival RR): exact at minute 0 when the arrival efficiency is the reference (the GI cases); a lower efficiency lowers W and raises PaCO2 above that anchor (review: a constant efficiency used on both sides cancelled); PaCO2_rest is implied by the anchoring, not a parameter |
| ph | pH = 6.1 + log10(HCO3 / (0.03 PaCO2)), the case bank's own constants (clinical_cases._gas) |
| production | the minute's effective oxygen deficit, max(0, demand - reserve x delivery) at the start-of-minute delivery and the minute's demand: the one D integrates; linear, so more deficit never produces less and no deficit produces nothing |
| rr | RR = intrinsic + S (1 - exp(-drive / S)), S = rr_drive_saturation (25, structural); rr_max a safety guard only; RR = 0 without a pulse |
| w | W = efficiency x (RR / intrinsic RR) / (demand / baseline demand): effective alveolar ventilation over the ventilation of the patient's eupnoea at the current CO2 production; 1 at the intrinsic RR with no drive and mechanics preserved. 'Need' is that eupnoeic ventilation: it is eucapnic only when the implied resting PaCO2 is (adversarial review) |
| w_channel | the W channel (C7) is read by no candidate term: RESERVED for future families; the default profile keeps the P2K-1 RR for the frozen records |

**Vías retiradas en la candidata:**
- `d_rr`: NO_DIRECT_PATH: D reaches no RR term; the deficit D integrates also produces the acid burden, an explicit intermediate
- `lactate_rr`: RETIRED_IN_CANDIDATE: no candidate RR term reads lactate (BIOMARKER_PROXY_REQUIRES_REFACTOR resolved for the candidate); the default profile keeps it only for the frozen records
- `w_rr`: RETIRED_IN_CANDIDATE: the candidate RR reads no W channel; W is derived from RR and efficiency and feeds PaCO2 only (SEMANTIC_LEAK removed)

**Estados:** approved = none FACULTY_APPROVED; arrival_tolerance = ARRIVAL_RR_TOLERANCE_PROVISIONAL; bicarbonate_reference = COMMON_REFERENCE_PROVISIONAL; candidates = EXPLORATORY; hypoxaemic_drive = HYPOXEMIC_DRIVE_DEFERRED; lgn = GENERALIZATION_PATH_RESERVED; paco2_reference = COMMON_REFERENCE_PROVISIONAL; rr_drive_saturation = STRUCTURAL_PROVISIONAL; support = FUTURE_GENERALIZATION_REQUIREMENT; ventilation_efficiency = STRUCTURAL_REFERENCE.

**Entradas candidatas de las anclas (fuera del registro de parámetros de caso y de la migración):** `intrinsic_respiratory_rate`, `arrival_bicarbonate`, `arrival_paco2`.

**L, G y N:**
- G: C6 gas exchange: no RR or SpO2 term; a future family may couple it to PaO2 / SpO2 and a hypoxaemic drive
- L: C5 lung water / mechanics: no RR term; a future respiratory family may lower efficiency or load the drive
- N: C9 CNS depression: no RR term; a future family may scale the drive (depressants)

**Soporte:**
- fio2: Oxygen sets FiO2, which moves SpO2 and, through delivery, the deficit, D, lactate and now the acid burden; it touches no drive, RR or W directly
- invasive: NOT_MODELED
- mode: NOT_MODELED
- niv: NOT_MODELED
- override: NOT_A_GI_BLOCKER: no GI scenario ventilates; FUTURE_GENERALIZATION_REQUIREMENT for respiratory families
- peep: NOT_MODELED
<!-- /generado:semantica -->

## 3. Gas de llegada y reconstrucción del pH (generado)

<!-- generado:gas -->
| caso | pH | PaCO2 | HCO3 (banco) | carga ácida de llegada | pH derivado | error |
|---|---|---|---|---|---|---|
| 57m | 7,37 | 31 | 17,3 | 6,7 mEq/L | 7,3696 | −0,0004 |
| 72f | 7,40 | 33 | 19,8 | 4,2 mEq/L | 7,4010 | 0,0010 |

El HCO3 es el que calcula el banco de casos (0,03 × PaCO2 × 10^(pH − 6,1), redondeado a 0,1); el pH derivado usa las mismas constantes. El error está dentro del redondeo del HCO3 (± 0,05 mEq/L, unos ± 0,0013 de pH). Ningún desplazamiento lo corrige. La PaCO2 de llegada es exacta por construcción.
<!-- /generado:gas -->

## 4. Candidatos predeclarados (generado)

<!-- generado:candidatos -->
Predeclared before any clinical respiratory trajectory. Intrinsic RR: the faculty's 12 / 16 / 20, per patient. Drive gain: the exact-arrival solutions over both cases and the intrinsic support, spanned geometrically (1 to 4, ratio sqrt 2, five points), common to both cases. Acid production and clearance: the steady-state burden per unit of deficit B (k x tau) at the arrival anchor A0 / d0, three points, times three clearance constants 60 / 120 / 240 min; k = B / tau. Efficiency 1 (structural reference). 5 x 3 x 3 x 3 x 3 = 405 combinations, factorized: arrival compatibility reads (gain, intrinsic RR) analytically; the burden reads (B, tau) per deficit trajectory; RR, W, PaCO2 and pH are algebraic in the burden. No legacy RR, no outcome-chosen value.

- **FR intrínseca:** 12, 16, 20 rpm por paciente (EXPLORATORY).
- **Ganancia ácido → impulso:** 1,000, 1,414, 2,000, 2,828, 4,000 rpm-equivalentes por mEq/L, común a los dos casos. Ganancias exactas de llegada: 57m 12: 3,06, 57m 16: 1,91, 57m 20: 1,02, 72f 12: 3,89, 72f 16: 2,30, 72f 20: 1,04.
- **Carga estacionaria por unidad de déficit B = k × τ:** 13,4, 19,4, 28,0 mEq/L. Déficits efectivos de llegada: 57m demanda 1: 0,40, 57m demanda 1.1: 0,50, 72f demanda 1: 0,15, 72f demanda 1.1: 0,25.
- **τ ácido:** 60, 120, 240 min; k = B / τ.
- **Eficiencia ventilatoria:** 1,0 (referencia estructural). **Saturación S:** 25 rpm. **Tolerancia de llegada:** ± 3 rpm (ARRIVAL_RR_TOLERANCE_PROVISIONAL).
<!-- /generado:candidatos -->

## 5. Compatibilidad de llegada (generado)

<!-- generado:llegada -->
Combinaciones comunes compatibles (ganancia, FR intrínseca 57m, FR intrínseca 72f): **9 de 45**.

| ganancia | intrínseca 57m | FR llegada 57m | PaCO2 en reposo 57m | intrínseca 72f | FR llegada 72f | PaCO2 en reposo 72f |
|---|---|---|---|---|---|---|
| 1,000 | 20 | 25,9 (−0,1) | 40,1 | 20 | 23,9 (−0,1) | 39,4 |
| 1,414 | 16 | 23,9 (−2,1) | 46,3 | 16 | 21,3 (−2,7) | 43,9 |
| 1,414 | 16 | 23,9 (−2,1) | 46,3 | 20 | 25,3 (1,3) | 41,7 |
| 1,414 | 20 | 27,9 (1,9) | 43,2 | 16 | 21,3 (−2,7) | 43,9 |
| 1,414 | 20 | 27,9 (1,9) | 43,2 | 20 | 25,3 (1,3) | 41,7 |
| 2,000 | 16 | 26,4 (0,4) | 51,1 | 16 | 23,1 (−0,9) | 47,7 |
| 2,828 | 12 | 25,3 (−0,7) | 65,3 | 12 | 21,5 (−2,5) | 59,0 |
| 2,828 | 12 | 25,3 (−0,7) | 65,3 | 16 | 25,5 (1,5) | 52,5 |
| 4,000 | 12 | 28,4 (2,4) | 73,5 | 12 | 24,2 (0,2) | 66,6 |

Entre paréntesis, la diferencia con la FR de autor (26 y 24). PaCO2 en reposo: la que el anclaje implica con W = 1 (PaCO2 de llegada × FR de llegada / FR intrínseca), a eficiencia 1.
<!-- /generado:llegada -->

## 6. Sondas estructurales A–H (generado)

<!-- generado:sondas -->
Synthetic, structural only, on the neutral probe arrival (no deficit) with a declared arrival gas (HCO3 20, PaCO2 36, intrinsic RR 16) and the probe profile (gain 2, B 19.4, tau 120, efficiency 1). A: burden 4 -> 8, oxygenation normal. B: lactate alone raised, burden fixed. C: D alone raised, burden fixed. D: 60 min with no deficit, lactate clearance slowed to 600 min: the burden clears, lactate stays high. E1: efficiency 0.5 in the core at a raised burden; E2: the core's functions with efficiency falling 1 -> 0.5 while the burden rises. F: CO2 production down (demand ratio 0.8), burden fixed. G: CO2 production up (1.25), burden fixed. H: pH from HCO3 and PaCO2 at fixed states. W channel: state W 0 -> +0.5 and -0.5 at a fixed burden. No number here is a candidate or a clinical value.

Llegada de la sonda: carga 4,0, FR 22,8, W 1,43, PaCO2 36,0, pH 7,368.

| sonda | resultado |
|---|---|
| A · sube la carga, oxigenación normal | impulso 8,0 → 16,0, FR 22,8 → 27,8 |
| B · sube sólo el lactato | lactato 1,0 → 5,0; FR sin cambio: sí |
| C · sube sólo D | D 0 → 40; FR sin cambio: sí |
| D · se aclara la carga, el lactato sigue alto | carga 8,0 → 4,8, FR 27,8 → 24,0, lactato 5,0 → 4,6 |
| E1 · eficiencia 0,5 con carga alta | FR 27,8, W 0,87 (≤ 1: sí) |
| E2 · la eficiencia cae de 1 a 0,5 mientras sube la carga | FR 22,8 → 29,8, W 1,43 → 0,93, PaCO2 36,0 → 55,3 |
| F · baja la producción de CO2, carga fija | W 1,43 → 1,78, PaCO2 36,0 → 28,8 |
| G · sube la producción de CO2, carga fija | W 1,43 → 1,14, PaCO2 36,0 → 45,0 |
| H · pH de HCO3 y PaCO2 | carga 10: HCO3 14,0, PaCO2 27,6, pH 7,328; fórmula exacta: sí; menos PaCO2, más pH: sí |
| canal W ± 0,5 | FR sin cambio: sí |
<!-- /generado:sondas -->

## 7. Escenarios clínicos R1–R4 (generado)

<!-- generado:reconstruccion -->
Every unique (scenario, blood set, lactate-side point) of the carried P2J-3 region at its demand and tone gain, as P2K-1 rebuilt it (vascular_tone.rebuild and debt_and_lactate): the effective deficit, D and lactate per minute. The burden is integrated from the deficit with the core's own acid_burden_after_minute for each (B, tau); RR, W, PaCO2 and pH are the core's algebra of the burden at each (gain, intrinsic RR). Validated against full core runs with the candidate declared, where every upstream row also equals the run without it. The P2K-1 RR of the same trajectories, recomputed, equals the P2K-1 record (default-profile non-regression).

Mediana [rango] sobre las trayectorias únicas y los candidatos compatibles en la llegada (FR intrínseca y ganancia de cada caso; B y τ, los nueve pares), a la ganancia de tono intermedia g = 0,5. Eficiencia ventilatoria 1 en todas. Las otras ganancias de tono están en el JSON (§10 da la dependencia).

**R1 · hemorragia sin tratamiento (L1) · 57m · demanda 1** (18 trayectorias; FR intrínseca 12, 16, 20)

| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 26,1 [23,9–28,4] | 11,4 [6,7–26,8] | 6,7 | 17,3 | 1,57 [1,29–2,37] | 31,0 | 7,37 | 4,4 | 60 | 0,40 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 120 | 29,0 [24,0–35,0] | 16,9 [6,8–63,3] | 9,6 [6,8–15,8] | 14,4 [8,2–17,2] | 1,74 [1,30–2,92] | 28,3 [23,9–30,9] | 7,34 [7,13–7,37] | 9,4 [9,2–9,4] | 194 [184–195] | 0,72 [0,63–0,73] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 15 | 26,3 [23,6–29,9] | 12,0 [6,4–31,3] | 6,9 [6,4–7,8] | 17,1 [16,2–17,6] | 1,59 [1,28–2,49] | 30,8 [29,4–31,4] | 7,37 [7,35–7,37] | 4,7 | 73 | 0,44 [0,43–0,44] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 30 | 26,7 [23,5–31,0] | 12,7 [6,3–35,8] | 7,1 [6,3–9,0] | 16,9 [15,0–17,7] | 1,62 [1,28–2,59] | 30,5 [28,1–31,6] | 7,37 [7,34–7,37] | 5,0 | 86 [86–86] | 0,48 [0,46–0,48] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 60 | 27,6 [23,6–32,9] | 13,3 [6,4–44,9] | 7,8 [6,4–11,2] | 16,2 [12,8–17,6] | 1,64 [1,28–2,74] | 29,8 [26,1–31,5] | 7,36 [7,29–7,37] | 6,1 | 118 [115–118] | 0,56 [0,52–0,56] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 90 | 28,1 [23,9–34,1] | 15,5 [6,7–54,1] | 8,6 [6,7–13,5] | 15,4 [10,5–17,3] | 1,67 [1,29–2,84] | 29,0 [24,8–31,0] | 7,35 [7,22–7,37] | 7,5 [7,4–7,5] | 153 [148–154] | 0,64 [0,57–0,65] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |

**R1 · hemorragia sin tratamiento (L1) · 72f · demanda 1** (18 trayectorias; FR intrínseca 12, 16, 20)

| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 23,9 [21,3–25,5] | 8,4 [4,2–16,8] | 4,2 | 19,8 | 1,45 [1,19–2,02] | 33,0 | 7,40 | 3,4 | 20 | 0,15 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 120 | 25,4 [21,0–32,4] | 11,4 [3,9–37,7] | 5,6 [3,9–9,4] | 18,4 [14,6–20,1] | 1,57 [1,18–2,62] | 31,0 [24,9–33,8] | 7,40 [7,34–7,41] | 4,9 [4,6–4,9] | 94 [83–95] | 0,47 [0,38–0,48] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 15 | 23,8 [20,7–25,7] | 8,2 [3,8–17,3] | 4,1 [3,8–4,3] | 19,9 [19,7–20,2] | 1,44 [1,17–2,04] | 33,2 [32,7–34,3] | 7,40 [7,39–7,40] | 3,3 | 25 | 0,19 [0,18–0,19] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 30 | 23,7 [20,2–26,3] | 8,2 [3,5–18,7] | 4,1 [3,5–4,7] | 19,9 [19,3–20,5] | 1,44 [1,16–2,10] | 33,2 [31,8–35,2] | 7,40 [7,39–7,41] | 3,3 | 31 [31–31] | 0,23 [0,21–0,23] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 60 | 23,9 [19,9–28,1] | 8,6 [3,4–23,5] | 4,3 [3,4–5,9] | 19,7 [18,1–20,6] | 1,46 [1,16–2,27] | 32,8 [29,3–35,6] | 7,40 [7,39–7,41] | 3,5 | 47 [45–48] | 0,31 [0,27–0,31] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 90 | 24,6 [20,4–30,3] | 10,2 [3,6–30,0] | 4,8 [3,6–7,5] | 19,2 [16,5–20,4] | 1,51 [1,17–2,46] | 32,0 [26,9–34,8] | 7,40 [7,37–7,41] | 4,0 [3,9–4,0] | 68 [62–69] | 0,39 [0,32–0,40] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |

**R2 · cristaloide (L2) · 57m · demanda 1** (181 trayectorias; FR intrínseca 12, 16, 20)

| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 26,1 [23,9–28,4] | 11,4 [6,7–26,8] | 6,7 | 17,3 | 1,57 [1,29–2,37] | 31,0 | 7,37 | 4,4 | 60 | 0,40 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/181 |
| 120 | 26,7 [22,1–33,1] | 12,5 [5,0–46,3] | 6,9 [5,0–11,6] | 17,1 [12,4–19,0] | 1,59 [1,23–2,76] | 30,7 [25,9–34,4] | 7,37 [7,28–7,39] | 7,8 [7,7–8,1] | 142 [137–153] | 0,49 [0,44–0,57] | cristaloide 400 mL; GR 0,0 U; hemostasia 0/181 |
| 15 | 26,1 [23,3–29,2] | 11,3 [6,1–29,2] | 6,6 [6,1–7,3] | 17,4 [16,7–17,9] | 1,57 [1,27–2,44] | 31,1 [30,1–32,0] | 7,37 [7,36–7,38] | 4,6 | 70 [69–70] | 0,25 [0,23–0,28] | cristaloide 300 mL; GR 0,0 U; hemostasia 0/181 |
| 30 | 25,9 [22,6–29,3] | 10,6 [5,4–29,4] | 6,4 [5,4–7,3] | 17,6 [16,7–18,6] | 1,54 [1,24–2,44] | 31,3 [30,0–33,4] | 7,37 [7,36–7,38] | 4,9 | 77 [76–78] | 0,25 [0,22–0,29] | cristaloide 400 mL; GR 0,0 U; hemostasia 0/181 |
| 60 | 25,7 [21,8–30,2] | 10,5 [4,7–32,5] | 6,2 [4,7–8,1] | 17,8 [15,9–19,3] | 1,53 [1,21–2,52] | 31,6 [29,0–35,2] | 7,37 [7,35–7,39] | 5,7 [5,6–5,7] | 94 [91–98] | 0,32 [0,30–0,38] | cristaloide 400 mL; GR 0,0 U; hemostasia 0/181 |
| 90 | 26,1 [21,8–31,6] | 11,6 [4,7–38,2] | 6,5 [4,7–9,6] | 17,5 [14,4–19,3] | 1,55 [1,21–2,63] | 31,3 [27,5–35,2] | 7,37 [7,32–7,39] | 6,6 [6,5–6,8] | 115 [112–123] | 0,41 [0,37–0,48] | cristaloide 400 mL; GR 0,0 U; hemostasia 0/181 |

**R2 · cristaloide (L2) · 72f · demanda 1** (181 trayectorias; FR intrínseca 12, 16, 20)

| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 23,9 [21,3–25,5] | 8,4 [4,2–16,8] | 4,2 | 19,8 | 1,45 [1,19–2,02] | 33,0 | 7,40 | 3,4 | 20 | 0,15 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/181 |
| 120 | 22,6 [17,0–27,8] | 6,6 [2,0–22,6] | 3,4 [2,0–5,7] | 20,6 [18,3–22,0] | 1,37 [1,10–2,24] | 34,6 [29,7–42,5] | 7,40 [7,34–7,41] | 3,5 [3,0–3,8] | 48 [37–58] | 0,26 [0,21–0,34] | cristaloide 400 mL; GR 0,0 U; hemostasia 0/181 |
| 15 | 23,4 [20,1–25,3] | 7,8 [3,5–16,5] | 3,9 [3,5–4,1] | 20,1 [19,9–20,5] | 1,42 [1,16–2,00] | 33,6 [33,1–35,3] | 7,40 [7,39–7,41] | 3,3 | 23 [22–23] | 0,03 [0,01–0,05] | cristaloide 300 mL; GR 0,0 U; hemostasia 0/181 |
| 30 | 22,6 [18,6–25,0] | 7,0 [2,7–15,8] | 3,5 [2,7–3,9] | 20,5 [20,1–21,3] | 1,38 [1,13–1,97] | 34,5 [33,3–38,5] | 7,40 [7,37–7,41] | 3,3 [3,2–3,3] | 23 [15–24] | 0,03 [0,00–0,06] | cristaloide 400 mL; GR 0,0 U; hemostasia 0/181 |
| 60 | 21,9 [16,7–24,9] | 5,7 [1,8–15,3] | 3,0 [1,8–3,8] | 21,0 [20,2–22,2] | 1,32 [1,09–1,95] | 35,5 [33,5–43,5] | 7,39 [7,33–7,41] | 3,2 [3,0–3,2] | 27 [18–30] | 0,10 [0,08–0,14] | cristaloide 400 mL; GR 0,0 U; hemostasia 0/181 |
| 90 | 22,0 [16,5–25,1] | 5,7 [1,7–16,0] | 3,1 [1,7–4,0] | 20,9 [20,0–22,3] | 1,33 [1,08–1,98] | 35,4 [33,2–44,2] | 7,39 [7,33–7,41] | 3,3 [2,9–3,4] | 35 [25–41] | 0,18 [0,14–0,24] | cristaloide 400 mL; GR 0,0 U; hemostasia 0/181 |

**R3 · GR sin hemostasia · 57m · demanda 1** (18 trayectorias; FR intrínseca 12, 16, 20)

| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 26,1 [23,9–28,4] | 11,4 [6,7–26,8] | 6,7 | 17,3 | 1,57 [1,29–2,37] | 31,0 | 7,37 | 4,4 | 60 | 0,40 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 120 | 21,5 [15,0–25,7] | 4,6 [1,1–18,3] | 2,9 [1,1–4,6] | 21,1 [19,4–22,9] | 1,28 [1,06–2,08] | 37,6 [33,2–54,6] | 7,37 [7,25–7,40] | 3,8 | 4 | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/18 |
| 15 | 26,0 [23,3–29,1] | 11,2 [6,1–28,7] | 6,6 [6,1–7,2] | 17,4 [16,8–17,9] | 1,56 [1,27–2,42] | 31,1 [30,3–32,0] | 7,37 [7,36–7,38] | 4,6 | 69 | 0,22 [0,22–0,23] | cristaloide 0 mL; GR 0,5 U; hemostasia 0/18 |
| 30 | 25,7 [22,3–28,4] | 9,9 [5,1–26,6] | 6,3 [5,1–6,7] | 17,7 [17,3–18,9] | 1,51 [1,23–2,37] | 31,6 [31,0–34,0] | 7,37 [7,37–7,39] | 4,9 | 73 [73–74] | 0,03 [0,03–0,04] | cristaloide 0 mL; GR 1,0 U; hemostasia 0/18 |
| 60 | 23,9 [19,4–27,3] | 8,0 [3,1–23,6] | 4,8 [3,1–5,9] | 19,2 [18,1–20,9] | 1,42 [1,15–2,27] | 33,8 [31,8–40,4] | 7,37 [7,34–7,40] | 5,0 | 30 [29–31] | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/18 |
| 90 | 22,6 [16,8–26,4] | 6,8 [1,9–20,8] | 3,7 [1,9–5,2] | 20,3 [18,8–22,1] | 1,35 [1,09–2,18] | 35,9 [32,5–47,7] | 7,37 [7,29–7,40] | 4,4 | 11 | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/18 |

**R3 · GR sin hemostasia · 72f · demanda 1** (18 trayectorias; FR intrínseca 12, 16, 20)

| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 23,9 [21,3–25,5] | 8,4 [4,2–16,8] | 4,2 | 19,8 | 1,45 [1,19–2,02] | 33,0 | 7,40 | 3,4 | 20 | 0,15 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 120 | 19,4 [13,6–23,4] | 2,6 [0,6–10,5] | 1,6 [0,6–2,6] | 22,4 [21,4–23,4] | 1,17 [1,03–1,71] | 39,1 [35,0–56,2] | 7,37 [7,24–7,41] | 2,1 | 1 | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/18 |
| 15 | 23,3 [20,0–25,2] | 7,7 [3,4–16,2] | 3,8 [3,4–4,1] | 20,2 [19,9–20,6] | 1,41 [1,16–1,99] | 33,7 [33,2–35,5] | 7,40 [7,39–7,41] | 3,3 | 19 [19–20] | 0,00 | cristaloide 0 mL; GR 0,5 U; hemostasia 0/18 |
| 30 | 22,5 [18,5–24,8] | 6,8 [2,7–15,2] | 3,4 [2,7–3,8] | 20,6 [20,2–21,3] | 1,37 [1,13–1,95] | 34,8 [33,5–38,7] | 7,40 [7,36–7,41] | 3,2 | 11 | 0,00 | cristaloide 0 mL; GR 1,0 U; hemostasia 0/18 |
| 60 | 20,7 [16,2–24,3] | 4,7 [1,6–13,4] | 2,6 [1,6–3,4] | 21,4 [20,6–22,4] | 1,27 [1,08–1,87] | 36,5 [34,0–45,3] | 7,39 [7,32–7,41] | 2,8 | 4 | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/18 |
| 90 | 19,8 [14,6–23,9] | 4,0 [1,0–11,8] | 2,0 [1,0–3,0] | 22,0 [21,0–23,0] | 1,22 [1,05–1,79] | 37,6 [34,6–51,3] | 7,38 [7,28–7,41] | 2,4 | 1 | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/18 |

**R4 · manejo definitivo (L3) · 57m · demanda 1** (18 trayectorias; FR intrínseca 12, 16, 20)

| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 26,1 [23,9–28,4] | 11,4 [6,7–26,8] | 6,7 | 17,3 | 1,57 [1,29–2,37] | 31,0 | 7,37 | 4,4 | 60 | 0,40 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 120 | 21,5 [15,0–25,7] | 4,6 [1,1–18,3] | 2,9 [1,1–4,6] | 21,1 [19,4–22,9] | 1,28 [1,06–2,08] | 37,6 [33,2–54,6] | 7,37 [7,25–7,40] | 3,8 | 4 | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 18/18 |
| 15 | 26,0 [23,3–29,1] | 11,2 [6,1–28,7] | 6,6 [6,1–7,2] | 17,4 [16,8–17,9] | 1,56 [1,27–2,42] | 31,1 [30,3–32,0] | 7,37 [7,36–7,38] | 4,6 | 69 | 0,22 [0,22–0,23] | cristaloide 0 mL; GR 0,5 U; hemostasia 0/18 |
| 30 | 25,7 [22,3–28,4] | 9,9 [5,1–26,6] | 6,3 [5,1–6,7] | 17,7 [17,3–18,9] | 1,51 [1,23–2,37] | 31,6 [31,0–34,0] | 7,37 [7,37–7,39] | 4,9 | 73 [73–74] | 0,03 [0,03–0,04] | cristaloide 0 mL; GR 1,0 U; hemostasia 0/18 |
| 60 | 23,9 [19,4–27,3] | 8,0 [3,1–23,6] | 4,8 [3,1–5,9] | 19,2 [18,1–20,9] | 1,42 [1,15–2,27] | 33,8 [31,8–40,4] | 7,37 [7,34–7,40] | 5,0 | 30 [29–31] | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 18/18 |
| 90 | 22,6 [16,8–26,4] | 6,8 [1,9–20,8] | 3,7 [1,9–5,2] | 20,3 [18,8–22,1] | 1,35 [1,09–2,18] | 35,9 [32,5–47,7] | 7,37 [7,29–7,40] | 4,4 | 11 | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 18/18 |

**R4 · manejo definitivo (L3) · 72f · demanda 1** (18 trayectorias; FR intrínseca 12, 16, 20)

| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 23,9 [21,3–25,5] | 8,4 [4,2–16,8] | 4,2 | 19,8 | 1,45 [1,19–2,02] | 33,0 | 7,40 | 3,4 | 20 | 0,15 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/18 |
| 120 | 19,4 [13,6–23,4] | 2,6 [0,6–10,5] | 1,6 [0,6–2,6] | 22,4 [21,4–23,4] | 1,17 [1,03–1,71] | 39,1 [35,0–56,2] | 7,37 [7,24–7,41] | 2,1 | 1 | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 18/18 |
| 15 | 23,3 [20,0–25,2] | 7,7 [3,4–16,2] | 3,8 [3,4–4,1] | 20,2 [19,9–20,6] | 1,41 [1,16–1,99] | 33,7 [33,2–35,5] | 7,40 [7,39–7,41] | 3,3 | 19 [19–20] | 0,00 | cristaloide 0 mL; GR 0,5 U; hemostasia 0/18 |
| 30 | 22,5 [18,5–24,8] | 6,8 [2,7–15,2] | 3,4 [2,7–3,8] | 20,6 [20,2–21,3] | 1,37 [1,13–1,95] | 34,8 [33,5–38,7] | 7,40 [7,36–7,41] | 3,2 | 11 | 0,00 | cristaloide 0 mL; GR 1,0 U; hemostasia 0/18 |
| 60 | 20,7 [16,2–24,3] | 4,7 [1,6–13,4] | 2,6 [1,6–3,4] | 21,4 [20,6–22,4] | 1,27 [1,08–1,87] | 36,5 [34,0–45,3] | 7,39 [7,32–7,41] | 2,8 | 4 | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 18/18 |
| 90 | 19,8 [14,6–23,9] | 4,0 [1,0–11,8] | 2,0 [1,0–3,0] | 22,0 [21,0–23,0] | 1,22 [1,05–1,79] | 37,6 [34,6–51,3] | 7,38 [7,28–7,41] | 2,4 | 1 | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 18/18 |

**R1 · hemorragia sin tratamiento (L1) · 57m · demanda 1,1** (37 trayectorias; FR intrínseca 12, 16, 20)

| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 26,1 [23,9–28,4] | 11,4 [6,7–26,8] | 6,7 | 17,3 | 1,57 [1,29–2,37] | 31,0 | 7,37 | 4,4 | 60 | 0,50 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 120 | 29,8 [24,5–36,1] | 18,9 [7,3–73,0] | 10,8 [7,3–18,2] | 13,2 [5,8–16,7] | 1,80 [1,32–2,97] | 27,4 [23,1–30,4] | 7,32 [6,99–7,37] | 9,0 [8,9–9,1] | 99 [97–100] | 0,82 [0,73–0,83] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 15 | 26,5 [23,9–30,5] | 12,7 [6,7–33,8] | 7,1 [6,7–8,4] | 16,9 [15,6–17,3] | 1,62 [1,29–2,54] | 30,6 [28,6–31,0] | 7,37 [7,34–7,37] | 5,2 | 64 | 0,54 [0,53–0,54] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 30 | 27,2 [23,9–32,0] | 13,7 [6,7–40,2] | 7,5 [6,7–10,1] | 16,5 [13,9–17,3] | 1,65 [1,30–2,67] | 30,1 [27,0–31,0] | 7,36 [7,31–7,37] | 5,8 | 68 | 0,58 [0,56–0,58] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 60 | 28,3 [24,1–33,9] | 14,9 [6,9–52,0] | 8,5 [6,9–13,0] | 15,5 [11,0–17,1] | 1,68 [1,30–2,82] | 29,2 [25,1–30,8] | 7,35 [7,24–7,37] | 6,9 | 77 [77–77] | 0,65 [0,61–0,66] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 90 | 29,0 [24,2–35,0] | 16,9 [7,1–62,8] | 9,6 [7,1–15,7] | 14,4 [8,3–16,9] | 1,74 [1,31–2,91] | 28,3 [23,9–30,7] | 7,34 [7,14–7,37] | 8,0 [7,9–8,0] | 87 [86–88] | 0,73 [0,67–0,75] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |

**R1 · hemorragia sin tratamiento (L1) · 72f · demanda 1,1** (37 trayectorias; FR intrínseca 12, 16, 20)

| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 23,9 [21,3–25,5] | 8,4 [4,2–16,8] | 4,2 | 19,8 | 1,45 [1,19–2,02] | 33,0 | 7,40 | 3,4 | 20 | 0,25 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 120 | 26,4 [21,6–34,4] | 13,5 [4,5–47,2] | 6,6 [4,5–11,8] | 17,4 [12,2–19,5] | 1,65 [1,21–2,77] | 29,5 [23,3–32,7] | 7,40 [7,28–7,41] | 4,4 [4,3–4,4] | 44 [42–45] | 0,56 [0,47–0,58] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 15 | 24,0 [21,1–26,7] | 8,6 [4,1–19,8] | 4,3 [4,1–4,9] | 19,7 [19,1–19,9] | 1,46 [1,19–2,14] | 32,8 [31,2–33,4] | 7,40 [7,40–7,41] | 3,3 | 22 | 0,29 [0,28–0,29] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 30 | 24,1 [21,1–28,0] | 9,0 [4,0–23,1] | 4,5 [4,0–5,8] | 19,5 [18,2–20,0] | 1,47 [1,19–2,26] | 32,5 [29,5–33,5] | 7,40 [7,39–7,41] | 3,3 | 24 | 0,33 [0,31–0,33] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 60 | 24,8 [21,3–30,4] | 10,6 [4,2–30,5] | 5,1 [4,2–7,6] | 18,9 [16,4–19,8] | 1,53 [1,19–2,47] | 31,7 [26,8–33,1] | 7,40 [7,37–7,41] | 3,5 | 30 [29–30] | 0,40 [0,36–0,41] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |
| 90 | 25,7 [21,4–32,6] | 12,2 [4,3–38,6] | 5,8 [4,3–9,7] | 18,2 [14,3–19,7] | 1,60 [1,20–2,64] | 30,7 [24,7–32,9] | 7,40 [7,33–7,41] | 3,8 [3,8–3,9] | 36 [35–37] | 0,48 [0,42–0,49] | cristaloide 0 mL; GR 0,0 U; hemostasia 0/37 |

**R2 · cristaloide (L2) · 57m · demanda 1,1** (444 trayectorias; FR intrínseca 12, 16, 20)

| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 26,1 [23,9–28,4] | 11,4 [6,7–26,8] | 6,7 | 17,3 | 1,57 [1,29–2,37] | 31,0 | 7,37 | 4,4 | 60 | 0,50 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/444 |
| 120 | 27,8 [23,1–34,3] | 14,8 [5,9–56,0] | 8,1 [5,9–14,0] | 15,9 [10,0–18,1] | 1,65 [1,26–2,86] | 29,4 [24,6–32,4] | 7,36 [7,21–7,38] | 8,3 [8,1–8,5] | 87 [84–90] | 0,57 [0,54–0,67] | cristaloide 400 mL; GR 0,0 U; hemostasia 0/444 |
| 15 | 26,3 [23,6–30,0] | 12,1 [6,4–31,9] | 6,9 [6,4–8,0] | 17,1 [16,0–17,6] | 1,60 [1,28–2,50] | 30,8 [29,2–31,5] | 7,37 [7,35–7,37] | 5,1 | 63 | 0,36 [0,32–0,40] | cristaloide 300 mL; GR 0,0 U; hemostasia 0/444 |
| 30 | 26,4 [23,1–30,7] | 12,0 [5,9–34,5] | 6,8 [5,9–8,6] | 17,2 [15,4–18,1] | 1,59 [1,26–2,56] | 30,8 [28,4–32,5] | 7,37 [7,34–7,38] | 5,8 | 66 [65–66] | 0,35 [0,30–0,41] | cristaloide 400 mL; GR 0,0 U; hemostasia 0/444 |
| 60 | 26,6 [22,5–32,1] | 12,4 [5,4–40,7] | 7,0 [5,4–10,2] | 17,0 [13,8–18,6] | 1,60 [1,24–2,67] | 30,7 [26,9–33,6] | 7,37 [7,31–7,38] | 6,7 [6,7–6,8] | 72 [70–73] | 0,42 [0,37–0,49] | cristaloide 400 mL; GR 0,0 U; hemostasia 0/444 |
| 90 | 27,2 [22,6–33,3] | 13,2 [5,4–48,1] | 7,4 [5,4–12,0] | 16,6 [12,0–18,6] | 1,62 [1,24–2,78] | 30,2 [25,6–33,4] | 7,36 [7,27–7,38] | 7,5 [7,4–7,6] | 79 [77–81] | 0,50 [0,45–0,58] | cristaloide 400 mL; GR 0,0 U; hemostasia 0/444 |

**R2 · cristaloide (L2) · 72f · demanda 1,1** (444 trayectorias; FR intrínseca 12, 16, 20)

| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 23,9 [21,3–25,5] | 8,4 [4,2–16,8] | 4,2 | 19,8 | 1,45 [1,19–2,02] | 33,0 | 7,40 | 3,4 | 20 | 0,25 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/444 |
| 120 | 24,1 [19,0–31,0] | 9,2 [2,9–32,3] | 4,4 [2,9–8,1] | 19,6 [15,9–21,1] | 1,48 [1,14–2,51] | 32,6 [26,3–37,5] | 7,40 [7,36–7,41] | 3,7 [3,5–3,9] | 33 [30–36] | 0,34 [0,30–0,43] | cristaloide 400 mL; GR 0,0 U; hemostasia 0/444 |
| 15 | 23,8 [20,7–26,1] | 8,3 [3,8–18,3] | 4,1 [3,8–4,6] | 19,9 [19,4–20,2] | 1,44 [1,17–2,08] | 33,1 [32,0–34,3] | 7,40 [7,39–7,41] | 3,3 | 21 | 0,14 [0,09–0,18] | cristaloide 300 mL; GR 0,0 U; hemostasia 0/444 |
| 30 | 23,4 [19,5–26,2] | 7,9 [3,1–18,5] | 4,0 [3,1–4,6] | 20,0 [19,4–20,9] | 1,42 [1,15–2,09] | 33,5 [31,9–36,6] | 7,40 [7,38–7,41] | 3,2 | 22 [22–23] | 0,13 [0,08–0,19] | cristaloide 400 mL; GR 0,0 U; hemostasia 0/444 |
| 60 | 23,2 [18,2–27,3] | 7,5 [2,5–21,2] | 3,8 [2,5–5,3] | 20,2 [18,7–21,5] | 1,41 [1,12–2,19] | 33,8 [30,4–39,5] | 7,40 [7,36–7,41] | 3,3 [3,2–3,3] | 25 [23–26] | 0,20 [0,15–0,26] | cristaloide 400 mL; GR 0,0 U; hemostasia 0/444 |
| 90 | 23,4 [18,1–29,0] | 8,0 [2,5–26,1] | 4,0 [2,5–6,5] | 20,0 [17,5–21,5] | 1,43 [1,12–2,35] | 33,4 [28,3–39,5] | 7,40 [7,36–7,41] | 3,4 [3,3–3,5] | 28 [26–31] | 0,27 [0,22–0,34] | cristaloide 400 mL; GR 0,0 U; hemostasia 0/444 |

**R3 · GR sin hemostasia · 57m · demanda 1,1** (91 trayectorias; FR intrínseca 12, 16, 20)

| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 26,1 [23,9–28,4] | 11,4 [6,7–26,8] | 6,7 | 17,3 | 1,57 [1,29–2,37] | 31,0 | 7,37 | 4,4 | 60 | 0,50 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/91 |
| 120 | 21,9 [15,4–26,2] | 5,4 [1,3–20,2] | 3,2 [1,3–5,1] | 20,8 [18,9–22,7] | 1,30 [1,06–2,16] | 36,8 [32,6–52,8] | 7,37 [7,26–7,40] | 3,4 [3,1–3,6] | 5 [4–7] | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/91 |
| 15 | 26,3 [23,6–29,9] | 12,0 [6,4–31,6] | 6,9 [6,4–7,9] | 17,1 [16,1–17,6] | 1,60 [1,28–2,50] | 30,8 [29,3–31,4] | 7,37 [7,35–7,37] | 5,1 | 63 | 0,33 [0,32–0,36] | cristaloide 0 mL; GR 0,5 U; hemostasia 0/91 |
| 30 | 26,1 [22,9–30,0] | 11,3 [5,7–31,7] | 6,6 [5,7–7,9] | 17,4 [16,1–18,3] | 1,57 [1,25–2,50] | 31,1 [29,2–32,9] | 7,37 [7,35–7,38] | 5,8 | 65 [65–65] | 0,17 [0,14–0,21] | cristaloide 0 mL; GR 1,0 U; hemostasia 0/91 |
| 60 | 24,7 [20,3–28,2] | 8,8 [3,6–26,0] | 5,4 [3,6–6,5] | 18,6 [17,5–20,4] | 1,45 [1,17–2,35] | 32,7 [31,2–38,6] | 7,37 [7,35–7,40] | 6,2 [6,0–6,4] | 41 [34–47] | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/91 |
| 90 | 23,0 [17,4–27,0] | 7,2 [2,1–22,9] | 4,2 [2,1–5,7] | 19,8 [18,3–21,9] | 1,38 [1,10–2,25] | 34,9 [31,9–45,7] | 7,37 [7,30–7,40] | 4,8 [4,5–5,1] | 15 [12–17] | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/91 |

**R3 · GR sin hemostasia · 72f · demanda 1,1** (91 trayectorias; FR intrínseca 12, 16, 20)

| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 23,9 [21,3–25,5] | 8,4 [4,2–16,8] | 4,2 | 19,8 | 1,45 [1,19–2,02] | 33,0 | 7,40 | 3,4 | 20 | 0,25 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/91 |
| 120 | 19,5 [13,7–23,6] | 2,7 [0,6–11,0] | 1,7 [0,6–2,8] | 22,3 [21,2–23,4] | 1,18 [1,03–1,74] | 38,6 [34,8–55,4] | 7,37 [7,25–7,41] | 1,5 [1,5–1,6] | 1 | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/91 |
| 15 | 23,7 [20,6–25,7] | 8,2 [3,7–17,3] | 4,1 [3,7–4,3] | 19,9 [19,7–20,3] | 1,43 [1,17–2,04] | 33,2 [32,6–34,5] | 7,40 [7,39–7,40] | 3,3 | 21 | 0,06 [0,04–0,08] | cristaloide 0 mL; GR 0,5 U; hemostasia 0/91 |
| 30 | 22,8 [19,0–25,1] | 7,2 [2,9–16,1] | 3,6 [2,9–4,0] | 20,4 [20,0–21,1] | 1,39 [1,14–1,99] | 34,1 [33,2–37,6] | 7,40 [7,37–7,41] | 3,2 [3,1–3,2] | 15 [14–17] | 0,00 | cristaloide 0 mL; GR 1,0 U; hemostasia 0/91 |
| 60 | 21,2 [16,5–24,5] | 5,0 [1,7–14,2] | 2,8 [1,7–3,5] | 21,2 [20,5–22,3] | 1,30 [1,08–1,90] | 36,0 [33,8–44,2] | 7,39 [7,32–7,41] | 2,5 [2,5–2,6] | 5 [5–6] | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/91 |
| 90 | 20,0 [14,8–24,1] | 4,2 [1,1–12,5] | 2,2 [1,1–3,1] | 21,8 [20,9–22,9] | 1,24 [1,05–1,82] | 37,3 [34,3–50,4] | 7,38 [7,28–7,41] | 1,9 [1,9–2,0] | 2 | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 0/91 |

**R4 · manejo definitivo (L3) · 57m · demanda 1,1** (91 trayectorias; FR intrínseca 12, 16, 20)

| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 26,1 [23,9–28,4] | 11,4 [6,7–26,8] | 6,7 | 17,3 | 1,57 [1,29–2,37] | 31,0 | 7,37 | 4,4 | 60 | 0,50 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/91 |
| 120 | 21,9 [15,4–26,2] | 5,4 [1,3–20,2] | 3,2 [1,3–5,1] | 20,8 [18,9–22,7] | 1,30 [1,06–2,16] | 36,8 [32,6–52,8] | 7,37 [7,26–7,40] | 3,4 [3,1–3,6] | 5 [4–6] | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 91/91 |
| 15 | 26,3 [23,6–29,9] | 12,0 [6,4–31,6] | 6,9 [6,4–7,9] | 17,1 [16,1–17,6] | 1,60 [1,28–2,50] | 30,8 [29,3–31,4] | 7,37 [7,35–7,37] | 5,1 | 63 | 0,33 [0,32–0,36] | cristaloide 0 mL; GR 0,5 U; hemostasia 0/91 |
| 30 | 26,1 [22,9–30,0] | 11,3 [5,7–31,7] | 6,6 [5,7–7,9] | 17,4 [16,1–18,3] | 1,57 [1,25–2,50] | 31,1 [29,2–32,9] | 7,37 [7,35–7,38] | 5,8 | 65 [65–65] | 0,17 [0,14–0,21] | cristaloide 0 mL; GR 1,0 U; hemostasia 0/91 |
| 60 | 24,7 [20,3–28,2] | 8,8 [3,6–26,0] | 5,4 [3,6–6,5] | 18,6 [17,5–20,4] | 1,45 [1,17–2,35] | 32,7 [31,2–38,6] | 7,37 [7,35–7,40] | 6,2 [6,0–6,4] | 41 [34–47] | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 91/91 |
| 90 | 23,0 [17,4–27,0] | 7,2 [2,1–22,9] | 4,2 [2,1–5,7] | 19,8 [18,3–21,9] | 1,38 [1,10–2,25] | 34,9 [31,9–45,7] | 7,37 [7,30–7,40] | 4,8 [4,5–5,1] | 15 [12–17] | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 91/91 |

**R4 · manejo definitivo (L3) · 72f · demanda 1,1** (91 trayectorias; FR intrínseca 12, 16, 20)

| min | FR | impulso | carga A | HCO3 | W | PaCO2 | pH | lactato | D | déficit | intervención |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 23,9 [21,3–25,5] | 8,4 [4,2–16,8] | 4,2 | 19,8 | 1,45 [1,19–2,02] | 33,0 | 7,40 | 3,4 | 20 | 0,25 | cristaloide 0 mL; GR 0,0 U; hemostasia 0/91 |
| 120 | 19,5 [13,7–23,6] | 2,7 [0,6–11,0] | 1,7 [0,6–2,8] | 22,3 [21,2–23,4] | 1,18 [1,03–1,74] | 38,6 [34,8–55,4] | 7,37 [7,25–7,41] | 1,5 [1,5–1,6] | 1 | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 91/91 |
| 15 | 23,7 [20,6–25,7] | 8,2 [3,7–17,3] | 4,1 [3,7–4,3] | 19,9 [19,7–20,3] | 1,43 [1,17–2,04] | 33,2 [32,6–34,5] | 7,40 [7,39–7,40] | 3,3 | 21 | 0,06 [0,04–0,08] | cristaloide 0 mL; GR 0,5 U; hemostasia 0/91 |
| 30 | 22,8 [19,0–25,1] | 7,2 [2,9–16,1] | 3,6 [2,9–4,0] | 20,4 [20,0–21,1] | 1,39 [1,14–1,99] | 34,1 [33,2–37,6] | 7,40 [7,37–7,41] | 3,2 [3,1–3,2] | 15 [14–17] | 0,00 | cristaloide 0 mL; GR 1,0 U; hemostasia 0/91 |
| 60 | 21,2 [16,5–24,5] | 5,0 [1,7–14,2] | 2,8 [1,7–3,5] | 21,2 [20,5–22,3] | 1,30 [1,08–1,90] | 36,0 [33,8–44,2] | 7,39 [7,32–7,41] | 2,5 [2,5–2,6] | 5 [5–6] | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 91/91 |
| 90 | 20,0 [14,8–24,1] | 4,2 [1,1–12,5] | 2,2 [1,1–3,1] | 21,8 [20,9–22,9] | 1,24 [1,05–1,82] | 37,3 [34,3–50,4] | 7,38 [7,28–7,41] | 1,9 [1,9–2,0] | 2 | 0,00 | cristaloide 0 mL; GR 2,0 U; hemostasia 91/91 |
<!-- /generado:reconstruccion -->

## 8. Preguntas fisiológicas clave (generado)

<!-- generado:preguntas -->
1. **Hemorragia sin tratamiento:** la carga nunca baja en 13734 de 19305 combinaciones (57m 7938 de 8910; 72f 5796 de 10395); a los 120 min está en o sobre la de llegada en 19032 de 19305. Por par: B/τ 13,4/120: 666 de 2145; B/τ 13,4/240: 666 de 2145; B/τ 13,4/60: 666 de 2145; B/τ 19,4/120: 1767 de 2145; B/τ 19,4/240: 1767 de 2145; B/τ 19,4/60: 1767 de 2145; B/τ 28/120: 2145 de 2145; B/τ 28/240: 2145 de 2145; B/τ 28/60: 2145 de 2145.
2. **Bradipnea precoz de 72f:** caída de la FR en los primeros 30 min en 4599 de 10395 (B 13,4: 3465 de 3465; B 19,4: 1134 de 3465; B 28: 0 de 3465); profundidad 0,00 [0,00–1,54] rpm. Mecanismo: acid clearance A0 / tau above production B / tau x d0 at the arrival deficit (B x d0 < A0); never lactate.
3. **Tras la reanimación (R4):** mayor paso de FR por minuto 0,05 [0,01–0,16] rpm; 15 min después de la hemostasia la FR sigue 5,4 [1,2–15,7] rpm sobre la intrínseca (≥ 1 rpm en 38259 de 38259); a los 120 min, 3,7 [0,6–14,0] rpm sobre la intrínseca. El paso del minuto de la hemostasia no supera a otro minuto en 38259 de 38259. PaCO2 en reposo implícita 47,7 [39,4–73,5] mmHg; a los 120 min la PaCO2 está 8,3 [1,1–39,5] mmHg por debajo de ella y sube hacia ella.
4. **Lactato y FR en sentidos opuestos** al menos un minuto en 259118 de 313794 combinaciones.
5. **FR alta con ventilación efectiva insuficiente:** E1 W ≤ 1 con taquipnea: sí; E2 PaCO2 sube pese a la taquipnea: sí.
<!-- /generado:preguntas -->

## 9. Dependencias de la incertidumbre previa (generado)

<!-- generado:dependencias -->
| magnitud | vía | efecto |
|---|---|---|
| demanda 1,0 / 1,1 | demand -> effective deficit -> acid burden -> drive -> RR / W / PaCO2 / pH | carga a 120 min (mediana), diferencia 0,65 [0,10–1,23] mEq/L |
| ganancia de tono g | g -> T -> output -> delivery -> deficit -> acid burden | carga a 120 min (mediana), dispersión entre g 0,07 [0,01–0,26] mEq/L |
| MAP_set | NONE | P2J-4 rows_equal (654 units): the baroreflex moves only the sympathetic drive; no deficit, burden or RR term reads it |
| ganancia del barorreflejo | NONE | as MAP_set |
| región latente de FC | NONE | HR reaches no output, delivery, deficit, D, lactate or burden (P2I-2AG, P2J-1) |

Se multiplican sólo: demand, tone_gain.
<!-- /generado:dependencias -->

## 10. Identificabilidad (generado)

<!-- generado:identificabilidad -->
| magnitud | clase | detalle |
|---|---|---|
| FR intrínseca 57m | NON_IDENTIFIABLE | valores compatibles: 12, 16, 20 |
| FR intrínseca 72f | NON_IDENTIFIABLE | valores compatibles: 12, 16, 20 |
| ganancia ácido → impulso | NON_IDENTIFIABLE | valores compatibles: 1,000, 1,414, 2,000, 2,828, 4,000 |
| ganancia déficit → ácido | NON_IDENTIFIABLE | no authored observation after arrival |
| τ de aclaramiento ácido | NON_IDENTIFIABLE | no authored observation after arrival |
| carga ácida | WELL_CONSTRAINED | at arrival, exact from the authored HCO3; after arrival it follows (B, tau), which nothing authored reads |
| W / eficiencia ventilatoria | NON_IDENTIFIABLE | efficiency fixed at the structural reference 1 and read by no authored observation (review: the frozen rule); W's absolute scale and the resting PaCO2 follow the intrinsic RR, itself constrained only jointly with the gain; PaCO2 en reposo implícita: 57m 46,3 [40,1–73,5]; 72f 43,9 [39,4–66,6] |

Frozen. Arrival compatibility (+/- 3, provisional) is the only authored respiratory constraint besides the arrival gas: a quantity is WELL_CONSTRAINED when one value is compatible, PARTIALLY_CONSTRAINED when some but not all are, NON_IDENTIFIABLE when every value is or the arrival does not read it; the arrival burden is exact from the authored HCO3. B and tau reach only trajectories with no authored later observation: NON_IDENTIFIABLE from authored data, their trajectory sensitivity reported. The implied resting PaCO2 is reported, never filtered. No best set.
<!-- /generado:identificabilidad -->

## 11. Veredicto (generado)

<!-- generado:veredicto -->
**ACID_BASE_RR_STRUCTURE_READY_FOR_NUMERIC_FACULTY_CALIBRATION**

| criterio | se cumple |
|---|---|
| la carga ácida es un estado explícito que mueve la FR | sí |
| superficie candidata acotada | sí |
| D no llega a la FR candidata | sí |
| impulso, FR y W son distintos | sí |
| el lactato no llega a la FR candidata | sí |
| sin regresión aguas arriba | sí |
| nada aprobado | sí |
| PaCO2 y pH coherentes | sí |
| trayectorias propias de un paciente | sí |
| la FR y W pueden disociarse | sí |

- Validación contra el núcleo: 48 corridas completas con el candidato de validación (ganancia 2,0, intrínseca 16 / 16, B 19,4, τ 120): iguales sí (diferencia máxima 0.0); aguas arriba iguales a la corrida sin la candidata: sí.
- Perfil por defecto: la FR, D, el lactato y el déficit de P2K-1 recalculados iguales al registro: sí; región de P2J-3 recalculada igual: demand_class sí, primary sí, support sí, units sí.
- Prueba AST de las inserciones de P2K-2: `clinical_core/derived.py` sí, `clinical_core/integration.py` sí, `clinical_core/state.py` sí.
- Rechazos: ANALYTIC_REJECTION 0, SIMULATION_REJECTION 0.

**Paquete de decisión que se prepara (sin filtrar):**
- arrival RR compatibility (per gain and intrinsic RR, +/- 3 provisional)
- untreated RR at 120 (R1)
- RR after crystalloid (R2)
- RR after PRBC without haemostasis (R3)
- RR after definitive resuscitation (R4)
- HCO3 / pH / PaCO2 trajectories (R1-R4)
- implied resting PaCO2 per intrinsic RR
<!-- /generado:veredicto -->

## 12. Eficiencia (generado)

<!-- generado:eficiencia -->
P2J-3 recalculado: 1326 trayectorias de sangre y 364 contrafactuales. 5364 trayectorias de déficit reconstruidas una vez; la carga se integra para 9 pares (B, τ) y la FR, W, PaCO2 y pH son álgebra de la carga para los 9 candidatos compatibles en la llegada (de 405 combinaciones posibles, factorizadas). Corridas completas del núcleo: 96 (validación). Barrido cartesiano: no; FR heredada leída: no.
<!-- /generado:eficiencia -->

## 13. Lo que se pide a la docencia

La estructura queda lista para una calibración numérica docente. Ningún valor está elegido, y la superficie tiene
zonas que la docencia debe juzgar antes de filtrar:

1. **FR intrínseca y volumen corriente.**
   - Con W ∝ FR, la recuperación eucápnica pide una FR intrínseca ≈ 20 en los dos casos. Con 12 o 16 la
     reanimación termina en hipercapnia (PaCO2 en reposo 44–74 mmHg).
   - Hay que decidir entre:
     - aceptar la PaCO2 tras la reanimación como observable de la calibración (lo que restringe la FR intrínseca);
     - o autorizar una extensión estructural en la que la ventilación efectiva crezca más que la FR (reclutamiento
       de volumen corriente), con su parámetro propio.
2. **Cota inferior de B.**
   - Si B × d0 < A0, la carga de llegada está por encima de la que sostiene el déficit de llegada y baja al
     principio aunque la hemorragia siga. Ocurre con B = 13,4 en todas las trayectorias y con 19,4 en parte; es la
     bradipnea precoz de 72f.
   - Hay que decidir si «sin tratamiento la carga no baja» es un criterio. Si lo es, B ≥ A0 / d0 en los dos casos
     deja sólo B = 28.
3. **Producción y aclaramiento ácidos (k, τ).**
   - No son identificables con los datos de autor: no hay HCO3, pH ni PaCO2 de autor después de la llegada.
   - Para calibrarlos hacen falta observaciones posteriores o rangos docentes.
4. **Referencias provisionales.**
   - HCO3 de referencia 24 mEq/L y PaCO2 de referencia 40 mmHg. Esta última sólo se usa para una llegada sin gas
     declarado.
   - Las dos siguen siendo COMMON_REFERENCE_PROVISIONAL.
5. **Tolerancia de llegada ± 3 rpm y saturación S = 25 rpm.**
   - Las dos siguen siendo provisionales y estructurales.
   - La ganancia y la FR intrínseca forman una cresta (9 de 45): la llegada sola no las separa.
6. **Paso al perfil por defecto.**
   - La candidata está en el núcleo pero apagada. Ponerla por defecto cambiaría la FR del golden y de los registros
     cerrados, lo que obliga a regenerarlos con su propio encargo.
   - Las tres entradas de las anclas (FR intrínseca, HCO3 y PaCO2 de llegada) entrarían entonces en el registro de
     parámetros de caso y en la compuerta de migración.
7. **Paquete de decisión.**
   - Preparado sin filtrar (§11): compatibilidad de llegada, FR a 120 min sin tratamiento, respuesta al cristaloide,
     a los GR y al manejo definitivo, y trayectorias de HCO3, pH y PaCO2.
   - Que se aplique como filtro es decisión docente.

## 14. Limitaciones

- **Criterios que se cumplen por construcción** (revisión, hallazgo 5):
  - `bounded_surface`: la rejilla de ganancias se construye con las soluciones exactas de llegada de las mismas FR de
    autor.
  - La parte R1 de `patient_like`: B máximo = A0 / d0 máximo, así que la carga no baja al llegar con B = 28.
  - `paco2_ph_coherent`: el HCO3 del banco sale del pH y la PaCO2 de autor, así que el error de pH es sólo redondeo.
  - `nothing_approved` es una constante.
  - Ningún resultado posterior a la llegada entra en un rango.
- **Eficiencia.** Es un campo constante del perfil: dentro de una corrida del núcleo no puede variar. E2 usa las
  funciones del núcleo con una eficiencia que cae, y E1 la usa constante dentro del núcleo.
- **Canal W (C7).** Queda reservado: la candidata no lo lee y nada impide hoy que un contribuyente lo escriba mientras
  la candidata está activa (no hay ninguno en GI).
- **Corridas con la candidata activa.**
  - Si el HCO3 llega a 0, la corrida se detiene (UnresolvedBoundary); no ocurrió.
  - La carga deriva el estado una vez más por minuto, y `derive` calcula y descarta la FR de P2K-1: sólo cuesta
    cómputo.
- **Tuplas de exclusión.** Las prueba su contenido la prueba de P2K-1 (`test_the_exclusion_tuples_hold_exactly_their_p2k1_content`),
  no los mapas de dependencias.

- **Mapa FR → W.**
  - Es proporcional (volumen corriente y espacio muerto constantes) y la eficiencia es 1 en los casos GI.
  - No hay quimiorreflejo de CO2: la PaCO2 no realimenta el impulso. Sólo la carga ácida lo mueve.
- **Demanda.** La relación de demanda es 1 en todos los escenarios GI, así que W no cambia con la producción de CO2.
  Sólo las sondas F y G la mueven.
- **Integración.** La carga se integra un minuto a la vez (Euler, τ ≥ 1) con el déficit del inicio del minuto, el
  mismo que integra D.
- **Validación.** Usa un solo candidato (ganancia 2, intrínseca 16 / 16, B 19,4, τ 120) en 48 corridas completas.
  Los demás candidatos usan las mismas funciones del núcleo sobre las mismas trayectorias de déficit.
- **Identificabilidad.** La regla congelada clasifica cada magnitud por separado: la ganancia y la FR intrínseca
  salen NON_IDENTIFIABLE aunque la llegada restringe su combinación (9 de 45).
- **Extremos.**
  - El pH más bajo es 6,98–7,00, en R1 57m a demanda 1,1 con la combinación más extrema. Es finito y no se rechaza.
  - Sólo se rechaza lo imposible (HCO3 o PaCO2 no positivos) y no hubo rechazos.
- **R3 y R4.** Siguen casi iguales, como en P2K-1: tras las GR el déficit es 0 en los dos.
- **Etiqueta de P2K-1.** La columna «deficit» de sus tablas era la fracción del déficit sobre la demanda (s), no el
  déficit efectivo. P2K-2 usa el déficit efectivo, que es lo que integran D y la carga. P2K-1 está cerrado y no se
  reescribe.
- **Fuera de este paquete.** Sin impulso hipoxémico (HYPOXEMIC_DRIVE_DEFERRED); L, G y N reservados; sin VNI ni
  ventilación mecánica (FUTURE_GENERALIZATION_REQUIREMENT).

## 15. Revisión adversarial

Una revisión independiente de sólo lectura, al final. Cada hallazgo se confirmó con una sonda antes de corregirlo. Los
dos de severidad alta tocaban la maquinaria, no los rangos: se corrigieron en el núcleo y en el módulo, y P2K-2 se
recongeló con los mismos candidatos, reglas y criterios. Luego se repitió una vez la evaluación.

| # | severidad | hallazgo | corrección |
|---|---|---|---|
| 1 | ALTA | La prueba AST no comprobaba la condición de un `If` insertado ni el contenido de lo insertado (valores por defecto, funciones nuevas). Seis mutaciones cambiaban la FR por defecto con la prueba en verde | Sólo se aceptan comprobaciones que lanzan un error, o que actúan bajo exactamente `acid_base_active(profile)` con uno de sus dos cuerpos; el digest AST de todo lo insertado queda fijado; las mutaciones son pruebas de regresión; la validación compara la FR por defecto de `derive` con la de P2K-1 |
| 2 | ALTA | Una eficiencia constante se cancelaba con el anclaje: no movía PaCO2 ni pH, y E1 se contradecía | El anclaje de llegada se lee a la eficiencia de referencia 1 (`REFERENCE_VENTILATION_EFFICIENCY`). E1 comprueba PaCO2 sobre la llegada; los criterios de disociación leen E1, E2 y F. Eficiencia NON_IDENTIFIABLE por la regla congelada |
| 3 | MEDIA | Cinco pines de paquetes cerrados quedaron como constante igual a constante, y `shadow.py` perdió el suyo | Se usa el hash de P2K-1 sólo para los tres archivos probados; el resto, con su hash vivo |
| 4 | MEDIA | W = 1 no es necesidad eucápnica para 6 de los 9 tríos, y `paco2_ph_coherent` no lee trayectorias | Resumen y §13: W = 1 es la eupnea a la FR intrínseca; el veredicto queda condicionado a §13.1 |
| 5 | MEDIA | Varios criterios se cumplen por construcción | §14 |
| 6 | BAJA | 55–56 mmHg y pH 7,24–7,25 eran sólo de 72f | Resumen corregido |
| 7 | BAJA | Los mapas de tuplas no comprueban su contenido | Lo cubre la prueba de P2K-1 que fija ese contenido (§14) |
| 8 | BAJA | Las tres entradas candidatas aceptaban `inf` | Ahora se exige finito y positivo; con prueba |
| 9 | BAJA | Dos W con el mismo nombre; el canal C7 sin guarda | §14 |
| 10 | BAJA | Corte por HCO3 ≤ 0 y cómputo extra | §14 |
