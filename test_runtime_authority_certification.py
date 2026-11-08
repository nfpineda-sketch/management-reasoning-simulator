"""P3-28: the final pre-authority certification. No real authority anywhere in this file.

Three things it adds to what the other authority files already prove: a negative control for every major
gate, so none of them is true by construction; the isolation of the scoring and rubric surfaces from the
authority path; and the two surviving snapshot candidates run through a real site, persisted, retrieved and
replayed from the store.

It also carries the E2E coverage manifest of the certification: the ten scenario classes the faculty
authorization lists, each tied to the test that proves it, so deleting or renaming one of those tests fails
this file instead of quietly reducing the certification.
"""
import ast
import dataclasses
import json
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_authority_store as store
import runtime_shadow as rs

ROOT = Path(__file__).resolve().parent
CASE = "gi_bleed_57m"
TEST_ONLY_SNAPSHOT = {"id": "test_only_certification_point",
                      "approved_by_faculty": True,
                      "decision": "TEST ONLY: exists inside one test session, approves nothing",
                      "runtime_parameter_snapshot_id": rs.PARAMETER_SNAPSHOT_ID,
                      "parameters": {"test_only_placeholder": 1.0}}
STORE_DIR = tempfile.mkdtemp(prefix="phase3-authority-certification-")
BEST = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY,
        ra.SNAPSHOT_FLAG: TEST_ONLY_SNAPSHOT["id"],
        ra.ENVIRONMENT_FLAG: "development",
        rs.FLAG: rs.MODE_SHADOW_COMPARE,
        store.STORE_FLAG: STORE_DIR}


@pytest.fixture(autouse=True)
def _pinned_store(monkeypatch):
    """No authority test may write into an ambient faculty store (P3-28 review)."""
    monkeypatch.setenv(store.STORE_FLAG, STORE_DIR)
#: The candidates P3-21 left standing. TEST-ONLY: nothing here approves a parameter point.
SURVIVING_CANDIDATES = {
    "gi_pressure_committed": {},
    "gi_pressure_preload_high": {"preload_curve_scale_ml": 1500.0, "arrival_preload_fraction": 0.7},
}
#: P3-28: the ten scenario classes of the certification, and the test that proves each one.
E2E_MANIFEST = {
    "A_successful_eligible_path": ("test_runtime_authority_site.py",
                                   "test_d17_the_application_store_hands_the_site_its_own_minute"),
    "B_unsupported_treatment_refusal": ("test_runtime_authority_battery.py",
                                        "test_g16_an_unsupported_action_in_the_turn_commits_nothing"),
    "C_failure_before_first_commit": ("test_runtime_authority_surface.py",
                                      "test_h1_a_failure_before_the_first_commit_halts_and_commits_nothing"),
    "D_failure_after_commits": ("test_runtime_authority_surface.py",
                                "test_h2_a_failure_after_a_commit_preserves_the_commit_and_halts"),
    "E_artifact_persistence": ("test_runtime_authority_surface.py",
                               "test_s6_every_outcome_is_persisted"),
    "F_faculty_failure_display": ("test_runtime_authority_surface.py",
                                  "test_s4_a_halted_experiment_is_drawn_with_its_exact_reason"),
    "G_retrieval_and_replay": ("test_runtime_authority_surface.py",
                               "test_s11_a_stored_artifact_is_retrieved_verified_and_replayed"),
    "H_resident_ui_isolation": ("test_runtime_authority_surface.py",
                                "test_h8_the_resident_sees_nothing_of_the_experiment"),
    "I_score_isolation": ("test_runtime_authority_certification.py",
                          "test_n2_the_authority_path_cannot_reach_the_scoring_surfaces"),
    "J_pilot_exclusion": ("test_runtime_authority_certification.py",
                          "test_n1_every_major_gate_has_a_negative_control"),
}


@pytest.fixture
def approved(monkeypatch, tmp_path):
    monkeypatch.setitem(ra._APPROVED_SNAPSHOT_POINTS, TEST_ONLY_SNAPSHOT["id"], TEST_ONLY_SNAPSHOT)
    for name, value in BEST.items():
        monkeypatch.setenv(name, value)
    for name in ra.PILOT_FLAGS + ra.PILOT_REQUIRED_ON:
        monkeypatch.delenv(name, raising=False)
    directory = tmp_path / "phase3_authority"
    monkeypatch.setenv(store.STORE_FLAG, str(directory))
    return {"environ": {**BEST, store.STORE_FLAG: str(directory)}, "store": directory}


@pytest.fixture(scope="module")
def gi_state():
    import pilot_acceptance
    return deepcopy(pilot_acceptance.Encounter(CASE).state)


# -- P3-28-4: a negative control for every major gate --------------------------------------------------

@pytest.mark.parametrize("condition,change", [
    ("authority_flag", {ra.AUTHORITY_FLAG: "off"}),
    ("approved_snapshot", {ra.SNAPSHOT_FLAG: "a name nobody approved"}),
    ("environment", {ra.ENVIRONMENT_FLAG: "production"}),
    ("no_pilot", {ra.PILOT_FLAGS[0]: "1"}),
    ("no_pilot_by_freeze", {"MRS_OFFLINE_CASES": "1", "MRS_IMAGE_REQUIRE_REVIEW": "on"}),
    ("family_and_case", "family"),
    ("family_and_case", "case"),
    ("authority_domain", "domain"),
    ("no_unsupported_action", "unsupported"),
    ("phase2_digest", "digest"),
    ("layer_version", "layer"),
])
def test_n1_every_major_gate_has_a_negative_control(gi_state, approved, monkeypatch, condition, change):
    """Each gate must be provably able to fail: none of the nine is true by construction."""
    environ = dict(approved["environ"])
    state, domain, unsupported = deepcopy(gi_state), ra.AUTHORITY_DOMAIN, ()
    name = condition.split("_by_")[0]
    # The clean reading is taken BEFORE the control is applied, so a control that patches the module
    # (the digest, the layer version) does not also change what it is compared against.
    clean = ra.gate(deepcopy(gi_state), environ=dict(approved["environ"]), unsupported=())
    if isinstance(change, dict):
        environ.update(change)
    elif change == "family":
        state["engine_family"] = "acs"
    elif change == "case":
        state["encounter_spec"] = {**dict(state.get("encounter_spec") or {}),
                                   "variant_id": "pneumonia_83m"}
    elif change == "domain":
        domain = ("sbp",)
    elif change == "unsupported":
        unsupported = ("norepinephrine",)
    elif change == "digest":
        import runtime_shadow_evidence as ev
        monkeypatch.setattr(ev, "phase2_digest_now", lambda: "a different digest")
    elif change == "layer":
        monkeypatch.setattr(rs, "MODULE_VERSION", "P9-99")
    decision = ra.gate(state, environ=environ, domain=domain, unsupported=unsupported)
    assert not decision.granted
    assert decision.conditions[name] is False, (condition, decision.to_dict())
    assert decision.reasons, condition
    # And without the control the same condition holds, so the control is what failed it.
    if name != "approved_snapshot":
        assert clean.conditions[name] is True, (condition, clean.to_dict())
    # A control that lives in the state or the environment also closes the site. The domain and the
    # declared action list are arguments of a minute, not of the arrival, so they are not asserted here:
    # the battery's failure stress is what proves those two close a minute.
    if change not in ("domain", "unsupported"):
        assert ra.open_site(state, environ=environ) is None, condition
        assert ra.site_for(state, {}, environ=environ) is None, condition


def test_n1b_with_every_control_removed_only_the_snapshot_can_hold_it(gi_state, approved):
    """The gate is not a wall of impossible conditions: eight of nine hold in a faculty environment."""
    decision = ra.gate(deepcopy(gi_state), environ=dict(approved["environ"]), unsupported=())
    failing = [name for name, ok in decision.conditions.items() if not ok]
    assert failing == [], failing
    assert decision.granted, "with a test-only approval registered, the gate can grant -- by injection"
    # And without the injection, the one condition nothing in the repository can satisfy is named.
    with pytest.MonkeyPatch.context() as patch:
        patch.delitem(ra._APPROVED_SNAPSHOT_POINTS, TEST_ONLY_SNAPSHOT["id"])
        again = ra.gate(deepcopy(gi_state), environ=dict(approved["environ"]), unsupported=())
        assert [name for name, ok in again.conditions.items() if not ok] == ["approved_snapshot"]


# -- P3-28 class I: the scoring surfaces -------------------------------------------------------------

def test_n2_the_authority_path_cannot_reach_the_scoring_surfaces():
    """Nothing in the layer imports or names a scoring, rubric or assessment surface."""
    forbidden = {"rubric_store", "rubric_portal", "case_assessment", "progress_store", "faculty_report",
                 "record_findings", "faculty_analysis", "faculty_analysis_store", "account_store"}

    def used(path):
        """Modules a file imports, and names it calls through -- by AST, not by substring."""
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)
                 for alias in node.names}
        names |= {str(node.module).split(".")[0] for node in ast.walk(tree)
                  if isinstance(node, ast.ImportFrom) and node.module}
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                names.add(node.value.id)
        return names

    for name in rs.LAYER_SOURCES:
        touched = used(ROOT / name) & forbidden
        assert not touched, (name, sorted(touched))
    # And the store's own directory is the only thing it writes.
    store_source = (ROOT / "runtime_authority_store.py").read_text(encoding="utf-8")
    writers = [line.strip() for line in store_source.splitlines()
               if "write_text" in line or "mkdir" in line]
    assert len(writers) == 2, writers
    assert all("path." in line or "directory." in line for line in writers), writers


def test_n3_an_authority_minute_changes_no_scoring_or_rubric_data(approved):
    """A committed minute moves the pressure domain and nothing a score is computed from."""
    import pilot_acceptance
    import runtime_shadow_evidence as ev
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = pilot_acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        site = ra.open_site(arrival, environ=approved["environ"])
        encounter.order("Give 1 litre of normal saline over 15 minutes. Reassess in 10 minutes.")
        ran = [dict(order) for order in encounter.entries[-1]["orders"]]
        before = deepcopy(encounter.state)
        prepared = site.minute(None, deepcopy(encounter.state), encounter.shadow, ran, "t0")
    assert prepared is not None
    # Everything a score or a rubric reads is byte-identical; only the pressure domain moved.
    moved = {key for key in set(before) | set(prepared)
             if key != "observable" and ra.canonical(before.get(key)) != ra.canonical(prepared.get(key))}
    assert moved == set(), moved
    one, two = dict(before["observable"]), dict(prepared["observable"])
    changed = {key for key in set(one) | set(two) if one.get(key) != two.get(key)}
    assert changed <= {"sbp", "dbp", "map"}, changed
    for key in ("treatments", "hidden", "family_state", "sim_time", "order_ledger"):
        if key in before:
            assert ra.canonical(before[key]) == ra.canonical(prepared[key]), key


# -- P3-28-2: the surviving candidates, through a real site, persisted and replayed --------------------

@pytest.mark.parametrize("candidate", sorted(SURVIVING_CANDIDATES))
def test_n4_each_surviving_candidate_runs_persists_and_replays(approved, candidate):
    """TEST-ONLY candidates: the profile is swapped on the shadow runner, so the core really runs it."""
    import pilot_acceptance
    import runtime_shadow_evidence as ev
    values = SURVIVING_CANDIDATES[candidate]
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = pilot_acceptance.Encounter(CASE)
        arrival = deepcopy(encounter.state)
        site = ra.open_site(arrival, environ=approved["environ"])
        assert site is not None
        if values:
            encounter.shadow.runner.profile = dataclasses.replace(encounter.shadow.runner.profile,
                                                                  **values)
        encounter.order("Give 1 litre of normal saline over 15 minutes. Reassess in 10 minutes.")
        ran = [dict(order) for order in encounter.entries[-1]["orders"]]
        prepared = site.minute(None, deepcopy(encounter.state), encounter.shadow, ran, "t0")
    assert prepared is not None, site.records
    record = dict(site.records[-1])
    assert record["outcome"] == ra.COMMITTED and sorted(record["committed"]) == ["dbp", "map", "sbp"]
    # The replay digest is computed from the artifact, which carries the candidate's own profile.
    assert record["replay_digest"] == record["candidate_digest"]
    assert dict(record["replay_input"])["scenario"]["profile"]["preload_curve_scale_ml"] == (
        values.get("preload_curve_scale_ml", 833.3333333333334))
    identifier = dict(site.stored)["artifact_id"]
    assert store.verify(identifier, environ=approved["environ"])["verified"]
    replayed = store.replay(identifier, environ=approved["environ"])
    assert replayed["reproduces"] and replayed["compared"] == 1
    # And nothing approved anything: the candidate is a profile, not a snapshot.
    assert ra._APPROVED_SNAPSHOT_POINTS[TEST_ONLY_SNAPSHOT["id"]]["parameters"] == {
        "test_only_placeholder": 1.0}


# -- P3-28-5 and the manifest --------------------------------------------------------------------------

def test_n5_no_production_configuration_reaches_authority(gi_state):
    assert ra.APPROVED_SNAPSHOTS == {} and ra._APPROVED_SNAPSHOT_POINTS == {}
    assert ra.unreachable_because()
    for environ in ({}, BEST, {**BEST, ra.ENVIRONMENT_FLAG: "faculty"},
                    {**BEST, store.STORE_FLAG: "/tmp/does-not-matter"}):
        assert ra.site_for(deepcopy(gi_state), {}, environ=environ) is None, environ
        assert ra.mode(deepcopy(gi_state), environ=environ, unsupported=()) != \
            ra.MODE_LIMITED_COMMON_AUTHORITY
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    assert not store.configured(environ={})


def test_n6_the_certification_covers_every_declared_scenario_class():
    """The manifest is checked, not asserted: every named test must exist in its named file."""
    for label, (filename, test) in sorted(E2E_MANIFEST.items()):
        path = ROOT / filename
        assert path.exists(), filename
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        assert test in names, (label, filename, test)
    assert len(E2E_MANIFEST) == 10
