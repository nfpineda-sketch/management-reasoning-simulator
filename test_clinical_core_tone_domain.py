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
from clinical_core import tone_domain as x1
from clinical_core.integration import CHANNEL_BOUNDS, step, tone_domain
from clinical_core.state import Channel, CoreInvariantError

ROOT = x1.ROOT
#: The P2X-1 freeze: the derivation, the guards, the contract, the probes, the supersession records, the debt classes,
#: the readiness rule, the proof and every clinical_core source but the downstream reports.
FROZEN_DIGEST = "3afa71b2dfa0f47eb1a00e8987c79cd18b246788e366ac07fe58eacc21815a0e"
T_LOWER, T_UPPER = CHANNEL_BOUNDS[Channel.T][0], CHANNEL_BOUNDS[Channel.T][1]


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
    profile, anchors = x1.reader(x1.acs_profile()), x1.anchors_with(0.0)
    severe = x1.state_with(anchors, profile, x1.SEVERE_BURDEN)
    assert dv.tone_target(severe, anchors, profile) < T_LOWER
    with pytest.raises(CoreInvariantError, match="leaves T's supported range"):
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
