"""Atropine and transcutaneous pacing for the block an inferior infarct makes.

Faculty decision 5 of 2026-09-21, from the full bank review. The complete
atrioventricular block appeared on its own at forty-five minutes and the
resident had nothing to offer: neither drug existed. The decision was explicit
about what the case must teach, so the model keeps three things apart:

  * **where the block is.** A nodal block, which is what an inferior infarct
    makes, may respond to atropine, and may not. An infranodal block does not:
    the atrial rate rises and the ventricle ignores it.
  * **electrical capture and mechanical capture.** Choosing a rate is not
    pacing. The output current has to reach this patient's threshold, and the
    resident still has to confirm a pulse and a pressure, not a monitor trace.
  * **the rate is not the whole shock.** Restoring the rate gives back the
    output the bradycardia was costing, and nothing else. The infarcting
    ventricle, the right ventricle and the owed reperfusion all remain.
"""

ATROPINE_DOSE_MG = 1.0
ATROPINE_MAX_MG = 3.0             # beyond this the drug is not the answer
ATROPINE_MIN_INTERVAL_MIN = 3     # the interval the guideline repeats it at
NODAL_FIRST_DOSE_BEATS = 18.0     # what a first dose buys in a nodal block
NODAL_DOSE_DECAY = .55            # each further dose buys less than the last
ATROPINE_TAU_MIN = 12.0           # and what it bought fades

PACING_DEFAULT_THRESHOLD_MA = 70  # this patient's capture threshold
PACING_MIN_RATE = 30
PACING_MAX_RATE = 100
PACING_MAX_MA = 200
# Fraction of the lost rate that pacing gives back as forward flow. Pacing an
# ischaemic ventricle is not the same as its own organized beat.
PACING_OUTPUT_EFFICIENCY = .85
# Pressure the block costs, at the full loss of rate, and gives back when the
# rate returns. It is the bradycardia's share of the low output, not the shock.
SBP_PER_LOST_RATE = 34.0


def location(spec):
    """Where the block sits, from the case's own coronary declaration."""
    declared = str((spec or {}).get("av_block_location") or "").strip().lower()
    if declared in {"nodal", "infranodal"}:
        return declared
    # An inferior occlusion takes the AV node; anything else that blocks is
    # below it until a case says otherwise.
    return "nodal" if (spec or {}).get("territory") == "inferior" else "infranodal"


def atropine_gain(f, spec):
    """Beats the atropine still contributes, after its decay."""
    if location(spec) != "nodal":
        return 0.0
    gain = 0.0
    for given in f.get("atropine_doses", ()):
        beats = NODAL_FIRST_DOSE_BEATS * (NODAL_DOSE_DECAY ** given["index"])
        elapsed = max(0.0, f["elapsed"] - given["at"])
        gain += beats * (ATROPINE_TAU_MIN / (ATROPINE_TAU_MIN + elapsed))
    return gain


def atropine_total_mg(f):
    return sum(given["dose_mg"] for given in f.get("atropine_doses", ()))


def capturing(f):
    """True when the pacer's output reaches this patient's threshold."""
    return bool(f.get("pacing_rate")) and float(f.get("pacing_ma") or 0) >= float(
        f.get("pacing_threshold_ma") or PACING_DEFAULT_THRESHOLD_MA)


def effective_rate(f, spec, escape_rate):
    """The ventricular rate the monitor shows under the block."""
    if capturing(f):
        return float(f["pacing_rate"])
    return escape_rate + atropine_gain(f, spec)


def rhythm(f):
    if not f.get("pacing_rate"):
        return "Complete AV block"
    return ("Paced rhythm, capture confirmed" if capturing(f)
            else "Pacing spikes without capture, underlying complete AV block")


def pressure_penalty(f, spec, escape_rate, baseline_rate):
    """How much systolic pressure the lost rate is still costing."""
    rate = effective_rate(f, spec, escape_rate)
    if capturing(f):
        rate = escape_rate + (rate - escape_rate) * PACING_OUTPUT_EFFICIENCY
    baseline = max(1.0, float(baseline_rate or 60))
    shortfall = max(0.0, min(1.0, (baseline - rate) / baseline))
    return SBP_PER_LOST_RATE * shortfall
