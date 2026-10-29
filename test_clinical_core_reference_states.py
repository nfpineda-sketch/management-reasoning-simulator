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

def test_p2e1_the_decomposition_reproduces_the_observed_arrival_and_is_inspectable():
    anchors = case(intrinsic_sinus_rate=90.0)
    arrival = arrival_state(anchors)
    assert arrival.R.rate_bpm == 90.0 and arrival.aux.sympathetic_drive > 0
    assert derive(arrival, anchors).pulse_rate_bpm == pytest.approx(124.0)
    split = heart_rate_decomposition(anchors)
    # P2I-2AE: the arrival drive splits further into the arrival debt's share (none declared here) and the rest.
    assert split == {"observed_arrival_hr": 124.0, "intrinsic_sinus_rate": 90.0, "arrival_sympathetic_bpm": 34.0,
                     "arrival_sympathetic_drive": pytest.approx(34.0 / 25.0), "arrival_debt_drive": 0.0,
                     "arrival_non_debt_drive": pytest.approx(34.0 / 25.0), "arrival_debt_bpm": 0.0,
                     "arrival_non_debt_bpm": pytest.approx(34.0), "source": "synthetic_probe"}


def test_p2e1_resolving_the_drive_takes_the_rate_below_arrival_but_never_below_intrinsic():
    """The arrival share is the response to an arrival deficit: correcting it lets the rate fall."""
    partly = case(intrinsic_sinus_rate=90.0)            # a large share: volume corrects part of it
    rates = _rates(run(partly, (Step("resuscitated", "V", 1, 800.0),), 60))
    assert rates[0] == pytest.approx(124.0)
    assert rates[-1] < 124.0 - 10, "the compensatory tachycardia resolves below the arrival rate"
    assert min(rates) >= 90.0, "never below the intrinsic rate"
    fully = case(intrinsic_sinus_rate=110.0)            # a small share: volume corrects all of it
    rates = _rates(run(fully, (Step("resuscitated", "V", 1, 800.0),), 60))
    assert min(rates) >= 110.0 and rates[-1] == pytest.approx(110.0, abs=1e-3), "down to intrinsic, no further"


def test_p2e1_unmapped_the_arrival_rate_stays_the_floor():
    plain = Anchors(**BASE)
    rates = _rates(run(plain, (Step("resuscitated", "V", 1, 800.0),), 60))
    assert min(rates) == 124.0
    assert heart_rate_decomposition(plain)["source"] == "default_unmapped"
    assert case_parameter_provenance(plain)["intrinsic_sinus_rate"]["value"] == 124.0


def test_p2e1_beta_blockade_attenuates_the_gain_not_the_intrinsic_rate():
    free, blocked = case(intrinsic_sinus_rate=90.0), case(intrinsic_sinus_rate=90.0, beta_blockade=0.5)
    assert derive(arrival_state(blocked), blocked).pulse_rate_bpm == pytest.approx(124.0)
    assert arrival_state(blocked).R.rate_bpm == arrival_state(free).R.rate_bpm == 90.0
    fall = (Step("bleed", "V", 1, -300.0),)
    rise_free = _rates(run(free, fall, 3))[-1] - 124.0
    rise_blocked = _rates(run(blocked, fall, 3))[-1] - 124.0
    assert 0 < rise_blocked == pytest.approx(0.5 * rise_free)
    assert min(_rates(run(blocked, (Step("fill", "V", 1, 800.0),), 60))) >= 90.0


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
    declared = case(intrinsic_sinus_rate=90.0)
    with pytest.raises(CoreInvariantError, match="arrival_state"):
        initial_state(declared)
    arrival = arrival_state(declared)
    assert run(declared, (), 2, initial=arrival).digest() == run(declared, (), 2).digest()
    stale = CoreState.from_dict({key: value for key, value in arrival.to_dict().items() if key != "aux"})
    with pytest.raises(CoreInvariantError, match="minute-0 initial state"):
        run(declared, (), 2, initial=stale)
    plain = Anchors(**BASE)
    assert initial_state(plain) == arrival_state(plain), "without references the two are the same arrival"
