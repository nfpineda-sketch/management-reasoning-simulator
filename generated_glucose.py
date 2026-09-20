"""Hypoglycaemia inside a generated case (faculty decision 2026-09-20).

Fourth mechanism, same shape as the three before it. The case declares
``engine.glucose_failure``; the gate refuses what the resident cannot discover;
the shared glucose_rescue module does the work, and the adapter reads its result
as a change in the glucose the monitor shows and in the brain that depends on it.

What the declaration buys: the glucose that falls on its own, faster with a
sulfonylurea until octreotide stops it; the ampoule, the glucagon, the oral
carbohydrate and the 10% infusion; the seizure of neuroglycopenia left too long;
and the encephalopathy of glucose given to a thiamine-depleted brain.
"""
import glucose_rescue

MECHANISM_ACTIONS = frozenset({"dextrose", "octreotide", "glucagon", "thiamine",
                               "oral_carbohydrate", "dextrose_infusion"})
DEXTROSE_G_PER_MIN = 10.0
MG_DL_PER_G = 4.0


def spec(state):
    case = state.get("encounter_spec", {}).get("clinical_case", {})
    return case.get("engine", {}).get("glucose_failure")


def _profile(state):
    """glucose_rescue reads the case engine, so mirror the declaration onto it."""
    declaration = spec(state) or {}
    engine = state["encounter_spec"]["clinical_case"]["engine"]
    engine["recurrence_risk"] = bool(declaration.get("sulfonylurea"))
    engine["thiamine_deficient"] = bool(declaration.get("thiamine_deficient"))


def step(state):
    """One minute of glucose. Returns an event text or None."""
    if spec(state) is None:
        return None
    _profile(state)
    f = state["family_state"]
    f.setdefault("glucose_reference", float(f.get("glucose", 100)))
    # The intravenous ampoule is delivered here, as the bank engine's minute does.
    given = min(DEXTROSE_G_PER_MIN, float(f.get("dextrose_g") or 0))
    if given:
        f["dextrose_g"] -= given
        f["glucose"] = min(350, f["glucose"] + given * MG_DL_PER_G)
    return glucose_rescue.step(state)


def mental_status(state):
    """What the glucose leaves of the brain, or None when the mechanism is silent."""
    if spec(state) is None:
        return None
    f = state["family_state"]
    if glucose_rescue.post_ictal(f):
        return "Unresponsive"
    glucose = float(f.get("glucose", 100))
    if glucose < 25:
        return "Unresponsive"
    if glucose < 45:
        return "Obtunded"
    if glucose < 70:
        return "Drowsy"
    return "Confused" if glucose_rescue.wernicke_share(f) > .35 else None


def generated_effects(state):
    """The change in the glucose the monitor shows, since arrival."""
    if spec(state) is None:
        return 0.0
    f = state["family_state"]
    return float(f.get("glucose", 0)) - float(f.get("glucose_reference", f.get("glucose", 0)))
