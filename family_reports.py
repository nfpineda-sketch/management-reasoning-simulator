"""Render only documented results; missing measurements are never normal values."""

TEST_LABELS = {
    "head_ct": "Head CT", "abdominal_ct": "Abdominal CT", "cortisol": "Cortisol",
    "thyroid_function": "Thyroid function", "ketones": "Ketones", "toxicology": "Toxicology",
    "pocus": "POCUS", "ecg": "ECG", "vbg": "Venous blood gas", "abg": "Arterial blood gas",
    "lactate": "Lactate", "basic_labs": "Laboratory results", "poc_glucose": "Bedside glucose",
    "temperature": "Temperature", "chest_xray": "Chest X-ray", "urinalysis": "Urinalysis",
    "blood_cultures": "Blood cultures", "troponin": "Troponin", "ctpa": "CT pulmonary angiography",
    "hemoglobin": "Hemoglobin",
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
    "finding": "Finding", "history": "History",
}


def format_result(test_id, result):
    label = TEST_LABELS.get(test_id, "Investigation")
    if test_id == "pocus":
        # Every POCUS report uses the same structure, normal findings included.
        from pocus_report import format_pocus
        return format_pocus(result, heading=label)
    parts = [str(result["report"])] if isinstance(result.get("report"), str) else []
    if type(result.get("collected_at_min")) in {int, float}:
        parts.insert(0, f"Sample obtained at minute {result['collected_at_min']}")
    for key, title in FIELDS.items():
        value = result.get(key)
        if isinstance(value, (str, int, float)) and not isinstance(value, bool):
            parts.append(f"{title}: {value}")
    return label + ": " + (" · ".join(parts) if parts else "No result has been recorded.")


def format_administration(record):
    amount = record.get("dose_g", record.get("dose_mg", record.get("dose")))
    unit = "g" if "dose_g" in record else "mg" if "dose_mg" in record else record.get("units", "")
    parts = [str(record.get("agent") or "Medication")]
    if isinstance(amount, (int, float)) and not isinstance(amount, bool):
        parts.append(f"{amount:g} {unit}")
    if record.get("route"):
        parts.append(str(record["route"]))
    return " ".join(parts) + " · minute " + str(record.get("time_min", "—"))
