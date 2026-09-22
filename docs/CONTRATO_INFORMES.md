# Contrato de los tres informes

> Versión de referencia, cerrada el 2026-09-23. Vale para **cualquier** encuentro, del banco o
> generado por IA. No depende de correcciones manuales, identificadores ni frases de ningún caso.
>
> A partir de aquí los informes se modifican sólo por defectos de fidelidad, funcionamiento o
> legibilidad, o por una petición explícita del docente.

## Los tres documentos

| Documento | Para quién | Regla de extensión |
|---|---|---|
| **Management Trace** | El residente | Tantas páginas como decisiones y evidencia haya |
| **Faculty Brief compacto** | El docente, en la mesa | Dos páginas: lo que se lee y se decide, y la tabla de sugerencias |
| **Faculty Brief completo** | El docente, para verificar | Tantas páginas como objetivos y texto haya |

Los tres salen de **una misma representación del encuentro y del análisis**: el registro
congelado (`payload` / `record.payload.session`) y el análisis guardado. La app usa los mismos
renderizadores y el mismo almacén de correcciones, así que la descarga desde la aplicación y el
archivo revisado aquí son el mismo documento.

## Secciones

### Management Trace

**Obligatorias, en este orden:**

1. Título, identificador del encuentro y aviso de que es interpretación provisional.
2. *The encounter in perspective* — síntesis.
3. *Recorded patient trajectory* — gráficos y leyenda.
4. *What to carry forward* — patrones y preguntas.
5. *Decisions worth revisiting* — cada decisión en seis bloques.
6. *Report provenance* — metadatos al final.

**Condicionales:**

- *Your later adaptation plan*: sólo si el residente escribió uno.
- *AI summary of your later reflection*: sólo si hay reflexión enlazada a esa decisión.
- *Technical record*: sólo si algún pasaje del análisis quedó cortado.
- El aviso de interpretación incompleta y el **curso registrado**: sólo si la síntesis se cortó.

**Los seis bloques de una decisión**, siempre en este orden y con estos nombres:

1. `WHAT YOU HAD OBSERVED` · 2. `HOW YOU REASONED` · 3. `WHAT YOU ORDERED`
4. `WHAT YOU EXPECTED` · 5. `WHAT WAS RECORDED NEXT` · 6. `NEXT MANAGEMENT ADJUSTMENT`

El sexto se llama `POINT TO REVISIT` únicamente cuando el texto del modelo formula una pregunta.

### Faculty Brief compacto

**Página 1**: síntesis · contexto de asistencia · prioridades de revisión · preguntas de
debriefing. **Página 2**: tabla de sugerencias por objetivo · alcance · llamado a la acción ·
pie con procedencia breve.

Las sugerencias van **después** de la evidencia y las preocupaciones, nunca antes.

### Faculty Brief completo

Síntesis · fortalezas · puntos de revisión · límites · decisiones citadas · un bloque por
objetivo · registro de generación al final. Cada objetivo y cada decisión citada viajan enteros.

## Qué se distingue siempre

| Categoría | Cómo se presenta |
|---|---|
| **Hecho registrado** | Sin atribución: vitales, tiempos, resultados, acciones ejecutadas |
| **Palabras del residente** | *"Written by you"*, y sólo ahí |
| **Interpretación de IA** | Bloques rotulados; la síntesis de una reflexión es *"AI summary of your later reflection"* |
| **Juicio docente** | Sólo el que el docente registra en la app. Ningún informe lo escribe |

Y cuatro ausencias que no son lo mismo:

- **Dato ausente** — no se informa como cero. Una diuresis sin medición se dice así.
- **Resultado pendiente** — se nombra la solicitud, su hora y el cierre del encuentro.
- **Objetivo no evaluable** — *"Not assessed in this encounter — no recorded opportunity"*.
- **Análisis incompleto** — el pasaje sale de la lectura, se conserva en el registro técnico y
  el encabezado dice *AI interpretation incomplete*.

## Solicitud, muestra y resultado

Son tres momentos. Una orden entendida en una decisión e informada en otra es **una** orden: se
lista donde se pidió y su resultado aparece donde llegó. Una segunda solicitud del mismo estudio
sí es una orden nueva. Ningún informe convierte la llegada de un resultado en una orden nueva.

## Cuando falta información o falla una sección

- Nunca se inventa contenido ni se continúa una frase cortada.
- Nunca se bloquea el informe entero: se conserva el registro factual y se señala la limitación.
- Un pasaje cortado se sustituye por el resumen factual del registro, **identificado como
  lectura del registro y no como interpretación**.
- Una sugerencia negativa cuyo fundamento el registro no puede resolver se presenta como
  **`Requires faculty review`**, con la sugerencia original de IA conservada al lado y el motivo.
  No se recalifica, no pasa a satisfactoria y no toca un juicio docente ya guardado.
- Una observación que el registro no puede resolver se acompaña de *"Ask this rather than judge
  it"* con el motivo.

## Estilo y paginación

- Cuerpo de 11 puntos en los tres. Etiquetas de sección en versalitas azules.
- Referencias breves y legibles (*"D2 at 15 min"*, *"study result at 20 min"*), sin
  identificadores de máquina en el texto de lectura.
- Ninguna página vacía; ninguna sección aislada; ninguna frase partida entre páginas.
- Una decisión que ocupa dos páginas se parte **entre secciones numeradas**, y la página que
  sólo la continúa se encabeza `DECISION N · CONTINUED`. Una página donde empieza otra decisión
  no lleva ese encabezado.
- **No se fuerza un número de páginas** recortando información relevante ni achicando la letra.
  La única extensión fija es el compacto, que resume sin cambiar el significado.

## Originales y correcciones

- Los análisis guardados y las respuestas crudas del proveedor **no se modifican nunca**.
- Las correcciones factuales viven en `MRS_ANALYSIS_CORRECTIONS/<id de encuentro>.json`, con el
  fragmento original exacto, el reemplazo y la razón. Se aplican al renderizar, en la app y en
  los PDF por igual, y cada documento informa cuántas aplicó.
- Se versionan agregando entradas, no editando las anteriores.
- Regenerar un PDF **no modifica** ninguna evaluación docente guardada.

## Controles que corren antes de mostrar un informe

En [`record_findings.py`](../record_findings.py), sobre el registro congelado:

`order_stages` · `urine_evidence` · `first_interval` · `inert_observables` ·
`unresponsive_to_support` · `unsettled` · `hold_for_review`

## Verificaciones de regresión

En `test_report_regressions.py`, una por defecto encontrado: orden omitida, orden duplicada por
un resultado tardío, tiempos cruzados, ausencia confundida con cero, recomendación sin
fundamento suficiente, encabezado de continuación equivocado, texto cortado presentado como
terminado, y desbordamiento o vaciado de página con texto extenso.

En `test_report_contract.py`, la estructura sobre encuentros distintos: uno largo y uno corto, con
análisis completo e incompleto, y el almacén de correcciones compartido leído por los tres
documentos sin que nadie se lo pase.
