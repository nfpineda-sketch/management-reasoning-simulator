"""P3-117 a P3-124: la transmision hipoventilacion -> oxigenacion, y lo que se audito a su alrededor.

No enciende el enlace comun de P2T-5 en ningun perfil comprometido: cada prueba que lo necesita lo declara
en una copia local del perfil, mide y lo descarta. No puntua contra curvas del legado.
Documento: docs/PHASE3_RESPIRATORY_TRANSMISSION.md
"""
import dataclasses

import pytest

import respiratory_transmission_record as rec
import runtime_shadow as rs
import runtime_shadow_families as fam
from clinical_core import derived as dv
from clinical_core import integration
from clinical_core import opioid_migration as om

ODC, IODC = dv.oxygen_saturation_from_pao2, dv.pao2_from_oxygen_saturation


def _trajectory(family, case, migration, adapter_cls, *, rq=None, minutes=60, events=(), overrides=None):
    """La trayectoria y su estado interno, por el mismo camino que arma el runner: escritores + acciones."""
    fields = dict(overrides or {})
    if rq is not None:
        fields["respiratory_quotient"] = rq
    profile = dataclasses.replace(migration.profile(), **fields) if fields else migration.profile()

    class Local(adapter_cls):
        def profile(self, point):
            return profile

    adapter = Local()
    anchors = adapter.anchors(case, fam.COMMITTED, None)
    writers = tuple(adapter.writers(case, fam.COMMITTED, None))
    built, gaps = adapter.interventions(list(events), None) if events else ((), [])
    trajectory = integration.run(anchors, writers + tuple(built), minutes, profile)
    return trajectory, anchors, profile, gaps


def _reading(trajectory, minute):
    return trajectory.derived()[minute].to_dict()


def _paco2(trajectory, anchors, profile, minute):
    return dv.respiration(trajectory.states[minute], anchors, profile).paco2


def _delta(trajectory, anchors, profile, minute):
    return _paco2(trajectory, anchors, profile, minute) - dv.arrival_paco2_reference(anchors, profile)


def _opioid(case, **kw):
    return _trajectory("opioid", case, om, fam.OpioidAdapter, **kw)


def _asthma(case, **kw):
    from clinical_core import asthma_migration as am
    return _trajectory("asthma", case, am, fam.AsthmaAdapter, **kw)


def _series(family, case, events=(), state=None, minutes=120):
    runner = fam.ShadowPhysiologyRunner.open(family, case, state=state)
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


def _action(kind, order_id, minute, fio2=0.21):
    return rs.MirroredAction(order_id, minute, kind, {"type": kind}, {}, fio2)


# R1..R2 - el registro y la ecuacion (P3-117-1) --------------------------------------------------------

def test_r1_the_record_adopts_no_parameter_and_the_core_link_is_still_unset():
    assert rec.STATUS == "DEVELOPMENT_MEASUREMENT_NO_PARAMETER_ADOPTED"
    assert rec.P3_118_EXECUTED is False
    assert rec.FACULTY_DEVELOPMENT_DECISION["is_clinical_truth"] is False
    assert rec.FACULTY_DEVELOPMENT_DECISION["classification"] == "DEVELOPMENT_CLINICAL_REGION"
    assert rec.FACULTY_DEVELOPMENT_DECISION["confidence"] >= 0.80
    # el nucleo congelado sigue sin el enlace, en los dos perfiles respiratorios que lo admitirian
    from clinical_core import asthma_migration as am
    assert om.profile().respiratory_quotient is None
    assert am.profile().respiratory_quotient is None
    assert dv.CoreProfile().respiratory_quotient is None
    assert dv.hypoventilation_link_active(om.profile()) is False
    # ninguna etiqueta prohibida se usa como estado de este registro
    for label in rec.FORBIDDEN_STATUSES:
        assert label != rec.STATUS and label != rec.VERDICT
    # y el modulo no importa ni el nucleo ni la capa de ejecucion
    import ast
    source = open(rec.__file__, encoding="utf-8").read()
    tree = ast.parse(source)
    names = {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    names |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not any(x.startswith(("clinical_core", "runtime_")) for x in names), names


def test_r2_the_recorded_equation_is_exactly_what_the_core_computes():
    """La cadena del registro, recompuesta a mano, reproduce la SpO2 viva del caso de mapa limpio."""
    quotient = 0.8
    off, anchors, profile, _ = _opioid("opioid_67f")
    base = _reading(off, 60)["spo2"]
    delta = _delta(off, anchors, profile, 60)
    by_hand = ODC(IODC(base) - delta / quotient)

    on, _, _, _ = _opioid("opioid_67f", rq=quotient)
    assert _reading(on, 60)["spo2"] == pytest.approx(by_hand, abs=1e-9)
    # y los eslabones declarados son los que el nucleo expone, con su procedencia
    assert len(rec.EQUATION) == 8
    assert [row[2] for row in rec.EQUATION].count("UNSET") == 1
    assert rec.EQUATION[6][2] == "UNSET"      # dPaO2 = -delta / respiratory_quotient


# R3..R6 - la region admisible (P3-117-3), medida y no copiada ------------------------------------------

@pytest.mark.parametrize("case", sorted(rec.PER_CASE))
def test_r3_the_admissible_region_is_reproduced_from_the_live_model(case):
    off, anchors, profile, _ = _opioid(case)
    entry = rec.PER_CASE[case]
    base = _reading(off, 60)["spo2"]
    delta = _delta(off, anchors, profile, 60)
    assert base == pytest.approx(entry["spo2_base_at_60"], abs=1e-9)
    assert delta == pytest.approx(entry["delta_at_60"], abs=1e-4)
    floor = rec.FACULTY_DEVELOPMENT_DECISION["region"][0]
    drop = IODC(base) - IODC(floor)
    assert drop == pytest.approx(entry["admissible_pao2_drop_to_78"], abs=1e-3)
    assert drop / delta == pytest.approx(entry["transmission_fraction_max"], abs=1e-5)
    assert delta / drop == pytest.approx(entry["respiratory_quotient_min"], abs=1e-3)
    rec.validate_entry(entry)


def test_r4_the_common_region_is_the_intersection_and_never_a_point():
    low, high = rec.common_transmission_region()
    assert low == 0.0 and 0.0 < high < 1.0
    assert high == min(rec.PER_CASE[c]["transmission_fraction_max"] for c in rec.PER_CASE)
    assert rec.COMMON_REGION["is_a_point"] is False
    assert rec.COMMON_REGION["midpoint_is_preferred"] is False
    assert rec.COMMON_REGION["binding_case"] == "opioid_35m"
    # el segundo caso, solo, admitiria mas: la region comun la ata el mas grave
    assert rec.PER_CASE["opioid_67f"]["transmission_fraction_max"] > high
    assert rec.transmission_region_of("opioid_67f")[1] > rec.transmission_region_of("opioid_35m")[1]


def test_r5_the_four_declared_monotonicities_hold():
    base, quotient = 80.0, 0.8
    curve = [ODC(IODC(base) - d / quotient) for d in (-30.0, -10.0, -1.0, 0.0, 1.0, 10.0, 30.0)]
    assert all(b <= a for a, b in zip(curve, curve[1:]))          # M1
    assert curve[3] == pytest.approx(base, abs=1e-12)             # exacto en delta = 0
    assert curve[2] > base and curve[4] < base                    # M2, simetrico
    rising = [ODC(IODC(s) - 24.2104 / quotient) for s in (60.0, 70.0, 80.0, 90.0, 97.0)]
    assert all(a <= b for a, b in zip(rising, rising[1:]))        # M3 y M4, por SpO2_base
    assert rec.MONOTONICITY["M1_more_paco2_never_raises_spo2"] is True
    assert all(rec.MONOTONICITY[k] is True for k in rec.MONOTONICITY if k.startswith("M"))


@pytest.mark.parametrize("case", sorted(rec.PER_CASE))
def test_r6_the_region_bound_lands_inside_the_target_and_full_transmission_does_not(case):
    floor, ceiling = rec.FACULTY_DEVELOPMENT_DECISION["region"]
    bound = rec.COMMON_REGION["equivalent_respiratory_quotient"][0]
    inside, _, _, _ = _opioid(case, rq=bound)
    assert floor <= _reading(inside, 60)["spo2"] <= ceiling
    full, _, _, _ = _opioid(case, rq=0.8)
    spo2 = _reading(full, 60)["spo2"]
    assert spo2 < floor
    assert spo2 == pytest.approx(rec.PER_CASE[case]["spo2_at_full_transmission_r_0_8"], abs=1e-3)


# R7 - los otros dos mandos candidatos (P3-117-1) -------------------------------------------------------

def test_r7_neither_other_lever_is_a_transmission_coefficient():
    """Uno falsifica su propia cantidad declarada; el otro resulto inerte."""
    lever = rec.CANDIDATE_LEVERS["paco2_reference_mmhg"]
    needed = lever["required_for_the_region"]
    scaled, anchors, profile, _ = _opioid("opioid_35m", rq=0.8, overrides={"paco2_reference_mmhg": needed})
    assert _paco2(scaled, anchors, profile, 60) < 10.0        # un PaCO2 imposible: el precio del ajuste
    assert lever["verdict"] == rec.LEVER_DISHONEST

    floor_lever = rec.CANDIDATE_LEVERS["rr_ventilatory_floor"]
    assert floor_lever["verdict"] == rec.LEVER_INERT
    deltas = []
    for value in (0.0, 3.0, 6.0, 12.0, 18.0):
        run, anchors, profile, _ = _opioid("opioid_35m", overrides={"rr_ventilatory_floor": value})
        deltas.append(_delta(run, anchors, profile, 60))
    assert max(deltas) - min(deltas) < 1e-9, deltas           # hipotesis falsificada: el piso no mueve nada

    assert rec.CANDIDATE_LEVERS["respiratory_quotient"]["verdict"] == rec.LEVER_USABLE
    assert rec.VERDICT == "C_EXISTING_INTERFACE_CANNOT_EXPRESS_PARTIAL_TRANSMISSION"
    assert rec.CONSEQUENCE == "D_FROZEN_COMMON_CORE_EXTENSION_REQUIRED"


# R8..R9 - lo que el modelo ya hace, y el lazo que el enlace cierra ------------------------------------

@pytest.mark.parametrize("case", sorted(rec.PER_CASE))
def test_r8_the_target_is_already_met_with_the_link_off_but_without_a_trajectory(case):
    floor, ceiling = rec.FACULTY_DEVELOPMENT_DECISION["region"]
    off, _, _, _ = _opioid(case)
    first, last = _reading(off, 1)["spo2"], _reading(off, 60)["spo2"]
    assert floor <= last <= ceiling            # el nivel cae dentro de la region docente
    assert first == last                       # y es plano: no hay trayectoria de oxigenacion
    assert _reading(off, 60)["respiratory_rate"] < _reading(off, 1)["respiratory_rate"]
    assert rec.TARGET_ALREADY_MET_WITH_THE_LINK_OFF is True
    assert rec.SPO2_HAS_NO_OPIOID_TRAJECTORY is True


def test_r9_the_link_closes_an_indirect_loop_back_into_ventilation():
    """P2T-5 rechaza el impulso hipoxemico por ser un lazo sin auditar; este lazo pasa por otro lado."""
    off, a_off, p_off, _ = _opioid("opioid_35m")
    on, a_on, p_on, _ = _opioid("opioid_35m", rq=0.8)
    assert p_off.hypoxaemic_drive_mapping is None and p_on.hypoxaemic_drive_mapping is None
    assert _delta(on, a_on, p_on, 60) < _delta(off, a_off, p_off, 60) - 1e-3
    assert _reading(on, 60)["respiratory_rate"] > _reading(off, 60)["respiratory_rate"]
    assert _reading(on, 60)["delivery_rel"] < _reading(off, 60)["delivery_rel"]
    assert rec.INDIRECT_LOOP["exists"] is True
    # RECTIFICADO por P3-127: el lazo esta COMPUERTEADO por un umbral en D, no es continuo. Debajo del
    # umbral el desvio es EXACTAMENTE cero, no pequeno. La prueba anterior leia una sucesion monotona
    # cuyos primeros terminos valian cero y la llamaba crecimiento continuo.
    assert rec.INDIRECT_LOOP["continuous_not_a_threshold"] is False
    assert rec.INDIRECT_LOOP["dormant_throughout_the_development_region"] is True
    for quotient in (4.0, 2.0, 1.0):
        run, anchors, profile, _ = _opioid("opioid_35m", rq=quotient)
        assert _delta(run, anchors, profile, 60) == _delta(off, a_off, p_off, 60), quotient
        assert run.states[60].D == 0.0
    assert on.states[60].D > 0.0


# R10 - asma, sin ajustar aparte (P3-120) --------------------------------------------------------------

@pytest.mark.parametrize("case", sorted(rec.ASTHMA_WITNESSES))
def test_r10_the_common_region_does_not_contradict_certified_asthma(case):
    witness = rec.ASTHMA_WITNESSES[case]
    off, _, _, _ = _asthma(case)
    base = _reading(off, 60)["spo2"]
    assert base == pytest.approx(witness["spo2_at_60_link_off"], abs=1e-9)

    bound = rec.COMMON_REGION["equivalent_respiratory_quotient"][0]
    at_bound, _, _, _ = _asthma(case, rq=bound)
    shift = _reading(at_bound, 60)["spo2"] - base
    assert shift < 0.0                                   # mas PaCO2, nunca mas SpO2
    assert abs(shift) < 1.0                              # y el desplazamiento es pequeno en el borde
    assert shift == pytest.approx(witness["shift_at_the_common_boundary"], abs=1e-3)

    full, _, _, _ = _asthma(case, rq=0.8)
    assert _reading(full, 60)["spo2"] - base == pytest.approx(witness["shift_at_full_transmission"],
                                                              abs=1e-3)
    assert witness["classification"] == rec.ASTHMA_COMPATIBLE


# R11..R12 - la causalidad del manejo opioide (P3-119) y el contraste educativo (P3-121) --------------

@pytest.fixture(scope="module")
def opioid_arms():
    arms = {
        "untreated": [],
        "oxygen": [_action("oxygen", "o1", 10, 0.40)],
        "naloxone": [_action("naloxone", "n1", 20)],
        "both": [_action("oxygen", "o1", 10, 0.40), _action("naloxone", "n1", 20)],
        "late": [_action("naloxone", "n1", 45)],
    }
    return {name: _series("opioid", "opioid_35m", events, minutes=90) for name, events in arms.items()}


def test_r11_each_treatment_moves_its_own_mechanism_and_nothing_else(opioid_arms):
    import management_causality as mc
    base = opioid_arms["untreated"][0]
    oxygen = opioid_arms["oxygen"][0]
    naloxone = opioid_arms["naloxone"][0]
    both = opioid_arms["both"][0]
    for name, (_, runner) in opioid_arms.items():
        assert runner.gaps == [], (name, runner.gaps)

    # el oxigeno sube la SpO2 y no toca la ventilacion
    assert mc.direction(oxygen["spo2"], base["spo2"], 90, better="higher")
    assert mc.untouched(oxygen["respiratory_rate"], base["respiratory_rate"], tolerance=1e-9)
    assert mc.no_effect_before(oxygen["spo2"], base["spo2"], 10)
    # MEDIDO: el oxigeno pedido en el minuto 10 cambia la lectura en el 11, no en el 10. La naloxona,
    # en cambio, actua en su propio minuto (abajo). La asimetria esta en el nucleo congelado
    # (``Oxygen._running`` usa ``start_minute < minute`` y fija el FiO2 en ``start_minute + 1``) y aqui
    # se deja fijada, no corregida: la Fase 2 no se reabre. TD-130.
    assert mc.effect_starts_at(oxygen["spo2"], base["spo2"], 10) == 11

    # la naloxona sube la ventilacion, empieza cuando se da y no retrocede
    assert mc.direction(naloxone["respiratory_rate"], base["respiratory_rate"], 90, better="higher")
    assert mc.no_effect_before(naloxone["respiratory_rate"], base["respiratory_rate"], 20)
    assert mc.effect_starts_at(naloxone["respiratory_rate"], base["respiratory_rate"], 20) == 20
    assert mc.effect_starts_at(oxygen["spo2"], base["spo2"], 10) != 10, "la asimetria de un minuto"
    assert mc.monotone_after(naloxone["respiratory_rate"], 20, rising=True)
    assert mc.no_paradox(naloxone["respiratory_rate"], base["respiratory_rate"], 20, better="higher")

    # y la que importa en clinica: la naloxona NO mejora la oxigenacion en este modelo
    assert mc.untouched(naloxone["spo2"], base["spo2"], tolerance=1e-9)

    # los dos juntos son la union, sin interferencia
    assert both["respiratory_rate"][90] == pytest.approx(naloxone["respiratory_rate"][90], abs=1e-9)
    assert both["spo2"][90] == pytest.approx(oxygen["spo2"][90], abs=1e-9)


def test_r12_waiting_costs_ventilation_and_the_cost_lives_in_the_integral(opioid_arms):
    import management_causality as mc
    early = opioid_arms["naloxone"][0]["respiratory_rate"]
    late = opioid_arms["late"][0]["respiratory_rate"]
    base = opioid_arms["untreated"][0]["respiratory_rate"]
    assert mc.waiting_has_cost(early, late, 90, better="higher")
    assert sum(late[m] for m in range(1, 91)) < sum(early[m] for m in range(1, 91))
    # la naloxona es persistente, asi que el extremo casi converge: el coste real esta en la integral
    assert late[90] < early[90]
    assert abs(late[90] - early[90]) < 0.5


def test_r13_oxygen_and_ventilation_are_distinguishable_on_every_channel(opioid_arms):
    """P3-121: FR, W, PaCO2, SpO2 y DO2, con su temporalidad. El contraste que la docencia necesita."""
    off, anchors, profile, _ = _opioid("opioid_35m", minutes=90)
    with_oxygen = opioid_arms["oxygen"][0]
    with_naloxone = opioid_arms["naloxone"][0]
    base = opioid_arms["untreated"][0]

    # el oxigeno: SpO2 y entrega arriba; FR, W y PaCO2 intactos
    assert with_oxygen["spo2"][90] > base["spo2"][90]
    assert with_oxygen["delivery_rel"][90] >= base["delivery_rel"][90]
    assert with_oxygen["respiratory_rate"][90] == pytest.approx(base["respiratory_rate"][90], abs=1e-9)

    # la naloxona: FR arriba, y por tanto W arriba y PaCO2 abajo -- el canal que el oxigeno no toca
    treated, t_anchors, t_profile, _ = _opioid(
        "opioid_35m", minutes=90, events=[_action("naloxone", "n1", 20)])
    assert _paco2(treated, t_anchors, t_profile, 90) < _paco2(off, anchors, profile, 90) - 1.0
    assert with_naloxone["respiratory_rate"][90] > base["respiratory_rate"][90]
    # sin tratar, el PaCO2 sube de forma sostenida: la hipoventilacion progresa
    assert _paco2(off, anchors, profile, 90) > _paco2(off, anchors, profile, 30)


# R14..R15 - ACS en vivo: lo auditado y lo rechazado (P3-122) ------------------------------------------

def test_r14_acs_stays_out_of_the_live_list_and_says_why():
    assert rs.LIVE_FAMILIES == ("gi_bleed",)
    assert fam.ADAPTERS["acs"].live is False
    assert rs.enabled_for("acs", {rs.FLAG: rs.MODE_SHADOW_COMPARE}) is False
    assert "ARRIVAL_MAPPING" in fam.ACS_LIVE_GAP
    # la razon medida: anchors() ignora el estado del encuentro, donde el GI lo mapea
    adapter = fam.ADAPTERS["acs"]
    one = adapter.anchors("acs_70f_left_main", fam.COMMITTED, None)
    other = adapter.anchors("acs_70f_left_main", fam.COMMITTED, {"family_state": {}, "hidden": {}})
    assert one == other, "si el adaptador leyera la llegada del encuentro, estos dos no coincidirian"


def test_r15_the_reperfusion_referral_is_not_a_false_gap():
    """Correccion de P3-122: el pedido de reperfusion esta representado, en el reloj del motor."""
    adapter = fam.ADAPTERS["acs"]
    referral = _action("reperfusion_referral", "r1", 12)
    from clinical_core.modules.acs_ischaemia import CoronaryReperfusion

    built, gaps = adapter.interventions([referral], {"family_state": {"reperfusion_at": 95}})
    assert gaps == [], gaps                                   # representado: ningun hueco
    opens = [c for c in built if isinstance(c, CoronaryReperfusion)]
    assert len(opens) == 1 and opens[0].completes_at_minute == 95  # y una sola vez, no dos

    # pero si el motor no cronometro reperfusion, el hueco es real y se declara con su razon
    built, gaps = adapter.interventions([referral], {"family_state": {}})
    assert [c for c in built if isinstance(c, CoronaryReperfusion)] == []
    assert len(gaps) == 1 and gaps[0]["kind"] == "reperfusion_referral"
    assert "no minute at which the artery opens" in gaps[0]["why"]


def test_r16_acs_replay_equals_the_live_path_including_the_reperfusion():
    state = {"family_state": {"reperfusion_at": 95}}
    live, runner = _series("acs", "acs_70f_left_main",
                           [_action("reperfusion_referral", "r1", 12)], state=state, minutes=120)
    assert runner.gaps == [], runner.gaps
    captured = runner.replay_input()
    assert captured is not None
    replayed = fam.replay_shadow_encounter(captured)
    # el replay empieza en la llegada; el camino vivo, en el minuto 1
    assert [row["state_digest"] for row in replayed["results"]][1:] == list(runner.digests())
    # y la reperfusion esta en el artefacto, no solo en la corrida viva
    assert "acs-pci" in repr(captured.to_dict()["scenario"])


# R17..R18 - edema (P3-123) y el barrido multifamiliar (P3-124) ---------------------------------------

def test_r17_the_edema_decongestion_mechanism_exists_but_its_magnitude_is_not_authored():
    """P3-123: no falta contrato comun. Falta un numero que la docencia no ha autorizado."""
    from clinical_core import edema_migration as em
    from clinical_core.modules.pulmonary_edema import (DecongestiveTreatment, EdemaCongestion,
                                                       EDEMA_DECONGESTION)
    # la senal es de tiempo de tratamiento, con la MISMA forma que las dos ya mapeadas
    treatment = DecongestiveTreatment("edema-decongestion", 30)
    assert treatment.signals(29) == ()
    assert treatment.signals(30)[0].name == EDEMA_DECONGESTION
    assert EDEMA_DECONGESTION in EdemaCongestion.responds_to
    # la magnitud, en cambio, es un parametro de construccion, y vale 0 por omision
    assert em.writer().decongestion_per_min == 0.0
    # y la unica tasa que el repositorio ofrece esta declarada SYNTHETIC_ONLY, sin magnitud autorizada
    source = open(em.__file__, encoding="utf-8").read()
    assert "SYNTHETIC_ONLY" in source.split("DECONGESTION = ")[0].rsplit("#:", 1)[-1]
    assert "no magnitude is authored" in source
    # por eso el hueco del diuretico sigue declarado
    assert "diuretic" in fam.ADAPTERS["pulmonary_edema"].gaps_declared


@pytest.mark.parametrize("family", sorted(fam.ADAPTERS))
def test_r18_every_certified_family_still_runs_a_full_horizon_with_only_declared_gaps(family):
    adapter = fam.ADAPTERS[family]
    known = set(adapter.maps) | set(adapter.gaps_declared)
    for case in adapter.cases:
        readings, runner = _series(family, case, minutes=120)
        assert not runner.failures, (family, case, [v.classification for v in runner.failures])
        assert len(readings["spo2"]) >= 120
        for gap in runner.gaps:
            assert gap["kind"] in known, (family, case, gap)
