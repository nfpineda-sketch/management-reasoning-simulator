"""Right heart strain or a filling defect obliges the pulmonary obstruction declaration.

Faculty decision (2026-09-20), the third gate with the same rule as the coronary
and airway ones. A generated case whose POCUS describes a dilated or failing right
ventricle, or whose CT angiogram reports filling defects, is a case about an
obstructed pulmonary circulation, and it must declare
``engine.pulmonary_obstruction`` so the encounter runs the shared pathway: the
clock of sustained hypotension, the price of fast volume, the dissolution and its
bleeding.

A declaration with none of those findings is refused: the resident would have
nothing to find.
"""
import re

import pe_obstruction

RV_CUES = (r"\bdilat\w*", r"\bd-?sign\b", r"\bseptal flattening\b", r"\bmccon+ell\b",
           r"\blarger than the lv\b", r"\bright ventricular (?:strain|failure|dysfunction)\b")
CTPA_CUES = (r"\bfilling defect\w*\b", r"\bthrombus\b", r"\bembol\w*\b", r"\bsaddle\b")
NEGATION = re.compile(r"\b(?:no|not|without|absent|denies|never)\b")
BLEEDING_RISKS = tuple(sorted(pe_obstruction.BLEED_RISK_TEXT))


def _affirmed(text, cues):
    for sentence in re.split(r"(?<=[.;!?])\s+|;\s*", str(text or "")):
        if NEGATION.search(sentence.lower()):
            continue
        if any(re.search(cue, sentence, re.I) for cue in cues):
            return True
    return False


def discoverable(case):
    """True when the resident can find the obstruction in what the case reports."""
    investigations = case.get("investigations", {})
    rv = investigations.get("pocus", {}).get("result", {}).get("rv", "")
    ctpa = investigations.get("ctpa", {}).get("result", {})
    ctpa_text = " ".join(str(value) for value in ctpa.values()) if isinstance(ctpa, dict) else str(ctpa)
    return _affirmed(rv, RV_CUES) or _affirmed(ctpa_text, CTPA_CUES)


def issues(case):
    declaration = case.get("engine", {}).get("pulmonary_obstruction")
    found = []
    if discoverable(case) and not isinstance(declaration, dict):
        found.append({
            "code": "PULMONARY_OBSTRUCTION_UNDECLARED", "path": "case.engine.pulmonary_obstruction",
            "message": ("The case reports right heart strain or a pulmonary filling defect, so it must declare "
                        "engine.pulmonary_obstruction. The engine then runs the pathway: thrombolysis is the "
                        f"treatment only after {pe_obstruction.SUSTAINED_HYPOTENSION_MIN} minutes of systolic below "
                        f"{pe_obstruction.HYPOTENSION_SBP}, volume faster than "
                        f"{pe_obstruction.TOLERATED_ML_PER_MIN:g} mL/min distends the ventricle, and positive "
                        "pressure costs an obstructed circulation."),
            "details": {},
        })
        return found
    if not isinstance(declaration, dict):
        return found
    if not discoverable(case):
        found.append({
            "code": "PULMONARY_OBSTRUCTION_UNDISCOVERABLE", "path": "case.engine.pulmonary_obstruction",
            "message": ("engine.pulmonary_obstruction is declared, but neither the POCUS right ventricle nor a CT "
                        "angiogram reports anything the resident could find. Describe the dilated or failing right "
                        "ventricle, or the filling defects, or remove the declaration."),
            "details": {},
        })
    risk = declaration.get("bleeding_risk")
    if risk is not None and risk not in BLEEDING_RISKS:
        found.append({
            "code": "PULMONARY_OBSTRUCTION_UNDISCOVERABLE", "path": "case.engine.pulmonary_obstruction.bleeding_risk",
            "message": f"bleeding_risk must be null or one of {list(BLEEDING_RISKS)}.",
            "details": {"bleeding_risk": risk},
        })
    if risk == "recent_surgery" and not re.search(r"\b(?:surger\w*|operation|operated|post-?operative)\b",
                                                  " ".join(str(v) for values in case.get("history", {}).values()
                                                           for v in (values if isinstance(values, list) else [values])),
                                                  re.I):
        found.append({
            "code": "PULMONARY_OBSTRUCTION_UNDISCOVERABLE", "path": "case.engine.pulmonary_obstruction.bleeding_risk",
            "message": ("A declared recent-surgery bleeding risk must appear in the history the resident can take: "
                        "say when the operation was."),
            "details": {"bleeding_risk": risk},
        })
    return found
