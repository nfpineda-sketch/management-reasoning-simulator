"""An airway obstruction must be discoverable, and a wheezing case must declare it.

Faculty decision (2026-09-20), the same rule as the coronary mechanism: obligation,
not advice. A generated case whose examination describes bronchospasm is a case
about an obstructed airway, and it must declare ``engine.airway_obstruction`` so
the encounter runs the shared mechanics: the trapped gas of a short expiratory
time, the barotrauma of a sustained plateau, and the window in which intubation
belongs.

The reverse is rejected too: a declaration the resident cannot find in the
examination or the history leaves them nothing to read.
"""
import re

import asthma_ventilation

# What a resident would read as bronchospasm.
OBSTRUCTION_CUES = (r"\bwheez\w*", r"\bprolonged expiration\b", r"\bexpiratory (?:wheeze|phase)\b",
                    r"\bbronchospasm\b", r"\bair (?:entry|movement) (?:is )?(?:reduced|poor|decreased)\b",
                    r"\bsilent chest\b", r"\bquiet chest\b")
NEGATION = re.compile(r"\b(?:no|not|without|absent|denies|never)\b")
SEVERITY_RANGE = (.3, 1.3)


def _sentences(text):
    return [part for part in re.split(r"(?<=[.;!?])\s+", str(text or "")) if part]


def mentions_obstruction(case):
    """True when an affirmed cue of bronchospasm appears where the resident looks."""
    sources = [case.get("examination", {}).get("Respiratory", "")]
    history = case.get("history", {})
    for key in ("chief_complaint", "associated_symptoms", "breathing", "medical_history"):
        value = history.get(key)
        sources += value if isinstance(value, list) else [value or ""]
    for text in sources:
        for sentence in _sentences(text):
            if NEGATION.search(sentence.lower()):
                continue
            if any(re.search(cue, sentence, re.I) for cue in OBSTRUCTION_CUES):
                return True
    return False


def issues(case):
    declaration = case.get("engine", {}).get("airway_obstruction")
    described = mentions_obstruction(case)
    found = []
    if described and not isinstance(declaration, dict):
        found.append({
            "code": "AIRWAY_OBSTRUCTION_UNDECLARED", "path": "case.engine.airway_obstruction",
            "message": ("The case describes bronchospasm (wheeze, prolonged expiration or reduced air entry), so it "
                        "must declare engine.airway_obstruction with a severity. The engine then runs the airway "
                        "mechanics: trapped gas from a short expiratory time, barotrauma above a plateau of "
                        f"{asthma_ventilation.PLATEAU_LIMIT_CMH2O:g} cmH2O, and the window for intubation."),
            "details": {},
        })
        return found
    if not isinstance(declaration, dict):
        return found
    if not described:
        found.append({
            "code": "AIRWAY_OBSTRUCTION_UNDISCOVERABLE", "path": "case.engine.airway_obstruction",
            "message": ("engine.airway_obstruction is declared, but neither the respiratory examination nor the "
                        "history describes bronchospasm: the resident cannot discover it. Describe the wheeze, the "
                        "prolonged expiration or the reduced air entry, or remove the declaration."),
            "details": {},
        })
    severity = declaration.get("severity")
    if not isinstance(severity, (int, float)) or not SEVERITY_RANGE[0] <= severity <= SEVERITY_RANGE[1]:
        found.append({
            "code": "AIRWAY_OBSTRUCTION_UNDISCOVERABLE", "path": "case.engine.airway_obstruction.severity",
            "message": (f"Declare a severity between {SEVERITY_RANGE[0]} and {SEVERITY_RANGE[1]}: 1.0 is the patient "
                        "the case describes at arrival, and the engine relieves it with the bronchodilators the "
                        "resident gives."),
            "details": {"severity": severity},
        })
    return found
