"""P3-1: the live encounter may run the Phase-2 common core beside the legacy engine, and nothing else moves.

R1-R17 of the P3-1 authorization. The point of every test here is the same: the legacy engine is the only
runtime authority, so turning the shadow flag on must leave the encounter bit-for-bit as it was -- the
resident's vitals, the order fates, the events, the authoritative state and therefore the score, which is a
function of that record. The shadow's own result is a separate object nobody authoritative reads.
"""
import ast
import json
import os
from copy import deepcopy
from pathlib import Path

import pytest

import runtime_shadow
from clinical_core.state import CoreInvariantError

ROOT = Path(__file__).resolve().parent
CASE = "gi_bleed_57m"
OTHER_FAMILY = "acs_54m_inferior"
TURNS = ("Give 1 litre of normal saline over 15 minutes. Reassess in 10 minutes.",
         "Transfuse 2 units of packed red cells. Start pantoprazole 80 mg IV. Reassess in 20 minutes.")
ON = {runtime_shadow.FLAG: runtime_shadow.MODE_SHADOW_COMPARE}


def _play(variant, turns, environ):
    """One encounter through the page's own order path, with the given environment."""
    import pilot_acceptance
    kept = {name: os.environ.get(name) for name in (runtime_shadow.FLAG, runtime_shadow.FAMILIES_FLAG)}
    try:
        for name in kept:
            os.environ.pop(name, None)
        os.environ.update(environ)
        encounter = pilot_acceptance.Encounter(variant)
        for text in turns:
            encounter.order(text)
        return encounter
    finally:
        for name, value in kept.items():
            os.environ.pop(name, None)
            if value is not None:
                os.environ[name] = value


def _session_for(variant):
    """A session on a fresh encounter of ``variant``, with the flag on only while it is opened."""
    import pilot_acceptance
    return runtime_shadow.ShadowSession.start(pilot_acceptance.Encounter(variant).state, environ=dict(ON))


def _authoritative(encounter) -> dict:
    """Everything authoritative an encounter produced: what the resident sees and what scoring reads."""
    return {
        "entries": deepcopy(encounter.entries),
        "ledger": deepcopy(encounter.ledger),
        "observable": deepcopy(encounter.state.get("observable")),
        "hidden": deepcopy(encounter.state.get("hidden")),
        "family_state": deepcopy(encounter.state.get("family_state")),
        "sim_time": encounter.state.get("sim_time"),
        "keys": sorted(encounter.state),
    }


@pytest.fixture(scope="module")
def paired():
    """The same case and the same orders, once with the flag off and once in shadow compare."""
    return {"off": _play(CASE, TURNS, {}), "on": _play(CASE, TURNS, dict(ON))}


# -- R1, R14, R15, R16: the flag ---------------------------------------------------------------------------

def test_r1_the_flag_is_off_unless_it_is_set_and_off_opens_no_session():
    assert runtime_shadow.mode({}) == runtime_shadow.MODE_OFF
    assert runtime_shadow.mode({runtime_shadow.FLAG: ""}) == runtime_shadow.MODE_OFF
    assert runtime_shadow.mode({runtime_shadow.FLAG: "authority"}) == runtime_shadow.MODE_OFF
    assert not runtime_shadow.enabled_for("gi_bleed", {})
    assert runtime_shadow.ShadowSession.start({"engine_family": "gi_bleed"}, environ={}) is None
    assert runtime_shadow.COMMON_CORE_RUNTIME_AUTHORITY is False


def test_r14_a_family_outside_the_live_scope_stays_legacy_only():
    for family in ("acs", "pulmonary_edema", "pulmonary_embolism", "asthma", "opioid", "pneumonia", "generated"):
        assert not runtime_shadow.enabled_for(family, dict(ON)), family
        assert runtime_shadow.ShadowSession.start({"engine_family": family}, environ=dict(ON)) is None
    assert runtime_shadow.live_families(dict(ON)) == ("gi_bleed",)
    # An allowlist cannot widen the scope, only narrow it.
    asked = {**ON, runtime_shadow.FAMILIES_FLAG: "acs,asthma"}
    assert runtime_shadow.live_families(asked) == ()
    assert not runtime_shadow.enabled_for("acs", asked)


def test_r14_an_encounter_of_another_family_opens_no_session():
    encounter = _play(OTHER_FAMILY, ("Reassess in 5 minutes.",), dict(ON))
    assert encounter.shadow is None


def test_r15_no_pilot_configuration_surface_turns_the_flag_on():
    """The pilot runs the frozen engine: nothing in its configuration, runbook or preflight names the flag."""
    surfaces = ["tools_pilot_preflight.py", "tools_pilot_smoke.py", "docs/RUNBOOK_PILOTO.md",
                "docs/READINESS_PILOTO_FORMATIVO.md", "pilot_acceptance.py"]
    import pilot_freeze
    from clinical_core import calibration
    # The preflight cannot gain a row for this flag. ``pilot_freeze.py`` is inside the Phase-2 calibration
    # freeze (``calibration.INPUT_PATH_SOURCES``), so adding one moves that frozen digest and two generated
    # Phase-2 documents -- reopening a closed stage for a convenience. Declared instead as
    # PILOT_PREFLIGHT_FLAG_GATE_DEFERRED (TD-130). What protects the pilot is below: no pilot surface names
    # the flag, and a clean environment opens no session.
    assert "pilot_freeze.py" in calibration.INPUT_PATH_SOURCES, \
        "if the Phase-2 freeze no longer covers pilot_freeze.py, the preflight row can and should be added"
    assert runtime_shadow.FLAG not in pilot_freeze.RUNTIME_FLAGS
    for name in surfaces:
        path = ROOT / name
        assert path.is_file(), f"{name} is a pilot surface this test must actually read"
        text = path.read_text(encoding="utf-8")
        if name == "pilot_acceptance.py":
            # It may open a session, but it must never set the flag itself.
            assert f'"{runtime_shadow.FLAG}"' not in text and f"'{runtime_shadow.FLAG}'" not in text
            continue
        assert runtime_shadow.FLAG not in text, name
    import pilot_acceptance
    assert pilot_acceptance.Encounter(CASE).shadow is None, "a clean environment must open no session"


def test_r16_the_plumbing_introduces_no_randomness():
    for name in ("runtime_shadow.py", "runtime_shadow_families.py"):
        tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
        imported = {node.module for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom) and node.module}
        imported.update(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                        for alias in node.names)
        assert not {"random", "secrets", "numpy.random", "time", "datetime"} & imported, (name, imported)
        assert "clinical_physiology" not in imported, f"{name}: the generated-case engine stays out"


# -- R2, R4, R5, R6, R7: nothing authoritative moves -------------------------------------------------------

def test_r2_r4_r6_r7_the_authoritative_encounter_is_identical_with_the_shadow_on(paired):
    """Vitals, fates, events, authoritative state: equal. Scoring reads this record, so the score follows."""
    off, on = _authoritative(paired["off"]), _authoritative(paired["on"])
    assert off["observable"] == on["observable"]
    assert off["family_state"] == on["family_state"]
    assert off["hidden"] == on["hidden"]
    assert off["sim_time"] == on["sim_time"]
    assert off["ledger"] == on["ledger"]
    assert off["entries"] == on["entries"]
    assert off == on


def test_r5_the_record_scoring_reads_is_byte_identical(paired):
    """The score is a function of the frozen record; equal records cannot be scored differently."""
    off, on = paired["off"], paired["on"]
    assert json.dumps(off.entries, sort_keys=True, default=str) == \
           json.dumps(on.entries, sort_keys=True, default=str)
    assert json.dumps(off.ledger, sort_keys=True, default=str) == \
           json.dumps(on.ledger, sort_keys=True, default=str)


def test_r7_the_shadow_adds_no_key_to_the_patient_state(paired):
    assert _authoritative(paired["off"])["keys"] == _authoritative(paired["on"])["keys"]
    assert "phase3_shadow" not in paired["on"].state
    assert not any("shadow" in str(key).lower() for key in paired["on"].state)


# -- R3, R8, R9, R10: the shadow result, and the action applied once ---------------------------------------

def test_r3_the_common_result_is_computed_separately_and_per_minute(paired):
    session = paired["on"].shadow
    assert session is not None and session.failures == [] and session.gaps == []
    record = session.record()
    assert record["runtime_authority"] == "legacy"
    assert record["common_core_runtime_authority"] is False
    assert record["case_id"] == CASE and record["family"] == "gi_bleed"
    minutes = [item["minute"] for item in record["minutes"]]
    assert minutes == list(range(1, paired["on"].minute + 1)), "one shadow result per live minute"
    assert sum(1 for item in record["minutes"] if item["compared"]) == len(TURNS)
    assert record["parameter_snapshot"] == runtime_shadow.PARAMETER_SNAPSHOT_ID


def test_r8_r9_r10_each_action_is_mirrored_once_and_applied_once(paired):
    session = paired["on"].shadow
    mirrored = [event["shadow_order_id"] for event in session.record()["mirrored"]]
    assert len(mirrored) == len(set(mirrored))
    assert len([name for name in mirrored if name.endswith("fluid")]) == 1
    assert len([name for name in mirrored if name.endswith("blood")]) == 1
    # The engine's own delivered amounts and clock are untouched by the shadow (R8-R10).
    off, on = paired["off"].state["family_state"], paired["on"].state["family_state"]
    for field in ("fluid_delivered_ml", "blood_delivered_units", "pending_fluid_ml", "pending_blood_units"):
        assert off[field] == on[field], field
    assert paired["off"].minute == paired["on"].minute
    # And what the shadow itself holds matches the engine's receipts, which is where a pairing fault shows.
    built, _gaps = session._contributors()
    volume = sum(item.volume_ml for item in built if type(item).__name__ == "Crystalloid")
    units = sum(item.units for item in built if type(item).__name__ == "PackedRedCells")
    assert (volume, units) == (1000.0, 2.0), (volume, units)


def test_two_bags_in_one_turn_each_take_their_own_receipt():
    """The review's finding: pairing receipts by first-of-kind gave the second bag the first one's start."""
    encounter = _play(CASE, ("Give 500 ml of normal saline over 10 minutes and 1 litre of normal saline "
                             "over 60 minutes. Reassess in 30 minutes.",), dict(ON))
    built, gaps = encounter.shadow._contributors()
    bags = sorted((item.volume_ml, item.start_minute) for item in built
                  if type(item).__name__ == "Crystalloid")
    assert gaps == []
    assert bags == [(500.0, 0.0), (1000.0, 10.0)], bags
    receipts = [summary.get("delivery_starts_at_min") for summary in encounter.entries[0]["action_summaries"]
                if summary.get("type") == "fluid"]
    assert sorted(start for _volume, start in bags) == sorted(float(value or 0) for value in receipts)


def test_an_order_the_engine_did_not_run_is_never_mirrored():
    """The review's finding: a held order became a phantom transfusion in the shadow."""
    encounter = _play(CASE, ("Give oxygen 4 litres by nasal cannula, start a heparin drip, then transfuse "
                             "2 units of packed red cells.",), dict(ON))
    fates = {order.get("fate") for order in encounter.entries[0]["orders"]}
    assert "HELD_CLARIFICATION" in fates, "this probe needs a held order to be meaningful"
    kinds = [event.kind for event in encounter.shadow.mirrored]
    assert kinds == ["oxygen"], kinds
    built, _gaps = encounter.shadow._contributors()
    assert not any(type(item).__name__ == "PackedRedCells" for item in built), "phantom transfusion"


def test_without_the_settled_action_list_nothing_is_mirrored():
    """The shadow consumes the fate the ledger settled; it never decides for itself what ran."""
    import pilot_acceptance
    session = runtime_shadow.ShadowSession.start(pilot_acceptance.Encounter(CASE).state, environ=dict(ON))
    before = {"sim_time": 0}
    after = {"sim_time": 1, "family_state": {"oxygen_fio2": 0.21}}
    session.observe(before, after, {"actions": [{"type": "fluid", "volume_ml": 1000.0}]},
                    {"executed": True, "action_summaries": [{"type": "fluid"}]}, None)
    assert session.mirrored == []
    assert any("settled action list" in str(gap.get("why")) for gap in session.gaps)


def test_order_ids_do_not_collide_between_two_turns_of_the_same_minute():
    session = _session_for(CASE)
    before = {"sim_time": 0}
    after = {"sim_time": 0, "family_state": {"oxygen_fio2": 0.21}}
    action = {"type": "ppi"}
    result = {"executed": True, "action_summaries": [{"type": "ppi"}]}
    session.observe(before, after, {"actions": [action]}, result, [action])
    session.observe(before, after, {"actions": [action]}, result, [action])
    assert len({event.order_id for event in session.mirrored}) == 2, [e.order_id for e in session.mirrored]


def test_a_turn_that_advances_no_minute_still_compares():
    """The review's finding: a zero-minute turn silently lost its comparison."""
    session = _session_for(CASE)
    import pilot_acceptance
    from clinical_core import legacy_adapter
    state = pilot_acceptance.Encounter(CASE).state
    after = deepcopy(state)
    after["sim_time"] = 5
    session.observe(deepcopy(state), after, None, None, [])
    compared = [item for item in session.minutes if item.compared_against_legacy]
    assert len(compared) == 1 and compared[0].minute == 5
    session.observe(after, after, None, None, [])
    compared = [item for item in session.minutes if item.compared_against_legacy]
    assert len(compared) == 1 and compared[0].minute == 5 and compared[0].divergences
    assert session.failures == []


def test_a_state_that_cannot_be_copied_records_a_failure_instead_of_raising():
    """The review's finding: the deepcopy at the wiring point was outside any guard."""
    session = _session_for(CASE)
    class Hostile:
        def __deepcopy__(self, memo):
            raise RuntimeError("cannot copy this state")
    assert session.capture({"sim_time": 0, "hidden": Hostile()}) is None
    assert [item.where for item in session.failures] == ["capture"]
    assert [item.classification for item in session.failures] == [runtime_shadow.MAPPING_GAP]


def test_a_session_belongs_to_one_encounter():
    """The review's finding: a stale session mixed two patients in one provenance artifact."""
    import pilot_acceptance
    first, second = pilot_acceptance.Encounter(CASE), pilot_acceptance.Encounter("gi_bleed_72f")
    session = runtime_shadow.ShadowSession.start(first.state, environ=dict(ON))
    assert session.is_for(first.state) and not session.is_for(second.state)


def test_a_gap_is_recorded_once_however_many_turns_it_survives():
    session = _session_for(CASE)
    before = {"sim_time": 0}
    action = {"type": "tranexamic_acid"}
    result = {"executed": True, "action_summaries": [{"type": "tranexamic_acid"}]}
    for minute in range(1, 6):
        after = {"sim_time": minute, "family_state": {"oxygen_fio2": 0.21}}
        session.observe(before, after, {"actions": [action]}, result, [action])
    kinds = [gap.get("kind") for gap in session.gaps]
    assert kinds.count("tranexamic_acid") == 1, kinds


def test_r8_observing_the_same_turn_twice_mirrors_it_once():
    """Idempotency by stable order id: the same turn observed again cannot double-apply its treatment.

    Its own encounter, so the shared session of the paired run is never mutated by this probe.
    """
    import pilot_acceptance
    kept = os.environ.get(runtime_shadow.FLAG)
    os.environ[runtime_shadow.FLAG] = runtime_shadow.MODE_SHADOW_COMPARE
    try:
        encounter = pilot_acceptance.Encounter(CASE)
    finally:
        os.environ.pop(runtime_shadow.FLAG, None)
        if kept is not None:
            os.environ[runtime_shadow.FLAG] = kept
    session = encounter.shadow
    assert session is not None
    before = deepcopy(encounter.state)
    after = deepcopy(before)
    after["sim_time"] = 5
    # A real order carries the ledger's own id, and that is the shadow's identity for it.
    action = {"type": "fluid", "volume_ml": 1000.0, "_order_id": "t0:0"}
    parsed = {"actions": [action]}
    result = {"executed": True, "action_summaries": [{"type": "fluid", "duration_min": 0}]}
    session.observe(before, after, parsed, result, [action], "t0")
    mirrored, digests, minutes = len(session.mirrored), session.digests(), len(session.minutes)
    assert mirrored == 1 and minutes == 5
    assert session.mirrored[0].ledger_order_id == "t0:0"
    assert session.mirrored[0].order_id.endswith("-fluid")
    session.observe(before, after, parsed, result, [action], "t0")
    assert len(session.mirrored) == mirrored, "the same ledger order was mirrored twice"
    assert session.digests() == digests and len(session.minutes) == minutes
    assert session.failures == []


# -- R11, R13: isolation ------------------------------------------------------------------------------------

def test_r11_a_common_core_failure_leaves_the_encounter_untouched(monkeypatch):
    from clinical_core import integration
    import pilot_acceptance
    monkeypatch.setenv(runtime_shadow.FLAG, runtime_shadow.MODE_SHADOW_COMPARE)
    encounter = pilot_acceptance.Encounter(CASE)
    assert encounter.shadow is not None

    def explode(*_args, **_kwargs):
        raise CoreInvariantError("the shadow core refuses this minute")

    monkeypatch.setattr(integration, "run", explode)
    for text in TURNS:
        encounter.order(text)
    monkeypatch.undo()
    reference = _play(CASE, TURNS, {})
    assert _authoritative(encounter) == _authoritative(reference)
    failures = encounter.shadow.record()["failures"]
    assert failures and {item["exception"] for item in failures} == {"CoreInvariantError"}
    assert {item["classification"] for item in failures} == {runtime_shadow.UNEXPECTED}
    assert not any("the shadow core refuses" in json.dumps(entry, default=str) for entry in encounter.entries)


def test_r11_a_boundary_is_classified_as_a_boundary_not_as_a_fault(monkeypatch):
    from clinical_core import integration
    from clinical_core.state import UnresolvedBoundary
    import pilot_acceptance
    monkeypatch.setenv(runtime_shadow.FLAG, runtime_shadow.MODE_SHADOW_COMPARE)
    encounter = pilot_acceptance.Encounter(CASE)
    monkeypatch.setattr(integration, "run", lambda *a, **k: (_ for _ in ()).throw(UnresolvedBoundary("edge")))
    encounter.order(TURNS[0])
    assert [item["classification"] for item in encounter.shadow.record()["failures"]] == [runtime_shadow.BOUNDARY]


def test_r13_nothing_authoritative_reads_the_shadow_result():
    """Only the two wiring points touch it, and neither renders it or feeds it to the record."""
    # The exemption below is the declared layer, and the declaration is pinned HERE as a literal: adding
    # a name to ``LAYER_SOURCES`` cannot quietly exempt a new module from this guard (P3-17).
    assert runtime_shadow.LAYER_SOURCES == ("runtime_shadow.py", "runtime_shadow_families.py",
                                            "runtime_shadow_evidence.py", "runtime_authority.py",
                                            "runtime_authority_store.py")
    readers = []
    for path in sorted(ROOT.glob("*.py")):
        if path.name in runtime_shadow.LAYER_SOURCES or path.name.startswith("test_"):
            continue  # the declared shadow layer itself; everything else must not touch it
        text = path.read_text(encoding="utf-8")
        if "runtime_shadow" in text or "phase3_shadow" in text:
            readers.append(path.name)
    assert readers == ["app.py", "pilot_acceptance.py"], readers
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    # The session is observed and never read back: no render, no trace, no score, no persistence.
    for forbidden in ("st.json(_shadow", "st.write(_shadow", "_shadow.record()", "_shadow.minutes",
                      "phase3_shadow\"]", "shadow[\"minutes\"]"):
        assert forbidden not in app, forbidden
    assert app.count("_shadow.observe(") == 1
    headless = (ROOT / "pilot_acceptance.py").read_text(encoding="utf-8")
    assert headless.count("shadow.observe(") == 1
    assert 'getattr(self, "shadow", None)' in headless, "a subclass must not need to know about the hook"
    assert "shadow.record()" not in headless and "shadow.minutes" not in headless


def test_the_side_effect_firewall_holds():
    """The session reads copies, with real arguments: nothing it is handed changes, and no alias is kept.

    Its own encounter: a probe that mirrors a synthetic order must never mutate the shared paired session,
    whose mirrored list and digests the determinism and classification tests below read.
    """
    import pilot_acceptance
    encounter = pilot_acceptance.Encounter(CASE)
    session = runtime_shadow.ShadowSession.start(encounter.state, environ=dict(ON))
    assert session is not None
    state = encounter.state
    before, after = deepcopy(state), deepcopy(state)
    after["sim_time"] = int(after.get("sim_time", 0) or 0) + 1
    parsed = {"actions": [{"type": "fluid", "volume_ml": 250.0, "nested": {"a": [1, 2]}}]}
    result = {"executed": True, "action_summaries": [{"type": "fluid", "delivery_starts_at_min": 0}]}
    kept = (deepcopy(before), deepcopy(after), deepcopy(parsed), deepcopy(result))
    session.observe(before, after, parsed, result, parsed["actions"], "t9")
    assert (before, after, parsed, result) == kept, "the session changed something it was handed"
    mirrored = session.mirrored[-1]
    assert mirrored.action is not parsed["actions"][0], "the session kept an alias of the live action"
    mirrored.action["nested"]["a"].append(3)
    assert parsed["actions"][0]["nested"]["a"] == [1, 2]


# -- R12: determinism ---------------------------------------------------------------------------------------

def test_r12_the_captured_input_replays_to_the_same_digests(paired):
    session = paired["on"].shadow
    live = list(session.digests())
    # Since P3-11 ``replay()`` returns the same minutes the live record has (the arrival is reported
    # apart), so the two lists are compared index by index with nothing dropped by hand.
    replayed = [item["state_digest"] for item in session.replay()["minutes"]]
    assert live and replayed == live
    assert [item["minute"] for item in session.replay()["minutes"]][0] == 1
    assert session.replay()["arrival_digest"]


def test_r12_the_same_encounter_played_again_gives_the_same_shadow(paired):
    again = _play(CASE, TURNS, dict(ON))
    assert again.shadow.digests() == paired["on"].shadow.digests()
    assert [event["order_id"] for event in again.shadow.record()["mirrored"]] == \
           [event["order_id"] for event in paired["on"].shadow.record()["mirrored"]]


# -- R17: Phase 2 stays frozen ------------------------------------------------------------------------------

def test_r17_the_phase2_closure_digest_is_unchanged():
    import hashlib
    package = ROOT / "clinical_core"
    paths = sorted(path.relative_to(ROOT).as_posix() for path in package.rglob("*.py")
                   if "__pycache__" not in path.parts and path.is_file() and not path.name.startswith("."))
    sources = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}
    digest = hashlib.sha256(json.dumps(sources, sort_keys=True).encode("utf-8")).hexdigest()
    assert digest == runtime_shadow.PHASE2_DIGEST
    record = json.loads((ROOT / "docs" / "revision" / "P2X3_phase2_closure.json").read_text(encoding="utf-8"))
    assert record["phase2_digest"] == digest and record["sources"] == sources


def test_the_divergence_classes_come_from_the_committed_golden(paired):
    """Every mismatch is either a difference the golden already explains, or it is loud."""
    session = paired["on"].shadow
    compared = [item for item in session.minutes if item.compared_against_legacy]
    assert compared
    explained = runtime_shadow.golden_explained("gi_bleed")
    assert "hb_g_dl" in explained and "fluid_delivered_ml" not in explained
    for item in compared:
        for divergence in item.divergences:
            if divergence.status == runtime_shadow.EXPECTED:
                assert divergence.variable in explained and divergence.reasons
            if divergence.status == runtime_shadow.PARTIALLY_EXPLAINED:
                assert divergence.reasons and "scenarios" in divergence.reasons[0]
            assert divergence.status != runtime_shadow.SAFETY_CRITICAL, \
                (divergence.variable, divergence.legacy, divergence.core)
            if divergence.status == runtime_shadow.UNEXPECTED:
                # Only a variable the golden never declares may be loud here, and none of the seven
                # plumbing-sensitive ones may be: those are the ones a mapping fault would move.
                assert divergence.variable not in (
                    "fluid_delivered_ml", "blood_delivered_units", "fio2", "glucose_mg_dl", "k_mmol_l",
                    "hemostasis_relief", "transfusion_overload_units"), divergence.variable
    # Since P3-11 a record exists only for a variable that did NOT match, so the plumbing-sensitive ones
    # agreeing means they are absent from every compared minute. Same claim, read from the one record.
    names = {d.variable for item in compared for d in item.divergences}
    assert not ({"fluid_delivered_ml", "blood_delivered_units", "fio2", "pulse_present", "rhythm"} & names), \
        sorted(names)
    assert {d.domain for item in compared for d in item.divergences} <= set(
        __import__("runtime_shadow_families").DOMAINS), "every record names a declared domain"


def test_an_unexplained_difference_is_loud():
    """The classifier can fail: a variable the golden does not explain is UNEXPECTED, not EXPECTED."""
    from clinical_core import comparison
    fluid = next(v for v in comparison.VARIABLES if v.name == "fluid_delivered_ml")
    assert runtime_shadow._classify(fluid, 1.0, "gi_bleed") == runtime_shadow.UNEXPECTED
    pulse = next(v for v in comparison.VARIABLES if v.name == "pulse_present")
    assert runtime_shadow._classify(pulse, True, "gi_bleed") == runtime_shadow.SAFETY_CRITICAL
    hb = next(v for v in comparison.VARIABLES if v.name == "hb_g_dl")
    assert runtime_shadow._classify(hb, 1.0, "gi_bleed") == runtime_shadow.EXPECTED
    assert runtime_shadow._classify(hb, None, "gi_bleed") == runtime_shadow.BOUNDARY
