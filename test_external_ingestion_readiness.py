"""The returned documents, before anyone reads them: checksum, properties, completeness, readiness (cycle 9).

Faculty instruction of 2026-09-29 (§26-§29, §51-§60, §92-§97). With the pilots' blank
templates and sentences these tests already use elsewhere -- nothing here stands for a
physician's answer, and no real document is opened:

- the raw file's SHA-256 is recorded and the raw file never changes;
- the document's properties are reported by name, never by value, and a working copy
  clears them while the text stays byte for byte the raw file's own;
- duplicates count once, two versions of one document wait for a person, and wrong,
  empty, partial or unexpected documents are flagged, never interpreted;
- each language is inventoried and made ready on its own;
- from the raw folder to the entries, the physician's response is all that is read, as written.
"""
import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

import tools_validation_corpus as tool
import validation_corpus as vc

ROOT = Path(__file__).resolve().parent
PILOT_ES = json.loads((ROOT / "validation" / "pilot_v1" / "manifests" / "pilot_manifest.json").read_text(encoding="utf-8"))
PILOT_EN = json.loads((ROOT / "validation" / "pilot_v1_en" / "manifests" / "pilot_manifest.json").read_text(encoding="utf-8"))
# Sentences the validation tests already use (test_validation_readiness, test_validation_corpus).
WRITTEN = {"EM01_C01_es.docx": ["Oxígeno por mascarilla", "Hidrocortisona 200 mg ev"],
           "EM02_C01_es.docx": ["Oxígeno por naricera a 2 L/min", "Nebulizar salbutamol 5 mg"]}
FICTITIOUS = "Persona Ficticia"


def document(name, entries, pilot=PILOT_ES, **extra):
    participant, case, language = name[:-5].split("_")[:3]
    data, _ = vc.template(language, case, participant=participant, cases=pilot["cases"], prefill=[entries], **extra)
    return data


def with_properties(data):
    """The same document as a word processor may save it: author, company, title, a custom
    property, a comment and a tracked change, all fictitious."""
    source = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        for info in source.infolist():
            body = source.read(info.filename)
            if info.filename == "word/document.xml":
                body = body.replace(b"<w:body>", b'<w:body><w:p><w:ins w:author="' + FICTITIOUS.encode()
                                    + b'"><w:r><w:t>x</w:t></w:r></w:ins></w:p>', 1)
            archive.writestr(info, body)
        archive.writestr("docProps/core.xml", (
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/">'
            f"<dc:creator>{FICTITIOUS}</dc:creator><cp:lastModifiedBy>{FICTITIOUS}</cp:lastModifiedBy>"
            f"<dc:title>Caso de {FICTITIOUS}</dc:title><cp:revision>3</cp:revision>"
            '<dcterms:created>2026-09-01T10:00:00Z</dcterms:created></cp:coreProperties>'))
        archive.writestr("docProps/app.xml", (
            '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
            "<Company>Clínica Ficticia</Company><Template>Normal.dotm</Template></Properties>"))
        archive.writestr("docProps/custom.xml", (
            '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties" '
            'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
            f'<property fmtid="{{D5CDD505-2E9C-101B-9397-08002B2CF9AE}}" pid="2" name="Owner">'
            f"<vt:lpwstr>{FICTITIOUS}</vt:lpwstr></property></Properties>"))
        archive.writestr("word/comments.xml", (
            f'<w:comments xmlns:w="{vc._W}"><w:comment w:id="0" w:author="{FICTITIOUS}">'
            "<w:p><w:r><w:t>comentario</w:t></w:r></w:p></w:comment></w:comments>"))
    return out.getvalue()


def raw_folder(tmp_path, files):
    folder = tmp_path / "RAW_ES"
    folder.mkdir()
    for name, data in files.items():
        (folder / name).write_bytes(data)
    return folder


# --- the raw file and its checksum ------------------------------------------------------------

def test_the_raw_checksum_is_recorded_and_the_raw_file_never_changes(tmp_path):
    raw = raw_folder(tmp_path, {name: with_properties(document(name, entries)) for name, entries in WRITTEN.items()})
    before = {path.name: path.read_bytes() for path in raw.iterdir()}
    taken = vc.raw_inventory(raw, PILOT_ES, received_on="2026-10-01")
    for record in taken["records"]:
        assert record["sha256"] == hashlib.sha256(before[record["original_filename"]]).hexdigest()
        assert (record["corpus_version"], record["language"], record["raw_status"], record["ingestion_date"]) == (
            "VALIDATION_CORPUS_V1", "es", "RAW", "2026-10-01")
        assert record["participant"] in ("EM01", "EM02") and record["case"] == "C01"
    vc.deidentified_copy(raw / "EM01_C01_es.docx", tmp_path / "EM01_C01_es.docx")
    assert {path.name: path.read_bytes() for path in raw.iterdir()} == before
    # The same files give the same inventory.
    assert vc.raw_inventory(raw, PILOT_ES, received_on="2026-10-01") == taken


def test_the_raw_folder_stays_outside_the_repository():
    with pytest.raises(vc.CorpusError, match="outside the repository"):
        vc.raw_inventory(ROOT / "validation", PILOT_ES, received_on="2026-10-01")


# --- the document's properties -----------------------------------------------------------------

def test_the_properties_are_reported_by_name_never_by_value():
    report = vc.inspect_metadata(with_properties(document("EM01_C01_es.docx", WRITTEN["EM01_C01_es.docx"])))
    assert report["personal_properties"] == ["Company", "creator", "lastModifiedBy"]
    assert report["descriptive_properties"] == ["title"]
    assert (report["custom_properties"], report["comments"], report["comments_with_author"]) == (1, 1, 1)
    assert (report["tracked_changes"], report["tracked_changes_with_author"]) == (1, 1)
    assert report["status"] == "WORKING_COPY_NEEDED" and len(report["human_review"]) == 2
    dumped = json.dumps(report, ensure_ascii=False)
    assert FICTITIOUS not in dumped and "Clínica Ficticia" not in dumped and "comentario" not in dumped
    clean = vc.inspect_metadata(document("EM01_C01_es.docx", WRITTEN["EM01_C01_es.docx"]))
    assert (clean["status"], clean["human_review"]) == ("NO_PERSONAL_PROPERTIES", [])


def test_the_working_copy_clears_the_properties_and_keeps_the_text_byte_for_byte(tmp_path):
    raw = tmp_path / "EM01_C01_es.docx"
    raw.write_bytes(with_properties(document("EM01_C01_es.docx", WRITTEN["EM01_C01_es.docx"])))
    working = tmp_path / "working" / "EM01_C01_es.docx"
    working.parent.mkdir()
    done = vc.deidentified_copy(raw, working)
    assert done["cleared"] == ["Company", "creator", "custom properties", "lastModifiedBy", "title"]
    assert done["raw_sha256"] != done["working_sha256"] and done["text_parts_unchanged"]
    with zipfile.ZipFile(raw) as a, zipfile.ZipFile(working) as b:
        assert a.read("word/document.xml") == b.read("word/document.xml")
        assert a.read("word/comments.xml") == b.read("word/comments.xml")
        assert FICTITIOUS.encode() not in b.read("docProps/core.xml") + b.read("docProps/custom.xml")
        assert b"Normal.dotm" in b.read("docProps/app.xml") and b"2026-09-01" in b.read("docProps/core.xml")
    assert vc.read_document(working)["boxes"] == vc.read_document(raw)["boxes"]
    after = vc.inspect_metadata(working)
    # The properties are gone; the comment and the tracked change are content, left for a person.
    assert (after["personal_properties"], after["descriptive_properties"], after["custom_properties"]) == ([], [], 0)
    assert len(after["human_review"]) == 2
    with pytest.raises(vc.CorpusError, match="written once"):
        vc.deidentified_copy(raw, working)
    with pytest.raises(vc.CorpusError, match="never written"):
        vc.deidentified_copy(raw, raw)


# --- duplicates, versions, wrong and incomplete documents -----------------------------------------

def test_duplicates_count_once_and_two_versions_wait_for_a_person(tmp_path):
    first = document("EM01_C01_es.docx", WRITTEN["EM01_C01_es.docx"])
    raw = raw_folder(tmp_path, {
        "EM01_C01_es.docx": first, "EM01_C01_es (1).docx": first,
        "EM02_C01_es.docx": document("EM02_C01_es.docx", WRITTEN["EM02_C01_es.docx"]),
        "EM02_C01_es_v2.docx": document("EM02_C01_es.docx", WRITTEN["EM01_C01_es.docx"])})
    records = {r["original_filename"]: r for r in vc.raw_inventory(raw, PILOT_ES, received_on="2026-10-01")["records"]}
    assert "DUPLICATE" in records["EM01_C01_es (1).docx"]["problems"]
    assert records["EM01_C01_es (1).docx"]["duplicate_of"] == "EM01_C01_es.docx"
    assert "VERSION_CONFLICT" in records["EM02_C01_es.docx"]["problems"]
    assert records["EM02_C01_es_v2.docx"]["conflicts_with"] == ["EM02_C01_es.docx"]
    ready = vc.readiness(vc.raw_inventory(raw, PILOT_ES, received_on="2026-10-01"), PILOT_ES)
    assert ready["duplicates"] == ["EM01_C01_es (1).docx"] and ready["received"] == 2
    assert not ready["ready_for_split"]
    # Nothing is chosen for the person: the newer file is not kept by itself. A decision with its
    # reason settles it, and the other version is recorded as excluded.
    decisions = {"EM02_C01_es.docx": {"decision": "KEEP", "reason": "the physician confirmed this version", "by": "EM-admin",
                                      "on": "2026-10-02"},
                 "EM02_C01_es_v2.docx": {"decision": "EXCLUDED", "reason": "earlier draft sent by mistake"}}
    settled = vc.readiness(vc.raw_inventory(raw, PILOT_ES, received_on="2026-10-01", decisions=decisions), PILOT_ES)
    assert settled["ready_for_split"] and settled["decisions"] == {"EM02_C01_es.docx": "KEEP",
                                                                  "EM02_C01_es_v2.docx": "EXCLUDED"}
    with pytest.raises(vc.CorpusError, match="with its reason"):
        vc.raw_inventory(raw, PILOT_ES, received_on="2026-10-01", decisions={"EM02_C01_es.docx": {"decision": "KEEP"}})


def test_wrong_language_participant_case_and_codes_are_flagged(tmp_path):
    raw = raw_folder(tmp_path, {
        "EM01_C01_en.docx": document("EM01_C01_en.docx", ["Oxygen by mask"], pilot=PILOT_ES),
        "EM07_C01_es.docx": document("EM07_C01_es.docx", WRITTEN["EM01_C01_es.docx"]),
        "EM01_C02_es.docx": document("EM01_C02_es.docx", WRITTEN["EM01_C01_es.docx"]),
        # Written by EM02, returned under EM01's name.
        "EM01_C04_es.docx": document("EM02_C04_es.docx", WRITTEN["EM02_C01_es.docx"])})
    records = {r["original_filename"]: r["problems"] for r in vc.raw_inventory(raw, PILOT_ES, received_on="2026-10-01")["records"]}
    assert "WRONG_LANGUAGE" in records["EM01_C01_en.docx"]
    assert "WRONG_PARTICIPANT" in records["EM07_C01_es.docx"]
    assert "WRONG_CASE" in records["EM01_C02_es.docx"]
    assert "DOCUMENT_SAYS_OTHER" in records["EM01_C04_es.docx"]


def test_empty_partial_and_unexpected_documents_are_flagged_never_interpreted(tmp_path):
    blank, _ = vc.template("es", "C06", participant="EM01", cases=PILOT_ES["cases"])
    with_evolution, _ = vc.template("es", "C04", participant="EM01", cases=PILOT_ES["cases"],
                                    evolutions=["Veinte minutos después la paciente sigue igual."],
                                    prefill=[["Hidrocortisona 200 mg ev"], []])
    no_boxes = io.BytesIO()
    with zipfile.ZipFile(no_boxes, "w") as archive:
        archive.writestr("word/document.xml", f'<w:document xmlns:w="{vc._W}"><w:body><w:p/></w:body></w:document>')
    raw = raw_folder(tmp_path, {"EM01_C06_es.docx": blank, "EM01_C04_es.docx": with_evolution,
                                "EM02_C06_es.docx": no_boxes.getvalue(), "EM02_C02_es.pdf": b"%PDF-1.4",
                                "notes.docx": b"not a zip"})
    records = {r["original_filename"]: r for r in vc.raw_inventory(raw, PILOT_ES, received_on="2026-10-01")["records"]}
    assert "EMPTY" in records["EM01_C06_es.docx"]["problems"]
    assert "PARTIAL" in records["EM01_C04_es.docx"]["problems"]
    assert records["EM01_C04_es.docx"]["structure"]["boxes"] == 2
    assert "UNEXPECTED_STRUCTURE" in records["EM02_C06_es.docx"]["problems"]
    assert "UNEXPECTED_FILE" in records["EM02_C02_es.pdf"]["problems"]
    assert {"UNEXPECTED_NAME", "UNREADABLE"} <= set(records["notes.docx"]["problems"])
    # Counts, never what a box says.
    assert "Hidrocortisona" not in json.dumps(records, ensure_ascii=False)
    ready = vc.readiness(vc.raw_inventory(raw, PILOT_ES, received_on="2026-10-01"), PILOT_ES)
    assert not ready["ready_for_split"] and ready["empty"] == ["EM01_C06_es.docx"]
    assert ready["partial"] == ["EM01_C04_es.docx"]


def test_the_readiness_report_says_what_is_expected_received_and_missing(tmp_path):
    raw = raw_folder(tmp_path, {name: document(name, entries) for name, entries in WRITTEN.items()})
    ready = vc.readiness(vc.raw_inventory(raw, PILOT_ES, received_on="2026-10-01"), PILOT_ES)
    assert (ready["expected"], ready["received"], len(ready["missing"])) == (18, 2, 16)
    # A missing document is listed and does not block: splitting now freezes V1 without it.
    assert ready["ready_for_split"] and ready["open_problems"] == []
    text = vc.readiness_markdown(ready)
    assert "Ready for the split: **YES**" in text and "EM03_C02_es.docx" in text


# --- Spanish and English apart -------------------------------------------------------------------

def test_spanish_and_english_are_inventoried_and_made_ready_apart(tmp_path):
    spanish = {row["participant"] for row in PILOT_ES["assignment"]}
    english = {row["participant"] for row in PILOT_EN["assignment"]}
    assert spanish == {f"EM0{n}" for n in range(1, 7)} and english == {f"EM{n:02d}" for n in range(7, 13)}
    assert not spanish & english
    # The same case in both corpora is right; the codes and the language tell them apart.
    assert set(PILOT_ES["cases"]) & set(PILOT_EN["cases"])
    folder = tmp_path / "RAW_EN"
    folder.mkdir()
    (folder / "EM07_C01_en.docx").write_bytes(document("EM07_C01_en.docx", ["Oxygen by mask"], pilot=PILOT_EN))
    (folder / "EM01_C01_es.docx").write_bytes(document("EM01_C01_es.docx", WRITTEN["EM01_C01_es.docx"]))
    taken = vc.raw_inventory(folder, PILOT_EN, received_on="2026-10-01")
    assert (taken["language"], taken["corpus_version"]) == ("en", "VALIDATION_CORPUS_V1_EN")
    records = {r["original_filename"]: r["problems"] for r in taken["records"]}
    assert "WRONG_LANGUAGE" in records["EM01_C01_es.docx"] and "WRONG_LANGUAGE" not in records["EM07_C01_en.docx"]
    with pytest.raises(vc.CorpusError, match="different languages"):
        vc.readiness(taken, PILOT_ES)


# --- the dry run, from the raw folder to the entries ---------------------------------------------

def test_the_dry_run_reads_only_the_physician_s_response_as_written(tmp_path):
    """RAW -> checksum -> properties -> working copy -> split -> ingest, with the pilot's template."""
    raw = raw_folder(tmp_path, {name: with_properties(document(name, entries)) for name, entries in WRITTEN.items()})
    ready = tool.inventory(PILOT_ES_PATH, raw, "2026-10-01", tmp_path / "admin")
    assert ready["working_copy_needed"] == sorted(WRITTEN) and ready["human_review"] == sorted(WRITTEN)
    manifest = json.loads((tmp_path / "admin" / "raw_manifest.json").read_text(encoding="utf-8"))
    assert {r["original_filename"]: r["sha256"] for r in manifest["records"]} == {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in raw.iterdir()}
    # A raw manifest is never rewritten over other files.
    (raw / "EM03_C02_es.docx").write_bytes(document("EM03_C02_es.docx", WRITTEN["EM01_C01_es.docx"]))
    with pytest.raises(SystemExit, match="never rewritten"):
        tool.inventory(PILOT_ES_PATH, raw, "2026-10-02", tmp_path / "admin")
    (raw / "EM03_C02_es.docx").unlink()
    working = tmp_path / "WORKING_ES"
    working.mkdir()
    for path in sorted(raw.iterdir()):
        vc.deidentified_copy(path, working / path.name)
    drawn = tool.split(PILOT_ES_PATH, working, SPANISH, tmp_path / "CORPUS", "2026-10-01")
    assert {item["file"] for item in drawn["documents"]} == set(WRITTEN)
    entries = {}
    for subset in vc.SUBSETS:
        for document_read in vc.ingest(tmp_path / "CORPUS", subset)["documents"]:
            entries[document_read["file"]] = [entry["text"] for entry in document_read["entries"]]
    assert entries == WRITTEN
    # A rerun can be matched: the corpus, its draw and the lists of known defects are recorded (§132).
    development = vc.ingest(tmp_path / "CORPUS", "development")
    assert (development["pilot_id"], development["split_seed"], development["baseline_commit"]) == (
        PILOT_ES["pilot_id"], drawn["seed"], SPANISH)
    engine = {"engine": {"commit": SPANISH, "uncommitted_changes": False, "simulator_version": "x"},
              "configuration": tool.engine_configuration(), "seed": 3000, "run_on": "2026-10-02"}
    provenance = tool._provenance(development, engine, [])
    assert provenance["corpus_id"] == PILOT_ES["pilot_id"] and provenance["split"]["seed"] == drawn["seed"]
    assert provenance["engine_configuration"]["provider_key_present"] is False
    assert provenance["known_defect_lists"] == {"pilot_list_version": 2, "v3_state_version": 3}
    # The vignette, the instructions, the monitor and the chart are the template's, never entries.
    sheet = vc.case_sheet(PILOT_ES["cases"]["C01"], "es")
    template_lines = set(vc.TEXT["es"]["instructions"]) | set(sheet["opening"]) | {vc.TEXT["es"]["reminder"]}
    assert not template_lines & {text for texts in entries.values() for text in texts}


PILOT_ES_PATH = ROOT / "validation" / "pilot_v1" / "manifests" / "pilot_manifest.json"
SPANISH = "939978a5147ab859a6dc3566ef4e1a98611a5093"


@pytest.mark.parametrize("box", [
    # One short entry; several paragraphs with blank ones between them; a line break and a tab
    # inside a paragraph; a decimal comma, abbreviations, capitals and accents; a long entry.
    ["Hidrocortisona 200 mg ev"],
    ["Oxígeno por mascarilla", "", "", "Nebulizar salbutamol 5 mg", "Oxígeno por naricera a 2 L/min"],
    ["Salbutamol 5 mg nbz\ny repetir en 20 min", "Suero fisiológico\t500 ml\nen 30 min"],
    ["Adrenalina 0,5 mg IM", "SF 1000 ml administrado por SAMU", "Alta si sigue asintomática"],
    ["Oxígeno por naricera a 2 L/min, nebulizar salbutamol 5 mg, hidrocortisona 200 mg ev, reevaluar en 1 h, "
     "alta si sigue asintomática y control en APS en 48 h"],
])
def test_the_response_is_read_exactly_as_written(box):
    read = vc.read_document(document("EM01_C01_es.docx", box))
    assert read["boxes"][0]["entries"] == [text for text in box if text]


# --- the future report's separate counts ----------------------------------------------------------

def test_silent_loss_false_execution_trace_distortion_and_clarification_are_counted_apart():
    clear = {"items": [("MED", "a"), ("O2", "b")], "clinically_sufficient": True, "ambiguous": False}
    silent = vc.error_flags(clear, {"asked": False}, {"n_recognized": 1, "extra_or_wrong": False}, [])
    assert silent == ["SILENT_LOSS"]
    asked = vc.error_flags(clear, {"asked": True}, {"n_recognized": 1, "extra_or_wrong": False}, [])
    assert asked == []
    false = vc.error_flags(clear, {"asked": False}, {"n_recognized": 2, "extra_or_wrong": True}, ["trace"])
    assert false == ["FALSE_EXECUTION", "TRACE_DISTORTION"]
    ambiguous = {**clear, "ambiguous": True}
    assert vc.error_flags(ambiguous, {"asked": True}, {"n_recognized": 0, "extra_or_wrong": False}, []) == [
        "APPROPRIATE_CLARIFICATION"]
    assert vc.error_flags(clear, {"asked": False}, {"n_recognized": 2, "extra_or_wrong": False}, [], "trace") == [
        "TRACE_DISTORTION"]


def test_who_annotated_when_and_whether_blind_is_recorded_beside_the_sheets(tmp_path):
    template = vc.annotation_provenance_template()
    assert template["sheets"]["annotation_second.csv"]["second_annotation"] is True
    assert template["sheets"]["annotation.csv"]["blinded_to_engine_output"] is None
    path = tmp_path / "annotation_provenance.json"
    template["sheets"]["annotation.csv"].update(annotator="AN01", annotated_on="2026-10-05", blinded_to_engine_output=True)
    template["adjudication"].update(reviewer="RV01", adjudicated_on="2026-10-09")
    path.write_text(json.dumps(template), encoding="utf-8")
    record = vc.annotation_provenance(path, [{"n_recognized": "2"}, {"n_recognized": ""}])
    assert record["sheets"]["annotation.csv"] == {"annotator": "AN01", "annotated_on": "2026-10-05",
                                                  "blinded_to_engine_output": True, "second_annotation": False}
    assert record["adjudication"] == {"reviewer": "RV01", "adjudicated_on": "2026-10-09", "adjudicated_entries": 1}
    # Nothing recorded yet reads as nothing, never as blind.
    assert vc.annotation_provenance(tmp_path / "absent.json")["sheets"]["annotation.csv"]["blinded_to_engine_output"] is None
