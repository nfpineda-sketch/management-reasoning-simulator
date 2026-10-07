# B-5 · Relato en español · Lote R1B: síndrome coronario agudo (casos 4 a 6)

> **PARA REVISIÓN DOCENTE. Nada implementado.** Segunda mitad del lote R1 de la revisión del relato
> (`docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md`), en el orden canónico del banco (`clinical_cases.FAMILIES["acs"]`):
> `acs_52m_de_winter`, `acs_48m_wellens` y `acs_70f_left_main`. Se aprueba el caso entero, en la versión objetivo impresa
> (`case_text.version`). No se crea `approvals.json` ni se cambia `case_text/es`.
>
> 2026-10-07 · rama `clinical-encounter-v0.13` · relato leído de `case_text/es/acs.json` contra el inglés vigente de
> cada caso, sin cambiar nada.

**En una mirada**

- **Pasajes:** 3 casos y 105 pasajes. 61 están cubiertos por frases del lote 0, ya aprobadas; **44 son propios y se
  revisan** (14, 15 y 15).
- **Corpus de la validación externa:** ninguno de los 3 casos está en él, así que no hay pasajes fijos en este lote.
- **Lo que no apareció:** desajustes de sentido, redacción clínicamente engañosa ni términos que choquen con X-1, la
  rúbrica o T-1 a T-3.
- **Término ya aprobado que se aplica:** T-1 «crépitos», en un pasaje de `acs_52m_de_winter` y en uno de
  `acs_70f_left_main`. En este último cambia también la concordancia: «crepitaciones basales dispersas» pasa a
  «crépitos basales dispersos».
- **Regla de versión (docente, 2026-10-07):** la aprobación ata la versión objetivo presentada en la revisión, no la que está hoy en el repositorio. Al implementar, el español del repositorio tiene que dar exactamente ese hash antes de generar la entrada de aprobación; si da otro, se detiene y vuelve a revisión docente.
- **Recomendación:** **APPROVE** en los 3 casos.

## acs_52m_de_winter

- **Versión que se aprueba:** `daf766118b4ae254ae6fa4261bebb40a96eb3ce6d3a4d92f3048d0f5acdc4056` (con T-1 aplicada; la del repositorio hoy es `b881e9ab322e19179fc39e018a5a6e1c9dfbfd4129898151a72d9fefeaef52db`)
- **Pasajes:** 35. Cubiertos por frases del lote 0, ya aprobadas: 21. **Propios, a revisar: 14.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 52-year-old man arrives with 40 minutes of heavy central chest pain and sweating. | Un hombre de 52 años llega con dolor torácico central tipo peso y sudoración, de 40 minutos de evolución. |
| 2 | `/history/chief_complaint/0` | My chest feels crushed and I am sweating. | Siento como si me aplastaran el pecho y estoy sudando. |
| 3 | `/history/associated_symptoms/0` | I feel short of breath and nauseated. | Me falta el aire y tengo náuseas. |
| 4 | `/history/associated_symptoms/1` | I have no cough, fever or pleuritic pain. | No tengo tos, fiebre ni dolor pleurítico. |
| 5 | `/history/medical_history/0` | I have high cholesterol; I have never had a heart attack. | Tengo colesterol alto; nunca he tenido un infarto. |
| 6 | `/history/medications/0` | I take atorvastatin only; I have not taken an antiplatelet today. | Solo tomo atorvastatina; hoy no he tomado ningún antiagregante plaquetario. |
| 7 | `/history/onset/0` | The pain began 40 minutes ago at rest and has been constant since. | El dolor empezó hace 40 minutos, en reposo, y ha sido constante desde entonces. |
| 8 | `/history/risk_factors/0` | I smoke and my brother had a stent at 55. | Fumo y a mi hermano le pusieron un stent a los 55. |
| 9 | `/history/chest_pain/0` | The pain is central, heavy, and radiates to both arms; it is not positional. | El dolor es central, se siente como un peso y se me irradia a los dos brazos; no cambia con la posición. |
| 10 | `/history/breathing/0` | I am mildly short of breath with the pain. | Me falta un poco el aire con el dolor. |
| 11 | `/examination/Cardiac` | Regular pulse; no new murmur; skin is cool and damp. | Pulso regular; sin soplo nuevo; piel fría y húmeda. |
| 12 | `/examination/Respiratory` | Mildly increased effort; no crackles or wheeze. | Esfuerzo respiratorio levemente aumentado; sin crépitos ni sibilancias. *(T-1; antes: «Esfuerzo respiratorio levemente aumentado; sin crepitaciones ni sibilancias.»)* |
| 13 | `/investigations/pocus/result/lv` | Akinesis of the anterior wall and apex; the inferior wall contracts normally | Acinesia de la pared anterior y del ápex; la pared inferior se contrae normalmente |
| 14 | `/investigations/pocus/result/ivc` | 1.5 cm; about 50% inspiratory collapse | 1.5 cm; colapso inspiratorio de aproximadamente 50% |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/history/bleeding/0` (L0-34), `/examination/Abdomen` (L0-38), `/examination/Neurological` (L0-45), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/chest_xray/result/report` (L0-24), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21), `/investigations/ecg_right/result/report` (L0-29), `/investigations/ecg_posterior/result/report` (L0-28).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. Se aplica T-1 en `/examination/Respiratory`, ya aprobado.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## acs_48m_wellens

- **Versión que se aprueba:** `13a569872e3a88cf1f01537ee50544f5057cc21942bd10d4e3b3ba03681ab04d` (la del repositorio hoy; sin cambios)
- **Pasajes:** 35. Cubiertos por frases del lote 0, ya aprobadas: 20. **Propios, a revisar: 15.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 48-year-old man is pain-free now after three episodes of chest pressure today, the last one an hour ago. | Un hombre de 48 años se encuentra ahora sin dolor, tras presentar hoy tres episodios de opresión en el pecho, el último hace una hora. |
| 2 | `/history/chief_complaint/0` | I had three episodes of chest pressure today; right now I feel fine. | Hoy tuve tres episodios de opresión en el pecho; en este momento me siento bien. |
| 3 | `/history/associated_symptoms/0` | Each episode came with sweating and settled on its own. | Cada episodio vino acompañado de sudoración y se me pasó solo. |
| 4 | `/history/associated_symptoms/1` | I have no fever, cough or pleuritic pain. | No tengo fiebre, tos ni dolor pleurítico. |
| 5 | `/history/medical_history/0` | I have no diagnosed heart disease and take no regular medicines. | No tengo ninguna enfermedad del corazón diagnosticada y no tomo medicamentos de forma habitual. |
| 6 | `/history/medications/0` | I take no regular medicines and have not taken an antiplatelet. | No tomo medicamentos de forma habitual y no he tomado ningún antiagregante plaquetario. |
| 7 | `/history/onset/0` | The episodes began this morning; the last one ended an hour ago and lasted twenty minutes. | Los episodios empezaron esta mañana; el último terminó hace una hora y duró veinte minutos. |
| 8 | `/history/risk_factors/0` | I smoke twenty cigarettes a day. | Fumo veinte cigarrillos al día. |
| 9 | `/history/chest_pain/0` | During the episodes the pressure was central and heavy; between them I have no pain at all. | Durante los episodios, la opresión era central y se sentía como un peso; entre un episodio y otro no tengo nada de dolor. |
| 10 | `/history/breathing/0` | My breathing is normal now. | Ahora respiro normalmente. |
| 11 | `/examination/Cardiac` | Regular pulse at a normal rate; no murmur; skin warm and dry. | Pulso regular, de frecuencia normal; sin soplos; piel tibia y seca. |
| 12 | `/examination/Respiratory` | Normal effort; lungs clear. | Esfuerzo respiratorio normal; pulmones limpios. |
| 13 | `/examination/Neurological` | Alert, oriented and comfortable. | Alerta, orientado y cómodo. |
| 14 | `/investigations/pocus/result/lv` | Normal wall motion in every segment at rest | Motilidad parietal normal en todos los segmentos en reposo |
| 15 | `/investigations/pocus/result/ivc` | 1.5 cm; >50% inspiratory collapse | 1.5 cm; colapso inspiratorio >50% |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/history/bleeding/0` (L0-34), `/examination/Abdomen` (L0-38), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/chest_xray/result/report` (L0-27), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21), `/investigations/ecg_right/result/report` (L0-29), `/investigations/ecg_posterior/result/report` (L0-28).

- **Observaciones:** ninguna de sentido, clínica ni de terminología.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## acs_70f_left_main

- **Versión que se aprueba:** `c94b56ee409f799557c53b017e5144c4c076549426d9a75aaec6cd314bddb552` (con T-1 aplicada; la del repositorio hoy es `1bd4171c534ae4414be5d4a037d016d1c3b4235ec3ff376d0b78a0b1acaf39c9`)
- **Pasajes:** 35. Cubiertos por frases del lote 0, ya aprobadas: 20. **Propios, a revisar: 15.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 70-year-old woman presents with chest pressure, breathlessness and sweating that began an hour ago. | Una mujer de 70 años consulta por opresión en el pecho, disnea y sudoración que comenzaron hace una hora. |
| 2 | `/history/chief_complaint/0` | My chest is tight and I cannot catch my breath. | Siento el pecho apretado y no me alcanza el aire. |
| 3 | `/history/associated_symptoms/0` | I feel sick and very sweaty. | Tengo náuseas y estoy muy sudorosa. |
| 4 | `/history/medical_history/0` | I have diabetes, high blood pressure and kidney disease; I have had no heart attack. | Tengo diabetes, presión alta y enfermedad renal; no he tenido ningún infarto. |
| 5 | `/history/medications/0` | I take metformin, losartan and a statin; I have not taken an antiplatelet today. | Tomo metformina, losartán y una estatina; hoy no he tomado ningún antiagregante plaquetario. |
| 6 | `/history/onset/0` | The tightness and breathlessness began an hour ago at rest. | La opresión y la falta de aire empezaron hace una hora, en reposo. |
| 7 | `/history/risk_factors/0` | I have diabetes, high blood pressure and kidney disease. | Tengo diabetes, presión alta y enfermedad renal. |
| 8 | `/history/chest_pain/0` | The tightness is central and constant, with sweating; it does not change with breathing. | La opresión es central y constante, con sudoración; no cambia al respirar. |
| 9 | `/history/breathing/0` | The breathlessness came with the chest tightness. | La falta de aire apareció junto con la opresión en el pecho. |
| 10 | `/examination/Cardiac` | Regular tachycardia; no new murmur; extremities are cool. | Taquicardia regular; sin soplo nuevo; extremidades frías. |
| 11 | `/examination/Respiratory` | Mildly increased effort; scattered basal crackles. | Esfuerzo respiratorio levemente aumentado; crépitos basales dispersos. *(T-1; antes: «Esfuerzo respiratorio levemente aumentado; crepitaciones basales dispersas.»)* |
| 12 | `/investigations/pocus/result/lv` | Globally mildly reduced contraction without a single focal defect | Contracción globalmente levemente disminuida sin un defecto focal único |
| 13 | `/investigations/pocus/result/ivc` | 1.9 cm; about 50% inspiratory collapse | 1.9 cm; colapso inspiratorio de aproximadamente 50% |
| 14 | `/investigations/pocus/result/lungs` | Scattered B-lines at both bases; no diffuse B-line pattern | Líneas B dispersas en ambas bases; sin patrón difuso de líneas B |
| 15 | `/investigations/chest_xray/result/report` | Mild pulmonary congestion without focal consolidation. | Congestión pulmonar leve sin consolidación focal. |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/associated_symptoms/1` (L0-35), `/history/allergies/0` (L0-33), `/history/bleeding/0` (L0-34), `/examination/Abdomen` (L0-38), `/examination/Neurological` (L0-45), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21), `/investigations/ecg_right/result/report` (L0-29), `/investigations/ecg_posterior/result/report` (L0-28).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. Se aplica T-1 en `/examination/Respiratory`, ya aprobado.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## Resumen del lote R1B

| Caso | Propios | Cubiertos por el lote 0 | Versión objetivo que se aprueba | Recomendación | Decisión docente |
|---|---|---|---|---|---|
| `acs_52m_de_winter` | 14 | 21 | `daf76611…` (con T-1) | APPROVE | ☐ |
| `acs_48m_wellens` | 15 | 20 | `13a56987…` (sin cambios) | APPROVE | ☐ |
| `acs_70f_left_main` | 15 | 20 | `c94b56ee…` (con T-1) | APPROVE | ☐ |
| **Total** | **44** | **61** | | | |

Siguiente, según el orden docente: R2 (respiratorio), después de la decisión docente sobre R1B.
