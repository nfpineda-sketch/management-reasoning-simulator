"""The rubric assessment as its own document: the score, large, and its evidence.

The fourth report of an encounter, and the only one whose subject is a number.
It is built for one reader — the faculty member who has to confirm or change
what the AI proposed — and it carries, beside every domain, the learner's own
words from the Management Trace that the proposed score rests on.

Three rules this document keeps:

  * **It is not released to the learner before a faculty member completes it.**
    ``audience="learner"`` is refused while the review is a draft or absent.
    A provisional score on a learner's record is a score they did not receive
    from anyone.
  * **It never computes anything.** The totals arrive from ``rubric``, read
    through ``rubric_presentation``, which is the same reading the application
    and the two faculty briefs use. A fourth document that recomputed the
    arithmetic would be a fourth chance to disagree with the other three.
  * **A domain that is not assessable is not a zero**, on the page or in the
    shape beside it.
"""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

import report_palette as palette
import rubric_presentation as presentation
import rubric_radar
from faculty_report import (BLUE, INK, LINE, MUTED, NAVY, PALE, _fonts, _minute,
                            _styles, _timestamp, _xml)
from rubric import DOMAIN_IDS, DOMAINS, MAX_DOMAIN_SCORE


MARGIN = 38
FACULTY_ONLY = ("Faculty document. It is not released to the resident until a faculty "
                "member has reviewed and completed it.")
FACULTY_ONLY_ES = ("Documento docente. No se entrega al residente hasta que un docente lo "
                   "haya revisado y completado.")
PROVISIONAL = ("Provisional. Nothing here has been confirmed, and no score has been "
               "recorded against this resident.")
PROVISIONAL_ES = ("Provisional. Nada de esto ha sido confirmado y no se ha registrado ningún "
                  "puntaje para este residente.")


class RubricReportError(ValueError):
    """A safe, user-facing failure. Nothing partial is ever rendered."""


def _big_styles(styles, language):
    from reportlab.lib.styles import ParagraphStyle
    body = styles["body"]
    return {
        **styles,
        # The score is the subject of this page, so it is set at the size of a
        # subject rather than of a field in a table.
        "score": ParagraphStyle("RubricScore", parent=body, fontName="FacultySans-Bold",
                                fontSize=52, leading=54, textColor=NAVY, spaceAfter=0),
        "scoreunit": ParagraphStyle("RubricScoreUnit", parent=body, fontName="FacultySans-Bold",
                                    fontSize=15, leading=18, textColor=MUTED, spaceAfter=2),
        "partial": ParagraphStyle("RubricPartial", parent=body, fontName="FacultySans-Bold",
                                  fontSize=21, leading=25, textColor=NAVY, spaceAfter=3),
        "domainscore": ParagraphStyle("RubricDomainScore", parent=body,
                                      fontName="FacultySans-Bold", fontSize=17, leading=19,
                                      textColor=NAVY, spaceAfter=0),
        "banner": ParagraphStyle("RubricBanner", parent=body, fontSize=8.6, leading=11,
                                 textColor=MUTED, spaceAfter=0),
    }


def _headline_block(assessment, styles, language):
    """The number, set large, or the sentence that exists instead of one."""
    totals = assessment["totals"] or {}
    if not assessment["complete"]:
        label = assessment["coverage_label"] or (
            "Evaluación parcial" if language == "es" else "Partial assessment")
        flow = [Paragraph(_xml(label), styles["partial"]),
                Paragraph(_xml(
                    "Un subtotal sobre menos de cinco dominios no es comparable con un "
                    "episodio completo, y no se presenta como un puntaje sobre 15."
                    if language == "es" else
                    "A subtotal over fewer than five domains is not comparable with a complete "
                    "episode, and is not presented as a score out of 15."), styles["small"])]
        if totals.get("critical_events"):
            flow.append(Paragraph(_xml(assessment["headline"]), styles["status"]))
        return flow

    adjusted = totals.get("adjusted")
    maximum = totals.get("maximum")
    penalty = totals.get("penalty") or 0
    flow = [Paragraph(f"{adjusted}", styles["score"]),
            Paragraph(_xml(("de %s" if language == "es" else "out of %s") % maximum),
                      styles["scoreunit"])]
    if penalty:
        flow.append(Paragraph(_xml(
            (f"Base {totals['base']}/{maximum} · penalización −{penalty} por "
             f"{totals['critical_events']} evento(s) crítico(s) confirmado(s)"
             if language == "es" else
             f"Base {totals['base']}/{maximum} - penalty -{penalty} for "
             f"{totals['critical_events']} confirmed critical event(s)")), styles["status"]))
    return flow


def _radar_block(assessment, language, *, average=None):
    series = [{
        "key": "encounter",
        "label": "Este encuentro" if language == "es" else "This encounter",
        "values": {row["domain_id"]: row["score"] for row in assessment["profile"]
                   if row["decided"]},
        "colour": palette.BLUE, "opacity": 0.18,
    }]
    if average:
        series.append({
            "key": "average", "label": average.get("label", ""),
            "values": average.get("values") or {},
            "colour": palette.ORANGE, "opacity": 0.09,
        })
    return rubric_radar.drawing(series, size=138, language=language)


def _profile_table(assessment, styles, width, language):
    """One row per domain: the score, and the learner's words behind it."""
    head = lambda text: Paragraph(_xml(text), styles["eyebrow"])
    against = "En contra" if language == "es" else "Against"
    limits_label = "Límites" if language == "es" else "Limits"
    changed_from = ("Cambiado respecto de lo propuesto (%s): "
                    if language == "es" else "Changed from the proposed %s: ")
    # "D3" is a decision elsewhere in these documents; a rubric domain is
    # spelled out so the two cannot be read as the same thing.
    domain_word = "Dominio" if language == "es" else "Domain"
    rows = [[head("Dominio" if language == "es" else "Domain"),
             head("Puntaje" if language == "es" else "Score"),
             head("Evidencia del encuentro" if language == "es" else "Evidence from the encounter")]]
    for row in assessment["profile"]:
        basis = row["reason"] or row["rationale"] or ""
        if row["changed"]:
            basis = (changed_from % presentation.score_label(row["proposed"], language)
                     + f"{row['change_justification']} ") + basis
        details = [Paragraph(_xml(basis or "—"), styles["small"])]
        for quote in row["quotes"][:2]:
            details.append(Paragraph(
                _xml(f"{_minute(quote['minute'])} “{quote['quote']}”"), styles["quote"]))
        if row["contrary_evidence"]:
            details.append(Paragraph(_xml(f"{against}: {row['contrary_evidence']}"), styles["small"]))
        if row["limits"]:
            details.append(Paragraph(_xml(f"{limits_label}: {row['limits']}"), styles["small"]))
        rows.append([
            [Paragraph(_xml(domain_word + " " + row["domain_id"][1:]), styles["eyebrow"]),
             Paragraph(_xml(row["title"]), styles["small"])],
            Paragraph(_xml(row["score_label"]),
                      styles["domainscore"] if row["decided"] and row["score"] != "not_assessable"
                      else styles["small"]),
            details,
        ])
    table = Table(rows, colWidths=[width * .24, width * .13, width * .63], repeatRows=1)
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), .6, LINE),
        ("LINEBELOW", (0, 1), (-1, -2), .3, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


def _events_block(assessment, styles, language):
    flow = []
    confirmed = [a for a in assessment["alerts"] if a["status"] == "confirmed"]
    waiting = [a for a in assessment["alerts"] if a["status"] == "awaiting_review"]
    dismissed = [a for a in assessment["alerts"] if a["status"] == "dismissed"]
    if confirmed:
        flow.append(Paragraph(_xml("EVENTOS CRÍTICOS CONFIRMADOS" if language == "es"
                                   else "CRITICAL EVENTS CONFIRMED"), styles["eyebrow"]))
        for alert in confirmed:
            note = alert["action"] or alert["event_id"]
            text = f"{alert['event_id']} - {note}"
            if alert["justification"]:
                text += f" {alert['justification']}"
            flow.append(Paragraph(_xml(text), styles["body"]))
        flow.append(Paragraph(_xml(
            "Un evento confirmado puede bajar un dominio y además llevar la penalización de "
            "seguridad. Ese doble peso es deliberado." if language == "es" else
            "A confirmed event can both lower a domain and carry the safety penalty. That "
            "double weight is deliberate."), styles["small"]))
    if waiting:
        flow.append(Paragraph(_xml("PENDIENTE DE SU DECISIÓN" if language == "es"
                                   else "AWAITING YOUR DECISION"), styles["eyebrow"]))
        for alert in waiting:
            flow.append(Paragraph(_xml(
                f"{alert['event_id']} - " + (
                    "propuesto por la IA y aún no confirmado ni descartado. No lleva "
                    "penalización hasta que usted decida." if language == "es" else
                    "proposed by the AI and not yet confirmed or dismissed. It carries no "
                    "penalty until you decide.")), styles["body"]))
            if alert.get("trigger_evidence"):
                flow.append(Paragraph(_xml(alert["trigger_evidence"]), styles["quote"]))
    if dismissed:
        flow.append(Paragraph(_xml("DESCARTADOS" if language == "es" else "DISMISSED"),
                              styles["eyebrow"]))
        for alert in dismissed:
            flow.append(Paragraph(_xml(f"{alert['event_id']} - {alert['justification']}"),
                                  styles["small"]))
    for concern in assessment["concerns"]:
        flow.append(Paragraph(_xml(
            ("Señalado para revisión, sin deducción: " if language == "es" else
             "Flagged for review, carrying no deduction: ") + concern["concern"]), styles["small"]))
    return flow


def build_rubric_document(review, proposal=None, record=None, *, language="en",
                          audience="faculty", average=None):
    """The flowables of the document, so a test can read it without a PDF."""
    if audience not in {"faculty", "learner"}:
        raise RubricReportError("A rubric report is rendered for faculty or for a learner.")
    if review is None:
        raise RubricReportError("There is no rubric assessment to report on this encounter.")
    if audience == "learner" and review.get("status") != "confirmed":
        # The rule, enforced here rather than at the call site, because a
        # document is copied and a call site is not.
        raise RubricReportError(
            "This assessment has not been completed by a faculty member, so it is not "
            "released to the resident.")
    _fonts()
    styles = _big_styles(_styles(), language)
    assessment = presentation.summary(review, proposal, language)
    width = A4[0] - 2 * MARGIN

    spanish = language == "es"
    flow = [
        Paragraph(_xml("EVALUACIÓN POR RÚBRICA · RAZONAMIENTO DE MANEJO" if spanish else
                       "RUBRIC ASSESSMENT - MANAGEMENT REASONING"), styles["eyebrow"]),
        Paragraph(_xml(assessment["status"]["label"]), styles["status"]),
    ]
    if audience == "faculty":
        flow.append(Paragraph(_xml(FACULTY_ONLY_ES if spanish else FACULTY_ONLY), styles["banner"]))
        if not assessment["status"]["confirmed"]:
            flow.append(Paragraph(_xml(PROVISIONAL_ES if spanish else PROVISIONAL), styles["banner"]))
    flow.append(Spacer(0, 8))

    header = Table([[_headline_block(assessment, styles, language),
                     _radar_block(assessment, language, average=average)]],
                   colWidths=[width * .52, width * .48])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (0, 0), "MIDDLE"), ("VALIGN", (1, 0), (1, 0), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(palette.PALE)),
        ("LEFTPADDING", (0, 0), (0, 0), 14), ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (1, 0), (1, 0), 10),
    ]))
    flow.append(KeepTogether([header]))
    if average and average.get("values"):
        # The caption is built by the caller, which is where the language is
        # decided: it travels already written rather than assembled here.
        flow.append(Paragraph(_xml(average.get("caption", "")), styles["small"]))
    flow.append(Spacer(0, 10))
    flow.append(_profile_table(assessment, styles, width, language))
    flow.append(Spacer(0, 6))
    flow += _events_block(assessment, styles, language)

    flow.append(Spacer(0, 6))
    flow.append(Paragraph(_xml("TRAZABILIDAD" if spanish else "TRACEABILITY"), styles["eyebrow"]))
    rows = list(assessment["traceability"])
    if record:
        rows.append(("Encounter", str(record.get("id", ""))))
        rows.append(("Encounter revision", str(record.get("revision", ""))))
        rows.append(("Saved", _timestamp(record.get("updated_at"))))
    # One flowing line rather than a column: where every number came from is a
    # footnote, and a page of its own for a footnote pushes the evidence apart.
    flow.append(Paragraph(_xml(" \u00b7 ".join(f"{label}: {value}" for label, value in rows)),
                          styles["small"]))
    if spanish:
        # The proposal is generated in English by contract (rubric_analysis
        # asks for it), so a Spanish document carries Spanish chrome and the
        # model's own reasoning in English. Better said than quietly true.
        flow.append(Paragraph(_xml(
            "El fundamento propuesto por la IA se genera en inglés; los puntajes, los "
            "dominios y la decisión docente son los mismos en ambos idiomas."), styles["small"]))
    flow.append(Paragraph(_xml(assessment["notice"]), styles["small"]))
    return flow, assessment


def render_rubric_report_pdf(review, proposal=None, record=None, *, language="en",
                             audience="faculty", average=None):
    """One page where it fits, and as many as the evidence needs where it does not."""
    flow, assessment = build_rubric_document(review, proposal, record, language=language,
                                             audience=audience, average=average)
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title="Rubric assessment", author="Management Reasoning Simulator",
        subject=assessment["rubric_version"],
    )
    document.build(flow)
    return buffer.getvalue()
