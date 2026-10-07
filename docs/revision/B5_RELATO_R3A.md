# B-5 · Relato en español · Lote R3A: TEP y bradicardias (casos 1 a 3)

> **PARA REVISIÓN DOCENTE. Nada implementado.** Primera mitad del lote R3 de la revisión del relato
> (`docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md`). La docencia pidió R3 en dos mitades el 2026-10-07, como R1 y R2.
> Se sigue el orden canónico del banco (`clinical_cases.FAMILIES`: TEP, después bradicardias; el mismo del manifiesto,
> `pilot_freeze.CASES`):
> - R3A: `pulmonary_embolism_33f`, `pulmonary_embolism_61m` y `bradycardia_ccb_68m`;
> - R3B: `bradycardia_avb3_78f`, `bradycardia_bb_54f` y `bradycardia_hyperk_63m`.
>
> Se aprueba el caso entero, en la versión objetivo impresa (`case_text.version`). No se crea `approvals.json` ni se
> cambia `case_text/es`.
>
> 2026-10-07 · rama `clinical-encounter-v0.13` · relato leído de `case_text/es/pulmonary_embolism.json` y
> `case_text/es/bradycardia.json` contra el inglés vigente de cada caso, sin cambiar nada.

**En una mirada**

- **Pasajes:** 3 casos y 110 pasajes. 53 están cubiertos por frases del lote 0, ya aprobadas; **57 son propios y se
  revisan** (18, 20 y 19).
- **Corpus de la validación externa:** ninguno de los 3 casos está en él, así que no hay pasajes fijos en este lote.
- **Términos ya aprobados:** T-1 a T-3 ya rigen en los 3 casos (los dos de TEP ya dicen «crépitos», y la 61m dice
  «defensa muscular», la misma forma que los dos casos de hemorragia digestiva). **Ninguna versión cambia:** la
  versión objetivo de cada caso es la del repositorio hoy.
- **P-1, aprobada en R2B, revisada en este lote:** «crushing» aparece sólo en la 61m («crushing pressure» → «presión
  opresiva»). No reproduce el problema de la 24f: el caso no usa «opresión» para otro síntoma.
- **Lo que no apareció:** desajustes de sentido, redacción clínicamente engañosa ni términos que choquen con X-1, la
  rúbrica, T-1 a T-3 o P-1. El contenido clínico del POCUS de llegada de las dos TEP ya fue confirmado en R-2
  (`docs/revision/R2_POCUS_C14.md`); aquí se revisa su español.
- **Regla de versión (docente, 2026-10-07):** la aprobación ata la versión objetivo presentada en la revisión, no la
  que está hoy en el repositorio. Al implementar, cada versión del español tiene que dar exactamente su hash aprobado;
  si da otro, se detiene y vuelve a revisión docente.
- **Recomendación:** **APPROVE** en los 3 casos.

## pulmonary_embolism_33f

- **Versión que se aprueba:** `d3a826e9c4679a8944e2a5eb5e174f36ba800ca0c91a48bd7a14f8afbe05e5ab` (la del repositorio hoy; sin cambios)
- **Pasajes:** 37. Cubiertos por frases del lote 0, ya aprobadas: 19. **Propios, a revisar: 18.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 33-year-old woman arrives with sudden breathlessness and sharp right-sided chest discomfort. She wonders whether anxiety could explain the episode; this has not been assessed. | Una mujer de 33 años llega con disnea súbita y molestia punzante en el hemitórax derecho. Se pregunta si la ansiedad podría explicar el episodio; esto no ha sido evaluado. |
| 2 | `/history/chief_complaint/0` | I suddenly became short of breath and it hurts on the right when I breathe in. | De repente me empezó a faltar el aire y me duele en el lado derecho al inspirar. |
| 3 | `/history/associated_symptoms/0` | I have felt my heart racing and a little lightheaded. | He sentido el corazón acelerado y me he sentido un poco mareada. |
| 4 | `/history/medical_history/0` | I had surgery for an ankle fracture 12 days ago and have been much less mobile. | Me operaron de una fractura de tobillo hace 12 días y me he movido mucho menos. |
| 5 | `/history/medications/0` | I use an estrogen-containing contraceptive and occasional acetaminophen. | Uso un anticonceptivo con estrógeno y, de vez en cuando, paracetamol. |
| 6 | `/history/onset/0` | The breathing and chest discomfort started abruptly about two hours ago. | La dificultad para respirar y la molestia en el pecho comenzaron bruscamente hace unas dos horas. |
| 7 | `/history/risk_factors/0` | I have recent surgery, reduced mobility and use an estrogen-containing contraceptive. | Me operaron hace poco, tengo la movilidad reducida y uso un anticonceptivo con estrógeno. |
| 8 | `/history/chest_pain/0` | The pain is sharp and worsens with inspiration; it is not relieved by rest. | El dolor es punzante y empeora al inspirar; no se alivia con el reposo. |
| 9 | `/history/breathing/0` | The breathlessness started suddenly while I was sitting. | La falta de aire empezó de repente mientras estaba sentada. |
| 10 | `/history/bleeding/0` | I have not coughed blood or had other recent bleeding. | No he tosido sangre ni he tenido otros sangrados recientes. |
| 11 | `/history/leg_symptoms/0` | My operated leg has been more swollen, including the calf, since yesterday. | Desde ayer tengo más hinchada la pierna operada, incluida la pantorrilla. |
| 12 | `/examination/Respiratory` | Increased effort; breath sounds are equal without focal crackles or wheeze. | Esfuerzo respiratorio aumentado; murmullo pulmonar simétrico, sin crépitos focales ni sibilancias. |
| 13 | `/examination/Extremities` | Unilateral calf swelling and tenderness on the operated side. | Aumento de volumen unilateral y dolor a la palpación de la pantorrilla del lado operado. |
| 14 | `/investigations/pocus/result/rv` | Mildly enlarged, approximately equal to the LV; no septal flattening (no D-sign); no McConnell sign | Levemente aumentado de tamaño, aproximadamente igual al VI; sin aplanamiento septal (sin signo D); sin signo de McConnell |
| 15 | `/investigations/pocus/result/ivc` | 2.0 cm; <50% inspiratory collapse | 2.0 cm; colapso inspiratorio <50% |
| 16 | `/investigations/pocus/result/dvt_popliteal` | Non-compressible on the operated (symptomatic) side, with echogenic intraluminal material; compressible on the other side | No compresible en el lado operado (sintomático), con material ecogénico intraluminal; compresible en el otro lado |
| 17 | `/investigations/chest_xray/result/report` | No focal consolidation, edema or pneumothorax. | Sin consolidación focal, edema ni neumotórax. |
| 18 | `/investigations/ctpa/result/report` | Acute lobar and segmental filling defects in the right and left pulmonary arteries. Mild RV enlargement. | Defectos de llenado agudos lobares y segmentarios en las arterias pulmonares derecha e izquierda. Leve aumento de tamaño del VD. |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/associated_symptoms/1` (L0-35), `/history/allergies/0` (L0-33), `/examination/Cardiac` (L0-44), `/examination/Abdomen` (L0-38), `/examination/Neurological` (L0-45), `/investigations/pocus/result/lv` (L0-04), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21), `/investigations/d_dimer/result/report` (L0-23).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. Ya dice «crépitos» (T-1), así que no cambia nada.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## pulmonary_embolism_61m

- **Versión que se aprueba:** `71c15c2b2811acd747993f8bb4e5d6f0cad5083ceaf035655fe7aba055ebd714` (la del repositorio hoy; sin cambios)
- **Pasajes:** 36. Cubiertos por frases del lote 0, ya aprobadas: 16. **Propios, a revisar: 20.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 61-year-old man is brought in after nearly collapsing. He is breathless and says he feels faint even while lying on the trolley. | Un hombre de 61 años es traído tras casi desplomarse. Está disneico y dice sentirse a punto de desmayarse incluso estando acostado en la camilla. |
| 2 | `/history/chief_complaint/0` | I suddenly felt breathless and nearly passed out. | De repente sentí que me faltaba el aire y casi me desmayo. |
| 3 | `/history/associated_symptoms/0` | I have felt my heart racing and had discomfort when taking a deep breath. | He sentido el corazón acelerado y he tenido una molestia al respirar profundo. |
| 4 | `/history/associated_symptoms/1` | I have no fever, sputum or recent vomiting. | No tengo fiebre, flemas ni vómitos recientes. |
| 5 | `/history/medical_history/0` | I am receiving chemotherapy for colon cancer; I have not previously had a clot. | Estoy recibiendo quimioterapia por un cáncer de colon; no he tenido coágulos antes. |
| 6 | `/history/medications/0` | I receive scheduled chemotherapy and as-needed anti-nausea medication; I do not take an anticoagulant. | Recibo quimioterapia programada y un medicamento para las náuseas cuando lo necesito; no tomo ningún anticoagulante. |
| 7 | `/history/onset/0` | The severe breathlessness and near-collapse began about 45 minutes ago. | La falta de aire intensa y el episodio en que casi me desplomé comenzaron hace unos 45 minutos. |
| 8 | `/history/risk_factors/0` | I have active cancer and have spent much of the last week in bed because of fatigue. | Tengo un cáncer activo y he pasado gran parte de la última semana en cama por el cansancio. |
| 9 | `/history/chest_pain/0` | There is mild chest discomfort on a deep breath, without a sustained crushing pressure. | Hay una molestia leve en el pecho al respirar profundo, sin una presión opresiva sostenida. |
| 10 | `/history/bleeding/0` | I have no recent black stool, rectal bleeding or hematemesis. | No he tenido recientemente deposiciones negras, sangrado por el recto ni vómitos con sangre. |
| 11 | `/history/leg_symptoms/0` | My left calf has been swollen for several days. | Tengo la pantorrilla izquierda hinchada desde hace varios días. |
| 12 | `/examination/Respiratory` | Marked respiratory effort with equal breath sounds and no widespread crackles. | Esfuerzo respiratorio marcado, con murmullo pulmonar simétrico y sin crépitos difusos. |
| 13 | `/examination/Abdomen` | Soft, without guarding or focal tenderness. | Blando, sin defensa muscular ni dolor focal a la palpación. |
| 14 | `/examination/Neurological` | Awake and answers appropriately, but reports persistent faintness. | Vigil y responde adecuadamente, pero refiere sensación persistente de desmayo. |
| 15 | `/examination/Extremities` | Left calf swelling and tenderness. | Aumento de volumen y dolor a la palpación de la pantorrilla izquierda. |
| 16 | `/investigations/pocus/result/lv` | Small, underfilled cavity with vigorous contraction | Cavidad pequeña, con llenado disminuido y contracción vigorosa |
| 17 | `/investigations/pocus/result/rv` | Larger than the LV; septal flattening with a D-shaped LV; reduced free-wall contraction with apical sparing (McConnell sign) | Mayor que el VI; aplanamiento septal con VI en forma de D; contracción disminuida de la pared libre con preservación apical (signo de McConnell) |
| 18 | `/investigations/pocus/result/ivc` | 2.3 cm; minimal inspiratory collapse | 2.3 cm; colapso inspiratorio mínimo |
| 19 | `/investigations/pocus/result/dvt_popliteal` | Left popliteal vein non-compressible; right popliteal vein compressible | Vena poplítea izquierda no compresible; vena poplítea derecha compresible |
| 20 | `/investigations/ctpa/result/report` | Extensive acute bilateral main and lobar pulmonary arterial filling defects with RV enlargement and septal flattening. | Extensos defectos de llenado agudos bilaterales en las arterias pulmonares principales y lobares con aumento de tamaño del VD y aplanamiento septal. |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/examination/Cardiac` (L0-41), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/chest_xray/result/report` (L0-24), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21), `/investigations/d_dimer/result/report` (L0-23).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. Ya dice «crépitos» (T-1) y «defensa muscular» (T-2; la misma forma que en los dos casos de hemorragia digestiva), así que no cambia nada. Revisado a la luz de P-1: «crushing pressure» → «presión opresiva» no reproduce el problema de la 24f, porque este caso no usa «opresión» para otro síntoma, y «opresiva» conserva el sentido (una presión de tipo coronario, que el paciente niega).
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## bradycardia_ccb_68m

- **Versión que se aprueba:** `10b926936212c922ccd2a3ce699c4d87df4f76d4c50e456bbf0c628d3f8932c4` (la del repositorio hoy; sin cambios)
- **Pasajes:** 37. Cubiertos por frases del lote 0, ya aprobadas: 18. **Propios, a revisar: 19.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 68-year-old man is brought in after collapsing at home. He is pale, cold and very slow on the monitor. Handover notes a collapse and a slow rate; the boxes came in with the daughter. | Un hombre de 68 años es traído tras colapsar en su casa. Está pálido, frío y con una frecuencia muy lenta en el monitor. La entrega menciona un colapso y una frecuencia lenta; las cajas de los medicamentos llegaron con la hija. |
| 2 | `/history/chief_complaint/0` | His daughter says he has felt dizzy and weak all afternoon and then slumped in his chair. | Su hija cuenta que se ha sentido mareado y débil toda la tarde y que luego se desplomó en su silla. |
| 3 | `/history/associated_symptoms/0` | His daughter reports no chest pain and no breathlessness before the collapse. | Su hija refiere que no tuvo dolor en el pecho ni falta de aire antes del colapso. |
| 4 | `/history/associated_symptoms/1` | He has been nauseated and vomited once. | Ha tenido náuseas y vomitó una vez. |
| 5 | `/history/medical_history/0` | His daughter reports high blood pressure and an irregular heart rhythm treated for years. | Su hija refiere presión alta y un ritmo cardíaco irregular tratado desde hace años. |
| 6 | `/history/medications/0` | His daughter brought the boxes: verapamil, which he doubled last week on advice, and enalapril. She thinks he may have taken extra today because of palpitations. | Su hija trajo las cajas de los medicamentos: verapamilo, cuya dosis duplicó la semana pasada siguiendo indicaciones, y enalapril. Ella cree que hoy podría haber tomado de más por palpitaciones. |
| 7 | `/history/onset/0` | The dizziness began this afternoon; the collapse was about forty minutes ago. | El mareo comenzó esta tarde; el colapso fue hace unos cuarenta minutos. |
| 8 | `/history/risk_factors/0` | He lives alone and manages his own medication; the doses were changed last week. | Vive solo y maneja él mismo sus medicamentos; las dosis se cambiaron la semana pasada. |
| 9 | `/history/neurological_symptoms/0` | There was no seizure, no head strike and no focal weakness afterwards. | No hubo convulsión, ni golpe en la cabeza, ni debilidad focal después. |
| 10 | `/history/chest_pain/0` | His daughter reports no chest pain before or after the collapse. | Su hija refiere que no tuvo dolor en el pecho ni antes ni después del colapso. |
| 11 | `/history/breathing/0` | His daughter says the breathing has looked normal throughout. | Su hija cuenta que la respiración se ha visto normal todo el tiempo. |
| 12 | `/history/oral_intake/0` | He has eaten little today and vomited once. | Hoy ha comido poco y vomitó una vez. |
| 13 | `/history/exposure/0` | There is no other medicine in the house and no alcohol or drug use she knows of. | No hay otros medicamentos en la casa y, que ella sepa, no consume alcohol ni drogas. |
| 14 | `/examination/Cardiac` | Very slow regular pulse; peripheries cool with delayed capillary refill; no murmur. | Pulso muy lento y regular; extremidades frías con llene capilar enlentecido; sin soplos. |
| 15 | `/examination/Respiratory` | Normal rate and effort with clear breath sounds. | Frecuencia y esfuerzo respiratorios normales, con murmullo pulmonar sin ruidos agregados. |
| 16 | `/examination/General appearance` | Pale and cold; alert but slow to answer, with no rash or swelling. | Pálido y frío; alerta, pero lento para responder, sin erupción ni edema. |
| 17 | `/examination/Neurological` | Awake, oriented and moving all limbs; no focal deficit. | Vigil, orientado y moviliza todas las extremidades; sin déficit focal. |
| 18 | `/appearance_stable` | No rash or swelling. | Sin erupción ni edema. |
| 19 | `/investigations/chest_xray/result/report` | Clear lung fields; no consolidation, edema or pneumothorax. | Campos pulmonares limpios; sin consolidación, edema ni neumotórax. |

Cubiertos por el lote 0: `/history_source` (L0-31), `/history/allergies/0` (L0-33), `/examination/Abdomen` (L0-38), `/investigations/pocus/result/lv` (L0-07), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/ivc` (L0-12), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. Ningún término de T-1 a T-3 aparece en el caso.
- **Recomendación para el caso entero:** **APPROVE**.
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## Resumen del lote R3A

| Caso | Propios | Cubiertos por el lote 0 | Fijos del corpus | Versión objetivo que se aprueba | Recomendación | Decisión docente |
|---|---|---|---|---|---|---|
| `pulmonary_embolism_33f` | 18 | 19 | 0 | `d3a826e9…` (sin cambios) | APPROVE | ☐ |
| `pulmonary_embolism_61m` | 20 | 16 | 0 | `71c15c2b…` (sin cambios) | APPROVE | ☐ |
| `bradycardia_ccb_68m` | 19 | 18 | 0 | `10b92693…` (sin cambios) | APPROVE | ☐ |
| **Total** | **57** | **53** | **0** | | | |

Siguiente: R3B (`bradycardia_avb3_78f`, `bradycardia_bb_54f` y `bradycardia_hyperk_63m`), después de la decisión
docente sobre R3A.
