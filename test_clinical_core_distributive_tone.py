"""P2W-1: the minimum common distributive-tone composition (shadow only, inert by default).

These tests hold the auxiliary vasodilatory burden and its writer interface, the one UNSET reader of the common tone
target, the core's exclusive ownership of the T channel (P2J-2's guard intact), V1-V14, the distributive signature
against the authored truth, the parameter state, the carried debts, the default non-regression and the proof that
every other common file is P2V-1's.
"""
from __future__ import annotations

import json
import math
from dataclasses import fields, replace

import pytest

from clinical_core import acs_reference as ar
from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import distributive_tone as dt
from clinical_core import respiratory_distress as dm
from clinical_core import systemic_stress as ss
from clinical_core.integration import CHANNEL_BOUNDS, step
from clinical_core.provenance import DistressChange, ProvenanceError, Source, SourceKind, VasodilationChange
from clinical_core.state import AUXILIARY_FIELDS, AuxiliaryState, Channel, CoreInvariantError

#: The P2W-1 freeze: the core insertions, the probes, the synthetic values, the readiness rule, the proof and every
#: clinical_core source but the downstream reports, committed before the evaluation run.
FROZEN_DIGEST = "345deb5db60c0638b7b1e1d9a4eb1d1b5f6b82a232b24e084688e2db64174fed"
PROBE_SOURCE = Source(SourceKind.DISEASE_MODULE, "p2w1-test")


# The frozen package and its proof -------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert all(relative in sources for relative in dt.OWN) and dt.REPORT not in sources
    assert set(dt.TUPLES_ADDED["DOWNSTREAM_REPORTS"]) <= set(lactate_slice.DOWNSTREAM_REPORTS)
    assert set(dt.TUPLES_ADDED["PACK_DIGEST_EXCLUDED"]) <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    if FROZEN_DIGEST is not None:
        assert dt.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_only_the_declared_insertions_differ_from_p2v1():
    assert set(dt.REVERSAL) == set(dt.CORE_AT_P2V1) == set(dt.CORE_FILES) | {"clinical_core/lactate_slice.py",
                                                                             "clinical_core/decision_pack.py"}
    assert all(dt.proofs().values())
    common = dt.common_untouched()
    assert all(common.values()) and len(common) >= 127
    assert {"clinical_core/systemic_stress.py", "clinical_core/vascular_tone.py", "clinical_core/pressure_tone.py",
            "clinical_core/collapse_architecture.py"} <= set(common)
    proof = dt.upstream_unchanged()
    assert proof["p2v1_freeze_digest"] and proof["p2v1_proof"] and proof["p2v1_record"]


@pytest.mark.parametrize("relative", sorted(dt.REVERSAL))
def test_each_declared_replacement_occurs_once_and_reverses(relative):
    live = dt._live(relative)
    for new, old in dt.REVERSAL[relative]:
        assert live.count(new) == 1, (relative, new[:60])
    assert dt.proved(relative) and dt.p2v1_text(relative) != live


def test_the_p2v1_tree_reads_the_p2v1_files():
    with dt.p2v1_view():
        text = ss._live("clinical_core/derived.py")
    assert "vasodilatory_burden" not in text and "systemic_stress" in text


# The architecture: who owns and who reads T --------------------------------------------------------------------------------

def test_the_core_stays_the_only_writer_of_the_tone_channel():
    a = dt.audit()
    assert a["pass"], a
    assert a["t_writers"] == ["_vascular_tone"] and a["t_readers"] == ["_perfusion"]
    assert a["guard_unchanged"]
    assert a["burden_readers"] == ["tone_target"]
    assert "tone_target" not in a["beta_blockade_readers"] and "_perfusion" not in a["beta_blockade_readers"]


def test_a_family_delta_on_the_tone_channel_is_still_refused():
    a, prof = ar.anchors(), dt.reader(dt.acs_profile())
    with pytest.raises(CoreInvariantError):
        step(dv.arrival_state(a, prof), (dt._FamilyTone("t"),), a, prof)


def test_the_composition_is_the_compensatory_ratio_times_the_dilation_factor():
    a, prof = ar.anchors(), dt.reader(dt.acs_profile())
    state = dv.arrival_state(a, prof)
    for burden in dt.BURDEN_GRID:
        held = state.evolve(aux=replace(state.aux, vasodilatory_burden=burden))
        expected = (dv.tone_target(state, a, dt.acs_profile())
                    * (1.0 + dt.TONE_GAIN * a.arrival_vasodilatory_burden)
                    / (1.0 + dt.TONE_GAIN * burden))
        assert math.isclose(dv.tone_target(held, a, prof), expected, rel_tol=0.0, abs_tol=1e-12), burden


# The representation and the writer ------------------------------------------------------------------------------------------

def test_the_representation_adds_one_field_one_anchor_and_one_record():
    r = dt.representation()
    assert r["pass"], r
    assert r["added_fields"] == {"CoreProfile": [dt.NEW_PROFILE_FIELD], "AuxiliaryState": [dt.NEW_AUX],
                                "Anchors": [dt.NEW_ANCHOR], "Contribution": ["vasodilation"],
                                "MinuteRecord": ["vasodilation"]}
    assert dt.NEW_AUX in AUXILIARY_FIELDS and "primary loss of vascular tone" in AUXILIARY_FIELDS[dt.NEW_AUX]


def test_the_state_domain_is_zero_and_above_with_no_ceiling():
    assert AuxiliaryState().vasodilatory_burden == 0.0
    assert AuxiliaryState(vasodilatory_burden=1e9).vasodilatory_burden == 1e9
    for bad in (-1e-9, float("nan"), float("inf")):
        with pytest.raises(CoreInvariantError):
            AuxiliaryState(vasodilatory_burden=bad)
    assert AuxiliaryState.from_dict(AuxiliaryState(vasodilatory_burden=2.0).to_dict()).vasodilatory_burden == 2.0


def test_the_writer_record_has_the_distress_records_shape_and_its_guards():
    assert [f.name for f in fields(VasodilationChange)] == [f.name for f in fields(DistressChange)]
    change = VasodilationChange(0.25, PROBE_SOURCE, 1, "a declared dilation")
    assert change.to_dict()["type"] == "vasodilation" and change.amount == 0.25
    for bad in (float("nan"), float("inf"), True):
        with pytest.raises(ProvenanceError):
            VasodilationChange(bad, PROBE_SOURCE, 1, "x")
    with pytest.raises(ProvenanceError):
        VasodilationChange(1.0, "core", 1, "x")


def test_a_change_is_refused_while_the_reader_is_unset_and_below_zero():
    a = ar.anchors()
    off, on = dt.acs_profile(), dt.reader(dt.acs_profile())
    with pytest.raises(ProvenanceError):
        step(dv.arrival_state(a, off), (dt.SyntheticVasodilation("x", 0.5),), a, off)
    with pytest.raises(ProvenanceError):
        step(dv.arrival_state(a, on), (dt.SyntheticVasodilation("x", -1.0),), a, on)
    state, record = step(dv.arrival_state(a, on), (dt.SyntheticVasodilation("x", 0.5),), a, on)
    assert state.aux.vasodilatory_burden == 0.5 and len(record.vasodilation) == 1
    assert [c.quantity for c in record.auxiliary if c.quantity == dt.NEW_AUX] == [dt.NEW_AUX]


def test_the_arrival_anchor_needs_the_reader_and_its_domain():
    off, on = dt.base_profile(), dt.reader(dt.base_profile())
    for bad in (-1.0, True, float("inf")):
        with pytest.raises(CoreInvariantError):
            dt.probe_anchors(arrival_vasodilatory_burden=bad)
    with pytest.raises(CoreInvariantError):
        dv.arrival_state(dt.probe_anchors(arrival_vasodilatory_burden=1.0), off)
    assert dv.arrival_state(dt.probe_anchors(arrival_vasodilatory_burden=1.0), on).aux.vasodilatory_burden == 1.0
    assert dv.arrival_state(dt.probe_anchors(), off).aux.vasodilatory_burden == 0.0


def test_no_family_module_writes_the_burden_yet():
    assert not dt.representation()["family_writers"]


# The reader ------------------------------------------------------------------------------------------------------------------

def test_the_reader_is_unset_by_default_everywhere():
    r = dt.reader_audit()
    assert r["pass"], r
    assert dv.DEFAULT_PROFILE.vasodilatory_burden_to_tone_gain is None
    assert all(r["committed_profiles_unset"].values())


@pytest.mark.parametrize("gain", [0.0, -0.1, True, float("nan"), float("inf")])
def test_the_gain_is_a_finite_positive_tone_loss_or_unset(gain):
    with pytest.raises(CoreInvariantError):
        dt.reader(dt.acs_profile(), gain)


# The structural probes -------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def probes():
    return dt.structural_probes()


@pytest.mark.parametrize("name", dt.PROBES)
def test_each_structural_probe_holds(probes, name):
    assert probes[name]["pass"], probes[name]


def test_the_default_is_exactly_the_p2v1_core(probes):
    v1 = probes["V1"]
    assert all(v1["exact_reading_p2v1_core"].values()) and all(v1["burden_zero"].values())
    assert all(v1["identical_with_the_reader_declared"].values())
    assert v1["change_refused_with_the_reader_unset"]
    assert len(v1["exact_reading_p2v1_core"]) >= 9


def test_more_burden_lowers_the_tone_and_more_compensation_raises_it(probes):
    v2, v3 = probes["V2"], probes["V3"]
    assert v2["strictly_decreasing"] and v2["target"][0] == 1.0
    assert v3["rising_with_compensation"] and v3["rising_with_the_deficit"]
    assert v3["normalization_independent_of_the_gain"]


def test_the_compensation_opposes_without_erasing(probes):
    v4, v5 = probes["V4"], probes["V5"]
    assert v4["opposes"] and v4["never_erases"] and v4["still_below_arrival"]
    assert v5["target_at_a_severe_burden"] < 0.05 and v5["output_after"] > 1.0
    assert math.isclose(v5["t_after_the_course"][-1], CHANNEL_BOUNDS[Channel.T][0], abs_tol=1e-12)
    assert any("bounds:T" in key for keys in v5["clamped"] for key in keys)


def test_the_burden_moves_no_other_channel_and_nothing_else_moves_the_tone(probes):
    v6, v11, v12 = probes["V6"], probes["V11"], probes["V12"]
    assert set(v6["course_moved"]) <= set(dt.BURDEN_CONSEQUENCES)
    assert all(v6["never_moved_in_the_course"].values()) and all(v6["never_moved_at_arrival"].values())
    assert v11["tone_target"][0] == v11["tone_target"][1] and v11["hr"][1] > v11["hr"][0]
    assert not v11["stress_in_tone_target"] and not v11["burden_in_sympathetic_target"]
    assert v12["tone_identical"] and v12["map_identical"] and v12["hr_falls_with_blockade"]
    assert not v12["beta_in_tone_path"]


def test_arrival_exactness_and_the_lag_are_preserved(probes):
    v13, v14 = probes["V13"], probes["V14"]
    assert v13["arrival_exact"] and v13["arrival_tone_one"] and v13["minute_one_fixed_point"]
    assert not v14["tone_target_reads"] and v14["monotone_without_oscillation"]
    assert v14["minute_one_unchanged"] and v14["loop_bound"] < 1.0


@pytest.mark.parametrize("name", ["V7", "V8", "V9", "V10"])
def test_every_prior_family_is_exact(probes, name):
    row = probes[name]
    assert row["exact_course"] and row["exact_arrival"] and row["burden_zero"] and row["reader_unset"]


# The signature, the parameters and the debts ---------------------------------------------------------------------------------

def test_the_distributive_signature_holds_without_mapping_a_case():
    s = dt.distributive_signature()
    assert s["pass"], s
    assert all(s["pattern"].values())
    assert all(v == "UNSET" for v in s["arrival_burden"].values())
    assert "DISEASE_SPECIFIC_BP_AND_HR_EQUATION" in s["legacy"]["classification"]
    for case, row in s["authored"].items():
        assert row["extremities"] == "Warm" and dt.NEW_AUX not in row, case


def test_every_magnitude_is_unset():
    p = dt.parameters()
    assert p["pass"], p
    assert all(v is None for v in p["committed_gains"].values())
    assert all(v == 0.0 for v in p["committed_arrival"].values())
    assert p["committed_compensation"]["gi"] == 0.0
    assert all(v == 0.5 for k, v in p["committed_compensation"].items() if k != "gi")


def test_the_carried_debts_are_carried_not_resolved():
    d = dt.carried_debts()
    assert d["pass"], d
    assert d["debts"]["PRESSURE_TO_TONE_COMPENSATION_MISSING"]["status"] == "CARRIED, NOT REQUIRED HERE"
    assert not d["pressure_in_the_tone_path"] and d["no_family_writer"]


def test_the_p2v1_record_is_reproduced_on_its_tree():
    n = dt.non_regression()
    assert n["pass"], n
    assert n["p2v1_record_reproduced_on_its_tree"] and n["p2v1_record_untouched"]
    assert n["p2v1_verdict"] == ss.READY


def test_the_committed_courses_never_move_the_burden():
    for name, (states, _, _) in dt.reference_courses().items():
        assert {s.aux.vasodilatory_burden for s in states} == {0.0}, name


# The verdict, the frozen record and the document -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def found():
    return dt.run()


def test_the_readiness(found):
    assert found["readiness"]["verdict"] == dt.READY and found["readiness"]["blocker"] is None


@pytest.mark.parametrize("path, index", [
    (("representation", "pass"), 0), (("probes", "V2", "pass"), 1), (("probes", "V4", "pass"), 2),
    (("probes", "V6", "pass"), 3), (("probes", "V13", "pass"), 4), (("parameters", "pass"), 5),
    (("probes", "V1", "pass"), 6), (("non_regression", "pass"), 7),
])
def test_every_criterion_blocks_when_its_own_evidence_fails(found, path, index):
    broken = json.loads(json.dumps(found))
    node = broken
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = False
    verdict = dt.readiness(broken)
    assert verdict["blocker"] == dt.READINESS_CRITERIA[index] and verdict["verdict"].startswith(dt.NOT_READY)


@pytest.fixture(scope="module")
def record():
    if not dt.RECORD.exists():
        pytest.skip("the P2W-1 record is written by the evaluation run, after the freeze")
    return json.loads(dt.RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, found):
    assert record["freeze_digest"] == FROZEN_DIGEST
    assert record == json.loads(json.dumps(found, sort_keys=True, default=str))


def test_the_document_is_generated_from_the_record(record):
    if not dt.DOCUMENT.exists():
        pytest.skip("the P2W-1 document is written by the evaluation run, after the freeze")
    from clinical_core import distributive_tone_report as report
    text = dt.DOCUMENT.read_text(encoding="utf-8")
    for name, (opening, closing) in report.MARKERS.items():
        assert opening in text and closing in text, name
        assert report.RENDERERS[name](record).strip() in text, name
