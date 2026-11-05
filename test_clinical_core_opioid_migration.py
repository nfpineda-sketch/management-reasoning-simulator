"""P2U-1: the opioid shadow migration (central respiratory depression through the common architecture, shadow only).

These tests hold the minimum availability interface (one auxiliary field, one arrival anchor, one provenance record and
its guards), the family writers (depression and naloxone) writing nothing else, the arrival region and its exactness,
U1-U12, the primary / secondary contrast, the recurrence direction, the HR and consciousness status, the common FiO2 and
acid-base paths, the non-regression and the proof that every other file is P2T-5's.
"""
from __future__ import annotations

import json
import math
from dataclasses import replace

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import opioid_migration as un
from clinical_core import opioid_reference as orf
from clinical_core import oxygenation_link as om
from clinical_core.integration import _REGISTRY, availability_sum, step
from clinical_core.modules.opioid import NaloxoneReversal, OpioidCentralDepression
from clinical_core.provenance import AvailabilityChange, ProvenanceError, Source, SourceKind
from clinical_core.state import AuxiliaryState, CoreInvariantError

#: The P2U-1 freeze: the interface, the writers, the arrival mapping, the probes, the readiness rule, the proof and every
#: clinical_core source but the downstream reports, committed before the evaluation run.
FROZEN_DIGEST = "6638a22d34afcdef746f9718291b346b07d51e91d1e848dd82952f034178d2e5"
PROBE_SOURCE = Source(SourceKind.DISEASE_MODULE, "p2u1-test")


# The frozen package and its proof -------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert all(relative in sources for relative in un.OWN + un.FAMILY_FILES) and un.REPORT not in sources
    assert set(un.TUPLES_ADDED["DOWNSTREAM_REPORTS"]) <= set(lactate_slice.DOWNSTREAM_REPORTS)
    assert set(un.TUPLES_ADDED["PACK_DIGEST_EXCLUDED"]) <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    if FROZEN_DIGEST is not None:
        assert un.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_only_the_declared_files_changed():
    assert set(un.REVERSAL) == set(un.CORE_AT_P2T5) == {"clinical_core/derived.py", "clinical_core/integration.py",
                                                        "clinical_core/state.py", "clinical_core/provenance.py",
                                                        "clinical_core/lactate_slice.py",
                                                        "clinical_core/decision_pack.py"}
    assert all(un.proofs().values())
    common = un.common_untouched()
    assert all(common.values()) and len(common) >= 123
    assert {"clinical_core/oxygenation_link.py", "clinical_core/asthma_distress_migration.py",
            "clinical_core/modules/asthma.py", "clinical_core/collapse.py"} <= set(common)
    proof = un.upstream_unchanged()
    assert proof["p2t5_freeze_digest"] and proof["p2t5_proof"] and proof["p2t5_record"]


@pytest.mark.parametrize("relative, old, new", [
    ("clinical_core/derived.py", "return profile.central_drive_availability * central",
     "return profile.central_drive_availability * central * 1.0"),
    ("clinical_core/integration.py", "value = availability_sum(state.aux.central_availability",
     "value = 1.0 * availability_sum(state.aux.central_availability"),
    ("clinical_core/state.py", "arrival_central_availability: float = 1.0",
     "arrival_central_availability: float = 0.999"),
    ("clinical_core/lactate_slice.py", '"clinical_core/opioid_migration_report.py")',
     '"clinical_core/opioid_migration_report.py", "clinical_core/other.py")'),
])
def test_the_proof_notices_any_other_change(relative, old, new):
    live = un._live(relative)
    assert live.count(old) == 1 and not un.proved(relative, live.replace(old, new))


def test_the_p2t5_view_reads_the_p2t5_tree():
    with un.p2t5_view():
        assert "central_availability" not in om._live("clinical_core/derived.py")
        assert "opioid" not in om._live("clinical_core/lactate_slice.py")
        assert un.NEW_AUX not in {f.name for f in un._fields_at_p2t5(AuxiliaryState)}
        assert not (set(un.OWN) | set(un.FAMILY_FILES)) & set(bf.freeze_sources())
    assert "central_availability" in om._live("clinical_core/derived.py")


# The interface -------------------------------------------------------------------------------------------------------------

def test_the_availability_is_1_by_default_everywhere():
    assert AuxiliaryState().central_availability == 1.0
    a = om.probe_anchors()
    assert a.arrival_central_availability == 1.0
    assert dv.arrival_state(a, dv.DEFAULT_PROFILE).aux.central_availability == 1.0
    assert dv.central_availability(dv.DEFAULT_PROFILE, 1.0) == 1.0
    for anchors, prof in om.committed_pairs().values():
        assert anchors.arrival_central_availability == 1.0


@pytest.mark.parametrize("value", [-0.1, 1.1, math.nan, math.inf])
def test_the_domain_is_0_to_1(value):
    with pytest.raises(CoreInvariantError):
        AuxiliaryState(central_availability=value)
    with pytest.raises(CoreInvariantError):
        om.probe_anchors(arrival_central_availability=value)


def test_an_arrival_availability_needs_the_acid_base_physiology():
    a = om.probe_anchors(arrival_central_availability=0.5)
    with pytest.raises(CoreInvariantError, match="P2U-1"):
        dv.arrival_state(a, replace(dv.DEFAULT_PROFILE, acid_to_drive_gain=None))
    assert dv.arrival_state(a, un.profile()).aux.central_availability == 0.5


def test_a_change_needs_the_acid_base_physiology_and_stays_in_its_domain():
    a, p = orf.anchors(), un.profile()
    s = dv.arrival_state(a, p)
    off_anchors = om.probe_anchors()
    off = replace(dv.DEFAULT_PROFILE, acid_to_drive_gain=None)
    with pytest.raises(ProvenanceError, match="P2U-1"):
        step(dv.arrival_state(off_anchors, off), (_Raw(-0.1),), off_anchors, off)
    with pytest.raises(ProvenanceError, match="outside 0"):
        step(s, (_Raw(-1.0),), a, p)
    with pytest.raises(ProvenanceError, match="outside 0"):
        step(s, (_Raw(1.0),), a, p)


@pytest.mark.parametrize("amount", [math.nan, math.inf, True])
def test_a_change_record_is_finite(amount):
    with pytest.raises(ProvenanceError):
        AvailabilityChange(amount, PROBE_SOURCE, 1, "x")


def test_the_sum_snaps_only_within_roundoff():
    assert availability_sum(0.3, [-0.1, -0.2]) == 0.0
    assert availability_sum(0.5, [0.5]) == 1.0
    assert availability_sum(1.0, [math.ulp(1.0) / 4]) == 1.0
    assert availability_sum(0.0, [-0.001]) == -0.001
    assert availability_sum(1.0, [0.001]) == 1.001
    assert availability_sum(0.4, [0.1, 0.2]) == availability_sum(0.4, [0.2, 0.1])


class _Raw(OpioidCentralDepression):
    """A probe writer that asks for a flat amount, to exercise the domain guard."""

    def __init__(self, amount):
        object.__setattr__(self, "id", "p2u1-raw")
        object.__setattr__(self, "deepening_per_min", 0.5)
        object.__setattr__(self, "start_minute", 0)
        object.__setattr__(self, "stop_minute", None)
        object.__setattr__(self, "amount", amount)

    def contribute(self, state, minute, signals, anchors, profile):
        from clinical_core.integration import Contribution
        return Contribution(availability=(AvailabilityChange(self.amount, self.source, minute, "probe"),))


# The family writers ---------------------------------------------------------------------------------------------------------

def test_the_writers_are_registered_and_validated():
    assert _REGISTRY[OpioidCentralDepression.type_name] is OpioidCentralDepression
    assert _REGISTRY[NaloxoneReversal.type_name] is NaloxoneReversal
    for bad in (-0.1, 1.0, 1.5, math.nan, True):
        with pytest.raises(CoreInvariantError):
            OpioidCentralDepression("x", bad)
        with pytest.raises(CoreInvariantError):
            NaloxoneReversal("x", bad)
    with pytest.raises(CoreInvariantError):
        OpioidCentralDepression("x", 0.1, -1)
    with pytest.raises(CoreInvariantError):
        NaloxoneReversal("x", 0.1, 10, 10)


def test_the_writers_write_only_the_availability():
    found = un.writer_audit()
    assert found["pass"] and found["contribution_keywords"] == ["availability"] and not found["forbidden_names"]


def test_naloxone_never_takes_the_availability_above_1():
    a, p = orf.anchors(), un.link_profile()
    states, _ = un.course((un.naloxone(0.9, 0),), a, p, minutes=30)
    values = [s.aux.central_availability for s in states]
    assert max(values) <= 1.0 and values[-1] > values[0] and all(b >= x for x, b in zip(values, values[1:]))


# The arrival mapping and the probes -----------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def region():
    return un.arrival_region()


def test_the_case_truth_is_the_bank(region):
    found = un.case_truth()
    assert found["pass"]
    for case in orf.CASES:
        authored = found[case]["authored"]
        assert region[case]["authored"]["rr"] == float(authored["respiratory_rate"])
        assert region[case]["authored"]["paco2"] == float(authored["abg_paco2"])
        assert found[case]["later_observations"].startswith("none")


def test_the_arrival_is_exact_at_every_carried_intrinsic_rr(region):
    assert region["pass"]
    for case in orf.CASES:
        assert region[case]["exact"]
        for point in un.POINTS:
            row = region[case]["points"][point]
            assert 0.0 < row["availability"] < 1.0 and row["efficiency"] > 0.0
            assert row["spo2"] == row["spo2_link_on"]        # the link is exact at arrival (P2T-5's O2)


def test_the_steady_state_tension_is_reported_not_resolved(region):
    assert region["tension"]["label"] == "STEADY_STATE_W_ARRIVAL_TENSION"
    assert region[orf.CASE]["points"]["midpoint"]["efficiency_above_reference"]
    assert region[orf.CASE]["points"]["midpoint"]["restored_paco2"] < 40.0


def test_the_channel_map_is_neutral_outside_the_availability():
    found = un.channel_map()
    assert found["pass"]
    for case in orf.CASES:
        row = found["arrival_channels"][case]
        assert row["G"] == 0.0 and row["L"] == 0.0 and row["distress"] == 0.0 and row["D"] == 0.0


@pytest.fixture(scope="module")
def probes():
    return un.probes()


@pytest.mark.parametrize("name", ["U1", "U2", "U3", "U4", "U5", "U6", "U7", "U8", "U9"])
@pytest.mark.parametrize("case", orf.CASES)
def test_the_cascade_probes(probes, case, name):
    assert probes[case]["U"][name], (case, name, probes[case]["untreated"], probes[case]["naloxone"])


def test_no_disease_specific_oxygen_equation_or_scripting(probes):
    assert probes["U10"]["pass"] and probes["U11"]["pass"]


def test_review_hardening_the_cascade_is_serial_not_parallel():
    """On every state of the opioid course, the SpO2 is exactly the arrival SpO2 shifted by that state's PaCO2 change
    (P2T-5's link on an unchanged base SpO2: no G, no second oxygenation path). With the link off the same course moves no
    SpO2 at all. The two courses' PaCO2 then diverge slightly after the first minutes, through P2T-5's documented
    minute-lagged delivery -> deficit -> acid -> drive route (M1), which is compensatory: the link-on PaCO2 is the lower."""
    a = orf.anchors()
    on, off = un.link_profile(), un.profile()
    with_link, _ = un.course((un.depression(),), a, on)
    without, _ = un.course((un.depression(),), a, off)
    assert [om.spo2(s, a, off) for s in without] == [a.spo2] * len(without)
    assert om.spo2(with_link[-1], a, on) < a.spo2
    for s in with_link:
        assert om.spo2(s, a, on) == om.shift(a.spo2, dv.respiration(s, a, on).paco2
                                             - dv.arrival_paco2_reference(a, on))
    assert with_link[-1].aux.central_availability == without[-1].aux.central_availability
    assert 0.0 < with_link[-1].aux.metabolic_acid_burden and without[-1].aux.metabolic_acid_burden == 0.0
    assert dv.respiration(with_link[-1], a, on).paco2 < dv.respiration(without[-1], a, off).paco2


def test_the_contrast_orders_the_two_cases():
    found = un.contrast()
    assert found["pass"] and found["ordering"]


def test_the_recurrence_direction():
    found = un.recurrence()
    assert found["pass"], found


def test_the_collapse_direction_is_structural_only():
    found = un.collapse_direction()
    assert found["pass"] and found["no_opioid_collapse_rule"]


def test_the_heart_rate_residual_is_carried_not_patched(region):
    found = un.heart_rate(region)
    assert found["pass"] and found["opioid_hr_term"] is False
    assert found[orf.CASE]["within"]                                  # 35m inside the common band
    assert not found[orf.SECONDARY]["within"] and "OPIOID_HR_FAMILY_GAP" in found["gap"]
    assert abs(found[orf.SECONDARY]["residual_bpm"]) < 5.0            # reported, never closed with a term


def test_consciousness_stays_diagnostic():
    found = un.consciousness()
    assert found["pass"] and found["N_written"] is False
    for case in orf.CASES:
        assert "CONSCIOUSNESS_INTEGRATION_DEBT" in found[case]["reading"]


def test_the_oxygen_and_acid_base_paths_are_common():
    assert un.oxygen()["pass"] and un.acid_base()["pass"]
    assert un.oxygen()["debt"] == "FIO2_RESPONSE_MAGNITUDE_DEBT"


def test_the_interface_audit():
    found = un.interface_audit()
    assert found["pass"] and found["aux_fields_new"] == [un.NEW_AUX]
    assert found["anchor_fields_new"] == [un.NEW_ANCHOR] and not found["profile_fields_new"]


def test_the_legacy_is_classified_not_fitted():
    found = un.legacy()
    assert found["pass"] and found["fitted"] is False
    assert found["classification"] == "LEGACY_ENGINE_BEHAVIOR"


def test_the_non_regression():
    found = un.non_regression()
    assert found["pass"], found


# The verdict, the frozen record and the document -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def found():
    return un.run()


def test_the_readiness(found):
    assert found["readiness"]["verdict"] == un.READY and found["readiness"]["blocker"] is None


@pytest.mark.parametrize("path, index", [
    (("arrival_region", "pass"), 0), (("recurrence", "pass"), 4), (("interface", "pass"), 5),
    (("non_regression", "pass"), 6),
])
def test_the_first_failing_criterion_blocks(found, path, index):
    broken = json.loads(json.dumps(found))
    broken[path[0]][path[1]] = False
    verdict = un.readiness(broken)
    assert verdict["blocker"] == un.READINESS_CRITERIA[index] and verdict["verdict"].startswith(un.NOT_READY)


@pytest.fixture(scope="module")
def record():
    if not un.RECORD.exists():
        pytest.skip("the P2U-1 record is written by the evaluation run, after the freeze")
    return json.loads(un.RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, found):
    assert record["freeze_digest"] == FROZEN_DIGEST
    assert record == json.loads(json.dumps(found, sort_keys=True, default=str))


def test_the_document_is_generated_from_the_record(record):
    from clinical_core import opioid_migration_report as report
    text = un.DOCUMENT.read_text(encoding="utf-8")
    for name, render in report.RENDERERS.items():
        opening, closing = report.MARKERS[name]
        assert text.count(opening) == 1 and text.count(closing) == 1
        assert text.split(opening)[1].split(closing)[0].strip("\n") == render(record).strip("\n")
