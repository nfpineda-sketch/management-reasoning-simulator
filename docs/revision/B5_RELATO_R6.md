# B-5 · Relato en español · Lote R6: urología y trauma

> **PARA REVISIÓN DOCENTE. Nada implementado. Preparado en la sesión autónoma del 2026-10-08, sin decisión docente.**
> Lote R6, en el orden canónico del banco (`clinical_cases.FAMILIES`; el mismo de `pilot_freeze.CASES`): `renal_colic_34m`, `obstructive_pyelonephritis_58f` y `trauma_limb_hemorrhage_27m`. `trauma_hemothorax_41m` también está en `case_text`, pero está **excluido del piloto de residentes** (F0-2, `pilot_freeze.CASES`: EXCLUDE) y queda en el sandbox docente: no se revisa aquí ni cuenta entre los 30; sus decisiones abiertas (C-34, D-44, F-59) siguen opcionales y no bloquean.
>
> Se aprueba el caso entero, en la versión objetivo impresa (`case_text.version`). No se crea `approvals.json` ni se
> cambia `case_text/es`. Relato leído de `case_text/es/renal_colic.json` y `case_text/es/trauma.json` contra el inglés vigente de cada caso, sin cambiar nada.

**En una mirada**

- **Pasajes:** 3 casos y 126 pasajes. 49 están cubiertos por frases del lote 0, ya aprobadas;
  **77 son propios y se revisan** (20, 21, 36).
- **Corpus de la validación externa:** `renal_colic_34m`, `trauma_limb_hemorrhage_27m` están en él; sus 6 pasajes fijos van marcados 🔒, ya están aprobados tal como están escritos y no cambian.
- **Términos ya aprobados:** T-1 a T-3 ya rigen en estos casos (comprobado: ninguno conserva «crepitaciones», «resistencia
  muscular» ni el adjetivo «confuso»), y P-1 no aplica. **Ninguna versión cambia:** la versión objetivo de cada caso es la
  del repositorio hoy.
- **Lo que no apareció:** desajustes de sentido, redacción clínicamente engañosa ni términos que choquen con X-1, la
  rúbrica, T-1 a T-3, P-1 o V-9.
- **Regla de versión (docente):** la aprobación ata la versión exacta revisada (la objetivo, si difiere de la del repositorio). Si al implementar el hash de un caso aprobado cambia, se detiene y vuelve a revisión docente.
- **Recomendación:** **APPROVE** en los 3 casos (categoría A: limpios).

## renal_colic_34m

- **Versión que se aprueba:** `ec65504955b7c09e9028358d829d377d4b7a96f8f3d9246b335d44e333f710fa` (la del repositorio hoy; sin cambios)
- **Pasajes:** 38. Cubiertos por frases del lote 0, ya aprobadas: 18. **Propios, a revisar: 20.**
- **Pasajes que fija el corpus de la validación externa:** 3 (`/presentation`, `/history/chief_complaint/0`, `/history/onset/0`), marcados 🔒. Ya están aprobados tal como están escritos (§8 del diseño, 2026-10-07); se muestran para leerlos con el caso y no se cambian en esta revisión. Un error clínicamente relevante se escalaría.

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` 🔒 | A 34-year-old man arrives with severe right-sided flank pain that comes in waves. He cannot stay still on the trolley. | Un hombre de 34 años llega con dolor intenso en el flanco derecho, que se presenta en oleadas. No logra quedarse quieto en la camilla. |
| 2 | `/history/chief_complaint/0` 🔒 | The pain grips my right side and goes down into my groin, in waves. | El dolor me aprieta el lado derecho y me baja hacia la ingle, en oleadas. |
| 3 | `/history/associated_symptoms/0` | I have vomited twice with the pain. | He vomitado dos veces con el dolor. |
| 4 | `/history/associated_symptoms/1` | There is no fever and no burning when I pass urine. | No tengo fiebre ni ardor al orinar. |
| 5 | `/history/medical_history/0` | I have never had a stone or a kidney problem and I take nothing regularly. | Nunca he tenido un cálculo ni ningún problema de riñón y no tomo nada de forma habitual. |
| 6 | `/history/medications/0` | I have taken paracetamol at home with no relief. No antibiotics. | He tomado paracetamol en casa, sin alivio. Ningún antibiótico. |
| 7 | `/history/onset/0` 🔒 | The pain started abruptly four hours ago and comes and goes every few minutes. | El dolor empezó de golpe hace cuatro horas y va y viene cada pocos minutos. |
| 8 | `/history/risk_factors/0` | I have been drinking little in the heat and I work outdoors. | He estado tomando poco líquido con el calor y trabajo al aire libre. |
| 9 | `/history/urinary_symptoms/0` | There is no burning, no frequency and no visible blood, but the urine looks concentrated. | No hay ardor, no orino más seguido y no hay sangre visible, pero la orina se ve concentrada. |
| 10 | `/history/exposure/0` | There has been no instrumentation, no catheter and no recent hospital stay. | No ha habido instrumentación, ni sonda, ni hospitalización reciente. |
| 11 | `/history/oral_intake/0` | I have been drinking very little water for several days. | Llevo varios días tomando muy poca agua. |
| 12 | `/history/breathing/0` | My breathing is normal; it is the pain that makes me restless. | Mi respiración está normal; es el dolor lo que me pone inquieto. |
| 13 | `/history/chest_pain/0` | There is no chest pain. | No hay dolor en el pecho. |
| 14 | `/examination/Cardiac` | Regular pulse at a normal rate; peripheries warm and well filled. | Pulso regular, de frecuencia normal; extremidades tibias y bien perfundidas. |
| 15 | `/examination/Abdomen` | Soft, with right renal angle tenderness; no guarding, rebound or palpable mass. | Blando, con dolor a la palpación del ángulo costovertebral derecho; sin defensa, rebote ni masa palpable. |
| 16 | `/examination/General appearance` | Restless and in evident pain, moving constantly; no rash and no pallor. | Inquieto y con dolor evidente, se mueve constantemente; sin erupción ni palidez. |
| 17 | `/examination/Neurological` | Awake, oriented and fully cooperative. | Vigil, orientado y completamente cooperador. |
| 18 | `/investigations/chest_xray/result/report` | Clear lung fields; no free subdiaphragmatic air. | Campos pulmonares limpios; sin aire libre subdiafragmático. |
| 19 | `/investigations/urinalysis/result/report` | Blood +++. No leukocyte esterase and no nitrite. Few red cells; no white cells or bacteria. | Sangre +++. Sin esterasa leucocitaria ni nitritos. Escasos hematíes; sin leucocitos ni bacterias. |
| 20 | `/investigations/renal_ultrasound/result/report` | Mild right pelvicalyceal dilatation with a 5 mm calculus at the vesicoureteric junction. The left kidney is normal. No perinephric collection. The bladder is not distended. | Dilatación pielocalicial derecha leve con un cálculo de 5 mm en la unión ureterovesical. El riñón izquierdo es normal. Sin colección perirrenal. La vejiga no está distendida. |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/examination/Respiratory` (L0-40), `/appearance_stable` (L0-47), `/investigations/pocus/result/lv` (L0-05), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/ivc` (L0-10), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. «Paracetamol» coincide con V-9; lo tomó en su casa (historia, no una orden de la sala), y «Ningún antibiótico». La ecografía renal es un estudio formal, distinto del POCUS. «Escasos hematíes» es término de laboratorio. Los 3 pasajes 🔒 se leyeron con el caso: ningún error clínicamente relevante.
- **Recomendación para el caso entero:** **APPROVE** (categoría A: limpio, sin cambios de texto).
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## obstructive_pyelonephritis_58f

- **Versión que se aprueba:** `3a98131bf83b59dd084ce0b1a2a9ad8f3d93d404372e81260254a1e9f5c50c65` (la del repositorio hoy; sin cambios)
- **Pasajes:** 37. Cubiertos por frases del lote 0, ya aprobadas: 16. **Propios, a revisar: 21.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 58-year-old woman arrives with left-sided flank pain and fever. She is flushed, shivering and slow to answer. | Una mujer de 58 años llega con dolor en el flanco izquierdo y fiebre. Está enrojecida, con escalofríos y lenta para responder. |
| 2 | `/history/chief_complaint/0` | My left side has ached for two days and today I started shaking with fever. | Me duele el lado izquierdo desde hace dos días y hoy empecé a tiritar de fiebre. |
| 3 | `/history/associated_symptoms/0` | I have been burning when I pass urine and going very often. | He tenido ardor al orinar y he estado yendo al baño muy seguido. |
| 4 | `/history/associated_symptoms/1` | I have vomited and I feel weak standing up. | He vomitado y me siento débil al ponerme de pie. |
| 5 | `/history/medical_history/0` | I have type 2 diabetes. I had a stone on the left three years ago that passed by itself. | Tengo diabetes tipo 2. Hace tres años tuve un cálculo en el lado izquierdo que salió solo. |
| 6 | `/history/medications/0` | I take metformin. I have taken no antibiotic for this. | Tomo metformina. No he tomado ningún antibiótico por esto. |
| 7 | `/history/onset/0` | The pain began two days ago and the fever and shaking started this morning. | El dolor empezó hace dos días, y la fiebre y los escalofríos comenzaron esta mañana. |
| 8 | `/history/risk_factors/0` | I have diabetes and a previous stone on the same side. | Tengo diabetes y un cálculo anterior en el mismo lado. |
| 9 | `/history/urinary_symptoms/0` | The urine burns, I go constantly and it has looked cloudy and smelt strong since yesterday. | Me arde al orinar, voy al baño a cada rato y desde ayer la orina se ve turbia y tiene un olor fuerte. |
| 10 | `/history/exposure/0` | I have had no catheter, no procedure and no recent hospital admission. | No he tenido sonda, ni ningún procedimiento, ni una hospitalización reciente. |
| 11 | `/history/oral_intake/0` | I have kept almost nothing down since yesterday. | Desde ayer casi no he podido retener nada. |
| 12 | `/history/breathing/0` | My breathing feels faster than usual but I am not short of breath. | Siento que respiro más rápido de lo normal, pero no me falta el aire. |
| 13 | `/history/bleeding/0` | I have not seen blood in the urine or anywhere else. | No he visto sangre en la orina ni en ninguna otra parte. |
| 14 | `/examination/Cardiac` | Rapid regular pulse; peripheries cool with delayed capillary refill. | Pulso rápido y regular; extremidades frías con llene capilar enlentecido. |
| 15 | `/examination/Respiratory` | Mildly increased rate with clear breath sounds. | Frecuencia levemente aumentada, con murmullo pulmonar sin ruidos agregados. |
| 16 | `/examination/Abdomen` | Marked left renal angle tenderness; the abdomen is otherwise soft without guarding. | Dolor marcado a la palpación del ángulo costovertebral izquierdo; por lo demás, el abdomen está blando, sin defensa. |
| 17 | `/examination/General appearance` | Flushed and shivering; looks unwell and answers slowly. | Enrojecida y con escalofríos; se ve enferma y responde con lentitud. |
| 18 | `/examination/Neurological` | Awake and oriented but slowed; moves all limbs normally. | Vigil y orientada, pero enlentecida; moviliza todas las extremidades con normalidad. |
| 19 | `/investigations/chest_xray/result/report` | Clear lung fields; no consolidation and no free subdiaphragmatic air. | Campos pulmonares limpios; sin consolidación y sin aire libre subdiafragmático. |
| 20 | `/investigations/urinalysis/result/report` | Leukocyte esterase +++ and nitrite positive. Blood ++. Numerous white cells and bacteria. | Esterasa leucocitaria +++ y nitritos positivos. Sangre ++. Abundantes leucocitos y bacterias. |
| 21 | `/investigations/renal_ultrasound/result/report` | Moderate left pelvicalyceal dilatation with a dilated proximal ureter and a 9 mm calculus at the pelviureteric junction. The right kidney is normal. No perinephric collection is demonstrated. The bladder is not distended. | Dilatación pielocalicial izquierda moderada con un uréter proximal dilatado y un cálculo de 9 mm en la unión pieloureteral. El riñón derecho es normal. No se demuestra colección perirrenal. La vejiga no está distendida. |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/investigations/pocus/result/lv` (L0-05), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/ivc` (L0-08), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. La obstrucción (cálculo de 9 mm en la unión pieloureteral, con uréter proximal dilatado) y la infección (esterasa +++, nitritos, leucocitos y bacterias) quedan claras y separadas. El relato no habla de descompresión ni de antibiótico dado («No he tomado ningún antibiótico por esto»). «Metformina», medicación habitual. «Sin defensa» (T-2).
- **Recomendación para el caso entero:** **APPROVE** (categoría A: limpio, sin cambios de texto).
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## trauma_limb_hemorrhage_27m

- **Versión que se aprueba:** `58187a00974b8795cd1da0d72e99da0e7c65162bfeeca1531da1db19c11536e7` (la del repositorio hoy; sin cambios)
- **Pasajes:** 51. Cubiertos por frases del lote 0, ya aprobadas: 15. **Propios, a revisar: 36.**
- **Pasajes que fija el corpus de la validación externa:** 3 (`/presentation`, `/history/chief_complaint/0`, `/history/onset/0`), marcados 🔒. Ya están aprobados tal como están escritos (§8 del diseño, 2026-10-07); se muestran para leerlos con el caso y no se cambian en esta revisión. Un error clínicamente relevante se escalaría.

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` 🔒 | A 27-year-old man arrives by ambulance after a machinery injury to the right thigh. A soaked dressing is in place and blood is running off the trolley. | Un hombre de 27 años llega en ambulancia tras una lesión por maquinaria en el muslo derecho. Tiene colocado un apósito empapado y la sangre escurre de la camilla. |
| 2 | `/history/chief_complaint/0` 🔒 | My leg is bleeding and I feel like I am going to pass out. | Me sangra la pierna y siento que me voy a desmayar. |
| 3 | `/history/associated_symptoms/0` | The dressing they put on has not stopped it. | El apósito que me pusieron no ha parado el sangrado. |
| 4 | `/history/associated_symptoms/1` | I feel cold and my hands are shaking. | Tengo frío y me tiemblan las manos. |
| 5 | `/history/medical_history/0` | I have no medical problems and I take nothing. | No tengo problemas de salud y no tomo nada. |
| 6 | `/history/medications/0` | I take no medication and no blood thinner. | No tomo medicamentos ni nada para diluir la sangre. |
| 7 | `/history/onset/0` 🔒 | The injury was about twenty minutes ago at work. | La lesión ocurrió hace unos veinte minutos, en el trabajo. |
| 8 | `/history/risk_factors/0` | There was no fall from height, no vehicle and no head strike; the machine caught the thigh. | No hubo caída de altura, ni vehículos involucrados, ni golpe en la cabeza; la máquina atrapó el muslo. |
| 9 | `/history/bleeding/0` | It has been bleeding steadily since it happened and the dressing is soaked through. | Ha sangrado de forma continua desde que ocurrió y el apósito está empapado por completo. |
| 10 | `/history/neurological_symptoms/0` | He did not lose consciousness and has no neck pain. | No perdió el conocimiento y no tiene dolor de cuello. |
| 11 | `/history/breathing/0` | His breathing is fast but he is not short of breath. | Respira rápido, pero no le falta el aire. |
| 12 | `/history/chest_pain/0` | There is no chest or abdominal pain. | No hay dolor en el pecho ni en el abdomen. |
| 13 | `/history/exposure/0` | No other wound has been found and he was fully exposed in the ambulance. | No se ha encontrado ninguna otra herida y fue expuesto por completo en la ambulancia. |
| 14 | `/examination/Cardiac` | Fast, thready pulse; peripheries cold with delayed capillary refill. | Pulso rápido y filiforme; extremidades frías con llene capilar enlentecido. |
| 15 | `/examination/Respiratory` | Increased rate with equal air entry and no chest wall injury. | Frecuencia aumentada, con murmullo pulmonar simétrico y sin lesión de la pared torácica. |
| 16 | `/examination/Abdomen` | Soft and non-tender; the pelvis is stable to gentle assessment. | Blando e indoloro; la pelvis es estable al evaluarla con suavidad. |
| 17 | `/examination/General appearance` | Pale, cold and sweating; a soaked dressing over a deep right thigh wound that is bleeding. | Pálido, frío y sudoroso; apósito empapado sobre una herida profunda del muslo derecho que está sangrando. |
| 18 | `/examination/Neurological` | Fully alert and oriented; moves all limbs. | Completamente alerta y orientado; moviliza todas las extremidades. |
| 19 | `/appearance_stable` | A deep right thigh wound. | Una herida profunda del muslo derecho. |
| 20 | `/appearance_while_bleeding` | A soaked dressing over a deep right thigh wound that is bleeding. | Apósito empapado sobre una herida profunda del muslo derecho que está sangrando. |
| 21 | `/investigations/pocus/result/lv` | Vigorous contraction with near-obliteration in systole | Contracción vigorosa con obliteración casi completa en sístole |
| 22 | `/investigations/pocus/result/ivc` | 0.7 cm; complete inspiratory collapse | 0.7 cm; colapso inspiratorio completo |
| 23 | `/investigations/chest_xray/result/report` | No pneumothorax, haemothorax or mediastinal widening. | Sin neumotórax, hemotórax ni ensanchamiento mediastínico. |
| 24 | `/investigations/efast/result/ruq_morison` | No free fluid in the hepatorenal recess | Sin líquido libre en el receso hepatorrenal |
| 25 | `/investigations/efast/result/ruq_subdiaphragmatic` | No free fluid above the liver | Sin líquido libre por encima del hígado |
| 26 | `/investigations/efast/result/ruq_pleural` | No fluid in the right pleural recess | Sin líquido en el receso pleural derecho |
| 27 | `/investigations/efast/result/luq_splenorenal` | No free fluid in the splenorenal recess | Sin líquido libre en el receso esplenorrenal |
| 28 | `/investigations/efast/result/luq_subdiaphragmatic` | No free fluid above the spleen | Sin líquido libre por encima del bazo |
| 29 | `/investigations/efast/result/luq_pleural` | No fluid in the left pleural recess | Sin líquido en el receso pleural izquierdo |
| 30 | `/investigations/efast/result/suprapubic_longitudinal` | No free fluid behind or around the bladder | Sin líquido libre retrovesical ni perivesical |
| 31 | `/investigations/efast/result/suprapubic_transverse` | No free fluid behind or around the bladder | Sin líquido libre retrovesical ni perivesical |
| 32 | `/investigations/efast/result/pericardium` | No pericardial fluid | Sin líquido pericárdico |
| 33 | `/investigations/efast/result/lung_sliding_right` | Sliding present | Deslizamiento presente |
| 34 | `/investigations/efast/result/lung_sliding_left` | Sliding present | Deslizamiento presente |
| 35 | `/investigations/efast/result/lung_m_mode` | Seashore sign bilaterally; comet tails seen | Signo de la playa bilateral; se observan colas de cometa |
| 36 | `/investigations/pelvis_xray/result/report` | No pelvic fracture and no diastasis of the symphysis or the sacroiliac joints. | Sin fractura pélvica y sin diástasis de la sínfisis ni de las articulaciones sacroilíacas. |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. El apósito prehospitalario es real en el caso («El apósito que me pusieron no ha parado el sangrado»): no se lee como control del sangrado. Los 12 resultados del E-FAST, negativos, y la hemorragia externa activa son coherentes: la fuente es el muslo. El relato no habla de paro ni de torniquete; A-1, K-7 y K-E4 son frases del motor, sin texto en común. Los 3 pasajes 🔒 se leyeron con el caso: ningún error clínicamente relevante.
- **Recomendación para el caso entero:** **APPROVE** (categoría A: limpio, sin cambios de texto).
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## Resumen del lote R6

| Caso | Propios | Cubiertos por el lote 0 | Fijos del corpus | Versión objetivo que se aprueba | Recomendación | Decisión docente |
|---|---|---|---|---|---|---|
| `renal_colic_34m` | 20 | 18 | 3 🔒 | `ec655049…` (sin cambios) | APPROVE | ☐ |
| `obstructive_pyelonephritis_58f` | 21 | 16 | 0 | `3a98131b…` (sin cambios) | APPROVE | ☐ |
| `trauma_limb_hemorrhage_27m` | 36 | 15 | 3 🔒 | `58187a00…` (sin cambios) | APPROVE | ☐ |
| **Total** | **77** | **49** | **6** | | | |
