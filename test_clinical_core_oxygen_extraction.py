"""Phase 2 shadow core, P2I-2P: oxygen delivery, demand and the extraction reserve.

The delivery index is DO2 over normal resting DO2, the demand index VO2 demand over normal resting
VO2, and D integrates only the demand left unmet once extraction is exhausted. The canonical
reserve stays the neutral 1 (the pre-P2I-2P model); every other reserve here is synthetic.
"""
import json
import math
from dataclasses import replace
from pathlib import Path

import pytest

from clinical_core import calibration, decision_pack, faculty_constraints as fc, lactate_constraints, lactate_slice
from clinical_core import oxygen_probes as op
from clinical_core.bands import Drift
from clinical_core.derived import (DEFAULT_PROFILE, OXYGEN_ADEQUATE, OXYGEN_COMPENSATED, OXYGEN_CRITICAL, PARAMETERS,
                                   PROVISIONAL, CoreProfile, delivery_deficit, effective_oxygen_deficit,
                                   oxygen_balance)
from clinical_core.integration import run
from clinical_core.state import CoreInvariantError

ROOT = Path(__file__).resolve().parent
DOCUMENT = ROOT / "docs" / "revision" / "P2I2P_FISIOLOGIA_ENTREGA_O2.md"
DATA = ROOT / "docs" / "revision" / "P2I2P_oxygen_probes.json"


def test_the_reserve_is_provisional_neutral_and_never_below_normal_extraction():
    assert DEFAULT_PROFILE.oxygen_extraction_reserve == 1.0
    assert PARAMETERS["oxygen_extraction_reserve"][0] == PROVISIONAL
    assert "TBD" in PARAMETERS["oxygen_extraction_reserve"][1]
    assert "oxygen_extraction_reserve" not in calibration.REGISTRY
    with pytest.raises(CoreInvariantError):
        CoreProfile(oxygen_extraction_reserve=0.99)


@pytest.mark.parametrize("demand", [0.8, 1.0, 1.2, 1.5])
@pytest.mark.parametrize("delivery", [0.0, 0.3, 0.6, 0.99, 1.0, 1.4])
def test_reserve_one_is_exactly_the_earlier_deficit(demand, delivery):
    assert effective_oxygen_deficit(demand, delivery, 1.0) == delivery_deficit(demand, delivery)


def test_the_balance_states_follow_the_supply_ratio_and_the_reserve():
    assert oxygen_balance(1.2, 1.0, 2.5).state == OXYGEN_ADEQUATE
    assert oxygen_balance(1.0, 1.0, 2.5).state == OXYGEN_ADEQUATE
    compensated = oxygen_balance(0.5, 1.0, 2.5)
    assert compensated.state == OXYGEN_COMPENSATED and compensated.effective_deficit == 0.0
    assert compensated.required_extraction == pytest.approx(2.0) and compensated.critical_delivery == 0.4
    assert oxygen_balance(0.4, 1.0, 2.5).state == OXYGEN_COMPENSATED  # at the critical delivery itself
    critical = oxygen_balance(0.2, 1.0, 2.5)
    assert critical.state == OXYGEN_CRITICAL and critical.effective_deficit == pytest.approx(0.5)
    # Demand moves the critical delivery: the same delivery is compensated at rest, critical at 1.5.
    assert oxygen_balance(0.5, 1.0, 2.5).state == OXYGEN_COMPENSATED
    assert oxygen_balance(0.5, 1.5, 2.5).state == OXYGEN_CRITICAL
    assert oxygen_balance(0.5, 1.5, 2.5).critical_delivery == pytest.approx(0.6)
    assert oxygen_balance(0.5, 1.5, 4.0).state == OXYGEN_COMPENSATED
    # Reserve 1: no compensated state (the pre-P2I-2P model).
    assert {oxygen_balance(x / 10, 1.0, 1.0).state for x in range(1, 13)} == {OXYGEN_ADEQUATE, OXYGEN_CRITICAL}
    assert math.isinf(oxygen_balance(0.0, 1.0, 2.5).required_extraction)


@pytest.mark.parametrize("name", ["B compensated low delivery", "G high demand, delivery preserved",
                                  "J severe sustained critical deficit"])
def test_debt_integrates_only_the_effective_deficit(name):
    """Delivery at 70 % of normal, or demand x 1.5: compensated with a reserve, so no debt; with
    none, debt accrues. Each minute integrates the delivery at its start against its own demand."""
    contributors = op.PROBES[name][1]
    for reserve in (1.0, 2.5):
        profile = replace(DEFAULT_PROFILE, oxygen_extraction_reserve=reserve)
        states = run(op.NEUTRAL, contributors, 60, profile).states
        rows, _ = op.trajectory_rows(op.NEUTRAL, contributors, reserve, 60)
        assert [row["D"] for row in rows] == [state.D for state in states]
        for before, after in zip(rows, rows[1:]):
            deficit = effective_oxygen_deficit(after["demand"], before["delivery"], reserve)
            expected = before["D"] + profile.debt_per_delivery_deficit * deficit - before["D"] / profile.debt_clearance_tau_min
            assert after["D"] == pytest.approx(max(0.0, expected), abs=1e-12)
        compensated = name != "J severe sustained critical deficit" and reserve > 1.0
        assert (states[-1].D == 0.0) is compensated


def test_only_the_product_of_reserve_and_arrival_ratio_reaches_debt_and_lactate():
    """The structural result P2I-2P reports: re-anchoring the GI arrival band (ratio / reserve)
    leaves D and lactate exactly as today; keeping it fixed does not."""
    candidate = next(item for item in decision_pack.admissible() if item.delivery == "lower")
    for case in lactate_slice.CASES:
        for scenario in ("L1", "L3"):
            canonical = op._core_rows(case, candidate, scenario, 1.0)
            for reserve in (2.0, 2.5, 3.0):
                anchored = op._core_rows(case, candidate, scenario, reserve, op.RE_ANCHORED)
                assert op._same_dynamics(anchored, canonical) < 1e-9
                assert anchored[0]["delivery"] == pytest.approx(canonical[0]["delivery"] / reserve)
            assert op._same_dynamics(op._core_rows(case, candidate, scenario, 2.5, op.FIXED), canonical) > 0.1


def test_the_probes_behave_as_the_extraction_reserve_says():
    reserve = op.SYNTHETIC_RESERVE
    probes = {name: op.probe(name, reserve) for name in op.PROBES}
    assert probes["A normal"]["states_seen"] == [OXYGEN_ADEQUATE] and probes["A normal"]["max_D"] == 0.0
    for name in ("B compensated low delivery", "G high demand, delivery preserved"):
        assert OXYGEN_CRITICAL not in probes[name]["states_seen"] and probes[name]["max_D"] == 0.0, name
        assert OXYGEN_CRITICAL in op.probe(name, 1.0)["states_seen"], name
    crossing = probes["C delivery crossing the critical region"]
    first = crossing["first_critical_minute"]
    rows, _ = op.trajectory_rows(op.NEUTRAL, op.PROBES["C delivery crossing the critical region"][1], reserve)
    assert first is not None and all(row["D"] == 0.0 for row in rows[:first + 1])
    assert rows[first]["delivery"] < 1.0 / reserve <= rows[first - 1]["delivery"]
    # Restoration: D stops accruing when delivery recovers, and lactate need not fall at once.
    resuscitation = probes["H resuscitation restores delivery"]["points"]
    assert resuscitation["60"]["state"] == OXYGEN_ADEQUATE and resuscitation["120"]["D"] < resuscitation["60"]["D"]
    # A severe sustained deficit is critical early and reaches the deficit-based synthetic limit.
    severe = probes["J severe sustained critical deficit"]
    assert severe["first_critical_minute"] <= 15 and severe["collapse_limit_reached"]["oxygen_deficit"] is not None
    # Anaemia alone with output preserved (Hb 13 to the channel's floor of 3 g/dL): the output-based
    # burden never moves, the deficit-based one does.
    rows, _ = op.trajectory_rows(op.NEUTRAL, (Drift("hb", "hb", 0, 120, -0.09),), reserve)
    assert rows[-1]["state"] == OXYGEN_CRITICAL and rows[-1]["hb"] == pytest.approx(3.0)
    assert rows[-1]["burden_output"] == 0.0 < rows[-1]["burden_oxygen_deficit"]


def test_the_revisit_reads_the_committed_p2i2r_survivors_and_never_runs_an_fd_lac_rule(monkeypatch):
    survivors = op.frozen_survivors()
    data = json.loads((ROOT / "docs" / "revision" / "P2I2_lactate_constraints.json").read_text(encoding="utf-8"))
    assert survivors == data["faculty_constrained_region"] and len(survivors) == data["counts"]["all_six"]
    assert data["filter_digest"] == lactate_constraints.RESULTS_PENDING_REFILTER["filter_digest"]

    def refuse(*args, **kwargs):
        raise AssertionError("P2I-2P runs no FD-LAC rule and no filter")
    for name in ("evaluate", "fd_lac_01", "fd_lac_envelope", "fd_lac_04", "fd_lac_05", "fd_lac_06"):
        monkeypatch.setattr(fc, name, refuse)
    for name in ("evaluate_region", "region", "report"):
        monkeypatch.setattr(lactate_constraints, name, refuse)
    admissible = decision_pack.admissible()
    subset = [item for item in admissible if item.key() in set(survivors)][:2] + admissible[:3]
    monkeypatch.setattr(decision_pack, "admissible", lambda quick=False: subset)
    monkeypatch.setattr(op, "frozen_survivors", lambda: [item.key() for item in subset[:2]])
    result = op.revisit(reserves=(2.5,))
    assert set(result["collapse_interface"]) == {f"{scenario} {case}" for scenario in ("L1", "L2", "L3")
                                                 for case in lactate_slice.CASES}


def test_a_reserve_needs_the_gi_band_reading_stated():
    """Only reserve x arrival_delivery_ratio reaches D, so a GI run never applies a reserve to the
    band silently (P2I-2P)."""
    candidate = decision_pack.admissible()[0]
    with pytest.raises(ValueError):
        lactate_slice.slice_run(lactate_slice.CASES[0], candidate, "L1", profile_extra={"oxygen_extraction_reserve": 2.5})
    lactate_slice.slice_run(lactate_slice.CASES[0], candidate, "L1", profile_extra={"oxygen_extraction_reserve": 2.5},
                            case_extra={"arrival_delivery_ratio": 0.4})


def test_the_probe_document_is_generated_from_the_current_code():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    document = DOCUMENT.read_text(encoding="utf-8")
    assert data["probes_digest"] == op.probes_digest(), "the probes are stale: regenerate them"
    assert data["canonical_reserve"] == DEFAULT_PROFILE.oxygen_extraction_reserve == 1.0
    assert data["probes_digest"] in document
    assert op.apply(document, op.render(data)) == document, (
        "the document differs from the probes: run python -m clinical_core.oxygen_probes --write")
