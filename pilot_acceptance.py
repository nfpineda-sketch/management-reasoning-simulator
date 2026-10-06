"""The acceptance battery every pilot case runs (Phase 0, 0J).

Pre-pilot measurement safety, 2026-10-06. Each bank case is played through the scenarios the
Phase 0 request names -- A correct management, B delayed, C omission, D incorrect treatment,
E excessive treatment, F start and stop, G duplicate, H unexpected but reasonable, I waiting,
J reassessment, K combined interventions -- and through the course properties it asks for:
terminal deterioration, recovery, resume, deterministic replay, ledger completeness, event
provenance, observation consistency and the analysis guards.

The assertions are directional, never exact numbers: timely care is better than omission,
delay is no better than timely care, a known harmful treatment does not improve the patient,
an order the simulator did not carry out changes nothing, no contradiction is ever shown.

The turns run the family branch of the page's own order path without Streamlit: the frozen
reader, the time words (0E), the ledger (0A), the bundle rule (0B) and the engine, in that
order. The reasoning gate, the clarification answers and the saving belong to the page, and
``test_phase0_acceptance_page.py`` runs every case through the page itself.
"""
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

#: The challenge each family is launched with (any one that offers it).
LAUNCH = {"pneumonia": "R2-05", "pulmonary_edema": "R1-05", "acs": "R2-02", "pulmonary_embolism": "R2-02",
          "asthma": "R3-01", "gi_bleed": "R2-05", "hypoglycemia": "R1-06", "opioid": "R1-06",
          "anaphylaxis": "R1-06", "renal_colic": "R2-05", "bradycardia": "R2-04", "trauma": "R2-05"}
SEED = 17

#: What each family's scenarios write. ``correct`` is the bundle the case declares as
#: definitive (``engine.definitive_actions``); the others are the request's categories.
FAMILY_SCRIPTS = {
    "pneumonia": {
        "correct": "Give piperacillin-tazobactam 4.5 g IV. Give 1 liter of lactated Ringer's IV. "
                   "Give oxygen by nasal cannula at 4 L/min.",
        "harmful": "Give furosemide 40 mg IV.",
        "excess": ["Give 1 liter of normal saline IV."] * 3,
        "start_stop": ("Start norepinephrine at 0.1 mcg/kg/min.", "Stop norepinephrine.", "norepinephrine"),
        "extra": "Start norepinephrine at 0.1 mcg/kg/min.",
        "duplicate": "Give piperacillin-tazobactam 4.5 g IV.",
    },
    "pulmonary_edema": {
        "correct": "Start nitroglycerin infusion at 100 mcg/min. Start BiPAP with IPAP 12 and EPAP 6 and "
                   "FiO2 50%. Give furosemide 40 mg IV.",
        "harmful": "Give 1 liter of normal saline IV.",
        "excess": ["Give furosemide 80 mg IV."] * 3,
        "start_stop": ("Start nitroglycerin infusion at 50 mcg/min.", "Stop the nitroglycerin.", "nitroglycerin"),
        "extra": "Give aspirin 300 mg PO.",
        "duplicate": "Give furosemide 40 mg IV.",
    },
    "acs": {
        "correct": "Give aspirin 300 mg PO. Give ticagrelor 180 mg PO. Give heparin 4000 units IV bolus. "
                   "Activate the cath lab.",
        "harmful": "Order a stress test.",
        "excess": ["Give aspirin 300 mg PO."] * 3,
        "start_stop": ("Start nitroglycerin infusion at 20 mcg/min.", "Stop the nitroglycerin.", "nitroglycerin"),
        "extra": "Give oxygen by nasal cannula at 2 L/min.",
        "duplicate": "Give aspirin 300 mg PO.",
    },
    "pulmonary_embolism": {
        "correct": "Give oxygen 15 L/min by non-rebreather mask. Give heparin 5000 units IV bolus. "
                   "Give alteplase 100 mg IV over 2 hours. Start norepinephrine at 0.05 mcg/kg/min.",
        "harmful": "Give 1 liter of normal saline IV. Give 1 liter of normal saline IV.",
        "excess": ["Give 1 liter of normal saline IV."] * 3,
        "start_stop": ("Start norepinephrine at 0.1 mcg/kg/min.", "Stop norepinephrine.", "norepinephrine"),
        "extra": "Call cardiology.",
        "duplicate": "Give heparin 5000 units IV bolus.",
    },
    "asthma": {
        "correct": "Give oxygen by nasal cannula at 2 L/min. Give albuterol 5 mg nebulized. Give ipratropium "
                   "0.5 mg nebulized. Give methylprednisolone 125 mg IV. Give magnesium sulfate 2 g IV over "
                   "20 minutes.",
        "harmful": "Give midazolam 5 mg IV.",
        "excess": ["Give albuterol 5 mg nebulized."] * 3,
        "start_stop": ("Start BiPAP with IPAP 12 and EPAP 6 and FiO2 50%.", "Stop BiPAP.", "niv"),
        "extra": "Start BiPAP with IPAP 12 and EPAP 6 and FiO2 50%.",
        "duplicate": "Give albuterol 5 mg nebulized.",
    },
    "gi_bleed": {
        "correct": "Give 1 liter of lactated Ringer's IV. Transfuse 2 units of packed red blood cells. "
                   "Give pantoprazole 80 mg IV. Call gastroenterology for urgent endoscopy.",
        "harmful": "Give heparin 5000 units IV bolus. Give aspirin 300 mg PO.",
        "excess": ["Give 2 liters of normal saline IV."] * 3,
        "start_stop": ("Start norepinephrine at 0.1 mcg/kg/min.", "Stop norepinephrine.", "norepinephrine"),
        "extra": "Start norepinephrine at 0.1 mcg/kg/min.",
        "duplicate": "Give pantoprazole 80 mg IV.",
    },
    "hypoglycemia": {
        "correct": "Give 50 mL of D50 IV.",
        "harmful": "Give 10 units of regular insulin IV.",
        "excess": ["Give 50 mL of D50 IV."] * 3,
        "start_stop": ("Start a dextrose 10% infusion at 100 mL/h.", "Stop the dextrose infusion.",
                       "dextrose_infusion_ml_h"),
        "extra": "Start a dextrose 10% infusion at 100 mL/h.",
        "duplicate": "Give 50 mL of D50 IV.",
    },
    "opioid": {
        "correct": "Ventilate with bag-valve-mask. Give naloxone 0.4 mg IV.",
        "harmful": "Give midazolam 2 mg IV.",
        "excess": ["Give naloxone 2 mg IV."] * 3,
        "start_stop": ("Give oxygen 15 L/min by non-rebreather mask.", "Stop the oxygen.", None),
        "extra": "Give oxygen 15 L/min by non-rebreather mask.",
        "duplicate": "Give naloxone 0.4 mg IV.",
    },
    "anaphylaxis": {
        "correct": "Give epinephrine 0.5 mg IM. Give 1 liter of normal saline IV. Give oxygen 15 L/min by "
                   "non-rebreather mask.",
        "harmful": "Give dexamethasone 10 mg IV. Give diphenhydramine 50 mg IV.",
        "excess": ["Give epinephrine 0.5 mg IM."] * 3,
        "start_stop": ("Start epinephrine infusion at 0.1 mcg/kg/min.", "Stop the epinephrine infusion.",
                       "epinephrine"),
        "extra": "Give methylprednisolone 125 mg IV.",
        "duplicate": "Give epinephrine 0.5 mg IM.",
    },
    "renal_colic": {
        "correct": "Give ketorolac 30 mg IV. Give morphine 4 mg IV. Give acetaminophen 1 g IV.",
        "harmful": "Discharge the patient home.",
        "excess": ["Give 1 liter of normal saline IV."] * 3,
        "start_stop": ("Start norepinephrine at 0.1 mcg/kg/min.", "Stop norepinephrine.", "norepinephrine"),
        "extra": "Give 1 liter of lactated Ringer's IV.",
        "duplicate": "Give acetaminophen 1 g IV.",
    },
    "bradycardia": {
        "correct": "Give calcium chloride 1 g IV. Give glucagon 5 mg IV. Call cardiology.",
        "harmful": "Give metoprolol 5 mg IV.",
        "excess": ["Give atropine 1 mg IV."] * 3,
        "start_stop": ("Start epinephrine infusion at 10 mcg/min.", "Stop the epinephrine infusion.", "epinephrine"),
        "extra": "Start transcutaneous pacing at 70 per minute and 80 mA.",
        "duplicate": "Call cardiology.",
    },
    "trauma": {
        "correct": "Apply a tourniquet to the right thigh. Transfuse 2 units of packed red blood cells. "
                   "Give tranexamic acid 1 g IV.",
        "harmful": "Give 2 liters of normal saline IV.",
        "excess": ["Transfuse 2 units of packed red blood cells."] * 3,
        "start_stop": ("Start norepinephrine at 0.1 mcg/kg/min.", "Stop norepinephrine.", "norepinephrine"),
        "extra": "Give 500 mL of lactated Ringer's IV.",
        "duplicate": "Transfuse 2 units of packed red blood cells.",
    },
}

#: Where a case's own correct management differs from its family's.
VARIANT_SCRIPTS = {
    "pulmonary_edema_75f": {"correct": "Start BiPAP with IPAP 12 and EPAP 6 and FiO2 50%. Give furosemide 40 mg IV. "
                                       "Start nitroglycerin infusion at 20 mcg/min."},
    "acs_66f_nonst": {"correct": "Give aspirin 300 mg PO. Give heparin 4000 units IV bolus. Call cardiology."},
    "acs_48m_wellens": {"correct": "Give aspirin 300 mg PO. Give heparin 4000 units IV bolus. Call cardiology."},
    "pulmonary_embolism_33f": {"correct": "Give oxygen by nasal cannula at 4 L/min. Give heparin 5000 units IV bolus."},
    "hypoglycemia_54m_thiamine": {"correct": "Place a new peripheral IV line. Give thiamine 100 mg IV. "
                                             "Give 50 mL of D50 IV."},
    "anaphylaxis_63m_betablocked": {"correct": "Give epinephrine 0.5 mg IM. Give 1 liter of normal saline IV. "
                                               "Give glucagon 5 mg IV. Give oxygen 15 L/min by non-rebreather mask."},
    "obstructive_pyelonephritis_58f": {"correct": "Give 1 liter of lactated Ringer's IV. Give ceftriaxone 2 g IV. "
                                                  "Call urology for urgent decompression."},
    "bradycardia_avb3_78f": {"correct": "Give atropine 1 mg IV. Start transcutaneous pacing at 70 per minute and "
                                        "80 mA. Call cardiology.",
                             "extra": "Start epinephrine infusion at 10 mcg/min."},
    "bradycardia_bb_54f": {"correct": "Give glucagon 5 mg IV. Give calcium chloride 1 g IV. Call cardiology."},
    "bradycardia_hyperk_63m": {"correct": "Give calcium gluconate 3 g IV. Give albuterol 10 mg nebulized. "
                                          "Call nephrology for urgent dialysis."},
    "trauma_hemothorax_41m": {"correct": "Insert a left chest tube. Transfuse 2 units of packed red blood cells. "
                                         "Call general surgery for thoracotomy.",
                              "duplicate": "Transfuse 2 units of packed red blood cells."},
}

#: A reasonable order the engine of no family models: whatever its fate, it may change nothing.
UNMODELLED_ORDER = "Give ondansetron 4 mg IV."

#: When the correct course is compared with omission: after the omitted course has had time to
#: show what it costs (a scripted fibrillation at 120 minutes, a slow drift elsewhere).
COMPARE_AT = {"acs": 125, "bradycardia": 75}
DEFAULT_COMPARE_AT = 60
#: Families whose correct course ends better than the patient arrived, and when.
RECOVERS_BY = {"pneumonia": 60, "pulmonary_edema": 30, "pulmonary_embolism": 60, "asthma": 30, "gi_bleed": 60,
               "hypoglycemia": 30, "opioid": 15, "anaphylaxis": 15, "bradycardia": 15, "trauma": 60,
               "acs": 150}
#: Families whose untreated course reaches an arrest within four hours, and the variants that do.
TERMINAL = {"opioid", "anaphylaxis", "bradycardia", "trauma"}
TERMINAL_VARIANTS = {"acs_54m_inferior", "acs_61m_posterior", "acs_52m_de_winter", "acs_70f_left_main"}
#: Excess whose harm the engine models, with the event or the sign that shows it.
EXCESS_HARM = {"opioid": "opioid_withdrawal", "pulmonary_embolism_61m": "rv_failure_from_volume"}
TOLERANCE = 6.0

_MENTAL = {"Alert": 0, "Confused": 4, "Agitated": 4, "Drowsy": 8, "Obtunded": 16, "Unresponsive": 24}


def scripts(variant):
    family = family_of(variant)
    return {**FAMILY_SCRIPTS[family], **VARIANT_SCRIPTS.get(variant, {})}


@lru_cache(maxsize=None)
def _families():
    from clinical_cases import FAMILIES
    return {variant["id"]: family for family, spec in FAMILIES.items() for variant in spec["variants"]}


def family_of(variant):
    return _families()[variant]


def variants():
    return sorted(_families())


def severity(state):
    """How unwell the patient is, from what the monitor shows; an arrest is the worst there is."""
    o = (state or {}).get("observable") or {}
    if o.get("pulse_present") is False:
        return 1000.0
    score = max(0.0, 90 - float(o.get("sbp") or 0)) + 2 * max(0.0, 92 - float(o.get("spo2") or 0))
    score += _MENTAL.get(str(o.get("mental_status")), 0)
    score += max(0.0, float(o.get("respiratory_rate") or 0) - 24) + max(0.0, 50 - float(o.get("hr") or 0))
    score += max(0.0, 70 - float(o.get("glucose_mg_dl") or 100)) / 2
    return round(score, 1)


class Encounter:
    """One case on the family branch of the page's order path, without Streamlit."""

    def __init__(self, variant, seed=SEED):
        import encounter_generator
        from test_curriculum_trajectories import load_engine
        family = family_of(variant)
        self.variant = variant
        self.state = encounter_generator.generate_encounter(
            LAUNCH[family], load_engine()["INITIAL_STATE"], seed=seed, family_id=family,
            variant_id=variant)["state"]
        self.arrival = deepcopy(self.state["observable"])
        self.ledger, self.entries, self._turns = [], [], 0

    def order(self, text):
        import event_provenance
        import observation_consistency
        import order_ledger
        import order_pipeline
        import time_semantics
        import trace_phase0
        from family_parser import parse_family_actions
        state = self.state
        submission = f"t{self._turns}"
        self._turns += 1
        minute = int(state.get("sim_time", 0) or 0)
        parsed = time_semantics.apply(text, parse_family_actions(text))
        parsed.setdefault("raw_text", text)
        turn = order_pipeline.open_turn(text, parsed, submission_id=submission, entry_point="free_text",
                                        minute=minute, ledger=self.ledger)
        result, split, run = self._execute(parsed, text)
        order_pipeline.settle(turn, result=result, run_actions=run, split=split, minute_before=minute,
                              minute_after=int(state.get("sim_time", 0) or 0),
                              terminal=bool(result.get("terminal_locked")))
        orders = order_ledger.snapshot(turn["orders"])
        events = event_provenance.attribute(deepcopy(result.get("events") or []), list(self.ledger) + orders)
        problems = order_pipeline.check(turn)
        order_pipeline.upsert(self.ledger, turn["orders"])
        observation = trace_phase0.observation_snapshot(state, result)
        entry = {
            "text": text, "decision_time_min": minute, "response_time_min": int(state.get("sim_time", 0) or 0),
            "executed": bool(result.get("executed")), "terminal_locked": bool(result.get("terminal_locked")),
            "clarification": result.get("clarification"), "orders": orders, "events": events,
            "interrupted": deepcopy(result.get("interrupted")), "observation_snapshot": observation,
            "limitations": trace_phase0.limitations(orders=orders, events=events, observation=observation,
                                                    terminal_locked=bool(result.get("terminal_locked"))),
            "ledger_problems": problems, "inconsistencies": observation_consistency.check(state),
            "action_summaries": deepcopy(result.get("action_summaries") or []),
            "observable": deepcopy(state.get("observable") or {}),
        }
        self.entries.append(entry)
        return entry

    def _execute(self, parsed, text):
        """The family branch of the page's ``execute_bundle`` (app.py), without the session."""
        import observation_consistency
        import order_ledger
        import order_pipeline
        import unexecuted_items
        import weight_based_doses
        from family_engine import execute_family_bundle
        from pending_family_orders import hold_incomplete_bundle
        state = self.state
        if unexecuted_items.plans_only(parsed):
            return ({"executed": False, "clarification": None, "action_summaries": [], "elapsed_min": 0,
                     "plans_only": True}, None, [])
        waiting = weight_based_doses.resolve(parsed, state)
        if observation_consistency.arrest_minute(state) is None:
            split = order_pipeline.split_bundle(state, parsed, text=text, weight_waiting=waiting)
            if split["held"] or split["unreadable"] or split["refused"]:
                run = split["run"]
                held = [action for action, *_ in split["held"]]
                result = None
                if run or not held:
                    runnable = {**{k: v for k, v in parsed.items() if k != "clarification"},
                                "actions": [order_ledger.strip_tags(a) for a in run]}
                    result = execute_family_bundle(state, runnable)
                    if result.get("executed") and run:
                        weight_based_doses.remember(state, runnable)
                if held and not waiting:
                    held_parsed = {**{k: v for k, v in parsed.items() if k != "clarification"},
                                   "actions": deepcopy(held), "recognized_future_actions": [], "future_details": []}
                    if not hold_incomplete_bundle(held_parsed, state):
                        split["no_pending"] = True
                question = split["question"] or "held"
                if result is None or not result.get("executed"):
                    result = {"executed": False, "action_summaries": [], "elapsed_min": 0, "reassess_delay": None,
                              "clarification": question}
                else:
                    result = {**result, "clarification": question, "partial": True}
                return result, split, run
        if waiting:
            return ({"executed": False, "action_summaries": [], "elapsed_min": 0, "clarification": "weight"},
                    None, list(parsed.get("actions") or []))
        result = execute_family_bundle(
            state, {**parsed, "actions": [order_ledger.strip_tags(a) for a in parsed.get("actions") or []]})
        if result.get("executed"):
            weight_based_doses.remember(state, parsed)
        return result, None, list(parsed.get("actions") or [])

    @property
    def minute(self):
        return int(self.state.get("sim_time", 0) or 0)

    @property
    def arrested(self):
        import observation_consistency
        return observation_consistency.arrest_minute(self.state) is not None

    def wait_until(self, minute, step=30):
        """Reassess until the clock reaches ``minute`` or the patient arrests (waits may stop early)."""
        guard = 0
        while self.minute < minute and not self.arrested and guard < 40:
            guard += 1
            entry = self.order(f"Reassess in {min(step, minute - self.minute)} minutes.")
            if not entry["executed"]:
                break
        return self


def _play(variant, turns, until=None):
    encounter = Encounter(variant)
    for text in turns:
        if encounter.arrested:
            break
        encounter.order(text)
    if until is not None:
        encounter.wait_until(until)
    return encounter


def _peak(encounter):
    """The worst severity the patient showed, from arrival to the end of the run."""
    worst = severity({"observable": encounter.arrival})
    for entry in encounter.entries:
        worst = max(worst, severity({"observable": entry["observable"]}))
    return worst


def _fates(encounter):
    return [(order["class"], order["fate"]) for entry in encounter.entries for order in entry["orders"]]


def _result(ok, detail):
    return {"ok": bool(ok), "detail": str(detail)}


@lru_cache(maxsize=None)
def battery(variant):
    """Every category of the request for one case: ``{category: {"ok": bool, "detail": str}}``."""
    import event_provenance
    import order_ledger
    import time_semantics
    family = family_of(variant)
    s = scripts(variant)
    compare_at = COMPARE_AT.get(family, DEFAULT_COMPARE_AT)
    out, runs = {}, {}

    correct = runs["A"] = _play(variant, [s["correct"] + " Reassess in 15 minutes."], until=compare_at)
    omission = runs["C"] = _play(variant, [], until=compare_at)
    a, c = severity(correct.state), severity(omission.state)
    executed = [fate for klass, fate in _fates(correct) if klass not in ("reassessment",)]
    out["A_correct_management"] = _result(
        all(fate == "EXECUTED" for fate in executed) and (a < c or (c < 1000 and a <= c + TOLERANCE)),
        f"every order executed: {executed}; severity at {compare_at} min {a} with the bundle vs {c} without")

    delayed = runs["B"] = _play(variant, ["Reassess in 30 minutes.", s["correct"] + " Reassess in 15 minutes."],
                                until=compare_at)
    # The worst the patient was on the way, not the state at one minute: a single dose given
    # later is fresher at any later minute, which says nothing about the delay.
    b_peak, a_peak = _peak(delayed), _peak(correct)
    out["B_delayed_management"] = _result(b_peak >= a_peak - TOLERANCE,
                                          f"worst severity up to {compare_at} min {b_peak} with the bundle at 30 vs "
                                          f"{a_peak} with it at 0")

    worse_or_equal = c >= severity(Encounter(variant).state) - TOLERANCE or omission.arrested
    out["C_omission"] = _result(
        worse_or_equal and not any(e["inconsistencies"] for e in omission.entries),
        f"untreated severity {c} at {omission.minute} min; arrival {severity(Encounter(variant).state)}")

    harmful = runs["D"] = _play(variant, [s["harmful"] + " Reassess in 15 minutes."], until=compare_at)
    d = severity(harmful.state)
    out["D_incorrect_treatment"] = _result(d >= c - TOLERANCE,
                                           f"severity {d} after the harmful order vs {c} without it")

    excess = runs["E"] = _play(variant, [text + " Reassess in 10 minutes." for text in s["excess"]], until=None)
    fates = _fates(excess)
    harm = EXCESS_HARM.get(variant) or EXCESS_HARM.get(family)
    shown = [e["kind"] for entry in excess.entries for e in entry["events"]]
    harm_ok = harm is None or harm in shown
    out["E_excessive_treatment"] = _result(
        all(fate in order_ledger.FATES for _, fate in fates) and harm_ok
        and not any(e["inconsistencies"] for e in excess.entries),
        f"fates {fates}; modelled harm {harm or 'none declared'} -> events {shown}")

    start, stop, key = s["start_stop"]
    switched = runs["F"] = _play(variant, [start + " Reassess in 10 minutes."])
    running = switched.state.get("family_state", {}).get(key) if key else None
    switched.order(stop + " Reassess in 10 minutes.")
    stopped = switched.state.get("family_state", {}).get(key) if key else None
    f_fates = _fates(switched)
    stop_ok = key is None or switched.arrested or (float(running or 0) > 0 and float(stopped or 0) == 0)
    out["F_start_stop"] = _result(stop_ok and all(f in order_ledger.FATES for _, f in f_fates)
                                  and not any(e["inconsistencies"] for e in switched.entries),
                                  f"{key or 'treatment'} {running} while running, {stopped} after the stop; {f_fates}")

    twice = runs["G"] = _play(variant, [s["duplicate"] + " Reassess in 5 minutes."] * 2)
    ids = [order["order_id"] for entry in twice.entries for order in entry["orders"]]
    g_fates = _fates(twice)
    out["G_duplicate_treatment"] = _result(
        len(ids) == len(set(ids)) and all(f in order_ledger.FATES for _, f in g_fates)
        and not any(e["inconsistencies"] for e in twice.entries),
        f"two submissions, {len(ids)} orders, each its own id and fate: {g_fates}")

    with_it = runs["H"] = _play(variant, [UNMODELLED_ORDER + " " + s["correct"] + " Reassess in 15 minutes."])
    without = _play(variant, [s["correct"] + " Reassess in 15 minutes."])
    unmodelled = [o for e in with_it.entries for o in e["orders"]
                  if "ondansetron" in str(o.get("span") or "").lower()]
    same = with_it.state["observable"] == without.state["observable"]
    out["H_unexpected_reasonable"] = _result(
        unmodelled and all(o["fate"] != "EXECUTED" for o in unmodelled) and same,
        f"ondansetron {[o['fate'] for o in unmodelled]}; the rest of the bundle ran; physiology identical "
        f"to the same bundle without it: {same}")

    waiting = _play(variant, ["Wait 20 minutes."])
    entry = waiting.entries[-1]
    stop_at = (entry.get("interrupted") or {}).get("minute")
    out["I_waiting"] = _result(
        waiting.minute == 20 or (stop_at is not None and stop_at == waiting.minute < 20
                                 and all(e["cause_class"] in event_provenance.CAUSE_CLASSES
                                         for e in entry["events"])),
        f"clock {waiting.minute} after 'Wait 20 minutes'"
        + (f" (stopped at {stop_at} by {entry['interrupted']['kind']})" if stop_at is not None else ""))

    look = _play(variant, ["Reassess."])
    explicit = _play(variant, ["Reassess in 15 minutes."])
    stopped_at = (explicit.entries[-1].get("interrupted") or {}).get("minute")
    out["J_reassessment"] = _result(
        look.minute == time_semantics.BEDSIDE_LOOK_MIN
        and (explicit.minute == 15 or (stopped_at is not None and stopped_at == explicit.minute)),
        f"'Reassess.' -> {look.minute} min (bedside look); 'Reassess in 15 minutes.' -> {explicit.minute} min")

    combined = runs["K"] = _play(variant, [s["correct"] + " " + s["extra"] + " Reassess in 15 minutes."])
    k_fates = [f for klass, f in _fates(combined) if klass != "reassessment"]
    out["K_combined_interventions"] = _result(
        all(f == "EXECUTED" for f in k_fates) and not any(e["inconsistencies"] for e in combined.entries),
        f"{k_fates}")

    if family in TERMINAL or variant in TERMINAL_VARIANTS:
        course = _play(variant, [], until=240)
        after = course.order("Give 1 liter of normal saline IV. Reassess in 10 minutes.") if course.arrested else None
        o = course.state["observable"]
        out["terminal_deterioration"] = _result(
            course.arrested and o.get("pulse_present") is False and not o.get("sbp")
            and after is not None and all(order["fate"] == "TERMINAL_NOT_EXECUTABLE"
                                          for order in after["orders"] if order["class"] != "reassessment")
            and any(item["kind"] == "resuscitation_not_modelled" for item in after["limitations"]),
            f"arrest at {course.minute} min untreated; orders after it "
            f"{[order['fate'] for order in after['orders']] if after else None}")
    else:
        course = _play(variant, [], until=240)
        out["terminal_deterioration"] = _result(
            not course.arrested and not any(e["inconsistencies"] for e in course.entries),
            f"no arrest is modelled untreated; at {course.minute} min severity {severity(course.state)}")

    if family == "acs" and variant not in TERMINAL_VARIANTS:
        # A non-ST-elevation infarct is not built to deteriorate in the first hours: it must not.
        steady = _play(variant, [s["correct"] + " Reassess in 15 minutes."], until=RECOVERS_BY[family])
        out["recovery"] = _result(not steady.arrested and severity(steady.state) <= severity(
            Encounter(variant).state) + TOLERANCE, f"severity {severity(steady.state)} at {steady.minute} min vs "
                                                   f"{severity(Encounter(variant).state)} on arrival (flat course)")
    elif family == "acs":
        # An infarct recovers by its artery: open, and no arrest after it (the wall it lost stays lost).
        recovering = _play(variant, [s["correct"] + " Reassess in 15 minutes."], until=RECOVERS_BY[family])
        opened = [e["minute"] for entry in recovering.entries for e in entry["events"] if e["kind"] == "reperfusion"]
        out["recovery"] = _result(bool(opened) and not recovering.arrested,
                                  f"artery open at {opened or None}; alive at {recovering.minute} min, severity "
                                  f"{severity(recovering.state)}")
    elif family in RECOVERS_BY:
        by = RECOVERS_BY[family]
        recovering = _play(variant, [s["correct"] + " Reassess in 15 minutes."], until=by)
        out["recovery"] = _result(not recovering.arrested and severity(recovering.state) <= severity(
            Encounter(variant).state), f"severity {severity(recovering.state)} at {recovering.minute} min vs "
                                       f"{severity(Encounter(variant).state)} on arrival")
    else:
        out["recovery"] = _result(True, "this case is not built to deteriorate or recover (flat course)")

    first = _play(variant, [s["correct"] + " Reassess in 15 minutes."])
    resumed = Encounter(variant)
    resumed.state = json.loads(json.dumps(first.state))
    resumed.ledger = json.loads(json.dumps(first.ledger))
    target = first.minute + 45
    for encounter in (first, resumed):
        encounter.wait_until(target)
    out["reload_resume"] = _result(
        first.state["observable"] == resumed.state["observable"] and first.minute == resumed.minute,
        f"a state written to JSON at minute 15 and read back runs on to the same patient at {first.minute} min")

    again = _play(variant, [s["correct"] + " Reassess in 15 minutes."], until=compare_at)
    out["deterministic_replay"] = _result(
        again.state["observable"] == correct.state["observable"]
        and [e["events"] for e in again.entries] == [e["events"] for e in correct.entries]
        and _fates(again) == _fates(correct), "the correct course played twice from the same seed")

    every = [entry for run in runs.values() for entry in run.entries]
    orphans = [order for entry in every for order in entry["orders"] if order["fate"] not in order_ledger.FATES]
    problems = [entry["ledger_problems"] for entry in every if entry["ledger_problems"]]
    out["action_ledger_completeness"] = _result(not orphans and not problems,
                                                f"{sum(len(e['orders']) for e in every)} orders; "
                                                f"without a fate {len(orphans)}; problems {problems}")

    events = [event for entry in every for event in entry["events"]]
    bad = [e for e in events if e.get("cause_class") not in event_provenance.CAUSE_CLASSES
           or e.get("preventability") not in event_provenance.PREVENTABILITY
           or e.get("severity") not in event_provenance.SEVERITY or not isinstance(e.get("minute"), int)]
    unnamed = [e for e in events if e.get("cause_class") == "RESIDENT_TREATMENT" and not e.get("source_order_ids")]
    out["event_provenance"] = _result(not bad and not unnamed,
                                      f"{len(events)} events: {sorted({e['kind'] for e in events})}; "
                                      f"without provenance {len(bad)}; treatment events without their orders "
                                      f"{len(unnamed)}")

    broken = [(entry["text"], entry["inconsistencies"]) for entry in every if entry["inconsistencies"]]
    out["observation_consistency"] = _result(not broken, broken or "no contradiction after any turn")

    out["trace_safety_guards"] = guards(variant)
    return out


def guards(variant):
    """Rules A and E on this case's own critical events, on a record built like the page's."""
    import evaluation_basis
    import rubric_screening as screening
    defined = evaluation_basis.resolve({}, variant)["events"]
    omissions = [event for event in defined if event["kind"] == "critical_omission"]
    if not omissions:
        return _result(True, "the case defines no critical omission")
    rows = []
    for event in omissions:
        start, end = event["window_min"]
        unread = {"order_id": "s:1000", "class": "unrecognized", "fate": "UNRECOGNIZED", "written_at_min": start,
                  "executed_at_min": None, "span": "zyxin 2 g", "canonical": "unrecognized"}

        def record(*orders, arrest_at=None):
            first = {"execution_status": "executed", "decision_time_min": start, "response_time_min": start,
                     "learner_input": "", "interpreted_action": [], "action_summaries": [], "orders": list(orders),
                     "events": [], "limitations": [], "observation_snapshot": {}}
            if arrest_at is not None:
                first["events"] = [{"kind": "cardiac_arrest", "label": "cardiac arrest", "minute": arrest_at,
                                    "cause_class": "NATURAL_DISEASE", "preventability": "PREVENTABLE",
                                    "severity": "terminal", "terminal": True}]
            last = {**first, "decision_time_min": end + 10, "response_time_min": end + 10, "orders": [], "events": []}
            return {"payload": {"session": {"management_trace": [first, last]}}}

        def status(rec):
            return {row["event_id"]: row for row in screening.screen_events(rec, variant)}[event["event_id"]]

        nothing, unread_row = status(record()), status(record(unread))
        arrest_row = status(record(arrest_at=start + 1)) if end > start + 1 else None
        rows.append((event["event_id"], nothing["status"], unread_row["status"],
                     arrest_row["status"] if arrest_row else None))
    ok = all(unread != "met" and arrest != "met" for _, _, unread, arrest in rows)
    return _result(ok, "; ".join(f"{eid}: nothing written -> {plain}, an unread order -> {unread}, an arrest "
                                 f"inside the window -> {arrest}" for eid, plain, unread, arrest in rows))


def summary(variant):
    """One row of the acceptance table."""
    import pilot_freeze
    from cognitive_catalog import BIAS_CHALLENGES
    family = family_of(variant)
    results = battery(variant)
    failed = sorted(name for name, result in results.items() if not result["ok"])
    declared = pilot_freeze.CASES[variant]
    return {
        "case": variant, "family": family,
        "challenges": sorted(ch for ch, spec in BIAS_CHALLENGES.items() if family in spec.get("families", ())),
        "engine": "family engine (bank case)",
        "battery": "PASS" if not failed else "FAIL: " + ", ".join(failed),
        "limitations": [item["id"] for item in pilot_freeze.limitations(variant)],
        "case_limits": len(pilot_freeze.declared_engine_limits(variant)),
        "affects_assessed": any(item["affects_assessed"] for item in pilot_freeze.limitations(variant)),
        "decision": declared["status"],
    }
