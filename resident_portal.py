"""The resident's own record: what they did, what it was worth, and what they said next.

Until 2026-09-23 a resident's work became invisible the moment they finished
it. The Management Trace could be downloaded during the encounter and never
again; a confirmed rubric assessment reached the faculty and not the person it
was about; the plan they wrote for next time was shown once, in the next
encounter, and nowhere as a thread.

Everything here is read through the stores, which already refuse one
resident's data to another: a resident sees their own encounters and nobody
else's. Nothing in this module widens that, and ``test_a_resident_sees_only
_their_own`` states it as a property rather than trusting it.

No paid call is made here. A Management Trace is re-rendered from the analysis
already saved for that encounter; when none was ever generated, the encounter
is listed and says so.
"""

import json
import time

import streamlit as st

from account_store import AccountError
from screen_language import t as _t


MAX_LISTED = 200


def _date(value):
    from datetime import datetime, timezone
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except (TypeError, ValueError, OverflowError, OSError):
        return "—"


def own_encounters(context):
    """This person's completed, non-sandbox encounters, newest first."""
    attempts = context["store"].list_attempts(context["token"])
    mine = [item for item in attempts
            if item["user_id"] == context["user"]["id"]
            and item["status"] == "completed" and not item["is_sandbox"]]
    return mine[:MAX_LISTED]


def _case_label(record):
    import language
    from faculty_analysis import case_id_of
    encounter = record.get("encounter") or {}
    if isinstance(encounter, dict):
        for key in ("case_label", "presentation"):
            value = str(encounter.get(key) or "").strip()
            if value:
                # The case's own words as the faculty approved them, before they are shortened.
                value = language.narrative(value, case=case_id_of(record))
                return value.split("\n")[0][:160]
    return _t("Clinical encounter")


def _trace_pdf(context, record, language=None, *, owner=None, translate=None):
    """The learner's own document, re-rendered from the analysis already saved.

    Rendered against the frozen evidence the analysis was written from and saved
    against (``analysis_payload_from_session``), as the encounter's own page does.
    Until 2026-09-26 it was handed the whole saved record, which that check
    refuses, so "My progress" said no reading was saved beside a valid one.

    ``owner`` is the resident the document is about, when a faculty member opens
    it from that resident's portfolio: the same document, never a second
    version for staff (cycle 9, §154AH).
    """
    from management_trace_store import ManagementTraceStore, analysis_payload_from_session
    from management_trace_report import render_management_trace_pdf
    import prose_translation
    owner = owner or context["user"]
    store = ManagementTraceStore(context["store"])
    report = store.get_latest(context["token"], record["id"])
    if report is None:
        return None
    session = (record.get("payload") or {}).get("session") or {}
    return render_management_trace_pdf(
        report, analysis_payload_from_session(session), case_label=_case_label(record),
        learner_label=str(owner["username"]),
        review_completed=bool(session.get("review_completed")),
        adaptation_plan=session.get("adaptation_plan"), language=language,
        translate=translate or prose_translation.translator(context))


def _rubric_pdf(context, record, language="en", *, owner=None, translate=None):
    """The confirmed assessment, as the document, or None while it is a draft."""
    from rubric_report import RubricReportError, render_rubric_report_pdf
    from rubric_store import RubricStore
    import resident_profile
    owner = owner or context["user"]
    review, proposal = RubricStore(context["store"]).released(context["token"], record["id"])
    if review is None:
        return None, None
    badge = resident_profile.badge(context["store"], context["token"],
                                   owner["id"], owner.get("training_year"))
    try:
        import prose_translation
        return render_rubric_report_pdf(review, proposal, record, audience="learner",
                                        badge=badge, language=language,
                                        translate=translate or prose_translation.translator(context)), review
    except (RubricReportError, ValueError):
        return None, review


def adaptation_thread(context, encounters=None):
    """What this person said they would do differently, oldest first.

    Paired with the encounter that came after it, because a plan is only worth
    reading beside what happened next.
    """
    records = list(encounters if encounters is not None else own_encounters(context))
    records.sort(key=lambda item: item["updated_at"])
    rows = []
    for index, record in enumerate(records):
        session = (record.get("payload") or {}).get("session") or {}
        plan = session.get("adaptation_plan")
        plan = plan if isinstance(plan, dict) else {}
        stated = {key: str(value).strip() for key, value in plan.items()
                  if isinstance(value, str) and str(value).strip()}
        if not stated:
            continue
        following = records[index + 1] if index + 1 < len(records) else None
        rows.append({
            "attempt_id": record["id"], "when": _date(record["updated_at"]),
            "challenge_id": record["challenge_id"], "plan": stated,
            "next_attempt_id": following["id"] if following else None,
            "next_when": _date(following["updated_at"]) if following else "",
            "next_challenge": following["challenge_id"] if following else "",
        })
    return rows


def render_adaptation_thread(context, encounters=None):
    """The thread, in one place, which is where it has never been."""
    try:
        rows = adaptation_thread(context, encounters)
    except AccountError as error:
        st.caption(str(error))
        return []
    st.markdown("**" + _t('What you said you would do differently') + "**")
    if not rows:
        st.caption(_t("Nothing yet. Each encounter ends by asking what you would carry into the "
                   "next one, and those answers collect here."))
        return rows
    st.caption(_t("Written after each encounter, in your own words, and set beside the encounter "
               "that followed it. Nothing here is scored."))
    for row in rows:
        # The date, not the challenge: an encounter's target is not named before
        # a faculty member has reviewed it (cycle 9, §154AB).
        st.markdown(f"**{row['when']}**")
        for field, value in row["plan"].items():
            st.markdown(f"> {value}")
        if row["next_attempt_id"]:
            st.caption(_t("Next encounter: {when}", when=row['next_when']))
        else:
            st.caption(_t("This is your most recent encounter; the next one is still ahead."))
    return rows


def account_export(context, encounters=None):
    """Everything of this person's, in one structure, for the end of a programme.

    Their encounters, their reflections, their confirmed assessments and their
    profile. Not a certificate and not a transcript: a copy of their own record,
    which the programme's declared goal is that they leave holding.
    """
    import rubric_progress
    from rubric_store import RubricStore
    user = context["user"]
    records = list(encounters if encounters is not None else own_encounters(context))
    records.sort(key=lambda item: item["updated_at"])
    store = RubricStore(context["store"])
    reviews = store.progress(context["token"], user["id"])
    summary = rubric_progress.aggregate(reviews)
    by_attempt = {row.get("attempt_id"): row for row in reviews}
    # An encounter's target travels in the copy once a faculty member has reviewed
    # it, as it reads on the page (§154AB, 2026-09-29).
    import resident_pages
    from progress_store import ProgressStore
    try:
        goals = ProgressStore(context["store"]).get_progress(context["token"])["objectives"]
    except AccountError:
        goals = []
    reviewed = resident_pages.reviewed_attempts(goals, reviews)
    import resident_profile
    try:
        profile = resident_profile.ProfileStore(context["store"]).get(context["token"])
    except AccountError:
        profile = {"initials": "", "photo": ""}
    return {
        "schema": "mrs_resident_record_v1",
        "exported_at": _date(time.time()),
        "resident": {"username": user["username"], "training_year": user.get("training_year"),
                     "initials": profile["initials"],
                     # Their own photograph, in their own copy of their own
                     # record. It is theirs to keep or to delete.
                     "photograph": resident_profile.data_uri(profile["photo"])},
        "encounters": [{
            "attempt_id": record["id"],
            "completed_at": _date(record["updated_at"]),
            "challenge_id": record["challenge_id"] if record["id"] in reviewed else None,
            "case": _case_label(record),
            "management_trace": ((record.get("payload") or {}).get("session") or {})
                                .get("management_trace", []),
            "your_reflection": ((record.get("payload") or {}).get("session") or {})
                               .get("precomparison_decision_review", {}),
            "your_adaptation_plan": ((record.get("payload") or {}).get("session") or {})
                                    .get("adaptation_plan", {}),
            "confirmed_rubric": _exported_review(by_attempt.get(record["id"])),
        } for record in records],
        "rubric_profile": {
            "encounters_assessed": summary["encounters"],
            "mean_adjusted_total": summary["mean_adjusted"],
            "maximum": summary["maximum"],
            "confirmed_critical_events": summary["critical_events"],
            "per_domain": {domain: {"mean": row["mean"], "encounters": row["encounters"],
                                    "scores": row["values"]}
                           for domain, row in summary["domains"].items()},
            "rubric_versions": summary["rubric_versions"],
        },
        "notice": ("A copy of your own record from a pilot simulator. It is not a "
                   "certificate, a transcript, or evidence that a workplace EPA was "
                   "achieved. The rubric is a pilot instrument and its scores are not ACGME "
                   "Milestone levels, Canadian stages or EPA supervision levels."),
    }


def _exported_review(review):
    if not review:
        return None
    return {"scores": review.get("scores", {}), "reasons": review.get("reasons", {}),
            "critical_events": review.get("critical_events", []),
            "totals": review.get("totals", {}),
            "rubric_version": review.get("rubric_version", ""),
            "reviewed_by": review.get("reviewer", ""),
            "confirmed_at": _date(review.get("created_at"))}


def render_account_export(context, encounters=None):
    """One button, and what it will and will not contain."""
    st.markdown("**" + _t('Your complete record') + "**")
    st.caption(_t("Everything saved under your account: your encounters, your own reflections and "
               "plans, and every rubric assessment a faculty member has confirmed. It is a copy "
               "of your record, not a certificate."))
    try:
        bundle = account_export(context, encounters)
    except AccountError as error:
        st.caption(str(error))
        return
    st.download_button(
        _t("Download your complete record (JSON)"),
        json.dumps(bundle, ensure_ascii=False, indent=2, default=str),
        file_name=f"mrs_record_{context['user']['username']}.json",
        mime="application/json", key="_resident_account_export")
    st.caption(_t("{count} encounter(s) · {assessed} with a confirmed assessment.", count=len(bundle['encounters']),
                  assessed=bundle['rubric_profile']['encounters_assessed']))


def render_photo_and_initials(context, *, heading=True):
    """Accept the agreement, then store a face and initials. Or remove them.

    Nothing is stored before the agreement is accepted, which is why the
    controls only appear after it. Removing is one button and asks for no
    reason (faculty decision, 2026-09-23).
    """
    import resident_profile
    store = resident_profile.ProfileStore(context["store"])
    try:
        accepted = store.accepted(context["token"])
        profile = store.get(context["token"])
    except AccountError as error:
        st.caption(str(error))
        return

    if heading:
        st.markdown("**" + _t('Your photograph and initials') + "**")
    st.caption(_t("Shown in one place: the centre of your profile chart, and on the assessment "
               "documents that carry it. You and faculty of this programme can see it. "
               "No other resident can see your photograph, your chart or anything else of yours."))

    if not accepted:
        with st.expander(_t("Read the agreement"), expanded=True):
            st.markdown(resident_profile.AGREEMENT)
        if st.button(_t("I have read this and agree"), key="_resident_photo_agree"):
            try:
                store.accept(context["token"])
            except AccountError as error:
                st.error(str(error))
            else:
                st.rerun()
        return

    with st.expander(_t("The agreement you accepted")):
        st.markdown(resident_profile.AGREEMENT)
        st.caption(_t("Accepted {date} · version {version}", date=_date(accepted),
                      version=resident_profile.AGREEMENT_VERSION))

    if profile["photo"]:
        st.image(resident_profile.data_uri(profile["photo"]), width=128)
    st.caption(_t("Current initials:") + " " + (profile["initials"] or _t("none stored")))

    with st.form("resident_photo", clear_on_submit=False):
        initials = st.text_input(_t("Your initials"), value=profile["initials"],
                                 max_chars=resident_profile.MAX_INITIALS * 4)
        upload = st.file_uploader(_t("A photograph of your face"),
                                  type=["png", "jpg", "jpeg", "webp"])
        st.caption(_t("The file is re-encoded as a small square image before it is stored. "
                   "Nothing of the original is kept, including where and when it was taken."))
        saved = st.form_submit_button(_t("Save"))
    if saved:
        try:
            store.save(context["token"], initials=initials,
                       photo=upload.getvalue() if upload is not None else None)
        except AccountError as error:
            st.error(str(error))
        else:
            st.success(_t("Saved."))
            st.rerun()

    if (profile["photo"] or profile["initials"]) and st.button(
            _t("Delete my photograph and initials"), key="_resident_photo_forget"):
        try:
            store.forget(context["token"])
        except AccountError as error:
            st.error(str(error))
        else:
            st.success(_t("Deleted."))
            st.rerun()


def needs_setup(context):
    """Whether this person has still to be asked about the photograph.

    Asked once, at the start, rather than buried in a page they may never
    open. Once they have decided either way, never again for that version of
    the agreement (faculty, 2026-09-23).
    """
    import resident_profile
    if context["user"]["role"] != "resident":
        return False
    try:
        return resident_profile.ProfileStore(context["store"]).decision(context["token"]) is None
    except AccountError:
        return False


def render_setup(context):
    """The first thing a new resident sees, before any encounter.

    It is a step, not a toll. The agreement says that withdrawing the
    photograph does not affect their standing in the programme, and a wall
    that stopped them training until they agreed would contradict that and
    make the consent worthless. So "Not now" is a real answer, recorded, and
    the controls stay available afterwards under My progress.
    """
    import resident_profile
    store = resident_profile.ProfileStore(context["store"])
    st.subheader(_t("Set up your account"))
    st.caption(_t("One step, once. Everything else about your account is already ready."))

    st.markdown("**" + _t('Your photograph and initials') + "**")
    st.caption(_t("Encounters in this programme are reviewed at a distance. A face beside your "
               "initials and your training year helps a faculty member keep one encounter "
               "apart from another. It appears in one place: the centre of your profile "
               "chart. No other resident can see it."))
    with st.expander(_t("Read the agreement"), expanded=True):
        st.markdown(resident_profile.AGREEMENT)

    columns = st.columns(2)
    if columns[0].button(_t("I have read this and agree"), type="primary", key="_setup_agree"):
        try:
            store.accept(context["token"])
        except AccountError as error:
            st.error(str(error))
        else:
            st.rerun()
    if columns[1].button(_t("Not now"), key="_setup_decline"):
        try:
            store.decline(context["token"])
        except AccountError as error:
            st.error(str(error))
        else:
            st.rerun()
    st.caption(_t("Choosing 'Not now' changes nothing else: you can begin encounters immediately, "
               "and you can add a photograph later from My progress, or never."))


def needs_photo_step(context):
    """Just agreed, nothing stored yet, and has not said "later" in this visit."""
    import resident_profile
    if context["user"]["role"] != "resident" or st.session_state.get("_resident_setup_done"):
        return False
    store = resident_profile.ProfileStore(context["store"])
    try:
        if store.decision(context["token"]) != "accepted":
            return False
        profile = store.get(context["token"])
    except AccountError:
        return False
    return not (profile["photo"] or profile["initials"])


def render_setup_photo(context):
    """Right after agreeing: the photograph itself, and a way past it."""
    st.subheader(_t("Set up your account"))
    st.caption(_t("Thank you. One last optional step, and you are ready to begin."))
    render_photo_and_initials(context)
    if st.button(_t("Continue to my encounters"), type="primary", key="_setup_continue"):
        st.session_state["_resident_setup_done"] = True
        st.rerun()
    st.caption(_t("You can also do this later, or not at all."))
