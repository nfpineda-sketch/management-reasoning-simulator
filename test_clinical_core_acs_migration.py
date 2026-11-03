"""P2N-2: acs_70f_left_main as a cardiogenic shadow migration through the unchanged common core.

Repository truth read from the case bank; the arrival mapping declared, never approved; the arrival D independent of the
arrival lactate; the family writers (ischaemic pump on P, congestion on L, reperfusion as a logistic signal) and their
boundaries; the common core and the GI physiology unchanged.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
from dataclasses import replace

import pytest

from clinical_core import acs_migration as an
from clinical_core import acs_reference as ar
from clinical_core import blood_fluid_calibration as bf
from clinical_core import gas_exchange_architecture as go
from clinical_core import lung_water_reference as lw
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import vascular_tone as vt
from clinical_core.integration import step
from clinical_core.modules.acs_ischaemia import (CORONARY_REPERFUSION, CoronaryReperfusion, IschaemicCongestion,
                                                 IschaemicPump)
from clinical_core.state import CoreInvariantError, RhythmState

ROOT = an.ROOT
#: The P2N-2 freeze: the arrival mapping, the family writers, the common reference profile, the family region, the
#: counterfactuals, the criteria, the boundary rules and every clinical_core source but the downstream reports, committed
#: before the evaluation run.
FROZEN_DIGEST = "e7ff21e577cfadc3990ac9a27a3524d4e3bb80a7870d47e27dcc6e9420b7a718"


#: P2O-1 inserted its declared, inert names into derived.py and integration.py, proven byte for byte against the P2N-2
#: files (gas_exchange_architecture.proved): this package's guards read the P2N-2 core (go.p2n2_text, go.p2n2_sources,
#: go.p2n2_unchanged), never the live one; the record is unchanged.
#: P2O-3 replaced declared lines of derived.py, integration.py, state.py, modules/acs_ischaemia.py and two tuple
#: files, proven byte for byte against the P2O-1 files (lung_water_reference.proved): this package's guards read
#: the P2O-1 files through P2O-1's view of the P2N-2 core (lw.chain, lw.p2o1_sources); the record is unchanged.
_LIVE_SOURCES_P2O3 = bf.freeze_sources


def _LIVE_SOURCES_P2O1() -> dict:
    return lw.p2o1_sources(_LIVE_SOURCES_P2O3())


_UPSTREAM_P2N2 = an.upstream_unchanged


def _p2n2_upstream() -> dict:
    # P2O-1's analysis reads the ACS case for its post-freeze validation: an analysis module, never common
    # physiology; the common-core readers of the family stay what P2N-2 froze.
    up = _UPSTREAM_P2N2()
    return {**up, "core_readers_of_family": [r for r in up["core_readers_of_family"] if r not in go.OWN + lw.OWN]}


@pytest.fixture(autouse=True, scope="module")
def _p2n2_core():
    with pytest.MonkeyPatch.context() as patch:
        lw.chain(patch)
        patch.setattr(vt, "_live", go.p2n2_text)
        patch.setattr(bf, "freeze_sources", lambda: go.p2n2_sources(_LIVE_SOURCES_P2O1()))
        patch.setattr(an, "upstream_unchanged", _p2n2_upstream)
        yield


def _start():
    a, p = ar.anchors(), ar.common_profile()
    return dv.arrival_state(a, p), a, p


# The frozen package and its closure ---------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert set(an.OWN) <= set(sources) and an.REPORT not in sources
    assert an.REPORT in lactate_slice.DOWNSTREAM_REPORTS
    # The analysis and its report leave the P2G pack digest; the case mapping and the family writers stay in it.
    assert {an.OWN[2], an.REPORT} <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    assert not {an.OWN[0], an.OWN[1]} & set(decision_pack.PACK_DIGEST_EXCLUDED)
    assert hashlib.sha256(an.P2M2_RECORD.read_bytes()).hexdigest() == an.P2M2_RECORD_SHA
    if FROZEN_DIGEST is not None:
        assert an.freeze_digest() == FROZEN_DIGEST, "a source, a mapping or a definition changed after the freeze"


def test_the_p2m2_tree_is_byte_identical_and_the_common_core_never_reads_the_family():
    up = an.upstream_unchanged()
    assert up["unchanged"] and (up["digest"], up["files"]) == an.SOURCES_AT_P2M2 and not up["core_readers_of_family"]
    mapped = an.p2m2_sources(bf.freeze_sources())
    assert not set(an.OWN) & set(mapped)
    for relative, sha in an.TUPLE_AT_P2M2.items():
        assert mapped[relative] == sha
    original = vt._live
    try:
        vt._live = lambda relative: original(relative) + "\nX = 1\n"
        assert an.p2m2_sources(bf.freeze_sources())["clinical_core/decision_pack.py"] == \
            bf.freeze_sources()["clinical_core/decision_pack.py"]
    finally:
        vt._live = original


# Repository truth and the arrival mapping ------------------------------------------------------------------------------------

def test_the_truth_is_read_from_the_case_bank():
    t = ar.truth()
    assert (t["sbp"], t["dbp"], t["hr"], t["spo2"], t["respiratory_rate"], t["crt_s"]) == (104, 66, 112, 94, 26, 3)
    assert (t["lactate_mmol_l"], t["hb_g_dl"], t["glucose_mg_dl"], t["potassium_mmol_l"]) == (3.1, 12.2, 168, 4.1)
    # The repository's arterial bicarbonate is 18.0 (the brief's ~18.4 is not the case's).
    assert (t["abg_ph"], t["abg_paco2"], t["abg_pao2"], t["abg_hco3"], t["abg_fio2_percent"]) == (7.36, 33, 72, 18.0, 21)
    assert t["troponin_ng_l"] == 260 and t["ecg_profile"] == "diffuse_st_depression_avr"
    assert t["coronary"]["territory"] == "left_main" and t["coronary"]["symptom_onset_min"] == 60
    assert t["mental_status"] == "Alert" and t["rhythm"] == "Sinus tachycardia"
    assert ar.authored_map(t) == pytest.approx(78.6667, abs=1e-4)


def test_the_arrival_is_authored_exactly_and_every_candidate_is_declared_not_approved():
    a, t = ar.anchors(), ar.truth()
    assert (a.sbp, a.dbp, a.hr, a.spo2, a.lactate, a.hb, a.k, a.fio2) == (104, 66, 112, 94, 3.1, 12.2, 4.1, 0.21)
    assert a.arrival_bicarbonate == t["abg_hco3"] and a.arrival_paco2 == t["abg_paco2"]
    assert set(a.declared.values()) == {"synthetic_probe"}
    assert set(a.declared) == {"arrival_lactate_excess", "intrinsic_sinus_rate", "arrival_oxygen_debt",
                               "arrival_delivery_ratio", "pump_reserve"}
    assert a.preload_fraction is None and a.beta_blockade == 0.0 and a.metabolic_demand_baseline == 1.0
    assert all(v.classification in (ar.CASE_MAPPING, ar.FAMILY_CANDIDATE) for v in ar.bands().values())
    assert "FACULTY_APPROVED" not in json.dumps(ar.ARRIVAL_CLASSES)


def test_the_arrival_d_never_follows_the_arrival_lactate():
    # Faculty rule (P2N-2): arrival D is a latent arrival-state variable; there is no lactate -> D rule.
    base = ar.anchors()
    p = ar.common_profile()
    for lactate in (1.0, base.lactate, 6.2, 12.0):
        other = replace(base, lactate=lactate, arrival_lactate_excess=min(base.arrival_lactate_excess, lactate))
        assert dv.arrival_state(other, p).D == dv.arrival_state(base, p).D == ar.arrival_oxygen_debt()
    assert "lactate" not in ar.arrival_oxygen_debt.__code__.co_varnames
    assert an.lactate_does_not_set_d()["pass"]


def test_the_common_reference_values_equal_their_closed_sources():
    # acs_reference stays in the P2G pack digest and may not import the excluded analysis modules: its numbers are
    # written with their source and must equal it exactly.
    from clinical_core import acid_base as ab
    from clinical_core import baroreflex as br
    from clinical_core import lactate_closure as lc
    ref = ar.COMMON_REFERENCE
    assert ar.RESERVE == vt.RESERVE and ar.INTRINSIC_RR == ab.INTRINSIC_RR[1]
    assert ref["deficit_to_tone_gain"][0] == br.TONE_GAINS[1] and tuple(ar.TONE_SENSITIVITY) == tuple(br.TONE_GAINS)
    assert ref["afterload_sensitivity"][0] == br.AFTERLOAD and ref["baroreflex_map_set_mmhg"][0] == br.MAP_SETS[1]
    assert (ref["acute_deficit_to_sympathetic_gain"][0], ref["debt_to_sympathetic_gain"][0],
            ref["baroreflex_to_sympathetic_gain"][0]) == (br.PROBE_GAINS["acute"], br.PROBE_GAINS["debt"],
                                                          br.PROBE_GAINS["baro"])
    assert ref["debt_to_lactate_gain"][0] == lc.K_LD[2]
    assert ref["acid"][0] == (ab.DRIVE_GAINS[2], ab.STEADY_BURDENS[1], ab.ACID_TAUS[1])
    gain, b, tau = ref["acid"][0]
    expected = ab.candidate_profile(gain, b, tau, base=replace(dv.DEFAULT_PROFILE, **{
        k: v for k, (v, _) in ref.items() if k != "acid"}))
    assert ar.common_profile() == expected


def test_the_common_reference_is_one_predeclared_point_of_the_gi_carried_uncertainty():
    p = ar.common_profile()
    for name, (value, why) in ar.COMMON_REFERENCE.items():
        if name != "acid":
            assert getattr(p, name) == value and why
    assert p.collapse_output_threshold is None and p.collapse_burden_limit is None
    assert tuple(ar.TONE_SENSITIVITY) == (0.25, 0.5, 1.0)


# The family writers ------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("args", [(-0.001, 0.5, 0.5, 30.0), (0.001, 0.0, 0.5, 30.0), (0.001, 1.2, 0.5, 30.0),
                                  (0.001, 0.5, 1.5, 30.0), (0.001, 0.5, 0.5, 0.0), (math.inf, 0.5, 0.5, 30.0)])
def test_the_ischaemic_pump_refuses_incoherent_declarations(args):
    with pytest.raises(CoreInvariantError):
        IschaemicPump("x", *args)


def test_the_ischaemic_pump_lowers_only_p_to_its_floor_and_reperfusion_stops_it():
    s, a, p = _start()
    pump = IschaemicPump("acs-pump", 0.01, 0.9, 0.5, 30.0)
    states, records = an.course((pump,), 30, a, p, s)
    ps = [x.P for x in states]
    assert all(b <= c for c, b in zip(ps, ps[1:])) and min(ps) == pytest.approx(0.9)
    assert {d.channel.value for r in records for d in r.deltas if d.source.id == "acs-pump"} == {"P"}
    reperfused, recs = an.course((IschaemicPump("acs-pump", 0.01, 0.5, 0.5, 30.0),
                                  CoronaryReperfusion("acs-pci", 10)), 60, a, p, s)
    at = reperfused[10].P
    assert all(x.P >= at - 1e-15 for x in reperfused[10:]) and max(x.P for x in reperfused) <= 1.0
    assert reperfused[-1].P > at and reperfused[-1].P < at + 0.5 * (1.0 - at) + 1e-12


def test_the_congestion_writer_adds_only_l_in_proportion_to_the_pump_shortfall():
    s, a, p = _start()
    gain = dv.DEFAULT_PROFILE.congestion_per_excess_preload
    item = IschaemicCongestion("acs-congestion", gain)
    assert not item.contribute(s, 1, (), a, p).deltas                          # P = 1: no shortfall, nothing added
    weak = s.evolve(P=0.8)
    (delta,) = item.contribute(weak, 1, (), a, p).deltas
    assert delta.channel.value == "L" and delta.amount == pytest.approx(gain * 0.2)


def test_the_reperfusion_is_a_logistic_signal_that_writes_nothing():
    pci = CoronaryReperfusion("acs-pci", 5)
    assert pci.signals(4) == () and pci.signals(5)[0].name == CORONARY_REPERFUSION
    s, a, p = _start()
    assert not pci.contribute(s, 5, (), a, p).deltas
    with pytest.raises(CoreInvariantError):
        CoronaryReperfusion("acs-pci", 0)


def test_no_family_writer_acts_without_a_pulse():
    s, a, p = _start()
    arrest = s.evolve(R=RhythmState.vf(), terminal_since=0, P=0.8)
    for item in (IschaemicPump("acs-pump", 0.01, 0.5, 0.5, 30.0), IschaemicCongestion("acs-congestion", 0.05)):
        assert not item.contribute(arrest, 1, (), a, p).deltas


def test_the_family_boundary_holds_in_the_code():
    b = an.boundary()
    assert b["pass"] and b["writer_channels"] == ["L", "P"] and not b["writer_never_names"]
    assert not b["writer_other_writes"] and not b["common_files_name_acs"]
    for name in an.COMMON_FILES:
        tree = ast.parse((ROOT / "clinical_core" / name).read_text(encoding="utf-8"))
        imported = {a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names} | {
            n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        assert not any("acs" in m for m in imported), name


def test_a_planted_family_write_of_an_observable_is_caught(monkeypatch, tmp_path):
    core = tmp_path / "clinical_core"
    (core / "modules").mkdir(parents=True)
    text = (ROOT / "clinical_core" / "modules" / "acs_ischaemia.py").read_text(encoding="utf-8")
    (core / "modules" / "acs_ischaemia.py").write_text(text + "\n\ndef _planted(d):\n    return Channel.T, d.map\n",
                                                       encoding="utf-8")
    for name in an.COMMON_FILES:
        (core / name).write_text((ROOT / "clinical_core" / name).read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(an, "CORE_DIR", core)
    b = an.boundary()
    assert not b["pass"] and "T" in b["writer_channels"] and b["writer_never_names"] == ["map"]


# GI non-regression, collapse inactive, verdict machinery --------------------------------------------------------------------------

def test_the_gi_physiology_is_unchanged_with_inert_acs_writers():
    out = an.gi_nonregression(60)
    assert out["identical"] and out["inert_writes"] == 0


def test_collapse_is_read_structurally_and_never_acts():
    c = an.collapse_compatibility()
    assert c["max_holds"] and c["unset_is_lower_bound"] and c["no_family_rule"]
    assert not c["active"] and not c["thresholds_selected"] and not c["terminal_transition"]
    assert c["m1"] == "REQUIRED_BEFORE_ACTIVE_FAMILY_COLLAPSE" and c["m2"] == "REQUIRED_BEFORE_RUNTIME_TRACE_INTEGRATION"


def test_a_failing_criterion_names_the_blocker():
    out = an.verdict({name: True for name in an.CRITERIA} | {"gi_unchanged": False})
    assert out["verdict"] == f"{an.NOT_READY} — gi_unchanged" and out["failing"] == ["gi_unchanged"]


def test_a_changed_upstream_file_stops_before_any_probe(monkeypatch):
    monkeypatch.setattr(an, "upstream_unchanged", lambda: {"unchanged": False, "core_readers_of_family": []})
    out = an.run()
    assert "stopped" in out and out["verdict"]["verdict"].startswith(an.NOT_READY) and "arrival" not in out


# The committed record and its document -------------------------------------------------------------------------------------------

RECORD = ROOT / "docs" / "revision" / "P2N2_acs_migration.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2N2_MIGRACION_CARDIOGENICA_ACS.md"


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def result():
    return an.run()


def test_the_record_comes_from_the_frozen_package_and_is_reproduced_live(record, result):
    assert record["freeze_digest"] == FROZEN_DIGEST and "stopped" not in record
    assert record["design"] == _json(an.design())
    # P2O-3 gave the anchors one candidate input (reversible_lung_water), 0 at this arrival: the frozen record predates
    # the field, so it is removed (and checked neutral) before the comparison; nothing else moves.
    live = _json(result)
    assert live["arrival"]["anchors"].pop("reversible_lung_water") == 0.0
    for key in ("upstream", "arrival", "lactate_d", "pump", "untreated", "reperfusion", "fluid", "collapse", "boundary",
                "gi", "legacy", "legacy_comparison", "verdict", "recommendation", "decisions", "efficiency"):
        assert record[key] == live[key], key


def test_the_record_states_the_verdict_and_the_recommendation(record):
    assert record["verdict"]["verdict"] == an.READY and record["verdict"]["failing"] == []
    assert record["recommendation"] == "IMPLEMENT_EXPECTED_RESPIRATORY_EXTENSION"
    u = record["untreated"]
    assert all(r["first"]["spo2"] == r["last"]["spo2"] for r in u["region"].values())     # no L -> SpO2 path
    assert record["collapse"]["active"] is False and record["legacy_comparison"]["used_for_parameters"] is False


def test_the_document_is_generated_from_the_record(record):
    from clinical_core import acs_migration_report as rep
    document = DOCUMENT.read_text(encoding="utf-8")
    for name, render in rep.RENDERERS.items():
        assert rep.apply(document, name, render(record)) == document, name
    assert an.READY in document and "IMPLEMENT_EXPECTED_RESPIRATORY_EXTENSION" in document
    for placeholder in ("SUMMARY_TEXT", "LIMITS_TEXT", "REVIEW_TEXT", "FREEZE_COMMIT", "FREEZE_DIGEST"):
        assert placeholder not in document


# The adversarial review (P2N-2), pinned on the frozen package -------------------------------------------------------------
# The review ran once on the freeze and the evaluation. These tests give the weak criteria a non-vacuous check on the frozen
# outputs and pin what the review found, without touching the frozen modules (no refreeze): docs/revision/
# P2N2_MIGRACION_CARDIOGENICA_ACS.md §19.

def test_review_the_untreated_fall_is_the_writers_and_not_the_arrival_debt(record):
    # Without writers the arrival debt still accumulates (D_up holds with no ischaemia at all); with them every
    # downstream direction is strictly worse than the writer-free course.
    s, a, p = _start()
    bare, _ = an.course((), an.HORIZON, a, p, s)
    first, last = an.row(bare[0], a, p), an.row(bare[-1], a, p)
    assert (last["P"], last["L"], last["output_rel"]) == (1.0, 0.0, 1.0) and last["map"] == pytest.approx(first["map"])
    assert last["D"] > first["D"]
    ref = record["reperfusion"]["ongoing"]
    assert ref["P"] < last["P"] and ref["output_rel"] < last["output_rel"] and ref["map"] < last["map"]
    assert ref["delivery_index"] < last["delivery_index"] and ref["deficit"] > last["deficit"]
    assert ref["D"] > last["D"] and ref["L"] > last["L"]


def test_review_reperfusion_improves_p_strictly_and_in_the_order_of_the_declared_share(record):
    # The frozen criterion compares with >=, so a reperfusion that changed nothing would pass it; the frozen outputs
    # pass the strict comparison, ordered by the declared recovery share, and every downstream reading follows.
    rp = record["reperfusion"]
    shares = [rp["shares"][str(float(share))] for share in an.RECOVERY_SHARES]
    assert rp["ongoing"]["P"] < shares[0]["P"] < shares[1]["P"] < shares[2]["P"] <= 1.0
    for row in shares:
        assert row["map"] > rp["ongoing"]["map"] and row["deficit"] < rp["ongoing"]["deficit"]
        assert row["D"] < rp["ongoing"]["D"] and row["writes"] == {"channels": ["L", "P"], "other_writes": 0}


def test_review_the_arrival_d_does_not_follow_the_authored_lactate_through_the_mapping(monkeypatch):
    # The permanent guard moves the lactate of finished anchors; this one moves the authored lactate the mapping reads,
    # and shows that the same check catches a planted lactate -> D rule in the mapping.
    base, authored = ar.anchors(), ar.truth()
    monkeypatch.setattr(ar, "truth", lambda: {**authored, "lactate_mmol_l": 2.0 * authored["lactate_mmol_l"]})
    moved = ar.anchors()
    assert moved.lactate == 2.0 * base.lactate and moved.arrival_oxygen_debt == base.arrival_oxygen_debt
    monkeypatch.setattr(ar, "arrival_oxygen_debt", lambda point="midpoint": 5.0 * ar.truth()["lactate_mmol_l"])
    assert ar.anchors().arrival_oxygen_debt != base.arrival_oxygen_debt


def test_review_the_arrival_impairment_counts_once_and_the_pump_reserve_reaches_no_course_run():
    # Declared limitation (faculty decision): the arrival LV impairment acts through the arrival delivery ratio only.
    # pump_reserve enters the congestion shortfall alone, above the common preload knee, and no course this package
    # runs gets there: not the untreated region, not 4000 mL on the weak pump.
    p = ar.common_profile()
    courses = []
    for reserve in (0.3, 1.0):
        a = ar.anchors(pump_reserve=reserve)
        arrival = an.row(dv.arrival_state(a, p), a, p)
        assert arrival["output_rel"] == 1.0
        assert arrival["deficit"] == pytest.approx(1.0 - a.arrival_delivery_ratio * ar.RESERVE)
        states, _ = an.course(an.writers(), an.HORIZON, a, p)
        courses.append([an.row(x, a, p) for x in states])
    assert courses[0] == courses[1]
    a = ar.anchors(pump_reserve=0.3)
    weak = dv.arrival_state(a, p).evolve(P=an.FLUID["pump_failure_P"])
    bag = replace(an._bag(), volume_ml=4000.0, untimed_rate_ml_per_min=4000.0 / an.FLUID["duration_min"])
    wet, _ = an.course((bag,), an.FLUID["read_minute"], a, p, weak)
    assert dv.preload_position(wet[-1], a, p) < p.congestion_preload_knee and wet[-1].L == 0.0


def test_review_the_authored_arrival_hr_lies_just_above_the_intrinsic_band_alone():
    # The frozen "intrinsic band" row moved every band to the same point; the intrinsic rate alone spans 71.9 / 91.8 /
    # 111.8 and does not reach the authored 112: a faculty decision, never an ACS residual.
    p, b = ar.common_profile(), ar.bands()["intrinsic_sinus_rate"]
    hr = {}
    for point in ("lower", "midpoint", "upper"):
        a = ar.anchors(intrinsic_sinus_rate=getattr(b, point))
        hr[point] = an.row(dv.arrival_state(a, p), a, p)["hr"]
    assert hr["lower"] < hr["midpoint"] < hr["upper"] < float(ar.truth()["hr"]) < hr["upper"] + 1.0


def test_review_the_weak_pump_gains_less_than_a_normal_pump_at_the_same_neutral_preload(record):
    # The frozen comparison is confounded by preload (the preload-deficient arm sits low on the curve); the matched
    # control, the arrival pump at the same neutral preload, still gains more than the weak pump.
    s, a, p = _start()
    minute = an.FLUID["read_minute"]
    dry, _ = an.course((), minute, a, p, s)
    wet, _ = an.course((an._bag(),), minute, a, p, s)
    normal = an.row(wet[-1], a, p)["output_rel"] - an.row(dry[-1], a, p)["output_rel"]
    fl = record["fluid"]
    assert fl["pump_failure"]["output_gain"] < normal < fl["preload_deficiency"]["output_gain"]


def test_review_known_limitation_a_pump_with_no_loss_still_records_its_start():
    # Declared (no runtime reader, Trace integration is M2): the start event fires even when the declared loss is 0.
    s, a, p = _start()
    states, records = an.course((IschaemicPump("acs-pump", 0.0, 0.5, 0.5, 30.0),), 3, a, p, s)
    assert {x.P for x in states} == {1.0}
    assert [e.kind for r in records for e in r.events] == ["ischaemic_pump_loss"]


def test_review_the_channels_that_move_in_the_reference_course(record):
    # CHANNEL_ROLES are the brief's expectations; the reference course shows which hold: P and L written by the family,
    # T and D moved by the common core, V, R, G, W and N unchanged (G and W carry no role until the respiratory extension).
    region = record["untreated"]["region"][min(record["untreated"]["region"], key=lambda k: abs(float(k) - 0.1 / 60))]
    first, last = region["first"], region["last"]
    moved = {c for c in ("V", "T", "P", "R", "L", "G", "W", "D", "N") if first[c] != last[c]}
    assert moved == {"T", "P", "L", "D"}
    assert set(ar.CHANNEL_ROLES) == {"V", "T", "P", "R", "L", "G", "W", "D", "N"}


def test_review_every_common_reference_value_equals_its_source():
    from clinical_core import blood_anchors as ba
    from clinical_core import calibration
    from clinical_core import hr_primary as hp
    ref = ar.COMMON_REFERENCE
    assert ref["sympathetic_per_pressure_deficit"][0] == hp.PRIMARY_HR_CALIBRATION["sympathetic_per_pressure_deficit"]
    assert ref["debt_clearance_tau_min"][0] == ba.KINETICS["debt_clearance_tau_min"]
    assert ref["lactate_clearance_tau_min"][0] == ba.KINETICS["lactate_clearance_tau_min"]
    for name in ("debt_clearance_tau_min", "debt_per_delivery_deficit", "lactate_clearance_tau_min"):
        points = tuple(calibration.REGISTRY[name].points())
        assert ref[name][0] == points[len(points) // 2]
