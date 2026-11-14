# 09 · Plan de análisis posterior a la revisión (SÓLO DISEÑO; no se ejecuta aquí)

**Principio.** Los juicios son docentes y siguen siendo docentes. El análisis **resume y muestra**; no puntúa. No se convierte ninguna respuesta en un puntaje numérico, ranking o promedio, salvo decisión docente posterior expresa.

## 1 · Insumos
Por revisor: el resumen técnico (`tools/session_summary.py`), el formulario de papel (primera pasada global), el resumen de fin de sesión (08) y el registro del operador (07).

## 2 · Unidad de análisis: escenario × revisor
Para cada escenario se muestra una fila **por revisor** (nunca una fila promediada):
| Escenario | Revisor | Q10 final | Q1 | Q2 | Q3 | Q4 | Q5 | Q6/Q7 | Q8/Q9 | Comentarios (literal) | Primera pasada global (papel) |
|---|---|---|---|---|---|---|---|---|---|---|---|

## 3 · Resumen por escenario
- **Etiquetas globales**: lista de los `ACCEPT`, `ACCEPT_WITH_LIMITATION`, `RECALIBRATE` y `REJECT` individuales (no sólo conteos).
- **Preocupaciones por dimensión**, mostradas con el comentario que las acompaña:
  - *Dirección*: Q1 ∈ {PARTLY, NO}.
  - *Momento*: Q2 o Q3 ∈ {TOO_EARLY, TOO_LATE}.
  - *Magnitud*: Q4 ∈ {TOO_SMALL, TOO_LARGE, MIXED}.
  - *Educativa*: Q5 ∈ {POSSIBLY, YES}, Q7 ∈ {SOME, YES} o Q9 ∈ {MINOR, MAJOR}, más lo que diga el texto libre.
- **Cambios de opinión**: primera pasada (instantánea ciega + papel) frente a la final (líneas `AFTER REVEAL:`).
- Los comentarios **se leen y se codifican por personas del comité**. Ninguna IA interpreta los juicios docentes salvo decisión posterior expresa.

## 4 · El desacuerdo no se promedia (P3-299A)
Si dos o más revisores difieren, el resumen **muestra el desacuerdo**: matriz revisor × escenario con las etiquetas lado a lado y sus razones. No se elige una «etiqueta mayoritaria» ni se construye un puntaje.

## 5 · Etiquetas de resultado PROPUESTAS (P3-299B; no se aplican todavía)
Son etiquetas de **resumen**, no verdad clínica. Orden de precedencia: la primera que se cumpla.
| Etiqueta | Propuesta de condición |
|---|---|
| `STRUCTURAL_REJECTION` | Al menos un `REJECT` **con comentario** en un escenario núcleo, de cualquier revisor |
| `RECURRENT_CALIBRATION_CONCERN` | La misma dimensión (dirección, momento o magnitud) aparece señalada, o `RECALIBRATE`, en **≥ 2 escenarios** (de cualquier revisor) o en **el mismo escenario por ≥ 2 revisores** |
| `MIXED_REVIEW` | Hay desacuerdo entre revisores o límites declarados sin recurrencia |
| `UNANIMOUS_ACCEPT` | Con **≥ 2 revisores**: todos, en todos los escenarios núcleo, `ACCEPT` o `ACCEPT_WITH_LIMITATION`, sin `Q5 = YES`; los límites declarados se listan |
Con **un solo revisor** (la primera sesión) **no se asigna etiqueta de resultado**: se entrega la tabla por escenario marcada `SINGLE_REVIEWER_PRELIMINARY`.

## 6 · Qué puede desencadenar cada etiqueta (decisión docente, nunca automática)
- `UNANIMOUS_ACCEPT` → el comité decide si amplía la revisión a otra persona o a otros escenarios.
- `MIXED_REVIEW` → discusión docente; posible segunda ronda con otro revisor.
- `RECURRENT_CALIBRATION_CONCERN` → el comité decide **si** pedir una calibración y de **qué dimensión**; cualquier cambio de fisiología es un paquete nuevo con su propia autorización y certificación. **Esta revisión no recalibra nada.**
- `STRUCTURAL_REJECTION` → detener y reconsiderar el diseño.

## 7 · Anomalías técnicas (papel del software; separadas de lo clínico)
Del resumen técnico: escenarios sin paquete o sin respuesta, paquetes o artefactos que no verifican o no se repiten, ejecuciones que **difieren** del guion certificado, vínculos rotos y primera pasada no registrada. Se informan aparte y **no** se mezclan con los juicios docentes.

## 8 · Lo que el análisis no hará
No declara validación clínica, no concede autoridad de consciencia, no autoriza residentes ni producción, no usa residentes como fuente y no reescribe los registros originales (creación única).

## 9 · Entregables
Una tabla por escenario con todas las filas de revisores, la matriz de desacuerdo, la lista de anomalías técnicas, y un texto breve del comité con su decisión (si la hay).
