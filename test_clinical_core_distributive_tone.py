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

#: P2X-1 changed four files of the tree P2W-1 was frozen against (the derived tone-domain guards, the writer contract
#: and the two registry tuples) and added its own two: this package's guards read the tree as P2W-1 left it
#: (x1.tree, x1.p2w1_sources), which is where its hashes, its source audits and its freeze digest belong. The one
#: behaviour P2X-1 changed is V5's: a severe burden now fails closed instead of parking T on its guard
#: (P2W1_V5_CLAMP_BEHAVIOUR_SUPERSEDED_BY_P2X1, FACULTY DECISION 4). The frozen record is NOT rewritten.
#: The P2W-1 freeze: the core insertions, the probes, the synthetic values, the readiness rule, the proof and every
#: clinical_core source but the downstream reports, committed before the evaluation run.
FROZEN_DIGEST = "345deb5db60c0638b7b1e1d9a4eb1d1b5f6b82a232b24e084688e2db64174fed"
PROBE_SOURCE = Source(SourceKind.DISEASE_MODULE, "p2w1-test")


@pytest.fixture(autouse=True, scope="module")
def _p2w1_tree():
    from clinical_core import closure_guard as cg
    from clinical_core import amendment_1 as a1
    from clinical_core import tone_domain as x1
    with pytest.MonkeyPatch.context() as patch:
        cg.tree(patch)
        a1.chain(patch)
        x1.tree(patch)
        yield


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
    """P2W-1's probes as they run today. V5 is the one P2X-1 superseded: a burden whose target leaves T's supported
    range now fails closed, so the probe that read the clamp as the response raises instead (FACULTY DECISION 4,
    P2W1_V5_CLAMP_BEHAVIOUR_SUPERSEDED_BY_P2X1). The frozen record keeps its own V5 row; it is not rewritten."""
    found = {"V1": dt.probe_v1(), "V2": dt.probe_v2(), "V3": dt.probe_v3(), "V4": dt.probe_v4(),
             "V6": dt.probe_v6(), **dt.probes_v7_to_v10(), "V11": dt.probe_v11(), "V12": dt.probe_v12(),
             "V13": dt.probe_v13(), "V14": dt.probe_v14()}
    return {k: {"requires": dt.PROBES[k], **found[k]} for k in dt.PROBES if k in found}


@pytest.mark.parametrize("name", [n for n in dt.PROBES if n != "V5"])
def test_each_structural_probe_holds(probes, name):
    assert probes[name]["pass"], probes[name]


def test_the_severe_burden_probe_is_superseded_by_the_closure_package():
    """V5 published the clamp as the response ('no clinical ceiling is chosen'); P2X-1 replaced that reading with a
    refusal, and still declares no clinical maximum burden. The record's V5 row stays as history."""
    from clinical_core import tone_domain as x1
    with pytest.raises(CoreInvariantError):
        dt.probe_v5()
    row = x1.supersession()["records"]["P2W1_V5_CLAMP_BEHAVIOUR_SUPERSEDED_BY_P2X1"]
    assert row["status"] == "P2W1_V5_CLAMP_READING_SUPERSEDED"
    assert x1.probe_x7()["pass"] and x1.probe_x7()["refused"]
    record = json.loads(dt.RECORD.read_text(encoding="utf-8"))
    assert record["probes"]["V5"]["pass"] and record["probes"]["V5"]["clamped"]


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
    v4 = probes["V4"]
    assert v4["opposes"] and v4["never_erases"] and v4["still_below_arrival"]
    # V5's own reading is superseded (see the test above); what it established and P2X-1 keeps is that a severe
    # burden stays dominant: the target is still far below the arrival tone, now outside the supported range.
    record = json.loads(dt.RECORD.read_text(encoding="utf-8"))
    assert record["probes"]["V5"]["target_at_a_severe_burden"] < 0.05
    assert math.isclose(record["probes"]["V5"]["t_after_the_course"][-1], CHANNEL_BOUNDS[Channel.T][0], abs_tol=1e-12)


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
def found(probes):
    """What ``dt.run()`` produced, rebuilt here because its V5 probe no longer runs: P2X-1 refuses the combination
    that probe exercised (FACULTY DECISION 4), so its row is taken from the frozen record, labelled as the one
    superseded reading. Every other section is live."""
    record = json.loads(dt.RECORD.read_text(encoding="utf-8"))
    rows = {**probes, "V5": record["probes"]["V5"]}
    out = {"proof": dt.upstream_unchanged(), "audit": dt.audit(), "representation": dt.representation(),
           "reader": dt.reader_audit(), "probes": {k: rows[k] for k in dt.PROBES},
           "signature": dt.distributive_signature(), "parameters": dt.parameters(),
           "carried_debts": dt.carried_debts(), "non_regression": dt.non_regression()}
    out["readiness"] = dt.readiness(out)
    return dt.go._plain({"freeze_digest": dt.freeze_digest(), "revision": dt.REVISION, "design": dt.design(), **out})


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
    # Every section and every probe but V5 is reproduced live on P2W-1's own tree; V5's row is the frozen one, and
    # the test above is what now holds in its place (P2W1_V5_CLAMP_BEHAVIOUR_SUPERSEDED_BY_P2X1).
    assert record == json.loads(json.dumps(found, sort_keys=True, default=str))


def test_the_document_is_generated_from_the_record(record):
    if not dt.DOCUMENT.exists():
        pytest.skip("the P2W-1 document is written by the evaluation run, after the freeze")
    from clinical_core import distributive_tone_report as report
    text = dt.DOCUMENT.read_text(encoding="utf-8")
    for name, (opening, closing) in report.MARKERS.items():
        assert opening in text and closing in text, name
        assert report.RENDERERS[name](record).strip() in text, name


# The adversarial review's findings, pinned independently of the frozen package ------------------------------------------------
# The module, the record and the document are NOT re-cut: these checks state what the composition really does in the
# region the frozen guards never visit (b < b0, and a declared gain against the T guard), so no later reading of the
# package can mistake its texts for proven properties. Every decision they raise is the faculty's (TD-126 point 9).

def test_the_dilation_factor_is_at_or_below_one_only_for_a_burden_at_or_above_the_arrival_one():
    """R-F2: `derived.tone_target`'s comment, SEMANTICS['reader'] and reader_audit's `factor_at_or_below_one` say the
    factor is at or below 1. That is the b >= b0 branch only: the grid of reader_audit runs with b0 = 0, so the
    resolution branch (b < b0, which SEMANTICS['represents'] admits: 'a vasopressor that opposes it') is never probed.
    There the factor rises above 1, up to exactly 1 + k b0, reached at b = 0."""
    k = dt.TONE_GAIN
    prof = dt.reader(dt.acs_profile(), k)
    assert dt.reader_audit()["factor_at_or_below_one"], "the frozen claim holds on its own grid (b0 = 0)"
    assert all(b >= 0.0 for b in dt.BURDEN_GRID) and dt.BURDEN_STEP > 0, "the frozen grid only ever rises"
    for b0 in (0.0, 2.0):
        anchors = dt.probe_anchors(arrival_vasodilatory_burden=b0)
        arrival = dv.arrival_state(anchors, prof)
        assert dv.tone_target(arrival, anchors, prof) == 1.0, "the arrival is 1 either way"
        rows = {b: dv.tone_target(arrival.evolve(aux=replace(arrival.aux, vasodilatory_burden=b)), anchors, prof)
                for b in (0.0, 0.5, 1.0, 2.0, 4.0)}
        assert all(value <= 1.0 for b, value in rows.items() if b >= b0)
        assert all(value > 1.0 for b, value in rows.items() if b < b0)
        assert rows[0.0] == pytest.approx(1.0 + k * b0), "the ceiling of the resolution branch is 1 + k b0"


def test_the_still_below_arrival_claim_holds_at_the_committed_compensation_only():
    """R-F4: V4 ('the compensation partially opposes the vasodilation without erasing it') runs at one gain, the
    committed 0.5, over DEMANDS. Its own analytic bound already says the largest possible target is 1.1594 at
    g = 1.0 — a gain inside the module's COMPENSATION_GAINS — so above a deficit the grid does not reach, the
    compensation does take the tone above the arrival tone. `never_erases` cannot catch it: it is the identity
    target == compensation x dilation_only with compensation <= bound."""
    assert 1.0 in dt.COMPENSATION_GAINS and max(dt.DEMANDS) == 2.0
    burden = dt.PROBE_BURDEN
    for gain, expected_below in ((0.5, True), (1.0, False)):
        prof = dt.reader(dt.acs_profile(deficit_to_tone_gain=gain))
        anchors = dt.ar.anchors()
        held = dv.arrival_state(anchors, prof)
        held = held.evolve(aux=replace(held.aux, vasodilatory_burden=burden))
        over_the_grid = [dv.tone_target(held.evolve(aux=replace(held.aux, oxygen_demand=d)), anchors, prof)
                         for d in dt.DEMANDS]
        assert all(value < 1.0 for value in over_the_grid), "on the probed grid the claim holds at both gains"
        worst = dv.tone_target(held.evolve(V=-2000.0), anchors, prof)
        assert (worst < 1.0) is expected_below, (gain, worst)
        bound = (1.0 + gain) / (1.0 + gain * dv.arrival_tone_signal(anchors, prof))
        assert worst == pytest.approx(bound / (1.0 + dt.TONE_GAIN * burden)), "the analytic bound is reached at s = 1"


def test_the_tone_gain_guard_and_the_contraction_bound_now_see_the_dilation_factor():
    """R-F3, closed by P2X-1: the published checks read the compensation alone (1 + g against T's guard, and
    g a < 1), so with a declared reader and an arrival burden the largest target was (1 + g) (1 + k b0) / (1 + g s0)
    and the clamp shaped the response. The derived guards now refuse that combination before execution; the P2J-2
    checks themselves are untouched, and no committed profile reaches any of this (every gain is UNSET)."""
    from clinical_core.integration import tone_domain
    prof = dt.reader(dt.acs_profile(), 2.0)
    assert prof.deficit_to_tone_gain * prof.afterload_sensitivity < 1.0, "the P2J-2 profile invariant still passes"
    assert 1.0 + prof.deficit_to_tone_gain <= CHANNEL_BOUNDS[Channel.T][1], "and so does its gain check"
    anchors = dt.probe_anchors(arrival_vasodilatory_burden=10.0)
    arrival = dv.arrival_state(anchors, prof)
    assert dv.tone_target(arrival, anchors, prof) == 1.0
    resolved = arrival.evolve(aux=replace(arrival.aux, vasodilatory_burden=0.0))
    assert dv.tone_target(resolved, anchors, prof) > CHANNEL_BOUNDS[Channel.T][1], "the reachable target is outside"
    assert tone_domain(anchors, prof)["largest_target"] > CHANNEL_BOUNDS[Channel.T][1]
    with pytest.raises(CoreInvariantError):
        dt.course((dt.SyntheticVasodilation("down", -10.0, 0, 1),), 4, anchors, prof)


def test_the_lag_string_check_is_vacuous_but_the_lag_itself_holds():
    """R-F8: probe_v14's `lag_preserved` is `<string> in live or True`, and the string is not in derived.py, so the
    key is reported True whatever the code says (it conditions no `pass`). The lag is real; this pins the behaviour
    instead of the string."""
    import inspect
    source = inspect.getsource(dt.probe_v14)
    assert '"the minute after arrival keeps T = 1" in live or True' in source
    assert "the minute after arrival keeps T = 1" not in dv.__doc__ or True
    live = (dt.ROOT / "clinical_core" / "derived.py").read_text(encoding="utf-8")
    assert "the minute after arrival keeps T = 1" not in live, "the string the probe looks for does not exist"
    anchors, prof = dt.ar.anchors(), dt.reader(dt.acs_profile())
    states, records = dt.course((dt.SyntheticVasodilation("up", 5.0, 0, 1),), 4, anchors, prof)
    assert [state.aux.vasodilatory_burden for state in states][:3] == [0.0, 5.0, 5.0]
    assert states[0].T == 1.0 and states[1].T == 1.0, "the minute the burden is written does not move T"
    assert states[2].T < 1.0, "the tone answers one minute later"


def test_nothing_anywhere_in_the_repository_writes_the_burden():
    """R-F9: representation()['family_writers'] and carried_debts()['no_family_writer'] glob clinical_core/modules
    only, so a writer in clinical_core/interventions (where an epinephrine or vasopressor writer would live) would
    not be seen. The fact holds; the guard is widened here, as P2V-1 did for its own writer."""
    allowed = {"clinical_core/distributive_tone.py", "test_clinical_core_distributive_tone.py",
               "clinical_core/integration.py", "clinical_core/provenance.py", "clinical_core/state.py",
               # P2X-1's closure package names the record in the scan that enforces its writer contract, and
               # P2X-1A's carries the bypass patterns the scan must reject, as source strings.
               "clinical_core/tone_domain.py", "test_clinical_core_tone_domain.py",
               "clinical_core/closure_guard.py", "test_clinical_core_closure_guard.py"}
    found = set()
    for path in sorted(dt.ROOT.rglob("*.py")):
        relative = path.relative_to(dt.ROOT).as_posix()
        if "__pycache__" in path.parts or relative.startswith("validation/"):
            continue
        if "VasodilationChange(" in path.read_text(encoding="utf-8"):
            found.add(relative)
    assert found <= allowed, found
    interventions = sorted((dt.ROOT / "clinical_core" / "interventions").glob("*.py"))
    assert interventions, "the directory the frozen scan does not look at"
    assert not [p for p in interventions if "VasodilationChange" in p.read_text(encoding="utf-8")]


def test_the_burden_is_exactly_invertible_from_the_tone_once_the_gain_is_fixed():
    """R-F6: DECISIONS['residuals'] and SEMANTICS['observable'] are process statements, not guards: no code refuses a
    burden solved from an observable. With k and b0 fixed, b is recovered from the tone (and so from the MAP and the
    flow) to the last bit. At arrival it is not identifiable (the target is 1 for every b0); the risk starts the
    minute after, which is exactly where P2W-2 would fix a region."""
    k, b0 = dt.TONE_GAIN, 0.0
    prof = dt.reader(dt.acs_profile(deficit_to_tone_gain=0.0), k)
    anchors = dt.probe_anchors(arrival_vasodilatory_burden=b0)
    arrival = dv.arrival_state(anchors, prof)
    for truth in (0.25, 7.3):
        held = arrival.evolve(aux=replace(arrival.aux, vasodilatory_burden=truth))
        target = dv.tone_target(held, anchors, prof)
        recovered = ((1.0 + k * b0) / target - 1.0) / k
        assert recovered == pytest.approx(truth, rel=1e-12)
    assert "map" not in dt.mc._names(dt.audit()["functions"]["tone_target"]) if "functions" in dt.audit() else True


def test_the_core_has_no_maldistribution_so_the_burden_shortens_the_refill_and_lowers_the_lactate():
    """R-F7: the distributive signature compares the core against its own burden-0 row, never against the authored
    truth. The core's pressure falls with the flow kept, which is the authored pattern, but its refill SHORTENS
    (the authored cases carry 3 and 4 s, prolonged) and a pure burden LOWERS the lactate (the authored cases carry
    3.4 and 4.6), because the core has no maldistribution or extraction defect. Pinned as the gap it is."""
    signature = dt.distributive_signature()
    rows = signature["rows"]
    refill = [rows[key]["crt"] for key in sorted(rows, key=float)]
    assert refill == sorted(refill, reverse=True), refill
    assert refill[-1] < refill[0], "the core shortens the refill as the burden rises"
    authored = {case: signature["authored"][case]["crt_s"] for case in signature["authored"]}
    assert all(value >= 3.0 for value in authored.values()), authored
    anchors, prof = dt.ar.anchors(), dt.reader(dt.acs_profile())
    states, _ = dt.course((dt.SyntheticVasodilation("up", 0.5, 0, 1),), 8, anchors, prof)
    lactate = [dt.reading(state, anchors, prof)["lactate"] for state in states]
    assert lactate[-1] < lactate[0], lactate
    assert all(signature["authored"][case]["lactate"] >= 3.4 for case in signature["authored"])


def test_two_reported_keys_cannot_fail_as_written():
    """R-F10: `never_erases` is the identity target == compensation x dilation_only with compensation <= bound, and
    `burden_reads_pressure` is a conjunction whose second half is structurally False. Both are reported as evidence;
    neither can discriminate."""
    v4 = dt.probe_v4()
    for value in v4["rows"].values():
        assert value <= v4["largest_possible_target"] + 1e-12
    assert v4["largest_possible_target"] == pytest.approx(v4["dilation_only"] * v4["compensation_bound"])
    v14 = dt.probe_v14()
    assert v14["tone_target_reads"] == [], "no pressure name is read, so the conjunction's second half is always False"
    assert v14["burden_reads_pressure"] is False


def test_a_family_writer_could_close_a_pressure_loop_that_nothing_bounds():
    """R-F1: DECISIONS['timing'] says no pressure -> tone path is introduced because the burden is a state a family
    writes. The core introduces none, and no family writes the burden; but a contributor is handed the whole state
    and derived.derive is public, so a family COULD write the burden against its own MAP, with no rate bound
    anywhere (the kinetics are UNSET, TD-126 point 3). Pinned so the claim is read as what it is: a statement about
    the core, not a guard."""
    import inspect
    assert dt.probe_v14()["tone_target_reads"] == [], "the core's tone target reads no pressure"
    signature = inspect.signature(dt.SyntheticVasodilation.contribute)
    assert {"state", "anchors", "profile"} <= set(signature.parameters), signature
    assert callable(dv.derive), "a contributor can read every observable of the state it is handed"
    assert "PRESSURE_TO_TONE_NOT_REQUIRED_FOR_DISTRIBUTIVE_COMPOSITION" in inspect.getsource(dt)
    assert dt.carried_debts()["pressure_in_the_tone_path"] == [], "true of the core, not of a future family"
    anchors, prof = dt.ar.anchors(), dt.reader(dt.acs_profile())
    state = dv.arrival_state(anchors, prof)
    assert dv.derive(state, anchors, prof).map > 0, "the MAP a contributor could read is one call away"
    assert dv.PARAMETERS[dt.NEW_PROFILE_FIELD][0] == "provisional", "and no rate of its own is declared anywhere"
