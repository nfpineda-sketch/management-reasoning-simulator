"""The obstructed right ventricle (faculty decisions 2026-09-20).

Faculty: systemic thrombolysis if there is sustained hypotension, and punish volume
given fast. Teaching magnitudes pending review.
"""
import pytest

import pe_obstruction as pe
from family_engine import execute_family_bundle
from family_parser import parse_family_actions
from test_cognitive_encounters import encounter
from test_curriculum_trajectories import load_engine

OXYGEN = "Start oxygen 15 L/min non-rebreather. Reassess in 20 minutes."
LYSE = "Give alteplase 100 mg IV. Reassess in 40 minutes."
FAST = "Give 1000 mL normal saline IV over 10 minutes. Reassess in 12 minutes."
SLOW = "Give 250 mL normal saline IV over 30 minutes. Reassess in 32 minutes."


@pytest.fixture(scope="module")
def engine():
    return load_engine()


def course(engine, orders, variant="pulmonary_embolism_61m"):
    state = encounter(engine, "pulmonary_embolism", variant)["state"]
    events = []
    for order in orders:
        result = execute_family_bundle(state, parse_family_actions(order))
        assert result["executed"], result["clarification"]
        events += result["action_summaries"]
    return state, " | ".join(str(e.get("label", "")) for e in events)


def test_fast_volume_distends_the_ventricle_and_drops_the_output(engine):
    fast, labels = course(engine, [FAST])
    assert fast["family_state"]["rv_strain"] > .3
    assert fast["observable"]["sbp"] < 80 and fast["observable"]["spo2"] < 88
    assert "faster than the obstructed right ventricle can accept" in labels


def test_slow_volume_is_neither_treatment_nor_insult(engine):
    slow, labels = course(engine, [SLOW])
    assert slow["family_state"].get("rv_strain", 0) == 0
    assert "faster than" not in labels
    untouched, _ = course(engine, ["Reassess in 32 minutes."])
    assert slow["observable"]["sbp"] == untouched["observable"]["sbp"]


def test_the_insult_recovers_slowly(engine):
    state, _ = course(engine, [FAST])
    worst = state["observable"]["sbp"]
    execute_family_bundle(state, parse_family_actions("Reassess in 45 minutes."))
    assert state["observable"]["sbp"] > worst
    assert state["family_state"]["rv_strain"] < .2


def test_fifteen_consecutive_low_minutes_are_announced_as_sustained_hypotension(engine):
    state, labels = course(engine, [OXYGEN])
    assert state["family_state"]["sustained_hypotension_min"] >= pe.SUSTAINED_HYPOTENSION_MIN
    assert pe.indicated(state["family_state"])
    assert (f"below {pe.HYPOTENSION_SBP} mmHg for {pe.SUSTAINED_HYPOTENSION_MIN} consecutive minutes"
            in labels)


def test_thrombolysis_in_obstructive_shock_dissolves_the_obstruction(engine):
    state, labels = course(engine, [OXYGEN, LYSE, "Reassess in 40 minutes."])
    assert "given in obstructive shock" in labels
    assert state["family_state"]["circulation"] < .8
    # From 86/54 at arrival, without a vasopressor.
    assert state["observable"]["sbp"] > 98 and state["observable"]["hr"] < 130


@pytest.mark.parametrize("minute", [0, 5, 10, 14])
def test_arrival_in_obstructive_shock_needs_no_further_wait(engine, minute):
    """61m arrives hypotensive with cool extremities, a refill of 5 s and a lactate of 4.8 (2026-09-29)."""
    orders = ([f"Reassess in {minute} minutes."] if minute else []) + [LYSE, "Reassess in 45 minutes."]
    state, labels = course(engine, orders)
    f = state["family_state"]
    assert f["lysis_indicated"] is True and f["lysis_basis"] == "obstructive_shock"
    assert f["obstructive_shock_from_min"] == 0
    assert "given in obstructive shock" in labels and "before the hypotension" not in labels
    assert state["observable"]["sbp"] > 95 and f["circulation"] < .8


def test_a_normotensive_submassive_embolism_has_no_indication(engine):
    state, labels = course(engine, [LYSE], "pulmonary_embolism_33f")
    assert "without the hemodynamic indication" in labels and "no hypotension from the embolism" in labels
    assert not pe.indicated(state["family_state"])
    assert state["family_state"]["lysis_indicated"] is False
    # P-04 (2026-09-30): the drug acts whether or not it was indicated, and the note promises nothing.
    assert "acts on the clot whether or not it was indicated" in labels
    assert "obstruction is unchanged" not in labels and "begins to fall" not in labels


def test_an_unindicated_thrombolytic_still_reperfuses_and_is_still_judged_on_its_minute(engine):
    """P-04 B (2026-09-30): the effect, the bleeding and the judgement of the decision are three things."""
    from test_pe_thrombolysis_screening import lysis_row, played
    lysed, _ = course(engine, [LYSE, "Reassess in 50 minutes."], "pulmonary_embolism_33f")
    untreated, _ = course(engine, ["Reassess in 55 minutes."], "pulmonary_embolism_33f")
    f = lysed["family_state"]
    assert f["lysis_indicated"] is False and pe.lysis_effect(f) > .7
    embolism = f["circulation"] - f.get("pe_bleed_circulation", 0.0)
    assert embolism < untreated["family_state"]["circulation"] - .2      # the clot dissolved
    assert f["pe_bleed_circulation"] > 0 and f["major_bleed_reported"]   # and she bleeds, as her case declares
    assert lysed["observable"]["spo2"] > untreated["observable"]["spo2"]
    # A later improvement does not make the order a correct one: the screening reads its minute.
    record = played(engine, [LYSE, "Reassess in 50 minutes."])
    row = lysis_row(record)
    assert row["status"] == "met" and "what followed it does not change that" in str(row)


def test_a_pressure_held_up_by_a_vasopressor_it_needs_still_counts(engine):
    state, labels = course(engine, [
        "Start oxygen 15 L/min non-rebreather. Start norepinephrine 0.1 mcg/kg/min. Reassess in 20 minutes.",
        LYSE, "Reassess in 40 minutes."])
    assert state["observable"]["sbp"] > 105
    assert "given in obstructive shock" in labels
    [record] = state["family_state"]["lysis_doses"]
    assert record["data"]["vasopressor_needed"] is True and record["data"]["sbp"] < pe.HYPOTENSION_SBP
    assert state["family_state"]["circulation"] < .8


def test_starting_norepinephrine_creates_no_indication(engine):
    """33f is not hypotensive: a vasopressor she does not need never starts the clock (2026-09-29)."""
    state, labels = course(engine, ["Start norepinephrine 0.1 mcg/kg/min. Reassess in 20 minutes.", LYSE,
                                    "Reassess in 30 minutes."], "pulmonary_embolism_33f")
    f = state["family_state"]
    assert f["sustained_hypotension_min"] == 0 and not f.get("lysis_indication_met")
    assert "sustained hypotension" not in labels
    assert f["lysis_indicated"] is False
    assert "on a vasopressor the pressure does not need" in labels


@pytest.mark.parametrize("drop", ["sedation_bp_drop", "morphine_preload_drop"])
def test_a_drug_induced_drop_keeps_its_effect_and_is_not_the_embolism_s_shock(engine, drop):
    from family_engine import _surface
    state, _ = course(engine, ["Reassess in 1 minutes."], "pulmonary_embolism_33f")
    state["family_state"][drop] = 40.0
    _surface(state)
    assert state["observable"]["sbp"] < pe.HYPOTENSION_SBP            # the patient does get hypotensive
    assert state["family_state"]["pe_attributable"]["low"] is False  # but not from the embolism
    assert not pe.indicated(state["family_state"])


def test_bleeding_after_a_thrombolytic_is_not_the_embolism_s_shock(engine):
    state, labels = course(engine, [LYSE, "Reassess in 50 minutes."], "pulmonary_embolism_33f")
    f = state["family_state"]
    assert "Bleeding from the surgical site" in labels and f["pe_bleed_circulation"] > 0
    assert f["pe_attributable"]["sbp"] > state["observable"]["sbp"] + 1


def test_the_clock_counts_only_consecutive_minutes():
    low = pe.assessment(85, 2.2, 1.2, False)
    recovered = pe.assessment(95, 2.2, 1.2, False)
    f = {"elapsed": 0}
    for _ in range(pe.SUSTAINED_HYPOTENSION_MIN - 1):
        pe.track_hypotension(f, low)
    assert pe.basis(f, low) is None                      # a hypotension without hypoperfusion waits
    pe.track_hypotension(f, recovered)
    assert f["sustained_hypotension_min"] == 0            # a real recovery starts the count again
    for _ in range(pe.SUSTAINED_HYPOTENSION_MIN - 1):
        pe.track_hypotension(f, low)
    assert pe.basis(f, low) is None
    pe.track_hypotension(f, low)
    assert pe.basis(f, low) == "persistent_hypotension"
    assert pe.basis(f, recovered) is None                 # every order is judged on its own minute
    assert pe.criteria_met_before(f)                      # the history stays, as history


def test_one_sign_of_hypoperfusion_makes_a_hypotension_obstructive_shock_at_once():
    for crt, lactate, altered, sign in ((3.5, 1.2, False, "peripheral_hypoperfusion"),
                                        (2.2, 2.1, False, "lactate"),
                                        (2.2, 1.2, True, "altered_consciousness")):
        current = pe.assessment(88, crt, lactate, altered)
        assert current["signs"] == [sign]
        assert pe.basis({"elapsed": 0}, current) == "obstructive_shock"
    mild = pe.assessment(88, 3.4, 2.0, False)          # cool with a refill under 3.5 s, lactate at 2.0
    assert mild["signs"] == [] and pe.basis({"elapsed": 0}, mild) is None


def test_a_persisting_shock_does_not_make_a_second_dose_indicated(engine):
    # The second dose comes at minute 5, before the first has begun to act: the shock persists.
    once = "Give alteplase 100 mg IV."
    state, labels = course(engine, [once, once, "Reassess in 30 minutes."])
    f = state["family_state"]
    first, second = f["lysis_doses"]
    assert first["basis"] == "obstructive_shock" and f["lysis_at"] == first["minute"]
    assert second["basis"] is None and second["repeat_of_minute"] == first["minute"]
    assert second["criteria_present"] == "obstructive_shock"
    # P-05 D (2026-09-30): a second full course, recorded with its added exposure.
    assert second["course"] == "second_course" and second["additional_exposure"] is True
    assert "A second course of systemic thrombolysis is recorded" in labels
    assert "not evidence that repeating has no effect" in labels
    assert f["circulation"] < .8                          # the first dose keeps working


def test_each_thrombolytic_summary_carries_its_basis_minute_and_data(engine):
    state = encounter(engine, "pulmonary_embolism", "pulmonary_embolism_61m")["state"]
    result = execute_family_bundle(state, parse_family_actions(LYSE))
    [summary] = [s for s in result["action_summaries"] if s.get("type") == "thrombolysis"]
    record = summary["thrombolysis_indication"]
    assert record["version"] == pe.INDICATION_VERSION and record["minute"] == 0
    assert record["basis"] == "obstructive_shock" and summary["indication_basis"] == "obstructive_shock"
    assert record["data"]["engine_internal"] is True
    assert set(record["data"]["signs"]) == {"peripheral_hypoperfusion", "lactate"}


def test_anticoagulation_alone_does_not_relieve_the_obstruction(engine):
    state, _ = course(engine, ["Start oxygen 15 L/min non-rebreather. Give heparin 5000 units IV. Reassess in 40 minutes.",
                               "Reassess in 60 minutes."])
    assert state["family_state"]["circulation"] > 1.0
    assert state["observable"]["sbp"] < 90


def test_a_needed_vasopressor_keeps_the_criterion_and_the_history_is_kept(engine):
    state, _ = course(engine, [OXYGEN, "Start norepinephrine 0.2 mcg/kg/min. Reassess in 30 minutes."])
    f = state["family_state"]
    assert state["observable"]["sbp"] > pe.HYPOTENSION_SBP
    assert pe.indicated(f)                                  # the embolism still leaves it below 90
    assert f["obstructive_shock_from_min"] == 0 and f["persistent_hypotension_from_min"] >= 14


TUBE = "Give ketamine 100 mg IV and intubate VC/AC FiO2 100% PEEP 5. Reassess in 10 minutes."


def test_intubating_an_obstructed_circulation_drops_the_pressure(engine):
    tubed, _ = course(engine, [TUBE])
    untouched, _ = course(engine, ["Reassess in 10 minutes."])
    assert tubed["observable"]["sbp"] < untouched["observable"]["sbp"] - 12
    assert tubed["observable"]["hr"] > untouched["observable"]["hr"] + 5


def test_more_peep_costs_more(engine):
    modest, _ = course(engine, [TUBE])
    high, _ = course(engine, ["Give ketamine 100 mg IV and intubate VC/AC FiO2 100% PEEP 12. Reassess in 10 minutes."])
    assert high["observable"]["sbp"] < modest["observable"]["sbp"] - 5


def test_the_same_tube_is_tolerated_once_the_obstruction_dissolves(engine):
    state, _ = course(engine, [OXYGEN, LYSE, "Reassess in 30 minutes."])
    before = state["observable"]["sbp"]
    execute_family_bundle(state, parse_family_actions(TUBE))
    assert state["observable"]["sbp"] >= before - 3


def test_the_thrombolytic_bleeds_slowly_even_when_it_is_indicated(engine):
    state, _ = course(engine, [OXYGEN, LYSE, "Reassess in 30 minutes."])
    start = 12.6
    assert state["family_state"]["hemoglobin"] < start - .3
    assert state["family_state"]["hemoglobin"] > start - 1.5
    assert state["family_state"].get("major_bleed_reported") is None


def test_a_patient_with_a_reason_to_bleed_bleeds_badly(engine, monkeypatch):
    orders = [LYSE, "Order hemoglobin. Reassess in 40 minutes.", "Reassess in 40 minutes."]
    state, labels = course(engine, orders, "pulmonary_embolism_33f")
    assert "Bleeding from the surgical site" in labels
    assert state["family_state"]["hemoglobin"] < 10
    # The bleed says only what is certain: the pressure depends on everything else acting too (P-04).
    assert "and the pressure with it" not in labels
    # The bleeding costs circulation too: she is worse than the same dose without her reason to bleed.
    monkeypatch.setattr(pe, "bleeding_risk", lambda state: None)
    dry, dry_labels = course(engine, orders, "pulmonary_embolism_33f")
    assert "Bleeding from" not in dry_labels
    assert state["observable"]["sbp"] < dry["observable"]["sbp"]
    assert state["observable"]["hr"] > dry["observable"]["hr"]
    assert state["family_state"]["hemoglobin"] < dry["family_state"]["hemoglobin"] - 1.5


def test_the_rest_of_an_alteplase_regimen_completes_the_first_dose(engine):
    """P-05 (2026-09-30): a bolus and the rest are one regimen; the first dose keeps its clock."""
    state, labels = course(engine, ["Give alteplase 10 mg IV. Reassess in 2 minutes.",
                                    "Give alteplase 90 mg IV. Reassess in 30 minutes."])
    f = state["family_state"]
    first, rest = f["lysis_doses"]
    assert first["course"] == "initial" and rest["course"] == "initial_regimen"
    assert rest["regimen_total_mg"] == 100 and "additional_exposure" not in rest
    assert f["lysis_at"] == first["minute"]
    assert "recorded as part of the initial regimen begun at minute 0 (100 mg in all)" in labels
    assert "second course" not in labels


def test_a_second_course_neither_restarts_nor_stops_the_first_and_adds_no_effect(engine):
    """P-05 D: the pending dissolution goes on from the first dose; the repeat changes nothing modelled."""
    once, again = "Give alteplase 100 mg IV. Reassess in 10 minutes.", "Give tenecteplase 50 mg IV."
    repeated, labels = course(engine, [once, again, "Reassess in 30 minutes."])
    single, _ = course(engine, [once, "Reassess in 5 minutes.", "Reassess in 30 minutes."])
    assert repeated["sim_time"] == single["sim_time"]      # the same minutes, one dose fewer
    f = repeated["family_state"]
    assert f["lysis_at"] == 0 and f["lysis_doses"][1]["course"] == "second_course"
    assert f["circulation"] == pytest.approx(single["family_state"]["circulation"])
    assert f["hemoglobin"] == pytest.approx(single["family_state"]["hemoglobin"])
    assert "Bleeding from" not in labels                   # no bleed is described that was not modelled
    # Each dose is listed once in the medicines given: the exposure is what was given, no more.
    given = [m for m in repeated["treatments"]["administered_medications"]
             if m.get("agent") in {"alteplase", "tenecteplase"}]
    assert [(m["agent"], m["dose_mg"]) for m in given] == [("alteplase", 100), ("tenecteplase", 50)]


def test_the_case_without_a_declared_risk_has_no_major_bleed(engine):
    state, labels = course(engine, [OXYGEN, LYSE, "Reassess in 60 minutes."])
    assert "Bleeding from" not in labels
    assert state["family_state"].get("major_bleed_reported") is None


# Found playing the pulmonary embolism correctly (2026-09-21): "Mantén la
# heparina" — a decision to change nothing — held the whole turn, reassessment
# included, asking for a dose the resident never meant to give.

def continuation(engine, case_id, *orders):
    from family_engine import execute_family_bundle
    from family_parser import parse_family_actions
    state = encounter(engine, "pulmonary_embolism", case_id)["state"]
    results = []
    for order in orders:
        results.append(execute_family_bundle(state, parse_family_actions(order)))
    return state, results


GIVE = "Give heparin 5000 units IV. Reassess in 20 minutes."


@pytest.mark.parametrize("text", ["Mantén la heparina. Reevalúa en 30 minutos.",
                                  "Continue heparin. Reassess in 30 minutes."])
def test_continuing_a_dose_already_given_is_recorded_not_questioned(engine, text):
    state, (_, kept) = continuation(engine, "pulmonary_embolism_33f", GIVE, text)
    assert kept["executed"], kept.get("clarification")
    labels = [str(summary.get("label", summary)) for summary in kept["action_summaries"]]
    assert any("already given at minute" in label and "not repeated" in label for label in labels), labels
    # The clock moved: the reassessment in the same turn was not lost with it.
    assert state["sim_time"] == 50


def test_continuing_what_was_never_given_still_asks(engine):
    _, (result,) = continuation(engine, "pulmonary_embolism_33f", "Continue aspirin. Reassess in 10 minutes.")
    assert not result["executed"]
    assert "No aspirin is recorded as given" in result["clarification"]


def test_a_continuation_administers_nothing(engine):
    state, _ = continuation(engine, "pulmonary_embolism_33f", GIVE,
                            "Mantén la heparina. Reevalúa en 30 minutos.")
    given = [record for record in state["treatments"]["administered_medications"]
             if str(record.get("agent", "")).lower() == "heparin"]
    assert len(given) == 1, given


def test_stopping_a_fixed_dose_is_still_not_an_order(engine):
    _, (_, stopped) = continuation(engine, "pulmonary_embolism_33f", GIVE,
                                   "Suspende la heparina. Reevalúa en 10 minutos.")
    assert not stopped["executed"]
    assert "explicit new dose" in stopped["clarification"]
