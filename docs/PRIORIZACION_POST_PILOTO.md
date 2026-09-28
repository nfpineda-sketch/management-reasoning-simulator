# Cómo se priorizarán los errores del piloto

Ciclo 5 del AI Advisor (59S), 2026-09-28. Preparado antes de que vuelvan los
documentos; no inicia el ciclo 6.

**Qué es:** una matriz de decisión simple. **No es un puntaje**: las seis
dimensiones se leen juntas, en orden, y deciden en qué fila cae el error.

## Las seis dimensiones

Cada error adjudicado del piloto (`adjudication.csv`) se describe en seis
dimensiones:

| Dimensión | Pregunta | De dónde sale |
|---|---|---|
| **FREQUENCY** | ¿Cuántas entradas y cuántos médicos lo muestran? | conteo en la adjudicación; ¿aparece en DEVELOPMENT y también en SEALED? |
| **CLINICAL IMPORTANCE** | ¿Podría cambiar el manejo o registrar falsamente una decisión importante? | columna `impact` (CRITICAL / HIGH / MEDIUM / LOW) |
| **TRACE IMPACT** | ¿El Management Trace queda infiel: una orden que no se dio, una razón que no se dijo, un plan perdido? | columna `locus` = trace; fidelidad en el reporte |
| **PLAYABILITY IMPACT** | ¿El residente se atasca: retención, pregunta repetida, reformular algo ya dicho? | `clarification_asked` y retenciones en la hoja |
| **REPRODUCIBILITY** | ¿Se reproduce con una frase nueva de la misma clase, o sólo con esa frase? | prueba con frases nuevas escritas después, como en DF-16 |
| **FIX RISK** | ¿La corrección toca una regla deliberada, otra clase o el motor clínico? | revisión del código; defectos conocidos relacionados |

## La matriz

Se lee de arriba abajo; el error cae en la primera fila que lo describe.

| Fila | Cuándo | Qué se hace |
|---|---|---|
| **1 · Corregir ya** | **Importancia CRITICAL**, o **HIGH con traza infiel**, **y** reproducible como clase | Corrección por clase en el ciclo siguiente, con frases nuevas y guardas; se mide primero contra el baseline |
| **2 · Corregir por clase** | **Frecuente** (varios médicos) y reproducible, con **riesgo de corrección bajo** | Entra al ciclo siguiente como DF-16 o KD-01: una clase, BEFORE/AFTER, EN/ES |
| **3 · Preguntar al docente** | La corrección cambia una **regla deliberada** (p. ej. KD-02: un fármaco sin dosis no es orden; KB-01: el oxígeno pide el flujo), o el error depende de un **criterio clínico** | Decisión docente antes de tocar el código |
| **4 · Registrar y medir** | Poco frecuente, LOW o MEDIUM sin traza infiel, o que **no se reproduce** con frases nuevas | Defecto conocido con ID; se vuelve a medir en la fase siguiente |
| **5 · No es del motor** | ANNOTATION_DISAGREEMENT o AMBIGUOUS_INPUT | Se revisa la guía de anotación o el formato del documento, no el lector |

## Tres reglas

- **La frecuencia sola no manda.** Un error raro pero CRITICAL va antes que uno
  frecuente y cosmético.
- **Nunca se corrige una frase.** Si sólo se reproduce con la frase del médico,
  es fila 4. El piloto conserva su capacidad de revelar fallas independientes.
- **SEALED no se abre para priorizar.** La frecuencia se cuenta en
  DEVELOPMENT. SEALED se mide una sola vez, con una versión candidata
  congelada.

## Las clases de la auditoría nocturna (DF-22)

La auditoría interna del ciclo 5 encontró 9 clases CRITICAL y 14 HIGH con
frases escritas por una IA (`AUDITORIA_TRACE_CICLO5.md`). No se corrigieron ni
se registraron como defectos conocidos, para que el piloto mida su frecuencia
real.

- **Cuando un error del piloto cae en una de esas clases:**
  - se prioriza con esta misma matriz, con su frecuencia en el piloto;
  - se anota que la auditoría interna ya lo había visto. Eso cuenta como
    reproducibilidad, no como frecuencia.
- **Recomendación, a confirmar en DF-22:** las clases que el piloto no
  muestre van a la fila 4 (registrar y medir en la fase siguiente). No se
  corrigen sólo por haber aparecido en la auditoría.
