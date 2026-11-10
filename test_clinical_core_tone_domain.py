"""P2X-1: the Phase-2 declared-property closure.

The derived reachable tone domain and its guards, the writer contract, X1-X15, the two supersession records, the
consolidated debt classification, the reversal proof against the P2W-1 tree, and the record and document the single
evaluation run produced.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import math
from dataclasses import replace

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import distributive_tone as dt
from clinical_core import closure_guard as cg
from clinical_core import amendment_2 as a2
from clinical_core import tone_domain as x1
from clinical_core.integration import CHANNEL_BOUNDS, step, tone_domain
from clinical_core.state import Channel, CoreInvariantError

ROOT = x1.ROOT
#: The P2X-1 freeze: the derivation, the guards, the contract, the probes, the supersession records, the debt classes,
#: the readiness rule, the proof and every clinical_core source but the downstream reports.
FROZEN_DIGEST = "3afa71b2dfa0f47eb1a00e8987c79cd18b246788e366ac07fe58eacc21815a0e"
T_LOWER, T_UPPER = CHANNEL_BOUNDS[Channel.T][0], CHANNEL_BOUNDS[Channel.T][1]


@pytest.fixture(autouse=True, scope="module")
def _p2x1_tree():
    """P2X-1A changed the core again (the unconditional ownership guard, the strict interior domain) and the two tuple
    files, proven against the P2X-1 files (closure_guard.proved): this package's own guards, probes and freeze digest
    read the tree as P2X-1 left it (cg.chain, cg.p2x1_sources)."""
    with pytest.MonkeyPatch.context() as patch:
        cg.tree(patch)
        a2.chain(patch)
        yield


# The frozen package and its proof ---------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert set(x1.OWN) <= set(sources) and x1.REPORT not in sources
    assert x1.REPORT in lactate_slice.DOWNSTREAM_REPORTS
    assert {x1.OWN[0], x1.REPORT} <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    if FROZEN_DIGEST is not None:
        assert x1.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_only_the_declared_insertions_differ_from_p2w1():
    assert sorted(x1.REVERSAL) == sorted(x1.CORE_AT_P2W1)
    assert sorted(x1.REVERSAL) == ["clinical_core/decision_pack.py", "clinical_core/integration.py",
                                   "clinical_core/lactate_slice.py", "clinical_core/provenance.py"]
    assert all(x1.proofs().values()), x1.proofs()
    assert all(x1.common_untouched().values()), [k for k, v in x1.common_untouched().items() if not v]
    assert len(x1.COMMON_AT_P2W1) >= 130


@pytest.mark.parametrize("relative", sorted(x1.REVERSAL))
def test_each_declared_replacement_occurs_once_and_reverses(relative):
    live = x1._live(relative)
    for text, _ in x1.REVERSAL[relative]:
        assert live.count(text) == 1, relative
    assert x1.proved(relative)
    assert hashlib.sha256(x1.p2w1_text(relative).encode("utf-8")).hexdigest() == x1.CORE_AT_P2W1[relative]


def test_the_reversal_is_not_evadable():
    """Altering the composition by hand, with the hunks left alone, makes the proof fail in red."""
    live = x1._live("clinical_core/integration.py")
    altered = live.replace("recovery_max * gain * sensitivity", "recovery_max * gain * sensitivity * 0.5")
    assert altered != live
    assert not x1.proved("clinical_core/integration.py", altered)


def test_the_p2w1_tree_reads_the_p2w1_files(monkeypatch):
    with pytest.MonkeyPatch.context() as patch:
        cg.tree(patch)
        a2.chain(patch)
        x1.tree(patch)
        assert dt.freeze_digest() == x1.P2W1_FREEZE_DIGEST
        assert all(dt.proofs().values())
        assert all(dt.common_untouched().values())


# P2X-1-1: the derivation ------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def derivation():
    return x1.derivation()


def test_the_closed_forms_match_the_live_equations(derivation):
    assert derivation["pass"], derivation
    assert derivation["closed_forms_hold"] and derivation["slope_closed_form_holds"]
    for key, value in derivation["observed"].items():
        assert math.isclose(value, derivation["predicted"][key], rel_tol=1e-9, abs_tol=1e-12), key


def test_the_largest_target_is_the_product_of_the_two_maxima(derivation):
    domain = derivation["domain"]
    assert math.isclose(domain["largest_target"], domain["compensation_max"] * domain["recovery_max"], rel_tol=1e-12)
    assert domain["recovery_max"] == 1.0 + x1.TONE_GAIN * x1.ARRIVAL_BURDEN
    assert domain["supported"] == (T_LOWER, T_UPPER)


def test_the_derived_bound_reduces_to_the_p2j2_one_without_the_reader():
    """With the distributive reader UNSET the recovery factor is 1, so the derived bound is P2J-2's times the
    A(T_lo) / (1 + g s0) factor the exact derivation keeps; the published profile invariant is untouched."""
    plain = tone_domain(x1.anchors_with(0.0), x1.acs_profile())
    assert plain["recovery_max"] == 1.0 and plain["distributive_reader"] is False
    assert plain["loop_slope_bound"] < 1.0 and plain["p2j2_slope_bound"] < 1.0
    assert "self.deficit_to_tone_gain * self.afterload_sensitivity >= 1.0" in inspect.getsource(dv)


def test_the_slope_closed_form_holds_away_from_the_kink_and_the_kink_is_located(derivation):
    assert all(row["agree"] and row["active_branch"] for row in derivation["slope"].values())
    kink = derivation["kink"]
    assert kink["signal_below"] == 0.0 and kink["signal_above"] > 0.0
    assert kink["flat_below_the_kink"] and kink["within_bound_above"]


# P2X-1-2 and P2X-1-3: the guards ----------------------------------------------------------------------------------------------

def test_the_guards_read_the_declared_parameters_and_no_pressure():
    g = x1.guards()
    assert g["p2j2_invariant_unchanged"] and g["p2j2_gain_check_unchanged"]
    # The four declared parameters and the channel's own bound (CHANNEL_BOUNDS[Channel.T]); no pressure of any kind.
    assert set(g["tone_domain_reads"]) == {"afterload_sensitivity", "arrival_vasodilatory_burden",
                                           "deficit_to_tone_gain", "vasodilatory_burden_to_tone_gain", "T"}
    assert not {"map", "pressure_rel"} & set(g["tone_domain_reads"])
    assert g["only_refusals_added"]
    assert g["delta_expression"] == "target - state.T", g["delta_expression"]


def test_an_inadmissible_upper_domain_is_refused_before_execution():
    gain, burden = x1.OUTSIDE_UPPER
    profile, anchors = x1.reader(x1.acs_profile(), gain), x1.anchors_with(burden)
    assert tone_domain(anchors, profile)["largest_target"] > T_UPPER
    with pytest.raises(CoreInvariantError, match="largest reachable value"):
        step(x1.state_with(anchors, profile, 0.0), (), anchors, profile)


def test_a_non_contracting_combination_is_refused_before_execution():
    gain, burden, sensitivity = x1.OUTSIDE_CONTRACTION
    profile = x1.reader(x1.acs_profile(afterload_sensitivity=sensitivity), gain)
    anchors = x1.anchors_with(burden)
    domain = tone_domain(anchors, profile)
    assert domain["loop_slope_bound"] >= 1.0 and domain["p2j2_slope_bound"] < 1.0
    assert domain["largest_target"] <= T_UPPER, "the upper admissibility check is not what refuses this one"
    with pytest.raises(CoreInvariantError, match="derived bound with the distributive factor"):
        step(x1.state_with(anchors, profile, burden), (), anchors, profile)


def test_a_target_leaving_the_supported_range_fails_closed_each_minute():
    """P2X-1's refusal still fires; P2X-1A made it strict and reworded it (the endpoints are unresolved boundaries),
    so the message this asserts is the repaired one. The property P2X-1 published - a target outside the range never
    reaches the channel - is unchanged."""
    profile, anchors = x1.reader(x1.acs_profile()), x1.anchors_with(0.0)
    severe = x1.state_with(anchors, profile, x1.SEVERE_BURDEN)
    assert dv.tone_target(severe, anchors, profile) < T_LOWER
    with pytest.raises(CoreInvariantError, match="is not inside T's supported range"):
        step(severe, (), anchors, profile)


def test_no_clinical_ceiling_or_floor_is_declared():
    """The refusals are semantic boundaries, not clinical values: no maximum burden, no lower-tone parameter and no
    disease-specific floor is introduced, and T's own bounds are untouched."""
    assert CHANNEL_BOUNDS[Channel.T] == (0.1, 3.0, dv.PROVISIONAL, "guard only")
    source = inspect.getsource(x1)
    assert "no clinical maximum burden" in source
    names = {field for field in dv.PARAMETERS}
    assert not {n for n in names if "maximum_burden" in n or "tone_floor" in n}
    assert dv.DEFAULT_PROFILE.vasodilatory_burden_to_tone_gain is None


# P2X-1-4: the writer contract -------------------------------------------------------------------------------------------------

def test_the_writer_contract_is_declared_and_nothing_violates_it():
    contract = x1.writer_contract()
    assert contract["pass"], contract
    assert not contract["family_writers"] and not contract["offenders"]
    text = (ROOT / "clinical_core" / "provenance.py").read_text(encoding="utf-8")
    assert "PRESSURE_DRIVEN_FAMILY_VASODILATION = DEFERRED / NOT_AUTHORIZED" in text
    assert "negative burden is not" in text


def test_the_contract_scan_would_catch_a_pressure_reading_writer():
    """The scan is the enforcement, so it must fail on a writer that reads the MAP: proven on a synthetic source."""
    source = '''
from clinical_core.provenance import VasodilationChange
def contribute(self, state, minute, signals, anchors, profile):
    from clinical_core.derived import derive
    pressure = derive(state, anchors, profile).map
    return VasodilationChange(1.0 / pressure, self.source, minute, "pressure-driven")
'''
    tree = ast.parse(source)
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        builds = any(isinstance(inner, ast.Call) and getattr(inner.func, "id", None) == "VasodilationChange"
                     for inner in ast.walk(node))
        reads = {inner.attr for inner in ast.walk(node) if isinstance(inner, ast.Attribute)}
        if builds and (reads & {"map", "pressure_rel", "sbp", "dbp", "mean_arterial_pressure"} or "T" in reads):
            offenders.append(node.name)
    assert offenders == ["contribute"]


# P2X-1-5: X1-X15 --------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def probes():
    return x1.structural_probes()


@pytest.mark.parametrize("name", x1.PROBES)
def test_each_structural_probe_holds(probes, name):
    assert probes[name]["pass"], probes[name]


def test_the_factor_is_one_at_the_arrival_burden_and_rises_only_as_it_resolves(probes):
    x1_, x2, x3, x4 = probes["X1"], probes["X2"], probes["X3"], probes["X4"]
    assert all(value == 1.0 for value in x1_["rows"].values())
    assert x2["target"][0] == 1.0 and all(b < a for a, b in zip(x2["target"], x2["target"][1:]))
    assert x3["target"][0] == 1.0 and all(b > a for a, b in zip(x3["target"], x3["target"][1:]))
    assert all(math.isclose(row["observed"], row["predicted"], rel_tol=1e-12) for row in x4["rows"].values())


def test_a_negative_burden_is_refused_everywhere(probes):
    assert all(value is True for value in probes["X5"].values() if isinstance(value, bool))
    arrival = dv.arrival_state(x1.anchors_with(1.0), x1.reader(x1.acs_profile()))
    with pytest.raises(CoreInvariantError):
        replace(arrival.aux, vasodilatory_burden=-1e-9)


def test_valid_interior_combinations_never_clamp(probes):
    x8 = probes["X8"]
    assert not any(x8["clamps"]) and x8["inside_the_range"]


def test_the_predecessor_and_every_prior_family_are_exact(probes):
    x11, x12 = probes["X11"], probes["X12"]
    assert not x11["differing"] and x11["courses_identical"] and x11["v5_now_refused"]
    assert len(x11["probes_compared"]) == 13
    assert all(x12["committed_profiles_unset"].values()) and x12["no_refusal_in_any_committed_course"]


def test_neither_the_systemic_stress_nor_beta_blockade_reaches_the_tone(probes):
    x13, x14 = probes["X13"], probes["X14"]
    assert len(set(x13["targets"].values())) == 1 and x13["hr"]["2.0"] > x13["hr"]["0.0"]
    assert len(set(x14["targets"].values())) == 1 and x14["beta_not_in_the_tone_path"]


# P2X-1-6 and P2X-1-7: supersession and debt -----------------------------------------------------------------------------------

def test_the_supersession_records_preserve_history():
    s = x1.supersession()
    assert s["pass"] and s["p2w1_digest_unchanged"]
    assert set(s["records"]) == {"TD120_HISTORICAL_SUPERSESSION_ACCEPTED",
                                 "P2W1_V5_CLAMP_BEHAVIOUR_SUPERSEDED_BY_P2X1"}
    td120 = s["records"]["TD120_HISTORICAL_SUPERSESSION_ACCEPTED"]
    assert td120["status"] == "P2S3_FROZEN_VERDICT_SUPERSEDED_BY_P2T3"
    assert "ASTHMA_SHADOW_MIGRATION_READY" in td120["authoritative"]
    assert "is recut or rewritten" in td120["history_preserved"] and td120["history_preserved"].startswith("no ")


def test_no_historical_digest_is_rewritten():
    """P2S-3's and P2W-1's frozen records keep their own digests: the supersession is a record, not a rewrite."""
    from clinical_core import asthma_migration as sm
    record = json.loads(sm.RECORD.read_text(encoding="utf-8"))
    assert record["freeze_digest"]
    with pytest.MonkeyPatch.context() as patch:
        cg.tree(patch)
        a2.chain(patch)
        x1.tree(patch)
        assert dt.freeze_digest() == x1.P2W1_FREEZE_DIGEST
    p2w1 = json.loads(dt.RECORD.read_text(encoding="utf-8"))
    assert p2w1["readiness"]["verdict"] == "COMMON_DISTRIBUTIVE_TONE_COMPOSITION_READY"
    assert p2w1["probes"]["V5"]["pass"] is True


def test_the_debt_classification_is_explicit_and_blocks_nothing():
    d = x1.debt_classification()
    assert d["pass"] and not d["blockers"]
    assert set(d["classes"]) == {"ACCEPTABLE_PHASE2_DEBT", "NEXT_PHASE_INTEGRATION_DEBT", "FUTURE_RESEARCH_DEBT"}
    assert d["counts"]["ACCEPTABLE_PHASE2_DEBT"] >= 11
    assert {"CONSCIOUSNESS_WIRING", "RUNTIME_INTEGRATION", "RESIDENT_VISIBLE_BEHAVIOUR"} <= \
        set(d["classes"]["NEXT_PHASE_INTEGRATION_DEBT"])
    assert {"MALDISTRIBUTION_AND_EXTRACTION", "UPPER_AIRWAY", "PLASMA_LEAK"} <= \
        set(d["classes"]["FUTURE_RESEARCH_DEBT"])


def test_no_clinical_magnitude_is_chosen():
    assert "UNSET" in x1.design()["magnitudes"]
    for name, value in x1.design()["synthetic"].items():
        assert isinstance(value, (int, float, list)), name
    assert dv.DEFAULT_PROFILE.vasodilatory_burden_to_tone_gain is None
    assert all(profile.vasodilatory_burden_to_tone_gain is None for profile in dt.committed_profiles().values())


# Readiness, the record and the document ---------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def found():
    return x1.run()


def test_the_readiness(found):
    assert found["readiness"]["verdict"] == x1.READY and found["readiness"]["blocker"] is None
    assert len(found["readiness"]["criteria"]) == 9


@pytest.mark.parametrize("path, index", [
    (("derivation", "pass"), 0), (("probes", "X5", "pass"), 1), (("probes", "X6", "pass"), 2),
    (("probes", "X9", "pass"), 3), (("probes", "X15", "pass"), 4), (("probes", "X11", "pass"), 5),
    (("supersession", "pass"), 6), (("debt_classification", "pass"), 7), (("contradictions", "pass"), 8),
])
def test_every_criterion_blocks_when_its_own_evidence_fails(found, path, index):
    broken = json.loads(json.dumps(found, default=str))
    node = broken
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = False
    verdict = x1.readiness(broken)
    assert verdict["blocker"] == x1.READINESS_CRITERIA[index] and verdict["verdict"].startswith(x1.NOT_READY)


@pytest.fixture(scope="module")
def record():
    if not x1.RECORD.exists():
        pytest.skip("the P2X-1 record is written by the evaluation run, after the freeze")
    return json.loads(x1.RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, found):
    assert record["freeze_digest"] == FROZEN_DIGEST
    assert record == json.loads(json.dumps(found, sort_keys=True, default=str))


def test_the_document_is_generated_from_the_record(record):
    if not x1.DOCUMENT.exists():
        pytest.skip("the P2X-1 document is written by the evaluation run, after the freeze")
    from clinical_core import tone_domain_report as report
    text = x1.DOCUMENT.read_text(encoding="utf-8")
    for name, (opening, closing) in report.MARKERS.items():
        assert opening in text and closing in text, name
        assert report.RENDERERS[name](record).strip() in text, name


# The adversarial review's findings, pinned independently of the frozen package -------------------------------------------------
# The frozen rule returned PHASE2_DECLARED_PROPERTIES_CLOSED; the review showed that criterion 3 does not hold over the
# whole declared domain and that three of the nine criteria cannot fail. The module, the record and the document are
# NOT re-cut (history is preserved, as for P2S-3): the operative classification is NOT_CLOSED, recorded in
# PHASE2_SHADOW_CORE section 72 and TD-127, and every finding is pinned here so the next package starts from them.

def test_the_blocker_of_the_conditional_ownership_guard_is_closed_by_p2x1a():
    """R-F1 (the blocker, criterion 3): step calls _vascular_tone only when the compensation gain is above 0 or the
    distributive reader is declared, and BOTH P2J-2's second-writer refusal and P2X-1's per-minute boundary live
    inside it. The committed GI profile has g = 0 and the reader UNSET, so a writer of T drives the channel onto its
    guard and the clamp shapes the value. No contributor writes T today (pinned in
    test_clinical_core_pressure_tone.py), so it is reachable only with a new writer - but `contradictions()` publishes
    'a family delta on T is refused' as a fact, and criterion 3 claims the clamp never shapes physiology."""
    from clinical_core.provenance import SourceKind
    pairs = dt.committed_pairs()
    anchors, gi = pairs["gi"]
    assert gi.deficit_to_tone_gain == 0.0 and gi.vasodilatory_burden_to_tone_gain is None
    source = inspect.getsource(step)
    assert "profile.deficit_to_tone_gain > 0.0 or profile.vasodilatory_burden_to_tone_gain is not None" in source
    writer = dt._FamilyTone("fam")
    # CLOSED BY P2X-1A: integration._tone_ownership runs from step on every profile, so the writer that used to park
    # T on its guard with clamps recorded is now refused here too. What P2X-1 recorded stays in its own document and
    # in TD-127; what runs is the repair, pinned in test_clinical_core_closure_guard.py (A1-A3).
    with pytest.raises(CoreInvariantError, match="only clinical owner"):
        step(dv.arrival_state(anchors, gi), (writer,), anchors, gi)
    # With the response on, P2X-1A's ownership guard reaches the same writer first (it runs before the response);
    # P2J-2's own composition refusal is not relaxed and is still reachable for a declared synthetic probe, which
    # test_clinical_core_closure_guard.py pins.
    anchors_on, acs = pairs["acs"]
    with pytest.raises(CoreInvariantError, match="only clinical owner"):
        step(dv.arrival_state(anchors_on, acs), (writer,), anchors_on, acs)
    assert x1.contradictions()["searched"]["incompatible_writer_ownership"].startswith("no:")


def test_the_inclusive_boundary_that_recorded_a_roundoff_clamp_is_closed_by_p2x1a():
    """R-F4 (criterion 3, X8): the boundary accepts a target exactly on T's lower guard, but the channel rebuilds the
    value as T + (target - T) with fsum, and that round trip can land one ulp below it. The magnitude is 2.8e-17 and
    the clamp pushes towards the target, but a clamp IS recorded in an accepted minute, so 'valid interior
    combinations run with no clamp at all' is not true at the exact boundary."""
    from clinical_core.provenance import SourceKind
    profile, anchors = x1.reader(x1.acs_profile(), 1.0), x1.anchors_with(0.0)
    domain = tone_domain(anchors, profile)
    assert domain["largest_target"] <= T_UPPER and domain["loop_slope_bound"] < 1.0, "the domain is accepted"
    state = x1.state_with(anchors, profile, 9.0)
    assert dv.tone_target(state, anchors, profile) == T_LOWER, "exactly on the guard: what P2X-1 accepted"
    # CLOSED BY P2X-1A: the domain is the open interval and the reconstruction is checked, so this minute is refused
    # before the channel is rebuilt and no clamp can be recorded in an accepted one (A4, A8, A9).
    with pytest.raises(CoreInvariantError, match="unresolved boundaries"):
        step(state, (), anchors, profile)
    assert "not lower <= target <= upper" in inspect.getsource(x1.guards), "P2X-1's own record is not rewritten"
    hair_inside = x1.state_with(anchors, profile, 8.9)
    after, record = step(hair_inside, (), anchors, profile)
    assert T_LOWER < after.T and not [delta for delta in record.deltas
                                      if delta.source.kind is SourceKind.CLAMP]


def test_three_of_the_nine_criteria_cannot_fail_as_written():
    """R-F2 (criteria 7, 8, 9): contradictions() and debt_classification() derive `pass` from a list they build empty,
    and supersession()'s `pass` is all() over two non-empty prose strings. CONTRADICTIONS and DEBT are never compared
    with the code, so the document publishes 'no blockers / no contradictions' from a search that does not run. Of
    criterion 7 only p2w1_digest_unchanged is executable."""
    assert x1.contradictions()["inside_certified_scope"] == []
    assert "out[\"pass\"] = not out[\"inside_certified_scope\"]" in inspect.getsource(x1.contradictions)
    assert x1.debt_classification()["blockers"] == []
    assert "out[\"pass\"] = not out[\"blockers\"]" in inspect.getsource(x1.debt_classification)
    rows = x1.supersession()["records"]
    assert all(isinstance(row["history_preserved"], str) and row["history_preserved"] for row in rows.values())
    assert "all(row[\"history_preserved\"] for row in rows.values())" in inspect.getsource(x1.supersession)


def test_the_writer_contract_scan_misses_four_evasions():
    """R-F3 / R-F12 (criterion 5): the scan resolves the constructor only as an ast.Name, inspects only the function
    that builds the record, reads only attribute names, and its forbidden list omits same-loop observables. Each of
    the four shapes below reads the pressure loop and would pass. The contract text is wider than its enforcement."""
    shapes = {
        "qualified_constructor": "pv.VasodilationChange(1.0 / derive(state, anchors, profile).map, s, m, 'd')",
        "helper_function": "amount = _from_pressure(state, anchors, profile)\n    return VasodilationChange(amount, s, m, 'd')",
        "positional_access": "VasodilationChange(_perfusion(state, anchors, profile)[1], s, m, 'd')",
        "same_loop_observable": "VasodilationChange(derive(state, anchors, profile).output_rel, s, m, 'd')",
    }
    forbidden = set(x1.writer_contract()["forbidden_inputs"])
    for name, body in shapes.items():
        tree = ast.parse(f"def contribute(self, state, minute, signals, anchors, profile):\n    {body}\n")
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
        builds = any(isinstance(inner, ast.Call) and getattr(inner.func, "id", None) == "VasodilationChange"
                     for inner in ast.walk(node))
        reads = {inner.attr for inner in ast.walk(node) if isinstance(inner, ast.Attribute)}
        caught = builds and bool(reads & forbidden)
        assert not caught, f"{name} is not caught by the scan as written"
    assert "observable of the same" in (ROOT / "clinical_core" / "provenance.py").read_text(encoding="utf-8")
    assert not {"output_rel", "delivery_rel", "crt_s", "sympathetic_drive"} & forbidden
    assert x1.probe_x15()["family_writers"] == [], "X15 passes by absence: no family writer exists to test"


def test_the_contraction_witness_runs_with_the_distributive_factor_at_one():
    """R-F5 / R-F6 (criterion 4): OUTSIDE_CONTRACTION has b0 = 0, so its recovery factor is 1 and the refusal comes
    entirely from the afterload term the derivation inherits from P2J-2 - not from the distributive factor the
    criterion says the guard now covers. And the same profile with the reader UNSET has the same bound and is
    accepted, because the check sits behind `distributive_reader`."""
    gain, burden, sensitivity = x1.OUTSIDE_CONTRACTION
    assert burden == 0.0
    profile = x1.reader(x1.acs_profile(afterload_sensitivity=sensitivity), gain)
    anchors = x1.anchors_with(burden)
    declared = tone_domain(anchors, profile)
    assert declared["recovery_max"] == 1.0 and declared["loop_slope_bound"] >= 1.0
    unset = tone_domain(anchors, x1.acs_profile(afterload_sensitivity=sensitivity))
    assert unset["loop_slope_bound"] == declared["loop_slope_bound"] and unset["distributive_reader"] is False
    step(dv.arrival_state(anchors, x1.acs_profile(afterload_sensitivity=sensitivity)), (), anchors,
         x1.acs_profile(afterload_sensitivity=sensitivity))   # accepted: the check is skipped without the reader
    assert "if domain[\"distributive_reader\"]:" in inspect.getsource(step.__globals__["_vascular_tone"])


def test_the_slope_is_never_verified_with_the_distributive_factor_above_one():
    """R-F7 (criterion 4): derivation() and X9 sample the slope on arrival-like states, where the burden is b0 and so
    B(b) = 1 exactly. The live slope at b = 0 is B_max times larger - the one factor P2X-1 adds is absent from every
    numeric check of the slope. Pinned here with the factor measured."""
    profile, anchors = x1.reader(x1.acs_profile(), x1.TONE_GAIN), x1.anchors_with(x1.ARRIVAL_BURDEN)
    arrival = dv.arrival_state(anchors, profile)
    assert arrival.aux.vasodilatory_burden == x1.ARRIVAL_BURDEN
    recovery = tone_domain(anchors, profile)["recovery_max"]
    h = 1e-6
    for tone in (1.0, 1.5, 2.0):
        at_arrival_burden = (dv.tone_target(arrival.evolve(T=tone + h), anchors, profile)
                             - dv.tone_target(arrival.evolve(T=tone - h), anchors, profile)) / (2 * h)
        resolved = arrival.evolve(aux=replace(arrival.aux, vasodilatory_burden=0.0))
        at_zero = (dv.tone_target(resolved.evolve(T=tone + h), anchors, profile)
                   - dv.tone_target(resolved.evolve(T=tone - h), anchors, profile)) / (2 * h)
        assert math.isclose(at_zero / at_arrival_burden, recovery, rel_tol=1e-6), tone
    assert all(row["active_branch"] for row in x1.derivation()["slope"].values())


def test_x12_computes_course_digests_it_never_compares():
    """R-F8 (criterion 6): X12's name and docstring say the committed readings are the frozen ones, but its `pass`
    reads only `committed_profiles_unset` and a single accepted minute per profile. The real bit-exactness evidence
    is X11's reproduction of the P2V-1 record on its tree."""
    x12 = x1.probe_x12()
    assert x12["course_digests"] and "course_digests" not in inspect.getsource(x1.probe_x12).split('out["pass"]')[1]
    assert x1.probe_x11()["courses_identical"], "this is where the bit-exactness is really established"


def test_the_verdict_rule_does_not_read_the_reversal_proof():
    """R-F10: found['proof'] (the four reversals, the 133 common hashes and P2W-1's freeze digest on its own tree) is
    published in the record and in the document, and conditions none of the nine criteria. The fact is verified by
    pytest above; what is missing is that the verdict depend on it."""
    source = inspect.getsource(x1.readiness)
    assert '"proof"' not in source and "upstream_unchanged" not in source
    assert all(x1.proofs().values()) and all(x1.common_untouched().values())


def test_the_td120_supersession_cites_documents_that_do_not_exist_and_pins_no_p2s3_digest():
    """R-F11 (criterion 7): supersession() looks for P2S3_ASMA_EN_SOMBRA.md and P2T3_ASMA_CON_DISTRES.md, which are
    not the real filenames, so both rows fall back silently. No P2S-3 digest is pinned anywhere, and the test that
    claims to check it only asserts the string is non-empty. The FACT holds - no P2S-3 file is touched by this
    package - and that is what is asserted here instead."""
    from clinical_core import asthma_migration as sm
    documents = x1.supersession()["records"]["TD120_HISTORICAL_SUPERSESSION_ACCEPTED"]["documents"]
    assert documents["historical"].endswith("(P2S-3 section)") and documents["superseding"].endswith("(P2T-3 section)")
    assert not (ROOT / "docs" / "revision" / "P2S3_ASMA_EN_SOMBRA.md").exists()
    assert (ROOT / "docs" / "revision" / "P2S3_ASMA_SOMBRA.md").exists()
    assert "P2S3_ASMA_SOMBRA" not in inspect.getsource(x1.supersession)
    # the fact: P2S-3's record is byte-identical to the predecessor head's
    import subprocess
    at_head = subprocess.run(["git", "show", f"{x1.P2W1_HEAD}:{sm.RECORD.relative_to(ROOT).as_posix()}"],
                             cwd=ROOT, capture_output=True, check=True).stdout
    assert hashlib.sha256(at_head).hexdigest() == hashlib.sha256(sm.RECORD.read_bytes()).hexdigest()


def test_the_refusal_helper_is_blind_to_the_reason():
    """R-F13: x1._refused swallows any CoreInvariantError or ProvenanceError, and X5's three sub-refusals are not
    message-checked anywhere. Pinned with the messages they must carry."""
    assert "except error:" in inspect.getsource(x1._refused)
    with pytest.raises(CoreInvariantError, match="never negative"):
        replace(dv.arrival_state(x1.anchors_with(1.0), x1.reader(x1.acs_profile())).aux, vasodilatory_burden=-1.0)
    with pytest.raises(CoreInvariantError, match="vasodilatory burden"):
        x1.anchors_with(-1.0)
