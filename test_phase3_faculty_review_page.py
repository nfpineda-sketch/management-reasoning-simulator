"""P3-281 to P3-287: the controlled FACULTY DEVELOPMENT REVIEW environment on the REAL page (Streamlit AppTest, individual accounts, the actual ``app.py``).

What it proves, with a faculty (administrator) account and a resident account in the same review process:

* entry: the review mode replaces the dashboard with the scripted launcher; only the two allowlisted GI cases can be started;
* the seven scripted review encounters run on the real page to the outcome the certified series recorded (same committed minutes), with the pressure authority active under the registered grant;
* the faculty panel is a separate surface: operational status, the halt experience, the review bundle, the staged feedback form; the resident-facing views carry none of it;
* the bundle verifies, replays, keeps the authority view apart from the legacy comparator and the nonauthoritative consciousness comparison, and is bound to its feedback;
* after a halt nothing mutating can run, reading and exiting remain, no death or terminal wording appears, the three unjudged operations are listed as excluded, and exiting does not resume;
* an ordinary (non-faculty) session, an ordinary deployment, a partial configuration and a shared-password deployment get no review mode, no grant, no status, no bundle and no feedback.
"""
import json
import os
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import faculty_review_ui as ui
import runtime_authority as ra
import runtime_authority_session as se
import runtime_authority_store as ras
import runtime_faculty_bundle as bundles
import runtime_faculty_review as fr
import runtime_pressure_grant as grants
import runtime_shadow as rs
import test_phase3_pair_page as page
import test_phase3_stop_page as stop
from account_store import AccountStore, hash_password

ROOT = Path(__file__).resolve().parent
ADMIN, RESIDENT = ("admin", "faculty-review-admin-password"), ("resident1", "faculty-review-resident-password")
DEATH_WORDS = ("death", "died", "dead", "cardiac arrest", "terminal", "moribund", "expired", "exitus", "fatal")
INTERNALS = ("PRESSURE_ONLY", "GRANT_V1", "ACTIVE_AUTHORITY", "AUTHORITY_SESSION", "NONAUTHORITATIVE", "comparator", "review bundle", "phase3_", "GI_DEVELOPMENT_SNAPSHOT")


def _review_env(mp, store_dir, **override):
    for name in (ra.AUTHORITY_FLAG, ra.SNAPSHOT_FLAG, ra.ENVIRONMENT_FLAG, ras.STORE_FLAG, rs.FLAG, fr.FLAG, fr.OFFLINE_FLAG, "OPENAI_API_KEY") + tuple(ra.PILOT_FLAGS) + tuple(ra.PILOT_REQUIRED_ON):
        mp.delenv(name, raising=False)
    env = {fr.FLAG: fr.MODE_ON, rs.FLAG: rs.MODE_SHADOW_COMPARE, ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: grants.PRESSURE_SNAPSHOT_ID,
           ra.ENVIRONMENT_FLAG: "development", fr.OFFLINE_FLAG: "1", ras.STORE_FLAG: str(store_dir)}
    env.update(override)
    for name, value in env.items():
        if value is not None:
            mp.setenv(name, value)


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("faculty_review")
    url = "sqlite:///" + str(tmp / "accounts.sqlite3")
    accounts = AccountStore(url, allow_sqlite=True)
    accounts.bootstrap_admin(ADMIN[0], hash_password(ADMIN[1]))
    token = accounts.authenticate(*ADMIN)
    accounts.register(RESIDENT[0], RESIDENT[1], accounts.create_invite(token, "resident", 1))
    world_extra = {}
    secrets = {"MRS_AUTH_MODE": "accounts", "MRS_DATABASE_URL": url, "MRS_ALLOW_LOCAL_SQLITE": True, "MRS_ADMIN_USERNAME": ADMIN[0], "MRS_ADMIN_PASSWORD_HASH": hash_password(ADMIN[1])}
    with pytest.MonkeyPatch.context() as mp:
        _review_env(mp, tmp / "store")
        yield {"mp": mp, "tmp": tmp, "store": tmp / "store", "secrets": secrets, "accounts": accounts, "runs": {}, "creds": {}, "admin_token": token, "count": [0], **world_extra}
    fr.release_for_tests()


def _faculty(world):
    """A new faculty account for ONE review run: a run keeps an active attempt in the account database, and the review environment (rightly) never resumes one."""
    world["count"][0] += 1
    name, password = f"reviewer{world['count'][0]}", f"faculty-review-password-{world['count'][0]}"
    world["accounts"].register(name, password, world["accounts"].create_invite(world["admin_token"], "faculty"))
    return name, password


def _open(world, credentials=None, secrets=None):
    credentials = credentials or _faculty(world)
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=600)
    at._credentials = credentials
    at.secrets.update(secrets or world["secrets"])
    at.run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    next(item for item in at.text_input if item.label == "Username").set_value(credentials[0])
    next(item for item in at.text_input if item.label == "Password").set_value(credentials[1])
    next(item for item in at.button if item.label == "Sign in").click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    return at


def _begin(at, scenario_id):
    next(item for item in at.selectbox if item.label == "Review encounter").set_value(scenario_id).run()
    next(item for item in at.button if item.label == "Begin review encounter").click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    assert at.session_state["started"] is True


def _lifecycle(at):
    return (at.session_state.get(se.SESSION_KEY) or {}).get("lifecycle")


def _drive(at, steps):
    for kind, text in steps:
        if _lifecycle(at) == se.INVALID_FOR_CONTINUATION:
            break
        {"order": lambda: page._order(at, text), "question": lambda: page._ask(at), "examination": lambda: page._examine(at)}[kind]()


def _run(world, scenario_id):
    """One scripted review encounter, run once per module and kept (the tests that only read share it)."""
    if scenario_id not in world["runs"]:
        at = _open(world)
        _begin(at, scenario_id)
        _drive(at, fr.scenario(scenario_id)["steps"])
        world["runs"][scenario_id] = at
        world["creds"][scenario_id] = at._credentials
    return world["runs"][scenario_id]


def _panel(at):
    return next((item for item in at.expander if str(item.label).startswith("FACULTY DEVELOPMENT REVIEW PANEL")), None)


def _texts(node, skip=("FACULTY DEVELOPMENT REVIEW PANEL", "Developer:")):
    out = []
    for child in getattr(node, "children", {}).values():
        label = str(getattr(child, "label", "") or "")
        if getattr(child, "type", "") == "expander" and label.startswith(skip):
            continue
        out.extend(_texts(child, skip))
        value = getattr(child, "value", None)
        if isinstance(value, str):
            out.append(value)
        if label:
            out.append(label)
    return out


def _everything(at):
    return "\n".join(_texts(at.main, skip=()) + [str(item.value) for item in at.sidebar.markdown] if hasattr(at, "sidebar") else _texts(at.main, skip=()))


def _status(at):
    panel = _panel(at)
    for item in panel.json:
        body = json.loads(item.value)
        if body.get("record_type") == bundles.STATUS_TYPE:
            return body
    raise AssertionError("no status in the panel")


def _site(at):
    return at.session_state.get(ra.SITE_KEY)


# -- entry, launcher and the two allowlisted cases ---------------------------------------------------------------------------------------------------------------------

def test_e1_a_faculty_account_enters_the_review_launcher_instead_of_the_dashboard(world):
    at = _open(world)
    decision = at.session_state[fr.SESSION_KEY]
    assert decision["enabled"] is True and decision["access"] == "FACULTY_REVIEWER" and decision["single_process"]["held"] is True
    assert [item.value for item in at.title] == ["Faculty development review"]
    options = next(item for item in at.selectbox if item.label == "Review encounter").options
    assert [text.split(" · ")[0] for text in options] == [item["id"] for item in fr.SCENARIOS] and len(options) == 7
    assert all(item["case_id"] in grants.CASES for item in fr.SCENARIOS)
    labels = [item.label for item in at.selectbox] + [item.label for item in at.button]
    assert "Management challenge" not in labels and "Begin Encounter" not in labels, "the ordinary dashboard and the free problem list are not offered"
    assert any("Not a resident pilot" in str(item.value) for item in at.warning), "the experimental status is explicit on the first screen"
    assert at.session_state["started"] is False and not at.session_state.get(ra.SITE_KEY)


def test_e2_a_review_encounter_starts_the_pinned_allowlisted_case_with_the_pressure_authority_under_the_grant(world):
    at = _run(world, "FR-B")
    assignment = at.session_state["encounter_assignment"]
    assert (assignment["pinned_variant"], assignment["faculty_review_scenario"]) == ("gi_bleed_57m", "FR-B")
    state = at.session_state["state"]
    assert state["engine_family"] == "gi_bleed" and state["encounter_spec"]["clinical_case"]["id"] == "gi_bleed_57m"
    site = _site(at)
    assert site is not None and site.grant["grant_id"] == grants.GRANT_ID and site.environment == "development" and site.case_id == "gi_bleed_57m"
    assert list(site.minutes_committed) == [5, 10, 30] and not site.halted
    assert at.session_state[se.SESSION_KEY]["lifecycle"] == se.ACTIVE_AUTHORITY
    assert (grants.GRANT["authority_mode"], tuple(grants.GRANT["domain"])) == ("PRESSURE_ONLY", ("sbp", "dbp", "map"))
    token = world["accounts"].authenticate(*world["creds"]["FR-B"])
    mine = [item for item in world["accounts"].list_attempts(token) if item["user_id"] == world["accounts"].get_user(token)["id"]]
    assert len(mine) == 1 and mine[0]["is_sandbox"] is True and mine[0]["challenge_id"] == ui.CHALLENGE_ID, "a staff attempt: never a resident's, never scored"
    assert mine[0]["encounter"]["assignment"]["faculty_review_scenario"] == "FR-B"


@pytest.mark.parametrize("scenario_id", [item["id"] for item in fr.SCENARIOS])
def test_e3_every_scripted_review_encounter_runs_on_the_real_page_to_the_certified_outcome(world, scenario_id):
    scenario = fr.scenario(scenario_id)
    series = json.loads((ROOT / "docs" / "revision" / "PHASE3_PRESSURE_AUTHORITY_SERIES.json").read_text(encoding="utf-8"))
    row = next(item for item in series["runs"] if item["case"] == scenario["case_id"] and item["scenario"] == scenario["series"])
    at = _run(world, scenario_id)
    record = at.session_state[se.SESSION_KEY]
    committed = [int(minute) for minute in (_site(at).minutes_committed if _site(at) is not None else [item["minute"] for item in at.session_state[ra.ARTIFACT_KEY]["minutes"] if item["committed"]])]
    assert committed == row["committed_minutes"], (committed, row["committed_minutes"])
    assert (record["lifecycle"] == se.INVALID_FOR_CONTINUATION) is (scenario["expected"].startswith("HALTED")), record["lifecycle"]
    if scenario["expected"] == "HALTED_AT_COLLAPSE_BOUNDARY":
        assert record["stop_class"] == se.STOP_COLLAPSE_BOUNDARY
    if scenario["expected"] == "HALTED_BY_UNSUPPORTED_ACTION":
        assert record["stop_class"] == se.STOP_UNSUPPORTED_ACTION
    assert _panel(at) is not None and _status(at)["case_id"] == scenario["case_id"] and _status(at)["authority_mode"] == "PRESSURE_ONLY"


# -- the faculty panel is a separate surface ---------------------------------------------------------------------------------------------------------------------------

def test_e4_the_panel_shows_the_operational_status_and_the_resident_views_carry_none_of_it(world):
    at = _run(world, "FR-B")
    status = _status(at)
    assert status["case_id"] == "gi_bleed_57m" and status["grant_id"] == grants.GRANT_ID and status["grant_version"] == grants.GRANT_VERSION and status["authority_mode"] == "PRESSURE_ONLY"
    assert status["session_state"] == se.ACTIVE_AUTHORITY and status["last_authoritative_minute"] == 30 and set(status["last_authoritative_pressure"]) == {"sbp", "dbp", "map"}
    assert status["snapshot_id"] == grants.PRESSURE_SNAPSHOT_ID
    assert status["lineage"] == {"core_version": grants.CORE_VERSION, "core_digest": grants.CORE_DIGEST, "phase2_closure_digest": rs.PHASE2_DIGEST}, "the active core's version AND digest, with the closure digest named apart"
    assert status["artifact"]["digest"] and status["artifact"]["minutes_recorded"] >= 3 and status["halt"]["halted"] is False
    assert status["faculty_review"] == {"enabled": True, "single_process": True, "allowlist": ["gi_bleed_57m", "gi_bleed_72f"]}
    assert "consciousness" not in json.dumps(status).lower(), "the status never shows the common consciousness as a state of the encounter"
    resident_view = "\n".join(_texts(at.main))
    for internal in INTERNALS + tuple(page.FORBIDDEN_ON_THE_PAGE):
        assert internal not in resident_view, f"the resident-facing views must not carry {internal!r}"
    assert not any(label in resident_view for label in ("FACULTY DEVELOPMENT REVIEW", "Create review bundle", "Submit feedback", "Reveal the nonauthoritative comparison"))
    for word in DEATH_WORDS:
        assert word not in resident_view.lower(), word


# -- the review bundle -----------------------------------------------------------------------------------------------------------------------------------------------------

def _make_bundle(at):
    next(item for item in at.button if item.label == "Create review bundle").click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    return at.session_state[ui.BUNDLE_KEY]


def test_e5_the_bundle_holds_every_part_verifies_replays_and_is_stored(world):
    at = _run(world, "FR-B")
    made = _make_bundle(at)
    bundle, written = made["bundle"], made["written"]
    assert bundles.bundle_problems(bundle) == [] and written["stored"] is True and Path(written["path"]).is_file()
    assert written["path"].startswith(str(world["store"] / fr.REVIEW_DIRNAME / "bundles")), "inside the review directory of the faculty store, never in the repository"
    assert bundles.load(bundle["bundle_id"], environ={ras.STORE_FLAG: str(world["store"])}) == bundle
    assert bundle["encounter"] == {**bundle["encounter"], "case_id": "gi_bleed_57m", "scenario_id": "FR-B", "family": "gi_bleed", "environment": "development"}
    authority, comparator, evidence = bundle["authority_view"], bundle["comparator"], bundle["evidence"]
    assert [row["minute"] for row in authority["authoritative_pressure_timeline"]] == [5, 10, 30] and all(set(row) == {"minute", "sbp", "dbp", "map"} for row in authority["authoritative_pressure_timeline"])
    assert [row["minute"] for row in comparator["legacy_counterfactual_pressure_timeline"]] == [5, 10, 30]
    assert authority["management_timeline"] and authority["action_dispositions"] and authority["lifecycle"] == se.ACTIVE_AUTHORITY and authority["halted"] is False
    assert authority["collapse_boundary"]["window_max_minute"] == 240 and authority["halt_events"] == []
    assert evidence["artifact_verification"]["complete"] is True and evidence["artifact_verification"]["digest_matches"] is True and evidence["replay"]["reproduces"] is True
    overlay = comparator["consciousness_overlay_comparison"]
    assert overlay["label"] == "NONAUTHORITATIVE DEVELOPMENT COMPARISON" and overlay["authority"] is False and overlay["resident_visible"] is False and overlay["writes_mental_status"] is False and overlay["rows"]
    assert len(bundle["limitations"]) >= 9 and any("unsigned" in text for text in bundle["limitations"]) and any("Single process" in text for text in bundle["limitations"])
    again = bundles.build(**{key: value for key, value in bundles.from_session(at.session_state).items() if key != "decision"}, decision=at.session_state[fr.SESSION_KEY], scenario_id="FR-B")
    assert again["bundle_id"] == bundle["bundle_id"], "the same encounter state gives the same bundle id"


def test_e6_the_comparator_is_evidence_not_a_score_and_a_bundle_that_grades_is_refused(world):
    bundle = _make_bundle(_run(world, "FR-B"))["bundle"]
    differences = bundle["comparator"]["differences_from_legacy"]
    assert differences and all(set(row) == {"minute", "sbp_difference", "dbp_difference", "map_difference"} for row in differences)
    assert "not a score" in bundle["statement"] and "not a standard of truth" in bundle["comparator"]["note"]
    assert bundles.bundle_problems(bundle) == []
    for key in ("closeness", "score", "agreement"):
        tampered = json.loads(json.dumps(bundle))
        tampered["comparator"][key] = 0.97
        assert any("grading key" in problem for problem in bundles.bundle_problems(tampered)), key
    changed = json.loads(json.dumps(bundle))
    changed["authority_view"]["halted"] = True
    assert any("does not recompute" in problem for problem in bundles.bundle_problems(changed)), "a bundle edited after it was written no longer verifies"
    assert bundles.write(changed, environ={ras.STORE_FLAG: str(world["store"])})["stored"] is False


# -- the staged feedback ---------------------------------------------------------------------------------------------------------------------------------------------

def _select(at, label, value):
    next(item for item in at.selectbox if item.label == label).set_value(value)


def test_e7_the_comparator_is_hidden_until_revealed_the_blinded_answers_are_fixed_at_the_reveal_and_feedback_is_bound_to_its_bundle(world):
    at = _run(world, "FR-C")
    made = _make_bundle(at)
    bundle = made["bundle"]
    page_text = "\n".join(_texts(_panel(at), skip=()))
    assert "NONAUTHORITATIVE DEVELOPMENT COMPARISON" not in page_text, "before the reveal the reviewer sees the authority view only"
    labels = [item.label for item in at.selectbox]
    assert not any(label.startswith("Did the common consciousness comparison") or label.startswith("Was there any contradiction") for label in labels)
    assert not any(label.startswith("Did the halt occur") for label in labels), "no halt questions for an encounter that did not halt"
    reveal = next(item for item in at.button if item.label == "Reveal the nonauthoritative comparison")
    assert reveal.disabled is True, "the comparison cannot be revealed before the blinded questions are answered"
    blinded = {"Q1": "YES", "Q2": "APPROPRIATE", "Q3": "TOO_LATE", "Q4": "PLAUSIBLE", "Q5": "NO"}
    for question in bundles.QUESTIONS:
        if question["id"] in blinded:
            _select(at, question["text"], blinded[question["id"]])
    at.run()                                                              # the page redraws with the answers: only now can the comparison be revealed
    reveal = next(item for item in at.button if item.label == "Reveal the nonauthoritative comparison")
    assert reveal.disabled is False
    reveal.click().run()
    revealed = "\n".join(_texts(_panel(at), skip=()))
    assert "NONAUTHORITATIVE DEVELOPMENT COMPARISON" in revealed and any(item.label.startswith("Did the common consciousness comparison") for item in at.selectbox)
    assert at.session_state[ui.REVEALED_KEY] == {"bundle_id": bundle["bundle_id"], "blinded": blinded}
    assert all(next(item for item in at.selectbox if item.label == question["text"]).disabled is True for question in bundles.QUESTIONS if question["id"] in blinded), "Q1-Q5 cannot change after the reveal"
    for question in bundles.QUESTIONS:
        if question["id"] in ("Q8", "Q9", "Q10"):
            _select(at, question["text"], {"Q8": "YES", "Q9": "NONE", "Q10": "ACCEPT_WITH_LIMITATION"}[question["id"]])
    _select(at, "Reviewer role", "faculty")
    next(item for item in at.text_area if item.label.startswith("Comments")).set_value("The recovery began a little late; otherwise coherent.")
    next(item for item in at.button if item.label == "Submit feedback").click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    stored = sorted((world["store"] / fr.REVIEW_DIRNAME / "feedback").glob(f"{bundle['bundle_id']}__*.json"))
    assert len(stored) == 1, [str(error.value) for error in at.error]
    record = json.loads(stored[0].read_text(encoding="utf-8"))
    assert (record["bundle_id"], record["case_id"], record["scenario_id"], record["reviewer_role"], record["comparator_revealed"]) == (bundle["bundle_id"], "gi_bleed_57m", "FR-C", "faculty", True)
    assert record["answers"]["Q10"] == "ACCEPT_WITH_LIMITATION" and "synthetic" in record["statement"].lower()
    assert record["blinded_answers_at_reveal"] == blinded and {key: record["answers"][key] for key in blinded} == blinded, "the record shows the blinded answers were given before the reveal"


def test_e8_feedback_for_another_encounter_or_with_identifiers_is_refused(world):
    bundle = _make_bundle(_run(world, "FR-B"))["bundle"]
    answers = {f"Q{i}": bundles.QUESTIONS[i - 1]["choices"][0] for i in (1, 2, 3, 4, 5)}
    answers["Q10"] = "ACCEPT"
    good = {"bundle_id": bundle["bundle_id"], "case_id": "gi_bleed_57m", "scenario_id": "FR-B", "reviewer_role": "faculty", "comparator_revealed": False, "answers": answers, "comments": ""}
    assert bundles.feedback_problems(good, bundle) == []
    assert any("another bundle" in p for p in bundles.feedback_problems({**good, "bundle_id": "0" * 16}, bundle))
    assert any("another case" in p for p in bundles.feedback_problems({**good, "case_id": "gi_bleed_72f"}, bundle))
    assert any("another scenario" in p for p in bundles.feedback_problems({**good, "scenario_id": "FR-C"}, bundle))
    assert any("reviewer role" in p for p in bundles.feedback_problems({**good, "reviewer_role": "resident"}, bundle))
    assert any("Q1 is not answered" in p for p in bundles.feedback_problems({**good, "answers": {k: v for k, v in answers.items() if k != "Q1"}}, bundle))
    assert any("outside its choices" in p for p in bundles.feedback_problems({**good, "answers": {**answers, "Q1": "MAYBE"}}, bundle))
    assert any("before the comparator was revealed" in p for p in bundles.feedback_problems({**good, "answers": {**answers, "Q8": "YES"}}, bundle))
    assert any("identifiers" in p for p in bundles.feedback_problems({**good, "comments": "patient MRN: 123456 seen"}, bundle))
    assert any("identifiers" in p for p in bundles.feedback_problems({**good, "comments": "write to reviewer@example.org"}, bundle))
    assert any("Q5 asks for a comment" in p for p in bundles.feedback_problems({**good, "answers": {**answers, "Q5": "YES"}}, bundle))
    assert bundles.feedback_problems(good, {"record_type": "x"}) == ["the bundle the feedback is for does not verify"]
    refused = bundles.store_feedback({**good, "case_id": "gi_bleed_72f"}, bundle, environ={ras.STORE_FLAG: str(world["store"])})
    assert refused["stored"] is False and refused["problems"]
    first = bundles.store_feedback(good, bundle, environ={ras.STORE_FLAG: str(world["store"])})
    assert first["stored"] is True and bundles.store_feedback(good, bundle, environ={ras.STORE_FLAG: str(world["store"])})["feedback_id"] == first["feedback_id"], "create-only and idempotent"


# -- the halt experience -----------------------------------------------------------------------------------------------------------------------------------------------

def test_e9_after_a_collapse_boundary_halt_nothing_mutating_runs_reading_stays_and_the_wording_is_operational(world):
    at = _run(world, "FR-A")
    record = at.session_state[se.SESSION_KEY]
    assert record["lifecycle"] == se.INVALID_FOR_CONTINUATION and record["legacy_fallback_allowed"] is False and record["stop_class"] == se.STOP_COLLAPSE_BOUNDARY
    controls = stop._controls(at)
    assert not (controls["ask_box"] or controls["order_box"] or controls["examine"] or controls["ecg"] or controls["send"] or controls["ask_button"] or controls["complete_enabled"]), controls
    panel = _panel(at)
    text = "\n".join(_texts(panel, skip=()))
    assert "DEVELOPMENT AUTHORITY EXPERIMENT HALTED" in text and "Operational halt of the experiment, not an outcome of the patient" in text
    assert all(name in text for name in fr.EXCLUDED_AFTER_HALT) and "only resolution is to leave the experimental encounter" in text
    assert _status(at)["halt"]["halted"] is True and _status(at)["halt"]["stop_class"] == se.STOP_COLLAPSE_BOUNDARY, "faculty can read why it halted"
    everything = "\n".join(_texts(at.main, skip=()))
    for word in DEATH_WORDS:
        assert word not in everything.lower(), f"{word!r}: a halt is an operational stop of the experiment, never a statement about the patient"
    bundle = at.session_state[ui.BUNDLE_KEY]["bundle"]
    assert bundle["authority_view"]["halted"] is True and bundle["authority_view"]["halt_events"], "the halt is captured in a bundle even if the reviewer never asks for one"
    assert bundle["authority_view"]["stop_class"] == se.STOP_COLLAPSE_BOUNDARY and bundles.bundle_problems(bundle) == []
    assert any(item.label.startswith("Did the halt occur at an understandable point") for item in at.selectbox) and any(item.label.startswith("Did the halt behaviour create") for item in at.selectbox)
    assert any(item.label == "Exit the experimental encounter" for item in at.button) and not any(item.label.lower().startswith(("resume", "rollback", "restart")) for item in at.button)
    minute_before = page._minute(at)
    for attempt in (lambda: page._ask(at, "Where does it hurt?"), lambda: page._order(at, "Reassess in 10 minutes."), lambda: page._examine(at)):
        with pytest.raises(StopIteration):
            attempt()
    assert page._minute(at) == minute_before, "no legacy continuation"


def test_e10_a_halt_by_an_unsupported_action_is_operational_and_exiting_it_does_not_resume_the_encounter(world):
    at = _open(world)
    _begin(at, "FR-F")
    _drive(at, fr.scenario("FR-F")["steps"])
    record = at.session_state[se.SESSION_KEY]
    assert record["lifecycle"] == se.INVALID_FOR_CONTINUATION and record["stop_class"] == se.STOP_UNSUPPORTED_ACTION
    halted_encounter = at.session_state["state"]["encounter_spec"]["encounter_id"] if "encounter_id" in at.session_state["state"]["encounter_spec"] else rs._encounter_id(dict(at.session_state["state"]))
    assert halted_encounter
    next(item for item in at.button if item.label == "Exit the experimental encounter").click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    assert at.session_state["started"] is False, "leaving the experimental encounter ends it"
    assert at.session_state.get(ra.SITE_KEY) is None and not at.session_state.get(se.SESSION_KEY) and [item.value for item in at.title] == ["Faculty development review"]
    labels = [item.label for item in at.button]
    assert "Begin review encounter" in labels and not any(label.lower().startswith(("resume", "rollback", "restart")) for label in labels)
    _begin(at, "FR-B")
    assert page._minute(at) == 0 and rs._encounter_id(dict(at.session_state["state"])) != halted_encounter, "a new review encounter, not the halted one"
    assert (at.session_state.get(se.SESSION_KEY) or {}).get("lifecycle") in (None, se.PREAUTHORITY) and not (_site(at) is not None and _site(at).halted)


# -- an ordinary session, an ordinary deployment, a partial configuration, a shared password ---------------------------------------------------------------------------

def test_n1_a_resident_account_in_a_review_process_gets_no_mode_no_grant_no_status_no_bundle_and_no_feedback(world):
    at = _open(world, RESIDENT)
    decision = at.session_state[fr.SESSION_KEY]
    assert decision["enabled"] is False and decision["access"] == "NOT_A_FACULTY_ACCOUNT"
    text = "\n".join(_texts(at.main, skip=()))
    assert ui.GENERIC_REFUSAL in text and not any(item.label in ("Begin review encounter", "Review encounter") for item in list(at.button) + list(at.selectbox))
    assert not any(name in text for name in ("MRS_", "single_process", "PRESSURE_ONLY", "grant", "store", "flag"))
    assert not at.session_state.get("started") and at.session_state.get(ra.SITE_KEY) is None and _panel(at) is None
    assert ui.BUNDLE_KEY not in at.session_state and ui.REVEALED_KEY not in at.session_state


def test_n2_an_ordinary_deployment_has_no_review_mode_at_all(world, monkeypatch):
    monkeypatch.delenv(fr.FLAG)
    at = _open(world)
    assert fr.SESSION_KEY not in at.session_state, "with the flag absent the page never evaluates, publishes or imports the review mode"
    labels = [item.label for item in at.selectbox] + [item.label for item in at.button]
    assert "Review encounter" not in labels and "Begin review encounter" not in labels and any("Begin Encounter" == label or label == "Management challenge" for label in labels)
    assert _panel(at) is None and at.session_state.get(ra.SITE_KEY) is None


@pytest.mark.parametrize("name,override", (("no_store", {ras.STORE_FLAG: None}), ("paid_generation", {fr.OFFLINE_FLAG: None}), ("shadow_off", {rs.FLAG: None}), ("wrong_environment", {ra.ENVIRONMENT_FLAG: "production"})))
def test_n3_a_partial_configuration_makes_the_review_unavailable_to_faculty_and_starts_nothing(world, monkeypatch, name, override):
    for key, value in override.items():
        monkeypatch.delenv(key, raising=False) if value is None else monkeypatch.setenv(key, value)
    at = _open(world)
    assert [item.value for item in at.error] == ["FACULTY DEVELOPMENT REVIEW UNAVAILABLE"], name
    text = "\n".join(_texts(at.main, skip=()))
    assert "authority is unavailable and no review encounter can start" in text
    assert not any(item.label == "Begin review encounter" for item in at.button) and not at.session_state.get("started") and at.session_state.get(ra.SITE_KEY) is None
    assert at.session_state[fr.SESSION_KEY]["enabled"] is False
    labels = [item.label for item in at.selectbox] + [item.label for item in at.button]
    assert "Begin Encounter" not in labels and "Management challenge" not in labels and "Review encounter" not in labels, "the page stops: neither the launcher nor the ordinary dashboard is drawn"


def test_n4_a_shared_password_deployment_cannot_enable_faculty_only_review(world):
    secrets = {"APP_PASSWORD": "shared-test-password"}
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=600)
    at.secrets.update(secrets)
    at.session_state["_shared_access_granted"] = True
    at.run()
    assert at.session_state[fr.SESSION_KEY]["enabled"] is False and at.session_state[fr.SESSION_KEY]["conditions"]["accounts"] is False
    assert ui.GENERIC_REFUSAL in "\n".join(_texts(at.main, skip=())) and at.session_state.get(ra.SITE_KEY) is None


def test_n5_the_review_mode_is_inaccessible_from_the_first_pilot_configuration(world, monkeypatch):
    monkeypatch.setenv(ra.PILOT_FLAGS[0], "1")
    at = _open(world)
    assert at.session_state[fr.SESSION_KEY]["conditions"]["no_pilot"] is False and at.session_state[fr.SESSION_KEY]["enabled"] is False
    assert not any(item.label == "Begin review encounter" for item in at.button)


def test_n6_a_session_whose_review_decision_is_not_enabled_never_opens_the_authority_site(world):
    at = _open(world)
    at.session_state[fr.SESSION_KEY] = {**dict(at.session_state[fr.SESSION_KEY]), "enabled": False, "problems": ["tampered"]}
    available, why = fr.authority_available(at.session_state, dict(os.environ))
    assert available is False and "FACULTY_REVIEW_CONFIGURATION_INCOMPLETE" in why
    state = {"engine_family": "gi_bleed", "case_id": "x", "sim_time": 0, "observable": {}}
    assert ra.site_for(state, at.session_state) is None and at.session_state.get("phase3_faculty_review_refusal", "").startswith("FACULTY_REVIEW_CONFIGURATION_INCOMPLETE")


def test_n7_review_runs_never_touch_scoring_the_pilot_or_the_consciousness(world):
    at = _run(world, "FR-B")
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    artifact = bundles.from_session(at.session_state)["artifact"]
    assert artifact["consciousness_overlay"]["authority"] is False and artifact["consciousness_overlay"]["writes_mental_status"] is False
    assert artifact["consciousness_overlay"]["resident_visible"] is False and artifact["consciousness_overlay"]["written_into_the_encounter"] is False
    assert artifact["excluded_domains"] and "mental_status" in artifact["excluded_domains"] and "consciousness" in artifact["excluded_domains"]
    resident = world["accounts"].authenticate(*RESIDENT)
    assert world["accounts"].list_attempts(resident) == [], "no review encounter is ever recorded in a resident's account"


# -- FD-FAC-08: the review environment never resumes an encounter -----------------------------------------------------------------------------------------------------

def test_e11_an_unfinished_attempt_is_never_resumed_in_silence_it_must_be_abandoned_first(world):
    credentials = _faculty(world)
    first = _open(world, credentials)
    _begin(first, "FR-B")
    page._order(first, "Place an IV line.")
    second = _open(world, credentials)                                  # a refreshed page / a new session of the same account: the earlier attempt is still active in the database
    assert second.session_state["started"] is False
    assert [item.value for item in second.error] == ["UNFINISHED ATTEMPT · The review environment does not resume encounters: abandon the unfinished attempt to start a review encounter."]
    labels = [item.label for item in second.button]
    assert "Begin review encounter" not in labels and "Abandon the unfinished attempt" in labels and not any(label.lower().startswith(("resume", "continue")) for label in labels)
    next(item for item in second.button if item.label == "Abandon the unfinished attempt").click().run()
    assert not second.exception, [str(item.value)[:300] for item in second.exception]
    _begin(second, "FR-D")
    assert second.session_state["encounter_assignment"]["faculty_review_scenario"] == "FR-D" and second.session_state["state"]["encounter_spec"]["clinical_case"]["id"] == "gi_bleed_72f"
    assert page._minute(second) == 0, "the chosen scenario started fresh; the abandoned one was not restored"
    token = world["accounts"].authenticate(*credentials)
    statuses = sorted(item["status"] for item in world["accounts"].list_attempts(token) if item["user_id"] == world["accounts"].get_user(token)["id"])
    assert statuses == ["abandoned", "active"]


# -- P3-288 (independent review): the repairs, each with the attack that found it ---------------------------------------------------------------------------------------

def _rehash(bundle):
    body = {key: value for key, value in bundle.items() if key != "bundle_id"}
    return {**body, "bundle_id": ra.digest_of(json.loads(json.dumps(body, default=str)))[:16]}


def test_e12_a_bundle_and_a_reveal_of_an_earlier_encounter_never_follow_the_reviewer_into_the_next_one(world):
    at = _open(world)
    _begin(at, "FR-F")
    _drive(at, fr.scenario("FR-F")["steps"])
    first = at.session_state[ui.BUNDLE_KEY]
    assert first["bundle"]["encounter"]["scenario_id"] == "FR-F" and first["bundle"]["authority_view"]["halted"] is True
    at.session_state[ui.REVEALED_KEY] = {"bundle_id": first["bundle"]["bundle_id"], "blinded": {"Q1": "YES"}}
    next(item for item in at.button if item.label == "Exit the experimental encounter").click().run()
    assert at.session_state.get(ui.BUNDLE_KEY) is None and at.session_state.get(ui.REVEALED_KEY) is None, "the launcher drops what the earlier encounter's review left behind"
    _begin(at, "FR-D")
    # defence in depth: even a bundle injected into the next encounter's session is not shown, not judged and not revealed
    at.session_state[ui.BUNDLE_KEY] = first
    at.session_state[ui.REVEALED_KEY] = {"bundle_id": first["bundle"]["bundle_id"], "blinded": {"Q1": "YES"}}
    at.run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    assert at.session_state.get(ui.BUNDLE_KEY) is None and at.session_state.get(ui.REVEALED_KEY) is None
    assert first["bundle"]["bundle_id"] not in "\n".join(_texts(_panel(at), skip=()))
    _drive(at, fr.scenario("FR-D")["steps"])
    second = at.session_state[ui.BUNDLE_KEY]["bundle"]
    assert (second["encounter"]["case_id"], second["encounter"]["scenario_id"], second["authority_view"]["halted"]) == ("gi_bleed_72f", "FR-D", True), "the halt of THIS encounter is captured"
    assert second["bundle_id"] != first["bundle"]["bundle_id"] and second["encounter"]["encounter_id"] != first["bundle"]["encounter"]["encounter_id"]


def test_e13_the_bundle_and_feedback_api_refuse_every_integrity_attack_of_the_review(world):
    at = _run(world, "FR-B")
    bundle = _make_bundle(at)["bundle"]
    env = {ras.STORE_FLAG: str(world["store"])}
    answers = {"Q1": "YES", "Q2": "APPROPRIATE", "Q3": "APPROPRIATE", "Q4": "PLAUSIBLE", "Q5": "NO", "Q10": "ACCEPT"}
    good = {"bundle_id": bundle["bundle_id"], "case_id": "gi_bleed_57m", "scenario_id": "FR-B", "reviewer_role": "faculty", "comparator_revealed": False, "answers": answers, "comments": ""}
    assert bundles.feedback_problems(good, bundle) == [] and bundles.evidence_problems(bundle) == []
    assert bundle["evidence"]["artifact_id"] and ras.load(bundle["evidence"]["artifact_id"], environ=env) is not None, "the bundle names the stored artifact it is about"

    # a bundle that was never written is not feedback-able
    unwritten = _rehash({**bundle, "statement": bundle["statement"] + " (edited)"})
    assert bundles.bundle_problems(unwritten) == []
    refused = bundles.store_feedback({**good, "bundle_id": unwritten["bundle_id"]}, unwritten, environ=env)
    assert refused["stored"] is False and any("not stored" in problem for problem in refused["problems"])
    # only the ten questions are stored
    assert any("not one of the ten questions" in problem for problem in bundles.feedback_problems({**good, "answers": {**answers, "Q99": "John Smith"}}, bundle))
    # identifiers, in the shapes the review found
    for comment in ("MRN12345 was the patient", "patient id 4471", "DOB 03/04/1957", "+1 415 555 0100", "Mrs. Johnson in bed 4", "m​rn 123", "DNI12345678A", "12.345.678-9"):
        assert any("identifiers" in problem for problem in bundles.feedback_problems({**good, "comments": comment}, bundle)), comment
    assert bundles.feedback_problems({**good, "comments": "SBP fell from 120 to 90 over 60 minutes and recovered by minute 120."}, bundle) == []
    # a path that leaves the bundle directory
    traversal = _rehash({**bundle, "encounter": {**bundle["encounter"], "case_id": "../../escape"}})
    assert any("outside the allowlist" in problem for problem in bundles.bundle_problems(traversal))
    assert bundles.write(traversal, environ=env)["stored"] is False and not list(world["tmp"].rglob("escape__*")), "nothing was written outside the bundle directory"
    # grading keys, by word and in any list position
    for key in ("mean_absolute_error", "closeness_pct", "agreement_with_legacy", "meanAbsoluteError", "match_rate"):
        tampered = json.loads(json.dumps(bundle))
        tampered["comparator"][key] = 0.9
        assert any("grading key" in problem for problem in bundles.bundle_problems(_rehash(tampered))), key
    deep = json.loads(json.dumps(bundle))
    deep["comparator"]["differences_from_legacy"] = [{"minute": 0}] * 60 + [{"score": 1}]
    assert any("grading key" in problem for problem in bundles.bundle_problems(_rehash(deep))), "the 61st row is as much a grade as the first"
    assert bundles.bundle_problems(bundle) == [], "the evidence block's own words (digest_matches, label_matches_content, the replay verdict) are not grades"
    # a scenario that is not the case's
    assert any("another case" in problem for problem in bundles.bundle_problems(_rehash({**bundle, "encounter": {**bundle["encounter"], "scenario_id": "FR-D"}})))
    assert any("not in the review set" in problem for problem in bundles.bundle_problems(_rehash({**bundle, "encounter": {**bundle["encounter"], "scenario_id": "FR-Z"}})))
    # a forged reveal: no snapshot, or a snapshot that does not match
    assert any("not recorded" in problem for problem in bundles.feedback_problems({**good, "comparator_revealed": True, "answers": {**answers, "Q8": "YES", "Q9": "NONE"}}, bundle))
    blind = {key: answers[key] for key in ("Q1", "Q2", "Q3", "Q4", "Q5")}
    revealed = {**good, "comparator_revealed": True, "answers": {**answers, "Q8": "YES", "Q9": "NONE"}, "blinded_answers_at_reveal": blind}
    assert bundles.feedback_problems(revealed, bundle) == []
    assert any("changed after the comparator was revealed" in problem for problem in bundles.feedback_problems({**revealed, "answers": {**revealed["answers"], "Q1": "NO"}}, bundle))
    assert any("not revealed" in problem for problem in bundles.feedback_problems({**good, "blinded_answers_at_reveal": blind}, bundle))
    # a truncated file under a real identity is not a stored record
    stored = bundles.store_feedback(good, bundle, environ=env)
    assert stored["stored"] is True
    Path(stored["path"]).write_text("", encoding="utf-8")
    broken = bundles.store_feedback(good, bundle, environ=env)
    assert broken["stored"] is False and broken["problems"], "a 0-byte file is not reported as stored"
    bundle_path = Path(bundles.write(bundle, environ=env)["path"])
    bundle_path.write_text("{", encoding="utf-8")
    assert bundles.write(bundle, environ=env)["stored"] is False and bundles.load(bundle["bundle_id"], environ=env) is None
    bundle_path.write_text(json.dumps(bundle, indent=1, sort_keys=True), encoding="utf-8")        # restore for the other tests
    assert bundles.write(bundle, environ=env)["stored"] is True


def test_e14_evidence_that_fails_its_own_checks_is_shown_as_such_and_is_not_feedback_able(world):
    at = _run(world, "FR-B")
    env = {ras.STORE_FLAG: str(world["store"])}
    artifact = json.loads(json.dumps(bundles.from_session(at.session_state)["artifact"], default=str))
    live = bundles.from_session(at.session_state)
    artifact["minutes"][0]["common_pressures"]["sbp"] = float(artifact["minutes"][0]["common_pressures"]["sbp"]) + 7.0
    forged = bundles.build(artifact, record=live["record"], trace=live["trace"], decision=live["decision"], scenario_id="FR-B")
    assert bundles.bundle_problems(forged) == [], "structurally a bundle"
    failures = bundles.evidence_problems(forged)
    assert failures and any("does not verify" in problem for problem in failures), failures
    answers = {"Q1": "YES", "Q2": "APPROPRIATE", "Q3": "APPROPRIATE", "Q4": "PLAUSIBLE", "Q5": "NO", "Q10": "ACCEPT"}
    payload = {"bundle_id": forged["bundle_id"], "case_id": "gi_bleed_57m", "scenario_id": "FR-B", "reviewer_role": "faculty", "comparator_revealed": False, "answers": answers, "comments": ""}
    assert any("cannot be judged" in problem for problem in bundles.feedback_problems(payload, forged))
    assert bundles.write(forged, environ=env)["stored"] is True, "the failure itself is evidence a reviewer must be able to open"
    # an artifact that claims authority over the consciousness shows the claim instead of a hard-coded 'False'
    claimed = json.loads(json.dumps(bundles.from_session(at.session_state)["artifact"], default=str))
    claimed["consciousness_overlay"]["authority"] = True
    overclaim = bundles.build(claimed, record=live["record"], trace=live["trace"], decision=live["decision"], scenario_id="FR-B")
    assert overclaim["comparator"]["consciousness_overlay_comparison"]["authority"] is True and bundles.evidence_problems(overclaim)
    # on the page: a bundle whose evidence fails is shown as such and the feedback form is not offered for it
    original = at.session_state[ui.BUNDLE_KEY] if ui.BUNDLE_KEY in at.session_state else None
    at.session_state[ui.BUNDLE_KEY] = {"bundle": forged, "written": {"stored": True}}
    at.run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    panel_text = "\n".join(_texts(_panel(at), skip=()))
    assert "This bundle cannot be judged" in panel_text and "does not verify" in panel_text
    assert not any(item.label == "Submit feedback" for item in at.button) and not any(item.label == "Reviewer role" for item in at.selectbox)
    if original is not None:
        at.session_state[ui.BUNDLE_KEY] = original
        at.run()


def test_e15_a_review_session_whose_flag_disappears_halts_instead_of_continuing_as_an_ordinary_encounter(world, monkeypatch):
    at = _open(world)
    _begin(at, "FR-B")
    page._order(at, "Place an IV line.")
    page._order(at, "Give 1 litre of normal saline over 15 minutes.")
    assert _lifecycle(at) == se.ACTIVE_AUTHORITY, _lifecycle(at)
    monkeypatch.delenv(fr.FLAG)                                           # the review flag is gone; every other flag of the authority is still there
    page._order(at, "Reassess in 20 minutes.")                           # the next turn asks the authority site, which no longer finds a review configuration
    record = at.session_state.get(se.SESSION_KEY) or {}
    assert record.get("lifecycle") == se.INVALID_FOR_CONTINUATION, (record.get("lifecycle"), record.get("halt_reason"))
    assert ra.CONFIGURATION_CHANGED in json.dumps(record, default=str), "the halt names a configuration change, never a silent return to the legacy engine"
