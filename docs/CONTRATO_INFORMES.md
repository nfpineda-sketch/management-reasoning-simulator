# Contrato de los cuatro informes

> Versión de referencia, cerrada el 2026-09-23. Vale para **cualquier** encuentro, del banco o
> generado por IA. No depende de correcciones manuales, identificadores ni frases de ningún caso.
>
> A partir de aquí los informes se modifican sólo por defectos de fidelidad, funcionamiento o
> legibilidad, o por una petición explícita del docente.

## Los cuatro documentos

| Documento | Para quién | Regla de extensión |
|---|---|---|
| **Management Trace** | El residente | Tantas páginas como decisiones y evidencia haya |
| **Faculty Brief compacto** | El docente, en la mesa | La página de lectura y la de sugerencias; dos páginas salvo que la evidencia pida más |
| **Faculty Brief completo** | El docente, para verificar | Tantas páginas como objetivos y texto haya |
| **Evaluación por rúbrica** | El docente, hasta que la complete | Tantas páginas como evidencia sostenga el puntaje |

Los cuatro salen de **una misma representación del encuentro**: el registro congelado
(`payload` / `record.payload.session`). Los tres primeros añaden el análisis guardado del brief;
el cuarto añade la propuesta de rúbrica y la decisión del docente, que viven en sus propias
tablas. La app usa los mismos renderizadores y el mismo almacén de correcciones, así que la
descarga desde la aplicación y el archivo revisado aquí son el mismo documento.

**El compacto no se extrae del completo.** Los dos leen el mismo análisis guardado: el compacto
selecciona y el completo conserva todo. Por eso no pueden divergir — no hay un original y una
copia, hay una fuente y dos lecturas. La misma regla vale para la rúbrica: la app, los dos
briefs y el informe de rúbrica leen `rubric_presentation.summary`, y ninguno recalcula un total.

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

**Primera página**: síntesis · contexto de asistencia · prioridades de revisión · preguntas de
debriefing. **Después**: tabla de sugerencias por objetivo · alcance · llamado a la acción ·
pie con procedencia breve.

**El compacto dirige la atención.** Un objetivo sugerido como satisfactorio y que el registro
resuelve ocupa **una línea** —identificador, título, sugerencia, profundidad y anclas de
evidencia— y su justificación se lee en el completo y en la app. Todo lo que necesita una
decisión del docente conserva su **fila completa** con la justificación: lo retenido, lo que
sugiere mejorar y lo no evaluable.

Ningún objetivo desaparece del compacto. Dos páginas es lo habitual; antes que recortar una
justificación o achicar la letra, el compacto crece.

Las sugerencias van **después** de la evidencia y las preocupaciones, nunca antes.

### Faculty Brief completo

Síntesis · fortalezas · puntos de revisión · límites · decisiones citadas · un bloque por
objetivo · registro de generación al final. Cada objetivo y cada decisión citada viajan enteros.

### Evaluación por rúbrica

**Cuarto documento, agregado el 2026-09-23 a petición del docente.** Su tema es un número, y es
el único que lo tiene.

**Primero el puntaje**, grande: el total ajustado sobre 15, con la base y la penalización a su
lado, y el gráfico de araña de los cinco dominios junto a él. Cuando la evaluación es parcial no
hay número: hay una frase que dice cuántos dominios fueron evaluables y por qué un subtotal no
es comparable con un episodio completo.

**Después, un dominio por fila**: el puntaje, el fundamento y **las palabras del residente**
tomadas del Management Trace que lo sostienen, con su minuto. Si el docente cambió el puntaje
propuesto, la fila dice de cuál lo cambió y por qué. Si un dominio no es evaluable, la fila
lleva el motivo en lugar de un puntaje.

**Al final**: los eventos críticos confirmados con su doble peso declarado, los propuestos que
el docente aún no decidió —que no cuestan nada hasta que decida—, las preocupaciones que ningún
evento cubre y que no deducen, la trazabilidad y el aviso de instrumento piloto.

**Quién lo recibe.** Es del docente mientras no lo haya completado. El documento se niega a
renderizarse para el residente si la revisión es un borrador o no existe, y esa negativa vive en
el renderizador y no en quien lo llama, porque un documento se copia y un punto de llamada no.
Confirmado, el encuentro entra en el perfil del residente.

**El gráfico de araña.** Cinco ejes, uno por dominio, de 0 a 3. Dos reglas, que son las de la
rúbrica:

- Un dominio **no evaluable se dibuja como un hueco**, nunca en el centro. Un punto en el centro
  se lee como un cero, y "no evaluable" no es un cero. El contorno se abre en el hueco y se
  dibuja **sin relleno**, porque un relleno abierto lo cierra el renderizador y esa línea cruza
  justamente el eje que el hueco existe para dejar vacío. El eje se rotula en gris y la pantalla
  además lo dice con palabras.
- **La penalización no se resta de ningún eje.** Un evento de seguridad es un evento, no una
  fracción de uno; va en el titular al lado del gráfico.

El perfil longitudinal usa el mismo gráfico con un segundo contorno: el promedio del residente.
**Cada dominio promedia sólo los encuentros en que fue evaluable**, lleva su propio conteo, y el
pie lo dice cuando los conteos no coinciden. Un borrador no entra; un encuentro sin evaluar está
ausente, no en cero.

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

- Cuerpo de 11 puntos en los cuatro. Etiquetas de sección en versalitas azules.
- Referencias breves y legibles (*"D2 at 15 min"*, *"study result at 20 min"*), sin
  identificadores de máquina en el texto de lectura.
- Ninguna página vacía; ninguna sección aislada; ninguna frase partida entre páginas.
- Una decisión que ocupa dos páginas se parte **entre secciones numeradas**, y la página que
  sólo la continúa se encabeza `DECISION N · CONTINUED`. Una página donde empieza otra decisión
  no lleva ese encabezado.
- **No se fuerza un número de páginas** recortando información relevante ni achicando la letra,
  en ninguno de los cuatro. El compacto resume, pero no cambia el significado ni pierde una
  justificación para caber.

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
`unresponsive_to_support` · `unsettled` · `unsettled_by_evidence` · `hold_for_review`

`unsettled` lee las palabras de una afirmación; `unsettled_by_evidence` lee **las referencias de
evidencia que cita**, así que no depende de cómo esté redactada. Dos reglas estructurales: una
sugerencia cuya única ancla es la primera decisión —cuyo intervalo es el primero del encuentro— y
una que se apoya en una decisión que pidió algo que el registro nunca respondió. Se suman al
criterio textual y sólo actúan sobre sugerencias negativas.

## Verificaciones de regresión

En `test_report_regressions.py`, una por defecto encontrado: orden omitida, orden duplicada por
un resultado tardío, tiempos cruzados, ausencia confundida con cero, recomendación sin
fundamento suficiente, encabezado de continuación equivocado, texto cortado presentado como
terminado, y desbordamiento o vaciado de página con texto extenso.

En `test_report_contract.py`, la estructura sobre encuentros distintos: uno largo y uno corto, con
análisis completo e incompleto, y el almacén de correcciones compartido leído por los tres
primeros documentos sin que nadie se lo pase.

El cuarto tiene los suyos en `test_rubric_document.py` (quién puede leerlo, qué número imprime,
qué evidencia lleva), `test_rubric_radar.py` (el hueco que no es un cero) y
`test_rubric_progress.py` (lo que un perfil se niega a contar).
