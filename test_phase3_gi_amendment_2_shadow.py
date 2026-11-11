"""P3-174 a P3-179: la Enmienda 2 certificada en la SOMBRA de desarrollo de GI (y solo ahi).

Lo que se fija, con la medida que lo sostiene:

* ARQUITECTURA (P3-174): GI corre, ademas de la corrida propia de la sesion (perfil comprometido, enmienda APAGADA), tres
  testigos de desarrollo (LOW, CENTER_REFERENCE, HIGH), cada uno su propia trayectoria; ninguno se elige ni se promedia; cada
  magnitud es DEVELOPMENT_BEHAVIORAL_REGION y lleva su procedencia. Ninguna otra familia la declara.
* SERIE EN VIVO (P3-175/176): el orden causal exigido, la recuperacion segun la lectura de la docencia (2026-11-11) y la
  comparacion con la escalera heredada, contra el registro medido (``docs/revision/PHASE3_GI_AMENDMENT_2_SERIES.json``).
* FRONTERA (P3-178): el estado de colapso es SOLO estado fisiologico, explicito en la traza junto al motor heredado, y no
  termina un encuentro.
* ADVERSARIAL (P3-179): compuertas y mutantes de la capa (testigo elegido, enmienda fuera de GI, autoridad, linaje malo,
  replay) deben ser detectados; la sonda de control los deja pasar solo cuando nada esta roto.
"""
import copy
import dataclasses
import json
import os
from pathlib import Path

import pytest

import pilot_acceptance as acceptance
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam
import runtime_shadow_observer as obs
import runtime_shadow_store as store
import test_gi_amendment_2_series as series
from clinical_core import systemic_consciousness as sc
from test_shadow_observability import GI, _latest, _play, _resealed, traces  # noqa: F401

ROOT = Path(__file__).resolve().parent
RECORD = json.loads((ROOT / "docs" / "revision" / "PHASE3_GI_AMENDMENT_2_SERIES.json").read_text(encoding="utf-8"))
WITNESSES = list(sc.WITNESSES)
CASES = ("gi_bleed_57m", "gi_bleed_72f")


def _gi() -> fam.GiHaemorrhageAdapter:
    return fam.ADAPTERS["gi_bleed"]


# -- P3-174: arquitectura y procedencia ----------------------------------------------------------------------------------------

def test_gi_declares_exactly_the_three_witnesses_of_the_certified_region_and_each_is_its_own_adapter():
    assert list(_gi().region_witnesses()) == WITNESSES == list(fam.GI_AMENDMENT_2_WITNESS_NAMES)
    committed = _gi().profile(fam.COMMITTED)
    assert committed.amendment_2 is None                          # el adaptador registrado NO lleva la enmienda
    for name, adapter in _gi().region_witnesses().items():
        assert adapter.region_witnesses() == {}, "un conjunto no anida"
        assert adapter.amendment_2_witness == name and adapter.family == "gi_bleed"
        # el testigo difiere del perfil comprometido en UN campo, la enmienda, y en nada mas
        assert adapter.profile(fam.COMMITTED) == dataclasses.replace(committed, amendment_2=sc.WITNESSES[name])
    assert len({adapter.profile(fam.COMMITTED).amendment_2 for adapter in _gi().region_witnesses().values()}) == 3
    with pytest.raises(ValueError):
        fam.GiHaemorrhageAdapter.witness("MEAN")


def test_no_other_family_declares_the_amendment_in_any_adapter_or_point_or_witness():
    for family, adapter in fam.ADAPTERS.items():
        if family == "gi_bleed":
            continue
        declaration = adapter.region_declaration()
        assert declaration is None or declaration.parameter != fam.GI_AMENDMENT_2_FIELD, family
        for adapter_or_witness in [adapter, *adapter.region_witnesses().values()]:
            for point in (fam.COMMITTED, *fam.POINTS):
                assert adapter_or_witness.profile(point).amendment_2 is None, (family, point)
    assert {family for family, adapter in fam.ADAPTERS.items() if adapter.region_witnesses()} == {"opioid", "gi_bleed"}
    declaration = _gi().region_declaration()
    assert set(declaration.region["not_supported"]) == {"opioid", "acs", "pulmonary_edema", "pulmonary_embolism", "asthma"}
    assert declaration.region["supported_family"] == "gi_bleed" and "terminates" in declaration.region["state_only"]


def test_every_witness_names_the_provenance_of_each_magnitude_and_none_is_approved():
    names = set(sc.FIELDS)
    assert {name for fields in fam.GI_AMENDMENT_2_PROVENANCE.values() for name in fields} == names
    assert set(fam.GI_AMENDMENT_2_PROVENANCE) == {"F rise witness", "F fall witness", "relative-delivery thresholds",
                                                  "perfusion thresholds", "collapse persistence and recovery"}
    for name, adapter in _gi().region_witnesses().items():
        snapshot = adapter.snapshot(fam.COMMITTED)
        assert snapshot.approved is False and name.lower() in snapshot.id
        text = " ".join(snapshot.provenance)
        assert text.count("[DEVELOPMENT_BEHAVIORAL_REGION]") == len(fam.GI_AMENDMENT_2_PROVENANCE)
        assert sc.STATUS in text and "not a selection and not clinical truth" in text
        assert fam.GI_AMENDMENT_2_RECOVERY in snapshot.provenance
        extras = fam._gi_amendment_2_extras(adapter.profile(fam.COMMITTED))["provenance"]
        assert {field for group in extras.values() for field in group} == names
        assert all(row["status"] == "DEVELOPMENT_BEHAVIORAL_REGION" and row["origin"] == sc.IDENTIFIABILITY[field]
                   for group in extras.values() for field, row in group.items())
        assert {field: row["value"] for group in extras.values() for field, row in group.items()} == \
            sc.WITNESSES[name].to_dict()
    assert fam._gi_amendment_2_extras(_gi().profile(fam.COMMITTED)) == {"provenance": None}


def test_the_ensemble_opens_only_on_a_certified_lineage_whose_core_has_the_parameter(monkeypatch):
    opened = fam.RegionEnsemble.open("gi_bleed", "gi_bleed_72f")
    assert opened.refused is None and list(opened.runners) == WITNESSES and opened.parameter == "amendment_2"
    monkeypatch.setattr(ev, "core_lineage_ok", lambda: False)
    monkeypatch.setattr(ev, "core_lineage_reason", lambda: "the lineage is not certified")
    refused = fam.RegionEnsemble.open("gi_bleed", "gi_bleed_72f")
    assert refused.runners == {} and "not certified" in refused.refused
    assert refused.new_failures()[0].where == "ensemble:lineage"
    monkeypatch.undo()
    real = ev.core_lineage_verdict
    monkeypatch.setattr(ev, "core_lineage_verdict", lambda *a, **k: {**real(*a, **k), "active_core": "PHASE2_AMENDMENT_1"})
    wrong = fam.RegionEnsemble.open("gi_bleed", "gi_bleed_72f")
    assert wrong.runners == {} and "exists only in" in wrong.refused


# -- la sesion en vivo ---------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def short_live():
    """Un encuentro de GI de 40 minutos con la sombra encendida, y el mismo sin ella (la comparacion de no interferencia)."""
    orders = ("Place an IV line.", "Give 1 L of normal saline.", "Reassess in 5 minutes.")
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        on = acceptance.Encounter("gi_bleed_72f")
        for text in orders:
            on.order(text)
        on.wait_until(40)
    off = acceptance.Encounter("gi_bleed_72f")
    for text in orders:
        off.order(text)
    off.wait_until(40)
    return on, off


def test_the_live_session_keeps_its_own_committed_run_and_adds_three_witnesses_apart(short_live):
    on, _off = short_live
    session = on.shadow
    assert session.failures == [] and session.runner.profile.amendment_2 is None
    assert list(session.ensemble.runners) == WITNESSES
    assert {name: runner.profile.amendment_2 for name, runner in session.ensemble.runners.items()} == sc.WITNESSES
    record = session.ensemble.record()
    assert record["selected_witness"] is None and record["resident_visible"] is False and record["complete"] is True
    assert record["common_core_runtime_authority"] is False and record["runtime_authority"] == "legacy"
    assert record["classification"] == fam.GI_AMENDMENT_2_CLASSIFICATION and record["parameter"] == "amendment_2"
    assert {name: row["value"] for name, row in record["witnesses"].items()} == {n: p.to_dict() for n, p in sc.WITNESSES.items()}
    # el derivado es un MINIMO y un MAXIMO por minuto, junto a los valores individuales: nunca una media ni una trayectoria
    assert set(record["view"]) == {"consciousness_level", "delivery_rel", "pressure_rel", "output_rel"}
    row = record["view"]["consciousness_level"]["40"]
    assert set(row) == {"witnesses", "min", "max"} and set(row["witnesses"]) == set(WITNESSES)


def test_the_shadow_does_not_change_the_encounter_the_resident_the_ledger_or_the_clock(short_live):
    on, off = short_live
    assert on.minute == off.minute == 40
    assert json.dumps(on.state, sort_keys=True, default=str) == json.dumps(off.state, sort_keys=True, default=str)
    strip = lambda entries: [{k: v for k, v in entry.items() if k not in ("shadow", "shadow_record")} for entry in entries]
    assert json.dumps(strip(on.entries), sort_keys=True, default=str) == json.dumps(strip(off.entries), sort_keys=True, default=str)
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False


def test_the_trace_is_complete_verified_replays_exactly_and_names_the_boundary_beside_the_legacy_engine(traces):
    encounter = _play(GI, ("Place an IV line.", "Give 1 L of normal saline."), until=40)
    trace = _latest(encounter)
    assert sorted(trace["runs"]) == sorted(["SESSION_RUN", *WITNESSES]) and trace["expected_witnesses"] == WITNESSES
    assert trace["selected_witness"] is None and trace["region"]["parameter"] == "amendment_2"
    assert trace["region"]["status"] == sc.STATUS and trace["region"]["supported_family"] == "gi_bleed"
    checked = store.verify(trace)
    assert checked["verified"] and checked["lineage_matches"] and checked["inconsistencies"] == []
    replayed = store.replay(trace)
    assert replayed["replayed"] and replayed["reproduces"]
    assert all(run["reproduces"] for run in replayed["runs"].values()) and set(replayed["runs"]) == {"SESSION_RUN", *WITNESSES}
    # la corrida de la sesion NO lleva canales de la enmienda; cada testigo SI
    assert "category_index" not in trace["runs"]["SESSION_RUN"]["minutes"][-1]["channels"]
    for name in WITNESSES:
        last = trace["runs"][name]["minutes"][-1]["channels"]
        assert {"systemic_encephalopathy_burden", "collapse_burden", "relative_delivery", "relative_perfusion",
                "category_index", "collapse_state_index"} <= set(last)
        assert trace["runs"][name]["parameter"]["name"] == "amendment_2" and trace["runs"][name]["parameter"]["provenance"]
    boundary = trace["terminal_boundary"]
    assert boundary["decides_the_encounter"] == "legacy" and boundary["state"] == fam.BOTH_ACTIVE
    assert set(boundary["amendment_2"]["witnesses"]) == set(WITNESSES)
    assert "PHYSIOLOGICAL STATE ONLY" in boundary["amendment_2"]["note"]
    # editar el estado de un testigo en la traza (con el digesto recalculado) se ve: el limite se recalcula de la propia traza
    forged = copy.deepcopy(trace)
    forged["terminal_boundary"]["amendment_2"]["witnesses"]["LOW"]["state"] = fam.COLLAPSE_ESTABLISHED_LEGACY_ACTIVE
    assert store.verify(_resealed(forged))["verified"] is False
    # la guia docente de GI trae las preguntas de la enmienda y el limite explicito
    entry = obs.review_entry(trace)
    assert entry["selected_witness"] is None and len(entry["witnesses"]) == 3
    index = obs.review_markdown([entry])
    assert "Amendment-2 witnesses beside the legacy engine" in index and "PHYSIOLOGICAL STATE ONLY" in index
    assert any("recovery look too FAST or too SLOW" in question for question in entry["faculty_questions"])
    assert any("SAME shadow impairment timeline" in question for question in entry["faculty_questions"])


# -- P3-178: el limite terminal, sus cinco estados -------------------------------------------------------------------------------

def _witness(collapse, category=3, pulse=True):
    return {"collapse_state_index": collapse, "category_index": category, "pulse_present": pulse}


def test_every_collapse_state_beside_the_legacy_engine_is_explicit_and_none_is_a_silent_contradiction():
    active, ended = {"arrest_at": None, "vf_at": None}, {"arrest_at": 120, "vf_at": None}
    cases = (
        (active, _witness(2), fam.COLLAPSE_ESTABLISHED_LEGACY_ACTIVE),
        (active, _witness(1), fam.COLLAPSE_IMPENDING_LEGACY_ACTIVE),
        (active, _witness(0, 0), fam.NO_COLLAPSE_LEGACY_ACTIVE),
        (active, _witness(0, 3, pulse=False), fam.COLLAPSE_ESTABLISHED_LEGACY_ACTIVE),      # sin pulso: camino duro
        (ended, _witness(2), fam.LEGACY_TERMINAL_COLLAPSE_ESTABLISHED),
        (ended, _witness(0, 0), fam.LEGACY_TERMINAL_WITHOUT_ESTABLISHED_COLLAPSE),          # el heredado termina por OTRA razon
        (ended, _witness(1, 2), fam.LEGACY_TERMINAL_WITHOUT_ESTABLISHED_COLLAPSE),
    )
    for legacy, channels, expected in cases:
        boundary = fam.terminal_boundary(legacy, {"pulse_present": True}, False, {"LOW": channels})
        assert boundary["amendment_2"]["witnesses"]["LOW"]["state"] == expected, (legacy, channels)
        assert boundary["decides_the_encounter"] == "legacy"
    # un testigo sin lectura, o un registro heredado que no es una lectura, no se compara: se dice
    assert fam.terminal_boundary(None, {"pulse_present": True}, False, {"LOW": _witness(2)})["amendment_2"][
        "witnesses"]["LOW"]["state"] == fam.WITNESS_NOT_COMPARABLE
    assert fam.terminal_boundary(active, {"pulse_present": True}, False, {"LOW": _witness(None)})["amendment_2"][
        "witnesses"]["LOW"]["state"] == fam.WITNESS_NOT_COMPARABLE
    assert fam.terminal_boundary("not a record", {"pulse_present": True}, False, {"LOW": _witness(2)})["amendment_2"][
        "witnesses"]["LOW"]["state"] == fam.WITNESS_NOT_COMPARABLE
    # una familia sin canales de la enmienda no gana el bloque: su traza es la de siempre
    assert "amendment_2" not in fam.terminal_boundary(active, {"pulse_present": True}, False,
                                                      {"LOW": {"respiratory_rate": 12}})
    assert set(fam.WITNESS_COLLAPSE_STATES) >= {case[2] for case in cases}


def test_the_boundary_record_says_the_zero_output_with_pulse_boundary_is_not_moved_and_ends_nothing():
    for case in CASES:
        row = RECORD["boundary"][case]
        assert row["boundary_minute"] == 349 and row["exception"] == "UnresolvedBoundary" and row["classification"] == "COMMON_BOUNDARY"
        # la sesion y los tres testigos tocan la MISMA frontera en el MISMO minuto: la enmienda no la mueve
        assert row["failures"] == ["core", "ensemble:LOW:core", "ensemble:CENTER_REFERENCE:core", "ensemble:HIGH:core"]
        assert row["legacy_arrested"] is False and row["legacy_at_boundary"]["pulse_present"] is True
        assert row["terminal_boundary_state"] == fam.BOTH_ACTIVE
        assert row["amendment_2_witness_state"] == fam.COLLAPSE_ESTABLISHED_LEGACY_ACTIVE
        assert row["witness_state_at_boundary"] == {"collapse_state": "ESTABLISHED", "category": "UNRESPONSIVE", "F": 1.0,
                                                    "collapse_burden": 1.0, "pulse_present": True}


# -- P3-175/176: la serie contra el registro medido ------------------------------------------------------------------------------

def _compare(run_summary, scenario_key):
    """Lo recalculado de un escenario contra lo registrado, testigo por testigo."""
    recorded = RECORD["runs"][scenario_key]
    assert run_summary["minutes_played"] == recorded["minutes_played"]
    assert run_summary["treatment_minute"] == recorded["treatment_minute"] and run_summary["triggered_at"] == recorded["triggered_at"]
    for name, item in run_summary["witnesses"].items():
        old = recorded["witnesses"][name]
        assert [list(step) for step in item["category_sequence"]] == [list(step) for step in old["category_sequence"]], name
        assert round(item["f_peak"], 4) == old["f_peak"], name
        for key, value in old["order"].items():
            assert item["order"][key] == value, (name, key)
        for key, value in old["recovery"].items():
            got = item["recovery"].get(key)
            assert (round(got, 4) if isinstance(got, float) else got) == value, (name, key)
        for key in ("minutes_compared", "minutes_that_differ", "shadow_above_legacy", "shadow_below_legacy"):
            assert item["legacy"][key] == old["legacy"][key], (name, key)


@pytest.mark.parametrize("scenario", ["early_treatment", "recovery_after_severe"])
def test_a_live_series_reproduces_what_was_recorded_digest_free_and_apart_per_witness(scenario):
    run = series.run_scenario("gi_bleed_72f", scenario)
    summary = series.summarise(run)
    _compare(summary, f"gi_bleed_72f/{scenario}")
    assert summary["session_failures"] == [] and all(item["failures"] == [] for item in summary["witnesses"].values())
    assert run["legacy_arrested"] is False


def test_a_live_untreated_series_reproduces_the_recorded_onsets_and_the_collapse_through_minute_215():
    """El curso sin tratar hasta el minuto 215 (la serie registrada llega a 240): los inicios de cada eslabon, y el colapso
    inminente de cada testigo, son los registrados. Un colapso que llegara por una sola falla, o antes, no coincidiria."""
    run = series.run_scenario("gi_bleed_72f", "untreated", horizon=215)
    summary = series.summarise(run)
    for name, item in summary["witnesses"].items():
        old = RECORD["runs"]["gi_bleed_72f/untreated"]["witnesses"][name]["order"]
        for key in ("volume_below_arrival", "delivery_below_normal_bound", "perfusion_below_normal_bound", "f_above_zero",
                    "somnolent", "obtunded", "unresponsive", "collapse_impending"):
            assert item["order"][key] == old[key], (name, key)
        assert item["order"]["chain_in_order"] is True and item["order"]["collapse_needs_both_failures"] is True
    assert summary["session_failures"] == [] and run["legacy_arrested"] is False


def test_no_direct_pressure_saturation_fluid_or_red_cell_input_reaches_the_consciousness_composite():
    """P3-175A: la consciencia lee la entrega y la perfusion RELATIVAS a la llegada, F y el estado de colapso; ninguna entrada
    directa de PAS, SpO2, liquidos ni globulos rojos (esos actuan sobre V, y V sobre la entrega, mucho antes)."""
    import ast
    import inspect
    names = set()
    for node in ast.walk(ast.parse(inspect.getsource(sc))):
        for attribute in ("id", "attr", "arg", "name"):
            value = getattr(node, attribute, None)
            if isinstance(value, str):
                names.add(value.lower())
    forbidden = ("sbp", "dbp", "systolic", "spo2", "saturation", "fluid", "crystalloid", "transfus", "rbc", "red_cell", "saline",
                 "gcs", "opioid", "naloxone", "legacy")
    assert not [name for name in names if any(word in name for word in forbidden)]


def test_the_recorded_series_holds_the_required_causal_order_on_every_run_and_every_witness():
    assert sorted(RECORD["runs"]) == sorted(f"{case}/{scenario}" for case in CASES for scenario in RECORD["scenarios"])
    impaired = 0
    for key, run in RECORD["runs"].items():
        for name, item in run["witnesses"].items():
            order = item["order"]
            assert order["category_never_skips_up"] is True, (key, name)
            if order["somnolent"] is not None:
                impaired += 1
                # hemorragia -> volumen -> entrega -> F -> categoria observable, en ese orden
                assert order["chain_in_order"] is True, (key, name)
                assert order["volume_below_arrival"] <= order["delivery_below_normal_bound"] <= order["f_above_zero"] <= order["somnolent"]
            if order["collapse_impending"] is not None:
                # el colapso necesita entrega Y perfusion fallando, y llega DESPUES de la consciencia alterada
                assert order["collapse_needs_both_failures"] is True, (key, name)
                assert order["somnolent"] < order["collapse_impending"]
                if order["collapse_established"] is not None:
                    assert order["collapse_impending"] <= order["collapse_established"]
            if order["collapse_established"] is not None:
                assert order["collapse_established"] > order["unresponsive"] - 1
            assert order["f_above_zero"] is None or order["delivery_below_normal_bound"] is not None
    assert impaired >= 20
    # una condicion mas fuerte: ningun registro tiene un colapso sin consciencia alterada antes
    for run in RECORD["runs"].values():
        for item in run["witnesses"].values():
            if item["order"]["collapse_impending"] is not None:
                assert item["order"]["somnolent"] is not None


def test_the_recorded_recovery_follows_the_faculty_reading_of_three_to_five_minutes_from_the_upstream():
    import math
    for name, profile in sc.WITNESSES.items():
        # 0.80 -> por debajo de 0.50 por la ley de primer orden de la constante de limpieza de CADA testigo: 3 a 5 minutos
        assert 3.0 <= profile.burden_clear_tau * math.log(0.8 / 0.5) <= 5.0, name
    observed = 0
    for key, run in RECORD["runs"].items():
        for name, item in run["witnesses"].items():
            recovery = item["recovery"]
            if not recovery.get("applicable") or recovery.get("minutes_upstream_to_below_0_50") is None:
                continue
            observed += 1
            # desde que lo de aguas arriba se recupero, F cruza 0.50 como dice su propia ley (+- el redondeo del minuto)
            assert abs(recovery["minutes_upstream_to_below_0_50"] - recovery["minutes_upstream_to_below_0_50_by_the_law"]) <= 1.5, (key, name)
            # la categoria desciende tras el tratamiento (no se exige normalizar por debajo de 0.25 en ese intervalo)
            assert recovery["first_category_descent_at"] is not None
    assert observed >= 4
    # tras el tratamiento tardio y el de rescate, la categoria vuelve a la de llegada (0) por el final de la serie
    for key in ("gi_bleed_72f/recovery_after_severe", "gi_bleed_57m/recovery_after_severe"):
        for name, item in RECORD["runs"][key]["witnesses"].items():
            assert item["recovery"]["category_at_end"] == 0, (key, name)


def test_the_two_gi_cases_read_the_same_shadow_timeline_while_the_legacy_ladder_separates_them():
    """HALLAZGO registrado para la docencia, y fijado: la lectura de la enmienda es RELATIVA a la llegada de cada paciente, asi
    que dos pacientes que pierden volumen a la misma tasa leen igual, y la escalera heredada (absoluta en PAS) los separa. No se
    ajusta nada para igualarlos ni para separarlos: se informa, y si el mapeo de llegada cambia, esta prueba lo avisa."""
    for scenario in RECORD["scenarios"]:
        for name in WITNESSES:
            a = RECORD["runs"][f"gi_bleed_57m/{scenario}"]["witnesses"][name]
            b = RECORD["runs"][f"gi_bleed_72f/{scenario}"]["witnesses"][name]
            assert a["category_sequence"] == b["category_sequence"] and a["f_peak"] == b["f_peak"], (scenario, name)
    untreated = {case: RECORD["runs"][f"{case}/untreated"]["witnesses"]["CENTER_REFERENCE"]["legacy"]["first_impairment"]["legacy"]
                 for case in CASES}
    assert untreated["gi_bleed_57m"] == 63 and untreated["gi_bleed_72f"] == 138


def test_the_legacy_comparison_finds_no_contradiction_and_the_legacy_engine_never_ended_a_series():
    for key, run in RECORD["runs"].items():
        assert run["failures"] == 0, key
        for name, item in run["witnesses"].items():
            assert item["legacy"]["contradiction_minutes"] == 0, (key, name)


# -- P3-179: mutantes y controles de la capa ---------------------------------------------------------------------------------------

def _trace_of_a_live_session():
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter("gi_bleed_72f")
        encounter.order("Give 1 L of normal saline.")
        encounter.wait_until(15)
    return encounter.shadow


def test_control_a_healthy_session_passes_every_layer_detector():
    session = _trace_of_a_live_session()
    trace = json.loads(json.dumps(store.trace_of(session), default=str))
    assert store.is_a_trace(trace) and trace["selected_witness"] is None and trace["common_core_runtime_authority"] is False
    assert session.ensemble.record()["selected_witness"] is None


def test_mutant_a_witness_that_is_selected_is_not_a_trace(monkeypatch):
    session = _trace_of_a_live_session()
    trace = json.loads(json.dumps(store.trace_of(session), default=str))
    selected = {**trace, "selected_witness": "CENTER_REFERENCE"}
    assert store.is_a_trace(selected) is False and store.verify(_resealed(selected))["verified"] is False


def test_mutant_authority_accidentally_enabled_is_refused_by_the_trace_label_and_the_ensemble_record(monkeypatch):
    session = _trace_of_a_live_session()
    monkeypatch.setattr(rs, "COMMON_CORE_RUNTIME_AUTHORITY", True)
    trace = json.loads(json.dumps(store.trace_of(session), default=str))
    assert trace["common_core_runtime_authority"] is True and store.is_a_trace(trace) is False
    assert store.verify(trace)["verified"] is False


def test_mutant_the_amendment_enabled_outside_gi_is_caught_by_the_guard(monkeypatch):
    original = fam.AsthmaAdapter.profile
    monkeypatch.setattr(fam.AsthmaAdapter, "profile",
                        lambda self, point: dataclasses.replace(original(self, point), amendment_2=sc.WITNESSES["LOW"]))
    with pytest.raises(AssertionError):
        test_no_other_family_declares_the_amendment_in_any_adapter_or_point_or_witness()


def test_mutant_a_replay_that_cannot_reproduce_the_recorded_witness_is_detected(monkeypatch):
    session = _trace_of_a_live_session()
    trace = json.loads(json.dumps(store.trace_of(session), default=str))
    assert store.replay(trace)["reproduces"] is True
    real = sc.readout

    def moved(state, anchors, core_profile, pressure_rel=None, delivery_rel=None):
        reading = dict(real(state, anchors, core_profile, pressure_rel, delivery_rel))
        reading["category_index"] = (reading["category_index"] + 1) % 4
        return reading

    monkeypatch.setattr(sc, "readout", moved)
    assert store.replay(trace)["reproduces"] is False


def test_mutant_a_shadow_that_writes_into_the_encounter_is_detected_by_the_non_interference_comparison(monkeypatch):
    orders = ("Place an IV line.", "Give 1 L of normal saline.")
    real = rs.ShadowSession.capture

    def leaky(self, state):
        state["shadow_wrote_here"] = 1                              # la sombra escribe en el paciente
        return real(self, state)

    def run():
        with ev.shadow(rs.MODE_SHADOW_COMPARE):
            encounter = acceptance.Encounter("gi_bleed_72f")
            for text in orders:
                encounter.order(text)
            encounter.wait_until(12)
        return json.dumps(encounter.state, sort_keys=True, default=str)

    off = acceptance.Encounter("gi_bleed_72f")
    for text in orders:
        off.order(text)
    off.wait_until(12)
    healthy = json.dumps(off.state, sort_keys=True, default=str)
    assert run() == healthy
    monkeypatch.setattr(rs.ShadowSession, "capture", leaky)
    assert run() != healthy
