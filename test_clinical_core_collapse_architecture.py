"""P2M-2: the minimal common collapse safety layer (shadow candidate, nothing activated or valued).

The candidate (clinical_core/collapse.py): collapse_signal = max(MAP failure, delivery failure), the existing
aux.collapse_burden with repaying kinetics, the terminal transition on persistence AND current non-viability, the
explicit lag, every clinical slot UNSET. The frozen analysis (clinical_core/collapse_architecture.py): C1-C14, the seven
families, the P2M-1 supersession, the carried subset, the upstream non-regression, the verdict and the exit rule.
"""
from __future__ import annotations

import ast
import json
import math

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import gas_exchange_architecture as go
from clinical_core import lung_water_reference as lw
from clinical_core import edema_migration as pe
from clinical_core import respiratory_drive as rd
from clinical_core import embolism_migration as em
from clinical_core import respiratory_mechanics as mc
from clinical_core import asthma_migration as sm
from clinical_core import respiratory_distress as dm
from clinical_core import collapse as cx
from clinical_core import collapse_architecture as cy
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import vascular_tone as vt
from clinical_core.state import CoreInvariantError, UnresolvedBoundary

ROOT = cy.ROOT
SOURCE = ROOT / "clinical_core" / "collapse_architecture.py"
CANDIDATE = ROOT / "clinical_core" / "collapse.py"
#: The P2M-2 freeze: the candidate, the synthetic settings, the probes C1-C14, the families, the supersession, the
#: non-regression, the criteria, the verdict and exit rules and every clinical_core source but the downstream reports,
#: committed before the evaluation run.
FROZEN_DIGEST = "5f96f8603f2ecdcbf585cfac38e8abf4d4aec9ea9c64772d7d0c46da2f2544ae"


#: P2N-2's files, added after P2M-2 closed: this package's view of the tree leaves them out (acs_migration.p2m2_sources:
#: the ACS mapping, family writers and analysis removed, the tuple-only files at their P2M-2 hashes while only their
#: tuples changed; the import scan without the ACS analysis alone, which reads the candidate structurally: the ACS
#: mapping and family writers stay in the scan, so a collapse import there is caught); the record is unchanged.
#: P2O-3 replaced declared lines of derived.py, integration.py, state.py, modules/acs_ischaemia.py and two tuple
#: files, proven byte for byte against the P2O-1 files (lung_water_reference.proved): this package's guards read
#: the P2O-1 files through P2O-1's view of the P2N-2 core (lw.chain, lw.p2o1_sources); the record is unchanged.
#: P2P-1 added files (the edema family, its mapping and analysis) and two tuple entries, proven against the P2O-3
#: files (edema_migration.proved): this package's guards read the tree as P2O-3 left it (pe.chain, pe.p2o3_sources).
#: P2P-2 changed the core (the respiratory-drive composition, inert by default) and two tuple files, proven against
#: the P2P-1 files (respiratory_drive.proved): this package's guards read the tree as P2P-1 left it (rd.chain,
#: rd.p2p1_sources).
#: P2Q-2 added files (the PE family, its mapping and analysis) and two tuple entries, proven against the P2P-2
#: files (embolism_migration.proved): this package's guards read the tree as P2P-2 left it (em.chain,
#: em.p2p2_sources).
#: P2S-2 changed the core (the common respiratory mechanics candidate, off by default) and two tuple files,
#: proven against the P2Q-2 files (respiratory_mechanics.proved): this package's guards read the tree as
#: P2Q-2 left it (mc.chain, mc.p2q2_sources).
#: P2S-3 added files (the asthma family, its mapping and analysis) and two tuple entries, proven against the
#: P2S-2 files (asthma_migration.proved): this package's guards read the tree as P2S-2 left it (sm.chain,
#: sm.p2s2_sources).
#: P2T-1 changed four common files (the respiratory distress input and its two UNSET readers), proven against
#: the P2S-3 files (respiratory_distress.proved): this package's guards read the tree as P2S-3 left it
#: (dm.chain, dm.p2s3_sources).
_LIVE_SOURCES_P2T1 = bf.freeze_sources


def _LIVE_SOURCES_P2S3() -> dict:
    return dm.p2s3_sources(_LIVE_SOURCES_P2T1())


def _LIVE_SOURCES_P2S2() -> dict:
    return sm.p2s2_sources(_LIVE_SOURCES_P2S3())


def _LIVE_SOURCES_P2Q2() -> dict:
    return mc.p2q2_sources(_LIVE_SOURCES_P2S2())


def _LIVE_SOURCES_P2P2() -> dict:
    return em.p2p2_sources(_LIVE_SOURCES_P2Q2())


def _LIVE_SOURCES_P2P1() -> dict:
    return rd.p2p1_sources(_LIVE_SOURCES_P2P2())


def _LIVE_SOURCES_P2O3() -> dict:
    return pe.p2o3_sources(_LIVE_SOURCES_P2P1())


def _LIVE_SOURCES_P2O1() -> dict:
    return lw.p2o1_sources(_LIVE_SOURCES_P2O3())


def _FREEZE_SOURCES() -> dict:
    # P2O-1 inserted its declared, inert names into derived.py and integration.py, proven byte for byte against the
    # P2N-2 files (gas_exchange_architecture.proved): this view starts from the P2N-2 core, P2O-1's analysis left out.
    return go.p2n2_sources(_LIVE_SOURCES_P2O1())


_IMPORTED_BY = cy.imported_by
ACS_ANALYSIS = "clinical_core/acs_migration.py"


def _p2m2_view() -> dict:
    from clinical_core import acs_migration as an
    return an.p2m2_sources(_FREEZE_SOURCES())


def _p2m2_imported_by() -> list:
    # P2O-1's analysis reads the collapse layer only to show it unchanged (delivery only, no SpO2 input).
    # P2Q-2's analysis reads it only to exercise the PE outputs structurally (as ACS's does), never in the core.
    return [path for path in _IMPORTED_BY() if path not in (ACS_ANALYSIS, go.OWN[0], em.OWN[2], sm.OWN[2])]


def _patch(patch) -> None:
    lw.chain(patch)
    pe.chain(patch)
    rd.chain(patch)
    em.chain(patch)
    mc.chain(patch)
    sm.chain(patch)
    dm.chain(patch)
    patch.setattr(bf, "freeze_sources", _p2m2_view)
    patch.setattr(cy, "imported_by", _p2m2_imported_by)


@pytest.fixture(autouse=True)
def _p2m2_tree(monkeypatch):
    _patch(monkeypatch)


@pytest.fixture(scope="module")
def result():
    with pytest.MonkeyPatch.context() as patch:
        _patch(patch)
        return cy.run()


# The frozen package and its closure ----------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert set(cy.OWN) <= set(sources) and cy.REPORT not in sources
    assert cy.REPORT in lactate_slice.DOWNSTREAM_REPORTS
    assert {cy.OWN[1], cy.REPORT} <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    assert cy.OWN[0] not in decision_pack.PACK_DIGEST_EXCLUDED, "the candidate physiology stays in the pack digest"
    assert cy._record(cy.P2M1_RECORD, cy.P2M1_RECORD_SHA)["extreme_subset"]["flagged"] == 17604
    if FROZEN_DIGEST is not None:
        assert cy.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_the_p2m1_tree_is_byte_identical_and_only_the_analysis_reads_the_candidate():
    up = cy.upstream_unchanged()
    assert up["unchanged"] and (up["digest"], up["files"]) == cy.SOURCES_AT_P2M1
    assert up["imported_by"] == ["clinical_core/collapse_architecture.py"]
    mapped = cy.p2m1_sources(bf.freeze_sources())
    assert not set(cy.OWN) & set(mapped)
    for relative, sha in cy.TUPLE_AT_P2M1.items():
        assert mapped[relative] == sha
    original = vt._live
    try:
        vt._live = lambda relative: original(relative) + "\nX = 1\n"
        assert cy.p2m1_sources(bf.freeze_sources())["clinical_core/decision_pack.py"] == \
            bf.freeze_sources()["clinical_core/decision_pack.py"]
    finally:
        vt._live = original
    own = {a.name for n in ast.walk(ast.parse(SOURCE.read_text(encoding="utf-8")))
           if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
    assert not own & {"family_engine", "legacy_adapter", "collapse_audit", "encephalopathy",
                      "encephalopathy_architecture", "consciousness_audit"}


# The candidate, by construction ------------------------------------------------------------------------------------------

SYN = cy.synthetic()


def test_every_clinical_slot_is_unset_by_default_and_nothing_is_approved():
    d = cx.DEFAULT_COLLAPSE
    assert (d.perfusion_mapping, d.burden_tau_min, d.terminal_burden, d.current_nonviability, d.terminal_rhythm) == \
        (None,) * 5
    assert cx.STATUS["approved"] == "none FACULTY_APPROVED"
    assert cx.STATUS["map_mapping"] == cx.UNSET_CLINICAL_MAPPING
    assert cx.STATUS["terminal_rhythm"] == cx.TERMINAL_RHYTHM_PHENOTYPE_UNSET
    assert cx.STATUS["rosc"] == cx.ROSC_NOT_CURRENTLY_MODELED
    assert cx.perfusion_failure(40.0, d) is None
    assert dv.DEFAULT_PROFILE.collapse_output_threshold is None and dv.DEFAULT_PROFILE.collapse_burden_limit is None
    assert set(cy.PARAMETERS.values()) >= {cx.UNSET_CLINICAL_MAPPING, cx.UNSET, cx.TERMINAL_RHYTHM_PHENOTYPE_UNSET,
                                           "NOT_MODELED", cx.SYNTHETIC_ONLY}


@pytest.mark.parametrize("kwargs, message", [
    ({"burden_tau_min": 0.0}, "time constant"),
    ({"burden_tau_min": 30.0, "terminal_burden": 10.0}, "together"),
    ({"terminal_burden": 10.0, "current_nonviability": 0.5}, "kinetics"),
    ({"burden_tau_min": 30.0, "terminal_burden": 10.0, "current_nonviability": 0.0}, "zero signal"),
    ({"burden_tau_min": 30.0, "terminal_burden": 0.9, "current_nonviability": 0.5}, "persistence floor"),
    ({"burden_tau_min": 30.0, "terminal_burden": 30.0, "current_nonviability": 0.5}, "reachable"),
    ({"terminal_rhythm": "vf"}, "terminal rhythm")])
def test_the_profile_refuses_what_would_break_an_invariant(kwargs, message):
    with pytest.raises(CoreInvariantError, match=message):
        cx.CollapseProfile(**kwargs)


def test_the_signal_is_the_maximum_never_the_sum():
    assert cx.signal_value(0.6, 0.5) == 0.6 and cx.signal_value(0.0, 0.0) == 0.0
    for p in (0.0, 0.2, 1.0):
        for d in (0.0, 0.3, 1.0):
            assert cx.signal_value(p, d) == max(p, d) <= 1.0
    with pytest.raises(CoreInvariantError):
        cx.signal_value(1.2, 0.0)
    unset = cx.CollapseSignal(None, 0.4)
    assert not unset.complete and unset.value == 0.4
    assert cx.CollapseSignal(0.6, 0.6).dominant == ("perfusion_failure", "oxygen_delivery_failure")


def test_the_burden_relaxes_toward_signal_times_tau_and_repays():
    tau = cy.SYNTHETIC_TAU
    for burden in (0.0, 3.0, 12.0, 29.0):
        for signal in (0.0, 0.25, 1.0):
            after = cx.burden_after(burden, signal, SYN)
            target = signal * tau
            assert after >= 0.0 and min(burden, target) - 1e-12 <= after <= max(burden, target) + 1e-12
            assert math.isclose(after, target + (burden - target) * math.exp(-1.0 / tau))
    course = cx.burden_course([0.0] * 200, SYN, 9.9)
    assert all(b < a for a, b in zip(course, course[1:])) and course[-1] == pytest.approx(9.9 * math.exp(-200 / tau))
    with pytest.raises(CoreInvariantError, match="UNSET"):
        cx.burden_after(1.0, 0.5, cx.DEFAULT_COLLAPSE)
    with pytest.raises(CoreInvariantError):
        cx.burden_after(-1.0, 0.5, SYN)


def test_historical_burden_alone_never_meets_the_terminal_criterion():
    for burden in (10.0, 20.0, 29.0):
        for current in (0.0, 0.2, 0.49):
            assert not cx.terminal_due(burden, cx.CollapseSignal(current, current), SYN)
        assert cx.terminal_due(burden, cx.CollapseSignal(0.5, 0.0), SYN)
    assert not cx.terminal_due(20.0, cx.CollapseSignal(None, 1.0), SYN), "never on a lower bound"
    assert not cx.terminal_due(20.0, cx.CollapseSignal(1.0, 1.0), cy.synthetic(terminal=False))


def test_an_unset_mapping_holds_the_burden_and_decides_nothing():
    state, anchors, profile = cy._state({"P": 0.1, "collapse_burden": 3.0})
    m = cx.evaluate(state, anchors, profile, cx.CollapseProfile(burden_tau_min=30.0))
    assert m.status == cx.NOT_EVALUATED and m.burden_after == 3.0 and not m.terminal_due and m.perfusion is None


def test_the_shadow_refuses_the_p2e3_rule_and_an_unset_phenotype():
    from dataclasses import replace
    state, anchors, profile = cy._state({"P": 0.1})
    p2e3 = replace(profile, collapse_output_threshold=0.4, collapse_burden_limit=10.0)
    with pytest.raises(CoreInvariantError, match="never active together"):
        cx.shadow_step(state, (), anchors, p2e3, SYN)
    no_phenotype = cx.CollapseProfile(cx.PerfusionMapping(*cy.SYNTHETIC_MAP), 30.0, 10.0, 0.5)
    due = state.evolve(aux=replace(state.aux, collapse_burden=9.9))
    with pytest.raises(UnresolvedBoundary, match=cx.TERMINAL_RHYTHM_PHENOTYPE_UNSET):
        cx.shadow_step(due, (), anchors, profile, no_phenotype)


def test_the_candidate_reads_no_marker_and_names_no_disease():
    scan = cy.candidate_scan()
    assert scan["forbidden_reads"] == [] and scan["forbidden_imports"] == [] and scan["disease_terms"] == []
    assert scan["signal_by_max"] and not scan["signal_adds"] and not scan["sum_calls"]
    assert set(scan["state_writes"]) == {"aux", "collapse_burden", "collapse_terminal_rhythm"}
    tree = ast.parse(CANDIDATE.read_text(encoding="utf-8"))
    identifiers = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} | {
        n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert not identifiers & {"debt_clearance_tau_min", "lactate_clearance_tau_min", "burden_rise_tau",
                              "burden_clear_tau", "acid_clearance_tau_min"}, "no borrowed kinetics"


def test_a_planted_marker_read_is_caught(monkeypatch, tmp_path):
    planted = CANDIDATE.read_text(encoding="utf-8").replace(
        '"deficit_fraction": acute_deficit_signal(state, anchors, core_profile)}',
        '"deficit_fraction": acute_deficit_signal(state, anchors, core_profile) + state.D}')
    path = tmp_path / "collapse.py"
    path.write_text(planted, encoding="utf-8")
    monkeypatch.setattr(cy, "CANDIDATE_SOURCE", path)
    assert "D" in cy.candidate_scan()["forbidden_reads"]


# The evaluation (the frozen run) ---------------------------------------------------------------------------------------------

def test_c1_to_c14_hold(result):
    assert result["structural"] == {f"C{i}": True for i in range(1, 15)}
    s = result["signals"]
    assert s["C4"]["injected_signal"] == 0.6 and s["C4"]["reading"]["signal"] < (
        s["C4"]["reading"]["perfusion"] + s["C4"]["reading"]["delivery"])
    q = result["no_q"]
    assert abs(q["flow_difference"]) > 0.05 and abs(q["signal_difference"]) < 1e-6
    assert q["flow_alone_h2"]["signal"] == 0.0
    assert result["no_spo2"]["spo2_difference"] > 20.0
    assert all(r["same"] for r in result["no_markers"]["rows"].values())
    per = result["persistence"]
    assert per["C8"]["terminal"] is None and per["C8"]["peak"] < cy.SYNTHETIC_TERMINAL
    assert per["C9"]["terminal_minute"] == 14
    assert all(v["terminal"] is None for v in per["C10"]["from"].values()) and per["C10"]["partial_terminal"] is None
    assert per["C11"]["terminal"] is None and abs(per["C11"]["peak_growth_last_cycle"]) < 1e-6
    np_ = result["no_pulse"]
    assert np_["C12"]["map"] is None and np_["C12"]["burden_after"] == 0.0
    assert set(np_["C13"]["fired"].values()) <= {"UnresolvedBoundary", "CoreInvariantError"}
    assert all(r["pulse"] and r["map"] < 5.0 for r in np_["C14"]["rows"].values())


def test_the_event_order_is_an_explicit_lag_without_retrigger(result):
    o = result["event_order"]
    assert o["pass"] and o["transitions"] == 1 and o["terminal_minute"] == 14 and o["reads_start_state"]
    assert o["after_transition"] == {"statuses": [cx.ARREST], "burdens": [0.0], "pulse": False}
    assert o["deferral"]["minute_14"]["deferred"] and o["deferral"]["minute_15"]["applied"] == "pea"
    assert o["scripted_arrest"]["burden_after"] == 0.0
    assert o["stale_burden_normal_physiology"]["transition"] is None


def test_arrival_rosc_and_the_families(result):
    a = result["arrival"]["rows"]
    assert a["reference"]["arrival_signal"] == 0.0 and a["authored_map_70"]["arrival_burden"] == 0.0
    assert a["authored_map_70"]["arrival_signal"] == pytest.approx(result["arrival"]["expected_low_signal"])
    assert result["rosc"]["pass"] and result["rosc"]["status"] == cx.ROSC_NOT_CURRENTLY_MODELED
    g = result["generalization"]
    assert g["pass"] and set(g["checks"]) == set(cy.FAMILIES) and all(g["checks"].values())
    assert g["rows"]["malignant_arrhythmia"]["variants"]["pulseless"]["status"] == cx.ARREST


def test_upstream_is_unchanged_and_the_subset_is_not_classified(result):
    n = result["nonregression"]
    assert n["pass"] and set(n["identical"]) == set(cy.NONREG_ITEMS) and all(n["identical"].values())
    assert n["whole_state_but_burden"] and n["records_identical"] and n["plain_burden"] == 0.0
    e = result["extreme_subset"]
    assert e["flagged"] == 17604 and not e["filtered"] and e["classification"] is None and e["pulse"]
    assert set(result["supersession"]) == set(cy.SUPERSESSION)
    assert all(v["status"] == cy.SUPERSEDED for v in result["supersession"].values())


def test_the_verdict_and_the_exit_rule(result):
    v = result["verdict"]
    assert v["verdict"] == cy.READY and v["failing"] == [] and not v["not_evaluated"]
    r = result["recommendation"]
    assert r["recommendation"] == "MOVE_TO_SECOND_FAMILY_GENERALIZATION_WITH_COLLAPSE_THRESHOLDS_UNSET"
    assert r["numeric_collapse_calibration_required_before_second_family"] is False
    assert result["efficiency"]["gi_trajectories"] == 0 and result["efficiency"]["cartesian_sweep"] is False


def test_the_verdict_rule_and_the_stop(monkeypatch):
    checks = {c: True for c in cy.CRITERIA}
    assert cy.verdict(checks)["verdict"] == cy.READY
    v = cy.verdict(dict(checks, event_order_acyclic=False))
    assert v["verdict"] == f"{cy.NOT_READY} - EVENT_ORDER_ACYCLIC" and v["failing"] == ["event_order_acyclic"]
    assert cy.recommendation(v)["recommendation"] == "STOP_FOR_STRUCTURAL_CORRECTION"
    monkeypatch.setattr(cy, "upstream_unchanged", lambda: {"unchanged": False, "imported_by": []})
    monkeypatch.setattr(cy, "candidate_scan", lambda: pytest.fail("no probe after a STOP"))
    out = cy.run()
    assert out["stopped"].startswith("an upstream file changed") and out["verdict"]["checks"]["upstream_unchanged"] \
        is False


def test_the_scope_adds_and_reads_nothing_it_should_not():
    source = SOURCE.read_text(encoding="utf-8")
    for forbidden in ("import family_engine", "import legacy_adapter", "snapshot(", "clinical_cases", "gi_reference"):
        assert forbidden not in source
    assert "nothing selected, approved or activated" in cy.POLICY and cy.MIGRATION_GATE.startswith(
        "MIGRATION_GATE_CLOSED")
    assert json.loads(json.dumps(cy.design(), default=str))["revision"] == "P2M-2"
    assert cy.SYNTHETIC_RULE.startswith("SYNTHETIC_ONLY")


# The record and the report (generated once, after the frozen evaluation) -----------------------------------------------------

RECORD = ROOT / "docs" / "revision" / "P2M2_collapse_architecture.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2M2_ARQUITECTURA_COLAPSO.md"


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, result):
    assert record["freeze_digest"] == FROZEN_DIGEST and "stopped" not in record
    assert record["design"] == _json(cy.design())
    for key in ("upstream", "candidate_scan", "signals", "no_q", "no_spo2", "no_markers", "persistence", "no_pulse",
                "event_order", "arrival", "rosc", "generalization", "extreme_subset", "nonregression", "supersession",
                "parameters", "structural", "verdict", "recommendation", "decisions", "efficiency"):
        assert record[key] == _json(result[key]), key


def test_the_record_states_the_structural_verdict(record):
    assert record["verdict"]["verdict"] == cy.READY and record["verdict"]["failing"] == []
    assert record["recommendation"]["recommendation"] == \
        "MOVE_TO_SECOND_FAMILY_GENERALIZATION_WITH_COLLAPSE_THRESHOLDS_UNSET"
    assert record["approval"] == "none FACULTY_APPROVED" and record["extreme_subset"]["classification"] is None
    assert record["efficiency"]["gi_trajectories"] == 0


def test_the_document_is_generated_from_the_record(record):
    from clinical_core import collapse_architecture_report as rep
    document = DOCUMENT.read_text(encoding="utf-8")
    for name, render in rep.RENDERERS.items():
        assert rep.apply(document, name, render(record)) == document, name
    assert cy.READY in document and "MOVE_TO_SECOND_FAMILY_GENERALIZATION_WITH_COLLAPSE_THRESHOLDS_UNSET" in document
    for placeholder in ("SUMMARY_TEXT", "LIMITS_TEXT", "REVIEW_TEXT", "FREEZE_COMMIT", "FREEZE_SHORT"):
        assert placeholder not in document


# P2M-2 review findings, pinned as the current behaviour they describe (TD-110; the freeze and the record stay) ------------

def test_review_m1_the_counterfactual_core_minute_fails_loudly_where_the_declared_order_would_not():
    """MEDIUM-1: on a due minute shadow_step first runs the core's minute without the transition; if that counterfactual
    state(t+1) has a pulse and no output (V emptied this minute) it raises, although the declared order (the transition
    applied in the same core minute) gives a valid pulseless state. It fails loudly, never silently; the fix (one core
    minute with the transition, the deferral decided without materializing state(t+1)) needs a refreeze."""
    from dataclasses import replace
    from clinical_core.bands import Drift
    from clinical_core.integration import step
    from clinical_core.modules.rhythm_events import ScriptedRhythmEvent
    state, anchors, profile = cy._state({"P": 0.1, "collapse_burden": 9.95})
    assert cx.evaluate(state, anchors, profile, SYN).terminal_due
    empty = Drift("probe_v", "V", 0, 1, -(dv.arrival_filling(anchors, profile) + state.V) - 50.0)
    with pytest.raises(UnresolvedBoundary, match="effective output reached zero"):
        cx.shadow_step(state, (empty,), anchors, profile, SYN)
    target = dv.terminal_rhythm(state, anchors, replace(profile, collapse_terminal_rhythm="pea"))
    event = ScriptedRhythmEvent(id="probe", at_minute=1, target=target, preventability="not assessed")
    after, _ = step(state, (empty, event), anchors, profile)
    assert not after.R.pulse_present


def test_review_m2_the_burden_write_is_not_in_the_core_record():
    """MEDIUM-2: the layer writes aux.collapse_burden after the core's conservation check; the core record carries no
    AuxiliaryChange for it (the ShadowMinute does), so the core's own conservation check of that minute fails. The
    non-regression's 'records identical' holds partly for that reason. Trace fidelity needs it recorded at integration."""
    from clinical_core.integration import _check_conservation
    from clinical_core.provenance import ProvenanceError
    state, anchors, profile = cy._state({"P": 0.3})
    after, record, shadow = cx.shadow_step(state, (), anchors, profile, SYN)
    assert after.aux.collapse_burden == shadow.collapse.burden_after > 0.0
    assert "collapse_burden" not in {change.quantity for change in record.auxiliary}
    with pytest.raises(ProvenanceError, match="collapse_burden"):
        _check_conservation(state, after, record)


def test_review_m3_markers_change_neither_input_where_delivery_dominates():
    """MEDIUM-3: the frozen C7 compares the signal only, at a perfusion-dominated state, where the maximum would hide a
    leak into the delivery branch. Here, at a delivery-dominated state (Hb 25 %), lactate, D and the acid burden changed
    alone leave both inputs, not only their maximum; and the code scan finds no indirect read (getattr is used only by the
    records' to_dict)."""
    base_state, anchors, profile = cy._state({"hb_share": 0.25})
    base = cy.reading(base_state, anchors, profile)
    assert base["perfusion"] == 0.0 and base["delivery"] > 0.0 and base["dominant"] == ["oxygen_delivery_failure"]
    for spec in cy.ALONE.values():
        row = cy.reading(*cy._state({"hb_share": 0.25, **spec}))
        assert (row["perfusion"], row["delivery"], row["signal"]) == (base["perfusion"], base["delivery"],
                                                                       base["signal"]), spec
    tree = ast.parse(CANDIDATE.read_text(encoding="utf-8"))
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef):
            uses = {getattr(n.func, "id", None) for n in ast.walk(fn) if isinstance(n, ast.Call)}
            if "getattr" in uses or "vars" in uses:
                assert fn.name == "to_dict", fn.name
    assert "to_dict()" not in CANDIDATE.read_text(encoding="utf-8").split("def readings", 1)[1].split("def signal_at")[0]


def test_review_b3_the_persistence_floor_holds_from_zero_burden_only():
    """LOW-3: the floor refuses a limit one minute can reach from 0; from a burden already near the limit one minute can
    meet it, because the persistence is the burden itself."""
    assert cx.first_terminal([1.0], SYN) is None
    assert cx.first_terminal([0.55], SYN, 9.9) == 1


def test_review_b4_the_profile_does_not_check_its_field_types():
    """LOW-4: a tuple in place of a PerfusionMapping is accepted and fails only on use; a terminal criterion with the MAP
    mapping UNSET is accepted and never evaluates (NOT_EVALUATED_UNSET)."""
    loose = cx.CollapseProfile(perfusion_mapping=(90.0, 0.0))
    with pytest.raises(AttributeError):
        cx.perfusion_failure(50.0, loose)
    unmapped = cx.CollapseProfile(None, 30.0, 10.0, 0.5, "pea")
    state, anchors, profile = cy._state({"P": 0.1, "collapse_burden": 20.0})
    m = cx.evaluate(state, anchors, profile, unmapped)
    assert m.status == cx.NOT_EVALUATED and not m.terminal_due
