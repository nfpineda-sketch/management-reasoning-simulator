# Rúbrica de desempeño en management reasoning — versión piloto 1.0

> **Estado: piloto, pendiente de validación.** Es una síntesis propia fundamentada en los
> documentos citados abajo. Sus puntajes **no** equivalen a niveles de ACGME, a etapas
> canadienses ni a niveles de supervisión de APC, y **no** son una evaluación integral de la
> competencia de un especialista. Falta estudiar acuerdo entre evaluadores, funcionamiento de
> los descriptores, efecto de las penalizaciones y comparabilidad entre casos, idiomas y programas.

Identificador de versión en código: `rubric.VERSION = "1.0-pilot"`. Un encuentro evaluado
conserva la versión bajo la que se evaluó; actualizar la rúbrica **no** recalifica lo anterior.

## Qué mide y qué no

Cinco dominios, 0–3 cada uno, **igual ponderación**. Puntaje base 0–15 sólo cuando los cinco
son evaluables. La penalización por evento crítico confirmado es **−3**, centralizada en
`rubric.CRITICAL_EVENT_PENALTY`, y es una **decisión inicial de diseño pendiente de validación**.

Un 3 no significa escribir más, pedir más exámenes ni tratar más. Un manejo conservador bien
justificado puede obtener el máximo. Comunicación, preferencias del paciente, seguridad y uso
de recursos se consideran cuando son pertinentes y observables, sin añadir dominios nuevos.

**D4 frente a D5:** reevaluar es obtener y comprobar información nueva; adaptar es usarla para
decidir qué sigue. Mantener un tratamiento después de comprobar una respuesta adecuada **es**
una adaptación, no una omisión.

## Jerarquía de fuentes

**Principales** (las cinco acordadas):

| # | Documento | Versión leída | Págs. |
|---|---|---|---|
| 1 | ACGME — Emergency Medicine Milestones | v2.1, implementación 1 jul 2021; 2.ª revisión feb 2021 | 28 |
| 2 | Royal College of Physicians and Surgeons of Canada — *Pathway to Competence: Emergency Medicine* | 2018 | 61 |
| 3 | ACEM — FACEM Training Program Curriculum | CU440 v4.12, mayo 2026 | 164 |
| 4 | RCEM — Emergency Medicine Training Curriculum | actualización 2025, v1.5 | 131 |
| 5 | Argentina — Marco de Referencia para Residencias Médicas de Emergentología | 2023 | 63 |

**Secundarias de apoyo:** UEMS *European Training Requirements for Emergency Medicine* (2024);
España, Orden PJC/311/2026 (BOE-A-2026-7635); Brasil, Resolución CNRM n.º 12 de 6 jul 2021;
Chile, estudio Delphi modificado 2024; Colombia, documento ICFES–ASCOFAME; México, programa
operativo de sede bajo el PUEM de la UNAM 2025–2026.

**Precisiones que esta rúbrica sostiene explícitamente:**

- El documento canadiense es un *Pathway* con hitos y vínculos a EPA. **No** es el conjunto de
  fichas de evaluación de las EPA.
- El documento mexicano es el programa operativo de **una sede**. No es una rúbrica nacional.
- El documento chileno es un **estudio de consenso**, no una norma nacional.
- El resumen de cambios de RCEM **acompaña** al currículo; no es fuente independiente.
- No se afirma vigencia normativa que no se haya comprobado.
- Los marcos comparten contenidos pero **no son intercambiables**. ACEM declara basarse en
  CanMEDS; eso no lo convierte en copia del currículo canadiense. Argentina usa APC y un proceso
  de consenso propio. **Las coincidencias no cuentan como cinco validaciones independientes.**

## Matriz de trazabilidad

Cada fila: dominio → conducta observable → documento y versión → sección o identificador →
página → evidencia que el simulador puede capturar.

Las páginas son las del PDF leído. En el documento de ACEM la página impresa coincide con la
del PDF (verificado en p. 41, 45, 47 y 51).

### D1 · Reconocimiento de gravedad y priorización

| Conducta observable | Documento | Sección / id | Pág. | Evidencia capturable |
|---|---|---|---|---|
| Identifica al paciente inestable que requiere intervención inmediata | ACGME v2.1 | Patient Care 1: Emergency Stabilization | 7 | Observables de llegada frente al primer turno; minuto de la primera acción |
| Identifica presentación oculta con riesgo de deterioro | ACGME v2.1 | Patient Care 1, nivel 3 | 7 | Órdenes anticipatorias registradas antes del deterioro |
| Prioriza los problemas a abordar en el encuentro | Canadá 2018 | Medical Expert **2.1** *Prioritize issues to be addressed in a patient encounter* | 11 | Orden de las acciones dentro de un mismo envío |
| Realiza evaluaciones clínicas en el momento oportuno | Canadá 2018 | **1.4** *Perform appropriately timed clinical assessments* | 8 | Intervalos entre decisión y reevaluación |
| Atención inicial y reanimación | ACEM CU440 v4.12 | *Initial Emergency Medicine Care* | 41 | Acciones ejecutadas en los primeros minutos |
| Priorización y toma de decisiones | ACEM CU440 v4.12 | *Prioritisation and Decision Making* | 113 | Secuencia y urgencia de las órdenes |
| Identificar al paciente grave, reanimar y estabilizar | RCEM 2025 v1.5 | Learning Outcome **3**, §3.2.1 | 26 | Reconocimiento de la amenaza en el texto de razonamiento |
| Identificar la gravedad del cuadro al ingreso | Argentina 2023 | **APC #1** | 13 | Modelo de trabajo declarado en el primer turno |
| Decidir en los tiempos que requiere la urgencia | Argentina 2023 | **APC #3** | 16 | Minuto de cada orden ejecutada |

### D2 · Evaluación e interpretación clínica

| Conducta observable | Documento | Sección / id | Pág. | Evidencia capturable |
|---|---|---|---|---|
| Anamnesis y examen físico enfocados al motivo y a lo urgente | ACGME v2.1 | Patient Care 2: Performance of a Focused History and Physical Exam | 8 | Preguntas de anamnesis y regiones examinadas |
| Selección e interpretación de estudios | ACGME v2.1 | Patient Care 3: Diagnostic Studies | 9 | Estudios solicitados, hora de muestra y de informe |
| Construcción del diagnóstico | ACGME v2.1 | Patient Care 4: Diagnosis | 10 | Modelo de trabajo y su revisión entre turnos |
| Seleccionar e interpretar estudios según un diagnóstico diferencial | Canadá 2018 | Hito de Medical Expert (texto verbatim; el número de competencia habilitante no es separable en el texto extraído) | 13 | Relación entre estudio pedido y diferencial escrito |
| Generar diferenciales ante incertidumbre diagnóstica | Canadá 2018 | Hito de Medical Expert (ídem) | 14 | Alternativas nombradas en el razonamiento |
| Evaluación enfocada | ACEM CU440 v4.12 | *Focused Assessment* | 47 | Anamnesis dirigida y examen por regiones |
| Análisis de exámenes | ACEM CU440 v4.12 | *Analysis of Investigations* | 53 | Interpretación escrita frente al resultado entregado |
| Cuidado del paciente estable en todo el rango de complejidad | RCEM 2025 v1.5 | Learning Outcome **1**, §3.2.1 | 17 | Amplitud de la evaluación registrada |
| Responder preguntas clínicas y decidir con seguridad | RCEM 2025 v1.5 | Learning Outcome **2**, §3.2.1 | 22 | Justificación explícita de cada decisión |
| Identificar la gravedad; decidir a tiempo | Argentina 2023 | **APC #1**, **APC #3** | 13, 16 | Integración de hallazgos en el modelo declarado |

### D3 · Selección y ejecución de un manejo seguro

| Conducta observable | Documento | Sección / id | Pág. | Evidencia capturable |
|---|---|---|---|---|
| Estabilización: intervenciones y protocolos avanzados | ACGME v2.1 | Patient Care 1 | 7 | Acciones ejecutadas y su especificación |
| Farmacoterapia | ACGME v2.1 | Patient Care 5: Pharmacotherapy | 11 | Fármaco, dosis, vía y velocidad registrados |
| Abordaje general de procedimientos | ACGME v2.1 | Patient Care 8: General Approach to Procedures | 14 | **Cobertura parcial:** el motor ejecuta intubación, cardioversión, VNI y descompresión torácica; no ejecuta la mayoría de los procedimientos manuales |
| Determinar el procedimiento o terapia más apropiado | Canadá 2018 | **3.1** *Determine the most appropriate procedures or therapies* | 18 | Intervención elegida frente a alternativas disponibles |
| Priorizar según urgencia clínica y recursos | Canadá 2018 | **3.3** | 19 | Orden y momento de las intervenciones |
| Tratamiento | ACEM CU440 v4.12 | *Treatment* | 60 | Órdenes ejecutadas con sus parámetros |
| Medicina de reanimación | ACEM CU440 v4.12 | *Resuscitation Medicine* | 42 | Soporte instaurado y su configuración |
| Identificar, reanimar y estabilizar | RCEM 2025 v1.5 | Learning Outcome **3**, §3.2.1 | 26 | Intervenciones ejecutadas frente a las retenidas |
| Tratar emergencias que requieren intervención inmediata | Argentina 2023 | **APC #4** | 18 | Tratamiento ejecutado y su especificación |
| Tratar patologías clínicas en la Unidad de Emergencia | Argentina 2023 | **APC #9** | 29 | Ídem |

### D4 · Seguimiento y reevaluación

| Conducta observable | Documento | Sección / id | Pág. | Evidencia capturable |
|---|---|---|---|---|
| Reevaluar al paciente tras una intervención estabilizadora | ACGME v2.1 | Patient Care 1, nivel 3 | 7 | Reevaluación declarada y su intervalo |
| Reevaluación y destino | ACGME v2.1 | Patient Care 6: Reassessment and Disposition | 12 | Variables vigiladas y respuesta comprobada |
| Evaluaciones clínicas en el momento oportuno | Canadá 2018 | **1.4** | 8 | Intervalo entre orden y comprobación |
| Medicina de observación | ACEM CU440 v4.12 | *Observational Medicine* | 61 | Ventana de observación y lo que se vigiló |
| Seguimiento del paciente que espera definición de destino | Argentina 2023 | **APC #8** | 28 | Comprobación de ejecución y de resultado |

### D5 · Adaptación y continuidad del manejo

| Conducta observable | Documento | Sección / id | Pág. | Evidencia capturable |
|---|---|---|---|---|
| Revisión del diagnóstico ante información nueva | ACGME v2.1 | Patient Care 4: Diagnosis | 10 | Cambio o mantención justificada del modelo |
| Reevaluación y destino | ACGME v2.1 | Patient Care 6 | 12 | Destino decidido y pendientes declarados |
| Reconocer y responder a la complejidad, incertidumbre y ambigüedad | Canadá 2018 | **1.6** | 9 | Manejo de datos discordantes |
| Establecer un plan de manejo centrado en el paciente | Canadá 2018 | **2.4** *Establish a patient-centred management plan* | 15 | Plan declarado y su actualización |
| Toma de decisiones | ACEM CU440 v4.12 | *Decision Making* | 113 | Decisión de mantener, modificar, escalar o cerrar |
| Entrega de turno | ACEM CU440 v4.12 | *Handover* | 62 | Texto de traspaso y pendientes |
| Destino del paciente | ACEM CU440 v4.12 | *Patient Disposition* | 63 | Destino y condiciones de seguridad |
| Cuidado del paciente estable; decidir con seguridad; identificar al grave | RCEM 2025 v1.5 | Learning Outcomes **1**, **2**, **3**, §3.2.1 | 17, 22, 26 | Adaptación del plan a lo observado |
| Decidir a tiempo; seguimiento hasta definir destino | Argentina 2023 | **APC #3**, **APC #8** | 16, 28 | Reevaluación de conductas ante información nueva |

## Vacíos declarados

1. **Canadá.** El PDF es un gráfico: los rótulos del eje y no se extraen como texto junto a cada
   hito. Las competencias habilitantes **1.4, 1.5, 1.6, 2.1, 2.4, 3.1, 3.3 y 3.4** sí se
   verificaron con su número y página. Los hitos de las páginas 12–14 se citan **por su texto
   verbatim y su página**, sin afirmar el número de competencia habilitante, porque no pudo
   comprobarse en el texto extraído. Las correspondencias "Medical Expert 2.2" y "2.3" que
   figuraban en la especificación inicial **no se confirmaron** y no se afirman aquí.
2. **RCEM.** Los resultados de aprendizaje se verificaron en la sección 3.2.1 numerados como
   ordinales simples (1., 2., 3., 4., 5.). La equivalencia con la numeración "SLO n" es lectura
   propia por correspondencia de enunciado, no una afirmación del documento.
3. **ACGME PC8** (*General Approach to Procedures*) se cita con cobertura **parcial**: el motor
   no ejecuta la mayoría de los procedimientos manuales del currículo.
4. **Fuentes secundarias.** Se listan como apoyo; no se extrajeron identificadores de sección
   para ellas y no sostienen ninguna fila de la matriz.
5. **Colombia y México** no se citan en ninguna fila: el material disponible no permite un
   identificador de sección verificable con el mismo estándar que las fuentes principales.

## Lo que esta matriz no demuestra

Que una conducta aparezca en cinco marcos **no** son cinco validaciones independientes. Que un
caso tenga cobertura completa **no** demuestra dificultad equivalente entre casos ni validación
psicométrica. La validación técnica de la implementación **no** equivale a validación educativa.
