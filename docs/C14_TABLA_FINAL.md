# C14 · Tabla final derivada (ciclo 5, completada en el ciclo 7)

Autorización docente del 2026-09-28 (§17–§19, §22).

- **Qué es.** Lo que el banco declara hoy para C14 («usar el POCUS para guiar
  el manejo»), caso por caso. La generó `c14_review.final_table_markdown()`
  desde `case_assessment_bank.C14_DECLARATIONS`.
- **No se edita a mano.** `test_c14_opportunities.py` comprueba que este
  documento sea exactamente lo que el banco declara.
- **De dónde salen las filas:**
  - las decisiones A–H aprobadas (`docs/C14_DECISIONES_A_H.md`), derivadas por
    `c14_review.derive(APPROVED)`, y la decisión posterior DF-20 para
    `acs_54m_inferior` (`c14_review.final_states`);
  - las filas claras del borrador del ciclo 3
    (`docs/BORRADOR_C14_OBSERVATION_OPPORTUNITIES.md`), que el docente
    mantuvo.

**Totales:**

| Estado | Casos |
|---|---|
| YES | 14 |
| NO | 17 |
| NOT REVIEWED | 0 |

**Ciclo 7 (2026-09-28).** `acs_54m_inferior` pasó de NOT REVIEWED a NO: DF-20 no
cambió sus datos ni su fisiología, y el docente confirmó el NO con una razón
sobre la **oportunidad de observación**, no sobre lo que el POCUS puede mostrar
técnicamente (`c14_review.LATER`, revisión `C14-REVIEW-2`). Los 31 casos del
banco quedan revisados para C14.

**Lo que las filas no dicen:**

- **Una oportunidad no es una observación.** YES sólo hace evaluable C14 en un
  encuentro nuevo; la evidencia la produce el residente y la observación la
  confirma el docente.
- **NO significa no evaluable**, nunca una falla ni un cero.
- **La evidencia esperada orienta; no es una lista cerrada.**
- **Cada fila vale desde el encuentro siguiente.** Los encuentros anteriores
  conservan la base congelada con que empezaron.
- **Procedencia.** Cada fila del banco lleva `reviewed`: `by`, `on`, `source`,
  `decision_group` y `version`.
  - `decision_group` es la decisión que resolvió la fila, o `clear`.
  - Las neumonías resuelven por C y la pielonefritis 58f por C; su
    fundamentación cita también F y H.
- **Las filas están en inglés**, como el resto del banco. No hay versión en
  español aprobada.

| CASE ID | OPPORTUNITY | RATIONALE (YES) / REASON (NO) | OBSERVABLE COMPONENT | EXPECTED TRACE EVIDENCE | REVIEW SOURCE |
|---|---|---|---|---|---|
| `acs_54m_inferior` | NO | The encounter does not create a meaningful opportunity to observe POCUS-guided management: recognising right ventricular involvement through the available POCUS is not an expectation the ACEP 2016 emergency ultrasound guideline used here establishes (pp. 25, 29), and the nitrate, antiplatelet and cautious-volume decisions are driven mainly by the ECG, the right-sided leads (V4R) and the haemodynamic context rather than by the POCUS finding. | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; decision DF-20; C14-REVIEW-2 |
| `acs_66f_nonst` | NO | The acute coronary syndrome is already established by the ECG and a troponin of 180 ng/L; the mild inferolateral hypokinesis does not change the pathway, with no occlusion and an angiography that can wait (decision A). | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; decision A; C14-REVIEW-1 |
| `acs_61m_posterior` | YES | ST depression in V1-V3 with posterior hypokinesis on POCUS: the regional wall motion can prioritise reperfusion for an occlusion the 12-lead understates (decision A); in the engine the wall motion evolves with the ischaemic minutes. | Using regional wall motion to prioritise the reperfusion decision. | requests POCUS and names the posterior hypokinesis; uses it with the ECG and the posterior leads to treat the pattern as an occlusion; activates or expedites reperfusion | human_clinical_review; Nicolás Pineda, 2026-09-28; decision A; C14-REVIEW-1 |
| `acs_52m_de_winter` | YES | Akinesis of the anterior wall and apex supports treating the de Winter pattern as an anterior occlusion (decision A); in the engine the wall motion evolves with the ischaemic minutes. | Using regional wall motion to prioritise the reperfusion decision. | requests POCUS and names the anterior akinesis; relates it to the ECG pattern as an occlusion; activates or expedites reperfusion | human_clinical_review; Nicolás Pineda, 2026-09-28; decision A; C14-REVIEW-1 |
| `acs_48m_wellens` | NO | The right decision -- angiography and no provocation test -- does not depend on POCUS, and a normal resting POCUS cannot reasonably guide it. Not being reassured by it is diagnostic reasoning, not C14 (decision B). | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; decision B; C14-REVIEW-1 |
| `acs_70f_left_main` | YES | Borderline pressure with globally reduced contraction on POCUS: the global LV function, a state the EPA lists, is what should limit volume and prompt early support while reperfusion is arranged; the engine answers volume poorly in this profile. | Deciding volume, support and urgency from the global LV function. | requests POCUS and names the globally reduced contraction; limits or withholds volume, or escalates support, because of it; relates it to the urgency of reperfusion | human_clinical_review; Nicolás Pineda, 2026-09-28; clear row; C14-REVIEW-1 |
| `anaphylaxis_29f` | NO | Adrenaline and volume are indicated whatever the POCUS shows; the hyperdynamic LV and the collapsing IVC confirm a distributive shock without changing its management (decision C). | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; decision C; C14-REVIEW-1 |
| `anaphylaxis_63m_betablocked` | NO | In this refractory reaction the case's lever is the medication history and glucagon; volume is given regardless, and the POCUS supports without guiding the decision (decision C). | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; decision C; C14-REVIEW-1 |
| `asthma_24f` | NO | Bronchodilation does not depend on POCUS. A pneumothorax appears only after ventilation with sustained high plateau pressures, and its event already names the diagnosis, so a POCUS would only confirm it (decision D). Redesigning that event is a separate case decision. | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; decision D; C14-REVIEW-1 |
| `asthma_49m` | NO | Bronchodilation does not depend on POCUS. A pneumothorax appears only after ventilation with sustained high plateau pressures, and its event already names the diagnosis, so a POCUS would only confirm it (decision D). Redesigning that event is a separate case decision. | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; decision D; C14-REVIEW-1 |
| `bradycardia_ccb_68m` | NO | The POCUS is the same in the three toxic or metabolic bradycardias -- globally reduced contraction at a slow rate -- so it does not discriminate the cause, which the case separates by the history, the glucose and the ECG, and the modelled responses do not depend on it (decision E). | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; decision E; C14-REVIEW-1 |
| `bradycardia_avb3_78f` | NO | The decision is pacing, and the pulse and the pressure confirm its capture; the simulator's POCUS does not reflect the capture and would contradict the monitor after pacing (decision E). | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; decision E; C14-REVIEW-1 |
| `bradycardia_bb_54f` | NO | The POCUS is the same in the three toxic or metabolic bradycardias -- globally reduced contraction at a slow rate -- so it does not discriminate the cause, which the case separates by the history, the glucose and the ECG, and the modelled responses do not depend on it (decision E). | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; decision E; C14-REVIEW-1 |
| `bradycardia_hyperk_63m` | NO | Hyperkalaemia is treated with calcium, insulin with glucose and removal; the POCUS does not change that management. | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; clear row; C14-REVIEW-1 |
| `gi_bleed_57m` | YES | Haemorrhagic shock (88/54) with a small hyperdynamic LV and a near-completely collapsing IVC: the volume assessment is a target of the resuscitation alongside transfusion, and a repeat scan shows the IVC filling with volume and blood (decision C). | Using the POCUS volume assessment to guide and reassess resuscitation. | requests POCUS and names the empty, hyperdynamic LV and the collapsed IVC; relates them to transfusion or volume; reassesses with POCUS after resuscitation | human_clinical_review; Nicolás Pineda, 2026-09-28; decision C; C14-REVIEW-1 |
| `gi_bleed_72f` | YES | Hypotension from bleeding (98/62) with a hyperdynamic LV and a 1.1 cm collapsing IVC: the volume assessment is a target of the resuscitation alongside transfusion, and a repeat scan shows the IVC filling with volume and blood (decision C). | Using the POCUS volume assessment to guide and reassess resuscitation. | requests POCUS and names the hyperdynamic LV and the collapsing IVC; relates them to transfusion or volume; reassesses with POCUS after resuscitation | human_clinical_review; Nicolás Pineda, 2026-09-28; decision C; C14-REVIEW-1 |
| `hypoglycemia_28m` | NO | The capillary glucose and the glucose treat it; the POCUS adds nothing to the management. | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; clear row; C14-REVIEW-1 |
| `hypoglycemia_76f` | NO | The capillary glucose and the glucose treat it; the POCUS adds nothing to the management. | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; clear row; C14-REVIEW-1 |
| `hypoglycemia_54m_thiamine` | NO | The capillary glucose and the glucose treat it; the POCUS adds nothing to the management. The thiamine is decided by the history. | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; clear row; C14-REVIEW-1 |
| `opioid_35m` | NO | Opioid respiratory depression is treated with naloxone and ventilation; the POCUS adds nothing to the management. | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; clear row; C14-REVIEW-1 |
| `opioid_67f` | NO | Opioid respiratory depression is treated with naloxone and ventilation; the POCUS adds nothing to the management. | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; clear row; C14-REVIEW-1 |
| `pneumonia_46f` | YES | Septic hypotension (92/58) with a 1.0 cm collapsing IVC, a vigorous LV and no diffuse B-lines: POCUS can select and titrate the fluid strategy and time the vasopressor, and a repeat scan shows the IVC filling with volume (decision C). The consolidation may be named but does not by itself make the opportunity (decision F): one opportunity for the case. | Guiding and reassessing the fluid and haemodynamic strategy with POCUS. | requests POCUS and names the volume findings (the IVC and the LV); gives, limits or titrates volume, or moves to a vasopressor, because of them; reassesses with POCUS after volume | human_clinical_review; Nicolás Pineda, 2026-09-28; decision C; C14-REVIEW-1 |
| `pneumonia_83m` | YES | An older patient referred as dehydrated, 96/60 with a 1.2 cm collapsing IVC and a preserved LV: POCUS can select and titrate the fluid strategy and time the vasopressor, and a repeat scan shows the IVC filling with volume (decision C). The consolidation may be named but does not by itself make the opportunity (decision F): one opportunity for the case. | Guiding and reassessing the fluid and haemodynamic strategy with POCUS. | requests POCUS and names the volume findings (the IVC and the LV); gives, limits or titrates volume, or moves to a vasopressor, because of them; reassesses with POCUS after volume | human_clinical_review; Nicolás Pineda, 2026-09-28; decision C; C14-REVIEW-1 |
| `pulmonary_edema_58m` | YES | Diffuse B-lines, a moderately depressed LV and a plethoric IVC separate congestion from the other causes of this presentation; loading volume is a critical event of the case. | Deciding nitrate, diuretic or NIV, and withholding volume, from the B-lines, the LV and the IVC. | requests POCUS and names the diffuse B-lines and the depressed LV; withholds volume because of them; gives nitrate, diuretic or NIV because of them | human_clinical_review; Nicolás Pineda, 2026-09-28; clear row; C14-REVIEW-1 |
| `pulmonary_edema_75f` | YES | Diffuse B-lines, a severely depressed LV, a plethoric IVC and small effusions separate congestion from the other causes of this presentation; loading volume is a critical event of the case. | Deciding nitrate, diuretic or NIV, and withholding volume, from the B-lines, the LV and the IVC. | requests POCUS and names the diffuse B-lines and the depressed LV; withholds volume because of them; gives nitrate, diuretic or NIV because of them | human_clinical_review; Nicolás Pineda, 2026-09-28; clear row; C14-REVIEW-1 |
| `pulmonary_embolism_33f` | YES | Stable (110/70) with SpO2 90 %: a mildly enlarged RV without septal flattening and a non-compressible popliteal vein. The proximal DVT confirms thromboembolic disease before the CT angiogram (20 minutes) returns, and an RV without shock argues against thrombolysis, a dangerous action in this case (decision G). | Integrating the RV and a proximal DVT with the haemodynamic stability: anticoagulation before confirmation, and no thrombolysis. | requests POCUS and names the proximal DVT or the RV; anticoagulates, or states it as pending the angiogram, because of it; withholds thrombolysis with the stable haemodynamics and the RV stated | human_clinical_review; Nicolás Pineda, 2026-09-28; decision G; C14-REVIEW-1 |
| `pulmonary_embolism_61m` | YES | Obstructive shock (86/54, SpO2 88 %): an RV larger than the LV with a D-sign and McConnell's sign, and a non-compressible popliteal vein, justify treating a high-risk embolism and deciding reperfusion before the CT angiogram (decision G). | Deciding reperfusion and anticoagulation from RV strain and a proximal DVT in shock. | requests POCUS and names the dilated RV with a D-sign or McConnell's sign, or the DVT; anticoagulates and decides reperfusion because of it; acts without waiting for the angiogram | human_clinical_review; Nicolás Pineda, 2026-09-28; decision G; C14-REVIEW-1 |
| `renal_colic_34m` | NO | The renal ultrasound, the study that settles this disposition, is a formal study in the simulator and not POCUS; the POCUS proper does not change the management of a colic without shock (decision H). | — | — | human_clinical_review; Nicolás Pineda, 2026-09-28; decision H; C14-REVIEW-1 |
| `obstructive_pyelonephritis_58f` | YES | Septic shock from an infected obstruction (94/54) with a 1.0 cm collapsing IVC and a vigorous LV: POCUS can select and limit the fluid strategy and time the vasopressor (decision C). The renal ultrasound is a formal study in the simulator and does not count by itself (decision H). A repeat scan still shows the arrival IVC: the simulator does not model its response here. | Guiding the fluid and haemodynamic strategy with POCUS in septic shock. | requests POCUS and names the volume findings (the IVC and the LV); gives, limits or titrates volume, or moves to a vasopressor, because of them | human_clinical_review; Nicolás Pineda, 2026-09-28; decision C; C14-REVIEW-1 |
| `trauma_limb_hemorrhage_27m` | YES | Shock (96/54, HR 132) after a machinery injury to the thigh: a negative five-window E-FAST excludes a cavity source and keeps the control on the compressible limb. Free fluid, haemothorax, pneumothorax and the pericardium are states the EPA lists. | Directing haemorrhage control with the absence of cavity bleeding on the E-FAST. | requests the E-FAST and names it negative; keeps haemorrhage control on the limb rather than searching a cavity; states what would change that | human_clinical_review; Nicolás Pineda, 2026-09-28; clear row; C14-REVIEW-1 |
| `trauma_hemothorax_41m` | YES | The E-FAST shows an echogenic left pleural collection in shock: a haemothorax, a state the EPA lists, that defines the drain; the case's critical events are the undrained haemothorax and the drained one never looked at again. | Deciding the drain and its reassessment from the haemothorax on the E-FAST. | requests the E-FAST and names the left haemothorax; places a chest tube because of it; reassesses after the drain with the E-FAST, a film or surgery | human_clinical_review; Nicolás Pineda, 2026-09-28; clear row; C14-REVIEW-1 |
