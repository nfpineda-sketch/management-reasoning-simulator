# AI Advisor Development Charter

**Estado: recibido el 2026-09-27, adoptado como guía de trabajo. El documento
llegó incompleto** (ver nota al final): se corta a mitad de la Sección 18. No se
completó ni se infirió el resto. Cuando el docente envíe la continuación, se
añade aquí sin reescribir lo ya recibido.

Este documento gobierna cómo el AI Advisor prioriza, propone y decide qué
implementar en el Management Reasoning Simulator. No es autorización para
implementar de inmediato lo que describe: su función explícita es AUDITAR →
IDENTIFICAR GAPS → PRIORIZAR → PROPONER → ESTIMAR IMPACTO/COSTO → SOLICITAR
DECISIONES CUANDO CORRESPONDA → IMPLEMENTAR SÓLO LO AUTORIZADO → VERIFICAR.

Las recomendaciones pendientes que se desprenden de este charter viven en
`docs/COLA_DECISIONES_AI_ADVISOR.md`, no en este archivo.

---

## NORTH STAR

El simulador debe hacer que un encuentro clínico sea:

1. suficientemente natural para que el residente actúe aproximadamente como lo
   haría frente a un paciente real;
2. suficientemente preciso para reconstruir fielmente su Management Reasoning;
3. suficientemente estructurado para convertir múltiples observaciones
   validadas por faculty en evidencia longitudinal trazable de su progresión.

El resultado final del caso NO es el principal objeto de evaluación.

Lo más importante es comprender:

- qué pensó el residente;
- qué decidió;
- por qué lo decidió;
- qué esperaba que ocurriera;
- qué observó después;
- cómo reevaluó;
- cómo adaptó su manejo.

Proponemos representar este proceso mediante el MANAGEMENT TRACE.

El Management Trace es el registro primario del encuentro.

Los análisis posteriores, Faculty Briefs, rúbricas, PDFs, Objective Progress y
evidencia longitudinal dependen de su fidelidad.

Por lo tanto, cualquier cambio que pueda deteriorar la fidelidad del
Management Trace debe considerarse de alto riesgo.

## 1. PRIORIDADES DEL DESARROLLO

Todas las decisiones técnicas deben priorizar, en este orden:

1. fidelidad del Management Trace;
2. plausibilidad clínica;
3. jugabilidad;
4. calidad y trazabilidad de la evidencia longitudinal;
5. eficiencia/costo;
6. latencia.

Ninguna optimización de costo o performance debe deteriorar significativamente
las cuatro primeras.

El trabajo debe ser lo más costo-efectivo posible.

Antes de agregar una feature, pregunta:

1. ¿Mejora la fidelidad del Management Trace?
2. ¿Mejora la plausibilidad clínica?
3. ¿Mejora la jugabilidad?
4. ¿Mejora la calidad de la evidencia longitudinal?
5. ¿Reduce costo o latencia sin sacrificar lo anterior?

Si no mejora significativamente al menos uno de estos dominios, cuestiona si
vale la pena implementarla.

## 2. LÍMITES DE AUTONOMÍA DEL AI ADVISOR

Sin autorización explícita:

- NO enviar emails ni comunicaciones externas;
- NO realizar cambios clínicos sustantivos;
- NO realizar cambios mayores de arquitectura;
- NO realizar cambios mayores de UX/diseño;
- NO cambiar scoring, rúbricas, mappings, EPAs/Milestones o reglas de
  evaluación;
- NO exceder en más de 30% el presupuesto/costo autorizado para una tarea;
- NO hacer refactors extensos que no sean necesarios para resolver el
  problema actual.

Si se estima que una tarea superará el límite de costo autorizado +30%,
DETENERSE y solicitar autorización antes de continuar.

Priorizar siempre la solución más costo-efectiva que preserve la calidad.

Evitar:

- análisis repetitivos;
- suites innecesariamente amplias;
- regeneración de recursos existentes;
- reanálisis de decisiones ya aprobadas;
- trabajo LOW PRIORITY no autorizado;
- exploraciones extensas sin una pregunta concreta;
- refactors estéticos sin beneficio funcional demostrable.

## 3. DECISION FILE

Mantener un archivo de recomendaciones pendientes para revisión humana
(`docs/COLA_DECISIONES_AI_ADVISOR.md`), como cola clara de decisiones que
requieren intervención del docente.

Cada recomendación debe ser breve, concreta y accionable:

PROBLEMA → EVIDENCIA → IMPACTO → RECOMENDACIÓN → ALTERNATIVAS →
COSTO/ESFUERZO ESTIMADO → DECISIÓN REQUERIDA

Incluye especialmente:

- decisiones clínicas;
- cambios mayores de arquitectura;
- cambios importantes de UX;
- scoring/evaluación;
- mappings ACGME/Royal College;
- cambios que puedan afectar la futura validez del instrumento;
- decisiones metodológicas;
- cambios estructurales importantes.

No implementar estas decisiones sin autorización cuando pertenezcan a estas
categorías.

El objetivo del archivo no es acumular ideas indefinidamente: debe contener
recomendaciones sobre las que realmente haya que tomar una decisión.

## 4. MANAGEMENT TRACE

El motor debe ser excepcionalmente bueno interpretando lenguaje clínico
natural tanto en INGLÉS como en ESPAÑOL.

Debe:

- reconocer diferentes formas válidas de expresar una misma acción;
- aceptar múltiples órdenes en una misma entrada;
- evitar que el residente tenga que repetir una orden porque el sistema no la
  entendió;
- preservar dosis, vía, timing y contexto cuando sean relevantes;
- distinguir acciones, razonamiento, expectativas y reevaluaciones;
- preservar la secuencia temporal;
- registrar suficiente información para reconstruir el Management Reasoning;
- evitar transformar el encuentro en un formulario.

El equilibrio fundamental es: CAPTURAR SUFICIENTE INFORMACIÓN PARA
RECONSTRUIR FIELMENTE EL MANAGEMENT REASONING sin DETERIORAR LA FLUIDEZ DEL
ENCUENTRO.

Cuando exista tensión entre captura exhaustiva y jugabilidad, identificar
explícitamente el trade-off y proponer una solución antes de agregar fricción
significativa.

## 5. JUGABILIDAD Y PLAUSIBILIDAD CLÍNICA

El residente debe poder comportarse aproximadamente como lo haría frente a un
paciente real.

Evitar:

- repetir una misma orden porque el sistema no la reconoció;
- exigir sintaxis artificial;
- múltiples formularios para realizar acciones simples;
- información clínica que el residente no solicitó;
- deterioros clínicamente incoherentes;
- mejorías clínicamente incoherentes;
- órdenes ignoradas;
- acciones que deban ingresarse varias veces;
- bloqueos innecesarios del flujo del encuentro.

El paciente debe responder de manera clínicamente plausible: a las
intervenciones, a la enfermedad, al paso del tiempo, a la ausencia de
intervenciones cuando corresponda.

La jugabilidad NO significa simplificar clínicamente el caso hasta hacerlo
artificial. La plausibilidad clínica NO significa hacer la interfaz tan
estricta que deje de ser jugable. Debemos optimizar ese equilibrio.

## 6. PRINCIPIO FUNDAMENTAL DE LA EVALUACIÓN

El objetivo NO es inferir la competencia del residente desde un único
encuentro. El objetivo es acumular múltiples evidencias observacionales
provenientes de distintos encuentros, distintos Decision Challenges,
distintas capacidades clínicas y diferentes momentos del entrenamiento.

Más observaciones independientes y relevantes deben permitir construir
progresivamente una representación más robusta y fiel del desempeño real del
residente.

## 7. ARQUITECTURA EDUCACIONAL Y DE EVIDENCIA (PRIORIDAD ARQUITECTÓNICA ALTA)

El audit actual encontró que la arquitectura funciona parcialmente, pero
existen dos pipelines que todavía no están completamente unificados. De 19
objetivos actualmente identificados, 14 completan la cadena observación →
confirmación docente → persistencia → progreso longitudinal.

Los principales gaps identificados son: R1-03, R1-04, R2-01, C2, C15.

No implementar fixes aislados sin considerar la arquitectura completa
descrita a continuación.

## 8. MODELO ARQUITECTÓNICO OBJETIVO

```
                   CLINICAL ENCOUNTER
                          │
             crea oportunidades para observar
                          │
            ┌─────────────┴─────────────┐
            ↓                           ↓
    DECISION CHALLENGES          ROYAL COLLEGE EPAs
       R1 / R2 / R3               TD / F / C
            │                           │
            └─────────────┬─────────────┘
                          ↓
               FACULTY CONFIRMATION
                          ↓
               OBSERVATIONAL EVIDENCE
                          ↓
           ┌──────────────┴──────────────┐
           ↓                             ↓
     ACGME MILESTONES              ROYAL COLLEGE
           │                             │
           └──────────────┬──────────────┘
                          ↓
              LONGITUDINAL EVIDENCE
                          ↓
        PROGRESSIVELY RICHER REPRESENTATION
              OF RESIDENT PERFORMANCE
```

REGLA ARQUITECTÓNICA FUNDAMENTAL: EL ENCUENTRO NO DETERMINA QUÉ COMPETENCIAS
FUERON DEMOSTRADAS. EL ENCUENTRO DETERMINA QUÉ COMPETENCIAS TUVIERON
OPORTUNIDAD DE SER OBSERVADAS.

El desempeño real del residente genera la evidencia. El faculty humano
confirma esa observación. Sólo entonces debe incorporarse al registro
longitudinal.

Ausencia de oportunidad ≠ desempeño insuficiente. Ausencia de oportunidad debe
permanecer como NO EVALUABLE / NO OBSERVADO.

## 9. DECISION CHALLENGES

Los Decision Challenges R1/R2/R3 tienen dos funciones diferentes pero
relacionadas.

**Antes del encuentro:** guían la selección/generación de encuentros capaces
de provocar un determinado desafío de razonamiento.

**Después del encuentro:** si ese razonamiento fue efectivamente observado y
posteriormente validado por faculty, puede convertirse en evidencia
longitudinal.

Gap específico: R1-03, R1-04, R2-01 actualmente pueden determinar/generar
encuentros y tienen correspondencias conceptuales con frameworks externos,
pero no pueden convertirse en evidencia longitudinal. Esto es inconsistente
con la arquitectura objetivo.

Prioridad:

1. verificar formalmente sus mappings;
2. corregir/verificar específicamente MK1 de R2-01, que actualmente no tiene
   una fuente suficientemente verificable;
3. proponer cómo incorporar R1-03, R1-04 y R2-01 al mismo pipeline
   observacional/longitudinal de los demás Decision Challenges.

NO inventar mappings por similitud semántica. Cualquier mapping nuevo o
corregido requiere revisión humana antes de implementación.

## 10. TD / F / C — ROYAL COLLEGE EPAs

TD/F/C corresponden directamente a Royal College EPAs verificadas.
Actualmente activos: TD1, F1, C1, C3, C4, C14.

Problema (prioridad alta): estos objetivos pueden actualmente acreditarse
independientemente de si el encuentro realmente creó una oportunidad
suficiente para observar esa EPA.

Ejemplo conceptual: un encuentro sin problema relevante de
airway/ventilation NO debería permitir acreditar C3 · Manage airway and
ventilation simplemente porque el objetivo está disponible.

Necesitamos que la elegibilidad de TD/F/C dependa de las oportunidades reales
de observación creadas por cada encuentro. La lógica debe ser CASE/ENCOUNTER
→ OBSERVATION OPPORTUNITIES → ACTUAL RESIDENT PERFORMANCE → FACULTY
CONFIRMATION → EVIDENCE, no CASE → todos los TD/F/C disponibles → faculty
puede seleccionar cualquiera.

Diseñar una propuesta para determinar elegibilidad basada en oportunidades
reales del encuentro. No implementar una solución clínica o de mapping sin
aprobación.

## 11. C2 Y C15

C2 = Manage critical trauma resuscitation. Actualmente deshabilitada porque
originalmente no existían encuentros trauma suficientes. Posteriormente se
agregó una familia trauma utilizada por Decision Challenges como R2-04 y
R2-05. Esto NO significa automáticamente que C2 deba habilitarse. Primero
determinar si esos encuentros crean oportunidades suficientes para observar
"management of critical trauma resuscitation" y no simplemente la presencia
de un paciente traumatizado. Generar una recomendación separada.

C15 = Provide end-of-life care. Mantener C15 deshabilitada mientras no
existan encuentros que realmente creen oportunidades suficientes para
observar end-of-life/palliative care. No habilitar C15 simplemente para
completar el framework.

## 12. CONVERGENT EVIDENCE VS DOUBLE COUNTING

No interpretar automáticamente múltiples mappings hacia una misma
EPA/Milestone como duplicación. Ejemplo: R1-05 → PC4, R2-03 → PC4, R2-04 →
PC4 puede representar exactamente lo que buscamos: diferentes situaciones +
diferentes comportamientos + diferentes momentos → múltiples observaciones
convergentes sobre PC4. Eso aumenta la riqueza del perfil longitudinal.

Distinguir siempre:

- **A. Convergent evidence** — observaciones realmente diferentes que
  aportan información complementaria sobre una misma EPA/Milestone.
- **B. Double counting** — la misma conducta del mismo encuentro registrada
  más de una vez como si fueran observaciones independientes de la misma
  capacidad.

NO implementar todavía reglas de unicidad que impidan que diferentes
objetivos contribuyan al mismo EPA/Milestone. Podrían destruir la
convergencia de evidencia que queremos construir.

## 13. NO CREAR TODAVÍA UN SCORE GLOBAL EPA/MILESTONE

No agregar todavía scoring agregado por EPA o Milestone. Primero preservar:
observaciones individuales, encuentro de origen, evidencia, fecha, faculty
reviewer, objective_id, framework mapping, autonomía, profundidad, y
cualquier información contextual relevante. Después se decidirá
metodológicamente cómo sintetizar múltiples observaciones longitudinales.

No convertir automáticamente múltiples observaciones en: porcentaje de
competencia, nivel EPA, milestone level, pass/fail, certification.

## 14. CROSSWALK ACGME / ROYAL COLLEGE

TD/F/C ya son Royal College EPAs verificadas. No necesitan artificialmente
mapearse a otra Royal College EPA.

Los Decision Challenges son objetivos locales y sí necesitan mappings
externos defendibles si van a alimentar perfiles ACGME/Royal College. No
inventar crosswalks ACGME ↔ Royal College por similitud semántica.

Si se quiere que TODAS las observaciones puedan converger simultáneamente
sobre perfiles ACGME y Royal College, se necesitará construir y validar un
crosswalk metodológicamente defendible. Tratarlo como una futura tarea
metodológica separada que requiere aprobación.

## 15. OBJETIVO FINAL DE LA ARQUITECTURA DE EVIDENCIA

Que cada desempeño observable del residente —Decision Challenges y TD/F/C—
genere evidencia válida y trazable hacia las EPAs y/o Milestones
correspondientes, acumulándose longitudinalmente a través de múltiples
encuentros para construir una representación cada vez más robusta y fiel de
su progresión real.

No inferir competencia desde una única observación. Más encuentros → más
observaciones independientes → más evidencia convergente → representación
progresivamente más robusta del desempeño real.

## 16. PERFIL LONGITUDINAL MULTIDIMENSIONAL

NO reducir al residente a un único score. El perfil longitudinal debe
preservar varias dimensiones complementarias:

1. **Management reasoning** → dominios D1–D5 longitudinales.
2. **Safety** → critical safety events confirmados.
3. **Competency evidence** → Decision Challenges + TD/F/C → EPAs/Milestones.
4. **Depth / autonomy** → características de las observaciones confirmadas.
5. **Management Trace** → evidencia primaria desde la cual puede
   reconstruirse el razonamiento y auditarse el resto.

Estas señales responden preguntas diferentes y NO deben colapsarse
prematuramente en un único número.

## 17. LONGITUDINAL MANAGEMENT REASONING PROFILE (decisión tomada)

El spider/radar chart longitudinal utilizará los cinco dominios existentes
de la rúbrica (D1–D5) en su escala actual (0–3). Cada eje representa el
promedio aritmético de los scores válidos y confirmados por faculty para ese
dominio:

```
longitudinal_domain_value =
    sum(faculty-confirmed valid domain scores)
    / number of evaluable faculty-confirmed observations
```

Reglas:

- sólo cuentan rúbricas confirmadas por faculty;
- sólo cuentan observaciones donde ese dominio fue evaluable;
- NO EVALUABLE / NO OBSERVADO queda fuera del numerador y del denominador;
- ausencia de oportunidad nunca equivale a cero;
- la escala permanece 0–3, no se convierte a porcentaje;
- cada nueva rúbrica aprobada actualiza el promedio longitudinal;
- se conserva siempre cada observación individual, con timestamp,
  encounter_id y faculty confirmation — nunca se persiste únicamente el
  promedio.

Junto a cada dominio debe conservarse y, cuando sea posible, mostrarse n =
número de observaciones válidas que sustentan ese promedio (D1 = 2.6/3 · n=18
es informativamente distinto de D1 = 2.6/3 · n=3).

El spider chart responde principalmente "¿Cómo se desempeña habitualmente
este residente en cada dimensión observada del Management Reasoning?". No
responde por sí solo "¿Es competente?" y NO constituye certificación de
competencia.

## 18. CRITICAL SAFETY EVENTS COMO SEÑAL INDEPENDIENTE

> **[DOCUMENTO TRUNCADO AQUÍ — 2026-09-27]**
> El texto recibido termina a mitad de frase: *"Los critical safety events
> NO deben modificar los promedios D1–D5 ni la forma del spider/r…"*. No se
> completó ni se infirió el resto de esta sección, ni si existen secciones
> posteriores a la 18. Nada de la Sección 18 se trató como definido hasta
> recibir su continuación completa.
