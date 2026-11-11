"""P3-199 to P3-209: snapshot ratification, consciousness review, reader audit, pressure recertification, snapshot binding, collapse-boundary
guard, the dry pair transaction and its management series, and the checkpoint.

Nothing here enables authority. ``COMMON_CORE_RUNTIME_AUTHORITY`` stays False, the authority registry keeps only the pressure point, ``commit`` is
never called by the dry transaction, and no encounter state is written. What is proved is that the two records say what the code and live
encounters say, and that each guard REFUSES when it is attacked.
"""
import copy
import dataclasses
import hashlib
import inspect
import json
import types
from pathlib import Path

import pytest

import pilot_acceptance as acceptance
import runtime_authority as authority
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam
import test_gi_pair_dry_run as dry
import test_gi_preauthority_record as rec
import test_gi_preauthority_review as review
import test_gi_snapshot_analysis as an
import test_gi_snapshot_binding as binding
from clinical_core import systemic_consciousness as sc

ROOT = Path(__file__).resolve().parent
REVIEW = json.loads((ROOT / rec.REVIEW_FILE).read_text(encoding="utf-8"))
DRY = json.loads((ROOT / rec.DRY_RUN_FILE).read_text(encoding="utf-8"))
RATIFICATION = json.loads((ROOT / binding.RATIFICATION_FILE).read_text(encoding="utf-8"))
SNAPSHOT = json.loads((ROOT / an.SNAPSHOT_FILE).read_text(encoding="utf-8"))
COUNTERFACTUAL = json.loads((ROOT / "docs/revision/PHASE3_GI_AUTHORITY_COUNTERFACTUAL.json").read_text(encoding="utf-8"))
SENSITIVITY = json.loads((ROOT / an.SENSITIVITY_FILE).read_text(encoding="utf-8"))
RATIFICATION_DIGEST = "123135b3e35c7cb8117ed02600e19b8e44e117e4d58feb2cf0a630cb77f58f64"
BOUND_PROFILE_DIGEST = "c167b45ee0ce6ec29643cba47f2dde3b6eb760a4c6e37f11d3fa7e5e0a8acc89"


def _normal(value):
    return json.loads(json.dumps(value))


# -- nothing is enabled ------------------------------------------------------------------------------------------------------------------------

def test_authority_stays_disabled_and_v1_is_not_in_the_authority_registry():
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    assert sorted(authority.APPROVED_SNAPSHOTS) == ["gi_pressure_committed"]
    assert authority.gate({}, environ={}, unsupported=()).granted is False
    assert authority.AUTHORITY_DOMAIN == ("sbp", "dbp", "map")
    assert REVIEW["authority"] == {"enabled": False, "common_core_runtime_authority": False, "approved_authority_snapshots": ["gi_pressure_committed"],
                                   "granted_by_this_record": False}
    assert DRY["authority"] == {"common_core_runtime_authority": False, "approved_authority_snapshots": ["gi_pressure_committed"], "commit_called": False}


def test_no_runtime_module_names_the_harness_and_the_dry_transaction_never_calls_commit():
    names = ("test_gi_pair_dry_run", "test_gi_snapshot_binding", "test_gi_preauthority_review", "test_gi_preauthority_record", "GI_DEVELOPMENT_SNAPSHOT")
    for path in ROOT.glob("*.py"):
        if not path.name.startswith(("test_", "regression_")):
            assert not any(name in path.read_text(encoding="utf-8") for name in names), path.name
    source = inspect.getsource(dry)
    assert ".commit(" not in source and "open_site" not in source and "AUTHORITY_FLAG" not in source
    assert "setenv" not in source and "os.environ" not in source


# -- P3-199: the ratification ----------------------------------------------------------------------------------------------------------------------

def test_the_ratification_is_pinned_rebuilds_exactly_and_leaves_version_1_untouched():
    assert hashlib.sha256((ROOT / an.SNAPSHOT_FILE).read_bytes()).hexdigest() == binding.V1_FILE_SHA256
    assert RATIFICATION["ratification_digest"] == RATIFICATION_DIGEST
    assert _normal(binding.build_ratification(str(ROOT))) == RATIFICATION
    assert an.digest({key: value for key, value in RATIFICATION.items() if key != "ratification_digest"}) == RATIFICATION_DIGEST


def test_the_ratification_says_what_was_ratified_and_what_it_is_not():
    assert (RATIFICATION["snapshot_id"], RATIFICATION["version"], RATIFICATION["status"]) == ("GI_DEVELOPMENT_SNAPSHOT_V1", 1, "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS")
    assert RATIFICATION["is_not"] == ["clinical calibration", "production profile", "resident profile", "authority-approved snapshot"]
    assert RATIFICATION["values"] == SNAPSHOT["values"] and RATIFICATION["common_core_lineage"]["digest"] == rs.CORE_LINEAGE[-1].digest
    for key in ("selection_criteria", "boundary_margins", "sensitivity_witnesses", "faculty_decisions", "uncertainty", "falsifiers", "region_bounds"):
        assert RATIFICATION[key], key
    assert RATIFICATION["min_margin"] == 0.5 and set(RATIFICATION["boundary_margins"].values()) == {0.5}
    assert {"FD-AUTH-01", "FD-AUTH-02", "FD-AUTH-03"} <= set(RATIFICATION["faculty_decisions"]) and len(RATIFICATION["faculty_decisions"]["FD-AUTH-02"]) == 7
    assert RATIFICATION["authority"] == {"added_to_an_approved_authority_snapshot_registry": False,
                                         "approved_authority_snapshots_today": ["gi_pressure_committed"], "common_core_runtime_authority": False}


def test_low_v1_and_high_are_preserved_as_sensitivity_witnesses_and_the_region_is_not_replaced():
    kept = RATIFICATION["sensitivity_witnesses"]
    assert kept["LOW"] == sc.WITNESSES["LOW"].to_dict() and kept["HIGH"] == sc.WITNESSES["HIGH"].to_dict() and kept["V1"] == "GI_DEVELOPMENT_SNAPSHOT_V1"
    assert kept["region_not_replaced_by_the_point"] is True
    assert fam.GI_AMENDMENT_2_WITNESS_NAMES == ("LOW", "CENTER_REFERENCE", "HIGH")
    assert RATIFICATION["region_bounds"] == {name: list(sc.REGIONS[name][:2]) for name in sc.FIELDS}


# -- P3-204: the binding and its tamper controls ---------------------------------------------------------------------------------------------------

def test_bind_builds_the_profile_only_from_the_record_on_the_approved_pressure_point():
    bound = binding.bind(str(ROOT))
    assert bound.snapshot_id == "GI_DEVELOPMENT_SNAPSHOT_V1" and bound.version == 1 and bound.profile_digest == BOUND_PROFILE_DIGEST
    assert bound.profile.amendment_2.to_dict() == SNAPSHOT["values"] == bound.value_map()
    base = fam._bundle_profile(fam.COMMITTED)
    assert base.amendment_2 is None
    for field in dataclasses.fields(base):
        if field.name != "amendment_2":
            assert getattr(bound.profile, field.name) == getattr(base, field.name), field.name
    assert binding.pressure_point_matches(bound.profile) and bound.pressure_point == "gi_pressure_committed"
    assert RATIFICATION["binding"]["bound_profile_digest"] == BOUND_PROFILE_DIGEST
    with pytest.raises(dataclasses.FrozenInstanceError):
        bound.values = ()


def test_the_profile_construction_reads_no_witness_name_and_no_default():
    source = inspect.getsource(binding.build_profile)
    assert "WITNESSES" not in source and "development_profile(" not in source.split('"""')[2] and "CENTER_REFERENCE" not in source
    # the bound values are none of the layer's three named witnesses
    assert all(SNAPSHOT["values"] != witness.to_dict() for witness in sc.WITNESSES.values())


def _tampered(change):
    record = copy.deepcopy(SNAPSHOT)
    change(record)
    return record


TAMPERS = {
    "wrong snapshot id": (lambda r: r.update(snapshot_id="GI_DEVELOPMENT_SNAPSHOT_V2"), binding.WRONG_SNAPSHOT_ID),
    "wrong version": (lambda r: r.update(version=2), binding.WRONG_VERSION),
    "modified parameter": (lambda r: r["values"].update(delivery_severe=0.51), binding.MODIFIED_PARAMETER),
    "modified parameter with recomputed digests": (
        lambda r: (r["values"].update(burden_clear_tau=9.0),
                   r["immutability"].update(identity_digest=an.digest(binding.identity_of(r)),
                                            record_digest=an.digest({k: v for k, v in r.items() if k != "immutability"}))), binding.MODIFIED_PARAMETER),
    "wrong digest": (lambda r: r["immutability"].update(record_digest="0" * 64), binding.WRONG_DIGEST),
    "edited body": (lambda r: r.update(falsifiers=[]), binding.WRONG_DIGEST),
    "wrong core lineage in the record": (lambda r: r["common_core_lineage"].update(digest="22b90a6f" + "0" * 56), binding.WRONG_CORE_LINEAGE),
    "partial snapshot": (lambda r: r["values"].pop("collapse_clear_tau"), binding.PARTIAL_SNAPSHOT),
    "extra parameter": (lambda r: r["values"].update(extra=1.0), binding.PARTIAL_SNAPSHOT),
    "a non-number": (lambda r: r["values"].update(delivery_normal="0.75"), binding.PARTIAL_SNAPSHOT),
    "a boolean": (lambda r: r["values"].update(delivery_normal=True), binding.PARTIAL_SNAPSHOT),
    "LOW substituted": (lambda r: r.update(values=sc.WITNESSES["LOW"].to_dict()), binding.WITNESS_SUBSTITUTED),
    "HIGH substituted": (lambda r: r.update(values=sc.WITNESSES["HIGH"].to_dict()), binding.WITNESS_SUBSTITUTED),
    "CENTER_REFERENCE substituted": (lambda r: r.update(values=sc.WITNESSES["CENTER_REFERENCE"].to_dict()), binding.WITNESS_SUBSTITUTED),
    "registered as authority": (lambda r: r["authority"].update(registered_as_an_authority_artifact=True), binding.NOT_A_DEVELOPMENT_SNAPSHOT),
}


@pytest.mark.parametrize("label", sorted(TAMPERS))
def test_every_tampered_record_is_refused_with_its_own_code(label):
    change, expected = TAMPERS[label]
    with pytest.raises(binding.SnapshotBindingError) as refused:
        binding.bind(str(ROOT), record=_tampered(change))
    assert expected in refused.value.reasons, (label, refused.value.reasons)


def test_a_wrong_live_lineage_an_unratified_record_and_wrong_bytes_are_refused():
    wrong = {"version_id": "PHASE2_AMENDMENT_1", "digest": "10b45ce2" + "0" * 56, "bytes_digest": "10b45ce2" + "0" * 56, "certified": True}
    for lineage in (wrong, {**binding.live_lineage(), "certified": False}, {**binding.live_lineage(), "bytes_digest": "0" * 64}):
        with pytest.raises(binding.SnapshotBindingError) as refused:
            binding.bind(str(ROOT), record=copy.deepcopy(SNAPSHOT), lineage=lineage)
        assert refused.value.reasons == (binding.WRONG_CORE_LINEAGE,)
    for ratification in ({"status": "PENDING"}, {**RATIFICATION, "status": "RATIFIED_FOR_AUTHORITY"}, {**RATIFICATION, "values": sc.WITNESSES["LOW"].to_dict()},
                         {**RATIFICATION, "authority": {"added_to_an_approved_authority_snapshot_registry": True}}):
        with pytest.raises(binding.SnapshotBindingError) as refused:
            binding.bind(str(ROOT), record=copy.deepcopy(SNAPSHOT), ratification=ratification)
        assert refused.value.reasons == (binding.NOT_RATIFIED,)
    with pytest.raises(binding.SnapshotBindingError) as refused:
        binding.bind(str(ROOT), record=copy.deepcopy(SNAPSHOT), raw=b"{}")
    assert binding.WRONG_DIGEST in refused.value.reasons
    assert REVIEW["binding_contract"]["refusals"] == list(binding.REFUSALS)


# -- P3-200: the consciousness review ---------------------------------------------------------------------------------------------------------------

def test_the_episodes_re_derive_from_the_committed_records_and_account_for_all_461_minutes():
    found = _normal(review.episodes(COUNTERFACTUAL, SENSITIVITY, SNAPSHOT["values"]))
    stored = REVIEW["consciousness_review"]
    assert found == stored["episodes"]
    assert (stored["episode_count"], stored["compared_minutes"]) == (15, 461) == (len(found), sum(item["compared_minutes"] for item in found))
    assert stored["compared_minutes"] == COUNTERFACTUAL["summary_required"]["minutes_by_class"]["consciousness_category"]["POTENTIAL_EDUCATIONAL_PROBLEM"]
    assert stored["physiology_modified"] is False


def test_every_episode_has_a_direction_and_the_two_cases_diverge_in_opposite_directions_at_onset():
    stored = REVIEW["consciousness_review"]
    assert {item["direction"] for item in stored["episodes"]} == {review.COMMON_MORE, review.LEGACY_MORE, review.TRANSIENT}
    assert stored["by_direction"] == {review.LEGACY_MORE: {"episodes": 5, "compared_minutes": 196},
                                      review.COMMON_MORE: {"episodes": 8, "compared_minutes": 263},
                                      review.TRANSIENT: {"episodes": 2, "compared_minutes": 2}}
    # the legacy engine is the more impaired one ONLY in the 57-year-old, and only before the snapshot's own onset
    assert {item["case"] for item in stored["episodes"] if item["direction"] == review.LEGACY_MORE} == {"gi_bleed_57m"}
    assert all(item["at_end"]["minute"] <= 120 for item in stored["episodes"] if item["direction"] == review.LEGACY_MORE)
    assert all(item["direction"] in (review.COMMON_MORE, review.TRANSIENT) for item in stored["episodes"] if item["case"] == "gi_bleed_72f")


def test_the_opposite_directions_are_explained_by_an_absolute_legacy_threshold_against_relative_to_arrival_semantics():
    stored = REVIEW["consciousness_review"]["opposite_direction"]
    assert stored == _normal(review.opposite_direction_explanation(COUNTERFACTUAL, SENSITIVITY, SNAPSHOT["values"]))
    assert stored["explained_by"] == "ABSOLUTE_PAS_LEGACY_THRESHOLD_VERSUS_RELATIVE_TO_ARRIVAL_SEMANTICS"
    young, old = stored["cases"]["gi_bleed_57m"], stored["cases"]["gi_bleed_72f"]
    # both cross the SAME absolute pressure (80 mmHg), at different minutes because they arrive at different pressures
    assert (young["legacy_sbp_one_minute_before"], young["legacy_sbp_at_that_minute"]) == (80, 79) == (old["legacy_sbp_one_minute_before"], old["legacy_sbp_at_that_minute"])
    assert (young["legacy_arrival_sbp"], old["legacy_arrival_sbp"]) == (88, 98) and (young["legacy_first_drowsy_minute"], old["legacy_first_drowsy_minute"]) == (63, 138)
    # and both cross the SAME relative delivery at the SAME minute
    assert young["common_first_somnolent_minute"] == old["common_first_somnolent_minute"] == 109
    assert young["relative_delivery_at_that_minute"] == old["relative_delivery_at_that_minute"]
    assert (young["direction_at_onset"], old["direction_at_onset"]) == (review.LEGACY_MORE, review.COMMON_MORE)
    # the legacy ladder really is absolute systolic pressure
    import family_engine
    assert family_engine._PRESSURE_LEVELS == ((80.0, 1), (65.0, 2)) and max(level for _, level in family_engine._PRESSURE_LEVELS) == 2


def test_every_episode_is_mechanistically_coherent_and_the_coherence_check_can_fail():
    stored = REVIEW["consciousness_review"]
    assert stored["coherence"] == {"coherent": 15, "contradictions": []}
    assert all(set(item["coherence"]["violations"].values()) == {0} for item in stored["episodes"])
    # a category that is not the composite's, an F that moves away from its target and a delivery that rises untreated are each caught
    physical = an.course_of_record(SENSITIVITY["physical"])["gi_bleed_57m"]["untreated"]["physical"]
    mechanism = review._mechanism(SNAPSHOT["values"], physical)
    minutes = list(range(158, 175))
    honest = [mechanism[m]["category"] for m in minutes]
    assert review._coherence(minutes, honest, mechanism, None)["verdict"] == review.COHERENT
    assert review._coherence(minutes, [0] * len(minutes), mechanism, None)["verdict"] == review.CONTRADICTION
    bent = copy.deepcopy(mechanism)
    bent[165]["F"] = bent[164]["F"] - 0.2
    assert review._coherence(minutes, honest, bent, None)["violations"]["f_moves_away_from_its_target"] >= 1
    risen = copy.deepcopy(mechanism)
    risen[166]["relative_delivery"] = risen[165]["relative_delivery"] + 0.1
    assert review._coherence(minutes, honest, risen, None)["violations"]["delivery_rises_before_any_order"] >= 1


def test_the_faculty_table_is_short_representative_and_left_unanswered():
    table = REVIEW["consciousness_review"]["faculty_table"]
    assert 5 <= len(table) <= 10
    assert {row["case"] for row in table} == {"gi_bleed_57m", "gi_bleed_72f"}
    assert {row["direction"] for row in table} == {review.COMMON_MORE, review.LEGACY_MORE, review.TRANSIENT}
    assert REVIEW["consciousness_review"]["faculty_questions"] == list(review.FACULTY_QUESTIONS) and len(review.FACULTY_QUESTIONS) == 4
    for row in table:
        assert set(row["faculty_answers"]) == set(review.FACULTY_QUESTIONS) and set(row["faculty_answers"].values()) == {None}
        assert row["coherence"] == review.COHERENT
    assert table[0]["compared_minutes"] * table[0]["max_band_gap"] == max(row["compared_minutes"] * row["max_band_gap"] for row in table)


# -- P3-201: the readers ---------------------------------------------------------------------------------------------------------------------------

def test_the_reader_inventory_is_the_live_ast_scan_and_every_site_is_classified():
    audit = _normal(review.reader_audit(str(ROOT)))
    stored = REVIEW["reader_audit"]
    assert audit["rows"] == stored["rows"] and audit["unclassified"] == stored["unclassified"] == []
    assert (stored["modules_with_a_syntactic_use"], len(stored["modules_text_only"])) == (54, 7)
    assert stored["executable_readers_of_the_live_observable"] == 31 and stored["sites"] == len(stored["rows"])
    for row in stored["rows"]:
        assert row["class"] in (review.DISPLAY, review.TEXT, review.BRANCHING, review.SCORING, review.TERMINATION, review.ELIGIBILITY, review.PERSISTENCE,
                                review.TEST_DOC, review.WRITER, review.MENTION), row


def test_a_mention_is_told_apart_from_an_executable_read_and_the_engine_reads_the_live_word_in_five_functions_only():
    rows = {(row["module"], row["function"]): row for row in REVIEW["reader_audit"]["rows"]}
    engine = {function: row for (module, function), row in rows.items() if module == "family_engine.py"}
    live = {function for function, row in engine.items() if row["where"] in review.LIVE and row["executable_read"]}
    assert live == {"_validate", "_order", "_discharge_alarm", "current_findings", "clinical_update"}
    assert engine["_surface"]["class"] == review.WRITER and not engine["_surface"]["executable_read"]
    assert engine["_arrival_anchors"]["where"] == review.ARRIVAL
    # in the source, the three eligibility and outcome readers read the OBSERVABLE; the surface reads the baseline
    import family_engine
    for name in ("_discharge_alarm",):
        assert 'o.get("mental_status")' in inspect.getsource(getattr(family_engine, name))
    assert 'base.get("mental_status"' in inspect.getsource(family_engine._surface) and 'mental_status=mental' in inspect.getsource(family_engine._surface)
    assert not any(row["executable_read"] for row in rows.values() if row["class"] in (review.WRITER, review.MENTION))
    assert rows[("app.py", "_perfusion_response_direction")]["class"] == review.TEST_DOC
    assert "_perfusion_response_direction(" not in (ROOT / "app.py").read_text(encoding="utf-8").replace("def _perfusion_response_direction(", "")


def test_consciousness_authority_has_downstream_side_effects_and_the_surfaces_are_named():
    stored = REVIEW["reader_audit"]
    assert stored["verdict"] == "CONSCIOUSNESS_AUTHORITY_HAS_DOWNSTREAM_SIDE_EFFECTS"
    effects = stored["downstream_effects"]
    assert effects["available_actions"] == ["app.py::_clinical_encounter_workspace", "family_engine.py::_order", "family_engine.py::_validate"]
    assert effects["termination"] == ["family_engine.py::_discharge_alarm"]
    assert effects["scoring"] == ["faculty_analysis.py::<text>", "management_trace_analysis.py::<text>"]
    assert "app.py::observable_state_changed" in effects["scenario_flow"] and "family_engine.py::current_findings" in effects["resident_visible_text"]
    guards = stored["required_guards"]
    assert len(guards) == 8 and [item["exists"] for item in guards].count(True) == 1 and [item["exists"] for item in guards].count(False) == 7
    # the one existing guard is real: every class whose eligibility or outcome reads the word is refused by the authority
    assert set(authority.unsupported_among(("dextrose", "oral_carbohydrate", "antipyretic", "disposition", "discharge"))) == {
        "dextrose", "oral_carbohydrate", "antipyretic", "disposition", "discharge"}
    # the indirect scoring path is real: both analysis payloads select the word from every trace state
    for name in ("management_trace_analysis.py", "faculty_analysis.py"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "mental_status" in text.split("_OBSERVABLE = frozenset(")[1].split(")")[0] and '"observable":' in text


def test_live_a_written_word_does_not_reach_the_legacy_engines_state_through_a_supported_order():
    with ev.shadow(rs.MODE_OFF):
        plain, written = acceptance.Encounter("gi_bleed_57m"), acceptance.Encounter("gi_bleed_57m")
        for encounter in (plain, written):
            encounter.wait_until(5, step=1)
        written.state["observable"]["mental_status"] = "Unresponsive"
        assert authority.canonical(plain.state) != authority.canonical(written.state)
        for encounter in (plain, written):
            encounter.order("Give 1 L of normal saline.")
        # the engine re-wrote the word from its own ladder and nothing else kept it
        assert authority.canonical(plain.state) == authority.canonical(written.state)
        assert plain.state["observable"]["mental_status"] == "Alert"


# -- P3-202: pressure on the active core --------------------------------------------------------------------------------------------------------------

def test_the_pressure_authority_series_is_recertified_on_the_active_core_with_only_explained_differences():
    stored = REVIEW["pressure_recertification"]
    comparison = stored["comparison"]
    assert comparison["verdict"] == "GI_PRESSURE_AUTHORITY_RECERTIFIED_ON_ACTIVE_CORE" and stored["retuned"] is False
    assert (comparison["scenarios_compared"], comparison["minute_records_compared"]) == (34, 78)
    assert comparison["top_level_differences"] == {} and comparison["unexplained_differences"] == [] and comparison["must_match_failures"] == []
    for side in ("closure", "active"):
        totals = comparison[side]
        assert (totals["scenarios"], totals["completed"], totals["halted"], totals["committed_minutes"]) == (34, 26, 8, 66)
        assert totals["all_digests_verified"] and totals["replay_covers_every_committed_minute"] and totals["mixed_trajectory_declared_when_halted_after_a_commit"]
        assert totals["approved"] == ["gi_pressure_committed"] and totals["domain"] == ["sbp", "dbp", "map"] and totals["failure_policy"] == "HARD_FAIL_VISIBLE_TO_FACULTY"
        assert totals["cases"] == ["gi_bleed_57m", "gi_bleed_72f"]
    assert comparison["closure"]["lineage"] == [] and comparison["active"]["lineage"] == ["PHASE2_CLOSURE", "PHASE2_AMENDMENT_1", "PHASE2_AMENDMENT_2"]
    assert set(comparison["differing_fields"]) <= set(review.EXPLAINED_DIFFERENCES)
    assert not set(comparison["differing_fields"]) & set(review.MUST_MATCH)
    # the two amendments' profile fields are OFF in the committed profile: that is why the pressures cannot have moved
    base = fam._bundle_profile(fam.COMMITTED)
    assert base.amendment_2 is None and base.hypoventilation_oxygenation_transmission_fraction is None


def test_live_the_active_core_series_reproduces_the_closure_core_fingerprint_minute_by_minute():
    import test_runtime_authority_series as harness
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv(harness.store.STORE_FLAG, harness.STORE_DIR)
        rows = harness._play_the_battery_with_authority(patch, "gi_bleed_57m")
    assert rs.ShadowSession.observe.__qualname__ == "ShadowSession.observe" and acceptance.Encounter.order.__qualname__ == "Encounter.order"
    fingerprint = REVIEW["pressure_recertification"]["closure_fingerprint"]
    assert len(rows) == 17
    for row in rows:
        stored = fingerprint[f"{row['case']}/{row['scenario']}"]
        assert (row["halted"], row["committed"]) == (stored["halted"], stored["committed"]), row["scenario"]
        live = [[item.get("minute"), item.get("outcome"), item.get("candidate_digest"), item.get("written_digest"), item.get("replay_digest"),
                 item.get("state_digest"), item.get("common_pressures")] for item in row["artifact"]["minutes"]]
        assert _normal(live) == stored["minutes"], row["scenario"]
        if not row["halted"]:
            assert row["replay"]["covers_every_committed_minute"] and row["digest_verified"]


# -- P3-203 and P3-205: the design -----------------------------------------------------------------------------------------------------------------------

def test_the_pair_design_keeps_collapse_and_the_terminal_state_out_and_the_atomic_rule_is_stated():
    design = REVIEW["pair_design"]
    assert design["pressure_domain"]["written"] == ["sbp", "dbp"] and design["pressure_domain"]["derived_by_the_display"] == ["map"]
    assert design["consciousness_domain"]["written"] == ["mental_status"]
    assert design["consciousness_domain"]["mapping"] == {"0": "Alert", "1": "Drowsy", "2": "Obtunded", "3": "Unresponsive"}
    assert set(design["not_authoritative"]) == {"collapse_state", "terminal_state"}
    assert dry.PAIR_DOMAIN == ("sbp", "dbp", "map", "mental_status") and not set(dry.PAIR_DOMAIN) & set(dry.NEVER_WRITTEN)
    assert len(design["atomicity"]) == 4 and "NOT YET in the layer" in design["can_the_architecture_guarantee_it"]
    # the layer's commit really is numeric-pressure only today
    assert "isinstance(value, bool) or not isinstance(value, (int, float))" in inspect.getsource(authority.AuthorityTransaction.commit)


def test_the_collapse_guard_is_precommit_fails_closed_and_is_not_a_terminal_rule():
    guard = REVIEW["collapse_boundary_guard"]
    assert guard["precommit"] is True and guard["means"] == "EXPERIMENT NOT VALID BEYOND THIS PHYSIOLOGICAL BOUNDARY"
    assert "the patient died" in guard["does_not_mean"] and guard["resident_text"].startswith("none")
    bound = binding.bind(str(ROOT))
    probe = dry.PairDryRun.__new__(dry.PairDryRun)
    probe._cleared_through = 100

    def row(state):
        return {"channels": {"collapse_state_index": state}}
    # established at an INTERMEDIATE minute and cleared again by the turn's last minute: still a refusal
    probe._channels = {101: row(0), 102: row(1), 103: row(2), 104: row(1), 105: row(0)}
    assert probe._boundary(105) == {"first_established_minute": 103, "minutes_not_shown": [], "clear": False}
    # a minute the run cannot show is not a cleared minute
    probe._channels = {101: row(0), 103: row(0)}
    assert probe._boundary(103) == {"first_established_minute": None, "minutes_not_shown": [102], "clear": False}
    probe._channels = {101: row(0), 102: {"channels": {}, "channels_unavailable": "x"}}
    assert probe._boundary(102)["clear"] is False
    # impending is not the boundary; the first established minute itself is
    probe._channels = {101: row(1), 102: row(1)}
    assert probe._boundary(102)["clear"] is True
    probe._channels = {101: row(2)}
    assert probe._boundary(101) == {"first_established_minute": 101, "minutes_not_shown": [], "clear": False}
    assert bound.profile.amendment_2.established_burden == 0.625


# -- P3-206 and P3-207: the dry transaction and its series ----------------------------------------------------------------------------------------------------

RUNS = DRY["runs"]
COLUMNS = {name.split("(")[0]: index for index, name in enumerate(next(iter(RUNS.values()))["columns"])}


def test_the_series_covers_both_cases_the_eight_required_scenarios_and_the_two_extras():
    assert sorted(RUNS) == sorted(f"{case}/{scenario}" for case in dry.CASES for scenario in dry.REQUIRED_SCENARIOS + dry.EXTRA_SCENARIOS)
    assert DRY["required_scenarios"] == ["untreated", "early_treatment", "delayed_treatment", "fluid_focused", "blood_focused", "severe_deterioration",
                                         "recovery_after_severe", "late_rescue"]
    assert DRY["extra_scenarios"] == ["recovery_within_window", "unsupported_access"] and DRY["time_limit_min"] == 240
    assert DRY["snapshot"] == binding.bind(str(ROOT)).summary() and DRY["checks"] == list(dry.CHECKS) and len(dry.CHECKS) == 14
    assert all(DRY["matrix"]["the_two_cases_agree"].values())


def test_every_run_is_a_would_commit_window_then_at_most_one_abort_then_a_halt_and_nothing_else():
    for key, run in RUNS.items():
        verdicts = "".join(row[COLUMNS["verdict"]] for row in run["rows"])
        assert set(verdicts) <= set("WAH"), key
        assert verdicts.count("A") <= 1, key
        assert verdicts == "W" * verdicts.count("W") + "A" * verdicts.count("A") + "H" * verdicts.count("H"), key      # never a W after an A
        assert (verdicts.count("A") == 1) == (run["summary"]["first_would_abort"] is not None), key
        summary = run["summary"]
        assert summary["would_commit_minutes"] == verdicts.count("W") and summary["halted_minutes"] == verdicts.count("H"), key
        for row in run["rows"]:
            wrote = row[COLUMNS["would_write_sbp"]] is not None
            assert wrote == (row[COLUMNS["verdict"]] == "W"), (key, row[0])          # a pair is reported only on a would-commit
            if row[COLUMNS["verdict"]] == "W":
                assert row[COLUMNS["failed_checks"]] == "" and row[COLUMNS["minute"]] <= 240, (key, row[0])
                assert row[COLUMNS["collapse_state"]] in (0, 1), (key, row[0])            # never at or past established collapse
                assert row[COLUMNS["common_mental_status"]] in ("Alert", "Drowsy", "Obtunded", "Unresponsive"), (key, row[0])
            if row[COLUMNS["verdict"]] == "A":
                assert row[COLUMNS["failed_checks"]] != "", (key, row[0])
        assert run["bound_run_failures"] == [] and run["legacy_arrested"] is False, key


def test_the_would_commit_window_ends_at_the_first_established_collapse_or_at_the_time_limit_whichever_is_first():
    matrix = DRY["matrix"]["rows"]
    for case in dry.CASES:
        untreated = matrix[f"{case}/untreated"]
        assert (untreated["first_would_commit"], untreated["last_would_commit"], untreated["first_would_abort"]) == (1, 206, 207)
        assert untreated["abort_checks"] == ["collapse_boundary_not_reached"] and untreated["authority_had_begun_at_abort"] is True
        rows = RUNS[f"{case}/untreated"]["rows"]
        first_established = next(row[0] for row in rows if row[COLUMNS["collapse_state"]] == 2)
        assert first_established == 207 == min(dry.TIME_LIMIT_MIN, first_established) and untreated["halted_minutes"] == 240 - 207
        # the late rescue is ordered AFTER the boundary: the experiment had already stopped, eight minutes before the order
        rescue = matrix[f"{case}/late_rescue"]
        assert (rescue["last_would_commit"], rescue["first_would_abort"], rescue["orders"][0][0]) == (206, 207, 215)
        # treated courses never reach it and run to their horizon
        for scenario in ("early_treatment", "delayed_treatment", "fluid_focused", "blood_focused", "severe_deterioration", "recovery_within_window"):
            entry = matrix[f"{case}/{scenario}"]
            assert entry["first_would_abort"] is None and entry["first_would_commit"] == 1 and entry["halted_minutes"] == 0, (case, scenario)
        assert matrix[f"{case}/severe_deterioration"]["last_would_commit"] == 240
        # a four-unit transfusion takes 120 minutes of the engine's clock in ONE turn: ordered at 158, its turn ends at 278, past the limit
        recovery = matrix[f"{case}/recovery_after_severe"]
        assert (recovery["orders"][0][0], recovery["orders"][0][1], recovery["last_would_commit"], recovery["first_would_abort"]) == (158, 278, 158, 278)
        assert recovery["abort_checks"] == ["window_open"]
        inside = matrix[f"{case}/recovery_within_window"]
        assert (inside["orders"][0][0], inside["orders"][0][1], inside["last_would_commit"]) == (158, 218, 240)


def test_an_unsupported_class_aborts_after_authority_began_and_no_later_minute_would_commit():
    for case in dry.CASES:
        entry = DRY["matrix"]["rows"][f"{case}/unsupported_access"]
        assert (entry["last_would_commit"], entry["first_would_abort"], entry["authority_had_begun_at_abort"]) == (10, 70, True)
        assert entry["abort_checks"] == ["supported_management", "pressure_validated"] and entry["abort_stage"] == "validation"
        assert RUNS[f"{case}/unsupported_access"]["halt"]["detail"]["supported_management"] == {"unsupported": ["vascular_access"]}
        assert "INVALID_FOR_CONTINUATION" in RUNS[f"{case}/unsupported_access"]["halt"]["consequence"]
    assert authority.unsupported_among(("vascular_access",)) == ("vascular_access",)


def test_the_pair_is_one_course_the_recovery_gives_one_band_back_at_a_time_and_the_words_follow_f():
    for case in dry.CASES:
        rows = RUNS[f"{case}/recovery_within_window"]["rows"]
        words = [row[COLUMNS["common_mental_status"]] for row in rows]
        order = ["Alert", "Drowsy", "Obtunded", "Unresponsive"]
        levels = [order.index(word) for word in words]
        peak = levels.index(3)
        assert max(levels) == 3 and levels[-1] == 0
        # one band at a time on the way up (every minute is a turn there); after the order the word only improves. The order's own turn spans
        # the 60 minutes of its infusion, so the rows go from Unresponsive at 158 to Alert at 218 with no row between: one turn, one transaction.
        assert all(0 <= b - a <= 1 for a, b in zip(levels[:peak + 1], levels[1:peak + 1]))
        assert all(b <= a for a, b in zip(levels[peak:], levels[peak + 1:]))
        assert (rows[peak][0], rows[peak + 1][0]) == (158, 218) and words[peak + 1] == "Alert"
        for row in rows:
            burden = row[COLUMNS["F"]]
            assert order[sum(1 for cut in sc.CATEGORY_CUTS if burden >= cut - 1e-9)] == row[COLUMNS["common_mental_status"]] or \
                abs(min(abs(burden - cut) for cut in sc.CATEGORY_CUTS)) < 1e-4, (case, row[0])


@pytest.mark.parametrize("scenario", ["early_treatment", "unsupported_access"])
def test_live_the_dry_run_is_deterministic_reproduces_the_record_and_leaves_the_legacy_encounter_exactly_as_it_was(scenario):
    result = dry.run("gi_bleed_57m", scenario)
    stored = RUNS[f"gi_bleed_57m/{scenario}"]
    assert result["summary"]["record_digest"] == stored["summary"]["record_digest"]
    assert _normal(dry.compact(result))["rows"] == stored["rows"]
    # the same orders with the shadow OFF and no dry run: the legacy trajectory is the same at every minute both runs sampled
    alone = {item["minute"]: item for item in dry.legacy_alone("gi_bleed_57m", scenario, result["orders"])}
    beside = {item["minute"]: item for item in result["legacy_track"]}
    assert set(alone) == set(beside) and len(alone) >= 20
    assert all(alone[minute] == beside[minute] for minute in alone)
    # nothing leaked into the process: the patches are gone and the registries are what they were
    assert rs.ShadowSession.observe.__qualname__ == "ShadowSession.observe" and acceptance.Encounter.order.__qualname__ == "Encounter.order"
    assert sorted(authority.APPROVED_SNAPSHOTS) == ["gi_pressure_committed"] and rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    assert sc.WITNESSES["CENTER_REFERENCE"].to_dict() != SNAPSHOT["values"]


# -- attacks on the dry transaction (live, short) -----------------------------------------------------------------------------------------------------------

#: A six-minute untreated course for the attacks: long enough for a would-commit window and a refusal, short enough to run many.
dry.SCENARIOS.setdefault("probe_short", {"at": {}, "horizon": 6})


def _first_abort(result):
    return next(item for item in result["records"] if item["verdict"] == dry.WOULD_ABORT)


def test_attack_a_run_whose_profile_is_not_the_bound_one_never_would_commit():
    def swap(run, encounter):
        run.runner.profile = dataclasses.replace(run.runner.profile, amendment_2=sc.WITNESSES["LOW"])
    result = dry.run("gi_bleed_57m", "probe_short", tamper=swap)
    assert result["summary"]["would_commit_minutes"] == 0 and result["summary"]["first_would_abort"] == 1
    assert "snapshot_bound" in _first_abort(result)["failed_checks"] and result["halt"]["authority_had_begun"] is False
    assert "authority never began" in result["halt"]["consequence"]

    def other_adapter(run, encounter):
        run.runner.adapter = fam.GiHaemorrhageAdapter.witness("HIGH")
    result = dry.run("gi_bleed_57m", "probe_short", tamper=other_adapter)
    assert result["summary"]["would_commit_minutes"] == 0 and "snapshot_bound" in _first_abort(result)["failed_checks"]


def test_attack_a_wrong_lineage_never_would_commit():
    def wrong(run, encounter):
        run.lineage = {**run.lineage, "bytes_digest": "0" * 64}
    result = dry.run("gi_bleed_57m", "probe_short", tamper=wrong)
    assert result["summary"]["would_commit_minutes"] == 0 and "lineage_certified" in _first_abort(result)["failed_checks"]


def test_attack_consciousness_fails_while_pressure_passes_and_no_pressure_alone_would_be_written():
    def break_at_three(run, encounter):
        real = run._advance

        def advance(session, minute):
            real(session, minute)
            if minute >= 3:
                run._channels.pop(minute, None)          # the bound run cannot show this minute
        run._advance = advance
    result = dry.run("gi_bleed_57m", "probe_short", tamper=break_at_three)
    refused = _first_abort(result)
    assert refused["minute"] == 3 and result["summary"]["last_would_commit"] == 2 and result["halt"]["authority_had_begun"] is True
    assert "consciousness_candidate_present" in refused["failed_checks"] and "pressure_validated" not in refused["failed_checks"]
    assert "collapse_boundary_not_reached" in refused["failed_checks"]            # a minute it cannot show is not a cleared minute
    assert refused["would_write"] is None and refused["would_move"] is None
    assert all(item["verdict"] == dry.HALTED for item in result["records"] if item["minute"] > 3)


def test_attack_pressure_fails_while_consciousness_passes_and_no_pair_is_reported(monkeypatch):
    real = authority.AuthoritySite._replayed_point

    def drifted(artifact, minute):
        point = real(artifact, minute)
        return point if point is None or minute < 3 else {**point, "sbp": point["sbp"] + 1.0}
    monkeypatch.setattr(authority.AuthoritySite, "_replayed_point", staticmethod(drifted))
    result = dry.run("gi_bleed_57m", "probe_short")
    refused = _first_abort(result)
    assert refused["minute"] == 3 and refused["failed_checks"] == ["pressure_validated"]
    assert refused["detail"]["pressure_validated"] == {"validation_failures": ["minute_reproducible"]}
    assert refused["would_write"] is None and result["summary"]["last_would_commit"] == 2


def test_attack_the_same_minute_twice_an_undeclared_turn_and_no_resurrection_after_a_halt():
    captured = {}

    def keep(run, encounter):
        captured["run"], captured["encounter"] = run, encounter
    result = dry.run("gi_bleed_57m", "probe_short", tamper=keep)
    run, encounter = captured["run"], captured["encounter"]
    assert result["summary"]["would_commit_minutes"] == 6 and result["halt"] is None
    before = authority.canonical(encounter.state)
    again = run.minute(None, encounter.state, encounter.shadow, [{"type": "reassessment"}], "again")
    assert again["verdict"] == dry.WOULD_ABORT and "minute_not_already_committed" in again["failed_checks"]
    assert authority.canonical(encounter.state) == before
    later = run.minute(None, encounter.state, encounter.shadow, [{"type": "reassessment"}], "later")
    assert later["verdict"] == dry.HALTED and run.phase == dry.HALTED and run.would_commit[-1] == 6
    # an undeclared turn fails closed on a fresh run
    fresh = dry.PairDryRun(binding.bind(str(ROOT)), "gi_bleed_57m", acceptance.Encounter("gi_bleed_57m").state)
    assert fresh.phase == dry.NOT_STARTED


def test_attack_a_time_limit_and_an_ineligible_case_are_refused():
    result = dry.run("gi_bleed_57m", "probe_short", time_limit=3)
    assert (result["summary"]["last_would_commit"], result["summary"]["first_would_abort"]) == (3, 4) and _first_abort(result)["failed_checks"] == ["window_open"]

    def other_case(run, encounter):
        run.case_id = "acs_58m"
    result = dry.run("gi_bleed_57m", "probe_short", tamper=other_case)
    assert result["summary"]["would_commit_minutes"] == 0 and "case_eligible" in _first_abort(result)["failed_checks"]


def test_the_patches_are_restored_even_when_the_block_raises_and_the_state_guard_is_real():
    with pytest.raises(RuntimeError):
        with dry.observing({}):
            raise RuntimeError("boom")
    assert rs.ShadowSession.observe.__qualname__ == "ShadowSession.observe" and acceptance.Encounter.order.__qualname__ == "Encounter.order"
    # the guard that says "the dry run changed the encounter state" raises when something does
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter("gi_bleed_57m")
        run = dry.PairDryRun(binding.bind(str(ROOT)), "gi_bleed_57m", encounter.state)
        real = run._advance

        def meddle(session, minute):
            real(session, minute)
            encounter.state["observable"]["sbp"] = 1
        run._advance = meddle
        with dry.observing({id(encounter.shadow): run}):
            with pytest.raises(dry.DryRunViolation):
                encounter.wait_until(1, step=1)
    assert rs.ShadowSession.observe.__qualname__ == "ShadowSession.observe"


# -- P3-208 and P3-209: the review and the checkpoint -------------------------------------------------------------------------------------------------------

def test_the_adversarial_review_status_is_said_and_never_assumed():
    # The independent review (P3-208) is recorded as PENDING until its findings are in the record: nothing is claimed about it before.
    assert REVIEW["adversarial_review_status"] in ("PENDING", "DONE")
    assert (REVIEW["adversarial_review_status"] == "DONE") == bool(REVIEW["adversarial_review"])
    assert REVIEW["checkpoint"]["provisional"] == (REVIEW["adversarial_review_status"] == "PENDING")


def test_the_checkpoint_returns_exactly_one_legal_verdict_names_its_blockers_and_grants_nothing():
    checkpoint = REVIEW["checkpoint"]
    assert checkpoint["verdict"] == rec.CHECKPOINT == "PRESSURE_READY_BUT_CONSCIOUSNESS_NOT_READY" and checkpoint["verdict"] in checkpoint["options"]
    assert len(checkpoint["options"]) == 4 and checkpoint["options"].count(checkpoint["verdict"]) == 1
    assert [item["id"] for item in checkpoint["blockers"]] == [f"C{n}" for n in range(1, 9)]
    assert "None of this is an authority grant" in checkpoint["reading"]
    # the two halves of the verdict are the two measured facts
    assert REVIEW["pressure_recertification"]["comparison"]["verdict"] == "GI_PRESSURE_AUTHORITY_RECERTIFIED_ON_ACTIVE_CORE"
    assert REVIEW["reader_audit"]["verdict"] == "CONSCIOUSNESS_AUTHORITY_HAS_DOWNSTREAM_SIDE_EFFECTS"
    assert set(REVIEW["consciousness_review"]["faculty_table"][0]["faculty_answers"].values()) == {None}
