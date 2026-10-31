"""Phase 2 shadow core, P2K-3: effective ventilation decoupled from RR, and the respiratory decision surface.

These tests pin the candidate's ventilation mapping (capacity = efficiency x (1 + gain x burden), W = capacity / demand
ratio, PaCO2 = 40 / W), the structural invariants the faculty made critical (RR alone and the intrinsic RR alone move no W
and no PaCO2; lactate and D reach no RR or W term), the probes A-I, the frozen supports and tolerances, pH derived and
never a filter, the factorized algebra against the module on core states, the untouched core files, the closure maps the
closed packages rest on, and the policy: nothing approved, no legacy read.
"""
import ast
import hashlib
import inspect
import json
import math
from dataclasses import replace

import pytest

from clinical_core import acid_base as ab
from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import vascular_tone as vt
from clinical_core import ventilation as vn
from clinical_core import ventilation_surface as vs
from clinical_core.derived import DEFAULT_PROFILE, arrival_state, derive
from clinical_core.state import CoreInvariantError, FrozenRecord, UnresolvedBoundary

ROOT = vs.ROOT
SOURCE = ROOT / "clinical_core" / "ventilation_surface.py"
#: The P2K-3 freeze: the faculty decisions, the semantics, the supports, references and tolerances, the probes, the
#: factorization, the identifiability, decision-pack and verdict rules and every clinical_core source but the downstream
#: reports, committed before any arrival count or clinical trajectory was read.
FROZEN_DIGEST = "38e30b846a6647e9b759a06952322930eb22e62de8f521a86909055686b919da"
C57, C72 = vs.C57, vs.C72


@pytest.fixture(scope="module")
def probes():
    return vs.probes()


def _state(burden, anchors=vs.PROBE_ANCHORS, profile=vs.PROBE_PROFILE, **changes):
    return vs._probe_state(burden, anchors=anchors, profile=profile, **changes)


def _w(state, anchors=vs.PROBE_ANCHORS, profile=vs.PROBE_PROFILE, gain=0.05):
    return vn.ventilated_respiration(state, anchors, profile, vn.VentilationCandidate(gain))


# The frozen package ---------------------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert set(vs.OWN) <= set(sources) and vs.REPORT not in sources
    assert vs.REPORT in lactate_slice.DOWNSTREAM_REPORTS
    assert {"clinical_core/ventilation_surface.py", vs.REPORT} <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    # The physiology module is a core source of the pack (a future integration may import it from a hashed module).
    assert "clinical_core/ventilation.py" not in decision_pack.PACK_DIGEST_EXCLUDED
    # The closed P2K-2 record it builds on (its frozen digest, test_clinical_core_acid_base.FROZEN_DIGEST).
    assert vs.p2k2_record()["freeze_digest"] == vs.P2K2_DIGEST == \
        "7540ee76a681d272e8ac290781771d83d19c1562ea152209c88809aa4e8b710c"
    if FROZEN_DIGEST is not None:
        assert vs.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a support changed after the freeze"


def test_the_core_files_are_untouched_by_p2k3():
    """No core file changes: derived, integration, state and the P2K-2 module keep their P2K-2 (cbec249) bytes, so every
    default run, the golden and every closed record are unchanged by construction."""
    assert all(vs.core_unchanged().values())
    for path in (ROOT / "clinical_core").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {alias.name for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
                    for alias in node.names} | {node.module or "" for node in ast.walk(tree)
                                                if isinstance(node, ast.ImportFrom)}
        if "ventilation" in imported:
            assert path.name in ("ventilation_surface.py", "ventilation_surface_report.py"), path.name


def test_the_faculty_decisions_and_the_carried_uncertainty_are_recorded():
    assert vs.FACULTY["decided"] == vs.DECIDED == "2026-10-31" and vs.REVISION == "P2K-3"
    for key in ("issue", "shared_driver", "mapping", "efficiency", "paco2", "ventilation_gain", "rr", "acid",
                "arrival_paco2", "arrival_rr", "arrival_ph", "upstream", "support", "non_regression", "scope"):
        assert vs.FACULTY[key]
    assert "FREQUENCY_TO_VENTILATION_OVERCONSTRAINT" in vs.FACULTY["issue"]
    assert vs.CARRIED == ab.CARRIED
    assert vs.STATUS["approved"] == "none FACULTY_APPROVED" and vs.STATUS["tidal_volume"] == "IMPLICIT"
    assert vs.FUTURE_RESPIRATORY_GENERALIZATION["status"].startswith("FUTURE_RESPIRATORY_GENERALIZATION")


# The mapping ------------------------------------------------------------------------------------------------------------------

def test_the_mapping_is_the_faculty_one():
    for burden in (0.0, 4.2, 6.7, 12.0):
        for gain in vs.VENTILATION_GAINS:
            for efficiency in (1.0, 0.7):
                capacity = vn.ventilatory_capacity(burden, efficiency, gain)
                assert capacity == efficiency * (1.0 + gain * burden)
                for ratio in (1.0, 1.1, 0.8):
                    w = vn.effective_ventilation(capacity, ratio)
                    assert w == capacity / ratio
                    assert vn.paco2_from_ventilation(w, 40.0) == 40.0 / w
                    assert math.isclose(40.0 / w, 40.0 * ratio / capacity)
    assert inspect.signature(vn.ventilatory_capacity).parameters.keys() == {"burden", "efficiency", "gain"}
    assert inspect.signature(vn.effective_ventilation).parameters.keys() == {"capacity", "demand_ratio"}


def test_the_ventilation_gain_is_validated():
    for bad in (-0.01, math.inf, math.nan, True, "0.05"):
        with pytest.raises(CoreInvariantError):
            vn.VentilationCandidate(bad)
    assert vn.VentilationCandidate(0.0).acid_to_ventilation_gain == 0.0


def test_the_w_side_reads_no_rate_intrinsic_rate_drive_lactate_or_d():
    proof = vs.w_inputs()
    assert proof["leaks"] == []
    assert sorted(proof["targets_found"]) == sorted(vs.W_TARGETS)
    assert {"rate", "respiratory_rate", "intrinsic", "acid_to_drive_gain", "lactate", "D"} <= vs.W_FORBIDDEN


def test_rr_alone_changes_no_w_or_paco2():
    """P2K-3-1: with the burden, the demand and the efficiency fixed, changing RR (through the drive gain, the
    saturation or the rate guard) moves neither W nor PaCO2."""
    state = _state(8.0)
    ref = _w(state)
    for changes in ({"acid_to_drive_gain": 1.0}, {"acid_to_drive_gain": 4.0}, {"rr_drive_saturation": 10.0},
                    {"rr_max": 20.0}):
        profile = replace(vs.PROBE_PROFILE, **changes)
        other = _w(state, profile=profile)
        assert other.respiratory_rate != ref.respiratory_rate
        assert (other.ventilation, other.paco2, other.ph, other.capacity) == (ref.ventilation, ref.paco2, ref.ph,
                                                                              ref.capacity)


def test_intrinsic_rr_alone_changes_no_w_or_paco2():
    state = _state(8.0)
    seen = set()
    for intrinsic in (8.0, 12.0, 16.0, 20.0, 30.0):
        anchors = replace(vs.PROBE_ANCHORS, intrinsic_respiratory_rate=intrinsic)
        r = _w(state, anchors=anchors)
        seen.add((r.ventilation, r.paco2, r.ph))
        assert r.intrinsic_rr == intrinsic and r.frequency_drive == r.respiratory_rate - intrinsic
    assert len(seen) == 1


def test_no_burden_at_the_baseline_demand_is_eucapnia_at_every_intrinsic_rr():
    for intrinsic in vs.INTRINSIC_RR:
        anchors = replace(vs.PROBE_ANCHORS, intrinsic_respiratory_rate=intrinsic)
        for gain in vs.VENTILATION_GAINS:
            r = _w(_state(0.0, anchors=anchors), anchors=anchors, gain=gain)
            assert r.ventilation == 1.0 and r.paco2 == vs.PACO2_REFERENCE == 40.0
            assert r.respiratory_rate == intrinsic


def test_the_demand_is_relative_to_the_patients_baseline():
    """W = 1 at the patient's baseline demand whatever the demand class; a demand above the baseline lowers W."""
    for baseline in (1.0, 1.1):
        anchors = replace(vs.PROBE_ANCHORS, metabolic_demand_baseline=baseline,
                          declared=FrozenRecord({**vs.PROBE_ANCHORS.declared, "metabolic_demand_baseline": "synthetic_probe"}))
        state = _state(0.0, anchors=anchors)
        assert state.aux.oxygen_demand == baseline
        r = _w(state, anchors=anchors)
        assert r.demand_ratio == 1.0 and r.ventilation == 1.0 and r.paco2 == 40.0
        up = _w(_state(0.0, anchors=anchors, oxygen_demand=1.2 * baseline), anchors=anchors)
        assert up.ventilation < 1.0 and up.paco2 > 40.0
    assert "BASELINE_RELATIVE" in vs.SEMANTICS["demand"] and vn.STATUS["demand"].endswith("(BASELINE_RELATIVE)")


def test_without_a_pulse_there_is_no_breathing_and_no_paco2():
    from clinical_core.state import RhythmState
    state = _state(8.0).evolve(R=RhythmState.asystole(), terminal_since=0)
    r = _w(state)
    assert r.respiratory_rate == 0.0 and r.frequency_drive == 0.0 and r.ventilation == 0.0
    assert r.paco2 is None and r.ph is None


def test_no_bicarbonate_left_stops_the_candidate_as_in_p2k2():
    with pytest.raises(UnresolvedBoundary):
        _w(_state(24.0))


def test_the_candidate_needs_the_acid_base_physiology():
    state = arrival_state(vs.PROBE_ANCHORS, DEFAULT_PROFILE)
    with pytest.raises(CoreInvariantError):
        vn.ventilated_respiration(state, vs.PROBE_ANCHORS, DEFAULT_PROFILE, vn.VentilationCandidate(0.05))


# Probes A-I -----------------------------------------------------------------------------------------------------------------

def test_every_structural_probe_passes(probes):
    assert vs.probes_pass(probes) == {name: True for name in vs.probes_pass(probes)}
    assert set(vs.probes_pass(probes)) >= set("ABCDEFGHI")


def test_probe_a_rr_and_w_rise_by_their_own_gains(probes):
    a = probes["A"]
    assert a["rr_by_frequency_gain"] and a["w_by_ventilation_gain"]
    assert a["result"]["recruitment"] == 1.0 + vs.PROBE_GAIN * 8.0


def test_probes_e_f_lactate_and_d_reach_no_rr_or_w(probes):
    assert probes["E"]["lactate_raised"] and probes["E"]["unchanged"]
    assert probes["F"]["d_raised"] and probes["F"]["unchanged"]
    assert probes["W_channel"]["unchanged"]


def test_probe_g_a_low_efficiency_is_hypercapnia_despite_tachypnoea(probes):
    g = probes["G"]
    assert g["efficiency_0.5"]["rr"] == g["efficiency_1"]["rr"] > dv.intrinsic_respiratory_rate(vs.PROBE_ANCHORS) + 10.0
    assert g["efficiency_0.5"]["w"] < 1.0 < g["efficiency_1"]["w"] and g["hypercapnic_despite_tachypnoea"]
    assert g["course_rr_rises"] and g["course_paco2_rises"]


def test_probe_i_demand_lowers_w_unless_recruitment_compensates(probes):
    i = probes["I"]
    assert i["w_falls"] and i["paco2_rises"] and i["rr_unchanged"] and i["recruitment_compensates"]
    assert i["compensating_burden"] > 8.0


# Supports, tolerances, pH ---------------------------------------------------------------------------------------------------

def test_the_supports_and_tolerances_are_the_frozen_ones():
    assert vs.VENTILATION_GAINS == (0.03, 0.04, 0.05, 0.06, 0.08)
    assert vs.INTRINSIC_RR is ab.INTRINSIC_RR and vs.DRIVE_GAINS is ab.DRIVE_GAINS
    assert vs.STEADY_BURDENS is ab.STEADY_BURDENS and vs.ACID_TAUS is ab.ACID_TAUS and vs.SATURATION == 25.0
    assert vs.PACO2_REFERENCE == 40.0 and vs.HCO3_REFERENCE == 24.0 and vs.EFFICIENCY == 1.0
    assert vs.RR_TOLERANCE == 3.0 == vs.PACO2_TOLERANCE and vs.PH_TOLERANCE == 0.03
    for case in vs.CASES:
        paco2 = ab.authored_gas(case)["paco2"]
        assert vs.PACO2_WINDOWS[case] == (paco2 - vs.PACO2_TOLERANCE, paco2 + vs.PACO2_TOLERANCE)
    assert vs.PACO2_WINDOWS == {C57: (28.0, 34.0), C72: (30.0, 36.0)} and vs.AUTHORED_RR == {C57: 26.0, C72: 24.0}
    exact = vs.exact_ventilation_gains()
    for case, stated in vs.FACULTY_IMPLIED_GAINS.items():
        assert abs(exact[case] - stated) < 0.001


def test_ph_is_derived_and_only_diagnostic():
    for gain in vs.VENTILATION_GAINS:
        for case in vs.CASES:
            assert vs.predicted_ph(gain, case) == dv.carbonic_ph(ab.authored_gas(case)["hco3"],
                                                                 vs.predicted_paco2(gain, case))
    assert vs.ph_class(0.03) == "PH_CONSISTENT" and vs.ph_class(-0.0301) == "PH_INCONSISTENT"
    source = inspect.getsource(vs.paco2_compatibility)
    assert "ok = {case: PACO2_WINDOWS[case][0] <= paco2[case] <= PACO2_WINDOWS[case][1]" in source
    assert "if all(ok.values()):" in source


def test_the_arrival_paco2_is_predicted_never_anchored():
    anchors = replace(vs.PROBE_ANCHORS, arrival_paco2=55.0)
    r = _w(arrival_state(anchors, vs.PROBE_PROFILE), anchors=anchors)
    assert r.paco2 == 40.0 / (1.0 + 0.05 * dv.arrival_acid_burden(anchors, vs.PROBE_PROFILE))


# Factorization ---------------------------------------------------------------------------------------------------------------

def test_the_factorized_algebra_equals_the_module_on_core_states():
    anchors = replace(vt.tone_anchors(C57, "midpoint", 1.0), arrival_bicarbonate=ab.authored_gas(C57)["hco3"],
                      arrival_paco2=ab.authored_gas(C57)["paco2"], intrinsic_respiratory_rate=16.0)
    profile = ab.candidate_profile(2.0, 19.4, 120.0, base=replace(DEFAULT_PROFILE, oxygen_extraction_reserve=ab.RESERVE))
    state = arrival_state(anchors, profile)
    for burden in (0.0, ab.arrival_burden(C57), 9.0, 15.0):
        for gain in vs.VENTILATION_GAINS:
            s = state.evolve(aux=replace(state.aux, metabolic_acid_burden=burden))
            r = vn.ventilated_respiration(s, anchors, profile, vn.VentilationCandidate(gain))
            f = vs._gas_at(burden, 2.0, 16.0, gain, C57)
            for got, want in ((r.respiratory_rate, f["rr"]), (r.ventilation, f["w"]), (r.paco2, f["paco2"]),
                              (r.ph, f["ph"]), (r.bicarbonate, f["hco3"]), (r.recruitment, f["recruitment"]),
                              (r.frequency_drive, f["frequency_drive"])):
                assert abs(got - want) <= 1e-12
            assert derive(s, anchors, profile).respiratory_rate == r.respiratory_rate


def test_each_observable_is_read_over_the_factors_it_depends_on():
    assert set(vs.RR_FACTORS) == set(vs.SENSITIVITY_FACTORS) - {"ventilation_gain"}
    assert set(vs.GAS_FACTORS) == set(vs.SENSITIVITY_FACTORS) - {"intrinsic_rr", "drive_gain"}
    pack = vs._Pack()
    pack.add("A x", 1.0, {"intrinsic_rr": "12", "drive_gain": "2"})
    summary = pack.summary("A x")
    assert summary["ventilation_gain"] == {"path": "NONE", "range": 0.0}


def test_each_upstream_domain_is_compared_on_its_own_rows_and_states():
    """P2K-3-14's domains (BloodState, output, pressure / tone, delivery / deficit, D, lactate, HR / baroreflex): a change
    in one is seen by that domain only."""
    assert set(vs.UPSTREAM_DOMAINS) == {"blood_state", "output", "pressure_tone", "delivery_deficit", "D", "lactate",
                                        "hr_baroreflex"}
    state = arrival_state(vs.PROBE_ANCHORS, vs.PROBE_PROFILE)
    keys = {k for rows, _ in vs.UPSTREAM_DOMAINS.values() for k in rows}
    row = {k: 1.0 for k in keys}
    plain = {"rows": [dict(row)], "states": [state]}
    for domain, (rows, fields) in vs.UPSTREAM_DOMAINS.items():
        assert vs._domain_equal(plain, {"rows": [dict(row)], "states": [state]}, rows, fields)
        changed = {"rows": [{**row, rows[0]: 2.0}], "states": [state]}
        assert {name for name, (r, f) in vs.UPSTREAM_DOMAINS.items() if not vs._domain_equal(plain, changed, r, f)} \
            == {name for name, (r, _) in vs.UPSTREAM_DOMAINS.items() if rows[0] in r}
    moved = {"rows": [dict(row)], "states": [state.evolve(D=state.D + 1.0)]}
    assert not vs._domain_equal(plain, moved, *vs.UPSTREAM_DOMAINS["D"])
    assert vs._domain_equal(plain, moved, *vs.UPSTREAM_DOMAINS["lactate"])


# Closure ---------------------------------------------------------------------------------------------------------------------

def test_the_closed_packages_see_p2k2s_sources():
    sources = bf.freeze_sources()
    mapped = vs.p2k2_sources(sources)
    assert not set(vs.OWN) & set(mapped)
    for relative, sha in vs.TUPLE_AT_P2K2.items():
        assert mapped[relative] == sha
    for relative, sha in vs.CORE_AT_P2K2.items():
        assert mapped[relative] == sha
    for name, values in (("DOWNSTREAM_REPORTS", lactate_slice.DOWNSTREAM_REPORTS),
                         ("PACK_DIGEST_EXCLUDED", decision_pack.PACK_DIGEST_EXCLUDED)):
        assert set(vs.TUPLES_ADDED[name]) <= set(values)
    # A tuple file changed outside its tuple is not mapped.
    original = vt._live
    try:
        vt._live = lambda relative: original(relative) + "\nX = 1\n"
        assert vs.p2k2_sources(sources)["clinical_core/lactate_slice.py"] == sources["clinical_core/lactate_slice.py"]
    finally:
        vt._live = original


# Policy ----------------------------------------------------------------------------------------------------------------------

def test_the_verdict_rule_is_the_faculty_list_and_never_forces_the_burden_up():
    assert len(vs.CRITERIA) == 10 and vs.CRITERIA[-1] == "nothing_approved"
    assert "never required to rise" in vs.VERDICT_RULE
    assert vs.verdict({name: True for name in vs.CRITERIA})["verdict"] == vs.READY
    checks = {name: True for name in vs.CRITERIA}
    checks["arrival_paco2_reproduced"] = False
    assert vs.verdict(checks)["verdict"] == f"{vs.NOT_READY} - ARRIVAL_PACO2_REPRODUCED"


def test_the_policy_approves_nothing_and_reads_no_legacy():
    assert "nothing selected or approved" in vs.POLICY and "legacy RR is never read" in vs.POLICY
    assert "pH never filters" in vs.POLICY
    for item in vs.DECISION_ITEMS.values():
        assert item[0] and item[1]
    for path in (SOURCE, ROOT / "clinical_core" / "ventilation.py"):
        source = path.read_text(encoding="utf-8")
        for forbidden in ("family_engine", "legacy_adapter", "snapshot("):
            assert forbidden not in source
    assert json.loads(json.dumps(vs.design(), default=str))["ventilation_gains"] == [0.03, 0.04, 0.05, 0.06, 0.08]
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()


# The record and the report ------------------------------------------------------------------------------------------------

RECORD = ROOT / "docs" / "revision" / "P2K3_ventilation_surface.json"
DOCUMENT = ROOT / "docs" / "revision" / "P2K3_VENTILACION_EFECTIVA_Y_SUPERFICIE_RESPIRATORIA.md"


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def _json(value):
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def test_the_record_comes_from_the_frozen_package_and_its_analytic_part_is_reproduced_live(record, probes):
    assert record["freeze_digest"] == FROZEN_DIGEST and record["record"] == vs.P2K2_DIGEST
    assert record["design"] == _json(vs.design()) and record["probes"] == _json(probes)
    assert record["probes_pass"] == _json(vs.probes_pass(probes)) and record["w_inputs"] == _json(vs.w_inputs())
    assert record["arrival_rr"] == _json(ab.arrival_compatibility())
    assert record["arrival_paco2"] == _json(vs.paco2_compatibility())
    surface = vs.joint_surface(ab.arrival_compatibility(), vs.paco2_compatibility())
    assert record["joint_surface"] == _json(surface)
    assert record["demand_semantics"] == _json(vs.demand_semantics_sensitivity())
    assert record["exact_ventilation_gains"] == _json(vs.exact_ventilation_gains())
    assert record["arrival_rejections"] == _json(vs.arrival_rejections())
    assert record["identifiability"] == _json(vs.identifiability(surface["joint"]))
    assert record["core_unchanged"] == _json(vs.core_unchanged())


def test_the_verdict_validation_and_non_regression_the_report_states(record):
    assert record["verdict"]["verdict"] == vs.READY and not record["verdict"]["failing"] and "stopped" not in record
    assert all(record["verdict"]["checks"].values()) and set(record["verdict"]["checks"]) == set(vs.CRITERIA)
    v = record["validation"]
    assert v["compared"] == 48 and v["equal"] and v["max_abs_diff"] == 0.0 and v["order_independent"]
    assert v["rr_alone_moves_no_w"] and v["rr_moved"] and v["intrinsic_alone_moves_no_w"] and v["demand_ratio_one"]
    assert v["upstream_equal"] and v["default_rr_equal"] and v["domains"] == {name: True for name in vs.UPSTREAM_DOMAINS}
    assert record["p2k1_unchanged"] and all(record["pressure_tone_unchanged"].values())
    assert record["p2k2_reproduced"] == {"arrival_compatibility": True, "probes": True, "upstream_tables": True}
    assert record["rejections"] == {ab.ANALYTIC_REJECTION: 0, ab.SIMULATION_REJECTION: 0}
    assert record["arrival_rejections"] == {ab.ANALYTIC_REJECTION: 0}
    # The arrival surface: RR as in P2K-2, PaCO2 for every common gain but 0.08, joint the product.
    surface = record["joint_surface"]
    assert record["arrival_rr"]["count"] == 9 and record["arrival_paco2"]["compatible"] == [0.03, 0.04, 0.05, 0.06]
    assert surface["arrival_read"] == {"total": 225, "rr_compatible": 45, "paco2_compatible": 180, "joint": 36}
    assert surface["with_acid_support"]["joint"] == 324
    p = record["plausible"]
    assert p["outside"] == 0 and p["non_positive"] == 0 and vs.PH_PLAUSIBLE[0] < p["ph_low"] < p["ph_high"] < 7.8
    assert record["dependencies"]["multiplied"] == ["demand", "tone_gain"]
    assert record["efficiency"]["cartesian_sweep"] is False and record["efficiency"]["legacy_read"] is False
    assert record["envelope_request"] == list(vs.ENVELOPE_REQUEST)


def test_the_key_answers_the_report_puts_first(record):
    q = record["key_questions"]
    assert q["1_resting_hypercapnia"]["all_reference"]
    assert q["1_resting_hypercapnia"]["p2k2_over_the_same_rr_candidates"]["gi_bleed_57m"]["high"] > 70.0
    assert q["2_paco2_toward_40"]["r4_toward"]["true"] == q["2_paco2_toward_40"]["r4_toward"]["n"] > 0
    assert q["4_72f_early_dip"]["by_b"]["13.4"]["true"] == q["4_72f_early_dip"]["by_b"]["13.4"]["n"]
    assert q["4_72f_early_dip"]["by_b"]["28"]["true"] == 0
    assert 0 < q["5_lactate_rr_opposite"]["true"] < q["5_lactate_rr_opposite"]["n"]
    six = q["6_rr_paco2_directions"]
    assert six["same_direction"]["true"] == 0 and six["opposite_direction"]["true"] == six["opposite_direction"]["n"]
    # Every RR observable reads no ventilation gain, every gas observable no drive gain or intrinsic RR.
    for letter, item in record["decision_pack"].items():
        assert item["status"] == "PREPARED_NOT_APPROVED"
        for name, summary in item["distributions"].items():
            gas = letter in "CDH"
            silent = ("drive_gain", "intrinsic_rr") if gas else ("ventilation_gain",)
            for factor in silent:
                assert summary[factor] == {"path": "NONE", "range": 0.0}, (name, factor)


def test_the_document_is_generated_from_the_record():
    from clinical_core import ventilation_surface_report as rep
    document = DOCUMENT.read_text(encoding="utf-8")
    data = json.loads(RECORD.read_text(encoding="utf-8"))
    rendered = document
    for name, render in rep.RENDERERS.items():
        rendered = rep.apply(rendered, name, render(data))
    assert rendered == document, "the generated blocks are stale: regenerate the report"
    assert vs.READY in document and "## 15. Lo que se pide a la docencia" in document
    assert "## 16. Limitaciones" in document and "## 17. Revisión adversarial" in document
    assert len(rep.ENVELOPE_ES) == len(vs.ENVELOPE_REQUEST) and len(rep.QUESTIONS_ES) == len(vs.FACULTY_QUESTIONS)
