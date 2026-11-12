"""P3-226 and P3-224C: the arming gate, the grant schema, and the commit-or-abort interface of the DORMANT pair site.

TEST-SIDE. FD-AUTH-10 says activation must require an explicit future authorization artifact that does not exist, and must NOT happen by a feature flag,
``COMMON_CORE_RUNTIME_AUTHORITY = True``, a snapshot name, an environment variable or a direct call to the commit function. This file attacks each of those and proves
the site stays unarmed and the commit refused. In this cycle two of the nine conditions (the faculty's grant and the faculty's approval) are FALSE, in source.

Test fixtures that look like a grant are visibly ``TEST_ONLY_FAKE_GRANT`` and cannot be loaded as configuration; the one positive control below patches the module's
own source constants INSIDE a single test (monkeypatch), which is the only way to arm it, and shows that arming still leaves a second closed lock.
"""
import ast
from copy import deepcopy
from pathlib import Path

import pytest

import observable_view as view
import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_authority_store as store
import runtime_pair_site as site_module
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import test_phase3_pair_site as base
from test_phase3_clock_routes import BEST, CASE, OTHER_GI, TEST_ONLY_SNAPSHOT, approved, bound  # noqa: F401 (fixtures)
from test_phase3_pair_site import _feed, infusion  # noqa: F401 (fixture)

ROOT = Path(__file__).resolve().parent
RUNTIME_MODULES = sorted(path for path in ROOT.glob("*.py") if not path.name.startswith(("test_", "regression_")))


def _grant(bound, **change):
    """A grant of the FACULTY kind, built inside a test: it exists only as a dict in one test and is registered nowhere."""
    live = pair.live_lineage()
    grant = {"kind": site_module.GRANT_KIND, "grant_id": "TEST-POSITIVE-CONTROL-1", "domain": site_module.PAIR_DOMAIN, "snapshot_id": bound.snapshot_id,
             "snapshot_version": bound.version, "snapshot_record_digest": bound.record_digest, "core_version": live["version_id"], "core_digest": live["digest"],
             "cases": [CASE, OTHER_GI], "decision_reference": "TEST ONLY: no faculty decision exists", "issued_by_role": "test"}
    grant.update(change)
    return grant


def _fake_grant(bound):
    return {**_grant(bound), "kind": site_module.TEST_ONLY_FAKE_GRANT, "grant_id": "TEST_ONLY_FAKE_GRANT-1"}


# -- the closed state of the repository ----------------------------------------------------------------------------------------------------------------------------

def test_g1_in_this_repository_the_faculty_conditions_are_false_the_registry_is_empty_and_nothing_is_armed(infusion):
    assert site_module.GRANT_REGISTRY == () and dict(site_module.FACULTY_APPROVAL) == {"GI_PAIR_AUTHORITY": "NOT_GRANTED"}
    assert len(site_module.ARMING_CONDITIONS) == 9 and site_module.FACULTY_CONDITIONS == ("explicit_pair_authority_grant", "faculty_approval_permits_domain")
    _feed(infusion)
    arming = infusion["site"].arming({})
    assert arming["armed"] is False and set(arming["conditions"]) == set(site_module.ARMING_CONDITIONS)
    assert arming["faculty_conditions"] == {"explicit_pair_authority_grant": False, "faculty_approval_permits_domain": False}
    # everything the REPOSITORY can show is in order: the faculty's two are what keep it closed
    assert [name for name in arming["failed"]] == ["global_development_capability", "explicit_pair_authority_grant", "faculty_approval_permits_domain"]
    assert sorted(ra.APPROVED_SNAPSHOTS) == ["gi_pressure_committed"] and pair.V1_ID not in ra.APPROVED_SNAPSHOTS and rs.COMMON_CORE_RUNTIME_AUTHORITY is False


def test_g2_no_runtime_module_sets_or_loads_a_grant_or_the_faculty_approval_and_the_fixture_kind_exists_nowhere_else():
    """The registry and the approval are SOURCE constants of one module; no other module assigns them, and nothing reads a grant from the environment or a file."""
    for path in RUNTIME_MODULES:
        text = path.read_text(encoding="utf-8")
        if path.name == "runtime_pair_site.py":
            continue
        for name in ("GRANT_REGISTRY", "FACULTY_APPROVAL", "TEST_ONLY_FAKE_GRANT", "request_commit", "arming_of"):
            assert name not in text, (path.name, name)
        # the site is NAMED by the layer's own declaration (``LAYER_SOURCES``) and built by the pair module's hook factory, lazily: those are the only two mentions
        assert ("runtime_pair_site" in text) == (path.name in ("runtime_shadow.py", "runtime_authority_pair.py")), path.name
    tree = ast.parse((ROOT / "runtime_pair_site.py").read_text(encoding="utf-8"))
    users = set()
    for function in (node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)):
        if any(isinstance(node, ast.Name) and node.id == "GRANT_REGISTRY" for node in ast.walk(function)):
            users.add(function.name)
    assert users == {"arming_of"}, users                                         # the only reader of the registry is the gate itself
    # no grant loader: no builtin ``open``, no ``json.load``, and the process environment is read in ONE function (the gate's developer capability)
    assert not [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open"]
    assert not [node for node in ast.walk(tree) if isinstance(node, ast.Attribute) and node.attr == "load" and ast.unparse(node.value) == "json"]
    environments = {function.name for function in ast.walk(tree) if isinstance(function, ast.FunctionDef)
                    for node in ast.walk(function) if isinstance(node, ast.Attribute) and ast.unparse(node) in ("os.environ", "os.getenv")}
    assert environments == {"arming_of"}, environments
    # the page, the order pipeline and every resident-facing module never name the interface
    for name in ("app.py", "pilot_acceptance.py", "order_pipeline.py"):
        text = (ROOT / name).read_text(encoding="utf-8") if (ROOT / name).exists() else ""
        assert "request_commit" not in text and "PairAuthorityTransaction" not in text and "runtime_pair_site" not in text, name


def test_g3_request_commit_is_the_only_caller_of_commit_in_the_site_and_it_asks_the_gate_first():
    tree = ast.parse((ROOT / "runtime_pair_site.py").read_text(encoding="utf-8"))
    callers = {function.name for function in ast.walk(tree) if isinstance(function, ast.FunctionDef)
               for node in ast.walk(function) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "commit"}
    assert callers == {"request_commit"}
    body = ast.unparse(next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "request_commit"))
    assert body.index("arming_of(") < body.index("COMMIT_REFUSED_NOT_ARMED") < body.index(".commit(")


# -- 226A: a flag, an env var, a snapshot name, V1, the global constant: none is enough ---------------------------------------------------------------------------

def _all_the_flags(approved_env):
    """Every environment variable the repository defines for the shadow, the authority, the snapshot, the dry run and the store, set the way a developer would."""
    return {**approved_env, pair.DRY_FLAG: pair.DRY_ON, ra.SNAPSHOT_FLAG: pair.V1_ID}


@pytest.mark.parametrize("label", ("flag_only", "all_flags", "snapshot_name_v1", "global_constant_true", "v1_only", "everything_at_once"))
def test_g4_flags_env_vars_a_snapshot_name_the_global_constant_or_v1_alone_do_not_arm_and_commit_is_refused(infusion, monkeypatch, approved, label):
    site = infusion["site"]
    _feed(infusion)
    environ = {"flag_only": {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY},
               "all_flags": _all_the_flags(approved),
               "snapshot_name_v1": {ra.SNAPSHOT_FLAG: pair.V1_ID, ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.ENVIRONMENT_FLAG: "development"},
               "global_constant_true": {},
               "v1_only": {},
               "everything_at_once": _all_the_flags(approved)}[label]
    if label in ("global_constant_true", "everything_at_once"):
        monkeypatch.setattr(rs, "COMMON_CORE_RUNTIME_AUTHORITY", True)
    target = deepcopy(infusion["after"])
    digest = ra.digest_of(target)
    result = site.request_commit(target, environ=environ)
    assert result["committed"] is False and result["prepared"] is None and result["outcome"] == site_module.COMMIT_REFUSED_NOT_ARMED
    assert result["arming"]["faculty_conditions"] == {"explicit_pair_authority_grant": False, "faculty_approval_permits_domain": False}
    assert ra.digest_of(target) == digest and site.state == site_module.WOULD_COMMIT and site.commit_requests[-1]["committed"] is False
    if label in ("all_flags", "everything_at_once"):
        assert result["arming"]["conditions"]["global_development_capability"] is True      # the flags DID satisfy the only condition a flag can
    if label == "v1_only":
        assert result["arming"]["conditions"]["exact_snapshot"] is True and result["arming"]["conditions"]["certified_lineage"] is True
    assert ra.gate(infusion["after"], environ=environ).granted is False                      # the pressure authority gate agrees: V1 is not an approved snapshot


def test_g5_calling_the_commit_function_directly_is_refused_by_the_transactions_own_gate(infusion, approved):
    """A caller who skips the site and uses the transaction itself meets the second lock: the nine-condition gate refuses at commit."""
    _feed(infusion)
    evidence = infusion["site"]._commit_evidence
    payload = pair.PairPayload(**evidence["payload"])
    transaction = pair.PairAuthorityTransaction(minute=payload.minute, case_id=CASE, snapshot=infusion["site"].pressure_snapshot, bound=infusion["site"].bound)
    transaction.capture(evidence["after"]).compute(payload, evidence["legacy_pressure"])
    assert transaction.validate(pressure=evidence["pressure_kwargs"], consciousness_ok={}, interval_ok=True, boundary_clear=True, window_open=True, one_course=True)
    target = deepcopy(infusion["after"])
    with pytest.raises(ra.AuthorityRefused) as refused:
        transaction.commit(target, environ=_all_the_flags(approved))                       # every flag on, V1 named, the transaction VALIDATED: still refused
    assert "gate refuses" in str(refused.value) and transaction.state == pair.PAIR_ABORTED and transaction.committed == ()
    assert ra.digest_of(target) == ra.digest_of(infusion["after"])


# -- 226B: the grant schema, the fixtures, the positive control ------------------------------------------------------------------------------------------------------

def test_g6_the_grant_schema_names_what_is_authorized_exactly_and_every_gap_is_a_named_refusal(bound):
    assert site_module.GRANT_FIELDS == ("kind", "grant_id", "domain", "snapshot_id", "snapshot_version", "snapshot_record_digest", "core_version", "core_digest", "cases",
                                        "decision_reference", "issued_by_role")
    good = _grant(bound)
    assert site_module.grant_problems(good, bound=bound, case_id=CASE) == []
    for name in site_module.GRANT_FIELDS:
        gap = {key: value for key, value in good.items() if key != name}
        assert f"MISSING_{name.upper()}" in site_module.grant_problems(gap, bound=bound, case_id=CASE), name
    cases = {"kind": site_module.WRONG_GRANT_KIND, "domain": site_module.WRONG_GRANT_DOMAIN, "snapshot_id": site_module.GRANT_SNAPSHOT_MISMATCH,
             "snapshot_record_digest": site_module.GRANT_SNAPSHOT_MISMATCH, "snapshot_version": site_module.GRANT_SNAPSHOT_MISMATCH, "core_digest": site_module.GRANT_CORE_MISMATCH,
             "core_version": site_module.GRANT_CORE_MISMATCH, "decision_reference": "MISSING_DECISION_REFERENCE"}
    for name, code in cases.items():
        wrong = _grant(bound, **{name: "x" if name != "snapshot_version" else 9, **({} if name != "decision_reference" else {name: ""})})
        assert code in site_module.grant_problems(wrong, bound=bound, case_id=CASE), name
    assert site_module.GRANT_CASE_NOT_NAMED in site_module.grant_problems(_grant(bound, cases=[OTHER_GI]), bound=bound, case_id=CASE)
    assert site_module.GRANT_CASE_NOT_NAMED in site_module.grant_problems(good, bound=bound, case_id="opioid_35m")
    assert site_module.NOT_A_GRANT in site_module.grant_problems("a grant", bound=bound, case_id=CASE)
    assert site_module.GRANT_SNAPSHOT_MISMATCH in site_module.grant_problems(good, bound=None, case_id=CASE)


def test_g7_a_test_only_fake_grant_is_never_loadable_whatever_registry_it_is_put_in(infusion, bound, monkeypatch):
    fake = _fake_grant(bound)
    assert site_module.grant_problems(fake, bound=bound, case_id=CASE) == [site_module.TEST_ONLY_GRANT_NOT_LOADABLE]
    _feed(infusion)
    monkeypatch.setattr(site_module, "GRANT_REGISTRY", (fake,))
    monkeypatch.setattr(site_module, "FACULTY_APPROVAL", {site_module.PAIR_DOMAIN: site_module.GRANTED})
    arming = infusion["site"].arming({ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.ENVIRONMENT_FLAG: "development", rs.FLAG: rs.MODE_SHADOW_COMPARE})
    assert arming["conditions"]["explicit_pair_authority_grant"] is False and arming["conditions"]["faculty_approval_permits_domain"] is True and arming["armed"] is False
    assert infusion["site"].request_commit(deepcopy(infusion["after"]), environ={})["outcome"] == site_module.COMMIT_REFUSED_NOT_ARMED
    # and the fixture kind appears in no runtime module except the one that REFUSES it (g2): there is nothing to load it from


def _arm(monkeypatch, bound, *, v1_approved=False):
    """The ONLY way to arm the site: patch the module's own source constants for the length of one test. Not an environment, not a file, not a flag.

    ``v1_approved`` is the SECOND lock's own test fixture: version 1 registered as an authority snapshot inside this one test (it is not, anywhere)."""
    monkeypatch.setattr(site_module, "GRANT_REGISTRY", (_grant(bound),))
    monkeypatch.setattr(site_module, "FACULTY_APPROVAL", {site_module.PAIR_DOMAIN: site_module.GRANTED})
    if v1_approved:
        monkeypatch.setitem(ra._APPROVED_SNAPSHOT_POINTS, pair.V1_ID, TEST_ONLY_SNAPSHOT)


def test_g8_positive_control_a_patched_source_arms_the_site_and_the_second_lock_still_refuses(infusion, bound, monkeypatch):
    """The gate is real (it CAN be satisfied by the faculty's act, in source), and satisfying it does not commit: the transaction re-evaluates the pressure authority gate,
    and V1 is ratified for development EXPERIMENTS, not approved."""
    _feed(infusion)
    _arm(monkeypatch, bound)
    environ = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.ENVIRONMENT_FLAG: "development", rs.FLAG: rs.MODE_SHADOW_COMPARE, ra.SNAPSHOT_FLAG: pair.V1_ID}
    arming = infusion["site"].arming(environ)
    assert arming["armed"] is True and arming["failed"] == [] and arming["faculty_conditions"] == {"explicit_pair_authority_grant": True, "faculty_approval_permits_domain": True}
    target = deepcopy(infusion["after"])
    result = infusion["site"].request_commit(target, environ=environ)
    assert result["committed"] is False and result["prepared"] is None and result["outcome"] == site_module.COMMIT_REFUSED_V1_NOT_APPROVED
    assert ra.digest_of(target) == ra.digest_of(infusion["after"]) and infusion["site"].state == site_module.WOULD_COMMIT


def test_g9_with_both_locks_opened_by_test_fixtures_the_commit_is_atomic_prepared_in_a_copy_and_never_touches_the_live_word(infusion, bound, monkeypatch, approved):
    """224C, TEST-ONLY: the whole interface works, in a COPY. All six fields or none; the target is the caller's and stays as it was; the live word does not move."""
    _feed(infusion)
    _arm(monkeypatch, bound, v1_approved=True)
    environ = _all_the_flags(approved) | {ra.SNAPSHOT_FLAG: TEST_ONLY_SNAPSHOT["id"]}
    target = deepcopy(infusion["after"])
    digest, word = ra.digest_of(target), target["observable"]["mental_status"]
    result = infusion["site"].request_commit(target, environ=environ)
    assert result["committed"] is True and result["outcome"] == site_module.COMMIT_PREPARED_FOR_THE_CALLER, result.get("reason")
    prepared = result["prepared"]
    assert prepared is not target and ra.digest_of(target) == digest                          # the caller's state was never touched
    assert prepared["observable"]["mental_status"] == word                                    # the LIVE word is exactly as it was
    outside, observable = pair.moved_fields(target, prepared)
    assert outside == {view.OVERLAY_KEY} and observable <= {"sbp", "dbp", "map"} and observable
    common = prepared[view.OVERLAY_KEY]["common"]
    assert set(common) == {"consciousness_category", "mental_status", "pulse_present"} and prepared[view.OVERLAY_KEY]["mapped_into_live_field"] is False
    assert infusion["site"].commit_requests[-1]["committed"] is True and infusion["site"].state == site_module.WOULD_COMMIT


@pytest.mark.parametrize("failure", ("transaction_validate_raises", "overlay_is_not_a_view", "no_pressure_evidence"))
def test_g10_any_failure_inside_the_commit_leaves_nothing_written_and_returns_nothing(infusion, bound, monkeypatch, approved, failure):
    """224C atomicity: a failure at any stage of the commit is a refusal with no prepared state, no partial pair and the target intact."""
    _feed(infusion)
    _arm(monkeypatch, bound, v1_approved=True)
    environ = _all_the_flags(approved) | {ra.SNAPSHOT_FLAG: TEST_ONLY_SNAPSHOT["id"]}
    if failure == "transaction_validate_raises":
        monkeypatch.setattr(pair.PairAuthorityTransaction, "validate", lambda self, **kw: (_ for _ in ()).throw(RuntimeError("injected")))
    elif failure == "overlay_is_not_a_view":
        monkeypatch.setattr(view, "overlay_problems", lambda overlay: ["injected: not a view"])
    else:
        infusion["site"]._commit_evidence["pressure_kwargs"] = None
    target = deepcopy(infusion["after"])
    result = infusion["site"].request_commit(target, environ=environ)
    assert result["committed"] is False and result["prepared"] is None and result["outcome"] == site_module.COMMIT_REFUSED_BY_TRANSACTION
    assert ra.digest_of(target) == ra.digest_of(infusion["after"])


def test_g11_a_halted_site_and_a_site_with_no_validated_interval_refuse_a_commit_even_when_armed(infusion, bound, monkeypatch, approved):
    _arm(monkeypatch, bound, v1_approved=True)
    environ = _all_the_flags(approved) | {ra.SNAPSHOT_FLAG: TEST_ONLY_SNAPSHOT["id"]}
    site = infusion["site"]
    assert site.request_commit(deepcopy(infusion["after"]), environ=environ)["outcome"] == site_module.COMMIT_REFUSED_NO_INTERVAL        # nothing was evaluated yet
    base._break_minute(infusion, 6, "no_candidate")
    _feed(infusion)
    assert site.state == site_module.EXPERIMENT_HALTED
    result = site.request_commit(deepcopy(infusion["after"]), environ=environ)
    assert result["outcome"] == site_module.COMMIT_REFUSED_HALTED and result["prepared"] is None


def test_g12_the_page_hook_never_asks_for_a_commit_whatever_the_flags(approved):
    """The only path from the page into this layer is ``after_clock_moved`` / ``after_orders_settled``: they evaluate and settle; they never request a commit."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = base.acceptance.Encounter(CASE)
        before, entry, ran = base._turn(encounter, "Give 500 mL normal saline over 30 minutes.")
    held = {}
    environ = {**approved, pair.DRY_FLAG: pair.DRY_ON}
    pair.after_clock_moved(held, encounter.shadow, before, encounter.state, ran, "s1", ra.ORDER_TURN, environ=environ)
    pair.after_orders_settled(held, encounter.shadow, [dict(item) for item in entry["orders"]], environ=environ)
    evaluator = held[pair.DRY_KEY][1]
    assert isinstance(evaluator, site_module.DormantPairSite) and evaluator.commit_requests == [] and evaluator.arming(environ)["armed"] is False
