"""PHASE2_AMENDMENT_1: la enmienda formal y minima de la fisiologia comun cerrada.

Anade UN control explicito -- ``hypoventilation_oxygenation_transmission_fraction`` -- para que el enlace
relativo de P2T-5 pueda expresarse de forma PARCIAL y no solo todo o nada.

Cada propiedad es una funcion ``check_*`` sin fixtures. Las pruebas ``test_*`` las llaman sobre la
implementacion real, y los CONTROLES NEGATIVOS las llaman sobre un mutante de la implementacion y exigen que
FALLEN. Una propiedad que ningun mutante mata no se considera probada: asi se corrigio el defecto que la
revision adversarial encontro en la primera version de este archivo (30 de 39 pruebas seguian pasando con
la fraccion inerte).

Registro: docs/revision/PHASE2_AMENDMENT_1.json. Forense: docs/revision/PHASE2_AMENDMENT_1_FORENSICS.md
"""
import dataclasses

import pytest

import runtime_shadow as rs
import runtime_shadow_families as fam
from clinical_core import asthma_migration as am
from clinical_core import derived as dv
from clinical_core import integration
from clinical_core import opioid_migration as om
from clinical_core.state import CoreInvariantError

FIELD = "hypoventilation_oxygenation_transmission_fraction"
#: La referencia sintetica del cociente, la unica que las sondas usan (P2T-5).
R = 0.8
#: Por encima de esto despierta en opioid_35m el lazo auditado en P3-127 (D pasa de 0 a positivo).
LOOP_WAKES_AT = 0.818522
#: Lo que la via certificada daba ANTES de la enmienda, medido entonces (P3-117) y fijado aqui.
BEFORE_FULL = {"opioid_35m": 25.249191654270817, "opioid_67f": 37.21648925248409}
BEFORE_OFF = {"opioid_35m": 80.0, "opioid_67f": 84.0, "asthma_49m": 89.0, "asthma_24f": 90.0}
ODC, IODC = dv.oxygen_saturation_from_pao2, dv.pao2_from_oxygen_saturation


def _run(case, *, minutes=60, events=(), **fields):
    migration, adapter_cls = (om, fam.OpioidAdapter) if case.startswith("opioid") else (am, fam.AsthmaAdapter)
    profile = dataclasses.replace(migration.profile(), **fields) if fields else migration.profile()

    class Local(adapter_cls):
        def profile(self, point):
            return profile

    adapter = Local()
    anchors = adapter.anchors(case, fam.COMMITTED, None)
    writers = tuple(adapter.writers(case, fam.COMMITTED, None))
    built = tuple(adapter.interventions(list(events), None)[0]) if events else ()
    return integration.run(anchors, writers + built, minutes, profile), anchors, profile


def _linked(case, share, **kw):
    fields = {"respiratory_quotient": R}
    if share is not ...:
        fields[FIELD] = share
    return _run(case, **fields, **kw)


def _spo2(run, minute=60):
    return run[0].derived()[minute].to_dict()["spo2"]


def _rate(run, minute=60):
    return run[0].derived()[minute].to_dict()["respiratory_rate"]


def _paco2(run, minute=60):
    trajectory, anchors, profile = run
    return dv.respiration(trajectory.states[minute], anchors, profile).paco2


def _delta(run, minute=60):
    return _paco2(run, minute) - dv.arrival_paco2_reference(run[1], run[2])


def _naloxone(minute=5):
    return [rs.MirroredAction("n1", minute, "naloxone", {"type": "naloxone"}, {}, 0.21)]


def _oxygen(fio2):
    return [rs.MirroredAction("o1", 5, "oxygen", {"type": "oxygen"}, {}, fio2)]


# ====================================================================================================
# Las propiedades
# ====================================================================================================

def check_share_zero_is_the_link_not_declared():
    """Fraccion 0 == enlace sin declarar, en TODO estado: tambien en el borde sin ventilacion."""
    for case in ("opioid_35m", "opioid_67f"):
        off = _run(case)
        zero = _linked(case, 0.0)
        for minute in (1, 30, 60):
            assert _spo2(zero, minute) == _spo2(off, minute), (case, minute)
        assert _spo2(off) == BEFORE_OFF[case]
    # el borde: sin ventilacion no hay PaCO2, y una fraccion 0 no lo necesita
    off = _run("opioid_35m", minutes=30, central_drive_availability=0.0)
    try:
        zero = _run("opioid_35m", minutes=30, central_drive_availability=0.0, respiratory_quotient=R,
                    **{FIELD: 0.0})
    except dv.UnresolvedBoundary as error:
        raise AssertionError("una fraccion 0 pidio el PaCO2 en el borde sin ventilacion") from error
    assert _spo2(zero, 30) == _spo2(off, 30)


def check_share_one_is_the_certified_full_transmission():
    for case, before in BEFORE_FULL.items():
        assert _spo2(_linked(case, 1.0)) == before, case
        assert _spo2(_linked(case, ...)) == before, case          # sin escalar: la misma cifra, bit a bit
        assert before < BEFORE_OFF[case] - 40.0                    # y de verdad transmite


def check_an_intermediate_share_obeys_the_exact_equation():
    """SpO2 == ODC(ODC^-1(base) - s * delta / R), con base y delta medidos en la corrida SIN enlace."""
    for case in ("opioid_35m", "opioid_67f"):
        off = _run(case)
        base, delta = _spo2(off), _delta(off)
        assert delta > 10.0
        low, high = _spo2(_linked(case, 1.0)), base
        for share in (0.03, 0.25, 0.6):
            assert share < LOOP_WAKES_AT
            got = _spo2(_linked(case, share))
            assert got == pytest.approx(ODC(IODC(base) - share * delta / R), abs=1e-9), (case, share)
            assert low < got < high, (case, share)


def check_more_share_is_strictly_worse_under_hypercapnia():
    curve = [_spo2(_linked("opioid_35m", share)) for share in (0.0, 0.1, 0.3, 0.6, 1.0)]
    assert all(b < a for a, b in zip(curve, curve[1:])), curve


def check_more_share_is_strictly_better_under_hypocapnia():
    """Tras la reversion la ventilacion supera la de llegada, asi que el delta es NEGATIVO."""
    assert _delta(_linked("opioid_35m", 0.3, events=_naloxone())) < -10.0
    curve = [_spo2(_linked("opioid_35m", share, events=_naloxone())) for share in (0.0, 0.3, 0.6, 1.0)]
    assert all(b > a for a, b in zip(curve, curve[1:])), curve


def check_the_default_changes_nothing_and_is_the_unscaled_path():
    assert dv.CoreProfile().hypoventilation_oxygenation_transmission_fraction is None
    for case, before in BEFORE_OFF.items():
        migration = om if case.startswith("opioid") else am
        profile = migration.profile()
        assert getattr(profile, FIELD) is None and profile.respiratory_quotient is None
        assert dv.hypoventilation_link_active(profile) is False
        assert _spo2(_run(case)) == before, case
    # y por omision, con el enlace declarado, la via es la certificada completa: no un 0 ni un 0.5
    for case, before in BEFORE_FULL.items():
        assert _spo2(_linked(case, ...)) == before


def check_the_share_does_not_move_the_ventilation_chain():
    """FR y PaCO2 identicos bit a bit entre fracciones, donde el lazo auditado esta dormido."""
    for case, shares in (("opioid_35m", (0.1, 0.3, 0.6, 0.8)), ("asthma_49m", (0.3, 1.0)), ("asthma_24f", (0.3, 1.0))):
        base = _linked(case, 0.0)
        for share in shares:
            other = _linked(case, share)
            for minute in (1, 30, 60):
                assert _paco2(other, minute) == _paco2(base, minute), (case, share, minute)
                assert _rate(other, minute) == _rate(base, minute), (case, share, minute)


#: El UNICO canal de estado que la fraccion alcanza, y no por escritura propia: el lector de deficit agudo
#: de P2I-2AF lee la SpO2 y mueve el objetivo simpatico. Fisiologia certificada anterior a la enmienda.
REACHED_THROUGH_CERTIFIED_READERS = ("sympathetic_drive",)


def _moved(left, right):
    def differs(a, b, names):
        return [name for name in names if getattr(a, name) != getattr(b, name)]
    top = differs(left, right, [f.name for f in dataclasses.fields(left) if f.name != "aux"])
    aux = differs(left.aux, right.aux, [f.name for f in dataclasses.fields(left.aux)])
    return top, aux


def check_the_share_writes_into_no_state_channel_of_its_own():
    """TODOS los campos del estado, numericos o no: lo unico que se mueve es el canal declarado arriba."""
    base = _linked("opioid_35m", 0.0)[0]
    for share in (0.1, 0.3, 0.6, 0.8):
        other = _linked("opioid_35m", share)[0]
        for minute in (1, 30, 60):
            top, aux = _moved(base.states[minute], other.states[minute])
            assert top == [], (share, minute, top)
            assert aux == list(REACHED_THROUGH_CERTIFIED_READERS), (share, minute, aux)


def check_oxygen_stays_monotone_and_the_link_stays_expressed_under_it():
    for share in (0.0, 0.3, 1.0):
        rising = [_spo2(_linked("opioid_35m", share, events=_oxygen(f))) for f in (0.21, 0.40, 0.60, 1.0)]
        assert all(b >= a for a, b in zip(rising, rising[1:])), (share, rising)
        assert rising[-1] > rising[0], share
    # con oxigeno el enlace sigue expresandose: a igual FiO2, mas fraccion sigue siendo peor
    for fio2 in (0.40, 0.60):
        assert (_spo2(_linked("opioid_35m", 0.3, events=_oxygen(fio2)))
                < _spo2(_linked("opioid_35m", 0.0, events=_oxygen(fio2)))), fio2


def check_the_opioid_fixture_is_representable():
    """Existe fraccion que deja la SpO2(60) en [78, 88] % habiendo transmitido de verdad."""
    for case in ("opioid_35m", "opioid_67f"):
        base = _spo2(_run(case))
        inside = [s for s in (0.01, 0.02, 0.04, 0.06) if 78.0 <= _spo2(_linked(case, s)) < base]
        assert inside, case


def check_asthma_stays_representable_at_the_same_shares():
    for case in ("asthma_49m", "asthma_24f"):
        base = _spo2(_run(case))
        for share in (0.02, 0.06, 0.12):
            moved = _spo2(_linked(case, share))
            assert moved < base, (case, share)             # transmite: estrictamente por debajo
            assert base - moved < 1.0 and moved > 78.0, (case, share)


CHECKS = {
    "zero": check_share_zero_is_the_link_not_declared,
    "one": check_share_one_is_the_certified_full_transmission,
    "intermediate": check_an_intermediate_share_obeys_the_exact_equation,
    "hypercapnia": check_more_share_is_strictly_worse_under_hypercapnia,
    "hypocapnia": check_more_share_is_strictly_better_under_hypocapnia,
    "default": check_the_default_changes_nothing_and_is_the_unscaled_path,
    "ventilation_chain": check_the_share_does_not_move_the_ventilation_chain,
    "state": check_the_share_writes_into_no_state_channel_of_its_own,
    "oxygen": check_oxygen_stays_monotone_and_the_link_stays_expressed_under_it,
    "opioid": check_the_opioid_fixture_is_representable,
    "asthma": check_asthma_stays_representable_at_the_same_shares,
}


@pytest.mark.parametrize("name", sorted(CHECKS))
def test_the_property_holds_on_the_real_implementation(name):
    CHECKS[name]()


# ====================================================================================================
# Los controles negativos: mutantes de la implementacion que cada propiedad debe matar
# ====================================================================================================

_REAL_LINK = dv.ventilated_oxygenation
_REAL_RESPIRATION = dv.respiration


def _delta_of(state, anchors, profile):
    paco2 = _REAL_RESPIRATION(state, anchors, profile).paco2
    if paco2 is None:
        raise dv.UnresolvedBoundary("no PaCO2")
    return paco2 - dv.arrival_paco2_reference(anchors, profile)


def _share_of(profile):
    share = getattr(profile, FIELD)
    return 1.0 if share is None else share


def _inert(spo2_base, state, anchors, profile):
    return spo2_base                                              # la fraccion (y el enlace) no hacen nada


def _ignored(spo2_base, state, anchors, profile):
    delta = _delta_of(state, anchors, profile)                    # la ecuacion ANTERIOR: siempre completa
    return spo2_base if delta == 0.0 else ODC(IODC(spo2_base) - delta / profile.respiratory_quotient)


def _squared(spo2_base, state, anchors, profile):
    delta = _delta_of(state, anchors, profile)                    # la fraccion aplicada dos veces
    return ODC(IODC(spo2_base) - _share_of(profile) ** 2 * delta / profile.respiratory_quotient)


def _on_the_base(spo2_base, state, anchors, profile):
    delta = _delta_of(state, anchors, profile)                    # mal cableada: escala la base, no el delta
    return ODC(_share_of(profile) * IODC(spo2_base) - delta / profile.respiratory_quotient)


def _zero_decided_late(spo2_base, state, anchors, profile):
    delta = _delta_of(state, anchors, profile)                    # el defecto reparado: PaCO2 antes del 0
    share = getattr(profile, FIELD)
    if share == 0.0:
        return spo2_base
    return ODC(IODC(spo2_base) - _share_of(profile) * delta / profile.respiratory_quotient)


def _respiration_reads_the_share(state, anchors, profile):
    out = _REAL_RESPIRATION(state, anchors, profile)              # efecto DIRECTO prohibido sobre el PaCO2
    share = getattr(profile, FIELD)
    if share and out.paco2 is not None:
        return dataclasses.replace(out, paco2=out.paco2 * (1.0 + share))
    return out


MUTANTS = {
    "INERT": ("ventilated_oxygenation", _inert),
    "IGNORED_ALWAYS_FULL": ("ventilated_oxygenation", _ignored),
    "APPLIED_TWICE": ("ventilated_oxygenation", _squared),
    "SCALES_THE_BASE": ("ventilated_oxygenation", _on_the_base),
    "ZERO_DECIDED_AFTER_THE_PACO2": ("ventilated_oxygenation", _zero_decided_late),
    "WRITES_THE_PACO2": ("respiration", _respiration_reads_the_share),
}

#: Que propiedad mata a que mutante. Cada propiedad aparece al menos una vez: ninguna queda sin control.
KILLS = [
    ("INERT", "one"), ("INERT", "intermediate"), ("INERT", "hypercapnia"), ("INERT", "hypocapnia"),
    ("INERT", "default"), ("INERT", "oxygen"), ("INERT", "opioid"), ("INERT", "asthma"),
    ("IGNORED_ALWAYS_FULL", "zero"), ("IGNORED_ALWAYS_FULL", "intermediate"),
    ("IGNORED_ALWAYS_FULL", "hypercapnia"), ("IGNORED_ALWAYS_FULL", "hypocapnia"),
    ("IGNORED_ALWAYS_FULL", "opioid"), ("IGNORED_ALWAYS_FULL", "asthma"),
    ("APPLIED_TWICE", "intermediate"),
    ("SCALES_THE_BASE", "intermediate"), ("SCALES_THE_BASE", "zero"),
    ("ZERO_DECIDED_AFTER_THE_PACO2", "zero"),
    ("WRITES_THE_PACO2", "ventilation_chain"), ("WRITES_THE_PACO2", "state"),
]


@pytest.mark.parametrize("mutant,check", KILLS)
def test_negative_control_the_property_fails_on_the_mutant(monkeypatch, mutant, check):
    attribute, replacement = MUTANTS[mutant]
    monkeypatch.setattr(dv, attribute, replacement)
    with pytest.raises(AssertionError):
        CHECKS[check]()


def test_every_property_has_a_negative_control_and_every_mutant_is_killed():
    assert {check for _, check in KILLS} == set(CHECKS)
    assert {mutant for mutant, _ in KILLS} == set(MUTANTS)


def test_the_mutants_are_real_changes_and_the_real_code_is_restored():
    assert dv.ventilated_oxygenation is _REAL_LINK and dv.respiration is _REAL_RESPIRATION


# ====================================================================================================
# El invariante del perfil
# ====================================================================================================

@pytest.mark.parametrize("bad", [-1e-9, -0.5, 1.0000001, 2.0, float("nan"), float("inf"), True])
def test_an_invalid_share_is_refused_by_the_core_invariant(bad):
    """Por el invariante del nucleo, no por un TypeError de campo inexistente."""
    with pytest.raises(CoreInvariantError):
        dataclasses.replace(om.profile(), respiratory_quotient=R, **{FIELD: bad})


def test_a_non_numeric_share_is_refused_by_the_core_invariant():
    with pytest.raises(CoreInvariantError):
        dataclasses.replace(om.profile(), respiratory_quotient=R, **{FIELD: "0.5"})


def test_the_refusal_is_the_invariant_and_not_a_missing_field():
    """El control negativo de las dos pruebas de arriba: un campo que no existe da TypeError, otra cosa."""
    with pytest.raises(TypeError):
        dataclasses.replace(om.profile(), respiratory_quotient=R, no_such_field_at_all=0.5)
    assert FIELD in {f.name for f in dataclasses.fields(dv.CoreProfile)}


def test_a_share_is_declared_only_with_the_link_it_scales():
    with pytest.raises(CoreInvariantError, match="declared only with it"):
        dataclasses.replace(om.profile(), **{FIELD: 0.5})
    # y la enmienda no relaja la negativa de P2T-5 al impulso hipoxemico
    with pytest.raises(CoreInvariantError, match="HYPOXEMIC_FEEDBACK_LOOP_DEFERRED"):
        dataclasses.replace(om.profile(), respiratory_quotient=R, **{FIELD: 0.5},
                            hypoxaemic_drive_mapping=((80.0, 1.0),), hypoxaemic_to_drive_gain=1.0)


@pytest.mark.parametrize("good", [0.0, 1e-9, 0.5, 0.999, 1.0])
def test_a_share_in_the_closed_unit_interval_is_accepted(good):
    assert getattr(dataclasses.replace(om.profile(), respiratory_quotient=R, **{FIELD: good}), FIELD) == good


def test_the_profile_round_trips_with_and_without_the_share():
    for share in (None, 0.0, 0.37, 1.0):
        fields = {"respiratory_quotient": R} | ({} if share is None else {FIELD: share})
        profile = dataclasses.replace(om.profile(), **fields)
        assert dv.CoreProfile(**{k: (tuple(tuple(p) for p in v) if isinstance(v, list) else v)
                                 for k, v in profile.to_dict().items()}) == profile


def test_the_provenance_says_what_the_share_is_and_is_not():
    status, text = dv.PARAMETERS[FIELD]
    assert status == dv.PROVISIONAL and "PHASE2_AMENDMENT_1" in text
    for denial in ("not a respiratory quotient", "shunt fraction", "fio2 gain", "retained(g)"):
        assert denial in text.lower(), denial
