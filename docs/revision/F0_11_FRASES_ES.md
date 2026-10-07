# F0-11 · Las frases nuevas de la Fase 0 en español

**Hoja para la firma docente.** Cierre de la Fase 0 (2026-10-06), decisión F0-11: el piloto corre también en
español (la persona residente elige «Idioma · Language» y el idioma queda fijo durante el encuentro), así que
cada frase que la Fase 0 agregó a la sala se dice en español antes del despliegue. La autorización del
2026-10-06 activa estas frases; **no es su firma**: como en D-5 y R-4, la redacción final queda para la firma
docente. Corregir una frase es cambiar su regla en `language.py` (`_PHASE0_RULES`) y su prueba en
`test_phase0_spanish.py`.

Reglas de la traducción:

- Cada frase se dice entera, antes de las reglas de palabras: nunca una línea en dos idiomas.
- Las palabras de la persona residente citadas en una frase quedan como las escribió, entre «»: no se traducen.
- Los nombres de los fármacos, las unidades y las abreviaturas son iguales en ambos idiomas (convención de la
  sala); las etiquetas de órdenes que compone el motor siguen como antes.
  **Decisión docente del 2026-10-07 (X1-0, aclaración), sin implementar:** en un encuentro en español, los
  fármacos que el motor inserta en un texto que ve el residente se mostrarán con su nombre en español; el
  identificador canónico guardado no cambia. Hoy, las frases de abajo todavía los muestran en inglés. Las filas 5,
  6, 13 y 14 se aprobaron con esta regla (lotes 4 y 5 del paquete de firmas).
- Los códigos internos (destinos del ledger como UNRECOGNIZED o RECORDED_NOT_MODELLED, nombres de campos) no se
  traducen ni se muestran a la persona residente.
- El registro guarda la frase en inglés, como todo el registro; la sala la dice en el idioma del encuentro.

## Frases de la sala

Los ejemplos salen del código que las compone, con valores de muestra; las palabras entre «» son las de la
persona residente.

| # | Qué dice | Inglés (lo que guarda el registro) | Español (lo que ve la sala) |
|---|---|---|---|
| 1 | Orden no entendida (UNRECOGNIZED) | Not understood: "Zyvox IV". Nothing was given or done for it. Write it again in other words if you still want it. | No se entendió: «Zyvox IV». No se administró ni se hizo nada por ello. Escríbelo de nuevo con otras palabras si aún lo quieres. |
| 2 | La misma, con las palabras de la persona residente intactas | Not understood: "Stop the infusion". Nothing was given or done for it. Write it again in other words if you still want it. | No se entendió: «Stop the infusion». No se administró ni se hizo nada por ello. Escríbelo de nuevo con otras palabras si aún lo quieres. |
| 3 | Registrada, no administrada (RECORDED_NOT_MODELLED) | Recorded as your decision, not given: "Stop the infusion". This simulator does not model a response to it in this case, so nothing changed. | Registrado como tu decisión, no administrado: «Stop the infusion». Este simulador no modela una respuesta a ello en este caso, así que nada cambió. |
| 4 | Reevaluación inmediata (mirada en la cabecera) | On reassessment at the bedside, 2 minutes later, BP 100/60 mmHg. | Al reevaluar en la cabecera, 2 minutos después, PA 100/60 mmHg. |
| 5 | Mirada inmediata después de una orden | Normal saline 1000 mL. On reassessment at the bedside 1 minute after the order, BP 100/60 mmHg. | Suero fisiológico 1000 mL. Al reevaluar en la cabecera, 1 minuto después de la orden, PA 100/60 mmHg. |
| 6 | Espera interrumpida por un evento | Given: Normal saline 1000 mL. The wait was interrupted after 7 minutes of the 15 you asked for, at minute 7: systolic pressure 62 mmHg and falling. Now, BP 62/30 mmHg. | Administrado: Suero fisiológico 1000 mL. La espera se interrumpió tras 7 min de los 15 que pediste, en el minuto 7: presión sistólica de 62 mmHg y en descenso. Ahora, PA 62/30 mmHg. |
| 7 | Paro: mensaje acordado | Cardiac arrest occurred at minute 12. Resuscitation management is not modelled in this pilot. Subsequent management is not assessable. | Se produjo un paro cardíaco en el minuto 12. El manejo de la reanimación no está modelado en este piloto. El manejo posterior no es evaluable. |
| 8 | Orden escrita después del paro | Not executed: "Give 1 L LR". The patient is in cardiac arrest; resuscitation management is not modelled in this pilot. | No se ejecutó: «Give 1 L LR». El paciente está en paro cardíaco; el manejo de la reanimación no está modelado en este piloto. |
| 9 | Actualización sin pulso | The wait was interrupted after 3 minutes, at minute 3: cardiac arrest, pulse lost. Now, No pulse: Ventricular fibrillation on the monitor; no blood pressure; not breathing; unresponsive. | La espera se interrumpió tras 3 min, en el minuto 3: paro cardíaco, sin pulso. Ahora, sin pulso: Fibrilación ventricular en el monitor; sin presión arterial; sin respiración; sin respuesta. |
| 10 | Orden para más tarde, no programada | Not done now: "Give aspirin 300 mg in 30 minutes". An order for a later time is not carried out in this pilot: nothing was given and nothing was scheduled. Write it again when you want it done. | No se hizo ahora: «Give aspirin 300 mg in 30 minutes». En este piloto, una orden para más tarde no se ejecuta: no se administró nada ni se programó nada. Escríbela de nuevo cuando quieras que se haga. |
| 11 | Envío interrumpido (nada aplicado) | Your order "Give the normal saline" was interrupted while it was being processed, and nothing of it was applied. Nothing will be repeated automatically: check the patient's state, and send it again if it is still needed. | Tu orden «Give the normal saline» se interrumpió mientras se procesaba, y no se aplicó nada de ella. Nada se repetirá automáticamente: revisa el estado del paciente y envíala de nuevo si todavía es necesaria. |
| 12 | Envío interrumpido (quizá aplicado en parte) | Your order "Give 1 L LR" was interrupted while it was being processed, and part of it may have been applied. Nothing will be repeated automatically: check the patient's state, and send it again if it is still needed. | Tu orden «Give 1 L LR» se interrumpió mientras se procesaba, y es posible que una parte de ella se haya aplicado. Nada se repetirá automáticamente: revisa el estado del paciente y envíala de nuevo si todavía es necesaria. |
| 13 | Paquete parcial: parte no ejecutada | **PART OF THIS ORDER WAS NOT CARRIED OUT** /  / Executed now: **aspirin 300 mg PO**. / Not carried out: **norepinephrine**. Nothing of it has been given; write it again as a new order if you still want it. | **PARTE DE ESTA ORDEN NO SE EJECUTÓ** /  / Ejecutado ahora: **aspirin 300 mg PO**. / No ejecutado: **norepinephrine**. No se ha administrado nada de ello; escríbelo de nuevo como una orden nueva si aún lo quieres. |
| 14 | Paquete parcial: parte retenida | **PART OF THIS ORDER IS HELD — CLARIFICATION REQUIRED** /  / Executed now: **aspirin 300 mg PO**. / Held until you answer: **normal saline**. Nothing of it has been given. | **PARTE DE ESTA ORDEN ESTÁ RETENIDA — SE NECESITA UNA ACLARACIÓN** /  / Ejecutado ahora: **aspirin 300 mg PO**. / Retenido hasta que respondas: **suero fisiológico**. No se ha administrado nada de ello. |
| 15 | Orden junto a la respuesta, cuando algo sigue retenido | Not run: "ceftriaxone 2 g IV" was written in the answer to the question above, which completes the held order only. Write it again as a new order if you still want it. | No se ejecutó: «ceftriaxone 2 g IV» se escribió en la respuesta a la pregunta anterior, que solo completa la orden retenida. Escríbelo de nuevo como una orden nueva si aún lo quieres. |
| 16 | Orden después de la respuesta, leída a continuación (F0-12) | Also in your answer: "give 500 mL LR". The answer completes the held order only; this order is read next, as an order of its own, with its own receipt. | También en tu respuesta: «give 500 mL LR». La respuesta solo completa la orden retenida; esta orden se lee a continuación, como una orden propia, con su propio recibo. |
| 17 | Límite de 120 minutos por paso | Specify a reassessment interval from 0 to 120 minutes. The simulator moves the clock at most 120 minutes in one step (a limit of this pilot): write a wait or a reassessment of 120 minutes or less, and wait again afterwards if you need more time. | Indica un intervalo de reevaluación de 0 a 120 minutos. El simulador avanza el reloj como máximo 120 minutos de una vez (un límite de este piloto): escribe una espera o una reevaluación de 120 minutos o menos, y vuelve a esperar después si necesitas más tiempo. |
| 18 | Paro de la anafilaxia tras una dosis que se agotó | Circulatory arrest after twenty-five minutes without effective adrenaline: the adrenaline given earlier had worn off and the reaction had come back. Nothing else that was given acts on the reaction. | Paro circulatorio tras veinticinco minutos sin adrenalina eficaz: la adrenalina administrada antes había perdido su efecto y la reacción había vuelto. Nada más de lo administrado actúa sobre la reacción. |
| 19 | Flujo por omisión de la mascarilla con reservorio | oxygen non-rebreather mask 15 L/min: no flow was written; the standard non-rebreather flow, 15 L/min, was used. | Oxígeno por mascarilla con reservorio a 15 L/min: no se escribió un flujo; se usó el flujo habitual de la mascarilla con reservorio, 15 L/min. |

## Examen y frase hermana

| Qué dice | Inglés | Español |
|---|---|---|
| Examen de cualquier región tras el paro | Unresponsive, not breathing, no central pulse: the patient is in cardiac arrest. Resuscitation is not modelled in this pilot. | Sin respuesta, sin respiración, sin pulso central: el paciente está en paro cardíaco. La reanimación no está modelada en este piloto. |
| Paro de la anafilaxia sin tratar (frase anterior a la Fase 0, hermana de la 18) | Circulatory arrest after twenty-five minutes of untreated anaphylaxis. Adrenaline was the treatment that was missing; nothing else that was given acts on the reaction. | Paro circulatorio tras veinticinco minutos de anafilaxia no tratada. La adrenalina era el tratamiento que faltaba; nada más de lo administrado actúa sobre la reacción. |

La segunda fila es anterior a la Fase 0 y no estaba entre las 18 de R-4; se traduce con su frase hermana nueva
(fila 18 de la tabla anterior) para que el paro de la anafilaxia no se lea en dos idiomas en el mismo encuentro.

## Eventos que cortan una espera

Aparecen dentro de la frase de la espera interrumpida (fila 6).

| Inglés | Español |
|---|---|
| complete atrioventricular block | bloqueo auriculoventricular completo |
| ventricular fibrillation, pulse lost | fibrilación ventricular, sin pulso |
| cardiac arrest, pulse lost | paro cardíaco, sin pulso |
| cardiac arrest from uncontrolled haemorrhage | paro cardíaco por hemorragia no controlada |
| circulatory arrest from untreated anaphylaxis | paro circulatorio por anafilaxia no tratada |
| loss of circulation from the falling rate | pérdida de la circulación por la frecuencia que cae |
| generalized seizure | convulsión generalizada |
| the anaphylactic reaction returns | la reacción anafiláctica vuelve |
| tension pneumothorax on the ventilator | neumotórax a tensión con el ventilador |
| major bleeding after thrombolysis | hemorragia mayor tras la trombólisis |
| frequent ventricular ectopy on dobutamine | extrasístoles ventriculares frecuentes con dobutamina |
| right ventricle failing under fast volume | falla del ventrículo derecho con volumen rápido |
| sustained hypotension from the obstruction | hipotensión sostenida por la obstrucción |
| brought back after discharge | traído de vuelta tras el alta |
| systolic pressure 62 mmHg and falling | presión sistólica de 62 mmHg y en descenso |
| saturation 84 % and falling | saturación de 84 % y en descenso |
| a critical change | un cambio crítico |

## Firma

| Revisión | Resultado | Fecha | Firma |
|---|---|---|---|
| Redacción de las frases de la sala | Decidida: filas 1 a 17 y 19 y las dos de «Examen y frase hermana», aprobadas; fila 18, REVISE (redacción nueva abajo, sin implementar) | 2026-10-07 | |
| Eventos que cortan una espera | En curso: las catorce primeras filas (K-E1 a K-E14) decididas; la quinta y la sexta, REVISE (redacción nueva abajo, sin implementar), y el resto, aprobadas. Quedan las tres últimas (K-E15 a K-E17) | 2026-10-07 | |

**Decisiones docentes del 2026-10-07 (lotes 4, 5 y final del paquete de firmas), sin implementar.** Las filas 1 a
17 y 19, y las dos de «Examen y frase hermana», se aprueban como están, con dos condiciones que no cambian su
inglés:

- filas 5, 6, 13 y 14: rige X1-0 para los fármacos (regla 3, arriba);
- fila 16: se conserva la semántica de F0-12. La orden escrita después de responder se procesa como orden propia,
  con su propio destino y su propio recibo.

La fila 18 se revisa (REVISE). La tabla de arriba muestra la frase activa hasta implementarla (TD-82):

- EN: Circulatory arrest after twenty-five minutes without effective adrenaline: the adrenaline given earlier did not keep the reaction under control. Nothing else that was given acts on the reaction.
- ES: Paro circulatorio tras veinticinco minutos sin adrenalina eficaz: la adrenalina administrada antes no logró mantener la reacción bajo control. Nada más de lo administrado actúa sobre la reacción.

En la fila 9, la mayúscula tras «sin pulso:» es cosmética y no pide revisión. Cada decisión, con su nota, está en
el paquete (`docs/revision/FACULTY_SIGNOFF_PACKET_PREPILOT.md`, bloque K).

**Eventos (2026-10-07):** de «Eventos que cortan una espera», las filas 1 a 4 y 7 a 14 (K-E1 a K-E4 y K-E7 a
K-E14) quedan aprobadas como están. La quinta y la sexta se revisan (REVISE). La tabla de arriba muestra la etiqueta
activa hasta implementarlas:

- quinta (K-E5), cierta tanto si no se dio adrenalina como si se dio sin control eficaz. La anafilaxia realmente no
  tratada sigue teniendo su frase propia, la segunda de «Examen y frase hermana» (K-21) (TD-82):
  - EN: circulatory arrest from anaphylaxis without effective adrenaline
  - ES: paro circulatorio por anafilaxia sin adrenalina eficaz
- sexta (K-E6), el mismo evento terminal, sin cambiar su disparador, su prevenibilidad ni su fisiología:
  - EN: circulatory arrest from profound bradycardia
  - ES: paro circulatorio por bradicardia profunda

Quedan las tres últimas filas (K-E15 a K-E17).
