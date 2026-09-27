# Idioma de presentación — primera etapa implementada

> **Estado: PRIMERA ETAPA IMPLEMENTADA** el 2026-09-21 en `language.py` y en los puntos de
> render de `app.py`, con la decisión docente 16. La segunda etapa —el contenido narrativo y
> los informes— sigue pendiente y está listada abajo.

## Lo que la decisión separó

| Elemento | Estado |
|---|---|
| **Idioma de entrada** | Ya era bilingüe y no cambió: la misma orden en español o en inglés produce la misma acción |
| **Idioma de presentación** | **Nuevo**: es una configuración, por defecto **inglés** |
| **Las palabras del residente** | **Nunca se reescriben**: el bloque "TÚ / YOU" muestra el texto original tal cual |

## Cómo está construido

El registro se **guarda en inglés**, que es la forma canónica del motor, y se **traduce donde se
muestra**. De ahí salen tres propiedades que la decisión pedía:

- Cambiar de idioma **vuelve a presentar el mismo encuentro**: no regenera el caso, no reinicia
  nada, no cambia tiempos ni tratamientos.
- Los **identificadores clínicos internos** son independientes del texto mostrado, así que la
  traducción no puede alterar fisiología, acciones disponibles ni evaluación.
- **Números, dosis, unidades, tiempos y nombres de fármacos no se tocan**: `aspirin 300 mg PO`
  es `aspirin 300 mg PO` en las dos.

El selector está en la barra lateral (**Idioma · Language**) y `MRS_LANGUAGE=es` lo fija para
una corrida sin interfaz. Escribir una orden en español **no** mueve el selector.

**No se usa IA para traducir**: es un catálogo revisado de mensajes exactos y de reglas de
sustitución sobre los fragmentos que el motor compone. Lo que no tiene regla se muestra tal
cual, en inglés, en vez de romperse.

## Qué se traduce hoy

| Zona | Estado |
|---|---|
| Tarjeta de respuesta del paciente (signos, estados, esfuerzo, dolor) | **sí** |
| Órdenes retenidas y sus mensajes de aclaración | **sí** |
| Mensajes del sistema del motor (exámenes no disponibles, horizontes, vías, dosis) | **sí** |
| Eventos de procedimiento (bloqueo AV, reperfusión, endoscopía, trombolisis, paro, parálisis sin ventilación, abstinencia, Wernicke, convulsión, alta prematura, diuresis, AINE duplicado) | **sí** |
| Encabezados de exámenes y su momento de toma | **sí** |
| Monitor de cabecera y la grilla de signos | **sí** |
| Encabezados del registro (RESPUESTA DEL PACIENTE, ACLARACIÓN, PROCEDIMIENTO, TÚ…) | **sí** |
| **Texto del residente** | se conserva **sin tocar**, por diseño |

Ejemplo real, el mismo encuentro con el selector en español:

> **PROCEDIMIENTO · 00:45**
> Bloqueo auriculoventricular completo: el infarto inferior tomó el nodo AV. La frecuencia cae
> y la presión cae con ella.
>
> **RESPUESTA DEL PACIENTE · 00:50**
> Tras aspirin 300 mg PO administrado + hemodinamia activada, PA 84/55 mmHg · FC 42/min ·
> SpO₂ 96% · FR 22/min. Alerta; esfuerzo respiratorio normal; llene capilar 3.6 s. El paciente
> refiere dolor intenso.

## Segunda etapa: instrucción del 2026-09-26

> «Si el encuentro se corre en español, los PDF se generan en español; si se corre en inglés, en inglés.
> Todo lo que se almacena en la app se puede definir si verlo en inglés o español.»

| Parte | Estado |
|---|---|
| **1 · Idioma del encuentro** | **Hecho** (C-2026-09-26-22). El encuentro guarda el idioma de pantalla con que se cerró (`encounter_language`). El Management Trace, el Faculty Brief y el documento de rúbrica salen en ese idioma, con un selector «Idioma del documento · Document language» junto a cada descarga. Un encuentro cerrado antes no registró idioma: sus documentos siguen la elección de quien los abre, sin adivinar. |
| **2 · Texto fijo de los documentos** | **Hecho** (C-2026-09-26-23). Encabezados, referencias, signos y sus valores, exámenes, órdenes, temas de historia, dominios, notas de convenciones y trazabilidad, en español con el catálogo revisado. |
| **3 · Texto del modelo** | **Hecho** (C-2026-09-26-24). Al pedir un documento en español se traducen, en una llamada, las frases del modelo que imprime (después de las correcciones), con `MRS_TRANSLATION_MODEL` (por defecto gpt-5-mini). Se guardan y se reutilizan; el original en inglés sigue siendo el registro. Nunca se envían las palabras del residente. Sin clave no se traduce y el documento lo dice. |
| **4a · El cuarto PDF: registro completo del encuentro** | **Hecho** (C-2026-09-27-05). El PDF y el Markdown de la revisión de decisiones salen en el idioma del encuentro, con el mismo selector de los otros documentos; el JSON sigue siendo el registro. Las preguntas de reflexión y el modelo experto de los encuentros del currículo se componen de nuevo en español desde la misma evidencia, con las palabras del residente citadas «así». |
| **4a · Estructura de los informes de exámenes** | **Hecho** (C-2026-09-27-06). Secciones y etiquetas del POCUS y campos de laboratorio en español en la sala y en los documentos, para que un hallazgo aprobado no comparta línea con una etiqueta en inglés. |
| **4b · Sala y pantallas de revisión** | **Hecho** (C-2026-09-27-07). Las etiquetas de órdenes del motor, los hallazgos de examen que compone, el completado guiado del razonamiento y los avisos se dicen enteros en español (medido con el ensayo de los 20 escenarios); las cuatro pantallas de revisión muestran sus textos, preguntas y modelo experto en el idioma de quien lee. |
| **4b · Portal del residente y pantallas de la Management Trace** | **Hecho** (C-2026-09-27-08). Portal, Management Trace en pantalla, registro decisión por decisión y página del encuentro completado en el idioma elegido; el razonamiento de la IA en pantalla aparece traducido si su traducción ya está guardada. |
| **4c · Portales docentes** | **Hecho** (C-2026-09-27-09). Informe docente, rúbrica, progreso, banco de imágenes, cuentas y panel del currículo en el idioma elegido, con encabezados de tabla y opciones de formulario; los valores guardados no cambian. |
| **5 · Narrativa de los 31 casos** | **Hecho, a la espera de tu revisión** (C-2026-09-26-25). La presentación, la anamnesis, el examen físico y los informes de exámenes de los 31 casos están traducidos en `case_text/es/`. Cada caso se usa en español sólo después de que lo apruebes en el panel docente («Case narrative in Spanish»); hasta entonces sigue en inglés, entero. Los puntos para tu decisión están en `docs/TRADUCCION_CASOS.md`. |

**El idioma del encuentro es el de la pantalla, no el de las órdenes.** La decisión 16 los separó: escribir
en español no mueve el selector. Un residente que juega en español debe tener el selector en «Español»
(o la app `MRS_LANGUAGE=es`).

**Queda en inglés a propósito:** los títulos oficiales de los objetivos del currículo (redacción oficial
de competencias, decisión del 2026-09-23). Si quieres una versión en español, dímelo y la preparo para tu
revisión.

## Segunda etapa, pendiente (lista original del 2026-09-21)

- ~~**La narrativa autorizada de cada caso**~~: traducida el 2026-09-26 como pasajes enteros revisados
  por la docencia, no por sustitución, que produciría la frase mezclada que la decisión objeta (parte 5).
- **La revisión posterior**: Decision Review, Expert Comparison, Adaptation Plan, Final Summary
  y el Management Trace siguen en inglés, incluida la frase que originó la decisión
  (*"Your recorded expected effect was: …"*). Cuando se traduzca, el texto original del
  residente debe aparecer como cita, no insertado dentro de una frase en el otro idioma.
- **Elegir otro idioma al exportar** el Management Trace y el informe docente.
- **Los resultados estructurados de laboratorio** (nombres de los analitos) siguen en inglés.
- **El idioma real del paciente** como objetivo educativo propio (comunicación con intérprete)
  queda fuera, como pediste.
