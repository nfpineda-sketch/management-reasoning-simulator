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

## Lo que queda abierto

- **«Información consultada»** sólo existe para la historia (`history_review`).
  Nada registra que alguien mire el monitor, así que para signos vitales la
  distinción disponible/consultada no se puede sostener. No se construyó a
  medias.
- El vínculo **entre frases** no se reconoce (ver arriba). Es la mayor parte de
  lo que quedaría para un modelo.
- **Cues por modelo** (§3 con IA) no está hecho: cuesta una llamada por decisión,
  no por orden detenida, y espera autorización de presupuesto.
