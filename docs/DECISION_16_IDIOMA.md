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

## Segunda etapa, pendiente

- **La narrativa autorizada de cada caso**: presentación, respuestas de la anamnesis y prosa del
  examen físico siguen en inglés. Se dejaron fuera a propósito: traducirlas por sustitución
  produciría exactamente la frase mezclada que la decisión objeta.
- **La revisión posterior**: Decision Review, Expert Comparison, Adaptation Plan, Final Summary
  y el Management Trace siguen en inglés, incluida la frase que originó la decisión
  (*"Your recorded expected effect was: …"*). Cuando se traduzca, el texto original del
  residente debe aparecer como cita, no insertado dentro de una frase en el otro idioma.
- **Elegir otro idioma al exportar** el Management Trace y el informe docente.
- **Los resultados estructurados de laboratorio** (nombres de los analitos) siguen en inglés.
- **El idioma real del paciente** como objetivo educativo propio (comunicación con intérprete)
  queda fuera, como pediste.
