# B-5 · Relato en español · Lote R1A: síndrome coronario agudo (casos 1 a 3)

> **DECIDIDO por la docencia el 2026-10-07: los 3 casos, APPROVE WHOLE CASE. Nada implementado.** Primera mitad
> del lote R1 de la revisión del relato
> (`docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md`). La docencia dividió R1 en R1A y R1B el 2026-10-07. Se sigue el
> orden canónico del banco (`clinical_cases.FAMILIES["acs"]`, el mismo del manifiesto y de `case_text/es/acs.json`):
> - R1A: `acs_54m_inferior`, `acs_66f_nonst` y `acs_61m_posterior`;
> - R1B: `acs_52m_de_winter`, `acs_48m_wellens` y `acs_70f_left_main`.
>
> Se aprueba el caso entero, en la versión impresa (`case_text.version`). No se crea `approvals.json` ni se cambia
> `case_text/es`.
>
> 2026-10-07 · rama `clinical-encounter-v0.13` · relato leído de `case_text/es/acs.json` contra el inglés vigente de
> cada caso, sin cambiar nada.

**En una mirada**

- **Decidido (docente, 2026-10-07):** 3 de 3 casos aprobados, cada uno en su versión objetivo. Regla de versión: la aprobación ata la versión objetivo presentada en la revisión, no la que está hoy en el repositorio. Al implementar, el español del repositorio tiene que dar exactamente ese hash antes de generar la entrada de aprobación; si da otro, se detiene y vuelve a revisión docente.
- **Pasajes:** 3 casos y 105 pasajes. 56 están cubiertos por frases del lote 0, ya aprobadas; **49 son propios y se
  revisan** (18, 16 y 15).
- **Corpus de la validación externa:** ninguno de los 3 casos está en él, así que no hay pasajes fijos en este lote.
- **Lo que no apareció:** desajustes de sentido, redacción clínicamente engañosa, términos que choquen con X-1, la
  rúbrica o T-1 a T-3, o redacción que cambie la interpretación.
- **Términos ya aprobados que se aplican:**
  - T-2 «defensa» en `acs_54m_inferior` y T-1 «crépitos» en `acs_66f_nonst`, un pasaje cada uno;
  - la versión que se aprueba de esos dos casos es la del contenido con el término aplicado;
  - `case_text/es` cambia al implementar, y su hash tiene que coincidir entonces con el aprobado.
- **Recomendación:** **APPROVE** en los 3 casos.

## acs_54m_inferior

- **Versión que se aprueba:** `e1afcda52d3e3fab6853c2b1bd44bf07c4e6ef04296cdde9f7fe87723a48076a` (con T-2 aplicada; la del repositorio hoy es `8426f7ca71d9c4cfc8edb49e43944a53e5776f87357a652ab1cfbe2661ceac14`)
- **Pasajes:** 35. Cubiertos por frases del lote 0, ya aprobadas: 17. **Propios, a revisar: 18.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 54-year-old man presents with persistent upper-abdominal discomfort and nausea. He looks uncomfortable and sweaty. The triage note records 'indigestion?' as an unconfirmed impression. | Un hombre de 54 años consulta por molestia persistente en la parte alta del abdomen y náuseas. Se ve incómodo y sudoroso. La nota de triage registra '¿indigestión?' como impresión no confirmada. |
| 2 | `/history/chief_complaint/0` | I have a heavy discomfort high in my abdomen that will not go away. | Tengo una molestia como de peso en la parte alta del abdomen que no se me pasa. |
| 3 | `/history/associated_symptoms/0` | The discomfort sometimes extends into my chest and jaw. | A veces la molestia se me extiende al pecho y a la mandíbula. |
| 4 | `/history/associated_symptoms/1` | I feel nauseated and have broken into a sweat. | Tengo náuseas y empecé a sudar. |
| 5 | `/history/medical_history/0` | I have high blood pressure and high cholesterol, but no previous heart attack. | Tengo presión alta y colesterol alto, pero no he tenido ningún infarto antes. |
| 6 | `/history/medications/0` | I take losartan and atorvastatin; I have not taken an antiplatelet today. | Tomo losartán y atorvastatina; hoy no he tomado ningún antiagregante plaquetario. |
| 7 | `/history/onset/0` | The discomfort started 75 minutes ago while walking and has persisted at rest. | La molestia empezó hace 75 minutos mientras caminaba y ha persistido en reposo. |
| 8 | `/history/risk_factors/0` | I smoke, and my father had coronary disease in his fifties. | Fumo, y mi papá tuvo enfermedad coronaria cuando tenía cincuenta y tantos años. |
| 9 | `/history/chest_pain/0` | The upper-abdominal heaviness extends behind the sternum and into my jaw; it is not reproduced by touching my chest. | La pesadez en la parte alta del abdomen se me extiende por detrás del esternón y hasta la mandíbula; no se reproduce al tocarme el pecho. |
| 10 | `/history/breathing/0` | I feel mildly short of breath, without pleuritic pain. | Me falta un poco el aire, sin dolor pleurítico. |
| 11 | `/history/bleeding/0` | I have no hematemesis or black stool. | No tengo hematemesis ni deposiciones negras. |
| 12 | `/examination/Cardiac` | Slow regular pulse; no new murmur heard. | Pulso lento y regular; no se ausculta soplo nuevo. |
| 13 | `/examination/Respiratory` | No increased respiratory effort; lungs are clear on auscultation. | Sin aumento del esfuerzo respiratorio; pulmones limpios a la auscultación. |
| 14 | `/examination/Abdomen` | Soft, with no focal tenderness or guarding despite the reported discomfort. | Blando, sin dolor focal a la palpación ni defensa, a pesar de la molestia referida. *(T-2; antes: «Blando, sin dolor focal a la palpación ni resistencia muscular, a pesar de la molestia referida.»)* |
| 15 | `/examination/Neurological` | Awake, oriented and moving all limbs normally. | Vigil, orientado y moviliza las cuatro extremidades con normalidad. |
| 16 | `/investigations/pocus/result/lv` | Reduced contraction of the inferior wall; the other walls contract normally | Contracción disminuida de la pared inferior; las demás paredes se contraen normalmente |
| 17 | `/investigations/pocus/result/rv` | Smaller than the LV; RV free wall contracts normally; no septal flattening (no D-sign); no McConnell sign | Menor que el VI; la pared libre del VD se contrae normalmente; sin aplanamiento septal (sin signo D); sin signo de McConnell |
| 18 | `/investigations/pocus/result/ivc` | 1.8 cm; about 50% inspiratory collapse | 1.8 cm; colapso inspiratorio de aproximadamente 50% |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/chest_xray/result/report` (L0-24), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21), `/investigations/ecg_right/result/report` (L0-29), `/investigations/ecg_posterior/result/report` (L0-28).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. Se aplica T-2 en `/examination/Abdomen`, ya aprobado.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☒ **APPROVE WHOLE CASE** — docente, 2026-10-07; versión aprobada `e1afcda52d3e3fab6853c2b1bd44bf07c4e6ef04296cdde9f7fe87723a48076a`. Incluye T-2 (guarding → defensa).

## acs_66f_nonst

- **Versión que se aprueba:** `d64dc72663d6d94f4b919ab8529e2314263cbb010d4de66e52738a1221eb95c1` (con T-1 aplicada; la del repositorio hoy es `7e013ae208a4b34d3b2d61f2994c6285fc3a89714e29f61dac428a894026c7da`)
- **Pasajes:** 35. Cubiertos por frases del lote 0, ya aprobadas: 19. **Propios, a revisar: 16.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 66-year-old woman reports new breathlessness and a persistent heavy sensation across her upper chest. | Una mujer de 66 años refiere disnea nueva y una sensación persistente de peso a lo ancho de la parte alta del pecho. |
| 2 | `/history/chief_complaint/0` | I feel unusually short of breath and there is a weight across my upper chest. | Me falta el aire de una forma poco habitual y tengo un peso a lo ancho de la parte alta del pecho. |
| 3 | `/history/associated_symptoms/0` | I have been nauseated and more tired than usual. | He tenido náuseas y he estado más cansada de lo habitual. |
| 4 | `/history/associated_symptoms/1` | I have not had fever, sputum or pain on deep inspiration. | No he tenido fiebre, expectoración ni dolor al inspirar profundo. |
| 5 | `/history/medical_history/0` | I have diabetes and high blood pressure; these symptoms are new for me. | Tengo diabetes y presión alta; estos síntomas son nuevos para mí. |
| 6 | `/history/medications/0` | I take metformin, losartan and a statin. | Tomo metformina, losartán y una estatina. |
| 7 | `/history/onset/0` | The symptoms started about three hours ago during light activity and have not fully resolved. | Los síntomas empezaron hace unas tres horas durante una actividad liviana y no se me han pasado del todo. |
| 8 | `/history/risk_factors/0` | I have diabetes and hypertension; my sister has coronary disease. | Tengo diabetes e hipertensión; mi hermana tiene enfermedad coronaria. |
| 9 | `/history/chest_pain/0` | The heaviness is persistent, not positional and not reproduced by pressing on the chest. | La pesadez es persistente, no cambia con la posición y no se reproduce al presionar el pecho. |
| 10 | `/history/breathing/0` | I become breathless with much less activity than usual. | Me falta el aire con mucha menos actividad de lo habitual. |
| 11 | `/history/bleeding/0` | I have no recent bleeding or black stools. | No he tenido sangrado reciente ni deposiciones negras. |
| 12 | `/examination/Cardiac` | Regular mildly rapid pulse; no new murmur. | Pulso regular, levemente rápido; sin soplo nuevo. |
| 13 | `/examination/Respiratory` | Mildly increased effort; no focal crackles or wheeze. | Esfuerzo respiratorio levemente aumentado; sin crépitos focales ni sibilancias. *(T-1; antes: «Esfuerzo respiratorio levemente aumentado; sin crepitaciones focales ni sibilancias.»)* |
| 14 | `/examination/Neurological` | Alert, oriented and conversant. | Alerta, orientada y capaz de conversar. |
| 15 | `/investigations/pocus/result/lv` | Mild hypokinesis of the inferolateral wall; global contraction otherwise preserved | Hipocinesia leve de la pared inferolateral; contracción global por lo demás conservada |
| 16 | `/investigations/chest_xray/result/report` | No acute focal pulmonary abnormality. | Sin alteraciones pulmonares focales agudas. |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/examination/Abdomen` (L0-38), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/ivc` (L0-11), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21), `/investigations/ecg_right/result/report` (L0-29), `/investigations/ecg_posterior/result/report` (L0-28).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. Se aplica T-1 en `/examination/Respiratory`, ya aprobado.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☒ **APPROVE WHOLE CASE** — docente, 2026-10-07; versión aprobada `d64dc72663d6d94f4b919ab8529e2314263cbb010d4de66e52738a1221eb95c1`. Incluye T-1 (crackles → crépitos).

## acs_61m_posterior

- **Versión que se aprueba:** `a6311c114d9c4d8cd1c444fd724a0a62cced41d7ccfbb2392ce25773618d1890` (la del repositorio hoy; sin cambios)
- **Pasajes:** 35. Cubiertos por frases del lote 0, ya aprobadas: 20. **Propios, a revisar: 15.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 61-year-old man reports two hours of pressure across his chest and back, with nausea. | Un hombre de 61 años refiere opresión que abarca el pecho y la espalda, de dos horas de evolución, con náuseas. |
| 2 | `/history/chief_complaint/0` | There is a pressure in my chest that goes through to my back. | Tengo una opresión en el pecho que me atraviesa hasta la espalda. |
| 3 | `/history/associated_symptoms/0` | I feel sick and clammy. | Tengo náuseas y sudor frío. |
| 4 | `/history/associated_symptoms/1` | I have no fever, cough or pain on breathing. | No tengo fiebre, tos ni dolor al respirar. |
| 5 | `/history/medical_history/0` | I have high blood pressure and I stopped smoking five years ago; I have had no heart attack. | Tengo presión alta y dejé de fumar hace cinco años; no he tenido ningún infarto. |
| 6 | `/history/medications/0` | I take amlodipine; I have not taken an antiplatelet today. | Tomo amlodipino; hoy no he tomado ningún antiagregante plaquetario. |
| 7 | `/history/onset/0` | The pressure started two hours ago while I was at rest and has not eased. | La opresión empezó hace dos horas, mientras estaba en reposo, y no ha cedido. |
| 8 | `/history/risk_factors/0` | I have high blood pressure and a smoking history. | Tengo presión alta y he sido fumador. |
| 9 | `/history/chest_pain/0` | The pressure is central and goes through to the back; it does not change with breathing or position. | La opresión es central y me atraviesa hasta la espalda; no cambia al respirar ni con la posición. |
| 10 | `/history/breathing/0` | I am not especially short of breath. | No tengo mucha falta de aire. |
| 11 | `/examination/Cardiac` | Regular pulse at a normal rate; no new murmur. | Pulso regular, de frecuencia normal; sin soplo nuevo. |
| 12 | `/examination/Respiratory` | No increased effort; lungs clear. | Sin aumento del esfuerzo respiratorio; pulmones limpios. |
| 13 | `/examination/Neurological` | Alert, oriented and moving all limbs normally. | Alerta, orientado y moviliza las cuatro extremidades con normalidad. |
| 14 | `/investigations/pocus/result/lv` | Hypokinesis of the posterior wall; the anterior and lateral walls contract normally | Hipocinesia de la pared posterior; las paredes anterior y lateral se contraen normalmente |
| 15 | `/investigations/pocus/result/ivc` | 1.6 cm; about 50% inspiratory collapse | 1.6 cm; colapso inspiratorio de aproximadamente 50% |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/history/bleeding/0` (L0-34), `/examination/Abdomen` (L0-38), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/chest_xray/result/report` (L0-24), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21), `/investigations/ecg_right/result/report` (L0-29), `/investigations/ecg_posterior/result/report` (L0-28).

- **Observaciones:** ninguna de sentido, clínica ni de terminología.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☒ **APPROVE WHOLE CASE** — docente, 2026-10-07; versión aprobada `a6311c114d9c4d8cd1c444fd724a0a62cced41d7ccfbb2392ce25773618d1890`.

## Resumen del lote R1A

| Caso | Propios | Cubiertos por el lote 0 | Versión que se aprueba | Recomendación | Decisión docente |
|---|---|---|---|---|---|
| `acs_54m_inferior` | 18 | 17 | `e1afcda5…` (con T-2) | APPROVE | ☒ APPROVE |
| `acs_66f_nonst` | 16 | 19 | `d64dc726…` (con T-1) | APPROVE | ☒ APPROVE |
| `acs_61m_posterior` | 15 | 20 | `a6311c11…` (sin cambios) | APPROVE | ☒ APPROVE |
| **Total** | **49** | **56** | | | |

Siguiente: R1B (`acs_52m_de_winter`, `acs_48m_wellens` y `acs_70f_left_main`), en `docs/revision/B5_RELATO_R1B.md`.
