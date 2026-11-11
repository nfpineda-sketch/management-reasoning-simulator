"""P3-4: the generic shadow runner, one adapter per certified family, and deterministic replay.

H1-H25 of the P3-4 authorization. The invariant is still P3-1's: the legacy engine is the only runtime
authority. What this suite adds is that the shadow layer is *generic* (six families, ten certified cases),
*deterministic* (the same immutable input always replays to the same digests) and *honest* (a treatment the
core cannot represent is a declared gap, never silence).
"""
import ast
import json
from copy import deepcopy
from pathlib import Path

import pytest

import runtime_shadow as rs
import runtime_shadow_families as fam
from test_runtime_shadow_plumbing import CASE, ON, TURNS, _authoritative, _play

ROOT = Path(__file__).resolve().parent
#: Every certified family and case the adapters claim, as the matrix must find them.
CERTIFIED = {
    "gi_bleed": ("gi_bleed_57m", "gi_bleed_72f"),
    "acs": ("acs_70f_left_main",),
    "pulmonary_edema": ("pulmonary_edema_58m",),
    "pulmonary_embolism": ("pulmonary_embolism_61m", "pulmonary_embolism_33f"),
    "asthma": ("asthma_49m", "asthma_24f"),
    "opioid": ("opioid_35m", "opioid_67f"),
}


def _runner(family, case, point=fam.COMMITTED, minutes=30):
    runner = fam.ShadowPhysiologyRunner.open(family, case, point=point)
    assert runner is not None, (family, case)
    assert runner.advance(minutes), [vars(item) for item in runner.failures]
    return runner


# -- H1: Phase 2 stays frozen --------------------------------------------------------------------------------

def test_h1_the_phase2_closure_digest_is_unchanged():
    import hashlib
    paths = sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "clinical_core").rglob("*.py")
                   if "__pycache__" not in path.parts and path.is_file() and not path.name.startswith("."))
    sources = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}
    # PHASE2_AMENDMENT_1: the live tree is the closure's successor. What must be unchanged is the closure itself:
    # it is rebuilt from these same live sources by reversing the successor's declared insertions.
    from clinical_core import amendment_1 as a1
    from clinical_core import amendment_2 as a2
    assert hashlib.sha256(json.dumps(a2.closure_sources_of(sources), sort_keys=True).encode()).hexdigest() == rs.PHASE2_DIGEST
    assert hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest() == rs.CORE_LINEAGE[-1].digest


def test_the_phase3_layer_lives_outside_the_frozen_package():
    for name in ("runtime_shadow.py", "runtime_shadow_families.py"):
        assert (ROOT / name).is_file()
        assert not (ROOT / "clinical_core" / name).exists()


# -- H2, H10-H13, H15: nothing authoritative moves -----------------------------------------------------------

@pytest.fixture(scope="module")
def paired():
    return {"off": _play(CASE, TURNS, {}), "on": _play(CASE, TURNS, dict(ON))}


def test_h2_h10_h11_h12_h13_h15_the_encounter_is_identical(paired):
    off, on = _authoritative(paired["off"]), _authoritative(paired["on"])
    assert off == on, "the shadow changed something authoritative"
    assert off["sim_time"] == on["sim_time"], "the wait advanced differently"
    assert off["ledger"] == on["ledger"], "an order fate moved"


# -- H3, H4, H5-H9, H25: determinism and replay --------------------------------------------------------------

def test_h3_the_gi_live_shadow_is_deterministic(paired):
    again = _play(CASE, TURNS, dict(ON))
    assert again.shadow.digests() == paired["on"].shadow.digests()


def test_h4_gi_live_equals_its_offline_replay(paired):
    session = paired["on"].shadow
    replayed = [item["state_digest"] for item in session.replay()["minutes"]]
    live = list(session.digests())
    assert replayed == live, "the live shadow and its replay diverged"


@pytest.mark.parametrize("family,case", [(family, case) for family, cases in CERTIFIED.items()
                                         for case in cases])
def test_h5_to_h9_every_certified_family_replays_deterministically(family, case):
    first, second = _runner(family, case), _runner(family, case)
    assert first.digests() == second.digests()
    captured = first.replay_input()
    assert captured is not None and captured.digest() == second.replay_input().digest()
    replayed = fam.replay_shadow_encounter(captured)
    assert [item["state_digest"] for item in replayed["results"]][1:] == list(first.digests())
    assert replayed["final_digest"] == first.digests()[-1]


def test_h25_the_replay_reproduces_the_final_digest_from_json_alone():
    runner = _runner("acs", "acs_70f_left_main", minutes=60)
    payload = json.loads(json.dumps(runner.replay_input().to_dict(), default=str))
    assert fam.replay_shadow_encounter(payload)["final_digest"] == runner.digests()[-1]


# -- H14, H17: events ----------------------------------------------------------------------------------------

def test_h14_a_duplicate_mirrored_event_is_idempotent():
    runner = fam.ShadowPhysiologyRunner.open("gi_bleed", "gi_bleed_57m")
    event = rs.MirroredAction("m000-0-fluid", 0, "fluid", {"volume_ml": 1000.0}, {}, 0.21)
    runner.mirror([event])
    runner.advance(10)
    once = (len(runner.mirrored), runner.digests())
    runner.mirror([event, event])
    runner.advance(10)
    assert (len(runner.mirrored), runner.digests()) == once


def test_h17_a_malformed_event_is_refused_and_recorded():
    runner = fam.ShadowPhysiologyRunner.open("gi_bleed", "gi_bleed_57m")
    runner.mirror([rs.MirroredAction("m000-0-nonsense", 0, "nonsense", {}, {}, 0.21)])
    assert runner.advance(5)
    assert any(gap["kind"] == "nonsense" for gap in runner.gaps)
    runner.mirror([rs.MirroredAction("m001-0-fluid", 1, "fluid", {}, {}, 0.21)])
    assert runner.advance(6) is False, "a fluid with no volume must not pass silently"
    assert [item.classification for item in runner.failures] == [rs.MAPPING_GAP]


def test_the_clock_cannot_go_backwards():
    runner = _runner("gi_bleed", "gi_bleed_57m", minutes=20)
    assert not runner.advance(10)
    assert [item.exception for item in runner.failures] == ["TimeOrder"]


# -- H16: failure isolation ----------------------------------------------------------------------------------

@pytest.mark.parametrize("error,classification", [
    ("CoreInvariantError", rs.UNEXPECTED), ("UnresolvedBoundary", rs.BOUNDARY), ("ValueError", rs.MAPPING_GAP)])
def test_h16_every_common_core_failure_is_captured_and_classified(monkeypatch, error, classification):
    from clinical_core import integration, state as core_state
    kind = {"CoreInvariantError": core_state.CoreInvariantError,
            "UnresolvedBoundary": core_state.UnresolvedBoundary, "ValueError": ValueError}[error]
    runner = fam.ShadowPhysiologyRunner.open("gi_bleed", "gi_bleed_57m")
    monkeypatch.setattr(integration, "run", lambda *a, **k: (_ for _ in ()).throw(kind("no")))
    assert runner.advance(5) is False
    assert [item.classification for item in runner.failures] == [classification]
    assert runner.results == [], "a failed minute must leave no result behind"


def test_an_unmappable_case_opens_no_runner():
    assert fam.ShadowPhysiologyRunner.open("gi_bleed", "gi_bleed_nonexistent") is None
    assert fam.ShadowPhysiologyRunner.open("pneumonia", "pneumonia_71m") is None
    assert fam.adapter_for("pneumonia") is None


# -- H18, H24: the snapshot and its provenance ---------------------------------------------------------------

def test_h18_a_parameter_snapshot_is_immutable_and_never_approved():
    snapshot = fam.ADAPTERS["acs"].snapshot("upper")
    with pytest.raises(Exception):
        snapshot.id = "other"
    with pytest.raises(ValueError):
        fam.ShadowParameterSnapshot("x", "acs", "upper", (), approved=True)
    with pytest.raises(ValueError):
        fam.ShadowParameterSnapshot("x", "acs", "whatever", ())
    assert snapshot.to_dict()["approved"] is False


def test_every_witness_cites_a_committed_phase2_span():
    for family, adapter in fam.ADAPTERS.items():
        for point in fam.POINTS:
            snapshot = adapter.snapshot(point)
            assert snapshot.provenance, (family, point)
            assert all("clinical_core." in str(line) for line in snapshot.provenance), snapshot.provenance


def test_the_witnesses_of_a_region_are_different_trajectories():
    """A region is only honest if its witnesses actually differ.

    Until P3-11 GI read no band and its three points coincided. It now reads the declared region of the
    frozen calibration registry (29 profile magnitudes), so every certified family has three trajectories.
    """
    for family, cases in CERTIFIED.items():
        case = cases[0]
        digests = {point: _runner(family, case, point=point, minutes=60).digests()[-1] for point in fam.POINTS}
        assert len(set(digests.values())) == 3, (family, digests)
    committed = _runner("gi_bleed", CERTIFIED["gi_bleed"][0], point=fam.COMMITTED, minutes=60).digests()[-1]
    midpoint = _runner("gi_bleed", CERTIFIED["gi_bleed"][0], point="midpoint", minutes=60).digests()[-1]
    assert committed == midpoint, "GI's structural witness IS the committed profile, named once"


def test_h24_the_version_metadata_is_complete():
    runner = _runner("opioid", "opioid_35m")
    versions = runner.replay_input().versions
    for key in ("phase2_closure_head", "phase2_digest", "phase3_module", "adapter", "parameter_snapshot",
                "closure_guard_digest", "families_module"):
        assert versions.get(key), key
    assert versions["phase2_digest"] == rs.PHASE2_DIGEST
    record = runner.record()
    assert record["runtime_authority"] == "legacy" and record["common_core_runtime_authority"] is False
    # P3-141: el adaptador del opioide cambio (identidad de llegada, minuto efectivo, testigos) y su
    # version lo dice; el punto sigue siendo el comprometido.
    assert record["adapter"] == "opioid/P3-141L" and record["point"] == fam.COMMITTED


# -- H19, H20, H23: no randomness, no reader, pilot off ------------------------------------------------------

def test_h19_the_layer_introduces_no_randomness():
    tree = ast.parse((ROOT / "runtime_shadow_families.py").read_text(encoding="utf-8"))
    names = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    names |= {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert not {"random", "secrets", "time", "datetime", "clinical_physiology"} & names, sorted(names)


def test_h20_h23_no_authoritative_surface_reads_the_shadow_and_the_pilot_keeps_it_off():
    readers = [path.name for path in sorted(ROOT.glob("*.py"))
               if not path.name.startswith("test_") and path.name not in rs.LAYER_SOURCES
               and ("runtime_shadow" in path.read_text(encoding="utf-8")
                    or "phase3_shadow" in path.read_text(encoding="utf-8"))]
    assert readers == ["app.py", "pilot_acceptance.py"], readers
    for name in ("tools_pilot_preflight.py", "tools_pilot_smoke.py", "docs/RUNBOOK_PILOTO.md"):
        path = ROOT / name
        if path.is_file():
            assert rs.FLAG not in path.read_text(encoding="utf-8"), name
    import pilot_acceptance
    assert pilot_acceptance.Encounter(CASE).shadow is None


# -- H21, H22: the two candidates stay out of the encounter --------------------------------------------------

def test_h21_h22_the_collapse_and_consciousness_candidates_cannot_reach_the_encounter():
    """P3-8 reads both candidates as diagnostics. Neither can arrest a patient nor set a mental status.

    The live path never calls them -- the two wiring points do not name them -- and the diagnostic itself
    emits no category and no terminal transition, which test_runtime_shadow_ensemble.py checks value by
    value. Here the structural half: no live caller, and no arrest anywhere in a shadow result.
    """
    import ast
    for name in ("app.py", "pilot_acceptance.py", "runtime_shadow.py"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "shadow_diagnostics" not in text, name
        modules = {node.module for node in ast.walk(ast.parse(text))
                   if isinstance(node, ast.ImportFrom) and node.module}
        modules |= {alias.name for node in ast.walk(ast.parse(text)) if isinstance(node, ast.Import)
                    for alias in node.names}
        assert not {"clinical_core.encephalopathy", "clinical_core.collapse"} & modules, name
    runner = _runner("gi_bleed", "gi_bleed_57m")
    # The real property: the shadow's own pulse never contradicts a live patient, and the diagnostic
    # publishes no collapse signal at all while the Phase-2 mapping is UNSET.
    assert all(item.derived["pulse_present"] is True for item in runner.results)
    out = fam.shadow_diagnostics(runner, 30)
    assert out["collapse"]["perfusion_failure_signal"] is None
    assert out["authority"] == "none" and out["consciousness"]["mental_status_category"] is None
    assert out["collapse"]["terminal_transition"] is None


# -- the matrix ----------------------------------------------------------------------------------------------

def test_the_family_matrix_covers_every_certified_family_and_case():
    matrix = fam.family_matrix()
    assert sorted(matrix) == sorted(CERTIFIED)
    for family, cases in CERTIFIED.items():
        assert sorted(matrix[family]) == sorted(cases)
        for case, row in matrix[family].items():
            assert row["offline_replay"] is True, (family, case, row)
            assert row["failures"] == [], (family, case, row)
            # P3-141: el opioide es la segunda familia en sombra en vivo; ninguna otra entro.
            assert row["live_shadow"] is (family in ("gi_bleed", "opioid"))


def test_a_family_declares_the_treatments_it_cannot_represent():
    assert fam.ADAPTERS["asthma"].gaps_declared, "the bronchodilator gap must be declared, not silent"
    # P3-105 re-claveo los huecos a las clases de accion REALES del motor: "medicine" no era una de ellas
    # (la clase ES el farmaco), asi que ese hueco no podia dispararse nunca y su razon declarada no llegaba
    # al registro. Lo que esta prueba protege -- que PE declare lo que no puede representar -- sigue
    # protegido, y ahora la declaracion si alcanza al registro.
    pe_gaps = fam.ADAPTERS["pulmonary_embolism"].gaps_declared
    assert {"anticoagulation", "thrombolysis"} <= set(pe_gaps)
    assert "medicine" not in pe_gaps
    assert fam.ADAPTERS["gi_bleed"].maps == ("fluid", "blood", "oxygen", "ppi")
    # P3-141: el opioide paso sus compuertas (lazo indirecto y llegada en vivo) y es la segunda familia en
    # vivo. Lo que la prueba protege -- que ninguna familia este en vivo sin haberlo ganado -- sigue
    # protegido para las otras cuatro, y la lista del runtime y la de los adaptadores tienen que coincidir.
    for family, adapter in fam.ADAPTERS.items():
        if family not in ("gi_bleed", "opioid"):
            assert adapter.live is False, f"{family} is not live-shadow ready"
    assert sorted(f for f, adapter in fam.ADAPTERS.items() if adapter.live) == sorted(rs.LIVE_FAMILIES)
