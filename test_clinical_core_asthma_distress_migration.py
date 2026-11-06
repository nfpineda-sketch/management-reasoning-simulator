"""P2T-3: the asthma shadow migration retried with the cross-family respiratory distress region (shadow only).

These tests hold the re-read case truth, P2S-3's writer reused unchanged, the analytic normalization and its scale
invariance, the region-valued (k, rho) and distress mapping, the asthma subregion, the witnesses (only after
non-emptiness) on the live core, the structural courses, the mechanics / distress orthogonality, the cross-family and
control checks, the parameter state, the non-regression and the proof that every other file is P2T-1A's.
"""
from __future__ import annotations

import json
import math

import pytest

from clinical_core import asthma_distress_migration as tm
from clinical_core import asthma_migration as sm
from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import distress_closure as xm
from clinical_core import oxygenation_link as om
from clinical_core import opioid_migration as un
from clinical_core import systemic_stress as ss
from clinical_core import distributive_tone as dt
from clinical_core.state import CoreInvariantError

#: The P2T-3 freeze: the region rule, the witness rule, the probes, the verdict rule, the proof and every clinical_core
#: source but the downstream reports, committed before the evaluation run.
FROZEN_DIGEST = "3a648a9e055c9182fe670f5360f1cc73d1d799b9f1bd3d557df2ffdf67e2efb2"

#: P2T-5 changed the core (the hypoventilation -> oxygenation link, off by default: one UNSET profile field) and two tuple
#: files, proven against the P2T-3 files (oxygenation_link.proved): this package's guards read the tree as P2T-3 left it
#: (om.tree: om.chain, om.p2t3_sources and P2T-1A's reader on the P2T-3 files); P2T-5 changes no behaviour with the link
#: off.


#: P2U-1 changed the core (the common central availability, at its reference 1 by default) and two tuple files, proven
#: against the P2T-5 files (opioid_migration.proved): this view reads the P2T-5 tree first (un.tree), then P2T-5's own
#: view of the P2T-3 tree on top (om.tree).


@pytest.fixture(autouse=True, scope="module")
def _p2t3_tree():
    with pytest.MonkeyPatch.context() as patch:
        dt.tree(patch)
        ss.tree(patch)
        un.tree(patch)
        om.tree(patch)
        yield


# The frozen package and its proof -------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert all(relative in sources for relative in tm.OWN) and tm.REPORT not in sources
    assert set(tm.TUPLES_ADDED["DOWNSTREAM_REPORTS"]) <= set(lactate_slice.DOWNSTREAM_REPORTS)
    assert set(tm.TUPLES_ADDED["PACK_DIGEST_EXCLUDED"]) <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    if FROZEN_DIGEST is not None:
        assert tm.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_no_common_file_changed_only_the_two_tuples():
    assert set(tm.REVERSAL) == set(tm.CORE_AT_P2T1A) == {"clinical_core/lactate_slice.py",
                                                          "clinical_core/decision_pack.py"}
    assert all(tm.proofs().values())
    common = tm.common_untouched()
    assert all(common.values()) and len(common) >= 123
    assert {"clinical_core/derived.py", "clinical_core/integration.py", "clinical_core/state.py",
            "clinical_core/modules/asthma.py", "clinical_core/asthma_reference.py", "clinical_core/asthma_migration.py",
            "clinical_core/distress_closure.py"} <= set(common)
    proof = tm.upstream_unchanged()
    assert proof["p2t1a_freeze_digest"] and proof["p2t1a_proof"] and proof["p2t1a_record"]


@pytest.mark.parametrize("relative, old, new", [
    ("clinical_core/lactate_slice.py", '"clinical_core/asthma_distress_migration_report.py")',
     '"clinical_core/asthma_distress_migration_report.py", "clinical_core/other.py")'),
    ("clinical_core/decision_pack.py", '"clinical_core/asthma_distress_migration.py"',
     '"clinical_core/asthma_distress_migration2.py"'),
])
def test_the_proof_notices_any_other_change(relative, old, new):
    live = tm._live(relative)
    assert live.count(old) == 1 and not tm.proved(relative, live.replace(old, new))


def test_the_p2t1a_view_reads_the_p2t1a_tuples():
    with tm.p2t1a_view():
        assert "asthma_distress_migration" not in xm._live("clinical_core/lactate_slice.py")
        assert not set(tm.OWN) & set(bf.freeze_sources())
    assert "asthma_distress_migration" in xm._live("clinical_core/lactate_slice.py")


# Truth, writer, evidence -----------------------------------------------------------------------------------------------------

def test_the_case_truth_is_p2s3s_and_the_beta_agonist_is_authored():
    found = tm.case_truth()
    assert found["pass"] and found["same_as_p2s3"]
    assert found[tm.PRIMARY]["authored"]["work_of_breathing"] == "Severe"
    assert found[tm.SECONDARY]["authored"]["work_of_breathing"] == "Markedly increased"
    assert "35%" in found[tm.SECONDARY]["peak_flow"]


def test_the_writer_is_p2s3s_unchanged():
    assert tm.writer()["pass"]


def test_the_evidence_orders_49m_above_24f():
    found = tm.evidence()
    assert found["pass"] and found["cases"][tm.PRIMARY]["tier"] == 4 and found["cases"][tm.SECONDARY]["tier"] == 3


# The region ---------------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ev():
    return tm.evidence()


@pytest.fixture(scope="module")
def region(ev):
    return tm.region(ev)


def test_the_asthma_subregion_is_nonempty_at_every_carried_k(region):
    assert region["status"] == "ASTHMA_FEASIBLE_SUBREGION_NONEMPTY" and region["every_carried_k"]
    assert region["monotone_in_k"]
    for k, (lo, hi) in region["rho_conditional"].items():
        assert 0.0 < lo < hi < math.inf, k


def test_rho_is_carried_as_a_conditional_interval_not_a_point(region):
    widths = [hi - lo for lo, hi in region["rho_conditional"].values()]
    assert all(w > 0.05 for w in widths)
    assert region["diagnostic_label"].startswith("DIAGNOSTIC_ONLY")


def test_pe33_is_upper_bound_evidence_only(region):
    for pt in region["points"].values():
        assert pt["rows"]["pulmonary_embolism_33f"]["role"] == "upper_only"
        assert pt["bounds"]["binding"]["lo"] == "pulmonary_embolism_61m"
        assert pt["bounds"]["binding"]["hi"] == "pulmonary_edema_58m"


def test_the_normalized_distress_region_is_an_interval_below_49m(region):
    for pt in region["points"].values():
        for at in pt["at"].values():
            a = at["asthma"]
            assert a["feasible"] and 0.0 < a["d24"][0] < a["d24"][1] <= 1.0
            assert a["mechanics_order_admissible"] and a["E49"][0] < a["E24"][1]


def test_the_acid_gain_is_carried_only_in_1_to_2():
    assert tm.K_REGION == (1.0, 2.0) and set(tm.K_POINTS) <= {1.0, 2.0 ** 0.5, 2.0}


# Witnesses on the live core and structural courses ----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def witnesses(region):
    return tm.witnesses(region)


def test_witnesses_are_drawn_only_after_nonemptiness_and_supported(witnesses):
    assert witnesses["drawn"] and witnesses["pass"] and witnesses["label"] == "REGION_WITNESS_ONLY"
    for label in tm.WITNESS_RULE:
        w = witnesses[label]
        assert w["d49"] == 1.0 and 0.0 < w["d24"] < 1.0
        for case in (tm.PRIMARY, tm.SECONDARY):
            c = w["cases"][case]
            assert c["supported"] and c["mechanics_off_refused"]
            assert c["hr"] < c["authored"]["hr"]                 # distress never explains all the tachycardia


def test_review_hardening_the_witnesses_stay_inside_the_declared_bands(witnesses):
    # The adversarial review (finding 1): the frozen 'supported' flag does not read these; they are checked here.
    for label in tm.WITNESS_RULE:
        w = witnesses[label]
        assert 0.0 < w["d24"] < 1.0                                        # the authored order is strict
        for case in (tm.PRIMARY, tm.SECONDARY):
            c = w["cases"][case]
            assert tm.I_RR[0] <= c["intrinsic_rr"] <= tm.I_RR[1]
            assert 0.0 < c["mechanics_efficiency"] <= 1.0
        assert w["cases"][tm.PRIMARY]["mechanics_efficiency"] < w["cases"][tm.SECONDARY]["mechanics_efficiency"]


def test_review_hardening_every_carried_k_and_the_mechanics_order(region):
    # The adversarial review (finding 2): the frozen verdict reads only region['nonempty']; these are checked here.
    assert region["every_carried_k"] and region["monotone_in_k"]
    for pt in region["points"].values():
        assert pt["nonempty"] and pt["contiguous_at_probes"]
        assert all(at["asthma"]["mechanics_order_admissible"] for at in pt["at"].values())


def test_49m_high_rr_and_high_paco2_coexist_without_contradiction(witnesses):
    c = witnesses["MID"]["cases"][tm.PRIMARY]
    assert c["rr"] == 30.0 and abs(c["paco2"] - 51.0) < 1e-6 and c["W"] < 1.0
    s = witnesses["MID"]["cases"][tm.SECONDARY]
    assert s["rr"] == 34.0 and abs(s["paco2"] - 31.0) < 1e-6 and s["W"] > 1.0
    assert c["mechanics_efficiency"] < s["mechanics_efficiency"]


def test_the_structural_courses(witnesses):
    found = tm.courses(witnesses)
    assert found["pass"], found


def test_scale_invariance(witnesses, region):
    found = tm.scale_invariance(witnesses, region)
    assert found["pass"] and found["powers_of_two_max_abs_difference"] == 0.0


def test_mechanics_and_distress_are_orthogonal(region, witnesses):
    found = tm.orthogonality(region, witnesses)
    assert found["pass"] and not found["composition_reads_mechanics"]


def test_no_optimization():
    found = tm.no_optimization()
    assert found["pass"] and not found["fit_names"]


def test_the_mechanics_off_witness_is_refused(witnesses):
    w = witnesses["MID"]
    c = w["cases"][tm.PRIMARY]
    with pytest.raises(CoreInvariantError):
        dv.arrival_state(tm.witness_anchors(tm.PRIMARY, c["intrinsic_rr"], c["distress"]),
                         tm.witness_profile(w["k"], w["rho"], w["g_rr"], mechanics=False))


# Cross-family, controls, parameters, non-regression ---------------------------------------------------------------------------

def test_the_cross_family_and_controls(region):
    found = tm.cross_family(region)
    assert found["pass"], found
    for key, row in found.items():
        if key == "pass":
            continue
        assert all(row[c]["compatible"] for c in tm.CROSS_FAMILY)
        assert all(row[c]["distress_zero_admissible"] for c in tm.CONTROLS)
        assert not any(row[c]["forced_overprediction"] for c in tm.ANAPHYLAXIS)
        assert row[tm.ACS_RESIDUAL]["not_closed"]


def test_the_hypoxaemic_sensitivity_is_not_used(region):
    found = tm.hypoxaemic_sensitivity(region)
    assert found["performed"] and found["still_nonempty"] and not found["used_for_the_verdict"]


def test_the_parameters_stay_unset():
    found = tm.parameters()
    assert found["pass"] and not found["new_profile_fields"] and not found["beta_agonist_parameter"]


def test_the_non_regression():
    found = tm.non_regression()
    assert found["pass"], found


# The verdict, the frozen record and the document -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def found():
    return tm.run()


def test_the_verdict(found):
    assert found["verdict"]["verdict"] == tm.READY and found["verdict"]["blocker"] is None


@pytest.mark.parametrize("path, index", [
    (("orthogonality", "pass"), 1), (("cross_family", "pass"), 4), (("parameters", "pass"), 7),
    (("non_regression", "pass"), 8),
])
def test_the_first_failing_criterion_blocks(found, path, index):
    broken = json.loads(json.dumps(found))
    broken[path[0]][path[1]] = False
    verdict = tm.verdict(broken)
    assert verdict["blocker"] == tm.VERDICT_CRITERIA[index] and verdict["verdict"].startswith(tm.NOT_READY)


def test_p2s3_history_is_not_rewritten():
    record = json.loads(sm.RECORD.read_text(encoding="utf-8"))
    assert record["verdict"]["verdict"] == sm.READY        # the frozen record, untouched (documentation debt)
    assert tm.non_regression()["p2s3_record_untouched"]


@pytest.fixture(scope="module")
def record():
    if not tm.RECORD.exists():
        pytest.skip("the P2T-3 record is written by the evaluation run, after the freeze")
    return json.loads(tm.RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, found):
    assert record["freeze_digest"] == FROZEN_DIGEST
    assert record == json.loads(json.dumps(found, sort_keys=True, default=str))


def test_the_document_is_generated_from_the_record(record):
    from clinical_core import asthma_distress_migration_report as report
    text = tm.DOCUMENT.read_text(encoding="utf-8")
    for name, render in report.RENDERERS.items():
        opening, closing = report.MARKERS[name]
        assert text.count(opening) == 1 and text.count(closing) == 1
        assert text.split(opening)[1].split(closing)[0].strip("\n") == render(record).strip("\n")
