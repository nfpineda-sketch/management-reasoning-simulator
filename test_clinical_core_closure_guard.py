"""P2X-1A: the final Phase-2 closure guard repair.

The unconditional T ownership invariant, the strict interior tone domain, the zero-clamp guarantee, the strengthened
writer-contract scan, A1-A22, the executable contradictions / debt / supersession checks, the reversal proof against
the P2X-1 tree, and the record and document the single evaluation run produced. Every criterion is checked both ways:
it holds, and breaking the property it reads makes it fail.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
from dataclasses import replace

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import closure_guard as cg
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import distributive_tone as dt
from clinical_core import integration as ig
from clinical_core import pressure_tone as pt
from clinical_core import tone_domain as x1
from clinical_core import vascular_tone as vt
from clinical_core.integration import CHANNEL_BOUNDS, step
from clinical_core.provenance import Source, SourceKind
from clinical_core.state import Channel, CoreInvariantError, UnresolvedBoundary

ROOT = cg.ROOT
#: The P2X-1A freeze: the guards, the contract scan, A1-A22, the executable checks, the readiness rule, the proof and
#: every clinical_core source but the downstream reports.
FROZEN_DIGEST = "f54dbb441507c27182bfcc65f6636589db1f9df2a6c074d3ec9ce9bde303b289"
T_LOWER, T_UPPER = CHANNEL_BOUNDS[Channel.T][0], CHANNEL_BOUNDS[Channel.T][1]


@pytest.fixture(scope="module")
def probes():
    return cg.structural_probes()


# The frozen package and its proof ---------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert set(cg.OWN) <= set(sources) and cg.REPORT not in sources
    assert cg.REPORT in lactate_slice.DOWNSTREAM_REPORTS
    assert {cg.OWN[0], cg.REPORT} <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    if FROZEN_DIGEST is not None:
        assert cg.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_only_the_declared_insertions_differ_from_p2x1():
    assert sorted(cg.REVERSAL) == sorted(cg.CORE_AT_P2X1)
    assert sorted(cg.REVERSAL) == ["clinical_core/decision_pack.py", "clinical_core/integration.py",
                                   "clinical_core/lactate_slice.py", "clinical_core/provenance.py"]
    assert all(cg.proofs().values()), cg.proofs()
    assert all(cg.common_untouched().values()), [k for k, v in cg.common_untouched().items() if not v]
    assert len(cg.COMMON_AT_P2X1) >= 135
    assert "clinical_core/tone_domain.py" in cg.COMMON_AT_P2X1


@pytest.mark.parametrize("relative", sorted(cg.REVERSAL))
def test_each_declared_replacement_occurs_once_and_reverses(relative):
    live = cg._live(relative)
    for text, _ in cg.REVERSAL[relative]:
        assert live.count(text) == 1, relative
    assert cg.proved(relative)
    assert hashlib.sha256(cg.p2x1_text(relative).encode("utf-8")).hexdigest() == cg.CORE_AT_P2X1[relative]


def test_the_reversal_is_not_evadable():
    """Altering the guard by hand, with the hunks left alone, makes the proof fail in red."""
    live = cg._live("clinical_core/integration.py")
    altered = live.replace("not lower < target < upper", "not lower <= target <= upper")
    assert altered != live
    assert not cg.proved("clinical_core/integration.py", altered)


def test_the_p2x1_tree_reads_the_p2x1_files(monkeypatch):
    cg.chain(monkeypatch)
    text = x1._live("clinical_core/integration.py")
    assert "_tone_ownership" not in text
    assert "not lower <= target <= upper" in text
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == cg.CORE_AT_P2X1["clinical_core/integration.py"]
    listed = [p.name for p in x1.CORE_DIR.glob("*.py")]
    assert "closure_guard.py" not in listed and "tone_domain.py" in listed


def test_the_predecessor_record_reproduces_on_its_own_tree():
    found = cg.non_regression()
    assert found["p2x1_record_reproduced_on_its_tree"], "P2X-1's record no longer reproduces on its tree"
    assert found["p2x1_record_untouched"]
    assert found["p2x1_frozen_verdict"] == x1.READY
    assert found["pass"]


def test_the_predecessor_freeze_digest_still_holds():
    assert cg._p2x1_digest() == cg.P2X1_FREEZE_DIGEST
    assert cg.upstream_unchanged()["pass"]


# P2X-1A-1: the unconditional ownership invariant -------------------------------------------------------------------------------

def test_the_ownership_guard_runs_from_step_under_no_condition():
    guards = cg.guards()
    assert guards["ownership"]["called"] and guards["ownership"]["at_statement_level"]
    assert guards["ownership"]["before_the_channel_rebuild"]
    assert guards["ownership"]["out_of_the_response"] and not guards["ownership"]["inside_a_condition"]
    source = inspect.getsource(ig)
    tree = ast.parse(source)
    stepper = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "step")
    calls = [index for index, statement in enumerate(stepper.body)
             if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
             and getattr(statement.value.func, "id", None) == "_tone_ownership"]
    assert len(calls) == 1, "the ownership guard is called once, from step's own statement list"


@pytest.mark.parametrize("name", sorted(dt.committed_pairs()))
def test_a_clinical_writer_of_t_is_refused_on_every_committed_profile(name):
    anchors, profile = dt.committed_pairs()[name]
    with pytest.raises(CoreInvariantError, match="only clinical owner"):
        dt.course((dt._FamilyTone("fam"),), 4, anchors, profile)


def test_the_gi_profile_is_the_case_the_p2x1_review_demonstrated():
    """With the compensation at 0 and the reader UNSET the response does not run at all: before P2X-1A the writer
    reached the channel and the clamp shaped the value."""
    anchors, profile = dt.committed_pairs()["gi"]
    assert profile.deficit_to_tone_gain == 0.0 and profile.vasodilatory_burden_to_tone_gain is None
    source = inspect.getsource(ig.step)
    assert "if profile.deficit_to_tone_gain > 0.0 or profile.vasodilatory_burden_to_tone_gain is not None:" in source
    with pytest.raises(CoreInvariantError, match="only clinical owner"):
        step(dv.arrival_state(anchors, profile), (dt._FamilyTone("fam"),), anchors, profile)


def test_the_declared_synthetic_probes_still_write_t_and_are_published_as_non_clinical():
    """The one interpretation this package declares: a scripted probe is outside the owner for T as it is for V and
    Hb, which P2J-1's published TONE_RULE already says. If the faculty wants the wider reading, these three probes
    are what it retires."""
    from clinical_core import bands
    assert "writer outside a synthetic probe, a test or a bound is a clinical writer" in pt.TONE_RULE
    assert "clinical_core/bands.py" in pt.PROBE_MODULES
    drift = bands.Drift("tone", "T", 0, 40, -0.01)
    assert drift.source.kind is SourceKind.SCRIPTED_EVENT
    anchors, profile = dt.committed_pairs()["gi"]
    after, record = step(dv.arrival_state(anchors, profile), (drift,), anchors, profile)
    assert after.T == pytest.approx(0.99)
    assert cg.INTERPRETATION["implemented_as"].startswith("every clinical source")


def test_p2j2_still_refuses_any_second_writer_while_the_response_runs():
    """P2J-2's published composition refusal is not relaxed: with the response on, even a scripted drift is refused."""
    from clinical_core import bands
    anchors = vt.tone_anchors("gi_bleed_57m", "lower", 1.0)
    profile = vt.tone_profile(1.0, 0.3)
    with pytest.raises(CoreInvariantError, match="compose"):
        step(dv.arrival_state(anchors, profile), (bands.Drift("tone", "T", 0, 40, -0.01),), anchors, profile)


# P2X-1A-2 and P2X-1A-3: the strict domain and the zero clamp -------------------------------------------------------------------

def test_the_per_minute_boundary_is_strict_and_reads_the_reconstruction():
    guards = cg.guards()["strict_domain"]
    assert guards["strict"] and guards["reconstruction_checked"]
    assert guards["exception"] == "UnresolvedBoundary"
    assert guards["no_tolerance_constant"] and not guards["floats_below_the_lower_guard"]
    assert "lower < target < upper" in guards["per_minute"][0]
    assert "reconstructed" in guards["per_minute"][0]


def test_the_lower_endpoint_is_refused_and_a_hair_inside_it_runs_with_no_clamp():
    profile, anchors = cg._endpoint_reader()
    on_the_guard = x1.state_with(anchors, profile, cg.ENDPOINT_BURDEN)
    assert dv.tone_target(on_the_guard, anchors, profile) == T_LOWER
    with pytest.raises(UnresolvedBoundary, match="unresolved boundaries"):
        step(on_the_guard, (), anchors, profile)
    inside = x1.state_with(anchors, profile, cg.INSIDE_BURDEN)
    after, record = step(inside, (), anchors, profile)
    assert T_LOWER < after.T < T_UPPER
    assert not [delta for delta in record.deltas if delta.source.kind is SourceKind.CLAMP]


def test_the_upper_endpoint_is_refused_at_the_parameter_level_without_a_reader():
    profile = vt.tone_profile(cg.P2J2_ENDPOINT_GAIN, vt.PRIMARY_AFTERLOAD)
    assert profile.vasodilatory_burden_to_tone_gain is None
    assert ig.tone_domain(vt.NEUTRAL, profile)["largest_target"] == T_UPPER
    assert not 1.0 + cg.P2J2_ENDPOINT_GAIN > T_UPPER, "P2J-2's own check would pass: the endpoint was inclusive"
    with pytest.raises(CoreInvariantError, match="reaches or passes"):
        step(dv.arrival_state(vt.NEUTRAL, profile), (), vt.NEUTRAL, profile)


def test_no_accepted_minute_of_the_whole_course_carries_a_clamp_on_t(probes):
    found = probes["A9"]
    assert found["pass"] and not any(found["clamps"]) and not any(found["tone_clamps"])
    assert found["burden_trail"][1] == cg.COURSE_BURDEN


def test_the_rounding_the_review_found_is_inside_the_admissibility_test(probes):
    """R-F4: the reconstruction differs from the target by a 1e-17, which used to be recorded as a clamp inside an
    accepted minute. The guard now tests the value the channel will hold."""
    found = probes["A8"]
    assert found["rebuild_difference"] != 0.0 and abs(found["rebuild_difference"]) < 1e-16
    assert found["channel_holds_the_rebuilt_value"] and not found["clamps"]


def test_an_inclusive_boundary_would_let_the_clamp_back_in(monkeypatch):
    """The strictness is what keeps the clamp out: with the comparison relaxed, the endpoint witness is accepted and
    the channel records a clamp on T."""
    profile, anchors = cg._endpoint_reader()
    state = x1.state_with(anchors, profile, cg.ENDPOINT_BURDEN)
    lower, upper = T_LOWER, T_UPPER
    target = dv.tone_target(state, anchors, profile)
    assert lower <= target <= upper and not lower < target < upper
    rebuilt = state.T + (target - state.T)
    assert not lower < rebuilt < upper or rebuilt != target


# P2X-1A-8: the writer contract ------------------------------------------------------------------------------------------------

def test_the_contract_scan_covers_the_repository_and_finds_no_offender():
    found = cg.writer_contract()
    assert found["contract_declared"] and found["p2x1a_strengthening_declared"]
    assert found["files_scanned"] >= 3 and found["writers"]
    assert not found["offenders"], found["offenders"]
    assert set(cg.FORBIDDEN_READS) >= {"map", "pressure_rel", "T", "output_rel", "delivery_rel", "crt_s",
                                       "sympathetic_drive", "sbp", "dbp"}


@pytest.mark.parametrize("name", sorted(cg.BYPASS_PATTERNS))
def test_each_bypass_the_review_found_is_rejected(name):
    found = cg.scan_text(cg.BYPASS_PATTERNS[name])
    assert found["writers"], name
    assert found["offenders"], f"{name} slipped through the scan"


def test_the_allowed_writer_pattern_is_accepted():
    found = cg.scan_text(cg.ALLOWED_PATTERN)
    assert found["writers"] and not found["offenders"]


def test_two_methods_with_the_same_name_do_not_collapse():
    """P2X-1's scan keyed functions by name, so two ``contribute`` methods shadowed each other."""
    source = ("from clinical_core.provenance import VasodilationChange\n"
              "class A:\n"
              "    def contribute(self, view):\n"
              "        return VasodilationChange(view.map * 0.01, None, 1, 'b')\n"
              "class B:\n"
              "    def contribute(self, process):\n"
              "        return VasodilationChange(process.severity, None, 1, 'b')\n")
    found = cg.scan_text(source)
    assert sorted(found["writers"]) == ["<probe>:A.contribute", "<probe>:B.contribute"]
    assert [item["writer"] for item in found["offenders"]] == ["<probe>:A.contribute"]


# A1-A22 -----------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", [f"A{index}" for index in range(1, 23)])
def test_each_structural_probe_holds(name, probes):
    assert probes[name]["pass"], json.dumps(probes[name], default=str)[:600]


def test_the_contraction_witnesses_exercise_the_distributive_factor(probes):
    a13, a14 = probes["A13"], probes["A14"]
    assert any(row["arrival_burden"] > 0.0 for row in a13["witnesses"].values())
    assert all(row["factor_is_in_the_bound"] for row in a13["witnesses"].values())
    assert a14["witnesses"], "P2X-1's only witness ran with b0 = 0, where the factor is 1"
    for row in a14["witnesses"].values():
        assert row["distributive_factor"] != 1.0 and row["ratio_matches_the_factor"] and row["under_the_bound"]


def test_every_committed_family_is_identical_to_the_predecessor(probes):
    found = probes["A21"]
    assert found["digests_match_the_predecessor"] and all(found["digests_match_the_predecessor"].values())
    assert found["no_refusal_in_any_committed_course"]
    assert len(found["courses"]) >= 9


# P2X-1A-4 to P2X-1A-7: the criteria can fail ----------------------------------------------------------------------------------

def test_the_contradictions_check_is_executable_and_can_fail(probes):
    intact = cg.contradictions(probes)
    assert intact["pass"] and not intact["inside_certified_scope"]
    broken = {name: dict(row) for name, row in probes.items()}
    broken["A1"] = {"pass": False}
    found = cg.contradictions(broken)
    assert not found["pass"]
    assert any("incompatible_writer_ownership" in item for item in found["inside_certified_scope"])


def test_every_contradiction_row_is_decided_by_a_probe():
    for name, (statement, keys) in cg.CONTRADICTION_CHECKS.items():
        assert keys, name
        assert all(f"A{key[1:]}" in cg.PROBES for key in (k.upper() for k in keys)), name


def test_the_debt_classification_can_fail(probes):
    assert cg.debt_classification(probes)["pass"]
    broken = {name: dict(row) for name, row in probes.items()}
    broken["A4"] = {"pass": False}
    found = cg.debt_classification(broken)
    assert not found["pass"] and found["blockers"]
    assert not found["closure_blockers_resolved"]["P2X1_R_F4_CLAMP_IN_AN_ACCEPTED_MINUTE"]


def test_a_removed_or_misclassified_debt_fails_the_classification(monkeypatch, probes):
    table = {name: dict(items) for name, items in cg.DEBT.items()}
    table["ACCEPTABLE_PHASE2_DEBT"].pop("PRESSURE_TO_TONE")
    monkeypatch.setattr(cg, "DEBT", table)
    found = cg.debt_classification(probes)
    assert not found["pass"] and not found["every_required_entry_classified"]


def test_the_supersession_check_reads_the_artifacts_on_disk(monkeypatch):
    assert cg.supersession()["pass"]
    broken = {name: dict(row) for name, row in cg.HISTORY.items()}
    broken["TD120_HISTORICAL_SUPERSESSION_ACCEPTED"] = dict(broken["TD120_HISTORICAL_SUPERSESSION_ACCEPTED"])
    broken["TD120_HISTORICAL_SUPERSESSION_ACCEPTED"]["historical"] = dict(
        broken["TD120_HISTORICAL_SUPERSESSION_ACCEPTED"]["historical"],
        document="docs/revision/P2S3_ASMA_EN_SOMBRA.md")
    monkeypatch.setattr(cg, "HISTORY", broken)
    found = cg.supersession()
    assert not found["pass"] and found["problems"]
    assert any("does not exist" in problem for problem in found["problems"])


def test_the_names_p2x1_cited_do_not_exist_and_the_ones_here_do():
    """P2X-1's review found two document names in its supersession record that were not in the repository."""
    assert not (ROOT / "docs" / "revision" / "P2S3_ASMA_EN_SOMBRA.md").exists()
    assert not (ROOT / "docs" / "revision" / "P2T3_ASMA_CON_DISTRES.md").exists()
    for row in cg.HISTORY.values():
        for side in ("historical",):
            assert (ROOT / row[side]["document"]).exists(), row[side]["document"]
            assert (ROOT / row[side]["record"]).exists(), row[side]["record"]


def test_the_readiness_rule_reads_the_reversion_result(monkeypatch):
    intact = cg._verdict_from(cg.upstream_unchanged())
    assert intact["verdict"] == cg.READY
    monkeypatch.setattr(cg, "_live", lambda relative: cg._live_text(relative) + "\n# mutated\n")
    mutated = cg._verdict_from(cg.upstream_unchanged())
    assert mutated["verdict"].startswith(cg.NOT_READY) and "upstream" in mutated["blocker"]


def test_every_criterion_blocks_when_its_own_evidence_fails():
    found = cg.run.__wrapped__() if hasattr(cg.run, "__wrapped__") else None
    stub = {"pass": True}
    base = {"guards": stub, "writer_contract": stub, "contradictions": stub, "debt_classification": stub,
            "supersession": stub, "non_regression": stub, "upstream_unchanged": stub,
            "probes": {f"A{index}": stub for index in range(1, 23)}}
    assert cg.readiness(base)["verdict"] == cg.READY
    for statement, keys in cg.READINESS_CRITERIA:
        for key in keys:
            broken = {name: (dict(value) if isinstance(value, dict) else value) for name, value in base.items()}
            broken["probes"] = dict(base["probes"])
            if key in broken["probes"]:
                broken["probes"][key] = {"pass": False}
            else:
                target = {"guards": "guards", "writer_contract": "writer_contract", "contradictions":
                          "contradictions", "debt": "debt_classification", "supersession": "supersession",
                          "non_regression": "non_regression", "upstream": "upstream_unchanged"}[key]
                broken[target] = {"pass": False}
            verdict = cg.readiness(broken)
            assert verdict["verdict"].startswith(cg.NOT_READY), f"{statement} does not read {key}"


def test_no_criterion_is_a_constant():
    source = inspect.getsource(cg.readiness) + inspect.getsource(cg._evidence)
    assert "or True" not in source and "pass\": True" not in source
    for statement, keys in cg.READINESS_CRITERIA:
        assert keys, statement


# The record and the document the evaluation run produced ----------------------------------------------------------------------

@pytest.fixture(scope="module")
def record():
    if not cg.RECORD.exists():
        pytest.skip("the P2X-1A record is written by the evaluation run, after the freeze")
    return json.loads(cg.RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record):
    if FROZEN_DIGEST is not None:
        assert record["freeze_digest"] == FROZEN_DIGEST
    found = cg.run()
    assert record == json.loads(json.dumps(found, sort_keys=True, default=str))


def test_the_document_is_generated_from_the_record(record):
    if not cg.DOCUMENT.exists():
        pytest.skip("the P2X-1A document is written by the evaluation run, after the freeze")
    from clinical_core import closure_guard_report as report
    text = cg.DOCUMENT.read_text(encoding="utf-8")
    for name, (opening, closing) in report.MARKERS.items():
        assert opening in text and closing in text, name
        assert report.RENDERERS[name](record).strip() in text, name
