# P2V-1 · Arquitectura mínima del estrés sistémico común

Cambio común, en sombra. Rama `phase-2-clinical-core-shadow`; base `53c2102` (P2U-1 aceptado y cerrado:
`OPIOID_SHADOW_MIGRATION_READY`; P2V-0 aceptado y cerrado: B,
`COMMON_SYSTEMIC_STRESS_WITH_DISTINCT_FAMILY_WRITERS_SUPPORTED`).

P2V-0 mostró que las taquicardias autoradas de la hipoglucemia, el estrés coronario, la fiebre y el dolor no son
déficit de oxígeno, no son deuda D, no son barorreflejo y no son distrés respiratorio, y que el objetivo simpático
común no tiene ninguna entrada que las lleve. Este paquete añade esa entrada y nada más.

- **Cambio común mínimo** (`state.py`, `provenance.py`, `derived.py`, `integration.py`), probado contra `53c2102`:
  - `AuxiliaryState.systemic_stress` (finito, 0 o más, 0 por defecto, sin cota superior) y
    `Anchors.arrival_systemic_stress` (el estado latente de llegada, 0 por defecto): una entrada auxiliar común, nunca
    un canal canónico V/T/P/R/L/G/W/D/N;
  - `provenance.SystemicStressChange`: la interfaz del escritor, aditiva como un `DistressChange`; ninguna familia la
    implementa aquí;
  - `CoreProfile.systemic_stress_to_sympathetic_gain`: el único lector, UNSET (`None`) por defecto. Suma su propia
    ganancia por el estrés absoluto del estado al objetivo simpático de FC, aguas arriba de la saturación común y del
    bloqueo beta. Nada respiratorio lo lee.
- **Dos señales, no una:** el distrés respiratorio de P2T-1 (activación aferente respiratoria / trabajo respiratorio) y
  el estrés sistémico (activación simpática / adrenérgica no respiratoria) quedan separados por decisión docente.
  Ninguno se deriva del otro y ninguno se resuelve desde una FC observada.
- **Análisis:** `clinical_core/systemic_stress.py`, congelado antes de la única evaluación. **Registro:**
  `docs/revision/P2V1_systemic_stress.json`. Este documento se genera desde el registro
  (`clinical_core/systemic_stress_report.py`); el texto fuera de los marcadores es la narrativa.

## 1. Decisiones docentes que rigen

<!-- generado:decisiones -->
- **arrival:** a latent FAMILY_CANDIDATE / CASE MAPPING arrival state constrained by independent authored evidence; never inferred from the HR residual alone
- **classification:** B, COMMON_SYSTEMIC_STRESS_WITH_DISTINCT_FAMILY_WRITERS_SUPPORTED (P2V-0, accepted)
- **glucose:** GLUCOSE_CAN_ANCHOR_FAMILY_STRESS_REGION; NOT GLUCOSE_TO_STRESS_MAPPING_APPROVED
- **hypoglycaemia_term:** the existing sympathetic_per_hypoglycaemia_mg_dl is neither removed nor reinterpreted: it is classified below, unchanged
- **independence:** systemic_stress raises the sympathetic HR drive independently of the oxygen deficit, D, the baroreflex, the respiratory distress, hypoxaemia and hypercapnia
- **magnitudes:** every magnitude UNSET: no gain, no arrival value, no glucose / temperature / pain number
- **reader:** the SYMPATHETIC HR TARGET ONLY: systemic_stress_to_sympathetic_gain, UNSET (None) by default, upstream of the common saturation and of the beta-blockade, never a respiratory reader
- **representation:** non-respiratory central / adrenergic stress activation: an auxiliary common input, never a new canonical V/T/P/R/L/G/W/D/N channel
- **residuals:** a common causal signal, never an observable residual fit: no family-specific bpm term closes an HR residual here
- **scope:** one new common auxiliary input (systemic_stress) and its one sympathetic reader; no anaphylaxis migration, no distributive tone, no clinical calibration, no consciousness integration, no hypoxaemic drive
- **separation:** respiratory_distress and systemic_stress stay TWO independent signals and are never merged: distress = respiratory afferent / work-of-breathing activation; stress = non-respiratory sympathetic / adrenergic activation
- **temperature:** TEMPERATURE_CAN_CONSTRAIN_FAMILY_STRESS_REGION; no universal numeric mapping

- Representa: non-respiratory central / adrenergic stress activation: the sympathetic activation of pain, hypoglycaemic counter-regulation, coronary / ischaemic stress, fever and agitation, which raises the sympathetic HR drive without an oxygen deficit, a debt, a pressure fall or respiratory afferent traffic.
- No representa: the respiratory distress, the oxygen deficit, D, the baroreflex, hypoxaemia, hypercapnia, the respiratory drive, the RR, W, pain itself, the temperature, the glucose, an HR residual solved from the observed HR.
- Estado: aux.systemic_stress: finite, at or above 0, 0 none, no upper bound (no clinical bound is chosen).
- Llegada: Anchors.arrival_systemic_stress: a case / family latent arrival value, 0 by default; refused other than 0 unless the reader is declared.
- Escritor: Contribution.systemic_stress: provenance.SystemicStressChange(amount, source, minute, description); amounts add to the value the minute starts with (the stress has no reference above 0 to scale, so the convention is a channel delta's, as the distress's); a minute that would take it below 0 is refused; refused while the reader is UNSET.
- Cinética del núcleo: none: the integration sums the minute's declared changes only (source core_coupling:systemic_stress); no decay, no coupling, no derivation from any other state.
- Lector simpático: sympathetic target += systemic_stress_to_sympathetic_gain x the absolute stress (never relative to arrival), before max(0, .), then the common saturation and beta-blockade (sympathetic_increment).
- Lector respiratorio: none, by decision: no respiratory function reads the stress (NO_RESPIRATORY_STRESS_READER).
- Observable: no observable reads the stress; the diaphoresis, tremor, pain, fever and agitation descriptors stay authored evidence.
<!-- /generado:decisiones -->

## 2. El camino simpático antes del cambio (P2V-1-1)

La auditoría se hizo leyendo el código, antes de escribir una línea: qué alimenta hoy el objetivo simpático, en qué
orden, qué hace el efector con él y dónde entra el término nuevo.

<!-- generado:camino -->
Términos del objetivo simpático, en el orden en que el código los compone:

1. `profile.acute_deficit_to_sympathetic_gain * acute`
2. `profile.sympathetic_per_pressure_deficit * (1.0 - pressure_rel)`
3. `profile.debt_to_sympathetic_gain * state.D`
4. `profile.sympathetic_per_hypoxaemia_point * hypoxaemia`
5. `profile.sympathetic_per_hypoglycaemia_mg_dl * hypoglycaemia`
6. `if profile.distress_to_sympathetic_gain is not None: profile.distress_to_sympathetic_gain * state.aux.respiratory_distress`
7. `if profile.systemic_stress_to_sympathetic_gain is not None: profile.systemic_stress_to_sympathetic_gain * state.aux.systemic_stress`
8. `baroreflex_drive(pressure_rel, anchors, profile)`
9. `return max(0.0, target)`

Qué expresa cada entrada:

- **acute_deficit:** profile.acute_deficit_to_sympathetic_gain x acute_deficit_signal (absolute: the effective oxygen deficit over the demand; 0 when availability is adequate)
- **baroreflex:** baroreflex_drive(pressure_rel, anchors, profile): the MAP of this state against a declared MAP_set, after the other terms, 0 with the gain off (P2J-4)
- **debt:** profile.debt_to_sympathetic_gain x state.D (absolute: the memory, 0 at D = 0)
- **declared_without_state:** hypercapnia and withdrawal: declared inputs of the same drive with no core state (the docstring); fever, pain and agitation now reach it through the systemic stress, whose arrival value and gain stay UNSET
- **floor:** max(0, .): the drive is never negative (P2D-3)
- **hypoglycaemia:** profile.sympathetic_per_hypoglycaemia_mg_dl x (threshold - glucose now, minus the same at arrival): relative to arrival, so 0 at arrival (classified below)
- **hypoxaemia:** profile.sympathetic_per_hypoxaemia_point x (threshold - SpO2 now, minus the same at arrival): relative to arrival, so 0 at arrival
- **pressure_deficit:** profile.sympathetic_per_pressure_deficit x (1 - pressure_rel), relative to arrival (0 at arrival; 0 in every primary HR calibration since P2I-2AG)
- **respiratory_distress:** profile.distress_to_sympathetic_gain x aux.respiratory_distress (absolute), UNSET by default (P2T-1)
- **systemic_stress:** profile.systemic_stress_to_sympathetic_gain x aux.systemic_stress (absolute), UNSET by default (P2V-1, this package)

Efector común, aguas abajo:

- **beta_blockade:** unconstrained_increment = hr_per_sympathetic_drive x (1 - beta) x drive
- **held_drive:** integration.step: aux.sympathetic_drive = sympathetic_after_minute(before, after), which reads sympathetic_target on the state after the minute and decays toward it; derive reads the held drive, never the target
- **rhythm:** the increment applies to a sinus rate only; in another rhythm the rate is the rhythm's
- **saturation:** sympathetic_increment(drive, base_rate, beta, profile) = reserve x tanh(unconstrained / reserve), reserve = sinus_rate_ceiling_bpm - base_rate

- Punto de inserción: derived.sympathetic_target, after the distress reader and before the baroreflex and the max(0, .) floor: one additive term on the same target, so the common saturation and the beta-blockade stay downstream and are never bypassed.
- Términos añadidos: ['if profile.systemic_stress_to_sympathetic_gain is not None: profile.systemic_stress_to_sympathetic_gain * state.aux.systemic_stress']; retirados: ninguno.
- Lectores del estrés en `derived.py`: sympathetic_target; del ancla de llegada: arrival_state; de la ganancia: __post_init__, arrival_state, sympathetic_target.
- Funciones respiratorias que leen el estrés: ninguna.
- Lectores en `integration.py`: _check_conservation, _check_owned, _systemic_stress_after, step.
- Pasa: sí.
<!-- /generado:camino -->

## 3. Representación y escritor (P2V-1-2 / -3)

<!-- generado:representacion -->
- Campos nuevos: `Anchors` → ['arrival_systemic_stress']; `AuxiliaryState` → ['systemic_stress']; `Contribution` → ['systemic_stress']; `CoreProfile` → ['systemic_stress_to_sympathetic_gain']; `MinuteRecord` → ['systemic_stress'].
- Interfaz del escritor: provenance.SystemicStressChange(amount, source, minute, description), campo `systemic_stress` de la contribución, con la misma forma que provenance.DistressChange (P2T-1) (sí).
- Rastro aditivo de dos escritores: 0,00 → 1,50 → 3,00 → 4,00 → 4,00 → 4,00 → 4,00; cambios por minuto [2, 2, 1, 0, 0, 0]; fuente core_coupling:systemic_stress.
- Rastro con una caída declarada: 0,00 → 1,00 → 2,00 → 3,00 → 2,50 → 2,00 → 2,00.
- Estado por defecto: 0,00; sin cota superior: sí.
- Escritores de familia: ninguno.

Rechazos:

- amount_boolean: sí
- amount_infinite: sí
- amount_nan: sí
- amount_without_description: sí
- amount_without_source: sí
- arrival_without_reader: sí
- boolean_arrival: sí
- change_below_zero: sí
- change_without_reader: sí
- foreign_change_type: sí
- infinite_arrival: sí
- infinite_state: sí
- nan_state: sí
- negative_arrival: sí
- negative_state: sí

- Pasa: sí.
<!-- /generado:representacion -->

## 4. El lector y su ganancia (P2V-1-4)

<!-- generado:lector -->
- Campo nuevo del perfil: ['systemic_stress_to_sympathetic_gain']; UNSET por defecto: sí; en el perfil de sonda: sí.
- UNSET en todos los perfiles comprometidos: acs sí, asthma sí, edema sí, opioid_35m sí, opioid_67f sí, pe sí.
- Declararlo no declara ningún otro lector: sí.
- El alza del objetivo es exactamente la ganancia por el estrés: sí.
- El alza de la FC pasa por el incremento común (saturación y bloqueo beta): sí.
- Con un estrés enorme la FC queda en o bajo el techo sinusal (175,00 lpm): 175,00 lpm, sí; respuesta sublineal: sí.
- Ganancias rechazadas: boolean sí, infinite sí, nan sí, negative sí, zero sí.
- Registro de parámetros: provisional.
- Nota: UNSET (P2V-1): sympathetic drive per unit of the common systemic stress (non-respiratory adrenergic activation), added to the HR target upstream of the common saturation and the beta-blockade; None by default (no reader); it never feeds the respiratory drive and is never solved from an observed HR; SYNTHETIC_ONLY in probes; not approved
- Pasa: sí.
<!-- /generado:lector -->

## 5. Ningún lector respiratorio (P2V-1-5)

La decisión docente es explícita: el estrés alimenta **sólo** el objetivo simpático de FC. La guardia es estructural
(ninguna función respiratoria nombra el estrés) y además numérica (mover el estrés no mueve la FR, W, la PaCO2, el pH
ni la SpO2).

<!-- generado:aislamiento -->
- Funciones respiratorias que leen el estrés: ninguna; en la composición del impulso: no.
- Argumentos de `_composition`: `anchors.arrival_respiratory_distress`, `state.aux.respiratory_distress`.
- Cadena respiratoria fija al mover el estrés: W sí, acid_drive sí, availability sí, distress_drive sí, excitatory_drive sí, excitatory_rr sí, hypoxaemic_drive sí, paco2 sí, ph sí, rr sí, spo2 sí.
- La FC sí se mueve en la misma rejilla: 80,00 → 83,12 → 86,24 → 92,43.
- Guardia de integración: a SystemicStressChange is refused while the reader is UNSET; no respiratory guard reads it (check_distress_respiratory_effect is the distress's, not the stress's).
- Pasa: sí.
<!-- /generado:aislamiento -->

## 6. El término de hipoglucemia existente (P2V-1-6)

<!-- generado:hipoglucemia -->
- Expresión en el código: `max(0.0, profile.hypoglycaemia_threshold_mg_dl - state.glucose) - max(0.0, profile.hypoglycaemia_threshold_mg_dl - anchors.glucose)`; idéntica a la de P2U-1: sí.
- Umbral 70,0 mg/dL, ganancia 0,0100 por mg/dL.
- Clasificación: **CHANGE_TERM**.
- Estado: HYPOGLYCAEMIA_SYMPATHETIC_TERM_IS_A_CHANGE_TERM: sympathetic_per_hypoglycaemia_mg_dl reads the glucose of this state against the glucose at arrival, so it is 0 at arrival whatever the arrival glucose, positive only while the glucose falls further and negative while it recovers (a recovery term). It cannot carry an arrival stress, and it is not the systemic-stress reader. P2V-1 neither removes it nor reinterprets it: it stays exactly as P2U-1 left it, and the two terms are independently addressable.
- Con glucosa de llegada 34: objetivo 0,0000 en la llegada; si sigue cayendo 0,1000; si se recupera a 90 0,0000.
- FC de llegada con glucosa 34 y con glucosa 100: 80,00 y 80,00 lpm (el término no aporta nada en la llegada).
- Ni retirado ni reinterpretado: sí; direccionable aparte del estrés: sí.
- Pasa: sí.
<!-- /generado:hipoglucemia -->

## 7. Sondas estructurales S1–S10 (P2V-1-7)

Toda ganancia y todo valor de estrés aquí es `SYNTHETIC_ONLY`: las sondas prueban la estructura, no calibran nada.

<!-- generado:sondas -->
| Sonda | Qué exige | Pasa |
|---|---|---|
| S1 | systemic stress 0: the HR and every reading are exactly today's, with the reader declared | sí |
| S2 | stress > 0 with the synthetic reader: the sympathetic target (and the HR) rises by its own gain | sí |
| S3 | the RR and the whole respiratory chain are unchanged by the stress | sí |
| S4 | the respiratory distress is unchanged by the stress, and the stress by the distress: two signals | sí |
| S5 | V, T, P, L, G, W and D are not changed directly by a stress change | sí |
| S6 | the beta-blockade attenuates the stress's HR effect through the existing downstream pathway | sí |
| S7 | beta-blockade = 1 suppresses the stress's HR increment, as it does every other drive | sí |
| S8 | the acute deficit, D and the baroreflex stay independently addressable | sí |
| S9 | the distress and the systemic stress compose additively, each through its own gain | sí |
| S10 | with the gain UNSET (the default) every prior behaviour is exact (the P2U-1 core) | sí |

- S2: objetivo 0,0000 → 0,1250 → 0,2500 → 0,5000 y FC 80,00 → 83,12 → 86,24 → 92,43 sobre la rejilla [0.0, 2.5, 5.0, 10.0]; con otra ganancia 0,0000 → 0,5000 → 1,0000 → 2,0000.
- S6 / S7 (bloqueo beta): β 0.0 alza de FC 6,24 lpm (por el incremento sí); β 0.5 alza de FC 3,12 lpm (por el incremento sí); β 1.0 alza de FC 0,00 lpm (por el incremento sí).
- S8: acute_deficit objetivo 0,2500 → con estrés 0,5000; baroreflex objetivo 0,0020 → con estrés 0,2520; debt objetivo 0,0400 → con estrés 0,2900; hypoxaemia_arrival objetivo 0,0000 → con estrés 0,2500; neutral objetivo 0,0000 → con estrés 0,2500.
- S9: base 0,0000, sólo distrés 0,2500, sólo estrés 0,2500, juntos 0,5000 (aditivo sí); la FR sólo la mueve el distrés: sí.
<!-- /generado:sondas -->

## 8. Contrastes de casos (P2V-1-8 a -12)

Contrastes estructurales contra la verdad autoral transcrita. Ningún caso se mapea aquí y ningún estrés de llegada se
elige: la columna «Estrés de llegada» dice `UNSET` en todos.

Cómo leer la columna «Banda común» y la diferencia (revisión, R-F4): la banda es la banda intrínseca común
(`gi_reference.RESTING_HR` = 60 / 80 / 100), acotada por la FC observada; **no** es una evaluación del modelo caso por
caso. La diferencia es, por tanto, lo mínimo que queda sin explicar: lo que el modelo deja cuando se le concede la
frecuencia intrínseca más favorable que la banda admite. Verificado en las pruebas evaluando el modelo en ese borde:
hypoglycemia_28m no alcanza 112 ni en 100 (12 lpm sin explicar), renal_colic_34m alcanza 94 exacto con estrés 0 (nada
forzado), pneumonia_46f 18 y pneumonia_83m 8. Con la sonda de los contrastes (intrínseca 80, el punto medio) la
diferencia es mayor: 32, 14, 38 y 28 lpm respectivamente.

<!-- generado:contrastes -->
| Caso | FC autoral | Banda común | Diferencia (lpm) | Estado | Estrés de llegada |
|---|---|---|---|---|---|
| hypoglycemia_28m | 112 | [60.0, 100.0] | 12,00 | FAMILY_CANDIDATE / REGION UNSET | UNSET |
| acs_70f_left_main | 112 | modelo 91,84 | 20,16 | FAMILY_CANDIDATE / REGION UNSET | UNSET |
| renal_colic_34m | 94 | [60.0, 94.0] | 0,00 | COMPATIBILITY / POSSIBLE WRITER | UNSET |
| pneumonia_46f | 118 | [60.0, 100.0] | 18,00 | NOT_SEPARABLE / STRUCTURAL_ONLY | UNSET |
| pneumonia_83m | 108 | [60.0, 100.0] | 8,00 | NOT_SEPARABLE / STRUCTURAL_ONLY | UNSET |
| anaphylaxis_63m_betablocked | 64 | FA, sin vía sinusal | — | BETA_BLOCKADE_GUARD | UNSET |

- **hypoglycemia_28m:** the authored HR 112 sits above the whole intrinsic band with no deficit, no debt, no pressure fall and no respiratory distress, and the existing hypoglycaemia term is 0 at arrival: the gap needs a common non-respiratory input. Its size is not a calibration and no value is chosen here. Evidencia independiente: measured glucose 34 mg/dL; marked diaphoresis; tremor reported before the confusion; warm extremities with CRT 2 and lactate 1.7 (no shock); SpO2 98 (no hypoxaemia); normal work of breathing. Términos de shock en la llegada: entrega 1,000, D 0,000, objetivo 0,000.
- **acs_70f_left_main:** the residual is non-respiratory (marked diaphoresis and ischaemic stress, with the shock terms already carried by the deficit and D). Closing it with the distress reader would take the RR far past the authored 26, so the respiratory signal must not absorb it; the stress reader leaves the RR untouched. No value is chosen. Cerrar el residual con el distrés exigiría 17,12 unidades y llevaría la FR a 33,20 (autoral 26; +7,67 sobre la misma sonda).
- **renal_colic_34m:** the authored HR 94 is inside the intrinsic sinus band with no autonomic markers (diaphoresis absent, MAP above normal, lactate 1.4), so the architecture needs no stress here: pain is COMPATIBLE with a writer and forces nothing. A pain -> stress number is not approved and not proposed.
- **neumonía:** both cases carry several candidate contributors at once, so a stress value fitted to the HR gap would be an identifiability failure, not physiology. The temperature can only CONSTRAIN a family region (TEMPERATURE_CAN_CONSTRAIN_FAMILY_STRESS_REGION); no universal temperature -> stress mapping exists. Contribuyentes posibles: fever; sepsis / hypoperfusion (CRT 4, lactate above 3); hypoxaemia; respiratory distress (RR and work of breathing).
- **anaphylaxis_63m_betablocked:** a beta-blocked patient in AF at 64 is the structural guard: whatever the stress, the sympathetic target rises and the rate does not, because the beta-blockade is downstream and a non-sinus rate is the rhythm's. The architecture cannot manufacture tachycardia, which is what a residual fit would have done. En FA la frecuencia es la del ritmo (sí); con bloqueo completo la FC no se mueve (sí) aunque el objetivo sí (sí). No implementado: anaphylaxis family writer, distributive tone physiology, epinephrine, an anaphylaxis arrival mapping.

- SYNTHETIC stress and gains against the authored truth; no case is mapped, no arrival value is calibrated and nothing is approved. Pasa: sí.
<!-- /generado:contrastes -->

## 9. Metodología de la región de llegada (P2V-1-13 / -14)

Alcance de la guardia de literales (revisión, R-F2): el escaneo del módulo sólo ve palabras clave con literal, así que
la lista que sigue **no** es todo lo que el estrés recibe: las sondas lo escriben también por constantes con nombre
(`PROBE_STRESS` = 5, `STRESS_GRID` = 0 / 2,5 / 5 / 10, `STRESS_STEP` = 1/min), todas `SYNTHETIC_ONLY` y declaradas. Una
constante con nombre, una tabla o una fórmula serían invisibles a esa guardia; lo que lo cierra es la prueba que fija
todas las expresiones que escriben el estrés en los dos archivos del paquete, no esta lista.

<!-- generado:metodologia -->
1. The arrival systemic stress is a latent FAMILY_CANDIDATE / CASE MAPPING state: part of a case's arrival mapping when its family is migrated, never a canonical channel and never a number read off the HR.
2. It may be declared only where INDEPENDENT authored evidence constrains it: a measured metabolic cause (glucose), autonomic markers (diaphoresis, tremor), an ischaemic or painful stimulus, fever, agitation. The observed HR is not evidence for its own explanation.
3. The evidence constrains a REGION, not a point: a non-empty interval of arrival values compatible with every authored observable of that case, as P2S-3, P2T-3 and P2U-1 did for their own latent states.
4. The HR may be used only to TEST a region (is it empty? does it overshoot the authored HR?), never to generate the value: a region solved from the residual is a fit, not physiology.
5. Where the authored evidence does not separate the stress from another candidate contributor (fever vs sepsis vs respiratory stress), the case stays NOT_SEPARABLE and no region is proposed.
6. No universal lookup table, in any direction: no glucose -> stress number, no temperature -> stress number, no pain descriptor -> stress number. A family may anchor its own region; the anchor is not a formula.
7. Every magnitude stays UNSET until the faculty approves one. The AI proposes a method and a region; it never approves a value, and it never fits one to an observable.

Estado de cada ancla:

- **autonomic_markers:** diaphoresis, tremor and agitation are ordinal authored evidence: they constrain a region's ordering, never its magnitude
- **glucose:** GLUCOSE_CAN_ANCHOR_FAMILY_STRESS_REGION (approved as an anchor of a family region); GLUCOSE_TO_STRESS_MAPPING_APPROVED = False (no universal numeric mapping)
- **hr_residual:** NEVER_AN_ANCHOR: the residual tests a region, it never generates one
- **pain:** COMPATIBILITY only: a pain descriptor may justify a writer in a migrated family; it forces no value and maps to no number (renal_colic_34m is the control)
- **temperature:** TEMPERATURE_CAN_CONSTRAIN_FAMILY_STRESS_REGION (approved as a constraint on a family region); no universal numeric mapping

- Mapeos aprobados: glucose no, pain no, temperature no.
- Literales numéricos que este paquete escribe en el estrés: 1.0, 10000.0, 1000000.0, True (sondas de rechazo y de saturación).
- Ningún caso lleva valor: sí; la verdad autoral transcrita no lleva estrés: sí.
- no function here maps an authored observable to a stress value; the only numeric literals the stress ever receives are the refusal and saturation probes.
- Pasa: sí.
<!-- /generado:metodologia -->

## 10. Estado de los parámetros (P2V-1-15)

<!-- generado:parametros -->
- **arrival_systemic_stress:** UNSET (0.0 in every committed arrival mapping): no case carries an arrival stress
- **glucose_to_stress:** UNSET and not approved (no mapping)
- **pain_to_stress:** UNSET and not approved (no mapping)
- **systemic_stress_to_sympathetic_gain:** UNSET (None): no systemic-stress reader is declared in any committed profile; the probe gains here are SYNTHETIC_ONLY
- **temperature_to_stress:** UNSET and not approved (no mapping)
- **upper_bound:** UNSET by decision: the stress has no clinical ceiling (0 is none)
- **writer_rates:** UNSET: no family writer exists, so no rate of rise or resolution is declared

- En el registro de parámetros: sí, estado provisional.
- Entrada candidata fuera del registro de parámetros de caso: sí (arrival_systemic_stress).
- Ganancias comprometidas: acs None, asthma None, edema None, opioid_35m None, opioid_67f None, pe None.
- Estrés de llegada comprometido: acs 0,00, asthma 0,00, edema 0,00, opioid_35m 0,00, opioid_67f 0,00, pe 0,00.
- Valores sintéticos de las sondas (SYNTHETIC_ONLY, no aprobados): arrival_debt = 4.0, baroreflex_gain = 0.02, baroreflex_map_set = 100.0, deficit_delivery = 0.3, other_gain = 0.2, probe_stress = 5.0, stress_grid = [0.0, 2.5, 5.0, 10.0], stress_step = 1.0, sympathetic_gain = 0.05.
- Pasa: sí.
<!-- /generado:parametros -->

## 11. Deudas llevadas de P2T-5 y P2U-1 (P2V-1-17 / -18)

Nota de lectura sobre `OPIOID_HR_FAMILY_GAP`: P2U-1 midió la brecha contra el **borde** de la banda del modelo
(67f: −1,89 lpm bajo 63,89). El registro de P2V-1 la vuelve a medir contra el **mapeo comprometido** (el punto
medio: 65,89), así que lee −3,89 lpm en el 67f y −3,33 en el 35m. Es la misma brecha con otra referencia, y en
las dos lecturas sigue abierta: P2V-1 no añadió ningún escritor de estrés opioide ni ningún término de FC.

<!-- generado:deudas -->
- **HYPOXEMIC_FEEDBACK_STABILITY_AUDIT_DEFERRED** (de P2T-5): DEFERRED, untouched. the hypoxaemic respiratory drive stays UNSET and unactivated; P2V-1 adds no feedback and the stress never feeds the respiratory drive, so the audit stays deferred to its own package.
- **OPIOID_ARRIVAL_AVAILABILITY_UNSET** (de P2U-1): FAMILY_CANDIDATE / REGION. the arrival central availability stays a region per carried intrinsic RR (35m 0.30-0.50, 67f 0.40-0.67); no value is chosen.
- **OPIOID_HR_FAMILY_GAP** (de P2U-1): CARRIED, NOT PATCHED. the authored HR of opioid_67f stays below the model's band. P2V-1 adds no opioid stress writer and no opioid HR term: a common input exists now, but using it to close this gap would be the residual fit the methodology forbids.
- **P2T5_LATENT_PAO2_PHYSICAL_FLOOR** (de P2T-5): NOT_REQUIRED_BY_P2V1. the latent PaO2 floor max(0, .) would be declared PHYSICAL_FLOOR only if a live implementation forced the decision. P2V-1 touches no oxygenation code and no P2T-5 file, so nothing is decided and P2T-5 is not modified for it.
- **P2T5_R_CLINICAL_UNSET** (de P2T-5): UNSET. the respiratory quotient stays UNSET in every committed profile; 0.8 remains SYNTHETIC_PHYSIOLOGIC_REFERENCE and is used only in probes.
- **STEADY_STATE_W_ARRIVAL_TENSION** (de P2U-1): ACCEPTED_MODELING_DEBT / NOT_A_PHASE2_BLOCKER. carried as the faculty accepted it: the arrival efficiency the algebraic PaCO2 reads against the carried intrinsic RR is not resolved here and does not block Phase 2.

- Enlace de P2T-5 UNSET en los perfiles comprometidos: sí; impulso hipoxémico UNSET: sí; archivos de P2T-5 intactos: sí.
- Brecha de FC opioide, sin parchear: opioid_35m autoral 68 vs modelo 71,33 (−3,33 lpm); opioid_67f autoral 62 vs modelo 65,89 (−3,89 lpm).
- Ningún escritor de estrés en las familias: sí.
- Pasa: sí.
<!-- /generado:deudas -->

## 12. No regresión por defecto (P2V-1-16)

<!-- generado:no_regresion -->
- Registro de P2U-1 reproducido sobre su árbol: sí (anida P2T-5, P2T-3, P2T-1A, P2T-1, P2S-3, P2S-2 y, por ellos, opioides, asma, TEP, edema, SCA y GI); intacto sí; su veredicto OPIOID_SHADOW_MIGRATION_READY.
- Estrés de llegada 0 en los perfiles comprometidos: sí.
- Tuplas de registro: DOWNSTREAM_REPORTS sí, PACK_DIGEST_EXCLUDED sí.
- Pasa: sí.
<!-- /generado:no_regresion -->

## 13. Prueba contra el árbol de P2U-1

<!-- generado:prueba -->
- Archivos revertidos a los de P2U-1: `clinical_core/decision_pack.py` sí, `clinical_core/derived.py` sí, `clinical_core/integration.py` sí, `clinical_core/lactate_slice.py` sí, `clinical_core/provenance.py` sí, `clinical_core/state.py` sí.
- Archivos comunes fijados por hash: 127, intactos sí.
- Vista de P2U-1: digest sí, su prueba sí, registro sí.
<!-- /generado:prueba -->

## 14. Veredicto (P2V-1-19)

<!-- generado:veredicto -->
- sí — the architecture is minimal and declared: one auxiliary field, one arrival anchor, one writer record, one gain, with their refusals (representation, reader audit)
- sí — the reader feeds the sympathetic HR target only: no respiratory function reads the stress and the whole respiratory chain is unchanged by it (S3, isolation)
- sí — the respiratory distress and the systemic stress stay two independent signals and compose additively (S4, S9)
- sí — the common effector is untouched: the stress enters upstream of the saturation and of the beta-blockade and never bypasses them (S2, S6, S7)
- sí — the other sympathetic terms stay independently addressable and the existing hypoglycaemia term is unchanged and classified (S8, the hypoglycaemia audit)
- sí — every magnitude stays UNSET and no observable is mapped to a stress number (the parameter state, the arrival methodology, every contrast UNSET)
- sí — the case contrasts hold structurally, the negative control forces nothing and the beta-blockade guard holds (the five contrasts)
- sí — nothing prior changes by default: with the gain UNSET every prior reading is exact and P2U-1's record reproduces on its tree (S1, S10, the non-regression, the proof)

**Veredicto: COMMON_SYSTEMIC_STRESS_ARCHITECTURE_READY**
<!-- /generado:veredicto -->

## 15. Límites y lo que NO se hizo

- No se migró la anafilaxia: no hay escritor, ni mapeo de llegada, ni epinefrina.
- No se implementó fisiología de tono distributivo.
- No se calibró el estrés sistémico: la ganancia, el valor de llegada y toda magnitud quedan `UNSET`.
- No se mapeó ningún observable a un número de estrés: ni glucosa, ni temperatura, ni dolor.
- No se integró la conciencia ni se activó el impulso hipoxémico.
- El estrés no tiene cinética propia en el núcleo: sin escritor de familia, no hay tasa de subida ni de resolución.
- Ninguna FC autoral se cerró con un término de familia: los residuales se informan, no se absorben.

## 16. Qué sigue (propuesta, decide la docencia)

La IA propone; la persona docente decide. Orden sugerido si el veredicto es `READY`:

1. **P2W-0:** auditoría de sólo lectura de la composición del tono distributivo y de los escritores de T (la expectativa
   por defecto: auditar la composición de T antes de migrar la anafilaxia).
2. Migración en sombra de la anafilaxia.
3. Preparación de la integración de la conciencia.
4. Otra familia ortogonal.
