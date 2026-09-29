# Defectos conocidos de V3

Ciclo 9 · 2026-09-29 · §67 y §114 de la instrucción docente. El dato está en
`validation/known_defects_v3.json`; esta página lo resume.

**Qué es.** El estado de defectos conocidos del motor congelado como
**DEVELOPMENT PRE-VALIDATION BASELINE V3** (`3d942eedf1d5`): todo lo conocido y no
corregido al congelarlo, para leer después un error externo contra lo que ya se sabía.

**Qué no es.** No reescribe la lista del piloto
(`validation/pilot_v1/manifests/known_defects.json`, versión 2), que sigue
siendo la del SPANISH PILOT BASELINE y la del ENGLISH VALIDATION BASELINE. Una
etiqueta nunca saca un error de una métrica ni corrige un resultado hacia atrás.

**Cómo se etiqueta.** El adjudicador puede usar cualquier identificador de los
dos archivos. Un error de una corrida sobre `939978a` que corresponde a TD-39,
TD-34 o TD-36 se etiqueta con ese identificador: *known at time of analysis but
present in frozen baseline* (§67). La herramienta rechaza un identificador que
no esté en ninguno de los dos.

## Al congelar V3

- **CRITICAL sin resolver:** ninguno.
- **HIGH sin resolver:** KD-28 (TD-14), registrado HIGH desde el ciclo 5 por su
  amplitud: es fricción, el lector retiene con una pregunta y no ejecuta nada.
  Las ejecuciones falsas que se conocen son MEDIUM (KD-29: una condición con
  «we», partida por «and» o sobre «SatO2» corre ahora).

## Corregido en V3 y presente en los baselines congelados

| ID | Severidad | Clase | Presente en | Corrección |
|---|---|---|---|---|
| TD-39 | HIGH | A discharge for later (its own time, after an observation or a result, on a condition) ran now | SPANISH PILOT BASELINE, ENGLISH VALIDATION BASELINE, DEVELOPMENT HARDENED BASELINE V1, DEVELOPMENT HARDENED BASELINE V2 | C-2026-09-29-01, C-2026-09-29-07 |
| TD-34 | HIGH | A reassessment in abbreviated hours ran at 0 minutes | SPANISH PILOT BASELINE, ENGLISH VALIDATION BASELINE, DEVELOPMENT HARDENED BASELINE V1, DEVELOPMENT HARDENED BASELINE V2 | C-2026-09-29-02, C-2026-09-29-07 |
| TD-36 | HIGH | A treatment received before the resident's care, told as such, was given again or asked about as the resident's order | SPANISH PILOT BASELINE, ENGLISH VALIDATION BASELINE, DEVELOPMENT HARDENED BASELINE V1, DEVELOPMENT HARDENED BASELINE V2 | C-2026-09-29-03, C-2026-09-29-07 |
| TD-33 | HIGH | Trauma: after a loss replaced with crystalloid, blood set off the transfusion overload rule | DEVELOPMENT HARDENED BASELINE V2 | C-2026-09-29-04 |

## La lista del piloto, en V3

| ID | En V3 | Nota |
|---|---|---|
| KD-01 | corregido | ENGLISH VALIDATION BASELINE (cycle 5) |
| KD-02 | presente | Verified in cycle 9: 'Morfina ev y paracetamol 1 g' drops the morphine. Its vocabulary class is TD-35 (KD-26). |
| KD-03 | presente | Not re-verified in cycle 9; no correction recorded. |
| KD-04 | presente | Verified in cycle 9. |
| KD-05 | corregido | cycle 8, C-2026-09-28-23 (after V2); a clearance for later is a disposition plan since cycle 9 (C-2026-09-29-01) |
| KD-06 | corregido | cycle 6, C-2026-09-28-04 (class C05) |
| KD-07 | presente | Verified in cycle 9. |
| KD-08 | presente | Not re-verified in cycle 9; no correction recorded. |
| KD-09 | presente | Verified in cycle 9: the repeat keeps its count, not 'as needed'. |
| KD-10 | presente | Verified in cycle 9. |
| KD-11 | presente | Not re-verified in cycle 9; no correction recorded. |
| KD-12 | presente | Not re-verified in cycle 9; no correction recorded. |
| KD-13 | presente | Not re-verified in cycle 9; no correction recorded. |
| KD-14 | presente | Not re-verified in cycle 9; no correction recorded. |
| KD-15 | presente | Verified in cycle 9. |

## Conocidos y no corregidos al congelar V3

Todos son anteriores al ciclo 9 salvo KD-31, que el ciclo halló al revisar el
tamizaje.

| ID | Severidad | Clase | Ejemplo | Qué pasa |
|---|---|---|---|---|
| KD-16 | MEDIUM | 'd/c' and 'dc' are not read as a discharge | d/c home · Dc home w/ EpiPen x2 · D/C home 4 hrs post epi if no rebound | Nothing is read (the generic notice), or the line is kept as a home prescription and the discharge is lost without a word; with a time or a condition it is a plain conditional, not a disposition plan. 'd/c NS' still stops the fluid. |
| KD-17 | MEDIUM | A discharge written as an intention, a possibility or in the past is neither run nor recorded | Plan to discharge home in 2 hours · Planeo alta mañana · Will discharge home tomorrow · Posible alta en unas horas · Discharged home w/ EpiPen · Dada de alta a domicilio · Después de 3 NBZ de salbutamol, PEF 80%: alta · Tras adrenalina IM, PA 120/80 y sin estridor: alta con EpiPen | Nothing is recorded; the generic notice asks for an order ('Discharged home w/ EpiPen' keeps only the EpiPen prescription). 'Vamos a dar de alta en 2 horas' is a disposition plan. A bare 'alta' after a colon is not read either. |
| KD-18 | MEDIUM | An observation or a control written without 'dejar en' is not read | Observe 6 h · Observar 4 horas · Control en 1 hora · Control en 30 min · Discharge home, recheck in ED in 24 h · PCP follow-up tomorrow at 0900 · allergy clinic in 4 weeks | Nothing runs; the generic notice (or, for a recheck, a question about an unrecognised study). 'Dejar en observación 6 horas' is the ED observation of D4. Some follow-ups written after the discharge are dropped from the record. |
| KD-19 | MEDIUM | After a reassessment, what follows in the same sentence is absorbed | Reassess in 30 min, 2 L NS · Reassess in 30 min, discharge if improved | The verbless fluid after the reassessment is lost without a word; a reassessment followed by a conditional discharge becomes one conditional plan and the reassessment does not run. |
| KD-20 | MEDIUM | Interval forms outside hours and minutes | Reevaluar en 20' · Reassess in 90' · Reevaluar a las 14 h · reevaluar a la hora · Reevaluar en hora y media · Reassess in 1 h, then every 30 min | Minutes written with an apostrophe run at 0 without a word; a clock time after 'a las' is read as an interval in hours (840 minutes), which the engine asks about (0–120); 'a la hora' is asked. 'Hora y media' without 'una', and a first interval followed by a repeat interval, are asked. |
| KD-21 | MEDIUM | Repeating or continuing a treatment given before the resident's care | Repeat the epinephrine given by EMS · Ya recibió adrenalina, repetir adrenalina 0,5 mg IM · Continue NS started by EMS at 125 mL/h · Salbutamol nebulizado hace 20 minutos en el SAPU, repetir · Otra dosis de adrenalina 0,5 mg IM, ya recibió una en su centro de salud hace 15 minutos | The repeat is held with a question ('No matching administered treatment' or 'Specify which recorded drug or fluid to repeat'), even with drug, dose and route written and after the prior dose is recorded; the continuation is read as a bolus that asks its volume. Visible, but it delays epinephrine. A trailing 'repetir' after the recorded history is lost without a word. |
| KD-22 | MEDIUM | The second treatment of a prehospital account | EMS gave epi 0.5 IM and diphenhydramine 50 mg IV · El SAMU le puso adrenalina 0,5 IM y metilprednisolona 125 mg IV · Prehospital: epi 0.3 IM + benadryl 25 IV · Recibió AAS 250 mg y nitroglicerina sublingual en el SAMU | The first treatment is recorded as prior treatment. A modelled second one is not given but is held with a question instead of recorded; a not-modelled one is recorded as the resident's decision (a Trace distortion); after a header and '+', it is dropped. A second prehospital dose of the same drug is not recorded; a prehospital nitroglycerin is not recorded (relevant beside the right ventricle of acs_54m_inferior) or is asked about as the resident's order. |
| KD-23 | LOW | Prior-treatment wording outside the recogniser | s/p epi 0.3 IM by EMS · Epi IM x1 PTA · El 112 le puso adrenalina y Urbason · Recibio adrenalina IM por el 061 · Trae vía periférica canalizada por SAMU · Methylpred 125 mg given at OSH · Took 4 baby aspirin at home before calling 911 · Tres nebulizaciones con salbutamol en el consultorio antes del traslado · No response to the epinephrine given at urgent care · Adrenalina IM puesta por un amigo en el restaurante | Nothing is given and nothing is recorded (the generic notice), or an unknown word is asked about. History without a recognised place, participle or 'hace' is missed; some is read as a new order and stopped by a dose question; a friend's EpiPen is recorded as a home prescription. |
| KD-24 | MEDIUM | One unrecognised fragment holds every order written with it | Epi 0.5 mg IM now, already drawn up · Epi 0.5 mg IM, EMS report reviewed · Epi 0.5 mg IM now, symptoms began 30 min before arrival · Segunda dosis de adrenalina 0,5 mg IM; la primera se la pusieron en el SAPU · Epinephrine 0.5 mg IM, same dose as given at urgent care · AAS 300 mg VO. En casa tomó 100 mg hace 2 horas. · Methylprednisolone 125 mg IV; she took prednisone 40 mg at home this morning | The engine asks about the fragment and holds the other orders of the submission, epinephrine included, until it is answered. A history clause the reader cannot classify, written with the order, holds epinephrine, aspirin or the steroid behind a question. |
| KD-25 | LOW | A submission that only brings a plan or history adds the generic notice (TD-38) | Alta en 2 horas · Epinephrine 0.5 mg IM given by EMS | The room says what was recorded and why, and then adds 'Please specify a question, investigation, treatment, or reassessment.' |
| KD-26 | MEDIUM | Abbreviated tests and trade names in a verbless list are lost (TD-35) | CBC coags lactate now · hemograma, TP/TTPA, BUN/crea · protonix 80 IV | The rest of the list runs; what the reader does not know is lost without a word. |
| KD-27 | MEDIUM | A discharge prescription written as a list (TD-37) | Discharge prescription: prednisone 40 mg daily x 5 days, cetirizine 10 mg daily | The discharge runs; the prednisone is lost and the cetirizine is recorded as a not-modelled drug, not as a prescription. |
| KD-28 | HIGH | Vocabulary and forms outside the reader, mostly held with a question (TD-14) | amp of D50 · epi drip · Narcan · Page GI · STEMI code · floor/pabellón · D5W · glucosalino · run/hang/push · coags · protonix · q15min · titulando a PAM > 65 | Mostly held with a question (63 of 108 and 19 of 32 in the blind sets of cycle 6): honest, visible, but it costs turns. What of it is lost without a word is KD-26. |
| KD-29 | MEDIUM | Residues of the cycle 8 classes (TD-40) | EDA urgente para ligadura de várices · IC urgente a cirugía ya · Cuando la SatO2 baje de 92%, iniciar O2 por naricera · Once she has had 30 mL/kg and MAP remains < 65, start norepinephrine · OK to send home · Alta ok · Return to OR if rebleeds | Some orders are lost without a word; a condition with 'we', split by 'and', or on 'SatO2' runs now (the oxygen of the blind set 2, its only false execution); some discharge wordings are not read. |
| KD-30 | LOW | A home instruction after the discharge is read as an order now | Discharge home, start prednisone tomorrow · Adrenalina autoinyectable para casa | The discharge is held by a question about the steroid's dose; an auto-injector 'para casa' without a discharge is read as an epinephrine infusion that asks its rate. Nothing runs by itself. |
| KD-31 | MEDIUM | The critical-event screening does not cite a recorded prior treatment | Aspirin 300 mg given by EMS (ACS) · Epinephrine 0.5 mg IM given at OSH (anaphylaxis) | The prior treatment is recorded as history and never given, but the screening's facts for 'no antiplatelet' or 'no epinephrine' do not mention it: the omission is still proposed (for aspirin as a reading) and the faculty member sees the history only in the Trace. No event is ever accepted automatically. |

## Conducta por diseño registrada en el ciclo 9

| ID | Clase | Ejemplo | Por qué |
|---|---|---|---|
| KB-04 | A discharge after a wait of stated length is a plan, even when the wait is described as uneventful | Tras 6 h de observación sin incidencias, alta a domicilio · After 6 h of uneventful observation, discharge home | In a simulation the stated wait has usually not passed; a plan is visible and can be carried out with one more line, a discharge run too early cannot be undone. 'Now/ahora' in the discharge, or a value measured without a threshold before it ('Tras 3 nebulizaciones PEF 80%, alta'), make it a discharge now. |
| KB-05 | A time at the end of what a discharge sends home belongs to the discharge | Discharge home with EpiPen in 2 hours · Alta a domicilio con EpiPen en 2 horas | It is a plan unless that part names something with its own time (a follow-up, a control, a return, a dose, a start, 'every/cada'): 'Alta con control en 2 horas' discharges now. |
