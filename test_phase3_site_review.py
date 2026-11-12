"""P3-235 and P3-235A: the independent adversarial review of the dormant pair-authority site, its findings confirmed with probes and closed with mutants.

TEST-SIDE. A read-only reviewer attacked the candidate with 24 attacks and mutants of the code. No finding was HIGH; five were MEDIUM and several LOW. Each was reproduced
independently with a probe of the author's own BEFORE any correction (the probes are the first half of each test below: they state the attack), and each fix is
protected by a test that fails when the fix is removed (the mutants, named ``m*``).

* F1 (MEDIUM) ``request_abort`` after a would-commit minute forgot that authority had begun; the legacy fallback was granted while authority was evaluating.
* F2 (MEDIUM) the "second lock" depended on the pressure point's own approval: naming ``gi_pressure_committed`` committed a pair nobody approved.
* F3 (MEDIUM) ``replay_artifact`` / ``verify_artifact`` could not fail on a re-signed artifact for most fields.
* F4 (MEDIUM) the clock-writer guard saw only ``x["sim_time"] =``; a new caller of either engine clock function anywhere but the page went unseen.
* F5 (MEDIUM, test gap) the site's own ``settle`` and the page's call to it were covered by no assertion.
* F6 (LOW-MEDIUM) no test falsified the nine arming conditions one by one; ``case_allowlisted`` reported False for an allowed case.
* F7 grant exactness; F8 an exact int is a rung of the ladder; F9 one prepared commit per minute on exactly the evaluated state; F10 vacuous assertions, an
  artifact built with nowhere to put it, a process address in an experiment name.
"""
import ast
import dataclasses
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_authority_pair as pair
import runtime_minute_validation as mv
import runtime_pair_site as site_module
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam
import test_phase3_clock_routes as routes
import test_phase3_pair_site as base
import test_phase3_site_page as page_tests
from test_phase3_clock_routes import BEST, CASE, OTHER_GI, TEST_ONLY_SNAPSHOT, approved, bound  # noqa: F401 (fixtures)
from test_phase3_pair_gate import _all_the_flags, _arm, _fake_grant, _grant  # noqa: F401
from test_phase3_pair_site import _feed, infusion  # noqa: F401 (fixture)

ROOT = Path(__file__).resolve().parent
DEVELOPER = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, ra.ENVIRONMENT_FLAG: "development", rs.FLAG: rs.MODE_SHADOW_COMPARE}


def resign(artifact):
    """A re-signed artifact: the attacker recomputes the digest, which the package does not stop (it carries no signature) and which only the replay can catch."""
    artifact = deepcopy(artifact)
    artifact.pop("artifact_digest", None)
    artifact["artifact_digest"] = ra.digest_of(artifact)
    return artifact


# -- F1 ----------------------------------------------------------------------------------------------------------------------------------------------------------------

def test_f1_an_abort_after_a_would_commit_minute_is_invalid_for_continuation_and_the_legacy_fallback_is_refused_in_every_state(infusion):
    site = infusion["site"]
    _feed(infusion)
    assert site.state == site_module.WOULD_COMMIT and site.authority_began()
    assert site.request_legacy_fallback()["granted"] is False, "authority began: leaving is an explicit act, not a fallback"
    result = site.request_abort("operator requested")
    assert result["aborted"] is True and site.state == site_module.INVALID_FOR_CONTINUATION, site.state
    assert site.halt["authority_had_begun"] is True and "INVALID_FOR_CONTINUATION" in site.halt["consequence"]
    assert site.continuation()["legacy_may_continue_silently"] is False and site.request_legacy_fallback()["granted"] is False
    artifact = site.artifact()
    assert site_module.verify_artifact(artifact)["verified"] is True and artifact["halt"]["authority_had_begun"] is artifact["authority_had_begun"] is True


def test_f1_a_contradictory_artifact_is_refused_even_when_re_signed(infusion):
    """The artifact says authority began and the halt says it did not (the state of the defect): the consistency check, not the digest, finds it."""
    _feed(infusion)
    infusion["site"].request_abort("x")
    forged = deepcopy(infusion["site"].artifact())
    forged["halt"]["authority_had_begun"] = False
    forged["state"], forged["transitions"][-1]["to"] = site_module.EXPERIMENT_HALTED, site_module.EXPERIMENT_HALTED
    bad = site_module.verify_artifact(resign(forged))
    assert bad["verified"] is False and bad["digest_matches"] is True and bad["consistent"] is False, bad["consistency_problems"]


# -- F2 ----------------------------------------------------------------------------------------------------------------------------------------------------------------

def test_f2_naming_the_pressure_points_real_approval_does_not_commit_a_pair_nobody_approved(infusion, bound, monkeypatch):
    """The attack: both faculty constants satisfied, the environment names ``gi_pressure_committed`` (which IS in the registry). The pressure gate passes; the pair must not."""
    _feed(infusion)
    _arm(monkeypatch, bound)
    environ = {**DEVELOPER, ra.SNAPSHOT_FLAG: "gi_pressure_committed"}
    assert infusion["site"].arming(environ)["armed"] is True and "gi_pressure_committed" in ra.APPROVED_SNAPSHOTS
    target = deepcopy(infusion["after"])
    result = infusion["site"].request_commit(target, environ=environ)
    assert result["committed"] is False and result["prepared"] is None and result["outcome"] == site_module.COMMIT_REFUSED_V1_NOT_APPROVED
    assert ra.digest_of(target) == ra.digest_of(infusion["after"])
    assert pair.V1_ID not in ra.APPROVED_SNAPSHOTS


def test_f2_the_transaction_gate_is_still_a_further_lock_when_version_1_is_approved_by_a_test_fixture(infusion, bound, monkeypatch):
    _feed(infusion)
    _arm(monkeypatch, bound)
    monkeypatch.setitem(ra._APPROVED_SNAPSHOT_POINTS, pair.V1_ID, TEST_ONLY_SNAPSHOT)       # TEST ONLY: version 1 "approved" inside this one test
    result = infusion["site"].request_commit(deepcopy(infusion["after"]), environ=DEVELOPER)           # no authority snapshot named in the environment
    assert result["committed"] is False and result["outcome"] == site_module.COMMIT_REFUSED_BY_TRANSACTION and "gate refuses" in result["reason"]


# -- F3 ----------------------------------------------------------------------------------------------------------------------------------------------------------------

def _forge(label, artifact):
    turn = artifact["turns"][0]
    changes = {
        "would_write.sbp forged": lambda a: a["turns"][0]["would_write"].update(sbp=40.0),
        "would_write.category forged": lambda a: a["turns"][0]["would_write"].update(consciousness_category=3, mental_status="Unresponsive"),
        "interval emptied": lambda a: a["turns"][0].update(interval=[]),
        "interval truncated": lambda a: a["turns"][0].update(interval=a["turns"][0]["interval"][5:]),
        "common.F forged": lambda a: a["turns"][0]["common"].update(F=0.99),
        "common.word forged": lambda a: a["turns"][0]["common"].update(mental_status="Alert" if turn["common"]["mental_status"] != "Alert" else "Obtunded"),
        "snapshot profile lies": lambda a: a["snapshot"].update(profile_digest="0" * 64),
        "snapshot names another id": lambda a: a["snapshot"].update(snapshot_id="GI_DEVELOPMENT_SNAPSHOT_V2"),
        "lineage lies": lambda a: a["lineage"].update(digest="0" * 64),
        "commit request claims a commit": lambda a: a.update(commit_requests=[{"committed": True, "minute": 30}]),
        "armed gate claimed": lambda a: a["arming"].update(armed=True),
        "verdict flipped to a non-collapse abort": lambda a: a["turns"][0].update(verdict="WOULD_ABORT", failed_checks=["window_open"], would_write=None),
        "window check lies": lambda a: a["turns"][0].update(failed_checks=["window_open"]),
        "payload kept on an abort": lambda a: a["turns"][0].update(verdict="WOULD_ABORT", failed_checks=["pressure_validated"]),
        "turn duplicated": lambda a: a["turns"].append(deepcopy(a["turns"][0])),
        "illegal history": lambda a: a["transitions"].append({"to": "NOT_STARTED", "minute": 1, "why": "x"}),
        "state not the end of the history": lambda a: a.update(state="EXPERIMENT_HALTED"),
        "authority flag forged": lambda a: a.update(authority_had_begun=False),
        "would-commit minutes forged": lambda a: a.update(would_commit_minutes=[29]),
    }
    forged = deepcopy(artifact)
    changes[label](forged)
    return resign(forged)


FORGERIES = ("would_write.sbp forged", "would_write.category forged", "interval emptied", "interval truncated", "common.F forged", "common.word forged", "snapshot profile lies",
             "snapshot names another id", "lineage lies", "commit request claims a commit", "armed gate claimed", "verdict flipped to a non-collapse abort", "window check lies",
             "payload kept on an abort", "turn duplicated", "illegal history", "state not the end of the history", "authority flag forged", "would-commit minutes forged")


@pytest.mark.parametrize("label", FORGERIES)
def test_f3_a_re_signed_artifact_that_lies_fails_the_verification_or_the_replay(infusion, label):
    _feed(infusion)
    artifact = infusion["site"].artifact()
    assert site_module.verify_artifact(artifact)["verified"] is True and site_module.replay_artifact(artifact)["reproduces"] is True       # the honest one passes
    forged = _forge(label, artifact)
    verified, replayed = site_module.verify_artifact(forged), site_module.replay_artifact(forged)
    assert verified["digest_matches"] is True, "the forgery is re-signed: the digest cannot be what catches it"
    assert verified["verified"] is False or replayed["reproduces"] is False, (label, verified["consistency_problems"], replayed["mismatches"][:2])


def test_f3_the_replay_names_the_rebuilt_profile_and_a_swapped_replay_input_is_found(infusion):
    """The bound run's profile is REBUILT from its immutable input: an artifact whose input is another snapshot's cannot pass as version 1."""
    _feed(infusion)
    artifact = infusion["site"].artifact()
    assert site_module.replay_artifact(artifact)["snapshot_matches"] is True
    swapped = deepcopy(artifact)
    swapped["replay_inputs"]["bound"] = swapped["replay_inputs"]["pressure"]          # the pressure run's own input (the committed profile, no Amendment 2)
    result = site_module.replay_artifact(resign(swapped))
    assert result["snapshot_matches"] is False and result["reproduces"] is False


# -- F4 ----------------------------------------------------------------------------------------------------------------------------------------------------------------

def _clock_mentions(root):
    """Every place a non-test module of ``root`` WRITES ``sim_time`` into a state, in any of its forms: a subscript store, ``__setitem__`` / ``setdefault`` / ``update`` carrying the
    key (as an argument, inside a dict literal, or as a keyword), ``dict(state, sim_time=...)`` and a copy ``{**state, "sim_time": ...}``. (The older inventory sees only the first.)
    A key held in a variable cannot be resolved statically; the dynamic tripwire below covers it on the real page."""
    found = set()
    for path in sorted(root.rglob("*.py")):
        parts = path.relative_to(root).parts
        if parts[0] in ("validation", "docs", "scripts", ".git", "clinical_physiology", "clinical_core") or path.name.startswith(("test_", "regression_")):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))

        def has_key(node):
            return isinstance(node, ast.Dict) and any(isinstance(key, ast.Constant) and key.value == "sim_time" for key in node.keys)

        def walk(node, function):
            for child in ast.iter_child_nodes(node):
                name = child.name if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else function
                walk(child, name)
                if isinstance(child, ast.Subscript) and isinstance(child.ctx, ast.Store) and isinstance(child.slice, ast.Constant) and child.slice.value == "sim_time":
                    found.add((path.name, function))
                if has_key(child) and None in child.keys:                                     # ``{**state, "sim_time": ...}``
                    found.add((path.name, function))
                if isinstance(child, ast.Call):
                    attribute = child.func.attr if isinstance(child.func, ast.Attribute) else (child.func.id if isinstance(child.func, ast.Name) else None)
                    carries = (any(isinstance(arg, ast.Constant) and arg.value == "sim_time" for arg in child.args) or any(has_key(arg) for arg in child.args)
                               or any(keyword.arg == "sim_time" for keyword in child.keywords))
                    if attribute in ("__setitem__", "setdefault", "update", "dict") and carries:
                        found.add((path.name, function))
        walk(tree, None)
    return found


#: The five clock WRITERS of P3-215 (two reachable by a GI encounter) and the two builders of an encounter's ARRIVAL state (they set minute 0 on a state that does not exist yet:
#: they advance nothing). A new one, in any of the forms above, fails the pin below instead of passing unseen.
KNOWN_CLOCK_MENTIONS = {("family_engine.py", "advance_clinical_time"), ("family_engine.py", "execute_family_bundle"), ("app.py", "_advance_with_timed_fluids"),
                        ("coupled_encounter.py", "tick"), ("generated_engine.py", "_minute"),
                        ("cognitive_generator.py", "generate_cognitive_encounter"), ("generated_case.py", "generate_ai_encounter")}


def test_f4_the_wider_inventory_detects_every_form_of_a_new_clock_writer(tmp_path):
    forms = {
        "update_kw": "def f(s):\n    s.update(sim_time=3)\n", "dict_key": "def f(s):\n    return {**s, 'sim_time': 3}\n", "setitem": "def f(s):\n    s.__setitem__('sim_time', 3)\n",
        "update_arg": "def f(s):\n    s.update({'sim_time': 3})\n", "dict_call": "def f(s):\n    return dict(s, sim_time=3)\n", "setdefault": "def f(s):\n    s.setdefault('sim_time', 3)\n",
    }
    for label, source in forms.items():
        directory = tmp_path / label
        directory.mkdir()
        (directory / "new_writer.py").write_text(source, encoding="utf-8")
        assert ("new_writer.py", "f") in _clock_mentions(directory), label


def test_f4_the_repository_has_exactly_the_known_clock_mentions_and_the_known_callers_of_the_two_engine_clock_functions():
    """Pinned: a new writer in ANY form, or a new caller of ``advance_clinical_time`` / ``execute_family_bundle`` anywhere but the page, fails here instead of passing unseen.
    The callers that are not the page: the legacy counterfactual runners of the migration adapters (they run on copies, for the shadow), the catalog's offline trajectories
    and the headless acceptance harness. None of them is an encounter a resident plays."""
    mentions = _clock_mentions(ROOT)
    assert mentions >= routes._writers_of_the_clock(), "the wider scan sees at least what the older one saw"
    callers = {}
    for target in ("advance_clinical_time", "execute_family_bundle"):
        found = set()
        for path in sorted(ROOT.rglob("*.py")):
            parts = path.relative_to(ROOT).parts
            if parts[0] in ("validation", "docs", ".git", "clinical_physiology") or path.name.startswith(("test_", "regression_")):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for function in (node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)):
                if any(isinstance(node, ast.Call) and ast.unparse(node.func).split(".")[-1] == target for node in ast.walk(function)):
                    found.add((str(path.relative_to(ROOT)), function.name))
        callers[target] = found
    assert callers["advance_clinical_time"] == {("app.py", "spend_clinical_time"), ("clinical_core/acs_migration.py", "legacy"), ("clinical_core/asthma_migration.py", "legacy"),
                                                ("clinical_core/edema_migration.py", "legacy"), ("clinical_core/embolism_migration.py", "legacy"),
                                                ("clinical_core/legacy_adapter.py", "run_legacy")}
    assert callers["execute_family_bundle"] == {("app.py", "execute_bundle"), ("catalog_trajectories.py", "run"), ("catalog_trajectories.py", "waited_out"),
                                                ("clinical_core/legacy_adapter.py", "run_legacy"), ("pilot_acceptance.py", "_execute")}
    assert mentions == KNOWN_CLOCK_MENTIONS, sorted(mentions ^ KNOWN_CLOCK_MENTIONS, key=lambda item: (item[0], str(item[1])))


def test_f4_a_dynamic_tripwire_every_engine_clock_move_on_the_real_page_is_followed_by_the_one_hook_on_its_own_route(monkeypatch):
    """The static scan cannot see a route that is built at run time. Under the real page, spy on both engine functions and on the hook: every move of the clock must be
    answered by exactly one hook call, on the route of the function that moved it, in order."""
    import family_engine
    log = []
    real_time, real_bundle, real_hook = family_engine.advance_clinical_time, family_engine.execute_family_bundle, ra.after_clock_moved

    def spy_time(*args, **kwargs):
        log.append(("engine", ra.CLINICAL_TIME))
        return real_time(*args, **kwargs)

    def spy_bundle(*args, **kwargs):
        log.append(("engine", ra.ORDER_TURN))
        return real_bundle(*args, **kwargs)

    def spy_hook(store, session, before, after, ran, submission_id, route, **kwargs):
        log.append(("hook", route))
        return real_hook(store, session, before, after, ran, submission_id, route, **kwargs)
    monkeypatch.setattr(family_engine, "advance_clinical_time", spy_time)
    monkeypatch.setattr(family_engine, "execute_family_bundle", spy_bundle)
    monkeypatch.setattr(ra, "after_clock_moved", spy_hook)
    at = page_tests.page._open(monkeypatch, "gi_bleed_57m", shadow=True, dry=True)
    for step in (("question", None), ("examination", None), ("order", "Give 500 mL normal saline over 5 minutes."), ("question", "Any allergies?")):
        page_tests._drive(at, step)
    engine = [item for item in log if item[0] == "engine"]
    assert len(engine) >= 4, log
    for index, item in enumerate(log):
        if item[0] == "engine":
            assert index + 1 < len(log) and log[index + 1] == ("hook", item[1]), (index, log)
    assert [item for item in log if item[0] == "hook"] == [("hook", route) for _, route in engine]


# -- F5 ----------------------------------------------------------------------------------------------------------------------------------------------------------------

def test_f5_the_sites_own_settle_halts_visibly_on_an_unsupported_settled_class_and_keeps_the_record_digest_honest(infusion):
    site = infusion["site"]
    _feed(infusion)
    site.settle([{"order_id": "inf-1:0", "class": "intubation", "fate": "EXECUTED"}])
    assert site.state == site_module.INVALID_FOR_CONTINUATION and site.halt["stage"] == "settlement" and site.halt["authority_had_begun"] is True
    record = site.records[-1]
    assert record["settlement_refusal"] and record["digest"] == ra.digest_of({key: value for key, value in record.items() if key != "digest"})
    assert [item["to"] for item in site.transitions][-2:] == ["WOULD_ABORT", "INVALID_FOR_CONTINUATION"]
    assert site_module.verify_artifact(site.artifact())["verified"] is True


def test_f5_a_settled_iv_line_does_not_stop_the_experiment_and_a_settled_ledger_before_any_turn_changes_nothing(infusion):
    site = infusion["site"]
    site.settle([{"order_id": "x:0", "class": "intubation", "fate": "EXECUTED"}])           # no record yet: nothing to settle, nothing halts
    assert site.halt is None and site.state == site_module.NOT_STARTED
    _feed(infusion)
    site.settle([{"order_id": "inf-1:0", "class": "vascular_access", "fate": "EXECUTED"}])
    assert site.halt is None and site.state == site_module.WOULD_COMMIT


def test_f5_the_page_settles_the_ledger_once_per_order_turn_through_the_one_hook():
    """Static: the page calls ``after_orders_settled`` exactly once, in the order route, with the settled ledger (the mutant that drops the call changed no other test)."""
    text = (ROOT / "app.py").read_text(encoding="utf-8")
    assert text.count("after_orders_settled(") == 1
    tree = ast.parse(text)
    holders = [function.name for function in ast.walk(tree) if isinstance(function, ast.FunctionDef)
               if any(isinstance(node, ast.Call) and ast.unparse(node.func).endswith("after_orders_settled") for node in ast.walk(function))]
    assert holders == ["_process_encounter_submission"], holders
    call = text[text.index("after_orders_settled("):].split("\n")[0]
    assert "_ledger.snapshot(" in call and "_shadow" in call


# -- F6 ----------------------------------------------------------------------------------------------------------------------------------------------------------------

def _armed_site(infusion, bound, monkeypatch):
    _feed(infusion)
    _arm(monkeypatch, bound)
    site = infusion["site"]
    assert site.arming(DEVELOPER)["armed"] is True and site.arming(DEVELOPER)["failed"] == []
    return site


BREAKERS = {
    "global_development_capability": (lambda site, mp, env: env.pop(ra.ENVIRONMENT_FLAG), set()),
    "correct_mode": (lambda site, mp, env: setattr(site, "mode", mv.PRESSURE_ONLY), set()),
    "certified_lineage": (lambda site, mp, env: mp.setattr(ev, "core_lineage_ok", lambda: False), set()),
    "exact_snapshot": (lambda site, mp, env: setattr(site, "runner", None), {"technical_site_healthy"}),
    "explicit_pair_authority_grant": (lambda site, mp, env: mp.setattr(site_module, "GRANT_REGISTRY", ()), set()),
    "case_allowlisted": (lambda site, mp, env: setattr(site, "case_id", "opioid_35m"), {"explicit_pair_authority_grant"}),
    "experiment_not_halted": (lambda site, mp, env: setattr(site, "halt", {"minute": 1}), set()),
    "faculty_approval_permits_domain": (lambda site, mp, env: mp.setattr(site_module, "FACULTY_APPROVAL", {site_module.PAIR_DOMAIN: "NOT_GRANTED"}), set()),
    "technical_site_healthy": (lambda site, mp, env: site.violations.append("a violation"), set()),
}


@pytest.mark.parametrize("name", site_module.ARMING_CONDITIONS)
def test_f6_each_of_the_nine_arming_conditions_is_falsified_alone_and_disarms_the_site(infusion, bound, monkeypatch, name):
    """With every other condition satisfied, breaking ONE disarms the site, and the condition that went false is the one named (a coupled one may follow)."""
    site = _armed_site(infusion, bound, monkeypatch)
    environ = dict(DEVELOPER)
    breaker, coupled = BREAKERS[name]
    breaker(site, monkeypatch, environ)
    arming = site.arming(environ)
    assert arming["armed"] is False and arming["conditions"][name] is False, arming["conditions"]
    assert set(arming["failed"]) == {name} | coupled, arming["failed"]
    assert site.request_commit(deepcopy(infusion["after"]), environ=environ)["committed"] is False


def test_f6_the_case_allowlist_is_the_repositorys_and_true_for_the_two_gi_cases_even_with_no_grant(infusion):
    _feed(infusion)
    arming = infusion["site"].arming({})
    assert arming["conditions"]["case_allowlisted"] is True and arming["conditions"]["explicit_pair_authority_grant"] is False


# -- F7 ----------------------------------------------------------------------------------------------------------------------------------------------------------------

class _Chatty(dict):
    def get(self, name, default=None):                                                  # answers one thing to the check and another to the data
        return "whatever" if name == "decision_reference" else super().get(name, default)


@pytest.mark.parametrize("label", ("extra field", "mapping subclass", "version as a float", "version as a bool", "blank grant id", "blank decision", "cases as a tuple", "cases not strings",
                                   "a non-string core digest"))
def test_f7_a_grant_that_is_not_an_exact_plain_dict_of_the_right_types_is_refused(bound, label):
    good = _grant(bound)
    assert site_module.grant_problems(good, bound=bound, case_id=CASE) == []
    forged = {
        "extra field": {**good, "extra": 1}, "mapping subclass": _Chatty(good), "version as a float": {**good, "snapshot_version": 1.0}, "version as a bool": {**good, "snapshot_version": True},
        "blank grant id": {**good, "grant_id": "   "}, "blank decision": {**good, "decision_reference": " "}, "cases as a tuple": {**good, "cases": (CASE, OTHER_GI)},
        "cases not strings": {**good, "cases": [CASE, 3]}, "a non-string core digest": {**good, "core_digest": 7},
    }[label]
    assert site_module.grant_problems(forged, bound=bound, case_id=CASE), label


# -- F8 ----------------------------------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("value", (True, 0.0, 1.0))
def test_f8_a_category_that_hashes_like_a_rung_is_not_a_rung_at_an_intermediate_minute_either(infusion, monkeypatch, value):
    real = fam.run_channels

    def tampered(runner):
        rows = real(runner)
        for row in rows:
            if row["minute"] == 12 and "channels_unavailable" not in row:
                row["channels"] = {**row["channels"], "category_index": value, "consciousness_level": value}
        return rows
    monkeypatch.setattr(fam, "run_channels", tampered)
    record = _feed(infusion)
    assert record["verdict"] == pair.WOULD_ABORT and record["detail"]["interval_minutes_validated"]["first_failed_minute"] == 12


# -- F9 ----------------------------------------------------------------------------------------------------------------------------------------------------------------

def test_f9_one_prepared_commit_per_minute_and_only_on_exactly_the_state_that_was_evaluated(infusion, bound, monkeypatch, approved):
    _feed(infusion)
    _arm(monkeypatch, bound)
    monkeypatch.setitem(ra._APPROVED_SNAPSHOT_POINTS, pair.V1_ID, TEST_ONLY_SNAPSHOT)             # TEST ONLY
    environ = _all_the_flags(approved) | {ra.SNAPSHOT_FLAG: TEST_ONLY_SNAPSHOT["id"]}
    other = deepcopy(infusion["after"])
    other["observable"] = {**other["observable"], "hr": int(other["observable"].get("hr") or 80) + 1}            # same minute, another state
    assert infusion["site"].request_commit(other, environ=environ)["outcome"] == site_module.COMMIT_REFUSED_OTHER_STATE
    first = infusion["site"].request_commit(deepcopy(infusion["after"]), environ=environ)
    assert first["committed"] is True and first["outcome"] == site_module.COMMIT_PREPARED_FOR_THE_CALLER, first.get("reason")
    second = infusion["site"].request_commit(deepcopy(infusion["after"]), environ=environ)
    assert second["committed"] is False and second["outcome"] == site_module.COMMIT_REFUSED_ALREADY_PREPARED
    assert infusion["site"].artifact()["committed_authority"] is False
    assert site_module.verify_artifact(infusion["site"].artifact())["verified"] is False, "an artifact with a prepared commit is not a dormant evaluation: it says so"


# -- F10 ---------------------------------------------------------------------------------------------------------------------------------------------------------------

def test_f10_nothing_is_serialized_when_there_is_nowhere_to_write_and_the_experiment_name_is_the_encounters_not_a_process_address(infusion, monkeypatch, bound):
    _feed(infusion)
    monkeypatch.delenv(site_module.store.STORE_FLAG, raising=False)
    monkeypatch.setattr(site_module.DormantPairSite, "artifact", lambda self: (_ for _ in ()).throw(AssertionError("the artifact was built with the store off")))
    assert infusion["site"].persist({})["why"] == site_module.store.NOT_CONFIGURED
    arrival = infusion["arrival"]
    one, two = site_module.DormantPairSite(bound, CASE, arrival), site_module.DormantPairSite(bound, CASE, deepcopy(arrival))
    assert one.experiment_id == two.experiment_id == f"dormant-{CASE}-{one.encounter_id[:12]}" and "0x" not in one.experiment_id


def test_f10_the_faculty_column_of_the_record_is_read_from_the_code_not_a_literal(monkeypatch):
    import test_phase3_site_series as series
    source = (ROOT / "test_phase3_site_series.py").read_text(encoding="utf-8")
    assert "FACULTY_APPROVAL" in source and '"pair_authority": site_module.FACULTY_APPROVAL' in source.replace("  ", " ")
    assert series.site_module.FACULTY_APPROVAL[site_module.PAIR_DOMAIN] == "NOT_GRANTED"
