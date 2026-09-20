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

# Thiamine: glucose given to a depleted brain without it.
WERNICKE_WINDOW_MIN = 30               # thiamine given within this of the glucose prevents it
THIAMINE_RECOVERY_TAU_MIN = 30.0
WERNICKE_TEXT = ("Confusion persists with nystagmus and an unsteady gaze although the glucose is now normal: "
                 "glucose was given to a thiamine-depleted brain. Thiamine is the missing treatment.")


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
    if profile(state)["thiamine_deficient"] and f.get("glucose_given_at") is not None:
        thiamine = f.get("thiamine_at")
        in_time = thiamine is not None and thiamine - f["glucose_given_at"] <= WERNICKE_WINDOW_MIN
        if not in_time and not f.get("wernicke_at"):
            f["wernicke_at"] = f["elapsed"]
            return WERNICKE_TEXT
    return None


def post_ictal(f):
    seizure = f.get("seizure_at")
    return seizure is not None and f["elapsed"] - seizure <= POST_ICTAL_MIN


def wernicke_share(f):
    """How much of the encephalopathy is still present: 1.0 until thiamine is given."""
    if f.get("wernicke_at") is None:
        return 0.0
    thiamine = f.get("thiamine_at")
    if thiamine is None or thiamine < f["wernicke_at"]:
        return 1.0
    return math.exp(-(f["elapsed"] - thiamine) / THIAMINE_RECOVERY_TAU_MIN)
