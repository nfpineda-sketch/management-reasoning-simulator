"""P3-281 to P3-287: the FACULTY-ONLY page surfaces of the controlled faculty development review (draws; decides nothing).

THREE SURFACES, each reachable only in a process that named the review mode and only by a faculty or administrator account:

* ``gate``       -- the first thing the page asks. Not a faculty account, or any piece of the configuration missing: an operational notice and the page stops. The reviewer account gets the reasons;
                    anybody else gets a plain "not available to this account" (no configuration names).
* ``launcher``   -- replaces the account dashboard: the seven scripted review encounters (two allowlisted GI cases) and nothing else. No other case can be started from the review environment.
* ``panel``      -- drawn inside the staff tools, i.e. BESIDE the encounter and never inside the resident-facing views: the operational status, the halt experience, the review bundle and the
                    staged feedback form. It is a different surface from the simulated resident's view and carries the authority vocabulary the resident view must never carry.

Nothing here imports anything of the Phase-3 layer, the engine, the shadow bridge or the common core: the page hands it the review layer (obtained through ``runtime_authority.faculty_review_layer``,
the page's one crossing) and it only draws what that layer returns.
"""
from __future__ import annotations

from typing import Any, Callable

CHALLENGE_ID = "R2-05"
BANNER = ("FACULTY DEVELOPMENT REVIEW · controlled, faculty-only, single-process development environment · GI pressure development authority only (two synthetic cases). "
          "Not a resident pilot, not production, not a clinical validation.")
TONE_BANNER = ("FACULTY DEVELOPMENT REVIEW · controlled, faculty-only development environment · stored development trajectories of synthetic cases and one synthetic probe. "
               "Not a resident pilot, not production, not a clinical validation.")
TITRATION_BANNER = ("FACULTY DEVELOPMENT REVIEW · controlled, faculty-only development environment · stored development trajectories of one synthetic case. "
                    "Not a resident pilot, not production, not a clinical validation.")
MANAGEMENT_BANNER = ("FACULTY DEVELOPMENT REVIEW · controlled, faculty-only development environment · stored development management paths of one synthetic case, each with its management trace. "
                     "Not a resident pilot, not production, not a clinical validation.")
GENERIC_REFUSAL = "This is a faculty development review environment. It is not available to this account."
BUNDLE_KEY = "phase3_faculty_review_bundle"
REVEALED_KEY = "phase3_faculty_review_revealed"
SCENARIO_FIELD = "faculty_review_scenario"
TRAJECTORY_MODE = "Trajectory review (first review)"
REREVIEW_MODE = "Trajectory re-review"
TONE_MODE = "Norepinephrine review (vascular tone)"
TITRATION_MODE = "Norepinephrine titration review"
MANAGEMENT_MODE = "Management trace review (GI paths)"
HELD_NOTE = "The other review modes open when this re-review is complete."
TONE_HELD_NOTE = "The other review modes open when this review is complete."
TITRATION_HELD_NOTE = "The other review modes open when this review is complete."
MANAGEMENT_HELD_NOTE = "The other review modes open when this review is complete."
LIVE_MODE = "Live review encounter (advanced)"
MODE_KEY = "faculty_review_mode"
MODE_CHOICE_KEY = "faculty_review_mode_choice"       # a plain session key: a widget that is not drawn while an encounter is on screen loses its state, the choice must not


def _on_cloud() -> bool:
    try:
        from account_portal import _on_streamlit_cloud
        return bool(_on_streamlit_cloud())
    except Exception:
        return True            # cannot tell: Streamlit Community Cloud is refused, so an unreadable answer is a refusal


def gate(st: Any, layer: Any, account_context: Any, accounts: bool) -> dict:
    """Evaluate the review mode for this session and publish the decision. Stops the page unless this is a complete configuration AND a faculty or administrator account."""
    review = layer.review
    role = ((account_context or {}).get("user") or {}).get("role")
    decision = review.evaluate(accounts=bool(accounts), role=role, on_cloud=_on_cloud())
    review.publish(st.session_state, decision)
    if not decision.get("requested") or decision.get("enabled"):
        return decision
    st.title("Faculty development review")
    st.error("FACULTY DEVELOPMENT REVIEW UNAVAILABLE")
    if role in review.FACULTY_ROLES:
        st.write("The authority is unavailable and no review encounter can start: the faculty review configuration is incomplete or not allowed.")
        for problem in decision.get("problems") or ():
            st.write("• " + str(problem))
    else:
        st.write(GENERIC_REFUSAL)
    st.stop()
    return decision


def launcher(st: Any, layer: Any, context: Any, initial_state: Any, reset_session: Callable, start_encounter: Callable, trajectory_page: Callable | None = None, rereview_page: Callable | None = None,
             default_mode: str | None = None, hold_prior_modes: Callable | None = None, tone_page: Callable | None = None, hold_other_modes: Callable | None = None,
             titration_page: Callable | None = None, hold_titration: Callable | None = None, management_page: Callable | None = None, hold_management: Callable | None = None) -> None:
    """The review launcher: the scripted encounters, nothing else. Draws and stops the page when nothing has started."""
    review = layer.review
    st.title("Faculty development review")
    # UX-001..013: the primary workflow is the TRAJECTORY REVIEW (stored certified trajectories, one page per scenario). The page itself is HANDED IN by the caller (this module imports nothing of it, as it
    # imports nothing of the Phase-3 layer). The live review encounter below stays unchanged and available. Without a handed-in page there is only the live launcher, as before.
    # The blind RE-REVIEW of the joint-region candidate (P3-352) is a second trajectory page, handed in the same way: the same review, a different stored set, and the first review's page and records untouched.
    if trajectory_page is not None and rereview_page is not None and hold_prior_modes is not None:
        # FD-REREVIEW-21: while the blind re-review is incomplete, THIS launcher offers nothing but the re-review: not the first review (it draws the earlier trajectories and judgments) and not the live review
        # encounter. It is a temporary hold on this launcher, not a product switch: the data of the earlier modes is untouched and they return when the re-review is complete. Whatever cannot be decided is held.
        try:
            held = bool(hold_prior_modes(st, layer, context))
        except Exception:
            held = True
        if held:
            st.session_state[MODE_CHOICE_KEY] = REREVIEW_MODE            # a forged or stale choice of another mode is overwritten, and the radio is not drawn at all
            st.session_state.pop(MODE_KEY, None)
            st.warning(BANNER)
            st.caption(HELD_NOTE)
            rereview_page(st, layer, context)
            return
    if trajectory_page is not None and tone_page is not None and hold_other_modes is not None:
        # The same hold for the multifamily TONE review (P3-406): while this reviewer has not completed it, THIS launcher offers nothing but it. The first review, the re-review and the live encounter draw earlier
        # trajectories, the legacy comparator, heart rate and capillary refill and the reviewer's earlier judgments, and none of that may be reachable from a blind first pass. A temporary hold on this launcher, not a
        # product switch: the data of the other modes is untouched and they return when the five scenarios are submitted. Whatever cannot be decided is held.
        try:
            held_tone = bool(hold_other_modes(st, layer, context))
        except Exception:
            held_tone = True
        if held_tone:
            st.session_state[MODE_CHOICE_KEY] = TONE_MODE
            st.session_state.pop(MODE_KEY, None)
            st.warning(TONE_BANNER)
            st.caption(TONE_HELD_NOTE)
            tone_page(st, layer, context)
            return
    if trajectory_page is not None and titration_page is not None and hold_titration is not None:
        # The same hold for the norepinephrine TITRATION review (P3-441): while this reviewer has not completed it, THIS launcher offers nothing but it. The first review, the re-review, the tone review and the live
        # encounter draw earlier trajectories, the legacy comparator, heart rate and capillary refill and the reviewer's earlier judgments, and none of that may be reachable from a blind first pass. A temporary hold on
        # this launcher, not a product switch: the data of the other modes is untouched and they return when the five scenarios are submitted. Whatever cannot be decided is held. It comes AFTER the other two holds:
        # a reviewer whose re-review or tone review is still pending is shown that one first, exactly as before.
        try:
            held_titration = bool(hold_titration(st, layer, context))
        except Exception:
            held_titration = True
        if held_titration:
            st.session_state[MODE_CHOICE_KEY] = TITRATION_MODE
            st.session_state.pop(MODE_KEY, None)
            st.warning(TITRATION_BANNER)
            st.caption(TITRATION_HELD_NOTE)
            titration_page(st, layer, context)
            return
    if trajectory_page is not None and management_page is not None and hold_management is not None:
        # The same hold for the GI MANAGEMENT-TRACE review (P3-514): while this reviewer has not completed it, THIS launcher offers nothing but it (the other modes draw earlier trajectories, the legacy comparator
        # and the reviewer's earlier judgments). A temporary hold on this launcher, not a product switch: the data of the other modes is untouched and they return when the ten paths are submitted. Whatever cannot
        # be decided is held. It comes AFTER the other holds: a reviewer whose earlier review is still pending is shown that one first, exactly as before.
        try:
            held_management = bool(hold_management(st, layer, context))
        except Exception:
            held_management = True
        if held_management:
            st.session_state[MODE_CHOICE_KEY] = MANAGEMENT_MODE
            st.session_state.pop(MODE_KEY, None)
            st.warning(MANAGEMENT_BANNER)
            st.caption(MANAGEMENT_HELD_NOTE)
            management_page(st, layer, context)
            return
    if trajectory_page is not None:
        # The multifamily TONE review (norepinephrine / vascular tone, five scenarios) is a third trajectory page, handed in the same way: the same review on another stored set, the other pages and their records untouched.
        modes = [TRAJECTORY_MODE] + ([REREVIEW_MODE] if rereview_page is not None else []) + ([TONE_MODE] if tone_page is not None else []) + ([TITRATION_MODE] if titration_page is not None else []) + ([MANAGEMENT_MODE] if management_page is not None else []) + [LIVE_MODE]
        # ``default_mode`` is the page a reviewer lands on before choosing anything. The app names the tone review (P3-406); while the re-review is pending the hold above shows it instead (the earlier review's page draws
        # the earlier trajectories or the reviewer's earlier judgments, and nothing of them may be on screen before a blind first pass). Left out, the default is what it always was.
        landing = default_mode if default_mode in modes else TRAJECTORY_MODE
        # The banner names the environment. The tone review (stored trajectories of synthetic cases and one probe) says what IT is, not the live GI authority's scope; the mode in force is the radio's value (set by the
        # browser before this run), else the choice remembered, else the landing page.
        in_force = next((value for value in (st.session_state.get(MODE_KEY), st.session_state.get(MODE_CHOICE_KEY)) if value in modes), landing)
        st.warning(TONE_BANNER if in_force == TONE_MODE and tone_page is not None else TITRATION_BANNER if in_force == TITRATION_MODE and titration_page is not None
                   else MANAGEMENT_BANNER if in_force == MANAGEMENT_MODE and management_page is not None else BANNER)
        with st.expander("Review mode", expanded=False):
            mode = st.radio("Review mode", modes, index=modes.index(st.session_state.get(MODE_CHOICE_KEY, landing)) if st.session_state.get(MODE_CHOICE_KEY) in modes else modes.index(landing),
                            horizontal=True, key=MODE_KEY, label_visibility="collapsed")
        st.session_state[MODE_CHOICE_KEY] = mode
        if mode == TRAJECTORY_MODE:
            trajectory_page(st, layer, context)
            return
        if mode == REREVIEW_MODE and rereview_page is not None:
            rereview_page(st, layer, context)
            return
        if mode == TONE_MODE and tone_page is not None:
            tone_page(st, layer, context)
            return
        if mode == TITRATION_MODE and titration_page is not None:
            titration_page(st, layer, context)
            return
        if mode == MANAGEMENT_MODE and management_page is not None:
            management_page(st, layer, context)
            return
    if trajectory_page is None:
        st.warning(BANNER)
    # No encounter is on screen while the launcher is drawn, so nothing of an earlier encounter's review (its bundle, its reveal) may survive into the next one (P3-288 review, B1).
    for key in (BUNDLE_KEY, REVEALED_KEY):
        st.session_state.pop(key, None)
    unfinished = _unfinished_attempt(context)
    if unfinished is not None:
        # FD-FAC-08: the review environment never resumes an encounter. An unfinished attempt (a refreshed page, another case, an earlier normal attempt) would otherwise be restored in silence
        # by ``start_encounter`` -- possibly the wrong scenario, possibly a case outside the allowlist, and without its authority site. It is abandoned on purpose, never resumed.
        if not unfinished.get("id"):
            st.error("The attempts of this account cannot be read, so the review cannot tell whether an encounter is unfinished: no review encounter starts.")
            return
        st.error("UNFINISHED ATTEMPT · The review environment does not resume encounters: abandon the unfinished attempt to start a review encounter.")
        st.caption(f"Challenge {unfinished.get('challenge_id')} · started {unfinished.get('created_at')}")
        if st.button("Abandon the unfinished attempt", key="faculty_review_abandon_unfinished"):
            try:
                context["store"].save_attempt(context["token"], unfinished["id"], unfinished["payload"], status="abandoned")
            except Exception as error:
                st.error(f"The unfinished attempt could not be abandoned ({type(error).__name__}): no review encounter starts.")
                return
            st.rerun()
        return
    options = {item["id"]: f"{item['id']} · {item['title']} ({item['case_id']})" for item in review.SCENARIOS}
    choice = st.selectbox("Review encounter", list(options), format_func=options.get, key="faculty_review_scenario_choice")
    scenario = review.scenario(choice)
    st.caption(f"Why this encounter: {scenario['reason']}")
    with st.expander("Suggested management script (so every reviewer sees the same encounter)", expanded=False):
        for index, (kind, text) in enumerate(scenario["steps"], 1):
            st.write(f"{index}. " + (text if text else ("Ask the patient a question" if kind == "question" else "Examine the patient")))
        st.caption("Type or click each step in the encounter, in this order. A different course is welcome; the script exists so the review set is reproducible.")
    if st.button("Begin review encounter", type="primary", key="faculty_review_begin"):
        try:
            start_encounter(context, initial_state, reset_session, faculty_choice=CHALLENGE_ID, pinned_variant=scenario["case_id"], review_scenario=scenario["id"])
        except Exception as error:                                  # AccountError among them: the start refused, nothing started
            st.error(f"The review encounter could not start: {error}")
            return
        if not review.case_allowed(review.case_of_state(st.session_state.get("state"))):
            reset_session()                                        # defensive: whatever started is not one of the two allowlisted cases
            st.error("The review environment only runs the two allowlisted GI cases.")
            return
        st.rerun()


def _unfinished_attempt(context: Any) -> dict | None:
    """This account's own active attempt, or None. Never raises: an unreadable store is read as 'an attempt may exist' (the launcher then refuses to start)."""
    try:
        store, token, user = context["store"], context["token"], context["user"]
        return next((item for item in store.list_attempts(token) if item["user_id"] == user["id"] and item["status"] == "active"), None)
    except Exception:
        return {"id": "", "payload": {}, "challenge_id": "unreadable", "created_at": ""}


def _belongs(existing: Any, artifact: Any, scenario_id: str | None) -> bool:
    """Whether a kept bundle is the bundle of the encounter on screen: same encounter, same case, same scenario. Anything unreadable is 'no'."""
    try:
        encounter = dict(dict(existing["bundle"]).get("encounter") or {})
        art = dict(artifact or {})
        return bool(art) and encounter.get("encounter_id") == art.get("encounter_id") and encounter.get("case_id") == art.get("case_id") and (encounter.get("scenario_id") or None) == (scenario_id or None)
    except Exception:
        return False


def _encounter_scenario(st: Any) -> str | None:
    assignment = st.session_state.get("encounter_assignment") or {}
    return dict(assignment).get(SCENARIO_FIELD)


def _make_bundle(st: Any, layer: Any) -> dict:
    bundles = layer.bundles
    live = bundles.from_session(st.session_state)
    bundle = bundles.build(live["artifact"], record=live["record"], trace=live["trace"], decision=live["decision"], scenario_id=_encounter_scenario(st))
    written = bundles.write(bundle)
    st.session_state[BUNDLE_KEY] = {"bundle": bundle, "written": written}
    return st.session_state[BUNDLE_KEY]


def panel(st: Any, layer: Any, exit_encounter: Callable | None = None) -> None:
    """The faculty operational panel of ONE review encounter. Read-only over the encounter: it issues no order, moves no clock and changes no state."""
    review, bundles = layer.review, layer.bundles
    live = bundles.from_session(st.session_state)
    status = bundles.status_view(live["artifact"], live["record"], live["decision"])
    halted = bool(status["halt"]["halted"])
    with st.expander("FACULTY DEVELOPMENT REVIEW PANEL · not resident-facing", expanded=halted):
        st.caption(BANNER)
        if halted:
            st.error("DEVELOPMENT AUTHORITY EXPERIMENT HALTED · " + str(status["halt"]["reason"] or "halted"))
            after = review.surface_after_halt()
            st.write("Operational halt of the experiment, not an outcome of the patient. Read-only review stays available. The only resolution is to leave the experimental encounter.")
            st.write("Excluded from this protocol after a halt (not implemented on purpose): " + ", ".join(after["excluded_unjudged"]))
        st.subheader("Operational status")
        st.json(status)
        existing = st.session_state.get(BUNDLE_KEY)
        if existing is not None and not _belongs(existing, live["artifact"], _encounter_scenario(st)):
            # A bundle of another encounter (an earlier one in this browser session) is never shown, never fed to the feedback form and never carries its reveal (P3-288 review, B1).
            existing = None
            for key in (BUNDLE_KEY, REVEALED_KEY):
                st.session_state.pop(key, None)
        if halted and existing is None:
            existing = _make_bundle(st, layer)                  # the halt is captured even if the reviewer closes the tab
        if st.button("Create review bundle", key="faculty_review_make_bundle"):
            existing = _make_bundle(st, layer)
        if existing is not None:
            bundle, written = existing["bundle"], existing["written"]
            st.write(f"Review bundle {bundle['bundle_id']} · stored: {written.get('stored')}")
            unusable = list(layer.bundles.bundle_problems(bundle)) + list(layer.bundles.evidence_problems(bundle))
            if unusable or not written.get("stored"):
                st.error("This bundle cannot be judged: " + "; ".join(unusable or [str(written.get("why") or "it was not stored")]) + ".")
            else:
                _feedback(st, layer.bundles, bundle)
        if halted and exit_encounter is not None:
            if st.button("Exit the experimental encounter", key="faculty_review_exit"):
                if st.session_state.get(BUNDLE_KEY) is None:
                    _make_bundle(st, layer)
                exit_encounter()


def _feedback(st: Any, bundles: Any, bundle: dict) -> None:
    state = st.session_state.get(REVEALED_KEY)
    revealed = isinstance(state, dict) and state.get("bundle_id") == bundle["bundle_id"]
    locked = dict(state.get("blinded") or {}) if revealed else {}
    st.subheader("Authority view (judge this first)")
    st.json({"authoritative_pressure_timeline": bundle["authority_view"]["authoritative_pressure_timeline"], "management_timeline": bundle["authority_view"]["management_timeline"],
             "halt_events": bundle["authority_view"]["halt_events"]})
    answers: dict = {}
    blind_ids = []
    for question in bundles.QUESTIONS:
        if question["stage"] == bundles.STAGE_BLINDED or (question["stage"] == bundles.STAGE_HALT and bundle["authority_view"]["halted"]):
            blind_ids.append(question["id"])
            answer = st.selectbox(question["text"], list(question["choices"]), index=None, key=f"fr_{bundle['bundle_id']}_{question['id']}", disabled=revealed)
            answers[question["id"]] = locked.get(question["id"]) if revealed else answer
    if not revealed:
        ready = all(answers.get(identifier) for identifier in blind_ids)
        if not ready:
            st.caption("Answer the questions above before the comparison is revealed: once it is, those answers are fixed.")
        if st.button("Reveal the nonauthoritative comparison", key=f"fr_reveal_{bundle['bundle_id']}", disabled=not ready):
            st.session_state[REVEALED_KEY] = {"bundle_id": bundle["bundle_id"], "blinded": {identifier: answers[identifier] for identifier in blind_ids}}
            st.rerun()
    else:
        st.subheader(bundles.COMPARATOR_LABEL)
        st.caption(bundles.COMPARATOR_NOTE)
        st.json(bundle["comparator"])
        for question in bundles.QUESTIONS:
            if question["stage"] == bundles.STAGE_COMPARATOR:
                answers[question["id"]] = st.selectbox(question["text"], list(question["choices"]), index=None, key=f"fr_{bundle['bundle_id']}_{question['id']}")
    answers["Q10"] = st.selectbox(bundles.QUESTIONS[-1]["text"], list(bundles.OVERALL), index=None, key=f"fr_{bundle['bundle_id']}_Q10")
    role = st.selectbox("Reviewer role", list(bundles.REVIEWER_ROLES), index=None, key=f"fr_role_{bundle['bundle_id']}")
    comments = st.text_area("Comments (synthetic cases: no real-patient data)", key=f"fr_comments_{bundle['bundle_id']}")
    if st.button("Submit feedback", key=f"fr_submit_{bundle['bundle_id']}"):
        payload = {"bundle_id": bundle["bundle_id"], "case_id": bundle["encounter"]["case_id"], "scenario_id": bundle["encounter"]["scenario_id"], "reviewer_role": role,
                   "comparator_revealed": revealed, "blinded_answers_at_reveal": (dict(locked) if revealed else None),
                   "answers": {key: value for key, value in answers.items() if value}, "comments": comments}
        result = bundles.store_feedback(payload, bundle)
        if result["stored"]:
            st.success(f"Feedback stored: {result['feedback_id']}")
        else:
            for problem in result["problems"]:
                st.error(problem)
