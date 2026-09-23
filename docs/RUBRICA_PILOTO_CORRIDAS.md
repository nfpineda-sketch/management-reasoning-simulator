# Rúbrica piloto: trece encuentros evaluados por un modelo real

Generado por `tools_rubric_findings.py` · rúbrica 1.0-pilot · 13 encuentros.

> **Once corridas nuevas**, una llamada pagada cada una, más las dos del 2026-09-23 que ya estaban documentadas. Ninguna se repitió y ninguna se reintentó. Cada encuentro se jugó con `MRS_OFFLINE_CASES=1`, es decir con la clave retenida en todos los resolvedores, de modo que jugar no costó nada y el único gasto fue la propuesta.

## 1 · De dónde salen estos encuentros

No están escritos a mano. Cada uno se jugó a través del intérprete y del motor de producción con `tools_rubric_runs.py`, así que el registro que ve el modelo es el que el motor mismo escribió: sus consecuencias, su reloj y su interpretación de cada orden. Lo único escrito por mí son las órdenes del residente.

Cada guión se escribió **para provocar algo concreto**, y esa intención está en el código antes de ver la respuesta del modelo. Sin eso, "el modelo propuso el evento" no se puede leer contra nada.

## 2 · Los trece encuentros

> La fila de `hypoglycemia_76f` es la **primera** corrida. Ese caso se volvió a correr después, para verificar tu decisión; el antes y el después están en §6.

| Caso | Qué se quiso provocar | D1 | D2 | D3 | D4 | D5 | Evento esperado | Evento propuesto |
|---|---|:-:|:-:|:-:|:-:|:-:|---|---|
| `acs_52m_de_winter` | Encuentro truncado a los 15 minutos | 2 | 1 | 1 | 2 | 1 | — | — |
| `asthma_24f` | Manejo competente | 2 | 2 | 2 | 3 | 2 | — | — |
| `asthma_49m` | Broncodilata y no soporta la ventilación | 2 | 2 | 2 | 2 | 2 | `asthma_no_ventilatory_support` | `asthma_no_ventilatory_support` |
| `gi_bleed_57m` | Reanimación competente | 2 | 3 | 3 | 2 | 2 | — | — |
| `gi_bleed_72f` | Estudia y nunca reanima | 1 | 2 | 0 | 2 | 2 | `gi_no_resuscitation` | `gi_no_resuscitation` |
| `hypoglycemia_54m_thiamine` | Glucosa sin tiamina | 3 | 2 | 0 | 3 | 2 | `hypo_no_thiamine` | `hypo_no_thiamine` |
| `hypoglycemia_76f` | Alta tras hipoglicemia por sulfonilurea | 2 | 2 | 2 | 2 | 1 | `hypo_unsafe_discharge` | — |
| `opioid_35m` | Manejo competente | 2 | 2 | 3 | 3 | 2 | — | — |
| `pneumonia_83m` | Trata la neumonía, no estudia el compromiso de conciencia | 3 | 2 | 2 | 2 | 1 | `pneumonia_unexamined_altered_state` | `pneumonia_unexamined_altered_state` |
| `pulmonary_edema_58m` | Soporta bien y luego carga volumen | 3 | 3 | 0 | 2 | 2 | `edema_volume_loading` | `edema_volume_loading` |
| `pulmonary_embolism_61m` | Reconoce y nunca anticoagula | 3 | 3 | 0 | 3 | 2 | `pe_no_anticoagulation` | `pe_no_anticoagulation` |
| `acs_48m_wellens` | Corrida 1 · entrega retenida por el intérprete | 2 | 2 | 2 | 2 | 1 | — | — |
| `pulmonary_embolism_33f` | Corrida 2 · trombólisis sin hipotensión sostenida | 3 | 3 | 0 | 2 | 1 | `pe_unindicated_thrombolysis` | `pe_unindicated_thrombolysis` |

**7 de 8 eventos esperados fueron propuestos. 0 eventos propuestos sin que el guión los buscara. Ningún evento inventado: el esquema sólo admite los definidos para el caso.**

## 3 · Cómo se distribuyeron los puntajes

65 puntajes de dominio en 13 encuentros.

| | 0 | 1 | 2 | 3 | No evaluable | Media |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| **Dominio 1** · Reconocimiento de gravedad y priorización | 0 | 1 | 7 | 5 | 0 | 2.31 |
| **Dominio 2** · Evaluación e interpretación clínica | 0 | 1 | 8 | 4 | 0 | 2.23 |
| **Dominio 3** · Selección y ejecución de un manejo seguro | 5 | 1 | 5 | 2 | 0 | 1.31 |
| **Dominio 4** · Seguimiento y reevaluación | 0 | 0 | 9 | 4 | 0 | 2.31 |
| **Dominio 5** · Adaptación y continuidad del manejo | 0 | 5 | 8 | 0 | 0 | 1.62 |
| **Total** | 5 | 8 | 37 | 15 | 0 | |

## 4 · El hallazgo principal: "no evaluable" no se usó nunca

**Sesenta y cinco puntajes de dominio, trece encuentros, cero usos de `not_assessable`.**

La instrucción está escrita, y el modelo la lee: *"Use 'not_assessable' when the case offered
no real opportunity, the record holds insufficient evidence, or the simulator could not observe
the performance"*, y en la línea siguiente *"'not_assessable' is NOT a zero"*.

Dos encuentros se escribieron precisamente para ponerla a prueba, y en los dos el modelo
puntuó en vez de declarar la falta de oportunidad:

- **`acs_48m_wellens`** (corrida 1): la única entrega que llevaba un destino fue retenida por
  el intérprete. El modelo reconoció que no se ejecutó y aun así puso D5 = 1.
- **`acs_52m_de_winter`**: encuentro truncado a los 15 minutos, dos decisiones. El modelo puso
  D5 = 1 y escribió, en el mismo campo de límites: *"No disposition, consultation, or
  reperfusion pathway activation is recorded before case closure"*.

Es decir: **el modelo sabe el hecho y aun así lo convierte en un puntaje.** No es que no lo
vea; es que la diferencia entre "no lo hizo" y "no pudo observarse" no le resulta accionable.

Esto no es un defecto del contrato. Es exactamente el juicio que la especificación dejó en
manos del docente, y trece encuentros muestran que lo va a necesitar en todos. Lo que sí
sugiere es que **el valor por defecto del selector no debería ser el puntaje propuesto cuando
el propio modelo declara que el encuentro cerró antes de la oportunidad** — pero ese es un
cambio a la rúbrica y queda para tu decisión.

## 5 · Los eventos críticos: el modelo los propone bien, y no dispara de más

Siete de los ocho eventos que los guiones buscaban fueron propuestos, cada uno citando la
decisión, el minuto y los observables, y cada uno revisando las exclusiones declaradas antes
de proponerlo. Dos ejemplos, en sus palabras:

> `edema_volume_loading` — *"POCUS at minute 12 showed diffuse bilateral B-lines... Despite
> these findings of congestion and no documented cause of hypovolaemia, a 500 mL normal saline
> IV bolus was executed at minute 23."* Exclusiones: *"No prior record established a
> hypovolaemic contributor before the bolus."*

> `pneumonia_unexamined_altered_state` — *"Arrival state shows mental_status 'Drowsy'. In the
> 0–60 min window there is no executed bedside glucose, no documented focused neurological
> examination, and no head imaging recorded."*

Y, sobre todo, **no propuso los que no correspondían**:

- en `pneumonia_83m` no propuso `pneumonia_no_antibiotic`, porque la ceftriaxona sí se dio;
- en `hypoglycemia_54m_thiamine` no propuso `hypo_no_glucose`, porque la glucosa sí se dio;
- en `asthma_49m` propuso la falta de soporte ventilatorio **aunque el motor mejoró al
  paciente** tras el broncodilatador. Puntuó la decisión, no el desenlace, que es lo que la
  instrucción pide.

## 6 · El único evento que faltó, y por qué el modelo tenía razón

`hypoglycemia_76f`: el residente corrige la glicemia y manda a la paciente a la casa. La
paciente toma glimepirida. El evento `hypo_unsafe_discharge` existe para eso, y el modelo **no
lo propuso**.

Escribí ese guión esperando que lo propusiera. Se equivocó mi diseño, no el modelo.

El evento declara `information_required: "The history of the causative agent"`, y el residente
nunca preguntó por los medicamentos. La glimepirida está en la historia del caso, pero sólo
aparece si alguien la pide. El modelo lo dijo con precisión:

> *"No explicit medication history in the encounter to confirm or exclude sulfonylurea or other
> long-acting hypoglycaemic agents."*

y en vez de asumirla, mandó la preocupación al canal que existe para eso:

> *"Discharge executed after severe hypoglycaemia without a documented plan for continued
> observation, medication review to exclude long-acting hypoglycaemic agents, or explicit
> handover — this may be unsafe depending on etiology."*

**Eso es el comportamiento correcto**, y es el mismo error que cometí yo el 2026-09-23 cuando
mi propuesta ilustrativa inventó un valor de troponina que el registro no contenía.

### Tu decisión, y lo que cambió por ella (2026-09-23)

Te planteé la pregunta y la respondiste: **el evento se dispara igual.** El paciente está ahí y
se le puede preguntar; si el residente no lo hace, eso debe ser un punto de análisis explícito
en el Management Trace y en el Faculty Brief, y debe reflejarse en el puntaje.

Eso es ahora una regla del instrumento, no un parche a un caso:

> **La información disponible preguntando está disponible, se haya preguntado o no.** El
> paciente, o la fuente colateral que el caso nombra, está presente todo el encuentro y
> responde. Un residente que nunca preguntó no fue privado de la información: omitió
> obtenerla. Una historia no preguntada **nunca excusa un evento crítico**, y no haberla
> preguntado es en sí una omisión que la evaluación nombra.

Cómo quedó implementada:

- Cada evento declara ahora, por separado, **lo que tenía que estar en el registro** (los
  observables, un resultado, una acción ejecutada) y **lo que el caso responde si le preguntan**
  —cada uno como un par (tema de historia, qué le diría)—. `case_assessment.verify` comprueba
  que el tema prometido sea uno que el caso realmente escribe, igual que ya comprobaba que un
  estudio prometido esté entre sus investigaciones. **21 de 21 casos, cero discrepancias.**
- Nueve de los dieciséis eventos tenían una exigencia de historia; todas se movieron.
- La regla viaja con cada solicitud y está en las instrucciones de la rúbrica y del brief.

### La verificación, con una llamada pagada (2026-09-23)

Corrí **el mismo encuentro otra vez**, sin cambiar una sola orden del residente, para que la
comparación fuera directa. Una llamada, 65 s.

| | Antes | Después |
|---|---|---|
| D1 | 2 | 2 |
| D2 | 2 | **3** |
| D3 | 2 | 2 |
| D4 | 2 | 2 |
| D5 | 1 | **0** |
| Evento | ninguno | **`hypo_unsafe_discharge`** |
| Con el docente confirmando | `Base 9/15` | `Base 9/15 · Penalización −3 · Ajustado 6/15` |

El modelo propuso el evento y citó la orden del residente en sus propias palabras:

> *"An executed discharge disposition was recorded (trace:3 decision at minute 26: 'La envio a
> su casa...')... The case provides that the hypoglycaemia is attributable to a sulfonylurea
> **available on asking**; failure to arrange observation after such an episode meets the event
> trigger."*

Vale la pena notar que esa orden sólo existe en el registro porque anoche se arregló que `a su
casa` fuera un alta. Antes, la orden se evaporaba en silencio y con ella el evento.

Y D5 pasó a 0 con el fundamento escrito como la regla:

> *"The case specifies the hypoglycaemia is attributable to a long-acting sulfonylurea
> (information available on asking); discharging without observation after such an episode is
> unsafe."*

**Dónde no funcionó todavía.** D2 **subió** de 2 a 3. El modelo sí nombró la omisión, en la
evidencia en contra —*"The learner did not ask about medications (medication history is
available on asking)"*— y en dos preocupaciones señaladas. Pero no dejó que moviera el número:
*"this omission does not negate that relevant diagnostic data were obtained"*.

Es decir: **la regla llegó al evento y a la continuidad, y no llegó a la evaluación.** No lo
forcé con más instrucciones; es exactamente el tipo de juicio que el docente confirma, y ahora
tiene la omisión escrita delante en los tres documentos para hacerlo.

### Dos defectos silenciosos que la pregunta destapó

**La historia era invisible para todo.** Preguntar no es una orden: no consume tiempo simulado
y no cambia ningún observable, así que vive en los eventos del encuentro y no en la traza.
**Nada que construyera un análisis miraba ahí.** Cuando el modelo escribió *"No explicit
medication history in the encounter"* estaba diciendo la verdad sobre lo que le habían
mostrado, y algo falso sobre el encuentro. Ahora la historia obtenida, los temas ofrecidos y
los temas que nadie preguntó viajan en la misma fuente que leen los cuatro documentos.

**El caso también era invisible.** `case_id_of` leía sólo el campo que escribe la exportación, y
una sesión guardada no tiene ese campo: la app guarda sus campos de sesión y nada más. **Todo
encuentro real parecía un caso sin declaración: sin oportunidades declaradas y sin ningún evento
crítico definido.** Cada prueba que ejercitaba esa capa ponía el campo a mano, así que la suite
estaba verde mientras el camino de producción estaba muerto. Se lee ahora también desde el
estado que la sesión sí guarda, con una prueba que construye el payload campo por campo como lo
arma la app.

## 7 · Lo que el rango sugiere

- **D3 es el único dominio que llega a 0**, y llega exactamente donde hay un evento confirmado.
  El descriptor funciona como está escrito: *"ordena algo claramente peligroso"* o la omisión de
  una intervención esencial es un 0, no un 1.
- **D4 nunca bajó de 2** en trece encuentros. Declarar "reevalúo en 15 minutos" parece bastar
  para un 2, y ningún guión logró un 1 ahí, ni siquiera los que reevaluaron mal.
- **D5 nunca llegó a 3.** Ni el encuentro más competente lo alcanzó.
- Fuera de D3, las medias están todas entre 2,2 y 2,3. El instrumento discrimina bien la
  seguridad y discrimina poco el resto.

Con trece encuentros esto es una señal, no una medición. Pero si el piloto se corre con
residentes reales, **D4 y D5 son los descriptores que conviene mirar primero**.

## 8 · Dos cosas que siguen pendientes de ti

**El idioma del fundamento.** El contrato le pide al modelo que responda *en inglés*, y por eso
el informe de rúbrica en español lleva los rótulos, los dominios y la decisión docente en
español pero el fundamento del modelo en inglés. El documento ahora lo dice en vez de dejarlo
implícito. Cambiarlo es una llamada pagada por encuentro y una nueva versión de prompt, así que
no lo toqué.

**El valor por defecto del selector.** Hoy el selector del docente arranca en el puntaje que
propuso la IA. Dado que en trece encuentros la IA nunca eligió "no evaluable" —ni siquiera
donde ella misma escribió que el encuentro cerró antes de la oportunidad— ese valor por defecto
empuja hacia un puntaje. Es un cambio de una línea, pero cambia el comportamiento de la
rúbrica, así que queda para tu aprobación.

## 9 · Lo que se arregló en el camino

Escribir once encuentros en el español en que los escribe un residente encontró cinco
defectos del intérprete, todos en la misma frase: la que cierra el encuentro.

El español pone el pronombre **antes** del verbo. Nada lo leía, así que la frase no tenía verbo
inicial. `Le doy aspirina 300 mg vo` quedaba retenida como orden no reconocida, y
`lo hospitalizo en sala` y `le pido un electrocardiograma` **no producían ni acción ni
mensaje**. El silencio es peor que la retención, y caía sobre el destino del paciente, que es
todo el dominio 5: un dominio que no se puede puntuar porque la orden se evaporó no es un
residente que no decidió.

Los otros cuatro, en las mismas frases: `hospitalizar en sala para continuar broncodilatadores
y corticoides` se partía en "y" y el fragmento heredaba el verbo de ingreso, pedía un destino
que no tenía, y retenía toda la entrega; `a su casa` y `a domicilio` no eran un alta (sólo lo
era `a la casa`), y un alta es el disparador de un evento crítico definido, así que el silencio
se llevaba el evento con él; `angiotomografía de tórax` escrita completa se rechazaba; y el
equipo de tromboembolismo sólo existía por su sigla en inglés.

Los cinco están corregidos, con pruebas, en `test_spanish_pronoun_before_the_verb.py`.

### Y uno que introduje yo

Al hacer visible la historia, `history_review` alcanzaba las etiquetas de los temas a través de
`clinical_scene`, que importa Streamlit y PIL. Es decir: un PDF docente y una declaración de
rúbrica importaban Streamlit **para saber que `medications` se llama "Medications"**. Cuando un
hilo lo importaba mientras un hilo de script de Streamlit ya tenía tomado el lock de importación
de ese módulo, la suite completa se quedó detenida **dos horas** en
`test_exploring_patient_preserves_state_and_management_remains_reachable`.

Las etiquetas viven ahora en `history_topics.py`, una hoja sin ninguna importación, y
`clinical_scene` las reexporta para que ningún lector existente cambie. Hay una prueba que
arranca un intérprete limpio y verifica que importar `history_review` no traiga Streamlit ni
PIL.

Lo encontró la disciplina de correr la suite completa antes de cada commit, no una prueba: el
síntoma era una suite que no terminaba nunca, que es peor que una que falla.

## 10 · Costo y procedencia

- **11 solicitudes pagadas**, una por encuentro, 772 segundos en total de las once nuevas.
- Modelo `gpt-5-mini`. Ningún reintento automático: el guión cuenta las solicitudes y aborta antes de una segunda.
- Costo estimado por debajo de US$0,40 en total.
- Las propuestas crudas están en `local-data/paid_runs/rubric_pilot/`, junto con el registro jugado y la transcripción de cada encuentro.
- Los guiones están en `tools_rubric_runs.py`; `--play` reproduce cualquier encuentro sin costo alguno.
