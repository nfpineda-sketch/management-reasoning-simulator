"""P3-239, P3-239A, P3-239B, P3-240, P3-240A and P3-240B: ``GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V1``.

TEST-SIDE. The grant is the explicit, immutable, fingerprinted record of what the faculty authorized on 2026-11-12: development authority for the GI PRESSURE domain only,
on two cases, with the already-approved pressure snapshot and the certified common-core lineage. These tests prove its identity, its explicit exclusions, its immutability, that
every forgery of it is refused by name, that it is the TENTH condition of the authority gate (a flag alone, or the grant alone, never suffices), and that the page does not know it.
Every test here that needs the real grant function for a snapshot id other than the real one carries ``@pytest.mark.strict_grant`` (see ``conftest.py``).
"""
import ast
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import MappingProxyType

import pytest

import runtime_authority as ra
import runtime_pressure_grant as grants
import runtime_shadow as rs

ROOT = Path(__file__).resolve().parent
CASE, OTHER = "gi_bleed_57m", "gi_bleed_72f"
PINNED_FINGERPRINT = "3c29c2b9eb070ea1728bea2b17fd4484ff42c5105070c9402b17e73b29c3c136"
REAL = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: "gi_pressure_committed", ra.ENVIRONMENT_FLAG: "development"}
MEMBER = {"version_id": rs.CORE_LINEAGE[-1].version_id, "digest": rs.CORE_LINEAGE[-1].digest}


@pytest.fixture(scope="module")
def gi_state():
    import pilot_acceptance
    return deepcopy(pilot_acceptance.Encounter(CASE).state)


@pytest.fixture(autouse=True)
def _no_pilot(monkeypatch):
    for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
        monkeypatch.delenv(name, raising=False)


def _mutable(grant):
    return json.loads(json.dumps(grant, default=lambda value: list(value) if isinstance(value, tuple) else dict(value)))


def _problems(grant, **kwargs):
    return grants.grant_problems(grant, case_id=CASE, environment="development", snapshot_id="gi_pressure_committed", family="gi_bleed", lineage=MEMBER, **kwargs)


# -- P3-239: identity, bindings, immutability ---------------------------------------------------------------------------------------------------------------

def test_g1_the_grant_has_the_declared_identity_and_the_pinned_fingerprint():
    grant = grants.GRANT
    assert grant["grant_id"] == "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V1" and grant["grant_version"] == 1 and grant["kind"] == "FACULTY_GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT"
    assert grant["authority_mode"] == "PRESSURE_ONLY" and grant["status"] == "ACTIVE_FOR_DEVELOPMENT_EXPERIMENT" and grant["purpose"] == "DEVELOPMENT_AUTHORITY_EXPERIMENT_ONLY"
    assert grant["fingerprint"] == grants.GRANT_FINGERPRINT == PINNED_FINGERPRINT == grants.fingerprint_of(grant)
    assert grants.REGISTERED_GRANTS == (grant,) and grants.GRANT_FINGERPRINT == PINNED_FINGERPRINT, "exactly ONE grant is registered"
    assert grant["issued_by_role"] == "faculty" and "FD-P3-203" in grant["decision_reference"] and grant["issued_on"] == "2026-11-12"
    assert _problems(grant) == []


def test_g2_the_grant_binds_the_authority_mode_the_cases_the_snapshot_the_lineage_the_window_the_boundary_and_the_failure_policy():
    grant = grants.GRANT
    assert tuple(grant["cases"]) == (CASE, OTHER) and grant["family"] == "gi_bleed" and tuple(grant["environments"]) == ("development",)
    assert grant["pressure_snapshot"]["id"] == "gi_pressure_committed" and grant["pressure_snapshot"]["value_digest"] == ra.APPROVED_POINT_DIGESTS["gi_pressure_committed"]
    assert grant["core_lineage"]["version_id"] == rs.CORE_LINEAGE[-1].version_id and grant["core_lineage"]["digest"] == rs.CORE_LINEAGE[-1].digest
    assert grant["window"]["max_minute"] == 240 == grants.WINDOW_MINUTES
    boundary = grant["collapse_boundary"]
    assert boundary["boundary"] == "ESTABLISHED" and boundary["impending_is_a_boundary"] is False and boundary["fails_closed"] is True and boundary["is_a_terminal_state"] is False
    assert boundary["checked"] == "PRECOMMIT_EVERY_MINUTE_OF_THE_INTERVAL" and boundary["resident_text"] == "none" and boundary["is_patient_death"] is False
    policy = grant["failure_policy"]
    assert policy["after_the_first_commit"] == "INVALID_FOR_CONTINUATION" and policy["silent_fallback_to_the_legacy_engine"] is False and policy["is_patient_death"] is False
    assert policy["before_the_first_commit"].startswith("EXPERIMENT_HALTED")


def test_g3_the_domain_is_exactly_the_pressure_and_the_excluded_domains_are_listed_explicitly_not_left_to_omission():
    grant = grants.GRANT
    assert tuple(grant["domain"]) == ("sbp", "dbp", "map") == ra.AUTHORITY_DOMAIN
    assert set(grant["excluded_domains"]) == {"consciousness", "mental_status", "collapse", "terminal", "pulse", "oxygenation", "lactate", "hb"}
    assert not set(grant["domain"]) & set(grant["excluded_domains"])
    overlay = grant["consciousness_overlay"]
    assert overlay["snapshot_id"] == "GI_DEVELOPMENT_SNAPSHOT_V1" and overlay["label"] == "FACULTY_ACCEPTED_FOR_DEVELOPMENT_COMPARISON"
    assert overlay["authority"] is False and overlay["resident_visible"] is False and overlay["writes_mental_status"] is False and overlay["used_as_pressure_calibration"] is False
    assert "consciousness authority" in grant["not_granted"] and "mental_status writes" in grant["not_granted"] and "terminal semantics" in grant["not_granted"]


def test_g4_the_grant_is_immutable_and_a_changed_body_does_not_import():
    with pytest.raises(TypeError):
        grants.GRANT["authority_mode"] = "PAIR_PRESSURE_CONSCIOUSNESS"
    with pytest.raises(TypeError):
        grants.GRANT["domain"][0] = "mental_status"          # a tuple
    with pytest.raises(TypeError):
        grants.GRANT["window"]["max_minute"] = 10 ** 6       # a read-only nested mapping
    assert isinstance(grants.GRANT, MappingProxyType) and isinstance(grants.GRANT["window"], MappingProxyType) and isinstance(grants.REGISTERED_GRANTS, tuple)
    source = (ROOT / "runtime_pressure_grant.py").read_text(encoding="utf-8")
    for old, new in (('"issued_on": "2026-11-12"', '"issued_on": "2026-11-13"'), ('"max_minute": WINDOW_MINUTES', '"max_minute": 999'), ('"authority": False, "resident_visible"', '"authority": True, "resident_visible"')):
        assert old in source, old
        completed = subprocess.run([sys.executable, "-B", "-c", f"import sys; sys.path.insert(0, {str(ROOT)!r}); exec(compile({source.replace(old, new)!r}, 'runtime_pressure_grant.py', 'exec'), {{'__name__': 'tampered'}})"],
                                   capture_output=True, text=True, timeout=120, cwd=str(ROOT))
        assert completed.returncode != 0 and "RuntimeError" in completed.stderr, (old, completed.stderr[-300:])


# -- P3-239A: forgeries are refused, each by name ----------------------------------------------------------------------------------------------------------

def _coherent(forged):
    """A forger who also recomputes the fingerprint: only the PINNED fingerprint can catch the edit."""
    forged["fingerprint"] = grants.fingerprint_of(forged)
    return forged


@pytest.mark.parametrize("edit, expected", [
    (lambda g: g.update(domain=["sbp", "dbp", "map", "mental_status"]), grants.DOMAIN_NOT_PRESSURE),
    (lambda g: g.update(domain=["sbp", "dbp", "map", "consciousness"]), grants.DOMAIN_NOT_PRESSURE),
    (lambda g: g.update(excluded_domains=["consciousness", "mental_status", "collapse", "terminal", "pulse", "oxygenation", "lactate"]), grants.EXCLUSION_MISSING),
    (lambda g: g.update(excluded_domains=list(g["excluded_domains"]) + ["sbp"]), grants.EXCLUSION_OVERLAPS),
    (lambda g: g.update(cases=["gi_bleed_57m", "gi_bleed_72f", "acs_54m_inferior"]), grants.CASE_NOT_NAMED),
    (lambda g: g.update(cases=["gi_bleed_57m"]), grants.CASE_NOT_NAMED),
    (lambda g: g.update(environments=["development", "faculty"]), grants.ENVIRONMENT_NOT_NAMED),
    (lambda g: g.update(environments=["production"]), grants.ENVIRONMENT_NOT_NAMED),
    (lambda g: g.update(family="acs"), grants.FAMILY_MISMATCH),
    (lambda g: g.update(authority_mode="PAIR_PRESSURE_CONSCIOUSNESS"), grants.WRONG_MODE),
    (lambda g: g.update(status="PROPOSED"), grants.NOT_ACTIVE),
    (lambda g: g.update(purpose="PRODUCTION"), grants.WRONG_PURPOSE),
    (lambda g: g.update(kind="FACULTY_GI_PAIR_AUTHORITY_GRANT"), grants.WRONG_KIND),
    (lambda g: g.update(grant_version=2), grants.NOT_IN_REGISTRY_ID),
    (lambda g: g.update(grant_id="GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V2"), grants.NOT_IN_REGISTRY_ID),
    (lambda g: g.update(decision_reference=""), grants.NO_DECISION),
    (lambda g: g["pressure_snapshot"].update(id="GI_DEVELOPMENT_SNAPSHOT_V1"), grants.SNAPSHOT_MISMATCH),
    (lambda g: g["pressure_snapshot"].update(value_digest="0" * 64), grants.SNAPSHOT_DIGEST_MISMATCH),
    (lambda g: g["core_lineage"].update(version_id="HISTORICAL_PHASE2_CLOSURE"), grants.CORE_MISMATCH),
    (lambda g: g["core_lineage"].update(digest="1" * 64), grants.CORE_MISMATCH),
    (lambda g: g["window"].update(max_minute=10 ** 6), grants.WINDOW_WRONG),
    (lambda g: g["collapse_boundary"].update(impending_is_a_boundary=True), grants.BOUNDARY_POLICY_WRONG),
    (lambda g: g["collapse_boundary"].update(fails_closed=False), grants.BOUNDARY_POLICY_WRONG),
    (lambda g: g["collapse_boundary"].update(is_a_terminal_state=True), grants.BOUNDARY_POLICY_WRONG),
    (lambda g: g["failure_policy"].update(silent_fallback_to_the_legacy_engine=True), grants.FAILURE_POLICY_WRONG),
    (lambda g: g["failure_policy"].update(after_the_first_commit="LEGACY_CONTINUES"), grants.FAILURE_POLICY_WRONG),
    (lambda g: g["consciousness_overlay"].update(authority=True), grants.OVERLAY_AUTHORITATIVE),
    (lambda g: g["consciousness_overlay"].update(writes_mental_status=True), grants.OVERLAY_AUTHORITATIVE),
    (lambda g: g["consciousness_overlay"].update(resident_visible=True), grants.OVERLAY_AUTHORITATIVE),
    (lambda g: g["consciousness_overlay"].update(used_as_pressure_calibration=True), grants.OVERLAY_WRONG),
    (lambda g: g["consciousness_overlay"].update(snapshot_id="gi_pressure_committed"), grants.OVERLAY_WRONG),
    (lambda g: g.update(note="CLINICALLY_VALIDATED"), grants.FORBIDDEN_CLAIM),
    (lambda g: g.update(note="CONSCIOUSNESS_AUTHORITY_GRANTED"), grants.FORBIDDEN_CLAIM),
])
def test_g5_every_forgery_of_the_grant_is_refused_by_name_even_when_the_forger_recomputes_the_fingerprint(edit, expected):
    forged = _mutable(grants.GRANT)
    edit(forged)
    found = _problems(forged)
    assert any(problem.startswith(expected) for problem in found), (expected, found)
    assert grants.FINGERPRINT_MISMATCH in found, "an edit without recomputing the fingerprint is caught by the body"
    coherent = _problems(_coherent(deepcopy(forged)))
    assert any(problem.startswith(expected) for problem in coherent) and grants.FINGERPRINT_NOT_PINNED in coherent, (expected, coherent)


def test_g6_what_is_not_a_grant_and_the_fixture_kind_are_never_loadable():
    assert grants.grant_problems(None) == [grants.NOT_A_GRANT] and grants.grant_problems("a string") == [grants.NOT_A_GRANT] and grants.grant_problems({}) != []
    fixture = {**_mutable(grants.GRANT), "kind": grants.TEST_ONLY_FIXTURE_KIND}
    assert grants.grant_problems(fixture) == [grants.TEST_ONLY_GRANT_NOT_LOADABLE]
    for wrong in (dict(case_id=OTHER + "_x"), dict(case_id="acs_54m_inferior"), dict(environment="faculty"), dict(environment="production"), dict(snapshot_id="GI_DEVELOPMENT_SNAPSHOT_V1"),
                  dict(family="acs"), dict(lineage={"version_id": "PHASE2_AMENDMENT_1", "digest": "x"})):
        found = grants.grant_problems(grants.GRANT, **{**dict(case_id=CASE, environment="development", snapshot_id="gi_pressure_committed", family="gi_bleed", lineage=MEMBER), **wrong})
        assert found, wrong


# -- P3-240: the grant is the tenth condition of the gate ----------------------------------------------------------------------------------------------------

@pytest.mark.strict_grant
def test_g7_with_the_real_snapshot_the_flags_and_the_grant_the_gate_grants_and_only_then(gi_state):
    decision = ra.gate(gi_state, environ=REAL, unsupported=())
    assert decision.granted and decision.conditions["explicit_development_grant"] is True and len(decision.conditions) == 10 == len(ra.GATE_CONDITIONS)


@pytest.mark.strict_grant
def test_g8_the_grant_is_the_only_failing_condition_when_the_registry_is_empty_or_the_environment_is_not_the_granted_one(gi_state, monkeypatch):
    monkeypatch.setattr(grants, "REGISTERED_GRANTS", ())
    decision = ra.gate(gi_state, environ=REAL, unsupported=())
    assert not decision.granted and [name for name, ok in decision.conditions.items() if not ok] == ["explicit_development_grant"], decision.conditions
    assert any("NO_EXPLICIT_DEVELOPMENT_GRANT_FOR_THIS_RUN" in reason for reason in decision.reasons)
    monkeypatch.undo()
    faculty = ra.gate(gi_state, environ={**REAL, ra.ENVIRONMENT_FLAG: "faculty"}, unsupported=())
    assert not faculty.granted and [name for name, ok in faculty.conditions.items() if not ok] == ["explicit_development_grant"], faculty.conditions
    assert ra.open_site(gi_state, environ={**REAL, ra.ENVIRONMENT_FLAG: "faculty"}) is None


@pytest.mark.strict_grant
def test_g9_a_flag_alone_the_global_constant_or_the_grant_alone_never_starts_an_experiment(gi_state, monkeypatch):
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    # the global constant does not appear in the gate at all, and setting it opens nothing
    assert "COMMON_CORE_RUNTIME_AUTHORITY" not in ast.unparse(next(node for node in ast.walk(ast.parse((ROOT / "runtime_authority.py").read_text(encoding="utf-8")))
                                                                  if isinstance(node, ast.FunctionDef) and node.name == "gate"))
    monkeypatch.setattr(rs, "COMMON_CORE_RUNTIME_AUTHORITY", True)
    assert not ra.gate(gi_state, environ={}, unsupported=()).granted
    # the grant alone (every flag absent): nothing starts
    assert not ra.gate(gi_state, environ={}, unsupported=()).conditions["authority_flag"] and ra.open_site(gi_state, environ={}) is None
    # the flags alone WITHOUT the grant (registry empty): refused
    monkeypatch.setattr(grants, "REGISTERED_GRANTS", ())
    assert not ra.gate(gi_state, environ=REAL, unsupported=()).granted
    # the global constant AND every flag, still without the grant: refused
    assert not ra.gate(gi_state, environ={**REAL, "MRS_PHASE3_GLOBAL": "1"}, unsupported=()).granted


@pytest.mark.strict_grant
def test_g10_the_case_allowlist_rejects_everything_else_before_the_first_commit(gi_state):
    import pilot_acceptance
    import runtime_shadow_evidence as ev
    for other in ("acs_54m_inferior", "opioid_35m"):
        try:
            with ev.shadow(rs.MODE_SHADOW_COMPARE):
                state = deepcopy(pilot_acceptance.Encounter(other).state)
        except Exception:
            continue
        decision = ra.gate(state, environ=REAL, unsupported=())
        assert not decision.granted and not decision.conditions["family_and_case"] and not decision.conditions["explicit_development_grant"], other
    for wrong in ({"family": "acs"}, {"case_id": "gi_bleed_99x"}):
        decision = ra.gate(gi_state, environ=REAL, unsupported=(), **wrong)
        assert not decision.granted


@pytest.mark.strict_grant
def test_g11_v1_is_not_a_pressure_snapshot_and_the_overlay_snapshot_cannot_stand_in_for_it(gi_state):
    decision = ra.gate(gi_state, environ={**REAL, ra.SNAPSHOT_FLAG: "GI_DEVELOPMENT_SNAPSHOT_V1"}, unsupported=())
    assert not decision.granted and not decision.conditions["approved_snapshot"] and not decision.conditions["explicit_development_grant"]
    assert "GI_DEVELOPMENT_SNAPSHOT_V1" not in ra.APPROVED_SNAPSHOTS and sorted(ra.APPROVED_SNAPSHOTS) == ["gi_pressure_committed"]


# -- P3-240A/B: nothing reads a grant from outside, the page does not know it -------------------------------------------------------------------------------

def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    return names | {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}


def test_g12_the_grant_module_reads_nothing_from_the_outside_and_imports_nothing_of_the_repository():
    tree = ast.parse((ROOT / "runtime_pressure_grant.py").read_text(encoding="utf-8"))
    text = ast.unparse(tree)
    for forbidden in ("os.environ", "getenv", "open(", "read_text", "json.load(", "Path("):
        assert forbidden not in text, forbidden
    assert _imports(ROOT / "runtime_pressure_grant.py") <= {"__future__", "hashlib", "json", "types", "typing"}
    assert "runtime_pressure_grant.py" in rs.LAYER_SOURCES


def test_g13_only_the_grant_module_and_the_gate_name_the_registry_and_the_page_does_not_import_the_grant():
    readers = sorted(path.name for path in ROOT.glob("*.py") if not path.name.startswith("test_") and path.name != "conftest.py" and "REGISTERED_GRANTS" in path.read_text(encoding="utf-8"))
    assert readers == ["runtime_pressure_grant.py"], readers
    assert "runtime_pressure_grant" not in _imports(ROOT / "app.py"), "the page cannot see the grant: the layer reads it"
    importers = sorted(path.name for path in ROOT.glob("*.py") if not path.name.startswith("test_") and path.name != "conftest.py" and "runtime_pressure_grant" in _imports(path))
    # P3-288 (declared adaptation): the two faculty-review modules READ the identity of the grant (its id, version, cases, mode, snapshot id and fingerprint) to describe and to check the review
    # configuration; the gate stays the only module that DECIDES with it. What the test protects -- nobody but the gate can permit -- is protected twice: the importers are pinned, and the
    # attributes the review modules read are pinned to read-only constants (never ``permits``, ``grant_problems``, the registry or any grant constructor).
    assert importers == ["runtime_authority.py", "runtime_faculty_bundle.py", "runtime_faculty_review.py"], importers
    read_only = {"AUTHORITY_MODE", "CASES", "FAMILY", "GRANT", "GRANT_FINGERPRINT", "GRANT_ID", "GRANT_VERSION", "PRESSURE_SNAPSHOT_ID"}
    for name in ("runtime_faculty_review.py", "runtime_faculty_bundle.py"):
        tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
        used = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "grants"}
        assert used <= read_only, (name, sorted(used - read_only))
