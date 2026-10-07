# B-5 · Rúbrica en español · Lote RUB (D1–D5)

> **DECIDIDO por la docencia el 2026-10-07: D1 a D5, 5 de 5. Nada implementado.** Segundo lote de la revisión (`docs/revision/B5_REVISION_RELATO_Y_RUBRICA.md`,
> aprobado el 2026-10-07). Una decisión por dominio. Cada decisión ata la versión exacta del texto que se presenta: el
> hash de sus descriptores en los dos idiomas (`rubric_text.version`). No se crean aprobaciones ni se toca
> `rubric_text/es`.
>
> 2026-10-07 · rama `clinical-encounter-v0.13` · inglés de `rubric.DOMAINS`, borrador de
> `rubric_text/es/descriptors.json`, leídos sin cambiar nada.

**En una mirada**

- **Decidido (docente, 2026-10-07):** D1, D2 y D3, APPROVE AS IS; D4, APPROVE AS IS con R-1 (versión `041597d9…`); D5, APPROVE
  de la opción (b), «…un traspaso de la atención o un control posterior que explicite los asuntos pendientes.»
  (versión `52958f1c…`). Sin cambios en los niveles 0–3, el puntaje, la estructura de dominios ni la rúbrica en
  inglés. Sin aprobaciones creadas y sin cambios en `rubric_text/es`.
- **Estructura:** 5 dominios. Cada uno tiene «qué evalúa» y los niveles 0 a 3: 25 descriptores. El inglés del borrador
  coincide con el inglés vigente en los 5 (`rubric_text.current`). Nada cambia en los niveles, el puntaje ni la
  estructura.
- **Se aplica R-1 (aprobada):** «revisar» para «check» y «vigilar» sólo para «watch». Cambian 3 descriptores de D4,
  mostrados abajo con su texto anterior.
- **Recomendación:**
  - D1, D2, D3 y D4: **APPROVE AS IS**;
  - D5: **REVIEW CLOSELY**. En español, «seguimiento» nombra hoy el D4 («Seguimiento y reevaluación») y también el
    «follow-up» del nivel 3 de D5. Eso puede mezclar dos dominios que la docencia pidió separar (2026-09-27).
- **Conflicto con X-1:** ninguno después de R-1.
- **Texto activo (fuera de la compuerta de aprobación):** los títulos, los rótulos cortos del radar y la nota que
  separa D4 y D5 en el portal docente. Se muestran con su dominio para ver que son coherentes. La aprobación de un
  dominio no los cambia.
- **Criterio de la propuesta de la IA:** sigue en inglés por diseño (`rubric_text`). El español es cómo se lee en
  pantalla y no cambia el puntaje.

## D1 · Reconocimiento de gravedad y priorización

| Qué | EN | ES |
|---|---|---|
| Título (activo) | Recognition of severity and prioritisation | Reconocimiento de gravedad y priorización |
| Rótulo del radar (activo) | Severity | Gravedad |
| Qué evalúa | Whether the threats were identified, what had to come first was decided, and the urgency of the action matched the threat. | Si se identificaron las amenazas, si se decidió qué debía hacerse primero y si la urgencia de la acción correspondió a la amenaza. |
| 0 | Misses an observable threat, or delays an essential action in a way that matters clinically. | Pasa por alto una amenaza observable, o retrasa una acción esencial de un modo clínicamente relevante. |
| 1 | Recognises the problem but orders the priorities wrongly, or needs a substantial corrective prompt. | Reconoce el problema, pero ordena mal las prioridades, o requiere orientación correctiva importante. |
| 2 | Recognises the threats and prioritises timely actions. | Reconoce las amenazas y prioriza acciones oportunas. |
| 3 | Also anticipates plausible deterioration and arranges contingencies without delaying what is essential. | Además, anticipa un deterioro plausible y prepara planes de contingencia sin retrasar lo esencial. |

- **Otro texto del dominio:** ninguno.
- **Terminología que cruza X-1:** «qué debía hacerse primero» frente a «qué problema estás abordando primero» (G-03)
  y «Primero abordo…» (L-03). Es el mismo constructo, la prioridad, dicho desde la evaluación; concuerda.
- **Diferencias de sentido entre EN y ES:** ninguna que cambie la evaluación.
- **Recomendación:** **APPROVE AS IS**.
- **Decisión docente (D1, versión `552618f3085a42ae3d6e13d8be3338a60ce3fb713f1a223eb74825e505fe1369`):** ☒ **APPROVE AS IS** — docente, 2026-10-07.

## D2 · Evaluación e interpretación clínica

| Qué | EN | ES |
|---|---|---|
| Título (activo) | Clinical assessment and interpretation | Evaluación e interpretación clínica |
| Rótulo del radar (activo) | Assessment | Evaluación |
| Qué evalúa | Whether relevant information was obtained and interpreted, and an explanation was built that guides decisions. | Si se obtuvo e interpretó información pertinente, y si se construyó una explicación que guíe las decisiones. |
| 0 | Omits or misinterprets essential information, compromising management. | Omite o interpreta mal información esencial, lo que compromete el manejo. |
| 1 | Assessment incomplete or poorly directed; findings only partly integrated. | Evaluación incompleta o mal dirigida; hallazgos integrados sólo en parte. |
| 2 | Obtains and interprets relevant information and considers relevant alternatives. | Obtiene e interpreta información pertinente y considera alternativas pertinentes. |
| 3 | Also integrates uncertainty and discordant data, and selects further information for its capacity to change management. | Además, integra la incertidumbre y los datos discordantes, y selecciona información adicional por su capacidad de cambiar el manejo. |

- **Otro texto del dominio:** ninguno.
- **Terminología que cruza X-1:** «una explicación que guíe las decisiones» frente a «qué crees que está pasando»
  (G-03) y «Creo que…» (L-03). Es el mismo constructo, el modelo de trabajo; concuerda.
- **Diferencias de sentido entre EN y ES:** ninguna que cambie la evaluación.
- **Recomendación:** **APPROVE AS IS**.
- **Decisión docente (D2, versión `0393ca0dd6717a6a54b649541e7f140c1d0dd822cbf8e98e205f8456df6763c4`):** ☒ **APPROVE AS IS** — docente, 2026-10-07.

## D3 · Selección y ejecución de un manejo seguro

| Qué | EN | ES |
|---|---|---|
| Título (activo) | Selection and delivery of safe management | Selección y ejecución de un manejo seguro |
| Rótulo del radar (activo) | Management | Manejo |
| Qué evalúa | Whether the interventions were appropriate, specified enough to be carried out, and weighed against risk, contraindications and this patient's needs. | Si las intervenciones fueron apropiadas, si estaban especificadas lo suficiente para poder ejecutarse y si se sopesaron frente al riesgo, las contraindicaciones y las necesidades de este paciente. |
| 0 | Omits an essential intervention, or orders something clearly dangerous in this context. | Omite una intervención esencial, u ordena algo claramente peligroso en este contexto. |
| 1 | Partly appropriate management, with relevant omissions or insufficient specification. | Manejo apropiado sólo en parte, con omisiones relevantes o especificación insuficiente. |
| 2 | Orders appropriate management, sufficiently specified and safe. | Indica un manejo apropiado, suficientemente especificado y seguro. |
| 3 | Also individualises the management, anticipates adverse effects and coordinates the complementary measures that belong with it. | Además, individualiza el manejo, anticipa efectos adversos y coordina las medidas complementarias que le corresponden. |

- **Otro texto del dominio:** ninguno.
- **Terminología que cruza X-1:** «especificadas lo suficiente para poder ejecutarse» e «Indica un manejo» frente a las
  aclaraciones aprobadas («Indica …», «Aclara la orden») y a la pestaña «Indicaciones». Concuerda.
- **Diferencias de sentido entre EN y ES:** ninguna que cambie la evaluación.
- **Recomendación:** **APPROVE AS IS**.
- **Decisión docente (D3, versión `bf7395c34d28bce676adfc5bad71f5a6d4a1dbdced9952c64dda64f52284a191`):** ☒ **APPROVE AS IS** — docente, 2026-10-07.

## D4 · Seguimiento y reevaluación

| Qué | EN | ES propuesto (con R-1) |
|---|---|---|
| Título (activo) | Monitoring and reassessment | Seguimiento y reevaluación |
| Rótulo del radar (activo) | Follow-up | Seguimiento |
| Qué evalúa | Whether what to watch was defined, delivery and response were checked, and reassessment happened within an appropriate interval. | Si se definió qué vigilar, si se **revisaron** la ejecución y la respuesta, y si la reevaluación ocurrió en un intervalo apropiado. |
| 0 | Does not check the response or reassess, though there was both need and opportunity. | No **revisa** la respuesta ni reevalúa, aunque había necesidad y oportunidad. |
| 1 | Reassessment late, incomplete, or unrelated to what had to be watched. | Reevaluación tardía, incompleta o sin relación con lo que había que vigilar. |
| 2 | Checks delivery and response with appropriate variables and intervals. | **Revisa** la ejecución y la respuesta con variables e intervalos apropiados. |
| 3 | Also sets targets and alarm thresholds, and actively looks for treatment failure or complications. | Además, establece objetivos clínicos y umbrales de alarma, y busca activamente signos de fracaso terapéutico o complicaciones. |

- **Qué cambia R-1 respecto del borrador:**
  - «Qué evalúa»: «se comprobaron» → «se revisaron»;
  - nivel 0: «No comprueba» → «No revisa»;
  - nivel 2: «Comprueba» → «Revisa»;
  - «vigilar» se mantiene para «watch» (en «qué evalúa» y en el nivel 1).
- **Otro texto del dominio:**
  - la nota del portal docente que separa D4 y D5 (activa, y una prueba la fija, `test_rubric_text.py:183`): «D4
    evalúa monitorización y reevaluación; D5 evalúa cómo se utiliza esa información para adaptar o mantener
    justificadamente el manejo y asegurar su continuidad.»;
  - el criterio para la IA (`rubric.SEPARATION_NOTE`) sigue en inglés por diseño.
- **Terminología que cruza X-1:**
  - «revisar», con R-1, frente a «qué vas a revisar» y «cuándo lo vas a revisar» (G-03, G-13): el mismo verbo para el
    mismo acto;
  - «reevaluación» y «reevalúa», como «una reevaluación» (X1-C16) y «Reevalúo … en … minutos» (L-03);
  - «objetivos clínicos y umbrales de alarma» frente a «qué esperas que ocurra» (G-03): concuerda.
- **Diferencias de sentido entre EN y ES:** ninguna que cambie la evaluación.
  - El nivel 3 hace explícitos «objetivos clínicos» y «signos de», que no cambian el sentido.
  - El título y el radar dicen «Seguimiento» para «Monitoring». Ver D5.
- **Recomendación:** **APPROVE AS IS**, con R-1 ya aplicada en el texto propuesto.
- **Decisión docente (D4, versión con R-1 `041597d975468e31bdf8d6c1d1ddd35e289b98fa05b5e8d3b9106db0c36e2dad`):**
  ☒ **APPROVE AS IS con R-1** — docente, 2026-10-07: «revisar» para «check» y «vigilar» para «watch».

## D5 · Adaptación y continuidad del manejo

| Qué | EN | ES |
|---|---|---|
| Título (activo) | Adaptation and continuity of management | Adaptación y continuidad del manejo |
| Rótulo del radar (activo) | Continuity | Continuidad |
| Qué evalúa | Whether the course was integrated, the plan changed or justifiably kept, support requested, and a safe continuity defined. | Si se integró la evolución, si el plan se cambió o se mantuvo de forma justificada, si se pidió apoyo y si se definió una continuidad segura. |
| 0 | Persists with an inadequate plan despite the available evidence, or proposes an unsafe continuity. | Persiste en un plan inadecuado pese a la evidencia disponible, o propone una continuidad insegura. |
| 1 | Recognises the course but adjusts incompletely or late. | Reconoce la evolución, pero ajusta de forma incompleta o tardía. |
| 2 | Updates or justifiably keeps the plan and defines the next safe step. | Actualiza el plan o lo mantiene de forma justificada, y define el siguiente paso seguro. |
| 3 | Also sets alternatives for failure, timely escalation, and a handover or follow-up with its loose ends stated. | Además, define alternativas ante una falla, un escalamiento oportuno y un traspaso de la atención o un **seguimiento** que explicite los asuntos pendientes. |

- **Otro texto del dominio:** comparte con D4 la nota del portal que los separa (arriba).
- **Terminología que cruza X-1:** «evolución», como la pestaña «Evolución» de la sala; «ajusta», como «iniciar,
  ajustar, continuar o suspender» (X1-C19). Concuerda.
- **Lo que podría cambiar la evaluación: «seguimiento» en dos dominios.**
  - En el nivel 3, «seguimiento» traduce «follow-up»: la continuidad después del encuentro, que es de D5.
  - El título y el radar de D4 usan «Seguimiento» para «Monitoring», que es de D4.
  - Quien puntúa en español puede atribuir a D4 un plan de seguimiento que corresponde a D5. Es la confusión que
    la nota del portal busca evitar (2026-09-27).
  - En inglés, las palabras son distintas en los descriptores, aunque el rótulo inglés del radar de D4 también dice
    «Follow-up».
- **Opciones:**
  - (a) dejar el texto como está;
  - (b) sólo en el nivel 3 de D5, «un control posterior» en vez de «un seguimiento»: «…un traspaso de la atención o
    un control posterior que explicite los asuntos pendientes». No toca el título, el radar ni la nota, que están
    activos.
- **Recomendación:** **REVIEW CLOSELY**, y entre las opciones, la (b): cambia una palabra dentro de la unidad que se
  aprueba y deja «seguimiento» sólo en D4.
- **Decisión docente (D5):** ☐ APPROVE (a), versión `a87a1655f6611fbc3c55ee298447710c8343a3e0f42d2019d27539b99b989137` ·
  ☒ **APPROVE (b)**, versión `52958f1cdcd83dc9e7f4535c9ae65862f0f4ab829d230ac4bd8eff617abbdac4` — docente, 2026-10-07. En el nivel 3,
  «…un traspaso de la atención o un control posterior que explicite los asuntos pendientes.». No se usa
  «seguimiento» para «follow-up», porque D4 ya usa «Seguimiento» para «Monitoring», y la distinción entre D4 y D5
  tiene que quedar clara.

## Resumen del lote RUB

| Dominio | Recomendación | Versión que ata la aprobación | Decisión docente |
|---|---|---|---|
| D1 | APPROVE AS IS | `552618f3…` (tal cual) | ☒ APPROVE |
| D2 | APPROVE AS IS | `0393ca0d…` (tal cual) | ☒ APPROVE |
| D3 | APPROVE AS IS | `bf7395c3…` (tal cual) | ☒ APPROVE |
| D4 | APPROVE AS IS, con R-1 | `041597d9…` (con R-1; el borrador actual es `8591b254…`) | ☒ APPROVE, con R-1 |
| D5 | REVIEW CLOSELY; recomendada (b) | `52958f1c…` (b) | ☒ APPROVE (b) |

- **Decisiones que pide el lote:** 5, una por dominio.
- **Después, al implementar (no autorizado):**
  - `rubric_text/es/descriptors.json` recibe el texto aprobado, y su hash tiene que coincidir con la versión aprobada
    de cada dominio;
  - las aprobaciones `{domain_id, version, decision}` se generan de forma determinista, sin nombres;
  - antes de congelar el candidato, se identifica y se prueba el camino de activación que ya usa la app
    (`rubric_text.pack_approvals` y `rubric_text.status`).

Siguiente lote, según el orden docente: R1 (síndrome coronario agudo), dividido en R1A y R1B (`docs/revision/B5_RELATO_R1A.md`).
