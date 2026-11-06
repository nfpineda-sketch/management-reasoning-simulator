"""P2O-2: the congestion-generation and reference-semantics audit, read-only.

No core file changes. These tests pin the structural facts the audit's decision rests on
(docs/revision/P2O2_GENERACION_CONGESTION_Y_REFERENCIA.md): what L, V and P mean, who writes and reads L, why the
common volume coupling generates no lung water on acs_70f_left_main, the five V / P states, the new reachability of HR
and of the consciousness ladder through G -> SpO2, and the no-credit-below-arrival semantics. Every value is read from
the frozen core and the frozen packages; nothing is selected.
"""
import ast
import inspect
import json
import math
from dataclasses import replace
from pathlib import Path

import pytest

from clinical_core import acs_migration as an
from clinical_core import acs_reference as ar
from clinical_core import blood_anchors as ba
from clinical_core import derived as dv
from clinical_core import encephalopathy as enc
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
from clinical_core import closure_guard as cg
from clinical_core import tone_domain as x1
from clinical_core.bands import ARRIVAL
from clinical_core.integration import CHANNEL_BOUNDS
from clinical_core.state import CHANNEL_DEFINITIONS, Anchors, Channel

ROOT = Path(__file__).resolve().parent
P2O1_RECORD = ROOT / "docs" / "revision" / "P2O1_gas_exchange.json"


#: P2P-2 changed the core (the respiratory-drive composition, inert by default), proven against the P2P-1 files
#: (respiratory_drive.proved): the audit reads the core as P2O-1 left it through the chain (pe.chain, rd.chain).
@pytest.fixture(autouse=True, scope="module")
def _p2o1_core_through_the_chain():
    with pytest.MonkeyPatch.context() as patch:
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
        cg.chain(patch)
        yield


def _functions_naming_l(relative: str) -> set:
    # The audit describes the core at 96b9d65: P2O-3's changed files are read as P2O-1 left them (lw.p2o1_text, proven).
    tree = ast.parse(lw.p2o1_text(relative))
    out = set()
    for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
        if any(isinstance(n, ast.Attribute) and n.attr == "L" and isinstance(n.value, ast.Name) for n in ast.walk(fn)):
            out.add(fn.name)
    return out


# P2O-2-1: L ----------------------------------------------------------------------------------------------------------------

def test_l_is_an_arrival_relative_lung_water_index_with_a_guard_only_domain():
    assert CHANNEL_DEFINITIONS[Channel.L][1] == "index deviation from arrival"
    lower, upper, status, why = CHANNEL_BOUNDS[Channel.L]
    assert (lower, upper) == (-10.0, 10.0) and "guard only" in why
    # Arrival is L = 0 whatever the authored lungs: acs_70f_left_main arrives with bibasal B-lines and L = 0.
    assert dv.arrival_state(ar.anchors(), ar.common_profile()).L == 0.0 and "B-lines" in ar.truth()["pocus_lungs"]


def test_the_writers_and_readers_of_l():
    # The core: the preload-congestion coupling and the clearance write L; the clearance and P2O-1's coupling read it.
    assert _functions_naming_l("clinical_core/derived.py") == {"lung_water_clearance"}
    assert _functions_naming_l("clinical_core/integration.py") == {"step"}
    source = inspect.getsource(dv.congestion_rate)
    assert "state.L" not in source and "preload_position" in source and "pump_reserve" in source
    # Every ChannelDelta built in clinical_core, by AST: Channel.L literally only in the integrator and the ACS writer;
    # a channel built from a variable only where it is generic (the bounds' clamps, the synthetic Drift, P2O-1's G).
    literal_l, variable = set(), set()
    for path in (ROOT / "clinical_core").rglob("*.py"):
        relative = path.relative_to(ROOT).as_posix()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "ChannelDelta" and node.args:
                first = node.args[0]
                if isinstance(first, ast.Attribute) and isinstance(first.value, ast.Name) and first.value.id == "Channel":
                    # P2P-1's and P2Q-2's family writers postdate this audit.
                    if first.attr == "L" and relative not in pe.OWN + em.OWN:
                        literal_l.add(relative)
                else:
                    variable.add(relative)
    assert literal_l == {"clinical_core/integration.py", "clinical_core/modules/acs_ischaemia.py"}
    assert variable == {"clinical_core/integration.py", "clinical_core/bands.py"}
    # contracts_output exports every scalar channel generically (L among them), without reading L itself.
    assert "getattr(state, channel.value) for channel in SCALAR_CHANNELS" in \
        (ROOT / "clinical_core" / "contracts_output.py").read_text(encoding="utf-8")
    for relative in ("clinical_core/contracts_output.py", "clinical_core/legacy_adapter.py",
                     "clinical_core/contracts_shadow.py"):
        assert not _functions_naming_l(relative), relative
    # The guard's text has been stale since P2N-2 (a family writer writes L too): declared, not corrected here.
    assert "only the core's congestion and clearance write L yet" in CHANNEL_BOUNDS[Channel.L][3]


# P2O-2-2 / 3: V and P, the five states ------------------------------------------------------------------------------------

def _anchors(reserve: float) -> Anchors:
    return Anchors(**{**ARRIVAL, "case_id": f"vp_{reserve}", "pump_reserve": reserve,
                      "declared": ({"pump_reserve": "synthetic_probe"} if reserve != 1.0 else {})})


def _vp(name, reserve):
    V, P = {"A": (0.0, 1.0), "B": (0.0, 0.6), "C": (1500.0, 1.0), "D": (1500.0, 0.6), "E": (-300.0, 0.6)}[name]
    a, p = _anchors(reserve), dv.DEFAULT_PROFILE
    state = dv.arrival_state(a, p).evolve(V=V, P=P)
    return {"position": dv.preload_position(state, a, p), "arrival_position": dv.preload_position(state, a, p, volume=0.0),
            "rate": dv.congestion_rate(state, a, p), "output": dv.derive(state, a, p).output_rel}


@pytest.mark.parametrize("reserve", [1.0, 0.5])
def test_the_five_v_p_states_are_distinguished_but_only_added_volume_congests(reserve):
    a, b, c, d, e = (_vp(n, reserve) for n in "ABCDE")
    assert a["rate"] == b["rate"] == e["rate"] == 0.0
    # B: the same volume sits nearer the plateau of a weaker pump's curve, yet no congestion by construction.
    assert b["position"] > a["position"] and b["position"] == b["arrival_position"]
    # E: underfilling despite pump failure, told apart from B by its position and output.
    assert e["position"] < a["position"] < b["position"] and e["output"] < b["output"] < a["output"]
    # C: a pump with full reserve never congests from volume; a reserve-limited one does. D congests most.
    assert (c["rate"] == 0.0) == (reserve == 1.0)
    assert d["rate"] > c["rate"] and d["position"] > c["position"]


@pytest.mark.parametrize("p_value", [1.0, 0.8, 0.6, 0.4, 0.2])
def test_pump_failure_alone_never_generates_lung_water(p_value):
    a = _anchors(0.5)
    state = dv.arrival_state(a, dv.DEFAULT_PROFILE).evolve(P=p_value)
    assert dv.congestion_rate(state, a, dv.DEFAULT_PROFILE) == 0.0


# P2O-2-4: why the common coupling generates no L on the ACS arrival -------------------------------------------------------

def test_the_acs_volume_limitation_is_the_distance_to_the_knee_in_effective_volume():
    a, p = ar.anchors(), ar.common_profile()
    fill0 = dv.arrival_filling(a, p)
    assert dv.arrival_preload(a, p) == p.arrival_preload_fraction == 0.5          # neutral mapping (IVC), not the B-lines
    need = {P: -p.preload_curve_scale_ml * P * math.log(1.0 - p.congestion_preload_knee) - fill0 for P in (1.0, 0.7)}
    assert round(need[1.0]) == 1003 and round(need[0.7]) == 529
    assert an.CRYSTALLOID["crystalloid_effective_ml_per_ml"] == 0.125
    for volume, label in ((1000.0, 97), (4000.0, 386)):
        bag = replace(an._bag(), volume_ml=volume, untimed_rate_ml_per_min=volume / an.FLUID["duration_min"])
        for P in (1.0, 0.7):
            states, _ = an.course((bag,), 120, a, p, dv.arrival_state(a, p).evolve(P=P))
            v_max = max(s.V for s in states)
            assert round(v_max) == label and v_max < need[P] and max(s.L for s in states) == 0.0


def test_gi_never_congests_through_the_common_coupling():
    """GI: reserve 1.0 and no pump writer, so P stays 1 and the shortfall is 0; the courses write no congestion. (The
    coupling would act in GI only if a low P met volume above the knee.)"""
    for case in an.C57, "gi_bleed_72f":
        anchors, profile, values = ba.setup(case)
        assert anchors.pump_reserve == 1.0
        for scenario, volume in (("untreated", None), ("crystalloid", 1000.0)):
            states, records = an.course(ba.contributors(case, scenario, values, volume), 120, anchors, profile)
            assert {s.P for s in states} == {1.0} and max(s.L for s in states) == 0.0
            assert not any(d.source == dv.PRELOAD_CONGESTION for r in records for d in r.deltas)


# P2O-2-7: below arrival ----------------------------------------------------------------------------------------------------

def test_no_credit_below_arrival_and_reperfusion_never_improves_on_the_arrival_lungs():
    from clinical_core.bands import Drift
    p = go.gas_profile(dv.DEFAULT_PROFILE)
    assert dv.lung_water_gas_exchange(0.0, -0.5, p) == 0.0
    assert dv.oxygenation(-1.0, 0.21, ar.anchors(), p) == dv.oxygenation(0.0, 0.21, ar.anchors(), p) == 94.0
    # Lung water taken below arrival (a synthetic drift): G and SpO2 stay at arrival, and nothing returns L toward 0.
    a, gp = ar.anchors(), go.gas_profile(ar.common_profile())
    below, _ = an.course((Drift("p2o2-below", "L", 0, 30, -0.02),), 60, a, gp)
    assert below[-1].L < -0.5 and below[-1].L == below[30].L
    assert {s.G for s in below} == {0.0} and {dv.derive(s, a, gp).spo2 for s in below} == {94.0}
    a, gp = ar.anchors(), go.gas_profile(ar.common_profile())
    states, _ = an.course(an.writers(reperfusion=60), 360, a, gp)
    assert min(s.L for s in states) == 0.0 and max(dv.derive(s, a, gp).spo2 for s in states) == 94.0
    # With the declared partial recovery (P plateaus below 1) the family writer keeps a congestion source: L persists.
    assert states[-1].P < 1.0 and states[-1].L > states[120].L > 0.0


# P2O-2-9 / 10: new reachability through G -> SpO2 --------------------------------------------------------------------------

def _hr(states, a, p):
    return dv.derive(states[-1], a, p).monitor_rate_bpm


def test_g_reaches_hr_through_two_distinct_existing_terms():
    source = inspect.getsource(dv.sympathetic_target)
    assert "sympathetic_per_hypoxaemia_point * hypoxaemia" in source and "acute_deficit_to_sympathetic_gain * acute" in source
    assert dv.PARAMETERS["sympathetic_per_hypoxaemia_point"][0] == dv.PROVISIONAL
    a, p = ar.anchors(), ar.common_profile()
    gp = go.gas_profile(p)
    control = _hr(an.course(an.writers(), 120, a, p)[0], a, p)
    full = _hr(an.course(an.writers(), 120, a, gp)[0], a, gp)
    no_chemo = replace(gp, sympathetic_per_hypoxaemia_point=0.0)
    delivery_only = _hr(an.course(an.writers(), 120, a, no_chemo)[0], a, no_chemo)
    assert round(full - control, 2) == 1.72 and round(full - delivery_only, 2) == 1.16
    assert delivery_only > control                       # the delivery path alone also raises HR (deficit and D)


def test_the_adopted_consciousness_ladder_is_the_core_derive_s_not_the_p2l2_candidate_s():
    assert dv.PARAMETERS["oxygen_levels"][0] == dv.ADOPTED and dv.DEFAULT_PROFILE.oxygen_levels == ((87.0, 1), (80.0, 2))
    assert "_level(spo2, profile.oxygen_levels)" in inspect.getsource(dv.derive)
    candidate = (ROOT / "clinical_core" / "encephalopathy.py").read_text(encoding="utf-8")
    assert "oxygen_levels" not in candidate and "consciousness_level" not in inspect.getsource(enc.readings)
    assert enc.DEFAULT_ENCEPHALOPATHY.mapping("hypoxaemia") is None                  # UNMAPPED by default
    record = json.loads(P2O1_RECORD.read_text(encoding="utf-8"))
    levels = {r["consciousness_level"] for run in record["acs"]["runs"].values() for r in run["rows"]}
    spo2 = min(r["spo2"] for run in record["acs"]["runs"].values() for r in run["rows"])
    assert levels == {0} and spo2 > 87.0                 # not reached in any frozen ACS course


# P2O-2-11: one oxygen response ------------------------------------------------------------------------------------------------

def test_one_common_response_spans_responsive_to_refractory_but_one_r_serves_every_family():
    anchors = Anchors(**ARRIVAL)
    at_04 = {}
    for r in (0.0, 0.5, 2.0):
        p = go.gas_profile(dv.DEFAULT_PROFILE, oxygen_response_loss_per_gas_exchange_unit=r)
        assert dv.oxygenation(1.2, 0.21, anchors, p) == 91.0                    # the same room-air impairment
        at_04[r] = dv.oxygenation(1.2, 0.4, anchors, p)
    assert at_04[0.0] > at_04[0.5] > at_04[2.0] > 91.0


def test_k_s_r_stay_unset():
    assert all(getattr(dv.DEFAULT_PROFILE, name) is None for name in go.REFERENCE)


# The adversarial review (P2O-2), pinned ---------------------------------------------------------------------------------------

def test_review_full_reserve_still_congests_once_p_falls_with_volume_above_the_knee():
    a = _anchors(1.0)
    state = dv.arrival_state(a, dv.DEFAULT_PROFILE).evolve(V=1500.0)
    assert dv.congestion_rate(state, a, dv.DEFAULT_PROFILE) == 0.0
    assert dv.congestion_rate(state.evolve(P=0.6), a, dv.DEFAULT_PROFILE) > 0.0   # side-less: a right-sided P would too


def test_review_pump_failure_is_counted_twice_above_the_knee_in_acs():
    a, p = ar.anchors(), ar.common_profile()
    writer = an.writers()[1]
    rates = {}
    for P in (1.0, 0.7):
        state = dv.arrival_state(a, p).evolve(V=1500.0, P=P)
        rates[P] = (dv.congestion_rate(state, a, p), sum(d.amount for d in writer.contribute(state, 1, (), a, p).deltas))
    assert rates[0.7][0] > rates[1.0][0] > 0.0          # the core coupling rises with the pump failure
    assert rates[1.0][1] == 0.0 < rates[0.7][1]          # and the family writer adds its own share for the same failure
    # P2O-3: the writer's authority now keeps step from adding the core coupling at all (lung_water_reference R7).


@pytest.mark.parametrize("fraction, P, congests", [(0.5, 0.7, False), (0.6, 0.7, True), (0.7, 0.7, True),
                                                  (0.7, 1.0, False), (0.78, 1.0, True)])
def test_review_the_acs_limitation_depends_on_the_undeclared_arrival_preload_fraction(fraction, P, congests):
    a, p = ar.anchors(), ar.common_profile()
    assert a.preload_fraction is None                   # undeclared: the profile default 0.5
    af = replace(a, preload_fraction=fraction, declared={**dict(a.declared), "preload_fraction": "synthetic_probe"})
    bag = replace(an._bag(), volume_ml=4000.0, untimed_rate_ml_per_min=4000.0 / an.FLUID["duration_min"])
    states, _ = an.course((bag,), 120, af, p, dv.arrival_state(af, p).evolve(P=P))
    assert (max(s.L for s in states) > 0.0) == congests


def test_review_known_core_debt_the_coupling_divides_by_zero_at_the_curve_edge():
    a, p = ar.anchors(), ar.common_profile()
    af = replace(a, preload_fraction=0.99, declared={**dict(a.declared), "preload_fraction": "synthetic_probe"})
    with pytest.raises(ZeroDivisionError):
        dv.congestion_rate(dv.arrival_state(af, p).evolve(P=0.1), af, p)


def test_review_the_ladders_are_reached_in_a_longer_untreated_course():
    a, gp, p = ar.anchors(), go.gas_profile(ar.common_profile()), ar.common_profile()
    states, _ = an.course(an.writers(), 360, a, gp)
    first = lambda cond: next(s.minute for s in states if cond(dv.derive(s, a, gp)))
    assert (first(lambda d: d.spo2 < 87.0), first(lambda d: d.spo2 < 80.0)) == (211, 317)
    plain, _ = an.course(an.writers(), 360, a, p)
    assert next(s.minute for s in plain if dv.derive(s, a, p).consciousness_level >= 1) == 175   # the SBP ladder, no G


def test_review_the_delivery_path_of_hr_includes_an_opposing_baroreflex_share():
    a, p = ar.anchors(), ar.common_profile()
    gp = go.gas_profile(p)
    c, r = an.course(an.writers(), 120, a, p)[0][-1], an.course(an.writers(), 120, a, gp)[0][-1]
    baro = lambda s, prof: dv.baroreflex_drive(dv._perfusion(s, a, prof)[1], a, prof)
    assert baro(r, gp) < baro(c, p)                      # tone and MAP rise slightly: less baroreflex drive

