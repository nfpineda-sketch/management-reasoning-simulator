"""The authored arrival POCUS must agree with what the core derives from the drivers.

A paid sildenafil case authored "normal contractility" with drivers
(cardiac_function 0.7 x contractile_reserve 0.6) that the shared core reads as a
weak LV from the first minute. The display no longer contradicts itself, but the
patient was still simulated with a weak heart. Faculty decision (2026-09-18):
reject such a case before review so the author aligns drivers and findings.

Only clear contradictions are rejected: categories two steps apart (normal LV vs
moderately-severely reduced; collapsing vs non-collapsing IVC; no B-lines vs
diffuse B-lines). Wording the classifier cannot place, and focal findings the
core cannot represent (focal B-lines of a pneumonia), are left to the reviewer.
"""
import re

# Core thresholds, mirrored from clinical_diagnostics.pocus_transition.
LV_THRESHOLDS = (.68, .48)          # cardiac_function x contractile_reserve
IVC_THRESHOLDS = (.48, .65)         # effective_volume (preload at arrival)
B_LINE_THRESHOLDS = (.20, .48)      # pulmonary_congestion

LV_LEVELS = ("preserved or hyperdynamic", "mildly reduced", "moderately to severely reduced")
IVC_LEVELS = (">50% inspiratory collapse", "about 50% inspiratory collapse", "<50% inspiratory collapse")
B_LINE_LEVELS = ("no B-lines", "scattered B-lines", "diffuse B-lines")


def _lv_level(text):
    t = text.lower()
    if re.search(r"\b(?:moderate|moderately|severe|severely|poor|markedly reduced|significantly reduced)\b", t):
        return 2
    if re.search(r"\bmild(?:ly)?\b", t):
        return 1
    if re.search(r"\b(?:normal|preserved|hyperdynamic|vigorous|good)\b", t):
        return 0
    return None


def _ivc_level(text):
    t = text.lower()
    if re.search(r"not assessable", t):
        return None
    if re.search(r"(?:<\s*50\s*%|minimal|no (?:inspiratory )?collapse|plethoric|non-?collapsing|fixed)", t):
        return 2
    if re.search(r"(?:about|approximately|~)\s*50\s*%", t):
        return 1
    if re.search(r"(?:>\s*50\s*%|collapsing|near-?complete collapse|flat|collapses? completely)", t):
        return 0
    return None


def _b_line_level(text):
    t = text.lower()
    if re.search(r"\bfocal\b", t) and not re.search(r"\bdiffuse bilateral\b", t):
        return None
    if re.search(r"\bno (?:diffuse )?b-?lines\b|\ba-?line", t):
        return 0
    if re.search(r"\bdiffuse\b", t):
        return 2
    if re.search(r"\b(?:scattered|few|some|occasional)\b", t):
        return 1
    return None


def _band(value, lower, upper):
    """0 below ``lower``, 1 up to ``upper``, 2 above: the core's three categories."""
    return 0 if value < lower else 1 if value < upper else 2


def issues(case):
    engine = case.get("engine", {})
    if engine.get("core_profile") is None:
        return []
    authored = case.get("investigations", {}).get("pocus", {}).get("result", {})
    from clinical_core_defaults import INITIAL_HIDDEN
    h = {**INITIAL_HIDDEN, **engine["core_profile"]["initial_hidden"]}
    core = {
        # A stronger heart is the lower LV level, so invert the contractility band.
        "lv": 2 - _band(h["cardiac_function"] * h["contractile_reserve"], LV_THRESHOLDS[1], LV_THRESHOLDS[0]),
        "ivc": _band(h["effective_volume"], *IVC_THRESHOLDS),
        "lungs": _band(h["pulmonary_congestion"], *B_LINE_THRESHOLDS),
    }
    checks = (
        ("lv", _lv_level, LV_LEVELS, "cardiac_function x contractile_reserve: >= 0.68 preserved, 0.48-0.68 mildly reduced, < 0.48 moderately to severely reduced"),
        ("ivc", _ivc_level, IVC_LEVELS, "effective_volume: < 0.48 >50% collapse, 0.48-0.65 about 50%, >= 0.65 <50% collapse"),
        ("lungs", _b_line_level, B_LINE_LEVELS, "pulmonary_congestion: < 0.20 no B-lines, 0.20-0.48 scattered, >= 0.48 diffuse"),
    )
    found = []
    for field, classify, levels, rule in checks:
        text = authored.get(field)
        written = classify(text) if isinstance(text, str) else None
        if written is None or abs(written - core[field]) < 2:
            continue
        found.append({
            "code": "POCUS_CORE_MISMATCH", "path": f"case.investigations.pocus.result.{field}",
            "message": (f"The arrival POCUS {field} finding describes {levels[written]}, but the core_profile drivers "
                        f"produce {levels[core[field]]} from the first minute ({rule}). Align initial_hidden with the "
                        f"authored finding, or the finding with the drivers."),
            "details": {"field": field, "authored_level": levels[written], "core_level": levels[core[field]]},
        })
    return found


# The core also imposes respiratory floors from the arrival pulmonary signal
# (clinical_physiology: respiratory_surface thresholds). They only ever raise RR
# and cap SpO2, so an authored RR 18 with congestion 0.20 became 24 at once and
# stayed there. Mirrored thresholds: (surface, minimum RR, maximum SpO2).
RESPIRATORY_FLOORS = ((.18, 24, None), (.30, 28, 92), (.42, 32, 89), (.56, 36, 85), (.70, 40, 80))
RR_TOLERANCE = 3


def respiratory_floor(case):
    """(surface, minimum RR, maximum SpO2) the core imposes at arrival, or None."""
    from clinical_core_defaults import INITIAL_HIDDEN
    import clinical_physiology as core
    h = {**INITIAL_HIDDEN, **case["engine"]["core_profile"]["initial_hidden"]}
    surface = max(h.get("respiratory_failure_severity", 0.0), core.pulmonary_clinical_signal({"hidden": h}))
    applicable = [floor for floor in RESPIRATORY_FLOORS if surface >= floor[0]]
    if not applicable:
        return surface, None, None
    caps = [cap for _, _, cap in applicable if cap is not None]
    return surface, applicable[-1][1], (min(caps) if caps else None)


def respiratory_issues(case):
    if case.get("engine", {}).get("core_profile") is None:
        return []
    surface, minimum_rr, maximum_spo2 = respiratory_floor(case)
    observed = case.get("observable", {})
    found = []
    if minimum_rr is not None and observed.get("respiratory_rate", minimum_rr) <= minimum_rr - RR_TOLERANCE:
        found.append(("respiratory_rate", observed["respiratory_rate"], f"a respiratory rate of at least {minimum_rr}/min"))
    if maximum_spo2 is not None and observed.get("spo2", 0) > maximum_spo2 + 1:
        found.append(("spo2", observed["spo2"], f"an SpO2 of at most {maximum_spo2}%"))
    rule = ("pulmonary_congestion (the arrival pulmonary signal) >= 0.18 forces RR >= 24; >= 0.30 RR >= 28 and SpO2 <= 92; "
            ">= 0.42 RR >= 32 and SpO2 <= 89; >= 0.56 RR >= 36 and SpO2 <= 85; >= 0.70 RR >= 40 and SpO2 <= 80")
    return [{
        "code": "RESPIRATORY_CORE_MISMATCH", "path": f"case.observable.{field}",
        "message": (f"The arrival {field} is {value}, but the core_profile drivers impose {limit} from the first minute "
                    f"({rule}). Lower pulmonary_congestion to match the authored breathing, or author the breathing the "
                    f"drivers produce."),
        "details": {"field": field, "authored": value, "pulmonary_signal": round(surface, 3)},
    } for field, value, limit in found]
