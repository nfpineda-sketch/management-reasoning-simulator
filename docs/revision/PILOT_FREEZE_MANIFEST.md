# Manifiesto de congelamiento del piloto (Fase 0, 0K)

Generado por `tools_pilot_freeze.py` a partir de `pilot_freeze.py` (decisiones y limitaciones) y de
`pilot_acceptance.py` (batería). No se edita a mano: `test_phase0_pilot_freeze.py` falla si se aparta
del código. El informe de la fase es `docs/revision/PHASE_0_PILOT_SAFETY_REPORT.md`.

- **Identificador:** `pilot-freeze-phase0-2026-10-06`.
- **Regla de despliegue:** el piloto corre sobre el commit que fija `MRS_CODE_VERSION`; cada encuentro
  registra el código con que empezó (`assignment.code_version`) y cada turno el código con que corrió
  (`versions.code_version` del Trace). Un despliegue durante el piloto queda visible en el registro; la
  regla es no desplegar mientras haya encuentros abiertos.

## Versiones

| Componente | Versión |
|---|---|
| freeze_id | pilot-freeze-phase0-2026-10-06 |
| engine | family engine v1, execution 0.24.2 |
| case_bank | 1.0.0 |
| case_generator | 0.17.0 |
| runtime | 0.24.13 |
| payload | mrs_attempt_v1 |
| reader | frozen at V3 (validation/BASELINES.md, 3d942ee); not modified by Phase 0 |
| trace_schema | management_trace_v1 + phase0_trace_v1 |
| ledger_schema | order_ledger_v1 |
| event_provenance_schema | event_provenance_v1 |

## Indicadores del entorno

| Indicador | Valor exigido |
|---|---|
| `.streamlit/config.toml [runner] fastReruns` | false (Phase 0, 0D: a second click never starts a concurrent run) |
| `MRS_OFFLINE_CASES` | 1 (bank cases; no provider call during the encounter) |
| `MRS_PAID_GENERATION` | off |
| `MRS_FREE_GENERATION` | unset (free generation stays in the administrator's sandbox) |
| `MRS_DEFAULT_VARIANT` | unset (a pinned variant would bypass the case selection) |
| `MRS_REPLAY_CASE` | unset (a replayed case is outside the accepted list) |
| `MRS_CODE_VERSION` | the deployed commit (every encounter and every turn records it) |
| `MRS_IMAGE_REQUIRE_REVIEW` | on |

## Rutas heredadas excluidas

Los desafíos `R1-03`, `R1-04`, `R2-01` corren sobre el motor heredado PS001 y no se asignan automáticamente a residentes (0C). Siguen en
el catálogo, el sandbox docente y las pruebas; una directiva docente no puede alcanzarlos.

## Desafíos permitidos

Lo que la asignación automática puede dar a cada año (`curriculum.assignable_challenges`) y cuántos
casos aceptados puede sortear cada desafío.

| Año | Desafíos |
|---|---|
| R1 | R1-05, R1-06, R1-07 |
| R2 | R1-05, R1-06, R2-02, R2-03, R1-07, R2-04, R2-05 |
| R3 | R1-05, R1-06, R2-02, R2-03, R1-07, R2-04, R2-05, R3-01 |

| Desafío | Casos aceptados que puede sortear |
|---|---|
| R1-05 | 4 |
| R1-06 | 7 |
| R2-02 | 8 |
| R2-03 | 4 |
| R1-07 | 9 |
| R2-04 | 13 |
| R2-05 | 7 |
| R3-01 | 6 |

## Casos: batería y decisión

La columna de limitaciones nombra las que halló la batería en cada caso y cuenta las que el caso ya
declaraba (`engine_limits` de `case_assessment_bank`, cierre prepiloto C-2026-10-02-08: congeladas con
cada encuentro y mostradas al docente con «Never count these against the resident»; no se repiten
aquí). Las de todo el banco (abajo) valen para los 31; tres tocan decisiones evaluadas
(G-RESUSCITATION, G-LATER-ORDERS, G-READER-V3) y cada una tiene su guarda.

| Caso | Familia | Desafíos | Motor | Batería | Limitaciones declaradas | ¿Afecta una decisión evaluada? | Decisión |
|---|---|---|---|---|---|---|---|
| `acs_48m_wellens` | acs | R1-07, R2-02, R2-04 | family engine (bank case) | PASS | — + 2 del caso | no | **ACCEPT** |
| `acs_52m_de_winter` | acs | R1-07, R2-02, R2-04 | family engine (bank case) | PASS | C-SCRIPTED-VF + 2 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `acs_54m_inferior` | acs | R1-07, R2-02, R2-04 | family engine (bank case) | PASS | C-SCRIPTED-AV-BLOCK, C-SCRIPTED-VF + 2 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `acs_61m_posterior` | acs | R1-07, R2-02, R2-04 | family engine (bank case) | PASS | C-SCRIPTED-VF + 2 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `acs_66f_nonst` | acs | R1-07, R2-02, R2-04 | family engine (bank case) | PASS | — + 2 del caso | no | **ACCEPT** |
| `acs_70f_left_main` | acs | R1-07, R2-02, R2-04 | family engine (bank case) | PASS | C-SCRIPTED-VF + 3 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `anaphylaxis_29f` | anaphylaxis | R1-06, R3-01 | family engine (bank case) | PASS | C-BIPHASIC, G-HARM-NOT-MODELLED + 2 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `anaphylaxis_63m_betablocked` | anaphylaxis | R1-06, R3-01 | family engine (bank case) | PASS | C-GLUCAGON-INFUSION + 2 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `asthma_24f` | asthma | R3-01 | family engine (bank case) | PASS | G-HARM-NOT-MODELLED + 2 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `asthma_49m` | asthma | R3-01 | family engine (bank case) | PASS | G-HARM-NOT-MODELLED + 2 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `bradycardia_avb3_78f` | bradycardia | R2-04 | family engine (bank case) | PASS | C-INFRANODAL-BLOCK + 2 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `bradycardia_bb_54f` | bradycardia | R2-04 | family engine (bank case) | PASS | C-BRADYCARDIA-DEFINITIVE + 2 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `bradycardia_ccb_68m` | bradycardia | R2-04 | family engine (bank case) | PASS | C-BRADYCARDIA-DEFINITIVE + 2 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `bradycardia_hyperk_63m` | bradycardia | R2-04 | family engine (bank case) | PASS | C-BRADYCARDIA-DEFINITIVE + 2 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `gi_bleed_57m` | gi_bleed | R2-05 | family engine (bank case) | PASS | G-HARM-NOT-MODELLED + 2 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `gi_bleed_72f` | gi_bleed | R2-05 | family engine (bank case) | PASS | G-HARM-NOT-MODELLED + 2 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `hypoglycemia_28m` | hypoglycemia | R1-06, R1-07 | family engine (bank case) | PASS | — + 2 del caso | no | **ACCEPT** |
| `hypoglycemia_54m_thiamine` | hypoglycemia | R1-06, R1-07 | family engine (bank case) | PASS | — + 2 del caso | no | **ACCEPT** |
| `hypoglycemia_76f` | hypoglycemia | R1-06, R1-07 | family engine (bank case) | PASS | — + 2 del caso | no | **ACCEPT** |
| `obstructive_pyelonephritis_58f` | renal_colic | R2-05 | family engine (bank case) | PASS | C-SOURCE-CONTROL + 2 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `opioid_35m` | opioid | R1-06 | family engine (bank case) | PASS | — + 2 del caso | no | **ACCEPT** |
| `opioid_67f` | opioid | R1-06 | family engine (bank case) | PASS | — + 2 del caso | no | **ACCEPT** |
| `pneumonia_46f` | pneumonia | R1-05, R2-03, R2-05 | family engine (bank case) | PASS | G-HARM-NOT-MODELLED + 3 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `pneumonia_83m` | pneumonia | R1-05, R2-03, R2-05 | family engine (bank case) | PASS | G-HARM-NOT-MODELLED + 3 del caso | no | **ACCEPT WITH DECLARED LIMITATION** |
| `pulmonary_edema_58m` | pulmonary_edema | R1-05, R3-01 | family engine (bank case) | PASS | — + 2 del caso | no | **ACCEPT** |
| `pulmonary_edema_75f` | pulmonary_edema | R1-05, R3-01 | family engine (bank case) | PASS | — + 2 del caso | no | **ACCEPT** |
| `pulmonary_embolism_33f` | pulmonary_embolism | R2-02, R2-03, R2-04 | family engine (bank case) | PASS | — + 3 del caso | no | **ACCEPT** |
| `pulmonary_embolism_61m` | pulmonary_embolism | R2-02, R2-03, R2-04 | family engine (bank case) | PASS | — + 2 del caso | no | **ACCEPT** |
| `renal_colic_34m` | renal_colic | R2-05 | family engine (bank case) | PASS | — + 2 del caso | no | **ACCEPT** |
| `trauma_hemothorax_41m` | trauma | R2-04, R2-05 | family engine (bank case) | FAIL: A_correct_management, recovery | C-NO-THEATRE + 3 del caso | sí (con guarda) | **EXCLUDE** |
| `trauma_limb_hemorrhage_27m` | trauma | R2-04, R2-05 | family engine (bank case) | PASS | C-LIMB-ARREST-13 + 3 del caso | sí (con guarda) | **ACCEPT WITH DECLARED LIMITATION** |

**Aceptados:** 30 de 31 (12 ACCEPT, 18 ACCEPT WITH DECLARED LIMITATION). **Excluidos:** 1.

### Excluido: `trauma_hemothorax_41m`

An assessed management decision depends on a course the engine cannot run: the theatre is not modelled and, since Phase 0 made the arrest a true one, the patient arrests at about minute 60 whatever is done, so trauma_drained_and_never_looked_again (window 10-180) is never assessable. This departs from the pre-pilot closure (C-2026-10-02-08: no case excluded, the theatre declared as a limit while the arrest was only announced): the faculty decides between keeping it excluded, accepting it with the arrest declared, or representing the theatre.

## Versiones de los casos aceptados

Huella del texto del caso (`clinical_cases`) y de su declaración de evaluación: la segunda es la que
`evaluation_basis` congela con cada encuentro al iniciar (sus 12 primeros caracteres), para comparar un
encuentro con este congelamiento. Un cambio posterior en cualquiera de las dos cambia este manifiesto.

| Caso | Huella del caso | Huella de la declaración |
|---|---|---|
| `acs_48m_wellens` | `c200d69ddcf4` | `de8fb337d4ce` |
| `acs_52m_de_winter` | `666f8f024a1e` | `59d8741036be` |
| `acs_54m_inferior` | `7fd98b3d0de2` | `3a274930c5da` |
| `acs_61m_posterior` | `7daabc433733` | `4a514d2befb7` |
| `acs_66f_nonst` | `7ad5860ac6ba` | `f3777a7f984f` |
| `acs_70f_left_main` | `3d729ab76383` | `d60a2009c1da` |
| `anaphylaxis_29f` | `0af47141060f` | `e16654d92066` |
| `anaphylaxis_63m_betablocked` | `3a7880581c9a` | `1eab33356555` |
| `asthma_24f` | `3466d44e44f5` | `bdf2e56fb032` |
| `asthma_49m` | `3c822d8f1e90` | `b9cdfcce91be` |
| `bradycardia_avb3_78f` | `661b1a6db9b0` | `7d4050195a7d` |
| `bradycardia_bb_54f` | `6536441acd60` | `95d6eb21544e` |
| `bradycardia_ccb_68m` | `0cf52bb12175` | `ab40d347c98b` |
| `bradycardia_hyperk_63m` | `d33d62d37ccc` | `33014d897319` |
| `gi_bleed_57m` | `d1be19de8844` | `b681ed9a9b81` |
| `gi_bleed_72f` | `29421f79fcee` | `872afcdacbd2` |
| `hypoglycemia_28m` | `29fd80327d69` | `2528cb8d734b` |
| `hypoglycemia_54m_thiamine` | `9e6a3731de48` | `f9824f2e1ab6` |
| `hypoglycemia_76f` | `74a90e446890` | `71692ce62095` |
| `obstructive_pyelonephritis_58f` | `192a683e71c1` | `ecbf02bda191` |
| `opioid_35m` | `efb185b9c2a8` | `66fce23151d9` |
| `opioid_67f` | `1167fd812921` | `11f2a6b080b0` |
| `pneumonia_46f` | `135adeecdf1b` | `70950e5cbff2` |
| `pneumonia_83m` | `132ad9dce3ea` | `3011288786d8` |
| `pulmonary_edema_58m` | `4d28a1464460` | `48086990c5c3` |
| `pulmonary_edema_75f` | `7dfe9ff2e453` | `8d6784edd2b0` |
| `pulmonary_embolism_33f` | `6dcc6507e16c` | `33a88862483f` |
| `pulmonary_embolism_61m` | `d627f5bf33aa` | `9646776af073` |
| `renal_colic_34m` | `98529c3c1a6e` | `7dac95073fa4` |
| `trauma_limb_hemorrhage_27m` | `3a165b3696b3` | `c8f4e5d37e15` |

## Limitaciones de todo el banco

- **G-RESUSCITATION** — Resuscitation is not modelled: a cardiac arrest is the end of what can be assessed. The page says so in the agreed words, later orders are TERMINAL_NOT_EXECUTABLE, and every decision whose window reaches past the arrest is NOT ASSESSABLE (rule E). *Guarda:* rule E (resuscitation_not_modelled).
- **G-LATER-ORDERS** — An order for a later time ('in 30 minutes') is recorded and neither run nor scheduled (RECORDED_NOT_MODELLED, unsupported_future_execution); the resident is told to write it again when it is due. *Guarda:* rule A (the kinds the plan names, or a wildcard).
- **G-STEP-120** — One step moves the clock at most 120 minutes; a longer wait is refused and explained (pilot_time_step_limit), never shortened. *Guarda:* the refusal is recorded with its fate.
- **G-READER-V3** — The order reader is frozen at V3. What it does not read is UNRECOGNIZED, with a receipt, and never disappears; it counts as a wildcard for every assessed omission in its window. *Guarda:* rule A (wildcard) and rule D (an order not carried out).
- **G-STATIC-OBSERVATIONS** — History, collateral and the examination regions and studies the engine does not model are the case's authored values, declared static (observation_consistency.declaration); a static result reported in a turn is a limitation of that turn (observable_static). *Guarda:* observable_static in the turn's limitations.
- **G-HARM-NOT-MODELLED** — Several excesses and errors have no modelled harm (audit 8 D/E): crystalloid beyond need where the family has no lung to load, furosemide in septic hypotension, midazolam in severe asthma, repeated IM adrenaline, D50 or aspirin, repeated nebulised albuterol. The order runs with its fate; the absence of a consequence is the engine's, not evidence. *Guarda:* no declared critical event reads these consequences.
- **G-INTERRUPTIONS** — A wait stops at a declared engine event, at a systolic below 70 that fell 20 or more for 2 minutes, or at a saturation below 85 that fell 5 or more for 2 minutes (event_provenance). *Guarda:* every event carries its cause class and preventability.

## Limitaciones por caso

- **C-SCRIPTED-AV-BLOCK** (`acs_54m_inferior`) — The complete AV block at minute 45 of the inferior infarct is scripted (SCRIPTED_NATURAL_HISTORY, NOT_PREVENTABLE_IN_SIMULATOR): it comes whatever is done. *Guarda:* rule D: a scripted event never counts against the resident.
- **C-SCRIPTED-VF** (`acs_54m_inferior`, `acs_61m_posterior`, `acs_52m_de_winter`, `acs_70f_left_main`) — Ventricular fibrillation is scripted at minute 120 of occlusion and prevented by reperfusion before it. Whether the reperfusion decision came in time is read from the decision, never from the scripted minute. *Guarda:* rule D: a scripted event never counts against the resident.
- **C-BIPHASIC** (`anaphylaxis_29f`) — The biphasic reaction is scripted 75 minutes after the first one settles (NOT_PREVENTABLE_IN_SIMULATOR) and stops a wait when it comes. *Guarda:* rule D.
- **C-GLUCAGON-INFUSION** (`anaphylaxis_63m_betablocked`) — A glucagon infusion is not read (UNRECOGNIZED). Glucagon boluses, repeated IM adrenaline and an adrenaline infusion are modelled and hold the patient. *Guarda:* rule A (wildcard) and rule D.
- **C-BRADYCARDIA-DEFINITIVE** (`bradycardia_ccb_68m`, `bradycardia_bb_54f`, `bradycardia_hyperk_63m`) — By design the definitive treatment is not run: high-dose insulin (calcium-channel blocker), a glucagon infusion (beta blocker), insulin and dialysis (potassium); dopamine, isoproterenol and vasopressin are not read. What is modelled as a bridge: repeated antidote boluses, an adrenaline infusion and transcutaneous pacing. Phase 0 reads the arrest from the rate the monitor shows, which an adrenaline infusion lifts as well. *Guarda:* rule A and rule D for an order the simulator did not carry out.
- **C-INFRANODAL-BLOCK** (`bradycardia_avb3_78f`) — Atropine does nothing for the infranodal block, by design; pacing and an adrenaline infusion are modelled. *Guarda:* none needed: the behaviour is the case's teaching point.
- **C-SOURCE-CONTROL** (`obstructive_pyelonephritis_58f`) — The urology consult (source control) is recorded and has no modelled physiological effect: after the first fluid the pressure drifts back. *Guarda:* pyelo_no_source_control reads the decision, not its effect.
- **C-LIMB-ARREST-13** (`trauma_limb_hemorrhage_27m`) — Untreated, the arterial limb bleed reaches the engine's arrest threshold at about minute 13; Phase 0 made that arrest a true one (it was announced while a pulse was shown). *Guarda:* rule E: trauma_crystalloid_instead_of_blood is not assessable past the arrest.
- **C-NO-THEATRE** (`trauma_hemothorax_41m`) — The definitive control of the haemothorax, an operating theatre, is not modelled. After the drain the patient bleeds to a true arrest at about minute 60 whatever is done (drain at minute 0, repeated transfusion, search for another source, surgery called). The assessed management after drainage (look again, decide theatre) and the case's own endpoint depend on that course. *Guarda:* provenance ENGINE_LIMITATION; the case is excluded.

## Cómo se hace cumplir

- **Selección de casos:** un caso excluido nunca se sortea para un residente (`cognitive_generator`) ni se ofrece para una directiva docente (`encounter_directives.case_options`);
  sólo un caso nombrado explícitamente (sandbox docente, pruebas) lo alcanza.
- **Análisis:** un evento del curso que el simulador decide en un caso nunca cuenta en contra del
  residente (`rubric_screening.may_support_negative_feedback`, regla D).
- **Batería:** `test_phase0_acceptance_battery.py` (motor, 19 categorías por caso) y
  `test_phase0_acceptance_page.py` (la página real, con recarga y reanudación) cubren los 31 casos.
