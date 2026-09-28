# Defectos conocidos en los baselines de validación

Sirve para que un resultado del piloto se lea como **falla conocida** o como
**falla nueva** (§73). No se esconde ningún defecto para mejorar una medida.

**Versión de la lista: 2** (ciclo 5, 2026-09-28).

- **La versión 1** es la del ciclo 4: KD-01 a KD-14 y KB-01, tal como están en
  el **SPANISH PILOT BASELINE** (`939978a`).
- **La versión 2 corrige KD-01** a partir del **ENGLISH VALIDATION BASELINE**.
  En el baseline español sigue presente.
- **La versión 2 registra KD-15 y KB-02**, encontrados al corregir KD-01.
- **Cada defecto dice en qué baselines está** (`present_in`). Así una sola
  lista sirve para etiquetar un resultado de cualquiera de los dos.
- **Qué baseline leyó un resultado** lo dice el reporte (`engine_baseline`,
  `known_defects_version`). El registro es `validation/BASELINES.md`.

- **El dato** está en `manifests/known_defects.json`.
- **Cómo se usa en la adjudicación.** Si un error coincide con uno de estos
  defectos, se escribe su ID en la columna `known_defect`.
- **Severidad.** Usa la escala de impacto del piloto (§60) y sirve para ordenar
  el trabajo, nunca como puntaje.

**Corregidos en el ciclo 4:**

- DF-16a: listas de órdenes;
- DF-16b: orden + repetición + condición;
- DF-16c: vía en plural y vía compartida por una lista de dosis.

**Corregido en el ciclo 5, a partir del ENGLISH VALIDATION BASELINE (`ec1c77f`):**

- KD-01: la vía escrita antes del fármaco, incluida la misma confusión dentro
  de una lista («Aspirin 300 mg, IV morphine 4 mg» daba la aspirina IV).
  - Sigue presente en el SPANISH PILOT BASELINE: un error de este tipo leído
    en ese baseline se etiqueta KD-01.

| ID | Clase (ejemplo sintético) | Severidad | Causa conocida | Por qué no se corrigió | Siguiente paso | Efecto posible en el piloto |
|---|---|---|---|---|---|---|
| KD-01 | Inglés: la vía antes del fármaco, sin verbo («IV morphine 4 mg», «Nebulized albuterol 2.5 mg»): orden no reconocida que retiene el envío | MEDIUM | una orden sin verbo debía empezar por el fármaco | **CORREGIDO** desde el ENGLISH VALIDATION BASELINE (ciclo 5, por clase); presente en el SPANISH PILOT BASELINE | etiquetar KD-01 sólo en resultados del baseline español | bajo en español |
| KD-02 | Fármaco sin verbo ni dosis («Morfina ev», «Salbutamol nbz»): no es orden; en una lista se pierde sin aviso | MEDIUM | regla deliberada: un fármaco sin verbo ni dosis puede ser narrativo | decisión de diseño, no defecto de DF-16 | medir la frecuencia; decisión docente: ¿preguntar la dosis? | posible en abreviatura de ficha |
| KD-03 | Texto escrito con una aclaración pendiente se toma como su respuesta | MEDIUM | la página lee el envío siguiente como respuesta | interacción en vivo (DF-16d) | fase 2 | ninguno en la fase 1: la herramienta cancela la orden retenida |
| KD-04 | «si» con sentido de «whether» se lee como condición («Reevaluar en 15 minutos si puede hablar frases completas») | LOW | todo «si» abre una condición | independiente (DF-16e) | marcarlo en la adjudicación; si es frecuente, arreglo de clase (propuesta ciclo 5) | puede bajar la captura de reevaluación en español |
| KD-05 | «OK to discharge…» no se lee como alta | MEDIUM | falta esa forma del verbo | independiente (DF-16f) | arreglo de clase con las altas en inglés | fase en inglés |
| KD-06 | Receta unida al alta con «con/with» se pierde («Alta con paracetamol 1 g cada 8 horas») | MEDIUM | del «con» del alta sólo se guarda lo que es indicación (DF-10) | independiente (DF-16g) | guardar la receta como receta | probable en C05 |
| KD-07 | «Con hora en policlínico» no se lee como seguimiento | LOW | «hora» no está en el vocabulario de seguimiento | independiente (DF-16h) | agregarlo cuando se toque el seguimiento | posible en C05 |
| KD-08 | Cuatro líneas del mensaje de orden retenida sin español | LOW | faltan en `language.py` | independiente (DF-16i) | agregar las traducciones | ninguno |
| KD-09 | Repetición «as needed / según necesidad» sin condición guardada («SOS/PRN» sí) | LOW | esas palabras no están entre las condiciones | es una pregunta de anotación (VC-3) | alinear con la guía de anotación | bajo |
| KD-10 | Repetición diferida de un examen, escrita sola, corre ahora («Repeat the troponin in 3 hours») | LOW | alcance limitado a propósito de DF-16b | necesita su propia revisión | revisar con la reevaluación programada | bajo |
| KD-11 | Una indicación de vigilancia queda como modelo de trabajo («Vigilar diuresis y estado mental») | MEDIUM | el respaldo del modelo toma una cláusula que no reconoce como orden | familia DF-7, no DF-16 | arreglo de clase en la familia DF-7 | aparecería como cita no fiel |
| KD-12 | Hallazgos fuera del vocabulario cerrado no son modelo («Hyperkalemia with peaked T waves», «Still wheezing, …») | LOW | vocabulario cerrado | DF-11, baja prioridad | que el piloto diga qué hallazgos importan | baja la captura de razonamiento |
| KD-13 | «since» y «por» no se leen como causa; «and I will» queda dentro de la expectativa | LOW | palabras ambiguas; el patrón de efecto no corta ahí | DF-11 | medir | bajo |
| KD-14 | La cita corrige la ortografía («rythm» → «rhythm») | LOW | normalización antes de citar; fijada por regresiones | DF-11 | decidir si la cita conserva la ortografía | cita no literal |
| KD-15 | Fluido nombrado en palabras, sin verbo («IV fluids 1 L», «Normal saline 1 L IV»): orden no reconocida que retiene el envío | MEDIUM | una orden sin verbo debe empezar por un fármaco, una cantidad o una abreviatura de fluido (SF, NS, LR); «fluids» y «normal saline» no están | encontrado al corregir KD-01 (era su ejemplo «IV fluids 1 L»), pero es otra causa, fuera de la clase autorizada | arreglo de clase de los nombres de fluido, previa decisión docente | posible en inglés; en español «SF 1000 mL» se lee |

**Conducta por diseño, no defecto:**

- **KB-01.** El oxígeno sin flujo absoluto («O2 por mascarilla para saturar
  sobre 94 %») se retiene para preguntar el flujo. El piloto medirá si los
  clínicos consideran innecesaria esa pregunta.
- **KB-02.** Un «IN» suelto antes del fármaco («IN naloxone 2 mg») no se lee
  como vía nasal. Antes de un fármaco, «in» es primero una preposición.
  - La vía nasal se lee donde el lector ya la lee: después de la dosis
    («naloxone 2 mg IN»), o escrita «intranasal».
  - La orden se retiene; nunca se da por otra vía.
