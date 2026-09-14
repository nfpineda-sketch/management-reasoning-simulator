"""Bounded, case-specific teaching trajectories for the cognitive-case catalogue.

This is an authored educational model, not a clinical prediction model. Direction
of effects follows the cited case-bank sources and GINA/SSC/AHA guidance; numeric
magnitudes and timings are simulation parameters requiring faculty review. Bias
selection, learner scores and diagnostic labels never drive patient physiology.
Orders are validated as a whole before an isolated copy is executed and committed.
"""
from copy import deepcopy
import math

FAMILY_ENGINE_VERSION = 1
FAMILIES = frozenset({"pneumonia", "pulmonary_edema", "acs", "pulmonary_embolism", "asthma", "gi_bleed", "hypoglycemia", "opioid"})
_ROUTES = {"iv": "IV", "intravenous": "IV", "io": "IO", "intraosseous": "IO", "im": "IM", "intramuscular": "IM", "po": "PO", "oral": "PO", "in": "IN", "intranasal": "IN", "nebulized": "nebulized", "nebulised": "nebulized", "inhaled": "inhaled", "sc": "SC", "subcutaneous": "SC"}
_DEVICES = {"none": "Room air", "room air": "Room air", "nasal cannula": "Nasal cannula", "nc": "Nasal cannula", "non-rebreather mask": "Non-rebreather mask", "non rebreather mask": "Non-rebreather mask", "nrb": "Non-rebreather mask", "non-rebreather": "Non-rebreather mask", "simple mask": "Simple mask"}
# Reference exposures are authored adult teaching-model scales, not prescribing
# thresholds. They only prevent a tiny parsed dose producing a full-size effect;
# actual dose/route are retained and no intended order is silently substituted.
_EXPOSURE_MG = {
    "antibiotics": {"ceftriaxone": 1000, "azithromycin": 500,
                    "piperacillin-tazobactam": 4500, "vancomycin": 1000},
    "steroid": {"prednisone": 40, "methylprednisolone": 32,
                "hydrocortisone": 160, "dexamethasone": 6},
}
_MEDICINES = {
    "antibiotics": ({"IV", "IO", "PO"}, .01, 20000),
    "bronchodilator": ({"nebulized", "inhaled"}, .01, 20),
    "steroid": ({"IV", "IO", "PO"}, .01, 1000),
    "dextrose": ({"IV", "IO", "PO"}, .1, 50),
    "naloxone": ({"IV", "IO", "IM", "IN"}, .01, 10),
    "ppi": ({"IV", "PO"}, 1, 160),
    "aspirin": ({"PO"}, 1, 650),
    "diuretic": ({"IV", "PO"}, .1, 250),
    "beta_blocker": ({"IV", "PO"}, .001, 1000),
    "diltiazem": ({"IV", "PO"}, .001, 1000),
    "amiodarone": ({"IV", "PO"}, .001, 2000),
    "procedural_sedation": ({"IV", "IM", "IN"}, .001, 1000),
}


def _clamp(value, lower, upper):
    return min(upper, max(lower, float(value)))


def _number(value, lower, upper):
    return not isinstance(value, bool) and isinstance(value, (float, int)) and math.isfinite(value) and lower <= value <= upper


def _case(state):
    return state.get("encounter_spec", {}).get("clinical_case", {})


def _failure(message):
    return {"executed": False, "clarification": message, "action_summaries": [], "reassess_delay": None, "elapsed_min": 0}


def _validate(state, parsed):
    if isinstance(parsed, dict) and parsed.get("clarification"):
        return None, str(parsed["clarification"])
    actions = parsed.get("actions") if isinstance(parsed, dict) else None
    if not isinstance(actions, list) or not actions:
        return None, "Please specify a question, investigation, treatment, or reassessment."
    normalized = []
    validation_state = deepcopy(state)
    for raw in actions:
        if not isinstance(raw, dict):
            return None, "Please restate the order."
        from active_order_context import complete_active_order, remember_validated_support
        a, context_error = complete_active_order(validation_state, raw)
        if context_error:
            return None, context_error
        kind = a.get("type")
        if validation_state.get("family_state", {}).get("invasive") and kind in {"oxygen", "niv", "bag_mask"}:
            return None, "The patient is receiving invasive ventilation. Please specify ventilator settings or clarify the intended airway change."
        if kind in {"beta_blocker", "diltiazem", "amiodarone", "cardioversion", "procedural_sedation", "ventilator_adjustment", "dobutamine"} and state.get("engine_family") != "generated":
            return None, "This intervention requires a generated encounter with an explicit response rule."
        if kind == "clarification":
            return None, str(a.get("message") or "Please clarify the order before it is executed.")
        if kind == "diagnostic":
            study = _case(state).get("investigations", {}).get(a.get("diagnostic"), {})
            if str(study.get("result", {}).get("report", "")).startswith("No result is recorded"):
                return None, "That investigation has no available result in this encounter. It has not been reported as normal."
            if a.get("diagnostic") != "ecg" and a.get("diagnostic") not in _case(state).get("investigations", {}):
                return None, "That investigation is not available in this encounter. Please specify an available study."
        elif kind == "reassessment":
            if not _number(a.get("delay_min"), 0, 120):
                return None, "Specify a reassessment interval from 0 to 120 minutes."
            a["delay_min"] = int(math.ceil(a["delay_min"]))
        elif kind in _MEDICINES:
            field = "dose_g" if kind == "dextrose" else "dose_mg"
            routes, lower, upper = _MEDICINES[kind]
            if not _number(a.get(field), lower, upper):
                return None, f"Please specify or confirm the {kind} dose in {'grams' if field == 'dose_g' else 'milligrams'}."
            a["route"] = _ROUTES.get(str(a.get("route", "")).strip().lower())
            if a["route"] not in routes:
                return None, f"Please specify a supported route for {kind}."
            if kind not in {"dextrose", "naloxone", "aspirin"} and not str(a.get("agent", "")).strip():
                return None, f"Which {kind} medication would you like to administer?"
            if kind in _EXPOSURE_MG and str(a.get("agent", "")).lower() not in _EXPOSURE_MG[kind]:
                return None, f"The specified {kind} agent has no modeled response in this encounter. Please clarify the medication."
            if kind == "dextrose" and a["route"] == "PO" and str(state.get("observable", {}).get("mental_status", "")).lower() != "alert":
                return None, "The patient is not fully alert. Please clarify the intended route and airway protection before oral glucose."
        elif kind == "fluid":
            if not _number(a.get("volume_ml"), 1, 3000) or not a.get("fluid_type"):
                return None, "Specify the crystalloid and confirm the bolus volume in mL (up to 3000 mL per order)."
        elif kind == "cardioversion":
            if a.get("synchronized") is not True or not _number(a.get("energy_j"), 1, 360):
                return None, "Specify synchronized cardioversion and its energy in joules."
            if state.get("observable", {}).get("pulse_present") is not True:
                return None, "Cardioversion requires a pulse-present encounter."
        elif kind == "blood":
            if not _number(a.get("units"), 1, 4) or int(a["units"]) != a["units"]:
                return None, "Confirm the number of packed red-cell units (1–4 per order)."
        elif kind == "oxygen":
            a["device"] = _DEVICES.get(str(a.get("device", "")).strip().lower())
            if a["device"] is None:
                return None, "Specify nasal cannula, a simple mask, a non-rebreather mask, or room air."
            if a["device"] != "Room air" and not _number(a.get("flow_lpm"), .1, 15):
                return None, "Specify the oxygen flow in L/min."
        elif kind == "niv":
            a["operation"] = str(a.get("operation") or "start").lower()
            if a["operation"] not in {"start", "adjust", "continue", "stop"}:
                return None, "Specify whether to start, adjust, continue, or stop NIV."
            if a["operation"] != "stop":
                if not _number(a.get("epap_cmh2o"), 0, 20) or not _number(a.get("fio2_percent"), 21, 100):
                    return None, "Specify NIV expiratory pressure and FiO₂."
                a["mode"] = str(a.get("mode") or "BiPAP")
                if a["mode"].lower() not in {"cpap", "bipap"}:
                    return None, "Specify CPAP or BiPAP."
                if a["mode"].lower() == "bipap" and (not _number(a.get("ipap_cmh2o"), a["epap_cmh2o"], 35)):
                    return None, "Specify an inspiratory pressure at least as high as expiratory pressure."
        elif kind in {"nitroglycerin", "norepinephrine", "dobutamine"}:
            a["operation"] = str(a.get("operation") or "start").lower()
            if a["operation"] not in {"start", "adjust", "continue", "stop"}:
                return None, "Specify whether to start, adjust, continue, or stop the infusion."
            if a["operation"] != "stop":
                if kind == "nitroglycerin" and not _number(a.get("rate_mcg_min"), .1, 400):
                    return None, "Specify or confirm the nitroglycerin rate in mcg/min."
                if kind in {"norepinephrine", "dobutamine"}:
                    units = str(a.get("units", "")).lower().replace("μ", "u").replace("µ", "u")
                    aliases = {"mcg/min": "mcg/min", "ug/min": "mcg/min", "mcg/kg/min": "mcg/kg/min", "ug/kg/min": "mcg/kg/min"}
                    a["units"] = aliases.get(units)
                    if a["units"] is None or not _number(a.get("rate"), .001, (10000 if kind == "dobutamine" else 100) if a["units"] == "mcg/min" else (50 if kind == "dobutamine" else 1.5)):
                        return None, f"Specify or confirm {kind} dose and units (mcg/min or mcg/kg/min)."
        elif kind in {"intubation", "ventilator_adjustment"}:
            if not a.get("ventilator_mode") or not _number(a.get("fio2_percent"), 21, 100) or not _number(a.get("peep_cmh2o"), 0, 20):
                return None, "Specify initial ventilator mode, FiO₂ and PEEP."
        elif kind == "anticoagulation":
            a["route"] = _ROUTES.get(str(a.get("route", "")).strip().lower())
            if not a.get("agent") or not _number(a.get("dose"), .01, 30000) or a.get("units") not in {"mg", "units", "U", "IU"} or a["route"] not in {"IV", "SC", "PO"}:
                return None, "Specify anticoagulant, dose, dose units, and route."
        elif kind in {"consult", "reperfusion_referral"}:
            if not str(a.get("service") or a.get("destination") or "").strip():
                return None, "Which specialist or reperfusion service would you like to contact?"
        elif kind == "disposition":
            if not str(a.get("destination") or "").strip():
                return None, "Where would you like to transfer or admit the patient?"
        elif kind == "bag_mask":
            pass
        else:
            return None, f"The requested action ({str(kind)[:60]}) is not executable in this encounter. Please clarify the order."
        if a.get("administration_duration_min") is not None:
            if kind not in set(_MEDICINES) | {"fluid", "blood", "anticoagulation"} or not _number(a["administration_duration_min"], 1/60, 120):
                return None, "Specify a positive supported delivery duration for a fluid, blood or fixed-dose medication."
            if state.get("engine_family") != "generated":
                return None, "Timed administration is available in generated encounters."
        normalized.append(a)
        remember_validated_support(validation_state, a)
    return normalized, None


def _initialize(state):
    if state.get("family_state", {}).get("version") == FAMILY_ENGINE_VERSION:
        return
    case = _case(state)
    base = deepcopy(case.get("observable") or state.get("observable", {}))
    engine = case.get("engine", {})
    state["family_state"] = {
        "version": FAMILY_ENGINE_VERSION, "baseline": base, "elapsed": 0,
        "lung": 1.0, "circulation": 1.0, "obstruction": 1.0,
        "glucose": float(engine.get("baseline_glucose", base.get("glucose_mg_dl", 100))),
        "hemoglobin": float(engine.get("baseline_hemoglobin", 12)),
        "lactate": float(engine.get("baseline_lactate", 1.5)),
        "opioid": 1.0, "naloxone": 0.0, "bronchodilation": 0.0,
        "antibiotic_at": None, "steroid_at": None, "diuretic_at": None,
        "antibiotic_exposure": 0, "steroid_exposure": 0, "anticoagulant_exposure": 0,
        "diuretic_dose": 0, "nitroglycerin": 0, "norepinephrine": 0,
        "pending_fluid_ml": 0, "pending_blood_units": 0, "dextrose_g": 0,
        "blood_delivered_units": 0, "fluid_delivered_ml": 0,
        "oxygen_fio2": .21, "oxygen_device": "Room air", "niv": False,
        "invasive": False, "bag_mask": False, "consultations": [],
        "anticoagulated": False, "aspirin": False, "ppi": False,
        "recurrence_risk": bool(engine.get("recurrence_risk", False)),
    }
    state.setdefault("treatments", {})
    state["treatments"].setdefault("administered_medications", [])
    state.setdefault("diagnostics", {})
    state.setdefault("diagnostic_history", [])
    state.setdefault("hidden", {})


def _order(state, a):
    f = state["family_state"]
    tr = state["treatments"]
    kind = a["type"]
    duration = 1
    label = kind.replace("_", " ").capitalize()
    if kind == "cardioversion":
        tr.setdefault("cardioversions", []).append({"energy_j": a["energy_j"], "synchronized": True, "time_min": state.get("sim_time", 0)})
        label = f"Synchronized cardioversion delivered: {a['energy_j']:g} J"
        duration = 0
    elif kind in {"beta_blocker", "diltiazem", "amiodarone", "procedural_sedation"}:
        label = f"{a['agent']} {a['dose_mg']:g} mg {a['route']} administered"
        duration = 0
    elif kind == "fluid":
        f["pending_fluid_ml"] += a["volume_ml"]
        duration = math.ceil(a["volume_ml"] / 50)
        label = f"{a['fluid_type']} {a['volume_ml']:g} mL started"
    elif kind == "blood":
        f["pending_blood_units"] += a["units"]
        duration = int(30 * a["units"])
        label = f"Packed red cells: {a['units']:g} unit(s) ordered; transfusion started"
    elif kind == "dextrose":
        f["dextrose_g"] += a["dose_g"]
        duration = 3 if a["route"] in {"IV", "IO"} else 10
        label = f"Glucose {a['dose_g']:g} g {a['route']}"
    elif kind == "naloxone":
        f["naloxone"] += min(1.4, a["dose_mg"] / (.4 if a["route"] in {"IV", "IO"} else 2))
        duration = 2 if a["route"] in {"IV", "IO"} else 4
        label = f"Naloxone {a['dose_mg']:g} mg {a['route']}"
    elif kind == "bronchodilator":
        f["bronchodilation"] = min(1.3, f["bronchodilation"] + min(.8, a["dose_mg"] / 5))
        duration = 5
        label = f"{a['agent']} {a['dose_mg']:g} mg {a['route']}"
    elif kind in {"antibiotics", "steroid", "diuretic"}:
        field = {"antibiotics": "antibiotic_at", "steroid": "steroid_at", "diuretic": "diuretic_at"}[kind]
        if f[field] is None:
            f[field] = f["elapsed"]
        if kind == "diuretic":
            f["diuretic_dose"] += a["dose_mg"]
        else:
            exposure = "antibiotic_exposure" if kind == "antibiotics" else "steroid_exposure"
            f[exposure] = min(1, f[exposure] + a["dose_mg"] / _EXPOSURE_MG[kind][str(a["agent"]).lower()])
        tr[kind] = {"agent": a["agent"], "dose_mg": a["dose_mg"], "route": a["route"]}
        duration = 5
        label = f"{a['agent']} {a['dose_mg']:g} mg {a['route']} administered"
    elif kind in {"ppi", "aspirin", "anticoagulation"}:
        f[{"anticoagulation": "anticoagulated"}.get(kind, kind)] = True
        tr[kind] = deepcopy(a)
        if kind == "anticoagulation":
            scale = 5000 if a["units"] in {"units", "U", "IU"} else 70
            f["anticoagulant_exposure"] = min(1, f["anticoagulant_exposure"] + a["dose"] / scale)
        label = f"{a.get('agent', kind)} {a.get('dose_mg', a.get('dose')):g} {a.get('units', 'mg')} {a['route']} administered"
    elif kind == "oxygen":
        device = a["device"]
        fio2 = .21 if device == "Room air" else min(.45, .21 + .04 * a["flow_lpm"]) if device == "Nasal cannula" else .50 if device == "Simple mask" else .85
        f.update(oxygen_fio2=fio2, oxygen_device=device, bag_mask=False, niv=False)
        tr.update(bag_mask=False, niv=False)
        tr.update(oxygen=device != "Room air", oxygen_device=device, oxygen_flow_lpm=a.get("flow_lpm", 0))
        label = f"{device}" + (f" at {a['flow_lpm']:g} L/min" if device != "Room air" else "")
    elif kind == "niv":
        f["niv"] = a["operation"] != "stop"
        f["bag_mask"] = False
        tr["bag_mask"] = False
        tr["niv"] = f["niv"]
        tr.update(oxygen=False, oxygen_device="Room air", oxygen_flow_lpm=0)
        f["oxygen_device"] = "Room air"
        if f["niv"]:
            f["oxygen_fio2"] = a["fio2_percent"] / 100
            tr.update(niv_mode=a["mode"], niv_pressure_cmh2o=a["epap_cmh2o"], niv_ipap_cmh2o=a.get("ipap_cmh2o"), niv_epap_cmh2o=a["epap_cmh2o"], niv_fio2_percent=a["fio2_percent"])
        else:
            f["oxygen_fio2"] = .21
        label = f"NIV {a['operation']}" + (f": {a['mode']}, FiO₂ {a['fio2_percent']:g}%" if f["niv"] else "")
        duration = 3
    elif kind in {"nitroglycerin", "norepinephrine", "dobutamine"}:
        rate = 0 if a["operation"] == "stop" else a.get("rate_mcg_min", a.get("rate", 0))
        if kind in {"norepinephrine", "dobutamine"} and a.get("units") == "mcg/kg/min":
            rate *= _case(state).get("patient", {}).get("weight_kg", 70)
        f[kind] = rate
        tr[kind] = bool(rate)
        reported_rate = a.get("rate_mcg_min", a.get("rate", 0))
        reported_units = "mcg/min" if kind == "nitroglycerin" else a.get("units", "mcg/min")
        if kind == "nitroglycerin":
            tr["nitroglycerin_rate_mcg_min"] = reported_rate if rate else 0
        else:
            tr.update({kind + "_rate": reported_rate if rate else 0, kind + "_units": reported_units})
        label = f"{kind.capitalize()} {a['operation']}" + (f" at {reported_rate:g} {reported_units}" if rate else "")
    elif kind == "ventilator_adjustment":
        f["oxygen_fio2"] = a["fio2_percent"] / 100
        tr.update(ventilator_mode=a["ventilator_mode"], ventilator_fio2_percent=a["fio2_percent"], ventilator_peep_cmh2o=a["peep_cmh2o"])
        label = f"Ventilator settings: {a['ventilator_mode']}, FiO2 {a['fio2_percent']:g}%, PEEP {a['peep_cmh2o']:g}"
        duration = 0
    elif kind in {"bag_mask", "intubation"}:
        f["bag_mask"] = kind == "bag_mask"
        tr["bag_mask"] = f["bag_mask"]
        f["niv"] = False
        tr["niv"] = False
        tr.update(oxygen=False, oxygen_device="Room air", oxygen_flow_lpm=0)
        f["oxygen_device"] = "Room air"
        if kind == "intubation":
            f["invasive"] = True
            f["niv"] = False
            f["oxygen_fio2"] = a["fio2_percent"] / 100
            tr.update(invasive_ventilation=True, niv=False, ventilator_mode=a["ventilator_mode"], ventilator_fio2_percent=a["fio2_percent"], ventilator_peep_cmh2o=a["peep_cmh2o"])
            duration = 5
            label = "Intubation completed; invasive ventilation started"
        else:
            label = "Bag-mask assisted ventilation started"
            tr["bag_mask"] = True
            f["oxygen_fio2"] = .85
    elif kind in {"consult", "reperfusion_referral"}:
        service = str(a.get("service") or a.get("destination"))
        f["consultations"].append({"service": service, "time_min": state.get("sim_time", 0)})
        label = f"{service} contacted; definitive intervention has not yet occurred"
        duration = 0
    elif kind == "disposition":
        state["disposition"] = a["destination"]
        tr["disposition"] = a["destination"]
        f["handoff_requested"] = True
        label = f"Transfer/admission requested: {a['destination']}"
        duration = 0
    summary = {"type": kind, "label": label, "duration_min": duration}
    for key in ("agent", "dose_mg", "dose_g", "dose", "units", "route", "volume_ml", "fluid_type", "service", "destination", "device", "flow_lpm", "rate", "rate_mcg_min", "operation", "energy_j", "synchronized", "mode", "ipap_cmh2o", "epap_cmh2o", "fio2_percent", "ventilator_mode", "peep_cmh2o"):
        if key in a:
            summary[key] = a[key]
    if kind in _MEDICINES or kind == "anticoagulation":
        record = {key: deepcopy(summary[key]) for key in ("agent", "dose_mg", "dose_g", "dose", "units", "route") if key in summary}
        record.setdefault("agent", kind)
        record["time_min"] = int(state.get("sim_time", 0))
        tr["administered_medications"].append(record)
    if kind in {"oxygen", "niv", "norepinephrine", "nitroglycerin", "dobutamine", "ventilator_adjustment"}:
        tr.setdefault("active_orders", {})[kind] = deepcopy(a)
    tr.setdefault("order_history", []).append(deepcopy(a))
    if a.get("administration_duration_min") is not None:
        summary["administration_duration_min"] = a["administration_duration_min"]
        summary["duration_min"] = math.ceil(a["administration_duration_min"])
    return summary


def _minute(state):
    f, family = state["family_state"], state["engine_family"]
    f["elapsed"] += 1
    fluid = min(50, f["pending_fluid_ml"])
    blood = min(1 / 30, f["pending_blood_units"])
    glucose = min(10, f["dextrose_g"])
    f["pending_fluid_ml"] = max(0, f["pending_fluid_ml"] - fluid)
    f["pending_blood_units"] = max(0, f["pending_blood_units"] - blood)
    f["dextrose_g"] -= glucose
    f["blood_delivered_units"] += blood
    f["fluid_delivered_ml"] += fluid
    state["treatments"]["total_crystalloid_ml"] = round(f["fluid_delivered_ml"], 1)
    state["treatments"]["cumulative_crystalloid_ml"] = round(f["fluid_delivered_ml"], 1)
    state["treatments"]["packed_red_cells_units"] = round(f["blood_delivered_units"], 3)
    if family in {"pneumonia", "gi_bleed"}:
        f["circulation"] -= fluid * .00025 + blood * .36
    elif family in {"pulmonary_edema", "pulmonary_embolism"}:
        f["lung"] += fluid * .00015
        f["circulation"] += fluid * (.00005 if family == "pulmonary_embolism" else 0)
    f["hemoglobin"] += blood * .85
    f["glucose"] = min(350, f["glucose"] + glucose * 4)
    if family == "pneumonia":
        elapsed_abx = -1 if f["antibiotic_at"] is None else f["elapsed"] - f["antibiotic_at"]
        antibiotic_effect = 0 if elapsed_abx < 60 else .003 * f["antibiotic_exposure"]
        f["lung"] += .002 - antibiotic_effect
        f["circulation"] += .002 - antibiotic_effect
    elif family == "pulmonary_edema":
        f["lung"] += .003 - min(.012, f["nitroglycerin"] * .00012)
        if f["diuretic_at"] is not None and f["elapsed"] - f["diuretic_at"] >= 20:
            f["lung"] -= min(.006, f["diuretic_dose"] * .0001)
    elif family == "asthma":
        steroid_active = f["steroid_at"] is not None and f["elapsed"] - f["steroid_at"] >= 60
        f["obstruction"] += .002 - (.004 * f["steroid_exposure"] if steroid_active else 0)
    elif family == "gi_bleed":
        f["circulation"] += .003 + .002 * f["anticoagulant_exposure"]
        f["hemoglobin"] -= .009 + .006 * f["anticoagulant_exposure"]
    elif family == "hypoglycemia":
        f["glucose"] -= .6 if f["recurrence_risk"] else .08
    elif family == "opioid":
        f["opioid"] *= .999
    elif family in {"acs", "pulmonary_embolism"}:
        f["circulation"] += .001
    f["naloxone"] *= .975
    f["bronchodilation"] *= .986
    for key in {"lung", "circulation", "obstruction"}:
        f[key] = _clamp(f[key], .25, 1.9)
    f["glucose"] = _clamp(f["glucose"], 15, 350)
    f["hemoglobin"] = _clamp(f["hemoglobin"], 3, 18)


def _surface(state):
    f, family = state["family_state"], state["engine_family"]
    base = f["baseline"]
    o = state.setdefault("observable", {})
    circulation = f["circulation"]
    lung = f["lung"]
    effort = 1.0
    sbp = float(base.get("sbp", 110)) - (circulation - 1) * 45
    dbp = float(base.get("dbp", 70)) - (circulation - 1) * 25
    hr = float(base.get("hr", 100)) + (circulation - 1) * 25
    spo2 = float(base.get("spo2", 96))
    rr = float(base.get("respiratory_rate", 20))
    mental = str(base.get("mental_status", "Alert"))
    support = f["invasive"] or f["niv"] or f["bag_mask"]
    fio2 = max(f["oxygen_fio2"], .85 if f["bag_mask"] else .21)
    oxygen_gain = max(0, fio2 - .21) * (30 if family not in {"opioid"} else 22)
    if family in {"pneumonia", "pulmonary_edema"}:
        recruitment = .35 if f["niv"] else .48 if f["invasive"] else 0
        effective_lung = max(.25, lung - recruitment)
        spo2 -= (effective_lung - 1) * 18
        rr += (effective_lung - 1) * 18
        effort = effective_lung
        if family == "pulmonary_edema":
            pressure_reduction = min(65, f["nitroglycerin"] * .35)
            sbp -= pressure_reduction
            dbp -= pressure_reduction * .48
            hr -= max(0, 1 - effective_lung) * 15
    elif family == "asthma":
        obstruction = max(.2, f["obstruction"] - f["bronchodilation"])
        spo2 -= (obstruction - 1) * 14
        rr += (obstruction - 1) * 18
        hr += min(12, f["bronchodilation"] * 12)
        effort = obstruction
        if obstruction < .4 and spo2 + oxygen_gain >= 90:
            mental = "Alert"
    elif family == "hypoglycemia":
        mental = "Alert" if f["glucose"] >= 70 else "Drowsy" if f["glucose"] >= 45 else "Obtunded" if f["glucose"] >= 25 else "Unresponsive"
        if f["glucose"] >= 70:
            hr = max(72, float(base.get("hr", 100)) - 18)
    elif family == "opioid":
        suppression = max(0, f["opioid"] - f["naloxone"])
        rr = 14 - (14 - float(base.get("respiratory_rate", 6))) * suppression
        spo2 = 97 - (97 - float(base.get("spo2", 85))) * suppression
        mental = "Alert" if suppression < .2 else "Drowsy" if suppression < .55 else "Obtunded" if suppression < .95 else str(base.get("mental_status", "Obtunded"))
        effort = 1
        if f["bag_mask"] or f["invasive"]:
            spo2 = 96
            rr = 12
    elif family == "pulmonary_embolism":
        spo2 -= (circulation - 1) * 8
        rr += (circulation - 1) * 10
    # Supplemental oxygen changes oxygenation, not bronchospasm or respiratory drive.
    spo2 += oxygen_gain
    if family != "pulmonary_edema":
        sbp -= min(45, f["nitroglycerin"] * .3)
        dbp -= min(25, f["nitroglycerin"] * .15)
    vasopressor_boost = min(35, f["norepinephrine"] * 1.5)
    sbp += vasopressor_boost
    dbp += vasopressor_boost * .7
    # Pressure support does not independently clear authored peripheral findings.
    crt = _clamp(float(base.get("crt") or 2) + (circulation - 1) * 4, 2, 8)
    perfusion = "preserved" if crt < 2.6 else "mildly impaired" if crt < 3.5 else "impaired" if crt < 5.5 else "severely impaired" if crt < 7 else "critical"
    baseline_crt = float(base.get("crt") or 2)
    extremities = str(base.get("extremities", "Warm"))
    if abs(crt - baseline_crt) < .75:
        perfusion = str(base.get("peripheral_perfusion", perfusion))
    else:
        extremities = "Warm" if crt < 3 else "Cool" if crt < 5.5 else "Cold"
    spo2 = int(round(_clamp(spo2, 55, 99)))
    sbp = int(round(_clamp(sbp, 50, 240)))
    dbp = int(round(_clamp(dbp, 25, min(140, sbp - 15))))
    if spo2 < 80 or sbp < 65:
        mental = "Obtunded"
    elif (spo2 < 87 or sbp < 80) and mental == "Alert":
        mental = "Drowsy"
    if f["invasive"]:
        mental = "Sedated"
        wob = "Ventilator-supported"
    elif family == "opioid":
        spontaneous_rr = 14 - (14 - float(base.get("respiratory_rate", 6))) * max(0, f["opioid"] - f["naloxone"])
        wob = "Reduced" if spontaneous_rr < 10 else "Normal"
    elif family in {"pneumonia", "pulmonary_edema", "asthma"}:
        baseline_wob = str(base.get("work_of_breathing", "Normal"))
        levels = ["Normal", "Mildly increased", "Moderately increased", "Markedly increased", "Severe"]
        index = {"normal": 0, "mildly increased": 1, "increased": 2, "moderately increased": 2, "markedly increased": 3, "severe": 4}.get(baseline_wob.lower(), 2)
        change = int(round((effort - 1) * 3))
        wob = baseline_wob if change == 0 else levels[int(_clamp(index + change, 0, 4))]

    else:
        wob = str(base.get("work_of_breathing", "Normal"))
    o.update(sbp=sbp, dbp=dbp, map=int(round((sbp + 2 * dbp) / 3)), hr=int(round(_clamp(hr, 45, 180))), spo2=spo2,
             respiratory_rate=int(round(_clamp(rr, 3, 45))), work_of_breathing=wob, mental_status=mental,
             crt=round(crt, 1), peripheral_perfusion=perfusion, glucose_mg_dl=int(round(f["glucose"])),
             rhythm=str(base.get("rhythm", "Sinus rhythm")), pulse_present=True,
             extremities=extremities)
    if str(base.get("rhythm", "")).lower().startswith("sinus"):
        o["rhythm"] = "Sinus tachycardia" if o["hr"] > 100 else "Sinus bradycardia" if o["hr"] < 60 else "Sinus rhythm"
    o["respiratory_support"] = "Invasive ventilation" if f["invasive"] else "NIV" if f["niv"] else "Bag-mask ventilation" if f["bag_mask"] else f["oxygen_device"]
    # Explicit authored visual contract is kept separate from diagnostic text.
    if family == "hypoglycemia":
        authored = _case(state).get("visual_profile", {}).get("baseline", {})
        o["visual"] = {"expression": "neutral" if f["glucose"] >= 70 else "uncomfortable",
                       "diaphoresis": "absent" if f["glucose"] >= 70 else authored.get("diaphoresis", "mild")}
    elif family == "opioid":
        o["visual"] = {"expression": "neutral" if mental == "Alert" else "passive"}
    elif family == "gi_bleed":
        # This case explicitly authors pallor with low haemoglobin; correcting
        # arterial pressure or peripheral flow alone does not remove that cue.
        baseline_skin = _case(state).get("visual_profile", {}).get("baseline", {}).get("skin_color")
        if baseline_skin in {"mild pallor", "pallor"} and f["hemoglobin"] < 9:
            o["visual"] = {"skin_color": baseline_skin}
    elif family in {"asthma", "pulmonary_edema"}:
        baseline_visual = _case(state).get("visual_profile", {}).get("baseline", {})
        if effort < .55:
            o["visual"] = {"expression": "uncomfortable" if effort >= .3 else "neutral"}
            if baseline_visual.get("diaphoresis") in {"mild", "marked"}:
                o["visual"]["diaphoresis"] = "mild" if effort >= .3 else "absent"
        else:
            o.pop("visual", None)
    state["hidden"].update(tissue_perfusion=_clamp(1 - (crt - 2) / 8, .05, 1), effective_map=o["map"],
                           oxygen_delivery=_clamp((1 - (crt - 2) / 8) * spo2 / 100 * f["hemoglobin"] / 12, .02, 1.2),
                           pulmonary_congestion=_clamp(lung * .65, 0, 1) if family == "pulmonary_edema" else 0,
                           terminal_collapse=False)


def _diagnostic(state, diagnostic, duration):
    case, f = _case(state), state["family_state"]
    if diagnostic == "ecg":
        from ecg12 import acquire_ecg
        result = acquire_ecg(state)
        state["diagnostics"].setdefault("ecg", []).append(deepcopy(result))
        state["diagnostic_history"].append({"diagnostic_type": "ecg", "result": deepcopy(result)})
        return {"type": "diagnostic", "diagnostic_type": "ecg", "result": result, "duration_min": duration}
    result = deepcopy(case["investigations"][diagnostic]["result"])
    o = state["observable"]
    if diagnostic == "poc_glucose":
        result = {"glucose_mg_dl": o["glucose_mg_dl"], "report": f"Glucose {o['glucose_mg_dl']} mg/dL"}
    elif diagnostic == "temperature":
        result = {"temperature_c": o.get("temperature_c", 37), "report": f"Temperature {o.get('temperature_c', 37):g} °C"}
    elif diagnostic in {"hemoglobin", "basic_labs"}:
        if "hemoglobin_g_dl" in result or state["engine_family"] == "gi_bleed" or diagnostic == "hemoglobin":
            result["hemoglobin_g_dl"] = round(f["hemoglobin"], 1)
            # Replace stale prose carrying old values; preserve authored other fields.
            result["report"] = f"Hemoglobin {f['hemoglobin']:.1f} g/dL." + (" Other measured values are shown below." if diagnostic == "basic_labs" else "")
        if "glucose_mg_dl" in result:
            result["glucose_mg_dl"] = o["glucose_mg_dl"]
    elif diagnostic == "lactate":
        value = round(max(.8, f["lactate"] + (f["circulation"] - 1) * 2), 1)
        result = {"lactate_mmol_l": value, "report": f"Lactate {value:g} mmol/L"}
    elif diagnostic == "pocus":
        if state["engine_family"] == "pulmonary_edema":
            result["lungs"] = "Diffuse bilateral B-lines" if f["lung"] >= .65 else "Fewer but persistent bilateral B-lines"
        if "ivc" in result and state["engine_family"] in {"pneumonia", "gi_bleed"} and f["fluid_delivered_ml"] + f["blood_delivered_units"] * 300 >= 500:
            result["ivc"] = "IVC is less small than at presentation; interpret with the current support and the rest of the examination."
    elif diagnostic in {"vbg", "abg"}:
        respiratory_failure = state["engine_family"] in {"asthma", "opioid"}
        pco2 = float(result.get("pco2_mm_hg", result.get("paco2_mm_hg", result.get("pco2_mmhg", result.get("pco2", 40)))))
        if respiratory_failure:
            baseline_co2 = pco2
            bicarbonate = float(result.get("bicarbonate_mmol_l", .03 * baseline_co2 * 10 ** (float(result.get("ph", 7.4)) - 6.1)))
            factor = max(.15, f["obstruction"] - f["bronchodilation"]) if state["engine_family"] == "asthma" else max(.05, f["opioid"] - f["naloxone"])
            pco2 = 40 + (baseline_co2 - 40) * factor
            if state["engine_family"] == "asthma" and baseline_co2 < 40 and factor > 1.25:
                pco2 = baseline_co2 + (factor - 1.25) * 40

            if f["bag_mask"] or f["invasive"]:
                pco2 = min(pco2, 46)
            result["pco2_mm_hg" if diagnostic == "vbg" else "paco2_mm_hg"] = round(pco2)
            result["bicarbonate_mmol_l"] = round(bicarbonate, 1)
            result["ph"] = round(6.1 + math.log10(bicarbonate / (.03 * pco2)), 2)
        result["fio2_percent"] = round(f["oxygen_fio2"] * 100)
        if diagnostic == "abg":
            result["sao2_percent"] = o["spo2"]
            baseline_oxygen = float(result.get("pao2_mm_hg", 80))
            pao2 = round(_clamp(baseline_oxygen + (o["spo2"] - f["baseline"].get("spo2", o["spo2"])) * 2.0, 28, 180))
            result["pao2_mm_hg"] = pao2
            result["pf_ratio"] = round(pao2 / max(.21, f["oxygen_fio2"]))
        result.pop("report", None)
    result["time_min"] = int(state.get("sim_time", 0))
    state["diagnostics"][diagnostic] = deepcopy(result)
    state["diagnostic_history"].append({"diagnostic_type": diagnostic, "result": deepcopy(result)})
    return {"type": "diagnostic", "diagnostic_type": diagnostic, "result": result, "duration_min": duration}



def _release_diagnostic(state, summary, available_time):
    summary = deepcopy(summary)
    name, result = summary["diagnostic_type"], summary["result"]
    result["collected_at_min"] = result.get("acquired_at_minutes", result.get("time_min", available_time))
    result["time_min"] = int(available_time)
    if name == "ecg":
        state["diagnostics"].setdefault("ecg", []).append(deepcopy(result))
    else:
        state["diagnostics"][name] = deepcopy(result)
    state["diagnostic_history"].append({"diagnostic_type": name, "result": deepcopy(result)})
    return summary


def execute_family_bundle(state, parsed):
    """Execute a fully validated bundle atomically; all clocks are simulated minutes."""
    if state.get("engine_family") == "generated":
        from generated_engine import execute_generated_bundle
        return execute_generated_bundle(state, parsed)
    if state.get("engine_family") not in FAMILIES:
        return _failure("This encounter does not have a supported clinical trajectory.")
    actions, error = _validate(state, parsed)
    if error:
        return _failure(error)
    candidate = deepcopy(state)
    _initialize(candidate)
    summaries, diagnostic_orders = [], []
    collection_state = deepcopy(candidate)
    reassess = None
    for a in actions:
        if a["type"] == "reassessment":
            reassess = a["delay_min"]
        elif a["type"] == "diagnostic":
            delay = 1 if a["diagnostic"] == "ecg" else int(_case(candidate)["investigations"][a["diagnostic"]].get("duration_min", 0))
            delay = max(0, min(delay, 120))
            # A specimen records the patient at collection. Therapy during the
            # processing interval must not retrospectively change its result.
            diagnostic_orders.append((delay, _diagnostic(collection_state, a["diagnostic"], delay)))
        else:
            summaries.append(_order(candidate, a))
    diagnostic_delay = max((delay for delay, _ in diagnostic_orders), default=0)
    treatment_delay = max((s["duration_min"] for s in summaries), default=0)
    elapsed = max(diagnostic_delay, reassess if reassess is not None else treatment_delay)
    due = {}
    for delay, summary in diagnostic_orders:
        due.setdefault(delay, []).append(summary)
    for summary in due.get(0, []):
        summaries.append(_release_diagnostic(candidate, summary, candidate.get("sim_time", 0)))
    for minute in range(1, elapsed + 1):
        _minute(candidate)
        candidate["sim_time"] = int(candidate.get("sim_time", 0)) + 1
        _surface(candidate)
        for summary in due.get(minute, []):
            summaries.append(_release_diagnostic(candidate, summary, candidate["sim_time"]))
    if elapsed == 0 and summaries and any(s.get("type") not in {"consult", "reperfusion_referral", "disposition", "diagnostic"} for s in summaries):
        _surface(candidate)
    state.clear()
    state.update(candidate)
    return {"executed": True, "clarification": None, "action_summaries": summaries, "reassess_delay": reassess, "elapsed_min": elapsed}


def current_findings(state):
    """Current examination with authored case findings and evolving surfaces."""
    if state.get("engine_family") == "generated":
        from generated_engine import current_findings as generated_findings
        return generated_findings(state)
    o = state.get("observable", {})
    findings = deepcopy(_case(state).get("examination", {}))
    findings["General appearance"] = f"{o.get('mental_status', 'Not recorded')}. Respiratory effort: {o.get('work_of_breathing', 'Not recorded')}."
    findings["Peripheral perfusion"] = f"Capillary refill {o.get('crt', 'not measured')} s; extremities {str(o.get('extremities', 'not recorded')).lower()}."
    authored_neuro = findings.get("Neurological", "")
    import re
    pupils = " ".join(re.findall(r"\bpupils?[^.!?;]*[.!?]?", authored_neuro, flags=re.I)).strip()
    lateralizing = " ".join(re.findall(r"\b(?:no (?:lateralizing|lateralising|focal motor|focal neurological|focal neurologic)|moving all limbs)[^.!?;]*[.!?]?", authored_neuro, flags=re.I)).strip()
    findings["Neurological"] = f"Current mental status: {o.get('mental_status', 'not recorded')}." + (" The patient engages in conversation and follows commands." if o.get("mental_status") == "Alert" else " Engagement is reduced; interpret alongside respiratory and circulatory findings.")
    if pupils:
        findings["Neurological"] += " " + pupils
    if lateralizing:
        findings["Neurological"] += " " + lateralizing

    f = state.get("family_state", {})
    family = state.get("engine_family")
    if family == "asthma" and f:
        airflow = f["obstruction"] - f["bronchodilation"]
        findings["Respiratory"] = "Improved air entry with residual expiratory wheeze." if airflow < .65 else "Reduced bilateral air entry with prolonged expiration and wheeze."
    elif family == "pulmonary_edema" and f:
        findings["Respiratory"] = "Bilateral crackles remain, with reduced respiratory effort." if f["lung"] < .7 else "Bilateral inspiratory crackles with increased respiratory effort."
    elif family == "opioid":
        findings["Respiratory"] = f"Respiratory rate {o.get('respiratory_rate')} /min; " + ("assisted ventilation is in progress." if f.get("bag_mask") or f.get("invasive") else "breaths remain shallow." if o.get("respiratory_rate", 12) < 10 else "spontaneous breaths have greater depth.")
    return findings


def clinical_update(state):
    if state.get("engine_family") == "generated":
        from generated_engine import clinical_update as generated_update
        return generated_update(state)
    o = state.get("observable", {})
    return (f"BP {o.get('sbp')}/{o.get('dbp')} mmHg · HR {o.get('hr')}/min · "
            f"SpO₂ {o.get('spo2')}% · RR {o.get('respiratory_rate')}/min. "
            f"{o.get('mental_status', 'Not recorded')}; respiratory effort {str(o.get('work_of_breathing', 'not recorded')).lower()}; "
            f"capillary refill {o.get('crt')} s.")
