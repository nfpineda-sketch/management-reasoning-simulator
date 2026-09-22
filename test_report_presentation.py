"""How the three PDFs read: one identifier, real orders, honest text.

Faculty request 2026-09-23, after reading the first reports produced from a real
encounter. The learner report printed the engine's own field names, the same
encounter carried two different identifiers, and a model field cut off at its
schema cap was presented as a finished sentence.
"""
import pytest

import report_presentation as presentation


# --- one identifier for one encounter ---------------------------------------

def test_the_identifier_joins_the_encounter_and_its_challenge():
    assert presentation.identifier("CE-abc123", "R1-05") == "CE-abc123 · R1-05"


def test_a_missing_part_does_not_leave_a_dangling_separator():
    assert presentation.identifier("CE-abc123", "") == "CE-abc123"
    assert presentation.identifier("", "R1-05") == "R1-05"


def test_something_is_always_shown():
    assert presentation.identifier("", "", fallback="R1-05") == "R1-05"
    assert presentation.identifier("", "") == "Encounter not identified"


# --- a field cut at its cap is not a finished sentence ----------------------

def test_a_field_that_fills_its_cap_and_stops_mid_word_is_marked():
    capped = "x" * presentation.CLAIM_CAPS[0]
    assert presentation.was_truncated(capped)
    assert presentation.claim_text(capped).endswith(presentation.TRUNCATION_NOTE)


def test_a_finished_sentence_is_left_alone():
    ended = "x" * (presentation.CLAIM_CAPS[0] - 1) + "."
    assert not presentation.was_truncated(ended)
    assert presentation.claim_text(ended) == ended


def test_the_cut_is_measured_before_the_prefix_is_removed():
    # The model repeats "AI interpretation:" on every field. Removing it for
    # display makes a capped answer look shorter than its cap.
    prefix = "AI interpretation: "
    capped = prefix + "y" * (presentation.CLAIM_CAPS[0] - len(prefix))
    assert presentation.was_truncated(capped)
    text = presentation.claim_text(capped)
    assert not text.startswith("AI interpretation")
    assert text.endswith(presentation.TRUNCATION_NOTE)


def test_the_repeated_prefix_is_removed_without_touching_the_sentence():
    assert presentation.claim_text("AI interpretation: The resident acted early.") == "The resident acted early."


def test_a_title_has_its_own_cap():
    capped = "z" * presentation.TITLE_CAPS[0]
    assert presentation.was_truncated(capped, presentation.TITLE_CAPS)
    assert not presentation.was_truncated(capped)


# --- an order reads as an order ---------------------------------------------

@pytest.mark.parametrize("action, expected", [
    ({"type": "opioid_analgesia", "agent": "morphine", "dose_mg": 2, "route": "IV"}, "Morphine 2 mg IV"),
    ({"type": "diagnostic", "diagnostic": "ecg", "duration_min": 1}, "12-lead ECG requested · takes 1 min"),
    ({"type": "diagnostic", "diagnostic": "pocus", "result": {"time_min": 15}},
     "Bedside ultrasound (POCUS) requested · result at 15 min"),
    ({"type": "fluid", "volume_ml": 500, "fluid_type": "normal saline", "route": "IV",
      "administration_duration_min": 20}, "500 mL normal saline IV · over 20 min"),
    ({"type": "norepinephrine", "rate": 0.1, "units": "mcg/kg/min", "operation": "start"},
     "Norepinephrine 0.1 mcg/kg/min (started)"),
    ({"type": "disposition", "destination": "ICU"}, "Admission to ICU"),
    ({"type": "disposition", "destination": "home"}, "Discharge home"),
    ({"support_type": "oxygen", "flow_lpm": 15, "device": "non-rebreather mask"},
     "Oxygen 15 L/min via non-rebreather mask"),
    ({"type": "niv", "ipap_cmh2o": 14, "epap_cmh2o": 8, "fio2_percent": 50, "operation": "start"},
     "Non-invasive ventilation 14 cm H2O IPAP, 8 cm H2O EPAP, 50 % FiO2 (started)"),
    ({"type": "transcutaneous_pacing", "rate_per_min": 70, "output_ma": 50, "operation": "start"},
     "Transcutaneous pacing 70 /min, 50 mA (started)"),
    ({"type": "cardioversion", "energy_j": 100}, "Synchronized cardioversion 100 J"),
    ({"type": "vascular_access", "operation": "start"}, "Peripheral IV access (started)"),
])
def test_an_action_keeps_its_dose_route_settings_and_timing(action, expected):
    assert presentation.action_phrase(action) == expected


def test_a_compound_order_keeps_the_drugs_it_gave():
    phrase = presentation.action_phrase({
        "type": "procedural_sedation",
        "medications": [{"agent": "etomidate", "dose_mg": 20, "route": "IV"},
                        {"agent": "rocuronium", "dose_mg": 90, "route": "IV"}]})
    assert "etomidate 20 mg IV" in phrase and "rocuronium 90 mg IV" in phrase


def test_an_order_already_in_place_says_so():
    assert "not repeated" in presentation.action_phrase(
        {"type": "vascular_access", "operation": "start", "repeated": True})


def test_the_engine_narrating_itself_is_not_an_order():
    # "The monitor watches the patient and treats nothing" is the engine
    # describing the response, not something the resident wrote.
    lines = presentation.action_lines([
        {"type": "procedure", "label": "The monitor watches the patient and treats nothing."},
        {"type": "diagnostic", "diagnostic": "lactate"},
    ])
    assert lines == ["Lactate requested"]


def test_the_same_order_twice_is_listed_once():
    action = {"type": "diagnostic", "diagnostic": "lactate"}
    assert presentation.action_lines([action, dict(action)]) == ["Lactate requested"]


def test_an_unknown_action_is_described_rather_than_dumped():
    phrase = presentation.action_phrase({"type": "some_new_thing", "label": "a new supportive measure"})
    assert phrase == "A new supportive measure"
    assert ":" not in phrase


# --- a result carries its unit ----------------------------------------------

@pytest.mark.parametrize("key, value, expected", [
    ("lactate_mmol_l", 3.2, "lactate 3.2 mmol/L"),
    ("glucose_mg_dl", 110, "glucose 110 mg/dL"),
    ("troponin_ng_l", 260, "troponin 260 ng/L"),
    ("lung_sliding", "present", "lung sliding present"),
])
def test_a_result_field_reads_as_a_result(key, value, expected):
    assert presentation.result_field(key, value) == expected


def test_a_study_is_named_the_way_it_is_asked_for():
    assert presentation.study_name("pocus") == "bedside ultrasound (POCUS)"
    assert presentation.study_name("ecg_right") == "right-sided ECG (V3R-V4R)"
    assert presentation.study_name("something_new") == "something new"
