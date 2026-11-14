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
GENERIC_REFUSAL = "This is a faculty development review environment. It is not available to this account."
BUNDLE_KEY = "phase3_faculty_review_bundle"
REVEALED_KEY = "phase3_faculty_review_revealed"
SCENARIO_FIELD = "faculty_review_scenario"


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


def launcher(st: Any, layer: Any, context: Any, initial_state: Any, reset_session: Callable, start_encounter: Callable) -> None:
    """The review launcher: the scripted encounters, nothing else. Draws and stops the page when nothing has started."""
    review = layer.review
    st.title("Faculty development review")
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
