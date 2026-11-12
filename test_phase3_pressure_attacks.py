"""P3-248 (the part that does not need the page): the attacks on the real pressure authority, as executable controls.

TEST-SIDE. A real GI encounter and a REAL site (the real registered pressure approval and the real grant) are built headlessly, and each control attacks one claim: a forged grant,
a commit before the grant is validated, a tampered artifact, an artifact that names another grant or another authority mode, an overlay that tries to write, a leak of the common
consciousness to a reader. Every one must fail closed, by name. The page-level attacks (wrong case, boundary, post-commit failure, long infusion) are in the series and failure files.
"""
import ast
import json
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

import observable_view as view
import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_authority_store as store
import runtime_pressure_grant as grants
import runtime_shadow as rs

ROOT = Path(__file__).resolve().parent
CASE = "gi_bleed_57m"
STORE_DIR = tempfile.mkdtemp(prefix="phase3-pressure-attacks-")
REAL = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: "gi_pressure_committed", ra.ENVIRONMENT_FLAG: "development", rs.FLAG: rs.MODE_SHADOW_COMPARE,
        store.STORE_FLAG: STORE_DIR}
OVERLAY_TOKENS = ("FACULTY_ACCEPTED_FOR_DEVELOPMENT_COMPARISON", "CANDIDATE_OVERLAY", "relative_delivery", "collapse_burden", "systemic_encephalopathy", "ConsciousnessOverlay")


@pytest.fixture(autouse=True)
def _real_environment(monkeypatch):
    for name, value in REAL.items():
        monkeypatch.setenv(name, value)
    for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(scope="module")
def turn():
    """A real GI encounter with one settled turn and its live shadow session."""
    import pilot_acceptance
    import runtime_shadow_evidence as ev
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = pilot_acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        encounter.order("Give 1 litre of normal saline over 15 minutes. Reassess in 10 minutes.")
    return {"arrival": arrival, "state": deepcopy(encounter.state), "session": encounter.shadow, "ran": [dict(order) for order in encounter.entries[-1]["orders"]]}


def _site(turn):
    site = ra.open_site(turn["arrival"], environ=REAL)
    assert site is not None and site.grant is not None
    return site


def _committed(turn):
    site = _site(turn)
    prepared = site.minute(turn["arrival"], deepcopy(turn["state"]), turn["session"], turn["ran"], "t0")
    assert prepared is not None, (site.halt_reason, site.records[-1:])
    return site, prepared


# -- attacks 1-7: the grant ---------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.strict_grant
def test_x1_a_grant_for_the_wrong_family_or_the_wrong_case_opens_no_site(turn, monkeypatch):
    forged = json.loads(json.dumps(dict(grants.GRANT), default=lambda value: list(value) if isinstance(value, tuple) else dict(value)))
    forged["cases"] = ["gi_bleed_72f"]
    forged["fingerprint"] = grants.fingerprint_of(forged)
    monkeypatch.setattr(grants, "REGISTERED_GRANTS", (forged,))
    assert ra.open_site(turn["arrival"], environ=REAL) is None, "the grant names the other case"
    forged["cases"], forged["family"] = list(grants.CASES), "acs"
    forged["fingerprint"] = grants.fingerprint_of(forged)
    monkeypatch.setattr(grants, "REGISTERED_GRANTS", (forged,))
    assert ra.open_site(turn["arrival"], environ=REAL) is None, "the grant names another family"


@pytest.mark.strict_grant
def test_x2_a_forged_or_consciousness_carrying_grant_opens_no_site_even_when_coherent(turn, monkeypatch):
    base = json.loads(json.dumps(dict(grants.GRANT), default=lambda value: list(value) if isinstance(value, tuple) else dict(value)))
    for edit in (lambda g: g.update(domain=["sbp", "dbp", "map", "mental_status"]), lambda g: g["consciousness_overlay"].update(authority=True),
                 lambda g: g.update(excluded_domains=["consciousness"]), lambda g: g.update(note="CONSCIOUSNESS_AUTHORITY_GRANTED")):
        forged = deepcopy(base)
        edit(forged)
        forged["fingerprint"] = grants.fingerprint_of(forged)
        monkeypatch.setattr(grants, "REGISTERED_GRANTS", (forged,))
        assert ra.open_site(turn["arrival"], environ=REAL) is None
        assert not ra.gate(turn["arrival"], environ=REAL, unsupported=()).conditions["explicit_development_grant"]


@pytest.mark.strict_grant
def test_x3_the_commit_re_evaluates_the_grant_so_no_pressure_commits_before_or_without_it(turn, monkeypatch):
    site = _site(turn)
    transaction = ra.AuthorityTransaction(minute=10, case_id=CASE, family="gi_bleed", domain=ra.AUTHORITY_DOMAIN, snapshot=ra.approved_snapshot("gi_pressure_committed"))
    transaction.capture(turn["arrival"]).compute({"sbp": 80, "dbp": 50, "map": 60}, ra.pressure_point(turn["arrival"]["observable"]))
    assert transaction.validate(replay_digest="a" * 64, expected_digest="a" * 64, unsupported=())
    monkeypatch.setattr(grants, "REGISTERED_GRANTS", ())
    with pytest.raises(ra.AuthorityRefused) as refused:
        transaction.commit({**deepcopy(turn["arrival"]), "sim_time": turn["arrival"]["sim_time"]}, environ=REAL)
    assert "the authority gate refuses at commit" in str(refused.value) and grants.UNKNOWN_GRANT in str(refused.value), str(refused.value)
    assert transaction.state == ra.ABORTED and transaction.committed == ()
    assert site.grant is not None and site.minutes_committed == ()


def test_x4_the_overlay_snapshot_is_not_a_pressure_snapshot_and_the_grant_does_not_calibrate_pressure_with_it(turn):
    site = _site(turn)
    assert site.snapshot_id == "gi_pressure_committed" and dict(site.grant)["consciousness_overlay"]["used_as_pressure_calibration"] is False
    bound = pair.bind()
    assert pair.bound_is_v1(bound)
    assert "GI_DEVELOPMENT_SNAPSHOT_V1" not in ra.APPROVED_SNAPSHOTS and ra.APPROVED_SNAPSHOTS["gi_pressure_committed"]["parameters"] == dict(site.snapshot["parameters"])


# -- attacks 17, 18, 22: the artifact ------------------------------------------------------------------------------------------------------------------------

def _tampered(artifact, edit, *, recompute=True):
    body = json.loads(ra.canonical(artifact))
    edit(body)
    body.pop("artifact_digest", None)
    return {**body, "artifact_digest": ra.digest_of(body)} if recompute else {**body, "artifact_digest": artifact["artifact_digest"]}


def test_x5_the_artifact_of_a_real_commit_verifies_and_replays_and_every_tamper_is_detected(turn):
    site, prepared = _committed(turn)
    artifact = site.artifact()
    assert ra.verify_artifact(artifact)["complete"] and ra.replay_site_artifact(artifact)["reproduces"]
    written = artifact["minutes"][0]["written_candidate"]
    assert (prepared["observable"]["sbp"], prepared["observable"]["dbp"]) == (written["sbp"], written["dbp"])
    attacks = {
        "a committed pressure edited (digest recomputed)": lambda b: b["minutes"][0]["written_candidate"].update(sbp=written["sbp"] + 7),
        "the common candidate edited (digest recomputed)": lambda b: b["minutes"][0]["common_candidate"].update(sbp=1.0),
        "an overlay row edited (digest recomputed)": lambda b: b["consciousness_overlay"]["turns"][0]["rows"][0].update(F=0.77),
        "the recorded boundary reading edited (digest recomputed)": lambda b: b["consciousness_overlay"]["turns"][0]["boundary"].update(first_established_minute=3),
        "the overlay's replay input swapped for an empty one": lambda b: b["consciousness_overlay"].update(replay_input=None),
        "the outcome rewritten to an abort": lambda b: b["minutes"][0].update(outcome=ra.ABORTED),
    }
    for name, edit in attacks.items():
        forged = _tampered(artifact, edit)
        verdict, replay = ra.verify_artifact(forged), ra.replay_site_artifact(forged)
        assert not (verdict["complete"] and replay["reproduces"]), name
    stale = _tampered(artifact, lambda b: b["minutes"][0]["written_candidate"].update(sbp=written["sbp"] + 7), recompute=False)
    assert not ra.verify_artifact(stale)["digest_matches"] and not ra.replay_site_artifact(stale)["reproduces"], "an edit without recomputing the digest"


def test_x6_an_artifact_that_claims_another_authority_mode_or_another_grant_or_consciousness_authority_is_not_complete(turn):
    site, _ = _committed(turn)
    artifact = site.artifact()
    wrong = {
        "authority mode": lambda b: b.update(authority_mode="PAIR_PRESSURE_CONSCIOUSNESS"),
        "another grant fingerprint": lambda b: b["grant"].update(fingerprint="f" * 64),
        "another grant id": lambda b: b["grant"].update(grant_id="GI_PRESSURE_DEVELOPMENT_AUTHORITY_GRANT_V2"),
        "a minute under another grant": lambda b: b["minutes"][0].update(grant_fingerprint="0" * 64),
        "a domain that includes consciousness": lambda b: b.update(domain=["sbp", "dbp", "map", "mental_status"]),
        "an overlay that claims authority": lambda b: b["consciousness_overlay"].update(authority=True),
        "an overlay that writes the live word": lambda b: b["consciousness_overlay"].update(writes_mental_status=True),
        "an overlay that was written into the encounter": lambda b: b["consciousness_overlay"].update(written_into_the_encounter=True),
        "the excluded domains emptied": lambda b: b.update(excluded_domains=[]),
    }
    for name, edit in wrong.items():
        verdict = ra.verify_artifact(_tampered(artifact, edit))
        assert not verdict["complete"], (name, verdict)


# -- attacks 14-16: nothing of the common consciousness reaches a reader -----------------------------------------------------------------------------------

def test_x7_the_overlay_never_touches_the_state_and_never_the_live_word(turn):
    site = _site(turn)
    before = ra.digest_of(turn["state"])
    prepared = site.minute(turn["arrival"], deepcopy(turn["state"]), turn["session"], turn["ran"], "t0")
    assert ra.digest_of(turn["state"]) == before, "the state the site was handed is untouched"
    assert prepared["observable"]["mental_status"] == turn["state"]["observable"]["mental_status"], "the legacy word is the legacy engine's"
    assert set(site._moved(turn["state"], prepared)) <= {"sbp", "dbp", "map"}
    assert view.OVERLAY_KEY not in prepared and not any("overlay" in str(key).lower() for key in prepared)
    assert not any(token in json.dumps(prepared, default=str) for token in OVERLAY_TOKENS)
    assert site.overlay.violations == []


def test_x8_no_module_outside_the_layer_reads_the_artifact_or_the_overlay_so_no_scoring_or_payload_can_see_it():
    layer = set(rs.LAYER_SOURCES)
    offenders = []
    for path in sorted(ROOT.glob("*.py")):
        if path.name.startswith(("test_", "regression_", "tools_")) or path.name in layer or path.name == "conftest.py":
            continue
        text = path.read_text(encoding="utf-8")
        for token in ("consciousness_overlay", "ConsciousnessOverlay", "OVERLAY_LABEL", "FACULTY_ACCEPTED_FOR_DEVELOPMENT_COMPARISON", "CANDIDATE_OVERLAY_NONAUTHORITATIVE"):
            if token in text:
                offenders.append((path.name, token))
    assert not offenders, offenders
    # the page only ASSIGNS the artifact to its session (never reads it) and only CLEARS the key on a reset; the scoring/payload modules never name it. (P3-248 review L5: the earlier predicate saw only
    # ``session_state["..."]`` subscripts; this one sees every way of naming the key: an attribute load, ``.get``/``getattr``/``in`` with the literal, and the layer's ``ARTIFACT_KEY`` constant.)
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    parent = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and node.value == "phase3_authority_artifact":
            raise AssertionError(f"the page names the artifact key as a literal at line {node.lineno}")
        if isinstance(node, ast.Attribute) and node.attr == "phase3_authority_artifact":
            assert isinstance(node.ctx, ast.Store), f"the page READS the artifact at line {node.lineno}"
        if isinstance(node, ast.Attribute) and node.attr == "ARTIFACT_KEY":
            loop = parent.get(parent.get(node))                         # the tuple of keys of the reset loop, and the ``for`` that owns it
            assert isinstance(parent.get(node), ast.Tuple) and isinstance(loop, ast.For), f"the page names ARTIFACT_KEY outside the reset loop at line {node.lineno}"
    for path in sorted(ROOT.glob("*.py")):
        if path.name.startswith("test_") or path.name in layer or path.name in ("app.py", "conftest.py"):
            continue
        text = path.read_text(encoding="utf-8")
        assert "phase3_authority_artifact" not in text and "ARTIFACT_KEY" not in text and "authority_status" not in text, path.name


def test_x9_the_overlay_can_be_handed_nothing_that_makes_it_write_and_a_failing_overlay_fails_the_boundary_closed(turn, monkeypatch):
    site = _site(turn)
    monkeypatch.setattr(pair.ConsciousnessOverlay, "turn", lambda self, after, session: (_ for _ in ()).throw(RuntimeError("the overlay broke")))
    assert site.minute(turn["arrival"], deepcopy(turn["state"]), turn["session"], turn["ran"], "t0") is None
    assert site.halted and site.halt_reason.startswith(ra.COLLAPSE_BOUNDARY_NOT_VERIFIABLE) and site.minutes_committed == ()


def test_x10_a_site_opened_with_a_test_only_point_carries_no_grant_and_behaves_as_before(turn, monkeypatch):
    """The seam is test-side only: a TEST-ONLY point (not the real registered one) yields a site with no grant, no overlay and no real-artifact fields."""
    point = {"id": "test_only_attack_point", "approved_by_faculty": True, "decision": "TEST ONLY: approves nothing", "runtime_parameter_snapshot_id": rs.PARAMETER_SNAPSHOT_ID,
             "parameters": {"test_only_placeholder": 1.0}}
    monkeypatch.setitem(ra._APPROVED_SNAPSHOT_POINTS, point["id"], point)
    site = ra.open_site(turn["arrival"], environ={**REAL, ra.SNAPSHOT_FLAG: point["id"]})
    assert site is not None and site.grant is None
    assert "authority_label" not in site.artifact() and ra.artifact_class(site.artifact()) == ra.HISTORICAL_PRESSURE_LABEL
