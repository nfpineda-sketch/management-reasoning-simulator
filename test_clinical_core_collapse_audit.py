"""P2M-1: the structural audit of collapse / arrest safety (shadow only, read-only).

The pulse semantics and their writers and readers; the current mechanisms; the zero-flow physiology; the flow / pressure,
pump / rhythm and oxygen-delivery probes with their threshold-free reading; the persistence and the event order of the
existing P2E-3 rule; ROSC; the carried extreme GI subset; the generalization; the consciousness-trigger audit; the
minimum structure and the verdict; the closure of everything before.
"""
from __future__ import annotations

import ast
import hashlib
import json

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import gas_exchange_architecture as go
from clinical_core import lung_water_reference as lw
from clinical_core import collapse_audit as cm
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import vascular_tone as vt

ROOT = cm.ROOT
SOURCE = ROOT / "clinical_core" / "collapse_audit.py"
#: The P2M-1 freeze: the faculty decisions, the mechanism table, the probes, the persistence and order design, the
#: generalization, the redundancy and minimum structure, the criteria and every clinical_core source but the downstream
#: reports, committed before the evaluation run.
FROZEN_DIGEST = "c4aa95f62273136934b1b7a31bbb7637fa71fdb00638ddc1fd3974eeeecea9f1"
#: P2M-2's layer, added after P2M-1 closed: this package's view of the tree leaves it out (collapse_architecture.
#: p2m1_sources: the candidate and its analysis removed, the tuple-only files at their P2M-1 hashes while only their
#: tuples changed; the audit's core-file scan without the candidate); the record is unchanged.
#: P2O-3 replaced declared lines of derived.py, integration.py, state.py, modules/acs_ischaemia.py and two tuple
#: files, proven byte for byte against the P2O-1 files (lung_water_reference.proved): this package's guards read
#: the P2O-1 files through P2O-1's view of the P2N-2 core (lw.chain, lw.p2o1_sources); the record is unchanged.
_LIVE_SOURCES_P2O3 = bf.freeze_sources


def _LIVE_SOURCES_P2O1() -> dict:
    return lw.p2o1_sources(_LIVE_SOURCES_P2O3())


def _FREEZE_SOURCES() -> dict:
    # P2O-1 inserted its declared, inert names into derived.py and integration.py, proven byte for byte against the
    # P2N-2 files (gas_exchange_architecture.proved): this view starts from the P2N-2 core, P2O-1's analysis left out.
    return go.p2n2_sources(_LIVE_SOURCES_P2O1())


_CORE_FILES = cm.core_files
LATER_MODULES = ("clinical_core/collapse.py", "clinical_core/collapse_architecture.py",
                 "clinical_core/acs_reference.py", "clinical_core/modules/acs_ischaemia.py",
                 "clinical_core/acs_migration.py", "clinical_core/gas_exchange_architecture.py",
                 "clinical_core/lung_water_reference.py")


def _p2m1_view() -> dict:
    from clinical_core import collapse_architecture as cy
    from clinical_core import acs_migration as an
    return cy.p2m1_sources(an.p2m2_sources(_FREEZE_SOURCES()))


def _p2m1_core_files() -> list:
    later = {ROOT / relative for relative in LATER_MODULES}
    # P2O-1: the scans read the two core files as P2N-2 left them (go.p2n2_path, proven).
    return [go.p2n2_path(p) for p in _CORE_FILES() if p not in later]


def _patch(patch) -> None:
    lw.chain(patch)
    patch.setattr(bf, "freeze_sources", _p2m1_view)
    patch.setattr(cm, "core_files", _p2m1_core_files)


@pytest.fixture(autouse=True)
def _p2m1_tree(monkeypatch):
    _patch(monkeypatch)


@pytest.fixture(scope="module")
def result():
    with pytest.MonkeyPatch.context() as patch:
        _patch(patch)
        return cm.run()


# The frozen package and its closure ---------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert set(cm.OWN) <= set(sources) and cm.REPORT not in sources
    assert cm.REPORT in lactate_slice.DOWNSTREAM_REPORTS
    assert {cm.OWN[0], cm.REPORT} <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    assert cm._record(cm.P2L1_RECORD, cm.P2L1_RECORD_SHA)["extreme_acidemia"]["flagged"] == 17604
    assert cm._record(cm.P2K5_RECORD, cm.P2K5_RECORD_SHA)["demands"]["1.1"]["observed"]["extreme_acidemia"][
        "lowest"]["ph"] < 7.0
    if FROZEN_DIGEST is not None:
        assert cm.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_the_p2l2_tree_is_byte_identical_and_nothing_reads_the_audit():
    up = cm.upstream_unchanged()
    assert up["unchanged"] and (up["digest"], up["files"]) == cm.SOURCES_AT_P2L2
    mapped = cm.p2l2_sources(bf.freeze_sources())
    assert not set(cm.OWN) & set(mapped)
    for relative, sha in cm.TUPLE_AT_P2L2.items():
        assert mapped[relative] == sha
    original = vt._live
    try:
        vt._live = lambda relative: original(relative) + "\nX = 1\n"
        assert cm.p2l2_sources(bf.freeze_sources())["clinical_core/decision_pack.py"] == \
            bf.freeze_sources()["clinical_core/decision_pack.py"]
    finally:
        vt._live = original
    for path in (ROOT / "clinical_core").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names} | {
            n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        if "collapse_audit" in names:
            assert path.name == "collapse_audit_report.py", path.name
    own = {a.name for n in ast.walk(ast.parse(SOURCE.read_text(encoding="utf-8")))
           if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
    assert not own & {"family_engine", "legacy_adapter", "consciousness_audit", "encephalopathy",
                      "encephalopathy_architecture"}


# P2M-1-1 / -2 / -3: pulse, mechanisms, zero flow ----------------------------------------------------------------------------

def test_the_pulse_is_rhythm_state_written_only_by_transitions(result):
    scan = result["pulse"]
    assert scan["transitions"] == ["integration.py:421", "modules/rhythm_events.py:52"]
    assert scan["files_scanned"] == 31 and scan["pulse_reads"] and "derived.py:1325" in scan["pulse_reads"]
    assert scan["terminal_since_writes"] == ["integration.py:458"]
    assert cm.PULSE_SEMANTICS["class"].startswith("AUTHORITATIVE_STATE")
    assert set(cm.MECHANISMS) >= {"p2e3_collapse_rule", "zero_output_guard", "no_return_of_pulse",
                                  "resuscitation_rosc", "legacy_engine_arrests"}
    assert {v[2] for v in cm.MECHANISMS.values()} <= set(cm.MECHANISM_CLASSES)
    assert all(result["legacy_quoted"].values()) and len(result["legacy_quoted"]) == 5


def test_zero_flow_is_consistent_and_a_pulse_without_pressure_is_representable(result):
    z = result["zero_flow"]
    assert set(z["impossible_rhythms"].values()) == {"RAISES"}
    assert z["pulse_with_zero_output"] == "STOPS_THE_RUN" and z["acid_burden_30"] == "STOPS_THE_RUN"
    pulseless = z["pulseless"]
    assert not pulseless["pulse"] and pulseless["output_rel"] == 0.0 == pulseless["delivery_rel"]
    assert pulseless["map"] is None and pulseless["spo2"] is None and pulseless["legacy_level"] == 3
    near = z["pulse_with_near_zero_flow"]
    assert near["pulse"] and near["map"] < 5.0 and near["output_rel"] == pytest.approx(0.02)
    one = z["one_minute"]
    assert one["D"][1] > one["D"][0] and one["acid_burden"][1] > one["acid_burden"][0]
    assert one["collapse_burden"] == [0.0, 0.0] and one["T"] == [1.0, 1.0] and one["P"] == [1.0, 1.0]


# P2M-1-4 / -5 / -6 / -7: the probes ----------------------------------------------------------------------------------------

def test_the_probes_read_as_declared_and_the_current_rule_is_blind_to_pressure_and_content(result):
    pr = result["probes"]
    assert pr["all_as_expected"] and pr["groups"]["flow_map"]["distinguishable"]
    assert pr["groups"]["oxygen"]["distinguishable"]
    assert pr["groups"]["flow_map"]["current_rule_blind"] == ["flow_B_flow_kept_low_tone"]
    assert "oxygen_B_content_failure" in pr["groups"]["oxygen"]["current_rule_blind"]
    rows = pr["rows"]
    assert rows["flow_A_low_flow_high_tone"]["reading"]["map"] >= rows["reference"]["reading"]["map"]
    assert rows["flow_B_flow_kept_low_tone"]["reading"]["output_rel"] > 1.0
    assert rows["oxygen_B_content_failure"]["mechanism"] == "METABOLIC_NONVIABILITY_RISK"
    assert rows["pump_B2_pulseless_rhythm"]["mechanism"] == "ARREST"
    pump = pr["groups"]["pump_rhythm"]
    assert pump["rhythm_equals_pump_at_equal_output"] and pump["pump_and_rhythm_failures_share_inputs"]
    assert rows["acid_severe_metabolic"]["positive"] == [] and rows["acid_severe_metabolic"]["reading"]["ph"] < 7.2


def test_the_redundancy_holds_on_the_probes(result):
    assert all(result["redundancy_evidence"].values()) and len(result["redundancy_evidence"]) == 7
    assert cm.REDUNDANCY["A_flow"].startswith("REDUNDANT") and cm.REDUNDANCY["C_pump"].startswith("REDUNDANT")
    assert cm.REDUNDANCY["lactate_D_I_F"].startswith("EXCLUDED") and cm.REDUNDANCY["G_acid_base"].startswith(
        "MODIFIER_NOT_INPUT")


# P2M-1-8 / -9 / -10: persistence, order, ROSC --------------------------------------------------------------------------------

def test_the_existing_burden_persists_and_its_two_gaps_are_shown(result):
    p = result["persistence"]
    assert p["values"] == {"threshold": 0.4, "limit": 10.0, "repayment_tau_min": 30.0}
    assert p["sustained_output_0_1"]["criterion_minute"] == 14 and not p["one_transient_minute"]["arrest"]
    assert p["restored_after_8_min"]["held_after_60"] == p["restored_after_8_min"]["burden_at_8"]
    assert p["restored_after_8_min"]["repaid_after_60"] < 1.0
    assert p["intermittent_1_in_10_for_4h"]["held_criterion_minute"] is not None
    assert p["intermittent_1_in_10_for_4h"]["repaid_criterion_minute"] is None
    assert p["single_minute_limit_0_5"] == {"criterion_minute": 1, "profile_accepts_it": True}
    assert set(p["committed_rules"]) == {"CO1", "CO2"}


def test_the_event_order_is_an_explicit_lag_without_retrigger(result):
    o = result["event_order"]
    assert o["reads_start_state"] and o["derive_on_new_state"] and o["no_retrigger"] and o["frozen_after_arrest"]
    assert o["previous_state_burden"] < 10.0 <= o["burden_when_met"] and o["pulse_lost_minute"] == 14
    assert o["classification"].startswith("EXPLICIT_LAG_REQUIRED")
    r = result["rosc"]
    assert r["status"] == "ROSC_NOT_CURRENTLY_MODELED" and all(r["guards"].values())


# P2M-1-11 / -12 / -13: the extreme subset, generalization, the trigger audit -------------------------------------------------

def test_the_extreme_subset_keeps_a_pulse_and_is_not_filtered(result):
    x = result["extreme_subset"]
    assert x["flagged"] == 17604 and x["filtered"] is False and x["pulse"] is True and x["stability_problem"]
    assert x["map120"][0] < 35.0 < x["map120"][1] < 50.0 and x["lowest"]["ph"] < 6.97
    low, high = x["output_rel_bounds"]
    assert 0.0 < low < high < 1.0 and x["effective_delivery_lowest"] == pytest.approx((1.1 - x["lowest"]["deficit"])
                                                                                     / 2.5)
    assert x["missing_safety_mechanism"].startswith("ACTIVE_COMMON_COLLAPSE_RULE_MISSING")


def test_the_generalization_and_the_trigger_audit(result):
    g = result["generalization"]
    assert g["current"] == "STRUCTURAL_GAP" and g["proposed"] == "COMMON_COLLAPSE_ARCHITECTURE_PLAUSIBLE"
    assert g["current_gap"] == ["anaphylaxis", "distributive_sepsis", "hypoxaemia_respiratory_failure"]
    assert len(g["rows"]) == 7 and all(r["proposed_sees"] for r in g["rows"].values())
    t = result["trigger_audit"]
    assert t["collapse_rule_reads"] == [] and t["integration_block_reads"] == []


# P2M-1-14 / -18: the minimum structure and the verdict ------------------------------------------------------------------------

def test_the_minimum_structure_and_the_verdict(result):
    assert cm.MINIMUM["classification"] == "DERIVED_COLLAPSE_SIGNAL_ONLY_REQUIRED"
    assert cm.MINIMUM["not_added_here"].startswith("nothing")
    v = result["verdict"]
    assert v["verdict"] == cm.READY and set(v["checks"]) == set(cm.CRITERIA) and all(v["checks"].values())
    assert dv.DEFAULT_PROFILE.collapse_output_threshold is None and dv.DEFAULT_PROFILE.collapse_burden_limit is None
    e = result["efficiency"]
    assert e["gi_trajectories"] == 0 and e["cartesian_sweep"] is False and e["trajectory_simulations"] == 1


def test_the_verdict_rule_and_the_stop():
    checks = {c: True for c in cm.CRITERIA}
    assert cm.verdict(checks)["verdict"] == cm.READY
    v = cm.verdict(dict(checks, event_order_safe=False))
    assert v["verdict"] == f"{cm.NOT_READY} - EVENT_ORDER_SAFE" and v["failing"] == ["event_order_safe"]
    assert cm.verdict({c: True for c in cm.CRITERIA[:-1]})["not_evaluated"] == [cm.CRITERIA[-1]]


def test_a_changed_upstream_file_stops_before_any_probe(monkeypatch):
    monkeypatch.setattr(cm, "upstream_unchanged", lambda: {"unchanged": False})
    monkeypatch.setattr(cm, "pulse_scan", lambda: pytest.fail("no probe after a STOP"))
    out = cm.run()
    assert out["stopped"].startswith("an upstream file changed") and out["verdict"]["checks"]["upstream_unchanged"] \
        is False


def test_the_scope_adds_and_reads_nothing_it_should_not():
    source = SOURCE.read_text(encoding="utf-8")
    for forbidden in ("import family_engine", "legacy_adapter", "snapshot(", "clinical_cases"):
        assert forbidden not in source
    assert "nothing selected, approved or activated" in cm.POLICY and cm.MIGRATION_GATE.startswith(
        "MIGRATION_GATE_CLOSED")
    assert "UNSET" not in cm.RANGES["existing_committed_candidates"] and cm.RANGES["unset"]
    assert json.loads(json.dumps(cm.design(), default=str))["revision"] == "P2M-1"
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() != hashlib.sha256(b"").hexdigest()


def test_the_trigger_audit_catches_a_planted_trigger(monkeypatch, tmp_path):
    """P2M-1 review L11: the trigger audit can fail. A planted copy of the integrator's collapse block that reads the
    lactate is caught."""
    source = (ROOT / "clinical_core" / "integration.py").read_text(encoding="utf-8")
    planted = source.replace("    burden = collapse_burden_after_minute(state, anchors, profile)",
                             "    burden = collapse_burden_after_minute(state, anchors, profile) + state.aux.lactate_excess_mmol_l")
    assert planted != source
    root = tmp_path / "clinical_core"
    root.mkdir()
    (root / "integration.py").write_text(planted, encoding="utf-8")
    (root / "derived.py").write_text((ROOT / "clinical_core" / "derived.py").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(cm, "CORE_DIR", root)
    assert "lactate" in cm.trigger_audit()["integration_block_reads"]


# P2M-1 review findings, pinned as the current behaviour they describe (TD-109; the record and verdict stay frozen) --------------

def test_review_h1_a_stale_burden_arrests_a_patient_whose_output_is_normal():
    """HIGH-1: collapse_reached reads the burden and the pulse, never the current severity, so a burden left at the limit
    (a contributor moved the rhythm the minute it was met, or a future return of circulation) arrests a patient with
    normal output the next minute; a repayment tau from the P2F candidates (30 / 60 / 240) does not prevent it."""
    from dataclasses import replace
    from clinical_core.integration import step
    for tau in (None, 30.0, 240.0):
        profile = cm._rule() if tau is None else cm._rule(collapse_repayment_tau_min=tau)
        state, anchors, _ = cm._probe_state({})
        state = state.evolve(aux=replace(state.aux, collapse_burden=10.5))
        assert dv.derive(state, anchors, profile).output_rel == 1.0
        after, _ = step(state, (), anchors, profile)
        assert not after.R.pulse_present and after.R.code.value == "pea", tau


def test_review_h2_flow_can_fail_alone_inside_the_guards():
    """HIGH-2: the probes' 'flow never fails alone' holds for the chosen probes only; inside the guards a low flow with
    MAP kept and no deficit exists (flow redundancy is a physiological premise, for the faculty to confirm)."""
    for spec in ({"P": 0.7, "T": 2.0}, {"P": 0.8, "T": 1.5}):
        r = cm.reading(*cm._probe_state(spec))
        assert r["output_rel"] < 0.7 and r["map"] > 90.0 and r["deficit_fraction"] == 0.0, spec


def test_review_h3_the_pump_guard_keeps_a_pulse_at_a_map_near_zero():
    """HIGH-3: P is held at its guard floor 0.1 (a silent clamp), so the numerical-zero guard is out of reach through the
    pump while a pulse with MAP 9 mmHg (4.5 with an AV block) is reachable for the whole persistence window."""
    from clinical_core.integration import CHANNEL_BOUNDS
    from clinical_core.state import Channel
    assert CHANNEL_BOUNDS[Channel.P][:2] == (0.1, 3.0)
    floor = cm.reading(*cm._probe_state({"P": 0.1}))
    blocked = cm.reading(*cm._probe_state({"P": 0.1, "rhythm": "avb"}))
    assert floor["pulse"] and floor["map"] == pytest.approx(9.0) and blocked["map"] == pytest.approx(4.5)


def test_review_m5_content_and_saturation_failures_of_equal_delivery_read_alike_in_the_deficit():
    """MEDIUM-5: Hb at 75.6 % and SpO2 73.3 give the same delivery and no deficit; the arterial input flags only the
    second: the myocardial-extraction argument applies to oxygen content (CaO2), not to SpO2 alone."""
    anaemia = cm.reading(*cm._probe_state({"hb_share": 0.756}))
    hypoxaemia = cm.reading(*cm._probe_state({"arrival_fio2": 1.0, "fio2": 0.21}))
    assert anaemia["delivery_rel"] == pytest.approx(hypoxaemia["delivery_rel"], abs=1e-3)
    assert anaemia["deficit_fraction"] == 0.0 == hypoxaemia["deficit_fraction"]


# The record and the report (generated once, after the frozen evaluation) -----------------------------------------------------

RECORD = ROOT / "docs" / "revision" / "P2M1_collapse_audit.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2M1_AUDITORIA_COLAPSO.md"


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, result):
    assert record["freeze_digest"] == FROZEN_DIGEST and "stopped" not in record
    assert record["design"] == _json(cm.design())
    for key in ("upstream", "pulse", "legacy_quoted", "zero_flow", "probes", "persistence", "event_order", "rosc",
                "extreme_subset", "generalization", "trigger_audit", "redundancy", "redundancy_evidence", "minimum",
                "ranges", "verdict", "decisions", "efficiency"):
        assert record[key] == _json(result[key]), key


def test_the_record_states_the_structural_verdict(record):
    v = record["verdict"]
    assert v["verdict"] == cm.READY and v["failing"] == [] and not v["not_evaluated"]
    assert record["minimum"]["classification"] == "DERIVED_COLLAPSE_SIGNAL_ONLY_REQUIRED"
    assert record["extreme_subset"]["flagged"] == 17604 and record["extreme_subset"]["filtered"] is False
    assert record["approval"] == "none FACULTY_APPROVED" and record["efficiency"]["gi_trajectories"] == 0


def test_the_document_is_generated_from_the_record(record):
    from clinical_core import collapse_audit_report as rep
    document = DOCUMENT.read_text(encoding="utf-8")
    for name, render in rep.RENDERERS.items():
        assert rep.apply(document, name, render(record)) == document, name
    assert "COLLAPSE_STRUCTURE_READY_FOR_FACULTY_DECISION" in document
    assert "DERIVED_COLLAPSE_SIGNAL_ONLY_REQUIRED" in document
    for placeholder in ("SUMMARY_TEXT", "LIMITS_TEXT", "REVIEW_TEXT", "FREEZE_COMMIT", "FREEZE_SHORT"):
        assert placeholder not in document
