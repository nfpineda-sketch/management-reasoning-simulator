"""The arrival line says that a line exists, never who placed it (faculty, 2026-09-29).

Most hypoglycaemia stories have no paramedics: the arrival line is neutral, "Peripheral IV
in place in the left forearm." ("Vía venosa periférica instalada en el antebrazo
izquierdo."). It follows the case's narrative: Spanish where the faculty approved the case's
Spanish, English where it did not. The wording before the decision stays readable.
"""
import re

import pytest

import arrival_brief
import glucose_rescue
import language
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

SPANISH = "Vía venosa periférica instalada en el antebrazo izquierdo."


@pytest.fixture(scope="module")
def engine():
    return load_engine()


@pytest.mark.parametrize("variant", ["hypoglycemia_28m", "hypoglycemia_76f", "hypoglycemia_54m_thiamine"])
def test_the_arrival_line_names_the_line_and_nobody(engine, variant):
    said = arrival_brief.handover(encounter(engine, "hypoglycemia", variant)["state"])
    assert said.endswith("Peripheral IV in place in the left forearm.")
    assert not re.search(r"paramedic|\bEMS\b|ambulance|placed by|inserted by", glucose_rescue.ARRIVAL_ACCESS_TEXT, re.I)


def test_the_line_follows_the_case_narrative_language(monkeypatch):
    block = "His speech is muddled. " + glucose_rescue.ARRIVAL_ACCESS_TEXT
    monkeypatch.setattr(language, "_NARRATIVE", {})
    assert language.narrative(block, "es", "hypoglycemia_28m") == block      # not approved: English, whole
    language.set_narrative({"hypoglycemia_28m": {"His speech is muddled.": "Habla de forma confusa."}})
    assert language.narrative(block, "es", "hypoglycemia_28m") == "Habla de forma confusa. " + SPANISH
    assert language.say(glucose_rescue.ARRIVAL_ACCESS_TEXT, "es") == SPANISH
    older = "His speech is muddled. " + glucose_rescue.LEGACY_ARRIVAL_ACCESS_TEXT
    assert language.narrative(older, "es", "hypoglycemia_28m").endswith("cánula venosa periférica en el antebrazo izquierdo.")
