"""Streamlit orchestration; private encounter records never go to learner widgets."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import secrets

import streamlit as st

from account_store import AccountError
from curriculum import CHALLENGES, assign_challenge, evidence_summary
from encounter_generator import generate_encounter
from generation_progress import encounter_preparation
from scene_preparation import ScenePreparation
from progress_portal import render_progress_dashboard, render_attempt_assessment
from faculty_portal import render_faculty_analysis

RUNTIME_VERSION = "0.24.13"
PAYLOAD_VERSION = "mrs_attempt_v1"
SESSION_FIELDS = (
    "started", "selected_case", "state", "events", "history", "management_trace",
    "encounter_ended", "encounter_closed_trace", "encounter_closed_state", "encounter_closed_events",
    "encounter_closed_time_min", "review_prompts", "decision_review", "adaptation_plan",
    "adaptation_plan_user_edited", "review_completed", "review_stage", "active_review_index",
    "active_comparison_index", "review_autosave_revision", "expert_comparison_unlocked",
    "precomparison_decision_review", "expert_comparison_responses", "attempt_number",
    "carry_forward_plan", "prior_attempt_summary", "prior_attempt_record", "last_parse",
    "rng_counter", "pending_action", "pending_bundle", "pending_reasoning",
    "reasoning_gate_counter", "last_executed_action", "encounter_assignment",
)


def _secret(name, default=""):
    import os
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    from offline_cases import withhold
    return withhold(name, str(value or os.environ.get(name, default) or "").strip())


def _payload():
    result = {"schema_version": PAYLOAD_VERSION,
              "session": {key: deepcopy(st.session_state[key]) for key in SESSION_FIELDS if key in st.session_state}}
    result["evidence"] = evidence_summary(result)
    return result


def save_session(context, status=None):
    if not context or not st.session_state.get("_attempt_id"):
        return
    if st.session_state.get("_attempt_status") == "completed":
        return  # Finalized reviews are displayed read-only; the frozen evidence stays intact.
    payload = _payload()
    status = status or ("completed" if st.session_state.get("review_completed") else "active")
    digest = hashlib.sha256(json.dumps([payload, status], sort_keys=True).encode()).hexdigest()
    if digest == st.session_state.get("_saved_digest"):
        return
    try:
        revision = context["store"].save_attempt(
            context["token"], st.session_state["_attempt_id"], payload, status,
            expected_revision=st.session_state.get("_attempt_revision", 0),
        )
    except AccountError as exc:
        st.error(str(exc))
        st.info("Your current work remains in this browser session. Resolve the save problem before continuing. If another tab changed this attempt, reopen it from your dashboard.")
        if st.button("Retry save", key="retry_attempt_save"):
            st.rerun()
        if st.button("Discard this tab's unsaved changes and reopen dashboard", key="discard_unsaved_attempt"):
            st.session_state.clear()
            st.session_state["_account_token"] = context["token"]
            st.session_state["_account_user_id"] = context["user"]["id"]
            st.rerun()
        st.stop()
    st.session_state["_attempt_revision"] = revision
    st.session_state["_attempt_status"] = status
    st.session_state["_saved_digest"] = digest


def restore_attempt(context, record, reset_session):
    # Re-fetch through the authorization boundary, never trust a UI record.
    record = context["store"].get_attempt(context["token"], record["id"])
    if not record:
        raise AccountError("This encounter is unavailable.")
    if record["user_id"] != context["user"]["id"]:
        raise AccountError("You can resume only your own encounters.")
    payload = record.get("payload") or {}
    if payload and payload.get("schema_version") != PAYLOAD_VERSION:
        raise AccountError("This encounter was saved by an incompatible version.")
    reset_session()
    for key in list(st.session_state):
        if str(key).startswith(("decision_review__", "adaptation_plan__", "expert_comparison__")):
            del st.session_state[key]
    for key, value in (payload.get("session") or {}).items():
        if key in SESSION_FIELDS:
            st.session_state[key] = deepcopy(value)
    if not payload.get("session"):
        encounter = record["encounter"]
        st.session_state.state = deepcopy(encounter["state"])
        st.session_state.started = True
        st.session_state.events = [{"kind": "presentation", "text": encounter["presentation"], "time": 0}]
        st.session_state.encounter_assignment = encounter.get("assignment", {})
    st.session_state["_attempt_id"] = record["id"]
    st.session_state["_attempt_revision"] = record["revision"]
    st.session_state["_attempt_status"] = record["status"]
    if payload.get("session"):
        st.session_state["_saved_digest"] = hashlib.sha256(
            json.dumps([_payload(), record["status"]], sort_keys=True).encode()
        ).hexdigest()
    else:
        st.session_state.pop("_saved_digest", None)


def start_encounter(context, initial_state, reset_session, faculty_choice=None, adaptation_plan=None, prior_record=None):
    store, token, user = context["store"], context["token"], context["user"]
    attempts = store.list_attempts(token)
    own = [a for a in attempts if a["user_id"] == user["id"]]
    active = next((a for a in own if a["status"] == "active"), None)
    if active:
        restore_attempt(context, active, reset_session)
        return
    seed = secrets.randbelow(2**31)
    if user["role"] in {"faculty", "admin"}:
        if faculty_choice not in CHALLENGES:
            raise AccountError("Choose an implemented faculty challenge.")
        assignment = {"challenge_id": faculty_choice, "reason": "faculty_sandbox", "assignment_seed": seed}
    else:
        # What this resident has never been placed in, computed here and passed
        # in, so that curriculum.py keeps knowing nothing about the rubric. It
        # breaks a tie between candidates the curriculum already chose.
        import challenge_targeting
        assignment = assign_challenge(user["training_year"], own, seed,
                                      challenge_targeting.unmet(own, CHALLENGES))
    from offline_cases import launch_options
    generation, scene_key = launch_options(_secret("OPENAI_API_KEY"))
    with ScenePreparation(scene_key,
                          _secret("MRS_IMAGE_MODEL", "gpt-image-1.5"),
                          _secret("MRS_IMAGE_REVIEW_MODEL", "gpt-5-mini")) as scene:
        with encounter_preparation(st) as progress:
            encounter = generate_encounter(
                assignment["challenge_id"], initial_state,
                model=_secret("MRS_GENERATOR_MODEL", _secret("OPENAI_MODEL", "gpt-5-mini")), seed=seed,
                review_model=_secret("MRS_GENERATOR_REVIEW_MODEL") or None,
                progress=progress, on_case_compiled=scene.on_case_compiled, **generation,
            )
        st.session_state.pop("_case_generation_failure", None)
        encounter["assignment"] = assignment
        attempt_id = store.create_attempt(token, assignment["challenge_id"], encounter, user["role"] != "resident")
        record = store.get_attempt(token, attempt_id)
        restore_attempt(context, record, reset_session)
        st.session_state.attempt_number = 1 + sum(a["status"] == "completed" for a in own)
        st.session_state.carry_forward_plan = deepcopy(adaptation_plan or {})
        st.session_state.prior_attempt_record = deepcopy(prior_record)
        save_session(context)
        scene.adopt(st.session_state, st.session_state.state, attempt_id)


def _date(value):
    return datetime.fromtimestamp(float(value), tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def render_dashboard(context, initial_state, reset_session):
    user, store, token = context["user"], context["store"], context["token"]
    if user["role"] == "resident":
        view = st.sidebar.radio(
            "Navigation", ("Clinical encounters", "My progress"),
            key="_resident_dashboard_view",
        )
        if view == "My progress":
            # Render only the selected page. Hidden tabs/expanders would still
            # send objective labels and feedback with the encounter launch UI.
            render_progress_dashboard(context, title="My progress")
            _render_rubric_profile(context)
            _render_own_record(context)
            return
    attempts = store.list_attempts(token)
    own = [a for a in attempts if a["user_id"] == user["id"]]
    completed = [a for a in own if a["status"] == "completed" and not a["is_sandbox"]]
    faculty_choice = None
    if user["role"] == "resident":
        st.subheader("Your next clinical encounter")
        st.caption(f"Training year {user['training_year']} · {len(completed)} completed encounter reviews")
        st.write("Manage the patient, explain your reasoning, and reassess as the encounter evolves. Your learning focus will be discussed after the encounter.")
    else:
        st.subheader("Faculty sandbox")
        st.caption(f"These encounters are excluded from resident progress. {len(CHALLENGES)} challenges are available.")
        faculty_choice = st.selectbox("Management challenge", list(CHALLENGES), format_func=lambda key: key + " · " + CHALLENGES[key]["title"])
        with st.expander("Clinical and cognitive catalog"):
            st.dataframe([
                {"Code": key, "Learning focus": challenge["title"],
                 "Cognitive focus": challenge.get("bias_name", "Management reasoning"),
                 "Scenario": "New AI-authored clinical case",
                 "Competencies": challenge.get("acgme", "Management reasoning")}
                for key, challenge in CHALLENGES.items()
            ], hide_index=True)
            st.caption("These are formative teaching opportunities. The catalog does not diagnose a learner's cognitive bias or establish competence.")
    st.caption("You may enter your reasoning and orders in English or Spanish. Patient information and feedback are in English.")
    st.caption("Your encounter and reflection are saved to your account. Faculty in this pilot program can review them.")
    retained = st.session_state.get('_case_generation_failure')
    if retained and retained.get('owner') == user['id'] and not retained.get('report_id'):
        try:
            retained['report_id'] = store.save_generation_failure(token, retained['data'])
            st.caption('Support report: ' + retained['report_id'])
        except AccountError:
            st.warning('The support report could not be saved. The failure remains in this session.')
    if user['role'] == 'admin':
        with st.expander('Case preparation diagnostics'):
            if st.button('Load saved generation failures'):
                try:
                    reports = store.list_generation_failures(token)
                    if not reports:
                        st.info('No saved generation failures.')
                    for report in reports:
                        st.download_button('Download report ' + report['id'][:8],
                            json.dumps(report, ensure_ascii=False, indent=2),
                            file_name='case_preparation_' + report['id'] + '.json',
                            mime='application/json', key='failure_' + report['id'])
                except AccountError as error:
                    st.error(str(error))
    failure = st.session_state.get('_case_generation_failure')
    if user['role'] in {'faculty', 'admin'} and failure and failure.get('owner') == user['id']:
        st.download_button('Download case preparation diagnostic',
            json.dumps(failure['data'], ensure_ascii=False, indent=2),
            file_name='case_preparation_diagnostic.json', mime='application/json')
    active = next((a for a in own if a["status"] == "active"), None)
    if st.button("Resume encounter" if active else "Begin Encounter", type="primary"):
        from generated_case import GeneratedCaseError
        try:
            if active:
                restore_attempt(context, active, reset_session)
            else:
                start_encounter(context, initial_state, reset_session, faculty_choice)
        except (AccountError, GeneratedCaseError) as exc:
            diagnostic = getattr(exc, 'diagnostic', None)
            if diagnostic is not None:
                # A local copy as well: the database row is administrator-only and
                # an offline replay should not need database access.
                from generation_diagnostics import save_failure
                save_failure(exc, challenge_id=faculty_choice)
                # Private session storage only; never a learner widget or accepted attempt.
                st.session_state['_case_generation_failure'] = {'owner': user['id'], 'data': deepcopy(diagnostic)}
                try:
                    report_id = store.save_generation_failure(token, diagnostic)
                    st.session_state['_case_generation_failure']['report_id'] = report_id
                    st.caption('Support report: ' + report_id)
                except AccountError:
                    st.warning('The support report could not be saved. The failure remains in this session.')
            st.error(str(exc))
            st.stop()
        st.rerun()
    if completed:
        with st.expander("Previous completed reviews"):
            for i, attempt in enumerate(reversed(completed), 1):
                st.write(f"Encounter review · {_date(attempt['updated_at'])}")
                if st.button("Open review", key="resume_" + attempt["id"]):
                    restore_attempt(context, attempt, reset_session)
                    st.rerun()
    if user["role"] in {"faculty", "admin"}:
        requested = st.query_params.get("faculty_attempt", "")
        with st.expander("Resident activity and recorded evidence", expanded=bool(requested)):
            resident_attempts = [a for a in attempts if not a["is_sandbox"]]
            st.caption("Single-program pilot. These are activity records and evidence prompts for faculty review, not competency scores.")
            st.dataframe([{"Resident": a["username"], "Challenge": a["challenge_id"], "Status": a["status"], "Updated": _date(a["updated_at"])} for a in resident_attempts], hide_index=True)
            if resident_attempts:
                # A PDF link selects from the already authorized list; it never
                # fetches an arbitrary ID or bypasses the staff review gates.
                attempt_ids = [a["id"] for a in resident_attempts]
                selection_key = "_faculty_encounter_" + user["id"]
                link_key = selection_key + "_opened_link"
                if requested and requested != st.session_state.get(link_key):
                    if requested in attempt_ids:
                        st.session_state[selection_key] = requested
                    else:
                        st.info("The linked encounter is not available to this account. Select an available encounter below.")
                    st.session_state[link_key] = requested
                if st.session_state.get(selection_key) not in attempt_ids:
                    st.session_state[selection_key] = next(
                        (a["id"] for a in resident_attempts if a["status"] == "completed"), attempt_ids[0])
                selected = st.selectbox("Encounter record", attempt_ids, key=selection_key,
                    format_func=lambda key: next(a["username"] + " · " + a["challenge_id"] + " · " + a["status"] + " · " + _date(a["updated_at"]) for a in resident_attempts if a["id"] == key))
                record = store.get_attempt(token, selected)
                render_faculty_analysis(context, record)
                render_attempt_assessment(context, record)
                with st.expander("Complete encounter record and export"):
                    st.json((record.get("payload") or {}).get("evidence", {}), expanded=False)
                    st.download_button("Download faculty record", json.dumps(record, indent=2), file_name="faculty_encounter_record.json", mime="application/json")
        _render_rubric_profile(context, render_progress_dashboard(context))


def _render_own_record(context):
    """The resident's own encounters, plans and record, on their own page.

    Their work used to disappear the moment they finished it: the Management
    Trace was downloadable during the encounter and never again (2026-09-23).
    """
    import resident_portal
    with st.expander("Your photograph and initials"):
        resident_portal.render_photo_and_initials(context)
    encounters = resident_portal.render_my_encounters(context)
    with st.expander("What you said you would do differently"):
        resident_portal.render_adaptation_thread(context, encounters)
    with st.expander("Download your complete record"):
        resident_portal.render_account_export(context, encounters)


def _render_rubric_profile(context, user_id=None):
    """The rubric profile, beside the objective record and never inside it.

    Two instruments: an objective is observed behaviour a faculty member
    recorded against a curriculum, and the rubric is a score for one encounter.
    The page shows both; neither module imports the other, and neither number
    is computed from the other.
    """
    if not context:
        return
    with st.expander("Management reasoning rubric profile", expanded=False):
        st.caption("A pilot instrument. These are not ACGME Milestone levels, Canadian stages "
                   "or EPA supervision levels, and they neither feed nor replace the objective "
                   "record above. Only assessments a faculty member has confirmed appear here.")
        from rubric_portal import render_rubric_profile
        render_rubric_profile(context, user_id)


def render_learning_focus(context):
    if not st.session_state.get("encounter_ended"):
        return
    assignment = (st.session_state.get("encounter_assignment") or {}) if context else {}
    closed_state = st.session_state.get("encounter_closed_state") or {}
    state = st.session_state.get("state") or {}
    # The public frozen management snapshot deliberately omits the private
    # encounter spec. Shared sessions retain it in their server-side live state.
    spec = closed_state.get("encounter_spec") or state.get("encounter_spec") or {}
    challenge = CHALLENGES.get(assignment.get("challenge_id") or spec.get("challenge_id"))
    if challenge:
        with st.expander("Learning focus for this encounter", expanded=True):
            st.write(challenge["title"])
            if challenge.get("bias_name"):
                st.write("Cognitive focus: " + challenge["bias_name"])
            st.write(challenge["objective"])
            for question in challenge.get("debrief_questions", ()):
                st.write(question)
            st.caption("This local curriculum mapping supports formative faculty review. Completing a case does not establish competence.")


def return_to_dashboard(context, reset_session, abandon=False):
    save_session(context, "abandoned" if abandon and not st.session_state.get("review_completed") else None)
    reset_session()
    for key in ("_attempt_id", "_attempt_revision", "_attempt_status", "_saved_digest"):
        st.session_state.pop(key, None)
    st.rerun()
