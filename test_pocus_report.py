"""Every emergency POCUS report follows one fixed protocol, findings not conclusions.

Faculty specification: LV contractility (qualitative), RV size and relation to
the LV with D-sign and McConnell sign, pericardium with chamber collapse, IVC
diameter and collapse, pleural sliding, B-lines and their distribution,
consolidation and effusion, aortic root, descending and abdominal aorta, and
femoral and popliteal vein compression -- always, normal findings included.

Before this, each case reported whatever it happened to author, no bank case
documented the IVC, and one case's non-compressible vein was stored in a field
the report never displayed.
"""
from copy import deepcopy
import re

import pytest

import clinical_cases
from pocus_report import NOT_DOCUMENTED, POCUS_KEYS, SECTIONS, format_pocus, missing_sections

# Words that state a conclusion rather than what the scan shows.
INTERPRETATION = re.compile(
    r"\b(?:responsive\w*|responder|tamponade|preload|hypovol\w*|overload\w*|"
    r"consistent with|suggest\w*|indicat\w*|diagnostic of)\b", re.I)


def bank_cases():
    for family, data in clinical_cases.FAMILIES.items():
        variants = data["variants"]
        for variant, case in (variants.items() if isinstance(variants, dict) else enumerate(variants)):
            yield family, variant, case


def test_the_report_lists_every_section_in_a_fixed_order():
    text = format_pocus({key: "finding" for key in POCUS_KEYS})
    lines = text.splitlines()[1:]
    headers = [line for line in lines if not line.startswith("· ")]
    assert headers == [section.upper() for section, _ in SECTIONS]
    positions = [text.index(label) for _, items in SECTIONS for _, label in items]
    assert positions == sorted(positions)


def test_each_structure_has_its_own_line_for_the_narrow_bedside_panel():
    lines = format_pocus({key: "finding" for key in POCUS_KEYS}).splitlines()
    items = [line for line in lines if line.startswith("· ")]
    assert len(items) == len(POCUS_KEYS)
    assert all(line.count(": ") == 1 for line in items)


def test_the_compact_layout_keeps_one_line_per_section():
    lines = format_pocus({key: "finding" for key in POCUS_KEYS}, compact=True).splitlines()[1:]
    assert [line.split(" — ")[0] for line in lines] == [section.upper() for section, _ in SECTIONS]


def test_pulmonary_oedema_b_lines_keep_their_distribution_before_and_after_improvement():
    import ast
    from pathlib import Path
    from encounter_generator import generate_encounter
    from family_engine import execute_family_bundle
    tree = ast.parse(Path("app.py").read_text())
    node = next(n for n in tree.body if isinstance(n, ast.Assign)
                and any(getattr(t, "id", "") == "INITIAL_STATE" for t in n.targets))
    state = generate_encounter("R1-05", ast.literal_eval(node.value), api_key="",
                               generation_mode="authored", seed=0)["state"]
    assert state["engine_family"] == "pulmonary_edema"

    def b_lines():
        execute_family_bundle(state, {"actions": [{"type": "diagnostic", "diagnostic": "pocus"},
                                                   {"type": "reassessment", "delay_min": 3}]})
        return state["diagnostics"]["pocus"]["lungs"]

    authored = state["encounter_spec"]  # noqa: F841 -- the case is frozen in the spec
    assert b_lines() == "Diffuse bilateral B-lines in the anterior and lateral zones"
    execute_family_bundle(state, {"actions": [
        {"type": "niv", "mode": "BiPAP", "ipap_cmh2o": 12.0, "epap_cmh2o": 6.0, "fio2_percent": 60.0, "operation": "start"},
        {"type": "nitroglycerin", "rate_mcg_min": 100.0, "operation": "start"},
        {"type": "diuretic", "agent": "furosemide", "dose_mg": 80.0, "route": "IV"},
        {"type": "reassessment", "delay_min": 40}]})
    assert b_lines() == "Fewer but persistent bilateral B-lines in the anterior and lateral zones"


def test_an_undocumented_structure_is_never_shown_as_normal():
    text = format_pocus({"lv": "Preserved contraction"})
    assert text.count(NOT_DOCUMENTED) == len(POCUS_KEYS) - 1
    assert "Compressible" not in text and "Not dilated" not in text


@pytest.mark.parametrize("family,variant,case", list(bank_cases()),
                         ids=lambda v: str(v) if not isinstance(v, dict) else "")
def test_every_bank_case_documents_the_whole_protocol(family, variant, case):
    result = case["investigations"]["pocus"]["result"]
    assert missing_sections(result) == [], (family, variant)
    for key in POCUS_KEYS:
        assert not INTERPRETATION.search(result[key]), (family, variant, key, result[key])


def test_the_ivc_keeps_a_diameter_in_every_bank_case():
    for family, variant, case in bank_cases():
        assert re.search(r"\d+(?:\.\d+)? cm", case["investigations"]["pocus"]["result"]["ivc"]), (family, variant)


def test_the_non_compressible_vein_is_now_visible():
    """It used to live in a field the report never displayed."""
    case = clinical_cases.FAMILIES["pulmonary_embolism"]["variants"][0]
    text = format_pocus(case["investigations"]["pocus"]["result"])
    assert "Non-compressible" in text


def test_ps001_reports_the_whole_protocol_and_no_other_caller_is_filled_in():
    from clinical_diagnostics import pocus_transition
    state = {"case_id": "PS001", "sim_time": 0, "treatments": {},
             "hidden": {"preload_state": .4, "cardiac_function": .8, "pulmonary_congestion": 0}}
    result = pocus_transition(deepcopy(state))["result"]
    assert missing_sections(result) == []
    other = pocus_transition({**deepcopy(state), "case_id": "PS002"})["result"]
    assert "aorta_root" not in other and "dvt_femoral" not in other


@pytest.mark.parametrize("support,expected", [
    ({}, ">50% inspiratory collapse"),
    ({"niv": True}, "not assessable during positive-pressure support"),
    ({"invasive_ventilation": True, "ventilator_peep_cmh2o": 10}, "not assessable during positive-pressure support"),
])
def test_ps001_ivc_is_a_finding_under_each_form_of_support(support, expected):
    from clinical_diagnostics import pocus_transition
    state = {"case_id": "PS001", "sim_time": 0, "treatments": support,
             "hidden": {"preload_state": .4, "cardiac_function": .8, "pulmonary_congestion": 0}}
    ivc = pocus_transition(state)["result"]["ivc"]
    assert expected in ivc and not INTERPRETATION.search(ivc)


def test_the_bank_ivc_evolves_with_the_volume_actually_delivered():
    """The volume branch existed but never ran, because no case documented the IVC."""
    import ast
    from pathlib import Path
    from encounter_generator import generate_encounter
    from family_engine import execute_family_bundle
    tree = ast.parse(Path("app.py").read_text())
    node = next(n for n in tree.body if isinstance(n, ast.Assign)
                and any(getattr(t, "id", "") == "INITIAL_STATE" for t in n.targets))
    state = generate_encounter("R1-05", ast.literal_eval(node.value), api_key="",
                               generation_mode="authored", seed=1)["state"]
    assert state["engine_family"] == "pneumonia"

    def scan():
        execute_family_bundle(state, {"actions": [{"type": "diagnostic", "diagnostic": "pocus"},
                                                   {"type": "reassessment", "delay_min": 3}]})
        return state["diagnostics"]["pocus"]["ivc"]

    before = scan()
    execute_family_bundle(state, {"actions": [{"type": "fluid", "volume_ml": 500, "fluid_type": "normal saline"},
                                               {"type": "reassessment", "delay_min": 12}]})
    after = scan()
    assert before.startswith("1.2 cm") and after.startswith("1.5 cm")


def test_a_generated_case_without_the_whole_protocol_is_refused():
    from generated_case_schema import compile_case
    from generated_case_validation import ContractValidationError, safe_validation_codes
    from test_generated_case import novel_payload
    case = deepcopy(novel_payload())
    pocus = next(s for s in case["investigations"] if s["id"] == "pocus")
    pocus["result"] = [row for row in pocus["result"] if row["field"] not in {"aorta_abdominal", "dvt_popliteal"}]
    with pytest.raises(ContractValidationError) as raised:
        compile_case(case)
    assert "POCUS_INCOMPLETE" in safe_validation_codes(raised.value)
    issue = next(i for i in raised.value.issues if i["code"] == "POCUS_INCOMPLETE")
    assert set(issue["details"]["missing_fields"]) == {"aorta_abdominal", "dvt_popliteal"}


def test_the_faculty_analyses_receive_every_pocus_structure():
    import faculty_analysis
    import management_trace_analysis
    for module in (faculty_analysis, management_trace_analysis):
        assert set(POCUS_KEYS) <= module._DIAGNOSTIC_FIELDS, module.__name__


def test_the_management_trace_records_every_finding_the_resident_had():
    """The trace summary guessed from wording, dropped RV and B-lines, and never had the IVC."""
    import ast
    from pathlib import Path
    source = Path("app.py").read_text()
    nodes = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    namespace = {"re": re, "deepcopy": deepcopy, "__file__": "app.py"}
    import json, math, random
    namespace.update(json=json, math=math, random=random)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "app.py", "exec"), namespace)
    pocus = clinical_cases.FAMILIES["pulmonary_embolism"]["variants"][0]["investigations"]["pocus"]["result"]
    snapshot = {"sim_time": 10, "treatments": {}, "diagnostics": {"pocus": pocus},
                "observable": {"sbp": 110, "dbp": 70, "hr": 124, "spo2": 90, "crt": 3,
                               "respiratory_rate": 30, "mental_status": "Alert", "extremities": "Warm"}}
    text = namespace["_trace_state_text"](snapshot)
    for key in POCUS_KEYS:
        assert pocus[key] in text, key
