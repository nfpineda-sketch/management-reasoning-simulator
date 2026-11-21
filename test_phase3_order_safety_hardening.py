"""P3-474 to P3-482: the FINAL vasoactive order-safety hardening (faculty decisions FD-ORDER-01 to FD-ORDER-11, 2026-11-21).

The previous cycle made a physiologic TARGET never a DRUG RATE (``test_phase3_target_rate_source``, ``test_phase3_target_order_boundary``). It left eight demonstrated order semantics open (L-1 to L-8). Each one is a way for the
simulator to run a vasoactive infusion at a rate the resident did not write for that drug, to stop an infusion the resident did not name, or to make an incomplete order executable. They are closed here, with the smallest
change that does it, and each is proven in the REAL encounter (reader -> time semantics -> pipeline -> engine), not only in the reader:

  L-1  FD-ORDER-01  an adjustment named only by ITS ROLE ("increase the infusion to 40 mL/h") is run with the unit it was written in or not at all: never as mcg/min.      (order_pipeline)
  L-2  FD-ORDER-02  a rate belongs to AT MOST ONE drug: another medicine's rate in the same piece is never an infusion's.                                          (family_parser)
  L-3  FD-ORDER-03  a stop is attributed to a vasoactive infusion only if the verb governs its name: never inherited by "norepinephrine to MAP 65", never through an exception. (family_parser)
  L-4  FD-ORDER-04  the "/min" of "mcg/min" is the denominator of a rate, not the duration of an order written for LATER.                                            (time_semantics)
  L-5  FD-ORDER-05  "restart norepinephrine" with no explicit rate is the approved incomplete-rate question; the previous rate is not reused.                        (family_parser)
  L-6  FD-ORDER-06  "continue norepinephrine at 12" is incomplete, not a silent continue; "... at 12 mcg/min" is valid.                                                (family_parser)
  L-7  FD-ORDER-07  the pipeline barrier reads ``rate_mcg_min``: nitroglycerin no longer depends on the reader alone.                                                  (order_pipeline)
  L-8  FD-ORDER-08  a number alone, answering "what rate?", is never a rate and takes its unit from nothing (not the running infusion, not the drug's usual one).      (app.py legacy path)

Nothing here changes a physiology constant, the engine, the shadow boundary (FD-ORDER-10), the permanent fail-closed of the shadow (FD-ORDER-09) or any authority (FD-ORDER-11).
"""
import json
import re
from copy import deepcopy
from types import SimpleNamespace

import pytest

import family_parser as fp
import order_pipeline as op
import pending_family_orders as pending
import pilot_acceptance as acceptance
import reader_succession as succession
import test_phase3_target_order_boundary as boundary
import test_tone_pathway_analysis as ta
import time_semantics

DRUGS = ("norepinephrine", "epinephrine", "dobutamine", "nitroglycerin")
NE10, NE5, NTG20, DOB5 = "Start norepinephrine at 10 mcg/min.", "Start norepinephrine at 5 mcg/min.", "Start nitroglycerin at 20 mcg/min.", "Start dobutamine at 5 mcg/min."
MESSAGE = op.INCOMPLETE_EXPLICIT_RATE


def _run(*texts):
    encounter = acceptance.Encounter(ta.FRF_CASE)
    return encounter, [encounter.order(text) for text in texts]


def _rates(encounter):
    family = encounter.state.get("family_state") or {}
    return {drug: float(family.get(drug) or 0.0) for drug in DRUGS}


def _parse(text):
    return boundary._parse(text)


def _numbers(actions):
    return [action for action in actions if any(action.get(key) is not None for key in ("rate", "rate_value", "rate_mcg_min"))]


def _the_incomplete_question(entry):
    return entry["executed"] is False and entry["clarification"] == MESSAGE


# =============================================================================================================================================================================
# L-1 · FD-ORDER-01 · unit compatibility
# =============================================================================================================================================================================
@pytest.mark.parametrize("running, expected", [(NTG20, {"nitroglycerin": 20.0}), (NE10, {"norepinephrine": 10.0}), (DOB5, {"dobutamine": 5.0})])
@pytest.mark.parametrize("text", ["increase the infusion to 40 mL/h", "increase the infusion to 40 ml/hr", "decrease the infusion to 5 mL/h", "Subele la infusion a 40 mL/h"])
def test_l1_an_adjustment_named_by_its_role_with_a_unit_no_vasoactive_runs_in_never_runs(running, expected, text):
    """The reproduced defect: with nitroglycerin running, ``increase the infusion to 40 mL/h`` ran as 40 mcg/min (the completion drops the unit). Now it is the incomplete-rate question and nothing changes."""
    encounter, entries = _run(running, text)
    assert _the_incomplete_question(entries[-1]) and {drug: value for drug, value in _rates(encounter).items() if value} == expected


def test_l1_nitroglycerin_is_not_adjusted_in_mcg_per_kg_per_min_and_the_barrier_says_so_before_the_engine():
    encounter, entries = _run(NTG20, "decrease the infusion to 5 mcg/kg/min")
    assert entries[-1]["executed"] is False and _rates(encounter)["nitroglycerin"] == 20.0
    adjustment = {"type": "infusion_adjustment", "operation": "adjust", "rate_value": 5.0, "rate_units": "mcg/kg/min"}
    assert op.incomplete_explicit_rate(adjustment, state={"treatments": {"nitroglycerin": True}})[0] == MESSAGE
    assert op.incomplete_explicit_rate(adjustment, state={"treatments": {"norepinephrine": True}}) is None, "mcg/kg/min is a unit norepinephrine runs in"


@pytest.mark.parametrize("running, text, expected", [(NE10, "increase the infusion to 12 mcg/min", {"norepinephrine": 12.0}), (NTG20, "increase the infusion to 40 mcg/min", {"nitroglycerin": 40.0}),
                                                     (DOB5, "increase the infusion to 7 mcg/min", {"dobutamine": 7.0}), (NE10, "Subele la infusion a 15 mcg/min", {"norepinephrine": 15.0})])
def test_l1_nonregression_a_role_named_adjustment_with_a_supported_unit_runs_exactly_as_before(running, text, expected):
    encounter, entries = _run(running, text)
    assert entries[-1]["executed"] is True and {drug: value for drug, value in _rates(encounter).items() if value} == expected


@pytest.mark.parametrize("units, held", [("mcg/min", False), ("ug/min", False), ("mcg / min", False), ("MCG/MIN", False), ("µg/min", False), ("mcg/kg/min", False), ("ml/h", True), ("mL/hr", True), ("units", True), ("%", True),
                                         (None, True), ("", True), ("mg/h", True)])
def test_l1_the_unit_rule_is_structural_a_vasoactive_rate_unit_or_nothing(units, held):
    action = {"type": "infusion_adjustment", "operation": "adjust", "rate_value": 12.0, "rate_units": units}
    result = op.incomplete_explicit_rate(action, state={"treatments": {"norepinephrine": True}})
    assert (result is not None) is held
    if result:
        assert result[0] == MESSAGE and result[1]["rate_value"] is None and result[1]["rate_units"] is None, "the held copy keeps NO number and NO unit"


def test_l1_a_role_named_stop_and_an_adjustment_with_no_rate_are_not_touched_by_the_unit_rule():
    assert op.incomplete_explicit_rate({"type": "infusion_adjustment", "operation": "stop", "rate_value": None, "rate_units": None}) is None
    assert op.incomplete_explicit_rate({"type": "infusion_adjustment", "operation": "adjust", "rate_value": None, "rate_units": None}) is None, "the engine's own question ('Specify the new ... rate') stands"


# =============================================================================================================================================================================
# L-2 · FD-ORDER-02 · a rate belongs to at most one drug
# =============================================================================================================================================================================
OTHER_DRUG_RATE = (
    "titrate norepinephrine to MAP 65 with propofol 5 mcg/min", "increase norepinephrine to MAP 65 with propofol 5 mcg/min", "norepinephrine to MAP 65 with fentanyl 50 mcg/h",
    "titrate norepinephrine to MAP 65 with midazolam 2 mg/h", "start propofol 5 mcg/kg/min with norepinephrine", "increase norepinephrine to 10 mcg/min with propofol 5 mcg/min",
    "increase nitroglycerin to 20 mcg/min with norepinephrine 5 mcg/min", "titrate norepinephrine to MAP 65 with dexmedetomidine 0.5 mcg/kg/h",
    "increase norepinephrine along with vasopressin 3 mcg/min", "titrate norepinephrine to MAP 65 with phenylephrine 40 mcg/min", "titula noradrenalina a PAM 65 con propofol 5 mcg/min",
    "sube noradrenalina con midazolam 2 mg/h", "increase norepinephrine to 12 mcg/min plus amiodarone 1 mg/min", "norepinephrine at 5 mcg/min propofol 5 mcg/min",
    "increase the infusion to MAP 65 with propofol 5 mcg/min", "increase the infusion to 20 mcg/min with propofol 5 mcg/min",
    # the number is written AFTER its drug in the other medicine's own words, or BEFORE it ("5 mcg/min of propofol"): the claimant is the other drug
    "start 5 mcg/min of propofol with norepinephrine", "increase norepinephrine to MAP 65 with 5 mcg/min of propofol",
    # no drug claims the number (words other than a dose's connectors stand between it and the name, and another medicine is in the piece): it is asked, never read as the infusion's
    "start norepinephrine via central line at 5 mcg/min with propofol", "start norepinephrine peripherally at 5 mcg/min while on propofol")


@pytest.mark.parametrize("text", OTHER_DRUG_RATE)
def test_l2_the_reader_never_gives_a_vasoactive_infusion_the_rate_of_another_medicine_in_the_same_piece(text):
    actions = fp.parse_family_actions(text)["actions"]
    assert not _numbers(actions), (text, actions)
    assert actions and all(action["type"] == "clarification" for action in actions), "the whole piece is held: no other medicine's order is dropped in silence"


@pytest.mark.parametrize("text", ["titrate norepinephrine to MAP 65 with propofol 5 mcg/min", "increase norepinephrine to MAP 65 with propofol 5 mcg/min", "norepinephrine to MAP 65 with fentanyl 50 mcg/h",
                                  "increase the infusion to MAP 65 with propofol 5 mcg/min", "increase norepinephrine to 10 mcg/min with propofol 5 mcg/min"])
def test_l2_in_the_real_encounter_nothing_runs_and_the_running_rate_does_not_move(text):
    encounter, entries = _run(NE10, text)
    assert entries[-1]["executed"] is False and _rates(encounter)["norepinephrine"] == 10.0


@pytest.mark.parametrize("text, expected", [
    ("Start norepinephrine at 10 mcg/min for hypotension", {"type": "norepinephrine", "operation": "start", "rate": 10.0, "units": "mcg/min"}),
    ("start norepinephrine peripherally at 5 mcg/min", {"type": "norepinephrine", "operation": "start", "rate": 5.0, "units": "mcg/min"}),
    ("norepinephrine drip at 8 mcg/min", {"type": "norepinephrine", "operation": "start", "rate": 8.0, "units": "mcg/min"}),
    ("norepinephrine 0.1 mcg/kg/min", {"type": "norepinephrine", "operation": "start", "rate": 0.1, "units": "mcg/kg/min"}),
    ("increase norepinephrine to 12 mcg/min to keep MAP above 65", {"type": "norepinephrine", "operation": "adjust", "rate": 12.0, "units": "mcg/min"}),
    ("nitroglycerin 20 mcg/min", {"type": "nitroglycerin", "operation": "start", "rate_mcg_min": 20.0}),
    ("start dobutamine 5 mcg/kg/min", {"type": "dobutamine", "operation": "start", "rate": 5.0, "units": "mcg/kg/min"}),
    ("start epinephrine at 2 mcg/min", {"type": "epinephrine", "operation": "start", "rate": 2.0, "units": "mcg/min"}),
    ("inicio noradrenalina 8 mcg/min objetivo PAM 65", {"type": "norepinephrine", "operation": "start", "rate": 8.0, "units": "mcg/min"}),
    ("start norepinephrine at 5 mcg/min while the patient is on propofol", {"type": "norepinephrine", "operation": "start", "rate": 5.0, "units": "mcg/min"}),
    ("increase norepinephrine to 12 mcg/min with fentanyl running", {"type": "norepinephrine", "operation": "adjust", "rate": 12.0, "units": "mcg/min"}),
    ("norepinephrine at 5 mcg/min for the patient sedated with midazolam", {"type": "norepinephrine", "operation": "start", "rate": 5.0, "units": "mcg/min"}),
    ("start norepinephrine at 5 mcg/min under propofol sedation", {"type": "norepinephrine", "operation": "start", "rate": 5.0, "units": "mcg/min"}),
    ("5 mcg/min of norepinephrine with propofol", {"type": "norepinephrine", "operation": "start", "rate": 5.0, "units": "mcg/min"}),
    ("start 5 mcg/min of norepinephrine with propofol", {"type": "norepinephrine", "operation": "start", "rate": 5.0, "units": "mcg/min"})])
def test_l2_nonregression_a_rate_written_for_its_own_drug_is_read_exactly_as_before(text, expected):
    actions = fp.parse_family_actions(text)["actions"]
    assert len(actions) == 1 and {key: actions[0].get(key) for key in expected} == expected


def test_l2_a_list_of_orders_each_with_its_own_rate_still_gives_each_drug_its_own():
    actions = fp.parse_family_actions("start norepinephrine at 10 mcg/min and dobutamine at 300 mcg/min, nitroglycerin 20 mcg/min")["actions"]
    assert [(a["type"], a.get("rate", a.get("rate_mcg_min"))) for a in actions] == [("norepinephrine", 10.0), ("dobutamine", 300.0), ("nitroglycerin", 20.0)]
    encounter, entries = _run("Start norepinephrine at 10 mcg/min and dobutamine at 300 mcg/min, nitroglycerin 20 mcg/min")
    assert {drug: value for drug, value in _rates(encounter).items() if value} == {"norepinephrine": 10.0, "dobutamine": 300.0, "nitroglycerin": 20.0}


def test_l2_a_rate_in_a_list_with_two_infusions_goes_to_the_drug_that_names_it_and_the_other_asks():
    actions = fp.parse_family_actions("increase norepinephrine and dobutamine to 10 mcg/min")["actions"]
    assert len(actions) == 2 and actions[0]["incomplete_explicit_rate"]["agent"] == "norepinephrine" and not _numbers(actions[:1])
    assert (actions[1]["type"], actions[1]["rate"], actions[1]["units"]) == ("dobutamine", 10.0, "mcg/min"), "the rate belongs to ONE drug: the one named with it"


# =============================================================================================================================================================================
# L-3 · FD-ORDER-03 · a stop belongs to at most one drug and only if the verb governs its name
# =============================================================================================================================================================================
NOT_ATTRIBUTED_TO_NE = (
    "stop NS, norepinephrine to MAP 65", "stop nitroglycerin, norepinephrine to MAP 65", "stop the saline, norepinephrine to MAP 65", "stop NS; norepinephrine to MAP 65", "stop oxygen, titrate norepinephrine to MAP 65",
    "stop NS, norepinephrine at 12", "stop NS, norepinephrine 10 mcg/min", "stop NS but keep norepinephrine", "stop all except norepinephrine", "stop everything but norepinephrine", "stop all other than norepinephrine",
    "stop NS, keep norepinephrine", "suspender todo excepto noradrenalina", "para todo menos la noradrenalina", "suspende SF pero manten noradrenalina", "stop it", "stop NS, norepinephrine to keep MAP above 65",
    "stop the fluids and the oxygen, norepinephrine to MAP 65", "stop NS not norepinephrine", "stop NS, not norepinephrine", "stop the saline and do not stop norepinephrine")


@pytest.mark.parametrize("text", NOT_ATTRIBUTED_TO_NE)
def test_l3_a_stop_is_never_given_to_a_vasoactive_infusion_by_a_list_a_neighbour_or_an_exception(text):
    actions = fp.parse_family_actions(text)["actions"]
    assert not [a for a in actions if a.get("type") == "norepinephrine" and a.get("operation") == "stop"], (text, actions)
    assert not [a for a in actions if a.get("type") == "infusion_adjustment" and a.get("operation") == "stop"] or text == "stop it", (text, actions)
    encounter, entries = _run(NE10, text)
    assert _rates(encounter)["norepinephrine"] >= 10.0, "the running infusion is not stopped"


def test_l3_the_neighbour_stop_still_runs_and_the_infusion_is_asked_instead_of_stopped():
    encounter, entries = _run(NTG20, NE10, "stop nitroglycerin, norepinephrine to MAP 65")
    rates = _rates(encounter)
    assert rates["nitroglycerin"] == 0.0 and rates["norepinephrine"] == 10.0, "only the stop that was attributed ran"
    assert entries[-1]["clarification"] == MESSAGE, "what was not attributed is the approved question"


@pytest.mark.parametrize("text, stopped", [("stop norepinephrine", {"norepinephrine"}), ("stop the norepinephrine infusion", {"norepinephrine"}), ("suspende la noradrenalina", {"norepinephrine"}),
                                           ("stop norepinephrine and nitroglycerin", {"norepinephrine", "nitroglycerin"}), ("stop NS, norepinephrine", {"norepinephrine"}),
                                           ("stop nitroglycerin, norepinephrine", {"norepinephrine", "nitroglycerin"}), ("stop nitroglycerin", {"nitroglycerin"}), ("stop the nitroglycerin drip", {"nitroglycerin"}),
                                           ("discontinue norepinephrine", {"norepinephrine"}), ("Stop norepinephrine. Reassess in 5 minutes.", {"norepinephrine"}),
                                           ("stop norepinephrine because MAP is not low", {"norepinephrine"}), ("stop norepinephrine as he does not need pressors", {"norepinephrine"}),
                                           ("stop norepinephrine to keep MAP above 65", {"norepinephrine"}), ("discontinue norepinephrine to keep MAP above 65", {"norepinephrine"}),
                                           ("please stop norepinephrine to keep MAP above 65", {"norepinephrine"}), ("discontinue nitro to keep MAP above 65, reassess in 5 minutes", {"nitroglycerin"}),
                                           ("suspende la noradrenalina para mantener la PAM", {"norepinephrine"}), ("stop norepinephrine and leave MAP to settle", {"norepinephrine"})])
def test_l3_a_stop_that_is_written_for_the_drug_still_stops_it(text, stopped):
    encounter, entries = _run(NE10, NTG20, text)
    rates = _rates(encounter)
    assert {drug for drug in ("norepinephrine", "nitroglycerin") if rates[drug] == 0.0} == stopped, (text, rates)


def test_l3_the_bare_name_in_a_list_takes_the_stop_and_anything_more_does_not():
    assert [a["type"] for a in fp.parse_family_actions("stop NS, norepinephrine")["actions"]] == ["fluid", "norepinephrine"]
    assert fp.parse_family_actions("stop NS, norepinephrine")["actions"][1]["operation"] == "stop"
    after = fp.parse_family_actions("stop NS, norepinephrine to MAP 65")["actions"]
    assert after[0]["operation"] == "stop" and after[1].get("incomplete_explicit_rate") and not _numbers(after)


def test_l3_the_exception_clause_is_not_read_as_a_stop_of_the_drug_it_keeps_and_is_an_unrecognised_order():
    for text in ("stop NS but keep norepinephrine", "stop all except norepinephrine"):
        actions = fp.parse_family_actions(text)["actions"]
        assert len(actions) == 1 and actions[0]["type"] == "clarification" and actions[0].get("unrecognized_text"), (text, actions)


# =============================================================================================================================================================================
# L-4 · FD-ORDER-04 · the "/min" of a rate is not the duration of an order written for later
# =============================================================================================================================================================================
@pytest.mark.parametrize("setup, text, drug, before", [([NE10], "increase norepinephrine to 12 mcg/min in 5 minutes", "norepinephrine", 10.0), ([], "start nitroglycerin at 20 mcg/min in 5 minutes", "nitroglycerin", 0.0),
                                                      ([NE10], "increase norepinephrine to 12 mcg/min after 5 min", "norepinephrine", 10.0), ([], "start norepinephrine 0.1 mcg/kg/min in 10 minutes", "norepinephrine", 0.0),
                                                      ([NE10], "sube la noradrenalina a 12 mcg/min en 5 minutos", "norepinephrine", 10.0), ([], "start dobutamine at 5 mcg/min in 15 minutes", "dobutamine", 0.0),
                                                      ([NE10], "increase norepinephrine to 0.012 mg/min in 5 minutes", "norepinephrine", 10.0), ([NE10], "increase norepinephrine to 12 mcg per minute in 5 minutes", "norepinephrine", 10.0)])
def test_l4_an_order_for_later_that_carries_a_rate_unit_is_a_plan_not_something_done_now(setup, text, drug, before):
    encounter, entries = _run(*setup, text)
    assert _rates(encounter)[drug] == before, "nothing ran now"
    parsed = _parse(text)
    assert not parsed["actions"] and parsed["ledger_plans"][0]["kind"] == "future_timed" and "nothing was given and nothing was scheduled" in parsed["ledger_plans"][0]["receipt"]


@pytest.mark.parametrize("text, runs", [("Start norepinephrine at 10 mcg/min, reassess in 5 minutes", True), ("Start norepinephrine at 10 mcg/min. Reassess in 5 minutes.", True), ("Start norepinephrine at 10 mcg/min and reassess in 5 min", True),
                                        ("Start norepinephrine at 10 mcg/min", True), ("increase norepinephrine to 12 mcg/min over 5 minutes", None), ("Give NS 500 mL in 20 minutes", None)])
def test_l4_nonregression_what_was_not_an_order_for_later_is_read_as_before(text, runs):
    parsed = _parse(text)
    if runs:
        assert any(a.get("type") == "norepinephrine" for a in parsed["actions"]) and not parsed.get("ledger_plans")


def test_l4_the_rate_unit_is_set_aside_only_for_the_four_infusions_and_only_for_this_test():
    clause = "increase norepinephrine to 12 mcg/min in 5 minutes"
    assert time_semantics._runs_for_a_duration(clause) is False
    assert time_semantics._runs_for_a_duration("give heparin 1000 units/h in 5 minutes") is True, "any other clause reads '/h' as it always did"
    assert time_semantics._runs_for_a_duration("give NS at 125 mL/h in 5 minutes") is True
    assert time_semantics._runs_for_a_duration("give diltiazem 10 mg/h in 5 minutes") is True, "a medicine that is not one of the four keeps its '/h'"
    assert time_semantics._runs_for_a_duration("increase norepinephrine to 12 mcg/min over 5 minutes") is True, "'over' still says how long it runs"
    assert time_semantics._runs_for_a_duration("run norepinephrine per minute for an hour, infusing") is True


# =============================================================================================================================================================================
# L-5 / L-6 · FD-ORDER-05 and FD-ORDER-06 · restart and continue, and the P3-479 matrix
# =============================================================================================================================================================================
@pytest.mark.parametrize("text, agent", [("restart norepinephrine", "norepinephrine"), ("resume norepinephrine", "norepinephrine"), ("restart levophed", "norepinephrine"), ("reinicia noradrenalina", "norepinephrine"),
                                         ("reanuda la noradrenalina", "norepinephrine"), ("restart nitroglycerin", "nitroglycerin"), ("restart dobutamine", "dobutamine"), ("restart epinephrine", "epinephrine"),
                                         ("I will restart norepinephrine", "norepinephrine")])
def test_l5_a_restart_with_no_explicit_rate_is_the_approved_incomplete_rate_question(text, agent):
    actions = fp.parse_family_actions(text)["actions"]
    assert len(actions) == 1 and actions[0]["message"] == MESSAGE and actions[0]["incomplete_explicit_rate"] == {"agent": agent, "operation": "start", "reason": "NO_EXPLICIT_RATE"} and not _numbers(actions)


def test_l5_in_the_real_encounter_a_restart_neither_runs_nor_reuses_the_previous_rate():
    encounter, entries = _run(NE10, "stop norepinephrine", "restart norepinephrine")
    assert _the_incomplete_question(entries[-1]) and _rates(encounter)["norepinephrine"] == 0.0
    encounter, entries = _run(NTG20, "stop nitroglycerin", "restart nitroglycerin")
    assert _the_incomplete_question(entries[-1]) and _rates(encounter)["nitroglycerin"] == 0.0


@pytest.mark.parametrize("text, kind, rate", [("restart norepinephrine at 10 mcg/min", "norepinephrine", 10.0), ("reinicia la noradrenalina a 10 mcg/min", "norepinephrine", 10.0), ("restart nitroglycerin at 20 mcg/min", "nitroglycerin", 20.0)])
def test_l5_a_restart_with_an_explicit_rate_is_a_valid_start(text, kind, rate):
    encounter, entries = _run(NE10, "stop norepinephrine", NTG20, "stop nitroglycerin", text)
    assert entries[-1]["executed"] is True and _rates(encounter)[kind] == rate


@pytest.mark.parametrize("text", ["continue norepinephrine at 12", "continue norepinephrine 12", "continue norepinephrine to keep MAP above 65", "continue norepinephrine for MAP 65", "continua la noradrenalina a 12",
                                  "continue nitroglycerin at 12", "continue dobutamine at 12"])
def test_l6_a_continue_with_a_number_and_no_unit_is_incomplete_not_a_silent_continue(text):
    actions = fp.parse_family_actions(text)["actions"]
    assert len(actions) == 1 and actions[0]["message"] == MESSAGE and actions[0]["incomplete_explicit_rate"]["operation"] == "continue" and not _numbers(actions), (text, actions)


def test_l6_in_the_real_encounter_the_continue_asks_and_the_running_rate_is_not_touched():
    encounter, entries = _run(NE10, "continue norepinephrine at 12")
    assert _the_incomplete_question(entries[-1]) and _rates(encounter)["norepinephrine"] == 10.0
    encounter, entries = _run(NE10, "continue norepinephrine at 12 mcg/min")
    assert entries[-1]["executed"] is True and _rates(encounter)["norepinephrine"] == 12.0


@pytest.mark.parametrize("text", ["continue norepinephrine", "continue norepinephrine at current rate", "continue norepinephrine for 2 hours", "continue norepinephrine, reassess in 5 minutes", "continue norepinephrine at 12 mcg/min"])
def test_l6_nonregression_a_continue_with_no_number_or_with_a_time_or_with_its_unit_is_read_as_before(text):
    actions = fp.parse_family_actions(text)["actions"]
    assert [a["type"] for a in actions if a["type"] in DRUGS] == ["norepinephrine"] and not [a for a in actions if a.get("incomplete_explicit_rate")]


def test_p3_479_the_whole_increase_restart_continue_matrix_in_the_real_encounter():
    matrix = [
        ("restart norepinephrine", False, 0.0), ("restart norepinephrine at 10 mcg/min", True, 10.0), ("continue norepinephrine at 12", False, 10.0), ("continue norepinephrine at 12 mcg/min", True, 12.0),
        ("increase norepinephrine", False, 12.0), ("increase norepinephrine to 12", False, 12.0), ("increase norepinephrine to 15 mcg/min", True, 15.0), ("decrease norepinephrine", False, 15.0),
        ("decrease norepinephrine to 4 mcg/min", True, 4.0)]
    encounter = acceptance.Encounter(ta.FRF_CASE)
    encounter.order(NE10)
    # restart needs it stopped first; the matrix is then walked in order
    encounter.order("stop norepinephrine")
    for text, executes, rate in matrix:
        if text == "continue norepinephrine at 12":
            assert _rates(encounter)["norepinephrine"] == 10.0
        entry = encounter.order(text)
        assert entry["executed"] is executes, (text, entry["clarification"])
        if not executes:
            assert entry["clarification"] == MESSAGE
        assert _rates(encounter)["norepinephrine"] == rate, text


# =============================================================================================================================================================================
# L-7 · FD-ORDER-07 · the pipeline barrier reads ``rate_mcg_min``: each barrier alone protects nitroglycerin
# =============================================================================================================================================================================
NTG_TARGETS = ("titrate nitroglycerin to SBP 120", "nitroglycerin to keep SBP <140", "nitroglicerina para PAS 120", "nitroglycerin 20", "increase nitroglycerin to 40", "start nitroglycerin 30", "nitro 15",
               "titrate nitroglycerin to a goal of 100", "titrate nitroglycerin to SBP 120 mmHg")


@pytest.mark.parametrize("text", NTG_TARGETS)
def test_l7_the_pipeline_alone_holds_what_the_historical_reader_gave_as_a_nitroglycerin_rate(text):
    """With the reader of the Phase-2 closure in front (it reads ``nitroglycerin 20`` and ``SBP 120`` as 20 and 120 mcg/min) the pipeline still holds it: the number is not WRITTEN with a mass-per-time unit."""
    old = succession.historical_reader_module()
    parsed = time_semantics.apply(text, old.parse_family_actions(text))
    parsed.setdefault("raw_text", text)
    assert [a for a in parsed["actions"] if a.get("rate_mcg_min") is not None], "the historical reader read a number as a rate (the premise of the test)"
    state = acceptance.Encounter(ta.FRF_CASE).state
    split = op.split_bundle(state, parsed, text=text)
    assert not [a for a in split["run"] if a.get("type") == "nitroglycerin"], (text, split["run"])
    held = [(a, reason) for a, reason, kind in split["held"] if a.get("type") == "nitroglycerin"]
    assert held and all(reason == MESSAGE and a.get("rate_mcg_min") is None for a, reason in held), "the held copy keeps NO number"


@pytest.mark.parametrize("text", NTG_TARGETS)
def test_l7_the_source_alone_holds_it_when_the_pipeline_barrier_is_removed(text, monkeypatch):
    monkeypatch.setattr(op, "incomplete_explicit_rate", lambda action, text="", state=None: None)
    encounter, entries = _run(text)
    assert entries[-1]["executed"] is False and _rates(encounter)["nitroglycerin"] == 0.0


@pytest.mark.parametrize("text", NTG_TARGETS)
def test_l7_and_in_the_real_encounter_with_both_barriers_nothing_runs(text):
    encounter, entries = _run(text)
    assert entries[-1]["executed"] is False and _rates(encounter)["nitroglycerin"] == 0.0 and entries[-1]["clarification"] == MESSAGE


@pytest.mark.parametrize("text, number", [("nitroglycerin 20 mcg/min", 20.0), ("nitroglycerin 0.02 mg/min", 20.0), ("nitroglycerin 1200 mcg/h", 20.0), ("nitroglycerin 20 mcg per minute", 20.0), ("nitroglicerina 20 mcg por minuto", 20.0),
                                          ("titrate nitroglycerin to 30 mcg/min to keep SBP 120", 30.0), ("increase nitroglycerin to 40 mcg/min", 40.0), ("nitro 20 mcg/min", 20.0)])
def test_l7_nonregression_a_nitroglycerin_rate_written_with_its_unit_is_not_held_by_the_barrier(text, number):
    """The barrier (alone, behind the reader of the Phase-2 closure) does not hold a number that IS written with its mass-per-time unit, in any of the forms the reader converts."""
    old = succession.historical_reader_module()
    parsed = time_semantics.apply(text, old.parse_family_actions(text))
    state = acceptance.Encounter(ta.FRF_CASE).state
    actions = [a for a in parsed["actions"] if a.get("type") == "nitroglycerin"]
    assert [a["rate_mcg_min"] for a in actions] == [pytest.approx(number)]
    assert [op.incomplete_explicit_rate(a, text=text, state=state) for a in actions] == [None]
    running = acceptance.Encounter(ta.FRF_CASE)
    running.order(NTG20)
    split = op.split_bundle(running.state, {**parsed, "raw_text": text}, text=text)
    assert [a["rate_mcg_min"] for a in split["run"] if a.get("type") == "nitroglycerin"] == [pytest.approx(number)], "and with the infusion running it is executable"


def test_l7_the_number_must_be_written_in_a_clause_that_names_the_drug_not_in_another_drugs_clause():
    state = acceptance.Encounter(ta.FRF_CASE).state
    action = {"type": "nitroglycerin", "operation": "start", "rate_mcg_min": 20.0}
    assert op.incomplete_explicit_rate(action, text="nitroglycerin 20, propofol 20 mcg/min", state=state)[0] == MESSAGE, "20 mcg/min is propofol's"
    assert op.incomplete_explicit_rate(action, text="nitroglycerin 20 mcg/min, propofol 5 mcg/min", state=state) is None
    assert op.incomplete_explicit_rate(action, text="", state=state) is None, "with no text there is nothing to read the unit from (the page always passes it)"


@pytest.mark.parametrize("kind", ["norepinephrine", "epinephrine", "dobutamine", "nitroglycerin"])
def test_l7_the_field_the_engine_reads_for_any_infusion_is_read_for_any_infusion(kind):
    """``rate_mcg_min`` is the field the engine reads for ANY infusion (``a.get("rate_mcg_min", a.get("rate"))``): a number there that is not written with its unit is held for all four, in every operation."""
    for operation in ("start", "adjust", "continue"):
        action = {"type": kind, "operation": operation, "rate_mcg_min": 65.0}
        result = op.incomplete_explicit_rate(action, text=f"{kind} to MAP 65")
        assert result is not None and result[0] == MESSAGE and result[1].get("rate_mcg_min") is None, (kind, operation)
    for operation in ("start", "continue") + (("adjust",) if kind == "nitroglycerin" else ()):
        action = {"type": kind, "operation": operation, "rate_mcg_min": 65.0}
        assert op.incomplete_explicit_rate(action, text=f"{kind} 65 mcg/min") is None, "the same number, written with its unit, is a rate"


# =============================================================================================================================================================================
# L-8 · FD-ORDER-08 · a numeric-only answer is never an executable rate
# =============================================================================================================================================================================
class _Session(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


def _legacy_reply(pending_action, reply, active_norepinephrine=False):
    import app
    from test_coupled_encounter import patient
    state = patient()
    if active_norepinephrine:
        state["treatments"].update({"norepinephrine": True, "norepinephrine_rate": 10, "norepinephrine_units": "mcg/min"})
    session = _Session(state=state, pending_action=dict(pending_action))
    original = app.st
    app.st = SimpleNamespace(session_state=session)
    try:
        return app.try_resolve_pending_action(reply)
    finally:
        app.st = original


@pytest.mark.parametrize("active", [True, False])
@pytest.mark.parametrize("reply", ["12", "12.5", " 12 ", "MAP 65", "stop", "mcg/min", "65"])
def test_l8_the_legacy_page_asks_again_when_the_answer_to_what_rate_is_not_a_rate_with_its_unit(reply, active):
    result = _legacy_reply({"type": "norepinephrine", "operation": "start", "rate": None, "units": None}, reply, active)
    assert result and result.get("clarification") and not result.get("parsed"), (reply, active, result)
    result = _legacy_reply({"type": "dobutamine", "operation": "start", "rate": None, "units": None}, reply)
    assert result and result.get("clarification") and not result.get("parsed"), (reply, result)


@pytest.mark.parametrize("active", [True, False])
@pytest.mark.parametrize("reply, rate, units", [("12 mcg/min", 12.0, "mcg/min"), ("0.1 mcg/kg/min", 0.1, "mcg/kg/min"), ("restart at 10 mcg/min", 10.0, "mcg/min")])
def test_l8_nonregression_the_legacy_page_still_takes_a_rate_written_with_its_unit(reply, rate, units, active):
    result = _legacy_reply({"type": "norepinephrine", "operation": "start", "rate": None, "units": None}, reply, active)
    action = result["parsed"]["actions"][0]
    assert (action["rate"], action["units"]) == (rate, units)


def test_l8_the_dobutamine_answer_still_needs_its_usual_unit_written_and_a_bare_number_is_not_that_unit():
    assert _legacy_reply({"type": "dobutamine", "operation": "start", "rate": None, "units": None}, "5 mcg/kg/min")["parsed"]["actions"][0]["rate"] == 5.0
    assert _legacy_reply({"type": "dobutamine", "operation": "start", "rate": None, "units": None}, "12")["clarification"].startswith("Please specify the dobutamine dose in mcg/kg/min")


@pytest.mark.parametrize("held_text", ["increase norepinephrine", "increase norepinephrine to 12", "titrate norepinephrine to MAP 65", "restart norepinephrine", "continue norepinephrine at 12"])
@pytest.mark.parametrize("reply", ["12", "12.5", "MAP 65", "stop", "mcg/min", "65"])
def test_l8_in_the_family_path_a_numeric_only_or_unitless_answer_never_completes_a_held_infusion_order(held_text, reply):
    encounter = acceptance.Encounter(ta.FRF_CASE)
    encounter.order(NE10)
    held = pending.hold_incomplete_bundle(boundary._parse(held_text), encounter.state)
    assert held, held_text
    answer = pending.complete_bundle(deepcopy(held), reply, encounter.state)
    if answer is None or answer.get("superseded") or answer.get("clarification"):
        return
    assert not [a for a in answer["parsed"]["actions"] if a.get("type") in DRUGS and (a.get("rate") is not None or a.get("rate_mcg_min") is not None)], (held_text, reply, answer)


@pytest.mark.parametrize("reply", ["12", "MAP 65", "stop", "mcg/min", "restart at 10 mcg/min", "12 mcg/min", "0.1 mcg/kg/min"])
def test_l8_a_standalone_reply_in_the_real_encounter_is_not_an_order_for_any_infusion(reply):
    """With no question pending, the same words are read as a fresh order: none of them is a vasoactive order."""
    encounter, entries = _run(NE10, reply)
    assert _rates(encounter)["norepinephrine"] == 10.0 and entries[-1]["executed"] is False


# =============================================================================================================================================================================
# P3-484 · the findings of the INDEPENDENT adversarial review (F01 to F13), each reproduced before it was repaired
# =============================================================================================================================================================================
def _answer_to(held_text, reply, setup=()):
    """The family path of an answer: held order -> reply -> the page's completion -> the real execution."""
    encounter = acceptance.Encounter(ta.FRF_CASE)
    for text in setup:
        encounter.order(text)
    held = pending.hold_incomplete_bundle(boundary._parse(held_text), encounter.state)
    assert held, held_text
    answer = pending.complete_bundle(deepcopy(held), reply, encounter.state)
    before = _rates(encounter)
    if not answer or not answer.get("parsed"):
        return before, _rates(encounter), answer
    entry = encounter._execute(answer["parsed"], answer["parsed"]["raw_text"])
    return before, _rates(encounter), entry


@pytest.mark.parametrize("held_text, reply, drug, rate", [("start nitroglycerin", "20 mcg/min", "nitroglycerin", 20.0), ("start nitro", "at 20 mcg/min", "nitroglycerin", 20.0),
                                                            ("start nitroglycerin", "nitroglycerin 20 mcg/min", "nitroglycerin", 20.0), ("start nitroglycerin", "20 mcg per min", "nitroglycerin", 20.0),
                                                            ("start norepinephrine", "5 mcg/min", "norepinephrine", 5.0), ("start dobutamine", "5 mcg/min", "dobutamine", 5.0)])
def test_f01_the_answer_to_a_held_infusion_rate_question_runs_it_for_every_infusion(held_text, reply, drug, rate):
    """Nitroglycerin was refused for good: the page appends the answer on a line of its own and the barrier looked for the rate in the clause that names the drug."""
    before, after, entry = _answer_to(held_text, reply)
    assert before[drug] == 0.0 and after[drug] == pytest.approx(rate), (held_text, reply, after)


@pytest.mark.parametrize("unit", ["mcg/min", "ug/min", "\u00b5g/min", "\u03bcg/min", "micrograms/min", "microgramos/min", "mcg per min", "mcg por minuto"])
def test_f02_every_way_to_write_micrograms_per_minute_runs_for_nitroglycerin(unit):
    encounter, entries = _run(NTG20, f"increase nitroglycerin to 30 {unit}")
    assert _rates(encounter)["nitroglycerin"] == 30.0, (unit, entries[-1])


@pytest.mark.parametrize("text", ["increase norepinephrine to 12 mcg/min to reach MAP 65 in 10 minutes", "increase norepinephrine to 12 mcg/min within 10 minutes"])
def test_f03_an_order_with_a_time_in_it_is_read_conservatively_and_declared_as_a_plan_never_run_at_the_wrong_time(text):
    """Declared limitation: "in 10 minutes" after a vasoactive order is a plan (nothing ran, nothing was scheduled). The goal phrase cannot be told from the time of the order."""
    encounter, entries = _run(NE10, text)
    assert _rates(encounter)["norepinephrine"] == 10.0
    parsed = _parse(text)
    assert not parsed["actions"] and parsed["ledger_plans"][0]["kind"] == "future_timed"


@pytest.mark.parametrize("text", ["stop norepinephrine but monitor BP", "stop norepinephrine but start fluids", "stop norepinephrine but keep an eye on the MAP", "suspende noradrenalina pero vigila la PAM",
                                  "stop norepinephrine but leave the line in"])
def test_f04_a_stop_with_a_but_after_the_name_still_stops_that_infusion(text):
    encounter, entries = _run(NE10, DOB5, text)
    assert _rates(encounter)["norepinephrine"] == 0.0 and _rates(encounter)["dobutamine"] == 5.0, text


@pytest.mark.parametrize("text, setup, kept", [("espera 5 minutos y luego reanuda dobutamina", (DOB5,), "dobutamine"), ("wait 5 minutes then restart dobutamine", (DOB5,), "dobutamine"),
                                               ("cuando llegue el lactato luego reinicia dobutamina", (DOB5,), "dobutamine"), ("resume adrenalina without salbutamol 5 mcg/min", (), "epinephrine")])
def test_f06_an_incomplete_order_that_waits_or_is_shared_is_asked_never_dropped_in_silence(text, setup, kept):
    """It vanished: no action, no question and no record. Now the approved question (or the one-rate question) is asked and nothing runs."""
    actions = fp.parse_family_actions(text)["actions"]
    questions = [a for a in actions if a.get("type") == "clarification"]
    assert questions and (questions[0].get("incomplete_explicit_rate") or questions[0]["message"] == fp._AMBIGUOUS_RATE), (text, actions)
    encounter, entries = _run(*setup, text)
    assert entries[-1]["executed"] is False and entries[-1]["clarification"]
    assert _rates(encounter)[kept] == (5.0 if kept == "dobutamine" and setup else 0.0)


@pytest.mark.parametrize("text, setup", [("stop all except dobutamine and norepinephrine", (NE10, DOB5)), ("stop all medications except norepinephrine and dobutamine", (NE10, DOB5)),
                                         ("stop propofol but keep dobutamine and norepinephrine", (NE10, DOB5)), ("stop all but dobutamine, norepinephrine", (NE10, DOB5)),
                                         ("suspende todo excepto noradrenalina y nitroglicerina", (NE10, NTG20)), ("suspende todo menos nitroglicerina, noradrenalina", (NE10, NTG20)),
                                         ("detén todo menos noradrenalina y dobutamina", (NE10, DOB5)), ("stop all except propofol and norepinephrine", (NE10,))])
def test_f07_an_exception_keeps_every_infusion_it_lists_not_only_the_first(text, setup):
    encounter, entries = _run(*setup, text)
    for name, line in (("norepinephrine", NE10), ("dobutamine", DOB5), ("nitroglycerin", NTG20)):
        if line in setup:
            assert _rates(encounter)[name] > 0.0, (text, name, _rates(encounter))


@pytest.mark.parametrize("text, setup", [("stop norepinephrine while dobutamine continues", (NE10, DOB5)), ("stop norepinephrine with dobutamine running", (NE10, DOB5)),
                                         ("stop norepinephrine while epinephrine continues", (NE10, "Start epinephrine at 3 mcg/min.")), ("stop nitroglycerin while norepinephrine continues", (NE10, NTG20)),
                                         ("stop norepinephrine while nitroglycerin continues", (NE10, NTG20)), ("stop dobutamine along with norepinephrine running", (NE10, DOB5))])
def test_f08_one_stop_that_names_two_infusions_never_picks_one_by_the_readers_priority(text, setup):
    """Nothing is stopped and the order is asked: the reader used to stop the infusion that comes first in its own fixed priority, which was the one the resident wanted kept."""
    encounter, entries = _run(*setup, text)
    before = _rates(_run(*setup)[0])
    assert _rates(encounter) == before, (text, _rates(encounter), before)
    assert entries[-1]["executed"] is False


def test_f08_two_infusions_named_in_a_list_are_both_stopped_as_before():
    encounter, entries = _run(NE10, DOB5, "stop norepinephrine and dobutamine")
    assert _rates(encounter)["norepinephrine"] == 0.0 and _rates(encounter)["dobutamine"] == 0.0


@pytest.mark.parametrize("name", ["NTG", "GTN", "TNG", "NE", "treprostinil", "epoprostenol", "ephedrine", "levo", "nesiritide", "vasopressin", "propofol", "phenylephrine"])
def test_f09_a_rate_beside_the_name_of_another_medicine_or_another_way_to_write_an_infusion_is_not_the_infusions(name):
    for text, setup, drug in ((f"increase norepinephrine to MAP 65 with {name} 20 mcg/min", (NE10,), "norepinephrine"), (f"increase nitroglycerin to MAP 65 with {name} 5 mcg/min", (NTG20,), "nitroglycerin")):
        if name in ("NTG", "GTN", "TNG") and drug == "nitroglycerin" or name in ("NE", "levo") and drug == "norepinephrine":
            continue  # the drug's own other name: it is the drug's own rate
        encounter, entries = _run(*setup, text)
        assert _rates(encounter)[drug] in (10.0, 20.0), (text, _rates(encounter))
        assert entries[-1]["executed"] is False, text


@pytest.mark.parametrize("text", ["start norepinephrine 12 mcg/min of propofol", "start norepinephrine at 12 mcg/min of vasopressin", "inicia noradrenalina 12 mcg/min de insulina"])
def test_f10_a_rate_followed_by_of_another_drug_belongs_to_that_drug(text):
    encounter, entries = _run(text)
    assert _rates(encounter)["norepinephrine"] == 0.0 and entries[-1]["executed"] is False


@pytest.mark.parametrize("held_text, reply", [("start norepinephrine", "dobutamine 12 mcg/min"), ("start norepinephrine", "12 mcg/min of propofol"), ("start dobutamine", "12 mcg/min norepinephrine"),
                                              ("start norepinephrine", "12 mcg/min in 5 minutes"), ("start dobutamine", "in 5 minutes 12 mcg/min"), ("start nitroglycerin", "norepinephrine 20 mcg/min"),
                                              ("start norepinephrine", "12 mcg/min and 5 mcg/min")])
def test_f11_the_answer_is_for_the_drug_that_asked_one_rate_now(held_text, reply):
    before, after, answer = _answer_to(held_text, reply)
    assert after == before, (held_text, reply, after)
    assert not answer or answer.get("clarification") or answer.get("superseded") or answer.get("executed") is False, (held_text, reply, answer)


@pytest.mark.parametrize("reply", ["dobutamine 12 mcg/min", "12 mcg/min of propofol", "dopamine 12 mcg/min", "12 mcg/min and 5 mcg/min", "12 mcg/min in 5 minutes"])
def test_f11_the_legacy_page_asks_again_for_another_drugs_rate_two_rates_or_a_time(reply):
    result = _legacy_reply({"type": "norepinephrine", "operation": "start", "rate": None, "units": None}, reply)
    assert result and result.get("clarification") and not result.get("parsed"), (reply, result)
    other = reply.replace("dobutamine", "norepinephrine").replace("12 mcg/min", "12 mcg/kg/min").replace("5 mcg/min", "5 mcg/kg/min")
    result = _legacy_reply({"type": "dobutamine", "operation": "start", "rate": None, "units": None}, other)
    assert result and result.get("clarification") and not result.get("parsed"), (other, result)


@pytest.mark.parametrize("text, setup", [("stop the norepinephrine infusion in 5 minutes", (NE10,)), ("increase the norepinephrine infusion to 12 mcg/min in 5 minutes", (NE10,)), ("start norepinephrine infusion at 12 mcg/min in 5 minutes", ()),
                                         ("increase the infusion to 12 mcg/min in 5 minutes", (NE10,)), ("increase norepinephrine to 12 \u00b5g/min in 5 minutes", (NE10,)),
                                         ("increase norepinephrine to 0.1 mcg per kg per minute in 5 minutes", (NE10,)), ("increase epi to 5 mcg/min in 5 minutes", ("Start epinephrine at 3 mcg/min.",))])
def test_f12_the_words_that_name_the_infusion_and_its_rate_unit_are_not_a_duration(text, setup):
    encounter, entries = _run(*setup, text)
    expected = {"norepinephrine": 10.0 if NE10 in setup else 0.0, "epinephrine": 3.0 if setup and setup[0].startswith("Start epinephrine") else 0.0}
    assert {name: _rates(encounter)[name] for name in expected} == expected, (text, _rates(encounter))
    assert not _parse(text)["actions"] and _parse(text)["ledger_plans"]


@pytest.mark.parametrize("text", ["start nor-epi at 5 mcg/min", "start nor epi at 5 mcg/min", "increase nor-epi to 12 mcg/min", "restart nor-epi at 5 mcg/min"])
def test_f13_nor_epi_is_never_epinephrine(text):
    encounter, entries = _run(NE10, text)
    assert _rates(encounter)["epinephrine"] == 0.0 and _rates(encounter)["norepinephrine"] == 10.0, (text, _rates(encounter))
    assert not [a for a in fp.parse_family_actions(text)["actions"] if a.get("type") == "epinephrine"]


def test_f13_epinephrine_by_every_name_it_was_read_by_is_still_read():
    for text in ("start epinephrine at 3 mcg/min", "start epi at 3 mcg/min", "inicia adrenalina a 3 mcg/min", "start adrenaline at 3 mcg/min"):
        assert [(a["type"], a["rate"]) for a in fp.parse_family_actions(text)["actions"]] == [("epinephrine", 3.0)], text


def test_f13_the_alias_patterns_themselves_never_match_nor_epi():
    for kind, text in (("epinephrine", "start nor-epi at 5"), ("epinephrine", "start nor epi at 5")):
        assert not re.search(r"\b(?:" + fp._VASOACTIVE_ALIASES[kind] + r")\b", text), text
    assert re.search(r"\b(?:" + fp._VASOACTIVE_ALIASES["epinephrine"] + r")\b", "start epi at 5")


def test_f07_the_exception_piece_itself_hands_the_next_piece_no_verb():
    """The vasoactive branch ends the stop on its own, not only through the list loop that reads the pieces: a direct call returns no inherited verb."""
    actions, verb = fp._parse_piece("stop all except dobutamine")
    assert verb is None and actions and actions[0]["type"] == "clarification"
    actions, verb = fp._parse_piece("stop NS but keep norepinephrine")
    assert verb is None and actions and actions[0]["type"] == "clarification"
    actions, verb = fp._parse_piece("stop norepinephrine")
    assert verb is not None and actions[0]["operation"] == "stop", "a plain stop keeps its verb for the list that follows"


def test_f01_a_continuation_that_names_another_infusion_is_never_evidence_for_this_one():
    held = "start nitroglycerin\nClarification: norepinephrine 20 mcg/min"
    assert op._written_absolute_rates(held, "nitroglycerin") == []
    question = op.incomplete_explicit_rate({"type": "nitroglycerin", "operation": "start", "rate_mcg_min": 20.0}, text=held, state={})
    assert question and question[0] == MESSAGE and question[1]["rate_mcg_min"] is None
    assert op.incomplete_explicit_rate({"type": "nitroglycerin", "operation": "start", "rate_mcg_min": 20.0}, text="start nitroglycerin\nClarification: at 20 mcg/min", state={}) is None


# =============================================================================================================================================================================
# P3-482 · valid orders run EXACTLY as before: the same engine state, step by step, under the live reader and under the reader of the Phase-2 closure
# =============================================================================================================================================================================
VALID_SCRIPTS = (
    ("Start norepinephrine at 5 mcg/min.", "Reassess in 2 minutes.", "increase norepinephrine to 10 mcg/min", "Reassess in 2 minutes.", "decrease norepinephrine to 4 mcg/min", "Reassess in 2 minutes.", "stop norepinephrine"),
    ("Start norepinephrine at 10 mcg/min, reassess in 2 minutes.", "stop norepinephrine. Reassess in 2 minutes.", "restart norepinephrine at 10 mcg/min", "Reassess in 2 minutes."),
    ("Start nitroglycerin at 20 mcg/min.", "increase nitroglycerin to 40 mcg/min", "Reassess in 2 minutes.", "decrease nitroglycerin to 10 mcg/min", "stop nitroglycerin"),
    ("Start norepinephrine at 0.1 mcg/kg/min.", "Reassess in 2 minutes."),
    ("Start dobutamine at 5 mcg/kg/min.", "Start epinephrine at 2 mcg/min.", "stop epinephrine", "stop dobutamine"),
    ("Start norepinephrine at 10 mcg/min.", "increase the infusion to 12 mcg/min", "Subele la infusion a 15 mcg/min", "Stop the infusion."),
    ("Start norepinephrine at 10 mcg/min and nitroglycerin at 20 mcg/min.", "stop norepinephrine and nitroglycerin"),
    ("inicio noradrenalina 8 mcg/min objetivo PAM 65", "Reevaluar en 2 minutos", "sube la noradrenalina a 10 mcg/min", "suspende la noradrenalina"),
    ("Start norepinephrine at 10 mcg/min to keep MAP above 65.", "continue norepinephrine at 12 mcg/min", "continue norepinephrine", "Reassess in 3 minutes."))


def _trajectory(script, reader):
    import family_parser as live
    original = live.parse_family_actions
    live.parse_family_actions = reader.parse_family_actions
    try:
        encounter = acceptance.Encounter(ta.FRF_CASE)
        out = []
        for text in script:
            entry = encounter.order(text)
            state = encounter.state
            out.append(json.dumps({"executed": entry["executed"], "clar": entry["clarification"], "family_state": state.get("family_state"), "observable": state.get("observable"),
                                   "treatments": state.get("treatments"), "sim_time": state.get("sim_time")}, sort_keys=True, default=str))
        return out
    finally:
        live.parse_family_actions = original


@pytest.mark.parametrize("script", VALID_SCRIPTS)
def test_p3_482_a_valid_order_runs_with_no_numerical_drift_against_the_reader_of_the_first_successor(script):
    """The accepted behavior -- explicit supported orders, START / INCREASE / DECREASE / STOP / SEQUENCE / RESTART -- gives the same engine state at every step under the live reader and under the reader
    of the first successor (the one the faculty reviewed and ratified)."""
    assert _trajectory(script, fp) == _trajectory(script, succession.target_safety_reader_module())


@pytest.mark.parametrize("script", [script for script in VALID_SCRIPTS if not any(word in " ".join(script).lower() for word in ("restart", "reinicia"))])
def test_p3_482_and_against_the_reader_of_the_phase_two_closure_for_every_order_it_read(script):
    """The restart verb was not read by the closure reader (the first successor added it), so the scripts that restart are compared with the first successor only."""
    assert _trajectory(script, fp) == _trajectory(script, succession.historical_reader_module())


def test_p3_482_the_accepted_manual_rate_control_sequences_keep_their_exact_rates():
    encounter = acceptance.Encounter(ta.FRF_CASE)
    seen = []
    for text in ("Start norepinephrine at 5 mcg/min.", "increase norepinephrine to 10 mcg/min", "decrease norepinephrine to 4 mcg/min", "stop norepinephrine", "restart norepinephrine at 10 mcg/min"):
        encounter.order(text)
        seen.append(_rates(encounter)["norepinephrine"])
    assert seen == [5.0, 10.0, 4.0, 0.0, 10.0]
