"""Enmienda 2 (terminal y consciencia, GI primero) · A2-011 y A2-012: auditoria de escalas, SOLO LECTURA.

Fija, contra el nucleo certificado de la Enmienda 1, por que la deuda D existente NO expresa la temporalidad que la
docencia pidio para la consciencia sistemica (decision A2-FD-004), y por que el indice de aporte de los casos de GI
no es comparable con «% de lo normal». No cambia el nucleo: ninguna prueba aqui escribe estado.

Veredicto de A2-012: EXISTING_DEBT_STATE_INSUFFICIENT_FOR_CONSCIOUSNESS_TEMPORALITY.
Registro: docs/revision/PHASE2_AMENDMENT_2_A2_011_012.md.
"""
import dataclasses
import math
from pathlib import Path

import pytest

from clinical_core import collapse, derived as dv, encephalopathy
from clinical_core.state import AuxiliaryState

ROOT = Path(__file__).resolve().parent
PROFILE = dv.DEFAULT_PROFILE
#: Las regiones de comportamiento que definio la docencia (A2-FD-004), en indice de aporte y en minutos.
EARLY, SEVERE, RECOVERY = (0.35, 0.45), (0.20, 0.25), (0.50, 0.60)
ONSET_MINUTES, RECOVERY_MINUTES = (2, 4), (3, 5)


def _deficit(delivery, demand=1.0):
    return dv.effective_oxygen_deficit(demand, delivery, PROFILE.oxygen_extraction_reserve)


def _debt_after(minutes, delivery):
    """D tras ``minutes`` de un aporte sostenido, desde 0, por la ecuacion del nucleo: dD = g x deficit."""
    return PROFILE.debt_per_delivery_deficit * _deficit(delivery) * minutes


def test_a2_011_the_scales_of_the_committed_profile():
    assert (PROFILE.oxygen_extraction_reserve, PROFILE.debt_per_delivery_deficit, PROFILE.debt_clearance_tau_min) == (
        1.0, 1.0, 60.0)
    for name in ("oxygen_extraction_reserve", "debt_per_delivery_deficit", "debt_clearance_tau_min"):
        assert dv.PARAMETERS[name][0] == dv.PROVISIONAL, name
    assert "60 min is not approved" in dv.PARAMETERS["debt_clearance_tau_min"][1]
    # el deficit es lineal en el aporte y empieza en cuanto el aporte baja de la demanda (reserva 1)
    assert _deficit(1.0) == 0.0 and _deficit(0.999) > 0.0
    assert _deficit(0.40) == pytest.approx(0.60) and _deficit(0.22) == pytest.approx(0.78)
    # la escalera directa que la enmienda debe reemplazar, y de donde salio
    assert PROFILE.pressure_levels == ((80.0, 1), (65.0, 2)) and PROFILE.oxygen_levels == ((87.0, 1), (80.0, 2))
    assert dv.PARAMETERS["pressure_levels"][0] == dv.ADOPTED and "family_engine" in dv.PARAMETERS["pressure_levels"][1]
    # PHASE2_AMENDMENT_2: this audit documents the tree BEFORE the amendment (the first amendment's), so it reads that text.
    from clinical_core import amendment_2 as a2
    source = a2.a1_text("clinical_core/derived.py")
    assert ("level = max(anchors.consciousness_level, _level(sbp, profile.pressure_levels), "
            "_level(spo2, profile.oxygen_levels))") in source


def test_a2_012_the_debt_has_no_severity_gate():
    """El mismo D se alcanza con un deficit grave y breve o con uno leve y largo: D no distingue gravedad."""
    target = _debt_after(3, 0.40)                              # «aporte 40 % sostenido 3 minutos»
    assert target == pytest.approx(1.8)
    minutes = {delivery: target / (PROFILE.debt_per_delivery_deficit * _deficit(delivery))
               for delivery in (0.60, 0.80, 0.90, 0.97)}
    assert minutes[0.90] == pytest.approx(18.0) and minutes[0.97] == pytest.approx(60.0)
    # todos esos aportes estan POR ENCIMA de la region de recuperacion de la docencia, y aun asi llegan al mismo D
    assert all(delivery >= RECOVERY[1] for delivery in minutes) and all(value < 61 for value in minutes.values())


def test_a2_012_the_debt_cannot_express_the_persistence_window():
    """En el curso de GI comprometido el aporte baja despacio: cuando por fin cruza la region temprana, D ya es
    decenas de veces el D de «3 minutos al 40 %». Una condicion sobre D esta cumplida de antemano: no hay ventana."""
    # el curso medido del caso comprometido, por la ecuacion: el aporte cae ~0,003 por minuto desde 1
    debt, delivery, minute = 0.0, 1.0, 0
    while delivery > EARLY[1]:
        debt += PROFILE.debt_per_delivery_deficit * _deficit(delivery)
        delivery -= 0.0029
        minute += 1
    assert minute > 180 and debt > 25 * _debt_after(3, 0.40)


def test_a2_012_the_debt_recovers_only_at_full_delivery_and_over_an_hour():
    # con el aporte «restaurado» al 60 % sigue habiendo deficit: D sigue SUBIENDO, no se recupera
    assert _deficit(RECOVERY[1]) > 0 and _debt_after(1, RECOVERY[1]) > 0
    assert 1.0 / PROFILE.oxygen_extraction_reserve == 1.0            # solo se repaga con aporte >= 100 %
    kept = math.exp(-RECOVERY_MINUTES[1] / PROFILE.debt_clearance_tau_min)
    assert kept > 0.9                                               # y en 5 minutos queda mas del 90 %
    integration = (ROOT / "clinical_core" / "integration.py").read_text(encoding="utf-8")
    assert '"no unmet demand: first-order repayment"' in integration
    assert "accrued, not repaid" in integration


def test_a2_012_no_existing_state_carries_a_consciousness_memory():
    from clinical_core import systemic_consciousness as sc
    fields = {item.name for item in dataclasses.fields(AuxiliaryState)} - {sc.STATE_FIELD}   # the pre-amendment state
    assert "collapse_burden" in fields                               # el colapso SI tiene su memoria en el estado
    assert not [name for name in fields if "enceph" in name or "conscious" in name or "brain" in name]
    # la memoria que la docencia diseño en P2L-2 existe como capa candidata, fuera del estado y sin magnitudes
    profile = encephalopathy.DEFAULT_ENCEPHALOPATHY
    assert profile.mappings == () and not profile.memory_declared
    assert "distinct from N, from D" in (ROOT / "clinical_core" / "encephalopathy.py").read_text(encoding="utf-8")


def test_a2_012_the_behaviour_inverts_cleanly_on_the_candidate_memory_and_one_tension_remains():
    """En papel, sin implementar: la memoria candidata F (relaja hacia la senal aguda S) SI expresa la conducta."""
    rise = tuple(minutes / math.log(5) for minutes in ONSET_MINUTES)          # S = 1 lleva F a 0,80 en 2-4 min
    assert rise == pytest.approx((1.2427, 2.4853), abs=1e-3)
    clear = tuple(minutes / math.log(1.6) for minutes in RECOVERY_MINUTES)    # de 0,80 a 0,50 en 3-5 min con S = 0
    assert clear == pytest.approx((6.383, 10.638), abs=1e-3) and clear[0] > rise[1]
    made = encephalopathy.EncephalopathyProfile(
        mappings=(("oxygen_deficit", encephalopathy.SignalMapping(normal=0.52, severe=0.775)),),
        burden_rise_tau=3 / math.log(5), burden_clear_tau=4 / math.log(1.6))
    severe = encephalopathy.burden_course([1.0] * 3, 1.0, made)[-1]
    assert severe == pytest.approx(0.80, abs=1e-9)
    early = encephalopathy.ramp(_deficit(0.40), made.mapping("oxygen_deficit"), encephalopathy.HIGH)
    assert encephalopathy.burden_course([early] * 3, 1.0, made)[-1] == pytest.approx(0.25, abs=0.01)
    assert encephalopathy.ramp(_deficit(0.55), made.mapping("oxygen_deficit"), encephalopathy.HIGH) == 0.0
    recovered = encephalopathy.burden_course([0.0] * 4, 1.0, made, initial=0.80)[-1]
    assert recovered == pytest.approx(0.50, abs=1e-9)
    # la tension: con esas constantes, UN minuto de fallo extremo ya da un deterioro observable
    one_minute = [1 - math.exp(-1 / tau) for tau in rise]
    assert min(one_minute) > 0.25 and max(one_minute) > 0.50


def test_a2_012_the_delivery_index_of_the_gi_cases_is_not_a_percentage_of_normal():
    source = (ROOT / "clinical_core" / "derived.py").read_text(encoding="utf-8")
    assert '"arrival_delivery_ratio": "not declared: arrival delivery read as adequate"' in source
    assert "return anchors.arrival_delivery_ratio * delivery_rel" in source


def test_a2_014_the_two_collapse_structures_and_what_the_faculty_decision_asks_of_them():
    # la regla del nucleo es solo por gasto (rechazada: gasto bajo solo no es colapso) y esta apagada
    assert PROFILE.collapse_output_threshold is None and PROFILE.collapse_burden_limit is None
    # la capa candidata combina por MAXIMO (basta una señal) y mide la perfusion en mmHg absolutos
    assert collapse.signal_value(0.9, 0.0) == 0.9 and collapse.signal_value(0.0, 0.9) == 0.9
    assert {item.name for item in dataclasses.fields(collapse.PerfusionMapping)} == {"viable_map_mmhg",
                                                                                     "failed_map_mmhg"}
    assert collapse.DEFAULT_COLLAPSE.perfusion_mapping is None and not collapse.DEFAULT_COLLAPSE.kinetics_declared
