"""Bounded, case-specific teaching trajectories for the cognitive-case catalogue.

This is an authored educational model, not a clinical prediction model. Direction
of effects follows the cited case-bank sources and GINA/SSC/AHA guidance; numeric
magnitudes and timings are simulation parameters requiring faculty review. Bias
selection, learner scores and diagnostic labels never drive patient physiology.
Orders are validated as a whole before an isolated copy is executed and committed.
"""
EXECUTION_VERSION = "0.24.2"

from copy import deepcopy
import math

import acs_reperfusion
import asthma_complications
import asthma_ventilation
import glucose_rescue
import opioid_reversal
import airway_pharmacology
import antipyretics
import pe_obstruction
import re
import urine_output
import work_of_breathing

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
# Nursing and support orders: recorded, with a state, and no physiology of their
# own except the collection a catheter makes possible (faculty decision 13).
# The label is what the response card says after "After …", so it stays short;
# what the order does and does not do is said once, on its own line.
_SUPPORT_ORDERS = {
    "vascular_access": ("peripheral intravenous access", "placed", 3,
                        "Intravenous orders were already being given through a working line."),
    "monitoring": ("continuous monitoring and pulse oximetry", "started", 2,
                   "The monitor watches the patient and treats nothing."),
    "npo": ("nil by mouth", "recorded", 1, "Nothing is to be given by mouth."),
    "urinary_catheter": ("urinary catheter", "placed", 4,
                         "Urine is collected and measured from now on; the catheter does not make any."),
    "gastric_tube": ("nasogastric tube", "placed", 4, "What it is for belongs to the indication."),
}
_MEDICINES = {
    "antibiotics": ({"IV", "IO", "PO"}, .01, 20000),
    "bronchodilator": ({"nebulized", "inhaled"}, .01, 20),
    "steroid": ({"IV", "IO", "PO"}, .01, 1000),
    "dextrose": ({"IV", "IO", "PO"}, .1, 50),
    "naloxone": ({"IV", "IO", "IM", "IN"}, .01, 10),
    "atropine": ({"IV", "IO"}, .1, 3),
    "opioid_analgesia": ({"IV", "IO", "IM", "SC"}, .5, 30),
    "antipyretic": ({"IV", "IO", "PO", "IM"}, 10, 4000),
    "ppi": ({"IV", "PO"}, 1, 160),
    "aspirin": ({"PO"}, 1, 650),
    "diuretic": ({"IV", "PO"}, .1, 250),
    "beta_blocker": ({"IV", "PO"}, .001, 1000),
    "diltiazem": ({"IV", "PO"}, .001, 1000),
    "amiodarone": ({"IV", "PO"}, .001, 2000),
    "procedural_sedation": ({"IV", "IM", "IN"}, .001, 1000),
    "magnesium": ({"IV", "IO"}, 500, 4000),
    "thrombolysis": ({"IV", "IO"}, 5, 200),
    "octreotide": ({"SC", "IV", "IM"}, .025, .5),
    "glucagon": ({"IM", "IV", "IN", "SC"}, .5, 2),
    "thiamine": ({"IV", "IO", "IM"}, 50, 1000),
    # Induction and maintenance sedation are part of intubating an asthmatic, so
    # they are no longer restricted to generated encounters.
}

# Intravenous magnesium in severe asthma (faculty decision 2026-09-19): given
# before intubation, it adds a modest bronchodilation on top of the beta-agonist.
# Teaching magnitudes pending review.
# Faculty 2026-09-20: magnesium helps, but not as much as the other interventions.
MAGNESIUM = {"bronchodilation_per_g": .05, "max_bronchodilation": .12, "onset_min": 10}

# Diluted epinephrine in severe asthma (faculty decision 2026-09-19): 1 mg in
# 1000 mL as a drip, or 50-150 mcg IV boluses, before considering intubation. It
# bronchodilates and supports pressure at the cost of tachycardia. A bolus fades
# over minutes, so it has to be repeated or replaced by the drip. Magnitudes
# pending faculty review.
EPINEPHRINE = {
    "bolus_tau_min": 3.0,           # a bolus behaves like this many mcg/min while it lasts
    "bolus_equivalent_divisor": 3.0,
    "bronchodilation_per_mcg_min": .035, "max_bronchodilation": .45,
    "sbp_per_mcg_min": 1.2, "max_sbp": 30.0,
    "hr_per_mcg_min": 1.5, "max_hr": 25.0,
}

# Continuous nebulization holds the beta-agonist effect instead of letting each
# dose fade (faculty decision 2026-09-19).
CONTINUOUS_NEBULIZER = {"bronchodilation_per_mg_h": .09, "max_bronchodilation": 1.0, "tau_min": 10.0}

# A nebulized dose arrives over minutes and leaves faster than it used to: the
# faculty asked for the onset (2026-09-20) and for a quicker fade, so that
# continuous nebulization earns its place before ninety minutes.
BRONCHODILATOR_ONSET_MIN = 7.0
BRONCHODILATOR_DECAY_PER_MIN = .975

# Ketamine keeps airway reflexes and relaxes bronchial smooth muscle, so it is the
# preferred induction and maintenance agent in asthma (faculty decision 2026-09-19).
KETAMINE = {"bronchodilation_per_mg": .0015, "max_bronchodilation": .25, "tau_min": 45.0}

# The other induction agents drop the pressure of a preload-dependent, air-trapped
# asthmatic; ketamine and etomidate do not (faculty decision 2026-09-19).
SEDATION_BP_DROP_PER_MG = {"propofol": .12, "midazolam": .8, "fentanyl": .05}
SEDATION_BP_TAU_MIN = 15.0

# Share of each family's oxygenation defect that oxygen cannot fix (true shunt).
_OXYGEN_SHUNT = {"asthma": .30, "opioid": .10, "pneumonia": .60, "pulmonary_edema": .70,
                 "pulmonary_embolism": .45, "acs": .35, "gi_bleed": .20, "hypoglycemia": .20}


# Pulmonary oedema teaching magnitudes (docs/PULMONARY_EDEMA_PHYSIOLOGY_PROPOSAL.md,
# faculty decisions of 2026-09-18). "lung" is 1.0 at arrival and 0.25 when resolved.
EDEMA = {
    "drift_per_min": .003,               # untreated progression
    "resolved_drift_euvolemic": .001,    # once resolved, little recurrence without excess volume
    "fluid_per_ml": .0004,               # crystalloid worsens congestion...
    "fluid_on_positive_pressure": .4,    # ...less under NIV/invasive support, whose benefit dominates
    "niv_heal_per_min": .006,            # NIV itself resolves oedema (EPAP 5)...
    "niv_heal_per_epap": .0006,          # ...more with higher EPAP
    "nitro_lung_per_mcg": .00008,        # per mcg/min equivalent of nitroglycerin
    "nitro_lung_max": .02,
    "nitro_bolus_tau_min": 4.0,          # IV bolus effect decays with this time constant
    "nitro_bp_per_mcg": .35, "nitro_bp_max_fraction": .30, "nitro_bp_tau_min": 3.0,
    "congestion_bp_fraction": .10,       # sympathetic relief as congestion resolves
    "diuretic_onset_min": 30, "diuretic_per_mg": .00005, "diuretic_max": .004,
    "diuretic_resolved_lung": .65,       # before oedema resolves, furosemide has almost no effect
    "diuretic_early_factor": .1, "diuretic_euvolemic_factor": .25,
    "recruit_base": .20, "recruit_per_epap": .03, "recruit_max": .50,
    "pressure_support_rr_per_cm": 1.0, "epap_bp_per_cm": 1.5,
    "shunt_attenuation": .6, "rr_resolved": 16, "spo2_resolved": 97, "hr_relief": 20,
}


# Active GI bleeding (faculty request 2026-09-18): crystalloid alone must do less
# than blood. 2 L of saline used to restore pressure and refill almost as well as
# a transfusion, with only a 0.2 g/dL fall in haemoglobin. Magnitudes pending review.
GI_BLEED = {
    "crystalloid_per_ml": .00015,     # circulation gain per mL (other families: .00025)
    "crystalloid_transient": .6,      # share of that gain that redistributes out of the vessels...
    "crystalloid_leak_tau_min": 30.0, # ...with this time constant
    "hemodilution_g_dl_per_ml": .0006,  # 1 L of crystalloid dilutes haemoglobin by 0.6 g/dL
    "rr_per_circulation": 15.0,       # RR change per unit of circulation deficit (0 at arrival)
    "rr_floor": 14,
    # Hemostasis (faculty decision 2026-09-19). Gastroenterology performs the
    # endoscopy some time after the call, only once the patient is resuscitated
    # enough; until then it is deferred and re-checked. Pantoprazole slows the
    # bleeding a little, and only before endoscopy.
    "endoscopy_after_consult_min": 60,
    "endoscopy_retry_min": 15,
    "endoscopy_min_sbp": 90,
    "endoscopy_min_hemoglobin": 7.0,  # ...or blood still running
    "bleeding_after_hemostasis": .10,
    "bleeding_with_ppi": .80,
    # Once the bleeding is controlled and the anemia corrected, the compensatory
    # tachycardia eases (faculty decision 2026-09-19). The circulation variable
    # alone cannot show it: its floor (.25) holds the 57m at HR 105.
    "recovery_tau_min": 45.0,   # faculty 2026-09-20: the relief was too slow
    "recovery_min_hemoglobin": 7.0,
    "recovery_hr_relief": 20.0,
}

# Unfractionated heparin is cleared: a bolus given in error stops mattering, and
# stopping an infusion is a real decision (faculty decision 2026-09-19).
ANTICOAGULANT_TAU_MIN = 60.0

# Transfusing a patient who is not anaemic (faculty question 2026-09-20): a unit is
# about 300 mL that arrives quickly and stays in the vessels, so in a patient with no
# oxygen-carrying deficit the volume goes to the lungs. The consequence modelled is
# circulatory overload, which is the common and teachable one; a febrile reaction is
# frequent but random, and this engine is deterministic.
TRANSFUSION = {
    "unnecessary_above_g_dl": 10.0,   # no oxygen-carrying benefit at or above this
    "onset_min": 30,                  # the overload builds over half an hour
    "spo2_per_unit": 4.0,
    "rr_per_unit": 4.0,
    "congested_multiplier": 1.6,      # worse in a lung that is already wet
    "diuretic_relief_per_mg": .012,   # 40 mg of furosemide undoes about half a unit
    "max_units": 4.0,
}
TRANSFUSION_OVERLOAD_TEXT = (
    "Transfusion-associated circulatory overload: the haemoglobin was already adequate, so the units added volume "
    "rather than oxygen-carrying capacity. The saturation is falling and the breathing is faster, with crackles "
    "appearing at the bases. A diuretic treats it.")


def _clamp(value, lower, upper):
    return min(upper, max(lower, float(value)))


def _number(value, lower, upper):
    return not isinstance(value, bool) and isinstance(value, (float, int)) and math.isfinite(value) and lower <= value <= upper


def _case(state):
    return state.get("encounter_spec", {}).get("clinical_case", {})


NIV_ASSUMED_FIO2 = 100    # an NIV order without a stated FiO₂ runs at 100%

# A mental status the case authored as abnormal is a sign of the illness, so it
# must be able to answer treatment (faculty decision 2026-09-21). It recovers by
# one step, and only once the circulation and the oxygenation that explain it
# have been back for half an hour: the brain lags behind the haemodynamics.
MENTAL_RECOVERY = {"delay_min": 30, "spo2": 92, "sbp": 100, "crt_s": 3.5}
PNEUMONIA_WOB_PER_EFFORT = 6    # levels of respiratory effort per unit of lung burden
_MENTAL_LADDER = ("Unresponsive", "Obtunded", "Drowsy", "Alert")


def _perfusion_is_recovered(state):
    o = state.get("observable", {})
    return (float(o.get("spo2") or 0) >= MENTAL_RECOVERY["spo2"]
            and float(o.get("sbp") or 0) >= MENTAL_RECOVERY["sbp"]
            and float(o.get("crt") or 9) < MENTAL_RECOVERY["crt_s"])


def _mental_after_recovery(f, base_mental, mental):
    """One step up from the arrival state, never more, and never before its time."""
    if not f.get("mental_recovered"):
        return mental
    if base_mental not in _MENTAL_LADDER or base_mental == "Alert":
        return mental
    ceiling = _MENTAL_LADDER[min(_MENTAL_LADDER.index(base_mental) + 1, len(_MENTAL_LADDER) - 1)]
    if mental not in _MENTAL_LADDER:
        return mental
    return ceiling if _MENTAL_LADDER.index(mental) < _MENTAL_LADDER.index(ceiling) else mental


def _listed(items):
    """"a", "a and b", "a, b and c" — so a message names only what is missing."""
    items = list(items)
    if len(items) < 3:
        return " and ".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


# Everything given as a dose rather than run as an infusion or a setting.
_FIXED_DOSE_KINDS = frozenset(_MEDICINES) | {"anticoagulation", "ppi", "aspirin"}


def _already_given(state, kind, agent):
    """The minute a fixed-dose medicine was administered, or None.

    A continuation is a decision to change nothing, so it is answered from the
    record the way a repeated consult is, instead of demanding a new dose.
    """
    for record in reversed(state.get("treatments", {}).get("administered_medications", []) or []):
        if str(record.get("kind") or record.get("type") or "") == kind or (
                agent and str(record.get("agent", "")).lower() == str(agent).lower()):
            return int(record.get("time_min", 0))
    recorded = state.get("treatments", {}).get(kind)
    if isinstance(recorded, dict) and (not agent or str(recorded.get("agent", "")).lower() == str(agent).lower()):
        return int(recorded.get("time_min", 0))
    return None


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
        if a.get("dose_mg_per_kg") is not None and a.get("dose_mg") is None and kind != "neuromuscular_blockade":
            # "Ketamina 2 mg/kg" is a dose; the weight is the case's own.
            a = {**a, "dose_mg": round(a["dose_mg_per_kg"] * float(
                _case(validation_state).get("patient", {}).get("weight_kg") or 70), 3)}
        if validation_state.get("family_state", {}).get("invasive") and kind in {"oxygen", "niv", "bag_mask"}:
            return None, "The patient is receiving invasive ventilation. Please specify ventilator settings or clarify the intended airway change."
        # Ventilator settings are the treatment in a ventilated asthmatic.
        # Dobutamine left this set on 2026-09-21 (faculty decision 6): the
        # inotrope decision belongs to a cardiogenic shock in any engine.
        generated_only = {"beta_blocker", "diltiazem", "amiodarone", "cardioversion"}
        if state.get("engine_family") != "asthma":
            generated_only = generated_only | {"ventilator_adjustment"}
        if kind in generated_only and state.get("engine_family") != "generated":
            return None, "This intervention requires a generated encounter with an explicit response rule."
        if a.get("operation") == "continue" and kind in _FIXED_DOSE_KINDS:
            # A decision to change nothing is answered from the record, the way a
            # repeated consult is, instead of demanding a dose nobody meant to give.
            given = _already_given(validation_state, kind, a.get("agent"))
            if given is None:
                return None, (f"No {a.get('agent') or kind} is recorded as given. "
                              "Specify the dose and route to start it.")
            a["given_at_min"] = given
            normalized.append(a)
            continue
        if kind == "examination":
            regions = available_regions(validation_state)
            match = next((r for r in regions if r.lower() == str(a.get("region", "")).lower()), None)
            if match is None:
                return None, ("That examination is not available in this encounter. You may examine "
                              + ", ".join(regions[:-1]) + " or " + regions[-1] + ".")
            a["region"] = match
            normalized.append(a)
            continue
        if kind == "clarification":
            return None, str(a.get("message") or "Please clarify the order before it is executed.")
        if kind == "diagnostic":
            study = _case(state).get("investigations", {}).get(a.get("diagnostic"), {})
            if str(study.get("result", {}).get("report", "")).startswith("No result is recorded"):
                return None, "That investigation has no available result in this encounter. It has not been reported as normal."
            if a.get("diagnostic") != "ecg" and a.get("diagnostic") not in _case(state).get("investigations", {}):
                return None, f"Requested study {a.get('diagnostic')!r} is unavailable. Available studies: {', '.join(sorted(_case(state).get('investigations', {})))}; ecg. No orders in this submission were executed."
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
        elif kind == "fluid" and a.get("operation") == "stop":
            # "Stop further fluids" with nothing running withholds fluid; it is recorded, not questioned.
            pass
        elif kind == "fluid":
            if not a.get("fluid_type"):
                return None, "Which crystalloid would you like to give (for example, normal saline or LR)?"
            if not _number(a.get("volume_ml"), 1, 3000):
                return None, "Confirm the bolus volume in mL, up to 3000 mL per order."
            if a.get("route") is not None:
                a["route"] = _ROUTES.get(str(a["route"]).strip().lower())
                if a["route"] not in {"IV", "IO"}:
                    return None, "A crystalloid bolus is given IV or IO. Please specify the route."
        elif kind == "cardioversion":
            if a.get("synchronized") is not True:
                return None, "Specify that the cardioversion is synchronized; an unsynchronized shock is outside this encounter."
            if not _number(a.get("energy_j"), 1, 360):
                return None, "Specify the cardioversion energy in joules, from 1 to 360."
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
                if not _number(a.get("epap_cmh2o"), 0, 20):
                    return None, "Specify the NIV expiratory pressure in cm H₂O, from 0 to 20."
                if a.get("fio2_percent") is None:
                    # Faculty decision 2026-09-20: the resident connects the device
                    # and titrates afterwards, so an unstated FiO₂ is 100% and the
                    # response says so rather than holding the whole order.
                    a["fio2_percent"], a["fio2_assumed"] = float(NIV_ASSUMED_FIO2), True
                if not _number(a.get("fio2_percent"), 21, 100):
                    return None, "Specify the NIV FiO₂ as a percentage, from 21 to 100."
                a["mode"] = str(a.get("mode") or "BiPAP")
                if a["mode"].lower() not in {"cpap", "bipap"}:
                    return None, "Specify CPAP or BiPAP."
                if a["mode"].lower() == "bipap" and (not _number(a.get("ipap_cmh2o"), a["epap_cmh2o"], 35)):
                    return None, "Specify an inspiratory pressure at least as high as expiratory pressure."
        elif kind == "epinephrine_bolus":
            if not _number(a.get("dose_mcg"), 10, 500):
                return None, "Specify an epinephrine IV bolus from 10 to 500 mcg (50-150 mcg is the usual diluted bolus)."
            if str(a.get("route") or "IV").upper() != "IV":
                return None, "A diluted epinephrine bolus is given IV in this encounter."
            a["route"] = "IV"
        elif kind == "continuous_bronchodilator":
            a["operation"] = str(a.get("operation") or "start").lower()
            if a["operation"] not in {"start", "adjust", "continue", "stop"}:
                return None, "Specify whether to start, adjust, continue, or stop the continuous nebulization."
            if a["operation"] != "stop" and not _number(a.get("rate_mg_h"), 1, 30):
                return None, "Specify the continuous nebulized albuterol rate in mg/h (1 to 30)."
        elif kind == "nitroglycerin_bolus":
            if not _number(a.get("dose_mcg"), 50, 3000):
                return None, "Specify a nitroglycerin IV bolus from 50 to 3000 mcg."
            if str(a.get("route") or "IV").upper() != "IV":
                return None, "A nitroglycerin bolus is given IV in this encounter."
            a["route"] = "IV"
        elif kind in {"nitroglycerin", "norepinephrine", "dobutamine", "epinephrine"}:
            a["operation"] = str(a.get("operation") or "start").lower()
            if a["operation"] not in {"start", "adjust", "continue", "stop"}:
                return None, "Specify whether to start, adjust, continue, or stop the infusion."
            if a["operation"] != "stop":
                if kind == "nitroglycerin" and not _number(a.get("rate_mcg_min"), .1, 400):
                    return None, "Specify or confirm the nitroglycerin rate in mcg/min."
                if kind in {"norepinephrine", "dobutamine", "epinephrine"}:
                    units = str(a.get("units", "")).lower().replace("μ", "u").replace("µ", "u")
                    aliases = {"mcg/min": "mcg/min", "ug/min": "mcg/min", "mcg/kg/min": "mcg/kg/min", "ug/kg/min": "mcg/kg/min"}
                    a["units"] = aliases.get(units)
                    ceiling = {"dobutamine": (10000, 50), "norepinephrine": (100, 1.5), "epinephrine": (60, 1.0)}[kind]
                    if a["units"] is None or not _number(a.get("rate"), .001, ceiling[0] if a["units"] == "mcg/min" else ceiling[1]):
                        return None, f"Specify or confirm {kind} dose and units (mcg/min or mcg/kg/min)."
        elif kind == "oral_carbohydrate":
            mental = str(validation_state.get("observable", {}).get("mental_status"))
            if mental not in glucose_rescue.ORAL_SAFE_MENTAL:
                return None, (f"The patient is {mental.lower()} and cannot safely swallow. Use an intravenous or "
                              "intramuscular route until the airway is protected.")
        elif kind == "dextrose_infusion":
            a["operation"] = str(a.get("operation") or "start").lower()
            if a["operation"] != "stop" and not _number(a.get("rate_ml_h"), 10, 500):
                return None, "Specify the dextrose infusion rate in mL/h (10 to 500)."
        elif kind == "naloxone_infusion":
            a["operation"] = str(a.get("operation") or "start").lower()
            if a["operation"] != "stop" and not _number(a.get("rate_mg_h"), .05, 4):
                return None, "Specify the naloxone infusion rate in mg/h (0.05 to 4)."
        elif kind == "stress_test":
            if validation_state.get("engine_family") != "acs":
                return None, "A stress test is not an executable study in this encounter."
        elif kind == "chest_decompression":
            import generated_airway
            if validation_state.get("engine_family") != "asthma" and generated_airway.spec(validation_state) is None:
                return None, "Chest decompression is not an executable intervention in this encounter."
            if str(a.get("side")) not in {"left", "right"}:
                return None, "Specify which side of the chest to decompress."
        elif kind == "ventilator_disconnect":
            if not validation_state.get("family_state", {}).get("invasive"):
                return None, "The patient is not on a ventilator, so there is no circuit to disconnect."
        elif kind in {"intubation", "ventilator_adjustment"}:
            missing = [name for name, given in (("mode", a.get("ventilator_mode")),
                                               ("FiO₂ as a percentage", _number(a.get("fio2_percent"), 21, 100)),
                                               ("PEEP in cm H₂O", _number(a.get("peep_cmh2o"), 0, 20))) if not given]
            if missing:
                return None, "Specify the ventilator " + _listed(missing) + "."
            if a.get("tidal_volume_ml") is not None and not _number(a["tidal_volume_ml"], 200, 900):
                return None, "Specify a tidal volume from 200 to 900 mL."
            if a.get("tidal_ml_per_kg") is not None and not _number(a["tidal_ml_per_kg"], 3, 12):
                return None, "Specify a tidal volume from 3 to 12 mL/kg."
            if a.get("rate_per_min") is not None and not _number(a["rate_per_min"], 4, 35):
                return None, "Specify a ventilator rate from 4 to 35 breaths per minute."
            if a.get("flow_l_per_min") is not None and not _number(a["flow_l_per_min"], 20, 120):
                return None, "Specify an inspiratory flow from 20 to 120 L/min."
        elif kind == "anticoagulation":
            a["route"] = _ROUTES.get(str(a.get("route", "")).strip().lower())
            missing = [name for name, given in (("which anticoagulant", a.get("agent")),
                                               ("the dose", _number(a.get("dose"), .01, 30000)),
                                               ("the dose units", a.get("units") in {"mg", "units", "U", "IU"}),
                                               ("the route", a["route"] in {"IV", "SC", "PO"})) if not given]
            if missing:
                return None, "Specify " + _listed(missing) + "."
        elif kind in {"consult", "reperfusion_referral"}:
            if not str(a.get("service") or a.get("destination") or "").strip():
                return None, "Which specialist or reperfusion service would you like to contact?"
        elif kind == "disposition":
            if not str(a.get("destination") or "").strip():
                return None, "Where would you like to transfer or admit the patient?"
        elif kind in _SUPPORT_ORDERS:
            pass
        elif kind == "neuromuscular_blockade":
            if a.get("dose_mg") is None and a.get("dose_mg_per_kg") is None:
                return None, "Specify the neuromuscular blocker dose, in mg or mg/kg."
            if a.get("route") is None:
                # There is no other route for a blocker; asking would be a quibble.
                a = {**a, "route": "IV"}
            if a.get("route") not in {"IV", "IO"}:
                return None, "A neuromuscular blocker is given IV or IO, not by that route."
            if a.get("agent") not in airway_pharmacology.BLOCKERS:
                return None, "That neuromuscular blocker is not supported in this encounter."
        elif kind == "sedation_infusion":
            if a.get("operation") != "stop" and not a.get("rate"):
                return None, "Specify the infusion rate and its units (for example, propofol 2 mg/kg/h)."
        elif kind == "transcutaneous_pacing":
            import bradycardia_support
            if a.get("operation") != "stop":
                missing = [name for name, given in (("the pacing rate in beats per minute", a.get("rate_per_min")),
                                                    ("the output current in mA", a.get("output_ma"))) if given is None]
                # Choosing a rate is not pacing: without a current there is no
                # capture to confirm (faculty decision 5, 2026-09-21).
                if missing and a.get("operation") == "start":
                    return None, "Specify " + _listed(missing) + "."
                if a.get("rate_per_min") is not None and not _number(
                        a["rate_per_min"], bradycardia_support.PACING_MIN_RATE, bradycardia_support.PACING_MAX_RATE):
                    return None, (f"Set a pacing rate between {bradycardia_support.PACING_MIN_RATE} and "
                                  f"{bradycardia_support.PACING_MAX_RATE} beats per minute.")
                if a.get("output_ma") is not None and not _number(a["output_ma"], 1, bradycardia_support.PACING_MAX_MA):
                    return None, f"Set a pacing output between 1 and {bradycardia_support.PACING_MAX_MA} mA."
        elif kind in {"bag_mask", "airway_preparation"}:
            pass
        else:
            return None, f"The requested action ({str(kind)[:60]}) is not executable in this encounter. Please clarify the order."
        if a.get("administration_duration_min") is not None:
            if kind not in set(_MEDICINES) | {"fluid", "blood", "anticoagulation"} or not _number(a["administration_duration_min"], 1/60, 120):
                return None, "Specify a positive supported delivery duration for a fluid, blood or fixed-dose medication."
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
        "opioid_depot": float(engine.get("opioid_depot", 0.0)),
        "iv_access_failed": bool(engine.get("iv_access_failed")),
        "glycogen_depleted": bool(engine.get("glycogen_depleted")),
        "antibiotic_at": None, "steroid_at": None, "diuretic_at": None, "discharged_at": None,
        "antibiotic_exposure": 0, "steroid_exposure": 0, "anticoagulant_exposure": 0,
        "diuretic_dose": 0, "nitroglycerin": 0, "norepinephrine": 0, "epinephrine": 0,
        "dobutamine": 0, "dobutamine_effect": 0.0,
        "atropine_doses": [], "pacing_rate": None, "pacing_ma": None, "antipyretic_doses": [],
        "urine_ml": 0.0, "urine_since_report_ml": 0.0, "urine_report_min": 0,
        "urinary_catheter": False, "iv_access": True, "monitoring": False, "npo": False,
        "gastric_tube": False, "furosemide_doses": [],
        "morphine_mg": 0.0, "morphine_relief": 0.0, "morphine_preload_drop": 0.0,
        "morphine_reversed_mg": 0.0, "pain_baseline": None,
        "epi_bolus_pool": 0.0, "continuous_bronchodilator_mg_h": 0.0, "ketamine_mg": 0.0,
        "sedation_bp_drop": 0.0,
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


_TIMED_FIELD = {"fluid": "volume_ml", "blood": "units", "dextrose": "dose_g", "anticoagulation": "dose"}


def _medicine_effect(state, a, amount):
    """Apply ``amount`` of a medicine's modeled effect.

    An untimed order applies its whole dose at once, exactly as before. A timed
    order applies the part delivered in each simulated minute.
    """
    f, kind = state["family_state"], a["type"]
    if kind == "dextrose":
        # An ordered dose and a received dose are not the same thing when the
        # line is not in the vein (faculty decision 8, 2026-09-21).
        f["dextrose_g"] += amount * glucose_rescue.delivered_share(f, a.get("route"))
        f.setdefault("glucose_given_at", f["elapsed"])
    elif kind == "opioid_analgesia":
        # Fentanyl is written in mcg; 100 mcg is about 10 mg of morphine.
        f["morphine_mg"] = f.get("morphine_mg", 0.0) + (amount if a.get("agent") != "fentanyl" else amount * 10)
    elif kind == "naloxone":
        # 0.4 mg IV is one unit of antidote. Larger doses are not capped at the
        # ventilation target: pushing past it is how withdrawal is precipitated.
        f["naloxone"] = min(6.0, f["naloxone"] + amount / (.4 if a["route"] in {"IV", "IO"} else 2))
    elif kind == "bronchodilator":
        # Faculty decision 2026-09-20: no bronchodilator works in one minute. The dose
        # is held and released over its onset instead of landing at once.
        f["bronchodilator_pending"] = f.get("bronchodilator_pending", 0.0) + min(.8, amount / 5)
    elif kind == "magnesium":
        # Smooth-muscle relaxation adds to the beta-agonist rather than replacing it.
        f["magnesium_pending"] = f.get("magnesium_pending", 0.0) + amount / 1000
        f["magnesium_at"] = f["elapsed"]
    elif kind == "diuretic":
        f["diuretic_dose"] += amount
    elif kind in {"antibiotics", "steroid"}:
        exposure = "antibiotic_exposure" if kind == "antibiotics" else "steroid_exposure"
        f[exposure] = min(1, f[exposure] + amount / _EXPOSURE_MG[kind][str(a["agent"]).lower()])
    elif kind == "anticoagulation":
        scale = 5000 if a["units"] in {"units", "U", "IU"} else 70
        f["anticoagulant_exposure"] = min(1, f["anticoagulant_exposure"] + amount / scale)


def _store_ventilator_settings(tr, a):
    """Keep the settings the resident stated; the rest stay at the ventilator's defaults."""
    for field, key in (("tidal_volume_ml", "ventilator_tidal_volume_ml"), ("tidal_ml_per_kg", "ventilator_tidal_ml_per_kg"),
                       ("rate_per_min", "ventilator_rate_per_min"), ("flow_l_per_min", "ventilator_flow_l_per_min")):
        if a.get(field) is not None:
            tr[key] = a[field]
            if field == "tidal_volume_ml":
                tr.pop("ventilator_tidal_ml_per_kg", None)
            elif field == "tidal_ml_per_kg":
                tr.pop("ventilator_tidal_volume_ml", None)


def _settings_tail(tr):
    parts = []
    if tr.get("ventilator_tidal_volume_ml") is not None:
        parts.append(f"Vt {tr['ventilator_tidal_volume_ml']:g} mL")
    elif tr.get("ventilator_tidal_ml_per_kg") is not None:
        parts.append(f"Vt {tr['ventilator_tidal_ml_per_kg']:g} mL/kg")
    if tr.get("ventilator_rate_per_min") is not None:
        parts.append(f"rate {tr['ventilator_rate_per_min']:g}/min")
    if tr.get("ventilator_flow_l_per_min") is not None:
        parts.append(f"flow {tr['ventilator_flow_l_per_min']:g} L/min")
    return (", " + ", ".join(parts)) if parts else ""


def _queue_delivery(state, a, summary):
    """Deliver a timed order evenly over its stated duration on the simulation clock."""
    f, tr, kind = state["family_state"], state["treatments"], a["type"]
    field = _TIMED_FIELD.get(kind, "dose_mg")
    duration = float(a["administration_duration_min"])
    queue = f.setdefault("deliveries", [])
    key = [kind, a.get("agent")]
    # A second bag of the same order follows the first rather than doubling the rate.
    start = max([f["elapsed"]] + [item["start"] + item["duration"] for item in queue
                                  if item["key"] == key and item["delivered"] < item["amount"]])
    record_index = None
    if kind in _MEDICINES or kind == "anticoagulation":
        record_index = len(tr["administered_medications"]) - 1
        record = tr["administered_medications"][record_index]
        record["ordered_" + field] = a[field]
        record[field] = 0
        record["administration_duration_min"] = duration
        record["administration_status"] = "in_progress"
    queue.append({"key": key, "field": field, "amount": float(a[field]), "delivered": 0.0,
                  "start": start, "duration": duration, "record_index": record_index,
                  "action": deepcopy(a)})
    offset = int(state.get("sim_time", 0)) - f["elapsed"]
    summary["administration_duration_min"] = duration
    summary["delivery_starts_at_min"] = start + offset
    summary["delivery_due_at_min"] = start + offset + duration
    summary["duration_min"] = math.ceil(start - f["elapsed"] + duration)


def _advance_deliveries(state):
    """Deliver this minute's share of each timed order; return fluid and blood given."""
    f, tr = state["family_state"], state["treatments"]
    given = {"fluid": 0.0, "blood": 0.0}
    for item in f.get("deliveries", []):
        target = item["amount"] * min(1, max(0, (f["elapsed"] - item["start"]) / item["duration"]))
        change = target - item["delivered"]
        if change <= 0:
            continue
        item["delivered"] = target
        kind = item["key"][0]
        if kind in given:
            given[kind] += change
            continue
        _medicine_effect(state, item["action"], change)
        record = tr["administered_medications"][item["record_index"]]
        record[item["field"]] = round(target, 6)
        if target >= item["amount"]:
            record["administration_status"] = "completed"
            record["completed_at_min"] = int(state.get("sim_time", 0)) + 1
    return given


def _stop_fluid(state):
    """Stop every running crystalloid and return the volume that will not be given.

    Bank cases hold untimed volume in pending_fluid_ml and timed volume in the
    family_state queue; generated cases queue it in generated_state. Each queued
    bag is closed at what it has delivered, so its record stays true.
    """
    f = state["family_state"]
    remaining = max(0.0, float(f.get("pending_fluid_ml", 0)))
    f["pending_fluid_ml"] = 0
    for item in f.get("deliveries", []):
        if item["key"][0] == "fluid":
            item["amount"] = item["delivered"]
    g = state.get("generated_state") or {}
    for item in g.get("deliveries", []):
        if item["key"][0] == "fluid" and item["delivered"] < item["amount"]:
            elapsed = g.get("elapsed", 0) - item["start"]
            item["amount"] = item["delivered"]
            # Closing the bag at its elapsed time keeps the linear delivery formula at the amount given.
            if elapsed > 0:
                item["duration"] = elapsed
    return remaining


def _order(state, a):
    f = state["family_state"]
    tr = state["treatments"]
    kind = a["type"]
    if a.get("dose_mg_per_kg") is not None and a.get("dose_mg") is None and kind != "neuromuscular_blockade":
        # A dose written by weight is the same dose (faculty decision 11).
        a = {**a, "dose_mg": a["dose_mg_per_kg"] * float(_case(state).get("patient", {}).get("weight_kg") or 70)}
    # Generated cases schedule timed delivery in generated_delivery; only bank cases queue here.
    timed = a.get("administration_duration_min") is not None and state.get("engine_family") != "generated"
    duration = 1
    label = kind.replace("_", " ").capitalize()
    if kind == "airway_preparation":
        tr["airway_prepared"] = True
        label = "Airway equipment prepared; intubation has not occurred"
        duration = 2
    elif kind == "cardioversion":
        tr.setdefault("cardioversions", []).append({"energy_j": a["energy_j"], "synchronized": True, "time_min": state.get("sim_time", 0)})
        label = f"Synchronized cardioversion delivered: {a['energy_j']:g} J"
        duration = 0
    elif kind in {"beta_blocker", "diltiazem", "amiodarone", "procedural_sedation"}:
        if kind == "procedural_sedation":
            agent = str(a["agent"]).lower()
            if agent == "ketamine":
                # Ketamine also relaxes bronchial smooth muscle, which is why it is
                # the preferred induction and maintenance agent here.
                f["ketamine_mg"] = f.get("ketamine_mg", 0.0) + a["dose_mg"]
            f["sedation_at"] = f["elapsed"]
            drop = SEDATION_BP_DROP_PER_MG.get(agent, 0.0) * a["dose_mg"]
            f["sedation_bp_drop"] = f.get("sedation_bp_drop", 0.0) + drop
        label = f"{a['agent']} {a['dose_mg']:g} mg {a['route']} administered"
        duration = 0
    elif kind == "fluid" and a.get("operation") == "stop":
        remaining = _stop_fluid(state)
        label = (f"stopping crystalloid ({remaining:.0f} mL not given)" if remaining > 0
                 else "withholding further fluid (none was running)")
        duration = 0
    elif kind == "fluid":
        # The pending total includes timed volume, so the bedside shows what is still to run.
        f["pending_fluid_ml"] += a["volume_ml"]
        duration = math.ceil(a["volume_ml"] / 50)
        label = f"{a['fluid_type']} {a['volume_ml']:g} mL" + (f" {a['route']}" if a.get("route") else "") + " started"
    elif kind == "blood":
        f["pending_blood_units"] += a["units"]
        duration = int(30 * a["units"])
        label = f"Packed red cells {a['units']:g} unit{'' if a['units'] == 1 else 's'} started"
    elif kind == "dextrose":
        if f.get("iv_access_failed") and a.get("route") in {"IV", "IO"} and not f.get("failed_access_reported"):
            f["failed_access_reported"] = True
            f.setdefault("procedure_events", []).append(
                {"type": "procedure", "label": glucose_rescue.FAILED_ACCESS_TEXT,
                 "time_min": int(state.get("sim_time", 0)) + 1, "duration_min": 0})
        if not timed:
            _medicine_effect(state, a, a["dose_g"])
        duration = 3 if a["route"] in {"IV", "IO"} else 10
        label = f"Glucose {a['dose_g']:g} g {a['route']}"
    elif kind == "antipyretic":
        if a.get("route") == "PO" and str(state.get("observable", {}).get("mental_status") or "Alert") not in {
                "Alert", "Agitated"}:
            label = (f"{a.get('agent')} withheld by mouth: the patient is "
                     f"{str(state.get('observable', {}).get('mental_status')).lower()} and swallowing is not safe")
            withheld = True
            duration = 1
        else:
            caution = antipyretics.record_dose(state, a.get("agent"), a.get("dose_mg"), a.get("route"))
            label = f"{a.get('agent')} {a.get('dose_mg'):g} mg {a.get('route')} administered"
            if caution:
                f.setdefault("procedure_events", []).append(
                    {"type": "procedure", "label": caution,
                     "time_min": int(state.get("sim_time", 0)) + 1, "duration_min": 0})
            duration = 2 if a.get("route") in {"IV", "IO"} else 4
    elif kind == "opioid_analgesia":
        if not timed:
            _medicine_effect(state, a, a["dose_mg"])
        duration = 2 if a["route"] in {"IV", "IO"} else 5
        label = f"{a.get('agent', 'morphine')} {a['dose_mg']:g} mg {a['route']} administered"
    elif kind == "naloxone":
        if not timed:
            _medicine_effect(state, a, a["dose_mg"])
        # Naloxone answers whatever opioid is on board, including the one the
        # resident gave: the analgesia goes with the sedation.
        f["morphine_reversed_mg"] = float(f.get("morphine_mg") or 0)
        duration = 2 if a["route"] in {"IV", "IO"} else 4
        label = f"Naloxone {a['dose_mg']:g} mg {a['route']}"
    elif kind == "bronchodilator":
        if not timed:
            _medicine_effect(state, a, a["dose_mg"])
        duration = 5
        label = f"{a['agent']} {a['dose_mg']:g} mg {a['route']}"
    elif kind == "magnesium":
        if not timed:
            _medicine_effect(state, a, a["dose_mg"])
        duration = 5
        label = f"Magnesium sulfate {a['dose_mg'] / 1000:g} g {a['route']}"
    elif kind in {"antibiotics", "steroid", "diuretic"}:
        field = {"antibiotics": "antibiotic_at", "steroid": "steroid_at", "diuretic": "diuretic_at"}[kind]
        if f[field] is None:
            f[field] = f["elapsed"]
        if not timed:
            _medicine_effect(state, a, a["dose_mg"])
        if kind == "diuretic":
            urine_output.record_dose(state, a.get("dose_mg"), a.get("route"))
        if kind == "diuretic" and state.get("engine_family") == "pulmonary_edema":
            congestion = _case(state).get("engine", {}).get("congestion", {})
            factor = 1.0 if f["lung"] <= EDEMA["diuretic_resolved_lung"] else EDEMA["diuretic_early_factor"]
            factor *= 1.0 if congestion.get("volume_overload", True) else EDEMA["diuretic_euvolemic_factor"]
            f["diuretic_effective_mg"] = f.get("diuretic_effective_mg", 0.0) + a["dose_mg"] * factor
            f["diuretic_effective_at"] = f["elapsed"]
        tr[kind] = {"agent": a["agent"], "dose_mg": a["dose_mg"], "route": a["route"]}
        duration = 5
        label = f"{a['agent']} {a['dose_mg']:g} mg {a['route']} administered"
    elif a.get("operation") == "continue" and kind in _FIXED_DOSE_KINDS:
        agent = a.get("agent") or kind
        label = f"{agent} already given at minute {a.get('given_at_min', 0)}; not repeated"
        duration = 0
    elif kind in {"ppi", "aspirin", "anticoagulation"}:
        f[{"anticoagulation": "anticoagulated"}.get(kind, kind)] = True
        tr[kind] = deepcopy(a)
        if kind == "anticoagulation" and not timed:
            _medicine_effect(state, a, a["dose"])
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
        label = f"NIV {a['operation']}" + (f": {a['mode']}, FiO₂ {a['fio2_percent']:g}%"
                                           + (" (assumed; titrate as needed)" if a.get("fio2_assumed") else "")
                                           if f["niv"] else "")
        duration = 3
    elif kind == "epinephrine_bolus":
        f["epi_bolus_pool"] = f.get("epi_bolus_pool", 0.0) + a["dose_mcg"]
        tr["administered_medications"].append({"agent": "epinephrine", "dose": a["dose_mcg"], "units": "mcg",
                                               "route": "IV", "time_min": int(state.get("sim_time", 0))})
        label = f"Epinephrine {a['dose_mcg']:g} mcg IV bolus"
        duration = 1
    elif kind == "continuous_bronchodilator":
        rate = 0.0 if a["operation"] == "stop" else float(a["rate_mg_h"])
        running = f.get("continuous_bronchodilator_mg_h") or 0.0
        f["continuous_bronchodilator_mg_h"] = rate
        tr["continuous_bronchodilator"] = ({"agent": a["agent"], "rate_mg_h": rate, "route": a["route"]} if rate else None)
        if a["operation"] == "continue" and rate == running:
            label = f"Continuous nebulized {a['agent']} running at {rate:g} mg/h; unchanged"
        elif rate and running and rate != running:
            label = f"Continuous nebulized {a['agent']} adjusted to {rate:g} mg/h"
        else:
            label = (f"Continuous nebulized {a['agent']} {rate:g} mg/h started" if rate
                     else "Continuous nebulized albuterol stopped")
        duration = 3
    elif kind == "nitroglycerin_bolus":
        f["nitro_bolus_pool"] = f.get("nitro_bolus_pool", 0.0) + a["dose_mcg"]
        tr["administered_medications"].append({"agent": "nitroglycerin", "dose": a["dose_mcg"], "units": "mcg",
                                               "route": "IV", "time_min": int(state.get("sim_time", 0))})
        label = f"Nitroglycerin {a['dose_mcg']:g} mcg IV bolus"
        duration = 1
    elif kind in {"nitroglycerin", "norepinephrine", "dobutamine", "epinephrine"}:
        rate = 0 if a["operation"] == "stop" else a.get("rate_mcg_min", a.get("rate", 0))
        if kind in {"norepinephrine", "dobutamine", "epinephrine"} and a.get("units") == "mcg/kg/min":
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
    elif kind in _SUPPORT_ORDERS:
        name, done, minutes, note = _SUPPORT_ORDERS[kind]
        field = {"urinary_catheter": "urinary_catheter", "vascular_access": "iv_access",
                 "monitoring": "monitoring", "npo": "npo", "gastric_tube": "gastric_tube"}[kind]
        # A line that is there and does not run is not "already in place".
        already = bool(f.get(field)) and not (kind == "vascular_access" and f.get("iv_access_failed"))
        if a.get("operation") == "stop":
            f[field] = False
            label = f"{name} removed"
        else:
            f[field] = True
            label = f"{name} already in place; not repeated" if already else f"{name} {done}"
            replacing = kind == "vascular_access" and f.get("iv_access_failed")
            if not already and not replacing:
                f.setdefault("procedure_events", []).append(
                    {"type": "procedure", "label": note,
                     "time_min": int(state.get("sim_time", 0)), "duration_min": 0})
                if kind == "urinary_catheter":
                    # What was in the bladder before the catheter is drained now;
                    # it is not urine made during the collection that follows.
                    residual = float(f.get("urine_since_report_ml", 0.0))
                    f["urine_since_report_ml"] = 0.0
                    f["urine_report_min"] = 0
                    if residual >= 1:
                        f["procedure_events"][-1]["label"] += (
                            f" {residual:.0f} mL drained on placement, made before the catheter went in.")
        if kind == "vascular_access" and a.get("operation") != "stop" and f.get("iv_access_failed"):
            f["iv_access_failed"] = False
            label = "peripheral intravenous access replaced"
            f.setdefault("procedure_events", []).append(
                {"type": "procedure", "label": glucose_rescue.NEW_ACCESS_TEXT,
                 "time_min": int(state.get("sim_time", 0)), "duration_min": 0})
        tr.setdefault("support_orders", {})[kind] = bool(f.get(field))
        duration = 0 if already else minutes
    elif kind == "neuromuscular_blockade":
        weight = float(_case(state).get("patient", {}).get("weight_kg") or 70)
        onset, duration = airway_pharmacology.blocker_duration(
            a.get("agent"), a.get("dose_mg"), a.get("dose_mg_per_kg"), weight)
        f["paralysis_until"] = f["elapsed"] + onset + duration
        f["paralysis_unsedated_reported"] = False
        dose = (f"{a['dose_mg_per_kg']:g} mg/kg" if a.get("dose_mg_per_kg") is not None
                else f"{a.get('dose_mg', 0):g} mg")
        tr.setdefault("administered_medications", []).append(
            {"agent": a.get("agent"), "dose_mg": a.get("dose_mg"), "dose_mg_per_kg": a.get("dose_mg_per_kg"),
             "route": a.get("route"), "time_min": int(state.get("sim_time", 0))})
        label = (f"{a.get('agent')} {dose} {a.get('route')} administered: movement is abolished for about "
                 f"{duration:.0f} minutes. It does not sedate and it does not relieve pain.")
        duration = 2
    elif kind == "sedation_infusion":
        if a.get("operation") == "stop":
            f["sedation_infusion"] = None
            label = f"{a.get('agent')} infusion stopped"
        else:
            f["sedation_infusion"] = {"agent": a.get("agent"), "rate": a.get("rate"), "units": a.get("units")}
            verb = "adjusted to" if a.get("operation") == "adjust" else "started at"
            label = f"{a.get('agent')} infusion {verb} {a.get('rate'):g} {a.get('units')}"
            if a.get("agent") in airway_pharmacology.ANALGESIC_INFUSIONS:
                label += "; this is analgesia, not sedation"
        tr["sedation_infusion"] = bool(f.get("sedation_infusion"))
        duration = 2
    elif kind == "atropine":
        import bradycardia_support
        given = f.setdefault("atropine_doses", [])
        total = bradycardia_support.atropine_total_mg(f)
        spec = acs_reperfusion.coronary(state) or {}
        withheld = total + a["dose_mg"] > bradycardia_support.ATROPINE_MAX_MG + 1e-9
        if withheld:
            label = (f"atropine withheld: {total:g} mg has already been given and "
                     f"{bradycardia_support.ATROPINE_MAX_MG:g} mg is the maximum; this block needs pacing, "
                     "not more atropine")
        else:
            given.append({"index": len(given), "at": f["elapsed"], "dose_mg": a["dose_mg"]})
            label = f"atropine {a['dose_mg']:g} mg {a['route']} administered"
            if f.get("av_block_at") is not None and bradycardia_support.location(spec) == "infranodal":
                label += "; the atrial rate rises and the ventricular escape does not follow"
        duration = 1
    elif kind == "transcutaneous_pacing":
        import bradycardia_support
        if a.get("operation") == "stop":
            f.update(pacing_rate=None, pacing_ma=None)
            label = "transcutaneous pacing stopped"
        else:
            if a.get("rate_per_min") is not None:
                f["pacing_rate"] = float(a["rate_per_min"])
            if a.get("output_ma") is not None:
                f["pacing_ma"] = float(a["output_ma"])
            f.setdefault("pacing_threshold_ma", bradycardia_support.PACING_DEFAULT_THRESHOLD_MA)
            captured = bradycardia_support.capturing(f)
            label = f"transcutaneous pacing at {f.get('pacing_rate'):g}/min and {f.get('pacing_ma') or 0:g} mA"
            f.setdefault("procedure_events", []).append(
                {"type": "procedure", "time_min": int(state.get("sim_time", 0)), "duration_min": 0,
                 "label": ("Pacing spikes are followed by wide complexes and a palpable pulse: capture is confirmed."
                           if captured else
                           "Pacing spikes appear without a following complex: there is no capture at this output.")})
        tr["transcutaneous_pacing"] = bool(f.get("pacing_rate"))
        duration = 2
    elif kind == "dextrose_failed_access_marker":
        pass
    elif kind in {"octreotide", "glucagon", "thiamine"}:
        f[kind + "_at"] = f["elapsed"]
        if kind == "glucagon":
            f["glucagon_doses"] = f.get("glucagon_doses", 0) + 1
        tr.setdefault("administered_medications", []).append(
            {"agent": a["agent"], "dose_mg": a["dose_mg"], "route": a["route"], "time_min": int(state.get("sim_time", 0))})
        dose = f"{a['dose_mg'] * 1000:g} mcg" if kind == "octreotide" else f"{a['dose_mg']:g} mg"
        label = f"{a['agent']} {dose} {a['route']} administered"
        duration = 3 if kind != "glucagon" else 5
    elif kind == "oral_carbohydrate":
        f["oral_carbohydrate_at"] = f["elapsed"]
        label = "Oral carbohydrate given"
        duration = 3
    elif kind == "dextrose_infusion":
        rate = 0.0 if a["operation"] == "stop" else float(a["rate_ml_h"])
        f["dextrose_infusion_ml_h"] = rate
        tr["dextrose_infusion"] = ({"rate_ml_h": rate, "concentration_percent": a.get("concentration_percent", 10)}
                                   if rate else None)
        label = (f"Dextrose 10% at {rate:g} mL/h started" if rate else "Dextrose infusion stopped")
        duration = 3
    elif kind == "naloxone_infusion":
        rate = 0.0 if a["operation"] == "stop" else float(a["rate_mg_h"])
        f["naloxone_infusion_mg_h"] = rate
        tr["naloxone_infusion"] = {"rate_mg_h": rate} if rate else None
        label = (f"Naloxone infusion at {rate:g} mg/h started" if rate else "Naloxone infusion stopped")
        duration = 3
    elif kind == "thrombolysis" and (state.get("engine_family") == "pulmonary_embolism"
                                     or __import__("generated_pe").spec(state) is not None):
        note = pe_obstruction.give_thrombolysis(f, f["elapsed"], state.get("observable", {}))
        tr["administered_medications"].append({"agent": a["agent"], "dose_mg": a["dose_mg"], "route": a["route"],
                                               "time_min": int(state.get("sim_time", 0))})
        f.setdefault("procedure_events", []).append(
            {"type": "procedure", "label": note, "time_min": int(state.get("sim_time", 0)), "duration_min": 0})
        label = f"{a['agent']} {a['dose_mg']:g} mg {a['route']} given"
        duration = 5
    elif kind == "thrombolysis":
        spec = acs_reperfusion.coronary(state) or {}
        offset = int(state.get("sim_time", 0)) - f["elapsed"]
        if not spec.get("omi"):
            label = (f"{a['agent']} {a['dose_mg']:g} mg {a['route']} given: this ECG shows no occlusion pattern, so "
                     "thrombolysis carries its bleeding risk without an artery to open")
        elif acs_reperfusion.is_open(f):
            label = f"{a['agent']} {a['dose_mg']:g} mg {a['route']} given: the artery is already open"
        else:
            expected = acs_reperfusion.activate(f, spec, f["elapsed"], method="thrombolysis")
            label = (f"{a['agent']} {a['dose_mg']:g} mg {a['route']} given: reperfusion is expected at minute "
                     f"{expected + offset}")
        tr["administered_medications"].append({"agent": a["agent"], "dose_mg": a["dose_mg"], "route": a["route"],
                                               "time_min": int(state.get("sim_time", 0))})
        duration = 5
    elif kind == "stress_test":
        # Faculty decision: it is executed, and on an unstable occlusion it fibrillates.
        spec = acs_reperfusion.coronary(state) or {}
        if spec.get("omi") and not acs_reperfusion.is_open(f):
            f.setdefault("procedure_events", []).append(
                {"type": "procedure",
                 "label": acs_reperfusion.ventricular_fibrillation(f, "an exercise stress test on an unstable occlusion"),
                 "time_min": int(state.get("sim_time", 0)) + 10, "duration_min": 0})
            label = "Exercise stress test started"
        else:
            label = "Exercise stress test performed: no ischaemic change at the workload achieved"
        duration = 10
    elif kind == "chest_decompression":
        side, device = a["side"], a.get("device", "needle")
        if f.get("pneumothorax_at") is None:
            label = f"{device.capitalize()} decompression of the {side} chest: no air under tension was released"
        elif side != f.get("pneumothorax_side"):
            label = f"{device.capitalize()} decompression of the {side} chest: the pneumothorax is on the other side"
        else:
            f["pneumothorax_decompressed_at"] = f["elapsed"]
            label = (f"{device.capitalize()} decompression of the {side} chest: air under tension released; "
                     "the pressure and the saturation recover")
        duration = 3
    elif kind == "ventilator_disconnect":
        # Emptying the trapped gas is the manoeuvre for hyperinflation hypotension.
        f["circuit_disconnected_at"] = f["elapsed"]
        label = "Ventilator circuit disconnected; the chest is allowed to empty"
        duration = 1
    elif kind == "ventilator_adjustment":
        f["oxygen_fio2"] = a["fio2_percent"] / 100
        tr.update(ventilator_mode=a["ventilator_mode"], ventilator_fio2_percent=a["fio2_percent"], ventilator_peep_cmh2o=a["peep_cmh2o"])
        _store_ventilator_settings(tr, a)
        label = f"Ventilator settings: {a['ventilator_mode']}, FiO2 {a['fio2_percent']:g}%, PEEP {a['peep_cmh2o']:g}" + _settings_tail(tr)
        duration = 0
    elif kind in {"bag_mask", "intubation"}:
        f["bag_mask"] = kind == "bag_mask"
        tr["bag_mask"] = f["bag_mask"]
        f["niv"] = False
        tr["niv"] = False
        tr.update(oxygen=False, oxygen_device="Room air", oxygen_flow_lpm=0)
        f["oxygen_device"] = "Room air"
        if kind == "intubation":
            if state.get("engine_family") == "asthma":
                # The window is judged on the patient the resident had in front of them.
                obstruction = max(.2, f["obstruction"] - f["bronchodilation"] - _airway_relaxation(f))
                timing = asthma_complications.intubation_timing(f, state.get("observable", {}), obstruction)
                asthma_complications.apply_intubation_timing(f, timing)
                f.setdefault("procedure_events", []).append(
                    {"type": "procedure", "label": asthma_complications.timing_note(timing),
                     "time_min": int(state.get("sim_time", 0)), "duration_min": 0})
            f["invasive"] = True
            f["niv"] = False
            f["oxygen_fio2"] = a["fio2_percent"] / 100
            tr.update(invasive_ventilation=True, niv=False, ventilator_mode=a["ventilator_mode"], ventilator_fio2_percent=a["fio2_percent"], ventilator_peep_cmh2o=a["peep_cmh2o"])
            _store_ventilator_settings(tr, a)
            duration = 5
            label = "Intubation completed; invasive ventilation started" + _settings_tail(tr)
        else:
            label = "Bag-mask assisted ventilation started"
            tr["bag_mask"] = True
            f["oxygen_fio2"] = .85
    elif kind in {"consult", "reperfusion_referral"}:
        service = str(a.get("service") or a.get("destination"))
        pathway_note = None
        earlier = next((c for c in f["consultations"] if c["service"] == service), None)
        if earlier:
            # A repeated call is recorded as such, not as a second consultation.
            label = f"{service} already contacted at minute {earlier['time_min']}; not repeated"
        else:
            f["consultations"].append({"service": service, "time_min": state.get("sim_time", 0)})
            label = f"{service} contacted; definitive intervention has not yet occurred"
            spec = acs_reperfusion.coronary(state)
            if spec is not None and service == "cath lab":
                # Activating the cath lab starts the door-to-balloon clock.
                if spec.get("omi"):
                    acs_reperfusion.activate(f, spec, f["elapsed"], method="pci")
                # The short label belongs in "After ..., BP ..."; the pathway the ECG
                # dictates is reported as its own entry.
                pathway_note = acs_reperfusion.pathway_note(spec, f, int(state.get("sim_time", 0)))
                label = ("cath lab activated" if acs_reperfusion.active_occlusion(spec)
                         else "cath lab contacted for angiography" if spec.get("omi") else "cath lab contacted")
        duration = 0
    elif kind == "examination":
        label = examination_finding(state, a["region"])
        duration = 0
        examined = a["region"]
    elif kind == "disposition":
        repeated = tr.get("disposition") == a["destination"]
        state["disposition"] = a["destination"]
        tr["disposition"] = a["destination"]
        f["handoff_requested"] = True
        if a["destination"] == "home":
            f["discharged_at"] = f["elapsed"]
            f.pop("discharge_alarm_at", None)
            f.pop("discharge_return_reported", None)
            label = ("Discharge home already requested; not repeated" if repeated
                     else "Discharge home requested")
            # A patient who is already alarming when the discharge is written
            # comes back without waiting for the resident to let time run.
            _discharge_return(state)
        else:
            label = (f"Admission to {a['destination']} already requested; not repeated" if repeated
                     else f"Transfer/admission requested: {a['destination']}")
        duration = 0
    else:
        repeated = False
    pathway_note = pathway_note if kind in {"consult", "reperfusion_referral"} else None
    summary = {"type": kind, "label": label, "duration_min": duration}
    if kind == "examination":
        summary["region"] = a["region"]
        summary["time_min"] = int(state.get("sim_time", 0))
    if kind == "consult" and pathway_note:
        summary["pathway_note"] = pathway_note
    if kind in {"consult", "reperfusion_referral"} and earlier:
        summary["repeated"] = True
    if kind == "disposition" and repeated:
        summary["repeated"] = True
    for key in ("agent", "dose_mg", "dose_g", "dose", "units", "route", "volume_ml", "fluid_type", "service", "destination", "device", "flow_lpm", "rate", "rate_mcg_min", "operation", "energy_j", "synchronized", "mode", "ipap_cmh2o", "epap_cmh2o", "fio2_percent", "ventilator_mode", "peep_cmh2o"):
        if key in a:
            summary[key] = a[key]
    if ((kind in _MEDICINES or kind == "anticoagulation") and a.get("operation") != "continue"
            and not locals().get("withheld")):
        # A continuation gave nothing, so it is not an administration.
        record = {key: deepcopy(summary[key]) for key in ("agent", "dose_mg", "dose_g", "dose", "units", "route") if key in summary}
        record.setdefault("agent", kind)
        record["time_min"] = int(state.get("sim_time", 0))
        tr["administered_medications"].append(record)
    if kind in {"oxygen", "niv", "norepinephrine", "nitroglycerin", "dobutamine", "ventilator_adjustment"}:
        tr.setdefault("active_orders", {})[kind] = deepcopy(a)
    tr.setdefault("order_history", []).append(deepcopy(a))
    if a.get("administration_duration_min") is not None and not timed:
        summary["administration_duration_min"] = a["administration_duration_min"]
        summary["duration_min"] = math.ceil(a["administration_duration_min"])
    if timed:
        _queue_delivery(state, a, summary)
        summary["label"] = re.sub(r" (?:administered|started)$", "", summary["label"]) + \
            f" started over {summary['administration_duration_min']:g} min"
    return summary


def _nitro_equivalent(f):
    """Infusion rate plus the current effect of IV boluses, in mcg/min."""
    return f["nitroglycerin"] + f.get("nitro_bolus_pool", 0.0) / EDEMA["nitro_bolus_tau_min"]


def _edema_minute(state, fluid):
    f, tr, e = state["family_state"], state["treatments"], EDEMA
    congestion = _case(state).get("engine", {}).get("congestion", {})
    positive_pressure = f["niv"] or f["invasive"]
    resolved = f["lung"] <= e["diuretic_resolved_lung"]
    f["lung"] += (e["resolved_drift_euvolemic"] if resolved and not congestion.get("volume_overload", True)
                  else e["drift_per_min"])
    f["lung"] += fluid * e["fluid_per_ml"] * congestion.get("fluid_sensitivity", 1.0) * (
        e["fluid_on_positive_pressure"] if positive_pressure else 1)
    if f["niv"]:
        epap = float(tr.get("niv_epap_cmh2o") or 5)
        f["lung"] -= e["niv_heal_per_min"] + e["niv_heal_per_epap"] * max(0, epap - 5)
    equivalent = _nitro_equivalent(f)
    f["lung"] -= min(e["nitro_lung_max"], equivalent * e["nitro_lung_per_mcg"])
    if f.get("diuretic_effective_mg") and f["elapsed"] - f.get("diuretic_effective_at", 0) >= e["diuretic_onset_min"]:
        f["lung"] -= min(e["diuretic_max"], f["diuretic_effective_mg"] * e["diuretic_per_mg"])
    target = min(e["nitro_bp_max_fraction"] * float(f["baseline"].get("sbp", 120)), equivalent * e["nitro_bp_per_mcg"])
    effect = f.get("nitro_bp_effect", 0.0)
    f["nitro_bp_effect"] = effect + (target - effect) / e["nitro_bp_tau_min"]


def _gi_bleeding_fraction(f):
    """Share of the untreated bleeding rate that continues."""
    if f.get("endoscopy_at") is not None:
        return GI_BLEED["bleeding_after_hemostasis"]
    return GI_BLEED["bleeding_with_ppi"] if f.get("ppi") else 1.0


def _endoscopy_minute(state):
    """Perform or defer the endoscopy once gastroenterology has had time to come."""
    f, g = state["family_state"], GI_BLEED
    if f.get("endoscopy_at") is not None:
        return
    call = next((c for c in f["consultations"] if c["service"] == "gastroenterology"), None)
    now = int(state.get("sim_time", 0)) + 1  # the minute being simulated ends here
    if call is None or now < max(call["time_min"] + g["endoscopy_after_consult_min"], f.get("endoscopy_retry_at", 0)):
        return
    sbp = state.get("observable", {}).get("sbp", 0)
    transfusing = f["pending_blood_units"] > 0
    if sbp >= g["endoscopy_min_sbp"] and (f["hemoglobin"] >= g["endoscopy_min_hemoglobin"] or transfusing):
        f["endoscopy_at"] = now
        text = ("Gastroenterology performed upper endoscopy: bleeding ulcer treated endoscopically; "
                "active bleeding controlled. Rebleeding remains possible.")
    else:
        f["endoscopy_retry_at"] = now + g["endoscopy_retry_min"]
        reasons = ([f"SBP {sbp} mmHg"] if sbp < g["endoscopy_min_sbp"] else []) + \
                  ([f"hemoglobin {f['hemoglobin']:.1f} g/dL without blood running"]
                   if f["hemoglobin"] < g["endoscopy_min_hemoglobin"] and not transfusing else [])
        if f.get("endoscopy_deferral_reported"):
            return  # once per order; the 15-minute re-checks in between are silent
        f["endoscopy_deferral_reported"] = True
        text = (f"Gastroenterology is at the bedside but defers endoscopy until the patient is resuscitated "
                f"({', '.join(reasons)}); they will re-check every {g['endoscopy_retry_min']} minutes.")
    f.setdefault("procedure_events", []).append({"type": "procedure", "label": text, "time_min": now, "duration_min": 0})


# Faculty decision 2026-09-21: a discharge decided while the problem is still
# running is answered by the patient coming back, in a plausible time, rather
# than by the encounter simply ending. The engine keeps running the same
# physiology and watches for the finding that should have kept them in.
DISCHARGE_RETURN_DELAY_MIN = 20
_AWAKE = frozenset({"Alert", "Agitated", "Sedated", "Awake and fighting the ventilator"})


def _discharge_alarm(state):
    """What the patient was brought back with, or None while they are well."""
    o = state.get("observable", {}) or {}
    mental = str(o.get("mental_status") or "")
    glucose, rate = o.get("glucose_mg_dl"), o.get("respiratory_rate")
    if mental and mental not in _AWAKE:
        return f"found {mental.lower()} at home"
    if glucose is not None and glucose < 60:
        return f"unwell again, with a capillary glucose of {int(glucose)} mg/dL"
    if rate is not None and rate < 10:
        return f"breathing {rate:g} times a minute"
    if o.get("spo2") is not None and o["spo2"] < 90:
        return f"with a saturation of {o['spo2']:g}% on room air"
    if o.get("sbp") is not None and o["sbp"] < 90:
        return f"with a systolic pressure of {o['sbp']:g} mmHg"
    return None


def _discharge_return(state):
    f = state["family_state"]
    if f.get("discharged_at") is None or f.get("discharge_return_reported"):
        return
    if f.get("discharge_alarm_at") is None:
        alarm = _discharge_alarm(state)
        if alarm is None:
            return
        f["discharge_alarm_at"], f["discharge_alarm"] = f["elapsed"], alarm
    if f["elapsed"] - f["discharge_alarm_at"] < DISCHARGE_RETURN_DELAY_MIN:
        return
    f["discharge_return_reported"] = True
    f["discharged_at"] = None
    state["disposition"] = None
    state["treatments"]["disposition"] = None
    f.setdefault("procedure_events", []).append({
        "type": "procedure", "duration_min": 0,
        "time_min": int(state.get("sim_time", 0)) + DISCHARGE_RETURN_DELAY_MIN,
        "label": ("The patient was brought back to the emergency department after being sent home: "
                  + f["discharge_alarm"] + ". The problem that sent them home had not finished.")})


def _minute(state):
    f, family = state["family_state"], state["engine_family"]
    f["elapsed"] += 1
    # A minute of recovered perfusion counts, a minute without it discounts: a
    # one-mmHg wobble around the threshold must not restart the half hour. Once
    # the half hour is complete the patient is awake, and only a real
    # deterioration puts them back down, through the rules that already do that.
    f["perfusion_recovered_min"] = max(0, f.get("perfusion_recovered_min", 0)
                                       + (1 if _perfusion_is_recovered(state) else -1))
    if f["perfusion_recovered_min"] >= MENTAL_RECOVERY["delay_min"]:
        f["mental_recovered"] = True
    if f.get("deliveries"):
        # Timed volume runs at its own rate; any untimed bolus keeps running alongside.
        timed_remaining = {kind: sum(item["amount"] - item["delivered"] for item in f["deliveries"]
                                     if item["key"][0] == kind) for kind in ("fluid", "blood")}
        given = _advance_deliveries(state)
        fluid = given["fluid"] + min(50, max(0, f["pending_fluid_ml"] - timed_remaining["fluid"]))
        blood = given["blood"] + min(1 / 30, max(0, f["pending_blood_units"] - timed_remaining["blood"]))
        f["deliveries"] = [item for item in f["deliveries"] if item["delivered"] < item["amount"]]
    else:
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
    if family == "gi_bleed":
        g = GI_BLEED
        gain = fluid * g["crystalloid_per_ml"]
        f["circulation"] -= gain + blood * .36
        # Part of the crystalloid leaves the circulation; the pressure it bought fades.
        f["crystalloid_boost"] = f.get("crystalloid_boost", 0.0) + gain * g["crystalloid_transient"]
        leak = f["crystalloid_boost"] * (1 - math.exp(-1 / g["crystalloid_leak_tau_min"]))
        f["crystalloid_boost"] -= leak
        f["circulation"] += leak
        f["hemoglobin"] -= fluid * g["hemodilution_g_dl_per_ml"]
    elif family == "pneumonia":
        f["circulation"] -= fluid * .00025 + blood * .36
    elif family == "pulmonary_embolism":
        # Volume is neither the treatment nor the insult until it is given fast:
        # pe_obstruction prices the rate, not the total.
        event = pe_obstruction.step(state, fluid)
        if event:
            f.setdefault("procedure_events", []).append(
                {"type": "procedure", "label": event, "time_min": int(state.get("sim_time", 0)) + 1, "duration_min": 0})
    f["hemoglobin"] += blood * .85
    if blood:
        # Volume the patient did not need is volume all the same.
        if f["hemoglobin"] - blood * .85 >= TRANSFUSION["unnecessary_above_g_dl"]:
            f["transfusion_overload_units"] = min(TRANSFUSION["max_units"],
                                                  f.get("transfusion_overload_units", 0.0) + blood)
            f.setdefault("transfusion_overload_at", f["elapsed"])
    f["glucose"] = min(350, f["glucose"] + glucose * 4)
    if family == "pneumonia":
        elapsed_abx = -1 if f["antibiotic_at"] is None else f["elapsed"] - f["antibiotic_at"]
        antibiotic_effect = 0 if elapsed_abx < 60 else .003 * f["antibiotic_exposure"]
        f["lung"] += .002 - antibiotic_effect
        f["circulation"] += .002 - antibiotic_effect
    elif family == "pulmonary_edema":
        _edema_minute(state, fluid)
    elif family == "asthma":
        steroid_active = f["steroid_at"] is not None and f["elapsed"] - f["steroid_at"] >= 60
        f["obstruction"] += .002 - (.004 * f["steroid_exposure"] if steroid_active else 0)
        f["obstruction"] += asthma_complications.track_exhaustion(f, state.get("observable", {}))
        labs = _case(state).get("investigations", {}).get("basic_labs", {}).get("result", {})
        asthma_complications.step_beta_side_effects(
            f, _airway_relaxation(f), float(labs.get("potassium_mmol_l", 4.0)),
            float(_case(state).get("engine", {}).get("baseline_lactate", f["lactate"])))
        event = asthma_complications.step(f, f.get("ventilator_mechanics"))
        if event:
            f.setdefault("procedure_events", []).append(
                {"type": "procedure", "label": event, "time_min": int(state.get("sim_time", 0)) + 1, "duration_min": 0})
    elif family == "gi_bleed":
        _endoscopy_minute(state)
        # Recovery is conditional: it reverses if the bleeding is not controlled
        # or the anemia returns.
        recovering = f.get("endoscopy_at") is not None and f["hemoglobin"] >= GI_BLEED["recovery_min_hemoglobin"]
        relief = f.get("hemostasis_relief", 0.0)
        f["hemostasis_relief"] = relief + ((1 if recovering else 0) - relief) / GI_BLEED["recovery_tau_min"]
        bleeding = _gi_bleeding_fraction(f)
        f["circulation"] += (.003 + .002 * f["anticoagulant_exposure"]) * bleeding
        f["hemoglobin"] -= (.009 + .006 * f["anticoagulant_exposure"]) * bleeding
    elif family == "hypoglycemia":
        event = glucose_rescue.step(state)
        if event:
            f.setdefault("procedure_events", []).append(
                {"type": "procedure", "label": event, "time_min": int(state.get("sim_time", 0)) + 1, "duration_min": 0})
    elif family == "opioid":
        event = opioid_reversal.step(state)
        if event:
            f.setdefault("procedure_events", []).append(
                {"type": "procedure", "label": event, "time_min": int(state.get("sim_time", 0)) + 1, "duration_min": 0})
    elif family in {"acs", "pulmonary_embolism"}:
        f["circulation"] += acs_reperfusion.FAMILY_DRIFT_PER_MIN
        if family == "acs":
            spec = acs_reperfusion.coronary(state) or {}
            if spec.get("omi") and (acs_reperfusion.is_open(f)
                                    or not acs_reperfusion.active_occlusion(spec)):
                # Nothing is infarcting: the artery is open, either because the
                # resident opened it or because this lesion never occluded
                # (Wellens). The drift of an infarct in progress does not apply.
                f["circulation"] -= acs_reperfusion.FAMILY_DRIFT_PER_MIN
            if spec.get("rv_involvement"):
                # A preload-dependent right ventricle: nitroglycerin can collapse it.
                acs_reperfusion.nitrate_drop(f, _nitro_equivalent(f), float(f["baseline"].get("sbp", 120)), fluid)
            # Volume answers to the haemodynamics, not to having had a nitrate
            # first (faculty decision 4, 2026-09-21).
            import preload_response
            overload = preload_response.step(state, spec, fluid)
            if overload:
                f.setdefault("procedure_events", []).append(
                    {"type": "procedure", "label": overload,
                     "time_min": int(state.get("sim_time", 0)) + 1, "duration_min": 0})
            event = acs_reperfusion.step(state)
            if event:
                f.setdefault("procedure_events", []).append(
                    {"type": "procedure", "label": event, "time_min": int(state.get("sim_time", 0)) + 1, "duration_min": 0})
    urine_event = urine_output.step(state)
    if urine_event:
        f.setdefault("procedure_events", []).append(
            {"type": "procedure", "label": urine_event, "time_min": int(state.get("sim_time", 0)) + 1, "duration_min": 0})
    airway_event = airway_pharmacology.step(state)
    if airway_event:
        f.setdefault("procedure_events", []).append(
            {"type": "procedure", "label": airway_event, "time_min": int(state.get("sim_time", 0)) + 1, "duration_min": 0})
    # One more minute of carrying the load the last surface measured.
    work_of_breathing.count_minute(f, bool(f.get("invasive") or f.get("niv") or f.get("bag_mask")))
    import analgesia
    pain_event = analgesia.step(state, float(state.get("observable", {}).get("sbp") or 110))
    if pain_event:
        f.setdefault("procedure_events", []).append(
            {"type": "procedure", "label": pain_event, "time_min": int(state.get("sim_time", 0)) + 1, "duration_min": 0})
    import inotrope_support
    event = inotrope_support.step(state)
    if event:
        f.setdefault("procedure_events", []).append(
            {"type": "procedure", "label": event, "time_min": int(state.get("sim_time", 0)) + 1, "duration_min": 0})
    if f.get("nitro_bolus_pool"):
        f["nitro_bolus_pool"] *= math.exp(-1 / EDEMA["nitro_bolus_tau_min"])
        if f["nitro_bolus_pool"] < 1:
            f["nitro_bolus_pool"] = 0.0
    # Continuous nebulization holds a level of bronchodilation instead of fading.
    if f.get("continuous_bronchodilator_mg_h"):
        target = min(CONTINUOUS_NEBULIZER["max_bronchodilation"],
                     CONTINUOUS_NEBULIZER["bronchodilation_per_mg_h"] * f["continuous_bronchodilator_mg_h"])
        if target > f["bronchodilation"]:
            f["bronchodilation"] += (target - f["bronchodilation"]) / CONTINUOUS_NEBULIZER["tau_min"]
    if f.get("epi_bolus_pool"):
        f["epi_bolus_pool"] *= math.exp(-1 / EPINEPHRINE["bolus_tau_min"])
        if f["epi_bolus_pool"] < 1:
            f["epi_bolus_pool"] = 0.0
    if f.get("sedation_bp_drop"):
        f["sedation_bp_drop"] *= math.exp(-1 / SEDATION_BP_TAU_MIN)
        if f["sedation_bp_drop"] < .5:
            f["sedation_bp_drop"] = 0.0
    if f.get("ketamine_mg"):
        f["ketamine_mg"] *= math.exp(-1 / KETAMINE["tau_min"])
        if f["ketamine_mg"] < .5:
            f["ketamine_mg"] = 0.0
    if f.get("transfusion_overload_units") and not f.get("transfusion_overload_reported"):
        if transfusion_overload(state) >= .5:
            f["transfusion_overload_reported"] = True
            f.setdefault("procedure_events", []).append(
                {"type": "procedure", "label": TRANSFUSION_OVERLOAD_TEXT,
                 "time_min": int(state.get("sim_time", 0)) + 1, "duration_min": 0})
    if f.get("magnesium_pending"):
        grams = f["magnesium_pending"]
        share = min(1.0, 1 / MAGNESIUM["onset_min"])
        gain = min(MAGNESIUM["max_bronchodilation"] - f.get("magnesium_effect", 0.0),
                   grams * MAGNESIUM["bronchodilation_per_g"] * share)
        f["magnesium_effect"] = f.get("magnesium_effect", 0.0) + max(0.0, gain)
        f["bronchodilation"] = min(1.3, f["bronchodilation"] + max(0.0, gain))
        f["magnesium_pending"] = max(0.0, grams - grams * share)
    f["anticoagulant_exposure"] *= math.exp(-1 / ANTICOAGULANT_TAU_MIN)
    # The naloxone decay lives in opioid_reversal.step, which both engines call.
    if f.get("bronchodilator_pending"):
        share = min(1.0, 1 / BRONCHODILATOR_ONSET_MIN)
        arriving = f["bronchodilator_pending"] * share
        f["bronchodilation"] = min(1.3, f["bronchodilation"] + arriving)
        f["bronchodilator_pending"] -= arriving
    f["bronchodilation"] *= BRONCHODILATOR_DECAY_PER_MIN
    for key in {"lung", "circulation", "obstruction"}:
        f[key] = _clamp(f[key], .25, 1.9)
    f["glucose"] = _clamp(f["glucose"], 15, 350)
    f["hemoglobin"] = _clamp(f["hemoglobin"], 3, 18)


def transfusion_overload(state):
    """How many units of unnecessary volume are acting on the lungs right now."""
    f = state["family_state"]
    units = float(f.get("transfusion_overload_units") or 0)
    if not units:
        return 0.0
    started = f.get("transfusion_overload_at", f["elapsed"])
    share = min(1.0, max(0.0, (f["elapsed"] - started) / TRANSFUSION["onset_min"]))
    relieved = TRANSFUSION["diuretic_relief_per_mg"] * float(f.get("diuretic_dose") or 0)
    congested = TRANSFUSION["congested_multiplier"] if state.get("engine_family") == "pulmonary_edema" else 1.0
    return max(0.0, units * share * congested - relieved)


def _sedated(f):
    """Induction wears off: maintenance sedation is a decision, not a given.

    A running sedation infusion is that decision. A neuromuscular blocker is
    not: it removes the patient's breaths, which is what the mechanics need to
    know, and it removes nothing else (faculty decision 11, 2026-09-21).
    """
    return airway_pharmacology.sedated_now(f, asthma_ventilation.SEDATION_DURATION_MIN)


def _no_spontaneous_effort(f):
    """True when nothing of the patient's own is reaching the ventilator."""
    return _sedated(f) or airway_pharmacology.paralysed(f)


def _epinephrine_equivalent(f):
    """Current epinephrine effect in mcg/min, counting a fading IV bolus."""
    return float(f.get("epinephrine") or 0) + float(f.get("epi_bolus_pool") or 0) / EPINEPHRINE["bolus_equivalent_divisor"]


def _airway_relaxation(f):
    """Bronchodilation from epinephrine and ketamine, beyond the nebulized dose."""
    epi = min(EPINEPHRINE["max_bronchodilation"],
              EPINEPHRINE["bronchodilation_per_mcg_min"] * _epinephrine_equivalent(f))
    ketamine = min(KETAMINE["max_bronchodilation"], KETAMINE["bronchodilation_per_mg"] * float(f.get("ketamine_mg") or 0))
    return epi + ketamine


def _surface(state):
    import analgesia, inotrope_support
    f, family = state["family_state"], state["engine_family"]
    if f.get("pain_baseline") is None:
        f["pain_baseline"] = analgesia.arrival_pain(state)
    base = f["baseline"]
    o = state.setdefault("observable", {})
    # A running inotrope carries part of the low-output burden; stopping it
    # gives the burden straight back, so the relief is never written into it.
    circulation = max(1.0, f["circulation"] - inotrope_support.burden_relief(f)) if f["circulation"] > 1 else f["circulation"]
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
    if family == "pulmonary_edema":
        e, tr = EDEMA, state["treatments"]
        epap = float(tr.get("niv_epap_cmh2o") or 5) if f["niv"] else 0
        ipap = float(tr.get("niv_ipap_cmh2o") or epap) if f["niv"] else 0
        recruitment = (min(e["recruit_max"], e["recruit_base"] + e["recruit_per_epap"] * epap) if f["niv"]
                       else .48 if f["invasive"] else 0)
        effective_lung = max(.25, lung - recruitment)
        drive = _clamp((effective_lung - .25) / .75, 0, 1)
        worse = max(0.0, effective_lung - 1)
        base_spo2, base_rr = float(base.get("spo2", 96)), float(base.get("respiratory_rate", 20))
        spo2 = base_spo2 + (e["spo2_resolved"] - base_spo2) * (1 - drive) - worse * 18
        rr = e["rr_resolved"] + (base_rr - e["rr_resolved"]) * drive + worse * 18
        if f["niv"]:
            rr -= _clamp(e["pressure_support_rr_per_cm"] * ((ipap - epap) - 5), -3, 5)
        relief = e["congestion_bp_fraction"] * float(base.get("sbp", 120)) * (1 - drive)
        pressure_drop = f.get("nitro_bp_effect", 0.0) + relief
        sbp -= pressure_drop + e["epap_bp_per_cm"] * max(0, epap - 5)
        dbp -= pressure_drop * .48
        hr -= e["hr_relief"] * (1 - drive)
        oxygen_gain *= 1 - e["shunt_attenuation"] * drive
        effort = drive + worse
    elif family == "pneumonia":
        recruitment = .35 if f["niv"] else .48 if f["invasive"] else 0
        effective_lung = max(.25, lung - recruitment)
        spo2 -= (effective_lung - 1) * 18
        rr += (effective_lung - 1) * 18
        effort = effective_lung
    elif family == "asthma":
        obstruction = max(.2, f["obstruction"] - f["bronchodilation"] - _airway_relaxation(f))
        spo2 -= (obstruction - 1) * 14
        rr += (obstruction - 1) * 18
        # Tachycardia has three sources: the obstruction itself, the exhaustion it
        # causes, and the beta-agonist used to treat it. Relief lowers the first two.
        hr += (obstruction - 1) * 25 + asthma_complications.fatigue_tachycardia(f) + min(12, f["bronchodilation"] * 12)
        if f["invasive"]:
            # Trapped gas raises intrathoracic pressure and obstructs venous return.
            mech = asthma_ventilation.mechanics(state, obstruction, _no_spontaneous_effort(f))
            auto_peep = asthma_ventilation.effective_auto_peep(f, mech["auto_peep_cmh2o"])
            tension = asthma_complications.tension_fraction(f)
            penalty = asthma_complications.intubation_penalty(f)
            f["ventilator_mechanics"] = {
                **mech, "auto_peep_cmh2o": round(auto_peep, 1),
                "peak_cmh2o": round(mech["peak_cmh2o"] + asthma_complications.TENSION_PEAK_RISE * tension, 1),
                "pneumothorax": tension > .2, "pneumothorax_side": f.get("pneumothorax_side"),
            }
            # Volume given before induction, or as the rescue afterwards, buys back
            # part of what positive pressure costs an empty circulation.
            reserve = 1 - asthma_complications.preload_protection(f)
            cost = (asthma_ventilation.SBP_PER_AUTO_PEEP * auto_peep
                    + asthma_complications.TENSION_SBP_DROP * tension + penalty) * reserve
            sbp -= cost
            dbp -= cost * .6
            spo2 -= asthma_complications.TENSION_SPO2_DROP * tension
            oxygen_gain *= 1 - .7 * tension
            rr = mech["rate_per_min"]
        effort = obstruction
        # The patient wakes when the oxygenation returns, not when the wheeze is gone.
        # With the dose's onset and faster fade (faculty 2026-09-20) a single
        # nebulization peaks lower, and the old .4 threshold left them drowsy at 97%.
        if obstruction < .6 and spo2 + oxygen_gain >= 90:
            mental = "Alert"
    elif family == "hypoglycemia":
        mental = "Alert" if f["glucose"] >= 70 else "Drowsy" if f["glucose"] >= 45 else "Obtunded" if f["glucose"] >= 25 else "Unresponsive"
        if f["glucose"] >= 70:
            hr = max(72, float(base.get("hr", 100)) - 18)
        if glucose_rescue.post_ictal(f):
            mental = "Unresponsive"

    elif family == "opioid":
        # Breathing and consciousness are depressed by the same drug and recover
        # on their own schedules (faculty decision 3b, 2026-09-21).
        suppression = opioid_reversal.suppression(f)
        sedation_level = opioid_reversal.sedation(f)
        rr = 14 - (14 - float(base.get("respiratory_rate", 6))) * suppression
        spo2 = 97 - (97 - float(base.get("spo2", 85))) * suppression
        mental = ("Alert" if sedation_level < .2 else "Drowsy" if sedation_level < .55
                  else "Obtunded" if sedation_level < .95 else str(base.get("mental_status", "Obtunded")))
        effort = 1
        excess = opioid_reversal.withdrawal(f)
        if excess:
            hr += opioid_reversal.WITHDRAWAL_HR * min(1.5, excess)
            sbp += opioid_reversal.WITHDRAWAL_SBP * min(1.5, excess)
            dbp += opioid_reversal.WITHDRAWAL_SBP * .6 * min(1.5, excess)
            rr += opioid_reversal.WITHDRAWAL_RR * min(1.5, excess)
            mental = "Agitated"
        if f["bag_mask"] or f["invasive"]:
            spo2 = 96
            rr = 12
    elif family == "acs" and acs_reperfusion.coronary(state):
        import bradycardia_support
        if acs_reperfusion.is_open(f):
            # "The discomfort settles" is what the reperfusion event already says,
            # and decision 3 says a patient treated in time ends better than they
            # arrived: the ischaemic pain goes, it does not linger at a floor.
            f["pain_baseline"] = 0.0
        spec = acs_reperfusion.coronary(state) or {}
        if f.get("av_block_at") is not None and not acs_reperfusion.is_open(f):
            hr = bradycardia_support.effective_rate(f, spec, acs_reperfusion.AV_BLOCK_RATE)
            f["surface_rhythm"] = bradycardia_support.rhythm(f)
            # The rate the block costs is paid in pressure, and given back when
            # atropine or capture restores it (faculty decision 5, 2026-09-21).
            penalty = bradycardia_support.pressure_penalty(
                f, spec, acs_reperfusion.AV_BLOCK_RATE, base.get("hr", 60))
            sbp -= penalty
            dbp -= penalty * .6
        else:
            f.pop("surface_rhythm", None)
        if bradycardia_support.capturing(f):
            # A pacer left running keeps the floor it was set to, block or no block.
            hr = max(hr, float(f["pacing_rate"]))
            f["surface_rhythm"] = bradycardia_support.rhythm(f)
        drop = f.get("nitrate_drop", 0.0)
        sbp -= drop
        dbp -= drop * .6
        if acs_reperfusion.in_shock(f) and mental == "Alert":
            mental = "Drowsy"
    elif family == "pulmonary_embolism":
        # The distended ventricle costs output and oxygenation, with the same
        # coefficients the family already uses for the obstruction itself.
        strain_circulation, strain_lung = pe_obstruction.surface_penalty(
            f, state.get("treatments", {}).get("ventilator_peep_cmh2o"))
        sbp -= strain_circulation * 45
        dbp -= strain_circulation * 25
        hr += strain_circulation * 25
        spo2 -= (circulation - 1 + strain_lung) * 8
        rr += (circulation - 1 + strain_lung) * 10
        # The load is the obstruction the right ventricle and the lung are
        # carrying, not the saturation an oxygen mask can lift.
        effort = 1 + (circulation - 1) + strain_lung + strain_circulation
    elif family == "gi_bleed":
        effort = 1 + (circulation - 1)
        # Tachypnoea of hemorrhagic hypoperfusion eases as circulation recovers and
        # worsens as it fails (faculty request 2026-09-19; magnitude pending review).
        rr = max(GI_BLEED["rr_floor"], rr + (circulation - 1) * GI_BLEED["rr_per_circulation"])
        hr -= GI_BLEED["recovery_hr_relief"] * f.get("hemostasis_relief", 0.0)
    overload = transfusion_overload(state)
    if overload:
        spo2 -= TRANSFUSION["spo2_per_unit"] * overload
        rr += TRANSFUSION["rr_per_unit"] * overload
    # Supplemental oxygen changes oxygenation, not bronchospasm or respiratory drive.
    spo2 += oxygen_gain
    if family != "pulmonary_edema":
        sbp -= min(45, _nitro_equivalent(f) * .3)
        dbp -= min(25, _nitro_equivalent(f) * .15)
    sedation_drop = airway_pharmacology.infusion_pressure_cost(
        f, float(_case(state).get("patient", {}).get("weight_kg") or 70))
    sbp -= sedation_drop
    dbp -= sedation_drop * .6
    import analgesia
    morphine_drop = float(f.get("morphine_preload_drop") or 0)
    sbp -= morphine_drop
    dbp -= morphine_drop * .6
    sedation_steps, rr_cost = analgesia.sedation(state)
    rr = max(4.0, rr - rr_cost)
    inotrope_sbp, inotrope_hr = inotrope_support.surface(state)
    sbp += inotrope_sbp
    dbp += inotrope_sbp * .6
    hr += inotrope_hr
    vasopressor_boost = min(35, f["norepinephrine"] * 1.5)
    equivalent = _epinephrine_equivalent(f)
    vasopressor_boost += min(EPINEPHRINE["max_sbp"], EPINEPHRINE["sbp_per_mcg_min"] * equivalent)
    hr += min(EPINEPHRINE["max_hr"], EPINEPHRINE["hr_per_mcg_min"] * equivalent)
    sbp += vasopressor_boost - float(f.get("sedation_bp_drop") or 0)
    dbp += vasopressor_boost * .7 - float(f.get("sedation_bp_drop") or 0) * .6
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
    elif family not in {"hypoglycemia", "opioid"}:
        mental = _mental_after_recovery(f, str(base.get("mental_status", "Alert")), mental)
    if f["invasive"]:
        mental, wob = airway_pharmacology.mental_and_effort(f)
    elif family == "opioid":
        spontaneous_rr = 14 - (14 - float(base.get("respiratory_rate", 6))) * max(0, f["opioid"] - f["naloxone"])
        wob = "Reduced" if spontaneous_rr < 10 else "Normal"
    else:
        # Faculty decision 9 of 2026-09-21: every family recomputes the effort
        # from its own load, and none of them reports the authoring word for a
        # patient who has moved. The load itself is family-specific and was set
        # above; a family that has no respiratory load carries 1.0 and stays put.
        baseline_wob = str(base.get("work_of_breathing", "Normal"))
        f["respiratory_load"] = float(effort)
        wob = work_of_breathing.describe(family, baseline_wob, effort, f, support)
        if family == "pulmonary_edema" and effort < 1 and not work_of_breathing.exhausted(f, support):
            # Resolving oedema returns the work of breathing towards normal in proportion.
            index = work_of_breathing.load_index(baseline_wob)
            wob = work_of_breathing.LEVELS[int(_clamp(round(index * effort), 0, 4))]
    # Morphine on board takes consciousness down the same ladder every other
    # cause uses, and the pain it relieved is reported beside the vital signs.
    if sedation_steps and mental in _MENTAL_LADDER:
        mental = _MENTAL_LADDER[max(0, _MENTAL_LADDER.index(mental) - sedation_steps)]
    o["temperature_c"] = antipyretics.temperature(f, float(base.get("temperature_c") or 37))
    pain_score = max(0.0, analgesia.pain(state) - antipyretics.relief(f))
    o["pain_score"] = round(pain_score, 1)
    o["discomfort"] = analgesia.descriptor(pain_score)
    o.update(sbp=sbp, dbp=dbp, map=int(round((sbp + 2 * dbp) / 3)), hr=int(round(_clamp(hr, 42, 180))), spo2=spo2,
             respiratory_rate=int(round(_clamp(rr, 3, 45))), work_of_breathing=wob, mental_status=mental,
             crt=round(crt, 1), peripheral_perfusion=perfusion, glucose_mg_dl=int(round(f["glucose"])),
             rhythm=str(base.get("rhythm", "Sinus rhythm")), pulse_present=True,
             extremities=extremities)
    if f.get("arrest_at") is not None:
        # An arrest is an arrest in any family: paralysis without ventilation
        # reaches it the same way apnoea does (2026-09-21).
        f["surface_arrest"] = True
    if f.get("surface_rhythm"):
        o["rhythm"] = f["surface_rhythm"]
    if f.get("surface_arrest"):
        o.update(pulse_present=False, hr=0, sbp=0, dbp=0, map=0, spo2=0, respiratory_rate=0,
                 work_of_breathing="Absent", mental_status="Unresponsive", crt=8.0,
                 peripheral_perfusion="critical", rhythm="Asystole")
    if f.get("vf_at") is not None:
        # Ventricular fibrillation: no organized rhythm and no pulse.
        o.update(rhythm="VF", pulse_present=False, hr=0, sbp=0, dbp=0, map=0,
                 mental_status="Unresponsive", crt=8.0, peripheral_perfusion="critical",
                 spo2=0, respiratory_rate=0, work_of_breathing="Absent")
        state["ecg_profile"] = "baseline"
    if str(base.get("rhythm", "")).lower().startswith("sinus") and not f.get("surface_rhythm") and f.get("vf_at") is None:
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
    if diagnostic in {"ecg_right", "ecg_posterior"}:
        # These leads are their own study, never a second standard tracing.
        result = acs_reperfusion.additional_leads(state, diagnostic)
        state["diagnostic_history"].append({"diagnostic_type": diagnostic, "result": deepcopy(result)})
        return {"type": "diagnostic", "diagnostic_type": diagnostic, "result": result, "duration_min": duration}
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
            if diagnostic == "basic_labs":
                # The panel lists its own values; a prose line saying so read as
                # "... Other measured values are shown below. · WBC ..." on one line.
                result.pop("report", None)
            else:
                result["report"] = f"Hemoglobin {f['hemoglobin']:.1f} g/dL."
        if "glucose_mg_dl" in result:
            result["glucose_mg_dl"] = o["glucose_mg_dl"]
        if state["engine_family"] == "asthma" and "potassium_mmol_l" in result and f.get("potassium") is not None:
            result["potassium_mmol_l"] = round(f["potassium"], 1)
    elif diagnostic == "troponin" and state["engine_family"] == "acs" and acs_reperfusion.coronary(state):
        baseline = float(result.get("value_ng_l", 20))
        spec = acs_reperfusion.coronary(state) or {}
        result["value_ng_l"] = acs_reperfusion.troponin(
            f, baseline, float(spec.get("symptom_onset_min") or 0), spec)
    elif diagnostic == "lactate":
        value = round(max(.8, f["lactate"] + (f["circulation"] - 1) * 2), 1)
        result = {"lactate_mmol_l": value, "report": f"Lactate {value:g} mmol/L"}
    elif diagnostic == "pocus":
        if state["engine_family"] == "pulmonary_edema":
            # Keep the case's own finding, distribution included, while the lungs
            # have not improved; replacing it at every scan dropped "in the
            # anterior and lateral zones" even before any treatment.
            if f["lung"] < .65:
                authored = str(result.get("lungs") or "")
                zones = authored[authored.find(" in the "):] if " in the " in authored else ""
                result["lungs"] = "Fewer but persistent bilateral B-lines" + zones
        # Every bank case now documents the IVC, so this finally runs. It reports
        # what is seen after volume, not what the resident should conclude.
        volume = f["fluid_delivered_ml"] + f["blood_delivered_units"] * 300
        if "ivc" in result and state["engine_family"] in {"pneumonia", "gi_bleed"}:
            if volume >= 1500:
                result["ivc"] = "2.0 cm; <50% inspiratory collapse"
            elif volume >= 500:
                result["ivc"] = "1.5 cm; about 50% inspiratory collapse"
        if state["engine_family"] == "asthma" and f.get("pneumothorax_at") is not None:
            side = f.get("pneumothorax_side", "right")
            treated = f.get("pneumothorax_decompressed_at") is not None
            result["lung_sliding"] = (f"Sliding restored on the {side} after decompression" if treated
                                      else f"Absent on the {side}, with a lung point; present on the other side")
        spec = acs_reperfusion.coronary(state) if state["engine_family"] == "acs" else None
        # The arrival scan is the authored one; the model takes over once the
        # infarct has had minutes to evolve.
        if spec is not None and spec.get("omi") and "lv" in result and f.get("ischemic_min", 0):
            result["lv"] = acs_reperfusion.wall_motion(f, spec)
        if "ivc" in result and (f.get("niv") or f.get("invasive")):
            result["ivc"] = (result["ivc"].split(";")[0]
                             + "; respiratory variation not assessable during positive-pressure support")
    elif diagnostic in {"vbg", "abg"}:
        respiratory_failure = state["engine_family"] in {"asthma", "opioid"}
        pco2 = float(result.get("pco2_mm_hg", result.get("paco2_mm_hg", result.get("pco2_mmhg", result.get("pco2", 40)))))
        if respiratory_failure:
            baseline_co2 = pco2
            bicarbonate = float(result.get("bicarbonate_mmol_l", .03 * baseline_co2 * 10 ** (float(result.get("ph", 7.4)) - 6.1)))
            factor = (max(.15, f["obstruction"] - f["bronchodilation"] - _airway_relaxation(f))
                      if state["engine_family"] == "asthma" else max(.05, f["opioid"] - f["naloxone"]))
            pco2 = 40 + (baseline_co2 - 40) * factor
            if state["engine_family"] == "asthma" and baseline_co2 < 40 and factor > 1.25:
                pco2 = baseline_co2 + (factor - 1.25) * 40

            if state["engine_family"] == "asthma" and f["invasive"]:
                # Permissive hypercapnia: what the set minute ventilation leaves behind.
                ventilated, _ = asthma_ventilation.blood_gas(state, factor, _no_spontaneous_effort(f))
                pco2 = _clamp(ventilated, 30, 130)
            elif f["bag_mask"] or f["invasive"]:
                pco2 = min(pco2, 46)
            result["pco2_mm_hg" if diagnostic == "vbg" else "paco2_mm_hg"] = round(pco2)
            result["bicarbonate_mmol_l"] = round(bicarbonate, 1)
            result["ph"] = round(6.1 + math.log10(bicarbonate / (.03 * pco2)), 2)
        result["fio2_percent"] = round(f["oxygen_fio2"] * 100)
        if diagnostic == "abg":
            result["sao2_percent"] = o["spo2"]
            baseline_oxygen = float(result.get("pao2_mm_hg", 80))
            # Supplemental oxygen raises the arterial tension, not only the saturation:
            # a saturation of 99% on FiO2 100% used to report PaO2 77 and a P/F of 77.
            # How much it rises depends on how much of the defect is true shunt.
            shunt = _OXYGEN_SHUNT.get(state["engine_family"], .35)
            oxygen_step = max(0.0, f["oxygen_fio2"] - .21) * 350 * (1 - shunt)
            pao2 = round(_clamp(baseline_oxygen + (o["spo2"] - f["baseline"].get("spo2", o["spo2"])) * 2.0
                                + oxygen_step, 28, 500))
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
        from coupled_encounter import enabled
        if not enabled(_case(state)):
            return _failure("This saved case predates the shared main/IA engine. Generate a new case to continue; the original record is preserved.")
        from generated_engine import execute_generated_bundle
        return execute_generated_bundle(state, parsed)
    if state.get("engine_family") not in FAMILIES:
        return _failure("This encounter does not have a supported clinical trajectory.")
    actions, error = _validate(state, parsed)
    if error:
        return _failure(error)
    if state.get("family_state", {}).get("vf_at") is not None or state.get("family_state", {}).get("arrest_at") is not None:
        # Arrest management is outside this build: do not run ordinary physiology as
        # though there were a circulation.
        return {"executed": False, "terminal_locked": True, "clarification": None,
                "action_summaries": [], "reassess_delay": None, "elapsed_min": 0}
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
        _discharge_return(candidate)
        for summary in due.get(minute, []):
            summaries.append(_release_diagnostic(candidate, summary, candidate["sim_time"]))
    # Events the patient's course produced on its own (an endoscopy) are reported
    # at the minute they happened, not as part of the resident's order.
    summaries.extend(candidate.get("family_state", {}).pop("procedure_events", []))
    candidate.get("family_state", {}).pop("endoscopy_deferral_reported", None)
    if elapsed == 0 and summaries and any(s.get("type") not in {"consult", "reperfusion_referral", "disposition", "diagnostic", "procedure"} for s in summaries):
        _surface(candidate)
    state.clear()
    state.update(candidate)
    return {"executed": True, "clarification": None, "action_summaries": summaries, "reassess_delay": reassess, "elapsed_min": elapsed}


EXAMINATION_REGIONS = ("General appearance", "Breathing", "Peripheral perfusion")


def examination_finding(state, region):
    """The finding for one region, for the Examine control and for a written order."""
    observed = state.get("observable", {})
    if region == "General appearance":
        from patient_appearance import appearance_summary
        return appearance_summary(state)
    findings = current_findings(state)
    if region in findings:
        return findings[region]
    if region == "Breathing":
        return ("Respiratory rate: " + str(observed.get("respiratory_rate", "—")) + "/min. Work of breathing: "
                + str(observed.get("work_of_breathing", "Not documented")))
    if not observed.get("pulse_present", True):
        return "Pulse absent. Capillary refill is not measurable."
    return ("Capillary refill: " + str(observed.get("crt", "—")) + " s. Extremities: "
            + str(observed.get("extremities", "Not documented")))


def available_regions(state):
    """Every region the resident may examine in this encounter, in menu order."""
    return list(dict.fromkeys(list(EXAMINATION_REGIONS) + list(current_findings(state))))


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
    if f and transfusion_overload(state) >= .5:
        # Replace the authored line rather than prepending to it: the lungs are no
        # longer clear, whatever the case said at arrival.
        findings["Respiratory"] = ("New bibasal inspiratory crackles since the transfusion, with increased effort and "
                                   "no wheeze.")
    if family == "asthma" and f:
        airflow = f["obstruction"] - f["bronchodilation"] - _airway_relaxation(f)
        findings["Respiratory"] = "Improved air entry with residual expiratory wheeze." if airflow < .65 else "Reduced bilateral air entry with prolonged expiration and wheeze."
        if f.get("pneumothorax_at") is not None:
            side = f.get("pneumothorax_side", "right")
            findings["Respiratory"] = (
                f"Breath sounds returning on the {side} after decompression; " + findings["Respiratory"][0].lower() + findings["Respiratory"][1:]
                if f.get("pneumothorax_decompressed_at") is not None else
                f"Breath sounds absent over the {side} hemithorax, which is hyper-resonant; wheeze on the other side.")
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
    text = (f"BP {o.get('sbp')}/{o.get('dbp')} mmHg · HR {o.get('hr')}/min · "
            f"SpO₂ {o.get('spo2')}% · RR {o.get('respiratory_rate')}/min. "
            f"{o.get('mental_status', 'Not recorded')}; respiratory effort {str(o.get('work_of_breathing', 'not recorded')).lower()}; "
            f"capillary refill {o.get('crt')} s.")
    if o.get("discomfort") and o.get("discomfort") != "no pain":
        text += f" The patient reports {o['discomfort']}."
    elif o.get("pain_score") is not None and float(o.get("pain_score") or 0) < .5 and state.get(
            "family_state", {}).get("pain_baseline"):
        text += " The patient reports no pain."
    mechanics = state.get("family_state", {}).get("ventilator_mechanics")
    if mechanics and state.get("family_state", {}).get("invasive"):
        text += " " + asthma_ventilation.pressure_report(mechanics, mechanics["auto_peep_cmh2o"])
        gas = state.get("diagnostics", {}).get("abg", {})
        text += asthma_ventilation.hypercapnia_note(gas.get("ph"), gas.get("paco2_mm_hg"))
    return text
