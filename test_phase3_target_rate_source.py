"""P3-464 to P3-468: the SOURCE repair of the order reader -- a physiologic TARGET is never a DRUG RATE (faculty decisions FD-TARGET-01 to FD-TARGET-11, 2026-11-20).

The reader (``family_parser``) used to turn the only number of an infusion clause into its rate: ``titrate norepinephrine to MAP 65`` was ``rate 65, units None`` and ``titrate nitroglycerin to SBP 120`` was
``rate_mcg_min 120`` (the unit of nitroglycerin is in the NAME of its field). Now:

* a rate is read ONLY when it is written with its unit (``10 mcg/min``, ``0.1 mcg/kg/min``, ``20 mcg per minute``);
* a number with no rate unit (a target, a pressure, a typo), and a relative change with no rate at all, is INCOMPLETE: a clarification that carries ``incomplete_explicit_rate`` and NO number, never completed from the
  running infusion and never a silent no-op;
* ``restart``/``resume`` (and the Spanish forms) of the four infusions is a START: with an explicit rate it runs, without one it asks; the previous rate is never reused.

The tests read the live reader against the historical one (the reader of the Phase-2 closure, rebuilt by ``reader_succession``), the real encounter, and a differential corpus that shows nothing else changed.
"""
import itertools

import pytest

import family_parser as fp
import language
import order_pipeline as op
import pilot_acceptance as acceptance
import reader_succession as succession
import test_phase3_target_order_boundary as boundary
import test_tone_pathway_analysis as ta

NUMBER_KEYS = ("rate", "rate_value", "rate_mcg_min")
MESSAGE = fp.INCOMPLETE_EXPLICIT_RATE
INFUSIONS = ("norepinephrine", "epinephrine", "dobutamine", "nitroglycerin")


def _actions(reader, text):
    return reader.parse_family_actions(text)["actions"]


def _live(text):
    return _actions(fp, text)


def _old(text):
    return _actions(succession.historical_reader_module(), text)


def _has_a_number(actions):
    return [a for a in actions if any(a.get(key) is not None for key in NUMBER_KEYS)]


def _is_incomplete(action, agent, operation=None, reason=None):
    marker = action.get("incomplete_explicit_rate") or {}
    return (action["type"] == "clarification" and action["message"] == MESSAGE and marker.get("agent") == agent
            and (operation is None or marker.get("operation") == operation) and (reason is None or marker.get("reason") == reason) and not _has_a_number([action]))


# -- P3-464: norepinephrine ---------------------------------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("text", ["titrate norepinephrine to MAP 65", "titrate norepinephrine to MAP >65", "titrate norepinephrine to MAP > 65 mmHg", "Titrate norepinephrine to MAP of at least 65",
                                  "titrate norepinephrine to a goal of 65", "titrate norepinephrine to keep SBP above 90", "titrate norepinephrine to pressure goal 65", "titrate norepinephrine to SBP >100",
                                  "start norepinephrine for MAP 65", "titula noradrenalina a PAM 65", "titula noradrenalina a PAS >100", "ajusta noradrenalina para meta de 65",
                                  "wean norepinephrine to MAP 70", "Titrate norepinephrine to TAM 65", "titrate noradrenaline to MAP 65"])
def test_s1_a_target_beside_norepinephrine_is_never_a_rate(text):
    actions = _live(text)
    assert len(actions) == 1 and _is_incomplete(actions[0], "norepinephrine", reason="NUMBER_WITHOUT_RATE_UNITS"), (text, actions)
    old = _old(text)
    assert old and old[0].get("rate") is not None and not old[0].get("units"), "the historical reader gave the number as a rate with no units: the defect this repairs"


@pytest.mark.parametrize("text", ["maintain MAP 65", "target MAP 65 with norepinephrine", "keep the MAP above 65", "MAP goal 65 on norepinephrine", "norepinephrine, MAP goal 65"])
def test_s1b_a_target_statement_that_is_not_an_order_carries_no_rate_at_all(text):
    """The statements the reader never read as an order stay that way: no action carries a rate."""
    assert not _has_a_number(_live(text)), text


# -- P3-465/466: nitroglycerin, epinephrine, dobutamine -----------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("drug, kind", [("nitroglycerin", "nitroglycerin"), ("nitroglicerina", "nitroglycerin"), ("nitro", "nitroglycerin"), ("epinephrine", "epinephrine"), ("epinefrina", "epinephrine"),
                                        ("adrenaline", "epinephrine"), ("dobutamine", "dobutamine"), ("dobutamina", "dobutamine")])
@pytest.mark.parametrize("tail", ["to SBP 120", "to keep SBP <140", "to MAP 65", "for PAS 120", "to a goal of 120", "para PAM 65", "SBP 120"])
def test_s2_a_target_beside_any_modelled_vasoactive_infusion_is_never_a_rate(drug, kind, tail):
    for verb in ("titrate", "start", "increase", "titula"):
        text = f"{verb} {drug} {tail}"
        live = _live(text)
        assert not _has_a_number(live), (text, live)
        assert len(live) == 1 and _is_incomplete(live[0], kind), (text, live)


@pytest.mark.parametrize("text", ["titrate nitroglycerin to SBP 120", "nitroglycerin to keep SBP <140", "nitroglicerina para PAS 120", "nitroglycerin 20"])
def test_s2b_nitroglycerin_120_is_not_120_mcg_per_min(text):
    old = _old(text)
    assert old and old[0]["type"] == "nitroglycerin" and old[0]["rate_mcg_min"] in (120.0, 140.0, 20.0), "the historical reader: the field name hid the unit"
    live = _live(text)
    assert len(live) == 1 and live[0]["type"] == "clarification" and not _has_a_number(live), live


# -- FD-TARGET-05: explicit rates remain explicit -----------------------------------------------------------------------------------------------------------------------------
EXPLICIT = {
    "norepinephrine 10 mcg/min": {"type": "norepinephrine", "operation": "start", "rate": 10.0, "units": "mcg/min"},
    "increase norepinephrine to 12 mcg/min": {"type": "norepinephrine", "operation": "adjust", "rate": 12.0, "units": "mcg/min"},
    "decrease norepinephrine to 4 mcg/min": {"type": "norepinephrine", "operation": "adjust", "rate": 4.0, "units": "mcg/min"},
    "norepinephrine 20 mcg per minute": {"type": "norepinephrine", "operation": "start", "rate": 20.0, "units": "mcg/min"},
    "noradrenalina 8 mcg/min": {"type": "norepinephrine", "operation": "start", "rate": 8.0, "units": "mcg/min"},
    "norepinephrine 0.1 mcg/kg/min": {"type": "norepinephrine", "operation": "start", "rate": 0.1, "units": "mcg/kg/min"},
    "increase norepinephrine to 10 mcg/min to keep MAP above 65": {"type": "norepinephrine", "operation": "adjust", "rate": 10.0, "units": "mcg/min"},
    "Start norepinephrine at 10 mcg/min, MAP 58": {"type": "norepinephrine", "operation": "start", "rate": 10.0, "units": "mcg/min"},
    "epinephrine 5 mcg/min": {"type": "epinephrine", "operation": "start", "rate": 5.0, "units": "mcg/min"},
    "dobutamine 5 mcg/kg/min": {"type": "dobutamine", "operation": "start", "rate": 5.0, "units": "mcg/kg/min"},
    "nitroglycerin 20 mcg/min": {"type": "nitroglycerin", "operation": "start", "rate_mcg_min": 20.0},
    "increase nitroglycerin to 40 mcg/min": {"type": "nitroglycerin", "operation": "adjust", "rate_mcg_min": 40.0},
    "nitroglicerina 20 mcg/min": {"type": "nitroglycerin", "operation": "start", "rate_mcg_min": 20.0},
    "titrate nitroglycerin to 30 mcg/min to keep SBP 120": {"type": "nitroglycerin", "operation": "adjust", "rate_mcg_min": 30.0},
}


@pytest.mark.parametrize("text, expected", sorted(EXPLICIT.items()))
def test_s3_an_explicit_rate_with_its_units_is_read_exactly_as_before(text, expected):
    live, old = _live(text), _old(text)
    assert live == old and len(live) == 1 and {key: live[0].get(key) for key in expected} == expected, (text, live, old)


# -- P3-467: incomplete commands ----------------------------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("text, operation, reason", [("increase norepinephrine", "adjust", "NO_EXPLICIT_RATE"), ("decrease norepinephrine", "adjust", "NO_EXPLICIT_RATE"),
                                                      ("increase norepinephrine to 12", "adjust", "NUMBER_WITHOUT_RATE_UNITS"), ("wean norepinephrine off", "adjust", "NO_EXPLICIT_RATE"),
                                                      ("titrate norepinephrine to effect", "adjust", "NO_EXPLICIT_RATE"), ("aumenta la noradrenalina", "adjust", "NO_EXPLICIT_RATE"),
                                                      ("Bajar la noradrenalina.", "adjust", "NO_EXPLICIT_RATE"), ("start norepinephrine 10", "start", "NUMBER_WITHOUT_RATE_UNITS"),
                                                      ("decrease nitroglycerin", "adjust", "NO_EXPLICIT_RATE"), ("increase dobutamine", "adjust", "NO_EXPLICIT_RATE"), ("increase epinephrine to 3", "adjust", "NUMBER_WITHOUT_RATE_UNITS")])
def test_s4_an_incomplete_rate_command_is_an_incomplete_order_never_a_rate_and_never_a_no_op(text, operation, reason):
    live = _live(text)
    agent = ("nitroglycerin" if "nitro" in text else "dobutamine" if "dobutamine" in text else "norepinephrine" if ("norepinephrine" in text or "noradrenalina" in text)
             else "epinephrine" if "epinephrine" in text else "norepinephrine")
    assert len(live) == 1 and _is_incomplete(live[0], agent, operation, reason), (text, live)


@pytest.mark.parametrize("text", ["increase norepinephrine", "increase norepinephrine to 12", "decrease norepinephrine", "wean norepinephrine off", "Increase norepinephrine to 12 gamma"])
def test_s4b_in_the_real_encounter_an_incomplete_command_neither_executes_nor_changes_the_running_rate(text):
    encounter, entries, mirrored = boundary._play(boundary.START10, "Reassess in 2 minutes.", text)
    assert entries[-1]["executed"] is False and MESSAGE in str(entries[-1]["clarification"]), entries[-1]
    assert boundary._rate(encounter) == 10.0 and boundary._only_infusion_orders(mirrored) == [("norepinephrine", "start", 10.0, "mcg/min")], "no no-op, no new rate, nothing mirrored"


def test_s4c_the_incomplete_state_is_asked_in_both_languages_and_names_no_number():
    assert MESSAGE == op.INCOMPLETE_EXPLICIT_RATE
    assert language.say(MESSAGE, "es") == "La orden especifica un objetivo o una tasa incompleta. Indique una tasa explícita con sus unidades para continuar."
    assert not any(character.isdigit() for character in MESSAGE), "it cannot suggest that a detected number is a dose"


# -- P3-468: explicit restart -------------------------------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("text, kind, rate, units", [("restart norepinephrine at 10 mcg/min", "norepinephrine", 10.0, "mcg/min"), ("Restart norepinephrine at 10 mcg/min.", "norepinephrine", 10.0, "mcg/min"),
                                                      ("resume norepinephrine at 8 mcg/min", "norepinephrine", 8.0, "mcg/min"), ("re-start the norepinephrine at 6 mcg/min", "norepinephrine", 6.0, "mcg/min"),
                                                      ("reinicia la noradrenalina a 10 mcg/min", "norepinephrine", 10.0, "mcg/min"), ("reanuda noradrenalina 8 mcg/min", "norepinephrine", 8.0, "mcg/min"),
                                                      ("restart dobutamine at 5 mcg/kg/min", "dobutamine", 5.0, "mcg/kg/min"), ("restart epinephrine at 4 mcg/min", "epinephrine", 4.0, "mcg/min")])
def test_s5_an_explicit_restart_is_a_start_with_its_explicit_rate(text, kind, rate, units):
    live = _live(text)
    assert live == [{"type": kind, "rate": rate, "units": units, "operation": "start"}], (text, live)
    assert _actions(succession.historical_reader_module(), text)[0]["type"] == "clarification", "the historical reader did not read the verb"


def test_s5b_a_restart_of_nitroglycerin_with_an_explicit_rate_is_a_start_too():
    assert _live("restart nitroglycerin at 20 mcg/min") == [{"type": "nitroglycerin", "rate_mcg_min": 20.0, "operation": "start"}]


@pytest.mark.parametrize("text", ["restart norepinephrine", "resume norepinephrine", "reinicia la noradrenalina", "restart nitroglycerin"])
def test_s5c_a_restart_without_an_explicit_rate_is_incomplete_and_the_previous_rate_is_not_reused(text):
    live = _live(text)
    assert len(live) == 1 and live[0]["operation"] == "start" and not _has_a_number(live) and live[0]["type"] in INFUSIONS, (text, live)
    encounter, entries, mirrored = boundary._play(boundary.START10, "Reassess in 2 minutes.", "Stop norepinephrine.", text if "nitro" not in text else "restart norepinephrine")
    assert entries[-1]["executed"] is False and boundary._rate(encounter) == 0.0, "the engine asks for the rate: it does not restart at the previous 10 mcg/min"


def test_s5d_the_restart_verb_is_read_only_for_the_four_infusions():
    """No other family's wording changes: 'restart oxygen', 'resume the fluids' are exactly what the historical reader gave."""
    for text in ("restart oxygen at 4 L/min", "resume the normal saline", "restart the BiPAP", "restart antibiotics", "reinicia el oxigeno a 4 L/min"):
        assert _live(text) == _old(text), text


def test_s5e_restart_after_a_stop_through_the_real_encounter_by_its_explicit_rate():
    encounter, entries, _ = boundary._play(boundary.START10 + " Reassess in 3 minutes.", "Stop norepinephrine. Reassess in 3 minutes.", "Restart norepinephrine at 10 mcg/min. Reassess in 3 minutes.")
    assert all(entry["executed"] for entry in entries) and boundary._rate(encounter) == 10.0


# -- nothing else changed: a differential corpus -------------------------------------------------------------------------------------------------------------------------------
OTHER_ORDERS = (
    "Start oxygen 4 L/min nasal cannula", "Give 500 mL normal saline over 30 minutes", "Start BiPAP 12/6 FiO2 40%", "Intubate", "Give aspirin 300 mg PO", "Order a 12-lead ECG", "Order a chest X-ray",
    "Give ceftriaxone 2 g IV", "Give furosemide 40 mg IV", "Start nitroglycerin 600 mcg IV bolus", "Give nitroglycerin 400 mcg sublingual", "Give epinephrine 0.3 mg IM", "Give epinephrine 50 mcg IV push",
    "Give naloxone 0.4 mg IV", "Give dextrose 25 g IV", "Transfuse 2 units of packed red blood cells", "Reassess in 5 minutes", "Monitor continuous ECG", "Give albuterol nebulizer", "Give dexamethasone 10 mg IV",
    "Start heparin bolus", "Give amiodarone 150 mg IV", "Cardiovert at 100 J", "Start norepinephrine at 10 mcg/min and give 500 mL saline", "Stop the normal saline", "Check a lactate", "Send blood cultures",
    "Dar oxigeno 4 L/min por canula nasal", "Administrar 500 ml de suero fisiologico", "Iniciar BiPAP 12/6", "Intubar al paciente", "Dar aspirina 300 mg", "Pedir ECG", "Solicitar radiografia de torax",
    "Dar ceftriaxona 2 g ev", "Suspender la noradrenalina", "Continuar la noradrenalina", "Mantener la nitroglicerina", "Stop nitroglycerin", "Continue dobutamine", "Start dobutamine at 5 mcg/kg/min",
    "Start norepinephrine in 5 minutes", "start norepinephrine at 14:30", "Give 1 L lactated ringers", "Repeat the fluid bolus", "Increase oxygen to 6 L/min", "Decrease FiO2 to 40%", "Titrate oxygen to SpO2 94%",
    "Increase PEEP to 8", "Raise the FiO2 to 60%", "Lower the PEEP to 5", "Titrate the oxygen to keep sats above 92", "Wean oxygen", "Aumentar el oxigeno a 6 L/min", "Disminuir la FiO2 a 40%",
    "Increase the infusion to 20 mcg/min", "Increase the infusion", "Stop the infusion", "Titrate the drip to MAP 65", "Prepare for intubation", "Call cardiology", "Admit to the ICU")


@pytest.mark.parametrize("text", OTHER_ORDERS)
def test_s6_every_other_order_is_read_exactly_as_the_historical_reader_read_it(text):
    assert fp.parse_family_actions(text) == succession.historical_reader_module().parse_family_actions(text), text


def test_s6b_the_only_texts_that_differ_are_a_target_or_incomplete_rate_or_a_restart():
    """The corpus the other tests use for the infusions: a difference is allowed ONLY when the historical reader gave a number with no unit, an adjustment with no rate, or did not read the restart verb."""
    old_reader = succession.historical_reader_module()
    texts = list(boundary.TARGET_TEXTS) + list(EXPLICIT) + ["increase norepinephrine", "restart norepinephrine", "restart norepinephrine at 10 mcg/min", "wean norepinephrine off", "start norepinephrine", "stop norepinephrine",
                                                           "continue norepinephrine", "increase the infusion to 20 mcg/min"]
    for text in texts:
        live, old = fp.parse_family_actions(text), old_reader.parse_family_actions(text)
        if live == old:
            continue
        old_infusions = [a for a in old["actions"] if a.get("type") in INFUSIONS]
        legitimately = ([a for a in old_infusions if (a.get("rate") is not None and not a.get("units")) or (a.get("rate_mcg_min") is not None and not _explicit_unit_in(text))
                         or (a.get("operation") == "adjust" and a.get("rate") is None and a.get("rate_mcg_min") is None)]
                        or ("restart" in text.lower() and all(a["type"] == "clarification" for a in old["actions"])))
        assert legitimately, (text, old["actions"], live["actions"])


def _explicit_unit_in(text):
    import re
    return bool(re.search(r"\d\s*(?:mcg|ug|mg)\s*(?:/|\s+(?:per|por)\s+)", text))


# -- a generated corpus: no phrasing turns a number without a unit into a rate -----------------------------------------------------------------------------------------------
def test_s7_a_generated_corpus_never_turns_a_number_without_a_rate_unit_into_a_rate():
    verbs = ("titrate", "wean", "reduce", "increase", "decrease", "continue", "start", "adjust", "titula", "ajusta", "sube", "baja", "set", "switch", "change", "restart", "resume")
    drugs = ("norepinephrine", "noradrenalina", "dobutamine", "epinephrine", "nitroglycerin", "nitroglicerina", "nitro", "epinefrina", "norepi")
    words = ("MAP", "PAM", "TAM", "PA", "TAS", "TAD", "SBP", "PAS", "BP", "HR", "mean", "CPP", "goal of", "target", "meta de", "objetivo de", "mmHg", "CVP", "CI")
    checked = 0
    for verb, drug, word, number in itertools.product(verbs, drugs, words, (65, 100)):
        for text in (f"{verb} {drug} to {word} {number}", f"{verb} {drug} to {number} {word}"):
            for action in _live(text):
                assert action.get("operation") in (None, "continue", "stop") or not _has_a_number([action]) or (action.get("units") or action["type"] == "nitroglycerin" and False), (text, action)
                assert not _has_a_number([action]) or action.get("operation") == "continue" and action.get("rate") is None, (text, action)
            checked += 1
    assert checked == len(verbs) * len(drugs) * len(words) * 4


def test_s7b_a_number_beside_a_time_word_is_a_time_not_a_rate():
    for text in ("start norepinephrine 10 in 5 minutes", "start nitroglycerin in 10 minutes", "restart norepinephrine in 5 minutes"):
        live, old = _live(text), _old(text)
        assert not _has_a_number(live), (text, live)


# -- reasoning that precedes an incomplete order ------------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("text", ["My priority is perfusion, titrate norepinephrine to MAP 65", "My priority is perfusion, increase norepinephrine", "Mi prioridad es la perfusion, titula noradrenalina a PAM 65"])
def test_s4d_reasoning_followed_by_an_incomplete_order_asks_for_the_rate_instead_of_dropping_it_or_running_it(text):
    """It used to execute 65 mcg/min (the clause after the reasoning was an order with a rate of 65). Read as reasoning only it would vanish with a generic message; the resident is told what is missing."""
    encounter, entries, mirrored = boundary._play(boundary.START10, "Reassess in 2 minutes.", text)
    assert entries[-1]["executed"] is False and MESSAGE in str(entries[-1]["clarification"]), entries[-1]
    assert boundary._rate(encounter) == 10.0 and boundary._only_infusion_orders(mirrored) == [("norepinephrine", "start", 10.0, "mcg/min")]


def test_s4e_reasoning_followed_by_an_explicit_rate_still_executes():
    encounter, entries, _ = boundary._play(boundary.START10, "Reassess in 2 minutes.", "My priority is perfusion, increase norepinephrine to 12 mcg/min")
    assert entries[-1]["executed"] is True and boundary._rate(encounter) == 12.0


# -- P3-471: what the independent adversarial review found in THIS change (reproduced first, then repaired) -----------------------------------------------------------------
@pytest.mark.parametrize("text", ["My working model is septic shock, titrate norepinephrine to MAP 65", "My working model is septic shock, increase norepinephrine",
                                  "Mi modelo de trabajo es shock septico, titula noradrenalina a PAM 65", "My working model is cardiogenic shock, titrate nitroglycerin to SBP 120",
                                  "My working model is septic shock, start norepinephrine at 5 mcg/min"])
def test_s8_the_stored_working_model_never_swallows_an_incomplete_infusion_order(text):
    """Review finding F4. The reasoning extractor took the reader's question as 'not an order' and stored the order text as the working model (the old reader read it as an order, so it was left out)."""
    import app
    model = app.extract_explicit_reasoning(text)["problem_representation"]
    assert model in ("septic shock", "shock septico", "cardiogenic shock"), (text, model)


@pytest.mark.parametrize("drug, tail, then", [("norepinephrine", "to MAP 65", "then"), ("norepinephrine", "to 12", "then"), ("epinephrine", "to MAP 65", "then"), ("dobutamine", "to CI 2.5", "then"),
                                              ("nitroglycerin", "to SBP 120", "then"), ("noradrenalina", "a PAM 65", "luego")])
def test_s8b_an_order_written_after_an_incomplete_infusion_order_with_then_waits_with_it(drug, tail, then):
    """Review finding F5. The question had no span in the text, so 'then give 500 mL NS' ran while the order it followed was held (the same sequence rule holds it after any other held order)."""
    verb = "titula" if then == "luego" else "titrate"
    fluid = "da 500 mL de SF" if then == "luego" else "give 500 mL NS"
    encounter, entries, mirrored = boundary._play(boundary.START10, "Reassess in 2 minutes.", f"{verb} {drug} {tail} {then} {fluid}")
    last = entries[-1]
    assert last["executed"] is False and MESSAGE in str(last["clarification"]), last
    assert {(o["class"], o["fate"]) for o in last["orders"]} == {("clarification", "HELD_CLARIFICATION"), ("fluid", "HELD_CLARIFICATION")}, last["orders"]
    assert boundary._rate(encounter) == 10.0


@pytest.mark.parametrize("text", ["titrate norepinephrine to MAP 65", "increase norepinephrine", "increase norepi to 12", "titrate nitroglycerin to SBP 120", "increase epinephrine", "titrate dobutamine to CI 2.5",
                                  "aumentar noradrenalina", "titula noradrenalina a PAM 65", "nitroglycerin 120", "increase levophed", "titrate levophed to MAP 65", "increase epi to 4", "titrate nitro to SBP 120",
                                  "aumentar adrenalina", "titula dobutamina a IC 2.5", "disminuye la nitroglicerina", "wean norepi"])
def test_s8c_an_incomplete_infusion_order_is_recorded_once_and_as_held_not_as_not_understood(text):
    """Review finding F5 (record). The order was kept twice and both as UNRECOGNIZED ('Not understood ... write it again in other words'): the reader had understood it and asked for the rate."""
    _, entries, _ = boundary._play(boundary.START10, "Reassess in 2 minutes.", text)
    orders = entries[-1]["orders"]
    assert [(o["class"], o["fate"]) for o in orders] == [("clarification", "HELD_CLARIFICATION")], orders
    assert orders[0]["span"].lower().startswith(text.lower().split()[0]), orders[0]


@pytest.mark.parametrize("text", ["restart epinephrine 0.3 mg IM", "restart nitroglycerin 1000 mcg IV bolus", "restart epinephrine 1 mg IV push", "resume epinephrine 50 mcg IV push", "reinicia epinefrina 0.3 mg IM"])
def test_s8d_a_restart_of_a_one_shot_dose_is_not_read_as_a_start_of_that_dose(text):
    """Review finding F6. The restart verb is read only when the rest of the clause reads as an infusion; a bolus or an IM dose is left exactly as the historical reader left it (not read)."""
    assert _live(text) == _old(text), text
    encounter, entries, _ = boundary._play("Reassess in 1 minutes.", text)
    assert entries[-1]["executed"] is False


@pytest.mark.parametrize("text, expected", [("restart levophed at 10 mcg/min", 10.0), ("Restart Levophed at 4 mcg/min", 4.0), ("reinicia levophed a 6 mcg/min", 6.0), ("resume the levophed 8 mcg/min", 8.0)])
def test_s8e_restart_reads_every_name_the_vasoactive_block_reads(text, expected):
    """Review finding F7b. 'restart levophed' was not read ('start levophed' was) and, written beside another order, the restart vanished with no question and no entry."""
    live = _live(text)
    assert len(live) == 1 and live[0]["type"] == "norepinephrine" and live[0]["operation"] == "start" and live[0]["rate"] == expected, live
    encounter, entries, _ = boundary._play(boundary.START10 + " Reassess in 2 minutes.", "Stop norepinephrine. Reassess in 2 minutes.", text + ". Reassess in 2 minutes.")
    assert entries[-1]["executed"] is True and boundary._rate(encounter) == expected


def test_s8f_a_restart_written_beside_another_order_never_vanishes():
    _, entries, _ = boundary._play(boundary.START10 + " Reassess in 2 minutes.", "Stop norepinephrine. Reassess in 2 minutes.", "restart levophed, reassess in 5 minutes")
    last = entries[-1]
    assert last["executed"] is False and last["clarification"], last
    assert any(o["class"] == "norepinephrine" and o["fate"] == "HELD_CLARIFICATION" for o in last["orders"]), last["orders"]


@pytest.mark.parametrize("text, rate", [("My priority is perfusion, restart norepinephrine at 5 mcg/min", 5.0), ("Because MAP is 58, restart norepinephrine at 5 mcg/min", 5.0),
                                        ("Mi prioridad es la perfusion, reinicia noradrenalina a 5 mcg/min", 5.0)])
def test_s8g_a_restart_written_after_a_statement_of_reasoning_is_an_order_too(text, rate):
    """Review finding F7c. The restart verbs are not in the command list, so the order was dropped as reasoning (nothing ran, no question); the same text with 'start' executed."""
    encounter, entries, _ = boundary._play(boundary.START10 + " Reassess in 2 minutes.", "Stop norepinephrine. Reassess in 2 minutes.", text)
    assert entries[-1]["executed"] is True and boundary._rate(encounter) == rate, entries[-1]
    encounter, entries, _ = boundary._play(boundary.START10 + " Reassess in 2 minutes.", "Stop norepinephrine. Reassess in 2 minutes.", text.replace("restart norepinephrine at 5 mcg/min", "restart norepinephrine at 5").replace("reinicia noradrenalina a 5 mcg/min", "reinicia noradrenalina a 5"))
    assert entries[-1]["executed"] is False and boundary._rate(encounter) == 0.0, "no unit: asked, nothing runs"
