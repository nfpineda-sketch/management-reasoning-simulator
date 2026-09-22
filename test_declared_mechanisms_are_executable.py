"""A mechanism the case declares makes its own therapy executable.

Found by the paid generation of 2026-09-22. The model authored a high-risk
pulmonary embolism, declared engine.pulmonary_obstruction — the mechanism whose
physiology the engine runs end to end, and which authorises thrombolysis — and
the validator rejected it for resting on "a therapy the engine cannot execute".
The automatic correction it bought was rejected for the same reason, so the run
produced nothing. What the engine can do had moved; the two checks had not.
"""
import generated_case_coverage as coverage
import generated_pe
from acs_reperfusion import MECHANISM_ACTIONS as CORONARY_ACTIONS


def case(diagnosis, engine=None, paths=None):
    return {"faculty": {"diagnosis": diagnosis,
                        "anticipated_management_paths": list(paths or []),
                        "management_dilemma": "", "management_focus": ""},
            "engine": dict(engine or {})}


def test_the_engine_really_does_thrombolyse_a_declared_obstruction():
    # The claim the checks now rest on, read from the mechanism itself.
    assert "thrombolysis" in generated_pe.MECHANISM_ACTIONS
    assert "thrombolysis" in CORONARY_ACTIONS


def test_a_declared_obstruction_makes_high_risk_pe_manageable():
    declared = case("Acute high-risk pulmonary embolism with RV strain and obstructive shock",
                    {"pulmonary_obstruction": {"bleeding_risk": None}})
    assert coverage.unmanageable_diagnosis_issues(declared) == []


def test_without_the_mechanism_it_is_still_refused():
    # Nothing is declared, so nothing authorises the therapy and the syndrome
    # has no practisable dilemma: the original check is intact.
    bare = case("Acute high-risk pulmonary embolism with obstructive shock")
    assert [i["code"] for i in coverage.unmanageable_diagnosis_issues(bare)] == ["UNMANAGEABLE_DIAGNOSIS"]


def test_a_declared_coronary_makes_a_stemi_manageable():
    declared = case("ST-elevation myocardial infarction of the inferior wall",
                    {"coronary": {"territory": "inferior", "omi": True}})
    assert coverage.unmanageable_diagnosis_issues(declared) == []


def test_the_management_path_may_name_the_therapy_the_mechanism_delivers():
    declared = case("Acute high-risk pulmonary embolism",
                    {"pulmonary_obstruction": {"bleeding_risk": None}},
                    ["Give systemic thrombolysis once the hypotension is sustained."])
    assert coverage.unexecutable_path_issues(declared) == []


def test_a_therapy_no_mechanism_delivers_is_still_refused():
    declared = case("Cardiac tamponade", {"pulmonary_obstruction": {"bleeding_risk": None}},
                    ["Perform pericardiocentesis at the bedside."])
    issues = coverage.unexecutable_path_issues(declared)
    assert [i["details"]["therapy"] for i in issues] == ["chest drainage or pericardial drainage"]
    assert [i["code"] for i in coverage.unmanageable_diagnosis_issues(declared)] == ["UNMANAGEABLE_DIAGNOSIS"]


def test_the_syndromes_that_stay_unmanageable_are_the_ones_with_no_mechanism():
    for syndrome in coverage.REPERFUSION_DEPENDENT_SYNDROMES:
        therapy = coverage.SYNDROME_THERAPY.get(syndrome)
        if therapy is None:
            continue
        assert any(therapy in therapies for therapies in coverage.MECHANISM_THERAPIES.values()), syndrome
