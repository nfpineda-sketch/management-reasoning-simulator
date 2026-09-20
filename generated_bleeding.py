"""Active bleeding inside a generated case (faculty decision 2026-09-20).

Sixth mechanism. The shared core models volume, but it does not model losing
blood: haemoglobin only moves where a disease model moves it. So a generated case
about a bleeding patient had no bleeding at all.

The case declares ``engine.active_bleeding``; the gate refuses what the resident
cannot discover; the bank's GI_BLEED magnitudes do the work, and the adapter reads
the result as a change in the haemoglobin the resident measures and in the
circulation that carries it.

What the declaration buys: blood that keeps being lost until it is stopped,
crystalloid that buys less than blood and dilutes what is left, a proton-pump
inhibitor that slows it a little, the endoscopy that gastroenterology performs
once the patient is resuscitated enough, and the tachycardia that eases only
after haemostasis.
"""
from family_engine import GI_BLEED

MECHANISM_ACTIONS = frozenset({"blood", "ppi"})

# The shared core amplifies what it is given, so the deltas are gentler than the
# bank's internal mapping, as for every other generated mechanism.
SBP_PER_BURDEN = 35.0
DBP_PER_BURDEN = 20.0
HR_PER_BURDEN = 20.0
RR_PER_BURDEN = 12.0
CRT_PER_BURDEN = 3.0
SBP_FLOOR = -30.0


def spec(state):
    case = state.get("encounter_spec", {}).get("clinical_case", {})
    return case.get("engine", {}).get("active_bleeding")


def _consulted(f):
    return any(c["service"] == "gastroenterology" for c in f.get("consultations", []))


def step(state):
    """One minute of bleeding, transfusion and haemostasis. Returns an event or None."""
    declaration = spec(state)
    if declaration is None:
        return None
    from family_engine import _endoscopy_minute, _gi_bleeding_fraction
    f = state["family_state"]
    f.setdefault("hemoglobin_reference", float(f.get("hemoglobin", 12)))
    f.setdefault("bleeding_burden", 0.0)
    event = None
    before = f.get("endoscopy_at")
    _endoscopy_minute(state)
    if f.get("endoscopy_at") != before or f.get("procedure_events"):
        queued = f.pop("procedure_events", [])
        event = queued[0]["label"] if queued else None
    bleeding = _gi_bleeding_fraction(f)
    anticoagulant = float(f.get("anticoagulant_exposure") or 0)
    f["bleeding_burden"] += (.003 + .002 * anticoagulant) * bleeding
    f["hemoglobin"] -= (.009 + .006 * anticoagulant) * bleeding
    # Transfusion and crystalloid are delivered by the shared order path; their
    # circulating effect is the bank's, and the dilution comes with the volume.
    given_blood = float(f.get("blood_delivered_units") or 0) - float(f.get("bleeding_blood_seen", 0))
    if given_blood:
        f["bleeding_blood_seen"] = float(f.get("blood_delivered_units") or 0)
        f["bleeding_burden"] -= given_blood * .36
        f["hemoglobin"] += given_blood * .85
    given_fluid = float(f.get("fluid_delivered_ml") or 0) - float(f.get("bleeding_fluid_seen", 0))
    if given_fluid:
        f["bleeding_fluid_seen"] = float(f.get("fluid_delivered_ml") or 0)
        f["bleeding_burden"] -= given_fluid * GI_BLEED["crystalloid_per_ml"]
        f["hemoglobin"] -= given_fluid * GI_BLEED["hemodilution_g_dl_per_ml"]
    if f.get("endoscopy_at") is not None and f["hemoglobin"] >= GI_BLEED["recovery_min_hemoglobin"]:
        relief = f.get("hemostasis_relief", 0.0)
        f["hemostasis_relief"] = relief + (1 - relief) / GI_BLEED["recovery_tau_min"]
    return event


def generated_effects(state):
    """(sbp, dbp, hr, respiratory_rate, crt, hemoglobin) since arrival."""
    if spec(state) is None:
        return (0.0,) * 6
    f = state["family_state"]
    burden = f.get("bleeding_burden", 0.0)
    relief = f.get("hemostasis_relief", 0.0)
    sbp = max(SBP_FLOOR, -SBP_PER_BURDEN * burden)
    dbp = max(SBP_FLOOR * .6, -DBP_PER_BURDEN * burden)
    hr = HR_PER_BURDEN * burden - GI_BLEED["recovery_hr_relief"] * relief
    rr = RR_PER_BURDEN * burden
    crt = CRT_PER_BURDEN * burden
    hemoglobin = float(f.get("hemoglobin", 0)) - float(f.get("hemoglobin_reference", f.get("hemoglobin", 0)))
    return sbp, dbp, hr, rr, crt, hemoglobin
