"""TD-59 (pre-pilot closure, 2026-10-02): "General appearance" says what the case wrote that still holds.

Since 2026-09-21 the region was only the engine's summary, which follows the state, and the line the
case wrote was never shown: the dialysis fistula, the belt mark, the sting site, the bleeding thigh.
Now the summary comes first and, below it, the case's own findings:

* what does not change in an encounter, as the case wrote it (``appearance_stable``);
* the bleeding thigh as the case wrote it while nothing has been applied to it, and afterwards the
  wound and what the engine holds of its bleeding -- reduced, or stopped;
* nothing for urticaria, flushing, swelling, shivering or restlessness: the engine gives them no
  course, so they are not said again after arrival (docs/REGISTRO_DEUDA_TECNICA.md, TD-59).

Each line reads whole in one language: the summary and the engine's sentences in Spanish, the case's
lines in English until the faculty approves the case's Spanish, and in Spanish afterwards.
"""
import json
import re

import pytest

import clinical_cases
import language
import tools_case_text
from family_engine import examination_finding, execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

STABLE = {
    "anaphylaxis_63m_betablocked": "A sting site on the right forearm.",
    "renal_colic_34m": "No rash.",
    "bradycardia_ccb_68m": "No rash or swelling.",
    "bradycardia_bb_54f": "No rash.",
    "bradycardia_hyperk_63m": "A dialysis fistula in the left forearm.",
    "trauma_hemothorax_41m": "Seatbelt marking across the chest and abdomen.",
}
NOT_FOLLOWED = ("anaphylaxis_29f", "obstructive_pyelonephritis_58f", "bradycardia_avb3_78f")
FILES = {"renal_colic_34m": "renal_colic", "obstructive_pyelonephritis_58f": "renal_colic"}


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def family_of(case):
    return next(family for family, spec in clinical_cases.FAMILIES.items()
                if any(variant["id"] == case for variant in spec["variants"]))


def appearance(engine, case, orders=()):
    state = encounter(engine, family_of(case), case)["state"]
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result.get("clarification")
    return examination_finding(state, "General appearance")


def approved(case):
    rows = json.loads(open(f"case_text/es/{FILES.get(case, family_of(case))}.json", encoding="utf-8").read())[case]
    return {row["en"]: row["es"] for row in rows.values() if row.get("es")}


def test_each_line_is_a_verbatim_part_of_what_the_case_wrote():
    for spec in clinical_cases.FAMILIES.values():
        for variant in spec["variants"]:
            written = (variant.get("examination") or {}).get("General appearance", "")
            for key in ("appearance_stable", "appearance_while_bleeding"):
                if variant.get(key):
                    fragment = variant[key].rstrip(".").lower()
                    assert fragment in written.lower(), (variant["id"], key)


def test_a_stable_finding_is_said_below_the_engine_s_summary(engine):
    for case, line in STABLE.items():
        lines = appearance(engine, case).split("\n")
        assert lines[0].startswith("Mental status: ") and lines[1:] == [line], case


def test_what_has_no_course_in_the_engine_is_not_said_again(engine):
    for case in NOT_FOLLOWED:
        text = appearance(engine, case)
        assert "\n" not in text and text.startswith("Mental status: "), case
        assert not re.search(r"urticari|wheal|swelling|shivering|restless", text, re.I)


def test_the_bleeding_thigh_follows_what_was_applied_to_it(engine):
    case = "trauma_limb_hemorrhage_27m"
    assert appearance(engine, case).split("\n")[1:] == [
        "A soaked dressing over a deep right thigh wound that is bleeding."]
    assert appearance(engine, case, ["Apply direct pressure to the thigh wound."]).split("\n")[1:] == [
        "A deep right thigh wound.", "The external bleeding is reduced, not stopped."]
    assert appearance(engine, case, ["Apply a tourniquet to the right thigh."]).split("\n")[1:] == [
        "A deep right thigh wound.", "The external bleeding is stopped."]


def test_an_encounter_keeps_the_case_it_started_with(engine):
    state = encounter(engine, "bradycardia", "bradycardia_hyperk_63m")["state"]
    for key in ("appearance_stable", "appearance_while_bleeding"):
        state["encounter_spec"]["clinical_case"].pop(key, None)
    assert "\n" not in examination_finding(state, "General appearance")


def test_each_line_reads_whole_in_one_language(engine):
    for case, orders in (("bradycardia_hyperk_63m", ()), ("anaphylaxis_63m_betablocked", ()),
                         ("trauma_limb_hemorrhage_27m", ("Apply direct pressure to the thigh wound.",)),
                         ("anaphylaxis_29f", ())):
        text = appearance(engine, case, orders)
        # "Before" means no approved passage installed: a room run earlier in the process installs them all.
        language.set_narrative({}, "es")
        with language.narrating(case):
            before = language.examination(text, "es").split("\n")
            language.set_narrative({case: approved(case)}, "es")
            try:
                after = language.examination(text, "es").split("\n")
            finally:
                language.set_narrative({}, "es")
        # The summary in Spanish either way, "flushed" included.
        for said in (before[0], after[0]):
            assert said.startswith("Estado mental: ") and not re.search(r"Expression|Color: [a-z ]*flushed|Diaphoresis", said)
        english = text.split("\n")
        for index, line in enumerate(english[1:], start=1):
            if line.startswith("The external bleeding"):
                assert before[index] == after[index] == "El sangrado externo está disminuido, sin detenerse."
            else:
                assert before[index] == line                   # the case's line, whole, until approved
                assert after[index] == approved(case)[line]    # and whole in Spanish afterwards


def test_the_rewritten_chest_is_part_of_the_case_s_narrative():
    """TD-47 and TD-50 rewrite the anaphylaxis chest; those lines are approved with the case."""
    for case in ("anaphylaxis_29f", "anaphylaxis_63m_betablocked"):
        variant = next(v for v in clinical_cases.FAMILIES["anaphylaxis"]["variants"] if v["id"] == case)
        derived = {path: text for path, text in tools_case_text.passages(variant).items()
                   if path.startswith("/derived/")}
        assert derived and all(approved(case).get(text) for text in derived.values())
    assert approved("anaphylaxis_29f")["Increased effort with widespread expiratory wheeze; no stridor heard now."] == (
        "Esfuerzo respiratorio aumentado, con sibilancias espiratorias difusas; ya no se escucha estridor.")
    assert tools_case_text.problems() == []
