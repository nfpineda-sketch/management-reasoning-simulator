"""P3-46: the authority artifact records the SAME order identity and fate the runtime used.

P3-44 left two debts. A real encounter's artifact carried action classes with no canonical order id and
no fate, because the production call site runs the authority minute before the order pipeline settles
each order's fate; and it carried no eligibility row at all, so nothing in the record said why authority
had been allowed. Both are closed here, and these tests are what keeps them closed.

The repair does NOT move the commit. Everything about the physiology -- when an action activates, what
the common trajectory is, what the legacy counterfactual is -- is pinned against the values the first
experiment (P3-41) measured BEFORE the repair, which is what makes "provenance only" a claim and not an
intention.
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_authority_store as store
import runtime_shadow as rs

ROOT = Path(__file__).resolve().parent
CASE = "gi_bleed_57m"
SNAP = "gi_pressure_committed"
STORE_DIR = tempfile.mkdtemp(prefix="phase3-authority-provenance-")

#: What P3-41 measured before the repair: the three authority turns of B_delayed_management, the written
#: pressures, the legacy counterfactual and the minute each one landed on.
P341_TRAJECTORY = (
    {"minute": 30, "written": {"sbp": 80, "dbp": 49, "map": 59},
     "legacy": {"sbp": 84.0, "dbp": 52.0, "map": 63.0}, "kinds": ["reassessment"]},
    {"minute": 45, "written": {"sbp": 101, "dbp": 62, "map": 75},
     "legacy": {"sbp": 95.0, "dbp": 58.0, "map": 70.0},
     "kinds": ["blood", "consult", "fluid", "ppi", "reassessment"]},
    {"minute": 60, "written": {"sbp": 112, "dbp": 68, "map": 83},
     "legacy": {"sbp": 102.0, "dbp": 62.0, "map": 75.0}, "kinds": ["reassessment"]},
)


def _environ(**extra):
    out = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: SNAP,
           ra.ENVIRONMENT_FLAG: "development", rs.FLAG: rs.MODE_SHADOW_COMPARE,
           store.STORE_FLAG: STORE_DIR}
    out.update(extra)
    return out


@pytest.fixture(autouse=True)
def _pinned_store(monkeypatch):
    monkeypatch.setenv(store.STORE_FLAG, STORE_DIR)


def _run(monkeypatch, *, experiment_id, settle=True, orders_hook=None):
    """One real development authority encounter, in the production sequence.

    The authority hook is installed by wrapping ``ShadowSession.observe``, which receives exactly the
    five arguments ``app.py`` passes to ``minute``: the shadow's capture of the pre-turn state, the state
    the engine committed, the session, the actions whose fate the pipeline settled, and the submission
    id. ``settle_provenance`` is then called with the settled ledger, as ``app.py`` calls it after
    ``order_pipeline.settle``.
    """
    import order_ledger
    import pilot_acceptance as acceptance
    for name, value in _environ().items():
        monkeypatch.setenv(name, value)
    for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
        monkeypatch.delenv(name, raising=False)
    encounter = acceptance.Encounter(CASE)
    site = ra.open_site(encounter.state, environ=dict(os.environ), experiment_id=experiment_id)
    assert site is not None, "the authorized development configuration must open a site"
    real_observe = type(encounter.shadow).observe
    real_order = type(encounter).order
    reports, submissions = [], []

    def hooked_observe(self, before, state, parsed, result, run, submission_id):
        real_observe(self, before, state, parsed, result, run, submission_id)
        submissions.append(submission_id)
        prepared = site.minute(before, state, self, run, submission_id)
        if prepared is not None:
            state.clear()
            state.update(prepared)

    def hooked_order(self, text):
        """``app.py``'s sequence: the minute inside the turn, the provenance after the settlement.

        ``Encounter.order`` settles the fates and snapshots the ledger before it returns, so calling
        ``settle_provenance`` here is calling it exactly where the application calls it -- after
        ``order_pipeline.settle``, never inside the turn.
        """
        before = len(submissions)
        entry = real_order(self, text)
        if settle and len(submissions) > before:
            orders = [dict(order) for order in (entry.get("orders") or [])]
            if orders_hook is not None:
                orders = orders_hook(orders)
            reports.append(site.settle_provenance(submissions[-1], orders))
        return entry

    type(encounter.shadow).observe = hooked_observe
    type(encounter).order = hooked_order
    try:
        scripts = acceptance.scripts(CASE)
        encounter.order("Reassess in 30 minutes.")
        encounter.order(scripts["correct"] + " Reassess in 15 minutes.")
        encounter.wait_until(60)
    finally:
        type(encounter.shadow).observe = real_observe
        type(encounter).order = real_order
    return site, encounter, reports


@pytest.fixture(scope="module")
def _done():
    """One encounter, shared by the tests that only read its artifact."""
    with pytest.MonkeyPatch.context() as patch:
        site, encounter, reports = _run(patch, experiment_id="p346-shared")
        yield site, encounter, reports, site.artifact()


# -- A1, A2: the canonical identity and the settled fate ----------------------------------------------

def test_a1_a_real_successful_action_carries_a_canonical_order_id(_done):
    _site, _encounter, _reports, artifact = _done
    treated = [item for item in artifact["minutes"] if "fluid" in (item.get("action_kinds") or [])]
    assert treated, "the bundle minute must be in the artifact"
    for item in treated:
        rows = [dict(row) for row in (item.get("action_fates") or [])]
        assert rows, "the minute carries its settled orders"
        for row in rows:
            assert str(row.get("order_id") or "").strip(), row
            # The identity is the ledger's, not one this layer made up: ``t<turn>:<index>``.
            assert ":" in str(row["order_id"]), row
        assert {str(row.get("class")) for row in rows} >= {"fluid", "blood", "ppi", "consult"}


def test_a2_a_real_successful_action_carries_its_settled_fate(_done):
    _site, _encounter, _reports, artifact = _done
    did_not_act = ra.fates_that_did_not_act()
    assert did_not_act, "the ledger's own vocabulary must be readable"
    for item in artifact["minutes"]:
        for row in (item.get("action_fates") or []):
            fate = str(dict(row).get("fate") or "")
            assert fate, row
            assert fate not in did_not_act, "a committed minute consumed only orders that acted"
        assert item.get("provenance_settled") is True, item.get("minute")
    assert all(dict(row).get("fate") == "EXECUTED" for row in artifact["action_history"])


def test_a3_an_action_that_did_not_act_cannot_be_consumed_as_authority_treatment(monkeypatch):
    """P3-46-4. The site does not re-decide a fate: it compares, and a contradiction halts visibly."""
    did_not_act = sorted(ra.fates_that_did_not_act())
    assert did_not_act

    def forge(orders):
        return [{**dict(order),
                 "fate": ("SCHEDULED" if str(dict(order).get("class")) == "fluid"
                          else dict(order).get("fate"))}
                for order in orders]

    site, _encounter, reports = _run(monkeypatch, experiment_id="p346-contradiction",
                                     orders_hook=forge)
    halted = [report for report in reports if report["halted"]]
    assert halted, reports
    assert site.halted and site.experiment_state == ra.EXPERIMENT_HALTED
    assert ra.PROVENANCE_CONTRADICTION in site.halt_reason
    artifact = site.artifact()
    # The minute that committed is preserved exactly as it happened: faculty decision F forbids
    # rewriting it. The contradiction is a FRESH failure record beside it.
    committed = [item for item in artifact["minutes"] if item.get("outcome") == ra.COMMITTED]
    assert committed, artifact["minutes"]
    aborted = [item for item in artifact["minutes"] if item.get("outcome") == ra.ABORTED]
    # The contradiction is its own failure minute; the turns after the halt refuse for being after it.
    assert any(ra.PROVENANCE_CONTRADICTION in str(item.get("failure_reason")) for item in aborted), \
        [str(item.get("failure_reason")) for item in aborted]
    assert all(str(item.get("failure_reason")) for item in aborted), "every refusal states its reason"
    assert artifact["halted"] is True and artifact["experiment_state"] == ra.EXPERIMENT_HALTED


# -- A4, A5: the eligibility row ----------------------------------------------------------------------

def test_a4_the_artifact_carries_the_eligibility_decision_that_allowed_authority(_done):
    _site, _encounter, _reports, artifact = _done
    row = artifact.get("eligibility")
    assert isinstance(row, dict), "P3-44 found this missing on a real encounter"
    for name in ra.ELIGIBILITY_RECORD_FIELDS:
        assert name in row, name
    assert row["granted"] is True and row["classification"] == ra.ELIGIBLE_FOR_DEVELOPMENT
    assert row["family"] == ra.AUTHORITY_FAMILY and row["case_id"] == CASE
    assert list(row["domain"]) == list(ra.AUTHORITY_DOMAIN)
    assert row["snapshot_id"] == SNAP and row["phase2_digest"] == rs.PHASE2_DIGEST
    assert row["layer_version"] == rs.MODULE_VERSION
    assert row["artifact_store_configured"] is True and row["allowlisted"] is True
    assert row["pilot"]["looks_like_the_pilot"] is False
    assert sorted(row["conditions"]) == sorted(ra.GATE_CONDITIONS)
    assert all(row["conditions"].values()), row["conditions"]
    ok, why = ra.eligibility_is_consistent(artifact)
    assert ok, why


def test_a5_the_eligibility_row_is_the_gate_that_was_used(_done):
    """P3-46-6: not a second reading. Mutating a gate condition changes the eligibility result."""
    _site, _encounter, _reports, artifact = _done
    row = dict(artifact["eligibility"])
    for condition in ra.GATE_CONDITIONS:
        broken = {**row, "conditions": {**row["conditions"], condition: False}}
        ok, why = ra.eligibility_is_consistent({**artifact, "eligibility": broken})
        assert not ok and any(condition in reason for reason in why), (condition, why)
    for name, other in (("family", "acs"), ("case_id", "gi_bleed_99x"), ("snapshot_id", "other"),
                        ("environment", "production"), ("phase2_digest", "0" * 64)):
        ok, why = ra.eligibility_is_consistent({**artifact, "eligibility": {**row, name: other}})
        assert not ok, name
    ok, _why = ra.eligibility_is_consistent({**artifact, "eligibility": {**row, "granted": False}})
    assert not ok


# -- A6, A7: nothing about the physiology moved -------------------------------------------------------

def test_a6_the_provenance_repair_does_not_change_the_pressure_trajectory(_done):
    """Pinned against what P3-41 measured BEFORE the repair."""
    _site, _encounter, _reports, artifact = _done
    minutes = [item for item in artifact["minutes"] if item.get("outcome") == ra.COMMITTED]
    assert len(minutes) == len(P341_TRAJECTORY)
    for item, expected in zip(minutes, P341_TRAJECTORY):
        assert item["minute"] == expected["minute"]
        assert {key: dict(item["written_candidate"])[key] for key in ("sbp", "dbp", "map")} \
            == expected["written"], item["minute"]
        assert {key: dict(item["legacy_counterfactual"])[key] for key in ("sbp", "dbp", "map")} \
            == expected["legacy"], item["minute"]
        assert sorted(item["committed"]) == ["dbp", "map", "sbp"]


def test_a7_no_action_activates_a_minute_earlier_or_later(_done):
    _site, _encounter, _reports, artifact = _done
    minutes = [item for item in artifact["minutes"] if item.get("outcome") == ra.COMMITTED]
    for item, expected in zip(minutes, P341_TRAJECTORY):
        assert sorted(item.get("action_kinds") or []) == sorted(expected["kinds"]), item["minute"]
        for row in (item.get("action_fates") or []):
            executed_at = dict(row).get("executed_at_min")
            if executed_at is not None:
                # The order acted in the turn that reported it, never in a later or earlier one.
                assert int(executed_at) <= int(item["minute"]), row


def test_a7b_a_run_without_the_provenance_step_has_the_same_trajectory(monkeypatch):
    """The equivalence, measured rather than argued: settle or do not settle, the physiology is one."""
    with_settle, _e1, _r1 = _run(monkeypatch, experiment_id="p346-with")
    without, _e2, _r2 = _run(monkeypatch, experiment_id="p346-without", settle=False)
    keys = ("minute", "outcome", "committed", "common_candidate", "written_candidate",
            "legacy_counterfactual", "divergence_classes", "candidate_digest", "replay_digest",
            "transaction_digest", "action_kinds")
    a = [{key: item.get(key) for key in keys} for item in with_settle.artifact()["minutes"]]
    b = [{key: item.get(key) for key in keys} for item in without.artifact()["minutes"]]
    assert json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


# -- A8: the replay checks the provenance -------------------------------------------------------------

def test_a8_the_replay_validates_the_stored_identity_and_fate(_done):
    _site, _encounter, _reports, artifact = _done
    out = ra.replay_site_artifact(artifact)
    assert out["eligibility_present"] and out["eligibility_consistent"], out["eligibility_reasons"]
    assert out["provenance_settled_minutes"] == len(artifact["minutes"])
    assert out["provenance_consistent_minutes"] == len(artifact["minutes"])
    for row in out["minutes"]:
        assert row["provenance_settled"] and row["provenance_consistent"], row["minute"]
        assert not row["provenance_contradictions"]
    # An artifact whose stored fate says the order did not act is not consistent, and the replay says so.
    broken = json.loads(json.dumps(artifact, default=str))
    for item in broken["minutes"]:
        for row in item.get("action_fates") or []:
            row["fate"] = "SCHEDULED"
    assert all(not row["provenance_consistent"]
               for row in ra.replay_site_artifact(broken)["minutes"])
    # And neither is one whose stored identity is blank.
    blanked = json.loads(json.dumps(artifact, default=str))
    for item in blanked["minutes"]:
        for row in item.get("action_fates") or []:
            row["order_id"] = ""
    assert all(not row["provenance_consistent"]
               for row in ra.replay_site_artifact(blanked)["minutes"])


# -- A9 to A12: nothing else moved --------------------------------------------------------------------

def test_a9_the_shadow_behaviour_is_unchanged(_done):
    _site, encounter, _reports, _artifact = _done
    session = encounter.shadow
    assert session is not None and not session.failures, getattr(session, "failures", None)
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    # The shadow's own record of the encounter is the one it always kept: the authority site reads it.
    assert getattr(session.runner, "compared", None), "the shadow compared its minutes as before"


def test_a10_no_scoring_surface_is_reachable_from_the_provenance_repair():
    source = (ROOT / "runtime_authority.py").read_text(encoding="utf-8")
    for forbidden in ("score", "rubric", "radar", "penalt", " assessment"):
        offenders = [line for line in source.splitlines()
                     if forbidden in line.lower() and not line.strip().startswith("#")]
        assert not offenders, (forbidden, offenders[:2])
    import ast
    tree = ast.parse(source)
    imported = {name.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                for name in node.names} | {str(node.module) for node in ast.walk(tree)
                                           if isinstance(node, ast.ImportFrom) and node.module}
    assert not {name for name in imported if "scor" in name or "rubric" in name}, sorted(imported)
    # order_ledger is read for the fate vocabulary and for nothing else.
    assert "order_ledger" in imported
    assert source.count("import order_ledger") == 1


def test_a11_the_pilot_is_still_refused_with_the_repair_in_place(monkeypatch):
    import pilot_acceptance as acceptance
    state = dict(acceptance.Encounter(CASE).state)
    for extra in ({ra.PILOT_FLAGS[0]: "1"}, {ra.PILOT_FLAGS[1]: "1"},
                  {name: "1" for name in ra.PILOT_REQUIRED_ON}):
        environ = _environ(**extra)
        assert ra.open_site(state, environ=environ) is None, extra
        decision = ra.gate(state, environ=environ, unsupported=())
        assert not decision.conditions["no_pilot"]
        row = ra.eligibility_record(decision, family="gi_bleed", case_id=CASE,
                                    environment="development", snapshot=None, environ=environ)
        assert row["pilot"]["looks_like_the_pilot"] is True and row["granted"] is False


def test_a12_the_phase_two_digest_did_not_move(_done):
    _site, _encounter, _reports, artifact = _done
    assert artifact["phase2_digest"] == rs.PHASE2_DIGEST
    assert rs.PHASE2_DIGEST == "22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a"
    import runtime_shadow_evidence as ev
    # PHASE2_AMENDMENT_1: the closure has a successor, so the LIVE digest is the successor's. What must not
    # have moved is the historical closure, and it is still recomputed from the live files.
    assert ev.historical_closure_digest_now() == rs.PHASE2_DIGEST
    assert ev.phase2_digest_now() in {version.digest for version in rs.CORE_LINEAGE}
