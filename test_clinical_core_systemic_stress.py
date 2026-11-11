"""P2V-1: the minimum common systemic stress architecture (shadow only, inert by default).

These tests hold the auxiliary stress and its writer interface, the one UNSET sympathetic reader and its refusals, the
absence of any respiratory reader, the classification of the existing hypoglycaemia term, S1-S10, the five case
contrasts, the arrival-region methodology (no numeric mapping), the parameter state, the carried P2T-5 and P2U-1 debts,
the default non-regression and the proof that every other common file is P2U-1's.
"""
from __future__ import annotations

import json
import math
from dataclasses import fields, replace

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import opioid_migration as un
from clinical_core import respiratory_distress as dm
from clinical_core import respiratory_mechanics as mc
from clinical_core import systemic_stress as ss
from clinical_core import distributive_tone as dt
from clinical_core import closure_guard as cg
from clinical_core import amendment_2 as a2
from clinical_core import tone_domain as x1
from clinical_core.integration import step
from clinical_core.provenance import DistressChange, ProvenanceError, Source, SourceKind, SystemicStressChange
from clinical_core.state import AUXILIARY_FIELDS, AuxiliaryState, CoreInvariantError, RhythmCode, RhythmState

#: The P2V-1 freeze: the core insertions, the probes, the synthetic values, the readiness rule, the proof and every
#: clinical_core source but the downstream reports, committed before the evaluation run.
FROZEN_DIGEST = "00ce9e64b78d961c6f5e6894f4b4c78d9bacfbadf3b93e95bc6aae26cf804f95"
PROBE_SOURCE = Source(SourceKind.DISEASE_MODULE, "p2v1-test")

#: P2W-1 changed the core (the common vasodilatory burden, 0 by default, read only by the tone target
#: through an UNSET gain) and two tuple files, proven against the P2V-1 files (distributive_tone.proved):
#: these tests read the tree as P2V-1 left it (dt.tree), and this package changes no behaviour with its
#: own reader UNSET.


@pytest.fixture(autouse=True, scope="module")
def _p2v1_tree():
    with pytest.MonkeyPatch.context() as patch:
        x1.chain(patch)
        cg.chain(patch)
        a2.chain(patch)
        dt.tree(patch)
        yield


# The frozen package and its proof -------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert all(relative in sources for relative in ss.OWN) and ss.REPORT not in sources
    assert set(ss.TUPLES_ADDED["DOWNSTREAM_REPORTS"]) <= set(lactate_slice.DOWNSTREAM_REPORTS)
    assert set(ss.TUPLES_ADDED["PACK_DIGEST_EXCLUDED"]) <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    if FROZEN_DIGEST is not None:
        assert ss.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_only_the_declared_insertions_differ_from_p2u1():
    assert set(ss.REVERSAL) == set(ss.CORE_AT_P2U1) == set(ss.CORE_FILES) | {"clinical_core/lactate_slice.py",
                                                                            "clinical_core/decision_pack.py"}
    assert all(ss.proofs().values())
    common = ss.common_untouched()
    assert all(common.values()) and len(common) >= 125
    assert {"clinical_core/opioid_migration.py", "clinical_core/oxygenation_link.py",
            "clinical_core/respiratory_distress.py", "clinical_core/modules/opioid.py"} <= set(common)
    proof = ss.upstream_unchanged()
    assert proof["p2u1_freeze_digest"] and proof["p2u1_proof"] and proof["p2u1_record"]


@pytest.mark.parametrize("relative", sorted(ss.REVERSAL))
def test_each_declared_replacement_occurs_once_and_reverses(relative):
    live = ss._live(relative)
    for new, old in ss.REVERSAL[relative]:
        assert live.count(new) == 1, (relative, new[:60])
    assert ss.proved(relative) and ss.p2u1_text(relative) != live


def test_the_p2u1_tree_reads_the_p2u1_files():
    with ss.p2u1_view():
        text = un._live("clinical_core/derived.py")
    assert "systemic_stress" not in text and "central_availability" in text


# P2V-1-1: the sympathetic path ------------------------------------------------------------------------------------------------

def test_the_audit_reads_the_whole_sympathetic_path():
    a = ss.audit()
    assert a["pass"], a
    assert [t for t in a["target_terms"] if "acute" in t] and [t for t in a["target_terms"] if "state.D" in t]
    assert a["target_terms"][-1] == "return max(0.0, target)"
    assert a["target_terms"][-2].startswith("baroreflex_drive")
    assert "systemic_stress" in a["target_terms"][-3]
    assert a["increment_reads_beta_blockade"]


def test_the_one_new_term_is_the_only_difference_in_the_target():
    a = ss.audit()
    assert len(a["terms_added"]) == 1 and not a["terms_removed"]
    assert set(a["target_terms_before"]) < set(a["target_terms"])


# P2V-1-2 / -3: the representation and the writer -------------------------------------------------------------------------------

def test_the_representation_adds_one_field_one_anchor_and_one_record():
    r = ss.representation()
    assert r["pass"], r
    assert r["added_fields"] == {"CoreProfile": [ss.NEW_PROFILE_FIELD], "AuxiliaryState": [ss.NEW_AUX],
                                "Anchors": [ss.NEW_ANCHOR], "Contribution": [ss.NEW_AUX],
                                "MinuteRecord": [ss.NEW_AUX]}
    assert ss.NEW_AUX in AUXILIARY_FIELDS and "non-respiratory" in AUXILIARY_FIELDS[ss.NEW_AUX]


def test_the_state_domain_is_zero_and_above_with_no_ceiling():
    assert AuxiliaryState().systemic_stress == 0.0
    assert AuxiliaryState(systemic_stress=1e9).systemic_stress == 1e9
    with pytest.raises(CoreInvariantError):
        AuxiliaryState(systemic_stress=-1e-9)
    with pytest.raises(CoreInvariantError):
        AuxiliaryState(systemic_stress=float("nan"))
    assert AuxiliaryState.from_dict(AuxiliaryState(systemic_stress=3.0).to_dict()).systemic_stress == 3.0


def test_the_writer_record_has_the_distress_records_shape_and_its_guards():
    assert [f.name for f in fields(SystemicStressChange)] == [f.name for f in fields(DistressChange)]
    change = SystemicStressChange(2.5, PROBE_SOURCE, 1, "a declared change")
    assert change.to_dict()["type"] == "systemic_stress" and change.amount == 2.5
    assert SystemicStressChange(0, PROBE_SOURCE, 1, "zero").amount == 0.0
    for bad in (float("nan"), float("inf"), True):
        with pytest.raises(ProvenanceError):
            SystemicStressChange(bad, PROBE_SOURCE, 1, "x")
    with pytest.raises(ProvenanceError):
        SystemicStressChange(1.0, "core", 1, "x")


def test_a_change_is_refused_while_the_reader_is_unset_and_below_zero():
    a = ss.probe_anchors()
    off, on = ss.base_profile(), ss.reader(ss.base_profile())
    with pytest.raises(ProvenanceError):
        step(dv.arrival_state(a, off), (ss.SyntheticStress("x", 1.0),), a, off)
    with pytest.raises(ProvenanceError):
        step(dv.arrival_state(a, on), (ss.SyntheticStress("x", -1.0),), a, on)
    state, record = step(dv.arrival_state(a, on), (ss.SyntheticStress("x", 1.0),), a, on)
    assert state.aux.systemic_stress == 1.0 and len(record.systemic_stress) == 1
    assert [c.quantity for c in record.auxiliary if c.quantity == ss.NEW_AUX] == [ss.NEW_AUX]


def test_the_arrival_anchor_needs_the_reader_and_its_domain():
    off, on = ss.base_profile(), ss.reader(ss.base_profile())
    with pytest.raises(CoreInvariantError):
        ss.probe_anchors(arrival_systemic_stress=-1.0)
    with pytest.raises(CoreInvariantError):
        ss.probe_anchors(arrival_systemic_stress=True)
    with pytest.raises(CoreInvariantError):
        dv.arrival_state(ss.probe_anchors(arrival_systemic_stress=1.0), off)
    assert dv.arrival_state(ss.probe_anchors(arrival_systemic_stress=1.0), on).aux.systemic_stress == 1.0
    assert dv.arrival_state(ss.probe_anchors(), off).aux.systemic_stress == 0.0


def test_no_family_module_writes_the_stress_yet():
    assert not ss.representation()["family_writers"]


# P2V-1-4: the reader ----------------------------------------------------------------------------------------------------------

def test_the_reader_is_unset_by_default_everywhere():
    r = ss.reader_audit()
    assert r["pass"], r
    assert r["default_unset"] and all(r["committed_profiles_unset"].values())
    assert dv.DEFAULT_PROFILE.systemic_stress_to_sympathetic_gain is None


@pytest.mark.parametrize("gain", [0.0, -0.1, True, float("nan"), float("inf")])
def test_the_gain_is_a_finite_positive_drive_or_unset(gain):
    with pytest.raises(CoreInvariantError):
        ss.reader(ss.base_profile(), gain)


def test_the_gain_enters_upstream_of_the_saturation_and_the_beta_blockade():
    r = ss.reader_audit()
    assert r["target_rise_is_the_gain"] and r["hr_rise_through_the_increment"]
    assert r["saturated_at_or_below_the_ceiling"] and r["saturation_is_sublinear"]


# P2V-1-5: no respiratory reader ------------------------------------------------------------------------------------------------

def test_nothing_respiratory_reads_the_stress():
    i = ss.respiratory_isolation()
    assert i["pass"], i
    assert not i["respiratory_functions_reading_stress"] and not i["stress_in_the_drive_composition"]
    assert all(i["respiratory_chain_fixed"].values())


def test_changing_the_stress_alone_changes_no_respiratory_rate():
    a, prof = ss.probe_anchors(), ss.reader(ss.base_profile())
    rows = [ss.at_arrival(replace(a, arrival_systemic_stress=s), prof) for s in ss.STRESS_GRID]
    assert len({row["rr"] for row in rows}) == 1 and len({row["paco2"] for row in rows}) == 1
    assert rows[0]["hr"] < rows[-1]["hr"]


# P2V-1-6: the existing hypoglycaemia term --------------------------------------------------------------------------------------

def test_the_hypoglycaemia_term_is_a_change_term_and_is_untouched():
    h = ss.hypoglycaemia_term()
    assert h["pass"], h
    assert h["classification"] == "CHANGE_TERM" and h["unchanged_since_p2u1"]
    assert h["at_arrival_with_glucose_34"] == 0.0 and h["falling_further"] > 0.0
    assert h["arrival_hr_with_glucose_34"] == h["arrival_hr_with_glucose_100"]


# P2V-1-7: the structural probes ------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def probes():
    return ss.structural_probes()


@pytest.mark.parametrize("name", ss.PROBES)
def test_each_structural_probe_holds(probes, name):
    assert probes[name]["pass"], probes[name]


def test_the_default_is_exactly_the_p2u1_core(probes):
    s10 = probes["S10"]
    assert all(s10["exact_reading_p2u1_core"].values()) and all(s10["exact_arrival_p2u1_core"].values())
    assert all(s10["committed_arrival_stress_zero"].values())
    assert len(s10["exact_reading_p2u1_core"]) >= 9


def test_declaring_the_reader_with_no_stress_changes_nothing(probes):
    assert all(probes["S1"]["identical_with_the_reader_declared"].values())
    assert all(probes["S1"]["stress_zero"].values())


def test_the_beta_blockade_attenuates_and_suppresses(probes):
    rows = probes["S6"]["rows"]
    assert rows["0.0"]["hr_rise"] > rows["0.5"]["hr_rise"] > 0.0 and rows["1.0"]["hr_rise"] == 0.0
    assert all(row["through_increment"] for row in rows.values())
    assert probes["S6"]["target_rise_is_beta_independent"]


def test_the_two_signals_compose_without_merging(probes):
    s4, s9 = probes["S4"], probes["S9"]
    assert s4["stress_course_distress"] == [0.0] and s4["distress_course_stress"] == [0.0]
    assert s4["records_are_separate"] and s4["each_guard_refuses_the_others_anchor"]
    assert s9["additive"] and s9["stress_never_moves_the_rr"] and s9["distress_also_moves_the_rr"]


def test_the_other_sympathetic_terms_stay_addressable(probes):
    s8 = probes["S8"]
    assert all(s8["each_term_addressable"].values()) and s8["stress_rise_is_always_its_own"]
    assert s8["arrival_hypoxaemia_is_relative"]


def test_a_stress_change_moves_only_its_own_effectors(probes):
    s5 = probes["S5"]
    assert set(s5["arrival_moved"]) <= set(ss.STRESS_CONSEQUENCES)
    assert set(s5["course_moved"]) <= set(ss.STRESS_CONSEQUENCES)
    assert all(s5["never_moved_at_arrival"].values()) and all(s5["never_moved_in_the_course"].values())


# P2V-1-8 to -12: the case contrasts --------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def contrasts():
    return ss.contrasts()


def test_the_contrasts_hold(contrasts):
    assert contrasts["pass"], {k: v.get("pass") for k, v in contrasts.items() if isinstance(v, dict)}


def test_hypoglycaemia_forces_a_gap_no_common_term_explains(contrasts):
    h = contrasts["hypoglycemia_28m"]
    assert h["forced_bpm"] >= 12.0 and h["shock_terms"]["target"] == 0.0
    assert h["arrival_stress"] == "UNSET" and h["status"] == "FAMILY_CANDIDATE / REGION UNSET"


def test_the_acs_residual_is_not_closed_by_the_respiratory_distress(contrasts):
    a = contrasts["acs_70f_left_main"]
    assert a["residual_bpm"] > 0.0 and a["unchanged_with_the_reader_declared"]
    assert a["closing_with_distress"]["rr"] > a["authored_rr"] and a["distress_cost_on_the_rr"] > 0.0
    assert a["arrival_stress"] == "UNSET"


def test_pain_forces_no_stress(contrasts):
    r = contrasts["renal_colic_34m"]
    assert r["forced_bpm"] <= 0.0 and r["zero_stress_is_compatible"]
    assert r["status"] == "COMPATIBILITY / POSSIBLE WRITER" and r["arrival_stress"] == "UNSET"


def test_the_pneumonias_are_not_separated_numerically(contrasts):
    for row in contrasts["pneumonia"]["cases"].values():
        assert row["status"] == "NOT_SEPARABLE / STRUCTURAL_ONLY" and row["arrival_stress"] == "UNSET"
        assert row["separation"].startswith("NOT_ATTEMPTED") and len(row["candidate_contributors"]) >= 3


def test_the_beta_blocked_anaphylaxis_is_the_guard(contrasts):
    an = contrasts["anaphylaxis_63m_betablocked"]
    assert an["af_rate_is_the_rhythms"] and an["full_blockade_suppresses"] and an["partial_blockade_attenuates"]
    assert an["target_still_rises_under_blockade"] and an["arrival_stress"] == "UNSET"
    assert "anaphylaxis family writer" in an["not_implemented"]


# P2V-1-13 to -15: the methodology and the parameter state ----------------------------------------------------------------------

def test_the_arrival_methodology_has_no_lookup_table():
    m = ss.arrival_methodology()
    assert m["pass"], m
    assert not any(m["mappings_approved"].values())
    assert set(m["stress_literals"]) <= set(ss.ALLOWED_STRESS_LITERALS)
    assert m["every_case_unset"] and m["authored_rows_carry_no_stress"]
    assert "GLUCOSE_CAN_ANCHOR_FAMILY_STRESS_REGION" in m["anchor_status"]["glucose"]
    assert "GLUCOSE_TO_STRESS_MAPPING_APPROVED = False" in m["anchor_status"]["glucose"]
    assert "TEMPERATURE_CAN_CONSTRAIN_FAMILY_STRESS_REGION" in m["anchor_status"]["temperature"]
    assert m["anchor_status"]["hr_residual"].startswith("NEVER_AN_ANCHOR")


def test_every_magnitude_is_unset():
    p = ss.parameters()
    assert p["pass"], p
    assert all(v is None for v in p["committed_gains"].values())
    assert all(v == 0.0 for v in p["committed_arrival"].values())
    assert p["candidate_input_outside_case_parameters"] and p["registry_state"] == "provisional"
    assert all("UNSET" in note or "not approved" in note for note in p["unset"].values())


def test_the_authored_truth_is_transcribed_without_a_stress_value():
    for case, row in ss.AUTHORED.items():
        assert {"hr", "rhythm", "sbp", "dbp", "spo2", "rr", "glucose", "temperature_c"} <= set(row)
        assert ss.NEW_AUX not in row and case in ss.INDEPENDENT_EVIDENCE and case in ss.CONTRAST_STATUS
        assert not any("hr" == item for item in ss.INDEPENDENT_EVIDENCE[case])


# P2V-1-16 to -18: the non-regression and the carried debts ---------------------------------------------------------------------

def test_the_carried_debts_are_carried_not_resolved():
    d = ss.carried_debts()
    assert d["pass"], d
    assert d["debts"]["HYPOXEMIC_FEEDBACK_STABILITY_AUDIT_DEFERRED"]["status"].startswith("DEFERRED")
    assert d["debts"]["P2T5_LATENT_PAO2_PHYSICAL_FLOOR"]["status"] == "NOT_REQUIRED_BY_P2V1"
    assert d["debts"]["STEADY_STATE_W_ARRIVAL_TENSION"]["status"] == "ACCEPTED_MODELING_DEBT / NOT_A_PHASE2_BLOCKER"
    assert d["debts"]["OPIOID_HR_FAMILY_GAP"]["status"] == "CARRIED, NOT PATCHED"
    assert all(not row["stress_writer"] and not row["opioid_hr_term"] for row in d["opioid_hr_gap"].values())
    assert d["opioid_hr_gap"]["opioid_67f"]["gap_bpm"] < 0.0


def test_the_p2u1_record_is_reproduced_on_its_tree():
    n = ss.non_regression()
    assert n["pass"], n
    assert n["p2u1_record_reproduced_on_its_tree"] and n["p2u1_record_untouched"]
    assert n["p2u1_verdict"] == un.READY


def test_the_committed_courses_never_move_the_stress():
    for name, (states, _, _) in ss.reference_courses().items():
        assert {s.aux.systemic_stress for s in states} == {0.0}, name


# The verdict, the frozen record and the document -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def found():
    return ss.run()


def test_the_readiness(found):
    assert found["readiness"]["verdict"] == ss.READY and found["readiness"]["blocker"] is None


@pytest.mark.parametrize("path, index", [
    (("representation", "pass"), 0), (("isolation", "pass"), 1), (("contrasts", "pass"), 6),
    (("non_regression", "pass"), 7),
])
def test_the_first_failing_criterion_blocks(found, path, index):
    broken = json.loads(json.dumps(found))
    broken[path[0]][path[1]] = False
    verdict = ss.readiness(broken)
    assert verdict["blocker"] == ss.READINESS_CRITERIA[index] and verdict["verdict"].startswith(ss.NOT_READY)


@pytest.fixture(scope="module")
def record():
    if not ss.RECORD.exists():
        pytest.skip("the P2V-1 record is written by the evaluation run, after the freeze")
    return json.loads(ss.RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, found):
    assert record["freeze_digest"] == FROZEN_DIGEST
    assert record == json.loads(json.dumps(found, sort_keys=True, default=str))


def test_the_document_is_generated_from_the_record(record):
    if not ss.DOCUMENT.exists():
        pytest.skip("the P2V-1 document is written by the evaluation run, after the freeze")
    from clinical_core import systemic_stress_report as report
    text = ss.DOCUMENT.read_text(encoding="utf-8")
    for name, (opening, closing) in report.MARKERS.items():
        assert opening in text and closing in text, name
        block = report.RENDERERS[name](record)
        assert block.strip() in text, name


# The adversarial review's independent checks (R-F1 to R-F9) --------------------------------------------------------------------
# The frozen analysis module and its record are not re-cut: these are the independent checks the review asked for, in the
# tests, as P2U-1 did with its own review (TD-124, point 9). Each one names the finding it covers.

def test_the_readiness_rule_reads_only_these_sections_and_the_rest_are_asserted_here():
    """R-F1: the published verdict does not consult the sympathetic-path audit, S5 or the carried debts. That is pinned
    here, so the gap cannot grow silently, and those three sections are asserted on their own above."""
    found = ss.run()
    gating = set()
    for key in ("representation", "reader", "isolation", "hypoglycaemia", "contrasts", "arrival_methodology",
                "parameters", "non_regression", "audit", "carried_debts"):
        broken = json.loads(json.dumps(found))
        broken[key]["pass"] = False
        if ss.readiness(broken)["blocker"] is not None:
            gating.add(key)
    probes_gating = set()
    for name in ss.PROBES:
        broken = json.loads(json.dumps(found))
        broken["probes"][name]["pass"] = False
        if ss.readiness(broken)["blocker"] is not None:
            probes_gating.add(name)
    assert gating == {"representation", "reader", "isolation", "hypoglycaemia", "contrasts", "arrival_methodology",
                      "parameters", "non_regression"}
    assert probes_gating == {"S1", "S2", "S3", "S4", "S6", "S7", "S8", "S9", "S10"}
    # The three the rule never reads: asserted separately, here.
    assert ss.audit()["pass"] and ss.carried_debts()["pass"] and ss.structural_probes()["S5"]["pass"]


@pytest.mark.parametrize("path, index", [
    (("representation", "pass"), 0), (("isolation", "pass"), 1), (("probes", "S4", "pass"), 2),
    (("probes", "S2", "pass"), 3), (("hypoglycaemia", "pass"), 4), (("parameters", "pass"), 5),
    (("contrasts", "pass"), 6), (("non_regression", "pass"), 7),
])
def test_every_criterion_blocks_when_its_own_evidence_fails(found, path, index):
    """R-F9: all eight criteria, not four."""
    broken = json.loads(json.dumps(found))
    node = broken
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = False
    verdict = ss.readiness(broken)
    assert verdict["blocker"] == ss.READINESS_CRITERIA[index] and verdict["verdict"].startswith(ss.NOT_READY)


#: R-F2: every expression this package ever writes into the stress or its arrival anchor, and every dict it unpacks into
#: a call, read from both of its files. The module's own guard sees literal keywords only, so a named constant, a lookup
#: table or a formula would be invisible to it; this pins the expressions themselves, so any new one fails the test.
STRESS_WRITES = {
    "clinical_core/systemic_stress.py": (
        {"(DistressChange(1.0, self.source, minute, 'wrong record type'),)",
         "(SystemicStressChange(self.amount, self.source, minute, 'probe: declared change of the systemic stress'),)",
         "-0.1", "-1.0", "1.0", "10000.0", "1000000.0", "PROBE_STRESS", "True", "float('inf')", "float('nan')", "s"},
        {"changes", "intrinsic", "{field: value}", "{n: getattr(profile, n) for n in names}"}),
    "clinical_core/systemic_stress_report.py": (set(), set()),
}


def _stress_writes(relative: str):
    tree = __import__("ast").parse((ss.ROOT / relative).read_text(encoding="utf-8"))
    import ast as _ast
    direct = {_ast.unparse(k.value) for n in _ast.walk(tree) if isinstance(n, _ast.Call)
              for k in n.keywords if k.arg in (ss.NEW_AUX, ss.NEW_ANCHOR)}
    unpacked = {_ast.unparse(k.value) for n in _ast.walk(tree) if isinstance(n, _ast.Call)
                for k in n.keywords if k.arg is None}
    return direct, unpacked


@pytest.mark.parametrize("relative", sorted(STRESS_WRITES))
def test_no_expression_writes_the_stress_but_the_declared_ones(relative):
    """R-F2: the stronger scan the module's literal guard cannot do. `s` ranges over STRESS_GRID and PROBE_STRESS /
    STRESS_STEP are the declared synthetic values; nothing here reads an observable."""
    assert _stress_writes(relative) == STRESS_WRITES[relative]
    assert {"PROBE_STRESS", "STRESS_GRID", "STRESS_STEP"} == {"PROBE_STRESS", "STRESS_GRID", "STRESS_STEP"}
    assert ss.PROBE_STRESS == 5.0 and ss.STRESS_GRID == (0.0, 2.5, 5.0, 10.0) and ss.STRESS_STEP == 1.0


def test_every_contrast_probe_really_carries_a_zero_arrival_stress():
    """R-F3: the contrasts report the string UNSET; this reads the anchors they actually build."""
    for case in ss.AUTHORED:
        assert getattr(ss._authored_anchors(case), ss.NEW_ANCHOR) == 0.0, case
    from clinical_core import acs_reference as ar
    assert getattr(ar.anchors(), ss.NEW_ANCHOR) == 0.0
    assert all(getattr(a, ss.NEW_ANCHOR) == 0.0 for a, _ in ss.committed_pairs().values())


#: R-F4: the model's own arrival HR at the most favourable intrinsic rate the common band admits (the band's top, at
#: most the authored HR), with no stress and no reader: what the architecture can reach before anything is added.
BAND_TOP_MODEL = {"hypoglycemia_28m": (100.0, 12.0), "renal_colic_34m": (94.0, 0.0), "pneumonia_46f": (100.0, 18.0),
                  "pneumonia_83m": (100.0, 8.0)}


@pytest.mark.parametrize("case", sorted(BAND_TOP_MODEL))
def test_the_reported_gap_is_what_the_model_leaves_at_the_best_admissible_intrinsic_rate(case):
    """R-F4: the published forced_bpm / gap_bpm is arithmetic over the intrinsic band's constants. This evaluates the
    model at the band's top and checks the same number, so the claim is model-dependent: 112 cannot be reached at all
    (12 bpm unexplained at best), 94 is reached exactly (nothing forced)."""
    top, expected = BAND_TOP_MODEL[case]
    authored = ss.AUTHORED[case]
    anchors = ss.probe_anchors(hr=authored["hr"], rhythm=RhythmState(RhythmCode.SINUS, authored["hr"], 1.0, True),
                               intrinsic_sinus_rate=top, glucose=authored["glucose"], spo2=authored["spo2"],
                               crt_s=authored["crt_s"])
    row = ss.at_arrival(anchors, ss.base_profile())
    assert math.isclose(row["hr"], top, abs_tol=1e-9), (case, row["hr"])
    assert math.isclose(authored["hr"] - row["hr"], expected, abs_tol=1e-9)
    assert row["stress"] == 0.0 and row["sympathetic_target"] == 0.0
    # And the probe the contrast itself uses (intrinsic 80, the band's midpoint) leaves at least as much unexplained.
    assert ss.AUTHORED[case]["hr"] - ss.at_arrival(ss._authored_anchors(case), ss.base_profile())["hr"] >= expected


def test_no_module_outside_the_core_and_this_package_names_the_stress_writer():
    """R-F5: the module's family-writer guard globs clinical_core/modules only; contributors live elsewhere too."""
    # Who actually builds the record (a call), not who names the type: the core declares and collects it, this package
    # writes it in its own probe, and a newer package quotes the core's lines inside its reversal hunks.
    allowed = {"clinical_core/systemic_stress.py", "test_clinical_core_systemic_stress.py"}
    found, mentions = set(), set()
    for path in sorted(ss.ROOT.rglob("*.py")):
        relative = path.relative_to(ss.ROOT).as_posix()
        if relative.startswith("validation/") or "__pycache__" in relative:
            continue
        text = path.read_text(encoding="utf-8")
        if "SystemicStressChange(" in text:
            found.add(relative)
        if "SystemicStressChange" in text:
            mentions.add(relative)
    assert found == allowed, found - allowed
    assert not [m for m in mentions if m.startswith("clinical_core/modules/")]


def test_the_hypoglycaemia_term_itself_is_negative_on_recovery():
    """R-F8: the module reads the floored target, where a recovery and a 0 term look alike. This reads the term."""
    profile = ss.base_profile()
    threshold = profile.hypoglycaemia_threshold_mg_dl

    def term(arrival_glucose, glucose):
        return max(0.0, threshold - glucose) - max(0.0, threshold - arrival_glucose)

    assert term(ss.LOW_GLUCOSE, ss.LOW_GLUCOSE) == 0.0
    assert term(ss.LOW_GLUCOSE, ss.LOW_GLUCOSE - 10.0) > 0.0
    assert term(ss.LOW_GLUCOSE, ss.RECOVERED_GLUCOSE) < 0.0
    # The floor is what makes the recovery read as 0 in the target, and the floor is P2D-3's, not this package's.
    a = ss.probe_anchors(glucose=ss.LOW_GLUCOSE)
    state = dv.arrival_state(a, profile).evolve(glucose=ss.RECOVERED_GLUCOSE)
    assert dv.sympathetic_target(state, a, profile) == 0.0
