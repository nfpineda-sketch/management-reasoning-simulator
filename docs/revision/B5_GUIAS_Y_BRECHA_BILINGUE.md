# B-5 · Guías para la firma, brecha bilingüe (X-1 / F0-11) y primer lote de nivel 1

> **Estado (2026-10-07): trabajo PRE-DEPLOYMENT de B-5, sólo documentación. No aprueba nada.**
>
> - Las dos guías quedan actualizadas para la firma y **no aprobadas**: su firma sigue en blanco.
> - Ninguna brecha bilingüe se corrigió. Ningún texto clínico se activó ni se reescribió.
> - El código no cambió: fuera de `docs/`, el árbol es el de `8ff41a4` (B-1, 23 de 23).
> - B-5 sigue **BLOCKED**.

## 0. La decisión X-1 y lo que pide este encargo

- **X-1, cerrada** (decisión docente comunicada en el encargo del 2026-10-07): el piloto de residentes corre en
  inglés y en español.
- Lo que sigue de ella, según el encargo:
  - el español entra en el candidato final, y F0-11 es un requisito previo al candidato, no un opcional
    posterior al despliegue;
  - todos los textos activos de la Fase 0 que ve el residente deben estar en inglés y en español antes de
    congelar el candidato;
  - un residente en español no debe encontrar mensajes de la Fase 0 sólo en inglés: ni en la sala, ni en el
    panel del examen, los recibos, el paro, las interrupciones, la aclaración u otra pantalla activa del piloto;
  - los códigos y destinos que lee la máquina (EXECUTED, UNRECOGNIZED, HELD_REASONING…) son canónicos y no se
    traducen;
  - todavía no se activa ni se reescribe texto clínico, salvo la actualización de las guías.
- El encargo nombra las filas 12–18 de R-4 y el panel del examen: entran en X-1.
- **Alcance ampliado por decisión docente (2026-10-07, después de este informe):**
  - en un encuentro en español, todo texto que ve el residente es enteramente español, salvo los nombres
    canónicos de fármacos y los códigos;
  - incluye las filas 1–18 de R-4, el aviso de la foto, las preguntas de aclaración, el texto de la compuerta
    y los rótulos;
  - no se acepta una interfaz mezclada en el candidato final.
- Este documento tiene tres partes:
  1. las guías, ANTES → DESPUÉS;
  2. la brecha bilingüe;
  3. el primer lote de diez decisiones de nivel 1.

## 1. Guías: ANTES → DESPUÉS

- **Fuente de cada corrección:** las filas H-1 a H-11 e I-1 a I-9 del paquete
  (`docs/revision/FACULTY_SIGNOFF_PACKET_PREPILOT.md`, bloques H e I).
- **Cómo se aplicaron:** como el paquete las propuso, salvo los desvíos de 1.3, cada uno con su motivo.
- **Estado:** ninguna guía se marcó aprobada. Las dos dicen «lista para su firma» o «lista para la firma
  docente», «no aprobada», con la firma en blanco.

### 1.1 Guía docente (`docs/GUIA_DOCENTE_PILOTO.md`)

| Fila | Sección | ANTES | DESPUÉS |
|---|---|---|---|
| H-1 | Encabezado | «Estado (cierre prepiloto, 2026-10-02)»; describe lo comprobado al cierre del paquete prepiloto (D-1 a D-11) | «Estado (Fase 0 cerrada el 2026-10-06): lista para su firma, no aprobada»; describe D-1 a D-11 **y lo que cambió la Fase 0 (F0-1 a F0-12)** |
| H-2 | Lo esencial · Casos | «los 31 del banco» | **30 de los 31.** `trauma_hemothorax_41m` queda fuera del piloto de residentes (F0-2): el pabellón no está modelado y, tras el drenaje, el paciente hace un paro hacia el minuto 60. Sigue en el sandbox docente y no se ofrece al dirigir un caso. R1-03, R1-04 y R2-01 no se asignan (F0-4) |
| Nuevo (encargo) | Lo esencial · Idioma (X-1) | — | El piloto corre en inglés y en español. El idioma se elige antes de empezar y queda fijo. Los mensajes nuevos de la Fase 0 sobre las órdenes (recibos, esperas, interrupciones, paro, la respuesta a una aclaración) se dicen en ese idioma (F0-11). El registro, el Trace y el ledger se guardan en inglés; destinos y códigos son canónicos y no se traducen. Lo que todavía se ve en inglés está en «Limitaciones conocidas» |
| H-3 | Lo decidido · E-FAST (TD-48) | «En la 41m se ve el líquido…» | «En la 41m (sólo en el sandbox docente, F0-2) se ve el líquido…» |
| H-4 | Lo decidido · Terminología (R-4) | La firma está en `CIERRE_PREPILOTO.md` | Igual, y agrega: «ordenadas en» el paquete |
| H-5 | La pantalla del encuentro | «**No cambió nada de lo que se registra:** las mismas entradas producen…» | «**El cambio de pantalla no cambió nada de lo que se registra:** … producían … (comprobado antes/después, 2026-10-02). La Fase 0, después, sí cambió la ejecución y el tiempo: ver «La sala desde la Fase 0».» |
| H-7 | Fotos y POCUS · control (TD-54) | «…también el receso drenado de la 41m» | «…(en la 41m, sólo en el sandbox docente, también el receso drenado)» |
| H-9 | Sección nueva: «La sala desde la Fase 0 (2026-10-06)», antes de las limitaciones | — | 11 puntos: cada orden tiene destino y recibo (los destinos, por su código); tiempo (F0-5): esperas, mirada de 2 minutos, «dar X y reevaluar», orden para más tarde, tope de 120 minutos; interrupciones (F0-6): eventos y cambios vigilados de causa desconocida; paro (F0-8): mensaje acordado; la reanimación no está modelada y nada posterior es evaluable; **compuerta de razonamiento** (desvío 1); guardas A–E del registro; respuesta a una aclaración (F0-12, TD-70); envío seguro; oxígeno (F0-9); idioma (F0-11); casos y límites por caso (manifiesto; C-LIMB-ARREST-13). |
| H-8 | Limitaciones · Lector de órdenes | «Un fármaco o un examen nombrado en una lista sin verbo, que el lector no conoce, puede perderse sin aviso.» | Desde la Fase 0, toda orden termina con un destino y un recibo. Lo no entendido queda UNRECOGNIZED y la sala dice «No se entendió…». Siguen las formas sin recibo de TD-69: guardadas en silencio o sin guarda propia, con ejemplos. El registro guarda el turno entero: «léalo» |
| H-10 | Limitaciones · Relato en español | El relato aprobado se ve en español; el resto, en inglés, cada línea entera | Agrega: las frases nuevas de la Fase 0, siempre en español (F0-11); mientras no se activen (X-1), R-4 y el aviso de la foto se ven en inglés; (desvío 5) también se ven en inglés, en todo o en parte: la mayoría de las preguntas de aclaración de la sala, el aviso de la compuerta y varios rótulos. |
| H-11 | Si algo no calza | La firma está en `CIERRE_PREPILOTO.md` | Agrega `F0_11_FRASES_ES.md`, «ordenado en» el paquete |
| H-6 | Fotos · la nota de la foto | «esa nota todavía se ve en inglés» | **Sin cambio:** sigue siendo cierto. Cambia cuando se active su español (X-1, bloque J) |

### 1.2 Guía del residente (`docs/GUIA_RESIDENTE_PILOTO.md`)

| Fila | Sección | ANTES | DESPUÉS |
|---|---|---|---|
| I-1 | Encabezado | «Estado (cierre prepiloto, 2026-10-02)» | «Estado (Fase 0 cerrada el 2026-10-06): lista para la firma docente, no aprobada» |
| I-2 | Antes de empezar · Idioma | Elige el idioma; las pantallas están en español o en inglés; el idioma queda fijo; el relato no aprobado se ve en inglés, cada línea entera | Agrega: «el piloto corre en español y en inglés»; lo que la sala te dice sobre tus órdenes (qué pasó con cada una, las esperas, las interrupciones, el paro) se ve en el idioma que elegiste; algunas líneas del examen (la auscultación, las vías venosas) pueden verse en inglés; (desvío 5) por ahora, muchas preguntas de la sala sobre una orden, el aviso de una orden retenida por el razonamiento y algunos rótulos se ven en inglés, en todo o en parte. |
| I-3 | El encuentro · paso 3 | «si una orden es ambigua, la sala te pregunta, y la pregunta no consume minutos.» | Agrega: tu respuesta completa sólo esa orden. Otra orden escrita en la misma respuesta se lee a continuación, como orden aparte, y la sala dice qué pasó con ella. Si tu respuesta deja algo sin completar, esa otra orden no se ejecuta y la sala lo dice (F0-12, TD-70) |
| I-4 | Paso 4 | «**Explica tu razonamiento cuando puedas:** tu modelo de trabajo, tu prioridad, qué respuesta esperas y cuándo reevaluarás.» | «**Explica tu razonamiento con tus órdenes de manejo:** qué crees que está pasando, qué esperas que ocurra y qué vas a revisar.» Sin alguna de las tres, la sala retiene todo el envío y te pide completarlas, con tus palabras o con las preguntas guiadas (desvío 3). La prioridad y cuándo reevaluar se registran sin retener la orden. Una intervención urgente nunca se retiene. |
| I-5 | Paso 5 | «el tiempo avanza con tus órdenes y reevaluaciones» | Agrega: las esperas («espera u observa 15 minutos»); «reevalúa» sin número es una mirada de 2 minutos; «da X y reevalúa»; para ver un efecto, un intervalo; como máximo 120 minutos por paso; una espera se corta si ocurre algo importante. |
| I-7 | Paso 6, nuevo | — | «**Si el paciente hace un paro,** la sala lo dice. La reanimación no está modelada en este piloto: nada de lo que escribas después se ejecuta ni se evalúa.» Los dos pasos siguientes pasan a ser el 7 y el 8 |
| I-6 | La pantalla · «Manejo» | «…la sala te dice qué pasó con tu última orden.» | Agrega «(su recibo)» y ejemplos, con su inglés entre paréntesis (desvío 4): «No se entendió: …»; «Registrado como tu decisión, no administrado»; «No se hizo ahora»; en un envío con varias órdenes, qué se ejecutó y qué no. |
| I-8 | Punto nuevo, después de «Manejo» | — | Punto «**Envía una vez**»: «Enviar» se desactiva mientras la sala procesa; un doble clic o una recarga no repiten una orden; un envío interrumpido se dice y no se repite. |
| I-9 | La foto | «(por ahora, en inglés)» | **Sin cambio:** sigue siendo cierto hasta que se active su español (X-1, bloque J) |

### 1.3 Desvíos respecto del texto del paquete

1. **H-9 tiene un punto más, «Compuerta de razonamiento».**
   - El encargo pide describir la compuerta, y el texto H.2 del paquete no la tenía.
   - El texto sale de F0-10 y del código: `app.py`, `REASONING_GATE_BLOCKING` y `REASONING_GATE_NOTED`, y
     `urgent_interventions.py`.
2. **El punto «Idioma (X-1)» de la guía docente y la frase bilingüe de I-2 son nuevos.**
   - El encargo pide describir el piloto bilingüe; el paquete no tenía esas frases.
   - Dicen sólo lo comprobado en la sección 2.
3. **I-4 no cita «ORDEN RETENIDA — FALTA EL RAZONAMIENTO».**
   - El residente no ve ese rótulo. Mientras la orden está retenida, la sala oculta esa pregunta y muestra el
     bloque de la compuerta. El aviso de ese bloque está en inglés: «An understood order is being held…»
     (`app.py:10992`).
   - Por eso la guía dice qué pasa, sin citar ningún rótulo. La guía docente tampoco lo cita.
4. **I-6 cambia la forma de los ejemplos, no su contenido.**
   - Sigue la convención de la guía: el texto en español de la pantalla y, entre paréntesis, su inglés.
   - La explicación va después de los dos puntos.
5. **H-10 e I-2 tienen una frase más: lo anterior a la Fase 0 que hoy se ve en inglés (2.4).** Sin ella, las
   guías dirían que la aclaración se ve en español, y no es así.
6. **H-8 queda en dos sub-puntos:** el recibo y TD-69, con el texto del paquete.

### 1.4 Qué no cambió

- **Puntaje, D1–D5, rúbricas, casos, motor y criterios de evaluación:** sin cambio. Sólo se tocaron archivos de
  `docs/`.
- **La intención formativa de las dos guías:**
  - es un piloto formativo, sin nota global, ranking ni IA que evalúe;
  - el foco de aprendizaje aparece después de la revisión;
  - el residente actúa como en la práctica.
- **Lo que el paquete marcó como vigente en el bloque H:** sin tocar.

### 1.5 Qué cambiará en las guías cuando se active el español

- Las frases que dicen qué se ve en inglés en un encuentro en español:
  - H-6 e I-9 (el aviso de la foto);
  - la última frase de H-10;
  - la parte de I-2 sobre el examen y su última frase;
  - la última frase del punto «Idioma (X-1)».
- Con las decisiones del 2026-10-07, también:
  - la limitación TD-51 de la guía docente, que todavía dice «diferida» (A-2 la decidió para antes del
    candidato final), al implementarse;
  - los modos Talk, Examine, Tests y Treat, que la guía del residente nombra en inglés, si se traducen (X-1).
- Es una edición de documentación (S-C): por sí sola no cambia el SHA.

## 2. Brecha bilingüe (X-1 / F0-11)

### 2.1 Cómo se comprobó (2026-10-07, código de `8ff41a4`)

- **Ruta de cada texto en la pantalla (`app.py`, `render_event`):**
  - las entradas de los tipos traducidos pasan por `language.say`: respuesta del paciente, procedimiento,
    aclaración, y recibos y avisos (`prototype`);
  - el examen pasa por `language.examination`;
  - el registro, el Trace y el ledger guardan el inglés.
- **Frases K:** para las 21 frases K, `language.say(EN, "es")` devuelve exactamente el español de la hoja
  `F0_11_FRASES_ES.md`. Para K-20 también lo hace `language.examination`.
- **Eventos K-E:** los 17 se dicen en español dentro de K-6 y K-9 (`test_phase0_spanish.py`).
- **R-4, filas 12–18:** `language.say` devuelve el español; `language.examination` devuelve el inglés.
- **Pruebas focalizadas:** `test_phase0_spanish.py`, `test_hypoglycemia_lines.py`, `test_pe_notes_and_row_18.py`
  y `test_room_labels_in_spanish.py`, 125 passed.
- **No se abrió la app en un navegador:** las superficies salen de leer el código, no de capturas.

**Superficies:**

- **M:** bajo «Manejo» (el recibo o el aviso de la última orden; una pregunta queda a la vista hasta que se
  responde) y en la fila de esa orden en «Indicaciones».
- **E:** una entrada en «Evolución».
- **X:** el examen, es decir, la entrada EXAMINATION de una región en «Historia y examen» y en «Evolución».
- **R:** el registro, el Management Trace y el ledger. Guardan siempre el inglés, en ambos idiomas: es el texto
  canónico.

### 2.2 Tabla

Los textos EN y ES de las filas K son los de la hoja F0-11, con valores de muestra. Cada par se comprobó contra
`language.say` al generar esta tabla.

| ID | Inglés (fuente) | Español actual | Dónde se ve el inglés hoy | Dónde se ve el español hoy | ¿Activo en ambos idiomas? | ¿Requiere cambio de implementación? |
|---|---|---|---|---|---|---|
| K-1 | Not understood: "Zyvox IV". Nothing was given or done for it. Write it again in other words if you still want it. | No se entendió: «Zyvox IV». No se administró ni se hizo nada por ello. Escríbelo de nuevo con otras palabras si aún lo quieres. | Encuentro en inglés: M. Siempre: R | Encuentro en español: M | SÍ | NO (sólo si la firma cambia la redacción) |
| K-2 | Not understood: "Stop the infusion". Nothing was given or done for it. Write it again in other words if you still want it. | No se entendió: «Stop the infusion». No se administró ni se hizo nada por ello. Escríbelo de nuevo con otras palabras si aún lo quieres. | Encuentro en inglés: M. Siempre: R | Encuentro en español: M | SÍ | NO (sólo si la firma cambia la redacción) |
| K-3 | Recorded as your decision, not given: "Stop the infusion". This simulator does not model a response to it in this case, so nothing changed. | Registrado como tu decisión, no administrado: «Stop the infusion». Este simulador no modela una respuesta a ello en este caso, así que nada cambió. | Encuentro en inglés: M. Siempre: R | Encuentro en español: M | SÍ | NO (sólo si la firma cambia la redacción) |
| K-4 | On reassessment at the bedside, 2 minutes later, BP 100/60 mmHg. | Al reevaluar en la cabecera, 2 minutos después, PA 100/60 mmHg. | Encuentro en inglés: E. Siempre: R | Encuentro en español: E | SÍ | NO (sólo si la firma cambia la redacción) |
| K-5 | Normal saline 1000 mL. On reassessment at the bedside 1 minute after the order, BP 100/60 mmHg. | Suero fisiológico 1000 mL. Al reevaluar en la cabecera, 1 minuto después de la orden, PA 100/60 mmHg. | Encuentro en inglés: E. Siempre: R | Encuentro en español: E | SÍ | NO (sólo si la firma cambia la redacción) |
| K-6 | Given: Normal saline 1000 mL. The wait was interrupted after 7 minutes of the 15 you asked for, at minute 7: systolic pressure 62 mmHg and falling. Now, BP 62/30 mmHg. | Administrado: Suero fisiológico 1000 mL. La espera se interrumpió tras 7 min de los 15 que pediste, en el minuto 7: presión sistólica de 62 mmHg y en descenso. Ahora, PA 62/30 mmHg. | Encuentro en inglés: E. Siempre: R | Encuentro en español: E | SÍ | NO (sólo si la firma cambia la redacción) |
| K-7 | Cardiac arrest occurred at minute 12. Resuscitation management is not modelled in this pilot. Subsequent management is not assessable. | Se produjo un paro cardíaco en el minuto 12. El manejo de la reanimación no está modelado en este piloto. El manejo posterior no es evaluable. | Encuentro en inglés: M. Siempre: R | Encuentro en español: M | SÍ | NO (sólo si la firma cambia la redacción) |
| K-8 | Not executed: "Give 1 L LR". The patient is in cardiac arrest; resuscitation management is not modelled in this pilot. | No se ejecutó: «Give 1 L LR». El paciente está en paro cardíaco; el manejo de la reanimación no está modelado en este piloto. | Encuentro en inglés: M. Siempre: R | Encuentro en español: M | SÍ | NO (sólo si la firma cambia la redacción) |
| K-9 | The wait was interrupted after 3 minutes, at minute 3: cardiac arrest, pulse lost. Now, No pulse: Ventricular fibrillation on the monitor; no blood pressure; not breathing; unresponsive. | La espera se interrumpió tras 3 min, en el minuto 3: paro cardíaco, sin pulso. Ahora, sin pulso: Fibrilación ventricular en el monitor; sin presión arterial; sin respiración; sin respuesta. | Encuentro en inglés: E. Siempre: R | Encuentro en español: E | SÍ | NO (sólo si la firma cambia la redacción) |
| K-10 | Not done now: "Give aspirin 300 mg in 30 minutes". An order for a later time is not carried out in this pilot: nothing was given and nothing was scheduled. Write it again when you want it done. | No se hizo ahora: «Give aspirin 300 mg in 30 minutes». En este piloto, una orden para más tarde no se ejecuta: no se administró nada ni se programó nada. Escríbela de nuevo cuando quieras que se haga. | Encuentro en inglés: M. Siempre: R | Encuentro en español: M | SÍ | NO (sólo si la firma cambia la redacción) |
| K-11 | Your order "Give the normal saline" was interrupted while it was being processed, and nothing of it was applied. Nothing will be repeated automatically: check the patient's state, and send it again if it is still needed. | Tu orden «Give the normal saline» se interrumpió mientras se procesaba, y no se aplicó nada de ella. Nada se repetirá automáticamente: revisa el estado del paciente y envíala de nuevo si todavía es necesaria. | Encuentro en inglés: M. Siempre: R | Encuentro en español: M | SÍ | NO (sólo si la firma cambia la redacción) |
| K-12 | Your order "Give 1 L LR" was interrupted while it was being processed, and part of it may have been applied. Nothing will be repeated automatically: check the patient's state, and send it again if it is still needed. | Tu orden «Give 1 L LR» se interrumpió mientras se procesaba, y es posible que una parte de ella se haya aplicado. Nada se repetirá automáticamente: revisa el estado del paciente y envíala de nuevo si todavía es necesaria. | Encuentro en inglés: M. Siempre: R | Encuentro en español: M | SÍ | NO (sólo si la firma cambia la redacción) |
| K-13 | **PART OF THIS ORDER WAS NOT CARRIED OUT** / Executed now: **aspirin 300 mg PO**. / Not carried out: **norepinephrine**. Nothing of it has been given; write it again as a new order if you still want it. | **PARTE DE ESTA ORDEN NO SE EJECUTÓ** / Ejecutado ahora: **aspirin 300 mg PO**. / No ejecutado: **norepinephrine**. No se ha administrado nada de ello; escríbelo de nuevo como una orden nueva si aún lo quieres. | Encuentro en inglés: M. Siempre: R | Encuentro en español: M | SÍ | NO (sólo si la firma cambia la redacción) |
| K-14 | **PART OF THIS ORDER IS HELD — CLARIFICATION REQUIRED** / Executed now: **aspirin 300 mg PO**. / Held until you answer: **normal saline**. Nothing of it has been given. | **PARTE DE ESTA ORDEN ESTÁ RETENIDA — SE NECESITA UNA ACLARACIÓN** / Ejecutado ahora: **aspirin 300 mg PO**. / Retenido hasta que respondas: **suero fisiológico**. No se ha administrado nada de ello. | Encuentro en inglés: M. Siempre: R | Encuentro en español: M | SÍ | NO (sólo si la firma cambia la redacción) |
| K-15 | Not run: "ceftriaxone 2 g IV" was written in the answer to the question above, which completes the held order only. Write it again as a new order if you still want it. | No se ejecutó: «ceftriaxone 2 g IV» se escribió en la respuesta a la pregunta anterior, que solo completa la orden retenida. Escríbelo de nuevo como una orden nueva si aún lo quieres. | Encuentro en inglés: M. Siempre: R | Encuentro en español: M | SÍ | NO (sólo si la firma cambia la redacción) |
| K-16 | Also in your answer: "give 500 mL LR". The answer completes the held order only; this order is read next, as an order of its own, with its own receipt. | También en tu respuesta: «give 500 mL LR». La respuesta solo completa la orden retenida; esta orden se lee a continuación, como una orden propia, con su propio recibo. | Encuentro en inglés: M. Siempre: R | Encuentro en español: M | SÍ | NO (sólo si la firma cambia la redacción) |
| K-17 | Specify a reassessment interval from 0 to 120 minutes. The simulator moves the clock at most 120 minutes in one step (a limit of this pilot): write a wait or a reassessment of 120 minutes or less, and wait again afterwards if you need more time. | Indica un intervalo de reevaluación de 0 a 120 minutos. El simulador avanza el reloj como máximo 120 minutos de una vez (un límite de este piloto): escribe una espera o una reevaluación de 120 minutos o menos, y vuelve a esperar después si necesitas más tiempo. | Encuentro en inglés: M. Siempre: R | Encuentro en español: M | SÍ | NO (sólo si la firma cambia la redacción) |
| K-18 | Circulatory arrest after twenty-five minutes without effective adrenaline: the adrenaline given earlier had worn off and the reaction had come back. Nothing else that was given acts on the reaction. | Paro circulatorio tras veinticinco minutos sin adrenalina eficaz: la adrenalina administrada antes había perdido su efecto y la reacción había vuelto. Nada más de lo administrado actúa sobre la reacción. | Encuentro en inglés: E. Siempre: R | Encuentro en español: E | SÍ | NO (sólo si la firma cambia la redacción) |
| K-19 | oxygen non-rebreather mask 15 L/min: no flow was written; the standard non-rebreather flow, 15 L/min, was used. | Oxígeno por mascarilla con reservorio a 15 L/min: no se escribió un flujo; se usó el flujo habitual de la mascarilla con reservorio, 15 L/min. | Encuentro en inglés: M. Siempre: R | Encuentro en español: M | SÍ | NO (sólo si la firma cambia la redacción) |
| K-20 | Unresponsive, not breathing, no central pulse: the patient is in cardiac arrest. Resuscitation is not modelled in this pilot. | Sin respuesta, sin respiración, sin pulso central: el paciente está en paro cardíaco. La reanimación no está modelada en este piloto. | Encuentro en inglés: X (y E). Siempre: R | Encuentro en español: X (y E) | SÍ | NO (sólo si la firma cambia la redacción) |
| K-21 | Circulatory arrest after twenty-five minutes of untreated anaphylaxis. Adrenaline was the treatment that was missing; nothing else that was given acts on the reaction. | Paro circulatorio tras veinticinco minutos de anafilaxia no tratada. La adrenalina era el tratamiento que faltaba; nada más de lo administrado actúa sobre la reacción. | Encuentro en inglés: E. Siempre: R | Encuentro en español: E | SÍ | NO (sólo si la firma cambia la redacción) |
| K-E1 a K-E17 | Los 17 eventos que cortan una espera (por ejemplo, «complete atrioventricular block», «systolic pressure 62 mmHg and falling», «a critical change»), dentro de K-6 y K-9 | Los 17, en español (por ejemplo, «bloqueo auriculoventricular completo», «presión sistólica de 62 mmHg y en descenso», «un cambio crítico»); la lista está en el bloque K del paquete | Encuentro en inglés: E. Siempre: R | Encuentro en español: E | SÍ | NO (sólo si la firma cambia la redacción) |
| A-12 (R-4, 54m) | Peripheral cannula in the left forearm; the skin around its tip is slightly swollen and cool. | Cánula periférica en el antebrazo izquierdo; la piel alrededor del extremo del catéter está levemente aumentada de volumen y fría. | X, en **ambos** idiomas (región «Vascular access»). Siempre: R | Ninguna pantalla | **NO** | **SÍ** (2.3) |
| A-13 (R-4, hipoglicemia) | Peripheral cannula in the left forearm; the site is clean, without swelling or tenderness. | Cánula periférica en el antebrazo izquierdo; el sitio está limpio, sin aumento de volumen ni dolor a la palpación. | X, en ambos idiomas. Siempre: R | Ninguna pantalla | **NO** | **SÍ** |
| A-14 (R-4, hipoglicemia) | Peripheral cannula in the left forearm; the forearm around it is swollen, pale, cool and tender. | Cánula periférica en el antebrazo izquierdo; el antebrazo a su alrededor está aumentado de volumen, pálido, frío y doloroso a la palpación. | X, en ambos idiomas. Siempre: R | Ninguna pantalla | **NO** | **SÍ** |
| A-15 (R-4, hipoglicemia) | A second peripheral cannula in the right forearm; the site is clean. | Una segunda cánula periférica en el antebrazo derecho; el sitio está limpio. | X, en ambos idiomas. Siempre: R | Ninguna pantalla | **NO** | **SÍ** |
| A-16 (R-4, hipoglicemia) | An intraosseous needle in place (humeral). | Una aguja intraósea instalada (humeral). | X, en ambos idiomas. Siempre: R | Ninguna pantalla | **NO** | **SÍ** |
| A-17 (R-4, hipoglicemia) | An intraosseous needle in place; no site was recorded. | Una aguja intraósea instalada; no se registró el sitio. | X, en ambos idiomas. Siempre: R | Ninguna pantalla | **NO** | **SÍ** |
| A-18 (R-4, hipoglicemia) | Dextrose {n}% runs at {n} mL/h through the cannula in the left forearm. | El suero glucosado al {n} % pasa a {n} mL/h por la cánula del antebrazo izquierdo. | X, en ambos idiomas. Siempre: R | Ninguna pantalla | **NO** | **SÍ** |
| PANEL (2.3) | El panel del examen: `language.examination` no conoce las filas 2–18 de R-4 | — | X, en ambos idiomas: esas filas, enteras en inglés | Ninguna pantalla | **NO** | **SÍ** |

**Notas:**

- **K-13 y K-14:** dentro de la frase en español, el nombre del fármaco queda como lo escribe el motor (por
  ejemplo, «aspirin 300 mg PO», «norepinephrine»). Es la convención declarada (decisión 16), no una brecha.
  - El suero sí se traduce («suero fisiológico»).
  - El paquete marca K-13 «REVIEW CLOSELY» por esos dos criterios.
- **Las palabras del residente entre «»** quedan como las escribió, en las dos versiones.
- **K-21** es anterior a la Fase 0. Se tradujo con K-18 para que el paro de la anafilaxia no se lea en dos
  idiomas.

### 2.3 El problema del panel del examen

- **Qué pasa:**
  - El residente examina la región «Vascular access». La sala guarda el hallazgo como una entrada EXAMINATION
    (`app.py:10961`, desde `family_engine.current_findings` → `glucose_rescue.access_finding`).
  - Esa entrada se dibuja con `language.examination`, que sólo conoce:
    - las frases de `_EXAMINATION_SENTENCES_ES`;
    - las plantillas de «Breathing» y de la circulación;
    - el relato aprobado de cada caso.
  - El español de las filas 12–18 vive en las reglas de `language.say` (`language.py`, R-4), que el panel no usa.
  - Resultado: en un encuentro en español, esas líneas se ven enteras en inglés.
- **Lo saben el código y las pruebas:**
  - `spanish_drafts.py` lo anota (líneas 96–97);
  - la prueba `test_hypoglycemia_lines.py::test_the_room_says_it_in_spanish` comprueba `language.say`, no la
    ruta del panel. Por eso pasa.
- **Alcance:** lo mismo vale para las filas 2–11 de R-4 (región «Respiratory»), cuyo español además es borrador.
- **Lo que habrá que cambiar después de la firma (no se hizo):**
  - que el panel diga entero el español aprobado de esas filas;
  - una prueba por la ruta del panel (`language.examination`), en los dos idiomas.
  - Es un cambio de código: nuevo SHA y contrato de promoción (16.4).

### 2.4 Fuera de las 19 frases: lo anterior a la Fase 0 que hoy se ve en inglés o mezclado

No se corrigió. El encargo nombra la aclaración y «otra pantalla activa del piloto», así que se informa aquí.

**Actualizado el 2026-10-07:** el inventario completo, con la fuente de cada frase y su español propuesto, está en
`docs/revision/X1_ESPANOL_PROPUESTO.md`. Corrige la cifra de abajo: 40 de las preguntas de `app.py` son del motor
heredado y ningún caso del piloto llega a ellas (su anexo A); las que un residente puede ver son 73.

| Grupo | Qué ve hoy un residente en español | Medida | Registro |
|---|---|---|---|
| Preguntas de aclaración de la sala | Muchas, enteras en inglés: «What route would you like to use (IV or PO)?», «Please specify the fluid volume (for example, 500 mL or 1 L).». Otras, mezcladas, porque `language.say` traduce palabras sueltas dentro de una oración que no conoce: «What infusión de norepinephrine rate would you like to inicio (for example, 0.05 mcg/kg/min or 5 mcg/min)?», «Indica cardioversion energy in joules, from 1 to 360.» | De 102 textos escritos como literales (36 en `app.py`, 66 que devuelve `family_engine.py`): 52 en inglés, 31 mezclados, 19 en español, según un detector de palabras inglesas (cifra aproximada). No se midió cuántas aparecen en los 30 casos; las de dosis, vía, flujo y ritmo son frecuentes. | TD-79 (nueva) |
| Bloque de la compuerta de razonamiento | En inglés: el aviso «An understood order is being held…», «Held order:», el botón «Complete reasoning & execute held order», la nota «Or answer naturally below…» y el ejemplo de un campo. Las preguntas guiadas sí están en español. | — | TD-61 (en parte) y TD-79 |
| Rótulos de la sala | Los modos (Talk, Examine, Tests, Treat; las guías los nombran así), «Current treatments», «Current support», «Diagnostics», «Cancel pending orders», «Examine patient», los nombres de las regiones del examen, «Ask the patient», el texto de ejemplo del cuadro de escritura, «Complete Encounter & Begin Review», «Save & return to dashboard» y «End this attempt without completing review». Al cerrar, «Latest response» y «Clinical chart…». | — | TD-61 (en parte) y TD-79 |
| R-4, filas 1–11 | En inglés: en el panel del examen, y la fila 1 (A-1) como entrada. Su español es borrador | — | Paquete, bloque A |
| Aviso de la foto | En inglés; su español propuesto sólo está en el §2 del cierre | — | Paquete, bloque J |

### 2.5 Qué habrá que cambiar, después de la firma (no se hizo)

1. **El panel del examen (2.3):** las filas 12–18 de R-4, y las 2–11 si X-1 las incluye.
2. **Las 21 frases K y los 17 eventos:** nada, salvo que la firma cambie una redacción. En ese caso se cambia
   su regla en `_PHASE0_RULES` y su prueba en `test_phase0_spanish.py`.
3. **Si X-1 abarca lo de 2.4:**
   - qué entra: las preguntas de aclaración (TD-79), los rótulos (TD-61), las filas 1–11 de R-4 y el aviso de
     la foto;
   - cada uno necesita su español aprobado (TD-46: no hay traducción automática); hoy ninguno lo tiene;
   - lo mezclado no se arregla con más palabras sueltas: necesita frases enteras.
4. **Las guías, después de activar (1.5).**

## 3. Primer lote de nivel 1: las diez primeras decisiones del paquete

- **Orden del paquete:** A-1, A-2, A-9 y B-19 a B-25.
- **Dónde está cada decisión:** el texto exacto en inglés y en español y sus casillas (APPROVE · REVISE · DEFER)
  están en el paquete, en la fila de cada ID. Aquí va el índice del lote; las casillas no se duplican.
- **Comprobado hoy contra el código:**
  - las siete notas B-19 a B-25, generadas por `pe_obstruction`, coinciden con el paquete en inglés y, por
    `language.say`, en español;
  - A-1, A-2 y A-9 existen en inglés en el código, y su español es el borrador de `spanish_drafts.py`, que hoy
    no se muestra.

| # | ID · fila | Dónde lo ve | Por qué es nivel 1 | Español hoy | Recomendación |
|---|---|---|---|---|---|
| 1 | A-1 · R-4, fila 1 | Residente: entrada de la sala al paro hemorrágico de la 27m (la 41m, sólo en el sandbox). Docente: el registro | Atribuye una causa al paro | Borrador: en español se ve el inglés | **APPROVE AS IS** (vinculada con K-E4 y K-7) |
| 2 | A-2 · R-4, fila 2 | Residente: examen, «Respiratory», 75f | Ambigüedad conocida (TD-51): sin tratamiento, dice «increased respiratory effort» mientras el esfuerzo ya es «Exhausted» | Borrador | **REVIEW CLOSELY** (la traducción es fiel; el problema es del motor y la guía docente lo declara) |
| 3 | A-9 · R-4, fila 9 | Residente: examen, «Respiratory», 35m y 67f | Dice algo distinto en inglés y en español (TD-52 a) | Borrador | **NEEDS REVISION** del inglés. El paquete decía REVIEW CLOSELY; con X-1 cerrada se muestran las dos versiones y no dicen lo mismo. Corregir el inglés es código (nuevo SHA) |
| 4 | B-19 · nota 1, shock obstructivo | Residente: entrada de la sala al trombolizar en la 33f o la 61m. Docente: el registro y el Trace (inglés) | Declara el criterio de indicación (D-4) | Activo (D-4) | **APPROVE AS IS** |
| 5 | B-20 · nota 2, hipotensión sostenida | Ídem | Declara el criterio de indicación (D-4) | Activo | **APPROVE AS IS** |
| 6 | B-21 · nota 3, sin indicación, presión baja | Ídem | Juzga la indicación durante el encuentro | Activo | **APPROVE AS IS** |
| 7 | B-22 · nota 4, vasopresor innecesario | Ídem | Juzga la indicación | Activo | **APPROVE AS IS** |
| 8 | B-23 · nota 5, normotensión | Ídem | Juzga la indicación | Activo | **APPROVE AS IS** |
| 9 | B-24 · nota 6, resto del esquema | Ídem | Dice qué se dio y que no es un segundo curso | Activo | **APPROVE AS IS** (el fármaco va en español, «alteplasa», como pidió D-5; K-13 deja los nombres en inglés) |
| 10 | B-25 · nota 7, segundo curso | Ídem | Declara una simplificación del motor y registra la exposición | Activo | **APPROVE AS IS** |

**Decisión docente (2026-10-07):** A-1 y B-19 a B-25, APPROVE; A-2 y A-9, REVISE. Están registradas en el
paquete y en el Decision File, sin implementar.

### 3.2 Segundo lote de nivel 1 (propuesto el 2026-10-07)

Orden del paquete: B-26, C-37, D-39 a D-43, E-45, E-46 y F-47. Los textos exactos y las casillas están en el
paquete. Cada texto se comprobó contra el código: el inglés, en el banco o en el motor; el español, en
`language.py`, `report_language.py` o `spanish_drafts.py`.

| # | ID · fila | Dónde lo ve | Por qué es nivel 1 | Español hoy | Recomendación |
|---|---|---|---|---|---|
| 1 | B-26 · aviso del sangrado (33f) | Residente: entrada de la sala cuando sangra tras la lisis. Docente: el registro | Atribuye una causa a la decisión de trombolizar | Activo | **APPROVE AS IS** (vinculada con D-40) |
| 2 | C-37 · 27m, «General appearance» tras una medida | Residente: examen de la 27m | Dice si la medida detuvo el sangrado (escalar o no) | Activo (panel) | **APPROVE AS IS** |
| 3 | D-39 · encabezado y aviso de los límites | Docente: rúbrica y objetivos del caso | Declara lo que nunca se cobra | Activo | **APPROVE AS IS** |
| 4 | D-40 · límite de la 33f | Docente: rúbrica y objetivos | Declara un límite y lo que no se evalúa | Sólo en la guía docente | **APPROVE AS IS** (vinculada con B-26) |
| 5 | D-41 · límite de la 70f | Ídem | Declara un límite y lo no evaluable | Sólo en la guía docente | **APPROVE AS IS** (decidir con E-46) |
| 6 | D-42 · límite de las neumonías (46f, 83m) | Ídem | Declara un límite | Sólo en la guía docente | **APPROVE AS IS** (una decisión para los dos casos) |
| 7 | D-43 · límite de la 27m | Ídem | Declara un límite | Sólo en la guía docente | **APPROVE AS IS** |
| 8 | E-45 · C14 de la 52m | Docente: la declaración C14 del caso (en inglés también en español, TD-07) | Criterio de evaluación | Borrador | **APPROVE AS IS** (decidir con F-47) |
| 9 | E-46 · C14 de la 70f | Ídem | Criterio de evaluación | Borrador | **APPROVE AS IS** (decidir con D-41) |
| 10 | F-47 · ficha POCUS de la 52m | Docente: la ficha R-2 y la declaración C14 | Criterio de evaluación | Borrador | **APPROVE AS IS** (decidir con E-45) |

**Decisión docente (2026-10-07):** B-26, C-37, D-39, D-40, D-41, D-43, E-45, E-46 y F-47, APPROVE; D-42, REVISE:
se mantienen el inglés y el motor, y D-42 lleva un español propio para las dos neumonías, propuesto en el paquete
(bloque D-42). Están registradas en el paquete y en el Decision File, sin implementar.

### 3.3 Tercer lote de nivel 1 (propuesto el 2026-10-07)

Orden del paquete: F-48 a F-57, diez fichas POCUS C14 YES (R-2). Los textos exactos y las casillas están en el
paquete. **Comprobado el 2026-10-07:** en las diez, el componente y la evidencia en inglés coinciden con la
declaración C14 del banco (`case_assessment_bank.CASES[<caso>]["objectives"]["C14"]`), y su español con el
borrador (`spanish_drafts.C14`). Las diez son C14 = yes y ninguna tiene casilla marcada.

Todas son nivel 1 porque son criterio de evaluación. Las ve el docente, en la ficha R-2 y en la declaración C14 del
caso (en inglés también en español, TD-07); su español es borrador inactivo.

| # | ID · caso | Qué observa C14 | Recomendación |
|---|---|---|---|
| 1 | F-48 · `acs_61m_posterior` | Usar la motilidad informada, con el ECG y las derivaciones posteriores, para priorizar la reperfusión | **APPROVE AS IS** — no se exige reconocer la hipocinesia posterior sutil; una aorta no dilatada no descarta una disección |
| 2 | F-49 · `acs_70f_left_main` | Decidir volumen, soporte y urgencia con la función del VI a la vista, y adaptarlos a la respuesta | **REVIEW CLOSELY** — D-8: la sobrecarga no cambia pulmón, examen, saturación ni POCUS (TD-53); confirmar que la ficha no exige verla. Es el mismo criterio de D-41 y E-46, ya aprobadas |
| 3 | F-50 · `gi_bleed_57m` | Usar la volemia por POCUS para guiar y reevaluar la reanimación | **APPROVE AS IS** |
| 4 | F-51 · `gi_bleed_72f` | Lo mismo, con la VCI que colapsa | **APPROVE AS IS** |
| 5 | F-52 · `obstructive_pyelonephritis_58f` | Guiar con POCUS los fluidos y la hemodinamia en el shock séptico | **APPROVE AS IS** — la VCI de control no cambia (TD-54) y la evidencia no exige reevaluar con POCUS |
| 6 | F-53 · `pneumonia_46f` | Guiar y reevaluar con POCUS los fluidos y la hemodinamia | **REVIEW CLOSELY** — una evidencia pide reevaluar con POCUS tras el volumen; el control muestra la VCI que se llena y ninguna línea B nueva (D-42): confirmar que se juzga con la VCI y la saturación, nunca con las líneas B. Decidir con F-54 |
| 7 | F-54 · `pneumonia_83m` | Lo mismo | **REVIEW CLOSELY** — igual que F-53 |
| 8 | F-55 · `pulmonary_edema_58m` | Decidir nitrato, diurético o VMNI, y no dar volumen, por las líneas B, el VI y la VCI | **APPROVE AS IS** — decidir con F-56 (el mismo texto C14) |
| 9 | F-56 · `pulmonary_edema_75f` | Lo mismo | **APPROVE AS IS** — llega con la vista neutral (P-07); la ficha no depende de la foto |
| 10 | F-57 · `pulmonary_embolism_33f` | Integrar el VD y la TVP proximal con la estabilidad: anticoagular antes de confirmar y no trombolizar | **APPROVE AS IS** |

**Decisión docente (2026-10-07):** F-48 a F-57, APPROVE. En F-49, el límite de D-41 y E-46 es vinculante: no se
exige detectar la sobrecarga por examen ni por POCUS cuando el motor no la modela. F-53 y F-54 quedan vinculadas a
D-42: la respuesta al volumen se juzga con la VCI y la saturación, nunca con líneas B nuevas. Registradas en el
paquete y en el Decision File (décima actualización), sin implementar.

### 3.4 Cuarto lote de nivel 1 (propuesto el 2026-10-07)

Orden del paquete: F-58, F-60, G-61, H-62, I-63, K-1 y K-2 (una decisión), K-3, K-4, K-5 y K-6. Los textos exactos y
las casillas están en el paquete. **Comprobado el 2026-10-07:**

- F-58 y F-60: el componente y la evidencia en inglés coinciden con el banco, y su español con el borrador.
- G-61: el documento termina con la tabla que genera `tdfc_review.final_table_markdown()`; lo comprueba
  `test_tdfc_opportunities.py`, 12 de 12.
- K-1 a K-6: `language.say` convierte cada ejemplo inglés exactamente en el español del paquete, que también está en
  la hoja F0-11. Están activas en los dos idiomas.

| # | ID | Qué se decide | Recomendación |
|---|---|---|---|
| 1 | F-58 · `pulmonary_embolism_61m` | Decidir reperfusión y anticoagulación por la sobrecarga del VD (signo D o de McConnell) o la TVP, en shock, sin esperar la angio-TC | **APPROVE AS IS** |
| 2 | F-60 · `trauma_limb_hemorrhage_27m` | Dirigir el control de la hemorragia con el E-FAST negativo: mantenerlo en la extremidad y decir qué lo cambiaría | **APPROVE AS IS** — el E-FAST de control repite la llegada (D-43, ya aprobada) |
| 3 | G-61 · tabla TDFC final | Las oportunidades TD1, F1, C1 y C3 de los 31 casos (T-2: C1 YES; T-3 y T-4: NO) | **APPROVE AS IS** |
| 4 | H-62 · guía docente | La guía actualizada | **DEFER la firma** (recomendación nueva): describe la sala anterior a X-1 y el calendario anterior del relato (lista abajo). Actualizarla, sólo documentación, cuando se implemente X-1 y se revise el relato, y firmar la versión que describe el candidato final |
| 5 | I-63 · guía del residente | La guía actualizada | **DEFER la firma**, por la misma razón |
| 6 | K-1 y K-2 · orden no entendida | «No se entendió: «…». No se administró ni se hizo nada por ello. Escríbelo de nuevo con otras palabras si aún lo quieres.» | **APPROVE AS IS** |
| 7 | K-3 · registrada, no administrada | «Registrado como tu decisión, no administrado: «…». Este simulador no modela una respuesta a ello en este caso, así que nada cambió.» | **APPROVE AS IS** |
| 8 | K-4 · mirada en la cabecera | «Al reevaluar en la cabecera, 2 minutos después, PA …» | **APPROVE AS IS** |
| 9 | K-5 · mirada después de una orden | «Suero fisiológico 1000 mL. Al reevaluar en la cabecera, 1 minuto después de la orden, PA …» | **APPROVE AS IS** — con X1-0, un fármaco en esa línea se nombrará en español al implementarse |
| 10 | K-6 · espera interrumpida | «Administrado: Suero fisiológico 1000 mL. La espera se interrumpió tras 7 min de los 15 que pediste, en el minuto 7: …» | **APPROVE AS IS** — lo mismo de K-5; la mayúscula tras «Administrado:» es cosmética |

**Frases de las guías que las decisiones del 2026-10-07 dejan desactualizadas** (H-62 e I-63):

- Guía del residente:
  - líneas 16–24 («Idioma»): el relato puede verse en inglés; líneas del examen, muchas preguntas de la sala, el
    aviso de una orden retenida y algunos rótulos se ven en inglés;
  - línea 75: nombra los modos en inglés (L-01);
  - líneas 93–94: el aviso de la foto se ve «por ahora, en inglés» (J).
- Guía docente:
  - líneas 25–30 («Idioma (X-1)»): remite a lo que «todavía se ve en inglés»;
  - líneas 149–150: el aviso de la foto «todavía se ve en inglés» (J);
  - líneas 156–159 (TD-54): junta el trauma y la neumonía; D-42 tiene su español propio;
  - líneas 232–233: «TD-51, diferida»; A-2 quedó decidida para antes del candidato;
  - líneas 238–244 («Relato en español»): el relato se revisa antes del candidato; R-4, el aviso de la foto, las
    preguntas de la sala y la compuerta dejarán de verse en inglés.

**Decisión docente (2026-10-07):** F-58, F-60, G-61, K-1 y K-2, K-3 y K-4, APPROVE. K-5 y K-6, APPROVE: cuando la
orden insertada contiene un fármaco reconocido, rige X1-0 (en un encuentro en español se muestra su nombre en
español; el valor canónico guardado no cambia). H-62 e I-63, DEFER de la firma: no es un rechazo. Se firman cuando
describan el candidato final, después de implementar X-1, A-2 y A-9, la redacción final de D-42, la limpieza de la
interfaz bilingüe y la revisión y activación del relato y de la rúbrica en español. Registradas en el paquete y en el
Decision File (undécima actualización), sin implementar.

### 3.5 Quinto lote de nivel 1 (propuesto el 2026-10-07)

Orden del paquete: K-7 a K-16. Los textos exactos y las casillas están en el paquete. **Comprobado el 2026-10-07:**
en las diez, el inglés y el español del paquete coinciden con la hoja F0-11, y `language.say` convierte cada ejemplo
inglés exactamente en el español del paquete. Están activas en los dos idiomas (S-A).

Las citas entre «» son lo que escribió el residente y no se traducen (paquete, K). X1-0 rige el nombre que inserta
el motor, no la cita.

| # | ID | Qué dice el español activo | Recomendación |
|---|---|---|---|
| 1 | K-7 · paro: mensaje acordado | «Se produjo un paro cardíaco en el minuto 12. El manejo de la reanimación no está modelado en este piloto. El manejo posterior no es evaluable.» | **APPROVE AS IS** |
| 2 | K-8 · orden escrita después del paro | «No se ejecutó: «…». El paciente está en paro cardíaco; el manejo de la reanimación no está modelado en este piloto.» | **APPROVE AS IS** |
| 3 | K-9 · actualización sin pulso | «La espera se interrumpió tras 3 min, en el minuto 3: paro cardíaco, sin pulso. Ahora, sin pulso: Fibrilación ventricular en el monitor; …» | **APPROVE AS IS** — la mayúscula tras «sin pulso:» es cosmética |
| 4 | K-10 · orden para más tarde | «No se hizo ahora: «…». En este piloto, una orden para más tarde no se ejecuta: no se administró nada ni se programó nada. Escríbela de nuevo cuando quieras que se haga.» | **APPROVE AS IS** |
| 5 | K-11 · envío interrumpido, nada aplicado | «Tu orden «…» se interrumpió mientras se procesaba, y no se aplicó nada de ella. Nada se repetirá automáticamente: revisa el estado del paciente y envíala de nuevo si todavía es necesaria.» | **APPROVE AS IS** |
| 6 | K-12 · envío interrumpido, quizá en parte | Lo mismo, con «… y es posible que una parte de ella se haya aplicado.» | **APPROVE AS IS** — conserva la incertidumbre del inglés |
| 7 | K-13 · paquete parcial, parte no ejecutada | «**PARTE DE ESTA ORDEN NO SE EJECUTÓ** … Ejecutado ahora: **aspirin 300 mg PO**. / No ejecutado: **norepinephrine**. …» | **APPROVE con la regla de X1-0**, como K-5 y K-6: se verá «**aspirina 300 mg PO**» y «**noradrenalina**»; el valor canónico no cambia. Antes recomendaba REVISE, que lleva al mismo texto |
| 8 | K-14 · paquete parcial, parte retenida | «**PARTE DE ESTA ORDEN ESTÁ RETENIDA — SE NECESITA UNA ACLARACIÓN** … Ejecutado ahora: **aspirin 300 mg PO**. / Retenido hasta que respondas: **suero fisiológico**. …» | **APPROVE con la regla de X1-0**: se verá «**aspirina 300 mg PO**» |
| 9 | K-15 · orden en la respuesta, con algo retenido | «No se ejecutó: «…» se escribió en la respuesta a la pregunta anterior, que solo completa la orden retenida. Escríbelo de nuevo como una orden nueva si aún lo quieres.» | **APPROVE AS IS** — es el caso protegido de TD-70 (a) |
| 10 | K-16 · orden después de la respuesta (F0-12) | «También en tu respuesta: «…». La respuesta solo completa la orden retenida; esta orden se lee a continuación, como una orden propia, con su propio recibo.» | **APPROVE AS IS** — la guía del residente actualizada, sin firmar, ya explica «recibo» (I-6) y este caso (I-3); corregido el 2026-10-07, antes decía que no |

**Decisión docente (2026-10-07):** K-7 a K-16, APPROVE. K-13 y K-14, con la regla de X1-0: en un encuentro en
español, los fármacos reconocidos que ve el residente llevan su nombre en español, y el valor canónico guardado no
cambia. En K-9, la mayúscula tras «sin pulso:» es cosmética y no pide revisión. K-16 conserva la semántica de
F0-12: una orden escrita después de responder la aclaración se procesa como orden propia, con su propio destino y
su propio recibo; la guía puede explicar «recibo» al actualizarse, sin bloquear la aprobación. Registradas en el
paquete, en la hoja F0-11 y en el Decision File (duodécima actualización), sin implementar.

### 3.6 Lote final de nivel 1 (propuesto el 2026-10-07)

Orden del paquete: K-17 a K-21. **Comprobado el 2026-10-07:**

- en las cinco, el inglés y el español del paquete coinciden con la hoja F0-11;
- `language.say` convierte cada inglés exactamente en el español del paquete, y en K-20 también
  `language.examination`, el panel del examen;
- cada línea citada del código tiene esa frase.

K-18 se comprobó además en la sala real (`pilot_acceptance`), sin cambiar código.

| # | ID | Qué dice el español activo | Recomendación |
|---|---|---|---|
| 1 | K-17 · límite de 120 minutos por paso | «Indica un intervalo de reevaluación de 0 a 120 minutos. El simulador avanza el reloj como máximo 120 minutos de una vez (un límite de este piloto): escribe una espera o una reevaluación de 120 minutos o menos, y vuelve a esperar después si necesitas más tiempo.» | **APPROVE AS IS** — dice el límite y qué hacer; el mismo «como máximo» del borrador X1-C30 |
| 2 | K-18 · paro de la anafilaxia tras una dosis | «Paro circulatorio tras veinticinco minutos sin adrenalina eficaz: la adrenalina administrada antes había perdido su efecto y la reacción había vuelto. Nada más de lo administrado actúa sobre la reacción.» | **REVISE** (antes, APPROVE AS IS) — en `anaphylaxis_63m_betablocked`, con una sola dosis y espera, la reacción nunca mejora y el paro (minuto 71) dice que «había vuelto». Se propone una frase cierta en los dos cursos: «… la adrenalina administrada antes no logró mantener la reacción bajo control. …» (paquete, K-18, con el inglés y las opciones) |
| 3 | K-19 · flujo por omisión de la mascarilla con reservorio | «Oxígeno por mascarilla con reservorio a 15 L/min: no se escribió un flujo; se usó el flujo habitual de la mascarilla con reservorio, 15 L/min.» | **APPROVE AS IS** — F0-9; la mayúscula inicial es cosmética |
| 4 | K-20 · examen de cualquier región tras el paro | «Sin respuesta, sin respiración, sin pulso central: el paciente está en paro cardíaco. La reanimación no está modelada en este piloto.» | **APPROVE AS IS** — se ve en español también en el panel del examen |
| 5 | K-21 · paro de la anafilaxia sin tratar (anterior a la Fase 0) | «Paro circulatorio tras veinticinco minutos de anafilaxia no tratada. La adrenalina era el tratamiento que faltaba; nada más de lo administrado actúa sobre la reacción.» | **APPROVE AS IS** — exacta en el motor: sin adrenalina, nada más actúa sobre la reacción (el glucagón sólo devuelve la respuesta a la adrenalina). Se decide junto a K-18, su hermana |

**Decisión docente (2026-10-07):** K-17, K-19, K-20 y K-21, APPROVE. K-18, REVISE, con la redacción propuesta: EN
«Circulatory arrest after twenty-five minutes without effective adrenaline: the adrenaline given earlier did not keep the reaction under control. Nothing else that was given acts on the reaction.» · ES «Paro circulatorio tras veinticinco minutos sin adrenalina eficaz: la adrenalina administrada antes no logró mantener la reacción bajo control. Nada más de lo administrado actúa sobre la reacción.» Motivo docente: es cierta cuando la adrenalina ayudó y después perdió su efecto, y cuando
la dosis previa nunca controló bien la reacción, también con betabloqueo. Es una corrección de texto antes del
candidato final (TD-82), sin implementar. **Con este lote, todas las decisiones de nivel 1 están tomadas.** H-62 e
I-63 siguen sin firma a propósito, hasta el candidato final implementado: no es un rechazo y no reabre el nivel 1.

### 3.7 Primer lote de nivel 2 (propuesto el 2026-10-07)

Orden del paquete: A-3 a A-8 y A-10 a A-13; A-9 es de nivel 1, ya decidida. Son frases del motor (R-4): el examen
respiratorio y la vía de la hipoglicemia. **Comprobado el 2026-10-07:**

- el inglés y el español coinciden con el motor (`family_engine.py:3222–3247`, `glucose_rescue.py:202–220`), los
  borradores (`spanish_drafts.ENGINE`) y la hoja R-4;
- en un encuentro en español, el panel del examen las muestra hoy en inglés (`language.examination`). Con X-1
  decidida, se verán en español al implementarla. El registro las guarda en inglés;
- cuándo aparece cada una, con el motor y sin cambiar código: asma y opioides con y sin tratamiento; edema
  pulmonar, por su prueba (`test_td47_and_r4_engine_findings.py`).

Dónde se ven: en el panel del examen, región «Respiratory» (A-3 a A-11) o «Vascular access» (A-12 y A-13).
Ninguna es idéntica a otra, así que no se agrupan. A-5, A-6 y A-8 se marcan VINCULADAS: A-8 repite A-5 o A-6.

| # | ID · casos | EN exacto | ES exacto | Qué significa | Recomendación |
|---|---|---|---|---|---|
| 1 | A-3 · 58m, 75f | Bilateral crackles remain, with reduced respiratory effort. | Persisten crépitos bilaterales, con menor esfuerzo respiratorio. | La congestión mejora con el tratamiento: el menor esfuerzo es mejoría. Una prueba fija que nunca aparece sin tratamiento ni junto al agotamiento | **APPROVE AS IS** — distinta de la frase de esfuerzo aumentado y de A-2 revisada (agotamiento) |
| 2 | A-4 · todas las familias salvo asma, edema pulmonar y opioides | New bibasal inspiratory crackles since the transfusion, with increased effort and no wheeze. | Crépitos inspiratorios bibasales nuevos desde la transfusión, con aumento del esfuerzo y sin sibilancias. | Sobrecarga circulatoria por una transfusión innecesaria (hemoglobina de 10 g/dL o más, sin hemorragia activa que reponer), no broncoespasmo | **APPROVE AS IS** — con la precisión de dónde aparece |
| 3 | A-5 · 24f, 49m | Improved air entry with residual expiratory wheeze. | Mejor entrada de aire, con sibilancias espiratorias residuales. | Responde a los broncodilatadores; queda una obstrucción leve. Aparece con broncodilatadores (minuto 6), nunca con oxígeno solo | **APPROVE AS IS** — VINCULADA con A-8 |
| 4 | A-6 · 24f, 49m | Reduced bilateral air entry with prolonged expiration and wheeze. | Entrada de aire disminuida en ambos lados, con espiración prolongada y sibilancias. | Obstrucción grave, sin respuesta | **REVIEW CLOSELY** — en la 49m reemplaza, desde la primera orden y sin cambio fisiológico, un tórax casi silente («very poor bilateral air entry and only faint wheeze»). Opciones: aprobar tal cual, o que el motor conserve el examen de llegada mientras la obstrucción siga igual (TD-83) |
| 5 | A-7 · 24f, 49m, intubados | Breath sounds absent over the right hemithorax, which is hyper-resonant; wheeze on the other side. | Murmullo pulmonar abolido en el hemitórax derecho, que está hipersonoro; sibilancias en el otro lado. | Neumotórax a tensión por barotrauma en ventilación mecánica (meseta sostenida sobre 30 cmH₂O): hay que descomprimir. El motor lo pone siempre a la derecha | **APPROVE AS IS** |
| 6 | A-8 · 24f, 49m | Breath sounds returning on the right after decompression; improved air entry with residual expiratory wheeze. | Reaparece el murmullo pulmonar en el hemitórax derecho tras la descompresión; mejor entrada de aire, con sibilancias espiratorias residuales. | La descompresión funcionó; queda la obstrucción. Si sigue grave, la segunda parte es A-6 | **APPROVE AS IS** — VINCULADA con A-5 y A-6 |
| 7 | A-10 · 35m, 67f | Respiratory rate {n} /min; breaths remain shallow. | Frecuencia respiratoria {n}/min; las respiraciones siguen siendo superficiales. | Hipoventilación persistente (FR bajo 10 sin ventilación asistida): faltan la naloxona o la ventilación. Es también el examen de llegada | **APPROVE AS IS** — notas cosméticas: «{n} /min» lleva un espacio que A-9 revisada no lleva; «siguen siendo» en el primer examen |
| 8 | A-11 · 35m, 67f | Respiratory rate {n} /min; spontaneous breaths have greater depth. | Frecuencia respiratoria {n}/min; las respiraciones espontáneas son más profundas. | Respuesta a la naloxona (FR de 10 o más sin ventilación asistida; minuto 3 tras la dosis IV) | **APPROVE AS IS** — la misma nota de «{n} /min» |
| 9 | A-12 · `hypoglycemia_54m_thiamine` | Peripheral cannula in the left forearm; the skin around its tip is slightly swollen and cool. | Cánula periférica en el antebrazo izquierdo; la piel alrededor del extremo del catéter está levemente aumentada de volumen y fría. | La vía de llegada puede estar infiltrada: un signo, no un veredicto | **APPROVE AS IS** |
| 10 | A-13 · `hypoglycemia_28m`, `hypoglycemia_76f` | Peripheral cannula in the left forearm; the site is clean, without swelling or tenderness. | Cánula periférica en el antebrazo izquierdo; el sitio está limpio, sin aumento de volumen ni dolor a la palpación. | La vía de llegada está en vena y limpia | **APPROVE AS IS** |

Campo de decisión de cada una, en el paquete (bloque A): ☐ APPROVE · ☐ REVISE · ☐ DEFER.

**Decisión docente (2026-10-07):** A-3, A-4, A-5, A-7, A-8, A-10, A-11, A-12 y A-13, APPROVE. A-6, REVISE: en
`asthma_49m`, el examen respiratorio conserva la gravedad de llegada mientras la obstrucción no haya mejorado; una
orden que no la mejora, tampoco el oxígeno solo, no puede hacerlo parecer menos grave; A-6 sólo cuando describe el
estado actual del motor, y A-5 para la mejoría real tras el broncodilatador. Es redacción coherente con el estado,
sin cambiar la trayectoria (TD-83; la consecuencia para implementar está en el Decision File, decimocuarta
actualización). Al implementar A-9, A-10 y A-11, la frecuencia se escribe «{n}/min»: es cosmético, no otra
decisión. Ninguna está implementada.

### 3.8 Segundo lote de nivel 2 (propuesto el 2026-10-07)

Orden del paquete: A-14 a A-18 y C-27 a C-31. **Comprobado el 2026-10-07:**

- A-14 a A-18: el inglés y el español coinciden con el motor (`glucose_rescue.access_finding`), los borradores y
  la hoja R-4. Cada variante sale entera en español en las entradas: los cuatro sitios intraóseos y las tres vías
  de la infusión. El panel del examen las muestra hoy en inglés; se verán en español con X-1.
- C-27 a C-31: el inglés coincide con el motor y el banco (`anaphylaxis_reaction.py:84–96`,
  `clinical_cases.py:1511–1515`). Su español es parte del relato de cada caso. Con el relato aprobado en memoria,
  sin escribir aprobaciones, el panel dice exactamente el español del paquete; hoy, sin aprobación, cada línea se
  ve entera en inglés.

Dónde se ven: en el panel del examen, «Vascular access» de la hipoglicemia (A-14 a A-18), «Respiratory» (C-27 a
C-29) y «General appearance» (C-30 y C-31). En C-27 a C-31 se decide el inglés; su español se aprueba con el relato
del caso (4.1 del paquete) y llega en `case_text/es/approvals.json`. Ninguna es idéntica a otra; C-31 ya es una
decisión para dos casos.

| # | ID · casos | EN exacto | ES exacto | Qué significa | Recomendación |
|---|---|---|---|---|---|
| 1 | A-14 · `hypoglycemia_54m_thiamine` | Peripheral cannula in the left forearm; the forearm around it is swollen, pale, cool and tender. | Cánula periférica en el antebrazo izquierdo; el antebrazo a su alrededor está aumentado de volumen, pálido, frío y doloroso a la palpación. | Extravasación: se pasó algo por la vía infiltrada de llegada | **APPROVE AS IS** |
| 2 | A-15 · hipoglicemia | A second peripheral cannula in the right forearm; the site is clean. | Una segunda cánula periférica en el antebrazo derecho; el sitio está limpio. | Hay una segunda vía, limpia | **APPROVE AS IS** — el motor la pone siempre en el antebrazo derecho, aunque el residente nombre otro sitio; la sala lo dice en la nota del procedimiento |
| 3 | A-16 · hipoglicemia | An intraosseous needle in place (humeral). | Una aguja intraósea instalada (humeral). | Acceso intraóseo instalado; el sitio puede ser humeral, tibial, esternal o femoral | **APPROVE AS IS** — los cuatro sitios salen en español («sternal» → «esternal») |
| 4 | A-17 · hipoglicemia | An intraosseous needle in place; no site was recorded. | Una aguja intraósea instalada; no se registró el sitio. | Acceso intraóseo sin sitio registrado | **APPROVE AS IS** |
| 5 | A-18 · hipoglicemia | Dextrose {n}% runs at {n} mL/h through the cannula in the left forearm. | El suero glucosado al {n} % pasa a {n} mL/h por la cánula del antebrazo izquierdo. | La glucosa está pasando por esa vía: un estado, no una indicación (D-6). El motor escribe siempre el 10 %; la vía puede ser la de llegada, la nueva del antebrazo derecho o la aguja intraósea | **APPROVE AS IS** |
| 6 | C-27 · `anaphylaxis_29f` | Increased effort with widespread expiratory wheeze; no stridor heard now. | Esfuerzo respiratorio aumentado, con sibilancias espiratorias difusas; ya no se escucha estridor. | La reacción bajó lo bastante para que ya no haya estridor; el broncoespasmo sigue. El examen sigue al motor, no a la SpO₂ (TD-50) | **APPROVE AS IS** (EN) |
| 7 | C-28 · `anaphylaxis_29f` intubada | Endotracheal tube in place: no stridor through the tube; widespread expiratory wheeze. | Tubo endotraqueal instalado: sin estridor a través del tubo; sibilancias espiratorias difusas. | Con el tubo no se ausculta estridor; las sibilancias dicen que la reacción sigue (TD-47). No es un modelo de vía aérea difícil | **APPROVE AS IS** (EN) |
| 8 | C-29 · `anaphylaxis_63m_betablocked` intubado | Endotracheal tube in place: no stridor through the tube; widespread wheeze. | Tubo endotraqueal instalado: sin estridor a través del tubo; sibilancias difusas. | Igual que C-28, con las sibilancias que escribió el caso | **APPROVE AS IS** (EN) — no se agrupa con C-28: no dice «expiratory» |
| 9 | C-30 · `anaphylaxis_63m_betablocked` | A sting site on the right forearm. | Sitio de picadura en el antebrazo derecho. | La puerta de entrada, que sigue a la vista durante el encuentro (TD-59) | **APPROVE AS IS** (EN) |
| 10 | C-31 · `renal_colic_34m` y `bradycardia_bb_54f` | No rash. | Sin erupción. | Una negativa que el caso escribe y que se mantiene | **APPROVE AS IS** (EN) — UNA DECISIÓN para los dos casos |

Campo de decisión de cada una, en el paquete (bloques A y C): ☐ APPROVE · ☐ REVISE · ☐ DEFER.

**Decisión docente (2026-10-07):** A-14 a A-18 y C-27 a C-31, APPROVE; C-31 es una sola decisión para sus dos
casos. Las dos formas de pedir una segunda vía que el lector no lee no cambian A-15 y quedan sólo en TD-45; el
lector congelado no se toca. A-6 sigue en REVISE: la redacción de sus estados límite y de A-8 está propuesta para
la firma en el paquete (bloque A, «A-6 y A-8 · Estados límite»). Ninguna está implementada.

### 3.9 Tercer lote de nivel 2 (propuesto el 2026-10-07)

Orden del paquete: C-32, C-33, C-35, C-36, C-38, C-EFAST y K-E1 a K-E4. **Comprobado el 2026-10-07, sin escribir
nada:**

- C-32 a C-36: el inglés coincide con el banco (`clinical_cases.py:1511–1518`). Con el relato aprobado en memoria,
  el panel dice exactamente el español del paquete; hoy cada línea se ve entera en inglés.
- C-38: el resumen de la apariencia de la 29f y la 63m («Mental status: Alert. Expression: uncomfortable. Color:
  flushed. Diaphoresis: mild.») sale entero en español: «Estado mental: Alerta. Expresión: incómoda. Color:
  enrojecimiento. Diaforesis: leve.»
- C-EFAST: el formateador único (`efast_report.format_efast`) y su español dan los títulos y rótulos del paquete.
- K-E1 a K-E4: el inglés y el español coinciden con la hoja F0-11, y la frase entera de la espera interrumpida
  (K-6) sale en español con cada evento.

| # | ID · dónde | EN exacto | ES exacto | Qué significa | Recomendación |
|---|---|---|---|---|---|
| 1 | C-32 · `bradycardia_ccb_68m`, «General appearance» | No rash or swelling. | Sin erupción ni edema. | Una negativa que el caso escribe y que se mantiene | **APPROVE AS IS** (EN) — «swelling» es «edema» aquí y «aumento de volumen» en R-4: contextos distintos |
| 2 | C-33 · `bradycardia_hyperk_63m`, «General appearance» | A dialysis fistula in the left forearm. | Una fístula de diálisis en el antebrazo izquierdo. | Paciente en diálisis: una pista de la hiperkalemia | **APPROVE AS IS** (EN) |
| 3 | C-35 · 27m antes de cualquier medida, «General appearance» | A soaked dressing over a deep right thigh wound that is bleeding. | Apósito empapado sobre una herida profunda del muslo derecho que está sangrando. | La herida sangra activamente: hay que controlarla. Se ve mientras no se aplicó nada (TD-59) | **APPROVE AS IS** (EN) |
| 4 | C-36 · 27m con una medida aplicada, «General appearance» | A deep right thigh wound. | Una herida profunda del muslo derecho. | La herida, sin el apósito empapado; el estado del sangrado lo dice C-37, ya aprobada | **APPROVE AS IS** (EN) — VINCULADA con C-37 |
| 5 | C-38 · 29f y 63m, resumen de la apariencia | Color: flushed | Color: enrojecimiento | Piel enrojecida (anafilaxia) | **APPROVE AS IS** — sustantivo, como «palidez» en el mismo resumen |
| 6 | C-EFAST · resultado del E-FAST en la sala, el Trace y los documentos | E-FAST · performed at minute {n}; RIGHT UPPER QUADRANT, LEFT UPPER QUADRANT, SUPRAPUBIC, SUBXIPHOID, LUNG; Morison's pouch (hepatorenal) y los otros diez rótulos; Not documented | E-FAST · realizado en el minuto {n}; CUADRANTE SUPERIOR DERECHO, CUADRANTE SUPERIOR IZQUIERDO, SUPRAPÚBICA, SUBXIFOIDEA, PULMÓN; Espacio de Morison (hepatorrenal) y los otros diez; No documentado | Las cinco ventanas, en doce líneas. «No documentado» quiere decir que el caso no documenta esa ventana: no es un hallazgo negativo | **APPROVE AS IS** — lista completa en el paquete (C-EFAST) |
| 7 | K-E1 · en la espera interrumpida (K-6) | complete atrioventricular block | bloqueo auriculoventricular completo | Historia natural del infarto inferior (minuto isquémico 45): el registro lo marca no prevenible en el simulador | **APPROVE AS IS** |
| 8 | K-E2 · ídem | ventricular fibrillation, pulse lost | fibrilación ventricular, sin pulso | Fibrilación de una arteria todavía cerrada (minuto isquémico 120); el registro la marca prevenible con una reperfusión a tiempo. Terminal | **APPROVE AS IS** |
| 9 | K-E3 · ídem (y K-9) | cardiac arrest, pulse lost | paro cardíaco, sin pulso | Paro por la evolución sin tratamiento (por ejemplo, la apnea por opioides sin soporte); prevenible con el tratamiento de la causa. Terminal | **APPROVE AS IS** |
| 10 | K-E4 · ídem | cardiac arrest from uncontrolled haemorrhage | paro cardíaco por hemorragia no controlada | La 27m llega al paro con la fuente abierta; prevenible controlándola. Terminal | **APPROVE AS IS** — VINCULADA con A-1 («Circulatory arrest…») y K-7 («Cardiac arrest occurred…»), ya aprobadas: dos nombres del mismo paro |

Campo de decisión de cada una, en el paquete (bloques C y K): ☐ APPROVE · ☐ REVISE · ☐ DEFER. Ninguna es idéntica a
otra.

**Decisión docente (2026-10-07):** C-32, C-33, C-35, C-36, C-38, C-EFAST y K-E1 a K-E4, APPROVE. En la misma
respuesta quedó aprobada la redacción de los estados límite de la 49m (A-6a, A-6b y A-8a, con sus condiciones de
uso), y A-7 se reabrió sólo para el estado grave de llegada de la 49m, con la variante docente A-7-49m: es coherencia
del examen con el estado, no una trayectoria clínica nueva (paquete, bloque A; TD-83). Ninguna está implementada.

### 3.10 Cuarto lote de nivel 2 (propuesto el 2026-10-07)

Orden del paquete: K-E5 a K-E14; después quedan K-E15 a K-E17. **Comprobado el 2026-10-07, sin escribir nada:**

- el inglés coincide con las etiquetas del motor (`event_provenance.FLAG_EVENTS`) y con la hoja F0-11, y el
  español, con la hoja;
- la frase entera de la espera interrumpida (K-6) sale en español con cada evento, sin mezcla;
- dónde aparece cada evento, en el código que lo dispara; y, para K-E5, en la sala real con `pilot_acceptance`.

Todos aparecen dentro de la frase de K-6, cuando el evento corta una espera; el registro guarda además su
procedencia (causa, prevenibilidad, gravedad). Ninguno es idéntico a otro.

| # | ID · dónde | EN exacto | ES exacto | Qué significa | Recomendación |
|---|---|---|---|---|---|
| 1 | K-E5 · anafilaxia (29f y 63m) | circulatory arrest from untreated anaphylaxis | paro circulatorio por anafilaxia no tratada | Paro tras 25 minutos sin adrenalina eficaz; el registro lo marca prevenible con adrenalina. Terminal | **NEEDS REVISION** — la etiqueta es la misma se haya dado adrenalina o no. Con una dosis IM, la espera se corta con «untreated» en la misma entrada que K-18 («…without effective adrenaline…»): 63m, minuto 71; 29f, minuto 93. Es el defecto que llevó a revisar K-18 (TD-82). Propuesta, cierta en los dos cursos: EN «circulatory arrest from anaphylaxis without effective adrenaline» · ES «paro circulatorio por anafilaxia sin adrenalina eficaz»; o dos etiquetas según el curso. VINCULADA con K-18 y K-21 |
| 2 | K-E6 · bradicardias (54f, 68m, 63m y 78f) | loss of circulation from the falling rate | pérdida de la circulación por la frecuencia que cae | La frecuencia del monitor cae a 20/min o menos y deja de sostener un gasto; prevenible con marcapaso o antídoto. Terminal | **REVIEW CLOSELY** — calco del inglés, se entiende. Opcional, sin cambiar el sentido: «por la caída de la frecuencia» |
| 3 | K-E7 · hipoglicemia | generalized seizure | convulsión generalizada | Veinte minutos con glucosa bajo 40 mg/dL; prevenible con glucosa a tiempo. Crítico, no terminal | **APPROVE AS IS** |
| 4 | K-E8 · `anaphylaxis_29f` | the anaphylactic reaction returns | la reacción anafiláctica vuelve | Reacción bifásica, programada 75 minutos después de que la primera se calmó; el registro la marca no prevenible en el simulador. Sólo la 29f la tiene | **APPROVE AS IS** |
| 5 | K-E9 · asma (24f, 49m) con ventilación invasiva | tension pneumothorax on the ventilator | neumotórax a tensión con el ventilador | Barotrauma por una presión meseta sostenida sobre 30 cmH₂O; prevenible con una programación que la mantenga más baja. Abre el estado de A-7 (A-7-49m en la 49m grave) | **APPROVE AS IS** — «con el ventilador» se entiende; «en ventilación mecánica» sería más usual |
| 6 | K-E10 · `pulmonary_embolism_33f` | major bleeding after thrombolysis | hemorragia mayor tras la trombólisis | Sangrado desde 20 minutos después de la lisis, en la única paciente con riesgo declarado (cirugía reciente). Si la lisis estaba indicada lo juzga la docencia: prevenibilidad desconocida | **APPROVE AS IS** — VINCULADA con B-26 y D-40 |
| 7 | K-E11 · cualquier caso con dobutamina sobre 10 mcg/kg/min | frequent ventricular ectopy on dobutamine | extrasístoles ventriculares frecuentes con dobutamina | La dosis pasó el umbral de arritmia; prevenible con una dosis menor. Significativo, no terminal | **APPROVE AS IS** |
| 8 | K-E12 · TEP (33f, 61m) | right ventricle failing under fast volume | falla del ventrículo derecho con volumen rápido | Volumen dado más rápido de lo que acepta un ventrículo derecho obstruido; prevenible con volúmenes lentos y pequeños | **APPROVE AS IS** |
| 9 | K-E13 · TEP (33f, 61m) sin lisis | sustained hypotension from the obstruction | hipotensión sostenida por la obstrucción | 15 minutos seguidos con la sistólica bajo 90 mmHg, o sostenida con vasopresor: define el shock, se haya hecho lo que se haya hecho (prevenibilidad desconocida) | **APPROVE AS IS** |
| 10 | K-E14 · cualquier caso dado de alta inestable | brought back after discharge | traído de vuelta tras el alta | Vuelve 20 minutos después de la alarma (conciencia, glucosa bajo 60 mg/dL, FR bajo 10, SpO₂ bajo 90 % o sistólica bajo 90 mmHg); prevenible. Logístico | **APPROVE AS IS** — masculino genérico, como «el paciente» en toda la sala, también con pacientes mujeres |

Campo de decisión de cada una, en el paquete (bloque K): ☐ APPROVE · ☐ REVISE · ☐ DEFER.

**Decisión docente (2026-10-07):** K-E7 a K-E14, APPROVE. K-E5, REVISE: EN «circulatory arrest from anaphylaxis
without effective adrenaline» · ES «paro circulatorio por anafilaxia sin adrenalina eficaz», cierta se haya dado
adrenalina o no; K-21 sigue siendo la frase de la anafilaxia realmente no tratada (TD-82). K-E6, REVISE: EN
«circulatory arrest from profound bradycardia» · ES «paro circulatorio por bradicardia profunda», el mismo evento
terminal, sin cambiar su disparador, su prevenibilidad ni su fisiología (TD-67). En la misma respuesta, A-6 y A-6b
quedaron aclaradas: se eligen por el estado del motor, no por la intubación ni por el fármaco de inducción, y la
fisiología de la ketamina no cambia (TD-83). Ninguna está implementada.

### 3.11 Lote final de nivel 2 (propuesto el 2026-10-07)

Orden del paquete: K-E15, K-E16 y K-E17, las tres últimas de las 100 decisiones. **Comprobado el 2026-10-07, sin
escribir nada:**

- el inglés coincide con el motor (`event_provenance.Watch` para los dos cambios vigilados y
  `time_semantics.interrupted_lead` para el respaldo) y con la hoja F0-11, y el español, con la hoja;
- la frase entera de la espera interrumpida (K-6) sale en español con cada una, también con otros valores (48 mmHg,
  79 %);
- qué exige el motor para cada cambio vigilado, y si su etiqueta fue cierta: 90 recorridos de la sala (los 30
  casos, sin tratamiento, con el tratamiento definitivo y con uno dañino), con el detector envuelto en memoria y sin
  cambiar código.

Los dos cambios vigilados no nombran una causa: el motor no la sabe. El registro los guarda con la clase
`NATURAL_DISEASE`, prevenibilidad `UNKNOWN`, gravedad crítica y la nota de que el motor no dice su causa, y nunca se
usan solos en contra del residente (F0-6).

| # | ID · cuándo aparece | EN exacto | ES exacto | Qué significa y por qué | Recomendación |
|---|---|---|---|---|---|
| 1 | K-E15 · cualquier caso, con pulso: la sistólica queda bajo 70 mmHg y 20 o más por debajo del inicio de la espera durante dos minutos seguidos; una vez por espera | systolic pressure {n} mmHg and falling (en el paquete, 62) | presión sistólica de {n} mmHg y en descenso | Un colapso circulatorio que muestran los signos vitales, sin nombrar su causa. En los 90 recorridos apareció 8 veces (anafilaxia 29f y 63m, hemorragia 27m), y en las 8 la presión seguía bajando en ese minuto | **APPROVE AS IS** |
| 2 | K-E16 · cualquier caso, con pulso: la saturación queda bajo 85 % y 5 puntos o más por debajo del inicio de la espera durante dos minutos seguidos; una vez por espera | saturation {n} % and falling (en el paquete, 84) | saturación de {n} % y en descenso | Una caída de la oxigenación, sin nombrar su causa. Apareció 3 veces (edema pulmonar 58m y 75f, con suero): la lectura entera repetía la del minuto anterior, dentro de un descenso que seguía después | **APPROVE AS IS** — cosmético: el inglés escribe «84 %» con espacio y el resto de la sala en inglés, «84%»; si se unifica, cambia también la regla en español |
| 3 | K-E17 · respaldo de K-6 cuando el evento no trae nombre | a critical change | un cambio crítico | Que la frase nunca quede sin nombre. Con el código actual no aparece: todo evento que corta una espera trae su etiqueta | **APPROVE AS IS** |

Campo de decisión de cada una, en el paquete (bloque K): ☐ APPROVE · ☐ REVISE · ☐ DEFER. Con ellas se completan las
100.

**Decisión docente (2026-10-07):** K-E15, K-E16 y K-E17, APPROVE. En K-E16, la diferencia del inglés «84 %» /
«84%» es cosmética: al implementar se normaliza, sin otra decisión y sin cambiar el disparador ni el sentido del
evento. Con ellas quedan decididas las 100 del paquete (niveles 1, 2 y 3). H-62 e I-63 siguen sin firma a propósito,
hasta el candidato final implementado. B-5 no está resuelto.

### 3.12 X-1: lotes de revisión (propuesto el 2026-10-07)

La consolidación y el primer lote están en `docs/revision/X1_ESPANOL_PROPUESTO.md`, §12, junto al español que
revisan, y no se repiten aquí. Las 98 decisiones pendientes quedan en 28 decisiones consolidadas (XR-01 a XR-28), en
dos lotes de 14:

- se agrupan las que siguen una misma regla de traducción, las que llena una misma tabla de vocabulario y las que
  forman una familia coherente de la pantalla;
- las preguntas con un sentido clínico propio (vía, deglución, cardioversión) siguen siendo decisiones separadas.

El lote 1 (XR-01 a XR-14) reúne lo que se ve en cada turno del manejo activo e incluye V-9, los nombres de fármacos
en español, redactada para este lote.

**Lote 1, decidido el 2026-10-07 (docente):** 9 APPROVE y 5 REVISE (XR-01, XR-07, XR-10, XR-11 y XR-14), con el
texto final en el §12.2 de X-1 y en la fila de cada miembro. XR-05 queda con la opción b: la pregunta repite el
fármaco que el residente nombró. L-09 abre una contradicción con C-2026-09-26-25, a decisión docente. El lote 2
(XR-15 a XR-28) está en el §12.3; al prepararlo se vio que X1-C11 y X1-C30 ya tienen español activo.

**Lote 2 y L-09, decididos el 2026-10-07 (docente):** 12 APPROVE y 2 REVISE (XR-18 y XR-23), y L-09 resuelta con la
opción (c): «Fuente de la historia: {fuente}». Con eso están tomadas las 105 decisiones de X-1 (28 consolidadas: 21
APPROVE y 7 REVISE), sin implementar. La etapa siguiente, la revisión del relato y de la rúbrica en español, quedó
diseñada en `docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md`.

## 4. Verificación

- **El código no cambió:** el diff respecto de `8ff41a4`, fuera de `docs/`, está vacío. B-1 sigue valiendo
  (paquete, sección 5; S-C).
- **Las guías:** cada frase nueva se contrastó con el código o con las fuentes que cita.
  - Línea más larga: 111 caracteres, como antes.
  - Ninguna prueba lee las guías.
- **Las pruebas que leen los documentos tocados:** 42 passed, después de editarlos.
  - `test_debt_register_cites_its_corrections.py`, `test_phase0_spanish.py`, `test_phase0_pilot_freeze.py`;
  - `test_review_sheets_are_current.py`, `test_pocus_review_notes.py`,
    `test_td59_general_appearance_keeps_the_case.py`.
- **Lo que no se probó:**
  - no se abrió la app ni se tomaron capturas;
  - los escaneos de 2.4 son estáticos, sobre los literales del código: no cubren textos armados de otra forma.

## 5. Decisiones pendientes

Actualizado el 2026-10-07, con las 100 decisiones docentes del paquete, los estados límite de la 49m, el alcance y
X-1 entera, el relato, la rúbrica y las guías (Decision File, octava a vigesimoséptima actualizaciones).

1. **Decidido:** el alcance de X-1, sin interfaz mezclada en el candidato final, y sus decisiones de base (X1-0,
   I-10, L-01, V-4, M-02, L-17). X1-0 rige también los documentos que se ofrecen al residente en español.
2. **Decidido:** el español de X-1, entero (105 de 105, 2026-10-07; `docs/revision/X1_ESPANOL_PROPUESTO.md`), sin
   implementar. L-09 se resolvió con la opción (c), «Fuente de la historia: {fuente}».
3. **Decidido:** el relato en español de los 30 casos se revisa antes de congelar el candidato final, y su
   aprobación entra en el candidato en `case_text/es/approvals.json` (camino a). El archivo se crea después de la
   revisión. **La revisión quedó diseñada y aprobada el 2026-10-07** (`docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md`, §8): la unidad es el caso
   entero; T-1 a T-3 y los 18 pasajes del corpus, decididos. El archivo se genera cuando los 30 casos terminen su
   revisión. **Lote 0 aprobado el 2026-10-07** (`docs/revision/B5_RELATO_LOTE_0.md`): 47 de 47 frases comunes.
   **R1A y R1B aprobados** (`docs/revision/B5_RELATO_R1A.md` y `docs/revision/B5_RELATO_R1B.md`): el bloque de SCA entero. **R2A y R2B aprobados** (`docs/revision/B5_RELATO_R2A.md` y `docs/revision/B5_RELATO_R2B.md`): el bloque
   respiratorio entero, con P-1 en la 24f. Van 12 de 30 casos, cada uno en su versión objetivo. R3A en revisión
   (`docs/revision/B5_RELATO_R3A.md`).
4. **Decidido:** las 100 decisiones del paquete (3.11). Siguen sin firma, a propósito, H-62 e I-63, hasta el
   candidato final implementado.
5. **Decidido:** las dos guías difieren su firma hasta que describan el candidato final (3.4).
6. **Decidido:** la rúbrica en español se revisa antes de congelar el candidato final. **Falta identificar**, antes
   de implementarla, el mecanismo exacto con que se activa en el candidato, comprobable de forma determinista. El
   diseño aprobado el 2026-10-07 sigue el mismo principio que el relato: una aprobación por dominio, con
   `{domain_id, version, decision}`, que el código ya lee (`rubric_text/es/approvals.json`), y R-1 («revisar» para
   «check»). Antes de congelar el candidato, se identifica y se prueba el camino de activación que ya usa la app.
   **Rúbrica decidida el 2026-10-07 (`docs/revision/B5_RUBRICA_RUB.md`): 5 de 5**, con R-1 en D4 y la opción (b) en D5; sin aprobaciones
   creadas todavía.
7. **Decidido:** K-18, REVISE con la redacción docente; es una corrección de texto antes del candidato final
   (3.6; TD-82). También K-E5 y K-E6, REVISE con la redacción docente (3.10; TD-82 y TD-67).
8. **Decidido:** A-6, REVISE. En la 49m, el examen respiratorio conserva la gravedad de llegada mientras la
   obstrucción no mejore (TD-83). Al implementarlo hay que resolver, con aprobación docente de cualquier texto
   nuevo, el examen de la 49m intubada sin mejoría y la segunda parte de A-8. **Redacción aprobada el 2026-10-07**
   (paquete, bloque A): A-6a, A-6b y A-8a, con sus condiciones de uso, y A-7 reabierta sólo para el estado grave de
   llegada de la 49m, con la variante A-7-49m. A-6 y A-6b se eligen por el estado del motor, no por el fármaco de
   inducción (aclaración docente). Falta implementarlo (TD-83).
