"""The faculty's cohort: every resident as a card, grouped by training year (cycle 9, §154G–§154L).

Who are my residents, who needs my attention, what do I need to review. A card shows the
resident's photograph or initials, the training year, the D1–D5 shape of their
faculty-confirmed assessments and what waits for review; opening it shows that resident's
record on the same page. There is no overall score, no rank and no comparison with peers
(§154H, §154CM, §154EF): residents are listed by year and name, never by result.

Everything is read through the stores with the reader's own token, and the stores check the
role again. The page changes how the record is found, never what it holds (§154CO).
"""
from html import escape

import streamlit as st

from account_store import AccountError
from screen_language import t as _t

SELECTED = "_cohort_resident"
FILTERS = ("All", "R1", "R2", "R3", "Needs review")


def roster(context, attempts):
    """Each resident with what their card shows. An inactive account is labelled, never dropped."""
    import resident_profile
    import rubric_progress
    from progress_store import ProgressStore
    from rubric_store import RubricStore
    store, token = context["store"], context["token"]
    progress = ProgressStore(store)
    residents = progress.list_residents(token)
    try:
        pending = {item["attempt_id"]: item for item in progress.pending_reviews(token)}
    except AccountError:
        pending = {}
    rubric = RubricStore(store)
    people = []
    for person in residents:
        encounters = [a for a in attempts if a["user_id"] == person["id"] and not a["is_sandbox"]]
        completed = [a for a in encounters if a["status"] == "completed"]
        reviews = rubric.progress(token, person["id"])
        confirmed = {review["attempt_id"] for review in reviews}
        # An encounter waits while its rubric is unconfirmed or an objective still has no observation.
        awaiting = sum(1 for a in completed
                       if a["id"] not in confirmed or (pending.get(a["id"]) or {}).get("pending_objectives"))
        summary = rubric_progress.aggregate(reviews)
        people.append({**person, "completed": len(completed), "confirmed_reviews": len(confirmed),
                       "awaiting": awaiting, "summary": summary,
                       "critical_events": summary["critical_events"],
                       "badge": resident_profile.badge(store, token, person["id"], person.get("training_year"))})
    return people


def _initials(username):
    parts = [part for part in str(username).replace("_", ".").replace("-", ".").split(".") if part]
    letters = "".join(part[0] for part in parts[:2]) or str(username)[:2]
    return letters.upper()


def _chart(person, language, size):
    import rubric_progress
    import rubric_radar
    average = rubric_progress.average_series(person["summary"], language, colour=rubric_radar.SERIES_COLOURS[1])
    badge = person["badge"] or {"image": None, "initials": _initials(person["username"]),
                                "year": person.get("training_year")}
    return rubric_radar.svg([average] if average else [], size=size, language=language,
                            title=_t("D1–D5 profile of {v0}", v0=person["username"]), badge=badge)


def _status_line(person):
    parts = [_t("{v0} completed", v0=person["completed"]),
             _t("{v0} confirmed rubric reviews", v0=person["confirmed_reviews"])]
    line = " · ".join(parts)
    if person["awaiting"]:
        line += " · " + _t("⚑ {v0} awaiting review", v0=person["awaiting"])
    if not person.get("active", True):
        line += " · " + _t("inactive account")
    return line


def _visible(people, search, choice):
    shown = [p for p in people if not search or search.lower() in p["username"].lower()]
    if choice in ("R1", "R2", "R3"):
        shown = [p for p in shown if p.get("training_year") == int(choice[1])]
    elif choice == "Needs review":
        shown = [p for p in shown if p["awaiting"]]
    return shown


def render_cohort(context, attempts):
    """The cohort, or the one resident a card opened. Returns that resident's id, or None."""
    import language
    lang = language.current()
    try:
        people = roster(context, attempts)
    except AccountError as error:
        st.error(str(error))
        return None
    selected = st.session_state.get(SELECTED)
    if selected and selected in {p["id"] for p in people}:
        _render_resident_header(context, next(p for p in people if p["id"] == selected), lang)
        return selected
    st.session_state.pop(SELECTED, None)
    st.subheader(_t("Residents"))
    st.caption(_t("Faculty-confirmed evidence only. There is no overall score and no ranking: each card is one "
                  "resident's own record, in training-year and name order."))
    if not people:
        st.info(_t("No resident accounts are available yet."))
        return None
    left, right = st.columns([2, 3])
    search = left.text_input(_t("Search residents"), key="_cohort_search")
    choice = right.radio(_t("Show"), FILTERS, horizontal=True, format_func=_t, key="_cohort_filter")
    shown = _visible(people, search, choice)
    waiting = sum(p["awaiting"] for p in people)
    st.caption(_t("Needs your attention: {v0} completed encounter(s) awaiting review.", v0=waiting) if waiting
               else _t("No encounter is awaiting review."))
    if not shown:
        st.caption(_t("No resident matches this search."))
        return None
    for year in sorted({p.get("training_year") or 0 for p in shown}):
        group = sorted((p for p in shown if (p.get("training_year") or 0) == year), key=lambda p: p["username"])
        st.markdown("**" + (_t("R{v0}", v0=year) if year else _t("Training year not recorded")) + "**")
        for start in range(0, len(group), 3):
            columns = st.columns(3)
            for column, person in zip(columns, group[start:start + 3]):
                with column.container(border=True):
                    st.markdown(f'<div class="mrs-card-chart">{_chart(person, lang, 180)}</div>'
                                f'<p class="mrs-card-name">{escape(person["username"])}</p>'
                                f'<p class="mrs-card-status">{escape(_status_line(person))}</p>'
                                + _CARD_STYLE, unsafe_allow_html=True)
                    if st.button(_t("Open"), key="_cohort_open_" + person["id"]):
                        st.session_state[SELECTED] = person["id"]
                        # The objective record below follows the resident the card opened.
                        st.session_state["progress_resident"] = person["id"]
                        st.rerun()
    return None


def _render_resident_header(context, person, lang):
    """The top of one resident's record: identity, shape, and what the record holds (§154L)."""
    summary = person["summary"]
    left, right = st.columns([2, 3])
    with left:
        st.markdown(f'<div class="mrs-card-chart">{_chart(person, lang, 240)}</div>' + _CARD_STYLE,
                    unsafe_allow_html=True)
    with right:
        st.subheader(person["username"] + ("" if person.get("active", True) else _t(" (inactive)")))
        st.caption(_t("Training year {v0}", v0=person.get("training_year") or "—"))
        st.markdown(
            _t("Completed encounters: **{v0}** · Confirmed rubric reviews: **{v1}** · Awaiting review: **{v2}** · "
               "Confirmed critical safety events: **{v3}**", v0=person["completed"], v1=person["confirmed_reviews"],
               v2=person["awaiting"], v3=person["critical_events"]))
        domains = summary.get("domains") or {}
        if any(item["encounters"] for item in domains.values()):
            st.caption(_t("Faculty-confirmed encounters per domain: ") + " · ".join(
                f"D{domain[1:]} n={item['encounters']}" for domain, item in domains.items()))
        st.caption(_t("The shape is the mean of faculty-confirmed domain scores; a domain not assessable is left "
                      "out, never counted as zero. No overall score is shown."))
        if st.button(_t("Back to all residents"), key="_cohort_back"):
            st.session_state.pop(SELECTED, None)
            st.rerun()


_CARD_STYLE = """
<style>
  .mrs-card-chart svg { display: block; width: 100%; max-width: 240px; height: auto; margin: 0 auto; }
  .mrs-card-name { font-weight: 600; text-align: center; margin: .2rem 0 0; }
  .mrs-card-status { font-size: .8rem; text-align: center; margin: .1rem 0 .3rem; }
</style>
"""
