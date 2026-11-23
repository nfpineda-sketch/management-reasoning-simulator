"""P3-521 to P3-530 (page level): the controlled DEVELOPMENT pilot of the GI management trace on the REAL page (Streamlit AppTest, individual synthetic accounts, ``app.py``).

What it proves, with synthetic resident and faculty accounts in one pilot deployment (the resident and faculty dry runs of P3-528 and P3-529 are these tests):

* the participant's page is the pilot start only; the encounter starts on the one pilot case WITHOUT an attempt in the account (nothing reaches progress, portfolio or evaluation);
* pressures are the live development authority's (the same as the headless development runner for the same orders) and the pilot record logs every turn and the artifact;
* mental status is the earlier model's on the monitor, the patient-response text and the appearance line, and is withheld once norepinephrine has been given;
* a request for definitive control of the bleeding does NOT run: no consultation reaches the engine, the clock does not move, the encounter ends at the development boundary;
* no participant screen carries an internal variable, an identifier, a grant or snapshot, a faculty category or a score; the legacy post-encounter review layer is absent;
* the faculty supervision page observes, reviews the replay (every check matches), inspects the trace, flags, marks unusable and stops an encounter -- and a stop ends the
  participant's encounter before their next order runs; faculty actions never touch the participant's log;
* refresh never resumes; an incomplete configuration, a broken record, the horizon, the participant's own end and an authority stop all end or refuse in the stated way.
"""
import json
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import development_management_trace as mt
import gi_pilot as gp
import runtime_authority as ra
import runtime_authority_store as ras
import runtime_ne_grant as ne_grant
import runtime_pressure_snapshot as ps
import runtime_shadow as rs
import runtime_tone_snapshot as tn
import test_gi_management_trace_paths as tp
import test_phase3_pair_page as page
from account_store import AccountStore, hash_password

pytestmark = pytest.mark.ordinary_configuration
ROOT = Path(__file__).resolve().parent
ADMIN = ("admin", "gi-pilot-admin-password")
EXPECTATION = "I expect the blood pressure and perfusion to improve."
ORDERS = (tp.VOL + " " + EXPECTATION, "Start norepinephrine at 10 mcg/min. Reassess in 15 minutes.")
REQUEST = "Call gastroenterology for urgent endoscopy."
INTERNALS = ("GRANT_V", "GI_NOREPINEPHRINE", "SNAPSHOT_V1", "GI_JOINT_PRESSURE", "COMMON_TONE", "tone_gain", "lineage", "digest", "phase3_", "PRESSURE_ONLY", "NONAUTHORITATIVE",
             "REASONABLE", "TEMPORIZING", "CLEARLY_NONBENEFICIAL", "INCOMPLETE", "Q6", "score", "Score", "rubric", "radar", "PE-", "P-", "F-", "proposed for faculty review",
             "Scenario priority", "bleed_rate", "preload", "candidate_digest")
LEGACY_REVIEW = ("Complete your independent reflection", "expert model", "Original decision-by-decision record", "analyzed Management Trace", "Compare your locked reflection")


def _environment(mp, tmp, **override):
    for name in list(__import__("os").environ):
        if name.startswith("MRS_") or name == "OPENAI_API_KEY":
            mp.delenv(name, raising=False)
    import runtime_pressure_grant as grants
    mp.delenv(grants.HISTORICAL_RECONSTRUCTION_FLAG, raising=False)
    env = {gp.FLAG: gp.MODE_ON, gp.STORE_FLAG: str(tmp / "pilot"), ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: ps.SNAPSHOT_ID, ra.TONE_FLAG: tn.SNAPSHOT_ID,
           ra.ENVIRONMENT_FLAG: "development", rs.FLAG: rs.MODE_SHADOW_COMPARE, ras.STORE_FLAG: str(tmp / "authority"), "MRS_OFFLINE_CASES": "1", "MRS_IMAGE_BANK": "off"}
    env.update(override)
    for name, value in env.items():
        if value is None:
            mp.delenv(name, raising=False)
        else:
            mp.setenv(name, value)


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("gi_pilot")
    url = "sqlite:///" + str(tmp / "accounts.sqlite3")
    accounts = AccountStore(url, allow_sqlite=True)
    accounts.bootstrap_admin(ADMIN[0], hash_password(ADMIN[1]))
    token = accounts.authenticate(*ADMIN)
    secrets = {"MRS_AUTH_MODE": "accounts", "MRS_DATABASE_URL": url, "MRS_ALLOW_LOCAL_SQLITE": True, "MRS_ADMIN_USERNAME": ADMIN[0], "MRS_ADMIN_PASSWORD_HASH": hash_password(ADMIN[1])}
    with pytest.MonkeyPatch.context() as mp:
        _environment(mp, tmp)
        yield {"mp": mp, "tmp": tmp, "accounts": accounts, "token": token, "secrets": secrets, "count": [0], "runs": {}}


def _account(world, role):
    world["count"][0] += 1
    name, password = f"{role}{world['count'][0]}", f"gi-pilot-{role}-password-{world['count'][0]}"
    invite = world["accounts"].create_invite(world["token"], role, 1) if role == "resident" else world["accounts"].create_invite(world["token"], role)
    world["accounts"].register(name, password, invite)
    return name, password


def _sign_in(world, credentials):
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=600)
    at.secrets.update(world["secrets"])
    at.run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    next(item for item in at.text_input if item.label == "Username").set_value(credentials[0])
    next(item for item in at.text_input if item.label == "Password").set_value(credentials[1])
    next(item for item in at.button if item.label == "Sign in").click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    return at


def _screen(at):
    parts = []
    for kind in ("markdown", "caption", "text", "title", "header", "subheader", "info", "warning", "error", "success"):
        parts.extend(str(item.value) for item in getattr(at, kind, []))
    parts.extend(str(item.label) for item in at.button)
    return "\n".join(parts)


def _begin(at):
    next(item for item in at.button if item.label == "Begin the development pilot encounter").click().run()
    assert not at.exception, [str(item.value)[:300] for item in at.exception]
    assert at.session_state["started"] is True


def _pilot(at):
    return at.session_state[gp.SESSION_KEY] if gp.SESSION_KEY in at.session_state else None


def _store(world):
    return gp.PilotStore(world["tmp"] / "pilot")


@pytest.fixture(scope="module")
def run_a(world):
    """The resident dry run (P3-528): volume and blood with the resident's expectation, norepinephrine, then the request for definitive control."""
    credentials = _account(world, "resident")
    at = _sign_in(world, credentials)
    launch = _screen(at)
    _begin(at)
    screens = {"launch": launch, "arrival": _screen(at)}
    for index, text in enumerate(ORDERS):
        page._order(at, text)
        screens[f"after_{index}"] = _screen(at)
    page._examine(at)
    screens["after_exam"] = _screen(at)
    before_request = {"sim": int(at.session_state["state"]["sim_time"]), "ledger": len(at.session_state["order_ledger"])}
    page._order(at, REQUEST)
    screens["after_request"] = _screen(at)
    at.run()
    screens["post"] = _screen(at)
    return {"at": at, "credentials": credentials, "screens": screens, "before_request": before_request, "eid": _pilot(at)["encounter_id"]}


def test_p1_the_participant_page_is_the_pilot_start_and_the_encounter_creates_no_attempt_in_the_account(world, run_a):
    launch = run_a["screens"]["launch"]
    assert gp.PILOT_NOTICE.split(" · ")[0] in launch and "Begin the development pilot encounter" in launch
    for word in ("Start encounter", "Your progress", "portfolio", "Choose a clinical problem"):
        assert word not in launch, word
    token = world["accounts"].authenticate(*run_a["credentials"])
    assert world["accounts"].list_attempts(token) == [], "the pilot encounter never creates an attempt: nothing reaches progress, portfolio, rubric or evaluation"
    assert dict(run_a["at"].session_state["encounter_assignment"])["reason"] == gp.ASSIGNMENT_REASON
    assert "_attempt_id" not in run_a["at"].session_state or run_a["at"].session_state["_attempt_id"] is None
    status = _store(world).status(run_a["eid"])
    assert status["case_id"] == "gi_bleed_57m" and status["participant"].startswith("P-") and status["participant"] != run_a["credentials"][0]


def test_p2_the_pressures_are_the_live_authority_s_and_the_headless_runner_s_and_the_record_holds_every_turn(world, run_a):
    site = run_a["at"].session_state[ra.SITE_KEY]
    assert site is not None and not site.halted
    run = tp.DevelopmentEncounter("gi_bleed_57m")
    for text in ORDERS:
        run.order(text)
    headless, live = mt.authority_points(run.artifact()), mt.authority_points(site.artifact())
    assert headless and all(live[minute]["pressure"] == point["pressure"] for minute, point in headless.items()), "the same orders give the same committed minutes"
    assert all(minute > max(headless) for minute in set(live) - set(headless)), "the page's only other minutes are the examination's clinical time, after the orders"
    logs = _store(world).logs(run_a["eid"])
    assert logs["problems"] == [] and sum(entry["kind"] == "turn" for entry in logs["participant"]) == len(run_a["at"].session_state["management_trace"])
    assert ra.verify_artifact(_store(world).artifact(run_a["eid"]))["digest_matches"]


def test_p3_mental_status_is_the_earlier_model_s_and_is_withheld_once_norepinephrine_was_given(run_a):
    before, after = run_a["screens"]["after_0"], run_a["screens"]["after_1"]
    assert gp.MENTAL_STATUS_LABEL in before and gp.MENTAL_STATUS_WITHHELD not in before
    assert "(mental status from the earlier simulator model)" in before and "Mental status (earlier model):" in before
    assert gp.MENTAL_STATUS_LABEL in after and gp.MENTAL_STATUS_WITHHELD in after and gp.MENTAL_STATUS_WITHHELD_NOTE in after
    assert not re.search(r"\b(Alert|Drowsy|Obtunded|Unresponsive); respiratory effort", after), "no patient-response card keeps the earlier model's word after norepinephrine"
    assert gp.APPEARANCE_MENTAL_WITHHELD in after and "Mental status (earlier model):" not in after
    exam = run_a["screens"]["after_exam"]
    assert not re.search(r"Current mental status:\s*[A-Z]", exam) and "engages in conversation" not in exam and "Engagement is reduced" not in exam, \
        "the examination never shows the earlier model's mental status after norepinephrine"


def test_p4_the_request_for_definitive_control_does_not_run_and_ends_the_encounter_at_the_boundary(world, run_a):
    at = run_a["at"]
    family = dict(at.session_state["state"].get("family_state") or {})
    assert not family.get("consultations") and family.get("endoscopy_at") is None
    assert int(at.session_state["state"]["sim_time"]) == run_a["before_request"]["sim"], "no clock moved"
    assert at.session_state["encounter_ended"] is True and _pilot(at)["exit"] == gp.EXIT_DEFINITIVE_REQUEST
    request_orders = at.session_state["order_ledger"][run_a["before_request"]["ledger"]:]
    assert request_orders and all(order["fate"] == "RECORDED_NOT_MODELLED" and "development pilot boundary" in str(order.get("reason")) for order in request_orders)
    assert all("Gastroenterology performed" not in str(event.get("text")) for event in at.session_state["events"])
    status = _store(world).status(run_a["eid"])
    assert status["state"] == "ENDED" and status["exit"] == gp.EXIT_DEFINITIVE_REQUEST
    assert mt.BOUNDARY_MESSAGE_REQUEST.split(".")[0] in run_a["screens"]["post"]


def test_p5_no_participant_screen_carries_an_internal_an_identifier_a_category_or_a_score(run_a):
    for name, screen in run_a["screens"].items():
        if name == "launch":
            continue
        for disclaimer in ("it is not a score, not a grade", "nothing here counts toward any grade"):
            screen = screen.replace(disclaimer, "")
        for word in INTERNALS:
            assert word not in screen, (name, word)
    for word in LEGACY_REVIEW:
        assert word not in run_a["screens"]["post"], word


def test_p6_the_participant_trace_is_the_reviewed_construct_with_their_own_words_and_every_order_said(run_a):
    post = run_a["screens"]["post"]
    assert "Your management trace" in post and gp.TRACE_INTRO.split(".")[0] in post
    assert EXPECTATION.rstrip(".") in post, "the resident's own expectation, exactly as written"
    assert "fluid normal saline 1000 mL: carried out" in post, "every order is said with what the simulator did with it"
    assert "consult gastroenterology: recorded and not carried out (development boundary)" in post
    assert "Development boundary" in post and "bleeding not controlled" in post


def test_p6b_the_resident_s_post_encounter_screen_teaches_no_misleading_lesson(run_a):
    """P3-530 on the real screen: support is not volume, fluid and blood do not stop the bleeding, a better pressure is not cure, the request for definitive control is
    not carried out, no reward or recommendation words in what the model says, no faculty category, no mental status in the trace."""
    import test_gi_pilot as unit
    post = run_a["screens"]["post"]
    model = [line for line in post.splitlines() if line.startswith(("**State:**", "**Expected (model):**", "**Observed:**", "**Reassessment:**", "**New state:**"))]
    assert len(model) >= 16, "four steps, each with the model's own lines"
    text = "\n".join(model)
    assert "does not replace volume" in text and "It does not stop the bleeding" in text and "They do not stop the bleeding" in text
    assert "temporary, not control of the bleeding" in text
    assert all("bleeding not controlled" in line or "Beyond the development boundary" in line for line in model if line.startswith("**New state:**"))
    assert "does not mean that the patient has recovered" in post and "consult gastroenterology: recorded and not carried out (development boundary)" in post
    assert not unit.REWARD_WORDS.search(text), unit.REWARD_WORDS.search(text)
    for word in ("REASONABLE", "TEMPORIZING", "INCOMPLETE", "NONBENEFICIAL", "Alert", "Drowsy", "consciousness", "mental status", "Mental status"):
        assert word not in text, word


@pytest.fixture(scope="module")
def faculty(world, run_a):
    """The faculty dry run (P3-529): the supervision page over the resident's ended encounter."""
    credentials = _account(world, "faculty")
    at = _sign_in(world, credentials)
    return {"at": at, "credentials": credentials}


def test_p7_the_faculty_observe_review_the_replay_inspect_flag_and_mark_unusable_without_touching_the_participant_log(world, run_a, faculty):
    at = faculty["at"]
    assert at.title[0].value == "GI development pilot · faculty supervision"
    folder = world["tmp"] / "pilot" / "encounters" / run_a["eid"]
    participant_bytes = (folder / gp.RESIDENT_LOG).read_bytes()
    next(item for item in at.selectbox if item.label == "Encounter").set_value(run_a["eid"]).run()
    next(item for item in at.button if item.label == "Review the replay").click().run()
    assert not at.exception and any("every check matches" in str(item.value) for item in at.success), [str(item.value) for item in at.error]
    next(item for item in at.button if item.label == "Inspect the trace").click().run()
    assert not at.exception and not [item for item in at.error if "does not verify" in str(item.value)]
    next(item for item in at.text_area if item.label.startswith("What is unsafe or ambiguous")).set_value("Synthetic dry-run flag: wording to discuss.").run()
    next(item for item in at.button if item.label == "Record the flag").click().run()
    next(item for item in at.text_input if item.label == "Why is this encounter unusable?").set_value("Dry run: synthetic account.").run()
    next(item for item in at.button if item.label == "Mark unusable").click().run()
    assert not at.exception
    faculty_log = [json.loads(line) for line in (folder / gp.FACULTY_LOG).read_text(encoding="utf-8").splitlines()]
    assert [entry["action"] for entry in faculty_log] == ["replay_review", "inspect_trace", "flag", "unusable"]
    assert all(entry["faculty"].startswith("F-") and faculty["credentials"][0] not in json.dumps(entry) for entry in faculty_log)
    assert (folder / gp.RESIDENT_LOG).read_bytes() == participant_bytes, "no faculty action touches the participant's log"
    status = _store(world).status(run_a["eid"])
    assert status["unusable"] and status["flags"] == 1


def test_p8_a_faculty_stop_ends_the_participant_s_encounter_before_their_next_order_runs(world, faculty):
    resident = _sign_in(world, _account(world, "resident"))
    _begin(resident)
    page._order(resident, ORDERS[0])
    eid = _pilot(resident)["encounter_id"]
    minute = int(resident.session_state["state"]["sim_time"])
    _store(world).append_faculty(eid, gp.faculty_ref(faculty["credentials"][0]), "stop", {"why": "dry run"})
    next(a for a in resident.text_area if a.label == "Enter your clinical reasoning and/or actions").set_value("Start norepinephrine at 10 mcg/min. Reassess in 15 minutes.")
    next(b for b in resident.button if b.label == "Send").click().run()
    assert not resident.exception, [str(item.value)[:300] for item in resident.exception]
    assert resident.session_state["encounter_ended"] is True and _pilot(resident)["exit"] == gp.EXIT_FACULTY_STOP
    assert int(resident.session_state["state"]["sim_time"]) == minute and not gp.norepinephrine_given(resident.session_state["order_ledger"]), "the order after the stop never ran"
    assert gp.FACULTY_STOP_MESSAGE.split(".")[0] in _screen(resident)


def test_p9_a_refresh_never_resumes_and_a_new_start_records_the_open_one_interrupted(world):
    credentials = _account(world, "resident")
    first = _sign_in(world, credentials)
    _begin(first)
    page._order(first, ORDERS[0])
    eid = _pilot(first)["encounter_id"]
    again = _sign_in(world, credentials)                               # a refresh, a new tab or a restart: a new browser session
    assert again.session_state["started"] is not True and "Begin the development pilot encounter" in _screen(again)
    _begin(again)
    assert _pilot(again)["encounter_id"] != eid and _store(world).status(eid)["state"] == "INTERRUPTED"


def test_p10_a_named_pilot_with_an_incomplete_configuration_refuses_before_anything_starts(world):
    with pytest.MonkeyPatch.context() as mp:
        mp.delenv(gp.STORE_FLAG, raising=False)
        resident = _sign_in(world, _account(world, "resident"))
        assert "DEVELOPMENT PILOT UNAVAILABLE" in _screen(resident) and "Begin the development pilot encounter" not in _screen(resident)
        assert gp.STORE_FLAG not in _screen(resident), "a participant is not shown the configuration"
        staff = _sign_in(world, _account(world, "faculty"))
        assert gp.STORE_FLAG in _screen(staff)


def test_p11_a_broken_record_ends_the_encounter_and_the_next_order_never_runs(world):
    resident = _sign_in(world, _account(world, "resident"))
    _begin(resident)
    page._order(resident, ORDERS[0])
    eid = _pilot(resident)["encounter_id"]
    minute = int(resident.session_state["state"]["sim_time"])
    (world["tmp"] / "pilot" / "encounters" / eid / gp.FACULTY_LOG).write_text("not a chained record\n", encoding="utf-8")
    next(a for a in resident.text_area if a.label == "Enter your clinical reasoning and/or actions").set_value("Reassess in 15 minutes.")
    next(b for b in resident.button if b.label == "Send").click().run()
    assert resident.session_state["encounter_ended"] is True and _pilot(resident)["exit"] == gp.EXIT_RECORD_UNAVAILABLE
    assert int(resident.session_state["state"]["sim_time"]) == minute


def test_p12_the_two_hour_horizon_ends_the_encounter_at_the_development_boundary(world):
    resident = _sign_in(world, _account(world, "resident"))
    _begin(resident)
    for text in (ORDERS[0], "Reassess in 60 minutes.", "Reassess in 60 minutes."):
        page._order(resident, text)
        if resident.session_state["encounter_ended"]:
            break
    resident.run()
    assert resident.session_state["encounter_ended"] is True and _pilot(resident)["exit"] == gp.EXIT_HORIZON
    assert mt.BOUNDARY_MESSAGE.split(".")[0] in _screen(resident) and "two hours after arrival" in _screen(resident)


def test_p13_the_participant_can_end_the_encounter_and_the_trace_says_what_ending_means(world):
    resident = _sign_in(world, _account(world, "resident"))
    _begin(resident)
    page._order(resident, ORDERS[0])
    next(item for item in resident.button if "Complete Encounter" in item.label).click().run()
    finish = next((item for item in resident.button if item.label == "Finish now"), None)
    if finish is not None:
        finish.click().run()
    resident.run()
    assert resident.session_state["encounter_ended"] is True and _pilot(resident)["exit"] == gp.EXIT_PARTICIPANT_FINISHED
    assert gp.FINISHED_MESSAGE.split(".")[0] in _screen(resident) and "Your management trace" in _screen(resident)


def test_p14_an_order_the_authority_does_not_represent_stops_the_experiment_with_the_operational_message(world):
    resident = _sign_in(world, _account(world, "resident"))
    _begin(resident)
    page._order(resident, ORDERS[0])
    page._order(resident, "Give tranexamic acid 1 g IV over 10 minutes.")
    resident.run()
    assert resident.session_state["encounter_ended"] is True and _pilot(resident)["exit"] == gp.EXIT_AUTHORITY_STOP
    screen = _screen(resident)
    assert mt.AUTHORITY_STOP_MESSAGE.split(",")[0] in screen
    for word in ("death", "died", "cardiac arrest", "terminal"):
        assert word not in screen.lower()


def test_p15_without_the_pilot_flag_the_page_is_the_ordinary_one(world):
    with pytest.MonkeyPatch.context() as mp:
        mp.delenv(gp.FLAG, raising=False)
        resident = _sign_in(world, _account(world, "resident"))
        screen = _screen(resident)
        assert "GI development pilot" not in screen and "Begin the development pilot encounter" not in screen
        decision = dict(resident.session_state[gp.DECISION_KEY]) if gp.DECISION_KEY in resident.session_state else {}
        assert not decision.get("enabled")


def test_p16_after_the_first_commit_an_incomplete_order_is_a_clarification_noop_and_the_encounter_goes_on(world):
    """P3-532 pinned the pre-existing rule (MINUTE_ALREADY_COMMITTED stopped the experiment on an incomplete order after the first commit). DECLARED ADAPTATION (P3-537,
    FD-FINALPILOT-01 to 04): the faculty decided that a PROVEN clarification no-op preserves the authority on the same committed minute. The same turn is now held, recorded on
    the same minute, and the encounter goes on; what fails closed (an unsafe or unprovable same-minute turn) is pinned in ``test_gi_final_pilot.py``."""
    resident = _sign_in(world, _account(world, "resident"))
    assert "holds it and asks what is missing" in _screen(resident)
    _begin(resident)
    page._order(resident, ORDERS[0])
    minute = int(resident.session_state["state"]["sim_time"])
    next(a for a in resident.text_area if a.label == "Enter your clinical reasoning and/or actions").set_value("Give normal saline.")
    next(b for b in resident.button if b.label == "Send").click().run()
    resident.run()
    site = resident.session_state[ra.SITE_KEY]
    assert not site.halted, site.halt_reason
    assert site.no_advance_turns[-1]["outcome"] == ra.NONADVANCING_CLARIFICATION_NOOP and site.no_advance_turns[-1]["attached_to_committed_minute"] == minute
    assert resident.session_state["encounter_ended"] is not True and _pilot(resident)["exit"] is None
    assert int(resident.session_state["state"]["sim_time"]) == minute and resident.session_state["pending_action"]


# -- P3-531: the independent review's material findings, pinned on the real page -----------------------------------------------------------

SPANISH_MENTAL_WORDS = ("Alerta", "Somnoliento", "Somnolienta", "Confuso", "Confusa", "Obnubilado", "Estuporoso")


def test_p17_a_participant_who_chose_spanish_never_reads_the_earlier_model_s_mental_status_after_norepinephrine(world):
    """F1: the pilot runs in English, and it classifies the ENGLISH words before any translation, so the presentation language cannot carry the mental status past it."""
    resident = _sign_in(world, _account(world, "resident"))
    next(item for item in resident.selectbox if item.label == "Idioma · Language").set_value("es").run()
    _begin(resident)
    assert resident.session_state["encounter_language"] == "en", "the development pilot is presented in English only"
    for text in ORDERS:
        page._order(resident, text)
    page._examine(resident)
    during = _screen(resident)
    for word in SPANISH_MENTAL_WORDS + ("Alert;", "Mental status: Alert", "Drowsy"):
        assert word not in during, word
    page._order(resident, REQUEST)
    resident.run()
    assert resident.session_state["encounter_ended"] is True
    next(item for item in resident.selectbox if item.label == "Idioma · Language").set_value("es").run()     # after the close the reader may choose the language again
    assert not resident.exception, [str(item.value)[:300] for item in resident.exception]
    after = _screen(resident)
    events = [line for line in after.splitlines() if "esfuerzo respiratorio" in line or "respiratory effort" in line or "Expresión" in line or "Expression:" in line]
    assert events, "the patient-response and examination events are on the closed page"
    for line in events:
        for word in SPANISH_MENTAL_WORDS + ("Alert;", "Alert.", "Drowsy"):
            assert word not in line, (word, line)


def test_p18_an_encounter_another_tab_interrupted_never_runs_another_order(world):
    """F2: the same participant in two tabs; the second start records the first INTERRUPTED, and the first ends on its own next run without carrying the order out."""
    credentials = _account(world, "resident")
    tab_a = _sign_in(world, credentials)
    _begin(tab_a)
    page._order(tab_a, ORDERS[0])
    eid_a = _pilot(tab_a)["encounter_id"]
    minute = int(tab_a.session_state["state"]["sim_time"])
    tab_b = _sign_in(world, credentials)
    _begin(tab_b)
    assert _store(world).status(eid_a)["state"] == "INTERRUPTED"
    next(a for a in tab_a.text_area if a.label == "Enter your clinical reasoning and/or actions").set_value("Give 2 units of packed red cells. Reassess in 15 minutes.")
    next(b for b in tab_a.button if b.label == "Send").click().run()
    assert not tab_a.exception, [str(item.value)[:300] for item in tab_a.exception]
    assert tab_a.session_state["encounter_ended"] is True and _pilot(tab_a)["exit"] == gp.EXIT_CLOSED_IN_RECORD
    assert int(tab_a.session_state["state"]["sim_time"]) == minute, "the order after the interruption never ran"
    kinds = [entry["kind"] for entry in _store(world).logs(eid_a)["participant"]]
    assert "turn" not in kinds[kinds.index("interrupted"):], kinds
    assert gp.CLOSED_IN_RECORD_MESSAGE.split(".")[0] in _screen(tab_a)
    assert _store(world).status(_pilot(tab_b)["encounter_id"])["state"] == "ACTIVE", "the new encounter is the one that runs"


def test_p19_patient_photographs_switched_on_in_the_deployment_s_secrets_refuse_the_pilot(world):
    """F4: the image bank reads the secrets first; the pilot refuses whichever source turns it on."""
    secret_world = dict(world, secrets=dict(world["secrets"], MRS_IMAGE_BANK="on"))
    resident = _sign_in(secret_world, _account(world, "resident"))
    assert "DEVELOPMENT PILOT UNAVAILABLE" in _screen(resident) and "Begin the development pilot encounter" not in _screen(resident)
