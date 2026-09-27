# Descriptores de la rúbrica en español — borrador para revisión docente

> **Estado: borrador, sin aprobar.** Nada de esto se muestra en la aplicación hasta que un docente
> apruebe cada dominio en el panel de revisión. Preparado el 2026-09-27 a pedido del docente.
> Fuente única del texto: `rubric_text/es/descriptors.json` (cada frase en español va junto al
> inglés exacto que traduce).

## Qué cambia y qué no

- **Cambia sólo cómo se leen** lo que evalúa cada dominio y sus cuatro descriptores de nivel en la
  pantalla docente de la rúbrica, cuando la pantalla está en español.
- **No cambian los criterios.** El inglés de `rubric.DOMAINS` sigue siendo la rúbrica: los puntajes,
  la propuesta de la IA y su prompt, y las evaluaciones guardadas usan el inglés, apruebe o no.
- **Los PDF no imprimen descriptores**, sólo los títulos de dominio, que ya estaban en español.
- Se aprueba **dominio por dominio**. Una aprobación queda registrada con la cuenta de quien aprueba
  y nombra el texto exacto que leyó: si después cambia el español o el inglés, el dominio vuelve
  a mostrarse en inglés, completo, hasta una nueva aprobación. Ningún dominio mezcla los dos idiomas.

## Cómo revisarlo en la aplicación

1. Entra con una cuenta docente o de administración y abre el panel docente.
2. Abre **«Rubric descriptors in Spanish (faculty review) · Descriptores de la rúbrica en español»**.
3. Elige un dominio. Verás cada frase en inglés y en español, lado a lado.
4. **Aprobar** lo deja en uso desde la siguiente carga de página (a lo más dos minutos).
   **Pedir cambios** exige una nota que diga qué corregir; el dominio sigue en inglés.

Si pides cambios, corrijo el borrador con tu nota y el dominio vuelve a quedar pendiente de revisión.

## Decisiones de traducción que conviene mirar

1. **«prompt» → «indicación»** (D1, nivel 1: «necesita una indicación correctiva sustancial»).
   Coincide con la autonomía «Con indicaciones» y con `docs/OBJECTIVE_TRACKING.md` («requirió
   indicaciones»). Riesgo: en Chile «indicaciones» también son las órdenes médicas. Alternativas:
   «orientación», «pista».
2. **«Orders» → «Ordena»** (D3, niveles 0 y 2). Es la forma que ya citan
   `docs/EJEMPLO_RUBRICA.md` y `docs/RUBRICA_PILOTO_CORRIDAS.md` («ordena algo claramente peligroso
   en este contexto»). Alternativa: «Indica».
3. **«relevant»**: «pertinente» cuando califica información o alternativas (D2); «relevante» cuando
   habla de importancia clínica (D1 nivel 0, D3 nivel 1).
4. **«delivery» → «ejecución»** (D4), como en la matriz de trazabilidad («Comprobación de ejecución
   y de resultado»). Alternativa: «administración», que sólo cubre fármacos.
5. **«targets» → «metas»** (D4, nivel 3). La aplicación también llama «metas» a las metas de
   observación del programa. Alternativa: «objetivos terapéuticos».
6. **«treatment failure» → «falla del tratamiento»** (D4 nivel 3; D5 nivel 3: «ante una falla»).
   Alternativa: «fracaso terapéutico».
7. **«handover» → «traspaso»** y **«loose ends» → «pendientes»** (D5, nivel 3), como en la matriz
   («Texto de traspaso y pendientes»). Alternativa: «entrega de turno».
8. **«escalation» → «escalamiento»** (D5, nivel 3).
9. **«Also…» del nivel 3 → «Además, …»**: el nivel 3 incluye lo del nivel 2.
10. **«Misses» → «Pasa por alto»** (D1, nivel 0).
11. **«the course» → «la evolución»** y **«continuity» → «continuidad»** (D5), como en el título
    «Adaptación y continuidad del manejo».
12. **«Whether…» → «Si…»**, repetido antes de cada condición para que se lea cada una por separado.

## D1 · Reconocimiento de gravedad y priorización

*Recognition of severity and prioritisation*

| | Inglés (criterio vigente) | Español (borrador) |
|---|---|---|
| **Qué evalúa** | Whether the threats were identified, what had to come first was decided, and the urgency of the action matched the threat. | Si se identificaron las amenazas, si se decidió qué debía hacerse primero y si la urgencia de la acción correspondió a la amenaza. |
| **Nivel 0** | Misses an observable threat, or delays an essential action in a way that matters clinically. | Pasa por alto una amenaza observable, o retrasa una acción esencial de un modo clínicamente relevante. |
| **Nivel 1** | Recognises the problem but orders the priorities wrongly, or needs a substantial corrective prompt. | Reconoce el problema, pero ordena mal las prioridades, o necesita una indicación correctiva sustancial. |
| **Nivel 2** | Recognises the threats and prioritises timely actions. | Reconoce las amenazas y prioriza acciones oportunas. |
| **Nivel 3** | Also anticipates plausible deterioration and arranges contingencies without delaying what is essential. | Además, anticipa un deterioro plausible y prepara contingencias sin retrasar lo esencial. |

## D2 · Evaluación e interpretación clínica

*Clinical assessment and interpretation*

| | Inglés (criterio vigente) | Español (borrador) |
|---|---|---|
| **Qué evalúa** | Whether relevant information was obtained and interpreted, and an explanation was built that guides decisions. | Si se obtuvo e interpretó información pertinente, y si se construyó una explicación que guíe las decisiones. |
| **Nivel 0** | Omits or misinterprets essential information, compromising management. | Omite o interpreta mal información esencial, lo que compromete el manejo. |
| **Nivel 1** | Assessment incomplete or poorly directed; findings only partly integrated. | Evaluación incompleta o mal dirigida; hallazgos integrados sólo en parte. |
| **Nivel 2** | Obtains and interprets relevant information and considers relevant alternatives. | Obtiene e interpreta información pertinente y considera alternativas pertinentes. |
| **Nivel 3** | Also integrates uncertainty and discordant data, and selects further information for its capacity to change management. | Además, integra la incertidumbre y los datos discordantes, y selecciona información adicional por su capacidad de cambiar el manejo. |

## D3 · Selección y ejecución de un manejo seguro

*Selection and delivery of safe management*

| | Inglés (criterio vigente) | Español (borrador) |
|---|---|---|
| **Qué evalúa** | Whether the interventions were appropriate, specified enough to be carried out, and weighed against risk, contraindications and this patient's needs. | Si las intervenciones fueron apropiadas, si estaban especificadas lo suficiente para poder ejecutarse y si se sopesaron frente al riesgo, las contraindicaciones y las necesidades de este paciente. |
| **Nivel 0** | Omits an essential intervention, or orders something clearly dangerous in this context. | Omite una intervención esencial, u ordena algo claramente peligroso en este contexto. |
| **Nivel 1** | Partly appropriate management, with relevant omissions or insufficient specification. | Manejo apropiado sólo en parte, con omisiones relevantes o especificación insuficiente. |
| **Nivel 2** | Orders appropriate management, sufficiently specified and safe. | Ordena un manejo apropiado, suficientemente especificado y seguro. |
| **Nivel 3** | Also individualises the management, anticipates adverse effects and coordinates the complementary measures that belong with it. | Además, individualiza el manejo, anticipa efectos adversos y coordina las medidas complementarias que le corresponden. |

## D4 · Seguimiento y reevaluación

*Monitoring and reassessment*

| | Inglés (criterio vigente) | Español (borrador) |
|---|---|---|
| **Qué evalúa** | Whether what to watch was defined, delivery and response were checked, and reassessment happened within an appropriate interval. | Si se definió qué vigilar, si se comprobaron la ejecución y la respuesta, y si la reevaluación ocurrió en un intervalo apropiado. |
| **Nivel 0** | Does not check the response or reassess, though there was both need and opportunity. | No comprueba la respuesta ni reevalúa, aunque había necesidad y oportunidad. |
| **Nivel 1** | Reassessment late, incomplete, or unrelated to what had to be watched. | Reevaluación tardía, incompleta o sin relación con lo que había que vigilar. |
| **Nivel 2** | Checks delivery and response with appropriate variables and intervals. | Comprueba la ejecución y la respuesta con variables e intervalos apropiados. |
| **Nivel 3** | Also sets targets and alarm thresholds, and actively looks for treatment failure or complications. | Además, fija metas y umbrales de alarma, y busca activamente la falla del tratamiento o las complicaciones. |

## D5 · Adaptación y continuidad del manejo

*Adaptation and continuity of management*

| | Inglés (criterio vigente) | Español (borrador) |
|---|---|---|
| **Qué evalúa** | Whether the course was integrated, the plan changed or justifiably kept, support requested, and a safe continuity defined. | Si se integró la evolución, si el plan se cambió o se mantuvo de forma justificada, si se pidió apoyo y si se definió una continuidad segura. |
| **Nivel 0** | Persists with an inadequate plan despite the available evidence, or proposes an unsafe continuity. | Persiste en un plan inadecuado pese a la evidencia disponible, o propone una continuidad insegura. |
| **Nivel 1** | Recognises the course but adjusts incompletely or late. | Reconoce la evolución, pero ajusta de forma incompleta o tardía. |
| **Nivel 2** | Updates or justifiably keeps the plan and defines the next safe step. | Actualiza el plan o lo mantiene de forma justificada, y define el siguiente paso seguro. |
| **Nivel 3** | Also sets alternatives for failure, timely escalation, and a handover or follow-up with its loose ends stated. | Además, define alternativas ante una falla, un escalamiento oportuno y un traspaso o seguimiento con sus pendientes explícitos. |

## Ya en pantalla: profundidad y autonomía de las observaciones por objetivo

Estas descripciones aparecen como ayuda en el formulario de progreso por objetivo. Ya estaban en
español en `docs/OBJECTIVE_TRACKING.md`, así que se muestran en pantalla desde la traducción de los
portales docentes, ahora con esa misma redacción. Si quieres cambiar alguna, dímelo y la corrijo.

| Etiqueta | Inglés | Español en pantalla |
|---|---|---|
| Profundidad · Básica | A focused management decision with explicit supporting evidence. | Una decisión de manejo focalizada, con evidencia de apoyo explícita. |
| Profundidad · Integrada | Related decisions integrating response, reassessment, and competing priorities. | Decisiones relacionadas que integran respuesta, reevaluación y prioridades en competencia. |
| Profundidad · Compleja | Management reasoning under uncertainty or evolving, competing clinical problems. | Razonamiento de manejo frente a incertidumbre o a problemas clínicos que evolucionan y compiten. |
| Autonomía · Guiada | Faculty or structured guidance directed the management reasoning. | Un docente o una guía estructurada dirigió el razonamiento de manejo. |
| Autonomía · Con indicaciones | Prompts were needed before the resident completed the reasoning. | Se necesitaron indicaciones antes de que el residente completara el razonamiento. |
| Autonomía · Independiente | The observed reasoning was completed without additional guidance or prompts. | El razonamiento observado se completó sin guía ni indicaciones adicionales. |

## Sigue en inglés

- **Los eventos críticos de cada caso** («Se activa cuando», «Alternativas aceptables», «No cuenta
  cuando»). Son declaraciones de evaluación propias de cada caso; traducirlas sería otra revisión.
- **La nota que separa D4 de D5** (`rubric.SEPARATION_NOTE`). Sólo va en el prompt de la IA y no se
  muestra en pantalla. Su sentido ya está en español en `docs/RUBRICA_MANAGEMENT_REASONING_v1.0.md`.
