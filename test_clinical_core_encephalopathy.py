"""P2L-2: the common systemic-encephalopathy architecture (shadow only, candidate off unless called).

The candidate physiology (encephalopathy.py): N reserved for the primary neurologic state; six acute systemic signals,
each from one certified reading, aggregated by their maximum; the systemic memory F; the observable as the maximum of N,
the acute stress and F; the legacy ladders, the arrival floor, lactate, D and the heart rate never read; nothing written.
Its structural evaluation (encephalopathy_architecture.py): N1-N12 on synthetic normalized signals, the threshold-free
orthogonality and isolation probes on fixed core states at both retained ventilation gains, the tone loop and the carried
extreme-acidemia subset from the pinned P2L-1 record, the generalization, the verdict; the closure of everything before.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import math

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import gas_exchange_architecture as go
from clinical_core import lung_water_reference as lw
from clinical_core import edema_migration as pe
from clinical_core import respiratory_drive as rd
from clinical_core import embolism_migration as em
from clinical_core import consciousness_audit as ca
from clinical_core import decision_pack, lactate_slice
from clinical_core import encephalopathy as enc
from clinical_core import encephalopathy_architecture as ea
from clinical_core import vascular_tone as vt
from clinical_core import ventilation_surface as vs
from clinical_core.state import CoreInvariantError

ROOT = ea.ROOT
PHYSIOLOGY = ROOT / "clinical_core" / "encephalopathy.py"
ANALYSIS = ROOT / "clinical_core" / "encephalopathy_architecture.py"
#: The P2L-2 freeze: the candidate physiology, the faculty decisions, the synthetic probe design, the physiological
#: probes, the criteria, the verdict and next rules, and every clinical_core source but the downstream reports, committed
#: before the evaluation run.
FROZEN_DIGEST = "970db00d1f7e84c1f5fd752f34af452955f873f4ba0ebae32a5cd5c2887e70df"
#: A synthetic mapping for the ramp's own unit tests only (never a profile value, never a clinical bound).
TEST_MAPPING = enc.SignalMapping(normal=10.0, severe=0.0)


#: P2M-1's layer, added after P2L-2 closed: this package's view of the tree leaves it out (collapse_audit.p2l2_sources:
#: the audit removed, the tuple-only files at their P2L-2 hashes while only their tuples changed; P2L-1's frozen N scan
#: without the audit); the record is unchanged.
#: P2O-3 replaced declared lines of derived.py, integration.py, state.py, modules/acs_ischaemia.py and two tuple
#: files, proven byte for byte against the P2O-1 files (lung_water_reference.proved): this package's guards read
#: the P2O-1 files through P2O-1's view of the P2N-2 core (lw.chain, lw.p2o1_sources); the record is unchanged.
#: P2P-1 added files (the edema family, its mapping and analysis) and two tuple entries, proven against the P2O-3
#: files (edema_migration.proved): this package's guards read the tree as P2O-3 left it (pe.chain, pe.p2o3_sources).
#: P2P-2 changed the core (the respiratory-drive composition, inert by default) and two tuple files, proven against
#: the P2P-1 files (respiratory_drive.proved): this package's guards read the tree as P2P-1 left it (rd.chain,
#: rd.p2p1_sources).
#: P2Q-2 added files (the PE family, its mapping and analysis) and two tuple entries, proven against the P2P-2
#: files (embolism_migration.proved): this package's guards read the tree as P2P-2 left it (em.chain,
#: em.p2p2_sources).
_LIVE_SOURCES_P2Q2 = bf.freeze_sources


def _LIVE_SOURCES_P2P2() -> dict:
    return em.p2p2_sources(_LIVE_SOURCES_P2Q2())


def _LIVE_SOURCES_P2P1() -> dict:
    return rd.p2p1_sources(_LIVE_SOURCES_P2P2())


def _LIVE_SOURCES_P2O3() -> dict:
    return pe.p2o3_sources(_LIVE_SOURCES_P2P1())


def _LIVE_SOURCES_P2O1() -> dict:
    return lw.p2o1_sources(_LIVE_SOURCES_P2O3())


def _FREEZE_SOURCES() -> dict:
    # P2O-1 inserted its declared, inert names into derived.py and integration.py, proven byte for byte against the
    # P2N-2 files (gas_exchange_architecture.proved): this view starts from the P2N-2 core, P2O-1's analysis left out.
    return go.p2n2_sources(_LIVE_SOURCES_P2O1())


_PYTHON, _EA_IMPORTED_BY = ca._python, ea.imported_by
LATER_MODULES = ("clinical_core/collapse_audit.py", "clinical_core/collapse.py",
                 "clinical_core/collapse_architecture.py",
                 "clinical_core/acs_reference.py", "clinical_core/modules/acs_ischaemia.py",
                 "clinical_core/acs_migration.py", "clinical_core/gas_exchange_architecture.py",
                 "clinical_core/lung_water_reference.py",
                 "clinical_core/edema_migration.py", "clinical_core/edema_reference.py",
                 "clinical_core/modules/pulmonary_edema.py",
                 "clinical_core/respiratory_drive.py",
                 "clinical_core/embolism_reference.py", "clinical_core/modules/pulmonary_embolism.py",
                 "clinical_core/embolism_migration.py")


def _p2l2_view() -> dict:
    from clinical_core import collapse_audit as cm
    from clinical_core import collapse_architecture as cy
    from clinical_core import acs_migration as an
    return cm.p2l2_sources(cy.p2m1_sources(an.p2m2_sources(_FREEZE_SOURCES())))


def _p2l2_python() -> list:
    later = {ROOT / relative for relative in LATER_MODULES}
    # P2O-1: the scans read the two core files as P2N-2 left them (go.p2n2_path, proven).
    return [go.p2n2_path(p) for p in _PYTHON() if p not in later]


def _patch(patch) -> None:
    lw.chain(patch)
    pe.chain(patch)
    rd.chain(patch)
    em.chain(patch)
    patch.setattr(bf, "freeze_sources", _p2l2_view)
    patch.setattr(ca, "_python", _p2l2_python)
    # P2O-1's analysis imports the candidate only to read its hypoxaemia signal (the candidate unchanged).
    patch.setattr(ea, "imported_by", lambda: [p for p in _EA_IMPORTED_BY() if p != go.OWN[0]])


@pytest.fixture(autouse=True)
def _p2l2_tree(monkeypatch):
    _patch(monkeypatch)


@pytest.fixture(scope="module")
def result():
    with pytest.MonkeyPatch.context() as patch:
        _patch(patch)
        return ea.run()


# The frozen package and its closure ------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert set(ea.OWN) <= set(sources) and ea.REPORT not in sources
    assert ea.REPORT in lactate_slice.DOWNSTREAM_REPORTS
    # The analysis and its report leave the P2G pack digest; the candidate physiology stays in it (as ventilation.py).
    assert {ea.OWN[1], ea.REPORT} <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    assert ea.OWN[0] not in decision_pack.PACK_DIGEST_EXCLUDED
    assert ca._record(ea.P2L1_RECORD, ea.P2L1_RECORD_SHA)["verdict"]["verdict"] == \
        "CONSCIOUSNESS_STRUCTURE_NOT_READY - RECOVERY_LAG_STATE_REQUIRED"
    if FROZEN_DIGEST is not None:
        assert ea.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_the_p2l1_tree_is_byte_identical_and_no_core_module_reads_the_candidate():
    up = ea.upstream_unchanged()
    assert up["unchanged"] and (up["digest"], up["files"]) == ea.SOURCES_AT_P2L1
    assert up["imported_by"] == ["clinical_core/encephalopathy_architecture.py"]
    mapped = ea.p2l1_sources(bf.freeze_sources())
    assert not set(ea.OWN) & set(mapped)
    for relative, sha in ea.TUPLE_AT_P2L1.items():
        assert mapped[relative] == sha
    original = vt._live
    try:
        vt._live = lambda relative: original(relative) + "\nX = 1\n"
        assert ea.p2l1_sources(bf.freeze_sources())["clinical_core/decision_pack.py"] == \
            bf.freeze_sources()["clinical_core/decision_pack.py"]
    finally:
        vt._live = original


def test_the_physiology_imports_only_the_certified_core():
    tree = ast.parse(PHYSIOLOGY.read_text(encoding="utf-8"))
    modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert modules == {"__future__", "dataclasses", "derived", "state"}
    assert {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} == {"math"}
    analysis = ANALYSIS.read_text(encoding="utf-8")
    for forbidden in ("import family_engine", "legacy_adapter", "snapshot(", "clinical_cases"):
        assert forbidden not in analysis and forbidden not in PHYSIOLOGY.read_text(encoding="utf-8")


# The candidate physiology ----------------------------------------------------------------------------------------------

def test_the_committed_profile_declares_no_number():
    default = enc.DEFAULT_ENCEPHALOPATHY
    assert default.mappings == () and not default.memory_declared
    assert default.burden_rise_tau is None and default.burden_clear_tau is None
    with pytest.raises(CoreInvariantError, match="UNSET"):
        enc.burden_after(0.0, 0.5, 1.0, default)
    state, anchors, profile, gas = ea._probe({}, 0.04)
    reasons = dict(enc.acute_signals(enc.readings(state, anchors, profile, gas), default).reasons)
    assert set(reasons) == set(enc.SIGNALS) and set(reasons.values()) == {"UNMAPPED"}
    assert {name: enc.STATUS[name] for name in ("signals", "memory")} == {
        "signals": "STRUCTURALLY_DEFINED_BUT_CLINICALLY_UNIDENTIFIED: no bound has a committed value (UNMAPPED)",
        "memory": enc.STATUS["memory"]} and enc.STATUS["memory"].startswith("STRUCTURALLY_DEFINED_BUT_CLINICALLY")


def test_the_profile_invariants():
    with pytest.raises(CoreInvariantError, match="impaired side"):
        enc.EncephalopathyProfile(mappings=(("cerebral_hypoperfusion", enc.SignalMapping(50.0, 60.0)),))
    with pytest.raises(CoreInvariantError, match="impaired side"):
        enc.EncephalopathyProfile(mappings=(("hypercapnia", enc.SignalMapping(50.0, 40.0)),))
    with pytest.raises(CoreInvariantError, match="once"):
        enc.EncephalopathyProfile(mappings=(("lactate", TEST_MAPPING),))
    with pytest.raises(CoreInvariantError, match="once"):
        enc.EncephalopathyProfile(mappings=(("hypoxaemia", TEST_MAPPING), ("hypoxaemia", TEST_MAPPING)))
    with pytest.raises(CoreInvariantError, match="together"):
        enc.EncephalopathyProfile(burden_rise_tau=1.0)
    for rise, clear in ((2.0, 2.0), (3.0, 1.0), (0.0, 1.0), (1.0, math.inf)):
        with pytest.raises(CoreInvariantError, match="rises faster"):
            enc.EncephalopathyProfile(burden_rise_tau=rise, burden_clear_tau=clear)


def test_the_ramp_is_monotone_saturating_and_zero_on_the_normal_side():
    low = [enc.ramp(v, TEST_MAPPING, enc.LOW) for v in (20.0, 10.0, 7.5, 5.0, 0.0, -5.0)]
    assert low == [0.0, 0.0, 0.25, 0.5, 1.0, 1.0]
    high_mapping = enc.SignalMapping(normal=0.0, severe=10.0)
    assert [enc.ramp(v, high_mapping, enc.HIGH) for v in (-1.0, 0.0, 2.5, 10.0, 12.0)] == [0.0, 0.0, 0.25, 1.0, 1.0]
    # Mapped through a declared profile: each signal reads its own reading only.
    profile = enc.EncephalopathyProfile(mappings=(("hypoglycaemia", enc.SignalMapping(70.0, 30.0)),))
    reading = {"pulse": True, "map": 90.0, "spo2": 97.0, "glucose": 50.0, "deficit_fraction": 0.0, "ph": None,
               "paco2": None}
    signals = enc.acute_signals(reading, profile)
    assert signals.value("hypoglycaemia") == 0.5
    assert dict(signals.reasons) == {"cerebral_hypoperfusion": "UNMAPPED", "oxygen_deficit": "UNMAPPED",
                                     "hypoxaemia": "UNMAPPED", "acidemia": "UNAVAILABLE",
                                     "hypercapnia": "UNAVAILABLE", "hypoglycaemia": "MAPPED"}


def test_the_acute_aggregation_is_the_maximum_never_the_sum():
    for values in ({"a": 0.5, "b": 0.6, "c": 0.4}, {"a": 0.0}, {"a": 1.0, "b": 1.0}, {"a": None, "b": 0.2}, {}):
        assert enc.systemic_acute_brain_stress(values) == max([v for v in values.values() if v is not None],
                                                               default=0.0)
    assert enc.systemic_acute_brain_stress({"a": 0.5, "b": 0.6, "c": 0.4}) < 1.5
    for bad in (-0.1, 1.1, math.nan):
        with pytest.raises(CoreInvariantError, match="impairment scale"):
            enc.systemic_acute_brain_stress({"a": bad})


def test_the_memory_has_the_required_properties():
    profile = ea.probe_profile()
    f = enc.burden_after(0.0, 0.8, 1.0, profile)
    assert f == pytest.approx(0.8 * (1.0 - math.exp(-1.0)))                   # rises toward S with tau_rise
    g = enc.burden_after(f, 0.0, 1.0, profile)
    assert g == pytest.approx(f * math.exp(-1.0 / profile.burden_clear_tau))  # clears with tau_clear
    assert 0.0 < g < f                                                         # persists, falls, stays positive
    assert enc.burden_after(0.5, 0.5, 3.0, profile) == 0.5
    for start, stress in ((0.0, 0.9), (0.9, 0.0), (0.3, 0.7), (0.7, 0.3)):
        nxt = enc.burden_after(start, stress, 0.25, profile)
        assert min(start, stress) <= nxt <= max(start, stress)                # between F and S: never past S
    brief = enc.burden_course([0.9] * 4, 0.25, profile)[-1]
    prolonged = enc.burden_course([0.9] * 24, 0.25, profile)[-1]
    assert brief < prolonged < 0.9
    with pytest.raises(CoreInvariantError, match="impairment scale"):
        enc.burden_after(-0.1, 0.0, 1.0, profile)
    with pytest.raises(CoreInvariantError, match="non-negative"):
        enc.burden_after(0.1, 0.0, -1.0, profile)
    # The memory reads no N, D, lactate or authored level: the names and attributes of its code (docstring aside).
    tree = ast.parse(inspect.getsource(enc.burden_after))
    used = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} | {
        n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {a.arg for a in tree.body[0].args.args}
    assert not used & {"N", "D", "lactate", "lactate_excess_mmol_l", "consciousness_level", "state"}
    assert {a.arg for a in tree.body[0].args.args} == {"burden", "stress", "dt", "profile"}


def test_the_observable_is_the_maximum_and_n_is_only_read():
    out = enc.observable_impairment(0.4, 0.7, 0.2)
    assert out["impairment"] == 0.7 and out["dominant"] == ["acute"] and out["components"]["primary"] == 0.4
    assert enc.observable_impairment(0.0, 0.0, 0.0) == {"impairment": 0.0, "components": {
        "primary": 0.0, "acute": 0.0, "memory": 0.0}, "dominant": []}
    state, anchors, profile, gas = ea._probe({"N": 0.3}, 0.04)
    assert enc.primary_from_state(state) == 0.3 == state.N
    for bad in (-0.1, 1.5):
        with pytest.raises(CoreInvariantError, match="primary N"):
            enc.primary_neurologic_impairment(bad)
    source = inspect.getsource(enc.observable_impairment)
    assert "+" not in source and "sum(" not in source


def test_circulatory_arrest_is_maximal_hypoperfusion_without_any_mapping():
    reading = {"pulse": False, "map": None, "spo2": None, "glucose": 100.0, "deficit_fraction": None, "ph": None,
               "paco2": None}
    signals = enc.acute_signals(reading, enc.DEFAULT_ENCEPHALOPATHY)
    assert signals.value("cerebral_hypoperfusion") == 1.0 and dict(signals.reasons)["cerebral_hypoperfusion"] == \
        "ARREST"
    assert enc.systemic_acute_brain_stress(dict(signals.values)) == 1.0
    assert enc.admissible_support(reading, reading)["cerebral_hypoperfusion"] == "MAXIMAL_ARREST"


def test_the_readings_are_the_certified_cores_and_write_nothing():
    for spec in ({}, {"T": 0.45}, {"hb_share": 0.3}, {"burden": 15.0}, {"glucose": 30.0}):
        state, anchors, profile, gas = ea._probe(spec, 0.04)
        before = state.to_dict() if hasattr(state, "to_dict") else repr(state)
        reading = enc.readings(state, anchors, profile, gas)
        certified = ca.reading(state, anchors, profile)
        assert {k: reading[k] for k in ("map", "spo2", "glucose", "deficit_fraction")} == \
            {k: certified[k] for k in ("map", "spo2", "glucose", "deficit_fraction")}
        assert (reading["ph"], reading["paco2"]) == (gas.ph, gas.paco2)
        assert (state.to_dict() if hasattr(state, "to_dict") else repr(state)) == before
    no_gas = enc.readings(state, anchors, profile)
    assert no_gas["ph"] is None and no_gas["paco2"] is None


def test_the_candidate_never_reads_the_legacy_ladders_lactate_d_or_the_heart_rate(result):
    scan = result["scan"]
    assert scan["forbidden_reads"] == [] and scan["writes_state"] == [] and scan["disease_terms"] == []
    assert scan["sum_calls"] is False and not any(scan["aggregation_adds"].values())
    assert all(scan["aggregation_by_max"].values()) and scan["reads_n_only_through"] == "primary_from_state"
    assert {k: v[0] for k, v in enc.SIGNALS.items()} == {
        "cerebral_hypoperfusion": "map", "oxygen_deficit": "deficit_fraction", "hypoxaemia": "spo2", "acidemia": "ph",
        "hypercapnia": "paco2", "hypoglycaemia": "glucose"}
    assert "pharmacologic_cns_depression" not in enc.SIGNALS
    assert enc.FUTURE_MODIFIERS["pharmacologic_cns_depression"].startswith("FUTURE_COMMON_SYSTEMIC_OR_PHARMACOLOGIC")


#: Names the candidate must never read, by attribute or by string (the frozen scan sees attributes only; P2L-2 review M2).
STRING_FORBIDDEN = set(ea.FORBIDDEN_READS) | {"N"}


def _string_reads(tree) -> set:
    """Reads by string: getattr(x, "name"), vars(x)["name"] / x["name"] subscripts, x.get("name")."""
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "getattr" and len(node.args) > 1 \
                and isinstance(node.args[1], ast.Constant):
            out.add(node.args[1].value)
        elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
            out.add(node.slice.value)
        elif isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "get" and node.args \
                and isinstance(node.args[0], ast.Constant):
            out.add(node.args[0].value)
    return out


def test_the_scans_catch_planted_reads_and_the_physiology_has_none(tmp_path, monkeypatch):
    # The physiology reads no forbidden name by string either; it reads N once, by attribute, in primary_from_state.
    tree = ast.parse(PHYSIOLOGY.read_text(encoding="utf-8"))
    assert not _string_reads(tree) & STRING_FORBIDDEN
    readers = [n for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr == "N"]
    assert len(readers) == 1 and readers[0].lineno == 189
    # A planted copy: the frozen attribute scan catches the attribute read and the write; the string scan the rest.
    planted = tmp_path / "encephalopathy.py"
    planted.write_text(PHYSIOLOGY.read_text(encoding="utf-8") + "\n\ndef _planted(state, d, anchors):\n"
                       "    a = state.lactate\n    b = state.evolve(N=1.0)\n    c = getattr(d, 'sbp')\n"
                       "    return vars(anchors)['consciousness_level'], a, b, c\n", encoding="utf-8")
    monkeypatch.setattr(ea, "PHYSIOLOGY_SOURCE", planted)
    scan = ea.candidate_scan()
    assert "lactate" in scan["forbidden_reads"] and "evolve" in scan["writes_state"] and "N" in scan["writes_state"]
    assert {"sbp", "consciousness_level"} <= _string_reads(ast.parse(planted.read_text(encoding="utf-8")))


# The structural evaluation -----------------------------------------------------------------------------------------------

def test_n_is_reserved_for_the_primary_state(result):
    n = result["n"]
    assert n["writers"] == ["state.py:697"] and n["readers"] == ["encephalopathy.py:189"]
    assert n["semantics"].startswith("PRIMARY_NEUROLOGIC_STATE") and "DOCUMENTED_SEMANTIC_DEBT" in n["closed_wording"]


def test_the_neuro_probes_pass_at_every_synthetic_ratio(result):
    rows = result["neuro_probes"]["rows"]
    assert set(rows) == {f"N{i}" for i in range(1, 13)} and all(r["passes"] for r in rows.values())
    assert result["ratio_robustness"]["all_pass"] and set(result["ratio_robustness"]["by_ratio"]) == {"2", "4", "8"}
    assert rows["N9"]["stress"] == 0.6 < rows["N9"]["sum_would_be"]
    assert rows["N10"]["stress_at_restoration"] == 0.0 < rows["N10"]["burden_at_restoration"]
    n11 = rows["N11"]
    assert n11["brief"]["memory_area"] < n11["repeated"]["memory_area"] and \
        n11["brief"]["memory_area"] < n11["prolonged"]["memory_area"]
    assert rows["N12"]["burden_independent_of_n"] and rows["N2"]["max_burden"] == 0.0


def test_the_orthogonality_and_isolation_probes_at_both_gains(result):
    for group in ("map_deficit", "spo2_delivery", "ph_paco2"):
        assert result["orthogonality"][group]["distinguishable"] and result["orthogonality"][group]["isolated_as_declared"]
    for gain, rows in result["physiology"].items():
        assert all(row["wired"] and row["isolated_as_declared"] for row in rows.values()), gain
        assert rows["reference"]["positive"] == []
        assert rows["A_low_map_no_deficit"]["positive"] == ["cerebral_hypoperfusion"]
        assert rows["B_normal_map_high_deficit"]["positive"] == ["oxygen_deficit"]
        assert rows["G_low_ph_normal_paco2"]["positive"] == ["acidemia"]
        assert rows["H_high_paco2_near_normal_ph"]["positive"] == ["hypercapnia"]
        assert rows["acute_hypercapnia"]["positive"] == ["acidemia", "hypercapnia"]
        assert all(set(row["committed_profile"].values()) == {"UNMAPPED"} for row in rows.values())
        # No arrival floor: an authored obtunded label reads exactly as the reference; N leaks into no systemic signal.
        assert rows["arrival_label_obtunded"]["reading"] == rows["reference"]["reading"]
        assert rows["arrival_label_obtunded"]["positive"] == [] == rows["primary_n_only"]["positive"]
        assert rows["primary_n_only"]["primary_n"] == 0.5 and rows["reference"]["primary_n"] == 0.0


def test_the_tone_loop_inversion_is_removed_and_the_subset_is_carried(result):
    tone = result["tone_loop"]
    assert tone["candidate_inversion_removed"] and tone["legacy_inverted"] == [
        "anaemia g0.5", "anaemia g1", "demand_x2 g0.5", "demand_x2 g1"]
    x = result["extreme_acidemia"]
    # The subset's 'filtered' is P2L-1's recorded value (the frozen module restates it as a literal; review M2).
    assert ca._record(ea.P2L1_RECORD, ea.P2L1_RECORD_SHA)["extreme_acidemia"]["filtered"] is False
    assert x["flagged"] == 17604 and x["by_case"] == {"gi_bleed_57m": 17604, "gi_bleed_72f": 0}
    assert x["filtered"] is False and x["classification"] == "CONSCIOUSNESS_COLLAPSE_REVIEW"
    assert x["signals"]["hypercapnia"].startswith("ZERO_UNDER_EVERY") and x["ph_range"][1] == 7.0
    assert all(x["signals"][k].startswith("POSITIVE_UNDER_SOME") for k in
               ("acidemia", "cerebral_hypoperfusion", "oxygen_deficit"))


def test_the_generalization_and_identifiability(result):
    g = result["generalization"]
    assert g["result"] == "COMMON_NEUROLOGIC_ARCHITECTURE_PLAUSIBLE" and all(r["represented"] for r in g["rows"].values())
    assert g["rows"]["D_primary_stroke"]["lag"] is False and g["rows"]["A_hemorrhagic_shock"]["lag"] is True
    assert not any("WELL_CONSTRAINED" in v and not v.startswith("none") for v in ea.IDENTIFIABILITY.values())
    assert ea.IDENTIFIABILITY["well_constrained"].startswith("none")
    assert ea.TRAJECTORIES.startswith("NOT_GENERATED") and result["efficiency"]["gi_trajectories"] == 0


def test_the_verdict_and_next_rules():
    checks = {c: True for c in ea.CRITERIA}
    assert ea.verdict(checks)["verdict"] == ea.READY
    failing = dict(checks, maximum_aggregation=False, lactate_not_controller=False)
    v = ea.verdict(failing)
    assert v["verdict"] == f"{ea.NOT_READY} - MAXIMUM_AGGREGATION" and v["failing"] == [
        "maximum_aggregation", "lactate_not_controller"]
    partial = {c: True for c in ea.CRITERIA[:-1]}
    assert ea.verdict(partial)["not_evaluated"] == [ea.CRITERIA[-1]]
    ready = ea.verdict(checks)
    assert ea.recommendation(ready, {"flagged": 1, "filtered": False})["recommendation"] == \
        "COLLAPSE_SAFETY_ARCHITECTURE"
    assert ea.recommendation(ready, {"flagged": 0, "filtered": False})["recommendation"] == \
        "SECOND_FAMILY_GENERALIZATION"
    assert ea.recommendation(v, None)["recommendation"] == "STOP_FOR_STRUCTURAL_CORRECTION"


def test_a_changed_upstream_file_stops_before_any_probe(monkeypatch):
    monkeypatch.setattr(ea, "upstream_unchanged", lambda: {"unchanged": False, "imported_by": []})
    monkeypatch.setattr(ea, "candidate_scan", lambda: pytest.fail("no probe after a STOP"))
    out = ea.run()
    assert out["stopped"].startswith("an upstream file changed") and \
        out["verdict"]["checks"]["upstream_unchanged"] is False


def test_the_run_states_its_verdict_and_scope(result):
    assert "stopped" not in result and result["verdict"]["verdict"] == ea.READY
    assert result["recommendation"]["strategy"] == "DO_NOT_OVERFIT_GI"
    assert result["recommendation"]["numeric_calibration_required_before_generalization"] is False
    e = result["efficiency"]
    assert e["trajectory_simulations"] == 0 and e["integrator_steps"] == 0 and e["cartesian_sweep"] is False
    assert e["fixed_state_readings"] == len(ea.PHYSIOLOGY_PROBES) * len(ea.GAINS)
    assert "nothing selected or approved" in ea.POLICY and ea.MIGRATION_GATE.startswith("MIGRATION_GATE_CLOSED")
    assert vs.PROBE_PROFILE.oxygen_extraction_reserve == 2.5


# The record and the report (generated once, after the frozen evaluation) -----------------------------------------------------

RECORD = ROOT / "docs" / "revision" / "P2L2_encephalopathy_architecture.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2L2_ARQUITECTURA_ENCEFALOPATIA.md"


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, result):
    assert record["freeze_digest"] == FROZEN_DIGEST and "stopped" not in record
    assert record["design"] == _json(ea.design())
    for key in ("upstream", "scan", "n", "legacy", "neuro_probes", "ratio_robustness", "memory_proof", "physiology",
                "orthogonality", "tone_loop", "extreme_acidemia", "generalization", "pharmacologic", "identifiability",
                "trajectories", "verdict", "recommendation", "efficiency"):
        assert record[key] == _json(result[key]), key


def test_the_record_states_the_architecture_verdict(record):
    v = record["verdict"]
    assert v["verdict"] == ea.READY and v["failing"] == [] and not v["not_evaluated"]
    assert set(v["checks"]) == set(ea.CRITERIA) and all(v["checks"].values())
    r = record["recommendation"]
    assert r["recommendation"] == "COLLAPSE_SAFETY_ARCHITECTURE" and r["strategy"] == "DO_NOT_OVERFIT_GI"
    e = record["efficiency"]
    assert e["trajectory_simulations"] == 0 == e["gi_trajectories"] and e["fixed_state_readings"] == 28
    assert record["extreme_acidemia"]["flagged"] == 17604 and record["extreme_acidemia"]["filtered"] is False
    assert record["approval"] == "none FACULTY_APPROVED"


def test_the_document_is_generated_from_the_record(record):
    from clinical_core import encephalopathy_architecture_report as rep
    document = DOCUMENT.read_text(encoding="utf-8")
    for name, render in rep.RENDERERS.items():
        assert rep.apply(document, name, render(record)) == document, name
    assert "COMMON_CONSCIOUSNESS_ARCHITECTURE_READY" in document and "COLLAPSE_SAFETY_ARCHITECTURE" in document
    assert "SUMMARY" not in document and "LIMITATIONS" not in document


def test_under_tone_compensation_the_observable_never_falls_below_the_deficit_signal():
    """P2L-2 review M1: the deficit's own path is monotone, but tone compensation raises MAP, so with an admissible
    mapping S can fall while the deficit rises; it never falls below the deficit's own signal. Test-only synthetic
    mapping (zero at the reference MAP 90 and deficit 0), never a profile value."""
    from dataclasses import replace
    from clinical_core import acid_base as ab
    from clinical_core.bands import Demand, Drift
    from clinical_core.integration import step
    anchors, base, profile0 = ca.neutral()
    mapping = enc.EncephalopathyProfile(mappings=(("cerebral_hypoperfusion", enc.SignalMapping(70.0, 40.0)),
                                                  ("oxygen_deficit", enc.SignalMapping(0.0, 1.0))))
    insults = {"anaemia": (Drift("hb", "hb", 0, 1, -anchors.hb / 2.0),), "demand_x2": (Demand("demand", 0, 10, 2.0),)}
    fell = []
    for name, contributors in insults.items():
        for gain in (0.0,) + tuple(ab.TONE_GAINS):
            profile = replace(profile0, deficit_to_tone_gain=gain)
            state, rows = base.evolve(P=ca.TONE_START_PUMP), []
            for _ in range(3):
                state, _ = step(state, contributors, anchors, profile)
                signals = enc.acute_signals(enc.readings(state, anchors, profile), mapping)
                rows.append((signals.value("oxygen_deficit"), enc.systemic_acute_brain_stress(dict(signals.values))))
            assert all(b[0] >= a[0] for a, b in zip(rows, rows[1:])), (name, gain)
            assert all(stress >= deficit for deficit, stress in rows), (name, gain)
            fell.append(rows[-1][1] < rows[0][1])
    assert any(fell) and not all(fell)
