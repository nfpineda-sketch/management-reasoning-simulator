"""P3-520 to P3-527 (module level): the controlled development pilot's policy (``gi_pilot``) -- configuration that fails closed, the development boundary before definitive
control of the bleeding, the classification of what a participant sees, the de-identified pilot record, the participant trace and the replay review, the scope and the
fail-safe rules. The page-level proof is ``test_gi_pilot_page.py``.
"""
import json
import os
import re
from pathlib import Path

import pytest

import development_management_trace as mt
import gi_pilot as gp
import runtime_authority as ra
import runtime_authority_store as ras
import runtime_pressure_snapshot as ps
import runtime_shadow as rs
import runtime_tone_snapshot as tn
import test_gi_management_trace_paths as tp

pytestmark = pytest.mark.ordinary_configuration
ROOT = Path(__file__).resolve().parent
#: What the page's crossing hands over (P3-532), built here the way ``app.py`` builds it; the site helper is not needed by the module-level tests.
LAYER = gp.layer_from(ra, rs, lambda: None)


def _environment(tmp_path, **override):
    env = {gp.FLAG: "on", gp.STORE_FLAG: str(tmp_path / "pilot"), ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: ps.SNAPSHOT_ID, ra.TONE_FLAG: tn.SNAPSHOT_ID,
           ra.ENVIRONMENT_FLAG: "development", rs.FLAG: rs.MODE_SHADOW_COMPARE, ras.STORE_FLAG: str(tmp_path / "authority"), "MRS_OFFLINE_CASES": "1", "MRS_IMAGE_BANK": "off"}
    env.update(override)
    return {key: value for key, value in env.items() if value is not None}


# -- configuration -------------------------------------------------------------------------------------------------------------------------

def test_u1_the_pilot_is_off_unless_named_and_a_complete_configuration_enables_it(tmp_path):
    assert gp.evaluate({}, accounts=True, on_cloud=False) == {"requested": False, "enabled": False, "problems": []}
    decision = gp.evaluate(_environment(tmp_path), accounts=True, on_cloud=False, layer=LAYER)
    assert decision["requested"] and decision["enabled"] and decision["problems"] == []
    # P3-532: a requested pilot the page handed no layer is refused, never run without its authority configuration
    refused = gp.evaluate(_environment(tmp_path), accounts=True, on_cloud=False)
    assert refused["requested"] and not refused["enabled"] and any("cannot be read" in problem for problem in refused["problems"])


@pytest.mark.parametrize("override, accounts, on_cloud, secret, words", [
    ({gp.FLAG: "yes"}, True, False, None, "must be 'on'"),
    ({}, False, False, None, "individual accounts"),
    ({}, True, True, None, "hosted public deployment"),
    ({"MRS_FACULTY_DEVELOPMENT_REVIEW": "on"}, True, False, None, "separate mode"),
    ({ra.AUTHORITY_FLAG: None}, True, False, None, ra.AUTHORITY_FLAG),
    ({ra.SNAPSHOT_FLAG: "GI_DEVELOPMENT_SNAPSHOT_V1"}, True, False, None, ra.SNAPSHOT_FLAG),
    ({ra.TONE_FLAG: None}, True, False, None, ra.TONE_FLAG),
    ({ra.ENVIRONMENT_FLAG: "faculty"}, True, False, None, ra.ENVIRONMENT_FLAG),
    ({rs.FLAG: None}, True, False, None, rs.FLAG),
    ({gp.STORE_FLAG: None}, True, False, None, "not set"),
    ({gp.STORE_FLAG: "relative/dir"}, True, False, None, "absolute"),
    ({gp.STORE_FLAG: str(ROOT / "pilot_store")}, True, False, None, "outside the repository"),
    ({"OPENAI_API_KEY": "sk-test-not-a-key"}, True, False, None, "no AI call"),
    ({}, True, False, {"OPENAI_API_KEY": "sk-test-not-a-key"}.get, "no AI call"),
    ({"MRS_IMAGE_BANK": None}, True, False, None, "MRS_IMAGE_BANK"),
    ({"MRS_IMAGE_REQUIRE_REVIEW": "1"}, True, False, None, "first resident pilot"),
    ({"MRS_PILOT_RESIDENTS": "1"}, True, False, None, "first resident pilot"),
    # P3-531 F4, F5, F6: a refusal never depends on where the operator put the setting
    ({}, True, False, {"MRS_IMAGE_BANK": "on"}.get, "MRS_IMAGE_BANK must be off wherever it is set"),
    ({"MRS_IMAGE_BANK": "on"}, True, False, {"MRS_IMAGE_BANK": "off"}.get, "MRS_IMAGE_BANK must be off wherever it is set"),
    ({}, True, False, {"MRS_PILOT_RESIDENTS": "1"}.get, "first resident pilot"),
    ({}, True, False, {"MRS_PILOT": "1"}.get, "first resident pilot"),
    ({}, True, False, {"MRS_FACULTY_DEVELOPMENT_REVIEW": "on"}.get, "separate mode"),
    ({ras.STORE_FLAG: None}, True, False, None, ras.STORE_FLAG),
])
def test_u2_every_condition_the_pilot_cannot_verify_is_a_refusal_that_names_itself(tmp_path, override, accounts, on_cloud, secret, words):
    env = _environment(tmp_path)
    for key, value in override.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    decision = gp.evaluate(env, accounts=accounts, on_cloud=on_cloud, secret=secret, layer=LAYER)
    assert decision["requested"] and not decision["enabled"]
    assert any(words in problem for problem in decision["problems"]), decision["problems"]
    assert not (ROOT / "pilot_store").exists(), "a refused store inside the repository is never created"


# -- the boundary (P3-521) -----------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("order", [
    {"class": "consult", "canonical": "consult gastroenterology", "span": "Call gastroenterology for urgent endoscopy"},
    {"class": "consult", "canonical": "consult GI", "span": "Consult GI"},
    {"class": "consult", "canonical": "consult surgery", "span": "Call the surgeons"},
    {"class": "unrecognized", "canonical": None, "span": "Arrange an urgent upper endoscopy"},
    {"class": "unrecognized", "canonical": None, "span": "Page the GI fellow"},
    {"class": "endoscopy", "canonical": "endoscopy", "span": "Get an urgent OGD"},
    {"class": "procedure", "canonical": "procedure", "span": "embolization"},
    {"class": "plan", "canonical": "plan interventional radiology embolization", "span": "IR for embolization"},
])
def test_u3_a_request_for_definitive_control_is_found_before_the_engine_runs_whatever_the_engine_would_do(order):
    assert gp.definitive_orders([order]) == [order]


@pytest.mark.parametrize("order", [
    {"class": "fluid", "canonical": "normal saline 1000 mL over 15 min", "span": "for the GI bleed give 1 litre of normal saline"},
    {"class": "blood", "canonical": "packed red cells 2 units", "span": "Transfuse 2 units of packed red cells"},
    {"class": "ppi", "canonical": "pantoprazole", "span": "Start a pantoprazole infusion"},
    {"class": "norepinephrine", "canonical": "norepinephrine 10 mcg/min", "span": "Start norepinephrine at 10 mcg/min"},
    {"class": "reassessment", "canonical": "reassess 15", "span": "Reassess in 15 minutes"},
])
def test_u4_ordinary_resuscitation_orders_are_never_the_boundary_even_when_they_name_the_bleed(order):
    assert gp.definitive_orders([order]) == []


def test_u5_the_structural_barrier_reads_the_engine_state_itself():
    assert gp.engine_source_control({}) == [] and gp.engine_source_control({"family_state": {"consultations": []}}) == []
    assert gp.engine_source_control({"family_state": {"consultations": [{"service": "gastroenterology", "time_min": 0}]}})
    assert gp.engine_source_control({"family_state": {"endoscopy_at": 75}})
    assert gp.engine_source_control({"family_state": {"procedure_events": [{"type": "procedure", "label": "Gastroenterology performed upper endoscopy: bleeding ulcer treated endoscopically; active bleeding controlled."}]}})
    assert gp.engine_source_control({"family_state": {"consultations": [{"service": "ICU", "time_min": 0}]}}) == []


# -- what the participant sees (P3-522) ----------------------------------------------------------------------------------------------------

CELLS = (("SIM TIME", "15 min"), ("BP · MAP", "94/58 · MAP 70"), ("HR", "112/min"), ("MENTAL STATUS", "Alert"))


def test_u6_mental_status_is_the_earlier_models_and_is_withheld_once_norepinephrine_was_given():
    before = dict(gp.display_cells(CELLS, False))
    assert before[gp.MENTAL_STATUS_LABEL] == "Alert" and "MENTAL STATUS" not in before and before["BP · MAP"] == "94/58 · MAP 70"
    after = dict(gp.display_cells(CELLS, True))
    assert after[gp.MENTAL_STATUS_LABEL] == gp.MENTAL_STATUS_WITHHELD and "Alert" not in after.values()
    text = "BP 64/40 mmHg · HR 120/min · SpO₂ 97% · RR 22/min. Alert; respiratory effort normal; capillary refill 3 s."
    assert gp.display_update_text(text, False) == text.replace("Alert;", "Alert (mental status from the earlier simulator model);")
    withheld = gp.display_update_text(text, True)
    assert "Alert" not in withheld and gp.UPDATE_MENTAL_WITHHELD in withheld and "BP 64/40" in withheld
    assert "Drowsy" not in gp.display_update_text("The patient is Drowsy and pale.", True), "an unknown sentence fails closed after norepinephrine"
    assert "obtunded" not in gp.display_update_text("Now obtunded, pale and cold.", True).lower(), "the fail-closed vocabulary ignores case"
    twice = gp.display_update_text(text + " Earlier the patient was Drowsy.", True)
    assert "Alert" not in twice and "Drowsy" not in twice and twice.count(gp.UPDATE_MENTAL_WITHHELD) == 2, "a second mention is withheld too"
    assert gp.display_update_text("The patient is Drowsy and pale.", False) == "The patient is Drowsy and pale.", "before norepinephrine an unknown sentence is left as it is"
    assert gp.display_appearance("Mental status: Alert. Color: pale.", False) == "Mental status (earlier model): Alert. Color: pale."
    assert gp.display_appearance("Mental status: Alert. Color: pale.", True) == gp.APPEARANCE_MENTAL_WITHHELD + ". Color: pale."


def test_u7_norepinephrine_counts_as_given_only_when_the_engine_carried_it_out():
    assert not gp.norepinephrine_given([]) and not gp.norepinephrine_given([{"class": "norepinephrine", "canonical": "norepinephrine 10 mcg/min", "fate": "HELD_CLARIFICATION"}])
    assert gp.norepinephrine_given([{"class": "norepinephrine", "canonical": "norepinephrine 10 mcg/min", "fate": "EXECUTED"}])


def test_u8_every_visible_field_is_classified_and_the_internals_are_hidden():
    classes = {field: cls for field, cls, _ in gp.FIELD_CLASSES}
    assert classes["blood pressure (SBP/DBP) and MAP"] == gp.AUTHORITATIVE and classes["mental status"] == gp.LEGACY_NONAUTHORITATIVE
    hidden = " ".join(field for field, cls, _ in gp.FIELD_CLASSES if cls == gp.HIDDEN)
    for word in ("V, T, tone gain", "grant, snapshot", "consciousness", "faculty management categories", "participant reference"):
        assert word in hidden
    assert set(cls for _, cls, _ in gp.FIELD_CLASSES) <= {gp.AUTHORITATIVE, gp.LEGACY_NONAUTHORITATIVE, gp.DEVELOPMENT_ONLY, gp.HIDDEN}
    assert "mental status" in gp.PILOT_NOTICE and "not an assessment" in gp.PILOT_NOTICE


def test_u9_the_scope_excludes_everything_the_faculty_excluded_and_names_one_reviewed_case():
    assert gp.PILOT_CASES == ("gi_bleed_57m",)
    excluded = " ".join(text for dimension in gp.SCOPE.values() for text in dimension.get(gp.EXCLUDED, ()))
    for word in ("pump-limited", "pulmonary edema", "ACS", "other vasopressors", "target-based", "weight-based", "score", "faculty management categories", "AI call", "definitive control"):
        assert word in excluded, word
    assert set(gp.SCOPE) == {"cases", "interventions", "visible_outputs", "trace_fields", "faculty_controls"}
    for situation in ("authority mismatch", "malformed vasopressor order", "pilot record unavailable", "replay mismatch", "definitive control", "faculty abort", "refresh",
                      "process restart", "two-hour"):
        assert any(situation in row[0] for row in gp.FAIL_SAFE), situation


# -- the pilot record (P3-525) -------------------------------------------------------------------------------------------------------------

def _store(tmp_path):
    return gp.PilotStore(tmp_path / "pilot")


def test_u10_the_record_names_no_person_and_its_identifiers_are_synthetic(tmp_path):
    store = _store(tmp_path)
    participant = gp.participant_ref(4321)
    assert participant.startswith("P-") and "4321" not in participant and participant == gp.participant_ref(4321) and participant != gp.participant_ref(4322)
    assert gp.faculty_ref(4321).startswith("F-") and gp.faculty_ref(4321) != participant
    eid = store.new_encounter(participant=participant, case_id="gi_bleed_57m", arrival={"sbp": 88, "dbp": 54, "map": 65}, configuration={"grant": "X"})
    assert gp.ENCOUNTER_ID.match(eid)
    text = "".join(path.read_text(encoding="utf-8") for path in (tmp_path / "pilot").rglob("*") if path.is_file())
    for word in ("4321", "resident1", "username", "@"):
        assert word not in text
    with pytest.raises(gp.PilotRecordError):
        store.new_encounter(participant=participant, case_id="gi_bleed_72f", arrival={}, configuration={})


def test_u11_the_participant_and_the_faculty_write_separate_chained_logs_and_a_broken_chain_fails_closed(tmp_path):
    store = _store(tmp_path)
    eid = store.new_encounter(participant=gp.participant_ref(1), case_id="gi_bleed_57m", arrival={"sbp": 88, "dbp": 54, "map": 65}, configuration={})
    store.append_participant(eid, "turn", {"minute": 15, "event": {"learner_input": "x"}})
    store.append_faculty(eid, gp.faculty_ref(2), "flag", {"category": "AMBIGUOUS", "note": "n"})
    with pytest.raises(gp.PilotRecordError):
        store.append_faculty(eid, gp.faculty_ref(2), "flag", {"category": "MAYBE"})
    with pytest.raises(gp.PilotRecordError):
        store.append_faculty(eid, "P-123", "stop", {})
    with pytest.raises(gp.PilotRecordError):
        store.append_participant(eid, "stop", {})
    folder = tmp_path / "pilot" / "encounters" / eid
    assert (folder / gp.RESIDENT_LOG).exists() and (folder / gp.FACULTY_LOG).exists()
    assert store.controls(eid) == {"stop_requested": False, "unusable": False, "flags": [{"category": "AMBIGUOUS", "note": "n"}]}
    store.append_faculty(eid, gp.faculty_ref(2), "stop", {})
    assert store.controls(eid)["stop_requested"] and store.status(eid)["stop_requested"]
    lines = (folder / gp.FACULTY_LOG).read_text(encoding="utf-8").splitlines()
    tampered = json.loads(lines[0])
    tampered["payload"]["category"] = "UNSAFE"
    (folder / gp.FACULTY_LOG).write_text("\n".join([json.dumps(tampered)] + lines[1:]) + "\n", encoding="utf-8")
    with pytest.raises(gp.PilotRecordError):
        store.controls(eid)
    assert store.status(eid)["state"] == "RECORD_PROBLEM"
    with pytest.raises(gp.PilotRecordError):
        store.append_faculty(eid, gp.faculty_ref(2), "unusable", {"reason": "r"})


def test_u12_an_open_encounter_is_known_and_a_closing_trace_is_written_once(tmp_path):
    store = _store(tmp_path)
    participant = gp.participant_ref(7)
    eid = store.new_encounter(participant=participant, case_id="gi_bleed_57m", arrival={"sbp": 88, "dbp": 54, "map": 65}, configuration={})
    assert store.open_encounters_of(participant) == [eid] and store.open_encounters_of(gp.participant_ref(8)) == []
    store.append_participant(eid, "interrupted", {"why": "w"})
    assert store.open_encounters_of(participant) == [] and store.status(eid)["state"] == "INTERRUPTED"
    store.write_trace(eid, {"trace_digest": "a"})
    store.write_trace(eid, {"trace_digest": "a"})
    with pytest.raises(gp.PilotRecordError):
        store.write_trace(eid, {"trace_digest": "b"})
    with pytest.raises(gp.PilotRecordError):
        store.meta("../../etc")


# -- the participant trace and the replay (P3-523, P3-525) ---------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def played():
    """One encounter through the live development authority (the page's order path), as the pilot record would hold it."""
    import runtime_pressure_grant as grants
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.delenv(grants.HISTORICAL_RECONSTRUCTION_FLAG, raising=False)
        run = tp.DevelopmentEncounter("gi_bleed_57m")
        for text in (tp.VOL, "Put the patient in the Trendelenburg position.", "Reassess in 60 minutes.", "Start norepinephrine at 10 mcg/min. Reassess in 15 minutes."):
            run.order(text)
        yield {"run": run, "artifact": gp.plain(run.artifact()), "arrival": dict(run.arrival["observable"])}


def test_u13_the_participant_trace_is_the_reviewed_construct_with_every_order_said_and_nothing_internal(played):
    turns = [mt.turn_from_runner_entry(entry) for entry in played["run"].entries]
    trace = mt.extract(turns, played["artifact"], {key: played["arrival"][key] for key in ("sbp", "dbp")} | {"map": ra.derived_map(played["arrival"]["sbp"], played["arrival"]["dbp"])})
    raw = mt.trace_problems(trace, turns)
    assert raw == [gp.CARRIED_READING_PROBLEM.format(n=2)], "the construct's verifier over-rejects the carried reading of the no-advance turn (declared, TD-165)"
    assert gp.carried_reading_tolerated(trace, raw) == [], "the pilot tolerates exactly that case"
    forged = json.loads(json.dumps(trace))
    forged["steps"][1]["new_state"]["pressure"]["value"] = {"sbp": 140, "dbp": 90, "map": 107}
    assert gp.carried_reading_tolerated(forged, [gp.CARRIED_READING_PROBLEM.format(n=2)]) == [gp.CARRIED_READING_PROBLEM.format(n=2)], "a carried reading that is not the state is never tolerated"
    moved = json.loads(json.dumps(trace))
    moved["steps"][1]["response_minute"]["value"] = moved["steps"][1]["decision_minute"]["value"] + 15
    assert gp.carried_reading_tolerated(moved, [gp.CARRIED_READING_PROBLEM.format(n=2)]) != [], "a turn that moved the clock needs its committed minute"
    blocks = mt.render(trace)
    for block, step in zip(blocks, trace["steps"]):
        block["order_words"] = [f"{row['order']}: {gp.fate_words(row['fate'])}" for row in step["action"]["orders"]["value"] if row["class"] != "reassessment" and row["order"]]
    words = " ".join(" ".join(block.get("order_words") or ()) for block in blocks)
    assert "not understood by the simulator; nothing was done" in words and "carried out" in words
    text = " ".join(line["text"] + " " + line["label"] for block in blocks for line in block["lines"] if line["provenance"] != mt.RESIDENT_EXPRESSED)
    for word in gp.FORBIDDEN_ON_PARTICIPANT_TRACE:
        assert word not in text, word


def test_u14_the_replay_review_matches_a_true_record_and_finds_a_tampered_artifact(tmp_path, played):
    store = _store(tmp_path)
    arrival = {"sbp": played["arrival"]["sbp"], "dbp": played["arrival"]["dbp"], "map": ra.derived_map(played["arrival"]["sbp"], played["arrival"]["dbp"])}
    eid = store.new_encounter(participant=gp.participant_ref(9), case_id="gi_bleed_57m", arrival=arrival, configuration={})
    store.write_artifact(eid, played["artifact"])
    review = gp.replay_review(store, eid, LAYER)
    assert review["checks"]["logs_chain"] == "MATCH" and review["checks"]["artifact_verifies"] == "MATCH" and review["checks"]["artifact_reproduces"] == "MATCH"
    assert review["checks"]["trace_reextracts"] == "MISSING" and not review["usable"], "no closing trace yet: not usable"
    tampered = json.loads(json.dumps(played["artifact"]))
    first = next(item for item in tampered["minutes"] if item.get("outcome") == "COMMITTED")
    first["written_candidate"]["sbp"] = int(first["written_candidate"]["sbp"]) + 10
    store.write_artifact(eid, tampered)
    review = gp.replay_review(store, eid, LAYER)
    assert review["checks"]["artifact_verifies"] == "MISMATCH" and not review["usable"]


def test_u15_a_participant_trace_without_an_artifact_is_withheld():
    result = gp.participant_trace([], None, {"sbp": 88, "dbp": 54, "map": 65})
    assert not result["ok"] and result["blocks"] == []
    assert "not shown" in gp.TRACE_WITHHELD and "score" not in gp.TRACE_WITHHELD


def test_u16_the_exit_messages_never_claim_an_outcome():
    for kind, message in gp.EXIT_MESSAGES.items():
        assert kind in gp.EXITS
        lower = message.lower()
        for word in ("recovered and", "cured", "stable", "safe for discharge", "management complete", "bleeding controlled", "died", "death"):
            assert word not in lower, (kind, word)


def test_u17_an_examination_keeps_its_findings_and_classifies_or_withholds_the_earlier_model_s_mental_status():
    general = "Mental status: Alert. Expression: uncomfortable. Color: mild pallor."
    neuro = "Current mental status: Drowsy. Engagement is reduced; interpret alongside respiratory and circulatory findings. Pupils equal and reactive."
    assert gp.display_examination(general, False) == "Mental status (earlier model): Alert. Expression: uncomfortable. Color: mild pallor."
    assert gp.display_examination(neuro, False).startswith("Current mental status (earlier model): Drowsy.")
    after = gp.display_examination(general + "\n" + neuro, True)
    for word in ("Alert", "Drowsy", "Engagement is reduced", "engages in conversation"):
        assert word not in after, word
    assert "Expression: uncomfortable" in after and "Pupils equal and reactive." in after, "the other findings stay"


# -- educational safety attacks on the participant trace (P3-530) ----------------------------------------------------------------------------

REWARD_WORDS = re.compile(r"\b(recommended|correct(?:ly)?|well done|good (?:management|choice|job)|appropriate|optimal|successful(?:ly)?|resuscitated|shock (?:corrected|resolved)|"
                          r"stabili[sz]ed|bleeding (?:stopped|controlled)|hemorrhage controlled|haemorrhage controlled|cured|recovered and)\b", re.IGNORECASE)


def test_u18_the_participant_trace_never_teaches_a_misleading_lesson(played):
    """The nine attacks of P3-530 on the trace a participant reads: vasopressor as a substitute for volume, blood or fluid stopping the bleeding, a normal pressure as cure, waiting
    as harmless, mental status validated, unreviewed haemostasis, a negative path as recommended, a faculty category as a score, invented reasoning."""
    turns = [mt.turn_from_runner_entry(entry) for entry in played["run"].entries]
    arrival = {key: played["arrival"][key] for key in ("sbp", "dbp")} | {"map": ra.derived_map(played["arrival"]["sbp"], played["arrival"]["dbp"])}
    blocks = mt.render(mt.extract(turns, played["artifact"], arrival))
    lines = [line for block in blocks for line in block["lines"]]
    model_text = " ".join(line["text"] for line in lines if line["provenance"] != mt.RESIDENT_EXPRESSED)
    assert not REWARD_WORDS.search(model_text), REWARD_WORDS.search(model_text)
    expected = [line["text"] for line in lines if line["label"] == "Expected (model)"]
    assert any("does not replace volume" in text and "does not stop the bleeding" in text for text in expected), "the vasopressor is support, not volume"
    assert any("Crystalloid" in text and "It does not stop the bleeding" in text for text in expected) and any("Red cells" in text and "do not stop the bleeding" in text for text in expected)
    assert any(text.startswith("Time passes. The bleeding continues.") for text in expected), "waiting is never neutral"
    new_states = [line["text"] for line in lines if line["label"] == "New state"]
    assert new_states and all("bleeding not controlled" in text for text in new_states), "a better pressure is never cure"
    assert any("temporary, not control of the bleeding" in line["text"] for line in lines if line["label"] == "Reassessment")
    for word in ("Alert", "Drowsy", "Confused", "mental status", "Mental status", "consciousness"):
        assert word not in model_text, word
    for line in lines:
        if line["provenance"] == mt.RESIDENT_EXPRESSED:
            assert line["text"].endswith("not expressed"), "a scripted turn expressed nothing and nothing is invented"
    for word in gp.FORBIDDEN_ON_PARTICIPANT_TRACE:
        assert word not in model_text, word



# -- P3-531: the independent review's findings, pinned -----------------------------------------------------------------------------------

def test_u19_concurrent_writers_never_fork_a_chain_and_the_write_check_never_collides(tmp_path):
    """F3: the sessions of the one Streamlit process are threads; appends are one locked step and the store's write check is unique per call."""
    import threading
    store = _store(tmp_path)
    eid = store.new_encounter(participant=gp.participant_ref(1), case_id="gi_bleed_57m", arrival={"sbp": 88, "dbp": 54, "map": 65}, configuration={})
    failures = []

    def faculty(n):
        for i in range(40):
            try:
                store.append_faculty(eid, gp.faculty_ref(n), "observe", {"i": i})
            except Exception as error:                       # pragma: no cover - the failure is what the test looks for
                failures.append(repr(error))

    def gate():
        for _ in range(150):
            if gp.store_root({gp.STORE_FLAG: str(tmp_path / "pilot")})[1]:
                failures.append("write check refused")

    threads = [threading.Thread(target=faculty, args=(n,)) for n in range(6)] + [threading.Thread(target=gate) for _ in range(4)]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
    assert failures == []
    logs = store.logs(eid)
    assert logs["problems"] == [] and len(logs["faculty"]) == 240
    assert store.controls(eid)["stop_requested"] is False and store.status(eid)["state"] == "ACTIVE"


def test_u20_an_order_the_ledger_holds_as_an_internal_token_is_said_in_the_participant_s_words():
    """F8: "unread", "plan:future_timed" or "held_with_question" are never shown; the participant's own words are, quoted."""
    spans = {1: "Put the patient in the Trendelenburg position", 2: "Reassess later"}
    assert gp.order_label({"order_id": 1, "order": "unread"}, spans) == '"Put the patient in the Trendelenburg position"'
    assert gp.order_label({"order_id": 2, "order": "plan:future_timed"}, spans) == '"Reassess later"'
    assert gp.order_label({"order_id": 3, "order": "held_with_question"}, spans) == "an order"
    assert gp.order_label({"order_id": 4, "order": "fluid normal saline 1000 mL"}, spans) == "fluid normal saline 1000 mL"


def test_u21_an_encounter_the_record_closed_elsewhere_has_its_own_exit_message():
    assert gp.EXIT_CLOSED_IN_RECORD in gp.EXITS and "does not continue here" in gp.EXIT_MESSAGES[gp.EXIT_CLOSED_IN_RECORD]
    assert any(row[2] == gp.EXIT_CLOSED_IN_RECORD for row in gp.FAIL_SAFE)


# -- P3-532: the pilot imports nothing of the Phase-3 layer; the page's crossing hands it a narrow, read-only layer -------------------------

def _imports(path):
    import ast
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names} | \
           {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}


def test_u22_the_pilot_modules_import_nothing_of_the_phase3_layer_and_name_no_mental_status_field():
    """The certification of P3-532 found the pilot importing the authority, its store and the shadow, and reading the mental-status field to relabel it. Now: like the
    faculty review pages, it imports nothing of the layer (the page's one crossing hands it a ``Layer``), and its mental-status filters are text transforms."""
    for name in ("gi_pilot.py", "gi_pilot_ui.py"):
        found = {module for module in _imports(ROOT / name) if module.startswith(("runtime_", "clinical_core"))}
        assert found == set(), (name, found)
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "mental_status" not in text, name
        assert "runtime_shadow" not in text and "phase3_shadow" not in text, name
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    hooks = app[app.index("def render_event(event):"):app.index("    body = (language.say(event[\"text\"])")]
    assert "mental_status" not in hooks, "the page's pilot hook passes only the text"


def test_u23_the_layer_carries_only_names_pure_checks_the_artifact_checks_and_the_page_s_own_site_helper():
    assert tuple(field for field in gp.Layer.__dataclass_fields__) == gp.LAYER_MEMBERS
    assert LAYER.verify_artifact is ra.verify_artifact and LAYER.replay_site_artifact is ra.replay_site_artifact and LAYER.derived_map is ra.derived_map
    assert LAYER.looks_like_the_pilot is ra.looks_like_the_pilot and LAYER.deployment_markers is ra.pilot_deployment_markers and LAYER.pilot_flags == tuple(ra.PILOT_FLAGS)
    assert LAYER.site_key == ra.SITE_KEY
    writers = {"open_site", "site_for", "after_clock_moved", "authority_turn", "turn_reset", "turn_check", "continuation_guard", "forget_dry_evaluator"}
    held = {getattr(value, "__name__", "") for value in (getattr(LAYER, name) for name in gp.LAYER_MEMBERS) if callable(value)}
    assert not (held & writers), held & writers
    # the published configuration, by name, is the layer's own
    assert dict(LAYER.configuration) == {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: ps.SNAPSHOT_ID, ra.TONE_FLAG: tn.SNAPSHOT_ID,
                                         ra.ENVIRONMENT_FLAG: "development", rs.FLAG: rs.MODE_SHADOW_COMPARE}
    import runtime_ne_grant as ne_grant
    assert (gp.PRESSURE_SNAPSHOT_ID, gp.TONE_SNAPSHOT_ID, gp.NOREPINEPHRINE_GRANT_ID, gp.AUTHORITY_STORE_FLAG) == (ps.SNAPSHOT_ID, tn.SNAPSHOT_ID, ne_grant.GRANT_ID, ras.STORE_FLAG)
    # the page builds it in one place, from the modules it already imports, with its own site helper
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert app.count("_gi_pilot.layer_from(") == 1 and "lambda: _runtime_authority_site()" in app


def test_u24_the_fail_closed_vocabulary_covers_the_engine_s_own_mental_status_ladder():
    import family_engine
    words = {word.lower() for word in gp.MENTAL_WORDS}
    assert {word.lower() for word in family_engine._MENTAL_LADDER} <= words and {word.lower() for word in family_engine._NAME_OF.values()} <= words
