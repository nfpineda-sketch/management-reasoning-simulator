"""P3-424 to P3-434: the harness of the norepinephrine titration and stop DEVELOPMENT probes (a tool, never imported by a page; it holds no test).

WHAT IT DOES. It runs, through the REAL legacy encounter, its mirror and the development shadow mapping (``runtime_tone_support``), the order histories the faculty asked for -- start, start then
increase, start then decrease, start then stop, the four in a row, and a restart -- on the GI hemorrhage case whose common-tone pressure behaviour passed the human review, and it reads what the common core made
of them. It also runs the edge-case matrix (every case with its expected outcome WRITTEN BELOW BEFORE the matrix was ever executed), the same history in the other families, and it formalizes the
hypertensive pulmonary-edema order as a negative-control management scenario. It writes sealed, versioned records and changes nothing executable.

AFTER THE ADVERSARIAL REVIEW (P3-435). The independent review showed that the order shapes the first matrix used were not all shapes the real parser emits, and that three of the mapping's rules
were wrong. What changed here is said where it changed and is in the record: one expectation of the first matrix was REVISED (07: an order replaced within its minute is a declared gap, not a
carried order), cases and variants were ADDED (each with its expectation written before it was run through the repaired mapping), and a set of REAL-TEXT probes runs the order sentences the
review used -- an order that names no drug, a rate without units, a pressure target -- through the real encounter. Nothing was adjusted to pass: the original expectation of 07 is kept beside
its revision.

WHAT IT IS NOT. Not a calibration and not a request for an mmHg judgment: what is read is direction, timing, ordering, smoothness and persistence or decay. Only ``CENTER_REFERENCE`` is run (the reviewed
witness; FD-TITRATE-13: no LOW/HIGH sensitivity review). No constant of the tone pathway is changed, nothing is fitted, and a prediction that fails is REPORTED as failed, never adjusted to pass.
"""
from __future__ import annotations

import dataclasses
import functools
import json
import math
from copy import deepcopy
from pathlib import Path

import historical_records as hr
import test_tone_pathway_analysis as ta

ROOT = Path(__file__).resolve().parent
REV = ROOT / "docs" / "revision"
PROBES_PATH = REV / "PHASE3_NOREPINEPHRINE_TITRATION_PROBES.json"
NEGATIVE_CONTROL_PATH = REV / "NEGATIVE_CONTROL_HYPERTENSIVE_PULMONARY_EDEMA_NOREPI_V1.json"
CHECKPOINT_PATH = REV / "PHASE3_NOREPINEPHRINE_TITRATION_CHECKPOINT.json"
PROBES_ID = "NOREPINEPHRINE_TITRATION_PROBES_V1"
NEGATIVE_CONTROL_ID = "NEGATIVE_CONTROL_HYPERTENSIVE_PULMONARY_EDEMA_NOREPI_V1"
CHECKPOINT_ID = "NOREPINEPHRINE_TITRATION_CHECKPOINT_V1"
#: The faculty decided on 2026-11-18; the records were generated the day the package closed, after the adversarial review was repaired.
DECIDED_ON = "2026-11-18"
GENERATED_ON = "2026-11-19"
DECISIONS = "FD-TITRATE-01 to FD-TITRATE-13"
WITNESS = "CENTER_REFERENCE"
NOT_MAPPED = ta.NOT_MAPPED
STATEMENT = ("Synthetic development cases run in the shadow. Development probes of order semantics on an already ratified development snapshot: not a clinical validation, not a calibration, not a "
             "dose-response, not authority and not for residents. Norepinephrine stays outside the live authority.")

# -- the GI scripts: real order text through the real encounter ---------------------------------------------------------------------------------
START5, START10 = "Start norepinephrine at 5 mcg/min.", "Start norepinephrine at 10 mcg/min."
UP10, DOWN4, STOP = "Increase norepinephrine to 10 mcg/min.", "Decrease norepinephrine to 4 mcg/min.", "Stop norepinephrine."
#: Every script reads at the same minutes, so that two of them are compared minute by minute: the first order is at minute 2 (as in the certified FR-F run), the later ones at 10, 18 and 25.
READS = (2, 10, 18, 25, 32)
ORDER_MINUTES = READS[:-1]
_WAITS = (8, 8, 7, 7)


def _script(*orders: str) -> tuple:
    return ("Reassess in 2 minutes.",) + tuple(f"{order} Reassess in {wait} minutes.".strip() for order, wait in zip(orders, _WAITS))


GI_SCRIPTS = {
    "NO_ORDER": _script("", "", "", ""),
    "A_START": _script(START5, "", "", ""),
    "A10_START": _script(START10, "", "", ""),
    "B_START_INCREASE": _script(START5, UP10, "", ""),
    "C_START_DECREASE": _script(START10, DOWN4, "", ""),
    "D_START_STOP": _script(START10, STOP, "", ""),
    "E3_START_INCREASE_DECREASE": _script(START5, UP10, DOWN4, ""),
    "E_START_INCREASE_DECREASE_STOP": _script(START5, UP10, DOWN4, STOP),
    "F_START_STOP_RESTART": _script(START10, STOP, START10, ""),
}
#: P3-435: the order sentences of the adversarial review, through the real parser, engine and mirror. The first order is at minute 2 and the second at minute 10, as in the scripts above.
REAL_TEXT_SCRIPTS = {
    "R1_STOP_THE_INFUSION": _script(START10, "Stop the infusion.", "", ""),
    "R2_INCREASE_THE_INFUSION_RATE": _script(START10, "Increase the infusion rate to 20 mcg/min.", "", ""),
    "R3_INCREASE_WITHOUT_UNITS_THEN_STOP": _script(START10, "Increase norepinephrine to 12.", STOP, ""),
    "R4_CONTINUE_WITHOUT_A_RATE": _script(START10, "Continue norepinephrine.", "", ""),
    "R5_PRESSURE_TARGET": _script(START10, "Titrate norepinephrine to MAP 65.", "", ""),
    "R6_WEIGHT_BASED_START": _script("Start norepinephrine at 0.1 mcg/kg/min.", "", "", ""),
    "R7_STOP_THAT_CARRIES_A_RATE": _script(START10, "Stop norepinephrine 10 mcg/min.", "", ""),
    "R8_TWO_ORDERS_IN_ONE_TURN": _script("Start norepinephrine at 5 mcg/min. Increase norepinephrine to 10 mcg/min.", "", "", ""),
}
#: WRITTEN AFTER the review showed how the mirror hands these orders over, and BEFORE they were run through the repaired mapping. ``engine_rate_at_the_end`` is what the legacy engine runs
#: (its own state) and ``run_rate_at_the_end`` what the shadow run carries: where the two differ the run must SAY it no longer mirrors the vasopressor.
REAL_TEXT_EXPECTED = {
    "R1_STOP_THE_INFUSION": {"kinds": ["norepinephrine", "infusion_adjustment"], "outcomes": ["STARTED", "REFUSED_FAIL_CLOSED"], "writer": "norepinephrine", "states_equal_to": "A10_START",
                             "engine_rate_at_the_end": 0.0, "run_rate_at_the_end": 10.0, "says_it_no_longer_mirrors": True},
    "R2_INCREASE_THE_INFUSION_RATE": {"kinds": ["norepinephrine", "infusion_adjustment"], "outcomes": ["STARTED", "REFUSED_FAIL_CLOSED"], "writer": "norepinephrine", "states_equal_to": "A10_START",
                                      "engine_rate_at_the_end": 20.0, "run_rate_at_the_end": 10.0, "says_it_no_longer_mirrors": True},
    "R3_INCREASE_WITHOUT_UNITS_THEN_STOP": {"kinds": ["norepinephrine"] * 3, "outcomes": ["STARTED", "REFUSED_FAIL_CLOSED", "REFUSED_FAIL_CLOSED"], "writer": "norepinephrine",
                                            "states_equal_to": "A10_START", "engine_rate_at_the_end": 0.0, "run_rate_at_the_end": 10.0, "says_it_no_longer_mirrors": True},
    "R4_CONTINUE_WITHOUT_A_RATE": {"kinds": ["norepinephrine"] * 2, "outcomes": ["STARTED", "IDEMPOTENT_NO_CHANGE"], "writer": "norepinephrine_rate_history", "states_equal_to": "A10_START",
                                   "engine_rate_at_the_end": 10.0, "run_rate_at_the_end": 10.0, "says_it_no_longer_mirrors": False},
    "R5_PRESSURE_TARGET": {"kinds": ["norepinephrine"] * 2, "outcomes": ["STARTED", "REFUSED_FAIL_CLOSED"], "writer": "norepinephrine", "states_equal_to": "A10_START",
                           "engine_rate_at_the_end": 65.0, "run_rate_at_the_end": 10.0, "says_it_no_longer_mirrors": True},
    "R6_WEIGHT_BASED_START": {"kinds": ["norepinephrine"], "outcomes": ["REFUSED_FAIL_CLOSED"], "writer": None, "states_equal_to": "NO_ORDER", "engine_rate_at_the_end": 11.1,
                              "run_rate_at_the_end": 0.0, "says_it_no_longer_mirrors": False},
    "R7_STOP_THAT_CARRIES_A_RATE": {"kinds": ["norepinephrine"] * 2, "outcomes": ["STARTED", "STOPPED"], "writer": "norepinephrine_rate_history", "states_equal_to": "D_START_STOP",
                                    "engine_rate_at_the_end": 0.0, "run_rate_at_the_end": 0.0, "says_it_no_longer_mirrors": False},
    "R8_TWO_ORDERS_IN_ONE_TURN": {"kinds": ["norepinephrine"] * 2, "outcomes": ["REPLACED_WITHIN_ITS_MINUTE", "STARTED"], "writer": "norepinephrine", "states_equal_to": "A10_START",
                                  "engine_rate_at_the_end": 10.0, "run_rate_at_the_end": 10.0, "says_it_no_longer_mirrors": False},
}
#: The rate each script's infusion runs at, as ((minute, mcg/min), ...): what the orders say, written here by hand.
GI_HISTORIES = {
    "NO_ORDER": (), "A_START": ((2, 5.0),), "A10_START": ((2, 10.0),), "B_START_INCREASE": ((2, 5.0), (10, 10.0)), "C_START_DECREASE": ((2, 10.0), (10, 4.0)),
    "D_START_STOP": ((2, 10.0), (10, 0.0)), "E3_START_INCREASE_DECREASE": ((2, 5.0), (10, 10.0), (18, 4.0)),
    "E_START_INCREASE_DECREASE_STOP": ((2, 5.0), (10, 10.0), (18, 4.0), (25, 0.0)), "F_START_STOP_RESTART": ((2, 10.0), (10, 0.0), (18, 10.0)),
}
#: The probes the faculty named (P3-432), with the script each is, and the one extra the operations list asks for (0 -> 10 -> 0 -> 10).
NAMED_PROBES = {"A": "A_START", "B": "B_START_INCREASE", "C": "C_START_DECREASE", "D": "D_START_STOP", "E": "E_START_INCREASE_DECREASE_STOP", "RESTART": "F_START_STOP_RESTART"}
#: (the run with one more order, the same run without it, the minute of that order, what the order is): each pair differs by ONE order.
GI_PAIRS = (("B_START_INCREASE", "A_START", 10, "INCREASE"), ("C_START_DECREASE", "A10_START", 10, "DECREASE"), ("D_START_STOP", "A10_START", 10, "STOP"),
            ("E3_START_INCREASE_DECREASE", "B_START_INCREASE", 18, "DECREASE"), ("E_START_INCREASE_DECREASE_STOP", "E3_START_INCREASE_DECREASE", 25, "STOP"),
            ("F_START_STOP_RESTART", "D_START_STOP", 18, "RESTART"))
#: WRITTEN BEFORE THE RUNS. What each check expects of the GI probes; a check that fails is reported as failed.
GI_PREDICTIONS = {
    "TIMING": ("an order at minute s changes nothing at or before s: the support is the same as in the run without that order through minute s and first differs at s + 1; the tone and the pressure are the "
               "same through s + 1 and first differ at s + 2 (the tone moves one minute behind the state that calls for it)"),
    "DIRECTION": ("after an INCREASE or a RESTART the support, the tone and the pressure are never below the run without that order, and above it somewhere; after a DECREASE or a STOP they are never "
                  "above it, and below it somewhere"),
    "ORDERING": ("in probe E the support at the end of each plateau orders as the rates do: 10 mcg/min above 5 above 4 above the stopped infusion, which is at or above 0; the pressure relative to the "
                 "run without any mapped order orders the same way"),
    "SMOOTHNESS": ("the support never moves in the minute of an order, and in no minute by more than its own first-order step (the distance to the ordered rate's steady support times 1 - exp(-1/tau), "
                   "tau the onset constant while it rises and the offset constant while it falls); the largest one-minute change of the tone against the run without any mapped order is, in every probe, "
                   "at most the largest one in the plain start at 10 mcg/min"),
    "PERSISTENCE_AND_DECAY": ("with an unchanged rate the support approaches that rate's steady support and never passes it (and, added after the review, it is within 1e-7 of an independent "
                              "numerical integration of the first-order equation); after a STOP it is NOT erased in the minute of the stop, it decays by the "
                              "offset constant alone (the core's own closed form, bit for bit), it is never negative, less than 1 % of what it was at the stop is left 12 minutes later, and at least "
                              "90 % of the pressure effect the infusion had at the stop is gone 22 minutes after it (probe D)"),
    "UNTOUCHED_STATE": "the volume, the pump, the hemoglobin and the lung water are the same, minute by minute, as in the run without any mapped order: the orders change the tone and nothing else",
    "HISTORICAL": ("the plain start at 10 mcg/min builds the core's own writer (type norepinephrine), exactly as before this package; the run in which the order is not mapped is the same, state by "
                   "state, whatever the orders were"),
}

# -- the edge cases: the expected outcome of each, WRITTEN BEFORE the matrix was executed ---------------------------------------------------------
EDGE_FAMILY, EDGE_MINUTES = "gi_bleed", 32
EDGE_EXPECTED = {
    "01_START_FROM_ZERO": {"outcomes": ["STARTED"], "writer": "norepinephrine", "writers": 1, "gaps": 0, "support_is_zero_through_the_order_minute": True, "first_minute_with_support": 6,
                           "replays_exactly": True},
    "02_INCREASE": {"outcomes": ["STARTED", "INCREASED"], "writer": "norepinephrine_rate_history", "writers": 1, "gaps": 0, "same_as_without_the_order_through_its_minute": True,
                    "support_after_the_order": "NEVER_FALLS", "never_past_the_ordered_steady_support": True, "replays_exactly": True},
    "03_DECREASE": {"outcomes": ["STARTED", "DECREASED"], "writer": "norepinephrine_rate_history", "writers": 1, "gaps": 0, "same_as_without_the_order_through_its_minute": True,
                    "support_after_the_order": "NEVER_RISES", "never_past_the_ordered_steady_support": True, "replays_exactly": True},
    "04_STOP": {"outcomes": ["STARTED", "STOPPED"], "writer": "norepinephrine_rate_history", "writers": 1, "gaps": 0, "support_at_the_stop_minute_is_not_erased": True,
                "bit_identical_to_the_cores_own_stopped_writer": True, "support_returns_to_exactly_zero": True, "never_negative": True, "replays_exactly": True},
    "05_RESTART_AFTER_STOP": {"outcomes": ["STARTED", "STOPPED", "RESTARTED"], "writer": "norepinephrine_rate_history", "writers": 1, "gaps": 0, "support_after_the_order": "NEVER_FALLS",
                              "never_past_the_ordered_steady_support": True, "replays_exactly": True},
    "06_DUPLICATE_IDENTICAL_RATE": {"outcomes": ["STARTED", "IDEMPOTENT_NO_CHANGE", "IDEMPOTENT_NO_CHANGE"], "writer": "norepinephrine_rate_history", "writers": 1, "gaps": 0,
                                    "states_equal_to": "THE_SINGLE_START", "replays_exactly": True},
    "07_TWO_ORDERS_IN_ONE_MINUTE": {"outcomes": ["REPLACED_WITHIN_ITS_MINUTE", "STARTED"], "replaced_within_its_minute": [True, False], "writer": "norepinephrine", "writers": 1, "gaps": 1,
                                    "states_equal_to": "A_SINGLE_START_AT_THE_LAST_RATE", "replays_exactly": True},
    "08_INVALID_UNIT": {"outcomes": ["STARTED", "REFUSED_FAIL_CLOSED", "REFUSED_FAIL_CLOSED"], "writer": "norepinephrine", "writers": 1, "gaps": 2, "states_equal_to": "THE_SINGLE_START",
                        "says_it_no_longer_mirrors": True},
    "09_NEGATIVE_DOSE": {"outcomes": ["STARTED", "REFUSED_FAIL_CLOSED"], "writer": "norepinephrine", "writers": 1, "gaps": 1, "states_equal_to": "THE_SINGLE_START", "says_it_no_longer_mirrors": True},
    "10_STOP_WITHOUT_PRIOR_START": {"outcomes": ["REFUSED_FAIL_CLOSED", "REFUSED_FAIL_CLOSED"], "writer": None, "writers": 0, "gaps": 2, "states_equal_to": "NO_ORDER"},
    "11A_WEIGHT_BASED_FIRST_ORDER": {"outcomes": ["REFUSED_FAIL_CLOSED", "REFUSED_FAIL_CLOSED"], "writer": None, "writers": 0, "gaps": 2, "states_equal_to": "NO_ORDER", "never_converted": True},
    "11B_WEIGHT_BASED_RATE_CHANGE": {"outcomes": ["STARTED", "REFUSED_FAIL_CLOSED"], "writer": "norepinephrine", "writers": 1, "gaps": 1, "states_equal_to": "THE_SINGLE_START",
                                     "never_converted": True, "says_it_no_longer_mirrors": True},
    "12_MALFORMED_ORDER": {"each_variant": {"outcomes": ["STARTED", "REFUSED_FAIL_CLOSED"], "writer": "norepinephrine", "writers": 1, "gaps": 1, "states_equal_to": "THE_SINGLE_START"},
                           "variants": ["A_PRESSURE_TARGET", "NO_OPERATION", "NO_ACTION", "A_RATE_IN_WORDS", "A_RATE_THAT_IS_NOT_A_NUMBER", "AN_INFINITE_RATE", "A_ZERO_RATE_THAT_IS_NOT_A_STOP",
                                        "A_PRESSURE_TARGET_AS_THE_PARSER_HANDS_IT_OVER", "A_RATE_WITHOUT_UNITS", "A_RATE_TOO_LARGE_TO_BE_A_NUMBER", "AN_ACTION_THAT_IS_NOT_AN_ORDER",
                                        "A_RECEIPT_THAT_SAYS_ANOTHER_RATE"]},
    "13_NO_PULSE_STATE": {"the_run_completes": True, "support_is_the_writers_closed_form_with_or_without_a_pulse": True, "no_pressure_is_reported_without_a_pulse": True,
                          "the_orders_given_without_a_pulse_are_accounted": ["STARTED", "INCREASED", "STOPPED"]},
    "14_SESSION_RESTART_AND_REPLAY": {"the_artifact_survives_json_and_replays_exactly": True, "the_artifact_names_the_rate_history_the_units_and_the_writer_version": True,
                                      "a_run_rebuilt_from_the_same_orders_is_the_same": True, "any_division_into_turns_gives_the_same_states": True,
                                      "orders_mirrored_as_they_are_given_give_the_same_states": True, "orders_mirrored_as_they_are_given_declare_the_same_gaps": True},
    "15A_ORDER_WITHOUT_A_WHOLE_MINUTE": {"outcomes": ["REFUSED_FAIL_CLOSED", "REFUSED_FAIL_CLOSED"], "writer": None, "writers": 0, "gaps": 2, "states_equal_to": "NO_ORDER"},
    "15B_ORDER_DATED_BEFORE_A_RECORDED_MINUTE": {"the_runner_refuses_it": "HistoryRewritten", "nothing_is_recorded_after_the_refusal": True},
    "15C_ORDERS_AGAINST_THE_CLOCK": {"outcomes": ["REFUSED_FAIL_CLOSED", "REFUSED_FAIL_CLOSED"], "writer": None, "writers": 0, "gaps": 2, "states_equal_to": "NO_ORDER"},
    "16_ORDER_THAT_NAMES_NO_DRUG": {"outcomes": ["STARTED", "REFUSED_FAIL_CLOSED", "REFUSED_FAIL_CLOSED"], "writer": "norepinephrine", "writers": 1, "gaps": 1, "states_equal_to": "THE_SINGLE_START",
                                    "says_it_no_longer_mirrors": True, "the_order_that_names_no_drug_says_why": True, "left_alone_while_no_norepinephrine_runs": True},
    "17_REFUSED_ORDER_IN_THE_MINUTE_OF_A_VALID_ONE": {"outcomes": ["STARTED", "REPLACED_WITHIN_ITS_MINUTE", "REFUSED_FAIL_CLOSED", "REFUSED_FAIL_CLOSED"], "writer": "norepinephrine", "writers": 1,
                                                      "gaps": 3, "states_equal_to": "THE_SINGLE_START", "says_it_no_longer_mirrors": True},
    "18_ORDERS_OF_ONE_MINUTE_ARRIVING_TURN_BY_TURN": {"outcomes": ["REPLACED_WITHIN_ITS_MINUTE", "NOTHING_TO_BUILD", "STARTED"], "writer": "norepinephrine", "writers": 1, "gaps": 2,
                                                      "the_gaps_recorded_turn_by_turn_are_the_gaps_of_the_whole": True, "no_order_is_both_declared_and_built": True,
                                                      "states_equal_to": "A_SINGLE_START_AT_MINUTE_9"},
}
#: P3-435. What the adversarial review changed in this matrix, said in the record. The ORIGINAL expectation of a revised case is kept: it was what the first matrix was run against.
EDGE_REVISED_AFTER_THE_REVIEW = {
    "07_TWO_ORDERS_IN_ONE_MINUTE": {
        "expected_before_the_review": {"outcomes": ["STARTED", "INCREASED"], "replaced_within_its_minute": [True, False], "writer": "norepinephrine_rate_history", "writers": 1, "gaps": 0,
                                       "states_equal_to": "A_SINGLE_START_AT_THE_LAST_RATE", "replays_exactly": True},
        "why": ("the first rule carried both orders and reported the replaced one as BUILT with an effective minute it never had; the infusion now carries ONE order a minute and the replaced "
                "one is a declared gap. The states were and are those of a single start at the last rate.")}}
EDGE_ADDED_AFTER_THE_REVIEW = {
    "cases": ["15C_ORDERS_AGAINST_THE_CLOCK", "16_ORDER_THAT_NAMES_NO_DRUG", "17_REFUSED_ORDER_IN_THE_MINUTE_OF_A_VALID_ONE", "18_ORDERS_OF_ONE_MINUTE_ARRIVING_TURN_BY_TURN"],
    "variants_of_12": ["A_PRESSURE_TARGET_AS_THE_PARSER_HANDS_IT_OVER", "A_RATE_WITHOUT_UNITS", "A_RATE_TOO_LARGE_TO_BE_A_NUMBER", "AN_ACTION_THAT_IS_NOT_AN_ORDER", "A_RECEIPT_THAT_SAYS_ANOTHER_RATE"],
    "checks_of_14": ["orders_mirrored_as_they_are_given_declare_the_same_gaps"],
    "each_expectation_was_written_before_the_case_was_run_through_the_repaired_mapping": True}
#: What each case IS, for a reader of the record.
EDGE_DESCRIPTIONS = {
    "01_START_FROM_ZERO": "start 5 mcg/min at minute 5", "02_INCREASE": "start 5 at minute 5, adjust to 10 at minute 12", "03_DECREASE": "start 10 at minute 5, adjust to 4 at minute 12",
    "04_STOP": "start 10 at minute 5, stop at minute 12", "05_RESTART_AFTER_STOP": "start 10 at minute 5, stop at minute 12, start 10 at minute 16",
    "06_DUPLICATE_IDENTICAL_RATE": "start 10 at minute 5, continue at 10 at minute 9, adjust to 10 at minute 14",
    "07_TWO_ORDERS_IN_ONE_MINUTE": "start 5 and then adjust to 10, both at minute 5", "08_INVALID_UNIT": "start 10 at minute 5, adjust to 8 mg/h at minute 12, adjust to 6 mcg/min at minute 15",
    "09_NEGATIVE_DOSE": "start 10 at minute 5, adjust to -5 mcg/min at minute 12", "10_STOP_WITHOUT_PRIOR_START": "stop at minute 5, start 10 at minute 9",
    "11A_WEIGHT_BASED_FIRST_ORDER": "start 0.1 mcg/kg/min at minute 5, start 10 mcg/min at minute 9", "11B_WEIGHT_BASED_RATE_CHANGE": "start 10 mcg/min at minute 5, adjust to 0.2 mcg/kg/min at minute 12",
    "12_MALFORMED_ORDER": "start 10 at minute 5, then at minute 12 an order that is not one (a pressure target, no operation, no action, a rate in words, not a number, infinite, or zero without a stop)",
    "13_NO_PULSE_STATE": "the common core alone: start 10 at minute 5, asystole at minute 9, adjust to 20 at minute 12 and stop at minute 18 without a pulse",
    "14_SESSION_RESTART_AND_REPLAY": "start 5, adjust to 10, adjust to 4, stop: the artifact through JSON, a run rebuilt from the same orders, and another division into turns",
    "15A_ORDER_WITHOUT_A_WHOLE_MINUTE": "a start whose minute is 5.5, then a start at minute 9", "15B_ORDER_DATED_BEFORE_A_RECORDED_MINUTE": "a run recorded to minute 12 that is then handed a start dated minute 5",
    "15C_ORDERS_AGAINST_THE_CLOCK": "a start dated minute 9 handed over before a start dated minute 5",
    "16_ORDER_THAT_NAMES_NO_DRUG": "start 10 at minute 5, 'stop the infusion' (an infusion adjustment that names no drug) at minute 12, adjust to 6 at minute 15; and the same order while no norepinephrine runs",
    "17_REFUSED_ORDER_IN_THE_MINUTE_OF_A_VALID_ONE": "start 10 at minute 5; at minute 12 adjust to 20 and then adjust to 8 mg/h; stop at minute 15",
    "18_ORDERS_OF_ONE_MINUTE_ARRIVING_TURN_BY_TURN": "start 5 and then stop, both at minute 5 but handed over in two turns of that minute, then start 10 at minute 9",
}
#: The same order history in every family named by the faculty (P3-433): a start, an increase, a decrease and a stop.
FAMILY_SEQUENCE = ((5, "start", 5.0), (12, "adjust", 10.0), (19, "adjust", 4.0), (25, "stop", None))
FAMILY_CASES = {"gi_bleed": "hemorrhagic", "pulmonary_embolism": "obstructive", "acs": "pump_limited", "pulmonary_edema": "pump_limited_and_congested"}
PUMP_LIMITED = ("acs", "pulmonary_edema")


# -- small readers ----------------------------------------------------------------------------------------------------------------------------------
def _witness() -> dict:
    from clinical_core import vascular_support as vs
    return vs.witness(WITNESS)


def _constants() -> dict:
    point = _witness()
    return {name: point[name] for name in ("half_effect_rate_mcg_min", "onset_tau_min", "offset_tau_min")}


def event(minute, operation="start", rate=None, units="mcg/min", order_id=None, position=0):
    """One norepinephrine order as the engine's mirror hands it over (a development probe: no encounter ran it)."""
    import runtime_shadow as rs
    action = {"type": "norepinephrine", "operation": operation, "rate": rate, "units": units if operation != "stop" else None}
    return rs.MirroredAction(order_id or f"probe-m{minute}-{position}-norepinephrine", minute, "norepinephrine", action, {}, 0.21)


def role_event(minute, operation="stop", rate=None, units=None, order_id=None):
    """An order that names no drug, as the mirror hands it over: the parsed action, before the engine resolves it, and an empty receipt (receipts are paired by the parsed kind)."""
    import runtime_shadow as rs
    action = {"type": "infusion_adjustment", "operation": operation, "rate_value": rate, "rate_units": units}
    return rs.MirroredAction(order_id or f"probe-m{minute}-0-infusion_adjustment", minute, "infusion_adjustment", action, {}, 0.21)


def events_of(sequence) -> tuple:
    return tuple(event(minute, operation, rate) for minute, operation, rate in sequence)


def writers_of(run: dict) -> list:
    from clinical_core import vascular_support as vs
    return [item for item in run["runner"].contributors() if isinstance(item, vs.Norepinephrine)]


def support_series(run: dict) -> list:
    return [state.aux.vasoconstrictor_support or 0.0 for state in run["trajectory"].states]


def closed_form(history: tuple, minutes: int) -> list:
    """The support the writer's closed form gives for a rate history, minute by minute, computed HERE and independently of the writer: the same first-order approach, in plain arithmetic."""
    from clinical_core import vascular_support as vs
    point = _constants()
    half, onset, offset = point["half_effect_rate_mcg_min"], point["onset_tau_min"], point["offset_tau_min"]
    out = []
    for minute in range(minutes + 1):
        level, since, target = 0.0, None, 0.0
        for at, rate in history:
            if minute <= at:
                break
            if since is not None:
                elapsed = at - since
                level = level + (target - level) * -math.expm1(-elapsed / onset) if target > level else target + (level - target) * math.exp(-elapsed / offset) if target < level else level
            since, target = at, rate / half
        if since is None:
            out.append(0.0)
            continue
        elapsed = minute - since
        value = level + (target - level) * -math.expm1(-elapsed / onset) if target > level else target + (level - target) * math.exp(-elapsed / offset) if target < level else level
        out.append(vs.on_the_grid(value))
    return out


def integrated(history: tuple, minutes: int, steps_per_minute: int = 240) -> list:
    """The same support by NUMERICAL integration, not by the closed form: dx/dt = (target - x) / tau, tau the onset constant while x is below the target and the offset constant while it is
    above, by classical Runge-Kutta steps. It shares no arithmetic with the writer (no exponential is taken), so agreement is evidence about the rule and not about a transcription."""
    point = _constants()
    half, onset, offset = point["half_effect_rate_mcg_min"], point["onset_tau_min"], point["offset_tau_min"]
    rate_over = lambda minute: next((rate for at, rate in reversed(history) if at < minute), 0.0)

    def slope(x, target):
        return (target - x) / (onset if target > x else offset)

    x, out, h = 0.0, [0.0], 1.0 / steps_per_minute
    for minute in range(1, minutes + 1):
        target = rate_over(minute) / half
        for _ in range(steps_per_minute):
            k1 = slope(x, target)
            k2 = slope(x + 0.5 * h * k1, target)
            k3 = slope(x + 0.5 * h * k2, target)
            k4 = slope(x + h * k3, target)
            x += h * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0
        out.append(x)
    return out


def step_bound(history: tuple, minute: int) -> float:
    """The largest change the support may make over (minute - 1, minute]: its own first-order step toward the rate ordered for that interval."""
    from clinical_core import vascular_support as vs
    point = _constants()
    before = closed_form(history, minute)[minute - 1]
    rate = next((rate for at, rate in reversed(history) if at < minute), 0.0)
    target = rate / point["half_effect_rate_mcg_min"]
    tau = point["onset_tau_min"] if target > before else point["offset_tau_min"]
    return abs(target - before) * -math.expm1(-1.0 / tau) + 2.0 * vs.SUPPORT_QUANTUM


def _same_states(one: dict, other: dict, through: int | None = None) -> bool:
    a, b = tuple(one["runner"].digests()), tuple(other["runner"].digests())
    return a == b if through is None else a[:through] == b[:through]


def _readings(run: dict) -> list:
    return [{key: value for key, value in row.items() if key != "support"} for row in run["rows"]]


def _log(run: dict) -> list:
    import runtime_tone_support as ts
    return ts.order_log(run["runner"].mirrored, _witness())


def _digest(value) -> str:
    return hr.digest_of(value)


# -- P3-432: the GI probes through the real encounter ------------------------------------------------------------------------------------------------
@functools.lru_cache(maxsize=None)
def capture(name: str) -> dict:
    """One script through the REAL legacy encounter with the shadow mirror on: the arrival the shadow maps and the orders the engine executed, exactly as its mirror hands them over."""
    import pilot_acceptance as acceptance
    import runtime_shadow as rs
    import runtime_shadow_evidence as ev
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(ta.FRF_CASE)
        arrival = deepcopy(encounter.state)
        turns = []
        for text in {**GI_SCRIPTS, **REAL_TEXT_SCRIPTS}[name]:
            entry = encounter.order(text)
            turns.append({"text": text, "from_minute": int(entry["decision_time_min"]), "to_minute": int(entry["response_time_min"]), "executed": bool(entry["executed"])})
        runner = encounter.shadow.runner
        legacy_rate = float((encounter.state.get("family_state") or {}).get("norepinephrine") or 0.0)
        return {"arrival": arrival, "mirrored": tuple(runner.mirrored), "mapping_state": deepcopy(runner.mapping_state), "turns": turns, "legacy_active_rate_at_the_end": legacy_rate}


@functools.lru_cache(maxsize=None)
def gi_run(name: str, witness: str | None = WITNESS) -> dict:
    captured = capture(name)
    return ta.shadow_run(ta.FRF_FAMILY, ta.FRF_CASE, witness, captured["mirrored"], READS, base=ta.frf_base_adapter(), state=captured["arrival"],
                         mapping_state=captured["mapping_state"], scenario_id=f"{PROBES_ID}::{name}::{witness or NOT_MAPPED}")


def _first_difference(a: list, b: list):
    return next((index for index, (x, y) in enumerate(zip(a, b)) if x != y), None)


def _column(run: dict, name: str) -> list:
    """One reading of a run, minute by minute; a support that is not tracked yet (the arrival) reads as none, 0."""
    return [(row[name] or 0.0) if name == "support" else row[name] for row in run["rows"]]


def pair_facts(later: str, earlier: str, minute: int, what: str) -> dict:
    """What ONE more order did, read against the same run without it."""
    one, other = gi_run(later), gi_run(earlier)
    support, tone, pressure = (list(zip(_column(one, name), _column(other, name))) for name in ("support", "T", "pressure_rel"))
    sign = 1.0 if what in ("INCREASE", "RESTART") else -1.0
    after = range(minute + 2, len(one["rows"]))
    return {"order": what, "order_minute": minute, "with": later, "without": earlier,
            "support_first_differs_at": _first_difference(_column(one, "support"), _column(other, "support")),
            "tone_first_differs_at": _first_difference(_column(one, "T"), _column(other, "T")),
            "pressure_first_differs_at": _first_difference(_column(one, "pressure_rel"), _column(other, "pressure_rel")),
            "states_identical_through_the_order_minute": _same_states(one, other, through=minute),
            "never_on_the_wrong_side": all(sign * (a - b) >= 0.0 for series in (support, tone, pressure) for a, b in series),
            "on_the_right_side_somewhere": all(any(sign * (series[index][0] - series[index][1]) > 0.0 for index in after) for series in (support, tone, pressure)),
            "at_the_end": {"minute": READS[-1], "support_with": one["rows"][-1]["support"], "support_without": other["rows"][-1]["support"],
                           "displayed_with": ta.displayed(one["rows"][-1]), "displayed_without": ta.displayed(other["rows"][-1])}}


def tone_step(run: dict, reference: dict) -> float:
    """The largest one-minute change of the tone AGAINST the run without any mapped order: what the orders, and nothing else, did to the tone in one minute."""
    gap = [a - b for a, b in zip(_column(run, "T"), _column(reference, "T"))]
    return max(abs(after - before) for before, after in zip(gap, gap[1:]))


def gi_probe(name: str) -> dict:
    from clinical_core import vascular_support as vs
    run, reference, history = gi_run(name), gi_run(name, None), GI_HISTORIES[name]
    series, expected = support_series(run), closed_form(history, READS[-1])
    writers = writers_of(run)
    steps = [abs(series[minute] - series[minute - 1]) for minute in range(1, len(series))]
    ratio = [run["rows"][minute]["pressure_rel"] / reference["rows"][minute]["pressure_rel"] for minute in range(len(series))]
    return {"script": list(GI_SCRIPTS[name]), "turns": capture(name)["turns"], "rate_history_as_written": [list(item) for item in history],
            "legacy_engine_active_rate_at_the_end_mcg_min": capture(name)["legacy_active_rate_at_the_end"],
            "orders": _log(run), "writers": [type(item).type_name for item in writers], "writer_spec": writers[0].to_spec() if writers else None,
            "dispositions": [row["disposition"] for row in run["dispositions"] if row["kind"] == "norepinephrine"],
            "gaps": [gap for gap in run["gaps"] if gap.get("kind") == "norepinephrine"], "failures": run["failures"],
            "replays_exactly": bool(run["replay_equal"] and run["same_states_as_the_runner"]),
            "support_is_the_closed_form": series == expected, "support_never_negative": min(series) >= 0.0,
            "largest_difference_from_the_independent_numerical_integration": max(abs(a - b) for a, b in zip(series, integrated(history, READS[-1]))),
            "support_never_moves_in_the_minute_of_an_order": all(series[minute] == closed_form(tuple(item for item in history if item[0] < minute), minute)[minute] for minute, _rate in history),
            "every_step_within_its_first_order_bound": all(steps[minute - 1] <= step_bound(history, minute) for minute in range(1, len(series))),
            "largest_one_minute_change_of_the_tone_against_the_unmapped_run": ta._r(tone_step(run, reference)),
            "untouched_state": ta.untouched(reference["rows"], run["rows"]),
            "unmapped_run_is_the_no_order_run": _same_states(reference, gi_run("NO_ORDER", None)),
            "at_the_reads": [{"minute": minute, "support": ta._r(series[minute]), "ordered_rate_mcg_min": next((rate for at, rate in reversed(history) if at < minute), 0.0),
                              "T": run["rows"][minute]["T"], "displayed": ta.displayed(run["rows"][minute]), "displayed_without_any_mapped_order": ta.displayed(reference["rows"][minute]),
                              "pressure_against_the_unmapped_run": ta._r(ratio[minute], 6)} for minute in READS],
            "per_minute": [{"minute": row["minute"], "support": row["support"], "T": row["T"], "pressure_rel": row["pressure_rel"], **{key: value for key, value in ta.displayed(row).items() if key != "minute"}}
                           for row in run["rows"]],
            "quantum": vs.SUPPORT_QUANTUM}


def gi_checks(probes: dict, pairs: list) -> dict:
    """The predictions, each read from the runs. Nothing here is tuned: a check is True or it is reported False."""
    from clinical_core import vascular_support as vs
    e, d = probes["E_START_INCREASE_DECREASE_STOP"], probes["D_START_STOP"]
    reads = {row["minute"]: row for row in e["at_the_reads"]}
    stop_support = [row["support"] or 0.0 for row in d["per_minute"]]
    core = vs.Norepinephrine("core", 2, 10.0, stop_minute=10, **_constants())
    d_ratio = {row["minute"]: row["pressure_against_the_unmapped_run"] for row in d["at_the_reads"]}
    start_step = probes["A10_START"]["largest_one_minute_change_of_the_tone_against_the_unmapped_run"]
    return {
        "TIMING": all(pair["support_first_differs_at"] == pair["order_minute"] + 1 and pair["tone_first_differs_at"] == pair["order_minute"] + 2
                      and pair["pressure_first_differs_at"] == pair["order_minute"] + 2 and pair["states_identical_through_the_order_minute"] for pair in pairs),
        "DIRECTION": all(pair["never_on_the_wrong_side"] and pair["on_the_right_side_somewhere"] for pair in pairs),
        "ORDERING": (reads[18]["support"] > reads[10]["support"] > reads[25]["support"] > reads[32]["support"] >= 0.0
                     and reads[18]["pressure_against_the_unmapped_run"] > reads[10]["pressure_against_the_unmapped_run"] > reads[25]["pressure_against_the_unmapped_run"]
                     > reads[32]["pressure_against_the_unmapped_run"]),
        "SMOOTHNESS": (all(probe["support_never_moves_in_the_minute_of_an_order"] and probe["every_step_within_its_first_order_bound"] for probe in probes.values())
                       and all(probe["largest_one_minute_change_of_the_tone_against_the_unmapped_run"] <= start_step + 1e-12 for probe in probes.values())),
        "PERSISTENCE_AND_DECAY": (all(probe["support_is_the_closed_form"] and probe["support_never_negative"] and probe["largest_difference_from_the_independent_numerical_integration"] <= 1e-7
                                      for probe in probes.values())
                                  and stop_support[10] > 0.0 and stop_support[11] > 0.0 and stop_support[22] < 0.01 * stop_support[10]
                                  and support_series(gi_run("D_START_STOP")) == [core.support_at(minute) for minute in range(READS[-1] + 1)]
                                  and abs(d_ratio[32] - 1.0) <= 0.1 * abs(d_ratio[10] - 1.0)),
        "UNTOUCHED_STATE": all(all(probe["untouched_state"].values()) for probe in probes.values()),
        "HISTORICAL": probes["A10_START"]["writers"] == ["norepinephrine"] and probes["A_START"]["writers"] == ["norepinephrine"]
                      and all(probe["unmapped_run_is_the_no_order_run"] for probe in probes.values()),
    }


def gi_probes() -> dict:
    probes = {name: gi_probe(name) for name in GI_SCRIPTS}
    pairs = [pair_facts(*pair) for pair in GI_PAIRS]
    checks = gi_checks(probes, pairs)
    return {"case_id": ta.FRF_CASE, "family": ta.FRF_FAMILY, "witness": WITNESS, "reads": list(READS),
            "why_this_case": "its common-tone pressure behaviour passed the human review (FR-F, ACCEPT_WITH_LIMITATION); the base mapping is the ratified GI pressure snapshot",
            "named_probes": dict(NAMED_PROBES), "predictions_written_before_the_runs": dict(GI_PREDICTIONS), "checks": checks, "all_as_predicted": all(checks.values()),
            "pairs": pairs, "probes": probes, "the_legacy_engine_is_not_read": "its own vasopressor rule is a fixed bonus in mmHg; nothing here compares with it"}


# -- P3-435: the review's order sentences through the real encounter ---------------------------------------------------------------------------------
def _run_rate_at_the_end(run: dict) -> float:
    writers = writers_of(run)
    if not writers:
        return 0.0
    writer = writers[0]
    return float(writer.ordered_rate_over(READS[-1] + 1)) if hasattr(writer, "ordered_rate_over") else float(writer.rate_mcg_min if writer.stop_minute is None else 0.0)


def real_text_probe(name: str) -> dict:
    """One sentence of the review through the real parser, engine and mirror: how the mirror hands the order over, what the mapping makes of it, and whether the run still says what the engine runs."""
    captured, run = capture(name), gi_run(name)
    log = _log(run)
    ours = [item for item in captured["mirrored"] if item.kind in ("norepinephrine", "infusion_adjustment")]
    writers = writers_of(run)
    expected = REAL_TEXT_EXPECTED[name]
    observed = {"kinds": [row["kind"] for row in log], "outcomes": [row["outcome"] for row in log], "writer": type(writers[0]).type_name if writers else None,
                "states_equal_to": expected["states_equal_to"] if _same_states(run, gi_run(expected["states_equal_to"])) else "DIFFERENT_STATES",
                "engine_rate_at_the_end": round(captured["legacy_active_rate_at_the_end"], 6), "run_rate_at_the_end": _run_rate_at_the_end(run),
                "says_it_no_longer_mirrors": any("no longer mirrors the encounter's vasopressor" in str(gap.get("why")) for gap in run["gaps"])}
    return {"script": list(REAL_TEXT_SCRIPTS[name]), "turns": captured["turns"],
            "as_the_mirror_hands_it_over": [{"minute": item.minute, "kind": item.kind,
                                             "action": {key: item.action.get(key) for key in ("type", "operation", "rate", "units", "rate_value", "rate_units") if key in item.action},
                                             "receipt": {key: item.receipt.get(key) for key in ("type", "operation", "rate", "units") if key in item.receipt}} for item in ours],
            "orders": log, "gaps": [gap for gap in run["gaps"] if gap.get("kind") in ("norepinephrine", "infusion_adjustment")], "failures": run["failures"],
            "replays_exactly": bool(run["replay_equal"] and run["same_states_as_the_runner"]),
            "the_run_and_the_engine_run_the_same_rate": observed["engine_rate_at_the_end"] == observed["run_rate_at_the_end"],
            "expected_before_it_was_run_through_the_repaired_mapping": expected, "observed": observed,
            "as_expected": observed == expected and not run["failures"] and bool(run["replay_equal"])}


def real_text_probes() -> dict:
    probes = {name: real_text_probe(name) for name in REAL_TEXT_SCRIPTS}
    silent = [name for name, probe in probes.items() if not probe["the_run_and_the_engine_run_the_same_rate"] and not probe["observed"]["says_it_no_longer_mirrors"]
              and probe["observed"]["outcomes"] != ["REFUSED_FAIL_CLOSED"]]
    return {"case_id": ta.FRF_CASE, "witness": WITNESS, "why": "the adversarial review ran these sentences: the mirror hands an order over as it was WRITTEN, before the engine resolves or completes it",
            "probes": probes, "all_as_expected": all(probe["as_expected"] for probe in probes.values()),
            "no_run_differs_from_the_engine_without_saying_so": silent == [],
            "what_this_shows": ["an order that names no drug is resolved by the engine to the running infusion; the mirror hands it over unresolved, so the mapping closes the infusion and says so",
                                "a rate without units is run by the engine in the running infusion's units; the mapping reads the order as written and refuses it, so a pressure target is never read as a rate",
                                "the legacy engine reads 'titrate to MAP 65' as 65 mcg/min when an infusion runs: a defect of the legacy parser, outside this package, reported",
                                "after a refusal the shadow run keeps computing the history it had mapped, which is no longer the encounter's: it says so, and nothing else in the run changes"]}


# -- P3-429: the edge-case matrix ------------------------------------------------------------------------------------------------------------------
def _edge_run(events, turns=EDGE_MINUTES, witness: str | None = WITNESS) -> dict:
    import runtime_shadow_families as fam
    return ta.shadow_run(EDGE_FAMILY, fam.ADAPTERS[EDGE_FAMILY].cases[0], witness, events, turns, scenario_id=f"{PROBES_ID}::edge")


@functools.lru_cache(maxsize=None)
def _edge_reference(kind: str) -> dict:
    return {"NO_ORDER": lambda: _edge_run(()), "START_10": lambda: _edge_run((event(5, "start", 10.0),)), "START_5": lambda: _edge_run((event(5, "start", 5.0),)),
            "START_10_AT_9": lambda: _edge_run((event(9, "start", 10.0),))}[kind]()


def _observed(run: dict, *, equal_to: str | None = None) -> dict:
    writers = writers_of(run)
    log = _log(run)
    out = {"outcomes": [row["outcome"] for row in log], "writer": type(writers[0]).type_name if writers else None, "writers": len(writers),
           "gaps": len([gap for gap in run["gaps"] if gap.get("kind") == "norepinephrine"]), "failures": run["failures"]}
    if equal_to is not None:
        reference = {"THE_SINGLE_START": "START_10", "NO_ORDER": "NO_ORDER", "A_SINGLE_START_AT_MINUTE_9": "START_10_AT_9"}[equal_to]
        out["states_equal_to"] = equal_to if _same_states(run, _edge_reference(reference)) else "DIFFERENT_STATES"
    return out


def _monotone(series: list, start: int) -> str:
    steps = [b - a for a, b in zip(series[start:], series[start + 1:])]
    return "NEVER_FALLS" if all(step >= 0.0 for step in steps) and any(step > 0.0 for step in steps) else "NEVER_RISES" if all(step <= 0.0 for step in steps) and any(step < 0.0 for step in steps) else "MIXED"


def _says_no_longer_mirrors(run: dict) -> bool:
    return any("no longer mirrors the encounter's vasopressor" in gap["why"] for gap in run["gaps"] if gap.get("kind") in ("norepinephrine", "infusion_adjustment"))


def _edge_cases() -> dict:
    from clinical_core import vascular_support as vs
    import runtime_shadow_families as fam
    import runtime_tone_support as ts
    half = _constants()["half_effect_rate_mcg_min"]
    out = {}
    # 01
    run = _edge_run((event(5, "start", 5.0),))
    series = support_series(run)
    out["01_START_FROM_ZERO"] = {**_observed(run), "support_is_zero_through_the_order_minute": all(value == 0.0 for value in series[:6]),
                                 "first_minute_with_support": next(index for index, value in enumerate(series) if value > 0.0), "replays_exactly": run["replay_equal"]}
    # 02 / 03
    for key, first, second, reference in (("02_INCREASE", 5.0, 10.0, "START_5"), ("03_DECREASE", 10.0, 4.0, "START_10")):
        run = _edge_run((event(5, "start", first), event(12, "adjust", second)))
        series = support_series(run)
        target = second / half
        out[key] = {**_observed(run), "same_as_without_the_order_through_its_minute": _same_states(run, _edge_reference(reference), through=12), "support_after_the_order": _monotone(series, 12),
                    "never_past_the_ordered_steady_support": all((value <= target + vs.SUPPORT_QUANTUM) if second > first else (value >= target - vs.SUPPORT_QUANTUM) for value in series[12:]),
                    "replays_exactly": run["replay_equal"]}
    # 04
    run = _edge_run((event(5, "start", 10.0), event(12, "stop")))
    series = support_series(run)
    core = vs.Norepinephrine("core", 5, 10.0, stop_minute=12, **_constants())
    long_run = [ts.NorepinephrineRateHistory("o1", 5, 10.0, changes=((12, 0.0),), orders=(("o1", 5, 10.0, ts.STARTED), ("o2", 12, 0.0, ts.STOPPED)), **_constants()).support_at(minute) for minute in range(0, 200)]
    out["04_STOP"] = {**_observed(run), "support_at_the_stop_minute_is_not_erased": series[12] > 0.0 and series[13] > 0.5 * series[12],
                      "bit_identical_to_the_cores_own_stopped_writer": series == [core.support_at(minute) for minute in range(EDGE_MINUTES + 1)],
                      "support_returns_to_exactly_zero": long_run[-1] == 0.0 and long_run == [core.support_at(minute) for minute in range(0, 200)],
                      "never_negative": min(series) >= 0.0 and min(long_run) >= 0.0, "replays_exactly": run["replay_equal"]}
    # 05
    run = _edge_run((event(5, "start", 10.0), event(12, "stop"), event(16, "start", 10.0)))
    series = support_series(run)
    out["05_RESTART_AFTER_STOP"] = {**_observed(run), "support_after_the_order": _monotone(series, 16),
                                    "never_past_the_ordered_steady_support": all(value <= 10.0 / half + vs.SUPPORT_QUANTUM for value in series), "replays_exactly": run["replay_equal"]}
    # 06
    run = _edge_run((event(5, "start", 10.0), event(9, "continue", 10.0), event(14, "adjust", 10.0)))
    out["06_DUPLICATE_IDENTICAL_RATE"] = {**_observed(run, equal_to="THE_SINGLE_START"), "replays_exactly": run["replay_equal"]}
    # 07
    run = _edge_run((event(5, "start", 5.0, position=0), event(5, "adjust", 10.0, position=1)))
    observed = _observed(run)
    observed["states_equal_to"] = "A_SINGLE_START_AT_THE_LAST_RATE" if _same_states(run, _edge_reference("START_10")) else "DIFFERENT_STATES"
    out["07_TWO_ORDERS_IN_ONE_MINUTE"] = {**observed, "replaced_within_its_minute": [row["replaced_within_its_minute"] for row in _log(run)], "replays_exactly": run["replay_equal"]}
    # 08 / 09
    run = _edge_run((event(5, "start", 10.0), event(12, "adjust", 8.0, units="mg/h"), event(15, "adjust", 6.0)))
    out["08_INVALID_UNIT"] = {**_observed(run, equal_to="THE_SINGLE_START"), "says_it_no_longer_mirrors": _says_no_longer_mirrors(run)}
    run = _edge_run((event(5, "start", 10.0), event(12, "adjust", -5.0)))
    out["09_NEGATIVE_DOSE"] = {**_observed(run, equal_to="THE_SINGLE_START"), "says_it_no_longer_mirrors": _says_no_longer_mirrors(run)}
    # 10
    out["10_STOP_WITHOUT_PRIOR_START"] = _observed(_edge_run((event(5, "stop"), event(9, "start", 10.0))), equal_to="NO_ORDER")
    # 11
    run = _edge_run((event(5, "start", 0.1, units="mcg/kg/min"), event(9, "start", 10.0)))
    out["11A_WEIGHT_BASED_FIRST_ORDER"] = {**_observed(run, equal_to="NO_ORDER"), "never_converted": not writers_of(run)}
    run = _edge_run((event(5, "start", 10.0), event(12, "adjust", 0.2, units="mcg/kg/min")))
    out["11B_WEIGHT_BASED_RATE_CHANGE"] = {**_observed(run, equal_to="THE_SINGLE_START"), "never_converted": [item.to_spec().get("changes") for item in writers_of(run)] == [None],
                                           "says_it_no_longer_mirrors": _says_no_longer_mirrors(run)}
    # 12
    import runtime_shadow as rs
    malformed = {"A_PRESSURE_TARGET": {"type": "norepinephrine", "operation": "titrate to MAP 65", "rate": None, "units": None}, "NO_OPERATION": {"type": "norepinephrine", "rate": 8.0, "units": "mcg/min"},
                 "NO_ACTION": None, "A_RATE_IN_WORDS": {"type": "norepinephrine", "operation": "adjust", "rate": "eight", "units": "mcg/min"},
                 "A_RATE_THAT_IS_NOT_A_NUMBER": {"type": "norepinephrine", "operation": "adjust", "rate": math.nan, "units": "mcg/min"},
                 "AN_INFINITE_RATE": {"type": "norepinephrine", "operation": "adjust", "rate": math.inf, "units": "mcg/min"},
                 "A_ZERO_RATE_THAT_IS_NOT_A_STOP": {"type": "norepinephrine", "operation": "adjust", "rate": 0.0, "units": "mcg/min"},
                 "A_PRESSURE_TARGET_AS_THE_PARSER_HANDS_IT_OVER": {"type": "norepinephrine", "operation": "adjust", "rate": 65.0, "units": None},
                 "A_RATE_WITHOUT_UNITS": {"type": "norepinephrine", "operation": "adjust", "rate": 12.0, "units": None},
                 "A_RATE_TOO_LARGE_TO_BE_A_NUMBER": {"type": "norepinephrine", "operation": "adjust", "rate": 10 ** 400, "units": "mcg/min"},
                 "AN_ACTION_THAT_IS_NOT_AN_ORDER": "adjust norepinephrine to 8 mcg/min",
                 "A_RECEIPT_THAT_SAYS_ANOTHER_RATE": {"type": "norepinephrine", "operation": "adjust", "rate": 8.0, "units": "mcg/min"}}
    receipts = {"A_RECEIPT_THAT_SAYS_ANOTHER_RATE": {"type": "norepinephrine", "operation": "adjust", "rate": 80.0, "units": "mcg/min"}}
    variants = {}
    for label, action in malformed.items():
        bad = rs.MirroredAction("probe-m12-0-norepinephrine", 12, "norepinephrine", action, receipts.get(label, {}), 0.21)
        variants[label] = _observed(_edge_run((event(5, "start", 10.0), bad)), equal_to="THE_SINGLE_START")
    out["12_MALFORMED_ORDER"] = {"variants": variants}
    # 13
    out["13_NO_PULSE_STATE"] = _no_pulse()
    # 14
    sequence = (event(5, "start", 5.0), event(12, "adjust", 10.0), event(19, "adjust", 4.0), event(25, "stop"))
    run = _edge_run(sequence)
    artifact = json.loads(json.dumps(run["runner"].replay_input().to_dict()))
    replayed = fam.replay_shadow_encounter(artifact)
    spec = next(item for item in artifact["scenario"]["contributors"] if item["type"] == ts.NorepinephrineRateHistory.type_name)
    again, chunked = _edge_run(sequence), _edge_run(sequence, turns=(5, 5, 6, 12, 12, 13, 19, 20, 25, 26, 27, 32))
    live = fam.ShadowPhysiologyRunner.open(EDGE_FAMILY, fam.ADAPTERS[EDGE_FAMILY].cases[0], adapter=ts.with_tone_support(fam.adapter_for(EDGE_FAMILY), WITNESS),
                                           scenario_id=f"{PROBES_ID}::edge")          # the same label as the run it is compared with: the artifact carries it
    kinds = []
    for item in sequence:                                  # each order is handed over at its own minute, after that minute was recorded: the writer the run carries changes as the orders arrive
        live.advance(item.minute)
        live.mirror([item])
        kinds.append(type(writers_of({"runner": live})[0]).type_name)
    live.advance(EDGE_MINUTES)
    _gaps = lambda runner: sorted(json.dumps(gap, sort_keys=True, default=str) for gap in runner.gaps)
    out["14_SESSION_RESTART_AND_REPLAY"] = {
        "the_artifact_survives_json_and_replays_exactly": [item["state_digest"] for item in replayed["results"][1:]] == list(run["runner"].digests()),
        "the_artifact_names_the_rate_history_the_units_and_the_writer_version": (spec["start_minute"], spec["rate_mcg_min"], spec["changes"], spec["rate_units"], spec["writer_version"])
        == (5, 5.0, [[12, 10.0], [19, 4.0], [25, 0.0]], "mcg/min", ts.WRITER_VERSION) and [row[0] for row in spec["orders"]] == [item.order_id for item in sequence],
        "a_run_rebuilt_from_the_same_orders_is_the_same": _same_states(run, again) and tuple(again["runner"].contributors()) == tuple(run["runner"].contributors())
        and again["runner"].replay_input().digest() == run["runner"].replay_input().digest(),
        "any_division_into_turns_gives_the_same_states": _same_states(run, chunked),
        "orders_mirrored_as_they_are_given_give_the_same_states": tuple(live.digests()) == tuple(run["runner"].digests()) and not live.failures
        and kinds == ["norepinephrine"] + [ts.NorepinephrineRateHistory.type_name] * 3 and live.replay_input().digest() == run["runner"].replay_input().digest(),
        "orders_mirrored_as_they_are_given_declare_the_same_gaps": _gaps(live) == _gaps(run["runner"]),
        "artifact_digest": run["runner"].replay_input().digest(), "writer_spec": spec}
    # 15
    run = _edge_run((event(5.5, "start", 10.0, order_id="probe-half-minute"), event(9, "start", 10.0)))
    out["15A_ORDER_WITHOUT_A_WHOLE_MINUTE"] = _observed_unplaced(run)
    runner = fam.ShadowPhysiologyRunner.open(EDGE_FAMILY, fam.ADAPTERS[EDGE_FAMILY].cases[0], adapter=ts.with_tone_support(fam.adapter_for(EDGE_FAMILY), WITNESS))
    first = runner.advance(12)
    runner.mirror([event(5, "start", 10.0)])
    second = runner.advance(20)
    out["15B_ORDER_DATED_BEFORE_A_RECORDED_MINUTE"] = {"the_runner_refuses_it": next((item.exception for item in runner.failures if item.where == "history"), None) if first and not second else None,
                                                       "nothing_is_recorded_after_the_refusal": runner.minutes_done == 12 and len(runner.digests()) == 12}
    # 15C (added after the review): the mirror's order is the engine's; an order dated before one that came before it is a contradiction the mapping does not resolve
    out["15C_ORDERS_AGAINST_THE_CLOCK"] = _observed_unplaced(_edge_run((event(9, "start", 10.0), event(5, "start", 10.0))))
    # 16 (added after the review)
    run = _edge_run((event(5, "start", 10.0), role_event(12, "stop"), event(15, "adjust", 6.0)))
    role_gaps = [gap for gap in run["gaps"] if gap.get("kind") == ts.ROLE_KIND]
    idle = _edge_run((role_event(3, "stop", order_id="probe-m3-role"), event(5, "start", 10.0), event(12, "stop"), role_event(14, "adjust", 20.0, "mcg/min", order_id="probe-m14-role"), event(16, "start", 10.0)))
    out["16_ORDER_THAT_NAMES_NO_DRUG"] = {**_observed(run, equal_to="THE_SINGLE_START"), "says_it_no_longer_mirrors": _says_no_longer_mirrors(run),
                                          "the_order_that_names_no_drug_says_why": len(role_gaps) == 1 and "names no drug" in role_gaps[0]["why"],
                                          "left_alone_while_no_norepinephrine_runs": [row["outcome"] for row in _log(idle)] == [ts.STARTED, ts.STOPPED, ts.RESTARTED] and not _says_no_longer_mirrors(idle)
                                          and not [gap for gap in idle["gaps"] if "names no drug" in str(gap.get("why"))]}
    # 17 (added after the review)
    run = _edge_run((event(5, "start", 10.0), event(12, "adjust", 20.0, position=0), event(12, "adjust", 8.0, units="mg/h", position=1), event(15, "stop")))
    out["17_REFUSED_ORDER_IN_THE_MINUTE_OF_A_VALID_ONE"] = {**_observed(run, equal_to="THE_SINGLE_START"), "says_it_no_longer_mirrors": _says_no_longer_mirrors(run)}
    # 18 (added after the review): the session's gaps only accumulate, so a reason must never stop being true
    sequence = (event(5, "start", 5.0, position=0), event(5, "stop", position=1), event(9, "start", 10.0))
    run = _edge_run(sequence)
    live = fam.ShadowPhysiologyRunner.open(EDGE_FAMILY, fam.ADAPTERS[EDGE_FAMILY].cases[0], adapter=ts.with_tone_support(fam.adapter_for(EDGE_FAMILY), WITNESS), scenario_id=f"{PROBES_ID}::edge")
    for item in sequence:                                  # one turn per order: two of them in minute 5
        live.advance(item.minute)
        live.mirror([item])
        live.advance(item.minute)
    live.advance(EDGE_MINUTES)
    rows = fam.action_dispositions(live.adapter, live.mirrored, live.mapping_state)
    declared = {str(gap.get("order_id")) for gap in live.gaps}
    out["18_ORDERS_OF_ONE_MINUTE_ARRIVING_TURN_BY_TURN"] = {
        **_observed(run, equal_to="A_SINGLE_START_AT_MINUTE_9"), "the_gaps_recorded_turn_by_turn_are_the_gaps_of_the_whole": _gaps(live) == _gaps(run["runner"]) and not live.failures
        and tuple(live.digests()) == tuple(run["runner"].digests()),
        "no_order_is_both_declared_and_built": not [row for row in rows if row["disposition"] == fam.BUILT and row["shadow_order_id"] in declared]}
    return out


def _observed_unplaced(run: dict) -> dict:
    out = _observed(run)
    out["states_equal_to"] = "NO_ORDER" if _same_states(run, _edge_reference("NO_ORDER")) else "DIFFERENT_STATES"
    return out


def _no_pulse() -> dict:
    """The common core alone (no authored case reaches this state): an infusion started with a pulse, then changed and stopped without one."""
    from clinical_core import integration as ig
    from clinical_core.modules.rhythm_events import ScriptedRhythmEvent
    from clinical_core.state import RhythmState
    import runtime_tone_support as ts
    anchors, profile, items = ta._gi_core()
    declared = ta._declared(profile, WITNESS)
    orders = (("o1", 5, 10.0, ts.STARTED), ("o2", 12, 20.0, ts.INCREASED), ("o3", 18, 0.0, ts.STOPPED))
    history = ((5, 10.0), (12, 20.0), (18, 0.0))
    writer = ts.NorepinephrineRateHistory("o1", 5, 10.0, changes=history[1:], orders=orders, **_constants())
    arrest = ScriptedRhythmEvent("probe-arrest", 9, RhythmState.asystole(), "not_preventable")
    out = {"the_run_completes": False, "support_is_the_writers_closed_form_with_or_without_a_pulse": False, "no_pressure_is_reported_without_a_pulse": False,
           "the_orders_given_without_a_pulse_are_accounted": [row[3] for row in orders]}
    try:
        with_pulse = ig.run(anchors, items + (writer,), 30, declared)
        without = ig.run(anchors, items + (writer, arrest), 30, declared)
    except Exception as error:
        return {**out, "error": f"{type(error).__name__}: {error}"}
    readings = without.derived()
    pulseless = [minute for minute, reading in enumerate(readings) if not reading.pulse_present]
    expected = closed_form(history, 30)
    out.update({"the_run_completes": True, "first_minute_without_a_pulse": pulseless[0] if pulseless else None,
                "support_is_the_writers_closed_form_with_or_without_a_pulse": [state.aux.vasoconstrictor_support or 0.0 for state in without.states] == expected
                == [state.aux.vasoconstrictor_support or 0.0 for state in with_pulse.states],
                "no_pressure_is_reported_without_a_pulse": bool(pulseless) and all(readings[minute].sbp is None and readings[minute].map is None and readings[minute].pressure_rel == 0.0
                                                                                   for minute in pulseless)})
    return out


def edge_matrix() -> list:
    observed = _edge_cases()
    rows = []
    for key, expected in EDGE_EXPECTED.items():
        seen = observed[key]
        if key == "12_MALFORMED_ORDER":
            ok = sorted(seen["variants"]) == sorted(expected["variants"]) and all(all(variant.get(name) == value for name, value in expected["each_variant"].items()) and not variant["failures"]
                                                                                  for variant in seen["variants"].values())
        else:
            ok = all(seen.get(name) == value for name, value in expected.items()) and not seen.get("failures") and "error" not in seen
        row = {"case": key, "what": EDGE_DESCRIPTIONS[key], "expected_before_executing": expected, "observed": seen, "as_expected": bool(ok)}
        if key in EDGE_REVISED_AFTER_THE_REVIEW:
            row["revised_after_the_adversarial_review"] = EDGE_REVISED_AFTER_THE_REVIEW[key]
        if key in EDGE_ADDED_AFTER_THE_REVIEW["cases"]:
            row["added_after_the_adversarial_review"] = True
        rows.append(row)
    return rows


# -- P3-433: the same history in the families the faculty named ------------------------------------------------------------------------------------
def family_run(family: str, sequence=FAMILY_SEQUENCE, witness: str | None = WITNESS) -> dict:
    import runtime_shadow_families as fam
    return ta.shadow_run(family, fam.ADAPTERS[family].cases[0], witness, events_of(sequence), EDGE_MINUTES, scenario_id=f"{PROBES_ID}::{family}")


def multifamily() -> dict:
    import runtime_shadow_families as fam
    import runtime_tone_support as ts
    stored = ta.load(ta.PROBES_PATH)
    history = tuple((minute, 0.0 if rate is None else rate) for minute, _operation, rate in FAMILY_SEQUENCE)
    expected = closed_form(history, EDGE_MINUTES)
    families, series_by_family = {}, {}
    for family, role in FAMILY_CASES.items():
        case_id = fam.ADAPTERS[family].cases[0]
        run, reference = family_run(family), family_run(family, witness=None)
        quiet = ta.shadow_run(family, case_id, WITNESS, (), EDGE_MINUTES)
        registered = ta.shadow_run(family, case_id, None, (), EDGE_MINUTES)
        single_reference = ta.shadow_run(family, case_id, None, (ta.order_event(ta.PROBE_ORDER_MINUTE),), ta.PROBE_MINUTES)
        single = ta.shadow_run(family, case_id, WITNESS, (ta.order_event(ta.PROBE_ORDER_MINUTE),), ta.PROBE_MINUTES)
        seen = [ta.observed(single_reference["rows"], single["rows"], minute) for minute in (ta.PROBE_ORDER_MINUTE + 2, ta.PROBE_ORDER_MINUTE + 5, ta.PROBE_MINUTES)]
        series = support_series(run)
        series_by_family[family] = series
        writers = writers_of(run)
        families[family] = {
            "case_id": case_id, "role": role, "pump_limited": family in PUMP_LIMITED,
            "orders": [row["outcome"] for row in _log(run)], "writers": [type(item).type_name for item in writers], "gaps": [gap for gap in run["gaps"] if gap.get("kind") == "norepinephrine"],
            "failures": run["failures"], "replays_exactly": bool(run["replay_equal"] and run["same_states_as_the_runner"]),
            "support_is_the_closed_form": series == expected, "untouched_state": ta.untouched(reference["rows"], run["rows"]),
            "pressure_never_below_the_unmapped_run_while_support_remains": all(b["pressure_rel"] >= a["pressure_rel"] for a, b in zip(reference["rows"][:26], run["rows"][:26])),
            "at_the_reads": [{"minute": minute, "support": ta._r(series[minute]), "displayed": ta.displayed(run["rows"][minute]), "displayed_without_any_mapped_order": ta.displayed(reference["rows"][minute])}
                             for minute in (5, 12, 19, 25, 32)],
            # with the reader declared the support is TRACKED (0 instead of not tracked): every reading and every other part of the state is the same, as the certified test of P3-396 states it
            "no_tone_action_the_trajectory_is_unchanged": _readings(quiet) == _readings(registered) and all((row["support"] or 0.0) == 0.0 for row in quiet["rows"])
            and not quiet["gaps"] and not quiet["failures"],
            "the_certified_single_start_is_unchanged": {"writer": [type(item).type_name for item in writers_of(single)], "observed_now": seen,
                                                        "equal_to_the_certified_probe_record": seen == stored["family_probes"][family]["witnesses"][WITNESS]["observed"]},
            "educational_promotion": "BLOCKED (COMMON_TONE_PUMP_DEPENDENCE_NOT_YET_VALIDATED)" if family in PUMP_LIMITED else "NOT_CLAIMED (a development probe)"}
    synthetic = low_tone()
    ok = (all(item["orders"] == [ts.STARTED, ts.INCREASED, ts.DECREASED, ts.STOPPED] and item["writers"] == [ts.NorepinephrineRateHistory.type_name] and not item["gaps"] and not item["failures"]
              and item["replays_exactly"] and item["support_is_the_closed_form"] and all(item["untouched_state"].values()) and item["no_tone_action_the_trajectory_is_unchanged"]
              and item["pressure_never_below_the_unmapped_run_while_support_remains"]
              and item["the_certified_single_start_is_unchanged"]["equal_to_the_certified_probe_record"] and item["the_certified_single_start_is_unchanged"]["writer"] == ["norepinephrine"]
              for item in families.values())
          and len({tuple(series) for series in series_by_family.values()}) == 1 and synthetic["as_expected"])
    return {"sequence": [list(item) for item in FAMILY_SEQUENCE], "witness": WITNESS, "families": families, "low_tone_synthetic_probe": synthetic,
            "the_support_is_the_same_in_every_family": len({tuple(series) for series in series_by_family.values()}) == 1,
            "why": "the writer reads its orders and time only: the same orders give the same support whatever the family, and what differs is what each family's flow, preload and pump make of the tone",
            "no_regression": bool(ok), "pump_limited_use_is_not_promoted": True}


def low_tone() -> dict:
    """The synthetic low-tone probe of the certified record (SYNTHETIC_ONLY), with the same order history: the positive control."""
    from clinical_core import distributive_tone as dt
    from clinical_core import integration as ig
    import runtime_tone_support as ts
    anchors = dt.probe_anchors()
    declared = ta._declared(dt.reader(dt.base_profile()), WITNESS)
    burden = (dt.SyntheticVasodilation("probe-burden", dt.BURDEN_STEP, 0, 4),)
    history = ((10, 5.0), (17, 10.0), (24, 4.0), (30, 0.0))
    orders = (("o1", 10, 5.0, ts.STARTED), ("o2", 17, 10.0, ts.INCREASED), ("o3", 24, 4.0, ts.DECREASED), ("o4", 30, 0.0, ts.STOPPED))
    writer = ts.NorepinephrineRateHistory("o1", 10, 5.0, changes=history[1:], orders=orders, **_constants())
    plain, infused = ig.run(anchors, burden, 40, declared), ig.run(anchors, burden + (writer,), 40, declared)
    a, b = plain.derived(), infused.derived()
    series = [state.aux.vasoconstrictor_support or 0.0 for state in infused.states]
    stored = ta.load(ta.PROBES_PATH)["core_probes"]["distributive"]
    again = json.loads(json.dumps(ta.core_distributive(WITNESS)))
    gain = {minute: b[minute].pressure_rel - a[minute].pressure_rel for minute in (10, 17, 24, 30, 40)}
    out = {"probe": "SYNTHETIC_ONLY: clinical_core.distributive_tone probe anchors and scripted burden; no authored case and no family adapter",
           "rate_history": [list(item) for item in history], "support_is_the_closed_form": series == closed_form(history, 40),
           "pressure_gain_over_the_low_tone_run": {str(minute): ta._r(value) for minute, value in gain.items()},
           "ordering_as_the_rates": gain[24] > gain[17] > gain[30] > gain[40] >= -1e-12 and gain[10] == 0.0,
           "pressure_never_above_arrival": all(reading.pressure_rel <= 1.0 + 1e-9 for reading in b),
           "the_certified_single_start_probe_is_unchanged": again == stored}
    out["as_expected"] = bool(out["support_is_the_closed_form"] and out["ordering_as_the_rates"] and out["the_certified_single_start_probe_is_unchanged"])
    return out


# -- the design, as data ---------------------------------------------------------------------------------------------------------------------------
def design() -> dict:
    import runtime_shadow as rs
    import runtime_tone_support as ts
    from clinical_core import amendment_3 as a3
    from clinical_core import vascular_support as vs
    return {
        "order_semantics_audit": {
            "verdict": "B", "verdict_name": "SMALL_NOREPINEPHRINE_EVENT_ADAPTER_REQUIRED",
            "verdicts": {"A": "EXISTING_GENERIC_INFUSION_SEMANTICS_SUFFICIENT", "B": "SMALL_NOREPINEPHRINE_EVENT_ADAPTER_REQUIRED", "C": "GENERIC_INFUSION_MODEL_REQUIRES_SUCCESSOR",
                         "D": "CURRENT_ORDER_MODEL_CANNOT_REPRESENT_TITRATION_SAFELY"},
            "found": {"action_type": "norepinephrine (family_parser), with operation start / adjust / continue / stop; 'increase' and 'decrease' are read as adjust with ONE absolute target rate, and a relative change or two rates in one order is answered with a clarification, never executed",
                      "rate_and_units": ("rate with units mcg/min or mcg/kg/min (family_engine validates 0.001 to 100 mcg/min or 0.001 to 1.5 mcg/kg/min). A stop needs neither and may carry both "
                                         "('stop norepinephrine 10 mcg/min'): it is a stop. An adjustment or a continuation may be WRITTEN without units or without a rate: the engine completes "
                                         "it from the running infusion (active_order_context) before it executes it"),
                      "orders_that_name_no_drug": ("'stop the infusion' and 'increase the infusion rate to 20 mcg/min' are parsed as another action type, infusion_adjustment, which the engine "
                                                   "resolves to the ONE running infusion among norepinephrine, nitroglycerin and dobutamine (and refuses when none or more than one runs)"),
                      "what_the_mirror_hands_over": ("the PARSED action, as written, before the engine resolves or completes it, with the engine's receipt paired by the parsed kind: a norepinephrine "
                                                     "order carries the engine's settled order in its receipt; an order that names no drug arrives as infusion_adjustment with an EMPTY receipt, so "
                                                     "nothing in it says which infusion the engine changed"),
                      "a_legacy_defect_found_and_not_touched": ("'titrate norepinephrine to MAP 65' is parsed as an adjustment to a rate of 65 with no units, and the legacy engine runs it as "
                                                                "65 mcg/min when an infusion is running: outside this package, reported"),
                      "engine_state": "ONE absolute active rate per infusion (family_state['norepinephrine']): every executed order replaces it, a stop sets it to 0; a weight-based rate is converted by the engine with the case's weight",
                      "timestamp_and_minute": "the mirror dates an order at the encounter minute of the state it was given from (sim_time before the turn); a held order is dated at the minute the engine executed it",
                      "identity_and_duplicates": "one shadow order id per (minute, turn, position, kind) and the ledger's own order id; the same turn observed twice is mirrored once, and the mapping counts an order id once",
                      "deferred_orders": "an order held until a result is mirrored only when the engine runs it, at that minute; one the engine never ran is never mirrored",
                      "persistence_and_serialization": "the session keeps the mirrored actions; the replay artifact holds each action's identity (never the resident's text) and the scenario's contributors as plain data (integration.scenario_to_dict)",
                      "artifact_replay": "a run is recomputed from arrival with the contributors mirrored so far, and a contributor that changes a minute already recorded is refused (HistoryRewritten); the artifact replays through the same function",
                      "what_was_missing": "the development mapping built only the encounter's FIRST start, and the core's writer represents one fixed rate with an optional stop: a rate that changes had no representation",
                      "corrected_after_the_adversarial_review": ("the first audit said a stop carries neither a rate nor units and did not find the orders that name no drug nor that the mirror hands "
                                                                 "the order over as written; the three are corrected above, and the verdict B stands")}},
        "event_stream": {"model": "ONE infusion: an ordered stream (t0, rate0), (t1, rate1), ..., (t_stop, 0); the rate ordered at a time is the LAST valid event at or before it; rates are never integrated together",
                         "operations": {"START": "0 -> r (the run must have seen it)", "INCREASE": "r -> r' above r", "DECREASE": "r -> r' below r and above 0", "STOP": "r -> 0",
                                        "RESTART": "0 -> r after a stop, the same infusion", "IDEMPOTENT_NO_CHANGE": "the same rate again, a bare continuation, or a stop of a stopped infusion: carried, nothing changes"},
                         "engine_vocabulary_read": list(ts.MAPPED_OPERATIONS), "units_read": ts.MAPPED_UNITS, "outcomes_of_a_carried_order": list(ts.OUTCOMES),
                         "what_an_order_not_carried_is": list(ts.NOT_CARRIED),
                         "read_as_written": ("the order must itself say mcg/min; the one exception is a continuation that gives no rate and no units, which keeps the rate ordered before it (and the "
                                             "engine's receipt, when there, must say that rate). When a receipt is there it must agree with the order, or the order is refused"),
                         "increase_and_decrease_are_read_from_the_rates": "the engine has one operation for both (adjust, with an absolute rate); which one an order was is read against the rate ordered before it"},
        "temporal_contract": {"order_minute": "the encounter minute of the state the order was given from",
                              "first_physiologic_effect": "the support first moves over (s, s + 1]; the tone, which follows the state one minute behind, and the pressure first move over (s + 1, s + 2]",
                              "no_retroactive_change": "nothing at or before the order minute changes; a contributor that would change a recorded minute is refused by the runner",
                              "no_look_ahead": "a minute's contribution depends on the orders before it only",
                              "same_minute": ("within one minute the LAST valid order in the engine's order is the one a modelled interval carries, and the ONLY one the infusion carries; an earlier one is a "
                                              "declared gap (replaced within its minute). When the last order of the minute is one the mapping refuses, the valid ones before it in that minute are "
                                              "replaced too, and the history the run keeps ends before that minute"),
                              "the_engines_order_is_the_mirrors": "orders are read in the order the mirror holds them; an order dated before one that came before it is refused with every order of the kind",
                              "a_reason_never_stops_being_true": ("the session's gaps only accumulate, so a declared order never becomes a carried one when more orders arrive: each reason depends on the "
                                                                  "order, on those before it, and on whether a later order of its own minute exists"),
                              "turn_boundaries_and_reassessment": "the trajectory does not depend on how the minutes are divided into turns",
                              "deferred_execution": "a held order acts from the minute the engine executed it, never from the minute it was placed"},
        "dynamics": {"rule": "the contribution approaches the steady support of the rate ordered (rate over half-effect rate), first order, with the writer's ONSET constant while it is below it and its OFFSET constant while it is above it",
                     "why_this_rule": ("it is the core's own closed form at both of its ends (a start from nothing rises with the onset constant, a stop decays with the offset constant) and it is continuous "
                                       "between them: a decrease to a rate near 0 behaves like a stop, a restart from a residue like a start. It is the simplest rule with those properties, not the only "
                                       "conceivable one: it is a development choice, and no faculty member has reviewed it yet"),
                     "what_direction_means": ("the contribution moves toward the rate ordered and never past it; against the same history WITHOUT the last order it is never above after a decrease or a stop "
                                              "and never below after an increase or a restart. It does NOT mean the contribution falls the moment a lower rate is ordered: a decrease ordered before the "
                                              "steady effect keeps rising toward the lower rate's steady support"),
                     "checked_independently": "against a numerical integration of dx/dt = (target - x) / tau that shares no arithmetic with the writer",
                     "constants": {**_constants(), "tone_gain": _witness()["tone_gain"]}, "constants_changed": False, "new_constants": [],
                     "rejected": {"stop_the_old_infusion_and_start_a_new_one": "two streams at once: with these constants a small increase overshoots the new steady support, and a small decrease first RAISES the support",
                                  "add_an_infusion_for_each_increment": "several rates integrated together, and no exact form for a decrease before the steady effect"}},
        "governance": {"verdict": "A", "verdict_name": "RUNTIME_ADAPTER_ONLY",
                       "verdicts": {"A": "RUNTIME_ADAPTER_ONLY", "B": "AMENDMENT_3_SUCCESSOR_CONFIGURATION_ONLY", "C": "NEW_COMMON_CORE_SUCCESSOR", "D": "AMENDMENT_4_PHYSIOLOGY_CHANGE"},
                       "why": "no file of clinical_core changes: the common state, its reader, the tone equation, the afterload and every constant are the certified ones; the rate history is a writer that IS the core's writer (a subclass in the development mapping module) and honours its writer contract",
                       "core_digest": a3.amended_core_digest_now(), "clinical_core_edited": False, "lineage_member": ts.REVISION, "grant_changed": False},
        "writer": {"class": "runtime_tone_support.NorepinephrineRateHistory", "is_a": "clinical_core.vascular_support.Norepinephrine", "type_name": ts.NorepinephrineRateHistory.type_name,
                   "version": ts.WRITER_VERSION, "one_writer_per_run": True, "single_start_still_builds": vs.Norepinephrine.type_name,
                   "writes": "one VasoconstrictionChange a minute to the common vasoconstrictor support; no channel, no pressure, no volume, no pump",
                   "reads": "its own orders and time (the writer contract): no pressure, tone, output, delivery or any other reading"},
        "fail_closed": {"rule": ("the first order the mapping cannot read closes the infusion: it and every later order of the kind are declared gaps, nothing after it is applied, and the run says it no "
                                 "longer mirrors the encounter's vasopressor"),
                        "what_the_run_keeps_computing_after_a_refusal": ("the history it had mapped, at its last rate, for the rest of the encounter: NOT what the engine runs. A shadow run has no "
                                                                         "safe value for an infusion it can no longer follow, so it says so and changes nothing else"),
                        "refused": ["an operation that is not start, adjust, continue or stop", "an order that gives no units (so a pressure target written as a bare number is never read as a rate)",
                                    "units other than mcg/min (mcg/kg/min is never converted)", "a rate that is not a finite positive number, or two different rates in one order",
                                    "an order and a receipt that disagree", "an adjustment, a continuation or a stop of an infusion the run never saw start", "a rate the core's own writer refuses",
                                    "an order that names no drug while the norepinephrine runs (the mirror does not say which infusion the engine changed)",
                                    "an order without an identity or a whole minute, or orders against the clock (then none of the kind is mapped)",
                                    "a second norepinephrine writer in the run (the run is refused)"],
                        "declared_and_never_raised": "an action that is not a mapping, a rate too large to be a number, an order id that is not text: each is a declared gap, not an exception"},
        "replay": {"the_artifact_binds": ["every order's identity, minute and receipt digest (actions)", "the rate history ((minute, rate), ...) and its units", "every order the infusion carries, with its outcome",
                                          "the writer's version", "the witness values and the lineage member (the snapshot's provenance) and the declared profile field"],
                   "a_specification_is_rebuilt_only_if_it_names": list(ts.SPEC_NAMES),
                   "what_the_writer_checks_of_its_own_accounting": ("one order a minute, in time; the first is the start, at the first rate; each outcome is what its rate did to the rate before it; "
                                                                    "and the rate history is exactly what the orders make"),
                   "what_it_cannot_check": ("that the orders it names are the encounter's: that is the artifact's, which stores the mirrored actions beside the contributors. The core's replay does not "
                                            "check the witness constants in a specification against the declared witness either (it never did, for any contributor)"),
                   "historical_single_start_artifacts": "replay unchanged: the single start still builds the core's own writer, with the same specification",
                   "a_rate_history_replays_where": "in a process that has loaded the development mapping module (the type is registered there); elsewhere the artifact is refused by name, never approximated",
                   "registration": ("the type registers when the module is imported and the mapping registers BOTH writers it builds -- the core's own and the rate history -- each time it builds "
                                    "(ensure_registered): a registry that was swapped when a module was first imported does not keep the registration, and the full certification found that this "
                                    "happens to the core's own writer under a module-scoped historical view (not caused by this package: the same order fails on the base commit). A historical "
                                    "view of an earlier tree filters the registry by the core's own new types only, so the rate-history type, which is the Phase-3 layer's and not the core's, "
                                    "stays listed inside such a view: nothing there builds it")},
        "layer": {"module": "runtime_tone_support.py", "in_the_layer_digest": "runtime_tone_support.py" in rs.LAYER_SOURCES, "summary": ts.summary()},
    }


# -- P3-434: the negative-control management scenario --------------------------------------------------------------------------------------------
def build_negative_control() -> dict:
    import faculty_tone_review as ftm
    import faculty_trajectory_review as ftr
    human = json.loads((REV / "PHASE3_HUMAN_COMMON_TONE_MULTIFAMILY_REVIEW.json").read_text(encoding="utf-8"))
    ratification = json.loads((REV / "COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json").read_text(encoding="utf-8"))
    loaded = ftm.load_set()
    item = loaded["items"]["PULM-EDEMA"]
    judged = next(entry for entry in human["scenarios"] if entry["scenario_id"] == "PULM-EDEMA")
    family, case_id = "pulmonary_edema", "pulmonary_edema_58m"
    reference = ta.shadow_run(family, case_id, None, (ta.order_event(ta.PROBE_ORDER_MINUTE),), ta.PROBE_MINUTES)
    run = ta.shadow_run(family, case_id, WITNESS, (ta.order_event(ta.PROBE_ORDER_MINUTE),), ta.PROBE_MINUTES)
    now = [ta.displayed(row) for row in run["rows"]]
    body = {"record_type": "NEGATIVE_CONTROL_MANAGEMENT_SCENARIO", "version": "P3-434", "scenario_id": "HYPERTENSIVE_PULMONARY_EDEMA_NOREPI",
            "classification": "NEGATIVE_CONTROL_MANAGEMENT_SCENARIO", "decision_reference": "FD-TITRATE-10 (it formalizes FD-TONE-RATIFY-06)", "decided_on": DECIDED_ON, "date": GENERATED_ON,
            "purpose": ("To show that a physiologically understandable pressor response can still be a clinically inappropriate management action: the response of the common mechanism is what it is, "
                        "and the order is the wrong one for this patient. Physiologic response is not appropriate management."),
            "case": {"family": family, "case_id": case_id, "title_in_the_review_set": item["title"], "arrival_pressure_displayed": item["common"][0]},
            "intervention": {"order": "norepinephrine, start, 10 mcg/min", "minute": ta.PROBE_ORDER_MINUTE, "read_until": ta.PROBE_MINUTES, "as_reviewed": item["intervention"]},
            "human_evidence": {"evidence_class": "HUMAN_FACULTY_REVIEW", "overall": judged["overall"], "first_pass": judged["first_pass"],
                               "faculty_interpretation_as_reported": judged["faculty_interpretation_as_reported"],
                               "record": {"file": "docs/revision/PHASE3_HUMAN_COMMON_TONE_MULTIFAMILY_REVIEW.json", "record_digest": human["record_digest"],
                                          "verification": human["provenance_of_the_evidence"]["verification"]},
                               "the_reject_is_not_converted": "the REJECT stays a REJECT of the management action; it is not a mechanism failure and it is not softened into an acceptance"},
            "earlier_classification": {"classification": ratification["scenario_classification"]["PULM-EDEMA"]["classification"], "negative_control_candidate": True,
                                       "record": {"file": "docs/revision/COMMON_TONE_DEVELOPMENT_SNAPSHOT_V1_RATIFICATION.json", "record_digest": ratification["record_digest"]}},
            "mechanism_failure": False,
            "physiology": {"altered": False, "witness": WITNESS, "writer": [type(writer).type_name for writer in writers_of(run)],
                           "reviewed_item_digest": ftr.item_digest(item), "reviewed_trajectory_digest": judged["reviewed_trajectory_digest"], "review_set_digest": loaded["digest"],
                           "the_trajectory_recomputed_now_is_the_one_the_faculty_reviewed": now == item["common"],
                           "displayed_pressure": {"at_the_order": now[ta.PROBE_ORDER_MINUTE], "at_the_end": now[ta.PROBE_MINUTES],
                                                  "without_the_order_at_the_end": ta.displayed(reference["rows"][ta.PROBE_MINUTES])},
                           "nothing_was_changed_to_make_the_intervention_look_beneficial_or_harmless": True},
            "what_it_is_evidence_of": ["a pressure response in the expected direction and with a plausible timing (Q1 Expected, Q2 Plausible)",
                                       "a management action the faculty rejected for this patient (Q3 Too large, Q4 Incoherent, Q5 Yes: already profoundly hypertensive, acute cardiogenic pulmonary edema)"],
            "use": {"status": "FORMALIZED_AS_A_RECORD", "built_into_the_application": False, "resident_visible": False, "scored": False,
                    "norepinephrine_made_unavailable": False,
                    "future": "a management-reasoning scenario in which the order is available and its consequence can be judged; building it is a separate decision"},
            "titration_and_stop": "not part of this scenario: it is the single start the faculty reviewed; nothing in it was re-run with a rate change",
            "is_not": ["a mechanism failure", "a recalibration request", "a change of the case's physiology", "a restriction of the order", "clinical validation", "an educational claim about pump-limited families"]}
    body["provenance"] = hr.provenance(record_id=NEGATIVE_CONTROL_ID, generating_code=generating_code(), generated_on=GENERATED_ON,
                                       source_data={"human": human["record_digest"], "ratification": ratification["record_digest"], "set": loaded["digest"], "displayed": now})
    return hr.seal(body)


# -- the records -----------------------------------------------------------------------------------------------------------------------------------
def generating_code() -> dict:
    """What generated these records, by content: the live common core, every application module and the harnesses."""
    out = ta.generating_code()
    out["test_tone_titration_analysis.py"] = ta._sha(Path(__file__).resolve())
    return out


def build_probes() -> dict:
    gi, matrix, families = gi_probes(), edge_matrix(), multifamily()
    body = {"record_type": "NOREPINEPHRINE_TITRATION_DEVELOPMENT_PROBES", "version": PROBES_ID, "decisions": DECISIONS, "statement": STATEMENT, "witness": WITNESS,
            "design": design(), "gi_probes": gi,
            "edge_cases": {"expected_outcomes_were_written_before_the_matrix_was_executed": True,
                           "after_the_adversarial_review": {"revised": sorted(EDGE_REVISED_AFTER_THE_REVIEW), "added": dict(EDGE_ADDED_AFTER_THE_REVIEW),
                                                            "said_plainly": ("the first matrix (17 rows) was written before it was executed and all 17 were as expected. The review then showed that one "
                                                                             "of those expectations described a wrong rule (07) and that the matrix missed cases. 07 was revised, with its original kept "
                                                                             "in its row, and the cases and variants listed here were added, each written before it was run through the repaired mapping")},
                           "rows": matrix, "all_as_expected": all(row["as_expected"] for row in matrix)},
            "real_text_probes": real_text_probes(),
            "multifamily": families,
            "limitations": ["one witness (CENTER_REFERENCE): no LOW/HIGH run of these histories (FD-TITRATE-13)",
                            "the rule for a rate change (onset while rising, offset while falling) is the continuous extension of the reviewed start and of the core's stop; no faculty member has yet reviewed a titration trajectory",
                            "heart rate, capillary refill, consciousness, output, delivery and debt are not part of what is read here; consciousness under tone stays unresolved and is not derived",
                            "pump-limited families are run for non-regression only: the pump-dependence limitation stays open and nothing is promoted",
                            "an order the engine ran and the session did not observe (a held order released in an unobserved interval) is declared by the session, not by this mapping: the run cannot know the infusion changed",
                            ("the mirror hands an order over as it was written, before the engine resolves or completes it. So an order that names no drug ('stop the infusion') and an adjustment "
                             "written without units ('increase norepinephrine to 12') CLOSE the infusion: the run declares it, keeps computing the history it had mapped, and from then on does not "
                             "show what the engine runs -- a later explicit stop included. Mirroring the engine's settled order instead is a change to the shared mirror, not made here"),
                            "the legacy engine runs 'titrate norepinephrine to MAP 65' as 65 mcg/min when an infusion is running (a legacy parser defect, outside this package); the mapping refuses the order",
                            "a rate history replays only where the development mapping module is loaded",
                            "the legacy engine keeps its own vasopressor rule and remains the only runtime authority; norepinephrine is outside the live authority"],
            "not_done": ["automatic titration, a pressure target or a closed loop", "weight-based dosing", "another vasopressor", "any change of a tone constant or of the afterload coupling", "authority", "a human review of these trajectories"]}
    body["provenance"] = hr.provenance(record_id=PROBES_ID, generating_code=generating_code(), generated_on=GENERATED_ON,
                                       source_data={"scripts": GI_SCRIPTS, "real_text_scripts": REAL_TEXT_SCRIPTS, "real_text_expected": REAL_TEXT_EXPECTED, "edge_expected": EDGE_EXPECTED,
                                                    "edge_revised": EDGE_REVISED_AFTER_THE_REVIEW, "edge_added": EDGE_ADDED_AFTER_THE_REVIEW, "sequence": FAMILY_SEQUENCE, "witness": _witness()})
    return hr.seal(body)


def write_records() -> dict:
    return {str(PROBES_PATH.relative_to(ROOT)): hr.write(PROBES_PATH, build_probes()),
            str(NEGATIVE_CONTROL_PATH.relative_to(ROOT)): hr.write(NEGATIVE_CONTROL_PATH, build_negative_control())}


def content_of(record: dict) -> dict:
    return {name: value for name, value in record.items() if name not in ("provenance", "record_digest")}


VERDICTS = {"A": "NOREPINEPHRINE_TITRATION_AND_STOP_READY_FOR_HUMAN_DEVELOPMENT_REVIEW", "B": "ORDER_SEMANTICS_REQUIRE_FACULTY_DECISION", "C": "TITRATION_REQUIRES_GENERIC_INFUSION_REDESIGN",
            "D": "REPLAY_SEMANTICS_NOT_CERTIFIABLE", "E": "IMPLEMENTATION_REQUIRES_NEW_PHYSIOLOGY"}


def build_checkpoint(verdict: str, certification: dict, adversarial_review: dict, *, sequence: list, why_not_the_others: dict, facts: dict | None = None) -> dict:
    """The checkpoint record, written ONCE after the certification."""
    import runtime_authority as ra
    import runtime_pressure_grant as grants
    import runtime_shadow as rs
    import runtime_tone_support as ts
    probes = json.loads(PROBES_PATH.read_text(encoding="utf-8"))
    control = json.loads(NEGATIVE_CONTROL_PATH.read_text(encoding="utf-8"))
    body = {"record_type": "NOREPINEPHRINE_TITRATION_CHECKPOINT", "version": CHECKPOINT_ID, "decision_reference": DECISIONS, "statement": STATEMENT,
            "verdict": verdict, "verdict_name": VERDICTS[verdict], "verdicts": dict(VERDICTS), "why_not_the_others": why_not_the_others,
            "facts": {"probes_record_digest": probes["record_digest"], "negative_control_record_digest": control["record_digest"],
                      "order_semantics_audit": probes["design"]["order_semantics_audit"]["verdict_name"], "governance": probes["design"]["governance"]["verdict_name"],
                      "gi_checks": probes["gi_probes"]["checks"], "edge_cases_as_expected": {row["case"]: row["as_expected"] for row in probes["edge_cases"]["rows"]},
                      "real_text_probes_as_expected": {name: probe["as_expected"] for name, probe in probes["real_text_probes"]["probes"].items()},
                      "no_run_differs_from_the_engine_without_saying_so": probes["real_text_probes"]["no_run_differs_from_the_engine_without_saying_so"],
                      "multifamily_no_regression": probes["multifamily"]["no_regression"], "writer_version": ts.WRITER_VERSION, "core_digest": probes["design"]["governance"]["core_digest"],
                      "norepinephrine_in_supported_actions": ts.ORDER_KIND in ra.SUPPORTED_ACTIONS, "norepinephrine_not_granted_by_the_live_grant": "norepinephrine" in grants.LIVE_GRANT["not_granted"],
                      "common_core_runtime_authority": rs.COMMON_CORE_RUNTIME_AUTHORITY, **(facts or {})},
            "confirmations": {"no_tone_recalibration": True, "no_pump_coupling_change": True, "no_new_physiology": True, "no_authority_expansion": True, "no_consciousness_authority": True,
                              "no_terminal_authority": True, "no_resident_deployment": True, "no_clinical_validation_claim": True, "clinical_core_not_edited": True,
                              "no_automatic_titration_or_pressure_target": True, "no_weight_based_dosing": True, "no_other_vasopressor": True},
            "limitations": probes["limitations"], "adversarial_review": adversarial_review, "certification": certification, "sequence": sequence,
            "next_human_action": ("A faculty member looks at the titration and stop development trajectories of the GI hemorrhage case (direction, timing, ordering, smoothness, persistence and decay; "
                                  "no mmHg calibration) and says whether the rule for a rate change -- onset while rising, offset while falling -- is acceptable for development."),
            "open_faculty_decisions": ["whether the titration and stop trajectories are acceptable for development (a human review, not held)",
                                       ("whether the shadow should mirror the engine's SETTLED order (so that 'stop the infusion' and an adjustment written without units are followed) instead of "
                                        "closing the infusion: an architectural change to the shared mirror, with the legacy 'MAP 65' defect to be settled first"),
                                       "whether the first refused order should keep closing the infusion for the rest of the encounter, or a later explicit rate or stop should be followed again",
                                       "whether an adjustment ordered while the infusion is stopped should keep being read as a restart", "whether the negative-control scenario is ever built into the application",
                                       "whether the pump-dependence and consciousness limitations need work before any educational use"]}
    parts = {**generating_code(), "probes_record_digest": probes["record_digest"], "negative_control_record_digest": control["record_digest"]}
    body["provenance"] = hr.provenance(record_id=CHECKPOINT_ID, generating_code=parts, generated_on=GENERATED_ON, grant_id="GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V3",
                                       source_data={"verdict": verdict, "certification": certification, "adversarial_review": adversarial_review, "sequence": sequence})
    return hr.seal(body)


def write_checkpoint(*args, **kwargs) -> dict:
    return {str(CHECKPOINT_PATH.relative_to(ROOT)): hr.write(CHECKPOINT_PATH, build_checkpoint(*args, **kwargs))}


if __name__ == "__main__":
    print(json.dumps(write_records(), indent=2))
