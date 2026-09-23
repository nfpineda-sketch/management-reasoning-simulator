"""The faculty's own decision on the five domains, and the events beside it.

Every value on this screen is the faculty's. The AI proposal sits next to each
control as a suggestion, never as the stored value, and nothing is recorded as
confirmed until a faculty member confirms it. The totals shown here are the
ones ``rubric`` computes from what is on the screen, so the number a reviewer
sees before saving is the number that gets saved.
"""
from __future__ import annotations

import os

import streamlit as st

from account_store import AccountError
from case_assessment import declared, events as defined_events
from rubric import DOMAIN_IDS, DOMAINS, NOT_ASSESSABLE, headline, score as compute_score
from rubric_analysis import RubricAnalysisError, case_id_of, generate_rubric_proposal
from rubric_store import RubricStore

STAFF = {"faculty", "admin"}
_CHOICES = [0, 1, 2, 3, NOT_ASSESSABLE]


def _secret(name, default=""):
    """Every provider key goes through the offline rule, without exception.

    A resolver that read the key directly would reopen the leak closed on
    2026-09-22: in offline mode the key must resolve to empty at every reader,
    or a panel like this one could make a paid call nobody authorised.
    """
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    from offline_cases import withhold
    return withhold(name, str(value or os.environ.get(name, default) or "").strip())


def _label(value):
    return "Not assessable" if value == NOT_ASSESSABLE else f"{value} - " + _short(value)


def _short(value):
    return {0: "insufficient", 1: "partial", 2: "adequate", 3: "sound and anticipatory"}[value]


def _proposed_for(proposal, domain):
    for row in (proposal or {}).get("proposal", {}).get("domains", []):
        if row["domain_id"] == domain:
            return row
    return {}


def _key(record, *parts):
    return "_".join(("rubric", record["id"][:16], *(str(p) for p in parts)))


def render_rubric_assessment(context, record):
    """The rubric panel. Returns the saved review to pass to the PDFs, or None."""
    if not context or context["user"]["role"] not in STAFF:
        return None
    session = (record.get("payload") or {}).get("session") or {}
    if record.get("status") != "completed" or session.get("review_completed") is not True:
        return None
    store = RubricStore(context["store"])
    token = context["token"]
    try:
        proposal = store.latest_proposal(token, record["id"])
        review = store.latest_review(token, record["id"])
    except AccountError as error:
        st.warning(str(error))
        return None

    case_id = case_id_of(record)
    with st.expander("Management reasoning rubric - pilot 1.0", expanded=False):
        st.caption("A pilot instrument. Its scores are not ACGME Milestone levels, Canadian "
                   "stages or EPA supervision levels, and they do not assess a specialist's "
                   "competence. You confirm or change every value; the totals are computed "
                   "from what you record.")
        if not case_id:
            st.info("This encounter does not name an authored case, so its declared "
                    "opportunities and critical events are unavailable. You can still score "
                    "the five domains from the record.")
        elif declared(case_id) is None:
            st.info(f"No rubric coverage is declared for {case_id}. Scores remain available; "
                    "no critical event is defined for this case.")

        _proposal_controls(store, token, record, proposal)
        return _review_form(store, token, record, case_id, proposal, review)


def _proposal_controls(store, token, record, proposal):
    api_key = _secret("OPENAI_API_KEY")
    if proposal:
        st.caption(f"AI proposal {proposal.get('sequence', 1)} · model "
                   f"{proposal.get('model', '')} · prompt {proposal.get('prompt_version', '')} · "
                   f"generated {proposal.get('generated_at', '')}")
    else:
        st.caption("No AI proposal has been generated for this encounter revision.")
    if not api_key:
        st.info("AI generation is unavailable until OPENAI_API_KEY is configured. "
                "You can still score the rubric yourself.")
    label = "Generate a new AI proposal" if proposal else "Generate an AI proposal"
    if st.button(label, key=_key(record, "generate"), disabled=not api_key):
        model = _secret("MRS_RUBRIC_MODEL", _secret("MRS_FACULTY_MODEL", _secret("OPENAI_MODEL", "")))
        if not model:
            st.error("No rubric analysis model is configured.")
            return
        with st.spinner("Requesting one bounded proposal..."):
            try:
                report = generate_rubric_proposal(record, api_key=api_key, model=model)
                store.save_proposal(token, record["id"], report)
            except (RubricAnalysisError, AccountError) as error:
                # A failure leaves the encounter and its reports untouched. It is
                # never a zero and never a partial score.
                st.error(f"{error} The rubric assessment remains pending.")
                return
        st.rerun()


def _review_form(store, token, record, case_id, proposal, review):
    saved_scores = (review or {}).get("scores", {})
    saved_reasons = (review or {}).get("reasons", {})
    saved_changes = (review or {}).get("changes", {})
    saved_events = {row["event_id"]: row for row in (review or {}).get("critical_events", [])}
    proposed_events = {row["event_id"] for row
                       in (proposal or {}).get("proposal", {}).get("critical_events", [])}

    scores, reasons, justifications = {}, {}, {}
    for domain in DOMAIN_IDS:
        suggestion = _proposed_for(proposal, domain)
        proposed = suggestion.get("score")
        # Decisions on screen are D1, D2, D3. A rubric domain is spelled out
        # so the two cannot be read as the same thing.
        st.markdown(f"**Domain {domain[1:]} · {DOMAINS[domain]['title']}**")
        st.caption(DOMAINS[domain]["asks"])
        with st.popover(f"Descriptors for domain {domain[1:]}"):
            for level, text in sorted(DOMAINS[domain]["levels"].items()):
                st.markdown(f"**{level}** — {text}")
        if suggestion:
            st.caption(f"AI proposes **{_label(proposed)}**. {suggestion.get('rationale', '')}")
            if suggestion.get("contrary_evidence"):
                st.caption(f"Against it: {suggestion['contrary_evidence']}")
            for item in suggestion.get("learner_evidence", []):
                st.caption(f"At minute {item.get('minute')}: “{item.get('quote', '')}”")
        default = saved_scores.get(domain, proposed if proposed in _CHOICES else 2)
        value = st.selectbox("Your score", _CHOICES, index=_CHOICES.index(default),
                             format_func=_label, key=_key(record, "score", domain))
        scores[domain] = value
        if value == NOT_ASSESSABLE:
            reasons[domain] = st.text_input(
                "Why is it not assessable? (a zero is a demonstrated failure; this is not one)",
                value=saved_reasons.get(domain, ""), key=_key(record, "reason", domain))
        if suggestion and proposed in _CHOICES and value != proposed:
            justifications[domain] = st.text_input(
                f"Why you changed it from the proposed {_label(proposed)}",
                value=saved_changes.get(domain, {}).get("justification", ""),
                key=_key(record, "why", domain))
        st.divider()

    events = _event_controls(record, case_id, proposed_events, saved_events)
    try:
        preview = compute_score(scores, events)
    except Exception:
        preview = None
    if preview:
        st.markdown(f"**{headline(preview)}**")
        if not preview["coverage"]["complete"]:
            st.caption("A partial assessment keeps its events and their penalty but has no "
                       "total comparable with a complete episode.")
    columns = st.columns(2)
    action = None
    if columns[0].button("Save draft", key=_key(record, "draft")):
        action = "draft"
    if columns[1].button("Confirm assessment", key=_key(record, "confirm"), type="primary"):
        action = "confirmed"
    if action:
        try:
            saved = store.save_review(token, record["id"], scores=scores, reasons=reasons,
                                      events=events, justifications=justifications,
                                      status=action, proposal_id=(proposal or {}).get("proposal_id"))
        except AccountError as error:
            st.error(str(error))
            return review
        st.success(f"Saved as revision {saved['sequence']} · {headline(saved['totals'])}")
        return saved
    _history(store, token, record)
    return review


def _event_controls(record, case_id, proposed_events, saved_events):
    defined = defined_events(case_id) if case_id else ()
    if not defined:
        return []
    st.markdown("**Critical events defined for this case**")
    st.caption("Each is defined before the encounter. A confirmed event costs 3 points and "
               "stays visible however high the total is. Anything else that concerns you is "
               "recorded for review and carries no deduction.")
    decided = []
    for event in defined:
        kind = "Dangerous action" if event["kind"] == "dangerous_action" else "Critical omission"
        proposed = event["event_id"] in proposed_events
        saved = saved_events.get(event["event_id"], {})
        st.markdown(f"`{event['event_id']}` — **{kind}.** {event['action']}")
        st.caption(f"Triggers when: {event['trigger']} · Window {event['window_min'][0]}–"
                   f"{event['window_min'][1]} min")
        st.caption("Acceptable alternatives: " + "; ".join(event["alternatives"]))
        st.caption("Does not count when: " + "; ".join(event["exclusions"]))
        if proposed:
            st.warning("The AI proposes this event occurred. Confirm or dismiss it.")
        options = ["proposed", "confirmed", "dismissed"] if proposed else ["proposed", "confirmed"]
        labels = {"proposed": "Not decided yet", "confirmed": "Confirmed - applies the penalty",
                  "dismissed": "Dismissed - no penalty"}
        current = saved.get("status", "proposed")
        state = st.radio("Your decision", options,
                         index=options.index(current) if current in options else 0,
                         format_func=labels.get, horizontal=True,
                         key=_key(record, "event", event["event_id"]))
        justification = ""
        if state != "proposed" and not proposed:
            justification = st.text_input(
                "Why (the AI did not propose this one)", value=saved.get("justification", ""),
                key=_key(record, "eventwhy", event["event_id"]))
        elif state != "proposed":
            justification = st.text_input(
                "Note (optional)", value=saved.get("justification", ""),
                key=_key(record, "eventnote", event["event_id"]))
        if state != "proposed" or proposed:
            decided.append({"event_id": event["event_id"], "status": state,
                            "justification": justification})
        st.divider()
    return decided


def _history(store, token, record):
    try:
        history = store.history(token, record["id"])
    except AccountError:
        return
    if len(history) <= 1:
        return
    with st.expander(f"Revision history ({len(history)})"):
        for row in history:
            st.caption(f"Revision {row['sequence']} · {row['status']} · {row['reviewer']} · "
                       f"{headline(row['totals'])}")
            for domain, change in (row.get("changes") or {}).items():
                st.caption(f"   {domain}: proposed {change['proposed']} → "
                           f"{change['confirmed']} — {change['justification']}")
