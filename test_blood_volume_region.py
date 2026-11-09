"""P3-76 y P3-77: fija la forma cerrada, la transformada inversa y la región del bloque de volumen.

Las cifras se comprueban contra el evaluador congelado, no contra sí mismas. Ninguna prueba aprueba un
parámetro. Documento: docs/PHASE3_BLOOD_VOLUME_REGION.md
"""
import ast
import math
import subprocess
import sys

import pytest

import blood_volume_region as bvr
from clinical_core import blood_anchors as ba
from clinical_core import blood_constraints as bc
from clinical_core import blood_extension as be

#: Las envolventes docentes, leídas del módulo congelado (nunca escritas a mano aquí).
ENVELOPES = {"peak": bc.DECISIONS["FD-BLD-04"]["envelope"],
             **{t: v for t, v in bc.DECISIONS["FD-BLD-05"]["envelopes"].items()}}
E_MAX = be.DOMAIN["crystalloid_effective_ml_per_ml"][1]
#: Techo de Rpico que impone FD-BLD-06 por su lectura de 2 L, MEDIDO en el caso que liga (gi_bleed_57m).
PEAK_CEILING_57M = 0.27072


# R1 - la forma cerrada -------------------------------------------------------------------------------

def test_r1_the_closed_form_matches_the_frozen_evaluator():
    """Exacta: el error contra el núcleo congelado se queda en precisión de máquina."""
    worst = 0.0
    for e, s, tau in ((0.22, 0.4, 60.0), (0.18, 0.2, 30.0), (0.30, 0.8, 120.0),
                      (0.16, 0.6, 15.0), (0.34, 0.5, 90.0), (0.25, 0.0, 30.0)):
        row = bc.retained(bc.CASES[0], {"crystalloid_effective_ml_per_ml": e,
                                        "crystalloid_transient_share": s,
                                        "crystalloid_leak_tau_min": tau})
        worst = max(worst, abs(row["early"] - bvr.peak_share(e, s, tau)))
        for t in (30, 60, 120):
            worst = max(worst, abs(row["share"][t] - bvr.retained_share(e, s, tau, float(t))))
    assert worst < 1e-12, worst


def test_r2_the_peak_is_below_e_and_that_is_the_declared_infusion_profile():
    """El pico vale 0,83·e con τ=30 porque la bolsa entra en 20 min: está en la lectura declarada."""
    assert "20 min" in bc.IMPLEMENTATION["crystalloid"]
    assert bvr.INFUSION_MINUTES == 20
    assert 0.0 < bvr.smearing(30.0) < 1.0
    assert bvr.peak_share(1.0, 0.6, 30.0) == pytest.approx(0.830666, abs=1e-6)
    # de ahí la condición necesaria de FD-BLD-04, que el valor provisional de referencia no alcanza
    floor = ENVELOPES["peak"][0] / bvr.peak_share(1.0, 0.6, 30.0)
    assert floor > ba.REFERENCE["crystalloid_effective_ml_per_ml"]


def test_r3_the_smearing_factor_grows_with_tau_and_stays_in_the_unit_interval():
    values = [bvr.smearing(t) for t in (1.0, 5.0, 30.0, 120.0, 600.0, 6000.0)]
    assert all(0.0 < v < 1.0 for v in values)
    assert values == sorted(values)


# R2 - el intervalo exacto ----------------------------------------------------------------------------

def test_r4_the_e_interval_is_exact_and_names_its_binding_constraint():
    got = bvr.e_interval(0.4, 60.0, ENVELOPES, e_max=E_MAX)
    lo, hi, lo_key, hi_key = got
    assert lo < hi
    # el borde es exactamente donde la lectura toca su envolvente
    assert bvr.retained_share(lo, 0.4, 60.0, 30.0) == pytest.approx(ENVELOPES[30][0], abs=1e-12)
    assert bvr.retained_share(hi, 0.4, 60.0, 120.0) == pytest.approx(ENVELOPES[120][1], abs=1e-12)
    assert (lo_key, hi_key) == (30, 120)


def test_r5_the_lowest_admissible_e_is_bounded_away_from_the_provisional_reference():
    best = min(r[0] for r in (bvr.e_interval(s / 100, float(t), ENVELOPES, e_max=E_MAX)
                              for s in range(1, 100) for t in range(1, 601))
               if r != bvr.EMPTY)
    assert best > ENVELOPES["peak"][0]            # e > 0,15 analíticamente, para todo (s, τ)
    assert best / ba.REFERENCE["crystalloid_effective_ml_per_ml"] > 1.19


def test_r6_the_region_is_disconnected_in_a_narrow_band_of_s():
    """A s ~ 0,85 hay un hueco real en τ: FD-BLD-05@60 por abajo pide más que FD-BLD-04 por arriba."""
    assert bvr.e_interval(0.85, 5.0, ENVELOPES, e_max=E_MAX) != bvr.EMPTY
    assert bvr.e_interval(0.85, 15.0, ENVELOPES, e_max=E_MAX) == bvr.EMPTY
    assert bvr.e_interval(0.85, 60.0, ENVELOPES, e_max=E_MAX) != bvr.EMPTY
    # fuera de esa banda no hay hueco: la viabilidad es un intervalo en tau
    def feasible(s, tau):
        return bvr.e_interval(s, tau, ENVELOPES, e_max=E_MAX) != bvr.EMPTY
    for s in (0.5, 0.7):
        taus = [t / 2 for t in range(2, 1201)]
        ok = [t for t in taus if feasible(s, t)]
        assert ok and len(ok) == len(taus), s          # viable en todo tau explorado
    # y a s = 0,95 lo que hay es un SUELO en tau, no un hueco: nada por debajo, todo por encima
    taus = [t / 2 for t in range(2, 1201)]
    ok = [t for t in taus if feasible(0.95, t)]
    assert ok and ok == [t for t in taus if t >= min(ok)], (min(ok), len(ok))
    assert min(ok) > 15.0


# R3 - la transformada --------------------------------------------------------------------------------

def test_r7_the_inverse_transform_is_one_to_one():
    worst = 0.0
    for e, s, tau in ((0.22, 0.4, 60.0), (0.18, 0.2, 30.0), (0.30, 0.8, 120.0),
                      (0.17, 0.6, 200.0), (0.25, 0.5, 45.0)):
        b = bvr.behaviour(e, s, tau)
        e2, s2, tau2 = bvr.invert(b["peak"], b[30.0], b[120.0])
        worst = max(worst, abs(e2 - e), abs(s2 - s), abs(tau2 - tau) / tau)
    assert worst < 1e-10, worst


def test_r8_the_model_cannot_produce_a_rising_retained_fraction():
    assert not bvr.behaviour_is_reachable(0.20, 0.22, 0.10)     # R30 por encima del pico
    assert not bvr.behaviour_is_reachable(0.20, 0.10, 0.12)     # R120 por encima de R30
    assert bvr.behaviour_is_reachable(0.20, 0.18, 0.10)
    with pytest.raises(ValueError):
        bvr.invert(0.20, 0.22, 0.10)


def test_r9_the_provisional_reference_sits_outside_in_behaviour_space():
    ref = ba.REFERENCE
    b = bvr.behaviour(ref["crystalloid_effective_ml_per_ml"], ref["crystalloid_transient_share"],
                      ref["crystalloid_leak_tau_min"])
    assert b["peak"] < ENVELOPES["peak"][0]        # fuera por abajo en el pico
    assert b[30.0] < ENVELOPES[30][0]              # fuera por abajo a los 30 min
    assert ENVELOPES[120][0] <= b[120.0] <= ENVELOPES[120][1]   # dentro sólo a los 120 min
    assert b["peak"] == pytest.approx(0.103833, abs=1e-5)


# R4 - FD-BLD-06 reducida -----------------------------------------------------------------------------

def test_r10_the_dilution_peak_is_a_function_of_the_retained_peak_alone():
    """Por eso FD-BLD-06 se reduce a un techo sobre Rpico: a Rpico fijo no distingue (s, τ)."""
    seen = []
    for s, tau in ((0.2, 30.0), (0.6, 120.0), (0.9, 200.0)):
        e = 0.30 / bvr.peak_share(1.0, s, tau)
        row = bc.evaluate(bc.CASES[0], {"crystalloid_effective_ml_per_ml": e,
                                        "crystalloid_transient_share": s,
                                        "crystalloid_leak_tau_min": tau})["rows"]["crystalloid"]
        seen.append((row[1000.0]["peak"], row[2000.0]["peak"]))
    spread_1l = max(v[0] for v in seen) - min(v[0] for v in seen)
    spread_2l = max(v[1] for v in seen) - min(v[1] for v in seen)
    assert spread_1l < 1e-4 and spread_2l < 1e-4, (spread_1l, spread_2l)


def test_r11_the_measured_peak_ceiling_brackets_the_two_litre_envelope():
    top = bc.DECISIONS["FD-BLD-06"]["envelopes"][2000][1]
    def dil2l(peak):
        e = peak / bvr.peak_share(1.0, 0.4, 60.0)
        return bc.evaluate(bc.CASES[0], {"crystalloid_effective_ml_per_ml": e,
                                         "crystalloid_transient_share": 0.4,
                                         "crystalloid_leak_tau_min": 60.0}
                           )["rows"]["crystalloid"][2000.0]["peak"]
    assert dil2l(PEAK_CEILING_57M - 0.005) <= top
    assert dil2l(PEAK_CEILING_57M + 0.005) > top
    assert bvr.peak_ceiling_from_dilution(PEAK_CEILING_57M) == PEAK_CEILING_57M
    assert PEAK_CEILING_57M < ENVELOPES["peak"][1]      # recorta de verdad la caja de FD-BLD-04


# R5 - disciplina de la herramienta -------------------------------------------------------------------

def test_r12_the_module_imports_neither_the_core_nor_the_authority_registry():
    tree = ast.parse(open(bvr.__file__, encoding="utf-8").read())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    assert not any(n.startswith(("clinical_core", "runtime_authority", "runtime_shadow"))
                   for n in names), names
    out = subprocess.run([sys.executable, "-c",
                          "import blood_volume_region, sys; "
                          "print(any(m.startswith('clinical_core') for m in sys.modules))"],
                         capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "False", out.stdout


def test_r13_the_tool_refuses_to_supply_faculty_values_by_itself():
    with pytest.raises(ValueError):
        bvr.e_interval(0.4, 60.0, {}, e_max=E_MAX)
    with pytest.raises(ValueError):
        bvr.peak_ceiling_from_dilution(0.0)
    with pytest.raises(ValueError):
        bvr.decay(0.0)
    with pytest.raises(ValueError):
        bvr.coefficient(1.5, 60.0, 30.0)
    with pytest.raises(ValueError):
        bvr.coefficient(0.4, 60.0, 10.0)        # antes del final de la infusión no hay forma cerrada


def test_r14_no_optimiser_or_recommendation_names_in_the_tool():
    source = open(bvr.__file__, encoding="utf-8").read().lower()
    for banned in ("optimi", "recommend", "best_", "approve", "ranking", "score"):
        assert banned not in source, banned
