# B-5 · Relato en español · Lote R2A: respiratorio (casos 1 a 3)

> **PARA REVISIÓN DOCENTE. Nada implementado.** Primera mitad del lote R2 de la revisión del relato
> (`docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md`). La docencia pidió R2 en dos mitades el 2026-10-07, como R1. Se
> sigue el orden canónico del banco (`clinical_cases.FAMILIES`: neumonía, edema pulmonar y asma; el mismo del
> manifiesto, `pilot_freeze.CASES`):
> - R2A: `pneumonia_46f`, `pneumonia_83m` y `pulmonary_edema_58m`;
> - R2B: `pulmonary_edema_75f`, `asthma_24f` y `asthma_49m`.
>
> El rótulo del lote en el §4 del diseño («asma, neumonía y edema pulmonar») sólo nombra las familias; no fija un
> orden. Se aprueba el caso entero, en la versión objetivo impresa (`case_text.version`). No se crea `approvals.json`
> ni se cambia `case_text/es`.
>
> 2026-10-07 · rama `clinical-encounter-v0.13` · relato leído de `case_text/es/pneumonia.json` y
> `case_text/es/pulmonary_edema.json` contra el inglés vigente de cada caso, sin cambiar nada.

**En una mirada**

- **Pasajes:** 3 casos y 103 pasajes. 50 están cubiertos por frases del lote 0, ya aprobadas; **53 son propios y se
  revisan** (18, 19 y 16).
- **Corpus de la validación externa:** `pneumonia_46f` está en él (C02). Sus 3 pasajes fijos (la presentación,
  `/history/chief_complaint/0` y `/history/onset/0`) van marcados 🔒. Ya están aprobados tal como están escritos (§8
  del diseño) y no cambian. Ningún término aplicado los toca.
- **Lo que no apareció:** desajustes de sentido, redacción clínicamente engañosa ni términos que choquen con X-1, la
  rúbrica o T-1 a T-3.
- **Términos ya aprobados que se aplican:**
  - T-1 «crépitos», en `/examination/Respiratory` de los 3 casos. En `pulmonary_edema_58m` cambia también la
    concordancia: «crepitaciones bilaterales difusas» pasa a «crépitos bilaterales difusos».
  - T-2 «defensa», en `/examination/Abdomen` de `pneumonia_46f`.
- **Regla de versión (docente, 2026-10-07):** la aprobación ata la versión objetivo presentada en la revisión, no la que está hoy en el repositorio. Al implementar, el español del repositorio tiene que dar exactamente ese hash antes de generar la entrada de aprobación; si da otro, se detiene y vuelve a revisión docente.
- **Recomendación:** **APPROVE** en los 3 casos.

## pneumonia_46f

- **Versión que se aprueba:** `d16cb3330fc87b73abb6d2e03eae76b428b4f61c0c33b9848cff27caa22977ca` (con T-1 y T-2 aplicadas; la del repositorio hoy es `7b5db0dd396d89dafb439790b0c61467738eff577318e5869c0726a83741f3a3`)
- **Pasajes:** 35. Cubiertos por frases del lote 0, ya aprobadas: 17. **Propios, a revisar: 18.**
- **Pasajes que fija el corpus de la validación externa:** 3 (`/presentation`, `/history/chief_complaint/0`, `/history/onset/0`), marcados 🔒. Ya están aprobados tal como están escritos (§8 del diseño, 2026-10-07); se muestran para leerlos con el caso y no se cambian en esta revisión. Un error clínicamente relevante se escalaría.

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` 🔒 | A 46-year-old woman presents with breathlessness and worsening weakness. She is awake and pauses between sentences. | Una mujer de 46 años consulta por disnea y debilidad progresiva. Está vigil y hace pausas entre frases. |
| 2 | `/history/chief_complaint/0` 🔒 | I feel short of breath and too weak to stand for long. | Me falta el aire y me siento demasiado débil para estar mucho rato de pie. |
| 3 | `/history/associated_symptoms/0` | I have had a cough with yellow sputum and shaking chills. | He tenido tos con expectoración amarilla y escalofríos con temblor. |
| 4 | `/history/associated_symptoms/1` | It hurts on the right when I take a deep breath. | Me duele en el lado derecho cuando respiro profundo. |
| 5 | `/history/medical_history/0` | I have rheumatoid arthritis; I have not previously needed oxygen. | Tengo artritis reumatoide; antes no había necesitado oxígeno. |
| 6 | `/history/medications/0` | I take methotrexate weekly and folic acid; no antibiotic has been started. | Tomo metotrexato semanal y ácido fólico; no me han iniciado ningún antibiótico. |
| 7 | `/history/onset/0` 🔒 | The cough began three days ago; the breathing and weakness worsened today. | La tos empezó hace tres días; hoy empeoraron la respiración y la debilidad. |
| 8 | `/history/risk_factors/0` | I receive methotrexate and have eaten and drunk little since yesterday. | Estoy en tratamiento con metotrexato y desde ayer he comido y tomado poco. |
| 9 | `/history/chest_pain/0` | The right-sided pain occurs with coughing or deep inspiration, not as a central pressure. | El dolor del lado derecho aparece al toser o al inspirar profundo, no como una opresión central. |
| 10 | `/history/breathing/0` | The shortness of breath is now present while sitting still. | Ahora me falta el aire estando sentada y quieta. |
| 11 | `/history/oral_intake/0` | I have had very little to eat or drink since yesterday. | Desde ayer he comido y tomado muy poco. |
| 12 | `/history/bleeding/0` | I have not coughed blood, vomited blood or passed black stools. | No he tosido sangre, no he vomitado sangre ni he tenido deposiciones negras. |
| 13 | `/examination/Respiratory` | Increased respiratory effort; focal crackles and bronchial breathing at the right base. | Esfuerzo respiratorio aumentado; crépitos focales y soplo tubario en la base derecha. *(T-1; antes: «Esfuerzo respiratorio aumentado; crepitaciones focales y soplo tubario en la base derecha.»)* |
| 14 | `/examination/Abdomen` | Soft; no focal tenderness or guarding. | Blando; sin dolor focal a la palpación ni defensa. *(T-2; antes: «Blando; sin dolor focal a la palpación ni resistencia muscular.»)* |
| 15 | `/examination/Neurological` | Awake, oriented and moving all limbs symmetrically. | Vigil, orientada y moviliza las cuatro extremidades en forma simétrica. |
| 16 | `/investigations/pocus/result/lungs` | Focal B-lines at the right base; no diffuse bilateral B-lines | Líneas B focales en la base derecha; sin líneas B difusas bilaterales |
| 17 | `/investigations/pocus/result/lung_consolidation` | Right basal subpleural consolidation with dynamic air bronchograms; no pleural effusion | Consolidación subpleural basal derecha con broncogramas aéreos dinámicos; sin derrame pleural |
| 18 | `/investigations/chest_xray/result/report` | Right lower-lobe air-space opacity. No pulmonary edema or pneumothorax. | Opacidad alveolar en el lóbulo inferior derecho. Sin edema pulmonar ni neumotórax. |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/history/urinary_symptoms/0` (L0-36), `/examination/Cardiac` (L0-42), `/investigations/pocus/result/lv` (L0-05), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/ivc` (L0-08), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. Se aplican T-1 en `/examination/Respiratory` y T-2 en `/examination/Abdomen`, ya aprobados. Los 3 pasajes 🔒 se leyeron con el caso: ningún error clínicamente relevante, así que quedan como están.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## pneumonia_83m

- **Versión que se aprueba:** `45a84e879f0a33e8167bf2de5937d23d7eb8ef4068439f77f162563640cd0c1b` (con T-1 aplicada; la del repositorio hoy es `0a65e473433ec383d8b29f77951bb03ed0b8350f568dac5076c0e7e5a67687c4`)
- **Pasajes:** 34. Cubiertos por frases del lote 0, ya aprobadas: 15. **Propios, a revisar: 19.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | An 83-year-old man is brought by his daughter after becoming unusually sleepy and nearly falling at home. The referral note suggests possible dehydration after poor intake; no diagnosis has been established. | Un hombre de 83 años es traído por su hija tras presentar una somnolencia inusual y estar a punto de caerse en casa. La nota de derivación sugiere una posible deshidratación tras una baja ingesta; no se ha establecido ningún diagnóstico. |
| 2 | `/history/chief_complaint/0` | His daughter reports that he has become sleepy and much less steady on his feet. | Su hija refiere que se ha puesto somnoliento y mucho menos estable de pie. |
| 3 | `/history/associated_symptoms/0` | His daughter noticed a new cough and reduced appetite over two days. | Su hija notó una tos nueva y disminución del apetito en los últimos dos días. |
| 4 | `/history/associated_symptoms/1` | He has been breathing faster today. | Hoy ha estado respirando más rápido. |
| 5 | `/history/medical_history/0` | His daughter reports hypertension and hearing impairment; he normally walks independently and converses clearly. | Su hija refiere hipertensión e hipoacusia; habitualmente camina sin ayuda y conversa con claridad. |
| 6 | `/history/medications/0` | His daughter lists amlodipine as his only regular prescription. | Su hija menciona amlodipino como su único medicamento recetado de uso habitual. |
| 7 | `/history/onset/0` | The cough began two days ago; sleepiness and near-fall occurred this morning. | La tos empezó hace dos días; la somnolencia y la casi caída ocurrieron esta mañana. |
| 8 | `/history/risk_factors/0` | He is independently mobile at baseline and has had poor oral intake during this illness. | En su estado basal se moviliza en forma independiente y durante este cuadro ha tenido una baja ingesta oral. |
| 9 | `/history/breathing/0` | His daughter says the faster breathing began before the near-fall. | Su hija cuenta que la respiración rápida empezó antes de la casi caída. |
| 10 | `/history/oral_intake/0` | His daughter says he has taken only small sips and little food today. | Su hija cuenta que hoy solo ha tomado pequeños sorbos y ha comido poco. |
| 11 | `/history/exposure/0` | There was no witnessed head strike, seizure or new sedative exposure. | No se presenció golpe en la cabeza, convulsión ni exposición a un sedante nuevo. |
| 12 | `/history/urinary_symptoms/0` | His daughter reports no preceding urinary complaints. | Su hija no refiere molestias urinarias previas. |
| 13 | `/examination/Respiratory` | Tachypnea with focal crackles and reduced air entry at the left base. | Taquipnea con crépitos focales y murmullo pulmonar disminuido en la base izquierda. *(T-1; antes: «Taquipnea con crepitaciones focales y murmullo pulmonar disminuido en la base izquierda.»)* |
| 14 | `/examination/Abdomen` | Soft and non-tender; no suprapubic tenderness. | Blando e indoloro; sin dolor suprapúbico a la palpación. |
| 15 | `/examination/Neurological` | Opens eyes to voice, follows simple commands slowly, and moves all limbs without an obvious focal deficit. | Abre los ojos al estímulo verbal, obedece órdenes simples con lentitud y moviliza las cuatro extremidades sin déficit focal evidente. |
| 16 | `/investigations/pocus/result/ivc` | 1.2 cm; >50% inspiratory collapse | 1.2 cm; colapso inspiratorio >50% |
| 17 | `/investigations/pocus/result/lungs` | Focal B-lines at the left base; no diffuse bilateral B-lines | Líneas B focales en la base izquierda; sin líneas B difusas bilaterales |
| 18 | `/investigations/pocus/result/lung_consolidation` | Left basal consolidation with air bronchograms; no pleural effusion | Consolidación basal izquierda con broncogramas aéreos; sin derrame pleural |
| 19 | `/investigations/chest_xray/result/report` | Left lower-lobe consolidation without diffuse edema. | Consolidación en el lóbulo inferior izquierdo sin edema difuso. |

Cubiertos por el lote 0: `/history_source` (L0-31), `/history/allergies/0` (L0-33), `/examination/Cardiac` (L0-42), `/investigations/pocus/result/lv` (L0-04), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. Se aplica T-1 en `/examination/Respiratory`, ya aprobado.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## pulmonary_edema_58m

- **Versión que se aprueba:** `dffcae29509ba47cbea4b30959c62e9093d6bce2df1099d724495a6238f804ae` (con T-1 aplicada; la del repositorio hoy es `a76b14a3a9ef944631ef01db471f7ca015860bbaa9261c3b6dd3a8632040c709`)
- **Pasajes:** 34. Cubiertos por frases del lote 0, ya aprobadas: 18. **Propios, a revisar: 16.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 58-year-old man arrives with rapidly worsening breathlessness. He remains upright and can speak only a few words at a time. | Un hombre de 58 años llega con disnea que empeora rápidamente. Se mantiene erguido y solo puede decir unas pocas palabras a la vez. |
| 2 | `/history/chief_complaint/0` | I suddenly cannot catch my breath, especially if I lie back. | De un momento a otro no me alcanza el aire, sobre todo si me recuesto. |
| 3 | `/history/associated_symptoms/0` | I woke up gasping and have been coughing up a small amount of frothy sputum. | Me desperté ahogándome y he estado tosiendo con un poco de expectoración espumosa. |
| 4 | `/history/associated_symptoms/1` | I have not had fever or a preceding productive cough. | No he tenido fiebre ni tos productiva previa. |
| 5 | `/history/medical_history/0` | I have high blood pressure; I have never been told I have asthma. | Tengo presión alta; nunca me han dicho que tenga asma. |
| 6 | `/history/medications/0` | I ran out of my usual antihypertensive medication four days ago. | Hace cuatro días se me acabó mi medicamento antihipertensivo habitual. |
| 7 | `/history/onset/0` | Severe breathlessness began about an hour ago and worsened rapidly. | La falta de aire intensa empezó hace alrededor de una hora y empeoró rápidamente. |
| 8 | `/history/risk_factors/0` | My blood pressure has been high and I have missed several days of treatment. | He tenido la presión alta y me he saltado varios días de tratamiento. |
| 9 | `/history/breathing/0` | Lying flat makes my breathing markedly worse. | Acostarme plano me empeora mucho la respiración. |
| 10 | `/history/chest_pain/0` | I feel chest tightness with the effort of breathing, without a separate persistent crushing pain. | Siento opresión en el pecho con el esfuerzo de respirar, sin un dolor aparte, aplastante y persistente. |
| 11 | `/history/oral_intake/0` | I have eaten and drunk normally. | He comido y tomado con normalidad. |
| 12 | `/examination/Respiratory` | Severe respiratory effort with widespread bilateral crackles and some expiratory wheeze. | Esfuerzo respiratorio severo, con crépitos bilaterales difusos y algunas sibilancias espiratorias. *(T-1; antes: «Esfuerzo respiratorio severo, con crepitaciones bilaterales difusas y algunas sibilancias espiratorias.»)* |
| 13 | `/examination/Neurological` | Awake, oriented and distressed; answers are brief because of breathlessness. | Vigil, orientado y angustiado; sus respuestas son breves por la disnea. |
| 14 | `/investigations/pocus/result/lv` | Moderately reduced global contraction | Contracción global moderadamente disminuida |
| 15 | `/investigations/pocus/result/ivc` | 2.4 cm; <50% inspiratory collapse | 2.4 cm; colapso inspiratorio <50% |
| 16 | `/investigations/chest_xray/result/report` | Bilateral perihilar air-space and interstitial opacities with vascular congestion. | Opacidades alveolares e intersticiales perihiliares bilaterales con congestión vascular. |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/history/urinary_symptoms/0` (L0-37), `/examination/Cardiac` (L0-41), `/examination/Abdomen` (L0-38), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-16), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. Se aplica T-1 en `/examination/Respiratory`, ya aprobado, con la concordancia: «crepitaciones bilaterales difusas» pasa a «crépitos bilaterales difusos». Así la llegada coincide con la frase del motor A-3, ya aprobada («Persisten crépitos bilaterales»).
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## Resumen del lote R2A

| Caso | Propios | Cubiertos por el lote 0 | Fijos del corpus | Versión objetivo que se aprueba | Recomendación | Decisión docente |
|---|---|---|---|---|---|---|
| `pneumonia_46f` | 18 | 17 | 3 🔒 | `d16cb333…` (con T-1 y T-2) | APPROVE | ☐ |
| `pneumonia_83m` | 19 | 15 | 0 | `45a84e87…` (con T-1) | APPROVE | ☐ |
| `pulmonary_edema_58m` | 16 | 18 | 0 | `dffcae29…` (con T-1) | APPROVE | ☐ |
| **Total** | **53** | **50** | **3** | | | |

Siguiente: R2B (`pulmonary_edema_75f`, `asthma_24f` y `asthma_49m`), después de la decisión docente sobre R2A.
