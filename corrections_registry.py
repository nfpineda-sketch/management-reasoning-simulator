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
        variant = declared["variant"]
        allowed["variant_fields"].setdefault(variant, set()).update(declared.get("variant_fields", ()))
        allowed["scripts"].setdefault(variant, set()).update(declared.get("scripts", ()))
        if declared.get("declaration") == "new_version":
            allowed["declarations"].add(variant)
    return allowed


def cosmetic_waivers():
    """Fingerprint changes declared cosmetic: the only ones a clinical review survives."""
    return [dict(change) for entry in CORRECTIONS if entry["clinical_relevance"] == "cosmetic"
            for change in entry.get("fingerprint_changes", ())]
