"""What a resident's record holds, read by framework (cycle 9, §154S–§154AA, §154AF, §154K, §154Y).

The same views serve the resident, on their own record, and faculty and
administrators, on a resident opened from the cohort: one evidence, different
permissions (§154C). They show what already exists -- observations a faculty
member recorded, rubric reviews a faculty member confirmed -- and compute
nothing new: counts, encounters, dates, and the clinical contexts the faculty
wrote. There is no level, no percentage and no completion. An observation
target is the amount of evidence the programme aims to collect, and says so.

Every row leads back to what was observed: the objective, its observations,
the encounter each came from and that encounter's Management Trace.
"""
from datetime import datetime, timezone

import streamlit as st

from screen_language import rows as _rows, t as _t

#: The Royal College EPAs the simulator follows; every other objective is a Decision Challenge.
ROYAL_COLLEGE = ("TD1", "F1", "C1", "C2", "C3", "C4", "C14", "C15")
#: Fewer faculty-confirmed observations than this is shown as limited evidence.
#: A display rule, not a standard (§154Z).
LIMITED_BELOW = 5
TARGET_HELP = ("The observation target represents the amount of evidence the program aims to collect. "
               "It is not a competency score or percentage.")


def day(value):
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OverflowError, OSError):
        return "—"


def moment(value):
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except (TypeError, ValueError, OverflowError, OSError):
        return "—"


def encounter_labels(records):
    """One distinct label per encounter: when it began, its case, and a number while two still read alike.

    A selector whose options read the same cannot hold its choice between
    reruns: the first visual review (cycle 9) saw a document request land on
    another encounter of the same case and minute.
    """
    import resident_portal
    records = sorted(records, key=lambda record: (record["created_at"], record["id"]))
    labels = {record["id"]: f"{moment(record['created_at'])} · {resident_portal._case_label(record)}"
              for record in records}
    alike = {}
    for label in labels.values():
        alike[label] = alike.get(label, 0) + 1
    seen = {}
    for record in records:
        label = labels[record["id"]]
        if alike[label] > 1:
            seen[label] = seen.get(label, 0) + 1
            labels[record["id"]] = f"{label} · #{seen[label]}"
    return labels


def recorded(goal):
    """The observations a faculty member recorded and did not void."""
    return [item for item in goal.get("observations", []) if not item.get("voided")]


def _carried(observed, field):
    """What the opportunity each observation was confirmed under says, once each.

    Only the component observed and what stays outside it (§154W); the case's
    rationale and the generation notes are never shown (§154F).
    """
    values = []
    for item in observed:
        opportunity = (item.get("provenance") or {}).get("opportunity")
        value = opportunity.get(field) if isinstance(opportunity, dict) else None
        if isinstance(value, str) and value.strip() and value.strip() not in values:
            values.append(value.strip())
    return values


def objective_row(goal):
    observed = recorded(goal)
    contexts = []
    for item in observed:
        text = str(item.get("context") or "").strip()
        if text and text not in contexts:
            contexts.append(text)
    return {
        "objective_id": goal["objective_id"], "title": goal["title"], "scope": goal["scope"],
        "limitation": goal.get("limitation") or "", "supported": bool(goal.get("supported")),
        "target": goal.get("target"), "observations": len(observed),
        "satisfactory": sum(1 for item in observed if item.get("satisfactory")),
        "encounters": sorted({item["attempt_id"] for item in observed}),
        "last_observed": max((item["created_at"] for item in observed), default=None),
        "contexts": contexts, "components": _carried(observed, "observable_component"),
        "outside": _carried(observed, "outside_the_encounter"), "items": observed,
    }


def challenge_rows(goals):
    """The Decision Challenges that have faculty-confirmed evidence (§154U)."""
    return [objective_row(goal) for goal in goals
            if goal["objective_id"] not in ROYAL_COLLEGE and recorded(goal)]


def royal_college_rows(goals):
    """TD, F and C: every EPA the simulator follows, observed or not (§154V)."""
    return [objective_row(goal) for goal in goals if goal["objective_id"] in ROYAL_COLLEGE]


def _contribution(item, framework, code):
    kinds = {str(link.get("contribution") or "").lower()
             for link in ((item.get("provenance") or {}).get("contributions") or [])
             if isinstance(link, dict) and link.get("framework") == framework and link.get("code") == code}
    return "direct" if "direct" in kinds else "partial" if "partial" in kinds else None


def framework_rows(goals, framework):
    """Evidence related to one framework's subcompetencies or milestones, with no level (§154X).

    An observation is related to a code when its objective is linked to that
    code. The contribution recorded with the observation, DIRECT or PARTIAL, is
    counted when one was recorded; an observation recorded before contributions
    existed shows none, and none is inferred for it. One observation counts
    once per code, however many links lead there.
    """
    rows = {}
    for goal in goals:
        links = [link for link in goal.get("competency_mapping") or []
                 if isinstance(link, dict) and link.get("framework") == framework and link.get("code")]
        observed = recorded(goal)
        for link in links:
            row = rows.setdefault(link["code"], {
                "code": link["code"], "label": link.get("label") or "", "objectives": [],
                "observations": [], "direct": 0, "partial": 0, "not_recorded": 0, "sources": []})
            if goal["objective_id"] not in row["objectives"]:
                row["objectives"].append(goal["objective_id"])
            source = link.get("source_version") or link.get("source_id") or ""
            if source and source not in row["sources"]:
                row["sources"].append(source)
            seen = {item["id"] for item in row["observations"]}
            for item in observed:
                if item["id"] in seen:
                    continue
                seen.add(item["id"])
                row["observations"].append(item)
                kind = _contribution(item, framework, link["code"])
                row["direct" if kind == "direct" else "partial" if kind == "partial" else "not_recorded"] += 1
    for row in rows.values():
        row["encounters"] = sorted({item["attempt_id"] for item in row["observations"]})
    return [rows[code] for code in sorted(rows)]


def limited_rows(goals, summary):
    """Where the record still holds little: few observations, not poor performance (§154Z)."""
    rows = []
    for goal in goals:
        count = len(recorded(goal))
        if goal.get("supported") and 0 < count < LIMITED_BELOW:
            rows.append({"area": goal["objective_id"] + " · " + goal["title"], "n": count,
                         "unit": "faculty-confirmed observation(s)"})
    from rubric_progress import DOMAINS
    import language
    for domain, item in (summary.get("domains") or {}).items():
        if 0 < item["encounters"] < LIMITED_BELOW:
            title = DOMAINS[domain]["title_es" if language.current() == "es" else "title"]
            rows.append({"area": domain + " · " + title, "n": item["encounters"],
                         "unit": "faculty-confirmed encounter(s)"})
    not_yet = [goal["objective_id"] for goal in goals if goal.get("supported") and not recorded(goal)]
    return rows, not_yet


def safety_rows(reviews):
    """Critical safety events a faculty member confirmed; never an AI candidate (§154AF)."""
    rows, seen = [], set()
    for review in reviews:
        for event in review.get("critical_events") or []:
            if not isinstance(event, dict) or event.get("status") != "confirmed":
                continue
            key = (review.get("attempt_id"), event.get("event_id"))
            if key in seen:
                continue
            seen.add(key)
            rows.append({"attempt_id": review.get("attempt_id"), "encounter_at": review.get("encounter_at"),
                         "event_id": event.get("event_id") or "", "event": event.get("action") or "",
                         "confirmed_at": review.get("created_at"), "reviewer": review.get("reviewer") or ""})
    return rows


# --- rendering ------------------------------------------------------------------------------------

def _open_button(attempt_id, on_open, key):
    """The way from an observation to its encounter and Management Trace (§154Y)."""
    if on_open is not None:
        st.button(_t("Open this encounter and its Management Trace"), key=key,
                  on_click=on_open, args=(attempt_id,))


def _evidence(row, labels, on_open, prefix):
    with st.expander(_t("Evidence · {v0}", v0=row["objective_id"])):
        for item in row["items"]:
            verdict = _t("Satisfactory") if item.get("satisfactory") else _t("Needs improvement")
            st.markdown(f"**{labels.get(item['attempt_id'], _t('Encounter'))}** · " + verdict)
            st.caption(_t("Observed by faculty on {v0}", v0=day(item.get("created_at"))))
            if str(item.get("context") or "").strip():
                st.caption(_t("Observed clinical context: {v0}", v0=item["context"]))
            if str(item.get("notes") or "").strip():
                st.caption(_t("Faculty feedback: {v0}", v0=item["notes"]))
            _open_button(item["attempt_id"], on_open, f"{prefix}_{row['objective_id']}_{item['id']}")


def render_challenges(goals, labels, on_open=None, prefix="_ev"):
    rows = challenge_rows(goals)
    st.caption(_t("The Decision Challenges with faculty-confirmed evidence. Read-only: faculty record and "
                  "correct observations; nothing here can be edited."))
    if not rows:
        st.info(_t("No Decision Challenge has faculty-confirmed evidence yet."))
        return rows
    for row in rows:
        st.markdown(f"**{row['objective_id']} · {row['title']}**")
        st.caption(row["scope"])
        st.caption(_t("{v0} faculty-confirmed observation(s) ({v1} satisfactory) · {v2} encounter(s) · last observed {v3}",
                      v0=row["observations"], v1=row["satisfactory"], v2=len(row["encounters"]),
                      v3=day(row["last_observed"])))
        _evidence(row, labels, on_open, prefix + "_ch")
    return rows


def render_royal_college(goals, labels, on_open=None, prefix="_ev"):
    rows = royal_college_rows(goals)
    st.caption(_t("Royal College EPAs as observational evidence of simulated components. No EPA is completed, "
                  "no percentage is shown and no entrustment is inferred here."))
    for row in rows:
        st.markdown(f"**{row['objective_id']} · {row['title']}**")
        if not row["supported"]:
            st.caption(_t("Not enabled: current encounters are not established as offering enough "
                          "opportunities to observe this objective."))
            continue
        st.caption(_t("{v0} faculty-confirmed observation(s) across {v1} encounter(s).",
                      v0=row["observations"], v1=len(row["encounters"])))
        if row["target"]:
            st.caption(_t("Local observation target: {v0}", v0=row["target"]), help=_t(TARGET_HELP))
        if row["observations"]:
            st.caption(_t("Components observed: {v0}", v0="; ".join(row["components"]) or row["scope"]))
            outside = "; ".join(row["outside"]) or row["limitation"]
            if outside:
                st.caption(_t("What remains outside this simulator: {v0}", v0=outside))
            if row["contexts"]:
                # Descriptive only: where it was seen, never a diversity score (§154AA).
                st.caption(_t("Observed in: {v0}", v0="; ".join(row["contexts"])))
            _evidence(row, labels, on_open, prefix + "_rc")
    milestones = framework_rows(goals, "Royal College")
    if milestones:
        st.markdown("**" + _t("CanMEDS milestones related through the Decision Challenges") + "**")
        _framework_table(milestones)
    return rows


def _framework_table(rows):
    # Short columns, so the table fits a desktop screen; the source goes under it.
    st.dataframe(_rows([{
        "Code": row["code"], "Title": row["label"], "Observations": len(row["observations"]),
        "Direct": row["direct"], "Partial": row["partial"], "Encounters": len(row["encounters"]),
        "Through": ", ".join(row["objectives"]),
    } for row in rows]), hide_index=True)
    st.caption(_t("Observations: faculty-confirmed observations of the objectives linked to the code. Direct and "
                  "Partial: the contribution recorded with each observation."))
    unstated = sum(row["not_recorded"] for row in rows)
    if unstated:
        st.caption(_t("{v0} observation(s) were recorded before contributions existed and show none; none is "
                      "inferred for them.", v0=unstated))
    sources = sorted({source for row in rows for source in row["sources"]})
    if sources:
        st.caption(_t("Source: {v0}", v0="; ".join(sources)))


def render_acgme(goals):
    rows = framework_rows(goals, "ACGME")
    st.caption(_t("Evidence related to ACGME Milestones subcompetencies. No Milestone level is assigned or "
                  "inferred: a contribution is evidence for the program's Clinical Competency Committee to weigh."))
    if not rows:
        st.info(_t("No objective followed here is linked to an ACGME subcompetency."))
        return rows
    _framework_table(rows)
    st.caption(_t("A partial contribution observes part of a subcompetency; what remains outside is named with "
                  "each objective. It is not a lesser result."))
    return rows


def render_limited(goals, summary):
    rows, not_yet = limited_rows(goals, summary)
    st.markdown("**" + _t("Areas with limited evidence") + "**")
    st.caption(_t("Where the record still holds little, not where performance is weak. Fewer than {v0} "
                  "faculty-confirmed observations is listed here; that is a display rule, not a standard.",
                  v0=LIMITED_BELOW))
    if rows:
        for row in rows:
            st.caption(f"{row['area']} · {row['n']} " + _t(row["unit"]))
    else:
        st.caption(_t("No area is in this range yet."))
    if not_yet:
        st.caption(_t("Not observed yet: {v0}", v0=", ".join(not_yet)))


def render_safety(reviews, labels, on_open=None, prefix="_ev"):
    rows = safety_rows(reviews)
    st.caption(_t("Critical safety events a faculty member confirmed. They are shown apart from the "
                  "management reasoning profile and never change its shape; AI candidates and unconfirmed "
                  "events are not listed."))
    if not rows:
        st.info(_t("No confirmed critical safety event."))
        return rows
    for index, row in enumerate(rows):
        st.markdown(f"**{labels.get(row['attempt_id']) or day(row['encounter_at'])}**")
        st.caption(f"{row['event_id']} · {row['event']}")
        st.caption(_t("Confirmed {v0} by {v1}", v0=day(row["confirmed_at"]), v1=row["reviewer"] or "—"))
        _open_button(row["attempt_id"], on_open, f"{prefix}_safety_{index}")
    return rows
