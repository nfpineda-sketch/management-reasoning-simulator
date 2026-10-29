"""Phase 2 shadow core, P2I-2AD: the D -> lactate production gain is its own parameter.

Faculty decision (P2I-2AD): after P2I-2AC D has no steady state under a persistent deficit, so tau_D is only the
kinetics of debt repayment and must not set lactate production per unit of D. The core reads
``debt_to_lactate_gain`` (mmol/L per minute per unit of D); tau_D sets how D is repaid and tau_lactate how lactate
clears; the former steady-state gain ``lactate_per_output_deficit`` no longer reaches the core. Every probe here is
synthetic (declared pump drifts on the neutral arrival), never a case.
"""
import inspect
from dataclasses import replace

import pytest

from clinical_core import oxygen_probes as op
from clinical_core.bands import Drift
from clinical_core.derived import DEFAULT_PROFILE, PARAMETERS, PROVISIONAL, CoreProfile, lactate_after_minute
from clinical_core.integration import run
from clinical_core.state import CoreInvariantError

#: The neutral arrival, indebted and declared exactly at the critical delivery for reserve 1: with the pump falling
#: from minute 0 the deficit is critical at every minute's end, so D only accrues and never repays.
ARRIVAL = replace(op.NEUTRAL, arrival_oxygen_debt=20.0, arrival_lactate_excess=0.5,
                  declared={**dict(op.NEUTRAL.declared), "arrival_oxygen_debt": "synthetic_probe",
                            "arrival_lactate_excess": "synthetic_probe"})
FALLING = (Drift("pump", "P", 0, 90, -0.005),)


def _run(**changes):
    return run(ARRIVAL, FALLING, 90, replace(DEFAULT_PROFILE, **changes)).states


def test_the_core_reads_its_own_gain_and_neither_time_constant_scales_production():
    source = inspect.getsource(lactate_after_minute)
    assert "debt_to_lactate_gain" in source.split('"""')[-1]
    assert "debt_clearance_tau_min" not in source.split('"""')[-1]
    assert "lactate_per_output_deficit" not in source.split('"""')[-1]
    for state in _run(debt_to_lactate_gain=0.002, lactate_clearance_tau_min=90.0)[:-1]:
        profile = replace(DEFAULT_PROFILE, debt_to_lactate_gain=0.002, lactate_clearance_tau_min=90.0)
        excess = state.aux.lactate_excess_mmol_l
        assert lactate_after_minute(state, profile) == excess + 0.002 * state.D - excess / 90.0


def test_tau_d_changes_no_lactate_while_d_only_accrues():
    runs = [_run(debt_clearance_tau_min=tau) for tau in (30.0, 60.0, 120.0)]
    assert all(b.D >= a.D for a, b in zip(runs[0], runs[0][1:])) and runs[0][-1].D > runs[0][0].D, (
        "D only accrues in this probe (its first minute crosses from the tie: no repayment)")
    for other in runs[1:]:
        assert [s.D for s in other] == [s.D for s in runs[0]]
        assert [s.aux.lactate_excess_mmol_l for s in other] == [s.aux.lactate_excess_mmol_l for s in runs[0]]


def test_the_former_steady_state_gain_no_longer_reaches_the_core():
    base = _run()
    for value in (2.0, 6.0, 12.0):
        assert [s.aux.lactate_excess_mmol_l for s in _run(lactate_per_output_deficit=value)] == [
            s.aux.lactate_excess_mmol_l for s in base]
    doubled = _run(debt_to_lactate_gain=2 * DEFAULT_PROFILE.debt_to_lactate_gain)
    assert doubled[-1].aux.lactate_excess_mmol_l > base[-1].aux.lactate_excess_mmol_l


def test_the_gain_is_provisional_and_its_default_keeps_the_former_default_number():
    assert DEFAULT_PROFILE.debt_to_lactate_gain == 2.0 / 3600.0
    assert PARAMETERS["debt_to_lactate_gain"][0] == PROVISIONAL and "TBD" in PARAMETERS["debt_to_lactate_gain"][1]
    assert "does not read it" in PARAMETERS["lactate_per_output_deficit"][1]
    with pytest.raises(CoreInvariantError):
        CoreProfile(debt_to_lactate_gain=-1e-6)
