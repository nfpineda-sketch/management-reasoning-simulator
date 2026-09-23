# Matriz de cobertura de los casos

> Generado por `tools_coverage_matrix.py` desde `case_assessment_bank.py`.
> Rúbrica 1.0-pilot · declaraciones versión 1.0.

La cobertura completa es **requisito para comparar puntajes totales**. No demuestra dificultad equivalente entre casos ni validación psicométrica.

Cada oportunidad declarada se verifica contra el caso: un estudio nombrado tiene que estar en sus investigaciones, una acción tiene que ser una que el motor ejecute, y una región de examen tiene que ser una que el caso escriba. `case_assessment.verify` reporta cualquier discrepancia y hay una prueba por caso.

## Resumen

| Casos | Cobertura completa | Evaluación parcial | Discrepancias | Eventos críticos |
|---|---|---|---|---|
| 21 | 21 | 0 | 0 | 16 definiciones distintas |

## Por caso

| Caso | Familia | D1 | D2 | D3 | D4 | D5 | Eventos críticos definidos |
|---|---|---|---|---|---|---|---|
| `acs_54m_inferior` | acs | ✅ | ✅ | ✅ | ✅ | ✅ | `acs_no_antiplatelet`, `acs_provocation_test` |
| `acs_66f_nonst` | acs | ✅ | ✅ | ✅ | ✅ | ✅ | `acs_no_antiplatelet`, `acs_provocation_test` |
| `acs_61m_posterior` | acs | ✅ | ✅ | ✅ | ✅ | ✅ | `acs_no_antiplatelet`, `acs_provocation_test` |
| `acs_52m_de_winter` | acs | ✅ | ✅ | ✅ | ✅ | ✅ | `acs_no_antiplatelet`, `acs_provocation_test` |
| `acs_48m_wellens` | acs | ✅ | ✅ | ✅ | ✅ | ✅ | `acs_no_antiplatelet`, `acs_provocation_test` |
| `acs_70f_left_main` | acs | ✅ | ✅ | ✅ | ✅ | ✅ | `acs_no_antiplatelet`, `acs_provocation_test` |
| `asthma_24f` | asthma | ✅ | ✅ | ✅ | ✅ | ✅ | `asthma_no_bronchodilator` |
| `asthma_49m` | asthma | ✅ | ✅ | ✅ | ✅ | ✅ | `asthma_no_bronchodilator`, `asthma_no_ventilatory_support` |
| `gi_bleed_57m` | gi_bleed | ✅ | ✅ | ✅ | ✅ | ✅ | `gi_no_resuscitation` |
| `gi_bleed_72f` | gi_bleed | ✅ | ✅ | ✅ | ✅ | ✅ | `gi_no_resuscitation` |
| `hypoglycemia_28m` | hypoglycemia | ✅ | ✅ | ✅ | ✅ | ✅ | `hypo_no_glucose` |
| `hypoglycemia_76f` | hypoglycemia | ✅ | ✅ | ✅ | ✅ | ✅ | `hypo_no_glucose`, `hypo_unsafe_discharge` |
| `hypoglycemia_54m_thiamine` | hypoglycemia | ✅ | ✅ | ✅ | ✅ | ✅ | `hypo_no_glucose`, `hypo_no_thiamine` |
| `opioid_35m` | opioid | ✅ | ✅ | ✅ | ✅ | ✅ | `opioid_no_ventilatory_support` |
| `opioid_67f` | opioid | ✅ | ✅ | ✅ | ✅ | ✅ | `opioid_no_ventilatory_support`, `opioid_unsafe_discharge` |
| `pneumonia_46f` | pneumonia | ✅ | ✅ | ✅ | ✅ | ✅ | `pneumonia_no_antibiotic` |
| `pneumonia_83m` | pneumonia | ✅ | ✅ | ✅ | ✅ | ✅ | `pneumonia_no_antibiotic`, `pneumonia_unexamined_altered_state` |
| `pulmonary_edema_58m` | pulmonary_edema | ✅ | ✅ | ✅ | ✅ | ✅ | `edema_no_ventilatory_support`, `edema_volume_loading` |
| `pulmonary_edema_75f` | pulmonary_edema | ✅ | ✅ | ✅ | ✅ | ✅ | `edema_no_ventilatory_support`, `edema_volume_loading` |
| `pulmonary_embolism_33f` | pulmonary_embolism | ✅ | ✅ | ✅ | ✅ | ✅ | `pe_no_anticoagulation`, `pe_unindicated_thrombolysis` |
| `pulmonary_embolism_61m` | pulmonary_embolism | ✅ | ✅ | ✅ | ✅ | ✅ | `pe_no_anticoagulation` |

## Los cinco dominios

| | Dominio | Qué pregunta |
|---|---|---|
| **D1** | Reconocimiento de gravedad y priorización | Whether the threats were identified, what had to come first was decided, and the urgency of the action matched the threat. |
| **D2** | Evaluación e interpretación clínica | Whether relevant information was obtained and interpreted, and an explanation was built that guides decisions. |
| **D3** | Selección y ejecución de un manejo seguro | Whether the interventions were appropriate, specified enough to be carried out, and weighed against risk, contraindications and this patient's needs. |
| **D4** | Seguimiento y reevaluación | Whether what to watch was defined, delivery and response were checked, and reassessment happened within an appropriate interval. |
| **D5** | Adaptación y continuidad del manejo | Whether the course was integrated, the plan changed or justifiably kept, support requested, and a safe continuity defined. |

## Qué declara cada caso

### `acs_54m_inferior`

- **D1** · ventana 0–20 min. The arrival ECG carries the ischaemic pattern of this case; there is a priority to decide between opening the artery, treating, and investigating further.
  - Esperado: Names the ischaemic pattern or the threat it represents within the window; acts on it before pursuing unrelated investigation.
  - Alternativas aceptables: Naming the threat without the eponym; acting first and naming it in the same turn.
- **D2** · ventana 0–30 min. A 12-lead ECG, a troponin and a history that distinguishes this pattern from the others in the family are all available.
  - Esperado: Requests the ECG and interprets it; relates the troponin to the ECG and the symptoms.
  - Alternativas aceptables: Interpreting the ECG without requesting the troponin when the pattern is already an occlusion equivalent; using POCUS as the second line of evidence.
- **D3** · ventana 0–40 min. An inferior ST-elevation infarction: antiplatelet therapy and the reperfusion pathway, with the preload caution an inferior territory carries.
  - Esperado: Gives an antiplatelet; arranges reperfusion or the consultation that decides it.
  - Alternativas aceptables: A P2Y12 inhibitor when aspirin is contraindicated; withholding a nitrate, which in this territory is a defensible choice.
- **D4** · ventana 10–90 min. The engine runs a clock and responds to what is given: an antiplatelet, a nitrate or an opioid changes observables that can be checked.
  - Esperado: States a reassessment interval; checks the response to what was executed.
  - Alternativas aceptables: Reassessing with the ECG rather than the vitals; a shorter interval than stated.
- **D5** · ventana 15–180 min. The pattern is an occlusion: the decision is whether the artery is opened now and by whom, and what happens while that is arranged.
  - Esperado: Arranges reperfusion or the specialist assessment that decides it; states what is watched while it is arranged.
  - Alternativas aceptables: Thrombolysis with a stated reason when timely intervention is not available; transfer stated as the reperfusion pathway.

**Información accesible:** Arrival observables and the monitor; the patient's own history; the 12-lead ECG and, where the case carries them, additional leads; laboratory, troponin, POCUS and chest radiograph.

**Criterio de cierre:** A disposition is decided, or the horizon of the encounter is reached.

**Límites reales del motor:**
- The engine does not perform angiography; a referral is recorded, not its result.
- Serial troponin requires a new sample and the encounter may close first.

**Eventos críticos:**

- `acs_no_antiplatelet` — **Omisión crítica.** No antiplatelet is given in a recognised acute coronary syndrome.
  - Se activa cuando: The ECG is reported and the presentation is ischaemic, and no aspirin or P2Y12 inhibitor is executed within the window.
  - Información que debía estar disponible: The 12-lead ECG result; the presenting history.
  - Ventana y oportunidad: 0–30 min.
  - Alternativas aceptables: A P2Y12 inhibitor when aspirin is contraindicated or refused, stated as such; withholding it with a stated contraindication such as active bleeding or allergy.
  - Evidencia necesaria: An executed antiplatelet action, or its absence across every executed turn in the window.
  - Exclusiones: The encounter closed before the ECG was reported; the interpreter refused the order and the resident was never told what it could accept.
  - Dominios sobre los que pesa: D3.
- `acs_provocation_test` — **Acción peligrosa.** A provocation or stress test is ordered in an unstable coronary syndrome.
  - Se activa cuando: A stress test is ordered while the presentation is an acute coronary syndrome.
  - Información que debía estar disponible: The 12-lead ECG result; the troponin result when it was requested.
  - Ventana y oportunidad: 0–180 min.
  - Alternativas aceptables: Angiography, invasive assessment or specialist consultation; scheduled outpatient testing stated as after this episode, not now.
  - Evidencia necesaria: An executed or ordered stress test action in the record.
  - Exclusiones: The order was considered in writing but never submitted as an order.
  - Dominios sobre los que pesa: D3.

### `acs_66f_nonst`

- **D1** · ventana 0–20 min. The arrival ECG carries the ischaemic pattern of this case; there is a priority to decide between opening the artery, treating, and investigating further.
  - Esperado: Names the ischaemic pattern or the threat it represents within the window; acts on it before pursuing unrelated investigation.
  - Alternativas aceptables: Naming the threat without the eponym; acting first and naming it in the same turn.
- **D2** · ventana 0–30 min. A 12-lead ECG, a troponin and a history that distinguishes this pattern from the others in the family are all available.
  - Esperado: Requests the ECG and interprets it; relates the troponin to the ECG and the symptoms.
  - Alternativas aceptables: Interpreting the ECG without requesting the troponin when the pattern is already an occlusion equivalent; using POCUS as the second line of evidence.
- **D3** · ventana 0–40 min. Ischaemia without ST elevation: antiplatelet therapy and a monitored specialist assessment rather than immediate angiography.
  - Esperado: Gives an antiplatelet; arranges monitored specialist assessment.
  - Alternativas aceptables: Anticoagulation added to the antiplatelet; stating that immediate angiography is not required here.
- **D4** · ventana 10–90 min. The engine runs a clock and responds to what is given: an antiplatelet, a nitrate or an opioid changes observables that can be checked.
  - Esperado: States a reassessment interval; checks the response to what was executed.
  - Alternativas aceptables: Reassessing with the ECG rather than the vitals; a shorter interval than stated.
- **D5** · ventana 15–180 min. Without ST elevation the decision is the level of monitoring and who assesses next, not an immediate cath lab activation.
  - Esperado: Defines a monitored destination; states what would change the urgency.
  - Alternativas aceptables: Escalating to immediate invasive assessment with a stated reason such as refractory pain.

**Información accesible:** Arrival observables and the monitor; the patient's own history; the 12-lead ECG and, where the case carries them, additional leads; laboratory, troponin, POCUS and chest radiograph.

**Criterio de cierre:** A disposition is decided, or the horizon of the encounter is reached.

**Límites reales del motor:**
- The engine does not perform angiography; a referral is recorded, not its result.
- Serial troponin requires a new sample and the encounter may close first.

**Eventos críticos:**

- `acs_no_antiplatelet` — **Omisión crítica.** No antiplatelet is given in a recognised acute coronary syndrome.
  - Se activa cuando: The ECG is reported and the presentation is ischaemic, and no aspirin or P2Y12 inhibitor is executed within the window.
  - Información que debía estar disponible: The 12-lead ECG result; the presenting history.
  - Ventana y oportunidad: 0–30 min.
  - Alternativas aceptables: A P2Y12 inhibitor when aspirin is contraindicated or refused, stated as such; withholding it with a stated contraindication such as active bleeding or allergy.
  - Evidencia necesaria: An executed antiplatelet action, or its absence across every executed turn in the window.
  - Exclusiones: The encounter closed before the ECG was reported; the interpreter refused the order and the resident was never told what it could accept.
  - Dominios sobre los que pesa: D3.
- `acs_provocation_test` — **Acción peligrosa.** A provocation or stress test is ordered in an unstable coronary syndrome.
  - Se activa cuando: A stress test is ordered while the presentation is an acute coronary syndrome.
  - Información que debía estar disponible: The 12-lead ECG result; the troponin result when it was requested.
  - Ventana y oportunidad: 0–180 min.
  - Alternativas aceptables: Angiography, invasive assessment or specialist consultation; scheduled outpatient testing stated as after this episode, not now.
  - Evidencia necesaria: An executed or ordered stress test action in the record.
  - Exclusiones: The order was considered in writing but never submitted as an order.
  - Dominios sobre los que pesa: D3.

### `acs_61m_posterior`

- **D1** · ventana 0–20 min. The arrival ECG carries the ischaemic pattern of this case; there is a priority to decide between opening the artery, treating, and investigating further.
  - Esperado: Names the ischaemic pattern or the threat it represents within the window; acts on it before pursuing unrelated investigation.
  - Alternativas aceptables: Naming the threat without the eponym; acting first and naming it in the same turn.
- **D2** · ventana 0–30 min. A 12-lead ECG, a troponin and a history that distinguishes this pattern from the others in the family are all available.
  - Esperado: Requests the ECG and interprets it; relates the troponin to the ECG and the symptoms.
  - Alternativas aceptables: Interpreting the ECG without requesting the troponin when the pattern is already an occlusion equivalent; using POCUS as the second line of evidence.
- **D3** · ventana 0–40 min. An occlusion the standard 12-lead shows only as a mirror image: the antiplatelet and the reperfusion pathway, once posterior leads confirm it.
  - Esperado: Gives an antiplatelet; arranges reperfusion once the posterior pattern is recognised.
  - Alternativas aceptables: Acting on the mirror-image pattern without recording posterior leads, stated as such.
- **D4** · ventana 10–90 min. The engine runs a clock and responds to what is given: an antiplatelet, a nitrate or an opioid changes observables that can be checked.
  - Esperado: States a reassessment interval; checks the response to what was executed.
  - Alternativas aceptables: Reassessing with the ECG rather than the vitals; a shorter interval than stated.
- **D5** · ventana 15–180 min. The pattern is an occlusion: the decision is whether the artery is opened now and by whom, and what happens while that is arranged.
  - Esperado: Arranges reperfusion or the specialist assessment that decides it; states what is watched while it is arranged.
  - Alternativas aceptables: Thrombolysis with a stated reason when timely intervention is not available; transfer stated as the reperfusion pathway.

**Información accesible:** Arrival observables and the monitor; the patient's own history; the 12-lead ECG and, where the case carries them, additional leads; laboratory, troponin, POCUS and chest radiograph.

**Criterio de cierre:** A disposition is decided, or the horizon of the encounter is reached.

**Límites reales del motor:**
- The engine does not perform angiography; a referral is recorded, not its result.
- Serial troponin requires a new sample and the encounter may close first.

**Eventos críticos:**

- `acs_no_antiplatelet` — **Omisión crítica.** No antiplatelet is given in a recognised acute coronary syndrome.
  - Se activa cuando: The ECG is reported and the presentation is ischaemic, and no aspirin or P2Y12 inhibitor is executed within the window.
  - Información que debía estar disponible: The 12-lead ECG result; the presenting history.
  - Ventana y oportunidad: 0–30 min.
  - Alternativas aceptables: A P2Y12 inhibitor when aspirin is contraindicated or refused, stated as such; withholding it with a stated contraindication such as active bleeding or allergy.
  - Evidencia necesaria: An executed antiplatelet action, or its absence across every executed turn in the window.
  - Exclusiones: The encounter closed before the ECG was reported; the interpreter refused the order and the resident was never told what it could accept.
  - Dominios sobre los que pesa: D3.
- `acs_provocation_test` — **Acción peligrosa.** A provocation or stress test is ordered in an unstable coronary syndrome.
  - Se activa cuando: A stress test is ordered while the presentation is an acute coronary syndrome.
  - Información que debía estar disponible: The 12-lead ECG result; the troponin result when it was requested.
  - Ventana y oportunidad: 0–180 min.
  - Alternativas aceptables: Angiography, invasive assessment or specialist consultation; scheduled outpatient testing stated as after this episode, not now.
  - Evidencia necesaria: An executed or ordered stress test action in the record.
  - Exclusiones: The order was considered in writing but never submitted as an order.
  - Dominios sobre los que pesa: D3.

### `acs_52m_de_winter`

- **D1** · ventana 0–20 min. The arrival ECG carries the ischaemic pattern of this case; there is a priority to decide between opening the artery, treating, and investigating further.
  - Esperado: Names the ischaemic pattern or the threat it represents within the window; acts on it before pursuing unrelated investigation.
  - Alternativas aceptables: Naming the threat without the eponym; acting first and naming it in the same turn.
- **D2** · ventana 0–30 min. A 12-lead ECG, a troponin and a history that distinguishes this pattern from the others in the family are all available.
  - Esperado: Requests the ECG and interprets it; relates the troponin to the ECG and the symptoms.
  - Alternativas aceptables: Interpreting the ECG without requesting the troponin when the pattern is already an occlusion equivalent; using POCUS as the second line of evidence.
- **D3** · ventana 0–40 min. A proximal anterior occlusion whose pattern precedes ST elevation: the artery is opened now, not after waiting for the elevation.
  - Esperado: Gives an antiplatelet; arranges reperfusion without waiting for ST elevation.
  - Alternativas aceptables: Stating the equivalence explicitly and escalating on that basis.
- **D4** · ventana 10–90 min. The engine runs a clock and responds to what is given: an antiplatelet, a nitrate or an opioid changes observables that can be checked.
  - Esperado: States a reassessment interval; checks the response to what was executed.
  - Alternativas aceptables: Reassessing with the ECG rather than the vitals; a shorter interval than stated.
- **D5** · ventana 15–180 min. The pattern is an occlusion: the decision is whether the artery is opened now and by whom, and what happens while that is arranged.
  - Esperado: Arranges reperfusion or the specialist assessment that decides it; states what is watched while it is arranged.
  - Alternativas aceptables: Thrombolysis with a stated reason when timely intervention is not available; transfer stated as the reperfusion pathway.

**Información accesible:** Arrival observables and the monitor; the patient's own history; the 12-lead ECG and, where the case carries them, additional leads; laboratory, troponin, POCUS and chest radiograph.

**Criterio de cierre:** A disposition is decided, or the horizon of the encounter is reached.

**Límites reales del motor:**
- The engine does not perform angiography; a referral is recorded, not its result.
- Serial troponin requires a new sample and the encounter may close first.

**Eventos críticos:**

- `acs_no_antiplatelet` — **Omisión crítica.** No antiplatelet is given in a recognised acute coronary syndrome.
  - Se activa cuando: The ECG is reported and the presentation is ischaemic, and no aspirin or P2Y12 inhibitor is executed within the window.
  - Información que debía estar disponible: The 12-lead ECG result; the presenting history.
  - Ventana y oportunidad: 0–30 min.
  - Alternativas aceptables: A P2Y12 inhibitor when aspirin is contraindicated or refused, stated as such; withholding it with a stated contraindication such as active bleeding or allergy.
  - Evidencia necesaria: An executed antiplatelet action, or its absence across every executed turn in the window.
  - Exclusiones: The encounter closed before the ECG was reported; the interpreter refused the order and the resident was never told what it could accept.
  - Dominios sobre los que pesa: D3.
- `acs_provocation_test` — **Acción peligrosa.** A provocation or stress test is ordered in an unstable coronary syndrome.
  - Se activa cuando: A stress test is ordered while the presentation is an acute coronary syndrome.
  - Información que debía estar disponible: The 12-lead ECG result; the troponin result when it was requested.
  - Ventana y oportunidad: 0–180 min.
  - Alternativas aceptables: Angiography, invasive assessment or specialist consultation; scheduled outpatient testing stated as after this episode, not now.
  - Evidencia necesaria: An executed or ordered stress test action in the record.
  - Exclusiones: The order was considered in writing but never submitted as an order.
  - Dominios sobre los que pesa: D3.

### `acs_48m_wellens`

- **D1** · ventana 0–20 min. The arrival ECG carries the ischaemic pattern of this case; there is a priority to decide between opening the artery, treating, and investigating further.
  - Esperado: Names the ischaemic pattern or the threat it represents within the window; acts on it before pursuing unrelated investigation.
  - Alternativas aceptables: Naming the threat without the eponym; acting first and naming it in the same turn.
- **D2** · ventana 0–30 min. A 12-lead ECG, a troponin and a history that distinguishes this pattern from the others in the family are all available.
  - Esperado: Requests the ECG and interprets it; relates the troponin to the ECG and the symptoms.
  - Alternativas aceptables: Interpreting the ECG without requesting the troponin when the pattern is already an occlusion equivalent; using POCUS as the second line of evidence.
- **D3** · ventana 0–40 min. A critical stenosis that is transiently reperfused: the antiplatelet and scheduled angiography, and never a provocation test.
  - Esperado: Gives an antiplatelet; arranges inpatient or scheduled angiography.
  - Alternativas aceptables: Admitting for monitoring with angiography stated as the plan.
- **D4** · ventana 10–90 min. The engine runs a clock and responds to what is given: an antiplatelet, a nitrate or an opioid changes observables that can be checked.
  - Esperado: States a reassessment interval; checks the response to what was executed.
  - Alternativas aceptables: Reassessing with the ECG rather than the vitals; a shorter interval than stated.
- **D5** · ventana 15–180 min. The patient feels well and the troponin is not raised. The decision is what happens next for a lesion that is not currently occluding, and what must not be done.
  - Esperado: Keeps the patient for definitive assessment rather than discharging; states that provocation testing is unsafe here.
  - Alternativas aceptables: Admitting without naming the test that must be avoided.

**Información accesible:** Arrival observables and the monitor; the patient's own history; the 12-lead ECG and, where the case carries them, additional leads; laboratory, troponin, POCUS and chest radiograph.

**Criterio de cierre:** A disposition is decided, or the horizon of the encounter is reached.

**Límites reales del motor:**
- The engine does not perform angiography; a referral is recorded, not its result.
- Serial troponin requires a new sample and the encounter may close first.

**Eventos críticos:**

- `acs_no_antiplatelet` — **Omisión crítica.** No antiplatelet is given in a recognised acute coronary syndrome.
  - Se activa cuando: The ECG is reported and the presentation is ischaemic, and no aspirin or P2Y12 inhibitor is executed within the window.
  - Información que debía estar disponible: The 12-lead ECG result; the presenting history.
  - Ventana y oportunidad: 0–30 min.
  - Alternativas aceptables: A P2Y12 inhibitor when aspirin is contraindicated or refused, stated as such; withholding it with a stated contraindication such as active bleeding or allergy.
  - Evidencia necesaria: An executed antiplatelet action, or its absence across every executed turn in the window.
  - Exclusiones: The encounter closed before the ECG was reported; the interpreter refused the order and the resident was never told what it could accept.
  - Dominios sobre los que pesa: D3.
- `acs_provocation_test` — **Acción peligrosa.** A provocation or stress test is ordered in an unstable coronary syndrome.
  - Se activa cuando: A stress test is ordered while the presentation is an acute coronary syndrome.
  - Información que debía estar disponible: The 12-lead ECG result; the troponin result when it was requested.
  - Ventana y oportunidad: 0–180 min.
  - Alternativas aceptables: Angiography, invasive assessment or specialist consultation; scheduled outpatient testing stated as after this episode, not now.
  - Evidencia necesaria: An executed or ordered stress test action in the record.
  - Exclusiones: The order was considered in writing but never submitted as an order.
  - Dominios sobre los que pesa: D3.

### `acs_70f_left_main`

- **D1** · ventana 0–20 min. The arrival ECG carries the ischaemic pattern of this case; there is a priority to decide between opening the artery, treating, and investigating further.
  - Esperado: Names the ischaemic pattern or the threat it represents within the window; acts on it before pursuing unrelated investigation.
  - Alternativas aceptables: Naming the threat without the eponym; acting first and naming it in the same turn.
- **D2** · ventana 0–30 min. A 12-lead ECG, a troponin and a history that distinguishes this pattern from the others in the family are all available.
  - Esperado: Requests the ECG and interprets it; relates the troponin to the ECG and the symptoms.
  - Alternativas aceptables: Interpreting the ECG without requesting the troponin when the pattern is already an occlusion equivalent; using POCUS as the second line of evidence.
- **D3** · ventana 0–40 min. A proximal lesion behind a diffuse pattern, in a patient who is already hypoperfused: the antiplatelet, the invasive pathway, and support meanwhile.
  - Esperado: Gives an antiplatelet; arranges immediate invasive assessment; addresses the hypoperfusion.
  - Alternativas aceptables: Oxygen and cautious volume before the invasive pathway is confirmed.
- **D4** · ventana 10–90 min. The engine runs a clock and responds to what is given: an antiplatelet, a nitrate or an opioid changes observables that can be checked.
  - Esperado: States a reassessment interval; checks the response to what was executed.
  - Alternativas aceptables: Reassessing with the ECG rather than the vitals; a shorter interval than stated.
- **D5** · ventana 15–180 min. The pattern is an occlusion: the decision is whether the artery is opened now and by whom, and what happens while that is arranged.
  - Esperado: Arranges reperfusion or the specialist assessment that decides it; states what is watched while it is arranged.
  - Alternativas aceptables: Thrombolysis with a stated reason when timely intervention is not available; transfer stated as the reperfusion pathway.

**Información accesible:** Arrival observables and the monitor; the patient's own history; the 12-lead ECG and, where the case carries them, additional leads; laboratory, troponin, POCUS and chest radiograph.

**Criterio de cierre:** A disposition is decided, or the horizon of the encounter is reached.

**Límites reales del motor:**
- The engine does not perform angiography; a referral is recorded, not its result.
- Serial troponin requires a new sample and the encounter may close first.

**Eventos críticos:**

- `acs_no_antiplatelet` — **Omisión crítica.** No antiplatelet is given in a recognised acute coronary syndrome.
  - Se activa cuando: The ECG is reported and the presentation is ischaemic, and no aspirin or P2Y12 inhibitor is executed within the window.
  - Información que debía estar disponible: The 12-lead ECG result; the presenting history.
  - Ventana y oportunidad: 0–30 min.
  - Alternativas aceptables: A P2Y12 inhibitor when aspirin is contraindicated or refused, stated as such; withholding it with a stated contraindication such as active bleeding or allergy.
  - Evidencia necesaria: An executed antiplatelet action, or its absence across every executed turn in the window.
  - Exclusiones: The encounter closed before the ECG was reported; the interpreter refused the order and the resident was never told what it could accept.
  - Dominios sobre los que pesa: D3.
- `acs_provocation_test` — **Acción peligrosa.** A provocation or stress test is ordered in an unstable coronary syndrome.
  - Se activa cuando: A stress test is ordered while the presentation is an acute coronary syndrome.
  - Información que debía estar disponible: The 12-lead ECG result; the troponin result when it was requested.
  - Ventana y oportunidad: 0–180 min.
  - Alternativas aceptables: Angiography, invasive assessment or specialist consultation; scheduled outpatient testing stated as after this episode, not now.
  - Evidencia necesaria: An executed or ordered stress test action in the record.
  - Exclusiones: The order was considered in writing but never submitted as an order.
  - Dominios sobre los que pesa: D3.

### `asthma_24f`

- **D1** · ventana 0–15 min. Severe airflow obstruction is present at arrival and the work of breathing is visible on the monitor.
  - Esperado: Names the obstruction and its severity; treats before completing the investigation.
  - Alternativas aceptables: Naming severity by the effort and speech rather than by a peak flow.
- **D2** · ventana 0–30 min. The history, the chest examination and the blood gas distinguish a severe exacerbation from ventilatory failure.
  - Esperado: Examines the breathing or the chest; relates the gas or the effort to the severity.
  - Alternativas aceptables: Using the examination alone when the gas has not returned.
- **D3** · ventana 0–30 min. Bronchodilator, corticosteroid and oxygen are all executable, and the engine responds to each.
  - Esperado: Gives a bronchodilator; gives a corticosteroid.
  - Alternativas aceptables: Continuous nebulisation instead of repeated doses; magnesium added to the bronchodilator.
- **D4** · ventana 10–60 min. The engine moves the work of breathing and the saturation in response to treatment.
  - Esperado: States a reassessment interval; checks the work of breathing or the saturation.
  - Alternativas aceptables: Reassessing by the gas rather than the effort.
- **D5** · ventana 15–180 min. The response decides whether treatment continues, escalates, or the patient is observed and discharged.
  - Esperado: Decides on the basis of the response; states the next step and its destination.
  - Alternativas aceptables: Continuing the same treatment with a stated reason and a further check.

**Información accesible:** Arrival observables and the monitor; the patient's history; chest examination; arterial and venous blood gases, chest radiograph, laboratory.

**Criterio de cierre:** A disposition is decided, or the encounter reaches its horizon.

**Límites reales del motor:**
- Peak flow is not a study the engine reports.
- The engine does not model an inhaler technique.

**Eventos críticos:**

- `asthma_no_bronchodilator` — **Omisión crítica.** No bronchodilator is given in an asthma exacerbation.
  - Se activa cuando: The presentation is an asthma exacerbation with increased work of breathing and no bronchodilator is executed in the window.
  - Información que debía estar disponible: Arrival observables; the presenting history.
  - Ventana y oportunidad: 0–30 min.
  - Alternativas aceptables: Continuous nebulised bronchodilator; an intravenous bronchodilator stated as such.
  - Evidencia necesaria: An executed bronchodilator action, or its absence across the window.
  - Exclusiones: The encounter closed before any order could be executed.
  - Dominios sobre los que pesa: D3.

### `asthma_49m`

- **D1** · ventana 0–15 min. Fatigue and a rising carbon dioxide are present at arrival: this is ventilatory failure, not only obstruction.
  - Esperado: Names the ventilatory failure or the fatigue; acts with that urgency.
  - Alternativas aceptables: Naming exhaustion or a silent chest rather than the gas.
- **D2** · ventana 0–30 min. The gas shows hypercapnia and the examination shows the effort that precedes arrest.
  - Esperado: Requests or reads the blood gas; examines the breathing.
  - Alternativas aceptables: Acting on the clinical picture and stating that the gas will confirm it.
- **D3** · ventana 0–40 min. Bronchodilator and steroid continue while ventilatory support is the decision the case turns on.
  - Esperado: Gives a bronchodilator; addresses the ventilation with support or its preparation.
  - Alternativas aceptables: Non-invasive support before intubation; intubation with stated preparation.
- **D4** · ventana 5–60 min. The engine responds to support and to obstruction treatment separately.
  - Esperado: States a reassessment interval; checks the effort, the gas or the saturation.
  - Alternativas aceptables: A shorter interval than stated when the patient is deteriorating.
- **D5** · ventana 10–180 min. Whether support is escalated, maintained or withdrawn is decided on what the reassessment shows.
  - Esperado: Decides escalation or continuation on the observed response; states the destination and what is still pending.
  - Alternativas aceptables: Maintaining support with a stated reason and a further check.

**Información accesible:** Arrival observables and the monitor; the patient's history; chest examination; blood gases, chest radiograph, laboratory.

**Criterio de cierre:** A disposition is decided, or the encounter reaches its horizon.

**Límites reales del motor:**
- Peak flow is not reported.
- The engine models ventilation settings but not a bronchoscopy or a chest CT.

**Eventos críticos:**

- `asthma_no_bronchodilator` — **Omisión crítica.** No bronchodilator is given in an asthma exacerbation.
  - Se activa cuando: The presentation is an asthma exacerbation and no bronchodilator is executed in the window.
  - Información que debía estar disponible: Arrival observables; the presenting history.
  - Ventana y oportunidad: 0–30 min.
  - Alternativas aceptables: Continuous nebulised bronchodilator; an intravenous bronchodilator stated as such.
  - Evidencia necesaria: An executed bronchodilator action, or its absence across the window.
  - Exclusiones: The encounter closed before any order could be executed.
  - Dominios sobre los que pesa: D3.
- `asthma_no_ventilatory_support` — **Omisión crítica.** Ventilatory failure is left without any support or preparation for it.
  - Se activa cuando: The blood gas or the recorded effort shows ventilatory failure and neither oxygen, non-invasive support, bag-mask nor intubation is executed or prepared.
  - Información que debía estar disponible: The blood gas result or the recorded work of breathing.
  - Ventana y oportunidad: 0–60 min.
  - Alternativas aceptables: Non-invasive support; bag-mask ventilation; intubation; stating a ceiling of treatment.
  - Evidencia necesaria: The absence of any executed airway or ventilation action in the window.
  - Exclusiones: The gas was never reported within the encounter; the resident's support order was refused by the interpreter.
  - Dominios sobre los que pesa: D3, D5.

### `gi_bleed_57m`

- **D1** · ventana 0–20 min. Bleeding with hypoperfusion is visible in the arrival observables; volume and haemostasis compete for first place with investigation.
  - Esperado: Names the bleeding and the hypoperfusion; resuscitates before completing the workup.
  - Alternativas aceptables: Naming shock by the perfusion rather than by a pressure threshold.
- **D2** · ventana 0–30 min. The haemoglobin, the perfusion and the history of the bleeding are all obtainable, and the first haemoglobin does not yet show the whole loss.
  - Esperado: Requests the haemoglobin or the laboratory; relates the perfusion to the bleeding.
  - Alternativas aceptables: Acting on the perfusion before the haemoglobin returns, stated as such.
- **D3** · ventana 0–40 min. Transfusion, a proton pump inhibitor and the consultation that arranges haemostasis are all executable.
  - Esperado: Restores circulating volume or oxygen-carrying capacity; arranges the haemostasis pathway.
  - Alternativas aceptables: Crystalloid first with blood stated as next; an octreotide infusion where variceal bleeding is suspected.
- **D4** · ventana 10–60 min. The engine moves the pressure, the perfusion and the haemoglobin in response to what is given.
  - Esperado: States a reassessment interval; checks the perfusion or the pressure after volume.
  - Alternativas aceptables: Reassessing by the haemoglobin when a repeat sample was sent.
- **D5** · ventana 15–180 min. Continued bleeding, a stabilising response, or neither decides what follows and where.
  - Esperado: Decides continuation or escalation on the observed response; states the destination and what is pending.
  - Alternativas aceptables: Keeping the patient for observation with a stated threshold to escalate.

**Información accesible:** Arrival observables and the monitor; the patient's history; haemoglobin, laboratory, lactate, blood gases, POCUS.

**Criterio de cierre:** A disposition is decided, or the encounter reaches its horizon.

**Límites reales del motor:**
- The engine does not perform endoscopy; the referral is recorded, not its result.
- A repeat haemoglobin requires a new sample and the encounter may close first.

**Eventos críticos:**

- `gi_no_resuscitation` — **Omisión crítica.** Haemorrhagic hypoperfusion is left without volume or blood.
  - Se activa cuando: The arrival observables show hypoperfusion from bleeding and neither blood nor fluid is executed in the window.
  - Información que debía estar disponible: Arrival observables; the presenting history of bleeding.
  - Ventana y oportunidad: 0–40 min.
  - Alternativas aceptables: Packed red cells; crystalloid stated as the bridge to blood; a stated ceiling of treatment.
  - Evidencia necesaria: The absence of any executed blood or fluid action in the window.
  - Exclusiones: The encounter closed before any order could be executed; vascular access failed in the engine and the resident addressed it.
  - Dominios sobre los que pesa: D3.

### `gi_bleed_72f`

- **D1** · ventana 0–20 min. The pain is limited and the arrival picture is anaemia and hypoperfusion: the threat has to be recognised without a dramatic complaint.
  - Esperado: Names the clinically important bleeding despite the quiet presentation; acts on the perfusion rather than on the symptom.
  - Alternativas aceptables: Naming the anaemia and its consequence rather than the bleeding itself.
- **D2** · ventana 0–30 min. The haemoglobin, the perfusion and the history of the bleeding are all obtainable, and the first haemoglobin does not yet show the whole loss.
  - Esperado: Requests the haemoglobin or the laboratory; relates the perfusion to the bleeding.
  - Alternativas aceptables: Acting on the perfusion before the haemoglobin returns, stated as such.
- **D3** · ventana 0–40 min. Transfusion, a proton pump inhibitor and the consultation that arranges haemostasis are all executable.
  - Esperado: Restores circulating volume or oxygen-carrying capacity; arranges the haemostasis pathway.
  - Alternativas aceptables: Crystalloid first with blood stated as next; an octreotide infusion where variceal bleeding is suspected.
- **D4** · ventana 10–60 min. The engine moves the pressure, the perfusion and the haemoglobin in response to what is given.
  - Esperado: States a reassessment interval; checks the perfusion or the pressure after volume.
  - Alternativas aceptables: Reassessing by the haemoglobin when a repeat sample was sent.
- **D5** · ventana 15–180 min. Continued bleeding, a stabilising response, or neither decides what follows and where.
  - Esperado: Decides continuation or escalation on the observed response; states the destination and what is pending.
  - Alternativas aceptables: Keeping the patient for observation with a stated threshold to escalate.

**Información accesible:** Arrival observables and the monitor; the patient's history; haemoglobin, laboratory, lactate, blood gases, POCUS.

**Criterio de cierre:** A disposition is decided, or the encounter reaches its horizon.

**Límites reales del motor:**
- The engine does not perform endoscopy; the referral is recorded, not its result.
- A repeat haemoglobin requires a new sample and the encounter may close first.

**Eventos críticos:**

- `gi_no_resuscitation` — **Omisión crítica.** Haemorrhagic hypoperfusion is left without volume or blood.
  - Se activa cuando: The arrival observables show hypoperfusion from bleeding and neither blood nor fluid is executed in the window.
  - Información que debía estar disponible: Arrival observables; the presenting history of bleeding.
  - Ventana y oportunidad: 0–40 min.
  - Alternativas aceptables: Packed red cells; crystalloid stated as the bridge to blood; a stated ceiling of treatment.
  - Evidencia necesaria: The absence of any executed blood or fluid action in the window.
  - Exclusiones: The encounter closed before any order could be executed; vascular access failed in the engine and the resident addressed it.
  - Dominios sobre los que pesa: D3.

### `hypoglycemia_28m`

- **D1** · ventana 0–15 min. The glucose is low enough to explain the altered state and the correction is time-critical.
  - Esperado: Names the hypoglycaemia or the neuroglycopenia; treats it first.
  - Alternativas aceptables: Naming the altered state and the glucose together.
- **D2** · ventana 0–20 min. A bedside glucose, the history of the exposure and the neurological examination are all available.
  - Esperado: Requests or reads the bedside glucose; relates the mental state to the glucose.
  - Alternativas aceptables: Treating on the history and confirming with the glucose in the same turn.
- **D3** · ventana 0–30 min. Intravenous dextrose is executable, and vascular access may have to be established first.
  - Esperado: Gives dextrose; secures the route it needs.
  - Alternativas aceptables: Glucagon when access is not available; oral carbohydrate once the patient is alert.
- **D4** · ventana 5–60 min. The engine raises the glucose and the mental state in response, and lets them fall again where the case carries that risk.
  - Esperado: States a reassessment interval; rechecks the glucose or the mental state.
  - Alternativas aceptables: Rechecking the mental state rather than the number.
- **D5** · ventana 15–180 min. Once the glucose and the consciousness recover, the decision is whether this patient can safely leave and what would bring them back.
  - Esperado: Decides the destination on the recovery observed; states what is still pending.
  - Alternativas aceptables: Keeping the patient for a stated period before deciding.

**Información accesible:** Arrival observables and the monitor; the patient's or the witness's history; bedside glucose, laboratory, neurological examination.

**Criterio de cierre:** A disposition is decided, or the encounter reaches its horizon.

**Límites reales del motor:**
- The engine does not model a continuous glucose monitor.
- An oral route is refused while the patient is not fully alert, by design.

**Eventos críticos:**

- `hypo_no_glucose` — **Omisión crítica.** Neuroglycopenia is left uncorrected.
  - Se activa cuando: The bedside glucose is low and the patient is not alert, and no dextrose, glucagon or oral carbohydrate is executed in the window.
  - Información que debía estar disponible: The bedside glucose result; the recorded mental status.
  - Ventana y oportunidad: 0–30 min.
  - Alternativas aceptables: Intravenous dextrose; glucagon when there is no vascular access; oral carbohydrate once the patient is alert enough to swallow.
  - Evidencia necesaria: The absence of any executed glucose-raising action in the window.
  - Exclusiones: Vascular access failed in the engine and the resident addressed it; the encounter closed before the glucose was reported.
  - Dominios sobre los que pesa: D3.

### `hypoglycemia_76f`

- **D1** · ventana 0–15 min. The glucose is low and the agent that caused it is long-acting: correction is urgent and the recurrence is the reason the encounter continues.
  - Esperado: Names the hypoglycaemia or the neuroglycopenia; treats it first.
  - Alternativas aceptables: Naming the altered state and the glucose together.
- **D2** · ventana 0–20 min. A bedside glucose, the history of the exposure and the neurological examination are all available.
  - Esperado: Requests or reads the bedside glucose; relates the mental state to the glucose.
  - Alternativas aceptables: Treating on the history and confirming with the glucose in the same turn.
- **D3** · ventana 0–30 min. Dextrose corrects it; the recurrence risk is what the rest of the management addresses.
  - Esperado: Gives dextrose; plans for the recurrence the agent carries.
  - Alternativas aceptables: A dextrose infusion rather than repeated boluses; octreotide stated for a sulfonylurea.
- **D4** · ventana 5–60 min. The engine raises the glucose and the mental state in response, and lets them fall again where the case carries that risk.
  - Esperado: States a reassessment interval; rechecks the glucose or the mental state.
  - Alternativas aceptables: Rechecking the mental state rather than the number.
- **D5** · ventana 15–180 min. A sulfonylurea patient who recovers is not a patient who can leave: the decision is observation and its length.
  - Esperado: Arranges continued observation rather than discharge; states what is watched and for how long.
  - Alternativas aceptables: Admission stated as the observation.

**Información accesible:** Arrival observables and the monitor; the patient's or the witness's history; bedside glucose, laboratory, neurological examination.

**Criterio de cierre:** A disposition is decided, or the encounter reaches its horizon.

**Límites reales del motor:**
- The engine does not model a continuous glucose monitor.
- An oral route is refused while the patient is not fully alert, by design.

**Eventos críticos:**

- `hypo_no_glucose` — **Omisión crítica.** Neuroglycopenia is left uncorrected.
  - Se activa cuando: The bedside glucose is low and the patient is not alert, and no dextrose, glucagon or oral carbohydrate is executed in the window.
  - Información que debía estar disponible: The bedside glucose result; the recorded mental status.
  - Ventana y oportunidad: 0–30 min.
  - Alternativas aceptables: Intravenous dextrose; glucagon when there is no vascular access; oral carbohydrate once the patient is alert enough to swallow.
  - Evidencia necesaria: The absence of any executed glucose-raising action in the window.
  - Exclusiones: Vascular access failed in the engine and the resident addressed it; the encounter closed before the glucose was reported.
  - Dominios sobre los que pesa: D3.
- `hypo_unsafe_discharge` — **Omisión crítica.** A patient whose hypoglycaemia was caused by a long-acting agent is discharged without observation.
  - Se activa cuando: A discharge disposition is executed after a sulfonylurea-associated hypoglycaemia, without any recorded plan for continued observation.
  - Información que debía estar disponible: The history of the causative agent; the recorded recurrence risk.
  - Ventana y oportunidad: 0–180 min.
  - Alternativas aceptables: Admission; observation with a stated duration; discharge with an explicitly arranged early review.
  - Evidencia necesaria: An executed discharge disposition with no observation stated in the same encounter.
  - Exclusiones: The encounter reached its horizon before any disposition was decided.
  - Dominios sobre los que pesa: D5.

### `hypoglycemia_54m_thiamine`

- **D1** · ventana 0–15 min. The glucose is low and this patient is thiamine-depleted: correcting one threat without the other creates a second.
  - Esperado: Names the hypoglycaemia or the neuroglycopenia; treats it first.
  - Alternativas aceptables: Naming the altered state and the glucose together.
- **D2** · ventana 0–20 min. A bedside glucose, the history of the exposure and the neurological examination are all available.
  - Esperado: Requests or reads the bedside glucose; relates the mental state to the glucose.
  - Alternativas aceptables: Treating on the history and confirming with the glucose in the same turn.
- **D3** · ventana 0–30 min. Dextrose and thiamine are both executable, and the order in which they are given is the point of the case.
  - Esperado: Gives dextrose; gives thiamine.
  - Alternativas aceptables: Thiamine first; both in the same submission.
- **D4** · ventana 5–60 min. The engine raises the glucose and the mental state in response, and lets them fall again where the case carries that risk.
  - Esperado: States a reassessment interval; rechecks the glucose or the mental state.
  - Alternativas aceptables: Rechecking the mental state rather than the number.
- **D5** · ventana 15–180 min. The decision is continued treatment of the deficiency and where that happens, not only the glucose.
  - Esperado: Decides the destination with the deficiency in it; states what continues.
  - Alternativas aceptables: Admission stated as the continuation.

**Información accesible:** Arrival observables and the monitor; the patient's or the witness's history; bedside glucose, laboratory, neurological examination.

**Criterio de cierre:** A disposition is decided, or the encounter reaches its horizon.

**Límites reales del motor:**
- The engine does not model a continuous glucose monitor.
- An oral route is refused while the patient is not fully alert, by design.

**Eventos críticos:**

- `hypo_no_glucose` — **Omisión crítica.** Neuroglycopenia is left uncorrected.
  - Se activa cuando: The bedside glucose is low and the patient is not alert, and no dextrose, glucagon or oral carbohydrate is executed in the window.
  - Información que debía estar disponible: The bedside glucose result; the recorded mental status.
  - Ventana y oportunidad: 0–30 min.
  - Alternativas aceptables: Intravenous dextrose; glucagon when there is no vascular access; oral carbohydrate once the patient is alert enough to swallow.
  - Evidencia necesaria: The absence of any executed glucose-raising action in the window.
  - Exclusiones: Vascular access failed in the engine and the resident addressed it; the encounter closed before the glucose was reported.
  - Dominios sobre los que pesa: D3.
- `hypo_no_thiamine` — **Omisión crítica.** Glucose is given to a thiamine-depleted patient and no thiamine is given.
  - Se activa cuando: Dextrose is executed in a patient the case declares thiamine-depleted and no thiamine is executed within the window.
  - Información que debía estar disponible: The history of chronic alcohol use or malnutrition.
  - Ventana y oportunidad: 0–60 min.
  - Alternativas aceptables: Thiamine before the dextrose; thiamine in the same submission.
  - Evidencia necesaria: An executed dextrose action with no executed thiamine action in the window.
  - Exclusiones: The encounter closed before a second order could be executed.
  - Dominios sobre los que pesa: D3.

### `opioid_35m`

- **D1** · ventana 0–10 min. The respiratory rate at arrival is the threat, and it is the breathing rather than the diagnosis that has to be addressed first.
  - Esperado: Names the ventilatory depression; supports the ventilation first.
  - Alternativas aceptables: Naming the toxidrome and acting on the breathing in the same turn.
- **D2** · ventana 0–30 min. The respiratory rate, the effort, the pupils and the blood gas separate an opioid effect from another cause of the altered state.
  - Esperado: Reads the respiratory rate and the effort; considers the gas or the glucose.
  - Alternativas aceptables: Treating first and confirming with the response to the antagonist.
- **D3** · ventana 0–30 min. Bag-mask ventilation, oxygen and an opioid antagonist are all executable, and the engine separates supporting the breathing from reversing the drug.
  - Esperado: Supports the ventilation; gives an antagonist or states why it is withheld.
  - Alternativas aceptables: Ventilating and titrating the antagonist to the breathing, not to wakefulness; supporting without an antagonist when the airway is already secured.
- **D4** · ventana 5–60 min. The engine moves the respiratory rate and the mental state in response, and lets them fall again where the exposure is long-acting.
  - Esperado: States a reassessment interval; rechecks the breathing and the mental state.
  - Alternativas aceptables: Rechecking the saturation alone when the rate is the variable that matters.
- **D5** · ventana 15–180 min. Whether the patient can leave depends on what the exposure was and how long its effect outlasts the antagonist.
  - Esperado: Decides the destination on the observed response and the exposure; states what is watched.
  - Alternativas aceptables: Observation with a stated duration.

**Información accesible:** Arrival observables and the monitor; the witness's history; blood gases, bedside glucose, neurological examination.

**Criterio de cierre:** A disposition is decided, or the encounter reaches its horizon.

**Límites reales del motor:**
- The engine does not model a urine toxicology screen.
- Pupil size is described in the examination, not measured.

**Eventos críticos:**

- `opioid_no_ventilatory_support` — **Omisión crítica.** Ventilatory depression is left without support or reversal.
  - Se activa cuando: The recorded respiratory rate is depressed and neither oxygen, bag-mask ventilation, an antagonist nor intubation is executed in the window.
  - Información que debía estar disponible: Arrival observables, including the respiratory rate.
  - Ventana y oportunidad: 0–20 min.
  - Alternativas aceptables: Bag-mask ventilation; an opioid antagonist; intubation; oxygen stated as the bridge while the antagonist is drawn up.
  - Evidencia necesaria: The absence of any executed airway, oxygen or antagonist action in the window.
  - Exclusiones: The encounter closed before any order could be executed.
  - Dominios sobre los que pesa: D1, D3.

### `opioid_67f`

- **D1** · ventana 0–10 min. The ventilation is depressed and the agent is long-acting: the first correction will not be the last.
  - Esperado: Names the ventilatory depression; supports the ventilation first.
  - Alternativas aceptables: Naming the toxidrome and acting on the breathing in the same turn.
- **D2** · ventana 0–30 min. The respiratory rate, the effort, the pupils and the blood gas separate an opioid effect from another cause of the altered state.
  - Esperado: Reads the respiratory rate and the effort; considers the gas or the glucose.
  - Alternativas aceptables: Treating first and confirming with the response to the antagonist.
- **D3** · ventana 0–30 min. Bag-mask ventilation, oxygen and an opioid antagonist are all executable, and the engine separates supporting the breathing from reversing the drug.
  - Esperado: Supports the ventilation; gives an antagonist or states why it is withheld.
  - Alternativas aceptables: Ventilating and titrating the antagonist to the breathing, not to wakefulness; supporting without an antagonist when the airway is already secured.
- **D4** · ventana 5–60 min. The engine moves the respiratory rate and the mental state in response, and lets them fall again where the exposure is long-acting.
  - Esperado: States a reassessment interval; rechecks the breathing and the mental state.
  - Alternativas aceptables: Rechecking the saturation alone when the rate is the variable that matters.
- **D5** · ventana 15–180 min. An antagonist that is shorter than the opioid makes observation the decision, not the response to the first dose.
  - Esperado: Arranges observation for recurrence rather than discharging on the first response; states the duration or what would bring the depression back.
  - Alternativas aceptables: An antagonist infusion stated as the reason observation continues; admission.

**Información accesible:** Arrival observables and the monitor; the witness's history; blood gases, bedside glucose, neurological examination.

**Criterio de cierre:** A disposition is decided, or the encounter reaches its horizon.

**Límites reales del motor:**
- The engine does not model a urine toxicology screen.
- Pupil size is described in the examination, not measured.

**Eventos críticos:**

- `opioid_no_ventilatory_support` — **Omisión crítica.** Ventilatory depression is left without support or reversal.
  - Se activa cuando: The recorded respiratory rate is depressed and neither oxygen, bag-mask ventilation, an antagonist nor intubation is executed in the window.
  - Información que debía estar disponible: Arrival observables, including the respiratory rate.
  - Ventana y oportunidad: 0–20 min.
  - Alternativas aceptables: Bag-mask ventilation; an opioid antagonist; intubation; oxygen stated as the bridge while the antagonist is drawn up.
  - Evidencia necesaria: The absence of any executed airway, oxygen or antagonist action in the window.
  - Exclusiones: The encounter closed before any order could be executed.
  - Dominios sobre los que pesa: D1, D3.
- `opioid_unsafe_discharge` — **Omisión crítica.** A patient exposed to a long-acting opioid is discharged on the response to a short-acting antagonist.
  - Se activa cuando: A discharge disposition is executed after an antagonist was given for a long-acting exposure, with no observation stated in the encounter.
  - Información que debía estar disponible: The history of the exposure; the recorded response to the antagonist.
  - Ventana y oportunidad: 0–180 min.
  - Alternativas aceptables: Admission; observation with a stated duration; an antagonist infusion.
  - Evidencia necesaria: An executed discharge disposition with no observation stated.
  - Exclusiones: The encounter reached its horizon before any disposition was decided.
  - Dominios sobre los que pesa: D5.

### `pneumonia_46f`

- **D1** · ventana 0–20 min. Hypoxaemia and impaired perfusion are both present at arrival and both need a decision about what comes first.
  - Esperado: Names the hypoxaemia or the hypoperfusion; treats before the imaging returns.
  - Alternativas aceptables: Naming the hypoperfusion rather than a sepsis label.
- **D2** · ventana 0–40 min. The radiograph, the laboratory, the lactate and the chest examination are all available.
  - Esperado: Requests the radiograph or the laboratory; relates the findings to the physiology.
  - Alternativas aceptables: Acting on the radiograph before the laboratory returns.
- **D3** · ventana 0–60 min. Antibiotics, oxygen and fluid are all executable and the engine responds to each.
  - Esperado: Gives an antibiotic; addresses the oxygenation; addresses the perfusion.
  - Alternativas aceptables: Fluid withheld with a stated reason such as congestion; oxygen titrated rather than given at a fixed flow.
- **D4** · ventana 15–90 min. The engine moves the saturation, the perfusion and the lactate in response.
  - Esperado: States a reassessment interval; checks the oxygenation or the perfusion.
  - Alternativas aceptables: Rechecking the lactate when a repeat sample was sent.
- **D5** · ventana 20–180 min. The response to the first hour decides the level of care and what continues.
  - Esperado: Decides the destination on the observed response; states what is pending.
  - Alternativas aceptables: Escalating the level of care with a stated threshold.

**Información accesible:** Arrival observables and the monitor; the patient's or an informant's history; chest radiograph, laboratory, lactate, blood gases, POCUS, cultures.

**Criterio de cierre:** A disposition is decided, or the encounter reaches its horizon.

**Límites reales del motor:**
- Culture results are pending within the encounter, by design.
- The engine does not model a chest CT.

**Eventos críticos:**

- `pneumonia_no_antibiotic` — **Omisión crítica.** No antibiotic is given in a pneumonia with hypoperfusion.
  - Se activa cuando: The presentation is a pneumonia with impaired perfusion and no antibiotic is executed in the window.
  - Información que debía estar disponible: Arrival observables; the presenting history; the chest radiograph where it was requested.
  - Ventana y oportunidad: 0–60 min.
  - Alternativas aceptables: Any of the antibiotics the engine models, with a route; a stated ceiling of treatment.
  - Evidencia necesaria: The absence of an executed antibiotic action in the window.
  - Exclusiones: The encounter closed before any order could be executed; the interpreter refused the agent and never said what it accepts.
  - Dominios sobre los que pesa: D3.

### `pneumonia_83m`

- **D1** · ventana 0–20 min. The arrival complaint is nonspecific and the altered state is the finding that has to be recognised as a threat rather than as age.
  - Esperado: Names the altered state as something to explain; does not attribute it to age alone.
  - Alternativas aceptables: Naming the hypoperfusion rather than a sepsis label.
- **D2** · ventana 0–40 min. The new confusion has to be investigated alongside the infection; glucose, gases and imaging are all available.
  - Esperado: Investigates the altered state as well as the infection; relates the findings to the physiology.
  - Alternativas aceptables: Acting on the radiograph before the laboratory returns.
- **D3** · ventana 0–60 min. Antibiotics, oxygen and fluid are all executable and the engine responds to each.
  - Esperado: Gives an antibiotic; addresses the oxygenation; addresses the perfusion.
  - Alternativas aceptables: Fluid withheld with a stated reason such as congestion; oxygen titrated rather than given at a fixed flow.
- **D4** · ventana 15–90 min. The engine moves the saturation, the perfusion and the lactate in response.
  - Esperado: States a reassessment interval; checks the oxygenation or the perfusion.
  - Alternativas aceptables: Rechecking the lactate when a repeat sample was sent.
- **D5** · ventana 20–180 min. The response to the first hour decides the level of care and what continues.
  - Esperado: Decides the destination on the observed response; states what is pending.
  - Alternativas aceptables: Escalating the level of care with a stated threshold.

**Información accesible:** Arrival observables and the monitor; the patient's or an informant's history; chest radiograph, laboratory, lactate, blood gases, POCUS, cultures.

**Criterio de cierre:** A disposition is decided, or the encounter reaches its horizon.

**Límites reales del motor:**
- Culture results are pending within the encounter, by design.
- The engine does not model a chest CT.

**Eventos críticos:**

- `pneumonia_no_antibiotic` — **Omisión crítica.** No antibiotic is given in a pneumonia with hypoperfusion.
  - Se activa cuando: The presentation is a pneumonia with impaired perfusion and no antibiotic is executed in the window.
  - Información que debía estar disponible: Arrival observables; the presenting history; the chest radiograph where it was requested.
  - Ventana y oportunidad: 0–60 min.
  - Alternativas aceptables: Any of the antibiotics the engine models, with a route; a stated ceiling of treatment.
  - Evidencia necesaria: The absence of an executed antibiotic action in the window.
  - Exclusiones: The encounter closed before any order could be executed; the interpreter refused the agent and never said what it accepts.
  - Dominios sobre los que pesa: D3.
- `pneumonia_unexamined_altered_state` — **Omisión crítica.** A new altered mental state is never investigated.
  - Se activa cuando: The patient arrives with an altered mental state and no glucose, neurological examination or imaging of the head is obtained in the window.
  - Información que debía estar disponible: Arrival observables, including the mental status.
  - Ventana y oportunidad: 0–60 min.
  - Alternativas aceptables: A bedside glucose; a neurological examination; stating that the infection explains it and checking the glucose anyway.
  - Evidencia necesaria: The absence of any executed glucose, neurological examination or head imaging.
  - Exclusiones: The encounter closed before a second order could be executed.
  - Dominios sobre los que pesa: D2.

### `pulmonary_edema_58m`

- **D1** · ventana 0–15 min. The pressure is high and the breathing is failing: both the loading and the ventilation need a decision in the first minutes.
  - Esperado: Names the respiratory failure and its cardiac cause; supports the breathing before completing the investigation.
  - Alternativas aceptables: Naming the congestion and acting on the breathing in the same turn.
- **D2** · ventana 0–30 min. POCUS, the chest radiograph, the blood gas and the examination separate congestion from the other causes of this presentation.
  - Esperado: Requests POCUS or the radiograph; relates the findings to the physiology.
  - Alternativas aceptables: Acting on the examination and confirming with POCUS in the same turn.
- **D3** · ventana 0–40 min. Non-invasive support, a nitrate and a diuretic are all executable, and in a hypertensive oedema the loading is what the nitrate addresses.
  - Esperado: Supports the breathing; reduces the cardiac loading.
  - Alternativas aceptables: A diuretic stated as secondary to the nitrate; oxygen first while support is set up.
- **D4** · ventana 5–60 min. The engine moves the pressure, the saturation and the work of breathing in response, and a nitrate has to be watched against the pressure it lowers.
  - Esperado: States a reassessment interval; checks the pressure as well as the breathing.
  - Alternativas aceptables: A shorter interval while a nitrate is running.
- **D5** · ventana 15–180 min. The pressure and the breathing after the first intervention decide whether support continues, escalates or can be reduced.
  - Esperado: Decides continuation or escalation on the observed response; states the destination and what is watched.
  - Alternativas aceptables: Maintaining the support with a stated reason and a further check.

**Información accesible:** Arrival observables and the monitor; the patient's history; POCUS, chest radiograph, blood gases, laboratory, troponin.

**Criterio de cierre:** A disposition is decided, or the encounter reaches its horizon.

**Límites reales del motor:**
- The engine reports a nitrate as an infusion rate, not as a titration protocol.
- Urine output is reported only where the case measures it.

**Eventos críticos:**

- `edema_no_ventilatory_support` — **Omisión crítica.** Respiratory failure from congestion is left without oxygen or ventilatory support.
  - Se activa cuando: The arrival observables show hypoxaemia with increased work of breathing and no oxygen, non-invasive support or intubation is executed in the window.
  - Información que debía estar disponible: Arrival observables.
  - Ventana y oportunidad: 0–30 min.
  - Alternativas aceptables: Non-invasive support; oxygen at a stated device and flow; intubation.
  - Evidencia necesaria: The absence of any executed oxygen or ventilation action in the window.
  - Exclusiones: The encounter closed before any order could be executed.
  - Dominios sobre los que pesa: D1, D3.
- `edema_volume_loading` — **Acción peligrosa.** A fluid bolus is given in acute cardiogenic pulmonary oedema.
  - Se activa cuando: A crystalloid bolus is executed while the record shows congestion and no cause of hypovolaemia has been established.
  - Información que debía estar disponible: Arrival observables; the POCUS or radiograph where it was requested.
  - Ventana y oportunidad: 0–180 min.
  - Alternativas aceptables: A small stated challenge with an explicit hypovolaemic rationale and a reassessment attached; withholding fluid.
  - Evidencia necesaria: An executed fluid action with a recorded congested state.
  - Exclusiones: The case established a hypovolaemic contributor before the bolus.
  - Dominios sobre los que pesa: D3.

### `pulmonary_edema_75f`

- **D1** · ventana 0–15 min. Respiratory distress with congestion, in a patient whose renal function and pressure limit what can be given.
  - Esperado: Names the respiratory failure and its cardiac cause; supports the breathing before completing the investigation.
  - Alternativas aceptables: Naming the congestion and acting on the breathing in the same turn.
- **D2** · ventana 0–30 min. POCUS, the chest radiograph, the blood gas and the examination separate congestion from the other causes of this presentation.
  - Esperado: Requests POCUS or the radiograph; relates the findings to the physiology.
  - Alternativas aceptables: Acting on the examination and confirming with POCUS in the same turn.
- **D3** · ventana 0–40 min. Support, a nitrate and a diuretic are executable, and this patient's pressure and renal function constrain the choice.
  - Esperado: Supports the breathing; addresses the congestion within the pressure available.
  - Alternativas aceptables: Withholding the nitrate with a stated pressure reason; a diuretic with the renal function stated.
- **D4** · ventana 5–60 min. The engine moves the pressure, the saturation and the work of breathing in response, and a nitrate has to be watched against the pressure it lowers.
  - Esperado: States a reassessment interval; checks the pressure as well as the breathing.
  - Alternativas aceptables: A shorter interval while a nitrate is running.
- **D5** · ventana 15–180 min. The response, the pressure and the renal function decide what continues and where.
  - Esperado: Decides continuation or escalation on the observed response; states the destination and what is watched.
  - Alternativas aceptables: Maintaining the support with a stated reason and a further check.

**Información accesible:** Arrival observables and the monitor; the patient's history; POCUS, chest radiograph, blood gases, laboratory, troponin.

**Criterio de cierre:** A disposition is decided, or the encounter reaches its horizon.

**Límites reales del motor:**
- The engine reports a nitrate as an infusion rate, not as a titration protocol.
- Urine output is reported only where the case measures it.

**Eventos críticos:**

- `edema_no_ventilatory_support` — **Omisión crítica.** Respiratory failure from congestion is left without oxygen or ventilatory support.
  - Se activa cuando: The arrival observables show hypoxaemia with increased work of breathing and no oxygen, non-invasive support or intubation is executed in the window.
  - Información que debía estar disponible: Arrival observables.
  - Ventana y oportunidad: 0–30 min.
  - Alternativas aceptables: Non-invasive support; oxygen at a stated device and flow; intubation.
  - Evidencia necesaria: The absence of any executed oxygen or ventilation action in the window.
  - Exclusiones: The encounter closed before any order could be executed.
  - Dominios sobre los que pesa: D1, D3.
- `edema_volume_loading` — **Acción peligrosa.** A fluid bolus is given in acute cardiogenic pulmonary oedema.
  - Se activa cuando: A crystalloid bolus is executed while the record shows congestion and no cause of hypovolaemia has been established.
  - Información que debía estar disponible: Arrival observables; the POCUS or radiograph where it was requested.
  - Ventana y oportunidad: 0–180 min.
  - Alternativas aceptables: A small stated challenge with an explicit hypovolaemic rationale and a reassessment attached; withholding fluid.
  - Evidencia necesaria: An executed fluid action with a recorded congested state.
  - Exclusiones: The case established a hypovolaemic contributor before the bolus.
  - Dominios sobre los que pesa: D3.

### `pulmonary_embolism_33f`

- **D1** · ventana 0–20 min. Sudden breathlessness with tachycardia and hypoxaemia, in a patient who offers anxiety as the explanation: the threat has to be recognised against that anchor.
  - Esperado: Names the hypoxaemia and the tachycardia as a threat; does not accept the offered explanation without objective evidence.
  - Alternativas aceptables: Naming the hypoxaemia and the tachycardia rather than the diagnosis.
- **D2** · ventana 0–45 min. The POCUS, the CT pulmonary angiogram, the D-dimer with its age-adjusted limit, the blood gas and the calf examination are all available, and the case's own alternative explanation has to be addressed rather than assumed.
  - Esperado: Obtains objective evidence rather than accepting the offered explanation; examines or investigates for the source.
  - Alternativas aceptables: POCUS as the first objective evidence when the patient cannot be moved; treating on clinical grounds with the confirmation stated as pending.
- **D3** · ventana 0–60 min. Anticoagulation, oxygen and the specialist pathway are executable; without sustained hypotension, thrombolysis is not the treatment this patient needs.
  - Esperado: Anticoagulates or states why it is withheld; addresses the oxygenation.
  - Alternativas aceptables: Awaiting the confirming study with anticoagulation stated as pending it; oxygen titrated rather than given at a fixed flow.
- **D4** · ventana 10–90 min. The engine moves the saturation, the rate and the pressure in response, and the right ventricle is where deterioration shows first.
  - Esperado: States a reassessment interval; checks the oxygenation and the haemodynamics.
  - Alternativas aceptables: Reassessing by POCUS rather than by the vitals.
- **D5** · ventana 20–180 min. The haemodynamics decide the level of care and whether reperfusion enters the plan at all.
  - Esperado: Decides the destination on the observed haemodynamics; states what would change the plan.
  - Alternativas aceptables: Keeping the patient monitored with a stated threshold to escalate.

**Información accesible:** Arrival observables and the monitor; the patient's history; POCUS, CT pulmonary angiogram, D-dimer, blood gases, troponin, radiograph; the examination of the legs, which the case authors.

**Criterio de cierre:** A disposition is decided, or the encounter reaches its horizon.

**Límites reales del motor:**
- The engine records a reperfusion referral, not its result.
- The CT angiogram takes twenty minutes of simulated time and the encounter may close first.

**Eventos críticos:**

- `pe_no_anticoagulation` — **Omisión crítica.** No anticoagulation is given or stated as withheld in a recognised embolism.
  - Se activa cuando: Objective or clinical evidence of embolism is recorded and no anticoagulation is executed in the window, with no contraindication stated.
  - Información que debía estar disponible: The POCUS, angiogram or D-dimer where requested; the presenting history.
  - Ventana y oportunidad: 0–60 min.
  - Alternativas aceptables: Anticoagulation of any modelled agent and route; withholding it with a stated bleeding contraindication; proceeding directly to reperfusion with a stated reason.
  - Evidencia necesaria: The absence of an executed anticoagulation action in the window.
  - Exclusiones: The encounter closed before the confirming study was reported.
  - Dominios sobre los que pesa: D3.
- `pe_unindicated_thrombolysis` — **Acción peligrosa.** Systemic thrombolysis is given without sustained hypotension, in a patient with a recent operation.
  - Se activa cuando: A thrombolytic is executed while the record shows no sustained hypotension and the history carries a recent surgical site.
  - Información que debía estar disponible: Arrival and subsequent observables; the surgical history.
  - Ventana y oportunidad: 0–180 min.
  - Alternativas aceptables: Anticoagulation; arranging a reperfusion-capable team without giving the drug; thrombolysis after sustained hypotension is recorded.
  - Evidencia necesaria: An executed thrombolysis action with the record showing no sustained hypotension.
  - Exclusiones: The record shows sustained hypotension within the engine's own criterion.
  - Dominios sobre los que pesa: D3.

### `pulmonary_embolism_61m`

- **D1** · ventana 0–20 min. Obstructive shock: the pressure, the rate and the perfusion all demand action before the confirming study returns.
  - Esperado: Names the shock and its obstructive cause; acts before the angiogram returns.
  - Alternativas aceptables: Naming the hypoxaemia and the tachycardia rather than the diagnosis.
- **D2** · ventana 0–45 min. The POCUS, the CT pulmonary angiogram, the D-dimer with its age-adjusted limit, the blood gas and the calf examination are all available, and the case's own alternative explanation has to be addressed rather than assumed.
  - Esperado: Obtains objective evidence rather than accepting the offered explanation; examines or investigates for the source.
  - Alternativas aceptables: POCUS as the first objective evidence when the patient cannot be moved; treating on clinical grounds with the confirmation stated as pending.
- **D3** · ventana 0–60 min. Anticoagulation, oxygen, the reperfusion-capable team and, in sustained hypotension, thrombolysis are all executable.
  - Esperado: Anticoagulates or states why it is withheld; involves a reperfusion-capable team rapidly.
  - Alternativas aceptables: Thrombolysis with the sustained hypotension stated; cautious volume with a stated limit.
- **D4** · ventana 10–90 min. The engine moves the saturation, the rate and the pressure in response, and the right ventricle is where deterioration shows first.
  - Esperado: States a reassessment interval; checks the oxygenation and the haemodynamics.
  - Alternativas aceptables: Reassessing by POCUS rather than by the vitals.
- **D5** · ventana 20–180 min. Transport, the level of care and who performs the reperfusion are the continuity decisions, and they depend on the pressure.
  - Esperado: Decides transport and level of care on the observed haemodynamics; states what is pending and who is responsible.
  - Alternativas aceptables: Keeping the patient monitored with a stated threshold to escalate.

**Información accesible:** Arrival observables and the monitor; the patient's history; POCUS, CT pulmonary angiogram, D-dimer, blood gases, troponin, radiograph; the examination of the legs, which the case authors.

**Criterio de cierre:** A disposition is decided, or the encounter reaches its horizon.

**Límites reales del motor:**
- The engine records a reperfusion referral, not its result.
- The CT angiogram takes twenty minutes of simulated time and the encounter may close first.

**Eventos críticos:**

- `pe_no_anticoagulation` — **Omisión crítica.** No anticoagulation is given or stated as withheld in a recognised embolism.
  - Se activa cuando: Objective or clinical evidence of embolism is recorded and no anticoagulation is executed in the window, with no contraindication stated.
  - Información que debía estar disponible: The POCUS, angiogram or D-dimer where requested; the presenting history.
  - Ventana y oportunidad: 0–60 min.
  - Alternativas aceptables: Anticoagulation of any modelled agent and route; withholding it with a stated bleeding contraindication; proceeding directly to reperfusion with a stated reason.
  - Evidencia necesaria: The absence of an executed anticoagulation action in the window.
  - Exclusiones: The encounter closed before the confirming study was reported.
  - Dominios sobre los que pesa: D3.

