# Guía de anotación · reference standard del piloto

Versión de la hoja: `VC2-ANNOTATION-1`. La hoja la escribe
`tools_validation_corpus.py ingest`: una fila por entrada, con el texto del
médico y las columnas vacías. La plantilla en blanco está en
`annotation_template.csv`.

## Qué se anota

- **La intención clínica escrita, no su calidad (§38).** Se registra qué quiso
  hacer o decir el médico. Una orden discutible pero clara se anota tal como
  está escrita. La pregunta es «¿qué dijo?», no «¿fue buena medicina?».
- **A ciegas.** Se anota antes de correr el motor y sin ver lo que entendió. No
  abra `engine_output.json` ni `adjudication.csv` hasta terminar la hoja.
- **Una fila por entrada.** Cada párrafo del cuadro del médico es una entrada.
  No se unen ni se agregan filas, y el texto no se corrige.
- **No es una evaluación del médico (§62).** Sin puntajes, rankings ni
  comentarios sobre la calidad clínica.

Tiempo esperado: alrededor de un minuto por entrada.

## Las columnas

Los campos pedidos para la hoja (§39) caben en pocas columnas: todo lo que es
una orden o un plan va en `intended_items`, un ítem por intención.

| Campo pedido | Columna | Cómo |
|---|---|---|
| participant code, case ID, entry number, original free text | `participant`, `case`, `entry_id`, `text` | Vienen llenos. `EM01-C01-es-b1-e03` es el documento, el cuadro 1 y la entrada 3. |
| intended action(s), medication, dose, route, settings, timing | `intended_items` | `MED`, `FLUID`, `O2`, `PROC`, `MON`, con la dosis, vía, parámetros y momento tal como se escribieron. |
| study/request | `intended_items` | `STUDY` |
| information request | `intended_items` | `HX` (preguntar), `EX` (examinar) |
| reassessment | `reassessment` (S/N) | Más un ítem `REEVAL` si es una reevaluación concreta. |
| repeat instruction | `intended_items` | `REPEAT` |
| disposition | `intended_items` | `DISP` |
| follow-up | `intended_items` | `FOLLOWUP` |
| return precaution | `intended_items` | `RETURN` |
| interpretation/reasoning | `rationale` (S/N) | |
| expectation | `expectation` (S/N) | |
| contingency | `contingency` (S/N) | |
| ambiguity | `ambiguous` (S/N) y `acceptable_readings` | |
| annotator notes | `note` | |

**Otras columnas.**

- `clinically_sufficient` (S/N). Obligatoria si hay ítems. Vea «Las marcas».
- `context_dependent` (S/N).
- `annotator`: sus iniciales o su código de anotador, nunca el nombre del
  médico.
- `annotation_version`: viene llena.

## `intended_items`: cómo se escribe

Se escribe `TIPO: qué`, con los ítems separados por `;`. Los ejemplos están
escritos para esta guía; ninguno viene de un médico del piloto.

| Tipo | Qué va | Ejemplo |
|---|---|---|
| `MED` | un medicamento, con dosis, vía y momento como se escribieron | `MED: salbutamol 5 mg nebulizado ahora` |
| `FLUID` | fluidos o hemoderivados | `FLUID: SF 1000 ml ev en 30 min` |
| `O2` | oxígeno o soporte ventilatorio, con dispositivo y parámetros | `O2: mascarilla con reservorio 15 L/min` |
| `PROC` | un procedimiento o una intervención | `PROC: torniquete en el muslo derecho` |
| `MON` | monitorización | `MON: monitor cardíaco` |
| `STUDY` | un examen pedido | `STUDY: hemograma` |
| `CONSULT` | una interconsulta o una llamada | `CONSULT: cirujano de turno` |
| `DISP` | el destino | `DISP: alta` · `DISP: hospitalizar en intermedio` |
| `FOLLOWUP` | un control o seguimiento | `FOLLOWUP: control en policlínico en 48 h` |
| `RETURN` | una indicación de regreso | `RETURN: volver si fiebre` |
| `REPEAT` | repetir una orden, con intervalo, número y condición | `REPEAT: salbutamol cada 20 min x3 si persiste` |
| `REEVAL` | una reevaluación: qué y cuándo | `REEVAL: FR y saturación en 15 min` |
| `HX` | una pregunta de historia, o lo que se informa como antecedente | `HX: alergias` · `HX: recibió aspirina 300 mg (SAMU)` |
| `EX` | un examen físico | `EX: auscultación pulmonar` |
| `OTHER` | otra intención | `OTHER: …` |

**Reglas.**

- **Un ítem por intención.** «Salbutamol 5 mg + ipratropio 0,5 mg nbz» son dos
  `MED`.
- **Lo que no se escribió no se completa.** Si falta la dosis o la vía, el
  ítem queda sin ella, y eso se refleja en `clinically_sufficient`.
- **Una orden condicionada es un ítem con su condición**, y además
  `contingency: S`. Ejemplo: `MED: noradrenalina si persiste hipotensión`.
- **Una entrada sin intención clínica** («Plan:», «Continúo:») se anota `—`.

## Indicaciones de regreso, seguimiento y contingencia (VC-3)

**La indicación de regreso es parte del plan de alta.** No es, por sí misma,
una contingencia.

- **Ejemplo.** «Alta con control en 48 h y volver si presenta fiebre.»
  - `DISP: alta; FOLLOWUP: control en 48 h; RETURN: volver si fiebre`
  - `contingency: N`
- **Cuándo cuenta como contingencia.** Sólo si la frase trae además una
  condición explícita que **cambia el plan**. Ejemplo: «si al reevaluar sigue
  con dolor, lo hospitalizo» → `contingency: S`.

## Instrucciones de repetición

- **Se anotan como `REPEAT`**, con su intervalo, número y condición tal como se
  escribieron.
- **`contingency: S` sólo si la repetición depende de una condición clínica
  explícita.** «Repetir si persiste el broncoespasmo» es S. Un esquema fijo
  («cada 20 min x3») y «SOS / PRN / según necesidad» no son una condición
  explícita: N.

## Ahora, después, antes: siete ejemplos (ciclo 9)

Aclaración del 2026-09-29, **sin etiquetas ni columnas nuevas**: la hoja sigue
siendo `VC2-ANNOTATION-1`. La pregunta sigue siendo «¿qué quiso hacer o decir
el médico?». El momento se escribe en el ítem tal como está escrito, y el
motor no se mira.

| Qué escribió | Cómo se anota |
|---|---|
| **Acción ahora.** «Adrenalina 0,5 mg IM ahora» | `MED: adrenalina 0,5 mg IM ahora` |
| **Plan condicional.** «Noradrenalina si PAM < 65 tras 2 L» | `MED: noradrenalina si PAM < 65 tras 2 L` · `contingency: S` |
| **Tratamiento previo.** «Aspirina 300 mg dada por SAMU» | `HX: recibió aspirina 300 mg (SAMU)`: es un antecedente que el médico informa, no una orden suya. Si además ordena algo, ese ítem va aparte. |
| **Reevaluación.** «Reevaluar en 1 h» | `REEVAL: reevaluar en 1 h` · `reassessment: S` |
| **Destino ahora.** «Alta a domicilio» | `DISP: alta a domicilio` |
| **Destino planificado.** «Alta en 2 horas», «observar 6 h y luego alta» | `DISP: alta en 2 horas` · `DISP: alta tras observar 6 h`: el momento queda en el ítem. Con una condición («alta si sigue asintomática»), además `contingency: S`. |
| **Acción que el simulador no modela.** «Ondansetrón 4 mg ev» | `MED: ondansetrón 4 mg ev`: la intención se anota igual; que el simulador la modele o no es asunto del motor, no de la anotación. |
| **Entrada ambigua.** «Evaluar y alta» | Los ítems que se lean con certeza; `ambiguous: S` y las lecturas posibles en `acceptable_readings`. No se obliga a una sola intención. |

- **`HX` cubre la historia en ambos sentidos:** lo que el médico pregunta y lo
  que informa como antecedente, como un tratamiento recibido antes de llegar.
- **La corrección clínica no es la etiqueta.** Una orden discutible pero clara
  se anota como está escrita.

## Las marcas (S/N)

Una marca en blanco se lee como N.

- **`rationale`.** La entrada dice qué cree que está pasando o por qué hace
  algo.
- **`expectation`.** Dice qué espera que ocurra o qué quiere aclarar.
- **`reassessment`.** Dice qué va a reevaluar, cuándo o ambas cosas.
- **`contingency`.** Dice qué haría si la evolución es otra, con una condición
  explícita que cambia el plan.
- **`clinically_sufficient`.** Un colega podría cumplir las órdenes tal como
  están escritas, sin preguntar nada. Sirve para juzgar si una pregunta del
  motor era necesaria.
- **`ambiguous`.** El texto admite razonablemente más de una lectura clínica.
  Escriba las lecturas en `acceptable_readings`.
- **`context_dependent`.** La entrada necesita las anteriores para entenderse
  («repetir», «lo mismo»).

## Quién, cuándo y a ciegas (ciclo 9)

`ingest` deja junto a las hojas `annotation_provenance.json`. Quien coordina la
anotación anota ahí, por hoja, el **código** del anotador (nunca un nombre), la
fecha y si anotó sin haber visto la salida del motor (`true` / `false`); y, para
la adjudicación, el código del revisor y la fecha. El informe lo lleva en su
procedencia. Lo que no se anotó queda como no registrado, nunca como «a ciegas».

## Doble anotación (VC-2)

- **Qué hoja.** `ingest` escribe también `annotation_second.csv`: una quinta
  parte fija de las entradas de cada documento, elegida antes de que nadie las
  lea.
- **Quién.** Un segundo clínico la anota sin ver la primera anotación ni el
  motor.
- **Sin conversar antes.** Los dos anotadores no hablan de las entradas hasta
  que ambos terminan.
- **Los desacuerdos** se resuelven como indica `adjudication_guide.md`.

## Lo que no se hace

- Mirar la salida del motor antes de anotar.
- Cambiar una anotación después de ver el motor para que coincida.
- Calificar al médico o comparar médicos.
- Abrir entradas del subconjunto sellado durante el desarrollo.
