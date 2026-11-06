"""P2T-1: the minimum common respiratory distress architecture (shadow only, inert by default).

These tests hold the auxiliary distress and its writer, the two UNSET readers and their independence, the composition
with the acid drive before the saturation, the central-availability gate on the RR only, beta-blockade downstream, the
refusals, D1-D12, the case contrasts, the WOB ordering (evidence only), the mechanics / distress orthogonality, the
parameter state, the absence of systemic stress, the default non-regression and the proof that every other common file is
P2S-3's.
"""
from __future__ import annotations

import json
from dataclasses import replace

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import asthma_migration as sm
from clinical_core import respiratory_distress as dm
from clinical_core import distress_closure as xm
from clinical_core import asthma_distress_migration as tm
from clinical_core import oxygenation_link as om
from clinical_core import opioid_migration as un
from clinical_core import systemic_stress as ss
from clinical_core import distributive_tone as dt
from clinical_core import tone_domain as x1
from clinical_core import respiratory_mechanics as mc
from clinical_core.integration import step
from clinical_core.provenance import DistressChange, ProvenanceError
from clinical_core.state import CoreInvariantError

#: The P2T-1 freeze: the core insertions, the probes, the synthetic grids, the readiness rule, the proof and every
#: clinical_core source but the downstream reports, committed before the evaluation run.
FROZEN_DIGEST = "773188d100813d0cced871f007d35c18bdeff18d95e7d4cecab160cc46c0fc2c"

#: P2T-1A changed two common files (the M1 guard and the L1 sum) and two tuple files, proven against the P2T-1 files
#: (distress_closure.proved): this package's guards read the tree as P2T-1 left it (xm.chain, xm.p2t1_sources), with the
#: two new helpers read as P2T-1 had them (no M1 guard, the unnormalized sum); its record is unchanged.
#: P2T-3 added files (the asthma distress migration) and two tuple entries, proven against the P2T-1A files
#: (asthma_distress_migration.proved): this package's guards read the tree as P2T-1A left it (tm.chain,
#: tm.p2t1a_sources).
#: P2T-5 changed the core (the hypoventilation -> oxygenation link, off by default: one UNSET profile field) and
#: two tuple files, proven against the P2T-3 files (oxygenation_link.proved): this package's guards read the
#: tree as P2T-3 left it (om.chain, om.p2t3_sources).
#: P2W-1 changed the core (the common vasodilatory burden: one auxiliary field, one arrival anchor, one
#: provenance record and one UNSET profile reader of the tone target, the burden 0 by default) and two tuple
#: files, proven against the P2V-1 files (distributive_tone.proved): this package's guards read the tree as
#: P2V-1 left it (dt.chain, dt.p2v1_sources).
#: P2V-1 changed the core (the common systemic stress: one auxiliary field, one arrival anchor, one provenance
#: record and one UNSET profile reader, the stress 0 by default) and two tuple files, proven against the P2U-1
#: files (systemic_stress.proved): this package's guards read the tree as P2U-1 left it (ss.chain,
#: ss.p2u1_sources).
#: P2U-1 changed the core (the common central respiratory drive availability: one auxiliary field, one arrival
#: anchor and one provenance record, all at their reference 1 by default) and two tuple files, proven against the
#: P2T-5 files (opioid_migration.proved): this package's guards read the tree as P2T-5 left it (un.chain,
#: un.p2t5_sources).
_LIVE_SOURCES_P2X1 = bf.freeze_sources


def _LIVE_SOURCES_P2W1() -> dict:
    return x1.p2w1_sources(_LIVE_SOURCES_P2X1())


def _LIVE_SOURCES_P2V1() -> dict:
    return dt.p2v1_sources(_LIVE_SOURCES_P2W1())


def _LIVE_SOURCES_P2U1() -> dict:
    return ss.p2u1_sources(_LIVE_SOURCES_P2V1())


def _LIVE_SOURCES_P2T5() -> dict:
    return un.p2t5_sources(_LIVE_SOURCES_P2U1())


def _LIVE_SOURCES_P2T3() -> dict:
    return om.p2t3_sources(_LIVE_SOURCES_P2T5())


def _LIVE_SOURCES_P2T1A() -> dict:
    return tm.p2t1a_sources(_LIVE_SOURCES_P2T3())


@pytest.fixture(autouse=True, scope="module")
def _p2t1_tree():
    with pytest.MonkeyPatch.context() as patch:
        xm.chain(patch)
        tm.chain(patch)
        om.chain(patch)
        un.chain(patch)
        ss.chain(patch)
        dt.chain(patch)
        x1.chain(patch)
        patch.setattr(bf, "freeze_sources", lambda: xm.p2t1_sources(_LIVE_SOURCES_P2T1A()))
        yield


# The frozen package and its proof -------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert all(relative in sources for relative in dm.OWN) and dm.REPORT not in sources
    assert set(dm.TUPLES_ADDED["DOWNSTREAM_REPORTS"]) <= set(lactate_slice.DOWNSTREAM_REPORTS)
    assert set(dm.TUPLES_ADDED["PACK_DIGEST_EXCLUDED"]) <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    if FROZEN_DIGEST is not None:
        assert dm.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_only_the_declared_insertions_differ_from_p2s3():
    assert set(dm.REVERSAL) == set(dm.CORE_AT_P2S3) == set(dm.CORE_FILES) | {"clinical_core/lactate_slice.py",
                                                                            "clinical_core/decision_pack.py"}
    assert all(dm.proofs().values())
    common = dm.common_untouched()
    assert all(common.values()) and len(common) >= 115
    assert {"clinical_core/respiratory_mechanics.py", "clinical_core/asthma_migration.py",
            "clinical_core/modules/asthma.py"} <= set(common)
    proof = dm.upstream_unchanged()
    assert proof["p2s3_freeze_digest"] and proof["p2s3_proof"] and proof["p2s3_record"]


@pytest.mark.parametrize("relative, old, new", [
    ("clinical_core/derived.py", "        excitatory = excitatory + distress_drive\n",
     "        excitatory = excitatory + 2.0 * distress_drive\n"),
    ("clinical_core/derived.py", "    distress_to_sympathetic_gain: float | None = None\n",
     "    distress_to_sympathetic_gain: float | None = 0.01\n"),
    ("clinical_core/integration.py", "    value = state.aux.respiratory_distress + math.fsum(",
     "    value = 0.99 * state.aux.respiratory_distress + math.fsum("),
])
def test_the_proof_notices_any_other_change(relative, old, new):
    live = dm._live(relative)
    assert live.count(old) == 1 and not dm.proved(relative, live.replace(old, new))


def test_the_closed_packages_read_the_p2s3_tree():
    with pytest.MonkeyPatch.context() as patch:
        dm.chain(patch)
        assert "respiratory_distress" not in sm._live("clinical_core/derived.py")
        assert all(sm.common_untouched().values())
        assert "respiratory_distress" not in mc.AUXILIARY_FIELDS
        assert mc.without_new_anchor_key({"case_id": "x", dm.NEW_ANCHOR_KEY: 0.0}) == {"case_id": "x"}
        with pytest.raises(AssertionError):
            mc.without_new_anchor_key({"case_id": "x", dm.NEW_ANCHOR_KEY: 1.0})
    assert "respiratory_distress" in sm._live("clinical_core/derived.py")


def test_the_p2s3_sources_leave_out_the_p2t1_files():
    sources = dm.p2s3_sources(bf.freeze_sources())
    assert not set(dm.OWN) & set(sources)
    for relative, sha in dm.CORE_AT_P2S3.items():
        if relative in sources:
            assert sources[relative] == sha


# The state, the writer and the refusals ---------------------------------------------------------------------------------------

def test_the_default_core_reads_no_distress():
    p = dv.DEFAULT_PROFILE
    assert p.distress_to_respiratory_drive_gain is None and p.distress_to_sympathetic_gain is None
    assert not dv.respiratory_distress_read(p)
    assert dv.arrival_state(dm.PROBE_ANCHORS, dm.base_profile()).aux.respiratory_distress == 0.0


def test_the_representation_and_its_refusals():
    found = dm.representation()
    assert found["pass"], found


@pytest.mark.parametrize("amount", [float("nan"), float("inf"), True, "1"])
def test_a_distress_change_is_a_finite_number(amount):
    with pytest.raises(ProvenanceError):
        DistressChange(amount, dm.PROBE_SOURCE, 1, "x")


@pytest.mark.parametrize("gain", [0.0, -1.0, float("nan"), True])
def test_a_declared_reader_has_a_positive_gain(gain):
    with pytest.raises(CoreInvariantError):
        dm.readers(dm.base_profile(), gain, None)
    with pytest.raises(CoreInvariantError):
        dm.readers(dm.base_profile(), None, gain)


def test_nothing_is_written_while_no_reader_is_declared():
    off = dm.base_profile()
    with pytest.raises(ProvenanceError):
        step(dv.arrival_state(dm.PROBE_ANCHORS, off), (dm.SyntheticDistress("x", 1.0),), dm.PROBE_ANCHORS, off)
    with pytest.raises(CoreInvariantError):
        dv.arrival_state(dm.probe_anchors(arrival_respiratory_distress=1.0), off)


def test_the_distress_never_goes_below_zero_and_is_conserved():
    on = dm.readers(dm.base_profile())
    state = dv.arrival_state(dm.probe_anchors(arrival_respiratory_distress=2.0), on)
    with pytest.raises(ProvenanceError):
        step(state, (dm.SyntheticDistress("x", -3.0),), dm.PROBE_ANCHORS, on)
    after, record = step(state, (dm.SyntheticDistress("x", -0.5),), dm.PROBE_ANCHORS, on)
    assert after.aux.respiratory_distress == 1.5 and [c.amount for c in record.distress] == [-0.5]
    assert record.to_dict()["distress"][0]["type"] == "distress"


def test_the_insertion_points():
    found = dm.audit()
    assert found["pass"], found


# D1-D12 ------------------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def probes():
    return dm.structural_probes()


@pytest.mark.parametrize("name", sorted(dm.PROBES, key=lambda k: int(k[1:])))
def test_each_structural_probe(probes, name):
    assert probes[name]["pass"], (name, probes[name])


def test_the_readers_are_independent(probes):
    delta = probes["D4"]["delta"]
    assert delta["rr_only"]["hr"] == 0.0 and delta["hr_only"]["rr"] == 0.0
    assert delta["B"]["rr"] / delta["A"]["rr"] != delta["B"]["hr"] / delta["A"]["hr"]


def test_central_depression_gates_the_rr_and_not_the_hr(probes):
    assert probes["D5"]["rr"][-1] == 0.0 and set(probes["D5"]["distress"]) == {dm.PROBE_DISTRESS}
    assert len(set(probes["D6"]["hr"])) == 1


# Contrasts, beta-blockade, ordering, orthogonality ----------------------------------------------------------------------------

def test_the_case_contrasts():
    found = dm.contrasts()
    assert found["pass"], found
    assert found["acs_70f_left_main"]["status"] == "SYSTEMIC_STRESS_DEFERRED"


def test_beta_blockade_stays_downstream():
    found = dm.beta_blockade()
    assert found["pass"], found


def test_the_wob_ordering_is_evidence_only():
    found = dm.wob_ordering()
    assert found["pass"] and not found["fitted_to_rr_or_hr"]
    assert found["status"].endswith("WOB_NUMERIC_MAPPING_UNSET")


def test_mechanics_and_distress_are_orthogonal():
    found = dm.orthogonality()
    assert found["pass"], found


def test_the_observable_parameters_and_scope():
    assert dm.observable()["pass"]
    assert dm.parameter_state()["pass"]
    assert dm.systemic_stress()["pass"]


def test_the_closed_records_are_reproduced():
    found = dm.non_regression()
    assert found["pass"], found
    assert found["p2s3_historical_verdict"] == sm.READY       # the frozen record, untouched (documentation debt)


# The readiness rule ------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def found():
    return dm.run()


def test_the_readiness(found):
    assert found["readiness"]["verdict"] == dm.READY and found["readiness"]["blocker"] is None
    assert found["readiness"]["composition"] == list(dm.COMPOSITION_CLASSES)


@pytest.mark.parametrize("path, index", [
    (("representation", "pass"), 0), (("orthogonality", "pass"), 1), (("beta_blockade", "pass"), 8),
    (("systemic_stress", "pass"), 10),
])
def test_the_first_failing_criterion_blocks(found, path, index):
    broken = json.loads(json.dumps(found))
    broken[path[0]][path[1]] = False
    verdict = dm.readiness(broken)
    assert verdict["blocker"] == dm.READINESS_CRITERIA[index] and verdict["verdict"].startswith(dm.NOT_READY)


# The frozen record and the document ------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def record():
    if not dm.RECORD.exists():
        pytest.skip("the P2T-1 record is written by the evaluation run, after the freeze")
    return json.loads(dm.RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, found):
    assert record["freeze_digest"] == FROZEN_DIGEST
    assert record == json.loads(json.dumps(found, sort_keys=True, default=str))


def test_the_document_is_generated_from_the_record(record):
    from clinical_core import respiratory_distress_report as report
    text = dm.DOCUMENT.read_text(encoding="utf-8")
    for name, render in report.RENDERERS.items():
        opening, closing = report.MARKERS[name]
        assert text.count(opening) == 1 and text.count(closing) == 1
        assert text.split(opening)[1].split(closing)[0].strip("\n") == render(record).strip("\n")
