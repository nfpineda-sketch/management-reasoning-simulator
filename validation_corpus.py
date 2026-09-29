"""Validation corpus, phase 1: what emergency physicians write, read by the real reader (DF-6).

Faculty decisions of 2026-09-27, cycle 3 (§19–§25, §42–§48, §64–§75, §95–§97).
Emergency physicians receive a bank case as the simulator opens it -- the
presentation, the handover, the monitor and the chart -- and write in a Word
document, in their own words, how they would manage the patient. They never
see the simulator, its syntax, its parser or its feedback. Their text is then
read by the product's own page (``tools_validation_corpus.py``) and compared
with a reference standard that clinicians build without seeing what the
engine understood.

This module holds everything that does not need the page: the Word template
and its reading, the corpus manifest and its subsets, the annotation and
adjudication sheets, and the metrics.

What it never does:

* call a model -- everything here is deterministic (§46, §71);
* give the engine anything but the physician's original text: the annotation
  is for evaluation only (§44);
* read a Word file's properties, comments or revision authors: only the body
  text is read, and a participant is a code (EM01), never a name (§72);
* keep the sealed subset inside the repository (§73): ``check_outside``
  refuses a sealed path inside this checkout;
* move an entry between subsets silently: a sealed entry used to change the
  reader is recorded as retired from validation (§47, §74).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import unicodedata
import zipfile
from datetime import date
from pathlib import Path
from xml.etree import ElementTree
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent

CORPUS_VERSION = "VALIDATION_CORPUS_V1"
#: One corpus per language (faculty, 2026-09-28, cycle 7, §33, §37 and §87). The
#: English validation is a separate corpus: its own version, participant codes,
#: assignment, baseline, known defects and split. A manifest declares its language
#: explicitly, and it is never detected from what the physicians wrote.
CORPUS_VERSIONS = {"es": CORPUS_VERSION, "en": "VALIDATION_CORPUS_V1_EN"}
#: The registered engine baselines (never replaced, only added) and the list of
#: known defects a result's errors are tagged against (faculty, 2026-09-28, §51).
BASELINES = ROOT / "validation" / "baselines.json"
KNOWN_DEFECTS = ROOT / "validation" / "pilot_v1" / "manifests" / "known_defects.json"
# The known-defect state of DEVELOPMENT PRE-VALIDATION BASELINE V3 (cycle 9, §114), in a file of its
# own: the pilot's list is never rewritten.
KNOWN_DEFECTS_V3 = ROOT / "validation" / "known_defects_v3.json"
# VC2 (cycle 4, 2026-09-28): the faculty's shorter instruction, aligned with the
# resident's own guide (what is going on, what you do, what you expect, what
# you will check), in free text; VC1 documents are still read.
TEMPLATE_VERSION = "VC2"
# VC2-ANNOTATION-1: repeat instructions and return precautions are items of
# their own, and a return precaution is not a contingency (VC-3, 2026-09-28).
ANNOTATION_VERSION = "VC2-ANNOTATION-1"
SOURCE_TYPE = "physician_free_text_docx"
SUBSETS = {"development": "DEVELOPMENT_SUBSET_V1", "sealed": "SEALED_SUBSET_V1"}
RETIRED = "retired_from_validation"
LANGUAGES = ("es", "en")
CLASSES = ("CORRECT", "PARTIAL_ENGINE_ERROR", "ENGINE_ERROR", "AMBIGUOUS_INPUT", "ANNOTATION_DISAGREEMENT")
#: Where an engine error sits, the faculty's second dimension (cycle 4, §40). An
#: ambiguous input or an annotation disagreement is not the engine's, and has none.
LOCI = ("parsing", "execution", "trace", "clarification", "other")
#: How much an error matters, to order the work (§60). Never a score.
IMPACTS = ("CRITICAL", "HIGH", "MEDIUM", "LOW")
PARTICIPANT = re.compile(r"^EM\d{2,3}$")
CASE_CODE = re.compile(r"^C\d{2}$")

#: The pilot's six cases, approved by the faculty on 2026-09-28 (DF-15). The
#: document shows only the code, because the bank's identifiers name the diagnosis.
PILOT_CASES = {
    "C01": "asthma_24f",
    "C02": "pneumonia_46f",
    "C03": "gi_bleed_57m",
    "C04": "anaphylaxis_29f",
    "C05": "renal_colic_34m",
    "C06": "trauma_limb_hemorrhage_27m",
}

#: What an annotator may tag an intended item with. Clinical words, not the
#: engine's action types: the annotation describes what the physician meant.
ITEM_KINDS = ("MED", "FLUID", "O2", "PROC", "STUDY", "MON", "CONSULT", "DISP", "FOLLOWUP", "RETURN",
              "REPEAT", "REEVAL", "HX", "EX", "OTHER")
INFORMATION_KINDS = frozenset({"HX", "EX"})


class CorpusError(ValueError):
    """A document, manifest or sheet that cannot be used as it stands."""


# --------------------------------------------------------------------------- the template

TEXT = {
    "es": {
        "title": "Caso clínico · manejo en urgencias",
        "participant": "Código de participante",
        "participant_hint": "(lo completa quien le envía este documento)",
        "language": "Idioma de la respuesta",
        "language_value": "Español",
        "case": "Caso",
        "version": "Versión del documento",
        "instructions_title": "Instrucciones",
        "instructions": (
            "Imagine que recibe a este paciente en un servicio de urgencia. Escriba en el cuadro, en "
            "texto libre, cómo lo manejaría, en uno o varios párrafos.",
            "Cuando corresponda, deje ver qué cree que está pasando y en qué se basa; qué hará, con dosis, "
            "vías o parámetros; qué espera que ocurra o qué quiere aclarar; y qué va a reevaluar, cuándo "
            "y qué lo haría cambiar de conducta. Nada de esto es obligatorio ni tiene un orden.",
            "El documento no muestra resultados ni la evolución del paciente: si pediría algo, escríbalo; "
            "si su conducta depende del resultado, puede decir qué haría según lo que encuentre.",
            "No escriba su nombre ni otros datos personales. No necesita consultar referencias.",
        ),
        # Faculty wording, verbatim (cycle 4, 2026-09-28, §13).
        "reminder": ("Escriba naturalmente, como lo haría al manejar el paciente. No existe un formato "
                     "correcto y no intente adaptar su lenguaje a un sistema informático."),
        "patient": "El paciente",
        "monitor": "Monitor al llegar",
        "monitor_line": "FC {hr}/min · SpO₂ {spo2} % · PA {bp} mmHg · FR {rr}/min",
        "chart": "Ficha",
        "evolution": "Evolución {n}",
        "response": "Su manejo",
        "response_after": "Su manejo después de la evolución {n}",
        "response_hint": "Escriba debajo de esta línea; puede usar varios párrafos.",
        "closing": ("Al terminar, guarde el documento con el mismo nombre y devuélvalo a quien se lo "
                    "envió. Gracias por su tiempo."),
    },
    "en": {
        "title": "Clinical case · emergency department management",
        "participant": "Participant code",
        "participant_hint": "(filled in by whoever sends you this document)",
        "language": "Response language",
        "language_value": "English",
        "case": "Case",
        "version": "Document version",
        "instructions_title": "Instructions",
        "instructions": (
            "Imagine you are receiving this patient in an emergency department. In the box, write in free "
            "text how you would manage them, in one paragraph or several.",
            "Where it fits, let it show what you think is going on and what makes you think so; what you "
            "will do, with doses, routes or settings; what you expect to happen or what you want to "
            "clarify; and what you will reassess, when, and what would make you change course. None of "
            "this is required, and there is no set order.",
            "The document shows no results and not how the patient evolves: if you would order something, "
            "write it; if what you do depends on the result, you may say what you would do depending on "
            "what you find.",
            "Do not write your name or any other personal details. You do not need to look anything up.",
        ),
        "reminder": ("Write naturally, as you would when managing the patient. There is no correct format, "
                     "and do not try to adapt your language to a computer system."),
        "patient": "The patient",
        "monitor": "Monitor on arrival",
        "monitor_line": "HR {hr}/min · SpO₂ {spo2}% · BP {bp} mmHg · RR {rr}/min",
        "chart": "Chart",
        "evolution": "Evolution {n}",
        "response": "Your management",
        "response_after": "Your management after evolution {n}",
        "response_hint": "Write below this line; you may use several paragraphs.",
        "closing": ("When you finish, save the document under the same name and return it to whoever "
                    "sent it to you. Thank you for your time."),
    },
}

# Every label the reader recognises, in both languages: a document is read the
# same way whichever language it was written in.
_FIELD_LABELS = {
    "participant": {TEXT[code]["participant"] for code in LANGUAGES},
    "language": {TEXT[code]["language"] for code in LANGUAGES},
    "case": {TEXT[code]["case"] for code in LANGUAGES},
    "version": {TEXT[code]["version"] for code in LANGUAGES},
}
_LANGUAGE_VALUES = {"español": "es", "espanol": "es", "es": "es", "spanish": "es",
                    "english": "en", "inglés": "en", "ingles": "en", "en": "en"}
_RESPONSE = re.compile(r"^(?:su manejo|your management)\b", re.I)
_TEMPLATE_LINES = {text for code in LANGUAGES for text in (
    TEXT[code]["response_hint"], TEXT[code]["closing"], TEXT[code]["participant_hint"])}


class CaseSheetError(CorpusError):
    """The case cannot be shown in that language without inventing words."""


def case_sheet(case_id, language):
    """What the simulator shows at the door, in the document's language.

    The presentation and the handover (``arrival_brief``), the four numbers of
    the monitor, and the chart's weight and height -- no diagnosis, no
    examination, no result. In Spanish, the case's own translation
    (``case_text/es``); whether the faculty approved it is recorded in the
    deployment's database and is *not* checked here, so the sheet says so.
    """
    import arrival_brief
    import case_text
    import language as reader_language
    import patient_body
    from clinical_cases import variant_by_id
    if language not in LANGUAGES:
        raise CorpusError(f"Unknown language {language!r}.")
    case = variant_by_id(case_id)
    state = {"encounter_spec": {"clinical_case": case}}
    if language == "en":
        opening = case["presentation"] + arrival_brief.handover(state)
        paragraphs = [part.strip() for part in opening.split("\n\n") if part.strip()]
        chart = patient_body.chart_lines(case["patient"])
        text_source = "bank case (English, canonical)"
    else:
        rows = case_text.passages("es").get(case["id"], {})

        def spanish(path, english):
            row = rows.get(path)
            if not row or row.get("en") != english or not str(row.get("es") or "").strip():
                raise CaseSheetError(f"{case['id']}: no Spanish text for {path} that matches the case's English.")
            return str(row["es"]).strip()

        paragraphs = [spanish("/presentation", case["presentation"])]
        history = case.get("history") if isinstance(case.get("history"), dict) else {}
        lines = []
        for field in arrival_brief.HANDED_OVER:
            values = history.get(field)
            if isinstance(values, str) and values.strip():
                lines.append(spanish(f"/history/{field}", values))
            elif isinstance(values, (list, tuple)):
                lines.extend(spanish(f"/history/{field}/{index}", value)
                             for index, value in enumerate(values) if str(value).strip())
        source = str(case.get("history_source") or "").strip()
        if lines and source and source.lower() not in {"patient", "the patient"}:
            frame = case_text.FRAMES["es"]["/history_source"][0][1]
            lines.append(frame.format(spanish("/history_source", source)))
        if lines:
            paragraphs.append(" ".join(lines))
        chart = [reader_language.say(line, "es") for line in patient_body.chart_lines(case["patient"])]
        text_source = ("case_text/es translation; its faculty approval lives in the deployment's "
                       "database and was not checked when this sheet was made")
    observed = case.get("observable") or {}
    pulse = observed.get("pulse_present", True)
    monitor = TEXT[language]["monitor_line"].format(
        hr=observed.get("hr", "—"), spo2=observed.get("spo2", "—") if pulse else "—",
        bp=f"{observed.get('sbp', '—')}/{observed.get('dbp', '—')}" if pulse else "—",
        rr=observed.get("respiratory_rate", "—"))
    return {"case_id": case["id"], "language": language, "opening": paragraphs, "monitor": monitor,
            "chart": list(chart), "text_source": text_source}


_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_FONT = '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri" w:cs="Calibri"/>'
# A fixed date inside the archive, so the same template is the same bytes.
_ZIP_DATE = (2026, 1, 1, 0, 0, 0)


def _run(text, *, bold=False, italic=False, size=None, color=None):
    props = "".join(part for part in (
        "<w:b/>" if bold else "", "<w:i/>" if italic else "",
        f'<w:color w:val="{color}"/>' if color else "",
        f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>' if size else "") if part)
    pieces = str(text).split("\n")
    body = '<w:br/>'.join(f'<w:t xml:space="preserve">{escape(piece)}</w:t>' for piece in pieces)
    return f"<w:r>{f'<w:rPr>{props}</w:rPr>' if props else ''}{body}</w:r>"


def _paragraph(text="", *, bold=False, italic=False, size=None, color=None, after=120):
    spacing = f'<w:pPr><w:spacing w:after="{after}"/></w:pPr>'
    return f"<w:p>{spacing}{_run(text, bold=bold, italic=italic, size=size, color=color) if text else ''}</w:p>"


def _cell(paragraphs, width, fill=None):
    shading = f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>' if fill else ""
    return (f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shading}</w:tcPr>'
            f'{"".join(paragraphs) or _paragraph()}</w:tc>')


def _table(rows, widths):
    borders = "".join(f'<w:{side} w:val="single" w:sz="4" w:space="0" w:color="8EA9C1"/>'
                      for side in ("top", "left", "bottom", "right", "insideH", "insideV"))
    grid = "".join(f'<w:gridCol w:w="{width}"/>' for width in widths)
    body = "".join(f"<w:tr>{''.join(row)}</w:tr>" for row in rows)
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:tblBorders>{borders}'
            f'</w:tblBorders><w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>{body}</w:tbl>')


def _response_box(label, hint, lines, width=9638):
    header = _cell([_paragraph(label, bold=True, after=0), _paragraph(hint, italic=True, size=18, color="555555",
                                                                     after=0)], width, fill="DCE6F0")
    body = _cell([_paragraph(line, after=60) if line else _paragraph(after=60) for line in lines], width)
    return _table([[header], [body]], [width])


def document_xml(language, *, case_code="", participant="", sheet=None, evolutions=(), prefill=None):
    """The body of one document. ``prefill`` puts text in the response boxes: the
    tests use it to stand in for what a physician types, nothing else does."""
    text = TEXT[language]
    version = f"{TEMPLATE_VERSION}-{language.upper()}"
    field_rows = [
        [_cell([_paragraph(label, bold=True, after=0)], 3200, fill="EEF2F6"), _cell([_paragraph(value, after=0)], 6438)]
        for label, value in ((text["participant"], participant), (text["language"], text["language_value"]),
                             (text["case"], case_code), (text["version"], version))]
    if not participant:
        field_rows[0][1] = _cell([_paragraph(after=0), _paragraph(text["participant_hint"], italic=True, size=18,
                                                                  color="555555", after=0)], 6438)
    parts = [_paragraph(text["title"], bold=True, size=32, after=200), _table(field_rows, [3200, 6438]),
             _paragraph(after=60), _paragraph(text["instructions_title"], bold=True, size=26, after=100)]
    parts += [_paragraph(line) for line in text["instructions"]]
    parts.append(_paragraph(text["reminder"], bold=True, after=200))
    if sheet:
        parts.append(_paragraph(text["patient"], bold=True, size=26, after=100))
        parts += [_paragraph(line) for line in sheet["opening"]]
        parts.append(_paragraph(f"{text['monitor']}: {sheet['monitor']}"))
        parts.append(_paragraph(f"{text['chart']}: " + " · ".join(sheet["chart"]), after=200))
    prefill = list(prefill or [])
    blank = [""] * 14
    parts.append(_response_box(text["response"], text["response_hint"], (prefill[0] if prefill else None) or blank))
    for number, evolution in enumerate(evolutions, start=1):
        parts.append(_paragraph(after=60))
        parts.append(_paragraph(text["evolution"].format(n=number), bold=True, size=26, after=100))
        parts += [_paragraph(line) for line in str(evolution).split("\n\n") if line.strip()]
        box = prefill[number] if len(prefill) > number else None
        parts.append(_response_box(text["response_after"].format(n=number), text["response_hint"], box or blank))
    parts.append(_paragraph(after=60))
    parts.append(_paragraph(text["closing"], italic=True))
    section = ('<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" '
               'w:bottom="1134" w:left="1134" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:document xmlns:w="{_W}">'
            f'<w:body>{"".join(parts)}{section}</w:body></w:document>')


_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    '</Types>')
_PACKAGE_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
    'officeDocument" Target="word/document.xml"/></Relationships>')
_DOCUMENT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
    'styles" Target="styles.xml"/></Relationships>')
# Only defaults: Calibri 11 everywhere, including what the physician types.
_STYLES = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:styles xmlns:w="{_W}"><w:docDefaults>'
    f'<w:rPrDefault><w:rPr>{_FONT}<w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="es-CL" '
    'w:eastAsia="en-US" w:bidi="ar-SA"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr>'
    '<w:spacing w:after="120" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
    '</w:styles>')


def docx_bytes(body):
    """A minimal Word package around one body: the same body, the same bytes."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in (("[Content_Types].xml", _CONTENT_TYPES), ("_rels/.rels", _PACKAGE_RELS),
                              ("word/_rels/document.xml.rels", _DOCUMENT_RELS), ("word/styles.xml", _STYLES),
                              ("word/document.xml", body)):
            info = zipfile.ZipInfo(name, date_time=_ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content.encode("utf-8"))
    return buffer.getvalue()


def template(language, case_code, *, participant="", cases=None, evolutions=(), prefill=None):
    """One document for one case: (bytes, how its case text was obtained)."""
    cases = PILOT_CASES if cases is None else cases
    if not CASE_CODE.match(str(case_code or "")) or case_code not in cases:
        raise CorpusError(f"Unknown case code {case_code!r}: expected one of {sorted(cases)}.")
    if participant and not PARTICIPANT.match(participant):
        raise CorpusError(f"A participant is a code such as EM01, not {participant!r}.")
    sheet = case_sheet(cases[case_code], language)
    body = document_xml(language, case_code=case_code, participant=participant, sheet=sheet,
                        evolutions=evolutions, prefill=prefill)
    return docx_bytes(body), sheet["text_source"]


def file_name(participant, case_code, language):
    return f"{participant or 'EMxx'}_{case_code}_{language}.docx"


# --------------------------------------------------------------------------- reading a document

def _q(tag):
    return f"{{{_W}}}{tag}"


def _run_text(run, warnings):
    parts = []
    for node in run:
        if node.tag == _q("t"):
            parts.append(node.text or "")
        elif node.tag == _q("tab"):
            parts.append("\t")
        elif node.tag in (_q("br"), _q("cr")):
            parts.append("\n")
        elif node.tag == _q("noBreakHyphen"):
            parts.append("-")
        elif any(child.tag == _q("txbxContent") for child in node.iter()):
            # Drawings, legacy shapes and their compatibility wrappers alike.
            warnings.append("A text box was ignored: only the text in the paragraphs and tables is read.")
    return "".join(parts)


def _inline_text(element, warnings):
    """The visible text of one paragraph: inserted text kept, deleted text left out."""
    parts = []
    for child in element:
        tag = child.tag
        if tag == _q("r"):
            parts.append(_run_text(child, warnings))
        elif tag in (_q("del"), _q("moveFrom"), _q("pPr"), _q("rPr")):
            continue
        elif tag == _q("sdt"):
            content = child.find(_q("sdtContent"))
            if content is not None:
                parts.append(_inline_text(content, warnings))
        else:  # hyperlinks, insertions, fields, smart tags: runs inside them are text
            parts.append(_inline_text(child, warnings))
    return "".join(parts)


def _clean(text):
    text = text.replace(" ", " ").replace("\r", "\n")
    text = re.sub(r"\n\s*\n+", "\n", text)
    return "\n".join(line.strip() for line in text.split("\n")).strip()


def _blocks(parent, warnings):
    for child in parent:
        if child.tag == _q("p"):
            yield ("p", _clean(_inline_text(child, warnings)))
        elif child.tag == _q("tbl"):
            rows = []
            for row in child.findall(_q("tr")):
                cells = []
                for cell in row.findall(_q("tc")):
                    texts = []
                    for kind, content in _blocks(cell, warnings):
                        texts.extend([content] if kind == "p" else
                                     [text for nested in content for cell_texts in nested for text in cell_texts])
                    cells.append(texts)
                rows.append(cells)
            yield ("table", rows)
        elif child.tag == _q("sdt"):
            content = child.find(_q("sdtContent"))
            if content is not None:
                yield from _blocks(content, warnings)
        elif child.tag in (_q("ins"), _q("customXml")):
            yield from _blocks(child, warnings)


def read_blocks(source):
    """The body of a .docx in order, as ("p", text) and ("table", rows) blocks.

    Only ``word/document.xml`` is read into the corpus: the comments and the
    headers are never opened, and the properties only to warn that they carry
    the name of whoever saved the file -- the name is never read out.
    """
    try:
        with zipfile.ZipFile(source if not isinstance(source, bytes) else io.BytesIO(source)) as archive:
            xml = archive.read("word/document.xml")
            properties = archive.read("docProps/core.xml") if "docProps/core.xml" in archive.namelist() else b""
    except (zipfile.BadZipFile, KeyError) as error:
        raise CorpusError(f"Not a Word document: {error}") from None
    if b"<!DOCTYPE" in xml or b"<!ENTITY" in xml:
        raise CorpusError("The document declares a DOCTYPE or entities, which a Word body never does.")
    body = ElementTree.fromstring(xml).find(_q("body"))
    if body is None:
        raise CorpusError("The document has no body.")
    warnings = []
    # Whether the properties carry a name is looked at; the name itself never is.
    if re.search(rb"<(?:dc:creator|cp:lastModifiedBy)>\s*[^<\s][^<]*</", properties):
        warnings.append("The file's properties carry an author name: remove it before storing the file "
                        "(Word: File > Info > Inspect Document).")
    blocks = list(_blocks(body, warnings))
    return blocks, sorted(set(warnings))


def _folded(text):
    text = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", text).strip()


def _field(label):
    for name, labels in _FIELD_LABELS.items():
        if _folded(label).rstrip(":") in {_folded(item) for item in labels}:
            return name
    return None


def read_document(source):
    """Fields and entries of one returned document.

    Each non-empty paragraph inside a response box is one entry, in the order
    written; a line break inside a paragraph stays inside the entry. Text
    written outside the boxes is reported, never read as an entry.
    """
    blocks, warnings = read_blocks(source)
    fields, boxes = {}, []
    # Between two boxes stands the faculty's evolution text; only what follows
    # the last box, other than the closing line, can have been typed outside.
    after_last_box = []
    for kind, content in blocks:
        if kind == "table":
            texts = [text for row in content for cell in row for text in cell]
            first = next((index for index, text in enumerate(texts) if text.strip()), None)
            if first is not None and _RESPONSE.match(texts[first]):
                entries = [text for index, text in enumerate(texts)
                           if index != first and text.strip() and text not in _TEMPLATE_LINES]
                boxes.append({"box": len(boxes) + 1, "label": texts[first], "entries": entries})
                after_last_box = []
                continue
            for row in content:
                if len(row) >= 2 and row[0]:
                    name = _field(row[0][0])
                    if name:
                        values = [text for text in row[1] if text.strip() and text not in _TEMPLATE_LINES]
                        fields[name] = " ".join(values).strip()
            continue
        if boxes and content and content not in _TEMPLATE_LINES:
            after_last_box.append(content)
    if after_last_box:
        warnings.append(f"{len(after_last_box)} paragraph(s) written after the last response box were not "
                        "read as entries.")
    return {"fields": fields, "boxes": boxes, "outside": after_last_box, "warnings": warnings}


_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_PHONE = re.compile(r"(?<!\d)(?:\+?\d[\d\s-]{7,}\d)(?!\d)")
_NUMBER_WITH_UNIT = re.compile(r"\d[\d\s-]*\s*(?:mg|mcg|g|ml|mL|l|L|kg|min|h|hrs?|horas|minutos|%)\b", re.I)


def privacy_flags(text):
    """What in an entry looks like a way to identify someone: flagged, never altered."""
    flags = []
    if _EMAIL.search(text):
        flags.append("email address")
    for match in _PHONE.finditer(text):
        if not _NUMBER_WITH_UNIT.match(text[match.start():]):
            flags.append("phone-like number")
            break
    return flags


# --------------------------------------------------------------------------- the corpus

def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_outside(path, subset):
    """Refuse a sealed path inside this checkout; the development one may live in local-data/."""
    resolved = Path(path).resolve()
    inside = resolved == ROOT or ROOT in resolved.parents
    if not inside:
        return resolved
    if subset == "sealed":
        raise CorpusError(f"The sealed subset stays outside the repository (§73): {resolved} is inside it.")
    ignored = ROOT / "local-data"
    if resolved != ignored and ignored not in resolved.parents:
        raise CorpusError(f"Corpus material inside the repository goes under local-data/ only: {resolved}.")
    return resolved


# --------------------------------------------------------------------------- the raw returned documents

# Cycle 9 (2026-09-29, §26-§29, §51-§60, §95-§97). What comes back from a physician is the raw
# source: it is never edited, its SHA-256 proves it did not change, and it stays outside this
# repository. Before the split only its structure is looked at -- the file, its properties, its
# codes, its checksum and whether its response boxes are filled -- never what it says. A working
# copy clears the document's properties and nothing else: the free text is never touched. Every
# problem is flagged for a person to decide; nothing is chosen, excluded or merged automatically.
RAW_INVENTORY_VERSION = "RAW-INVENTORY-1"
_CORE = {"cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
         "dc": "http://purl.org/dc/elements/1.1/"}
#: Who saved the file: always cleared in a working copy.
_CORE_PERSONAL = {"creator": ("dc", "creator"), "lastModifiedBy": ("cp", "lastModifiedBy")}
#: What the file says about itself, where a name can be written: cleared too.
_CORE_DESCRIPTIVE = {"title": ("dc", "title"), "subject": ("dc", "subject"), "description": ("dc", "description"),
                     "keywords": ("cp", "keywords"), "category": ("cp", "category"),
                     "contentStatus": ("cp", "contentStatus")}
_APP = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
_APP_PERSONAL = ("Company", "Manager")
_CUSTOM = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
_RETURNED_LOOSE = re.compile(r"^(EM\d{2,3})_(C\d{2})_(es|en)(.*)\.docx$", re.I)
#: What a problem does to the split: these wait for a person's decision (§58, §59, §97).
BLOCKING = ("UNREADABLE", "UNEXPECTED_FILE", "UNEXPECTED_NAME", "WRONG_LANGUAGE", "WRONG_PARTICIPANT",
            "WRONG_CASE", "DOCUMENT_SAYS_OTHER", "VERSION_CONFLICT", "EMPTY", "UNEXPECTED_STRUCTURE")
#: What a person may decide about a document, with a reason; nothing is replaced silently (§97).
DECISIONS = ("EXCLUDED", "WITHDRAWN", "INVALID", "KEEP")


def _safe_xml(data):
    if b"<!DOCTYPE" in data or b"<!ENTITY" in data:
        raise CorpusError("A document part declares a DOCTYPE or entities, which Word never writes.")
    return ElementTree.fromstring(data)


def inspect_metadata(source):
    """Which personal properties a .docx carries, by name, never by value (§28, §54, §95).

    Deterministic, local, without a model: the properties Word keeps (docProps/core.xml,
    app.xml, custom.xml), whether comments or tracked changes name their author, and how
    many there are. The result says whether a de-identified working copy is needed; the
    comments and tracked changes are content, so they are only flagged for a person.
    """
    try:
        with zipfile.ZipFile(source if not isinstance(source, bytes) else io.BytesIO(source)) as archive:
            names = set(archive.namelist())
            read = {name: archive.read(name) for name in ("docProps/core.xml", "docProps/app.xml",
                                                           "docProps/custom.xml", "word/comments.xml",
                                                           "word/people.xml", "word/document.xml") if name in names}
    except zipfile.BadZipFile as error:
        raise CorpusError(f"Not a Word document: {error}") from None
    present = {}
    if "docProps/core.xml" in read:
        core = _safe_xml(read["docProps/core.xml"])
        for name, (prefix, tag) in {**_CORE_PERSONAL, **_CORE_DESCRIPTIVE}.items():
            element = core.find(f"{{{_CORE[prefix]}}}{tag}")
            present[name] = bool(element is not None and (element.text or "").strip())
    if "docProps/app.xml" in read:
        app = _safe_xml(read["docProps/app.xml"])
        for name in _APP_PERSONAL:
            element = app.find(f"{{{_APP}}}{name}")
            present[name] = bool(element is not None and (element.text or "").strip())
    custom = 0
    if "docProps/custom.xml" in read:
        # A property whose value was cleared names nobody.
        custom = sum(1 for element in _safe_xml(read["docProps/custom.xml"]).iter(f"{{{_CUSTOM}}}property")
                     if any((child.text or "").strip() for child in element))
    author = f"{{{_W}}}author"
    comments = authored_comments = 0
    if "word/comments.xml" in read:
        found = list(_safe_xml(read["word/comments.xml"]).iter(_q("comment")))
        comments = len(found)
        authored_comments = sum(1 for element in found if (element.get(author) or "").strip())
    revisions = authored_revisions = 0
    if "word/document.xml" in read:
        found = [element for element in _safe_xml(read["word/document.xml"]).iter()
                 if element.tag in (_q("ins"), _q("del"), _q("moveFrom"), _q("moveTo"))]
        revisions = len(found)
        authored_revisions = sum(1 for element in found if (element.get(author) or "").strip())
    personal = sorted(name for name in (*_CORE_PERSONAL, *_APP_PERSONAL) if present.get(name))
    descriptive = sorted(name for name in _CORE_DESCRIPTIVE if present.get(name))
    human_review = []
    if comments:
        human_review.append(f"{comments} comment(s) in the document"
                            + (", naming their author" if authored_comments else "")
                            + ": a person reads them before the document is used; they are never read as entries.")
    if revisions:
        human_review.append(f"{revisions} tracked change(s)" + (", naming their author" if authored_revisions else "")
                            + ": the reader takes the visible text; a person checks the changes.")
    if "word/people.xml" in read:
        human_review.append("The document lists the people who edited it (word/people.xml).")
    needs_copy = bool(personal or descriptive or custom)
    return {"personal_properties": personal, "descriptive_properties": descriptive, "custom_properties": custom,
            "comments": comments, "comments_with_author": authored_comments, "tracked_changes": revisions,
            "tracked_changes_with_author": authored_revisions, "human_review": human_review,
            "working_copy_needed": needs_copy,
            "status": "WORKING_COPY_NEEDED" if needs_copy else "NO_PERSONAL_PROPERTIES"}


def _cleared(data, namespace_elements):
    """The part's XML with the text of the named elements removed, the rest as it was."""
    text = data.decode("utf-8")
    cleared = []
    for label, (uri, tag) in namespace_elements.items():
        pattern = re.compile(r"(<(?:[\w.-]+:)?" + re.escape(tag) + r"\b(?:\s[^>]*)?>)([^<]*)(</(?:[\w.-]+:)?"
                             + re.escape(tag) + r">)")
        def empty(match):
            return match.group(1) + match.group(3)
        if any(match.group(2).strip() for match in pattern.finditer(text)):
            cleared.append(label)
            text = pattern.sub(empty, text)
    return text.encode("utf-8"), cleared


def deidentified_copy(raw_path, out_path):
    """A working copy with the document's properties cleared and its text untouched (§28, §55).

    The raw file is only read. Every part but docProps/ is copied byte for byte, so the
    physician's text -- word/document.xml -- is the raw file's own; comments and tracked
    changes are content and stay for a person to review. Returns what was cleared, by
    name, and both checksums.
    """
    raw_path, out_path = Path(raw_path), Path(out_path)
    if raw_path.resolve() == out_path.resolve():
        raise CorpusError("The working copy is a new file: the raw document is never written.")
    if out_path.exists():
        raise CorpusError(f"{out_path} already exists: a working copy is written once.")
    before = _sha256(raw_path)
    cleared = []
    core_targets = {name: (_CORE[prefix], tag) for name, (prefix, tag) in {**_CORE_PERSONAL, **_CORE_DESCRIPTIVE}.items()}
    with zipfile.ZipFile(raw_path) as source, zipfile.ZipFile(out_path, "w") as copy:
        for info in source.infolist():
            data = source.read(info.filename)
            if info.filename == "docProps/core.xml":
                _safe_xml(data)
                data, names = _cleared(data, core_targets)
                cleared += names
            elif info.filename == "docProps/app.xml":
                _safe_xml(data)
                data, names = _cleared(data, {name: (_APP, name) for name in _APP_PERSONAL})
                cleared += names
            elif info.filename == "docProps/custom.xml":
                _safe_xml(data)
                data, names = _cleared(data, {f"custom:{tag}": (_CUSTOM, tag) for tag in
                                              ("lpwstr", "lpstr", "bstr", "i4", "r8", "bool", "filetime")})
                cleared += ["custom properties"] if names else []
            copy.writestr(info, data)
    with zipfile.ZipFile(raw_path) as source, zipfile.ZipFile(out_path) as copy:
        unchanged = all(source.read(name) == copy.read(name) for name in source.namelist()
                        if not name.startswith("docProps/"))
    if not unchanged or _sha256(raw_path) != before:
        out_path.unlink()
        raise CorpusError("The working copy would not keep the document's text as written; nothing was written.")
    return {"raw_sha256": before, "working_sha256": _sha256(out_path), "cleared": sorted(set(cleared)),
            "text_parts_unchanged": True}


def document_structure(source):
    """Whether a returned document is complete, from its boxes, without keeping what it says (§58, §130).

    The response boxes are counted and whether each holds an entry; the codes the
    document declares are compared with its name. No entry text leaves this function.
    """
    read = read_document(source)
    fields = read["fields"]
    boxes = read["boxes"]
    filled = sum(1 for box in boxes if box["entries"])
    status = ("UNEXPECTED_STRUCTURE" if not boxes else "EMPTY" if not filled
              else "PARTIAL" if filled < len(boxes) else "COMPLETE")
    return {"status": status, "boxes": len(boxes), "boxes_filled": filled,
            "entries": sum(len(box["entries"]) for box in boxes), "outside_boxes": len(read["outside"]),
            "declared": {"participant": fields.get("participant") or None, "case": fields.get("case") or None,
                         "language": _LANGUAGE_VALUES.get(_folded(fields.get("language"))),
                         "template_version": fields.get("version") or None},
            "reader_warnings": [warning for warning in read["warnings"] if "author name" not in warning]}


def raw_inventory(raw_dir, pilot, *, received_on, decisions=None):
    """Every file in the raw folder: its codes, SHA-256, properties, completeness and problems.

    ``pilot`` is the language's pilot manifest (its assignment); ``received_on`` is the date
    the inventory is taken, written as given so the same files give the same inventory;
    ``decisions`` maps a file name to a person's decision about it (``DECISIONS``) with its
    reason. The folder must be outside this repository: raw physician documents never enter it.
    """
    language = corpus_language(pilot)
    date.fromisoformat(received_on)
    raw_dir = check_outside(raw_dir, "sealed")
    decisions = decisions or {}
    for name, decision in decisions.items():
        if decision.get("decision") not in DECISIONS or not str(decision.get("reason") or "").strip():
            raise CorpusError(f"{name}: a decision is one of {DECISIONS}, with its reason.")
    assigned = {(row["participant"], row["case"], row["language"]) for row in pilot["assignment"]}
    participants = {row["participant"] for row in pilot["assignment"]}
    records = []
    for path in sorted(item for item in Path(raw_dir).iterdir() if item.is_file() and not item.name.startswith(("~$", "."))):
        record = {"corpus_version": CORPUS_VERSIONS[language], "language": language, "pilot_id": pilot["pilot_id"],
                  "original_filename": path.name, "sha256": _sha256(path), "ingestion_date": received_on,
                  "raw_status": "RAW", "participant": None, "case": None, "file_language": None,
                  "problems": [], "metadata": None, "structure": None}
        loose = _RETURNED_LOOSE.match(path.name)
        if path.suffix.lower() != ".docx":
            record["problems"].append("UNEXPECTED_FILE")
        elif not loose:
            record["problems"].append("UNEXPECTED_NAME")
        else:
            participant, case, file_language, extra = loose.groups()
            record.update(participant=participant.upper(), case=case.upper(), file_language=file_language.lower())
            if extra or not _RETURNED.match(path.name):
                record["problems"].append("UNEXPECTED_NAME")
            if record["file_language"] != language:
                record["problems"].append("WRONG_LANGUAGE")
            elif record["participant"] not in participants:
                record["problems"].append("WRONG_PARTICIPANT")
            elif (record["participant"], record["case"], language) not in assigned:
                record["problems"].append("WRONG_CASE")
        if path.suffix.lower() == ".docx":
            try:
                record["metadata"] = inspect_metadata(path)
                record["structure"] = document_structure(path)
            except CorpusError:
                record["problems"].append("UNREADABLE")
        structure = record["structure"]
        if structure:
            if structure["status"] in ("EMPTY", "UNEXPECTED_STRUCTURE"):
                record["problems"].append(structure["status"])
            elif structure["status"] == "PARTIAL":
                record["problems"].append("PARTIAL")
            declared = structure["declared"]
            for key, found in (("participant", declared["participant"]), ("case", declared["case"]),
                               ("file_language", declared["language"])):
                if found and record[key] and found.upper() != record[key].upper():
                    record["problems"].append("DOCUMENT_SAYS_OTHER")
                    break
        record["working_status"] = ("WORKING_COPY_NEEDED" if record["metadata"] and record["metadata"]["working_copy_needed"]
                                    else "RAW_IS_WORKING" if record["metadata"] else "NONE")
        record["metadata_review_status"] = ("HUMAN_REVIEW" if record["metadata"] and record["metadata"]["human_review"]
                                            else record["metadata"]["status"] if record["metadata"] else "NOT_READ")
        records.append(record)
    # The same bytes twice count once; the same document in two versions waits for a person (§59).
    by_digest = {}
    for record in records:
        by_digest.setdefault(record["sha256"], []).append(record)
    for group in by_digest.values():
        # The file with the name as sent is the one kept; any other copy is the duplicate.
        group.sort(key=lambda record: (not _RETURNED.match(record["original_filename"]), record["original_filename"]))
        for record in group[1:]:
            record["problems"].append("DUPLICATE")
            record["duplicate_of"] = group[0]["original_filename"]
    by_key = {}
    for record in records:
        if record["participant"] and "DUPLICATE" not in record["problems"]:
            by_key.setdefault((record["participant"], record["case"], record["file_language"]), []).append(record)
    for group in by_key.values():
        if len({record["sha256"] for record in group}) > 1:
            for record in group:
                record["problems"].append("VERSION_CONFLICT")
                record["conflicts_with"] = sorted(other["original_filename"] for other in group if other is not record)
    for record in records:
        decision = decisions.get(record["original_filename"])
        if decision:
            record["decision"] = {"decision": decision["decision"], "reason": decision["reason"],
                                  "by": decision.get("by"), "on": decision.get("on")}
    return {"inventory_version": RAW_INVENTORY_VERSION, "pilot_id": pilot["pilot_id"], "language": language,
            "corpus_version": CORPUS_VERSIONS[language], "received_on": received_on, "records": records}


def readiness(inventory, pilot):
    """Whether a language's corpus can be split, and what stands in the way (§60).

    Expected, received, missing, duplicates, conflicts, the documents a working copy must
    clear and those a person must look at. Ready means no problem is left without a
    person's decision; a missing document does not block, it is listed.
    """
    language = inventory["language"]
    if corpus_language(pilot) != language:
        raise CorpusError("The inventory and the pilot are different languages: each corpus is read on its own.")
    expected = sorted(file_name(row["participant"], row["case"], row["language"])
                      for row in pilot["assignment"] if row["language"] == language)
    records = inventory["records"]
    decided = {record["original_filename"]: record["decision"]["decision"] for record in records if record.get("decision")}
    kept = {record["original_filename"] for record in records if decided.get(record["original_filename"]) == "KEEP"}
    set_aside = {name for name, decision in decided.items() if decision in ("EXCLUDED", "WITHDRAWN", "INVALID")}
    received = sorted(record["original_filename"] for record in records
                      if record["original_filename"] in expected and "DUPLICATE" not in record["problems"]
                      and record["original_filename"] not in set_aside)
    open_problems = []
    for record in records:
        name = record["original_filename"]
        if name in set_aside or "DUPLICATE" in record["problems"]:
            continue
        blocking = [problem for problem in record["problems"] if problem in BLOCKING]
        if name in kept:
            blocking = [problem for problem in blocking if problem != "VERSION_CONFLICT"]
        if "VERSION_CONFLICT" in record["problems"] and name not in kept and any(
                other in kept for other in record.get("conflicts_with", ())):
            continue
        if blocking:
            open_problems.append({"file": name, "problems": blocking})
    by_problem = {}
    for record in records:
        for problem in record["problems"]:
            by_problem.setdefault(problem, []).append(record["original_filename"])
    return {
        "language": language, "corpus_version": inventory["corpus_version"], "pilot_id": inventory["pilot_id"],
        "expected": len(expected), "received": len(received), "missing": sorted(set(expected) - set(received) - set_aside),
        "duplicates": sorted(by_problem.get("DUPLICATE", [])), "conflicts": sorted(by_problem.get("VERSION_CONFLICT", [])),
        "partial": sorted(by_problem.get("PARTIAL", [])), "empty": sorted(by_problem.get("EMPTY", [])),
        "unexpected": sorted(set(by_problem.get("UNEXPECTED_NAME", []) + by_problem.get("UNEXPECTED_FILE", [])
                                 + by_problem.get("UNEXPECTED_STRUCTURE", []) + by_problem.get("UNREADABLE", []))),
        "wrong": sorted(set(by_problem.get("WRONG_LANGUAGE", []) + by_problem.get("WRONG_PARTICIPANT", [])
                            + by_problem.get("WRONG_CASE", []) + by_problem.get("DOCUMENT_SAYS_OTHER", []))),
        "working_copy_needed": sorted(record["original_filename"] for record in records
                                      if record["working_status"] == "WORKING_COPY_NEEDED"),
        "human_review": sorted(record["original_filename"] for record in records
                               if record["metadata_review_status"] == "HUMAN_REVIEW"),
        "decisions": {name: decision for name, decision in sorted(decided.items())},
        "open_problems": open_problems, "ready_for_split": not open_problems}


def readiness_markdown(report):
    """The readiness report for a person: codes, counts and file names, never what a document says."""
    lines = [f"# Readiness · {report['pilot_id']} · {report['language'].upper()} · {report['corpus_version']}", "",
             f"- Expected: {report['expected']} · received: {report['received']} · missing: {len(report['missing'])}",
             f"- Ready for the split: **{'YES' if report['ready_for_split'] else 'NO'}**", ""]
    for label, key in (("Missing", "missing"), ("Duplicates (counted once)", "duplicates"),
                       ("Version conflicts (a person decides)", "conflicts"), ("Empty", "empty"),
                       ("Partial", "partial"), ("Unexpected", "unexpected"), ("Wrong code or language", "wrong"),
                       ("Working copy needed (document properties)", "working_copy_needed"),
                       ("For a person to look at (comments, tracked changes)", "human_review")):
        lines.append(f"- {label}: " + (", ".join(report[key]) if report[key] else "none"))
    if report["decisions"]:
        lines.append("- Decisions recorded: " + ", ".join(f"{name}: {decision}"
                                                         for name, decision in report["decisions"].items()))
    for item in report["open_problems"]:
        lines.append(f"- Open: {item['file']}: {', '.join(item['problems'])}")
    return "\n".join(lines) + "\n"


def baseline_of(engine):
    """The registered baseline a run's engine was, its known-defects list, or None for both.

    Read from the registry when the report is made, so that a run made at a
    commit registered afterwards is still named: a baseline is only ever added.
    A reading made with uncommitted changes is not any baseline.
    """
    engine = engine or {}
    registry = json.loads(BASELINES.read_text(encoding="utf-8"))["baselines"]
    found = next((item for item in registry if not engine.get("uncommitted_changes")
                  and engine.get("commit") and item["commit"] == engine["commit"]), None)
    return {"engine_baseline": found["name"] if found else None,
            "known_defects_version": found["known_defects_version"] if found else None}


def known_defects_version():
    """The version of the known-defects list as it stands in this checkout."""
    return json.loads(KNOWN_DEFECTS.read_text(encoding="utf-8"))["version"]


def known_defects_state_version():
    """The version of the known-defect state of V3 as it stands in this checkout (§114 of cycle 9)."""
    return json.loads(KNOWN_DEFECTS_V3.read_text(encoding="utf-8"))["version"]


# --------------------------------------------------------------------------- the development/sealed draw

SPLIT_RULE = (
    "The seed is the SHA-256 of these lines: the pilot's identifier, the baseline commit, then one line "
    "per returned file with its name and SHA-256, in name order. For each participant pair, in the pilot "
    "manifest's order, the pair's hexadecimal digit of the seed decides: even sends the first physician "
    "listed to development and the second to sealed, odd the reverse. All of a physician's documents "
    "follow the physician.")
_RETURNED = re.compile(r"^(EM\d{2,3})_(C\d{2})_(es|en)\.docx$")


def draw_split(pilot, received, baseline_commit):
    """Which subset each physician's documents go to, drawn once they are back (§18, §41).

    ``pilot`` is the pilot manifest (its pairs and its assignment); ``received``
    maps each returned file's name to the SHA-256 of its bytes. The draw never
    reads a document's text, so nobody can see how hard an answer was before it
    is placed; its seed does not exist before the documents do; and anyone with
    the same files and the same commit draws the same split.
    """
    if not re.fullmatch(r"[0-9a-f]{40}", str(baseline_commit or "")):
        raise CorpusError(f"The baseline is a full commit SHA, not {baseline_commit!r}.")
    assigned = {(row["participant"], row["case"], row["language"]) for row in pilot["assignment"]}
    documents = []
    for name, digest in sorted(received.items()):
        match = _RETURNED.match(name)
        if not match or tuple(match.groups()) not in assigned:
            raise CorpusError(f"{name} is not a document this pilot assigned (EM01_C01_es.docx, as sent).")
        if not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
            raise CorpusError(f"{name}: {digest!r} is not a SHA-256.")
        documents.append({"file": name, "participant": match[1], "case": match[2], "language": match[3],
                          "sha256": digest})
    lines = [f"pilot {pilot['pilot_id']}", f"baseline {baseline_commit}"]
    lines += [f"{item['file']} {item['sha256']}" for item in documents]
    seed = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    pairs, subset_of = [], {}
    for index, pair in enumerate(pilot["pairs"]):
        first, second = pair["participants"]
        digit = int(seed[index], 16)
        development, sealed = (first, second) if digit % 2 == 0 else (second, first)
        subset_of.update({development: "development", sealed: "sealed"})
        pairs.append({"pair": pair["pair"], "digit": seed[index], "development": development, "sealed": sealed})
    for item in documents:
        item["subset"] = subset_of[item["participant"]]
    returned = {item["file"] for item in documents}
    missing = sorted(file_name(*key[:2], key[2]) for key in assigned if file_name(*key[:2], key[2]) not in returned)
    return {"pilot_id": pilot["pilot_id"], "baseline_commit": baseline_commit, "rule": SPLIT_RULE,
            "seed_lines": lines, "seed": seed, "pairs": pairs, "documents": documents, "missing": missing}


def corpus_language(manifest):
    """The one language a corpus or pilot manifest declares, or a CorpusError.

    Spanish and English are separate corpora, never one run (§37 of cycle 7).
    The manifest declares its language explicitly (``"language": "es"`` or
    ``"en"``, §87), its corpus version must be that language's, and every
    document or assignment row it lists must be in it. Nothing is detected from
    the text.
    """
    version = manifest.get("corpus_version")
    by_version = {value: key for key, value in CORPUS_VERSIONS.items()}.get(version)
    declared = manifest.get("language")
    problems = []
    if version is not None and by_version is None:
        problems.append(f"corpus_version is {version!r}, not one of {sorted(CORPUS_VERSIONS.values())}.")
    if declared is not None and declared not in LANGUAGES:
        problems.append(f"language {declared!r} is not es or en.")
    elif declared and by_version and declared != by_version:
        problems.append(f"the manifest says language {declared!r}, and {version} is the {by_version!r} corpus.")
    language = declared
    if declared is None:
        # Declared, never inferred (§87 of cycle 7): LANGUAGE = ES or LANGUAGE = EN.
        problems.append('the manifest must declare its language explicitly: "language": "es" or "en".')
    rows = [row for key in ("documents", "assignment") if isinstance(manifest.get(key), list)
            for row in manifest[key] if isinstance(row, dict)]
    mixed = sorted({str(row.get("language")) for row in rows if row.get("language") not in (None, language)})
    if language and mixed:
        problems.append(f"{language!r} corpus lists documents in {mixed}: Spanish and English are separate "
                        "corpora, each with its own version, participants, assignment, baseline and split, and "
                        "are never read in one run.")
    if problems:
        raise CorpusError("The manifest mixes or misnames its language:\n- " + "\n- ".join(problems))
    return language


def load_manifest(corpus_dir):
    """The custodian's manifest, checked: codes only, one subset per participant, one language."""
    path = Path(corpus_dir) / "manifest.json"
    if not path.exists():
        raise CorpusError(f"No manifest.json in {corpus_dir}.")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    problems = []
    try:
        corpus_language(manifest)
    except CorpusError as error:
        problems.extend(str(error).split("\n- ")[1:])
    cases = manifest.get("cases") or {}
    for code in cases:
        if not CASE_CODE.match(code):
            problems.append(f"case code {code!r} is not of the form C01.")
    subsets_of = {}
    for document in manifest.get("documents") or []:
        name = document.get("file", "?")
        for key in ("file", "participant", "case", "language", "collected_on", "subset"):
            if not document.get(key):
                problems.append(f"{name}: {key} is missing.")
        if document.get("participant") and not PARTICIPANT.match(document["participant"]):
            problems.append(f"{name}: participant {document['participant']!r} is not a code such as EM01.")
        if document.get("case") and document["case"] not in cases:
            problems.append(f"{name}: case {document['case']!r} is not in the manifest's cases.")
        if document.get("language") and document["language"] not in LANGUAGES:
            problems.append(f"{name}: language {document['language']!r} is not es or en.")
        if document.get("subset") and document["subset"] not in SUBSETS:
            problems.append(f"{name}: subset {document['subset']!r} is not development or sealed.")
        subsets_of.setdefault(document.get("participant"), set()).add(document.get("subset"))
    for participant, subsets in subsets_of.items():
        if len(subsets) > 1:
            problems.append(f"{participant} has documents in {sorted(map(str, subsets))}: a participant's "
                            "documents all belong to one subset, so a writer's style cannot cross it.")
    for retired in manifest.get("retired_entries") or []:
        for key in ("entry_id", "on", "reason"):
            if not retired.get(key):
                problems.append(f"a retired entry lacks {key!r}.")
    if problems:
        raise CorpusError("The manifest cannot be used:\n- " + "\n- ".join(problems))
    return manifest


def ingest(corpus_dir, subset):
    """Every document of one subset, read into entries with their provenance.

    Nothing here depends on the clock: the same documents give the same file.
    """
    if subset not in SUBSETS:
        raise CorpusError(f"Unknown subset {subset!r}.")
    corpus_dir = check_outside(corpus_dir, subset)
    manifest = load_manifest(corpus_dir)
    retired = {item["entry_id"]: item for item in manifest.get("retired_entries") or []}
    documents, problems = [], []
    for document in manifest["documents"]:
        if document["subset"] != subset:
            continue
        path = corpus_dir / subset / document["file"]
        if not path.exists():
            problems.append(f"{document['file']}: not found in {subset}/.")
            continue
        read = read_document(path)
        fields = read["fields"]
        declared_language = _LANGUAGE_VALUES.get(_folded(fields.get("language")))
        for key, found, expected in (("participant", fields.get("participant"), document["participant"]),
                                     ("case", fields.get("case"), document["case"]),
                                     ("language", declared_language, document["language"])):
            if found and found != expected:
                problems.append(f"{document['file']}: the document says {key} {found!r}, the manifest {expected!r}.")
        if not read["boxes"]:
            problems.append(f"{document['file']}: no response box was found.")
            continue
        entries, warnings = [], list(read["warnings"])
        for box in read["boxes"]:
            for index, text in enumerate(box["entries"], start=1):
                entry_id = f"{document['participant']}-{document['case']}-{document['language']}-b{box['box']}-e{index:02d}"
                flags = privacy_flags(text)
                if flags:
                    warnings.append(f"{entry_id}: {', '.join(flags)} -- check and redact before any use.")
                entries.append({"entry_id": entry_id, "box": box["box"], "index": index, "text": text,
                                "status": RETIRED if entry_id in retired else subset})
        documents.append({
            "file": document["file"], "sha256": _sha256(path), "participant": document["participant"],
            "case": document["case"], "bank_case": manifest["cases"][document["case"]],
            "language": document["language"], "collected_on": document["collected_on"],
            "template_version": fields.get("version") or None, "entries": entries,
            "outside_boxes": len(read["outside"]), "warnings": warnings,
        })
    if problems:
        raise CorpusError("Some documents cannot be read as they stand:\n- " + "\n- ".join(problems))
    return {"corpus_version": manifest["corpus_version"], "subset": subset, "subset_version": SUBSETS[subset],
            "source_type": SOURCE_TYPE, "pilot_id": manifest.get("pilot_id"),
            "split_seed": manifest.get("split_seed"), "baseline_commit": manifest.get("baseline_commit"),
            "documents": documents, "retired_entries": sorted(retired)}


def entries_of(corpus, *, include_retired=False):
    """(document, entry) pairs in order; retired entries count only when asked."""
    for document in corpus["documents"]:
        for entry in document["entries"]:
            if include_retired or entry["status"] != RETIRED:
                yield document, entry


# --------------------------------------------------------------------------- sheets

# Disposition, follow-up, return precautions and repeat instructions are
# intended items (DISP, FOLLOWUP, RETURN, REPEAT): an entry says them, it does
# not merely have them. A return precaution is the discharge's safety plan and
# only a condition that changes the plan makes a contingency (VC-3, 2026-09-28).
ANNOTATION_COLUMNS = (
    "entry_id", "participant", "case", "language", "text",
    "intended_items", "reassessment", "rationale", "expectation", "contingency",
    "clinically_sufficient", "ambiguous", "acceptable_readings", "context_dependent",
    "annotator", "annotation_version", "note")
ENGINE_COLUMNS = ("engine_status", "engine_read", "clarification_asked", "reasoning_gate", "stated_slots",
                  "plans_not_executed", "auto_flags")
# The impact and a known defect's identifier are for ordering the work and for
# telling a known failure from a new one (§60, §73); neither enters a measure.
REVIEW_COLUMNS = ("n_recognized", "n_complete", "n_partial", "extra_or_wrong_execution",
                  "proposed_classification", "classification", "locus", "impact", "known_defect",
                  "reviewer", "review_note")
_YES = {"y", "yes", "s", "si", "sí", "1", "true", "x"}
_NO = {"n", "no", "0", "false", ""}


def write_csv(path, columns, rows):
    """UTF-8 with a byte-order mark, so a spreadsheet opens the accents correctly."""
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in columns})


def read_csv(path):
    """A sheet as a spreadsheet may save it back: comma or semicolon, UTF-8 or Windows-1252."""
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")
    header = text.split("\n", 1)[0]
    delimiter = ";" if header.count(";") > header.count(",") else ","
    return list(csv.DictReader(io.StringIO(text), delimiter=delimiter))


def annotation_rows(corpus):
    """The blind sheet: the physician's text and empty columns, nothing from the engine."""
    return [{"entry_id": entry["entry_id"], "participant": document["participant"], "case": document["case"],
             "language": document["language"], "text": entry["text"], "annotation_version": ANNOTATION_VERSION}
            for document, entry in entries_of(corpus)]


def annotation_provenance_template():
    """The record of who annotated each sheet, when, and whether blind to the engine (cycle 9, §98).

    Codes, never names. The sheets' columns and version do not change: the record sits beside
    them, filled by whoever coordinates the annotation, and the report carries it.
    """
    sheet = {"annotator": "", "annotated_on": "", "blinded_to_engine_output": None}
    return {"annotation_version": ANNOTATION_VERSION,
            "sheets": {"annotation.csv": {**sheet, "second_annotation": False},
                       "annotation_second.csv": {**sheet, "second_annotation": True}},
            "adjudication": {"reviewer": "", "adjudicated_on": ""},
            "note": "Annotator and reviewer codes only, never names. Blinded: the engine output was not seen before "
                    "the sheet was finished (annotation_guide.md)."}


def annotation_provenance(path, rows=()):
    """The record as filled, with what the adjudication sheet shows; None where nothing was recorded."""
    path = Path(path)
    record = json.loads(path.read_text(encoding="utf-8")) if path.exists() else annotation_provenance_template()
    sheets = {}
    for name, sheet in (record.get("sheets") or {}).items():
        blinded = sheet.get("blinded_to_engine_output")
        sheets[name] = {"annotator": sheet.get("annotator") or None, "annotated_on": sheet.get("annotated_on") or None,
                        "blinded_to_engine_output": blinded if isinstance(blinded, bool) else None,
                        "second_annotation": bool(sheet.get("second_annotation"))}
    adjudicated = sum(1 for row in rows if str(row.get("n_recognized") or "").strip())
    adjudication = record.get("adjudication") or {}
    return {"recorded": path.exists(), "annotation_version": record.get("annotation_version"), "sheets": sheets,
            "adjudication": {"reviewer": adjudication.get("reviewer") or None,
                             "adjudicated_on": adjudication.get("adjudicated_on") or None,
                             "adjudicated_entries": adjudicated}}


def double_annotation_sample(corpus, fraction=.2):
    """The entries a second clinician annotates blind: a fifth of each document, at least one (VC-2).

    Chosen by the SHA-256 of each entry's identifier, so the sample is fixed
    before anyone reads an entry, spreads over every physician and case, and
    is the same for whoever draws it.
    """
    chosen = []
    for document in corpus["documents"]:
        entries = [entry for entry in document["entries"] if entry["status"] != RETIRED]
        if not entries:
            continue
        ranked = sorted(entries, key=lambda entry: hashlib.sha256(
            f"second annotation {entry['entry_id']}".encode("utf-8")).hexdigest())
        chosen += [entry["entry_id"] for entry in ranked[:max(1, math.ceil(len(entries) * fraction))]]
    return chosen


def yes(value):
    folded = _folded(value)
    if folded in _YES:
        return True
    if folded in _NO:
        return False
    raise CorpusError(f"{value!r} is neither yes nor no.")


#: What an annotator writes for an entry with no clinical intent at all (a
#: heading such as "Plan:"): annotated, and with nothing to recognise.
NOTHING = {"-", "—", "–", "none", "ninguno", "ninguna", "nada"}
_FLAGS = ("reassessment", "rationale", "expectation", "contingency",
          "clinically_sufficient", "ambiguous", "context_dependent")


def items(cell):
    """An annotation's intended items: ``KIND: what`` separated by semicolons or lines."""
    found = []
    if str(cell or "").strip().casefold() in NOTHING or _folded(cell) in NOTHING:
        return found
    for part in re.split(r"[;\n]", str(cell or "")):
        part = part.strip()
        if not part:
            continue
        kind, _, rest = part.partition(":")
        if rest and kind.strip().upper() in ITEM_KINDS:
            found.append((kind.strip().upper(), rest.strip()))
        else:
            found.append(("OTHER", part))
    return found


def annotation_of(row):
    """One annotated row, checked; None while nobody has annotated it.

    A blank yes/no column reads as no. Whether the entry could be executed as
    written has to be said, though, whenever it asks for anything: it is what
    decides whether a question from the engine was necessary.
    """
    if not str(row.get("intended_items") or "").strip() and not any(
            str(row.get(key) or "").strip() for key in _FLAGS):
        return None
    annotation = {
        "items": items(row.get("intended_items")),
        **{key: yes(row.get(key)) for key in _FLAGS},
        "acceptable_readings": str(row.get("acceptable_readings") or "").strip(),
        "annotator": str(row.get("annotator") or "").strip(),
    }
    if annotation["items"] and not str(row.get("clinically_sufficient") or "").strip():
        raise CorpusError(f"{row.get('entry_id', '?')}: clinically_sufficient is required when items are annotated.")
    return annotation


def agreement(first_rows, second_rows):
    """Where two blind annotations of the same entries agree, field by field (§67, §70)."""
    second = {row["entry_id"]: row for row in second_rows}
    fields = ("n_items", "kinds", "reassessment", "rationale", "expectation", "contingency",
              "clinically_sufficient", "ambiguous")
    counts = {field: [0, 0] for field in fields}
    disagreements = {}
    for row in first_rows:
        other = second.get(row["entry_id"])
        if other is None:
            continue
        a, b = annotation_of(row), annotation_of(other)
        if a is None or b is None:
            continue
        values = {"n_items": (len(a["items"]), len(b["items"])),
                  "kinds": (sorted(kind for kind, _ in a["items"]), sorted(kind for kind, _ in b["items"]))}
        values.update({field: (a[field], b[field]) for field in fields[2:]})
        for field, (x, y) in values.items():
            counts[field][1] += 1
            if x == y:
                counts[field][0] += 1
            else:
                disagreements.setdefault(row["entry_id"], []).append(field)
    return {"compared": max((total for _, total in counts.values()), default=0),
            "agreement": {field: {"agree": agree, "of": total} for field, (agree, total) in counts.items()},
            "disagreements": disagreements}


# --------------------------------------------------------------------------- what the engine did

_SLOTS_RATIONALE = ("problem_representation", "rationale", "management_priority")
_HARNESS_MARKS = ("Guided reasoning completion", "Reasoning clarification")
CLARIFICATION_STATUSES = ("clarification_required", "not_executed")


def _normal(text):
    return re.sub(r"\s+", " ", str(text or "")).strip().casefold()


def align(entries, trace):
    """Which Management Trace entries each physician entry produced.

    The page stores the submitted text first, and anything a completion added
    after a blank line; entries are matched in order on that first part, so a
    repeated sentence goes to the next entry that wrote it.
    """
    matched = {entry["entry_id"]: [] for entry in entries}
    unmatched = []
    position = 0
    for item in trace:
        head = _normal(str(item.get("input") or "").split("\n\n")[0])
        candidates = [index for index in range(position, len(entries)) if _normal(entries[index]["text"]) == head]
        if not candidates:
            unmatched.append(item)
            continue
        index = next((i for i in candidates if not matched[entries[i]["entry_id"]]), candidates[0])
        matched[entries[index]["entry_id"]].append(item)
        position = index
    return matched, unmatched


def _action_text(signature):
    action = {key: value for key, value in signature}
    kind = action.pop("type", "?")
    if kind == "clarification":
        return f"ASKED: {action.get('message', '')}"
    return kind + ("(" + ", ".join(f"{key}={value}" for key, value in sorted(action.items())) + ")" if action else "")


def engine_view(record):
    """One entry's engine output, reduced to what the sheet and the metrics read."""
    trace = record.get("trace") or []
    harness = any(any(mark in str(item.get("input") or "") for mark in _HARNESS_MARKS) for item in trace)
    stated = {}
    for item in trace:
        for slot, text in (item.get("slots") or {}).items():
            if (item.get("provenance") or {}).get(slot) == "stated":
                stated[slot] = text
    # Each plan with its own kind, in the order the reader kept them. Pairing the
    # separately sorted texts and kinds put a return advice under "conditional"
    # whenever two plans of different kinds sorted apart (fixed 2026-09-28).
    plans = [(str(kind), str(text)) for item in trace for kind, text in item.get("plans") or []]
    conditional = [text for kind, text in plans if kind == "conditional"]
    # A repeat with an explicit condition changes the plan, like a conditional one (DF-16b).
    from family_parser import repeat_structure
    conditional_repeats = [text for kind, text in plans if kind == "repeat" and repeat_structure(text).get("condition")]
    # A reassessment the physician scheduled; "monitor" becomes one at minute 0,
    # which is watching now, not a reassessment written for later.
    reassessment_action = any(dict(signature).get("type") == "reassessment"
                              and (dict(signature).get("delay_min") or 0) > 0
                              for item in trace for signature in item.get("actions") or [])
    statuses = [item.get("status") for item in trace]
    asked = (record.get("held") in ("pending_action", "pending_bundle")
             or any(status in CLARIFICATION_STATUSES for status in statuses))
    read = []
    for item in trace:
        read += [_action_text(signature) for signature in item.get("actions") or []]
        read += [f"DONE: {label}" for label in item.get("summaries") or []]
    # What the patient received before the physician's care is history, never a plan (TD-36, cycle 9).
    read += [f"HISTORY (prior treatment): {text}" if kind == "prior_treatment"
             else f"PLAN ({kind.replace('_', ' ')}): {text}" for kind, text in plans]
    return {
        "played": bool(record.get("played")), "statuses": statuses, "executed": "executed" in statuses,
        "asked": asked, "reasoning_gate": record.get("held") == "pending_reasoning",
        "harness_completed": harness, "stated": stated, "conditional": conditional, "plans": plans, "read": read,
        "no_trace": not trace,
        "captured": {
            "reassessment": "reassessment_target" in stated or (reassessment_action and not harness),
            "rationale": any(slot in stated for slot in _SLOTS_RATIONALE),
            "expectation": "expected_effect" in stated,
            "contingency": (any(slot in stated for slot in ("contingency", "threshold")) or bool(conditional)
                            or bool(conditional_repeats)),
        },
    }


def fidelity(view, text):
    """Each stated slot: does it quote the physician, and is a working model an order?"""
    from tools_order_reading import quoted_faithfully, reads_as_an_order
    rows = []
    for slot, value in sorted(view["stated"].items()):
        quoted = quoted_faithfully(value, text)
        order = slot == "problem_representation" and reads_as_an_order(value)
        rows.append({"slot": slot, "text": value, "faithful": quoted and not order,
                     "why": "" if quoted and not order else ("an order recorded as the working model" if order
                                                             else "words the physician did not write")})
    return rows


def adjudication_rows(corpus, engine, annotations, second=None):
    """The reviewer's sheet: annotation and engine side by side, and a proposal.

    The proposal is deterministic (``propose``); the reviewer's own
    classification, when filled, is the one the report uses.
    """
    by_entry = {row["entry_id"]: row for row in annotations}
    disagreements = agreement(annotations, second)["disagreements"] if second else {}
    rows = []
    for document, entry in entries_of(corpus):
        record = engine.get(entry["entry_id"]) or {}
        view = engine_view(record)
        slots = fidelity(view, entry["text"])
        flags = [f"slot {row['slot']}: {row['why']}" for row in slots if not row["faithful"]]
        flags += ["no Management Trace entry" if view["played"] else "not played"] if view["no_trace"] else []
        flags += ["reasoning completed by the harness, not the physician"] if view["harness_completed"] else []
        annotated = by_entry.get(entry["entry_id"]) or {}
        row = {key: annotated.get(key, "") for key in ANNOTATION_COLUMNS}
        row.update({"entry_id": entry["entry_id"], "case": document["case"], "language": document["language"],
                    "text": entry["text"],
                    "engine_status": ", ".join(str(status) for status in view["statuses"]) or "—",
                    "engine_read": " | ".join(view["read"]) or "—",
                    "clarification_asked": "Y" if view["asked"] else "N",
                    "reasoning_gate": "Y" if view["reasoning_gate"] else "N",
                    "stated_slots": " | ".join(f"{slot}: {text}" for slot, text in sorted(view["stated"].items())),
                    "plans_not_executed": " | ".join(f"{kind}: {text}" for kind, text in view["plans"]),
                    "auto_flags": " | ".join(flags)})
        if entry["entry_id"] in disagreements:
            row["auto_flags"] = " | ".join(filter(None, [row["auto_flags"], "annotators disagree on "
                                                         + ", ".join(disagreements[entry["entry_id"]])]))
        rows.append(row)
    return rows


def _count(value, name, entry_id):
    try:
        number = int(str(value).strip())
    except ValueError:
        raise CorpusError(f"{entry_id}: {name} {value!r} is not a whole number.") from None
    if number < 0:
        raise CorpusError(f"{entry_id}: {name} cannot be negative.")
    return number


def propose(annotation, view, review, *, disagreement=False, faithful=True):
    """The class and locus a reviewer's counts imply (§70). Returns (class, loci)."""
    n = len(annotation["items"])
    captures_missed = any(annotation[key] and not view["captured"][key]
                          for key in ("reassessment", "rationale", "expectation", "contingency"))
    unnecessary = view["asked"] and annotation["clinically_sufficient"] and not annotation["ambiguous"]
    loci = []
    if review["n_recognized"] < n or review["n_partial"] > 0:
        loci.append("parsing")
    if review["extra_or_wrong"]:
        loci.append("execution")
    if captures_missed or not faithful:
        loci.append("trace")
    if unnecessary:
        loci.append("clarification")
    all_right = (review["n_recognized"] == n and review["n_complete"] == n and not review["extra_or_wrong"]
                 and not unnecessary and not captures_missed and faithful)
    if disagreement:
        return "ANNOTATION_DISAGREEMENT", []
    if annotation["ambiguous"]:
        return ("CORRECT", []) if all_right else ("AMBIGUOUS_INPUT", [])
    if all_right:
        return "CORRECT", []
    if review["extra_or_wrong"] or (n and review["n_recognized"] == 0):
        return "ENGINE_ERROR", loci
    return "PARTIAL_ENGINE_ERROR", loci


def review_of(row):
    """The reviewer's counts, or None while the row is not adjudicated."""
    if not str(row.get("n_recognized") or "").strip():
        return None
    entry_id = row.get("entry_id", "?")
    review = {name: _count(row.get(name) or 0, name, entry_id) for name in ("n_recognized", "n_complete", "n_partial")}
    review["extra_or_wrong"] = yes(row.get("extra_or_wrong_execution"))
    if review["n_complete"] + review["n_partial"] > review["n_recognized"]:
        raise CorpusError(f"{entry_id}: complete and partial add up to more than was recognised.")
    impact = str(row.get("impact") or "").strip().upper()
    if impact and impact not in IMPACTS:
        raise CorpusError(f"{entry_id}: impact {impact!r} is not one of {IMPACTS}.")
    loci = [part.strip().lower() for part in re.split(r"[;,]", str(row.get("locus") or "")) if part.strip()]
    unknown = [part for part in loci if part not in LOCI]
    if unknown:
        raise CorpusError(f"{entry_id}: locus {unknown} is not one of {LOCI}.")
    review["impact"] = impact or None
    # A known defect is named by its identifier in the list, or it is not known:
    # a mistyped tag would count a new failure as a known one (§73, cycle 5).
    tags = [part.strip().upper() for part in re.split(r"[;,]", str(row.get("known_defect") or "")) if part.strip()]
    unknown = [tag for tag in tags if tag not in known_defect_ids()]
    if unknown:
        raise CorpusError(f"{entry_id}: known defect {unknown} is not in the list of known defects "
                          "(validation/pilot_v1/KNOWN_DEFECTS.md) nor in the state of V3 "
                          "(validation/KNOWN_DEFECTS_V3.md).")
    review["known_defect"] = "; ".join(tags) or None
    return review


def known_defect_ids():
    """Every identifier an adjudicator may tag: the known defects and the behaviours by design.

    Those of the pilot's list and those of the state of V3, including what V3 fixed and the frozen
    baselines still carry (TD-39, TD-34, TD-36, TD-33). A tag says the defect was known when the
    analysis was made; it never takes the error out of a metric (§67 of cycle 9).
    """
    known = json.loads(KNOWN_DEFECTS.read_text(encoding="utf-8"))
    ids = {item["id"] for item in [*known["defects"], *known["known_behaviour_by_design"]]}
    state = json.loads(KNOWN_DEFECTS_V3.read_text(encoding="utf-8"))
    return ids | {item["id"] for item in [*state["defects"], *state["fixed_before_v3"],
                                          *state["known_behaviour_by_design"]]}


def _rate(numerator, denominator):
    return {"n": numerator, "of": denominator, "rate": round(numerator / denominator, 3) if denominator else None}


def metrics(corpus, engine, rows, second=None):
    """The pilot's measures (§68), per language and together, as plain counts.

    No interval and no test: with a pilot's numbers they would claim more than
    the data holds. A row nobody has adjudicated is counted as such and left
    out of the rates that need a reviewer.
    """
    disagreements = agreement(rows, second)["disagreements"] if second else {}
    texts = {entry["entry_id"]: (document, entry) for document, entry in entries_of(corpus)}
    groups = {}
    traceability, overridden = [], 0
    for row in rows:
        entry_id = row["entry_id"]
        if entry_id not in texts:
            continue
        document, entry = texts[entry_id]
        annotation = annotation_of(row)
        view = engine_view(engine.get(entry_id) or {})
        slots = fidelity(view, entry["text"])
        for language in (document["language"], "all"):
            group = groups.setdefault(language, {
                "entries": 0, "not_annotated": 0, "no_clinical_content": 0, "not_adjudicated": 0,
                "information_only": 0, "items": 0, "recognized": 0, "complete": 0, "partial": 0,
                "adjudicated_entries": 0, "extra_or_wrong": 0, "sufficient": 0, "unnecessary": 0,
                "sufficient_orders": 0, "unnecessary_orders": 0, "gate_holds": 0, "stated_slots": 0,
                "faithful_slots": 0, "multi": 0, "multi_success": 0,
                "capture": {key: {"annotated": 0, "captured": 0, "spurious": 0}
                            for key in ("reassessment", "rationale", "expectation", "contingency")},
                "classes": {name: 0 for name in CLASSES}, "flags": {name: 0 for name in ERROR_FLAGS}})
            group["entries"] += 1
            group["gate_holds"] += view["reasoning_gate"]
            group["stated_slots"] += len(slots)
            group["faithful_slots"] += sum(item["faithful"] for item in slots)
        if annotation is None:
            for language in (document["language"], "all"):
                groups[language]["not_annotated"] += 1
            continue
        n = len(annotation["items"])
        clinical = n > 0 or any(annotation[key] for key in ("reassessment", "rationale", "expectation", "contingency"))
        information_only = n > 0 and all(kind in INFORMATION_KINDS for kind, _ in annotation["items"])
        for language in (document["language"], "all"):
            group = groups[language]
            if not clinical:
                group["no_clinical_content"] += 1
                continue
            group["information_only"] += information_only
            for key, counts in group["capture"].items():
                counts["annotated"] += annotation[key]
                counts["captured"] += annotation[key] and view["captured"][key]
                counts["spurious"] += (not annotation[key]) and view["captured"][key]
            if annotation["clinically_sufficient"] and not annotation["ambiguous"]:
                group["sufficient"] += 1
                group["unnecessary"] += view["asked"]
                if not information_only:
                    group["sufficient_orders"] += 1
                    group["unnecessary_orders"] += view["asked"]
        if not clinical:
            continue
        review = review_of(row)
        if review is None:
            for language in (document["language"], "all"):
                groups[language]["not_adjudicated"] += 1
            continue
        proposed, loci = propose(annotation, view, review, disagreement=entry_id in disagreements,
                                 faithful=all(item["faithful"] for item in slots))
        final = str(row.get("classification") or "").strip().upper() or proposed
        if final not in CLASSES:
            raise CorpusError(f"{entry_id}: classification {final!r} is not one of {CLASSES}.")
        overridden += final != proposed
        flags = error_flags(annotation, view, review, loci, row.get("locus"))
        for language in (document["language"], "all"):
            group = groups[language]
            group["adjudicated_entries"] += 1
            group["items"] += n
            group["recognized"] += review["n_recognized"]
            group["complete"] += review["n_complete"]
            group["partial"] += review["n_partial"]
            group["extra_or_wrong"] += review["extra_or_wrong"]
            if n >= 2:
                group["multi"] += 1
                group["multi_success"] += review["n_recognized"] == n and not review["extra_or_wrong"]
            group["classes"][final] += 1
            for name in flags:
                group["flags"][name] += 1
        if final != "CORRECT" or flags:
            traceability.append({
                "entry_id": entry_id, "case": document["case"], "bank_case": document["bank_case"],
                "language": document["language"], "free_text": entry["text"],
                "reference_intent": row.get("intended_items", ""),
                "engine_interpretation": " | ".join(view["read"]) or "—",
                "execution": ", ".join(str(status) for status in view["statuses"]) or "—",
                "management_trace": " | ".join(f"{slot}: {text}" for slot, text in sorted(view["stated"].items())) or "—",
                "classification": final, "locus": str(row.get("locus") or "").strip() or "; ".join(loci),
                "flags": sorted(flags), "impact": review["impact"], "known_defect": review["known_defect"],
                "note": row.get("review_note", "")})
    report = {}
    for language, group in groups.items():
        report[language] = {
            "entries": group["entries"], "not_annotated": group["not_annotated"],
            "no_clinical_content": group["no_clinical_content"], "not_adjudicated": group["not_adjudicated"],
            "adjudicated_entries": group["adjudicated_entries"], "intended_items": group["items"],
            "order_recognition_rate": _rate(group["recognized"], group["items"]),
            "complete_interpretation_rate": _rate(group["complete"], group["items"]),
            "partial_interpretation_rate": _rate(group["partial"], group["items"]),
            "incorrect_execution_rate": _rate(group["extra_or_wrong"], group["adjudicated_entries"]),
            "unnecessary_clarification_rate": _rate(group["unnecessary"], group["sufficient"]),
            "unnecessary_clarification_rate_orders_only": _rate(group["unnecessary_orders"], group["sufficient_orders"]),
            "information_only_entries": group["information_only"],
            "reasoning_gate_holds": group["gate_holds"],
            "trace_fidelity_rate": _rate(group["faithful_slots"], group["stated_slots"]),
            "multi_order_success_rate": _rate(group["multi_success"], group["multi"]),
            **{f"{key}_capture_rate": {**_rate(counts["captured"], counts["annotated"]), "spurious": counts["spurious"]}
               for key, counts in group["capture"].items()},
            "classes": group["classes"],
            # Counted apart from the classes, over the adjudicated entries, so that an important
            # failure is never hidden inside a class count (cycle 9, §34, §68, §138-§140).
            "error_flags": {name: _rate(count, group["adjudicated_entries"]) for name, count in group["flags"].items()},
        }
    return {"metrics": report, "traceability": traceability, "overridden_proposals": overridden}


#: What the external report counts apart from the five classes (cycle 9, §34, §68): each is a
#: flag on an adjudicated entry, read from the columns the workflow already has; an entry can
#: carry several, and a class never hides one.
ERROR_FLAGS = ("SILENT_LOSS", "FALSE_EXECUTION", "TRACE_DISTORTION", "APPROPRIATE_CLARIFICATION")


def error_flags(annotation, view, review, loci, reviewer_locus=None):
    """The flags of one adjudicated entry.

    * SILENT_LOSS: a clear intent (clinically sufficient, not ambiguous) lost in part or whole
      with no question from the engine -- nothing happened and nothing said why.
    * FALSE_EXECUTION: the engine executed something the physician did not order (the
      reviewer's ``extra_or_wrong_execution``).
    * TRACE_DISTORTION: the record says something the physician did not express -- a capture
      missed or a slot that does not quote them (locus ``trace``, proposed or the reviewer's).
    * APPROPRIATE_CLARIFICATION: the engine asked, and the entry was ambiguous or not
      executable as written.
    """
    n = len(annotation["items"])
    written = [part.strip().lower() for part in re.split(r"[;,]", str(reviewer_locus or "")) if part.strip()]
    flags = []
    if (n and annotation["clinically_sufficient"] and not annotation["ambiguous"]
            and review["n_recognized"] < n and not view["asked"]):
        flags.append("SILENT_LOSS")
    if review["extra_or_wrong"]:
        flags.append("FALSE_EXECUTION")
    if "trace" in loci or "trace" in written:
        flags.append("TRACE_DISTORTION")
    if view["asked"] and (annotation["ambiguous"] or not annotation["clinically_sufficient"]):
        flags.append("APPROPRIATE_CLARIFICATION")
    return flags
