"""P2T-5: the minimum common hypoventilation -> oxygenation link (shadow only, off by default).

These tests hold the core change (one UNSET profile field, its guards, the standard dissociation relation and its exact
inverse, the model-derived arrival PaCO2 reference, full relative transmission), O1-O11, the family probes, the FiO2
masking, the downstream directions, the parameter state, the non-regression and the proof that every other file is
P2T-3's.
"""
from __future__ import annotations

import json
import math
from dataclasses import replace

import pytest

from clinical_core import asthma_distress_migration as tm
from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import distress_closure as xm
from clinical_core import oxygenation_link as om
from clinical_core import respiratory_drive as rd
from clinical_core import respiratory_mechanics as mc
from clinical_core.state import CoreInvariantError, UnresolvedBoundary

#: The P2T-5 freeze: the core change, the probes, the readiness rule, the proof and every clinical_core source but the
#: downstream reports, committed before the evaluation run.
FROZEN_DIGEST = "3a042f0fabeecff58f97e198fc3d65cb878eeada63d01039c89d0e0564798f2e"


# The frozen package and its proof -------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert all(relative in sources for relative in om.OWN) and om.REPORT not in sources
    assert set(om.TUPLES_ADDED["DOWNSTREAM_REPORTS"]) <= set(lactate_slice.DOWNSTREAM_REPORTS)
    assert set(om.TUPLES_ADDED["PACK_DIGEST_EXCLUDED"]) <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    if FROZEN_DIGEST is not None:
        assert om.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_only_the_core_and_the_two_tuples_changed():
    assert set(om.REVERSAL) == set(om.CORE_AT_P2T3) == {"clinical_core/derived.py", "clinical_core/lactate_slice.py",
                                                        "clinical_core/decision_pack.py"}
    assert all(om.proofs().values())
    common = om.common_untouched()
    assert all(common.values()) and len(common) >= 124
    assert {"clinical_core/integration.py", "clinical_core/state.py", "clinical_core/asthma_distress_migration.py",
            "clinical_core/modules/asthma.py", "clinical_core/gas_exchange_architecture.py"} <= set(common)
    proof = om.upstream_unchanged()
    assert proof["p2t3_freeze_digest"] and proof["p2t3_proof"] and proof["p2t3_record"]


@pytest.mark.parametrize("relative, old, new", [
    ("clinical_core/lactate_slice.py", '"clinical_core/oxygenation_link_report.py")',
     '"clinical_core/oxygenation_link_report.py", "clinical_core/other.py")'),
    ("clinical_core/decision_pack.py", '"clinical_core/oxygenation_link.py"', '"clinical_core/oxygenation_link2.py"'),
    ("clinical_core/derived.py", "return u - 50.0 / u", "return u - 50.0 / u + 0.0"),
    ("clinical_core/derived.py", "spo2 = min(100.0, max(0.0, anchors.spo2 + profile.spo2_per_fio2 * oxygen))",
     "spo2 = min(100.0, max(0.0, anchors.spo2 + 1.0 * profile.spo2_per_fio2 * oxygen))"),
])
def test_the_proof_notices_any_other_change(relative, old, new):
    live = om._live(relative)
    assert live.count(old) == 1 and not om.proved(relative, live.replace(old, new))


def test_the_p2t3_view_reads_the_p2t3_tree():
    with om.p2t3_view():
        assert "ventilated_oxygenation" not in tm._live("clinical_core/derived.py")
        assert "oxygenation_link" not in xm._live("clinical_core/lactate_slice.py")
        assert "respiratory_quotient" not in dv.PARAMETERS
        assert "respiratory_quotient" not in {f.name for f in tm.fields(dv.CoreProfile)}
        assert not set(om.OWN) & set(bf.freeze_sources())
    assert "ventilated_oxygenation" in tm._live("clinical_core/derived.py")
    assert "respiratory_quotient" in dv.PARAMETERS


# The core change ------------------------------------------------------------------------------------------------------------

def test_the_link_is_unset_by_default():
    assert dv.DEFAULT_PROFILE.respiratory_quotient is None and not dv.hypoventilation_link_active(dv.DEFAULT_PROFILE)
    assert dv.PARAMETERS["respiratory_quotient"][0] == dv.PROVISIONAL
    assert dv.PARAMETERS["respiratory_quotient"][1].startswith("UNSET (P2T-5)")


@pytest.mark.parametrize("value", [0.0, -0.8, math.nan, math.inf, True, "0.8"])
def test_a_declared_quotient_is_finite_and_positive(value):
    with pytest.raises(CoreInvariantError):
        om.probe_profile(value)


def test_the_link_needs_the_mechanics_and_refuses_the_hypoxaemic_drive():
    with pytest.raises(CoreInvariantError, match="mechanics"):
        replace(dv.DEFAULT_PROFILE, respiratory_quotient=om.SYNTHETIC_R)
    with pytest.raises(CoreInvariantError, match="HYPOXEMIC_FEEDBACK_LOOP_DEFERRED"):
        replace(rd.hypoxaemic(mc.base_profile(), rd.SYNTHETIC_GAINS[0]), respiratory_quotient=om.SYNTHETIC_R)
    assert om.probe_profile().respiratory_quotient == om.SYNTHETIC_R


def test_the_dissociation_relation_and_its_exact_inverse():
    grid = [0.5, 1.0, 5.0, 20.0, 40.0, 60.0, 100.0, 250.0, 600.0]
    sats = [dv.oxygen_saturation_from_pao2(p) for p in grid]
    assert all(b > a for a, b in zip(sats, sats[1:])) and all(0.0 < s < 100.0 for s in sats)
    for p, s in zip(grid, sats):
        assert dv.pao2_from_oxygen_saturation(s) == pytest.approx(p, rel=1e-9)
    assert dv.oxygen_saturation_from_pao2(0.0) == 0.0 and dv.oxygen_saturation_from_pao2(-3.0) == 0.0
    assert dv.oxygen_saturation_from_pao2(math.inf) == 100.0
    assert dv.pao2_from_oxygen_saturation(100.0) == math.inf and dv.pao2_from_oxygen_saturation(0.0) == 0.0
    assert dv.oxygen_saturation_from_pao2(26.86) == pytest.approx(50.0, abs=0.05)      # P50 of the standard curve


def test_review_hardening_the_retained_g_transmission_was_rightly_rejected():
    """The rejected composition (the alveolar shift multiplied by retained(G)) lets a worse G raise SpO2 when PaCO2 rises
    enough (here from 55 mmHg above arrival, probe patient at room air); the accepted full transmission never does (O5)."""
    p, a = om.probe_profile(), om.probe_anchors()
    gs = [i / 10 for i in range(21)]
    base = [a.spo2 - p.spo2_per_gas_exchange_unit * g for g in gs]

    def rejected(spo2_base, g, d):
        retained = dv.oxygen_response_retained(g, p)
        return dv.oxygen_saturation_from_pao2(dv.pao2_from_oxygen_saturation(spo2_base)
                                              - retained * d / p.respiratory_quotient)

    rises = [(d, gs[i]) for d in (55.0, 60.0, 65.0) for i in range(len(gs) - 1)
             if rejected(base[i + 1], gs[i + 1], d) > rejected(base[i], gs[i], d)]
    accepted = [[om.shift(b, d) for b in base] for d in (10.0, 30.0, 55.0, 60.0, 65.0)]
    assert rises and all(all(y <= x for x, y in zip(r, r[1:])) for r in accepted)


def test_the_arrival_reference_is_the_arrival_respiration_and_arrival_is_exact():
    for e in (1.0, 0.6, 0.35):
        for fio2 in (0.21, 0.3):
            a, p = om.probe_anchors(arrival_mechanics_efficiency=e, fio2=fio2), om.probe_profile()
            s = dv.arrival_state(a, p)
            assert dv.arrival_paco2_reference(a, p) == dv.respiration(s, a, p).paco2
            assert dv.derive(s, a, p).spo2 == dv.derive(s, a, replace(p, respiratory_quotient=None)).spo2


def test_apnoea_is_an_unresolved_boundary_not_a_value():
    a, p = om.probe_anchors(), replace(om.probe_profile(), central_drive_availability=0.0)
    with pytest.raises(UnresolvedBoundary, match="APNOEA_BOUNDARY_UNRESOLVED"):
        dv.derive(dv.arrival_state(a, p), a, p)


# O1-O11 and the family probes -------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def probes():
    return om.probes()


@pytest.mark.parametrize("name", ["O1", "O2", "O3", "O4", "O5", "O6", "O7", "O8", "O9", "O10", "O11", "guards"])
def test_the_probes(probes, name):
    assert probes[name]["pass"], probes[name]


def test_review_hardening_full_monotonicity_grid():
    """Worse G never raises, higher PaCO2 never raises, lower PaCO2 never lowers, more FiO2 never lowers the final SpO2,
    on a grid wider than the frozen probes (states read by the live core)."""
    a, p = om.probe_anchors(), om.probe_profile()
    s0 = dv.arrival_state(a, p)
    factors, gs, fio2s = (0.4, 0.6, 0.8, 1.0, 1.2, 1.6), (0.0, 0.25, 0.5, 1.0, 1.5, 3.0), (0.21, 0.24, 0.28, 0.35, 0.6)
    table = {(f, g, fi): om.spo2(om._with(s0, f, g, fi), a, p) for f in factors for g in gs for fi in fio2s}
    for f in factors:
        for fi in fio2s:
            row = [table[(f, g, fi)] for g in gs]
            assert all(y <= x for x, y in zip(row, row[1:]))
    for g in gs:
        for fi in fio2s:
            col = [table[(f, g, fi)] for f in factors]          # more efficiency = lower PaCO2
            assert all(y >= x for x, y in zip(col, col[1:]))
        for f in factors:
            fr = [table[(f, g, fi)] for fi in fio2s]
            assert all(y >= x for x, y in zip(fr, fr[1:]))


def test_the_opioid_probe():
    found = om.opioid_probe()
    assert found["pass"] and found["label"] == "FIXED_STATE_COMPARATIVE_PROBE", found


def test_the_asthma_probes():
    found = om.asthma_probes()
    assert found["pass"], found


def test_the_pe_probe():
    found = om.pe_probe()
    assert found["pass"], found


def test_the_edema_probe():
    found = om.edema_probe()
    assert found["pass"], found


def test_fio2_masking_and_the_plateau():
    found = om.fio2_masking()
    assert found["pass"], found


def test_the_downstream_directions():
    found = om.downstream()
    assert found["pass"], found


def test_the_parameters_stay_unset():
    found = om.parameters()
    assert found["pass"] and found["new_profile_fields"] == ["respiratory_quotient"], found


def test_the_audit_and_the_curve():
    assert om.audit()["pass"] and om.odc()["pass"] and om.retained_audit()["pass"]


def test_the_non_regression():
    found = om.non_regression()
    assert found["pass"], found


# The verdict, the frozen record and the document -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def found():
    return om.run()


def test_the_readiness(found):
    assert found["readiness"]["verdict"] == om.READY and found["readiness"]["blocker"] is None


@pytest.mark.parametrize("path, index", [
    (("odc", "pass"), 1), (("opioid", "pass"), 4), (("pe", "pass"), 6), (("parameters", "pass"), 9),
    (("non_regression", "pass"), 10),
])
def test_the_first_failing_criterion_blocks(found, path, index):
    broken = json.loads(json.dumps(found))
    broken[path[0]][path[1]] = False
    verdict = om.readiness(broken)
    assert verdict["blocker"] == om.READINESS_CRITERIA[index] and verdict["verdict"].startswith(om.NOT_READY)


@pytest.fixture(scope="module")
def record():
    if not om.RECORD.exists():
        pytest.skip("the P2T-5 record is written by the evaluation run, after the freeze")
    return json.loads(om.RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, found):
    assert record["freeze_digest"] == FROZEN_DIGEST
    assert record == json.loads(json.dumps(found, sort_keys=True, default=str))


def test_the_document_is_generated_from_the_record(record):
    from clinical_core import oxygenation_link_report as report
    text = om.DOCUMENT.read_text(encoding="utf-8")
    for name, render in report.RENDERERS.items():
        opening, closing = report.MARKERS[name]
        assert text.count(opening) == 1 and text.count(closing) == 1
        assert text.split(opening)[1].split(closing)[0].strip("\n") == render(record).strip("\n")
