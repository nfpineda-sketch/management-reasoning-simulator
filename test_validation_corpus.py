"""The validation corpus, phase 1: Word documents in, a reproducible report out (DF-6).

Faculty decisions of 2026-09-27, cycle 3 (§21–§24, §43–§48, §66–§74). Every
sentence below is written for these tests: none is a physician's, and nothing
here stands for the sealed subset (§73).
"""
import io
import json
import zipfile
from pathlib import Path

import pytest

import validation_corpus as vc

ROOT = Path(__file__).resolve().parent
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _document(tmp_path, name, language="es", case="C01", participant="EM90", boxes=(), evolutions=()):
    data, _ = vc.template(language, case, participant=participant, evolutions=evolutions, prefill=list(boxes))
    path = tmp_path / name
    path.write_bytes(data)
    return path


def _xml_text(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        return archive.read("word/document.xml").decode("utf-8")


# --- the template ---------------------------------------------------------------------------

@pytest.mark.parametrize("language", vc.LANGUAGES)
def test_the_template_asks_for_natural_language_and_teaches_nothing_internal(language):
    data, source = vc.template(language, "C01")
    text = _xml_text(data)
    # The faculty's sentence, word for word (cycle 4, §13).
    reminder = {"es": ("Escriba naturalmente, como lo haría al manejar el paciente. No existe un formato correcto "
                       "y no intente adaptar su lenguaje a un sistema informático."),
                "en": ("Write naturally, as you would when managing the patient. There is no correct format, and "
                       "do not try to adapt your language to a computer system.")}[language]
    assert reminder in text
    for internal in ("working model", "expected effect", "contingency", "modelo de trabajo", "efecto esperado",
                     "contingencia", "parser", "Management Trace", "reassessment target", "prioridad de manejo"):
        assert internal.lower() not in text.lower()
    # The case is a code: the bank's identifier and its diagnosis name the answer.
    assert "asthma_24f" not in text and "Acute severe asthma" not in text
    assert ">C01<" in text
    # Personal details are neither asked for nor wanted.
    for asked in ("correo", "email", "nombre del participante", "your name:"):
        assert asked not in text.lower()


def test_the_case_is_shown_as_the_simulator_opens_it():
    sheet = vc.case_sheet("anaphylaxis_63m_betablocked", "en")
    assert sheet["opening"][0].startswith("A 63-year-old man is brought in after a wasp sting")
    assert sheet["opening"][1].endswith("History from: Wife.")
    assert sheet["monitor"] == "HR 64/min · SpO₂ 89% · BP 76/42 mmHg · RR 26/min"
    assert sheet["chart"] == ["Weight 115 kg (reported by his wife)", "Height 1.72 m (reported by his wife)"]
    spanish = vc.case_sheet("anaphylaxis_63m_betablocked", "es")
    assert spanish["opening"][1].endswith("Fuente de la historia: Esposa.")
    assert spanish["chart"][0] == "Peso 115 kg (referido por su esposa)"
    # The Spanish is the case's own translation, and the sheet says its approval was not checked.
    assert "not checked" in spanish["text_source"]


def test_the_same_template_is_the_same_bytes():
    assert vc.template("es", "C03")[0] == vc.template("es", "C03")[0]


def test_a_participant_is_a_code():
    with pytest.raises(vc.CorpusError, match="code such as EM01"):
        vc.template("es", "C01", participant="Dra. Pérez")
    with pytest.raises(vc.CorpusError, match="Unknown case code"):
        vc.template("es", "asthma_24f")


def test_the_committed_blank_templates_are_what_the_generator_writes():
    folder = ROOT / "validation" / "pilot_v1" / "blank"
    listed = json.loads((folder / "templates.json").read_text(encoding="utf-8"))
    assert len(listed["documents"]) == 2 * len(vc.PILOT_CASES)
    for item in listed["documents"]:
        data = (folder / item["file"]).read_bytes()
        assert vc.hashlib.sha256(data).hexdigest() == item["sha256"]
        assert data == vc.template(item["language"], item["case"])[0]


# --- reading a document ---------------------------------------------------------------------

def test_a_blank_template_reads_back_with_its_fields_and_no_entries(tmp_path):
    read = vc.read_document(_document(tmp_path, "blank.docx"))
    assert read["fields"] == {"participant": "EM90", "language": "Español", "case": "C01", "version": "VC2-ES"}
    assert read["boxes"] == [{"box": 1, "label": "Su manejo", "entries": []}]
    assert read["warnings"] == []


def test_each_paragraph_in_a_box_is_one_entry_in_the_order_written(tmp_path):
    path = _document(tmp_path, "filled.docx", evolutions=["Veinte minutos después la paciente sigue igual."],
                     boxes=[["", "Oxígeno por naricera a 3 L/min", "", "Salbutamol 5 mg nbz\ny repetir en 20 min"],
                            ["Hidrocortisona 200 mg ev"]])
    read = vc.read_document(path)
    assert [box["entries"] for box in read["boxes"]] == [
        ["Oxígeno por naricera a 3 L/min", "Salbutamol 5 mg nbz\ny repetir en 20 min"],
        ["Hidrocortisona 200 mg ev"]]
    # The evolution between the boxes is the faculty's text, not something typed outside.
    assert read["outside"] == []


def _word_like(tmp_path):
    """A document shaped the way a word processor saves one: split runs, revisions, fields, metadata."""
    def cell(*paragraphs):
        return f"<w:tc>{''.join(paragraphs) or '<w:p/>'}</w:tc>"

    def p(inner):
        return f"<w:p>{inner}</w:p>"

    def r(text):
        return f'<w:r><w:t xml:space="preserve">{text}</w:t></w:r>'

    fields = (f"<w:tbl><w:tr>{cell(p(r('Código de participante')))}{cell(p(r('EM9') + r('1')))}</w:tr>"
              f"<w:tr>{cell(p(r('Idioma de la respuesta')))}{cell(p(r('Español')))}</w:tr>"
              f"<w:tr>{cell(p(r('Caso')))}{cell(p(r('C02')))}</w:tr></w:tbl>")
    header = cell(p(r("Su manejo")), p(r(vc.TEXT["es"]["response_hint"])))
    written = cell(
        p(r("Ceftriaxona 2 ") + '<w:ins w:author="Persona Ficticia"><w:r><w:t>g ev</w:t></w:r></w:ins>'
          + '<w:del w:author="Persona Ficticia"><w:r><w:delText>1 g</w:delText></w:r></w:del>'),
        p(r("Suero fisiológico") + "<w:r><w:tab/></w:r>" + r("500 ml") + "<w:r><w:br/></w:r>" + r("en 30 min")),
        p("<w:hyperlink><w:r><w:t>Hemocultivos x2</w:t></w:r></w:hyperlink>"),
        p("<w:sdt><w:sdtContent><w:r><w:t>Lactato</w:t></w:r></w:sdtContent></w:sdt>"),
        p("<w:r><w:drawing><w:txbxContent><w:p><w:r><w:t>Texto en un cuadro</w:t></w:r></w:p>"
          "</w:txbxContent></w:drawing></w:r>"),
        p(""),
    )
    box = f"<w:tbl><w:tr>{header}</w:tr><w:tr>{written}</w:tr></w:tbl>"
    body = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W}"><w:body>'
            f"{p(r('Caso clínico'))}{fields}{box}{p(r('Escrito después del cuadro'))}"
            f"{p(r(vc.TEXT['es']['closing']))}<w:sectPr/></w:body></w:document>")
    path = tmp_path / "EM91_C02_es.docx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", body)
        archive.writestr("docProps/core.xml", "<cp:coreProperties><dc:creator>Persona Ficticia</dc:creator>"
                                              "</cp:coreProperties>")
        archive.writestr("word/comments.xml", '<w:comments><w:comment w:author="Persona Ficticia">'
                                              "<w:p><w:r><w:t>comentario</w:t></w:r></w:p></w:comment></w:comments>")
    return path


def test_revisions_properties_and_comments_are_never_read(tmp_path):
    read = vc.read_document(_word_like(tmp_path))
    assert read["fields"]["participant"] == "EM91"
    assert read["boxes"][0]["entries"] == ["Ceftriaxona 2 g ev", "Suero fisiológico\t500 ml\nen 30 min",
                                           "Hemocultivos x2", "Lactato"]
    dumped = json.dumps(read, ensure_ascii=False)
    assert "Persona Ficticia" not in dumped and "comentario" not in dumped and "1 g" not in dumped
    assert "Texto en un cuadro" not in dumped
    assert any("text box" in warning for warning in read["warnings"])
    # The properties name whoever saved the file: said, so it can be removed, and never repeated.
    assert any("author name" in warning for warning in read["warnings"])
    # Typed after the last box: reported, never read as an entry.
    assert read["outside"] == ["Escrito después del cuadro"]


def test_a_document_that_declares_entities_is_refused(tmp_path):
    path = tmp_path / "bad.docx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", '<!DOCTYPE x [<!ENTITY a "b">]><w:document/>')
    with pytest.raises(vc.CorpusError, match="DOCTYPE"):
        vc.read_document(path)


def test_privacy_is_flagged_and_doses_are_not():
    assert vc.privacy_flags("Aviso a juan.perez@hospital.cl") == ["email address"]
    assert vc.privacy_flags("llamar al +56 9 8765 4321") == ["phone-like number"]
    assert vc.privacy_flags("Noradrenalina 0.1 mcg/kg/min, SF 1000 ml en 30 min, PA 138/84") == []


# --- the corpus --------------------------------------------------------------------------------

def _corpus(tmp_path, documents, retired=()):
    folder = tmp_path / "VALIDATION_CORPUS_V1"
    for subset in vc.SUBSETS:
        (folder / subset).mkdir(parents=True, exist_ok=True)
    rows = []
    for subset, participant, case, language, boxes in documents:
        name = vc.file_name(participant, case, language)
        _document(folder / subset, name, language, case, participant, boxes)
        rows.append({"file": name, "participant": participant, "case": case, "language": language,
                     "collected_on": "2026-10-01", "subset": subset})
    manifest = {"corpus_version": vc.CORPUS_VERSION, "cases": vc.PILOT_CASES, "documents": rows,
                "retired_entries": list(retired)}
    (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return folder


def test_ingest_gives_stable_identifiers_and_provenance(tmp_path):
    folder = _corpus(tmp_path, [("development", "EM90", "C01", "es", [["Oxígeno por naricera a 2 L/min",
                                                                       "Nebulizar salbutamol 5 mg"]]),
                                ("sealed", "EM91", "C02", "es", [["Ceftriaxona 2 g ev"]])])
    corpus = vc.ingest(folder, "development")
    assert corpus["subset_version"] == "DEVELOPMENT_SUBSET_V1" and corpus["source_type"] == vc.SOURCE_TYPE
    [document] = corpus["documents"]
    assert document["bank_case"] == "asthma_24f" and document["collected_on"] == "2026-10-01"
    assert document["template_version"] == "VC2-ES" and len(document["sha256"]) == 64
    assert [entry["entry_id"] for entry in document["entries"]] == ["EM90-C01-es-b1-e01", "EM90-C01-es-b1-e02"]
    # The same documents, the same file: nothing depends on the clock.
    assert vc.ingest(folder, "development") == corpus


def test_a_participant_belongs_to_one_subset_and_the_manifest_must_agree(tmp_path):
    folder = _corpus(tmp_path, [("development", "EM90", "C01", "es", [["Ceftriaxona 2 g ev"]]),
                                ("sealed", "EM90", "C02", "es", [["Ceftriaxona 2 g ev"]])])
    with pytest.raises(vc.CorpusError, match="one subset"):
        vc.ingest(folder, "development")
    folder = _corpus(tmp_path / "b", [("development", "EM90", "C01", "es", [["Ceftriaxona 2 g ev"]])])
    manifest = json.loads((folder / "manifest.json").read_text())
    manifest["documents"][0]["case"] = "C02"
    manifest["documents"][0]["file"] = "EM90_C01_es.docx"
    (folder / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(vc.CorpusError, match="the document says case 'C01', the manifest 'C02'"):
        vc.ingest(folder, "development")


def test_a_retired_entry_leaves_validation_and_says_why(tmp_path):
    retired = [{"entry_id": "EM91-C02-es-b1-e01", "on": "2026-11-02", "reason": "used to correct the reader"}]
    folder = _corpus(tmp_path, [("sealed", "EM91", "C02", "es", [["Ceftriaxona 2 g ev", "Hemocultivos x2"]])],
                     retired)
    corpus = vc.ingest(folder, "sealed")
    statuses = {entry["entry_id"]: entry["status"] for entry in corpus["documents"][0]["entries"]}
    assert statuses == {"EM91-C02-es-b1-e01": vc.RETIRED, "EM91-C02-es-b1-e02": "sealed"}
    assert [entry["entry_id"] for _, entry in vc.entries_of(corpus)] == ["EM91-C02-es-b1-e02"]


def test_the_sealed_subset_stays_outside_the_repository(tmp_path):
    with pytest.raises(vc.CorpusError, match="outside the repository"):
        vc.check_outside(ROOT / "local-data" / "sealed-run", "sealed")
    with pytest.raises(vc.CorpusError, match="local-data/ only"):
        vc.check_outside(ROOT / "docs" / "corpus", "development")
    assert vc.check_outside(ROOT / "local-data" / "development-run", "development")
    assert vc.check_outside(tmp_path / "sealed-run", "sealed") == (tmp_path / "sealed-run").resolve()


# --- sheets -----------------------------------------------------------------------------------

def test_the_annotation_sheet_is_blind(tmp_path):
    folder = _corpus(tmp_path, [("development", "EM90", "C01", "es", [["Ceftriaxona 2 g ev"]])])
    rows = vc.annotation_rows(vc.ingest(folder, "development"))
    assert set(rows[0]) <= set(vc.ANNOTATION_COLUMNS)
    assert not set(vc.ENGINE_COLUMNS) & set(vc.ANNOTATION_COLUMNS)
    path = tmp_path / "annotation.csv"
    vc.write_csv(path, vc.ANNOTATION_COLUMNS, rows)
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")  # a spreadsheet opens the accents as written


def test_a_sheet_saved_back_by_a_spreadsheet_is_read(tmp_path):
    path = tmp_path / "saved.csv"
    path.write_bytes("entry_id;text;intended_items\nEM90-C01-es-b1-e01;Hidrocortisona 200 mg ev;MED: hidrocortisona\n"
                     .encode("cp1252"))
    assert vc.read_csv(path) == [{"entry_id": "EM90-C01-es-b1-e01", "text": "Hidrocortisona 200 mg ev",
                                  "intended_items": "MED: hidrocortisona"}]


def test_annotations_read_kinds_nothing_and_yes_in_either_language():
    assert vc.items("MED: salbutamol 5 mg nbz; HX: alergias\nreevaluar en 20 min") == [
        ("MED", "salbutamol 5 mg nbz"), ("HX", "alergias"), ("OTHER", "reevaluar en 20 min")]
    assert vc.items("—") == [] and vc.items("ninguno") == []
    assert vc.annotation_of({"entry_id": "x", "intended_items": ""}) is None
    row = {"entry_id": "x", "intended_items": "MED: ceftriaxona 2 g ev", "clinically_sufficient": "S",
           "rationale": "sí", "contingency": "Y"}
    annotation = vc.annotation_of(row)
    assert annotation["clinically_sufficient"] and annotation["rationale"] and annotation["contingency"]
    assert not annotation["ambiguous"]
    with pytest.raises(vc.CorpusError, match="clinically_sufficient is required"):
        vc.annotation_of({"entry_id": "x", "intended_items": "MED: ceftriaxona"})
    with pytest.raises(vc.CorpusError, match="neither yes nor no"):
        vc.annotation_of({"entry_id": "x", "intended_items": "MED: a", "clinically_sufficient": "quizás"})


def test_two_blind_annotations_are_compared_field_by_field():
    first = [{"entry_id": "a", "intended_items": "MED: x; MED: y", "clinically_sufficient": "Y"},
             {"entry_id": "b", "intended_items": "MED: z", "clinically_sufficient": "Y", "contingency": "Y"}]
    second = [{"entry_id": "a", "intended_items": "MED: x; MED: y", "clinically_sufficient": "Y"},
              {"entry_id": "b", "intended_items": "MED: z", "clinically_sufficient": "N", "contingency": "Y"}]
    result = vc.agreement(first, second)
    assert result["compared"] == 2
    assert result["agreement"]["n_items"] == {"agree": 2, "of": 2}
    assert result["agreement"]["clinically_sufficient"] == {"agree": 1, "of": 2}
    assert result["disagreements"] == {"b": ["clinically_sufficient"]}


# --- the engine's reading and the measures ------------------------------------------------------

def _trace(text, status="executed", actions=(), slots=None, provenance=None, plans=()):
    return {"input": text, "status": status, "actions": [list(a) for a in actions],
            "slots": slots or {}, "provenance": provenance or {},
            "future": sorted(plan for _, plan in plans), "future_details": sorted(f"{kind}/None" for kind, _ in plans),
            "plans": [list(plan) for plan in plans], "summaries": []}


def test_trace_entries_are_matched_to_what_produced_them_in_order():
    entries = [{"entry_id": "e1", "text": "Ceftriaxona 2 g ev"}, {"entry_id": "e2", "text": "Plan:"},
               {"entry_id": "e3", "text": "Ceftriaxona 2 g ev"}]
    trace = [_trace("Ceftriaxona 2 g ev\n\nGuided reasoning completion: ..."), _trace("Plan:", "clarification_required"),
             _trace("ceftriaxona  2 g EV"), _trace("something the page wrote alone")]
    matched, unmatched = vc.align(entries, trace)
    assert [len(matched[key]) for key in ("e1", "e2", "e3")] == [1, 1, 1]
    assert [item["input"] for item in unmatched] == ["something the page wrote alone"]


def test_what_the_engine_did_is_read_from_the_trace_and_the_harness_is_named():
    record = {"played": True, "held": "pending_reasoning", "trace": [_trace(
        "Hidrocortisona 200 mg ev\n\nGuided reasoning completion: **Working model:** ...",
        actions=[(("agent", "hydrocortisone"), ("type", "steroid")), (("delay_min", 5), ("type", "reassessment"))],
        slots={"problem_representation": "harness words", "expected_effect": "menos broncoespasmo"},
        provenance={"problem_representation": "completed", "expected_effect": "stated"})]}
    view = vc.engine_view(record)
    assert view["reasoning_gate"] and view["harness_completed"] and view["executed"] and not view["asked"]
    # What the harness answered is never counted as the physician's reasoning.
    assert view["stated"] == {"expected_effect": "menos broncoespasmo"}
    assert view["captured"] == {"reassessment": False, "rationale": False, "expectation": True, "contingency": False}
    held = vc.engine_view({"played": True, "held": "pending_action", "trace": [_trace(
        "Oxígeno por mascarilla", "clarification_required",
        actions=[(("message", "Specify one absolute target oxygen flow"), ("type", "clarification"))])]})
    assert held["asked"] and held["read"] == ["ASKED: Specify one absolute target oxygen flow"]
    conditional = vc.engine_view({"played": True, "trace": [_trace(
        "Si no mejora, adrenalina", "clarification_required", plans=[("conditional", "si no mejora, adrenalina")])]})
    assert conditional["captured"]["contingency"]


def test_each_plan_keeps_its_own_kind():
    # The trace keeps the texts and the kinds in two separately sorted lists;
    # paired, a return advice sorted under "conditional" and counted as a
    # contingency (found 2026-09-28).
    view = vc.engine_view({"played": True, "trace": [_trace(
        "Alta, volver si fiebre, y si vomita ondansetrón", plans=[
            ("advice", "volver si fiebre"), ("conditional", "si vomita ondansetron")])]})
    assert view["conditional"] == ["si vomita ondansetron"]
    assert view["read"] == ["PLAN (advice): volver si fiebre", "PLAN (conditional): si vomita ondansetron"]
    advice_only = vc.engine_view({"played": True, "trace": [_trace(
        "Alta, volver si fiebre", plans=[("advice", "volver si fiebre")])]})
    # A return precaution is the discharge's safety plan, not a contingency (VC-3).
    assert not advice_only["captured"]["contingency"]


def test_the_stored_trace_keeps_each_plan_with_its_kind_in_order():
    from tools_order_reading import compact_entry
    entry = compact_entry({"learner_input": "x", "recognized_future_actions": ["volver si fiebre", "amoxicilina"],
                           "future_details": [{"kind": "advice", "text": "volver si fiebre"},
                                              {"kind": "prescription", "text": "amoxicilina"}]})
    assert entry["plans"] == [["advice", "volver si fiebre"], ["prescription", "amoxicilina"]]


def test_a_repeat_with_a_condition_is_a_contingency_and_a_schedule_is_not():
    conditioned = vc.engine_view({"played": True, "trace": [_trace(
        "Salbutamol 5 mg nbz, repetir cada 20 minutos si persiste", plans=[
            ("repeat", "repetir cada 20 minutos si persiste")])]})
    scheduled = vc.engine_view({"played": True, "trace": [_trace(
        "Salbutamol 5 mg nbz, repetir cada 20 minutos por 3 veces", plans=[
            ("repeat", "repetir cada 20 minutos por 3 veces")])]})
    assert conditioned["captured"]["contingency"] and not scheduled["captured"]["contingency"]
    assert scheduled["read"] == ["PLAN (repeat): repetir cada 20 minutos por 3 veces"]


def _annotation(n=1, **flags):
    base = {key: False for key in ("reassessment", "rationale", "expectation", "contingency",
                                   "clinically_sufficient", "ambiguous", "context_dependent")}
    base.update(flags)
    return {"items": [("MED", "x")] * n, **base}


def _view(asked=False, **captured):
    return {"asked": asked, "captured": {key: captured.get(key, False)
                                         for key in ("reassessment", "rationale", "expectation", "contingency")}}


def _review(recognized, complete, partial=0, extra=False):
    return {"n_recognized": recognized, "n_complete": complete, "n_partial": partial, "extra_or_wrong": extra}


def test_the_proposed_class_follows_the_reviewers_counts():
    sufficient = {"clinically_sufficient": True}
    assert vc.propose(_annotation(2, **sufficient), _view(), _review(2, 2)) == ("CORRECT", [])
    assert vc.propose(_annotation(2, **sufficient), _view(), _review(1, 1)) == ("PARTIAL_ENGINE_ERROR", ["parsing"])
    assert vc.propose(_annotation(2, **sufficient), _view(), _review(0, 0)) == ("ENGINE_ERROR", ["parsing"])
    assert vc.propose(_annotation(1, **sufficient), _view(), _review(1, 1, extra=True)) == ("ENGINE_ERROR", ["execution"])
    # A clear order the engine asked about is an unnecessary clarification even when it was understood.
    assert vc.propose(_annotation(1, **sufficient), _view(asked=True), _review(1, 1)) == (
        "PARTIAL_ENGINE_ERROR", ["clarification"])
    # A stated expectation the trace did not keep is the Management Trace's error.
    assert vc.propose(_annotation(1, expectation=True, **sufficient), _view(), _review(1, 1)) == (
        "PARTIAL_ENGINE_ERROR", ["trace"])
    # Genuinely ambiguous input is not forced into an engine error, and has no engine location (§40).
    assert vc.propose(_annotation(1, ambiguous=True), _view(asked=True), _review(0, 0)) == ("AMBIGUOUS_INPUT", [])
    assert vc.propose(_annotation(1, **sufficient), _view(), _review(1, 1), disagreement=True) == (
        "ANNOTATION_DISAGREEMENT", [])
    assert set(vc.LOCI) == {"parsing", "execution", "trace", "clarification", "other"}


def test_the_measures_are_counts_over_what_was_annotated_and_adjudicated():
    corpus = {"documents": [{"case": "C01", "bank_case": "asthma_24f", "language": "es", "entries": [
        {"entry_id": f"e{index}", "text": text, "status": "development"} for index, text in enumerate(
            ["Plan:", "Salbutamol 5 mg nbz y oxígeno por naricera a 3 L/min", "Hidrocortisona 200 mg ev",
             "Preguntaría si tiene alergias", "Reevaluar FR en 20 minutos", "Ceftriaxona 2 g ev"])]}]}
    engine = {
        "e0": {"played": True, "trace": [_trace("Plan:", "clarification_required")]},
        "e1": {"played": True, "trace": [_trace("Salbutamol 5 mg nbz y oxígeno por naricera a 3 L/min")]},
        "e2": {"played": True, "held": "pending_action", "trace": [_trace("Hidrocortisona 200 mg ev",
                                                                          "clarification_required")]},
        "e3": {"played": True, "trace": [_trace("Preguntaría si tiene alergias", "clarification_required")]},
        "e4": {"played": True, "trace": [_trace("Reevaluar FR en 20 minutos",
                                                actions=[(("delay_min", 20), ("type", "reassessment"))],
                                                slots={"reassessment_target": "FR"},
                                                provenance={"reassessment_target": "stated"})]},
        "e5": {"played": True, "trace": [_trace("Ceftriaxona 2 g ev")]},
    }
    rows = [
        {"entry_id": "e0", "intended_items": "—"},
        {"entry_id": "e1", "intended_items": "MED: salbutamol; O2: naricera 3 L/min", "clinically_sufficient": "Y",
         "n_recognized": "2", "n_complete": "2", "n_partial": "0", "extra_or_wrong_execution": "N"},
        {"entry_id": "e2", "intended_items": "MED: hidrocortisona 200 mg ev", "clinically_sufficient": "Y",
         "n_recognized": "1", "n_complete": "1", "n_partial": "0", "extra_or_wrong_execution": "N"},
        {"entry_id": "e3", "intended_items": "HX: alergias", "clinically_sufficient": "Y",
         "n_recognized": "0", "n_complete": "0", "n_partial": "0", "extra_or_wrong_execution": "N"},
        {"entry_id": "e4", "intended_items": "REEVAL: FR en 20 min", "reassessment": "Y", "clinically_sufficient": "Y",
         "n_recognized": "1", "n_complete": "1", "n_partial": "0", "extra_or_wrong_execution": "N",
         "classification": "CORRECT"},
        {"entry_id": "e5", "intended_items": "MED: ceftriaxona 2 g ev", "clinically_sufficient": "Y"},
    ]
    result = vc.metrics(corpus, engine, rows)
    es = result["metrics"]["es"]
    assert (es["entries"], es["no_clinical_content"], es["not_adjudicated"], es["adjudicated_entries"]) == (6, 1, 1, 4)
    assert es["order_recognition_rate"] == {"n": 4, "of": 5, "rate": 0.8}
    assert es["multi_order_success_rate"] == {"n": 1, "of": 1, "rate": 1.0}
    # Five entries could be executed as written; two of them were asked about.
    assert es["unnecessary_clarification_rate"] == {"n": 2, "of": 5, "rate": 0.4}
    # Without the history question typed where orders go, one of four.
    assert es["unnecessary_clarification_rate_orders_only"] == {"n": 1, "of": 4, "rate": 0.25}
    assert es["information_only_entries"] == 1
    assert es["reassessment_capture_rate"] == {"n": 1, "of": 1, "rate": 1.0, "spurious": 0}
    assert es["classes"]["CORRECT"] == 2 and es["classes"]["PARTIAL_ENGINE_ERROR"] == 1
    assert es["classes"]["ENGINE_ERROR"] == 1
    assert result["metrics"]["all"]["order_recognition_rate"] == es["order_recognition_rate"]
    # Every entry not classified CORRECT can be traced from the case to the class (§69).
    [first, second] = result["traceability"]
    assert first["free_text"] == "Hidrocortisona 200 mg ev" and first["classification"] == "PARTIAL_ENGINE_ERROR"
    assert set(first) >= {"case", "free_text", "reference_intent", "engine_interpretation", "execution",
                          "management_trace", "classification", "locus"}
    assert second["classification"] == "ENGINE_ERROR"


def test_impact_and_known_defect_order_the_work_and_are_checked():
    corpus = {"documents": [{"case": "C01", "bank_case": "asthma_24f", "language": "es",
                             "entries": [{"entry_id": "e1", "text": "Ceftriaxona 2 g ev", "status": "development"}]}]}
    engine = {"e1": {"played": True, "trace": [_trace("Ceftriaxona 2 g ev")]}}
    row = {"entry_id": "e1", "intended_items": "MED: ceftriaxona 2 g ev", "clinically_sufficient": "Y",
           "n_recognized": "0", "n_complete": "0", "n_partial": "0", "impact": "high", "known_defect": "KD-02",
           "locus": "PARSING"}
    [traced] = vc.metrics(corpus, engine, [row])["traceability"]
    assert (traced["impact"], traced["known_defect"], traced["locus"]) == ("HIGH", "KD-02", "PARSING")
    with pytest.raises(vc.CorpusError, match="impact"):
        vc.metrics(corpus, engine, [{**row, "impact": "severe"}])
    with pytest.raises(vc.CorpusError, match="locus"):
        vc.metrics(corpus, engine, [{**row, "locus": "reasoning_extraction"}])
    # A tag names an entry of the list, or a new failure would count as a known one.
    with pytest.raises(vc.CorpusError, match="not in the list of known defects"):
        vc.metrics(corpus, engine, [{**row, "known_defect": "KD-1"}])
    [both] = vc.metrics(corpus, engine, [{**row, "known_defect": "kd-02; KB-01"}])["traceability"]
    assert both["known_defect"] == "KD-02; KB-01"


def test_a_fifth_of_each_document_goes_to_the_second_annotator():
    corpus = {"documents": [
        {"entries": [{"entry_id": f"EM90-C01-es-b1-e{i:02d}", "status": "development"} for i in range(1, 11)]},
        {"entries": [{"entry_id": "EM91-C02-es-b1-e01", "status": "development"},
                     {"entry_id": "EM91-C02-es-b1-e02", "status": vc.RETIRED}]}]}
    chosen = vc.double_annotation_sample(corpus)
    assert len([entry for entry in chosen if entry.startswith("EM90")]) == 2
    # At least one per document, never a retired entry, and the same for whoever draws it.
    assert [entry for entry in chosen if entry.startswith("EM91")] == ["EM91-C02-es-b1-e01"]
    assert vc.double_annotation_sample(corpus) == chosen


def test_a_reviewers_class_must_be_one_of_the_five():
    corpus = {"documents": [{"case": "C01", "bank_case": "asthma_24f", "language": "es",
                             "entries": [{"entry_id": "e1", "text": "Ceftriaxona 2 g ev", "status": "development"}]}]}
    rows = [{"entry_id": "e1", "intended_items": "MED: ceftriaxona", "clinically_sufficient": "Y",
             "n_recognized": "1", "n_complete": "1", "n_partial": "0", "classification": "OK"}]
    with pytest.raises(vc.CorpusError, match="is not one of"):
        vc.metrics(corpus, {"e1": {"played": True, "trace": [_trace("Ceftriaxona 2 g ev")]}}, rows)


# --- through the real page --------------------------------------------------------------------

def test_each_entry_is_read_by_the_real_page_and_a_held_one_does_not_swallow_the_next(tmp_path, monkeypatch):
    import tools_validation_corpus as tool
    # play() sets the offline mode for its whole process, as a command should;
    # here monkeypatch takes it back when the test ends, so no later file of the
    # run inherits it (C-2026-09-26-20).
    monkeypatch.setenv("MRS_OFFLINE_CASES", "1")
    folder = _corpus(tmp_path, [("development", "EM90", "C01", "es", [[
        "Oxígeno por mascarilla", "Hidrocortisona 200 mg ev"]])])
    corpus = vc.ingest(folder, "development")
    engine = tool.play(corpus, tmp_path / "out", seed=3000)
    assert engine["documents"][0]["stopped"] is None and engine["documents"][0]["ai_calls_spent"] == 0
    assert engine["documents"][0]["unmatched_trace_entries"] == 0
    oxygen, steroid = engine["entries"]["EM90-C01-es-b1-e01"], engine["entries"]["EM90-C01-es-b1-e02"]
    # The oxygen without a flow is asked about and, with nobody to answer, cancelled ...
    assert oxygen["held"] == "pending_action" and vc.engine_view(oxygen)["asked"]
    # ... so the next order is read as an order, not as the answer to that question.
    assert [item["input"].split("\n\n")[0] for item in steroid["trace"]] == ["Hidrocortisona 200 mg ev"]
    assert vc.engine_view(steroid)["executed"]
    assert any(dict(map(tuple, signature)).get("agent") == "hydrocortisone"
               for item in steroid["trace"] for signature in item["actions"])
    assert engine["engine"]["simulator_version"]


# --- the development/sealed draw (§18, §41) -------------------------------------------------

def _pilot():
    return json.loads((ROOT / "validation" / "pilot_v1" / "manifests" / "pilot_manifest.json").read_text())


def _returned(tmp_path, files):
    folder = tmp_path / "returned"
    folder.mkdir(parents=True, exist_ok=True)
    for name in files:
        # Bytes that stand for a returned document; the draw never reads a text.
        (folder / name).write_bytes(f"synthetic bytes of {name}".encode())
    return folder


BASELINE = "0123456789abcdef0123456789abcdef01234567"


def test_the_draw_splits_every_pair_and_keeps_a_physician_whole():
    pilot = _pilot()
    received = {row["file"]: vc.hashlib.sha256(row["file"].encode()).hexdigest() for row in pilot["assignment"]}
    drawn = vc.draw_split(pilot, received, BASELINE)
    assert vc.draw_split(pilot, dict(reversed(list(received.items()))), BASELINE) == drawn
    assert drawn["missing"] == [] and len(drawn["documents"]) == 18
    subsets = {}
    for item in drawn["documents"]:
        subsets.setdefault(item["participant"], set()).add(item["subset"])
    assert all(len(found) == 1 for found in subsets.values())
    for pair in drawn["pairs"]:
        assert {subsets[pair["development"]].pop(), subsets[pair["sealed"]].pop()} == {"development", "sealed"}
    # Every case is in both subsets, because the two members of a pair share two cases.
    for subset in vc.SUBSETS:
        assert {item["case"] for item in drawn["documents"] if item["subset"] == subset} == set(pilot["cases"])
    # The seed is recomputable from what split.json keeps.
    assert vc.hashlib.sha256("\n".join(drawn["seed_lines"]).encode()).hexdigest() == drawn["seed"]


def test_the_draw_refuses_what_it_cannot_audit():
    pilot = _pilot()
    good = {"EM01_C01_es.docx": "a" * 64}
    with pytest.raises(vc.CorpusError, match="full commit"):
        vc.draw_split(pilot, good, "main")
    with pytest.raises(vc.CorpusError, match="not a document this pilot assigned"):
        vc.draw_split(pilot, {"EM01_C02_es.docx": "a" * 64}, BASELINE)
    drawn = vc.draw_split(pilot, good, BASELINE)
    assert len(drawn["missing"]) == 17 and "EM06_C05_es.docx" in drawn["missing"]


def test_split_lays_out_a_corpus_that_ingest_reads_and_never_draws_twice(tmp_path):
    import tools_validation_corpus as tool
    pilot_path = ROOT / "validation" / "pilot_v1" / "manifests" / "pilot_manifest.json"
    files = [row["file"] for row in _pilot()["assignment"]][:6]
    returned = _returned(tmp_path, files)
    with pytest.raises(vc.CorpusError, match="outside the repository"):
        tool.split(pilot_path, returned, BASELINE, ROOT / "local-data" / "corpus", "2026-10-15")
    corpus = tmp_path / "corpus"
    drawn = tool.split(pilot_path, returned, BASELINE, corpus, "2026-10-15")
    manifest = json.loads((corpus / "manifest.json").read_text())
    assert [row["subset"] for row in manifest["documents"]] == [item["subset"] for item in drawn["documents"]]
    assert all((corpus / row["subset"] / row["file"]).exists() for row in manifest["documents"])
    vc.load_manifest(corpus)  # one subset per participant, codes only
    assert tool.split(pilot_path, returned, BASELINE, corpus, "2026-10-15")["seed"] == drawn["seed"]
    (returned / files[0]).write_bytes(b"changed")
    with pytest.raises(SystemExit, match="drawn once"):
        tool.split(pilot_path, returned, BASELINE, corpus, "2026-10-15")
