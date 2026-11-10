"""P3-6, P3-8 and P3-9: the region ensemble, the non-authoritative diagnostics and the research trace.

E1-E10 (ensemble), C1-C8 (consciousness and collapse diagnostics) and the trace checks. The boundary is the
same one P3-1 set: the legacy engine decides everything the resident sees, and nothing here can change it.
"""
import json
from pathlib import Path

import pytest

import runtime_shadow as rs
import runtime_shadow_families as fam

ROOT = Path(__file__).resolve().parent
GI = ("gi_bleed", "gi_bleed_57m")
ACS = ("acs", "acs_70f_left_main")


@pytest.fixture(scope="module")
def acs_ensemble():
    return fam.ensemble(*ACS, 60)


# -- P3-6: E1-E10 --------------------------------------------------------------------------------------------

def test_e1_a_snapshot_is_immutable_and_declares_where_each_value_comes_from(acs_ensemble):
    import dataclasses
    for snapshot in acs_ensemble.snapshots:
        assert snapshot["approved"] is False and snapshot["provenance"]
    frozen = fam.ADAPTERS["acs"].snapshot("upper")
    with pytest.raises(dataclasses.FrozenInstanceError):
        frozen.point = "other"
    with pytest.raises(dataclasses.FrozenInstanceError):
        frozen.provenance = ()
    # to_dict hands out a copy: changing it cannot change the snapshot
    data = frozen.to_dict()
    data["provenance"].clear()
    assert frozen.to_dict()["provenance"] == list(frozen.provenance)


def test_e2_e3_the_same_witnesses_are_deterministic_and_order_does_not_matter(acs_ensemble):
    again = fam.ensemble(*ACS, 60)
    assert {point: runner.digests() for point, runner in again.runs.items()} == \
           {point: runner.digests() for point, runner in acs_ensemble.runs.items()}
    reversed_order = fam.ensemble(*ACS, 60, points=tuple(reversed(fam.POINTS)))
    assert {point: runner.digests() for point, runner in reversed_order.runs.items()} == \
           {point: runner.digests() for point, runner in acs_ensemble.runs.items()}
    assert reversed_order.envelope == acs_ensemble.envelope


def test_e4_the_actions_are_applied_once_for_every_snapshot():
    event = rs.MirroredAction("m000-0-fluid", 0, "fluid", {"volume_ml": 1000.0}, {}, 0.21)
    result = fam.ensemble(*GI, 20, points=(fam.COMMITTED,), mirrored=[event])
    runner = result.runs[fam.COMMITTED]
    assert [item.order_id for item in runner.mirrored] == ["m000-0-fluid"]
    many = fam.ensemble(*ACS, 20, mirrored=[event])
    for runner in many.runs.values():
        assert [item.order_id for item in runner.mirrored] == ["m000-0-fluid"]


def test_e5_n_witnesses_give_n_independent_results(acs_ensemble):
    assert sorted(acs_ensemble.runs) == sorted(fam.POINTS)
    digests = {point: runner.digests()[-1] for point, runner in acs_ensemble.runs.items()}
    assert len(set(digests.values())) == 3, digests


def test_e6_the_phase2_digest_is_untouched_by_an_ensemble(acs_ensemble):
    import hashlib
    paths = sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "clinical_core").rglob("*.py")
                   if "__pycache__" not in path.parts and path.is_file() and not path.name.startswith("."))
    sources = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}
    # PHASE2_AMENDMENT_1: the live tree is the closure's successor. What must be unchanged is the closure itself:
    # it is rebuilt from these same live sources by reversing the successor's declared insertions.
    from clinical_core import amendment_1 as a1
    assert hashlib.sha256(json.dumps(a1.p2x1a_sources(sources), sort_keys=True).encode()).hexdigest() == rs.PHASE2_DIGEST
    assert hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest() == rs.CORE_LINEAGE[-1].digest


def test_e7_e8_an_ensemble_touches_no_authoritative_state():
    from clinical_core import legacy_adapter
    case = legacy_adapter.bank_case("gi_bleed_57m")
    before = json.dumps(case, sort_keys=True, default=str)
    fam.ensemble(*GI, 20, state=case)
    assert json.dumps(case, sort_keys=True, default=str) == before


def test_e9_the_envelope_contains_every_witness_trajectory(acs_ensemble):
    """Checked against witnesses recomputed by an independent replay, not against the same comprehension."""
    independent = {}
    for point in acs_ensemble.points:
        runner = fam.ShadowPhysiologyRunner.open(*ACS, point=point)
        runner.advance(60)
        independent[point] = fam.replay_shadow_encounter(runner.replay_input())["results"]
    widths = 0
    for name, rows in acs_ensemble.envelope.items():
        for minute, (low, high, structural) in rows.items():
            values = [row["derived"].get(name) for results in independent.values() for row in results
                      if row["minute"] == minute]
            numeric = [value for value in values if isinstance(value, (int, float))
                       and not isinstance(value, bool)]
            assert numeric, (name, minute)
            assert low == pytest.approx(min(numeric)) and high == pytest.approx(max(numeric))
            if structural is not None:
                assert low <= structural <= high
            if high > low:
                widths += 1
    assert widths, "the witnesses of a region must give an envelope of non-zero width somewhere"


def test_e10_no_point_is_labelled_approved_and_a_matrix_is_refused():
    for family, adapter in fam.ADAPTERS.items():
        for point in fam.POINTS:
            assert adapter.snapshot(point).approved is False
    with pytest.raises(ValueError):
        fam.ensemble(*ACS, 10, points=("made_up",))
    # An unknown name is dropped, never run: only named, certified witnesses reach the core.
    narrowed = fam.ensemble(*ACS, 10, points=("lower", "made_up"))
    assert narrowed.points == ("lower",) and sorted(narrowed.runs) == ["lower"]


def test_the_legacy_reading_against_the_region_is_a_position_not_a_verdict(acs_ensemble):
    import pilot_acceptance
    from clinical_core import legacy_adapter
    # A launched encounter of the same case, so the legacy reading is the engine's own, not a reconstruction.
    legacy = legacy_adapter.snapshot(pilot_acceptance.Encounter(ACS[1]).state)
    reading = fam.legacy_against_region(legacy, acs_ensemble, 60)
    assert set(reading) >= {"sbp", "hr", "spo2"}
    assert all(row["status"] in (fam.WITHIN, fam.OUTSIDE, fam.REGION_DISABLED, fam.NOT_COMPARABLE)
               for row in reading.values())
    for row in reading.values():
        if row["status"] in (fam.WITHIN, fam.OUTSIDE):
            assert row["region"][0] <= row["region"][1]


# -- P3-8: C1-C8 ---------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def diagnostics():
    runner = fam.ShadowPhysiologyRunner.open(*GI)
    runner.advance(30)
    return runner, fam.shadow_diagnostics(runner, 30)


def test_c1_c2_the_diagnostic_emits_no_category_and_no_arrest(diagnostics):
    _runner, out = diagnostics
    assert out["authority"] == "none" and out["label"] == fam.NONAUTHORITATIVE
    assert out["consciousness"]["mental_status_category"] is None
    assert out["collapse"]["terminal_transition"] is None and out["collapse"]["collapse_burden"] is None
    assert "pending faculty" in out["consciousness"]["category_status"]


def test_c3_the_diagnostic_is_deterministic(diagnostics):
    runner, out = diagnostics
    assert json.dumps(fam.shadow_diagnostics(runner, 30), sort_keys=True, default=str) == \
           json.dumps(out, sort_keys=True, default=str)


def test_c4_c5_c6_the_diagnostic_has_no_path_into_authority(diagnostics):
    _runner, out = diagnostics
    assert sorted(out) == ["authority", "available", "collapse", "consciousness", "label",
                           "legacy_comparison", "minute"]
    text = json.dumps(out, default=str)
    for forbidden in ("family_state", "ledger", "order_id", "score", '"fate"'):
        assert forbidden not in text, forbidden
    source = (ROOT / "runtime_shadow_families.py").read_text(encoding="utf-8")
    assert "shadow_diagnostics" not in (ROOT / "app.py").read_text(encoding="utf-8")
    assert "shadow_diagnostics" not in (ROOT / "pilot_acceptance.py").read_text(encoding="utf-8")
    assert source.count("def shadow_diagnostics") == 1


def test_c7_hypercapnia_and_hypoxaemia_stay_distinct_signals(diagnostics):
    _runner, out = diagnostics
    readings = out["consciousness"]["signal_readings"]
    assert set(readings) == {"cerebral_hypoperfusion", "oxygen_deficit", "hypoxaemia", "acidemia",
                             "hypercapnia", "hypoglycaemia"}
    assert out["consciousness"]["signals_mapped"] is False, "no bound is committed: S is a lower bound"


def test_c8_n_is_primary_neurologic_only(diagnostics):
    _runner, out = diagnostics
    from clinical_core import encephalopathy as en
    assert "PRIMARY_NEUROLOGIC_STATE" in en.STATUS["N"]
    assert out["consciousness"]["systemic_encephalopathy_burden"] == 0.0
    assert out["consciousness"]["primary_neurologic_impairment"] >= 0.0


def test_the_collapse_diagnostic_says_which_signal_is_unmapped(diagnostics):
    _runner, out = diagnostics
    assert out["collapse"]["perfusion_failure_signal"] is None
    assert "UNSET" in out["collapse"]["perfusion_mapping_status"]
    assert isinstance(out["collapse"]["oxygen_delivery_failure_signal"], float)
    assert "ROSC_NOT_CURRENTLY_MODELED" in out["collapse"]["rosc"]


# -- P3-9: the research trace --------------------------------------------------------------------------------

def test_the_research_trace_is_faculty_only_and_carries_its_join_keys(diagnostics):
    runner, _out = diagnostics
    trace = fam.research_trace(runner)
    assert trace["resident_visible"] is False and trace["runtime_authority"] == "legacy"
    assert trace["join_keys"] == list(fam.JOIN_KEYS)
    assert len(trace["rows"]) == len(runner.results)
    assert trace["replay_digest"] and trace["versions"]["phase2_digest"] == rs.PHASE2_DIGEST
    assert "not clinical ground truth" in trace["summary"]["reading"]


def test_the_minimal_trace_is_much_smaller_than_the_verbose_one(diagnostics):
    runner, _out = diagnostics
    sizes = fam.artifact_sizes(runner)
    assert sizes["minimal_trace_bytes"] < sizes["verbose_trace_bytes"]
    assert sizes["recommended_default"] == "minimal_trace"
    assert sizes["replay_input_bytes"] > 0


def test_the_summary_counts_only_what_it_compared():
    runner = fam.ShadowPhysiologyRunner.open(*GI)
    runner.advance(10)
    summary = fam.difference_summary(runner)
    assert summary["minutes"] == 10 and summary["compared_minutes"] == 0, "no legacy snapshot was given"
    assert summary["by_status"] == {} and summary["parameter_uncertainty"]


# -- what the adversarial review of 2026-11-07 found ---------------------------------------------------------

def test_a_region_of_width_zero_is_declared_disabled_variable_by_variable():
    """A band of width zero is never dressed as a region, whatever the family or the variable.

    Since P3-11 GI reads the declared calibration region, so some of its variables DO span a band and get a
    position. The claim this test defends is the other half: where the band has no width, the reading is
    COMMON_REGION_DISABLED and not "the legacy value is outside the region".
    """
    from clinical_core import legacy_adapter
    import pilot_acceptance
    result = fam.ensemble(*GI, 20)
    legacy = legacy_adapter.snapshot(pilot_acceptance.Encounter(GI[1]).state)
    reading = fam.legacy_against_region(legacy, result, 20)
    assert reading, "the reading must cover the display variables"
    pairs = {"sbp": "sbp", "dbp": "dbp", "map": "map", "hr": "pulse_rate_bpm", "spo2": "spo2",
             "respiratory_rate": "respiratory_rate", "crt": "crt_s"}
    for name, row in reading.items():
        band = (result.envelope.get(pairs[name]) or {}).get(20)
        if row["status"] == fam.NOT_COMPARABLE:
            continue
        low, high, _structural = band
        if low == high:
            assert row["status"] == fam.REGION_DISABLED, (name, row, band)
        else:
            assert row["status"] in (fam.WITHIN, fam.OUTSIDE), (name, row, band)
    assert any(row["status"] == fam.REGION_DISABLED for row in reading.values()), reading


def test_the_asthma_witness_is_not_the_no_worsening_sentinel():
    from clinical_core import asthma_migration as sm
    lower = fam.ADAPTERS["asthma"].writers("asthma_49m", "lower")[0]
    assert sm.WORSENING_PER_MIN[0] == 0.0, "this test exists because index 0 is the sentinel"
    assert lower.worsening_per_min == sm.WORSENING_PER_MIN[1] > 0.0
    text = fam.ADAPTERS["asthma"].snapshot("lower").provenance[0]
    assert "WORSENING_PER_MIN[1]" in text and "sentinel" in text


def test_no_adapter_invents_a_magnitude_as_a_fallback():
    import ast
    source = (ROOT / "runtime_shadow_families.py").read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "getattr" and len(node.args) == 3:
            assert False, f"a getattr fallback could invent a magnitude: line {node.lineno}"


def test_the_trace_carries_the_ledger_identity_it_promises_to_join_on():
    import pilot_acceptance
    import os
    kept = os.environ.get(rs.FLAG)
    os.environ[rs.FLAG] = rs.MODE_SHADOW_COMPARE
    try:
        encounter = pilot_acceptance.Encounter(GI[1])
        encounter.order("Start pantoprazole 80 mg IV. Reassess in 5 minutes.")
    finally:
        os.environ.pop(rs.FLAG, None)
        if kept is not None:
            os.environ[rs.FLAG] = kept
    mirrored = encounter.shadow.record()["mirrored"]
    assert mirrored and all(item["submission_id"] for item in mirrored), mirrored
    ledger = {order["order_id"] for order in encounter.entries[0]["orders"]}
    assert any(item["order_id"] in ledger for item in mirrored), (mirrored, ledger)


def test_the_golden_only_explains_what_it_declares_in_every_scenario():
    """The review's finding: the union over 20 scenarios silenced consciousness_level, declared in 1."""
    explained, counts = rs.golden_explained("gi_bleed"), rs.golden_partial("gi_bleed")
    total = max(total for _seen, total in counts.values())
    assert total == 20
    assert counts["consciousness_level"] == (1, 20) and "consciousness_level" not in explained
    assert counts["V_ml_eq"][0] < total and "V_ml_eq" not in explained
    assert set(explained) == {name for name, (seen, _total) in counts.items() if seen == total}
    from clinical_core import comparison
    for name in ("consciousness_level", "V_ml_eq", "crt_s", "hr"):
        variable = next(item for item in comparison.VARIABLES if item.name == name)
        assert rs._classify(variable, 1.0, "gi_bleed") == rs.PARTIALLY_EXPLAINED, name
    # A variable the golden never declares stays loud, which is where a mapping fault shows.
    delivered = next(item for item in comparison.VARIABLES if item.name == "fluid_delivered_ml")
    assert rs._classify(delivered, 1.0, "gi_bleed") == rs.UNEXPECTED


def test_the_collapse_signal_goes_through_the_phase2_guard(diagnostics):
    _runner, out = diagnostics
    source = (ROOT / "runtime_shadow_families.py").read_text(encoding="utf-8")
    assert "co.delivery_failure(" in source
    assert isinstance(out["collapse"]["oxygen_delivery_failure_signal"], float)
    assert 0.0 <= out["collapse"]["oxygen_delivery_failure_signal"] <= 1.0


def test_the_consciousness_diagnostic_declares_that_zero_is_a_lower_bound(diagnostics):
    _runner, out = diagnostics
    consciousness = out["consciousness"]
    assert "LOWER BOUND" in consciousness["reading_note"]
    assert consciousness["signals_available"]["acidemia"] is False
    assert consciousness["signals_available"]["hypercapnia"] is False
    assert any("availability" in str(item) or "lower bound" in str(item)
               for item in consciousness["limitations"])
