# Ajustes finales de los tres informes

> Los dos pedidos juntos, sobre el diseño ya aprobado. **Cero llamadas nuevas al proveedor**:
> los tres documentos se rehacen desde el encuentro y las respuestas guardadas con las
> conexiones salientes bloqueadas. Revisé todas las páginas en imagen.
>
> **Lo importante de esta vuelta**: además de corregir este encuentro, las reglas quedaron
> implementadas como **controles generales** en [record_findings.py](../record_findings.py), que
> corren sobre cualquier encuentro antes de mostrar un informe. El cambio de prompt no era
> prueba de nada; esto sí se puede verificar.

---

## Lo que el registro respalda, verificado

| Pregunta | Lo que encontré |
|---|---|
| ¿Hay medición de volumen urinario? | **No existe ninguna.** Lo único que hay es un mensaje del motor en el minuto 55: *"Urine is collected and measured from now on; the catheter does not make any."* Es narrativa, no medición |
| ¿El trabajo respiratorio era dinámico en este motor? | **Sí.** Se movió: *Moderately increased → Increased* en D1, y quedó ahí. El descriptor que nunca se mueve es la **frecuencia respiratoria** |
| ¿Cuánto abarca el registro? | **60 minutos**, no cuatro horas. Ese error era mío, en el resumen anterior, y está corregido |
| ¿Cuándo se pidió cada estudio? | Lactato y troponina se pidieron **en D1** y se informaron a los 20 y 45 min. El lactato de control es una **segunda orden**, en D4, sin resultado |

## 1. Información útil restituida en el compacto

Las dos prioridades de revisión ahora dicen exactamente:

> **01** Support began at the first reassessment. Verify the intended sequence and how simulation time advanced.
> **03** Repeat lactate was requested at 55 minutes; the encounter ended at 60 minutes without a recorded result.

Desapareció todo *"Read this review point in full in the app"* y todo *"Review the full rationale in the app"*. El compacto sigue en **dos páginas**, con cuerpo de 11 puntos, todas las justificaciones completas y las anclas de evidencia intactas. Lo que hice para que cupiera: el contexto de asistencia pasó a una línea en la página 1 en vez de un recuadro propio, y la explicación de la retención dice el motivo sin repetir el encabezado.

## 2. TD1: retenida, no recalificada

Verifiqué si el registro permite atribuir la demora al residente: **no permite distinguirla** del avance temporal del simulador. El primer intervalo de reevaluación fue de 15 minutos y lo eligió el residente; el encuentro no ofrece granularidad menor para el soporte.

Los dos informes docentes y la app muestran ahora:

> **Requires faculty review** · AI suggested needs improvement
> Held because the first reassessment interval was 15 min, so the record cannot separate a delay in support from the interval the encounter advances in.

No se asignó ninguna calificación nueva, no se convirtió en satisfactoria, y **la sugerencia original de IA se conserva** —en el análisis guardado sin tocar y visible junto al estado retenido—. Los juicios docentes ya registrados no se modifican: esto afecta sólo a la sugerencia de IA.

La regla es general: `hold_for_review` retiene **cualquier** sugerencia negativa cuyo fundamento dependa de una limitación que el registro no resuelve, y nunca toca una favorable.

## 3. Los fragmentos truncados salieron de la lectura

Confirmado otra vez: **el original guardado también está cortado** (600 y 90 caracteres exactos). No inventé continuaciones.

- *"The encounter in perspective"* muestra ahora el **resumen factual del registro**, identificado como tal: *"What follows is read from the record, and is not an interpretation."*
- La lectura de la trayectoria cortada **no se muestra**; se avisa que quedó en el registro técnico.
- Los tres fragmentos incompletos se conservan **en el registro técnico al final**, marcados.
- El título de la decisión 1, que también venía cortado, se **deriva de las acciones registradas**.
- El encabezado dice **AI INTERPRETATION INCOMPLETE** en lugar de *Review complete*.

## 4. Diuresis: el estado exacto

No hay medición, así que el informe no dice cero. Dice lo que hay:

> The engine reported at 55 min that the catheter was producing none; no urine volume was recorded before the encounter ended at 60 min.

`urine_evidence` distingue los tres estados —**medido**, **narrado por el motor**, **ausente**— y sólo informa un valor, incluido cero, cuando existe la medición con su intervalo. Todas las frases equivalentes a *"the catheter had produced no urine"* quedaron corregidas en los tres documentos.

## 5. Solicitud, toma de muestra y disponibilidad, separadas

`order_stages` empareja cada solicitud con su propio informe. Consecuencias visibles:

- D2 y D3 **ya no aparecen pidiendo** lactato ni troponina. En su lugar: *"lactate: sampled at 0 min, reported at 20 min, requested at decision 1"*.
- La leyenda de los gráficos dejó de decir *"Troponin requested"* en D3.
- Una **segunda** solicitud del mismo estudio sí cuenta como orden nueva: el lactato de control de D4 aparece como pedido y sin resultado.

## 6. Paginación

| Documento | Páginas | Observación |
|---|---|---|
| Management Trace | **7** | Ninguna página termina a media frase; el plan de adaptación viaja entero; la última lleva el plan, la procedencia y el registro técnico |
| Faculty compacto | **2** | Sin recortes de información ni letra más chica |
| Faculty completo | **9** | Ninguna vacía; cada objetivo y cada decisión citada, completos |

Los gráficos se reparten en filas que pueden quebrar, así que ya no saltan enteros dejando media página en blanco. Una decisión que ocupa dos páginas conserva su encabezado **`DECISIÓN N · CONTINUED`**.

---

## Controles generales implementados

En [record_findings.py](../record_findings.py), con 17 pruebas propias:

- `order_stages` — solicitud, muestra y resultado como tres momentos, emparejados.
- `urine_evidence` / `urine_statement` — medido, narrado o ausente.
- `first_interval` — lo más temprano que el encuentro permite mostrar algo.
- `inert_observables` — descriptores que el registro nunca mueve.
- `unsettled` — qué limitación del registro sostiene una afirmación.
- `hold_for_review` — retiene una sugerencia negativa que se apoya en una de ellas.

Las correcciones específicas de este encuentro siguen en
`local-data/demo_2026-09-22/analysis_corrections.json`, auditables, con el fragmento original
exacto, su reemplazo, la razón y los siete hechos del registro en que se apoyan. Los análisis
guardados y las respuestas crudas no se modificaron.

## Pendientes

1. **El texto truncado sólo se recupera regenerando.** Ya no estorba la lectura, pero la
   síntesis del modelo no existe completa. Costo si lo autorizas: **≈ US$ 0,15** las dos
   llamadas, **US$ 0,25–0,45** con reintentos. No la ejecuté.
2. **`unsettled` es conservador y textual.** Detecta lo que este registro permite detectar;
   una afirmación escrita de otro modo puede escapársele. Prefiero que deje pasar algo antes
   que retener una sugerencia legítima.
3. **El Faculty completo tiene blancos** al final de algunos objetivos, por mantenerlos enteros.
4. **La leyenda de los gráficos muestra dos acciones por decisión** y resume el resto como
   "+N more".

Nada desplegado. El PR #1 sigue sin fusionar y espero tu aprobación.
