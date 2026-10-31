"""Phase 2 shadow core, P2K-2: the metabolic acid burden and the effective-ventilation core.

These tests pin the acid-base physiology in the core (off by default, all three gains or none, the burden a dynamic state
produced by the effective deficit and cleared first-order, never negative, no repayment rule), the retirement of every
lactate, D and W-channel path into the candidate RR, the separation of drive, RR and W, PaCO2 anchored and pH from HCO3
and PaCO2, the structural probes A-H, the predeclared candidates and their construction, the analytic arrival, the
factorized reconstruction against the core, the default-profile non-regression, the AST proof of P2K-2's insertions and
the dependency maps the closed packages rest on, and the policy: nothing approved.
"""
import ast
import hashlib
import inspect
import json
import math
from dataclasses import fields, replace

import pytest

from clinical_core import acid_base as ab
from clinical_core import blood_fluid_calibration as bf
from clinical_core import decision_pack, lactate_slice
from clinical_core import derived as dv
from clinical_core import integration
from clinical_core import vascular_tone as vt
from clinical_core.derived import DEFAULT_PROFILE, PARAMETERS, CoreProfile, arrival_state, derive, respiration
from clinical_core.integration import step
from clinical_core.state import (ARRIVAL_LAYERS, AUXILIARY_FIELDS, CASE_PARAMETERS, AuxiliaryState, CoreInvariantError,
                                 UnresolvedBoundary)

ROOT = ab.ROOT
SOURCE = ROOT / "clinical_core" / "acid_base.py"
#: The P2K-2 freeze: the faculty decisions, the semantics, the predeclared candidates and their rules, the probes, the
#: reconstruction, identifiability and verdict rules, the AST proof and every clinical_core source but the downstream
#: reports, committed before any clinical respiratory trajectory was read.
FROZEN_DIGEST = "23aa0a38ccecac0284f14e6ef46b81e49da4c0bb6510b65e99372a3d79ae1b22"
C57, C72 = ab.C57, ab.C72
GAINS = ("deficit_to_acid_gain", "acid_clearance_tau_min", "acid_to_drive_gain")


@pytest.fixture(scope="module")
def probes():
    return ab.probes()


def _active(**changes):
    return ab.candidate_profile(2.0, 19.4, 120.0, base=replace(DEFAULT_PROFILE, oxygen_extraction_reserve=ab.RESERVE),
                                **changes)


# The frozen package ------------------------------------------------------------------------------------------------------

def test_the_package_is_frozen():
    sources = bf.freeze_sources()
    assert "clinical_core/acid_base.py" in sources and "clinical_core/derived.py" in sources
    assert "clinical_core/acid_base_report.py" in lactate_slice.DOWNSTREAM_REPORTS
    assert {"clinical_core/acid_base.py", "clinical_core/acid_base_report.py"} <= set(decision_pack.PACK_DIGEST_EXCLUDED)
    assert ab.p2k1_record()["freeze_digest"] == ab.P2K1_DIGEST
    if FROZEN_DIGEST is not None:
        assert ab.freeze_digest() == FROZEN_DIGEST, "a source, a rule or a candidate changed after the freeze"


def test_the_faculty_decisions_and_the_carried_uncertainty_are_recorded():
    assert {"acid_state", "acid_dynamics", "lactate", "d", "drive_rr_w", "w", "paco2", "ph", "w_leak", "hypoxaemia",
            "lgn", "support", "upstream", "early_stop", "scope"} <= set(ab.FACULTY)
    assert ab.CARRIED["baroreflex_gain"] == {"1": [0.25, 0.5], "1.1": [0.25, 0.5, 1.0, 1.5]}
    assert ab.CARRIED["map_set"] == [80.0, 90.0, 100.0] and ab.CARRIED["approved"] == []
    assert "not FACULTY_APPROVED" in ab.FACULTY["acid_state"] and "not collapsed" in ab.FACULTY["carried"]
    assert ab.STATUS["bicarbonate_reference"] == "COMMON_REFERENCE_PROVISIONAL"
    assert ab.STATUS["hypoxaemic_drive"] == "HYPOXEMIC_DRIVE_DEFERRED" and ab.STATUS["lgn"] == "GENERALIZATION_PATH_RESERVED"
    assert ab.STATUS["support"] == "FUTURE_GENERALIZATION_REQUIREMENT" and ab.STATUS["approved"] == "none FACULTY_APPROVED"


# The core: off by default, all or nothing --------------------------------------------------------------------------------

def test_the_acid_base_physiology_is_off_by_default_and_declared_whole():
    assert not dv.acid_base_active(DEFAULT_PROFILE)
    assert all(getattr(DEFAULT_PROFILE, name) is None for name in GAINS)
    assert DEFAULT_PROFILE.bicarbonate_reference_meq_l == 24.0 and DEFAULT_PROFILE.ventilation_efficiency == 1.0
    for name in GAINS:
        with pytest.raises(CoreInvariantError):
            replace(DEFAULT_PROFILE, **{name: 1.0})
    with pytest.raises(CoreInvariantError):
        _active(acid_clearance_tau_min=0.5)
    for bad in (0.0, 1.5):
        with pytest.raises(CoreInvariantError):
            _active(ventilation_efficiency=bad)
    for name in ("bicarbonate_reference_meq_l", "paco2_reference_mmhg", "rr_drive_saturation"):
        assert "PROVISIONAL" in PARAMETERS[name][0].upper() or PARAMETERS[name][0] == dv.PROVISIONAL
    assert "COMMON_REFERENCE_PROVISIONAL" in PARAMETERS["bicarbonate_reference_meq_l"][1]
    assert "not FACULTY_APPROVED" in PARAMETERS["bicarbonate_reference_meq_l"][1]
    assert set(PARAMETERS) == {f.name for f in fields(CoreProfile)}
    with pytest.raises(CoreInvariantError):
        respiration(arrival_state(ab.PROBE_ANCHORS, DEFAULT_PROFILE), ab.PROBE_ANCHORS, DEFAULT_PROFILE)


def test_the_new_case_parameters_and_the_auxiliary_burden_are_declared():
    # Candidate inputs, outside the case-parameter / migration registry until the faculty adopts the physiology.
    for name in ab.CANDIDATE_INPUTS:
        assert name not in CASE_PARAMETERS and getattr(vt.NEUTRAL, name) is None
    assert "intrinsic_respiratory_rate" in ARRIVAL_LAYERS["physiological_reference"]
    assert {"arrival_bicarbonate", "arrival_paco2"} <= set(ARRIVAL_LAYERS["arrival_dynamic_state"])
    assert "metabolic_acid_burden" in AUXILIARY_FIELDS and "metabolic_acid_burden" in dv.AUXILIARY_SOURCES
    with pytest.raises(CoreInvariantError):
        AuxiliaryState(metabolic_acid_burden=-0.1)
    with pytest.raises(CoreInvariantError):
        replace(ab.PROBE_ANCHORS, arrival_paco2=0.0)
    with pytest.raises(CoreInvariantError):
        replace(vt.NEUTRAL, intrinsic_respiratory_rate=-1.0)


def test_the_arrival_burden_comes_from_the_bicarbonate_never_the_lactate():
    for case, hco3 in ((C57, 17.3), (C72, 19.8)):
        assert ab.authored_gas(case)["hco3"] == hco3
        assert math.isclose(ab.arrival_burden(case), 24.0 - hco3)
    import clinical_cases
    for case in (C57, C72):
        result = clinical_cases.variant_by_id(case)["investigations"]["abg"]["result"]
        gas = ab.authored_gas(case)
        assert (result["ph"], result["paco2_mm_hg"], result["bicarbonate_mmol_l"]) == (gas["ph"], gas["paco2"], gas["hco3"])
    high = replace(ab.PROBE_ANCHORS, lactate=6.0)
    assert dv.arrival_acid_burden(high, _active()) == dv.arrival_acid_burden(ab.PROBE_ANCHORS, _active()) == 4.0
    assert "lactate" not in inspect.getsource(dv.arrival_acid_burden).split('"""')[-1]


def test_the_burden_dynamics_produce_from_the_deficit_and_clear_first_order():
    p = _active()
    k, tau = p.deficit_to_acid_gain, p.acid_clearance_tau_min
    assert dv.acid_burden_after_minute(0.0, 0.0, p) == 0.0, "no deficit, no burden, no production"
    assert dv.acid_burden_after_minute(4.0, 0.3, p) == 4.0 + k * 0.3 - 4.0 / tau
    assert dv.acid_burden_after_minute(4.0, 0.5, p) > dv.acid_burden_after_minute(4.0, 0.3, p), "more deficit, more acid"
    # The burden may fall while a deficit lasts (clearance above production): no no-repayment rule.
    assert dv.acid_burden_after_minute(10.0, 0.1, p) < 10.0
    for a in (0.0, 0.1, 5.0, 30.0):
        assert dv.acid_burden_after_minute(a, 0.0, replace(p, acid_clearance_tau_min=1.0)) >= 0.0
    source = inspect.getsource(dv.acid_burden_after_minute) + inspect.getsource(integration._acid_burden)
    for forbidden in ("state.D", "lactate", "no_repayment", "withdrawn"):
        assert forbidden not in source.split('"""')[-1]


def test_the_core_integrates_the_burden_from_the_deficit_d_integrates():
    p = _active()
    state = arrival_state(ab.PROBE_ANCHORS, p).evolve(P=0.3)
    for _ in range(5):
        before = state
        delivery = dv.effective_delivery(derive(before, ab.PROBE_ANCHORS, p).delivery_rel, ab.PROBE_ANCHORS)
        deficit = dv.effective_oxygen_deficit(before.aux.oxygen_demand, delivery, p.oxygen_extraction_reserve)
        state, record = step(state, (), ab.PROBE_ANCHORS, p)
        assert deficit > 0.0
        assert state.aux.metabolic_acid_burden == dv.acid_burden_after_minute(before.aux.metabolic_acid_burden, deficit, p)
        assert "metabolic_acid_burden" in {c.quantity for c in record.auxiliary}
    off = arrival_state(ab.PROBE_ANCHORS, DEFAULT_PROFILE).evolve(P=0.3)
    for _ in range(5):
        off, _ = step(off, (), ab.PROBE_ANCHORS, DEFAULT_PROFILE)
    assert off.aux.metabolic_acid_burden == 4.0, "held while the physiology is off"


# No lactate, D or W channel in the candidate RR; drive, RR and W distinct -----------------------------------------------

def test_the_candidate_rr_reads_the_burden_only(probes):
    for name in ("respiratory_drive", "rate_from_drive", "respiration"):
        body = inspect.getsource(getattr(dv, name)).split('"""')[-1]
        for forbidden in ("lactate", "state.D", "state.W", "sympathetic", "pressure", ".hr"):
            assert forbidden not in body, (name, forbidden)
    assert probes["B"]["rr_unchanged"] and probes["B"]["lactate_raised"]
    assert probes["C"]["rr_unchanged"] and probes["W_channel"]["rr_unchanged"]
    assert probes["A"]["drive_rises"] and probes["A"]["rr_rises"] and probes["A"]["deficit"] == 0.0
    assert probes["D"]["burden_falls"] and probes["D"]["rr_falls"] and probes["D"]["lactate_stays_high"]


def test_drive_rr_and_w_are_three_quantities(probes):
    r = respiration(ab._probe_state(8.0), ab.PROBE_ANCHORS, ab.PROBE_PROFILE)
    assert r.drive != r.respiratory_rate != r.ventilation
    assert probes["E1"]["w_at_most_1"] and probes["E1"]["rr_above_intrinsic"]
    assert probes["E2"]["paco2_rises"] and probes["E2"]["rr_rises"] and probes["E2"]["w_falls_below_1"]
    assert probes["F"]["w_rises"] and probes["F"]["rr_unchanged"] and probes["F"]["paco2_falls"]
    assert probes["G"]["w_falls"] and probes["G"]["paco2_rises"]
    # RR rises smoothly and monotonically with the drive, slope 1 at no drive, toward intrinsic + S; rr_max only guards.
    rates = [dv.rate_from_drive(d, 16.0, DEFAULT_PROFILE) for d in (0.0, 1.0, 5.0, 20.0, 100.0, 1e4)]
    assert rates[0] == 16.0 and all(b > a for a, b in zip(rates, rates[1:-1])) and rates[-1] <= 16.0 + 25.0
    assert math.isclose(dv.rate_from_drive(1e-6, 16.0, DEFAULT_PROFILE) - 16.0, 1e-6, rel_tol=1e-5)


def test_paco2_is_exact_at_arrival_and_ph_follows_hco3_and_paco2(probes):
    assert probes["H"]["arrival_exact"] and probes["H"]["ph_formula"]
    assert probes["H"]["more_acid_lower_ph"] and probes["H"]["lower_paco2_higher_ph"]
    for case in (C57, C72):
        rec = ab.ph_reconstruction(case)
        assert abs(rec["error"]) < 0.0015, "within the bank's 0.1 mEq/L rounding of HCO3"
    assert math.isclose(ab.ph_reconstruction(C57)["derived_ph"], 6.1 + math.log10(17.3 / (0.03 * 31)))


def test_without_a_pulse_there_is_no_breathing_and_no_paco2():
    p = _active()
    state = arrival_state(ab.PROBE_ANCHORS, p)
    from clinical_core.state import RhythmState
    pulseless = state.evolve(R=RhythmState.asystole(), terminal_since=0)
    r = respiration(pulseless, ab.PROBE_ANCHORS, p)
    assert r.respiratory_rate == 0.0 and r.ventilation == 0.0 and r.paco2 is None and r.ph is None
    assert derive(pulseless, ab.PROBE_ANCHORS, p).respiratory_rate == 0.0


def test_no_bicarbonate_left_stops_the_run():
    p = _active()
    state = arrival_state(ab.PROBE_ANCHORS, p)
    with pytest.raises(UnresolvedBoundary):
        respiration(state.evolve(aux=replace(state.aux, metabolic_acid_burden=24.0)), ab.PROBE_ANCHORS, p)


def test_the_arrival_rr_is_reported_not_forced():
    p = _active()
    anchors = replace(ab.PROBE_ANCHORS, respiratory_rate=24.0)
    split = dv.respiratory_rate_decomposition(anchors, p)
    assert split["model_rr"] != split["authored_rr"] and math.isclose(split["mismatch"], split["model_rr"] - 24.0)
    view = dv.check_arrival_reconstruction(anchors, p)
    assert view.respiratory_rate == split["model_rr"]
    # Off, the P2K-1 RR still reproduces the authored arrival RR exactly, and the check still requires it.
    off = replace(DEFAULT_PROFILE, oxygen_extraction_reserve=ab.RESERVE)
    assert dv.check_arrival_reconstruction(anchors, off).respiratory_rate == 24.0
    assert "expected.pop(\"respiratory_rate\")" in inspect.getsource(dv.check_arrival_reconstruction)


# Predeclared candidates and their construction ---------------------------------------------------------------------------

def test_the_candidates_are_the_predeclared_ones_and_their_rules_reproduce_them():
    assert ab.INTRINSIC_RR == (12.0, 16.0, 20.0) and ab.ACID_TAUS == (60.0, 120.0, 240.0)
    assert all(math.isclose(a, b) for a, b in zip(ab.drive_gain_support(), ab.DRIVE_GAINS))
    assert ab.steady_burden_support() == ab.STEADY_BURDENS == (13.4, 19.4, 28.0)
    gains = ab.exact_arrival_gains()
    assert min(gains.values()) >= ab.DRIVE_GAINS[0] and max(gains.values()) <= ab.DRIVE_GAINS[-1]
    deficits = ab.arrival_deficits()
    assert {k: round(v, 9) for k, v in deficits.items()} == {f"{C57} x1": 0.4, f"{C72} x1": 0.15, f"{C57} x1.1": 0.5,
                                                             f"{C72} x1.1": 0.25}
    assert len(ab.acid_pairs()) == 9 and ab.EFFICIENCY == 1.0 and ab.ARRIVAL_TOLERANCE == 3.0
    p = ab.candidate_profile(2.0, 19.4, 120.0)
    assert math.isclose(p.deficit_to_acid_gain * p.acid_clearance_tau_min, 19.4)
    for name in ("debt_clearance_tau_min", "debt_per_delivery_deficit", "debt_to_lactate_gain", "lactate_clearance_tau_min"):
        assert getattr(p, name) == getattr(DEFAULT_PROFILE, name), "independent of the debt and lactate parameters"


def test_analytic_rejections_mark_only_impossible_values():
    assert ab.analytic_rejections(2.0, 16.0, 19.4, 120.0, 0.8, C57) == []
    assert "non-positive HCO3" in ab.analytic_rejections(2.0, 16.0, 40.0, 120.0, 0.8, C57)
    assert "negative respiratory drive" in ab.analytic_rejections(-1.0, 16.0, 19.4, 120.0, 0.8, C57)
    assert "RR saturation above the safety guard" in ab.analytic_rejections(2.0, 40.0, 19.4, 120.0, 0.8, C57)
    assert "legacy" not in inspect.getsource(ab.analytic_rejections).lower().split('"""')[-1]


def test_the_burden_series_is_the_cores_integration():
    deficits = [0.4, 0.4, 0.3, 0.0, 0.0]
    series = ab.burden_series(deficits, 6.7, 19.4, 120.0)
    p = ab.candidate_profile(1.0, 19.4, 120.0)
    assert series[0] == 6.7 and series[1] == dv.acid_burden_after_minute(6.7, 0.4, p) and len(series) == len(deficits)


# The AST proof of P2K-2's insertions and the closed packages' maps --------------------------------------------------------

def test_p2k2_changed_the_core_only_by_its_declared_inert_insertions():
    assert all(ab.proofs().values())
    assert all(ab.inert(relative) for relative in ab.CORE_FILES)
    for relative in ab.CORE_FILES:
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != ab.CORE_AT_P2K1[relative]
        live = vt._live(relative)
        assert ast.dump(ast.parse(ab.stripped_text(relative))) == ast.dump(ast.parse(ab.p2k1_text(relative)))
    derived = vt._live(ab.DERIVED)
    mutated = derived.replace("OUTPUT_EPSILON = 1e-9", "OUTPUT_EPSILON = 1e-8")
    assert ab.body_digest(ab.stripped_body(ab.DERIVED, mutated)) != ab.WHOLE_AT_P2K1[ab.DERIVED], "a change outside"
    mutated = derived.replace("rr = respiration(state, anchors, profile).respiratory_rate",
                              "rr = respiration(state, anchors, profile).respiratory_rate\n        output_rel = 1.0")
    assert ab._strip(ab.DERIVED, mutated)[1], "logic hidden in an inserted check must be noticed"
    mutated = derived + "\nOUTPUT_EPSILON = bicarbonate\n"
    assert ab.body_digest(ab.stripped_body(ab.DERIVED, mutated)) != ab.WHOLE_AT_P2K1[ab.DERIVED], \
        "a new statement that only mentions a P2K-2 name is not dropped"
    state = vt._live(ab.STATE)
    mutated = state.replace('"arrival_delivery_ratio": 1.0, "reference_preload_fraction": None}',
                            '"arrival_delivery_ratio": 0.9, "reference_preload_fraction": None}')
    assert mutated != state and ab.body_digest(ab.stripped_body(ab.STATE, mutated)) != ab.WHOLE_AT_P2K1[ab.STATE]


def test_the_closed_packages_see_the_core_at_their_own_hashes_only_while_proven():
    from clinical_core import baroreflex as br
    sources = {relative: "live" for relative in ab.CORE_FILES}
    core = {k: ab.CORE_AT_P2K1[k] for k in ab.CORE_FILES}
    assert ab.p2j4_sources(sources) == core == ab.p2k1_sources(sources)
    item = br.P2J4_CHANGES[ab.DERIVED]
    assert ab.p2j3_sources(sources)[ab.DERIVED] == item["sha_at_p2j3"]
    assert ab.p2j1_sources(sources)[ab.DERIVED] == item["sha_at_p2j1"]
    assert ab.p2i2ak_sources(sources)[ab.DERIVED] == item["sha_at_p2i2ak"]
    integration_item = vt.P2J2_CHANGES[ab.INTEGRATION]
    assert ab.p2j1_sources(sources)[ab.INTEGRATION] == integration_item["sha_at_p2j1"]
    assert ab.p2i2ak_sources(sources)[ab.INTEGRATION] == integration_item["sha_at_p2i2ak"]
    assert ab.p2j3_sources(sources)[ab.STATE] == ab.p2i2ak_sources(sources)[ab.STATE] == ab.CORE_AT_P2K1[ab.STATE]


def test_the_default_core_is_unchanged_where_it_runs():
    """With the physiology off, the arrival and a minute of every probe are the P2K-1 core's: the RR is the P2K-1 RR."""
    from clinical_core import rr_audit as ra
    state = arrival_state(ra.PROBE_ANCHORS, DEFAULT_PROFILE)
    assert state.aux.metabolic_acid_burden == 0.0
    assert derive(state, ra.PROBE_ANCHORS, DEFAULT_PROFILE).respiratory_rate == \
        dv.respiratory_rate(state, ra.PROBE_ANCHORS, DEFAULT_PROFILE, derive(state, ra.PROBE_ANCHORS).lactate)


# Policy -------------------------------------------------------------------------------------------------------------------

def test_the_policy_approves_nothing_and_reads_no_legacy_rr():
    assert "nothing selected or approved" in ab.POLICY and "legacy RR never read" in ab.POLICY
    assert ab.verdict({name: True for name in ab.CRITERIA})["verdict"] == ab.READY
    checks = {name: True for name in ab.CRITERIA}
    checks["patient_like"] = False
    assert ab.verdict(checks)["verdict"] == f"{ab.NOT_READY} - PATIENT_LIKE"
    source = SOURCE.read_text(encoding="utf-8")
    for forbidden in ("family_engine", "legacy_adapter", "snapshot("):
        assert forbidden not in source
