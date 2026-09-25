"""Hypoglycaemia beyond the ampoule of dextrose (faculty decisions 2026-09-20).

The bank had one treatment: intravenous dextrose. The faculty asked for the rest
of the bedside: octreotide as the specific treatment of sulfonylurea
hypoglycaemia, so that repeated ampoules stop being the only answer; glucagon
when there is no line, slower and smaller and limited by the glycogen it has to
mobilise; oral carbohydrate once the patient can protect their airway; a 10%
dextrose infusion instead of boluses alone; thiamine where it matters; and a
consequence for neuroglycopenia that is left long enough.

Teaching magnitudes pending faculty review, and only the bank hypoglycaemia
family uses them.
"""
import math

# The mechanism's version, recorded with every frozen evaluation basis of a
# catalogued case; a change of behaviour raises it. 1.0 is the mechanism as
# faculty decision 8 (2026-09-21) left it: a line that is not in the vein holds
# back a dextrose bolus given through it, and nothing else (the scope that decision
# set; whether to widen it is pending, docs/HIPOGLICEMIA_DECISIONES_PENDIENTES.md).
VERSION = "1.0"

# Sulfonylurea: the recurrence the ampoule cannot fix.
OCTREOTIDE_ONSET_MIN = 15
OCTREOTIDE_DURATION_MIN = 360
OCTREOTIDE_MIN_DOSE_MG = .025          # 25 mcg

# Glucagon mobilises glycogen: slower, smaller, and it runs out.
GLUCAGON_ONSET_MIN = 10
GLUCAGON_DURATION_MIN = 25
GLUCAGON_MG_DL_PER_MIN = 1.6           # about 40 mg/dL from the first dose
GLYCOGEN_SECOND_DOSE_SHARE = .5        # a second dose mobilises half as much
GLYCOGEN_EXHAUSTED_AFTER = 2
# Glucagon works on the liver's glycogen, so a patient who has not eaten for days
# has little for it to mobilise (faculty decision 8, 2026-09-21). The case
# declares the reserve; everyone else has a full one.
DEPLETED_GLYCOGEN_SHARE = .3

# Oral carbohydrate: only for an airway the patient can protect.
ORAL_ONSET_MIN = 5
ORAL_DURATION_MIN = 25
ORAL_MG_DL_PER_MIN = 1.2
ORAL_SAFE_MENTAL = {"Alert"}

# A 10% infusion, in grams per minute: 100 mL/h is 10 g/h.
INFUSION_G_PER_ML = .1

# Overcorrection (faculty decision 2026-09-20). Hyperglycaemia above 300 mg/dL has
# little acute repercussion, so the number itself is not punished. What is punished is
# what overcorrection provokes in a patient whose pancreas works: an insulin response
# that takes the glucose back down, faster than it fell before.
REBOUND_GLUCOSE = 200          # a doubled ampoule reaches this; a single one does not
REBOUND_DELAY_MIN = 30
REBOUND_FALL_PER_MIN = .8      # enough that the rebound is reached inside an encounter
REBOUND_ENDS_BELOW = 100
REBOUND_TEXT = ("The correction overshot: a glucose above 200 mg/dL in a patient with a working pancreas provoked an "
                "insulin response, and the glucose is now falling faster than it fell before. Overcorrection buys the "
                "next hypoglycaemia, not safety.")

# Neuroglycopenia that is left too long.
SEIZURE_GLUCOSE = 40
SEIZURE_AFTER_MIN = 20
POST_ICTAL_MIN = 10

# Consciousness read from the glucose, highest threshold first: at or above
# each value the patient is in that state, and below the last one they are
# unresponsive. The bank engine surfaces it every minute and the hypoglycaemia
# catalogue derives its severity bands from it, so the two cannot drift apart.
# Teaching magnitudes the faculty reviewed on 2026-09-20
# (docs/HYPOGLYCEMIA_MAGNITUDES.md): parameters of the simulator, never
# criteria a resident is assessed against.
CONSCIOUSNESS_BY_GLUCOSE = ((70, "Alert"), (45, "Drowsy"), (25, "Obtunded"))
BELOW_CONSCIOUSNESS_THRESHOLDS = "Unresponsive"

# What makes the mechanism discoverable, for every engine that runs it: the gate
# of generated cases and the hypoglycaemia catalogue read these same patterns.
HYPOGLYCAEMIA_MG_DL = 70
SULFONYLUREA_NAMES = r"\b(?:sulfonylurea|sulfonilurea|glibenclamide|glyburide|glipizide|gliclazide|glimepiride)\b"
ALCOHOL_OR_STARVATION = (r"\balcohol\w*\b", r"\bdrink\w+ (?:heavily|daily)\b", r"\bmalnourish\w*\b",
                         r"\b(?:eaten|eating) (?:almost )?nothing\b", r"\bpoor (?:oral )?intake\b",
                         r"\bdesnutri\w*\b")


def consciousness(glucose):
    """The mental state the engine shows for a glucose, before any seizure."""
    for threshold, state in CONSCIOUSNESS_BY_GLUCOSE:
        if glucose >= threshold:
            return state
    return BELOW_CONSCIOUSNESS_THRESHOLDS

# Thiamine. Faculty decision 8 of 2026-09-21 retired the established
# encephalopathy this case used to produce: glucose that reaches the patient
# corrects the hypoglycaemia and the consciousness with it, thiamine or no
# thiamine. Thiamine stays as the second objective — recognising who needs it
# and starting it in time — and it neither wakes a patient nor, by its absence,
# deteriorates one. What the case teaches instead is that an ordered dose and a
# received dose are not the same thing.
#
# A line that is not in the vein: the glucose is ordered, and this much of it
# arrives. The state is the case's own and it is visible at the bedside, never
# hidden and never random.
FAILED_ACCESS_SHARE = .15
FAILED_ACCESS_TEXT = ("The dextrose does not run: the forearm swells around the cannula and the infusion slows to a "
                      "stop. What was ordered is not what reached the patient.")
NEW_ACCESS_TEXT = "The new line runs freely. What is given now reaches the circulation."


def profile(state):
    case = state.get("encounter_spec", {}).get("clinical_case", {}).get("engine", {})
    return {"sulfonylurea": bool(case.get("recurrence_risk")),
            "thiamine_deficient": bool(case.get("thiamine_deficient")),
            "endogenous_insulin": bool(case.get("endogenous_insulin"))}


def octreotide_active(f):
    given = f.get("octreotide_at")
    return given is not None and given + OCTREOTIDE_ONSET_MIN <= f["elapsed"] <= given + OCTREOTIDE_DURATION_MIN


def drift_per_min(f, state):
    """How fast the glucose falls on its own, before any treatment."""
    own = profile(state)
    drift = -.08 if (not own["sulfonylurea"] or octreotide_active(f)) else -.6
    return drift - rebound_fall(f)


def rebound_fall(f):
    """The extra fall an overshoot bought, once the insulin response has started."""
    started = f.get("rebound_at")
    if started is None or f["elapsed"] - started < REBOUND_DELAY_MIN:
        return 0.0
    return 0.0 if f.get("glucose", 0) <= REBOUND_ENDS_BELOW else REBOUND_FALL_PER_MIN


def _window_gain(f, key, onset, duration, per_min, scale=1.0):
    given = f.get(key)
    if given is None:
        return 0.0
    since = f["elapsed"] - given
    return per_min * scale if onset <= since <= onset + duration else 0.0


def treatment_gain(f):
    """Glucose added this minute by glucagon, oral carbohydrate and the infusion."""
    doses = f.get("glucagon_doses", 0)
    scale = 1.0 if doses <= 1 else (GLYCOGEN_SECOND_DOSE_SHARE if doses < GLYCOGEN_EXHAUSTED_AFTER + 1 else 0.0)
    scale *= DEPLETED_GLYCOGEN_SHARE if f.get("glycogen_depleted") else 1.0
    gain = _window_gain(f, "glucagon_at", GLUCAGON_ONSET_MIN, GLUCAGON_DURATION_MIN, GLUCAGON_MG_DL_PER_MIN, scale)
    gain += _window_gain(f, "oral_carbohydrate_at", ORAL_ONSET_MIN, ORAL_DURATION_MIN, ORAL_MG_DL_PER_MIN)
    rate = float(f.get("dextrose_infusion_ml_h") or 0)
    if rate:
        # Grams per minute, at the engine's 4 mg/dL per gram.
        gain += rate / 60 * INFUSION_G_PER_ML * 4
    return gain


def step(state):
    """One minute of glucose and of the brain that depends on it."""
    f = state["family_state"]
    f["glucose"] += drift_per_min(f, state) + treatment_gain(f)
    if f["glucose"] < SEIZURE_GLUCOSE:
        f["neuroglycopenia_min"] = f.get("neuroglycopenia_min", 0.0) + 1
    else:
        f["neuroglycopenia_min"] = 0.0
    if (profile(state)["endogenous_insulin"] and f.get("rebound_at") is None
            and f["glucose"] > REBOUND_GLUCOSE):
        f["rebound_at"] = f["elapsed"]
        return REBOUND_TEXT
    if f.get("seizure_at") is None and f["neuroglycopenia_min"] >= SEIZURE_AFTER_MIN:
        f["seizure_at"] = f["elapsed"]
        return ("Generalized tonic-clonic seizure after twenty minutes below 40 mg/dL. It stops on its own and "
                "leaves the patient post-ictal; the treatment is the glucose, not an anticonvulsant.")
    return None


def post_ictal(f):
    seizure = f.get("seizure_at")
    return seizure is not None and f["elapsed"] - seizure <= POST_ICTAL_MIN


def delivered_share(f, route):
    """The share of an intravenous dose that actually reaches the circulation."""
    if route in {"IV", "IO"} and f.get("iv_access_failed"):
        return FAILED_ACCESS_SHARE
    return 1.0
