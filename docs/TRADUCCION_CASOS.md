# Narrativa de los casos en español — revisión docente

> Instrucción del 2026-09-26: «Todo lo que se almacena en la app se puede definir si verlo en inglés o
> español». La narrativa de los 31 casos del banco se tradujo y **se usa sólo después de tu revisión, caso
> por caso** (elegiste «Sí, con tu revisión»).

## Qué se tradujo y cómo se usa

- **1.108 pasajes** (599 textos distintos): presentación, quién da la historia, respuestas de la anamnesis,
  examen físico e informes de exámenes (POCUS, eFAST, radiografías, TAC, ecografía renal y comentarios de
  laboratorio). Están en `case_text/es/<familia>.json`, cada uno junto al inglés que traduce.
- Los tradujeron cuatro agentes con una misma guía: español clínico de uso en Chile, sin agregar ni quitar
  información, con números, dosis y unidades tal como en inglés. Se verificó que todos los números
  coinciden y que una misma frase inglesa tiene siempre la misma traducción.
- **Nada se muestra en español sin tu aprobación.** En el panel docente, «Case narrative in Spanish
  (faculty review)» muestra cada caso en dos columnas (inglés | español). «Aprobar» registra tu revisión
  con tu cuenta y la versión exacta que leíste. «Pedir cambios» exige una nota.
- Una vez aprobado, el caso se ve en español en la sala y en los documentos cuando el idioma es español.
  La aprobación vale sólo para ese caso: muchas frases se repiten entre casos (por ejemplo, las del POCUS),
  y en un caso todavía no aprobado siguen en inglés, igual que el resto de ese caso.
  Un pasaje se reemplaza entero o no se reemplaza, así que ninguna línea mezcla idiomas. Si después cambia
  el inglés del caso o su traducción, el caso vuelve a «pendiente» y ese texto no se usa hasta rehacerlo.
- El registro del encuentro sigue en inglés; el español es presentación. Por eso un encuentro jugado antes
  de tu aprobación también se lee en español después.

## Decisiones que conviene que confirmes

| # | Punto | Borrador | Alternativa |
|---|---|---|---|
| 1 | Nombres de fármacos en la narrativa | Genérico en español (ibuprofeno, apixabán, losartán, metformina, verapamilo) | Dejarlos como en inglés, como en las etiquetas del motor (decisión 16) |
| 2 | «I feel sick» (acs_61m_posterior, acs_70f_left_main) | «Tengo náuseas» | «Me siento mal»: en 70f, «náuseas» agrega un síntoma que la presentación no nombra |
| 3 | Extremidades «cool» y «cold» | Ambas «frías», como la grilla de signos | «Heladas» para «cold», con lo que se conserva la gradación |
| 4 | «slow» en bradycardia_bb_54f y bradycardia_hyperk_63m | «lenta / lento», literal | Explicitar frecuencia («con frecuencia muy lenta») si es lo que quiso decir el caso |
| 5 | «consolidation» | «consolidación» | «condensación», muy usado en Chile |
| 6 | «arthritis» (el caso dice osteoartritis) | «artritis» | «artrosis», como lo diría un paciente chileno |
| 7 | «crackles» | «crepitaciones» (7 pasajes) y «crépitos» (4), según el lote | Unificar en uno de los dos |
| 8 | «solo» | Sin tilde, como pide la RAE | Con tilde, como en la mayor parte de la interfaz |

**Un posible error en el inglés del caso (no se cambió):** en `obstructive_pyelonephritis_58f`, la ecografía
renal describe un cálculo de 9 mm en la unión pieloureteral y además un uréter proximal dilatado. Una
obstrucción en esa unión no dilata el uréter que está por debajo de ella. Queda como está hasta que lo decidas.

**Consistencia del catálogo de la sala:** el ECG derecho decía «derivadas derechas» y el posterior
«derivaciones posteriores»; ahora ambos dicen «derivaciones».

**Quién da la historia:** las fuentes de una palabra (Patient, Wife, Son, Daughter, Partner) quedaron como
Paciente, Esposa, Hijo, Hija y Pareja. En la sala aparecen dentro de una etiqueta fija, «History from:» en la
llegada y «History source:» en el panel de conversación. Esa etiqueta se traduce junto con la fuente, como
«Fuente de la historia: Esposa», así que la línea sale entera en un idioma.

## Notas completas de cada lote

Se reproducen como las dejaron quienes tradujeron. Lo que ya se resolvió está indicado arriba (por ejemplo,
las derivaciones del ECG) y lo que requiere tu decisión está en la tabla.

### Neumonía, edema pulmonar, SCA

143 pasajes traducidos. Aquí van solo las decisiones que merecen una mirada docente.

1. **Nombres de fármacos (posible conflicto con la decisión 16).**
   *losartan, atorvastatin, amlodipine, metformin, methotrexate* → **losartán, atorvastatina, amlodipino, metformina, metotrexato**. Seguí la regla 4 de la guía de estilo (genérico en español). Pero el docstring de `tools_case_text.py` y `docs/DECISION_16_IDIOMA.md` dicen que los nombres de fármacos se escriben "como los escribe el inglés". Si la decisión 16 también rige para la narrativa, hay que revertir estos cinco nombres (aparecen en 7 pasajes).

2. **"I feel sick", entendido como náuseas.**
   *I feel sick and clammy.* → **Tengo náuseas y sudor frío.** (acs_61m_posterior)
   *I feel sick and very sweaty.* → **Tengo náuseas y estoy muy sudorosa.** (acs_70f_left_main)
   Lo leí en el sentido británico (náuseas), que calza con "with nausea" en la presentación del caso 61m. En el caso 70f la presentación no menciona náuseas. Si la intención era "me siento mal", usar **Me siento mal**.

3. **"Alert and oriented." se comparte entre un hombre (acs_52m_de_winter) y dos mujeres (acs_70f_left_main, pulmonary_embolism_33f).**
   → **Alerta, con orientación conservada.** Es neutro en género porque una sola clave sirve a los tres casos, y `tools_case_text.py check` marcaría como inconsistente una traducción distinta por caso. En los demás hallazgos, el adjetivo concuerda con el sexo del paciente (orientado/orientada).

4. *focal crackles and bronchial breathing at the right base* → **crepitaciones focales y soplo tubario en la base derecha**. "Soplo tubario" es el término semiológico habitual en Chile. La alternativa literal es "respiración bronquial".

5. *reduced air entry at the left base* → **murmullo pulmonar disminuido en la base izquierda**. Es la forma chilena (en otros países se dice "murmullo vesicular"). La alternativa literal es "disminución de la entrada de aire".

6. **crackles → "crepitaciones"** en todo el archivo, por ser neutro. En la ficha chilena es muy común "crépitos"; si se prefiere, el cambio es un reemplazo global.

7. **Alcance de "witnessed".**
   *There was no witnessed head strike, seizure or new sedative exposure.* → **No se presenció golpe en la cabeza, convulsión ni exposición a un sedante nuevo.**
   Conservé el alcance del inglés ("witnessed" cubre los tres elementos). Si lo que se quiere decir es "sin golpe ni convulsión presenciados, y sin sedantes nuevos", usar: **No hubo golpe en la cabeza ni convulsión presenciados, ni exposición a un sedante nuevo.**

8. *I suddenly cannot catch my breath, especially if I lie back.* → **De un momento a otro no me alcanza el aire, sobre todo si me recuesto.** Evité "de repente", que en Chile suele significar "a veces".

9. **Registro del paciente.**
   - Mantuve los términos técnicos que el inglés pone en boca del paciente: dolor pleurítico, hematemesis, disuria, tos productiva, fracción de eyección, antiagregante plaquetario, antihipertensivo.
   - *sputum* → **expectoración**. En Chile el paciente diría "desgarro" o "flemas".
   - *rigors* y *shaking chills* → **escalofríos con temblor**, ambos con la misma traducción.
   - *my father* → **mi papá**, que es lo natural en el habla chilena.

10. **Glosario, para armonizar con narrative_b, narrative_c e investigations.**
    - *breathlessness* → **disnea** (presentación y examen) / **falta de aire** (palabras del paciente).
    - *cannot catch my breath* → **no me alcanza el aire**.
    - *chest pressure* y *tightness* → **opresión (en el pecho)**; *tight* → **apretado**.
    - *heavy* → **tipo peso** / **como un peso** / **pesadez**.
    - *crushing* → **aplastante**.
    - *tenderness* → **dolor a la palpación**; *non-tender* → **indoloro**.
    - *guarding* → **resistencia muscular**.
    - *elevated JVP* → **presión venosa yugular elevada** (en la ficha chilena también se escribe "ingurgitación yugular").
    - *pitting edema* → **edema con fóvea**.
    - *Awake* → **Vigil**; *Alert* → **Alerta**.
    - *warm/cool* → **tibia/fría**, como en `language.py`.
    - *effort* a secas, en el examen respiratorio → **esfuerzo respiratorio**.
    - *Severe respiratory effort* → **Esfuerzo respiratorio severo**, igual que la interfaz.
    - *all limbs* → **las cuatro extremidades**.
    - *referral note* → **nota de derivación**.
    - *triage* se mantiene como "triage", igual que la interfaz.

### TEP, asma, HDA, hipoglicemia

Casos: asthma_24f, asthma_49m, gi_bleed_57m, gi_bleed_72f, hypoglycemia_28m / _76f / _54m_thiamine,
pulmonary_embolism_33f / _61m (más dos pasajes compartidos con opioid_35m y pulmonary_edema_58m).

#### Glosario aplicado en todo el archivo

- **reliever / rescue inhaler** → «inhalador de rescate»; **preventer inhaler / inhaled controller** → «inhalador
  de mantención». Los dos términos ingleses del controlador quedan en uno solo. Alternativa GINA: «de alivio» /
  «controlador».
- **wheeze** → «sibilancias» en la entrega y el examen, pero «me silba el pecho» / «el pecho le silbaba» cuando
  hablan la paciente o la pareja (registro lego).
- **breathlessness** → «disnea» en presentaciones; «falta de aire» en palabras del paciente. **chest tightness** →
  «opresión torácica» (narración) / «pecho apretado» (paciente).
- **air entry / breath sounds** → «murmullo pulmonar» (disminuido, simétrico, bilateral); **clear** → «sin ruidos
  agregados». Alternativa: «entrada de aire», que usa docs/GENERATED_MECHANISMS.md.
- **lightheaded(ness)** → «mareo / mareada»; **feel faint** → «sentirse a punto de desmayarse»; **faintness** →
  «sensación de desmayo». «Mareo» es amplio en español; alternativa: «sensación de desvanecimiento».
- **Awake** → «Vigil» (uso de ficha chilena); **Alert** → «Alerta»; **swelling** (examen) → «aumento de volumen»;
  **tenderness** → «dolor a la palpación»; **guarding** → «defensa muscular».
- «solo» sin tilde (norma RAE), igual que narrative_a y narrative_c. La interfaz de la aplicación usa mayormente
  «sólo»; conviene unificar en un solo criterio.

#### Pasajes puntuales

1. *Handover notes that the wheeze sounds quieter than it did earlier.* → «En la entrega se señala que las
   sibilancias suenan más silenciosas que antes.» Es la pista del agotamiento (tórax silencioso). Usé la expresión
   de la facultad («sibilancias más silenciosas», tanda20.py) y no la escalé a «tórax silencioso». Alternativa:
   «son menos audibles».
2. *Peak expiratory flow is 35% of her documented personal best.* / *peak-flow maneuver* → «flujo espiratorio
   máximo». Alternativa de uso chileno: «PEF» / «flujometría».
3. *occasional acetaminophen* → «paracetamol». No es una variante ortográfica: es el nombre que se usa en Chile
   (DCI).
4. *knee arthritis* (57m), *have arthritis* / *naproxen for arthritis* (72f) → «artritis». Los datos del caso dicen
   *osteoarthritis*, y un paciente chileno con artrosis diría «artrosis». Mantuve «artritis» para no reinterpretar;
   la facultad decide.
5. *Regular pulse with preserved peripheral volume.* → «Pulso regular, con pulsos periféricos de amplitud
   conservada.» Leí *volume* como amplitud del pulso: «volumen periférico conservado», literal, se leería como
   volemia.
6. *I have no recent black stool, rectal bleeding or hematemesis.* → «…sangrado por el recto ni vómitos con
   sangre.» El inglés pone un término técnico en boca del paciente; lo pasé a registro lego sin cambiar el
   contenido.
7. *the near-faint occurred this morning* / *The severe breathlessness and near-collapse began…* → «el episodio en
   que casi me desmayé / casi me desplomé». El español no tiene un sustantivo natural para esto. *collapse* →
   «desplomarse»; evité «colapso», que puede leerse como colapso hemodinámico o pulmonar.
8. *Coworker and emergency medication information* (y todo el 28m) → «compañero de trabajo». El inglés no da el
   sexo; usé masculino genérico. Si una imagen muestra a una mujer, cambiar a «compañera».
9. *mealtime insulin* → «insulina prandial», también cuando lo cuenta el compañero. Alternativa lega: «insulina de
   las comidas».
10. *I have been drinking normally…* → «He estado tomando líquidos normalmente…». «Bebiendo» o «tomando» a secas
    se lee como alcohol.
11. *Shelter staff and the paramedic record* → «Personal del albergue y registro de los paramédicos». Alternativa:
    «registro prehospitalario (SAMU)».

### Opioides, anafilaxia, cólico renal, bradicardia, trauma

205 pasajes traducidos. Aquí solo van las decisiones que conviene revisar. El resto es traducción directa.

1. **Extremidades "cool" y "cold": ambas quedan como "frías"**
   - EN: "Very slow regular pulse; peripheries cool with delayed capillary refill; no murmur." / "Fast, thready pulse; peripheries cold with delayed capillary refill."
   - ES: "…extremidades frías con llene capilar enlentecido…" en los dos casos.
   - Por qué: la grilla de signos de la app muestra "Cool" como "Frías" (`language.py`). En este lote, cada "cold" pertenece a un caso cuyo valor observado es "Cool". Usar "heladas", que es como la app traduce "Cold", haría el hallazgo más grave de lo que muestra la grilla. Con esto se pierde la gradación inglesa entre cool y cold. Si se quiere conservarla, la alternativa es traducir "cold" como "heladas".

2. **"slow" ambiguo en dos presentaciones**
   - EN: "She is cold and very slow." (bradycardia_bb_54f) / "He is cold, slow and short of breath on minimal effort." (bradycardia_hyperk_63m)
   - ES: "Está fría y muy lenta." / "Está frío, lento y con falta de aire al mínimo esfuerzo."
   - Por qué: la traducción es literal. En español, "lento/a" se lee como enlentecimiento psicomotor. Si el autor se refería a la frecuencia cardíaca, conviene explicitarlo como en bradycardia_ccb_68m, donde "very slow on the monitor" quedó como "con una frecuencia muy lenta en el monitor".

3. **"the boxes" como "las cajas de los medicamentos"** (bradycardia_ccb_68m, presentación y medicamentos)
   - EN: "…the boxes came in with the daughter." / "His daughter brought the boxes: verapamil, …"
   - ES: "…las cajas de los medicamentos llegaron con la hija." / "Su hija trajo las cajas de los medicamentos: verapamilo, …"
   - Por qué: "las cajas", sin más, no se entiende en español. Se hizo explícito lo que el inglés da por entendido.

4. **"on advice"**
   - EN: "verapamil, which he doubled last week on advice"
   - ES: "verapamilo, cuya dosis duplicó la semana pasada siguiendo indicaciones"
   - Por qué: el inglés no dice quién dio el consejo, así que no se agregó "médica".

5. **"sick" en inglés británico**
   - EN: "I have felt weak and sick and my legs will not hold me."
   - ES: "Me he sentido débil y con náuseas, y las piernas no me sostienen."
   - Por qué: "sick" puede significar "enfermo" o "con náuseas". Se eligió "con náuseas" porque la presentación dice "nauseated".

6. **"spouse" como "cónyuge" y "partner" como "pareja"** (opioid_67f, bradycardia_bb_54f)
   - EN: "Her spouse reports…" / "Spouse and medication list"
   - ES: "Su cónyuge refiere…" / "Cónyuge y lista de medicamentos"
   - Por qué: el caso no indica el sexo del cónyuge. "Cónyuge" es neutro, y se evitaron adjetivos con género ("no sabe con certeza" en lugar de "no está seguro/a"). Si el cuerpo docente define el sexo, "esposo/a" sonaría más coloquial.

7. **"blood thinner"**
   - EN: "I take no medication and no blood thinner." / "I take nothing, including no blood thinner."
   - ES: "No tomo medicamentos ni nada para diluir la sangre." / "No tomo nada, tampoco nada para diluir la sangre."
   - Por qué: es una expresión coloquial que en inglés también incluye los antiagregantes. Traducirla como "anticoagulante" la restringiría.

8. **"hay fever", "peanuts" y "satay"**
   - EN: "I have hay fever; …" / "I ate a dish with a satay sauce; I have avoided peanuts since childhood…"
   - ES: "Tengo rinitis alérgica; …" / "Comí un plato con salsa satay; evito el maní desde niña…"
   - Por qué: "fiebre del heno" casi no se usa en Chile, y "maní" es el término chileno. "Satay" se mantuvo como nombre del plato; el pasaje de exposición aclara que era salsa de maní.

9. **"tightness" frente a "crushing"**
   - EN: "There is tightness across the chest but no crushing central pain."
   - ES: "Hay una opresión que atraviesa el pecho, pero no un dolor aplastante en el centro."
   - Por qué: en Chile lo habitual para el dolor coronario es "dolor opresivo". Aquí, sin embargo, "opresión" ya traduce "tightness". Se usó "aplastante" para que lo que la paciente niega se distinga de lo que afirma.

10. **Examen respiratorio en el registro de ficha chileno, no literal**
    - "clear breath sounds" → "murmullo pulmonar sin ruidos agregados"; "reduced/equal air entry" → "murmullo pulmonar disminuido/simétrico"; "crackles" → "crépitos".
    - En "Slightly increased rate with clear breath sounds; no crackles." queda "…sin ruidos agregados; sin crépitos.". La redundancia viene del original.

11. **Otros términos del examen**
    - "renal angle tenderness" → "dolor a la palpación del ángulo costovertebral". No se usó "puñopercusión", porque nombraría una maniobra que el inglés no describe.
    - "cannon waves in the neck" → "ondas en cañón en el cuello". El inglés no dice "ondas a", así que no se agregó.
    - "thready" → "filiforme"; "well filled" → "bien perfundidas"; "capillary refill" → "llene capilar" (término que ya usa la app).
    - "Awake" → "Vigil"; "moves all limbs" → "moviliza todas las extremidades". No se escribió "las cuatro" para no agregar un número.

12. **"collapse", "blackouts" y "floppy"**
    - "collapsing / the collapse" → "colapsar / el colapso"; "blackouts" → "desmayos" (el término técnico sería "pérdidas de conciencia"); "became grey and floppy" → "se puso grisáceo y quedó sin fuerza" ("floppy" no tiene un equivalente coloquial exacto).

13. **"wheeze" en el relato de la esposa**
    - EN: "His wife says the wheeze began before he became drowsy."
    - ES: "Su esposa cuenta que las sibilancias comenzaron antes de que se pusiera somnoliento."
    - Por qué: se mantuvo "sibilancias" para que coincida con el examen. Una versión más coloquial sería "el silbido al respirar".

14. **Fármacos**: verapamil → verapamilo, apixaban → apixabán, losartan → losartán, amlodipine → amlodipino, atorvastatin → atorvastatina, digoxin → digoxina, spironolactone → espironolactona, metformin → metformina, sustained-release morphine → morfina de liberación prolongada, long-acting opioid → opioide de acción prolongada, beta blocker → betabloqueador. Se mantienen igual atenolol, enalapril, propranolol y paracetamol.

15. **Otros**: "Handover notes…" → "La entrega menciona…" (igual que el "Llegada y entrega" de la app); "fully exposed" → "fue expuesto por completo" (la exposición del ATLS); "back strain" → "distensión de espalda"; "no intent is established" → "no se ha establecido intencionalidad".

### Informes de exámenes

111 pasajes traducidos (`investigations.es.json`). Cada frase repetida se tradujo de la misma forma en todos los casos. Estos son los puntos en que conviene que el docente confirme la elección.

1. **"air-space opacity"** (Rx: "focal air-space opacity", "Right lower-lobe air-space opacity", "perihilar air-space and interstitial opacities") → **"opacidad alveolar"** / "opacidades alveolares e intersticiales". Es el término habitual en los informes radiológicos chilenos; la alternativa literal es "opacidad del espacio aéreo".
2. **"consolidation"** → **"consolidación"** en todo el archivo (POCUS y Rx), como indica la guía de estilo, aunque en Chile se usa mucho "condensación".
3. **"Globally reduced contraction without a single focal defect"** → **"Contracción globalmente disminuida sin un defecto focal único"**. El inglés es ambiguo: puede querer decir "ningún defecto focal" o "no un defecto focal aislado". Elegí la segunda lectura porque el código fuente del caso habla de isquemia difusa por lesión de tronco o de tres vasos. Si el sentido era "ninguno", la frase sería "sin ningún defecto focal".
4. **VD "enlarged" / "RV enlargement"** → **"Levemente aumentado de tamaño"** / **"aumento de tamaño del VD"**, y no "dilatado/dilatación", para no cambiar el hallazgo. Si el docente prefiere "dilatación del VD", el cambio afecta tres pasajes (POCUS y AngioTAC).
5. **"hypokinesis / akinesis / apex"** → **"hipocinesia / acinesia / ápex"**. Las dos primeras son las formas de la RAE; en los informes de eco chilenos también aparecen "hipokinesia/aquinesia". Para "apex", la alternativa es "ápice".
6. **"No pericardial effusion"** (POCUS) → **"Sin derrame pericárdico"**, pero **"No pericardial fluid"** (E-FAST) → **"Sin líquido pericárdico"**. Mantuve la diferencia del inglés porque en el E-FAST se informa el líquido, que es el hallazgo, y no su interpretación.
7. **"Right-sided leads." / "Posterior leads."** → **"Derivaciones derechas." / "Derivaciones posteriores."**. En `language.py` la etiqueta de la orden dice "ECG con **derivadas** derechas" pero "ECG con **derivaciones** posteriores". Convendría unificarlas.
8. **Comentario del dímero D**: reutilicé literalmente la traducción que ya existe en `language.py` ("Referencia superior ajustada por edad: … Sobre el límite: esto no establece un diagnóstico ni lo descarta."), para que las dos vías muestren el mismo texto.
9. **Orina completa**: "red/white cells" → **"hematíes/leucocitos"**; "Few / Numerous" → **"Escasos / Abundantes"** (la escala semicuantitativa del sedimento); "Blood" → **"Sangre"** (algunos laboratorios informan "hemoglobina"); "nitrite" → **"nitritos"**.
10. **"No free fluid behind or around the bladder"** → **"Sin líquido libre retrovesical ni perivesical"**. Usé los equivalentes técnicos; la alternativa literal es "detrás ni alrededor de la vejiga". En la Rx de hemotórax, "loss of the left hemidiaphragm outline" → **"borramiento del contorno…"** y "with a meniscus" → **"con menisco"**.
11. **Cifras**: "about 50%" → "de aproximadamente 50%"; ">50%" y "<50%" se mantienen como símbolos ("colapso inspiratorio >50%"). Mantuve el punto decimal ("1.8 cm") según la decisión 16, aunque en Chile se usa la coma decimal.
12. **Concordancia con las etiquetas** (aviso para quien traduzca las etiquetas): "No dilatada" es femenino, porque supone "Raíz aórtica" y "Aorta torácica descendente". "Compresibles" es plural, porque supone "Venas femorales/poplíteas". Los descriptores del VD van en masculino.
13. **Observación sobre el original en inglés** (no lo corregí): la eco renal de `obstructive_pyelonephritis_58f` describe un cálculo de 9 mm **en la unión pieloureteral** con **uréter proximal dilatado**. Anatómicamente no calza: una obstrucción en la unión pieloureteral no dilata el uréter que está por debajo. Conviene revisar el texto en inglés.

