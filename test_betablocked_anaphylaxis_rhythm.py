"""DF-23 row 7 (faculty, 2026-09-29, A): anaphylaxis_63m_betablocked shows atrial fibrillation.

The monitor and the 12-lead ECG show the atrial fibrillation the case documents (apixaban,
the irregular rhythm his wife reports, the irregular pulse on examination). The rate stays
64, and the beta blockade, the adrenaline response and the glucagon response are the same
as before: only the rhythm label changed.
"""
import pytest

import ecg12
from clinical_cases import FAMILIES
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

CASE = "anaphylaxis_63m_betablocked"
COURSE = ["Give epinephrine 0.5 mg IM. Reassess in 5 minutes.",
          "Give glucagon 1 mg IV. Reassess in 10 minutes.",
          "Order a 12-lead ECG. Reassess in 5 minutes."]


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def played(engine):
    state = encounter(engine, "anaphylaxis", CASE)["state"]
    seen = [dict(state["observable"])]
    for order in COURSE:
        assert execute_family_bundle(state, parse_family_actions(order))["executed"], order
        seen.append(dict(state["observable"]))
    return state, seen


def test_the_monitor_and_the_ecg_show_atrial_fibrillation_at_64(engine):
    state, seen = played(engine)
    assert seen[0]["hr"] == 64 and all(o["rhythm"] == "AF" for o in seen)
    assert ecg12.acquire_ecg(state)["rhythm"] == "af"


def test_the_physiology_is_the_one_the_sinus_label_had(engine, monkeypatch):
    af_state, af = played(engine)
    [variant] = [v for v in FAMILIES["anaphylaxis"]["variants"] if v["id"] == CASE]
    monkeypatch.setitem(variant["observable"], "rhythm", "Sinus rhythm")
    _, sinus = played(engine)
    keys = ("sbp", "dbp", "hr", "spo2", "respiratory_rate", "mental_status", "crt")
    assert [{k: o[k] for k in keys} for o in af] == [{k: o[k] for k in keys} for o in sinus]
    assert {o["rhythm"] for o in sinus} <= {"Sinus rhythm", "Sinus bradycardia", "Sinus tachycardia"}
