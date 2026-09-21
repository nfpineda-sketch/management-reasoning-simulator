"""Opening the artery: the ACS pathway the ECG dictates (faculty, 2026-09-19).

Faculty statement: management changes with the ECG. In ACS with ST elevation the
cath lab is activated to open the artery. In ACS without it management is
different and immediate angiography is not required. And there are
electrocardiographic equivalents that carry no ST elevation yet must be studied
aggressively with angiography: an isolated posterior infarct, de Winter T waves,
diffuse ST depression with ST elevation in aVR, and Wellens syndrome. The
nomenclature is moving to OMI precisely so these are not left out.

Times, from the faculty: door to balloon under 90 minutes in a centre with a cath
lab; 120 minutes when the patient must be transferred; if a delay beyond 120
minutes is anticipated, the correct treatment is thrombolysis.

The cost of delay, which the faculty accepted as plausible in full: a rising
troponin, a worsening regional wall motion on POCUS, arrhythmia (complete AV
block in an inferior infarct, ventricular fibrillation late), hypotension and
shock. A stress test in Wellens syndrome produces ventricular fibrillation.

These are teaching magnitudes, not a prediction, and only the bank ACS family
uses them.
"""

DOOR_TO_BALLOON_MIN = 90          # a centre with a cath lab
DOOR_TO_BALLOON_TRANSFER_MIN = 120
THROMBOLYSIS_TO_REPERFUSION_MIN = 60
THROMBOLYSIS_WINDOW_MIN = 720     # beyond twelve hours of symptoms it buys nothing

# Cost of an artery that stays closed, per minute of occlusion.
# Troponin follows the faculty's illustrative hs-cTnI curve (2026-09-20), timed from
# the onset of pain rather than from arrival: 8 ng/L at 30 minutes, 18 at one hour,
# 90 at two, 450 at three, 1600 at four and 6000 at six. Those are one plausible
# curve, not thresholds, and the assay's own upper reference belongs to the case.
# Two consequences the faculty stated: the first hours show the rise, not the peak,
# which falls around twelve hours; and reperfusion accelerates the rise by washout,
# so a brisk climb after angioplasty does not by itself mean the procedure failed.
# The last point is the peak the faculty placed around twelve hours from the pain,
# after which the curve holds rather than growing without bound.
TROPONIN_CURVE = ((30, 8), (60, 18), (120, 90), (180, 450), (240, 1600), (360, 6000), (720, 20000))
TROPONIN_WASHOUT_FACTOR = 1.6     # the peak after reperfusion, from washout
TROPONIN_AFTER_REPERFUSION_SHARE = .3   # the rise continues, more slowly
LV_LOSS_PER_MIN = .0025           # regional function lost: 90 minutes closed costs a grade
LV_FLOOR = .45
LV_RECOVERY_PER_MIN = .0015       # after the artery opens
LV_RECOVERY_CEILING = .85
CIRCULATION_PER_MIN = .0012       # the failing pump, on top of the family drift
RV_CIRCULATION_PER_MIN = .0018    # an inferior infarct with right ventricular involvement
FAMILY_DRIFT_PER_MIN = .001       # what the engine adds for the family; imported there
# Faculty decision 2026-09-21: where the left ventricle is the problem, its
# contractility is paired to the pressure and the perfusion. Opening the artery
# used to recover the wall on POCUS while the circulation kept sliding, so the
# reward for a good door-to-balloon was an isolated ultrasound finding. The
# recovery now gives back what the occlusion took, at the rate it took it.
CIRCULATION_ARRIVAL = 1.0         # the circulation the case describes on arrival
# Faculty 2026-09-20: the block is conditional, but it must not be rare. It belongs
# to the inferior territory, it needs the artery still shut, and the case can exclude
# it with av_block_risk false.
AV_BLOCK_AT_MIN = 45
AV_BLOCK_RATE = 42
VF_AT_MIN = 120                   # an artery closed this long, or a stress test in Wellens
SHOCK_LV = .55
ARRIVAL_LV = .82                  # the wall the case already describes as reduced

# (threshold, singular clause, plural clause): the report has to read as English.
WALL_MOTION = (
    (.85, "contracts normally", "contract normally"),
    (.70, "shows mildly reduced contraction", "show mildly reduced contraction"),
    (.58, "shows moderately reduced contraction", "show moderately reduced contraction"),
    (0.0, "is akinetic", "are akinetic"),
)
TERRITORY_WALL = {"inferior": "inferior wall", "anterior": "anterior wall and apex",
                  "lateral": "lateral wall", "posterior": "posterior wall",
                  "left_main": "anterior and lateral walls", "subendocardial": "left ventricle diffusely"}
# Reperfusion resolves the injury current; the ECG the resident repeats says so.
RESOLVED_PROFILE = "baseline"


def nitrate_drop(f, equivalent_mcg_min, baseline_sbp, fluid_ml):
    """Nitroglycerin in a preload-dependent right ventricular infarct.

    Same mechanics and constants as the generated-case hazard
    (nitrate_hazard.CAUSES["right_ventricular_infarction"]): a saturating fall that
    develops in minutes, recovers slowly when the drug is stopped, and is rescued by
    volume. Faculty decision 2026-09-19: model it in the bank case too.
    """
    import nitrate_hazard
    spec = nitrate_hazard.CAUSES["right_ventricular_infarction"]
    rate = max(0.0, float(equivalent_mcg_min or 0))
    target = spec["max_fraction"] * baseline_sbp * rate / (rate + spec["half_effect_mcg_min"]) if rate else 0.0
    drop = f.get("nitrate_drop", 0.0)
    drop += (target - drop) / (nitrate_hazard.ONSET_TAU_MIN if target > drop else nitrate_hazard.RECOVERY_TAU_MIN)
    f["nitrate_drop"] = max(0.0, drop - nitrate_hazard.FLUID_RESCUE_MMHG_PER_ML * max(0.0, fluid_ml))
    return f["nitrate_drop"]


# Actions a declared coronary mechanism authorises in a generated case, which would
# otherwise need an authored response rule of their own.
MECHANISM_ACTIONS = frozenset({"thrombolysis", "stress_test"})

# The generated adapter receives observable deltas, not the bank's internal variables,
# exactly as the nitrate hazard does.
SBP_PER_BURDEN = 45.0
DBP_PER_BURDEN = 25.0
HR_PER_BURDEN = 25.0


# The shared core amplifies what it is given: a large negative rate input collapsed
# the patient within minutes. These are deliberately small nudges, ramped in.
AV_BLOCK_HR_DELTA = -12.0
AV_BLOCK_SBP_DELTA = -6.0
AV_BLOCK_RAMP_MIN = 5.0
GENERATED_SBP_FLOOR = -30.0        # the mechanism never pushes the core past this


def generated_effects(f):
    """Observable deltas for a generated case: (sbp, dbp, hr).

    The pathway keeps its bookkeeping in the shared family_state, where the burden
    of the failing pump accumulates as it does for a bank case. A generated case
    reads that burden as a fall in pressure and a rise in rate. The core owns the
    rate, so a complete AV block enters as a bounded fall, never as an imposed value.
    """
    burden = max(0.0, float(f.get("circulation", 1.0)) - 1.0)
    sbp, dbp, hr = -SBP_PER_BURDEN * burden, -DBP_PER_BURDEN * burden, HR_PER_BURDEN * burden
    block = f.get("av_block_at")
    if block is not None and not is_open(f):
        share = min(1.0, (f["elapsed"] - block) / AV_BLOCK_RAMP_MIN)
        sbp += AV_BLOCK_SBP_DELTA * share
        dbp += AV_BLOCK_SBP_DELTA * .6 * share
        hr += AV_BLOCK_HR_DELTA * share
    return max(GENERATED_SBP_FLOOR, sbp), max(GENERATED_SBP_FLOOR * .6, dbp), hr


def coronary(state):
    """The case's coronary declaration, or None for a case that has none."""
    return state.get("encounter_spec", {}).get("clinical_case", {}).get("engine", {}).get("coronary")


def active_occlusion(spec):
    """True when muscle is dying now.

    Wellens syndrome is the exception the faculty named: the artery is open at this
    moment, so nothing infarcts while the resident watches, and yet the lesion is
    unstable. It needs scheduled angiography, and provocation testing fibrillates.
    """
    return bool(spec.get("omi")) and spec.get("active_occlusion", True)


def door_to_balloon(spec):
    return DOOR_TO_BALLOON_MIN if spec.get("pci_capable", True) else DOOR_TO_BALLOON_TRANSFER_MIN


def anticipated_delay_exceeds_window(spec):
    """True when the faculty's rule makes thrombolysis, not transfer, the answer."""
    return door_to_balloon(spec) > DOOR_TO_BALLOON_TRANSFER_MIN or not spec.get("pci_capable", True) and spec.get("transfer_delay_min", 0) > DOOR_TO_BALLOON_TRANSFER_MIN


def activate(f, spec, now, method="pci"):
    """Start the clock. Returns the minute the artery is expected to open."""
    if f.get("reperfusion_at") is not None:
        return f["reperfusion_at"]
    delay = THROMBOLYSIS_TO_REPERFUSION_MIN if method == "thrombolysis" else door_to_balloon(spec)
    f["reperfusion_method"] = method
    f["reperfusion_activated_at"] = now
    f["reperfusion_at"] = now + delay
    return f["reperfusion_at"]


def open_artery(f, now):
    f["artery_open_at"] = now
    f["troponin_peak_at"] = now


def is_open(f):
    return f.get("artery_open_at") is not None


def step(state):
    """Advance the infarct by one minute; return an event text when one happens."""
    f, spec = state["family_state"], coronary(state)
    if spec is None or not spec.get("omi"):
        return None
    now = f["elapsed"]
    if active_occlusion(spec):
        f.setdefault("lv_function", ARRIVAL_LV)
    if not is_open(f):
        if f.get("reperfusion_at") is not None and now >= f["reperfusion_at"]:
            open_artery(f, now)
            state["ecg_profile"] = RESOLVED_PROFILE
            if not active_occlusion(spec):
                return ("Angiography found a critical proximal stenosis, which was stented before it occluded. The "
                        "T-wave pattern resolves on a repeated ECG.")
            method = "percutaneous coronary intervention" if f.get("reperfusion_method") == "pci" else "thrombolysis"
            return (f"The artery is open after {method}: the ST segment resolves on a repeated ECG and the discomfort "
                    "settles. The troponin climbs faster now, from washout, which is not a failed procedure; its peak "
                    "comes hours later. The affected wall recovers only partly.")
        if not active_occlusion(spec):
            return None
        f["ischemic_min"] = f.get("ischemic_min", 0.0) + 1
        f["lv_function"] = max(LV_FLOOR, f.get("lv_function", 1.0) - LV_LOSS_PER_MIN)
        f["circulation"] += RV_CIRCULATION_PER_MIN if spec.get("rv_involvement") else CIRCULATION_PER_MIN
        if (spec.get("territory") == "inferior" and spec.get("av_block_risk", True)
                and f["ischemic_min"] >= AV_BLOCK_AT_MIN and not f.get("av_block_at")):
            f["av_block_at"] = now
            return ("Complete atrioventricular block: the inferior infarct has taken the AV node. The rate falls and "
                    "the pressure falls with it.")
        if f["ischemic_min"] >= VF_AT_MIN and not f.get("vf_at"):
            f["vf_at"] = now
            return ventricular_fibrillation(f, "an artery that has stayed closed for two hours")
    else:
        since = now - f["artery_open_at"]
        if active_occlusion(spec):
            # Only a wall that was lost can come back. A lesion that never
            # occluded (Wellens) keeps the normal ventricle the case describes.
            before = f.get("lv_function", ARRIVAL_LV)
            f["lv_function"] = min(LV_RECOVERY_CEILING, before + LV_RECOVERY_PER_MIN)
            # The wall that comes back brings the pressure and the perfusion with it.
            f["circulation"] = max(CIRCULATION_ARRIVAL,
                                   f["circulation"] - circulation_per_lv(spec) * (f["lv_function"] - before))
        if since <= 60:
            f["troponin_peak_at"] = now
    return None


def circulation_per_lv(spec):
    """How much circulation a unit of ventricle is worth, for this case.

    The ratio the occlusion itself used, so a wall that returns to where it
    started returns the patient to the circulation they arrived with.
    """
    per_min = RV_CIRCULATION_PER_MIN if spec.get("rv_involvement") else CIRCULATION_PER_MIN
    return (per_min + FAMILY_DRIFT_PER_MIN) / LV_LOSS_PER_MIN


def ventricular_fibrillation(f, cause):
    f["vf_at"] = f["elapsed"]
    return (f"Ventricular fibrillation, precipitated by {cause}. The pulse is lost and organized reassessment is "
            "paused: this is the outcome the pathway exists to prevent.")


def _curve(minutes_since_onset):
    """The faculty's curve, interpolated in log space between its points."""
    import math
    points = TROPONIN_CURVE
    if minutes_since_onset <= points[0][0]:
        return points[0][1] * minutes_since_onset / points[0][0]
    for (t0, v0), (t1, v1) in zip(points, points[1:]):
        if minutes_since_onset <= t1:
            share = (minutes_since_onset - t0) / (t1 - t0)
            return 10 ** (math.log10(v0) + share * (math.log10(v1) - math.log10(v0)))
    return points[-1][1]   # the peak holds; the fall is beyond this encounter


def curve_minute(value):
    """Where a value sits on the curve: the minute of infarct that produces it."""
    import math
    points = TROPONIN_CURVE
    value = max(0.0, float(value))
    if value <= points[0][1]:
        return points[0][0] * value / points[0][1]
    for (t0, v0), (t1, v1) in zip(points, points[1:]):
        if value <= v1:
            share = (math.log10(value) - math.log10(v0)) / (math.log10(v1) - math.log10(v0))
            return t0 + share * (t1 - t0)
    return float(points[-1][0])


def troponin(f, baseline, onset_min=0, spec=None):
    """The troponin the resident measures, on the curve timed from the pain.

    Faculty decision 2026-09-21: the case's authored arrival value sets the clock
    rather than a floor. It used to be a floor, so the value did not move until
    the curve caught up with it — a hundred minutes in the left main case, the
    sickest of the six, where serial samples all read 260 with the artery shut.
    Read as a clock, the arrival value is still exactly what the case authored
    and it rises from the first minute, at the curve's own pace. ``onset_min``
    stays the narrative the patient tells; the assay carries its own history.

    A case with no artery shut — a non-occlusion syndrome, or Wellens with its
    artery open — keeps the authored value: nothing is infarcting while the
    resident watches.
    """
    if spec is not None and not active_occlusion(spec):
        return round(float(baseline))
    ischaemic = f.get("ischemic_min", 0.0)
    after = max(0.0, f.get("elapsed", ischaemic) - ischaemic) * TROPONIN_AFTER_REPERFUSION_SHARE
    started_at = max(float(onset_min), curve_minute(baseline))
    value = _curve(started_at + ischaemic + after)
    if is_open(f):
        value *= TROPONIN_WASHOUT_FACTOR
    return round(max(float(baseline), value))


GLOBAL_MOTION = ((.85, "normal"), (.70, "mildly reduced"), (.58, "moderately reduced"), (0.0, "severely reduced"))


def wall_motion(f, spec):
    territory = spec.get("territory")
    if territory in {"subendocardial", "left_main"}:
        grade = next(text for threshold, text in GLOBAL_MOTION if f.get("lv_function", 1.0) >= threshold)
        return f"Contraction is globally {grade}, without a single focal defect"
    wall = TERRITORY_WALL.get(territory, "affected wall")
    plural = wall.endswith("walls") or " and " in wall
    singular_clause, plural_clause = next((one, many) for threshold, one, many in WALL_MOTION
                                          if f.get("lv_function", 1.0) >= threshold)
    grade = plural_clause if plural else singular_clause
    return f"The {wall} {grade}; the other walls contract normally"


def in_shock(f):
    return not is_open(f) and f.get("lv_function", 1.0) <= SHOCK_LV


def pathway_note(spec, f, now):
    """What the resident is told when they activate reperfusion."""
    if not spec.get("omi"):
        return ("Cath lab contacted. This ECG shows no occlusion pattern: immediate angiography is not required, and "
                "the pathway here is antiplatelet and anticoagulant treatment with a monitored bed and reassessment.")
    delay = door_to_balloon(spec)
    where = "in this centre" if spec.get("pci_capable", True) else "after transfer to a centre with a cath lab"
    if not active_occlusion(spec):
        return (f"Cath lab contacted {where}: angiography is scheduled for minute {now + delay}. This pattern demands "
                "angiography and rules out provocation testing, even though the patient is pain-free.")
    return (f"Cath lab activated {where}: the artery is expected to be open at minute {now + delay} "
            f"(door to balloon {delay} minutes).")
