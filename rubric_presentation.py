"""One reading of a rubric assessment, shared by the screen and the documents.

The compact brief, the full brief and the application all render from here, so
a rating, a penalty or a status cannot differ between what a faculty member
sees and what they print. Nothing in this module calls a model or a database:
re-exporting a document, or correcting how it looks, never costs a request.

A review that does not exist is not a zero. It is "not yet assessed", and that
is what every surface says.
"""

from rubric import (DOMAIN_IDS, DOMAINS, NOT_ASSESSABLE, PILOT_NOTICE, PILOT_NOTICE_ES,
                    VERSION, headline as score_headline)


NOT_ASSESSED_LABEL = "Not assessed"
PENDING_LABEL = "Rubric assessment pending"
FAILED_LABEL = "Rubric assessment could not be generated"


def _title(domain, language):
    return DOMAINS[domain]["title_es" if language == "es" else "title"]


def score_label(value, language="en"):
    if value == NOT_ASSESSABLE:
        return "No evaluable" if language == "es" else "Not assessable"
    if isinstance(value, int):
        return f"{value}/3"
    return "—"


def profile(review, proposal=None, language="en"):
    """One row per domain, in rubric order, whatever the review contains.

    A domain nobody decided is shown as undecided rather than dropped, because
    a five-domain instrument that quietly prints four is a different instrument.
    """
    scores = (review or {}).get("scores", {})
    reasons = (review or {}).get("reasons", {})
    changes = (review or {}).get("changes", {})
    proposed = {}
    evidence = {}
    if proposal:
        for row in proposal.get("proposal", {}).get("domains", []):
            proposed[row["domain_id"]] = row["score"]
            evidence[row["domain_id"]] = row
    rows = []
    for domain in DOMAIN_IDS:
        decided = scores.get(domain)
        source = evidence.get(domain, {})
        rows.append({
            "domain_id": domain,
            "title": _title(domain, language),
            "score": decided,
            "score_label": score_label(decided, language) if domain in scores else "—",
            "decided": domain in scores,
            # What was proposed is recorded in the change itself, so a review read
            # without its proposal still says what it moved away from.
            "proposed": changes.get(domain, {}).get("proposed", proposed.get(domain)),
            "changed": domain in changes,
            "change_justification": changes.get(domain, {}).get("justification", ""),
            "reason": reasons.get(domain, ""),
            "rationale": source.get("rationale", ""),
            "contrary_evidence": source.get("contrary_evidence", ""),
            "limits": source.get("limits", ""),
            "evidence_refs": list(source.get("evidence_refs", ())),
            "quotes": [
                {"minute": item.get("minute"), "quote": item.get("quote", ""),
                 "evidence_ref": item.get("evidence_ref", "")}
                for item in source.get("learner_evidence", ())
            ],
        })
    return rows


def alerts(review, proposal=None, language="en"):
    """Confirmed events first, then anything still waiting on the faculty.

    A safety alert stays visible however high the total is, and an event the
    model proposed but nobody has ruled on is never silently dropped.
    """
    decided = {row["event_id"]: row for row in (review or {}).get("critical_events", [])}
    rows = []
    for event_id, row in decided.items():
        if row["status"] == "confirmed":
            rows.append({"event_id": event_id, "status": "confirmed", "kind": row.get("kind", ""),
                         "action": row.get("action", ""), "proposed_by_ai": row.get("proposed_by_ai", False),
                         "justification": row.get("justification", "")})
    for row in (proposal or {}).get("proposal", {}).get("critical_events", []):
        event_id = row["event_id"]
        if event_id in decided and decided[event_id]["status"] != "proposed":
            continue
        rows.append({"event_id": event_id, "status": "awaiting_review", "kind": "",
                     "action": "", "proposed_by_ai": True,
                     "trigger_evidence": row.get("trigger_evidence", ""),
                     "justification": ""})
    for row in (review or {}).get("critical_events", []):
        if row["status"] == "dismissed":
            rows.append({"event_id": row["event_id"], "status": "dismissed",
                         "kind": row.get("kind", ""), "action": row.get("action", ""),
                         "proposed_by_ai": row.get("proposed_by_ai", False),
                         "justification": row.get("justification", "")})
    return rows


def concerns(proposal, language="en"):
    """Worries the case never defined as events. They carry no deduction."""
    return [{"concern": row.get("concern", ""), "evidence_refs": list(row.get("evidence_refs", ()))}
            for row in (proposal or {}).get("proposal", {}).get("concerns_for_review", [])]


def status_line(review, proposal=None, language="en"):
    """What this assessment is: absent, provisional, or a faculty decision."""
    if review is None:
        if proposal is None:
            return {"state": "absent", "label": PENDING_LABEL if language != "es"
                    else "Evaluación de rúbrica pendiente", "confirmed": False}
        return {"state": "proposed", "confirmed": False,
                "label": "AI proposal awaiting faculty review" if language != "es"
                         else "Propuesta de IA pendiente de revisión docente"}
    confirmed = review.get("status") == "confirmed"
    if language == "es":
        label = "Confirmado por el docente" if confirmed else "Provisional · borrador del docente"
    else:
        label = "Confirmed by faculty" if confirmed else "Provisional - faculty draft"
    return {"state": review.get("status"), "confirmed": confirmed, "label": label}


def summary(review, proposal=None, language="en"):
    """Everything a surface needs, computed once, in one shape."""
    totals = (review or {}).get("totals") or {}
    complete = bool(totals.get("coverage", {}).get("complete"))
    return {
        "rubric_version": (review or proposal or {}).get("rubric_version", VERSION),
        "status": status_line(review, proposal, language),
        "headline": score_headline(totals, language) if totals else "",
        "totals": totals,
        "complete": complete,
        "coverage_label": _coverage_label(totals, language),
        "profile": profile(review, proposal, language),
        "alerts": alerts(review, proposal, language),
        "concerns": concerns(proposal, language),
        "notice": PILOT_NOTICE_ES if language == "es" else PILOT_NOTICE,
        "traceability": traceability(review, proposal, language),
    }


def _coverage_label(totals, language):
    coverage = totals.get("coverage") or {}
    if not coverage:
        return ""
    assessed, total = coverage.get("assessed", 0), coverage.get("total", len(DOMAIN_IDS))
    if coverage.get("complete"):
        return "5 de 5 dominios evaluables" if language == "es" else "5 of 5 domains assessable"
    return (f"{assessed} de {total} dominios evaluables · sin total comparable"
            if language == "es" else
            f"{assessed} of {total} domains assessable - no comparable total")


def traceability(review, proposal=None, language="en"):
    """Where every number came from, for the full brief and the audit."""
    rows = []
    if review:
        rows.append(("Rubric version", review.get("rubric_version", "")))
        rows.append(("Assessment status", status_line(review, proposal, "en")["label"]))
        if review.get("reviewer"):
            rows.append(("Reviewed by", review["reviewer"]))
        if review.get("sequence"):
            rows.append(("Review revision", str(review["sequence"])))
    if proposal:
        rows.append(("Proposal model", proposal.get("model", "")))
        rows.append(("Proposal prompt version", proposal.get("prompt_version", "")))
        rows.append(("Proposal generated", proposal.get("generated_at", "")))
        rows.append(("Case coverage version", proposal.get("coverage_version", "")))
        if proposal.get("case_id"):
            rows.append(("Authored case", proposal["case_id"]))
    return [(label, str(value)) for label, value in rows if str(value).strip()]
