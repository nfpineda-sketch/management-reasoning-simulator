"""P3-11: one execution path for live and replay, and the GI acceptance battery as shadow evidence.

What every test here defends is the same boundary as P3-1 and P3-4: the legacy engine is the only runtime
authority, so the shadow may observe and must never decide. What P3-11 adds is that the evidence is now the
repository's own acceptance battery instead of one case and two turns, and that the live path and the offline
replay are the SAME function of the same immutable input -- not two implementations that happen to agree.

The digests pinned in ``BASELINE`` were captured from the live path BEFORE the unification (P3-11-2): they
are how a future change that silently moves the GI shadow gets caught.
"""
import ast
import json
import os
from copy import deepcopy
from pathlib import Path

import pytest

import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam
from clinical_core.state import CoreInvariantError, UnresolvedBoundary

ROOT = Path(__file__).resolve().parent
CASE = "gi_bleed_57m"
TURNS = ("Give 1 litre of normal saline over 15 minutes. Reassess in 10 minutes.",
         "Transfuse 2 units of packed red cells. Start pantoprazole 80 mg IV. Reassess in 20 minutes.")
#: The live GI shadow before the P3-11 unification: final state digest, minutes, mirrored actions.
BASELINE = {
    "gi_bleed_57m": ("37ead19e198878ca61aa073ff816f5900dcaf13d73a2a2cf5733e193b36b4de5", 30, 5),
    "gi_bleed_72f": ("497c1d3527433b5acd8029a98ee7ebb7acb86f78ff2e6c0ba8b8ddfcc18e0446", 30, 5),
}
#: The GI actions whose correct use defines management of a haemorrhage in this battery.
MANAGEMENT_DEFINING = ("fluid", "blood", "ppi", "procedure")


def _play(variant, turns, mode=rs.MODE_SHADOW_COMPARE):
    import pilot_acceptance
    with ev.shadow(mode):
        encounter = pilot_acceptance.Encounter(variant)
        for text in turns:
            encounter.order(text)
    return encounter


@pytest.fixture(scope="module")
def evidence():
    """The full GI acceptance battery, played off and on, once for this module."""
    data = ev.gi_evidence()
    data["matrix"] = ev.scenario_matrix(data)
    return data


@pytest.fixture(scope="module")
def scenarios(evidence):
    return [scenario for case in evidence["cases"] for scenario in case["scenarios"]]


# -- P3-11-1: ONE execution path ---------------------------------------------------------------------------

def test_u1_only_the_runner_advances_the_core():
    """No module of the layer but the runner may call the core's integration: one minute-advance.

    This is the structural half of ``LIVE_REPLAY_SINGLE_EXECUTION_PATH``: if the live path could call
    ``integration.run`` itself, the two paths could drift again however green the equality test is.
    """
    callers = {}
    for name in ("runtime_shadow.py", "runtime_shadow_families.py", "runtime_shadow_evidence.py"):
        tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = node.func
            if isinstance(target, ast.Attribute) and target.attr == "run" and \
                    isinstance(target.value, ast.Name) and target.value.id == "integration":
                callers.setdefault(name, []).append(node.lineno)
    assert set(callers) == {"runtime_shadow_families.py"}, callers
    advance = next(node for node in ast.walk(ast.parse(
        (ROOT / "runtime_shadow_families.py").read_text(encoding="utf-8")))
        if isinstance(node, ast.FunctionDef) and node.name == "advance")
    inside = {node.lineno for node in ast.walk(advance) if isinstance(node, ast.Call)
              and isinstance(node.func, ast.Attribute) and node.func.attr == "run"}
    assert inside and inside <= set(callers["runtime_shadow_families.py"])


def test_u1_the_live_session_owns_no_second_comparison_or_replay():
    """The live session delegates: no classifier, no scenario serialization, no digest loop of its own."""
    source = (ROOT / "runtime_shadow.py").read_text(encoding="utf-8")
    for forbidden in ("def _compare", "comparison.VARIABLES", "integration.scenario_to_dict",
                      "integration.scenario_from_dict", "trajectory.derived()"):
        assert forbidden not in source, forbidden
    session = rs.ShadowSession.start({"engine_family": "gi_bleed"}, environ={rs.FLAG: rs.MODE_SHADOW_COMPARE})
    assert session is not None and isinstance(session.minutes, list)


# -- P3-11-2: the GI live behaviour is exactly what it was -------------------------------------------------

@pytest.mark.parametrize("variant", sorted(BASELINE))
def test_u2_the_unification_did_not_move_the_gi_shadow(variant):
    expected_digest, expected_minutes, expected_actions = BASELINE[variant]
    session = _play(variant, TURNS).shadow
    digests = list(session.digests())
    assert len(digests) == expected_minutes and digests[-1] == expected_digest
    assert len(session.mirrored) == expected_actions
    assert session.failures == [] and session.gaps == []
    assert [item["state_digest"] for item in session.replay()["minutes"]] == digests


# -- P3-11-3, P3-11-8: the battery decides the same thing with the shadow on -------------------------------

def test_u3_the_battery_is_the_repositorys_own_and_decides_identically(evidence):
    import pilot_acceptance
    import test_phase0_acceptance_battery as battery_test
    assert ev.gi_variants() == ("gi_bleed_57m", "gi_bleed_72f")
    for case in evidence["cases"]:
        assert set(case["categories_on"]) == set(battery_test.CATEGORIES), case["case"]
        assert case["categories_identical"], case["case"]
        assert case["failed_categories"] == [], case["failed_categories"]
        assert not case["unpaired"], case["unpaired"]
    assert evidence["scenarios_played"] == 34, evidence["scenarios_played"]
    assert pilot_acceptance._COLLECTOR is None, "the collector must not survive the run"


def test_u4_no_safety_critical_condition_is_tripped_in_any_scenario(scenarios):
    for scenario in scenarios:
        tripped = {name for name, value in scenario["safety"].items() if value}
        assert not tripped, (scenario["case"], scenario["scenario"], tripped)
    assert {name for scenario in scenarios for name in scenario["safety"]} == set(ev.SAFETY_CONDITIONS)


# -- P3-11-4: live == replay, digest by digest, by construction and by test --------------------------------

def test_u5_live_equals_replay_for_every_scenario(scenarios):
    for scenario in scenarios:
        assert scenario["live_equals_replay"], (scenario["case"], scenario["scenario"])
        assert scenario["live_digests"] and scenario["final_digest"] == scenario["live_digests"][-1]


def test_u6_the_replay_artifact_rebuilds_the_run_from_json_alone(scenarios):
    """P3-11-12: representative scenarios reconstructed from the serialized artifact and nothing else."""
    wanted = ("C_omission", "E_excessive_treatment", "B_delayed_management", "A_correct_management",
              "I_waiting", "J_reassessment")
    seen = []
    for scenario in scenarios:
        if scenario["scenario"] not in wanted or scenario["case"] != CASE:
            continue
        seen.append(scenario["scenario"])
        result = ev.replay_from_json(scenario)
        assert result["ok"], (scenario["scenario"], result.get("why"))
        assert result["digests"] == scenario["live_digests"]
    assert sorted(seen) == sorted(wanted), seen


def test_u7_an_oxygen_order_is_mirrored_too_even_though_the_battery_never_gives_one(scenarios):
    """The battery's GI scripts order no oxygen, so the mapping's oxygen arm is exercised here."""
    assert "oxygen" not in {kind for scenario in scenarios for kind in scenario["coverage"]}
    session = _play(CASE, ("Start oxygen at 4 litres by nasal cannula. Reassess in 10 minutes.",)).shadow
    kinds = [event.kind for event in session.mirrored]
    # The reassessment is mirrored as an event and dropped by the mapping: Phase 2 declares it
    # non-physiological, so it builds no contributor and is not a gap either.
    assert [kind for kind in kinds if kind != "reassessment"] == ["oxygen"], kinds
    assert session.gaps == [] and session.failures == []
    assert [item["state_digest"] for item in session.replay()["minutes"]] == list(session.digests())


# -- P3-11-9: action coverage ------------------------------------------------------------------------------

def test_u8_every_management_defining_action_is_mirrored(evidence):
    coverage = evidence["coverage"]
    for kind in MANAGEMENT_DEFINING:
        assert coverage[kind]["status"] == ev.FULLY_MIRRORED, (kind, coverage[kind])
    assert coverage["consult"]["status"] == ev.STRUCTURAL_ONLY
    # The engine reports the haemostasis as a ``procedure`` receipt and the core receives it through
    # ``family_state``. That shortcut is only honest while the battery's only procedure IS the endoscopy:
    # the two are claimed in exactly the same scenarios, and that is checked, not assumed.
    assert sorted(coverage["procedure"]["scenarios"]) == sorted(coverage["endoscopy"]["scenarios"])


def test_u9_an_action_the_core_cannot_represent_is_declared_not_silent(evidence, scenarios):
    """The battery exercises three GI treatments the common mapping has no writer for.

    They are the blocker P3-11 was run to find: each is DECLARED as a gap in the scenario that uses it, so a
    reader cannot mistake the shadow's unchanged course for the core disagreeing with the engine.
    """
    assert evidence["unsupported"] == ["anticoagulation", "aspirin", "norepinephrine"]
    for scenario in scenarios:
        unsupported = {kind for kind, how in scenario["coverage"].items()
                       if how["status"] == ev.UNSUPPORTED}
        declared = {str(gap.get("kind")) for gap in scenario["gaps"]}
        assert unsupported <= declared, (scenario["scenario"], unsupported, declared)
    assert "TREATMENT_GAP on ['anticoagulation', 'aspirin', 'norepinephrine']" in evidence["blockers"]
    assert evidence["readiness"] == "GI_FULL_LIVE_SHADOW_EVIDENCE_NOT_READY"


# -- P3-11-6, P3-11-7: comparability and classification ----------------------------------------------------

def test_u10_every_domain_is_classified_and_every_difference_has_a_class(scenarios):
    allowed = {fam.EXPECTED_ARCHITECTURAL, rs.PARTIALLY_EXPLAINED, fam.PARAMETER_DISABLED,
               fam.REGION_DIVERGENCE, fam.MAPPING_GAP, fam.TREATMENT_GAP, fam.BOUNDARY,
               fam.NOT_COMPARABLE, fam.UNEXPECTED, rs.SAFETY_CRITICAL}
    for scenario in scenarios:
        assert set(scenario["domains"]) == set(fam.DOMAINS), scenario["scenario"]
        for name, item in scenario["domains"].items():
            assert item["comparability"] in (ev.COMPARABLE, ev.PARTIALLY_COMPARABLE,
                                             ev.NOT_COMPARABLE, ev.NOT_EXERCISED), (name, item)
        assert set(scenario["divergence_classes"]) <= allowed, scenario["divergence_classes"]


def test_u11_no_unexpected_structural_divergence_in_the_whole_battery(evidence, scenarios):
    assert evidence["unexpected"] == []
    for scenario in scenarios:
        assert not scenario["unexpected"], (scenario["scenario"], scenario["unexpected"])
    classes = {name for scenario in scenarios for name in scenario["divergence_classes"]}
    # Only two classes appear in the whole battery, and neither is loud: the golden explains the first in
    # every GI scenario and declares the second in some of them, with its count.
    assert classes == {fam.EXPECTED_ARCHITECTURAL, rs.PARTIALLY_EXPLAINED}, classes


def test_u12_a_treatment_gap_is_not_hidden_by_an_already_explained_difference(scenarios):
    """The honest reading of the three gaps: their scenarios show no UNEXPECTED difference either.

    The golden declares the pressures and the rate architectural in GI, so a missing vasopressor writer
    cannot show up as a loud divergence. That is exactly why coverage is reported next to the classes.
    """
    gapped = [scenario for scenario in scenarios
              if any(how["status"] == ev.UNSUPPORTED for how in scenario["coverage"].values())]
    assert sorted(scenario["scenario"] for scenario in gapped) == [
        "D_incorrect_treatment", "D_incorrect_treatment", "F_start_stop", "F_start_stop",
        "K_combined_interventions", "K_combined_interventions"], [s["scenario"] for s in gapped]
    assert all(not scenario["unexpected"] for scenario in gapped)


# -- P3-11-10: order, fate, write-ahead -------------------------------------------------------------------

def test_u13_nothing_is_mirrored_before_its_fate_and_nothing_twice(scenarios):
    for scenario in scenarios:
        ids = [event["order_id"] for event in scenario["mirrored"]]
        assert len(ids) == len(set(ids)), (scenario["scenario"], ids)
        ledger = [event["ledger_order_id"] for event in scenario["mirrored"]]
        assert all(item is not None for item in ledger), (scenario["scenario"], ledger)
        assert len(ledger) == len(set(ledger)), (scenario["scenario"], ledger)
    source = (ROOT / "runtime_shadow.py").read_text(encoding="utf-8")
    assert 'parsed["actions"]' not in source, "the mirror must read the settled list, never the parse"


def test_u14_the_replay_artifact_carries_every_identity_it_promises(scenarios):
    for scenario in scenarios:
        captured = scenario["replay_input"]
        assert captured["case_id"] and captured["family"] == "gi_bleed"
        assert captured["adapter_version"] and captured["snapshot"]["id"]
        assert captured["scenario_id"] == scenario["scenario"]
        versions = captured["versions"]
        for key in ("phase2_closure_head", "phase2_digest", "phase3_module", "adapter",
                    "parameter_snapshot", "closure_guard_digest", "families_module",
                    "phase3_layer_digest"):
            assert versions.get(key), key
        assert versions["phase2_digest"] == rs.PHASE2_DIGEST
        for action in captured["actions"]:
            assert action["order_id"] and action["kind"] and action["ledger_order_id"]
            assert action["submission_id"] is not None


def test_u15_the_layer_digest_is_the_identity_of_the_code_that_ran():
    first = rs.layer_digest()
    assert first == rs.layer_digest() and len(first) == 64
    # P3-148/P3-149: the shadow research trace store and its faculty observer joined the layer, so the
    # digest covers them too. The set stays pinned by name.
    assert set(rs.LAYER_SOURCES) == {"runtime_shadow.py", "runtime_shadow_families.py",
                                     "runtime_authority_store.py",
                                     "runtime_shadow_evidence.py", "runtime_authority.py",
                                     "runtime_shadow_store.py", "runtime_shadow_observer.py",
                                     "runtime_authority_pair.py", "runtime_minute_validation.py", "runtime_pair_site.py",
                                     "runtime_pressure_grant.py", "runtime_authority_session.py", "runtime_authority_turn.py"}                   # P3-271 (declared adaptation): runtime_authority_turn, the authority-controlled turn (copy, judge, apply or discard). P3-251 (declared adaptation): the authority-session stop guard. P3-239 (declared adaptation): the explicit GI development pressure grant
    for name in rs.LAYER_SOURCES:
        assert (ROOT / name).exists(), name


# -- P3-11-13: error injection ----------------------------------------------------------------------------

def test_u16_an_invalid_parameter_snapshot_is_refused_and_no_run_opens():
    with pytest.raises(ValueError):  # a snapshot can never claim approval
        fam.ShadowParameterSnapshot("gi_x", "gi_bleed", fam.COMMITTED, ("probe",), approved=True)
    with pytest.raises(ValueError):  # nor sit at a point the region does not have
        fam.ShadowParameterSnapshot("gi_x", "gi_bleed", "whatever", ("probe",))
    assert fam.ShadowPhysiologyRunner.open("gi_bleed", "not_a_case") is None
    assert fam.ShadowPhysiologyRunner.open("not_a_family", "gi_bleed_57m") is None


def test_u17_a_duplicate_or_malformed_event_cannot_reach_the_physics():
    runner = fam.ShadowPhysiologyRunner.open("gi_bleed", CASE)
    event = rs.MirroredAction("m000-t00-0-fluid", 0, "fluid", {"volume_ml": 500.0},
                              {"delivery_starts_at_min": 0}, 0.21, "t0:0", "t0")
    runner.mirror([event, event, deepcopy(event)])
    assert len(runner.mirrored) == 1, "the same order id is mirrored once"
    broken = rs.MirroredAction("m000-t00-1-fluid", 0, "fluid", {}, {}, 0.21, "t0:1", "t0")
    runner.mirror([broken])
    assert runner.advance(5) is False, "a fluid with no volume must not pass silently"
    assert runner.results == [] and runner.failures


@pytest.mark.parametrize("error,classification", [(CoreInvariantError("broken"), rs.UNEXPECTED),
                                                  (UnresolvedBoundary("unmapped"), rs.BOUNDARY),
                                                  (RuntimeError("anything"), rs.MAPPING_GAP)])
def test_u18_a_core_failure_is_captured_classified_and_the_encounter_goes_on(monkeypatch, error,
                                                                             classification):
    from clinical_core import integration
    encounter = _play(CASE, ())
    session = encounter.shadow
    monkeypatch.setattr(integration, "run", lambda *args, **kwargs: (_ for _ in ()).throw(error))
    before = deepcopy(encounter.state)
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        entry = encounter.order(TURNS[0])
    assert entry["executed"], "the legacy encounter must run whatever the shadow did"
    assert encounter.state["observable"] != before["observable"] or encounter.state["sim_time"] > 0
    assert [item.classification for item in session.failures][-1:] == [classification]


def test_u19_a_state_that_cannot_be_copied_is_recorded_not_raised():
    class Hostile:
        def __deepcopy__(self, memo):
            raise RuntimeError("this state refuses to be copied")

    session = rs.ShadowSession.start({"engine_family": "gi_bleed"}, environ={rs.FLAG: rs.MODE_SHADOW_COMPARE})
    assert session.capture({"sim_time": 0, "hidden": Hostile()}) is None
    assert [item.where for item in session.failures][-1] == "capture"


def test_u20_an_unsupported_action_is_a_gap_and_the_encounter_is_untouched():
    off = _play(CASE, ("Give tranexamic acid 1 g IV. Reassess in 10 minutes.",), None)
    on = _play(CASE, ("Give tranexamic acid 1 g IV. Reassess in 10 minutes.",))
    assert ev.authoritative(off) == ev.authoritative(on)
    kinds = {str(gap.get("kind")) for gap in on.shadow.gaps}
    assert kinds and all(kind != "None" for kind in kinds), on.shadow.gaps


# -- P3-11-14, P3-11-15: the flag matrix and the pilot -----------------------------------------------------

@pytest.mark.parametrize("environ,opens", [({}, False), ({rs.FLAG: ""}, False), ({rs.FLAG: "nonsense"}, False),
                                           ({rs.FLAG: "off"}, False), ({rs.FLAG: "authority"}, False),
                                           ({rs.FLAG: rs.MODE_SHADOW_COMPARE}, True)])
def test_u21_only_the_one_valid_mode_opens_a_session(environ, opens):
    import pilot_acceptance
    session = rs.ShadowSession.start({"engine_family": "gi_bleed"}, environ=environ)
    assert (session is not None) is opens, environ
    with ev.shadow(environ.get(rs.FLAG)):
        encounter = pilot_acceptance.Encounter(CASE)
    assert (encounter.shadow is not None) is opens, environ


def test_u22_a_clean_pilot_environment_opens_no_session_and_the_freeze_is_untouched():
    import pilot_freeze
    from clinical_core import calibration
    with ev.shadow(None):
        import pilot_acceptance
        assert pilot_acceptance.Encounter(CASE).shadow is None
    # The preflight still cannot gain a row for the flag: pilot_freeze.py is inside the Phase-2
    # calibration freeze, so the protection is that no pilot surface names it (PILOT_PREFLIGHT_FLAG_GATE
    # _DEFERRED, TD-130).
    assert "pilot_freeze.py" in calibration.INPUT_PATH_SOURCES
    assert rs.FLAG not in pilot_freeze.RUNTIME_FLAGS
    for name in ("pilot_freeze.py", "tools_pilot_preflight.py", "docs/RUNBOOK_PILOTO.md"):
        path = ROOT / name
        if path.exists():
            assert rs.FLAG not in path.read_text(encoding="utf-8"), name


# -- P3-11-16: the app-layer hook -------------------------------------------------------------------------

class _SessionState(dict):
    """Streamlit's session_state as the hook uses it: attribute access over a mapping."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as missing:
            raise AttributeError(name) from missing

    def __setattr__(self, name, value):
        self[name] = value


def test_u23_the_app_hook_opens_drops_and_keeps_one_session_per_encounter(monkeypatch):
    """P3-11-16: the exact ``app.py`` hook path, driven deterministically and without a browser.

    Nothing is rendered by the shadow, so there is no screen to drive: what needed coverage was this
    helper's own behaviour -- open on the flag, one session per encounter, dropped when the case changes.
    """
    import app
    import pilot_acceptance

    class Stub:
        def __init__(self, state):
            self.session_state = _SessionState(state=state)

    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        first, second = pilot_acceptance.Encounter(CASE), pilot_acceptance.Encounter("gi_bleed_72f")
        stub = Stub(first.state)
        monkeypatch.setattr(app, "st", stub)
        opened = app._runtime_shadow_session()
        assert opened is not None and opened.case_id == CASE
        assert app._runtime_shadow_session() is opened, "one session per encounter, not one per turn"
        assert stub.session_state["phase3_shadow"] is opened
        stub.session_state["state"] = second.state
        moved = app._runtime_shadow_session()
        assert moved is not opened and moved.case_id == "gi_bleed_72f"
    with ev.shadow(None):
        stub.session_state.pop("phase3_shadow", None)
        assert app._runtime_shadow_session() is None, "the flag off opens nothing in the app layer either"


def test_u24_the_app_call_site_observes_after_the_engine_and_reads_the_settled_list():
    """The two lines in ``app.py``: capture before ``execute_bundle``, observe the settled actions after."""
    tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
    function = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                    and node.name == "_process_encounter_submission_turn")        # P3-271 (declared adaptation): the turn body moved under the authority turn
    found: dict = {"capture": [], "execute": [], "observe": [], "settle": []}
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("capture", "observe", "settle"):
            found[node.func.attr].append(node.lineno)
            if node.func.attr == "observe":
                names = [argument.id for argument in node.args if isinstance(argument, ast.Name)]
                assert "run_actions" in names, names
        if getattr(node.func, "id", "") == "execute_bundle":
            found["execute"].append(node.lineno)
    assert all(found.values()), found
    assert len(found["capture"]) == len(found["observe"]) == len(found["execute"]) == 1, found
    capture, execute, observe = found["capture"][0], found["execute"][0], found["observe"][0]
    # The order is the whole claim: the shadow copies the state before the engine runs, observes only
    # after it committed the turn, and the order pipeline still settles the turn after that.
    assert capture < execute < observe, found
    assert any(line > observe for line in found["settle"]), found


# -- P3-11-17, P3-11-18: cost ------------------------------------------------------------------------------

def test_u25_the_double_run_costs_what_it_costs_and_nothing_pathological(evidence):
    for case in evidence["cases"]:
        timing = case["timing"]
        assert timing["legacy_s"] > 0 and timing["ratio"] is not None
        # No threshold is chosen here (none is authorized): only a pathological order of magnitude fails.
        assert timing["ratio"] < 4, timing


def test_u26_the_artifacts_of_a_whole_battery_are_small_and_the_default_is_the_minimal_trace(evidence):
    totals = ev.artifact_totals(evidence)
    assert totals["scenarios"] == 34
    assert 0 < totals["replay_input_bytes"] < totals["minimal_trace_bytes"] < totals["verbose_trace_bytes"]
    assert totals["verbose_trace_bytes"] < 4_000_000, totals
    assert "minimal" in totals["retention_default"]


# -- P3-11-19: the matrix, and the Phase-2 freeze ----------------------------------------------------------

def test_u27_the_scenario_matrix_says_everything_the_decision_needs(evidence):
    rows = evidence["matrix"]
    assert len(rows) == 34
    for row in rows:
        assert set(row) == {"scenario", "case", "actions", "snapshots", "live_equals_replay",
                            "authority_unchanged", "comparable_domains", "partially_comparable",
                            "divergence_classes", "boundaries", "shadow_failures", "gaps",
                            "unexpected", "replay_artifact_valid"}
        assert row["shadow_failures"] == [], row["shadow_failures"]
        assert row["live_equals_replay"] and row["authority_unchanged"] and row["replay_artifact_valid"]
        assert row["unexpected"] == 0
        assert row["snapshots"] == ["gi_committed_default"], row["snapshots"]
        assert "HEMODYNAMICS" in row["comparable_domains"]


def test_u28_the_phase2_closure_digest_is_unchanged():
    import hashlib
    package = ROOT / "clinical_core"
    sources = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
               for path in package.rglob("*.py")
               if "__pycache__" not in path.parts and path.is_file() and not path.name.startswith(".")}
    # PHASE2_AMENDMENT_1: the live tree is the closure's successor. The closure itself is what must be unchanged,
    # and it is rebuilt from these same live sources by reversing the successor's declared insertions.
    from clinical_core import amendment_1 as a1
    from clinical_core import amendment_2 as a2
    closure = a2.closure_sources_of(sources)
    assert len(closure) == 141 and len(sources) == 144
    digest = hashlib.sha256(json.dumps(closure, sort_keys=True).encode("utf-8")).hexdigest()
    assert digest == rs.PHASE2_DIGEST
    live = hashlib.sha256(json.dumps(sources, sort_keys=True).encode("utf-8")).hexdigest()
    assert live != rs.PHASE2_DIGEST and live == rs.CORE_LINEAGE[-1].digest
    assert not (ROOT / "clinical_core" / "runtime_shadow.py").exists()


def test_u29_no_clinical_magnitude_is_approved_by_this_package():
    from clinical_core import calibration
    approved = [name for name, entry in calibration.REGISTRY.items()
                if getattr(entry, "faculty_approved", False)]
    assert approved == []
    snapshot = fam.ADAPTERS["gi_bleed"].snapshot()
    assert snapshot.point == fam.COMMITTED and snapshot.provenance
    assert "no band" in " ".join(snapshot.provenance)


def test_u30_the_evidence_module_introduces_no_randomness_into_a_shadow_result():
    """It may read the clock to time a battery; the shadow result may not depend on it."""
    tree = ast.parse((ROOT / "runtime_shadow_evidence.py").read_text(encoding="utf-8"))
    names = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
             for alias in node.names}
    assert not {"random", "secrets", "datetime", "clinical_physiology"} & names, sorted(names)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "time":
            assert node.func.attr == "perf_counter", ast.dump(node.func)


# -- P3-11-5: the named region witnesses -------------------------------------------------------------------

def test_u31_the_region_is_read_from_the_frozen_registry_and_approves_nothing():
    import dataclasses
    from clinical_core import calibration
    from clinical_core.derived import DEFAULT_PROFILE
    region = fam.registry_region()
    assert len(region) == 29, sorted(region)
    for name, entry in region.items():
        assert entry.target == "profile" and float(entry.upper) > float(entry.lower), name
        assert getattr(DEFAULT_PROFILE, name) is not None, name
        assert entry.status == "CANDIDATE", (name, entry.status)
    held = [name for name, entry in calibration.REGISTRY.items()
            if entry.target == "profile" and entry.lower is not None
            and float(entry.lower) == float(entry.upper)]
    assert held and not (set(held) & set(region)), "a held magnitude is not a region"
    fields = {field.name for field in dataclasses.fields(DEFAULT_PROFILE)}
    assert set(region) <= fields


def test_u32_a_witness_never_turns_on_a_mechanism_the_committed_profile_leaves_off():
    from clinical_core.derived import DEFAULT_PROFILE
    off = [name for name in ("collapse_output_threshold", "collapse_burden_limit",
                             "collapse_repayment_tau_min")
           if getattr(DEFAULT_PROFILE, name, "missing") is None]
    assert off, "this test exists because Phase 2 leaves the collapse layer off by default"
    for point in ("lower", "midpoint", "upper", fam.COMMITTED):
        profile = fam.ADAPTERS["gi_bleed"].profile(point)
        for name in off:
            assert getattr(profile, name) is None, (point, name)


def test_u33_the_committed_point_sits_on_a_region_edge_for_four_magnitudes():
    """Why a point is not enough: for these four the committed value IS an edge of its own region."""
    notes = fam.region_notes()
    edges = {name: item["where"] for name, item in notes.items() if item["where"] != "midpoint"}
    assert edges == {"lactate_per_output_deficit": "lower edge",
                     "hypoxaemia_threshold_spo2": "upper edge",
                     "pump_preload_coupling": "upper edge",
                     "lactate_clearance_tau_min": "inside, off the midpoint"}, edges


def test_u34_every_scenario_carries_three_named_witnesses_and_a_position(scenarios):
    allowed = {fam.WITHIN, fam.OUTSIDE, fam.REGION_DISABLED, fam.NOT_COMPARABLE}
    for scenario in scenarios:
        region = scenario["region"]
        assert region["status"] == "RUN", (scenario["scenario"], region.get("why"))
        assert region["snapshots"] == ["gi_region_lower", "gi_committed_default", "gi_region_upper"]
        assert region["widths"], scenario["scenario"]
        assert region["minutes"] == sorted(scenario["compared_minutes"]), scenario["scenario"]
        assert set(region["positions"]) == set(region["minutes"]), scenario["scenario"]
        for reading in region["positions"].values():
            for name, item in reading.items():
                assert item["status"] in allowed, (name, item)
        for name, item in region["legacy_against_region"].items():
            assert item["status"] in allowed, (name, item)


def test_u35_the_region_changes_what_the_comparison_means(evidence):
    """The reading a point comparison could not give: most pressures are INSIDE the common region.

    The golden declares sbp, dbp and map architectural differences in every GI scenario, and they are --
    against the committed point. Against the declared region they sit inside it in all but a few minutes,
    so part of what reads as architecture is parameter uncertainty. Neither engine is ground truth here.
    """
    table = evidence["legacy_against_region"]
    minutes = evidence["compared_minutes"]
    agreement = evidence["within_by_agreement"]
    assert minutes == 82, minutes
    for name in table:
        assert sum(table[name].values()) == minutes, (name, minutes, table[name])
        assert agreement.get(name, 0) <= minutes, (name, agreement.get(name))
    for name in ("sbp", "dbp", "map"):
        assert table[name].get(fam.WITHIN, 0) >= 0.9 * minutes, (name, table[name])
        # And not because they are identical: the minutes whose legacy value had to be taken from the
        # structural witness (they agreed) are counted apart, so they cannot inflate the reading.
        assert agreement.get(name, 0) <= 0.1 * minutes, (name, agreement.get(name))
    assert table["crt"].get(fam.WITHIN, 0) >= 0.8 * minutes, table["crt"]
    # The respiratory rate is the opposite reading, and the region does not rescue it: the legacy rate is
    # authored where the common one is driven (P2K-1, P2K-2), which is architecture, not uncertainty.
    assert table["respiratory_rate"].get(fam.OUTSIDE, 0) >= 40, table["respiratory_rate"]
    assert table["respiratory_rate"].get(fam.WITHIN, 0) <= 0.1 * minutes, table["respiratory_rate"]
    assert table["spo2"] == {fam.REGION_DISABLED: minutes}, table["spo2"]
    assert table["hr"].get(fam.REGION_DISABLED, 0) > 0 and table["hr"].get(fam.WITHIN, 0) > 0
    assert set(agreement) <= {name for name, *_ in ev.POSITION_VARIABLES}, agreement


# -- the negative control: every safety check must be able to fail ----------------------------------------

def test_u36_each_safety_check_can_actually_fail():
    """A check that cannot fail certifies nothing. Each one is tripped on purpose here.

    The scenarios of the real battery report every check as False; this test shows that False is a reading
    and not a property of the code: a perturbed authoritative record, a clock that disagrees, a duplicated
    mirrored action and a replay that does not match all turn their own check True.
    """
    off = _play(CASE, TURNS[:1], None)
    on = _play(CASE, TURNS[:1])
    clean = ev.scenario_evidence("control", CASE, TURNS[:1], off, on)
    assert not any(clean["safety"].values()), clean["safety"]

    # 1 and 2: the authoritative record and the persistence differ
    perturbed = _play(CASE, TURNS[:1])
    perturbed.state["observable"] = {**perturbed.state["observable"], "sbp": 1}
    tripped = ev.scenario_evidence("control", CASE, TURNS[:1], off, perturbed)
    assert tripped["safety"]["authoritative_record_differs"]
    assert tripped["safety"]["persistence_differs"]

    # 3: the clocks disagree
    late = _play(CASE, TURNS[:1])
    late.state["sim_time"] = int(late.state["sim_time"]) + 7
    assert ev.scenario_evidence("control", CASE, TURNS[:1], off, late)["safety"][
        "minute_alignment_differs"]

    # 4: an action mirrored twice
    doubled = _play(CASE, TURNS[:1])
    doubled.shadow.mirrored.append(doubled.shadow.mirrored[0])
    assert ev.scenario_evidence("control", CASE, TURNS[:1], off, doubled)["safety"]["action_duplicated"]

    # 5: the replay does not match the live run
    moved = _play(CASE, TURNS[:1])
    moved.shadow.runner.results[-1] = type(moved.shadow.runner.results[-1])(
        moved.shadow.runner.results[-1].minute, "not the digest the core produced",
        moved.shadow.runner.results[-1].derived)
    assert ev.scenario_evidence("control", CASE, TURNS[:1], off, moved)["safety"][
        "replay_differs_from_live"]

    # 6: the order fates differ
    refated = _play(CASE, TURNS[:1])
    refated.entries[-1]["orders"] = [{**order, "fate": "SOMETHING_ELSE"}
                                     for order in refated.entries[-1]["orders"]]
    assert ev.scenario_evidence("control", CASE, TURNS[:1], off, refated)["safety"]["order_fates_differ"]


# -- what the adversarial review of P3-11 found, and what now holds ---------------------------------------

def test_v1_a_deployment_secret_cannot_turn_the_shadow_on(monkeypatch):
    """Streamlit copies every secret into ``os.environ``, so reading the environment alone is not a gate.

    The pilot's preflight cannot carry a row for this flag (``pilot_freeze.py`` is inside the Phase-2
    calibration freeze), so this is the gate that replaces it: a flag that comes from a secrets file is
    not honoured, whatever the environment says.
    """
    monkeypatch.setenv(rs.FLAG, rs.MODE_SHADOW_COMPARE)
    assert rs.mode() == rs.MODE_SHADOW_COMPARE, "the process environment still turns it on"
    monkeypatch.setattr(rs, "_named_in_secrets", lambda name: name == rs.FLAG)
    assert rs.mode() == rs.MODE_OFF, "a Secret of this name must not enable the shadow"
    assert not rs.enabled_for("gi_bleed")
    assert rs.ShadowSession.start({"engine_family": "gi_bleed", "sim_time": 0}) is None
    # And the check cannot be the reason the off path fails: with the flag absent it is never consulted.
    monkeypatch.delenv(rs.FLAG, raising=False)
    monkeypatch.setattr(rs, "_named_in_secrets", lambda name: (_ for _ in ()).throw(RuntimeError("boom")))
    assert rs.mode() == rs.MODE_OFF


def test_v2_a_session_never_opens_in_the_middle_of_an_encounter():
    """Opening at minute N would read the arrival from a treated patient and lose every order before it."""
    import pilot_acceptance
    with ev.shadow(None):
        encounter = pilot_acceptance.Encounter(CASE)
        encounter.order(TURNS[0])
    assert encounter.shadow is None and int(encounter.state["sim_time"]) > 0
    # P3-147: the refusal used to be silent (no session at all). It is now a session that RUNS NOTHING and
    # says why, so a faculty reader can see that this encounter was legacy-only. What the test protects --
    # no run ever opens on a patient time has already passed for -- is protected, and now visibly.
    refused = rs.ShadowSession.start(encounter.state, environ={rs.FLAG: rs.MODE_SHADOW_COMPARE})
    assert refused is not None and refused.runner is None and refused.ensemble is None
    assert [failure.exception for failure in refused.failures] == [rs.ARRIVAL_REJECTED]
    assert refused.eligibility["conditions"]["clock_at_arrival"] is False
    assert refused.record()["minutes"] == [] and refused.record()["replay_input"] is None
    fresh = {"engine_family": "gi_bleed", "sim_time": 0}
    assert rs.ShadowSession.start(fresh, environ={rs.FLAG: rs.MODE_SHADOW_COMPARE}) is not None


def test_v3_a_second_attempt_at_the_same_case_does_not_inherit_the_first_run():
    """A case id is not an encounter: the clock is what separates two attempts at the same case."""
    import pilot_acceptance
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        first = pilot_acceptance.Encounter(CASE)
        first.order(TURNS[0])
        session = first.shadow
        assert session.is_for(first.state), "the live encounter keeps its session"
        again = pilot_acceptance.Encounter(CASE)
        assert not session.is_for(again.state), "a second attempt must drop it"
        assert not session.is_for(pilot_acceptance.Encounter("gi_bleed_72f").state)
    record = session.record()
    assert record["encounter_id"] and len(record["encounter_id"]) == 64
    # And this is WHY the clock is the discriminator: the generator is deterministic, so the arrival of
    # the second attempt is byte-identical to the first and the digest cannot tell them apart.
    assert record["encounter_id"] == rs._encounter_id(session.arrival)
    assert rs._encounter_id(again.state) == record["encounter_id"]
    # The clock going backwards is refused even for the same encounter.
    backwards = dict(first.state)
    backwards["sim_time"] = 0
    assert not session.is_for(backwards)


def test_v4_a_turn_whose_before_state_could_not_be_copied_mirrors_nothing_and_says_so():
    """Dating those actions at minute zero would move a treatment to the arrival; the gap says why."""
    import pilot_acceptance
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = pilot_acceptance.Encounter(CASE)
        encounter.order("Reassess in 20 minutes.")
        session = encounter.shadow
        session.capture = lambda state: None
        encounter.order("Give 1 litre of normal saline over 15 minutes. Reassess in 10 minutes.")
    assert not [event for event in session.mirrored if event.kind == "fluid"], \
        [event.kind for event in session.mirrored]
    assert any("could not be copied" in str(gap.get("why")) for gap in session.gaps), session.gaps


def test_v5_the_artifact_carries_the_digest_of_the_golden_that_classified_it():
    """Every divergence class here is read from the committed golden; no other digest covers that file."""
    import hashlib
    runner = fam.ShadowPhysiologyRunner.open("gi_bleed", CASE)
    runner.advance(5)
    versions = runner.replay_input().versions
    expected = hashlib.sha256((ROOT / "clinical_core" / "golden" / "gi_bleed_shadow.json")
                              .read_bytes()).hexdigest()
    assert versions["golden_digest"] == expected
    assert rs.golden_digest("not_a_family") == "missing"


def test_v6_the_phase2_digest_condition_is_computed_and_can_fail(monkeypatch):
    """Comparing the constant with itself would make the condition true by construction."""
    assert ev.historical_closure_digest_now() == rs.PHASE2_DIGEST
    assert ev.phase2_digest_now() in {version.digest for version in rs.CORE_LINEAGE}
    off = _play(CASE, TURNS[:1], None)
    on = _play(CASE, TURNS[:1])
    monkeypatch.setattr(ev, "phase2_digest_now", lambda: "a different digest")
    tripped = ev.scenario_evidence("control", CASE, TURNS[:1], off, on)
    assert tripped["safety"]["phase2_digest_changed"] and not tripped["safe"]


def test_v7_a_region_reading_says_how_many_witnesses_it_spans(scenarios):
    """OUTSIDE means outside the span of the named witnesses, not outside the declared region."""
    for scenario in scenarios:
        for reading in scenario["region"]["positions"].values():
            for name, item in reading.items():
                if item["status"] in (fam.WITHIN, fam.OUTSIDE, fam.REGION_DISABLED):
                    assert item["witnesses"] == 3, (name, item)


def test_v8_a_difference_the_golden_declares_in_only_some_scenarios_blocks_the_reading(evidence):
    """The golden explains a difference in the scenarios it declares it in, and not in the others."""
    partially = evidence["partially_explained"]
    assert set(partially) == {"hr", "crt_s", "V_ml_eq", "consciousness_level"}, sorted(partially)
    for name, item in partially.items():
        assert item["minutes"] > 0 and item["scenarios"]
        assert 0 < item["seen"] < item["total"] == 20, (name, item)
        assert item["declaring_scenarios"] and item["silent_scenarios"], name
    assert partially["consciousness_level"]["seen"] == 1, partially["consciousness_level"]
    assert any(blocker.startswith("PARTIALLY_EXPLAINED_DIVERGENCE_REQUIRES_A_READING")
               for blocker in evidence["blockers"]), evidence["blockers"]
    assert evidence["readiness"] == "GI_FULL_LIVE_SHADOW_EVIDENCE_NOT_READY"
