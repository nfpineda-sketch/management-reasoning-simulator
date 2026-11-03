"""P2O-3: lung-water reversibility (L_rev) and congestion-writer authority, shadow only.

The live core is the P2O-1 core plus exactly P2O-3's declared replacements (proven byte for byte, the live bytes pinned);
with L_rev = 0 and no owning writer it is P2O-1's exactly. These tests pin the authority (one generator of L), L_rev
(credit only in L -> G, no floor on L), the sign of G, R1-R8, the ACS mapping (V from the IVC, L from the congestion),
the partial recovery, the HR sign, the parameter status and the frozen record. Every probe value is SYNTHETIC_ONLY.
"""
import ast
import hashlib
import json
from dataclasses import dataclass, replace

import pytest

from clinical_core import acs_migration as an
from clinical_core import acs_reference as ar
from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import gas_exchange_architecture as go
from clinical_core import lung_water_reference as lw
from clinical_core.bands import ARRIVAL
from clinical_core.integration import Contributor, step
from clinical_core.modules.acs_ischaemia import IschaemicCongestion
from clinical_core.provenance import ProvenanceError, SourceKind
from clinical_core.state import ARRIVAL_LAYERS, CASE_PARAMETERS, Anchors, Channel, CoreInvariantError

#: The P2O-3 freeze: the decisions, the authority and L_rev semantics, the G-sign audit, the SYNTHETIC_ONLY probe values,
#: the ACS / recovery / HR designs, the debts, the verdict and recommendation rules, the reversal proof and every
#: clinical_core source but the downstream reports, committed before the evaluation run.
FROZEN_DIGEST = "ecb7ec088a3c8bc256bd00a9c89e0e84c417895f58e435153ee8813dc864323d"
#: The live bytes of every file P2O-3 changed, as frozen: with the reversal proof, the closed packages' views are exact.
CORE_AT_P2O3 = {'clinical_core/decision_pack.py': 'a176cb385e896bbc96c39e66f7e9b9c07bdcf25c491b82df71480f6162578d2d',
 'clinical_core/derived.py': '19caba4f5a508507e1c63c64f098f2a3d1255832ec96bbc16a9ad16cc03b3030',
 'clinical_core/integration.py': '3d4475f3d94fa2cc8832ed758cc9c85bd22913cc1911afc2fee0e306fbac5e82',
 'clinical_core/lactate_slice.py': '27fa0e3b3df18e796bd32ce311313c4569ca2a11df19b6df90c24462e85e35c1',
 'clinical_core/modules/acs_ischaemia.py': '6db1b0f09946d448c7b18462b0e80fd616e0602a593f76b0e45d145c1ef4a6a0',
 'clinical_core/state.py': '141cd5a2aada89a58e7de9ee1436b2f52fd68141df132bcb26e934e6e9ddc7d1'}


# The frozen package and its proof -------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert lw.OWN[0] in sources and lw.REPORT not in sources
    assert set(lw.TUPLES_ADDED["DOWNSTREAM_REPORTS"]) <= set(lactate_slice.DOWNSTREAM_REPORTS)
    assert set(lw.TUPLES_ADDED["PACK_DIGEST_EXCLUDED"]) <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    if FROZEN_DIGEST is not None:
        assert lw.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_the_live_files_are_the_p2o1_files_plus_exactly_the_declared_replacements():
    assert set(lw.REVERSAL) == set(lw.CORE_AT_P2O1) == set(CORE_AT_P2O3)
    assert all(lw.proofs().values())
    for relative, sha in CORE_AT_P2O3.items():
        assert hashlib.sha256((lw.ROOT / relative).read_bytes()).hexdigest() == sha
        assert hashlib.sha256(lw.p2o1_bytes(relative)).hexdigest() == lw.CORE_AT_P2O1[relative]
    proof = lw.upstream_unchanged()
    assert proof["p2o1_freeze_digest"] and proof["p2o1_record"]


@pytest.mark.parametrize("relative, old, new", [
    ("clinical_core/derived.py", "max(credit, gas_exchange)", "max(credit, gas_exchange) * 1.0"),
    ("clinical_core/derived.py", "def congestion_rate(", "def congestion_rate_(  "),
    ("clinical_core/integration.py", "congestion = 0.0 if owned else", "congestion = 0.0 if not owned else"),
    ("clinical_core/state.py", "    pump_reserve: float = 1.0\n", "    pump_reserve: float = 0.9\n"),
    ("clinical_core/modules/acs_ischaemia.py", "lung_water_authority = True", "lung_water_authority = False"),
])
def test_the_proof_notices_any_other_change(relative, old, new):
    live = lw._live(relative)
    assert live.count(old) == 1
    assert not lw.proved(relative, live.replace(old, new))


def test_the_view_gives_the_p2o1_text_to_paths_and_bytes():
    path = lw.P2O1Path(lw.ROOT / "clinical_core" / "state.py")
    assert hashlib.sha256(path.read_text().encode("utf-8")).hexdigest() == lw.CORE_AT_P2O1["clinical_core/state.py"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == lw.CORE_AT_P2O1["clinical_core/state.py"]
    assert "reversible_lung_water" not in lw.p2o1_text("clinical_core/state.py")
    assert lw.p2o1_unchanged(lw.CORE_AT_P2O1) == {k: True for k in lw.CORE_AT_P2O1}


# P2O-3-1 / 2: composition and authority -------------------------------------------------------------------------------------

def test_the_authority_is_a_class_declaration_only_a_disease_module_may_make():
    assert Contributor.lung_water_authority is False and IschaemicCongestion.lung_water_authority is True
    assert "lung_water_authority" not in IschaemicCongestion("x", 0.05).to_spec()        # no spec field, no golden change
    with pytest.raises(ProvenanceError):
        step(dv.arrival_state(lw.NEUTRAL, lw.profile()), (lw.ScriptedOwner("s", "L", 0, 1, 0.0),), lw.NEUTRAL,
             lw.profile())

    @dataclass(frozen=True)
    class Truthy(IschaemicCongestion):
        lung_water_authority = 1

    with pytest.raises(ProvenanceError):
        step(dv.arrival_state(lw.NEUTRAL, lw.profile()), (Truthy("t", 0.05),), lw.NEUTRAL, lw.profile())


def test_the_composition_adds_and_the_authority_leaves_one_generator(result):
    comp = result["probes"]["composition"]
    assert comp["rule"] == "ADDS" and comp["adds"] and comp["minutes_with_both"] > 0
    r7, r8 = result["probes"]["probes"]["R7"], result["probes"]["probes"]["R8"]
    assert r7["common_writes"] == 0 and r7["L_equals_family_alone"] and r7["V_moved"]
    assert r8["common_writes"] > 0 and r8["L_end"] > 0.0


def test_the_authority_holds_for_the_run_even_in_a_minute_the_family_writes_nothing():
    # P = 1 (the family writer adds nothing) with volume above the knee: without the writer the common coupling
    # congests; with it present nothing does (the authority is presence, not the minute).
    a = ar.anchors(preload_fraction=0.78)
    p = ar.common_profile()
    bag = replace(an._bag(), volume_ml=4000.0, untimed_rate_ml_per_min=4000.0 / an.FLUID["duration_min"])
    owner = IschaemicCongestion("acs-congestion", an.writers()[1].lung_water_per_shortfall_per_min)
    common, records = an.course((bag,), 120, a, p)
    owned, owned_records = an.course((bag, owner), 120, a, p)
    assert max(s.L for s in common) > 0.0 and any(d.source == dv.PRELOAD_CONGESTION for r in records for d in r.deltas)
    assert {s.L for s in owned} == {0.0} and not any(d.channel is Channel.L for r in owned_records for d in r.deltas)


def test_without_an_owner_the_core_coupling_is_unchanged_minute_by_minute():
    a = ar.anchors(preload_fraction=0.7)
    p = ar.common_profile()
    bag = replace(an._bag(), volume_ml=4000.0, untimed_rate_ml_per_min=4000.0 / an.FLUID["duration_min"])
    states, records = an.course((bag,), 120, a, p, dv.arrival_state(a, p).evolve(P=0.7))
    written = 0
    for before, record in zip(states, records):
        amounts = [d.amount for d in record.deltas if d.source == dv.PRELOAD_CONGESTION]
        rate = dv.congestion_rate(before, a, p)
        assert amounts == ([rate] if rate else [])
        written += bool(amounts)
    assert written > 0


# P2O-3-3: L_rev and the L -> G reader ---------------------------------------------------------------------------------------

def test_l_rev_is_a_candidate_reference_input_at_or_below_arrival():
    assert Anchors(**ARRIVAL).reversible_lung_water == 0.0
    assert "reversible_lung_water" not in CASE_PARAMETERS
    assert "reversible_lung_water" in ARRIVAL_LAYERS["physiological_reference"]
    assert lw.CANDIDATE_INPUTS == ("reversible_lung_water",)
    assert Anchors(**{**ARRIVAL, "reversible_lung_water": -2.0}).reversible_lung_water == -2.0
    for bad in (0.1, float("inf"), float("nan")):
        with pytest.raises(CoreInvariantError):
            Anchors(**{**ARRIVAL, "reversible_lung_water": bad})


@pytest.mark.parametrize("l_rev", [0.0, -0.5, -1.0])
def test_the_coupling_sums_to_k_times_max_l_rev_l(l_rev):
    p = lw.profile()
    k = p.lung_water_to_gas_exchange_gain
    path = [0.0, 0.3, -0.2, -0.8, -1.5, -0.6, 0.4, 1.2, 0.0, -2.0]
    total = 0.0
    for before, after in zip(path, path[1:]):
        total += dv.lung_water_gas_exchange(before, after, p, l_rev)
        assert abs(total - k * max(l_rev, after)) < 1e-12


def test_the_credit_is_the_lung_water_share_below_arrival_and_zero_by_default():
    p, off = lw.profile(), go.off_profile(lw.profile())
    k = p.lung_water_to_gas_exchange_gain
    for l in lw.L_GRID:
        assert dv.lung_water_gas_credit(l, lw.neutral(), p) == 0.0
        assert dv.lung_water_gas_credit(l, lw.neutral(-1.0), off) == 0.0
        assert dv.lung_water_gas_credit(l, lw.neutral(-1.0), p) == k * min(0.0, max(-1.0, l))


def test_only_the_coupling_and_the_credit_read_l_rev_and_perfusion_reads_l_only_for_the_credit():
    text = lw._live("clinical_core/derived.py")
    tree = ast.parse(text)
    readers = sorted(n.name for n in tree.body if isinstance(n, ast.FunctionDef)
                     and any(isinstance(x, ast.Attribute) and x.attr == "reversible_lung_water" for x in ast.walk(n)))
    assert readers == ["lung_water_gas_credit"]
    naming_l = sorted(n.name for n in tree.body if isinstance(n, ast.FunctionDef)
                      and any(isinstance(x, ast.Attribute) and x.attr == "L" and isinstance(x.value, ast.Name)
                              for x in ast.walk(n)))
    assert naming_l == ["_perfusion", "lung_water_clearance"]
    perfusion = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_perfusion")
    uses = [x for x in ast.walk(perfusion) if isinstance(x, ast.Attribute) and x.attr == "L"]
    assert len(uses) == 1 and "lung_water_gas_credit(state.L, anchors, profile)" in ast.get_source_segment(
        text, perfusion)
    assert "anchors.reversible_lung_water" in lw._live("clinical_core/integration.py")


# The sign of G -------------------------------------------------------------------------------------------------------------

def test_the_core_boundaries_hold(result):
    b = result["boundaries"]
    assert b["pass"] and b["derived_readers_of_l_rev"] == ["lung_water_gas_credit"] and not b["disease_terms_in_core"]


def test_negative_g_is_supported_bounded(result):
    g = result["probes"]["g_sign"]
    assert g["verdict"] == "NEGATIVE_G_SUPPORTED_BOUNDED" and g["pass"]
    assert result["probes"]["direct_g"]["pass"]
    with pytest.raises(CoreInvariantError):
        dv.oxygenation(0.0, 0.21, lw.NEUTRAL, lw.profile(), 0.01)


# R1-R8 ---------------------------------------------------------------------------------------------------------------------

def test_every_r_probe_passes(result):
    assert result["probes"]["pass"] == {f"R{i}": True for i in range(1, 9)}
    r1 = result["probes"]["probes"]["R1"]
    assert all(r1["p2o1_sections_reproduced"].values()) and all(r1["arrival_any_l_rev"].values())


def test_r4_r5_numbers_follow_the_structure(result):
    p = lw.profile()
    k, s = p.lung_water_to_gas_exchange_gain, p.spo2_per_gas_exchange_unit
    r4, r5 = result["probes"]["probes"]["R4"], result["probes"]["probes"]["R5"]
    assert abs(r4["spo2"] - (lw.NEUTRAL.spo2 - s * k * r4["L"])) < 1e-9
    assert r5["L"] < r5["l_rev"] and abs(r5["G"] - k * r5["l_rev"]) < 1e-12 and r5["spo2"] == r5["cap_spo2"]


# ACS, recovery, HR, parameters, GI ------------------------------------------------------------------------------------------

def test_the_acs_mapping_keeps_v_and_l_apart(result):
    m = result["acs_mapping"]
    assert m["pass"] and m["preload_fraction"] is None and m["ivc_informs_v"] and m["b_lines_not_in_v"]
    assert m["l_rev_at_acs"] == 0.0 and m["pump_reserve_inert_under_authority"]


def test_acs_represents_arrival_congestion_and_decongestion_without_moving_v(result):
    r = result["acs_representation"]
    assert r["pass"] and r["v_unchanged"] and r["p_unchanged"]
    assert r["arrival"]["L"] == 0.0 < r["congestion"]["L"] and r["decongestion"]["L"] < r["decongestion"]["l_rev"] < 0.0


def test_a_recovery_of_p_never_clears_l_at_once(result):
    rec = result["partial_recovery"]
    assert rec["pass"]
    for key in ("0.5", "1.0"):
        assert rec[key]["persists"] and rec[key]["max_fall_per_min"] <= rec[key]["clearance_share"] * rec[key]["L_peak"]


def test_hr_keeps_its_sign(result):
    assert result["heart_rate"]["pass"]


def test_no_value_is_approved_and_gi_is_unchanged(result):
    assert result["parameters"]["pass"] and result["gi"]["pass"] and result["arrival_relative"]["pass"]
    assert all(getattr(dv.DEFAULT_PROFILE, k) is None for k in go.REFERENCE)


# The frozen evaluation ----------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def result():
    return json.loads(json.dumps(lw.run(), sort_keys=True))


@pytest.fixture(scope="module")
def record():
    if not lw.RECORD.exists():
        pytest.skip("the P2O-3 record is written by the evaluation run, after the freeze")
    return json.loads(lw.RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, result):
    assert record["freeze_digest"] == FROZEN_DIGEST
    assert record == result


def test_the_verdict_follows_the_predeclared_rule(record):
    assert record["verdict"]["verdict"] == "L_REFERENCE_AND_WRITER_AUTHORITY_READY"
    assert all(record["verdict"]["criteria"].values())
    assert record["recommendation"] == "MIGRATE_PULMONARY_EDEMA_SHADOW"
