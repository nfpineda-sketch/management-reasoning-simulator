"""Phase 0 (0G, 0H): what the room shows follows the state, and every event says where it came from.

Pre-pilot measurement safety, 2026-10-06. The clinical engine audit found arrests announced in
prose while the monitor kept a pulse and a pressure (anaphylaxis, trauma, bradycardia), an
arrest's rate of 0 relabelled "sinus bradycardia", a normal examination after an arrest, a
laboratory potassium that stayed at the authored value while the engine's rose, and events the
record could not tell apart from the resident's own doing.
"""
import pytest

import encounter_generator
import event_provenance
import family_engine
import observation_consistency
import time_semantics
import trace_phase0
from family_parser import parse_family_actions
from test_curriculum_trajectories import load_engine
from test_phase0_order_ledger import _encounter, submit

BANK = {  # family, the challenge that launches it, the variants of the pilot bank that arrest untreated
    "anaphylaxis_29f": ("anaphylaxis", "R1-06"), "anaphylaxis_63m_betablocked": ("anaphylaxis", "R1-06"),
    "trauma_limb_hemorrhage_27m": ("trauma", "R2-05"), "trauma_hemothorax_41m": ("trauma", "R2-05"),
    "bradycardia_ccb_68m": ("bradycardia", "R2-04"), "bradycardia_avb3_78f": ("bradycardia", "R2-04"),
    "bradycardia_bb_54f": ("bradycardia", "R2-04"), "bradycardia_hyperk_63m": ("bradycardia", "R2-04"),
    "opioid_35m": ("opioid", "R1-06"), "acs_54m_inferior": ("acs", "R2-02"),
}


def _state(variant):
    family, challenge = BANK.get(variant, (None, None))
    return encounter_generator.generate_encounter(challenge, load_engine()["INITIAL_STATE"], seed=17,
                                                  family_id=family, variant_id=variant)["state"]


def _wait(state, minutes):
    text = f"Wait {minutes} minutes."
    return family_engine.execute_family_bundle(state, time_semantics.apply(text, parse_family_actions(text)))


def _until_arrest(state, limit=6):
    results = []
    for _ in range(limit):
        result = _wait(state, 120)
        results.append(result)
        assert observation_consistency.check(state) == [], observation_consistency.check(state)
        if observation_consistency.arrest_minute(state) is not None or not result.get("executed"):
            break
    return results


# --- 0G: an arrest is an arrest ----------------------------------------------------------
@pytest.mark.parametrize("variant", sorted(BANK))
def test_an_untreated_arrest_is_the_engines_arrest_and_nothing_contradicts_it(variant):
    state = _state(variant)
    results = _until_arrest(state)
    minute = observation_consistency.arrest_minute(state)
    assert minute is not None, f"{variant} reached no arrest in {state['sim_time']} min"
    o = state["observable"]
    assert o["pulse_present"] is False and o["hr"] == 0 and not o["rhythm"].lower().startswith("sinus")
    assert o["rhythm"] in ("Asystole", "VF")
    # No pressure, rate or normal finding is shown after it, and no further order runs.
    update = family_engine.clinical_update(state)
    assert update.startswith("No pulse") and "no blood pressure" in update and "mmHg" not in update
    for region in family_engine.available_regions(state):
        assert "cardiac arrest" in family_engine.examination_finding(state, region)
    after = family_engine.execute_family_bundle(state, parse_family_actions("Give 1 L LR. Reassess in 10 minutes."))
    assert after.get("terminal_locked") and not after["executed"]
    # The arrest is one event, terminal, with its provenance.
    arrests = [e for r in results for e in r.get("events") or [] if e["terminal"]]
    assert len(arrests) == 1 and arrests[0]["minute"] == minute
    assert "resuscitation" not in str(arrests[0]["label"]).lower()


def test_the_page_says_the_arrest_in_the_agreed_words_and_invents_no_recovery(tmp_path, monkeypatch):
    at = _encounter(tmp_path, monkeypatch, "anaphylaxis_29f", "R1-06")
    submit(at, "Wait 60 minutes.")  # stops at the collapse, minute 19
    assert at.session_state["management_trace"][-1]["interrupted"]["kind"] == "circulatory_collapse"
    submit(at, "Wait 60 minutes.")  # the arrest, minute 25
    texts = [str(e.get("text") or "") for e in at.session_state["events"]]
    minute = observation_consistency.arrest_minute(at.session_state["state"])
    assert minute == 25
    assert (f"Cardiac arrest occurred at minute {minute}. Resuscitation management is not modelled in this pilot. "
            "Subsequent management is not assessable.") in texts
    entry = at.session_state["management_trace"][-1]
    assert entry["observation_snapshot"]["arrest"] == {"minute": minute}
    assert any(item["kind"] == "resuscitation_not_modelled" for item in entry["limitations"])
    submit(at, "Give epinephrine 0.5 mg IM. Reassess in 5 minutes.")
    assert at.session_state["state"]["observable"]["pulse_present"] is False
    assert at.session_state["management_trace"][-1]["execution_status"] == "terminal_locked"


def test_a_rate_of_zero_is_never_called_sinus():
    state = _state("opioid_35m")
    _until_arrest(state)
    assert state["observable"]["hr"] == 0 and state["observable"]["rhythm"] == "Asystole"
    broken = dict(state)
    broken["observable"] = {**state["observable"], "rhythm": "Sinus bradycardia", "pulse_present": True}
    assert observation_consistency.check(broken)  # the checker names it


# --- 0G: a laboratory the engine models reads the engine ---------------------------------------
def test_the_hyperkalaemia_laboratory_potassium_reads_the_engine():
    state = _state("bradycardia_hyperk_63m")
    authored = state["encounter_spec"]["clinical_case"]["investigations"]["basic_labs"]["result"]["potassium_mmol_l"]
    _wait(state, 40)
    engine_k = round(state["family_state"]["potassium"], 1)
    assert engine_k != authored
    family_engine.execute_family_bundle(state, parse_family_actions("Order basic labs. Reassess in 30 minutes."))
    reported = state["diagnostics"]["basic_labs"]["potassium_mmol_l"]
    collected_at = state["diagnostics"]["basic_labs"]["collected_at_min"]
    assert reported != authored and collected_at == 40 and reported == engine_k


def test_static_observations_are_declared_static():
    declared = observation_consistency.declaration(_state("acs_54m_inferior"))
    assert "chest_xray" in declared["studies"]["static"] and "ecg" in declared["studies"]["dynamic"]
    assert "Peripheral perfusion" in declared["examination"]["dynamic"]
    assert declared["history"].startswith("authored (static)")


# --- 0H: every meaningful event has its provenance ---------------------------------------------
def test_every_event_of_the_course_declares_where_it_comes_from():
    seen = []
    for variant in ("acs_54m_inferior", "opioid_35m", "anaphylaxis_29f", "trauma_limb_hemorrhage_27m",
                    "bradycardia_hyperk_63m"):
        state = _state(variant)
        seen += [e for r in _until_arrest(state) for e in r.get("events") or []]
    assert seen
    for event in seen:
        assert event["cause_class"] in event_provenance.CAUSE_CLASSES
        assert event["preventability"] in event_provenance.PREVENTABILITY
        assert event["severity"] in event_provenance.SEVERITY
        assert isinstance(event["minute"], int) and event["preventability_reason"]
    block = next(e for e in seen if e["kind"] == "av_block")
    assert (block["cause_class"], block["preventability"]) == ("SCRIPTED_NATURAL_HISTORY",
                                                               "NOT_PREVENTABLE_IN_SIMULATOR")


def test_a_treatment_event_names_the_orders_it_follows():
    state = _state("acs_54m_inferior")
    parsed = parse_family_actions("Give 2 units packed red blood cells. Reassess in 60 minutes.")
    for index, action in enumerate(parsed["actions"]):
        action["_order_id"] = f"t:{index}"
    result = family_engine.execute_family_bundle(state, parsed)
    overload = [e for e in result["events"] if e["kind"] == "transfusion_overload"]
    assert overload and overload[0]["cause_class"] == "RESIDENT_TREATMENT"
    assert overload[0]["source_order_ids"] and all(i.startswith("t:") for i in overload[0]["source_order_ids"])


def test_the_trace_records_observation_limitations_and_versions(tmp_path, monkeypatch):
    at = _encounter(tmp_path, monkeypatch, "acs_54m_inferior", "R2-02")
    submit(at, "Repeat ECG in 30 minutes.")
    submit(at, "Reassess in 120 minutes.")
    later, block = at.session_state["management_trace"][-2:]
    assert [item["kind"] for item in later["limitations"]] == ["unsupported_future_execution"]
    assert any(item["kind"] == "scripted_event" and item["event"] == "av_block" for item in block["limitations"])
    for entry in (later, block):
        assert entry["versions"]["variant_id"] == "acs_54m_inferior"
        assert entry["versions"]["ledger_schema"] == "order_ledger_v1"
        assert entry["observation_snapshot"]["inconsistencies"] == []
    assert block["observation_snapshot"]["visible"]["rhythm"] == "Complete AV block"
    assert set(trace_phase0.LIMITATION_KINDS) >= {item["kind"] for item in later["limitations"] + block["limitations"]}
