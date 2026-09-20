"""Gates for the bleeding and congestion mechanisms (faculty decision 2026-09-20).

Same rule as the five before them. A case that describes blood being lost must
declare ``engine.active_bleeding``, and a case whose lungs are full must declare
``engine.pulmonary_congestion``; a declaration the resident cannot discover is
refused.
"""
import re

from family_engine import GI_BLEED

BLEEDING_CUES = (r"\bmelena\b", r"\bmelaena\b", r"\bhaematemesis\b", r"\bhematemesis\b",
                 r"\bvomit\w* blood\b", r"\bcoffee[- ]ground\b", r"\bblack,? (?:tarry|sticky) stool\w*\b",
                 r"\brectal bleeding\b", r"\bfrank blood\b", r"\bupper gastrointestinal bleed\w*\b")
CONGESTION_CUES = (r"\bdiffuse (?:bilateral )?b-?lines\b", r"\bbilateral b-?lines\b",
                   r"\bbilateral (?:inspiratory )?crackles\b", r"\bpulmonary (?:oedema|edema)\b",
                   r"\bfrothy sputum\b")
NEGATION = re.compile(r"\b(?:no|not|without|absent|denies|never)\b")
ANAEMIA_G_DL = 10


def _texts(case):
    parts = list(case.get("examination", {}).values())
    for values in case.get("history", {}).values():
        parts += values if isinstance(values, list) else [values]
    investigations = case.get("investigations", {})
    for study in ("pocus", "chest_xray"):
        result = investigations.get(study, {}).get("result", {})
        parts += list(result.values()) if isinstance(result, dict) else [result]
    return [str(part) for part in parts if part]


def _affirmed(case, cues):
    for text in _texts(case):
        for sentence in re.split(r"(?<=[.;!?])\s+|;\s*", text):
            if NEGATION.search(sentence.lower()):
                continue
            if any(re.search(cue, sentence, re.I) for cue in cues):
                return True
    return False


def bleeding_issues(case):
    declaration = case.get("engine", {}).get("active_bleeding")
    described = _affirmed(case, BLEEDING_CUES)
    found = []
    if described and not isinstance(declaration, dict):
        found.append({
            "code": "ACTIVE_BLEEDING_UNDECLARED", "path": "case.engine.active_bleeding",
            "message": ("The case describes blood being lost, so it must declare engine.active_bleeding. The engine "
                        "then runs the shared pathway: haemoglobin falling while the bleeding continues, crystalloid "
                        "that buys less than blood and dilutes what is left, a proton-pump inhibitor that leaves "
                        f"{GI_BLEED['bleeding_with_ppi']:.0%} of it, and the endoscopy gastroenterology performs "
                        f"{GI_BLEED['endoscopy_after_consult_min']} minutes after the call once the patient is "
                        "resuscitated."),
            "details": {},
        })
        return found
    if not isinstance(declaration, dict):
        return found
    if not described:
        found.append({
            "code": "ACTIVE_BLEEDING_UNDISCOVERABLE", "path": "case.engine.active_bleeding",
            "message": ("engine.active_bleeding is declared, but nothing in the history, the examination or the "
                        "studies describes blood being lost: the resident cannot find it."),
            "details": {},
        })
    hemoglobin = case.get("engine", {}).get("initial_labs", {}).get("hemoglobin_g_dl")
    if isinstance(hemoglobin, (int, float)) and hemoglobin > ANAEMIA_G_DL and declaration.get("established"):
        found.append({
            "code": "ACTIVE_BLEEDING_UNDISCOVERABLE", "path": "case.engine.initial_labs.hemoglobin_g_dl",
            "message": (f"An established bleed arrives anaemic: author a haemoglobin at or below {ANAEMIA_G_DL} g/dL, "
                        "or declare established false for a bleed that has only just begun."),
            "details": {"hemoglobin_g_dl": hemoglobin},
        })
    return found


def congestion_issues(case):
    declaration = case.get("engine", {}).get("pulmonary_congestion")
    described = _affirmed(case, CONGESTION_CUES)
    found = []
    if described and not isinstance(declaration, dict):
        found.append({
            "code": "PULMONARY_CONGESTION_UNDECLARED", "path": "case.engine.pulmonary_congestion",
            "message": ("The case describes a congested lung, so it must declare engine.pulmonary_congestion. The "
                        "shared core already models the congestion itself; the declaration adds the intravenous "
                        "nitroglycerin bolus, which no native action covers, and states the case's intent."),
            "details": {},
        })
        return found
    if not isinstance(declaration, dict):
        return found
    if not described:
        found.append({
            "code": "PULMONARY_CONGESTION_UNDISCOVERABLE", "path": "case.engine.pulmonary_congestion",
            "message": ("engine.pulmonary_congestion is declared, but neither the examination nor the POCUS nor the "
                        "chest radiograph describes a congested lung."),
            "details": {},
        })
    return found


def issues(case):
    return bleeding_issues(case) + congestion_issues(case)
