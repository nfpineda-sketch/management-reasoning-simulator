"""P3-248, the independent review's confirmed findings (M1 to M5 and the cheap LOWs), as executable controls.

TEST-SIDE. The reviewer (read-only) attacked the real pressure authority and the author reproduced each MEDIUM with an own probe BEFORE repairing it; every control below is the
probe turned into a test, and the mutation runner (``MRS_`` none; see the report) removes each repair to prove the control can fail.

* M1 an encounter resumed after a commit has no site (the saved session does not carry it): the stored experiment is MARKED, never left ACTIVE.
* M2 the replay of a genuine post-commit halt whose cause lives in the settled ledger reproduces (the evidence is searched where it is recorded).
* M3 a relabelled halt reason is not accepted (the aborted minute names the same reason; the unsupported-class branch has no tautology); a reason that cannot be re-derived says so.
* M4 verification and replay refuse an artifact that COMMITTED a minute past the window or without a clear collapse boundary, and a turn whose verdict is not what its parts give.
* M5 the label does not switch the real checks off: content decides, and an artifact that contradicts its own label is INCONSISTENT.
* L1 a turn that does not move the clock is stored without an identity collision; L2 a turn after a halt does not copy the stale overlay; L3 the failure handler cannot raise into the
  page; L4 ``permits`` names every dimension (an omitted one is a refusal).
"""
import json
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_authority_store as store
import runtime_pressure_grant as grants
import runtime_shadow as rs

STORE_DIR = tempfile.mkdtemp(prefix="phase3-pressure-review-")
REAL = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: "gi_pressure_committed", ra.ENVIRONMENT_FLAG: "development", rs.FLAG: rs.MODE_SHADOW_COMPARE,
        store.STORE_FLAG: STORE_DIR}
CASE = "gi_bleed_57m"


@pytest.fixture(autouse=True, scope="module")
def _real_environment():
    """Module-scoped, so the module's own fixtures (which build encounters and need the shadow flag at construction) see the real development configuration too."""
    with pytest.MonkeyPatch.context() as patch:
        for name, value in REAL.items():
            patch.setenv(name, value)
        for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
            patch.delenv(name, raising=False)
        yield


def _plain(value):
    return json.loads(ra.canonical(value))


def _seal(artifact: dict) -> dict:
    body = {key: value for key, value in artifact.items() if key != "artifact_digest"}
    return {**body, "artifact_digest": ra.digest_of(body)}


class Driver:
    """A real GI encounter and a REAL authority site, imitating the page's two clock routes (an order turn and clinical time outside an order turn)."""

    def __init__(self, case=CASE):
        import pilot_acceptance
        self.enc = pilot_acceptance.Encounter(case)
        self.arrival = deepcopy(self.enc.state)
        self.site = ra.open_site(self.arrival, environ=REAL)
        assert self.site is not None and self.site.grant is not None

    @property
    def state(self):
        return self.enc.state

    def order(self, text):
        import order_ledger
        import order_pipeline
        import time_semantics
        from family_parser import parse_family_actions
        enc = self.enc
        submission = f"t{enc._turns}"
        enc._turns += 1
        minute = int(enc.state.get("sim_time", 0) or 0)
        parsed = time_semantics.apply(text, parse_family_actions(text))
        parsed.setdefault("raw_text", text)
        turn = order_pipeline.open_turn(text, parsed, submission_id=submission, entry_point="free_text", minute=minute, ledger=enc.ledger)
        before = enc.shadow.capture(enc.state)
        result, split, run = enc._execute(parsed, text)
        enc.shadow.observe(before, enc.state, parsed, result, run, submission)
        prepared = self.site.minute(before, enc.state, enc.shadow, run, submission)
        if prepared is not None:
            enc.state = prepared
        order_pipeline.settle(turn, result=result, run_actions=run, split=split, minute_before=minute, minute_after=int(enc.state.get("sim_time", 0) or 0),
                              terminal=bool(result.get("terminal_locked")))
        orders = order_ledger.snapshot(turn["orders"])
        order_pipeline.upsert(enc.ledger, turn["orders"])
        self.site.settle_provenance(submission, orders)
        return prepared

    def ask(self, minutes=2):
        from family_engine import advance_clinical_time
        enc = self.enc
        before = enc.shadow.capture(enc.state)
        result = advance_clinical_time(enc.state, minutes, label="question")
        enc.shadow.observe_time(before, enc.state, result)
        prepared = self.site.minute(before, enc.state, enc.shadow, None, None, ra.CLINICAL_TIME)
        if prepared is not None:
            enc.state = prepared
        return prepared


@pytest.fixture(scope="module")
def ledger_only_halt():
    """A genuine halt AFTER a commit whose only evidence is the settled ledger (an unmodelled class on a turn that did not move the clock)."""
    d = Driver()
    d.order("Give 1 litre of normal saline over 15 minutes.")
    d.order("Place an IV line. Give ondansetron 4 mg IV.")
    assert d.site.halted and d.site.minutes_committed, (d.site.halt_reason, d.site.records[-1:])
    return d.site.artifact()


@pytest.fixture(scope="module")
def boundary_halt():
    """A genuine halt at the collapse boundary: four hours with no treatment."""
    d = Driver()
    for _ in range(4):
        d.ask(60)
    assert d.site.halted and d.site.halt_reason.startswith(ra.COLLAPSE_BOUNDARY_REACHED), d.site.halt_reason
    return d.site.artifact()


@pytest.fixture(scope="module")
def active_artifact():
    d = Driver()
    d.order("Give 1 litre of normal saline over 15 minutes.")
    assert not d.site.halted and d.site.minutes_committed
    return d.site.artifact()


# -- M2 -----------------------------------------------------------------------------------------------------------------------------------------------------

def test_r1_a_genuine_post_commit_halt_caused_by_the_settled_ledger_reproduces(ledger_only_halt):
    verdict, replay = ra.verify_artifact(ledger_only_halt), ra.replay_site_artifact(ledger_only_halt)
    assert ledger_only_halt["halt_reason"].startswith(ra.PROVENANCE_CONTRADICTION) and ledger_only_halt["experiment_outcome"] == "INVALID_FOR_CONTINUATION"
    assert verdict["complete"], verdict
    assert replay["halt_reason_replay"]["rederived"] and replay["halt_reason_replay"]["reproduces"] and replay["reproduces"], replay["halt_reason_replay"]


def test_r1b_the_evidence_is_searched_where_it_is_recorded_not_only_on_the_failure_record(ledger_only_halt):
    failed = next(record for record in ledger_only_halt["minutes"] if record["outcome"] == ra.ABORTED)
    assert not failed.get("provenance_contradictions"), "the failure record is fresh: the contradiction is recorded on the turn that carried it"
    assert any(item.get("provenance_contradictions") for item in ledger_only_halt.get("no_advance_turns", []) + ledger_only_halt["minutes"])


# -- M3 -----------------------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("reason", ["UNSUPPORTED_AUTHORITY_ACTION: ['x']", "SITE_ERROR boom", ra.CONFIGURATION_CHANGED, f"{ra.MINUTE_ALREADY_COMMITTED}: 5", ra.WINDOW_CLOSED])
def test_r2_a_relabelled_halt_reason_is_not_accepted_even_with_the_digest_recomputed(boundary_halt, reason):
    forged = _plain(boundary_halt)
    forged["halt_reason"] = reason
    forged = _seal(forged)
    replay = ra.replay_site_artifact(forged)
    assert not replay["reproduces"] and not replay["halt_reason_replay"]["reproduces"], replay["halt_reason_replay"]
    assert not ra.verify_artifact(forged)["complete"], "the derived fields and the first recorded failure also contradict the relabelled reason"


def test_r2b_the_unsupported_class_branch_has_no_tautology(boundary_halt):
    forged = _plain(boundary_halt)
    failed = next(record for record in forged["minutes"] if record["outcome"] == ra.ABORTED)
    forged["halt_reason"] = failed["failure_reason"] = "UNSUPPORTED_AUTHORITY_ACTION: ['x']"
    replay = ra.replay_site_artifact(_seal(forged))
    assert replay["halt_reason_replay"]["kind"] == ra.UNSUPPORTED_AUTHORITY_ACTION and not replay["halt_reason_replay"]["reproduces"], "no unsupported class is recorded anywhere"


def test_r2c_a_reason_that_cannot_be_re_derived_says_so_and_is_declared_in_the_verdict(boundary_halt):
    forged = _plain(boundary_halt)
    failed = next(record for record in forged["minutes"] if record["outcome"] == ra.ABORTED)
    forged["halt_reason"] = failed["failure_reason"] = "SITE_ERROR RuntimeError: boom"
    replay = ra.replay_site_artifact(_seal(forged))
    assert replay["halt_reason_replay"]["rederived"] is False and replay["halt_reason_rederived"] is False
    assert "the halt reason is recorded, not re-derived" in replay["verdict_notes"], "a consumer is told this reason was not re-derived (the digest has no signature: a forger who rewrites both fields is a declared limit)"
    assert replay["verdict"] == "every committed minute reproduces", "the verdict text itself is the certified one"


# -- M4 -----------------------------------------------------------------------------------------------------------------------------------------------------

def test_r3_an_artifact_that_committed_through_the_boundary_or_past_the_window_is_refused_by_verification_and_replay(monkeypatch):
    """A regression that lets the precommit guard pass would be invisible to the artifact before the repair; now the artifact must SHOW the rule was kept."""
    monkeypatch.setattr(ra.AuthoritySite, "_boundary_guard", lambda self, minute: "")
    d = Driver()
    for _ in range(5):
        d.ask(60)
    artifact = d.site.artifact()
    assert 240 in artifact["authority_minutes"] and 300 in artifact["authority_minutes"], artifact["authority_minutes"]
    verdict, replay = ra.verify_artifact(artifact), ra.replay_site_artifact(artifact)
    assert not verdict["complete"] and not replay["reproduces"]
    text = " | ".join(verdict["real_claims_problems"])
    assert "without a clear collapse boundary" in text and "past the experiment window" in text, text


def test_r3b_a_genuine_artifact_has_no_such_problem(boundary_halt, active_artifact):
    for artifact in (boundary_halt, active_artifact):
        assert ra.verify_artifact(artifact)["real_claims_problems"] == [] and ra.verify_artifact(artifact)["complete"]


def test_r3c_a_forged_turn_verdict_or_digest_is_not_accepted_by_the_overlay_replay(boundary_halt):
    forged = _plain(boundary_halt)
    turns = forged["consciousness_overlay"]["turns"]
    unclear = next(turn for turn in turns if not turn["clear"])
    unclear["clear"] = True
    unclear["digest"] = ra.digest_of({key: value for key, value in unclear.items() if key != "digest"})
    forged["consciousness_overlay"]["record_digest"] = ra.digest_of([turn["digest"] for turn in turns])
    replay = ra.replay_site_artifact(_seal(forged))
    assert not replay["overlay_replay"]["reproduces"] and not replay["reproduces"], replay["overlay_replay"]["mismatches"]
    stale = _plain(boundary_halt)
    stale["consciousness_overlay"]["turns"][0]["failed"] = ["x"]
    assert not ra.replay_site_artifact(_seal(stale))["overlay_replay"]["reproduces"], "a turn edited without its digest is refused (and the record digest)"
    # a field no other check re-derives (the legacy word the turn recorded), edited with the ARTIFACT digest recomputed: only the turn's own digest can see it
    recorded = _plain(boundary_halt)
    recorded["consciousness_overlay"]["turns"][0]["legacy_mental_status"] = "Alert-but-edited"
    refused = ra.replay_site_artifact(_seal(recorded))["overlay_replay"]
    assert not refused["reproduces"] and any("digest does not recompute" in text for text in refused["mismatches"]), refused["mismatches"]


# -- M5 / L6 ------------------------------------------------------------------------------------------------------------------------------------------------

def test_r4_lowering_or_removing_the_label_does_not_switch_the_real_checks_off(active_artifact, boundary_halt):
    for artifact in (active_artifact, boundary_halt):
        for label in (ra.HISTORICAL_PRESSURE_LABEL, None, "SOMETHING_ELSE"):
            forged = _plain(artifact)
            forged["consciousness_overlay"]["turns"][0]["rows"][0]["F"] = 0.123
            forged["grant"]["fingerprint"] = "0" * 64
            if label is None:
                del forged["authority_label"]
            else:
                forged["authority_label"] = label
            forged = _seal(forged)
            assert ra.artifact_class(forged) == ra.INCONSISTENT_ARTIFACT
            verdict = ra.verify_artifact(forged)
            assert not verdict["complete"] and not ra.replay_site_artifact(forged)["reproduces"]
            assert verdict["label_matches_content"] is False
            assert verdict["grant_is_the_registered_one"] is False and verdict["real_claims_problems"] is not None, "the real checks RAN (they were not switched off by the lowered label)"


def test_r4b_a_label_without_the_content_is_inconsistent_too_and_a_genuine_historical_artifact_is_not_touched(active_artifact):
    bare = {key: value for key, value in _plain(active_artifact).items() if key not in ra.REAL_CONTENT_KEYS and key != "authority_label"}
    bare["minutes"] = [{key: value for key, value in record.items() if key not in ra.REAL_MINUTE_CONTENT_KEYS} for record in bare["minutes"]]
    historical = _seal(bare)
    assert ra.artifact_class(historical) == ra.HISTORICAL_PRESSURE_LABEL and not ra.claims_real_content(historical)
    labelled = _seal({**bare, "authority_label": ra.REAL_PRESSURE_LABEL})
    assert ra.artifact_class(labelled) == ra.INCONSISTENT_ARTIFACT and not ra.verify_artifact(labelled)["complete"]


@pytest.mark.parametrize("edit", [
    lambda a: a.update(halted=True),
    lambda a: a.update(experiment_outcome="INVALID_FOR_CONTINUATION"),
    lambda a: a.update(authority_began=False),
    lambda a: a.update(mixed_trajectory=True),
    lambda a: a.update(invalid_for_continuation="HALTED/INVALID_FOR_CONTINUATION"),
    lambda a: a.update(authority_minutes=[]),
    lambda a: a["post_commit_policy"].update(silent_fallback_to_the_legacy_engine=True),
    lambda a: a["post_commit_policy"].update(is_patient_death=True),
    lambda a: a["grant"].update(window_max_minute=999),
    lambda a: a["grant"].update(cases=["gi_bleed_57m", "acs_48m_wellens"]),
    lambda a: a["grant"].update(core_version="OTHER"),
    lambda a: a["grant"].update(pressure_snapshot_id="GI_DEVELOPMENT_SNAPSHOT_V1"),
    lambda a: a["collapse_boundary"]["policy"].update(boundary="IMPENDING"),
    lambda a: a["collapse_boundary"].update(window_max_minute=999),
])
def test_r5_every_derived_field_of_a_real_artifact_is_re_derived_not_trusted(active_artifact, edit):
    forged = _plain(active_artifact)
    edit(forged)
    forged = _seal(forged)
    assert not ra.verify_artifact(forged)["complete"], "a derived field edited with the digest recomputed must stop verifying"
    assert not ra.replay_site_artifact(forged)["reproduces"]


# -- M1 -----------------------------------------------------------------------------------------------------------------------------------------------------

def test_r6_an_encounter_resumed_after_a_commit_is_marked_not_left_active(monkeypatch):
    d = Driver()
    d.order("Give 1 litre of normal saline over 15 minutes.")
    saved = _plain(d.state)
    assert d.site.minutes_committed == (15,)
    fresh = {"state": saved}
    assert ra.site_for(saved, fresh, environ=REAL) is None, "the saved session carries no site: the page cannot continue the experiment"
    status = ra.authority_status(fresh)
    assert status["experiment_state"] == ra.EXPERIMENT_HALTED and status["mixed_trajectory"] is True and status["authority_minutes"] == [15] and status["halted"]
    marker = fresh[ra.ARTIFACT_KEY]
    assert marker["halt_reason"].startswith(ra.RESUMED_WITHOUT_SITE) and marker["experiment_outcome"] == "INVALID_FOR_CONTINUATION" and marker["resumed_at_minute"] == 15
    assert ra.verify_artifact(marker)["complete"] and ra.replay_site_artifact(marker)["reproduces"]
    assert ra.replay_site_artifact(marker)["halt_reason_replay"]["rederived"] is False
    durable = [row for row in store.records(environ=REAL) if row["halted"] and row["artifact_id"] == store.artifact_id(marker)]
    assert durable and durable[0]["mixed_trajectory"] and durable[0]["artifact_class"] == ra.REAL_PRESSURE_LABEL
    # the same page asking again, or the same session resumed twice, does not write a second marker nor raise
    again = ra.note_resume_without_site(saved, fresh, REAL)
    assert again is None, "checked once per case and minute of a session"
    other_session = {"state": saved}
    assert ra.note_resume_without_site(saved, other_session, REAL)["artifact_digest"] == marker["artifact_digest"], "the same resume is the same record (idempotent)"


def test_r6b_a_resume_that_matches_no_stored_experiment_marks_nothing(monkeypatch):
    d = Driver()
    d.order("Give 1 litre of normal saline over 15 minutes.")
    state = _plain(d.state)
    state["observable"]["sbp"] = int(state["observable"]["sbp"]) + 7              # not the pressure any stored experiment committed
    session = {}
    assert ra.note_resume_without_site(state, session, REAL) is None and ra.ARTIFACT_KEY not in session
    arrival = {"state": deepcopy(d.arrival)}
    assert ra.note_resume_without_site(d.arrival, arrival, REAL) is None, "an arrival (minute 0) is not a resume"
    unconfigured = {key: value for key, value in REAL.items() if key != store.STORE_FLAG}
    assert ra.note_resume_without_site(_plain(d.state), {}, unconfigured) is None, "with no store there is nothing durable to mark"


# -- L1, L2, L3, L4 -----------------------------------------------------------------------------------------------------------------------------------------

def test_r7_a_turn_that_does_not_move_the_clock_is_stored_without_an_identity_collision():
    d = Driver()
    d.order("Give 1 litre of normal saline over 15 minutes.")
    before = d.site.stored
    d.order("Place an IV line.")
    assert not d.site.halted and d.site.no_advance_turns
    stored = d.site.stored
    assert stored.get("stored") is True and stored.get("why", "") == "", stored
    assert stored["artifact_id"] != before["artifact_id"], "the quiet turn is part of the identity: its evidence is durable, not lost until the next minute"
    quiet = [row for row in store.records(encounter_id=d.site.encounter_id, environ=REAL)]
    assert len(quiet) >= 2


def test_r8_a_turn_after_a_halt_does_not_copy_the_stale_overlay():
    d = Driver()
    d.ask(60)
    d.order("Start norepinephrine at 10 mcg/min.")
    assert d.site.halted
    size = len(ra.canonical(d.site.artifact()))
    for _ in range(10):
        d.ask(5)
    after_halt = [record for record in d.site.records if record.get("failure_reason") == ra.SITE_HALTED]
    assert len(after_halt) == 10 and all(record["consciousness_overlay"] is None and record["legacy_non_authority"] is None for record in after_halt)
    assert len(ra.canonical(d.site.artifact())) - size < 10 * 6000, "each post-halt turn is a small record, not a copy of the last overlay turn"


def test_r9_the_failure_handler_cannot_raise_into_the_page(monkeypatch):
    def broken(self):
        raise RuntimeError("the real-fields constructor is broken")
    monkeypatch.setattr(ra.AuthoritySite, "_real_minute_fields", broken)
    d = Driver()
    d.order("Give 1 litre of normal saline over 15 minutes. Start norepinephrine at 10 mcg/min.")     # an unsupported class: a refusal is built
    assert d.site.halted
    record = d.site.records[-1]
    assert "real_fields_error" in record and record["grant_id"] == grants.GRANT_ID and record["collapse_boundary"]["clear"] is False


def test_r10_the_one_question_names_every_dimension_of_the_run():
    good = dict(case_id=CASE, environment="development", snapshot_id="gi_pressure_committed", family="gi_bleed", domain=grants.DOMAIN,
                lineage={"version_id": rs.CORE_LINEAGE[-1].version_id, "digest": rs.CORE_LINEAGE[-1].digest})
    assert grants.permits(**good)[0] is True
    for name in ("case_id", "environment", "snapshot_id", "family", "lineage"):
        omitted = dict(good, **{name: None})
        ok, reasons = grants.permits(**omitted)
        assert ok is False and any(grants.RUN_DIMENSION_NOT_NAMED in reason and name in reason for reason in reasons), (name, reasons)
    assert grants.permits(case_id=None, environment=None, snapshot_id=None, family=None, domain=grants.DOMAIN)[0] is False
