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
    'not present':
        'no presente',
    'changing':
        'en cambio',
    'uncertain':
        'incierto',
    'The resident set these against one another.':
        'El residente los contrastó entre sí.',
    "some read by a model":
        "algunos leídos por un modelo",
    'Findings mentioned':
        'Hallazgos mencionados',
    'Link expressed':
        'Relación expresada',
    'these findings were given as the reason: "{marker}"':
        'esos hallazgos se dieron como la razón: «{marker}»',
    'Link to the interpretation: not stated.':
        'Relación con la interpretación: no explicitada.',
    'Findings mentioned: not stated.':
        'Hallazgos mencionados: no explicitados.',
    'stated earlier, in decision {n} at {minute:g} min':
        'enunciado antes, en la decisión {n} al minuto {minute:g}',
    'stated in this entry':
        'enunciado en esta entrada',
    'shared with the plan of an earlier decision': 'compartido con el plan de una decisión anterior',
    'explained afterwards, as a retrospective': 'explicado después, como retrospectiva',
    'shared with the plan of decision {n} at {minute:g} min': 'compartido con el plan de la decisión {n}, a los {minute:g} min',
    'stated earlier in this encounter':
        'enunciado antes en este encuentro',
    'completed in the follow-up':
        'completado en el formulario',
    'composed by the application from your other words':
        'compuesto por la aplicación a partir de sus otras palabras',
    'Working model':
        'Modelo de trabajo',
    'Priority':
        'Prioridad',
    'Rationale':
        'Fundamento',
    'Preserve':
        'Preservar',
    "Not stated before this order: {elements}.":
        "No se enunció antes de esta orden: {elements}.",
    "which problem was being addressed first":
        "qué problema se estaba abordando primero",
    "when the reassessment would happen":
        "cuándo ocurriría la reevaluación",
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
    'ENGINE CONVENTIONS THIS ENCOUNTER TOUCHED':
        'CONVENCIONES DEL MOTOR QUE ESTE ENCUENTRO TOCÓ',
    'These outputs follow engine conventions the faculty has not yet decided (docs/PESOS_CASOS.md, section 4). They bound those specific observations only: do not ground a deficiency on one of them alone. Everything else in the encounter is evaluated as usual.':
        'Estas salidas siguen convenciones del motor que la facultad aún no decide (docs/PESOS_CASOS.md, sección 4). Acotan sólo esas observaciones específicas: no funde una deficiencia únicamente en una de ellas. Todo lo demás del encuentro se evalúa como siempre.',
    'Pending: {decision}.':
        'Pendiente: {decision}.',
    'Rests on it: {depends}':
        'Descansa en ella: {depends}',
    'Weight type per drug and indication (decisions C and E)':
        'Tipo de peso por fármaco e indicación (decisiones C y E)',
    'Infusion weight basis and effect reference (decision E)':
        'Peso de las infusiones y referencia de su efecto (decisión E)',
    'Neuromuscular blocker dosing weight (decision C)':
        'Peso de dosificación del bloqueante neuromuscular (decisión C)',
    'Required minute ventilation and default tidal volume (section 4)':
        'Ventilación minuto requerida y volumen corriente por defecto (sección 4)',
    'Baseline urine output and residual renal function (decision D)':
        'Diuresis basal y función renal residual (decisión D)',
    'Baseline urine output weight basis (decision D)':
        'Base de peso de la diuresis basal (decisión D)',
    'The executed dose, and what followed from it.':
        'La dosis ejecutada, y lo que siguió de ella.',
    'The pressure and heart-rate response recorded after these rates.':
        'La respuesta de presión y frecuencia registrada tras esas tasas.',
    'How long paralysis lasted, and any decision timed against it.':
        'Cuánto duró la parálisis, y toda decisión medida contra ella.',
    'The PaCO2 and pH trajectory on the ventilator.':
        'La trayectoria de PaCO2 y pH en el ventilador.',
    'The measured urine output, and the response to the diuretic.':
        'La diuresis medida, y la respuesta al diurético.',
    'The measured urine output before and after the diuretic.':
        'La diuresis medida antes y después del diurético.',
    'The gases follow a required minute ventilation and a default tidal volume calibrated at 70 kg, while a tidal volume per kilogram uses the predicted body weight (decision B).':
        'Los gases siguen una ventilación minuto requerida y un volumen corriente por defecto calibrados a 70 kg, mientras un volumen por kilo usa el peso corporal predicho (decisión B).',
    'This case declares minimal residual renal function; the exact residual baseline the model ran on is a simulator convention pending that decision.':
        'Este caso declara una función renal residual mínima; la basal residual exacta con la que corrió el modelo es una convención del simulador pendiente de esa decisión.',
    'The baseline urine output is calibrated at 70 kg whatever the chart weighs, pending the faculty\'s basis for it.':
        'La diuresis basal está calibrada a 70 kg pese lo que pese la ficha, pendiente de la base que la facultad decida.',
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
    'Information obtained':
        'Información obtenida',
    'Autonomy not determined: requires faculty confirmation':
        'Autonomía no determinada: requiere confirmación docente',
    'No external help': 'Sin ayuda externa',
    'External help received': 'Con ayuda externa',
    'Not reported': 'No informado',
    '(declared by the resident)': '(declaración de la persona residente)',
    '(declared by faculty)': '(declaración docente)',
    '(declared by an administrator)': '(declaración de administración)',
    '(declared)': '(declarado)',
    '(nobody has declared it)': '(nadie lo ha declarado)',
    'Synthetic test: automated run without external assistance':
        'Prueba sintética: ejecución automatizada sin asistencia externa',
    'An autonomy the record cannot establish is left for faculty confirmation.':
        'Una autonomía que el registro no permite establecer queda para confirmación docente.',
    'not modelled in this version of the simulator':
        'no modelado en esta versión del simulador',
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
    ', and {n} more':
        ', y {n} más',
    '3 of {n} decision prompts shown; full analysis contains the rest.':
        '3 de {n} indicaciones de decisión mostradas; el análisis completo contiene el resto.',
    'AI draft - faculty judgment required | Model: {model} | Generated: {when}\nEncounter revision {revision} | Source: {source}':
        'Borrador de IA - requiere juicio docente | Modelo: {model} | Generado: {when}\nRevisión del encuentro {revision} | Origen: {source}',
    'Changed from the proposed {score}:':
        'Cambiado respecto de lo propuesto ({score}):',
    'D = recorded decision and simulation time. Reflection = post-encounter evidence and does not establish what was understood during care. Suggestions add no credit and save no assessment. Encounter {encounter} · revision {revision} · {model}. Full generation record, citations and rationales in the complete PDF.':
        'D = decisión registrada y tiempo de simulación. Reflexión = evidencia posterior al encuentro; no establece qué se comprendió durante la atención. Las sugerencias no otorgan crédito ni guardan evaluación. Encuentro {encounter} · revisión {revision} · {model}. El registro de generación completo, las citas y los fundamentos están en el PDF completo.',
    'Encounter: {encounter}\nAttempt ID: {attempt}\nSource revision: {revision} | Schema: {schema} | Prompt version: {prompt}':
        'Encuentro: {encounter}\nIdentificador del intento: {attempt}\nRevisión de origen: {revision} | Esquema: {schema} | Versión del prompt: {prompt}',
    'Encounter: {encounter} | Generated: {when} | Model: {model}\nAnalysis: {schema} | Prompt: {prompt} | Renderer: {renderer}\nSource fingerprint: {fingerprint}\nThe source fingerprint binds this analysis to the frozen encounter and locked reflections. The full encounter record remains available separately.':
        'Encuentro: {encounter} | Generado: {when} | Modelo: {model}\nAnálisis: {schema} | Prompt: {prompt} | Renderizador: {renderer}\nHuella de origen: {fingerprint}\nLa huella de origen liga este análisis al encuentro congelado y a las reflexiones bloqueadas. El registro completo del encuentro queda disponible por separado.',
    "First 3 of {total} review points, in the analysis's original order. Read the remaining {rest} in the full analysis before finalizing.":
        'Los primeros 3 de {total} puntos de revisión, en el orden original del análisis. Lea los {rest} restantes en el análisis completo antes de finalizar.',
    'Flagged for review, carrying no deduction: {concern}':
        'Señalado para revisión, sin deducción: {concern}',
    'Recorded learner excerpt - {label}: {excerpt}':
        'Extracto registrado del residente - {label}: {excerpt}',
    'Suggested depth: {depth} | Suggested autonomy: {autonomy}':
        'Profundidad sugerida: {depth} | Autonomía sugerida: {autonomy}',
    'Technical record — {n} AI passage(s) withheld from the reading above, kept here with the reason:':
        'Registro técnico — {n} pasaje(s) de IA retenidos de la lectura anterior, conservados aquí con su motivo:',
    'before the encounter closed at {n:g} min':
        ' antes de que el encuentro cerrara a los {n:g} min',
    'reported at {n:g} min':
        'informado a los {n:g} min',
    'requested at decision {n}':
        'solicitado en la decisión {n}',
    'result at {n:g} min':
        'resultado a los {n:g} min',
    'sampled at {n:g} min':
        'muestra tomada a los {n:g} min',
    'your later reflection on D{n}':
        'su reflexión posterior sobre D{n}',
    '{event} - proposed by the AI and not yet confirmed or dismissed. It carries no penalty until you decide.':
        '{event} - propuesto por la IA y aún no confirmado ni descartado. No lleva penalización hasta que usted decida.',
    '{n} factual correction(s) applied to the AI text; the stored brief keeps the original wording.':
        '{n} corrección(es) factual(es) aplicada(s) al texto de IA; el informe guardado conserva la redacción original.',
    '{n} factual correction(s) were applied to the AI text at render time; the saved analysis keeps the original wording.':
        '{n} corrección(es) factual(es) aplicada(s) al texto de IA al renderizar; el análisis guardado conserva la redacción original.',
    '{n} factual correction(s) were applied to the AI text at render time; the stored brief keeps the original wording.':
        '{n} corrección(es) factual(es) aplicada(s) al texto de IA al renderizar; el informe guardado conserva la redacción original.',
    '{n} interpretation field(s) reached the analysis length limit and are marked where they stop.':
        '{n} campo(s) de interpretación alcanzaron el límite de longitud del análisis y están marcados donde se detienen.',
    '{n} question(s) asked.':
        '{n} pregunta(s) hecha(s).',
    '{n} recorded decisions':
        '{n} decisiones registradas',
    '{n} recorded decisions between {start:g} and {finish:g} min':
        '{n} decisiones registradas entre los {start:g} y los {finish:g} min',
    '{n} selected review priorities':
        '{n} prioridades de revisión seleccionadas',
    '· {section} — withheld for {reason}:':
        '· {section} — retenido por {reason}: ',
    'AI draft. Every suggestion in this brief stays provisional until you record your own judgment. Assistance and autonomy: {assistance}':
        'Borrador de IA. Toda sugerencia de este informe es provisional hasta que usted registre su propio juicio. Asistencia y autonomía: {assistance}',
    'Points are recorded observations; lines connect them and do not show continuous monitoring. Missing values interrupt the line, and each panel has its own vertical scale. The dashed marks are the minutes at which D1-D{last} were taken: they show when you acted, and a change after a mark does not establish that the action caused it.':
        'Los puntos son observaciones registradas; las líneas los unen y no representan monitorización continua. Los valores faltantes interrumpen la línea, y cada panel tiene su propia escala vertical. Las marcas punteadas son los minutos en que se tomaron D1-D{last}: muestran cuándo actuó, y un cambio posterior a una marca no establece que la acción lo haya causado.',
    'Recorded reassessment plan: {plan}':
        'Plan de reevaluación registrado: {plan}',
    'Selected analysis limit: {limit}':
        'Límite del análisis seleccionado: {limit}',
    'The AI reasoning, the clinical identifiers and the curriculum objective titles are written in English; the scores, the sections and the recorded judgements are the same in both languages.':
        'El razonamiento de la IA, los identificadores clínicos y los títulos de los objetivos del currículo están en inglés; los puntajes, las secciones y los juicios registrados son los mismos en ambos idiomas.',
    '<b>Recorded course:</b> {course}':
        '<b>Curso registrado:</b> {course}',
    '<link href="{url}" color="#FFFFFF"><b>Open this encounter → review and record your assessment</b></link>':
        '<link href="{url}" color="#FFFFFF"><b>Abrir este encuentro → revisar y registrar su evaluación</b></link>',
    'AI suggestion on record: {suggestion}. It is held for your reading because {reason}. No new rating was assigned and no recorded faculty judgment was changed.':
        'Sugerencia de IA registrada: {suggestion}. Queda retenida para su lectura porque {reason}. No se asignó ninguna calificación nueva ni se cambió ningún juicio docente registrado.',
    'Ask this rather than judge it: {caveat}.':
        'Pregunte esto en vez de juzgarlo: {caveat}.',
    'Available and not asked about: {topics}.':
        'Disponible y no preguntado: {topics}.',
    'Held because {reason}.':
        'Retenido porque {reason}.',
    'Pilot rubric {version}. Not ACGME Milestone levels, Canadian stages or EPA supervision levels.':
        'Rúbrica piloto {version}. No son niveles de Milestone de ACGME, etapas canadienses ni niveles de supervisión de APC.',
    'Scope limit: {limit}':
        'Límite de alcance: {limit}',
    'The record cannot settle this: {reason}.':
        'El registro no puede resolver esto: {reason}.',
    # A document written in the language its encounter was played in (faculty,
    # 2026-09-26): the record's observations, references, study requests and
    # decision headings, which were assembled around their values in English.
    "HR":
        "FC",
    "SBP":
        "PAS",
    "DBP":
        "PAD",
    "RR":
        "FR",
    "CRT":
        "LLC",
    "Alertness":
        "Conciencia",
    "Extremities":
        "Extremidades",
    "Rhythm":
        "Ritmo",
    "Heart rate":
        "Frecuencia cardíaca",
    "not recorded":
        "no registrado",
    "available at {time}":
        "disponible a los {time}",
    ", sampled at {time}":
        ", muestra tomada a los {time}",
    " and ":
        " y ",
    "unchanged":
        "sin cambio",
    "Unchanged:":
        "Sin cambio:",
    "Changed:":
        "Cambió:",
    "{label} at {time}":
        "{label} a los {time}",
    "history":
        "historia",
    "study result":
        "resultado de examen",
    "presentation":
        "presentación",
    "procedure":
        "procedimiento",
    "clarification":
        "aclaración",
    "Based on: {refs}":
        "Basado en: {refs}",
    "{study} requested":
        "solicitud de {study}",
    "; +{n} more":
        "; +{n} más",
    "no result recorded":
        "sin resultado registrado",
    "{start} to {end}":
        "{start} a {end}",
    "DECISION {n} · {span} · {status}":
        "DECISIÓN {n} · {span} · {status}",
    "executed":
        "ejecutada",
    "not executed":
        "no ejecutada",
    "terminal locked":
        "cerrada al terminar el encuentro",
    "clarification required":
        "requiere aclaración",
    "information":
        "información",
    "Decision {n}":
        "Decisión {n}",
    "Reflection {n}":
        "Reflexión {n}",
    "Domain {n}":
        "Dominio {n}",
    # The convention notes that name this encounter's orders (model_conventions).
    "Converted on the chart's actual weight, the engine's stated convention while the weight type for each drug is undecided: {orders}.":
        "Convertido con el peso real de la ficha, la convención declarada del motor mientras el tipo de peso de cada fármaco está pendiente: {orders}.",
    "Rates per kilogram converted on the actual weight; the simulated effect follows the absolute mcg/min, calibrated at 70 kg: {orders}.":
        "Dosis por kilo convertidas con el peso real; el efecto simulado sigue los mcg/min absolutos, calibrados a 70 kg: {orders}.",
    "The block's duration was measured on the actual weight, the engine's convention, whatever weight the dose was written on: {orders}.":
        "La duración del bloqueo se midió con el peso real, la convención del motor, cualquiera sea el peso con que se escribió la dosis: {orders}.",
    # A document whose model prose was translated for it (prose_translation).
    "The AI reasoning was translated automatically from its English original, which remains the reference record; the clinical identifiers and the curriculum objective titles are written in English.":
        "El razonamiento de la IA se tradujo automáticamente de su original en inglés, que sigue siendo el registro de referencia; los identificadores clínicos y los títulos de los objetivos del currículo están en inglés.",
    # The Decision Review record (app._review_pdf, _review_markdown) and its downloads (Idioma 4a).
    " · composed by the app from the resident's own words, not stated as such":
        ' · compuesto por la aplicación a partir de las palabras del residente, no expresado así',
    'A learner-authored commitment for a similar future encounter.':
        'Un compromiso escrito por el residente para un encuentro similar en el futuro.',
    'A portable record of the clinical trajectory, learner reflection, expert comparison, and prospective adaptation plan.':
        'Un registro portable de la trayectoria clínica, la reflexión del residente, la comparación experta y el plan de adaptación prospectivo.',
    'ATTEMPT':
        'INTENTO',
    'CASE':
        'CASO',
    'CLOSED':
        'CIERRE',
    'STATUS':
        'ESTADO',
    'Across Decisions {first}–{last} · {times}':
        'Entre las decisiones {first}–{last} · {times}',
    'Action':
        'Acción',
    'Adaptation Plan':
        'Plan de adaptación',
    'Attempt:':
        'Intento:',
    'BP':
        'PA',
    'Carry-Forward Plan':
        'Plan traído del intento anterior',
    'Case:':
        'Caso:',
    'Complete':
        'Completa',
    'Draft':
        'Borrador',
    'Complete original encounter record · PDF, Markdown and JSON':
        'Registro original completo del encuentro · PDF, Markdown y JSON',
    'Complete review':
        'Revisión completa',
    'Decision Review':
        'Revisión de decisiones',
    'Descriptive and non-scoring. No reasoning is added unless the learner explicitly stated it.':
        'Descriptiva y sin puntaje. No se agrega ningún razonamiento que el residente no haya expresado explícitamente.',
    'Diagnostic result | {time}:':
        'Resultado de examen | {time}:',
    'Diagnostic result · {time}:':
        'Resultado de examen · {time}:',
    'Download JSON':
        'Descargar JSON',
    'Download Markdown':
        'Descargar Markdown',
    'Download PDF':
        'Descargar PDF',
    'Draft export available':
        'Borrador disponible para exportar',
    'Draft review - incomplete fields remain.':
        'Borrador de revisión: quedan campos incompletos.',
    'Educational simulation - reflective and non-scoring':
        'Simulación educativa - reflexiva y sin puntaje',
    'Encounter':
        'Encuentro',
    'Encounter closed:':
        'Cierre del encuentro:',
    'Expert Comparison':
        'Comparación experta',
    'Expert comparison has not been revealed.':
        'La comparación experta todavía no se ha revelado.',
    'Expert framing':
        'Encuadre experto',
    'How has your working model changed?':
        '¿Cómo cambió tu modelo de trabajo?',
    'Key cues':
        'Claves principales',
    'Management Reasoning Decision Review':
        'Revisión de decisiones de Management Reasoning',
    'Management Reasoning<br/>Decision Review':
        'Management Reasoning<br/>Revisión de decisiones',
    'Management Trace is a time-resolved record of how a learner translates patient state into management priorities and actions, anticipates their effects, observes the resulting patient response, and adapts subsequent management.':
        'La Management Trace es un registro ordenado en el tiempo de cómo un residente traduce el estado del paciente en prioridades y acciones de manejo, anticipa sus efectos, observa la respuesta del paciente y adapta el manejo siguiente.',
    'Management priority':
        'Prioridad de manejo',
    'Management reasoning':
        'Razonamiento de manejo',
    'Mental status':
        'Estado mental',
    'Work of breathing':
        'Trabajo respiratorio',
    'No executed action recorded':
        'No se registró una acción ejecutada',
    'No executed management decisions were recorded.':
        'No se registraron decisiones de manejo ejecutadas.',
    'No material observable change recorded.':
        'No se registró un cambio observable relevante.',
    'No reflection prompt was generated.':
        'No se generó ninguna pregunta de reflexión.',
    'Not answered':
        'Sin respuesta',
    'Not explicitly stated':
        'No expresado explícitamente',
    'Not recorded':
        'No registrado',
    'Not specified':
        'No especificado',
    'Observed response | {time}':
        'Respuesta observada | {time}',
    'Observed response · {time}':
        'Respuesta observada · {time}',
    'One defensible action':
        'Una acción defendible',
    'One defensible expert reasoning model for comparison. It is non-scoring, is not an answer key, and requires faculty validation.':
        'Un modelo de razonamiento experto defendible, para comparar. No da puntaje, no es una pauta de respuestas y requiere validación docente.',
    'Original learner input':
        'Texto original del residente',
    'PATIENT STATE':
        'ESTADO DEL PACIENTE',
    'Page {page}':
        'Página {page}',
    'Patient state':
        'Estado del paciente',
    'Preservation goal':
        'Objetivo de preservación',
    'Problem':
        'Problema',
    'Prospective Adaptation Plan':
        'Plan de adaptación prospectivo',
    'Prospective commitment for a similar future encounter.':
        'Compromiso prospectivo para un encuentro similar en el futuro.',
    'Prospective learning intention brought into this repeat attempt.':
        'Intención de aprendizaje prospectiva traída a este nuevo intento.',
    'Reassessment':
        'Reevaluación',
    'Reassessment target':
        'Objetivo de reevaluación',
    'Reassessment targets':
        'Objetivos de reevaluación',
    'Reflective, non-scoring clinical management review':
        'Revisión reflexiva del manejo clínico, sin puntaje',
    'Retrospective learner reflection. These responses do not alter the Management Trace above.':
        'Reflexión retrospectiva del residente. Estas respuestas no modifican la Management Trace anterior.',
    'Retrospective learner reflection. These responses do not alter the Management Trace.':
        'Reflexión retrospectiva del residente. Estas respuestas no modifican la Management Trace.',
    'Review complete and ready to export.':
        'Revisión completa y lista para exportar.',
    'Review status:':
        'Estado de la revisión:',
    'Simulator:':
        'Simulador:',
    'Some reflection prompts or expert models were written for this case in English and are shown as written.':
        'Algunas preguntas de reflexión o modelos expertos de este caso se escribieron en inglés y se muestran tal como están.',
    'The frozen trace and current autosaved responses are exportable at any stage.':
        'La traza congelada y las respuestas guardadas automáticamente se pueden exportar en cualquier etapa.',
    'This report supports facilitated reflection and deliberate practice. It does not provide a score or replace clinical supervision.':
        'Este informe apoya la reflexión guiada y la práctica deliberada. No entrega un puntaje ni reemplaza la supervisión clínica.',
    'This review is reflective and non-scoring. The expert model is one defensible approach, not an answer key.':
        'Esta revisión es reflexiva y sin puntaje. El modelo experto es un enfoque defendible, no una pauta de respuestas.',
    'This trace is descriptive and non-scoring. It does not add reasoning that the learner did not explicitly state.':
        'Esta traza es descriptiva y sin puntaje. No agrega razonamiento que el residente no haya expresado explícitamente.',
    'Trade-off to manage':
        'Compromiso que hay que manejar',
    'What alternative action would you take?':
        '¿Qué acción alternativa tomarías?',
    'What finding or threshold should influence your next priority?':
        '¿Qué hallazgo o umbral debería influir en tu siguiente prioridad?',
    'What response would you expect, and what would you reassess?':
        '¿Qué respuesta esperarías y qué reevaluarías?',
    'What will you change or preserve next time?':
        '¿Qué cambiarás o mantendrás la próxima vez?',
    'Where did your reasoning align with this model?':
        '¿En qué coincidió tu razonamiento con este modelo?',
    'advice to the patient':
        'indicación al paciente',
    'conditional plan; not executed now':
        'plan condicional; no se ejecutó ahora',
    'indicated; administration and effect not modelled':
        'indicado; administración y efecto no modelados',
    'prescription for home; not a dose given here':
        'receta para el domicilio; no es una dosis administrada aquí',
    'recognized; not yet executable':
        'reconocido; todavía no ejecutable',
    '{time} | Decision {number}':
        '{time} | Decisión {number}',
    "Reasoning clarification:":
        "Aclaración del razonamiento:",
    "Guided reasoning completion:":
        "Razonamiento completado con guía:",
    "Comparison point":
        "Punto de comparación",
    "Review prompt":
        "Pregunta de revisión",
    '{time} · Decision {number}':
        '{time} · Decisión {number}',
    'Review your management model':
        'Revisa tu modelo de manejo',
    'What response did you expect, what did you observe, and how would those observations influence your next priority?':
        '¿Qué respuesta esperabas, qué observaste y cómo influirían esas observaciones en tu siguiente prioridad?',
    'Reasoning not explicitly stated':
        'Razonamiento no expresado explícitamente',
    'No management reasoning was explicitly stated. What problem representation, priority, and expected effect were guiding this action?':
        'No se expresó explícitamente un razonamiento de manejo. ¿Qué representación del problema, qué prioridad y qué efecto esperado guiaban esta acción?',
    'Reasoning across decisions':
        'Razonamiento a lo largo de las decisiones',
    'You made several management decisions without explicitly stating the reasoning guiding them. Looking back across this sequence, what problem representation and management priorities drove your actions, and when did your working model change?':
        'Tomaste varias decisiones de manejo sin expresar explícitamente el razonamiento que las guiaba. Mirando esta secuencia en retrospectiva, ¿qué representación del problema y qué prioridades de manejo guiaron tus acciones, y cuándo cambió tu modelo de trabajo?',
    # The review screens after an encounter (app.render_decision_review, Idioma 4b).
    'First record your own retrospective reasoning. The expert model remains hidden until your reflection is complete and locked; comparison is reflective and non-scoring.':
        'Primero registra tu propio razonamiento retrospectivo. El modelo experto permanece oculto hasta que tu reflexión esté completa y bloqueada; la comparación es reflexiva y sin puntaje.',
    '{done}/{total} fields autosaved':
        '{done}/{total} campos guardados automáticamente',
    '{done}/{total} decisions':
        '{done}/{total} decisiones',
    '{done}/{total} plan fields':
        '{done}/{total} campos del plan',
    'Autosave is active when you leave a field or move to another step.':
        'El guardado automático se activa al salir de un campo o pasar a otro paso.',
    '{done}/{total} comparisons':
        '{done}/{total} comparaciones',
    '1 · Decision Review':
        '1 · Revisión de decisiones',
    '2 · Expert Comparison':
        '2 · Comparación experta',
    '3 · Adaptation Plan':
        '3 · Plan de adaptación',
    '4 · Final Summary':
        '4 · Resumen final',
    'No reflection prompt was generated. Continue to the Adaptation Plan.':
        'No se generó ninguna pregunta de reflexión. Continúa al Plan de adaptación.',
    'Your original reflection is locked because the expert model has been revealed.':
        'Tu reflexión original está bloqueada porque ya se reveló el modelo experto.',
    'Review point {number} of {total}':
        'Punto de revisión {number} de {total}',
    'Previous decision':
        'Decisión anterior',
    'Next decision':
        'Decisión siguiente',
    'Complete all four fields for every selected decision. Revealing the model locks these responses so the comparison cannot rewrite your initial reflection.':
        'Completa los cuatro campos de cada decisión seleccionada. Revelar el modelo bloquea estas respuestas, para que la comparación no pueda reescribir tu reflexión inicial.',
    'Lock Decision Review & Reveal Expert Comparison':
        'Bloquear la revisión y revelar la comparación experta',
    'Compare your locked reflection with one defensible expert reasoning model. This is a faculty-validation draft, not an answer key and not a score.':
        'Compara tu reflexión bloqueada con un modelo de razonamiento experto defendible. Es un borrador para validación docente, no una pauta de respuestas ni un puntaje.',
    'Other review points':
        'Otros puntos de revisión',
    '{done}/{total} fields':
        '{done}/{total} campos',
    'Reveal comparison':
        'Revelar la comparación',
    'No faculty-validation expert model is available for these review points.':
        'No hay un modelo experto para validación docente en estos puntos de revisión.',
    'Continue to Adaptation Plan':
        'Continuar al Plan de adaptación',
    'Comparison point {number} of {total}':
        'Punto de comparación {number} de {total}',
    'Previous comparison':
        'Comparación anterior',
    'Next comparison':
        'Comparación siguiente',
    '{count} fields were drafted from your locked reflection. Use the comparison insights to define your next management priority; every field remains editable.':
        '{count} campos se redactaron a partir de tu reflexión bloqueada. Usa lo que aprendiste de la comparación para definir tu siguiente prioridad de manejo; todos los campos siguen siendo editables.',
    'Decisions':
        'Decisiones',
    'Comparisons':
        'Comparaciones',
    'Plan fields':
        'Campos del plan',
    'Status':
        'Estado',
    'Start a new assigned encounter with your Adaptation Plan. The next clinical trajectory and review begin empty.':
        'Inicia un nuevo encuentro asignado con tu Plan de adaptación. La siguiente trayectoria clínica y su revisión comienzan vacías.',
    'Start a clean attempt of the same encounter. Only the prospective Adaptation Plan is carried forward; the clinical trajectory, Management Trace, self-review, and comparison restart empty.':
        'Inicia un intento limpio del mismo encuentro. Sólo se lleva el Plan de adaptación prospectivo; la trayectoria clínica, la Management Trace, la autorrevisión y la comparación comienzan vacías.',
    'Next Encounter with This Adaptation Plan':
        'Siguiente encuentro con este Plan de adaptación',
    'Repeat Encounter with This Adaptation Plan':
        'Repetir el encuentro con este Plan de adaptación',
    'Continue to Expert Comparison':
        'Continuar a la comparación experta',
    'No response recorded yet.':
        'Todavía no hay respuesta registrada.',
    'Review this decision':
        'Revisar esta decisión',
    'Your locked reflection':
        'Tu reflexión bloqueada',
    'Expert reasoning model':
        'Modelo de razonamiento experto',
    'Your comparison':
        'Tu comparación',
    'Other comparison points':
        'Otros puntos de comparación',
    'Back to Expert Comparison':
        'Volver a la comparación experta',
    'Continue to Final Summary':
        'Continuar al Resumen final',
    'Final Summary':
        'Resumen final',
    'Decision Review, Expert Comparison, and Adaptation Plan are complete and ready to export.':
        'La revisión de decisiones, la comparación experta y el Plan de adaptación están completos y listos para exportar.',
    '{count} field(s) remain incomplete. The current draft can still be exported.':
        'Quedan {count} campo(s) incompletos. El borrador actual igual se puede exportar.',
    'Decision synthesis':
        'Síntesis de las decisiones',
    'Comparison synthesis':
        'Síntesis de la comparación',
    'View Locked Review':
        'Ver la revisión bloqueada',
    'Edit Comparison':
        'Editar la comparación',
    'Edit Adaptation Plan':
        'Editar el Plan de adaptación',
    'Download complete record':
        'Descargar el registro completo',
    'Adapt & Repeat':
        'Adaptar y repetir',
    'Framing':
        'Encuadre',
    'Expert model available · faculty-validation draft':
        'Modelo experto disponible · borrador para validación docente',
    'Compare this decision':
        'Comparar esta decisión',
    'Show incomplete fields':
        'Mostrar los campos incompletos',
    'Saved response preview:':
        'Vista previa de la respuesta guardada:',
    ' · drafted from your review':
        ' · redactado a partir de tu revisión',
}
TABLES = {"es": ES}
