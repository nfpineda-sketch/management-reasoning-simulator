"""P2L-1: the structural audit of consciousness / neurologic response (shadow only, read-only).

N's writers, readers and class; the observable consciousness equation and every causal path, each checked by a
perturbation through the certified core; the double-counting and orthogonality probes; the recovery lag; the probes
N1-N9; the authored GI neurologic observations; the carried extreme-acidemia subset; the upstream dependency; the
qualitative generalization; the structural verdict; the closure. The record tests read the committed run.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json

import pytest

from clinical_core import blood_fluid_calibration as bf
from clinical_core import gas_exchange_architecture as go
from clinical_core import lung_water_reference as lw
from clinical_core import edema_migration as pe
from clinical_core import respiratory_drive as rd
from clinical_core import embolism_migration as em
from clinical_core import respiratory_mechanics as mc
from clinical_core import asthma_migration as sm
from clinical_core import respiratory_distress as dm
from clinical_core import distress_closure as xm
from clinical_core import asthma_distress_migration as tm
from clinical_core import oxygenation_link as om
from clinical_core import opioid_migration as un
from clinical_core import systemic_stress as ss
from clinical_core import distributive_tone as dt
from clinical_core import tone_domain as x1
from clinical_core import consciousness_audit as ca
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import vascular_tone as vt

ROOT = ca.ROOT
SOURCE = ROOT / "clinical_core" / "consciousness_audit.py"
#: The P2L-1 freeze (second, after the adversarial review; declared in ca.FREEZE): the faculty decisions, the path
#: classes, the probes, the criteria, the verdict and next rules, the smallest structure and every clinical_core source
#: but the downstream reports, committed before the evaluation run.
FROZEN_DIGEST = "f3ec29e684331fd7750e4471d2cdc1b21374123bf2ab79c0e187a27ff2edf83c"
#: P2L-2's layer, added after P2L-1 closed: the audit's view of the tree leaves it out (its N reader is the candidate's,
#: P2L-2's own audit reports it), and the freeze is recomputed on P2L-1's sources (encephalopathy_architecture.
#: p2l1_sources); the record is unchanged.
LATER_MODULES = ("clinical_core/encephalopathy.py", "clinical_core/encephalopathy_architecture.py",
                 "clinical_core/collapse_audit.py",
                 "clinical_core/collapse.py", "clinical_core/collapse_architecture.py",
                 "clinical_core/acs_reference.py", "clinical_core/modules/acs_ischaemia.py",
                 "clinical_core/acs_migration.py", "clinical_core/gas_exchange_architecture.py",
                 "clinical_core/lung_water_reference.py",
                 "clinical_core/edema_migration.py", "clinical_core/edema_reference.py",
                 "clinical_core/modules/pulmonary_edema.py",
                 "clinical_core/respiratory_drive.py",
                 "clinical_core/embolism_reference.py", "clinical_core/modules/pulmonary_embolism.py",
                 "clinical_core/embolism_migration.py",
                 "clinical_core/respiratory_mechanics.py",
                 "clinical_core/asthma_reference.py", "clinical_core/modules/asthma.py", "clinical_core/asthma_migration.py",
                 "clinical_core/respiratory_distress.py",
                 "clinical_core/distress_closure.py",
                 "clinical_core/asthma_distress_migration.py",
                 "clinical_core/oxygenation_link.py",
                 "clinical_core/opioid_migration.py")


#: P2O-1 inserted its declared, inert names into derived.py and integration.py, proven byte for byte against the P2N-2
#: files (gas_exchange_architecture.proved): this package's guards read the P2N-2 core (go.p2n2_text, go.p2n2_sources,
#: go.p2n2_unchanged), never the live one; the record is unchanged.
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
#: P2W-1 changed the core (the common vasodilatory burden: one auxiliary field, one arrival anchor, one
#: provenance record and one UNSET profile reader of the tone target, the burden 0 by default) and two tuple
#: files, proven against the P2V-1 files (distributive_tone.proved): this package's guards read the tree as
#: P2V-1 left it (dt.chain, dt.p2v1_sources).
#: P2V-1 changed the core (the common systemic stress: one auxiliary field, one arrival anchor, one provenance
#: record and one UNSET profile reader, the stress 0 by default) and two tuple files, proven against the P2U-1
#: files (systemic_stress.proved): this package's guards read the tree as P2U-1 left it (ss.chain,
#: ss.p2u1_sources).
#: P2U-1 changed the core (the common central respiratory drive availability: one auxiliary field, one arrival
#: anchor and one provenance record, all at their reference 1 by default) and two tuple files, proven against the
#: P2T-5 files (opioid_migration.proved): this package's guards read the tree as P2T-5 left it (un.chain,
#: un.p2t5_sources).
_LIVE_SOURCES_P2X1 = bf.freeze_sources


def _LIVE_SOURCES_P2W1() -> dict:
    return x1.p2w1_sources(_LIVE_SOURCES_P2X1())


def _LIVE_SOURCES_P2V1() -> dict:
    return dt.p2v1_sources(_LIVE_SOURCES_P2W1())


def _LIVE_SOURCES_P2U1() -> dict:
    return ss.p2u1_sources(_LIVE_SOURCES_P2V1())


def _LIVE_SOURCES_P2T5() -> dict:
    return un.p2t5_sources(_LIVE_SOURCES_P2U1())


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


def _LIVE_SOURCES_P2P1() -> dict:
    return rd.p2p1_sources(_LIVE_SOURCES_P2P2())


def _LIVE_SOURCES_P2O3() -> dict:
    return pe.p2o3_sources(_LIVE_SOURCES_P2P1())


def _LIVE_SOURCES_P2O1() -> dict:
    return lw.p2o1_sources(_LIVE_SOURCES_P2O3())


@pytest.fixture(autouse=True, scope="module")
def _p2n2_core():
    with pytest.MonkeyPatch.context() as patch:
        lw.chain(patch)
        pe.chain(patch)
        rd.chain(patch)
        em.chain(patch)
        mc.chain(patch)
        sm.chain(patch)
        dm.chain(patch)
        xm.chain(patch, historical=False)
        tm.chain(patch)
        om.chain(patch)
        un.chain(patch)
        ss.chain(patch)
        dt.chain(patch)
        x1.chain(patch)
        patch.setattr(vt, "_live", go.p2n2_text)
        patch.setattr(bf, "freeze_sources", lambda: go.p2n2_sources(_LIVE_SOURCES_P2O1()))
        patch.setattr(ca, "closed_unchanged", lambda: go.p2n2_unchanged(ca.CLOSED_AT_P2K5))
        yield


@pytest.fixture(autouse=True)
def _p2l1_tree(monkeypatch):
    original = ca._python
    later = {ROOT / relative for relative in LATER_MODULES}
    # P2O-1: the scan reads the two core files as P2N-2 left them (go.p2n2_path, proven).
    monkeypatch.setattr(ca, "_python", lambda: [go.p2n2_path(p) for p in original() if p not in later])


def _freeze_digest_at_p2l1() -> str:
    """consciousness_audit.freeze_digest's formula on the sources P2L-1 froze (P2L-2's modules left out, the tuple-only
    files at their P2L-1 hashes while only their tuples changed)."""
    from clinical_core import collapse_audit as cm
    from clinical_core import collapse_architecture as cy
    from clinical_core import acs_migration as an
    from clinical_core import encephalopathy_architecture as ea
    assert '"sources": bf.freeze_sources()}, sort_keys=True, default=str)' in inspect.getsource(ca.freeze_digest)
    text = json.dumps({"revision": ca.REVISION, "p2k5": hashlib.sha256(ca.P2K5_RECORD.read_bytes()).hexdigest(),
                       "p2j3": hashlib.sha256(ca.P2J3_RECORD.read_bytes()).hexdigest(), "design": ca.design(),
                       "sources": ea.p2l1_sources(cm.p2l2_sources(cy.p2m1_sources(an.p2m2_sources(bf.freeze_sources()))))}, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# The frozen package and its closure --------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert set(ca.OWN) <= set(sources) and ca.REPORT not in sources
    assert ca.REPORT in lactate_slice.DOWNSTREAM_REPORTS
    assert {ca.OWN[0], ca.REPORT} <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    assert ca._record(ca.P2K5_RECORD, ca.P2K5_RECORD_SHA)["verdict"]["verdict"] == \
        "GI_RESPIRATORY_PHYSIOLOGY_CLOSED_FOR_CURRENT_PHASE"
    assert ca._record(ca.P2J3_RECORD, ca.P2J3_RECORD_SHA)["support"]
    if FROZEN_DIGEST is not None:
        assert _freeze_digest_at_p2l1() == FROZEN_DIGEST, "a source, a rule or a probe changed after the freeze"


def test_the_closed_files_keep_their_p2k5_bytes_and_nothing_imports_the_audit():
    assert all(ca.closed_unchanged().values()) and len(ca.CLOSED_AT_P2K5) == 8
    for path in (ROOT / "clinical_core").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                    for alias in node.names} | {node.module or "" for node in ast.walk(tree)
                                                if isinstance(node, ast.ImportFrom)}
        if any("consciousness_audit" in name for name in imported):
            # Its report, and P2L-2's analysis, which reuses the frozen scan and the pinned-record reader.
            assert path.name in ("consciousness_audit_report.py", "encephalopathy_architecture.py"), path.name
    own = {alias.name for node in ast.walk(ast.parse(SOURCE.read_text(encoding="utf-8")))
           if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    assert not own & {"family_engine", "legacy_adapter", "ventilation_filter", "respiratory_monotonicity", "ventilation"}


def test_the_closed_packages_see_p2k5s_sources():
    sources = bf.freeze_sources()
    mapped = ca.p2k5_sources(sources)
    assert not set(ca.OWN) & set(mapped)
    for relative, sha in ca.TUPLE_AT_P2K5.items():
        assert mapped[relative] == sha
    original = vt._live
    try:
        vt._live = lambda relative: original(relative) + "\nX = 1\n"
        assert ca.p2k5_sources(sources)["clinical_core/decision_pack.py"] == sources["clinical_core/decision_pack.py"]
    finally:
        vt._live = original


# P2L-1-1: N --------------------------------------------------------------------------------------------------------------

def test_n_is_an_unused_placeholder():
    n = ca.n_audit()
    assert n["classification"] == "UNUSED_PLACEHOLDER" and n["arrival_value"] == 0.0
    refs = n["references"]
    assert refs["writes"] == n["writers"] and all(w.startswith("state.py") for w in refs["writes"])
    assert refs["reads"] == [] and n["readers_rule"].startswith("no reader")
    assert {r.split(":")[0] for r in refs["generic_scalar_loops"]} <= {"state.py", "integration.py", "contracts_output.py"}
    assert set(n["observable_effect"].values()) == {0}
    assert "contracts_output" in n["serialization"] and n["declared_semantics"].startswith("MIXED_NEUROLOGIC_CONSTRUCT")


def test_the_reference_scan_is_recursive_and_finds_known_readers():
    files = {path.relative_to(ROOT / "clinical_core").as_posix() for path in ca._python()}
    assert any(name.startswith("modules/") for name in files) and "consciousness_audit.py" not in files
    assert ca.channel_references("N", "N")["files_scanned"] == len(files)
    tree = ast.parse("a = Channel.N\nb = Channel('N')\nc = 'N'\n")
    assert all(ca._is_channel(node.value, "N") for node in tree.body)
    # The same scan finds the readers of a channel the core does read (D: lactate and the sympathetic drive).
    d = ca.channel_references("D", "D")
    assert d["reads"] and d["writes"] and any(r.startswith("integration.py") for r in d["reads"])


# P2L-1-2: the equation and every causal path ------------------------------------------------------------------------------

def test_the_equation_is_the_cores_and_reads_only_pressure_saturation_and_the_arrival_floor():
    e = ca.equation_audit()
    assert e["source_line_present"] and e["pulseless_level"]
    assert e["pressure_levels"] == [[80.0, 1], [65.0, 2]] and e["oxygen_levels"] == [[87.0, 1], [80.0, 2]]
    assert all(row[0] == "adopted" and "family_engine" in row[1] for row in e["provenance"].values())


def test_every_path_is_classified_and_checked_by_a_perturbation():
    table = ca.path_table()
    assert set(row["class"] for row in table.values()) <= set(ca.PATH_CLASSES)
    moving = {name for name, row in table.items() if row.get("moves_level")}
    assert moving == {"sbp", "spo2", "arrival_level", "map"}
    assert {name for name, row in table.items() if row.get("moves_level_dynamic")} == {"effective_oxygen_deficit",
                                                                                         "demand"}
    assert table["pulse"]["class"] == "VALID_CAUSAL_PATH"
    assert table["sbp"]["class"] == table["spo2"]["class"] == table["map"]["class"] == "LEGACY_ARTIFACT"
    assert table["arrival_level"]["class"] == "SEMANTIC_LEAK"
    assert table["effective_oxygen_deficit"]["class"] == table["demand"]["class"] == "SEMANTIC_LEAK"
    for name in ("N", "D", "glucose", "ph", "paco2", "lactate", "hr"):
        assert table[name]["class"] == "NOT_CURRENTLY_MODELED" and not table[name].get("moves_level"), name
    # No direct lactate path: nothing to refactor as a biomarker proxy.
    assert all(row["class"] not in ("BIOMARKER_PROXY", "BIOMARKER_PROXY_REQUIRES_REFACTOR") for row in table.values())
    # The whole level expression (every argument of the max), read by AST: no name in it mentions lactate.
    tree = ast.parse(inspect.getsource(dv.derive).strip())
    level = [node.value for node in ast.walk(tree) if isinstance(node, ast.Assign)
             and any(getattr(t, "id", None) == "level" for t in node.targets)]
    assert level and all(isinstance(v, ast.Call) and getattr(v.func, "id", None) == "max" for v in level)
    names = {getattr(n, "id", None) or getattr(n, "attr", None) for v in level for n in ast.walk(v)}
    assert {"consciousness_level", "sbp", "spo2", "pressure_levels", "oxygen_levels"} <= names
    assert not any("lactate" in (name or "") for name in names)


# P2L-1-3 to -6: double counting and orthogonality ---------------------------------------------------------------------------

def test_map_and_deficit_are_distinct_signals_but_only_pressure_is_read():
    p = ca.deficit_map_probes()
    assert p["signals_distinguish_a_from_b"] and p["current_a_impaired"] and p["current_b_alert"]
    rows = p["rows"]
    assert rows["A_low_map_no_deficit"]["deficit"] == 0.0 and rows["B_adequate_map_high_deficit_anaemia"]["sbp"] == 120.0
    assert rows["C_low_map_and_high_deficit"]["level"] == 2 and rows["D_neither"]["level"] == 0
    # MAP moves the level today (through SBP = 4/3 MAP): a vasoconstricted low-output state at MAP 52 reads drowsy.
    assert rows["B2_vasoconstricted_low_output_map_52"]["map"] == pytest.approx(52.26, abs=0.01)
    assert rows["B2_vasoconstricted_low_output_map_52"]["level"] == 1


def test_the_tone_response_inverts_the_deficit_path():
    loop = ca.tone_loop()
    assert loop["start_level"] == 1 and loop["inverted_at_some_primary_gain"]
    assert {k for k, v in loop["level_improves_with_deficit"].items() if v} == {
        "anaemia g0.5", "anaemia g1", "demand_x2 g0.5", "demand_x2 g1"}
    rows = loop["rows"]["anaemia g1"]
    assert [r["level"] for r in rows] == [1, 0, 0] and rows[-1]["deficit"] > rows[0]["deficit"] > 0.0
    assert all(r["level"] == 1 for r in loop["rows"]["anaemia g0"])  # no tone response: no inversion


def test_spo2_is_not_double_counted_in_the_ladder_range_and_the_deficit_misses_hypoxaemia():
    p = ca.oxygenation_probes()
    assert not p["double_count_in_ladder_range"] and p["deficit_misses_hypoxaemia"] and p["current_a_impaired_b_alert"]
    assert p["deficit_onset_spo2"] == pytest.approx(38.8, abs=0.05) and p["ladder_top"] == 87.0
    rows = p["rows"]
    assert rows["A_low_spo2_adequate_delivery"]["do2"] == 1.0 and rows["A_low_spo2_adequate_delivery"]["level"] == 1
    a2 = rows["A2_fio2_falls_from_1_to_room_air"]
    assert a2["spo2"] == pytest.approx(73.3) and a2["deficit"] == 0.0 and a2["level"] == 2
    assert rows["B_normal_spo2_critical_deficit"]["deficit"] > 0.0 and rows["B_normal_spo2_critical_deficit"]["level"] == 0


def test_metabolic_acidemia_and_hypercapnia_are_kept_apart_and_compensation_is_representable_at_arrival():
    p = ca.acid_base_probes()
    assert p["distinguishes"] and p["compensated_at_arrival_representable"]
    assert not p["renal_compensation_during_encounter"]
    c = p["compensated_at_arrival"]
    assert c["hco3"] == 32.0 and c["paco2"] == pytest.approx(50.0) and c["ph"] == pytest.approx(7.429, abs=1e-3)
    rows = p["rows"]
    assert rows["A_metabolic_acidemia"]["paco2"] < 30.0 < 50.0 < rows["B_hypercapnia"]["paco2"]
    assert {row["level"] for row in rows.values()} == {0}


def test_glucose_is_orthogonal_and_unread():
    p = ca.glucose_probe()
    assert p["level_unchanged"] and p["rows"]["severe_hypoglycaemia"]["deficit"] == 0.0
    assert {w.split(":")[0] for w in p["writers"]} <= {"state.py", "legacy_adapter.py", "bands.py"}
    assert p["writers_rule"].startswith("constructors only")


# P2L-1-7, -10: recovery lag and the neurologic probes -----------------------------------------------------------------------

def test_no_memory_can_carry_a_neurologic_recovery_lag():
    r = ca.recovery_lag()
    assert r["insult_level"] == 2 and r["restored_level"] == 0 and not r["lag_represented"]
    # One integrator minute: D accrues only under a deficit and repays otherwise.
    d = r["d_after_one_minute"]
    assert d["deficit_shock"] == pytest.approx(0.25) and d["restored_d600_no_deficit"] == pytest.approx(590.0)
    assert d["low_map"] == d["hypoglycaemia"] == d["hypercapnia"] == 0.0
    assert r["d_covers_insult"] == {"deficit_shock": True, "low_map": False, "hypoglycaemia": False,
                                    "hypercapnia": False}
    assert not r["d_sufficient"] and r["new_state_required"] and len(r["options"]) == 2
    assert r["verdict"] == ca.BLOCKER and {"D", "state.internal"} <= set(r["memories"])
    assert r["expectation"].startswith("FACULTY_PRIOR_CONCEPT")


def test_the_neurologic_probes():
    p = ca.neuro_probes()
    assert p["represented"] == ["N1", "N4", "N8"] and p["signal_missing"] == ["N9"]
    rows = p["rows"]
    for name in ("N2", "N3", "N5", "N6", "N7"):
        assert rows[name]["level"] == 0 and rows[name]["gap"] == "the observable does not read the signal", name
    assert rows["N9"]["gap"].startswith("a common memory")


# P2L-1-8, -9: authored observations and the extreme-acidemia subset -----------------------------------------------------------

def test_the_authored_gi_neurologic_observations():
    bank = (ROOT / "clinical_cases.py").read_text(encoding="utf-8")
    for case in ca.CASES:
        a = ca.authored(case)
        assert a["presentation"]["value"] in bank and a["presentation"]["class"] == "AUTHORED_OBSERVATION"
        assert a["mental_status"]["value"] == "Alert" and a["core_arrival_level"]["value"] == 0
        assert a["map"]["class"] == "MODEL_DERIVED" and a["legacy_arrival"]["class"] == "LEGACY_REFERENCE"
        assert a["absent"]["later_neurologic_anchors"].startswith("none authored")
    assert "Awake and oriented" in ca.authored(ca.C57)["neurological_exam"]["value"]


def test_the_extreme_acidemia_subset_is_carried_and_already_reads_obtunded():
    x = ca.extreme_acidemia()
    assert x["flagged"] == 17604 and x["by_case"] == {ca.C57: 17604, ca.C72: 0}
    assert x["classification"] == "CONSCIOUSNESS_COLLAPSE_REVIEW" and x["lowest"]["ph"] < 7.0
    assert x["highest_untreated_sbp120"] < 65.0 and x["current_level_at_120"] == 2
    assert x["units_match"] and set(x["units"]) == {"0.25", "0.5", "1"}
    assert all(v["p2k5"] == v["p2j3"] for v in x["units"].values()) and x["unit"].startswith("candidate rows")
    assert not x["fully_alert_plausible"] and not x["filtered"]


# P2L-1-12, -13: generalization and upstream ----------------------------------------------------------------------------------

def test_the_upstream_dependency_and_the_generalization():
    u = ca.upstream()
    assert u["evidence"] == {"hr_moves_level": False, "demand_moves_level_fixed": False,
                             "demand_moves_level_with_tone_response": True, "sbp_moves_level": True}
    assert u["table"]["map_set"]["current"] == u["table"]["baroreflex_gain"]["current"] == "no"
    assert u["table"]["tone_gain"]["current"].startswith("yes") and u["table"]["demand"]["current"].startswith("yes")
    g = ca.generalization()
    assert g["result"] == "STRUCTURAL_GAP" and set(g["families"]) == {
        "hemorrhagic_shock", "hypoglycaemia", "hypercapnia_opioid", "primary_neurologic_injury", "severe_hypoxaemia",
        "distributive_shock"}
    text = json.dumps(ca.design())
    assert "gi_bleed" not in json.dumps({k: ca.design()[k] for k in ("smallest_structure", "decision_surface")})
    assert "maximum" in text and "no lactate term" in text and "no SBP ladder" in text


# P2L-1-15: the verdict, the early stop, the scope ------------------------------------------------------------------------------

def test_the_verdict_names_the_early_stop_blocker():
    good = {name: True for name in ca.CRITERIA}
    assert ca.verdict(good)["verdict"] == ca.READY
    assert ca.recommendation(ca.verdict(good))["recommendation"] == "PREPARE_OBSERVABLE_CONSCIOUSNESS_DECISION_PACK"
    lagged = ca.verdict({**good, "recovery_lag_coherent": False, "causal_modifiers_explicit": False})
    assert lagged["verdict"] == f"{ca.NOT_READY} - {ca.BLOCKER}" == f"{ca.NOT_READY} - RECOVERY_LAG_STATE_REQUIRED"
    assert lagged["failing"] == ["causal_modifiers_explicit", "recovery_lag_coherent"]
    assert ca.recommendation(lagged)["recommendation"] == "STOP_FOR_FACULTY_STRUCTURAL_DECISION"
    assert ca.verdict({**good, "lactate_not_proxy": False})["verdict"] == f"{ca.NOT_READY} - LACTATE_NOT_PROXY"


def test_a_changed_closed_file_stops_before_any_probe(monkeypatch):
    monkeypatch.setattr(ca, "closed_unchanged", lambda: {"clinical_core/derived.py": False})
    monkeypatch.setattr(ca, "n_audit", lambda: pytest.fail("no probe after a STOP"))
    out = ca.run()
    assert out["stopped"].startswith("a closed file changed") and out["verdict"]["checks"]["upstream_unchanged"] is False


def test_the_scope_adds_and_reads_nothing_it_should_not():
    source = SOURCE.read_text(encoding="utf-8")
    for forbidden in ("import family_engine", "legacy_adapter", "snapshot("):
        assert forbidden not in source
    assert "nothing selected or approved" in ca.POLICY and ca.MIGRATION_GATE.startswith("MIGRATION_GATE_CLOSED")
    assert ca.SMALLEST_STRUCTURE["not_added_here"].startswith("no state")
    assert ca.DECISION_SURFACE["numeric"].startswith("none")
    assert {v["status"] for v in ca.DOUBLE_COUNTING.values()} == {"PENDING_FACULTY", "SEPARABLE"}
    assert ca.DOUBLE_COUNTING["ph_and_paco2"]["status"] == "SEPARABLE"
    assert "never as the arrival value of F" in ca.SMALLEST_STRUCTURE["arrival"]
    # The legacy reference is quoted from the engine as text (never imported, never fitted).
    engine = (ROOT / "family_engine.py").read_text(encoding="utf-8")
    for name in ("_PRESSURE_LEVELS", "_OXYGEN_LEVELS", "_anchored_levels", "_RECOVERY_MARGIN", "MENTAL_RECOVERY"):
        assert name in engine and name in ca.LEGACY[{"_PRESSURE_LEVELS": "thresholds", "_OXYGEN_LEVELS": "thresholds",
                                                     "_anchored_levels": "dc1", "_RECOVERY_MARGIN": "margin",
                                                     "MENTAL_RECOVERY": "recovery"}[name]]


# The record and the report (generated once, after the frozen evaluation) -----------------------------------------------------

RECORD = ROOT / "docs" / "revision" / "P2L1_consciousness_audit.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2L1_AUDITORIA_CONCIENCIA.md"


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record):
    assert record["freeze_digest"] == FROZEN_DIGEST and "stopped" not in record
    assert record["design"] == _json(ca.design()) and record["closed_unchanged"] == _json(ca.closed_unchanged())
    live = ca.run()
    for key in ("n", "equation", "paths", "perturbations", "tone_loop", "authored", "deficit_map", "oxygenation",
                "acid_base", "glucose", "recovery_lag", "neuro_probes", "extreme_acidemia", "upstream",
                "generalization", "double_counting", "verdict", "recommendation", "efficiency"):
        assert record[key] == _json(live[key]), key


def test_the_record_states_the_structural_verdict(record):
    v = record["verdict"]
    assert v["verdict"] == f"{ca.NOT_READY} - {ca.BLOCKER}" and not v["not_evaluated"]
    assert set(v["checks"]) == set(ca.CRITERIA)
    assert v["checks"]["upstream_unchanged"] and v["checks"]["nothing_approved"] and v["checks"]["lactate_not_proxy"]
    assert v["failing"] == ["n_semantics_explicit", "observable_separated_from_n", "causal_modifiers_explicit",
                            "double_counting_resolved", "recovery_lag_coherent", "generalization_plausible"]
    r = record["recommendation"]
    assert r["recommendation"] == "STOP_FOR_FACULTY_STRUCTURAL_DECISION" and r["smallest_structure"]["memory"]
    e = record["efficiency"]
    assert e["trajectory_simulations"] == 0 and e["cartesian_sweep"] is False and e["integrator_steps"] == 29
    assert record["extreme_acidemia"]["flagged"] == 17604 and record["extreme_acidemia"]["filtered"] is False


def test_the_document_is_generated_from_the_record():
    from clinical_core import consciousness_audit_report as rep
    document = DOCUMENT.read_text(encoding="utf-8")
    data = json.loads(RECORD.read_text(encoding="utf-8"))
    for name, render in rep.RENDERERS.items():
        assert rep.apply(document, name, render(data)) == document, name
    assert "RECOVERY_LAG_STATE_REQUIRED" in document and "STOP_FOR_FACULTY_STRUCTURAL_DECISION" in document
    assert "NEUROLOGIC_RECOVERY_STATE_REQUIRED" not in document
