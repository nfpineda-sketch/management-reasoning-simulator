"""Phase 2 shadow core, P2B-4: the golden comparison routed through the final Contracts v2.

The family engine runs through the page's order path, the core takes its interventions
from Contracts v2 alone, and the result must be the committed golden: the same exact
matches and the same known differences KD-S1..KD-S4, nothing tuned.
"""
import json
from dataclasses import replace

import pytest

import pilot_acceptance
from contracts_v2 import trace
from clinical_core.comparison import mismatching
from clinical_core.contracts_input import AdaptedInputs
from clinical_core.contracts_legacy import ONE_MINUTE, _ContractEncounter, run_contract_legacy
from clinical_core.contracts_output import check_shadow_payload
from clinical_core.contracts_shadow import (check_rebuilt_against_engine, contract_golden_report, legacy_names,
                                            run_contract_shadow)
from clinical_core.legacy_adapter import UnsupportedScenario, bank_case, run_legacy
from clinical_core.shadow import (DIFFERENCES, DORMANT, EXPECTED_DIFFERENCES, GOLDEN, SCENARIOS, VARIANTS, acting_mechanisms,
                                  expected_causes, run_shadow)
from clinical_core.state import SCALAR_CHANNELS


@pytest.fixture(scope="module")
def results():
    return {f"{v}/{s}": run_contract_shadow(v, s) for v in VARIANTS for s in SCENARIOS}


def test_the_golden_through_contracts_v2_is_the_committed_golden(results):
    produced = json.loads(json.dumps(contract_golden_report(list(results.values())), allow_nan=False))
    assert produced == json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_the_known_differences_are_the_same_and_all_still_occur(results):
    for key, result in results.items():
        assert set(mismatching(result.summary)) == set(EXPECTED_DIFFERENCES[key]), key
    # Run-dependent mechanisms (P2E-2) count where they acted.
    used = {cause for key, result in results.items()
            for causes in expected_causes(key, acting_mechanisms(result.core)).values() for cause in causes}
    # P2I-2T added the shared blood state; KD-S3 stays registered but no run produces it (DORMANT).
    assert used == set(DIFFERENCES) - set(DORMANT) == {"KD-S1", "KD-S2", "KD-S4", "P2E-2", "P2I-2T"}
    assert set(DIFFERENCES) == {"KD-S1", "KD-S2", "KD-S3", "KD-S4", "P2E-2", "P2I-2T"} and set(DORMANT) == {"KD-S3"}


def test_the_core_runs_the_same_patient_from_the_contracts_as_from_the_engine(results):
    """Minute by minute, every channel, the rhythm, FiO2 and every derived value: exactly equal."""
    for key, result in results.items():
        variant, scenario = key.split("/")
        direct = run_shadow(variant, scenario)
        for through, legacy in zip(result.core.states, direct.core.states):
            assert [getattr(through, c.value) for c in SCALAR_CHANNELS] == [getattr(legacy, c.value)
                                                                         for c in SCALAR_CHANNELS], key
            assert (through.R, through.fio2, through.terminal_since) == (legacy.R, legacy.fio2,
                                                                         legacy.terminal_since), key
        assert [d.to_dict() for d in result.core.derived()] == [d.to_dict() for d in direct.core.derived()], key


def test_the_page_path_runs_the_same_engine_course_as_the_direct_run(results):
    for key, result in results.items():
        variant, scenario = key.split("/")
        spec = SCENARIOS[scenario]
        assert result.legacy.snapshots == run_legacy(variant, spec["orders"], spec["minutes"]).snapshots, key


def test_every_order_of_every_run_is_bound_once_with_its_ledger_identity(results):
    for key, result in results.items():
        ids = [action.order_id for action in result.legacy.actions()]
        bindings = result.adapted.bindings
        assert [b.order_id for b in bindings] == ids, key
        assert {b.disposition for b in bindings} <= {"core_contributor", "core_stop", "no_physiology"}, key
        for turn in result.legacy.turns:
            assert all(a.submission_id == turn.submission_id == f"t{turn.minute}" for a in turn.actions), key
        contributors = {c.id for c in result.adapted.contributors}
        assert {b.order_id for b in bindings if b.disposition == "core_contributor"} <= contributors, key


def test_each_run_emits_a_shadow_trace_that_round_trips(results):
    for key, result in results.items():
        record = result.trace()
        check_shadow_payload(record.payload)
        assert trace.shadow_from_legacy_trace(json.loads(json.dumps(record.payload))).payload == record.payload
        assert [o["order_id"] for o in record.orders] == [a.order_id for a in result.legacy.actions()], key


def test_the_rebuilt_queue_start_and_fio2_are_checked_against_the_engine(results):
    queued = results["gi_bleed_57m/queued_timed_bags"]
    second = queued.adapted.bindings[1]
    assert (second.order_id, second.start_minute) == ("t0:1", 15.0)
    wrong = AdaptedInputs(queued.adapted.contributors,
                          (queued.adapted.bindings[0], replace(second, start_minute=0.0)) + queued.adapted.bindings[2:],
                          queued.adapted.events_not_consumed)
    with pytest.raises(UnsupportedScenario):
        check_rebuilt_against_engine(queued.legacy, wrong)
    oxygen = results["gi_bleed_72f/oxygen_non_rebreather"]
    bad = [replace(c, fio2=0.6) if c.id == "t0:0" else c for c in oxygen.adapted.contributors]
    with pytest.raises(UnsupportedScenario):
        check_rebuilt_against_engine(oxygen.legacy, AdaptedInputs(tuple(bad), oxygen.adapted.bindings, ()))


def test_ledger_ids_map_to_the_legacy_names(results):
    names = legacy_names(results["gi_bleed_57m/untimed_shared_line"].legacy)
    assert {k: v for k, v in names.items() if not v.endswith("reassessment")} == {
        "t0:0": "m000-0-fluid", "t5:0": "m005-0-fluid", "t10:0": "m010-0-blood", "t20:0": "m020-0-blood"}


def test_keeping_the_contracts_does_not_change_the_page_s_order_path():
    """The driver only listens where the live path builds OrderAction v2; the turns are the same."""

    class Plain(pilot_acceptance.Encounter):
        def __init__(self, variant, state):
            self.variant, self.state = variant, state
            self.arrival = dict(state.get("observable") or {})
            self.ledger, self.entries, self._turns = [], [], 0

    texts = [f"{SCENARIOS['stop_fluids']['orders'][0]} {ONE_MINUTE}"] + [ONE_MINUTE] * 3
    plain, listening = Plain("gi_bleed_72f", bank_case("gi_bleed_72f")), _ContractEncounter(
        "gi_bleed_72f", bank_case("gi_bleed_72f"))
    for text in texts:
        assert plain.order(text) == listening.order(text)
    assert plain.state == listening.state


def test_a_turn_that_does_not_run_as_one_plain_minute_is_refused():
    """A bolus without a volume is held with a question: the turn does not run, so the scenario stops."""
    with pytest.raises(UnsupportedScenario):
        run_contract_legacy("gi_bleed_57m", {0: "Give normal saline IV."}, 3)


def test_an_order_the_engine_did_not_act_on_stays_bound_and_gives_nothing():
    """The engine records a 5 L bolus without giving it; the core binds it and gives nothing either."""
    import family_engine
    from clinical_core.contracts_input import adapt
    legacy = run_contract_legacy("gi_bleed_57m", {0: "Give 5000 mL normal saline IV."}, 2)
    adapted = adapt(legacy.actions(), legacy.fates(), [t.time for t in legacy.turns], [t.events for t in legacy.turns],
                    gi_bleed=family_engine.GI_BLEED, devices=family_engine._DEVICES)
    bolus = adapted.binding("t0:0")
    assert (bolus.fate, bolus.disposition, bolus.source_key) == ("RECORDED_NOT_MODELLED", "not_acted_by_engine", None)
    assert adapted.contributors == ()


def test_the_contract_route_is_deterministic():
    one, two = run_contract_shadow("gi_bleed_57m", "stop_fluids"), run_contract_shadow("gi_bleed_57m", "stop_fluids")
    assert one.trace().payload == two.trace().payload and one.core.digest() == two.core.digest()
