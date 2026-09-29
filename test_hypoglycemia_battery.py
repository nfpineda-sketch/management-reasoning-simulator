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


def test_the_failed_line_holds_back_everything_that_runs_through_it(report):
    """DC4, decided 2026-09-29: the failure belongs to the line, not to the bolus."""
    for entry in _failed_line_configurations(report):
        results = {r["id"]: r for r in entry["checks"]}
        for check in ("T5", "T14", "T15"):
            assert results[check]["status"] == "passed", (entry["configuration_id"], results[check])
        assert entry["summary"]["pending_decisions"] == []
    assert battery.PENDING == {}
    # Through the failed arrival cannula, a 10% infusion reaches the circulation in part...
    running = {"iv_access_failed": True, "dextrose_infusion_ml_h": 100.0, "elapsed": 0,
               "arrival_line": {"in_vein": False}, "dextrose_infusion_access": "arrival_line"}
    full = 100 / 60 * glucose_rescue.INFUSION_G_PER_ML * 4
    assert glucose_rescue.treatment_gain(running) == pytest.approx(full * glucose_rescue.FAILED_ACCESS_SHARE)
    # ...and whole once it runs through a line that works.
    assert glucose_rescue.treatment_gain({**running, "dextrose_infusion_access": "new_line"}) == pytest.approx(full)
    # An encounter begun under 1.0 keeps 1.0's rule: the infusion arrived whole.
    legacy = {"iv_access_failed": True, "dextrose_infusion_ml_h": 100.0, "elapsed": 0}
    assert glucose_rescue.treatment_gain(legacy) == pytest.approx(full)


def test_the_arrival_consciousness_is_what_the_engine_shows_at_minute_one(report):
    """DC1, decided 2026-09-29: the consciousness written at arrival is the reference."""
    for entry in report["configurations"]:
        result = {r["id"]: r for r in entry["checks"]}["T12"]
        assert result["status"] == "passed", (entry["configuration_id"], result)
        assert "DC1" not in entry["summary"]["pending_decisions"]
    assert "DC1" not in battery.PENDING
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
            # The intraosseous dose is played now (T14); the examination and the
            # pharmacology of a partial glucagon or octreotide dose are not.
            assert not any("intraósea" in line for line in entry["unobserved"])
            assert any("Vascular access" in line for line in entry["unobserved"])
            assert any("DC4-F" in line for line in entry["unobserved"])
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
