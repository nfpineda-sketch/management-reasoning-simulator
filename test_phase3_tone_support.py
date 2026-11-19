"""P3-396 / P3-397: the development mapping of the common vasoconstrictor support (``runtime_tone_support``).

What is defended here:

  * no registered adapter declares the reader, and declaring it is a COPY that leaves the registry as it was;
  * the mapping is one function for every family: it reads the order and the witness, never a family, a case or a pressure;
  * one order is built (a start at a fixed rate in mcg/min) and every other one is a DECLARED gap with its own reason;
  * it fails closed on the core's lineage;
  * the live authority still does not accept the order, and nothing a resident runs imports this module;
  * FR-F, run in the shadow with the order mapped: the order is accepted, the tone changes, the response begins causally and
    a reassessment is possible -- on the ratified GI pressure snapshot, which the run reads and does not change.
"""
import ast
import dataclasses
import math
from pathlib import Path

import pytest

import runtime_authority as ra
import runtime_pressure_grant as grants
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam
import runtime_tone_support as ts
import test_tone_pathway_analysis as ta
from clinical_core import vascular_support as vs

ROOT = Path(__file__).resolve().parent
START = {"type": "norepinephrine", "rate": 10.0, "units": "mcg/min", "operation": "start"}


def _event(minute, order_id, **changes):
    return rs.MirroredAction(order_id, minute, "norepinephrine", {**START, **changes}, {}, 0.21)


# -- nothing registered declares it -----------------------------------------------------------------------------------------

def test_no_registered_adapter_declares_the_reader_or_maps_the_order():
    for family, adapter in fam.ADAPTERS.items():
        assert adapter.tone_support_witness is None, family
        assert ts.ORDER_KIND not in adapter.maps, family
        assert adapter.profile(fam.COMMITTED).vasoconstrictor_support_to_tone_gain is None, family
        for name, witness in adapter.region_witnesses().items():
            assert witness.tone_support_witness is None and witness.profile(fam.COMMITTED).vasoconstrictor_support_to_tone_gain is None, (family, name)
        built, gaps = adapter.interventions([_event(3, "o1")], None)
        assert not any(type(item).__name__ == "Norepinephrine" for item in built), family
        assert [gap["kind"] for gap in gaps] == ["norepinephrine"], family


def test_declaring_it_is_a_copy_that_leaves_the_registered_adapter_as_it_was():
    for family, adapter in fam.ADAPTERS.items():
        before = (type(adapter), adapter.version, tuple(adapter.maps), dict(vars(adapter)))
        made = ts.with_tone_support(adapter, "LOW")
        assert made is not adapter and isinstance(made, type(adapter)) and made.family == adapter.family and made.cases == adapter.cases
        assert made.tone_support_witness == "LOW" and made.version == f"{adapter.version}+tone_support/LOW"
        assert made.maps == tuple(adapter.maps) + (ts.ORDER_KIND,) and made.region_witnesses() == {}
        assert (type(adapter), adapter.version, tuple(adapter.maps), dict(vars(adapter))) == before
        assert fam.ADAPTERS[family] is adapter and fam.adapter_for(family) is adapter
        with pytest.raises(ValueError, match="already declares"):
            ts.with_tone_support(made, "LOW")
    assert not any(isinstance(adapter, ts.ToneSupport) for adapter in fam.ADAPTERS.values())
    with pytest.raises(Exception, match="development witnesses"):
        ts.with_tone_support(fam.ADAPTERS["gi_bleed"], "MEDIAN")
    with pytest.raises(TypeError):
        ts.with_tone_support(object(), "LOW")


@pytest.mark.parametrize("family", sorted(fam.ADAPTERS))
@pytest.mark.parametrize("witness", vs.WITNESS_NAMES)
def test_the_copy_declares_exactly_one_profile_field_and_names_its_witness(family, witness):
    adapter = fam.ADAPTERS[family]
    made = ts.with_tone_support(adapter, witness)
    plain, declared = dataclasses.asdict(adapter.profile(fam.COMMITTED)), dataclasses.asdict(made.profile(fam.COMMITTED))
    assert {key for key in plain if plain[key] != declared[key]} == {ts.PROFILE_FIELD}
    assert declared[ts.PROFILE_FIELD] == vs.witness(witness)["tone_gain"]
    base, snapshot = adapter.snapshot(), made.snapshot()
    assert snapshot.id == f"{base.id}+tone_support_{witness.lower()}" and snapshot.approved is False
    assert snapshot.provenance[:len(base.provenance)] == base.provenance
    said = " ".join(snapshot.provenance[len(base.provenance):])
    assert witness in said and "not a calibration" in said and "does not grant norepinephrine" in said


# -- one mapping, for every family ---------------------------------------------------------------------------------------------

def test_the_mapping_names_no_family_no_case_and_reads_no_pressure():
    source = (ROOT / "runtime_tone_support.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    strings = {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    names = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)} | {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    cases = {case for adapter in fam.ADAPTERS.values() for case in adapter.cases}
    assert not (strings & (set(fam.ADAPTERS) | cases))
    assert not names & {"sbp", "dbp", "map", "pressure_rel", "output_rel", "delivery_rel", "T", "V", "P", "hb", "D", "mapping_state", "case_id", "cases"}
    # the family is named once, to copy the base snapshot's own label into the development snapshot; nothing branches on it
    assert [ast.unparse(node) for node in ast.walk(tree) if isinstance(node, ast.Attribute) and node.attr == "family"] == ["base.family"]
    tests = [node.test for node in ast.walk(tree) if isinstance(node, (ast.If, ast.IfExp, ast.While))] + [node for node in ast.walk(tree) if isinstance(node, ast.Compare)]
    assert tests and not any("family" in ast.unparse(node) or "case" in ast.unparse(node) for node in tests)
    body = ast.unparse(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "map_orders"))
    assert "state" not in body and "adapter" not in body


def test_one_order_shape_is_built_and_every_other_is_a_declared_gap_with_its_reason():
    """``order_disposition`` judges the order ALONE (whether the run saw the infusion start is ``infusion_history``'s).

    P3-431 (declared adaptation, FD-TITRATE-01): an adjustment, a continuation and a stop are READ now -- each sets ONE absolute rate, 0 for a stop -- where they used to be
    'no core mapping'. Everything else this test protected still holds: other units, a weight-based dose and a rate that is not a finite positive number are refused with their reason."""
    assert ts.order_disposition(START) == (10.0, None)
    assert ts.order_disposition({**START, "rate": 4}) == (4.0, None)
    assert ts.order_disposition({**START, "operation": "adjust", "rate": 6}) == (6.0, None) and ts.order_disposition({**START, "operation": "continue"}) == (10.0, None)
    assert ts.order_disposition({"type": "norepinephrine", "operation": "stop", "rate": None, "units": None}) == (0.0, None)
    for changes, text in (({"operation": None}, "not an operation this mapping reads"), ({"operation": "titrate to MAP 65"}, "not an operation this mapping reads"),
                          ({"operation": ["start"]}, "not an operation this mapping reads"), ({"units": "mcg/kg/min"}, "weight"),
                          ({"operation": "adjust", "units": "mcg/kg/min"}, "weight"),
                          ({"units": None}, "gives no units"), ({"units": "mg/h"}, "only a fixed rate in mcg/min"), ({"rate": None}, "positive rate"), ({"rate": 0.0}, "positive rate"),
                          ({"rate": -5.0}, "positive rate"), ({"rate": math.nan}, "positive rate"), ({"rate": math.inf}, "positive rate"),
                          ({"rate": True}, "positive rate"), ({"rate": "10"}, "positive rate"), ({"operation": "adjust", "rate": 0.0}, "positive rate")):
        rate, why = ts.order_disposition({**START, **changes})
        assert rate is None and text in why, (changes, why)
    assert ts.order_disposition(None)[0] is None


def test_only_the_first_order_of_the_kind_is_built_and_nothing_else_in_the_run_is_touched():
    """P3-431 (declared adaptation, FD-TITRATE-01 and FD-TITRATE-07): the later orders -- an adjustment, a stop and a restart -- used to be declared gaps of a run that 'no longer
    mirrors the vasopressor'; they are now CARRIED by the encounter's ONE infusion, which still carries the id of the first order and the witness's constants. What the test
    protected still holds: ONE contributor of the kind, and nothing else in the run touched."""
    events = [_event(5, "o1"), _event(10, "o2", operation="adjust", rate=20.0), _event(20, "o3", operation="stop", rate=None, units=None), _event(25, "o4")]
    other_built, other_gaps = ("a-fluid", "an-oxygen"), [{"order_id": "x9", "kind": "dopamine", "why": "no core intervention for this order type"}]
    family_gaps = other_gaps + [{"order_id": event.order_id, "kind": "norepinephrine", "why": "no core intervention for this order type yet"} for event in events]
    point = vs.witness("CENTER_REFERENCE")
    built, gaps = ts.map_orders(events, other_built, family_gaps, point)
    assert built[:2] == other_built and len(built) == 3
    infusion = built[2]
    assert isinstance(infusion, vs.Norepinephrine) and (infusion.id, infusion.start_minute, infusion.rate_mcg_min, infusion.stop_minute) == ("o1", 5, 10.0, None)
    assert (infusion.half_effect_rate_mcg_min, infusion.onset_tau_min, infusion.offset_tau_min) == (point["half_effect_rate_mcg_min"], point["onset_tau_min"], point["offset_tau_min"])
    assert type(infusion) is ts.NorepinephrineRateHistory and infusion.changes == ((10, 20.0), (20, 0.0), (25, 10.0)) and infusion.carried_order_ids == ("o1", "o2", "o3", "o4")
    assert [row[3] for row in infusion.orders] == [ts.STARTED, ts.INCREASED, ts.STOPPED, ts.RESTARTED]
    assert gaps == other_gaps, "no order of the kind is a gap, and the other family's gap is as it was"
    # a single start is still the core's own writer, exactly as before
    alone, none = ts.map_orders(events[:1], other_built, family_gaps[:2], point)
    assert type(alone[2]) is vs.Norepinephrine and alone[2] == vs.Norepinephrine("o1", 5, 10.0, half_effect_rate_mcg_min=point["half_effect_rate_mcg_min"],
                                                                                 onset_tau_min=point["onset_tau_min"], offset_tau_min=point["offset_tau_min"]) and none == other_gaps


def test_an_unmappable_first_order_is_never_replaced_by_a_later_one():
    """Review finding: a weight-based start followed by a fixed-rate one used to build the SECOND, so the run carried an infusion the encounter started at another time and dose."""
    point = vs.witness("CENTER_REFERENCE")
    built, gaps = ts.map_orders([_event(3, "w1", units="mcg/kg/min", rate=0.1), _event(8, "w2"), _event(12, "w3", operation="stop", rate=None, units=None)], (), [], point)
    assert built == () and [gap["order_id"] for gap in gaps] == ["w1", "w2", "w3"]
    assert "weight" in gaps[0]["why"] and gaps[0]["why"].endswith(ts.NOT_MIRRORED)
    assert gaps[1]["why"] == ts.GAP_NOT_MIRRORED and gaps[2]["why"] == ts.GAP_NOT_MIRRORED
    # the same for an encounter that begins with a stop or an adjustment (an infusion the run never saw start)
    for first in (dict(operation="stop", rate=None, units=None), dict(operation="adjust", rate=6.0)):
        built, gaps = ts.map_orders([_event(2, "a", **first), _event(9, "b")], (), [], point)
        assert built == () and [gap["why"] == ts.GAP_NOT_MIRRORED for gap in gaps] == [False, True], (first, gaps)


def test_the_first_order_is_the_engines_first_not_the_mirrors_first_nor_the_alphabets():
    """P3-435 (declared adaptation, after the adversarial review). The engine's order IS the mirror's own (the mirror dates every order at the minute the engine ran it, so its minutes
    never go back). An order dated BEFORE one that came before it used to be sorted into place; it is now a contradiction the mapping does not resolve: no order of the kind is mapped
    and each says why. What this test protected still holds, and more strictly: a later order is never built in the place of the encounter's first."""
    point = vs.witness("CENTER_REFERENCE")
    built, gaps = ts.map_orders([_event(25, "late"), _event(5, "early")], (), [], point)
    assert built == () and [(gap["order_id"], gap["why"]) for gap in gaps] == [(name, f"{ts.GAP_CHRONOLOGY}. {ts.NOT_MIRRORED}") for name in ("late", "early")]
    # in time, the later order -- the same rate again -- is carried by the ONE infusion, and changes nothing  (P3-431, declared adaptation: it used to be a gap)
    built, gaps = ts.map_orders([_event(5, "early"), _event(25, "late")], (), [], point)
    assert [(item.id, item.start_minute) for item in built] == [("early", 5)] and gaps == []
    assert built[0].carried_order_ids == ("early", "late") and built[0].changes == () and [row[3] for row in built[0].orders] == [ts.STARTED, ts.IDEMPOTENT]
    # ... and within one minute the position in the mirror decides, never the order id's spelling: a start and then a stop leave nothing running and no modelled interval to carry
    # either, so nothing is built and each says why (the start was replaced within its minute; the stop stopped nothing)
    built, gaps = ts.map_orders([_event(5, "m005-z"), _event(5, "m005-a", operation="stop", rate=None, units=None)], (), [], point)
    assert built == () and [(gap["order_id"], gap["why"]) for gap in gaps] == [("m005-z", ts.GAP_REPLACED.format(operation="start")), ("m005-a", ts.GAP_NOTHING_TO_BUILD.format(operation="stop"))]
    built, gaps = ts.map_orders([_event(5, "m005-z", operation="stop", rate=None, units=None), _event(5, "m005-a")], (), [], point)
    assert built == () and [gap["order_id"] for gap in gaps] == ["m005-z", "m005-a"]


def test_an_order_id_counts_once_and_a_writer_the_core_refuses_is_a_declared_gap():
    point = vs.witness("CENTER_REFERENCE")
    family_gaps = [{"order_id": "o1", "kind": "norepinephrine", "why": "no core intervention for this order type yet"}] * 2
    built, gaps = ts.map_orders([_event(5, "o1"), _event(5, "o1")], (), family_gaps, point)
    assert [item.id for item in built] == ["o1"] and gaps == []
    # a rate past what the core's writer represents is refused by the core, declared, and replaced by nothing
    absurd = vs.SUPPORT_LIMIT * point["half_effect_rate_mcg_min"] * 2.0
    built, gaps = ts.map_orders([_event(5, "huge", rate=absurd), _event(9, "next")], (), [], point)
    assert built == () and "the core's writer refuses this order" in gaps[0]["why"] and gaps[0]["why"].endswith(ts.NOT_MIRRORED) and gaps[1]["why"] == ts.GAP_NOT_MIRRORED


def test_it_is_refused_on_an_amendment_2_consciousness_witness():
    """Review finding: the support raises the pressure the Amendment-2 composite reads while delivery falls; the two together are unreviewed, so the combination is not offered."""
    gi = type(fam.ADAPTERS["gi_bleed"])
    for name in fam.GI_AMENDMENT_2_WITNESS_NAMES:
        with pytest.raises(ValueError, match="Amendment-2 consciousness witness"):
            ts.with_tone_support(gi.witness(name), "CENTER_REFERENCE")
    # P3-431 (declared adaptation): 'only the first order can be built' is no longer said -- the later orders are carried by the ONE infusion -- and what is said instead is checked
    assert ts.summary()["refused_on_an_amendment_2_witness"] is True and ts.summary()["one_infusion_one_ordered_rate"] is True and ts.summary()["refusal_closes_the_infusion"] is True


def test_each_copy_has_a_class_of_its_own_and_the_module_keeps_no_cache():
    one, two = ts.with_tone_support(fam.ADAPTERS["gi_bleed"], "LOW"), ts.with_tone_support(fam.ADAPTERS["gi_bleed"], "HIGH")
    assert type(one) is not type(two) and type(one).__name__ == type(two).__name__ and (one.tone_support_witness, two.tone_support_witness) == ("LOW", "HIGH")
    assert not [name for name, value in vars(ts).items() if isinstance(value, (dict, list, set)) and not name.startswith("__")]


@pytest.mark.parametrize("family", sorted(fam.ADAPTERS))
def test_every_family_reports_the_order_built_through_the_same_mapping(family):
    adapter = ts.with_tone_support(fam.ADAPTERS[family], "CENTER_REFERENCE")
    events = [_event(4, "m004-norepinephrine")]
    built, gaps = adapter.interventions(events, None)
    ours = [item for item in built if isinstance(item, vs.Norepinephrine)]
    assert len(ours) == 1 and (ours[0].id, ours[0].start_minute) == ("m004-norepinephrine", 4) and not [gap for gap in gaps if gap["kind"] == "norepinephrine"]
    rows = fam.action_dispositions(adapter, events, None)
    assert [(row["kind"], row["disposition"], row["effective_minute"]) for row in rows if row["kind"] == "norepinephrine"] == [("norepinephrine", fam.BUILT, 5)]
    plain_built, _ = fam.ADAPTERS[family].interventions(events, None)
    assert [item for item in built if not isinstance(item, vs.Norepinephrine)] == list(plain_built)


# -- fail closed ----------------------------------------------------------------------------------------------------------------

def test_the_reader_is_declared_only_on_a_certified_core_that_carries_it(monkeypatch):
    monkeypatch.setattr(ev, "core_lineage_ok", lambda: True)
    monkeypatch.setattr(ev, "core_lineage_verdict", lambda: {"active_core": "PHASE2_AMENDMENT_3"})
    assert ts.availability() is None
    for older in ("PHASE2_AMENDMENT_2", "PHASE2_AMENDMENT_1", "PHASE2_CLOSURE", "SOMETHING_ELSE", None):
        monkeypatch.setattr(ev, "core_lineage_verdict", lambda older=older: {"active_core": older})
        assert "exists only in PHASE2_AMENDMENT_3" in ts.availability(), older
    monkeypatch.setattr(ev, "core_lineage_verdict", lambda: {"active_core": "PHASE2_AMENDMENT_3"})
    monkeypatch.setattr(ev, "core_lineage_ok", lambda: False)
    monkeypatch.setattr(ev, "core_lineage_reason", lambda: "the live core is a CANDIDATE")
    assert ts.availability() == "the live core is a CANDIDATE"
    monkeypatch.setattr(ev, "core_lineage_reason", lambda: "")
    assert "could not be evaluated" in ts.availability()

    def broken():
        raise OSError("no record")
    monkeypatch.setattr(ev, "core_lineage_ok", broken)
    assert ts.availability() == "the common core lineage could not be evaluated: OSError"


def test_a_run_whose_core_does_not_carry_the_reader_never_opens(monkeypatch):
    monkeypatch.setattr(ev, "core_lineage_ok", lambda: False)
    monkeypatch.setattr(ev, "core_lineage_reason", lambda: "the live core is a CANDIDATE")
    adapter = ts.with_tone_support(fam.ADAPTERS["gi_bleed"], "CENTER_REFERENCE")
    with pytest.raises(ts.ToneSupportUnavailable):
        adapter.profile(fam.COMMITTED)
    runner = fam.ShadowPhysiologyRunner.open("gi_bleed", "gi_bleed_57m", adapter=adapter)
    assert runner.anchors is None and [(item.where, item.exception) for item in runner.failures] == [("open", "ToneSupportUnavailable")]
    assert runner.advance(5) is False and runner.results == [] and runner.replay_input() is None


def test_a_development_copy_cannot_run_another_familys_case():
    adapter = ts.with_tone_support(fam.ADAPTERS["acs"], "LOW")
    assert fam.ShadowPhysiologyRunner.open("gi_bleed", "gi_bleed_57m", adapter=adapter) is None
    assert fam.ShadowPhysiologyRunner.open("acs", "gi_bleed_57m", adapter=adapter) is None


# -- no authority, no resident ------------------------------------------------------------------------------------------------------

def test_the_live_authority_still_does_not_accept_the_order():
    assert ts.ORDER_KIND not in ra.SUPPORTED_ACTIONS
    assert "norepinephrine" in grants.LIVE_GRANT["not_granted"]
    assert any("vasopressor" in item for item in grants.LIVE_GRANT["not_granted"])
    import runtime_faculty_review as review
    frf = review.scenario("FR-F")
    assert frf["expected"] == "HALTED_BY_UNSUPPORTED_ACTION" and frf["steps"][1] == ("order", ta.FRF_ORDER)
    assert ts.summary()["registered_adapters_declaring_it"] == [] and ts.summary()["chosen_witness"] is None


def test_nothing_outside_the_shadow_layers_own_tests_reads_the_mapping():
    """The module is named by the layer's digest and read by test code only: no page, no engine, no authority and no scoring imports it."""
    readers = []
    for path in sorted(ROOT.glob("*.py")) + sorted((ROOT / "clinical_core").rglob("*.py")):
        if path.name == "runtime_tone_support.py" or path.name.startswith("test_") or path.name == "conftest.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "runtime_tone_support" in text or "with_tone_support" in text:
            readers.append(path.name)
    assert readers == ["runtime_shadow.py", "runtime_shadow_families.py"]
    assert "import runtime_tone_support" not in (ROOT / "runtime_shadow.py").read_text(encoding="utf-8")
    assert "import runtime_tone_support" not in (ROOT / "runtime_shadow_families.py").read_text(encoding="utf-8")
    assert "runtime_tone_support.py" in rs.LAYER_SOURCES


# -- FR-F in the shadow ---------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def frf():
    captured = ta.capture_frf()
    return captured, ta.frf_runs(captured)


def test_the_encounters_own_shadow_run_still_declares_the_order_as_a_gap(frf):
    captured, runs = frf
    order = [event for event in captured["mirrored"] if event.kind == "norepinephrine"]
    assert len(order) == 1 and order[0].minute == ta.FRF_ORDER_MINUTE
    assert {key: order[0].action[key] for key in START} == START
    assert [turn["to_minute"] for turn in captured["turns"]] == [ta.FRF_ORDER_MINUTE, *ta.FRF_REASSESSMENTS]
    unmapped = runs[ta.NOT_MAPPED]
    assert [gap["kind"] for gap in unmapped["gaps"]] == ["norepinephrine"] and unmapped["profile_gain"] is None
    assert all(row["support"] is None and row["T"] == 1.0 for row in unmapped["rows"])


@pytest.mark.parametrize("witness", vs.WITNESS_NAMES)
def test_frf_the_order_is_accepted_the_tone_changes_causally_and_a_reassessment_is_possible(frf, witness):
    _captured, runs = frf
    run, reference = runs[witness], runs[ta.NOT_MAPPED]
    checks = ta._frf_checks(run, reference, ta.FRF_ORDER_MINUTE)
    assert {name: value for name, value in checks.items() if name != "facts"} == {
        "order_accepted": True, "tone_changes": True, "response_begins_causally": True, "reassessment_possible": True,
        "no_volume_and_no_pump_created": True, "bounded_by_its_own_form": True, "replays_exactly": True}
    facts = checks["facts"]
    assert (facts["first_minute_with_support"], facts["first_minute_tone_differs"], facts["first_minute_pressure_differs"]) == (3, 4, 4)
    assert facts["pressure_never_below_the_unmapped_run"] and facts["output_never_above_the_unmapped_run"] and facts["delivery_never_above_the_unmapped_run"]
    assert facts["debt_never_below_the_unmapped_run"]
    assert run["snapshot_id"].endswith(f"+tone_support_{witness.lower()}") and run["adapter_version"].endswith(f"+tone_support/{witness}")
    assert run["runner"].replay_input().versions["parameter_snapshot"] == run["snapshot_id"]
    gains = [row["map_gain_mmhg"] for row in (ta.observed(reference["rows"], run["rows"], minute) for minute in ta.FRF_REASSESSMENTS)]
    assert all(gain > 0.0 for gain in gains) and len({round(gain, 3) for gain in gains}) == len(gains)        # mmHg follow the flow: never one constant


def test_frf_the_witnesses_order_the_response_and_the_bleed_goes_on_under_all_of_them(frf):
    _captured, runs = frf
    for minute in ta.FRF_REASSESSMENTS:
        maps = [runs[name]["rows"][minute]["map"] for name in (ta.NOT_MAPPED,) + tuple(vs.WITNESS_NAMES)]
        assert maps == sorted(maps) and len(set(maps)) == 4, minute
        flows = [runs[name]["rows"][minute]["output_rel"] for name in (ta.NOT_MAPPED,) + tuple(vs.WITNESS_NAMES)]
        assert flows == sorted(flows, reverse=True), minute
    for name in vs.WITNESS_NAMES:
        rows = runs[name]["rows"]
        assert rows[ta.FRF_REASSESSMENTS[-1]]["map"] < rows[ta.FRF_REASSESSMENTS[0]]["map"]            # no volume was given: the pressure it bought keeps falling
        assert [row["V"] for row in rows] == [row["V"] for row in runs[ta.NOT_MAPPED]["rows"]]


def test_frf_runs_on_the_ratified_pressure_snapshot_and_does_not_change_it(frf):
    import runtime_pressure_snapshot as ps
    _captured, runs = frf
    base = ta.frf_base_adapter()
    assert ps.configuration_is_pinned(base.pressure_configuration) and base.pressure_configuration.snapshot_id == ps.SNAPSHOT_ID
    for name in vs.WITNESS_NAMES:
        adapter = runs[name]["adapter"]
        assert adapter.pressure_configuration is base.pressure_configuration or adapter.pressure_configuration == base.pressure_configuration
        plain, declared = dataclasses.asdict(base.profile(fam.COMMITTED)), dataclasses.asdict(adapter.profile(fam.COMMITTED))
        assert {key for key in plain if plain[key] != declared[key]} == {ts.PROFILE_FIELD}
        assert adapter.writers(ta.FRF_CASE, fam.COMMITTED) == base.writers(ta.FRF_CASE, fam.COMMITTED)
    assert runs[ta.NOT_MAPPED]["snapshot_id"] == ps.RUNTIME_SNAPSHOT_ID


def test_a_declared_reader_with_no_order_changes_no_reading():
    """Declaring the reader alone is silent: with no norepinephrine order the run reads exactly what the same run without it reads."""
    for family in ("gi_bleed", "acs"):
        case = fam.ADAPTERS[family].cases[0]
        plain = ta.shadow_run(family, case, None, (), 20)
        declared = ta.shadow_run(family, case, "HIGH", (), 20)
        strip = lambda rows: [{key: value for key, value in row.items() if key != "support"} for row in rows]
        assert strip(plain["rows"]) == strip(declared["rows"]) and not declared["gaps"] and not declared["failures"]
        assert all(row["support"] == 0.0 for row in declared["rows"][1:])


# -- the consciousness binding does not absorb the reader -------------------------------------------------------------------------------

def test_a_profile_that_declares_the_reader_is_not_the_ratified_one_for_the_snapshot_binding():
    """``runtime_authority_pair.profile_digest`` leaves an UNSET successor field out, so the pinned digests still describe the ratified profile on the
    successor core. A profile that DECLARES the reader keeps the field in its digest: it is another profile, and a binding built around it is refused."""
    import runtime_authority_pair as pair
    bound = pair.bind()
    assert pair.bound_is_v1(bound) and bound.profile.vasoconstrictor_support_to_tone_gain is None
    assert pair.profile_digest(bound.profile) == bound.profile_digest == pair.V1_PROFILE_DIGEST
    assert pair.SUCCESSOR_PROFILE_FIELDS == (ts.PROFILE_FIELD,)
    for witness in vs.WITNESS_NAMES:
        declared = dataclasses.replace(bound.profile, **{ts.PROFILE_FIELD: vs.witness(witness)["tone_gain"]})
        assert pair.profile_digest(declared) != pair.V1_PROFILE_DIGEST and pair.profile_digest(declared) != pair.V2_PROFILE_DIGEST
        forged = dataclasses.replace(bound, profile=declared)
        assert pair.bound_is_v1(forged) is False
        relabelled = dataclasses.replace(bound, profile=declared, profile_digest=pair.profile_digest(declared))
        assert pair.bound_is_v1(relabelled) is False
