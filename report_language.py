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
    # The foundation challenges' compact titles (DF-2, 2026-09-27).
    'Relate the rhythm to the patient':
        'Relacionar el ritmo con el paciente',
    'Anticipate and check an effect':
        'Anticipar y comprobar un efecto',
    'Pressure, flow and perfusion':
        'Presión, flujo y perfusión',
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
        'Con orientación - se necesitó orientación adicional (informado por el docente).',
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
        'preguntas por decisión mostradas; el análisis completo contiene el resto.',
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
        '3 de {n} preguntas por decisión mostradas; el análisis completo contiene el resto.',
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
    # What each competency link contributes (DF-2, 2026-09-27). Labels of the
    # scope of the evidence, never scores.
    'Direct contribution:':
        'Contribución directa:',
    'Partial contribution:':
        'Contribución parcial:',
    'Not observed: {limit}':
        'No observado: {limit}',
    # Where an objective's observation opportunity comes from (DF-1,
    # observation_opportunities._NOTES), on the faculty's assessment form.
    'Observation opportunity: {note}':
        'Oportunidad de observación: {note}',
    'What the record might show, as guidance: {items}':
        'Lo que el registro podría mostrar, como orientación: {items}',
    'The encounter was generated to offer this objective.':
        'El encuentro se generó para ofrecer este objetivo.',
    'The case declares a real opportunity to observe this objective.':
        'El caso declara una oportunidad real de observar este objetivo.',
    'The case declares no opportunity to observe this objective.':
        'El caso declara que no hay oportunidad de observar este objetivo.',
    ('Not reviewed for this case. It stays observable under the rule that applied '
     'before observation opportunities were declared.'):
        ('Sin revisar para este caso. Sigue siendo observable con la regla que regía '
         'antes de que se declararan las oportunidades de observación.'),
    ('Not reviewed for this case. Under the rule that applied before, only the '
     'encounter generated for this objective offers it.'):
        ('Sin revisar para este caso. Con la regla que regía antes, sólo el encuentro '
         'generado para este objetivo lo ofrece.'),
    'This objective is not enabled.':
        'Este objetivo no está habilitado.',
    'This objective does not exist.':
        'Este objetivo no existe.',
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
    'repeat instruction; not executed now':
        'instrucción de repetición; no se ejecutó ahora',
    'indicated; administration and effect not modelled':
        'indicado; administración y efecto no modelados',
    'blood product ordered; physiologic effect not modelled':
        'hemoderivado indicado; efecto fisiológico no modelado',
    'massive transfusion protocol activated; the activation gives no blood product by itself':
        'protocolo de transfusión masiva activado; la activación no administra hemoderivados por sí sola',
    'massive transfusion protocol stood down; no unit already given is taken back':
        'protocolo de transfusión masiva desactivado; ninguna unidad ya administrada se revierte',
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
    # The resident's portal and the Management Trace screen (Idioma 4b).
    'A copy of your own record from a pilot simulator. It is not a certificate, a transcript, or evidence that a workplace EPA was achieved. The rubric is a pilot instrument and its scores are not ACGME Milestone levels, Canadian stages or EPA supervision levels.':
        'Una copia de tu propio registro en un simulador piloto. No es un certificado, un expediente académico ni evidencia de que se haya logrado una APC en el lugar de trabajo. La rúbrica es un instrumento piloto y sus puntajes no son niveles de los Milestones de ACGME, etapas canadienses ni niveles de supervisión de APC.',
    'A photograph of your face':
        'Una fotografía de tu cara',
    'Accepted {date} · version {version}':
        'Aceptado el {date} · versión {version}',
    "Choosing 'Not now' changes nothing else: you can begin encounters immediately, and you can add a photograph later from My progress, or never.":
        'Elegir «Ahora no» no cambia nada más: puedes comenzar encuentros de inmediato y agregar una fotografía más tarde desde Mi progreso, o nunca.',
    'Clinical encounter':
        'Encuentro clínico',
    'Continue to my encounters':
        'Continuar a mis encuentros',
    'Current initials:':
        'Iniciales actuales:',
    'Delete my photograph and initials':
        'Borrar mi fotografía y mis iniciales',
    'Download your Management Trace (PDF)':
        'Descargar tu Management Trace (PDF)',
    'Download your complete record (JSON)':
        'Descargar tu registro completo (JSON)',
    'Download your rubric assessment (PDF)':
        'Descargar tu evaluación con rúbrica (PDF)',
    'Encounters in this programme are reviewed at a distance. A face beside your initials and your training year helps a faculty member keep one encounter apart from another. It appears in one place: the centre of your profile chart. No other resident can see it.':
        'Los encuentros de este programa se revisan a distancia. Una cara junto a tus iniciales y tu año de formación ayuda a un docente a distinguir un encuentro de otro. Aparece en un solo lugar: el centro de tu gráfico de perfil. Ningún otro residente puede verla.',
    'Everything saved under your account: your encounters, your own reflections and plans, and every rubric assessment a faculty member has confirmed. It is a copy of your record, not a certificate.':
        'Todo lo guardado en tu cuenta: tus encuentros, tus propias reflexiones y planes, y cada evaluación con rúbrica que un docente haya confirmado. Es una copia de tu registro, no un certificado.',
    'I have read this and agree':
        'Lo leí y estoy de acuerdo',
    'Next encounter: {when} · {challenge}':
        'Encuentro siguiente: {when} · {challenge}',
    'No AI reading of this encounter was saved, so the Management Trace cannot be rebuilt. The encounter record itself is intact.':
        'No se guardó una lectura de IA de este encuentro, así que la Management Trace no se puede reconstruir. El registro del encuentro está intacto.',
    'No completed encounter is saved yet. Your first one will appear here with its Management Trace.':
        'Todavía no hay encuentros completados guardados. El primero aparecerá aquí con su Management Trace.',
    'No confirmed rubric assessment yet.':
        'Todavía no hay una evaluación con rúbrica confirmada.',
    'Nothing yet. Each encounter ends by asking what you would carry into the next one, and those answers collect here.':
        'Nada todavía. Cada encuentro termina preguntando qué llevarías al siguiente, y esas respuestas se reúnen aquí.',
    'One step, once. Everything else about your account is already ready.':
        'Un paso, una sola vez. Todo lo demás de tu cuenta ya está listo.',
    'Read the agreement':
        'Leer el acuerdo',
    'Set up your account':
        'Configura tu cuenta',
    'Shown in one place: the centre of your profile chart, and on the assessment documents that carry it. You and faculty of this programme can see it. No other resident can see your photograph, your chart or anything else of yours.':
        'Se muestra en un solo lugar: el centro de tu gráfico de perfil, y en los documentos de evaluación que lo incluyen. La ven tú y los docentes de este programa. Ningún otro residente puede ver tu fotografía, tu gráfico ni nada tuyo.',
    'Thank you. One last optional step, and you are ready to begin.':
        'Gracias. Un último paso opcional y estarás listo para comenzar.',
    'The agreement you accepted':
        'El acuerdo que aceptaste',
    'The file is re-encoded as a small square image before it is stored. Nothing of the original is kept, including where and when it was taken.':
        'El archivo se vuelve a codificar como una imagen cuadrada pequeña antes de guardarlo. No se conserva nada del original, ni dónde ni cuándo se tomó.',
    'This is your most recent encounter; the next one is still ahead.':
        'Este es tu encuentro más reciente; el siguiente todavía está por venir.',
    'What you said you would do differently':
        'Lo que dijiste que harías distinto',
    'Written after each encounter, in your own words, and set beside the encounter that followed it. Nothing here is scored.':
        'Escrito después de cada encuentro, con tus propias palabras, y puesto junto al encuentro que vino después. Nada de esto tiene puntaje.',
    'You can also do this later, or not at all.':
        'También puedes hacerlo más tarde, o no hacerlo.',
    'Your complete record':
        'Tu registro completo',
    'Your completed encounters':
        'Tus encuentros completados',
    'Your initials':
        'Tus iniciales',
    'Your own record. A rubric assessment appears here once a faculty member has reviewed and completed it; until then it is still theirs.':
        'Tu propio registro. Una evaluación con rúbrica aparece aquí cuando un docente la revisa y la completa; hasta entonces sigue siendo suya.',
    'Your photograph and initials':
        'Tu fotografía y tus iniciales',
    '{count} encounter(s) · {assessed} with a confirmed assessment.':
        '{count} encuentro(s) · {assessed} con una evaluación confirmada.',
    'Not now':
        'Ahora no',
    'none stored':
        'ninguna guardada',
    'A working model was not explicitly recorded.':
        'No se registró explícitamente un modelo de trabajo.',
    'AI analysis is not configured for this application. You can still review and download your original encounter record.':
        'El análisis de IA no está configurado en esta aplicación. Igual puedes revisar y descargar el registro original de tu encuentro.',
    'AI interpretation of your recorded encounter · your original decisions and locked reflection are preserved.':
        'Interpretación de IA de tu encuentro registrado · tus decisiones originales y tu reflexión bloqueada se conservan.',
    'Blood pressure · mmHg':
        'Presión arterial · mmHg',
    'Connecting your decisions, expectations and observed patient responses...':
        'Relacionando tus decisiones, expectativas y las respuestas observadas del paciente...',
    'Decision {number}':
        'Decisión {number}',
    'Download Management Trace PDF':
        'Descargar el PDF de la Management Trace',
    'Encounter information':
        'Información del encuentro',
    'Executed actions':
        'Acciones ejecutadas',
    'Expectation and observed response':
        'Expectativa y respuesta observada',
    'Heart rate · /min':
        'Frecuencia cardíaca · /min',
    'How your management evolved':
        'Cómo evolucionó tu manejo',
    'Later reflection on {decision}':
        'Reflexión posterior sobre {decision}',
    'No explicit expectation was recorded.':
        'No se registró una expectativa explícita.',
    'Order as entered':
        'Orden tal como se escribió',
    'Oxygen saturation · %':
        'Saturación de oxígeno · %',
    "Partial analysis: {count} passage(s) were withheld because they broke a rule of this report (a number in the prose, or a citation outside what that decision may cite). They are listed in the PDF's technical record. Your complete encounter record is unaffected.":
        'Análisis parcial: se retuvieron {count} pasaje(s) porque rompían una regla de este informe (un número en la prosa, o una cita fuera de lo que esa decisión puede citar). Están en el registro técnico del PDF. El registro completo de tu encuentro no se ve afectado.',
    'Patterns to retain':
        'Patrones que conservar',
    'Questions for your next encounter':
        'Preguntas para tu próximo encuentro',
    'Recorded order':
        'Orden registrada',
    'Recorded order and patient response':
        'Orden registrada y respuesta del paciente',
    'Retry Management Trace analysis':
        'Reintentar el análisis de la Management Trace',
    'The AI reasoning is shown in English; the Spanish PDF of your Management Trace translates it.':
        'El razonamiento de la IA se muestra en inglés; el PDF en español de tu Management Trace lo trae traducido.',
    'Values recorded at decision and response times. Lines connect observations; they do not represent continuous measurements.':
        'Valores registrados en los momentos de decisión y de respuesta. Las líneas unen observaciones; no representan mediciones continuas.',
    'What you expected':
        'Lo que esperabas',
    'Your Management Trace':
        'Tu Management Trace',
    'Your analysis was not available. The complete encounter record remains available below.':
        'Tu análisis no estuvo disponible. El registro completo del encuentro sigue disponible más abajo.',
    'Your later reflection':
        'Tu reflexión posterior',
    'Your recorded reasoning':
        'Tu razonamiento registrado',
    'a recorded decision':
        'una decisión registrada',
    'Evidence:':
        'Evidencia:',
    'Priority:':
        'Prioridad:',
    'Observation':
        'Observación',
    'Before':
        'Antes',
    'After':
        'Después',
    'Systolic BP':
        'PA sistólica',
    'Presentation':
        'Presentación',
    'Patient history':
        'Anamnesis',
    'Examination':
        'Examen físico',
    'Diagnostic result':
        'Resultado de examen',
    'Clinical update':
        'Actualización clínica',
    'Procedure':
        'Procedimiento',
    'Clarification':
        'Aclaración',
    'Prototype':
        'Registro',
    'Study not performed':
        'Examen no realizado',
    # The room's decision-by-decision record (app.render_management_trace).
    'No executed management decisions were recorded in this encounter.':
        'No se registraron decisiones de manejo ejecutadas en este encuentro.',
    'Clinical response':
        'Respuesta clínica',
    'New diagnostic information':
        'Nueva información diagnóstica',
    # The completed encounter's page in the room.
    'Completed encounter review':
        'Revisión del encuentro completado',
    'This saved review is read-only. Start a new encounter to apply your Adaptation Plan.':
        'Esta revisión guardada es de sólo lectura. Inicia un nuevo encuentro para aplicar tu Plan de adaptación.',
    'Your Adaptation Plan':
        'Tu Plan de adaptación',
    'Your original orders, stated reasoning and recorded responses remain unchanged.':
        'Tus órdenes originales, el razonamiento que expresaste y las respuestas registradas se mantienen sin cambios.',
    'Complete your independent reflection to receive an analyzed Management Trace with your clinical trajectory and key decisions.':
        'Completa tu reflexión independiente para recibir una Management Trace analizada con tu trayectoria clínica y tus decisiones clave.',
    'Original decision-by-decision record':
        'Registro original, decisión por decisión',
    # The faculty portals, the rubric, progress, the image bank, accounts and the curriculum (Idioma 4c).
    '- declared by the':
        '- declarado por el',
    '- nobody has declared it yet':
        '- nadie lo ha declarado aún',
    '. Help described:':
        '. Ayuda descrita:',
    '. No new rating was assigned and no recorded judgment was changed.':
        '. No se asignó ninguna calificación nueva ni se cambió ningún juicio registrado.',
    'A new declaration is added to the history; nothing earlier is overwritten, and no assessment already confirmed changes.':
        'Se agrega una nueva declaración al historial; no se sobrescribe nada anterior y ninguna evaluación ya confirmada cambia.',
    'AI draft loaded. Edit every field as needed and confirm your assessment before saving. An unanswered field is not an unsatisfactory judgment.':
        'Borrador de IA cargado. Edita cada campo según sea necesario y confirma tu evaluación antes de guardar. Un campo sin responder no es un juicio insatisfactorio.',
    'AI faculty assessment brief':
        'Informe de evaluación docente de IA',
    'AI generation is unavailable until OPENAI_API_KEY is configured in the private deployment secrets. Saved reports remain available.':
        'La generación con IA no está disponible hasta que se configure OPENAI_API_KEY en los secretos privados del despliegue. Los informes guardados siguen disponibles.',
    'AI suggestion':
        'Sugerencia de IA',
    'An unreported context is a valid state: the brief is generated either way, and an autonomy the record cannot establish is left for your confirmation.':
        'Un contexto no informado es un estado válido: el informe se genera de todos modos, y una autonomía que el registro no permite establecer queda para tu confirmación.',
    'Analyzing the completed encounter and its recorded evidence...':
        'Analizando el encuentro completado y su evidencia registrada...',
    'Autonomy the declared context did not allow the AI to propose was left for your confirmation:':
        'La autonomía que el contexto declarado no permitió proponer a la IA quedó para tu confirmación:',
    'Choose what is known about the help received.':
        'Elige lo que se sabe sobre la ayuda recibida.',
    'Complete or correct the assistance context':
        'Completar o corregir el contexto de asistencia',
    "Confirmed. The resident's profile now includes this encounter.":
        'Confirmado. El perfil del residente ahora incluye este encuentro.',
    'Decisions the help affected (optional)':
        'Decisiones en que influyó la ayuda (opcional)',
    'Declaration saved and added to the history.':
        'Declaración guardada y agregada al historial.',
    'Discard loaded AI draft':
        'Descartar el borrador de IA cargado',
    'Download 2-page faculty brief (PDF)':
        'Descargar informe docente de 2 páginas (PDF)',
    'Download full faculty analysis (PDF)':
        'Descargar análisis docente completo (PDF)',
    'Download rubric assessment (PDF)':
        'Descargar evaluación por rúbrica (PDF)',
    'Faculty analysis saved. Review it here or download the PDF.':
        'Análisis docente guardado. Revísalo aquí o descarga el PDF.',
    'Faculty document. It is not released to the resident until you have reviewed and completed it.':
        'Documento docente. No se entrega al residente hasta que lo hayas revisado y completado.',
    'Faculty judgment needed':
        'Se requiere el juicio docente',
    'Generate AI faculty brief':
        'Generar informe docente de IA',
    'Generate a brief to review the reasoning, key decisions, evidence by objective, and suggested feedback.':
        'Genera un informe para revisar el razonamiento, las decisiones clave, la evidencia por objetivo y la retroalimentación sugerida.',
    'Generate a new AI faculty brief':
        'Generar un nuevo informe docente de IA',
    'Guided - structured help directed the reasoning':
        'Guiada - una ayuda estructurada dirigió el razonamiento',
    'Help received during the encounter':
        'Ayuda recibida durante el encuentro',
    'Independent - faculty has verified no additional help':
        'Independiente - el docente verificó que no hubo ayuda adicional',
    'Insufficient evidence - faculty judgment needed':
        'Evidencia insuficiente - se requiere el juicio docente',
    'Limits of this analysis':
        'Límites de este análisis',
    'Load AI suggestion into editable form':
        'Cargar la sugerencia de IA en un formulario editable',
    'Not known / not documented':
        'No se sabe / no está documentado',
    'Points to review':
        'Puntos para revisar',
    'Private decision support for faculty. Review suggestions against the recorded evidence before making an assessment.':
        'Apoyo privado a la decisión para docentes. Contrasta las sugerencias con la evidencia registrada antes de hacer una evaluación.',
    'Prompted - additional prompts were needed':
        'Con orientación - se necesitó orientación adicional',
    'Read the analysis and debriefing questions':
        'Lee el análisis y las preguntas de debriefing',
    'Reference unavailable':
        'Referencia no disponible',
    'Reflection and adaptation':
        'Reflexión y adaptación',
    'Save declaration':
        'Guardar declaración',
    'Select an objective below to load its suggestion as an editable draft. Only Record objective assessment saves your final judgment.':
        'Selecciona un objetivo más abajo para cargar su sugerencia como borrador editable. Solo Registrar evaluación del objetivo guarda tu juicio final.',
    'Show the patient image record':
        'Mostrar el registro de imágenes del paciente',
    'Start with the 2-page brief, then review an objective below, edit its draft and record your judgment. The full analysis remains available for verification.':
        'Comienza con el informe de 2 páginas, luego revisa un objetivo más abajo, edita su borrador y registra tu juicio. El análisis completo sigue disponible para verificación.',
    'Suggested needs improvement':
        'Se sugiere que requiere mejorar',
    'The assistance context was declared again after this brief was written. The brief is kept exactly as written; generate a new one to use the current declaration, and both will remain on record.':
        'El contexto de asistencia se volvió a declarar después de redactar este informe. El informe se conserva exactamente como se redactó; genera uno nuevo para usar la declaración actual, y ambos quedarán registrados.',
    'The full PDF could not be prepared. The saved analysis and assessment form remain available here.':
        'No se pudo preparar el PDF completo. El análisis guardado y el formulario de evaluación siguen disponibles aquí.',
    'The rubric document could not be prepared. The assessment above is unchanged and remains available.':
        'No se pudo preparar el documento de la rúbrica. La evaluación anterior no cambia y sigue disponible.',
    'This report could not be fitted into the concise PDF. Open the full analysis below; you can still review and record assessments.':
        'Este informe no cupo en el PDF conciso. Abre el análisis completo más abajo; igual puedes revisar y registrar evaluaciones.',
    'What help, if any (optional)':
        'Qué ayuda, si la hubo (opcional)',
    'Why you are completing or correcting it (optional)':
        'Por qué lo completas o corriges (opcional)',
    'Written under the faculty-reported context of its time:':
        'Redactado bajo el contexto informado por el docente en ese momento:',
    'Written under:':
        'Redactado bajo:',
    'time not recorded':
        'hora no registrada',
    '\n\nThese marks change nothing by themselves; the decision stays yours.':
        '\n\nEstas marcas no cambian nada por sí solas; la decisión sigue siendo tuya.',
    '(not averaged)':
        '(no promediado)',
    'A declared exclusion is established by the record':
        'El registro establece una exclusión declarada',
    'A partial assessment keeps its events and their penalty but has no total comparable with a complete episode.':
        'Una evaluación parcial conserva sus eventos y su penalización, pero no tiene un total comparable con un episodio completo.',
    "A pilot instrument. Its scores are not ACGME Milestone levels, Canadian stages or EPA supervision levels, and they do not assess a specialist's competence. You confirm or change every value; the totals are computed from what you record.":
        'Un instrumento piloto. Sus puntajes no son niveles de Milestone de ACGME, etapas canadienses ni niveles de supervisión de APC, y no evalúan la competencia de un especialista. Tú confirmas o cambias cada valor; los totales se calculan a partir de lo que registras.',
    'AI generation is unavailable until OPENAI_API_KEY is configured. You can still score the rubric yourself.':
        'La generación con IA no está disponible hasta que se configure OPENAI_API_KEY. Igual puedes puntuar la rúbrica tú mismo.',
    'Acceptable alternatives:':
        'Alternativas aceptables:',
    'Confirm assessment':
        'Confirmar evaluación',
    'Confirmed - applies the penalty':
        'Confirmado - aplica la penalización',
    'Critical events defined for this case':
        'Eventos críticos definidos para este caso',
    'Critical omission':
        'Omisión crítica',
    'Dangerous action':
        'Acción peligrosa',
    'Dismissed - no penalty':
        'Descartado - sin penalización',
    'Does not count when:':
        'No cuenta cuando:',
    'Drawn as a gap rather than at the centre, because it is not a zero:':
        'Se dibuja como un vacío y no en el centro, porque no es un cero:',
    'Each is defined before the encounter. A confirmed event costs 3 points and stays visible however high the total is. Anything else that concerns you is recorded for review and carries no deduction.':
        'Cada uno se define antes del encuentro. Un evento confirmado cuesta 3 puntos y sigue visible por alto que sea el total. Cualquier otra cosa que te preocupe se registra para revisión y no descuenta puntos.',
    'Every condition the record can settle is met':
        'Se cumple cada condición que el registro puede resolver',
    'Generate a new AI proposal':
        'Generar una nueva propuesta de IA',
    'Generate an AI proposal':
        'Generar una propuesta de IA',
    'Latest encounter':
        'Último encuentro',
    'Management reasoning profile** (pilot rubric':
        'Perfil de razonamiento de manejo** (rúbrica piloto',
    'Management reasoning rubric - pilot 1.0':
        'Rúbrica de razonamiento de manejo - piloto 1.0',
    'No AI proposal has been generated for this encounter revision.':
        'No se ha generado ninguna propuesta de IA para esta revisión del encuentro.',
    'No encounter has a rubric assessment a faculty member has confirmed yet. An encounter nobody has assessed is absent from this profile, not a zero.':
        'Ningún encuentro tiene aún una evaluación por rúbrica confirmada por un docente. Un encuentro que nadie ha evaluado está ausente de este perfil, no es un cero.',
    'No rubric analysis model is configured.':
        'No hay ningún modelo de análisis de rúbrica configurado.',
    'Not assessable':
        'No evaluable',
    'Not decided yet':
        'Aún sin decidir',
    'Note (optional)':
        'Nota (opcional)',
    'Requesting one bounded proposal...':
        'Solicitando una propuesta acotada...',
    'The AI proposes this event occurred. Confirm or dismiss it.':
        'La IA propone que este evento ocurrió. Confírmalo o descártalo.',
    'The AI proposes this event, but the record contradicts it. Confirming it requires your written reason.':
        'La IA propone este evento, pero el registro lo contradice. Confirmarlo requiere que escribas tu motivo.',
    'The record contradicts this event':
        'El registro contradice este evento',
    'The record is compatible; part of the trigger needs your reading':
        'El registro es compatible; parte del disparador requiere tu lectura',
    'Why (the AI did not propose this one)':
        'Por qué (la IA no propuso este)',
    'Why is it not assessable? (a zero is a demonstrated failure; this is not one)':
        '¿Por qué no es evaluable? (un cero es una falla demostrada; esto no lo es)',
    'Why you confirm it although the record contradicts it':
        'Por qué lo confirmas aunque el registro lo contradiga',
    'Your decision':
        'Tu decisión',
    'date not recorded':
        'fecha no registrada',
    'never asked about':
        'nunca se preguntó',
    'not assessable in this encounter.':
        'no evaluable en este encuentro.',
    'sound and anticipatory':
        'sólido y anticipatorio',
    'without a version':
        'sin versión',
    '\n\nCould not be determined: the record does not let you judge it. It is not a negative result and not independence.':
        '\n\nNo se pudo determinar: el registro no permite juzgarla. No es un resultado negativo ni es independencia.',
    ': an assessment is already recorded for this encounter.':
        ': ya hay una evaluación registrada para este encuentro.',
    "A satisfactory observation whose autonomy could not be determined is counted and shown apart. Where an objective requires a level of autonomy, it does not meet that level: only observations at the required level count toward that objective's target.":
        'Una observación satisfactoria cuya autonomía no se pudo determinar se cuenta y se muestra aparte. Cuando un objetivo exige un nivel de autonomía, esa observación no cumple ese nivel: solo las observaciones en el nivel exigido cuentan para la meta de ese objetivo.',
    'Assess observed objectives':
        'Evaluar objetivos observados',
    'Assessed encounters':
        'Encuentros evaluados',
    'Assessment and feedback saved without increasing the satisfactory count.':
        'Evaluación y retroalimentación guardadas sin aumentar el conteo de observaciones satisfactorias.',
    'Assessment to void':
        'Evaluación que se anulará',
    'Assessment voided. Its history has been retained and the count updated.':
        'Evaluación anulada. Se conservó su historial y se actualizó el conteo.',
    'At confirmation:':
        'Al confirmar:',
    'Autonomy not determined':
        'Autonomía no determinada',
    'Before recording, confirm your review of the AI draft.':
        'Antes de registrar, confirma tu revisión del borrador de IA.',
    'Changes to assessments, targets, and faculty decisions are retained for review.':
        'Los cambios en evaluaciones, metas y decisiones docentes se conservan para revisión.',
    'Choose your assessment after reviewing the evidence':
        'Elige tu evaluación después de revisar la evidencia',
    'Competency evidence to review':
        'Evidencia de competencia para revisar',
    'Complete the encounter and reflection before recording an objective assessment.':
        'Completa el encuentro y la reflexión antes de registrar una evaluación de objetivo.',
    'Confirm simulated-component achievement':
        'Confirmar el logro del componente simulado',
    'Correct a recorded assessment':
        'Corregir una evaluación registrada',
    'Could not be determined':
        'No se pudo determinar',
    'Depth and autonomy are local observation descriptors, not ACGME milestone levels or residency years. Autonomy is asked for only to confirm this objective; a draft can keep it pending.':
        'La profundidad y la autonomía son descriptores locales de observación, no niveles de Milestone de ACGME ni años de residencia. La autonomía se pide solo para confirmar este objetivo; un borrador puede dejarla pendiente.',
    'Draft saved. It counts for nothing until you record the assessment.':
        'Borrador guardado. No cuenta para nada hasta que registres la evaluación.',
    'Evidence supporting your judgment':
        'Evidencia que respalda tu juicio',
    'Explain the judgment using the selected evidence, including any limits or areas for improvement.':
        'Explica el juicio usando la evidencia seleccionada, incluidos los límites o aspectos por mejorar.',
    'Faculty assessment decision':
        'Decisión de evaluación docente',
    'Faculty confirmation and reopening':
        'Confirmación docente y reapertura',
    'Faculty confirmation is recorded. Continued observations remain available. Review new evidence to maintain confirmation or reopen the objective; both decisions retain its history.':
        'La confirmación docente está registrada. Las observaciones continuas siguen disponibles. Revisa la nueva evidencia para mantener la confirmación o reabrir el objetivo; ambas decisiones conservan su historial.',
    'Faculty confirmation saved for the simulated component.':
        'Confirmación docente guardada para el componente simulado.',
    'Faculty rationale and feedback':
        'Fundamento y retroalimentación docente',
    'Faculty-reviewed evidence from simulated management. This record does not certify completion of a workplace EPA.':
        'Evidencia revisada por docentes, proveniente de manejo simulado. Este registro no certifica que se haya completado una APC en el lugar de trabajo.',
    'From synthetic test runs':
        'De ejecuciones de prueba sintéticas',
    'I reviewed the AI draft and confirmed the assessment fields':
        'Revisé el borrador de IA y confirmé los campos de la evaluación',
    'Latest faculty decision ·':
        'Última decisión docente ·',
    'Maintain confirmation after reviewing the continued evidence':
        'Mantener la confirmación después de revisar la evidencia posterior',
    'No progress changes have been recorded.':
        'No se han registrado cambios en el progreso.',
    'No resident accounts are available yet.':
        'Aún no hay cuentas de residentes disponibles.',
    'Not determined: requires your confirmation':
        'No determinada: requiere tu confirmación',
    'Not enabled: current encounters are not established as offering enough opportunities to observe this objective':
        'No habilitado: no se ha establecido que los encuentros actuales ofrezcan oportunidades suficientes '
        'para observar este objetivo',
    'Objective for faculty decision':
        'Objetivo para decisión docente',
    'Objective observed in this encounter':
        'Objetivo observado en este encuentro',
    'Objective progress':
        'Progreso por objetivo',
    'Objective reopened. Previous observations and the count have been retained.':
        'Objetivo reabierto. Se conservaron las observaciones anteriores y el conteo.',
    'Objective target':
        'Meta del objetivo',
    'Observation continues after the target and after faculty confirmation. New strengths and concerns remain in the record; they never automatically award or revoke achievement. Faculty confirmation concerns the simulated component and does not certify a workplace EPA.':
        'La observación continúa después de la meta y después de la confirmación docente. Las nuevas fortalezas y preocupaciones quedan en el registro; nunca otorgan ni revocan el logro automáticamente. La confirmación docente se refiere al componente simulado y no certifica una APC en el lugar de trabajo.',
    'Observation history ·':
        'Historial de observaciones ·',
    'Observed autonomy':
        'Autonomía observada',
    'Observed clinical context':
        'Contexto clínico observado',
    'Observed depth':
        'Profundidad observada',
    'Only assess what the recorded encounter demonstrates. Unobserved actions and skills outside this scope are not credited.':
        'Evalúa solo lo que demuestra el encuentro registrado. Las acciones no observadas y las destrezas fuera de este alcance no se acreditan.',
    'Program observation targets':
        'Metas de observación del programa',
    'Program target saved and added to the audit history.':
        'Meta del programa guardada y agregada al historial de auditoría.',
    'Progress audit history':
        'Historial de auditoría del progreso',
    'Read the recorded evidence':
        'Lee la evidencia registrada',
    'Reason for faculty decision':
        'Motivo de la decisión docente',
    'Reason for target change':
        'Motivo del cambio de meta',
    'Reason for voiding assessment':
        'Motivo para anular la evaluación',
    'Record follow-up decision':
        'Registrar decisión de seguimiento',
    'Record objective assessment':
        'Registrar evaluación del objetivo',
    'Recorded evidence':
        'Evidencia registrada',
    'Reopen objective':
        'Reabrir objetivo',
    'Required satisfactory observations':
        'Observaciones satisfactorias requeridas',
    'Resident progress':
        'Progreso del residente',
    'Review each demonstrated objective separately. There is no automatic credit from a completed case, a treatment keyword, or a favorable patient outcome.':
        'Revisa cada objetivo demostrado por separado. No hay crédito automático por un caso completado, una palabra clave de tratamiento ni un resultado favorable del paciente.',
    'Review later concerns':
        'Revisar preocupaciones posteriores',
    'Sandbox and self-assessment encounters do not contribute to resident progress.':
        'Los encuentros de sandbox y de autoevaluación no contribuyen al progreso del residente.',
    'Satisfactory observation saved. You can review another objective from this encounter.':
        'Observación satisfactoria guardada. Puedes revisar otro objetivo de este encuentro.',
    'Satisfactory observations':
        'Observaciones satisfactorias',
    'Satisfactory observations:':
        'Observaciones satisfactorias:',
    'Save program target':
        'Guardar meta del programa',
    'Still needed:':
        'Falta:',
    'Synthetic test run':
        'Ejecución de prueba sintética',
    'Targets are review thresholds. Changing them preserves every observation and the recorded faculty decision; counts may exceed targets.':
        'Las metas son umbrales de revisión. Cambiarlas conserva cada observación y la decisión docente registrada; los conteos pueden superar las metas.',
    'The numeric target alone does not establish achievement. Review consistency, depth, autonomy, and variation of context before confirming the simulated component.':
        'La meta numérica por sí sola no establece el logro. Revisa la consistencia, la profundidad, la autonomía y la variación de contexto antes de confirmar el componente simulado.',
    'The numeric target has not been reached. Confirmation becomes available after the target is reached.':
        'No se ha alcanzado la meta numérica. La confirmación queda disponible una vez que se alcance la meta.',
    'There are no additional eligible objectives to assess for this encounter.':
        'No hay otros objetivos elegibles que evaluar en este encuentro.',
    'These are configurable program targets. One completed encounter may contribute to several objectives. Each objective can receive at most one active observation per encounter. Only faculty-reviewed satisfactory observations increase the counter; depth and autonomy describe that observation without multiplying it.':
        'Estas son metas configurables del programa. Un encuentro completado puede contribuir a varios objetivos. Cada objetivo puede recibir como máximo una observación activa por encuentro. Solo las observaciones satisfactorias revisadas por un docente aumentan el contador; la profundidad y la autonomía describen esa observación sin multiplicarla.',
    'These configurable targets were supplied by the program owner. They have not been independently verified as official EPA observation requirements. A target applies across depth levels; it is not repeated for each level.':
        'Estas metas configurables las proporcionó el responsable del programa. No se han verificado de forma independiente como requisitos oficiales de observación de EPA. Una meta se aplica a todos los niveles de profundidad; no se repite para cada nivel.',
    'They do not meet the required level.':
        'No cumplen el nivel exigido.',
    'This completed encounter has no eligible recorded decisions or complete reflection to assess.':
        'Este encuentro completado no tiene decisiones registradas elegibles ni una reflexión completa que evaluar.',
    'This encounter already has an assessment for that objective; no duplicate was added.':
        'Este encuentro ya tiene una evaluación para ese objetivo; no se agregó un duplicado.',
    'This observation was voided and contributes no credit.':
        'Esta observación fue anulada y no aporta crédito.',
    'To record this objective, complete:':
        'Para registrar este objetivo, completa:',
    'Void an assessment only to correct its record. The original judgment and the reason remain in the audit history. A voided satisfactory observation no longer contributes to the count.':
        'Anula una evaluación solo para corregir su registro. El juicio original y el motivo quedan en el historial de auditoría. Una observación satisfactoria anulada deja de contribuir al conteo.',
    'Void assessment':
        'Anular evaluación',
    'Component this encounter can show: {text}':
        'Componente que este encuentro puede mostrar: {text}',
    'Outside this encounter: {text}':
        'Fuera de este encuentro: {text}',
    'The resident reads this reason on their progress page, beside the original judgment and the notes. Write it for them to read.':
        'La persona residente lee este motivo en su página de progreso, junto al juicio original y las notas. Escríbelo para que lo lea.',
    'This draft does not replace confirmed revision {v0}: the resident, the profile and the radar keep showing that revision until you confirm another.':
        'Este borrador no reemplaza la revisión confirmada {v0}: la persona residente, el perfil y el radar siguen mostrando esa revisión hasta que confirmes otra.',
    'You can save everything else as a draft; nothing is lost.':
        'Puedes guardar todo lo demás como borrador; no se pierde nada.',
    'later observation(s) need improvement. Review the evidence and decide whether the existing confirmation remains appropriate.':
        'observación(es) posterior(es) requieren mejorar. Revisa la evidencia y decide si la confirmación existente sigue siendo adecuada.',
    'observations since confirmation':
        'observaciones desde la confirmación',
    "of them from synthetic test runs, not a person's performance.":
        'de ellas provienen de ejecuciones de prueba sintéticas, no del desempeño de una persona.',
    'of them with an autonomy that could not be determined.':
        'de ellas con una autonomía que no se pudo determinar.',
    "satisfactory observation(s) come from synthetic test runs: an automated agent on a test account. They exercise the simulator and show nothing about a person's performance.":
        'observación(es) satisfactoria(s) provienen de ejecuciones de prueba sintéticas: un agente automatizado en una cuenta de prueba. Ejercitan el simulador y no muestran nada sobre el desempeño de una persona.',
    'satisfactory observations.':
        'observaciones satisfactorias.',
    '· Faculty feedback':
        '· Retroalimentación docente',
    '\nIn use: approved in the visual and clinical reviews over the automated screen':
        '\nEn uso: aprobada en las revisiones visual y clínica, por sobre el cribado automático',
    '\nNot shown, on a reading of the photograph (not a review):':
        '\nNo mostrado, según una lectura de la fotografía (no una revisión):',
    '\nScreen found:':
        '\nEl cribado encontró:',
    'Accepted, with limitations':
        'Aceptada, con limitaciones',
    'Being prepared':
        'En preparación',
    'Clinical review':
        'Revisión clínica',
    'Decision (for a review)':
        'Decisión (para una revisión)',
    'Each change in what the encounter room showed. Without a photograph the room showed its neutral view, with the monitor and the examination current; a finding the photograph could not show was stated beside it.':
        'Cada cambio en lo que mostró la sala del encuentro. Sin fotografía, la sala mostró su vista neutra, con el monitor y el examen actualizados; un hallazgo que la fotografía no podía mostrar se indicó a su lado.',
    'No usable photograph of this person.':
        'No hay una fotografía utilizable de esta persona.',
    'None (failed)':
        'Ninguna (falló)',
    'Not discernible':
        'No discernible',
    'Not screened yet':
        'Aún sin cribado',
    'Patient image bank (faculty)':
        'Banco de imágenes de pacientes (docentes)',
    'Recorded with your account.':
        'Registrado con tu cuenta.',
    'Show rejected and excluded images too':
        'Mostrar también las imágenes rechazadas y excluidas',
    'Synthetic people and the photographs the encounter room shows. The automated screen is a check, not an approval: the visual and clinical reviews below are recorded with the account that records them. Nothing here is a real patient.':
        'Personas sintéticas y las fotografías que muestra la sala del encuentro. El cribado automático es una verificación, no una aprobación: las revisiones visual y clínica de más abajo se registran con la cuenta que las registra. Nada de esto corresponde a un paciente real.',
    'The bank is empty.':
        'El banco está vacío.',
    'Visual review':
        'Revisión visual',
    'What you looked at and why':
        'Qué revisaste y por qué',
    'breathing effort not discernible':
        'esfuerzo respiratorio no discernible',
    'degree of distress not shown':
        'grado de angustia no mostrado',
    'level of consciousness not shown':
        'nivel de conciencia no mostrado',
    'mild pallor not discernible':
        'palidez leve no discernible',
    'mild sweat not discernible':
        'sudoración leve no discernible',
    'no respiratory support':
        'sin soporte respiratorio',
    'skin colour not shown':
        'color de piel no mostrado',
    'sweating not shown':
        'sudoración no mostrada',
    'unknown identity':
        'identidad desconocida',
    'Access is temporarily closed. The account mode is not configured correctly.':
        'El acceso está cerrado temporalmente. El modo de cuentas no está configurado correctamente.',
    'Account access is temporarily unavailable. Ask the administrator to configure persistent account storage.':
        'El acceso a las cuentas no está disponible temporalmente. Pide al administrador que configure el almacenamiento persistente de cuentas.',
    'Account access is temporarily unavailable. Please contact the application administrator.':
        'El acceso a las cuentas no está disponible temporalmente. Contacta al administrador de la aplicación.',
    'Account access is temporarily unavailable. Please try again later.':
        'El acceso a las cuentas no está disponible temporalmente. Inténtalo de nuevo más tarde.',
    'Account access is temporarily unavailable. The administrator account configuration is incomplete.':
        'El acceso a las cuentas no está disponible temporalmente. La configuración de la cuenta de administrador está incompleta.',
    'Account access requires persistent database storage. Local test storage is not enabled for this deployment.':
        'El acceso a las cuentas requiere almacenamiento persistente en base de datos. El almacenamiento local de prueba no está habilitado en este despliegue.',
    'Account active':
        'Cuenta activa',
    'Account administration':
        'Administración de cuentas',
    'Account storage is temporarily unavailable.':
        'El almacenamiento de cuentas no está disponible temporalmente.',
    'Account updated. The user must sign in again.':
        'Cuenta actualizada. El usuario debe volver a iniciar sesión.',
    'Administrator access is required to manage accounts.':
        'Se requiere acceso de administrador para administrar cuentas.',
    'At least 12 characters. Signing in again will be required everywhere else you are signed in.':
        'Al menos 12 caracteres. Deberás volver a iniciar sesión en todos los demás lugares donde tengas la sesión iniciada.',
    'Change password':
        'Cambiar contraseña',
    'Change your password':
        'Cambia tu contraseña',
    "Changing access invalidates this user's existing sessions.":
        'Cambiar el acceso invalida las sesiones existentes de este usuario.',
    'Choose a password':
        'Elige una contraseña',
    'Choose a password with at least 12 characters.':
        'Elige una contraseña de al menos 12 caracteres.',
    'Choose a username':
        'Elige un nombre de usuario',
    'Confirm password':
        'Confirma la contraseña',
    'Copy this invitation and share it privately:':
        'Copia esta invitación y compártela en privado:',
    'Create account':
        'Crear cuenta',
    'Create invitation':
        'Crear invitación',
    'Current password':
        'Contraseña actual',
    'Hide invitation':
        'Ocultar invitación',
    'Individual accounts are not enabled for this deployment.':
        'Las cuentas individuales no están habilitadas en este despliegue.',
    'Invitation code':
        'Código de invitación',
    'Invitations define access privileges. Send each invitation privately to its intended user.':
        'Las invitaciones definen los privilegios de acceso. Envía cada invitación en privado a su destinatario.',
    'Manage an account':
        'Administrar una cuenta',
    'Password changed. Other sessions were signed out.':
        'Contraseña cambiada. Se cerraron las demás sesiones.',
    'Repeat the new password':
        'Repite la nueva contraseña',
    'Resident year':
        'Año de residencia',
    'Sign in to continue your training. New accounts require an invitation.':
        'Inicia sesión para continuar tu formación. Las cuentas nuevas requieren una invitación.',
    'The passwords do not match.':
        'Las contraseñas no coinciden.',
    'The two new passwords do not match.':
        'Las dos contraseñas nuevas no coinciden.',
    'Training year':
        'Año de formación',
    'Unable to create an invitation. Check your administrator access.':
        'No se pudo crear la invitación. Revisa tu acceso de administrador.',
    'Unable to create this account. Check that your username is available and your invitation is valid.':
        'No se pudo crear esta cuenta. Verifica que tu nombre de usuario esté disponible y que tu invitación sea válida.',
    'Unable to sign in. Check your credentials or try again later.':
        'No se pudo iniciar sesión. Revisa tus credenciales o inténtalo de nuevo más tarde.',
    'Unable to update this account. At least one active administrator must remain.':
        'No se pudo actualizar esta cuenta. Debe quedar al menos un administrador activo.',
    'Use a unique password with at least 12 characters. Your invitation determines your role and training year.':
        'Usa una contraseña única de al menos 12 caracteres. Tu invitación determina tu rol y tu año de formación.',
    'Your session has ended. Please sign in again.':
        'Tu sesión terminó. Vuelve a iniciar sesión.',
    'opening the account store failed at administrator bootstrap: %s: %s':
        'la apertura del almacén de cuentas falló al inicializar el administrador: %s: %s',
    'opening the account store failed at connection: %s: %s':
        'la apertura del almacén de cuentas falló en la conexión: %s: %s',
    'A pilot instrument. These are not ACGME Milestone levels, Canadian stages or EPA supervision levels, and they neither feed nor replace the objective record above. Only assessments a faculty member has confirmed appear here.':
        'Un instrumento piloto. No son niveles de Milestone de ACGME, etapas canadienses ni niveles de supervisión de APC, y no alimentan ni reemplazan el registro de objetivos de más arriba. Aquí solo aparecen las evaluaciones que un docente ha confirmado.',
    "Administrators may choose any resident's next case. A faculty member may choose only the cases of the residents authorized here. Each authorization keeps its reason, and a revoked one stays in the history.":
        'Los administradores pueden elegir el próximo caso de cualquier residente. Un docente solo puede elegir los casos de los residentes autorizados aquí. Cada autorización conserva su motivo, y una revocada queda en el historial.',
    'As usual: the application chooses':
        'Como de costumbre: la aplicación elige',
    'Authorizing needs at least one faculty account and one resident account.':
        'Para autorizar se necesita al menos una cuenta docente y una cuenta de residente.',
    'Awaiting your review':
        'Esperando tu revisión',
    'Begin Encounter':
        'Comenzar encuentro',
    'Case preparation diagnostics':
        'Diagnósticos de preparación del caso',
    'Case to open (faculty review)':
        'Caso para abrir (revisión docente)',
    'Changes requested':
        'Cambios solicitados',
    'Clinical and cognitive catalog':
        'Catálogo clínico y cognitivo',
    'Clinical encounters':
        'Encuentros clínicos',
    'Clinical review of the hypoglycemia catalogue (faculty)':
        'Revisión clínica del catálogo de hipoglicemia (docentes)',
    'Cognitive focus':
        'Foco cognitivo',
    'Cognitive focus:':
        'Foco cognitivo:',
    'Compatible and tested are computed by the code (docs/CATALOGO_HIPOGLICEMIA.md). A clinical review is yours alone: it is recorded with your account and refers to this version of the configuration; a clinically relevant change later asks for a new one.':
        'Compatible y probado los calcula el código (docs/CATALOGO_HIPOGLICEMIA.md). La revisión clínica es solo tuya: se registra con tu cuenta y se refiere a esta versión de la configuración; un cambio clínicamente relevante posterior pide una nueva.',
    'Complete encounter record and export':
        'Registro completo del encuentro y exportación',
    "Direct a resident's next encounter":
        'Dirigir el próximo encuentro de un residente',
    "Discard this tab's unsaved changes and reopen dashboard":
        'Descartar los cambios no guardados de esta pestaña y volver a abrir el panel',
    'Download case preparation diagnostic':
        'Descargar diagnóstico de preparación del caso',
    'Download faculty record':
        'Descargar registro docente',
    'Download report':
        'Descargar informe',
    'Download your complete record':
        'Descarga tu registro completo',
    'Encounter record':
        'Registro del encuentro',
    'Faculty member':
        'Docente',
    'Faculty sandbox':
        'Sandbox docente',
    'Last reviewer':
        'Último revisor',
    'Learning focus':
        'Foco de aprendizaje',
    'Learning focus for this encounter':
        'Foco de aprendizaje de este encuentro',
    'Load saved generation failures':
        'Cargar las fallas de generación guardadas',
    'Manage the patient, explain your reasoning, and reassess as the encounter evolves. Your learning focus will be discussed after the encounter.':
        'Maneja al paciente, explica tu razonamiento y reevalúa a medida que evoluciona el encuentro. Tu foco de aprendizaje se discutirá después del encuentro.',
    'Management challenge':
        'Desafío de manejo',
    'Management reasoning rubric profile':
        'Perfil de la rúbrica de razonamiento de manejo',
    'Mechanism · access · severity':
        'Mecanismo · acceso · gravedad',
    'New AI-authored clinical case':
        'Nuevo caso clínico escrito por IA',
    'No resident account exists yet.':
        'Aún no existe ninguna cuenta de residente.',
    'No resident has been assigned to you for choosing cases. An administrator can authorize it.':
        'No se te ha asignado ningún residente para elegirle casos. Un administrador puede autorizarlo.',
    'No saved generation failures.':
        'No hay fallas de generación guardadas.',
    'Not assessed automatically':
        'No se evalúa automáticamente',
    'Opened for clinical review in the sandbox: no generation, no picture, and never offered to residents.':
        'Abierto para revisión clínica en el sandbox: sin generación, sin imagen y nunca ofrecido a los residentes.',
    'Previous completed reviews':
        'Revisiones completadas anteriores',
    'Record clinical review':
        'Registrar revisión clínica',
    'Resident activity and recorded evidence':
        'Actividad del residente y evidencia registrada',
    'Resident to authorize for':
        'Residente para el que se autoriza',
    'Resume encounter':
        'Retomar encuentro',
    'Review outdated':
        'Revisión desactualizada',
    'Review recorded.':
        'Revisión registrada.',
    'Reviewed (approved)':
        'Revisado (aprobado)',
    'Revoked by an administrator from the dashboard.':
        'Revocada por un administrador desde el panel.',
    'Save directive':
        'Guardar directiva',
    "Saved. The resident's next encounter will use this case.":
        'Guardado. El próximo encuentro del residente usará este caso.',
    'Show the history of directives':
        'Mostrar el historial de directivas',
    'Single-program pilot. These are activity records and evidence prompts for faculty review, not competency scores.':
        'Piloto de un solo programa. Estos son registros de actividad y orientaciones sobre la evidencia para la revisión docente, no puntajes de competencia.',
    'Support report:':
        'Informe de soporte:',
    'The linked encounter is not available to this account. Select an available encounter below.':
        'El encuentro enlazado no está disponible para esta cuenta. Selecciona un encuentro disponible más abajo.',
    "The resident's next launch uses this case instead of the curriculum's choice, once. Who chose it and why stay in this history, for faculty; the resident is not told that the case was chosen, which one it is, or why. Without a directive the curriculum decides, exactly as before.":
        'El próximo inicio del residente usa este caso en lugar de la elección del currículo, una sola vez. Quién lo eligió y por qué quedan en este historial, para los docentes; al residente no se le informa que el caso fue elegido, cuál es ni por qué. Sin una directiva, decide el currículo, exactamente como antes.',
    'The support report could not be saved. The failure remains in this session.':
        'No se pudo guardar el informe de soporte. La falla sigue en esta sesión.',
    "These are formative teaching opportunities. The catalog does not diagnose a learner's cognitive bias or establish competence.":
        'Estas son oportunidades de enseñanza formativa. El catálogo no diagnostica el sesgo cognitivo de un estudiante ni establece competencia.',
    'This local curriculum mapping supports formative faculty review. Completing a case does not establish competence.':
        'Esta correspondencia local con el currículo apoya la revisión docente formativa. Completar un caso no establece competencia.',
    'What you reviewed and why':
        'Qué revisaste y por qué',
    "Who may choose a resident's cases":
        'Quién puede elegir los casos de un residente',
    'Why this case':
        'Por qué este caso',
    'Why this faculty member':
        'Por qué este docente',
    "You may enter your reasoning and orders in English or Spanish. The patient's information and the feedback are shown in the language set in the sidebar.":
        'Puedes ingresar tu razonamiento y tus indicaciones en inglés o en español. La información del paciente y la retroalimentación se muestran en el idioma seleccionado en la barra lateral.',
    'Your current work remains in this browser session. Resolve the save problem before continuing. If another tab changed this attempt, reopen it from your dashboard.':
        'Tu trabajo actual sigue en esta sesión del navegador. Resuelve el problema de guardado antes de continuar. Si otra pestaña cambió este intento, vuelve a abrirlo desde tu panel.',
    'Your encounter and reflection are saved to your account. Faculty in this pilot program can review them.':
        'Tu encuentro y tu reflexión se guardan en tu cuenta. Los docentes de este programa piloto pueden revisarlos.',
    'Your next clinical encounter':
        'Tu próximo encuentro clínico',
    'challenge objective(s)':
        'objetivo(s) de desafío',
    'nothing pending':
        'nada pendiente',
    '. It is held for your reading because ':
        '. Queda retenido para tu lectura porque ',
    'AI suggestion on record: ':
        'Sugerencia de IA registrada: ',
    'Autonomy the declared context did not allow the AI to propose was left for your confirmation: ':
        'La autonomía que el contexto declarado no permitió proponer a la IA quedó para tu confirmación: ',
    'Written under the faculty-reported context of its time: ':
        'Redactado bajo el contexto informado por el docente en ese momento: ',
    'Written under: ':
        'Redactado bajo: ',
    ' not assessable in this encounter.':
        ' no evaluable en este encuentro.',
    'Acceptable alternatives: ':
        'Alternativas aceptables: ',
    'Does not count when: ':
        'No cuenta cuando: ',
    'Drawn as a gap rather than at the centre, because it is not a zero: ':
        'Se dibuja como un vacío y no en el centro, porque no es un cero: ',
    ' You can save everything else as a draft; nothing is lost.':
        ' Puedes guardar todo lo demás como borrador; no se pierde nada.',
    ' later observation(s) need improvement. Review the evidence and decide whether the existing confirmation remains appropriate.':
        ' observación(es) posterior(es) requieren mejorar. Revisa la evidencia y decide si la confirmación existente sigue siendo adecuada.',
    " of them from synthetic test runs, not a person's performance.":
        ' de ellas provienen de ejecuciones de prueba sintéticas, no del desempeño de una persona.',
    ' of them with an autonomy that could not be determined.':
        ' de ellas con una autonomía que no se pudo determinar.',
    " satisfactory observation(s) come from synthetic test runs: an automated agent on a test account. They exercise the simulator and show nothing about a person's performance.":
        ' observación(es) satisfactoria(s) provienen de ejecuciones de prueba sintéticas: un agente automatizado en una cuenta de prueba. Ejercitan el simulador y no muestran nada sobre el desempeño de una persona.',
    ' satisfactory observations.':
        ' observaciones satisfactorias.',
    ' · Faculty feedback':
        ' · Retroalimentación docente',
    'At confirmation: ':
        'Al confirmar: ',
    'Latest faculty decision · ':
        'Última decisión docente · ',
    'Observation history · ':
        'Historial de observaciones · ',
    'Satisfactory observations: ':
        'Observaciones satisfactorias: ',
    'Cognitive focus: ':
        'Foco cognitivo: ',
    'Download report ':
        'Descargar informe ',
    'Support report: ':
        'Informe de soporte: ',
    'AI draft: ':
        'Borrador de IA: ',
    'Declaration history ({v0})':
        'Historial de declaraciones ({v0})',
    'Discuss: ':
        'Para conversar: ',
    'Generated ':
        'Generado ',
    '   {v0}: proposed {v1} → {v2} — {v3}':
        '   {v0}: propuesto {v1} → {v2} — {v3}',
    '**Check before deciding: the proposal and the record disagree.**\n\n':
        '**Revisa antes de decidir: la propuesta y el registro no coinciden.**\n\n',
    '**Domain {v0} · {v1}**':
        '**Dominio {v0} · {v1}**',
    '**Domain {v0} · {v1}** — {v2}':
        '**Dominio {v0} · {v1}** — {v2}',
    '**Management reasoning profile** (pilot rubric ':
        '**Perfil de razonamiento de manejo** (rúbrica piloto ',
    'AI proposal {v0} · model {v1} · prompt {v2} · generated {v3}':
        'Propuesta de IA {v0} · modelo {v1} · prompt {v2} · generada {v3}',
    'AI proposes **{v0}**. {v1}':
        'La IA propone **{v0}**. {v1}',
    'Against it: {v0}':
        'En contra: {v0}',
    'At minute {v0}: “{v1}”':
        'Al minuto {v0}: «{v1}»',
    'Available on asking — {v0} ({v1}): {v2}. The patient answers for the whole encounter, so this was available either way; not asking is part of the omission, not an excuse for it.':
        'Disponible al preguntar — {v0} ({v1}): {v2}. El paciente responde durante todo el encuentro, así que esto estaba disponible de todos modos; no preguntar es parte de la omisión, no una excusa para ella.',
    'Descriptors for domain {v0}':
        'Descriptores del dominio {v0}',
    'Domain {v0} · {v1}':
        'Dominio {v0} · {v1}',
    'Encounters included: {v0} (confirmed, rubric {v1}).':
        'Encuentros incluidos: {v0} (confirmados, rúbrica {v1}).',
    'For the next level: {v0}':
        'Para el siguiente nivel: {v0}',
    'Individual results ({v0})':
        'Resultados individuales ({v0})',
    'Lowest mean: domain {v0} · {v1}. This is where the shape is pulled in, not a judgement about the resident.':
        'Media más baja: dominio {v0} · {v1}. Es donde la figura se contrae, no un juicio sobre el residente.',
    'Mean adjusted total {v0}/{v1} over {v2} encounter(s) where all five domains were assessable. Partial assessments keep their events but have no comparable total.':
        'Total ajustado medio {v0}/{v1} en {v2} encuentro(s) en que los cinco dominios fueron evaluables. Las evaluaciones parciales conservan sus eventos pero no tienen un total comparable.',
    'No rubric coverage is declared for {v0}. Scores remain available; no critical event is defined for this case.':
        'No hay cobertura de rúbrica declarada para {v0}. Los puntajes siguen disponibles; no hay eventos críticos definidos para este caso.',
    'Record: {v0}':
        'Registro: {v0}',
    'Revision history ({v0})':
        'Historial de revisiones ({v0})',
    'Revision {v0} · {v1} · {v2} · {v3}':
        'Revisión {v0} · {v1} · {v2} · {v3}',
    'Save draft':
        'Guardar borrador',
    'Saved as revision {v0} · {v1}':
        'Guardado como revisión {v0} · {v1}',
    'Triggers when: {v0} · Window {v1}–{v2} min':
        'Se activa cuando: {v0} · Ventana {v1}–{v2} min',
    'Why you changed it from the proposed {v0}':
        'Por qué lo cambiaste respecto del {v0} propuesto',
    'Your score':
        'Tu puntaje',
    '{v0} The rubric assessment remains pending.':
        '{v0} La evaluación por rúbrica sigue pendiente.',
    "{v0} completed encounter(s) await a faculty member's confirmation and are not included: a suggestion is not a result.":
        '{v0} encuentro(s) completado(s) esperan la confirmación de un docente y no se incluyen: una sugerencia no es un resultado.',
    '{v0} confirmed critical event(s) across these encounters. A safety event is counted, never averaged into a domain.':
        '{v0} evento(s) crítico(s) confirmado(s) en estos encuentros. Un evento de seguridad se cuenta, nunca se promedia dentro de un dominio.',
    '{v0} encounter(s) confirmed under rubric {v1} are listed below and not averaged in: the two scales are not assumed to be the same.':
        '{v0} encuentro(s) confirmado(s) con la rúbrica {v1} se listan abajo y no se promedian: no se asume que ambas escalas sean iguales.',
    '{v0}: proposed {v1} → {v2} — {v3}':
        '{v0}: propuesto {v1} → {v2} — {v3}',
    '⚠ {v0} · confirmed {v1}':
        '⚠ {v0} · confirmado {v1}',
    'Draft {v0} saved by {v1}. Still needed to confirm:':
        'Borrador {v0} guardado por {v1}. Falta para confirmar:',
    'Draft {v0} saved by {v1}. Still needed to confirm: ':
        'Borrador {v0} guardado por {v1}. Falta para confirmar: ',
    "**Budget `{v0}`** · committed {v1} of {v2} ({v3} from the provider's reported usage, {v4} estimated, {v5} reserved in flight) · image requests {v6} of {v7} · retries {v8}":
        '**Presupuesto `{v0}`** · comprometido {v1} de {v2} ({v3} según el uso informado por el proveedor, {v4} estimado, {v5} reservado en curso) · solicitudes de imagen {v6} de {v7} · reintentos {v8}',
    "Budget `{v0}` (not the one this app spends from) · committed {v1} of {v2} ({v3} from the provider's reported usage, {v4} estimated) · image requests {v5} of {v6} · retries {v7}":
        'Presupuesto `{v0}` (no es el que usa esta aplicación) · comprometido {v1} de {v2} ({v3} según el uso informado por el proveedor, {v4} estimado) · solicitudes de imagen {v5} de {v6} · reintentos {v7}',
    'Image':
        'Imagen',
    'Patient image · what the room showed ({v0})':
        'Imagen del paciente · lo que mostró la sala ({v0})',
    'Record':
        'Registrar',
    '{v0} · {v1}  \nScreen: {v2}{v3} · visual review {v4} · clinical review {v5}':
        '{v0} · {v1}  \nCribado: {v2}{v3} · revisión visual {v4} · revisión clínica {v5}',
    'Invite role':
        'Rol de la invitación',
    'New password':
        'Nueva contraseña',
    'Password':
        'Contraseña',
    'Role':
        'Rol',
    'Save account':
        'Guardar cuenta',
    'Sign in':
        'Iniciar sesión',
    'Sign out':
        'Cerrar sesión',
    'Signed in':
        'Sesión iniciada',
    'Username':
        'Usuario',
    'Authorize':
        'Autorizar',
    'Authorized.':
        'Autorizado.',
    'Cancel':
        'Cancelar',
    'Case':
        'Caso',
    'Challenge':
        'Desafío',
    'Configuration':
        'Configuración',
    'Decision':
        'Decisión',
    'Encounter review · {v0}':
        'Revisión del encuentro · {v0}',
    'Navigation':
        'Navegación',
    'Open review':
        'Abrir revisión',
    'Resident':
        'Residente',
    'Retry save':
        'Reintentar guardado',
    'Revoke':
        'Revocar',
    'These encounters are excluded from resident progress. {v0} challenges are available.':
        'Estos encuentros se excluyen del progreso del residente. Hay {v0} desafíos disponibles.',
    'Training year {v0} · {v1} completed encounter reviews':
        'Año de formación {v0} · {v1} revisiones de encuentro completadas',
    'Waiting: {v0} · {v1} · {v2} · by {v3} · {v4}':
        'En espera: {v0} · {v1} · {v2} · por {v3} · {v4}',
    '{v0}: {v1} → {v2} · by {v3} · {v4}':
        '{v0}: {v1} → {v2} · por {v3} · {v4}',
    ' - declared by the ':
        ' - declarado por el ',
    ' - nobody has declared it yet':
        ' - nadie lo ha declarado aún',
    '. Help described: ':
        '. Ayuda descrita: ',
    ' (not averaged)':
        ' (no promediado)',
    '**never asked about**':
        '**nunca se preguntó**',
    'partial {v0} ({v1}/5)':
        'parcial {v0} ({v1}/5)',
    ' Before recording, confirm your review of the AI draft.':
        ' Antes de registrar, confirma que revisaste el borrador de IA.',
    ' Still needed: ':
        ' Falta: ',
    ' They do not meet the required level.':
        ' No alcanzan el nivel requerido.',
    ' at {level} or above ({count} satisfactory)':
        ' en nivel {level} o superior ({count} satisfactorias)',
    ' observations since confirmation':
        ' observaciones desde la confirmación',
    'Could not be determined: the record does not let you judge it. It is not a negative result and not independence.':
        'No se pudo determinar: el registro no permite juzgarla. No es un resultado negativo ni equivale a independencia.',
    'Pending':
        'Pendiente',
    'To record this objective, complete: ':
        'Para registrar este objetivo, completa: ',
    'nothing':
        'nada',
    'Excluded: ':
        'Excluida: ',
    'In use: approved in the visual and clinical reviews over the automated screen':
        'En uso: aprobada en las revisiones visual y clínica por sobre el cribado automático',
    'Not shown, on a reading of the photograph (not a review): ':
        'No se muestra, según una lectura de la fotografía (no una revisión): ',
    'Screen found: ':
        'El cribado encontró: ',
    ' ({fields} changed)':
        ' (cambió: {fields})',
    ' challenge objective(s)':
        ' objetivo(s) de desafío',
    ' · revoked: {reason}':
        ' · revocada: {reason}',
    'Foundational':
        'Básica',
    'Integrated':
        'Integrada',
    'Complex':
        'Compleja',
    'Guided':
        'Guiada',
    'Prompted':
        'Con orientación',
    'Independent':
        'Independiente',
    'Satisfactory':
        'Satisfactoria',
    'Requires faculty review':
        'Requiere revisión docente',
    'A focused management decision with explicit supporting evidence.':
        'Una decisión de manejo focalizada, con evidencia de apoyo explícita.',
    'Related decisions integrating response, reassessment, and competing priorities.':
        'Decisiones relacionadas que integran respuesta, reevaluación y prioridades en competencia.',
    'Management reasoning under uncertainty or evolving, competing clinical problems.':
        'Razonamiento de manejo frente a incertidumbre o a problemas clínicos que evolucionan y compiten.',
    'Faculty or structured guidance directed the management reasoning.':
        'Un docente o una guía estructurada dirigió el razonamiento de manejo.',
    'Prompts were needed before the resident completed the reasoning.':
        'Se necesitó orientación antes de que el residente completara el razonamiento.',
    'The observed reasoning was completed without additional guidance or prompts.':
        'El razonamiento observado se completó sin guía ni orientación adicionales.',
    'the decision':
        'la decisión',
    'the depth':
        'la profundidad',
    'the autonomy (a level, or that it could not be determined)':
        'la autonomía (un nivel, o que no se pudo determinar)',
    'the clinical context':
        'el contexto clínico',
    'the supporting evidence':
        'la evidencia de apoyo',
    'the rationale and feedback':
        'el fundamento y la retroalimentación',
    'Anchor':
        'Ancla',
    'State':
        'Estado',
    'Active':
        'Activa',
    'Revoked':
        'Revocada',
    'yes':
        'sí',
    'Photograph':
        'Fotografía',
    'None':
        'Ninguna',
    'Exclude':
        'Excluir',
    'Bring back':
        'Restituir',
    'My progress':
        'Mi progreso',
    'Objective':
        'Objetivo',
    'Depth':
        'Profundidad',
    'Autonomy':
        'Autonomía',
    'Confirmed':
        'Confirmado',
    'Alerts':
        'Alertas',
    'Rubric':
        'Rúbrica',
    'Follow-up':
        'Seguimiento',
    'Scope':
        'Alcance',
    'Minute':
        'Minuto',
    'Shown':
        'Mostrada',
    'Why none':
        'Por qué ninguna',
    'Person':
        'Persona',
    'Origin':
        'Origen',
    'Saved':
        'Guardado',
    'By':
        'Por',
    'Why':
        'Por qué',
    'Code':
        'Código',
    'Scenario':
        'Escenario',
    'Competencies':
        'Competencias',
    'Updated':
        'Actualizado',
    'Not available':
        'No disponible',
    'Deleted.':
        'Eliminado.',
    'Save':
        'Guardar',
    'Saved.':
        'Guardado.',
    'Descriptors a faculty member has not yet approved in Spanish are shown in English.':
        'Los descriptores que un docente aún no aprueba en español se muestran en inglés.',
    'D4 assesses monitoring and reassessment; D5 assesses how that information is used to adapt the management or justifiably keep it, and to secure its continuity.':
        'D4 evalúa monitorización y reevaluación; D5 evalúa cómo se utiliza esa información para adaptar o mantener justificadamente el manejo y asegurar su continuidad.',
    'Developing':
        'En desarrollo',
    'Not observed':
        'No observado',
    'Target reached':
        'Meta alcanzada',
}
TABLES = {"es": ES}
