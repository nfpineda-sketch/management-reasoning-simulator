"""What the room shows must not contradict the patient's state (Phase 0, 0G).

Pre-pilot measurement safety, 2026-10-06. The clinical engine audit (§6, §16) found
observations that contradicted the state the engine held: three families announced an arrest
in prose while the monitor kept a pulse and a pressure (anaphylaxis, trauma, bradycardia);
an arrest's heart rate of 0 was relabelled "sinus bradycardia"; a normal examination could
be read after an arrest; and the hyperkalaemia case's laboratory potassium stayed at the
authored value while the engine's own potassium climbed.

This module states the invariants once and checks them; the narrow fixes live where the
observation is produced (``family_engine._surface``, ``examination_finding``, ``_diagnostic``
and the three family modules), and the page says the arrest in the words the pilot agreed:

    Cardiac arrest occurred at minute X. Resuscitation management is not modelled in this
    pilot. Subsequent management is not assessable.

Nothing here invents a recovery, and nothing models resuscitation.
"""
from __future__ import annotations

NON_PERFUSING = ("VF", "pVT", "Ventricular fibrillation", "Pulseless ventricular tachycardia", "Asystole", "PEA")

#: The engine's flags for a loss of circulation, in the order they are read.
ARREST_FLAGS = ("vf_at", "arrest_at")
#: Family flags that announced an arrest; each now sets ``arrest_at`` with it.
NARRATIVE_ARREST_FLAGS = ("arrested", "hemorrhage_arrest", "bradycardia_arrest")


def arrest_minute(state):
    """The simulated minute the circulation was lost, or None.

    The family state counts minutes from arrival (``elapsed``), as the simulated clock does.
    """
    f = (state or {}).get("family_state") or {}
    minutes = [f.get(flag) for flag in ARREST_FLAGS if f.get(flag) is not None]
    return int(min(minutes)) if minutes else None


def arrest_message(minute):
    where = f"minute {int(minute)}" if minute is not None else "an earlier minute"
    return (f"Cardiac arrest occurred at {where}. Resuscitation management is not modelled in this pilot. "
            "Subsequent management is not assessable.")


def arrest_examination(region):
    """Every region, after an arrest: what any examiner finds, and nothing the case wrote for a live patient."""
    return ("Unresponsive, not breathing, no central pulse: the patient is in cardiac arrest. "
            "Resuscitation is not modelled in this pilot.")


def check(state):
    """The invariants between the observable and the state; a list of what is broken (empty when none)."""
    o = (state or {}).get("observable") or {}
    f = (state or {}).get("family_state") or {}
    broken = []
    pulse = o.get("pulse_present", True)
    rhythm = str(o.get("rhythm") or "")
    hr, sbp, dbp = o.get("hr"), o.get("sbp"), o.get("dbp")
    arrested = arrest_minute(state) is not None or bool(f.get("surface_arrest"))
    narrative = [flag for flag in NARRATIVE_ARREST_FLAGS if f.get(flag)]
    if narrative and pulse:
        broken.append(f"an arrest was announced ({', '.join(narrative)}) while a pulse is shown")
    if arrested and pulse:
        broken.append("the engine holds an arrest while a pulse is shown")
    if not pulse:
        if rhythm and not any(rhythm.lower().startswith(name.lower()) for name in NON_PERFUSING):
            broken.append(f"no pulse with a perfusing rhythm label ({rhythm})")
        if (sbp or 0) > 0 or (dbp or 0) > 0:
            broken.append(f"no pulse with a blood pressure ({sbp}/{dbp})")
    if pulse and rhythm and any(rhythm.lower().startswith(name.lower()) for name in NON_PERFUSING):
        broken.append(f"a pulse with a non-perfusing rhythm ({rhythm})")
    if hr is not None and float(hr) <= 0 and rhythm.lower().startswith("sinus"):
        broken.append(f"a heart rate of 0 labelled {rhythm}")
    if pulse and hr is not None and float(hr) <= 0:
        broken.append("a pulse with a heart rate of 0")
    return broken


def lab_follows_state(state, diagnostic, result):
    """Laboratory values the engine models are read from the engine, never from the authored case."""
    f = (state or {}).get("family_state") or {}
    if isinstance(result, dict) and "potassium_mmol_l" in result and f.get("potassium") is not None:
        result["potassium_mmol_l"] = round(float(f["potassium"]), 1)
    return result


#: Studies whose result is read from the engine at the minute of collection (dynamic), in every family.
DYNAMIC_STUDIES = ("ecg", "poc_glucose", "temperature", "hemoglobin", "lactate")
#: Studies whose result is partly read from the engine: the fields named here follow it; the rest is authored.
PARTLY_DYNAMIC = {
    "basic_labs": ("hemoglobin_g_dl", "glucose_mg_dl", "potassium_mmol_l (where the family models potassium)"),
    "troponin": ("value_ng_l (acute coronary syndrome)",),
    "pocus": ("ivc", "lungs", "lv", "lung_sliding (where the family models them)"),
    "vbg": ("pco2 and pH (asthma and opioid)",),
    "abg": ("pco2, pH and po2 (asthma and opioid)",),
    "ecg_right": ("the right-sided leads (acute coronary syndrome)",),
    "ecg_posterior": ("the posterior leads (acute coronary syndrome)",),
}
#: Examination regions the engine writes from the state; every other region is the case's authored finding.
DYNAMIC_REGIONS = ("General appearance", "Breathing", "Peripheral perfusion", "Neurological")
#: Regions a family's engine rewrites from its own state (``family_engine.current_findings``).
FAMILY_DYNAMIC_REGIONS = {
    "asthma": ("Respiratory",), "pulmonary_edema": ("Respiratory",), "opioid": ("Respiratory",),
    "anaphylaxis": ("Respiratory",), "hypoglycemia": ("Vascular access",),
}
#: Rewritten in any family once a transfusion overloads the patient.
PARTLY_DYNAMIC_REGIONS = {"Respiratory": "after a transfusion overload, in any family"}


def declaration(state):
    """Which observations follow the state and which are the case's authored, static ones."""
    case = ((state or {}).get("encounter_spec") or {}).get("clinical_case") or {}
    studies = sorted((case.get("investigations") or {}).keys())
    regions = sorted((case.get("examination") or {}).keys())
    dynamic_regions = list(DYNAMIC_REGIONS) + list(FAMILY_DYNAMIC_REGIONS.get((state or {}).get("engine_family"), ()))
    return {
        "studies": {
            "dynamic": sorted(set([s for s in studies if s in DYNAMIC_STUDIES] + ["ecg"])),
            "partly_dynamic": {s: list(PARTLY_DYNAMIC[s]) for s in studies if s in PARTLY_DYNAMIC},
            "static": [s for s in studies if s not in DYNAMIC_STUDIES and s not in PARTLY_DYNAMIC],
        },
        "examination": {
            "dynamic": dynamic_regions,
            "partly_dynamic": {r: PARTLY_DYNAMIC_REGIONS[r] for r in regions
                               if r in PARTLY_DYNAMIC_REGIONS and r not in dynamic_regions},
            "static": [r for r in regions if r not in dynamic_regions and r not in PARTLY_DYNAMIC_REGIONS],
        },
        "history": "authored (static): the case's history and the collateral source do not follow the state",
    }
