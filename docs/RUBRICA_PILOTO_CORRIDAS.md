# Rúbrica piloto: trece encuentros evaluados por un modelo real

Generado por `tools_rubric_findings.py` · rúbrica 1.0-pilot · 13 encuentros.

> **Once corridas nuevas**, una llamada pagada cada una, más las dos del 2026-09-23 que ya estaban documentadas. Ninguna se repitió y ninguna se reintentó. Cada encuentro se jugó con `MRS_OFFLINE_CASES=1`, es decir con la clave retenida en todos los resolvedores, de modo que jugar no costó nada y el único gasto fue la propuesta.

## 1 · De dónde salen estos encuentros

No están escritos a mano. Cada uno se jugó a través del intérprete y del motor de producción con `tools_rubric_runs.py`, así que el registro que ve el modelo es el que el motor mismo escribió: sus consecuencias, su reloj y su interpretación de cada orden. Lo único escrito por mí son las órdenes del residente.

Cada guión se escribió **para provocar algo concreto**, y esa intención está en el código antes de ver la respuesta del modelo. Sin eso, "el modelo propuso el evento" no se puede leer contra nada.

## 2 · Los trece encuentros

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

Pero deja una decisión clínica sobre la mesa, y es tuya, no mía:

> Cuando el caso declara que la hipoglicemia es por un agente de acción prolongada y el
> residente da el alta **sin haber preguntado nunca**, ¿el evento debe dispararse igual?
>
> **Lectura actual:** no, porque el registro no contiene el agente. No preguntar es una falla
> de D2 y D5, no un evento de seguridad.
>
> **La otra lectura:** sí, porque no saber es precisamente la falla. Tal como está escrito, la
> omisión del residente lo protege del evento.

No lo cambié. Cambia el significado de la rúbrica y la rúbrica es tuya.

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

## 8 · Dos cosas que conviene que decidas tú

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

## 10 · Costo y procedencia

- **11 solicitudes pagadas**, una por encuentro, 781 segundos en total de las once nuevas.
- Modelo `gpt-5-mini`. Ningún reintento automático: el guión cuenta las solicitudes y aborta antes de una segunda.
- Costo estimado por debajo de US$0,40 en total.
- Las propuestas crudas están en `local-data/paid_runs/rubric_pilot/`, junto con el registro jugado y la transcripción de cada encuentro.
- Los guiones están en `tools_rubric_runs.py`; `--play` reproduce cualquier encuentro sin costo alguno.
