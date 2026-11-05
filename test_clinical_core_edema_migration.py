"""P2P-1: pulmonary_edema_58m migrated in shadow with a family L writer, on the unchanged common core.

No common file changes (pinned at its P2O-3 bytes); the tuple files differ from P2O-3's only by P2P-1's entries (proven).
These tests pin the case and its mapping (V from the IVC, L from the congestion), the family writer (L only, the owner,
decongestion never below L_rev), the common L -> G -> SpO2 path, oxygen, the authority, decongestion with L_rev = 0, the
HR sign, the consciousness guard, the expected respiratory extension, GI / ACS non-regression and the frozen record.
"""
import ast
import copy
import hashlib
import json
from dataclasses import replace

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import edema_migration as pe
from clinical_core import edema_reference as er
from clinical_core import respiratory_drive as rd
from clinical_core import embolism_migration as em
from clinical_core import respiratory_mechanics as mc
from clinical_core import asthma_migration as sm
from clinical_core import respiratory_distress as dm
from clinical_core import distress_closure as xm
from clinical_core import asthma_distress_migration as tm
from clinical_core import oxygenation_link as om
from clinical_core.bands import Drift
from clinical_core.integration import from_spec, step
from clinical_core.modules.pulmonary_edema import DecongestiveTreatment, EdemaCongestion
from clinical_core.state import CoreInvariantError, RhythmState

#: The P2P-1 freeze: the case and its mapping, the writer, the predeclared spans, probes and verdict rule, the proof and
#: every clinical_core source but the downstream reports, committed before the evaluation run.
FROZEN_DIGEST = "2c7dc8b184529edea5a77c6beb8bf9b270391d4ae49f5a0d4221aa1a7a3a5c2e"

#: P2P-2 changed the core (the respiratory-drive composition, inert by default) and the two tuple files, proven against
#: the P2P-1 files (respiratory_drive.proved): this package's guards read the tree as P2P-1 left it (rd.chain,
#: rd.p2p1_sources); the record is unchanged.
#: P2Q-2 added files (the PE family, its mapping and analysis) and two tuple entries, proven against the P2P-2
#: files (embolism_migration.proved): this package's guards read the tree as P2P-2 left it (em.chain,
#: em.p2p2_sources).
#: P2S-2 changed the core (the common respiratory mechanics candidate, off by default) and two tuple files,
#: proven against the P2Q-2 files (respiratory_mechanics.proved): this package's guards read the tree as
#: P2Q-2 left it (mc.chain, mc.p2q2_sources).
#: P2S-3 added files (the asthma family, its mapping and analysis) and two tuple entries, proven against the
#: P2S-2 files (asthma_migration.proved): this package's guards read the tree as P2S-2 left it (sm.chain,
#: sm.p2s2_sources).
#: P2T-1 changed four common files (the respiratory distress input and its two UNSET readers), proven against
#: the P2S-3 files (respiratory_distress.proved): this package's guards read the tree as P2S-3 left it
#: (dm.chain, dm.p2s3_sources).
#: P2T-1A changed two common files (the M1 guard and the L1 sum) and two tuple files, proven against the
#: P2T-1 files (distress_closure.proved): this package's guards read the tree as P2T-1 left it
#: (xm.chain, xm.p2t1_sources).
#: P2T-3 added files (the asthma distress migration) and two tuple entries, proven against the P2T-1A files
#: (asthma_distress_migration.proved): this package's guards read the tree as P2T-1A left it (tm.chain,
#: tm.p2t1a_sources).
#: P2T-5 changed the core (the hypoventilation -> oxygenation link, off by default: one UNSET profile field) and
#: two tuple files, proven against the P2T-3 files (oxygenation_link.proved): this package's guards read the
#: tree as P2T-3 left it (om.chain, om.p2t3_sources).
_LIVE_SOURCES_P2T5 = bf.freeze_sources


def _LIVE_SOURCES_P2T3() -> dict:
    return om.p2t3_sources(_LIVE_SOURCES_P2T5())


def _LIVE_SOURCES_P2T1A() -> dict:
    return tm.p2t1a_sources(_LIVE_SOURCES_P2T3())


def _LIVE_SOURCES_P2T1() -> dict:
    return xm.p2t1_sources(_LIVE_SOURCES_P2T1A())


def _LIVE_SOURCES_P2S3() -> dict:
    return dm.p2s3_sources(_LIVE_SOURCES_P2T1())


def _LIVE_SOURCES_P2S2() -> dict:
    return sm.p2s2_sources(_LIVE_SOURCES_P2S3())


def _LIVE_SOURCES_P2Q2() -> dict:
    return mc.p2q2_sources(_LIVE_SOURCES_P2S2())


def _LIVE_SOURCES_P2P2() -> dict:
    return em.p2p2_sources(_LIVE_SOURCES_P2Q2())


@pytest.fixture(autouse=True, scope="module")
def _p2p1_tree():
    with pytest.MonkeyPatch.context() as patch:
        rd.chain(patch)
        em.chain(patch)
        mc.chain(patch)
        sm.chain(patch)
        dm.chain(patch)
        xm.chain(patch, historical=False)
        tm.chain(patch)
        om.chain(patch)
        patch.setattr(bf, "freeze_sources", lambda: rd.p2p1_sources(_LIVE_SOURCES_P2P2()))
        yield


# The frozen package and its proof -------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert all(relative in sources for relative in pe.OWN) and pe.REPORT not in sources
    assert set(pe.TUPLES_ADDED["DOWNSTREAM_REPORTS"]) <= set(lactate_slice.DOWNSTREAM_REPORTS)
    assert set(pe.TUPLES_ADDED["PACK_DIGEST_EXCLUDED"]) <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    if FROZEN_DIGEST is not None:
        assert pe.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_no_common_file_changed_and_the_tuples_differ_only_by_p2p1_entries():
    assert all(pe.common_untouched().values()) and len(pe.COMMON_AT_P2O3) >= 20
    assert all(pe.proofs().values()) and set(pe.REVERSAL) == set(pe.CORE_AT_P2O3)
    for relative, sha in pe.CORE_AT_P2O3.items():
        assert hashlib.sha256(pe.p2o3_bytes(relative)).hexdigest() == sha
    proof = pe.upstream_unchanged()
    assert proof["p2o3_freeze_digest"] and proof["p2o3_record"]


@pytest.mark.parametrize("relative, old, new", [
    ("clinical_core/lactate_slice.py", '"clinical_core/edema_migration_report.py")',
     '"clinical_core/edema_migration_report.py", "clinical_core/other.py")'),
    ("clinical_core/decision_pack.py", '"clinical_core/edema_migration.py"', '"clinical_core/edema_migration2.py"'),
])
def test_the_proof_notices_any_other_change(relative, old, new):
    live = pe._live(relative)
    assert live.count(old) == 1 and not pe.proved(relative, live.replace(old, new))


# The case and its mapping ----------------------------------------------------------------------------------------------------

def test_the_case_is_read_from_the_bank_by_a_predeclared_rule():
    c = pe.case()
    assert c["case"] == "pulmonary_edema_58m" and c["available"]
    assert "acute cardiogenic pulmonary edema" in c["truth"]["diagnosis"].lower()
    assert "acute cardiogenic pulmonary edema" not in c["other_variant_diagnosis"].lower()
    t = er.truth()
    assert (t["sbp"], t["dbp"], t["hr"], t["spo2"], t["respiratory_rate"]) == (218, 116, 126, 81, 38)
    assert (t["abg_ph"], t["abg_paco2"], t["abg_pao2"], t["abg_fio2_percent"]) == (7.29, 49, 46, 21)
    assert "B-lines" in t["pocus_lungs"] and t["pocus_ivc"].startswith("2.4 cm")
    assert set(t["definitive_actions"]) == {"niv", "nitroglycerin", "diuretic"}


def test_v_and_l_are_mapped_apart_and_b_lines_never_reach_v_or_the_pump():
    a = er.anchors()
    assert a.preload_fraction is None and "preload_fraction" not in a.declared
    assert a.pump_reserve == 1.0 and "pump_reserve" not in a.declared and a.reversible_lung_water == 0.0
    assert "IVC" in er.ARRIVAL_CLASSES["preload_fraction"] and "B-lines are not read" in er.ARRIVAL_CLASSES["preload_fraction"]
    assert "never pump evidence" in er.ARRIVAL_CLASSES["pump_reserve"]
    assert er.OBSERVATION_LAYER["b_lines_crackles_radiograph"].startswith("an observation of L")
    tree = ast.parse((pe.CORE_DIR / "edema_reference.py").read_text(encoding="utf-8"))
    anchors_fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "anchors")
    names = {c.value for c in ast.walk(anchors_fn) if isinstance(c, ast.Constant) and isinstance(c.value, str)}
    assert not any("lung" in x or "b_line" in x or "crackle" in x for x in names)


# The family writer -------------------------------------------------------------------------------------------------------

def test_the_writer_writes_l_only_owns_it_and_replays():
    w = pe.writer_semantics()
    assert w["pass"] and w["channels_written"] == ["L"]
    owner = EdemaCongestion("e", 0.005, 0.005)
    assert type(from_spec(owner.to_spec())).lung_water_authority is True
    for bad in (-0.1, float("nan"), True):
        with pytest.raises(CoreInvariantError):
            EdemaCongestion("e", bad)
    with pytest.raises(CoreInvariantError):
        DecongestiveTreatment("t", 0)


def test_decongestion_stops_at_l_rev_counting_the_common_clearance():
    p = pe.profile()
    for l_rev in (0.0, -0.4):
        a = er.anchors(reversible_lung_water=l_rev)
        states, _ = pe.course((EdemaCongestion("e", 0.01, 0.02), DecongestiveTreatment("t", 30)), 200, a, p)
        assert min(s.L for s in states) >= l_rev and abs(states[-1].L - l_rev) < 1e-12


def test_without_a_pulse_the_writer_writes_nothing():
    a, p = er.anchors(), pe.profile()
    w = EdemaCongestion("e", 0.01)
    state = dv.arrival_state(a, p)
    assert w.contribute(state, 1, (), a, p).deltas[0].amount == 0.01
    pulseless = state.evolve(R=RhythmState.vf(), terminal_since=0)
    assert w.contribute(pulseless, 1, (), a, p).deltas == ()


# The evaluation's pieces ------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def result():
    return json.loads(json.dumps(pe.run(), sort_keys=True))


def test_l_worsening_worsens_g_and_spo2_through_the_common_path(result):
    u = result["untreated"]
    assert u["pass"] and all(v["common_overload_writes"] == 0 for v in u["region"].values())
    for v in u["region"].values():
        assert all(v["directions"].values())
        assert v["family_L_sources"] == ["core_coupling:lung_water_clearance", "disease_module:edema-congestion"]


def test_oxygen_uses_the_common_fio2_path(result):
    o = result["oxygen"]
    assert o["pass"] and o["monotone_in_fio2"] and o["attenuated_as_G_worsens"] and not o["family_oxygen_function"]


def test_the_authority_holds_and_the_common_overload_stays_available(result):
    a = result["authority"]
    assert a["pass"] and a["owned"]["common_writes"] == 0 and a["owned"]["L_equals_writer_alone"]
    assert a["common_only"]["common_writes"] > 0 and a["second_owner_refused"]
    assert a["zero_gain_owner"] == {"common_writes": 0, "L_end": 0.0}


def test_decongestion_with_l_rev_zero_gives_no_credit_below_arrival(result):
    d = result["decongestion"]
    assert d["pass"] and d["l_rev"] == 0.0 and d["spo2_max"] == er.truth()["spo2"] and d["L_min"] >= 0.0
    assert d["scripted_below_arrival"]["L"] < 0.0 and d["scripted_below_arrival"]["G"] == 0.0


def test_hr_keeps_its_sign_and_nothing_is_retuned(result):
    h = result["heart_rate"]
    assert h["pass"] and h["untreated_minus_no_writer"] > 0.0 and h["oxygen_minus_untreated"] < 0.0
    assert dv.DEFAULT_PROFILE.hypoxaemia_threshold_spo2 == h["threshold"]


def test_the_consciousness_guard_and_the_arrival_ladder_misread_are_reported(result):
    c = result["consciousness"]
    assert c["pass"] and not c["derive_reads_p2l2_candidate"] and "ONE_HYPOXEMIA_CONSCIOUSNESS_SOURCE_ONLY" in c["guard"]
    assert c["arrival_level_core"] == 1 and c["arrival_level_authored"] == 0
    assert "LEGACY_SPO2_LADDER_ARRIVAL_MISREAD" in result["arrival"]["mismatches"]["consciousness_level"]["class"]


def test_the_respiratory_extension_is_expected_and_not_added(result):
    r = result["respiration"]
    assert r["extension_expected"] and r["gap"] > pe.RR_GAP and not r["rr_follows_L_or_G"]
    assert r["deferred_actions"] == ["VNI_COMMON_EXTENSION_DEFERRED"]


def test_treatments_map_to_common_targets_without_magnitudes(result):
    t = result["treatments"]
    assert t["pass"] and t["map"]["oxygen"]["class"] == "COMMON_TARGET_EXISTS"
    assert t["map"]["nitroglycerin"]["t_writer_refused"] and not t["map"]["diuretic"]["diuresis_blood_process"]
    assert t["map"]["niv"]["class"] == "VNI_COMMON_EXTENSION_DEFERRED"


def test_gi_and_acs_are_unchanged(result):
    n = result["non_regression"]
    assert n["pass"] and n["gi_o12"] and n["acs_evaluation"] and n["acs_authority_r7"] and n["common_overload_r8"]


def test_the_legacy_is_read_last_and_never_used_for_parameters(result):
    lc = result["legacy_comparison"]
    assert not lc["used_for_parameters"] and set(lc["rows"]) == {"0", "60", "120"}
    assert result["legacy"]["0"]["spo2"] == 81


def test_the_verdict_follows_the_predeclared_rule(result):
    v = result["verdict"]
    assert all(v["criteria"].values()) and v["letter"] == "B" and v["architecture_successful"]
    assert v["verdict"] == "PULMONARY_EDEMA_NEEDS_EXPECTED_RESPIRATORY_EXTENSION"
    assert v["recommendation"] == "IMPLEMENT_ONLY_THE_MINIMUM_RESPIRATORY_EXTENSION_REQUIRED"


# The frozen evaluation ----------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def record():
    if not pe.RECORD.exists():
        pytest.skip("the P2P-1 record is written by the evaluation run, after the freeze")
    return json.loads(pe.RECORD.read_text(encoding="utf-8"))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, result):
    # P2S-2 gave the anchors one candidate input (arrival_mechanics_efficiency), at its reference 1 here: the frozen record
    # predates it, so it is removed (and checked at the reference) before the comparison; nothing else moves.
    assert record["freeze_digest"] == FROZEN_DIGEST and record == mc.without_new_anchor_key(result)


def test_the_document_is_generated_from_the_record(record):
    from clinical_core import edema_migration_report as report
    text = pe.DOCUMENT.read_text(encoding="utf-8")
    for name, render in report.RENDERERS.items():
        opening, closing = report.MARKERS[name]
        start = text.index(opening) + len(opening)
        assert text[start:text.index(closing, start)] == render(record) + "\n", name


# The adversarial review -----------------------------------------------------------------------------------------------------

def test_review_the_authored_volume_loading_is_inert_in_l_and_declared(result):
    v = result["volume_loading"]
    assert v["event"] == "edema_volume_loading" and v["L_unchanged"] and v["position_with"] < v["knee"]
    assert v["with"]["map"] > v["without"]["map"] and v["class"].startswith("AUTHORED_DANGEROUS_ACTION_NOT_REPRESENTED")


@pytest.mark.parametrize("key, letter", [("arrival", "C"), ("heart_rate", "C"), ("writer", "C"), ("untreated", "C"),
                                         ("oxygen", "C"), ("decongestion", "C"), ("authority", "D"),
                                         ("non_regression", "D")])
def test_review_every_criterion_decides_a_letter(result, key, letter):
    found = copy.deepcopy(result)
    found[key]["pass"] = False
    assert pe.verdict(found)["letter"] == letter


def test_review_the_proof_and_the_extension_decide_their_letters(result):
    for name in ("p2o3_freeze_digest", "p2o3_record"):
        found = copy.deepcopy(result)
        found["proof"][name] = False
        assert pe.verdict(found)["letter"] == "D"
    found = copy.deepcopy(result)
    found["respiration"]["extension_expected"] = False
    assert pe.verdict(found)["letter"] == "A"


@pytest.mark.parametrize("extra", ["ChannelDelta(channel=Channel.G, amount=1.0)", "ChannelDelta(Channel.G, 1.0)",
                                   "ChannelDelta(chosen, 1.0)"])
def test_review_the_writer_guard_refuses_any_channel_but_a_literal_l(tmp_path, monkeypatch, extra):
    (tmp_path / "modules").mkdir()
    source = (pe.CORE_DIR / "modules" / "pulmonary_edema.py").read_text(encoding="utf-8")
    (tmp_path / "modules" / "pulmonary_edema.py").write_text(source + f"\n\ndef _probe(chosen):\n    return {extra}\n",
                                                            encoding="utf-8")
    monkeypatch.setattr(pe, "CORE_DIR", tmp_path)
    assert not pe.writer_semantics()["pass"]


def test_review_the_profile_differs_from_the_acs_point_only_in_the_gas_gains(result):
    assert result["heart_rate"]["gains_untouched"] and not result["oxygen"]["family_oxygen_function"]
    assert set(result["respiration"]["untreated_trends"]) == {"rr", "paco2", "lactate", "spo2"}
