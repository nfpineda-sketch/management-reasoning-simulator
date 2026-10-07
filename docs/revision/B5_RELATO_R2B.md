# B-5 · Relato en español · Lote R2B: respiratorio (casos 4 a 6)

> **DECIDIDO por la docencia el 2026-10-07: los 3 casos, APPROVE WHOLE CASE (la 24f, con P-1). Nada
> implementado.** Segunda mitad del lote R2 de la revisión del relato
> (`docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md`), en el orden canónico del banco (`clinical_cases.FAMILIES`):
> `pulmonary_edema_75f`, `asthma_24f` y `asthma_49m`. Se aprueba el caso entero, en la versión objetivo impresa
> (`case_text.version`). No se crea `approvals.json` ni se cambia `case_text/es`. No se implementa nada del motor
> (A-6, A-6a, A-6b, A-7-49m, A-8a; TD-83).
>
> 2026-10-07 · rama `clinical-encounter-v0.13` · relato leído de `case_text/es/pulmonary_edema.json` y
> `case_text/es/asthma.json` contra el inglés vigente de cada caso, sin cambiar nada.

**En una mirada**

- **Decidido (docente, 2026-10-07):** 3 de 3 casos aprobados, cada uno en su versión objetivo; `asthma_24f` con P-1. Con R2A,
  el bloque respiratorio queda aprobado entero (6 de 6) y el relato del piloto suma 12 de 30 casos. Rige la regla
  de versión.
- **Pasajes:** 3 casos y 99 pasajes. 50 están cubiertos por frases del lote 0, ya aprobadas; **49 son propios y se
  revisan** (19, 14 y 16). Con R2A, el bloque respiratorio suma los 102 pasajes propios que preveía el diseño (§4).
- **Corpus de la validación externa:** `asthma_24f` está en él (C01). Sus 3 pasajes fijos (la presentación,
  `/history/chief_complaint/0` y `/history/onset/0`) van marcados 🔒. Ya están aprobados tal como están escritos y no
  cambian; ni T-1 ni P-1 los tocan.
- **Término ya aprobado que se aplica:** T-1 «crépitos», en `/examination/Respiratory` de `pulmonary_edema_75f`. Los
  casos de asma no tienen «crackles», «guarding» ni «confused».
- **Una observación de sentido (P-1), en `asthma_24f`:** «crushing» está traducido «opresivo» en el pasaje que
  distingue la opresión del asma de un dolor de tipo coronario, cuando la presentación fija del mismo caso llama
  «opresión torácica» a su síntoma. Propuesta mínima: «aplastante», como en `pulmonary_edema_58m` (R2A) y en
  `anaphylaxis_29f`. Se imprimen las dos versiones objetivo, con P-1 y sin P-1.
- **Intersección con A-6, A-7 y A-8 (abajo):** en `asthma_49m`, el examen respiratorio de llegada es el texto exacto de
  A-6a. Nada en el relato contradice A-6a, A-6b, A-7-49m ni A-8a. No hace falta ninguna decisión nueva.
- **Regla de versión (docente, 2026-10-07):** la aprobación ata la versión objetivo presentada en la revisión, no la
  que está hoy en el repositorio. Al implementar, el español del repositorio tiene que dar exactamente ese hash antes
  de generar la entrada de aprobación; si da otro, se detiene y vuelve a revisión docente.
- **Recomendación:** **APPROVE** la 75f y la 49m; **APPROVE con P-1** la 24f.

## Intersección con A-6, A-7 y A-8 (estados límite de la 49m)

Lo aprobado el 2026-10-07 (paquete, bloque A; TD-83, sin implementar): A-6a, A-6b, A-7-49m y A-8a, y la regla de que
el examen dice el estado actual del motor, no la orden ejecutada.

| Punto | Qué dice el relato | Qué dicen las frases aprobadas | ¿Requiere decisión? |
|---|---|---|---|
| Examen de llegada de la 49m | `/examination/Respiratory`: «Esfuerzo respiratorio severo, con murmullo pulmonar muy disminuido en forma bilateral y solo sibilancias tenues. No logra completar una maniobra confiable de flujo espiratorio máximo.» | A-6a es este mismo texto, en inglés y en español (comprobado carácter por carácter); el paquete dice que su español «es el del relato del caso» | **No.** Aprobar la 49m tal cual mantiene A-6a idéntica. Cambiar este pasaje obligaría a reabrir A-6a y a realinear A-6b, A-7-49m y A-8a |
| Vocabulario de la gravedad | «murmullo pulmonar muy disminuido en forma bilateral», «solo sibilancias tenues» | A-6b, A-7-49m y A-8a repiten las mismas dos expresiones («sigue muy disminuido», «con solo sibilancias tenues») | **No.** Coinciden |
| Gravedad en el resto del relato de la 49m | Presentación: «Se ve cansado», «las sibilancias suenan más silenciosas que antes». Historia: «antes el pecho le silbaba más fuerte», «está moviendo menos aire». Examen neurológico: «Somnoliento» | A-6a a A-8a conservan la gravedad de llegada mientras la obstrucción no mejore | **No.** Nada del relato se lee como mejoría: las sibilancias más suaves se presentan como agotamiento, igual que en inglés |
| «Entrada de aire» y «murmullo pulmonar» | El relato traduce «air entry» como «murmullo pulmonar» en sus 4 casos (24f, 49m, `pneumonia_83m` y `trauma_limb_hemorrhage_27m`) | A-5, A-6 y la segunda parte de A-8, ya aprobadas, dicen «entrada de aire» («de uso clínico común», `spanish_drafts.py`); A-6a, A-6b, A-7-49m y A-8a dicen «murmullo pulmonar» | **No.** Es información. En la 24f, la llegada dice «murmullo pulmonar disminuido» y, desde la primera orden, el motor dice A-6 («Entrada de aire disminuida en ambos lados…»). Los dos términos dicen lo mismo y ninguno cambia la gravedad leída. Igualarlos obligaría a reabrir frases del motor ya aprobadas; no se recomienda en esta revisión |
| Neumotórax (A-7, A-7-49m, A-8, A-8a) | El relato no lo menciona: la radiografía y la ecografía de llegada dicen «sin neumotórax» en los dos casos de asma | El neumotórax del asma ocurre sólo con ventilación invasiva, siempre a la derecha (comprobado en el motor) | **No.** El relato describe la llegada, antes de cualquier complicación |

Pendiente, ya conocido y fuera de este lote: hasta implementar TD-83, el motor muestra A-6 en la 49m desde la primera
orden, aun con oxígeno solo. Lo decidió la docencia (A-6 REVISE) y lo corrige la implementación, no el relato.

## pulmonary_edema_75f

- **Versión que se aprueba:** `4695ee50cfa00208c0c9fa70b527e7495119392cf279487b72a5880d25d2d06c` (con T-1 aplicada; la del repositorio hoy es `53c936c98a9624bb20a784cb7cc2580c25800697832ae54afe036461d91bfe9f`)
- **Pasajes:** 33. Cubiertos por frases del lote 0, ya aprobadas: 14. **Propios, a revisar: 19.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 75-year-old woman presents with breathlessness that is now preventing her from resting in bed. | Una mujer de 75 años consulta por disnea que ahora le impide descansar en la cama. |
| 2 | `/history/chief_complaint/0` | My breathing has become so bad that I have to sit up all the time. | Mi respiración ha empeorado tanto que tengo que estar sentada todo el tiempo. |
| 3 | `/history/associated_symptoms/0` | My ankles have become more swollen and my clothes feel tighter. | Se me han hinchado más los tobillos y siento la ropa más apretada. |
| 4 | `/history/associated_symptoms/1` | I have no fever, rigors or new sputum. | No tengo fiebre, escalofríos con temblor ni expectoración nueva. |
| 5 | `/history/medical_history/0` | I have heart failure with an ejection fraction around 30% and chronic kidney disease. | Tengo insuficiencia cardíaca con una fracción de eyección de alrededor del 30% y enfermedad renal crónica. |
| 6 | `/history/medications/0` | I take a loop diuretic and heart-failure medicines, but missed the diuretic for three days while travelling. | Tomo un diurético de asa y medicamentos para la insuficiencia cardíaca, pero me salté el diurético durante tres días mientras estaba de viaje. |
| 7 | `/history/onset/0` | The swelling increased over four days; my breathing became much worse overnight. | La hinchazón fue aumentando a lo largo de cuatro días; durante la noche la respiración se me puso mucho peor. |
| 8 | `/history/risk_factors/0` | I have known reduced cardiac function and missed my usual diuretic. | Tengo la función cardíaca disminuida, ya conocida, y me salté mi diurético habitual. |
| 9 | `/history/breathing/0` | I have slept sitting up for the last two nights. | Las últimas dos noches he dormido sentada. |
| 10 | `/history/chest_pain/0` | I have not had a new focal or pressure-like chest pain. | No he tenido un dolor de pecho nuevo, ya sea localizado u opresivo. |
| 11 | `/history/urinary_symptoms/0` | I have passed less urine but have no dysuria. | He orinado menos, pero no tengo disuria. |
| 12 | `/examination/Cardiac` | Regular tachycardia, elevated jugular venous pressure and bilateral pitting ankle edema. | Taquicardia regular, presión venosa yugular elevada y edema bilateral de tobillos con fóvea. |
| 13 | `/examination/Respiratory` | Marked respiratory effort with bilateral crackles extending to the mid-zones. | Esfuerzo respiratorio marcado, con crépitos bilaterales que se extienden hasta los campos medios. *(T-1; antes: «Esfuerzo respiratorio marcado, con crepitaciones bilaterales que se extienden hasta los campos medios.»)* |
| 14 | `/examination/Abdomen` | Soft; no focal tenderness. | Blando; sin dolor focal a la palpación. |
| 15 | `/examination/Neurological` | Awake and oriented, speaking in short phrases. | Vigil y orientada, habla en frases cortas. |
| 16 | `/investigations/pocus/result/lv` | Severely reduced global contraction | Contracción global severamente disminuida |
| 17 | `/investigations/pocus/result/ivc` | 2.5 cm; minimal inspiratory collapse | 2.5 cm; colapso inspiratorio mínimo |
| 18 | `/investigations/pocus/result/lung_consolidation` | No consolidation; small bilateral pleural effusions | Sin consolidación; pequeños derrames pleurales bilaterales |
| 19 | `/investigations/chest_xray/result/report` | Cardiomegaly, bilateral vascular and interstitial congestion, and small pleural effusions. | Cardiomegalia, congestión vascular e intersticial bilateral, y pequeños derrames pleurales. |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-16), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. Se aplica T-1 en `/examination/Respiratory`, ya aprobado («crépitos bilaterales que se extienden hasta los campos medios»; la concordancia no cambia). Con eso, la llegada usa el mismo término que las frases del motor A-2 y A-3. La decisión A-2 (REVISE, TD-51) es sobre el texto del motor durante el agotamiento, no sobre este pasaje de llegada, que no se toca.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☒ **APPROVE WHOLE CASE** — docente, 2026-10-07; versión aprobada `4695ee50cfa00208c0c9fa70b527e7495119392cf279487b72a5880d25d2d06c`. Incluye T-1 (crackles → crépitos). La revisión A-2 del motor sigue igual y no es parte de esta aprobación.

## asthma_24f

- **Versión objetivo recomendada (con P-1):** `844d280d53271a3444adc8293a73f42ec5aac090a08d4af839d5100a5fbc4615`
- **Versión objetivo tal cual (sin P-1):** `6471a99e221d09521b1f72410763897cd1a6d4d588fc2f17b196f0fea93556ab` (la del repositorio hoy)
- **Pasajes:** 33. Cubiertos por frases del lote 0, ya aprobadas: 19. **Propios, a revisar: 14.**
- **Pasajes que fija el corpus de la validación externa:** 3 (`/presentation`, `/history/chief_complaint/0`, `/history/onset/0`), marcados 🔒. Ya están aprobados tal como están escritos (§8 del diseño, 2026-10-07); se muestran para leerlos con el caso y no se cambian en esta revisión. Un error clínicamente relevante se escalaría.

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` 🔒 | A 24-year-old woman presents with worsening breathlessness and chest tightness. She is sitting forward and speaking in short phrases. | Una mujer de 24 años consulta por disnea y opresión torácica que han ido empeorando. Está sentada inclinada hacia adelante y habla en frases cortas. |
| 2 | `/history/chief_complaint/0` 🔒 | My chest is tight and I cannot get my breathing under control. | Siento el pecho apretado y no logro controlar la respiración. |
| 3 | `/history/associated_symptoms/0` | I have a dry cough and can hear myself wheezing. | Tengo tos seca y escucho que me silba el pecho. |
| 4 | `/history/associated_symptoms/1` | I have no fever, productive sputum, rash or lip swelling. | No tengo fiebre, flemas, erupción en la piel ni hinchazón de los labios. |
| 5 | `/history/medical_history/0` | I have asthma and allergic rhinitis; I have previously needed an emergency visit but have never been intubated. | Tengo asma y rinitis alérgica; antes he necesitado una consulta de urgencia, pero nunca me han intubado. |
| 6 | `/history/medications/0` | I have used my reliever repeatedly today; my preventer inhaler ran out last week. | Hoy he usado una y otra vez mi inhalador de rescate; el inhalador de mantención se me acabó la semana pasada. |
| 7 | `/history/onset/0` 🔒 | Symptoms worsened over eight hours after a day outdoors with heavy pollen exposure. | Los síntomas empeoraron a lo largo de ocho horas después de un día al aire libre con alta exposición al polen. |
| 8 | `/history/risk_factors/0` | I have been without my inhaled controller and have needed frequent reliever use. | He estado sin mi inhalador de mantención y he necesitado usar el inhalador de rescate con frecuencia. |
| 9 | `/history/breathing/0` | It is difficult to breathe out, and the reliever only helps briefly. | Me cuesta sacar el aire, y el inhalador de rescate solo me ayuda por poco rato. |
| 10 | `/history/chest_pain/0` | The sensation is tightness with breathing, not a separate focal or crushing pain. | La sensación es de pecho apretado al respirar, no un dolor aparte que sea localizado o aplastante. *(**P-1, propuesto**; hoy: «La sensación es de pecho apretado al respirar, no un dolor aparte que sea localizado u opresivo.»)* |
| 11 | `/history/exposure/0` | There was heavy pollen exposure; no food exposure or new medication preceded the symptoms. | Hubo una alta exposición al polen; ninguna exposición a alimentos ni medicamento nuevo precedió a los síntomas. |
| 12 | `/examination/Respiratory` | Marked effort, prolonged expiration and widespread expiratory wheeze with reduced air entry. Peak expiratory flow is 35% of her documented personal best. | Esfuerzo respiratorio marcado, espiración prolongada y sibilancias espiratorias difusas, con murmullo pulmonar disminuido. El flujo espiratorio máximo corresponde al 35% de su mejor valor personal registrado. |
| 13 | `/examination/Neurological` | Awake, oriented and cooperative, but speech is limited by breathing. | Vigil, orientada y cooperadora, pero con el habla limitada por la respiración. |
| 14 | `/investigations/chest_xray/result/report` | Hyperinflation without focal consolidation or pneumothorax. | Hiperinsuflación sin consolidación focal ni neumotórax. |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/examination/Cardiac` (L0-44), `/examination/Abdomen` (L0-38), `/investigations/pocus/result/lv` (L0-04), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/ivc` (L0-10), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** **una, de sentido (P-1), en `/history/chest_pain/0`.** El pasaje existe para distinguir la opresión del asma de un dolor de tipo coronario: «tightness … not a separate focal or crushing pain». Hoy traduce «crushing» como «opresivo». En el relato, «opresión» es la palabra de «tightness» (la presentación fija de este mismo caso dice «opresión torácica») y «crushing» se traduce «aplastante» en `pulmonary_edema_58m` (aprobado en R2A) y en `anaphylaxis_29f`. Así, el caso afirma «opresión torácica» y luego niega un dolor «opresivo»: el residente puede leer que la paciente niega lo que la presentación afirma. Propuesta mínima: «…localizado u opresivo» → «…localizado o aplastante». No toca los 3 pasajes 🔒, que se leyeron con el caso sin hallar ningún error clínicamente relevante.
- **Recomendación para el caso entero:** **APPROVE con P-1** (versión `844d280d…`). Si la docencia prefiere el texto actual: APPROVE tal cual (versión `6471a99e…`).
- **Decisión docente:** ☒ **APPROVE WHOLE CASE WITH P-1** — docente, 2026-10-07; versión aprobada `844d280d53271a3444adc8293a73f42ec5aac090a08d4af839d5100a5fbc4615`. **Con P-1**: en `/history/chest_pain/0`, «…no un dolor aparte que sea localizado o aplastante.» Motivo docente: «crushing» no se traduce «opresivo» aquí, porque el caso ya usa «opresión» para «tightness», y la negación podría parecer que contradice el síntoma de presentación. Los 3 pasajes fijos del corpus siguen exactamente como están.

## asthma_49m

- **Versión que se aprueba:** `6b8cc7770904dce49a87fccc7ff91b4948d06d2c422c825854d0dc722d057540` (la del repositorio hoy; sin cambios)
- **Pasajes:** 33. Cubiertos por frases del lote 0, ya aprobadas: 17. **Propios, a revisar: 16.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 49-year-old man is brought in with persistent breathing difficulty. He appears tired and responds to questions only briefly. Handover notes that the wheeze sounds quieter than it did earlier. | Un hombre de 49 años es traído por dificultad respiratoria persistente. Se ve cansado y solo responde brevemente a las preguntas. En la entrega se señala que las sibilancias suenan más silenciosas que antes. |
| 2 | `/history/chief_complaint/0` | His partner reports worsening breathing difficulty and increasing exhaustion. | Su pareja refiere que la dificultad respiratoria ha ido empeorando y que está cada vez más agotado. |
| 3 | `/history/associated_symptoms/0` | His partner says the wheeze was louder earlier and he is now finding it difficult to speak. | Su pareja cuenta que antes el pecho le silbaba más fuerte y que ahora le cuesta hablar. |
| 4 | `/history/associated_symptoms/1` | There has been a dry cough without fever, purulent sputum or a rash. | Ha tenido tos seca, sin fiebre, expectoración purulenta ni erupción en la piel. |
| 5 | `/history/medical_history/0` | His partner reports asthma and a previous intensive care admission requiring ventilation. | Su pareja refiere que tiene asma y que antes estuvo hospitalizado en cuidados intensivos, donde requirió ventilación. |
| 6 | `/history/medications/0` | He uses an inhaled corticosteroid/long-acting bronchodilator and has repeatedly used his rescue inhaler today. | Usa un corticoide inhalado/broncodilatador de acción prolongada y hoy ha usado una y otra vez su inhalador de rescate. |
| 7 | `/history/onset/0` | Breathing worsened through the day after cleaning a dusty storage room; he became sleepier over the last hour. | La respiración empeoró a lo largo del día después de limpiar una bodega polvorienta; en la última hora se fue poniendo más somnoliento. |
| 8 | `/history/risk_factors/0` | He has a previous near-fatal exacerbation and little response to repeated home reliever use. | Tiene el antecedente de una exacerbación casi fatal y ha respondido poco al uso repetido del inhalador de rescate en casa. |
| 9 | `/history/breathing/0` | His partner says he is moving less air and can no longer complete a sentence. | Su pareja cuenta que está moviendo menos aire y que ya no logra terminar una frase. |
| 10 | `/history/exposure/0` | Dust exposure preceded the symptoms; there was no witnessed aspiration or new medication. | La exposición al polvo precedió a los síntomas; no hubo aspiración presenciada ni medicamento nuevo. |
| 11 | `/history/chest_pain/0` | Before becoming sleepy he described diffuse tightness rather than a focal chest pain. | Antes de ponerse somnoliento describió una opresión difusa en lugar de un dolor torácico localizado. |
| 12 | `/examination/Cardiac` | Regular tachycardia. | Taquicardia regular. |
| 13 | `/examination/Respiratory` | Severe effort with very poor bilateral air entry and only faint wheeze. He cannot complete a reliable peak-flow maneuver. | Esfuerzo respiratorio severo, con murmullo pulmonar muy disminuido en forma bilateral y solo sibilancias tenues. No logra completar una maniobra confiable de flujo espiratorio máximo. |
| 14 | `/examination/Neurological` | Drowsy, opens eyes to voice and follows simple commands briefly; no lateralizing motor deficit. | Somnoliento, abre los ojos a la voz y obedece órdenes simples por breves momentos; sin déficit motor lateralizado. |
| 15 | `/investigations/pocus/result/ivc` | 1.6 cm; >50% inspiratory collapse | 1.6 cm; colapso inspiratorio >50% |
| 16 | `/investigations/chest_xray/result/report` | Hyperinflation without pneumothorax or focal air-space opacity. | Hiperinsuflación sin neumotórax ni opacidad alveolar focal. |

Cubiertos por el lote 0: `/history_source` (L0-32), `/history/allergies/0` (L0-33), `/examination/Abdomen` (L0-38), `/investigations/pocus/result/lv` (L0-04), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. **Intersección con A-6a:** el examen respiratorio de llegada (`/examination/Respiratory`) es, en inglés y en español, el texto exacto de A-6a, aprobada el 2026-10-07 («su español es el del relato del caso»). Aprobar este caso fija también el español de A-6a; cambiar este pasaje obligaría a revisar A-6a y a mantener alineadas A-6b, A-7-49m y A-8a, que repiten «murmullo pulmonar … muy disminuido en forma bilateral» y «solo sibilancias tenues». La presentación («las sibilancias suenan más silenciosas que antes», «se ve cansado»), la historia («antes el pecho le silbaba más fuerte», «está moviendo menos aire») y el examen neurológico («Somnoliento») dicen la misma gravedad que A-6a: nada en el relato se lee como mejoría.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☒ **APPROVE WHOLE CASE** — docente, 2026-10-07; versión aprobada `6b8cc7770904dce49a87fccc7ff91b4948d06d2c422c825854d0dc722d057540`. El examen respiratorio de llegada no se cambia: es la redacción aprobada de A-6a y debe seguir alineado con A-6b, A-7-49m y A-8a. «Murmullo pulmonar» y «entrada de aire» siguen aceptados en sus contextos ya aprobados; no hace falta decisión nueva.

## Resumen del lote R2B

| Caso | Propios | Cubiertos por el lote 0 | Fijos del corpus | Versión objetivo que se aprueba | Recomendación | Decisión docente |
|---|---|---|---|---|---|---|
| `pulmonary_edema_75f` | 19 | 14 | 0 | `4695ee50…` (con T-1) | APPROVE | ☒ APPROVE |
| `asthma_24f` | 14 | 19 | 3 🔒 | `844d280d…` (con P-1) · tal cual: `6471a99e…` | APPROVE con P-1 | ☒ APPROVE con P-1 |
| `asthma_49m` | 16 | 17 | 0 | `6b8cc777…` (sin cambios) | APPROVE | ☒ APPROVE |
| **Total** | **49** | **50** | **3** | | | |

Siguiente, según el orden docente: R3 (TEP y bradicardias), en dos mitades. R3A, en `docs/revision/B5_RELATO_R3A.md`.
