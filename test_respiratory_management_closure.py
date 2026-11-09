"""P3-129 a P3-131: la causalidad de manejo respiratorio, cerrada sobre la enmienda.

Corre la MISMA region de transmision en las dos familias respiratorias, sin ajustar ninguna aparte, y
comprueba la cadena entera: disponibilidad central -> FR -> W -> PaCO2 -> SpO2. El punto educativo que
cierra el ciclo: el oxigeno puede mejorar la saturacion mientras la falla ventilatoria sigue ahi.

Region y testigos: respiratory_transmission_record. Enmienda: PHASE2_AMENDMENT_1.
"""
import dataclasses

import pytest

import management_causality as mc
import respiratory_transmission_record as rec
import runtime_shadow as rs
import runtime_shadow_families as fam
from clinical_core import asthma_migration as am
from clinical_core import derived as dv
from clinical_core import integration
from clinical_core import opioid_migration as om

FIELD = "hypoventilation_oxygenation_transmission_fraction"
R = rec.AMENDED_REGION_DECLARED_R
WITNESSES = rec.WITNESSES
MINUTES = 90


def _run(migration, adapter_cls, case, fraction, *, events=(), minutes=MINUTES):
    profile = dataclasses.replace(migration.profile(), respiratory_quotient=R, **{FIELD: fraction})

    class Local(adapter_cls):
        def profile(self, point):
            return profile

    adapter = Local()
    anchors = adapter.anchors(case, fam.COMMITTED, None)
    writers = tuple(adapter.writers(case, fam.COMMITTED, None))
    built = tuple(adapter.interventions(list(events), None)[0]) if events else ()
    trajectory = integration.run(anchors, writers + built, minutes, profile)
    series: dict = {}
    readings = trajectory.derived()
    for minute in range(1, minutes + 1):
        for key, value in readings[minute].to_dict().items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                series.setdefault(key, {})[minute] = float(value)
    series["paco2"] = {minute: dv.respiration(trajectory.states[minute], anchors, profile).paco2
                       for minute in range(1, minutes + 1)}
    series["ventilation"] = {minute: profile.paco2_reference_mmhg / series["paco2"][minute]
                             for minute in range(1, minutes + 1)}
    return series, trajectory


def _opioid(fraction, **kw):
    return _run(om, fam.OpioidAdapter, "opioid_35m", fraction, **kw)[0]


def _oxygen(minute=10, fio2=0.40):
    return [rs.MirroredAction("o1", minute, "oxygen", {"type": "oxygen"}, {}, fio2)]


def _naloxone(minute=20):
    return [rs.MirroredAction("n1", minute, "naloxone", {"type": "naloxone"}, {}, 0.21)]


# P3-129 -- la cadena opioide completa, en cada testigo de la region --------------------------------

@pytest.fixture(scope="module")
def arms():
    out = {}
    for name, fraction in WITNESSES.items():
        out[name] = {
            "untreated": _opioid(fraction),
            "oxygen": _opioid(fraction, events=_oxygen()),
            "naloxone": _opioid(fraction, events=_naloxone()),
            "both": _opioid(fraction, events=_oxygen() + _naloxone()),
            "late": _opioid(fraction, events=_naloxone(60)),
        }
    return out


@pytest.mark.parametrize("witness", sorted(WITNESSES))
def test_p3_129a_untreated_worsens_on_every_channel(arms, witness):
    series = arms[witness]["untreated"]
    assert series["respiratory_rate"][MINUTES] < series["respiratory_rate"][1]
    assert series["ventilation"][MINUTES] < series["ventilation"][1]
    assert series["paco2"][MINUTES] > series["paco2"][1]
    assert series["spo2"][MINUTES] < series["spo2"][1]
    assert mc.monotone_after(series["paco2"], 1, rising=True)


@pytest.mark.parametrize("witness", sorted(WITNESSES))
def test_p3_129b_oxygen_lifts_saturation_and_leaves_ventilation_alone(arms, witness):
    base, treated = arms[witness]["untreated"], arms[witness]["oxygen"]
    assert mc.direction(treated["spo2"], base["spo2"], MINUTES, better="higher")
    assert mc.untouched(treated["respiratory_rate"], base["respiratory_rate"], tolerance=1e-9)
    assert mc.untouched(treated["paco2"], base["paco2"], tolerance=1e-9)
    assert mc.untouched(treated["ventilation"], base["ventilation"], tolerance=1e-9)


@pytest.mark.parametrize("witness", sorted(WITNESSES))
def test_p3_129c_the_ventilatory_correction_runs_the_whole_chain_in_order(arms, witness):
    base, treated = arms[witness]["untreated"], arms[witness]["naloxone"]
    # nada antes de darla
    for channel in ("respiratory_rate", "paco2", "spo2"):
        assert mc.no_effect_before(treated[channel], base[channel], 20), channel
    # y despues, en el orden de la fisiologia: ventilacion arriba, PaCO2 abajo, oxigenacion arriba
    assert mc.direction(treated["respiratory_rate"], base["respiratory_rate"], MINUTES, better="higher")
    assert mc.direction(treated["ventilation"], base["ventilation"], MINUTES, better="higher")
    assert treated["paco2"][MINUTES] < base["paco2"][MINUTES]
    assert mc.direction(treated["spo2"], base["spo2"], MINUTES, better="higher")
    assert mc.no_paradox(treated["spo2"], base["spo2"], 20, better="higher")


@pytest.mark.parametrize("witness", sorted(WITNESSES))
def test_p3_129d_the_saturation_gain_is_measurable_and_grows_with_the_region(arms, witness):
    base, treated = arms[witness]["untreated"], arms[witness]["naloxone"]
    assert treated["spo2"][MINUTES] - base["spo2"][MINUTES] > 0.5, witness


def test_p3_129e_the_gain_is_monotone_across_the_witnesses(arms):
    gains = [arms[name]["naloxone"]["spo2"][MINUTES] - arms[name]["untreated"]["spo2"][MINUTES]
             for name in ("LOW", "CENTER_REFERENCE", "HIGH")]
    assert all(b > a for a, b in zip(gains, gains[1:])), gains


def test_p3_129f_there_is_no_direct_write_from_the_reversal_to_saturation():
    """La prueba que lo demuestra: a transmision CERO la reversion no mueve la SpO2 en absoluto.

    Si existiera una escritura directa, aqui se veria. La mejora de oxigenacion de los testigos viene
    entera por el PaCO2, que es lo que la enmienda autoriza y nada mas.
    """
    base = _opioid(0.0)
    treated = _opioid(0.0, events=_naloxone())
    assert mc.untouched(treated["spo2"], base["spo2"], tolerance=1e-12)
    # y aun asi la ventilacion si se corrige: la rama existe, solo no llega a la oxigenacion
    assert treated["respiratory_rate"][MINUTES] > base["respiratory_rate"][MINUTES]
    assert treated["paco2"][MINUTES] < base["paco2"][MINUTES]


@pytest.mark.parametrize("witness", sorted(WITNESSES))
def test_p3_129g_both_treatments_together_carry_both_mechanisms(arms, witness):
    both = arms[witness]["both"]
    oxygen, naloxone = arms[witness]["oxygen"], arms[witness]["naloxone"]
    assert both["respiratory_rate"][MINUTES] == pytest.approx(naloxone["respiratory_rate"][MINUTES])
    assert both["paco2"][MINUTES] == pytest.approx(naloxone["paco2"][MINUTES])
    assert both["spo2"][MINUTES] > max(oxygen["spo2"][MINUTES], naloxone["spo2"][MINUTES])


@pytest.mark.parametrize("witness", sorted(WITNESSES))
def test_p3_129h_waiting_costs_both_ventilation_and_oxygenation(arms, witness):
    early, late = arms[witness]["naloxone"], arms[witness]["late"]
    for channel in ("respiratory_rate", "spo2"):
        area_early = sum(early[channel][m] for m in range(1, MINUTES + 1))
        area_late = sum(late[channel][m] for m in range(1, MINUTES + 1))
        assert area_late < area_early, channel
    # y tambien cuesta en el PaCO2: esperar deja mas carga acumulada
    assert (sum(late["paco2"][m] for m in range(1, MINUTES + 1))
            > sum(early["paco2"][m] for m in range(1, MINUTES + 1)))


# P3-130 -- la misma region en asma, sin ajuste propio ----------------------------------------------

@pytest.mark.parametrize("case", ["asthma_49m", "asthma_24f"])
@pytest.mark.parametrize("witness", sorted(WITNESSES))
def test_p3_130_the_same_region_generalizes_to_asthma(case, witness):
    fraction = WITNESSES[witness]
    off = _run(am, fam.AsthmaAdapter, case, 0.0)[0]
    on = _run(am, fam.AsthmaAdapter, case, fraction)[0]
    # la llegada certificada sigue en pie y la direccion del PaCO2 se preserva
    assert on["spo2"][1] == pytest.approx(off["spo2"][1], abs=0.2)
    assert on["paco2"][MINUTES] == pytest.approx(off["paco2"][MINUTES], abs=1e-9)
    assert on["respiratory_rate"][MINUTES] == pytest.approx(off["respiratory_rate"][MINUTES], abs=1e-9)
    # la oxigenacion se mueve poco y siempre a la baja: ninguna hipoxemia grave nueva, ningun limite
    shift = on["spo2"][MINUTES] - off["spo2"][MINUTES]
    assert -1.0 < shift <= 0.0, (case, witness, shift)
    assert on["spo2"][MINUTES] > 78.0


# P3-131 -- el contraste educativo -----------------------------------------------------------------

def test_p3_131_oxygen_can_make_saturation_look_better_while_ventilation_still_fails():
    """El punto de ensenanza del ciclo, en una sola prueba y con los cinco canales."""
    fraction = WITNESSES["CENTER_REFERENCE"]
    base = _opioid(fraction)
    with_oxygen = _opioid(fraction, events=_oxygen())
    corrected = _opioid(fraction, events=_naloxone())

    # el oxigeno mejora lo que se MIRA en el monitor
    assert with_oxygen["spo2"][MINUTES] > base["spo2"][MINUTES]
    assert with_oxygen["delivery_rel"][MINUTES] >= base["delivery_rel"][MINUTES]
    # y no toca nada de lo que esta fallando de verdad
    assert with_oxygen["respiratory_rate"][MINUTES] == pytest.approx(base["respiratory_rate"][MINUTES])
    assert with_oxygen["ventilation"][MINUTES] == pytest.approx(base["ventilation"][MINUTES])
    assert with_oxygen["paco2"][MINUTES] == pytest.approx(base["paco2"][MINUTES])
    # el PaCO2 sigue subiendo bajo oxigeno: la falla ventilatoria PERSISTE mientras la cifra mejora
    assert with_oxygen["paco2"][MINUTES] > with_oxygen["paco2"][1]
    assert mc.monotone_after(with_oxygen["paco2"], 1, rising=True)
    # la correccion ventilatoria, en cambio, es la unica que baja el PaCO2
    assert corrected["paco2"][MINUTES] < base["paco2"][MINUTES]
    assert corrected["paco2"][MINUTES] < with_oxygen["paco2"][MINUTES]
    # y las dos suben la SpO2, que es exactamente por lo que la cifra sola no distingue
    assert with_oxygen["spo2"][MINUTES] > base["spo2"][MINUTES]
    assert corrected["spo2"][MINUTES] > base["spo2"][MINUTES]


def test_p3_131b_the_record_states_the_region_and_what_it_does_not_identify():
    assert rec.AMENDED_COMMON_REGION == (0.0, 0.060621)
    assert rec.AMENDED_REGION_IDENTIFIES_ONLY.startswith("the ratio")
    assert rec.AMENDED_DEVELOPMENT_DECISION["is_clinical_truth"] is False
    assert rec.AMENDED_DEVELOPMENT_DECISION["confidence"] >= 0.80
    assert rec.AMENDED_PER_CASE["opioid_35m"]["binds_the_common_region"] is True
    for value in WITNESSES.values():
        assert 0.0 < value <= rec.AMENDED_COMMON_REGION[1]
