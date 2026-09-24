# Las cuatro preguntas, las cues y de dónde vino cada cosa

Especificación docente del 2026-09-23, secciones 3, 4, 6 y 7. Implementado sin
ninguna llamada pagada. Continúa `JUGABILIDAD_Y_LAS_CUATRO_CATEGORIAS.md`.

## 1. Procedencia (§6)

Cada casilla registrada dice de dónde vino. Cuatro estados, y la ausencia no es
uno de ellos: una casilla que nadie llenó simplemente no está, y el trace dice
**«no explicitado»**, nunca «no reconoció» — lo único que sabemos es que no se
escribió.

| Estado | Significa |
|---|---|
| `stated` | lo escribió en esta entrada |
| `carried` | lo escribió antes en este encuentro, y se conserva como contexto |
| `completed` | lo escribió en el formulario de seguimiento |
| `composed` | lo redactó la aplicación a partir de sus otras palabras |

**El modelo de trabajo ya no se pide dos veces.** Si el residente explicó qué
cree que está pasando en una decisión anterior del mismo encuentro, la siguiente
orden no se detiene a pedirlo otra vez. Se conserva con la atribución al minuto
y a la decisión donde realmente lo dijo, así que el registro nunca lo lee como
una reafirmación nueva.

**Sólo viaja la interpretación.** La expectativa y el plan de reevaluación
pertenecen a la acción que los produjo; arrastrarlos pegaría las palabras del
residente a una decisión de la que nunca hablaron.

El formulario llega precargado, así que una casilla que el residente **no
cambió** conserva la mano que la escribió primero; sólo la que corrigió o
completó pasa a ser suya ahí.

## 2. El momento real (§6/§7)

Una orden detenida no se ejecuta y ninguna otra corre mientras espera, así que
la justificación queda fijada **antes** de que esa decisión tenga resultados.
Eso ya era estructuralmente cierto; ahora está registrado y probado:

- `reasoning_gate["sealed_at_min"]` — el minuto en que quedó fijada.
- `reasoning_gate["completed_after_results"]` — verdadero si el reloj o el
  número de decisiones se movió entre la retención y la respuesta.

Hoy no puede dispararse. Esa es la idea: si un cambio futuro abre esa puerta, el
registro lo dice en vez de mejorar un puntaje en silencio.

## 3. Las cuatro preguntas (§4)

La etiqueta es la pregunta. Antes decía «Working model», «Expected effect», y el
residente tenía que deducir qué quería la aplicación antes de poder contestarla.

| Pregunta | Ayuda |
|---|---|
| ¿Qué crees que está pasando? | Tu explicación actual del problema y los hallazgos que la apoyan. No necesitas un diagnóstico definitivo. |
| ¿Qué vas a hacer? | Las intervenciones, estudios o medidas que quieres indicar. |
| ¿Qué esperas que ocurra o qué buscas aclarar? | La respuesta que anticipas o la información que esperas obtener para orientar el manejo. |
| ¿Qué vas a revisar y cuándo? | Las variables o hallazgos que comprobarás y el momento o condición para hacerlo. |

Hay una prueba que impide que una ayuda nombre un hallazgo, una conducta o un
diagnóstico: una pista clínica disfrazada de instrucción sería indistinguible
del razonamiento del residente después.

**La acción es de sólo lectura.** Es una de las cuatro y la única que nunca se
pregunta aquí: es lo que pone la orden frente al portón. El formulario completa
el razonamiento alrededor de una orden que el motor ya leyó, y una casilla que
pudiera cambiarla dejaría que el formulario administrara un fármaco. Se muestra
lo entendido; para cambiarlo se cancela y se escribe de nuevo.

El mensaje dice primero lo reconocido:

> Reconocí qué vas a hacer y qué vas a revisar.
> Falta explicitar qué crees que está pasando y qué esperas que ocurra.

La prioridad de manejo queda como casilla opcional al final: se registra porque
sirve leerla, nunca porque detenga nada.

## 4. Las cues (§3)

Dentro del modelo de trabajo, nunca como quinta categoría. Su ausencia sola no
detiene nada.

De cada hallazgo se guarda la palabra del residente, su polaridad —presente,
ausente, en cambio, incierto—, si hubo contraste expresado, y **si el residente
dijo que ese hallazgo sostenía su interpretación**, con el conector que usó y la
frase completa que lo respalda.

Dos reglas, y las dos son negativas:

- **Nada se reconstruye desde la intervención.** «Dar suero» no nombra ningún
  hallazgo y no implica hipovolemia. El léxico sólo alcanza palabras escritas.
- **Una sospecha no es un hecho y una predicción no es un hallazgo presente.**
  «Creo que está en shock» es interpretación; «espero que suba la presión» es
  expectativa.

El vínculo se operacionaliza con una regla explicable: el hallazgo está en la
misma frase que un conector explícito. Y el lado importa — «porque» introduce la
razón, «lo que sugiere» introduce la conclusión. Leerlo al revés registraba la
interpretación como si fuera una observación: «lo que sugiere congestión»
quedaba archivado como si el residente hubiera visto congestión.

### Medición

Quince entradas, contra lo que un lector marcaría a mano:

| | |
|---|---|
| Hallazgos reconocidos | **28 de 30** |
| Hallazgos inventados | **0** |
| Vínculo juzgado como un lector | **13 de 15** |

Las dos diferencias de vínculo son del mismo tipo: el residente listó hallazgos
en una frase y su conclusión en la siguiente, sin conector. La lectura de aquí
es deliberadamente conservadora — la yuxtaposición no es una explicación, y §3
pide que se registre que **explicó** que el dato apoyaba su interpretación.

### En el Management Trace

Dentro del bloque de interpretación de cada decisión:

```
Modelo de trabajo: sospecha de shock   (enunciado en esta entrada)
Hallazgos mencionados: hipotenso; confuso
Relación expresada: esos hallazgos se dieron como la razón: «me preocupa que»
```

y cuando falta, «Hallazgos mencionados: no explicitados» o «Relación con la
interpretación: no explicitada». La misma información y la misma procedencia en
el registro, la interfaz y los PDF. No se reabrió el diseño de los documentos.

## 5. El modelo como lector de hallazgos — construido y apagado

`MRS_AI_CUES` con tres valores:

| Valor | Qué cuesta |
|---|---|
| `off` (por defecto) | nada. Sólo leen los patrones. |
| `held` | **nada adicional**. La pregunta por los hallazgos viaja en la misma petición que una orden detenida ya iba a hacer. |
| `always` | **una petición por decisión**. Es la diferencia entre una excepción y un cobro por orden. |

**Actualización 2026-09-24 — `held` ejercitado** (`test_the_findings_read_on_a_held_order.py`):

- `held` depende del segundo lector (`MRS_AI_REASONING`): es su petición la que lleva la
  pregunta por los hallazgos. Sin ese lector no hay petición que acompañar y `held`
  equivale a `off`. Antes el modo informaba `held` sin leer nada; ahora informa `off`.
- Una orden detenida hace **una** petición, con las dos preguntas. Completarla (en texto
  libre o en el formulario) no hace otra. Si se cancela, lo que el modelo leyó desaparece
  con ella: nada queda en el registro ni en lo que el encuentro guarda.
- Sin presupuesto, o si el modelo falla, la orden queda detenida exactamente como antes
  y los hallazgos de los patrones quedan intactos.
- La orden detenida, con lo que el modelo leyó, se guarda y se recupera al reanudar el
  encuentro. El **presupuesto** también: hasta hoy, reanudar un encuentro lo reiniciaba.
- Lo que el modelo lee pasa por la misma regla que los patrones: una palabra dentro de una
  expectativa o un plan («espero que suba la glicemia») no es una observación y se
  rechaza; una que el residente no escribió («glicemia 40») también. Sin esa regla, una
  respuesta esperada podía quedar registrada como un hallazgo que el residente vio.
- Nada de lo leído se muestra al residente mientras decide. El brief docente, la propuesta
  de rúbrica y la verificación del registro se construyen **con la misma entrada** haya o
  no hallazgos leídos por el modelo: no pueden acreditarlos ni penalizarlos. Sólo el
  análisis del Management Trace del residente los recibe, marcados con quién los leyó.

Categorías y cues son **una sola operación**, nunca dos, y nunca una llamada por
campo (§8).

Las mismas dos propiedades que ya tenía el segundo lector, extendidas a las
cues: cada hallazgo debe aparecer **textualmente** en lo que escribió el
residente o se descarta, y un vínculo que se afirma sin el conector citado
conserva el hallazgo y pierde la afirmación — la observación sigue siendo suya.
Los patrones conservan sus filas; el modelo sólo agrega donde ellos no vieron
nada, y cada fila dice cuál de los dos la leyó. En el trace aparece «algunos
leídos por un modelo».

Si el modelo falla, el texto queda íntegro y los patrones ya lo leyeron: nada se
presenta como información que el residente hubiera omitido (§8).

### La medición pagada: 25 autorizadas, 25 usadas

Una petición por entrada, contra texto congelado. Sin encuentro, sin fisiología,
sin reloj: una corrida aquí no puede cambiar un paciente ni un puntaje.

**Las primeras 15 salieron mal por culpa mía.** Diez de quince fallaron con un
timeout de cliente de 12 segundos copiado de `ai_interpreter`, y mi envoltorio
decía «The recognition request failed» sin la causa — así que la única forma de
diagnosticarlo habría sido otra corrida pagada. Una petición de diagnóstico, con
la causa ya pasando a través, lo resolvió. Corregido: la excepción viaja con el
mensaje, el timeout es de 45 s y `max_retries=0`, porque un reintento de la
librería es una segunda petición que nadie autorizó.

Las 9 restantes midieron las 9 entradas que faltaban. Las quince, completas:

| | Patrones | Modelo |
|---|---|---|
| Hallazgos reconocidos | 25 | **26** |
| Perdidos | 1 | **0** |
| **Inventados** | **0** | **1** |
| Vínculo como un lector | 13/15 | 13/15 |

**El modelo agregó uno y se inventó uno.** El que agregó fue «orina turbia» — un
hallazgo de vocabulario abierto que el léxico cerrado no podía alcanzar. El que
se inventó fue «la hipotensión», tomado de *«Espero que mejore la hipotensión»*:
convertir una expectativa en un hallazgo presente, que es exactamente la falla
que §3 nombra. Los patrones la rechazaron correctamente.

También falló un vínculo que los patrones acertaron: en *«so I suspect ongoing
hypoperfusion»* dijo que no había relación expresada.

Vale la pena decir qué **no** protege la verificación textual: las 24 citas
fueron exactas, cero rechazos. La única invención estaba **correctamente
citada** y usada en el rol equivocado. La comprobación garantiza que las
palabras son del residente, no que el papel sea el correcto.

**Qué hice con eso.** El único aporte real señalaba un léxico cerrado, así que lo
abrí donde apuntaba: aspecto de la orina, del esputo, de la piel y la herida.
Con eso el lector determinista queda en **26 reconocidos, 0 perdidos, 0
inventados, vínculo 14/15** — iguala al modelo en hallazgos, lo supera en el
vínculo, y cuesta cero.

**Recomendación: `always` se queda apagado.** No compra nada que los patrones no
den gratis, y compra un riesgo que los patrones no tienen. `held` sí tiene
sentido: viaja en una petición que ya se estaba pagando.

### El presupuesto dejó de ser una promesa

`MRS_AI_CALL_BUDGET`, ocho peticiones por encuentro por defecto, contadas en
`ai_calls_spent` y con un registro de para qué fue cada una. **Todas** las rutas
pagadas pasan por el mismo contador: la normalización de lenguaje, el segundo
lector de órdenes detenidas y la lectura de hallazgos. Agotado el presupuesto,
cada una vuelve a su lectura determinista y lo dice en el registro — que el
motivo fue el presupuesto, no el residente.

Hasta ahora el presupuesto acotado era una condición que yo cumplía a mano. Ahora
es un contador que se detiene.

## Lo que queda abierto

- **«Información consultada»** sólo existe para la historia (`history_review`).
  Nada registra que alguien mire el monitor, así que para signos vitales la
  distinción disponible/consultada no se puede sostener. No se construyó a
  medias.
- El vínculo **entre frases** no se reconoce (ver arriba). Es la mayor parte de
  lo que quedaría para un modelo.
- **El léxico sigue cerrado.** Se abrió donde la medición señaló, pero un
  hallazgo que nadie anticipó sigue fuera de su alcance. Ése es el precio de no
  inventar nada, y por ahora es el precio correcto.
- **El vínculo entre frases** sigue sin reconocerse, y el modelo tampoco lo
  resolvió: falló uno que los patrones acertaron.
- **La verificación textual no protege el rol**, sólo las palabras. Una cita
  exacta usada como hallazgo cuando era una expectativa pasa la comprobación.
  Ocurrió una vez en quince.
