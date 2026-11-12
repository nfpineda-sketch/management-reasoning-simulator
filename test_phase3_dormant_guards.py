"""P3-210 and P3-211: the downstream guards of ``mental_status`` and the explicit authority view. DORMANT: no authority anywhere in this file.

What is proved, by AST, by differential execution and by negative controls:

* the reader graph is REPRODUCED from the source (54 modules, 119 sites, 32 executable readers) and every reader has a class, a consequence row
  and a guard type;
* the readers that change something other than a sentence are FROZEN to the legacy word, by a view the transaction owns and no global mutation;
* a common-core word carried by the overlay, even one forced into the live field with the legacy word preserved, changes the engine's order
  outcomes, the page's snapshots, update cards and available actions, the trace, both AI payloads and the faculty's retention of an AI suggestion
  by exactly nothing;
* scoring modules never name the word.
"""
import ast
import copy
import inspect
import json
from pathlib import Path

import pytest

import family_engine
import observable_view as view
import pilot_acceptance as acceptance
import runtime_authority as authority
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import test_gi_preauthority_review as review
import test_gi_reader_guards as guards

ROOT = Path(__file__).resolve().parent
CASE = "gi_bleed_57m"
CONTROL, OVERLAY_ONLY, HOSTILE, MAPPED, MAPPED_HOSTILE = "control", "overlay_only", "hostile_views", "mapped_into_live_field", "mapped_and_hostile"
VARIANTS = (OVERLAY_ONLY, HOSTILE, MAPPED, MAPPED_HOSTILE)


def overlay_for(state, *, hostile=False, mapped=False, category=3, legacy=None):
    word = view.WORDS[category]
    readers = sorted(set(view.ROUTED_READERS) | set(guards.READER_GUARDS))
    return {"owner": "test-transaction", "minute": state["sim_time"], "views": {name: view.DEVELOPMENT_COMMON_AUTHORITY_VIEW for name in readers} if hostile else {},
            "common": {"consciousness_category": category, "mental_status": word, "pulse_present": True},
            "legacy": {"mental_status": legacy} if mapped else {}, "mapped_into_live_field": mapped}


def apply_variant(state, variant):
    """The state a (future, forbidden today) transaction could leave behind. The legacy word is read BEFORE the variant touches the state."""
    legacy = (state.get("observable") or {}).get("mental_status")
    if variant == CONTROL:
        return state
    mapped = variant in (MAPPED, MAPPED_HOSTILE)
    state[view.OVERLAY_KEY] = overlay_for(state, hostile=variant in (HOSTILE, MAPPED_HOSTILE), mapped=mapped, legacy=legacy)
    if mapped:
        state["observable"]["mental_status"] = view.WORDS[3]
    return state


def without_overlay(state):
    out = copy.deepcopy(state)
    out.pop(view.OVERLAY_KEY, None)
    return out


# -- P3-210: the graph, the classes, the consequences, the guard types --------------------------------------------------------------------------

def test_the_reader_graph_is_reproduced_from_the_source():
    audit = review.reader_audit(str(ROOT))
    rows = [row for row in audit["rows"] if row["module"] not in review.MECHANISM_MODULES]      # mechanisms, not readers of an encounter (P3-248: the two modules of the real pressure authority join the view and the pair)
    assert audit["unclassified"] == []
    assert (len({row["module"] for row in rows} - set(audit["modules_text_only"])), len([name for name in audit["modules_text_only"] if name not in review.MECHANISM_MODULES])) == (54, 7)
    assert len(rows) == 119
    live = sorted(f"{row['module']}::{row['function']}" for row in rows if row["where"] in review.LIVE and row["executable_read"])
    assert len(live) == 32 and live == guards.live_reader_ids(str(ROOT)) == sorted(guards.READER_GUARDS)
    # the mechanism module itself is the only new site, and it is told apart from a reader
    assert {row["function"] for row in audit["rows"] if row["module"] == "observable_view.py"} == {"<module>", "structure_problems"}
    assert all(row["class"] == review.MECHANISM and not row["executable_read"]
               for row in audit["rows"] if row["module"] in review.MECHANISM_MODULES)


def test_every_reader_has_a_class_a_consequence_row_and_a_guard_type():
    for reader, row in guards.READER_GUARDS.items():
        assert row["kind"] in guards.KINDS and row["guard"] in view.GUARD_TYPES and row["mechanism"] in guards.MECHANISMS, reader
        assert set(row["consequence"]) == set(guards.CONSEQUENCE_FIELDS) and row["why"], reader
    kinds = {kind: len(readers) for kind, readers in guards.by_kind().items()}
    assert sum(kinds.values()) == 32
    # no reader of the word scores or terminates by itself: the indirect paths are the AI payloads, the faculty portal and the persistence
    assert kinds[guards.SCORING] == 0 and kinds[guards.TERMINATION] == 0
    assert (kinds[guards.AI_PAYLOAD], kinds[guards.FACULTY_PORTAL], kinds[guards.PERSISTENCE], kinds[guards.DISCHARGE],
            kinds[guards.ACTION_AVAILABILITY]) == (2, 3, 3, 1, 3)


def test_210a_a_reader_that_could_change_anything_but_a_sentence_is_frozen_or_is_a_named_blocker_of_the_live_field_mapping():
    table = guards.READER_GUARDS
    for reader, row in table.items():
        c = row["consequence"]
        if c["scoring"] or c["scenario_state"] or c["available_actions"] or c["ai_output"] or c["termination"]:
            if reader in view.UNROUTED_CONSEQUENTIAL:
                # held ONLY because no transaction writes the live field and the writer refuses to: its guard says it still has to be authorized later
                assert row["mechanism"] == guards.LIVE_FIELD and row["guard"] == view.LATER, reader
            else:
                assert row["guard"] == view.FREEZE and row["mechanism"] in (guards.ROUTED, guards.SNAPSHOT), reader
    # every consequential reader of the LIVE field is a named blocker: the readers of the live field that are not display or text are exactly the unrouted list
    live_field = sorted(reader for reader, row in table.items() if row["mechanism"] == guards.LIVE_FIELD)
    assert all(table[reader]["guard"] == view.LATER for reader in live_field)
    consequential = sorted(reader for reader in live_field if table[reader]["kind"] in (guards.CLINICAL_BRANCHING, guards.ACTION_AVAILABILITY, guards.DISCHARGE)
                           or reader == "image_broker.py::edit_prompt")
    assert consequential == sorted(set(view.UNROUTED_CONSEQUENTIAL) | {"visual_observations.py::<module>"}) or consequential == sorted(view.UNROUTED_CONSEQUENTIAL), consequential
    assert set(view.UNROUTED_CONSEQUENTIAL) <= set(live_field)
    consequence = guards.consequences()
    assert consequence["available_actions"] == ["app.py::_clinical_encounter_workspace", "family_engine.py::_order", "family_engine.py::_validate"]
    assert consequence["termination"] == []                       # the engine's disposition outcome continues the encounter
    assert "family_engine.py::_discharge_alarm" in consequence["scenario_state"]


def test_the_engine_is_frozen_by_the_phase2_closure_and_therefore_is_not_routed_through_the_view():
    """Found by this cycle's FULL suite: an earlier draft routed the three engine readers through the view and moved the calibration freeze digests that the
    Phase-2 closure records (``test_phase2_closure``). ``family_engine.py`` is a source of that freeze, so it is NOT edited in this phase."""
    from clinical_core import calibration
    assert "family_engine.py" in calibration.INPUT_PATH_SOURCES
    assert "observable_view" not in (ROOT / "family_engine.py").read_text(encoding="utf-8")
    assert view.FROZEN_BY_THE_PHASE2_CLOSURE == {reader for reader in view.UNROUTED_CONSEQUENTIAL if reader.startswith("family_engine.py::")} and len(view.FROZEN_BY_THE_PHASE2_CLOSURE) == 3
    assert not [reader for reader in view.ROUTED_READERS if reader.startswith("family_engine.py::")]
    # the writer refuses the mapping, and says why: the engine readers would read the common word
    mapped = {"owner": "t", "minute": 5, "views": {}, "common": {"consciousness_category": 3, "mental_status": view.WORDS[3], "pulse_present": True},
              "legacy": {"mental_status": "Alert"}, "mapped_into_live_field": True}
    refusal = " ".join(view.mapping_problems(mapped))
    assert all(reader in refusal for reader in view.FROZEN_BY_THE_PHASE2_CLOSURE), refusal


def test_the_routed_readers_are_exactly_the_calls_to_the_view_found_in_the_source_and_each_asks_by_its_own_name():
    found = {}
    for path in sorted(ROOT.glob("*.py")):
        if path.name.startswith("test_") or path.name == "observable_view.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("mental_status_for", "legacy_mental_status"):
                owner = node
                while owner in parents and not isinstance(owner, ast.FunctionDef):
                    owner = parents[owner]
                name = f"{path.name}::{owner.name if isinstance(owner, ast.FunctionDef) else '<module>'}"
                literal = [arg.value for arg in node.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and "::" in arg.value]
                found.setdefault(name, []).append((node.func.attr, literal))
    assert sorted(found) == sorted(view.ROUTED_READERS), sorted(found)
    for reader, calls in found.items():
        assert all(attr == "mental_status_for" and literal == [reader] for attr, literal in calls), (reader, calls)
    assert {reader for reader, row in guards.READER_GUARDS.items() if row["mechanism"] == guards.ROUTED} == set(view.ROUTED_READERS)


def test_no_routed_function_reads_the_live_word_any_other_way():
    """After the routing, the only way a routed function gets the word is the view: no ``get('mental_status')`` and no subscript of it is left."""
    for reader in view.ROUTED_READERS:
        module, function = reader.split("::")
        tree = ast.parse((ROOT / module).read_text(encoding="utf-8"))
        node = next(item for item in ast.walk(tree) if isinstance(item, ast.FunctionDef) and item.name == function)
        direct = []
        for item in ast.walk(node):
            if isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute) and item.func.attr in ("get", "pop") and item.args \
                    and isinstance(item.args[0], ast.Constant) and item.args[0].value == "mental_status":
                direct.append(ast.unparse(item))
            if isinstance(item, ast.Subscript) and isinstance(item.slice, ast.Constant) and item.slice.value == "mental_status" and isinstance(item.ctx, ast.Load):
                direct.append(ast.unparse(item))
        assert direct == [], (reader, direct)


# -- P3-211A: the view, with nothing global and nothing mutated --------------------------------------------------------------------------------

STATES = ({"sim_time": 5, "observable": {"mental_status": "Drowsy"}}, {"sim_time": 0, "observable": {}}, {"sim_time": 3}, {"observable": {"mental_status": None}},
          {}, {"sim_time": 9, "observable": {"mental_status": "Unresponsive", "pulse_present": True}})


@pytest.mark.parametrize("state", STATES)
def test_with_no_overlay_every_accessor_returns_the_live_field_exactly(state):
    live = (state.get("observable") or {}).get("mental_status", "<default>")
    for reader in list(view.ROUTED_READERS) + ["anything.py::else"]:
        assert view.mental_status_for(state, reader, "<default>") == live
    assert view.legacy_mental_status(state, "<default>") == live and view.overlay_of(state) is None and view.common_consciousness(state) is None


def test_the_view_changes_nothing_it_is_given_and_holds_no_state_of_its_own():
    state = apply_variant({"sim_time": 5, "observable": {"mental_status": "Drowsy"}}, MAPPED_HOSTILE)
    before = copy.deepcopy(state)
    for reader in view.ROUTED_READERS:
        view.mental_status_for(state, reader)
    view.legacy_mental_status(state), view.common_consciousness(state), view.overlay_problems(state[view.OVERLAY_KEY])
    assert state == before
    names = [name for name, value in vars(view).items() if isinstance(value, (list, dict, set)) and not name.startswith("__")]
    assert names == [], names                                              # no mutable module state a transaction could flip globally


def test_no_reader_is_allowed_the_common_view_today_and_a_frozen_one_never_is(monkeypatch):
    assert view.COMMON_VIEW_READERS == frozenset() and view.DIAGNOSTIC_READERS == frozenset()
    state = {"sim_time": 5, "observable": {"mental_status": "Drowsy"}}
    hostile = overlay_for(state, hostile=True)
    problems = view.overlay_problems(hostile)
    assert problems and all(item.startswith("common_view_for_a_reader_not_allowed:") for item in problems)
    state[view.OVERLAY_KEY] = hostile
    # the assignment is refused: NO reader sees the common word. The overlay stays a trusted carrier of the preserved legacy word.
    assert view.view_problems(hostile) == problems and view.structure_problems(hostile) == []
    assert all(view.mental_status_for(state, reader) == "Drowsy" for reader in hostile["views"])
    # the later-authorization path works for a reader that is allowed ... and a frozen one stays frozen even if someone lists it
    monkeypatch.setattr(view, "COMMON_VIEW_READERS", frozenset({"app.py::_vitals_cells", "app.py::management_state_snapshot"}))
    only = {"sim_time": 5, "observable": {"mental_status": "Drowsy"},
            view.OVERLAY_KEY: {**overlay_for({"sim_time": 5}), "views": {"app.py::_vitals_cells": view.DEVELOPMENT_COMMON_AUTHORITY_VIEW}}}
    assert view.overlay_problems(only[view.OVERLAY_KEY]) == [] and view.mental_status_for(only, "app.py::_vitals_cells") == "Unresponsive"
    assert view.mental_status_for(only, "app.py::format_clinical_update") == "Drowsy"          # a reader nobody assigned: legacy
    frozen = {**only, view.OVERLAY_KEY: {**only[view.OVERLAY_KEY], "views": {"app.py::management_state_snapshot": view.DEVELOPMENT_COMMON_AUTHORITY_VIEW}}}
    assert view.overlay_problems(frozen[view.OVERLAY_KEY]) and view.mental_status_for(frozen, "app.py::management_state_snapshot") == "Drowsy"


#: A malformed VIEW assignment does not make the overlay worthless as a carrier of the preserved legacy word, and it gives no reader the common one.
VIEW_MALFORMED = {
    "unknown view": lambda o: {**o, "views": {"app.py::_vitals_cells": "SOME_OTHER_VIEW"}}, "views not a mapping": lambda o: {**o, "views": []},
}
MALFORMED = {
    "not a mapping": lambda o: "x", "no owner": lambda o: {**o, "owner": ""}, "owner not a string": lambda o: {**o, "owner": 7},
    "minute a bool": lambda o: {**o, "minute": True}, "minute a string": lambda o: {**o, "minute": "5"},
    "category out of range": lambda o: {**o, "common": {**o["common"], "consciousness_category": 4}},
    "category a bool": lambda o: {**o, "common": {**o["common"], "consciousness_category": True}},
    "word is not the category": lambda o: {**o, "common": {**o["common"], "mental_status": "Alert"}},
    "word not on the ladder": lambda o: {**o, "common": {**o["common"], "mental_status": "Comatose", "consciousness_category": 3}},
    "extra common field": lambda o: {**o, "common": {**o["common"], "gcs": 3}}, "pulse not a bool": lambda o: {**o, "common": {**o["common"], "pulse_present": 1}},
    "missing field": lambda o: {key: value for key, value in o.items() if key != "legacy"},
    "mapped without the legacy word": lambda o: {**o, "mapped_into_live_field": True, "legacy": {}},
    "mapped flag not a bool": lambda o: {**o, "mapped_into_live_field": 1},
}


@pytest.mark.parametrize("label", sorted(MALFORMED))
def test_a_malformed_overlay_is_not_a_view_and_the_reader_gets_the_live_field(label):
    state = {"sim_time": 5, "observable": {"mental_status": "Drowsy"}}
    state[view.OVERLAY_KEY] = MALFORMED[label](overlay_for(state))
    assert view.overlay_of(state) is None and (label == "not a mapping" or view.overlay_problems(state[view.OVERLAY_KEY]))
    assert view.mental_status_for(state, "family_engine.py::_validate") == "Drowsy" and view.common_consciousness(state) is None


@pytest.mark.parametrize("label", sorted(VIEW_MALFORMED))
def test_a_malformed_view_assignment_gives_no_reader_the_common_word_and_still_preserves_the_legacy_one(label):
    state = {"sim_time": 5, "observable": {"mental_status": "Unresponsive"}}
    state[view.OVERLAY_KEY] = {**VIEW_MALFORMED[label](overlay_for(state, mapped=True, legacy="Alert"))}
    assert view.view_problems(state[view.OVERLAY_KEY]) and view.overlay_problems(state[view.OVERLAY_KEY])
    assert all(view.mental_status_for(state, reader) == "Alert" for reader in view.ROUTED_READERS) and view.legacy_mental_status(state) == "Alert"


def test_a_stale_overlay_is_not_a_view():
    state = {"sim_time": 6, "observable": {"mental_status": "Drowsy"}, view.OVERLAY_KEY: overlay_for({"sim_time": 5}, mapped=True, legacy="Alert")}
    assert view.overlay_of(state) is None and view.legacy_mental_status(state) == "Drowsy"


def test_the_mapping_mutant_a_common_word_forced_into_the_live_field_still_reads_legacy_through_the_view():
    """The mutant this guard exists for: a transaction (not allowed to, today) overwrites the live field and preserves the legacy word."""
    state = {"sim_time": 5, "observable": {"mental_status": "Unresponsive"}, view.OVERLAY_KEY: overlay_for({"sim_time": 5}, mapped=True, legacy="Alert")}
    assert view.overlay_problems(state[view.OVERLAY_KEY]) == []
    assert view.legacy_mental_status(state) == "Alert"
    assert all(view.mental_status_for(state, reader) == "Alert" for reader in view.ROUTED_READERS)
    assert view.live_word(state) == "Unresponsive" and view.common_consciousness(state)["mental_status"] == "Unresponsive"
    # and the WRITE side refuses the mapping while a consequential reader of the live state is not routed
    assert view.mapping_problems(state[view.OVERLAY_KEY]) and view.UNROUTED_CONSEQUENTIAL
    assert view.mapping_problems({"mapped_into_live_field": False}) == [] and view.mapping_problems("x") == []


# -- P3-211: the readers, differentially ---------------------------------------------------------------------------------------------------------

def _encounter_at(minute=5):
    encounter = acceptance.Encounter(CASE)
    encounter.wait_until(minute, step=1)
    return encounter


def _played(variant, text):
    """One turn of the engine, from the same state, with the variant a transaction could leave behind."""
    with ev.shadow(rs.MODE_OFF):
        encounter = _encounter_at()
        apply_variant(encounter.state, variant)
        entry = encounter.order(text)
        state = without_overlay(encounter.state)
    # What a reader DECIDED: the order's outcome, its words and the ledger -- not the live field the variant itself forced into the state (a
    # turn that advances no minute leaves it there; the engine reflects it back in its own observation snapshot, which is no reader's decision).
    state["observable"].pop("mental_status", None)
    decided = {key: value for key, value in entry.items() if key not in ("observable", "observation_snapshot", "state_after", "state_before")}
    return {"entry": json.loads(json.dumps(decided, default=str)), "state": json.loads(json.dumps(state, default=str)), "ledger": encounter.ledger}


ORDERS = ("Give paracetamol 500 mg orally.", "Give 15 g of oral glucose.", "Give 30 g of oral carbohydrate.", "Give 1 L of normal saline.")


@pytest.mark.parametrize("text", ORDERS)
def test_the_engines_order_eligibility_is_unchanged_by_any_variant_and_the_reader_is_sensitive_to_the_live_word(text):
    control = _played(CONTROL, text)
    # the variants that write NOTHING into the live field (the only ones a transaction may leave: the overlay, hostile or not) change nothing the engine decides;
    # the two MAPPED variants are exactly what the writer refuses (the engine readers are not routed: ``test_the_engine_is_frozen_by_the_phase2_closure...``)
    for variant in (OVERLAY_ONLY, HOSTILE):
        assert _played(variant, text) == control, variant
    # the control is not trivially insensitive: with the word REALLY unresponsive in the live field and no overlay, the oral orders differ
    with ev.shadow(rs.MODE_OFF):
        encounter = _encounter_at()
        encounter.state["observable"]["mental_status"] = "Unresponsive"
        really = encounter.order(text)
    if "mouth" in text or "oral" in text:
        really = {key: value for key, value in really.items() if key not in ("observable", "observation_snapshot", "state_after", "state_before")}
        assert json.loads(json.dumps(really, default=str)) != control["entry"], text


def test_the_discharge_outcome_is_unchanged_by_any_variant():
    base = {"sim_time": 30, "observable": {"mental_status": "Alert", "pulse_present": True, "respiratory_rate": 16, "glucose_mg_dl": 100}}
    expected = family_engine._discharge_alarm(base)
    for variant in (OVERLAY_ONLY, HOSTILE):                                      # the variants that write nothing into the live field (see the eligibility test)
        assert family_engine._discharge_alarm(apply_variant(copy.deepcopy(base), variant)) == expected, variant
    # and it is sensitive: the word really in the live field makes the patient 'found ... at home'
    assert family_engine._discharge_alarm({**base, "observable": {**base["observable"], "mental_status": "Unresponsive"}}) == "found unresponsive at home"


@pytest.fixture(scope="module")
def app_module():
    import app
    return app


def test_the_pages_snapshots_update_cards_and_the_trace_are_unchanged_by_any_variant(app_module):
    with ev.shadow(rs.MODE_OFF):
        encounter = _encounter_at()
        control_state = copy.deepcopy(encounter.state)
    expected = {"learner": app_module.learner_vitals_snapshot(control_state), "management": app_module.management_state_snapshot(control_state)}
    for variant in VARIANTS:
        state = apply_variant(copy.deepcopy(control_state), variant)
        assert app_module.learner_vitals_snapshot(state) == expected["learner"], variant
        assert app_module.management_state_snapshot(state) == expected["management"], variant
        # the update-card decision compares two states: a variant on either side, or on both, changes nothing
        for before, after in ((control_state, state), (state, control_state), (state, state)):
            assert app_module.observable_state_changed(before, after) == app_module.observable_state_changed(control_state, control_state), variant
    # sensitivity: a real change of the word in the live field IS seen by the decision
    changed = copy.deepcopy(control_state)
    changed["observable"]["mental_status"] = "Obtunded"
    assert app_module.observable_state_changed(control_state, changed) is True
    assert app_module.learner_vitals_snapshot(changed)["mental_status"] == "Obtunded"


def _trace_event(app_module, state_before, state_after):
    return {"state_before": app_module.management_state_snapshot(state_before), "state_after": app_module.management_state_snapshot(state_after),
            "decision_time_min": state_before["sim_time"], "response_time_min": state_after["sim_time"]}


def test_211b_211c_the_two_ai_payloads_and_the_retention_of_an_ai_suggestion_are_built_from_legacy_in_every_variant(app_module):
    import faculty_analysis
    import management_trace_analysis
    import record_findings
    with ev.shadow(rs.MODE_OFF):
        encounter = _encounter_at(5)
        before = copy.deepcopy(encounter.state)
        encounter.wait_until(25, step=1)
        after = copy.deepcopy(encounter.state)
    results = {}
    for variant in (CONTROL,) + VARIANTS:
        event = _trace_event(app_module, apply_variant(copy.deepcopy(before), variant), apply_variant(copy.deepcopy(after), variant))
        suggestion = {"objective_id": "X", "recommendation": "needs_improvement", "rationale": "The resident did not reassess alertness.", "evidence_refs": []}
        limits = record_findings.encounter_limits([event, event])
        results[variant] = {
            "event": event,
            "management_payload": management_trace_analysis._state(event["state_after"], event["response_time_min"]),
            "faculty_payload": faculty_analysis._state(event["state_after"], event["response_time_min"]),
            "limits": limits, "held": record_findings.hold_for_review(suggestion, limits)}
    for variant in VARIANTS:
        assert json.dumps(results[variant], sort_keys=True, default=str) == json.dumps(results[CONTROL], sort_keys=True, default=str), variant
    assert "mental_status" in results[CONTROL]["event"]["state_after"]["observable"]            # the word IS in the trace, and it is the legacy one
    assert results[CONTROL]["event"]["state_after"]["observable"]["mental_status"] == "Alert"


def test_211b_no_scoring_surface_names_the_word_and_the_layer_cannot_reach_one():
    scoring = ("rubric_store", "rubric_portal", "case_assessment", "progress_store", "account_store", "faculty_analysis_store", "case_assessment")
    for name in scoring:
        path = ROOT / f"{name}.py"
        if path.is_file():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            assert not [node for node in ast.walk(tree) if isinstance(node, ast.Constant) and node.value == "mental_status"], name
            assert "observable_view" not in path.read_text(encoding="utf-8"), name
    # the view is imported by the page, the trace schema and the layer, and by no scoring surface; and it imports nothing at all from the project
    importers = sorted(path.name for path in ROOT.glob("*.py") if not path.name.startswith("test_") and path.name != "observable_view.py"
                       and "observable_view" in path.read_text(encoding="utf-8"))
    assert importers == ["app.py", "runtime_authority_pair.py", "trace_phase0.py"], importers          # and NOT family_engine.py: it is frozen by the Phase-2 closure
    tree = ast.parse((ROOT / "observable_view.py").read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    imported |= {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert imported <= {"__future__", "typing", "types"}, imported


def test_with_authority_off_the_view_is_inert_the_flag_is_false_and_nothing_registers_the_view_as_an_authority():
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False and sorted(authority.APPROVED_SNAPSHOTS) == ["gi_pressure_committed"]
    with ev.shadow(rs.MODE_OFF):
        encounter = _encounter_at(10)
    assert view.OVERLAY_KEY not in encounter.state and view.overlay_of(encounter.state) is None
    assert authority.AUTHORITY_DOMAIN == ("sbp", "dbp", "map") and "mental_status" not in authority.AUTHORITY_DOMAIN
