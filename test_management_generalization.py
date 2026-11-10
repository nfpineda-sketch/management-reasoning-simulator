"""P3-137 a P3-144: generalizacion de la causalidad de manejo sobre el runtime integrado y certificado.

Todo corre sobre ``phase-3-runtime-integration`` con el nucleo PHASE2_AMENDMENT_1 certificado, por el camino de los
adaptadores de familia (el mismo que usa la sombra) y sin tocar ``clinical_core/``. Nada aqui ajusta una curva a
la salida heredada: se prueba direccion, temporalidad, especificidad causal, orden de dosis, reversibilidad y coste
de esperar, en REGIONES de prueba de desarrollo y nunca en un punto elegido.

Cada cifra de ``management_generalization_record.MEASURED`` se recalcula aqui: el registro no puede quedar viejo.
Las regiones son DEVELOPMENT_TEST_REGION: no son verdad clinica, ni dosis, ni estan aprobadas.
"""
import dataclasses
import json

import pytest

import management_causality as mc
import management_generalization_record as rec
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam
from clinical_core import asthma_migration as am
from clinical_core import derived as dv
from clinical_core import integration
from clinical_core import legacy_adapter
from clinical_core import opioid_migration as om
from clinical_core.state import CoreInvariantError

FIELD = "hypoventilation_oxygenation_transmission_fraction"
R = rec.TRANSMISSION_REGION["declared_R"]
WITNESSES = rec.TRANSMISSION_REGION["witnesses"]
ORDER = ("LOW", "CENTER_REFERENCE", "HIGH")
STATE_CHANNELS = ("V", "P", "T", "L", "G", "D", "fio2")
AUX_CHANNELS = ("central_availability", "mechanics_efficiency", "sympathetic_drive")
#: El unico canal de estado que un cambio de SpO2 alcanza por un lector YA certificado (deficit agudo -> impulso).
CERTIFIED_READER = "sympathetic_drive"


# El arnes: el camino del adaptador, y ademas los canales de estado ----------------------------------------------

def _action(kind, order_id, minute, fio2=0.21, **payload):
    return rs.MirroredAction(order_id, minute, kind, {"type": kind, **payload}, {}, fio2)


def _oxygen(minute=10, fio2=0.40, order_id="o1"):
    return [_action("oxygen", order_id, minute, fio2)]


def _naloxone(minute=20, order_id="n1"):
    return [_action("naloxone", order_id, minute)]


def _diuretic(minute=30, order_id="d1"):
    return [_action("diuretic", order_id, minute)]


def _reassess(minute=15):
    return [_action("reassessment", "w1", minute)]


def _linked(adapter_cls, migration, fraction):
    """El adaptador registrado, con el enlace declarado en una fraccion de prueba. El perfil comprometido no cambia."""
    profile = dataclasses.replace(migration.profile(), respiratory_quotient=R, **{FIELD: fraction})

    class Linked(adapter_cls):
        def profile(self, point):
            return profile

    return Linked()


@dataclasses.dataclass
class Run:
    series: dict
    trajectory: object
    runner: object


def _run(adapter, case, events=(), *, state=None, minutes=120) -> Run:
    runner = fam.ShadowPhysiologyRunner(adapter, case, fam.COMMITTED)
    runner.snapshot_ = adapter.snapshot()
    runner.anchors = adapter.anchors(case, fam.COMMITTED, dict(state) if state else None)
    runner.profile = adapter.profile(fam.COMMITTED)
    runner.family_writers = tuple(adapter.writers(case, fam.COMMITTED, dict(state) if state else None))
    runner.mirror(list(events))
    assert runner.advance(minutes, state=state), runner.failures
    trajectory = integration.run(runner.anchors, runner.contributors(), minutes, runner.profile)
    assert tuple(rs._digest_of(s) for s in trajectory.states[1:]) == runner.digests()      # el mismo camino
    series: dict = {}
    for result in runner.results:
        for key, value in dict(result.derived).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                series.setdefault(key, {})[result.minute] = float(value)
    for minute in range(1, minutes + 1):
        state_now = trajectory.states[minute]
        for name in STATE_CHANNELS:
            series.setdefault(name, {})[minute] = float(getattr(state_now, name))
        for name in AUX_CHANNELS:
            series.setdefault(name, {})[minute] = float(getattr(state_now.aux, name))
        try:
            breathing = dv.respiration(state_now, runner.anchors, runner.profile)
        except CoreInvariantError:                     # un perfil sin fisiologia acido-base (GI): no hay PaCO2 que leer
            continue
        series.setdefault("paco2", {})[minute] = breathing.paco2
        series.setdefault("ventilation", {})[minute] = breathing.ventilation
    return Run(series, trajectory, runner)


def _area(series, minutes):
    return sum(series[m] for m in range(1, minutes + 1))


def _first_moved(treated: Run, base: Run, names) -> dict:
    """{canal: primer minuto en que difiere} para los canales que se mueven; los demas no aparecen."""
    out = {}
    for name in names:
        minute = mc.effect_starts_at(treated.series[name], base.series[name], 1)
        if minute is not None:
            out[name] = minute
    return out


def _replays(run: Run) -> bool:
    """El artefacto capturado reproduce la corrida, digesto por digesto, y dos corridas iguales son iguales."""
    replayed = fam.replay_from_runner(run.runner)
    return [row["state_digest"] for row in replayed["results"]][1:] == list(run.runner.digests())


def _rounded(value, digits):
    if isinstance(value, dict):
        return {str(k): _rounded(v, digits) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_rounded(v, digits) for v in value]
    if isinstance(value, float):
        return round(value, digits)
    return value


# 0. El runtime sobre el que se mide ------------------------------------------------------------------------------

def test_p3_integration_the_runtime_is_the_certified_amendment_and_nothing_gained_authority():
    verdict = ev.core_lineage_verdict()
    assert verdict["ok"] is True and verdict["active_core"] == "PHASE2_AMENDMENT_1" and verdict["status"] == "CERTIFIED"
    assert verdict["historical_closure_digest"] == rs.PHASE2_DIGEST
    assert rec.RUNTIME["core_version"] == verdict["active_core"]
    assert rec.RUNTIME["core_digest"] == verdict["live_digest"] == rs.CORE_LINEAGE[-1].digest
    assert rec.RUNTIME["historical_closure_digest"] == rs.PHASE2_DIGEST
    # nada gano autoridad con la integracion ni con aquel ciclo, y en aquel ciclo nada entro en vivo: el
    # registro de entonces lo dice. El opioide entro DESPUES, por una autorizacion propia (P3-141, segunda
    # familia en vivo), y sigue sin autoridad.
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    assert rec.CHECKPOINT["live_shadow_families"] == ["gi_bleed"]
    assert rs.LIVE_FAMILIES == ("gi_bleed", "opioid")
    assert [name for name, adapter in fam.ADAPTERS.items() if adapter.live] == ["gi_bleed", "opioid"]
    assert rec.STATUS == "DEVELOPMENT_MEASUREMENT_NO_PARAMETER_ADOPTED"
    text = json.dumps(rec.all_records(), default=str)
    assert not any(label in text for label in mc.FORBIDDEN_LABELS)


# C3. La region de transmision, DERIVADA de la ecuacion certificada y no copiada ---------------------------------

REGION_CASES = {"opioid_35m": (om, fam.OpioidAdapter), "opioid_67f": (om, fam.OpioidAdapter),
                "asthma_49m": (am, fam.AsthmaAdapter), "asthma_24f": (am, fam.AsthmaAdapter)}
TARGET = rec.TRANSMISSION_REGION["target"]


def _spo2_60(case, fraction):
    migration, adapter_cls = REGION_CASES[case]
    return _run(_linked(adapter_cls, migration, fraction), case, minutes=60).series["spo2"][60]


def _bisect_floor(case):
    """La fraccion a la que la SpO2(60) sin tratar toca el piso del objetivo, hallada en la SIMULACION."""
    if _spo2_60(case, 1.0) >= TARGET["spo2_low"]:
        return None                                    # todo el intervalo unidad queda por encima del piso
    low, high = 0.0, 1.0
    for _ in range(50):
        middle = (low + high) / 2.0
        if _spo2_60(case, middle) >= TARGET["spo2_low"]:
            low = middle
        else:
            high = middle
    return low


def measure_region() -> dict:
    out = {}
    for case, (migration, adapter_cls) in REGION_CASES.items():
        off = _run(_linked(adapter_cls, migration, 0.0), case, minutes=60)
        base = off.series["spo2"][60]
        linked = dataclasses.replace(migration.profile(), respiratory_quotient=R)
        delta = off.series["paco2"][60] - dv.arrival_paco2_reference(off.runner.anchors, linked)
        # la misma cota por la formula: ODC^-1(base) - f * delta / R = ODC^-1(piso)
        analytic = (dv.pao2_from_oxygen_saturation(base) - dv.pao2_from_oxygen_saturation(TARGET["spo2_low"])) * R / delta
        out[case] = {"spo2_60_at_f0": base, "delta_paco2_60": delta, "f_upper_by_formula": analytic,
                     "f_upper_by_bisection": _bisect_floor(case), "spo2_60_at_f1": _spo2_60(case, 1.0),
                     "spo2_60_at_witnesses": {name: _spo2_60(case, WITNESSES[name]) for name in ORDER}}
    return out


@pytest.fixture(scope="module")
def region():
    return measure_region()


def test_p3_137a_the_region_is_derived_twice_and_the_two_derivations_agree(region):
    for case in ("opioid_35m", "opioid_67f"):
        found = region[case]
        assert found["f_upper_by_bisection"] == pytest.approx(found["f_upper_by_formula"], abs=1e-9), case
        assert _spo2_60(case, found["f_upper_by_bisection"]) == pytest.approx(TARGET["spo2_low"], abs=1e-6)
        # el techo del objetivo no ata: a fraccion 0 ya se esta dentro, y la transmision solo baja la SpO2
        assert TARGET["spo2_low"] < found["spo2_60_at_f0"] < TARGET["spo2_high"]
        assert found["spo2_60_at_f1"] < TARGET["spo2_low"]            # la transmision completa NO cabe
    for case in ("asthma_49m", "asthma_24f"):
        assert region[case]["f_upper_by_bisection"] is None           # asma no ata: todo [0, 1] queda sobre el piso
        assert region[case]["f_upper_by_formula"] > 1.0 and region[case]["spo2_60_at_f1"] > TARGET["spo2_low"]


def test_p3_137b_the_common_region_is_the_intersection_and_one_case_binds_it(region):
    bounds = {case: region[case]["f_upper_by_bisection"] for case in region if region[case]["f_upper_by_bisection"]}
    upper = min(bounds.values())
    assert min(bounds, key=bounds.get) == "opioid_35m" == rec.TRANSMISSION_REGION["bound_by"]
    assert rec.TRANSMISSION_REGION["common_region"] == (0.0, round(upper, 6))
    assert round(upper, 6) == 0.060621 and round(bounds["opioid_67f"], 6) == 0.233153
    # tres testigos de prueba dentro de la region; ninguno es "el valor"
    assert set(WITNESSES) == set(ORDER) and 0.0 < WITNESSES["LOW"] < WITNESSES["CENTER_REFERENCE"] < WITNESSES["HIGH"] <= upper
    assert rec.TRANSMISSION_REGION["center_reference_is_preferred"] is False
    for case in region:
        for name in ORDER:
            assert region[case]["spo2_60_at_witnesses"][name] >= TARGET["spo2_low"], (case, name)
    assert rec.TRANSMISSION_REGION["verdict"] == "RESPIRATORY_DEVELOPMENT_REGION_REPRODUCED"


def test_p3_137c_the_recorded_region_is_what_the_runtime_gives_now(region):
    assert _rounded(region, 6) == rec.MEASURED["region"]


# C4. Opioide: seis vias, en cada testigo de la region -----------------------------------------------------------

OPIOID_MINUTES = 90


def _opioid_arms(fraction):
    adapter = _linked(fam.OpioidAdapter, om, fraction)
    run = lambda events=(): _run(adapter, "opioid_35m", events, minutes=OPIOID_MINUTES)
    return {"untreated": run(), "oxygen": run(_oxygen()), "naloxone": run(_naloxone()),
            "oxygen_and_naloxone": run(_oxygen() + _naloxone()), "delayed_naloxone": run(_naloxone(60)),
            "wait": run(_reassess())}


@pytest.fixture(scope="module")
def opioid():
    return {name: _opioid_arms(WITNESSES[name]) for name in ORDER}


@pytest.mark.parametrize("witness", ORDER)
def test_p3_138a_untreated_runs_the_whole_chain_downhill(opioid, witness):
    series = opioid[witness]["untreated"].series
    end = OPIOID_MINUTES
    assert series["central_availability"][end] < series["central_availability"][1]
    assert series["respiratory_rate"][end] < series["respiratory_rate"][1]
    assert series["ventilation"][end] < series["ventilation"][1]
    assert series["paco2"][end] > series["paco2"][1] and mc.monotone_after(series["paco2"], 1, rising=True)
    assert series["spo2"][end] < series["spo2"][1] and mc.monotone_after(series["spo2"], 1, rising=False)


@pytest.mark.parametrize("witness", ORDER)
def test_p3_138b_oxygen_improves_saturation_and_reaches_no_part_of_ventilation(opioid, witness):
    base, treated = opioid[witness]["untreated"], opioid[witness]["oxygen"]
    assert mc.direction(treated.series["spo2"], base.series["spo2"], OPIOID_MINUTES, better="higher")
    for channel in ("central_availability", "respiratory_rate", "ventilation", "paco2"):
        assert mc.untouched(treated.series[channel], base.series[channel]), channel
    # el estado: solo el FiO2 (y el lector certificado de la SpO2), un minuto despues del pedido
    moved = _first_moved(treated, base, STATE_CHANNELS + AUX_CHANNELS)
    assert moved == {"fio2": 11, CERTIFIED_READER: 11}
    assert mc.no_effect_before(treated.series["spo2"], base.series["spo2"], 11)


@pytest.mark.parametrize("witness", ORDER)
def test_p3_138c_naloxone_moves_the_central_availability_first_and_the_rest_downstream(opioid, witness):
    base, treated = opioid[witness]["untreated"], opioid[witness]["naloxone"]
    # nada antes de darla, en ningun canal
    for channel in ("central_availability", "respiratory_rate", "ventilation", "paco2", "spo2", "delivery_rel"):
        assert mc.no_effect_before(treated.series[channel], base.series[channel], 20), channel
    # el UNICO canal de estado que escribe es la disponibilidad central (mas el lector certificado de la SpO2)
    moved = _first_moved(treated, base, STATE_CHANNELS + AUX_CHANNELS)
    # P3-141: la orden ejecutada en el minuto 20 aparece en el estado del 21 (como el oxigeno en el 11)
    assert moved == {"central_availability": 21, CERTIFIED_READER: 21}
    # y aguas abajo, cada eslabon en su direccion: FR y W arriba, PaCO2 abajo, SpO2 arriba
    onset = {channel: mc.effect_starts_at(treated.series[channel], base.series[channel], 1)
             for channel in ("central_availability", "respiratory_rate", "ventilation", "paco2", "spo2")}
    assert onset["central_availability"] <= onset["respiratory_rate"] <= onset["paco2"] <= onset["spo2"]
    end = OPIOID_MINUTES
    assert treated.series["central_availability"][end] > base.series["central_availability"][end]
    assert mc.direction(treated.series["respiratory_rate"], base.series["respiratory_rate"], end, better="higher")
    assert mc.direction(treated.series["ventilation"], base.series["ventilation"], end, better="higher")
    assert treated.series["paco2"][end] < base.series["paco2"][end]
    assert mc.direction(treated.series["spo2"], base.series["spo2"], end, better="higher")
    assert mc.no_paradox(treated.series["spo2"], base.series["spo2"], 20, better="higher")


def test_p3_138d_the_reversal_reaches_saturation_only_through_the_paco2():
    """Sin escritura directa naloxona -> SpO2: a fraccion 0 la reversion corrige la ventilacion y la SpO2 no se mueve."""
    arms = _opioid_arms(0.0)
    base, treated = arms["untreated"], arms["naloxone"]
    assert mc.untouched(treated.series["spo2"], base.series["spo2"])
    assert treated.series["paco2"][OPIOID_MINUTES] < base.series["paco2"][OPIOID_MINUTES]
    assert _first_moved(treated, base, STATE_CHANNELS + AUX_CHANNELS) == {"central_availability": 21}


@pytest.mark.parametrize("witness", ORDER)
def test_p3_138e_together_the_two_mechanisms_coexist_without_interfering(opioid, witness):
    arms, end = opioid[witness], OPIOID_MINUTES
    both = arms["oxygen_and_naloxone"].series
    for channel in ("central_availability", "respiratory_rate", "ventilation", "paco2"):
        assert mc.untouched(both[channel], arms["naloxone"].series[channel]), channel      # la rama ventilatoria
    assert both["fio2"][end] == arms["oxygen"].series["fio2"][end]                          # la rama del oxigeno
    assert both["spo2"][end] > max(arms["oxygen"].series["spo2"][end], arms["naloxone"].series["spo2"][end])


@pytest.mark.parametrize("witness", ORDER)
def test_p3_138f_a_delayed_reversal_loses_state_in_the_integral_even_where_the_endpoint_converges(opioid, witness):
    early, late, base = (opioid[witness][name].series for name in ("naloxone", "delayed_naloxone", "untreated"))
    assert mc.no_effect_before(late["respiratory_rate"], base["respiratory_rate"], 60)
    for channel in ("respiratory_rate", "ventilation", "spo2"):
        assert _area(late[channel], OPIOID_MINUTES) < _area(early[channel], OPIOID_MINUTES), channel
    assert _area(late["paco2"], OPIOID_MINUTES) > _area(early["paco2"], OPIOID_MINUTES)
    # tarde sigue siendo mejor que nunca, y el punto final se acerca al de la reversion temprana
    assert mc.direction(late["spo2"], base["spo2"], OPIOID_MINUTES, better="higher")
    gap_end = early["respiratory_rate"][OPIOID_MINUTES] - late["respiratory_rate"][OPIOID_MINUTES]
    gap_60 = early["respiratory_rate"][60] - late["respiratory_rate"][60]
    assert 0.0 <= gap_end < gap_60


@pytest.mark.parametrize("witness", ORDER)
def test_p3_138g_waiting_is_not_a_treatment_and_time_without_action_has_a_cost(opioid, witness):
    arms = opioid[witness]
    wait, base = arms["wait"], arms["untreated"]
    assert wait.runner.gaps == [] and len(wait.runner.contributors()) == len(base.runner.contributors())
    assert wait.runner.digests() == base.runner.digests()             # reevaluar no cambia la fisiologia
    assert base.series["spo2"][OPIOID_MINUTES] < base.series["spo2"][20]
    assert base.series["paco2"][OPIOID_MINUTES] > base.series["paco2"][20]


@pytest.mark.parametrize("witness", ORDER)
def test_p3_138h_every_arm_is_gap_free_and_replays_exactly(opioid, witness):
    for name, run in opioid[witness].items():
        assert run.runner.gaps == [] and run.runner.failures == [], name
        assert _replays(run), name
    again = _opioid_arms(WITNESSES[witness])
    assert all(again[name].runner.digests() == opioid[witness][name].runner.digests() for name in again)


def test_p3_138i_the_ventilatory_correction_is_visible_and_ordered_across_the_region(opioid):
    gains = [opioid[name]["naloxone"].series["spo2"][OPIOID_MINUTES]
             - opioid[name]["untreated"].series["spo2"][OPIOID_MINUTES] for name in ORDER]
    assert all(later > earlier > 0.5 for earlier, later in zip(gains, gains[1:])) and gains[0] > 0.5, gains
    assert rec.OPIOID["verdict"] == "OPIOID_MANAGEMENT_CAUSALITY_READY"
    assert rec.OPIOID["status"] == mc.READY_WITH_REGION


def measure_opioid(opioid) -> dict:
    out = {}
    for witness in ORDER:
        arms = opioid[witness]
        out[witness] = {name: {channel: run.series[channel][OPIOID_MINUTES]
                               for channel in ("respiratory_rate", "ventilation", "paco2", "spo2")}
                        for name, run in arms.items()}
        out[witness]["respiratory_rate_area"] = {name: _area(arms[name].series["respiratory_rate"], OPIOID_MINUTES)
                                                 for name in ("naloxone", "delayed_naloxone", "untreated")}
    return out


def test_p3_138j_the_recorded_matrix_is_what_the_runtime_gives_now(opioid):
    assert _rounded(measure_opioid(opioid), 3) == rec.MEASURED["opioid"]


# C5. Asma con la MISMA region, sin ajuste propio -----------------------------------------------------------------

ASTHMA_MINUTES = 120
REFUSED_BY_THE_CORE = "__refused_by_the_core__"
ASTHMA_PROBES = ("arrival", "writer_semantics", "untreated", "relief", "oxygen", "direct_g", "drive", "heart_rate",
                 "collapse", "consciousness")


def _asthma(case, fraction, events=()):
    return _run(_linked(fam.AsthmaAdapter, am, fraction), case, events, minutes=ASTHMA_MINUTES)


def _stage_probes(fraction) -> dict:
    """Las sondas PROPIAS de la etapa P2S-3, vueltas a correr con el enlace declarado en ``fraction`` (None: sin el)."""
    real = am.profile
    if fraction is not None:
        am.profile = lambda **changes: real(**{"respiratory_quotient": R, FIELD: fraction, **changes})
    try:
        out = {}
        untreated = None
        for name in ASTHMA_PROBES:
            try:
                if name == "untreated":
                    untreated = found = am.untreated()
                elif name == "consciousness":
                    found = am.consciousness(untreated if untreated is not None else am.untreated())
                else:
                    found = getattr(am, name)()
                out[name] = found
            except Exception as error:                 # un rechazo del nucleo es un resultado, no un fallo de la prueba
                out[name] = {"pass": None, REFUSED_BY_THE_CORE: f"{type(error).__name__}: {error}"}
        return out
    finally:
        am.profile = real


def _flat(value, prefix=""):
    out = {}
    for key, item in value.items():
        if isinstance(item, dict):
            out.update(_flat(item, f"{prefix}{key}."))
        else:
            out[f"{prefix}{key}"] = item
    return out


def _changed_conditions(off: dict, on: dict) -> dict:
    """{sonda: condiciones booleanas que cambian al declarar el enlace}, sin contar el 'pass' agregado."""
    out = {}
    for name in ASTHMA_PROBES:
        a, b = _flat(off[name]), _flat(on[name])
        changed = sorted({key.rsplit(".", 1)[-1] if name != "relief" else key
                          for key in a if isinstance(a[key], bool) and a[key] != b.get(key) and key != "pass"})
        if changed or REFUSED_BY_THE_CORE in on[name]:
            out[name] = "REFUSED" if REFUSED_BY_THE_CORE in on[name] else changed
    return out


@pytest.fixture(scope="module")
def asthma_probes():
    return {"off": _stage_probes(None), **{name: _stage_probes(WITNESSES[name]) for name in ORDER}}


@pytest.mark.parametrize("case", ["asthma_49m", "asthma_24f"])
@pytest.mark.parametrize("witness", ORDER)
def test_p3_139a_the_certified_mechanics_stay_primary_and_ventilation_is_bit_identical(case, witness):
    off, on = _asthma(case, 0.0), _asthma(case, WITNESSES[witness])
    for channel in ("mechanics_efficiency", "respiratory_rate", "ventilation", "paco2"):
        assert mc.untouched(on.series[channel], off.series[channel]), channel
    assert off.series["mechanics_efficiency"][ASTHMA_MINUTES] < off.series["mechanics_efficiency"][1]
    assert on.series["paco2"][ASTHMA_MINUTES] > on.series["paco2"][1]                   # la direccion del PaCO2
    # el estado: nada se mueve salvo el lector certificado de la SpO2; ningun lazo se despierta
    moved = _first_moved(on, off, STATE_CHANNELS + AUX_CHANNELS)
    assert set(moved) <= {CERTIFIED_READER}
    assert on.runner.gaps == [] and on.runner.failures == [] and _replays(on)


@pytest.mark.parametrize("case", ["asthma_49m", "asthma_24f"])
def test_p3_139b_oxygenation_follows_ventilation_in_the_plausible_direction_only(case):
    off = _asthma(case, 0.0)
    shifts = {}
    for witness in ORDER:
        on = _asthma(case, WITNESSES[witness])
        shift = [on.series["spo2"][m] - off.series["spo2"][m] for m in range(1, ASTHMA_MINUTES + 1)]
        # peor ventilacion nunca mejora la oxigenacion; el desplazamiento crece con el PaCO2, sin oscilar
        assert all(value < 0.0 for value in shift) and all(b <= a for a, b in zip(shift, shift[1:]))
        assert min(on.series["spo2"].values()) > 88.0 - 2.0 * (case == "asthma_49m")       # sin limite grave nuevo
        assert shift[-1] > -1.0
        shifts[witness] = shift[-1]
    assert shifts["HIGH"] < shifts["CENTER_REFERENCE"] < shifts["LOW"] < 0.0                 # ordenado por fraccion


@pytest.mark.parametrize("case", ["asthma_49m", "asthma_24f"])
def test_p3_139c_oxygen_still_works_in_asthma_and_does_not_touch_the_mechanics(case):
    """De paso fija la correccion de P3-141: el adaptador de asma CONSTRUYE el oxigeno que declara mapeado."""
    adapter = _linked(fam.AsthmaAdapter, am, WITNESSES["CENTER_REFERENCE"])
    base = _run(adapter, case, minutes=ASTHMA_MINUTES)
    treated = _run(adapter, case, _oxygen(), minutes=ASTHMA_MINUTES)
    assert treated.runner.gaps == []
    assert mc.direction(treated.series["spo2"], base.series["spo2"], ASTHMA_MINUTES, better="higher")
    for channel in ("mechanics_efficiency", "respiratory_rate", "ventilation", "paco2"):
        assert mc.untouched(treated.series[channel], base.series[channel]), channel


def test_p3_139d_the_stage_probes_change_only_where_the_link_is_defined_to_act(asthma_probes):
    """Las sondas de P2S-3 con el enlace declarado. Lo que cambia es, exactamente, la afirmacion pre-enlace de que
    "solo se mueve la mecanica": la SpO2 (y por ella la entrega y la FC) ahora siguen a la ventilacion. Es lo que el
    enlace ES, y P2T-5 lo certifico a transmision completa. Nada mas cambia, y el impulso hipoxemico queda rechazado."""
    off = asthma_probes["off"]
    assert all(off[name]["pass"] is True for name in ASTHMA_PROBES)
    for witness in ORDER:
        on = asthma_probes[witness]
        changed = _changed_conditions(off, on)
        assert changed == rec.ASTHMA["probe_conditions_that_change_with_the_link"], witness
        unchanged = [name for name in ASTHMA_PROBES if name not in changed]
        assert unchanged == rec.ASTHMA["probes_unchanged"] and all(on[name]["pass"] is True for name in unchanged)
        assert "HYPOXEMIC_FEEDBACK_LOOP_DEFERRED" in on["drive"][REFUSED_BY_THE_CORE]
        # y lo superado va en la direccion declarada: el alivio de la mecanica ahora SUBE la SpO2
        at = on["relief"]["at"]
        last = sorted(at, key=int)[-1]
        assert at[last]["relieved"]["spo2"] > at[last]["plain"]["spo2"]
        assert on["relief"]["relief_raises_W_lowers_paco2"] is True
    assert rec.ASTHMA["verdict"] == "RESPIRATORY_TRANSMISSION_GENERALIZES"
    assert rec.ASTHMA["region_used"] == rec.TRANSMISSION_REGION["common_region"]


def measure_asthma() -> dict:
    out = {}
    for case in ("asthma_49m", "asthma_24f"):
        off = _asthma(case, 0.0)
        out[case] = {}
        for witness in ORDER:
            on = _asthma(case, WITNESSES[witness])
            out[case][witness] = {"spo2_shift_60": on.series["spo2"][60] - off.series["spo2"][60],
                                  "spo2_shift_120": on.series["spo2"][120] - off.series["spo2"][120],
                                  "spo2_min": min(on.series["spo2"].values())}
    return out


def test_p3_139e_the_recorded_shifts_are_what_the_runtime_gives_now():
    assert _rounded(measure_asthma(), 4) == rec.MEASURED["asthma"]


# C6. El contraste educativo: soporte de oxigenacion frente a correccion ventilatoria ----------------------------

CONTRAST_AT = (5, 15, 25, 30, 45, 60, 90)
CONTRAST_CHANNELS = ("respiratory_rate", "ventilation", "paco2", "spo2", "delivery_rel")


def measure_contrast(opioid) -> dict:
    arms = opioid["CENTER_REFERENCE"]
    return {name: {minute: {channel: arms[name].series[channel][minute] for channel in CONTRAST_CHANNELS}
                   for minute in CONTRAST_AT}
            for name in ("untreated", "oxygen", "naloxone")}


def test_p3_140a_oxygen_makes_the_number_look_better_while_ventilation_keeps_failing(opioid):
    table = measure_contrast(opioid)
    for minute in (15, 25, 30, 45, 60, 90):
        plain, oxygen = table["untreated"][minute], table["oxygen"][minute]
        assert oxygen["spo2"] > plain["spo2"] + 4.0 and oxygen["delivery_rel"] > plain["delivery_rel"]
        assert (oxygen["respiratory_rate"], oxygen["ventilation"], oxygen["paco2"]) == (
            plain["respiratory_rate"], plain["ventilation"], plain["paco2"])
    paco2 = [table["oxygen"][minute]["paco2"] for minute in CONTRAST_AT]
    rate = [table["oxygen"][minute]["respiratory_rate"] for minute in CONTRAST_AT]
    assert all(b > a for a, b in zip(paco2, paco2[1:])) and all(b < a for a, b in zip(rate, rate[1:]))
    assert table["oxygen"][90]["paco2"] > 100.0 and table["oxygen"][90]["spo2"] > table["untreated"][5]["spo2"]


def test_p3_140b_the_reversal_corrects_ventilation_first_and_oxygenation_downstream(opioid):
    table = measure_contrast(opioid)
    for minute in (5, 15):                                             # antes de darla: identico a no tratar
        assert table["naloxone"][minute] == table["untreated"][minute]
    for minute in (25, 30, 45, 60, 90):
        plain, reversed_ = table["untreated"][minute], table["naloxone"][minute]
        assert reversed_["respiratory_rate"] > plain["respiratory_rate"]
        assert reversed_["ventilation"] > plain["ventilation"] and reversed_["paco2"] < plain["paco2"]
        assert reversed_["spo2"] > plain["spo2"] and reversed_["delivery_rel"] > plain["delivery_rel"]
        # y el oxigeno, en el mismo minuto, sigue teniendo MAS SpO2 con PEOR ventilacion: la cifra sola no distingue
        assert table["oxygen"][minute]["spo2"] > reversed_["spo2"]
        assert table["oxygen"][minute]["paco2"] > reversed_["paco2"]
    assert rec.EDUCATIONAL_CONTRAST["distinguishing_channels"] == ["respiratory_rate", "ventilation", "paco2"]
    assert rec.EDUCATIONAL_CONTRAST["not_distinguishing_alone"] == ["spo2", "delivery_rel"]


def test_p3_140c_the_recorded_table_is_what_the_runtime_gives_now(opioid):
    assert _rounded(measure_contrast(opioid), 3) == rec.MEASURED["contrast"]


# C7. Edema pulmonar: la descongestion, por el adaptador de desarrollo --------------------------------------------

EDEMA_CASE, EDEMA_MINUTES = "pulmonary_edema_58m", 180


def _edema_arms(witness):
    adapter = fam.PulmonaryEdemaAdapter.development(witness)
    run = lambda events=(): _run(adapter, EDEMA_CASE, events, minutes=EDEMA_MINUTES)
    return {"untreated": run(), "oxygen": run(_oxygen()), "decongestion": run(_diuretic()),
            "oxygen_and_decongestion": run(_oxygen() + _diuretic()), "delayed_decongestion": run(_diuretic(90)),
            "wait": run(_reassess())}


@pytest.fixture(scope="module")
def edema():
    return {name: _edema_arms(name) for name in ORDER}


def test_p3_141a_the_registered_adapter_is_unchanged_and_still_declares_the_gap():
    registered = fam.ADAPTERS["pulmonary_edema"]
    assert registered.decongestion_witness is None and registered.decongestion_per_min == 0.0
    assert registered.maps == ("oxygen",) and registered.live is False
    run = _run(registered, EDEMA_CASE, _diuretic(), minutes=60)
    assert [gap["kind"] for gap in run.runner.gaps] == ["diuretic"]
    assert "construction parameter" in run.runner.gaps[0]["why"]
    plain = _run(registered, EDEMA_CASE, minutes=60)
    assert run.runner.digests() == plain.runner.digests()            # el pedido no hace NADA en el adaptador registrado
    assert "decongestion" not in registered.snapshot().id


def test_p3_141b_the_region_is_the_familys_own_declared_rate_span():
    from clinical_core import edema_migration as em
    assert fam.EDEMA_DECONGESTION_REGION == (em.PROGRESSION[0], em.PROGRESSION[-1]) == (0.0025, 0.01)
    assert fam.EDEMA_DECONGESTION_WITNESSES == {"LOW": em.PROGRESSION[0], "CENTER_REFERENCE": em.DECONGESTION["per_min"],
                                                "HIGH": em.PROGRESSION[-1]}
    decision = rec.DECONGESTION_DECISION
    assert decision["region"] == fam.EDEMA_DECONGESTION_REGION and decision["classification"] == "DEVELOPMENT_TEST_REGION"
    assert decision["confidence"] >= 0.80 and decision["is_clinical_truth"] is False and decision["is_a_dose"] is False
    assert all(decision[key] for key in ("rationale", "evidence", "uncertainty", "falsifier"))
    with pytest.raises(ValueError):
        fam.PulmonaryEdemaAdapter.development("PREFERRED")
    snapshot = fam.PulmonaryEdemaAdapter.development("LOW").snapshot()
    assert snapshot.approved is False and "DEVELOPMENT_TEST_REGION" in snapshot.provenance[-1]


@pytest.mark.parametrize("witness", ORDER)
def test_p3_141c_untreated_congestion_progresses_and_everything_downstream_follows(edema, witness):
    series = edema[witness]["untreated"].series
    assert mc.monotone_after(series["L"], 1, rising=True) and mc.monotone_after(series["G"], 1, rising=True)
    assert mc.monotone_after(series["spo2"], 1, rising=False)
    assert series["delivery_rel"][EDEMA_MINUTES] < series["delivery_rel"][1]


@pytest.mark.parametrize("witness", ORDER)
def test_p3_141d_decongestion_lowers_lung_water_first_and_oxygenation_downstream(edema, witness):
    base, treated = edema[witness]["untreated"], edema[witness]["decongestion"]
    for channel in ("L", "G", "spo2", "delivery_rel"):
        assert mc.no_effect_before(treated.series[channel], base.series[channel], 30), channel
    # escribe L y nada mas: G es la consecuencia comun, la SpO2 llega por G, V P T y FiO2 no se tocan
    moved = _first_moved(treated, base, STATE_CHANNELS + AUX_CHANNELS)
    assert moved == {"L": 30, "G": 30, CERTIFIED_READER: 30}
    writes = {delta.channel.name for record in treated.trajectory.records for delta in record.deltas
              if "decongesting under treatment" in delta.description}
    assert writes == {"L"}
    # y el tratamiento mismo no escribe ningun canal: solo publica el momento en que empieza
    assert not [delta for record in treated.trajectory.records for delta in record.deltas
                if delta.source.id == "d1"]
    assert mc.monotone_after(treated.series["L"], 30, rising=False)
    assert mc.direction(treated.series["spo2"], base.series["spo2"], EDEMA_MINUTES, better="higher")
    assert mc.no_paradox(treated.series["spo2"], base.series["spo2"], 30, better="higher")
    assert treated.runner.gaps == [] and _replays(treated)


@pytest.mark.parametrize("witness", ORDER)
def test_p3_141e_it_is_reversible_to_the_arrival_congestion_and_never_beyond(edema, witness):
    treated = edema[witness]["decongestion"]
    arrival_spo2 = treated.runner.anchors.spo2
    assert min(treated.series["L"].values()) >= 0.0 and treated.series["L"][EDEMA_MINUTES] == 0.0
    assert max(treated.series["spo2"].values()) <= arrival_spo2 and treated.series["spo2"][EDEMA_MINUTES] == arrival_spo2


@pytest.mark.parametrize("witness", ORDER)
def test_p3_141f_oxygen_raises_saturation_and_never_touches_lung_water(edema, witness):
    base, treated = edema[witness]["untreated"], edema[witness]["oxygen"]
    assert mc.direction(treated.series["spo2"], base.series["spo2"], EDEMA_MINUTES, better="higher")
    assert mc.untouched(treated.series["L"], base.series["L"]) and mc.untouched(treated.series["G"], base.series["G"])
    assert _first_moved(treated, base, STATE_CHANNELS + AUX_CHANNELS) == {"fio2": 11, CERTIFIED_READER: 11}
    # juntos: la rama del agua pulmonar es la de la descongestion, y la SpO2 supera a cualquiera de los dos
    both, alone = edema[witness]["oxygen_and_decongestion"].series, edema[witness]["decongestion"].series
    assert mc.untouched(both["L"], alone["L"])
    assert both["spo2"][EDEMA_MINUTES] > max(alone["spo2"][EDEMA_MINUTES], treated.series["spo2"][EDEMA_MINUTES])


@pytest.mark.parametrize("witness", ORDER)
def test_p3_141g_delay_costs_in_the_integral_and_waiting_is_not_a_treatment(edema, witness):
    arms = edema[witness]
    early, late, base = (arms[name].series for name in ("decongestion", "delayed_decongestion", "untreated"))
    assert mc.no_effect_before(late["L"], base["L"], 90)
    assert _area(early["spo2"], EDEMA_MINUTES) > _area(late["spo2"], EDEMA_MINUTES) > _area(base["spo2"], EDEMA_MINUTES)
    assert _area(early["L"], EDEMA_MINUTES) < _area(late["L"], EDEMA_MINUTES) < _area(base["L"], EDEMA_MINUTES)
    assert mc.direction(late["spo2"], base["spo2"], EDEMA_MINUTES, better="higher")
    assert arms["wait"].runner.digests() == arms["untreated"].runner.digests()      # reevaluar no es un tratamiento
    assert [gap["kind"] for gap in arms["wait"].runner.gaps] == ["reassessment"]     # se registra, no se construye


def test_p3_141h_a_faster_rate_recovers_sooner_and_one_therapy_begins_once(edema):
    back = {}
    for witness in ORDER:
        series = edema[witness]["decongestion"].series
        back[witness] = min(m for m in range(30, EDEMA_MINUTES + 1) if series["L"][m] == 0.0)
    assert back["HIGH"] < back["CENTER_REFERENCE"] < back["LOW"]                              # orden de dosis
    areas = [_area(edema[w]["decongestion"].series["spo2"], EDEMA_MINUTES) for w in ORDER]
    assert areas[0] < areas[1] < areas[2]
    adapter = fam.PulmonaryEdemaAdapter.development("CENTER_REFERENCE")
    twice = _run(adapter, EDEMA_CASE, _diuretic(30, "d1") + [_action("nitroglycerin", "n2", 45)], minutes=120)
    once = _run(adapter, EDEMA_CASE, _diuretic(30, "d1"), minutes=120)
    assert twice.runner.digests() == once.runner.digests()
    assert [gap["order_id"] for gap in twice.runner.gaps] == ["n2"] and "already begun" in twice.runner.gaps[0]["why"]


def test_p3_141i_the_contract_verdicts_do_not_depend_on_where_in_the_region_the_rate_is():
    """La razon de la confianza: los veredictos causales son los mismos muy por fuera de la region (x0,4 y x2)."""
    from clinical_core import edema_migration as em
    from clinical_core.modules.pulmonary_edema import DecongestiveTreatment
    adapter = fam.ADAPTERS["pulmonary_edema"]
    anchors, profile = adapter.anchors(EDEMA_CASE, fam.COMMITTED, None), adapter.profile(fam.COMMITTED)
    plain = integration.run(anchors, (em.writer(em.MID),), EDEMA_MINUTES, profile)
    spo2 = lambda trajectory: [trajectory.derived()[m].to_dict()["spo2"] for m in range(1, EDEMA_MINUTES + 1)]
    previous = None
    for rate in (0.001, 0.0025, 0.005, 0.01, 0.02):
        treated = integration.run(anchors, (em.writer(em.MID, rate), DecongestiveTreatment("tx", 30)),
                                  EDEMA_MINUTES, profile)
        levels = [state.L for state in treated.states]
        assert levels[:30] == [state.L for state in plain.states][:30]                          # temporalidad
        assert all(b <= a for a, b in zip(levels[30:], levels[31:])) and min(levels) >= 0.0     # direccion, L_rev
        assert max(spo2(treated)) <= anchors.spo2 and sum(spo2(treated)) > sum(spo2(plain))
        assert [s.V for s in treated.states] == [s.V for s in plain.states]                     # especificidad
        if previous is not None:
            assert sum(spo2(treated)) > previous                                                # orden de dosis
        previous = sum(spo2(treated))


def measure_edema(edema) -> dict:
    out = {}
    for witness in ORDER:
        arms = edema[witness]
        series = arms["decongestion"].series
        out[witness] = {
            "rate_per_min": fam.EDEMA_DECONGESTION_WITNESSES[witness],
            "back_to_arrival_at_minute": min(m for m in range(30, EDEMA_MINUTES + 1) if series["L"][m] == 0.0),
            "spo2_at_180": {name: run.series["spo2"][EDEMA_MINUTES] for name, run in arms.items()},
            "lung_water_at_180": {name: run.series["L"][EDEMA_MINUTES] for name, run in arms.items()},
            "spo2_area": {name: _area(arms[name].series["spo2"], EDEMA_MINUTES)
                          for name in ("untreated", "decongestion", "delayed_decongestion")}}
    return out


def test_p3_141j_the_recorded_matrix_and_the_verdict(edema):
    assert _rounded(measure_edema(edema), 4) == rec.MEASURED["edema"]
    assert rec.EDEMA["verdict"] == "PULMONARY_EDEMA_MANAGEMENT_CAUSALITY_READY"
    assert rec.EDEMA["status"] == mc.READY_WITH_REGION
    assert rec.EDEMA["respiratory_rate_follows"] is False                # limite declarado: la FR no lee L en este perfil
    untreated, treated = edema["HIGH"]["untreated"].series, edema["HIGH"]["decongestion"].series
    assert mc.untouched(treated["respiratory_rate"], untreated["respiratory_rate"])


# P3-141 bis. La correccion del oxigeno descartado en silencio ------------------------------------------------------

@pytest.mark.parametrize("family,case", [("pulmonary_edema", "pulmonary_edema_58m"), ("asthma", "asthma_49m"),
                                         ("pulmonary_embolism", "pulmonary_embolism_61m"), ("opioid", "opioid_35m"),
                                         ("acs", "acs_70f_left_main"), ("gi_bleed", "gi_bleed_57m")])
def test_p3_141k_an_adapter_builds_every_action_it_lists_as_mapped(family, case):
    """Antes, tres adaptadores listaban el oxigeno como mapeado y su sombra lo ignoraba: ni efecto ni hueco."""
    from clinical_core.interventions.oxygen import Oxygen
    adapter = fam.ADAPTERS[family]
    assert "oxygen" in adapter.maps
    state = dict(legacy_adapter.bank_case(case)) if family == "gi_bleed" else None
    built, gaps = adapter.interventions(_oxygen(), state)
    assert [type(item) for item in built if isinstance(item, Oxygen)] == [Oxygen] and gaps == []
    base = _run(adapter, case, state=state, minutes=60)
    treated = _run(adapter, case, _oxygen(), state=state, minutes=60)
    assert treated.series["spo2"][60] > base.series["spo2"][60]
    assert treated.series["fio2"][60] == 0.40 and base.series["fio2"][60] < 0.40


# C8. ACS: la llegada en vivo no tiene un mapeo certificado existente ------------------------------------------------

def test_p3_142_no_existing_certified_mapping_expresses_a_live_acs_arrival():
    # el UNICO mapeo certificado de estado vivo -> anclas rechaza toda familia que no sea GI
    assert set(legacy_adapter.FAMILY_CASE_PARAMETER_RULES) == {"gi_bleed"}
    with pytest.raises(legacy_adapter.UnsupportedScenario) as refused:
        legacy_adapter.anchors_from_legacy({"engine_family": "acs"})
    assert "no case mapping or approved default rule" in str(refused.value)
    # y la referencia de ACS no lee el encuentro: da la llegada de UN caso redactado, con cinco parametros de caso
    # declarados sonda sintetica en bandas de ese caso
    adapter = fam.ADAPTERS["acs"]
    fixed = adapter.anchors("acs_70f_left_main", fam.COMMITTED, None)
    assert fixed == adapter.anchors("acs_70f_left_main", fam.COMMITTED, {"family_state": {"baseline": {"sbp": 60.0}}})
    assert sorted(name for name, how in fixed.declared.items() if how == "synthetic_probe") == sorted(
        rec.ACS["case_parameters_with_no_live_rule"])
    assert adapter.cases == ("acs_70f_left_main",) and adapter.live is False
    assert "acs" not in rs.LIVE_FAMILIES and "ARRIVAL_MAPPING" in fam.ACS_LIVE_GAP
    assert rec.ACS["verdict"] == "ACS_ARRIVAL_MAPPING_REQUIRES_NEW_SEMANTICS"
    assert rec.ACS["offline_management_chain"] == mc.CAUSALLY_READY


# C9. La suite multifamilia, con el contrato generico ----------------------------------------------------------------

FAMILY_CASE = {"gi_bleed": "gi_bleed_57m", "acs": "acs_70f_left_main", "opioid": "opioid_35m",
               "pulmonary_edema": "pulmonary_edema_58m", "asthma": "asthma_49m",
               "pulmonary_embolism": "pulmonary_embolism_61m"}


def _gi(events=(), minutes=120, endoscopy=None):
    state = dict(legacy_adapter.bank_case("gi_bleed_57m"))
    if endoscopy is not None:
        state.setdefault("family_state", {})["endoscopy_at"] = endoscopy
    return _run(fam.ADAPTERS["gi_bleed"], "gi_bleed_57m", events, state=state, minutes=minutes)


def _acs(opens_at=None, minutes=180):
    state = {"family_state": {} if opens_at is None else {"reperfusion_at": opens_at}}
    events = [] if opens_at is None else [_action("reperfusion_referral", "r1", 12)]
    return _run(fam.ADAPTERS["acs"], "acs_70f_left_main", events, state=state, minutes=minutes)


def _contract(*, treated, base, primary, observable, better, activation, by_dose, dose_better, early, late,
              reversible, minutes) -> dict:
    """El contrato generico, evaluado igual para toda familia. None: el punto no aplica a esa intervencion."""
    moved = _first_moved(treated, base, STATE_CHANNELS + AUX_CHANNELS)
    out = {
        "DIRECTION": mc.direction(treated.series[observable], base.series[observable], minutes, better=better),
        "TEMPORALITY": (mc.no_effect_before(treated.series[observable], base.series[observable], activation)
                        and mc.no_effect_before(treated.series[primary], base.series[primary], activation)
                        and moved.get(primary) is not None
                        and moved[primary] <= mc.effect_starts_at(treated.series[observable],
                                                                   base.series[observable], 1)),
        "CAUSAL_SPECIFICITY": primary in moved and min(moved.values()) == moved[primary],
        "MAGNITUDE_PLAUSIBILITY": mc.no_paradox(treated.series[observable], base.series[observable], activation,
                                                better=better),
        "DOSE_ORDERING": None if by_dose is None else mc.dose_ordered(by_dose, dose_better[0], better=dose_better[1]),
        "REVERSIBILITY": reversible,
        "TIME_WITHOUT_ACTION": (None if early is None else
                                (_area(early, minutes) > _area(late, minutes) if better == "higher"
                                 else _area(early, minutes) < _area(late, minutes))),
        "SAFETY": treated.runner.failures == [] and treated.runner.gaps == [] and _replays(treated),
    }
    out["moved_state_channels"] = sorted(moved)
    return out


@pytest.fixture(scope="module")
def matrix(opioid, edema):
    out = {}
    # GI: volumen. Transfusion, con orden de dosis por unidades.
    base = _gi()
    blood = {units: _gi([_action("blood", f"b{units}", 20, units=units)]) for units in (1, 2, 4)}
    out["gi_bleed"] = _contract(
        treated=blood[2], base=base, primary="V", observable="sbp", better="higher", activation=20,
        by_dose={units: run.series["sbp"] for units, run in blood.items()}, dose_better=(90, "higher"),
        early=_gi([_action("blood", "b-now", 10, units=2)]).series["sbp"],
        late=_gi([_action("blood", "b-late", 60, units=2)]).series["sbp"], reversible=None, minutes=120)
    # ACS: bomba. Reperfusion, sobre el reloj del motor.
    plain, opened = _acs(), _acs(60)
    out["acs"] = _contract(
        treated=opened, base=plain, primary="P", observable="sbp", better="higher", activation=60,
        by_dose=None, dose_better=None, early=_acs(60).series["sbp"], late=_acs(120).series["sbp"],
        reversible=None, minutes=180)
    # Opioide: impulso central -> ventilacion -> oxigenacion. Naloxona, en el testigo central de la region.
    arms = opioid["CENTER_REFERENCE"]
    out["opioid"] = _contract(
        treated=arms["naloxone"], base=arms["untreated"], primary="central_availability", observable="spo2",
        better="higher", activation=20,
        by_dose={WITNESSES[w]: {m: opioid[w]["naloxone"].series["spo2"][m] - opioid[w]["untreated"].series["spo2"][m]
                                for m in range(1, OPIOID_MINUTES + 1)} for w in ORDER},
        dose_better=(OPIOID_MINUTES, "higher"),
        early=arms["naloxone"].series["spo2"], late=arms["delayed_naloxone"].series["spo2"],
        reversible=arms["naloxone"].series["paco2"][OPIOID_MINUTES] < arms["untreated"].series["paco2"][1],
        minutes=OPIOID_MINUTES)
    # Edema: agua pulmonar. Descongestion, en el testigo central de la region.
    arms = edema["CENTER_REFERENCE"]
    out["pulmonary_edema"] = _contract(
        treated=arms["decongestion"], base=arms["untreated"], primary="L", observable="spo2", better="higher",
        activation=30,
        by_dose={fam.EDEMA_DECONGESTION_WITNESSES[w]: {m: _area(edema[w]["decongestion"].series["spo2"], m)
                                                       for m in (EDEMA_MINUTES,)} for w in ORDER},
        dose_better=(EDEMA_MINUTES, "higher"),
        early=arms["decongestion"].series["spo2"], late=arms["delayed_decongestion"].series["spo2"],
        reversible=arms["decongestion"].series["L"][EDEMA_MINUTES] == 0.0, minutes=EDEMA_MINUTES)
    return out


@pytest.mark.parametrize("family", ["gi_bleed", "acs", "opioid", "pulmonary_edema"])
def test_p3_143a_each_complete_pathway_passes_the_whole_generic_contract(matrix, family):
    found = matrix[family]
    for item in mc.STANDARD:
        if item == "CROSS_FAMILY_CONSISTENCY":
            continue                                                  # se evalua entre familias, abajo
        assert found[item] in (True, None), (family, item, found)
        assert (found[item] is None) == (item in rec.READINESS[family]["not_applicable"]), (family, item)
    assert rec.READINESS[family]["primary_state_channel"] in found["moved_state_channels"]
    assert rec.READINESS[family]["complete_pathway"] is True


def test_p3_143b_the_two_incomplete_families_say_exactly_what_is_missing():
    # asma: el tratamiento que la define no tiene escritor; se declara y no se simula
    asthma = _run(fam.ADAPTERS["asthma"], "asthma_49m", [_action("bronchodilator", "b1", 20)], minutes=60)
    assert "BRONCHODILATOR_WRITER_DEFERRED" in asthma.runner.gaps[0]["why"]
    assert asthma.runner.digests() == _run(fam.ADAPTERS["asthma"], "asthma_49m", minutes=60).runner.digests()
    assert rec.READINESS["asthma"]["status"] == mc.MISSING_TREATMENT_WRITER
    # TEP: no hay mecanismo de tratamiento en el escritor de la familia
    embolism = _run(fam.ADAPTERS["pulmonary_embolism"], "pulmonary_embolism_61m",
                    [_action("thrombolysis", "t1", 20), _action("anticoagulation", "a1", 20)], minutes=60)
    assert sorted(gap["kind"] for gap in embolism.runner.gaps) == ["anticoagulation", "thrombolysis"]
    assert all("not modelled" in gap["why"] for gap in embolism.runner.gaps)
    assert rec.READINESS["pulmonary_embolism"]["status"] == mc.MISSING_COMMON_MECHANISM
    for family in ("asthma", "pulmonary_embolism"):
        assert rec.READINESS[family]["complete_pathway"] is False


def test_p3_143c_oxygen_is_consistent_across_the_six_families_and_writes_no_primary_channel():
    """CROSS_FAMILY_CONSISTENCY: la misma intervencion comun actua igual en todas, y solo por la oxigenacion."""
    for family, case in FAMILY_CASE.items():
        adapter = fam.ADAPTERS[family]
        state = dict(legacy_adapter.bank_case(case)) if family == "gi_bleed" else None
        base = _run(adapter, case, state=state, minutes=90)
        treated = _run(adapter, case, _oxygen(), state=state, minutes=90)
        assert mc.direction(treated.series["spo2"], base.series["spo2"], 90, better="higher"), family
        moved = _first_moved(treated, base, STATE_CHANNELS + AUX_CHANNELS)
        assert moved.get("fio2") == 11 and "fio2" in moved, family
        primary = rec.READINESS[family]["primary_state_channel"]
        assert primary not in moved, (family, moved)                  # el oxigeno no escribe el canal primario
        assert treated.runner.gaps == [] and treated.runner.failures == [], family


def test_p3_143d_the_primary_channels_of_the_complete_pathways_are_all_different(matrix):
    complete = [family for family, row in rec.READINESS.items() if row["complete_pathway"]]
    assert complete == ["gi_bleed", "acs", "opioid", "pulmonary_edema"] == rec.CHECKPOINT["complete_pathways"]
    channels = [rec.READINESS[family]["primary_state_channel"] for family in complete]
    assert len(set(channels)) == len(channels) == 4 and channels == ["V", "P", "central_availability", "L"]
    mechanisms = [rec.READINESS[family]["mechanism"] for family in complete]
    assert len(set(mechanisms)) == 4
    # cada tratamiento mueve SU canal primario, y lo mueve primero (CAUSAL_SPECIFICITY). Lo que se mueve despues son
    # consecuencias declaradas: la reperfusion de ACS baja tambien el agua pulmonar por el escritor de congestion de su
    # propia familia, y por eso L aparece en ACS sin ser su canal primario
    for family in complete:
        assert rec.READINESS[family]["primary_state_channel"] in matrix[family]["moved_state_channels"], family
        assert matrix[family]["CAUSAL_SPECIFICITY"] is True, family
    assert "L" in matrix["acs"]["moved_state_channels"] and "P" not in matrix["pulmonary_edema"]["moved_state_channels"]
    assert rec.CHECKPOINT["complete_pathway_count"] == 4
    assert rec.CHECKPOINT["verdict"] == "A_MULTIFAMILY_MANAGEMENT_CAUSALITY_VALIDATED_FOR_DEVELOPMENT"


def test_p3_143e_the_recorded_matrix_is_what_the_runtime_gives_now(matrix):
    assert {family: {item: value for item, value in row.items() if item != "moved_state_channels"}
            for family, row in matrix.items()} == rec.MEASURED["contract"]
    assert {family: row["moved_state_channels"] for family, row in matrix.items()} == rec.MEASURED["moved_state_channels"]


# C10. El punto de control y lo que NO afirma --------------------------------------------------------------------------

def test_p3_144_the_checkpoint_states_its_limits_and_every_development_decision_is_labelled():
    checkpoint = rec.CHECKPOINT
    assert checkpoint["threshold"] == 4 and checkpoint["complete_pathway_count"] >= checkpoint["threshold"]
    # el punto de control de AQUEL ciclo: solo GI estaba en vivo. La lista de hoy es la de entonces mas la
    # familia autorizada despues, y nada mas.
    assert checkpoint["live_shadow_families"] == ["gi_bleed"]
    assert list(rs.LIVE_FAMILIES) == checkpoint["live_shadow_families"] + ["opioid"]
    assert checkpoint["pathways_that_depend_on_a_development_region"] == ["opioid", "pulmonary_edema"]
    assert checkpoint["is_resident_deployment_readiness"] is False and checkpoint["is_clinical_validation"] is False
    for decision in rec.DEVELOPMENT_TEST_DECISIONS:
        assert decision["classification"] == "DEVELOPMENT_TEST_REGION" and decision["is_clinical_truth"] is False
        assert decision["confidence"] >= 0.80
        assert all(decision[key] for key in ("quantity", "region", "rationale", "uncertainty", "falsifier"))
    assert [d["quantity"].split(",")[0] for d in rec.DEVELOPMENT_TEST_DECISIONS] == [
        FIELD, "PulmonaryEdema decongestion rate"]
    gates = [gate["gate"] for gate in rec.PILOT_READINESS_REVIEW_PATH["remaining_gates"]]
    assert gates == ["runtime exposure", "UI exposure", "trace capture", "scoring isolation", "faculty review",
                     "case selection", "failure visibility", "rollback", "resident-facing safeguards"]
    assert rec.PILOT_READINESS_REVIEW_PATH["modifies_the_frozen_first_pilot"] is False
    assert rec.PILOT_READINESS_REVIEW_PATH["is_design_only"] is True
