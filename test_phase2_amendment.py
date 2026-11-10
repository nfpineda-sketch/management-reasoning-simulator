"""PHASE2_AMENDMENT_1: la enmienda formal y minima de la fisiologia comun cerrada.

Anade UN control explicito -- ``hypoventilation_oxygenation_transmission_fraction`` -- para que el enlace
alveolar relativo de P2T-5 pueda expresar transmision PARCIAL y no solo todo o nada. El cierre historico
de la Fase 2 NO se reescribe: su digesto sigue recalculando contra su propio arbol.

Registro: docs/revision/PHASE2_AMENDMENT_1.json. Auditoria previa: P3-127 (veredicto A).
Documento: docs/PHASE2_AMENDMENT_1.md
"""
import dataclasses
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

import runtime_shadow as rs
import runtime_shadow_families as fam
from clinical_core import asthma_migration as am
from clinical_core import derived as dv
from clinical_core import integration
from clinical_core import opioid_migration as om

ROOT = Path(__file__).resolve().parent
RECORD = ROOT / "docs" / "revision" / "PHASE2_AMENDMENT_1.json"
FIELD = "hypoventilation_oxygenation_transmission_fraction"
#: La referencia fisiologica sintetica del cociente respiratorio, la unica que las sondas usan (P2T-5).
R = 0.8
#: Por encima de esto el lazo auditado en P3-127 despierta en opioid_35m (D pasa de 0 a positivo).
LOOP_WAKES_AT = 0.818522


@pytest.fixture(scope="module")
def record():
    return json.loads(RECORD.read_text(encoding="utf-8"))


def _run(migration, adapter_cls, case, *, minutes=60, events=(), **fields):
    profile = dataclasses.replace(migration.profile(), **fields) if fields else migration.profile()

    class Local(adapter_cls):
        def profile(self, point):
            return profile

    adapter = Local()
    anchors = adapter.anchors(case, fam.COMMITTED, None)
    writers = tuple(adapter.writers(case, fam.COMMITTED, None))
    built = tuple(adapter.interventions(list(events), None)[0]) if events else ()
    return integration.run(anchors, writers + built, minutes, profile), anchors, profile


def _spo2(trajectory, minute=60):
    return trajectory.derived()[minute].to_dict()["spo2"]


def _paco2(trajectory, anchors, profile, minute=60):
    return dv.respiration(trajectory.states[minute], anchors, profile).paco2


def _opioid(case="opioid_35m", **kw):
    return _run(om, fam.OpioidAdapter, case, **kw)


def _asthma(case="asthma_49m", **kw):
    return _run(am, fam.AsthmaAdapter, case, **kw)


def _naloxone(minute=5):
    return [rs.MirroredAction("n1", minute, "naloxone", {"type": "naloxone"}, {}, 0.21)]


# T1 -- la omision no cambia nada ----------------------------------------------------------------------

def test_t1_the_backward_compatible_default_changes_no_committed_profile():
    assert dv.CoreProfile().hypoventilation_oxygenation_transmission_fraction is None
    for migration in (om, am):
        profile = migration.profile()
        assert getattr(profile, FIELD) is None
        # el enlace sigue APAGADO: la fraccion no es un segundo interruptor, y no enciende nada
        assert profile.respiratory_quotient is None
        assert dv.hypoventilation_link_active(profile) is False
    for migration, adapter, case in ((om, fam.OpioidAdapter, "opioid_35m"),
                                     (am, fam.AsthmaAdapter, "asthma_49m")):
        off = _run(migration, adapter, case)[0]
        explicit = _run(migration, adapter, case, **{FIELD: None})[0]
        assert _spo2(off) == _spo2(explicit)


# T2/T3 -- los anclajes exactos ------------------------------------------------------------------------

@pytest.mark.parametrize("case", ["opioid_35m", "opioid_67f"])
def test_t2_fraction_zero_transmits_nothing_exactly(case):
    """Sin ida y vuelta por la relacion de disociacion: la SpO2 es la de la via certificada, identica."""
    certified = _spo2(_run(om, fam.OpioidAdapter, case)[0])
    zero = _spo2(_run(om, fam.OpioidAdapter, case, respiratory_quotient=R, **{FIELD: 0.0})[0])
    assert zero == certified


@pytest.mark.parametrize("case", ["opioid_35m", "opioid_67f"])
def test_t3_fraction_one_reproduces_the_certified_full_transmission_bit_for_bit(case):
    unscaled = _spo2(_run(om, fam.OpioidAdapter, case, respiratory_quotient=R)[0])
    full = _spo2(_run(om, fam.OpioidAdapter, case, respiratory_quotient=R, **{FIELD: 1.0})[0])
    assert full == unscaled
    # y es el valor medido ANTES de la enmienda (P3-117), no uno nuevo
    before = {"opioid_35m": 25.249191654270817, "opioid_67f": 37.21648925248409}[case]
    assert full == before


def test_t3b_the_record_states_the_backward_compatibility_result(record):
    assert record["backward_compatibility"]["result"] == "EXACT"
    assert record["parameter"]["default"] is None
    assert "NOT a second off switch" in record["parameter"]["default_meaning"]


# T4/T5/T6 -- las monotonias ---------------------------------------------------------------------------

def test_t4_more_fraction_never_improves_spo2_under_hypercapnia():
    curve = [_spo2(_run(om, fam.OpioidAdapter, "opioid_35m", respiratory_quotient=R, **{FIELD: f})[0])
             for f in (0.0, 0.1, 0.3, 0.6, 1.0)]
    assert all(b <= a for a, b in zip(curve, curve[1:])), curve
    assert curve[0] > curve[-1]              # y la hipercapnia de este caso de verdad transmite


def test_t5_more_fraction_never_worsens_spo2_under_hypocapnia():
    """Tras la naloxona la FR sube sobre la de llegada, asi que el delta es NEGATIVO."""
    trajectory, anchors, profile = _opioid(respiratory_quotient=R, events=_naloxone(), **{FIELD: 0.3})
    assert _paco2(trajectory, anchors, profile) - dv.arrival_paco2_reference(anchors, profile) < 0.0
    curve = [_spo2(_opioid(respiratory_quotient=R, events=_naloxone(), **{FIELD: f})[0])
             for f in (0.0, 0.3, 0.6, 1.0)]
    assert all(b >= a for a, b in zip(curve, curve[1:])), curve


@pytest.mark.parametrize("fraction", [0.0, 0.3, 1.0])
def test_t6_oxygen_stays_monotonic_at_every_fraction(fraction):
    rising = []
    for fio2 in (0.21, 0.40, 0.60, 1.0):
        events = [rs.MirroredAction("o1", 5, "oxygen", {"type": "oxygen"}, {}, fio2)]
        rising.append(_spo2(_opioid(respiratory_quotient=R, events=events, **{FIELD: fraction})[0]))
    assert all(b >= a for a, b in zip(rising, rising[1:])), (fraction, rising)


# T7/T8/T9 -- ningun efecto directo --------------------------------------------------------------------

#: El UNICO canal de estado que la fraccion alcanza, y no por escritura propia: el lector de deficit
#: agudo de P2I-2AF lee la SpO2 y mueve el objetivo simpatico. Es fisiologia certificada anterior a la
#: enmienda, y cierra por FC -> gasto -> entrega -> deficit, nunca por el PaCO2. P3-127 lo omitio en su
#: primer grafo y esta prueba lo fija para que no se pierda otra vez.
REACHED_THROUGH_CERTIFIED_READERS = ("sympathetic_drive",)


@pytest.mark.parametrize("fraction", [0.1, 0.3, 0.6, 0.8])
def test_t7_t8_t9_the_fraction_writes_into_no_channel_of_its_own(fraction):
    """Ningun efecto DIRECTO: lo de aguas arriba del enlace es identico bit a bit, y lo que se mueve en
    el estado es exactamente un canal, alcanzado por un lector certificado de la SpO2 que ya existia.

    Asi queda cubierto de una vez cuanto la enmienda promete no tocar -- FR, W, PaCO2, mecanica, G, L,
    disponibilidad central, estres sistemico, distres y tono -- sin fingir que una SpO2 distinta no la lee
    nadie. Si la fraccion escribiera alguna vez en otro canal, esta prueba lo dice.
    """
    import dataclasses as dc
    assert fraction < LOOP_WAKES_AT
    base, base_anchors, base_profile = _run(om, fam.OpioidAdapter, "opioid_35m",
                                            respiratory_quotient=R, **{FIELD: 0.0})
    other, anchors, profile = _run(om, fam.OpioidAdapter, "opioid_35m",
                                   respiratory_quotient=R, **{FIELD: fraction})
    for minute in (1, 30, 60):
        left, right = base.states[minute], other.states[minute]
        # aguas arriba: la cadena de la ventilacion no se mueve
        assert _paco2(other, anchors, profile, minute) == _paco2(base, base_anchors, base_profile, minute)
        assert (other.derived()[minute].to_dict()["respiratory_rate"]
                == base.derived()[minute].to_dict()["respiratory_rate"])
        # el lazo acido sigue dormido en toda esta banda
        assert right.D == 0.0 and right.aux.metabolic_acid_burden == left.aux.metabolic_acid_burden
        # y el conjunto de canales alcanzados es EXACTAMENTE el declarado
        moved = [field.name for field in dc.fields(left)
                 if isinstance(getattr(left, field.name), (int, float))
                 and not isinstance(getattr(left, field.name), bool)
                 and getattr(left, field.name) != getattr(right, field.name)]
        moved_aux = [field.name for field in dc.fields(left.aux)
                     if isinstance(getattr(left.aux, field.name), (int, float))
                     and not isinstance(getattr(left.aux, field.name), bool)
                     and getattr(left.aux, field.name) != getattr(right.aux, field.name)]
        assert moved == [], (minute, moved)
        assert moved_aux == list(REACHED_THROUGH_CERTIFIED_READERS), (minute, moved_aux)


def test_t7c_the_one_reached_channel_is_a_certified_spo2_reader_with_no_return_limb_here():
    """Menos SpO2 -> mas impulso simpatico -> mas FC. Pero la entrega sigue a la SpO2 EXACTAMENTE, asi que
    la subida de FC no devuelve entrega en este caso: la rama de retorno del lazo es inerte aqui.

    Se midio porque la hipotesis contraria -- que la FC compensara y la entrega cayera menos -- resulto
    FALSA: los dos cocientes coinciden a doble precision. Queda fijado, porque si algun dia la FC sI
    devolviera entrega, ese lazo necesitaria su propia auditoria.
    """
    base = _run(om, fam.OpioidAdapter, "opioid_35m", respiratory_quotient=R, **{FIELD: 0.0})[0]
    other = _run(om, fam.OpioidAdapter, "opioid_35m", respiratory_quotient=R, **{FIELD: 0.1})[0]
    left, right = base.derived()[60].to_dict(), other.derived()[60].to_dict()
    assert right["spo2"] < left["spo2"]
    assert other.states[60].aux.sympathetic_drive > base.states[60].aux.sympathetic_drive
    assert right["pulse_rate_bpm"] > left["pulse_rate_bpm"]
    assert (right["delivery_rel"] / left["delivery_rel"]
            == pytest.approx(right["spo2"] / left["spo2"], rel=1e-12))


def test_t7b_above_the_threshold_the_only_change_is_the_audited_indirect_loop():
    """Y por encima del umbral lo que se mueve es el lazo que P3-127 audito, no una escritura directa."""
    low = _run(om, fam.OpioidAdapter, "opioid_35m", respiratory_quotient=R, **{FIELD: 0.5})
    high = _run(om, fam.OpioidAdapter, "opioid_35m", respiratory_quotient=R, **{FIELD: 1.0})
    assert low[0].states[60].D == 0.0 and high[0].states[60].D > 0.0
    # el signo es negativo: compensa, no amplifica
    assert (high[0].derived()[60].to_dict()["respiratory_rate"]
            > low[0].derived()[60].to_dict()["respiratory_rate"])
    assert _paco2(*high) < _paco2(*low)


def test_t8b_the_fraction_never_moves_the_paco2_chain_in_asthma_at_any_value():
    """En asma el lazo no despierta ni a 1.0, asi que el mapa es de una sola via en todo el rango."""
    for case in ("asthma_49m", "asthma_24f"):
        base = _run(am, fam.AsthmaAdapter, case, respiratory_quotient=R, **{FIELD: 0.0})
        for fraction in (0.3, 1.0):
            other = _run(am, fam.AsthmaAdapter, case, respiratory_quotient=R, **{FIELD: fraction})
            assert _paco2(*other) == _paco2(*base), (case, fraction)
            assert (other[0].derived()[60].to_dict()["respiratory_rate"]
                    == base[0].derived()[60].to_dict()["respiratory_rate"])
            assert other[0].states[60].D == base[0].states[60].D == 0.0


# T10 -- el invariante ---------------------------------------------------------------------------------

@pytest.mark.parametrize("bad", [-1e-9, -0.5, 1.0000001, 2.0, float("nan"), float("inf"), True, "0.5"])
def test_t10_an_invalid_fraction_is_refused(bad):
    with pytest.raises(Exception):
        dataclasses.replace(om.profile(), respiratory_quotient=R, **{FIELD: bad})


def test_t10b_a_fraction_without_the_link_it_scales_is_refused():
    with pytest.raises(Exception):
        dataclasses.replace(om.profile(), **{FIELD: 0.5})
    # y el enlace sigue rechazando el impulso hipoxemico: la enmienda no relaja eso
    with pytest.raises(Exception):
        dataclasses.replace(om.profile(), respiratory_quotient=R, **{FIELD: 0.5},
                            hypoxaemic_drive_mapping=((80.0, 1.0),), hypoxaemic_to_drive_gain=1.0)


@pytest.mark.parametrize("good", [0.0, 1e-9, 0.5, 0.999, 1.0])
def test_t10c_a_share_in_the_closed_unit_interval_is_accepted(good):
    assert getattr(dataclasses.replace(om.profile(), respiratory_quotient=R, **{FIELD: good}), FIELD) == good


# T11/T12 -- las dos familias respiratorias son representables ----------------------------------------

@pytest.mark.parametrize("case", ["opioid_35m", "opioid_67f"])
def test_t11_the_opioid_behaviour_is_representable_inside_the_faculty_region(case):
    """Existe una fraccion que deja la SpO2(60) sin tratar dentro de [78, 88] %, que era el objetivo."""
    inside = [f for f in (0.01, 0.02, 0.04, 0.06, 0.08, 0.12, 0.2)
              if 78.0 <= _spo2(_run(om, fam.OpioidAdapter, case, respiratory_quotient=R, **{FIELD: f})[0]) <= 88.0]
    assert inside, case


@pytest.mark.parametrize("case", ["asthma_49m", "asthma_24f"])
def test_t12_the_asthma_behaviour_stays_representable_at_the_same_fractions(case):
    base = _spo2(_run(am, fam.AsthmaAdapter, case)[0])
    for fraction in (0.02, 0.06, 0.12):
        moved = _spo2(_run(am, fam.AsthmaAdapter, case, respiratory_quotient=R, **{FIELD: fraction})[0])
        assert moved <= base                      # mas PaCO2, nunca mas SpO2
        assert base - moved < 1.0                 # y el desplazamiento es pequeno en esa banda
        assert moved > 78.0                       # sin hipoxemia grave nueva


# T13/T14 -- la historia y la procedencia --------------------------------------------------------------

def _sources_at(ref: str) -> dict:
    names = sorted(name for name in subprocess.run(
        ("git", "ls-tree", "-r", "--name-only", ref, "--", "clinical_core"),
        cwd=ROOT, capture_output=True, text=True, check=True).stdout.split() if name.endswith(".py"))
    return {name: hashlib.sha256(subprocess.run(("git", "show", f"{ref}:{name}"), cwd=ROOT,
                                                capture_output=True, check=True).stdout).hexdigest()
            for name in names}


def _sources_now() -> dict:
    paths = sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "clinical_core").rglob("*.py")
                   if "__pycache__" not in path.parts and path.is_file() and not path.name.startswith("."))
    return {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}


def _digest(sources: dict) -> str:
    return hashlib.sha256(json.dumps(sources, sort_keys=True).encode("utf-8")).hexdigest()


def test_t13_the_historical_phase2_closure_is_preserved_and_still_recomputes(record):
    """No se reescribe: el digesto de cierre sigue siendo verificable contra SU arbol, no transcrito."""
    historical = record["historical_closure"]
    assert historical["head"] == "d2cca46626ed5d45a792ec9456d46fb75fe87731"
    assert historical["phase2_digest"] == rs.PHASE2_DIGEST
    try:
        sources = _sources_at(historical["head"])
    except subprocess.CalledProcessError:
        pytest.skip("este clon no alcanza el commit de cierre, asi que la historia no se puede recalcular")
    assert len(sources) == historical["clinical_core_modules"] == 141
    assert _digest(sources) == historical["phase2_digest"]


def test_t13b_the_amended_digest_recomputes_and_exactly_one_source_changed(record):
    amended = record["amended"]
    now = _sources_now()
    assert _digest(now) == amended["phase2_amendment_1_digest"] == rs.PHASE2_AMENDMENT_1_DIGEST
    assert len(now) == amended["clinical_core_modules"] == 141
    try:
        historical = _sources_at(record["historical_closure"]["head"])
    except subprocess.CalledProcessError:
        pytest.skip("este clon no alcanza el commit de cierre")
    changed = sorted(k for k in set(historical) | set(now) if historical.get(k) != now.get(k))
    assert changed == amended["changed_sources"] == ["clinical_core/derived.py"]
    assert sorted(set(now) - set(historical)) == amended["added_sources"] == []
    assert sorted(set(historical) - set(now)) == amended["removed_sources"] == []


def test_t14_the_amendment_provenance_is_explicit(record):
    entry = dv.PARAMETERS[FIELD]
    assert entry[0] == dv.PROVISIONAL
    text = entry[1]
    assert "PHASE2_AMENDMENT_1" in text
    for denial in ("not a respiratory quotient", "shunt fraction", "FiO2 gain"):
        assert denial.lower() in text.lower(), denial
    assert "retained(G)" in text
    assert rs.PHASE2_STATUS == "PHASE2_CLOSED_PLUS_AMENDMENT_1" == record["status_phase_3_references"]
    assert record["pre_amendment_audit"]["verdict"] == "A_PARTIAL_TRANSMISSION_LOOP_STRUCTURALLY_SAFE"
    for forbidden in ("clinical validation", "runtime authority for the common core"):
        assert any(forbidden in item for item in record["not_claimed"]), forbidden
