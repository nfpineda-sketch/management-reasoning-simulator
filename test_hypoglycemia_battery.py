"""The trajectory battery: technical checks pass; references are references; nothing is 'validated'."""
import json

import pytest

import glucose_rescue
import hypoglycemia_battery as battery
import hypoglycemia_catalog as catalog


@pytest.fixture(scope="module")
def report():
    return battery.run()


def test_every_compatible_configuration_is_played_on_all_four_kinds(report):
    assert len(report["configurations"]) == 12
    for entry in report["configurations"]:
        assert entry["compatibility"]["compatible"], entry["configuration_id"]
        assert {s["kind"] for s in entry["scripts"]} == set(battery.TRAJECTORY_KINDS), entry["configuration_id"]
        # Defensible alternatives are played, not only one right answer.
        assert sum(s["kind"] == "adequate" for s in entry["scripts"]) >= 2, entry["configuration_id"]


def test_no_configuration_has_a_technical_defect(report):
    for entry in report["configurations"]:
        assert entry["summary"]["technical_defects"] == [], (entry["configuration_id"], entry["checks"])
        assert entry["tested"] is True


def _failed_line_configurations(report):
    return [e for e in report["configurations"]
            if catalog.configuration(e["configuration_id"])["conditions"]["iv_access_failed"]]


def test_the_ampoule_through_a_failed_line_does_not_arrive(report):
    failed = _failed_line_configurations(report)
    assert len(failed) == 6
    for entry in failed:
        results = {r["id"]: r for r in entry["checks"]}
        for check in ("T3", "T4", "T6"):
            assert results[check]["status"] == "passed", (entry["configuration_id"], results[check])


def test_the_scope_of_the_failed_line_is_a_pending_decision_and_the_engine_keeps_it(report):
    """Faculty decision 8 held back only the dextrose bolus; widening it is the faculty's call (DC4)."""
    for entry in _failed_line_configurations(report):
        result = {r["id"]: r for r in entry["checks"]}["T5"]
        assert result["status"] == "failed", entry["configuration_id"]
        assert result["classification"] == "pending_clinical_decision" and result["decision"] == "DC4"
        assert "DC4" in entry["summary"]["pending_decisions"]
    # Nothing was changed to make it pass: through the failed line, the 10% infusion still arrives whole.
    running = {"iv_access_failed": True, "dextrose_infusion_ml_h": 100.0, "elapsed": 0}
    assert glucose_rescue.treatment_gain(running) == pytest.approx(100 / 60 * glucose_rescue.INFUSION_G_PER_ML * 4)


def test_a_pending_clinical_decision_is_reported_and_nothing_is_changed_to_pass_it(report):
    """The arrival state against the engine's threshold (DC1): named, classified, left as it is."""
    flagged = {e["configuration_id"] for e in report["configurations"] if "DC1" in e["summary"]["pending_decisions"]}
    assert flagged == {"hypoglycemia_28m", "hypoglycemia_54m_thiamine", "hypoglycemia_cfg_insulin_failed_severe",
                       "hypoglycemia_cfg_alcohol_fasting_working_severe"}
    for entry in report["configurations"]:
        for result in entry["checks"]:
            if result["id"] == "T12" and result["status"] == "failed":
                assert result["classification"] == "pending_clinical_decision"
                assert result["decision"] == "DC1"
    # The bank cases still arrive as they were authored.
    from clinical_cases import variant_by_id
    assert variant_by_id("hypoglycemia_28m")["observable"]["mental_status"] == "Drowsy"


def test_references_name_their_parameters_and_are_never_criteria(report):
    known = {item["id"] for item in catalog.SIMPLIFICATIONS}
    for check in battery.CHECKS:
        if check["kind"] == "reference":
            assert check.get("parameters") and set(check["parameters"]) <= known, check["id"]
        else:
            assert "parameters" not in check, check["id"]
    text = json.dumps(report, ensure_ascii=False).lower()
    for word in ("validado", "validated", "aprobado", "approved"):
        assert word not in text


def test_every_configuration_says_what_was_not_observed(report):
    for entry in report["configurations"]:
        assert any("Lenguaje libre" in line for line in entry["unobserved"])
        configuration = catalog.configuration(entry["configuration_id"])
        if configuration["conditions"]["iv_access_failed"]:
            assert any("intraósea" in line for line in entry["unobserved"])
        if configuration["origin"] != "bank":
            assert any("superficie" in line for line in entry["unobserved"])


def test_thiamine_neither_wakes_nor_harms_in_every_configuration_that_needs_it(report):
    for entry in report["configurations"]:
        if catalog.configuration(entry["configuration_id"])["conditions"]["thiamine_deficient"]:
            assert {r["id"]: r["status"] for r in entry["checks"]}["T11"] == "passed"


def test_the_battery_calls_no_provider(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def refuse(name, *args, **kwargs):
        if name == "openai" or name.startswith("openai."):
            raise AssertionError("the battery must not reach a provider")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", refuse)
    entry = battery.run_configuration(catalog.configuration("hypoglycemia_cfg_sulfonylurea_failed_moderate"))
    assert entry["tested"]


def test_the_seizure_reference_follows_the_parameter_it_names(report):
    for entry in report["configurations"]:
        result = {r["id"]: r for r in entry["checks"]}["R3"]
        assert result["parameters"] == ["P1", "P2"]
        if entry["axes"]["severity"] == "severe":
            minute = int(result["observed"].rsplit(" ", 1)[1])
            assert glucose_rescue.SEIZURE_AFTER_MIN - 1 <= minute <= glucose_rescue.SEIZURE_AFTER_MIN + 2


def test_the_published_catalogue_is_the_one_the_code_produces():
    """Generated, like the coverage matrix: an edit made by hand would drift."""
    import tools_hypoglycemia_catalog
    assert tools_hypoglycemia_catalog.TARGET.read_text(encoding="utf-8") == tools_hypoglycemia_catalog.build(), (
        "docs/CATALOGO_HIPOGLICEMIA.md is out of date; run tools_hypoglycemia_catalog.py")
