"""acs_70f_left_main: the arrival scan names the grade the model keeps (faculty, 2026-09-29).

Mildly reduced, as the model's arrival position (lv_function 0.82) reads -- a teaching
position, never an ejection fraction -- and not recalibrated from the congestion.
"""
import json
from pathlib import Path

import acs_reperfusion
from clinical_cases import variant_by_id
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

ARRIVAL = "Globally mildly reduced contraction without a single focal defect"


def test_the_arrival_scan_names_the_grade_the_model_keeps():
    case = variant_by_id("acs_70f_left_main")
    assert case["investigations"]["pocus"]["result"]["lv"] == ARRIVAL
    assert "Globally mildly reduced contraction on POCUS" in case["faculty"]["discriminating_findings"]
    assert acs_reperfusion.GRADES[acs_reperfusion.authored_grade_index(case["engine"]["coronary"])] == "mildly reduced"
    assert "82" not in json.dumps(case["investigations"]["pocus"]["result"])
    state = encounter(load_engine(), "acs", "acs_70f_left_main")["state"]
    execute_family_bundle(state, parse_family_actions("Perform bedside POCUS. Reassess in 20 minutes."))
    execute_family_bundle(state, parse_family_actions("Perform bedside POCUS."))
    assert state["diagnostics"]["pocus"]["lv"] == "Contraction is globally mildly reduced, without a single focal defect"


def test_the_spanish_says_the_same_grade():
    rows = json.loads(Path("case_text/es/acs.json").read_text(encoding="utf-8"))["acs_70f_left_main"]
    row = rows["/investigations/pocus/result/lv"]
    assert row["en"] == ARRIVAL and "levemente" in row["es"] and "moderad" not in row["es"]
