"""Dynamic original main/IA diagnostic calculations."""
import math
from copy import deepcopy
from clinical_physiology import clamp

def _diagnostic_timestamp(state, delay_min=0):
    return int(state.get("sim_time", 0) + delay_min)


def pocus_transition(state, requested_delay_min=None):
    """Return a bedside POCUS result derived from the current simulated physiology.

    POCUS is informational only: it does not modify physiology.
    """
    h = state["hidden"]
    tr = state.get("treatments", {}) or {}
    d = state.setdefault("diagnostics", {})
    preload = float(h.get("preload_state", h.get("effective_volume", 0.5)))
    cardiac = float(h.get("cardiac_function", 0.8))
    congestion = float(h.get("pulmonary_congestion", 0.0))

    # PS001 deliberately evolves from a preserved baseline to acquired low
    # contractile reserve during the classroom trajectory. Use the current
    # effective state rather than the immutable baseline phenotype so repeat
    # POCUS can disclose that transition. PS002 retains its validated
    # case-specific imaging phenotype.
    if state.get("case_id") == "PS001" or state.get("engine_profile") == "main_ia_v1":
        current_contractility = float(
            h.get("effective_contractility", h.get("contractile_reserve", 1.0))
        )
        cardiac = clamp(cardiac * current_contractility, 0.0, 1.35)

    if cardiac >= 0.68:
        lv = "preserved to hyperdynamic LV systolic function"
    elif cardiac >= 0.48:
        lv = "mildly reduced LV systolic function"
    else:
        lv = "moderately to severely reduced LV systolic function"

    if preload < 0.48:
        ivc_diameter = 1.4
        spontaneous_variation = ">50% respiratory variation"
    elif preload < 0.65:
        ivc_diameter = 1.8
        spontaneous_variation = "moderate respiratory variation"
    else:
        ivc_diameter = 2.1
        spontaneous_variation = "limited respiratory variation"

    if tr.get("invasive_ventilation"):
        peep = float(tr.get("ventilator_peep_cmh2o") or 5.0)
        ivc = (
            f"IVC approximately {ivc_diameter:g} cm during positive-pressure ventilation "
            f"(PEEP {peep:g} cm H₂O); respiratory variation is not interpreted as a standalone preload marker"
        )
    elif tr.get("niv"):
        ivc = (
            f"IVC approximately {ivc_diameter:g} cm during noninvasive positive-pressure support; "
            "respiratory variation is not interpreted as a standalone preload marker"
        )
    else:
        ivc = f"IVC approximately {ivc_diameter:g} cm with {spontaneous_variation}"

    if congestion >= 0.48:
        lungs = "diffuse bilateral B-lines"
    elif congestion >= 0.20:
        lungs = "scattered bilateral B-lines"
    else:
        lungs = "no diffuse B-line pattern"

    delay = 2 if requested_delay_min is None else max(0, int(requested_delay_min))
    result = {
        "time_min": _diagnostic_timestamp(state, delay),
        "lv": lv,
        "rv": "RV not dilated; no clear RV pressure-overload pattern",
        "pericardium": "no pericardial effusion",
        "ivc": ivc,
        "lungs": lungs,
    }
    d["pocus"] = result
    return {"duration_min": delay, "diagnostic_type": "pocus", "result": deepcopy(result)}


def lactate_transition(state, requested_delay_min=None):
    """Return a lactate value coupled to tissue perfusion / low-flow burden."""
    h = state["hidden"]
    d = state.setdefault("diagnostics", {})
    perf = clamp(float(h.get("tissue_perfusion", 0.5)))
    low_flow = clamp(float(h.get("low_flow_burden", 0.0)))
    inflammatory = clamp(float(h.get("inflammatory_drive", 0.0)))
    # Deliberately deterministic for a reproducible teaching case.
    value = 1.1 + 5.0 * (1.0 - perf) + 1.8 * low_flow + 0.7 * inflammatory
    value = round(max(0.8, min(9.5, value)), 1)
    delay = 5 if requested_delay_min is None else max(0, int(requested_delay_min))
    result = {
        "time_min": _diagnostic_timestamp(state, delay),
        "value_mmol_l": value,
        "flag": "elevated" if value >= 2.0 else "normal",
    }
    d["lactate"] = result
    return {"duration_min": delay, "diagnostic_type": "lactate", "result": deepcopy(result)}


def vbg_transition(state, requested_delay_min=None):
    """Return a deterministic venous blood gas coupled to current physiology."""
    h = state["hidden"]
    d = state.setdefault("diagnostics", {})
    perf = clamp(float(h.get("tissue_perfusion", 0.5)))
    low_flow = clamp(float(h.get("low_flow_burden", 0.0)))
    inflammatory = clamp(float(h.get("inflammatory_drive", 0.0)))
    respiratory = clamp(float(h.get("respiratory_failure_severity", 0.0)))
    lactate = round(max(0.8, min(9.5, 1.1 + 5.0 * (1.0 - perf) + 1.8 * low_flow + 0.7 * inflammatory)), 1)
    bicarbonate = int(round(max(14, 24 - 7.0 * (1.0 - perf) - 3.0 * low_flow - 2.0 * inflammatory)))
    pco2 = int(round(max(24, min(55, 1.5 * bicarbonate + 8.0 - 3.0 * respiratory))))
    ph = round(max(6.90, min(7.55, 6.1 + math.log10(bicarbonate / (0.03 * pco2)))), 2)
    delay = 3 if requested_delay_min is None else max(0, int(requested_delay_min))
    result = {
        "time_min": _diagnostic_timestamp(state, delay),
        "ph": ph,
        "pco2_mm_hg": pco2,
        "bicarbonate_mmol_l": bicarbonate,
        "base_excess_mmol_l": int(round(bicarbonate - 24)),
        "lactate_mmol_l": lactate,
    }
    d["vbg"] = result
    return {"duration_min": delay, "diagnostic_type": "vbg", "result": deepcopy(result)}


def abg_transition(state, requested_delay_min=None):
    """Return an arterial blood gas with oxygenation tied to current support."""
    h = state["hidden"]
    o = state["observable"]
    tr = state["treatments"]
    d = state.setdefault("diagnostics", {})
    perf = clamp(float(h.get("tissue_perfusion", 0.5)))
    low_flow = clamp(float(h.get("low_flow_burden", 0.0)))
    inflammatory = clamp(float(h.get("inflammatory_drive", 0.0)))
    respiratory = clamp(float(h.get("respiratory_failure_severity", 0.0)))

    bicarbonate = int(round(max(14, 24 - 7.0 * (1.0 - perf) - 3.0 * low_flow - 2.0 * inflammatory)))
    paco2 = int(round(max(22, min(60, 1.45 * bicarbonate + 6.0 - 4.0 * respiratory))))
    ph = round(max(6.90, min(7.60, 6.1 + math.log10(bicarbonate / (0.03 * paco2)))), 2)

    spo2 = float(o.get("spo2") if o.get("spo2") is not None else 85.0)
    if spo2 <= 90:
        pao2 = 60.0 + 2.0 * (spo2 - 90.0)
    elif spo2 <= 94:
        pao2 = 60.0 + 7.5 * (spo2 - 90.0)
    elif spo2 <= 97:
        pao2 = 90.0 + 10.0 * (spo2 - 94.0)
    else:
        pao2 = 120.0 + 20.0 * (spo2 - 97.0)
    pao2 = int(round(max(35.0, min(300.0, pao2))))

    if tr.get("invasive_ventilation"):
        fio2_percent = float(tr.get("ventilator_fio2_percent") or 40.0)
    elif tr.get("niv"):
        fio2_percent = float(tr.get("niv_fio2_percent") or 40.0)
    elif tr.get("oxygen"):
        fio2_percent = min(60.0, 21.0 + 3.0 * float(tr.get("oxygen_flow_lpm") or 0.0))
    else:
        fio2_percent = 21.0
    fio2_fraction = clamp(fio2_percent / 100.0, 0.21, 1.0)
    pf_ratio = int(round(pao2 / fio2_fraction))

    delay = 3 if requested_delay_min is None else max(0, int(requested_delay_min))
    result = {
        "time_min": _diagnostic_timestamp(state, delay),
        "ph": ph,
        "paco2_mm_hg": paco2,
        "pao2_mm_hg": pao2,
        "bicarbonate_mmol_l": bicarbonate,
        "base_excess_mmol_l": int(round(bicarbonate - 24)),
        "fio2_percent": fio2_percent,
        "pf_ratio": pf_ratio,
    }
    d["abg"] = result
    return {"duration_min": delay, "diagnostic_type": "abg", "result": deepcopy(result)}
