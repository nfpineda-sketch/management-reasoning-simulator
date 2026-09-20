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
TROPONIN_PER_MIN = 25.0           # ng/L
TROPONIN_WASHOUT_FACTOR = 1.6     # the peak after reperfusion, from washout
LV_LOSS_PER_MIN = .0025           # regional function lost: 90 minutes closed costs a grade
LV_FLOOR = .45
LV_RECOVERY_PER_MIN = .0015       # after the artery opens
LV_RECOVERY_CEILING = .85
CIRCULATION_PER_MIN = .0012       # the failing pump, on top of the family drift
RV_CIRCULATION_PER_MIN = .0018    # an inferior infarct with right ventricular involvement
AV_BLOCK_AT_MIN = 45              # inferior territory only
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
            return (f"The artery is open after {method}: the ST segment resolves on a repeated ECG, the discomfort "
                    "settles and the troponin peaks from washout. The affected wall recovers only partly.")
        if not active_occlusion(spec):
            return None
        f["ischemic_min"] = f.get("ischemic_min", 0.0) + 1
        f["lv_function"] = max(LV_FLOOR, f.get("lv_function", 1.0) - LV_LOSS_PER_MIN)
        f["circulation"] += RV_CIRCULATION_PER_MIN if spec.get("rv_involvement") else CIRCULATION_PER_MIN
        if (spec.get("territory") == "inferior" and f["ischemic_min"] >= AV_BLOCK_AT_MIN
                and not f.get("av_block_at")):
            f["av_block_at"] = now
            return ("Complete atrioventricular block: the inferior infarct has taken the AV node. The rate falls and "
                    "the pressure falls with it.")
        if f["ischemic_min"] >= VF_AT_MIN and not f.get("vf_at"):
            f["vf_at"] = now
            return ventricular_fibrillation(f, "an artery that has stayed closed for two hours")
    else:
        since = now - f["artery_open_at"]
        f["lv_function"] = min(LV_RECOVERY_CEILING, f.get("lv_function", 1.0) + LV_RECOVERY_PER_MIN)
        if since <= 60:
            f["troponin_peak_at"] = now
    return None


def ventricular_fibrillation(f, cause):
    f["vf_at"] = f["elapsed"]
    return (f"Ventricular fibrillation, precipitated by {cause}. The pulse is lost and organized reassessment is "
            "paused: this is the outcome the pathway exists to prevent.")


def troponin(f, baseline):
    """The troponin the resident measures, with the washout peak after reperfusion."""
    released = TROPONIN_PER_MIN * f.get("ischemic_min", 0.0)
    if is_open(f):
        released *= TROPONIN_WASHOUT_FACTOR
    return round(baseline + released)


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
