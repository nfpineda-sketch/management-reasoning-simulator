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

Actualizado el 2026-10-07, con las decisiones docentes del lote 1 y del alcance de X-1 (Decision File,
octava actualización).

1. **Decidido:** el alcance de X-1, sin interfaz mezclada en el candidato final.
2. **Redactar y firmar el español que X-1 exige y no existe:** las preguntas de aclaración (TD-79), el texto
   de la compuerta y los rótulos (TD-61). También la redacción EN y ES del examen respiratorio en agotamiento
   (A-2, TD-51).
3. **Cuándo se revisa el relato en español de los casos:** antes de congelar el candidato o antes del GO.
4. **Las firmas que quedan del paquete:** 89 de 100. El segundo lote de nivel 1 está en 3.2.
5. **La firma de las dos guías actualizadas** (bloques H e I).
