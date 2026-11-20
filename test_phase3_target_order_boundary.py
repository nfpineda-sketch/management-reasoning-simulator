"""P3-452 to P3-456: a physiologic TARGET is never a RATE; a number without units is never a rate (faculty decision FD-NR-05, 2026-11-20).

THE DEFECT, from the trace of the real encounter. ``titrate norepinephrine to MAP 65`` leaves the order reader as an adjustment to a rate of 65 with NO units (its bare-number fallback reads the only number of
the clause as the rate). The engine's completion of an adjustment (``active_order_context.complete_active_order``) then takes the missing units from the running infusion, so the order was executed as 65
mcg/min. Two layers contributed (the reader invented the rate, the engine made it executable); the mirror and the shadow mapping read the order as written and refused it, so they were never the cause.

THE REPAIR, in a layer that is NOT frozen. The reader (``family_parser.py``), the engine (``family_engine.py``) and the completion (``active_order_context.py``) are pinned by the pre-Phase-1 reader freeze and by the
Phase-2 calibration freeze: changing them is a decision of its own and was not made. The repair is made before the engine, in the order pipeline (``order_pipeline.split_bundle``): an infusion order that carries a
rate WITHOUT units is held as a question, nothing is executed, and the held copy keeps no number. The rule is structural: it does not depend on a list of words, so a MAP, a PA, a TAM, a heart rate or a typo are
all the same thing -- a number without units.

These tests read the reader (to show what it still emits), the pipeline, the real encounter (reader -> pipeline -> engine -> mirror) and the shadow mapping. They change no physiology and no authority.
"""
import itertools
import json

import pytest

import family_parser as fp
import language
import order_pipeline as op
import pending_family_orders as pending
import pilot_acceptance as acceptance
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_tone_support as ts
import test_prephase1_reader_freeze as reader_freeze
import test_tone_pathway_analysis as ta
import test_tone_titration_analysis as tta
import time_semantics

START5, START10 = "Start norepinephrine at 5 mcg/min.", "Start norepinephrine at 10 mcg/min."
UNIT_COMPLETED = ("norepinephrine", "dobutamine", "epinephrine")
INFUSION_KINDS = UNIT_COMPLETED + ("infusion_adjustment",)

#: Orders that name a physiologic target (or any other number) and give no rate with units: all must be held. Includes every class of leak the independent review found in the first (vocabulary) design.
TARGET_TEXTS = (
    "titrate norepinephrine to MAP 65", "titrate norepinephrine to MAP >65", "titrate norepinephrine to MAP > 65 mmHg", "titrate norepinephrine to MAP of 65", "titrate norepinephrine to SBP >90",
    "wean norepinephrine to MAP 65", "reduce norepinephrine to MAP 70", "decrease norepinephrine to MAP 75", "increase norepinephrine to keep MAP above 65", "continue norepinephrine to keep MAP above 65",
    "norepinephrine to keep MAP > 65", "norepinephrine for MAP 65", "titrate noradrenaline to MAP 65", "titrate norepi to MAP 65",
    "titula noradrenalina a PAM 65", "ajusta la noradrenalina para PAM >65", "noradrenalina a PAS 100", "sube noradrenalina hasta PAM 65", "titrate dobutamine to MAP 65", "titrate epinephrine to MAP 65",
    # the classes of the independent review that a list of pressure words could not hold
    "Titrate norepinephrine to TAM 65.", "Titula noradrenalina a PA 100.", "Titula noradrenalina a PA > 90.", "Titula noradrenalina a TAS 100.", "Titula noradrenalina a TAD 60.", "Titrate norepinephrine to a goal of 65.",
    "Titrate norepinephrine to target 65.", "Titula noradrenalina a una meta de 65.", "Titula noradrenalina a un objetivo de 65.", "Continue norepinephrine for TAM 65.", "Titula noradrenalina hasta 65 de PAM.",
    "Titrate norepinephrine to 65 MAP.", "Titrate norepinephrine to 65 (mmHg).", "Titrate norepinephrine to mmHg 65.", "Titrate to MAP between 65 and 70 on norepinephrine.",
    "Titrate norepinephrine to keep the mean arterial pressure consistently above the threshold of 65.", "Titrate norepinephrine until the patient's mean arterial pressure on the arterial line reaches 65",
    "Titrate norepinephrine to HR 100", "Titrate dobutamine to CI 2.5", "Titrate norepinephrine to CPP 70", "Titrate norepinephrine to a mean of 65", "Increase norepinephrine to 12")
#: The same drugs and verbs with an EXPLICIT rate with units: these run exactly as before.
EXPLICIT = {
    "increase norepinephrine to 10 mcg/min": {"type": "norepinephrine", "operation": "adjust", "rate": 10.0, "units": "mcg/min"},
    "decrease norepinephrine to 4 mcg/min": {"type": "norepinephrine", "operation": "adjust", "rate": 4.0, "units": "mcg/min"},
    "norepinephrine 10 mcg/min": {"type": "norepinephrine", "operation": "start", "rate": 10.0, "units": "mcg/min"},
    "Start norepinephrine at 5 mcg/min": {"type": "norepinephrine", "operation": "start", "rate": 5.0, "units": "mcg/min"},
    "stop norepinephrine": {"type": "norepinephrine", "operation": "stop", "rate": None, "units": None},
    "increase norepinephrine to 10 mcg/min to keep MAP above 65": {"type": "norepinephrine", "operation": "adjust", "rate": 10.0, "units": "mcg/min"},
    "Start norepinephrine at 10 mcg/min, MAP 58": {"type": "norepinephrine", "operation": "start", "rate": 10.0, "units": "mcg/min"},
    "norepinephrine 20 mcg per minute": {"type": "norepinephrine", "operation": "start", "rate": 20.0, "units": "mcg/min"},
    "inicio noradrenalina 8 mcg/min objetivo PAM 65": {"type": "norepinephrine", "operation": "start", "rate": 8.0, "units": "mcg/min"},
    "norepinephrine 0.1 mcg/kg/min": {"type": "norepinephrine", "operation": "start", "rate": 0.1, "units": "mcg/kg/min"},
    "Start norepinephrine at 0.1 mcg/kg/min titrate to MAP 65": {"type": "norepinephrine", "operation": "start", "rate": 0.1, "units": "mcg/kg/min"},
    "dobutamine 5 mcg/kg/min": {"type": "dobutamine", "operation": "start", "rate": 5.0, "units": "mcg/kg/min"},
    "epinephrine 0.05 mcg/kg/min": {"type": "epinephrine", "operation": "start", "rate": 0.05, "units": "mcg/kg/min"},
}


def _parse(text: str) -> dict:
    parsed = time_semantics.apply(text, fp.parse_family_actions(text))
    parsed.setdefault("raw_text", text)
    return parsed


def _split(state, text: str) -> dict:
    return op.split_bundle(state, _parse(text), text=text)


def _a_rate_without_units(action: dict) -> bool:
    if action.get("type") in UNIT_COMPLETED:
        return action.get("rate") is not None and not action.get("units")
    return action.get("type") == "infusion_adjustment" and action.get("rate_value") is not None and not action.get("rate_units")


def _numbers(action: dict) -> list:
    return [value for key, value in action.items() if key in ("rate", "rate_value", "rate_mcg_min") and value is not None]


@pytest.fixture(scope="module")
def running():
    """The state of the real encounter with 10 mcg/min of norepinephrine running: what a pressure goal used to be completed against."""
    encounter = acceptance.Encounter(ta.FRF_CASE)
    encounter.order(START10)
    encounter.order("Reassess in 2 minutes.")
    return encounter.state


def _play(*texts: str):
    """One script through the REAL encounter (the page's family branch) with the shadow mirror on, on the GI case the manual rate control was reviewed on."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(ta.FRF_CASE)
        entries = [encounter.order(text) for text in texts]
        mirrored = tuple(encounter.shadow.runner.mirrored)
        return encounter, entries, mirrored


def _rate(encounter) -> float:
    return float((encounter.state.get("family_state") or {}).get("norepinephrine") or 0.0)


# -- the reader is untouched: what it still emits -------------------------------------------------------------------------------------------------------------------------------------
def test_t1_the_reader_is_frozen_and_still_emits_the_number_as_a_rate_without_units():
    """CHARACTERIZATION. The reader's bare-number fallback is the origin of the defect; the reader is frozen (the pre-Phase-1 reader freeze, and the Phase-2 calibration freeze), so what it emits is recorded here and the
    pipeline is the guard. If the reader is ever repaired at its source (a faculty decision), this test says so by failing."""
    assert reader_freeze.test_prephase1_reader_freeze_is_exact() is None
    assert _parse("titrate norepinephrine to MAP 65")["actions"] == [{"type": "norepinephrine", "rate": 65.0, "units": None, "operation": "adjust"}]
    assert _parse("titrate norepinephrine to MAP >65")["actions"] == [{"type": "norepinephrine", "rate": 65.0, "units": None, "operation": "adjust"}]
    assert _parse("Titula noradrenalina a PA 100")["actions"][0]["rate"] == 100.0, "any unit-less number leaves the reader as a rate: a list of words could never hold them all"


# -- the pipeline: a number without units is never a rate ---------------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("text", TARGET_TEXTS)
def test_t2_an_infusion_order_with_a_number_and_no_units_is_held_and_nothing_runs(running, text):
    split = _split(running, text)
    infusions = [action for action in split["run"] if action.get("type") in INFUSION_KINDS]
    assert not [action for action in infusions if _a_rate_without_units(action)], (text, infusions)
    held = [(action, reason) for action, reason, kind in split["held"] if action.get("type") in INFUSION_KINDS]
    assert held and all(reason.endswith("or say cancel.") and "without units" in reason for _, reason in held), (text, split["held"])
    assert all(not _numbers(action) for action, _ in held), "the held copy keeps NO number: a later answer must not complete it into a dose"
    assert split["question"] and "A number without units" in split["question"]


@pytest.mark.parametrize("text, expected", sorted(EXPLICIT.items()))
def test_t3_an_explicit_rate_with_units_runs_exactly_as_before(running, text, expected):
    """FD-NR-01: START, INCREASE, DECREASE and STOP by an explicit absolute rate are untouched; a pressure that only gives the REASON beside an explicit rate does not change the order."""
    split = _split(running, text)
    infusions = [action for action in split["run"] if action.get("type") in INFUSION_KINDS]
    assert len(infusions) == 1 and {key: infusions[0].get(key) for key in expected} == expected and not split["held"], (text, split)


def test_t4_a_stop_is_never_held_whatever_number_is_beside_it(running):
    """A stop needs no rate. ``stop norepinephrine MAP 75`` carries 75 as its (inert) rate in the reader; it has no units and it is NOT held."""
    for text in ("stop norepinephrine MAP 75", "stop norepinephrine, MAP is 75", "stop norepinephrine, goal MAP 65", "suspende la noradrenalina PAM 80", "Stop the infusion."):
        split = _split(running, text)
        assert not split["held"] and [action["operation"] for action in split["run"] if action.get("type") in INFUSION_KINDS] == ["stop"], (text, split)


def test_t5_the_orders_the_first_design_held_by_mistake_run_again(running):
    """The independent review found valid orders a list of pressure words wrongly held. The rule is about the units now, so they run exactly as they did before any repair."""
    for text in ("Continue norepinephrine at current rate BP 110/70.", "Continue norepinephrine since MAP goal is met.", "Continue norepinephrine as the target MAP was reached", "Continue dobutamine with BP stable at 110/70",
                 "Start epinephrine for anaphylaxis with BP 70/40"):
        split = _split(running, text)
        assert not [reason for _, reason, _ in split["held"] if "without units" in reason], (text, split["held"])


def test_t5b_the_role_named_infusion_never_read_a_bare_number_in_the_reader():
    """``Increase the infusion to 65``: the reader's role-named path (no drug named) reads a rate only WITH its units, so it carries no number to hold; a rate with units still runs."""
    assert _parse("Increase the infusion to 65")["actions"] == [{"type": "infusion_adjustment", "operation": "adjust", "rate_value": None, "rate_units": None}]
    assert _parse("Increase the infusion to 20 mcg/min")["actions"][0]["rate_value"] == 20.0


def test_t6_the_weight_based_dose_is_read_as_written_and_never_converted_by_the_pipeline_or_the_shadow():
    action = _parse("norepinephrine 0.1 mcg/kg/min")["actions"][0]
    assert (action["rate"], action["units"], action["operation"]) == (0.1, "mcg/kg/min", "start") and op.unitless_infusion_rate(action) is None
    alone, why_alone = ts.order_disposition(action)
    assert alone is None and why_alone == ts.GAP_UNITS.format(units=repr("mcg/kg/min")), "the shadow refuses the units: it never converts"
    rate, why = ts.order_disposition(action, {"type": "norepinephrine", "operation": "start", "rate": 0.1, "units": "mcg/kg/min"})
    assert rate is None and why and "units" in why


def test_t7_the_unit_rule_in_isolation():
    unitless = op.unitless_infusion_rate
    assert unitless({"type": "norepinephrine", "operation": "adjust", "rate": 65.0, "units": None}) == (op.UNITS_REQUIRED.format(name="Norepinephrine"), {"type": "norepinephrine", "operation": "adjust", "rate": None, "units": None})
    assert unitless({"type": "dobutamine", "operation": "start", "rate": 5.0, "units": ""})[0].startswith("Dobutamine was written with a rate but no units")
    assert unitless({"type": "infusion_adjustment", "operation": "adjust", "rate_value": 65.0, "rate_units": None})[1]["rate_value"] is None
    for not_held in ({"type": "norepinephrine", "operation": "stop", "rate": 5.0, "units": None}, {"type": "norepinephrine", "operation": "adjust", "rate": 10.0, "units": "mcg/min"},
                     {"type": "norepinephrine", "operation": "adjust", "rate": None, "units": None}, {"type": "infusion_adjustment", "operation": "stop", "rate_value": 5.0, "rate_units": None},
                     {"type": "infusion_adjustment", "operation": "adjust", "rate_value": 10.0, "rate_units": "mcg/min"}, {"type": "oxygen", "operation": "adjust", "rate": 4.0}, {"type": "clarification", "message": "x"}, "text", None):
        assert unitless(not_held) is None, not_held


def test_t8_a_generated_corpus_of_targets_never_reaches_the_engine_as_a_rate(running):
    """The structural invariant over a generated corpus (the classes of the independent review: every pressure word and abbreviation, goal words, the number before or after the word, units spelled or absent, in two
    languages): whatever the phrasing, no infusion order that carries a number without units is left to run."""
    verbs = ("titrate", "wean", "reduce", "increase", "decrease", "continue", "start", "adjust", "titula", "ajusta", "sube", "baja")
    drugs = ("norepinephrine", "noradrenalina", "dobutamine", "epinephrine")
    words = ("MAP", "PAM", "TAM", "PA", "TAS", "TAD", "SBP", "PAS", "BP", "HR", "mean", "CPP", "goal of", "target", "meta de", "objetivo de", "mmHg")
    checked = 0
    for verb, drug, word, number in itertools.product(verbs, drugs, words, (65, 100)):
        for text in (f"{verb} {drug} to {word} {number}", f"{verb} {drug} to {number} {word}"):
            split = _split(running, text)
            leaked = [action for action in split["run"] if action.get("type") in INFUSION_KINDS and _a_rate_without_units(action)]
            assert not leaked, (text, leaked)
            checked += 1
    assert checked == len(verbs) * len(drugs) * len(words) * 2 * 2


def test_t9_a_reply_that_only_gives_the_units_cannot_complete_the_held_order_into_a_dose(running):
    """The held order is kept as a pending question (the page's own mechanism). Because the held copy keeps no number, an answer of ``mcg/min`` cannot make 65 mcg/min of it."""
    text = "Titrate norepinephrine to MAP 65."
    parsed = _parse(text)
    split = op.split_bundle(running, parsed, text=text)
    held_parsed = {**{key: value for key, value in parsed.items() if key != "clarification"}, "actions": [action for action, *_ in split["held"]], "recognized_future_actions": [], "future_details": []}
    kept = pending.hold_incomplete_bundle(held_parsed, running)
    assert kept and pending.missing_fields(kept["parsed"]["actions"][kept["index"]]) == ["rate", "units"]
    for answer in ("mcg/min", "mcg/kg/min"):
        completed = pending.complete_bundle(kept, answer, running)["parsed"]["actions"][kept["index"]]
        assert completed["rate"] is None and "65" not in json.dumps(completed, default=str), (answer, completed)


# -- the real encounter ---------------------------------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("target", ["Titrate norepinephrine to MAP 65.", "Titrate norepinephrine to MAP >65.", "Wean norepinephrine to MAP 70.", "Continue norepinephrine to keep MAP above 65.",
                                    "Titula noradrenalina a PA 100.", "Titrate norepinephrine to a goal of 65.", "Titrate norepinephrine to HR 100.", "Increase norepinephrine to 12."])
def test_t10_through_the_real_encounter_a_target_is_never_executed_as_a_rate(target):
    """The defect reproduced and repaired end to end: with 10 mcg/min running, the engine rate stays 10, nothing is executed, the question is asked, and the mirror hands the shadow nothing for the turn."""
    encounter, entries, mirrored = _play(START10, "Reassess in 2 minutes.", target)
    held = entries[-1]
    assert held["executed"] is False and held["clarification"] and "without units" in str(held["clarification"]), held["clarification"]
    assert _rate(encounter) == 10.0 and encounter.state["treatments"]["norepinephrine_rate"] == 10.0 and encounter.state["treatments"]["norepinephrine_units"] == "mcg/min"
    assert [(item.kind, item.action.get("operation"), item.action.get("rate"), item.action.get("units")) for item in mirrored if item.kind in ("norepinephrine", "infusion_adjustment")] == [
        ("norepinephrine", "start", 10.0, "mcg/min")], "the mirror hands over only the start: the target is not an order"


def test_t11_the_held_target_leaves_the_encounter_and_the_shadow_exactly_as_if_it_had_not_been_written():
    with_target, _entries, mirrored_target = _play(START10, "Reassess in 2 minutes.", "Titrate norepinephrine to MAP 65.", "Reassess in 8 minutes.")
    plain, _entries, mirrored_plain = _play(START10, "Reassess in 2 minutes.", "Reassess in 8 minutes.")
    assert [(item.kind, item.minute) for item in mirrored_target if item.kind in ("norepinephrine", "infusion_adjustment")] == [(item.kind, item.minute) for item in mirrored_plain if item.kind in ("norepinephrine", "infusion_adjustment")]
    assert _rate(with_target) == _rate(plain) == 10.0


def test_t12_without_a_running_infusion_a_start_with_a_pressure_goal_executes_nothing():
    for text in ("Start norepinephrine for TAM 65.", "Titrate norepinephrine to MAP 65.", "Start norepinephrine to a goal of 65."):
        encounter, entries, mirrored = _play(text)
        assert entries[0]["executed"] is False and _rate(encounter) == 0.0 and not [item for item in mirrored if item.kind in ("norepinephrine", "infusion_adjustment")], text


def test_t13_a_later_stop_after_a_held_unit_less_order_is_followed_by_the_shadow():
    """Before the repair the unit-less order reached the mirror, the shadow refused it and closed its infusion, and the later stop was ignored (TD-158). Held before the engine, it never reaches the mirror: the stop is followed."""
    encounter, entries, mirrored = _play(START10 + " Reassess in 3 minutes.", "Increase norepinephrine to 12. Reassess in 3 minutes.", "Stop norepinephrine. Reassess in 3 minutes.")
    assert [row["outcome"] for row in ts.order_log(mirrored, tta._witness())] == [ts.STARTED, ts.STOPPED] and _rate(encounter) == 0.0


def test_t14_the_pressure_target_scenario_of_the_review_runs_exactly_as_the_start_alone():
    """The harness script of the review (R5): the shadow run is the run of the start alone and equals the engine."""
    probe = tta.real_text_probe("R5_PRESSURE_TARGET")
    assert probe["observed"]["engine_rate_at_the_end"] == probe["observed"]["run_rate_at_the_end"] == 10.0 and probe["observed"]["outcomes"] == [ts.STARTED] and probe["gaps"] == []


# -- the manual rate control the faculty accepted (FD-NR-01) is untouched --------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("script, outcomes, final", [
    ((START5, "Increase norepinephrine to 10 mcg/min."), [ts.STARTED, ts.INCREASED], 10.0),
    ((START10, "Decrease norepinephrine to 4 mcg/min."), [ts.STARTED, ts.DECREASED], 4.0),
    ((START10, "Stop norepinephrine."), [ts.STARTED, ts.STOPPED], 0.0),
    ((START5, "Increase norepinephrine to 10 mcg/min.", "Decrease norepinephrine to 4 mcg/min.", "Stop norepinephrine."), [ts.STARTED, ts.INCREASED, ts.DECREASED, ts.STOPPED], 0.0),
    ((START10, "Stop norepinephrine.", START10), [ts.STARTED, ts.STOPPED, ts.RESTARTED], 10.0)])
def test_t15_start_increase_decrease_stop_and_restart_by_explicit_rate_still_run_and_are_mirrored_as_before(script, outcomes, final):
    encounter, entries, mirrored = _play(*(f"{text} Reassess in 3 minutes." for text in script))
    assert all(entry["executed"] for entry in entries), [entry["clarification"] for entry in entries]
    assert [row["outcome"] for row in ts.order_log(mirrored, tta._witness())] == outcomes
    assert _rate(encounter) == final


def test_t16_the_belt_and_braces_of_the_shadow_still_refuses_a_hand_made_unit_less_order():
    rate, why = ts.order_disposition({"type": "norepinephrine", "operation": "adjust", "rate": 65.0, "units": None}, {"type": "norepinephrine", "operation": "adjust", "rate": 65.0, "units": "mcg/min"})
    assert rate is None and why == ts.GAP_NO_UNITS.format(operation="adjust")


def test_t17_the_restart_verb_and_the_relative_command_are_characterized_not_changed():
    """The verb 'restart' is not read by the frozen reader (held, nothing dosed: the supported restart is the explicit start after a stop, TIT-5). A relative command with no number is not given one."""
    held = fp.parse_family_actions("restart norepinephrine at 10 mcg/min")["actions"]
    assert len(held) == 1 and held[0]["type"] == "clarification" and "not recognized" in held[0]["message"]
    for text in ("increase norepinephrine", "titrate norepinephrine to effect"):
        action = fp.parse_family_actions(text)["actions"][0]
        assert action["type"] == "norepinephrine" and action["rate"] is None and action["units"] is None and op.unitless_infusion_rate(action) is None


def test_t18_known_residual_nitroglycerin_is_not_covered_by_the_unit_rule():
    """KNOWN RESIDUAL, declared (TD-160). Nitroglycerin carries its only unit in the field name (``rate_mcg_min``), so the pipeline cannot tell a bare number from an explicit rate: ``titrate nitroglycerin to SBP 120``
    is still read by the frozen reader as 120 mcg/min. It is outside this assignment (norepinephrine) and its repair is in the frozen reader. This test records it; it must change when the reader is repaired."""
    action = fp.parse_family_actions("titrate nitroglycerin to SBP 120")["actions"][0]
    assert action == {"type": "nitroglycerin", "operation": "adjust", "rate_mcg_min": 120.0} and op.unitless_infusion_rate(action) is None


def test_t19_the_spanish_message_is_there_and_says_the_same_thing():
    for name, spanish_name in (("Norepinephrine", "Noradrenalina"), ("Dobutamine", "Dobutamina"), ("The infusion", "La infusión")):
        english = op.UNITS_REQUIRED.format(name=name)
        spanish = language.say(english, "es")
        assert english != spanish and spanish.startswith(f"{spanish_name} se escribió con una velocidad pero sin unidades") and "objetivo de presión como PAM 65" in spanish, spanish
        assert "no se convirtió ni se ejecutó nada" in spanish and spanish.endswith("o di cancelar.")


def test_t20_the_legacy_ps001_path_of_the_page_never_read_a_pressure_as_a_rate():
    """The other text path of the page (app.py, the fixed PS001 case) reads a rate only WITH its units, so ``MAP 65`` was never a rate there. It is part of the trace of the order and is kept as a record of it."""
    import ast
    import re
    from pathlib import Path
    tree = ast.parse((Path(__file__).resolve().parent / "app.py").read_text(encoding="utf-8"))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "parse_agent_mcg_rate"]
    assert len(nodes) == 1
    namespace = {"re": re}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "subset", "exec"), namespace)
    read = namespace["parse_agent_mcg_rate"]
    aliases = ["norepinephrine", "noradrenaline", "levophed", "norepi", "levo"]
    assert read("titrate norepinephrine to MAP 65", aliases) == (None, None) and read("titrate norepinephrine to MAP >65", aliases) == (None, None)
    assert read("increase norepinephrine to 10 mcg/min", aliases) == (10.0, "mcg/min") and read("norepinephrine 0.1 mcg/kg/min", aliases) == (0.1, "mcg/kg/min")


def test_t21_the_repair_touches_no_frozen_file_no_physiology_and_no_authority():
    from clinical_core import amendment_3 as a3
    import runtime_authority as ra
    assert reader_freeze.test_prephase1_reader_freeze_is_exact() is None, "the five reader files are the ones the freeze accepted"
    assert a3.amended_core_digest_now() == "867bac09e09bb5c04629e73fbbdec0f7e1f100da17ef8966f580ba91067a7c9c"
    assert ts.MAPPED_UNITS == "mcg/min" and ts.MAPPED_OPERATIONS == ("start", "adjust", "continue", "stop")
    assert getattr(ra, "COMMON_CORE_RUNTIME_AUTHORITY", False) is False
