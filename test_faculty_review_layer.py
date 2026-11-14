"""P3-280 to P3-285, layer level: the faculty development review MODE, its fail-closed configuration, the SINGLE-PROCESS enforcement, the scripted scenario set, the surface after a halt and the feedback schema.

Fast tests with no page: the page-level proofs (entry, launcher, panel, bundle, feedback, halt, exit, ordinary-user negatives) are in ``test_phase3_faculty_review_page``.
"""
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_authority_session as se
import runtime_authority_store as ras
import runtime_faculty_bundle as bundles
import runtime_faculty_review as fr
import runtime_pressure_grant as grants
import runtime_shadow as rs

ROOT = Path(__file__).resolve().parent


@pytest.fixture
def store_dir(tmp_path):
    yield tmp_path / "store"
    fr.release_for_tests()


def _env(store_dir, **override):
    env = {fr.FLAG: fr.MODE_ON, rs.FLAG: rs.MODE_SHADOW_COMPARE, ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.SNAPSHOT_FLAG: grants.PRESSURE_SNAPSHOT_ID,
           ra.ENVIRONMENT_FLAG: "development", fr.OFFLINE_FLAG: "1", ras.STORE_FLAG: str(store_dir)}
    env.update(override)
    return {key: value for key, value in env.items() if value is not None}


def _evaluate(store_dir, role="faculty", accounts=True, on_cloud=False, **override):
    return fr.evaluate(_env(store_dir, **override), accounts=accounts, role=role, on_cloud=on_cloud)


# -- the mode is explicit, and complete or unavailable ----------------------------------------------------------------------------------------------------------

def test_f1_not_named_means_nothing_is_read_and_the_ordinary_development_path_is_untouched():
    class Counting(dict):
        reads = 0

        def get(self, key, default=None):
            Counting.reads += 1
            return super().get(key, default)

    environ = Counting({ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY})
    decision = fr.evaluate(environ, accounts=True, role="faculty")
    assert decision["requested"] is False and decision["enabled"] is False and decision["conditions"] == {}
    assert Counting.reads == 1, "one lookup when the review mode is not named"
    assert fr.authority_available({}, {}) == (True, ""), "an ordinary development configuration is not asked anything by the review mode"
    assert fr.asked({}) is False and fr.asked({fr.FLAG: "  "}) is False


def test_f2_a_complete_configuration_for_a_faculty_account_is_enabled_and_names_what_it_enables(store_dir):
    decision = _evaluate(store_dir)
    assert decision["enabled"] is True and decision["problems"] == [] and decision["access"] == "FACULTY_REVIEWER" and all(decision["conditions"].values())
    assert set(decision["conditions"]) == set(fr.CONDITIONS) and decision["single_process"]["held"] is True
    assert (decision["authority_mode"], decision["grant_id"], decision["environment"]) == ("PRESSURE_ONLY", grants.GRANT_ID, "development")
    assert decision["allowlist"] == ["gi_bleed_57m", "gi_bleed_72f"]
    assert fr.review_root(_env(store_dir)) == store_dir / fr.REVIEW_DIRNAME


@pytest.mark.parametrize("role,access", (("admin", "FACULTY_REVIEWER"), ("faculty", "FACULTY_REVIEWER"), ("resident", "NOT_A_FACULTY_ACCOUNT"), (None, "NOT_A_FACULTY_ACCOUNT"), ("", "NOT_A_FACULTY_ACCOUNT")))
def test_f3_only_faculty_and_administrator_accounts_get_the_review_mode(store_dir, role, access):
    decision = _evaluate(store_dir, role=role)
    assert decision["access"] == access and decision["enabled"] is (access == "FACULTY_REVIEWER")
    assert decision["configuration_complete"] is True, "the deployment is complete; only the account decides"


MISSING = (
    ("misspelled_flag", {fr.FLAG: "faculty_review"}, "process_flag"),
    ("wrong_flag_case", {fr.FLAG: "yes"}, "process_flag"),
    ("shadow_off", {rs.FLAG: None}, "shadow"),
    ("authority_off", {ra.AUTHORITY_FLAG: None}, "authority_flag"),
    ("authority_legacy", {ra.AUTHORITY_FLAG: "legacy"}, "authority_flag"),
    ("snapshot_missing", {ra.SNAPSHOT_FLAG: None}, "snapshot"),
    ("snapshot_other", {ra.SNAPSHOT_FLAG: "gi_pressure_other"}, "snapshot"),
    ("production_environment", {ra.ENVIRONMENT_FLAG: "production"}, "development_environment"),
    ("faculty_environment_label", {ra.ENVIRONMENT_FLAG: "faculty"}, "development_environment"),
    ("paid_generation_possible", {fr.OFFLINE_FLAG: None}, "offline_cases"),
    ("store_missing", {ras.STORE_FLAG: None}, "store"),
    ("store_relative", {ras.STORE_FLAG: "relative/dir"}, "store"),
    ("store_inside_the_repository", {ras.STORE_FLAG: str(ROOT / "docs")}, "store"),
)


@pytest.mark.parametrize("name,override,condition", MISSING, ids=[row[0] for row in MISSING])
def test_f4_every_missing_or_partial_piece_makes_the_authority_unavailable_never_partially_enabled(store_dir, name, override, condition):
    decision = _evaluate(store_dir, **override)
    assert decision["enabled"] is False and decision["conditions"][condition] is False, decision["conditions"]
    assert any(problem.startswith(condition + ":") for problem in decision["problems"])
    store = {}
    fr.publish(store, decision)
    available, why = fr.authority_available(store, _env(store_dir, **override))
    assert available is False and why.startswith("FACULTY_REVIEW_CONFIGURATION_INCOMPLETE"), why
    assert decision["single_process"].get("held") is not True or condition == "single_process", "an incomplete deployment must not hold the store"
    assert not (store_dir / fr.REVIEW_DIRNAME / "single_process.lock").exists(), "no lock file for a deployment that is not complete"


def test_f5_account_conditions_each_refuse(store_dir):
    assert _evaluate(store_dir, accounts=False)["conditions"]["accounts"] is False, "faculty-only cannot be enforced behind a shared password"
    assert _evaluate(store_dir, on_cloud=True)["conditions"]["not_streamlit_cloud"] is False
    pilot = _evaluate(store_dir, **{name: "1" for name in ra.PILOT_FLAGS[:1]})
    assert pilot["conditions"]["no_pilot"] is False and pilot["enabled"] is False, "the first pilot's configuration can never be a review environment"


def test_f6_a_flag_named_in_a_deployment_secret_is_not_honoured(store_dir, monkeypatch):
    for name in (fr.FLAG, ra.AUTHORITY_FLAG, ra.SNAPSHOT_FLAG, ra.ENVIRONMENT_FLAG, ras.STORE_FLAG, fr.OFFLINE_FLAG):
        monkeypatch.setattr(rs, "_named_in_secrets", lambda key, wanted=name: key == wanted)
        decision = _evaluate(store_dir)
        assert decision["enabled"] is False, f"{name} in a Secret must not enable the review mode"
        fr.release_for_tests()


def test_f7_an_unreadable_evaluation_fails_closed(store_dir, monkeypatch):
    monkeypatch.setattr(fr, "review_root", lambda environ=None: (_ for _ in ()).throw(RuntimeError("boom")))
    decision = _evaluate(store_dir)
    assert decision["enabled"] is False and decision["requested"] is True and decision["access"] == "CONFIGURATION_INCOMPLETE"
    assert fr.authority_available({}, _env(store_dir)) == (False, "FACULTY_REVIEW_CONFIGURATION_INCOMPLETE: the faculty review configuration was not evaluated for this session")
    assert fr.authority_available({fr.SESSION_KEY: "garbage"}, _env(store_dir))[0] is False
    assert fr.authority_available({fr.SESSION_KEY: {"enabled": "yes", "requested": True}}, _env(store_dir))[0] is False, "only the boolean True enables"


# -- P3-280A: the single process --------------------------------------------------------------------------------------------------------------------------------------

def _second_process_holds(directory) -> str:
    code = ("import sys; sys.path.insert(0, %r); import runtime_faculty_review as fr; from pathlib import Path; "
            "r = fr.acquire_single_process_lock(Path(%r)); print(r['held'], '|', r['why'])" % (str(ROOT), str(directory)))
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120).stdout.strip().splitlines()
    return out[-1]


def test_f8_a_second_process_cannot_take_the_lock_and_cannot_enable_the_review_mode(store_dir):
    decision = _evaluate(store_dir)
    assert decision["enabled"] is True
    directory = store_dir / fr.REVIEW_DIRNAME
    assert _second_process_holds(directory).startswith("False | another process holds the faculty review lock"), "one review process per store"
    # and through the whole decision: a second process that names the same store is unavailable
    code = ("import sys, os; sys.path.insert(0, %r); import runtime_faculty_review as fr; d = fr.evaluate(dict(os.environ), accounts=True, role='faculty'); "
            "print(d['enabled'], '|', [p.split(':')[0] for p in d['problems']])" % str(ROOT))
    env = {**os.environ, **_env(store_dir)}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120, env=env).stdout.strip().splitlines()[-1]
    assert out == "False | ['single_process']", out
    # the holder keeps it, and a repeat call in the holder is idempotent
    assert fr.acquire_single_process_lock(directory)["held"] is True


def test_f9_a_forked_child_shares_the_descriptor_but_is_not_the_holder(store_dir):
    directory = store_dir / fr.REVIEW_DIRNAME
    assert fr.acquire_single_process_lock(directory)["held"] is True
    read, write = os.pipe()
    pid = os.fork()
    if pid == 0:                                       # the child
        try:
            os.close(read)
            held = fr.acquire_single_process_lock(directory)["held"]
            os.write(write, b"1" if held else b"0")
        finally:
            os._exit(0)
    os.close(write)
    answer = os.read(read, 1)
    os.waitpid(pid, 0)
    assert answer == b"0", "an inherited lock must not make a child a second holder"
    assert fr.acquire_single_process_lock(directory)["held"] is True, "and the parent still holds it"


def test_f10_a_network_filesystem_or_a_lock_that_cannot_be_taken_fails_closed(store_dir, monkeypatch):
    directory = store_dir / fr.REVIEW_DIRNAME
    monkeypatch.setattr(fr, "filesystem_kind", lambda path: (fr.FS_NETWORK, "nfs4"))
    refused = fr.acquire_single_process_lock(directory)
    assert refused["held"] is False and "network filesystem" in refused["why"]
    monkeypatch.undo()
    import fcntl
    monkeypatch.setattr(fcntl, "flock", lambda fd, how: (_ for _ in ()).throw(OSError("unsupported")))
    broken = fr.acquire_single_process_lock(directory)
    assert broken["held"] is False and ("fails closed" in broken["why"] or "another process holds" in broken["why"]), broken


def test_f11_an_unknown_filesystem_is_reported_as_not_verifiable_and_never_as_verified(store_dir, monkeypatch):
    monkeypatch.setattr(fr, "filesystem_kind", lambda path: (fr.FS_UNKNOWN, ""))
    result = fr.acquire_single_process_lock(store_dir / fr.REVIEW_DIRNAME)
    assert result["held"] is True and result["filesystem"] == "UNKNOWN_NOT_VERIFIABLE", "the lock works; what it cannot prove is stated, not hidden"
    assert fr.filesystem_kind(Path(ROOT))[0] in (fr.FS_LOCAL, fr.FS_UNKNOWN)


# -- P3-285: the scripted review set ----------------------------------------------------------------------------------------------------------------------------------

def test_f12_the_review_set_is_small_allowlisted_explained_and_matches_the_certified_series():
    assert fr.scenario_problems() == [] and len(fr.SCENARIOS) == 7
    assert {item["case_id"] for item in fr.SCENARIOS} == {"gi_bleed_57m", "gi_bleed_72f"} == set(fr.ALLOWLIST) == set(grants.CASES)
    series = json.loads((ROOT / "docs" / "revision" / "PHASE3_PRESSURE_AUTHORITY_SERIES.json").read_text(encoding="utf-8"))
    rows = {(row["case"], row["scenario"]): row for row in series["runs"]}
    meaning = {"HALTED_AT_COLLAPSE_BOUNDARY": ("HALTED", "COLLAPSE_BOUNDARY_REACHED"), "HALTED_BY_UNSUPPORTED_ACTION": ("HALTED", "UNSUPPORTED_AUTHORITY_ACTION"), "ACTIVE_TO_THE_END": ("ACTIVE", "")}
    for item in fr.SCENARIOS:
        row = rows[(item["case_id"], item["series"])]
        assert (row["state"], row["halt_kind"] or "") == meaning[item["expected"]], item["id"]
    assert sum(item["expected"].startswith("HALTED") for item in fr.SCENARIOS) == 3, "two collapse-boundary halts and one operational halt"


def test_f13_a_scenario_set_that_leaves_the_allowlist_or_the_size_is_refused(monkeypatch):
    monkeypatch.setattr(fr, "SCENARIOS", fr.SCENARIOS + ({"id": "FR-X", "case_id": "pe_case", "steps": (), "reason": "a" * 50, "expected": "ACTIVE_TO_THE_END"},))
    assert any("outside the allowlist" in problem for problem in fr.scenario_problems()) and any("5 to 7" in problem for problem in fr.scenario_problems())


# -- FD-FAC-07/08/09: the surface after a halt ------------------------------------------------------------------------------------------------------------------------

def test_f14_after_a_halt_only_reading_and_leaving_survive_and_the_unjudged_operations_are_named_not_implemented():
    surface = fr.surface_after_halt()
    assert set(fr.EXCLUDED_AFTER_HALT) == {"ecg_acquisition", "cancel_pending_orders", "retrospective_explanation"} <= set(surface["blocked"])
    assert surface["excluded_unjudged"] == list(fr.EXCLUDED_AFTER_HALT) and "Excluded" in surface["excluded_reason"]
    assert surface["resolution"] == "ABANDON_EXPERIMENT" and list(se.OPERATOR_RESOLUTIONS) == ["ABANDON_EXPERIMENT"]
    assert set(surface["unsupported_resolutions"]) == {"RESUME", "ROLLBACK", "RESTART_FROM_PREAUTHORITY_SNAPSHOT"}
    assert {"history_question", "order_submission", "examination", "held_order_release", "complete_encounter", "finish_encounter", "clinical_time"} <= set(surface["blocked"])
    assert {"abandon_experiment", "return_to_dashboard", "reset_scenario", "view_authority_status", "render_room"} <= set(surface["allowed"])
    assert not (set(surface["allowed"]) & set(surface["blocked"]))
    assert surface["notice"] == "DEVELOPMENT AUTHORITY EXPERIMENT HALTED"
    words = (se.NOTICE_HEADLINE + " " + se.NOTICE_BODY).lower()
    for forbidden in ("death", "died", "dead", "arrest", "terminal", "moribund", "cardiac arrest", "expired"):
        assert forbidden not in words, forbidden


# -- P3-284: the feedback schema --------------------------------------------------------------------------------------------------------------------------------------

def test_f15_the_schema_asks_the_ten_educational_questions_and_the_four_overall_answers():
    schema = bundles.SCHEMA
    texts = [question["text"] for question in schema["questions"]]
    assert len(texts) == 10 and [q["id"] for q in schema["questions"]] == [f"Q{i}" for i in range(1, 11)]
    assert texts[0].startswith("Did pressure evolve in a clinically coherent direction")
    assert "too early, appropriately or too late" in texts[1] and "response to treatment" in texts[2] and "magnitude" in texts[3] and "mislead a resident" in texts[4]
    assert "halt occur at an understandable point" in texts[5] and "educational confusion" in texts[6] and "consciousness comparison" in texts[7] and "contradiction between pressure, consciousness and management" in texts[8]
    assert schema["overall_choices"] == ["ACCEPT", "ACCEPT_WITH_LIMITATION", "RECALIBRATE", "REJECT"]
    assert set(schema["fields"]) >= {"reviewer_role", "case_id", "scenario_id", "bundle_id", "comments"} and "synthetic" in schema["notice"]
    assert not [text for text in texts if any(word in text.lower() for word in ("function", "module", "digest", "flag", "code", "latency"))], "educational questions only, never implementation ones"
    stages = {q["id"]: q["stage"] for q in schema["questions"]}
    assert [i for i in range(1, 6) if stages[f"Q{i}"] != bundles.STAGE_BLINDED] == [], "Q1 to Q5 are judged on the authority view alone"
    assert stages["Q8"] == stages["Q9"] == bundles.STAGE_COMPARATOR, "the comparator questions come after the comparator is shown"


def test_f16_the_review_layer_adds_no_authority_scope_no_consciousness_and_touches_no_scoring_or_pilot():
    assert grants.GRANT["authority_mode"] == "PRESSURE_ONLY" and grants.ENVIRONMENTS == ("development",) and set(grants.DOMAIN) == {"sbp", "dbp", "map"}
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False and sorted(ra.APPROVED_SNAPSHOTS) == ["gi_pressure_committed"]
    for name in ("rubric.py", "rubric_store.py", "rubric_analysis.py", "progress_store.py", "management_trace_store.py", "pilot_freeze.py", "pilot_acceptance.py", "tools_pilot_preflight.py",
                 "family_engine.py", "scoring.py"):
        path = ROOT / name
        if path.exists():
            text = path.read_text(encoding="utf-8")
            assert "faculty_review" not in text and "runtime_faculty" not in text, f"{name} must not know the review environment"
    for name in ("runtime_faculty_review.py", "runtime_faculty_bundle.py", "faculty_review_ui.py"):
        tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
        imports = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        imports |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        assert not ({"app", "family_engine", "clinical_core", "curriculum", "rubric"} & imports), (name, imports)
        if name == "faculty_review_ui.py":
            assert not [item for item in imports if item.startswith("runtime_")], f"the page module imports nothing of the Phase-3 layer: it is handed the layer ({imports})"
        else:
            assert "streamlit" not in imports, f"{name} is a layer module and draws nothing"


# -- the launcher's own defence: whatever started must be one of the two allowlisted cases ------------------------------------------------------------------------------

class _FakeSt:
    """The few Streamlit calls the launcher makes, recorded. ``begin`` is the only button pressed."""

    def __init__(self):
        self.session_state, self.errors, self.reruns = {}, [], 0

    def __getattr__(self, name):
        return lambda *args, **kwargs: None

    def button(self, label, **kwargs):
        return label == "Begin review encounter"

    def selectbox(self, label, options, **kwargs):
        return "FR-B"

    def expander(self, *args, **kwargs):
        import contextlib
        return contextlib.nullcontext()

    def error(self, text):
        self.errors.append(text)

    def rerun(self):
        self.reruns += 1


def _launch(case_id):
    from types import SimpleNamespace
    import faculty_review_ui as ui
    st = _FakeSt()
    resets = []

    class Store:
        def list_attempts(self, token):
            return []

    def start(context, initial, reset, **kwargs):
        st.session_state["state"] = {"encounter_spec": {"clinical_case": {"id": case_id}}}
        st.session_state["started"] = True
        assert kwargs == {"faculty_choice": ui.CHALLENGE_ID, "pinned_variant": "gi_bleed_57m", "review_scenario": "FR-B"}

    ui.launcher(st, SimpleNamespace(review=fr, bundles=bundles), {"store": Store(), "token": "t", "user": {"id": "u"}}, {}, lambda: resets.append(1), start)
    return st, resets


def test_f17_the_launcher_resets_and_refuses_a_started_case_that_is_not_allowlisted_and_accepts_one_that_is():
    st, resets = _launch("pneumonia_case")
    assert resets == [1] and st.reruns == 0 and st.errors == ["The review environment only runs the two allowlisted GI cases."]
    st, resets = _launch("gi_bleed_57m")
    assert resets == [] and st.reruns == 1 and st.errors == []
    assert fr.case_of_state({"encounter_spec": {"clinical_case": {"id": "gi_bleed_72f"}}}) == "gi_bleed_72f" and fr.case_of_state(None) == "" and fr.case_of_state({"encounter_spec": 3}) == ""


# -- P3-288 (independent review): the repairs, each with the attack that found it ---------------------------------------------------------------------------------------

def _hold_in_another_process(directory):
    """A second process that takes the lock and KEEPS it until its stdin closes. Returns (process, first line it printed)."""
    code = ("import sys; sys.path.insert(0, %r); import runtime_faculty_review as fr; from pathlib import Path; "
            "r = fr.acquire_single_process_lock(Path(%r)); print(r['held'], flush=True); sys.stdin.readline()" % (str(ROOT), str(directory)))
    process = subprocess.Popen([sys.executable, "-c", code], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    return process, process.stdout.readline().strip()


def _release(process):
    process.stdin.close()
    process.wait(timeout=60)


def test_f18_the_gi_family_must_be_live_in_the_shadow_comparison(store_dir):
    off = _evaluate(store_dir, **{rs.FAMILIES_FLAG: "opioid"})
    assert off["enabled"] is False and off["conditions"]["shadow_family"] is False and any(problem.startswith("shadow_family:") for problem in off["problems"])
    assert off["single_process"]["held"] is False, "a refused configuration holds no store"
    fr.release_for_tests()
    on = _evaluate(store_dir, **{rs.FAMILIES_FLAG: "gi_bleed"})
    assert on["enabled"] is True and on["conditions"]["shadow_family"] is True and len(fr.CONDITIONS) == 14


def test_f19_the_environment_is_read_again_whenever_the_authority_asks(store_dir):
    published = {fr.SESSION_KEY: _evaluate(store_dir)}
    assert published[fr.SESSION_KEY]["enabled"] is True
    assert fr.authority_available(published, _env(store_dir)) == (True, "")
    for name, override in (("snapshot", {ra.SNAPSHOT_FLAG: "another"}), ("environment", {ra.ENVIRONMENT_FLAG: "production"}), ("families", {rs.FAMILIES_FLAG: "opioid"}),
                           ("offline", {fr.OFFLINE_FLAG: None}), ("shadow", {rs.FLAG: None}), ("authority", {ra.AUTHORITY_FLAG: None})):
        available, why = fr.authority_available(published, _env(store_dir, **override))
        assert available is False and "no longer holds" in why, (name, why)
    # the review flag itself removed after the session was a review session: not an ordinary development encounter
    gone = {key: value for key, value in _env(store_dir).items() if key != fr.FLAG}
    available, why = fr.authority_available(published, gone)
    assert available is False and "no longer set" in why
    assert fr.authority_available({}, gone) == (True, ""), "a session that never was a review session is not refused for the flag being absent"
    assert fr.authority_available({fr.SESSION_KEY: {"enabled": True, "requested": True}}, gone)[0] is False, "a forged enabled decision cannot outlive the flag"


def test_f20_a_lock_file_deleted_under_a_running_review_is_detected_and_not_held_when_another_process_took_it(store_dir):
    directory = store_dir / fr.REVIEW_DIRNAME
    assert fr.acquire_single_process_lock(directory)["held"] is True
    (directory / "single_process.lock").unlink()
    other, first = _hold_in_another_process(directory)
    try:
        assert first == "True", "the attack of the review: with the file gone a second process can take a lock"
        again = fr.acquire_single_process_lock(directory)
        assert again["held"] is False and "another process holds" in again["why"], "the first process no longer believes it holds a lock on a file nobody can see"
    finally:
        _release(other)
    assert fr.acquire_single_process_lock(directory)["held"] is True, "and takes it again once the other one has gone"


def test_f21_a_review_directory_moved_under_a_running_review_is_detected_the_same_way(store_dir):
    directory = store_dir / fr.REVIEW_DIRNAME
    assert fr.acquire_single_process_lock(directory)["held"] is True
    os.rename(directory, store_dir / "moved_away")
    other, first = _hold_in_another_process(directory)
    try:
        assert first == "True"
        assert fr.acquire_single_process_lock(directory)["held"] is False
    finally:
        _release(other)


def test_f22_concurrent_page_runs_of_one_process_are_all_the_holder(store_dir):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as pool:
        decisions = list(pool.map(lambda _: _evaluate(store_dir), range(16)))
    assert all(item["enabled"] is True for item in decisions), [item["problems"] for item in decisions if not item["enabled"]][:2]


def test_f23_only_vetted_local_filesystems_are_trusted_with_the_lock(store_dir, monkeypatch):
    base = "x /data {kind} rw 0 0\nr / ext4 rw 0 0\n"
    for kind in ("ext4", "xfs", "overlay", "tmpfs", "btrfs"):
        assert fr.filesystem_kind(Path("/data/store"), base.format(kind=kind))[0] == fr.FS_LOCAL, kind
    for kind in ("nfs4", "cifs", "virtiofs", "fuse.rclone", "lustre", "gpfs", "cephfs", "vboxsf", "9p"):
        assert fr.filesystem_kind(Path("/data/store"), base.format(kind=kind))[0] == fr.FS_NETWORK, kind
    assert fr.filesystem_kind(Path("/data/store"), base.format(kind="weirdfs"))[0] == fr.FS_UNVERIFIED, "a type nobody vetted is refused, not assumed local"
    monkeypatch.setattr(fr, "filesystem_kind", lambda path, mounts=None: (fr.FS_UNVERIFIED, "weirdfs"))
    result = fr.acquire_single_process_lock(store_dir / fr.REVIEW_DIRNAME)
    assert result["held"] is False and "not on the local list" in result["why"]


@pytest.mark.parametrize("name,kwargs,override", (("shared_password", {"accounts": False}, {}), ("cloud", {"on_cloud": True}, {}), ("pilot", {}, {ra.PILOT_FLAGS[0]: "1"}),
                                                 ("flag_misspelled", {}, {fr.FLAG: "faculty_review"}), ("shadow_off", {}, {rs.FLAG: None})))
def test_f24_a_refused_configuration_writes_nothing_to_the_disk(store_dir, name, kwargs, override):
    decision = _evaluate(store_dir, **kwargs, **override)
    assert decision["enabled"] is False
    assert not store_dir.exists(), f"{name}: the review directory was created for a configuration that is refused anyway"
    if name != "flag_misspelled":
        assert any(problem.startswith("store:") and "not probed" in problem for problem in decision["problems"]), decision["problems"]


def test_f25_the_one_place_that_starts_encounters_refuses_everything_but_the_review_launcher(monkeypatch):
    import curriculum_runtime as cr
    from account_store import AccountError

    class Store:
        def __init__(self, attempts):
            self.attempts = attempts

        def list_attempts(self, token):
            return self.attempts

    monkeypatch.setenv(fr.FLAG, fr.MODE_ON)
    context = {"store": Store([]), "token": "t", "user": {"id": 7, "role": "faculty"}}
    with pytest.raises(AccountError, match="only its scripted encounters"):
        cr.start_encounter(context, {}, lambda: None, "R2-05")                          # the repeat-attempt path (and any direct call): no pinned case
    active = {"user_id": 7, "status": "active", "id": "a1"}
    context = {"store": Store([active]), "token": "t", "user": {"id": 7, "role": "faculty"}}
    with pytest.raises(AccountError, match="does not resume"):
        cr.start_encounter(context, {}, lambda: None, "R2-05", pinned_variant="gi_bleed_57m")   # a pinned start never silently restores an unfinished attempt
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "except AccountError as exc:" in source[source.index("def begin_repeat_encounter"):source.index("def begin_repeat_encounter") + 1200], "the repeat path reports the refusal on the encounter that is open"


def test_f26_a_misspelled_flag_is_named_and_the_authority_is_unavailable_even_without_a_published_decision(store_dir):
    misspelled = _env(store_dir, **{fr.FLAG: "faculty_review"})
    assert fr.asked(misspelled) is True, "a misspelling is a refusal, not a silent absence"
    available, why = fr.authority_available({}, misspelled)
    assert available is False and "was not evaluated" in why
    assert fr.authority_available({}, {fr.FLAG: "  "}) == (True, ""), "blank is not named"
