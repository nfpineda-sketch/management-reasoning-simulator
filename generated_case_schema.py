"""Data-only contract for newly AI-authored fictional adult ED encounters.

Clinical narratives and diagnoses are newly authored; executable capability is
explicitly bounded. Model output is data, never Python, expressions, or code.
Structural checks are software checks, not clinical validation.
"""
from copy import deepcopy
import math

from ecg12 import PROFILES, RHYTHMS
from visual_observations import VISUAL_CHOICES, PERFUSION_CATEGORIES

SCHEMA_VERSION = "mrs.generated.case.v1"
OBSERVED_NUMERIC = ("sbp", "dbp", "hr", "spo2", "respiratory_rate", "crt", "temperature_c", "glucose_mg_dl")
LAB_NUMERIC = ("hemoglobin_g_dl", "lactate_mmol_l", "pco2_mm_hg", "bicarbonate_mmol_l", "pao2_mm_hg")
NUMERIC_FIELDS = OBSERVED_NUMERIC + LAB_NUMERIC
BOUNDS = {"sbp": (35, 260), "dbp": (15, 150), "hr": (20, 250), "spo2": (50, 100),
          "respiratory_rate": (4, 60), "crt": (1, 10), "temperature_c": (32, 42),
          "glucose_mg_dl": (15, 800), "hemoglobin_g_dl": (2, 22), "lactate_mmol_l": (.4, 20),
          "pco2_mm_hg": (10, 120), "bicarbonate_mmol_l": (4, 45), "pao2_mm_hg": (20, 500)}
HISTORY_TOPICS = ("chief_complaint", "onset", "associated_symptoms", "medical_history", "medications",
                  "allergies", "risk_factors", "chest_pain", "breathing", "bleeding", "oral_intake",
                  "exposure", "urinary_symptoms", "neurological_symptoms", "leg_symptoms")
EXAM_AREAS = ("Cardiac", "Respiratory", "Abdomen", "Neurological", "General appearance", "Peripheral perfusion")
STUDIES = ("pocus", "lactate", "vbg", "abg", "basic_labs", "temperature", "poc_glucose", "chest_xray",
           "urinalysis", "blood_cultures", "troponin", "ctpa", "hemoglobin", "head_ct", "abdominal_ct",
           "cortisol", "thyroid_function", "ketones", "toxicology")
ACTIONS = ("fluid", "oxygen", "niv", "nitroglycerin", "antibiotics", "bronchodilator", "steroid", "dextrose",
           "naloxone", "blood", "ppi", "aspirin", "anticoagulation", "bag_mask", "intubation", "norepinephrine", "diuretic")


def obj(properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def enum(values):
    return {"type": "string", "enum": list(values)}


def array(items, minimum=0, maximum=30):
    return {"type": "array", "items": items, "minItems": minimum, "maxItems": maximum}


def nullable(schema):
    return {"anyOf": [schema, {"type": "null"}]}


TEXT = {"type": "string", "minLength": 1, "maxLength": 1600}
SHORT = {"type": "string", "minLength": 1, "maxLength": 160}
NUMBER = {"type": "number"}
BOOL = {"type": "boolean"}
VISUAL = obj({"expression": enum(VISUAL_CHOICES["expression"][:-1]),
              "skin_color": enum(VISUAL_CHOICES["skin_color"][:-1]),
              "diaphoresis": enum(VISUAL_CHOICES["diaphoresis"][:-1]), "mottling": BOOL})
STATE_TEXT = {"mental_status": enum(("Alert", "Drowsy", "Obtunded", "Unresponsive", "Sedated")),
              "work_of_breathing": enum(("Normal", "Reduced", "Mildly increased", "Increased", "Moderately increased", "Markedly increased", "Severe", "Ventilator-supported")),
              "extremities": enum(("Warm", "Cool", "Cold", "Mottled/cold")),
              "peripheral_perfusion": enum(PERFUSION_CATEGORIES), "pulse_present": BOOL,
              "rhythm": enum(tuple(RHYTHMS)), "ecg_profile": enum(PROFILES), "visual": VISUAL}
NUMERIC_PAIRS = array(obj({"field": enum(NUMERIC_FIELDS), "value": NUMBER}), maximum=13)
EXAM = array(obj({"area": enum(EXAM_AREAS), "finding": TEXT}), minimum=1, maximum=6)
CONDITION = obj({"field": enum(NUMERIC_FIELDS), "operator": enum(("lt", "lte", "gt", "gte")), "value": NUMBER})
RESPONSE_RULE = obj({
    "id": SHORT, "action_type": enum(ACTIONS), "agent": nullable(SHORT), "route": nullable(SHORT),
    "units": nullable(SHORT), "device": nullable(SHORT),
    "dose_field": nullable(enum(("dose_mg", "dose_g", "volume_ml", "units", "rate", "rate_mcg_min", "dose", "flow_lpm"))),
    "reference_dose": nullable({"type": "number", "exclusiveMinimum": 0, "maximum": 30000}),
    "onset_min": {"type": "integer", "minimum": 0, "maximum": 120},
    "duration_min": {"type": "integer", "minimum": 1, "maximum": 180},
    "max_exposure": {"type": "number", "minimum": .1, "maximum": 5},
    "delta": NUMERIC_PAIRS, "explanation": TEXT,
})
RESULT_FIELDS = ("report", "lv", "rv", "pericardium", "ivc", "lungs", "ph", "pco2_mm_hg", "paco2_mm_hg",
                 "pao2_mm_hg", "bicarbonate_mmol_l", "lactate_mmol_l", "fio2_percent", "sao2_percent",
                 "wbc_k_ul", "hemoglobin_g_dl", "platelets_k_ul", "sodium_mmol_l", "potassium_mmol_l",
                 "bun_mg_dl", "creatinine_mg_dl", "glucose_mg_dl", "temperature_c", "value_ng_l",
                 "upper_reference_ng_l", "cortisol_ug_dl", "tsh_miu_l", "free_t4_ng_dl", "ketones_mmol_l")
CASE_SCHEMA = obj({
    "schema_version": enum((SCHEMA_VERSION,)), "title": SHORT,
    "patient": obj({"age_years": {"type": "integer", "minimum": 18, "maximum": 100},
                    "sex": enum(("male", "female")), "pronouns": enum(("she/her", "he/him")),
                    "weight_kg": {"type": "number", "minimum": 35, "maximum": 200},
                    "comorbidities": array(SHORT, maximum=10)}),
    "presentation": {"type": "string", "minLength": 20, "maxLength": 500},
    "history_source": enum(("Patient", "Family", "EMS", "Caregiver")),
    "history": obj({topic: array(TEXT, minimum=1, maximum=5) for topic in HISTORY_TOPICS}),
    "examination": EXAM,
    "observable": obj({**{key: {"type": "number", "minimum": BOUNDS[key][0], "maximum": BOUNDS[key][1]} for key in OBSERVED_NUMERIC},
                       **{key: value for key, value in STATE_TEXT.items() if key != "ecg_profile"}}),
    "ecg_profile": enum(PROFILES),
    "investigations": array(obj({"id": enum(STUDIES), "duration_min": {"type": "integer", "minimum": 0, "maximum": 120},
                                "result": array(obj({"field": enum(RESULT_FIELDS), "value": {"anyOf": [TEXT, NUMBER]}}), minimum=1, maximum=25),
                                "result_bindings": array(obj({"field": enum(RESULT_FIELDS), "observable_field": enum(NUMERIC_FIELDS)}), maximum=13)}), minimum=4, maximum=19),
    "engine": obj({"model": enum(("declarative_v1",)),
                   "horizon_min": {"type": "integer", "minimum": 30, "maximum": 180},
                   "initial_labs": obj({key: {"type": "number", "minimum": BOUNDS[key][0], "maximum": BOUNDS[key][1]} for key in LAB_NUMERIC}),
                   "untreated_drift_per_min": NUMERIC_PAIRS,
                   "response_rules": array(RESPONSE_RULE, minimum=2, maximum=24),
                   "state_rules": array(obj({"id": SHORT, "when": array(CONDITION, minimum=1, maximum=6),
                                             "set": obj({key: nullable(value) for key, value in STATE_TEXT.items()}),
                                             "examination": nullable(EXAM)}), minimum=2, maximum=12)}),
    "faculty": obj({"diagnosis": TEXT, "management_focus": TEXT, "management_dilemma": TEXT,
                    "challenge_alignment": TEXT, "discriminating_findings": array(TEXT, minimum=2, maximum=8),
                    "review_questions": array(TEXT, minimum=2, maximum=5),
                    "anticipated_management_paths": array(TEXT, minimum=2, maximum=5),
                    "limitations": array(TEXT, minimum=1, maximum=8)})})
REVIEW_SCHEMA = obj({"coherent": BOOL,
                     "checks": obj({key: BOOL for key in ("challenge_alignment", "complete_truthful_facts", "management_dilemma",
                                        "baseline_clinical_coherence", "diagnostic_consistency", "ecg_capability_match",
                                        "visual_consistency", "treatment_response_plausibility", "state_transitions",
                                        "supported_management_paths", "no_diagnosis_or_bias_leak_in_arrival")}),
                     "issues": array(TEXT, maximum=20)})


class GeneratedCaseError(ValueError):
    """Safe learner/faculty-facing message; never contains provider payloads."""


def validate_schema(value, schema, path="case"):
    """Validate the emitted strict JSON subset without trusting provider parsing."""
    if "anyOf" in schema:
        for alternative in schema["anyOf"]:
            try:
                validate_schema(value, alternative, path)
                return
            except ValueError:
                pass
        raise ValueError(f"Invalid value at {path}.")
    kind = schema["type"]
    if kind == "object":
        if not isinstance(value, dict) or set(value) != set(schema["properties"]):
            raise ValueError(f"Invalid fields at {path}.")
        for key, sub in schema["properties"].items():
            validate_schema(value[key], sub, path + "." + key)
    elif kind == "array":
        if not isinstance(value, list) or not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", 100):
            raise ValueError(f"Invalid list at {path}.")
        for index, child in enumerate(value):
            validate_schema(child, schema["items"], f"{path}[{index}]")
    elif kind in ("number", "integer"):
        if type(value) not in ((int,) if kind == "integer" else (int, float)) or not math.isfinite(value):
            raise ValueError(f"Invalid number at {path}.")
        if value < schema.get("minimum", -math.inf) or value > schema.get("maximum", math.inf) or value <= schema.get("exclusiveMinimum", -math.inf):
            raise ValueError(f"Number outside bounds at {path}.")
    elif kind == "string":
        if not isinstance(value, str) or not schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", 2000):
            raise ValueError(f"Invalid text at {path}.")
    elif kind == "boolean":
        if type(value) is not bool:
            raise ValueError(f"Invalid flag at {path}.")
    elif kind == "null" and value is not None:
        raise ValueError(f"Invalid null at {path}.")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"Unknown value at {path}.")


def _pairs(items, key, value):
    keys = [item[key] for item in items]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate case fields are not permitted.")
    return {item[key]: deepcopy(item[value]) for item in items}


def compile_case(raw):
    """Translate schema arrays to immutable, existing encounter data contracts."""
    validate_schema(raw, CASE_SCHEMA)
    case = deepcopy(raw)
    case["examination"] = _pairs(raw["examination"], "area", "finding")
    studies = {}
    for study in raw["investigations"]:
        if study["id"] in studies:
            raise ValueError("Duplicate studies are not permitted.")
        studies[study["id"]] = {"duration_min": study["duration_min"],
                                "result": _pairs(study["result"], "field", "value"),
                                "result_bindings": _pairs(study["result_bindings"], "field", "observable_field")}
    case["investigations"] = studies
    engine = case["engine"]
    engine["untreated_drift_per_min"] = _pairs(engine["untreated_drift_per_min"], "field", "value")
    for rule in engine["response_rules"]:
        rule["delta"] = _pairs(rule["delta"], "field", "value")
        for key in tuple(rule):
            if rule[key] is None:
                rule.pop(key)
    for rule in engine["state_rules"]:
        rule["set"] = {key: value for key, value in rule["set"].items() if value is not None}
        if rule["examination"] is None:
            rule.pop("examination")
        else:
            rule["examination"] = _pairs(rule["examination"], "area", "finding")
    case["visual_profile"] = {"id": "ai_authored_visible_findings_v1", "baseline": deepcopy(case["observable"]["visual"]), "perfusion_appearance": {}}
    from generated_engine import diagnostic_bindings
    for study in case["investigations"].values():
        study["result_bindings"] = diagnostic_bindings(case, study)
    validate_clinical_structure(case)
    return case


def validate_clinical_structure(case):
    """Reject demonstrable numerical/contract contradictions before model review."""
    from generated_engine import validate_declarative_case
    from ecg12 import acquire_ecg
    o, patient = case["observable"], case["patient"]
    if o["sbp"] <= o["dbp"] + 10 or o["pulse_present"] is not True:
        raise ValueError("Initial circulation is outside the supported encounter contract.")
    if patient["pronouns"] != ("she/her" if patient["sex"] == "female" else "he/him"):
        raise ValueError("Patient description is inconsistent.")
    if len(case["examination"]) != len(EXAM_AREAS):
        raise ValueError("All examination areas must have explicit findings.")
    if not {"poc_glucose", "temperature", "basic_labs", "pocus"}.issubset(case["investigations"]):
        raise ValueError("The case is missing essential source investigations.")
    for study_id, measurement in (("poc_glucose", "glucose_mg_dl"), ("temperature", "temperature_c")):
        if measurement not in case["investigations"][study_id]["result"]:
            raise ValueError("Essential bedside studies require an explicit numerical measurement.")
    for test in case["investigations"].values():
        for field, bound in test.get("result_bindings", {}).items():
            expected = "pco2_mm_hg" if field == "paco2_mm_hg" else field
            if expected not in NUMERIC_FIELDS or bound != expected:
                raise ValueError("A diagnostic binding cannot substitute a different measurement.")
            if field not in test["result"] or type(test["result"][field]) not in (int, float):
                raise ValueError("A bound diagnostic must include its initial numerical result.")
            initial = o.get(bound, case["engine"]["initial_labs"].get(bound))
            if abs(test["result"][field] - initial) > .11:
                raise ValueError("Initial results conflict with the initial physiology.")
        result = test["result"]
        if all(field in result for field in ("ph", "bicarbonate_mmol_l")) and ("pco2_mm_hg" in result or "paco2_mm_hg" in result):
            co2 = result.get("pco2_mm_hg", result.get("paco2_mm_hg"))
            if not isinstance(co2, (int, float)) or co2 <= 0 or result["bicarbonate_mmol_l"] <= 0:
                raise ValueError("Invalid blood-gas values.")
            calculated = 6.1 + math.log10(result["bicarbonate_mmol_l"] / (.03 * co2))
            if abs(result["ph"] - calculated) > .08:
                raise ValueError("Blood-gas measurements are internally inconsistent.")
    electrical = acquire_ecg({"observable": o, "ecg_profile": case["ecg_profile"], "sim_time": 0, "seed": 1})
    if electrical.get("status") != "available":
        raise ValueError("The generated ECG cannot be represented coherently.")
    if o["mental_status"] in {"Obtunded", "Unresponsive", "Sedated"} and case["history_source"] == "Patient":
        raise ValueError("An unavailable patient cannot supply an intact initial history.")
    if o["peripheral_perfusion"] in {"severely impaired", "critical"} and o["visual"]["expression"] == "neutral":
        raise ValueError("The visual appearance conflicts with this severe presentation.")
    for rule in case["engine"]["state_rules"]:
        mental = rule["set"].get("mental_status")
        if mental is not None and mental != o["mental_status"] and "Neurological" not in rule.get("examination", {}):
            raise ValueError("A mental-status change requires a consistent neurological examination update.")
    validate_declarative_case(case)
