"""P3-338 to P3-348: the joint GI region formalised, its witnesses, and the blinded candidate package for a human re-review.

What is protected, and kept apart:

* MODEL_ANALYSIS / TEST_RESULT: ``test_gi_joint_region`` is recomputed from the executable model and the frozen faculty evaluators and compared with the stored
  record, the stored blinded review set, the stored key and the review kit on disk;
* the faculty decisions FD-RATE-14 to FD-RATE-20 are applied as given: the complete-unit reading, no optimisation toward a window's centre, a rate that never
  stands apart from its scale, the old CANDIDATE band audited before a region outside it is formalised;
* the candidates are for a NEW blinded human review: the reviewer's view carries no parameter, no witness name and no legacy number, the earlier human review
  is byte-identical, and nothing here answers for a reviewer;
* what was NOT done: no executable change, no point chosen as a calibration, no Amendment 3, no change of the closed crystalloid region, no norepinephrine,
  no source control.

``MRS_WRITE_JOINT_REGION=1 python3 test_gi_joint_region.py`` regenerates the stored records and the kit, only when the analysis itself changes.
"""
import copy
import dataclasses
import hashlib
import json
import subprocess
import types
from pathlib import Path

import pytest

import faculty_trajectory_review as ftr
import test_gi_frg_crystalloid_analysis as fa
import test_gi_joint_feasibility_analysis as gj
import test_gi_joint_region as jr

ROOT = Path(__file__).resolve().parent
REVISION = ROOT / "docs" / "revision"
HUMAN_DIGEST = "9ba80fa70d3b38e178caa3aca9432f9227ce6d9591a48c9908c3f5ac4cc6c8d3"
FEASIBILITY_RECORD_DIGEST = "2ca6bc534f55508209459c834819c4269b59bbd60ec27ee905dcbd289187f059"
P3_336_DIGEST = "f18e181b3a4767384f34c90fb3bb0d483762eda3951434a480f1ffd5b7b601eb"
P3_325_DIGEST = "3198f62afd98655768e38e3e2ccceb226fe6cf842655c8b899d90ce4318d94f3"
P3_313_DIGEST = "093262fa98e9a4a476ad6005b1c5c6954858ddafd380ad8538c7c7e9bb644bf5"
CORE_DIGEST = "a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2"
FIRST_PASS_FILES = ("README.md", "conjunto_1.md", "conjunto_2.md", "conjunto_3.md", "formulario_respuestas.md")
KEY_FILE = "ABRIR_DESPUES_DE_LA_PRIMERA_PASADA.md"


def _sealed(record: dict) -> str:
    body = {key: value for key, value in record.items() if key != "record_digest"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def built() -> dict:
    return jr.build()


@pytest.fixture(scope="module")
def record(built) -> dict:
    return built["record"]


def test_a1_the_stored_record_the_review_set_the_key_and_the_kit_are_exactly_what_the_model_gives_now(built):
    stored = jr.load_record()
    assert built["record"]["record_digest"] == stored["record_digest"] == jr.digest(stored), "regenerate with MRS_WRITE_JOINT_REGION=1 only when the analysis itself changes"
    assert stored["evidence_class"] == "MODEL_ANALYSIS" and stored["executable_change"] is False
    for path, name in ((jr.REVIEW_SET_PATH, "review_set"), (jr.BLIND_KEY_PATH, "blind_key")):
        on_disk = _load(path)
        assert on_disk["record_digest"] == built[name]["record_digest"] == _sealed(on_disk), name
    assert sorted(path.name for path in jr.KIT_DIR.iterdir()) == sorted(built["kit"])
    for name, text in built["kit"].items():
        assert (jr.KIT_DIR / name).read_text(encoding="utf-8") == (text if text.endswith("\n") else text + "\n"), name
    assert stored["depends_on"]["joint_feasibility_record_digest"] == FEASIBILITY_RECORD_DIGEST == gj.load_record()["record_digest"]


def test_a2_the_faculty_decisions_are_applied_as_given(record):
    applied = record["faculty_decisions_applied"]
    assert sorted(applied) == [f"FD-RATE-{index}" for index in range(14, 21)]
    assert "complete unit at minute 30" in applied["FD-RATE-14"] and "no floor there" in applied["FD-RATE-14"]
    # FD-RATE-14 confirms the reading the feasibility analysis used: the one-unit window of this region IS that analysis's window, unchanged
    published = gj.load_record()["feasibility"]["by_shared_arrival_position"]["0.5"]["B_one_unit"]["common_scale_ml_eq"]
    assert [round(v, 3) for v in record["region"]["membership"]["B_one_unit"]["scale_window_ml_eq"]] == [round(v, 3) for v in published]
    assert jr.RISE_WINDOW == (8.0, 18.0) and jr.SHARE_WINDOW == (0.15, 0.35)


# -- P3-338 ----------------------------------------------------------------------------------------------------------------------------------------------

def test_b1_the_old_scale_band_is_a_pure_candidate_analysis_band_and_is_marked_superseded_without_touching_the_core(record):
    from clinical_core import amendment_2, calibration
    band = record["old_scale_band"]
    entry = calibration.REGISTRY["preload_curve_scale_ml"]
    assert band["band_ml_eq"] == [600.0, 1500.0] == [entry.lower, entry.upper] and band["registry_status"] == "CANDIDATE" == entry.status
    assert band["registry_entries_by_status"]["FACULTY_APPROVED"] == 0 and "FACULTY_APPROVED" in band["registry_statuses_available"], "the stronger status existed and was never given"
    assert not any(band["stronger_status_search"].values())
    basis = band["stronger_status_search_basis"]
    assert sorted(basis["read_from_the_registry_now"] + basis["recorded_from_a_manual_audit_not_recomputed"]) == sorted(band["stronger_status_search"]), "each answer says whether it was computed or audited by hand"
    assert (band["verdict"], band["name"]) == ("A", "PURE_CANDIDATE_ANALYSIS_BAND")
    assert band["introduced"]["commit"] == "b4040ba" and "candidate bands" in band["introduced"]["subject"]
    assert max(band["who_reads_the_band"]["the certified core's own haemorrhage probes"]["scales_explored_ml_eq"]) == 3000.0
    supersession = band["supersession"]
    assert supersession["mark"] == "SUPERSEDED_BY_JOINT_FEASIBILITY_ANALYSIS" and supersession["registry_edited"] is False and supersession["rewrites_historical_evidence"] is False
    assert supersession["registry_still_says"] == "CANDIDATE [600, 1500]"
    assert amendment_2.amended_core_digest_now() == CORE_DIGEST, "the registry lives in the certified core and was not edited"
    cola = (ROOT / "docs" / "COLA_DECISIONES_AI_ADVISOR.md").read_text(encoding="utf-8")
    assert all(f"| {row} |" in cola for row in band["decision_file_rows_that_named_the_scale_before_this_audit"])
    found = subprocess.run(["git", "log", "-1", "--format=%ad %s", "--date=short", "b4040ba"], cwd=ROOT, capture_output=True, text=True)
    if found.returncode == 0:                                     # where the history is available, the recorded provenance is the commit's own
        assert found.stdout.strip() == f"{band['introduced']['date']} {band['introduced']['subject']}"


def test_b2_a_band_with_a_stronger_status_would_stop_the_formalisation(built, monkeypatch):
    from clinical_core import calibration
    entry = calibration.REGISTRY["preload_curve_scale_ml"]
    stronger = dict(calibration.REGISTRY)
    stronger["preload_curve_scale_ml"] = dataclasses.replace(entry, status=calibration.FACULTY_APPROVED)
    monkeypatch.setattr(calibration, "REGISTRY", stronger)
    band = jr.section_old_band()
    assert band["verdict"] != "A" and band["supersession"]["mark"] is None
    record = built["record"]
    verdict = jr.decide(band, built["objects"]["region"], record["witnesses"], record["candidate_trajectories"], record["causal_audit"])
    assert (verdict["verdict"], verdict["name"]) == ("C", "OLD_CONSTRAINT_CONFLICT_REQUIRES_FACULTY_DECISION")


# -- P3-339 ----------------------------------------------------------------------------------------------------------------------------------------------

def test_c1_the_region_is_one_object_in_correlated_coordinates_and_the_rate_is_never_free(built, record):
    region = record["region"]
    assert region["id"] == "GI_JOINT_RATE_PRESSURE_DEVELOPMENT_REGION_V1" and "NOT_A_CALIBRATED_POINT" in region["status"] and "NOT_CLINICALLY_VALIDATED" in region["status"]
    assert set(region["coordinates"]) == {"c", "scale", "kernel", "held", "bleed_rate"} and "never a coordinate" in region["coordinates"]["bleed_rate"]
    assert "a clinically measured blood-loss rate" in region["is_not"] and "independent scalar ranges" in region["is_not"]
    assert set(region["membership"]) == {"A_untreated", "B_one_unit", "C_slow_crystalloid", "K_closed_crystalloid_region", "R_existing_constraints"}
    assert "bleed_rate_ml_eq_per_min" not in {field.name for field in dataclasses.fields(jr.Point)}, "a point cannot carry a rate of its own"
    # the correlation is real: a rate taken from one witness with the scale and kernel of another is OUTSIDE the region (P3-341A)
    live, solved = built["objects"]["region"], built["objects"]["solved"]
    low, high = solved["LOW"], solved["HIGH"]
    assert live.contains(low) and live.contains(high)
    assert not live.contains(jr.Point(low.rate / high.scale, high.scale, high.kernel)), "LOW's rate with HIGH's scale deteriorates too slowly"
    assert not live.contains(jr.Point(high.rate / low.scale, low.scale, low.kernel)), "HIGH's rate with LOW's scale deteriorates too fast"
    # and both projections of those mixed points are inside the published scalar projections: the ranges alone would have admitted them
    rates, scales = region["projections_are_not_ranges"]["bleed_rate_ml_eq_per_min"], region["projections_are_not_ranges"]["scale_ml_eq"]
    assert rates[0] <= low.rate <= rates[1] and rates[0] <= high.rate <= rates[1] and scales[0] <= low.scale <= scales[1] and scales[0] <= high.scale <= scales[1]
    lattice = region["compatible_retention_on_a_lattice"]
    assert len(lattice) == 12 and any(not row["inside_for_some_kernel"] for row in lattice) and any(row["inside_for_some_kernel"] for row in lattice)
    inside = [row for row in lattice if row["inside_for_some_kernel"]]
    assert all(134.6 <= row["largest_compatible_retention_at_60_ml"] <= 234.0 for row in inside), "the compatible retention is a sub-interval of the closed region's"
    same_c = sorted((row for row in inside if abs(row["c"] - inside[0]["c"]) < 1e-12), key=lambda row: row["scale_ml_eq"])
    assert [row["largest_compatible_retention_at_60_ml"] for row in same_c] == sorted(row["largest_compatible_retention_at_60_ml"] for row in same_c), "more retention is compatible only at larger scales"


# -- P3-340 ----------------------------------------------------------------------------------------------------------------------------------------------

def test_d1_the_margins_name_the_dominant_constraints_the_fragile_corners_and_a_narrow_interior(record):
    geometry = record["geometry"]
    profile = geometry["profile_along_the_scale"]
    unit = [row["one_unit_margin"] for row in profile]
    rest = [row["largest_equal_margin_of_the_untreated_crystalloid_and_kernel_constraints"] for row in profile]
    assert unit == sorted(unit, reverse=True) and rest == sorted(rest), "the one-unit margin falls with the scale while the others grow: they cross once"
    dominant = [row["dominant"][0] for row in profile]
    assert dominant[0] == "C" and dominant[-1] == "B" and "".join(dominant) == "".join(sorted(dominant, reverse=True))
    assert any(row["readable"] is False for row in profile), "the fastest balanced points are beyond what the frozen evaluator can read"
    interior = geometry["interior"]
    assert 0.12 < interior["largest_smallest_margin"] < 0.13 and interior["reached_at"] == "CENTER_REFERENCE"
    natural = interior["in_natural_units"]
    assert 1.2 < natural["one_unit_above_its_floor_mmHg"] < 1.3 and 2.4 < natural["share_below_its_ceiling_points"] < 2.6 and 0.011 < natural["c_below_the_fast_edge_as_a_share_of_c"] < 0.012
    for corner in geometry["fragile_corners"]:
        assert min(abs(value) for name, value in corner["margins_normalized"].items() if name != "R_existing_constraints_readable") < 1e-3, corner["where"]
    assert geometry["fragile_corners"][1]["margins_normalized"]["R_existing_constraints_readable"] < 0, "the large-scale corner is also beyond the readability limit"
    assert geometry["robust_floor"]["value"] == jr.ROBUST_FLOOR == 0.05 and "not a faculty decision" in geometry["robust_floor"]["status"]


# -- P3-341 and P3-341A ----------------------------------------------------------------------------------------------------------------------------------

def test_e1_three_test_witnesses_inside_off_every_boundary_and_fully_bound(record):
    witnesses = record["witnesses"]
    assert list(witnesses) == ["LOW", "CENTER_REFERENCE", "HIGH"]
    scales = [witnesses[label]["binding"]["preload_scale_ml_eq"] for label in jr.WITNESSES]
    rates = [witnesses[label]["binding"]["bleed_rate_ml_eq_per_min"] for label in jr.WITNESSES]
    assert scales == sorted(scales) and rates == sorted(rates) and [round(v) for v in scales] == [2469, 2697, 2906] and [round(v, 2) for v in rates] == [8.26, 8.97, 9.09]
    for label, item in witnesses.items():
        bound = item["binding"]
        assert item["role"] == "DEVELOPMENT_TEST_WITNESS" and item["is_a_calibrated_point"] is False and item["is_clinically_preferred"] is False, label
        assert abs(bound["bleed_rate_ml_eq_per_min"] - bound["c_rate_over_scale_per_min"] * bound["preload_scale_ml_eq"]) < 1e-5, "the rate is c x scale"
        assert item["satisfies_all_three_faculty_constraints"] and item["inside_the_closed_crystalloid_region"] and item["every_existing_constraint_readable_and_met"], label
        assert item["on_a_boundary"] is False and item["margins"]["smallest"]["normalized"] >= jr.ROBUST_FLOOR, label
        assert all(8.0 < rise < 18.0 for rise in item["one_unit_sbp_rise_at_30_mmHg"].values()) and 0.15 < item["slow_crystalloid_share_at_60"] < 0.35, label
        assert all(item["existing_constraints_frozen_evaluator"][case][name] is True for case in jr.CASES for name in jr.EXISTING_CONSTRAINTS), label
        assert item["single_parameter_moves"]["0.005"]["stays_inside_under_every_move"] is True, label
        kernel = item["margins"]["K_closed_crystalloid_region"]
        assert all(entry["window"][0] < entry["value"] < entry["window"][1] for entry in kernel["per_envelope"].values()), "strictly inside the closed crystalloid region"
    centre, low, high = witnesses["CENTER_REFERENCE"], witnesses["LOW"], witnesses["HIGH"]
    four = [centre["margins"][name]["normalized"] for name in ("A_untreated", "B_one_unit", "C_slow_crystalloid", "K_closed_crystalloid_region")]
    assert max(four) - min(four) < 1e-3 and centre["margins"]["R_existing_constraints_readable"]["normalized"] > max(four), "the centre is where the four margins are equal"
    half = centre["margins"]["smallest"]["normalized"] * jr.LOW_HIGH_SHARE_OF_THE_CENTRE
    assert abs(low["margins"]["smallest"]["normalized"] - half) < 1e-3 and abs(high["margins"]["smallest"]["normalized"] - half) < 1e-3
    assert high["margins"]["smallest"]["constraint"] == "B_one_unit" and low["margins"]["B_one_unit"]["normalized"] > centre["margins"]["B_one_unit"]["normalized"]
    # FD-RATE-15: the centre of the region is NOT the centre of a faculty window
    assert centre["one_unit_sbp_rise_at_30_mmHg"]["gi_bleed_57m"] < 10.0 and centre["slow_crystalloid_share_at_60"] > 0.30
    # the honest size of the margins: the fastest-course witness does not survive a 1 % move of the rate alone
    assert centre["single_parameter_moves"]["0.01"]["stays_inside_under_every_move"] and high["single_parameter_moves"]["0.01"]["stays_inside_under_every_move"]
    assert sorted(name for name, inside in low["single_parameter_moves"]["0.01"]["moves"].items() if not inside) == ["bleed_rate +0.01", "scale -0.01"]


def test_e2_the_witness_rule_is_not_vacuous(built):
    region, solved = built["objects"]["region"], built["objects"]["solved"]
    centre = solved["CENTER_REFERENCE"]
    # a little past the centre's margin the balanced family no longer holds, and the least-retaining kernel exactly on the closed region's edge has no margin
    beyond = region.balanced(solved["centre_margin"] + 0.02)
    assert beyond is None or region.share_margin(beyond) < solved["centre_margin"] + 0.02
    edge = jr.kernel_margin(jr.kernel_at_depth(0.0))
    assert abs(edge["normalized"]) < 1e-9 and abs(edge["retained_at_60_of_1L_over_60min_ml"] - 134.6014) < 1e-3
    assert jr.kernel_at_depth(0.6) is None, "no kernel is that deep inside the closed region"
    assert not region.contains(jr.Point(region.c_high * 1.01, centre.scale, centre.kernel)) and not region.contains(jr.Point(centre.c, region.scale_high * 1.02, centre.kernel))


# -- P3-342 .. P3-345 ------------------------------------------------------------------------------------------------------------------------------------

def test_f1_the_candidates_differ_from_the_reviewed_trajectories_only_by_the_witness(record):
    candidates = record["candidate_trajectories"]
    assert list(candidates) == ["FR-B", "FR-C", "FR-E", "FR-G"]
    expected_centre = {"FR-B": [(5, 89, 54), (10, 91, 56), (30, 92, 57)],
                       "FR-C": [(60, 71, 43), (120, 54, 33), (125, 56, 34), (130, 59, 36), (150, 64, 39)],
                       "FR-E": [(60, 79, 50), (120, 60, 38), (125, 62, 39), (130, 66, 42), (160, 72, 46)],
                       "FR-G": [(60, 85, 54), (70, 81, 51)]}
    for scenario_id, scenario in candidates.items():
        reviewed = fa.reviewed_item(scenario_id)
        assert all(scenario["reproduction_at_the_current_configuration"][name] for name in ("pressures_equal_the_reviewed_trajectory", "heart_rate_and_capillary_refill_equal_the_reviewed_context")), scenario_id
        assert scenario["script"] == [list(step) for step in reviewed["script"]] and scenario["reviewed_item_digest"] == ftr.item_digest(reviewed)
        assert list(scenario["candidates"]) == ["LOW", "CENTER_REFERENCE", "HIGH"]
        for label, candidate in scenario["candidates"].items():
            assert candidate["version"] == "JOINT_REGION_V1_CANDIDATE" and candidate["complete_to_the_last_committed_minute"], (scenario_id, label)
            assert candidate["unresolved_boundary_minute"] is None and candidate["experiment_would_stop"] is False, (scenario_id, label)
            assert [point["minute"] for point in candidate["pressures"]] == [row["minute"] for row in reviewed["bundle"]["authority_view"]["authoritative_pressure_timeline"]]
            assert all(point["map"] == float(int(round((point["sbp"] + 2 * point["dbp"]) / 3))) for point in candidate["pressures"])
            assert candidate["bleed_rate_distinct_values_ml_min"] == [round(record["witnesses"][label]["binding"]["bleed_rate_ml_eq_per_min"], 6)]
        centre = scenario["candidates"]["CENTER_REFERENCE"]["pressures"]
        assert [(point["minute"], int(point["sbp"]), int(point["dbp"])) for point in centre] == expected_centre[scenario_id], scenario_id
        assert scenario["largest_sbp_difference_between_witnesses_mmHg"] <= 3.0, "the three witnesses are nearly the same trajectory on the page"
    # the treated trajectories move a great deal, which is why the earlier judgments cannot be transferred (FD-RATE-20)
    change = {scenario_id: candidates[scenario_id]["candidates"]["CENTER_REFERENCE"]["change_from_the_reviewed_trajectory_mmHg"][-1]["sbp"] for scenario_id in candidates}
    assert change == {"FR-B": -20.0, "FR-C": -28.0, "FR-E": -37.0, "FR-G": -7.0}
    # FR-G: a modest attenuation, still deteriorating, not a matched target
    long_run = candidates["FR-G"]["candidates"]
    arrival = fa.reviewed_item("FR-G")["arrival"]["sbp"]
    assert all(arrival > item["pressures"][0]["sbp"] > item["pressures"][1]["sbp"] for item in long_run.values())
    assert all(0.15 < record["witnesses"][label]["slow_crystalloid_share_at_60"] < 0.35 for label in long_run)


def test_f2_a_candidate_is_reproduced_from_its_stored_binding_and_the_stopping_rule_is_the_experiments_own(record):
    import runtime_authority_pair as pair
    assert jr.overlay_amendment() == pair.bind().profile.amendment_2, "the overlay is the bound GI_DEVELOPMENT_SNAPSHOT_V1, read from its record"
    captured = jr.capture_reviewed("FR-B")
    for label in jr.WITNESSES:
        point = jr._point_of(record["witnesses"][label])
        rows = jr.simulate(captured["scenario"], 30, point)["rows"]
        assert [jr.displayed(rows, minute) for minute in (5, 10, 30)] == record["candidate_trajectories"]["FR-B"]["candidates"][label]["pressures"], label
    # at the CURRENT configuration the same overlay run finds the stop the earlier review recorded for the untreated 57-year-old: ESTABLISHED collapse at minute 207
    untreated = fa.capture(*fa.reviewed_orders("FR-A"))
    stop = jr.simulate(untreated, 240, overlay=jr.overlay_amendment())["first_established_collapse_minute"]
    assert stop == 207 and "minute 207" in fa.reviewed_item("FR-A")["bundle"]["authority_view"]["halt_reason"]


# -- P3-346 ----------------------------------------------------------------------------------------------------------------------------------------------

def test_g1_the_causal_audit_holds_for_every_witness(record):
    names = ("bleeding_remains_active", "blood_improves_volume_and_pressure_causally", "slow_crystalloid_weaker_than_blood", "untreated_deterioration_progressive",
             "treatment_ordering_preserved", "no_case_specific_branch", "no_fitting_to_the_legacy_engine", "no_candidate_reaches_a_boundary")
    for label, audit in record["causal_audit"].items():
        assert audit["all_hold"] and all(audit[name]["holds"] is True for name in names), label
        blood = audit["blood_improves_volume_and_pressure_causally"]["by_scenario"]
        assert sorted(blood) == ["FR-B", "FR-C", "FR-E"] and all(item["sbp_caused_by_red_cells_mmHg"] > 5.0 and item["effective_volume_caused_by_red_cells_ml_eq"] > 200.0 for item in blood.values())
        slow = audit["slow_crystalloid_weaker_than_blood"]
        assert 0 < slow["slow_litre_at_60_mmHg"] < slow["one_complete_unit_bleeding_controlled_mmHg"] < slow["two_units_in_the_delayed_scenario_same_case_mmHg"]
        assert slow["retained_ml"]["slow_litre_at_60"] < slow["retained_ml"]["one_unit"], "a slow litre leaves less in the circulation than one unit does"
        assert all("not a measurement" in audit[name]["basis"] for name in ("no_case_specific_branch", "no_fitting_to_the_legacy_engine")), "a declaration is labelled as one"
        order = audit["treatment_ordering_preserved"]
        assert order["early_treatment_end"]["sbp"] > order["delayed_treatment_end"]["sbp"] > order["untreated_at_that_minute_delayed"]
    source = (ROOT / "test_gi_joint_region.py").read_text(encoding="utf-8")
    assert "legacy_counterfactual" not in source and "gi_bleed_57m\" else" not in source and "if case ==" not in source, "no legacy pressure is read and no branch is taken on the case"


# -- P3-347 ----------------------------------------------------------------------------------------------------------------------------------------------

def test_h1_the_reviewer_sees_the_same_view_as_before_with_only_the_pressure_changed_and_nothing_technical(built, record):
    review_set = built["review_set"]
    assert review_set["version"] == "JOINT_REGION_V1_CANDIDATE" and review_set["order"] == {"first": "CONJUNTO-1", "then_if_wanted": ["CONJUNTO-2", "CONJUNTO-3"], "scenarios": list(jr.SCENARIOS)}
    assert [item["item_id"] for item in review_set["items"]] == [f"CONJUNTO-{number}/{scenario}" for number in (1, 2, 3) for scenario in jr.SCENARIOS]
    assert [item["required"] for item in review_set["items"]] == [True] * 4 + [False] * 8
    labels = jr.blind_labels()
    assert labels["CENTER_REFERENCE"] == "CONJUNTO-1" and sorted(labels.values()) == ["CONJUNTO-1", "CONJUNTO-2", "CONJUNTO-3"]
    of_set = {name: label for label, name in labels.items()}
    for item in review_set["items"]:
        stored = fa.reviewed_item(item["scenario_id"])
        page, mine = ftr.blind_view(stored), jr.reviewer_view(stored)
        # the view this module builds for the STORED item is the review page's own blind view of it ...
        assert all(mine[name] == page[name] for name in ("scenario_id", "title", "context", "purpose", "arrival", "common"))
        assert [{key: row[key] for key in ("n", "minute", "advance", "action", "result")} for row in page["timeline"]] == mine["timeline"]
        assert mine["heart_rate_and_capillary_refill"] == [{"minute": row["minute"], "hr": row["hr"], "crt": row["crt"]} for row in page["context_vitals"]]
        # ... and a candidate item is that view with ONLY the pressure points replaced
        assert all(item[name] == mine[name] for name in ("scenario_id", "title", "context", "purpose", "arrival", "timeline", "heart_rate_and_capillary_refill"))
        candidate = record["candidate_trajectories"][item["scenario_id"]]["candidates"][of_set[item["set"]]]["pressures"]
        assert item["common"][1:] == candidate and item["common"][0] == mine["common"][0] and item["common"] != mine["common"]
        assert item["stopped"] is False and item["overall_choices"] == list(ftr.OVERALL)
        assert [(q["id"], q["topic"], q["text"], q["choices"]) for q in item["questions"]] == [(q["id"], q["topic"], q["text"], list(q["choices"])) for q in ftr.FIRST_PASS]
    blinded = json.dumps(review_set["items"], ensure_ascii=False)          # what the reviewer is shown (the record's own description says what it leaves out)
    for word in ("CENTER_REFERENCE", '"LOW"', '"HIGH"', "witness", "bleed_rate", "preload", "kernel", "legacy", "mL-eq", "binding"):
        assert word not in blinded, f"the reviewer's set names {word}"
    assert sorted(built["blind_key"]["sets"]) == ["CONJUNTO-1", "CONJUNTO-2", "CONJUNTO-3"] and built["blind_key"]["sets"]["CONJUNTO-1"]["witness"] == "CENTER_REFERENCE"
    assert built["blind_key"]["legacy_comparator"]["copied_here"] is False and built["blind_key"]["earlier_review"]["preserved_unchanged"] is True


def test_h2_the_first_pass_files_carry_no_parameter_no_witness_and_no_legacy_number_and_the_key_is_apart(built, record):
    kit = built["kit"]
    assert sorted(kit) == sorted(FIRST_PASS_FILES + (KEY_FILE,))
    first_pass = "\n".join(kit[name] for name in FIRST_PASS_FILES)
    tokens = ["CENTER_REFERENCE", "LOW", "HIGH", "mL-eq", "legacy", "Legacy"]
    for label in jr.WITNESSES:
        bound = record["witnesses"][label]["binding"]
        tokens += [f"{bound['bleed_rate_ml_eq_per_min']:.2f}".replace(".", ","), f"{bound['preload_scale_ml_eq']:.0f}"]
    for token in tokens:
        assert token not in first_pass, f"the first-pass kit shows {token}"
    assert all(token in kit[KEY_FILE] for token in ("CENTER_REFERENCE", "LOW", "HIGH", "mL-eq")), "the key is where the identities are"
    for word in ("Q1 DIRECTION", "Q2 TIMING", "Q3 MAGNITUDE", "Q4 MANAGEMENT RESPONSE", "Q5 EDUCATIONAL RISK", "ACCEPT_WITH_LIMITATION", "RECALIBRATE", "REJECT"):
        assert word in kit["formulario_respuestas.md"], word
    assert "NO ha empezado" in kit["README.md"] and "No** es validación clínica" in kit["README.md"] and "no** se transfieren" in kit["README.md"]
    for name in ("conjunto_1.md", "conjunto_2.md", "conjunto_3.md"):
        assert all(f"## {scenario} ·" in kit[name] for scenario in jr.SCENARIOS) and "PAS | PAD | PAM | FC (contexto) | Relleno capilar" in kit[name], name
    assert kit["conjunto_1.md"] != kit["conjunto_2.md"] != kit["conjunto_3.md"]
    # neutrality of the first pass: the comment is optional (as on the page), the README names no behavioural target, and the reviewer is not sent to the technical document
    form = kit["formulario_respuestas.md"]
    assert form.count("Comentario (opcional):") == 12 and "obligatorio" not in form, "no rule that makes a non-ACCEPT answer cost more than an ACCEPT"
    assert "el juicio global se da en la primera pasada" in form
    for word in ("glóbulos", "atenuación", "modest", "anclas", "35 %", "+8"):
        assert word not in kit["README.md"], f"the reviewer's README names a behavioural target ({word})"
    assert "los calcula el motor vigente del simulador" in kit["README.md"] and all("los calcula el motor vigente del simulador" in kit[name] for name in ("conjunto_1.md", "conjunto_2.md", "conjunto_3.md"))
    parent = (ROOT / "faculty_review_kit" / "README.md").read_text(encoding="utf-8")
    row = next(line for line in parent.split("\n") if line.startswith("| `region_conjunta_v1/`"))
    assert "docs/PHASE3_GI_JOINT_REGION" not in row and "desvela el ciego" in row, "the kit index does not point the reviewer at the document that unblinds the sets"
    described = built["review_set"]
    assert "no legacy PRESSURE, no legacy comparator" in described["what_it_is"] and "ARE the legacy engine's own values" in described["what_it_is"]
    assert "legacy engine" in described["heart_rate_and_capillary_refill_source"], "heart rate and capillary refill are said to be what they are"


def test_h3_the_current_review_page_does_not_accept_these_candidates_and_the_earlier_review_is_untouched():
    refused = ftr.load_set(jr.REVIEW_SET_PATH, bundles=None, scenario_of=lambda identifier: None)
    assert refused["ok"] is False and refused["items"] == {} and "not the stored one" in refused["problems"][0], "the page offers only its own pinned, certified set"
    stored = _load(REVISION / "PHASE3_FACULTY_TRAJECTORY_REVIEW_SET.json")
    assert stored["record_digest"] == ftr.PINNED_SET_DIGEST == "f65d1127f3fb97926334d695aeab37b92f3a44236cec2ae025025eec90ba1649"
    human = _load(REVISION / "PHASE3_FIRST_HUMAN_FACULTY_REVIEW.json")
    assert human["record_digest"] == _sealed(human) == HUMAN_DIGEST
    assert {item["scenario_id"]: item["overall"] for item in human["scenarios"] if item["scenario_id"] in jr.SCENARIOS} == {
        "FR-B": "ACCEPT_WITH_LIMITATION", "FR-C": "ACCEPT_WITH_LIMITATION", "FR-E": "ACCEPT", "FR-G": "RECALIBRATE"}, "the earlier judgments stand as they were given"


# -- the decision ----------------------------------------------------------------------------------------------------------------------------------------

def test_j1_the_verdict_is_A_and_each_other_verdict_is_reachable(built, record):
    decision = record["decision"]
    assert (decision["verdict"], decision["name"]) == ("A", "JOINT_REGION_READY_FOR_BLINDED_HUMAN_REREVIEW")
    assert decision["a_point_was_chosen_as_a_calibration"] is False and decision["amendment_3"].startswith("CLOSED")
    assert decision["scenarios_ready"] == {scenario: True for scenario in jr.SCENARIOS}
    region = built["objects"]["region"]
    args = (record["old_scale_band"], region, record["witnesses"], record["candidate_trajectories"], record["causal_audit"])
    assert jr.decide(*args)["verdict"] == "A"
    on_the_edge = copy.deepcopy(record["witnesses"])
    on_the_edge["HIGH"]["on_a_boundary"] = True
    assert jr.decide(args[0], region, on_the_edge, args[3], args[4])["name"] == "JOINT_REGION_EXISTS_BUT_WITNESSES_NOT_ROBUST"
    broken = copy.deepcopy(record["causal_audit"])
    broken["LOW"]["all_hold"] = False
    assert jr.decide(args[0], region, args[2], args[3], broken)["verdict"] == "B"
    moved = types.SimpleNamespace(c_low=region.c_low * 1.01, c_high=region.c_high, scale_low=region.scale_low, scale_high=region.scale_high)
    assert jr.decide(args[0], moved, args[2], args[3], args[4])["name"] == "JOINT_FEASIBILITY_NOT_REPRODUCIBLE"


# -- nothing moved ---------------------------------------------------------------------------------------------------------------------------------------

def test_i1_the_core_the_closed_region_and_every_earlier_record_are_untouched():
    import runtime_pressure_grant as grants
    import volume_behaviour_record as vbr
    from clinical_core import amendment_2, legacy_adapter
    assert amendment_2.amended_core_digest_now() == grants.CORE_DIGEST == CORE_DIGEST
    assert vbr.EFFECTIVE_REGION == {"peak": (0.15, 0.27072), 30: (0.15, 0.25), 60: (0.10, 0.20), 120: (0.05, 0.15)} and vbr.STATUS == "FACULTY_DEFINED_BEHAVIORAL_REGION"
    assert legacy_adapter.LEGACY_LITERALS["gi_bleeding_circulation_per_min"][0] == 0.003, "the running bleed rate is still the historical reference"
    assert gj.load_record()["record_digest"] == FEASIBILITY_RECORD_DIGEST
    for name, expected in (("PHASE3_JOINT_FEASIBILITY_CHECKPOINT.json", P3_336_DIGEST), ("PHASE3_BLEED_RATE_SCALE_CHECKPOINT.json", P3_325_DIGEST),
                           ("PHASE3_FIRST_FACULTY_REVIEW_CHECKPOINT.json", P3_313_DIGEST)):
        assert _load(REVISION / name)["record_digest"] == expected, name
    assert not list(REVISION.glob("*AMENDMENT_3*")) and not list((ROOT / "docs").glob("*AMENDMENT_3*")), "Amendment 3 stays closed: no design"
    for path in sorted((ROOT / "clinical_core").rglob("*.py")):
        assert "norepinephrine" not in path.read_text(encoding="utf-8").lower(), f"{path.name}: norepinephrine was not implemented"
    source = (ROOT / "test_gi_joint_region.py").read_text(encoding="utf-8")
    assert "import faculty_trajectory_review" not in source and "runtime_authority" not in source and "runtime_pressure_grant" not in source, "the analysis reaches no page, authority or grant"


def test_i2_the_analysis_harnesses_are_test_side_modules_so_no_runtime_root_reaches_the_core_or_the_shadow_bridge():
    """Found in this cycle: the analysis harnesses of the three earlier cycles were non-test root modules that imported the core and the shadow bridge, which
    three isolation guards forbid. They are test-side modules now (the repository's convention, as test_gi_counterfactual.py), and no guard was changed."""
    renamed = {"frg_crystalloid_analysis": "test_gi_frg_crystalloid_analysis", "gi_bleed_rate_analysis": "test_gi_bleed_rate_analysis",
               "gi_joint_feasibility_analysis": "test_gi_joint_feasibility_analysis", "gi_joint_region": "test_gi_joint_region"}
    for old, new in renamed.items():
        assert not (ROOT / f"{old}.py").exists() and (ROOT / f"{new}.py").is_file(), old
    import ast
    for path in sorted(ROOT.glob("*.py")):
        if path.name.startswith(("test_", "regression_")):
            continue
        imported = {alias.name.split(".")[0] for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))) if isinstance(node, (ast.Import, ast.ImportFrom))
                    for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(name=node.module or "")])}
        assert not imported & set(renamed) and not imported & set(renamed.values()), f"{path.name} imports an analysis harness"
    # the sealed records were NOT rewritten: they still carry the names the modules had when the records were sealed
    assert "frg_crystalloid_analysis.py" in (REVISION / "PHASE3_GI_BLEED_RATE_SCALE_ANALYSIS.json").read_text(encoding="utf-8")
    cola = (ROOT / "docs" / "COLA_DECISIONES_AI_ADVISOR.md").read_text(encoding="utf-8")
    assert "| FD-P3-238 |" in cola and "388f279" in cola and "586d60a" in cola
    assert "| FD-P3-239 |" in cola and "exactamente tres commits" in cola
    readme = (jr.KIT_DIR / "README.md").read_text(encoding="utf-8")
    assert "**Sólo `CONJUNTO-1`**" in readme and "FR-B, FR-C, FR-E, FR-G" in readme and "**No los abras**" in readme, "the reviewer opens conjunto_1 only, in the given order"


# -- P3-348 ----------------------------------------------------------------------------------------------------------------------------------------------

def test_k1_the_decisions_the_debt_the_document_and_the_checkpoint_say_the_same_thing(record):
    cola = (ROOT / "docs" / "COLA_DECISIONES_AI_ADVISOR.md").read_text(encoding="utf-8")
    for index in range(14, 21):
        assert f"| FD-RATE-{index} |" in cola
    for index in range(234, 238):
        assert f"| FD-P3-{index} |" in cola
    assert "SUPERSEDED_BY_JOINT_FEASIBILITY_ANALYSIS" in cola and "JOINT_REGION_V1_CANDIDATE" in cola
    debt = (ROOT / "docs" / "REGISTRO_DEUDA_TECNICA.md").read_text(encoding="utf-8")
    assert "## TD-150" in debt
    checkpoint = _load(REVISION / "PHASE3_JOINT_REGION_CHECKPOINT.json")
    assert checkpoint["record_digest"] == _sealed(checkpoint)
    assert set(checkpoint["statuses"]) == {"OLD_SCALE_BAND_STATUS", "JOINT_REGION_FORMALIZED", "JOINT_REGION_MARGIN", "LOW_WITNESS", "CENTER_REFERENCE_WITNESS", "HIGH_WITNESS",
                                           "FR_B_READY_FOR_REREVIEW", "FR_C_READY_FOR_REREVIEW", "FR_E_READY_FOR_REREVIEW", "FR_G_READY_FOR_REREVIEW", "AMENDMENT3_STATUS"}
    assert checkpoint["overall"] == {"verdict": "A", "name": "JOINT_REGION_READY_FOR_BLINDED_HUMAN_REREVIEW"} and all(checkpoint["confirmations"].values())
    pins = checkpoint["pinned_records"]
    assert pins["joint_region_record_digest"] == record["record_digest"] == jr.load_record()["record_digest"]
    assert pins["candidate_review_set_digest"] == _load(jr.REVIEW_SET_PATH)["record_digest"] and pins["blind_key_digest"] == _load(jr.BLIND_KEY_PATH)["record_digest"]
    assert pins["human_review_record_digest"] == HUMAN_DIGEST and pins["p3_336_checkpoint_digest"] == P3_336_DIGEST and pins["active_core_digest"] == CORE_DIGEST
    assert checkpoint["blocker"] is None and "human" in checkpoint["next_human_action"].lower() and "conjunto_1.md ONLY" in checkpoint["next_human_action"]
    assert checkpoint["publication"]["authorised_afterwards_by"] == "FD-P3-239" and len(checkpoint["publication"]["commits"]) == 3
    assert checkpoint["isolation_regression_found_in_this_cycle"]["repair"] == {**checkpoint["isolation_regression_found_in_this_cycle"]["repair"], "guards_changed": False, "sealed_records_changed": False}
    doc = (ROOT / "docs" / "PHASE3_GI_JOINT_REGION.md").read_text(encoding="utf-8")
    assert "A · JOINT_REGION_READY_FOR_BLINDED_HUMAN_REREVIEW" in doc and "A · PURE_CANDIDATE_ANALYSIS_BAND" in doc and "No se eligió ningún punto" in doc
    assert "docs/PHASE3_GI_JOINT_REGION.md" in (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
