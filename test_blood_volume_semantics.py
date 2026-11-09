"""P3-69 a P3-75: fija lo medido sobre la capa semántica de volumen (análisis, sin cambiar nada).

Todo se lee del evaluador y del núcleo congelados. Ninguna prueba aprueba un parámetro ni mueve el punto de
desarrollo: fijan que el fallo de FD-BLD-04/05/06 es de REGIÓN DE PARÁMETROS y no del modelo, y que el bloque
de volumen es separable del de presión. Documento: docs/PHASE3_BLOOD_VOLUME_SEMANTICS.md
"""
import math

import pytest

from clinical_core import blood_anchors as ba
from clinical_core import blood_constraints as bc
from clinical_core import blood_extension as be

VOLUME = ("FD-BLD-04", "FD-BLD-05", "FD-BLD-06")
#: Un punto admisible del bloque de cristaloide. NO es una recomendación ni una aprobación: es el testigo de
#: que la región no es vacía (P3-73).
WITNESS_BAG = {"crystalloid_effective_ml_per_ml": 0.22, "crystalloid_transient_share": 0.4,
               "crystalloid_leak_tau_min": 60.0}
#: El mismo testigo cruzado con la cresta de U-OUT de P3-68, que satisface LAS DOCE restricciones.
WITNESS_ALL = {**WITNESS_BAG, "bleed_ml_per_min": 3.0, "preload_scale_over_kappa_ml": 1100.0,
               "preload_fraction": 0.45}
#: Medido con s = 0,6 y tau = 30 (el perfil de infusión de 20 min del evaluador).
PEAK_OVER_E, SHARE30_OVER_E = 0.830666, 0.708586


def _volume_verdicts(values, variant="primary"):
    """Veredictos de 04/05/06 exigidos en LOS DOS casos GI."""
    per = {case: dict(bc.evaluate(case, values)["verdicts"][variant]) for case in bc.CASES}
    return {name: all(per[case][name] for case in bc.CASES) for name in VOLUME}


# P3-69 - la semantica declarada ---------------------------------------------------------------------------

def test_v1_the_three_constraints_are_current_with_their_envelopes():
    """Las tres siguen en DECISIONS con sus envolventes, y el filtro declara los tres parámetros de la bolsa."""
    assert bc.DECISIONS["FD-BLD-04"]["envelope"] == (0.15, 0.30)
    assert bc.DECISIONS["FD-BLD-05"]["envelopes"] == {30: (0.15, 0.25), 60: (0.10, 0.20), 120: (0.05, 0.15)}
    assert bc.DECISIONS["FD-BLD-06"]["envelopes"] == {1000: (0.20, 0.50), 2000: (0.40, 0.80)}
    assert set(bc.BAG) == {"crystalloid_effective_ml_per_ml", "crystalloid_leak_tau_min",
                           "crystalloid_transient_share"}


def test_v2_the_evaluator_declares_its_reading_and_its_denominator():
    """El factor 0,83 del pico es el perfil DECLARADO, no un defecto: la lectura lo dice."""
    assert "20 min" in bc.IMPLEMENTATION["crystalloid"]
    assert "minutes 0-30" in bc.IMPLEMENTATION["FD-BLD-04"]
    assert "minutes 30, 60 and 120" in bc.IMPLEMENTATION["FD-BLD-05"]
    # el denominador es el litro infundido, no el volumen retenido ni la V canónica
    assert "over the volume infused (1 L)" in bc.IMPLEMENTATION["FD-BLD-04"]
    assert "over the volume infused (1 L)" in bc.IMPLEMENTATION["FD-BLD-05"]
    # FD-BLD-06 vive en otra magnitud: Hb, con reversión parcial exigida
    assert "dilution" in bc.IMPLEMENTATION["FD-BLD-06"] and "partial reversal" in bc.IMPLEMENTATION["FD-BLD-06"]


def test_v3_the_reference_value_is_documented_as_provisional_not_approved():
    """El 0,125 es un valor provisional de P2I-2T, anterior a las envolventes de P2I-2U."""
    source = open(ba.__file__, encoding="utf-8").read()
    assert "canonical provisional values (P2I-2T)" in source
    assert "neither candidate bands nor approved values" in source
    assert ba.REFERENCE["crystalloid_effective_ml_per_ml"] == 0.125
    # y el dominio declarado admite de sobra la región que sí pasa: ninguna región se amplió
    low, high, _meaning = be.DOMAIN["crystalloid_effective_ml_per_ml"]
    assert (low, high) == (0.0, 1.0)
    assert be.OPEN_EDGES["crystalloid_effective_ml_per_ml"] == "upper"


# P3-70 - balance de masa ----------------------------------------------------------------------------------

def test_v4_the_crystalloid_reading_is_exactly_linear_in_the_effective_fraction():
    """Toda la vía del cristaloide es lineal en `given · e`, así que retenido(t) = e · phi(t; s, tau)."""
    ratios = []
    for e in (0.16, 0.22, 0.30):
        row = bc.retained(bc.CASES[0], {"crystalloid_effective_ml_per_ml": e})
        ratios.append((row["early"] / e, row["share"][30] / e))
    for peak, share30 in ratios:
        assert peak == pytest.approx(PEAK_OVER_E, abs=1e-6)
        assert share30 == pytest.approx(SHARE30_OVER_E, abs=1e-6)
    # y el pico NO es `e`: la bolsa entra en 20 min mientras ya fuga
    assert PEAK_OVER_E < 1.0
    # de ahí la condición necesaria de FD-BLD-04, que el valor de referencia no puede cumplir
    assert 0.15 / PEAK_OVER_E > ba.REFERENCE["crystalloid_effective_ml_per_ml"]


def test_v5_crystalloid_switches_plasma_refill_off_so_nothing_is_counted_twice():
    """Replica la ecuación exacta de `derived`: si el cristaloide lleva volume_ml a no negativo, relleno = 0."""
    def refill(shed, volume_ml, refilled, *, capacity=1000.0, share=0.5, tau=120.0):
        target = min(capacity, share * shed)
        gap, deficit = target - refilled, -volume_ml
        if gap <= 0 or deficit <= 0:
            return 0.0
        return min(gap * -math.expm1(-1.0 / tau), deficit)

    assert refill(500.0, -400.0, 0.0) == pytest.approx(2.0747, abs=1e-4)
    assert refill(500.0, -50.0, 200.0) == pytest.approx(0.4149, abs=1e-4)
    assert refill(500.0, +100.0, 0.0) == 0.0     # el cristaloide apagó el relleno
    assert refill(500.0, -400.0, 250.0) == 0.0   # el relleno llegó a su objetivo


# P3-71 y P3-72 - atribucion y separabilidad ---------------------------------------------------------------

def test_v6_the_volume_constraints_are_invariant_to_bleeding_refill_and_pressure():
    """Separabilidad exacta: la lectura compara con bolsa contra sin bolsa AL MISMO sangrado."""
    base = bc.retained(bc.CASES[0], WITNESS_BAG)
    reference = (base["early"], base["share"][30], base["share"][60], base["share"][120])
    for key, values in (("bleed_ml_per_min", (1.5, 3.5)),
                        ("plasma_refill_target_share", (0.25, 0.75)),
                        ("plasma_refill_tau_min", (60.0, 240.0)),
                        ("arrival_circulating_volume_ml", (3000.0, 5000.0)),
                        ("preload_scale_over_kappa_ml", (600.0, 1500.0))):
        for value in values:
            row = bc.retained(bc.CASES[0], {**WITNESS_BAG, key: value})
            assert (row["early"], row["share"][30], row["share"][60],
                    row["share"][120]) == reference, key


def test_v7_no_parameter_other_than_the_effective_fraction_rescues_the_constraints():
    """A e = 0,125, mover relleno, tau, share, sangrado o la unidad de glóbulos no cambia ningún veredicto."""
    for key, value in (("crystalloid_transient_share", 0.2), ("crystalloid_leak_tau_min", 120.0),
                       ("plasma_refill_target_share", 0.8), ("bleed_ml_per_min", 1.5),
                       ("red_cell_unit_volume_ml", 400.0)):
        assert _volume_verdicts({key: value}) == {name: False for name in VOLUME}, key


# P3-73 - region factible ----------------------------------------------------------------------------------

def test_v8_the_reference_point_fails_all_three_in_every_declared_reading():
    """Fuera de la región, en los dos casos y en las diez lecturas (primary y las nueve variantes)."""
    per = {case: bc.evaluate(case, {})["verdicts"] for case in bc.CASES}
    assert len(per[bc.CASES[0]]) == 10
    for variant in per[bc.CASES[0]]:
        for case in bc.CASES:
            verdict = dict(per[case][variant])
            assert [verdict[name] for name in VOLUME] == [False, False, False], (case, variant)


def test_v9_the_region_is_not_empty_in_every_declared_reading():
    """El testigo satisface LAS DOCE restricciones en los dos casos y en las diez lecturas."""
    for case in bc.CASES:
        verdicts = bc.evaluate(case, WITNESS_ALL)["verdicts"]
        assert len(verdicts) == 10
        for variant, verdict in verdicts.items():
            failing = sorted(name for name, ok in dict(verdict).items() if ok is False)
            assert failing == [], (case, variant, failing)


def test_v10_the_admissible_fraction_is_bounded_on_both_sides():
    """FD-BLD-04 acota `e` por abajo y por arriba: no es «cuanto más, mejor»."""
    assert _volume_verdicts({**WITNESS_BAG, "crystalloid_effective_ml_per_ml": 0.125}) == {
        name: False for name in VOLUME}
    too_high = _volume_verdicts({**WITNESS_BAG, "crystalloid_effective_ml_per_ml": 0.50})
    assert too_high["FD-BLD-04"] is False

