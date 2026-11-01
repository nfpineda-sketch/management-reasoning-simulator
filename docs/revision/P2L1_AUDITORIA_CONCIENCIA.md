# P2L-1 · Auditoría estructural de la conciencia y la respuesta neurológica

- **Fecha:** 2026-11-01. **Rama:** `phase-2-clinical-core-shadow`. **Base:** `2063748` (P2K-5, aceptado y cerrado).
- **Congelamientos:**
  - el primero, `8f36bbb` (digest `a7de4d6c…`), queda en la historia;
  - el vigente es el segundo, `0239dce` (digest `f3ec29e6…`), hecho tras la revisión adversarial y antes de esta corrida.
    Es una **desviación declarada** de la regla de un único congelamiento (§19): en el primero, parte de los criterios
    estaba escrita a mano y dos clases de camino eran erróneas.
  - Antes de cada corrida quedaron fijados la tabla de caminos y sus clases, las sondas, los criterios, la regla del
    veredicto, la estructura mínima y las decisiones pedidas.
  - En ambos, el módulo se ejercitó sobre estados sintéticos mientras se escribía. No hay ninguna regla numérica que
    ajustar.
- **Números:** `docs/revision/P2L1_consciousness_audit.json`. Generador de los bloques:
  `python -m clinical_core.consciousness_audit_report`.
- **Alcance:** sólo sombra y sólo lectura.
  - No cambia ningún archivo del núcleo, canal, regla, umbral ni parámetro.
  - Se leen estados fijos por el núcleo certificado, más 29 pasos sueltos del integrador (el bucle del tono y un
    minuto de D), y registros comprometidos con su hash fijado. No se simula ninguna trayectoria.
  - El motor heredado se cita como texto, nunca se importa ni se ajusta.

## Resumen

- **N hoy** es un marcador sin uso (`UNUSED_PLACEHOLDER`).
  - Vale 0 a la llegada. Sólo lo escriben los constructores de llegada y ningún módulo lo lee: la búsqueda recorre
    recursivamente los 63 archivos de `clinical_core/`, incluido `modules/`.
  - Se serializa con el estado y en la carga en sombra de Contracts v2, siempre en 0, y su guarda es provisional.
  - Su definición declarada («depresión del SNC / estado neurológico») mezcla depresión farmacológica y lesión
    primaria (`MIXED_NEUROLOGIC_CONSTRUCT`). Es más amplia que el concepto docente: estado neurológico primario, lesión
    o reserva.
- **La conciencia observable hoy:**
  - sin pulso es 3;
  - con pulso es el máximo entre el nivel de autoría de llegada, la escalera de PAS (80 / 65) y la de SpO2 (87 / 80).
- **Los caminos causales:**
  - el pulso es un camino causal válido;
  - las escaleras de PAS y SpO2 son artefactos heredados, adoptados de `family_engine`. La PAM llega por la PAS
    (proporcional dentro de un caso): también es artefacto heredado;
  - el nivel de autoría actúa como piso permanente, sin causa ni recuperación: es una fuga semántica;
  - **el déficit efectivo y la demanda llegan al nivel con el signo invertido**, por el bucle del tono: más déficit
    sube el tono y la PAS, y la escalera lee al paciente compensado como menos deteriorado. Con g = 0,5 o 1, y anemia
    o demanda ×2, el nivel pasa de 1 a 0 mientras el déficit crece. Es una fuga semántica;
  - N, D, la glucosa, el pH, la PaCO2 y la FC no llegan a la conciencia;
  - el lactato tampoco: no existe un proxy directo que refactorizar.
- **Doble conteo y ortogonalidad:**
  - la PAM y el déficit son señales distintas con el tono fijo (tono frente a Hb). Se acoplan por la respuesta del
    tono y coinciden en el shock de bajo gasto: una regla aditiva contaría ese shock dos veces y un máximo no.
    Pendiente de la docencia;
  - la SpO2 no se cuenta dos veces en el rango de su escalera: el déficit sistémico empieza recién con SpO2 < 38,8 %
    (gasto y Hb normales). Al revés, el déficit sistémico no ve la hipoxemia cerebral: con la FiO2 de 1 a 0,21, la
    SpO2 baja a 73,3 % con déficit 0. La oxigenación necesita su propia entrada o una medida cerebral del aporte.
    Pendiente de la docencia;
  - la acidemia metabólica y la hipercapnia llegan al mismo pH por señales distintas, y la arquitectura las separa.
    Una hipercapnia compensada de autoría a la llegada es representable (HCO3 32, PaCO2 50, pH 7,429); lo que falta
    es la compensación renal durante el encuentro;
  - la glucosa es ortogonal al shock, pero sólo la escriben los constructores y nadie la lee para la conciencia.
- **La recuperación diferida no es representable** (N9).
  - El observable no tiene memoria: tras la agresión vuelve a «alerta» en cuanto la fisiología se normaliza.
  - D no basta: con un minuto del integrador acumula sólo con déficit (0,25 en el shock; 0 con PAM baja aislada,
    hipoglucemia o hipercapnia) y se repaga en los tiempos del lactato y la FC.
  - Que el estado mental se recupere más despacio que la fisiología es un concepto previo que la docencia debe
    confirmar; las sondas no lo deciden.
  - Si se confirma, falta una memoria común: un estado fisiológico F, distinto de N y de D, o un retraso en la capa de
    observación. Según la parada temprana del encargo, se describe la estructura mínima y no se inventa.
- **Las filas de acidemia extrema** (17 604 combinaciones de unidad y latentes, 57m, demanda 1,1) siguen en la
  región, sin filtrar. Hoy ya salen obnubiladas a los 120 min, pero sólo por el proxy de la PAS (siempre < 65): la
  dirección coincide, la razón no. Las unidades de P2K-5 coinciden con los supervivientes de P2J-3 (1 092 por tono).
- **Veredicto:** `CONSCIOUSNESS_STRUCTURE_NOT_READY - RECOVERY_LAG_STATE_REQUIRED`.
  - Fallan seis criterios, todos calculados desde la evidencia: semántica de N, separación del observable,
    modificadores explícitos, doble conteo, recuperación y generalización.
  - Se cumplen: el lactato no es proxy, la fisiología previa está intacta y no se aprobó nada.
  - **Recomendación:** `STOP_FOR_FACULTY_STRUCTURAL_DECISION`, con la estructura mínima (§16) y las decisiones
    pedidas.

## 1. Decisiones de la docencia (2026-11-01)

<!-- generado:decisiones -->
Decisiones de la docencia (texto congelado, en inglés):

- **closed**: P2K-5 accepted and closed: GI_RESPIRATORY_PHYSIOLOGY_CLOSED_FOR_CURRENT_PHASE and MOVE_FORWARD_TO_CONSCIOUSNESS; no respiratory cycle reopened, the respiratory uncertainty propagated
- **decided**: 2026-11-01
- **early_stop**: if common consciousness physiology needs a genuinely new state: STOP and report the smallest required structure; no arbitrary threshold, GI offset, lactate proxy or legacy matching
- **goals**: separate the primary neurologic state N from the observable consciousness; audit every causal path into mental status; decide which systemic signals should reach it; find the double counting among oxygen deficit, pressure, oxygenation, pH and PaCO2; decide whether a recovery-lag state is structurally required; prepare a minimal common-physiology decision surface; no collapse calibration
- **lactate**: no direct lactate -> consciousness path; a direct use is BIOMARKER_PROXY_REQUIRES_REFACTOR
- **n_concept**: N is the PRIMARY NEUROLOGIC STATE / neurologic injury or reserve, never a container for every systemic cause; observable consciousness is primary N plus relevant systemic modifiers; no shock, acidemia or glucose written into N unless a persistent neurologic consequence is explicitly modeled
- **no_numbers**: no numeric consciousness threshold invented to make a surface; numeric support only when the signals are explicit, no new state is required and the ranges stand without the GI outcomes
- **priority**: a coherent common physiology with explicit plausible uncertainty and no causal contradiction, good enough to migrate other families; not a tighter fit of two GI cases
- **probes**: MAP against deficit, SpO2 against delivery, pH against PaCO2, glucose, recovery lag, N1-N9, the extreme-acidemia subset, a qualitative generalization test and the upstream dependency, each on representative states; no Cartesian product
- **respiratory**: closed: ventilation gain 0.03 / 0.04, intrinsic RR, acid-to-RR gain, B, tau, HCO3 and PaCO2 references not reopened; P2K-5 M-1 is DOCUMENTED_SEMANTIC_DEBT; HCO3_reference 24 COMMON_REFERENCE_PROVISIONAL, g <= 1 / HCO3_reference the general rule for the linear mapping
- **reuse**: BloodState, preload / pump, pressure / tone, DO2 / deficit, D, lactate, HR / baroreflex, acid-base and RR / W / PaCO2 closed for the current GI calibration; reopened only on a direct causal contradiction
- **scope**: shadow only; no runtime integration, migration, consciousness parameter approval, collapse activation or legacy fitting
<!-- /generado:decisiones -->

## 2. N hoy

<!-- generado:n -->
- **Clasificación:** `UNUSED_PLACEHOLDER`; semántica declarada (texto congelado, en inglés): MIXED_NEUROLOGIC_CONSTRUCT: 'CNS depression / neurological state' joins drug-induced depression with primary neurologic injury; the faculty's concept (primary neurologic state / injury or reserve) is narrower.
- **Valor de llegada:** 0,0. **Escrituras:** state.py:697 (sólo los constructores de llegada). **Lecturas** (atributo, subíndice o canal): 0. Archivos examinados, recursivamente en `clinical_core/`: 63. (texto congelado, en inglés) no reader: N is touched only by the generic scalar-channel loops (finiteness, guard, deltas, the shadow payload).
- **Bucles genéricos sobre los canales escalares** (finitud, guarda, deltas, carga en sombra): contracts_output.py:86, integration.py:430, integration.py:515, state.py:611, state.py:651.
- **Serialización** (texto congelado, en inglés): a scalar channel of CoreState: serialized with the state and in the Contracts-v2 shadow payload's channels (contracts_output, always 0), its per-minute delta recorded and guarded by integration (always 0), its bound named in the golden's channel_bounds.
- **Efecto observable:** con N = -5.0: nivel 0, 0.0: nivel 0, 5.0: nivel 0; ningún caso cambia N.
<!-- /generado:n -->

## 3. La ecuación de la conciencia observable

<!-- generado:ecuacion -->
**Ecuación** (texto congelado, en inglés): derived.derive: without a pulse the level is 3 (unresponsive; derived.check enforces it); with a pulse level = max(anchors.consciousness_level, L(SBP), L(SpO2)), L(SBP) = 1 below 80 and 2 below 65 mmHg (profile.pressure_levels), L(SpO2) = 1 below 87 and 2 below 80 % (profile.oxygen_levels), on the raw derived values; ladder 0 alert, 1 drowsy, 2 obtunded, 3 unresponsive

- La línea del código está presente: sí; sin pulso, nivel 3: sí.
- Umbrales de PAS [[80.0, 1], [65.0, 2]] y de SpO2 [[87.0, 1], [80.0, 2]], ambos `adopted` de `family_engine`.
<!-- /generado:ecuacion -->

## 4. Todos los caminos causales

<!-- generado:caminos -->
| entrada | clase | la perturbación mueve el nivel | perturbación | por qué (texto congelado) |
|---|---|---|---|---|
| pulso | camino causal válido | — | — | circulatory arrest -> unresponsive (level 3), an invariant of derive / check |
| PAS | artefacto heredado | sí | tone T 0.45 (vasodilation: output and delivery rise about 20 %, CRT falls; SBP is what moves the level) | thresholds 80 / 65 adopted from family_engine._PRESSURE_LEVELS without its DC1 anchoring or recovery margin; raw SBP, not MAP, stands in for both cerebral perfusion pressure and systemic oxygen delivery |
| SpO2 | artefacto heredado | sí | authored arrival SpO2 82 % (delivery index 1) | thresholds 87 / 80 adopted from family_engine._OXYGEN_LEVELS; SpO2 also enters delivery (delivery_rel = output x Hb ratio x SpO2 ratio), but in the ladder's range the systemic deficit is 0 (with reserve 2.5 it begins only near 39 % at normal output and Hb), so the ladder carries cerebral-hypoxaemia information the deficit lacks: no double count today |
| nivel de autoría de llegada | fuga semántica | sí | authored arrival level 2 with every signal normal | the authored arrival level is a permanent floor, cause-agnostic and never recovered: it holds whatever made the arrival impaired (a primary neurologic state and the arrival's systemic causes alike) |
| N | no modelado hoy | no | N = 5 | the channel exists (an unused placeholder); derive never reads it |
| déficit efectivo de oxígeno | fuga semántica | no; sí, con la respuesta del tono | Hb at 30 % of arrival (SBP kept) | no direct path; with the P2J-2 tone response on (every P2J-3 / P2K calibration, tone gain 0.25-1), the deficit raises tone, tone raises SBP and the SBP ladder reads the patient as less impaired: an indirect path with the sign inverted (tone_loop) |
| D | no modelado hoy | no | D = 600 index-minutes, no deficit | the accumulated oxygen-delivery debt: read by lactate and the sympathetic drive |
| PAM | artefacto heredado | sí | the same state (MAP and SBP move together) | read through SBP: within a case SBP and MAP scale with the same pressure_rel, so the SBP ladder is a pressure ladder (80 / 65 mmHg of SBP), MAP-equivalent up to the case's ratio |
| glucosa | no modelado hoy | no | glucose 30 mg/dL | a state value (C11, absolute, from the case, no writer); read only by the sympathetic drive's hypoglycaemia term (threshold PROVISIONAL) |
| pH | no modelado hoy | no | metabolic acid burden 15 mEq/L (pH about 7.18) | the P2K-2 / P2K-3 respiration candidate's output, read by nothing downstream |
| PaCO2 | no modelado hoy | no | ventilation efficiency 0.6 (PaCO2 about 58 mmHg) | the P2K-3 ventilation candidate's output (PaCO2_reference / W), read by nothing |
| lactato | no modelado hoy | no | lactate excess 8 mmol/L | correctly absent: no direct lactate -> consciousness path exists (no BIOMARKER_PROXY to refactor) |
| FC | no modelado hoy | no | sympathetic drive 40 | correctly absent: the rate never reaches consciousness |
| demanda | fuga semántica | no; sí, con la respuesta del tono | oxygen demand 1.6 with delivery 1 (deficit 0 at reserve 2.5) | demand reaches the deficit and the acid burden; through the tone response and the SBP ladder, sign inverted, like the deficit |

**El bucle del tono** (bomba de partida 0,62, nivel de partida 1, tres minutos del integrador por condición):

| condición | nivel por minuto | PAS por minuto | déficit por minuto | el nivel mejora con más déficit |
|---|---|---|---|---|
| anaemia g0 | 1 → 1 → 1 | 74,4 → 74,4 → 74,4 | 0,225 → 0,225 → 0,225 | no |
| anaemia g0.25 | 1 → 1 → 1 | 74,4 → 77,3 → 77,4 | 0,225 → 0,238 → 0,239 | no |
| anaemia g0.5 | 1 → 0 → 0 | 74,4 → 80,1 → 80,7 | 0,225 → 0,250 → 0,253 | sí |
| anaemia g1 | 1 → 0 → 0 | 74,4 → 85,4 → 87,6 | 0,225 → 0,274 → 0,284 | sí |
| demand_x2 g0 | 1 → 1 → 1 | 74,4 → 74,4 → 74,4 | 0,450 → 0,450 → 0,450 | no |
| demand_x2 g0.25 | 1 → 1 → 1 | 74,4 → 77,3 → 77,4 | 0,450 → 0,476 → 0,477 | no |
| demand_x2 g0.5 | 1 → 0 → 0 | 74,4 → 80,1 → 80,7 | 0,450 → 0,501 → 0,506 | sí |
| demand_x2 g1 | 1 → 0 → 0 | 74,4 → 85,4 → 87,6 | 0,450 → 0,548 → 0,568 | sí |

Inversión con alguna ganancia primaria: sí. (texto congelado, en inglés) with the tone response on, a rising deficit raises tone and SBP, and the SBP ladder reads the compensated patient as less impaired: the deficit reaches the level, with the sign inverted.
<!-- /generado:caminos -->

## 5. PAM frente a déficit efectivo (sondas A–D)

<!-- generado:map_deficit -->
| sonda | nivel | PAS | PAM | DO2 | déficit |
|---|---|---|---|---|---|
| A_low_map_no_deficit | 2 (obnubilado) | 64,7 | 48,5 | 1,198 | 0,000 |
| B2_vasoconstricted_low_output_map_52 | 1 (somnoliento) | 69,7 | 52,3 | 0,323 | 0,194 |
| B_adequate_map_high_deficit_anaemia | 0 (alerta) | 120,0 | 90,0 | 0,300 | 0,250 |
| C_low_map_and_high_deficit | 2 (obnubilado) | 36,0 | 27,0 | 0,300 | 0,250 |
| D_neither | 0 (alerta) | 120,0 | 90,0 | 1,000 | 0,000 |

Las señales distinguen A de B: sí. Hoy A sale deteriorado: sí; B sale alerta: sí.

**Superposición** (texto congelado, en inglés): output lowers both MAP (pressure = output x tone) and delivery; at fixed tone, tone and Hb separate them, but with the tone response on, tone itself follows the deficit (tone_loop), so the two signals are coupled through compensation; in low-output shock (C) they coincide: an additive rule would count that shock twice, a maximum would not
<!-- /generado:map_deficit -->

## 6. Oxigenación frente a aporte (sondas A–C)

<!-- generado:oxigenacion -->
| sonda | nivel | SpO2 | DO2 | déficit |
|---|---|---|---|---|
| A2_fio2_falls_from_1_to_room_air | 2 (obnubilado) | 73,3 | 0,756 | 0,000 |
| A_low_spo2_adequate_delivery | 1 (somnoliento) | 82,0 | 1,000 | 0,000 |
| B_normal_spo2_critical_deficit | 0 (alerta) | 97,0 | 0,250 | 0,375 |
| C_both | 1 (somnoliento) | 82,0 | 0,300 | 0,250 |

SpO2 a la que empieza el déficit sistémico (gasto y Hb normales): 38,8 %; techo de la escalera de SpO2: 87,0 %. Doble conteo en el rango de la escalera: no. El déficit sistémico no ve la hipoxemia: sí.

(texto congelado, en inglés) delivery_rel = output x (Hb / Hb0) x (SpO2 / SpO2_0), arrival-relative; an authored arrival hypoxaemia reaches DO2 only through the case's arrival_delivery_ratio; during the encounter SpO2 moves only with FiO2. no double count today: in the SpO2 ladder's range the systemic deficit is 0 (with the extraction reserve it begins only below the onset SpO2 at normal output and Hb); the converse matters: the systemic deficit misses a cerebral hypoxaemia (SpO2 73 % after FiO2 falls reads deficit 0), so oxygenation needs its own input, or a cerebral delivery measure, beside the deficit; only below the onset would both count the same hypoxaemia
<!-- /generado:oxigenacion -->

## 7. pH frente a PaCO2 (sondas A–D)

<!-- generado:acido_base -->
| sonda | nivel | pH | PaCO2 |
|---|---|---|---|
| A_metabolic_acidemia | 0 (alerta) | 7,179 | 25,0 |
| B_hypercapnia | 0 (alerta) | 7,164 | 57,5 |
| C_both | 0 (alerta) | 6,957 | 41,7 |
| D_neither | 0 (alerta) | 7,386 | 34,5 |

Distingue acidemia metabólica de hipercapnia: sí. Hipercapnia compensada de autoría a la llegada (HCO3 32,0, PaCO2 50,0): pH 7,429, nivel 0; representable: sí. Compensación renal durante el encuentro: no.

(texto congelado, en inglés) metabolic acidemia (burden up, PaCO2 down) and acute hypercapnia (W down, PaCO2 up) reach the same pH by different signals, so the architecture can keep them apart; a compensated chronic hypercapnia is representable when the case authors its HCO3 above the reference (the burden starts at 0), but no renal compensation moves HCO3 during the encounter; neither pH nor PaCO2 reaches consciousness today
<!-- /generado:acido_base -->

## 8. Glucosa

<!-- generado:glucosa -->
| sonda | nivel | glucosa | déficit |
|---|---|---|---|
| normal | 0 (alerta) | 100,0 | 0,000 |
| severe_hypoglycaemia | 0 (alerta) | 30,0 | 0,000 |

El nivel no cambia: sí. (texto congelado, en inglés) Estado: CoreState.glucose (C11, absolute, from the case), guarded 15-350 (ADOPTED); escritores: bands.py:38, legacy_adapter.py:201, state.py:697 (constructors only (anchors, the arrival state, the legacy adapter): no contributor, dextrose or consumption); lector: the sympathetic drive's hypoglycaemia term (threshold PROVISIONAL, TBD).
<!-- /generado:glucosa -->

## 9. Recuperación diferida

<!-- generado:recuperacion -->
- Nivel durante la agresión (gasto 0,3): 2; con la fisiología restablecida (D 600): 0; el retraso queda representado: no. (texto congelado, en inglés) derive reads only the current state and the anchors: the observable has no memory.
- Expectativa (texto congelado, en inglés): FACULTY_PRIOR_CONCEPT: mental status may recover more slowly than instantaneous physiology (to confirm; the probes do not decide it).

| agresión (un minuto del integrador) | D tras un minuto | D cubre la agresión |
|---|---|---|
| deficit_shock | 0,25 | sí |
| hypercapnia | 0,00 | no |
| hypoglycaemia | 0,00 | no |
| low_map | 0,00 | no |
| restored_d600_no_deficit | 590,00 | — |

- D basta: no. Hace falta una memoria nueva: sí (`RECOVERY_LAG_STATE_REQUIRED`). Opciones (texto congelado, en inglés): a physiological auxiliary state (F, distinct from N and D); an observation-layer lag (as the legacy's 30-min counter).
- (texto congelado, en inglés) D accrues only with a deficit: it carries a deficit insult (and repays on the lactate / sympathetic time constant), not a MAP-only, hypoglycaemic or hypercapnic one; using it as neurologic memory would also tie brain recovery to debt repayment

| memoria existente | qué es (texto congelado) |
|---|---|
| D | accumulated oxygen-delivery debt: accrues only while the effective deficit is positive, repays first-order (debt_clearance_tau_min 60, PROVISIONAL, set for lactate and the sympathetic drive); systemic, read by lactate and the sympathetic drive |
| N | the unused placeholder: no writer, no reader, no dynamics |
| aux.collapse_burden | the collapse rule's burden (P2E-3): accrues below an output threshold; off by default |
| aux.lactate_excess_mmol_l | a biomarker: never a neurologic controller (faculty) |
| aux.metabolic_acid_burden | the acid burden: produced by the deficit, cleared with tau_acid; read by RR, W, pH |
| aux.sympathetic_drive | the drive: decays with its own tau; read by the heart rate |
| state.internal | each contributor's own frozen memory (family specific, e.g. a bleed's schedule); not common physiology |
| terminal_since | the arrest minute: a pulse-state record, not a recovery memory |
<!-- /generado:recuperacion -->

## 10. Sondas neurológicas N1–N9

<!-- generado:sondas_n -->
| sonda | qué se aísla | lo esperado | nivel hoy | lo representa la derivación actual | existe la señal | hueco |
|---|---|---|---|---|---|---|
| N1 | normal systemic physiology and normal N | alert | 0 (alerta) | sí | sí | none |
| N2 | isolated primary neurologic injury (N = 5) | impaired by N alone | 0 (alerta) | no | sí | the observable does not read the signal |
| N3 | isolated severe oxygen deficit (Hb 25 %, SBP and SpO2 kept) | impaired by cerebral oxygen under-delivery | 0 (alerta) | no | sí | the observable does not read the signal |
| N4 | isolated very low MAP with adequate delivery (tone 0.45; output rises) | vulnerable from cerebral perfusion failure | 2 (obnubilado) | sí | sí | none |
| N5 | isolated severe metabolic acidemia (burden 15, pH about 7.18) | impaired when severe | 0 (alerta) | no | sí | the observable does not read the signal |
| N6 | acute hypercapnia (efficiency 0.6, PaCO2 about 57) on the probe arrival (HCO3 20) | impaired (hypercapnic encephalopathy) | 0 (alerta) | no | sí | the observable does not read the signal |
| N7 | isolated hypoglycaemia (glucose 30) | impaired, independently of shock | 0 (alerta) | no | sí | the observable does not read the signal |
| N8 | combined low-output shock and acidemia (pump 0.3, burden 15) | impaired, both mechanisms, not counted twice | 2 (obnubilado) | sí | sí | none |
| N9 | physiology restored after a prolonged prior insult (D 600, no deficit) | recovery delayed after the physiology normalizes (the faculty's prior concept, to confirm) | 0 (alerta) | no | no | a common memory (D covers deficit insults only) |
<!-- /generado:sondas_n -->

## 11. Observaciones neurológicas de autoría de los casos GI

<!-- generado:autoria -->
| caso | elemento | valor | fuente | clase |
|---|---|---|---|---|
| 57m | abg | pH 7.37, PaCO2 31, HCO3 17.3, PaO2 91 on FiO2 21% | clinical_cases.py:901 | AUTHORED_OBSERVATION |
| 57m | core_arrival_level | 0 | — | MODEL_DERIVED |
| 57m | dbp | 54 | clinical_cases.py:881 | AUTHORED_OBSERVATION |
| 57m | glucose_mg_dl | 118 | clinical_cases.py:882 | AUTHORED_OBSERVATION |
| 57m | hb_g_dl | 6.7 | clinical_cases.py:900 | AUTHORED_OBSERVATION |
| 57m | lactate_mmol_l | 4.4 | clinical_cases.py:900 | AUTHORED_OBSERVATION |
| 57m | legacy_arrival | Alert | — | LEGACY_REFERENCE |
| 57m | map | 65.3 (derived, not authored) | clinical_cases.py:881 | MODEL_DERIVED |
| 57m | mental_status | Alert | clinical_cases.py:202 | AUTHORED_OBSERVATION |
| 57m | neurological_exam | Awake and oriented, reporting persistent faintness | clinical_cases.py:899 | AUTHORED_OBSERVATION |
| 57m | presentation | A 57-year-old man presents after nearly fainting when standing. He looks pale and says he feels profoundly weak. | clinical_cases.py:885 | AUTHORED_OBSERVATION |
| 57m | sbp | 88 | clinical_cases.py:881 | AUTHORED_OBSERVATION |
| 57m | spo2 | 97 | clinical_cases.py:881 | AUTHORED_OBSERVATION |
| 57m | ausentes | focal_deficits: none stated (72f: 'moving all limbs symmetrically'; 57m: not stated); gcs: not authored; later_neurologic_anchors: none authored; none invented; orientation_detail: only in the examination text | — | — |
| 72f | abg | pH 7.40, PaCO2 33, HCO3 19.8, PaO2 84 on FiO2 21% | clinical_cases.py:930 | AUTHORED_OBSERVATION |
| 72f | core_arrival_level | 0 | — | MODEL_DERIVED |
| 72f | dbp | 62 | clinical_cases.py:910 | AUTHORED_OBSERVATION |
| 72f | glucose_mg_dl | 130 | clinical_cases.py:911 | AUTHORED_OBSERVATION |
| 72f | hb_g_dl | 6.4 | clinical_cases.py:929 | AUTHORED_OBSERVATION |
| 72f | lactate_mmol_l | 3.4 | clinical_cases.py:929 | AUTHORED_OBSERVATION |
| 72f | legacy_arrival | Alert | — | LEGACY_REFERENCE |
| 72f | map | 74.0 (derived, not authored) | clinical_cases.py:910 | MODEL_DERIVED |
| 72f | mental_status | Alert | clinical_cases.py:202 | AUTHORED_OBSERVATION |
| 72f | neurological_exam | Alert, oriented and moving all limbs symmetrically | clinical_cases.py:928 | AUTHORED_OBSERVATION |
| 72f | presentation | A 72-year-old woman presents with worsening fatigue and lightheadedness. She had to stop walking from the waiting room because she felt faint. | clinical_cases.py:914 | AUTHORED_OBSERVATION |
| 72f | sbp | 98 | clinical_cases.py:910 | AUTHORED_OBSERVATION |
| 72f | spo2 | 96 | clinical_cases.py:910 | AUTHORED_OBSERVATION |
| 72f | ausentes | focal_deficits: none stated (72f: 'moving all limbs symmetrically'; 57m: not stated); gcs: not authored; later_neurologic_anchors: none authored; none invented; orientation_detail: only in the examination text | — | — |
<!-- /generado:autoria -->

## 12. El subconjunto de acidemia extrema que se arrastra

<!-- generado:acidemia -->
- Filas con pH < 7,00 sin tratamiento (57m, demanda 1,1): 17 604 de 511 056; pH mínimo 6,961 en el minuto 120 (carga 18,38, déficit 0,835, PaCO2 25,8); marca `CONSCIOUSNESS_COLLAPSE_REVIEW`.

| tono, demanda | PAS a 120 (mín – mediana – máx) | PAM a 120 | minutos bajo 80 | minutos bajo 65 |
|---|---|---|---|---|
| g0.25 x1.1 | 43,8 – 45,8 – 58,6 | 32,5 – 43,5 | 87–97 | 24–56 |
| g0.5 x1.1 | 45,3 – 47,3 – 60,1 | 33,7 – 44,6 | 84–95 | 19–52 |
| g1 x1.1 | 47,7 – 49,6 – 62,4 | 35,4 – 46,3 | 79–92 | 10–46 |

Unidades: tono 0.25: P2K-5 1 092, P2J-3 1 092; tono 0.5: P2K-5 1 092, P2J-3 1 092; tono 1: P2K-5 1 092, P2J-3 1 092 (coinciden: sí; (texto congelado, en inglés) candidate rows (upstream unit x latent combination), not trajectories).

Nivel actual a los 120 min: 2 (obnubilado), PAS máxima 62,4. Alerta plena plausible: no; filtradas: no.

(texto congelado, en inglés) every candidate row of the subset already reads obtunded at minute 120 today, through the SBP proxy alone (untreated SBP at 120 below 65 at every tone gain; the arrival floor is 0 and SpO2 stays at 97); pH 6.96 with a deficit of 0.84 and MAP 32-46 at 120 make full alertness implausible under any plausible consciousness physiology, so the direction agrees but for a proxy reason; the rows are kept and carried, never filtered
<!-- /generado:acidemia -->

## 13. Qué incertidumbre aguas arriba llega a la conciencia

<!-- generado:aguas_arriba -->
| incertidumbre | llega hoy a la conciencia | llegaría con los modificadores candidatos | por qué (texto congelado) |
|---|---|---|---|
| ganancia del barorreflejo | no | no | the same path as MAP_set |
| demanda | yes (through the tone response and SBP, sign inverted) | yes (deficit, acid burden) | demand moves the deficit and the burden; the deficit moves tone and SBP when the tone response is on |
| región latente de FC | no | no | the heart rate reaches no output, pressure or delivery in the core |
| MAP_set | no | no | P2J-4: the baroreflex acts on the heart rate only; the rate never feeds output or pressure |
| latentes respiratorios | no | yes (pH, PaCO2) | B, tau and the ventilation gain move the burden, pH and PaCO2; RR is no consciousness input |
| ganancia de tono g | yes (SBP; it also sets the strength of the inverted deficit path) | yes (deficit through output) | pressure = output x tone; P2J-3's untreated SBP differs by tone gain |

Evidencia por perturbación: demand_moves_level_fixed no, demand_moves_level_with_tone_response sí, hr_moves_level no, sbp_moves_level sí.
<!-- /generado:aguas_arriba -->

## 14. Generalización (cualitativa)

<!-- generado:generalizacion -->
| familia | lo que existe | lo que falta | recuperación |
|---|---|---|---|
| shock distributivo | low tone gives a low MAP with preserved delivery: the MAP path is distinct from the deficit | the observable reads SBP, not MAP | recovery lag missing |
| shock hemorrágico | deficit and MAP exist | the observable reads SBP only, and the compensating tone makes it read a worse deficit as less impairment | recovery lag missing |
| hipercapnia / opioides | acute hypercapnia representable (efficiency, demand); a compensated chronic hypercapnia at arrival when the case authors its HCO3 above the reference | PaCO2 not read; no renal compensation during the encounter; whether N carries a drug's primary CNS depression is a pending decision | recovery lag missing |
| hipoglucemia | glucose state exists, orthogonal to shock | not read; no glucose writer or dextrose in the core | post-hypoglycaemic recovery lag missing |
| lesión neurológica primaria | N exists | no N writer and no N reader | N's own dynamics undefined |
| hipoxemia grave | SpO2 (through FiO2) and DO2 exist | SpO2 moves only with FiO2 (gas exchange G has no writer); the systemic deficit misses cerebral hypoxaemia; the SpO2 ladder is legacy | recovery lag missing |

**Resultado:** `STRUCTURAL_GAP`. (texto congelado, en inglés) no GI-specific term is needed, and every systemic signal a family needs exists or is a family's own writer; the common gap is one recovery memory, which no family can supply
<!-- /generado:generalizacion -->

## 15. Veredicto

<!-- generado:veredicto -->
**Veredicto:** `CONSCIOUSNESS_STRUCTURE_NOT_READY - RECOVERY_LAG_STATE_REQUIRED`.

| criterio | cumple |
|---|---|
| semántica de N explícita | no |
| conciencia observable separada de N (N más modificadores explícitos) | no |
| modificadores sistémicos causales explícitos (sin artefactos ni fugas) | no |
| el lactato no es un proxy | sí |
| doble conteo resuelto | no |
| semántica de recuperación coherente | no |
| arquitectura generalizable | no |
| fisiología previa intacta | sí |
| nada aprobado | sí |

Criterios que fallan: n_semantics_explicit, observable_separated_from_n, causal_modifiers_explicit, double_counting_resolved, recovery_lag_coherent, generalization_plausible.

| doble conteo | estado | hallazgo (texto congelado) |
|---|---|---|
| PAM y déficit | `PENDING_FACULTY` | distinct at fixed tone (tone against Hb or output), coupled through the tone response, coincident in low-output shock: an additive rule counts that shock twice, a maximum does not |
| pH y PaCO2 | `SEPARABLE` | distinct signals (burden against W); not to be collapsed |
| SpO2 y aporte | `PENDING_FACULTY` | no double count in the SpO2 ladder's range (the systemic deficit is 0 down to the onset SpO2); the systemic deficit misses cerebral hypoxaemia, so oxygenation needs its own input or a cerebral delivery measure |

**Recomendación:** `STOP_FOR_FACULTY_STRUCTURAL_DECISION`.
<!-- /generado:veredicto -->

## 16. La estructura mínima que falta y las decisiones pedidas

<!-- generado:estructura -->
**La estructura mínima que falta** (texto congelado, en inglés), descrita y no implementada:

- **arrival**: an arrival impairment of unmodeled cause is carried by N or by a declared arrival cause, never as the arrival value of F (F would let it recover by itself: the inverse of today's permanent floor)
- **dynamics**: first order toward an instantaneous target F*, faster while F* rises than while it falls (two time constants, for a later faculty calibration)
- **memory**: one memory the core lacks, common to every insult: a physiological auxiliary scalar F >= 0 (NEUROLOGIC_FUNCTIONAL_IMPAIRMENT, reversible, distinct from N and from D) or an observation-layer lag (as the legacy's counter); the faculty chooses
- **not_added_here**: no state, parameter, threshold or rule is added in P2L-1
- **observable**: level = the ladder of max(primary N, F); without a pulse 3, as now
- **target**: F* from the causal modifiers combined by maximum, not by sum, so a shock that lowers both MAP and delivery is not counted twice: cerebral perfusion failure (MAP), cerebral oxygen delivery (the effective deficit, and oxygenation as its own input: the systemic deficit with its extraction reserve misses cerebral hypoxaemia), hypoglycaemia (glucose), acidemia (pH) and hypercapnia (PaCO2) as separate inputs; no lactate term; no SBP ladder (it reads compensation as recovery)

**Decisiones que se piden a la docencia** (texto congelado):

1. confirm the prior concept that mental status recovers more slowly than the physiology (N9), and where the memory lives: a physiological state F separate from N and D, or an observation-layer lag
2. retire the SBP and SpO2 ladders as consciousness inputs: with the tone response on, the SBP ladder reads a worse deficit as less impairment
3. the aggregation rule of the systemic modifiers: maximum (no double counting) or additive
4. which modifiers enter: MAP as cerebral perfusion (relative to autoregulation), the effective deficit, oxygenation as its own input, glucose, pH and PaCO2 separately; confirm no lactate path
5. N's semantics: primary injury / reserve only, or also a drug's primary CNS depression (opioids), or a separate pharmacologic channel
6. the authored arrival level: carried by N or a declared arrival cause instead of a permanent floor
7. the carried extreme-acidemia subset once the rules exist (kept, never filtered, today)
8. renal compensation of hypercapnia during an encounter: a respiratory-family question

**Superficie de decisión (sólo estructural):** aggregation: maximum / additive; arrival: N or a declared arrival cause / floor (today); lactate: never; map: enters as cerebral perfusion / does not enter; memory: physiological state F / observation-layer lag; n: primary injury / reserve / plus drug CNS depression / separate channel; oxygenation: its own input beside the deficit / through the deficit only; sbp_spo2_ladders: retired / kept. Numérica: none: P2L-1-11 forbids a numeric surface while a new structure is required.
<!-- /generado:estructura -->

## 17. Eficiencia

<!-- generado:eficiencia -->
- Lecturas de estados fijos sintéticos por el núcleo certificado: 37; pasos del integrador (bucle del tono y un minuto de D): 29; simulaciones de trayectorias: 0; región reconstruida: no; barrido cartesiano: no; motor heredado leído como código: no (sólo citado como texto).
- Registros comprometidos leídos con su hash fijado: P2K5_respiratory_monotonicity.json, P2J3_pressure_tone_filter.json.
<!-- /generado:eficiencia -->

## 18. Limitaciones

- **Alcance de las sondas.**
  - Las sondas usan estados fijos sintéticos (la llegada neutra de `bands.ARRIVAL` y la de P2K-2 para el ácido-base),
    con extremos ilustrativos. Muestran qué lee cada camino, no calibran nada.
  - El bucle del tono parte de una bomba de 0,62 y avanza tres minutos del integrador por condición. Muestra el signo
    del camino, no su tamaño clínico.
  - La hipercapnia se obtiene con una eficiencia ventilatoria de 0,6, posible sólo en sondas sintéticas. La sonda N6 se
    apoya en la llegada de la sonda (HCO3 20).
  - La sonda «tono 0,45» no aísla una sola entrada: también suben el gasto y el aporte y baja el TRC. Lo que mueve el
    nivel es la PAS.
- **La búsqueda de escritores y lectores** es sintáctica (AST): llamadas con palabra clave, `ChannelDelta`, `Drift`,
  `value(...)`, `getattr` y atributos. No sigue alias dinámicos; un `grep` independiente tampoco encontró escritores
  reales de N.
- **El subconjunto de acidemia extrema** se lee de los registros comprometidos. La PAS de P2J-3 es la misma, porque los
  latentes respiratorios no la mueven, y las unidades de P2K-5 coinciden con los supervivientes de P2J-3 en el mismo
  tono y demanda. No se reconstruyeron sus trayectorias.
- **El estado mental de autoría** («Alert») es el valor por defecto del banco, coherente con el examen de autoría.
- **La generalización** es cualitativa: no se calibró ninguna familia.
- **La estructura mínima de §16** es una propuesta para la docencia. Sus parámetros (dos constantes de tiempo y una
  correspondencia por modificador) no tienen valores.
- **El piso de autoría** no se toca: hoy sólo afecta a casos que llegan con la conciencia alterada, y los dos GI llegan
  alerta.

## 19. Revisión adversarial

Una revisión independiente, de sólo lectura, sobre el primer congelamiento (`8f36bbb`). Sus sondas quedaron fuera
del repositorio. Hallazgos y resolución:

- **ALTO-1. El déficit y la demanda sí llegan al nivel, por el bucle del tono.** El perfil de las sondas tenía la
  ganancia del tono en 0. Con g = 1, una anemia lleva la PAS de 74,4 a 85,4 y el nivel de 1 a 0.
  *Resuelto:* sonda `tone_loop`; el déficit y la demanda pasan a fuga semántica (`moves_level_dynamic`), y la fila de
  demanda de §13 dice «sí».
- **ALTO-2. El doble conteo SpO2/aporte estaba fijado a mano y sus propias sondas lo contradecían.** Además, la
  estructura propuesta («oxígeno sólo por el déficit») dejaba alerta una SpO2 de 73 %.
  *Resuelto:* se calcula la SpO2 a la que empieza el déficit (38,8 %); no hay doble conteo en el rango de la
  escalera. La oxigenación queda como entrada propia en la estructura mínima y la cuestión queda pendiente de la
  docencia.
- **MEDIO-1. El veredicto salía por construcción:** siete de nueve criterios eran constantes.
  *Resuelto:* todos se calculan desde la evidencia, el doble conteo lleva su propio estado y se listan todos los
  criterios que fallan. La semántica MIXED ya no cuenta como explícita.
- **MEDIO-2. La «hipercapnia compensada no representable» era falsa.**
  *Resuelto:* es representable a la llegada (HCO3 32, PaCO2 50, pH 7,429). Falta la compensación renal durante el
  encuentro, que se pide como pregunta de la familia respiratoria.
- **MEDIO-3. La búsqueda de N no era recursiva** y no veía `ChannelDelta`, `value`, `getattr`, `Drift` ni `**{...}`.
  *Resuelto:* la búsqueda recorre `clinical_core/` recursivamente y reconoce esas formas. La conclusión no cambia: no
  hay escritores reales.
- **MEDIO-4. Se afirmaba que la PAM no movía el nivel, sin perturbarla.**
  *Resuelto:* se perturba; la mueve por la PAS (artefacto heredado).
- **MEDIO-5. «Hace falta un estado nuevo» estaba sobredicho.**
  *Resuelto:*
  - D se comprueba con un minuto del integrador por tipo de agresión;
  - las memorias existentes incluyen `state.internal` y `terminal_since`;
  - la expectativa de N9 queda como concepto previo que la docencia debe confirmar;
  - el bloqueo pasa a `RECOVERY_LAG_STATE_REQUIRED`, con dos opciones: un estado fisiológico o un retraso en la
    observación.
- **BAJOS.** *Resueltos:*
  - B2 rotulada por su PAM (52);
  - el docstring de la acidemia corregido;
  - la acidemia extrema: PAM 32–46, unidad «combinaciones», `level_120` robusto y coincidencia de unidades comprobada
    en el código;
  - la fila de generalización ya no da por presente la depresión farmacológica en N;
  - en la estructura, la alteración de llegada la lleva N o una causa declarada, nunca F (si no, se recuperaría sola);
  - la prueba del lactato lee toda la expresión del nivel por AST.

  *Quedan como están:* la exclusión de `consciousness_audit.py` en la vista de escritores del tono de P2J-1 (el módulo
  fija T sólo en estados sintéticos de sondas, como `hemodynamic_probes`) y el estado mental de autoría por defecto
  (§18).
- **Revisado y limpio:**
  - el núcleo sin cambios;
  - sin camino directo del lactato;
  - N no se usa como depósito;
  - D acumula sólo con déficit;
  - sin umbral nuevo ni términos GI;
  - la acidemia extrema sin filtrar;
  - el pH y la PaCO2 separados;
  - el registro se reproduce en vivo.
- **La segunda congelación** es una decisión de proceso tomada sin consultar a la docencia: queda declarada aquí y en
  `consciousness_audit.FREEZE`. El registro del primer congelamiento sigue en `8f36bbb`.
