"""An occlusion pattern on the ECG obliges the case to declare its coronary mechanism.

Faculty decision (2026-09-20): make it mandatory, not advisory. A generated case
whose ECG shows ST elevation, an isolated posterior infarct, de Winter T waves,
diffuse ST depression with aVR elevation or Wellens syndrome is a case about an
occluded artery, and it must declare ``engine.coronary`` so the engine runs the
reperfusion pathway: the door-to-balloon clock, the infarct that grows while the
artery stays shut, the arrhythmias, and the ECG that resolves when it opens.

The reverse is also rejected: a declared occlusion whose ECG shows none of those
patterns leaves the resident nothing to read.
"""
import acs_reperfusion

# Territories each morphology can belong to. Wellens is the pattern of a critical
# stenosis that is open at this moment, so it never carries an active occlusion.
PATTERN_TERRITORIES = {
    "st_elevation_anterior": {"anterior"},
    "st_elevation_inferior": {"inferior"},
    "st_elevation_lateral": {"lateral"},
    "posterior_infarct": {"posterior"},
    "de_winter": {"anterior"},
    "diffuse_st_depression_avr": {"left_main"},
    "wellens": {"anterior"},
}
OCCLUSION_PATTERNS = frozenset(PATTERN_TERRITORIES)
OPEN_AT_ARRIVAL = frozenset({"wellens"})
RV_INVOLVEMENT_PATTERN = "st_elevation_inferior"


def issues(case):
    profile = str(case.get("ecg_profile") or "baseline")
    spec = case.get("engine", {}).get("coronary")
    found = []
    if profile in OCCLUSION_PATTERNS and not (isinstance(spec, dict) and spec.get("omi")):
        found.append({
            "code": "CORONARY_UNDECLARED", "path": "case.engine.coronary",
            "message": (f"ecg_profile is {profile!r}, which is an occlusion pattern (OMI). Declare engine.coronary "
                        f"with omi true and a territory in {sorted(PATTERN_TERRITORIES[profile])}, so the encounter "
                        "runs the reperfusion pathway, or author an ECG that shows no occlusion."),
            "details": {"ecg_profile": profile},
        })
        return found
    if not isinstance(spec, dict) or not spec.get("omi"):
        return found
    if profile not in OCCLUSION_PATTERNS:
        found.append({
            "code": "CORONARY_ECG_MISMATCH", "path": "case.ecg_profile",
            "message": (f"engine.coronary declares an occlusion, but ecg_profile is {profile!r}: the resident has no "
                        f"pattern to read. Use one of {sorted(OCCLUSION_PATTERNS)}."),
            "details": {"ecg_profile": profile},
        })
        return found
    territory = spec.get("territory")
    if territory not in PATTERN_TERRITORIES[profile]:
        found.append({
            "code": "CORONARY_ECG_MISMATCH", "path": "case.engine.coronary.territory",
            "message": (f"ecg_profile {profile!r} belongs to {sorted(PATTERN_TERRITORIES[profile])}, but the declared "
                        f"territory is {territory!r}."),
            "details": {"ecg_profile": profile, "territory": territory},
        })
    active = spec.get("active_occlusion", True)
    if profile in OPEN_AT_ARRIVAL and active:
        found.append({
            "code": "CORONARY_ECG_MISMATCH", "path": "case.engine.coronary.active_occlusion",
            "message": (f"ecg_profile {profile!r} is the pattern of an artery that is open at this moment. Set "
                        "active_occlusion false: the lesion is unstable and needs angiography, but nothing is "
                        "infarcting while the resident watches."),
            "details": {"ecg_profile": profile},
        })
    if profile not in OPEN_AT_ARRIVAL and not active:
        found.append({
            "code": "CORONARY_ECG_MISMATCH", "path": "case.engine.coronary.active_occlusion",
            "message": f"ecg_profile {profile!r} is an artery that is shut now. Set active_occlusion true.",
            "details": {"ecg_profile": profile},
        })
    if spec.get("rv_involvement") and profile != RV_INVOLVEMENT_PATTERN:
        found.append({
            "code": "CORONARY_ECG_MISMATCH", "path": "case.engine.coronary.rv_involvement",
            "message": (f"Right ventricular involvement belongs to {RV_INVOLVEMENT_PATTERN!r}, not to {profile!r}."),
            "details": {"ecg_profile": profile},
        })
    troponin = case.get("investigations", {}).get("troponin", {}).get("result", {})
    if not isinstance(troponin.get("value_ng_l"), (int, float)):
        found.append({
            "code": "CORONARY_UNDISCOVERABLE", "path": "case.investigations.troponin",
            "message": ("An occlusion case must report a troponin the resident can measure and follow: the engine "
                        "moves it along its curve from the onset of pain, taking the authored value as the floor "
                        f"({acs_reperfusion.TROPONIN_CURVE[2][0]} minutes of pain is about "
                        f"{acs_reperfusion.TROPONIN_CURVE[2][1]} ng/L)."),
            "details": {"ecg_profile": profile},
        })
    return found
