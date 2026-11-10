"""P3-104 a P3-114: causalidad de manejo, por familia y entre familias.

No puntúa contra curvas del legado. Comprueba DIRECCIÓN, TEMPORALIDAD, ESPECIFICIDAD CAUSAL, ORDEN DE DOSIS,
COSTE DE ESPERAR, AUSENCIA DE PARADOJA y los huecos **declarados**. Usa sólo casos ya certificados.
Documento: docs/PHASE3_MANAGEMENT_CAUSALITY.md
"""
import dataclasses

import pytest

import management_causality as mc
import runtime_shadow as rs
import runtime_shadow_families as fam

MINUTES = 120


def _series(family, case, events=(), state=None, minutes=MINUTES, adapter=None):
    """{lectura: {minuto: valor}} de una corrida de sombra, más el runner para leer huecos y fallos."""
    runner = (fam.ShadowPhysiologyRunner.open(family, case, state=state) if adapter is None
              else _open_with(adapter, case, state))
    assert runner is not None and not runner.failures, (family, case, runner and runner.failures)
    runner.mirror(list(events))
    for minute in range(1, minutes + 1):
        runner.advance(minute, state=state)
    out: dict = {}
    for result in runner.results:
        for key, value in dict(result.derived).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                out.setdefault(key, {})[result.minute] = float(value)
    return out, runner


def _open_with(adapter, case, state):
    runner = fam.ShadowPhysiologyRunner(adapter, case, fam.COMMITTED)
    runner.snapshot_ = adapter.snapshot()
    runner.anchors = adapter.anchors(case, fam.COMMITTED, dict(state) if state else None)
    runner.profile = adapter.profile(fam.COMMITTED)
    runner.family_writers = tuple(adapter.writers(case, fam.COMMITTED, dict(state) if state else None))
    return runner


def _fluid(order_id, minute, litres=1.0):
    return rs.MirroredAction(order_id, minute, "fluid",
                             {"type": "fluid", "volume_ml": 1000.0 * litres}, {}, 0.21)


def _blood(order_id, minute, units=2):
    return rs.MirroredAction(order_id, minute, "blood", {"type": "blood", "units": units}, {}, 0.21)


def _oxygen(order_id, minute, fio2=0.40):
    return rs.MirroredAction(order_id, minute, "oxygen", {"type": "oxygen"}, {}, fio2)


def _naloxone(order_id, minute):
    return rs.MirroredAction(order_id, minute, "naloxone", {"type": "naloxone"}, {}, 0.21)


# C1 - el contrato -------------------------------------------------------------------------------------

def test_c1_the_contract_is_a_specification_with_no_disease_numbers():
    assert len(mc.STANDARD) == 9 and len(mc.MANAGEMENT_CAUSALITY_CONTRACT) == 8
    source = open(mc.__file__, encoding="utf-8").read()
    for label in mc.FORBIDDEN_LABELS:
        assert source.count(label) == 1, label          # sólo en la lista que los prohíbe
    # ningún número de enfermedad en el contrato común
    for text in mc.MANAGEMENT_CAUSALITY_CONTRACT.values():
        assert not any(ch.isdigit() for ch in text), text
    # y el módulo no importa el núcleo ni la capa de sombra
    import ast
    names = {n.module or "" for n in ast.walk(ast.parse(source)) if isinstance(n, ast.ImportFrom)}
    names |= {a.name for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Import) for a in n.names}
    assert not any(x.startswith(("clinical_core", "runtime_")) for x in names), names


# C2..C6 - GI: la familia de referencia (P3-106) -------------------------------------------------------

@pytest.fixture(scope="module")
def gi_untreated():
    return _series("gi_bleed", "gi_bleed_57m")[0]


def test_c2_gi_fluid_improves_pressure_after_it_is_given_and_not_before(gi_untreated):
    treated, runner = _series("gi_bleed", "gi_bleed_57m", [_fluid("f1", 30)])
    assert runner.gaps == []
    assert mc.no_effect_before(treated["sbp"], gi_untreated["sbp"], 30)
    assert mc.effect_starts_at(treated["sbp"], gi_untreated["sbp"], 30) >= 30
    assert mc.direction(treated["sbp"], gi_untreated["sbp"], 90, better="higher")
    assert mc.no_paradox(treated["sbp"], gi_untreated["sbp"], 30, better="higher")


def test_c3_gi_blood_improves_and_more_units_are_not_less_effect(gi_untreated):
    by_dose = {}
    for units in (1, 2, 4):
        by_dose[units] = _series("gi_bleed", "gi_bleed_57m", [_blood(f"b{units}", 20, units)])[0]["sbp"]
    assert mc.direction(by_dose[2], gi_untreated["sbp"], 90, better="higher")
    assert mc.dose_ordered(by_dose, 90, better="higher")
    assert mc.no_effect_before(by_dose[2], gi_untreated["sbp"], 20)


def test_c4_gi_source_control_reduces_the_deterioration(gi_untreated):
    state = dict(_bank("gi_bleed_57m"))
    state.setdefault("family_state", {})["endoscopy_at"] = 40
    controlled = _series("gi_bleed", "gi_bleed_57m", [], state=state)[0]
    assert mc.no_effect_before(controlled["sbp"], gi_untreated["sbp"], 40)
    assert mc.direction(controlled["sbp"], gi_untreated["sbp"], 120, better="higher")


def test_c5_gi_waiting_has_a_causal_cost_in_the_integral_not_at_the_endpoint(gi_untreated):
    """Medido: para un tratamiento TRANSITORIO contra un sangrado que sigue, esperar cuesta el AREA.

    En un minuto tardío la bolsa puesta tarde todavía actúa y la puesta pronto ya fugó, así que el punto
    final favorece al tardío. Lo que el residente le quita al paciente esperando es el tiempo que pasó
    por debajo, y eso es la integral.
    """
    now = _series("gi_bleed", "gi_bleed_57m", [_fluid("f-now", 10)])[0]["sbp"]
    later = _series("gi_bleed", "gi_bleed_57m", [_fluid("f-late", 60)])[0]["sbp"]
    area = lambda s: sum(s.values()) / len(s)
    assert area(now) > area(later) > area(gi_untreated["sbp"])
    # y el punto final NO lo muestra: por eso la prueba no se escribe sobre un minuto
    assert later[120] > now[120]
    assert mc.direction(later, gi_untreated["sbp"], 120, better="higher")   # tarde sigue siendo mejor que nada


def test_c6_gi_the_whole_bundle_beats_any_single_part(gi_untreated):
    bundle = _series("gi_bleed", "gi_bleed_57m",
                     [_fluid("f1", 10), _blood("b1", 15, 2), _oxygen("o1", 5)])[0]["sbp"]
    only_fluid = _series("gi_bleed", "gi_bleed_57m", [_fluid("f1", 10)])[0]["sbp"]
    assert mc.direction(bundle, only_fluid, 120, better="higher")
    assert mc.direction(bundle, gi_untreated["sbp"], 120, better="higher")


# C7..C8 - ACS (P3-107) --------------------------------------------------------------------------------

def test_c7_acs_reperfusion_acts_on_the_engines_own_clock_and_never_instantly():
    plain = _series("acs", "acs_70f_left_main", state={"family_state": {}})[0]
    opened = _series("acs", "acs_70f_left_main", state={"family_state": {"reperfusion_at": 60}})[0]
    assert mc.no_effect_before(opened["sbp"], plain["sbp"], 60)
    assert mc.effect_starts_at(opened["sbp"], plain["sbp"], 60) == 60
    assert mc.direction(opened["sbp"], plain["sbp"], 120, better="higher")
    # gradual, no una normalización instantánea: el primer minuto mueve mucho menos que una hora después
    first = opened["sbp"][60] - plain["sbp"][60]
    later = opened["sbp"][120] - plain["sbp"][120]
    assert 0.0 < first < later / 10.0
    # y llega aguas abajo, al relleno capilar, no por una escritura directa de presión
    assert mc.direction(opened["crt_s"], plain["crt_s"], 120, better="lower")


def test_c8_acs_oxygen_acts_through_gas_exchange_and_gives_no_pump_benefit():
    """Medido: el oxígeno sube SpO2 y la entrega, baja el lactato, y BAJA la presión.

    El camino es el correcto —mejor oxigenación tisular, menos impulso simpático— así que su efecto sobre
    la presión es una consecuencia aguas abajo y de signo OPUESTO a un beneficio de bomba, y un orden de
    magnitud menor que la reperfusión. Exigir inmovilidad sería exigir que el oxígeno no haga nada.
    """
    plain = _series("acs", "acs_70f_left_main", state={"family_state": {}})[0]
    with_o2 = _series("acs", "acs_70f_left_main", [_oxygen("o1", 10, 0.40)],
                      state={"family_state": {}})[0]
    opened = _series("acs", "acs_70f_left_main", state={"family_state": {"reperfusion_at": 60}})[0]
    # primero el intercambio gaseoso, y nada antes de la orden
    assert mc.no_effect_before(with_o2["spo2"], plain["spo2"], 10)
    assert mc.direction(with_o2["spo2"], plain["spo2"], 120, better="higher")
    assert mc.direction(with_o2["delivery_rel"], plain["delivery_rel"], 120, better="higher")
    assert mc.direction(with_o2["lactate"], plain["lactate"], 120, better="lower")
    # ningun beneficio de bomba: la presion NO sube con oxigeno
    assert not mc.direction(with_o2["sbp"], plain["sbp"], 120, better="higher")
    # y su huella en la presion es un orden de magnitud menor que la de la reperfusion
    o2_effect = abs(with_o2["sbp"][120] - plain["sbp"][120])
    pci_effect = abs(opened["sbp"][120] - plain["sbp"][120])
    assert o2_effect * 5.0 < pci_effect, (o2_effect, pci_effect)


# C9..C11 - opioide (P3-111) ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def opioid_untreated():
    return _series("opioid", "opioid_35m", minutes=60)[0]


def test_c9_naloxone_reverses_the_central_availability_and_nothing_earlier(opioid_untreated):
    treated, runner = _series("opioid", "opioid_35m", [_naloxone("n1", 20)], minutes=60)
    assert runner.gaps == []
    assert mc.no_effect_before(treated["respiratory_rate"], opioid_untreated["respiratory_rate"], 20)
    # P3-141 (segunda familia en vivo): una orden que el motor ejecuto en el minuto 20 aparece por primera
    # vez en el estado del minuto 21, como el oxigeno. Antes el adaptador la mapeaba al propio minuto 20,
    # que ya existia cuando se ordeno. Lo que la prueba protege -- nada antes de darla -- sigue protegido.
    assert mc.effect_starts_at(treated["respiratory_rate"],
                               opioid_untreated["respiratory_rate"], 20) == 21
    assert mc.direction(treated["respiratory_rate"], opioid_untreated["respiratory_rate"], 60,
                        better="higher")
    assert mc.monotone_after(treated["respiratory_rate"], 20, rising=True)
    assert mc.no_paradox(treated["respiratory_rate"], opioid_untreated["respiratory_rate"], 20,
                         better="higher")


def test_c10_oxygen_does_not_correct_the_central_hypoventilation(opioid_untreated):
    """La distinción educativa de esta familia: el oxígeno no repara el impulso central."""
    with_o2 = _series("opioid", "opioid_35m", [_oxygen("o1", 10, 0.40)], minutes=60)[0]
    assert mc.untouched(with_o2["respiratory_rate"], opioid_untreated["respiratory_rate"],
                        tolerance=1e-9)


def test_c11_the_hypoventilation_to_oxygenation_link_is_declared_and_off(opioid_untreated):
    """Y encenderlo a transmisión completa da una SpO2 que no es defendible: decisión docente."""
    from clinical_core import opioid_migration as om
    assert om.profile().respiratory_quotient is None            # UNSET en el núcleo congelado
    # hoy: la FR cae y la SpO2 no se mueve
    assert opioid_untreated["respiratory_rate"][60] < opioid_untreated["respiratory_rate"][1]
    assert opioid_untreated["spo2"][60] == opioid_untreated["spo2"][1]

    class Linked(fam.OpioidAdapter):
        def profile(self, point):
            return dataclasses.replace(om.profile(), respiratory_quotient=0.8)

    linked = _series("opioid", "opioid_35m", minutes=60, adapter=Linked())[0]
    assert linked["spo2"][60] < 40.0        # insostenible en un caso redactado como sobrevivible
    assert linked["spo2"][60] < opioid_untreated["spo2"][60] - 40.0


# C12..C13 - los huecos declarados (P3-105, P3-108, P3-109, P3-110, P3-113) ----------------------------

def test_c12_every_declared_gap_key_is_a_real_engine_action_kind():
    """Un hueco declarado con una clave que ningún evento lleva no puede dispararse nunca."""
    import re
    import family_engine as fe
    # las clases que el motor compara explícitamente, leídas de su propio código, más sus medicinas
    source = open(fe.__file__, encoding="utf-8").read()
    kinds = set(fe._MEDICINES)
    kinds |= set(re.findall(r'kind == "([a-z_]+)"', source))
    kinds |= set(re.findall(r'kind in \{([^}]*)\}', source) and
                 re.findall(r'"([a-z_]+)"', " ".join(re.findall(r'kind in \{([^}]*)\}', source))))
    kinds |= {"fluid", "blood", "oxygen"}
    for family, adapter in fam.ADAPTERS.items():
        unknown = sorted(k for k in adapter.gaps_declared if k not in kinds)
        assert unknown == [], (family, unknown)


def test_c13_the_families_without_a_treatment_writer_declare_it():
    for family in ("pulmonary_edema", "pulmonary_embolism", "asthma"):
        adapter = fam.ADAPTERS[family]
        assert adapter.gaps_declared, family
        assert adapter.maps == ("oxygen",), (family, adapter.maps)
    # y las dos que este paquete mapeó ya no declaran su tratamiento como hueco
    assert "naloxone" in fam.ADAPTERS["opioid"].maps
    assert "reperfusion" not in fam.ADAPTERS["acs"].gaps_declared


def test_c14_a_persistent_treatment_shows_its_wait_cost_at_the_endpoint_too():
    """El contraste que cierra P3-112: transitorio contra persistente.

    El cristaloide es transitorio, así que esperar cuesta el ÁREA y el punto final favorece al tardío (C5).
    La reperfusión es PERSISTENTE —la arteria queda abierta—, así que esperar cuesta las dos cosas.
    """
    plain = _series("acs", "acs_70f_left_main", state={"family_state": {}}, minutes=180)[0]["sbp"]
    early = _series("acs", "acs_70f_left_main",
                    state={"family_state": {"reperfusion_at": 60}}, minutes=180)[0]["sbp"]
    late = _series("acs", "acs_70f_left_main",
                   state={"family_state": {"reperfusion_at": 120}}, minutes=180)[0]["sbp"]
    area = lambda s: sum(s.values()) / len(s)
    assert area(early) > area(late) > area(plain)              # el área, como en el cristaloide
    assert early[180] > late[180] > plain[180]                 # y además el punto final
    assert mc.no_effect_before(late, plain, 120)               # y la tardía no actúa antes de su minuto


def _bank(case_id):
    from clinical_core import legacy_adapter
    return legacy_adapter.bank_case(case_id)
