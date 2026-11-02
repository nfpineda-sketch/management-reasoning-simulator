# P2M-1 · Auditoría estructural de colapso y paro

**Rama:** `phase-2-clinical-core-shadow` · **Base:** `b9e4913` (P2L-2 cerrado) · **Congelamiento:** `033c272` (digest `c4aa95f6…`) · **Fecha:** 2026-11-02

Sólo sombra y sólo lectura. Un módulo de auditoría (`clinical_core/collapse_audit.py`) que no cambia ningún archivo del núcleo, no escribe canales, no agrega reglas, umbrales ni parámetros y no activa nada: el colapso sigue apagado. Las secciones generadas salen del registro `docs/revision/P2M1_collapse_audit.json` (`collapse_audit_report`).

## Resumen

**Veredicto congelado: `COLLAPSE_STRUCTURE_READY_FOR_FACULTY_DECISION`**, con estructura mínima
`DERIVED_COLLAPSE_SIGNAL_ONLY_REQUIRED`. **La revisión adversarial lo contradice en parte.** Dos criterios congelados
(`redundancy_resolved` y `persistence_classified`) se apoyaban en la elección de las sondas, y la estructura reutilizada
tiene un defecto que el criterio de orden no veía. No se recongeló: el registro sigue siendo el de `c4aa95f6`, y la
contradicción queda señalada para que la docencia decida (decisión 17). **Lectura corregida:** la estructura es
explícita y queda lista para decidir, pero el mínimo incluye también la forma de la persistencia y tres invariantes.
Nada se implementa, se activa ni recibe un valor.

- **El pulso es estado de ritmo, no de presión.** Es un campo de R, atado al código del ritmo, y sólo lo cambian
  transiciones de ritmo: un evento guionizado o la regla P2E-3.
  - Sin pulso nunca hay flujo, presión ni aporte.
  - Con pulso es alcanzable una PAM de 9 mmHg (4,5 con bloqueo AV): la guarda de P la recorta en 0,1, y nada lee la
    presión para quitar el pulso mientras el colapso está apagado.
  - El cero numérico de gasto detiene la corrida (una guarda), pero por la bomba no se alcanza.
- **Ya existe una estructura de colapso (P2E-3), apagada.** Tiene una carga propia, un orden acíclico sin redisparo (la
  carga del minuto lee el gasto del estado anterior) y la transición a AESP o asistolia. Lee sólo el gasto.
  - Su criterio mira la carga y no la severidad del minuto: una carga que quedó en el límite para a un paciente con
    gasto normal al minuto siguiente, y el repago (τ 30–240) no lo evita.
- **El gasto solo no basta.** La vasoplejía (tono 0,45: gasto 1,2, PAM 48,5), la anemia grave (Hb al 25 %: PAM 90,
  déficit 0,375) y la hipoxemia arterial no se ven por el gasto. Bomba y ritmo llegan sólo por el flujo, y un ritmo sin
  pulso es paro.
- **Redundancia:**
  - la presión de perfusión y el aporte de O2 son necesarios;
  - la redundancia del flujo es una premisa fisiológica, porque existen estados de flujo bajo con PAM conservada y sin
    déficit;
  - la oxigenación «distinta» vale igual para el contenido de O2 que para la SpO2;
  - la acidemia no llega a ninguna entrada;
  - lactato, D, I y F quedan excluidos.
- **Persistencia:**
  - con los valores sintéticos de P2E-3, el gasto 0,1 sostenido cumple el criterio en el minuto 14 y un minuto crítico
    aislado no basta;
  - el perfil admite paro en un minuto y no exige repago (minutos críticos aislados llegan a la transición en el minuto
    131);
  - con el déficit como entrada, la carga se parece a una D con umbral.
- **ROSC no está modelado** (dos guardas explícitas). Un retorno futuro tendría que reiniciar la carga.
- **Subconjunto extremo (17 604 filas, 57m):**
  - PAM 32,5–46,3, pH 6,961, DO2 0,106 y gasto entre 0,106 y 0,709;
  - P = 1, R sinusal y SpO2 97, con pulso.

  Falta la regla común activa.
- **Generalización:**
  - con la regla actual, STRUCTURAL_GAP;
  - con la señal propuesta, plausible para las siete familias, siempre que la hipoxemia entre por contenido o por SpO2.
- **Ninguna regla lee conciencia, lactato, D ni F.** El núcleo, el golden y todo lo cerrado quedan sin cambios.

**Lo mínimo antes de una segunda familia:**

1. Reemplazar el gasto por una señal común de no viabilidad: el máximo de la falla de presión de perfusión (PAM) y la de
   aporte de O2 (déficit), con contenido de O2 o SpO2 si se decide.
2. Elegir la persistencia: la carga existente con tres invariantes (piso, repago o reinicio obligatorio y severidad en
   el minuto que decide), o un contador de minutos consecutivos.
3. Exigir la señal nula a la llegada.

Los valores quedan UNSET.

## 1. Decisiones de la docencia

<!-- generado:decisiones -->
Decisiones de la docencia (texto congelado, en inglés):

- **acidemia**: no pH arrest threshold unless a committed common rule exists; the P2K-5 / P2L-2 subset (57m, demand 1.1, 17,604 rows, pH < 7.00) carried as a diagnostic stress subset, never filtered
- **brief**: P2M-1 collapse / arrest safety architecture audit (2026-11-02): structural; no arrest threshold chosen
- **candidate_domains**: A flow, B MAP / perfusion pressure, C pump P, D rhythm / pulse R, E effective oxygen delivery / deficit, F arterial oxygenation, G severe acid-base failure, H future respiratory failure; necessity, redundancy and order to be determined
- **closed**: BloodState, V, P, T, R, pressure, DO2 / deficit, D, lactate, HR / baroreflex, acid-base, RR / W / PaCO2 and the consciousness architecture closed; P2L-2's carried debts untouched unless collapse depends on them
- **no_biomarker_arrest**: lactate, D alone, consciousness I and the systemic encephalopathy burden F are never direct collapse or arrest triggers
- **order**: no implicit recursive pulse / collapse feedback; an explicit lag if needed
- **persistence**: if an instantaneous rule would flip or arrest in one minute: PERSISTENCE_STATE_OR_TIMER_REQUIRED; D and F are not collapse memory without strong causal justification
- **rosc**: no ACLS here; no proposed state may make a future return of circulation impossible
- **scope**: shadow only; no collapse activation, runtime integration, GI or second-family migration, death model or parameter approval
- **three_states**: consciousness impairment, hemodynamic collapse (circulation present, not viable) and cardiac arrest (no effective circulation) stay distinct; unconscious with a pulse, profound shock with a pulse and collapse progressing to arrest stay representable
- **thresholds**: the GI cases cannot identify minimum viable MAP or flow, an arrest pH or DO2 or a persistence duration; ranges only from general physiology, otherwise UNSET
<!-- /generado:decisiones -->

## 2. Semántica del pulso

<!-- generado:pulso -->
- **changed_by** (texto congelado, en inglés): a RhythmTransition: a contributor's (modules/rhythm_events.ScriptedRhythmEvent) or the core's P2E-3 collapse rule (integration.step); the arrival constructor sets the arrival rhythm
- **class** (texto congelado, en inglés): AUTHORITATIVE_STATE: pulse is a field of the rhythm state R, changed only by rhythm transitions; it is bound by invariant to the rhythm code (pulse exactly when the code perfuses: NON_PERFUSING = pulseless VT, VF, PEA, asystole), so it is ELECTRICAL / RHYTHM semantics, never read from pressure or flow
- **default** (texto congelado, en inglés): the case's arrival rhythm (Anchors.rhythm; bands.ARRIVAL: sinus 80, pulse); terminal_since None
- **field** (texto congelado, en inglés): CoreState.R (channel C4, 'state machine: code, rate, effective-output factor, pulse'): RhythmState.pulse_present
- **invariants** (texto congelado, en inglés): a perfusing rhythm has output_factor > 0, a pulseless one exactly 0; terminal_since is set exactly when there is no pulse, within the encounter, and never cleared
- **when_false** (texto congelado, en inglés): derive's pulseless branch: output, pressure and delivery 0; SBP, DBP, MAP, SpO2, CRT and pulse rate not measurable; RR 0; the legacy level 3; the integrator keeps T and P as latent values, accrues D at the full demand (lactate follows it a minute later), accrues the acid burden, holds the collapse burden; nothing restores a pulse

Búsqueda por AST en 31 archivos del núcleo (sin los de análisis ni los informes):

- **Transiciones de ritmo** (2): integration.py:421, modules/rhythm_events.py:52.
- **Escrituras de R por palabra clave** (3): derived.py:992, integration.py:458, state.py:696.
- **Escrituras de terminal_since** (1): integration.py:458.
- **Lecturas de pulse_present:** 37; de terminal_since: 6.
- **Constructores de ritmo:** 7; guardas que detienen la corrida (UnresolvedBoundary): derived.py:1337, derived.py:629, integration.py:442.
<!-- /generado:pulso -->

## 3. Mecanismos actuales de paro y colapso

<!-- generado:mecanismos -->
| Mecanismo | Dónde | Condición (congelada) | Clase | Activo por defecto |
|---|---|---|---|---|
| bicarbonate_guard | `derived.bicarbonate (P2K-2)` | an acid burden that takes HCO3 to or below 0 stops the run | SAFETY_GUARD | sí |
| blood_channel_guard | `integration.step` | a blood-state move outside the V / Hb guard stops the run | SAFETY_GUARD | sí |
| hemodynamic_collapse_with_pulse | `none` | no observable or state names a collapse while a pulse is present; only the hidden P2E-3 burden exists, and only when the rule is declared | NOT_CURRENTLY_MODELED | no |
| legacy_engine_arrests | `family_engine and its family modules (read as text)` | anaphylaxis untreated minutes, apnoea minutes, a closed coronary artery's minutes to VF, a bradycardia rate at or below 20, and the older generic low-flow conjunction in clinical_physiology | LEGACY_ARTIFACT | sí |
| no_return_of_pulse | `integration._rhythm_after; CoreState docstring` | a transition back to a pulse after arrest raises ('resuscitation is out of scope'); terminal_since never cleared | SAFETY_GUARD | sí |
| p2e3_collapse_rule | `derived.collapse_burden_after_minute / collapse_reached / terminal_rhythm; integration.step` | aux.collapse_burden accrues the share by which output_rel falls below a declared threshold (read on the minute's start state, only with a pulse), held or repaid when declared; at the declared limit R moves to PEA (or asystole) the same step, so the new state is pulseless one minute after the state that met the criterion; off by default (threshold and limit None) | VALID_COMMON_PHYSIOLOGY | no |
| resuscitation_rosc | `none` | no CPR, defibrillation, epinephrine-for-arrest or return of circulation | NOT_CURRENTLY_MODELED | no |
| rhythm_state_invariants | `state.RhythmState.__post_init__` | a pulse exactly when the rhythm perfuses; a non-perfusing rhythm has no output | SAFETY_GUARD | sí |
| scripted_pump_change | `modules/rhythm_events.ScriptedPumpChange` | a declared change of P per minute over an interval; reaches flow, never the pulse directly | CASE_SCRIPTED_EVENT | no |
| scripted_rhythm_event | `modules/rhythm_events.ScriptedRhythmEvent` | a declared natural-history change of R at a declared minute, cause class and preventability; not applied once in arrest; no GI case declares one | CASE_SCRIPTED_EVENT | no |
| zero_output_guard | `derived.derive` | a pulse with effective output at the numerical zero stops the run (UnresolvedBoundary), it is never shown | SAFETY_GUARD | sí |

Los mecanismos heredados se citan como texto (nunca se importan ni se ajustan): `acs_reperfusion.py` sí, `airway_pharmacology.py` sí, `anaphylaxis_reaction.py` sí, `bradycardia_toxicology.py` sí, `clinical_physiology.py` sí.
<!-- /generado:mecanismos -->

## 4. Fisiología sin flujo

<!-- generado:flujo_cero -->
- **Sin pulso (FV):** gasto 0,00, presión 0,00, aporte 0,00; PAM, PAS y SpO2 no medibles; nivel heredado 3.
- **Un minuto sin pulso:** D 0,00 → 1,00; carga ácida 4,000 → 4,128; lactato en exceso 0,00 → 0,00 (sigue a D con un minuto de retraso); carga de colapso 0,00 → 0,00; T y P latentes sin cambio; terminal_since 0.
- **Ritmos imposibles:** perfusing_without_output: RAISES, pulseless_organized_sinus: RAISES, pulseless_with_output: RAISES.
- **Pulso con gasto en el cero numérico:** STOPS_THE_RUN; carga ácida 30 (HCO3 ≤ 0): STOPS_THE_RUN.
- **Pulso con gasto 0,02:** representable: PAM 1,8 mmHg, PAS 2,4 mmHg, déficit 0,950, nivel heredado 2.

Lectura (texto congelado, en inglés): pulse=false can never carry flow, pressure or delivery (the rhythm invariant and derive's pulseless branch); pulse=true with output at the numerical zero is not representable (the run stops), but pulse=true with output 0.02 is: MAP about 2 mmHg with a pulse, because the pulse is rhythm semantics and nothing reads pressure to end it while the collapse rule is off
<!-- /generado:flujo_cero -->

## 5. Sondas de estado fijo: flujo / PAM, bomba / ritmo, aporte de O2, acidemia

<!-- generado:sondas -->
Regla (texto congelado, en inglés): Fixed states on P2K-2's neutral probe arrival (bands.ARRIVAL with HCO3 20, extraction reserve 2.5), read through derive, the deficit and the ventilation candidate (gain 0.04): illustrative extremes, P2L-1's sizes where they exist. Each candidate input is classified threshold-free against the neutral reference: zero under every admissible bound (the reading is on the reference's side), or positive under some. The current P2E-3 input is output_rel, whose admissible thresholds lie below arrival output (1).

| Sonda | Qué fija | Pulso | Gasto | PAM | Aporte rel. | Déficit / demanda | SpO2 | pH | Entradas que pueden fallar | Mecanismo |
|---|---|---|---|---|---|---|---|---|---|---|
| acid_severe_metabolic | metabolic acid burden 15 (pH about 7.18) | sí | 1,000 | 90,0 | 1,000 | 0,000 | 97,0 | 7,179 | ninguna | ninguno |
| flow_A_low_flow_high_tone | pump 0.55, tone 3.0 (the tone guard's ceiling): low flow, MAP kept | sí | 0,344 | 92,8 | 0,344 | 0,141 | 97,0 | 7,386 | gasto (regla P2E-3 actual), aporte de O2 (déficit) | riesgo de colapso circulatorio |
| flow_B_flow_kept_low_tone | tone 0.45 (vasodilation: flow rises, MAP falls) | sí | 1,198 | 48,5 | 1,198 | 0,000 | 97,0 | 7,386 | presión de perfusión (PAM) | riesgo de colapso circulatorio |
| flow_C_both | pump 0.3 | sí | 0,300 | 27,0 | 0,300 | 0,250 | 97,0 | 7,386 | gasto (regla P2E-3 actual), aporte de O2 (déficit), presión de perfusión (PAM) | riesgo de colapso circulatorio |
| oxygen_A_low_flow_delivery_kept | pump 0.5 (extraction reserve keeps consumption) | sí | 0,500 | 45,0 | 0,500 | 0,000 | 97,0 | 7,386 | gasto (regla P2E-3 actual), presión de perfusión (PAM) | riesgo de colapso circulatorio |
| oxygen_B_content_failure | Hb at 25 % (flow and MAP kept) | sí | 1,000 | 90,0 | 0,250 | 0,375 | 97,0 | 7,386 | aporte de O2 (déficit) | riesgo de no viabilidad metabólica |
| oxygen_C_both | pump 0.3, Hb at 60 % | sí | 0,300 | 27,0 | 0,180 | 0,550 | 97,0 | 7,386 | gasto (regla P2E-3 actual), aporte de O2 (déficit), presión de perfusión (PAM) | riesgo de colapso circulatorio |
| oxygen_E2_authored_hypoxaemia | authored arrival SpO2 60 (delivery index 1) | sí | 1,000 | 90,0 | 1,000 | 0,000 | 60,0 | 7,386 | oxigenación arterial (SpO2) | riesgo de no viabilidad metabólica |
| oxygen_E_arterial_hypoxaemia | arrival on FiO2 1, then room air (SpO2 73) | sí | 1,000 | 90,0 | 0,756 | 0,000 | 73,3 | 7,386 | oxigenación arterial (SpO2) | riesgo de no viabilidad metabólica |
| pump_A_pump_failure_organized_rhythm | pump 0.25, sinus | sí | 0,250 | 22,5 | 0,250 | 0,375 | 97,0 | 7,386 | gasto (regla P2E-3 actual), aporte de O2 (déficit), presión de perfusión (PAM) | riesgo de colapso circulatorio |
| pump_B2_pulseless_rhythm | pump 1, VF (no pulse) | no | 0,000 | — | 0,000 | — | — | — | ninguna | paro (sin pulso) |
| pump_B_rhythm_low_output_with_pulse | complete AV block at 30 / min, output factor 0.5, pump 1 | sí | 0,500 | 45,0 | 0,500 | 0,000 | 97,0 | 7,386 | gasto (regla P2E-3 actual), presión de perfusión (PAM) | riesgo de colapso circulatorio |
| pump_C_both | pump 0.4 with the AV block | sí | 0,200 | 18,0 | 0,200 | 0,500 | 97,0 | 7,386 | gasto (regla P2E-3 actual), aporte de O2 (déficit), presión de perfusión (PAM) | riesgo de colapso circulatorio |
| reference | the neutral probe arrival | sí | 1,000 | 90,0 | 1,000 | 0,000 | 97,0 | 7,386 | ninguna | ninguno |

- **Flujo / PAM (A, B, C, D) distinguibles:** sí; la regla actual (sólo gasto) no ve: flow_B_flow_kept_low_tone.
- **Aporte de O2 (A, B, C, D) distinguibles:** sí; la regla actual no ve: oxygen_B_content_failure, oxygen_E2_authored_hypoxaemia, oxygen_E_arterial_hypoxaemia.
- **Bomba / ritmo:** un ritmo con pulso y gasto 0,5 lee igual que una bomba en 0,5: sí; la falla de bomba y la combinada comparten entradas: sí; un ritmo sin pulso es paro: sí.
<!-- /generado:sondas -->

## 6. Necesidad y redundancia de las entradas

<!-- generado:redundancia -->
- **A_flow** (texto congelado, en inglés): REDUNDANT_GIVEN_B_AND_E: flow reaches viability through perfusion pressure (pressure = flow x tone) and through delivery (delivery = flow x content); a low flow that neither lowers MAP nor exhausts extraction is not by itself non-viable
- **B_perfusion_pressure** (texto congelado, en inglés): NECESSARY: vasoplegia keeps flow and delivery while MAP falls (flow_B); only pressure sees it
- **C_pump** (texto congelado, en inglés): REDUNDANT_VIA_FLOW: P enters output multiplicatively; reading it beside its consequences counts it twice
- **D_rhythm** (texto congelado, en inglés): SPLIT: a pulseless rhythm is arrest itself (a transition, not collapse); a perfusing rhythm's output factor enters flow like P
- **E_oxygen_delivery** (texto congelado, en inglés): NECESSARY: an oxygen-content failure keeps flow and MAP (oxygen_B); only the deficit sees it
- **F_arterial_oxygenation** (texto congelado, en inglés): DISTINCT_CANDIDATE: the systemic deficit misses arterial hypoxaemia to about 39 % at normal flow and Hb (oxygen_E); the myocardium extracts near its maximum at rest, so a separate input is plausible: faculty decision
- **G_acid_base** (texto congelado, en inglés): MODIFIER_NOT_INPUT: no path to P or R today; the acid burden integrates the deficit (P2L-2 M4), so an additive pH input would recount a prolonged deficit; amplifier or myocardial depression are later decisions
- **H_respiratory_failure** (texto congelado, en inglés): FUTURE: no apnoea or ventilatory-failure writer; it reaches viability through SpO2
- **lactate_D_I_F** (texto congelado, en inglés): EXCLUDED (faculty): consequences and markers, never triggers

Comprobado sobre las sondas elegidas (no sobre todo el espacio de estados: ver la nota que sigue):

- la acidemia no llega a ninguna entrada: sí
- hay un estado donde falla la oxigenación arterial sin déficit: sí
- hay un estado donde falla el aporte con la presión conservada: sí
- el flujo bajo nunca falla solo (siempre lo acompaña presión o aporte): sí
- hay un estado donde sólo falla la presión (vasoplejía): sí
- un ritmo sin pulso es paro, no colapso: sí
- bomba y ritmo llegan a las entradas sólo por el flujo: sí
<!-- /generado:redundancia -->

**Nota (revisión, ALTO-2).** «El flujo nunca falla solo» vale para las sondas elegidas, no para el modelo.

- Dentro de las guardas existen estados con flujo bajo, PAM conservada y sin déficit: bomba 0,7 con tono 2,0 (Q 0,538,
  PAM 96,9) y bomba 0,8 con tono 1,5 (Q 0,696, PAM 93,9). La prueba `test_review_h2_flow_can_fail_alone_inside_the_guards`
  los fija.
- La redundancia del flujo es, por lo tanto, una **premisa fisiológica**: un flujo bajo que no baja la PAM ni agota la
  extracción no es por sí solo no viable. Queda para que la docencia la confirme (decisión 13).
- Con la sonda de flujo solo incluida, el criterio congelado `redundancy_resolved` habría fallado.

## 7. Persistencia

<!-- generado:persistencia -->
Con los valores sintéticos comprometidos de P2E-3 (umbral 0,4, límite 10, τ de repago 30 min), por la función del núcleo:

- **Un minuto crítico aislado** (gasto casi 0): carga 1,00; paro: no.
- **Gasto 0,1 sostenido:** 0,75 por minuto; se cumple el criterio en el minuto 14.
- **8 min críticos y luego restaurado:** carga 6,00; a los 60 min sin repago 6,00, con repago 0,81.
- **Un minuto crítico cada 10 durante 4 h:** sin repago se cumple el criterio en el minuto 131; con repago la carga no pasa de 2,89 y nunca se cumple.
- **Límite 0,5 (el perfil lo acepta: sí):** paro en el minuto 1.

- **persistence_exists** (texto congelado, en inglés): aux.collapse_burden: a dedicated collapse memory (neither D nor F)
- **repayment_optional** (texto congelado, en inglés): without a declared repayment the burden never falls: brief dips separated by normal flow accumulate to the transition
- **single_minute_arrest_not_excluded** (texto congelado, en inglés): the profile accepts a limit at or below one minute's maximal accrual, so an instantaneous one-minute arrest is constructible
- **Reglas comprometidas CO1:** brief, moderate low flow need not cause arrest (five minutes at 90% of the collapse threshold, then recovery: no arrest)
- **Reglas comprometidas CO2:** severe, prolonged low flow can accumulate burden to the terminal transition (output 0.1 (the pump bound) for 240 min: the criterion is met)

**Clasificación** (texto congelado, en inglés): PERSISTENCE_STATE_OR_TIMER_REQUIRED: already present (P2E-3 collapse burden); two invariants missing (a persistence floor, a mandatory repayment)
<!-- /generado:persistencia -->

**Nota (revisión, ALTO-1, ALTO-4 y MEDIO-7).**

- **Carga vieja.** `collapse_reached` lee la carga y el pulso, nunca la severidad del minuto. Un paciente con pulso,
  gasto 1 y una carga de 10,5 pasa a AESP al minuto siguiente, con τ 30 o 240 (los candidatos P2F no lo evitan). Eso
  ocurre si un contribuyente movió el ritmo el minuto en que se cumplió el criterio, o tras un retorno futuro de la
  circulación sin reiniciar la carga. La prueba `test_review_h1_a_stale_burden_arrests_a_patient_whose_output_is_normal`
  lo fija.
- **Tercera invariante.** Hace falta una: la transición sólo con no viabilidad en el minuto que decide, y la carga
  reiniciada cuando otra fuente mueve R y en un ROSC (decisión 11).
- **Parecido con D.** Con el déficit como entrada, la carga se parece a una D con umbral: integra el déficit más allá de
  una cota y lo repaga. La docencia excluyó D como memoria de colapso salvo justificación causal fuerte. Las opciones
  son dos: justificarla como tiempo isquémico miocárdico más allá de una cota no viable, o usar un contador de minutos
  críticos consecutivos que se reinicia al recuperar (decisión 12).
- **El criterio congelado exige el defecto.** `persistence_classified` pide que el límite de 0,5 produzca paro en un
  minuto. Si se agrega el piso, el criterio falla; la brecha es un hallazgo, no una condición de preparación.

## 8. Orden de eventos y bucles

<!-- generado:orden -->
- La carga y el criterio se leen sobre el estado al inicio del minuto: sí; las invariantes de observación se comprueban sobre el estado nuevo: sí.
- En la trayectoria sintética (gasto 0,1, 20 pasos): la carga del estado previo 9,75 < límite ≤ 10,50; el pulso se pierde en el minuto 14.
- Tras el paro la carga queda congelada y no hay otra transición: sí; un solo disparo: sí.
- **Clasificación** (texto congelado, en inglés): EXPLICIT_LAG_REQUIRED: already implemented (the criterion is read on the minute's start state, the pulseless rhythm is the next state's; the detector never reads its own result in the same step, needs a pulse to fire and freezes after arrest): ACYCLIC
<!-- /generado:orden -->

**Nota (revisión, ALTO-1 y BAJO-9).**

- El primer estado con la carga en el límite ya es el que queda sin pulso: el «retraso» está en la entrada (la carga
  del minuto m lee el gasto del estado m − 1). No hay un minuto extra después de cumplir el criterio. El texto congelado
  de MECHANISMS («one minute after the state that met the criterion») lo dice mal.
- El orden es acíclico y sin redisparo, pero la trayectoria de prueba no tiene contribuyentes. El aplazamiento cuando un
  contribuyente mueve el ritmo es justamente el camino de la carga vieja de §7.

## 9. Retorno de la circulación (ROSC)

<!-- generado:rosc -->
- **Estado:** ROSC_NOT_CURRENTLY_MODELED.
- El regreso del pulso tras el paro lanza un error: sí; terminal_since nunca se borra: sí.
- Lectura (texto congelado, en inglés): a future return of circulation needs those two explicit guards lifted (and a rule that clears terminal_since); the collapse burden is an ordinary auxiliary state a future rule can reset or repay, so nothing in the existing structure, or in the minimum proposed here, makes it architecturally impossible
<!-- /generado:rosc -->

**Nota (revisión, ALTO-1).** «reset or repay» es inexacto: el repago no basta (τ 30 deja la carga en 10,16 ≥ 10). Un
retorno futuro de la circulación tiene que **reiniciar** la carga, o volvería a parar en un minuto.

## 10. Subconjunto extremo GI

<!-- generado:subconjunto -->
- **Filas:** 17 604 (57m: 17 604; 72f: 0); filtradas: no.
- **PAM a los 120 min:** 32,5–46,3 mmHg; **PAS:** 43,8–62,4 mmHg; presión relativa 0,498–0,709.
- **Fila de pH más bajo:** pH 6,961, PaCO2 25,8, déficit 0,835 (fracción 0,759), minuto 120.
- **DO2 efectivo** (índice, exacto desde el déficit): 0,106; aporte relativo 0,106–0,177.
- **Gasto Q (cota, no reconstruido):** 0,106–0,709 del de llegada. (texto congelado, en inglés): output_rel at minute 120 lies between the effective delivery over the largest arrival delivery ratio (Hb ratio at most 1) and the pressure the MAP implies (tone at least 1 under the tone response); not reconstructed: the structural conclusion does not depend on it
- **P** (texto congelado, en inglés): 1 (arrival): the untreated GI scenario writes no pump change (modules/gi_haemorrhage writes the blood state only)
- **R** (texto congelado, en inglés): sinus with a pulse: no rhythm transition is declared and the collapse rule is off
- **SpO2** (texto congelado, en inglés): 97 (authored arrival; untreated FiO2 unchanged, and SpO2 moves only with FiO2)
- **Pulso:** sí. **Problema de estabilidad:** sí.
- **Mecanismo de seguridad que falta** (texto congelado, en inglés): ACTIVE_COMMON_COLLAPSE_RULE_MISSING: the P2E-3 structure exists but is off and reads output only; with it off, MAP 31-46 mmHg, a deficit of 0.84 and pH 6.96 keep a pulse until a guard stops the run (zero output, HCO3 at 0, blood bounds), never an arrest
<!-- /generado:subconjunto -->

**Nota (revisión, BAJO-8 y ALTO-3).**

- El texto congelado «MAP 31-46 mmHg» viene del rango de referencia de P2J-3. El rango del subconjunto en el registro
  de P2L-1 es 32,5–46,3.
- **El cero numérico no se alcanza por la bomba.** La guarda de P la recorta en 0,1 (un recorte silencioso que la tabla
  de mecanismos no clasificaba, SAFETY_GUARD), así que el cero numérico de gasto no se alcanza por esa vía.
- **Pulso con PAM casi nula.** Es alcanzable un pulso con PAM de 9 mmHg (4,5 con bloqueo AV) durante toda la ventana de
  persistencia. Las sondas congeladas de «gasto 0,02» y «cero numérico» usan P fuera de la guarda.
- La prueba `test_review_h3_the_pump_guard_keeps_a_pulse_at_a_map_near_zero` lo fija.

## 11. Generalización

<!-- generado:generalizacion -->
| Familia | Camino (congelado) | Sonda | La regla actual lo ve | La señal propuesta lo ve | Mecanismo |
|---|---|---|---|---|---|
| Anafilaxia | T and V fall, airway: MAP first, flow later, hypoxaemia | flow_B_flow_kept_low_tone | no | sí | riesgo de colapso circulatorio |
| Shock cardiogénico | P falls: flow, MAP and delivery fall | pump_A_pump_failure_organized_rhythm | sí | sí | riesgo de colapso circulatorio |
| Shock distributivo / sepsis | T falls: MAP falls while flow is kept or rises; demand rises | flow_B_flow_kept_low_tone | no | sí | riesgo de colapso circulatorio |
| Shock hemorrágico | V and Hb fall: flow, MAP and delivery fall together | flow_C_both | sí | sí | riesgo de colapso circulatorio |
| Hipoxemia grave / insuficiencia respiratoria | SpO2 falls; the systemic deficit (extraction reserve) misses it to about 39 %; apnoea needs the respiratory family's writer | oxygen_E_arterial_hypoxaemia | no | sí | riesgo de no viabilidad metabólica |
| Arritmia maligna | a pulseless rhythm is arrest at once (a rhythm transition, not collapse); a perfusing low-output rhythm lowers flow | pump_B_rhythm_low_output_with_pulse | sí | sí | riesgo de colapso circulatorio |
| Shock obstructivo / TEP | no obstruction channel: the family's writer lowers effective preload / pump; PE adds hypoxaemia | flow_C_both | sí | sí | riesgo de colapso circulatorio |

**Con la regla actual:** STRUCTURAL_GAP (no ve: anaphylaxis, distributive_sepsis, hypoxaemia_respiratory_failure). **Con la señal propuesta:** COMMON_COLLAPSE_ARCHITECTURE_PLAUSIBLE. Condición (texto congelado, en inglés): the arterial-oxygenation input (a faculty decision) and each family's own writer of its signal; no family term in the collapse layer
<!-- /generado:generalizacion -->

**Nota (revisión, MEDIO-5).**

- La generalización «plausible» depende de la entrada opcional de oxigenación. Sin ella, la hipoxemia queda fuera
  (STRUCTURAL_GAP).
- Además, Hb al 75,6 % y SpO2 73,3 dan el mismo aporte y ningún déficit, y la entrada arterial sólo marca la segunda.
  El argumento de la extracción miocárdica vale igual para el contenido: justifica una entrada de contenido de O2
  (CaO2), no sólo de SpO2 (decisión 14).

## 12. La conciencia no es disparador

<!-- generado:disparadores -->
- Lo que la regla de colapso lee de los disparadores prohibidos: nada; en el bloque del integrador: nada.
- El ritmo terminal lee (texto congelado, en inglés): derive's monitor rate only (the PEA rate).
- Lectura (texto congelado, en inglés): no collapse code reads consciousness, lactate, D or the encephalopathy burden; consciousness is downstream (derive's pulseless level 3; the P2L-2 candidate's maximal hypoperfusion without a pulse)
<!-- /generado:disparadores -->

## 13. Estructura mínima

<!-- generado:minimo -->
**Clasificación: `DERIVED_COLLAPSE_SIGNAL_ONLY_REQUIRED`.**

- **invariants** (texto congelado, en inglés): a persistence floor (no one-minute arrest: the limit above one minute's maximal accrual) and a mandatory repayment whenever the rule is declared
- **new** (texto congelado, en inglés): one derived common non-viability signal replacing output_rel as the burden's input: the maximum (never a sum) of perfusion-pressure failure (MAP), oxygen-delivery failure (the effective deficit) and, if the faculty decides, arterial-oxygenation failure (SpO2), with the dominant mechanism recorded (CIRCULATORY_COLLAPSE / METABOLIC_NONVIABILITY_RISK)
- **not_added_here** (texto congelado, en inglés): nothing is implemented, activated or valued in P2M-1
- **not_needed** (texto congelado, en inglés): no new collapse state, no timer beside the burden, no pump or rhythm input, no flow input, no pH, lactate, D, I or F input
- **reuse** (texto congelado, en inglés): the P2E-3 structure: aux.collapse_burden (a dedicated persistence memory, neither D nor F), its explicit one-minute lag, the terminal transition to a pulseless rhythm and the CO1 / CO2 rules

- **Rangos candidatos ya comprometidos** (texto congelado, en inglés): the P2F calibration registry (CANDIDATE, not approved): burden per minute 0.5 / 1 / 2, limit 5 / 15 / 30 minutes at full severity, repayment 30 / 60 / 240 min; the output threshold 0.2 / 0.3 / 0.4 belongs to the output input the minimum replaces
- **Sin valor (UNSET)** (texto congelado, en inglés): the bounds of the perfusion-pressure, oxygen-delivery and arterial-oxygenation failure signals, the persistence floor, the terminal-rhythm selection rule: no committed common range; never from the GI cases
<!-- /generado:minimo -->

**Lectura corregida tras la revisión (señalada, no recongelada).** La clasificación congelada
`DERIVED_COLLAPSE_SIGNAL_ONLY_REQUIRED` se queda corta. La estructura de P2E-3 sólo es reutilizable con tres invariantes
y no con dos:

1. un piso de persistencia;
2. el repago o reinicio obligatorio;
3. la transición sólo con no viabilidad en el minuto que decide, con la carga reiniciada cuando otra fuente mueve R y en
   un ROSC.

A eso se suman dos decisiones más:

- **La forma de la persistencia:** la carga integrada, que con el déficit como entrada se parece a D y debe
  justificarse, o un contador de minutos consecutivos (`SHORT_PERSISTENCE_TIMER_REQUIRED`), que no acarrea memoria
  vieja.
- **La invariante de llegada:** la señal nula a la llegada, como el umbral de gasto bajo 1.

La entrada mínima sigue siendo una señal común derivada, el máximo de la falla de presión de perfusión y la de aporte de
O2, con el contenido de O2 o la SpO2 como posible tercera entrada. Pero la persistencia también es parte del mínimo, y
la elige la docencia.

## 14. Veredicto

<!-- generado:veredicto -->
| Criterio | Cumple |
|---|---|
| entradas causales explícitas | sí |
| colapso y paro separados | sí |
| orden de eventos seguro | sí |
| generalización plausible | sí |
| sin umbral GI | sí |
| persistencia clasificada | sí |
| semántica del pulso explícita | sí |
| redundancia resuelta | sí |
| fisiología previa intacta | sí |

**Veredicto:** `COLLAPSE_STRUCTURE_READY_FOR_FACULTY_DECISION`.
<!-- /generado:veredicto -->

## 15. Decisiones pedidas

<!-- generado:pedidas -->
Decisiones pedidas a la docencia (texto congelado, en inglés):

1. the input of the existing collapse burden: replace output_rel by the maximum of perfusion-pressure failure (MAP) and oxygen-delivery failure (the effective deficit); confirm both mechanisms
2. whether arterial oxygenation (SpO2) is a third input (the systemic deficit misses hypoxaemia to about 39 %)
3. the two persistence invariants: no one-minute arrest (a floor on the limit) and a mandatory repayment
4. acidemia: a consequence only (minimum), an amplifier of the burden, or a myocardial-depression path into P later
5. zero flow: keep the run-stopping guard, or a same-minute definitional arrest when output reaches the numerical zero
6. pulse semantics: the state's pulse stays rhythm semantics; whether a palpable-pulse observation is derived from pressure (a pulse with MAP about 2 mmHg is representable today)
7. the terminal-rhythm selection rule (PEA or asystole, still TBD)
8. the values: the new signals' bounds and the persistence floor stay UNSET until decided from general physiology; the P2F registry ranges for the persistence parameters are offered for review
9. ROSC in a later package: lift the two guards and decide how the burden resets
10. the next package: implement the decided collapse signal in the shadow core (off by default), then a second family
<!-- /generado:pedidas -->

Decisiones adicionales que salen de la revisión adversarial (§18):

11. **Tercera invariante:** la transición sólo con no viabilidad en el minuto que decide, y la carga reiniciada cuando
    otra fuente mueve R y en un ROSC. Sin ella, la carga vieja para a un paciente con gasto normal.
12. **La forma de la persistencia:** la carga integrada, que con el déficit como entrada se parece a una D con umbral y
    necesita justificación causal (tiempo isquémico miocárdico), o un contador de minutos críticos consecutivos que se
    reinicia al recuperar.
13. **Confirmar la premisa del flujo:** un flujo bajo con PAM conservada y sin déficit no es por sí solo no viable.
14. **La tercera entrada,** si se agrega: el contenido arterial de O2 (anemia e hipoxemia por igual) o sólo la SpO2.
15. **La señal nula a la llegada,** como invariante de punto fijo, igual que el umbral de gasto bajo 1.
16. **El pulso con PAM de 9 mmHg** (alcanzable durante la ventana de persistencia): un pulso palpable derivado de la
    presión en la capa de observación, un paro definicional, o aceptar la ventana. Amplía la decisión 6.
17. **El proceso:** aceptar este registro con las correcciones declaradas, como en P2L-2, o autorizar un segundo
    congelamiento que recalcule los criterios con las sondas de la revisión.

## 16. Eficiencia

<!-- generado:eficiencia -->
- Lecturas de estado fijo por el núcleo certificado: 18.
- Pasos del integrador: 21 (una trayectoria sintética de orden y un minuto sin pulso); actualizaciones de la carga por la función del núcleo: 638.
- Trayectorias GI: 0; barrido cartesiano: no; región reconstruida: no; motor heredado ajustado: no (citado como texto en 5 archivos).
- Registros reutilizados (con huella fijada): P2L1_consciousness_audit.json, P2K5_respiratory_monotonicity.json.
<!-- /generado:eficiencia -->

## 17. Limitaciones

- **Sólo estructura.** Ninguna sonda dice a qué PAM, déficit, SpO2, pH o duración se para el corazón. Las sondas son
  estados fijos ilustrativos; la clasificación sin umbral dice qué entrada puede fallar con algún límite admisible,
  no cuál falla.
- **Los valores sintéticos de P2E-3** (umbral 0,4, límite 10, τ 30) son los de sus pruebas, comprometidos como
  SYNTHETIC_ONLY. Muestran el comportamiento de la carga, no un límite clínico.
- **La sonda A de flujo/PAM** usa el tono en el techo de su guarda (3,0), para conservar la PAM con flujo bajo.
- **El subconjunto extremo** se lee de registros congelados. El gasto sólo se acota (no se reconstruye la
  trayectoria): la PAM y el DO2 vienen de filas que pueden ser unidades distintas.
- **La oxigenación arterial** queda propuesta como entrada candidata. Es la misma pregunta que P2L-2 resolvió para el
  cerebro; para el miocardio la decide la docencia.
- **Fuera del alcance:**
  - la reclasificación del pulso palpable (un pulso con PAM ~2 mmHg) es una decisión de la capa de observación;
  - el cero de flujo sigue siendo una guarda que detiene la corrida;
  - el retorno de la circulación sigue sin modelar.
- **Las vistas de P2L-1 y P2L-2** se adaptaron para dejar fuera la capa de P2M-1. La vista del tono de P2J-1 la
  excluye también. Ningún registro cerrado cambió.
- **Proceso:** el módulo se ejercitó en estados fijos (aprobado/fallido) mientras se escribía. Antes del
  congelamiento se rediseñó una sonda (flujo A) y tres criterios pasaron a calcularse desde la evidencia.

## 18. Revisión adversarial

Una revisión independiente, de sólo lectura, sobre `033c272` y `361c219`. Confirmé cada hallazgo con una sonda propia
antes de actuar. Las sondas del revisor y las mías quedaron fuera del repositorio.

**Revisado y limpio:**
- el núcleo sin cambios (el árbol de P2L-2 coincide byte a byte);
- el congelamiento íntegro y el registro reproducible byte a byte;
- el colapso apagado y sin umbrales nuevos;
- el subconjunto sin filtrar;
- sin lectura de lactato, D, I ni F;
- máximo sin doble conteo de Q;
- bomba y ritmo no agregados como entradas;
- sin términos de enfermedad;
- las cifras del informe correctas;
- las adaptaciones de las pruebas cerradas, que sólo excluyen el módulo nuevo.

**Hallazgos:**

- **ALTO-1. La carga vieja para a un paciente con gasto normal.** Pasa cuando un contribuyente movió el ritmo el minuto
  del criterio, o tras un ROSC futuro; el repago no lo evita, y el «reset or repay» de ROSC es inexacto.
  - *Confirmado:* con τ None, 30 y 240, AESP con gasto 1.
  - *Resuelto en pruebas y texto:* prueba nueva, notas en §7, §8 y §9, decisión 11.
- **ALTO-2. «El flujo nunca falla solo» dependía de las sondas elegidas.**
  - *Confirmado:* bomba 0,7 con tono 2,0 da Q 0,538, PAM 96,9 y déficit 0.
  - *Resuelto en pruebas y texto:* prueba nueva, nota en §6, decisión 13.
  - El criterio `redundancy_resolved` congelado habría fallado con esa sonda.
- **ALTO-3. No estaba demostrado que el mínimo B bastara sin flujo.**
  - *Confirmado:* la guarda de P (0,1) deja pulso con PAM 9 (4,5 con bloqueo AV) durante la ventana; las sondas
    congeladas de gasto 0,02 y del cero numérico usan P fuera de la guarda.
  - *Resuelto en pruebas y texto:* prueba nueva, nota en §10, decisión 16, y el recorte de P declarado como guarda.
- **ALTO-4. Con el déficit como entrada, la carga se parece a una D con umbral.**
  - *Declarado:* nota en §7, decisión 12, con un contador de minutos consecutivos como alternativa.
- **MEDIO-5. La oxigenación arterial «distinta» vale igual para el contenido.**
  - *Confirmado:* Hb al 75,6 % y SpO2 73,3 dan igual aporte y ningún déficit.
  - *Resuelto en pruebas y texto:* prueba nueva, nota en §11, decisión 14; la generalización queda condicionada a esa
    entrada.
- **MEDIO-6. Falta la invariante de llegada para la señal nueva.**
  - *Declarado:* decisión 15.
- **MEDIO-7. `persistence_classified` exige el defecto,** y `event_order_safe` deja fijo el minuto 14.
  - *Declarado:* nota en §7.
- **Bajos.**
  - El rango «MAP 31-46» del texto congelado frente al 32,5–46,3 del registro: nota en §10.
  - La descripción del retraso en MECHANISMS: nota en §8.
  - El escaneo de disparadores no es recursivo; la conclusión se mantiene.
  - Dos aserciones que no podían fallar: corregidas, y se agregó la prueba de un disparador plantado.
  - La etiqueta B se queda corta: lectura corregida en §13.

**Sin segundo congelamiento.** Corregir los criterios dentro del módulo congelado exigiría recongelar. En P2L-1 se señaló
que esa desviación la decide la docencia, y en P2L-2 se aceptó este mismo tratamiento. Por eso sólo se corrigió lo no
congelado (pruebas, informe y documentos) y la contradicción queda pedida como decisión 17. El registro sigue siendo el
de la corrida del congelamiento `c4aa95f6`.
