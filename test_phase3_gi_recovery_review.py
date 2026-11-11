"""P3-181 a P3-187: revision de la temporalidad de la RECUPERACION de la consciencia sistemica de GI (2026-11-11).

Nada ejecutable cambia en este ciclo: ni el nucleo comun, ni los testigos, ni la capa de sombra. Lo que se fija es la
MEDIDA que explica por que la ley aislada da 3,0 / 4,0 / 4,9 min (0,80 -> < 0,50) y la trayectoria completa da 0 a 2 min
desde la entrada en la region de recuperacion, y la demostracion de que ninguna constante de bajada lo arregla bajo la ley
certificada: es una decision docente (veredicto B), con una pregunta precisa.

Registro medido: ``docs/revision/PHASE3_GI_RECOVERY_REVIEW.json``. Los dos casos GI, los tres testigos, cada testigo
tratado en SU PROPIO primer minuto SIN RESPUESTA (asi cada uno entra en su recuperacion sustancialmente alterado).
"""
import json
import math
from pathlib import Path

import pytest

import runtime_shadow as rs
import runtime_shadow_families as fam
import test_gi_amendment_2_series as series
from clinical_core import amendment_2 as a2
from clinical_core import systemic_consciousness as sc

ROOT = Path(__file__).resolve().parent
RECORD = json.loads((ROOT / "docs" / "revision" / "PHASE3_GI_RECOVERY_REVIEW.json").read_text(encoding="utf-8"))
SERIES = json.loads((ROOT / "docs" / "revision" / "PHASE3_GI_AMENDMENT_2_SERIES.json").read_text(encoding="utf-8"))
WITNESSES = list(sc.WITNESSES)
CASES = ("gi_bleed_57m", "gi_bleed_72f")
KEYS = [f"{case}/{name}" for case in CASES for name in WITNESSES]
EVENTS = ("T_ORDER", "T_EFFECT", "T_SIGNAL_BEGINS_TO_FALL", "T_TARGET_BELOW_F", "T_F_PEAK", "T_F_BELOW_0_80",
          "T_CATEGORY_IMPROVES", "T_RECOVERY_REGION_ENTRY", "T_F_BELOW_0_50", "T_CATEGORY_NORMAL")


def _recomputed(key, *, clear_tau=None, law="certified"):
    """F recalculada FUERA de linea sobre la serie de entrega registrada de una corrida (exacta: F no realimenta nada)."""
    item, profile = RECORD["delivery_series"][key], sc.WITNESSES[key.split("/")[1]]
    return series.f_course(item["relative_delivery"], profile, item["F_at_first_minute"], clear_tau=clear_tau, law=law)


def _after_entry(key, *, clear_tau=None, law="certified"):
    """(F al entrar en la region de recuperacion, minutos desde la entrada hasta F < 0,50) bajo una constante o una ley."""
    item, profile = RECORD["delivery_series"][key], sc.WITNESSES[key.split("/")[1]]
    course = _recomputed(key, clear_tau=clear_tau, law=law)
    minutes = [item["first_minute"] + index for index in range(len(course))]
    start = minutes.index(item["order_minute"])
    entry = next(index for index in range(start, len(course)) if item["relative_delivery"][index] >= profile.delivery_normal)
    peak = max(range(start, len(course)), key=lambda index: (course[index], -index))
    below = next((index for index in range(peak + 1, len(course)) if course[index] < 0.50), None)
    return course[entry], None if below is None else below - entry


# -- P3-181: el orden exacto de los eventos ------------------------------------------------------------------------------------

def test_the_record_covers_both_cases_and_the_three_witnesses_each_treated_at_its_own_unresponsive_minute():
    assert sorted(RECORD["events"]) == sorted(KEYS) == sorted(RECORD["timelines"]) == sorted(RECORD["delivery_series"])
    for key in KEYS:
        events = RECORD["events"][key]
        assert events["category_at_order"] == 3 and 0.80 <= events["F_at_order"] < 0.82, key
        untreated = SERIES["runs"][f"{key.split('/')[0]}/untreated"]["witnesses"][key.split("/")[1]]["order"]["unresponsive"]
        assert events["T_ORDER"] == untreated, key                       # tratado en su primer minuto SIN RESPUESTA


@pytest.mark.parametrize("key", KEYS)
def test_the_exact_event_ordering_of_a_recovery(key):
    """orden < efecto = el objetivo empieza a caer = el objetivo queda bajo F = pico de F < F bajo 0,80 = la categoria mejora
    < ENTRADA en la region de recuperacion <= F bajo 0,50 < categoria normal."""
    e = RECORD["events"][key]
    assert all(e[name] is not None for name in EVENTS), key
    assert e["T_ORDER"] + 1 == e["T_EFFECT"] == e["T_SIGNAL_BEGINS_TO_FALL"] == e["T_TARGET_BELOW_F"] == e["T_F_PEAK"]
    assert e["T_F_PEAK"] < e["T_F_BELOW_0_80"] == e["T_CATEGORY_IMPROVES"] < e["T_RECOVERY_REGION_ENTRY"]
    assert e["T_RECOVERY_REGION_ENTRY"] <= e["T_F_BELOW_0_50"] < e["T_CATEGORY_NORMAL"]
    # la entrada llega 8 o 9 minutos despues de la orden: es el tiempo de la fisiologia aguas arriba, no de F
    assert e["minutes_order_to_entry"] in (8, 9)


def test_most_of_the_0_80_to_0_50_descent_is_already_done_when_the_upstream_enters_the_recovery_region():
    """P3-181A, cuantificado. F deja 0,80 seis a ocho minutos ANTES de cruzar 0,50, y entra en la region de recuperacion en
    0,43 a 0,56: del 80 % al 100 % del descenso de 0,80 a 0,50 ya ocurrio. Por eso desde la entrada quedan 0 a 2 minutos."""
    for key in KEYS:
        e, profile = RECORD["events"][key], sc.WITNESSES[key.split("/")[1]]
        assert 0.43 <= e["F_at_entry"] <= 0.57, key
        assert e["share_of_the_0_80_to_0_50_descent_done_before_entry"] >= 0.79, key
        assert e["minutes_entry_to_below_0_50"] in (0, 1, 2), key
        assert e["minutes_below_0_80_to_below_0_50"] in (6, 7, 8), key
        # la ley aislada, que la region certificada cumple exactamente: 3 a 5 minutos de 0,80 a 0,50 sin señal
        assert 3.0 <= profile.burden_clear_tau * math.log(0.8 / 0.5) <= 5.0
        # y lo que queda tras entrar es lo que esa misma ley predice desde donde F estaba al entrar
        predicted = 0.0 if e["F_at_entry"] <= 0.50 else profile.burden_clear_tau * math.log(e["F_at_entry"] / 0.50)
        assert abs(e["minutes_entry_to_below_0_50"] - predicted) <= 1.0, key


@pytest.mark.parametrize("key", KEYS)
def test_the_offline_recomputation_is_the_certified_law_exactly_and_a_closed_form_agrees(key):
    """Control de todo lo que sigue: recalcular F fuera de linea desde la entrega registrada da la F registrada, exacta. Y una
    forma cerrada independiente (objetivo en rampa lineal) predice F en la entrada."""
    item, profile = RECORD["delivery_series"][key], sc.WITNESSES[key.split("/")[1]]
    assert _recomputed(key) == item["F_recorded"]
    minutes = [item["first_minute"] + index for index in range(len(item["relative_delivery"]))]
    e = RECORD["events"][key]
    start, entry = minutes.index(e["T_EFFECT"]), minutes.index(e["T_RECOVERY_REGION_ENTRY"])
    target = lambda index: sc.delivery_failure(item["relative_delivery"][index], profile)
    s0, f0, span = target(start), item["F_recorded"][start], entry - start
    slope, tau = s0 / span, profile.burden_clear_tau
    closed = tau * slope * (1 - math.exp(-span / tau)) + (f0 - s0) * math.exp(-span / tau)
    assert abs(closed - item["F_recorded"][entry]) <= 0.035, (key, closed, item["F_recorded"][entry])


# -- P3-182: la region de recuperacion ---------------------------------------------------------------------------------------------

def test_the_recovery_region_is_the_designs_own_event_the_signal_is_gone():
    definition = RECORD["recovery_region_definition"]
    assert definition["chosen"] == "C" and set(definition["rejected"]) == {"A", "B", "D"}
    assert "once the signal is gone" in sc.REGIONS["burden_clear_tau"][2]
    for profile in sc.WITNESSES.values():
        for step in range(0, 121):
            delivery = step / 100
            assert (sc.delivery_failure(delivery, profile) == 0.0) == (delivery >= profile.delivery_normal)
    # ningun evento se redefinio para que el tiempo pase: la entrada registrada es ese cruce, y nada mas
    for key in KEYS:
        item, profile = RECORD["delivery_series"][key], sc.WITNESSES[key.split("/")[1]]
        minutes = [item["first_minute"] + index for index in range(len(item["relative_delivery"]))]
        start = minutes.index(item["order_minute"])
        crossing = next(minutes[index] for index in range(start, len(minutes))
                        if item["relative_delivery"][index] >= profile.delivery_normal)
        assert crossing == RECORD["events"][key]["T_RECOVERY_REGION_ENTRY"]


# -- P3-183: ninguna constante de bajada lo resuelve bajo la ley certificada ----------------------------------------------------

def test_inside_the_certified_fall_region_the_remaining_time_after_entry_never_reaches_three_minutes():
    low, high = sc.REGIONS["burden_clear_tau"][:2]
    assert (low, high) == tuple(RECORD["certified_fall_region"]) == (6.38, 10.64)
    for key in KEYS:
        for tau in (low, (low + high) / 2, high):
            at_entry, minutes = _after_entry(key, clear_tau=tau)
            assert minutes <= 2 and at_entry < 0.61, (key, tau)


def test_no_fall_constant_gives_the_literal_requirement_under_the_certified_law():
    """El requisito literal: entrar en la region de recuperacion en un deterioro de ~0,80 y cruzar 0,50 en 3 a 5 minutos.
    Bajo la relajacion de primer orden hacia un objetivo GRADUADO son incompatibles: las constantes que dan 3 a 5 minutos
    tras la entrada hacen entrar al paciente en 0,60 a 0,68 (ya no en 0,80) y estan FUERA de la region certificada; las que lo
    harian entrar cerca de 0,80 tardan decenas de minutos despues."""
    grid = [6.38 + 0.5 * step for step in range(0, 228)]                  # 6,38 a 120 min
    upper = sc.REGIONS["burden_clear_tau"][1]
    for key in KEYS:
        fits = []
        for tau in grid:
            at_entry, minutes = _after_entry(key, clear_tau=tau)
            assert not (at_entry >= 0.75 and minutes is not None and 3 <= minutes <= 5), (key, tau)
            if minutes is not None and 3 <= minutes <= 5:
                fits.append((tau, at_entry))
        assert fits and min(tau for tau, _ in fits) > upper, key          # todas fuera de la region certificada
        assert all(0.57 <= at_entry <= 0.69 for _, at_entry in fits), key  # y entrando OBNUBILADO, nunca en ~0,80
        assert all(tau * math.log(1.6) > 5.0 for tau, _ in fits), key      # con la ley aislada ya fuera del 3-5 acordado
        slow_entry, slow_minutes = _after_entry(key, clear_tau=120.0)
        assert slow_entry < 0.80 and (slow_minutes is None or slow_minutes > 20), key


def test_the_what_if_of_a_clearance_held_until_entry_meets_the_clock_and_removes_the_partial_recovery():
    """Solo un cambio de LEY (F retenida mientras el objetivo es positivo) hace entrar al paciente en ~0,81 y tardar 4 a 6
    minutos. Es un analisis: no se instalo. Su precio medido: con cristaloide solo, la mejoria transitoria de la consciencia
    desaparece en CENTER_REFERENCE y HIGH (la entrega mejora pero no vuelve a su region normal)."""
    for key in KEYS:
        at_entry, minutes = _after_entry(key, law="gated")
        assert 0.80 <= at_entry <= 0.82 and minutes in (4, 5, 6), key
    for case in CASES:
        run = RECORD["matrix_what_if"][f"{case}/severe_deterioration"]
        for name in ("CENTER_REFERENCE", "HIGH"):
            certified = [level for _, level in run[name]["certified"]]
            gated = [level for _, level in run[name]["gated"]]
            assert certified[:5] == [0, 1, 2, 1, 2] and gated == [0, 1, 2, 3], (case, name)


def test_neither_candidate_would_move_the_deterioration():
    """P3-185: la bajada solo actua cuando el objetivo esta por debajo de F. Antes de cualquier tratamiento, F es identica
    bajo la ley certificada, bajo una bajada mas lenta y bajo la retenida, en las 42 corridas de la matriz."""
    assert len(RECORD["matrix_what_if"]) == 14
    for key, run in RECORD["matrix_what_if"].items():
        for name in WITNESSES:
            assert run[name]["rise_identical_slow"] is True and run[name]["rise_identical_gated"] is True, (key, name)
            recorded = [list(step) for step in SERIES["runs"][key]["witnesses"][name]["category_sequence"]]
            assert run[name]["certified"] == recorded, (key, name)
    for case in CASES:
        untreated = RECORD["matrix_what_if"][f"{case}/untreated"]
        for name in WITNESSES:
            assert untreated[name]["certified"] == untreated[name]["slower_fall_16"] == untreated[name]["gated"]


# -- P3-184: el orden de una recuperacion completa -----------------------------------------------------------------------------------

def test_every_recorded_recovery_keeps_the_required_order():
    for key in KEYS:
        checks = RECORD["order_checks"][key]
        assert all(checks[name] is True for name in (
            "upstream_first", "f_falls_only_after_its_target_is_below_it",
            "f_does_not_fall_at_the_minute_the_treatment_takes_effect", "category_gives_back_one_band_at_a_time",
            "f_is_only_the_relaxation_toward_the_delivery_target")), (key, checks)
        # la normalizacion no es instantanea: de la orden a la categoria de llegada pasan 13 a 18 minutos
        e = RECORD["events"][key]
        assert 13 <= e["T_CATEGORY_NORMAL"] - e["T_ORDER"] <= 18, key


def test_a_live_recovery_reproduces_the_recorded_timeline():
    run = series.run_scenario("gi_bleed_72f", "recovery_after_severe", trigger_witness="HIGH")
    rows, profile = run["witness_rows"]["HIGH"], run["profile"]["HIGH"]
    order = series.treatment_minute(run)
    events = series.recovery_events(rows, profile, order)
    recorded = RECORD["events"]["gi_bleed_72f/HIGH"]
    for name, value in recorded.items():
        got = events[name]
        assert (round(got, 4) if isinstance(got, float) else got) == value, name
    checks = series.recovery_order_checks(rows, profile, order)
    assert all(value is True for name, value in checks.items() if name != "first_f_fall")
    assert run["failures"] == [] and run["legacy_arrested"] is False


def test_the_two_cases_differ_only_slightly_and_only_while_treated():
    """Los dos casos leen igual sin tratar; tratados, la transfusion mueve la entrega relativa de cada uno segun su propia
    llegada: una diferencia de un minuto en UNA entrada (LOW: 184 frente a 183) y ninguna en las categorias."""
    differing = []
    for name in WITNESSES:
        a, b = RECORD["events"][f"gi_bleed_57m/{name}"], RECORD["events"][f"gi_bleed_72f/{name}"]
        differing += [(name, event, a[event], b[event]) for event in EVENTS if a[event] != b[event]]
    assert differing == [("LOW", "T_RECOVERY_REGION_ENTRY", 184, 183)]


# -- P3-185: nada cambio ---------------------------------------------------------------------------------------------------------------

def test_nothing_executable_changed_the_witnesses_are_the_certified_ones_inside_the_certified_region():
    assert a2.amended_core_digest_now() == rs.CORE_LINEAGE[-1].digest == \
        "a0af7d08fec3aaf93606b5635cad9f26980428a5ab8d8f66afb1317bb4586ce2"
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    for name, adapter in fam.ADAPTERS["gi_bleed"].region_witnesses().items():
        profile = adapter.profile(fam.COMMITTED).amendment_2
        assert profile == sc.WITNESSES[name]
        for field in sc.FIELDS:
            low, high = sc.REGIONS[field][:2]
            assert low <= getattr(profile, field) <= high or abs(getattr(profile, field) - low) < 0.02 \
                or abs(getattr(profile, field) - high) < 0.02, (name, field)
    assert RECORD["verdict"] == "GI_REGION_NEEDS_ONE_MORE_FACULTY_DECISION"
