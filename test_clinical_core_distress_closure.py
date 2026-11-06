"""P2T-1A: the respiratory distress semantic / numerical closure (M1 and L1 only; shadow only).

These tests hold M1 (DISTRESS_REQUIRES_COMMON_MECHANICS_FOR_RESPIRATORY_EFFECT: the respiratory effect of a distress
above 0 is refused with the mechanics candidate off; the sympathetic reader alone, distress 0 and the default are
accepted; no PaCO2 anchoring returns, DISTRESS_IN_ANCHOR = REJECTED), L1 A-F (math.fsum plus a roundoff-scale tolerance,
no clinical epsilon), the audit of the changed functions, the non-regression and the proof that every other common file
is P2T-1's.
"""
from __future__ import annotations

import itertools
import json
import math
from dataclasses import fields, replace

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import distress_closure as xm
from clinical_core import asthma_distress_migration as tm
from clinical_core import oxygenation_link as om
from clinical_core import opioid_migration as un
from clinical_core import systemic_stress as ss
from clinical_core import distributive_tone as dt
from clinical_core import respiratory_distress as dm
from clinical_core.integration import distress_sum, step
from clinical_core.provenance import ProvenanceError
from clinical_core.state import CoreInvariantError

#: The P2T-1A freeze: the guard and sum audit, the M1 and L1 probes, the readiness rule, the proof and every
#: clinical_core source but the downstream reports, committed before the evaluation run.
FROZEN_DIGEST = "476e18f0e30f80745d2426d264bcf2e9a8617f7cdc585cc506f6c4e143c71982"

#: P2T-3 added files (the asthma distress migration) and two tuple entries, proven against the P2T-1A files
#: (asthma_distress_migration.proved): this package's guards read the tree as P2T-1A left it (tm.chain,
#: tm.p2t1a_sources); P2T-3 changes no behaviour.
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
_LIVE_SOURCES_P2W1 = bf.freeze_sources


def _LIVE_SOURCES_P2V1() -> dict:
    return dt.p2v1_sources(_LIVE_SOURCES_P2W1())


def _LIVE_SOURCES_P2U1() -> dict:
    return ss.p2u1_sources(_LIVE_SOURCES_P2V1())


def _LIVE_SOURCES_P2T5() -> dict:
    return un.p2t5_sources(_LIVE_SOURCES_P2U1())


def _LIVE_SOURCES_P2T3() -> dict:
    return om.p2t3_sources(_LIVE_SOURCES_P2T5())


@pytest.fixture(autouse=True, scope="module")
def _p2t1a_tree():
    with pytest.MonkeyPatch.context() as patch:
        tm.chain(patch)
        om.chain(patch)
        un.chain(patch)
        ss.chain(patch)
        dt.chain(patch)
        patch.setattr(bf, "freeze_sources", lambda: tm.p2t1a_sources(_LIVE_SOURCES_P2T3()))
        yield


# The frozen package and its proof -------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert all(relative in sources for relative in xm.OWN) and xm.REPORT not in sources
    assert set(xm.TUPLES_ADDED["DOWNSTREAM_REPORTS"]) <= set(lactate_slice.DOWNSTREAM_REPORTS)
    assert set(xm.TUPLES_ADDED["PACK_DIGEST_EXCLUDED"]) <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    if FROZEN_DIGEST is not None:
        assert xm.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_only_the_declared_insertions_differ_from_p2t1():
    assert set(xm.REVERSAL) == set(xm.CORE_AT_P2T1) == set(xm.CORE_FILES) | {"clinical_core/lactate_slice.py",
                                                                             "clinical_core/decision_pack.py"}
    assert all(xm.proofs().values())
    common = xm.common_untouched()
    assert all(common.values()) and len(common) >= 119
    assert {"clinical_core/state.py", "clinical_core/provenance.py", "clinical_core/respiratory_distress.py",
            "clinical_core/respiratory_mechanics.py", "clinical_core/asthma_migration.py"} <= set(common)
    proof = xm.upstream_unchanged()
    assert proof["p2t1_freeze_digest"] and proof["p2t1_proof"] and proof["p2t1_record"]


@pytest.mark.parametrize("relative, old, new", [
    ("clinical_core/derived.py", "    if distress > 0.0 and profile.distress_to_respiratory_drive_gain is not None and not ",
     "    if distress > 1.0 and profile.distress_to_respiratory_drive_gain is not None and not "),
    ("clinical_core/integration.py", "    if value < 0.0 and -value <= math.ulp(1.0) * math.fsum(",
     "    if value < 0.0 and -value <= 1e-9 + math.fsum("),
    ("clinical_core/derived.py", "        check_distress_respiratory_effect(profile, distress)\n", "\n"),
])
def test_the_proof_notices_any_other_change(relative, old, new):
    live = xm._live(relative)
    assert live.count(old) == 1 and not xm.proved(relative, live.replace(old, new))


def test_the_changed_functions_are_only_the_declared_ones():
    found = xm.audit()
    assert found["pass"], found
    assert found["derived"]["added"] == [xm.GUARD] and found["integration"]["added"] == [xm.SUM]


# M1 --------------------------------------------------------------------------------------------------------------------------

def _some(**changes):
    return dm.probe_anchors(arrival_respiratory_distress=xm.PROBE_DISTRESS, **changes)


@pytest.mark.parametrize("respiratory, sympathetic", [(xm.RESPIRATORY_GAIN, xm.SYMPATHETIC_GAIN),
                                                      (xm.RESPIRATORY_GAIN, None)])
def test_m1_arrival_distress_with_the_respiratory_reader_needs_mechanics(respiratory, sympathetic):
    off = xm.readers(xm.mechanics_off(), respiratory, sympathetic)
    with pytest.raises(CoreInvariantError):
        dv.arrival_state(_some(), off)
    on = xm.readers(xm.mechanics_on(), respiratory, sympathetic)
    assert dv.arrival_state(_some(), on).aux.respiratory_distress == xm.PROBE_DISTRESS


def test_m1_an_evolving_distress_read_by_the_respiratory_drive_needs_mechanics():
    off = xm.readers(xm.mechanics_off())
    state = dv.arrival_state(dm.PROBE_ANCHORS, off)
    with pytest.raises(CoreInvariantError):
        step(state, (dm.SyntheticDistress("x", 1.0),), dm.PROBE_ANCHORS, off)
    forced = state.evolve(aux=replace(state.aux, respiratory_distress=1.0))
    with pytest.raises(CoreInvariantError):
        dv.derive(forced, dm.PROBE_ANCHORS, off)


def test_m1_the_sympathetic_reader_alone_is_accepted_with_mechanics_off():
    symp = xm.readers(xm.mechanics_off(), respiratory=None)
    lifted, base = dm.at_arrival(_some(), symp), dm.at_arrival(dm.PROBE_ANCHORS, symp)
    assert lifted["hr"] > base["hr"]
    assert all(lifted[k] == base[k] for k in ("rr", "paco2", "ph", "W"))
    after, _ = step(dv.arrival_state(dm.PROBE_ANCHORS, symp), (dm.SyntheticDistress("x", 1.0),), dm.PROBE_ANCHORS, symp)
    assert after.aux.respiratory_distress == 1.0


def test_m1_distress_zero_and_the_default_are_accepted():
    off = xm.readers(xm.mechanics_off())
    unset, zero = dm.at_arrival(dm.PROBE_ANCHORS, xm.mechanics_off()), dm.at_arrival(dm.PROBE_ANCHORS, off)
    assert zero == unset
    step(dv.arrival_state(dm.PROBE_ANCHORS, off), (dm.SyntheticDistress("x", 0.0),), dm.PROBE_ANCHORS, off)
    assert not dv.respiratory_distress_read(dv.DEFAULT_PROFILE)
    dv.arrival_state(dm.PROBE_ANCHORS, dv.DEFAULT_PROFILE)


def test_m1_no_paco2_anchoring_returns():
    on = xm.readers(xm.mechanics_on())
    rows = [dm.at_arrival(_some(arrival_paco2=p), on) for p in xm.ARRIVAL_PACO2_VALUES]
    assert len({r["paco2"] for r in rows}) == 1
    found = xm.audit()
    assert found["anchor_readers_are_p2t1s"] and found["guard_reads_no_anchor"]


def test_m1_the_committed_mechanics_off_mappings_are_refused_and_asthma_is_not():
    found = xm.m1()
    assert found["pass"], found
    committed = found["committed"]
    assert {k for k, v in committed.items() if v["refused"]} == {"pulmonary_edema_58m", "pulmonary_embolism_61m",
                                                                  "pulmonary_embolism_33f"}
    assert all(v["sympathetic_only_accepted"] for v in committed.values())


# L1 A-F ------------------------------------------------------------------------------------------------------------------------

def _exact_zero(value):
    return value == 0.0 and math.copysign(1.0, value) == 1.0


def test_l1_a_the_triad_is_exactly_zero():
    assert math.fsum((0.3, -0.1, -0.2)) < 0.0                       # the binary64 sum is about -2.8e-17
    assert _exact_zero(distress_sum(0.0, [0.3, -0.1, -0.2]))
    on = xm.readers(xm.mechanics_on())
    state = dv.arrival_state(dm.PROBE_ANCHORS, on)
    one, _ = step(state, xm._writers((0.3, -0.1, -0.2), 1), dm.PROBE_ANCHORS, on)
    assert _exact_zero(one.aux.respiratory_distress)
    for amount in (0.3, -0.1, -0.2):
        state, _ = step(state, xm._writers((amount,), state.minute + 1), dm.PROBE_ANCHORS, on)
    assert _exact_zero(state.aux.respiratory_distress)


@pytest.mark.parametrize("order", list(itertools.permutations((0.3, -0.1, -0.2))))
def test_l1_b_any_order_in_one_minute_gives_the_same_result(order):
    assert _exact_zero(distress_sum(0.0, list(order)))


def test_l1_b_minute_by_minute_orders_give_the_same_result():
    found = xm.l1()["B"]
    assert found["pass"], found
    assert found["refused_exactly_when_a_minute_ends_materially_below_0"]


@pytest.mark.parametrize("before, amounts", xm.ROUNDOFF_NEGATIVES)
def test_l1_c_a_roundoff_negative_is_zero(before, amounts):
    assert math.fsum((before, *amounts)) < 0.0
    assert _exact_zero(distress_sum(before, list(amounts)))


@pytest.mark.parametrize("before, amounts", xm.MATERIAL_NEGATIVES)
def test_l1_d_a_material_negative_is_refused(before, amounts):
    assert distress_sum(before, list(amounts)) < 0.0
    on = xm.readers(xm.mechanics_on())
    state = dv.arrival_state(dm.PROBE_ANCHORS, on)
    if before:
        state, _ = step(state, xm._writers((before,), 1), dm.PROBE_ANCHORS, on)
    with pytest.raises(ProvenanceError):
        step(state, xm._writers(amounts, state.minute + 1), dm.PROBE_ANCHORS, on)


@pytest.mark.parametrize("before, amounts", xm.SMALL_POSITIVES)
def test_l1_e_a_small_positive_is_kept(before, amounts):
    raw = math.fsum((before, *amounts))
    assert raw > 0.0 and distress_sum(before, list(amounts)) == raw


def test_l1_f_no_clinical_parameter_or_threshold():
    found = xm.l1()["F"]
    assert found["pass"], found
    assert found["profile_fields_are_p2t1s"] and found["parameter_names_are_p2t1s"]
    assert set(found["sum_constants"]) <= {0.0, 1.0}
    # P2T-5: the profile as the closed listings read it (xm.fields: P2T-5's one new field, None in every closed profile,
    # out through om.chain), against the P2T-1 text.
    assert sorted(f.name for f in xm.fields(dv.CoreProfile)) == sorted(dm._class_fields(
        xm.p2t1_text("clinical_core/derived.py"), "CoreProfile"))


@pytest.mark.parametrize("k", xm.SCALES)
def test_l1_f_the_decision_is_scale_invariant(k):
    assert _exact_zero(distress_sum(0.0, [k * 0.3, -k * 0.1, -k * 0.2]))
    assert distress_sum(k * 0.3, [-k * 0.31]) < 0.0


# The non-regression and the readiness rule -----------------------------------------------------------------------------------

def test_the_p2t1_view_restores_p2t1s_sources_and_behaviour():
    with xm.p2t1_view():
        assert "check_distress_respiratory_effect" not in dm._live("clinical_core/derived.py")
        assert "distress_sum" not in (dm.CORE_DIR / "integration.py").read_text(encoding="utf-8")
        dv.arrival_state(_some(), xm.readers(xm.mechanics_off()))      # P2T-1 had no M1 guard
    with pytest.raises(CoreInvariantError):
        dv.arrival_state(_some(), xm.readers(xm.mechanics_off()))


@pytest.fixture(scope="module")
def found():
    return xm.run()


def test_the_non_regression(found):
    n = found["non_regression"]
    assert n["pass"], n
    assert all(n["p2t1_probes_live"].values()) and n["p2t1_contrasts_live_refused_by_m1"]
    assert n["p2t1_record_reproduced_on_its_tree"] and n["p2s3_historical_verdict"] == "ASTHMA_SHADOW_MIGRATION_READY"


def test_the_readiness(found):
    assert found["readiness"]["verdict"] == xm.READY and found["readiness"]["blocker"] is None


@pytest.mark.parametrize("path, index", [
    (("l1", "pass"), 3), (("audit", "pass"), 4), (("non_regression", "pass"), 5),
])
def test_the_first_failing_criterion_blocks(found, path, index):
    broken = json.loads(json.dumps(found))
    broken[path[0]][path[1]] = False
    verdict = xm.readiness(broken)
    assert verdict["blocker"] == xm.READINESS_CRITERIA[index] and verdict["verdict"].startswith(xm.NOT_READY)


# The frozen record and the document ------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def record():
    if not xm.RECORD.exists():
        pytest.skip("the P2T-1A record is written by the evaluation run, after the freeze")
    return json.loads(xm.RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, found):
    assert record["freeze_digest"] == FROZEN_DIGEST
    assert record == json.loads(json.dumps(found, sort_keys=True, default=str))


def test_the_document_is_generated_from_the_record(record):
    from clinical_core import distress_closure_report as report
    text = xm.DOCUMENT.read_text(encoding="utf-8")
    for name, render in report.RENDERERS.items():
        opening, closing = report.MARKERS[name]
        assert text.count(opening) == 1 and text.count(closing) == 1
        assert text.split(opening)[1].split(closing)[0].strip("\n") == render(record).strip("\n")
