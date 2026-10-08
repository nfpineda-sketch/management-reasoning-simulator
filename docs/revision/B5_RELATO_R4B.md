# B-5 · Relato en español · Lote R4B: opioides (casos 4 y 5 de R4)

> **PARA REVISIÓN DOCENTE. Nada implementado. Preparado en la sesión autónoma del 2026-10-08, sin decisión docente.**
> Segunda parte del lote R4, en el orden canónico del banco (`clinical_cases.FAMILIES`; el mismo de `pilot_freeze.CASES`): `opioid_35m` y `opioid_67f`.
>
> Se aprueba el caso entero, en la versión objetivo impresa (`case_text.version`). No se crea `approvals.json` ni se
> cambia `case_text/es`. Relato leído de `case_text/es/opioid.json` contra el inglés vigente de cada caso, sin cambiar nada.

**En una mirada**

- **Pasajes:** 2 casos y 66 pasajes. 35 están cubiertos por frases del lote 0, ya aprobadas;
  **31 son propios y se revisan** (16, 15).
- **Corpus de la validación externa:** ninguno de los casos está en él, así que no hay pasajes fijos en este lote.
- **Términos ya aprobados:** T-1 a T-3 ya rigen en estos casos (comprobado: ninguno conserva «crepitaciones», «resistencia
  muscular» ni el adjetivo «confuso»), y P-1 no aplica. **Ninguna versión cambia:** la versión objetivo de cada caso es la
  del repositorio hoy.
- **Lo que no apareció:** desajustes de sentido, redacción clínicamente engañosa ni términos que choquen con X-1, la
  rúbrica, T-1 a T-3, P-1 o V-9.
- **Regla de versión (docente):** la aprobación ata la versión exacta revisada (la objetivo, si difiere de la del repositorio). Si al implementar el hash de un caso aprobado cambia, se detiene y vuelve a revisión docente.
- **Recomendación:** **APPROVE** en los 2 casos (categoría A: limpios).
- **Hallazgo fuera del relato (TD-84, propuesta):** en las dos, el examen neurológico que compone el motor pierde en inglés «small reactive» antes de «pupils»; el español lo conserva. No cambia la recomendación sobre el relato; pide una decisión docente aparte (abajo, en cada caso, y en `docs/revision/B5_IMPLEMENTATION_READINESS_MAP.md`).

## opioid_35m

- **Versión que se aprueba:** `a130f860dd36d35d309fb845cd389aa59551bc6a95643b2324900bc05649ad12` (la del repositorio hoy; sin cambios)
- **Pasajes:** 33. Cubiertos por frases del lote 0, ya aprobadas: 17. **Propios, a revisar: 16.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 35-year-old man is brought by a friend because he is difficult to wake and is breathing slowly. | Un hombre de 35 años es traído por un amigo porque cuesta despertarlo y respira lentamente. |
| 2 | `/history_source` | Accompanying friend | Amigo acompañante |
| 3 | `/history/chief_complaint/0` | His friend says he became difficult to wake and started breathing very slowly. | Su amigo cuenta que se volvió difícil despertarlo y que empezó a respirar muy lentamente. |
| 4 | `/history/associated_symptoms/0` | His friend noticed increasing sleepiness after he took a tablet for back pain. | Su amigo notó somnolencia progresiva después de que tomó una pastilla para el dolor de espalda. |
| 5 | `/history/associated_symptoms/1` | There was no witnessed seizure, fall or trauma. | No se presenció ninguna convulsión, caída ni traumatismo. |
| 6 | `/history/medical_history/0` | His friend reports a recent back strain and no known chronic neurological disorder. | Su amigo refiere una distensión de espalda reciente y ningún trastorno neurológico crónico conocido. |
| 7 | `/history/medications/0` | He took a tablet obtained from an acquaintance for pain; its contents are not confirmed. | Tomó una pastilla para el dolor obtenida de un conocido; su contenido no está confirmado. |
| 8 | `/history/onset/0` | Increasing sleepiness began within the last hour after the tablet. | La somnolencia progresiva comenzó en la última hora, después de tomar la pastilla. |
| 9 | `/history/risk_factors/0` | There is a recent exposure to a medication of uncertain contents. | Hay una exposición reciente a un medicamento de contenido incierto. |
| 10 | `/history/exposure/0` | His friend reports one pain tablet from an acquaintance; the drug identity and amount are not established. | Su amigo refiere una pastilla para el dolor obtenida de un conocido; no se han establecido la identidad del fármaco ni la cantidad. |
| 11 | `/history/breathing/0` | His friend counted long pauses between small, shallow breaths. | Su amigo contó pausas largas entre respiraciones pequeñas y superficiales. |
| 12 | `/history/neurological_symptoms/0` | He became progressively sleepy without a witnessed focal deficit. | Se puso progresivamente somnoliento, sin que se presenciara un déficit focal. |
| 13 | `/examination/Respiratory` | Very slow, shallow breaths with reduced chest excursion; breath sounds are equal when air enters. | Respiraciones muy lentas y superficiales, con expansión torácica disminuida; el murmullo pulmonar es simétrico cuando entra aire. |
| 14 | `/examination/Neurological` | Obtunded, with small reactive pupils and brief bilateral withdrawal to firm stimulation; no visible head injury. | Obnubilado, con pupilas pequeñas y reactivas, y retiro bilateral breve ante un estímulo firme; sin traumatismo craneano visible. |
| 15 | `/investigations/pocus/result/ivc` | 1.8 cm; minimal respiratory variation with shallow breaths | 1.8 cm; variación respiratoria mínima con respiraciones superficiales |
| 16 | `/investigations/chest_xray/result/report` | No focal infiltrate or pulmonary edema. | Sin infiltrado focal ni edema pulmonar. |

Cubiertos por el lote 0: `/history/allergies/0` (L0-33), `/examination/Cardiac` (L0-43), `/examination/Abdomen` (L0-39), `/investigations/pocus/result/lv` (L0-04), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. El relato no nombra ningún opioide ni la naloxona (la pastilla es de contenido no confirmado) y nada se lee como un tratamiento ya dado. **Lo que ve el residente (VERIFICADO con el motor, sólo lectura):** en la familia de opioides el examen respiratorio de la sala es siempre la frase del motor (A-9 a A-11; al llegar, A-10 «Respiratory rate 6 /min; breaths remain shallow.»), no `/examination/Respiratory`; hoy sale en inglés también en la sala en español, hasta implementar X-1 (A-10 y A-11 aprobadas; A-9 REVISE; las tres pasan a «{n}/min»). **Hallazgo nuevo, fuera del relato (TD-84, propuesta a decisión docente):** el examen neurológico de la sala no muestra este pasaje: el motor compone «Current mental status: …» y le agrega las pupilas que extrae del relato en inglés (`family_engine.py:3210–3218`). En inglés la extracción empieza en la palabra «pupils» y pierde los adjetivos que la preceden; el español (`language._neurological_tail`) toma la frase entera de la traducción aprobada. VERIFICADO con el motor, sólo lectura, al llegar: EN «pupils and brief bilateral withdrawal to firm stimulation»; ES «Pupilas pequeñas y reactivas, y retiro bilateral breve ante un estímulo firme.». La miosis queda visible sólo en español. El relato está bien en los dos idiomas; lo que falla es la extracción inglesa del motor.
- **Recomendación para el caso entero:** **APPROVE** (categoría A: limpio, sin cambios de texto).
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## opioid_67f

- **Versión que se aprueba:** `6f065b332e31a608efe54e082265f310eeebfff5aecbc06898905faa0aba2568` (la del repositorio hoy; sin cambios)
- **Pasajes:** 33. Cubiertos por frases del lote 0, ya aprobadas: 18. **Propios, a revisar: 15.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 67-year-old woman is brought from home with increasing sleepiness and slow breathing noticed by her spouse. | Una mujer de 67 años es traída desde su casa con somnolencia progresiva y respiración lenta advertidas por su cónyuge. |
| 2 | `/history_source` | Spouse and medication list | Cónyuge y lista de medicamentos |
| 3 | `/history/chief_complaint/0` | Her spouse reports that she has become increasingly sleepy and is breathing slowly. | Su cónyuge refiere que ella se ha puesto cada vez más somnolienta y que respira lentamente. |
| 4 | `/history/associated_symptoms/0` | Her spouse has struggled to keep her awake this morning. | A su cónyuge le ha costado mantenerla despierta esta mañana. |
| 5 | `/history/associated_symptoms/1` | There was no witnessed seizure, head injury or febrile illness. | No se presenció ninguna convulsión, traumatismo craneano ni cuadro febril. |
| 6 | `/history/medical_history/0` | Her spouse reports chronic pain and chronic kidney disease; she normally converses clearly and manages at home. | Su cónyuge refiere dolor crónico y enfermedad renal crónica; habitualmente conversa con claridad y se las arregla en casa. |
| 7 | `/history/medications/0` | Her medication list includes sustained-release morphine; her spouse is uncertain whether today's dose was repeated. | Su lista de medicamentos incluye morfina de liberación prolongada; su cónyuge no sabe con certeza si la dosis de hoy se repitió. |
| 8 | `/history/onset/0` | She became progressively sleepier during the morning after taking her regular medication. | Se puso progresivamente más somnolienta durante la mañana, después de tomar sus medicamentos habituales. |
| 9 | `/history/risk_factors/0` | She receives a long-acting opioid and has impaired renal function. | Recibe un opioide de acción prolongada y tiene la función renal deteriorada. |
| 10 | `/history/exposure/0` | Sustained-release morphine is prescribed; a possible repeated dose is unconfirmed, and no intent is established. | Tiene indicada morfina de liberación prolongada; no se ha confirmado una posible dosis repetida, y no se ha establecido intencionalidad. |
| 11 | `/history/breathing/0` | Her spouse noticed unusually slow shallow breathing with occasional pauses. | Su cónyuge notó una respiración inusualmente lenta y superficial, con pausas ocasionales. |
| 12 | `/history/oral_intake/0` | She has eaten little today because she has been too sleepy. | Hoy ha comido poco porque ha estado demasiado somnolienta. |
| 13 | `/examination/Respiratory` | Slow shallow breathing with reduced chest excursion; no focal wheeze or crackles. | Respiración lenta y superficial, con expansión torácica disminuida; sin sibilancias ni crépitos focales. |
| 14 | `/examination/Neurological` | Obtunded with small reactive pupils, briefly withdrawing both arms to a firm stimulus. | Obnubilada, con pupilas pequeñas y reactivas, retira brevemente ambos brazos ante un estímulo firme. |
| 15 | `/investigations/pocus/result/ivc` | 1.9 cm; minimal respiratory variation with shallow breaths | 1.9 cm; variación respiratoria mínima con respiraciones superficiales |

Cubiertos por el lote 0: `/history/allergies/0` (L0-33), `/examination/Cardiac` (L0-43), `/examination/Abdomen` (L0-38), `/investigations/pocus/result/lv` (L0-04), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/chest_xray/result/report` (L0-25), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. «Morfina de liberación prolongada» usa el nombre de V-9 (morphine → morfina). «No se ha confirmado una posible dosis repetida» es la historia del caso, no una dosis dada en la sala. El examen respiratorio de la sala es A-10 (como en la 35m). **Hallazgo nuevo, fuera del relato (TD-84, propuesta a decisión docente):** el examen neurológico de la sala no muestra este pasaje: el motor compone «Current mental status: …» y le agrega las pupilas que extrae del relato en inglés (`family_engine.py:3210–3218`). En inglés la extracción empieza en la palabra «pupils» y pierde los adjetivos que la preceden; el español (`language._neurological_tail`) toma la frase entera de la traducción aprobada. VERIFICADO con el motor, sólo lectura, al llegar: EN «pupils, briefly withdrawing both arms to a firm stimulus.»; ES «Pupilas pequeñas y reactivas, retira brevemente ambos brazos ante un estímulo firme.». La miosis queda visible sólo en español. El relato está bien en los dos idiomas; lo que falla es la extracción inglesa del motor.
- **Recomendación para el caso entero:** **APPROVE** (categoría A: limpio, sin cambios de texto).
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## Resumen del lote R4B

| Caso | Propios | Cubiertos por el lote 0 | Fijos del corpus | Versión objetivo que se aprueba | Recomendación | Decisión docente |
|---|---|---|---|---|---|---|
| `opioid_35m` | 16 | 17 | 0 | `a130f860…` (sin cambios) | APPROVE | ☐ |
| `opioid_67f` | 15 | 18 | 0 | `6f065b33…` (sin cambios) | APPROVE | ☐ |
| **Total** | **31** | **35** | **0** | | | |
