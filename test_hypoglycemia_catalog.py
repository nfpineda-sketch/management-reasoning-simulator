"""The hypoglycaemia catalogue: one source, typed compatibilities, candidates kept from residents."""
from copy import deepcopy
import json

import pytest

import case_catalog
import glucose_rescue
import hypoglycemia_catalog as catalog


def test_the_bank_is_three_configurations_of_the_catalogue():
    from clinical_cases import FAMILIES
    bank = catalog.bank_configurations()
    assert [c["id"] for c in bank] == [v["id"] for v in FAMILIES["hypoglycemia"]["variants"]] == [
        "hypoglycemia_28m", "hypoglycemia_76f", "hypoglycemia_54m_thiamine"]
    for configuration, variant in zip(bank, FAMILIES["hypoglycemia"]["variants"]):
        flags = catalog.case_arguments(configuration)["flags"]
        assert variant["engine"]["recurrence_risk"] is flags["recurrence"]
        for name in ("endogenous_insulin", "thiamine_deficient", "iv_access_failed", "glycogen_depleted"):
            assert bool(variant["engine"].get(name)) is flags[name], (variant["id"], name)
        assert variant["observable"]["glucose_mg_dl"] == configuration["conditions"]["arrival_glucose"]


def test_twelve_combinations_three_of_them_the_bank():
    everything = catalog.configurations()
    keys = {(c["axes"]["mechanism"], c["axes"]["iv_access"], c["axes"]["severity"]) for c in everything}
    assert len(everything) == len(keys) == 12
    assert sum(c["origin"] == "bank" for c in everything) == 3
    assert all(c["origin"] == "composition" for c in catalog.review_candidates())


def test_every_combination_is_compatible_with_concrete_checks():
    for configuration in catalog.configurations():
        result = catalog.compatibility(configuration)
        assert result["compatible"], (configuration["id"], [c for c in result["checks"] if not c["passed"]])
        assert {c["id"] for c in result["checks"]} == {"relations", "case_contract", "declaration_reachable",
                                                        "engine_launch"}


def test_the_severity_bands_are_the_engine_thresholds():
    thresholds = dict((state, value) for value, state in glucose_rescue.CONSCIOUSNESS_BY_GLUCOSE)
    assert catalog.SEVERITY_BANDS["severe"] == (thresholds["Obtunded"], glucose_rescue.SEIZURE_GLUCOSE)
    assert catalog.SEVERITY_BANDS["moderate"] == (thresholds["Drowsy"], thresholds["Alert"])
    lower, upper = catalog.SEVERITY_BANDS["moderate"]
    assert lower <= catalog.MODERATE_ARRIVAL_GLUCOSE < upper
    for configuration in catalog.configurations():
        lower, upper = catalog.SEVERITY_BANDS[configuration["axes"]["severity"]]
        assert lower <= configuration["conditions"]["arrival_glucose"] < upper


def test_relations_are_typed_as_the_faculty_asked():
    kinds = {relation["kind"] for relation in catalog.RELATIONS}
    assert kinds == set(case_catalog.RELATION_KINDS)
    for relation in catalog.RELATIONS:
        assert relation["es"] and relation["why"]
        # An assumption binds only the configuration that declares it.
        assert (relation["check"] is None) is (relation["kind"] == "assumption")


def _broken(configuration_id, **changes):
    configuration = catalog.configuration(configuration_id)
    for path, value in changes.items():
        target = configuration
        *parents, leaf = path.split("__")
        for key in parents:
            target = target[key]
        target[leaf] = value
    return {finding["relation"] for finding in catalog.check(configuration)}


@pytest.mark.parametrize("configuration_id, changes, relation", [
    ("hypoglycemia_76f", {"conditions__sulfonylurea_effect": False}, "N1"),
    ("hypoglycemia_76f", {"conditions__endogenous_insulin": False}, "N2"),
    ("hypoglycemia_54m_thiamine", {"conditions__glycogen_depleted": False}, "N3"),
    ("hypoglycemia_28m", {"conditions__iv_access_failed": True}, "N4"),
    ("hypoglycemia_28m", {"conditions__arrival_glucose": 52}, "N5"),
    ("hypoglycemia_76f", {"narrative__history__medications": "Her medication list includes metformin."}, "N6"),
    ("hypoglycemia_28m", {"conditions__thiamine_deficient": True}, "N7"),
    ("hypoglycemia_28m", {"conditions__glycogen_depleted": True}, "N8"),
    ("hypoglycemia_28m", {"narrative__history_source": "Patient"}, "N9"),
    ("hypoglycemia_28m", {"conditions__endogenous_insulin": True}, "S1"),
])
def test_each_relation_refuses_what_it_forbids(configuration_id, changes, relation):
    assert relation in _broken(configuration_id, **changes)


def test_an_assumption_is_declared_not_imposed():
    # Type 1 diabetes does not fix the glycogen: a patient who has not eaten for
    # days can have spent it, and says so (A2).
    configuration = catalog.configuration("hypoglycemia_28m")
    configuration["conditions"]["glycogen_depleted"] = True
    configuration["narrative"]["history"]["focused"]["oral_intake"] = "He has eaten almost nothing for three days."
    assert catalog.check(configuration) == []
    # Alcohol does not impose a thiamine deficiency (A3).
    configuration = catalog.configuration("hypoglycemia_cfg_alcohol_fasting_working_severe")
    configuration["conditions"]["thiamine_deficient"] = False
    assert catalog.check(configuration) == []
    assert {a["condition"] for a in catalog.configuration("hypoglycemia_28m")["assumptions"]} >= {
        "diabetes", "glycogen_depleted"}


def test_an_ai_proposal_is_refused_in_this_stage():
    configuration = catalog.configuration("hypoglycemia_28m")
    configuration["origin"] = "ai_proposal"
    assert [f["code"] for f in catalog.check(configuration)] == ["origin"]
    # The data model leaves room for a proposal to bring new combinations of
    # executable conditions, not only a name or a story.
    assert set(case_catalog.ORIGINS) == {"bank", "composition", "ai_proposal"}
    assert {name for name, spec in catalog.CONDITIONS.items() if spec["decision_relevant"]} >= {
        "sulfonylurea_effect", "endogenous_insulin", "glycogen_depleted", "thiamine_deficient", "iv_access_failed"}


def test_a_capability_the_engine_lacks_is_refused():
    configuration = catalog.configuration("hypoglycemia_28m")
    configuration["conditions"]["prehospital_dextrose"] = True
    assert "condition" in {f["code"] for f in catalog.check(configuration)}


def test_candidates_are_never_offered_to_residents(monkeypatch):
    from clinical_cases import FAMILIES, review_candidates, variant_by_id
    import encounter_directives
    import offline_cases
    import catalog_trajectories
    candidates = {case["id"] for case in review_candidates()}
    assert len(candidates) == 9
    assert not candidates & {v["id"] for f in FAMILIES.values() for v in f["variants"]}
    for challenge in ("R1-06", "R1-07"):
        assert not candidates & {option[0] for option in encounter_directives.case_options(challenge)}
    monkeypatch.setenv(offline_cases.DEFAULT_VARIANT, "hypoglycemia_cfg_insulin_failed_severe")
    assert offline_cases.pinned_variant() is None
    with pytest.raises(ValueError, match="not available"):
        catalog_trajectories.launch("hypoglycemia_cfg_insulin_failed_severe", "hypoglycemia")
    state = catalog_trajectories.launch("hypoglycemia_cfg_insulin_failed_severe", "hypoglycemia",
                                        allow_review_candidates=True)
    assert state["encounter_spec"]["catalog"]["origin"] == "composition"
    # A candidate can still be read back, for the encounter a faculty member opened on it.
    assert variant_by_id("hypoglycemia_cfg_insulin_failed_severe")["id"] == "hypoglycemia_cfg_insulin_failed_severe"


def test_the_signature_ignores_the_surface_and_not_the_situation():
    configuration = catalog.configuration("hypoglycemia_76f")
    first = catalog.signature(configuration)["id"]
    surface = deepcopy(configuration)
    surface["narrative"]["patient"]["age"] = 81
    surface["narrative"]["presentation"] = "A different wording of the same arrival."
    assert catalog.signature(surface)["id"] == first
    situation = deepcopy(configuration)
    situation["conditions"]["iv_access_failed"] = True
    situation["axes"]["iv_access"] = "failed"
    assert catalog.signature(situation)["id"] != first


def test_the_fingerprint_names_the_component_that_changed():
    configuration = catalog.configuration("hypoglycemia_28m")
    before = catalog.fingerprint(configuration)["components"]
    changed = deepcopy(configuration)
    changed["narrative"]["examination"]["Abdomen"] = "Soft, non-tender, no organomegaly."
    after = catalog.fingerprint(changed)["components"]
    assert [name for name in case_catalog.FINGERPRINT_COMPONENTS if before[name] != after[name]] == ["narrative"]


def test_a_review_is_an_identified_action_at_a_version_and_goes_stale():
    configuration = catalog.configuration("hypoglycemia_76f")
    current = catalog.fingerprint(configuration)
    assert case_catalog.review_status(configuration["id"], current, [])["state"] == "not_reviewed"
    review = {"configuration_id": configuration["id"], "decision": "approved", "fingerprint": current,
              "reviewer": {"username": "docente", "role": "faculty"}}
    assert case_catalog.review_status(configuration["id"], current, [review])["state"] == "reviewed"
    changed = deepcopy(current)
    changed["components"]["parameters"] = "0" * 16
    status = case_catalog.review_status(configuration["id"], changed, [review])
    assert status["state"] == "review_outdated" and status["changed"] == ["parameters"]
    waiver = {"configuration_id": configuration["id"], "component": "parameters",
              "from": current["components"]["parameters"], "to": "0" * 16}
    assert case_catalog.review_status(configuration["id"], changed, [review], [waiver])["state"] == "reviewed"


def test_the_generated_gate_and_the_catalogue_read_the_same_cues():
    import case_cues
    import generated_metabolic_consistency as gate
    assert gate.SULFONYLUREAS is glucose_rescue.SULFONYLUREA_NAMES
    assert gate.ALCOHOL_OR_STARVATION is glucose_rescue.ALCOHOL_OR_STARVATION
    assert gate.HYPOGLYCAEMIA_MG_DL == glucose_rescue.HYPOGLYCAEMIA_MG_DL
    assert gate._affirmed is case_cues.affirmed


# --- faculty priorities of 2026-09-25 -----------------------------------------------
def _family_text():
    from case_assessment_bank import CANDIDATES, CASES
    from clinical_cases import review_candidates, variant_by_id
    cases = [variant_by_id(c["id"]) for c in catalog.bank_configurations()] + review_candidates()
    declarations = [CASES[c["id"]] for c in catalog.bank_configurations()] + list(CANDIDATES.values())
    return json.dumps(cases).lower() + json.dumps(declarations).lower()


def test_no_text_of_the_family_says_glucose_precipitates_an_encephalopathy():
    text = _family_text()
    assert "without precipitating an encephalopathy" not in text
    assert "did the glucose itself make urgent" not in text
    assert "creates a second" not in text
    assert "the order in which they are given is the point" not in text


def test_thiamine_is_a_second_objective_and_not_a_critical_event():
    from case_assessment_bank import CANDIDATES, CASES
    for configuration in catalog.configurations():
        declaration = CASES.get(configuration["id"]) or CANDIDATES[configuration["id"]]
        assert "hypo_no_thiamine" not in {e["event_id"] for e in declaration["critical_events"]}
        d3 = declaration["domains"]["D3"]
        if configuration["conditions"]["thiamine_deficient"]:
            assert "second objective" in d3["opportunity"]
            assert "never a reason to delay" in d3["opportunity"]
            assert d3["expected"][0] == "Gives dextrose"
            assert "thiamine" in d3["requires"]["actions"]
        # The glucose always comes first.
        assert "treats it first" in declaration["domains"]["D1"]["expected"]


def test_a_failed_line_is_an_opportunity_and_not_a_new_event():
    from case_assessment_bank import CANDIDATES, CASES
    for configuration in catalog.configurations():
        declaration = CASES.get(configuration["id"]) or CANDIDATES[configuration["id"]]
        events = {e["event_id"] for e in declaration["critical_events"]}
        assert events <= {"hypo_no_glucose", "hypo_unsafe_discharge"}
        d4 = declaration["domains"]["D4"]["opportunity"]
        if configuration["conditions"]["iv_access_failed"]:
            assert "check the delivery" in d4
            assert "vascular_access" in declaration["domains"]["D4"]["requires"]["actions"]
        else:
            assert "delivery" not in d4


def test_a_failed_line_is_named_in_the_faculty_text():
    from clinical_cases import variant_by_id
    for configuration in catalog.configurations():
        faculty = variant_by_id(configuration["id"])["faculty"]
        named = any("line" in finding for finding in faculty["discriminating_findings"])
        assert named is configuration["conditions"]["iv_access_failed"], configuration["id"]


def test_every_parameter_says_what_review_it_has_had():
    """Reviewed or not, a parameter is a reference, never a criterion; the ones with no review are named."""
    for item in catalog.SIMPLIFICATIONS:
        assert item["review"] in catalog.REVIEW_STATES and item["review_es"].strip(), item["id"]
    pending = {item["id"] for item in catalog.SIMPLIFICATIONS if item["review"] == "pending"}
    # The magnitudes implemented after the review of 2026-09-20 and never reviewed themselves.
    assert pending == {"P5", "P10", "P11"}
    # The line's scope is decision 8's: only a dextrose bolus is held back (DC4).
    assert "DC4" in {item["id"]: item for item in catalog.SIMPLIFICATIONS}["P10"]["review_es"]
