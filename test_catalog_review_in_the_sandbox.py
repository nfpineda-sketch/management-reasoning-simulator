"""The catalogue in the application: frozen at launch, reviewable by faculty, invisible to residents."""
import pytest

import evaluation_basis
from case_assessment_bank import CASES
from catalog_reviews import CatalogReviewStore
from account_store import AccountError
from test_curriculum_app import click, cohort, open_app  # noqa: F401  (fixture)


def test_a_resident_launch_freezes_what_the_encounter_is_judged_against(cohort):
    store, _, token = cohort
    at = open_app(token)
    assert [w.key for w in at.selectbox] == ["presentation_language"]
    assert not any("catalogue" in exp.label for exp in at.expander)
    click(at, "Begin Encounter")
    attempt = store.list_attempts(token)[0]
    basis = attempt["encounter"]["evaluation_basis"]
    case_id = attempt["payload"]["session"]["state"]["encounter_spec"]["clinical_case"]["id"] if \
        attempt["payload"] else basis["case_id"]
    assert basis["schema"] == evaluation_basis.SCHEMA and basis["source"] == "bank"
    assert basis["case_id"] == case_id and basis["declaration"] == evaluation_basis._plain(CASES[case_id])
    assert basis["versions"]["coverage"] == "1.1" and basis["code_version"]
    assert evaluation_basis.resolve(attempt)["status"] == "frozen"
    assert not attempt["encounter"]["assignment"].get("review_case")


def test_an_administrator_opens_a_configuration_under_review_in_the_sandbox(cohort):
    store, admin, _ = cohort
    at = open_app(admin)
    next(w for w in at.selectbox if w.label == "Management challenge").set_value("R1-06").run()
    review = next(w for w in at.selectbox if w.label == "Case to open (faculty review)")
    assert "hypoglycemia_cfg_sulfonylurea_failed_moderate" in review.options or any(
        "Sulfonilurea · Vía fallida · Moderada" in str(option) for option in review.options)
    review.set_value("hypoglycemia_cfg_sulfonylurea_failed_moderate").run()
    click(at, "Begin Encounter")
    attempt = store.list_attempts(admin)[0]
    assert attempt["is_sandbox"] is True
    assert attempt["encounter"]["assignment"]["review_case"] == "hypoglycemia_cfg_sulfonylurea_failed_moderate"
    state = at.session_state.state
    assert state["encounter_spec"]["variant_id"] == "hypoglycemia_cfg_sulfonylurea_failed_moderate"
    assert state["encounter_spec"]["catalog"]["origin"] == "composition"
    basis = attempt["encounter"]["evaluation_basis"]
    assert basis["source"] == "catalog_candidate"
    assert basis["versions"]["catalog"]["configuration_id"] == "hypoglycemia_cfg_sulfonylurea_failed_moderate"


def test_a_challenge_outside_the_catalogue_offers_no_review_case(cohort):
    _, admin, _ = cohort
    at = open_app(admin)
    next(w for w in at.selectbox if w.label == "Management challenge").set_value("R1-05").run()
    assert not any(w.label == "Case to open (faculty review)" for w in at.selectbox)


def test_a_clinical_review_is_an_identified_action_bound_to_a_version(cohort):
    store, admin, token = cohort
    reviews = CatalogReviewStore(store)
    with pytest.raises(AccountError):
        reviews.record(token, "hypoglycemia_76f", "approved", "A resident cannot review.")
    with pytest.raises(AccountError, match="written note"):
        reviews.record(admin, "hypoglycemia_76f", "approved", "")
    before = {row["configuration_id"]: row["state"] for row in reviews.statuses(admin)}
    assert set(before.values()) == {"not_reviewed"}
    saved = reviews.record(admin, "hypoglycemia_76f", "approved", "Reviewed the recurrence and the discharge.")
    assert saved["reviewer"]["username"] == "teacher" and saved["fingerprint"]["whole"]
    after = {row["configuration_id"]: row for row in reviews.statuses(admin)}
    assert after["hypoglycemia_76f"]["state"] == "reviewed"
    assert after["hypoglycemia_28m"]["state"] == "not_reviewed"
    # Nothing but that action produced it, and it is kept as history.
    assert [r["decision"] for r in reviews.reviews(admin, "hypoglycemia_76f")] == ["approved"]


def test_the_review_panel_is_on_the_faculty_sandbox(cohort):
    _, admin, _ = cohort
    at = open_app(admin)
    next(w for w in at.selectbox if w.label == "Management challenge").set_value("R1-06").run()
    assert any(exp.label == "Clinical review of the hypoglycemia catalogue (faculty)" for exp in at.expander)
    assert any("Configuration" in item.value.columns for item in at.dataframe)


def test_the_launch_records_purpose_and_prior_exposure_for_the_later_stages(cohort):
    """Prepared, not used: nothing is chosen from it yet (faculty instruction, point 10)."""
    from curriculum_runtime import prior_exposure
    earlier = [{"id": "a1", "status": "completed", "is_sandbox": False,
                "encounter": {"evaluation_basis": evaluation_basis.freeze("hypoglycemia_76f")}},
               {"id": "a2", "status": "completed", "is_sandbox": True,
                "encounter": {"evaluation_basis": evaluation_basis.freeze("hypoglycemia_28m")}},
               {"id": "a3", "status": "active", "is_sandbox": False,
                "encounter": {"evaluation_basis": evaluation_basis.freeze("hypoglycemia_76f")}},
               {"id": "old", "status": "completed", "is_sandbox": False,
                "encounter": {"state": {"encounter_spec": {"clinical_case": {"id": "hypoglycemia_76f"}}}}}]
    exposure = prior_exposure(earlier, evaluation_basis.freeze("hypoglycemia_76f"))
    assert [row["attempt_id"] for row in exposure["same_case"]] == ["a1", "old"]
    assert [row["attempt_id"] for row in exposure["same_signature"]] == ["a1"]
    store, _, token = cohort
    at = open_app(token)
    click(at, "Begin Encounter")
    assignment = store.list_attempts(token)[0]["encounter"]["assignment"]
    assert assignment["purpose"] == "practice"
    assert assignment["exposure"] == {"same_case": [], "same_signature": [],
                                      "signature": assignment["exposure"]["signature"]}
