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

## Ciclo 4 · DF-16a y DF-16b: listas de órdenes y repeticiones (2026-09-28)

**Defectos.** Se encontraron en el ciclo 3 con frases escritas para la
herramienta de validación. El docente autorizó corregir las **clases**, no las
frases, en inglés y en español.

- **DF-16a (listas).** «Monitor, vía venosa y oxígeno por mascarilla a 8 L/min»
  ejecutaba sólo la vía venosa: el monitor no se ordenaba y el oxígeno quedaba
  como un control de la saturación.
- **DF-16b (acción + repetición + condición).** «Salbutamol 5 mg nbz, repetir
  cada 20 minutos si persiste el broncoespasmo» no ejecutaba nada. La condición
  de la repetición convertía toda la oración en un plan condicional, y el
  Management Trace citaba la orden como modelo de trabajo.

### Causas raíz

**DF-16a.**

1. **«Monitor» se leía como el verbo «monitorizar» sin objeto.** No ordenaba
   nada. «Monitor cardíaco» volvía como orden no reconocida, y esa aclaración
   retenía todo el envío. El verbo, además, pasaba a los elementos siguientes:
   el oxígeno se convertía en «controlar la saturación».
2. **Un elemento de soporte sin verbo propio se descartaba en silencio** dentro
   de una lista: «vía venosa», «régimen cero», «sonda Foley», «IV access»,
   «NPO».
3. **La vía escrita una vez al final llegaba sólo a la última dosis** («salbutamol
   5 mg + ipratropio 0.5 mg nbz»). Además, el plural de la vía («nebulizados»,
   «endovenosos») no se reconocía.

**DF-16b.**

4. **La repetición no tenía clase propia.** La condición de la repetición se
   aplicaba a la oración entera, y un intervalo o un número de veces sin
   condición («repetir cada 20 min por 3 veces») volvía como orden no
   reconocida.

### Corrección (por clase)

- **`family_parser.py`, monitor.** «Monitor», «monitorización», «cardiac
  monitoring», «monitor cardíaco», «continuous monitoring», escritos solos o
  como elemento de una lista, son la orden de monitorizar
  (`_MONITOR_ORDER`). «Monitorizar la saturación», «Monitor BP, HR and SpO2»
  siguen siendo controles.
- **`family_parser.py`, oxígeno.** Con flujo o dispositivo, «oxígeno» se
  administra; ya no es la saturación que se vigila.
- **`family_parser.py`, soporte sin verbo en una lista.** Cuando el elemento no
  tiene verbo propio, se lee como orden (`_verbless_support`):
  - vía venosa, VVP, acceso venoso, «IV access», «large-bore IVs», «two IVs»;
  - régimen cero, NPO;
  - sonda Foley, vesical, nasogástrica.

  Esto aplica sólo **dentro de una lista o de un envío con varias oraciones**.
  Una descripción («permeable», «ya tiene», «in place», «funcionando») no es
  una orden.
- **`family_parser.py`, vía compartida.** Una vía escrita después de varias
  dosis llega a cada dosis anterior que no tiene vía propia, también si hay un
  fármaco no modelado entre ellas (`_share_trailing_route`). No cruza una
  secuencia («luego», «then», «después»): allí la vía es de la dosis que la
  lleva.
- **`shared_order_language.py`.** Se reconoce el plural de cada vía:
  endovenosos, intravenosas, intramusculares, orales, nebulizados, inhalados,
  subcutáneos, intraóseos, intranasales.
- **`family_parser.py`, repetición.** Una instrucción de repetición escrita
  después de su orden se separa de ella:
  - **La orden se ejecuta ahora.**
  - **La repetición queda registrada con su clase propia** (`kind: "repeat"`).
    Guarda la orden que repite, el intervalo (`every_min`) o la espera
    (`after_min`), el número de veces (`count`) y la condición.
  - **La condición es de la repetición, nunca de la orden.**
  - **Una repetición que espera una condición y viene sola** («Si no mejora,
    repetir adrenalina 0.5 mg im a los 5 minutos») es un plan: no ejecuta nada.
  - **«Volver a nebulizar / administrar / dar …»** es una repetición. «Volver a
    consultar» sigue siendo indicación.
  - **`repeat_structure`** se exporta para la traza y la herramienta de
    validación.
- **`family_parser.py`, condición después de una orden sin verbo.** Es la
  misma clase: la condición convertía en plan toda la acción. «Paracetamol 1 g
  ev y ondansetrón 4 mg ev si vomita» y «NS 1 L IV and norepinephrine if still
  hypotensive» quedaban enteras como plan condicional, sin ejecutar nada. Con
  verbo («Doy …») ya se separaban. Ahora la orden sin verbo, abreviatura de
  ficha, también se ejecuta, y sólo lo condicionado queda como plan.
- **`unexecuted_items.py`, `language.py`, `report_language.py`.** La página
  dice «Registrado como instrucción de repetición, no ejecutada ahora: «…»».
  Si la orden queda retenida, dice «También en esta orden, una instrucción de
  repetición: «…»». En la traza aparece como «instrucción de repetición; no se
  ejecutó ahora».
- **`app.py` (`extract_explicit_reasoning`).** El modelo de trabajo nunca es
  una orden, una repetición ni la condición de una repetición:
  - una apreciación escrita antes de la orden se corta donde empieza la orden
    («Persiste la hipotensión»);
  - un fragmento que empieza por «si/if/unless/en caso de» no se toma como
    modelo.

### Qué no cambió (a propósito)

- **«Vía venosa» escrita sola** sigue sin ser una orden. Puede describir la vía
  que el paciente ya tiene (decisión del 2026-09-26, `test_hypoglycemia_reader`).
- **«Monitorizar PA, FC y saturación cada 15 minutos»** sigue siendo control de
  signos vitales.
- **Nada se inventa.** Una dosis sin vía escrita queda sin vía, y la página la
  pregunta.
- **«Repito salbutamol 5 mg nbz»**, sin intervalo ni condición, es una dosis que
  se da de nuevo ahora.
- **«Give a second dose of epinephrine if there is no response»** y **«Start
  oxygen NC 3 L/min, if saturation falls»** siguen siendo planes condicionales.

### Antes y después

**Frases escritas para reproducir los defectos** (40, EN y ES; script
`df16_probe.py`, fuera del repositorio):

- **31 cambian, todas en la dirección esperada.** Las 9 que no cambian son las
  frases de control.
- **No cambian:** descripciones de vías, controles de signos vitales, el plan
  condicional y la repetición inmediata.

| Frase | Antes | Después |
|---|---|---|
| Monitor, vía venosa y oxígeno por mascarilla a 8 L/min | vía venosa + control de saturación | monitor + vía venosa + O2 mascarilla simple 8 L/min |
| Monitor cardíaco + vía venosa + O2 por naricera a 3 L/min | aclaración (retiene todo) + vía + O2 | monitor + vía + O2 naricera 3 L/min |
| Vía venosa y régimen cero | — | vía venosa + régimen cero |
| Monitor; IV access; oxygen by non-rebreather at 15 L/min | sólo O2 | monitor + vía + O2 con reservorio 15 L/min |
| Salbutamol 2.5 mg y bromuro de ipratropio 500 mcg nebulizados | dos broncodilatadores sin vía | los dos nebulizados |
| Paracetamol 1 g y ketorolaco 30 mg ev | paracetamol sin vía | los dos IV |
| Salbutamol 5 mg nbz, repetir cada 20 minutos si persiste el broncoespasmo | nada; plan condicional; la orden citada como modelo | salbutamol ejecutado; repetición {cada 20 min; si persiste…} |
| Morfina 2 mg ev, repetir cada 5 min hasta EVA menor de 4 | morfina + aclaración (retiene) | morfina; repetición {cada 5 min; hasta EVA…} |
| Epinephrine 0.5 mg IM, repeat in 5 minutes if no improvement | nada; plan condicional | adrenalina IM; repetición {a los 5 min; if no improvement} |
| Doy salbutamol 5 mg nbz y volver a nebulizar si persiste | salbutamol + «volver…» como indicación al alta | salbutamol + repetición |

**Frases nuevas, escritas después del fix** (39, EN y ES; `df16_heldout.py`,
fuera del repositorio). Se escribieron después de corregir y se corrieron una
sola vez, para comprobar que se corrigió la clase y no las frases de desarrollo:

- **Resultado esperado en 34.**
- **En 5 aparece un defecto que no es de DF-16**; queda registrado abajo.
- **8 quedaron como pruebas de regresión.**

**Corpus de ensayo** (mismo corpus, semilla 3000, 0 llamadas de IA):

- **Las 40 grabaciones son idénticas** a las del ciclo 3, decisión por
  decisión (20 ES y 20 EN).
- **Resumen:** 96/96 órdenes ejecutadas, 0 retenciones no previstas y 0
  modelos de trabajo que son una orden, con la misma diferencia pareada.
- **El corpus de ensayo no trae estas formas** (listas sin verbo, repeticiones
  con condición). Por eso la mejora se mide con frases nuevas y el corpus
  sirve para comprobar que nada se deterioró.

### Latencia

| Medida (268 textos: corpus de ensayo + frases de prueba, mediana de 5 pasadas) | Antes | Después |
|---|---|---|
| Lectura de la orden (`parse_family_actions`) | 0,40–0,47 ms | 0,45–0,46 ms |
| Extracción del razonamiento | 3,46–3,53 ms | 3,85–3,97 ms |

El lector no cambia. La extracción del razonamiento suma unos 0,4 ms por texto:
es la consulta extra al lector para cortar una apreciación donde empieza la
orden. El corpus completo tardó 376 s (ES) y 379 s (EN).

### Pruebas

- **`test_lists_and_repeats_keep_every_order.py` (nuevo, 60 casos).** Cada
  clase se prueba en ambos idiomas con frases escritas para la prueba, más 8
  guardas del conjunto escrito después del fix. Incluye una prueba por la
  página real (`tools_tanda20.rehearse`, asma): el monitor, la vía, el oxígeno
  y los broncodilatadores se ejecutan, la repetición queda en la traza, y el
  salbutamol no es el modelo de trabajo.
- **Archivos de prueba del lector y de la traza:** los 69 existentes pasan
  (1788 pasan y 2 xfail, con las 50 pruebas nuevas de la primera versión).
- **Regresiones:** 56 de 56 pasan.
- **Suite completa (4 shards).**
  - **Primera corrida:** 5 fallas dependientes del orden. La prueba nueva por la
    página real dejaba `MRS_OFFLINE_CASES` en el entorno del proceso. Se
    reprodujo y se corrigió con `monkeypatch`.
  - **Segunda corrida, commit `939978a`:** 4877 pasan, 77 omitidas, 2 xfail y
    0 fallas.
  - **Ese commit es el baseline del piloto:** `validation/pilot_v1/PILOT_BASELINE.md`.

### Encontrado y no corregido (registrado)

No están relacionados con DF-16a/b, o no cumplen los 8 criterios del §71. Se
registran en el manifiesto de defectos conocidos del piloto
(`validation/pilot_v1/KNOWN_DEFECTS.md`).

- **Vía escrita antes del fármaco, sin verbo, en inglés.** «IV morphine 4 mg»,
  «Nebulized albuterol 2.5 mg», «Oral paracetamol 1 g» e «IV fluids 1 L»
  vuelven como orden no reconocida, y la aclaración retiene el envío. Con verbo
  («Give nebulized albuterol») sí se leen. Es anterior a DF-16. Importa para la
  fase en inglés del piloto; en español la vía va después del fármaco.
- **Un fármaco sin verbo y sin dosis no es una orden.** «Morfina ev»,
  «Salbutamol nbz» siguen la regla deliberada «un nombre de fármaco sólo es
  orden con un verbo o una dosis». Dentro de una lista se pierde sin aviso.
  Seguido de una repetición, toda la oración queda registrada como instrucción
  de repetición; antes no quedaba nada.
- **«Mascarilla de alto flujo»** pide aclarar el dispositivo (ambiguo entre
  cánula de alto flujo y mascarilla). No es un defecto de listas.
- **«As needed / según necesidad».** La repetición guarda el intervalo y el
  número de veces, pero no la condición; «SOS/PRN» sí quedan como condición.
  Ninguna es una condición clínica explícita (VC-3). El texto se conserva
  literal.
- **«Repeat the troponin in 3 hours» escrita sola** pide la troponina ahora:
  comportamiento anterior, sin cambio. En cambio, «Troponina ahora y repetir en
  3 horas» ejecuta la troponina y registra la repetición.
- **«Vigilar diuresis y estado mental»** se cita como modelo de trabajo:
  anterior, de la misma familia que DF-7.

## Ciclo 5 · KD-01: la vía escrita antes del fármaco (2026-09-28)

Autorización docente del 2026-09-28 (§12, §24, §42, §43), DF-19.

### El defecto y su causa

- **La clase.** Una orden en inglés sin verbo, con la vía antes del fármaco:
  «IV morphine 4 mg», «Oral paracetamol 1 g», «Nebulized albuterol 2.5 mg».
- **Qué pasaba.** Se devolvía como orden no reconocida y retenía el resto del
  envío. La misma orden escrita con el fármaco primero se leía bien.
- **La causa** (`family_parser.py`, rama sin verbo). Una orden sin verbo tenía
  que empezar por un fármaco, una cantidad o una abreviatura.
  - Una vía delante sólo se saltaba antes de las abreviaturas; por eso «IM
    epinephrine 0.5 mg» ya funcionaba.
  - Delante de cualquier otro fármaco del catálogo no se saltaba.
  - Tampoco se reconocían las vías escritas como palabra («oral»,
    «nebulized», «intravenous»).
  - La dosis y la vía ya se leían en cualquier posición: el defecto era sólo
    reconocer dónde empieza la orden.
- **La misma causa, dentro de una lista.** En «Aspirin 300 mg, IV morphine
  4 mg», la vía de la morfina se tomaba como vía escrita después de la lista
  (DF-16a), y la aspirina quedaba IV. Ocurría ya en el baseline español.

### Corrección (por clase)

- **Qué vías.** Una palabra de vía que el lector ya lee
  (`shared_order_language.ROUTE_BEFORE_THE_DRUG`, **ninguna vía nueva**),
  seguida de un fármaco que conoce, abre la orden.
- **La vía queda donde fue escrita**, y la dosis y la vía se leen como siempre.
  La orden es exactamente la misma que con el fármaco primero; las pruebas lo
  comparan frase por frase.
- **En una lista, esa vía es sólo de su fármaco.** Nunca alcanza la dosis
  anterior. La vía escrita después de una lista de dosis sigue alcanzando a
  cada dosis (DF-16a).
- **Un «in» suelto no se salta (KB-02).** Antes de un fármaco es primero una
  preposición; la vía nasal se lee después de la dosis o escrita
  «intranasal».

### Antes y después (frases escritas para esta corrección)

| Frase | Antes | Después |
|---|---|---|
| IV morphine 4 mg | retenida: no reconocida | morfina 4 mg IV |
| PO acetaminophen 1 g | retenida | paracetamol 1000 mg PO |
| IV ceftriaxone 2 g | retenida | ceftriaxona 2000 mg IV |
| Oral paracetamol 1 g | retenida | paracetamol 1000 mg PO |
| Nebulized albuterol 2.5 mg | retenida | albuterol 2.5 mg nebulizado |
| Inhaled salbutamol 5 mg | retenida | albuterol 5 mg inhalado |
| IV furosemide 40 mg · IV naloxone 0.4 mg | retenidas | IV, con su dosis |
| EV morfina 4 mg · VO paracetamol 1 g · NBZ salbutamol 2.5 mg | retenidas | leídas (español) |
| IM epinephrine 0.5 mg | adrenalina IM | igual |
| Aspirin 300 mg, IV morphine 4 mg | **aspirina IV** + morfina IV | aspirina **sin vía**: se pregunta; morfina IV |
| IV morphine 4 mg every 10 minutes if pain persists | **nada, sin aviso** | plan condicional, como con el fármaco primero |

**Negativos: no cambian.**

- **Nada se vuelve orden ni vía:**
  - «Oral intake is poor»;
  - «IV access now»;
  - «Neb treatments helped before»;
  - «IM injection site is clean»;
  - «Oral paracetamol 1 g was given at home».
- **Sin dosis no se inventa ninguna:** «IV morphine», «Oral paracetamol» y
  «EV morfina» siguen sin ser órdenes (KD-02).
- **Dos vías para un fármaco** («IV morphine 4 mg PO») no eligen ninguna:
  se pregunta.
- **Dos fármacos tras una vía** piden separarlos.
- **La vía de la vía venosa no alcanza al fármaco siguiente:** en «IV access,
  morphine 4 mg», la morfina queda sin vía.
- **Siguen como estaban, por otras causas:**
  - «IV fluids 1 L» y «Normal saline 1 L IV»: fluido nombrado en palabras,
    **KD-15** nuevo, no corregido;
  - «SC insulin 10 units»: insulina no modelada;
  - «IV ondansetron 4 mg»: no modelado;
  - «IN naloxone 2 mg»: **KB-02**.

### Corpus de ensayo

Mismo corpus, semilla 3000, 0 llamadas de IA.

- **Las 40 grabaciones, 20 ES y 20 EN, son idénticas a las del ciclo 4**,
  decisión por decisión: 96/96 órdenes ejecutadas en cada idioma, 0
  retenciones no previstas, 0 modelos de trabajo que son una orden.
- **Lo único distinto** es el tiempo y el campo `plans` de la traza, que no
  existía cuando se grabó el ciclo 4.
- **El corpus no trae la clase.** La mejora se mide con las frases de arriba,
  y el corpus comprueba que nada se deterioró.

### Latencia

| Medida (268 textos, mediana de 5 pasadas, con la máquina ocupada) | Antes | Después |
|---|---|---|
| Lectura de la orden (`parse_family_actions`) | 0,57 ms | 0,55 ms |
| Extracción del razonamiento | 4,03 ms | 4,12 ms |

Iguales dentro del ruido. Las cifras absolutas son mayores que las del ciclo 4
porque la medición corrió en paralelo con el corpus.

### Pruebas

- **`test_a_route_written_before_the_drug.py` (nuevo, 53 casos):**
  - la clase en EN y ES;
  - igualdad frase por frase con el fármaco primero;
  - sólo vías que el lector ya lee;
  - negativos;
  - la vía en una lista;
  - ejecución en el motor;
  - la orden no es el modelo de trabajo;
  - una prueba por la página real, en inglés, leída desde el Management Trace
    guardado.
- **Archivos de prueba del lector y de la traza:** 1888 pasan y 2 xfail.
- **Regresiones:** 56 de 56.
- **Registro:** `corrections_registry` C-2026-09-28-02. KD-01 sigue presente en
  el SPANISH PILOT BASELINE y está corregido desde el ENGLISH VALIDATION
  BASELINE (`validation/BASELINES.md`).

## Ciclo 6 · DF-22: las nueve clases CRITICAL del lector (2026-09-28)

Aprobado por el docente el 2026-09-28: corregir por clase, no por frase, las
nueve clases CRITICAL de la auditoría del Trace del ciclo 5
(`AUDITORIA_TRACE_CICLO5.md`, C01–C09). Todas estaban ya en el SPANISH PILOT
BASELINE (`939978a`), que no se toca: el piloto las mide como fallas nuevas.

**Todas las frases de esta sección son INTERNAL DEVELOPMENT DATA.** Ninguna es
dato de validación externa, y nada aquí estima cuántas órdenes reales de un
residente se leen bien: eso lo mide el piloto.

### Causas raíz y correcciones (por clase)

| Clase | Forma | Causa raíz | Corrección |
|---|---|---|---|
| C01 | «X, si no responde, Y» | Sin nada entre la coma y «si», toda la oración quedaba condicional | Si tras la condición viene una instrucción (orden, verbo, fármaco, o una abreviatura que es orden con un verbo prestado), X corre ahora e Y queda como plan. Una X escrita como orden que el lector no ejecuta se pregunta, no se pierde. La condición escrita entre una orden y su repetición es de la repetición |
| C02 | «Diagnóstico: orden» | «:» no cortaba nada; la orden quedaba en el rótulo | Un rótulo que no ordena nada se salta; nunca tras una condición («si», «PRN», «SOS»), un tiempo («una vez estable», «post-intubación»), una alternativa («plan B»), algo pendiente, una retención («evitar»), una lista de medicamentos o alergias. Un cambio del paciente o una duda sólo es contingencia si es todo el rótulo («Persiste:», «Refractory:»); con el hallazgo es la razón de la orden («Hipotensión persistente:») |
| C03 | «Ahora X y luego repetir…» | La palabra de tiempo inicial impedía leer X, y la repetición archivaba todo | «Ahora», «primero», «stat», «inmediatamente» se quitan al inicio de una orden; la repetición se atribuye a X |
| C04 | «Suspende A y cambia a B 500 mL» | «cambia a ringer» se leía como perífrasis de «suspender» | La perífrasis no se aplica ante el nombre de una solución; «hold», «D/C», «cierra», «corta», «para» ante un cristaloide suspenden |
| C05 | Destino «con/on» tratamiento | La rama de destino devolvía sólo el destino | Lo escrito con el destino se ejecuta con él, con o sin dosis; un fármaco que no se puede ejecutar así se pregunta; «con su esposa» no pregunta nada. La receta del alta queda como receta (KD-06) |
| C06 | «Activo hemodinamia / código infarto» | «activo» no era verbo de orden | «Activo/activamos» ante un servicio o un código es activar |
| C07 | «Por <razón> instalo …» | El verbo en primera persona no abría la orden | Tras «Por/Ante/Dado…», un verbo de orden en primera persona abre la orden; no si el sujeto es otra persona («el paramédico inició») |
| C08 | TXA «en 10 min» | El motor no aceptaba duración para el TXA y rechazaba todo el paquete urgente | Se acepta y se registra; como todo fármaco con tiempo escrito, esos minutos pasan si no hay reevaluación |
| C09 | Orden + «satura 86 % con la naricera» | El hallazgo heredaba el verbo y era una segunda orden | Un signo vital con su valor, sin verbo propio, es un hallazgo |

### Antes y después: las 90 frases de la auditoría

Mismo guion que la auditoría (`probe_59g`), parser, intérprete de la página y
motor.

| Medida | Antes (HEAD del ciclo 5) | Después |
|---|---|---|
| Frases que cambian | — | 24 de 90 |
| Problemas del lector (todas las clases) | 120 | 98 |
| Órdenes esperadas que faltaban (MISSING) | 39 | 24 |
| Frases que el motor ejecuta | 35 | 45 |

Los 24 cambios se revisaron uno por uno: todos corrigen la clase o hacen más
honesta la respuesta (una pregunta concreta en vez de «not recognized», o
«no reconocido» en vez de nada). Ninguno empeora una lectura correcta.
Quedan, fuera de DF-22: «2 U de GR», «pip-tazo», el protocolo de transfusión
masiva, «evalúo PA» y la VCI.

### Medición ciega (1): 162 frases que el lector nunca vio

Un agente escribió 162 frases nuevas (9 clases × 18: 12 positivas y 6
negativas, mitad en inglés y mitad en español) **sin acceso al código, a las
frases de la auditoría ni a las de desarrollo**, con lo que debía ejecutarse y
lo que no. Se midieron **una vez**, antes de mirar sus fallas.

| 108 positivas | Lector antes | Lector después | Motor después |
|---|---|---|---|
| Correctas | 12 | 42 | 32 |
| Retenidas con una pregunta | 45 | 32 | 62 |
| Perdidas sin aviso | 48 | 32 | 12 |
| Ejecución falsa | 3 | 2 | 2 |

| 54 negativas | Lector antes | Lector después | Motor después |
|---|---|---|---|
| Nada ejecutado de más | 50 | 50 | 50 |
| Ejecución falsa | 4 | 4 | 4 |

- **Las cuatro negativas falsas eran las mismas antes y después, y todas
  C08:** el ácido tranexámico leído en lo que hizo el paramédico, en un
  pensamiento («estaba pensando en dar…») o en una retención («no
  corresponde…»).
  - **Antes, el motor las tapaba:** rechazaba la duración del fármaco y con
    ella todo el paquete.
  - **La corrección C08 las destapó:** aceptada la duración, se ejecutaban.
- **Qué dice.** La corrección generaliza a medias: las lecturas correctas se
  triplican y las pérdidas silenciosas bajan un tercio, pero la mayoría de las
  frases nuevas todavía no se ejecuta completa. En el motor, 62 de 108 quedan
  retenidas con una pregunta: honesto, pero no es lo que el residente quería.
- **Por qué.** Casi todo lo retenido o perdido cae en vocabulario de otras
  clases, no en la forma de la oración: «2 U de GR O negativo», «O-neg», el
  protocolo de transfusión masiva, «amp of D50», nitroglicerina SL o en
  infusión, heparina por kilo, «epi drip», «Page GI», «Call a STEMI code».
- **Tres fallas eran de mis propias correcciones de clase** y se corrigieron
  después de medir (lo que invalida esas frases como ciegas):
  - C05 exigía una cantidad de una lista corta de campos: se perdían en
    silencio la heparina en infusión, el salbutamol continuo, el marcapaso y
    la naloxona escritos con el destino;
  - C02 contaba «posterior» (la pared, el infarto) como palabra de tiempo;
  - C01 no reconocía «we go to RSI» ni un fármaco solo como instrucción, ni
    preguntaba por una X ilegible.
- **Las ejecuciones falsas de C08 también se corrigieron después de medir.**
  Sin un verbo del residente, el ácido tranexámico y las medidas de hemorragia
  pasan la misma prueba de historia que cualquier otro fármaco.

### Medición ciega (2): 48 frases nuevas para las clases re-corregidas

Un segundo agente, con las mismas condiciones, escribió 48 frases para las
cuatro clases corregidas después de la primera medición (C01, C02, C04 y C05;
8 positivas y 4 negativas por clase, mitad en cada idioma). Se midieron **una
vez**.

| 32 positivas | Lector antes | Lector después | Motor después |
|---|---|---|---|
| Correctas | 1 | 11 | 9 |
| Retenidas con una pregunta | 17 | 15 | 19 |
| Perdidas sin aviso | 14 | 6 | 4 |
| Ejecución falsa | 0 | 0 | 0 |

| 16 negativas | Lector antes | Lector después | Motor después |
|---|---|---|---|
| Nada ejecutado de más | 16 | 15 | 15 |
| Ejecución falsa | 0 | 1 | 1 |

- **La negativa falsa era una regresión de C02:** «Con HGT estables sobre 150:
  suspender SG 10% y dejar SG 5% a 70 mL/h» ejecutaba el cambio en el acto. Un
  umbral o un estado por alcanzar en el rótulo lo hacen condición; corregido
  después de medir.

### Medición ciega (3): 48 negativas, para buscar ejecuciones falsas

Un tercer agente escribió 48 frases que **no** deben ejecutar lo que nombran,
en seis formas (8 por forma, mitad en cada idioma): un rótulo con dos puntos,
lo que otro ya hizo, un pensamiento o una pregunta, la decisión de no dar, la
historia o los fármacos de la casa, y un plan para después. Cinco traen además
una orden de ahora. Se midieron **una vez**, con el código que ya incluía las
correcciones anteriores.

| 48 negativas | Lector antes | Lector después | Motor después |
|---|---|---|---|
| Nada ejecutado de más | 44 | 44 | **48** |
| Lectura falsa | 4 | 4 | 0 |

- **El motor no ejecutó nada de más en ninguna.** Las cuatro lecturas falsas
  del lector quedaron retenidas con una pregunta.
- **Una era regresión de C02:** «Con angioTAC positivo: enoxaparina 1 mg/kg»
  leía la anticoagulación como orden de ahora. Un resultado que puede no haber
  llegado hace condición al rótulo, como un umbral; corregido después de
  medir. «Troponina positiva: aspirina 300 mg», sin «con», sigue siendo la
  razón de una orden de ahora.
- **Las otras tres ya estaban en el HEAD del ciclo 5.**
  - Una condición escrita como rótulo sin «si»: «New crackles or sats under
    90%…:», «Sugar still under 70 at the 15-min recheck:». El rótulo ya no se
    salta, pero lo que sigue se lee como orden de ahora.
  - Una retención escrita después del fármaco: «y alteplase 100 mg tampoco por
    ahora».
  - Quedan en el registro de deuda técnica (TD-14).
- **De las cinco órdenes de ahora, una corrió** (el oxígeno después de lo que
  hicieron los paramédicos). Las otras cuatro quedaron retenidas con una
  pregunta: «Rx de tórax portátil altiro», «get a second 18 gauge in»,
  «Pidan ELP y creatinina» y un salbutamol tras una duda.

### Correcciones posteriores a las mediciones ciegas

Cada una corrige una regresión del ciclo 6 o una falla que una corrección de
DF-22 destapó (regla §64). **Ninguna se re-midió a ciegas:** los números que
siguen son post hoc, sobre frases ya vistas.

| Qué | Antes | Después |
|---|---|---|
| Ácido tranexámico en una historia, un pensamiento o una retención (C08) | se ejecutaba | no se ejecuta |
| Lo unido con «y/and» a lo que hizo el equipo prehospitalario: «Medic already gave TXA… and put on a tourniquet», «el paramédico ya dejó 2 VVP y pasó tranexámico…» | se ejecutaba como orden del residente | **se pregunta**: puede ser orden suya, y una pregunta no la pierde. Con el residente como sujeto («y pongo 1 L de SF», «and I place…») corre |
| Un rótulo con un umbral, un estado por alcanzar o un resultado (C02) | se ejecutaba lo que seguía | se lee como antes del ciclo |
| La vía por la que pasa un suero: «SF 500 mL por VVP», «pasar 1 L de Ringer por vía venosa periférica», «500 mL NS via the PIV», «through the IV line» | **el bolo se perdía sin aviso y se instalaba una vía** (ya en el HEAD; C01 lo destapó) | es la vía del suero; «instalar VVP» y «2 VVP» siguen pidiendo la vía |

### Revisión adversarial del diff y comparación con el ciclo 5

Hecho el commit `39bac97`, una revisión adversarial del código (un agente sin
parte en las correcciones) encontró **13 problemas que los conjuntos ciegos no
vieron**. Casi todos eran regresiones de las propias correcciones, en órdenes
de primera línea:

| Hallazgo | Ejemplo | En `39bac97` | Ahora |
|---|---|---|---|
| El «stop» de C04 se prestaba a la orden siguiente | «Hold NS, O2 4 L NC» | **oxígeno retirado** | suspende el suero y deja la naricera a 4 L/min |
| «Para» es también «para» | «Para los fluidos: Ringer lactato 500 mL ev» | suspendía el suero | se pregunta, como en el ciclo 5 |
| C07 leía preguntas, dudas y hábitos como órdenes | «Should I give aspirin 300 mg PO?», «por lo general administro aspirina» | **se administraba** | no es orden, como en el ciclo 5 |
| C07 retenía ante prosa en primera persona | «Epinephrine 0.5 mg IM now. We give it 5 minutes…» | **adrenalina retenida** | corre |
| La prueba de historia de C08 alcanzaba a toda pieza sin verbo | «Paracetamol 1 g ev ya que AINE contraindicado», «Urgent TXA 1 g IV», «IV TXA 1 g» | **perdida sin aviso o retenida** | corre |
| El relato prehospitalario retenía órdenes del residente y se saltaba con «, y» | «Remove the EMS dressing and apply a tourniquet…» · «…dejó 2 VVP, y pasó tranexámico» | retenida · **TXA ejecutado** | corre · se pregunta |
| C09 tragaba el «RR» del ventilador | «Intubate, VC/AC, RR 10, PEEP 5…» | la frecuencia se perdía | es la frecuencia de la intubación |
| C02 leía «sedación con X antes de la cardioversión» | «Sedation with etomidate 8 mg IV before synchronized cardioversion» | **sólo corría la cardioversión** | se cita y se pregunta, como en el ciclo 5 |
| C05 iniciaba lo preparado | «…with a norepinephrine infusion ready» | noradrenalina iniciada | no |
| C01 releía la frase entera por cada «si no» | «atropina 1 mg ev, si no, tcp, si no, tcp…» | minutos | milisegundos |
| C07 era cúbico ante una racha de espacios | «Por» + 600 espacios | 3,7 s (126 s con 2000) | como el ciclo 5 |
| Suspender un suero con duración | «Suspender el SF en 30 minutos» | **la página caía** (ya antes; C04 lo hizo más alcanzable) | corre |
| L-F01 contaba como generado un caso autorado que eligió el modelo | — | perdía sus temas de historia | los conserva |
| La respuesta «no sé» tomaba también «no se administra…» | «No se administra adrenalina, SF 500 mL ev» | se trataba como «no sé» | es una orden |

**Todos se corrigieron**, con una prueba cada uno
(`REVIEW` en `test_critical_clinical_language_regressions.py`, y pruebas del
motor, de L-F01 y de la página) y registro C-2026-09-28-09.

**Después se comparó el lector final con el del ciclo 5** sobre los 11 739
textos que tenemos: el corpus de ensayo, las 90 frases, los tres conjuntos
ciegos y los textos de las pruebas. Leen distinto 225. **Se revisaron uno por
uno**, clasificados por lo que el lector deja de leer y lo que empieza a leer:

- **25 dejan de ejecutar algo.** Todos a propósito:
  - el hallazgo que ya no es una segunda orden (C09);
  - el TXA de una historia, un pensamiento o una pregunta;
  - lo que hizo el equipo prehospitalario;
  - una suspensión invertida («pásate a Ringer 1000 mL» se leía como suspender
    el Ringer).
- **120 empiezan a ejecutar algo.** Son las clases corregidas o textos de
  salida de la página que las pruebas citan y nadie escribe como orden.
- **4 cambian las dos cosas y 76 sólo preguntas o planes.** También a
  propósito:
  - un hallazgo ya no pregunta;
  - un plan condicional ahora se guarda;
  - una receta del alta queda como receta.

La comparación encontró además **dos defectos más**, que se corrigieron:

- **La activación de un servicio se prestaba a los fármacos que la seguían.**
  «Activate the cath lab, aspirin 325 mg and ticagrelor 180 mg PO» volvía
  interconsultas la aspirina y el ticagrelor. Estaba así desde antes del ciclo
  6; C02 y C06 lo pusieron delante de más frases.
- **Un plan condicional que nombra el TXA se perdía** («if it keeps oozing,
  run the second gram of TXA over 8 hours»). Venía de la regla de inicio de
  C08.

**Lo que queda del ciclo 5, sin cambio:**

- **Preguntar ante lo ambiguo.** «El paramédico dejó 2 VVP y coloco
  torniquete» se pregunta: sin su tilde, «coloco» es también «colocó».
- **La lentitud ante 2000 espacios seguidos** (≈1 s), que ya tenía el ciclo 5.
- **Citar el texto normalizado** en una pregunta.

**Lección de método.** Los conjuntos ciegos miden la clase que se corrige. Los
efectos de una corrección sobre frases de otras clases los encontraron la
revisión adversarial y la comparación completa con el lector anterior. Las dos
forman parte ahora de cómo se cierra una corrección del lector.

### Los tres conjuntos con el código final (post hoc)

El puntuador contaba una infusión suspendida como dada: «stop the nitro drip»
contaba como nitrato dado, y una infusión leída como suspendida contaba como
iniciada. **Corregido el puntuador**, con el código final:

| Conjunto | Negativas sin ejecución falsa (motor) | Positivas correctas en el motor | Retenidas con pregunta | Perdidas sin aviso | Ejecución falsa |
|---|---|---|---|---|---|
| 1 (162) | **54/54** (medido una vez: 50) | 40/108 | 62 | 5 | 1 |
| 2 (48) | **16/16** (medido una vez: 15) | 9/32 | 19 | 4 | 0 |
| 3 (48 negativas) | **48/48** (lector: 45; las 3 de arriba, retenidas) | — | — | — | — |

- **La única ejecución falsa que queda es KD-06:** «Alta con prednisona…,
  loratadina 10 mg al día y receta de autoinyector…». Tras la coma, un fármaco
  de la receta queda registrado como indicado aquí.
- **Lo que más pesa de lo que queda son las pérdidas sin aviso:** 5 de 108 y
  4 de 32 en el motor. Casi todas son hemoderivados y vocabulario (TD-14 y
  TD-26).

### Corpus de ensayo

Los 20 guiones por idioma (semilla 3000), rejugados por la página real con el
código de DF-22, se compararon con las grabaciones del ciclo 5 decisión por
decisión: la entrada, el estado de ejecución, las acciones y los planes.

| Medida | Ciclo 5 | Ciclo 6 |
|---|---|---|
| Decisiones comparadas | 238 | 238 |
| Órdenes ejecutadas (ES / EN) | 96 / 96 | 96 / 96 |
| Retenciones no anticipadas, mensajes sin leer, lecturas vacías | 0 | 0 |
| Entradas con otra entrada, estado, acciones o planes | — | **0** |
| Minuto de cierre distinto | — | **0** |
| Diferencia ES/EN conocida (procedencia de un campo, script 5) | 1 | 1, la misma |

- **El rejuego se hizo antes de las correcciones posteriores.** Sus 213
  entradas distintas se leen igual con el lector final, así que el rejuego
  vale para él.
- **Una primera versión de esta comparación leía un campo que no existe.** Se
  rehízo con los campos del registro.

### Latencia

| Medida (330 textos: el corpus de ensayo y las 90 frases, mediana de 5 pasadas, intercaladas, con la máquina ocupada) | Antes | Después |
|---|---|---|
| Lectura de la orden (`parse_family_actions`) | 0,61 ms | 0,71 ms |

### Pruebas

- **`test_critical_clinical_language_regressions.py` (nuevo,
  CRITICAL_CLINICAL_LANGUAGE_REGRESSIONS):** 192 pruebas: 188 del lector y
  del motor, y 4 escenarios por la página real.
  - Por clase: el ejemplo de la auditoría, variantes y negativos en inglés y
    español.
  - Lo que el lector lee, lo que el motor ejecuta en el caso para el que está
    escrita la frase, y la paridad entre idiomas.
  - Las fallas que hallaron los conjuntos ciegos y la revisión adversarial.
  - Los escenarios críticos (anafilaxia, bradicardia, shock, oxígeno) se leen
    del Management Trace guardado.
- **Archivos de prueba del lector:** 1037 pasan y 2 xfail.
- **Registro:** `corrections_registry` C-2026-09-28-04 y C-2026-09-28-09.

## Ciclo 7 · TD-26 y C7-06: hemoderivados, hemorragia, IO y embarazo (2026-09-28)

El detalle completo, con el rediseño de la lectura de glóbulos rojos, está en
`docs/TD26_HEMODERIVADOS_Y_C7_06.md`. Como en el ciclo 6, todas las frases son
**INTERNAL DEVELOPMENT DATA**: nada aquí estima cuántas órdenes reales de un
residente se leen bien.

| Medición | Frases | Lector anterior (HEAD del ciclo 6) | Lector final del ciclo 7 |
|---|---|---|---|
| Conjunto independiente (se usó para desarrollar) | 74 | 32 correctas · 39 retenidas · 3 perdidas | 51 · 19 · **0 perdidas · 0 falsas** |
| Conjunto ciego, medido una vez | 70 | 23 · 45 · 1 perdida · 1 falsa | **Ciego:** 35 · 30 · 1 perdida · 2 falsas. **Post hoc:** 44 · 20 · 0 · 0 |
| Revisión adversarial | 656 | — | Los 12 grupos de fallas (203 entradas) pasan |
| Todo texto de orden que guarda el repositorio | 12 144 | — | 70 se leen distinto fuera de las pruebas del ciclo; todas revisadas |

- **Las «perdidas» que quedan en el puntaje automático** (4 y 6) son errores
  de etiqueta: pedían registrar como hemoderivado no modelado unos glóbulos
  rojos que corren en el número escrito.
- **Jugabilidad.** Las órdenes retenidas con una pregunta bajan a la mitad en
  los dos conjuntos: de 39 a 19 y de 45 a 20.
- **Lo que queda** está en «Límites documentados» del documento de TD-26 y en
  `docs/REGISTRO_DEUDA_TECNICA.md` (TD-14, TD-29 a TD-31). Nada de eso es una
  pérdida sin aviso de un hemoderivado indicado con claridad.
