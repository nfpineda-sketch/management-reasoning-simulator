# B-5 · Relato en español · Lote R3B: bradicardias (casos 4 a 6)

> **DECIDIDO por la docencia el 2026-10-08: los 3 casos, APPROVE WHOLE CASE. Nada implementado.** Segunda mitad
> del lote R3 de la revisión del relato
> (`docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md`), en el orden canónico del banco (`clinical_cases.FAMILIES`):
> `bradycardia_avb3_78f`, `bradycardia_bb_54f` y `bradycardia_hyperk_63m`. Se aprueba el caso entero, en la versión
> objetivo impresa (`case_text.version`). No se crea `approvals.json` ni se cambia `case_text/es`. No se implementa
> K-E6.
>
> 2026-10-07 · rama `clinical-encounter-v0.13` · relato leído de `case_text/es/bradycardia.json` contra el inglés
> vigente de cada caso, sin cambiar nada.

**En una mirada**

- **Decidido (docente, 2026-10-08):** 3 de 3 casos aprobados, cada uno en la versión exacta revisada (la del repositorio). Con
  R3A, el bloque de TEP y bradicardias queda aprobado entero (6 de 6) y el relato del piloto suma 18 de 30 casos.
  T-3, V-9 y K-E6 no requieren ninguna decisión docente adicional para estos 3 casos.
- **Pasajes:** 3 casos y 110 pasajes. 56 están cubiertos por frases del lote 0, ya aprobadas; **54 son propios y se
  revisan** (18, 16 y 20). Con R3A, el bloque suma los 111 pasajes propios que preveía el diseño (§4).
- **Corpus de la validación externa:** ninguno de los 3 casos está en él, así que no hay pasajes fijos en este lote.
- **Términos ya aprobados:** T-1 ya rige en la 63m («sin crépitos»); «guarding» no aparece; «confused» no aparece
  (abajo). **Ninguna versión cambia:** la versión objetivo de cada caso es la del repositorio hoy.
- **Lo que no apareció:** desajustes de sentido, redacción clínicamente engañosa ni términos que choquen con X-1, la
  rúbrica, T-1 a T-3, P-1, V-9 o K-E6.
- **Regla de versión (docente, 2026-10-07):** la aprobación ata la versión exacta revisada. Si la implementación
  cambia el hash de un caso aprobado, se detiene y vuelve a revisión docente.
- **Recomendación:** **APPROVE** en los 3 casos.

## T-3, V-9 y K-E6

| Punto | Qué dice el relato | Contra qué se comparó | ¿Requiere decisión? |
|---|---|---|---|
| T-3 («confused» → «confundido») | «Confused» no aparece en ninguno de los 3 casos, tampoco en los pasajes del lote 0. La 78f usa el sustantivo: «without … confusion afterwards» → «sin … confusión posterior» | T-3 decide el adjetivo en la voz del clínico (sólo `hypoglycemia_28m`) | **No.** «Confusión» es el sustantivo correcto y T-3 no lo toca |
| V-9 (nombres de fármacos) | «propranolol» (54f) y «betabloqueador» (78f, la clase) | V-9 (aprobada, XR-06): propranolol → propranolol; la clase beta_blocker → betabloqueador | **No.** Coinciden |
| Medicación habitual fuera de V-9 | amlodipino, atorvastatina, digoxina (78f); losartán (54f); carbonato de calcio, insulina, espironolactona (63m) | V-9 cubre los fármacos que el lector reconoce como orden; éstos son medicación de la historia, en su nombre genérico | **No.** Ninguno contradice V-9 |
| Antídotos | El relato no nombra antídotos (atropina, glucagón, gluconato o cloruro de calcio). El «carbonato de calcio» de la 63m es el quelante de fósforo que toma con las comidas | V-9: «gluconato de calcio», «cloruro de calcio», «glucagón», «atropina» | **No.** El español conserva la misma distinción que el inglés entre la sal de calcio habitual y las de antídoto |
| K-E6 («circulatory arrest from profound bradycardia» → «paro circulatorio por bradicardia profunda», REVISE, sin implementar) | El relato no dice «bradycardia» ni «arrest» en ningún caso. La lentitud se describe como «Pulso muy lento y regular» (examen de los 3) y, en la presentación, «muy lenta» (54f) o «lento» (63m), con la misma ambigüedad del inglés («very slow», «slow»: el pulso o la respuesta) | K-E6 nombra el evento terminal del motor, no la llegada | **No.** No hay conflicto: el relato describe la llegada, antes de cualquier paro. «Desmayos» (78f) y «colapso» (68m, aprobada en R3A) son síncope en casa, no el paro de K-E6 |

## bradycardia_avb3_78f

- **Versión que se aprueba:** `677c6278c0afd61dfc0e8c284473e88109b0d6e9e9222f5883555c60b338d3a7` (la del repositorio hoy; sin cambios)
- **Pasajes:** 36. Cubiertos por frases del lote 0, ya aprobadas: 18. **Propios, a revisar: 18.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 78-year-old woman is brought in after repeated blackouts at home. She is grey, cold and difficult to keep awake. | Una mujer de 78 años es traída tras desmayos repetidos en su casa. Está grisácea, fría y cuesta mantenerla despierta. |
| 2 | `/history_source` | Son | Hijo |
| 3 | `/history/chief_complaint/0` | Her son says she has blacked out three times today, each time without warning. | Su hijo cuenta que hoy se ha desmayado tres veces, cada vez sin previo aviso. |
| 4 | `/history/associated_symptoms/0` | Her son reports no chest pain and no palpitations that she described. | Su hijo refiere que ella no describió dolor en el pecho ni palpitaciones. |
| 5 | `/history/associated_symptoms/1` | She has been increasingly breathless on stairs for a fortnight. | Desde hace dos semanas le falta cada vez más el aire al subir escaleras. |
| 6 | `/history/medical_history/0` | Her son reports high blood pressure and kidney disease; she has never had a heart attack. | Su hijo refiere presión alta y enfermedad renal; nunca ha tenido un infarto. |
| 7 | `/history/medications/0` | Her son lists amlodipine and atorvastatin. He is certain there is no beta blocker and no digoxin, and the doses have not changed. | Su hijo enumera amlodipino y atorvastatina. Está seguro de que no toma ningún betabloqueador ni digoxina, y de que las dosis no han cambiado. |
| 8 | `/history/onset/0` | The blackouts began this morning and have become more frequent through the day. | Los desmayos comenzaron esta mañana y se han vuelto más frecuentes a lo largo del día. |
| 9 | `/history/risk_factors/0` | She has had two weeks of exertional breathlessness before today. | Antes de hoy, llevaba dos semanas con falta de aire al hacer esfuerzos. |
| 10 | `/history/neurological_symptoms/0` | The episodes were sudden, brief and without shaking, tongue-biting or confusion afterwards. | Los episodios fueron súbitos, breves y sin sacudidas, mordedura de lengua ni confusión posterior. |
| 11 | `/history/chest_pain/0` | Her son reports no chest pain at any point. | Su hijo refiere que en ningún momento tuvo dolor en el pecho. |
| 12 | `/history/breathing/0` | The breathlessness on exertion has been building for a fortnight. | La falta de aire al hacer esfuerzos ha ido aumentando desde hace dos semanas. |
| 13 | `/history/exposure/0` | There is no new medicine, no overdose and no herbal preparation. | No hay ningún medicamento nuevo, ni sobredosis, ni preparado de hierbas. |
| 14 | `/history/oral_intake/0` | She has been eating and drinking normally. | Ha estado comiendo y tomando líquidos con normalidad. |
| 15 | `/examination/Cardiac` | Very slow regular pulse with cannon waves in the neck; peripheries cool. | Pulso muy lento y regular, con ondas en cañón en el cuello; extremidades frías. |
| 16 | `/examination/General appearance` | Grey and cold; rouses to voice and drifts back. | Grisácea y fría; despierta al llamado verbal y vuelve a adormecerse. |
| 17 | `/investigations/pocus/result/lv` | Preserved contraction at a slow, regular ventricular rate independent of the atria | Contracción conservada a frecuencia ventricular lenta y regular independiente de las aurículas |
| 18 | `/investigations/pocus/result/ivc` | 1.7 cm; <50% inspiratory collapse | 1.7 cm; colapso inspiratorio <50% |

Cubiertos por el lote 0: `/history/allergies/0` (L0-33), `/examination/Respiratory` (L0-40), `/examination/Abdomen` (L0-38), `/examination/Neurological` (L0-46), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/chest_xray/result/report` (L0-26), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. **T-3:** no aparece «confused»; el pasaje `/history/neurological_symptoms/0` usa el sustantivo «confusion» → «confusión posterior», que T-3 no toca. **V-9:** «beta blocker» → «betabloqueador», como la clase de V-9; amlodipino, atorvastatina y digoxina son medicación habitual que el lector no reconoce como orden, en su nombre genérico.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☒ **APPROVE WHOLE CASE** — docente, 2026-10-08; versión aprobada `677c6278c0afd61dfc0e8c284473e88109b0d6e9e9222f5883555c60b338d3a7`. El sustantivo «confusión» queda como está: T-3 rige «confused» → «confundido» y no obliga a cambiar este sustantivo.

## bradycardia_bb_54f

- **Versión que se aprueba:** `45310f3bbe2d6151424d8955d4e2d24e8f88f72341670cf164955dbce8a009d9` (la del repositorio hoy; sin cambios)
- **Pasajes:** 37. Cubiertos por frases del lote 0, ya aprobadas: 21. **Propios, a revisar: 16.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 54-year-old woman is brought in after being found drowsy at home beside an empty blister pack. She is cold and very slow. | Una mujer de 54 años es traída tras ser encontrada somnolienta en su casa junto a un blíster vacío. Está fría y muy lenta. |
| 2 | `/history/chief_complaint/0` | Her partner says she was upset last night and he found her like this this morning. | Su pareja cuenta que anoche ella estaba alterada y que él la encontró así esta mañana. |
| 3 | `/history/associated_symptoms/0` | Her partner reports no chest pain and no breathlessness that she described. | Su pareja refiere que ella no describió dolor en el pecho ni falta de aire. |
| 4 | `/history/associated_symptoms/1` | She has vomited once since he found her. | Ha vomitado una vez desde que él la encontró. |
| 5 | `/history/medical_history/0` | Her partner reports high blood pressure and migraine; he knows of no heart disease. | Su pareja refiere presión alta y migraña; no sabe de ninguna enfermedad del corazón. |
| 6 | `/history/medications/0` | Her partner brought an empty blister pack of propranolol and says a full one was there yesterday. She also takes losartan. | Su pareja trajo un blíster vacío de propranolol y cuenta que ayer había uno lleno. También toma losartán. |
| 7 | `/history/onset/0` | She was last seen well around midnight and was found drowsy at about seven this morning. | La vieron bien por última vez cerca de la medianoche y la encontraron somnolienta alrededor de las siete de esta mañana. |
| 8 | `/history/risk_factors/0` | Her partner says there had been an argument and she had been low for weeks. | Su pareja cuenta que había habido una discusión y que ella llevaba semanas con el ánimo bajo. |
| 9 | `/history/neurological_symptoms/0` | There was no seizure and no head strike that he saw. | Él no vio ninguna convulsión ni golpe en la cabeza. |
| 10 | `/history/chest_pain/0` | Her partner reports no complaint of chest pain. | Su pareja refiere que ella no se quejó de dolor en el pecho. |
| 11 | `/history/breathing/0` | Her partner says the breathing has looked slow but regular. | Su pareja cuenta que la respiración se ha visto lenta pero regular. |
| 12 | `/history/oral_intake/0` | She has eaten nothing since last night and vomited once. | No ha comido nada desde anoche y vomitó una vez. |
| 13 | `/history/exposure/0` | He found no other empty packet and no alcohol. | No encontró ningún otro envase vacío ni alcohol. |
| 14 | `/examination/Cardiac` | Very slow regular pulse; peripheries cold with delayed refill; no murmur. | Pulso muy lento y regular; extremidades frías con llene enlentecido; sin soplos. |
| 15 | `/examination/Respiratory` | Slow regular breathing with clear breath sounds. | Respiración lenta y regular, con murmullo pulmonar sin ruidos agregados. |
| 16 | `/examination/General appearance` | Cold and pale; drowsy but rousable, with no rash. | Fría y pálida; somnolienta pero despertable, sin erupción. |

Cubiertos por el lote 0: `/history_source` (L0-32), `/history/allergies/0` (L0-33), `/examination/Abdomen` (L0-38), `/examination/Neurological` (L0-46), `/appearance_stable` (L0-47), `/investigations/pocus/result/lv` (L0-07), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/ivc` (L0-12), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/chest_xray/result/report` (L0-26), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. **V-9:** «propranolol» → «propranolol», como en V-9; losartán, medicación habitual en su nombre genérico. «Muy lenta» reproduce la misma ambigüedad del inglés («very slow»: el pulso o la respuesta); el examen («Pulso muy lento») y el monitor la resuelven.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☒ **APPROVE WHOLE CASE** — docente, 2026-10-08; versión aprobada `45310f3bbe2d6151424d8955d4e2d24e8f88f72341670cf164955dbce8a009d9`. Se conserva la redacción actual: «muy lenta» refleja la misma ambigüedad del inglés «very slow», y el examen físico identifica después el pulso como muy lento; no requiere revisión.

## bradycardia_hyperk_63m

- **Versión que se aprueba:** `89a347fa21123325e432c3b04970fd23b7218c8b4b41e2b5b0960510ad61b8e8` (la del repositorio hoy; sin cambios)
- **Pasajes:** 37. Cubiertos por frases del lote 0, ya aprobadas: 17. **Propios, a revisar: 20.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 63-year-old man on dialysis arrives weak and nauseated after missing sessions. He is cold, slow and short of breath on minimal effort. | Un hombre de 63 años en diálisis llega débil y con náuseas tras faltar a sesiones. Está frío, lento y con falta de aire al mínimo esfuerzo. |
| 2 | `/history/chief_complaint/0` | I have felt weak and sick and my legs will not hold me. | Me he sentido débil y con náuseas, y las piernas no me sostienen. |
| 3 | `/history/associated_symptoms/0` | I have been short of breath climbing the stairs since yesterday. | Desde ayer me falta el aire al subir las escaleras. |
| 4 | `/history/associated_symptoms/1` | My hands and feet feel numb and tingling. | Siento las manos y los pies adormecidos y con hormigueo. |
| 5 | `/history/medical_history/0` | I am on dialysis three times a week for kidney failure, and I have diabetes. | Me hago diálisis tres veces por semana por insuficiencia renal, y tengo diabetes. |
| 6 | `/history/medications/0` | I take calcium carbonate with meals, insulin, and a tablet for blood pressure. I was started on spironolactone a month ago. | Tomo carbonato de calcio con las comidas, me pongo insulina y tomo una pastilla para la presión. Hace un mes me indicaron espironolactona. |
| 7 | `/history/onset/0` | The weakness began two days ago and is worse today. | La debilidad empezó hace dos días y hoy está peor. |
| 8 | `/history/risk_factors/0` | I missed my last two dialysis sessions because the transport did not come. | Falté a mis dos últimas sesiones de diálisis porque no llegó el transporte. |
| 9 | `/history/oral_intake/0` | I have eaten and drunk as usual, including fruit and potatoes. | He comido y tomado líquidos como siempre, incluyendo fruta y papas. |
| 10 | `/history/urinary_symptoms/0` | I pass almost no urine; that has been true for years. | Casi no orino; eso es así desde hace años. |
| 11 | `/history/breathing/0` | The breathlessness is on effort, not at rest, and it is new since yesterday. | La falta de aire es al hacer esfuerzos, no en reposo, y empezó ayer. |
| 12 | `/history/chest_pain/0` | I have no chest pain. | No tengo dolor en el pecho. |
| 13 | `/history/neurological_symptoms/0` | The numbness in my hands and feet is new and there has been no weakness on one side. | El adormecimiento de las manos y los pies es nuevo y no he tenido debilidad de un solo lado. |
| 14 | `/examination/Cardiac` | Very slow regular pulse; peripheries cool with delayed refill. | Pulso muy lento y regular; extremidades frías con llene enlentecido. |
| 15 | `/examination/Respiratory` | Slightly increased rate with clear breath sounds; no crackles. | Frecuencia ligeramente aumentada, con murmullo pulmonar sin ruidos agregados; sin crépitos. |
| 16 | `/examination/Abdomen` | Soft and non-tender; no bladder palpable. | Blando e indoloro; sin globo vesical palpable. |
| 17 | `/examination/General appearance` | Pale and unwell with a dialysis fistula in the left forearm. | Pálido y con aspecto enfermo, con una fístula de diálisis en el antebrazo izquierdo. |
| 18 | `/examination/Neurological` | Awake and oriented; reduced power in both legs with reduced reflexes. | Vigil y orientado; fuerza disminuida en ambas extremidades inferiores, con reflejos disminuidos. |
| 19 | `/appearance_stable` | A dialysis fistula in the left forearm. | Una fístula de diálisis en el antebrazo izquierdo. |
| 20 | `/investigations/chest_xray/result/report` | Clear lung fields; no consolidation or pulmonary edema. | Campos pulmonares limpios; sin consolidación ni edema pulmonar. |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/investigations/pocus/result/lv` (L0-07), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/ivc` (L0-12), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. Ya dice «sin crépitos» (T-1). **V-9:** carbonato de calcio, insulina y espironolactona son medicación habitual, en su nombre genérico; «carbonato de calcio» (el quelante de fósforo que toma con las comidas) no se confunde con las sales de calcio de V-9 que sirven de antídoto («gluconato de calcio», «cloruro de calcio»): el español conserva la misma distinción que el inglés.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☒ **APPROVE WHOLE CASE** — docente, 2026-10-08; versión aprobada `89a347fa21123325e432c3b04970fd23b7218c8b4b41e2b5b0960510ad61b8e8`. Se conserva «carbonato de calcio» como medicación crónica del paciente, distinta de las sales de calcio que V-9 usa como tratamiento agudo.

## Resumen del lote R3B

| Caso | Propios | Cubiertos por el lote 0 | Fijos del corpus | Versión objetivo que se aprueba | Recomendación | Decisión docente |
|---|---|---|---|---|---|---|
| `bradycardia_avb3_78f` | 18 | 18 | 0 | `677c6278…` (sin cambios) | APPROVE | ☒ APPROVE |
| `bradycardia_bb_54f` | 16 | 21 | 0 | `45310f3b…` (sin cambios) | APPROVE | ☒ APPROVE |
| `bradycardia_hyperk_63m` | 20 | 17 | 0 | `89a347fa…` (sin cambios) | APPROVE | ☒ APPROVE |
| **Total** | **54** | **56** | **0** | | | |

Siguiente, según el orden docente: R4 (hipoglicemia y opioides). R4A, en `docs/revision/B5_RELATO_R4A.md`.
