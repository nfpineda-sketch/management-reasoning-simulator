# Medición EN/ES del lector de órdenes · corpus de ensayo

Ciclo 1 del AI Advisor, quick win QW1, aprobado por el docente el 2026-09-27:
«medición determinista del reconocimiento de órdenes EN/ES utilizando
exclusivamente el corpus de ensayo existente».

- **Código medido:** commit `3719b0c`. La app no se modificó.
- **Herramienta:** `tools_order_reading.py`, con semilla fija 3000.
- **Corpus:** los 20 guiones de `tanda20.py` y su versión en inglés,
  `tanda20_en.py`.
- **Ejecución:** los 40 recorridos pasaron por la página real (`app.py`), sin
  clave de proveedor y con una base temporal.
- **Datos reales:** no se leyó ningún encuentro real de residentes.

## Conclusión

1. **Reconocimiento de órdenes: el corpus es insuficiente para una comparación
   EN/ES útil.** Da 96 de 96 en ambos idiomas, pero no es una tasa real.
   - Es el mismo corpus con el que se ajustó el lector
     (`docs/TANDA_20_ESCENARIOS.md` §2).
   - `test_the_twenty_in_english.py` ya exige que cada orden produzca los
     mismos tipos de acción en los dos idiomas.
   - Por eso el resultado es una línea base de regresión dentro de la muestra
     de ajuste, no una estimación de cuántas órdenes reales se leen mal.
   - Según la instrucción, esta parte se detuvo aquí sin ampliar la fuente de
     datos. Es la decisión pendiente DF-6 en `docs/COLA_DECISIONES_AI_ADVISOR.md`.
2. **Razonamiento que el Trace atribuye al residente: la comparación sí fue útil.**
   - Esa capa (las cuatro categorías) no estaba cubierta por el ajuste ni por
     aquel test.
   - En 6 de 119 decisiones los dos idiomas registran algo distinto.
   - Aparecen defectos deterministas de fidelidad, más frecuentes en español:
     texto cambiado, palabras truncadas y órdenes guardadas como «modelo de
     trabajo».
   - Es un hallazgo CRITICAL según la §3 del charter (fidelidad del Management
     Trace). No se corrigió: queda como DF-7 en la cola de decisiones.
3. **Costo:** US$0, con 0 llamadas de IA registradas en los 40 encuentros
   (`ai_calls_spent` = 0) y 0 decisiones interpretadas por IA. El cómputo fue de
   unos 13 minutos locales.

## Resultados · órdenes (acciones que el motor ejecuta)

| Métrica (charter §90) | Español | Inglés |
|---|---|---|
| Órdenes enviadas (pasos «order») | 96 | 96 |
| Decisiones ejecutadas | 96 | 96 |
| Órdenes no reconocidas (UNRECOGNIZED ORDER RATE) | 0 / 96 | 0 / 96 |
| Decisiones aceptadas sin acción leída | 0 | 0 |
| Retenciones previstas por el guion (las cuatro preguntas) | 19 | 19 |
| Retenciones no previstas (proxy de REPEATED ORDER RATE) | 0 | 0 |
| Misma firma de acciones que el otro idioma (tipo y todos los parámetros) | 94 / 96 | 94 / 96 |
| Encuentros completos con revisión | 20 / 20 | 20 / 20 |
| Minuto de cierre distinto del otro idioma | 0 | 0 |

Las 2 firmas distintas son del mismo tipo:

- Cuando el residente responde «Reassessment: PA, FC…», el lector registra el
  foco de la reevaluación como `general` en español y como `perfusion` en inglés
  («BP, HR…»).
- Ocurre en el guion 4, decisión 4, y en el guion 16, decisión 5.
- Hay una divergencia más en las indicaciones de alta del guion 7, decisión 10:
  - en inglés se pierde «urology follow-up»;
  - «return precautions for fever, vomiting or uncontrolled pain» queda como
    «return precautions for fever»;
  - en español se registran las dos cosas completas.

**No medible con este corpus:**

- **PARTIAL / INCORRECT EXECUTION RATE (UNKNOWN):** requieren un estándar de
  referencia orden por orden, que no existe.
- **REPEATED ORDER RATE (UNKNOWN):** requiere un residente que repita. El guion
  no repite; las retenciones no previstas son sólo el proxy.

## Resultados · razonamiento registrado (las cuatro categorías)

| Métrica | Español | Inglés |
|---|---|---|
| Categorías registradas como «dichas por el residente» (`stated`) | 192 | 191 |
| … cuyo texto no aparece en lo que escribió el residente | **4** | 0 |
| «Modelo de trabajo» declarado (`problem_representation`, `stated`) | 30 | 29 |
| … que en realidad es una orden | **5** | 1 |
| Decisiones con procedencia distinta del otro idioma | 6 / 119 | 6 / 119 |

Defectos, con causa verificada en el código (KNOWN) y reproducibles sin la
página:

1. **«im» pasa a «I'm».**
   - **Dónde:** `extract_explicit_reasoning`, en `app.py:5687`, reescribe como
     «I'm» todo «im», «i.m» o «IM» aislado antes de extraer el razonamiento.
   - **Efecto en español:** «Doy adrenalina 0.5 mg im» queda registrado como
     *modelo de trabajo dicho por el residente*: «Doy adrenalina 0.5 mg I'm».
   - **Casos:** guion 19, decisión 2; guion 12, decisiones 1 y 4.
   - **Inglés:** en la misma decisión arrastra correctamente la hipótesis
     previa.
   - **Consecuencias:** el Trace le atribuye al residente un razonamiento que no
     escribió (§62) y altera sus palabras.
   - **Alcance:** la misma reescritura se aplica a «IM» en inglés.
2. **Palabras terminadas en «-so» se truncan.**
   - **Dónde:** las expresiones de límite de cláusula (`app.py:5708`, `5727`,
     `5743`, `5807`, `5942`, `5976`, `5980`, `5985`) buscan `\s*,?\s*so\b` sin
     un límite de palabra antes de «so».
   - **Efecto:** «un IAM inferior con posible compromiso del VD» queda como «un
     IAM inferior con posible compromi».
   - **Casos:** guion 3, decisión 1.
   - **Alcance:** afecta a cualquier palabra terminada en «so» (compromiso,
     caso, paso, peso, ingreso, acceso, uso). En inglés afectaría a «also».
3. **Una orden ocupa el lugar del modelo de trabajo.**
   - En el guion 19, decisión 4, el residente escribe «Toma betabloqueador, por
     eso no responde».
   - El Trace registra como modelo de trabajo «inicio adrenalina en infusion a
     0.1 mcg/kg/min».
   - En inglés, para la misma decisión, registra «not responding».
   - El guion 3, decisión 2, guarda en ambos idiomas «Consulto a hemodinamia …
     porque es un IAM con supradesnivel», mitad orden y mitad razón. Es igual en
     los dos idiomas.
4. **Actualizaciones del modelo que un idioma capta y el otro no.** Hay déficits
   en ambos sentidos:
   - **Guion 11, decisión 4 (falla en español):** no registra «una PaCO2 normal
     en una crisis así es agotamiento, es falla ventilatoria inminente». Arrastra
     «una crisis asmática». El inglés sí la registra.
   - **Guion 10, decisión 6 (falla en inglés):** no registra «she takes
     glimepiride: it can fall again for hours, so she cannot go home». Arrastra
     «hypoglycemia from eating little». El español sí la registra.
   - **Guion 5, decisión 9 (falla en inglés):** no arrastra ningún modelo de
     trabajo; el español arrastra el previo.
   - **Guion 7, decisión 10 (discrepancia de criterio):** el inglés registra los
     hallazgos («Mild pain, afebrile…») como modelo de trabajo; el español
     arrastra «un cólico renal derecho».

Por qué importa: el brief docente, la propuesta de rúbrica y los PDF leen estas
categorías como razonamiento del residente (§33, §62). Los defectos 1 y 2 son
de clase, no de frase (§57), y su corrección natural ocurre en la fuente
(`extract_explicit_reasoning`).

## Qué dice y qué no dice esta medición

**Lo que dice:**

- **KNOWN:** con el código actual, sobre este corpus, ambos idiomas ejecutan las
  mismas órdenes, con las mismas dosis y los mismos minutos.
- **KNOWN:** los defectos del razonamiento listados existen y se reproducen.

**Lo que no dice:**

- **INFERRED:** que el lector falle poco con residentes reales. El corpus está
  ajustado a sí mismo (§57, «no optimizar para los test cases»).
- **Cobertura del corpus:** 11 de las 12 familias del banco; no incluye
  **trauma**. Son 20 de 31 casos.
- **UNKNOWN:** la frecuencia real de órdenes no leídas, parciales o mal
  ejecutadas en encuentros de residentes.
- **UNKNOWN:** la latencia percibida. Los tiempos del runner en proceso (unos
  20 s por guion completo) no representan la experiencia en el navegador.

## Reproducir

```
python tools_order_reading.py --play es all --out DIR --seed 3000
python tools_order_reading.py --play en all --out DIR --seed 3000
python tools_order_reading.py --compare DIR     # escribe DIR/comparison.json
```

La herramienta se niega a correr si ve una clave de proveedor. Sus funciones de
comparación tienen pruebas en `test_tools_order_reading.py`.

## Ciclo 2 · DF-7: antes y después (2026-09-27)

**Qué se corrigió.** El docente aprobó corregir en la fuente, por clase, los
defectos de fidelidad del razonamiento. La medición se repitió sobre el mismo
corpus, con la misma semilla (3000) y sin llamadas de IA.

**Cambio en la herramienta.** Desde este ciclo también sigue la categoría
`rationale`. Las bases de ambas mediciones se releyeron con esa versión, sin
volver a jugar el antes (`--reread`).

### Resultado

| Métrica | ES antes | ES después | EN antes | EN después |
|---|---|---|---|---|
| Órdenes ejecutadas | 96/96 | 96/96 | 96/96 | 96/96 |
| Órdenes no reconocidas · decisiones sin acción leída | 0 · 0 | 0 · 0 | 0 · 0 | 0 · 0 |
| Retenciones previstas · no previstas | 19 · 0 | 19 · 0 | 19 · 0 | 19 · 0 |
| Encuentros completos | 20/20 | 20/20 | 20/20 | 20/20 |
| Categorías declaradas por el residente (`stated`) | 192 | **212** | 213 | 213 |
| … con texto que no está en lo que escribió | **4** | **0** | 0 | 0 |
| «Modelo de trabajo» que es una orden | **5** | **0** | **1** | **0** |
| `rationale` declarado | **0** | **21** | 22 | 22 |
| Decisiones con diferencia pareada EN/ES | **62** | **1** | — | — |
| Llamadas de IA | 0 | 0 | 0 | 0 |

Cambios de acciones, tiempos, retenciones y cierres entre antes y después, en
las 238 decisiones: sólo los tres buscados.

- **ES, 2 decisiones:** el foco de la reevaluación «PA, FC…» pasa de `general` a
  `perfusion`, como el inglés «BP, HR…».
- **EN, 1 decisión:** el alta conserva «urology follow-up» y el aviso completo
  «return precautions for fever, vomiting or uncontrolled pain», como el español.

No cambió ningún minuto, ninguna retención ni ningún cierre.

### Causas raíz y cambios

Todo está en la fuente: `app.py`, `extract_explicit_reasoning`, salvo donde se
indica otro archivo.

1. **«im» se reescribía como «I'm».**
   - **Antes:** la reescritura se aplicaba en cualquier posición.
   - **Ahora:** sólo se reescribe cuando abre una cláusula y la sigue un
     participio o un estado («I.m addressing…», «Im concerned…»).
   - **Resultado:** tras una dosis siempre es la vía intramuscular.
2. **Palabras terminadas en «-so» se truncaban.**
   - **Causa:** los 16 marcadores de cláusula (so, therefore, because, porque,
     then…) no exigían límite de palabra antes.
   - **Ahora:** lo exigen, así que «compromiso» y «also» ya no se cortan.
3. **Órdenes registradas como modelo de trabajo.** La causa era doble:
   - el indicio `adrenal\w*` también reconocía «adrenalina» y «adrenaline»;
   - la lista de verbos de orden sólo tenía infinitivos, así que «doy»,
     «inicio» y «consulto» no se reconocían.

   Ahora:

   - **Qué es una orden.** Lo decide el propio lector (`parse_family_actions`),
     que conoce todas las formas en ambos idiomas.
   - **Dónde se corta un modelo.** Se detiene antes de la orden que lo sigue.
   - **La razón de una orden.** Si la orden trae su razón («porque es un IAM»,
     «because this is a STEMI»), esa razón es la rationale.
   - **Los hallazgos compactos.** Se conservan hasta la primera orden o
     reevaluación, aunque estén en la misma oración: «hipoglicemia, dextrosa
     25 g EV, espero que…» registra «hipoglicemia» como modelo, y la orden, la
     expectativa y la reevaluación quedan en sus propias categorías.
   - **Dónde termina una cláusula.** En la coma, el punto y coma o los dos
     puntos, y donde el propio lector abre una cláusula para una intención
     declarada («Given the hypoxemia I will start NIV», «como está hipotenso le
     voy a pasar volumen»). Se reutiliza su patrón (`_DECLARED_INTENTION`), no
     una lista nueva.
4. **Asimetrías EN/ES del razonamiento registrado:**
   - **Vocabulario de hallazgos.** Faltaba en español lo que el inglés sí tenía:
     «falla», «infección», «lactato», «llene capilar», «estado mental»,
     «disnea»… Faltaban en ambos idiomas «exhaustion/agotamiento» y
     «asthmatic/asmático».
   - **Enunciados causales en inglés.** No había captura como la española (so,
     which is why, suggests…). Ahora la hay.
   - **«por eso» y equivalentes.** Faltaban en la captura causal española.
   - **Consecuencia con su causa.** «He takes a beta-blocker, which is why he is
     not responding» queda como un modelo, igual que «Toma betabloqueador, por
     eso no responde».
   - **«porque» como rationale.** No se registraba como la razón declarada,
     mientras «because» sí. Eran 21 decisiones del corpus.
   - **Valoración de la respuesta.** Se agregó en español.
   - **El propósito de una orden termina donde empieza otra categoría.** «para
     bajar la precarga, espero que mejore la disnea y reevalúo…» registra
     «bajar la precarga», igual que ya hacía la captura del objetivo («busco…»,
     «the aim is…»). Ambas aceptan ahora «reevalúo» con tilde.
   - **Una orden dentro de la razón no se lleva la expectativa.** «Because of
     the poor perfusion I will give 500 mL … to raise the blood pressure»
     perdía «raise the blood pressure», porque la razón todavía contenía la
     orden; en español se conservaba.
   - **Foco de la reevaluación y alta en inglés.** Foco: `app.py` (formulario
     guiado e intérprete). Alta: `family_parser.py`, que ahora reconoce el
     seguimiento que nombra primero al servicio y el aviso de regreso con su
     lista completa.

### Qué no cambió y queda registrado

- **1 diferencia pareada que queda (guion 5, decisión 9).** El inglés escribe
  «because of the work of breathing» y lo registra como razón. El español
  escribe «por el trabajo respiratorio» y arrastra el modelo previo. «por» es
  demasiado ambiguo en español para tratarlo como causal. Las dos lecturas son
  fieles a lo escrito.
- **«since» en inglés** no se lee como razón, porque también es temporal
  («hypotensive since arrival»).
- **Seguimiento pegado al alta.** «With cardiology follow-up» o «con control en
  policlínico» dentro de la misma orden de alta no se registran como indicación,
  en ninguno de los dos idiomas. Es anterior a este ciclo; queda en la cola.
- **Encontrado al probar, anterior al ciclo, igual en HEAD:**
  - en inglés, «to reduce the congestion and I will recheck…» registra «reduce
    the congestion and I will» como expectativa (el patrón de efecto no termina
    en «and I will»);
  - el vocabulario de hallazgos es una lista cerrada: «Hyperkalemia with peaked
    T waves» e «Hiperkalemia con T picudas» no se leen como modelo en ninguno de
    los dos idiomas, y el gate lo pregunta.

  Quedan en la cola (DF-11); el corpus de validación (DF-6) medirá cuánto pesan.
- **Correcciones ortográficas** («rythm» → «rhythm», «urianalysis» →
  «urinalysis»). Siguen cambiando la cita, sin cambiar el sentido. Dos
  regresiones las fijan (v0814, v0816); no eran parte de los defectos aprobados.

### Lo que encontró la suite completa

La primera corrida completa, con la versión medida arriba, dio 13 fallas. Se
corrigieron por su clase, y la medición se repitió con el código final.

- **12 en `test_the_gate_asks_for_four_things.py`** (6 frases × 2 pruebas).
  - **Qué eran.** Órdenes compactas que nombran las cuatro categorías, como
    «hipoglicemia, dextrosa 25 g EV, espero que recupere conciencia, controlo
    HGT en 15 minutos».
  - **Por qué fallaban.** Antes de DF-7 su «modelo» era la oración entera, orden
    incluida: justo el defecto que DF-7 corrige. La primera versión de la
    corrección descartaba esa oración en vez de cortarla antes de la orden, y el
    gate volvía a retener órdenes completas (la preocupación docente del
    2026-09-23). Además, el propósito de la orden corría hasta el final de la
    oración; antes lo tapaba el modelo defectuoso.
  - **Corrección.** Las de «Causas raíz» sobre los hallazgos compactos, el
    límite de cláusula y el propósito.
- **1 en `test_offline_cases.py`.**
  - **Qué era.** La herramienta de medición del ciclo 1 leía el valor de las
    claves de proveedor para negarse a correr (commit aae45a9).
  - **Corrección.** Ahora mira sólo los nombres y nunca lee un valor.
- **Medición repetida con el código final.** Los mismos números de la tabla y
  ninguna de las 238 decisiones registradas cambió: estas clases no aparecen en
  el corpus de ensayo.

### Latencia

- **Por llamada, código final.** La extracción pasa de 3,4 ms a 4,1–4,4 ms por
  orden: mejor de 5 pasadas sobre las 192 órdenes del corpus, en el mismo
  equipo. Ese milisegundo es la consulta al lector para decidir qué es una
  orden.
- **Por encuentro.** Se jugaron los guiones ES 1–4 alternando el código de HEAD
  y la versión medida arriba, dos veces cada uno:

  | Corrida | Antes (HEAD) | Después |
  |---|---|---|
  | 1 | 95,0 s | 93,3 s |
  | 2 | 99,4 s | 105,7 s |

  La diferencia de medias (+2,3 s, 2 %) es menor que la variación entre dos
  corridas del mismo código (4,4 s antes y 12,4 s después).
- **Corpus completo con el código final.** 488 s (ES) y 494 s (EN), frente a
  486 s y 487 s de la versión anterior.
- **Conclusión.** El aumento de la corrida completa frente al ciclo 1 (393 s →
  486–501 s) vino del entorno, no del cambio.

### Pruebas

- **`test_reasoning_fidelity_classes.py` (nuevo, 32 casos).** Cada clase se prueba
  en ambos idiomas con frases escritas para la prueba, no copiadas del corpus
  (§57).
- **Tests focalizados de razonamiento y lectura:** 366, todos pasan. Incluyen
  `test_spanish_working_model`, `test_working_model_recognition` y
  `test_the_twenty_in_english`.
- **Regresiones:** 56 de 56 pasan.
- **Suite completa, código final (4 shards):** 4696 pasan, 77 omitidas y 2
  xfail, sin fallas.

## Ciclo 3 · DF-10: el alta conserva el plan con que se escribe (2026-09-27)

**Defecto.** «Discharge her with cardiology follow-up» y «La doy de alta con
control en policlínico» ejecutaban el alta, pero el seguimiento no quedaba
registrado, en ninguno de los dos idiomas. El mismo seguimiento sí se
registraba cuando iba como elemento aparte («…, control urológico»).

**Causa raíz.** El lector parte cada oración en fragmentos por comas y
conjunciones. «Con control…» / «with … follow-up» queda dentro del fragmento
del alta, y ese fragmento sólo produce la disposición: el complemento se
descartaba en silencio.

**Corrección** (`family_parser.py`, por clase):

- **El plan escrito dentro de la orden de alta.** Cuando un fragmento produce un
  alta a domicilio, cada «with»/«con» puede abrir su plan. Se registra como
  indicación al paciente sólo lo que el propio lector ya reconoce como
  indicación en una lista (`_DISCHARGE_ADVICE`). Lo demás queda como antes:
  «con su esposa», «with his wife», «con paracetamol».
- **Artículo.** `_DISCHARGE_ADVICE` acepta un artículo delante: «a follow-up
  appointment», «una cita».
- **Orden del plan.** La indicación que cierra una oración (aviso de regreso,
  signos de alarma) se registra después de lo que la oración dice antes. Así
  el seguimiento y el aviso quedan en el orden en que se escribieron.
- **Sólo el alta.** Una hospitalización «con control de glicemia» no cambia:
  es una indicación intrahospitalaria, no un plan para la casa.

**Consecuencia corregida en el mismo cambio.** Si un alta sin razonamiento
queda retenida, el mensaje de la orden retenida enumera lo que la orden también
trae. Antes decía «These medications have not been administered» para
cualquier cosa. Con el seguimiento recuperado, ese mensaje habría anunciado un
seguimiento como un medicamento no administrado. Ahora dice qué es cada
elemento (`unexecuted_items.held_messages`), con su traducción al español.

### Antes y después

**Frases escritas para la prueba, EN y ES.** Son 10 altas con plan.

- **Antes:** el seguimiento se perdía en 7.
- **Después:** se conserva en 9, en el orden del texto, sin duplicarse cuando
  además va en la lista.
- **La décima** («OK to discharge with…») no se reconoce como alta. Es otro
  defecto, registrado abajo.
- **Las 2 frases sin plan** no cambian, y el alta se ejecuta igual en todas.

| Frase (ejemplo) | Antes | Después |
|---|---|---|
| Discharge him home with orthopedic follow-up in two weeks. | — | orthopedic follow-up in two weeks |
| Lo doy de alta con control en policlínico de traumatología en dos semanas. | — | control en policlinico de traumatologia en dos semanas |
| Alta con seguimiento por neurología y volver si reaparecen los síntomas. | volver si… | seguimiento por neurologia, volver si… |
| Discharge her with cardiology follow-up and return if the palpitations come back. | return if… | cardiology follow-up, return if… |

**Corpus de ensayo** (mismo corpus, semilla 3000, 0 llamadas de IA): cambió
una sola decisión, y es la misma en los dos idiomas. Es el guion 18, decisión 3,
del caso `acs_66f_nonst`:

- ES «La doy de alta con control ambulatorio» registra ahora «control
  ambulatorio».
- EN «Discharge her with outpatient follow-up» registra ahora «outpatient
  follow-up».

Nada más cambió: 96/96 órdenes, 0 retenciones no previstas, las mismas
categorías de razonamiento y la misma diferencia pareada.

**Pruebas.**

- **`test_a_discharge_keeps_the_plan_it_is_written_with.py`:** 17 casos EN/ES.
  Cubren:
  - el seguimiento conservado y el alta ejecutada;
  - el orden del plan;
  - que no se duplique;
  - que no invente un plan;
  - que la hospitalización no cambie;
  - la rationale conservada;
  - el mensaje de la orden retenida y su traducción.
- **Pruebas del alta y del lector:** 398 pasan.
- **Regresiones:** 56 de 56 pasan.

### Encontrado y no corregido (registrado)

Son defectos distintos de DF-10; se registran en la cola.

- «OK to discharge with…» no se reconoce como alta.
- Una receta unida al alta con «with»/«con» («with ibuprofen», «con
  paracetamol») se pierde. Como elemento aparte de la lista, se registra.
- «Con hora en policlínico» (hora = cita) no se reconoce como seguimiento.
- Cuatro líneas del mensaje de la orden retenida no tienen traducción al
  español: «I recognised…», «Still to state…», «In your own words…» y «What you
  already wrote is kept.».
