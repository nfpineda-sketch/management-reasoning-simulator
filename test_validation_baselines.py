"""The engine baselines a validation result is measured against (faculty, 2026-09-28, §13, §44, §51).

A baseline is never replaced retroactively, only added. Every run records its
corpus version, languages and engine commit; the report names the baseline that
commit is and the version of the known-defects list its errors are tagged against.
"""
import json
import re

import validation_corpus as vc

SPANISH = "939978a5147ab859a6dc3566ef4e1a98611a5093"


def registry():
    return json.loads(vc.BASELINES.read_text(encoding="utf-8"))["baselines"]


def test_the_spanish_pilot_baseline_stays_the_commit_it_was():
    [spanish] = [item for item in registry() if item["name"] == "SPANISH PILOT BASELINE"]
    assert (spanish["commit"], spanish["language"], spanish["known_defects_version"]) == (SPANISH, "es", 1)


def test_every_baseline_is_a_full_commit_with_its_language_and_defects_list():
    names = [item["name"] for item in registry()]
    assert len(names) == len(set(names))
    known = json.loads(vc.KNOWN_DEFECTS.read_text(encoding="utf-8"))
    for item in registry():
        assert re.fullmatch(r"[0-9a-f]{40}", item["commit"]), item["name"]
        assert item["language"] in vc.LANGUAGES
        # The pilot's list (version 2) or the state of V3 (version 3), once a baseline takes it.
        assert 1 <= item["known_defects_version"] <= max(known["version"], vc.known_defects_state_version())
        assert item["record"] and item["registered_on"] and item["simulator_version"]


def test_a_run_is_named_by_the_baseline_its_commit_is():
    assert vc.baseline_of({"commit": SPANISH, "uncommitted_changes": False}) == {
        "engine_baseline": "SPANISH PILOT BASELINE", "known_defects_version": 1}
    # Local changes make it no baseline, and so does any other commit.
    assert vc.baseline_of({"commit": SPANISH, "uncommitted_changes": True})["engine_baseline"] is None
    assert vc.baseline_of({"commit": "0" * 40, "uncommitted_changes": False}) == {
        "engine_baseline": None, "known_defects_version": None}
    assert vc.baseline_of(None)["engine_baseline"] is None


def test_the_report_records_corpus_language_engine_baseline_and_defects_list():
    import tools_validation_corpus as tools
    corpus = {"corpus_version": vc.CORPUS_VERSION, "subset": "development",
              "subset_version": vc.SUBSETS["development"], "source_type": vc.SOURCE_TYPE,
              "documents": [{"language": "es", "case": "C01", "collected_on": "2026-10-01",
                             "template_version": "VC2-ES"}]}
    engine = {"engine": {"commit": SPANISH, "uncommitted_changes": False, "simulator_version": "x"},
              "seed": 3000, "run_on": "2026-10-02"}
    provenance = tools._provenance(corpus, engine, [])
    assert (provenance["corpus_version"], provenance["languages"]) == (vc.CORPUS_VERSION, ["es"])
    assert provenance["engine"]["commit"] == SPANISH
    assert (provenance["engine_baseline"], provenance["known_defects_version"]) == ("SPANISH PILOT BASELINE", 1)


def test_the_known_defects_say_which_baselines_they_are_present_in():
    known = json.loads(vc.KNOWN_DEFECTS.read_text(encoding="utf-8"))
    assert known["version"] == vc.known_defects_version() == max(item["version"] for item in known["versions"])
    names = {"SPANISH PILOT BASELINE", "ENGLISH VALIDATION BASELINE"}
    for defect in known["defects"]:
        assert defect["present_in"] and set(defect["present_in"]) <= names, defect["id"]
    kd01 = next(defect for defect in known["defects"] if defect["id"] == "KD-01")
    assert kd01["present_in"] == ["SPANISH PILOT BASELINE"] and kd01["fixed_in"] == "ENGLISH VALIDATION BASELINE"


def test_the_state_of_v3_is_its_own_file_and_leaves_the_pilot_list_as_it_was():
    known = json.loads(vc.KNOWN_DEFECTS.read_text(encoding="utf-8"))
    assert known["version"] == 2 and len(known["defects"]) == 15
    state = json.loads(vc.KNOWN_DEFECTS_V3.read_text(encoding="utf-8"))
    assert (state["version"], state["baseline"]) == (3, "DEVELOPMENT PRE-VALIDATION BASELINE V3")
    assert state["unresolved_critical"] == []
    # TD-14 stays HIGH as it was registered (friction, a question); it is named, never dropped.
    assert [item.split()[0] for item in state["unresolved_high"]] == ["KD-28"]
    # Every defect of the pilot's list says what it is in V3; none is dropped.
    assert [item["id"] for item in state["from_the_pilot_list"]] == [item["id"] for item in known["defects"]]
    assert {item["in_v3"] for item in state["from_the_pilot_list"]} <= {"present", "fixed"}
    ids = [item["id"] for item in [*state["defects"], *state["fixed_before_v3"], *state["known_behaviour_by_design"]]]
    assert len(ids) == len(set(ids)) and not set(ids) & {item["id"] for item in known["defects"]}
    for defect in state["defects"]:
        assert defect["present_in"] == [state["baseline"]], defect["id"]
        assert defect["severity"] in ({"HIGH"} if defect["id"] == "KD-28" else {"MEDIUM", "LOW"}), defect["id"]
    # What V3 fixed is still in the frozen baselines: a run of one of them can tag it (§67).
    fixed = {item["id"]: item for item in state["fixed_before_v3"]}
    assert set(fixed) == {"TD-39", "TD-34", "TD-36", "TD-33"}
    for name in ("TD-39", "TD-34", "TD-36"):
        assert "SPANISH PILOT BASELINE" in fixed[name]["present_in"] and fixed[name]["fixed_in"] == state["baseline"]


def test_an_error_of_a_frozen_baseline_can_be_tagged_with_what_v3_fixed_and_a_typo_cannot():
    assert {"TD-39", "TD-34", "TD-36", "KD-16", "KB-04", "KD-02", "KB-01"} <= vc.known_defect_ids()
    assert "KD-99" not in vc.known_defect_ids() and "TD-99" not in vc.known_defect_ids()
