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
        assert 1 <= item["known_defects_version"] <= known["version"]
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
