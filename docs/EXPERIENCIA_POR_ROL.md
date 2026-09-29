# Experiencia por rol

Ciclo 9 · 2026-09-29 · fase posterior al congelamiento de V3 (§154A–§154GL de la
instrucción docente). Cambia cómo se encuentra y se lee el registro; no cambia
el motor, D1–D5, la escala 0–3, los eventos críticos, el puntaje ajustado, el
radar, la confirmación docente ni la semántica de la evidencia (§154CO, §154EN).
Todo se probó con cuentas y datos sintéticos.

**Principio (§154B).** El residente ve; el docente evalúa; el Admin gobierna; la
IA aconseja. Los tres miran la misma evidencia: cambian los permisos, no los datos.
Los permisos están en `docs/MATRIZ_PERMISOS_ROLES.md`.

## Residente

| Página | Qué muestra | Dónde |
|---|---|---|
| Inicio («Clinical encounters») | Si hay un caso asignado: «Assigned to me · New clinical encounter · assigned AAAA-MM-DD» y el botón de siempre. Nunca el desafío, el caso, la razón ni quién lo asignó (§154E, §154R). | `curriculum_runtime.render_dashboard`, `DirectiveStore.assigned` |
| My progress | Seis vistas de sólo lectura, nunca un puntaje único (§154S): **Overview** (registro por objetivo de siempre + áreas con evidencia limitada + foto e iniciales), **Management reasoning** (el mismo perfil D1–D5 que lee el docente, con la frase de §154T), **Decision challenges**, **Royal College** (EPA como evidencia observacional; meta local con la explicación de §154V; componentes observados y lo que queda fuera; contextos en que se observó), **ACGME** (subcompetencias, contribuciones directas y parciales, encuentros, fuente; sin nivel), **Safety** (eventos críticos confirmados, aparte del radar). Cada observación lleva a su encuentro y su Management Trace (§154Y). | `resident_pages.render_my_progress`, `evidence_views` |
| My encounters | Tabla: fecha y hora, contexto clínico, revisión docente, rúbrica, observaciones confirmadas; nunca el desafío de un encuentro (§154AB). Detalle en el orden de §154AC: 1 Management Trace, 2 retroalimentación docente, 3 rúbrica, 4 observaciones confirmadas, 5 eventos de seguridad. Debajo, lo que el residente dijo que haría distinto. | `resident_pages.render_my_encounters` |
| My portfolio | Sólo documentos finales: la Management Trace de cada encuentro y cada rúbrica confirmada, en su última revisión confirmada (§154AG). Descarga individual a pedido y **portafolio completo en ZIP** (`Management_Traces/`, `Rubrics/`, `manifest.json` con encuentro, fecha, residente, revisor, fecha de confirmación, revisión y SHA-256; §154AI, §154AK, §154DN). El ZIP no hace ninguna llamada de IA: usa sólo traducciones ya guardadas (§154DO). Además, el registro completo en JSON de siempre. | `portfolio`, `prose_translation.stored_only` |

## Docente

- **Inicio = cohorte (§154G–§154J):** una tarjeta por residente, por año de
  formación y nombre, con foto o iniciales, año, la forma D1–D5 de lo confirmado
  y lo que espera revisión. Búsqueda y filtro «Needs review». Sin puntaje global,
  sin orden por resultado, sin comparación entre pares (§154CM, §154EF).
- **Vista del residente (§154K, §154L):** cabecera con foto/iniciales, año, radar,
  n por dominio, encuentros completados, revisiones de rúbrica confirmadas,
  observaciones confirmadas, pendientes y eventos críticos confirmados; debajo, el
  flujo de revisión existente, ya centrado en ese residente (encuentro → Trace →
  brief → rúbrica → observaciones), y **Evidence by framework and portfolio**: las
  mismas vistas que lee el residente y su portafolio (§154AL).
- **Asignación ciega:** la de siempre (`Direct a resident's next encounter`), con
  la autorización del Admin por residente.

## Administrador

- Todo lo del docente, con la misma cohorte y la misma vista del residente (§154AN).
- **Cuentas (§154AO–§154AQ):** tabla con cuenta, estado ACTIVA/INACTIVA, rol y año
  en «Account administration»; activar o desactivar con el control existente,
  verificado en el store. Desactivar no borra (§154AP).
- **AI Longitudinal Review:** especificada y diferida (`docs/AI_LONGITUDINAL_REVIEW_SPEC.md`).

## Diferido, con su razón

| Ítem | Por qué |
|---|---|
| AI Longitudinal Review (P3) | §154FS: presupuesto primero para P1/P2; especificación completa. |
| Notas privadas docentes (§154AE) | No existe la capa; requiere persistencia nueva. |
| Descarga selectiva del portafolio (§154AJ) | La individual y la completa cubren lo prioritario. |
| «Ver» el PDF dentro de la app (§154AH) | `st.pdf` necesita un componente que no está instalado; el PDF se descarga. |
| Registro de auditoría de activar/desactivar (§154EI) | Requiere una tabla nueva en el store de cuentas: Fase 2. |
| Historial de asignaciones por residente (§154DT) | `DirectiveStore.history` existe; falta una vista. |
| Portafolio de una cuenta inactiva (§154DM) | Una cuenta inactiva no inicia sesión; pedir otra cosa es una decisión aparte. |
| Reflexión posterior al encuentro (§154AM) | Hoja de ruta. |

## Hallazgos previos a esta fase, para decisión

1. **Llamadas automáticas de traducción.** Con clave configurada y un documento en
   español, la revisión del encuentro del residente y los PDF del docente se
   construyen al cargar la página y piden la traducción de lo no traducido.
   «My progress» ya no lo hace: sus documentos se preparan a pedido. No se cambió
   el resto (§154FT).
2. **El foco de aprendizaje se muestra al cerrar el encuentro,** antes de la
   revisión docente (decisión anterior). §154AB pide no mostrar el objetivo antes
   de la revisión: queda a su decisión.
   **Decidido e implementado el 2026-09-29:** el residente lee el foco de un
   encuentro cuando un docente lo revisó (rúbrica confirmada u observación
   confirmada, la regla con que ya se publican sus páginas); antes ve «Your
   learning focus for this encounter is shared after a faculty member reviews it».
   Vale para el cierre, la revisión guardada y la copia de su registro
   (`challenge_id` vacío hasta la revisión). El docente y el administrador lo ven
   siempre. Sin cuentas (modo local) no hay a quién ocultarlo.
3. **«Espera revisión» en la cohorte** usa el estado existente (§154N): un
   encuentro espera mientras su rúbrica no está confirmada o un objetivo elegible
   no tiene observación, así que puede seguir esperando tras confirmar la rúbrica.
4. **Selector «Encounter record» del docente:** su etiqueta tiene resolución de
   minuto; dos encuentros del mismo desafío terminados en el mismo minuto se
   confundirían (el mismo defecto que se corrigió en las páginas nuevas). Improbable.
5. **Faculty lee a todos los residentes del programa,** no sólo a los «asignados»
   (§154CA): arquitectura de un solo programa.
6. **Catálogo de pantallas:** la clave `Working model` está duplicada.

## Revisión visual (§154CQ, §154EM)

Renderizado real: la app en Streamlit local con una base SQLite sintética
descartable (fuera del repositorio) y Chromium con Playwright; 19 capturas a
1440 y 1000 px de ancho. Páginas: cohorte docente, vista del residente, evidencia
por marco, portafolio docente, inicio del residente con asignación, las seis
vistas de My progress, My encounters con documentos, My portfolio con ZIP, inicio
del Admin, administración de cuentas, cohorte y Royal College a 1000 px.

| Hallazgo | Estado |
|---|---|
| El radar de la tarjeta quedaba vacío con una sola revisión confirmada | Corregido, con prueba |
| Tres encuentros del mismo caso y minuto tenían la misma etiqueta: el pedido de documentos caía en otro encuentro | Corregido (etiqueta con hora y número), con prueba |
| Tablas ACGME/CanMEDS más anchas que la pantalla | Columnas acortadas; la fuente va debajo |
| Columna «Status» oculta en la barra lateral del Admin | Reordenada |
| Fecha repetida en la vista de seguridad; avisos sobre «cómo correr un encuentro» sobre el registro de un residente | Corregidos |
| Tipos mezclados en la columna «Year» (advertencia de Arrow) | Corregido |
| Estado de la tarjeta en cuatro renglones a 1000 px | Dos líneas cortas |
| Página docente larga: la evidencia por marco queda al final | Sin resolver (prioridad al flujo de revisión, §154DV) |
| Rótulos del radar pequeños en la tarjeta | Sin resolver (el radar grande está en la vista del residente) |
| Columna «Through» larga | Sin resolver (la tabla se desplaza) |

## Pruebas

`test_role_permissions.py` (5), `test_faculty_cohort.py` (7), `test_resident_pages.py`
(15) y los ajustes de navegación en `test_curriculum_app.py` y
`test_curriculum_assignment.py`. Todas con cuentas sintéticas.
