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


def _low_bound():
    """A ``BoundSnapshot`` made BY HAND: version 1's identity on the LOW witness's values (the independent review's attack 1)."""
    low = sc.WITNESSES["LOW"].to_dict()
    profile = binding.build_profile(low)
    return binding.BoundSnapshot(binding.V1_ID, binding.V1_VERSION, tuple((name, float(low[name])) for name in sc.FIELDS), binding.V1_IDENTITY_DIGEST,
                                 binding.V1_RECORD_DIGEST, binding.V1_FILE_SHA256, binding.V1_CORE_VERSION, binding.V1_CORE_DIGEST,
                                 binding.PRESSURE_POINT, profile, binding.profile_digest(profile))


def test_review_what_is_bound_is_what_was_built_and_a_hand_made_binding_is_not_one():
    real = binding.bind(str(ROOT))
    assert binding.bound_is_v1(real) and real.profile_digest == binding.V1_PROFILE_DIGEST == BOUND_PROFILE_DIGEST
    assert an.digest(SNAPSHOT) == binding.V1_FULL_DIGEST and RATIFICATION["ratification_digest"] == binding.V1_RATIFICATION_DIGEST == RATIFICATION_DIGEST
    forged = _low_bound()
    assert forged.snapshot_id == real.snapshot_id and forged.identity_digest == real.identity_digest      # it SAYS it is version 1
    assert not binding.bound_is_v1(forged)
    with pytest.raises(binding.SnapshotBindingError):
        binding.BoundSnapshotAdapter(forged)
    with pytest.raises(binding.SnapshotBindingError):
        dry.PairDryRun(forged, "gi_bleed_57m", {"sim_time": 0})
    with pytest.raises(binding.SnapshotBindingError):
        dry.run("gi_bleed_57m", "probe_short", bound=forged)
    # a value forced into the real binding after the fact is seen too
    edited = binding.bind(str(ROOT))
    object.__setattr__(edited.profile, "amendment_2", sc.WITNESSES["HIGH"])
    assert not binding.bound_is_v1(edited)


def test_review_a_record_that_answers_differently_when_verified_and_when_built_cannot_change_the_profile():
    class Liar(float):
        """Reads as the ratified number, converts to another one."""
        def __new__(cls, real, told):
            self = super().__new__(cls, real)
            self._told = told
            return self

        def __float__(self):
            return self._told

    class Flipping(dict):
        """Answers with the ratified values for a while, then with the LOW witness's."""
        reads = 0

        def __getitem__(self, key):
            type(self).reads += 1
            return sc.WITNESSES["LOW"].to_dict()[key] if type(self).reads > 30 else super().__getitem__(key)

    lying = copy.deepcopy(SNAPSHOT)
    lying["values"]["burden_rise_tau"] = Liar(lying["values"]["burden_rise_tau"], 1.5)
    lying["values"]["established_burden"] = Liar(lying["values"]["established_burden"], 0.55)
    flipping = copy.deepcopy(SNAPSHOT)
    flipping["values"] = Flipping(flipping["values"])
    for record in (lying, flipping):
        bound = binding.bind(str(ROOT), record=record)             # reduced to plain data first: one answer, the one both steps read
        assert binding.bound_is_v1(bound) and bound.profile.amendment_2.to_dict() == SNAPSHOT["values"]
        assert bound.profile_digest == binding.V1_PROFILE_DIGEST
    assert binding.plain(float("nan")) is None and binding.plain({1, 2}) is None


def test_review_a_forged_ratification_a_superseded_record_and_foreign_bytes_are_refused():
    nine_fields = {"status": binding.RATIFIED, "snapshot_id": binding.V1_ID, "version": 1, "identity_digest": binding.V1_IDENTITY_DIGEST,
                   "record_digest": binding.V1_RECORD_DIGEST, "snapshot_file_sha256": binding.V1_FILE_SHA256, "values": SNAPSHOT["values"],
                   "is_not": list(binding.IS_NOT), "authority": {"added_to_an_approved_authority_snapshot_registry": False}}
    rewritten = {**copy.deepcopy(RATIFICATION), "faculty_decisions": {"FD-AUTH-01": "approved for authority"}, "ratification_digest": "0" * 64}
    relabelled = {**copy.deepcopy(RATIFICATION), "ratified_for": "AUTHORITY"}                # the pinned digest left in place over another text
    for ratification in (nine_fields, rewritten, relabelled):
        with pytest.raises(binding.SnapshotBindingError) as refused:
            binding.bind(str(ROOT), record=copy.deepcopy(SNAPSHOT), ratification=ratification)
        assert refused.value.reasons == (binding.NOT_RATIFIED,)
    raw = (ROOT / an.SNAPSHOT_FILE).read_bytes()
    superseded = copy.deepcopy(SNAPSHOT)
    superseded["immutability"]["superseded_by"] = "GI_DEVELOPMENT_SNAPSHOT_V2"
    for kwargs in ({"record": superseded}, {"record": superseded, "raw": raw}):
        with pytest.raises(binding.SnapshotBindingError) as refused:
            binding.bind(str(ROOT), **kwargs)
        assert binding.WRONG_DIGEST in refused.value.reasons
    assert binding.bind(str(ROOT), record=copy.deepcopy(SNAPSHOT), raw=raw).profile_digest == binding.V1_PROFILE_DIGEST


def test_review_an_offered_lineage_cannot_stand_in_for_the_live_one(monkeypatch):
    from clinical_core import amendment_2 as a2
    forged = {"version_id": binding.V1_CORE_VERSION, "digest": binding.V1_CORE_DIGEST, "bytes_digest": binding.V1_CORE_DIGEST, "certified": True}
    assert binding.lineage_is_v1(forged) and binding.lineage_is_v1(binding.live_lineage())
    monkeypatch.setattr(a2, "amended_core_digest_now", lambda: "f" * 64)       # the core's own bytes no longer hash to the certified member
    assert not binding.lineage_is_v1(binding.live_lineage())
    for lineage in (None, forged):
        with pytest.raises(binding.SnapshotBindingError) as refused:
            binding.bind(str(ROOT), record=copy.deepcopy(SNAPSHOT), lineage=lineage)
        assert refused.value.reasons == (binding.WRONG_CORE_LINEAGE,)


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


def test_review_coherence_is_checked_over_every_compared_minute_and_a_contradiction_outside_the_episodes_is_seen():
    stored = REVIEW["consciousness_review"]["whole_run_coherence"]
    assert _normal(review.run_coherence(COUNTERFACTUAL, SENSITIVITY, SNAPSHOT["values"])) == stored
    assert (stored["runs"], stored["compared_minutes"], stored["contradictions"], stored["verdict"]) == (14, 1930, [], review.COHERENT)
    assert set(stored["violations"].values()) == {0}
    # the independent review planted a contradiction at a minute where the two words agree: no episode covers it, the whole run does
    planted = copy.deepcopy(COUNTERFACTUAL)
    key = sorted(planted["required_runs"])[0]
    domain = planted["required_runs"][key]["domains"]["consciousness_category"]
    assert domain["candidate"][5] == domain["legacy"][5] == 0
    domain["candidate"][5] = 3
    assert review.run_coherence(planted, SENSITIVITY, SNAPSHOT["values"])["contradictions"] == [key]


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
    assert stored["executable_readers_of_the_live_observable"] == 32 and stored["sites"] == len(stored["rows"]) == 119
    assert {key: len(value) for key, value in stored["live_readers_by_class"].items()} == {
        review.DISPLAY: 3, review.TEXT: 10, review.BRANCHING: 8, review.SCORING: 3, review.TERMINATION: 1, review.ELIGIBILITY: 3,
        review.PERSISTENCE: 3, review.TEST_DOC: 1}
    # the inventory says what it cannot see, and it is not offered as a proof
    assert stored["scan_limits"] == list(review.SCAN_LIMITS) and len(stored["scan_limits"]) == 4
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
    assert effects["scoring"] == ["faculty_analysis.py::<text>", "faculty_portal.py::<consumer of record_findings.py>",
                                  "faculty_report.py::<consumer of record_findings.py>", "management_trace_analysis.py::<text>",
                                  "management_trace_report.py::<consumer of record_findings.py>", "record_findings.py::<module>"]
    assert "app.py::observable_state_changed" in effects["scenario_flow"] and "family_engine.py::current_findings" in effects["resident_visible_text"]
    guards = stored["required_guards"]
    assert len(guards) == 9 and [item["exists"] for item in guards].count(True) == 1 and [item["exists"] for item in guards].count(False) == 8
    # the one existing guard is real: every class whose eligibility or outcome reads the word is refused by the authority
    assert set(authority.unsupported_among(("dextrose", "oral_carbohydrate", "antipyretic", "disposition", "discharge"))) == {
        "dextrose", "oral_carbohydrate", "antipyretic", "disposition", "discharge"}
    # the indirect scoring path is real: both analysis payloads select the word from every trace state
    for name in ("management_trace_analysis.py", "faculty_analysis.py"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "mental_status" in text.split("_OBSERVABLE = frozenset(")[1].split(")")[0] and '"observable":' in text


def test_review_the_hold_of_an_ai_suggestion_reads_the_word_and_the_audit_now_says_so():
    """The independent review's finding: ``record_findings`` was classed as persistence. It decides whether the faculty portal HOLDS an AI
    suggestion, and it does so from whether the word ever changed -- which a consciousness authority changes."""
    import record_findings as findings
    row = next(item for item in REVIEW["reader_audit"]["rows"] if item["module"] == "record_findings.py")
    assert row["class"] == review.SCORING and row["where"] == review.GI_AFTER and row["executable_read"] and row["guard"]
    assert ("mental_status", "alertness") in findings.OBSERVED

    def trace(words):
        return [{"decision_time_min": index * 10, "response_time_min": index * 10 + 10,
                 "state_before": {"observable": {"sbp": 100 - index, "mental_status": words[index]}},
                 "state_after": {"observable": {"sbp": 99 - index, "mental_status": words[index + 1]}}} for index in range(len(words) - 1)]
    claim = "The resident did not reassess alertness after the transfusion."
    constant, moving = findings.encounter_limits(trace(["Alert"] * 4)), findings.encounter_limits(trace(["Alert", "Drowsy", "Drowsy", "Alert"]))
    assert "alertness" in constant["inert_observables"] and "alertness" not in moving["inert_observables"]
    assert findings.unsettled(claim, constant) and not findings.unsettled(claim, moving)
    # its consumers do not name the word, so no scan finds them: they are listed by hand and verified to import it
    stored = REVIEW["reader_audit"]["indirect_consumers"]
    assert _normal(review.indirect_consumers(str(ROOT))) == stored
    assert stored == {"record_findings.py": {"verified": ["faculty_portal.py", "faculty_report.py", "management_trace_report.py"],
                                            "not_found_or_not_importing": []}}


def test_review_the_engine_surface_reads_only_the_baseline_and_the_claim_is_derived_from_the_source():
    stored = REVIEW["reader_audit"]
    surface = review.surface_reads(str(ROOT))
    assert _normal(surface) == stored["surface_reads_of_the_key"]
    assert surface == {"function_found": True, "receivers": ["base"] * 4, "not_the_baseline": [], "reads_the_live_word": False}
    assert stored["legacy_physiology_reads_the_live_word"] is False
    # the claim can be false: a surface that reads the live observable is seen, and so is a surface that is not found
    reading = "def _surface(state, base):\n    mental = state.get('observable', {}).get('mental_status')\n    return base.get('mental_status')\n"
    assert review.surface_reads(source=reading)["reads_the_live_word"] is True
    assert review.surface_reads(source=reading)["not_the_baseline"] == ["state.get('observable', {})"]
    assert review.surface_reads(source="def other():\n    pass\n")["reads_the_live_word"] is True


WORD_SCRIPT = ("Reassess in 2 minutes.", "Give oxygen by nasal cannula at 2 L/min.", "Give pantoprazole 80 mg IV.", "Order a hemoglobin.",
               "Give 1 L of normal saline.", "Reassess in 5 minutes.", "Transfuse 2 units of packed red blood cells.", "Request urgent upper endoscopy.",
               "Consult gastroenterology.", "Reassess in 10 minutes.", "Reassess in 30 minutes.", "Reassess in 30 minutes.")


def _played_with_the_word(case, word):
    states = []
    with ev.shadow(rs.MODE_OFF):
        encounter = acceptance.Encounter(case)
        for text in WORD_SCRIPT:
            started = int(encounter.minute)
            if word is not None:
                encounter.state["observable"]["mental_status"] = word      # what a consciousness commit would have left in the state
            encounter.order(text)
            states.append((started, copy.deepcopy(encounter.state)))
    return states, copy.deepcopy(encounter.ledger)


@pytest.mark.parametrize("case", ["gi_bleed_57m", "gi_bleed_72f"])
def test_live_a_written_word_never_reaches_the_legacy_engines_physiology_and_survives_only_a_zero_minute_turn(case):
    """Twelve supported turns, the word forced before each one. The engine's physiology, its family state and the order ledger are identical;
    the word itself survives exactly the turns that did not advance the clock (the two consults)."""
    plain_states, plain_ledger = _played_with_the_word(case, None)
    for word in ("Unresponsive", "Obtunded", "Drowsy"):
        states, ledger = _played_with_the_word(case, word)
        assert authority.canonical(ledger) == authority.canonical(plain_ledger)
        kept = []
        for (started, plain), (_, written) in zip(plain_states, states):
            without = copy.deepcopy(written)
            without["observable"]["mental_status"] = plain["observable"]["mental_status"]
            assert authority.canonical(without) == authority.canonical(plain)                      # nothing but the word differs, ever
            assert authority.canonical(written["family_state"]) == authority.canonical(plain["family_state"])
            if written["observable"]["mental_status"] != plain["observable"]["mental_status"]:
                assert int(written["sim_time"]) == started                                         # a zero-minute turn
                kept.append(started)
        assert len(kept) == 2 and {state["observable"]["mental_status"] for _, state in plain_states} == {"Alert"}


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


def test_review_the_pressure_comparison_cannot_pass_on_an_empty_a_truncated_or_a_fieldless_series():
    def minute(index, **extra):
        return {**{name: f"{name}@{index}" for name in review.MUST_MATCH}, "minute": index, "outcome": "COMMITTED", **extra}

    def dump(minutes):
        meta = {name: None for name in ("layer", "authority_module", "phase2_digest", "approved", "failure_policy", "domain", "cases", "lineage")}
        if minutes is None:
            return {"rows": [], "meta": meta}
        # the row counters are those of the WHOLE series on both sides, as in the review's probe: only the artifact's minutes can tell them apart
        row = {"case": "gi_bleed_57m", "scenario": "s", "halted": False, "halt_reason": None, "committed": 3, "minutes": 3,
               "digest_verified": True, "kinds": [], "settled_classes": [], "site": True, "replay": {"covers_every_committed_minute": True},
               "artifact": {"minutes": minutes, "mixed_trajectory": False}}
        return {"rows": [row], "meta": meta}
    whole = [minute(1), minute(2), minute(3)]
    ok = "GI_PRESSURE_AUTHORITY_RECERTIFIED_ON_ACTIVE_CORE"
    assert review.compare_pressure_series(dump(whole), dump(copy.deepcopy(whole)))["verdict"] == ok
    empty = review.compare_pressure_series(dump(None), dump(None))
    assert empty["verdict"] == "BLOCKED" and "nothing_was_compared" in empty["top_level_differences"]
    lost = review.compare_pressure_series(dump(whole), dump(whole[:1]))                 # the same counters, two minutes gone: zip() would drop them
    assert lost["verdict"] == "BLOCKED" and "minute_records_differ_in_number_or_order" in lost["top_level_differences"]
    bare = [{"minute": 1, "outcome": "COMMITTED"}, {"minute": 2, "outcome": "COMMITTED"}]
    fieldless = review.compare_pressure_series(dump(bare), dump(copy.deepcopy(bare)))
    assert fieldless["verdict"] == "BLOCKED" and any(item[2].endswith("ABSENT") for item in fieldless["must_match_failures"])
    one_sided = review.compare_pressure_series(dump(whole), dump([minute(1), minute(2), {k: v for k, v in minute(3).items() if k != "replay_digest"}]))
    assert one_sided["verdict"] == "BLOCKED"
    # a minute that did not commit legitimately carries no written state: that absence, on both sides, is not a failure
    aborted = [minute(1), {k: v for k, v in minute(2, outcome="ABORTED").items() if k not in review.COMMIT_ONLY}]
    assert review.compare_pressure_series(dump(aborted), dump(copy.deepcopy(aborted)))["verdict"] == ok


def test_review_two_limits_of_the_existing_site_are_read_from_the_source_and_declared_not_changed():
    stored = REVIEW["authority_site_coverage"]
    assert _normal(review.site_coverage(str(ROOT))) == stored
    route = stored["time_outside_an_order_turn"]
    assert route["route"] == "app.spend_clinical_time" and route["callers_in_app"] == 3 and route["calls_the_shadow"] is True
    assert route["calls_the_authority_site"] is False and route["the_site_names_the_route"] is False and route["authority_site_call_sites_in_app"] == 1
    assert "NOT executed with an authority" in route["evidence"]
    assert stored["failures_read_by_the_site"]["rule_in_the_site"] is True
    blockers = {item["id"]: item for item in REVIEW["checkpoint"]["blockers"]}
    assert "spend_clinical_time" in blockers["C9"]["blocker"] and "LAST minute" in blockers["C10"]["blocker"]
    assert "binds the pressure half too" in blockers["C9"]["kind"] and "binds the pressure half too" in blockers["C10"]["kind"]
    # the development harness plays orders only: it never takes the route (that is why the recertification says nothing about it)
    import test_runtime_authority_series as harness
    assert "observe_time" not in inspect.getsource(harness) and "spend_clinical_time" not in inspect.getsource(harness)


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
    assert len(design["atomicity"]) == 6 and "NOT YET in the layer" in design["can_the_architecture_guarantee_it"]
    assert dry.CHECKS[:4] == ("transaction_completed", "encounter_state_untouched", "turn_has_a_transaction_site", "turn_was_observed")
    assert len(dry.CHECKS) == 18 and DRY["checks"] == list(dry.CHECKS)
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
    # a state that is not exactly one of the core's three is a minute not shown (True is not "impending")
    for odd in (True, 2.0, "2", 3, -1, None):
        probe._channels = {101: row(odd)}
        assert probe._boundary(101) == {"first_established_minute": None, "minutes_not_shown": [101], "clear": False}, odd
    assert bound.profile.amendment_2.established_burden == 0.625


# -- P3-206 and P3-207: the dry transaction and its series ----------------------------------------------------------------------------------------------------

RUNS = DRY["runs"]
COLUMNS = {name.split("(")[0]: index for index, name in enumerate(next(iter(RUNS.values()))["columns"])}


def test_the_series_covers_both_cases_the_eight_required_scenarios_and_the_two_extras():
    assert sorted(RUNS) == sorted(f"{case}/{scenario}" for case in dry.CASES for scenario in dry.REQUIRED_SCENARIOS + dry.EXTRA_SCENARIOS)
    assert DRY["required_scenarios"] == ["untreated", "early_treatment", "delayed_treatment", "fluid_focused", "blood_focused", "severe_deterioration",
                                         "recovery_after_severe", "late_rescue"]
    assert DRY["extra_scenarios"] == ["recovery_within_window", "unsupported_access"] and DRY["time_limit_min"] == 240
    assert DRY["snapshot"] == binding.bind(str(ROOT)).summary() and DRY["checks"] == list(dry.CHECKS) and len(dry.CHECKS) == 18
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


def test_attack_a_wrong_lineage_never_would_commit(monkeypatch):
    # a wrong lineage OFFERED by the caller refuses; so does writing one over the reading (it is read again every minute, so this changes nothing)
    def offered(run, encounter):
        run.offered_lineage = {**binding.live_lineage(), "bytes_digest": "0" * 64}
    result = dry.run("gi_bleed_57m", "probe_short", tamper=offered)
    assert result["summary"]["would_commit_minutes"] == 0 and "lineage_certified" in _first_abort(result)["failed_checks"]

    def overwritten(run, encounter):
        run.lineage = {**run.lineage, "bytes_digest": "0" * 64}
    assert dry.run("gi_bleed_57m", "probe_short", tamper=overwritten)["summary"]["would_commit_minutes"] == 6
    # the core's bytes change AFTER the dry run opened, and the caller offers a forged "good" lineage: the next minute refuses
    from clinical_core import amendment_2 as a2
    forged = {"version_id": binding.V1_CORE_VERSION, "digest": binding.V1_CORE_DIGEST, "bytes_digest": binding.V1_CORE_DIGEST, "certified": True}
    real = a2.amended_core_digest_now

    def bytes_move_at_three(run, encounter):
        run.offered_lineage = dict(forged)
        advance = run._advance

        def moved(session, minute):
            if minute >= 3:
                monkeypatch.setattr(a2, "amended_core_digest_now", lambda: "f" * 64)
            advance(session, minute)
        run._advance = moved
    result = dry.run("gi_bleed_57m", "probe_short", tamper=bytes_move_at_three)
    monkeypatch.setattr(a2, "amended_core_digest_now", real)
    assert result["summary"]["last_would_commit"] == 2 and _first_abort(result)["minute"] == 3
    assert _first_abort(result)["failed_checks"] == ["lineage_certified"] and result["halt"]["authority_had_begun"] is True


def test_review_attack_the_arrival_anchors_of_the_bound_run_cannot_be_moved():
    """The independent review's attack: the ten values untouched, the bound run's arrival level raised. The readings that do not depend on the
    ten magnitudes stay equal, so only the anchors show it."""
    for level in (1, 2, 3):
        def raised(run, encounter, level=level):
            run.runner.anchors = dataclasses.replace(run.runner.anchors, consciousness_level=level)
        result = dry.run("gi_bleed_57m", "probe_short", tamper=raised)
        assert result["summary"]["would_commit_minutes"] == 0 and _first_abort(result)["failed_checks"][0] == "snapshot_bound", level
        assert all(item["would_write"] is None for item in result["records"])


def test_review_attack_an_exception_inside_the_transaction_is_an_abort_and_never_reaches_the_legacy_turn(monkeypatch):
    real = authority.AuthoritySite._replayed_point

    def crashes_at_three(artifact, minute):
        if minute >= 3:
            raise RuntimeError("replay crashed")
        return real(artifact, minute)
    monkeypatch.setattr(authority.AuthoritySite, "_replayed_point", staticmethod(crashes_at_three))
    result = dry.run("gi_bleed_57m", "probe_short")                         # does not raise: the turn of minute 3 completed in the legacy engine
    refused = _first_abort(result)
    assert refused["minute"] == 3 and refused["failed_checks"] == ["transaction_completed"] and "replay crashed" in refused["detail"]["transaction_completed"]
    assert result["halt"]["stage"] == "exception" and result["halt"]["authority_had_begun"] is True and result["summary"]["last_would_commit"] == 2
    assert [item["verdict"] for item in result["records"] if item["minute"] > 3] == [dry.HALTED] * 3            # no later minute would commit
    # the legacy encounter is the one nobody observed: same clock, same number of entries, same ledger rows
    monkeypatch.setattr(authority.AuthoritySite, "_replayed_point", staticmethod(real))
    with ev.shadow(rs.MODE_OFF):
        alone = acceptance.Encounter("gi_bleed_57m")
        alone.wait_until(6, step=1)
    beside = result["encounter"]
    assert (int(beside.minute), len(beside.entries), len(beside.ledger)) == (int(alone.minute), len(alone.entries), len(alone.ledger)) == (6, 6, 6)
    assert authority.canonical(beside.state["observable"]) == authority.canonical(alone.state["observable"])


def test_review_attack_time_outside_an_order_turn_and_a_turn_nobody_saw_are_refused():
    with ev.shadow(rs.MODE_SHADOW_COMPARE), dry.observing(registry := {}):
        encounter = acceptance.Encounter("gi_bleed_57m")
        run = dry.PairDryRun(binding.bind(str(ROOT)), "gi_bleed_57m", encounter.state)
        registry[id(encounter.shadow)] = run
        encounter.wait_until(2, step=1)
        assert [item["verdict"] for item in run.records] == [dry.WOULD_COMMIT] * 2
        # the route of app.spend_clinical_time: the engine lets a minute pass and the shadow is told through observe_time
        import family_engine
        before = encounter.shadow.capture(encounter.state)
        passed = family_engine.advance_clinical_time(encounter.state, 1, label="history question")
        encounter.shadow.observe_time(before, encounter.state, passed)
        refused = run.records[-1]
        assert refused["route"] == dry.TIME_OUTSIDE_AN_ORDER and refused["verdict"] == dry.WOULD_ABORT
        assert refused["failed_checks"][0] == "turn_has_a_transaction_site" and run.halt["authority_had_begun"] is True
        encounter.wait_until(int(encounter.minute) + 1, step=1)
        assert run.records[-1]["verdict"] == dry.HALTED and run.would_commit == [1, 2]
    # a turn the transaction never saw: the clock moved between two turns it was shown
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter("gi_bleed_57m")
        run = dry.PairDryRun(binding.bind(str(ROOT)), "gi_bleed_57m", encounter.state)
        encounter.wait_until(2, step=1)                                       # not observed: nothing is patched here
        with dry.observing({id(encounter.shadow): run}):
            encounter.wait_until(3, step=1)
    assert run.records[0]["minute"] == 3 and run.records[0]["verdict"] == dry.WOULD_ABORT and "turn_was_observed" in run.records[0]["failed_checks"]
    assert run.records[0]["detail"]["turn_was_observed"] == {"turn_started_at": 2, "last_minute_this_transaction_saw": 0}
    assert rs.ShadowSession.observe_time.__qualname__ == "ShadowSession.observe_time"


def test_review_attack_a_candidate_that_carries_another_field_is_refused_by_the_domain_check_alone(monkeypatch):
    real = authority.shaped_like_legacy
    monkeypatch.setattr(authority, "shaped_like_legacy", lambda candidate, legacy: {**real(candidate, legacy), "hr": 999, "lactate": 99.0})
    result = dry.run("gi_bleed_57m", "probe_short")
    refused = _first_abort(result)
    assert refused["minute"] == 1 and refused["failed_checks"] == ["only_the_pair_would_move"] and refused["would_write"] is None
    assert set(refused["detail"]["only_the_pair_would_move"]["would_write_fields"]) == set(dry.PAIR_DOMAIN) | {"hr", "lactate"}
    assert {"hr", "lactate"} <= set(refused["would_move"]) and result["summary"]["would_commit_minutes"] == 0


def test_review_attack_a_settled_row_without_a_class_and_an_unreadable_ledger_halt_at_settlement():
    for ledger in ([{"order_id": "t9:0", "fate": "EXECUTED"}], [{"class": None, "fate": "EXECUTED"}], "garbage", None, [None],
                   [{"class": " Vascular_Access "}], [{"class": "fluid"}, {"class": "intubation"}]):
        captured = {}
        result = dry.run("gi_bleed_57m", "probe_short", tamper=lambda run, encounter: captured.update(run=run))
        run = captured["run"]
        assert result["halt"] is None and run.would_commit == [1, 2, 3, 4, 5, 6]
        run.settle(ledger)
        assert run.halt is not None and run.halt["stage"] == "settlement" and run.halt["authority_had_begun"] is True, ledger
        assert run.records[-1]["verdict"] == dry.WOULD_COMMIT            # the minute that would already have committed is not rewritten
    captured = {}
    dry.run("gi_bleed_57m", "probe_short", tamper=lambda run, encounter: captured.update(run=run))
    captured["run"].settle([{"class": "fluid"}, {"class": "reassessment"}])
    assert captured["run"].halt is None


def test_review_attack_a_failure_at_an_earlier_minute_of_the_turn_refuses_the_turn():
    """The existing site reads the failures of the turn's last minute. The dry transaction reads every failure since the last turn."""
    def fails_inside_the_infusion(run, encounter):
        advance = run._advance

        def injected(session, minute):
            if minute > 20 and not any(item.where == "injected" for item in session.failures):
                session.failures.append(rs.ShadowFailure(15, "injected", "Injected", "a failure at an intermediate minute of this turn", rs.UNEXPECTED))
            advance(session, minute)
        run._advance = injected
    dry.SCENARIOS["probe_infusion"] = {"at": {2: (dry.SALINE,)}, "horizon": 24}
    result = dry.run("gi_bleed_57m", "probe_infusion", tamper=fails_inside_the_infusion)
    refused = _first_abort(result)
    assert refused["minute"] == 22 and result["summary"]["last_would_commit"] == 2
    assert refused["failed_checks"] == ["pressure_validated"] and "invariants_hold" in refused["detail"]["pressure_validated"]["validation_failures"]


def test_review_attack_the_time_limit_can_be_shortened_and_never_lengthened():
    for asked, held in ((10 ** 9, dry.TIME_LIMIT_MIN), (dry.TIME_LIMIT_MIN + 1, dry.TIME_LIMIT_MIN), (3, 3), (-5, 0)):
        assert dry.PairDryRun(binding.bind(str(ROOT)), "gi_bleed_57m", {"sim_time": 0}, time_limit=asked).time_limit == held
    assert dry.run("gi_bleed_57m", "probe_short", time_limit=10 ** 9)["summary"]["time_limit"] == dry.TIME_LIMIT_MIN == 240


def test_review_attack_a_second_nested_observer_is_refused_and_every_patch_is_restored():
    with dry.observing({}):
        with pytest.raises(RuntimeError, match="already observing"):
            with dry.observing({}):
                pass
        assert getattr(rs.ShadowSession.observe, "_pair_dry_run_patch", False)       # the outer observer is still in place
    for function, name in ((rs.ShadowSession.observe, "ShadowSession.observe"), (rs.ShadowSession.observe_time, "ShadowSession.observe_time"),
                           (acceptance.Encounter.order, "Encounter.order")):
        assert function.__qualname__ == name and not getattr(function, "_pair_dry_run_patch", False)


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
    again = run.minute(copy.deepcopy(encounter.state), encounter.state, encounter.shadow, [{"type": "reassessment"}], "again")
    assert again["verdict"] == dry.WOULD_ABORT and again["failed_checks"] == ["minute_not_already_committed"]
    assert authority.canonical(encounter.state) == before
    later = run.minute(copy.deepcopy(encounter.state), encounter.state, encounter.shadow, [{"type": "reassessment"}], "later")
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
    # The transaction works on a COPY: a write made through what it is handed never reaches the encounter (the review's probe D)
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter("gi_bleed_57m")
        run = dry.PairDryRun(binding.bind(str(ROOT)), "gi_bleed_57m", encounter.state)
        evaluate = run._evaluate

        def writes_into_what_it_was_handed(record, minute, before, after, *rest):
            after["observable"]["sbp"] = 1
            return evaluate(record, minute, before, after, *rest)
        run._evaluate = writes_into_what_it_was_handed
        with dry.observing({id(encounter.shadow): run}):
            encounter.wait_until(1, step=1)
        assert encounter.state["observable"]["sbp"] != 1 and run.violations == []
    # The guard itself: something that holds the ENCOUNTER and writes to it during the dry minute is detected, recorded and refused --
    # without raising into the legacy turn. ``run`` raises afterwards, once the encounter has ended.
    def meddle(run, encounter):
        advance = run._advance

        def meddling(session, minute):
            advance(session, minute)
            encounter.state["observable"]["sbp"] = 1
        run._advance = meddling
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter("gi_bleed_57m")
        run = dry.PairDryRun(binding.bind(str(ROOT)), "gi_bleed_57m", encounter.state)
        meddle(run, encounter)
        with dry.observing({id(encounter.shadow): run}):
            encounter.wait_until(1, step=1)                                  # no exception inside the turn
        assert len(encounter.entries) == 1 and run.violations and run.records[-1]["verdict"] == dry.WOULD_ABORT
        assert "encounter_state_untouched" in run.records[-1]["failed_checks"] and run.would_commit == [] and run.halt["stage"] == "state_guard"
    with pytest.raises(dry.DryRunViolation):
        dry.run("gi_bleed_57m", "probe_short", tamper=meddle)
    assert rs.ShadowSession.observe.__qualname__ == "ShadowSession.observe"


# -- P3-208 and P3-209: the review and the checkpoint -------------------------------------------------------------------------------------------------------

REQUIRED_ATTACKS = ("altered V1 snapshot", "wrong lineage", "consciousness reader causing hidden scoring change", "action unsupported after first commit",
                    "pressure passes / consciousness fails", "consciousness passes / pressure fails", "collapse reached between capture and commit",
                    "replay mismatch", "duplicated commit", "fallback to legacy after first authority commit", "resident-visible output changes",
                    "legacy authority accidentally changed during dry-run")


def test_the_adversarial_review_is_recorded_with_what_was_found_and_what_was_done():
    findings = REVIEW["adversarial_review"]
    assert REVIEW["adversarial_review_status"] == "DONE" and REVIEW["checkpoint"]["provisional"] is False
    assert [item["attack"] for item in findings][:12] == list(REQUIRED_ATTACKS)             # the twelve attacks of the assignment, in its order
    for item in findings:
        assert item["attack"] and item["outcome"] in REVIEW["adversarial_review_scope"]["outcomes"], item
        assert item["evidence"], item
        if item["outcome"] == "FINDING_CORRECTED":
            assert item.get("before") and item.get("after") and item.get("regression_tests"), item
    # every regression test the record cites exists in this module
    cited = {name for item in findings for name in item.get("regression_tests", [])}
    assert cited and cited <= {name for name in globals() if name.startswith("test_")}, sorted(cited - set(globals()))
    outcomes = [item["outcome"] for item in findings]
    assert outcomes.count("FINDING_CORRECTED") >= 5 and "FINDING_ACCEPTED_AND_DECLARED" in outcomes and "NOT_TESTABLE" in outcomes
    scope = REVIEW["adversarial_review_scope"]
    assert "ran no actual authority" in scope["who"] and len(scope["not_tested"]) == 4


def test_the_checkpoint_returns_exactly_one_legal_verdict_names_its_blockers_and_grants_nothing():
    checkpoint = REVIEW["checkpoint"]
    assert checkpoint["verdict"] == rec.CHECKPOINT == "PRESSURE_READY_BUT_CONSCIOUSNESS_NOT_READY" and checkpoint["verdict"] in checkpoint["options"]
    assert len(checkpoint["options"]) == 4 and checkpoint["options"].count(checkpoint["verdict"]) == 1
    assert [item["id"] for item in checkpoint["blockers"]] == [f"C{n}" for n in range(1, 11)]
    assert checkpoint["provisional"] is False and "THROUGH THE SCRIPTED HARNESS" in checkpoint["next_package"]
    assert "None of this is an authority grant" in checkpoint["reading"]
    # the two halves of the verdict are the two measured facts
    assert REVIEW["pressure_recertification"]["comparison"]["verdict"] == "GI_PRESSURE_AUTHORITY_RECERTIFIED_ON_ACTIVE_CORE"
    assert REVIEW["reader_audit"]["verdict"] == "CONSCIOUSNESS_AUTHORITY_HAS_DOWNSTREAM_SIDE_EFFECTS"
    assert set(REVIEW["consciousness_review"]["faculty_table"][0]["faculty_answers"].values()) == {None}
