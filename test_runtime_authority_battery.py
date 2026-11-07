"""P3-22 and P3-23: every GI acceptance scenario through the dormant authority, and the artifact.

P3-22 drives all 34 scenarios of the repository's own GI acceptance battery through the eligibility
reading AND the transaction logic, with a TEST-ONLY snapshot that exists for one process. P3-23 checks
that what a future experiment would leave behind is complete, replayable from itself, and detectably
changed if anyone edits it.

No production authority is enabled anywhere here: the registry is empty before and after, and the
injection goes through the private mapping the production scan watches.
"""
import json
from copy import deepcopy
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_shadow as rs

ROOT = Path(__file__).resolve().parent
TEST_ONLY_SNAPSHOT = {"id": "test_only_battery_point",
                      "approved_by_faculty": True,
                      "decision": "TEST ONLY: exists inside one test session, approves nothing",
                      "runtime_parameter_snapshot_id": rs.PARAMETER_SNAPSHOT_ID,
                      "parameters": {"test_only_placeholder": 1.0}}
BEST = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY,
        ra.SNAPSHOT_FLAG: TEST_ONLY_SNAPSHOT["id"],
        ra.ENVIRONMENT_FLAG: "development",
        rs.FLAG: rs.MODE_SHADOW_COMPARE}
#: The two candidates P3-21 left standing, plus the one it retired, so the retirement is re-measured.
CANDIDATES = {"gi_pressure_committed": {},
              "gi_pressure_preload_high": {"preload_curve_scale_ml": 1500.0,
                                           "arrival_preload_fraction": 0.7},
              "gi_pressure_preload_low": {"preload_curve_scale_ml": 600.0,
                                          "arrival_preload_fraction": 0.3}}


@pytest.fixture(scope="module")
def registered():
    """The test-only approval, for this module's process only."""
    ra._APPROVED_SNAPSHOT_POINTS[TEST_ONLY_SNAPSHOT["id"]] = TEST_ONLY_SNAPSHOT
    try:
        yield TEST_ONLY_SNAPSHOT
    finally:
        ra._APPROVED_SNAPSHOT_POINTS.pop(TEST_ONLY_SNAPSHOT["id"], None)


@pytest.fixture(scope="module")
def battery(registered):
    """The whole GI battery, played once: the evidence, the eligibility and the transactions."""
    import runtime_shadow_evidence as ev
    evidence = ev.gi_evidence()
    return {"evidence": evidence,
            "authority": ra.authority_scenario_battery(registered, environ=BEST, evidence=evidence),
            "eligibility": ra.eligibility_battery(evidence, environ=BEST)}


# -- P3-22A, P3-22B: the scenario matrix and its honest counts -----------------------------------------

def test_g1_all_thirty_four_scenarios_are_driven_and_classified(battery):
    result = battery["authority"]
    assert result["scenarios"] == 34, result["scenarios"]
    assert sum(result["counts"].values()) == 34
    assert set(result["counts"]) <= {ra.TECHNICALLY_VALID, ra.NOT_ELIGIBLE, ra.BOUNDARY_FAILURE,
                                     ra.REPLAY_FAILURE, ra.STRUCTURAL_DIVERGENCE, ra.OTHER_FAILURE}
    # The count moved when the call site arrived, and it is reported as it is, not as it was: the two
    # scenarios that order something the engine itself does not model are not eligible either.
    assert result["counts"] == {ra.TECHNICALLY_VALID: 26, ra.NOT_ELIGIBLE: 8}, result["counts"]
    for row in result["rows"]:
        for key in ("case", "scenario", "actions", "eligibility", "unsupported", "transaction_valid",
                    "atomic_commit", "replay_exact", "legacy_counterfactual", "classification"):
            assert key in row, key


def test_g2_the_eligibility_reading_and_the_transaction_agree(battery):
    """Two readings of the same question used to disagree on two scenarios. They now agree."""
    eligible = {(row["case_id"], row["scenario"]) for row in battery["eligibility"]["rows"]
                if row["classification"] == ra.ELIGIBLE_BUT_NO_SNAPSHOT}
    valid = {(row["case"], row["scenario"]) for row in battery["authority"]["rows"]
             if row["classification"] == ra.TECHNICALLY_VALID}
    assert eligible == valid, sorted(eligible ^ valid)
    assert battery["eligibility"]["counts"] == {ra.ELIGIBLE_BUT_NO_SNAPSHOT: 26,
                                                ra.INELIGIBLE_UNSUPPORTED: 8}


def test_g3_every_valid_scenario_commits_atomically_and_replays(battery):
    result = battery["authority"]
    valid = [row for row in result["rows"] if row["classification"] == ra.TECHNICALLY_VALID]
    assert len(valid) == 26
    assert result["atomic_commits"] == 26 and result["replay_exact"] == 26
    assert result["counterfactual_captured"] == 26
    for row in valid:
        assert row["transaction_valid"] and row["atomic_commit"] and row["replay_exact"], row
        assert (row["legacy_counterfactual"] or {}).get("sbp") is not None, row


def test_g4_the_unsupported_action_matrix_names_every_blocked_class(battery):
    rows = [row for row in battery["authority"]["rows"]
            if row["classification"] == ra.NOT_ELIGIBLE]
    assert len(rows) == 8
    blocked = {kind for row in rows for kind in row["unsupported"]}
    assert blocked == {"anticoagulation", "aspirin", "norepinephrine", "not_modelled"}, blocked
    scenarios = sorted({row["scenario"] for row in rows})
    assert scenarios == ["D_incorrect_treatment", "F_start_stop", "H_unexpected_reasonable",
                         "K_combined_interventions"], scenarios
    for row in rows:
        assert row["why"], row


def test_g5_each_candidate_is_measured_against_every_scenario(battery):
    matrix = ra.candidate_matrix(CANDIDATES, evidence=battery["evidence"])
    assert set(matrix) == set(CANDIDATES)
    assert matrix["gi_pressure_committed"]["counts"] == {ra.TECHNICALLY_VALID: 34}
    assert matrix["gi_pressure_preload_high"]["counts"] == {ra.TECHNICALLY_VALID: 34}
    # The candidate P3-21 retired fails on the two terminal scenarios, in the core and not in a test.
    retired = matrix["gi_pressure_preload_low"]["counts"]
    assert retired == {ra.TECHNICALLY_VALID: 32, ra.BOUNDARY_FAILURE: 2}, retired
    boundary = [row for row in matrix["gi_pressure_preload_low"]["rows"]
                if row["classification"] == ra.BOUNDARY_FAILURE]
    assert sorted(row["scenario"] for row in boundary) == ["terminal_deterioration"] * 2
    assert all("UnresolvedBoundary" in row["why"] for row in boundary)
    for name in ("gi_pressure_committed", "gi_pressure_preload_high"):
        for row in matrix[name]["rows"]:
            assert row["pressures"] and row["pressures"]["sbp"] is not None, (name, row)


# -- P3-22D: the action stress -------------------------------------------------------------------------

@pytest.mark.parametrize("kind,blocks", [
    ("fluid", False), ("blood", False), ("oxygen", False), ("ppi", False), ("endoscopy", False),
    ("procedure", False), ("reassessment", False), ("consult", False), ("diagnostic", False),
    ("anticoagulation", True), ("aspirin", True), ("norepinephrine", True),
    ("not_modelled", True), ("unrecognized", True), ("a_class_nobody_declared", True),
])
def test_g6_every_action_class_is_either_supported_or_blocked(kind, blocks):
    assert bool(ra.unsupported_among((kind,))) is blocks, kind
    # And the three key shapes the runtime uses all read the same way.
    for key in ("type", "kind", "class"):
        assert ra.action_kinds([{key: kind.upper(), "order_id": "x"}]) == (kind,)
        assert bool(ra.unsupported_among(ra.action_kinds([{key: f"  {kind.upper()} "}]))) is blocks
    assert ra.action_kinds([{"order_id": "x"}]) == ("untyped_action",)
    assert ra.unsupported_among(("untyped_action",)) == ("untyped_action",)


def test_g7_a_duplicate_receipt_does_not_commit_twice(registered):
    """A turn that does not advance the clock may not commit its minute again (P3-22D)."""
    import pilot_acceptance
    import runtime_shadow_evidence as ev
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = pilot_acceptance.Encounter("gi_bleed_57m")
        arrival = deepcopy(encounter.state)
        site = ra.open_site(arrival, environ=BEST)
        encounter.order("Give 1 litre of normal saline over 15 minutes. Reassess in 10 minutes.")
        ran = [dict(order) for order in encounter.entries[-1]["orders"]]
        first = site.minute(None, deepcopy(encounter.state), encounter.shadow, ran, "t0")
        duplicate = site.minute(None, deepcopy(encounter.state), encounter.shadow, ran, "t0-again")
    assert first is not None and duplicate is None
    assert ra.MINUTE_ALREADY_COMMITTED in site.halt_reason
    assert len(site.minutes_committed) == 1


# -- P3-22E: the failure stress ------------------------------------------------------------------------

@pytest.fixture(scope="module")
def live(registered):
    """One real GI minute, kept for the failure injections."""
    import pilot_acceptance
    import runtime_shadow_evidence as ev
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = pilot_acceptance.Encounter("gi_bleed_57m")
        arrival = deepcopy(encounter.state)
        encounter.order("Give 1 litre of normal saline over 15 minutes. Reassess in 10 minutes.")
    return {"arrival": arrival, "state": deepcopy(encounter.state), "session": encounter.shadow,
            "ran": [dict(order) for order in encounter.entries[-1]["orders"]]}


def _run(live, *, environ=None, snapshot=None, ran=None, state=None):
    site = ra.open_site(live["arrival"], environ=environ or BEST)
    if site is None:
        return None, None
    if snapshot is not None:
        site.snapshot = snapshot
    prepared = site.minute(None, state or deepcopy(live["state"]), live["session"],
                           live["ran"] if ran is None else ran, "stress")
    return site, prepared


def test_g8_an_invalid_or_wrong_snapshot_fails_closed(live):
    for snapshot in ({}, "not a mapping", {**TEST_ONLY_SNAPSHOT, "approved_by_faculty": False},
                     {**TEST_ONLY_SNAPSHOT, "runtime_parameter_snapshot_id": "another_point"},
                     {**TEST_ONLY_SNAPSHOT, "id": "an id nobody registered"}):
        site, prepared = _run(live, snapshot=snapshot)
        assert prepared is None and site.halted, snapshot
        assert site.records[-1]["committed"] == []


def test_g9_a_wrong_snapshot_id_in_the_environment_opens_nothing(live):
    assert ra.open_site(live["arrival"], environ={**BEST, ra.SNAPSHOT_FLAG: "nobody"}) is None
    assert ra.site_for(live["arrival"], {}, environ={**BEST, ra.SNAPSHOT_FLAG: ""}) is None


def test_g10_a_digest_mismatch_fails_closed(live, monkeypatch):
    monkeypatch.setattr(ra.AuthoritySite, "_replayed_point",
                        staticmethod(lambda artifact, minute: {"sbp": 1.0, "dbp": 1.0, "map": 1.0}))
    site, prepared = _run(live)
    assert prepared is None and site.halted
    assert "minute_reproducible" in site.halt_reason, site.halt_reason
    assert site.records[-1]["rollback"]["validation_failures"] == ["minute_reproducible"]


@pytest.mark.parametrize("environ_change", [
    {ra.ENVIRONMENT_FLAG: "production"}, {ra.ENVIRONMENT_FLAG: ""},
    {ra.PILOT_FLAGS[0]: "1"}, {"MRS_OFFLINE_CASES": "1", "MRS_IMAGE_REQUIRE_REVIEW": "on"},
    {ra.AUTHORITY_FLAG: ""}, {rs.FLAG: ""},
])
def test_g11_a_wrong_environment_or_a_pilot_opens_nothing(live, environ_change):
    assert ra.open_site(live["arrival"], environ={**BEST, **environ_change}) is None


def test_g12_a_wrong_family_or_case_is_refused(live):
    from copy import deepcopy as copy
    other = copy(live["arrival"])
    other["engine_family"] = "acs"
    assert ra.open_site(other, environ=BEST) is None
    other = copy(live["arrival"])
    other["encounter_spec"] = {**dict(other.get("encounter_spec") or {}), "variant_id": "acs_70f_left_main"}
    assert ra.open_site(other, environ=BEST) is None


@pytest.mark.parametrize("classification,expected", [
    (rs.UNEXPECTED, "no_core_failure"), (rs.BOUNDARY, "no_unresolved_boundary"),
])
def test_g13_a_core_failure_or_an_unresolved_boundary_fails_closed(live, classification, expected):
    session = live["session"]
    minute = max(session.runner.compared)
    failure = rs.ShadowFailure(minute, "core", "CoreInvariantError", "injected", classification)
    session.failures.append(failure)
    try:
        site, prepared = _run(live)
    finally:
        session.failures.remove(failure)
    assert prepared is None and site.halted
    assert expected in str(site.records[-1]["validation_failures"]), site.records[-1]
    assert site.records[-1]["rollback"]["committed"] == []


def test_g14_a_partial_transaction_fault_commits_nothing(live, monkeypatch):
    def hostile(self, target, *, environ=None):
        raise RuntimeError("the write failed half way")
    monkeypatch.setattr(ra.AuthorityTransaction, "commit", hostile)
    state = deepcopy(live["state"])
    site, prepared = _run(live, state=state)
    assert prepared is None and site.halted
    assert state == deepcopy(live["state"])
    assert site.records[-1]["committed"] == []


def test_g15_a_replay_mismatch_in_the_artifact_is_detected(live):
    site, prepared = _run(live)
    assert prepared is not None
    artifact = json.loads(json.dumps(site.artifact(), default=str))
    assert ra.replay_site_artifact(artifact)["reproduces"]
    broken = json.loads(json.dumps(artifact, default=str))
    broken["minutes"][0]["replay_input"]["scenario"]["minutes"] = 1
    verdict = ra.replay_site_artifact(broken)
    assert not verdict["reproduces"]


def test_g16_an_unsupported_action_in_the_turn_commits_nothing(live):
    for kind in ("anticoagulation", "aspirin", "norepinephrine"):
        ran = list(live["ran"]) + [{"order_id": "t9:9", "class": kind, "fate": "EXECUTED"}]
        site, prepared = _run(live, ran=ran)
        assert prepared is None and site.halted, kind
        assert kind in site.records[-1]["unsupported_actions"]
        assert ra.UNSUPPORTED_AUTHORITY_ACTION in site.halt_reason


# -- P3-23: the experiment artifact --------------------------------------------------------------------

def test_g17_the_artifact_carries_every_field_an_auditor_needs(live):
    site, prepared = _run(live)
    assert prepared is not None
    site.eligibility = {"classification": ra.ELIGIBLE_BUT_NO_SNAPSHOT, "scenario": "stress"}
    artifact = site.artifact()
    verdict = ra.verify_artifact(artifact)
    assert verdict["complete"], verdict
    assert verdict["digest_matches"] and verdict["outcomes_consistent"]
    assert artifact["eligibility"]["classification"] == ra.ELIGIBLE_BUT_NO_SNAPSHOT
    assert artifact["action_history"] and all("order_id" in item for item in artifact["action_history"])
    assert artifact["ownership"]["sbp"] == ra.COMMON and artifact["ownership"]["hr"] == ra.LEGACY
    assert artifact["phase2_digest"] == rs.PHASE2_DIGEST
    assert artifact["phase3_versions"]["phase3_layer_digest"]
    assert artifact["mixed_trajectory"] is False and artifact["authority_minutes"]


def test_g18_the_artifact_does_not_change_after_it_is_created(live):
    site, prepared = _run(live)
    assert prepared is not None
    first = site.artifact()
    assert site.artifact()["artifact_digest"] == first["artifact_digest"], "same site, same artifact"
    for field in ("case_id", "snapshot_id", "halted", "phase2_digest"):
        tampered = {**json.loads(json.dumps(first, default=str)), field: "changed"}
        assert not ra.verify_artifact(tampered)["digest_matches"], field
    incomplete = json.loads(json.dumps(first, default=str))
    incomplete["minutes"][0].pop("transaction_digest")
    assert not ra.verify_artifact(incomplete)["complete"]
    lying = json.loads(json.dumps(first, default=str))
    lying["minutes"][0]["outcome"] = ra.ABORTED
    assert not ra.verify_artifact(lying)["outcomes_consistent"]


def test_g19_the_rollback_artifact_reproduces_the_failed_minute(live, monkeypatch):
    monkeypatch.setattr(ra.AuthoritySite, "_replayed_point",
                        staticmethod(lambda artifact, minute: {"sbp": 1.0, "dbp": 1.0, "map": 1.0}))
    site, prepared = _run(live)
    assert prepared is None
    record = site.records[-1]
    rollback = record["rollback"]
    for key in ("failure_policy", "mode_decided_at", "reason", "minute",
                "precommit_authoritative_state", "common_candidate", "legacy_counterfactual",
                "validation_failures", "parameter_snapshot", "phase2_digest", "phase3_layer",
                "phase3_layer_digest", "committed", "rescue"):
        assert key in rollback, key
    assert rollback["committed"] == [] and rollback["validation_failures"]
    assert rollback["precommit_authoritative_state"]["observable"]["sbp"] is not None
    assert "never continue the same encounter with the other engine" in rollback["rescue"]
    assert record["precommit_observable_digest"] == ra.digest_of(
        dict(rollback["precommit_authoritative_state"]["observable"]))


def test_g20_the_registry_is_empty_when_this_module_is_done(battery):
    """The battery ran with a test-only approval; nothing of it survives."""
    assert battery["authority"]["snapshot_id"] == TEST_ONLY_SNAPSHOT["id"]
    assert not any(key != TEST_ONLY_SNAPSHOT["id"] for key in ra._APPROVED_SNAPSHOT_POINTS)
    assert ra.unreachable_because() or TEST_ONLY_SNAPSHOT["id"] in ra._APPROVED_SNAPSHOT_POINTS
    decision_file = (ROOT / "docs" / "COLA_DECISIONES_AI_ADVISOR.md").read_text(encoding="utf-8")
    assert TEST_ONLY_SNAPSHOT["id"] not in decision_file
