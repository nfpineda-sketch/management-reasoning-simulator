"""Render only documented results; missing measurements are never normal values."""

TEST_LABELS = {
    "head_ct": "Head CT", "abdominal_ct": "Abdominal CT", "cortisol": "Cortisol",
    "thyroid_function": "Thyroid function", "ketones": "Ketones", "toxicology": "Toxicology",
    "pocus": "POCUS", "ecg": "ECG", "vbg": "Venous blood gas", "abg": "Arterial blood gas",
    "lactate": "Lactate", "basic_labs": "Laboratory results", "poc_glucose": "Bedside glucose",
    "temperature": "Temperature", "chest_xray": "Chest X-ray", "urinalysis": "Urinalysis",
    "blood_cultures": "Blood cultures", "troponin": "Troponin", "ctpa": "CT pulmonary angiography", "d_dimer": "D-dimer",
    "hemoglobin": "Hemoglobin",
    "ecg_right": "Right-sided ECG (V3R-V4R)", "ecg_posterior": "Posterior ECG (V7-V9)",
    "renal_ultrasound": "Renal tract ultrasound",
    "efast": "E-FAST", "pelvis_xray": "Pelvis X-ray",
}
FIELDS = {
    "cortisol_ug_dl": "Cortisol (µg/dL)", "tsh_miu_l": "TSH (mIU/L)",
    "free_t4_ng_dl": "Free T4 (ng/dL)", "ketones_mmol_l": "Ketones (mmol/L)",
    "lv": "LV", "rv": "RV", "pericardium": "Pericardium", "ivc": "IVC", "lungs": "Lungs",
    "ph": "pH", "pco2_mm_hg": "pCO₂ (mmHg)", "paco2_mm_hg": "PaCO₂ (mmHg)",
    "pao2_mm_hg": "PaO₂ (mmHg)", "bicarbonate_mmol_l": "HCO₃ (mmol/L)",
    "base_excess_mmol_l": "Base excess (mmol/L)", "lactate_mmol_l": "Lactate (mmol/L)",
    "value_mmol_l": "Value (mmol/L)", "fio2_percent": "FiO₂ (%)", "pf_ratio": "P/F ratio",
    "sao2_percent": "SaO₂ (%)", "wbc_k_ul": "WBC (K/µL)", "hemoglobin_g_dl": "Hemoglobin (g/dL)",
    "platelets_k_ul": "Platelets (K/µL)", "sodium_mmol_l": "Na (mmol/L)",
    "potassium_mmol_l": "K (mmol/L)", "bun_mg_dl": "BUN (mg/dL)",
    "creatinine_mg_dl": "Creatinine (mg/dL)", "glucose_mg_dl": "Glucose (mg/dL)",
    "crp_mg_l": "CRP (mg/L)", "temperature_c": "Temperature (°C)",
    "value_ng_l": "Troponin (ng/L)", "upper_reference_ng_l": "Upper reference (ng/L)",
    "d_dimer_ng_ml_feu": "D-dimer (ng/mL FEU)",
    "upper_reference_ng_ml_feu": "Upper reference, age-adjusted (ng/mL FEU)",
    "finding": "Finding", "history": "History",
}

TIMING_VERBS = {
    "chest_xray": "Performed", "head_ct": "Performed", "abdominal_ct": "Performed",
    "ctpa": "Performed", "ecg": "Performed", "temperature": "Measured",
    "ecg_right": "Performed", "ecg_posterior": "Performed",
}


def _dose_text(amount):
    """A dose as a clinician writes it: whole units from 10 up, three figures below."""
    return f"{amount:.0f}" if abs(amount) >= 10 else f"{amount:.3g}"


def format_result(test_id, result):
    label = TEST_LABELS.get(test_id, "Investigation")
    if test_id == "pocus":
        # Every POCUS report uses the same structure, normal findings included.
        from pocus_report import format_pocus
        return format_pocus(result, heading=label)
    if test_id == "ecg":
        # The tracing is the result. The resident reads it; the report never names the rhythm.
        timing = (f"Performed at minute {result['collected_at_min']:g} · "
                  if type(result.get("collected_at_min")) in {int, float} else "")
        if result.get("status") not in (None, "available"):
            return f"{label}: {timing}{result.get('reason') or 'No tracing could be acquired.'}"
        return f"{label}: {timing}12-lead tracing available in ECG recordings at the bedside."
    report = result.get("report") if isinstance(result.get("report"), str) else None
    parts = [report] if report else []
    if type(result.get("collected_at_min")) in {int, float}:
        # Imaging and tracings are performed and a temperature is measured; only a
        # specimen is a sample.
        verb = TIMING_VERBS.get(test_id, "Sample obtained")
        parts.insert(0, f"{verb} at minute {result['collected_at_min']:g}")
    for key, title in FIELDS.items():
        value = result.get(key)
        if isinstance(value, (str, int, float)) and not isinstance(value, bool):
            # "Lactate 3.4 mmol/L" already states the value; do not repeat it as a field.
            if report and f"{value}" in report and title.split(" (")[0].lower() in report.lower():
                continue
            parts.append(f"{title}: {value}")
    return label + ": " + (" · ".join(parts) if parts else "No result has been recorded.")


def format_administration(record):
    amount = record.get("dose_g", record.get("dose_mg", record.get("dose")))
    unit = "g" if "dose_g" in record else "mg" if "dose_mg" in record else record.get("units", "")
    parts = [str(record.get("agent") or "Medication")]
    if isinstance(amount, (int, float)) and not isinstance(amount, bool):
        parts.append(f"{_dose_text(amount)} {unit}")
    if record.get("route"):
        parts.append(str(record["route"]))
    text = " ".join(parts) + " · minute " + str(record.get("time_min", "—"))
    duration = record.get("administration_duration_min")
    if duration:
        # A timed dose names what has gone in, not only what was ordered.
        ordered = record.get("ordered_dose_g", record.get("ordered_dose_mg", record.get("ordered_dose")))
        text += f" · over {duration:g} min"
        if record.get("administration_status") == "in_progress" and isinstance(ordered, (int, float)):
            text += f" · {_dose_text(amount)} of {_dose_text(ordered)} {unit} given so far"
    return text


def format_transfusion(delivered, pending):
    """Red cells given so far, and what is still running, without spurious decimals."""
    def number(value):
        return f"{value:.1f}".rstrip("0").rstrip(".")
    if pending >= .05:
        return f"Packed red cells: {number(delivered)} of {number(delivered + pending)} units given so far"
    given = number(delivered)
    return f"Packed red cells given: {given} unit" + ("" if given == "1" else "s")
