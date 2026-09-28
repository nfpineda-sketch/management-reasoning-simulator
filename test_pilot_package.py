"""The validation pilot's package is what the faculty approved, and ready to send (DF-15, cycle 4, 2026-09-28).

The documents are exactly what the generator writes from the bank, give only
the initial information, teach nothing about the system, and read back through
the pipeline the pilot will use. Nothing here is a physician's response.
"""
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pytest

import validation_corpus as vc

PILOT = Path(__file__).resolve().parent / "validation" / "pilot_v1"
MANIFEST = json.loads((PILOT / "manifests" / "pilot_manifest.json").read_text(encoding="utf-8"))
ASSIGNED = MANIFEST["assignment"]
FACULTY_SENTENCE = ("Escriba naturalmente, como lo haría al manejar el paciente. No existe un formato correcto y "
                    "no intente adaptar su lenguaje a un sistema informático.")


def _fold(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def _plain(path):
    blocks, _ = vc.read_blocks(path)
    parts = []
    for kind, content in blocks:
        parts += [content] if kind == "p" else [text for row in content for cell in row for text in cell]
    return "\n".join(parts)


# --- the design --------------------------------------------------------------------------------

def test_six_physicians_three_cases_each_every_case_three_times():
    assert MANIFEST["cases"] == vc.PILOT_CASES
    physicians = Counter(row["participant"] for row in ASSIGNED)
    assert sorted(physicians) == [f"EM0{n}" for n in range(1, 7)] and set(physicians.values()) == {3}
    assert set(Counter(row["case"] for row in ASSIGNED).values()) == {3}
    assert {row["language"] for row in ASSIGNED} == {"es"}


def test_no_physician_gets_three_similar_cases():
    for physician in {row["participant"] for row in ASSIGNED}:
        cases = {row["case"] for row in ASSIGNED if row["participant"] == physician}
        assert len(cases & {"C01", "C05"}) == 1, physician      # one case without shock
        assert not {"C03", "C06"} <= cases, physician          # never both haemorrhages


def test_a_pair_shares_two_cases_so_both_subsets_hold_all_six():
    shared = set()
    for pair in MANIFEST["pairs"]:
        for physician in pair["participants"]:
            cases = {row["case"] for row in ASSIGNED if row["participant"] == physician}
            assert set(pair["shared_cases"]) <= cases
        shared |= set(pair["shared_cases"])
    assert shared == set(vc.PILOT_CASES)


def test_the_matrix_says_what_the_manifest_says():
    with open(PILOT / "assignment_matrix.csv", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [(row["participante"], row["caso"], row["archivo_a_enviar"]) for row in rows] == [
        (row["participant"], row["case"], row["file"]) for row in ASSIGNED]


# --- the documents -------------------------------------------------------------------------------

def test_the_folders_hold_exactly_the_documents_to_send():
    sent = sorted(path.relative_to(PILOT / "documents").as_posix() for path in (PILOT / "documents").rglob("*")
                  if path.is_file())
    assert sent == sorted(f"{row['participant']}/{row['file']}" for row in ASSIGNED)


@pytest.mark.parametrize("row", ASSIGNED, ids=[row["file"] for row in ASSIGNED])
def test_each_document_is_what_the_generator_writes_and_gives_nothing_away(row):
    path = PILOT / "documents" / row["participant"] / row["file"]
    data = path.read_bytes()
    assert data == vc.template(row["language"], row["case"], participant=row["participant"])[0]
    listed = {item["file"]: item for item in json.loads((PILOT / "manifests" / "documents.json").read_text())["documents"]}
    assert listed[row["file"]]["sha256"] == hashlib.sha256(data).hexdigest()
    read = vc.read_document(path)
    assert read["fields"] == {"participant": row["participant"], "language": "Español", "case": row["case"],
                              "version": "VC2-ES"}
    assert [box["entries"] for box in read["boxes"]] == [[]] and read["warnings"] == []
    text = _plain(path)
    assert FACULTY_SENTENCE in text
    # The initial information exactly as the simulator opens the case.
    sheet = vc.case_sheet(MANIFEST["cases"][row["case"]], "es")
    for line in sheet["opening"] + [sheet["monitor"]] + sheet["chart"]:
        assert line in text
    # No diagnosis, no bank identifier, nothing of the system's own language (§12, §37).
    from clinical_cases import variant_by_id
    bank_id = MANIFEST["cases"][row["case"]]
    folded = _fold(text)
    assert _fold(variant_by_id(bank_id)["faculty"]["diagnosis"]) not in folded and bank_id not in text
    for word in ("asma", "neumonia", "hemorragia digestiva", "anafilax", "colico", "sepsis", "shock",
                 "parser", "palabra clave", "modelo de trabajo", "efecto esperado", "contingencia", "management trace",
                 "rubrica", "evento critico", "simulador", "c14", "td1"):
        assert word not in folded, word


def test_a_filled_document_reads_back_in_the_order_written():
    row = ASSIGNED[0]
    typed = ["Primera línea escrita para la prueba.", "Segunda línea.\nCon un salto dentro."]
    data, _ = vc.template(row["language"], row["case"], participant=row["participant"], prefill=[typed])
    assert vc.read_document(data)["boxes"][0]["entries"] == typed


def test_the_structural_verification_covers_every_document_and_claims_no_visual_check():
    record = json.loads((PILOT / "manifests" / "docx_verification.json").read_text(encoding="utf-8"))
    assert record["status"] == "DOCX STRUCTURALLY VERIFIED" and "NOT visually verified" in record["not_claimed"]
    assert record["summary"]["problems"] == [] and record["summary"]["ingest"]["entries_in_typed_order"]
    on_disk = {path.relative_to(PILOT).as_posix() for path in PILOT.rglob("*.docx")}
    assert set(record["documents"]) == on_disk and len(on_disk) == 30
    for relative, checked in record["documents"].items():
        # A document changed after the verification would need it again.
        assert checked["sha256"] == hashlib.sha256((PILOT / relative).read_bytes()).hexdigest(), relative
        assert checked["python_docx_filled_saved_reopened"] and checked["reads_back_typed_text_in_order"]


def test_the_repository_holds_no_physician_response():
    for path in (Path(__file__).resolve().parent / "validation").rglob("*.docx"):
        assert all(not box["entries"] for box in vc.read_document(path)["boxes"]), path


def test_the_physicians_message_carries_the_faculty_sentence_and_nothing_internal():
    message = (PILOT / "instructions" / "physician_instructions_es.md").read_text(encoding="utf-8")
    to_send = message.split("\n---\n")[1]
    assert FACULTY_SENTENCE in to_send.replace("**", "").replace("\n", " ")
    for word in ("parser", "palabras que reconoce", "modelo de trabajo", "contingencia", "C14"):
        assert word not in to_send


# --- the known defects of the baseline (§70, §73) ------------------------------------------------

def test_the_known_defects_are_well_formed_and_listed_the_same_in_both_files():
    known = json.loads((PILOT / "manifests" / "known_defects.json").read_text(encoding="utf-8"))
    ids = [defect["id"] for defect in known["defects"]]
    assert len(ids) == len(set(ids)) and all(re.fullmatch(r"KD-\d{2}", value) for value in ids)
    for defect in known["defects"]:
        for field in ("class", "example", "severity", "known_cause", "why_not_fixed", "next_step", "pilot_relevance"):
            assert defect[field], (defect["id"], field)
        assert defect["severity"] in vc.IMPACTS and defect["location"] in vc.LOCI
    listed = re.findall(r"^\| (KD-\d{2}) \|", (PILOT / "KNOWN_DEFECTS.md").read_text(encoding="utf-8"), re.M)
    assert listed == ids
