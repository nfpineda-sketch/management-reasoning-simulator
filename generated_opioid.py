"""Opioid toxicity inside a generated case (faculty decision 2026-09-20).

Fifth and last mechanism of the first pass. The case declares
``engine.opioid_toxidrome``; the gate refuses what the resident cannot discover;
the shared opioid_reversal module does the work, and the adapter reads it as a
change in breathing, in the rate and pressure of withdrawal, and in the arrest
that follows apnoea nobody supports.
"""
import opioid_reversal

MECHANISM_ACTIONS = frozenset({"naloxone", "naloxone_infusion", "bag_mask"})
REVERSED_RR = 14.0
REVERSED_SPO2 = 97.0


def spec(state):
    case = state.get("encounter_spec", {}).get("clinical_case", {})
    return case.get("engine", {}).get("opioid_toxidrome")


def step(state):
    """One minute of opioid and antidote. Returns an event text or None."""
    declaration = spec(state)
    if declaration is None:
        return None
    engine = state["encounter_spec"]["clinical_case"]["engine"]
    engine["recurrence_risk"] = bool(declaration.get("long_acting"))
    f = state["family_state"]
    f.setdefault("opioid_arrival_rr", float(state["observable"].get("respiratory_rate", 8)))
    f.setdefault("opioid_arrival_spo2", float(state["observable"].get("spo2", 85)))
    return opioid_reversal.step(state)


def generated_effects(state):
    """(sbp, dbp, hr, spo2, respiratory_rate) since arrival."""
    if spec(state) is None:
        return (0.0,) * 5
    f = state["family_state"]
    arrival_rr = float(f.get("opioid_arrival_rr", 8))
    arrival_spo2 = float(f.get("opioid_arrival_spo2", 85))
    suppression = opioid_reversal.suppression(f)
    if f.get("bag_mask") or f.get("invasive"):
        rr, spo2 = 12.0, 96.0
    else:
        rr = REVERSED_RR - (REVERSED_RR - arrival_rr) * suppression
        spo2 = REVERSED_SPO2 - (REVERSED_SPO2 - arrival_spo2) * suppression
    sbp = dbp = hr = 0.0
    excess = min(1.5, opioid_reversal.withdrawal(f))
    if excess:
        hr += opioid_reversal.WITHDRAWAL_HR * excess
        sbp += opioid_reversal.WITHDRAWAL_SBP * excess
        dbp += opioid_reversal.WITHDRAWAL_SBP * .6 * excess
        rr += opioid_reversal.WITHDRAWAL_RR * excess
    return sbp, dbp, hr, spo2 - arrival_spo2, rr - arrival_rr


def mental_status(state):
    """Awake, drowsy, obtunded or agitated, from the balance of drug and antidote."""
    if spec(state) is None:
        return None
    f = state["family_state"]
    if opioid_reversal.withdrawal(f) > 0:
        return "Agitated"
    suppression = opioid_reversal.suppression(f)
    if suppression < .2:
        return "Alert"
    if suppression < .55:
        return "Drowsy"
    return "Obtunded"


def arrested(state):
    return spec(state) is not None and state["family_state"].get("arrest_at") is not None
