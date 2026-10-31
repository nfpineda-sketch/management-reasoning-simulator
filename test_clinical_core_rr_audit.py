"""Phase 2 shadow core, P2K-1: the RR / ventilatory-drive structural audit.

These tests pin what the audit states about the core: RR's exact reads (W, the authored arrival RR and lactate, the RR
parameters and the derived lactate), D reaching RR only through lactate, the lactate concentration as a biomarker
proxy, W's mixed semantics and its readers and writers, the absence of pH, pCO2, bicarbonate and acid load, the probes
A-E, oxygen moving oxygenation only, the authored respiratory observations, the exact RR reconstruction, the directional
reading, the upstream dependencies, the unchanged core and the verdict: nothing approved, nothing calibrated.
"""
import ast
import hashlib
import inspect
import json
from dataclasses import fields, replace

import pytest

from clinical_core import baroreflex as br
from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, gi_reference, lactate_slice
from clinical_core import derived as dv
from clinical_core import lactate_adequacy as la
from clinical_core import lactate_rebuild as lr
from clinical_core import pressure_tone as pt
from clinical_core import rr_audit as ra
from clinical_core import vascular_tone as vt
from clinical_core.derived import DEFAULT_PROFILE, Derived, arrival_state, derive
from clinical_core.integration import step
from clinical_core.interventions.oxygen import Oxygen
from clinical_core.state import CoreState

ROOT = ra.ROOT
SOURCE = ROOT / "clinical_core" / "rr_audit.py"
#: The P2K-1 freeze: the faculty decisions, the equation and contributor classification, the D path, the W and
#: acid-base audits, the probe rule, the support audit, the reconstruction, direction, identifiability and verdict
#: rules, the missing structure and the decisions, and every clinical_core source but the downstream reports, committed
#: before any clinical RR trajectory was read.
FROZEN_DIGEST = "a3f098deb7d643e6158da3aaa8852874d6fa35d981379be173a17d6d8d8ec427"
#: P2K-1 is closed (P2K-2): its module and record byte for byte, and the modules added after it.
P2K1_MODULE_SHA = "4b663ffad81ff88f728707e7c96a255d882cbf62247107980652331fff885bf1"
P2K1_RECORD_SHA = "e297209a8d7bbe1c475e12b3f23f5881f95ec232ee68523b621d48ca7ef2824a"
LATER_MODULES = ("clinical_core/acid_base.py",)
C57, C72 = ra.C57, ra.C72


@pytest.fixture(scope="module")
def probes():
    return ra.probes()


# The frozen package ----------------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert "clinical_core/rr_audit.py" in sources
    assert "clinical_core/rr_audit_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert {"clinical_core/rr_audit.py", "clinical_core/rr_audit_report.py"} <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    assert ra.p2j4_record()["freeze_digest"] == ra.P2J4_DIGEST
    # P2K-1 is closed (P2K-2): its module and record are pinned byte for byte, and its freeze is recomputed from the live
    # sources without the later modules, with the core files and the two tuple-only files at their P2K-1 hashes while
    # P2K-2 only inserted its declared, off-by-default names (acid_base.p2k1_sources).
    from clinical_core import acid_base as ab
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == P2K1_MODULE_SHA, "the closed P2K-1 module changed"
    assert hashlib.sha256(RECORD.read_bytes()).hexdigest() == P2K1_RECORD_SHA
    sources = {k: v for k, v in bf.freeze_sources().items() if k not in LATER_MODULES}
    text = json.dumps({"revision": ra.REVISION, "p2j4": hashlib.sha256(ra.P2J4_RECORD.read_bytes()).hexdigest(),
                       "design": ra.design(), "sources": ab.p2k1_sources(sources)}, sort_keys=True, default=str)
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == FROZEN_DIGEST, "a source P2K-1 froze changed"


def test_the_faculty_decisions_and_the_carried_uncertainty_are_recorded():
    assert set(ra.FACULTY) == {"decided", "closed", "carried", "w_rr", "lactate", "kd_s1", "d", "early_stop", "scope"}
    assert ra.CARRIED["baroreflex_gain"] == {"1": [0.25, 0.5], "1.1": [0.25, 0.5, 1.0, 1.5]}
    assert ra.CARRIED["map_set"] == [80.0, 90.0, 100.0] and ra.CARRIED["approved"] == []
    assert "not collapsed" in ra.FACULTY["carried"] and "BIOMARKER_PROXY_REQUIRES_REFACTOR" in ra.FACULTY["lactate"]


# RR's causal paths ---------------------------------------------------------------------------------------------------------

def test_rr_reads_w_the_authored_arrival_and_the_derived_lactate_only():
    reads = ra.rr_reads()
    assert reads["respiratory_rate"]["attributes"] == ["anchors.lactate", "anchors.respiratory_rate", "profile.rr_max",
                                                       "profile.rr_ventilatory_floor", "state.W"]
    assert reads["respiratory_rate"]["calls"] == ["_metabolic_drive", "max", "min"]
    assert reads["_metabolic_drive"]["attributes"] == ["math.exp", "profile.lactate_drive_threshold_mmol_l",
                                                       "profile.rr_metabolic_max", "profile.rr_per_lactate"]
    assert "rr = respiratory_rate(state, anchors, profile, lactate)" in inspect.getsource(dv.derive)
    for forbidden in ("state.D", "spo2", "deficit", "glucose", "sympathetic", "oxygen_demand", "fio2"):
        assert forbidden not in inspect.getsource(dv.respiratory_rate) + inspect.getsource(dv._metabolic_drive)
    assert set(ra.RR_PARAMETERS) == {"rr_per_lactate", "lactate_drive_threshold_mmol_l", "rr_metabolic_max",
                                     "rr_ventilatory_floor", "rr_max"}


def test_every_contributor_is_classified_and_the_lactate_path_is_a_proxy():
    names = {c["name"] for c in ra.CONTRIBUTORS}
    assert {"baseline / intrinsic RR", "W", "effective oxygen deficit", "D", "lactate", "pH", "pCO2", "metabolic demand",
            "hypoxaemia", "glucose", "drugs", "respiratory support", "mechanics", "fatigue", "caps / floors",
            "case-specific terms", "legacy terms"} <= names
    assert all(c["class"] in ra.CLASSES for c in ra.CONTRIBUTORS)
    by = {c["name"]: c for c in ra.CONTRIBUTORS}
    assert by["lactate"]["class"] == "BIOMARKER_PROXY" and ra.BIOMARKER_PROXY_REQUIRES_REFACTOR in by["lactate"]["path"]
    assert by["D"]["class"] == "BIOMARKER_PROXY" and by["W"]["class"] == "SEMANTIC_LEAK"
    assert by["lactate gain value"]["class"] == "LEGACY_ARTIFACT"
    assert "legacy GI RR gain" in dv.PARAMETERS["rr_per_lactate"][1]


def test_d_reaches_rr_only_through_lactate(probes):
    c = probes["C"]
    assert c["rr_moves_only_with_lactate"] and c["first_minute_rr_change"] == 0.0
    assert c["lactate_held"]["D_end"] > 0.0 and len(set(c["lactate_held"]["rr"])) == 1
    assert c["with_lactate_production"]["rr"][-1] > c["with_lactate_production"]["rr"][0]
    assert [step_[0] for step_ in ra.D_PATH] == ["integration.step", "integration.step", "derived.derive",
                                                  "derived.derive", "derived.respiratory_rate"]
    assert "profile.debt_to_lactate_gain * state.D" in inspect.getsource(dv.lactate_after_minute)


def test_a_lactate_rise_alone_raises_rr(probes):
    b = probes["B"]
    assert b["result"] == "RR_RISES_FROM_LACTATE_ALONE" and b["rise"] > 0.0
    assert b["deficit"] == 0.0 and b["D"] == 0.0 and b["W"] == 0.0


def test_the_same_debt_with_faster_clearance_gives_a_lower_rr(probes):
    clearance = probes["clearance"]
    assert clearance["rr_follows_clearance"] and clearance["30"]["rr"] < clearance["120"]["rr"]


# W, acid-base, probes ------------------------------------------------------------------------------------------------------

def _readers_of_w():
    out = set()
    for path in sorted((ROOT / "clinical_core").glob("*.py")):
        if path.name.endswith("_report.py") or path.name == "rr_audit.py":
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.FunctionDef):
                if any(isinstance(n, ast.Attribute) and n.attr == "W" and isinstance(n.value, ast.Name)
                       and n.value.id == "state" for n in ast.walk(node)):
                    out.add((path.name, node.name))
    return out


def test_w_is_a_mixed_construct_read_only_by_rr(probes):
    assert ra.W_AUDIT["class"] == "MIXED_DRIVE_AND_VENTILATION_CONSTRUCT" and ra.W_AUDIT["arrival"] == 0.0
    readers = _readers_of_w()
    assert {r for r in readers if r[0] != "decision_pack.py"} == {("derived.py", "respiratory_rate")}
    assert {r[1] for r in readers if r[0] == "decision_pack.py"} <= {"rr_parts", "rr_bounds"}, readers
    # P2K-2 adds one file that names W: its probe writes the W channel to show the candidate RR does not read it.
    assert ra.w_references() == ["clinical_core/acid_base.py", "clinical_core/bands.py", "clinical_core/decision_pack.py",
                                 "clinical_core/derived.py", "clinical_core/integration.py", "clinical_core/state.py"]
    assert probes["D"]["w_minus_half_rr"] < probes["arrival_rr"] < probes["E"]["w_plus_half_rr"]
    assert not any("ventilation" in f.name for f in fields(Derived)), "no effective-ventilation output exists"


def test_no_acid_base_quantity_exists_in_the_core():
    names = {f.name for f in fields(Derived)} | {f.name for f in fields(CoreState)}
    assert not names & {"ph", "pH", "pco2", "paco2", "hco3", "bicarbonate", "base_excess", "acid_load"}
    assert ra.ACIDOSIS_TO_DRIVE["representable_without_lactate"] is False
    assert {k: v["class"] for k, v in ra.ACID_BASE.items()} == {
        "pH": "AUTHORED_OBSERVATION_ONLY", "pCO2": "AUTHORED_OBSERVATION_ONLY", "bicarbonate": "AUTHORED_OBSERVATION_ONLY",
        "metabolic acid load": "NOT_MODELED", "respiratory compensation": "NOT_MODELED"}


def test_probes_a_to_e(probes):
    assert probes["A"]["result"] == probes["D"]["result"] == probes["E"]["result"] == ra.NOT_REPRESENTABLE
    assert probes["B"]["result"] == "RR_RISES_FROM_LACTATE_ALONE"
    assert "deficit -> D -> lactate" in probes["C"]["pathway"]
    assert not probes["hypoxaemia"]["independent_drive"]


def test_oxygen_moves_oxygenation_only(probes):
    assert probes["oxygen"]["oxygenation_only"]
    anchors, profile = ra.PROBE_ANCHORS, ra._profile()
    start = arrival_state(anchors, profile)
    after, record = step(start, (Oxygen("o", 1, 0.6),), anchors, profile)
    after, record = step(after, (Oxygen("o", 1, 0.6),), anchors, profile)
    assert after.fio2 == 0.6 and after.W == start.W and not any(d.channel.value == "W" for d in record.deltas)
    assert ra.SUPPORT["NIV / BiPAP"] == ra.SUPPORT["invasive ventilation"] == "NOT_MODELED"


# Authored observations and the reconstruction -----------------------------------------------------------------------------

def test_the_authored_respiratory_observations_are_the_case_bank_s():
    authored = ra.authored()
    assert authored[C57]["respiratory_rate"]["value"] == 26 and authored[C72]["respiratory_rate"]["value"] == 24
    assert authored[C57]["abg"]["value"].startswith("pH 7.37, PaCO2 31") and authored[C72]["abg"]["value"].startswith(
        "pH 7.40, PaCO2 33")
    assert authored[C57]["abg"]["parts"]["HCO3"].startswith("MODEL_DERIVED")
    for case in ra.CASES:
        assert authored[case]["oxygen_support"]["origin"] == "LEGACY_REFERENCE"
        assert authored[case]["later_respiratory_observations"]["origin"] == "NOT_STATED"
        assert authored[case]["respiratory_rate"]["value"] == gi_reference.authored(case, "respiratory_rate")


def test_the_rr_reconstruction_equals_the_core():
    record = la.record_p2i2ab()
    source, support = la.source_space(record), record["crystalloid_support"]
    arrivals = lr.arrival_table()
    for case, lam in ((C57, 612), (C72, 611)):
        for name, entry, bag in (("P1", source["p1"][0], None), ("P2", source["p1"][0], support[0]["bag"]),
                                 ("P3", source["p3"][0], None), ("P4", source["p3"][0], None)):
            _, blood = vt._blood_task(((name, case, 0), entry, case, vt.SCENARIOS[name], bag))
            for factor, gain in ((1.0, 0.25), (1.1, 1.0)):
                traj = ra.trajectory(blood, case, lam, factor, gain, arrivals)
                core = pt.full_run(entry, case, pt.SCENARIOS[name], factor, ra.LAMBDAS[lam], bag, "midpoint",
                                   {"deficit_to_tone_gain": gain, "afterload_sensitivity": ra.AFTERLOAD})
                assert [r["rr"] for r in core["rows"]] == traj["rr"], (case, name, factor, gain)
                assert [r["lactate"] for r in core["rows"]] == traj["lactate"]


def test_one_unit_per_scenario_no_hr_or_baroreflex_dimension():
    assert "HR, MAP_set and the baroreflex gain do not reach RR" in ra.RECONSTRUCTION_RULE
    source = inspect.getsource(ra.reconstruct)
    assert "MAP_SETS" not in source and "PRIMARY_BARO" not in source and "combos" not in source


# Directions, dependencies, identifiability, verdict ------------------------------------------------------------------------

def test_the_directions_read_as_frozen(probes):
    result = ra.directions(probes, {})
    assert {k: v["status"] for k, v in result.items() if k in (4, 5, 7)} == {4: ra.NOT_REPRESENTABLE,
                                                                            5: ra.NOT_REPRESENTABLE,
                                                                            7: ra.NOT_REPRESENTABLE}
    assert result[1]["status"] == "PASSES_FOR_THE_PROXY_ONLY" and result[2]["status"] == "PASSES"
    assert result[3]["status"] == "VIOLATED_BY_THE_PROXY" and result[6]["status"] == "PASSES"
    assert set(result) == set(ra.DIRECTIONS)


def test_hr_and_the_baroreflex_never_reach_rr():
    for function in (dv.respiratory_rate, dv._metabolic_drive, dv.lactate_after_minute):
        text = inspect.getsource(function)
        assert "sympathetic" not in text and "baroreflex" not in text and "pulse_rate" not in text
    anchors = ra.PROBE_ANCHORS
    off = replace(DEFAULT_PROFILE, oxygen_extraction_reserve=ra.RESERVE, sympathetic_per_pressure_deficit=0.0)
    on = replace(off, baroreflex_to_sympathetic_gain=1.5, baroreflex_map_set_mmhg=100.0, acute_deficit_to_sympathetic_gain=2.0)
    a, b = arrival_state(anchors, off).evolve(P=0.3), arrival_state(anchors, on).evolve(P=0.3)
    for _ in range(10):
        a, _ = step(a, (), anchors, off)
        b, _ = step(b, (), anchors, on)
        assert derive(a, anchors, off).respiratory_rate == derive(b, anchors, on).respiratory_rate
    deps = ra.dependencies({})
    assert deps["map_set"]["path"].startswith("NONE") and deps["baroreflex_gain"]["path"].startswith("NONE")
    assert deps["hr_latent"]["path"].startswith("NONE")


def test_the_core_is_unchanged_and_nothing_is_corrected_or_approved():
    # P2K-2 changed the core files only by its off-by-default insertions: stripped of them, each is the P2K-1 file.
    from clinical_core import acid_base as ab
    assert not all(ra.core_unchanged().values()) and all(ab.proofs().values())
    assert ra.CORRECTION["made"] is False and ra.CANDIDATE_SURFACE["built"] is False
    checks = {name: False for name in ra.BLOCKERS}
    assert ra.verdict(checks)["verdict"] == f"{ra.NOT_READY} — ACID_BASE_STATE_REQUIRED"
    assert ra.verdict({name: True for name in ra.BLOCKERS})["verdict"] == ra.READY
    assert ra.verdict(checks)["approved"] == []
    assert "(1) a metabolic acid-load state" in ra.MISSING_STRUCTURE and len(ra.DECISIONS) == 5


def test_identifiability_is_not_applicable_on_the_proxy_paths():
    result = ra.identifiability({("g", "f", "P1", C57): {("k", 0): (None, {"rr": [26.0, 27.0], "metabolic": [1.0]})}})
    assert result["metabolic_gain"]["class"] == result["d_lactate_pathway"]["class"] == "NOT_APPLICABLE"
    assert result["baseline_rr"]["class"] == "PARTIALLY_CONSTRAINED" and result["rr_max"]["class"] == "NON_IDENTIFIABLE"


def test_no_legacy_no_p2f_nothing_approved():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported = {(n.module or "") + ":" + a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names}
    assert not any(x in name for name in imported for x in ("family_engine", "legacy_adapter", "contracts_legacy",
                                                             ":shadow"))
    assert "lr.P2FGuard(), lr.LegacyLock()" in inspect.getsource(ra.run)
    assert '"approved": []' in inspect.getsource(ra.verdict) and '"candidate_runs": 0' in inspect.getsource(ra.run)


# The committed record ----------------------------------------------------------------------------------------------------

RECORD = ROOT / "docs" / "revision" / "P2K1_rr_audit.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2K1_AUDITORIA_FR_Y_VENTILACION.md"


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def test_the_record_comes_from_the_frozen_package_and_its_analytic_part_is_reproduced_live(record, probes):
    assert record["freeze_digest"] == FROZEN_DIGEST and record["record"] == ra.P2J4_DIGEST
    assert record["design"] == _json(ra.design()) and record["probes"] == _json(probes)
    assert record["authored"] == _json(ra.authored()) and record["reads"] == _json(ra.rr_reads())
    assert record["w_references"] == [r for r in ra.w_references() if r != "clinical_core/acid_base.py"]
    assert all(record["core_unchanged"].values())


def test_the_verdict_and_the_reconstruction_the_report_states(record):
    assert record["verdict"]["verdict"] == f"{ra.NOT_READY} — ACID_BASE_STATE_REQUIRED"
    assert record["verdict"]["blockers"] == list(ra.BLOCKERS) and record["verdict"]["approved"] == []
    assert record["validation"] == {"compared": 48, "equal": True}
    assert record["pressure_tone_unchanged"] == {"units": True, "primary": True, "support": True, "demand_class": True}
    assert {k: v["status"] for k, v in record["directions"].items()} == {
        "1": "PASSES_FOR_THE_PROXY_ONLY", "2": "PASSES", "3": "VIOLATED_BY_THE_PROXY", "4": "NOT_REPRESENTABLE",
        "5": "NOT_REPRESENTABLE", "6": "PASSES", "7": "NOT_REPRESENTABLE", "8": "PASSES"}
    assert record["efficiency"]["candidate_runs"] == 0 and not record["efficiency"]["cartesian_sweep"]
    assert record["identifiability"]["rr_max"]["class"] == "NON_IDENTIFIABLE"
    assert record["dependencies"]["demand"]["max_rr_difference"] == {"n": 0}


def test_rr_depends_on_demand_through_the_lactate_chain():
    """The frozen comparison found no unit at both demands (the surviving lactate-side points differ); here one unit at
    1.0 and 1.1 (supplementary, after the run)."""
    record = la.record_p2i2ab()
    source = la.source_space(record)
    for case, lam in ((C57, 612), (C72, 611)):
        rows = {factor: pt.full_run(source["p3"][0], case, pt.L1, factor, ra.LAMBDAS[lam], None, "midpoint",
                                    {"deficit_to_tone_gain": 0.5, "afterload_sensitivity": ra.AFTERLOAD})["rows"]
                for factor in ra.DEMANDS}
        assert rows[1.0][0]["rr"] == rows[1.1][0]["rr"]
        assert any(a["rr"] != b["rr"] for a, b in zip(rows[1.0], rows[1.1]))
        assert any(a["D"] != b["D"] for a, b in zip(rows[1.0], rows[1.1]))


def test_the_document_is_generated_from_the_record(tmp_path):
    from clinical_core import rr_audit_report as rp
    copy = tmp_path / "doc.md"
    copy.write_text(DOCUMENT.read_text(encoding="utf-8"), encoding="utf-8")
    assert rp.main(["--write", str(copy), "--data", str(RECORD)]) == 0
    assert copy.read_text(encoding="utf-8") == DOCUMENT.read_text(encoding="utf-8")
    text = DOCUMENT.read_text(encoding="utf-8")
    assert "RR_STRUCTURE_NOT_READY — ACID_BASE_STATE_REQUIRED" in text
    for name in rp.NAMES:
        assert f"<!-- generado:{name} -->" in text


# After the adversarial review of P2K-1 (tests only; the frozen module is unchanged) ----------------------------------------

def _course(anchors, profile, items, minutes=20, fio2=None):
    state = arrival_state(anchors, profile).evolve(P=0.3)
    if fio2 is not None:
        state = state.evolve(fio2=fio2)
    for _ in range(minutes):
        state, _ = step(state, items, anchors, profile)
    return state, derive(state, anchors, profile)


def test_oxygen_and_desaturation_reach_rr_only_through_the_debt_and_lactate_chain():
    """Review M1: with a deficit, FiO2 moves SpO2, delivery, the deficit and D, and RR follows through lactate; with the
    lactate held, RR does not move at all. Oxygen has no direct path to RR or W."""
    anchors, profile = ra.PROBE_ANCHORS, ra._profile()
    room, room_view = _course(anchors, profile, ())
    oxy, oxy_view = _course(anchors, profile, (Oxygen("o", 0, 0.6),))
    assert oxy.fio2 == 0.6 and oxy.D < room.D and oxy_view.lactate < room_view.lactate
    assert oxy_view.respiratory_rate < room_view.respiratory_rate and oxy.W == room.W == 0.0
    held = ra._profile(debt_to_lactate_gain=0.0)
    _, a = _course(anchors, held, ())
    _, b = _course(anchors, held, (Oxygen("o", 0, 0.6),))
    assert a.respiratory_rate == b.respiratory_rate and a.spo2 != b.spo2
    high = replace(anchors, fio2=0.6)
    _, kept = _course(high, profile, (), fio2=0.6)
    _, dropped = _course(high, profile, (Oxygen("o", 0, 0.21),), fio2=0.6)
    assert dropped.respiratory_rate > kept.respiratory_rate, "desaturation raises RR only through D -> lactate"


def test_haemostasis_moves_rr_no_more_than_any_other_minute_and_rr_recovers_after_definitive_care():
    """Review M3: the frozen direction-8 check compares a step with the largest step including itself; here the
    haemostasis step is compared with every other step of the same R4 trajectory, and recovery is read on R4."""
    record = la.record_p2i2ab()
    source, arrivals = la.source_space(record), lr.arrival_table()
    for case, lam in ((C57, 612), (C72, 611)):
        _, blood = vt._blood_task((("P4", case, 0), source["p3"][0], case, vt.SCENARIOS["P4"], None))
        for factor, gain in ((1.0, 0.25), (1.1, 1.0)):
            t = ra.trajectory(blood, case, lam, factor, gain, arrivals)
            h = t["controlled_at"]
            steps = [abs(b - a) for a, b in zip(t["rr"], t["rr"][1:])]
            assert h is not None and steps[h] <= max(steps[:h] + steps[h + 1:])
            assert t["ventilatory"] <= t["rr"][120] <= max(t["rr"])


#: The exact content of the two exclusion tuples after P2K-1 (review B3): the closure proofs accept any tuple
#: content, so it is pinned here.
TUPLES_AT_P2K1 = {"DOWNSTREAM_REPORTS": ("6168a4c03e11e94b625d5eaf6706181f253860e3646d4cb13e1b479a501cc67a", 20),
                  "PACK_DIGEST_EXCLUDED": ("64f2e94cfea36f7ba4d73b63a1c935e612626c6161158bdd5dfafba48bfd2dca", 49)}


#: What P2K-2 added to them.
TUPLES_ADDED_BY_P2K2 = {"DOWNSTREAM_REPORTS": ("clinical_core/acid_base_report.py",),
                        "PACK_DIGEST_EXCLUDED": ("clinical_core/acid_base.py", "clinical_core/acid_base_report.py")}


def test_the_exclusion_tuples_hold_exactly_their_p2k1_content():
    for name, values in (("DOWNSTREAM_REPORTS", lactate_slice.DOWNSTREAM_REPORTS),
                         ("PACK_DIGEST_EXCLUDED", decision_pack.PACK_DIGEST_EXCLUDED)):
        added = TUPLES_ADDED_BY_P2K2[name]
        assert set(added) <= set(values), name
        values = [v for v in values if v not in added]
        assert (hashlib.sha256(json.dumps(sorted(values)).encode("utf-8")).hexdigest(), len(values)) == \
            TUPLES_AT_P2K1[name], name


def test_the_other_ventilation_related_channels_are_named_and_read_by_neither_rr_nor_spo2():
    """Review M6: L (lung water), G (gas exchange) and N (CNS depression) exist as channels; neither RR nor SpO2 reads
    them today, which the decisions on W and support must take into account."""
    from clinical_core.state import Channel
    assert {"L", "G", "N"} <= {c.value for c in Channel}
    text = inspect.getsource(dv.respiratory_rate) + inspect.getsource(dv._perfusion)
    for name in ("state.L", "state.G", "state.N"):
        assert name not in text
