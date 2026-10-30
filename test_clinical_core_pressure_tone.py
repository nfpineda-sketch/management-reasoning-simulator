"""Phase 2 shadow core, P2J-1: the pressure / vascular-tone structural audit and calibration surface.

These tests pin the structural correction (SBP and DBP proportional to output x tone over the whole range, no knee, no
floor, no new parameter, the gains and the knee unread), the audit of the relation before it (reproduced from the
committed P2I-2Q record), the knee classifier, tone's paths, the pump / tone coupling, zero output and arrest, the
authored pressures and the arrival reconstruction, the pressure path's independence from demand, D and HR, the P3
comparator, the frozen candidate surface and the policy; nothing is approved, and pressure does not feed HR.
"""
import ast
import hashlib
import inspect
import json
from dataclasses import replace

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import calibration, decision_pack, gi_reference, lactate_slice
from clinical_core import hr_primary as hp
from clinical_core import lactate_adequacy as la
from clinical_core import lactate_rebuild as lr
from clinical_core import pressure_tone as pt
from clinical_core.bands import ARRIVAL
from clinical_core.derived import DEFAULT_PROFILE, PARAMETERS, arterial_pressures
from clinical_core.state import Anchors

ROOT = pt.ROOT
SOURCE = ROOT / "clinical_core" / "pressure_tone.py"
#: The P2J-1 freeze: faculty decisions, the P2I-2AK record, the equations, the knee and tone rules, the candidate
#: surface and its range rule, the scenarios, the directions, identifiability, the dependency rule, the baroreflex
#: plan, the verdict rule, the policy and every clinical_core source but the downstream reports, committed before any
#: trajectory on the retained physiology was read.
FROZEN_DIGEST = "92aa42cbf18d6f2e4e3a978babbd8a4b0f8dd8a1058a8d6bde4b2592ac3f4091"
C57, C72 = pt.C57, pt.C72
NEUTRAL = Anchors(**ARRIVAL)


@pytest.fixture(scope="module")
def source():
    record = la.record_p2i2ab()
    return la.source_space(record), record["crystalloid_support"]


# The frozen package ------------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert "clinical_core/pressure_tone.py" in sources
    assert "clinical_core/pressure_tone_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert {"clinical_core/pressure_tone.py", "clinical_core/pressure_tone_report.py"} <= set(
        decision_pack.PACK_DIGEST_EXCLUDED)
    assert pt.p2i2ak_record()["freeze_digest"] == pt.P2I2AK_DIGEST
    assert pt.freeze_digest() == FROZEN_DIGEST, "a source, the design, a rule or the policy changed after the freeze"


def test_the_faculty_decisions_are_recorded():
    assert set(pt.FACULTY) == {"decided", "hr", "demand", "pressure_to_hr", "structure", "correction", "scope"}
    assert "PRESSURE_TERM_DIAGNOSTIC_ONLY" in pt.FACULTY["pressure_to_hr"]
    assert "CURRENTLY_COMPATIBLE" in pt.FACULTY["demand"]


# The structural correction ------------------------------------------------------------------------------------------

@pytest.mark.parametrize("arrival", [NEUTRAL, gi_reference.canonical_anchors(C57), gi_reference.canonical_anchors(C72),
                                     Anchors(**{**ARRIVAL, "sbp": 70.0, "dbp": 66.0})])
def test_pressure_is_the_arrival_pressure_times_output_x_tone_everywhere(arrival):
    for p in [i * 0.01 for i in range(301)]:
        sbp, dbp = arterial_pressures(p, arrival, DEFAULT_PROFILE)
        assert sbp == arrival.sbp * p and dbp == arrival.dbp * p and sbp >= dbp >= 0.0
    assert arterial_pressures(0.0, arrival, DEFAULT_PROFILE) == (0.0, 0.0)
    # The adopted gains and the knee stay in the profile, unread.
    other = replace(DEFAULT_PROFILE, sbp_per_pressure_deficit=10.0, dbp_per_pressure_deficit=5.0,
                    low_output_pressure_knee=0.2)
    assert all(arterial_pressures(p, arrival, other) == arterial_pressures(p, arrival, DEFAULT_PROFILE)
               for p in (0.1, 0.5, 1.0, 1.7))


def test_p2j1_changed_only_the_declared_statements_of_derived_and_shadow():
    assert pt.outside_unchanged() == {pt.DERIVED: True, pt.SHADOW: True}
    text = (ROOT / pt.DERIVED).read_text(encoding="utf-8")
    assert pt.outside_digest(pt.DERIVED, text.replace("OUTPUT_EPSILON = 1e-9", "OUTPUT_EPSILON = 1e-8")) != \
        pt.P2J1_CHANGES[pt.DERIVED]["outside"], "the proof must notice a change outside the pressure relation"
    shadow = (ROOT / pt.SHADOW).read_text(encoding="utf-8")
    assert pt.outside_digest(pt.SHADOW, shadow.replace('UNRESOLVED = "MATCH",', 'UNRESOLVED = "SAME",')) != \
        pt.P2J1_CHANGES[pt.SHADOW]["outside"], "the proof must notice a change outside the golden's registry"
    for relative, item in pt.P2J1_CHANGES.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != item["sha_at_p2i2ak"]
    sources = {pt.DERIVED: "live", pt.SHADOW: "live", "clinical_core/state.py": "s"}
    assert pt.pressure_only_sources(sources) == {pt.DERIVED: pt.P2J1_CHANGES[pt.DERIVED]["sha_at_p2i2ak"],
                                                 pt.SHADOW: pt.P2J1_CHANGES[pt.SHADOW]["sha_at_p2i2ak"],
                                                 "clinical_core/state.py": "s"}
    for name in ("sbp_per_pressure_deficit", "dbp_per_pressure_deficit", "low_output_pressure_knee"):
        assert "Since P2J-1 the core does not read it" in PARAMETERS[name][1]


def test_the_prior_relation_is_the_one_the_p2i2q_record_measured():
    assert pt.prior_matches_p2i2q() == {"max_difference": 0.0, "equal": True}
    assert pt.prior_pressures(1.0, NEUTRAL) == (120.0, 75.0) and pt.prior_pressures(0.8, NEUTRAL) == (111.0, 70.0)
    assert pt.prior_pressures(0.1, NEUTRAL) == pytest.approx((19.5, 12.5))


def test_the_knee_is_classified_on_fixed_states():
    audit = pt.knee_audit()
    ratios = {"GI 57m": 131.0 / 45.0, "GI 72f": 151.0 / 45.0, "neutral arrival": 195.0 / 45.0}
    for name, item in audit.items():
        prior, current = item["prior"], item["current"]
        assert prior["classification"] == "CONTINUOUS_WITH_KNEE" and not prior["value_jumps"]
        assert {k["p"] for k in prior["kinks"]} == {0.5} and prior["value_at_zero"] == 0.0
        assert item["prior_slopes_at_knee"]["SBP"]["ratio"] == pytest.approx(ratios[name], rel=1e-6)
        assert prior["implicit_resistance"]["0.5"] > 1.5 and prior["implicit_resistance"]["2"] < 0.75
        assert current["classification"] == "CONTINUOUS_AND_SMOOTH" and not current["kinks"]
        assert all(v == pytest.approx(1.0, abs=1e-12) for v in current["implicit_resistance"].values())


def test_the_classifier_tells_a_jump_and_a_floor_apart():
    jump = pt.classify_mapping(lambda p, a: (a.sbp * p + (10.0 if p > 0.7 else 0.0),
                                             a.dbp * p + (10.0 if p > 0.7 else 0.0)), NEUTRAL)
    floor = pt.classify_mapping(lambda p, a: (40.0 + a.sbp * p, 20.0 + a.dbp * p), NEUTRAL)
    smooth_curve = pt.classify_mapping(lambda p, a: (a.sbp * p ** 0.8, a.dbp * p ** 0.8), NEUTRAL)
    assert jump["classification"] == "DISCONTINUOUS" and floor["classification"] == "OTHER"
    assert smooth_curve["classification"] == "CONTINUOUS_AND_SMOOTH"


# Tone, coupling, zero output ----------------------------------------------------------------------------------------

def test_tone_is_read_in_output_and_pressure_and_no_clinical_mechanism_writes_it():
    paths = pt.tone_paths()
    assert ["clinical_core/derived.py", "_perfusion", ".T"] in paths["reads"]
    assert not paths["clinical_writers"]
    writers = {w[0] for w in paths["writes"]}
    assert writers <= set(pt.PROBE_MODULES) | {"clinical_core/state.py"}
    assert not any(w[0].startswith(("clinical_core/modules", "clinical_core/interventions")) for w in paths["writes"])


def test_the_pump_tone_coupling_is_coherent_at_every_afterload_point():
    probes = pt.coupling_probes()
    assert all(all(flag for flag in group.values()) for name, group in probes["coupling"].items()
               if isinstance(group, dict))
    assert pt.AFTERLOAD == tuple(calibration.REGISTRY["afterload_sensitivity"].points()) == (0.1, 0.3, 0.5)
    assert all(pt._tone_admissible(point) for point in probes["P5"].values())
    fixed = probes["P5"]["0.3"]["fixed_output"]
    assert all(row["output"] == pytest.approx(1.0) for row in fixed.values())
    assert fixed["2"]["map"] == pytest.approx(2.0 * fixed["1"]["map"])


def test_zero_output_stops_the_run_and_arrest_shows_no_pressure():
    probe = pt.zero_output_probe()
    assert probe["holds"] and probe["numerical_zero_with_pulse"] == "UNRESOLVED_BOUNDARY"
    assert probe["small_output"]["1e-06 at T 3"]["map"] < 1e-3
    assert set(probe["pulseless"]) == {"pea", "asystole", "vf"}


# Authored pressures, arrival, dependency ---------------------------------------------------------------------------

def test_the_authored_pressures_are_arrival_only_and_the_arrival_is_reproduced_by_construction():
    authored = pt.authored_pressures()
    assert (authored[C57]["sbp"]["value"], authored[C57]["dbp"]["value"]) == (88, 54)
    assert (authored[C72]["sbp"]["value"], authored[C72]["dbp"]["value"]) == (98, 62)
    assert all(item["later"] == [] and item["map"]["kind"] == pt.DERIVED_FROM_AUTHORED for item in authored.values())
    arrival = pt.arrival_reconstruction()
    assert set(arrival) == {f"{c} x{f:g}" for f in pt.DEMANDS for c in pt.CASES}
    assert all(row["mismatch"] == [0.0, 0.0, 0.0] and row["output"] == 1.0 for row in arrival.values())
    assert arrival[f"{C57} x1"]["D0"] == 60.0 and arrival[f"{C72} x1"]["D0"] == 20.0
    assert arrival[f"{C57} x1"]["map"] == pytest.approx(196.0 / 3.0)


def test_the_pressure_path_reads_no_demand_debt_or_heart_rate():
    path = pt.path_reads()
    assert not path["forbidden_read"] and not path["contributors_reading_derived"]
    assert {"T", "P", "V", "output_factor", "afterload_sensitivity"} <= set(path["reads"])


def test_the_p3_comparator_omits_only_the_haemostasis(source):
    space, _ = source
    for case in pt.CASES:
        values = lr.blood_values(space["p3"][0], case)
        from clinical_core import blood_anchors
        _, _, full = blood_anchors.setup(case, **values)
        l3 = [type(i).__name__ for i in lr.scenario_items(case, pt.L3, full)]
        p3 = [type(i).__name__ for i in pt.scenario_items(case, pt.NO_HAEMOSTASIS, full)]
        assert p3 == [name for name in l3 if name != "EndoscopicHemostasis"] and len(l3) == len(p3) + 1
        with_, without = pt.pressure_run(space["p3"][0], case, pt.L3), pt.pressure_run(space["p3"][0], case,
                                                                                       pt.NO_HAEMOSTASIS)
        h = with_["controlled_at"]
        assert h == 60 and without["controlled_at"] is None
        assert with_["rows"][:h] == without["rows"][:h] and with_["rows"][h] != without["rows"][h]


def test_pressure_is_the_same_at_both_demands_any_lactate_side_and_any_hr_profile(source):
    space, support = source
    case, q = C57, 0
    reference = pt.pressure_run(space["p3"][q], case, pt.L3)["rows"]
    runs = [pt.full_run(space["p3"][q], case, pt.L3, f, pt.LAMBDAS[0]) for f in pt.DEMANDS]
    runs.append(pt.full_run(space["p3"][q], case, pt.L3, 1.0, pt.LAMBDAS[-1]))
    for intrinsic, changes in pt.HR_VARIANTS.values():
        runs.append(pt.full_run(space["p3"][q], case, pt.L3, 1.0, pt.LAMBDAS[0], None, intrinsic, changes))
    for run_ in runs:
        assert all(row[f] == ref[f] for row, ref in zip(run_["rows"], reference) for f in pt.COMPARED)
    assert any(x["D"] != y["D"] for x, y in zip(runs[0]["rows"], runs[1]["rows"])), "demand reaches D"
    assert any(x["hr"] != y["hr"] for x, y in zip(runs[0]["rows"], runs[3]["rows"])), "the HR profile reaches HR"


# Candidate surface, policy, verdict ---------------------------------------------------------------------------------

def test_the_candidate_surface_is_frozen_with_no_free_mapping_parameter():
    surface = pt.CANDIDATE_SURFACE
    assert surface["mapping"]["free_parameters"] == []
    assert surface["afterload_sensitivity"]["points"] == [0.1, 0.3, 0.5]
    assert surface["tone_response"]["status"].startswith("NOT_AUTHORIZED")
    assert surface["tone_reference"]["value"] == 1.0 and "never reopened" in surface["upstream"]
    assert "No GI trajectory and no legacy pressure" in pt.RANGE_RULE


def test_no_legacy_no_p2f_no_pressure_feedback_and_nothing_approved():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names}
    assert not imported & {"shadow", "legacy_adapter", "comparison", "family_engine", "contracts_shadow",
                           "contracts_legacy", "hemodynamic_probes"}
    assert "with lr.P2FGuard(), lr.LegacyLock():" in inspect.getsource(pt.run)
    assert hp.PRIMARY_HR_CALIBRATION == {"sympathetic_per_pressure_deficit": 0.0}
    assert pt.BAROREFLEX_PLAN["status"].startswith("PLAN_ONLY")
    text = json.dumps(pt.design(), default=str).lower()
    for word in ("faculty_approved", "\"best", "\"selected", "\"recommended", "\"preferred", "\"rank"):
        assert word not in text


def _checks_input(**overrides):
    audit = pt.knee_audit()
    coupling, zero = pt.coupling_probes(), pt.zero_output_probe()
    arrival = pt.arrival_reconstruction()
    reuse = {"units_equal": True, "outside_unchanged": {pt.DERIVED: True, pt.SHADOW: True}}
    dependency, path = {"pressure_equal": True}, pt.path_reads()
    invariants = {k: {"holds": True} for k in ("1", "2", "3", "4", "5", "7", "8")}
    values = dict(audit=audit, tone=pt.tone_paths(), coupling=coupling, zero=zero, arrival=arrival, reuse=reuse,
                  dependency=dependency, path=path, invariants=invariants)
    values.update(overrides)
    return values


def test_the_verdict_follows_its_checks():
    assert pt.verdict(**_checks_input())["verdict"] == pt.READY
    blocked = pt.verdict(**_checks_input(dependency={"pressure_equal": False}))
    assert blocked["verdict"] == f"{pt.NOT_READY} — upstream_unchanged" and blocked["approved"] == []
    kinked = pt.knee_audit()
    for item in kinked.values():
        item["current"] = item["prior"]
    assert pt.verdict(**_checks_input(audit=kinked))["verdict"] == f"{pt.NOT_READY} — mapping_coherent"


# The evaluation, on the frozen package (freeze 31a74ef) ---------------------------------------------------------------

RECORD = ROOT / "docs" / "revision" / "P2J1_pressure_tone.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2J1_PRESION_Y_TONO_VASCULAR.md"


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_its_analytic_part_is_reproduced_live(record):
    assert record["freeze_digest"] == FROZEN_DIGEST and record["record"] == pt.P2I2AK_DIGEST
    # The trajectories (minutes of physiology) are not re-run here; the audit and the probes are.
    assert record["knee"] == _json(pt.knee_audit()) and record["prior_matches_p2i2q"]["equal"]
    assert record["tone"] == _json(pt.tone_paths()) and record["coupling"] == _json(pt.coupling_probes())
    assert record["zero_output"] == _json(pt.zero_output_probe())
    assert record["authored"] == _json(pt.authored_pressures())
    assert record["arrival"] == _json(pt.arrival_reconstruction()) and record["path"] == _json(pt.path_reads())
    assert record["candidate_surface"] == _json(pt.CANDIDATE_SURFACE)


def test_the_reuse_and_the_dependency_proof_the_report_states(record):
    assert record["reuse"]["units_digests"] == {"1": pt.UNITS[1.0], "1.1": pt.UNITS[1.1]}
    assert record["reuse"]["units_equal"] and all(record["reuse"]["outside_unchanged"].values())
    assert record["blood_sets"] == {"P1": 37, "P2": 444, "P3": 91, "P4": 91}
    dependency = record["dependency"]
    assert dependency["pressure_equal"] and dependency["d_moves_with_demand"] and dependency["full_runs"] == 240
    assert record["efficiency"]["pressure_runs"] == 1326 and not record["efficiency"]["legacy_read"]


def test_the_directions_and_the_verdict_the_report_states(record):
    d = record["directions"]
    assert all(d[k]["holds"] for k in ("1", "2", "3", "4", "5", "7", "8"))
    assert (d["5"]["blood_sets"], d["5"]["failing"]) == (74, 0)
    assert (d["6"]["improved"], d["6"]["blood_sets"]) == (182, 182) and d["7"]["haemostasis_minute"] == [60]
    verdict = record["verdict"]
    assert verdict["verdict"] == pt.READY and all(verdict["checks"].values()) and verdict["approved"] == []


def test_the_trajectories_the_report_states(record):
    t = record["trajectories"]
    for name in pt.SCENARIOS:
        for case in pt.CASES:
            for item in t[f"{name} {case}"]["times"].values():
                assert item["T"]["low"] == item["T"]["high"] == 1.0
            assert t[f"{name} {case}"]["stops"] == 0
    untreated, definitive = t[f"P1 {C57}"]["times"], t[f"P4 {C57}"]["times"]
    assert untreated["0"]["map"]["median"] == pytest.approx(196.0 / 3.0)
    assert untreated["120"]["map"]["high"] < untreated["120"]["map_prior"]["low"], "the hidden tone no longer buffers"
    assert round(untreated["120"]["sbp"]["median"]) == 44 and round(definitive["120"]["map"]["median"]) == 101
    assert round(t[f"P4 {C72}"]["times"]["120"]["sbp"]["median"]) == 133
    changed = record["changed"]
    assert changed["arrival_unchanged"] and changed["largest_change_mmhg"]["map"] < 25.0


def test_the_document_is_generated_from_the_record(tmp_path):
    from clinical_core import pressure_tone_report
    copy = tmp_path / "document.md"
    copy.write_text(DOCUMENT.read_text(encoding="utf-8"), encoding="utf-8")
    pressure_tone_report.main(["--write", str(copy), "--data", str(RECORD)])
    assert copy.read_text(encoding="utf-8") == DOCUMENT.read_text(encoding="utf-8"), "regenerate the document"
