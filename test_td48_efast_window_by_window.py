"""TD-48 (faculty, 2026-10-02): the E-FAST shows every window its case documents.

Until then the room, the Management Trace and the review documents showed only
"Pericardium: No pericardial fluid": the 41m's left haemothorax and both trauma
cases' negative abdominal, pelvic and lung windows never reached the resident.
Now the report follows the faculty's protocol (``efast_report.SECTIONS``), with
"Not documented" for a window a case does not document -- never a finding made
up to complete it. A result made before carries no mark and keeps the single
line its room showed, so an older record still says what the resident saw.
"""
import ast
import json
import math
import random
import re
from copy import deepcopy
from pathlib import Path

import pytest

import efast_report
import language
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from family_reports import format_result
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine


@pytest.fixture(scope="module")
def engine():
    return load_engine()


@pytest.fixture(scope="module")
def app_functions():
    nodes = [n for n in ast.parse(Path("app.py").read_text()).body if isinstance(n, ast.FunctionDef)]
    namespace = {"re": re, "deepcopy": deepcopy, "__file__": "app.py", "json": json, "math": math,
                 "random": random}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "app.py", "exec"), namespace)
    return namespace


def efast(engine, case, orders=("E-FAST",)):
    state = encounter(engine, "trauma", case)["state"]
    result = None
    for order in orders:
        outcome = execute_family_bundle(state, parse_family_actions(order))
        assert outcome["executed"], outcome.get("clarification")
        for summary in outcome["action_summaries"]:
            if summary.get("diagnostic_type") == "efast":
                result = summary["result"]
    return state, result


def test_the_41m_haemothorax_is_in_the_report_with_every_window(engine):
    _, result = efast(engine, "trauma_hemothorax_41m")
    assert efast_report.shown_as_windows(result)
    text = format_result("efast", result)
    lines = text.splitlines()
    assert lines[0] == "E-FAST · performed at minute 0"
    assert [line for line in lines[1:] if not line.startswith("· ")] == [
        "RIGHT UPPER QUADRANT", "LEFT UPPER QUADRANT", "SUPRAPUBIC", "SUBXIPHOID", "LUNG"]
    for key, label in efast_report.LABELS.items():
        assert f"· {label}: {result[key]}" in lines, key
    assert "· Left pleural recess: Fluid in the left pleural recess" in lines
    assert efast_report.free_fluid(result) == ["luq_pleural"]


def test_both_trauma_c14_opportunities_can_now_be_observed(engine):
    # 41m: named on the first scan, and the scan after the drain shows the other cavities still clear.
    _, again = efast(engine, "trauma_hemothorax_41m", ("E-FAST", "Insert a left chest tube.", "E-FAST"))
    repeat = format_result("efast", again)
    for window in ("ruq_morison", "luq_splenorenal", "suprapubic_longitudinal", "suprapubic_transverse"):
        assert again[window].startswith("No free fluid") and again[window] in repeat
    # 27m: every window is there, and none is positive.
    _, negative = efast(engine, "trauma_limb_hemorrhage_27m")
    text = format_result("efast", negative)
    assert all(f"{label}: " in text for label in efast_report.LABELS.values())
    assert efast_report.free_fluid(negative) == [] and efast_report.pneumothorax_windows(negative) == []


def test_a_window_the_case_does_not_document_says_so():
    result = {key: value for key, value in efast_report.study().items() if key != "luq_pleural"}
    result["shown_as"] = efast_report.SHOWN_AS
    text = format_result("efast", result)
    assert "· Left pleural recess: Not documented" in text
    assert efast_report.NORMAL["luq_pleural"] not in text


def test_an_older_record_keeps_the_line_its_room_showed(engine, app_functions):
    state, result = efast(engine, "trauma_hemothorax_41m")
    older = {key: value for key, value in result.items() if key != "shown_as"}
    assert format_result("efast", older) == "E-FAST: Performed at minute 0 · Pericardium: No pericardial fluid"
    snapshot = deepcopy(state)
    snapshot["diagnostics"]["efast"] = older
    assert "E-FAST" not in app_functions["_trace_state_text"](snapshot)


def test_the_trace_state_carries_every_window(engine, app_functions):
    state, result = efast(engine, "trauma_hemothorax_41m")
    text = app_functions["_trace_state_text"](deepcopy(state))
    assert "E-FAST: RIGHT UPPER QUADRANT — " in text
    for key in efast_report.KEYS:
        assert result[key] in text, key
    with language.narrating("trauma_hemothorax_41m"):
        spanish = app_functions["_trace_state_text"](deepcopy(state), "es")
    assert "E-FAST: " in spanish and "Fluid in the left pleural recess" in spanish


def test_spanish_titles_and_whole_lines_until_the_case_is_approved(engine):
    _, result = efast(engine, "trauma_hemothorax_41m")
    english = format_result("efast", result)
    with language.narrating("trauma_hemothorax_41m"):
        spanish = language.say(english, "es")
    assert spanish.splitlines()[0] == "E-FAST · realizado en el minuto 0"
    for title in ("CUADRANTE SUPERIOR DERECHO", "CUADRANTE SUPERIOR IZQUIERDO", "SUPRAPÚBICA", "SUBXIFOIDEA",
                  "PULMÓN"):
        assert title in spanish.splitlines()
    # Without an approved translation the case's own lines stay whole in English (TD-46).
    assert "· Left pleural recess: Fluid in the left pleural recess" in spanish.splitlines()


def test_with_an_approved_translation_the_report_reads_in_spanish(engine):
    _, result = efast(engine, "trauma_hemothorax_41m")
    case = "trauma_hemothorax_41m"
    table = {row["en"]: row["es"] for row in json.loads(Path("case_text/es/trauma.json").read_text())[case].values()}
    language.set_narrative({case: table}, "es")
    try:
        with language.narrating(case):
            spanish = language.say(format_result("efast", result), "es")
    finally:
        language.set_narrative({}, "es")
    assert "· Receso pleural izquierdo: Líquido en el receso pleural izquierdo" in spanish.splitlines()
    assert "· Pericardio: Sin líquido pericárdico" in spanish.splitlines()
    assert not re.search(r"\b(?:recess|pouch|sliding|view|Seashore)\b", spanish)
