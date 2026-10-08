# B-5 · Relato en español · Lote R5: hemorragia digestiva y anafilaxia

> **PARA REVISIÓN DOCENTE. Nada implementado. Preparado en la sesión autónoma del 2026-10-08, sin decisión docente.**
> Lote R5, en el orden canónico del banco (`clinical_cases.FAMILIES`: `gi_bleed` va antes que `anaphylaxis`; el mismo de `pilot_freeze.CASES`): `gi_bleed_57m`, `gi_bleed_72f`, `anaphylaxis_29f` y `anaphylaxis_63m_betablocked`. El rótulo del §4 del diseño («Anafilaxia y hemorragia digestiva») sólo nombra las familias.
>
> Se aprueba el caso entero, en la versión objetivo impresa (`case_text.version`). No se crea `approvals.json` ni se
> cambia `case_text/es`. Relato leído de `case_text/es/gi_bleed.json` y `case_text/es/anaphylaxis.json` contra el inglés vigente de cada caso, sin cambiar nada.

**En una mirada**

- **Pasajes:** 4 casos y 146 pasajes. 66 están cubiertos por frases del lote 0, ya aprobadas;
  **80 son propios y se revisan** (17, 17, 23, 23).
- **Corpus de la validación externa:** `gi_bleed_57m`, `anaphylaxis_29f` están en él; sus 6 pasajes fijos van marcados 🔒, ya están aprobados tal como están escritos y no cambian.
- **Términos ya aprobados:** T-1 a T-3 ya rigen en estos casos (comprobado: ninguno conserva «crepitaciones», «resistencia
  muscular» ni el adjetivo «confuso»), y P-1 no aplica. **Ninguna versión cambia:** la versión objetivo de cada caso es la
  del repositorio hoy.
- **Lo que no apareció:** desajustes de sentido, redacción clínicamente engañosa ni términos que choquen con X-1, la
  rúbrica, T-1 a T-3, P-1 o V-9.
- **Regla de versión (docente):** la aprobación ata la versión exacta revisada (la objetivo, si difiere de la del repositorio). Si al implementar el hash de un caso aprobado cambia, se detiene y vuelve a revisión docente.
- **Recomendación:** **APPROVE** en los 4 casos (categoría A: limpios).

## gi_bleed_57m

- **Versión que se aprueba:** `5d758337c68f1c59fea20607c1d65cd939dcf8953a4ff85cc5b1867a7e9abcca` (la del repositorio hoy; sin cambios)
- **Pasajes:** 34. Cubiertos por frases del lote 0, ya aprobadas: 17. **Propios, a revisar: 17.**
- **Pasajes que fija el corpus de la validación externa:** 3 (`/presentation`, `/history/chief_complaint/0`, `/history/onset/0`), marcados 🔒. Ya están aprobados tal como están escritos (§8 del diseño, 2026-10-07); se muestran para leerlos con el caso y no se cambian en esta revisión. Un error clínicamente relevante se escalaría.

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` 🔒 | A 57-year-old man presents after nearly fainting when standing. He looks pale and says he feels profoundly weak. | Un hombre de 57 años consulta tras casi desmayarse al ponerse de pie. Se ve pálido y dice sentirse profundamente débil. |
| 2 | `/history/chief_complaint/0` 🔒 | I nearly passed out when I stood up and still feel very weak. | Casi me desmayo cuando me paré y todavía me siento muy débil. |
| 3 | `/history/associated_symptoms/0` | I have had dark, sticky stools since yesterday. | Desde ayer tengo deposiciones oscuras y pegajosas. |
| 4 | `/history/associated_symptoms/1` | I have felt mild burning high in my abdomen and become breathless on walking. | He sentido un ardor leve en la parte alta del abdomen y me ha faltado el aire al caminar. |
| 5 | `/history/medical_history/0` | I have knee arthritis and intermittent indigestion; no known liver disease. | Tengo artritis en la rodilla y a veces indigestión; no tengo ninguna enfermedad conocida del hígado. |
| 6 | `/history/medications/0` | I have taken ibuprofen most days for my knee over the last two weeks. | En las últimas dos semanas he tomado ibuprofeno casi todos los días por la rodilla. |
| 7 | `/history/onset/0` 🔒 | The dark stools began yesterday; the near-faint occurred this morning. | Las deposiciones oscuras empezaron ayer; el episodio en que casi me desmayé fue esta mañana. |
| 8 | `/history/risk_factors/0` | I have used regular anti-inflammatory tablets and have new dark stools. | He tomado pastillas antiinflamatorias en forma regular y tengo deposiciones oscuras que antes no tenía. |
| 9 | `/history/bleeding/0` | The stools are black and sticky, not just dark brown; I have not vomited blood. | Las deposiciones son negras y pegajosas, no solo café oscuro; no he vomitado sangre. |
| 10 | `/history/chest_pain/0` | I have no central chest pressure. | No tengo presión en el centro del pecho. |
| 11 | `/history/oral_intake/0` | I have had less appetite but have not had vomiting or diarrhea. | He tenido menos apetito, pero no he tenido vómitos ni diarrea. |
| 12 | `/examination/Cardiac` | Regular tachycardia with weak peripheral pulses. | Taquicardia regular con pulsos periféricos débiles. |
| 13 | `/examination/Respiratory` | No increased effort; lungs clear on auscultation despite tachypnea. | Sin aumento del esfuerzo respiratorio; auscultación pulmonar sin ruidos agregados pese a la taquipnea. |
| 14 | `/examination/Abdomen` | Mild epigastric tenderness without guarding. Rectal examination reveals black tarry stool. | Dolor leve a la palpación del epigastrio, sin defensa muscular. El tacto rectal muestra deposición negra, de aspecto alquitranado. |
| 15 | `/examination/Neurological` | Awake and oriented, reporting persistent faintness. | Vigil y orientado, refiere sensación persistente de desmayo. |
| 16 | `/investigations/pocus/result/lv` | Small cavity with hyperdynamic contraction; near-obliteration of the cavity in systole | Cavidad pequeña con contracción hiperdinámica; obliteración casi completa de la cavidad en sístole |
| 17 | `/investigations/pocus/result/ivc` | 0.9 cm; near-complete inspiratory collapse | 0.9 cm; colapso inspiratorio casi completo |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/history/urinary_symptoms/0` (L0-37), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/chest_xray/result/report` (L0-24), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. «Defensa muscular» es la forma que la docencia ya aceptó como equivalente a T-2 (R3A, 61m). «Ibuprofeno» coincide con V-9. Nada se lee como transfusión ni volumen ya administrados. Los 3 pasajes 🔒 se leyeron con el caso: ningún error clínicamente relevante.
- **Recomendación para el caso entero:** **APPROVE** (categoría A: limpio, sin cambios de texto).
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## gi_bleed_72f

- **Versión que se aprueba:** `9c6d28681ed8084f616d940bfe16d3475aec1a724f656a43f177930b82dd634b` (la del repositorio hoy; sin cambios)
- **Pasajes:** 34. Cubiertos por frases del lote 0, ya aprobadas: 17. **Propios, a revisar: 17.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 72-year-old woman presents with worsening fatigue and lightheadedness. She had to stop walking from the waiting room because she felt faint. | Una mujer de 72 años consulta por cansancio y mareo que han ido empeorando. Tuvo que detenerse mientras caminaba desde la sala de espera porque se sintió a punto de desmayarse. |
| 2 | `/history/chief_complaint/0` | I am unusually tired and keep feeling lightheaded when I move. | Estoy más cansada de lo normal y me mareo cada vez que me muevo. |
| 3 | `/history/associated_symptoms/0` | My stools have become black and sticky over several days. | Mis deposiciones se han ido poniendo negras y pegajosas a lo largo de varios días. |
| 4 | `/history/associated_symptoms/1` | I have little abdominal pain and have not vomited blood. | Tengo poco dolor abdominal y no he vomitado sangre. |
| 5 | `/history/medical_history/0` | I had a stomach ulcer years ago and have arthritis. | Tuve una úlcera de estómago hace años y tengo artritis. |
| 6 | `/history/medications/0` | I have recently been taking naproxen for arthritis; I am not taking a stomach-protecting medicine. | Últimamente he estado tomando naproxeno para la artritis; no estoy tomando ningún medicamento para proteger el estómago. |
| 7 | `/history/onset/0` | Fatigue began four days ago; the lightheadedness is much worse today. | El cansancio empezó hace cuatro días; hoy el mareo está mucho peor. |
| 8 | `/history/risk_factors/0` | I have a prior ulcer and recent regular anti-inflammatory use. | Tuve una úlcera antes y últimamente he tomado antiinflamatorios en forma regular. |
| 9 | `/history/bleeding/0` | I have passed black, sticky stool for three days, with another episode this morning. | Hace tres días que tengo deposiciones negras y pegajosas, y esta mañana tuve otro episodio. |
| 10 | `/history/chest_pain/0` | I have not had new central chest pain. | No he tenido dolor nuevo en el centro del pecho. |
| 11 | `/history/oral_intake/0` | I have been drinking normally, without diarrhea or repeated vomiting. | He estado tomando líquidos normalmente, sin diarrea ni vómitos repetidos. |
| 12 | `/history/urinary_symptoms/0` | I have no urinary symptoms. | No tengo molestias urinarias. |
| 13 | `/examination/Cardiac` | Rapid regular pulse; no new murmur. | Pulso rápido y regular; sin soplos nuevos. |
| 14 | `/examination/Respiratory` | No increased respiratory effort; breath sounds clear bilaterally. | Sin aumento del esfuerzo respiratorio; murmullo pulmonar bilateral sin ruidos agregados. |
| 15 | `/examination/Abdomen` | Soft without guarding or significant tenderness. Rectal examination reveals melena. | Blando, sin defensa muscular ni dolor significativo a la palpación. El tacto rectal muestra melena. |
| 16 | `/examination/Neurological` | Alert, oriented and moving all limbs symmetrically. | Alerta, orientada y moviliza las cuatro extremidades en forma simétrica. |
| 17 | `/investigations/pocus/result/lv` | Hyperdynamic contraction | Contracción hiperdinámica |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/ivc` (L0-09), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/chest_xray/result/report` (L0-27), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. «Defensa muscular», equivalente a T-2. «Naproxeno» es medicación habitual, fuera de V-9 (que cubre los fármacos que el lector reconoce como orden).
- **Recomendación para el caso entero:** **APPROVE** (categoría A: limpio, sin cambios de texto).
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## anaphylaxis_29f

- **Versión que se aprueba:** `7ea433dc65d28ee292505e42846080aef573ba0175f327179bf696843567a237` (la del repositorio hoy; sin cambios)
- **Pasajes:** 39. Cubiertos por frases del lote 0, ya aprobadas: 16. **Propios, a revisar: 23.**
- **Pasajes que fija el corpus de la validación externa:** 3 (`/presentation`, `/history/chief_complaint/0`, `/history/onset/0`), marcados 🔒. Ya están aprobados tal como están escritos (§8 del diseño, 2026-10-07); se muestran para leerlos con el caso y no se cambian en esta revisión. Un error clínicamente relevante se escalaría.

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` 🔒 | A 29-year-old woman arrives from a restaurant with a spreading rash, a swollen face and noisy breathing. She is anxious and speaks in short phrases. | Una mujer de 29 años llega desde un restaurante con una erupción que se extiende, la cara hinchada y respiración ruidosa. Está ansiosa y habla con frases cortas. |
| 2 | `/history/chief_complaint/0` 🔒 | My face and throat feel like they are closing and my whole body is itching. | Siento como si la cara y la garganta se me estuvieran cerrando, y me pica todo el cuerpo. |
| 3 | `/history/associated_symptoms/0` | The rash came up everywhere within minutes and my lips are swollen. | La erupción me salió por todas partes en cuestión de minutos y tengo los labios hinchados. |
| 4 | `/history/associated_symptoms/1` | I feel light-headed and my chest is tight. | Me siento mareada y tengo el pecho apretado. |
| 5 | `/history/medical_history/0` | I have hay fever; I have never had a reaction like this and I have no asthma. | Tengo rinitis alérgica; nunca había tenido una reacción así y no tengo asma. |
| 6 | `/history/medications/0` | I take no regular medication. I have no adrenaline autoinjector. | No tomo medicamentos habituales. No tengo autoinyector de adrenalina. |
| 7 | `/history/onset/0` 🔒 | It began about fifteen minutes into the meal and has worsened since. | Comenzó unos quince minutos después de empezar a comer y ha empeorado desde entonces. |
| 8 | `/history/risk_factors/0` | I ate a dish with a satay sauce; I have avoided peanuts since childhood without ever being tested. | Comí un plato con salsa satay; evito el maní desde niña, sin que nunca me hayan hecho exámenes. |
| 9 | `/history/exposure/0` | The meal contained a peanut sauce; there was no sting, no new medicine and no contrast. | La comida tenía una salsa de maní; no hubo picadura, ni medicamento nuevo, ni medio de contraste. |
| 10 | `/history/breathing/0` | My chest feels tight and my throat feels narrow when I breathe in. | Siento el pecho apretado y la garganta estrecha cuando tomo aire. |
| 11 | `/history/chest_pain/0` | There is tightness across the chest but no crushing central pain. | Hay una opresión que atraviesa el pecho, pero no un dolor aplastante en el centro. |
| 12 | `/history/oral_intake/0` | I had eaten only a few mouthfuls when it started. | Había comido solo unos pocos bocados cuando empezó. |
| 13 | `/history/bleeding/0` | I have not coughed or vomited blood. | No he tosido ni vomitado sangre. |
| 14 | `/examination/Cardiac` | Rapid regular pulse; the peripheries are warm and well filled. | Pulso rápido y regular; extremidades tibias y bien perfundidas. |
| 15 | `/examination/Respiratory` | Increased effort with widespread expiratory wheeze and audible inspiratory stridor. | Esfuerzo respiratorio aumentado, con sibilancias espiratorias difusas y estridor inspiratorio audible. |
| 16 | `/examination/Abdomen` | Soft; mild diffuse discomfort without guarding. | Blando; molestia difusa leve, sin defensa. |
| 17 | `/examination/General appearance` | Widespread urticarial wheals, flushing and periorbital and lip swelling. | Habones urticariales difusos, enrojecimiento y edema periorbitario y labial. |
| 18 | `/examination/Neurological` | Awake, oriented and anxious; answers are short because of the breathing. | Vigil, orientada y ansiosa; sus respuestas son breves a causa de la respiración. |
| 19 | `/investigations/pocus/result/lv` | Vigorous, hyperdynamic contraction with near-obliteration in systole | Contracción vigorosa e hiperdinámica con obliteración casi completa en sístole |
| 20 | `/investigations/pocus/result/ivc` | 0.9 cm; >50% inspiratory collapse | 0.9 cm; colapso inspiratorio >50% |
| 21 | `/investigations/chest_xray/result/report` | Hyperinflated lung fields without consolidation, edema or pneumothorax. | Campos pulmonares hiperinsuflados sin consolidación, edema ni neumotórax. |
| 22 | `/derived/Respiratory/without_stridor` | Increased effort with widespread expiratory wheeze; no stridor heard now. | Esfuerzo respiratorio aumentado, con sibilancias espiratorias difusas; ya no se escucha estridor. |
| 23 | `/derived/Respiratory/intubated` | Endotracheal tube in place: no stridor through the tube; widespread expiratory wheeze. | Tubo endotraqueal instalado: sin estridor a través del tubo; sibilancias espiratorias difusas. |

Cubiertos por el lote 0: `/history_source` (L0-30), `/history/allergies/0` (L0-33), `/history/urinary_symptoms/0` (L0-36), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. «Autoinyector de adrenalina» usa el nombre de V-9 (epinephrine → adrenalina) y deja claro que no hubo adrenalina previa. «Dolor aplastante» coincide con P-1. «Sin defensa» (T-2). Las líneas derivadas («ya no se escucha estridor»; «Tubo endotraqueal instalado: …», igual que C-28 y C-29) siguen el estado del motor (TD-50, TD-47) sin atribuir una causa: no dicen que la adrenalina funcionó, y nada choca con K-18, K-21, K-E5 ni TD-82. Los 3 pasajes 🔒 se leyeron con el caso: ningún error clínicamente relevante.
- **Recomendación para el caso entero:** **APPROVE** (categoría A: limpio, sin cambios de texto).
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## anaphylaxis_63m_betablocked

- **Versión que se aprueba:** `c153cc253f35dc6509d059ec916100362f97c02616eac022c3a66f4a5b266200` (la del repositorio hoy; sin cambios)
- **Pasajes:** 39. Cubiertos por frases del lote 0, ya aprobadas: 16. **Propios, a revisar: 23.**
- **Pasajes que fija el corpus de la validación externa:** ninguno (el caso no está en el corpus).
- **Texto fijado por una prueba del corpus** (no es uno de los 18): `/history_source`, marcado ⚑ (`test_validation_corpus.py:62`). Cambiarlo obligaría a cambiar esa prueba.

| N.º | Ruta | EN | ES |
|---|---|---|---|
| 1 | `/presentation` | A 63-year-old man is brought in after a wasp sting in his garden. He is flushed, wheezing and difficult to rouse fully. Handover notes a sting and a rash; the medication list came with the family, not with the patient. | Un hombre de 63 años es traído tras una picadura de avispa en su jardín. Está enrojecido, con sibilancias y cuesta despertarlo por completo. La entrega menciona una picadura y una erupción; la lista de medicamentos llegó con la familia, no con el paciente. |
| 2 | `/history_source` ⚑ | Wife | Esposa |
| 3 | `/history/chief_complaint/0` | His wife says he was stung, came inside saying he felt strange, and then became grey and floppy. | Su esposa cuenta que lo picaron, que entró a la casa diciendo que se sentía raro y que después se puso grisáceo y quedó sin fuerza. |
| 4 | `/history/associated_symptoms/0` | His wife reports a rash over his chest and arms within minutes. | Su esposa refiere que en cuestión de minutos le apareció una erupción en el pecho y los brazos. |
| 5 | `/history/associated_symptoms/1` | He complained of tightness in the throat before he stopped speaking clearly. | Se quejó de opresión en la garganta antes de dejar de hablar con claridad. |
| 6 | `/history/medical_history/0` | His wife reports high blood pressure and an irregular heart rhythm. He has been stung before without a reaction. | Su esposa refiere presión alta y un ritmo cardíaco irregular. Lo han picado antes sin que haya tenido una reacción. |
| 7 | `/history/medications/0` | His wife lists atenolol and apixaban, taken every morning; he took both today. | Su esposa enumera atenolol y apixabán, que toma todas las mañanas; hoy tomó ambos. |
| 8 | `/history/onset/0` | The sting was about twenty minutes ago and he deteriorated within ten. | La picadura fue hace unos veinte minutos y empeoró en menos de diez. |
| 9 | `/history/risk_factors/0` | He keeps bees at the end of the garden and has been stung several times over the years. | Cría abejas al fondo del jardín y lo han picado varias veces a lo largo de los años. |
| 10 | `/history/exposure/0` | His wife saw the wasp and the sting site on the forearm; no new medicine and no food were involved. | Su esposa vio la avispa y el sitio de la picadura en el antebrazo; no hubo ningún medicamento nuevo ni alimento involucrado. |
| 11 | `/history/breathing/0` | His wife says the wheeze began before he became drowsy. | Su esposa cuenta que las sibilancias comenzaron antes de que se pusiera somnoliento. |
| 12 | `/history/chest_pain/0` | His wife reports no complaint of chest pain before he stopped speaking. | Su esposa refiere que no se quejó de dolor en el pecho antes de dejar de hablar. |
| 13 | `/history/neurological_symptoms/0` | There was no witnessed seizure, head strike or focal weakness. | No se presenció ninguna convulsión, golpe en la cabeza ni debilidad focal. |
| 14 | `/history/oral_intake/0` | He had eaten breakfast several hours earlier. | Había desayunado varias horas antes. |
| 15 | `/history/bleeding/0` | There is no bleeding from the sting site or elsewhere. | No hay sangrado en el sitio de la picadura ni en otra parte. |
| 16 | `/examination/Cardiac` | Irregular pulse at a rate that does not rise with the low pressure; peripheries warm. | Pulso irregular, con una frecuencia que no aumenta pese a la presión baja; extremidades tibias. |
| 17 | `/examination/Respiratory` | Increased effort with widespread wheeze; no stridor heard. | Esfuerzo respiratorio aumentado, con sibilancias difusas; no se escucha estridor. |
| 18 | `/examination/General appearance` | Flushing over the chest and arms with scattered wheals; a sting site on the right forearm. | Enrojecimiento en el tórax y los brazos, con habones dispersos; sitio de picadura en el antebrazo derecho. |
| 19 | `/examination/Neurological` | Opens eyes to voice and follows simple commands slowly; moves all limbs. | Abre los ojos al llamado verbal y obedece órdenes simples con lentitud; moviliza todas las extremidades. |
| 20 | `/appearance_stable` | A sting site on the right forearm. | Sitio de picadura en el antebrazo derecho. |
| 21 | `/investigations/pocus/result/lv` | Preserved contraction without the hyperdynamic pattern | Contracción conservada sin el patrón hiperdinámico |
| 22 | `/investigations/chest_xray/result/report` | No consolidation, edema or pneumothorax. | Sin consolidación, edema ni neumotórax. |
| 23 | `/derived/Respiratory/intubated` | Endotracheal tube in place: no stridor through the tube; widespread wheeze. | Tubo endotraqueal instalado: sin estridor a través del tubo; sibilancias difusas. |

Cubiertos por el lote 0: `/history/allergies/0` (L0-33), `/examination/Abdomen` (L0-38), `/investigations/pocus/result/rv` (L0-03), `/investigations/pocus/result/pericardium` (L0-02), `/investigations/pocus/result/ivc` (L0-09), `/investigations/pocus/result/lung_sliding` (L0-13), `/investigations/pocus/result/lungs` (L0-15), `/investigations/pocus/result/lung_consolidation` (L0-14), `/investigations/pocus/result/aorta_root` (L0-17), `/investigations/pocus/result/aorta_descending` (L0-18), `/investigations/pocus/result/aorta_abdominal` (L0-19), `/investigations/pocus/result/dvt_femoral` (L0-01), `/investigations/pocus/result/dvt_popliteal` (L0-01), `/investigations/troponin/result/report` (L0-20), `/investigations/urinalysis/result/report` (L0-22), `/investigations/blood_cultures/result/report` (L0-21).

- **Observaciones:** ninguna de sentido, clínica ni de terminología. Atenolol y apixabán son medicación habitual («hoy tomó ambos»: historia, no una orden). El relato no nombra glucagón ni adrenalina ni dice que se haya tratado. «Pulso irregular, con una frecuencia que no aumenta pese a la presión baja» conserva la pista del betabloqueo (DF-23 fila 7). La fuente «Esposa» (⚑) también la fija una prueba del corpus.
- **Recomendación para el caso entero:** **APPROVE** (categoría A: limpio, sin cambios de texto).
- **Decisión docente:** ☐ APPROVE WHOLE CASE · ☐ REVISE — Nota: ________

## Resumen del lote R5

| Caso | Propios | Cubiertos por el lote 0 | Fijos del corpus | Versión objetivo que se aprueba | Recomendación | Decisión docente |
|---|---|---|---|---|---|---|
| `gi_bleed_57m` | 17 | 17 | 3 🔒 | `5d758337…` (sin cambios) | APPROVE | ☐ |
| `gi_bleed_72f` | 17 | 17 | 0 | `9c6d2868…` (sin cambios) | APPROVE | ☐ |
| `anaphylaxis_29f` | 23 | 16 | 3 🔒 | `7ea433dc…` (sin cambios) | APPROVE | ☐ |
| `anaphylaxis_63m_betablocked` | 23 | 16 | 0 + 1 ⚑ | `c153cc25…` (sin cambios) | APPROVE | ☐ |
| **Total** | **80** | **66** | **6** | | | |
