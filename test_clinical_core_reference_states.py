"""Phase 2 shadow core, P2E: physiological reference states, oxygen demand, terminal collapse.

Structural tests only. The values below are synthetic probes, declared as such; none is a
calibrated or approved number, and the GI golden keeps its unmapped defaults.
"""
import json
import math
from dataclasses import dataclass, replace

import pytest

from clinical_core import (Anchors, Channel, ChannelDelta, Contribution, Contributor, CoreInvariantError, RhythmCode,
                           RhythmState,
                           SourceKind, run)
from clinical_core.derived import (DEFAULT_PROFILE, arrival_state, case_parameter_provenance, derive,
                                   heart_rate_decomposition)
from clinical_core.modules import GIHaemorrhage

BASE = dict(case_id="synthetic", sbp=88.0, dbp=54.0, hr=124.0, spo2=97.0, respiratory_rate=26.0, crt_s=5.0,
            lactate=4.4, hb=6.7, glucose=118.0, k=4.1, fio2=0.21, rhythm=RhythmState.sinus(124.0),
            consciousness_level=0)
BLEED = GIHaemorrhage("gi_haemorrhage", 2.5, 0.8, 0.1)


def case(**declared):
    """Anchors with case parameters declared as synthetic probes."""
    return Anchors(**{**BASE, **declared, "declared": {name: "synthetic_probe" for name in declared}})


@dataclass(frozen=True)
class Step(Contributor):
    """A one-off change of one channel at one minute (test only)."""

    kind = SourceKind.SCRIPTED_EVENT
    type_name = "test_reference_step"
    id: str
    channel: str
    at_minute: int
    amount: float

    def contribute(self, state, minute, signals, anchors, profile):
        if minute != self.at_minute:
            return Contribution()
        return Contribution(deltas=(ChannelDelta(Channel(self.channel), self.amount, self.source, minute,
                                                 f"synthetic step of {self.channel}"),))


def _rates(trajectory):
    return [d.pulse_rate_bpm for d in trajectory.derived()]


# P2E-1 -- the arrival HR is not the intrinsic HR -------------------------------------------------

#: P2I-2AF: the arrival drive comes from the arrival physiology. A synthetic shocked arrival (deficit 0.15 of demand)
#: read with a synthetic acute-deficit gain; neither value is a mapping or a calibration.
SHOCK = {"arrival_delivery_ratio": 0.85}
ACUTE = replace(DEFAULT_PROFILE, acute_deficit_to_sympathetic_gain=8.0)


def test_p2e1_the_decomposition_predicts_the_arrival_and_reports_its_mismatch():
    """P2I-2AF: the arrival HR is predicted from the arrival physiology (intrinsic + saturated acute and debt
    increments); its mismatch with the authored HR is reported, never absorbed by a residual."""
    anchors = case(intrinsic_sinus_rate=90.0, **SHOCK)
    arrival = arrival_state(anchors, ACUTE)
    assert arrival.R.rate_bpm == 90.0 and arrival.aux.sympathetic_drive == pytest.approx(8.0 * 0.15)
    split = heart_rate_decomposition(anchors, ACUTE)
    assert split["predicted_arrival_hr"] == derive(arrival, anchors, ACUTE).pulse_rate_bpm
    assert split["mismatch_bpm"] == split["predicted_arrival_hr"] - 124.0 != 0.0
    assert split["acute_unconstrained_bpm"] == pytest.approx(25.0 * 8.0 * 0.15) and split["debt_unconstrained_bpm"] == 0
    assert split["saturated_bpm"] < split["unconstrained_bpm"] and split["acute_bpm"] + split["debt_bpm"] == (
        pytest.approx(split["saturated_bpm"]))
    assert split["source"] == "synthetic_probe" and split["arrival_sympathetic_bpm"] == 34.0
    # Without a declared shock, the predicted arrival HR is the intrinsic rate: nothing is solved from 124.
    assert heart_rate_decomposition(case(intrinsic_sinus_rate=90.0))["predicted_arrival_hr"] == 90.0


def test_p2e1_resolving_the_shock_takes_the_rate_down_to_intrinsic_and_never_below():
    """The arrival share is the response to the arrival deficit: correcting it lets the rate fall to intrinsic."""
    shocked = case(intrinsic_sinus_rate=90.0, **SHOCK)
    rates = _rates(run(shocked, (Step("resuscitated", "V", 1, 800.0),), 60, ACUTE))
    assert rates[0] == heart_rate_decomposition(shocked, ACUTE)["predicted_arrival_hr"] > 110.0
    assert rates[-1] == pytest.approx(90.0, abs=1e-3), "the acute deficit resolves, and the drive with it"
    assert min(rates) >= 90.0, "never below the intrinsic rate"


def test_p2e1_beta_blockade_attenuates_the_gain_not_the_intrinsic_rate():
    free, blocked = case(intrinsic_sinus_rate=90.0, **SHOCK), case(intrinsic_sinus_rate=90.0, beta_blockade=0.5,
                                                                      **SHOCK)
    assert arrival_state(blocked, ACUTE).R.rate_bpm == arrival_state(free, ACUTE).R.rate_bpm == 90.0
    assert arrival_state(blocked, ACUTE).aux == arrival_state(free, ACUTE).aux, "the same drive"
    fall = (Step("bleed", "V", 1, -300.0),)
    rise_free = _rates(run(free, fall, 3, ACUTE))[-1] - 90.0
    rise_blocked = _rates(run(blocked, fall, 3, ACUTE))[-1] - 90.0
    assert 0 < rise_blocked < rise_free
    assert min(_rates(run(blocked, (Step("fill", "V", 1, 800.0),), 60, ACUTE))) >= 90.0


def test_p2e1_unmapped_the_arrival_rate_stays_the_floor():
    plain = Anchors(**BASE)
    rates = _rates(run(plain, (Step("resuscitated", "V", 1, 800.0),), 60))
    assert min(rates) == 124.0
    assert heart_rate_decomposition(plain)["source"] == "default_unmapped"
    assert case_parameter_provenance(plain)["intrinsic_sinus_rate"]["value"] == 124.0


def test_p2e1_a_rate_below_intrinsic_still_needs_an_explicit_source():
    from clinical_core.modules import ScriptedRhythmEvent
    anchors = case(intrinsic_sinus_rate=90.0)
    slowed = ScriptedRhythmEvent("negative_chronotrope", 30, RhythmState.sinus(60.0), "declared drug effect")
    trajectory = run(anchors, (Step("fill", "V", 1, 800.0), slowed), 60)
    rates, last = _rates(trajectory), trajectory.states[-1]
    assert min(rates[:30]) >= 90.0, "the drive alone never takes the rate below intrinsic"
    assert last.R.rate_bpm == 60.0, "the explicit source changed R"
    assert rates[-1] == pytest.approx(60.0 + DEFAULT_PROFILE.hr_per_sympathetic_drive * last.aux.sympathetic_drive)
    assert rates[-1] < 90.0


@pytest.mark.parametrize("bad", [dict(intrinsic_sinus_rate=130.0), dict(intrinsic_sinus_rate=0.0),
                                 dict(intrinsic_sinus_rate=90.0, beta_blockade=1.0)])
def test_p2e1_impossible_decompositions_are_refused(bad):
    with pytest.raises(CoreInvariantError):
        case(**bad)


def test_p2e1_a_non_sinus_arrival_cannot_declare_an_intrinsic_sinus_rate():
    with pytest.raises(CoreInvariantError):
        Anchors(**{**BASE, "rhythm": RhythmState(RhythmCode.PACED, 124.0, 1.0, True), "intrinsic_sinus_rate": 90.0,
                   "declared": {"intrinsic_sinus_rate": "synthetic_probe"}})


def test_p2e1_the_gi_golden_keeps_the_unmapped_decomposition():
    from clinical_core.shadow import GOLDEN
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    for entry in golden["scenarios"].values():
        assert entry["case_parameters"]["intrinsic_sinus_rate"]["source"] == "default_unmapped"


# After the adversarial review of P2E ------------------------------------------------------------

def test_review_f1_a_case_with_reference_states_cannot_start_from_the_anchored_defaults():
    """initial_state and a minute-0 initial= would skip the declared intrinsic rate (and P2E-2 references)."""
    from clinical_core import initial_state
    from clinical_core.derived import arrival_state
    from clinical_core.state import CoreState, CoreInvariantError
    # P2I-2AF: an arrival debt gives the declared arrival a drive of its own, which the stale state lacks.
    declared = case(intrinsic_sinus_rate=90.0, arrival_oxygen_debt=10.0)
    with pytest.raises(CoreInvariantError, match="arrival_state"):
        initial_state(declared)
    arrival = arrival_state(declared)
    assert run(declared, (), 2, initial=arrival).digest() == run(declared, (), 2).digest()
    stale = CoreState.from_dict({key: value for key, value in arrival.to_dict().items() if key != "aux"})
    with pytest.raises(CoreInvariantError, match="minute-0 initial state"):
        run(declared, (), 2, initial=stale)
    plain = Anchors(**BASE)
    assert initial_state(plain) == arrival_state(plain), "without references the two are the same arrival"
