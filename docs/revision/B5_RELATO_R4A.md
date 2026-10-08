# B-5 · Relato en español · Lote R4A: hipoglicemia (casos 1 a 3)

> **DECIDIDO por la docencia (estado comunicado el 2026-10-08): los 3 casos, APPROVE WHOLE CASE. Nada
> implementado.** Primera parte del lote R4 de la revisión del relato
> (`docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md`). La docencia pidió los 3 primeros casos en el orden canónico del
> banco (`clinical_cases.FAMILIES`: hipoglicemia, después opioides; el mismo del manifiesto, `pilot_freeze.CASES`):
> - R4A: `hypoglycemia_28m`, `hypoglycemia_76f` y `hypoglycemia_54m_thiamine`;
> - R4B: `opioid_35m` y `opioid_67f` (R4 tiene 5 casos).
>
> Se aprueba el caso entero, en la versión objetivo impresa (`case_text.version`). No se crea `approvals.json` ni se
> cambia `case_text/es`. No se implementa nada.
>
> 2026-10-08 · rama `clinical-encounter-v0.13` · relato leído de `case_text/es/hypoglycemia.json` contra el inglés
> vigente de cada caso, sin cambiar nada.

**En una mirada**

- **Decidido (docente, estado del 2026-10-08):** «R4A = 3/3 approved; TOTAL = 21/30». La docencia no repitió los
  hashes: rige la regla de versión, así que la aprobación ata las versiones presentadas aquí (la 28m, la objetivo con
  T-3). El relato del piloto suma 21 de 30 casos.
- **Precisión posterior a la decisión (2026-10-08, sin cambio de la decisión):** el relato aprobado (`case_text`) no
  nombra la vía, pero el bloque de llegada de la sala sí agrega, en la hipoglicemia, una frase del motor que no es
  del caso: «Peripheral IV in place in the left forearm.» → «Vía venosa periférica instalada en el antebrazo
  izquierdo.» (`language.py`, `ENGINE_SENTENCES`). Sigue al relato (español si el caso está aprobado), no entra en
  el hash del caso y nombra el mismo sitio que A-13. No hace falta decisión.
- **Pasajes:** 3 casos y 99 pasajes. 51 están cubiertos por frases del lote 0, ya aprobadas; **48 son propios y se
  revisan** (16, 15 y 17).
- **Corpus de la validación externa:** ninguno de los 3 casos está en él, así que no hay pasajes fijos en este lote.
- **Término ya aprobado que se aplica:** T-3 «confundido», en `/examination/Neurological` de `hypoglycemia_28m`
  («Somnoliento y confuso» → «Somnoliento y confundido»). Es el pasaje para el que se decidió T-3. Las otras dos
  versiones no cambian.
- **Lo que no apareció:** desajustes de sentido, redacción clínicamente engañosa ni términos que choquen con X-1, la
  rúbrica, T-1 a T-3, P-1, V-9, A-12 a A-18 o F0-12.
- **Regla de versión (docente):** la aprobación ata la versión exacta revisada. Si la implementación cambia el hash
  de un caso aprobado, se detiene y vuelve a revisión docente.
- **Recomendación:** **APPROVE** en los 3 casos.

## A-12 a A-18, V-9 y F0-12

| Punto | Qué dice el relato | Contra qué se comparó | ¿Requiere decisión? |
|---|---|---|---|
| Vía venosa (A-12 a A-18, aprobadas) | El relato de los 3 casos no menciona ninguna vía: ni cánula, ni sitio, ni acceso intraóseo. La vía de llegada la pone el motor (`glucose_rescue.py`: cánula periférica en el antebrazo izquierdo), fuera del relato | A-12 a A-18 son frases del examen que escribe el motor («Cánula periférica en el antebrazo izquierdo…», la segunda cánula, la aguja intraósea, el suero glucosado que «pasa» por la vía) | **No.** Sin texto en común, no hay nada que alinear. Aprobar el relato no toca A-12 a A-18, ya aprobadas por separado |
| Glucosa y dextrosa (V-9) | El relato no nombra glucosa, dextrosa ni glucagón. Nombra la medicación habitual: «insulina basal y prandial» (28m), «glimepirida» y «una sulfonilurea» (76f) | V-9: dextrose → glucosa (bolo); dextrose infusion → suero glucosado; glucagon → glucagón | **No.** No hay término de V-9 en el relato; la medicación habitual va en su nombre genérico |
| Tiamina (54m) | «No ha recibido vitaminas» | V-9: thiamine → tiamina; el motor no modela tratamientos prehospitalarios en la hipoglicemia (`hypoglycemia_battery.py`) | **No.** El relato no nombra la tiamina y coincide con el motor: no hay vitaminas previas que dar por puestas |
| Naloxona y opioides (V-9) | No aparecen en estos 3 casos; la exposición se niega en términos generales («sedantes», «alcohol») | V-9: naloxone → naloxona | **No.** Se revisan en R4B, con los dos casos de opioides |
| F0-12 y la ejecución de la Fase 0 | El relato describe la llegada: no contiene órdenes, aclaraciones ni tratamientos ya administrados | F0-12: la respuesta a una aclaración completa sólo la orden retenida, y una orden nueva se procesa como propia; la regla de que un tratamiento previo no se vuelve a dar | **No.** Nada del relato se lee como una orden ejecutada ni como un tratamiento ya puesto |
| T-3 fuera de la 28m | «Habla de forma confusa» (54m) traduce «speech is muddled» y califica el habla; «La confusión» (54m) es el sustantivo | T-3 decide el adjetivo «confundido» en la voz del clínico | **No.** T-3 no se aplica a estas formas |

## hypoglycemia_28m

- **Versión que se aprueba:** `65cae7edde83847fd6641ca77a94b034da1ced9e1228df8894f9cbe09ab61950` (con T-3 aplicada; la del repositorio hoy es `ba88eb952b3d3b8d7dacace8c71dbf683529d08eb3c3265b2159645b3cbb212a`)
- **Pasajes:** 33. Cubiertos por frases del lote 0, ya aprobadas: 17. **Propios, a revisar: 16.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 28-year-old man is brought from work after becoming confused and having difficulty answering simple questions. | Un hombre de 28 años es traído desde su trabajo tras quedar confundido y con dificultad para responder preguntas simples. |
| 2 | `/history_source` | Coworker and emergency medication information | Compañero de trabajo e información de emergencia sobre medicamentos |
| 3 | `/history/chief_complaint/0` | His coworker reports sudden confusion and difficulty finding words. | Su compañero de trabajo refiere que de repente quedó confundido y con dificultad para encontrar las palabras. |
| 4 | `/history/associated_symptoms/0` | His coworker noticed shaking and sweating before he became confused. | Su compañero de trabajo notó que temblaba y sudaba antes de quedar confundido. |
| 5 | `/history/associated_symptoms/1` | There was no witnessed seizure, fall or head injury. | No se presenció ninguna convulsión, caída ni golpe en la cabeza. |
| 6 | `/history/medical_history/0` | His coworker reports type 1 diabetes; his emergency information confirms this. | Su compañero de trabajo refiere que tiene diabetes tipo 1; su información de emergencia lo confirma. |
| 7 | `/history/medications/0` | His medication record lists basal and mealtime insulin. | Su registro de medicamentos incluye insulina basal y prandial. |
| 8 | `/history/onset/0` | He was well at the start of work and became confused over the last 20 minutes. | Estaba bien al comienzo de la jornada y quedó confundido en los últimos 20 minutos. |
| 9 | `/history/risk_factors/0` | His coworker reports that he took his usual mealtime insulin but was called away before eating lunch. | Su compañero de trabajo refiere que se puso su insulina prandial habitual, pero lo llamaron y tuvo que irse antes de almorzar. |
| 10 | `/history/oral_intake/0` | His lunch was left uneaten after he took his mealtime insulin. | Su almuerzo quedó sin comer después de que se puso la insulina prandial. |
| 11 | `/history/exposure/0` | His coworker reports no known alcohol or sedative exposure during the shift. | Su compañero de trabajo no refiere exposición conocida a alcohol ni a sedantes durante el turno. |
| 12 | `/history/neurological_symptoms/0` | He became confused and had difficulty speaking; no one saw a persistent one-sided weakness. | Quedó confundido y le costaba hablar; nadie vio una debilidad persistente de un lado del cuerpo. |
| 13 | `/examination/Cardiac` | Regular tachycardia with palpable peripheral pulses. | Taquicardia regular con pulsos periféricos palpables. |
| 14 | `/examination/Respiratory` | Normal effort; clear bilateral breath sounds. | Esfuerzo respiratorio normal; murmullo pulmonar bilateral sin ruidos agregados. |
| 15 | `/examination/Neurological` | Drowsy and confused, but opens eyes to voice; speech is slow and all limbs move symmetrically. Pupils are equal and reactive. | Somnoliento y confundido, pero abre los ojos a la voz; habla lentamente y moviliza las cuatro extremidades en forma simétrica. Pupilas isocóricas y reactivas. *(T-3; antes: «Somnoliento y confuso, pero abre los ojos a la voz; habla lentamente y moviliza las cuatro extremidades en forma simétrica. Pupilas isocóricas y reactivas.»)* |
| 16 | `/investigations/chest_xray/result/report` | No acute pulmonary abnormality. | Sin alteraciones pulmonares agudas. |

Cubiertos por el lote 0: `/history/allergies/0` (L0-33), `/examination/Abdomen` (L0-38), `/investigations/pocus/result/lv` (L0-06), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/ivc` (L0-09), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. Se aplica T-3 en `/examination/Neurological`, ya aprobado: «Somnoliento y confuso» → «Somnoliento y confundido», como la presentación y la historia del mismo caso («quedó confundido»). Es el único pasaje del banco que T-3 cambia.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☒ **APPROVE WHOLE CASE** — docente, estado del 2026-10-08; versión aprobada `65cae7edde83847fd6641ca77a94b034da1ced9e1228df8894f9cbe09ab61950`. Incluye T-3 («Somnoliento y confundido»).

## hypoglycemia_76f

- **Versión que se aprueba:** `a7abad85dad8fdae2263696303b1a207b7f4d0580fe951cb3e47050d787df845` (la del repositorio hoy; sin cambios)
- **Pasajes:** 33. Cubiertos por frases del lote 0, ya aprobadas: 18. **Propios, a revisar: 15.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 76-year-old woman is brought by her son because she has become difficult to wake this morning. | Una mujer de 76 años es traída por su hijo porque esta mañana está difícil de despertar. |
| 2 | `/history_source` | Son and medication list | Hijo y lista de medicamentos |
| 3 | `/history/chief_complaint/0` | Her son reports that she has become unusually difficult to wake. | Su hijo refiere que está más difícil de despertar que de costumbre. |
| 4 | `/history/associated_symptoms/0` | Her son noticed sweating and reduced interaction. | Su hijo notó que sudaba y que interactuaba menos. |
| 5 | `/history/associated_symptoms/1` | There was no witnessed seizure or head injury. | No se presenció ninguna convulsión ni golpe en la cabeza. |
| 6 | `/history/medical_history/0` | Her son reports type 2 diabetes and chronic kidney disease; she is normally alert and independent at home. | Su hijo refiere que tiene diabetes tipo 2 y enfermedad renal crónica; habitualmente está alerta y es independiente en su casa. |
| 7 | `/history/medications/0` | Her medication list includes glimepiride; she continued taking it despite eating very little. | Su lista de medicamentos incluye glimepirida; siguió tomándola pese a que comía muy poco. |
| 8 | `/history/onset/0` | Her intake has been poor for two days; she was markedly less responsive this morning. | Su ingesta ha sido escasa durante dos días; esta mañana estaba marcadamente menos reactiva. |
| 9 | `/history/risk_factors/0` | She has continued a sulfonylurea during poor intake and has impaired renal function. | Ha seguido tomando una sulfonilurea mientras su ingesta era escasa y tiene la función renal alterada. |
| 10 | `/history/oral_intake/0` | Her son reports that she has eaten little for two days but continued her usual tablets. | Su hijo refiere que lleva dos días comiendo poco, pero siguió tomando sus pastillas habituales. |
| 11 | `/history/exposure/0` | Her son reports no new sedatives or known alcohol ingestion. | Su hijo no refiere sedantes nuevos ni ingesta conocida de alcohol. |
| 12 | `/history/neurological_symptoms/0` | Her son describes a generalized reduction in responsiveness rather than a witnessed focal weakness. | Su hijo describe una disminución generalizada de la reactividad en lugar de una debilidad focal presenciada. |
| 13 | `/examination/Cardiac` | Regular pulse with preserved peripheral volume. | Pulso regular, con pulsos periféricos de amplitud conservada. |
| 14 | `/examination/Respiratory` | Normal effort and clear bilateral breath sounds. | Esfuerzo respiratorio normal y murmullo pulmonar bilateral sin ruidos agregados. |
| 15 | `/examination/Neurological` | Opens eyes only briefly to a firm stimulus and localizes with both arms. Pupils are equal and reactive. | Abre los ojos solo brevemente ante un estímulo firme y localiza con ambos brazos. Pupilas isocóricas y reactivas. |

Cubiertos por el lote 0: `/history/allergies/0` (L0-33), `/examination/Abdomen` (L0-39), `/investigations/pocus/result/lv` (L0-04), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/ivc` (L0-11), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/chest_xray/result/report` (L0-25), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. Ningún término de T-1 a T-3 aparece en el caso.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☒ **APPROVE WHOLE CASE** — docente, estado del 2026-10-08; versión aprobada `a7abad85dad8fdae2263696303b1a207b7f4d0580fe951cb3e47050d787df845`.

## hypoglycemia_54m_thiamine

- **Versión que se aprueba:** `cbd0c47926b04387966b539cad27acd7de9dbce5d3f2093d560dede738ed608a` (la del repositorio hoy; sin cambios)
- **Pasajes:** 33. Cubiertos por frases del lote 0, ya aprobadas: 16. **Propios, a revisar: 17.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 54-year-old man is brought from a shelter after being found drowsy and unsteady. He has eaten almost nothing for days. | Un hombre de 54 años es traído desde un albergue tras ser encontrado somnoliento e inestable. Lleva días sin comer casi nada. |
| 2 | `/history_source` | Shelter staff and the paramedic record | Personal del albergue y registro de los paramédicos |
| 3 | `/history/chief_complaint/0` | His speech is muddled and he says he feels shaky. | Habla de forma confusa y dice que se siente tembloroso. |
| 4 | `/history/associated_symptoms/0` | He has been unsteady on his feet. | Ha estado inestable de pie. |
| 5 | `/history/associated_symptoms/1` | He has had no fever, cough or vomiting. | No ha tenido fiebre, tos ni vómitos. |
| 6 | `/history/medical_history/0` | He drinks heavily every day and has eaten very little for a week; he is not diabetic. | Bebe mucho alcohol todos los días y lleva una semana comiendo muy poco; no es diabético. |
| 7 | `/history/medications/0` | He takes no regular medicines and has received no vitamins. | No toma medicamentos de uso habitual y no ha recibido vitaminas. |
| 8 | `/history/onset/0` | The confusion and unsteadiness came on through this morning. | La confusión y la inestabilidad fueron apareciendo durante esta mañana. |
| 9 | `/history/risk_factors/0` | He drinks heavily and has eaten almost nothing for days. | Bebe mucho alcohol y lleva días sin comer casi nada. |
| 10 | `/history/oral_intake/0` | He has had almost nothing to eat for about a week, and alcohol most days. | Lleva alrededor de una semana sin comer casi nada, y ha bebido alcohol casi todos los días. |
| 11 | `/history/neurological_symptoms/0` | His walking has been unsteady and he says his vision feels unfocused. | Ha caminado de forma inestable y dice que siente la vista desenfocada. |
| 12 | `/history/chest_pain/0` | He reports no chest pain. | No refiere dolor torácico. |
| 13 | `/examination/Cardiac` | Regular mildly rapid pulse; no murmur. | Pulso regular y levemente rápido; sin soplos. |
| 14 | `/examination/Respiratory` | Normal effort; clear breath sounds. | Esfuerzo respiratorio normal; murmullo pulmonar sin ruidos agregados. |
| 15 | `/examination/Abdomen` | Soft, without tenderness or organomegaly. | Blando, sin dolor a la palpación ni visceromegalias. |
| 16 | `/examination/Neurological` | Drowsy but rousable; gaze is unsteady with a few beats of nystagmus, and gait could not be tested safely. Pupils are equal and reactive. | Somnoliento pero despertable; mirada inestable con algunas sacudidas de nistagmo, y no fue posible evaluar la marcha de forma segura. Pupilas isocóricas y reactivas. |
| 17 | `/investigations/chest_xray/result/report` | No focal consolidation. | Sin consolidación focal. |

Cubiertos por el lote 0: `/history/allergies/0` (L0-33), `/investigations/pocus/result/lv` (L0-06), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/ivc` (L0-09), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. «Habla de forma confusa» traduce «speech is muddled»: califica el habla, no el estado mental, y T-3 no lo toca; «La confusión» (`/history/onset/0`) es el sustantivo. «No ha recibido vitaminas» coincide con el motor, que no modela tratamientos prehospitalarios en la hipoglicemia (`hypoglycemia_battery.py`).
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☒ **APPROVE WHOLE CASE** — docente, estado del 2026-10-08; versión aprobada `cbd0c47926b04387966b539cad27acd7de9dbce5d3f2093d560dede738ed608a`.

## Resumen del lote R4A

| Caso | Propios | Cubiertos por el lote 0 | Fijos del corpus | Versión objetivo que se aprueba | Recomendación | Decisión docente |
|---|---|---|---|---|---|---|
| `hypoglycemia_28m` | 16 | 17 | 0 | `65cae7ed…` (con T-3) | APPROVE | ☒ APPROVE |
| `hypoglycemia_76f` | 15 | 18 | 0 | `a7abad85…` (sin cambios) | APPROVE | ☒ APPROVE |
| `hypoglycemia_54m_thiamine` | 17 | 16 | 0 | `cbd0c479…` (sin cambios) | APPROVE | ☒ APPROVE |
| **Total** | **48** | **51** | **0** | | | |

Siguiente: R4B (`opioid_35m` y `opioid_67f`), en `docs/revision/B5_RELATO_R4B.md`.
