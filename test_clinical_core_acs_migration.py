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
