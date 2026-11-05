"""P2S-2: common respiratory mechanics and W's one meaning (shadow only).

The core gained the mechanics efficiency (state, latent arrival value, family writer target) behind a switch that is off
by default; W = (RR / intrinsic RR) x mechanics efficiency / demand ratio and PaCO2 = the common reference / W in the
candidate. These tests hold the semantics, the refusals, probes M1-M12, the contrasts, the arrival-efficiency ordering,
the default non-regression and the proof that every other common file is P2Q-2's.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import replace

import pytest

from clinical_core import bands
from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import embolism_migration as em
from clinical_core import respiratory_mechanics as mc
from clinical_core import asthma_migration as sm
from clinical_core import respiratory_distress as dm
from clinical_core.integration import Contribution, _check_conservation, step
from clinical_core.provenance import MechanicsChange, MinuteRecord, ProvenanceError, Source, SourceKind
from clinical_core.state import AUXILIARY_FIELDS, Anchors, AuxiliaryState, CoreInvariantError

#: The P2S-2 freeze: the core insertions (by the proof), the path audit, the semantics, the synthetic values, probes
#: M1-M12, the contrasts, the arrival ordering rule, the readiness rule and every clinical_core source but the
#: downstream reports, committed before the evaluation run.
FROZEN_DIGEST = "ba6e9997495dd2009526841189e622fc6c6b9b92f0c987535cfff2e8a8462e64"

#: P2S-3 added files (the asthma family, its mapping and analysis) and two tuple entries, proven against the P2S-2 files
#: (asthma_migration.proved): this package's guards read the tree as P2S-2 left it (sm.chain, sm.p2s2_sources); its
#: record is unchanged.
#: P2T-1 changed four common files (the respiratory distress input and its two UNSET readers), proven against
#: the P2S-3 files (respiratory_distress.proved): this package's guards read the tree as P2S-3 left it
#: (dm.chain, dm.p2s3_sources).
_LIVE_SOURCES_P2T1 = bf.freeze_sources


def _LIVE_SOURCES_P2S3() -> dict:
    return dm.p2s3_sources(_LIVE_SOURCES_P2T1())


@pytest.fixture(autouse=True, scope="module")
def _p2s2_tree():
    with pytest.MonkeyPatch.context() as patch:
        sm.chain(patch)
        dm.chain(patch)
        patch.setattr(bf, "freeze_sources", lambda: sm.p2s2_sources(_LIVE_SOURCES_P2S3()))
        yield


# The frozen package and its proof -------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert mc.OWN[0] in sources and mc.REPORT not in sources
    assert set(mc.TUPLES_ADDED["DOWNSTREAM_REPORTS"]) <= set(lactate_slice.DOWNSTREAM_REPORTS)
    assert set(mc.TUPLES_ADDED["PACK_DIGEST_EXCLUDED"]) <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    if FROZEN_DIGEST is not None:
        assert mc.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_the_core_is_p2q2_plus_the_declared_insertions():
    assert set(mc.REVERSAL) == set(mc.CORE_AT_P2Q2) == set(mc.CORE_FILES) | {"clinical_core/lactate_slice.py",
                                                                            "clinical_core/decision_pack.py"}
    assert all(mc.proofs().values())
    for relative, sha in mc.CORE_AT_P2Q2.items():
        assert hashlib.sha256(mc.p2q2_bytes(relative)).hexdigest() == sha
    common = mc.common_untouched()
    assert all(common.values()) and len(common) >= 100
    assert {"clinical_core/ventilation.py", "clinical_core/respiratory_drive.py", "clinical_core/embolism_migration.py",
            "clinical_core/collapse.py"} <= set(common)
    proof = mc.upstream_unchanged()
    assert proof["p2q2_freeze_digest"] and proof["p2q2_proof"] and proof["p2q2_record"]
    assert all(proof["p2q2_common_untouched"].values())


@pytest.mark.parametrize("relative, old, new", [
    ("clinical_core/derived.py", "resting = profile.paco2_reference_mmhg", "resting = arrival_paco2(anchors, profile)"),
    ("clinical_core/integration.py", "mechanics.extend(contribution.mechanics)", "pass"),
    ("clinical_core/integration.py", "any(delta.channel is Channel.W for delta in deltas)", "False"),
    ("clinical_core/state.py", "\n    mechanics_efficiency: float = 1.0\n", "\n    mechanics_efficiency: float = 0.9\n"),
])
def test_the_proof_notices_any_other_change(relative, old, new):
    live = mc._live(relative)
    assert live.count(old) == 1 and not mc.proved(relative, live.replace(old, new))


def test_closed_packages_read_the_p2q2_tree():
    with pytest.MonkeyPatch.context() as patch:
        mc.chain(patch)
        assert "respiratory_mechanics" not in em._live("clinical_core/derived.py")
        assert "mechanics_efficiency" not in em._live("clinical_core/state.py")
        assert all(em.proofs().values()) and all(em.common_untouched().values())
    assert "respiratory_mechanics" in em._live("clinical_core/derived.py")


def test_the_p2q2_sources_leave_out_the_p2s2_files():
    sources = mc.p2q2_sources(bf.freeze_sources())
    assert not set(mc.OWN) & set(sources)
    for relative, sha in mc.CORE_AT_P2Q2.items():
        assert sources[relative] == sha


# The core: switch, state, arrival, interface ------------------------------------------------------------------------------------

def test_the_switch_is_off_by_default_and_registered_provisional():
    assert dv.DEFAULT_PROFILE.respiratory_mechanics is False and not dv.respiratory_mechanics_active(dv.DEFAULT_PROFILE)
    status, note = dv.PARAMETERS["respiratory_mechanics"]
    assert status == dv.PROVISIONAL and "STRUCTURAL_SWITCH" in note and "not approved" in note
    assert dv.DEFAULT_PROFILE.paco2_reference_mmhg == 40.0
    assert AuxiliaryState().mechanics_efficiency == 1.0 and "mechanics_efficiency" in AUXILIARY_FIELDS
    assert dv.RESPIRATORY_MECHANICS == Source(SourceKind.CORE_COUPLING, "respiratory_mechanics")
    assert dv.AUXILIARY_SOURCES["mechanics_efficiency"] is dv.RESPIRATORY_MECHANICS


@pytest.mark.parametrize("build", [
    lambda: replace(dv.DEFAULT_PROFILE, respiratory_mechanics=True),
    lambda: mc.base_profile(ventilation_efficiency=0.5),
    lambda: replace(mc.rd.base_profile(), respiratory_mechanics=1),
])
def test_the_candidate_needs_acid_base_and_the_reference_efficiency(build):
    with pytest.raises(CoreInvariantError):
        build()


@pytest.mark.parametrize("value", [0.0, -0.1, float("inf"), float("nan")])
def test_the_mechanics_domain_is_above_zero(value):
    with pytest.raises(CoreInvariantError):
        AuxiliaryState(mechanics_efficiency=value)
    with pytest.raises(CoreInvariantError):
        mc.probe_anchors(arrival_mechanics_efficiency=value)


def test_no_upper_bound_and_the_arrival_is_the_latent_value():
    prof = mc.base_profile()
    state = dv.arrival_state(mc.probe_anchors(arrival_mechanics_efficiency=1.7), prof)
    assert state.aux.mechanics_efficiency == 1.7
    assert dv.respiration(state, mc.PROBE_ANCHORS, prof).ventilation == pytest.approx(1.7)


def test_off_the_mechanics_inputs_are_refused():
    off = mc.rd.base_profile()
    with pytest.raises(CoreInvariantError):
        dv.arrival_state(mc.probe_anchors(arrival_mechanics_efficiency=0.5), off)
    state = dv.arrival_state(mc.PROBE_ANCHORS, off)
    with pytest.raises(CoreInvariantError):
        dv.respiration(state.evolve(aux=replace(state.aux, mechanics_efficiency=0.5)), mc.PROBE_ANCHORS, off)
    with pytest.raises(ProvenanceError):
        step(state, (mc.SyntheticMechanics("x", 0.9),), mc.PROBE_ANCHORS, off)


def test_on_the_w_channel_is_not_writable_and_reads_nothing():
    prof = mc.base_profile()
    state = dv.arrival_state(mc.PROBE_ANCHORS, prof)
    with pytest.raises(ProvenanceError):
        step(state, (bands.Drift("w", "W", 0, 1, -0.3),), mc.PROBE_ANCHORS, prof)
    carrying = state.evolve(W=0.3)
    assert dv.respiration(carrying, mc.PROBE_ANCHORS, prof) == dv.respiration(state, mc.PROBE_ANCHORS, prof)
    assert dv.derive(carrying, mc.PROBE_ANCHORS, prof) == dv.derive(state, mc.PROBE_ANCHORS, prof)
    # Off, the historical P2K-1 reader still answers to W with the acid-base physiology off.
    plain = dv.arrival_state(mc.PROBE_ANCHORS)
    assert dv.derive(plain.evolve(W=0.5), mc.PROBE_ANCHORS).respiratory_rate > dv.derive(plain, mc.PROBE_ANCHORS).respiratory_rate


def test_the_candidate_w_and_paco2_are_the_faculty_form():
    prof = mc.driven(mc.base_profile(central_drive_availability=0.75))
    anchors = mc.probe_anchors(arrival_mechanics_efficiency=0.6, arrival_bicarbonate=18.0)
    state = dv.arrival_state(anchors, prof)
    state = state.evolve(aux=replace(state.aux, oxygen_demand=1.3))
    r = dv.respiration(state, anchors, prof)
    frequency = r.respiratory_rate / r.intrinsic_rr
    assert r.efficiency == 0.6 and r.ventilation == pytest.approx(frequency * 0.6 / 1.3, rel=1e-12)
    assert r.resting_paco2 == 40.0 and r.paco2 == pytest.approx(40.0 / r.ventilation, rel=1e-12)
    assert r.ph == dv.carbonic_ph(r.bicarbonate, r.paco2)


def test_without_a_pulse_there_is_no_ventilation():
    prof = mc.base_profile()
    state = dv.arrival_state(mc.PROBE_ANCHORS, prof)
    from clinical_core.state import RhythmState
    arrest = state.evolve(R=RhythmState.asystole(), terminal_since=state.minute)
    r = dv.respiration(arrest, mc.PROBE_ANCHORS, prof)
    assert r.respiratory_rate == 0.0 and r.ventilation == 0.0 and r.paco2 is None and r.ph is None


@pytest.mark.parametrize("factor", [0.0, -1.0, float("inf"), float("nan"), True, "0.9"])
def test_a_mechanics_change_is_a_finite_positive_factor(factor):
    with pytest.raises(ProvenanceError):
        MechanicsChange(factor, Source(SourceKind.SCRIPTED_EVENT, "x"), 1, "x")


def test_the_family_writer_target_composes_persists_and_is_recorded():
    prof = mc.base_profile()
    state = dv.arrival_state(mc.PROBE_ANCHORS, prof)
    writers = (mc.SyntheticMechanics("a", 0.9), mc.SyntheticMechanics("b", 1.25))
    after, record = step(state, writers, mc.PROBE_ANCHORS, prof)
    assert after.aux.mechanics_efficiency == pytest.approx(0.9 * 1.25)
    assert [c.source.key for c in record.mechanics] == ["scripted_event:a", "scripted_event:b"]
    change = [c for c in record.auxiliary if c.quantity == "mechanics_efficiency"]
    assert len(change) == 1 and change[0].source == dv.RESPIRATORY_MECHANICS
    assert record.to_dict()["mechanics"][0]["type"] == "mechanics"
    later, quiet = step(after, (), mc.PROBE_ANCHORS, prof)
    assert later.aux.mechanics_efficiency == after.aux.mechanics_efficiency and not quiet.mechanics
    assert MinuteRecord(minute=1).to_dict()["mechanics"] == []


def test_the_conservation_check_holds_mechanics_to_its_records():
    prof = mc.base_profile()
    state = dv.arrival_state(mc.PROBE_ANCHORS, prof)
    after, record = step(state, (mc.SyntheticMechanics("a", 0.9),), mc.PROBE_ANCHORS, prof)
    forged = replace(record, mechanics=())
    with pytest.raises(ProvenanceError):
        _check_conservation(state, after, forged)


def test_a_contribution_writes_mechanics_only_as_its_own_records():
    from clinical_core.integration import _check_owned
    writer = mc.SyntheticMechanics("a", 0.9)
    other = Source(SourceKind.SCRIPTED_EVENT, "b")
    with pytest.raises(ProvenanceError):
        _check_owned(writer, Contribution(mechanics=[MechanicsChange(0.9, writer.source, 1, "x")]), 1)
    with pytest.raises(ProvenanceError):
        _check_owned(writer, Contribution(mechanics=(MechanicsChange(0.9, other, 1, "x"),)), 1)
    with pytest.raises(ProvenanceError):
        _check_owned(writer, Contribution(mechanics=(MechanicsChange(0.9, writer.source, 2, "x"),)), 1)


# The analysis: audit, probes, contrasts, regions -----------------------------------------------------------------------------

def test_the_path_audit_reads_the_live_core():
    audit = mc.audit()
    assert audit["pass"], audit
    assert set(mc.PATHS) >= {"respiratory_drive", "expressed_rr", "intrinsic_rr", "central_drive_availability",
                             "ventilation_efficiency", "W_channel_P2K1_reader", "W_P2K2", "PaCO2_P2K2",
                             "metabolic_demand", "acid_drive", "P2K2_path", "P2K3_candidate", "P2P2_path"}
    assert mc.RETIRED_FROM_CANDIDATE in mc.PATHS["W_channel_P2K1_reader"][1]


@pytest.fixture(scope="module")
def probes():
    return mc.structural_probes()


@pytest.mark.parametrize("name", [f"M{i}" for i in range(1, 13)])
def test_probe(probes, name):
    assert probes["pass"][name], probes["probes"][name]


def test_m1_is_the_reference_state(probes):
    m1 = probes["probes"]["M1"]
    assert (m1["rr"], m1["W"], m1["paco2"], m1["mechanics_efficiency"]) == (16.0, 1.0, 40.0, 1.0)


def test_the_required_directions():
    found = mc.directions()
    assert found["pass"], found
    assert found["demand"]["W"] == pytest.approx([1.0, 1 / 1.2, 1 / 1.5])


def test_the_interface():
    found = mc.interface()
    assert found["pass"], found
    assert not found["family_writers"]


def test_high_rr_high_paco2_is_representable():
    found = mc.high_rr_high_paco2()
    assert found["pass"] and found["class"] == "HIGH_RR_HIGH_PACO2_STRUCTURALLY_REPRESENTABLE"
    for row in found["core"].values():
        assert row["availability"] == 1.0 and row["paco2"] > 40.0


def test_the_compensated_and_opioid_contrasts():
    assert mc.compensated_contrast()["pass"]
    found = mc.opioid_contrast()
    assert found["pass"]
    assert found["CENTRAL_DRIVE_FAILURE"]["mechanics_efficiency"] == 1.0
    assert found["MECHANICAL_VENTILATORY_FAILURE"]["availability"] == 1.0


def test_the_arrival_regions_follow_the_predeclared_ordering():
    found = mc.arrival_regions()
    assert found["coherent"] and found["class"] == "CLINICALLY_COHERENT_ORDERING"
    for case_id, region in found["regions"].items():
        low, high = region["region"]
        assert low == region["by_intrinsic"]["12"] and high == region["by_intrinsic"]["20"], case_id


def test_the_implied_efficiency_inverts_the_candidate():
    for rr, paco2, intrinsic in ((30.0, 51.0, 16.0), (6.0, 69.0, 12.0), (34.0, 31.0, 20.0)):
        e = mc.implied_efficiency(rr, paco2, intrinsic)
        assert mc.analytic_paco2(rr, intrinsic, e) == pytest.approx(paco2, rel=1e-12)


def test_no_anchor_absorption_and_one_w():
    assert mc.no_anchor_absorption()["pass"]
    assert mc.w_uniqueness()["pass"]
    assert mc.no_extra_state()["pass"]


def test_load_signal_hr_and_parameters():
    assert mc.respiratory_load_signal()["pass"]
    assert mc.heart_rate()["pass"]
    assert mc.parameter_state()["pass"]


def test_the_default_behaviour_is_unchanged():
    found = mc.non_regression()
    assert found["pass"], found


def test_the_new_anchor_key_is_removed_only_at_the_reference():
    view = mc.without_new_anchor_key({"a": [{"case_id": "x", "arrival_mechanics_efficiency": 1.0, "hr": 80}]})
    assert view == {"a": [{"case_id": "x", "hr": 80}]}
    with pytest.raises(AssertionError):
        mc.without_new_anchor_key({"case_id": "x", "arrival_mechanics_efficiency": 0.5})


# The readiness rule ---------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def found():
    return mc.run()


def test_the_readiness(found):
    assert found["readiness"]["verdict"] == mc.READY and found["readiness"]["blocker"] is None
    assert found["readiness"]["recommendation"].startswith("PROCEED_TO_ASTHMA_SHADOW_MIGRATION")


@pytest.mark.parametrize("path, index", [
    (("arrival_regions", "coherent"), 6),
    (("non_regression", "pass"), 7),
    (("parameter_state", "pass"), 8),
    (("w_uniqueness", "pass"), 2),
    (("high_rr_high_paco2", "pass"), 3),
])
def test_the_first_failing_criterion_blocks(found, path, index):
    broken = json.loads(json.dumps(found))
    broken[path[0]][path[1]] = False
    verdict = mc.readiness(broken)
    assert verdict["blocker"] == mc.READINESS_CRITERIA[index] and verdict["verdict"].startswith(mc.NOT_READY)


# The frozen record and the document ------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def record():
    if not mc.RECORD.exists():
        pytest.skip("the P2S-2 record is written by the evaluation run, after the freeze")
    return json.loads(mc.RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, found):
    assert record["freeze_digest"] == FROZEN_DIGEST
    assert record == json.loads(json.dumps(found, sort_keys=True, default=str))
    assert record["readiness"]["verdict"] == mc.READY


def test_the_document_is_generated_from_the_record(record):
    from clinical_core import respiratory_mechanics_report as report
    text = mc.DOCUMENT.read_text(encoding="utf-8")
    for name, render in report.RENDERERS.items():
        opening, closing = report.MARKERS[name]
        assert text.count(opening) == 1 and text.count(closing) == 1
        assert text.split(opening)[1].split(closing)[0].strip("\n") == render(record).strip("\n")
