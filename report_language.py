"""The language the four documents are written in, kept in one table.

Faculty decision of 2026-09-23: the documents follow the language the reader
chose. English is the default and its path is unchanged -- ``t`` returns the
source string untouched -- so this cannot alter an English document.

**What is translated is the document's own words**: its section titles, its
labels, its captions, its notices. Three things stay as they are:

  * **the resident's own words**, quoted verbatim, in whichever language they
    wrote them. Splicing a translation into somebody's quoted sentence would
    be putting words in their mouth;
  * **the model's prose**, which is generated in English by contract. A Spanish
    document therefore carries Spanish chrome and English reasoning, and says
    so on the page rather than leaving it to be noticed;
  * **the clinical identifiers** -- doses, units, drug names, times, event
    identifiers -- which are the same in both languages by design, so that a
    change of language cannot alter physiology, timing or assessment.

A missing translation falls back to English, which is the safe failure. It is
also the silent one, so ``test_the_documents_speak_the_readers_language``
walks the renderers and fails when any visible string is missing from this
table. That test is what keeps the table honest: editing an English sentence
breaks it until the Spanish is updated too.
"""

from language import DEFAULT, LANGUAGES          # noqa: F401  (re-export)


def t(text, language=None):
    """The document's own words in the reader's language."""
    if not text or language in (None, "en"):
        return text
    table = TABLES.get(language)
    if not table:
        return text
    return table.get(text, text)


def missing(strings, language="es"):
    """Which of these strings this table cannot say. Empty is good."""
    table = TABLES.get(language, {})
    return sorted({text for text in strings
                   if text and text not in table and text not in KEEP})


# Written the same in both languages, and declared here so that the guard test
# cannot be satisfied by forgetting one. Two kinds only:
#
#   * the names of the product and of its documents, which the programme uses
#     untranslated in its Spanish material as well;
#   * markup with no words of its own.
KEEP = frozenset({
    "Management Reasoning Simulator",
    "MANAGEMENT REASONING SIMULATOR",
    "Management Trace",
    "Faculty Assessment Brief",
})

ES = {
    '" color="#FFFFFF"><b>Open this encounter → review and record your assessment</b></link>':
        '" color="#FFFFFF"><b>Abrir este encuentro → revisar y registrar su evaluación</b></link>',
    '- proposed by the AI and not yet confirmed or dismissed. It carries no penalty until you decide.':
        '- propuesto por la IA y aún no confirmado ni descartado. No lleva penalización hasta que usted decida.',
    '. Full generation record, citations and rationales in the complete PDF.':
        '. El registro de generación completo, las citas y los fundamentos están en el PDF completo.',
    '. It is held for your reading because':
        '. Queda retenido para su lectura porque',
    '. No new rating was assigned and no recorded faculty judgment was changed.':
        '. No se asignó ninguna calificación nueva ni se cambió ningún juicio docente registrado.',
    '. Not ACGME Milestone levels, Canadian stages or EPA supervision levels.':
        '. No son niveles de Milestone de ACGME, etapas canadienses ni niveles de supervisión de APC.',
    '1  Read the synthesis and concerns  ·  2  Check the evidence  ·  3  Record your judgment':
        '1  Lea la síntesis y las preocupaciones  ·  2  Revise la evidencia  ·  3  Registre su juicio',
    '1 · WHAT YOU HAD OBSERVED':
        '1 · LO QUE HABÍA OBSERVADO',
    '2 · HOW YOU REASONED':
        '2 · CÓMO RAZONÓ',
    '3 · WHAT YOU ORDERED':
        '3 · LO QUE INDICÓ',
    '4 · WHAT YOU EXPECTED':
        '4 · LO QUE ESPERABA',
    '5 · WHAT WAS RECORDED NEXT':
        '5 · LO QUE SE REGISTRÓ DESPUÉS',
    '6 · NEXT MANAGEMENT ADJUSTMENT':
        '6 · SIGUIENTE AJUSTE DEL MANEJO',
    '6 · POINT TO REVISIT':
        '6 · PUNTO PARA REVISAR',
    ': requested; no result was recorded':
        ': solicitado; no se registró resultado',
    '<b>Recorded course:</b>':
        '<b>Curso registrado:</b>',
    '<font size="8" color="#607482">(composed by the application from your other words, not typed by you)</font>':
        '<font size="8" color="#607482">(compuesto por la aplicación a partir de sus otras palabras, no escrito por usted)</font>',
    'A confirmed event can both lower a domain and carry the safety penalty. That double weight is deliberate.':
        'Un evento confirmado puede bajar un dominio y además llevar la penalización de seguridad. Ese doble peso es deliberado.',
    'AI INTERPRETATION INCOMPLETE':
        'INTERPRETACIÓN DE IA INCOMPLETA',
    'AI INTERPRETATION PARTIAL':
        'INTERPRETACIÓN DE IA PARCIAL',
    'AI SUGGESTION':
        'SUGERENCIA DE IA',
    'AI SUMMARY OF YOUR LATER REFLECTION':
        'RESUMEN DE IA DE SU REFLEXIÓN POSTERIOR',
    'AI draft - faculty judgment required | Model:':
        'Borrador de IA - requiere juicio docente | Modelo:',
    'AI draft. Every suggestion in this brief stays provisional until you record your own judgment. Assistance and autonomy:':
        'Borrador de IA. Toda sugerencia de este informe es provisional hasta que usted registre su propio juicio. Asistencia y autonomía:',
    'AI interpretation':
        'Interpretación de IA',
    'AI interpretation of the trajectory':
        'Interpretación de IA de la trayectoria',
    'AI passage(s) withheld from the reading above, kept here with the reason:':
        'Pasaje(s) de IA retenidos de la lectura anterior, conservados aquí con su motivo:',
    'AI suggestion on record:':
        'Sugerencia de IA registrada:',
    'AI suggestions are provisional; documented factual corrections have been applied. Resolve the concerns on page 1 before accepting a suggestion; the rationale excerpts and evidence anchors are a reading aid.':
        'Las sugerencias de IA son provisionales; se aplicaron las correcciones factuales documentadas. Resuelva las preocupaciones de la página 1 antes de aceptar una sugerencia; los extractos de fundamento y las anclas de evidencia son una ayuda de lectura.',
    'AI synthesis of your recorded decisions and subsequent reflection. It is a learning report: it does not award a grade, establish competence or infer a cognitive bias. Every interpretation below is provisional until your faculty reviews it.':
        'Síntesis de IA de sus decisiones registradas y de su reflexión posterior. Es un informe de aprendizaje: no otorga una calificación, no establece competencia y no infiere un sesgo cognitivo. Toda interpretación de abajo es provisional hasta que su docente la revise.',
    'AI-generated decision support for faculty review':
        'Apoyo a la decisión generado por IA para revisión docente',
    'AI-generated interpretation for faculty review. Suggestions remain provisional until the faculty member reviews the evidence and records a judgment.':
        'Interpretación generada por IA para revisión docente. Las sugerencias son provisionales hasta que el docente revise la evidencia y registre un juicio.',
    'AVAILABLE AND NOT ASKED ABOUT':
        'DISPONIBLE Y NO PREGUNTADO',
    'AWAITING YOUR DECISION':
        'PENDIENTE DE SU DECISIÓN',
    'Airway and ventilation':
        'Vía aérea y ventilación',
    'Alternative action':
        'Acción alternativa',
    'Ask this rather than judge it:':
        'Pregunte esto en vez de juzgarlo:',
    'Assistance context':
        'Contexto de asistencia',
    'Available and not asked about:':
        'Disponible y no preguntado:',
    "Blue excerpts reproduce the learner's recorded words. The analysis and questions are AI interpretations to verify against the complete Management Trace.":
        'Los extractos en azul reproducen las palabras registradas del residente. El análisis y las preguntas son interpretaciones de IA que hay que verificar contra el Management Trace completo.',
    'Breathing effort':
        'Esfuerzo respiratorio',
    'COMPLETED RECORD':
        'REGISTRO COMPLETADO',
    'CRITICAL EVENTS CONFIRMED':
        'EVENTOS CRÍTICOS CONFIRMADOS',
    'Capillary refill':
        'Llene capilar',
    'Changed from the proposed':
        'Cambiado respecto de lo propuesto',
    'Clinical cue to watch':
        'Señal clínica a vigilar',
    'Competency correspondence · local simulated evidence':
        'Correspondencia de competencias · evidencia simulada local',
    'D = recorded decision and simulation time. Reflection = post-encounter evidence and does not establish what was understood during care. Suggestions add no credit and save no assessment. Encounter':
        'D = decisión registrada y tiempo de simulación. Reflexión = evidencia posterior al encuentro; no establece qué se comprendió durante la atención. Las sugerencias no otorgan crédito ni guardan evaluación. Encuentro',
    'DECISION REVIEW':
        'REVISIÓN DE DECISIONES',
    'DRAFT - REVIEW IN PROGRESS':
        'BORRADOR - REVISIÓN EN CURSO',
    'Debrief question':
        'Pregunta de debriefing',
    'Decisions worth revisiting':
        'Decisiones que vale la pena revisar',
    'ENCOUNTER ASSESSMENT SUPPORT':
        'APOYO A LA EVALUACIÓN DEL ENCUENTRO',
    'Each decision is shown as it happened: what you had observed, how you reasoned, what you ordered, what you expected, what was recorded next, and what changed after it. Your later reflection is summarised separately by the model, because it is retrospective and does not describe what you necessarily knew at the time.':
        'Cada decisión se muestra tal como ocurrió: lo que había observado, cómo razonó, lo que indicó, lo que esperaba, lo que se registró después, y qué cambió tras ella. Su reflexión posterior la resume el modelo por separado, porque es retrospectiva y no describe lo que necesariamente sabía en ese momento.',
    'Encounter revision':
        'Revisión del encuentro',
    'Evidence to discuss':
        'Evidencia para discutir',
    'Expected effect':
        'Efecto esperado',
    'FACULTY REVIEW · AI DRAFT':
        'REVISIÓN DOCENTE · BORRADOR DE IA',
    'FACULTY REVIEW • AI DRAFT':
        'REVISIÓN DOCENTE • BORRADOR DE IA',
    'Faculty Assessment Brief - concise review':
        'Faculty Assessment Brief - revisión concisa',
    'Feedback draft - editable in the app':
        'Borrador de retroalimentación - editable en la aplicación',
    'Flagged for review, carrying no deduction:':
        'Señalado para revisión, sin deducción:',
    'Focused debrief prompts':
        'Preguntas de debriefing focalizadas',
    'Generation record':
        'Registro de generación',
    'Guided - structured help directed the reasoning (faculty-reported).':
        'Guiada - una ayuda estructurada dirigió el razonamiento (informado por el docente).',
    'HISTORY OBTAINED':
        'HISTORIA OBTENIDA',
    'In the app: open this encounter, inspect the evidence, then edit and save each objective assessment.':
        'En la aplicación: abra este encuentro, revise la evidencia, y luego edite y guarde la evaluación de cada objetivo.',
    'Independent - faculty has verified no additional help.':
        'Independiente - el docente verificó que no hubo ayuda adicional.',
    'Initiate resuscitation':
        'Iniciar reanimación',
    'Insufficient evidence':
        'Evidencia insuficiente',
    'Insufficient evidence to judge':
        'Evidencia insuficiente para juzgar',
    'Interpretation limits':
        'Límites de la interpretación',
    'Justify action or observation':
        'Justificar la acción o la observación',
    'Keep alternatives open':
        'Mantener alternativas abiertas',
    'Learner report · AI interpretation · Renderer':
        'Informe del residente · interpretación de IA · Renderizador',
    'Look beyond the first finding':
        'Mirar más allá del primer hallazgo',
    'MANAGEMENT REASONING RUBRIC':
        'RÚBRICA DE RAZONAMIENTO DE MANEJO',
    'Manage resuscitation':
        'Conducir la reanimación',
    'Management Trace - learner synthesis':
        'Management Trace - síntesis del residente',
    'Needs faculty judgment':
        'Requiere juicio docente',
    'Needs improvement':
        'Requiere mejorar',
    'Next management priority':
        'Siguiente prioridad de manejo',
    'No additional evidence-supported pattern was identified.':
        'No se identificó ningún otro patrón sostenido por la evidencia.',
    'No before/after observations recorded.':
        'No se registraron observaciones antes ni después.',
    'No before/after observations were recorded.':
        'No se registraron observaciones antes ni después.',
    'No cited decision':
        'Ninguna decisión citada',
    'No executed action documented.':
        'No se documentó ninguna acción ejecutada.',
    'No expectation was recorded, so this decision has no expectation to compare.':
        'No se registró ninguna expectativa, así que esta decisión no tiene expectativa que comparar.',
    'No explicit working model, priority or rationale was recorded.':
        'No se registró explícitamente un modelo de trabajo, una prioridad ni un fundamento.',
    'No observations were recorded before this decision.':
        'No se registraron observaciones antes de esta decisión.',
    'No question was asked of the patient or the available history source during this encounter.':
        'No se hizo ninguna pregunta al paciente ni a la fuente de historia disponible durante este encuentro.',
    'No question was asked of the patient or the available history source.':
        'No se hizo ninguna pregunta al paciente ni a la fuente de historia disponible.',
    'No recorded measurements':
        'Sin mediciones registradas',
    'No recorded opportunity':
        'Sin oportunidad registrada',
    'No review points were provided. Verify the source evidence before accepting any suggestion.':
        'No se entregaron puntos de revisión. Verifique la evidencia de origen antes de aceptar cualquier sugerencia.',
    'No supporting reference selected':
        'Ninguna referencia de respaldo seleccionada',
    'No supporting references were selected. Do not infer an observed skill from absence of evidence.':
        'No se seleccionó ninguna referencia de respaldo. No infiera una habilidad observada a partir de la ausencia de evidencia.',
    'Non-executed entry':
        'Entrada no ejecutada',
    'Not assessed in this encounter':
        'No evaluado en este encuentro',
    'Not assessed in this encounter - no recorded opportunity to demonstrate it':
        'No evaluado en este encuentro - sin oportunidad registrada para demostrarlo',
    'Not known / not documented. Faculty must establish the assistance received before judging autonomy.':
        'No se sabe / no está documentado. El docente debe establecer la asistencia recibida antes de juzgar la autonomía.',
    'Not recorded.':
        'No registrado.',
    'Not yet recorded. Complete your comparison and adaptation plan in the app.':
        'Aún no registrado. Complete su comparación y su plan de adaptación en la aplicación.',
    'Observed context':
        'Contexto observado',
    'One line each; the rationale and the evidence for these are in the complete PDF and in the app. They still need your judgment to be recorded.':
        'Una línea cada uno; el fundamento y la evidencia de estos están en el PDF completo y en la aplicación. Igual necesitan que usted registre su juicio.',
    'Oxygen saturation':
        'Saturación de oxígeno',
    'PATTERNS TO PRESERVE':
        'PATRONES QUE CONVIENE CONSERVAR',
    'POCUS in management':
        'POCUS en el manejo',
    'PROVISIONAL OBJECTIVE ASSESSMENTS':
        'EVALUACIONES DE OBJETIVOS PROVISIONALES',
    'Performance synthesis':
        'Síntesis del desempeño',
    'Points are recorded observations; lines connect them and do not show continuous monitoring. Missing values interrupt the line, and each panel has its own vertical scale. The dashed marks are the minutes at which D1-D':
        'Los puntos son observaciones registradas; las líneas los unen y no representan monitorización continua. Los valores faltantes interrumpen la línea, y cada panel tiene su propia escala vertical. Las marcas punteadas son los minutos en que se tomaron D1-D',
    'Points for faculty review':
        'Puntos para revisión docente',
    'Post-encounter reflection':
        'Reflexión posterior al encuentro',
    'Procedural sedation':
        'Sedación para procedimientos',
    'Prompted - additional prompts were needed (faculty-reported).':
        'Con indicaciones - se necesitaron indicaciones adicionales (informado por el docente).',
    'Pulse present':
        'Pulso presente',
    'QUESTIONS FOR YOUR NEXT ENCOUNTER':
        'PREGUNTAS PARA SU PRÓXIMO ENCUENTRO',
    'Questions before recording':
        'Preguntas antes de registrar',
    'RATIONALE EXCERPT · EVIDENCE':
        'EXTRACTO DEL FUNDAMENTO · EVIDENCIA',
    'REVIEW COMPLETE':
        'REVISIÓN COMPLETA',
    'Read the full synthesis in the app before judging this encounter.':
        'Lea la síntesis completa en la aplicación antes de juzgar este encuentro.',
    'Read this review point in full in the app; its context cannot be safely shortened here.':
        'Lea este punto de revisión completo en la aplicación; su contexto no se puede acortar aquí sin riesgo.',
    'Reasoning during the encounter and later reflection':
        'Razonamiento durante el encuentro y reflexión posterior',
    'Reassess the handover frame':
        'Reevaluar el marco de la entrega',
    'Reassessment target and timing':
        'Objetivo y momento de la reevaluación',
    'Recognize atypical illness':
        'Reconocer la enfermedad atípica',
    'Recognize instability':
        'Reconocer la inestabilidad',
    'Reconsider the initial model':
        'Reconsiderar el modelo inicial',
    "Recorded changes do not establish a treatment's causal effect.":
        'Los cambios registrados no establecen el efecto causal de un tratamiento.',
    'Recorded decision':
        'Decisión registrada',
    'Recorded evidence to inspect':
        'Evidencia registrada para revisar',
    'Recorded learner excerpt -':
        'Extracto registrado del residente -',
    'Recorded patient trajectory':
        'Trayectoria registrada del paciente',
    'Recorded reasoning under simulation: not teamwork, hands-on airway or procedural skill, and not image acquisition. A local observation awards no Milestone level or EPA. Scope per objective and competency correspondence are in the complete PDF.':
        'Razonamiento registrado bajo simulación: no es trabajo en equipo, ni destreza manual de vía aérea o procedimiento, ni adquisición de imágenes. Una observación local no otorga ningún nivel de Milestone ni APC. El alcance por objetivo y la correspondencia de competencias están en el PDF completo.',
    'Recorded reassessment plan:':
        'Plan de reevaluación registrado:',
    'Report provenance':
        'Procedencia del informe',
    'Respiratory rate':
        'Frecuencia respiratoria',
    'Review the analysis-specific limits in the app.':
        'Revise en la aplicación los límites propios de este análisis.',
    'Review the full rationale in the app before judging this objective.':
        'Revise el fundamento completo en la aplicación antes de juzgar este objetivo.',
    "Review this decision's full debrief question in the app.":
        'Revise en la aplicación la pregunta de debriefing completa de esta decisión.',
    'Review, edit and record':
        'Revisar, editar y registrar',
    'Seek discordant evidence':
        'Buscar evidencia discordante',
    'Selected analysis limit:':
        'Límite del análisis seleccionado:',
    'Selected evidence and provisional suggestions for faculty review':
        'Evidencia seleccionada y sugerencias provisionales para revisión docente',
    'Source fingerprint:':
        'Huella de origen:',
    'Source revision:':
        'Revisión de origen:',
    'Source-bound AI interpretation of management decisions and observed patient response':
        'Interpretación de IA ligada al origen, sobre las decisiones de manejo y la respuesta observada del paciente',
    'Strengths supported by the record':
        'Fortalezas sostenidas por el registro',
    'Suggested assessments':
        'Evaluaciones sugeridas',
    'Suggested depth:':
        'Profundidad sugerida:',
    'Suggested improvement needed':
        'Se sugiere que requiere mejorar',
    'Suggested satisfactory demonstration':
        'Se sugiere demostración satisfactoria',
    'Suggested satisfactory, and settled by the record':
        'Se sugiere satisfactorio, y el registro lo resuelve',
    'Systolic pressure':
        'Presión sistólica',
    'Technical record —':
        'Registro técnico —',
    'Technical record — AI passages that stopped at the analysis length limit and were therefore not used in the reading above:':
        'Registro técnico — pasajes de IA que se detuvieron en el límite de longitud del análisis y por eso no se usaron en la lectura anterior:',
    'The AI reading of the trajectory is not shown here; it is kept in the technical record at the end with the reason.':
        'La lectura de IA de la trayectoria no se muestra aquí; queda en el registro técnico del final, con su motivo.',
    'The AI synthesis is not shown here: it was withheld, and the passage is kept in the technical record at the end with the reason. What follows is read from the record, and is not an interpretation.':
        'La síntesis de IA no se muestra aquí: fue retenida, y el pasaje queda en el registro técnico del final con su motivo. Lo que sigue se lee del registro, y no es una interpretación.',
    'The encounter in perspective':
        'El encuentro en perspectiva',
    'The history you took':
        'La historia que tomó',
    "The patient answers for the whole encounter, so these were available. Not asking is an omission of the resident's, not a limitation of the record, and it is not a reason to withhold a judgement.":
        'El paciente responde durante todo el encuentro, así que esto estaba disponible. No preguntarlo es una omisión del residente, no una limitación del registro, y no es motivo para retener un juicio.',
    'The patient answers what you ask, for the whole encounter. A topic you did not ask about was available to you: it is not missing from the record, it was not obtained.':
        'El paciente responde lo que usted le pregunte, durante todo el encuentro. Un tema que no preguntó estaba disponible para usted: no falta en el registro, no se obtuvo.',
    'The record cannot settle this:':
        'El registro no puede resolver esto:',
    'The source fingerprint binds this analysis to the frozen encounter and locked reflections. The full encounter record remains available separately.':
        'La huella de origen liga este análisis al encuentro congelado y a las reflexiones bloqueadas. El registro completo del encuentro queda disponible por separado.',
    'This brief does not save an assessment, add observations, or confirm an objective. Only the supported simulated components are considered.':
        'Este informe no guarda una evaluación, no agrega observaciones y no confirma un objetivo. Sólo se consideran los componentes simulados soportados.',
    'Threshold for changing course':
        'Umbral para cambiar de rumbo',
    'Time not recorded':
        'Hora no registrada',
    'WHAT EACH MARK WAS':
        'QUÉ FUE CADA MARCA',
    'WHAT YOU ASKED, AND WHAT YOU WERE TOLD':
        'LO QUE PREGUNTÓ, Y LO QUE LE DIJERON',
    'Weigh the current evidence':
        'Sopesar la evidencia actual',
    'What this encounter can and cannot show':
        'Lo que este encuentro puede y no puede mostrar',
    'What to carry forward':
        'Qué llevarse de aquí',
    'What you did. Why you acted. What happened next.':
        'Lo que hizo. Por qué actuó. Qué pasó después.',
    'Working model':
        'Modelo de trabajo',
    'Written by the model from what you wrote after the encounter. It is retrospective and does not establish what you understood while deciding.':
        'Escrito por el modelo a partir de lo que usted escribió después del encuentro. Es retrospectivo y no establece qué comprendía mientras decidía.',
    'Written by you after the comparison. It is your own text and is not part of the AI analysis above.':
        'Escrito por usted después de la comparación. Es su propio texto y no forma parte del análisis de IA de arriba.',
    'YOUR MANAGEMENT, RECONSTRUCTED':
        'SU MANEJO, RECONSTRUIDO',
    'Your later adaptation plan':
        'Su plan de adaptación posterior',
    'airway preparation was not marked as completed':
        'la preparación de la vía aérea no quedó marcada como completada',
    'airway_prepared remained false':
        'airway_prepared siguió en falso',
    'before the encounter closed at':
        'antes de que el encuentro cerrara a las',
    'clinical update':
        'actualización clínica',
    'decision prompts shown; full analysis contains the rest.':
        'indicaciones de decisión mostradas; el análisis completo contiene el resto.',
    'diagnostic result':
        'resultado de examen',
    'encounter record':
        'registro del encuentro',
    'factual correction(s) applied to the AI text; the stored brief keeps the original wording.':
        'corrección(es) factual(es) aplicada(s) al texto de IA; el informe guardado conserva la redacción original.',
    'factual correction(s) were applied to the AI text at render time; the saved analysis keeps the original wording.':
        'corrección(es) factual(es) aplicada(s) al texto de IA al renderizar; el análisis guardado conserva la redacción original.',
    'factual correction(s) were applied to the AI text at render time; the stored brief keeps the original wording.':
        'corrección(es) factual(es) aplicada(s) al texto de IA al renderizar; el informe guardado conserva la redacción original.',
    'in the full analysis before finalizing.':
        'en el análisis completo antes de finalizar.',
    'interpretation field(s) reached the analysis length limit and are marked where they stop.':
        'campo(s) de interpretación alcanzaron el límite de longitud del análisis y están marcados donde se detienen.',
    'no executed action recorded':
        'ninguna acción ejecutada registrada',
    'no recorded change':
        'sin cambio registrado',
    'patient history':
        'historia del paciente',
    'patient update':
        'actualización del paciente',
    'question(s) asked.':
        'pregunta(s) hecha(s).',
    'recorded decisions':
        'decisiones registradas',
    'recorded decisions between':
        'decisiones registradas entre',
    'requested at decision':
        'solicitado en la decisión',
    "review points, in the analysis's original order. Read the remaining":
        'puntos de revisión, en el orden original del análisis. Lea los restantes',
    'selected review priorities':
        'prioridades de revisión seleccionadas',
    'were taken: they show when you acted, and a change after a mark does not establish that the action caused it.':
        'fueron tomadas: muestran cuándo actuó, y un cambio posterior a una marca no establece que la acción lo haya causado.',
    'your later reflection on D':
        'su reflexión posterior sobre D',
    'your own order':
        'su propia orden',
    '| Prompt version:':
        '| Versión del prompt:',
    '| Suggested autonomy:':
        '| Autonomía sugerida:',
    '· Faculty judgment required':
        '· Requiere juicio docente',
    '· no result recorded':
        '· sin resultado registrado',
    '— withheld for':
        '— retenido por',
    '{id} · revision {n} · Faculty judgment required':
        '{id} · revisión {n} · requiere juicio docente',
    'DECISION {n} · CONTINUED':
        'DECISIÓN {n} · CONTINUACIÓN',
    'Learner report · AI interpretation · Renderer {v}':
        'Informe del residente · interpretación de IA · renderizador {v}',
}
TABLES = {"es": ES}
