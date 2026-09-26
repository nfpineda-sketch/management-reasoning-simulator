"""The faculty's own decision on the five domains, and the events beside it.

Every value on this screen is the faculty's. The AI proposal sits next to each
control as a suggestion, never as the stored value, and nothing is recorded as
confirmed until a faculty member confirms it. The totals shown here are the
ones ``rubric`` computes from what is on the screen, so the number a reviewer
sees before saving is the number that gets saved.
"""
from __future__ import annotations

import os
from html import escape

import streamlit as st

import report_palette as palette

from account_store import AccountError
import evaluation_basis
from rubric import DOMAIN_IDS, DOMAINS, NOT_ASSESSABLE, headline, score as compute_score
from rubric_analysis import (RubricAnalysisError, case_id_of, generate_rubric_proposal,
                             proposed_event_rows)
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


def render_rubric_assessment(context, record, *, training_year=None):
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
    # What this encounter is judged against. A generated case, an older record,
    # an invalid identifier and a damaged record each say what they are; none
    # of them closes the panel or the encounter's documents (2026-09-25).
    basis = evaluation_basis.resolve(record)
    with st.expander("Management reasoning rubric - pilot 1.0", expanded=False):
        st.caption("A pilot instrument. Its scores are not ACGME Milestone levels, Canadian "
                   "stages or EPA supervision levels, and they do not assess a specialist's "
                   "competence. You confirm or change every value; the totals are computed "
                   "from what you record.")
        limitation = (basis.get("limitation") or {}).get("en")
        if basis["status"] in ("unknown_case", "corrupt"):
            st.error(limitation)
        elif limitation:
            st.info(limitation)
        elif basis["declaration"] is None:
            st.info(f"No rubric coverage is declared for {case_id}. Scores remain available; "
                    "no critical event is defined for this case.")

        _proposal_controls(store, token, record, proposal)
        return _review_form(store, token, record, case_id, proposal, review, training_year)


def _declared_context(store, token, record):
    """The help declaration as it stands now, frozen into the request.

    The rubric records it and never scores it; an encounter nobody declared
    anything about is "not reported", a valid state.
    """
    import encounter_context
    try:
        current = encounter_context.EncounterContextStore(store.accounts).current(token, record["id"])
    except AccountError:
        current = {}
    return encounter_context.snapshot(current)


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
                report = generate_rubric_proposal(record, api_key=api_key, model=model,
                                                  context=_declared_context(store, token, record))
                store.save_proposal(token, record["id"], report)
            except (RubricAnalysisError, AccountError) as error:
                # A failure leaves the encounter and its reports untouched. It is
                # never a zero and never a partial score.
                st.error(f"{error} The rubric assessment remains pending.")
                return
        st.rerun()


def _render_flags(check):
    """Where the proposal and the record disagree, before anything is decided."""
    flags = check.get("flags") or []
    if not flags:
        return
    lines = []
    for flag in flags:
        subject = (f"`{flag['event_id']}`" if flag.get("event_id")
                   else f"Domain {str(flag.get('domain_id', ''))[1:]}")
        lines.append(f"- {subject}: {flag['label']}. " + " ".join(flag.get("facts") or []))
    st.warning("**Check before deciding: the proposal and the record disagree.**\n\n"
               + "\n".join(lines)
               + "\n\nThese marks change nothing by themselves; the decision stays yours.")


def _review_form(store, token, record, case_id, proposal, review, training_year=None):
    import rubric_presentation
    check = rubric_presentation.record_check(proposal, record)
    prose = rubric_presentation.model_prose(record)
    _render_flags(check)
    saved_scores = (review or {}).get("scores", {})
    saved_reasons = (review or {}).get("reasons", {})
    saved_changes = (review or {}).get("changes", {})
    saved_events = {row["event_id"]: row for row in (review or {}).get("critical_events", [])}
    proposed_events = {row["event_id"] for row in proposed_event_rows(proposal)}

    scores, reasons, justifications = {}, {}, {}
    # Every block below keeps one fixed place on the page. A domain left "not
    # assessable" adds a field, and without a container of its own everything
    # after it -- the shape, the buttons -- moved down a place: while the page
    # reran, the previous run's buttons stayed on screen, faded, where they had
    # been (development app, 2026-09-26).
    for domain in DOMAIN_IDS:
        with st.container():
            suggestion = _proposed_for(proposal, domain)
            proposed = suggestion.get("score")
            # Decisions on screen are D1, D2, D3. A rubric domain is spelled out
            # so the two cannot be read as the same thing.
            st.markdown(f"**Domain {domain[1:]} · {DOMAINS[domain]['title']}**")
            st.caption(DOMAINS[domain]["asks"])
            with st.popover(f"Descriptors for domain {domain[1:]}"):
                for level, text in sorted(DOMAINS[domain]["levels"].items()):
                    st.markdown(f"**{level}** — {text}")
            domain_check = (check.get("domains") or {}).get(domain) or {}
            for fact in domain_check.get("facts", []):
                st.caption(f"Record: {fact}")
            if suggestion:
                st.caption(f"AI proposes **{_label(proposed)}**. {prose(suggestion.get('rationale', ''))}")
                if suggestion.get("contrary_evidence"):
                    st.caption(f"Against it: {prose(suggestion['contrary_evidence'])}")
                if suggestion.get("next_level_gap"):
                    st.caption(f"For the next level: {prose(suggestion['next_level_gap'])}")
                for item in suggestion.get("learner_evidence", []):
                    st.caption(f"At minute {item.get('minute')}: “{item.get('quote', '')}”")
            # Faculty decision of 2026-09-23: an untouched domain starts at "not
            # assessable", not at what the AI proposed. Across thirteen real
            # proposals the model chose "not assessable" exactly never -- including
            # two encounters where it wrote in its own limits that the encounter
            # closed before the opportunity -- so starting at its score pushed a
            # reviewer towards scoring. Starting here pushes towards deciding: a
            # domain left alone cannot be confirmed without a written reason.
            default = saved_scores.get(domain, NOT_ASSESSABLE)
            value = st.selectbox("Your score", _CHOICES, index=_CHOICES.index(default),
                                 format_func=_label, key=_key(record, "score", domain))
            scores[domain] = value
            if value == NOT_ASSESSABLE:
                # When the record itself says the window never opened, the reason
                # is offered already written, in the record's words: the reviewer
                # can keep it, change it, or score the domain instead.
                offered = (" ".join(domain_check.get("facts", []))
                           if domain_check.get("suggestion") == "no_opportunity" else "")
                reasons[domain] = st.text_input(
                    "Why is it not assessable? (a zero is a demonstrated failure; this is not one)",
                    value=saved_reasons.get(domain, offered), key=_key(record, "reason", domain))
            if suggestion and proposed in _CHOICES and value != proposed:
                justifications[domain] = st.text_input(
                    f"Why you changed it from the proposed {_label(proposed)}",
                    value=saved_changes.get(domain, {}).get("justification", ""),
                    key=_key(record, "why", domain))
            st.divider()

    with st.container():
        events = _event_controls(record, case_id, proposed_events, saved_events, check)
    try:
        preview = compute_score(scores, events)
    except Exception:
        preview = None
    with st.container():
        if preview:
            st.markdown(f"**{headline(preview)}**")
            if not preview["coverage"]["complete"]:
                st.caption("A partial assessment keeps its events and their penalty but has no "
                           "total comparable with a complete episode.")
            # The shape of what is on screen, redrawn as the selectboxes move, so a
            # reviewer sees the profile they are about to save rather than the one
            # they saved last time.
            _live_shape(store, token, record, {"scores": scores}, proposal, training_year)
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


def _live_shape(store, token, record, pending, proposal, training_year=None):
    """The five domains as a shape, beside this resident's running average."""
    import rubric_progress
    import rubric_radar
    try:
        # This encounter is excluded: a profile compared against itself is not
        # a comparison.
        reviews = [review for review in store.progress(token, record.get("user_id"))
                   if review.get("attempt_id") != record["id"]]
    except AccountError:
        reviews = []
    summary = rubric_progress.aggregate(reviews)
    average = rubric_progress.average_series(summary, colour=rubric_radar.SERIES_COLOURS[1])
    import resident_profile
    render_rubric_shape(pending, proposal, average=average,
                        caption=rubric_progress.caption(summary),
                        badge=resident_profile.badge(store.accounts, token,
                                                     record.get("user_id"), training_year))


def _event_controls(record, case_id, proposed_events, saved_events, check=None):
    defined = evaluation_basis.resolve(record)["events"] if case_id else ()
    if not defined:
        return []
    # Whether the resident asked is the fact a reviewer needs in front of them
    # here, because it is exactly what the event no longer waits for.
    import history_review
    asked_topics = set(history_review.review(record, case_id)["named"])
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
        for row in event["information_on_asking"]:
            topic, tells = row
            state = "asked about" if topic in asked_topics else "**never asked about**"
            st.caption(f"Available on asking — {topic.replace('_', ' ')} ({tells}): {state}. "
                       "The patient answers for the whole encounter, so this was available "
                       "either way; not asking is part of the omission, not an excuse for it.")
        screen = ((check or {}).get("events") or {}).get(event["event_id"]) or {}
        against = screen.get("status") in ("contradicted", "excluded")
        if screen.get("facts"):
            label = {"contradicted": "The record contradicts this event",
                     "excluded": "A declared exclusion is established by the record",
                     "met": "Every condition the record can settle is met",
                     "reading": "The record is compatible; part of the trigger needs your reading"
                     }.get(screen.get("status"), "Record")
            st.caption(f"**{label}.** " + " ".join(screen["facts"]))
        if proposed and against:
            st.error("The AI proposes this event, but the record contradicts it. Confirming it "
                     "requires your written reason.")
        elif proposed:
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
        if state == "confirmed" and against:
            justification = st.text_input(
                "Why you confirm it although the record contradicts it",
                value=saved.get("justification", ""),
                key=_key(record, "eventagainst", event["event_id"]))
        elif state != "proposed" and not proposed:
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


def _radar_html(series, language, caption="", badge=None):
    """The radar, sized to its column, with the caption under it."""
    import rubric_radar
    chart = rubric_radar.svg(series, size=240, language=language, badge=badge)
    legend = "".join(
        f'<span class="mrs-radar-key"><i style="background:{item["colour"]}"></i>'
        f'{escape(str(item["label"]))}</span>'
        for item in rubric_radar.geometry(series, language=language)["series"] if item["label"])
    note = f'<p class="mrs-radar-note">{escape(caption)}</p>' if caption else ""
    return f"""
    <div class="mrs-radar">{chart}<div class="mrs-radar-legend">{legend}</div>{note}</div>
    <style>
      .mrs-radar {{ width: 100%; max-width: 420px; margin: .2rem 0 .6rem; }}
      .mrs-radar svg {{ display: block; width: 100%; height: auto; }}
      .mrs-radar-legend {{ display: flex; flex-wrap: wrap; gap: .9rem; font-size: .78rem;
                           color: {palette.MUTED}; margin-top: .1rem; }}
      .mrs-radar-key i {{ display: inline-block; width: .62rem; height: .62rem;
                          border-radius: 2px; margin-right: .32rem; }}
      .mrs-radar-note {{ font-size: .76rem; color: {palette.MUTED}; margin: .3rem 0 0; }}
    </style>
    """


def render_rubric_shape(review, proposal=None, *, language="en", average=None, caption="",
                        badge=None):
    """The one encounter's profile as a shape, beside its numbers."""
    import rubric_radar
    if review is None:
        return
    series = [rubric_radar.series_from_review(review, language=language)]
    if average:
        series.append(average)
    st.markdown(_radar_html(series, language, caption, badge), unsafe_allow_html=True)
    gaps = [domain for domain in DOMAIN_IDS
            if (review.get("scores") or {}).get(domain) in (None, NOT_ASSESSABLE)]
    if gaps:
        # Said in words as well as drawn, because an axis with no point is
        # quieter than a low one and it must not read as a zero.
        st.caption("Drawn as a gap rather than at the centre, because it is not a zero: "
                   + ", ".join(f"domain {domain[1:]}" for domain in gaps)
                   + (" was" if len(gaps) == 1 else " were") + " not assessable in this encounter.")


def render_rubric_profile(context, user_id=None, *, language="en", training_year=None):
    """A resident's confirmed assessments, taken together.

    Read from confirmed reviews only. A resident sees their own; staff see the
    resident they selected. Nothing here is a grade, and the page says so.
    """
    import rubric_progress
    import rubric_radar
    if not context:
        return None
    try:
        reviews = RubricStore(context["store"]).progress(context["token"], user_id)
    except AccountError as error:
        st.caption(str(error))
        return None
    summary = rubric_progress.aggregate(reviews)
    import resident_profile
    badge = resident_profile.badge(context["store"], context["token"], user_id, training_year)
    spanish = language == "es"
    st.markdown("**Management reasoning profile** (pilot rubric " + summary["rubric_version"] + ")")
    st.caption(rubric_progress.FRAMING[1 if spanish else 0])
    waiting = _awaiting_confirmation(context, user_id, reviews)
    if waiting:
        st.caption(f"{waiting} completed encounter(s) await a faculty member's confirmation and are "
                   "not included: a suggestion is not a result.")
    if not summary["encounters"]:
        st.caption("No encounter has a rubric assessment a faculty member has confirmed yet. "
                   "An encounter nobody has assessed is absent from this profile, not a zero.")
        _render_results(summary)
        return summary
    st.caption(f"Encounters included: {summary['encounters']} (confirmed, rubric "
               f"{summary['rubric_version']}).")
    for version, count in sorted(summary["set_apart"].items()):
        st.caption(f"{count} encounter(s) confirmed under rubric {version or 'without a version'} are "
                   "listed below and not averaged in: the two scales are not assumed to be the same.")
    latest = reviews[-1]
    series = [{**rubric_radar.series_from_review(latest, language=language),
               "label": "Latest encounter" if language != "es" else "Último encuentro"}]
    average = rubric_progress.average_series(summary, language, colour=rubric_radar.SERIES_COLOURS[1])
    if average:
        series.append(average)
    st.markdown(_radar_html(series, language, rubric_progress.caption(summary, language), badge),
                unsafe_allow_html=True)
    for row in rubric_progress.table(summary, language):
        st.markdown(f"**Domain {row['domain_id'][1:]} · {row['title']}** — {row['mean_label']}")
        st.caption(row["note"])
    if summary["mean_adjusted"] is not None:
        st.caption(f"Mean adjusted total {summary['mean_adjusted']}/{summary['maximum']} over "
                   f"{summary['complete_encounters']} encounter(s) where all five domains were "
                   f"assessable. Partial assessments keep their events but have no comparable total.")
    if summary["critical_events"]:
        st.caption(f"{summary['critical_events']} confirmed critical event(s) across these "
                   "encounters. A safety event is counted, never averaged into a domain.")
        for alert in summary["alerts"]:
            st.caption(f"⚠ {alert['event_id']} · confirmed {_when(alert['confirmed_at'])}")
    if summary["weakest"]:
        st.caption(f"Lowest mean: domain {summary['weakest'][1:]} · "
                   f"{DOMAINS[summary['weakest']]['title']}. This is where the shape is pulled "
                   "in, not a judgement about the resident.")
    _render_results(summary)
    return summary


def _when(value):
    from datetime import datetime, timezone
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OverflowError, OSError):
        return "date not recorded"


def _render_results(summary):
    """Every confirmed encounter behind the shape, with its date."""
    rows = summary.get("results") or []
    if not rows:
        return
    with st.expander(f"Individual results ({len(rows)})"):
        st.dataframe([{
            "Confirmed": _when(row["confirmed_at"]),
            "Challenge": row.get("challenge_id") or "",
            "Case": row.get("case_id") or "",
            **{f"D{domain[1:]}": ("N/A" if value == NOT_ASSESSABLE else value)
               for domain, value in row["scores"].items()},
            "Total": (f"{row['adjusted']}/15" if row["adjusted"] is not None
                      else f"partial {row['partial_subtotal']} ({row['assessed']}/5)"),
            "Alerts": ", ".join(row["critical_events"]),
            "Rubric": row["rubric_version"] + ("" if row["included"] else " (not averaged)"),
        } for row in rows], hide_index=True)


def _awaiting_confirmation(context, user_id, reviews):
    """Completed encounters of this resident with no confirmed rubric assessment."""
    try:
        attempts = context["store"].list_attempts(context["token"])
    except AccountError:
        return 0
    target = user_id or context["user"]["id"]
    confirmed_ids = {review.get("attempt_id") for review in reviews}
    return sum(1 for attempt in attempts
               if attempt.get("user_id") == target and attempt.get("status") == "completed"
               and not attempt.get("is_sandbox") and attempt.get("id") not in confirmed_ids)
