"""P3-224 to P3-230: the DORMANT GI pair-authority site: its evaluation, its payload, its V1 binding, its interval engine, its artifact and its state machine.

TEST-SIDE. The site is dormant and non-activatable: nothing here arms it, nothing here commits, and every encounter below is the legacy engine's, untouched. The
arming gate and the commit-or-abort interface have their own file (``test_phase3_pair_gate.py``).

* P3-224: the site IS the pair evaluator plus a state machine, an arming gate and an artifact: its records are the evaluator's, byte for byte; the candidate payload is
  the complete pair or it is not a payload; collapse is boundary metadata, never a terminal state; the live word is never written (224A, 224B).
* P3-225: the V1 binding is built inside the layer from the immutable record; a forged or altered binding cannot open a site.
* P3-228: every minute of an interval leaves evidence; the first failed minute aborts the whole interval and no later minute can become authoritative.
* P3-229: the artifact is distinguishable from the pressure artifact, is labelled DORMANT_AUTHORITY_EVALUATION, never claims committed authority, persists, verifies
  and replays from itself alone.
* P3-230: NOT_STARTED, EVALUATING, WOULD_COMMIT, WOULD_ABORT, EXPERIMENT_HALTED, INVALID_FOR_CONTINUATION.
"""
import ast
import dataclasses
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

import observable_view as view
import pilot_acceptance as acceptance
import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_authority_store as store
import runtime_minute_validation as mv
import runtime_pair_site as site_module
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam
import test_phase3_gi_preauthority_review as review
from clinical_core import systemic_consciousness as sc
from family_engine import advance_clinical_time
from test_phase3_clock_routes import CASE, OTHER_GI, _break_minute, _spend, _turn, bound  # noqa: F401 (fixture)

ROOT = Path(__file__).resolve().parent


def _new(bound, arrival, **kw):
    return site_module.DormantPairSite(bound, kw.pop("case", CASE), arrival, experiment_id="test-site", **kw)


def _encounter(case=CASE):
    """A real GI encounter before any turn: ``(encounter, arrival)``."""
    encounter = acceptance.Encounter(case)
    return encounter, deepcopy(encounter.state)


@pytest.fixture
def infusion(bound):
    """ONE turn: a 30-minute infusion from the arrival. The site is fed the way the page's hook feeds it."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter, arrival = _encounter()
        before, entry, ran = _turn(encounter, "Give 500 mL normal saline over 30 minutes.")
    return {"site": _new(bound, arrival), "before": before, "after": deepcopy(encounter.state), "ran": ran, "session": encounter.shadow, "arrival": arrival,
            "encounter": encounter}


def _feed(fixture, submission="inf-1"):
    return fixture["site"].minute(fixture["before"], deepcopy(fixture["after"]), fixture["session"], fixture["ran"], submission, ra.ORDER_TURN)


# -- P3-224: the site is the evaluator, plus the rest -------------------------------------------------------------------------------------------------------------

def test_p1_the_sites_records_are_the_dry_evaluators_records_byte_for_byte(infusion, bound):
    """224. The site adds a state machine, a gate and an artifact; it changes no verdict and no record of the evaluation it wraps."""
    plain = pair.PairDryEvaluator(bound, CASE, infusion["arrival"])
    expected = plain.minute(infusion["before"], deepcopy(infusion["after"]), infusion["session"], infusion["ran"], "inf-1", ra.ORDER_TURN)
    seen = _feed(infusion)
    assert seen == expected and seen["verdict"] == pair.WOULD_COMMIT
    assert issubclass(site_module.DormantPairSite, pair.PairDryEvaluator) and infusion["site"].summary() == plain.summary()


def test_p2_the_candidate_payload_is_the_complete_pair_or_it_is_not_a_payload_and_collapse_is_metadata_not_a_field(infusion):
    """224A."""
    record = _feed(infusion)
    values = record["would_write"]
    assert set(values) == {"minute"} | set(pair.PAIR_FIELDS) and values["minute"] == 30
    payload = pair.PairPayload(**values)
    assert pair.payload_problems(payload) == [] and payload.map == ra.derived_map(payload.sbp, payload.dbp)
    for name in ("sbp", "dbp", "map", "consciousness_category", "pulse_present"):
        broken = dict(values)
        broken[name] = None
        assert pair.payload_problems(pair.PairPayload(**broken)), name                       # one missing half: not a payload
    # collapse is the experiment's validity boundary: it is in the turn's checks, never a payload field, and nothing in the record says "terminal"
    assert not [name for name in values if "collapse" in name or "terminal" in name or "dead" in name]
    assert "collapse_boundary_not_reached" not in record["failed_checks"] and record["common"]["collapse_state"] == 0


def test_p3_the_site_writes_nothing_into_the_encounter_and_never_the_live_word(infusion):
    """224B. The state is hashed before and after; the only things a would-be commit would move are the three pressures and the overlay."""
    before = ra.digest_of(infusion["after"])
    record = _feed(infusion)
    assert ra.digest_of(infusion["after"]) == before and infusion["site"].violations == []
    moved = set(record["would_move"])
    assert moved <= {"sbp", "dbp", "map", view.OVERLAY_KEY}, moved
    # the module names no field of the live word: reader-audit rule for new layer modules
    for module in ("runtime_pair_site.py", "runtime_minute_validation.py"):
        tree = ast.parse((ROOT / module).read_text(encoding="utf-8"))
        literals = {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        assert not [text for text in literals if "mental_status" in text and len(text) < 40], (module, [text for text in literals if "mental_status" in text])


# -- P3-225: the V1 binding inside the layer ------------------------------------------------------------------------------------------------------------------------

def test_b1_the_site_binds_the_pinned_version_1_and_the_artifact_names_every_digest(infusion):
    summary = _feed(infusion) and infusion["site"].artifact()["snapshot"]
    assert (summary["snapshot_id"], summary["version"]) == (pair.V1_ID, 1)
    assert summary["record_digest"] == pair.V1_RECORD_DIGEST and summary["identity_digest"] == pair.V1_IDENTITY_DIGEST and summary["file_sha256"] == pair.V1_FILE_SHA256
    assert summary["profile_digest"] == pair.V1_PROFILE_DIGEST and (summary["core_version"], summary["core_digest"]) == (pair.V1_CORE_VERSION, pair.V1_CORE_DIGEST)
    artifact = infusion["site"].artifact()
    assert artifact["snapshot_status"] == pair.RATIFIED == "RATIFIED_FOR_DEVELOPMENT_EXPERIMENTS" and artifact["snapshot_is_authority_approved"] is False
    assert artifact["lineage"]["digest"] == pair.V1_CORE_DIGEST and artifact["lineage"]["certified"] is True
    # the profile of the bound run is the one built from the record, not one a caller supplied
    assert pair.runner_is_bound(infusion["site"].runner, infusion["site"].bound)


def _forged(bound):
    low = sc.WITNESSES["LOW"].to_dict()
    profile = pair.build_profile(low)
    return {
        "LOW values under the V1 identity": pair.BoundSnapshot(pair.V1_ID, 1, tuple((name, float(low[name])) for name in sc.FIELDS), pair.V1_IDENTITY_DIGEST,
                                                               pair.V1_RECORD_DIGEST, pair.V1_FILE_SHA256, pair.V1_CORE_VERSION, pair.V1_CORE_DIGEST, pair.PRESSURE_POINT,
                                                               profile, pair.profile_digest(profile)),
        "a caller-altered profile": dataclasses.replace(bound, profile=dataclasses.replace(bound.profile, amendment_2=dataclasses.replace(
            bound.profile.amendment_2, delivery_severe=float(bound.profile.amendment_2.delivery_severe) + 1e-9))),
        "a wrong record digest": dataclasses.replace(bound, record_digest="0" * 64),
        "another snapshot id": dataclasses.replace(bound, snapshot_id="GI_DEVELOPMENT_SNAPSHOT_V2"),
        "another version": dataclasses.replace(bound, version=2),
        "values mutated by 1e-9": dataclasses.replace(bound, values=tuple((name, value + (1e-9 if name == "delivery_severe" else 0.0)) for name, value in bound.values)),
        "a wrong core digest": dataclasses.replace(bound, core_digest="22b90a6f" + "0" * 56),
        "a wrong profile digest": dataclasses.replace(bound, profile_digest="0" * 64),
    }


FORGED = ("LOW values under the V1 identity", "a caller-altered profile", "a wrong record digest", "another snapshot id", "another version", "values mutated by 1e-9",
          "a wrong core digest", "a wrong profile digest")


@pytest.mark.parametrize("label", FORGED)
def test_b2_a_forged_or_altered_binding_cannot_open_a_site(bound, label):
    """225 negative controls: the site REFUSES a binding that is not the pinned, rebuilt version 1."""
    forged = _forged(bound)[label]
    assert not pair.bound_is_v1(forged), label
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        _, arrival = _encounter()
    with pytest.raises(pair.SnapshotBindingError):
        _new(forged, arrival)


@pytest.mark.parametrize("label", sorted(review.TAMPERS))
def test_b3_a_tampered_record_never_yields_a_binding_so_no_site_can_exist_on_it(label):
    change, code = review.TAMPERS[label]
    with pytest.raises(pair.SnapshotBindingError) as caught:
        pair.bind(str(ROOT), record=review._tampered(change))
    assert code in caught.value.args[0] or code in str(caught.value)


def test_b4_the_three_witnesses_are_not_the_snapshot_and_a_wrong_live_lineage_stops_the_minute(infusion, monkeypatch):
    """LOW, HIGH and CENTER_REFERENCE are sensitivity witnesses: they bind nothing. And a lineage that is not the certified member aborts the interval."""
    for name in ("LOW", "HIGH", "CENTER_REFERENCE"):
        with pytest.raises(pair.SnapshotBindingError):
            pair.bind(str(ROOT), record=review._tampered(lambda r, n=name: r.update(values=sc.WITNESSES[n].to_dict())))
    monkeypatch.setattr(ev, "core_lineage_ok", lambda: False)
    record = _feed(infusion)
    assert record["verdict"] == pair.WOULD_ABORT and "lineage_certified" in record["failed_checks"] and infusion["site"].state == site_module.EXPERIMENT_HALTED


# -- P3-228: the interval engine ---------------------------------------------------------------------------------------------------------------------------------

def test_i1_every_minute_of_the_interval_leaves_its_evidence_and_one_commit_of_the_end_state_is_what_would_happen(infusion):
    record = _feed(infusion)
    assert [row["minute"] for row in record["interval"]] == list(range(1, 31)) and all(row["ok"] and row["failed"] == [] for row in record["interval"])
    assert infusion["site"].would_commit == [30] and infusion["site"].artifact()["turns"][-1]["interval"] == record["interval"]
    assert site_module.GRANULARITY == pair.VALIDATED_ATOMIC_INTERVAL


@pytest.mark.parametrize("how", ("no_candidate", "failure_at_minute", "not_one_course"))
@pytest.mark.parametrize("k", (1, 15, 29))
def test_i2_the_first_failed_minute_aborts_the_whole_interval_and_a_clean_end_state_cannot_override_it(infusion, k, how):
    """228B. The END minute is intact in every case; the interval is refused at minute k, every later minute is ineligible, nothing would commit."""
    _break_minute(infusion, k, how)
    record = _feed(infusion)
    detail = record["detail"]["interval_minutes_validated"]
    assert record["verdict"] == pair.WOULD_ABORT and detail["first_failed_minute"] == k and "ineligible_after" not in detail, "the pair's record is what the P3-218 record pins"
    assert infusion["site"].artifact()["turns"][-1]["ineligible_after"] == list(range(k + 1, 31)), "228B: the artifact says which minutes the failed one made ineligible"
    assert record["would_write"] is None and infusion["site"].would_commit == [] and infusion["site"].state == site_module.EXPERIMENT_HALTED
    follow = infusion["site"].minute(deepcopy(infusion["after"]), deepcopy(infusion["after"]), infusion["session"], None, "next", ra.CLINICAL_TIME)
    assert follow["verdict"] == pair.HALTED and infusion["site"].would_commit == []          # no later minute can become authoritative


@pytest.mark.parametrize("k", (3, 12, 28))
def test_i3_collapse_established_at_an_internal_minute_aborts_at_that_minute_before_any_commit_and_is_not_a_terminal_state(infusion, monkeypatch, k):
    """228C / FD-AUTH-17. The boundary is the experiment's validity boundary: established at ANY internal minute, the transaction aborts before commit. It is not death,
    not a terminal state and not resident text."""
    real = fam.run_channels

    def collapsing(runner):
        rows = real(runner)
        for row in rows:
            if row["minute"] == k and "channels_unavailable" not in row:
                row["channels"] = {**row["channels"], "collapse_state_index": pair.ESTABLISHED}
        return rows
    monkeypatch.setattr(fam, "run_channels", collapsing)
    record = _feed(infusion)
    boundary = record["detail"]["collapse_boundary_not_reached"]
    assert record["verdict"] == pair.WOULD_ABORT and boundary["first_established_minute"] == k and boundary["clear"] is False
    assert record["would_write"] is None and infusion["site"].would_commit == []
    artifact = infusion["site"].artifact()
    # what the experiment SAYS about the boundary (not the snapshot's physiology parameters, one of which is named for the core's own terminal rhythm)
    text = repr({key: artifact[key] for key in ("halt", "continuation", "transitions", "state")} | {"reasons": [turn["reason"] for turn in artifact["turns"]]}).lower()
    assert "terminal" not in text and "dead" not in text and "death" not in text
    assert infusion["site"].continuation()["state"] == site_module.EXPERIMENT_HALTED


@pytest.mark.parametrize("how,expected", (("off_the_ladder", "consciousness_candidate_present"), ("pulse_lost", "pulse_present")))
@pytest.mark.parametrize("k", (1, 15, 29))
def test_i4_a_failure_of_the_consciousness_half_alone_aborts_the_pair_with_the_pressure_half_clean(infusion, monkeypatch, k, how, expected):
    """Attack 'consciousness fails, pressure is fine': the pair is all or nothing. The pressure half of the failing minute is valid; the pair still does not commit."""
    real = fam.run_channels

    def tampered(runner):
        rows = real(runner)
        for row in rows:
            if row["minute"] == k and "channels_unavailable" not in row:
                row["channels"] = {**row["channels"], **({"category_index": 9} if how == "off_the_ladder" else {"pulse_present": False})}
        return rows
    monkeypatch.setattr(fam, "run_channels", tampered)
    record = _feed(infusion)
    detail = record["detail"]["interval_minutes_validated"]
    failed_row = next(row for row in record["interval"] if row["minute"] == k)
    assert record["verdict"] == pair.WOULD_ABORT and detail["first_failed_minute"] == k and failed_row["failed"] == [expected] and "pressure_validated" not in record["failed_checks"]
    assert record["would_write"] is None and infusion["site"].would_commit == [] and infusion["site"].state == site_module.EXPERIMENT_HALTED


# -- P3-229: the artifact ------------------------------------------------------------------------------------------------------------------------------------------

@pytest.fixture
def stored_dir(monkeypatch):
    directory = tempfile.mkdtemp(prefix="phase3-pair-site-")
    monkeypatch.setenv(store.STORE_FLAG, directory)
    return Path(directory)


def test_a1_the_artifact_is_not_the_pressure_artifact_says_dormant_and_never_claims_committed_authority(infusion, stored_dir):
    _feed(infusion)
    artifact = infusion["site"].artifact()
    assert artifact["artifact"] == site_module.ARTIFACT_TYPE != "phase3_authority_experiment"
    assert artifact["label"] == "DORMANT_AUTHORITY_EVALUATION" and artifact["authority_mode"] == "DORMANT_NOT_ARMED" and artifact["committed_authority"] is False
    assert artifact["common_core_runtime_authority"] is False and artifact["arming"]["armed"] is False
    assert "COMMITTED_AUTHORITY" not in repr(artifact) and artifact["granularity"] == "VALIDATED_ATOMIC_INTERVAL"
    assert store.persist(artifact)["why"] == store.NOT_AN_ARTIFACT                    # the pressure store refuses it: it cannot be mistaken for one
    required = {"case_id", "snapshot", "lineage", "turns", "transitions", "halt", "replay_inputs", "arming", "state"}
    assert required <= set(artifact) and artifact["turns"][0]["legacy"] and artifact["turns"][0]["common"] and artifact["turns"][0]["interval"]
    assert {"action_kinds", "no_common_physiology", "verdict", "failed_checks"} <= set(artifact["turns"][0])


def test_a2_the_artifact_verifies_replays_and_a_tampered_one_does_neither(infusion):
    _feed(infusion)
    artifact = infusion["site"].artifact()
    assert site_module.verify_artifact(artifact)["verified"] is True
    replay = site_module.replay_artifact(artifact)
    assert replay["reproduces"] and replay["candidate_matches"] and replay["decisions_match"] and replay["compared"] == 1 and replay["mismatches"] == []
    for label, change in (("candidate", lambda a: a["turns"][0]["common"].update(category=2)),
                          ("pressure", lambda a: a["turns"][0]["common"].update(sbp=a["turns"][0]["common"]["sbp"] + 1.0)),
                          ("collapse", lambda a: a["turns"][0]["common"].update(collapse_state=2))):
        bad = deepcopy(artifact)
        change(bad)
        assert site_module.verify_artifact(bad)["digest_matches"] is False, label
        assert site_module.replay_artifact(bad)["candidate_matches"] is False, label
    claimed = deepcopy(artifact)
    claimed["committed_authority"] = True
    assert site_module.verify_artifact(claimed)["verified"] is False and site_module.persist_artifact(claimed)["why"] == store.NOT_AN_ARTIFACT
    empty = deepcopy(artifact)
    empty["replay_inputs"] = {}
    assert site_module.replay_artifact(empty)["reproduces"] is False


def test_a3_a_recorded_decision_the_replay_does_not_support_is_a_mismatch(infusion):
    """229B. The replay re-derives the consciousness half of every interval minute and the collapse boundary: a WOULD_COMMIT the run does not support is found."""
    _feed(infusion)
    artifact = infusion["site"].artifact()
    forged = deepcopy(artifact)
    forged["turns"][0]["interval"][4]["ok"] = False
    assert site_module.replay_artifact(forged)["decisions_match"] is False
    rows = {row["minute"]: row["channels"] for row in fam.artifact_rows(artifact["replay_inputs"]["bound"]["scenario"])}
    assert all(rows[minute]["category_index"] in mv.LADDER and rows[minute]["collapse_state_index"] < pair.ESTABLISHED for minute in range(1, 31))


def test_a4_persistence_is_create_only_idempotent_off_by_default_and_outside_the_repository(infusion, stored_dir, monkeypatch):
    _feed(infusion)
    first = infusion["site"].persist()
    assert first["stored"] is True and first["idempotent"] is False and (stored_dir / site_module.SUBDIRECTORY).is_dir()
    assert infusion["site"].persist()["idempotent"] is True
    assert len(site_module.stored_artifacts()) == 1 and store.paths() == [], "the pressure store's own listing does not see it"
    # a record with the same name and other content is a collision, never an overwrite
    path = Path(first["path"])
    path.write_text("changed", encoding="utf-8")
    assert infusion["site"].persist()["why"] == store.COLLISION
    monkeypatch.delenv(store.STORE_FLAG)
    assert infusion["site"].persist()["why"] == store.NOT_CONFIGURED
    monkeypatch.setenv(store.STORE_FLAG, "relative/dir")
    assert infusion["site"].persist()["stored"] is False


# -- P3-230: the state machine -----------------------------------------------------------------------------------------------------------------------------------------

def test_x1_the_machine_has_six_states_a_closed_transition_table_and_two_terminal_halts():
    assert site_module.STATES == ("NOT_STARTED", "EVALUATING", "WOULD_COMMIT", "WOULD_ABORT", "EXPERIMENT_HALTED", "INVALID_FOR_CONTINUATION")
    assert set(site_module.TRANSITIONS) == set(site_module.STATES) and site_module.TERMINAL_STATES == ("EXPERIMENT_HALTED", "INVALID_FOR_CONTINUATION")
    assert all(site_module.TRANSITIONS[state] == () for state in site_module.TERMINAL_STATES)
    assert all(target in site_module.STATES for moves in site_module.TRANSITIONS.values() for target in moves)


def test_x2_an_illegal_move_is_refused_loudly_and_a_halt_cannot_be_left(infusion):
    site = infusion["site"]
    assert site.state == site_module.NOT_STARTED and site.transitions[0]["to"] == "NOT_STARTED"
    with pytest.raises(site_module.StateMachineError):
        site._move(site_module.WOULD_COMMIT)                                          # a commit cannot be reached without evaluating
    _break_minute(infusion, 5, "no_candidate")
    _feed(infusion)
    assert site.state == site_module.EXPERIMENT_HALTED
    for target in site_module.STATES:
        if target != site_module.EXPERIMENT_HALTED:
            with pytest.raises(site_module.StateMachineError):
                site._move(target)


def test_x3_a_failure_before_authority_began_halts_the_experiment_and_leaves_the_legacy_encounter_exactly_as_it_was(infusion):
    """230A / FD-AUTH-20."""
    before = ra.digest_of({"state": infusion["after"], "shadow_minutes": len(infusion["session"].minutes)})
    _break_minute(infusion, 9, "no_candidate")
    record = _feed(infusion)
    site = infusion["site"]
    assert record["verdict"] == pair.WOULD_ABORT and site.state == site_module.EXPERIMENT_HALTED and not site.authority_began()
    assert [item["to"] for item in site.transitions] == ["NOT_STARTED", "EVALUATING", "WOULD_ABORT", "EXPERIMENT_HALTED"]
    assert ra.digest_of({"state": infusion["after"], "shadow_minutes": len(infusion["session"].minutes)}) == before
    verdict = site.continuation()
    assert verdict["legacy_may_continue_silently"] is True and verdict["encounter_valid_for_continuation"] is True
    assert site.request_legacy_fallback()["granted"] is True and "never began" in site.halt["consequence"]


def test_x4_a_failure_after_authority_began_is_invalid_for_continuation_and_the_legacy_engine_does_not_quietly_take_over(bound):
    """230B: a REAL earlier would-commit minute, then a failure. No commit is made at any point."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter, arrival = _encounter()
        before, entry, ran = _turn(encounter, "Give 250 mL normal saline over 5 minutes.")
    site = _new(bound, arrival)
    assert site.minute(before, deepcopy(encounter.state), encounter.shadow, ran, "t1", ra.ORDER_TURN)["verdict"] == pair.WOULD_COMMIT
    assert site.state == site_module.WOULD_COMMIT and site.authority_began() and site.would_commit == [5]
    before2 = encounter.shadow.capture(encounter.state)
    advance = advance_clinical_time(encounter.state, 10, label="examination")
    encounter.shadow.observe_time(before2, encounter.state, advance)
    _break_minute({"session": encounter.shadow}, 9, "no_candidate")
    second = site.minute(before2, deepcopy(encounter.state), encounter.shadow, None, "t2", ra.CLINICAL_TIME)
    assert second["verdict"] == pair.WOULD_ABORT and site.state == site_module.INVALID_FOR_CONTINUATION
    assert [item["to"] for item in site.transitions][-3:] == ["EVALUATING", "WOULD_ABORT", "INVALID_FOR_CONTINUATION"]
    verdict = site.continuation()
    assert verdict == {"state": "INVALID_FOR_CONTINUATION", "legacy_may_continue_silently": False, "encounter_valid_for_continuation": False,
                       "why": site_module.NO_SILENT_FALLBACK}
    assert site.request_legacy_fallback()["granted"] is False and site.would_commit == [5] and site.commit_requests == []
    assert site.summary()["authority_had_begun_at_abort"] is True and "INVALID_FOR_CONTINUATION" in site.halt["consequence"]


def test_x5_a_simulated_prior_authority_exercises_the_post_authority_path_with_no_real_write(bound, infusion):
    """230B, TEST-ONLY: the simulation changes a label and writes nothing."""
    site = _new(bound, infusion["arrival"], simulate_prior_authority=True)
    state_before = ra.digest_of(infusion["after"])
    _break_minute(infusion, 4, "no_candidate")
    record = site.minute(infusion["before"], deepcopy(infusion["after"]), infusion["session"], infusion["ran"], "inf-1", ra.ORDER_TURN)
    assert record["verdict"] == pair.WOULD_ABORT and site.state == site_module.INVALID_FOR_CONTINUATION and site.would_commit == []
    assert site.halt["simulated_prior_authority"] is True and "SIMULATED" in site.halt["consequence"]
    assert ra.digest_of(infusion["after"]) == state_before and site.artifact()["simulated_prior_authority"] is True
    assert site.request_legacy_fallback()["granted"] is False


def test_x6_a_halt_is_not_the_patients_death_and_names_no_clinical_outcome(infusion):
    """230C."""
    _break_minute(infusion, 2, "no_candidate")
    _feed(infusion)
    artifact = infusion["site"].artifact()
    text = repr({key: artifact[key] for key in ("halt", "continuation", "transitions", "state")}).lower()
    for word in ("death", "died", "dead", "terminal", "discharge", "outcome", "arrest"):
        assert word not in text.replace("terminal_states", ""), word
    assert artifact["state"] == "EXPERIMENT_HALTED" and "legacy" in artifact["continuation"]["why"].lower()


def test_x7_a_turn_that_did_not_move_the_clock_leaves_the_state_where_it_was(bound):
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter, arrival = _encounter()
        before, entry, ran = _turn(encounter, "Place an IV line.")
    site = _new(bound, arrival)
    record = site.minute(before, deepcopy(encounter.state), encounter.shadow, ran, "iv", ra.ORDER_TURN)
    assert record["verdict"] == pair.NO_ADVANCE and site.state == site_module.NOT_STARTED
    assert [item["to"] for item in site.transitions] == ["NOT_STARTED", "EVALUATING", "NOT_STARTED"]
    assert record["no_common_physiology"][0]["disposition"] == ra.EXECUTED_NO_COMMON_PHYSIOLOGY


def test_x8_an_unsupported_executed_action_stops_the_experiment_and_is_never_silently_continued(bound):
    """FD-AUTH-19."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter, arrival = _encounter()
        before = encounter.shadow.capture(encounter.state)
    site = _new(bound, arrival)
    record = site.minute(before, deepcopy(encounter.state), encounter.shadow, [{"order_id": "t0:0", "type": "intubation", "fate": "EXECUTED"}], "bad", ra.ORDER_TURN)
    assert record["verdict"] == pair.WOULD_ABORT and "supported_management" in record["failed_checks"] and site.state == site_module.EXPERIMENT_HALTED
    assert site.minute(before, deepcopy(encounter.state), encounter.shadow, [], "again", ra.ORDER_TURN)["verdict"] == pair.HALTED


def test_x9_the_abort_half_of_the_interface_halts_visibly_with_nothing_committed(infusion):
    site = infusion["site"]
    result = site.request_abort("operator requested")
    assert result["aborted"] is True and site.state == site_module.EXPERIMENT_HALTED and site.would_commit == []
    assert [item["to"] for item in site.transitions] == ["NOT_STARTED", "EVALUATING", "WOULD_ABORT", "EXPERIMENT_HALTED"]
    assert site.request_abort("again")["aborted"] is False
    assert _feed(infusion)["verdict"] == pair.HALTED
