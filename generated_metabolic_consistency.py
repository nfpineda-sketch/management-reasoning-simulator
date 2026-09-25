"""Gates for the glucose and opioid mechanisms (faculty decision 2026-09-20).

The same rule as the three gates before them: a case that describes the finding
must declare the mechanism, and a declaration the resident cannot discover is
refused. Here the findings are at the bedside rather than in a study: the glucose
on the monitor, and the breathing of an opioid.
"""
import re

import case_cues
import glucose_rescue
import opioid_reversal

# The glucose mechanism's own definitions, shared with the hypoglycaemia
# catalogue of the bank (2026-09-25): one source, not two copies.
HYPOGLYCAEMIA_MG_DL = glucose_rescue.HYPOGLYCAEMIA_MG_DL
SULFONYLUREAS = glucose_rescue.SULFONYLUREA_NAMES
ALCOHOL_OR_STARVATION = glucose_rescue.ALCOHOL_OR_STARVATION
OPIOID_CUES = (r"\bopioid\w*\b", r"\bopiate\w*\b", r"\bfentanyl\b", r"\bheroin\w*\b", r"\bmorphine\b",
               r"\boxycodone\b", r"\bmethadone\b", r"\bbuprenorphine\b", r"\bnaloxone\b",
               r"\bpinpoint pupils?\b", r"\bpupils? are pinpoint\b")
OPIOID_RR = 12
NEGATION = case_cues.NEGATION
_history_text = case_cues.history_text
_affirmed = case_cues.affirmed


def glucose_issues(case):
    declaration = case.get("engine", {}).get("glucose_failure")
    glucose = case.get("observable", {}).get("glucose_mg_dl")
    low = isinstance(glucose, (int, float)) and glucose < HYPOGLYCAEMIA_MG_DL
    found = []
    if low and not isinstance(declaration, dict):
        found.append({
            "code": "GLUCOSE_FAILURE_UNDECLARED", "path": "case.engine.glucose_failure",
            "message": (f"The arrival glucose is {glucose} mg/dL, so the case must declare engine.glucose_failure. "
                        "The engine then runs the shared pathway: the glucose that keeps falling, the ampoule, "
                        "glucagon, oral carbohydrate and the 10% infusion, the seizure after "
                        f"{glucose_rescue.SEIZURE_AFTER_MIN} minutes below {glucose_rescue.SEIZURE_GLUCOSE} mg/dL, "
                        "and thiamine where it matters."),
            "details": {"glucose_mg_dl": glucose},
        })
        return found
    if not isinstance(declaration, dict):
        return found
    if not low:
        found.append({
            "code": "GLUCOSE_FAILURE_UNDISCOVERABLE", "path": "case.observable.glucose_mg_dl",
            "message": (f"engine.glucose_failure is declared, but the arrival glucose is {glucose}: author a glucose "
                        f"below {HYPOGLYCAEMIA_MG_DL} mg/dL or remove the declaration."),
            "details": {"glucose_mg_dl": glucose},
        })
    history = _history_text(case)
    if declaration.get("sulfonylurea") and not re.search(SULFONYLUREAS, history, re.I):
        found.append({
            "code": "GLUCOSE_FAILURE_UNDISCOVERABLE", "path": "case.engine.glucose_failure.sulfonylurea",
            "message": ("A declared sulfonylurea must be in the medicines the resident can ask about: name the drug "
                        "in the history."),
            "details": {},
        })
    if declaration.get("thiamine_deficient") and not _affirmed(history, ALCOHOL_OR_STARVATION):
        found.append({
            "code": "GLUCOSE_FAILURE_UNDISCOVERABLE", "path": "case.engine.glucose_failure.thiamine_deficient",
            "message": ("A declared thiamine deficiency must be discoverable: the history has to describe the alcohol "
                        "use or the weeks without food that caused it."),
            "details": {},
        })
    return found


def opioid_issues(case):
    declaration = case.get("engine", {}).get("opioid_toxidrome")
    observed = case.get("observable", {})
    rate = observed.get("respiratory_rate")
    slow = isinstance(rate, (int, float)) and rate < OPIOID_RR
    described = _affirmed(_history_text(case), OPIOID_CUES)
    found = []
    if slow and described and not isinstance(declaration, dict):
        found.append({
            "code": "OPIOID_TOXIDROME_UNDECLARED", "path": "case.engine.opioid_toxidrome",
            "message": (f"The case describes an opioid and a respiratory rate of {rate}/min, so it must declare "
                        "engine.opioid_toxidrome. The engine then runs the shared pathway: the antidote that wears "
                        "off before the drug, the withdrawal of pushing past the ventilation target, and the arrest "
                        f"after {opioid_reversal.ARREST_AFTER_MIN} minutes of unsupported apnoeic breathing."),
            "details": {"respiratory_rate": rate},
        })
        return found
    if not isinstance(declaration, dict):
        return found
    if not described:
        found.append({
            "code": "OPIOID_TOXIDROME_UNDISCOVERABLE", "path": "case.engine.opioid_toxidrome",
            "message": ("engine.opioid_toxidrome is declared, but nothing in the history or the examination points to "
                        "an opioid: name the exposure, or describe the pupils."),
            "details": {},
        })
    if not slow:
        found.append({
            "code": "OPIOID_TOXIDROME_UNDISCOVERABLE", "path": "case.observable.respiratory_rate",
            "message": (f"An opioid toxidrome arrives with a respiratory rate below {OPIOID_RR}/min; this case "
                        f"authored {rate}."),
            "details": {"respiratory_rate": rate},
        })
    return found


def issues(case):
    return glucose_issues(case) + opioid_issues(case)
