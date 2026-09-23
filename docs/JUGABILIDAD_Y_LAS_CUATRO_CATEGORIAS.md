# Jugabilidad: por qué se detenían las órdenes y qué cambió

Fecha: 2026-09-23. Decisión docente: el simulador bloqueaba demasiadas órdenes,
el encuentro se hacía lento y se perdía parte de su utilidad — mientras que
**registrar** el modelo de trabajo, la expectativa, lo que se va a reevaluar y
la acción sigue siendo indispensable para analizar el caso y generar el
Management Trace.

Todo lo que sigue se midió sin una sola llamada pagada.

## La medición

Quince órdenes que nombran las cuatro categorías en prosa corriente, en español
y en inglés, tal como se escriben con el paciente delante.

| | Antes | Después |
|---|---|---|
| Órdenes completas detenidas | **7 de 15** | **0 de 15** |
| Órdenes completas con una cláusula devuelta como «orden no reconocida» | **8 de 15** | **1 de 15** |
| Órdenes escuetas, sin razonamiento, que siguen detenidas | 3 de 3 | **3 de 3** |

La que sigue detenida no es un problema de lenguaje: pide adrenalina 0,5 mg IM,
y la vía intramuscular no es una intervención que este motor administre.

## Dos causas distintas

### 1. El portón pedía cinco cosas y el docente nombró cuatro

De las siete órdenes completas que se detenían, en **cinco** lo único ausente
era `management_priority`. El residente había escrito el modelo, la expectativa,
la reevaluación y la orden, y el encuentro se detenía a pedir un encabezado.
El tiempo de reevaluación se comportaba igual.

El portón ahora retiene la orden por las cuatro categorías:

- **modelo de trabajo** — qué cree que está pasando
- **expectativa** — qué espera que cambie
- **qué reevaluará** — las variables
- **la acción** — que es la cuarta, y es lo que pone la orden frente al portón,
  así que nunca puede ser lo que falta

La prioridad y el momento de la reevaluación **se siguen extrayendo y se siguen
registrando**. Viajan con la decisión en `reasoning_gate["noted"]`, entran al
Management Trace y aparecen impresos como *«Not stated before this order: …»*.
Se anotan en vez de exigirse, que es como este simulador trata cualquier otra
omisión del residente.

### 2. El razonamiento se devolvía como «orden no reconocida»

Peor que el portón. El separador de cláusulas trataba cada fragmento como una
orden candidata, así que el residente escribía exactamente lo que se le pide y
el simulador le contestaba que reemplazara su expectativa por una intervención
con dosis y vía:

- «quiero frenar la agregacion»
- «the goal is to limit thrombus growth»
- «apunto a PAM sobre 65»
- «controlo PAM», «llene capilar»
- «busco subir la presion» → *«nombre la parte del examen a realizar»*
- «control de PAM en 15 min» → *«el estudio solicitado no fue reconocido»*

Una cláusula que enuncia un objetivo, una expectativa o lo que se va a vigilar
ya no es una orden ilegible. **El límite importa más que el alivio**: una
cláusula que nombra algo administrable sigue siendo una orden dijera lo que
dijera, así que `bajar la nitroglicerina a 20 mcg/min` se ejecuta y
`adrenalina 0,5 mg IM` se sigue devolviendo. El silencio es la peor de las dos
fallas y hay pruebas que impiden que sea la solución.

### Además: dos órdenes que no producían nada

- «Given the hypoxemia I will start NIV» — la orden anunciada a mitad de frase
  se leía como prosa: ni ejecución ni pregunta.
- «le voy a pasar 500 cc», «parto con volumen 500 cc» — la perífrasis chilena
  de intención y de inicio no se reconocía.

Ambas ejecutan ahora.

## Lo que aprende el reconocimiento determinista

Frases que antes no se leían y ahora sí, en los dos idiomas:

- **Expectativa como propósito**: «para subir la PAM», «to raise the MAP»,
  «to unload the work of breathing».
- **Expectativa como objetivo declarado**: «busco…», «quiero…», «apunto a…»,
  «la idea es…», «the goal is…», «the aim is…», «expecting…».
- **Expectativa como valor objetivo**: «PAM sobre 65», «saturación sobre 92».
- **Reevaluación en primera persona**: «controlo», «reviso», «vigilo», «mido»,
  «monitorizo», «control de X en N minutos», «I will look at the sat and the RR».

Con una restricción que no se movió: **nada fabrica una categoría que el
residente no escribió**. Se probó derivar la expectativa desde la prioridad
cuando sólo había una de las dos, y se descartó: una orden cuya expectativa
nadie escribió debe detenerse.

## El modelo de lenguaje como segundo lector

`reasoning_recognition.py`. Se le hace **una sola pregunta**: ¿cuál de estas
categorías está presente en lo que escribió el residente, y con qué palabras
suyas?

Dos propiedades lo hacen seguro en ese puesto:

- **No escribe.** Devuelve presente/ausente y una cita. Cada cita se verifica
  aquí contra el mensaje del residente y se descarta si no aparece textualmente
  (se perdonan tildes, mayúsculas y espacios, que son transcripción). Nada que
  el modelo componga entra al registro con el que se arma el Management Trace,
  el Faculty Brief y la rúbrica. Una cita inventada se rechaza y el rechazo
  queda anotado, para que una deriva del modelo se vea en vez de pasar callada.
- **No cuesta una llamada por orden.** Se consulta **sólo cuando el parser
  determinista iba a detener la orden**, y sólo sobre las categorías que
  reportó ausentes. Un residente que escribe completo nunca es una llamada.

Está construido y probado sin red (cliente de prueba). **Está apagado.** Se
enciende con `MRS_AI_REASONING`, aparte de `MRS_AI_LANGUAGE`, y no se ha
gastado ninguna llamada pagada en él.

## Lo que queda abierto

- **Adrenalina IM** no es una intervención soportada. Es una brecha de
  capacidad, no de lenguaje.
- **«IM» se lee como un «I'm» dictado** en el extractor de razonamiento, porque
  la puntuación de dictado se repara antes de considerar la vía.
- **«Reducir la dobutamina a 2»** no produce ninguna acción — ni ejecución ni
  pregunta. Es previo a este cambio y es el tipo de falla que más importa: una
  titulación que desaparece en silencio.
