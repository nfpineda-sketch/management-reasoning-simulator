"""Data-only contract for newly AI-authored fictional adult ED encounters.

Clinical narratives and diagnoses are newly authored; executable capability is
explicitly bounded. Model output is data, never Python, expressions, or code.
Structural checks are software checks, not clinical validation.
"""
EXECUTION_VERSION = "0.24.2"

from copy import deepcopy
import math

from ecg12 import PROFILES, RHYTHMS
from clinical_core_defaults import CORE_VERSION, PHENOTYPE_FIELDS
from nitrate_hazard import CAUSES as NITRATE_HAZARD_CAUSES
from acs_reperfusion import TERRITORY_WALL as _CORONARY_WALLS

CORONARY_TERRITORIES = tuple(sorted(_CORONARY_WALLS))
from visual_observations import VISUAL_CHOICES, PERFUSION_CATEGORIES
from generated_case_validation import ContractValidationError

SCHEMA_VERSION = "mrs.generated.case.v3"
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
           "naloxone", "blood", "ppi", "aspirin", "anticoagulation", "bag_mask", "intubation", "norepinephrine", "dobutamine", "diuretic", "beta_blocker", "diltiazem", "amiodarone", "procedural_sedation", "cardioversion", "ventilator_adjustment", "magnesium", "thrombolysis", "octreotide", "glucagon", "thiamine")


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
              # The executor also reports "Very cold" and "Mottled/Cold" as
              # perfusion falls. Declaring only the first four made the shared
              # core violate the contract published to the author and reviewer.
              "extremities": enum(("Warm", "Warmer", "Cool", "Cold", "Very cold",
                                   "Mottled/cold", "Mottled/Cold")),
              "peripheral_perfusion": enum(PERFUSION_CATEGORIES), "pulse_present": BOOL,
              "rhythm": enum(tuple(RHYTHMS)), "ecg_profile": enum(PROFILES), "visual": VISUAL}
NUMERIC_PAIRS = array(obj({"field": enum(NUMERIC_FIELDS), "value": NUMBER}), maximum=13)
EXAM = array(obj({"area": enum(EXAM_AREAS), "finding": TEXT}), minimum=1, maximum=6)
from generated_physiology import VOLUME_FIELDS
DRIVER_FIELDS = NUMERIC_FIELDS + tuple(sorted(VOLUME_FIELDS))
CONDITION = obj({"field": enum(DRIVER_FIELDS + ("elapsed_min", "fluid_delivered_ml")), "operator": enum(("lt", "lte", "gt", "gte")), "value": NUMBER})
RESPONSE_RULE = obj({
    "id": SHORT, "action_type": enum(ACTIONS), "agent": nullable(SHORT), "route": nullable(SHORT),
    "units": nullable(SHORT), "device": nullable(SHORT),
    "dose_field": nullable(enum(("dose_mg", "dose_g", "volume_ml", "units", "rate", "rate_mcg_min", "dose", "flow_lpm"))),
    "settings": nullable(array(obj({"field": enum(("energy_j", "fio2_percent", "peep_cmh2o")), "value": NUMBER}), minimum=1, maximum=2)),
    "interpolate_settings": nullable(BOOL),
    "exposure_pool": nullable(SHORT),
    "volume_basis": nullable(enum(("circulating", "extravascular"))),
    "diuresis_ml_min": nullable({"type":"number", "minimum":0, "maximum":50}),
    "exposure_curve": nullable(obj({"saturating_weight":{"type":"number","minimum":0,"maximum":1}, "progressive_weight":{"type":"number","minimum":0,"maximum":1}, "rate":{"type":"number","minimum":.01,"maximum":10}, "power":{"type":"number","minimum":1,"maximum":3}, "onset_half_life_min":{"type":"number","minimum":.1,"maximum":120}, "elimination_half_life_min":{"type":"number","minimum":1,"maximum":1440}})),
    "washout_min": nullable({"type":"number", "minimum":1, "maximum":180}),
    "state_gain": nullable(obj({"field": enum(DRIVER_FIELDS + ("elapsed_min", "fluid_delivered_ml")), "points": array(obj({"value": NUMBER, "factor": {"type":"number", "minimum":0, "maximum":1}}), minimum=2, maximum=8)})),
    "recovery_min": nullable({"type":"number", "minimum":1, "maximum":180}),
    "mental_status_during": nullable(enum(("Sedated",))),
    "mental_status_threshold": nullable({"type":"number", "exclusiveMinimum":0, "maximum":5}),
    "rhythm_before": nullable(enum(tuple(k for k,v in RHYTHMS.items() if v not in {"vf", "asystole"}))),
    "recurrence": nullable(obj({"after_min":{"type":"integer", "minimum":1, "maximum":180}, "when":array(CONDITION, maximum=6), "rhythm_after":enum(tuple(k for k,v in RHYTHMS.items() if v not in {"vf", "asystole"})), "delta":NUMERIC_PAIRS})),
    "rhythm_after": nullable(enum(tuple(k for k,v in RHYTHMS.items() if v not in {"vf", "asystole"}))),
    "reference_dose": nullable({"type": "number", "exclusiveMinimum": 0, "maximum": 30000}),
    "onset_min": {"type": "integer", "minimum": 0, "maximum": 120},
    "duration_min": {"type": "integer", "minimum": 1, "maximum": 180},
    "max_exposure": {"type": "number", "minimum": .1, "maximum": 5},
    "delta": NUMERIC_PAIRS, "explanation": TEXT,
})
RESULT_FIELDS = ("report", "lv", "rv", "pericardium", "ivc", "lungs",
                 "lung_sliding", "lung_consolidation", "aorta_root", "aorta_descending",
                 "aorta_abdominal", "dvt_femoral", "dvt_popliteal", "ph", "pco2_mm_hg", "paco2_mm_hg",
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
    "engine": obj({"core_profile": obj({"version":enum((CORE_VERSION,)), "infection_active":BOOL, "initial_hidden":obj({k:{"type":"number","minimum":0,"maximum":1} for k in PHENOTYPE_FIELDS})}), "model": enum((CORE_VERSION,)),
                   "volume_model": nullable(obj({"initial_extravascular_ml":{"type":"number","minimum":0,"maximum":10000}, "redistribution_half_life_min":{"type":"number","minimum":1,"maximum":240}, "clearance_half_life_min":{"type":"number","minimum":1,"maximum":1440}, "extravascular_fraction":{"type":"number","minimum":0,"maximum":1}, "diuresis_extravascular_fraction":{"type":"number","minimum":0,"maximum":1}})),
                   "terminal_rule": nullable(obj({"when":array(obj({"field":enum(NUMERIC_FIELDS),"operator":enum(("lt","lte","gt","gte")),"value":NUMBER}),minimum=1,maximum=6), "sustained_min":{"type":"integer","minimum":1,"maximum":60}})),
                   "nitrate_hazard": nullable(obj({"cause": enum(tuple(NITRATE_HAZARD_CAUSES))})),
                   # An occlusion pattern on the ECG obliges this declaration, which runs
                   # the reperfusion pathway (acs_reperfusion) instead of authored rules.
                   "coronary": nullable(obj({"omi": BOOL, "active_occlusion": BOOL,
                                             "territory": enum(CORONARY_TERRITORIES),
                                             "rv_involvement": BOOL, "pci_capable": BOOL,
                                             "symptom_onset_min": {"type": "integer", "minimum": 0, "maximum": 1440}})),
                   "horizon_min": {"type": "integer", "minimum": 30, "maximum": 180},
                   "initial_labs": obj({key: {"type": "number", "minimum": BOUNDS[key][0], "maximum": BOUNDS[key][1]} for key in LAB_NUMERIC}),
                   "untreated_drift_per_min": NUMERIC_PAIRS,
                   "response_rules": array(RESPONSE_RULE, minimum=0, maximum=64),
                   "stable_diagnostics": array(enum(STUDIES), maximum=19),
                   "state_rules": array(obj({"id": SHORT, "when": array(CONDITION, minimum=1, maximum=6),
                                             "set": obj({key: nullable(value) for key, value in STATE_TEXT.items()}),
                                             "diagnostic_updates": nullable(array(obj({"diagnostic": enum(STUDIES), "findings": array(obj({"field": enum(("lv","rv","ivc","lungs","pericardium","report")), "value": TEXT}), minimum=1, maximum=6)}), minimum=1, maximum=19)),
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


def _duplicate_issues(raw):
    """Reject every ambiguous array before converting any duplicate to a dict."""
    issues = []

    def check(items, key, path, code="DUPLICATE_FIELD"):
        seen = {}
        for index, item in enumerate(items):
            name = item[key]
            if name in seen:
                issues.append({"code": code, "path": f"{path}[{index}].{key}",
                               "message": "Duplicate studies are not permitted." if code == "DUPLICATE_STUDY" else "Duplicate case fields are not permitted.",
                               "details": {"field": name, "first_index": seen[name], "duplicate_index": index}})
            else:
                seen[name] = index

    check(raw["examination"], "area", "case.examination")
    check(raw["investigations"], "id", "case.investigations", "DUPLICATE_STUDY")
    for index, study in enumerate(raw["investigations"]):
        for key in ("result", "result_bindings"):
            check(study[key], "field", f"case.investigations[{index}].{key}")
    check(raw["engine"]["untreated_drift_per_min"], "field", "case.engine.untreated_drift_per_min")
    for index, rule in enumerate(raw["engine"]["response_rules"]):
        check(rule["delta"], "field", f"case.engine.response_rules[{index}].delta")
    for index, rule in enumerate(raw["engine"]["state_rules"]):
        if rule["examination"] is not None:
            check(rule["examination"], "area", f"case.engine.state_rules[{index}].examination")
    return issues


def collect_clinical_issues(case):
    """Collect independent existing clinical contradictions without changing data.

    This receives a schema-validated case whose arrays have been normalized and
    whose bindings are still as authored. The final validators remain mandatory.
    """
    from ecg12 import acquire_ecg
    issues = []

    def add(code, path, message, **details):
        issues.append({"code": code, "path": path, "message": message, "details": details})

    def number(value):
        return type(value) in (int, float) and math.isfinite(value)

    observed, patient = case["observable"], case["patient"]
    if observed["sbp"] <= observed["dbp"] + 10 or observed["pulse_present"] is not True:
        add("INITIAL_CIRCULATION", "case.observable", "Initial circulation is outside the supported encounter contract.",
            sbp=observed["sbp"], dbp=observed["dbp"], pulse_present=observed["pulse_present"], minimum_pulse_pressure_exclusive=10)
    if patient["pronouns"] != ("she/her" if patient["sex"] == "female" else "he/him"):
        add("PATIENT_PRONOUNS", "case.patient.pronouns", "Patient description is inconsistent.", sex=patient["sex"], pronouns=patient["pronouns"])
    if len(case["examination"]) != len(EXAM_AREAS):
        add("EXAMINATION_INCOMPLETE", "case.examination", "All examination areas must have explicit findings.",
            missing_areas=sorted(set(EXAM_AREAS) - set(case["examination"])))
    studies = case["investigations"]
    for study_id in sorted({"poc_glucose", "temperature", "basic_labs", "pocus"} - set(studies)):
        add("ESSENTIAL_STUDY_MISSING", "case.investigations", "The case is missing an essential source investigation.", study_id=study_id)
    if "pocus" in studies:
        # The faculty's emergency POCUS protocol reports every structure, normal
        # findings included, so a generated case must document all of them.
        from pocus_report import missing_sections
        missing = missing_sections(studies["pocus"]["result"])
        if missing:
            add("POCUS_INCOMPLETE", "case.investigations.pocus.result",
                "POCUS must document every structure of the protocol, normal findings included: "
                "LV contractility, RV size and relation to LV, pericardium, IVC, pleural sliding, "
                "B-lines, consolidation and effusion, aortic root, descending and abdominal aorta, "
                "and femoral and popliteal vein compression. Report findings, not interpretation.",
                missing_fields=missing)
    # Nitroglycerin can collapse the pressure of a preload-dependent patient. The
    # case must declare such a condition exactly when it describes one.
    from nitrate_hazard import issues as nitrate_hazard_issues
    issues.extend(nitrate_hazard_issues(case))
    # The authored arrival POCUS must not contradict what the core derives from the drivers.
    # An ECG that shows an occluded artery obliges the coronary declaration.
    from generated_coronary_consistency import issues as coronary_issues
    issues.extend(coronary_issues(case))
    from generated_pocus_consistency import issues as pocus_core_issues
    issues.extend(pocus_core_issues(case))
    from generated_pocus_consistency import respiratory_issues
    issues.extend(respiratory_issues(case))
    for study_id, measurement in (("poc_glucose", "glucose_mg_dl"), ("temperature", "temperature_c")):
        if study_id in studies and measurement not in studies[study_id]["result"]:
            add("BEDSIDE_MEASUREMENT_MISSING", f"case.investigations.{study_id}.result", "Essential bedside studies require an explicit numerical measurement.", field=measurement)
    baseline = {key: observed[key] for key in OBSERVED_NUMERIC}
    baseline.update(case["engine"]["initial_labs"])
    for study_id, study in studies.items():
        result, bindings = study["result"], study["result_bindings"]
        path = f"case.investigations.{study_id}"
        for field, target in bindings.items():
            expected = "pco2_mm_hg" if field == "paco2_mm_hg" else field
            if field not in result or expected not in NUMERIC_FIELDS or target != expected:
                add("DIAGNOSTIC_BINDING", f"{path}.result_bindings.{field}", "A diagnostic binding cannot substitute a different measurement.",
                    field=field, declared_target=target, expected_target=expected if expected in NUMERIC_FIELDS else None,
                    result_present=field in result)
        # Include derived bindings: omission must never freeze a modeled result.
        for field, measured in result.items():
            target = "pco2_mm_hg" if field == "paco2_mm_hg" else field
            if target not in NUMERIC_FIELDS:
                continue
            initial = baseline.get(target)
            if not number(measured) or not number(initial):
                add("DIAGNOSTIC_NUMERIC", f"{path}.result.{field}", "Every modeled diagnostic needs a numerical initial physiological value.",
                    field=field, result=measured, baseline=initial)
            elif abs(measured - initial) > .11:
                add("DIAGNOSTIC_BASELINE", f"{path}.result.{field}", "Initial results conflict with the initial physiology.",
                    field=field, result=measured, baseline=initial, maximum_absolute_difference=.11)
        if all(field in result for field in ("ph", "bicarbonate_mmol_l")) and ("pco2_mm_hg" in result or "paco2_mm_hg" in result):
            co2 = result.get("pco2_mm_hg", result.get("paco2_mm_hg"))
            bicarbonate, ph = result["bicarbonate_mmol_l"], result["ph"]
            if not all(number(value) for value in (co2, bicarbonate, ph)) or co2 <= 0 or bicarbonate <= 0:
                add("BLOOD_GAS_NUMERIC", f"{path}.result", "Invalid blood-gas values: pH, bicarbonate and carbon dioxide must be numerical, with positive bicarbonate and carbon dioxide.",
                    ph=ph, bicarbonate_mmol_l=bicarbonate, pco2_mm_hg=co2)
            else:
                calculated = 6.1 + math.log10(bicarbonate / (.03 * co2))
                if abs(ph - calculated) > .08:
                    add("BLOOD_GAS_CONSISTENCY", f"{path}.result.ph", "Blood-gas measurements are internally inconsistent.",
                        ph=ph, calculated_ph=calculated, maximum_absolute_difference=.08)
    electrical = acquire_ecg({"observable": observed, "ecg_profile": case["ecg_profile"], "sim_time": 0, "seed": 1})
    if electrical.get("status") != "available":
        add("ECG_UNREPRESENTABLE", "case.ecg_profile", "The generated ECG cannot be represented coherently.",
            profile=case["ecg_profile"], rhythm=observed["rhythm"], hr=observed["hr"])
    if observed["mental_status"] in {"Obtunded", "Unresponsive", "Sedated"} and case["history_source"] == "Patient":
        add("HISTORY_SOURCE", "case.history_source", "An unavailable patient cannot supply an intact initial history.", mental_status=observed["mental_status"])
    if observed["peripheral_perfusion"] in {"severely impaired", "critical"} and observed["visual"]["expression"] == "neutral":
        add("VISUAL_PERFUSION", "case.observable.visual.expression", "The visual appearance conflicts with this severe presentation.",
            peripheral_perfusion=observed["peripheral_perfusion"], expression=observed["visual"]["expression"])
    for index, rule in enumerate(case["engine"]["state_rules"]):
        mental = rule["set"].get("mental_status")
        if mental is not None and mental != observed["mental_status"] and "Neurological" not in rule.get("examination", {}):
            add("NEUROLOGICAL_UPDATE", f"case.engine.state_rules[{index}].examination", "A mental-status change requires a consistent neurological examination update.",
                mental_status=mental, initial_mental_status=observed["mental_status"])
    return issues


def _normalize_case(raw):
    """Normalize structure only; output is NOT approved for an encounter."""
    validate_schema(raw, CASE_SCHEMA)
    duplicates = _duplicate_issues(raw)
    if duplicates:
        raise ContractValidationError(duplicates)
    case = deepcopy(raw)
    case["examination"] = _pairs(raw["examination"], "area", "finding")
    studies = {}
    for study in raw["investigations"]:
        if study["id"] in studies:
            raise ValueError("Duplicate studies are not permitted.")
        studies[study["id"]] = {"duration_min": study["duration_min"],
                                "result": _pairs(study["result"], "field", "value"),
                                "result_bindings": _pairs(study["result_bindings"], "field", "observable_field")}
    # Native laboratory studies use explicit authored baseline values, never
    # invented normal results. Keep authored studies and their validation intact.
    if raw['engine'].get('core_profile') is not None:
        labs = raw['engine']['initial_labs']
        for name, fields, delay in (
            ('vbg', ('pco2_mm_hg', 'bicarbonate_mmol_l', 'lactate_mmol_l'), 3),
            ('abg', ('pco2_mm_hg', 'bicarbonate_mmol_l', 'pao2_mm_hg'), 3),
            ('lactate', ('lactate_mmol_l',), 3),
        ):
            if name not in studies and all(field in labs for field in fields):
                studies[name] = {'duration_min': delay,
                                 'result': {field: labs[field] for field in fields},
                                 'result_bindings': {field: field for field in fields}}
    case["investigations"] = studies
    engine = case["engine"]
    engine["untreated_drift_per_min"] = _pairs(engine["untreated_drift_per_min"], "field", "value")
    for rule in engine["response_rules"]:
        rule["delta"] = _pairs(rule["delta"], "field", "value")
        if rule.get("recurrence") is not None:
            rule["recurrence"]["delta"] = _pairs(rule["recurrence"]["delta"], "field", "value")
        if rule.get("settings") is not None:
            fields = [item["field"] for item in rule["settings"]]
            if len(fields) != len(set(fields)):
                raise ValueError("Duplicate response settings are not permitted.")
            rule["settings"] = _pairs(rule["settings"], "field", "value")
        for key in tuple(rule):
            if rule[key] is None:
                rule.pop(key)
    for rule in engine["state_rules"]:
        updates = rule.get("diagnostic_updates")
        if updates is not None:
            if len({u["diagnostic"] for u in updates}) != len(updates) or any(len({f["field"] for f in u["findings"]}) != len(u["findings"]) for u in updates):
                raise ValueError("Duplicate dynamic diagnostic findings are not permitted.")
            rule["diagnostic_updates"] = {u["diagnostic"]: _pairs(u["findings"], "field", "value") for u in updates}
        else:
            rule.pop("diagnostic_updates", None)
        rule["set"] = {key: value for key, value in rule["set"].items() if value is not None}
        if rule["examination"] is None:
            rule.pop("examination")
        else:
            rule["examination"] = _pairs(rule["examination"], "area", "finding")
    case["visual_profile"] = {"id": "ai_authored_visible_findings_v1", "baseline": deepcopy(case["observable"]["visual"]), "perfusion_appearance": {}}
    return case


def compile_case(raw):
    """Normalize and pass every encounter validation gate."""
    case = _normalize_case(raw)
    from generated_engine_diagnostics import collect_declarative_issues
    from generated_case_coverage import (coverage_issues, unexecutable_path_issues,
                                         unmanageable_diagnosis_issues, untreated_window_issues)
    # Check auto-derived bindings too; omitted bindings cannot conceal conflicts.
    binding_issues = []
    from generated_engine import diagnostic_bindings
    for study_id, study in case['investigations'].items():
        try:
            study['result_bindings'] = diagnostic_bindings(case, study)
        except ValueError as exc:
            binding_issues.append({'code': 'DIAGNOSTIC_BINDING',
                'path': 'case.investigations.' + study_id,
                'message': str(exc), 'details': {}})
    issues = (binding_issues + collect_clinical_issues(case) + collect_declarative_issues(case)
              + coverage_issues(case) + unexecutable_path_issues(case)
              + unmanageable_diagnosis_issues(case) + untreated_window_issues(case))
    if issues:
        raise ContractValidationError(issues)
    from generated_engine import diagnostic_bindings
    try:
        for study in case["investigations"].values():
            study["result_bindings"] = diagnostic_bindings(case, study)
        validate_clinical_structure(case)
    except ValueError as exc:
        # Authoritative gates still reject if a new rule has not yet acquired
        # a dedicated collector. This private message is never a logging code.
        raise ContractValidationError([{"code": "CONTRACT_UNCLASSIFIED", "path": "case",
                                        "message": str(exc), "details": {}}]) from None
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
            if any(type(value) not in (int, float) or not math.isfinite(value) for value in (co2, result["bicarbonate_mmol_l"], result["ph"])) or co2 <= 0 or result["bicarbonate_mmol_l"] <= 0:
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
