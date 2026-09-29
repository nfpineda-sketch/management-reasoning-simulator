"""Every intentional correction, with its scope, its reason, the versions it affects and its tests.

Faculty instruction of 2026-09-25: a correction is incorporated where it
belongs -- the shared engine, the generation constraints, the checks of
generated cases or the evaluation -- with an explicit scope (general, one
family or one variant) and the regression tests that hold it in place, and it
is kept in the application rather than in a conversation.

This registry is that record, read by code:

* ``test_corrections_registry`` checks that every entry names its scope,
  reason and versions, and that every test it cites exists;
* ``test_hypoglycemia_preservation`` accepts exactly the differences against
  the record of 2026-09-25 that an entry here declares, and nothing else;
* ``catalog_reviews`` reads the entries declared ``cosmetic``: only those
  leave a faculty member's clinical review of a configuration standing when
  its fingerprint changes. Any other change asks for a new review.

``clinical_relevance`` is ``clinical`` (it changes what happens to a patient,
what a case says, or how an encounter is judged), ``cosmetic`` (wording only),
or ``none`` (code organisation with identical behaviour, proved by a test).

``authorised_by`` names the instruction under which the change was made. It
is not a clinical approval of the result: no entry here records anyone's
approval of a clinical parameter or criterion, and none may.
"""

SCOPES = ("general", "family", "variant")
KINDS = ("technical_defect", "clinical_decision_applied", "text", "refactor", "policy")
RELEVANCE = ("clinical", "cosmetic", "none")
INSTRUCTION_2026_09_25 = "Instrucción docente del 2026-09-25 (etapas 0-2 del catálogo de hipoglicemia)"
INSTRUCTION_2026_09_27 = ("Instrucción docente del 2026-09-27 (peso y talla; decisiones A, B y F; "
                          "compatibilidad visual amplia)")
INSTRUCTION_2026_09_26B = ("Instrucción docente del 2026-09-26 (cierre de jugabilidad, unificación de "
                           "recorridos, fidelidad del registro y alcance de la evaluación)")
INSTRUCTION_2026_09_26C = ("Instrucción docente del 2026-09-26 (idioma: un encuentro jugado en español da sus "
                           "documentos en español, uno en inglés en inglés, y lo almacenado se puede ver en "
                           "cualquiera de los dos)")
INSTRUCTION_2026_09_27B = ("Instrucción docente del 2026-09-27 (preparar el borrador en español de los descriptores "
                           "de la rúbrica, para revisión docente antes de usarlo)")
INSTRUCTION_2026_09_27C = ("Instrucción docente del 2026-09-27 (revisión de la traducción de la rúbrica: redacción, "
                           "«indicación» sólo para órdenes clínicas y «orientación» para la ayuda al residente, qué "
                           "cuenta como ayuda al juzgar la autonomía y nota visible D4/D5)")
INSTRUCTION_2026_09_27D = ("Instrucción docente del 2026-09-27 (el idioma del encuentro se fija al iniciarlo y no "
                           "cambia; las pantallas siguen a quien las mira; cada descarga empieza en el idioma del "
                           "encuentro y puede pedirse en el otro)")
INSTRUCTION_2026_09_28 = ("Instrucción docente del 2026-09-28 (ciclo 5 del AI Advisor: activar C14 en los casos "
                          "donde la revisión A–H lo resolvió, dejar acs_54m_inferior sin revisar y corregir KD-01 "
                          "por clase)")
INSTRUCTION_2026_09_28_NIGHT = ("Instrucción docente del 2026-09-28, extensión nocturna del ciclo 5 (59Z y 59BT: "
                                "corregir sólo bugs inequívocos de aislamiento o de persistencia, pequeños, "
                                "reversibles y probados)")
INSTRUCTION_2026_09_28_CYCLE7 = ("Instrucción docente del 2026-09-28, ciclo 7 del AI Advisor (C4 = NO en todo el entorno "
                                 "de observación, C14 NO en acs_54m_inferior, TD-21 con el principio D, TD-26 y C7-06 "
                                 "por clase con el estándar A–J, DF-24 aprobado y DF-23 conservador)")
INSTRUCTION_2026_09_28_CYCLE8 = ("Instrucción docente del 2026-09-28 al cerrar el ciclo 7 (dejar al AI Advisor trabajando en "
                                 "el ciclo 8, con tareas que no requieran mucha aprobación; lo que la requiera, al informe "
                                 "final), sobre la aprobación conceptual de TDFC-1 a 6 y 8 del ciclo 7 (§28)")
INSTRUCTION_2026_09_29_CYCLE9 = ("Instrucción docente del 2026-09-29, ciclo 9 del AI Advisor (endurecimiento previo a la "
                                 "validación externa: TD-39, TD-34, TD-36 y TD-33; DF-20 cerrado sin cambios y las filas "
                                 "TDFC de acs_54m_inferior; la fila 4a de DF-23 si es inequívoca)")
INSTRUCTION_2026_09_29_POST_V3 = ("Instrucción docente del 2026-09-29 posterior a V3 (cerrar e implementar las decisiones "
                                  "clínicas analizadas: TEP con D revisada, DC1, POCUS de la HDA, TD-31, DC2–DC5 de "
                                  "hipoglicemia y el texto de acs_70f_left_main; y las decisiones no clínicas de su "
                                  "ampliación)")
INSTRUCTION_2026_09_28_CYCLE6 = ("Instrucción docente del 2026-09-28, ciclo 6 del AI Advisor (DF-22 por clase, 59O-03 y "
                                 "seguridad de la aclaración, L-F01, L-F04 y sólo las correcciones de DF-23 que "
                                 "cumplen las seis condiciones)")

CORRECTIONS = (
    {
        "id": "C-2026-09-25-01",
        "date": "2026-09-25",
        "title": "Las tres variantes de hipoglicemia se expresan mediante el catálogo",
        "scope": {"level": "family", "family": "hypoglycemia"},
        "kind": "refactor",
        "reason": ("Una sola fuente para las banderas del motor, las pistas descubribles y las declaraciones de "
                   "evaluación, en vez de datos repetidos a mano en el banco y en las declaraciones."),
        "authorised_by": INSTRUCTION_2026_09_25,
        "affects": {"modules": ["hypoglycemia_catalog", "case_catalog", "clinical_cases", "case_assessment_bank"],
                    "versions": {"catalog": {"from": None, "to": "hypoglycemia 1.0.0"}}},
        "clinical_relevance": "none",
        "tests": ["test_hypoglycemia_preservation.py::test_bank_cases_match_the_record_except_declared_corrections",
                  "test_hypoglycemia_preservation.py::test_every_trajectory_matches_the_record_except_declared_corrections",
                  "test_hypoglycemia_catalog.py::test_the_bank_is_three_configurations_of_the_catalogue"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-25-02",
        "date": "2026-09-25",
        "title": "Umbrales de conciencia y pistas del mecanismo de glucosa en un solo lugar",
        "scope": {"level": "general"},
        "kind": "refactor",
        "reason": ("Los umbrales de conciencia estaban escritos en el motor del banco y las pistas de "
                   "descubribilidad en la compuerta de los casos generados; ahora ambos leen glucose_rescue y "
                   "case_cues, y el catálogo deriva de ahí sus bandas de gravedad."),
        "authorised_by": INSTRUCTION_2026_09_25,
        "affects": {"modules": ["glucose_rescue", "family_engine", "generated_metabolic_consistency", "case_cues"],
                    "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_hypoglycemia_preservation.py::test_every_trajectory_matches_the_record_except_declared_corrections",
                  "test_generated_metabolic.py::test_a_declared_sulfonylurea_must_be_in_the_medicines",
                  "test_hypoglycemia_catalog.py::test_the_severity_bands_are_the_engine_thresholds"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-25-03",
        "date": "2026-09-25",
        "title": "El foco docente de hypoglycemia_54m_thiamine contradecía la decisión 8",
        "scope": {"level": "variant", "variants": ["hypoglycemia_54m_thiamine"]},
        "kind": "text",
        "reason": ("'Correct the glucose without precipitating an encephalopathy' y la pregunta 'Which treatment "
                   "did the glucose itself make urgent?' suponían que la glucosa precipita una encefalopatía, lo que "
                   "la decisión docente 8 (2026-09-21) retiró del motor. El foco ahora pone primero reconocer y "
                   "corregir la hipoglicemia y comprobar que subió, y la tiamina como segundo objetivo."),
        "authorised_by": "Instrucción docente del 2026-09-25, punto 5",
        "affects": {"modules": ["hypoglycemia_catalog"], "versions": {"catalog": {"from": None, "to": "hypoglycemia 1.0.0"}}},
        "clinical_relevance": "clinical",
        "tests": ["test_hypoglycemia_catalog.py::test_no_text_of_the_family_says_glucose_precipitates_an_encephalopathy",
                  "test_hypoglycemia_preservation.py::test_bank_cases_match_the_record_except_declared_corrections"],
        "preservation": {"variant": "hypoglycemia_54m_thiamine",
                         "variant_fields": ["/faculty/management_focus", "/faculty/review_questions"]},
    },
    {
        "id": "C-2026-09-25-04",
        "date": "2026-09-25",
        "title": "Lo que la vía fallida agrega al texto docente de cada caso",
        "scope": {"level": "family", "family": "hypoglycemia",
                  "applies_to": "configuraciones con vía fallida"},
        "kind": "text",
        "reason": ("Una vía fallida es parte de lo que el caso enseña: el hallazgo, una frase del foco y una "
                   "pregunta de revisión la nombran, se derive la configuración de donde se derive."),
        "authorised_by": INSTRUCTION_2026_09_25,
        "affects": {"modules": ["hypoglycemia_catalog"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_hypoglycemia_catalog.py::test_a_failed_line_is_named_in_the_faculty_text",
                  "test_hypoglycemia_preservation.py::test_bank_cases_match_the_record_except_declared_corrections"],
        "preservation": {"variant": "hypoglycemia_54m_thiamine",
                         "variant_fields": ["/faculty/discriminating_findings", "/faculty/management_focus",
                                            "/faculty/review_questions"]},
    },
    {
        "id": "C-2026-09-25-05",
        "date": "2026-09-25",
        "title": "hypo_no_thiamine deja de ser un evento crítico; nueva versión de las declaraciones (cobertura 1.1)",
        "scope": {"level": "family", "family": "hypoglycemia",
                  "applies_to": "configuraciones con déficit de tiamina o vía fallida; en el banco, hypoglycemia_54m_thiamine"},
        "kind": "clinical_decision_applied",
        "reason": ("Instrucción docente: el objetivo principal es reconocer y corregir la hipoglicemia, comprobar la "
                   "respuesta y, si no responde, revisar la vía y la entrega efectiva; recordar la tiamina es "
                   "secundario y su omisión aislada no es un evento crítico. La definición vigente la trataba como "
                   "omisión crítica (resta 3 puntos si se confirma) en D3. En la versión 1.1 la tiamina es una "
                   "expectativa secundaria de D3 y la vía fallida una oportunidad de D4, sin evento nuevo. Las "
                   "evaluaciones hechas con 1.0 no se modifican: sus encuentros se juzgan con la base congelada o "
                   "con la instantánea 1.0 (evaluation_basis). La elección del siguiente desafío, que cuenta las "
                   "situaciones críticas nunca vistas (challenge_targeting), ofrece una menos en R1-06 y R1-07."),
        "authorised_by": "Instrucción docente del 2026-09-25, puntos 4 y 5",
        "affects": {"modules": ["hypoglycemia_catalog", "case_assessment_bank", "case_assessment"],
                    "versions": {"coverage": {"from": "1.0", "to": "1.1"}}},
        "clinical_relevance": "clinical",
        "tests": ["test_hypoglycemia_catalog.py::test_thiamine_is_a_second_objective_and_not_a_critical_event",
                  "test_hypoglycemia_catalog.py::test_a_failed_line_is_an_opportunity_and_not_a_new_event",
                  "test_evaluation_basis.py::test_an_encounter_judged_under_1_0_keeps_hypo_no_thiamine",
                  "test_the_next_challenge_targets_what_is_unmet.py::test_what_is_unmet_shrinks_as_situations_are_met"],
        "preservation": {"variant": "hypoglycemia_54m_thiamine", "declaration": "new_version"},
    },
    {
        "id": "C-2026-09-25-06",
        "date": "2026-09-25",
        "title": "Abrir la rúbrica o el análisis de un caso generado no interrumpe el circuito",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Un caso generado se identifica 'AI-…'; case_assessment lanzaba CoverageError y nadie la "
                   "capturaba en la rúbrica, el tamizaje, la propuesta ni la revisión de la historia. Ahora cada "
                   "registro resuelve un estado (generado sin declaraciones, identificador inválido, registro "
                   "dañado…) y se informa su limitación sin inventar cobertura, eventos ni puntajes."),
        "authorised_by": "Instrucción docente del 2026-09-25, punto 7",
        "affects": {"modules": ["evaluation_basis", "rubric_screening", "rubric_analysis", "rubric_store",
                                "rubric_portal", "history_review"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_evaluation_basis.py::test_a_generated_case_is_read_without_declarations_and_without_error",
                  "test_evaluation_basis.py::test_an_invalid_identifier_and_a_corrupt_record_are_told_apart",
                  "test_generated_case_evaluation.py::test_the_rubric_circuit_reads_a_generated_encounter"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-25-07",
        "date": "2026-09-25",
        "title": "Las declaraciones de evaluación se congelan con cada encuentro",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Los análisis leían las declaraciones vigentes del código: un cambio posterior cambiaba en "
                   "silencio cómo se juzgaba un encuentro anterior. Cada encuentro nuevo guarda una copia "
                   "versionada; los anteriores se juzgan con la instantánea 1.0 y lo dicen; una reevaluación con "
                   "criterios nuevos es explícita, con motivo, y conserva la anterior."),
        "authorised_by": "Instrucción docente del 2026-09-25, punto 8",
        "affects": {"modules": ["evaluation_basis", "curriculum_runtime", "rubric_analysis", "rubric_screening",
                                "rubric_store", "history_review"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_evaluation_basis.py::test_a_new_encounter_carries_its_own_frozen_declarations",
                  "test_evaluation_basis.py::test_a_later_change_does_not_change_how_a_frozen_encounter_is_judged",
                  "test_evaluation_basis.py::test_a_reevaluation_is_explicit_and_keeps_the_original"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-25-08",
        "date": "2026-09-25",
        "title": "Sin configuración explícita, sólo el administrador inicia una generación libre",
        "scope": {"level": "general"},
        "kind": "policy",
        "reason": ("Instrucción docente: mantener la generación libre restringida al sandbox del administrador "
                   "durante esta etapa. Antes, una aplicación sin MRS_PAID_GENERATION la abría a todas las cuentas. "
                   "Ahora las demás cuentas inician un caso del banco (o el caso guardado de B1) y conservan lo que "
                   "MRS_PAID_GENERATION les permite, la imagen del paciente incluida: la regla B1 no cambió. "
                   "MRS_FREE_GENERATION=all la reabre de forma explícita, nunca más allá de B1 ni del modo sin "
                   "conexión."),
        "authorised_by": "Instrucción docente del 2026-09-25 (entrega esperada)",
        "affects": {"modules": ["offline_cases"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_paid_generation_gate.py::test_free_generation_stays_in_the_administrator_s_sandbox",
                  "test_paid_generation_gate.py::test_free_generation_never_opens_what_the_paid_rule_closes",
                  "test_paid_generation_gate.py::test_admin_only_lets_the_administrator_through"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-25-09",
        "date": "2026-09-25",
        "title": "El lector: la infusión al 10 % en español y la glucosa escrita como solución",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Hallado en las verificaciones focalizadas del lector: 'inicio infusión de dextrosa al 10% a "
                   "100 mL/h' se leía como un bolo de 10 g (10 % de 100 mL), 'SG 10% a 100 ml/h' y 'Suero "
                   "glucosado al 10%...' no se reconocían, y 'D50 50 mL IV' o 'Dextrosa al 50% 50 mL EV' se "
                   "perdían sin aviso. Ahora son la infusión y la ampolla que dicen ser. Las brechas que quedan "
                   "están listadas y probadas como fallas esperadas."),
        "authorised_by": "Instrucción docente del 2026-09-25, punto 6",
        "affects": {"modules": ["family_parser"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_hypoglycemia_reader.py::test_the_ten_percent_infusion",
                  "test_hypoglycemia_reader.py::test_the_ampoule",
                  "test_hypoglycemia_reader.py::test_known_gaps_of_the_reader"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-01",
        "date": "2026-09-26",
        "title": "El panel de la rúbrica conserva sus botones, la telaraña su etiqueta superior y el rechazo nombra el evento",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Visto en la app de desarrollo al revisar un encuentro de la tanda: copias atenuadas de «Save "
                   "draft» y «Confirm assessment» bajo el rechazo (cada dominio «no evaluable» agrega un campo y la "
                   "fila de botones cambiaba de lugar entre recargas), «Severity» cortada por el borde del dibujo, "
                   "y un rechazo que no decía qué evento. La regla no cambió: confirmar un evento que el registro "
                   "contradice exige un motivo escrito."),
        "authorised_by": "Instrucción docente del 2026-09-26 (captura del panel de rúbrica)",
        "affects": {"modules": ["rubric_portal", "rubric_radar", "rubric_store"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_rubric_portal.py::test_the_buttons_keep_their_place_while_domains_change",
                  "test_rubric_radar.py::test_the_label_at_the_top_is_inside_the_drawing",
                  "test_the_record_settles_what_it_can.py::test_confirming_an_event_the_record_contradicts_needs_a_written_reason"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-02",
        "date": "2026-09-26",
        "title": "«My progress» reconstruye el Management Trace del residente desde el análisis guardado",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Escenario 1 de la tanda: «No AI reading of this encounter was saved» junto a un análisis "
                   "guardado y válido. El portal del residente comprobaba el análisis contra el registro completo "
                   "y no contra la evidencia congelada con que se escribió y guardó."),
        "authorised_by": "Instrucción docente del 2026-09-26 (pendientes técnicos durante la noche)",
        "affects": {"modules": ["resident_portal"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_the_resident_gets_their_management_trace.py::test_my_progress_rebuilds_the_saved_management_trace",
                  "test_the_resident_gets_their_management_trace.py::test_an_encounter_without_a_saved_analysis_still_says_so"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-03",
        "date": "2026-09-26",
        "title": "El lector: órdenes de glucosa, vías e interconsultas escritas como en una ficha",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Brechas técnicas de las verificaciones focalizadas del lector, sin decisión clínica: «Glucosa "
                   "capilar», «Nueva vía venosa» y «2 VVP» sin verbo se perdían; «Bolo de…» se devolvía como "
                   "ilegible; «glucosado» no nombraba el agente; «2 ampollas de glucosado al 30%» se perdía sin "
                   "aviso y «2 ampollas… 20 mL cada una» se leía como una; «suero glucosado al 5% a 100 mL/h» se "
                   "leía como la infusión al 10 % y ahora queda indicado, sin efecto modelado (decisión 3); "
                   "«Consulto a endocrinología» preguntaba qué especialista. Las etiquetas de interconsulta se leen "
                   "en español. Quedan como brechas la vía intraósea (DC3) y revisar la vía (DC2)."),
        "authorised_by": "Instrucción docente del 2026-09-26 (pendientes técnicos durante la noche)",
        "affects": {"modules": ["family_parser", "language"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_hypoglycemia_reader.py::test_orders_written_as_on_a_chart",
                  "test_hypoglycemia_reader.py::test_a_line_the_patient_has_is_not_an_order_for_a_new_one",
                  "test_hypoglycemia_reader.py::test_glucose_written_as_a_bolus_or_by_the_ampoule",
                  "test_hypoglycemia_reader.py::test_ampoules_with_no_volume_are_an_order_whose_dose_is_asked_for",
                  "test_hypoglycemia_reader.py::test_ampoules_whose_volume_may_be_the_total_or_each_ask_for_the_total",
                  "test_hypoglycemia_reader.py::test_a_glucose_infusion_the_engine_does_not_run_is_recorded_not_converted",
                  "test_hypoglycemia_reader.py::test_the_rest_of_the_submission_runs_beside_an_infusion_that_is_not_modelled",
                  "test_presentation_language.py::test_a_consult_reads_in_spanish_whatever_the_service"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-04",
        "date": "2026-09-26",
        "title": "La página docente pregunta menos a la base: de 20 a 12 transacciones por cambio en la rúbrica",
        "scope": {"level": "general"},
        "kind": "refactor",
        "reason": ("Cada recarga de Streamlit construye de nuevo cada almacén, y cada uno volvía a ejecutar sus "
                   "CREATE TABLE IF NOT EXISTS; el panel de rúbrica y el contexto de asistencia leían dos veces el "
                   "mismo historial. Con la base remota de la app de desarrollo eso era la mayor parte de la "
                   "espera entre un cambio y la página asentada. Ahora cada almacén crea o migra sus tablas una vez "
                   "por proceso y por base (una base SQLite nueva o vacía se vuelve a revisar), y cada historial se "
                   "lee una vez. Mismo comportamiento: medido en local con un registro del ensayo, 20 → 12."),
        "authorised_by": "Instrucción docente del 2026-09-26 (reducir las transacciones de la página docente)",
        "affects": {"modules": ["account_store", "rubric_store", "progress_store", "resident_profile",
                                "faculty_analysis_store", "encounter_context", "management_trace_store",
                                "catalog_reviews", "encounter_directives", "rubric_portal", "faculty_portal"],
                    "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_the_faculty_page_asks_the_database_less.py::test_a_store_creates_its_tables_once_per_database",
                  "test_the_faculty_page_asks_the_database_less.py::test_another_database_still_gets_its_tables",
                  "test_the_faculty_page_asks_the_database_less.py::test_a_database_made_again_at_the_same_path_gets_its_tables_again",
                  "test_the_faculty_page_asks_the_database_less.py::test_the_rubric_panel_reads_its_revisions_once_per_rerun",
                  "test_progress_store.py::test_existing_confirmation_migrates_before_same_second_continued_evidence"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-05",
        "date": "2026-09-26",
        "title": "La sala pagaba la imagen del paciente aunque la regla B1 negara el gasto a ese rol",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("El lanzamiento retiene la clave de la imagen a un rol que la regla de gasto (B1) no autoriza "
                   "y a un caso abierto para revisión clínica, pero la sala leía la clave por su cuenta y generaba "
                   "igual. Ahora la sala sigue la misma regla que el lanzamiento, en los dos caminos (banco de "
                   "imágenes y fotografías de sesión); lo ya guardado en el banco se sigue mostrando."),
        "authorised_by": "Instrucción docente del 2026-09-26 (sistema de imágenes estáticas)",
        "affects": {"modules": ["clinical_scene", "image_scene"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_the_room_shows_the_bank.py::test_11_a_role_the_paid_gate_refuses_is_never_charged_but_sees_what_is_saved",
                  "test_the_room_shows_the_bank.py::test_the_session_only_room_follows_the_paid_gate_too"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-06",
        "date": "2026-09-26",
        "title": "Banco persistente de imágenes del paciente: misma persona, estado actual, gasto con tope",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("La fotografía vivía sólo en la memoria de una sesión del navegador: una recarga, una "
                   "reanudación o un reinicio pagaban una imagen nueva de otra persona, y la foto PNG de ~2 MB "
                   "viajaba dentro del HTML del monitor, 2,6 MB por cada orden (medido en un navegador real). "
                   "Ahora, con la base de cuentas: identidades sintéticas elegidas por compatibilidad y novedad, "
                   "cada estado editado desde el ancla de esa persona, una sola solicitud por persona y estado, "
                   "presupuesto reservado antes de cada llamada, fallas y respuestas tardías guardadas sin "
                   "mostrarse fuera de su estado, y lo que la sala mostró queda con el encuentro. La foto viaja "
                   "como WebP en un elemento propio: 20 KB por orden. No cambia la fisiología, la evaluación, "
                   "las cuatro categorías ni los PDF."),
        "authorised_by": "Instrucción docente del 2026-09-26 (sistema de imágenes estáticas)",
        "affects": {"modules": ["image_bank", "image_broker", "image_scene", "image_selection", "image_identities",
                                "image_pricing", "image_pack", "image_bank_portal", "clinical_scene",
                                "resuscitation_room", "patient_appearance", "scene_repair", "curriculum_runtime",
                                "faculty_portal"],
                    "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_the_image_bank.py::test_a_saved_image_is_shown_again_without_any_call_even_after_a_restart",
                  "test_the_image_bank.py::test_two_states_asked_for_at_once_share_one_first_photograph",
                  "test_the_room_shows_the_bank.py::test_6_a_reload_shows_the_same_person_from_the_database_without_a_call",
                  "test_the_room_shows_the_bank.py::test_4_a_state_change_during_a_request_never_shows_the_earlier_state",
                  "test_the_room_shows_the_bank.py::test_the_overlay_carries_no_image_bytes_and_the_photograph_element_depends_only_on_the_photograph"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-07",
        "date": "2026-09-26",
        "title": "La línea del presupuesto de imágenes se leía como una fórmula en el panel docente",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Streamlit lee como fórmula el texto entre dos signos de dólar, y la línea «committed US$2.50 "
                   "of US$10.00 (…)» del banco de imágenes aparecía en el navegador como «US2.50ofUS10.00…» en "
                   "cursiva matemática (visto en una copia local de la app con el mismo código y el mismo "
                   "paquete). Ahora cada signo de dólar va escapado. Sólo cambia cómo se ve la línea; las cifras "
                   "y el registro de gasto son los mismos."),
        "authorised_by": "Instrucción docente del 2026-09-26 (sistema de imágenes estáticas; revisar la app tras reiniciarla)",
        "affects": {"modules": ["image_bank_portal"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_image_bank_portal.py::test_the_budget_line_shows_dollars_not_a_formula"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-08",
        "date": "2026-09-26",
        "title": "Con la barra lateral abierta, la sala del encuentro quedaba en parte debajo de ella",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Las capas de la sala (fotografía, monitor, notas y consola) están fijas a la ventana desde el "
                   "2026-09-21, y la barra lateral de Streamlit, abierta por defecto en un computador (300 px), "
                   "tapaba su borde izquierdo: el minuto y el comienzo de la nota sobre lo que la fotografía no "
                   "permite ver. Ahora se fijan al área principal, que empieza donde termina la barra, sea cual sea "
                   "su ancho; con la barra cerrada y en un teléfono, donde la barra se abre encima, la sala queda "
                   "igual. Visto en un navegador real sobre una copia local (1400, 1280 y 1024 px de ancho y un "
                   "teléfono). No cambia qué se muestra, sólo dónde."),
        "authorised_by": "Instrucción docente del 2026-09-26 («sí, corrige lo de la barra lateral»)",
        "affects": {"modules": ["clinical_scene"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_clinical_scene.py::test_an_open_sidebar_covers_none_of_the_room"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-09",
        "date": "2026-09-26",
        "title": "Imágenes del paciente: las decisiones aprobadas por el docente, y sin gasto en lo que ya falló",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Decisiones aprobadas el 2026-09-26. (5) Las revisiones visual y clínica aprobadas habilitan una "
                   "foto que el revisor automático rechazó; nunca levantan la exclusión de una persona. (7) Sudor "
                   "leve, palidez leve y esfuerzo levemente aumentado se dibujan como su basal y comparten foto; la "
                   "sala dice al lado lo que la foto no muestra. (8) MRS_IMAGE_REQUIRE_REVIEW exige ambas "
                   "revisiones antes de mostrar una foto (para producción). (10) Sin base de cuentas no se paga "
                   "ninguna foto. (3) El equipo de pared no conectado no es tratamiento para el revisor. Además, "
                   "por la instrucción de evitar gastos que terminan en rechazo, no se piden la mascarilla de "
                   "reservorio ni el sudor marcado en piel oscura. Las aprobaciones del docente viajan en el "
                   "paquete, a nombre de su cuenta y con nota de quién las registró."),
        "authorised_by": "Instrucción docente del 2026-09-26 (decisiones de imágenes «Aprobado»; aprobación de las 7 fotos)",
        "affects": {"modules": ["image_bank", "image_selection", "image_broker", "image_scene", "image_pack",
                                "image_consistency", "clinical_scene", "image_bank_portal", "app"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_the_image_bank.py::test_approved_reviews_enable_a_photograph_the_screen_rejected_and_nothing_else_does",
                  "test_the_image_bank.py::test_mild_findings_share_the_photograph_of_their_baseline_and_are_named_beside_it",
                  "test_the_image_bank.py::test_a_state_known_to_fail_is_never_paid_for",
                  "test_the_image_bank.py::test_pack_approvals_are_recorded_once_under_the_account_they_name",
                  "test_the_room_shows_the_bank.py::test_with_review_required_only_a_photograph_a_person_approved_is_shown",
                  "test_scene_pipeline.py::test_without_an_account_database_no_picture_is_paid_for"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-10",
        "date": "2026-09-26",
        "title": "Imágenes del paciente: contextura corporal realista, que sigue el peso del caso",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Las 30 personas del banco se dibujaban delgadas o atléticas, cuando la mayoría de los adultos "
                   "de Cleveland y Santiago tiene sobrepeso u obesidad (NHANES 2021-23, CDC 2022, ENS 2016-17). "
                   "Identidades 1.1: la contextura es una dimensión propia (normal, sobrepeso, obesidad, obesidad "
                   "severa) nombrada en el prompt con palabras clínicas y respetuosas; diez personas nuevas; 55% "
                   "con sobrepeso u obesidad, repartidas en todos los tonos. La contextura sigue el peso del caso: "
                   "un caso sin peso, que el motor calcula a 70 kg, sólo muestra contextura normal o sobrepeso. "
                   "Las personas ya fotografiadas no cambian."),
        "authorised_by": "Instrucción docente del 2026-09-26 («creo que todos se ven demasiado atléticos»)",
        "affects": {"modules": ["image_identities", "image_arrivals"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_image_identities.py::test_a_case_without_a_weight_shows_only_a_body_that_could_weigh_the_engines_70_kg",
                  "test_image_identities.py::test_only_a_plain_contradiction_excludes_and_the_ranges_guide_the_choice",
                  "test_image_identities.py::test_the_bank_is_no_longer_all_slim_and_heavier_bodies_span_every_tone"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-11",
        "date": "2026-09-26",
        "title": "El desnivel real/ideal deja de preguntar por sí solo; la convención se registra como pendiente",
        "scope": {"level": "general"},
        "kind": "clinical_decision_applied",
        "reason": ("Punto 1 de la instrucción: el umbral real ≥ 1,30 × ideal no es una barrera general. Sin tipo de "
                   "peso nombrado ni regla acordada, la dosis corre sobre el peso real de la ficha y el registro "
                   "declara la convención y que el tipo de peso del fármaco es una decisión clínica pendiente "
                   "(weight_convention_pending). Una elección explícita se reutiliza sólo para el mismo fármaco y "
                   "clase de orden. Los encuentros de la primera revisión del sello (2026-09-27) conservan su "
                   "pregunta, para que lo guardado se reproduzca igual; el sello nuevo es 2026-09-27.2. Con las "
                   "reglas vigentes, una orden nueva completa reemplaza a la retenida en vez de repetir la pregunta."),
        "authorised_by": INSTRUCTION_2026_09_26B,
        "affects": {"modules": ["patient_body", "weight_based_doses", "pending_family_orders", "tanda20",
                                "tanda20_en"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_weight_and_height.py::test_the_weight_gap_alone_is_not_a_question_and_the_convention_is_recorded",
                  "test_weight_and_height.py::test_an_encounter_of_the_first_revision_still_asks_as_it_did",
                  "test_doses_by_solution_and_by_weight.py::test_the_weight_gap_no_longer_asks_and_the_convention_is_recorded",
                  "test_doses_by_solution_and_by_weight.py::test_an_encounter_of_the_first_revision_still_asks_the_weight_type"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-12",
        "date": "2026-09-26",
        "title": "Los casos generados registran talla y origen del cuerpo (esquema v4): un recorrido, una interpretación",
        "scope": {"level": "general"},
        "kind": "clinical_decision_applied",
        "reason": ("Punto 2: el esquema de generación exige peso Y talla con cómo se obtuvo cada uno, y una "
                   "verosimilitud estructural (IMC 13-70). patient_body lee esos campos planos, así que la ficha, "
                   "los tipos de peso y el Vt por kilo funcionan igual en casos del banco y generados. Un caso "
                   "generado antes de v4 conserva su versión histórica: sólo peso, talla no registrada, y un tipo "
                   "de peso que la necesite pregunta por el dato faltante sin inventarlo."),
        "authorised_by": INSTRUCTION_2026_09_26B,
        "affects": {"modules": ["generated_case_schema", "generated_case", "patient_body"],
                    "versions": {"generated_case_schema": {"from": "mrs.generated.case.v3",
                                                           "to": "mrs.generated.case.v4"}}},
        "clinical_relevance": "clinical",
        "tests": ["test_weight_and_height.py::test_a_generated_case_records_the_same_body_data_a_bank_case_does",
                  "test_weight_and_height.py::test_a_case_generated_before_v4_keeps_its_historical_reading"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-13",
        "date": "2026-09-26",
        "title": "«The history you took» vuelve al documento del residente por el recorrido real",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("La carga de análisis nunca lleva `session`, así que history_review no encontraba eventos y la "
                   "sección no se mostraba en producción; la prueba lo ocultaba inyectando `session` a mano. Ahora "
                   "history_review lee también los `encounter_events` congelados que la carga sí lleva, la carga "
                   "nombra su caso (authored_case_id, excluido de la huella: los análisis guardados siguen "
                   "válidos), y la prueba construye la carga por el mismo camino que producción."),
        "authorised_by": INSTRUCTION_2026_09_26B,
        "affects": {"modules": ["history_review", "management_trace_store", "management_trace_report"],
                    "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_history_is_part_of_the_record.py::test_the_learner_sees_what_they_asked_and_what_they_did_not",
                  "test_history_is_part_of_the_record.py::test_the_learner_who_asked_nothing_is_told_so_plainly",
                  "test_history_is_part_of_the_record.py::test_a_topic_that_was_asked_about_is_not_listed_as_unasked"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-14",
        "date": "2026-09-26",
        "title": "Fentanilo en microgramos: rango propio, etiqueta en mcg y equivalencia declarada",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("El rango de morfina (0,5-30 mg) rechazaba toda dosis habitual de fentanilo (50-100 mcg) y "
                   "cualquier fentanilo por kilo. Ahora el fentanilo tiene su propio rango (10-500 mcg, guardado en "
                   "mg), la etiqueta y el mensaje hablan en microgramos, la orden por kilo conserva su escritura "
                   "(«1 mcg/kg»), y el factor de equivalencia aplica lo que el propio código declaraba (100 mcg ≈ "
                   "10 mg de morfina): el ×10 anterior era un décimo de su enunciado y ninguna orden realista lo "
                   "ejerció, porque el rango las rechazaba antes."),
        "authorised_by": INSTRUCTION_2026_09_26B,
        "affects": {"modules": ["family_engine", "family_parser", "weight_based_doses"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_weight_and_height.py::test_fentanyl_doses_are_read_written_and_bounded_in_micrograms",
                  "test_weight_and_height.py::test_a_fentanyl_dose_becomes_its_stated_morphine_equivalence"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-15",
        "date": "2026-09-26",
        "title": "Adrenalina IM y ácido tranexámico por kilo: comprensión, validación y ejecución separadas",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("«TXA 15 mg/kg» se leía como 15 mg fijos y el rango lo rechazaba; «adrenalina 0,01 mg/kg IM» "
                   "caía al lector de infusiones. Ahora ambas se entienden por kilo, se convierten con el peso de "
                   "la ficha, se muestran como se escribieron y el rango juzga abiertamente la dosis resultante; "
                   "nada se corrige en silencio. Un TXA sin dosis aplica su carga fija estándar de 1 g y lo dice "
                   "en el registro, en vez de aplicarla calladamente."),
        "authorised_by": INSTRUCTION_2026_09_26B,
        "affects": {"modules": ["family_parser", "family_engine", "weight_based_doses"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_weight_and_height.py::test_tranexamic_acid_per_kilogram_converts_and_a_missing_dose_is_stated",
                  "test_weight_and_height.py::test_intramuscular_epinephrine_per_kilogram_converts_and_is_judged_openly"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-16",
        "date": "2026-09-26",
        "title": "Función renal residual declarable; el caso en diálisis deja de orinar 70 mL/h",
        "scope": {"level": "variant", "family": "bradycardia", "variants": ["bradycardia_hyperk_63m"]},
        "kind": "clinical_decision_applied",
        "reason": ("Punto 4: un caso puede declarar su función renal basal (engine.renal): «minimal» para «I pass "
                   "almost no urine» -- oligúrico, nunca anuria absoluta, con una participación residual del 10% "
                   "como convención del simulador presentada como decisión pendiente (decisión D) -- o una basal "
                   "absoluta en mL/h cuando la facultad la fije. La misma participación limita la respuesta a la "
                   "furosemida. Nada cambia en bloque: sólo el caso que lo declara, y un encuentro guardado "
                   "conserva la copia de caso con la que se lanzó."),
        "authorised_by": INSTRUCTION_2026_09_26B,
        "affects": {"modules": ["urine_output", "clinical_cases"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_weight_and_height.py::test_the_dialysis_case_no_longer_makes_the_urine_of_a_working_kidney",
                  "test_weight_and_height.py::test_an_encounter_saved_before_the_declaration_keeps_its_own_case_copy",
                  "test_weight_and_height.py::test_no_other_case_changed_its_urine_and_a_declared_absolute_baseline_is_possible"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-17",
        "date": "2026-09-26",
        "title": "El peso seco inferido (117 kg) se retira: no está registrado hasta que la facultad lo defina",
        "scope": {"level": "variant", "family": "bradycardia", "variants": ["bradycardia_hyperk_63m"]},
        "kind": "clinical_decision_applied",
        "reason": ("Punto 7: los 117 kg salían de restar 5 kg por dos sesiones perdidas -- una propuesta, no un "
                   "antecedente demostrado. En las versiones nuevas del caso el peso seco no está disponible; la "
                   "ficha no lo muestra y una dosis «de peso seco» pregunta por el dato faltante conservando la "
                   "orden completa. Lo ya mostrado en encuentros guardados queda intacto en su copia."),
        "authorised_by": INSTRUCTION_2026_09_26B,
        "affects": {"modules": ["patient_body", "tools_case_bodies"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_weight_and_height.py::test_the_dry_weight_is_not_recorded_until_the_faculty_defines_it"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-18",
        "date": "2026-09-26",
        "title": "La evaluación conoce sus convenciones: alcance por observación en el Brief y junto a la rúbrica",
        "scope": {"level": "general"},
        "kind": "policy",
        "reason": ("Punto 5: que la rúbrica no puntúe mg/kg no elimina los efectos indirectos (gases, presión, "
                   "duración del bloqueo, diuresis). model_conventions identifica por encuentro las observaciones "
                   "que dependen de una convención pendiente y las muestra, con su decisión, en el Faculty Brief y "
                   "junto a la sugerencia de rúbrica, con la regla de no fundar una deficiencia sólo en ellas. El "
                   "alcance es la observación, nunca el dominio, y la validación docente se mantiene."),
        "authorised_by": INSTRUCTION_2026_09_26B,
        "affects": {"modules": ["model_conventions", "faculty_report", "rubric_portal", "weight_based_doses"],
                    "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_model_conventions.py::test_a_per_kilogram_dose_on_the_convention_is_named_with_its_decision",
                  "test_model_conventions.py::test_an_explicitly_named_weight_type_is_not_a_convention_note",
                  "test_model_conventions.py::test_a_patient_without_the_relevant_gap_carries_no_weight_note",
                  "test_model_conventions.py::test_the_dialysis_case_notes_its_residual_diuresis_only_when_urine_was_touched",
                  "test_model_conventions.py::test_the_rule_bounds_the_observation_and_not_the_domain"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-19",
        "date": "2026-09-26",
        "title": "Imágenes: los rangos de IMC orientan sin excluir por poco, y la nota de la foto es neutral",
        "scope": {"level": "general"},
        "kind": "clinical_decision_applied",
        "reason": ("Punto 6: una ficha a menos de 2 puntos de IMC del rango de una contextura es una diferencia "
                   "pequeña alrededor de un límite -- la foto sigue usable, ordenada tras cualquier ajuste mejor, y "
                   "nunca motiva pagar un reemplazo; sólo más allá la contradicción es clara. La sala muestra una "
                   "misma frase neutral junto a toda foto vigente, sin nombrar qué hallazgos no muestra (nombrarlos "
                   "revelaba qué define el caso); los códigos siguen en el registro de visualizaciones y en la "
                   "revisión docente. Se planifica la tanda 7 (V34 para pulmonary_edema_75f, el caso sin foto)."),
        "authorised_by": INSTRUCTION_2026_09_26B,
        "affects": {"modules": ["image_identities", "image_selection", "clinical_scene", "image_arrivals"],
                    "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_image_identities.py::test_only_a_plain_contradiction_excludes_and_the_ranges_guide_the_choice",
                  "test_image_identities.py::test_photographed_people_are_matched_by_how_their_photograph_looks",
                  "test_the_room_shows_the_bank.py::test_the_room_s_still_view_note_is_neutral_and_the_record_keeps_the_codes"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-20",
        "date": "2026-09-26",
        "title": "La prueba que dependía del orden: el reemplazo del generador de una prueba no sobrevive a su fin",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Punto 3: test_problem_launch::test_new_ai_case_is_persisted_and_resumed_without_reauthoring fallaba "
                   "sólo después de test_cognitive_encounters en el mismo proceso. Reproducida: el fixture shared_app "
                   "reemplazaba sólo encounter_generator.generate_encounter, y curriculum_runtime, importado por primera "
                   "vez dentro de ese intervalo por la primera ejecución de la app, guardaba el reemplazo después de la "
                   "restauración; la prueba siguiente lanzaba un caso del banco en vez de uno generado. El estado "
                   "compartido estaba en la prueba, no en la aplicación, donde nada reemplaza el generador. El fixture "
                   "carga los dos alias antes de reemplazarlos y restaura ambos, como ya hacía test_curriculum_app; el "
                   "código de la aplicación no cambia."),
        "authorised_by": INSTRUCTION_2026_09_26B,
        "affects": {"modules": ["test_cognitive_encounters"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_cognitive_encounters.py::test_the_replay_fixture_leaves_no_generator_behind",
                  "test_problem_launch.py::test_new_ai_case_is_persisted_and_resumed_without_reauthoring"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-21",
        "date": "2026-09-26",
        "title": "Una dosis por kilo conserva la cantidad del residente con la unidad escrita como en el registro",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Al mostrar la dosis por kilo como se escribió (C-2026-09-26-15), la unidad quedaba tal cual en "
                   "minúsculas: «80 UI/kg» se registraba «80 ui/kg» junto a «3760 units». Se conservan la cantidad y la "
                   "unidad del residente (1 mcg/kg sigue en microgramos, no 0,001 mg/kg) con la grafía del registro: "
                   "UI, U y unidades son units; gramos es g. La dosis ejecutada no cambia y la etiqueta vuelve a la "
                   "que citan las pruebas de C-2026-09-27-03."),
        "authorised_by": INSTRUCTION_2026_09_26B,
        "affects": {"modules": ["family_parser"], "versions": {}},
        "clinical_relevance": "cosmetic",
        "tests": ["test_doses_by_solution_and_by_weight.py::test_a_dose_per_kilogram_keeps_the_resident_s_amount_in_the_record_s_units",
                  "test_doses_by_solution_and_by_weight.py::test_a_dose_per_kilogram_uses_the_weight_in_the_chart",
                  "test_weight_and_height.py::test_fentanyl_doses_are_read_written_and_bounded_in_micrograms"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-22",
        "date": "2026-09-26",
        "title": "Los documentos se escriben en el idioma en que se jugó el encuentro; quien los abre puede elegir el otro",
        "scope": {"level": "general"},
        "kind": "policy",
        "reason": ("Un encuentro guarda el idioma de pantalla con que se cerró (encounter_language, fuera de toda "
                   "huella de análisis). El Management Trace, el Faculty Brief y el documento de rúbrica se escriben "
                   "en ese idioma, con un selector Español/English junto a cada descarga; el documento de rúbrica "
                   "dejó de salir siempre en inglés. Un encuentro cerrado antes no registró idioma y no se adivina: "
                   "sus documentos siguen la elección de quien los abre, como antes. Nada se regenera."),
        "authorised_by": INSTRUCTION_2026_09_26C,
        "affects": {"modules": ["language", "document_language", "curriculum_runtime", "app",
                                "management_trace_report", "faculty_report", "rubric_report",
                                "management_trace_portal", "resident_portal", "faculty_portal"],
                    "versions": {}},
        "clinical_relevance": "cosmetic",
        "tests": ["test_document_language.py::test_an_encounter_that_recorded_no_language_at_its_start_records_the_one_it_closes_in",
                  "test_document_language.py::test_the_language_chosen_at_the_start_holds_through_the_encounter_and_its_documents",
                  "test_document_language.py::test_the_language_is_read_from_the_record_and_never_guessed",
                  "test_document_language.py::test_the_management_trace_is_written_in_the_language_it_is_given",
                  "test_document_language.py::test_the_faculty_brief_is_written_in_the_language_it_is_given",
                  "test_document_language.py::test_the_rubric_document_is_written_in_the_language_it_is_given",
                  "test_document_language.py::test_the_faculty_page_offers_the_encounter_s_language_first",
                  "test_document_language.py::test_the_faculty_brief_downloaded_is_in_the_chosen_language"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-23",
        "date": "2026-09-26",
        "title": "Un documento en español dice en español sus propias palabras",
        "scope": {"level": "general"},
        "kind": "text",
        "reason": ("Lo que el documento arma alrededor de sus valores salía en inglés dentro de un documento en "
                   "español: encabezados de decisión, «Based on», signos observados y sus valores, «Changed / "
                   "Unchanged», nombres de exámenes y campos de resultado, órdenes (ingresos, interconsultas, "
                   "solicitudes, oxígeno), temas de historia, dominios, notas de convenciones y la trazabilidad "
                   "de la rúbrica. Ahora se escriben en español con el catálogo revisado (sin IA); dosis, unidades, "
                   "números y nombres de fármacos no cambian (decisión 16) y el camino en inglés queda idéntico. "
                   "Quedan fuera, en sus propias etapas: el texto del modelo, la narrativa del caso y los títulos "
                   "oficiales de los objetivos del currículo (redacción oficial, 2026-09-23)."),
        "authorised_by": INSTRUCTION_2026_09_26C,
        "affects": {"modules": ["management_trace_report", "faculty_report", "report_presentation",
                                "rubric_presentation", "model_conventions", "language", "history_topics",
                                "report_language"], "versions": {}},
        "clinical_relevance": "cosmetic",
        "tests": ["test_document_language.py::test_a_spanish_document_says_its_own_words_in_spanish",
                  "test_document_language.py::test_an_order_is_written_in_spanish_with_its_dose_untouched",
                  "test_document_language.py::test_the_history_topics_have_spanish_names",
                  "test_the_documents_speak_the_readers_language.py::test_no_document_word_stays_english_when_the_reader_chose_spanish"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-24",
        "date": "2026-09-26",
        "title": "El texto del modelo se traduce al pedirlo, una vez, y el original en inglés sigue siendo el registro",
        "scope": {"level": "general"},
        "kind": "policy",
        "reason": ("Decisión docente del 2026-09-26: el análisis de IA se sigue generando en inglés (la evaluación, "
                   "el registro de correcciones y la reproducibilidad leen ese original) y, al pedir un documento en "
                   "español, se traducen exactamente las frases del modelo que imprime, después de las correcciones "
                   "registradas. La traducción se guarda por el hash del inglés y del prompt (mrs_prose_translations) "
                   "y se reutiliza; una frase corregida se traduce de nuevo. Nunca se envían las palabras del "
                   "residente ni el texto propio del documento. Sin clave configurada (o sin conexión) no se traduce "
                   "nada y el documento lo dice. Modelo: MRS_TRANSLATION_MODEL (por defecto gpt-5-mini)."),
        "authorised_by": INSTRUCTION_2026_09_26C,
        "affects": {"modules": ["prose_translation", "management_trace_report", "faculty_report", "rubric_report",
                                "rubric_presentation", "management_trace_portal", "resident_portal",
                                "faculty_portal"], "versions": {}},
        "clinical_relevance": "cosmetic",
        "tests": ["test_prose_translation.py::test_a_translation_is_paid_for_once_and_reused",
                  "test_prose_translation.py::test_english_asks_for_nothing_and_no_key_translates_nothing",
                  "test_prose_translation.py::test_the_management_trace_sends_only_the_model_s_sentences",
                  "test_prose_translation.py::test_the_faculty_brief_sends_only_the_model_s_sentences",
                  "test_prose_translation.py::test_the_rubric_document_sends_the_proposal_s_prose_and_never_the_learner_s_words",
                  "test_prose_translation.py::test_a_document_without_translations_keeps_the_english_and_says_so"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-26-25",
        "date": "2026-09-26",
        "title": "La narrativa de los 31 casos del banco en español, usada sólo después de la revisión docente de cada caso",
        "scope": {"level": "general"},
        "kind": "policy",
        "reason": ("Decisión docente del 2026-09-26: la presentación, quién da la historia, las respuestas de la "
                   "anamnesis, el examen físico y la prosa de los informes de exámenes de los 31 casos se traducen "
                   "como datos junto al inglés (case_text/es/, tools_case_text.py), y un caso se muestra en español "
                   "sólo después de que un docente aprueba su traducción en el panel docente. La revisión queda con "
                   "la cuenta de quien la registra y nombra la versión exacta leída; un cambio posterior en cualquiera "
                   "de los dos idiomas devuelve el caso a pendiente, y un pasaje cuyo inglés cambió no se usa. La "
                   "aprobación vale sólo para su caso: una frase que otro caso dice igual sigue en inglés en él. Un "
                   "pasaje se reemplaza entero o no se reemplaza, de modo que ninguna línea mezcla idiomas. El registro "
                   "del encuentro sigue en inglés; el español es presentación. La etiqueta fija que la sala pone "
                   "junto a la fuente de la historia se traduce con ella («Fuente de la historia: Esposa»). "
                   "Además, la orden de ECG derecho se presenta como «derivaciones derechas», igual que la "
                   "posterior."),
        "authorised_by": INSTRUCTION_2026_09_26C,
        "affects": {"modules": ["case_text", "case_text_portal", "tools_case_text", "language", "app",
                                "management_trace_report", "faculty_report", "rubric_report",
                                "curriculum_runtime"], "versions": {}},
        "clinical_relevance": "cosmetic",
        "tests": ["test_case_text.py::test_every_drafted_passage_translates_what_its_case_says_today",
                  "test_case_text.py::test_nothing_is_spanish_until_a_faculty_member_approves_it",
                  "test_case_text.py::test_an_approval_is_the_faculty_member_s_and_names_what_they_read",
                  "test_case_text.py::test_an_edit_after_the_approval_takes_the_case_back_to_pending",
                  "test_case_text.py::test_a_passage_whose_english_changed_is_not_used_even_in_an_approved_case",
                  "test_case_text.py::test_a_sentence_is_replaced_whole_or_not_at_all",
                  "test_case_text.py::test_the_room_reads_the_approved_narrative_of_its_own_case",
                  "test_case_text.py::test_the_room_s_arrival_line_is_whole_in_one_language",
                  "test_case_text.py::test_approvals_carried_from_another_deployment_count_for_the_same_words",
                  "test_case_text.py::test_the_documents_use_the_approved_narrative_in_spanish_only",
                  "test_case_text.py::test_the_review_page_records_the_approval_of_whoever_signs_it"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-27-01",
        "date": "2026-09-27",
        "title": "Peso y talla en los 31 casos del banco y en la ficha, sólo para encuentros nuevos",
        "scope": {"level": "general"},
        "kind": "clinical_decision_applied",
        "reason": ("Cada caso del banco registra peso y talla y cómo se obtuvieron (medido, referido o estimado); el "
                   "paciente en diálisis registra además su peso seco previo, rotulado como tal. La tabla sale de un "
                   "sorteo reproducible (tools_case_bodies.py) con las condiciones docentes: contextura independiente "
                   "de edad, diagnóstico y gravedad; sin peso normal por quimioterapia, alcohol o baja ingesta; tallas "
                   "variadas; sin mirar las fotos ni cambiar antecedentes. La ficha los muestra. Un encuentro nuevo "
                   "lleva weight_rules en su spec; uno lanzado antes no, y conserva sus datos y reglas."),
        "authorised_by": INSTRUCTION_2026_09_27,
        "affects": {"modules": ["patient_body", "clinical_cases", "cognitive_generator", "generated_case", "app",
                                "language", "tools_case_bodies"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_weight_and_height.py::test_every_bank_case_records_its_weight_and_height_and_how_each_was_obtained",
                  "test_weight_and_height.py::test_the_table_is_the_seeded_draw_and_meets_the_faculty_s_conditions",
                  "test_weight_and_height.py::test_the_dry_weight_is_not_recorded_until_the_faculty_defines_it",
                  "test_weight_and_height.py::test_the_chart_says_when_a_weight_is_an_estimate",
                  "test_weight_and_height.py::test_new_encounters_carry_the_rules_and_old_ones_keep_theirs",
                  "test_hypoglycemia_preservation.py::test_bank_cases_match_the_record_except_declared_corrections"],
        "preservation": {"variants": ["hypoglycemia_28m", "hypoglycemia_76f", "hypoglycemia_54m_thiamine"],
                         "variant_fields": ["/patient/body"]},
    },
    {
        "id": "C-2026-09-27-02",
        "date": "2026-09-27",
        "title": "Volumen corriente por kilo sobre el peso corporal predicho; el volumen absoluto se respeta",
        "scope": {"level": "general"},
        "kind": "clinical_decision_applied",
        "reason": ("Decisión B: un volumen corriente escrito en mL/kg se calcula sobre el peso predicho (Devine/ARDSNet, "
                   "por sexo y talla) y el registro muestra la fórmula; un tipo de peso nombrado por el residente se "
                   "respeta. Un volumen absoluto queda como se escribió: al pasar de mL/kg a mL en un ajuste, el valor "
                   "por kilo arrastrado sobrescribía el absoluto (defecto corregido). La ventilación minuto requerida y "
                   "el volumen por defecto no cambian: son decisiones pendientes."),
        "authorised_by": INSTRUCTION_2026_09_27,
        "affects": {"modules": ["asthma_ventilation", "family_engine", "active_order_context", "family_parser"],
                    "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_weight_and_height.py::test_a_tidal_volume_per_kilogram_is_on_the_predicted_body_weight_with_its_formula",
                  "test_weight_and_height.py::test_an_absolute_tidal_volume_is_kept_as_written_even_after_one_per_kilogram",
                  "test_weight_and_height.py::test_a_weight_type_the_resident_names_for_the_tidal_volume_is_kept",
                  "test_weight_and_height.py::test_before_the_weight_rules_a_tidal_volume_per_kilogram_stays_on_70_kg",
                  "test_weight_and_height.py::test_the_undecided_physiology_keeps_the_weight_it_was_calibrated_on"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-27-03",
        "date": "2026-09-27",
        "title": "Dosis por kilo: el tipo de peso explícito se respeta, se registra el peso usado y un mismo efecto por dosis",
        "scope": {"level": "general"},
        "kind": "clinical_decision_applied",
        "reason": ("Decisión F: el lector ya no pregunta el peso que está en la ficha; usa el tipo de peso que escribe "
                   "el residente, el que eligió antes para el mismo fármaco, una regla acordada o el peso real de la "
                   "ficha, y pregunta una vez por fármaco sólo si el peso real supera en 30% al ideal y no hay regla "
                   "acordada. Cada orden registra el peso usado, su tipo y su origen. El efecto se mide sobre un único "
                   "peso por paciente, así que la misma cantidad tiene el mismo efecto. Se corrigen: los mL/kg de "
                   "cristaloide, que se leían como mL, y los mg/kg/min de sedación, que se dividían dos veces."),
        "authorised_by": INSTRUCTION_2026_09_27,
        "affects": {"modules": ["weight_based_doses", "patient_body", "family_engine", "family_parser",
                                "pending_family_orders", "inotrope_support", "airway_pharmacology", "app"],
                    "versions": {}},
        "clinical_relevance": "clinical",
        # La conducta de "preguntar una vez si real ≥ 1,30 × ideal" fue la de la
        # primera revisión del sello y quedó conservada para esos encuentros;
        # C-2026-09-26-11 la retira para los lanzamientos nuevos. Las pruebas
        # citadas cubren hoy ambas revisiones con sus nombres actuales.
        "tests": ["test_weight_and_height.py::test_an_encounter_of_the_first_revision_still_asks_as_it_did",
                  "test_weight_and_height.py::test_the_same_amount_of_blocker_has_the_same_effect_however_it_was_written",
                  "test_weight_and_height.py::test_a_rate_per_kilogram_is_converted_on_the_chart_weight_and_recorded",
                  "test_weight_and_height.py::test_a_fluid_per_kilogram_is_a_volume_on_the_weight_not_that_many_millilitres",
                  "test_weight_and_height.py::test_a_sedation_rate_per_kilogram_per_minute_is_read_as_such",
                  "test_doses_by_solution_and_by_weight.py::test_a_dose_per_kilogram_uses_the_weight_in_the_chart",
                  "test_doses_by_solution_and_by_weight.py::test_an_encounter_of_the_first_revision_still_asks_the_weight_type",
                  "test_doses_by_solution_and_by_weight.py::test_an_encounter_launched_before_the_weight_rules_still_asks_the_weight"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-27-04",
        "date": "2026-09-27",
        "title": "Imágenes: compatibilidad visual amplia; se retira la diferencia rígida de 15 kg",
        "scope": {"level": "general"},
        "kind": "clinical_decision_applied",
        "reason": ("La foto no se usa para atribuir un peso. Una persona sirve a un caso salvo que el cuerpo que muestra "
                   "la foto (encuadre de pecho hacia arriba, en cama, bajo la frazada) contradiga claramente el peso y "
                   "la talla de la ficha; los rangos son amplios. Las personas ya fotografiadas se leen por cómo se ven "
                   "(lectura del agente, para revisión docente); entre dos que sirven, primero la de cuerpo más cercano, "
                   "después de lo ya guardado. La identidad se mantiene durante el encuentro."),
        "authorised_by": INSTRUCTION_2026_09_27,
        "affects": {"modules": ["image_identities", "image_selection", "image_scene"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_image_identities.py::test_the_rigid_15_kg_rule_is_retired",
                  "test_image_identities.py::test_photographed_people_are_matched_by_how_their_photograph_looks",
                  "test_image_identities.py::test_every_bank_case_has_a_compatible_person",
                  "test_image_identities.py::test_between_two_who_fit_the_nearer_body_comes_first"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-27-05",
        "date": "2026-09-27",
        "title": "El registro completo del encuentro (PDF y Markdown de la revisión) se escribe en el idioma del encuentro",
        "scope": {"level": "general"},
        "kind": "policy",
        "reason": ("El cuarto PDF, el registro original completo con su revisión de decisiones, comparación experta y "
                   "plan de adaptación, seguía sólo en inglés. Ahora se escribe en el idioma en que se jugó el encuentro, "
                   "con un selector para elegir el otro; el JSON sigue siendo el registro tal como se guardó. Las "
                   "palabras propias del documento salen del catálogo revisado; las preguntas de reflexión y el modelo "
                   "experto de los encuentros del currículo se componen de nuevo desde la misma evidencia, con las "
                   "palabras del residente citadas tal como las escribió; lo que un caso antiguo escribió en inglés se "
                   "muestra así y el documento lo dice. El inglés queda idéntico."),
        "authorised_by": INSTRUCTION_2026_09_26C,
        "affects": {"modules": ["app", "cognitive_review", "report_language", "language"], "versions": {}},
        "clinical_relevance": "cosmetic",
        "tests": ["test_review_record_language.py::test_the_record_follows_its_encounter_s_language_unless_its_reader_chooses",
                  "test_review_record_language.py::test_a_spanish_record_says_its_own_words_in_spanish",
                  "test_review_record_language.py::test_the_resident_s_words_stay_as_written_and_are_quoted_when_cited",
                  "test_review_record_language.py::test_the_expert_model_is_composed_again_from_the_same_evidence",
                  "test_review_record_language.py::test_a_prompt_written_in_english_for_its_case_is_shown_as_written_and_said_so",
                  "test_review_record_language.py::test_every_word_the_record_writes_can_be_said_in_spanish"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-27-06",
        "date": "2026-09-27",
        "title": "Un informe de examen dice su propia estructura en español, y una imagen se realiza, no se toma como muestra",
        "scope": {"level": "general"},
        "kind": "text",
        "reason": ("En la sala y en los documentos en español, la estructura de los informes seguía en inglés: las "
                   "secciones y etiquetas del POCUS («HEART», «LV contractility:») y campos de laboratorio como «WBC "
                   "(K/µL)». Con los hallazgos de un caso aprobado en español (case_text), cada línea del POCUS habría "
                   "mezclado los dos idiomas. Las etiquetas se traducen donde el informe las escribe, nunca dentro de "
                   "los hallazgos. Además, la ecografía renal, el eFAST y la radiografía de pelvis decían «Sample "
                   "obtained at minute» («Muestra tomada»), como si fueran una muestra: ahora dicen «Performed» "
                   "(«Realizado»), igual que las demás imágenes. Sólo cambia el texto de encuentros nuevos."),
        "authorised_by": INSTRUCTION_2026_09_26C,
        "affects": {"modules": ["language", "family_reports"], "versions": {}},
        "clinical_relevance": "cosmetic",
        "tests": ["test_study_reports_in_spanish.py::test_every_study_name_and_field_label_has_its_spanish",
                  "test_study_reports_in_spanish.py::test_a_pocus_report_has_no_english_structure",
                  "test_study_reports_in_spanish.py::test_imaging_is_performed_and_only_a_specimen_is_sampled_in_both_languages",
                  "test_study_reports_in_spanish.py::test_an_approved_case_reads_its_reports_wholly_in_spanish",
                  "test_family_report_wording.py::test_only_a_specimen_is_a_sample"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-27-07",
        "date": "2026-09-27",
        "title": "La sala y las pantallas de revisión dicen en español, enteras, las frases fijas del motor",
        "scope": {"level": "general"},
        "kind": "text",
        "reason": ("El ensayo de los 20 escenarios mostró en la sala en español líneas mezcladas: etiquetas de órdenes "
                   "del motor traducidas a medias («suero fisiológico 1000 mL IV started as a bolus…», «Epinephrine "
                   "inicio at 0.1 mcg/kg/min», «Tras requesting admission to ICU»), hallazgos de examen compuestos "
                   "por el motor («Respiratory rate: 34/min. Work of breathing: …»), el completado guiado del "
                   "razonamiento, los mensajes de órdenes no modeladas y otros avisos. Ahora cada frase fija se dice "
                   "entera desde el catálogo revisado; lo que escribió el residente se cita «así»; nombres de "
                   "fármacos, dosis y unidades como los escribe el motor (decisión 16). Las pantallas de revisión "
                   "(revisión de decisiones, comparación experta, plan de adaptación, resumen final) muestran sus "
                   "textos, preguntas y el modelo experto en el idioma de quien lee. El registro del encuentro nombra "
                   "ahora el caso de autor, que el estado congelado no guardaba, para usar su narrativa aprobada."),
        "authorised_by": INSTRUCTION_2026_09_26C,
        "affects": {"modules": ["language", "app", "report_language"], "versions": {}},
        "clinical_relevance": "cosmetic",
        "tests": ["test_room_labels_in_spanish.py::test_an_engine_order_is_said_whole_in_spanish",
                  "test_room_labels_in_spanish.py::test_what_the_engine_writes_stays_as_written",
                  "test_room_labels_in_spanish.py::test_the_room_s_other_fixed_sentences_are_said_whole",
                  "test_room_labels_in_spanish.py::test_what_the_resident_wrote_is_quoted_not_translated",
                  "test_room_labels_in_spanish.py::test_an_examination_finding_the_engine_composes_is_said_whole",
                  "test_room_labels_in_spanish.py::test_the_neurological_finding_quotes_the_case_s_approved_words_only",
                  "test_room_labels_in_spanish.py::test_a_fixed_message_among_the_history_answers_is_said_whole",
                  "test_review_record_language.py::test_every_word_the_record_writes_can_be_said_in_spanish"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-27-08",
        "date": "2026-09-27",
        "title": "El portal del residente, la pantalla de la Management Trace y el registro de la sala en el idioma de quien lee",
        "scope": {"level": "general"},
        "kind": "policy",
        "reason": ("Lo que el residente ve de sus encuentros guardados —su portal, su Management Trace en pantalla, el "
                   "registro decisión por decisión y la página del encuentro completado— dice sus propias palabras desde el "
                   "catálogo revisado (screen_language), en el idioma elegido. El razonamiento de la IA se muestra "
                   "traducido sólo si su traducción ya estaba guardada (la pantalla nunca paga una llamada); si no, en "
                   "inglés, y la pantalla lo dice. El nombre del caso sigue la narrativa aprobada. Una guarda recorre los "
                   "textos de estas pantallas y exige su español en el catálogo."),
        "authorised_by": INSTRUCTION_2026_09_26C,
        "affects": {"modules": ["screen_language", "resident_portal", "management_trace_portal", "app", "report_language"],
                    "versions": {}},
        "clinical_relevance": "cosmetic",
        "tests": ["test_screens_speak_the_readers_language.py::test_every_word_the_screen_writes_can_be_said_in_spanish",
                  "test_screens_speak_the_readers_language.py::test_english_is_returned_untouched"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-27-09",
        "date": "2026-09-27",
        "title": "Los portales docentes, la rúbrica, el progreso, el banco de imágenes, las cuentas y el currículo en el idioma de quien lee",
        "scope": {"level": "general"},
        "kind": "policy",
        "reason": ("Las pantallas del docente y del administrador —informe docente, rúbrica, progreso por objetivo, banco de "
                   "imágenes, cuentas y el panel del currículo— dicen sus propias palabras desde el catálogo revisado, con los "
                   "encabezados de sus tablas y las opciones de sus formularios. Lo guardado se muestra como se guardó: los "
                   "valores que se registran siguen en inglés y sólo cambia cómo se leen. El aviso que decía que la información "
                   "del paciente está en inglés dice ahora que sigue el idioma de la barra lateral. La guarda recorre también "
                   "estos portales y exige cada frase pedida al catálogo tal como se escribe, con sus valores."),
        "authorised_by": INSTRUCTION_2026_09_26C,
        "affects": {"modules": ["screen_language", "faculty_portal", "rubric_portal", "progress_portal", "image_bank_portal",
                                "account_portal", "curriculum_runtime", "report_language"],
                    "versions": {}},
        "clinical_relevance": "cosmetic",
        "tests": ["test_screens_speak_the_readers_language.py::test_every_word_the_screen_writes_can_be_said_in_spanish",
                  "test_screens_speak_the_readers_language.py::test_every_wrapped_phrase_is_in_the_catalog_as_written"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-27-10",
        "date": "2026-09-27",
        "title": "Los descriptores de la rúbrica en español, sólo después de la aprobación docente de cada dominio",
        "scope": {"level": "general"},
        "kind": "policy",
        "reason": ("Lo que evalúa cada dominio y sus cuatro descriptores de nivel son los criterios de la rúbrica. Su "
                   "español es un borrador junto al inglés (rubric_text/es/descriptors.json) que un docente revisa dominio "
                   "por dominio en el panel docente, como la narrativa de los casos. Un dominio se lee en español sólo "
                   "cuando está aprobado y cada descriptor sigue traduciendo el inglés vigente; si no, en inglés, completo. "
                   "La aprobación queda con la cuenta de quien aprueba y nombra el texto exacto que leyó. Los criterios no "
                   "cambian: los puntajes, la propuesta de la IA y su prompt siguen usando el inglés. Nada se aprobó."),
        "authorised_by": INSTRUCTION_2026_09_27B,
        "affects": {"modules": ["rubric_text", "rubric_text_portal", "rubric_portal", "curriculum_runtime",
                                "report_language"],
                    "versions": {}},
        "clinical_relevance": "cosmetic",
        "tests": ["test_rubric_text.py::test_nothing_is_spanish_until_a_faculty_member_approves_it",
                  "test_rubric_text.py::test_the_criteria_the_scores_and_the_ai_use_stay_english_whatever_is_approved"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-27-11",
        "date": "2026-09-27",
        "title": "Revisión docente de la traducción de la rúbrica: redacción, orientación frente a indicación, ayuda y autonomía, D4 frente a D5",
        "scope": {"level": "general"},
        "kind": "policy",
        "reason": ("Seis descriptores reescritos como pidió el docente (D1 niveles 1 y 3, D3 nivel 2, D4 nivel 3, D5 "
                   "nivel 3); siguen sin aprobar y los corregidos necesitan una aprobación nueva. «Indicación» queda para "
                   "las órdenes clínicas y «orientación» para la ayuda al residente: la autonomía «Con indicaciones» pasa a "
                   "«Con orientación» y las «indicaciones de decisión» del informe docente a «preguntas por decisión». Los "
                   "formularios donde se declara la ayuda y se registra la autonomía dicen, en inglés y en español, qué "
                   "cuenta como ayuda; la escala, el prompt del informe docente y la procedencia no cambian. La pantalla de "
                   "la rúbrica explica D4 frente a D5, y el panel de revisión dice que aprobar la traducción no valida el "
                   "instrumento ni demuestra equivalencia entre idiomas."),
        "authorised_by": INSTRUCTION_2026_09_27C,
        "affects": {"modules": ["rubric_text", "rubric_text_portal", "rubric_portal", "encounter_context",
                                "faculty_portal", "progress_portal", "report_language"],
                    "versions": {}},
        "clinical_relevance": "cosmetic",
        "tests": ["test_rubric_text.py::test_the_faculty_review_of_2026_09_27_is_applied_word_for_word",
                  "test_rubric_text.py::test_indicacion_is_kept_for_clinical_orders_and_orientacion_is_the_help_a_resident_receives",
                  "test_autonomy_guidance.py::test_a_faculty_member_reads_it_where_help_is_declared_and_where_autonomy_is_recorded"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-27-12",
        "date": "2026-09-27",
        "title": "El idioma del encuentro se fija al iniciarlo y el selector queda bloqueado mientras está en curso",
        "scope": {"level": "general"},
        "kind": "policy",
        "reason": ("El encuentro guarda como encounter_language el idioma de pantalla con que se inicia, y el selector "
                   "de idioma queda bloqueado hasta que se cierra; antes y después es la preferencia de quien mira. Ese "
                   "idioma sigue siendo el de partida de todos sus documentos, que pueden pedirse en el otro, y las "
                   "pantallas del docente siguen su propio idioma. Un encuentro que no registró idioma al iniciarse "
                   "conserva la regla anterior (el idioma con que se cierra) y los históricos siguen la elección de quien "
                   "lee: nada se migra. Análisis, puntajes y documentos ya generados no cambian."),
        "authorised_by": INSTRUCTION_2026_09_27D,
        "affects": {"modules": ["app", "curriculum_runtime", "document_language"], "versions": {}},
        "clinical_relevance": "cosmetic",
        "tests": ["test_document_language.py::test_the_language_chosen_at_the_start_holds_through_the_encounter_and_its_documents",
                  "test_document_language.py::test_a_faculty_member_reads_in_their_own_language_and_the_documents_start_in_the_encounter_s",
                  "test_document_language.py::test_closing_keeps_the_language_the_encounter_started_in"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-27-13",
        "date": "2026-09-27",
        "title": "DF-7: el razonamiento del residente se registra como lo escribió en el Management Trace",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Registrado en el ciclo 8 (TD-06): el registro no nombraba esta corrección del ciclo 2 (commit "
                   "f1948f1). El modelo de trabajo, la prioridad, el efecto esperado y el motivo de una orden se "
                   "leían mal por clase: «IM» reescrito como «I am», un conector cortado dentro de una palabra, la "
                   "orden arrastrada dentro del modelo y la razón que no llegaba a ser la justificación. Se corrigió "
                   "por clase, en inglés y en español, sin cambiar lo que se ejecuta. Medición en "
                   "docs/MEDICION_RECONOCIMIENTO_ORDENES.md, ciclo 2."),
        "authorised_by": ("Instrucción docente del 2026-09-27, ciclo 2 del AI Advisor (DF-7: fidelidad del "
                          "razonamiento en el Management Trace)"),
        "affects": {"modules": ["app", "family_parser", "tools_order_reading"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_reasoning_fidelity_classes.py::test_the_intramuscular_route_is_never_rewritten_as_i_am",
                  "test_reasoning_fidelity_classes.py::test_a_model_stops_before_the_order_that_follows_it",
                  "test_reasoning_fidelity_classes.py::"
                  "test_the_reason_given_for_an_order_is_its_rationale_in_both_languages",
                  "test_reasoning_fidelity_classes.py::"
                  "test_the_same_finding_makes_a_working_model_in_both_languages"],
    },
    {
        "id": "C-2026-09-27-14",
        "date": "2026-09-27",
        "title": "DF-10: el alta conserva el plan con el que se escribe, en ambos idiomas",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Registrado en el ciclo 8 (TD-06): el registro no nombraba esta corrección del ciclo 3 (commits "
                   "9d35b00 y e54b919). «Discharge him with orthopedic follow-up» y «lo doy de alta con control en "
                   "policlínico» ejecutaban el alta y perdían el seguimiento, que sí se guardaba escrito después "
                   "del alta. Ahora el plan unido con with/con se registra como indicación al paciente, en el orden "
                   "escrito, y el alta sigue corriendo. «OK to discharge…» quedó como KD-05 y se corrige en el "
                   "ciclo 8 (C-2026-09-28-23)."),
        "authorised_by": ("Instrucción docente del 2026-09-27, ciclo 3 del AI Advisor (DF-10: el seguimiento unido "
                          "al alta con with/con)"),
        "affects": {"modules": ["family_parser", "unexecuted_items", "language", "app"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_a_discharge_keeps_the_plan_it_is_written_with.py::"
                  "test_the_follow_up_written_into_the_discharge_is_kept_and_the_discharge_still_runs",
                  "test_a_discharge_keeps_the_plan_it_is_written_with.py::"
                  "test_the_follow_up_and_the_return_advice_keep_the_order_they_were_written_in",
                  "test_a_discharge_keeps_the_plan_it_is_written_with.py::test_an_admission_written_with_a_plan_is_left_as_it_was"],
    },
    {
        "id": "C-2026-09-28-01",
        "date": "2026-09-28",
        "title": "C14 declarado caso por caso en el banco: 14 con oportunidad, 16 sin ella y acs_54m_inferior sin revisar",
        "scope": {"level": "general"},
        "kind": "clinical_decision_applied",
        "reason": ("Las decisiones A–H sobre C14 (usar el POCUS para guiar el manejo) se escriben en el bloque objectives "
                   "de 30 casos del banco (case_assessment_bank.C14_DECLARATIONS), cada una con quién la revisó, cuándo, "
                   "su grupo de decisión y la versión C14-REVIEW-1; un NO lleva su razón. acs_54m_inferior queda sin "
                   "declarar hasta resolver la contradicción entre el compromiso del ventrículo derecho y su POCUS. Una "
                   "oportunidad sólo hace evaluable C14 en un encuentro nuevo y nunca lo observa: la observación sigue "
                   "siendo la del docente. Un NO no es evaluable, nunca una falla. La regla transitoria se retira sólo "
                   "para C14 y sólo en los casos revisados; TD1, F1, C1, C3 y C4 la conservan. Los encuentros ya "
                   "iniciados conservan su base congelada. Dominios, eventos críticos y puntajes no cambian."),
        "authorised_by": INSTRUCTION_2026_09_28,
        "affects": {"modules": ["case_assessment_bank", "c14_review"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_c14_opportunities.py::test_the_bank_holds_a_reviewed_row_for_every_case",
                  "test_c14_opportunities.py::test_a_no_encounter_cannot_confirm_c14_and_records_no_failure",
                  "test_c14_opportunities.py::test_historical_observations_are_neither_reanalysed_nor_lost",
                  "test_c14_review.py::test_the_bank_carries_exactly_what_the_approved_answers_and_the_later_decision_derive",
                  "test_evaluation_basis.py::test_the_legacy_snapshot_is_the_code_before_the_change_for_every_other_case",
                  "test_hypoglycemia_preservation.py::test_declarations_match_the_record_except_the_new_version"],
        # The three hypoglycaemia cases now carry their C14 row: a new version of their declaration.
        "preservation": {"variants": ["hypoglycemia_28m", "hypoglycemia_76f", "hypoglycemia_54m_thiamine"],
                         "declaration": "new_version"},
    },
    {
        "id": "C-2026-09-28-02",
        "date": "2026-09-28",
        "title": "KD-01: una vía escrita antes del fármaco, sin verbo, es la vía de ese fármaco",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("«IV morphine 4 mg», «Oral paracetamol 1 g» o «Nebulized albuterol 2.5 mg» se devolvían como órdenes "
                   "no reconocidas y retenían el resto del envío. Corregido por clase: una palabra de vía que el lector ya "
                   "lee (shared_order_language.ROUTE_BEFORE_THE_DRUG, ninguna vía nueva), seguida de un fármaco que "
                   "conoce y su dosis, se salta para encontrar la orden y se lee donde fue escrita; la orden es la misma "
                   "que escrita con el fármaco primero. En una lista esa vía es sólo de su fármaco: «Aspirin 300 mg, IV "
                   "morphine 4 mg» ya no da la aspirina IV (la misma confusión). Un «in» suelto no se salta (KB-02); un "
                   "fluido nombrado en palabras queda como KD-15. Presente en el baseline español del piloto; corregido "
                   "desde el baseline inglés de validación."),
        "authorised_by": INSTRUCTION_2026_09_28,
        "affects": {"modules": ["family_parser", "shared_order_language"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_a_route_written_before_the_drug.py::test_the_route_before_the_drug_is_read_as_that_drug_s_route",
                  "test_a_route_written_before_the_drug.py::test_it_is_the_same_order_as_the_drug_written_first",
                  "test_a_route_written_before_the_drug.py::test_the_route_before_a_drug_reaches_no_other_order",
                  "test_a_route_written_before_the_drug.py::test_input_execution_and_trace_through_the_real_page"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-28-03",
        "date": "2026-09-28",
        "title": "Un encuentro nuevo empieza sin el cierre del encuentro anterior",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Auditoría nocturna del ciclo 5 (59Z, aislamiento entre encuentros). Volver al panel reiniciaba el "
                   "encuentro pero no cómo había terminado el anterior: un aviso de cierre abierto («How is this "
                   "encounter ending?») abría el encuentro siguiente en el minuto 0 ofreciendo «Finish now», y el "
                   "registro de cierre anterior («clinical_close», minuto 2) se guardaba en el encuentro siguiente y "
                   "quedaba en él si se abandonaba, donde lo leen el brief docente y el tamizaje de la rúbrica. Ahora "
                   "reset_session() los quita, como ya quitaba el idioma del encuentro. Un encuentro retomado conserva "
                   "su propio aviso y uno cerrado su propio registro. Los registros ya guardados no se reescriben."),
        "authorised_by": INSTRUCTION_2026_09_28_NIGHT,
        "affects": {"modules": ["app"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_a_new_encounter_starts_without_the_last_close.py::"
                  "test_a_close_warning_left_open_does_not_open_the_next_encounter",
                  "test_a_new_encounter_starts_without_the_last_close.py::"
                  "test_the_last_close_record_is_not_the_next_encounter_s",
                  "test_a_new_encounter_starts_without_the_last_close.py::"
                  "test_a_resumed_encounter_keeps_its_own_close_warning"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-28-04",
        "date": "2026-09-28",
        "title": "DF-22: nueve clases de oración que perdían, invertían o retenían una orden de primera línea",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Auditoría del Trace del ciclo 5 (C01–C09), corregida por clase y no por frase: «X, si no responde, "
                   "Y» da X ahora y deja Y como plan (también con una condición entre la orden y su repetición); "
                   "«Diagnóstico: orden» ejecuta lo que sigue a los dos puntos salvo tras una condición, un tiempo, "
                   "una alternativa o algo pendiente, que se leen como antes; «Ahora X y luego repetir» da X y deja "
                   "la repetición como su plan; «Suspende A y cambia a B» suspende A e inicia B, y las formas de "
                   "suspender un cristaloide (hold, D/C, cierra, corta) ya no se pierden; el destino con «con/on» "
                   "tratamiento hace ambos y una receta del alta queda como receta; «Activo hemodinamia» activa; «Por "
                   "<razón> instalo…» ejecuta; el ácido tranexámico con su duración ya no retiene el paquete urgente; "
                   "un hallazgo tras la orden no es otra orden. Medido con frases de desarrollo y con tres conjuntos "
                   "ciegos internos. Lo que esos conjuntos hallaron en las correcciones mismas se corrigió después "
                   "de medir: el ácido tranexámico en la historia, en un pensamiento o en una retención; lo unido "
                   "con «y/and» a lo que hizo el equipo prehospitalario se pregunta y no se ejecuta; un rótulo con un "
                   "umbral, un estado a alcanzar o un resultado («Con angioTAC positivo:») es una condición; y la vía "
                   "por la que pasa un suero («SF 500 mL por VVP», «via the PIV») es su vía, no una vía nueva que "
                   "perdía el bolo. Los defectos que quedan están en KNOWN_DEFECTS y en el registro de deuda técnica. "
                   "Presente en el baseline español del piloto, que no se toca."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE6,
        "affects": {"modules": ["family_parser", "family_engine", "language"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_critical_clinical_language_regressions.py::test_the_reader_reads_the_order_that_runs_now",
                  "test_critical_clinical_language_regressions.py::test_a_near_miss_runs_nothing_it_should_not",
                  "test_critical_clinical_language_regressions.py::test_the_engine_runs_it",
                  "test_critical_clinical_language_regressions.py::"
                  "test_the_question_about_a_clause_joined_to_the_prehospital_account_reads_in_spanish",
                  "test_critical_clinical_language_regressions.py::test_the_stored_management_trace_records_what_was_written"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-28-05",
        "date": "2026-09-28",
        "title": "Lo que la página dice de una orden sigue a lo que el motor ejecutó; una aclaración no pierde la orden retenida",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("59O-03: la página anunciaba «Urgent intervention executed…» y ofrecía explicarla después antes de "
                   "ejecutar nada, aunque el motor rechazara el paquete; ahora el aviso y la oferta salen sólo de una "
                   "ejecución real, también cuando la respuesta a una aclaración la completa, y el análisis docente "
                   "marca «urgent_unheld» sólo si corrió. El aviso de la anulación docente dice si la orden no corrió. "
                   "Seguridad de la aclaración: «no sé» o «I don't know» ante una orden retenida la dejaba "
                   "desaparecer en español; ahora la mantiene y repite la pregunta, y una orden nueva que reemplaza a "
                   "la retenida lo dice. La traducción de esos avisos ya no queda a medias."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE6,
        "affects": {"modules": ["app", "urgent_interventions", "faculty_analysis", "language"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_what_the_page_says_follows_what_ran.py::test_a_an_urgent_order_that_runs_is_announced_and_offered_for_explanation",
                  "test_what_the_page_says_follows_what_ran.py::test_c_an_unreadable_item_holds_the_urgent_bundle_and_claims_nothing",
                  "test_what_the_page_says_follows_what_ran.py::test_d_f_e_a_question_keeps_the_urgent_bundle_until_it_runs",
                  "test_what_the_page_says_follows_what_ran.py::test_only_an_urgent_entry_that_ran_awaits_an_explanation"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-28-06",
        "date": "2026-09-28",
        "title": "L-F01: un encuentro antiguo se lee con los temas de historia de su propio caso",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Los temas de historia que un caso ofrecía se leían del banco vivo: un cambio del banco cambiaba el "
                   "«disponible y no preguntado» de encuentros antiguos y el tamizaje de eventos críticos que depende de "
                   "una pregunta. Ahora se leen del caso congelado con el encuentro (columna del encuentro, estado de la "
                   "sesión, o los nombres de los temas que lleva el payload de análisis, nunca el caso). Un encuentro "
                   "sin copia es legacy: sus temas quedan «no disponibles» y no se toman del banco de hoy. Las huellas "
                   "de los análisis guardados no cambian."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE6,
        "affects": {"modules": ["history_review", "management_trace_store"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_an_old_encounter_keeps_its_own_history.py::test_version_a_stays_a_after_the_bank_changes_to_b",
                  "test_an_old_encounter_keeps_its_own_history.py::test_the_critical_event_screening_keeps_the_question_that_was_asked",
                  "test_an_old_encounter_keeps_its_own_history.py::test_a_legacy_encounter_without_its_case_is_unavailable_not_today_s_bank",
                  "test_an_old_encounter_keeps_its_own_history.py::test_carrying_the_topic_names_changes_no_saved_analysis_fingerprint"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-28-07",
        "date": "2026-09-28",
        "title": "L-F04: la trayectoria del perfil sigue a los encuentros, no a las confirmaciones",
        "scope": {"level": "general"},
        "kind": "policy",
        "reason": ("El perfil ordenaba las rúbricas confirmadas por la hora de confirmación: confirmar tarde un encuentro "
                   "anterior lo volvía el «último» y un residente que pasó de 1 a 3 veía «−2». Ahora se ordena por la "
                   "hora del encuentro y la hora de confirmación queda como metadato. Los promedios no dependen del "
                   "orden y no cambian; qué revisión de un encuentro cuenta (L-F02) no se toca."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE6,
        "affects": {"modules": ["rubric_store", "rubric_progress"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_the_profile_follows_the_encounters.py::test_confirming_an_earlier_encounter_later_does_not_make_it_the_latest",
                  "test_the_profile_follows_the_encounters.py::test_the_means_are_the_same_whatever_the_order_of_confirmation"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-28-08",
        "date": "2026-09-28",
        "title": "DF-23: la acinesia de de Winter se sostiene con la arteria cerrada; bradycardia_bb_54f llega somnolienta",
        "scope": {"level": "variant", "family": "acs", "variants": ["acs_52m_de_winter", "bradycardia_bb_54f"]},
        "kind": "clinical_decision_applied",
        "reason": ("Las dos únicas correcciones de la auditoría DF-23 que cumplen las seis condiciones. De Winter llega "
                   "con «Akinesis of the anterior wall and apex» y el modelo, que parte toda oclusión en «mildly "
                   "reduced», tomaba el POCUS repetido con la arteria cerrada: una reperfusión espontánea que no "
                   "ocurrió. El caso declara su grado de llegada y su texto se mantiene hasta que el modelo lo alcanza "
                   "o se abre la arteria; la fisiología no cambia y los demás casos tampoco. bradycardia_bb_54f dice "
                   "cuatro veces que llega somnolienta y su estado de llegada quedaba en «Alert»: ahora llega "
                   "somnolienta y ya no «empeora» sola a los 5 minutos. Los encuentros guardados conservan su caso "
                   "congelado y sus informes."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE6,
        "affects": {"modules": ["acs_reperfusion", "family_engine", "clinical_cases"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_the_case_says_what_the_patient_shows.py::test_the_de_winter_akinesis_stands_while_the_artery_is_closed",
                  "test_the_case_says_what_the_patient_shows.py::test_nothing_else_changes_in_de_winter_nor_in_the_other_occlusions",
                  "test_the_case_says_what_the_patient_shows.py::test_the_beta_blocker_overdose_arrives_drowsy_and_does_not_worsen_on_its_own"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-28-09",
        "date": "2026-09-28",
        "title": "Regresiones de las correcciones del ciclo 6 halladas por la revisión adversarial del diff, corregidas",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Una revisión adversarial del diff y una comparación con el lector del ciclo 5 sobre todos los "
                   "textos que tenemos hallaron lo que los conjuntos ciegos no vieron. «Hold NS, O2 4 L NC» quitaba "
                   "el oxígeno: el «stop» de C04 se prestaba a la orden siguiente (ahora no a una con su dosis, "
                   "volumen o flujo, ni a lo dicho del paciente; «suspender SF, O2 4 L NC» ya lo hacía antes); "
                   "«para los fluidos: Ringer…» se leía como suspender. La primera persona de C07 ejecutaba una "
                   "pregunta, una duda o un hábito («Should I give aspirin?», «por lo general administro…») y "
                   "retenía la adrenalina ante prosa («we give it 5 minutes»). La prueba de historia de C08 "
                   "silenciaba o retenía órdenes comunes («paracetamol… ya que AINE contraindicado», «epinephrine "
                   "given anaphylaxis», «urgent TXA 1 g IV»). El relato prehospitalario retenía órdenes del "
                   "residente y se saltaba con «, y». Además: una sedación con su procedimiento perdía la "
                   "sedación; un «RR 10» tras intubar se perdía; «with a norepinephrine infusion ready» la "
                   "iniciaba; un plan condicional con TXA se perdía; «si no, X» repetido tardaba minutos y un "
                   "rótulo con espacios, más; suspender un suero con duración tiraba la página; un caso autorado "
                   "que eligió el modelo perdía sus temas de historia; «no se administra…» se tomaba por «no sé». Y "
                   "uno anterior al ciclo: la activación de un servicio se prestaba a los fármacos que la seguían "
                   "(«activate the cath lab, aspirin 325 mg and ticagrelor 180 mg PO» los volvía interconsultas)."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE6,
        "affects": {"modules": ["family_parser", "family_engine", "pending_family_orders", "app", "history_review",
                                "language"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_critical_clinical_language_regressions.py::"
                  "test_what_the_adversarial_review_found_reads_as_cycle_5_did_or_better",
                  "test_critical_clinical_language_regressions.py::test_a_conditional_plan_that_names_tranexamic_acid_is_kept",
                  "test_critical_clinical_language_regressions.py::test_a_chain_of_conditions_and_a_run_of_spaces_are_read_in_time",
                  "test_critical_clinical_language_regressions.py::test_an_answer_in_the_first_person_is_not_taken_for_a_new_order",
                  "test_critical_clinical_language_regressions.py::test_a_stop_written_with_a_duration_does_not_break_the_page",
                  "test_critical_clinical_language_regressions.py::"
                  "test_the_first_line_orders_the_review_found_held_run_in_the_engine",
                  "test_an_old_encounter_keeps_its_own_history.py::test_an_authored_case_the_model_chose_keeps_its_frozen_topics",
                  "test_what_the_page_says_follows_what_ran.py::"
                  "test_only_a_reply_that_says_nothing_but_unsure_keeps_the_order_held"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-28-10",
        "date": "2026-09-28",
        "title": "C4 = NO en todo el entorno de observación: los 31 casos, los casos generados y PS001",
        "scope": {"level": "general"},
        "kind": "clinical_decision_applied",
        "reason": ("TDFC-7 (y TDFC-8 para la analgesia del cólico): el motor no modela los componentes de la "
                   "sedación y analgesia procedural que observa C4, y pedir un procedimiento no es una oportunidad. "
                   "La razón es del entorno, no de los casos (H4 del ciclo 7). Cada caso del banco declara C4 NO con su "
                   "razón y su procedencia (case_assessment_bank.C4_DECLARATIONS), y el entorno declara lo mismo una vez "
                   "(observation_opportunities.ENVIRONMENT): evaluation_basis.freeze lo congela en todo encuentro nuevo, "
                   "también en los generados y en los que no tienen caso autorado. Es prospectivo: un encuentro congelado "
                   "antes conserva la transición con que empezó, y una observación ya confirmada no se pierde ni se relee. "
                   "El motor no se tocó; la evidencia C4 vendrá de simulación procedural u observación en el lugar de "
                   "trabajo."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE7,
        "affects": {"modules": ["case_assessment_bank", "observation_opportunities", "evaluation_basis",
                                "progress_store"],
                    "versions": {"opportunities": {"from": "1.0", "to": "1.1"}}},
        "clinical_relevance": "clinical",
        "tests": ["test_c4_is_not_observable_in_this_environment.py::"
                  "test_every_bank_case_declares_c4_no_with_its_reason_and_provenance",
                  "test_c4_is_not_observable_in_this_environment.py::"
                  "test_encounters_outside_the_bank_are_frozen_with_the_environment_s_no",
                  "test_c4_is_not_observable_in_this_environment.py::"
                  "test_an_encounter_frozen_before_the_environment_keeps_the_transition",
                  "test_c4_is_not_observable_in_this_environment.py::"
                  "test_a_c4_observation_confirmed_before_stays_and_is_not_re_read",
                  "test_c4_is_not_observable_in_this_environment.py::test_the_faculty_cannot_confirm_c4_in_a_new_encounter"],
        # The three hypoglycaemia cases now carry their C4 row: a new version of their declaration.
        "preservation": {"variants": ["hypoglycemia_28m", "hypoglycemia_76f", "hypoglycemia_54m_thiamine"],
                         "declaration": "new_version"},
    },
    {
        "id": "C-2026-09-28-11",
        "date": "2026-09-28",
        "title": "C14 NO en acs_54m_inferior: los 31 casos del banco quedan revisados para C14",
        "scope": {"level": "variant", "variants": ["acs_54m_inferior"]},
        "kind": "clinical_decision_applied",
        "reason": ("DF-20 no cambió los datos ni la fisiología del caso, y el docente confirmó su C14 NO (H3 del ciclo "
                   "7) con una razón sobre la oportunidad de observación y no sobre lo que el POCUS puede mostrar: "
                   "reconocer el compromiso del ventrículo derecho con el POCUS disponible no es una expectativa que "
                   "establezca el marco ACEP 2016 usado aquí, y los nitratos, la antiagregación y el volumen prudente "
                   "dependen sobre todo del ECG, de las derivadas derechas y de la hemodinamia. La fila lleva la "
                   "revisión C14-REVIEW-2; c14_review.LATER la aplica después de las respuestas A–H, que no cambian. "
                   "Los encuentros ya iniciados conservan su base congelada."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE7,
        "affects": {"modules": ["case_assessment_bank", "c14_review"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_c14_opportunities.py::test_acs_54m_inferior_is_no_for_the_opportunity_not_for_what_pocus_can_show",
                  "test_c14_opportunities.py::test_the_bank_holds_a_reviewed_row_for_every_case",
                  "test_c14_review.py::test_the_later_decision_settles_only_the_row_decision_a_left_open"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-28-12",
        "date": "2026-09-28",
        "title": "TD-21: transfundir una hemorragia activa en trauma ya no dispara una sobrecarga falsa",
        "scope": {"level": "family", "family": "trauma"},
        "kind": "clinical_decision_applied",
        "reason": ("Principio D aprobado por el docente: mientras la hemorragia modelada siga activa (una fuente que "
                   "sangra o sangre perdida no repuesta), una hemoglobina ≥ 10 aislada no es evidencia de sobrecarga, "
                   "porque la familia trauma no baja la hemoglobina con la pérdida. Las unidades dadas entonces no se "
                   "cuentan como innecesarias; con el sangrado controlado y la pérdida repuesta, la regla vuelve. Sin "
                   "equivalencia mL-unidades ni umbral nuevo. La HDA, cuya hemoglobina sí sigue la pérdida, no cambia "
                   "(regla del 2026-09-20). Un solo interruptor la revierte. Sin cambios en el −3, los eventos críticos "
                   "ni las rúbricas. Detalle y ANTES/DESPUÉS en docs/TD21_SOBRECARGA_TRANSFUSIONAL.md."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE7,
        "affects": {"modules": ["family_engine", "trauma_hemorrhage"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_transfusion_overload.py::"
                  "test_an_appropriate_transfusion_during_an_active_haemorrhage_is_not_an_overload",
                  "test_transfusion_overload.py::"
                  "test_once_the_bleeding_is_controlled_and_the_loss_replaced_more_blood_overloads_again",
                  "test_transfusion_overload.py::test_the_haemoglobin_still_decides_where_it_follows_the_loss",
                  "test_transfusion_overload.py::test_the_suspension_is_one_switch_that_goes_back_to_the_haemoglobin_alone"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-28-13",
        "date": "2026-09-28",
        "title": "TD-26: cada hemoderivado se lee como se escribió; ninguno se pierde en silencio ni se vuelve otro",
        "scope": {"level": "general"},
        "kind": "clinical_decision_applied",
        "reason": ("Decisión docente TD-26 (ciclo 7, estándar A–J). Los glóbulos rojos corren en las unidades escritas "
                   "(1 a 4 por orden, la regla del motor), también como los escribe la ficha: «2 U GR O negativo», "
                   "«O-neg», «packed cells», «no cruzados». El plasma, las plaquetas, el crioprecipitado y la sangre "
                   "total se registran como indicados, con su efecto fisiológico no modelado, y nunca se vuelven "
                   "glóbulos rojos. La activación del protocolo de transfusión masiva se registra y no da nada por sí "
                   "sola. Lo ambiguo se pregunta: una transfusión sin producto, un conteo compartido, unidades por "
                   "reservar, dos órdenes en una frase, lo que espera algo. Lo que no es una orden ahora no transfunde "
                   "nada: un resultado, lo recibido antes o en ruta, un rechazo, una pregunta, un plan, un umbral, "
                   "una detención; lo que el motor no hace se devuelve citado. Un envío con sólo lo registrado queda "
                   "como decisión sin que pase un minuto. En «cristaloide en vez de sangre» y «HDA sin reanimación», "
                   "un hemoderivado indicado en la ventana lleva el resultado a lectura docente; la definición, el −3, "
                   "los puntajes y D1–D5 no cambian. Detalle y ANTES/DESPUÉS en docs/TD26_HEMODERIVADOS_Y_C7_06.md."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE7,
        "affects": {"modules": ["family_parser", "family_engine", "generated_engine", "coupled_encounter",
                                "unexecuted_items", "rubric_screening", "faculty_analysis", "rubric_analysis",
                                "language", "report_language", "family_reports"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_blood_products_and_bleeding_orders.py::test_red_cells_are_run_in_the_units_written",
                  "test_blood_products_and_bleeding_orders.py::test_an_unmodelled_product_is_recorded_as_ordered_and_never_becomes_red_cells",
                  "test_blood_products_and_bleeding_orders.py::test_the_protocol_s_activation_is_recorded_and_gives_nothing_by_itself",
                  "test_blood_products_and_bleeding_orders.py::test_a_transfusion_that_names_no_product_is_asked_about",
                  "test_blood_products_and_bleeding_orders.py::test_nothing_the_resident_did_not_order_runs_red_cells",
                  "test_blood_products_and_bleeding_orders.py::test_red_cells_written_as_the_chart_writes_them_run_in_those_units",
                  "test_blood_products_and_bleeding_orders.py::test_two_red_cell_orders_in_one_sentence_are_one_whose_count_is_asked",
                  "test_blood_products_and_bleeding_orders.py::test_a_transfusion_stopped_kept_or_not_given_never_runs_and_is_quoted_back",
                  "test_blood_products_and_bleeding_orders.py::test_one_ratio_or_one_count_for_several_products_is_asked",
                  "test_blood_products_and_bleeding_orders.py::test_an_order_of_only_what_is_recorded_is_the_resident_s_decision_and_takes_no_minute",
                  "test_blood_products_and_bleeding_orders.py::test_crystalloid_with_ordered_plasma_is_the_faculty_s_reading_not_a_silent_met"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-28-14",
        "date": "2026-09-28",
        "title": "C7-06 y TD-22: medidas de control de hemorragia, acceso intraóseo y prueba de embarazo, por clase y EN/ES",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("C7-06 y TD-22 (ciclo 7, estándar A–J). Cada medida de control de hemorragia («pack the wound», "
                   "«hold pressure», «presión directa sobre la herida», «torniquete», «empaquetar») es su propia orden, "
                   "en el orden escrito, y ninguna se vuelve otra; «control de hemorragia» sin medida pregunta cuál; "
                   "retirar una medida, un taponamiento cardíaco, lo que otro hace o un packing quirúrgico no aplican "
                   "ninguna, y detener el sangrado con una medida es esa medida. El acceso intraóseo se registra como "
                   "tal, con su sitio, y nunca como vía venosa; retirarlo o describirlo no lo instala, y una dosis "
                   "«IO» es la vía de esa dosis. La prueba de embarazo se registra como pedida, sin resultado "
                   "inventado, y no retiene nada. Se leen además las formas naturales del conjunto independiente: el "
                   "plural del equipo, «de una vez», un hallazgo antes de la orden o negado. Sin cambios de "
                   "fisiología, puntajes ni eventos críticos."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE7,
        "affects": {"modules": ["family_parser", "family_engine", "unexecuted_items", "language"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_blood_products_and_bleeding_orders.py::test_each_bleeding_measure_is_its_own_order",
                  "test_blood_products_and_bleeding_orders.py::test_a_measure_named_by_none_is_asked_about_and_never_chosen",
                  "test_blood_products_and_bleeding_orders.py::test_what_only_mentions_a_bleeding_measure_applies_none",
                  "test_blood_products_and_bleeding_orders.py::test_stopping_the_bleeding_with_a_measure_is_the_measure",
                  "test_blood_products_and_bleeding_orders.py::test_a_measure_stopped_is_never_applied",
                  "test_blood_products_and_bleeding_orders.py::test_a_measure_removed_or_converted_is_quoted_back_never_applied",
                  "test_blood_products_and_bleeding_orders.py::test_an_intraosseous_line_is_its_own_access",
                  "test_blood_products_and_bleeding_orders.py::test_an_intraosseous_line_removed_or_described_is_never_placed",
                  "test_blood_products_and_bleeding_orders.py::test_io_after_a_dose_is_that_dose_s_route_never_a_line",
                  "test_blood_products_and_bleeding_orders.py::test_a_pregnancy_test_holds_nothing_and_no_result_is_invented",
                  "test_blood_products_and_bleeding_orders.py::test_the_pregnancy_test_is_read_in_its_natural_forms",
                  "test_blood_products_and_bleeding_orders.py::test_the_forms_of_the_independent_set_are_read",
                  "test_blood_products_and_bleeding_orders.py::test_what_the_new_readings_must_not_turn_into_an_order"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-28-15",
        "date": "2026-09-28",
        "title": "DF-24: quién confirmó, qué revisión alimenta el radar, la razón de la anulación y el aviso del borrador",
        "scope": {"level": "general"},
        "kind": "policy",
        "reason": ("Decisiones docentes DF-24 del ciclo 7 (I-F02 A, L-F02 A, anulada A, retiro A). La exportación del "
                   "perfil dice quién confirmó la rúbrica, como ya lo decía el PDF, sin cambiar ningún número. De un "
                   "mismo encuentro alimenta el radar su revisión confirmada de mayor número, como ya la elegían el "
                   "documento y la pantalla docente: un reloj atrasado ponía una revisión superada; con relojes "
                   "ordinarios nada cambia. El formulario de anulación advierte que la persona residente lee la razón, "
                   "y lo que ve de una observación anulada no cambia. Un borrador sobre una confirmación avisa que no "
                   "retira nada, sin estado «retirada». Ningún puntaje, dominio, promedio ni el método del radar "
                   "cambia."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE7,
        "affects": {"modules": ["rubric_store", "progress_portal", "rubric_portal", "report_language"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_df24_approved_integrity_changes.py::test_the_export_says_who_confirmed_the_rubric_as_the_pdf_does",
                  "test_df24_approved_integrity_changes.py::test_who_confirmed_changes_no_number",
                  "test_df24_approved_integrity_changes.py::test_a_late_clock_no_longer_puts_a_superseded_revision_in_the_radar",
                  "test_df24_approved_integrity_changes.py::test_two_confirmations_in_the_same_second_take_the_higher_number",
                  "test_df24_approved_integrity_changes.py::test_with_ordinary_clocks_nothing_changes",
                  "test_df24_approved_integrity_changes.py::test_the_void_form_says_the_resident_reads_the_reason",
                  "test_df24_approved_integrity_changes.py::test_what_the_resident_sees_of_a_voided_observation_is_unchanged",
                  "test_df24_approved_integrity_changes.py::test_a_draft_after_a_confirmation_is_said_to_withdraw_nothing",
                  "test_df24_approved_integrity_changes.py::test_no_warning_when_nothing_confirmed_stands_under_the_draft"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-28-16",
        "date": "2026-09-28",
        "title": "L-F07 B: las 9 composiciones del catálogo de hipoglicemia heredan el C14 NO de su caso de origen",
        "scope": {"level": "variant", "variants": [
            "hypoglycemia_cfg_alcohol_fasting_failed_moderate", "hypoglycemia_cfg_alcohol_fasting_working_moderate",
            "hypoglycemia_cfg_alcohol_fasting_working_severe", "hypoglycemia_cfg_insulin_failed_moderate",
            "hypoglycemia_cfg_insulin_failed_severe", "hypoglycemia_cfg_insulin_working_moderate",
            "hypoglycemia_cfg_sulfonylurea_failed_moderate", "hypoglycemia_cfg_sulfonylurea_failed_severe",
            "hypoglycemia_cfg_sulfonylurea_working_moderate"]},
        "kind": "policy",
        "reason": ("DF-24, L-F07 B (ciclo 7). Sin declaración, C14 quedaba valorable por la transición en las 9 "
                   "composiciones, aunque los 3 casos del banco de los que derivan dicen NO. Cada composición lleva "
                   "ahora la fila C14 de su caso de origen: NO, la misma razón y la firma de su revisión, con "
                   "inherited_from. Sólo se agrega C14. Los casos generados y los encuentros sin caso autorado, como "
                   "PS001, conservan la transición (DF-12); revisar PS001 (D) queda para la revisión de TD/F/C. Las "
                   "composiciones se juegan sólo en el sandbox docente, que no se valora: nada que hoy se valore "
                   "cambia."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE7,
        "affects": {"modules": ["case_assessment_bank"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_df24_approved_integrity_changes.py::test_each_composition_carries_the_c14_row_of_the_bank_case_it_derives_from",
                  "test_df24_approved_integrity_changes.py::test_a_new_composition_encounter_reads_c14_as_declared_no",
                  "test_df24_approved_integrity_changes.py::test_generated_cases_and_encounters_without_a_case_keep_the_transition"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-28-17",
        "date": "2026-09-28",
        "title": "TDFC: TD1, F1, C1 y C3 declarados caso por caso, con su componente observable y lo que queda fuera",
        "scope": {"level": "general"},
        "kind": "clinical_decision_applied",
        "reason": ("TDFC-1 a 6 y 8, aprobadas conceptualmente «según las recomendaciones actuales» (ciclo 7, §28), "
                   "se escriben en el banco con el modelo de C14 (§92): borrador, decisión, declaración por caso, "
                   "procedencia y congelada con el encuentro. Son 120 filas en 30 casos: TD1 25 YES / 5 NO, F1 25/5, C1 "
                   "18/12 y C3 10/20. TDFC-6 sigue la recomendación y no el borrador: C3 YES en las dos neumonías y "
                   "en pulmonary_embolism_61m. Cada YES nombra el componente que deja observar y lo que queda fuera del "
                   "encuentro (§30); una NO es no evaluable, nunca una falla. acs_54m_inferior espera DF-20 y conserva "
                   "la transición, igual que los casos generados, los encuentros sin caso autorado y las composiciones "
                   "de hipoglicemia. C4 sigue fuera (§93). Es prospectivo: un encuentro anterior conserva su "
                   "declaración congelada. Sin cambios en casos, eventos, dominios ni puntajes. Tabla: "
                   "docs/tdfc/TDFC_TABLA_FINAL.md."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE8,
        "affects": {"modules": ["tdfc_review", "tdfc_declarations", "case_assessment_bank", "observation_opportunities",
                                "faculty_analysis", "progress_portal", "report_language"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_tdfc_opportunities.py::test_the_bank_declares_exactly_the_rows_the_approved_decisions_derive",
                  "test_tdfc_opportunities.py::test_the_counts_are_the_totals_the_faculty_approved",
                  "test_tdfc_opportunities.py::test_tdfc_6_is_the_recommendation_not_the_draft",
                  "test_tdfc_opportunities.py::test_a_yes_names_its_component_and_what_stays_outside_and_a_no_its_reason",
                  "test_tdfc_opportunities.py::test_each_row_says_which_decision_settled_it_and_on_what_basis",
                  "test_tdfc_opportunities.py::test_a_new_encounter_freezes_the_rows_and_reads_them_as_declared",
                  "test_tdfc_opportunities.py::test_an_encounter_frozen_before_keeps_the_transition_it_started_with",
                  "test_tdfc_opportunities.py::test_generated_cases_and_encounters_without_a_case_keep_the_transition",
                  "test_tdfc_opportunities.py::test_c4_stays_out_whatever_the_case",
                  "test_observation_opportunities.py::"
                  "test_c14_c4_and_td_f_c_are_declared_and_only_the_pending_case_keeps_the_transition"],
        # The three hypoglycaemia cases now carry their TD/F/C rows: a new version of their declaration.
        "preservation": {"variants": ["hypoglycemia_28m", "hypoglycemia_76f", "hypoglycemia_54m_thiamine"],
                         "declaration": "new_version"},
    },
    {
        "id": "C-2026-09-28-18",
        "date": "2026-09-28",
        "title": "DF-16a/b/c: una lista de órdenes conserva cada orden; una repetición deja correr su orden",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Registrado en el ciclo 8 (TD-06): el registro no nombraba esta corrección del ciclo 4 (commit "
                   "643a936). En una lista escrita («Monitor, vía venosa y oxígeno por mascarilla a 8 L/min») se "
                   "perdían ítems sin aviso (DF-16a); una orden seguida de su repetición y su condición («salbutamol "
                   "5 mg nbz, repetir cada 20 minutos si persiste») no corría y quedaba sólo el plan (DF-16b); y la "
                   "vía escrita una vez al final de una lista de dosis no llegaba a cada dosis (DF-16c). Se "
                   "corrigió por clase, EN/ES, con la traza verificada; los restos quedaron en KD-01 a KD-14."),
        "authorised_by": ("Instrucción docente del 2026-09-28 que abre el ciclo 4 (DF-16a/b: listas de órdenes, "
                          "orden con repetición y condición)"),
        "affects": {"modules": ["family_parser", "shared_order_language", "unexecuted_items", "language",
                                "report_language", "app"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_lists_and_repeats_keep_every_order.py::test_a_setup_list_keeps_every_item",
                  "test_lists_and_repeats_keep_every_order.py::test_the_order_runs_and_the_repeat_is_its_plan",
                  "test_lists_and_repeats_keep_every_order.py::"
                  "test_a_route_written_after_a_list_of_doses_reaches_each_dose",
                  "test_lists_and_repeats_keep_every_order.py::test_input_execution_and_trace_through_the_real_page"],
    },
    {
        "id": "C-2026-09-28-19",
        "date": "2026-09-28",
        "title": "TD-29: «cuando», «when» y «once» hacen de una orden un plan cuando nombran el estado del paciente",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("«When BP drops, give NS 500 mL» y «Cuando baje la PA, bolo SF 500 mL» corrían ahora; «if» y «si» "
                   "ya las guardaban como plan (DF-16b). Ahora «when/whenever/once/as soon as/cuando/en cuanto/una "
                   "vez que/tan pronto como», y «apenas» con subjuntivo, son una condición cuando la cláusula nombra "
                   "un signo vital, un examen o al paciente con un cambio, un umbral o un estado por alcanzar, o "
                   "cuando lo que sigue es el curso del paciente («cuando empeore», «once stable»). Lo que el equipo "
                   "puede hacer («cuando puedas», «as soon as possible»), lo que se espera sin valor por alcanzar "
                   "(«when blood arrives»), un relato y «en cuanto a» se leen como antes. Además: lo que una "
                   "condición manda se guarda aunque el lector no pueda ejecutarlo, si la condición gobierna la "
                   "frase entera; el «if» tras «check/decidir/preguntar» es «whether»; el aviso de reconsulta en su "
                   "propia frase es indicación al paciente. Post hoc, tras el conjunto ciego: la condición sin coma "
                   "que se une a su orden, y el resultado con el valor por alcanzar («when lactate comes back >4»). "
                   "Post hoc, tras la revisión adversarial: un «cuando» dentro de lo que el residente vio no es "
                   "condición («Mareada cuando la PA baja a 80/50, SF 500 ml ev» perdía el suero sin aviso), ni en "
                   "indicativo o en pasado («cuando se acuesta la saturación cae»), ni con el residente o el equipo "
                   "como sujeto («when I examine her»), ni «once again/once more»; «then/luego» y «ahora» separan la "
                   "orden de su repetición condicionada; y la condición reconoce un umbral con cualquier nombre "
                   "(«when FSBG < 60») y el curso que la clase no nombraba («cuando se agote», «when afebrile»). "
                   "Nada que no sea un plan deja de ejecutarse: la comparación con V2 sobre todo texto del "
                   "repositorio se revisó frase por frase (docs/CICLO8_LECTOR.md). "
                   "Post hoc, tras la segunda revisión adversarial: «once» ante una razón o «now» es una dosis "
                   "(«Epinephrine 0.5 mg IM once since she is hypotensive» quedaba como plan); lo que el paciente hace "
                   "seguido de lo que se vio es relato («when she walks her sats drop», «cuando camina la sat baja», "
                   "«when SBP < 90 she gets dizzy»); un umbral hace condición aunque haya una actividad («once she "
                   "ambulates with SpO2 > 92%»); el curso que faltaba («afebril», «una vez controlado», «once tolerating "
                   "PO», «cuando camine»); y el lugar al que volver o el médico del paciente son indicación («Volver a "
                   "SAR si…», «Consultar a su médico si…»)."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE8,
        "affects": {"modules": ["family_parser"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_cycle8_reader_classes.py::test_a_condition_on_the_patient_keeps_the_order_as_a_plan",
                  "test_cycle8_reader_classes.py::test_the_order_before_the_condition_runs_and_the_one_after_it_is_the_plan",
                  "test_cycle8_reader_classes.py::test_what_the_team_can_do_a_story_and_the_same_turn_order_now",
                  "test_cycle8_reader_classes.py::test_what_a_condition_leads_to_is_kept_even_when_the_reader_cannot_run_it",
                  "test_cycle8_reader_classes.py::test_if_after_a_verb_of_finding_out_is_whether",
                  "test_cycle8_reader_classes.py::test_return_advice_in_a_sentence_of_its_own_is_advice",
                  "test_cycle8_reader_classes.py::test_a_plan_on_the_patient_runs_nothing_in_the_room",
                  "test_cycle8_reader_classes.py::test_a_when_in_what_the_resident_saw_is_no_condition",
                  "test_cycle8_reader_classes.py::test_the_order_now_runs_and_its_repeat_on_a_condition_is_the_plan",
                  "test_cycle8_reader_classes.py::test_a_condition_the_class_missed_is_a_plan",
                  "test_cycle8_reader_classes.py::test_the_account_of_the_ambulance_stays_one_plan",
                  "test_cycle8_reader_classes.py::test_once_before_a_reason_is_one_dose_given_now",
                  "test_cycle8_reader_classes.py::test_what_the_patient_does_and_what_follows_it_is_told_not_a_condition",
                  "test_cycle8_reader_classes.py::test_a_destination_on_the_patient_s_course_is_a_plan",
                  "test_cycle8_reader_classes.py::test_the_place_to_return_to_and_the_patient_s_own_doctor_are_advice",
                  "test_cycle8_reader_classes.py::test_one_dose_given_now_and_a_put_off_clearance_in_the_room"],
    },
    {
        "id": "C-2026-09-28-20",
        "date": "2026-09-28",
        "title": "TD-30: interconsultas, endoscopía, cultivos y vías escritas sin verbo ya no se pierden",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("«Surgery consult», «IC a urología», «Endoscopía urgente», «hemocultivos x2» y «2 large-bore IVs» "
                   "se perdían sin aviso. Ahora: la interconsulta escrita como sustantivo es la interconsulta, y "
                   "«cirugía/surgery» es cirugía general (una subespecialidad sigue preguntando cuál); la endoscopía "
                   "pedida es la llamada a gastroenterología, que el motor ya modela; los cultivos con su número y "
                   "sus sitios, y «take», son el examen; la vía nombrada por su número o su calibre es la vía. Lo "
                   "ya hecho, pendiente o respondido no se pide de nuevo. Post hoc, tras el conjunto ciego: "
                   "abreviaturas de servicio («IC uro», «gen surg», «cards»), «urgent scope», «endoscopía alta», «RL» "
                   "como Ringer lactato ante un volumen, «meanwhile/mientras tanto» antes de una orden, y los "
                   "exámenes unidos por «y» que cierra un estado («hemocultivos x2 y urocultivo ya tomados»). Post "
                   "hoc, tras la revisión adversarial: el estado de un examen no se lleva la orden que le sigue "
                   "(«Hemocultivos tomados y ceftriaxona 2 g ev»); el urocultivo se registra como pedido, sin "
                   "resultado, como la prueba de embarazo; una interconsulta pedida con verbo es interconsulta "
                   "aunque algo más esté «ya»; la escrita sin verbo con su estado, su negación o su fecha no se "
                   "pide; tras un alta, una derivación es el plan del paciente; «IC con FE…» es insuficiencia "
                   "cardiaca; «blood cx» son cultivos; los servicios no clínicos se leen como antes; y la "
                   "endoscopía escrita sin verbo pide su urgencia, nunca la de los antecedentes. "
                   "Post hoc, tras la segunda revisión adversarial: la interconsulta sin verbo «después del TAC» o "
                   "contada como hecha en la cláusula siguiente («IC a cirugía, ya la vio», «urgent endoscopy for "
                   "varices, done yesterday») no se pide; «IC a cirugía ya» es ahora, «ya que» es «porque» y «consult "
                   "for recs» la pide."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE8,
        "affects": {"modules": ["family_parser", "family_reports", "language"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_cycle8_reader_classes.py::test_a_consult_written_as_a_noun_is_the_consult",
                  "test_cycle8_reader_classes.py::test_an_endoscopy_asked_for_is_the_call_to_gastroenterology",
                  "test_cycle8_reader_classes.py::test_what_has_happened_or_is_pending_orders_nothing",
                  "test_cycle8_reader_classes.py::test_cultures_with_their_count_are_asked_for_beside_the_antibiotic",
                  "test_cycle8_reader_classes.py::test_a_line_named_by_its_count_or_bore_is_the_line",
                  "test_cycle8_reader_classes.py::test_rl_before_a_volume_is_lactated_ringer",
                  "test_a_route_written_before_the_drug.py::"
                  "test_in_the_meantime_opens_an_order_with_its_own_route_never_the_nasal_one",
                  "test_cycle8_reader_classes.py::test_a_study_s_state_takes_nothing_after_it",
                  "test_cycle8_reader_classes.py::test_a_urine_culture_is_asked_for_beside_the_rest",
                  "test_cycle8_reader_classes.py::test_a_urine_culture_is_recorded_with_no_result",
                  "test_cycle8_reader_classes.py::test_a_consult_asked_for_is_one_whatever_else_is_already_so",
                  "test_cycle8_reader_classes.py::test_a_consult_written_with_its_state_is_not_asked_for",
                  "test_cycle8_reader_classes.py::test_a_referral_after_a_discharge_is_the_patient_s_plan",
                  "test_cycle8_reader_classes.py::test_heart_failure_and_a_non_clinical_consult_hold_nothing",
                  "test_cycle8_reader_classes.py::test_blood_cultures_written_cx_are_not_surgery",
                  "test_cycle8_reader_classes.py::test_an_endoscopy_done_calls_no_one",
                  "test_cycle8_reader_classes.py::test_a_consult_after_something_else_or_already_done_is_not_called",
                  "test_cycle8_reader_classes.py::test_a_consult_now_or_for_recommendations_is_called"],
    },
    {
        "id": "C-2026-09-28-21",
        "date": "2026-09-28",
        "title": "TD-31: la adrenalina IM sin dosis pregunta su dosis en miligramos, nunca una velocidad",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("«Epinephrine IM now» y «Adrenalina IM ya» se leían como una infusión y el motor preguntaba una "
                   "velocidad en mcg/min. Ahora son la orden intramuscular sin dosis, y el motor pregunta la dosis "
                   "IM en miligramos, como ya hacía con una dosis fuera de rango. También con sólo su concentración "
                   "(«1:1000», «1 mg/mL»), con «epi» ante una vía, una dosis o un goteo, y con la vía escrita antes "
                   "(«IM epi stat», post hoc); el sitio de inyección escrito después es de esa orden. Post hoc, "
                   "tras la revisión adversarial: «epi» es adrenalina sólo con su dosis con unidad o su vía, "
                   "nunca ante un puntaje o un diagnóstico («Epi 8/10 pain», «EPI 1ria»), ni la dosis de otro, "
                   "de antes o de un plan («given by EMS», «20 min ago», «at home», «PRN»). La mitad de "
                   "TD-31 sobre las medidas combinadas pide una decisión y no se tocó."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE8,
        "affects": {"modules": ["family_parser"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_cycle8_reader_classes.py::test_an_intramuscular_adrenaline_without_a_dose_is_the_im_order_still_to_be_dosed",
                  "test_cycle8_reader_classes.py::test_a_dosed_im_order_and_an_infusion_read_as_before",
                  "test_cycle8_reader_classes.py::test_the_room_asks_an_undosed_im_adrenaline_its_dose_in_milligrams",
                  "test_cycle8_reader_classes.py::test_an_earlier_or_someone_else_s_epi_is_never_given",
                  "test_cycle8_reader_classes.py::test_epi_before_a_score_or_a_diagnosis_is_not_adrenaline"],
    },
    {
        "id": "C-2026-09-28-22",
        "date": "2026-09-28",
        "title": "TD-32: los residuos de hemoderivados ya no se pierden ni se leen como un pedido",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("«2 U. GR» perdía su producto en el punto; «Deactivate MTP» no dejaba registro; «Platelets if "
                   "count < 50» se perdía; «Type and cross pending» pedía otra prueba cruzada; «2 U GR en 2 horas "
                   "c/u» corría en 2 horas en total. Ahora el punto de «U.» no corta la frase; la desactivación del "
                   "protocolo queda registrada como tal (categoría massive_transfusion_stop, con su mensaje en "
                   "ambos idiomas), sin quitar ninguna unidad ya dada; las plaquetas según recuento son un plan; el "
                   "estado de las pruebas cruzadas no es un pedido; el tiempo de cada unidad se suma. Post hoc, "
                   "tras el conjunto ciego: «2u», las horas abreviadas («2 h», «hrs»), el tiempo escrito como su "
                   "propia cláusula y las plaquetas abreviadas («plts», «plaq»). Post hoc, tras la revisión "
                   "adversarial: el punto de «U.» sólo se salta ante glóbulos rojos no nombrados antes («Transfuse "
                   "PRBC 2 U. Platelets if count < 50.» son dos frases); la desactivación preguntada, sugerida o "
                   "escrita como el tiempo de otra cosa no se registra; «to be ready for the OR» es el propósito de "
                   "las pruebas cruzadas, no su estado; el control escrito en horas no es el tiempo del "
                   "tratamiento («con control de PA en 1 h»); y unas unidades que suman más de lo que el "
                   "simulador pasa se preguntan con un mensaje propio, como ya un fluido. "
                   "Post hoc, tras la segunda revisión adversarial: las unidades de otro fármaco no son glóbulos rojos "
                   "(«Insulina 10 U. GR 2 U» perdía la transfusión); una suspensión del PTM negada o pospuesta no se "
                   "registra («Can't stop MTP yet», «Suspender PTM una vez controlado el sangrado» es un plan); el "
                   "estado de las pruebas cruzadas es sólo el escrito junto a ellas («… mientras hemograma pendiente» "
                   "las pide) y no se pregunta como orden ilegible; «c/u» escrito antes del tiempo; y un torniquete «ya "
                   "puesto» no se pone de nuevo."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE8,
        "affects": {"modules": ["family_parser", "family_engine", "unexecuted_items", "rubric_screening", "language",
                                "report_language"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_cycle8_reader_classes.py::test_the_point_of_u_is_not_a_full_stop",
                  "test_cycle8_reader_classes.py::test_the_protocol_stood_down_is_recorded_and_gives_nothing",
                  "test_cycle8_reader_classes.py::test_platelets_on_a_count_are_a_plan",
                  "test_cycle8_reader_classes.py::test_the_state_of_a_crossmatch_is_not_a_new_one",
                  "test_cycle8_reader_classes.py::test_each_unit_s_time_adds_up",
                  "test_cycle8_reader_classes.py::test_a_point_after_the_count_of_named_red_cells_ends_the_sentence",
                  "test_cycle8_reader_classes.py::test_a_stand_down_asked_or_as_a_time_is_not_recorded",
                  "test_cycle8_reader_classes.py::test_a_crossmatch_with_its_purpose_is_asked_for",
                  "test_cycle8_reader_classes.py::test_when_the_patient_is_checked_is_not_how_long_the_order_runs",
                  "test_cycle8_reader_classes.py::test_units_run_one_after_another_longer_than_the_simulator_runs_are_asked",
                  "test_cycle8_reader_classes.py::test_a_volume_over_hours_is_asked_as_a_fluid_rate_is",
                  "test_cycle8_reader_classes.py::test_another_drug_s_units_are_not_given_to_the_red_cells",
                  "test_cycle8_reader_classes.py::test_a_stand_down_denied_or_put_off_is_not_recorded",
                  "test_cycle8_reader_classes.py::test_a_denied_stand_down_holds_nothing_beside_it",
                  "test_cycle8_reader_classes.py::test_a_crossmatch_s_state_is_only_what_is_written_with_it",
                  "test_cycle8_reader_classes.py::test_the_time_of_each_unit_written_before_the_time",
                  "test_cycle8_reader_classes.py::test_a_tourniquet_already_on_is_not_placed_again"],
    },
    {
        "id": "C-2026-09-28-23",
        "date": "2026-09-28",
        "title": "KD-05: «OK to discharge» y «ok para alta» son un alta; el alta conserva su receta",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("«OK to discharge with cardiology follow-up» no se leía (KD-05). Ahora el alta dicha como una "
                   "autorización es un alta, en ambos idiomas, salvo negada o preguntada. Al corregirlo aparecieron "
                   "dos pérdidas del alta anteriores al ciclo: «Discharge home with an EpiPen prescription» tomaba "
                   "toda la cláusula como receta y perdía el alta; y los medicamentos con un régimen para la casa "
                   "listados después del alta se leían como dosis y su pregunta retenía el alta. Ahora el alta corre "
                   "y lo que se lleva el paciente es su receta; los medicamentos de un ingreso no. «w/» es «with». "
                   "Post hoc, tras la revisión adversarial: «OK to d/c IV fluids» es suspender, no un alta; una "
                   "hora, un plazo o una negación después de la autorización la posponen o la niegan («OK to dc "
                   "home after 4 h observation», «OK to discharge: no»), salvo un curso del paciente, que la hace "
                   "plan («OK for d/c home once afebrile»); la autorización de otro servicio es suya («Per "
                   "surgery, OK to discharge»); «alta dosis» no es un alta; lo que se da antes de que el paciente "
                   "se vaya no es receta; y la adrenalina autoinyectable con el alta es su receta. "
                   "El defecto sigue presente en las dos líneas base registradas; el manifiesto no cambia hasta "
                   "que se elija una nueva. "
                   "Post hoc, tras la segunda revisión adversarial, que halló altas ahora donde V2 no hacía nada: una "
                   "hora, una observación, una condición o el servicio que autoriza, en cualquier parte de la oración, "
                   "posponen el alta («OK to dc home in 4 h», «OK para alta post observación de 6 horas», «OK to "
                   "discharge home, pending repeat lactate», «siempre que tolere VO», «OK para alta por urología»); la "
                   "hora del control, la receta y las indicaciones no la posponen; «no need for admission», «but needs "
                   "follow-up» y «pt home» son alta; y el autoinyector «SOS» tras un alta es su receta."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE8,
        "affects": {"modules": ["family_parser"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_cycle8_reader_classes.py::test_ok_to_discharge_is_a_discharge",
                  "test_cycle8_reader_classes.py::test_a_denied_or_asked_clearance_is_no_discharge",
                  "test_cycle8_reader_classes.py::test_a_discharge_with_its_prescription_keeps_the_discharge",
                  "test_cycle8_reader_classes.py::test_what_goes_home_with_the_patient_is_a_prescription",
                  "test_cycle8_reader_classes.py::test_an_admission_s_medicines_are_not_prescriptions",
                  "test_cycle8_reader_classes.py::test_a_clearance_that_is_not_a_discharge_now",
                  "test_cycle8_reader_classes.py::test_a_dose_given_before_the_patient_leaves_is_no_prescription",
                  "test_cycle8_reader_classes.py::test_a_consult_and_a_repeated_check_are_not_advice",
                  "test_cycle8_reader_classes.py::test_the_autoinjector_goes_home_and_one_given_now_is_given",
                  "test_cycle8_reader_classes.py::test_a_clearance_put_off_or_given_by_another_service_discharges_no_one_now",
                  "test_cycle8_reader_classes.py::test_a_clearance_with_the_plan_it_sends_home_is_a_discharge_now",
                  "test_cycle8_reader_classes.py::test_an_autoinjector_for_when_it_is_needed_goes_home_with_the_patient"],
    },
    {
        "id": "C-2026-09-28-24",
        "date": "2026-09-28",
        "title": "Deuda menor del ciclo 8: TD-23, TD-25, TD-27 y TD-28",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("TD-23: en español, la ecografía del infarto decía «mildly reducido contraction»; ahora cada "
                   "frase de movilidad parietal se dice entera en español, y también los avisos de intervención "
                   "urgente y de anulación docente. TD-25: la prueba «reperfusion prevents the block and the "
                   "arrest» se llama por lo que comprueba. TD-27: una racha de miles de espacios tardaba segundos "
                   "(14 s con 8000); ahora se lee como un espacio, en 1 ms. TD-28: una pregunta cita la orden como "
                   "el residente la escribió («Pasa pipetazo 4,5 g EV»), no la versión normalizada «administrar "
                   "pipetazo 4.5 g ev». Sin cambios en lo que se ejecuta."),
        "authorised_by": INSTRUCTION_2026_09_28_CYCLE8,
        "affects": {"modules": ["language", "family_parser", "test_acs_reperfusion"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_acs_reperfusion.py::test_reperfusion_prevents_the_arrest_and_the_shock",
                  "test_spanish_orders.py::test_an_unreadable_order_with_a_dose_is_quoted_back",
                  "test_cycle8_minor_debt.py::test_the_wall_motion_of_an_occlusion_is_said_whole_in_spanish",
                  "test_cycle8_minor_debt.py::test_the_urgent_and_override_notices_are_said_in_spanish",
                  "test_cycle8_minor_debt.py::test_a_long_run_of_spaces_is_read_at_once",
                  "test_cycle8_minor_debt.py::test_a_question_quotes_the_order_as_it_was_written"],
    },
    {
        "id": "C-2026-09-29-01",
        "date": "2026-09-29",
        "title": "TD-39: un alta para más tarde es un plan de destino, registrado y no realizado ahora",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Un alta con su propio plazo («Discharge home in 2 hours», «Alta en 2 horas», «alta mañana»), tras "
                   "una observación o un resultado («Observe 6 h then discharge home», «Observar 4 horas y luego "
                   "alta», «Discharge after repeat troponin», «Alta tras 6 horas de observación») o con un plazo "
                   "escrito después («Alta, mañana») se daba ahora, en el V2, en 939978a y en el ciclo 8, y cerraba el "
                   "encuentro con el alta que dispara los eventos críticos definidos sobre ella. Ahora es un plan de "
                   "destino: se registra con las palabras del residente, no se realiza y el Trace lo distingue de un "
                   "alta realizada. El alta condicional se dice igual. «OK to discharge…» aplazado, que se perdía sin "
                   "aviso, es el mismo plan. Lo pedido para ahora en la misma oración corre; la observación de D4 que el "
                   "alta espera corre; una reevaluación seguida de «y luego alta» ya no se traga el alta ni le presta "
                   "su verbo. El alta inmediata, negada, preguntada o de otro servicio no cambia."),
        "authorised_by": INSTRUCTION_2026_09_29_CYCLE9,
        "affects": {"modules": ["family_parser", "unexecuted_items", "language", "report_language"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_cycle9_prevalidation_hardening.py::test_an_immediate_discharge_still_runs",
                  "test_cycle9_prevalidation_hardening.py::test_a_discharge_for_later_is_a_disposition_plan_not_a_discharge_now",
                  "test_cycle9_prevalidation_hardening.py::test_a_denied_asked_or_someone_else_s_discharge_runs_nothing",
                  "test_cycle9_prevalidation_hardening.py::test_what_is_ordered_for_now_runs_beside_the_plan",
                  "test_cycle9_prevalidation_hardening.py::test_the_plan_keeps_the_resident_s_words",
                  "test_cycle9_prevalidation_hardening.py::test_a_planned_discharge_does_not_close_the_encounter_and_the_trace_says_it_is_a_plan",
                  "test_cycle9_prevalidation_hardening.py::test_an_immediate_discharge_still_closes_it",
                  "test_cycle9_prevalidation_hardening.py::test_a_planned_discharge_is_no_executed_discharge_for_the_critical_events"],
    },
    {
        "id": "C-2026-09-29-02",
        "date": "2026-09-29",
        "title": "TD-34: una reevaluación en horas espera sus minutos: «Reassess in 1 h» son 60, nunca 0",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("«Reevaluar en 1 h», «Reassess in 1 hr» o «en 2 h» corrían a los 0 minutos, sin aviso: el tiempo no "
                   "avanzaba y el residente veía al paciente como si no hubiera pasado nada. «1 hour» o «1,5 horas» "
                   "preguntaban los minutos. Ahora el intervalo se lee en minutos u horas (h, hr, hrs, hora, hour, "
                   "media hora, una hora y media, 1 h 30 min) y un solo valor, los minutos, va al motor, al reloj y al "
                   "Trace. La «h» es hora sólo después de un número; un intervalo que no se lee se pregunta, nunca se "
                   "toma como «ahora». El motor sigue aceptando de 0 a 120 minutos."),
        "authorised_by": INSTRUCTION_2026_09_29_CYCLE9,
        "affects": {"modules": ["family_parser"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_cycle9_prevalidation_hardening.py::test_the_interval_is_its_minutes",
                  "test_cycle9_prevalidation_hardening.py::test_an_interval_it_cannot_read_is_asked_never_taken_as_now",
                  "test_cycle9_prevalidation_hardening.py::test_one_hour_is_sixty_minutes_on_the_clock_and_in_the_record"],
    },
    {
        "id": "C-2026-09-29-03",
        "date": "2026-09-29",
        "title": "TD-36: un tratamiento recibido antes de la atención del residente es historia, no una orden",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Una dosis escrita antes de quien la dio se daba de nuevo («Epinephrine 0.5 mg IM given by EMS», «NS 1 L "
                   "given en route», «Adrenalina 0,5 mg IM dada por SAMU») o se preguntaba como orden del residente "
                   "(«Aspirin 300 mg given by EMS» retenía la adrenalina escrita al lado); lo que el paciente «ya "
                   "recibió» se perdía, y la difenhidramina del SAMU quedaba como decisión del residente. Ahora es "
                   "tratamiento previo, según lo informado: se registra con qué, dosis, vía, quién y cuándo, nunca se "
                   "administra ni es orden del residente, para cualquier fármaco, fluido, hemoderivado o medida. El "
                   "verbo propio del residente («give», «repeat», «continue») o «now» lo hacen su orden."),
        "authorised_by": INSTRUCTION_2026_09_29_CYCLE9,
        "affects": {"modules": ["family_parser", "unexecuted_items", "language", "report_language"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_cycle9_prevalidation_hardening.py::test_a_treatment_received_before_is_history_never_given_again",
                  "test_cycle9_prevalidation_hardening.py::test_the_resident_s_order_beside_it_runs",
                  "test_cycle9_prevalidation_hardening.py::test_the_resident_s_own_order_is_still_theirs",
                  "test_cycle9_prevalidation_hardening.py::test_what_was_received_is_recorded_with_its_dose_route_and_source",
                  "test_cycle9_prevalidation_hardening.py::test_it_is_never_given_nor_the_resident_s_decision"],
    },
    {
        "id": "C-2026-09-29-04",
        "date": "2026-09-29",
        "title": "TD-33: para la regla de sobrecarga en trauma, sólo la sangre repone el déficit hemorrágico",
        "scope": {"level": "family", "family": "trauma"},
        "kind": "clinical_decision_applied",
        "reason": ("Residuo de TD-21: con el sangrado controlado y la pérdida «repuesta» con cristaloide (torniquete + 3 L "
                   "de SF), transfundir 2 U disparaba la sobrecarga, porque la regla contaba el cristaloide como "
                   "reposición del déficit. Decisión docente del ciclo 9 (TD-33 aprobado): para esa regla sólo la "
                   "sangre repone el déficit. El cristaloide conserva sus efectos hemodinámicos en la fisiología; la "
                   "sobretransfusión real después de reponer el déficit con sangre se sigue detectando. No cambian la "
                   "fisiología general de fluidos, la hemoglobina, los eventos críticos, el −3 ni la rúbrica."),
        "authorised_by": INSTRUCTION_2026_09_29_CYCLE9,
        "affects": {"modules": ["trauma_hemorrhage"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_cycle9_prevalidation_hardening.py::test_crystalloid_before_blood_no_longer_makes_appropriate_blood_an_overload",
                  "test_cycle9_prevalidation_hardening.py::test_a_real_overtransfusion_after_the_loss_is_replaced_is_still_one",
                  "test_cycle9_prevalidation_hardening.py::test_the_crystalloid_keeps_its_haemodynamic_effect",
                  "test_transfusion_overload.py::test_once_the_bleeding_is_controlled_and_the_loss_replaced_more_blood_overloads_again"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-29-05",
        "date": "2026-09-29",
        "title": "DF-20 cerrado sin cambios: acs_54m_inferior declara TD1, F1, C1 y C3",
        "scope": {"level": "variant", "family": "acs", "variants": ["acs_54m_inferior"]},
        "kind": "clinical_decision_applied",
        "reason": ("DF-20 se cierra sin cambiar la fisiología del caso: un compromiso fisiológico del VD puede coexistir con "
                   "un POCUS cualitativo de urgencias normal o no diagnóstico; el tamaño y la función del VD, la VCI y el "
                   "modelo hemodinámico no cambian y su C14 sigue NO. Sus filas TDFC dejan de esperar y son las que ya "
                   "derivaban las decisiones aprobadas (TD1, F1 y C1 YES, esta por TDFC-5; C3 NO), escritas sobre la "
                   "fisiología, el monitor y el ECG, nunca sobre el POCUS. La tabla final y la matriz se regeneraron; "
                   "los totales son los aprobados (26/5, 26/5, 19/12 y 10/21). Un encuentro anterior conserva la "
                   "transición con que se congeló."),
        "authorised_by": INSTRUCTION_2026_09_29_CYCLE9,
        "affects": {"modules": ["tdfc_declarations", "tdfc_review", "case_assessment_bank"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_cycle9_prevalidation_hardening.py::test_acs_54m_inferior_declares_the_rows_the_approved_decisions_derived",
                  "test_cycle9_prevalidation_hardening.py::test_none_of_its_rows_rests_on_the_pocus",
                  "test_cycle9_prevalidation_hardening.py::test_a_new_encounter_freezes_its_rows_as_declared",
                  "test_tdfc_opportunities.py::test_the_counts_are_the_totals_the_faculty_approved",
                  "test_tdfc_opportunities.py::test_the_published_final_table_is_the_bank_s"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-29-06",
        "date": "2026-09-29",
        "title": "DF-23 fila 4a: el pulmón del POCUS de acs_70f_left_main dice lo que dicen su examen y su radiografía",
        "scope": {"level": "variant", "family": "acs", "variants": ["acs_70f_left_main"]},
        "kind": "clinical_decision_applied",
        "reason": ("El POCUS decía «No B-lines; A-line pattern bilaterally», el valor por defecto, frente a crépitos "
                   "basales en el examen, congestión leve en la radiografía y «hypoperfusion and congestion» como rasgo "
                   "clave. Se aplica el texto propuesto en el ciclo 7: «Scattered B-lines at both bases; no diffuse "
                   "B-line pattern», con su borrador en español «Líneas B dispersas en ambas bases; sin patrón difuso de "
                   "líneas B». No cambian el desafío de decisión, el objetivo de manejo, la fila C14, TDFC, los eventos "
                   "críticos ni la fisiología; las filas 4b, 6, 7 y 8 siguen en la cola. El español del caso vuelve a "
                   "esperar la revisión docente donde estaba aprobado: no se registra ninguna aprobación."),
        "authorised_by": INSTRUCTION_2026_09_29_CYCLE9,
        "affects": {"modules": ["clinical_cases", "case_text"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_cycle9_prevalidation_hardening.py::test_the_left_main_case_s_pocus_lungs_agree_with_its_examination_and_film",
                  "test_cycle9_prevalidation_hardening.py::test_its_spanish_draft_says_the_same_and_waits_for_review"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-29-07",
        "date": "2026-09-29",
        "title": "Revisión adversarial del ciclo 9: lo que halló en TD-39, TD-34 y TD-36, corregido dentro de su clase",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Una revisión independiente con 130 frases preregistradas no halló ninguna fila peor que el ciclo 8; "
                   "sus 54 frases posteriores hallaron tres regresiones y fallas de la misma clase, corregidas según "
                   "§90. Regresiones: «Alta ahora tras 6 h de observación» (el «ahora» explícito vuelve a dar el alta "
                   "ahora; una espera o condición escrita después, «OK to discharge now, pending repeat lactate», "
                   "sigue siendo un plan) y «Tras 3 nebulizaciones PEF 80%, alta con prednisona» (un valor medido sin umbral ni espera "
                   "declarada es un paso cumplido). «Tras 6 h de observación sin incidencias, alta» sigue como plan: una "
                   "espera de duración declarada es una espera. Altas falsas de TD-39: un reloj de cuatro cifras («at "
                   "1800») y un plazo al final de lo que el alta manda a casa («con EpiPen en 2 horas»), salvo que ese "
                   "plazo sea de un control, una dosis o un inicio. Readministración de TD-36 (adrenalina y "
                   "corticoides): dónde se dio antes de urgencias («given at OSH», «dada en su centro de salud», «at "
                   "work») y hace cuánto («given 20 min ago», «hace 20 minutos») la hacen tratamiento previo; una orden "
                   "que nombra otra dosis («última dosis hace 20 min») sigue siendo del residente. TD-34: «1 h 30» y "
                   "«1h30» son 90 minutos, no 60. Lo demás que halló (vocabulario «d/c», «repeat», «20'», órdenes "
                   "retenidas por un fragmento) es previo al ciclo 9 y queda como deuda."),
        "authorised_by": INSTRUCTION_2026_09_29_CYCLE9,
        "affects": {"modules": ["family_parser"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_cycle9_prevalidation_hardening.py::test_the_forms_the_review_found_are_plans_too",
                  "test_cycle9_prevalidation_hardening.py::test_a_discharge_now_the_review_found_still_runs",
                  "test_cycle9_prevalidation_hardening.py::test_the_interval_is_its_minutes",
                  "test_cycle9_prevalidation_hardening.py::test_where_and_how_long_ago_it_was_given_make_it_history_too",
                  "test_cycle9_prevalidation_hardening.py::test_an_order_that_names_an_earlier_dose_is_still_the_resident_s",
                  "test_cycle9_prevalidation_hardening.py::test_how_long_ago_is_kept_as_its_time",
                  "test_cycle9_prevalidation_hardening.py::test_the_review_s_epinephrine_given_elsewhere_is_not_given_again_and_its_timed_discharge_waits"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-29-08",
        "date": "2026-09-29",
        "title": "Segunda revisión del ciclo 9: lo que halló en las correcciones de la primera, corregido",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("Una revisión pequeña e independiente de las correcciones de C-2026-09-29-07 (70 frases "
                   "preregistradas) halló 0 CRITICAL y 8 HIGH. Frente al lector anterior a esas correcciones, cinco eran "
                   "regresiones suyas y se corrigen: «immediately after completing 6 h of observation» es una espera, "
                   "no «ahora»; una condición escrita después del «ahora» («siempre que tolere la vía oral», «provided "
                   "she stays asymptomatic») sigue haciendo un plan; una espera escrita en palabras («Tras una hora de "
                   "observación con SatO2 97%») es una espera; lo que el alta manda a casa («con prednisona hasta "
                   "completar 5 días») no es condición del alta; y una orden y el relato de otra dosis a cada lado de un "
                   "guion («Top up aspirin to 300 mg - 81 mg given at urgent care») no son un solo relato: se pregunta, "
                   "como antes. Una más, anterior al ciclo y de la clase de TD-39, también: lo visto entre una espera y "
                   "el alta pertenece a la espera («After four hours of observation, BP 118/72, discharge home»). Lo "
                   "MEDIUM y LOW que halló queda como deuda (KD-20 a KD-24)."),
        "authorised_by": INSTRUCTION_2026_09_29_CYCLE9,
        "affects": {"modules": ["family_parser"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_cycle9_prevalidation_hardening.py::test_the_forms_the_review_found_are_plans_too",
                  "test_cycle9_prevalidation_hardening.py::test_a_discharge_now_the_review_found_still_runs",
                  "test_cycle9_prevalidation_hardening.py::test_an_order_and_an_account_of_another_dose_are_not_one_account"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-29-09",
        "date": "2026-09-29",
        "title": "La prueba de la sala y el banco de imágenes pasaba o fallaba según el caso sorteado",
        "scope": {"level": "general"},
        "kind": "technical_defect",
        "reason": ("La suite completa del ciclo 9 halló test_image_bank_portal::test_a_residents_encounter_room_uses_the_"
                   "bank fallando una vez de cada tres, sin cambios. La sala abre un caso al azar; si su apariencia es "
                   "una que el generador de imágenes no dibuja con fiabilidad (mascarilla con reservorio, o sudor marcado "
                   "en piel oscura, decisión docente 6), el banco responde UNRENDERABLE antes de mirar la configuración, "
                   "y la prueba sólo aceptaba CONFIG o NOT_ALLOWED. La respuesta es la correcta: la prueba la acepta. "
                   "El código de la aplicación no cambia."),
        "authorised_by": INSTRUCTION_2026_09_29_CYCLE9,
        "affects": {"modules": ["test_image_bank_portal"], "versions": {}},
        "clinical_relevance": "none",
        "tests": ["test_image_bank_portal.py::test_a_residents_encounter_room_uses_the_bank"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-29-10",
        "date": "2026-09-29",
        "title": "TEP: el shock obstructivo atribuible indica la trombólisis de inmediato; la noradrenalina sola nunca",
        "scope": {"level": "family", "family": "pulmonary_embolism"},
        "kind": "clinical_decision_applied",
        "reason": ("D revisada. Un shock obstructivo atribuible al TEP (PAS < 90, o un vasopresor que la necesita "
                   "para sostener 90, con al menos un signo de hipoperfusión: conciencia alterada, periferia con llene "
                   "de 3,5 s o más, lactato interno > 2 mmol/L) cumple el criterio desde la llegada o cuando aparece. "
                   "Sin hipoperfusión, la hipotensión cuenta 15 minutos completos y consecutivos; una recuperación "
                   "real reinicia la cuenta. Iniciar noradrenalina no crea la indicación. La presión se atribuye antes "
                   "de redondear y separa las caídas por fármacos y el sangrado tras la lisis. Cada orden se juzga con "
                   "el estado de su minuto; una segunda dosis queda registrada como repetición. Cada trombolítico "
                   "lleva su motivo estructurado (versión 2) y el tamizaje de pe_unindicated_thrombolysis lo lee; un "
                   "registro anterior se lee con la regla de su tiempo. Quedan aparte la farmacología de la lisis no "
                   "indicada, la seguridad de repetir dosis y la redacción de D3, C1 y TDFC. "
                   "docs/PULMONARY_EMBOLISM_MAGNITUDES.md."),
        "authorised_by": INSTRUCTION_2026_09_29_POST_V3,
        "affects": {"modules": ["pe_obstruction", "family_engine", "generated_pe", "coupled_encounter",
                                "rubric_screening", "management_trace_analysis", "language", "generated_case",
                                "generated_pe_consistency"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_pe_obstruction.py::test_one_sign_of_hypoperfusion_makes_a_hypotension_obstructive_shock_at_once",
                  "test_pe_obstruction.py::test_the_clock_counts_only_consecutive_minutes",
                  "test_pe_obstruction.py::test_starting_norepinephrine_creates_no_indication",
                  "test_pe_obstruction.py::test_a_pressure_held_up_by_a_vasopressor_it_needs_still_counts",
                  "test_pe_obstruction.py::test_a_drug_induced_drop_keeps_its_effect_and_is_not_the_embolism_s_shock",
                  "test_pe_obstruction.py::test_bleeding_after_a_thrombolytic_is_not_the_embolism_s_shock",
                  "test_pe_obstruction.py::test_a_persisting_shock_does_not_make_a_second_dose_indicated",
                  "test_pe_obstruction.py::test_each_thrombolytic_summary_carries_its_basis_minute_and_data",
                  "test_generated_pe.py::test_starting_a_vasopressor_creates_no_indication",
                  "test_generated_pe.py::test_thrombolysis_in_obstructive_shock_dissolves_the_obstruction",
                  "test_pe_thrombolysis_screening.py::test_a_vasopressor_she_did_not_need_no_longer_hides_the_event",
                  "test_pe_thrombolysis_screening.py::test_a_recorded_basis_excludes_the_event",
                  "test_pe_thrombolysis_screening.py::test_an_old_record_keeps_the_rule_of_its_own_time"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-29-11",
        "date": "2026-09-29",
        "title": "DC1: la conciencia escrita al llegar es la que el motor muestra, sin volver a leerla",
        "scope": {"level": "variant", "variants": ["bradycardia_ccb_68m", "pulmonary_edema_58m", "pulmonary_edema_75f",
                                                   "hypoglycemia_28m", "hypoglycemia_54m_thiamine"]},
        "kind": "clinical_decision_applied",
        "reason": ("Cinco casos llegaban con una conciencia escrita mejor que la que el umbral del motor da a sus "
                   "valores, y al minuto 1 el motor la reescribía sin cambio fisiológico (Alert a Drowsy con PAS 74 o "
                   "SpO₂ 81-84; Drowsy a Obtunded con glucosa 32-34). Ahora el encuentro fija al empezar sólo los "
                   "umbrales que su llegada ya cruzaba, entre el valor de llegada y el umbral siguiente que se "
                   "mantiene; compara antes de redondear y deja un nivel peor que el de llegada sólo pasado un margen "
                   "(PAS 2, SpO₂ 1, glucosa 1 mg/dL). Mejorar más allá de la llegada usa el umbral de siempre. Se "
                   "conservan el deterioro real, la convulsión y el estado postictal, la sedación, la intubación y la "
                   "recuperación; una glucosa mejor ya no muestra un paciente peor. Los otros 26 casos no llevan ancla "
                   "y leen igual que antes; un encuentro empezado antes conserva su regla."),
        "authorised_by": INSTRUCTION_2026_09_29_POST_V3,
        "affects": {"modules": ["family_engine", "hypoglycemia_battery"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_arrival_consciousness.py::test_the_first_minutes_show_the_consciousness_written_at_arrival",
                  "test_arrival_consciousness.py::test_only_the_arrivals_that_needed_it_carry_an_anchor",
                  "test_arrival_consciousness.py::test_a_value_hovering_at_a_threshold_does_not_flicker",
                  "test_arrival_consciousness.py::test_a_real_fall_in_pressure_still_takes_consciousness_down",
                  "test_arrival_consciousness.py::test_a_better_glucose_never_shows_a_worse_patient",
                  "test_arrival_consciousness.py::test_a_seizure_and_its_post_ictal_state_are_untouched",
                  "test_arrival_consciousness.py::test_an_encounter_started_before_the_rule_keeps_the_rule_it_began_with",
                  "test_hypoglycemia_battery.py::test_the_arrival_consciousness_is_what_the_engine_shows_at_minute_one"],
        # The two anchored hypoglycaemia cases: the arrival reads as written, and the
        # engine state carries the anchor, so every script that runs the engine changes.
        "preservation": {"variants": ["hypoglycemia_28m", "hypoglycemia_54m_thiamine"],
                         "scripts": ["admission", "double_ampoule", "early_discharge", "ed_observation", "examinations", "existing_line_dextrose", "failed_line_then_new_line", "glucagon_im", "glucagon_iv_existing_line", "infusion_after_ampoule", "infusion_existing_line", "intraosseous_dextrose", "new_line_then_dextrose", "octreotide_iv_existing_line", "octreotide_sc", "oral_after_recovery", "thiamine_then_dextrose", "untreated"]},
    },
    {
        "id": "C-2026-09-29-12",
        "date": "2026-09-29",
        "title": "POCUS de la HDA: la VCI y el VI leen el llenado que el motor modela, no el volumen acumulado",
        "scope": {"level": "variant", "variants": ["gi_bleed_57m", "gi_bleed_72f"]},
        "kind": "clinical_decision_applied",
        "reason": ("DF-23 fila 11 (VCI y VI en la HDA). La VCI se leía del volumen acumulado (≥ 500 mL: 1,5 cm; ≥ "
                   "1500 mL: 2,0 cm) y el VI nunca cambiaba: tras 1 L de cristaloide y una hora la paciente estaba "
                   "peor que al llegar (80/50) con una VCI «1,5 cm», y tras 2 U el VI seguía «casi obliterado». Ahora "
                   "ambos leen la circulación de la familia, que ya integra la reposición, el sangrado que sigue y el "
                   "cristaloide que dejó los vasos, y que un vasopresor no cambia: una escala de vacío a lleno en la "
                   "que cada caso entra por su hallazgo escrito y se mueve una posición por cada 0,30 de circulación "
                   "(parámetro docente). La cavidad y la contracción van separadas: llenar termina la obliteración y "
                   "la contracción sigue hiperdinámica hasta que la recuperación que alivia la taquicardia está en "
                   "curso (alivio ≥ 0,5). Con presión positiva se conserva el diámetro y la variación respiratoria no "
                   "se evalúa. Las otras familias conservan su regla. Textos nuevos con su español."),
        "authorised_by": INSTRUCTION_2026_09_29_POST_V3,
        "affects": {"modules": ["family_engine", "language"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_gi_bleed_pocus.py::test_the_arrival_scan_is_the_one_the_case_wrote",
                  "test_gi_bleed_pocus.py::test_blood_fills_the_cava_and_ends_the_obliteration_without_calming_the_heart",
                  "test_gi_bleed_pocus.py::"
                  "test_the_contraction_settles_only_once_the_bleeding_is_controlled_and_the_patient_recovers",
                  "test_gi_bleed_pocus.py::test_crystalloid_that_leaves_the_vessels_leaves_the_cava_empty_again",
                  "test_gi_bleed_pocus.py::test_bleeding_that_goes_on_empties_the_cava",
                  "test_gi_bleed_pocus.py::test_a_vasopressor_raises_the_pressure_without_filling_anything",
                  "test_gi_bleed_pocus.py::test_positive_pressure_keeps_the_diameter_and_withholds_the_respiratory_variation",
                  "test_gi_bleed_pocus.py::test_other_families_keep_their_own_rule",
                  "test_gi_bleed_pocus.py::test_every_recomputed_finding_is_said_in_spanish"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-29-13",
        "date": "2026-09-29",
        "title": "TD-31: las medidas sobre una fuente externa no se suman; el registro dice si el sangrado disminuye o se detiene",
        "scope": {"level": "family", "family": "trauma"},
        "kind": "clinical_decision_applied",
        "reason": ("Resto de TD-31. Cada medida sumaba su control (0,75) hasta el tope: mantener o reformular la "
                   "compresión, o taponar con compresión, llegaba al nivel del torniquete y el sangrado arterial se "
                   "detenía (0 mL/min); y la sala decía «controlled» tanto para una compresión como para un "
                   "torniquete. Ahora una fuente conserva la mejor medida aplicada, nunca una suma: la compresión "
                   "repetida, mantenida o reformulada no agrega control y el taponamiento con compresión es una sola "
                   "intervención (36 mL/min en trauma_limb_hemorrhage_27m); sólo una técnica más eficaz lo sube (el "
                   "torniquete detiene la fuente). Magnitudes sin cambio y provisionales (compresión y taponamiento "
                   "0,75; torniquete 1,0). El registro dice «reduced, not stopped», «stopped» o que la medida no "
                   "agrega control, en inglés y en español; un registro anterior conserva sus palabras. El tamizaje "
                   "lee la acción, nunca el nivel: trauma_no_hemorrhage_control da lo mismo que antes."),
        "authorised_by": INSTRUCTION_2026_09_29_POST_V3,
        "affects": {"modules": ["trauma_hemorrhage", "family_engine", "language"], "versions": {}},
        "clinical_relevance": "clinical",
        "tests": ["test_hemostasis_is_not_a_sum.py::test_pressure_held_again_adds_no_control",
                  "test_hemostasis_is_not_a_sum.py::test_packing_with_pressure_is_one_intervention_written_together_or_apart",
                  "test_hemostasis_is_not_a_sum.py::test_a_more_effective_technique_still_raises_the_control",
                  "test_hemostasis_is_not_a_sum.py::test_a_tourniquet_alone_stops_it_and_pressure_after_it_changes_nothing",
                  "test_hemostasis_is_not_a_sum.py::test_the_record_says_reduced_or_stopped_in_both_languages",
                  "test_hemostasis_is_not_a_sum.py::test_the_scoring_reads_the_action_never_the_level",
                  "test_blood_products_and_bleeding_orders.py::test_each_bleeding_measure_acts_and_is_said_as_written"],
        "preservation": None,
    },
    {
        "id": "C-2026-09-29-14",
        "date": "2026-09-29",
        "title": "Hipoglicemia DC2–DC5: la falla es de la vía, no de la glucosa en bolo",
        "scope": {"level": "family", "family": "hypoglycemia"},
        "kind": "clinical_decision_applied",
        "reason": ("Un solo mecanismo (glucose_rescue 2.0). DC2: las 12 configuraciones declaran al llegar la misma "
                   "cánula en el antebrazo izquierdo, sin decir si funciona (28m y 76f no traen paramédicos en su "
                   "relato, así que no se nombra quién la puso); una vía nueva se instala y se dice igual con o sin "
                   "falla; nada dice «replaced» ni «What is given now reaches»; la falla se descubre en el sitio (una "
                   "observación al primer uso y la región «Vascular access» del control Examinar, disponible desde "
                   "la llegada) y en una respuesta que no alcanza; el 15 % queda en el registro técnico. DC4: por la "
                   "cánula fallida llega el 15 % de lo que corre por ella -- bolo, infusión y medicamentos "
                   "endovenosos --; lo IM, SC, IN y oral no pasa por ella. La glucosa actúa en proporción; el "
                   "glucagón y el octreótido conservan su efecto modelado y el registro dice que es una decisión "
                   "farmacológica pendiente (DC4-F); la tiamina sólo se registra, sin efecto ni cambio de peso. DC3: "
                   "una dosis intraósea válida instala su aguja con su minuto, sin sitio inventado ni orden propia, "
                   "llega entera y no repara la cánula; las vías no soportadas (glucagón u octreótido IO) siguen "
                   "rechazadas. DC5: una infusión que corre por la cánula de llegada pasa a la vía siguiente con su "
                   "acceso, velocidad y minuto; una detenida no se reinicia y nada se repite para compensar. Un "
                   "encuentro empezado con 1.0 conserva su regla. El lector no cambia."),
        "authorised_by": INSTRUCTION_2026_09_29_POST_V3,
        "affects": {"modules": ["glucose_rescue", "family_engine", "arrival_brief", "hypoglycemia_battery",
                                "hypoglycemia_catalog", "language"],
                    "versions": {"glucose_rescue": {"from": "1.0", "to": "2.0"}}},
        "clinical_relevance": "clinical",
        "tests": ["test_hypoglycemia_lines.py::test_every_configuration_declares_the_same_cannula_and_never_its_state",
                  "test_hypoglycemia_lines.py::test_a_new_line_is_placed_and_said_the_same_whether_the_old_one_runs",
                  "test_hypoglycemia_lines.py::test_the_share_that_arrives_stays_in_the_technical_record",
                  "test_hypoglycemia_lines.py::test_the_site_can_be_examined_before_anything_is_given",
                  "test_hypoglycemia_lines.py::test_using_the_failed_line_shows_at_the_site_once_and_stays_on_examination",
                  "test_hypoglycemia_lines.py::test_the_infusion_through_the_failed_line_arrives_only_in_part",
                  "test_hypoglycemia_lines.py::test_what_does_not_run_through_a_line_does_not_depend_on_it",
                  "test_hypoglycemia_lines.py::test_glucagon_through_the_failed_line_keeps_its_modelled_effect_and_says_why",
                  "test_hypoglycemia_lines.py::test_thiamine_is_recorded_as_given_where_it_went_and_does_nothing_else",
                  "test_hypoglycemia_lines.py::"
                  "test_a_valid_intraosseous_dose_places_its_needle_with_its_minute_and_no_invented_site",
                  "test_hypoglycemia_lines.py::test_the_needle_never_repairs_the_cannula",
                  "test_hypoglycemia_lines.py::test_a_route_the_drug_does_not_have_is_not_widened",
                  "test_hypoglycemia_lines.py::test_a_running_infusion_moves_to_the_new_line_with_its_access_rate_and_minute",
                  "test_hypoglycemia_lines.py::test_a_stopped_infusion_stays_stopped",
                  "test_hypoglycemia_lines.py::test_an_encounter_begun_under_1_0_keeps_its_rule",
                  "test_hypoglycemia_battery.py::test_the_failed_line_holds_back_everything_that_runs_through_it",
                  "test_blood_products_and_bleeding_orders.py::test_the_intraosseous_line_is_its_own_access_and_repairs_nothing"],
        # Every catalogued encounter now carries its arrival cannula, and a new line is
        # placed in a working configuration too: every script that runs the engine changes.
        "preservation": {"variants": ["hypoglycemia_28m", "hypoglycemia_76f", "hypoglycemia_54m_thiamine"],
                         "scripts": ["admission", "double_ampoule", "early_discharge", "ed_observation", "examinations", "existing_line_dextrose", "failed_line_then_new_line", "glucagon_im", "glucagon_iv_existing_line", "infusion_after_ampoule", "infusion_existing_line", "intraosseous_dextrose", "new_line_then_dextrose", "octreotide_iv_existing_line", "octreotide_sc", "oral_after_recovery", "thiamine_then_dextrose", "untreated"]},
    },
)


def by_id(correction_id):
    return next((entry for entry in CORRECTIONS if entry["id"] == correction_id), None)


def preserved_differences():
    """What the preservation test accepts, from the entries that declare it."""
    allowed = {"variant_fields": {}, "scripts": {}, "declarations": set()}
    for entry in CORRECTIONS:
        declared = entry.get("preservation")
        if not declared:
            continue
        for variant in declared.get("variants") or [declared["variant"]]:
            allowed["variant_fields"].setdefault(variant, set()).update(declared.get("variant_fields", ()))
            allowed["scripts"].setdefault(variant, set()).update(declared.get("scripts", ()))
            if declared.get("declaration") == "new_version":
                allowed["declarations"].add(variant)
    return allowed


def cosmetic_waivers():
    """Fingerprint changes declared cosmetic: the only ones a clinical review survives."""
    return [dict(change) for entry in CORRECTIONS if entry["clinical_relevance"] == "cosmetic"
            for change in entry.get("fingerprint_changes", ())]
