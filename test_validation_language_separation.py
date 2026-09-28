"""Spanish and English are separate validation corpora, never one run (cycle 7, §33, §37, §87).

A manifest declares its language explicitly, its corpus version is that language's, and every
document or assignment row is in it. A run that tries to mix them fails clearly; the language is
never detected from what the physicians wrote. The English pilot is prepared and not sent: its
documents are held outside the repository, and its baseline is chosen before any response is read.
"""
import json
from pathlib import Path

import pytest

import validation_corpus as vc

ROOT = Path(__file__).resolve().parent
SPANISH = ROOT / "validation" / "pilot_v1" / "manifests" / "pilot_manifest.json"
ENGLISH = ROOT / "validation" / "pilot_v1_en" / "manifests" / "pilot_manifest.json"


def _manifest(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _corpus(tmp_path, manifest):
    for subset in vc.SUBSETS:
        (tmp_path / subset).mkdir(parents=True, exist_ok=True)
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return tmp_path


def _rows(language, participant="EM90"):
    return [{"file": vc.file_name(participant, "C01", language), "participant": participant, "case": "C01",
             "language": language, "collected_on": "2026-10-01", "subset": "development"}]


def test_each_pilot_declares_its_own_language_and_corpus():
    assert vc.corpus_language(_manifest(SPANISH)) == "es"
    assert vc.corpus_language(_manifest(ENGLISH)) == "en"
    assert vc.CORPUS_VERSIONS == {"es": "VALIDATION_CORPUS_V1", "en": "VALIDATION_CORPUS_V1_EN"}


def test_a_manifest_that_mixes_the_languages_fails_clearly(tmp_path):
    manifest = {"corpus_version": vc.CORPUS_VERSIONS["es"], "language": "es", "cases": vc.PILOT_CASES,
                "documents": _rows("es") + _rows("en", "EM91")}
    with pytest.raises(vc.CorpusError, match="separate corpora"):
        vc.load_manifest(_corpus(tmp_path, manifest))


@pytest.mark.parametrize("manifest, reason", [
    ({"corpus_version": "VALIDATION_CORPUS_V1"}, "declare its language explicitly"),
    ({"corpus_version": "VALIDATION_CORPUS_V1", "language": "en"}, "is the 'es' corpus"),
    ({"corpus_version": "VALIDATION_CORPUS_V1_EN", "language": "es"}, "is the 'en' corpus"),
    ({"corpus_version": "VALIDATION_CORPUS_V2", "language": "es"}, "not one of"),
    ({"corpus_version": "VALIDATION_CORPUS_V1", "language": "fr"}, "not es or en"),
])
def test_the_language_is_declared_never_inferred_or_guessed(manifest, reason):
    with pytest.raises(vc.CorpusError, match=reason):
        vc.corpus_language({**manifest, "documents": _rows(manifest.get("language") or "es")})


def test_an_english_corpus_is_read_by_the_same_tools(tmp_path):
    manifest = {"corpus_version": vc.CORPUS_VERSIONS["en"], "language": "en", "cases": vc.PILOT_CASES,
                "documents": _rows("en", "EM07")}
    assert vc.load_manifest(_corpus(tmp_path, manifest))["language"] == "en"


def test_the_english_pilot_mirrors_the_spanish_one_with_its_own_codes():
    spanish, english = _manifest(SPANISH), _manifest(ENGLISH)
    assert english["pilot_id"] != spanish["pilot_id"] and english["corpus_version"] == "VALIDATION_CORPUS_V1_EN"
    codes = english["mirrors"]["participants"]
    assert sorted(codes.values()) == [f"EM{n:02d}" for n in range(7, 13)]
    # The same cases, pairs and assignment logic; only the codes and the language differ.
    assert english["cases"] == spanish["cases"]
    assert [(p["pair"], p["shared_cases"]) for p in english["pairs"]] == [
        (p["pair"], p["shared_cases"]) for p in spanish["pairs"]]
    assert [(codes[r["participant"]], r["case"]) for r in spanish["assignment"]] == [
        (r["participant"], r["case"]) for r in english["assignment"]]
    assert {r["language"] for r in english["assignment"]} == {"en"}
    assert not {r["participant"] for r in english["assignment"]} & {r["participant"] for r in spanish["assignment"]}


def test_the_english_pilot_is_prepared_not_sent_and_names_no_baseline_yet():
    english = _manifest(ENGLISH)
    assert english["status"].startswith("PREPARED, NOT SENT")
    assert english["documents"]["status"] == "ENGLISH DOCX AVAILABLE EXTERNALLY / NOT PRESENT IN REPOSITORY"
    assert not list((ENGLISH.parent.parent).glob("**/*.docx"))
    baseline = english["baseline"]
    assert baseline["status"].startswith("TO BE CHOSEN BY THE FACULTY BEFORE ANY ENGLISH RESPONSE")
    assert "commit" not in baseline
    assert [c["name"] for c in baseline["candidates"]][0] == "ENGLISH VALIDATION BASELINE"


def test_the_split_writes_the_pilot_s_language_into_the_corpus(tmp_path):
    import tools_validation_corpus as tool
    returned = tmp_path / "returned"
    returned.mkdir()
    for row in _manifest(ENGLISH)["assignment"][:3]:
        (returned / row["file"]).write_bytes(row["file"].encode("utf-8"))
    corpus = tmp_path / "corpus"
    tool.split(ENGLISH, returned, "0" * 40, corpus, "2026-11-01")
    written = json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))
    assert (written["language"], written["corpus_version"]) == ("en", "VALIDATION_CORPUS_V1_EN")
    assert vc.load_manifest(corpus)["pilot_id"] == "VALIDATION_PILOT_V1_EN"
