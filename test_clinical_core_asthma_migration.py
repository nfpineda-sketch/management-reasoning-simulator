"""P2S-3: asthma_49m and asthma_24f migrated in shadow with a family mechanics writer (shadow only).

The family's airflow obstruction writes the P2S-2 common mechanics efficiency only; every other consequence is common.
These tests hold the writer's semantics and refusals, the arrival mapping, the 49m / 24f contrast, the courses, the
unchanged drive, the HR gap kept diagnostic, the non-regression of the closed packages and the proof that every common
file is P2S-2's.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from clinical_core import asthma_migration as sm
from clinical_core import respiratory_distress as dm
from clinical_core import distress_closure as xm
from clinical_core import asthma_distress_migration as tm
from clinical_core import oxygenation_link as om
from clinical_core import opioid_migration as un
from clinical_core import systemic_stress as ss
from clinical_core import distributive_tone as dt
from clinical_core import closure_guard as cg
from clinical_core import amendment_2 as a2
from clinical_core import tone_domain as x1
from clinical_core import asthma_reference as sr
from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import respiratory_mechanics as mc
from clinical_core.integration import step
from clinical_core.modules.asthma import AirwayObstruction
from clinical_core.provenance import ProvenanceError
from clinical_core.state import CoreInvariantError

#: The P2S-3 freeze: the cases and their mapping, the writer, the predeclared span, the trajectories, the verdict rule,
#: the proof and every clinical_core source but the downstream reports, committed before the evaluation run.
FROZEN_DIGEST = "652d7138ff672fa9e43c92e06ac3042486e8f47ab504736726b0d53f42a7649b"

#: P2T-1 changed four common files and the two registry tuples (proven against P2S-3's, respiratory_distress.proved):
#: this package's guards read the tree as P2S-3 left it (dm.chain, dm.p2s3_sources); its record is unchanged.
#: P2T-1A changed two common files (the M1 guard and the L1 sum) and two tuple files, proven against the
#: P2T-1 files (distress_closure.proved): this package's guards read the tree as P2T-1 left it
#: (xm.chain, xm.p2t1_sources).
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
_LIVE_SOURCES_P2X1A = bf.freeze_sources


def _LIVE_SOURCES_P2X1() -> dict:
    return cg.p2x1_sources(_LIVE_SOURCES_P2X1A())


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


def _LIVE_SOURCES_P2T1() -> dict:
    return xm.p2t1_sources(_LIVE_SOURCES_P2T1A())


@pytest.fixture(autouse=True, scope="module")
def _p2s3_tree():
    with pytest.MonkeyPatch.context() as patch:
        dm.chain(patch)
        xm.chain(patch, historical=False)
        tm.chain(patch)
        om.chain(patch)
        un.chain(patch)
        ss.chain(patch)
        dt.chain(patch)
        x1.chain(patch)
        cg.chain(patch)
        a2.chain(patch)
        patch.setattr(bf, "freeze_sources", lambda: dm.p2s3_sources(_LIVE_SOURCES_P2T1()))
        yield


# The frozen package and its proof -------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert all(relative in sources for relative in sm.OWN) and sm.REPORT not in sources
    assert set(sm.TUPLES_ADDED["DOWNSTREAM_REPORTS"]) <= set(lactate_slice.DOWNSTREAM_REPORTS)
    assert set(sm.TUPLES_ADDED["PACK_DIGEST_EXCLUDED"]) <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    # The case mapping and the family writer stay in the P2G pack digest; the analysis and its report leave it.
    assert not {sm.OWN[0], sm.OWN[1]} & set(decision_pack.PACK_DIGEST_EXCLUDED)
    if FROZEN_DIGEST is not None:
        assert sm.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_no_common_file_changed_and_the_tuples_differ_only_by_p2s3_entries():
    assert set(sm.REVERSAL) == set(sm.CORE_AT_P2S2) == {"clinical_core/lactate_slice.py",
                                                        "clinical_core/decision_pack.py"}
    assert all(sm.proofs().values())
    common = sm.common_untouched()
    assert all(common.values()) and len(common) >= 100
    assert {"clinical_core/derived.py", "clinical_core/integration.py", "clinical_core/state.py",
            "clinical_core/provenance.py", "clinical_core/respiratory_mechanics.py"} <= set(common)
    proof = sm.upstream_unchanged()
    assert proof["p2s2_freeze_digest"] and proof["p2s2_proof"] and proof["p2s2_record"]


@pytest.mark.parametrize("old, new", [
    ('"clinical_core/asthma_migration_report.py")', '"clinical_core/asthma_migration_report.py", "x.py")'),
    ('"clinical_core/respiratory_mechanics_report.py",\n', '"clinical_core/respiratory_mechanics_reports.py",\n'),
])
def test_the_proof_notices_any_other_change(old, new):
    live = sm._live("clinical_core/lactate_slice.py")
    assert live.count(old) == 1 and not sm.proved("clinical_core/lactate_slice.py", live.replace(old, new))


def test_closed_packages_read_the_p2s2_tree():
    with pytest.MonkeyPatch.context() as patch:
        sm.chain(patch)
        dm.chain(patch)
        xm.chain(patch, historical=False)
        tm.chain(patch)
        om.chain(patch)
        un.chain(patch)
        ss.chain(patch)
        dt.chain(patch)
        x1.chain(patch)
        cg.chain(patch)
        a2.chain(patch)
        assert "asthma" not in mc._live("clinical_core/lactate_slice.py")
        assert "asthma" not in mc._live("clinical_core/decision_pack.py")
        assert all(mc.proofs().values())
        assert mc.interface()["pass"] and not mc.interface()["family_writers"]
    assert "asthma_migration_report" in mc._live("clinical_core/lactate_slice.py")
    assert sm.FAMILY_FILE in mc.interface()["family_writers"]


def test_the_p2s2_sources_leave_out_the_p2s3_files():
    sources = sm.p2s2_sources(bf.freeze_sources())
    assert not set(sm.OWN) & set(sources)
    for relative, sha in sm.CORE_AT_P2S2.items():
        assert sources[relative] == sha


# The family writer ------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("value", [-0.01, 1.0, 1.5, float("nan"), float("inf"), True])
def test_the_writer_refuses_impossible_rates(value):
    with pytest.raises(CoreInvariantError):
        AirwayObstruction("x", value)


def test_the_writer_writes_the_mechanics_only():
    found = sm.writer_semantics()
    assert found["pass"], found
    a, p = sr.anchors(), sm.profile()
    s = dv.arrival_state(a, p)
    c = sm.obstruction(0.01).contribute(s, 1, (), a, p)
    assert [m.factor for m in c.mechanics] == [0.99]
    assert not (c.deltas or c.transitions or c.settings or c.events or c.demand or c.blood)
    after, record = step(s, (sm.obstruction(0.01),), a, p)
    assert after.aux.mechanics_efficiency == pytest.approx(s.aux.mechanics_efficiency * 0.99)
    assert [m.source.key for m in record.mechanics] == ["disease_module:asthma-obstruction"]


def test_the_core_refuses_the_writer_with_the_candidate_off():
    off = sm.go.gas_profile(sm.ar.common_profile())
    a = sr.anchors(arrival_mechanics_efficiency=1.0)
    with pytest.raises(ProvenanceError):
        step(dv.arrival_state(a, off), (sm.obstruction(),), a, off)
    with pytest.raises(CoreInvariantError):
        dv.arrival_state(sr.anchors(), off)


# The arrival mapping and the contrast -----------------------------------------------------------------------------------------

def test_the_truth_is_read_by_path():
    found = sm.case()
    assert found["available"]
    t = found["cases"][sr.CASE]["truth"]
    assert (t["respiratory_rate"], t["abg_paco2"], t["mental_status"]) == (30, 51, "Drowsy")
    s = found["cases"][sr.SECONDARY]["truth"]
    assert (s["respiratory_rate"], s["abg_paco2"], s["mental_status"]) == (34, 31, "Alert")
    assert "35%" in found["cases"][sr.SECONDARY]["peak_flow"]


def test_the_mechanics_band_is_the_analytic_region():
    for name in sr.CASES:
        t = sr.truth(name)
        band = sr.mechanics_band(name)
        for point, intrinsic in sr.INTRINSIC_POINTS.items():
            value = getattr(band, point)
            assert value == pytest.approx(40.0 * intrinsic / (t["abg_paco2"] * t["respiratory_rate"]))
            a = sr.anchors(name, point)
            assert (a.intrinsic_respiratory_rate, a.arrival_mechanics_efficiency) == (intrinsic, value)
        assert band.classification == sr.FAMILY_CANDIDATE


@pytest.fixture(scope="module")
def arrival():
    return sm.arrival()


def test_the_arrival_is_coherent(arrival):
    assert arrival["pass"], arrival
    for name in sr.CASES:
        for row in arrival["cases"][name]["points"].values():
            assert row["availability"] == 1.0 and row["L"] == 0.0 and row["G"] == 0.0


def test_the_contrast_is_mechanics_severity_only(arrival):
    found = sm.contrast(arrival)
    assert found["pass"], found
    assert not any(found["secondary_hypocapnic_in_core"].values()), "the drive gap is reported, not hidden"


# Courses, drive, G, HR, collapse --------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def untreated():
    return sm.untreated()


def test_the_untreated_courses_move_only_the_ventilation(untreated):
    assert untreated["pass"]


def test_relief_and_oxygen_are_common():
    assert sm.relief()["pass"]
    assert sm.oxygen()["pass"]


def test_no_direct_g_and_no_false_l():
    found = sm.direct_g()
    assert found["pass"] and not found["used"]
    assert found["cases"][sr.CASE]["hypoventilatory_alveolar_loss"] > 0.0


def test_the_drive_is_p2p2_unchanged():
    found = sm.drive()
    assert found["pass"]
    assert found["cases"][sr.CASE]["unset"]["rr"] < sr.truth(sr.CASE)["respiratory_rate"]


def test_the_hr_gap_stays_diagnostic_and_collapse_is_structural(untreated):
    found = sm.heart_rate()
    assert found["pass"] and all(v["prehospital_beta_agonist"] for v in found["cases"].values())
    assert sm.collapse()["pass"]
    assert sm.consciousness(untreated)["pass"]


def test_the_closed_packages_are_unchanged():
    found = sm.non_regression()
    assert found["pass"], found


# The verdict rule ------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def found():
    return sm.run()


def test_the_verdict(found):
    assert found["verdict"]["verdict"] == sm.READY and found["verdict"]["blocker"] is None


@pytest.mark.parametrize("path, index", [
    (("writer", "pass"), 0), (("contrast", "pass"), 2), (("direct_g", "pass"), 5), (("non_regression", "pass"), 7),
])
def test_the_first_failing_criterion_blocks(found, path, index):
    broken = json.loads(json.dumps(found))
    broken[path[0]][path[1]] = False
    verdict = sm.verdict(broken)
    assert verdict["blocker"] == sm.VERDICT_CRITERIA[index] and verdict["verdict"].startswith(sm.NOT_READY)


# The frozen record and the document ------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def record():
    if not sm.RECORD.exists():
        pytest.skip("the P2S-3 record is written by the evaluation run, after the freeze")
    return json.loads(sm.RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, found):
    assert record["freeze_digest"] == FROZEN_DIGEST
    assert record == json.loads(json.dumps(found, sort_keys=True, default=str))


def test_the_document_is_generated_from_the_record(record):
    from clinical_core import asthma_migration_report as report
    text = sm.DOCUMENT.read_text(encoding="utf-8")
    for name, render in report.RENDERERS.items():
        opening, closing = report.MARKERS[name]
        assert text.count(opening) == 1 and text.count(closing) == 1
        assert text.split(opening)[1].split(closing)[0].strip("\n") == render(record).strip("\n")
