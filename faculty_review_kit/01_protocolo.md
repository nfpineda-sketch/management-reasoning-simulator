# 01 · Protocolo de la primera revisión docente

## 1 · Propósito y alcance
Obtener el **juicio de una persona docente** sobre la plausibilidad clínica y la utilidad educativa de la trayectoria de **presión** que produce la autoridad experimental de GI, en cinco escenarios cortos (uno opcional más). No valida clínicamente nada y no autoriza nada por sí misma: sus resultados alimentan una decisión docente posterior (plan 09).

## 2 · Revisor objetivo
Docente de Medicina de Urgencias o de cuidados agudos capaz de juzgar plausibilidad fisiológica y educativa. **No** está pensado para ingenieros de software: por eso las instrucciones evitan términos de implementación.

## 3 · Duración estimada
≈ **40 minutos** para el conjunto núcleo (orientación 5 + escenarios 32 + resumen 3). El sexto escenario, opcional, suma ≈ 5. Es una **estimación**, no una medición con una persona.

## 4 · Quién hace qué (frontera de decisión)
| Quién | Hace | No hace |
|---|---|---|
| **Persona docente** | Ejecuta los guiones, juzga plausibilidad clínica y educativa, escribe comentarios | No evalúa código ni interfaz |
| **Persona operadora** | Monta el entorno de **un** revisor, entrega materiales, corre el resumen técnico, resguarda los datos | No orienta el juicio, no revela el comparador, no responde por el revisor |
| **Software** | Comprueba consistencia técnica, trazas, repetición, vínculos de artefactos y completitud; tabula respuestas | No puntúa, no promedia, no clasifica como aceptable o no, no interpreta |

## 5 · Orden de la sesión
1. La persona revisora lee la **orientación** (03).
2. Ejecuta el **guion** de un escenario en la pantalla y ve la **trayectoria de la autoridad** (hoja de autoridad).
3. Responde la **primera pasada** (Q1–Q5; Q6–Q7 si hubo parada) **sin comparador**, en pantalla y en papel.
4. **Revela** el comparador heredado (y la comparación de consciencia, etiquetada) y abre la hoja del comparador.
5. Hace la **segunda pasada** (Q8, Q9, Q10 «Overall») y puede añadir o matizar comentarios (línea `AFTER REVEAL:`).
6. **Guarda** la retroalimentación (`Submit feedback`) y sale del encuentro.
7. Siguiente escenario. Al final, resumen de la sesión (08).

## 6 · Ciego (FD-FR-07): lo que ya existe en el entorno
- La pantalla muestra **primero** la trayectoria de autoridad (`Authority view (judge this first)`); el comparador heredado y la comparación de consciencia **no aparecen** hasta pulsar `Reveal the nonauthoritative comparison` (verificado en el navegador real).
- El botón de revelar **está deshabilitado** hasta que las preguntas ciegas estén respondidas.
- Al revelar, las respuestas ciegas **se fijan** (controles deshabilitados) y el registro guarda una instantánea (`blinded_answers_at_reveal`).
- **Límites declarados:** (a) la vista de autoridad aparece como lista JSON (la hoja de autoridad trae la misma tabla); (b) la pregunta `Overall.` es visible antes de revelar (la instrucción es dejarla para después); (c) en los escenarios con parada, un recuadro «Developer» menciona que existe un comparador (`legacy_counterfactual_available: true`, sin cifras); (d) el ciego protege **las cifras**, no el hecho de que existe un comparador, que la orientación explica.

## 7 · Primera pasada: qué se conserva (P3-298A)
**Se conserva, sin posibilidad de sobrescritura silenciosa:** las respuestas ciegas Q1–Q5 (y Q6–Q7) tal como estaban al revelar (instantánea en el registro); el registro es de **creación única** (un envío distinto no reemplaza al anterior: crea otro registro); se rechaza un registro cuyas respuestas ciegas difieran de la instantánea.
**No se conserva en la aplicación:** la impresión global (`Overall.`) **de primera pasada** (el campo final se guarda una sola vez, después del revelado) ni el orden temporal de varios envíos (los registros no llevan reloj, por determinismo; el resumen usa la fecha del archivo). **Mitigación:** el **formulario de papel** (06) recoge la primera pasada global antes de revelar; el comentario conserva el texto previo y la segunda pasada se añade con `AFTER REVEAL:`.

## 8 · Captura y vínculos (P3-298)
| Vínculo | Cómo queda establecido |
|---|---|
| **Revisor** | **Un almacén por revisor** (carpeta propia; el resumen lleva el código del revisor). El registro guarda el rol, no la identidad |
| **Caso y escenario** | El paquete y la retroalimentación llevan `case_id` y `scenario_id`; la retroalimentación que nombre otro caso, escenario o paquete se **rechaza** |
| **Paquete** | La retroalimentación nombra un paquete **ya almacenado** y su contenido tiene que ser el que se juzgó |
| **Artefacto** | El paquete lleva el identificador del artefacto almacenado; el resumen lo comprueba (verifica y se repite) |
| **Estado ciego/revelado** | `comparator_revealed` y la instantánea de primera pasada |
| **Sin arrastre entre casos** | Un paquete o un revelado de un encuentro anterior no sobreviven al siguiente (probado) |

## 9 · Privacidad (P3-298B)
Se usa **un código de revisor** (R1…), no el nombre. La cuenta del entorno necesita un usuario: usa uno **no identificable** (por ejemplo `revisor1`). No se recoge ningún otro dato personal. Los comentarios rechazan formas comunes de identificador (correos, números largos, fechas, nombres con título); es una **alarma, no una garantía**: pide a la persona revisora que no escriba datos de personas reales. Los casos son sintéticos.

## 10 · Cuándo detener la sesión
Si la pantalla difiere de la hoja de autoridad y no se entiende por qué; si aparece un error no descrito en las instrucciones; si la persona revisora lo pide. Se detiene el proceso (Ctrl+C), se conserva el almacén y se anota en el resumen. **No** se reintenta en el almacén del revisor: se ensaya en otro almacén (02).

## 11 · Qué no es
No es un piloto con residentes, ni producción, ni validación clínica; no reclutó residentes; no da autoridad de consciencia (la comparación de consciencia es **no autoritativa** y el campo vivo sigue siendo el heredado); un resultado favorable **no** autoriza nada: abre una decisión docente.
