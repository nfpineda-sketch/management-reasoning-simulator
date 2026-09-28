"""Two cases whose own words and whose patient disagreed (DF-23, cycle 6, 2026-09-28).

The cycle 6 clinical consistency audit (DF-23) corrected only what met all six
of the faculty's conditions: one defensible reading, a clear original design, no
change to the Decision Challenge, no new methodology, a before and after shown,
and tests that protect it. Two did.

- ``acs_52m_de_winter`` arrives with "Akinesis of the anterior wall and apex".
  The model starts every occlusion at the same "mildly reduced" wall, and took
  over at the first repeat scan: with the artery still closed the wall seemed
  to recover, then failed again -- a spontaneous reperfusion that never
  happened, in the case whose C14 evidence is naming that akinesis. The case now
  names its grade, and its words stand until the model reaches it or the artery
  opens. The physiology does not change, and neither does any other case.
- ``bradycardia_bb_54f`` is "found drowsy", "drowsy but rousable", "opens eyes to
  voice": four authored texts, and an arrival state left at the default "Alert".
  The room showed her conversing, then "worsening" at five minutes when nothing
  had changed. She now arrives drowsy.
"""
from copy import deepcopy

import pytest

import family_engine
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import initialize, load_engine


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def play(engine, family, case_id, orders, *, strip=None):
    state = deepcopy(encounter(engine, family, case_id)["state"])
    if strip:
        state["encounter_spec"]["clinical_case"]["engine"]["coronary"].pop(strip, None)
    initialize(engine, state)
    session = engine["st"].session_state
    seen = []
    for text in orders:
        result = family_engine.execute_family_bundle(session.state, engine["clinical_interpreter"](text))
        assert result["executed"], result.get("clarification")
        observable = session.state["observable"]
        seen.append({"lv": ((session.state.get("diagnostics") or {}).get("pocus") or {}).get("lv"),
                     "mental": observable.get("mental_status"),
                     "vitals": (observable.get("sbp"), observable.get("dbp"), observable.get("hr"),
                                observable.get("spo2"))})
    return seen


REPEAT = ["Order a POCUS. Reassess in 1 minute.", "Reassess in 30 minutes.", "Order a POCUS. Reassess in 5 minutes.",
          "Reassess in 60 minutes.", "Order a POCUS. Reassess in 5 minutes."]


def test_the_de_winter_akinesis_stands_while_the_artery_is_closed(engine):
    seen = play(engine, "acs", "acs_52m_de_winter", REPEAT)
    assert seen[0]["lv"].startswith("Akinesis of the anterior wall and apex")
    assert seen[2]["lv"].startswith("Akinesis of the anterior wall and apex")      # +35, closed
    assert seen[3]["lv"].startswith("Akinesis of the anterior wall and apex")      # +95, closed
    assert seen[4]["lv"] == "The anterior wall and apex are akinetic; the other walls contract normally"
    assert not any("mildly reduced" in (row["lv"] or "") for row in seen)


def test_once_the_artery_opens_the_model_reads_the_wall(engine):
    seen = play(engine, "acs", "acs_52m_de_winter",
                ["Activate the cath lab. Reassess in 95 minutes.", "Order a POCUS. Reassess in 5 minutes."])
    assert "moderately reduced" in seen[-1]["lv"]


def test_nothing_else_changes_in_de_winter_nor_in_the_other_occlusions(engine):
    # The physiology is the model's, with or without the arrival grade.
    with_grade = play(engine, "acs", "acs_52m_de_winter", REPEAT)
    without = play(engine, "acs", "acs_52m_de_winter", REPEAT, strip="arrival_wall_grade")
    assert [row["vitals"] for row in with_grade] == [row["vitals"] for row in without]
    # An encounter frozen before the grade existed keeps the reading it had.
    assert "mildly reduced" in without[2]["lv"]
    # The cases that name no grade read as before.
    posterior = play(engine, "acs", "acs_61m_posterior", REPEAT)
    assert posterior[2]["lv"] == "The posterior wall shows mildly reduced contraction; the other walls contract normally"
    left_main = play(engine, "acs", "acs_70f_left_main", REPEAT)
    assert left_main[2]["lv"] == "Contraction is globally mildly reduced, without a single focal defect"


def test_the_beta_blocker_overdose_arrives_drowsy_and_does_not_worsen_on_its_own(engine):
    seen = play(engine, "bradycardia", "bradycardia_bb_54f",
                ["Reassess in 1 minute.", "Atropine 1 mg IV, reassess in 5 minutes."])
    assert seen[0]["mental"] == "Drowsy"
    assert seen[0]["vitals"][:3] == (80, 48, 40)
    assert seen[1]["mental"] == "Drowsy"


def test_the_arrival_state_is_the_one_the_case_writes(engine):
    from clinical_cases import variant_by_id
    case = variant_by_id("bradycardia_bb_54f")
    assert case["observable"]["mental_status"] == "Drowsy"
    assert "drowsy" in case["presentation"].lower()
