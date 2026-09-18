"""Preload-dependent patients in whom nitroglycerin can cause abrupt hypotension.

Faculty decision (2026-09-18): model this only when an AI-generated case includes
one of these conditions. The case declares it in engine.nitrate_hazard, leaves a
cue the resident can find, and the engine then gives nitroglycerin a rapid,
deep fall in pressure that is best rescued by stopping it and giving volume.
Bank cases and PS001 are not affected.

The magnitudes are teaching parameters pending faculty review, not a prediction.
"""
import re

CAUSES = {
    "pde5_inhibitor": {
        "label": "phosphodiesterase-5 inhibitor taken within 48 hours",
        "cue": "the medications history names the drug (for example sildenafil, tadalafil or vardenafil) and when it was taken",
        "sbp_per_mcg_min": .50, "max_fraction": .55,
    },
    "severe_aortic_stenosis": {
        "label": "severe aortic stenosis",
        "cue": "the cardiac examination describes an ejection systolic murmur, or the medical history records aortic stenosis",
        "sbp_per_mcg_min": .45, "max_fraction": .50,
    },
    "lvot_obstruction": {
        "label": "left ventricular outflow tract obstruction (hypertrophic obstructive cardiomyopathy)",
        "cue": "the cardiac examination describes a systolic murmur, or the medical history records hypertrophic cardiomyopathy",
        "sbp_per_mcg_min": .45, "max_fraction": .50,
    },
    "right_ventricular_infarction": {
        "label": "right ventricular infarction",
        "cue": "ecg_profile is st_elevation_inferior and the POCUS RV finding describes a dilated or hypokinetic right ventricle",
        "sbp_per_mcg_min": .40, "max_fraction": .45,
    },
}
ONSET_TAU_MIN = 2.0        # the fall develops within minutes of starting nitroglycerin
RECOVERY_TAU_MIN = 12.0    # after stopping it, pressure returns slowly on its own
FLUID_RESCUE_MMHG_PER_ML = .06   # volume restores preload: 500 mL undoes about 30 mmHg
DBP_FRACTION = .6

_MENTION = {
    "pde5_inhibitor": r"\b(?:sildenafil|tadalafil|vardenafil|avanafil|viagra|cialis|levitra|pde-?5|phosphodiesterase)",
    "severe_aortic_stenosis": r"\baortic (?:valve )?stenosis\b",
    "lvot_obstruction": r"\b(?:hypertrophic (?:obstructive )?cardiomyopathy|hocm|lvot obstruction|outflow (?:tract )?obstruction)\b",
    "right_ventricular_infarction": r"\b(?:right ventricular (?:infarct|infarction|involvement|myocardial infarction)|rv (?:infarct|infarction|involvement))\b",
}
_NEGATION = re.compile(r"\b(?:no|not|never|denies|denied|without|none)\b")


def _sentences(text):
    return [part for part in re.split(r"(?<=[.;!?])\s+", str(text or "").lower()) if part]


def mentions(text, cause):
    """True when a sentence affirms the condition; "I have not taken sildenafil" does not."""
    return any(re.search(_MENTION[cause], sentence) and not _NEGATION.search(sentence)
               for sentence in _sentences(text))


def case_text(case):
    history = " ".join(" ".join(items) for items in case.get("history", {}).values())
    exam = " ".join(case.get("examination", {}).values())
    faculty = " ".join(str(value) for key, value in case.get("faculty", {}).items() if isinstance(value, str))
    rv = case.get("investigations", {}).get("pocus", {}).get("result", {}).get("rv", "")
    return " ".join((case.get("presentation", ""), history, exam, faculty, str(rv)))


def cue_present(case, cause):
    """The resident can discover the declared condition from the case itself."""
    history = case.get("history", {})
    cardiac = case.get("examination", {}).get("Cardiac", "")
    if cause == "pde5_inhibitor":
        return any(mentions(item, cause) for item in history.get("medications", []) + history.get("exposure", []))
    if cause in {"severe_aortic_stenosis", "lvot_obstruction"}:
        murmur = any(re.search(r"\bsystolic murmur\b", sentence) and not _NEGATION.search(sentence)
                     for sentence in _sentences(cardiac.replace(";", ".")))
        return murmur or any(mentions(item, cause) for item in history.get("medical_history", []))
    if cause == "right_ventricular_infarction":
        rv = str(case.get("investigations", {}).get("pocus", {}).get("result", {}).get("rv", ""))
        abnormal = any(re.search(r"\b(?:dilat|enlarg|hypokin|akine|reduced|impaired|larger than the lv)", sentence)
                       and not _NEGATION.search(sentence)
                       for sentence in _sentences(rv.replace(";", ".")))
        return case.get("ecg_profile") == "st_elevation_inferior" and abnormal
    return False


def issues(case):
    """Declared without a cue, or described without being declared: both are rejected."""
    found = []
    hazard = case.get("engine", {}).get("nitrate_hazard")
    declared = hazard.get("cause") if isinstance(hazard, dict) else None
    if declared and not cue_present(case, declared):
        found.append({"code": "NITRATE_HAZARD_UNDISCOVERABLE", "path": "case.engine.nitrate_hazard",
                      "message": f"engine.nitrate_hazard declares {CAUSES[declared]['label']}, but the resident cannot "
                                 f"discover it: {CAUSES[declared]['cue']}.",
                      "details": {"cause": declared}})
    text = case_text(case)
    for cause in CAUSES:
        if cause != declared and mentions(text, cause):
            found.append({"code": "NITRATE_HAZARD_UNDECLARED", "path": "case.engine.nitrate_hazard",
                          "message": f"The case describes {CAUSES[cause]['label']}, a condition in which nitroglycerin can "
                                     f"cause abrupt hypotension, but engine.nitrate_hazard does not declare it. Declare "
                                     f"cause '{cause}' or remove the condition from the case.",
                          "details": {"cause": cause}})
    return found


def step(state, fluid_ml):
    """Advance the nitrate-induced fall in systolic pressure by one minute.

    Returns the current fall in mmHg (0 for a case without a declared hazard).
    """
    case = state["encounter_spec"]["clinical_case"]
    hazard = case.get("engine", {}).get("nitrate_hazard")
    if not isinstance(hazard, dict) or hazard.get("cause") not in CAUSES:
        return 0.0
    spec = CAUSES[hazard["cause"]]
    g, treatments = state["generated_state"], state["coupled_state"]["treatments"]
    rate = float(treatments.get("nitroglycerin_rate_mcg_min") or 0) if treatments.get("nitroglycerin") else 0.0
    baseline = float(case["observable"]["sbp"])
    target = min(spec["max_fraction"] * baseline, spec["sbp_per_mcg_min"] * rate)
    drop = g.get("nitrate_drop", 0.0)
    drop += (target - drop) / (ONSET_TAU_MIN if target > drop else RECOVERY_TAU_MIN)
    # Volume refills the pooled venous capacitance; while nitroglycerin still runs
    # the fall re-develops, so the rescue lasts only once it is stopped.
    g["nitrate_drop"] = max(0.0, drop - FLUID_RESCUE_MMHG_PER_ML * max(0.0, fluid_ml))
    return g["nitrate_drop"]
