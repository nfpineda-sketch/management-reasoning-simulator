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
