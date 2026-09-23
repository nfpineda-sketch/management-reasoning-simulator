"""A patient the case describes as comfortable must not be reported in pain.

Found by playing the Wellens case (2026-09-22): the vignette said "pain-free
now", the history said "right now I feel fine" and "between them I have no pain
at all", and the encounter reported "The patient reports severe pain" next to
completely normal vitals. Nothing was wrong with the engine; the case declared
no pain score, so it inherited the family's arrival pain of 7/10.

The check is over the whole bank rather than that one case, because the trap is
in the inheritance and any family can fall into it.
"""
import re

import pytest

import analgesia
from clinical_cases import FAMILIES

# What a case says when the pain is over, in either language it is written in.
_COMFORTABLE = re.compile(
    r"\bpain[- ]free\b|\bno pain\b|\bnot? in pain\b|\bcomfortable\b|\bpain (?:has )?(?:resolved|settled|gone)\b"
    r"|\bfeel (?:fine|well)\b|\bsin dolor\b|\bno tengo dolor\b", re.I)
# ... and what it says when the pain is happening now, which the first pattern
# must not be allowed to override.
_IN_PAIN_NOW = re.compile(
    r"\b(?:constant|ongoing|continuous) (?:since|pain|pressure|tightness)\b"
    r"|\bhas been constant\b|\bcannot catch my breath\b|\bthe pain is\b", re.I)


def _variants():
    for family, definition in sorted(FAMILIES.items()):
        for case in definition.get("variants", []):
            yield family, case


def _arrival_pain(family, case):
    return analgesia.arrival_pain({"engine_family": family, "encounter_spec": {"clinical_case": case}})


def _said(case):
    history = case.get("history") or {}
    spoken = [str(value) for value in history.values() if isinstance(value, str)]
    for value in history.values():
        if isinstance(value, (list, tuple)):
            spoken.extend(str(item) for item in value)
    return " ".join([str(case.get("presentation", ""))] + spoken)


@pytest.mark.parametrize("family, case", list(_variants()), ids=lambda v: v if isinstance(v, str) else v["id"])
def test_a_case_that_says_the_patient_is_comfortable_arrives_without_pain(family, case):
    said = _said(case)
    if not _COMFORTABLE.search(said) or _IN_PAIN_NOW.search(said):
        pytest.skip("this case does not describe a patient who is free of pain")
    score = _arrival_pain(family, case)
    assert score < .5, (
        f"{case['id']} describes a patient who is free of pain but arrives at {score}/10, "
        f"which is reported as {analgesia.descriptor(score)!r}. Declare pain_score in its "
        "observable rather than inheriting the family's."
    )


@pytest.mark.parametrize("family, case", list(_variants()), ids=lambda v: v if isinstance(v, str) else v["id"])
def test_a_declared_pain_score_is_the_one_the_encounter_uses(family, case):
    declared = case.get("observable", {}).get("pain_score")
    if declared is None:
        pytest.skip("this case inherits the family's arrival pain")
    assert _arrival_pain(family, case) == float(declared)


def test_the_wellens_patient_is_the_one_this_was_found_on():
    case = next(c for _, c in _variants() if c["id"] == "acs_48m_wellens")
    assert _arrival_pain("acs", case) == 0
    assert analgesia.descriptor(_arrival_pain("acs", case)) == "no pain"
