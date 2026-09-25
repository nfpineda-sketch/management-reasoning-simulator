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
