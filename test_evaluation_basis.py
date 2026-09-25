"""What an encounter is judged against is frozen with it (faculty instruction of 2026-09-25)."""
import json

import pytest

import evaluation_basis
import glucose_rescue
from case_assessment_bank import CASES


def _record(case_id, basis=None):
    record = {"id": "attempt-x", "payload": {"session": {"state": {
        "encounter_spec": {"clinical_case": {"id": case_id, "history": {"chief_complaint": ["x"]}}}}}}}
    if basis is not None:
        record["encounter"] = {"evaluation_basis": basis}
    return record


def test_a_new_encounter_carries_its_own_frozen_declarations():
    basis = evaluation_basis.freeze("hypoglycemia_54m_thiamine", code_version="abc123")
    assert basis["schema"] == evaluation_basis.SCHEMA and basis["source"] == "bank"
    assert basis["declaration"] == json.loads(json.dumps(CASES["hypoglycemia_54m_thiamine"]))
    assert basis["versions"]["coverage"] == "1.1" and basis["versions"]["rubric"]
    assert basis["versions"]["catalog"]["configuration_id"] == "hypoglycemia_54m_thiamine"
    assert basis["versions"]["engine"]["glucose_rescue"] == glucose_rescue.VERSION == "1.0"
    resolved = evaluation_basis.resolve(_record("hypoglycemia_54m_thiamine", basis))
    assert resolved["status"] == "frozen" and resolved["limitation"] is None
    assert resolved["declaration"] == CASES["hypoglycemia_54m_thiamine"]  # tuples restored
    assert [e["event_id"] for e in resolved["events"]] == ["hypo_no_glucose"]


def test_a_later_change_does_not_change_how_a_frozen_encounter_is_judged(monkeypatch):
    basis = evaluation_basis.freeze("hypoglycemia_76f")
    record = _record("hypoglycemia_76f", basis)
    changed = json.loads(json.dumps(CASES["hypoglycemia_76f"]))
    changed["critical_events"] = []
    monkeypatch.setitem(CASES, "hypoglycemia_76f", changed)
    resolved = evaluation_basis.resolve(record)
    assert [e["event_id"] for e in resolved["events"]] == ["hypo_no_glucose", "hypo_unsafe_discharge"]


def test_an_encounter_judged_under_1_0_keeps_hypo_no_thiamine():
    """Saved before copies existed: the declarations of 2026-09-25, said to be unverifiable."""
    resolved = evaluation_basis.resolve(_record("hypoglycemia_54m_thiamine"))
    assert resolved["status"] == "legacy"
    assert [e["event_id"] for e in resolved["events"]] == ["hypo_no_glucose", "hypo_no_thiamine"]
    assert resolved["versions"]["coverage"] == "1.0"
    assert "cannot be verified" in resolved["limitation"]["en"]
    assert "no se puede verificar" in resolved["limitation"]["es"]
    # Nothing attributes a verified version to it.
    assert "catalog" not in resolved["versions"] and "code_version" not in resolved


def test_the_legacy_snapshot_is_the_code_before_the_change_for_every_other_case():
    legacy = evaluation_basis.legacy()["declarations"]
    assert set(legacy) == set(CASES)
    changed = [case_id for case_id in CASES if json.loads(json.dumps(CASES[case_id])) != legacy[case_id]]
    assert changed == ["hypoglycemia_54m_thiamine"]


def test_a_generated_case_is_read_without_declarations_and_without_error():
    for record in (_record("AI-0123456789abcdef"),
                   _record("AI-0123456789abcdef", evaluation_basis.freeze("AI-0123456789abcdef"))):
        resolved = evaluation_basis.resolve(record)
        assert resolved["status"] == "generated"
        assert resolved["declaration"] is None and resolved["events"] == ()
        assert "generated case" in resolved["limitation"]["en"]
        assert "no complete or comparable total" in resolved["limitation"]["en"]


def test_an_invalid_identifier_and_a_corrupt_record_are_told_apart():
    unknown = evaluation_basis.resolve(_record("hypoglycemia_99x"))
    assert unknown["status"] == "unknown_case" and "invalid identifier" in unknown["limitation"]["en"]
    assert evaluation_basis.resolve("not a record")["status"] == "corrupt"
    assert evaluation_basis.resolve({"payload": "garbage"})["status"] == "corrupt"
    tampered = evaluation_basis.freeze("hypoglycemia_28m")
    tampered["declaration"]["critical_events"] = []
    broken = evaluation_basis.resolve(_record("hypoglycemia_28m", tampered))
    assert broken["status"] == "corrupt" and "fingerprint" in broken["error"]
    mismatch = evaluation_basis.resolve(_record("hypoglycemia_28m", evaluation_basis.freeze("hypoglycemia_76f")),
                                        "hypoglycemia_28m")
    assert mismatch["status"] == "corrupt"
    assert evaluation_basis.resolve(_record(""))["status"] == "no_authored_case"
    with pytest.raises(evaluation_basis.EvaluationBasisError):
        evaluation_basis.freeze("hypoglycemia_99x")


def test_a_reevaluation_is_explicit_and_keeps_the_original():
    record = _record("hypoglycemia_54m_thiamine")
    with pytest.raises(evaluation_basis.EvaluationBasisError):
        evaluation_basis.reevaluation(record, reason="", requested_by="docente")
    with pytest.raises(evaluation_basis.EvaluationBasisError):
        evaluation_basis.reevaluation(record, reason="nuevos criterios", requested_by="")
    again = evaluation_basis.reevaluation(record, reason="Decisión docente del 2026-09-25",
                                          requested_by="docente")
    assert again["status"] == "reevaluation"
    assert [e["event_id"] for e in again["events"]] == ["hypo_no_glucose"]
    assert again["previous"]["status"] == "legacy"
    assert again["previous"]["fingerprint"] != again["fingerprint"]
    assert "Decisión docente del 2026-09-25" in again["limitation"]["es"]
    # The record itself is untouched: resolving it again still gives the original.
    assert evaluation_basis.resolve(record)["status"] == "legacy"
    with pytest.raises(evaluation_basis.EvaluationBasisError):
        evaluation_basis.reevaluation(_record("AI-0123456789abcdef"), reason="r", requested_by="d")


def test_the_analyses_read_the_basis_not_todays_declarations():
    import rubric_screening
    import history_review
    from rubric_store import build_review
    record = _record("hypoglycemia_54m_thiamine")
    events = [row["event_id"] for row in rubric_screening.screen_events(record, "hypoglycemia_54m_thiamine")]
    assert events == ["hypo_no_glucose", "hypo_no_thiamine"]
    frozen = _record("hypoglycemia_54m_thiamine", evaluation_basis.freeze("hypoglycemia_54m_thiamine"))
    events = [row["event_id"] for row in rubric_screening.screen_events(frozen, "hypoglycemia_54m_thiamine")]
    assert events == ["hypo_no_glucose"]
    assert history_review.unasked_for_events(frozen, "hypoglycemia_54m_thiamine") == []
    # A faculty decision on an event the encounter's basis does not define is refused.
    from account_store import AccountError
    with pytest.raises(AccountError, match="not one defined"):
        build_review(case_id="hypoglycemia_54m_thiamine", scores={"D1": 2}, reasons={},
                     events=[{"event_id": "hypo_no_thiamine", "status": "confirmed", "justification": "x"}],
                     justifications={}, status="draft", basis=evaluation_basis.resolve(frozen))
