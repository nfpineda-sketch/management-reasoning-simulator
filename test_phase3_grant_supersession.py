"""P3-387 (FD-TONE-09 to FD-TONE-11): which GI pressure grant a NEW development session can run under, and what the older ones still do.

The audit found that after the promotion of 2026-11-16 the older pressure point (``gi_pressure_committed``, grant version 1) was still a second
accepted configuration of the live gate: an environment that named it opened a new authoritative session. The faculty decided it must stay
replayable and must not be selectable for new sessions. This file defends that, and the re-ligation that the successor core required:

  * three grants are registered; versions 1 and 2 are byte for byte what they were (fingerprints pinned here, typed again);
  * version 3 is version 2's scope on the successor core, with only declared differences -- the same snapshot, cases, domain, environments, window,
    boundary, failure policy and overlay; no new authority; norepinephrine and the Amendment-3 reader named as NOT granted;
  * by ORDINARY configuration a superseded version opens nothing; only an explicit historical reconstruction names it, the declaration is never
    honoured from a Secret, and it is checked against what the live certified core actually rebuilds;
  * a reconstruction says what it is: it is not a new development session.

Tests marked ``ordinary_configuration`` run without the session-wide declaration ``conftest.py`` installs for the older suites.
"""
import copy

import pytest

import runtime_authority as ra
import runtime_pressure_grant as grants
import runtime_pressure_snapshot as ps
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import test_runtime_authority as base

V1_POINT, V2_POINT = grants.PRESSURE_SNAPSHOT_ID, grants.PRESSURE_SNAPSHOT_ID_V2
A2 = {"version_id": "PHASE2_AMENDMENT_2", "digest": "a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2"}
FLAG = "MRS_PHASE3_HISTORICAL_RECONSTRUCTION"
RUN = {"case_id": "gi_bleed_57m", "environment": "development", "family": "gi_bleed", "domain": grants.DOMAIN}


def _plain(value):
    """A frozen grant as plain, editable data."""
    if hasattr(value, "items"):
        return {key: _plain(item) for key, item in value.items()}
    return tuple(_plain(item) for item in value) if isinstance(value, tuple) else value


def _live() -> dict:
    return {"version_id": rs.CORE_LINEAGE[-1].version_id, "digest": rs.CORE_LINEAGE[-1].digest}


def _env(point: str, **more) -> dict:
    env = {key: value for key, value in base.DEV_ENV.items() if key != FLAG}
    env[ra.SNAPSHOT_FLAG] = point
    if point == V2_POINT:
        env[ps.SNAPSHOT_FLAG] = ps.SNAPSHOT_ID
    env.update(more)
    return env


# -- the registry ----------------------------------------------------------------------------------------------------------------------

def test_three_grants_are_registered_and_the_two_older_ones_are_what_they_were():
    assert [item["grant_id"] for item in grants.REGISTERED_GRANTS] == [grants.GRANT_ID, grants.GRANT_ID_V2, grants.GRANT_ID_V3]
    assert grants.GRANT_ID == "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V1" and grants.GRANT_ID_V2.endswith("_V2") and grants.GRANT_ID_V3.endswith("_V3") and FLAG == grants.HISTORICAL_RECONSTRUCTION_FLAG
    assert grants.GRANT["fingerprint"] == grants.GRANT_FINGERPRINT == "3c29c2b9eb070ea1728bea2b17fd4484ff42c5105070c9402b17e73b29c3c136"
    assert grants.GRANT_V2["fingerprint"] == grants.GRANT_FINGERPRINT_V2 == "8a91145dbfe899dffdc5de1ed28b116c61f4fa5b462a49979727ce8b05b3642f"
    assert grants.GRANT_V3["fingerprint"] == grants.GRANT_FINGERPRINT_V3 == grants.fingerprint_of(grants.GRANT_V3)
    for grant in grants.REGISTERED_GRANTS:
        assert grants.grant_problems(grant) == [], grant["grant_id"]
        assert grants.lineage_of(grant)["version_id"] in {version.version_id for version in rs.CORE_LINEAGE}
        with pytest.raises(TypeError):
            grant["status"] = "REVOKED"
    assert grants.lineage_of(grants.GRANT) == grants.lineage_of(grants.GRANT_V2) == A2 and grants.lineage_of(grants.GRANT_V3) == _live()
    assert dict(grants.SUPERSEDED[grants.GRANT_ID])["by"] == grants.GRANT_ID_V2 and dict(grants.SUPERSEDED[grants.GRANT_ID_V2])["by"] == grants.GRANT_ID_V3
    assert set(grants.SUPERSEDED) == {grants.GRANT_ID, grants.GRANT_ID_V2} and all("FD-TONE" in entry["decision_reference"] for entry in grants.SUPERSEDED.values())
    assert grants.LIVE_GRANT_ID == grants.GRANT_ID_V3 and grants.LIVE_GRANT is grants.GRANT_V3
    assert [item["grant_id"] for item in grants.REGISTERED_GRANTS if not grants.is_superseded(item["grant_id"])] == [grants.GRANT_ID_V3]


def test_version_three_is_version_twos_scope_on_the_successor_core_and_nothing_more():
    v2, v3 = dict(grants.GRANT_V2), dict(grants.GRANT_V3)
    declared = {"grant_id", "grant_version", "core_lineage", "promotion", "lineage_rebind", "decision_reference", "issued_on", "not_granted", "fingerprint"}
    assert {key for key in set(v2) | set(v3) if v2.get(key) != v3.get(key)} == declared
    for key in ("kind", "authority_mode", "status", "purpose", "domain", "excluded_domains", "family", "cases", "environments", "window", "pressure_snapshot",
                "collapse_boundary", "failure_policy", "consciousness_overlay"):
        assert v2[key] == v3[key], key
    assert "promotion" not in v3 and "lineage_rebind" not in v2
    rebind = dict(v3["lineage_rebind"])
    assert rebind["kind"] == "LINEAGE_REBIND_ONLY" and rebind["supersedes_grant_id"] == grants.GRANT_ID_V2
    assert dict(rebind["from_core"]) == A2 and dict(rebind["to_core"]) == _live() == dict(v3["core_lineage"])
    assert (rebind["pressure_snapshot_unchanged"], rebind["scope_unchanged"], rebind["new_calibration"], rebind["new_authority"]) == (True, True, False, False)
    assert rebind["successor_reader_declared_by_this_authority"] is False and "OFF BY DEFAULT" in rebind["successor_physiology"]
    assert "GI_BLOOD_RESUSCITATION_LOW_END_RESPONSE" in rebind["monitored_limitation"]
    kept = set(v2["not_granted"]) - {"Amendment 3 physiology"}
    assert kept <= set(v3["not_granted"])
    assert {"norepinephrine", "any vasopressor or other vascular-tone intervention", "the Amendment 3 vasoconstrictor reader", "source control",
            "consciousness authority", "terminal semantics", "resident deployment", "clinical validation"} <= set(v3["not_granted"])
    assert grants.summary(grants.GRANT_V3)["lineage_decision"] == "LINEAGE_REBIND_ONLY" and grants.summary(grants.GRANT_V3)["supersedes_grant_id"] == grants.GRANT_ID_V2


def test_a_rebind_that_claims_more_than_a_rebind_is_refused_by_name():
    body = _plain(grants.GRANT_V3)
    for change in ({"new_authority": True}, {"new_calibration": True}, {"scope_unchanged": False}, {"pressure_snapshot_unchanged": False},
                   {"successor_reader_declared_by_this_authority": True}, {"supersedes_grant_id": grants.GRANT_ID}, {"kind": "NEW_GRANT"},
                   {"to_core": A2}, {"from_core": _live()}, {"the_live_core_rebuilds_the_earlier_lineage_exactly": False}):
        forged = {**body, "lineage_rebind": {**body["lineage_rebind"], **change}}
        forged["fingerprint"] = grants.fingerprint_of(forged)
        found = grants.grant_problems(forged)
        assert grants.REBIND_POLICY_WRONG in found and grants.FINGERPRINT_NOT_PINNED in found, change
    with_promotion = {**body, "promotion": dict(grants.GRANT_V2["promotion"])}
    assert grants.REBIND_POLICY_WRONG in grants.grant_problems(with_promotion)
    on_the_old_core = {**body, "core_lineage": A2}
    assert grants.CORE_MISMATCH in grants.grant_problems(on_the_old_core)
    v2_with_a_rebind = {**dict(grants.GRANT_V2), "lineage_rebind": body["lineage_rebind"]}
    assert grants.REBIND_POLICY_WRONG in grants.grant_problems(v2_with_a_rebind)


# -- which grant a run stands under ------------------------------------------------------------------------------------------------------

def test_an_unqualified_run_gets_the_one_live_version_and_a_declaration_gets_only_the_grant_it_names():
    assert grants.grant_for_snapshot(V2_POINT) is grants.GRANT_V3
    assert grants.grant_for_snapshot(V1_POINT) is None                                        # only a superseded version binds the older point
    assert grants.grant_for_snapshot(V2_POINT, grants.GRANT_ID_V2) is grants.GRANT_V2
    assert grants.grant_for_snapshot(V1_POINT, grants.GRANT_ID) is grants.GRANT
    assert grants.grant_for_snapshot(V2_POINT, grants.GRANT_ID) is grants.GRANT_V3            # a declaration that names ANOTHER snapshot's grant changes nothing
    assert grants.grant_for_snapshot(V1_POINT, grants.GRANT_ID_V2) is None
    assert grants.grant_for_snapshot(V2_POINT, grants.GRANT_ID_V3) is grants.GRANT_V3         # the live version is not a "reconstruction"
    for junk in ("", "V1", "gi_pressure_committed", grants.GRANT_ID.lower(), 1, object()):
        assert grants.grant_for_snapshot(V1_POINT, junk) is None and grants.grant_for_snapshot(V2_POINT, junk) is grants.GRANT_V3
    assert grants.grant_for_snapshot("another_point") is None and grants.grant_for_snapshot(None, grants.GRANT_ID) is None
    assert grants.reconstruction_named({FLAG: grants.GRANT_ID}) == grants.GRANT_ID and grants.reconstruction_named({FLAG: f"  {grants.GRANT_ID_V2} "}) == grants.GRANT_ID_V2
    for value in ("", "1", "true", grants.GRANT_ID_V3, "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V9", grants.GRANT_ID.lower()):
        assert grants.reconstruction_named({FLAG: value}) is None, value
    assert grants.reconstruction_named({}) is None and grants.reconstruction_named(None) is None


def test_a_superseded_grant_authorizes_nothing_by_ordinary_configuration():
    ok, reasons = grants.permits(**RUN, snapshot_id=V1_POINT, lineage=_live())
    assert not ok and any(reason.startswith(f"{grants.SUPERSEDED_FOR_NEW_SESSIONS}: {grants.GRANT_ID} ") for reason in reasons)
    ok, reasons = grants.permits(**RUN, snapshot_id=V1_POINT, lineage=A2)                      # even on the lineage it names
    assert not ok and any(reason.startswith(f"{grants.SUPERSEDED_FOR_NEW_SESSIONS}: {grants.GRANT_ID} ") for reason in reasons)
    ok, reasons = grants.permits(**RUN, snapshot_id=V2_POINT, lineage=A2)                      # version 2's own lineage, no declaration: superseded, and version 3 names another core
    assert not ok and grants.CORE_MISMATCH in reasons and any(grants.GRANT_ID_V2 in reason and reason.startswith(grants.SUPERSEDED_FOR_NEW_SESSIONS) for reason in reasons)
    assert grants.permits(**RUN, snapshot_id=V2_POINT, lineage=_live()) == (True, [])        # the one live version
    for case in ("gi_bleed_57m", "gi_bleed_72f"):
        assert grants.permits(**{**RUN, "case_id": case}, snapshot_id=V2_POINT, lineage=_live())[0] is True
    assert grants.permits(**{**RUN, "case_id": "acs_70f_left_main"}, snapshot_id=V2_POINT, lineage=_live())[0] is False
    assert grants.permits(**{**RUN, "environment": "production"}, snapshot_id=V2_POINT, lineage=_live())[0] is False
    assert grants.permits(**{**RUN, "domain": ("sbp", "dbp", "map", "mental_status")}, snapshot_id=V2_POINT, lineage=_live()) == (False, [grants.DOMAIN_NOT_PRESSURE])


def test_a_declared_reconstruction_needs_the_live_core_to_rebuild_the_grants_lineage():
    declared = {"historical_reconstruction": grants.GRANT_ID}
    assert grants.permits(**RUN, snapshot_id=V1_POINT, lineage=_live(), **declared, rebuilt_lineages=(A2,)) == (True, [])
    ok, reasons = grants.permits(**RUN, snapshot_id=V1_POINT, lineage=_live(), **declared)
    assert not ok and any(reason.startswith(grants.RECONSTRUCTION_NOT_POSSIBLE) for reason in reasons)
    for wrong in (({"version_id": "PHASE2_AMENDMENT_2", "digest": "f" * 64},), (_live(),), ({"version_id": "PHASE2_AMENDMENT_1", "digest": A2["digest"]},), ("PHASE2_AMENDMENT_2",), (None,)):
        ok, reasons = grants.permits(**RUN, snapshot_id=V1_POINT, lineage=_live(), **declared, rebuilt_lineages=wrong)
        assert not ok and any(reason.startswith(grants.RECONSTRUCTION_NOT_POSSIBLE) for reason in reasons), wrong
    # the declaration opens the grant it names and no other: version 1 declared does not open version 2's snapshot under version 2
    assert grants.permits(**RUN, snapshot_id=V2_POINT, lineage=A2, **declared, rebuilt_lineages=(A2,))[0] is False
    assert grants.permits(**RUN, snapshot_id=V2_POINT, lineage=_live(), historical_reconstruction=grants.GRANT_ID_V2, rebuilt_lineages=(A2,)) == (True, [])
    # a reconstruction runs on the LIVE core: a caller that names another one as "live" is refused, whatever it says the core rebuilds (review finding 8)
    for forged in (A2, {"version_id": "x", "digest": "y"}, {}):
        ok, reasons = grants.permits(**RUN, snapshot_id=V1_POINT, lineage=forged, **declared, rebuilt_lineages=(A2,))
        assert not ok and len(reasons) == 1 and reasons[0].startswith(grants.CORE_MISMATCH), forged
    # and a declared reconstruction that cannot be honoured is decided by that grant alone: it never falls through to the live version
    ok, reasons = grants.permits(**RUN, snapshot_id=V2_POINT, lineage=_live(), historical_reconstruction=grants.GRANT_ID_V2)
    assert not ok and len(reasons) == 1 and reasons[0].startswith(grants.RECONSTRUCTION_NOT_POSSIBLE)
    # and a reconstruction widens nothing else
    assert grants.permits(**{**RUN, "case_id": "acs_70f_left_main"}, snapshot_id=V1_POINT, lineage=_live(), **declared, rebuilt_lineages=(A2,))[0] is False
    assert grants.permits(**{**RUN, "environment": "production"}, snapshot_id=V1_POINT, lineage=_live(), **declared, rebuilt_lineages=(A2,))[0] is False


def test_the_live_core_offers_only_its_immediate_predecessor_and_only_while_the_lineage_holds(monkeypatch):
    assert ev.rebuilt_predecessors() == (A2,)
    monkeypatch.setattr(ev, "core_lineage_verdict", lambda: {"ok": False, "active_core": rs.CORE_LINEAGE[-1].version_id})
    assert ev.rebuilt_predecessors() == ()
    monkeypatch.undo()
    from clinical_core import amendment_3 as a3
    monkeypatch.setattr(a3, "amendment_2_digest_now", lambda: "f" * 64)
    assert ev.rebuilt_predecessors() == ()
    monkeypatch.undo()

    def broken():
        raise OSError("no record")
    monkeypatch.setattr(ev, "core_lineage_verdict", broken)
    assert ev.rebuilt_predecessors() == ()


# -- the gate and the site, by ordinary configuration ---------------------------------------------------------------------------------

@pytest.mark.ordinary_configuration
def test_the_older_point_opens_no_new_session_by_ordinary_configuration(gi_state):
    import os
    assert FLAG not in os.environ
    env = _env(V1_POINT)
    decision = ra.gate(gi_state, environ=env, unsupported=())
    assert not decision.granted and any(grants.SUPERSEDED_FOR_NEW_SESSIONS in reason for reason in decision.reasons), decision.reasons
    assert ra.open_site(gi_state, environ=env) is None
    assert ra.historical_reconstruction(env) is None and ra.historical_reconstruction() is None


@pytest.mark.ordinary_configuration
def test_the_ratified_snapshot_opens_under_version_three_by_ordinary_configuration(gi_state):
    env = _env(V2_POINT)
    decision = ra.gate(gi_state, environ=env, unsupported=())
    assert decision.granted, decision.to_dict()
    site = ra.open_site(gi_state, environ=env)
    assert site is not None and "historical_reconstruction" not in site.eligibility
    assert site.grant is grants.GRANT_V3 and site.grant["fingerprint"] == grants.GRANT_FINGERPRINT_V3
    assert grants.summary(site.grant)["pressure_snapshot_id"] == V2_POINT and grants.summary(site.grant)["core_version"] == rs.CORE_LINEAGE[-1].version_id


@pytest.mark.ordinary_configuration
def test_a_declared_reconstruction_opens_the_older_point_and_says_it_is_not_a_new_session(gi_state):
    env = _env(V1_POINT, **{FLAG: grants.GRANT_ID})
    assert ra.historical_reconstruction(env) == grants.GRANT_ID
    decision = ra.gate(gi_state, environ=env, unsupported=())
    assert decision.granted, decision.to_dict()
    site = ra.open_site(gi_state, environ=env)
    assert site is not None and site.grant is grants.GRANT
    said = site.eligibility["historical_reconstruction"]
    assert said["grant_id"] == grants.GRANT_ID and said["superseded_by"] == grants.GRANT_ID_V2 and said["is_a_new_development_session"] is False
    assert said["live_core"] == _live() and said["rebuilt_core"] == A2 and said["declared_by"] == FLAG


@pytest.mark.ordinary_configuration
def test_a_declaration_is_never_honoured_from_a_secret_and_a_wrong_one_declares_nothing(gi_state, monkeypatch):
    env = _env(V1_POINT, **{FLAG: grants.GRANT_ID})
    monkeypatch.setattr(rs, "_named_in_secrets", lambda name: name == FLAG)
    assert ra.historical_reconstruction(env) is None
    assert not ra.gate(gi_state, environ=env, unsupported=()).granted and ra.open_site(gi_state, environ=env) is None
    monkeypatch.undo()
    for value in (grants.GRANT_ID_V2, grants.GRANT_ID_V3, "1", "GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V9"):
        wrong = _env(V1_POINT, **{FLAG: value})
        assert not ra.gate(gi_state, environ=wrong, unsupported=()).granted, value
        assert ra.open_site(gi_state, environ=wrong) is None, value


@pytest.mark.ordinary_configuration
def test_a_reconstruction_is_refused_when_the_live_core_does_not_rebuild_the_grants_lineage(gi_state, monkeypatch):
    env = _env(V1_POINT, **{FLAG: grants.GRANT_ID})
    monkeypatch.setattr(ev, "rebuilt_predecessors", lambda: ())
    decision = ra.gate(gi_state, environ=env, unsupported=())
    assert not decision.granted and any(grants.RECONSTRUCTION_NOT_POSSIBLE in reason for reason in decision.reasons), decision.reasons
    assert ra.open_site(gi_state, environ=env) is None


@pytest.fixture(scope="module")
def gi_state():
    import pilot_acceptance
    return copy.deepcopy(pilot_acceptance.Encounter(base.CASE).state)
