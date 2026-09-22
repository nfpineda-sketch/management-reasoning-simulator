"""Urine: produced by the kidney, measured by whoever is measuring it.

Faculty decision 12 of 2026-09-21, from the full bank review. Furosemide was
modelled and yet nothing happened in the record: no diuresis, no volume, not a
line, so the resident could not tell whether the order had done anything. The
decision keeps three things apart:

  * **administration**, which is recorded when the order runs;
  * **production**, which depends on renal perfusion, the dose, the route and
    what the kidney was like before, and which can be adequate, poor or absent;
  * **measurement**, which only exists when somebody is measuring. Without a
    collection the record says the diuresis is not quantified, and a patient who
    simply passes urine is reported without inventing a number.

The response is not conditional on the oedema clearing first: they are related
and they move on different clocks.
"""

# Millilitres per kilogram per hour at normal renal perfusion.
BASELINE_ML_KG_H = 1.0
# Perfusion closes the kidney down: this is the share of baseline output left
# per unit of circulation burden, floored at anuria.
OUTPUT_PER_BURDEN = 1.6
FUROSEMIDE_ONSET_MIN = 20          # IV; the oral route is slower
FUROSEMIDE_ORAL_EXTRA_MIN = 25
FUROSEMIDE_PEAK_ML_PER_MG = 6.0    # millilitres per mg at full responsiveness
FUROSEMIDE_TAU_MIN = 90.0          # and it fades over an hour and a half
# What blunts the response: a creatinine that says the kidney is not well, and
# a kidney that is not being perfused.
CREATININE_HALF_RESPONSE = 2.2
PRIOR_EXPOSURE_FACTOR = .7         # each previous dose buys less than the last
REPORT_EVERY_MIN = 30              # how often a collection is read out
VOID_ML = 250                      # the volume a patient notices without a catheter


def _responsiveness(state):
    f = state["family_state"]
    creatinine = float((state.get("encounter_spec", {}).get("clinical_case", {})
                        .get("investigations", {}).get("basic_labs", {})
                        .get("result", {}) or {}).get("creatinine_mg_dl") or 1.0)
    renal = CREATININE_HALF_RESPONSE / (CREATININE_HALF_RESPONSE + max(0.0, creatinine - 1.0))
    perfusion = max(0.0, 1 - OUTPUT_PER_BURDEN * max(0.0, float(f.get("circulation", 1.0)) - 1.0))
    return max(0.0, renal * perfusion)


def rate_ml_per_min(state):
    """Urine the kidney is making this minute."""
    f = state["family_state"]
    weight = float((state.get("encounter_spec", {}).get("clinical_case", {})
                    .get("patient", {}).get("weight_kg") or 70) or 70)
    perfusion = max(0.0, 1 - OUTPUT_PER_BURDEN * max(0.0, float(f.get("circulation", 1.0)) - 1.0))
    base = BASELINE_ML_KG_H * weight / 60 * perfusion
    extra = 0.0
    for dose in f.get("furosemide_doses", ()):
        onset = FUROSEMIDE_ONSET_MIN + (FUROSEMIDE_ORAL_EXTRA_MIN if dose.get("route") == "PO" else 0)
        since = f["elapsed"] - dose["at"] - onset
        if since < 0:
            continue
        peak = FUROSEMIDE_PEAK_ML_PER_MG * dose["mg"] * dose["responsiveness"] * (
            PRIOR_EXPOSURE_FACTOR ** dose["index"])
        extra += peak / FUROSEMIDE_TAU_MIN * 2.718281828 ** (-since / FUROSEMIDE_TAU_MIN)
    return max(0.0, base + extra)


def record_dose(state, mg, route):
    f = state["family_state"]
    given = f.setdefault("furosemide_doses", [])
    given.append({"at": f["elapsed"], "mg": float(mg or 0), "route": route or "IV",
                  "index": len(given), "responsiveness": _responsiveness(state)})


def step(state):
    """One minute of urine, and the reading of it when somebody is collecting."""
    f = state["family_state"]
    produced = rate_ml_per_min(state)
    f["urine_ml"] = float(f.get("urine_ml", 0.0)) + produced
    f["urine_since_report_ml"] = float(f.get("urine_since_report_ml", 0.0)) + produced
    f["urine_report_min"] = int(f.get("urine_report_min", 0)) + 1
    if not f.get("urinary_catheter"):
        # No collection: the patient passes urine, and nobody measured it.
        if f["urine_since_report_ml"] >= VOID_ML:
            f["urine_since_report_ml"] = 0.0
            f["urine_report_min"] = 0
            return ("The patient passes urine. Nobody is collecting it, so the volume is not quantified.")
        return None
    if f["urine_report_min"] < REPORT_EVERY_MIN:
        return None
    volume, minutes = f["urine_since_report_ml"], f["urine_report_min"]
    # The minute counter is advanced before the clock is, so the interval that
    # has just finished ends at the minute this event is stamped with.
    ended = int(state.get("sim_time", 0)) + 1
    started = max(0, ended - minutes)
    f["urine_since_report_ml"] = 0.0
    f["urine_report_min"] = 0
    return (f"{volume:.0f} mL of urine collected between minute {started} and minute "
            f"{ended} (about {volume * 60 / max(1, minutes):.0f} mL/h).")


def balance(state):
    """What went in and what came out, for the record."""
    f = state["family_state"]
    given = float(f.get("fluid_delivered_ml", 0.0)) + float(f.get("blood_delivered_units", 0.0)) * 300
    return {"given_ml": round(given), "urine_ml": round(float(f.get("urine_ml", 0.0))),
            "quantified": bool(f.get("urinary_catheter"))}
