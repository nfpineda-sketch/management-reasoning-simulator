"""Provenance, cues, and the decision that cannot be explained after its results.

Sections 3, 6 and 7 of the faculty specification of 2026-09-23.

Three properties, and each of them is a refusal as much as a capability:

* **Provenance.** A reader of the trace can tell the resident's own sentence from
  something they said earlier about another decision, from an answer typed into
  the follow-up, and from the application's phrasing. The fifth state is absence,
  and absence has no entry: the record says "not stated", never "did not
  recognise", because all we know is what was written.
* **Cues.** The findings the resident named, and whether they said what those
  findings meant. Nothing is reconstructed from the intervention: "dar suero"
  names no finding and does not imply hypovolaemia.
* **The moment.** A decision's justification is fixed before that decision has
  results. An explanation written afterwards belongs to the minute it was
  written in and never improves the decision it came after.
"""
import pytest

import reasoning_cues
import reasoning_provenance
import reasoning_questions
from test_curriculum_trajectories import initialize, load_engine


@pytest.fixture(scope="module")
def engine():
    loaded = load_engine()
    return loaded


@pytest.fixture
def encounter(engine):
    initialize(engine, engine["INITIAL_STATE"])
    engine["st"].session_state["state"] = {"engine_family": "generated", "observable": {},
                                           "sim_time": 0}
    return engine


# --- the four questions -----------------------------------------------------

def test_the_action_is_one_of_the_four_and_is_never_asked_for():
    fields = [field for field, _, _ in reasoning_questions.QUESTIONS]
    assert fields == ["working_model", "action", "expected_effect", "reassessment_target"]


def test_every_question_is_a_question_and_every_help_explains_the_category():
    for field, question, help_text in reasoning_questions.QUESTIONS:
        assert question.endswith("?"), field
        assert len(help_text) > 30, field


def test_the_help_never_names_a_finding_or_a_conduct():
    # A help text that hints at this patient would be a clinical cue disguised
    # as an instruction, and the rubric could not tell the two apart afterwards.
    forbidden = ("shock", "sepsis", "infarct", "edema", "hypotens", "give ", "start ",
                 "aspirin", "fluid", "oxygen", "diagnosis of")
    for field, _, help_text in reasoning_questions.QUESTIONS:
        lowered = help_text.lower()
        assert not [word for word in forbidden if word in lowered], (field, help_text)


def test_the_hold_says_what_it_recognised_before_what_is_missing(encounter):
    parsed = encounter["clinical_interpreter"](
        "Furosemida 40 mg EV, reevaluo diuresis en 30 minutos")
    prompt = encounter["reasoning_gate_prompt"](
        parsed, encounter["reasoning_gate_missing"](parsed))
    assert "I recognised what you want to do and what you will check." in prompt
    assert "Still to state: what you think is going on and what you expect to happen." in prompt
    assert prompt.index("I recognised") < prompt.index("Still to state")
    assert "You do not need to repeat the order." in prompt


def test_a_hold_with_one_gap_reads_as_one_clause(encounter):
    parsed = encounter["clinical_interpreter"](
        "Edema pulmonar cardiogenico. Furosemida 40 mg EV, reevaluo diuresis en 30 minutos")
    missing = encounter["reasoning_gate_missing"](parsed)
    assert missing == ["expected_effect"]
    prompt = encounter["reasoning_gate_prompt"](parsed, missing)
    assert "Still to state: what you expect to happen." in prompt


# --- cues -------------------------------------------------------------------

def test_a_finding_the_resident_linked_to_their_interpretation():
    rows = reasoning_cues.cues("Está hipotenso y confuso; me preocupa que esté en shock.")
    assert [row["finding"] for row in rows] == ["hipotenso", "confuso"]
    assert all(row["linked"] for row in rows)
    assert all(row["polarity"] == "present" for row in rows)
    assert all("hipotenso y confuso" in row["statement"] for row in rows)


def test_an_interpretation_without_findings_invents_none():
    assert reasoning_cues.cues("Creo que está en shock.") == []


def test_an_order_alone_is_not_a_hypothesis():
    # The rule that matters most: nothing here can reach hypovolaemia from fluid.
    assert reasoning_cues.cues("Dar suero.") == []
    assert reasoning_cues.cues("Pásale 1000 cc de suero fisiológico IV.") == []


def test_a_change_and_a_persistence_are_both_kept_with_their_contrast():
    rows = reasoning_cues.cues("La presión mejoró, pero sigue confuso.")
    assert [row["finding"] for row in rows] == ["La presión mejoró", "confuso"]
    assert all(row["polarity"] == "trend" for row in rows)
    assert all(row["contrast"] for row in rows)


def test_an_absent_finding_is_recorded_as_absent():
    rows = reasoning_cues.cues("Sin crepitantes ni edema.")
    assert [(row["finding"], row["polarity"]) for row in rows] == [
        ("crepitantes", "absent"), ("edema", "absent")]


def test_an_expectation_is_not_an_observation():
    assert reasoning_cues.cues("Espero que mejore la hipotension.") == []
    assert reasoning_cues.cues("I expect the hypoxemia to improve.") == []


def test_a_variable_named_without_a_change_is_not_a_finding():
    assert reasoning_cues.cues("Reevaluo la presion en 10 minutos.") == []


def test_a_measured_value_is_a_finding():
    rows = reasoning_cues.cues("PA 80/50, FC 130, sat 85%.")
    assert [row["finding"] for row in rows] == ["PA 80/50", "FC 130", "sat 85%"]


def test_a_hedge_is_kept_as_uncertainty_rather_than_a_fact():
    rows = reasoning_cues.cues("Posiblemente esté hipotenso.")
    assert rows and rows[0]["polarity"] == "uncertain"


def test_cues_reach_the_reasoning_without_becoming_a_requirement(encounter):
    parsed = encounter["clinical_interpreter"](
        "Está hipotenso y confuso, me preocupa que esté en shock. Pásale 1000 cc, "
        "espero que suba la presion, reevaluo PAM en 10 minutos.")
    findings = parsed["reasoning"]["mentioned_findings"]
    assert [row["finding"] for row in findings] == ["hipotenso", "confuso"]
    assert encounter["reasoning_gate_missing"](parsed) == []


def test_a_working_model_without_cues_is_still_a_working_model(encounter):
    parsed = encounter["clinical_interpreter"](
        "Creo que es un edema pulmonar cardiogenico. Furosemida 40 mg EV, espero que "
        "orine, reevaluo diuresis en 30 minutos.")
    assert parsed["reasoning"]["problem_representation"]
    assert "mentioned_findings" not in parsed["reasoning"]
    assert encounter["reasoning_gate_missing"](parsed) == []


def test_a_malformed_cue_never_reaches_the_record():
    assert reasoning_cues.sanitise([{"finding": "x", "polarity": "invented"}]) == []
    assert reasoning_cues.sanitise("not a list") == []
    assert reasoning_cues.sanitise([{"polarity": "present"}]) == []


# --- provenance -------------------------------------------------------------

def test_what_the_resident_wrote_here_is_marked_as_theirs(encounter):
    parsed = encounter["clinical_interpreter"](
        "Edema pulmonar cardiogenico. Furosemida 40 mg EV, espero que orine, "
        "reevaluo diuresis en 30 minutos.")
    provenance = parsed["reasoning"]["slot_provenance"]
    assert provenance["problem_representation"] == reasoning_provenance.STATED
    assert provenance["expected_effect"] == reasoning_provenance.STATED


def test_a_slot_the_application_composed_says_so(encounter):
    parsed = encounter["clinical_interpreter"](
        "Patient hypotensive and poorly perfused. Give 1000 cc NS, I expect the "
        "pressure to rise, reassess perfusion and BP in 10 minutes.")
    reasoning = parsed["reasoning"]
    if "management_priority" in (reasoning.get("derived_slots") or ()):
        assert reasoning["slot_provenance"]["management_priority"] == (
            reasoning_provenance.COMPOSED)


def test_an_absent_slot_has_no_provenance_at_all(encounter):
    parsed = encounter["clinical_interpreter"]("Start norepinephrine.")
    assert parsed["reasoning"] == {}
    assert reasoning_provenance.of(parsed["reasoning"], "problem_representation") is None


def test_only_the_interpretation_may_be_carried(encounter):
    assert "expected_effect" not in reasoning_provenance.CARRYABLE
    assert "reassessment_target" not in reasoning_provenance.CARRYABLE
    assert "problem_representation" in reasoning_provenance.CARRYABLE


def test_an_interpretation_stated_earlier_is_not_asked_for_again(encounter):
    engine = encounter
    trace = [{
        "execution_status": "executed",
        "decision_time_min": 0,
        "reasoning": {"problem_representation": "edema pulmonar cardiogenico",
                      "slot_provenance": {"problem_representation": reasoning_provenance.STATED}},
    }]
    engine["st"].session_state["management_trace"] = trace
    parsed = engine["clinical_interpreter"](
        "Nitroglicerina en infusion 50 mcg/min, espero que baje la precarga, "
        "reevaluo presion en 10 minutos.")
    assert engine["reasoning_gate_missing"](parsed) == ["working_model"]
    remaining = engine["apply_carried_reasoning"](
        parsed, engine["reasoning_gate_missing"](parsed))
    assert remaining == []
    assert parsed["reasoning"]["problem_representation"] == "edema pulmonar cardiogenico"
    assert parsed["reasoning"]["slot_provenance"]["problem_representation"] == (
        reasoning_provenance.CARRIED)
    # Not presented as a fresh statement: the record names where it was said.
    assert parsed["reasoning"]["carried_from"] == {"decision": 1, "minute": 0}


def test_a_carried_interpretation_names_the_decision_it_was_stated_in(encounter):
    engine = encounter
    engine["st"].session_state["management_trace"] = [
        {"execution_status": "executed", "decision_time_min": 0,
         "reasoning": {"problem_representation": "shock septico",
                       "slot_provenance": {"problem_representation": reasoning_provenance.STATED}}},
        {"execution_status": "executed", "decision_time_min": 10,
         "reasoning": {"problem_representation": "shock septico",
                       "carried_from": {"decision": 1, "minute": 0},
                       "slot_provenance": {"problem_representation": reasoning_provenance.CARRIED}}},
    ]
    # The third order still points at the first: where it was said, not where
    # it was carried.
    assert engine["carried_reasoning"]()["decision"] == 1


def test_nothing_is_carried_when_nothing_was_ever_stated(encounter):
    encounter["st"].session_state["management_trace"] = [
        {"execution_status": "executed", "decision_time_min": 0, "reasoning": {}}]
    assert encounter["carried_reasoning"]() is None


def test_an_unknown_provenance_is_dropped_rather_than_recorded():
    assert reasoning_provenance.sanitise(
        {"problem_representation": "invented"}) == {}
    assert reasoning_provenance.sanitise(
        {"not_a_slot": reasoning_provenance.STATED}) == {}
    assert reasoning_provenance.sanitise("not a mapping") == {}


# --- the moment -------------------------------------------------------------

def test_a_decision_records_when_its_justification_was_fixed(encounter):
    engine = encounter
    parsed = engine["clinical_interpreter"]("Give diltiazem 5 mg IV.")
    engine["hold_pending_reasoning"](parsed)
    resolved = engine["resolve_pending_reasoning"](
        "I think this is AF with RVR impairing filling. I expect the rate to fall. "
        "Reassess HR and BP in 5 minutes.")
    gate = resolved["parsed"]["reasoning_gate"]
    assert gate["sealed_at_min"] == 0
    assert gate["completed_after_results"] is False


def test_an_explanation_written_after_the_decision_moved_says_so(encounter):
    engine = encounter
    parsed = engine["clinical_interpreter"]("Give diltiazem 5 mg IV.")
    engine["hold_pending_reasoning"](parsed)
    # A held order cannot execute and nothing else runs while it waits, so this
    # cannot happen today. The guard is what makes a future change that opens
    # that door visible instead of quietly improving a score.
    engine["st"].session_state["state"]["sim_time"] = 15
    resolved = engine["resolve_pending_reasoning"](
        "I think this is AF with RVR. I expect the rate to fall. Reassess HR in 5 minutes.")
    assert resolved["parsed"]["reasoning_gate"]["completed_after_results"] is True


def test_a_new_decision_appearing_while_an_order_waits_is_also_late(encounter):
    engine = encounter
    parsed = engine["clinical_interpreter"]("Give diltiazem 5 mg IV.")
    engine["hold_pending_reasoning"](parsed)
    engine["st"].session_state["management_trace"] = [{"execution_status": "executed"}]
    resolved = engine["resolve_pending_reasoning"](
        "I think this is AF with RVR. I expect the rate to fall. Reassess HR in 5 minutes.")
    assert resolved["parsed"]["reasoning_gate"]["completed_after_results"] is True


# --- the follow-up loses nothing and executes nothing twice ------------------

def test_the_follow_up_answer_is_marked_as_completed_there(encounter):
    engine = encounter
    parsed = engine["clinical_interpreter"]("Give diltiazem 5 mg IV.")
    engine["hold_pending_reasoning"](parsed)
    resolved = engine["resolve_pending_reasoning"](
        "I think this is AF with RVR impairing filling. I expect the rate to fall. "
        "Reassess HR and BP in 5 minutes.")
    provenance = resolved["parsed"]["reasoning"]["slot_provenance"]
    assert provenance["problem_representation"] == reasoning_provenance.COMPLETED
    assert provenance["expected_effect"] == reasoning_provenance.COMPLETED


def test_the_original_entry_survives_the_follow_up(encounter):
    engine = encounter
    parsed = engine["clinical_interpreter"]("Give diltiazem 5 mg IV.")
    engine["hold_pending_reasoning"](parsed)
    resolved = engine["resolve_pending_reasoning"](
        "I think this is AF with RVR. I expect the rate to fall. Reassess HR in 5 minutes.")
    assert "diltiazem 5 mg IV" in resolved["parsed"]["raw_text"]
    assert "AF with RVR" in resolved["parsed"]["raw_text"]


def test_the_held_intervention_is_not_duplicated_by_the_follow_up(encounter):
    engine = encounter
    parsed = engine["clinical_interpreter"]("Give diltiazem 5 mg IV.")
    engine["hold_pending_reasoning"](parsed)
    resolved = engine["resolve_pending_reasoning"](
        "I think this is AF with RVR. I expect the rate to fall. "
        "Give diltiazem 5 mg IV. Reassess HR in 5 minutes.")
    types = [action["type"] for action in resolved["parsed"]["actions"]]
    assert types.count("diltiazem") == 1


def test_a_field_left_as_extracted_keeps_the_hand_that_wrote_it(encounter):
    engine = encounter
    parsed = engine["clinical_interpreter"](
        "Edema pulmonar cardiogenico. Furosemida 40 mg EV.")
    engine["hold_pending_reasoning"](parsed)
    resolved = engine["complete_pending_reasoning_fields"](
        "Edema pulmonar cardiogenico",   # unchanged: still theirs from the entry
        "",
        "que orine y baje la congestion",
        "diuresis y saturacion",
        30,
    )
    provenance = resolved["parsed"]["reasoning"]["slot_provenance"]
    assert provenance["problem_representation"] == reasoning_provenance.STATED
    assert provenance["expected_effect"] == reasoning_provenance.COMPLETED


# --- the model as a reader of findings, and the budget that stops it ---------

class CueStub:
    """A provider that answers from a script and counts what it was asked."""

    def __init__(self, answer):
        self.answer = answer
        self.calls = []
        self.responses = self

    def create(self, **kwargs):
        import json
        self.calls.append(kwargs)
        return type("R", (), {"output_text": json.dumps(self.answer)})()


ENTRY = "Está hipotenso y confuso, me preocupa que esté en shock. Pásale 1000 cc."


def test_the_categories_and_the_findings_are_one_question_not_two():
    from reasoning_recognition import recognize

    client = CueStub({"working_model": {"present": True, "quote": "esté en shock"},
                      "cues": [{"finding": "hipotenso", "polarity": "present",
                                "linked": True, "link_marker": "me preocupa que"}]})
    found = recognize(ENTRY, ["working_model"], cues=True, client=client)
    assert len(client.calls) == 1
    assert found.slots == {"working_model": "esté en shock"}
    assert [row["finding"] for row in found.cues] == ["hipotenso"]


def test_a_finding_the_resident_never_wrote_is_refused():
    from reasoning_recognition import recognize

    client = CueStub({"cues": [
        {"finding": "oliguria", "polarity": "present", "linked": False, "link_marker": ""},
        {"finding": "confuso", "polarity": "present", "linked": False, "link_marker": ""},
    ]})
    found = recognize(ENTRY, (), cues=True, client=client)
    assert [row["finding"] for row in found.cues] == ["confuso"]
    assert found.cues_rejected == 1


def test_a_claimed_link_without_the_connector_keeps_the_finding_and_drops_the_claim():
    from reasoning_recognition import recognize

    client = CueStub({"cues": [{"finding": "confuso", "polarity": "present",
                                "linked": True, "link_marker": "which clearly indicates"}]})
    found = recognize(ENTRY, (), cues=True, client=client)
    assert found.cues[0]["finding"] == "confuso"
    assert found.cues[0]["linked"] is False


def test_the_patterns_keep_their_rows_and_the_model_only_adds(encounter):
    engine = encounter
    parsed = engine["clinical_interpreter"](ENTRY)
    before = [row["finding"] for row in parsed["reasoning"]["mentioned_findings"]]
    assert before == ["hipotenso", "confuso"]
    engine["merge_cues"](parsed, [
        {"finding": "hipotenso", "polarity": "present", "linked": False,
         "link_marker": "", "contrast": False, "statement": "", "source": "model"},
        {"finding": "1000 cc", "polarity": "present", "linked": False,
         "link_marker": "", "contrast": False, "statement": "", "source": "model"},
    ])
    rows = parsed["reasoning"]["mentioned_findings"]
    assert [row["finding"] for row in rows] == ["hipotenso", "confuso", "1000 cc"]
    assert [row["source"] for row in rows] == ["pattern", "pattern", "model"]
    assert parsed["cue_recognition"]["added_by_model"] == 1


def test_the_budget_is_a_counter_that_stops(encounter):
    engine = encounter
    session = engine["st"].session_state
    session["ai_calls_spent"] = 0
    session["ai_call_ledger"] = []
    budget = engine["ai_call_budget"]()
    assert budget == 8
    for _ in range(budget):
        assert engine["spend_ai_call"]("test") is True
    assert engine["spend_ai_call"]("test") is False
    assert engine["ai_calls_spent"]() == budget


def test_the_ledger_says_what_each_request_was_for(encounter):
    engine = encounter
    engine["st"].session_state["ai_calls_spent"] = 0
    engine["st"].session_state["ai_call_ledger"] = []
    engine["spend_ai_call"]("held-order recognition")
    ledger = engine["st"].session_state["ai_call_ledger"]
    assert ledger == [{"purpose": "held-order recognition", "minute": 0}]


def test_an_exhausted_budget_falls_back_rather_than_failing(encounter):
    engine = encounter
    engine["st"].session_state["ai_calls_spent"] = 99
    parsed = engine["clinical_interpreter"](ENTRY)
    engine["recognize_cues_for"](parsed)
    # Off by default, so nothing is attempted and nothing is claimed either way.
    assert parsed.get("cue_recognition") is None
    assert [row["finding"] for row in parsed["reasoning"]["mentioned_findings"]] == [
        "hipotenso", "confuso"]


def test_reading_the_findings_with_a_model_is_off_unless_asked_for(encounter):
    assert encounter["ai_cue_mode"]() == "off"
    assert encounter["ai_reasoning_recognition_enabled"]() is False


# --- the measurement tool cannot spend more than it was authorised ----------

def test_the_measurement_refuses_to_run_without_a_number():
    import tools_cue_recognition_runs as tool

    with pytest.raises(SystemExit):
        tool.main(["--yes"])          # a promise is not a scope
    with pytest.raises(SystemExit):
        tool.main([])                 # neither is silence


def test_the_dry_run_sends_nothing_and_still_says_what_the_patterns_did(capsys):
    import tools_cue_recognition_runs as tool

    assert tool.main(["--dry-run"]) == 0
    printed = capsys.readouterr().out
    assert "requests 0" in printed
    assert "invented 0" in printed


def test_the_counter_refuses_the_request_past_the_cap():
    import httpx

    import tools_cue_recognition_runs as tool

    # The cap is enforced by the counter itself, not by the loop that calls it:
    # a retry inside the SDK cannot buy a request the faculty did not authorise.
    sent = []
    original = httpx.Client.send

    def counted(self, request, *args, **kwargs):
        if len(sent) >= 2:
            raise RuntimeError("refused")
        sent.append(request)
        raise RuntimeError("no network in this suite")

    try:
        httpx.Client.send = counted
        for _ in range(2):
            with pytest.raises(RuntimeError):
                httpx.Client().send(object())
        with pytest.raises(RuntimeError, match="refused"):
            httpx.Client().send(object())
    finally:
        httpx.Client.send = original
    assert len(sent) == 2


def test_the_findings_the_paid_measurement_exposed():
    """What one run of twenty-five requests bought, kept as a test.

    The model read "orina turbia" and the closed lexicon could not; that gap is
    closed. The model also read "la hipotension" out of "Espero que mejore la
    hipotension" -- an expectation turned into a present finding, which is the
    failure the specification names. The patterns refused it then and must keep
    refusing it.
    """
    assert [row["finding"] for row in reasoning_cues.cues(
        "Creo que es sepsis de foco urinario porque tiene orina turbia.")] == ["orina turbia"]
    assert reasoning_cues.cues("Espero que mejore la hipotension.") == []
    assert reasoning_cues.cues(
        "Espero que mejore la hipotension. Reevaluo la presion en 10 minutos.") == []


def test_the_link_the_widened_lexicon_now_carries():
    rows = reasoning_cues.cues(
        "Creo que es sepsis de foco urinario porque tiene orina turbia.")
    assert rows[0]["linked"] is True
    assert rows[0]["link_marker"].lower() == "porque"
