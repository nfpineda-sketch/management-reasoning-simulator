"""What a bolus of crystalloid does, and what it stops doing.

Faculty decision 4 of 2026-09-21, from the full bank review. In the inferior
infarct with right ventricular involvement, 500 mL of saline did nothing,
because the only crystalloid the coronary family modelled was the one that
rescues a nitrate-induced fall. The decision was explicit:

  * the benefit belongs to the haemodynamic state, not to having been given
    nitroglycerin first;
  * it depends on how full the patient already is and on which ventricle is
    failing, so a preload-dependent right ventricle answers and a failing left
    one answers much less;
  * it has diminishing returns, and past what the patient tolerates the volume
    buys congestion and costs output;
  * none of it replaces the reperfusion that is still owed.

The teaching sentence is "a careful bolus, then reassess tolerance and adapt",
never "right ventricular infarct, therefore unlimited volume".
"""

# Circulation burden relieved per millilitre, at full responsiveness.
GAIN_PER_ML = .00040
# Millilitres this patient tolerates before the volume turns against them.
TOLERANCE_ML = {"rv": 1600, "lv": 700, "other": 1000}
# Past tolerance, each further millilitre costs lung and gives nothing back.
CONGESTION_PER_ML_OVER = .00035
# How much of the low-output burden is preload at all, by what is failing.
PRELOAD_SHARE = {"rv": 1.0, "lv": .25, "other": .6}


def profile(spec):
    """Which ventricle this case is about."""
    if (spec or {}).get("rv_involvement"):
        return "rv"
    if (spec or {}).get("territory") in {"anterior", "left_main", "lateral"}:
        return "lv"
    return "other"


def responsiveness(f, spec):
    """What is left of the response, after everything already given."""
    given = float(f.get("fluid_delivered_ml", 0.0))
    return max(0.0, 1.0 - given / TOLERANCE_ML[profile(spec)])


def step(state, spec, fluid_ml):
    """One minute of crystalloid in a coronary patient; returns an event or None."""
    if fluid_ml <= 0:
        return None
    f = state["family_state"]
    kind = profile(spec)
    share = PRELOAD_SHARE[kind]
    left = responsiveness(f, spec)
    f["circulation"] -= fluid_ml * GAIN_PER_ML * share * left
    given = float(f.get("fluid_delivered_ml", 0.0))
    over = given - TOLERANCE_ML[kind]
    if over <= 0:
        return None
    # Past tolerance the volume is in the lung, not in the stroke volume.
    f["lung"] = float(f.get("lung", 1.0)) + fluid_ml * CONGESTION_PER_ML_OVER
    if f.get("volume_overload_reported"):
        return None
    f["volume_overload_reported"] = True
    return (f"{given:.0f} mL of crystalloid is past what this ventricle is carrying: the pressure has "
            "stopped answering and the lungs are starting to. Reassess tolerance before the next bolus.")
