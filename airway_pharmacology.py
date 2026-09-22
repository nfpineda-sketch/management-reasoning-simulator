"""Induction, paralysis and maintenance sedation, told apart.

Faculty decision 11 of 2026-09-21, from the full bank review. Sedation already
worked; what came after it did not exist. The decision was explicit that the
three things a rapid sequence does are not one thing:

  * **consciousness** is what the hypnotic takes;
  * **pain** is what the analgesic takes, and neither hypnotic takes it;
  * **movement** is what the blocker takes, and it takes nothing else.

So an unmoving patient is not a sedated patient. A block outlasting its hypnotic
is a paralysed, aware patient, which the record has to say out loud. And a
paralysed patient who is not being ventilated is apnoeic: the support that is
actually established decides whether the encounter stays stable, not the fact
that the word "intubate" was written.

Nothing here touches bronchial resistance. A block can improve synchrony where a
patient's own efforts were fighting the ventilator, and the trapped gas then
falls through the mechanics, not because the drug was given.
"""

# Neuromuscular blockers: onset, and how long movement stays gone at a
# reference dose. Duration scales with the dose actually given.
BLOCKERS = {
    "rocuronium": {"reference_mg_per_kg": 1.0, "onset_min": 1, "duration_min": 45},
    "succinylcholine": {"reference_mg_per_kg": 1.5, "onset_min": 1, "duration_min": 8},
    "vecuronium": {"reference_mg_per_kg": .1, "onset_min": 2, "duration_min": 40},
    "cisatracurium": {"reference_mg_per_kg": .15, "onset_min": 3, "duration_min": 50},
}
MAX_DURATION_FACTOR = 2.0   # a double dose does not last four times as long

# Maintenance sedation. A running infusion holds consciousness where the
# induction left it; stopping it lets the patient come back over this time.
INFUSION_OFFSET_MIN = 12
# Sedation is not analgesia: only the opioid infusion touches pain.
ANALGESIC_INFUSIONS = frozenset({"fentanyl", "morphine", "remifentanil"})
# Systolic pressure an infusion costs at its reference rate. Propofol is the one
# that reliably costs pressure; it is not inevitable, and it scales with rate.
INFUSION_SBP_PER_REFERENCE = {"propofol": 12.0, "midazolam": 6.0,
                              "dexmedetomidine": 8.0, "fentanyl": 3.0, "ketamine": 0.0}
REFERENCE_RATE_MG_KG_H = {"propofol": 3.0, "midazolam": .1, "dexmedetomidine": .001,
                          "fentanyl": .002, "ketamine": 1.0}

APNOEA_TO_ARREST_MIN = 8    # a paralysed patient nobody is ventilating
ARREST_TEXT = ("Cardiac arrest after {minutes} minutes of paralysis without ventilation. The blocker "
               "removed every breath the patient had; the ventilation that replaces them was never established.")
UNSEDATED_TEXT = ("The blocker is still working and the hypnotic is not: the patient cannot move and is not "
                  "sedated. Nothing on the monitor will say so.")


def blocker_duration(agent, dose_mg, dose_mg_per_kg, weight_kg):
    spec = BLOCKERS.get(agent) or BLOCKERS["rocuronium"]
    per_kg = dose_mg_per_kg if dose_mg_per_kg else (float(dose_mg or 0) / max(1.0, weight_kg))
    share = min(MAX_DURATION_FACTOR, per_kg / spec["reference_mg_per_kg"]) if per_kg else 0.0
    return spec["onset_min"], spec["duration_min"] * share


def paralysed(f):
    until = f.get("paralysis_until")
    return until is not None and f.get("elapsed", 0) < until


def infusion_sedating(f):
    infusion = f.get("sedation_infusion") or {}
    if not infusion.get("rate"):
        return False
    return infusion.get("agent") not in ANALGESIC_INFUSIONS


def infusion_pressure_cost(f, weight_kg):
    """Systolic mmHg the running sedation is costing, scaled by its rate."""
    infusion = f.get("sedation_infusion") or {}
    agent, rate = infusion.get("agent"), float(infusion.get("rate") or 0)
    if not rate or agent not in INFUSION_SBP_PER_REFERENCE:
        return 0.0
    units = str(infusion.get("units") or "mg/kg/h")
    per_kg_h = rate if units.startswith("mg/kg/h") else rate * 60 / max(1.0, weight_kg) if units.endswith("/min") else rate / max(1.0, weight_kg)
    reference = REFERENCE_RATE_MG_KG_H.get(agent) or 1.0
    return INFUSION_SBP_PER_REFERENCE[agent] * min(2.0, per_kg_h / reference)


def step(state):
    """One minute of paralysis without ventilation; returns an event or None."""
    f = state["family_state"]
    if not paralysed(f):
        f["paralysis_apnoea_min"] = 0
        return None
    supported = bool(f.get("invasive") or f.get("bag_mask"))
    if supported:
        f["paralysis_apnoea_min"] = 0
    else:
        f["paralysis_apnoea_min"] = int(f.get("paralysis_apnoea_min", 0)) + 1
    if not f.get("paralysis_unsedated_reported") and not sedated_now(f):
        f["paralysis_unsedated_reported"] = True
        return UNSEDATED_TEXT
    if f.get("arrest_at") is None and f["paralysis_apnoea_min"] >= APNOEA_TO_ARREST_MIN:
        f["arrest_at"] = f["elapsed"]
        return ARREST_TEXT.format(minutes=APNOEA_TO_ARREST_MIN)
    return None


def sedated_now(f, induction_window_min=45):
    given = f.get("sedation_at")
    if given is not None and f.get("elapsed", 0) - given <= induction_window_min:
        return True
    return infusion_sedating(f)


def mental_and_effort(f):
    """What to report for a ventilated patient: (mental status, visible effort)."""
    if sedated_now(f):
        return "Sedated", "Ventilator-supported"
    if paralysed(f):
        return "Paralysed, sedation not maintained", "Ventilator-supported, no spontaneous effort"
    return "Awake and fighting the ventilator", "Ventilator dyssynchrony"
