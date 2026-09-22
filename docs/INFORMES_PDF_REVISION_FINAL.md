# Corrección final de los tres informes — qué se resolvió y qué queda

> Sobre la revisión anterior, conservando todo lo ya implementado.
> **Cero llamadas nuevas al proveedor**: los tres documentos se rehacen desde el encuentro y las
> respuestas guardadas, con las conexiones salientes bloqueadas en el guion que los genera.
> Revisé **las 19 páginas una por una en imagen**, no sólo en texto.

---

## 1. Paginación

| Documento | Antes | Ahora |
|---|---|---|
| Management Trace | 9 páginas, una decisión partida en cada corte sin identificación | **8 páginas**, ninguna vacía |
| Faculty compacto | 3 páginas, la tercera con sólo el pie | **2 páginas**, con todas las justificaciones completas |
| Faculty completo | 9 páginas, la 3 vacía y las 5 y 7 con colas sueltas | **9 páginas**, ninguna vacía ni con contenido huérfano |

**Faculty completo.** La regla de "dos objetivos por página" forzaba un salto que, con el texto
más grande, dejaba una página en blanco y mandaba la cola de un objetivo sola a la siguiente.
Ahora **cada objetivo es un bloque indivisible** y fluye; el registro de generación cierra el
documento en vez de quedar suelto tras la primera página. Cada decisión citada viaja también
como un bloque.

**Faculty compacto.** Volvió a dos páginas sin tocar el cuerpo de 11 puntos y sin recortar
ninguna justificación: moví los metadatos al completo, fundí el pie repetido con la leyenda,
dejé el alcance en una línea que remite al completo, y subí el contexto de asistencia a la
primera página, donde se lee junto a la síntesis. La página 1 es lo que se lee y se hace; la
página 2 es la tabla de sugerencias entera.

**Management Trace.** La tabla de gráficos se partió en filas para que no saltara entera y
dejara dos tercios de página en blanco; desapareció el salto forzado antes de las decisiones;
cada afirmación de "qué llevarse" viaja completa. Y cuando una decisión ocupa dos páginas, la
segunda se encabeza con **`DECISIÓN N · CONTINUED`**, bajo la cabecera. Los cortes caen siempre
entre secciones numeradas, nunca dentro de una frase.

## 2. Texto incompleto

**Revisé la respuesta cruda guardada: también está cortada.** `trace_raw_output.json` tiene la
síntesis y la trayectoria en exactamente 600 caracteres y el título en exactamente 90, que son
los topes del esquema. No hay nada que recuperar y no inventé la continuación.

Lo que hace ahora el informe:

- Marca dónde se detuvo: `[…interrupted: the analysis reached its length limit]`.
- Abre un bloque propio, **THE INTERPRETATION ABOVE IS INCOMPLETE**, que dice que lo que sigue
  no es interpretación.
- Y muestra un **resumen factual derivado del registro**: *"5 recorded decisions between 0 and
  60 min. Heart rate 118 → 105 /min; Systolic pressure 88 → 112 mmHg; Oxygen saturation 90 → 96 %;
  Respiratory rate 28 /min unchanged; Capillary refill 3 → 2 s."*

Todos los mensajes de interfaz quedaron en inglés, el idioma de los informes.

## 3. Fidelidad al registro

Revisé el registro decisión por decisión y encontré más de lo que estaba señalado:

| Lo que dice el registro | Lo que decían los informes |
|---|---|
| Un solo lactato: 3,2 mmol/L a los 20 min. No hay segundo valor | *"lactate remained elevated"* |
| En D1 el residente pidió lactato **y** troponina; ambos se informaron después (20 y 45 min) | nada |
| En **D4 pidió lactato de control**; el motor lo entendió y el encuentro cerró a los 60 min sin resultado | *"no repeat lactate recorded"*, como omisión suya |
| La sonda se instaló en ese mismo intervalo y el motor registró que aún no producía orina | *"no urine output"* |
| La vía venosa estaba **ya instalada y no se repitió** | *"Peripheral IV access (started)"* |

Ahora, en el Management Trace, el bloque *"qué quedó registrado después"* distingue las cuatro
situaciones con el hecho y su hora, sin inferir motivo:

> lactate: requested here; the result was reported at 20 min, under decision 2
> troponin: requested here; the result was reported at 45 min, under decision 3
> lactate: requested; no result was recorded before the encounter closed at 60 min

Y la vía venosa se lee como la escribió el motor: *"Peripheral intravenous access already in
place; not repeated"*.

**Las correcciones al texto del modelo están registradas aparte**, en
`local-data/demo_2026-09-22/analysis_corrections.json`: ocho correcciones, cada una con el
fragmento original exacto, su reemplazo y la razón, más los cuatro hechos del registro en que se
apoyan. Los análisis guardados y las respuestas crudas **no se modificaron**. La sustitución es
por texto exacto, nunca por patrón, así que una corrección se aplica al pasaje para el que fue
escrita o no se aplica; y cada documento informa al pie cuántas aplicó y por qué. Las tres
correcciones de lactato, monitorización y vía venosa se aplican en los tres documentos.

## 4. Autoría e interpretación

- *"YOUR LATER REFLECTION — WRITTEN AFTER THE ENCOUNTER"* → **"AI SUMMARY OF YOUR LATER
  REFLECTION"**, con la línea *"Written by the model from what you wrote after the encounter"*.
- **"Written by you"** quedó sólo donde el texto es literalmente del residente: el plan de
  adaptación.
- **"6 · POINT TO REVISIT"** → **"6 · NEXT MANAGEMENT ADJUSTMENT"**. El campo del modelo describe
  el cambio siguiente, no plantea una pregunta. La etiqueta de pregunta sólo vuelve si el texto
  efectivamente termina en una; en este encuentro ninguno lo hace.

## 5. Evaluación justa

Las tres observaciones que señalaste están corregidas en el texto y, sobre todo, acompañadas del
hecho que permite juzgarlas:

- **Diuresis y lactato**: la orden existió y el encuentro terminó. El informe lo dice con la hora
  y añade explícitamente que *el registro no distingue una falta de ejecución del fin del
  encuentro*.
- **Los 15 minutos iniciales**: eran el intervalo de reevaluación que el propio residente eligió,
  y el encuentro no ofrece granularidad menor para el soporte. La justificación de TD1 y la
  primera prioridad de revisión lo dicen ahora, y piden verificarlo con él en vez de afirmarlo.
- **Trabajo respiratorio**: la frecuencia respiratoria no se movió en las cuatro horas, y el
  gráfico lo rotula **"no recorded change"**.

**No cambié ninguna recomendación.** La sugerencia de TD1 sigue siendo *needs improvement*: es un
juicio clínico y es tuyo. Lo que cambió es que ahora se lee junto al hecho que la sostiene o la
debilita, y los tres documentos repiten que toda sugerencia es provisional hasta tu revisión.
"No evaluado en este encuentro" se mantiene para C4.

## 6. Gráficos

- **Llene capilar incorporado** con sus valores registrados: 3 → 4 → 4 → 2 → 2 s.
- **Leyenda "WHAT EACH MARK WAS"**, que liga D1–D5 con sus acciones principales
  (*"D3 · 35 min — Dobutamine 5 mcg/kg/min (started); Troponin requested · result at 45 min"*).
- El pie mantiene la distinción: las marcas muestran **cuándo** actuaste, y **un cambio después de
  una marca no establece que la acción lo haya causado**.

---

## Limitaciones que quedan

1. **La síntesis y la trayectoria siguen cortadas.** El original guardado también lo está. Sólo
   se resuelve regenerando el análisis con el límite nuevo de 900 caracteres, ya escrito en el
   código. Costo estimado: **≈ US$ 0,07** esa llamada, **US$ 0,15** las dos, **US$ 0,25–0,45** con
   los reintentos que `gpt-5` necesita en la práctica. Tokens medidos; dinero estimado a
   US$ 1,25/M entrada y US$ 10/M salida. **No la ejecuté.**
2. **Las correcciones son de este encuentro.** Están escritas contra fragmentos exactos de este
   análisis. Para otros encuentros la solución de fondo es el prompt corregido, que sólo empieza
   a regir en generaciones nuevas.
3. **El Faculty completo tiene páginas con espacio en blanco** al final de algunos objetivos.
   Es el precio de que ningún objetivo se parta; preferí eso a partirlos o a achicar la letra.
4. **La última página del Management Trace es corta**: lleva el último campo del plan y los
   metadatos. No queda metadato aislado, pero la página no se llena.
5. **La recomendación de TD1 no fue tocada**, según lo dicho arriba.

Nada está desplegado. El PR #1 sigue sin fusionar y espero tu aprobación de esta versión.
