"""The resident's pages beside the encounter room (cycle 9, §154Q–§154AH, §154DW).

What do I need to do, how am I progressing, what evidence exists about my
performance, and what can I learn from my previous encounters. Simpler than
the faculty's pages, and read-only: a resident reads their own record through
the stores, which refuse anyone else's, and nothing here writes to it.

* **Home** says what is assigned, and nothing about it: a new clinical
  encounter and the day it was assigned. Which challenge, which case, why and
  by whom stay with the faculty (§154E).
* **My progress** keeps several kinds of evidence apart instead of reducing
  them to one score (§154S): the objective record, the management reasoning
  profile, the Decision Challenges, the Royal College EPAs, the ACGME
  subcompetencies and the confirmed safety events.
* **My encounters** lists what was completed and, for one encounter, puts the
  Management Trace first, as the primary evidence (§154AC).
* **My portfolio** holds the finalized documents (``portfolio``).
"""
import streamlit as st

from account_store import AccountError
from screen_language import rows as _rows, t as _t

PROGRESS_VIEWS = ("Overview", "Management reasoning", "Decision challenges", "Royal College EPAs",
                  "ACGME Milestones", "Safety")
ENCOUNTER_KEY = "_my_encounter"
PROFILE_NOTE = ("Your profile is based on faculty-confirmed observations from completed encounters. "
                "More observations make the profile more informative.")


def assigned_encounter(context):
    """The date a case was assigned to this resident, and nothing else about it (§154E)."""
    try:
        from encounter_directives import DirectiveStore
        return DirectiveStore(context["store"]).assigned(context["token"])
    except Exception:
        # No assignment can be read (a demonstration store, a database hiccup):
        # the page is the usual one, and the launch decides as it always has.
        return None


def _open_encounter(attempt_id):
    """From an observation or an event to its encounter and Management Trace (§154Y)."""
    st.session_state["_resident_dashboard_view"] = "My encounters"
    st.session_state[ENCOUNTER_KEY] = attempt_id


def _record(context):
    """The resident's own completed encounters, observations and confirmed reviews."""
    import resident_portal
    from progress_store import ProgressStore
    from rubric_store import RubricStore
    encounters = resident_portal.own_encounters(context)
    goals = ProgressStore(context["store"]).get_progress(context["token"])["objectives"]
    reviews = RubricStore(context["store"]).progress(context["token"])
    return encounters, goals, reviews


def _labels(encounters):
    from evidence_views import encounter_labels
    return encounter_labels(encounters)


def render_my_progress(context):
    import evidence_views
    import rubric_progress
    from progress_portal import render_progress_dashboard
    st.subheader(_t("My progress"))
    st.caption(_t("Several kinds of evidence, never one score. Everything here is read-only and comes from what "
                  "a faculty member observed and confirmed."))
    part = st.radio(_t("View"), PROGRESS_VIEWS, horizontal=True, format_func=_t, key="_my_progress_view")
    try:
        encounters, goals, reviews = _record(context)
    except AccountError as error:
        st.error(str(error))
        return
    labels = _labels(encounters)
    if part == "Overview":
        render_progress_dashboard(context, title="Objective record")
        evidence_views.render_limited(goals, rubric_progress.aggregate(reviews))
        import resident_portal
        with st.expander(_t("Your photograph and initials")):
            resident_portal.render_photo_and_initials(context, heading=False)
    elif part == "Management reasoning":
        # The same longitudinal profile faculty read, with the same methodology (§154T, §154M).
        import language
        from rubric_portal import render_rubric_profile
        st.caption(_t(PROFILE_NOTE))
        render_rubric_profile(context, None, language=language.current(),
                              training_year=context["user"].get("training_year"))
    elif part == "Decision challenges":
        evidence_views.render_challenges(goals, labels, on_open=_open_encounter, prefix="_mine")
    elif part == "Royal College EPAs":
        evidence_views.render_royal_college(goals, labels, on_open=_open_encounter, prefix="_mine")
    elif part == "ACGME Milestones":
        evidence_views.render_acgme(goals)
    else:
        evidence_views.render_safety(reviews, labels, on_open=_open_encounter, prefix="_mine")


def reviewed_attempts(goals, reviews):
    """The encounters a faculty member has reviewed: a confirmed rubric or a confirmed observation."""
    done = {review["attempt_id"] for review in reviews}
    for goal in goals:
        for item in goal.get("observations", []):
            if not item.get("voided"):
                done.add(item["attempt_id"])
    return done


def learning_focus_visible(context, attempt_id):
    """Whether this viewer may read an encounter's learning focus (§154AB, faculty 2026-09-29).

    Faculty and admins always. A resident once a faculty member has reviewed the
    encounter, by the same rule the resident's own pages publish by; before that,
    and whenever the review cannot be read, not. With no accounts there is nobody
    to keep it from.
    """
    if not context:
        return True
    if (context.get("user") or {}).get("role") in {"faculty", "admin"}:
        return True
    if not attempt_id:
        return False
    try:
        from progress_store import ProgressStore
        from rubric_store import RubricStore
        goals = ProgressStore(context["store"]).get_progress(context["token"])["objectives"]
        reviews = RubricStore(context["store"]).progress(context["token"])
    except AccountError:
        return False
    return attempt_id in reviewed_attempts(goals, reviews)


def encounter_rows(encounters, goals, reviews):
    """One row per completed encounter: review state and what was confirmed, never its target (§154AB)."""
    confirmed = {review["attempt_id"]: review for review in reviews}
    reviewed = reviewed_attempts(goals, reviews)
    observed = {}
    for goal in goals:
        for item in goal.get("observations", []):
            if not item.get("voided"):
                observed.setdefault(item["attempt_id"], []).append((goal, item))
    rows = []
    for record in encounters:
        review = confirmed.get(record["id"])
        found = observed.get(record["id"], [])
        rows.append({"record": record, "review": review, "observations": found,
                     "reviewed": record["id"] in reviewed})
    return rows


def render_my_encounters(context):
    import evidence_views
    import portfolio
    import resident_portal
    from evidence_views import day, moment
    st.subheader(_t("My encounters"))
    try:
        encounters, goals, reviews = _record(context)
    except AccountError as error:
        st.error(str(error))
        return
    if not encounters:
        st.info(_t("No completed encounter is saved yet. Your first one will appear here with its "
                   "Management Trace."))
        return
    rows = encounter_rows(encounters, goals, reviews)
    st.dataframe(_rows([{
        "Date": moment(row["record"]["created_at"]),
        "Clinical context": resident_portal._case_label(row["record"]),
        "Faculty review": _t("Reviewed") if row["reviewed"] else _t("Awaiting faculty review"),
        "Rubric": _t("Confirmed") if row["review"] else _t("Not confirmed yet"),
        "Confirmed observations": len(row["observations"]),
    } for row in rows]), hide_index=True)
    labels = _labels(encounters)
    if st.session_state.get(ENCOUNTER_KEY) not in labels:
        st.session_state[ENCOUNTER_KEY] = rows[0]["record"]["id"]
    # In the table's order, newest first.
    chosen = st.selectbox(_t("Encounter"), [row["record"]["id"] for row in rows], format_func=labels.get,
                          key=ENCOUNTER_KEY)
    row = next(item for item in rows if item["record"]["id"] == chosen)
    owner = portfolio.owner_of(context)
    # 1. The primary evidence first, never below a score (§154AC).
    st.markdown("**1 · " + _t("Management Trace") + "**")
    st.caption(_t("The primary record of what you decided and why. Read it before any score."))
    portfolio.render_encounter_documents(context, row["record"], owner, "mine")
    # 2. What a faculty member wrote for you. Faculty private notes are never shown here (§154AD).
    st.markdown("**" + _t("2 · Faculty feedback") + "**")
    notes = [(goal, item) for goal, item in row["observations"] if str(item.get("notes") or "").strip()]
    if notes:
        for goal, item in notes:
            st.caption(f"{goal['objective_id']} · " + str(item["notes"]))
    else:
        st.caption(_t("No faculty feedback on this encounter yet."))
    # 3. The rubric, once a faculty member confirmed it.
    st.markdown("**" + _t("3 · Management reasoning rubric") + "**")
    if row["review"]:
        from rubric import headline
        st.caption(headline(row["review"]["totals"]))
        st.caption(_t("Confirmed {v0} by {v1} (revision {v2}). Its document is with the Management Trace above.",
                      v0=day(row["review"].get("created_at")), v1=row["review"].get("reviewer") or "—",
                      v2=row["review"].get("sequence")))
    else:
        st.caption(_t("No confirmed rubric assessment yet."))
    # 4. What was observed and confirmed: shown after review, never before (§154F).
    st.markdown("**" + _t("4 · Confirmed observations") + "**")
    if row["observations"]:
        for goal, item in row["observations"]:
            verdict = _t("Satisfactory") if item.get("satisfactory") else _t("Needs improvement")
            st.caption(f"{goal['objective_id']} · {goal['title']} · " + verdict)
    else:
        st.caption(_t("No observation has been recorded for this encounter yet."))
    # 5. Confirmed safety events of this encounter, apart from the profile.
    st.markdown("**" + _t("5 · Safety events") + "**")
    events = evidence_views.safety_rows([row["review"]] if row["review"] else [])
    if events:
        for event in events:
            st.caption(f"⚠ {event['event_id']} · {event['event']}")
    else:
        st.caption(_t("No confirmed critical safety event in this encounter."))
    with st.expander(_t("What you said you would do differently")):
        resident_portal.render_adaptation_thread(context, encounters)


def render_my_portfolio(context):
    import portfolio
    import resident_portal
    portfolio.render_portfolio(context)
    with st.expander(_t("Download your complete record")):
        resident_portal.render_account_export(context)
