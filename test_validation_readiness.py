"""The pilot tooling from returned documents to a report, end to end (cycle 5, §26, §47).

The readiness check the faculty asked for, with synthetic documents only: the two
documents here are the pilot's blank templates filled with sentences these tests
already use elsewhere, and the annotation is a test fixture. Nothing stands for a
physician's answer, nothing is sealed data, and no result is claimed from it.

The ten criteria of §47, in order: the split is reproducible; the sealed subset stays
outside the repository; ingest keeps the text and its order; the annotation sheets are
written; the second annotator's sample is reproducible; the run uses the real page;
adjudication keeps a disagreement; the report tells the five classes apart; a known
defect can be tagged; and the baseline is recorded.
"""
import json
from pathlib import Path

import pytest

import tools_validation_corpus as tool
import validation_corpus as vc

ROOT = Path(__file__).resolve().parent
PILOT = ROOT / "validation" / "pilot_v1" / "manifests" / "pilot_manifest.json"
SPANISH = "939978a5147ab859a6dc3566ef4e1a98611a5093"
# One pair of the pilot (P1) and the case both of them write; sentences from test_validation_corpus.
WRITTEN = {"EM01_C01_es.docx": ["Oxígeno por mascarilla", "Hidrocortisona 200 mg ev"],
           "EM02_C01_es.docx": ["Oxígeno por naricera a 2 L/min", "Nebulizar salbutamol 5 mg"]}
FIXTURE_ITEMS = {"Oxígeno por mascarilla": "O2: oxígeno por mascarilla",
                 "Hidrocortisona 200 mg ev": "MED: hidrocortisona 200 mg ev",
                 "Oxígeno por naricera a 2 L/min": "O2: oxígeno por naricera 2 L/min",
                 "Nebulizar salbutamol 5 mg": "MED: salbutamol 5 mg nbz"}


def returned(folder):
    pilot = json.loads(PILOT.read_text(encoding="utf-8"))
    folder.mkdir(parents=True)
    for name, entries in WRITTEN.items():
        participant, case, language = name[:-5].split("_")
        data, _ = vc.template(language, case, participant=participant, cases=pilot["cases"], prefill=[entries])
        (folder / name).write_bytes(data)
    return folder


def test_from_the_returned_documents_to_the_report(tmp_path, monkeypatch):
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    # play() sets the offline mode for its process; monkeypatch takes it back (C-2026-09-26-20).
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    back = returned(tmp_path / "returned")

    # 1 · the split, drawn from the files' bytes, is the same every time.
    corpus = tmp_path / "corpus"
    drawn = tool.split(PILOT, back, SPANISH, corpus, "2026-10-15")
    assert tool.split(PILOT, back, SPANISH, corpus, "2026-10-15")["seed"] == drawn["seed"]
    subsets = {item["file"]: item["subset"] for item in drawn["documents"]}
    assert sorted(subsets.values()) == ["development", "sealed"]
    development = next(name for name, subset in subsets.items() if subset == "development")

    # 2 · the sealed subset and its output never live in the repository.
    with pytest.raises(vc.CorpusError, match="outside the repository"):
        vc.check_outside(ROOT / "local-data" / "sealed-run", "sealed")

    # 3, 4 and 5 · ingest keeps each paragraph and its order, and writes the blind sheets.
    out = tmp_path / "development-run"
    assert tool.main(["ingest", "--corpus", str(corpus), "--subset", "development", "--out", str(out)]) == 0
    entries = json.loads((out / "entries.json").read_text(encoding="utf-8"))
    [document] = entries["documents"]
    assert document["file"] == development
    assert [entry["text"] for entry in document["entries"]] == WRITTEN[development]
    sheet = vc.read_csv(out / "annotation.csv")
    assert [row["text"] for row in sheet] == WRITTEN[development]
    assert not set(sheet[0]) & set(vc.ENGINE_COLUMNS)
    second = vc.read_csv(out / "annotation_second.csv")
    assert [row["entry_id"] for row in second] == vc.double_annotation_sample(entries)
    assert vc.double_annotation_sample(entries) == vc.double_annotation_sample(json.loads(
        (out / "entries.json").read_text(encoding="utf-8")))

    # 6 · the run reads every entry through the real page, with no model.
    assert tool.main(["run", "--out", str(out)]) == 0
    engine = json.loads((out / "engine_output.json").read_text(encoding="utf-8"))
    [played] = engine["documents"]
    assert played["stopped"] is None and played["ai_calls_spent"] == 0 and played["unmatched_trace_entries"] == 0
    assert all(engine["entries"][entry["entry_id"]]["played"] for entry in document["entries"])

    # The annotation, as a test fixture: every entry annotated, and the second
    # annotator disagreeing on one field of the entry in the sample.
    annotated = [{**row, "intended_items": FIXTURE_ITEMS[row["text"]], "clinically_sufficient": "Y",
                  "annotator": "fixture"} for row in sheet]
    vc.write_csv(out / "annotation.csv", vc.ANNOTATION_COLUMNS, annotated)
    doubled = [{**row, "intended_items": FIXTURE_ITEMS[row["text"]], "clinically_sufficient": "N",
                "annotator": "fixture-2"} for row in second]
    vc.write_csv(out / "annotation_B.csv", vc.ANNOTATION_COLUMNS, doubled)

    # 7 · adjudication keeps the disagreement and a reviewer's own entries.
    second_sheet = str(out / "annotation_B.csv")
    tool.main(["adjudicate", "--out", str(out), "--second", second_sheet])
    rows = vc.read_csv(out / "adjudication.csv")
    disputed = set(vc.double_annotation_sample(entries))
    tagged_entry = sorted(disputed)[0]
    for row in rows:
        row.update({"n_recognized": "1", "n_complete": "1", "n_partial": "0", "reviewer": "fixture"})
        if row["entry_id"] == tagged_entry:
            row.update({"impact": "LOW", "known_defect": "KB-01", "review_note": "a fixture note"})
    vc.write_csv(out / "adjudication.csv", vc.ANNOTATION_COLUMNS + vc.ENGINE_COLUMNS + vc.REVIEW_COLUMNS, rows)
    tool.main(["adjudicate", "--out", str(out), "--second", second_sheet])
    rows = {row["entry_id"]: row for row in vc.read_csv(out / "adjudication.csv")}
    assert rows[tagged_entry]["review_note"] == "a fixture note"
    for entry_id, row in rows.items():
        assert (row["proposed_classification"] == "ANNOTATION_DISAGREEMENT") is (entry_id in disputed)
        row["classification"] = row["proposed_classification"]
    vc.write_csv(out / "adjudication.csv", vc.ANNOTATION_COLUMNS + vc.ENGINE_COLUMNS + vc.REVIEW_COLUMNS,
                 list(rows.values()))

    # 8, 9 and 10 · the report tells the five classes apart, carries the tag, and
    # records the corpus, the language, the engine and its baseline.
    assert tool.main(["report", "--out", str(out), "--second", second_sheet]) == 0
    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert set(report["metrics"]["all"]["classes"]) == set(vc.CLASSES)
    assert sum(report["metrics"]["all"]["classes"].values()) == len(rows)
    provenance = report["provenance"]
    assert provenance["corpus_version"] == vc.CORPUS_VERSION and provenance["languages"] == ["es"]
    assert provenance["engine"]["commit"] and "uncommitted_changes" in provenance["engine"]
    assert {"engine_baseline", "known_defects_version"} <= set(provenance)
    expected = vc.baseline_of(provenance["engine"])
    assert (provenance["engine_baseline"], provenance["known_defects_version"]) == (
        expected["engine_baseline"], expected["known_defects_version"])
    # The entries in disagreement are listed for the faculty, the tagged one with its tag.
    traced = {row["classification"]: row for row in report["traceability"]}
    assert set(traced) == {"ANNOTATION_DISAGREEMENT"}
    assert [row["known_defect"] for row in report["traceability"] if row.get("known_defect")] == ["KB-01"]
    assert "Provenance" in (out / "report.md").read_text(encoding="utf-8")
