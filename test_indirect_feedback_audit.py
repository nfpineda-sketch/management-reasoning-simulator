"""Ciclo de la segunda familia en vivo (2026-11-10): P3-137A y P3-138.

P3-137A -- las tres sondas de P2S-3 cuya condicion "solo se mueve la mecanica" choca con el enlace certificado
ventilacion -> PaCO2 -> oxigenacion quedan SUSTITUIDAS, no borradas: aqui estan los invariantes causales que
conservan su intencion legitima, y la prueba de que la evidencia historica se sigue reproduciendo.

P3-138 -- la auditoria completa del lazo indirecto de TD-130 (40):

    oxigenacion -> entrega -> deficit -> carga acida -> impulso -> FR -> W -> PaCO2 -> oxigenacion

con cada umbral, saturacion, retraso, acumulador y arista deshabilitada, su condicion de activacion, su signo,
y el barrido de la region de desarrollo. Nada se ajusta: se lee el nucleo certificado tal como esta.

Las etiquetas P3-137..P3-146 de ESTE ciclo son las del encargo; el ciclo anterior uso P3-137..P3-144 como
etiquetas propias en ``test_management_generalization.py``. Por eso las pruebas de aqui llevan ``p3l``.

Registro: second_live_family_record.
"""
import dataclasses

import pytest

import runtime_shadow_families as fam
import second_live_family_record as rec
from clinical_core import asthma_migration as am
from clinical_core import asthma_reference as sr
from clinical_core import derived as dv
from clinical_core import integration
from clinical_core import respiratory_mechanics
from clinical_core import opioid_migration as om
from clinical_core.state import CoreInvariantError

FIELD = fam.TRANSMISSION_FIELD
R = fam.TRANSMISSION_DECLARED_R
WITNESSES = dict(fam.TRANSMISSION_WITNESSES)
UPPER = fam.TRANSMISSION_MATHEMATICAL_REGION[1]
#: El barrido de P3-138C: el control negativo, los tres testigos y el borde superior de la region.
SWEEP = {"ZERO": 0.0, **WITNESSES, "UPPER": UPPER}
CASES = {"opioid_35m": (om, fam.OpioidAdapter), "opioid_67f": (om, fam.OpioidAdapter),
         "asthma_49m": (am, fam.AsthmaAdapter), "asthma_24f": (am, fam.AsthmaAdapter)}
HORIZONS = (60, 120, 240)
LONG = 600
LOOP_STATE = ("acid", "D", "T")
VENTILATION = ("rr", "w", "paco2")


# -- arnes -------------------------------------------------------------------------------------------------------

def _profile(case, fraction, **changes):
    migration, _ = CASES[case]
    return dataclasses.replace(migration.profile(), respiratory_quotient=R, **{FIELD: fraction, **changes})


def _run(case, fraction, minutes, **changes):
    _, adapter_cls = CASES[case]
    adapter = adapter_cls()
    anchors = adapter.anchors(case, fam.COMMITTED, None)
    profile = _profile(case, fraction, **changes)
    trajectory = integration.run(anchors, tuple(adapter.writers(case, fam.COMMITTED, None)), minutes, profile)
    return trajectory, anchors, profile


def _rows(case, fraction, minutes, **changes):
    """Por minuto: la lectura de cada nodo del lazo, calculada con las funciones del propio nucleo."""
    trajectory, anchors, profile = _run(case, fraction, minutes, **changes)
    rows = []
    for state in trajectory.states[1:]:
        derived = dv.derive(state, anchors, profile)
        breathing = dv.respiration(state, anchors, profile)
        delivery = dv.effective_delivery(derived.delivery_rel, anchors)
        rows.append({"minute": state.minute, "spo2": derived.spo2, "rr": breathing.respiratory_rate,
                     "w": breathing.ventilation, "paco2": breathing.paco2, "delivery": delivery,
                     "critical": state.aux.oxygen_demand / profile.oxygen_extraction_reserve,
                     "deficit": dv.effective_oxygen_deficit(state.aux.oxygen_demand, delivery,
                                                           profile.oxygen_extraction_reserve),
                     "acid": state.aux.metabolic_acid_burden, "D": state.D, "T": state.T,
                     "sympathetic": state.aux.sympathetic_drive, "efficiency": state.aux.mechanics_efficiency})
    return rows


def _gate(rows):
    """El primer minuto con deficit efectivo: donde el lazo puede cerrarse. None si nunca."""
    return next((row["minute"] for row in rows if row["deficit"] > 0.0), None)


def _turns(values):
    """Cuantas veces cambia de signo la primera diferencia: 0 es monotono, sin alternancia ni oscilacion."""
    steps = [b - a for a, b in zip(values, values[1:]) if abs(b - a) > 1e-12]
    return sum(1 for a, b in zip(steps, steps[1:]) if (a > 0) != (b > 0))


def _toggles(rows):
    """Cuantas veces el deficit pasa de 0 a positivo o al reves: mas de una es parpadeo de umbral."""
    on = [row["deficit"] > 0.0 for row in rows]
    return sum(1 for a, b in zip(on, on[1:]) if a != b)


@pytest.fixture(scope="module")
def sweep():
    return {case: {name: _rows(case, fraction, max(HORIZONS)) for name, fraction in SWEEP.items()}
            for case in CASES}


# -- P3-138: el grafo ejecutable, arista por arista ----------------------------------------------------------------

EDGE_CLASSES = {"ALWAYS_ACTIVE", "THRESHOLDED", "SATURATING", "DELAYED", "DISABLED", "CASE_DEPENDENT"}


def test_p3l_138a_every_edge_of_the_recorded_graph_has_a_class_and_a_source():
    graph = rec.FEEDBACK_GRAPH
    assert [edge["id"] for edge in graph["edges"]] == sorted(edge["id"] for edge in graph["edges"])
    for edge in graph["edges"]:
        assert set(edge["classes"]) <= EDGE_CLASSES and edge["classes"], edge["id"]
        assert edge["source"] and edge["sign"] in ("+", "-", "0"), edge["id"]
    # el lazo respiratorio se recorre entero, de la oxigenacion a la oxigenacion
    loop = [edge for edge in graph["edges"] if edge["id"] in graph["respiratory_loop"]]
    assert [edge["from"] for edge in loop][0] == "SpO2" and loop[-1]["to"] == "SpO2"
    for before, after in zip(loop, loop[1:]):
        assert before["to"] == after["from"], (before["id"], after["id"])
    # signo analitico: el producto de los signos de sus aristas
    product = 1
    for edge in loop:
        product *= {"+": 1, "-": -1}[edge["sign"]]
    assert product == -1 and graph["respiratory_loop_sign"] == "NEGATIVE_FEEDBACK"


def test_p3l_138b_the_link_edge_is_instantaneous_signed_and_off_at_zero(sweep):
    """PaCO2 -> SpO2: nada a fraccion 0, y mas PaCO2 nunca sube la SpO2."""
    for case, runs in sweep.items():
        assert len({row["spo2"] for row in runs["ZERO"]}) == 1, case      # el control negativo: SpO2 plana
        for name in list(WITNESSES) + ["UPPER"]:
            for zero, row in zip(runs["ZERO"], runs[name]):
                assert row["paco2"] == zero["paco2"]                      # la transmision no toca el PaCO2
                assert row["spo2"] <= zero["spo2"] + 1e-12, (case, name, row["minute"])


def test_p3l_138c_delivery_reads_saturation_in_proportion_and_nothing_else_moved(sweep):
    """SpO2 -> entrega: lineal e instantanea. En la region el gasto no cambia, asi que la razon es exacta."""
    for case, runs in sweep.items():
        for name in WITNESSES:
            for zero, row in zip(runs["ZERO"], runs[name]):
                assert row["delivery"] == pytest.approx(zero["delivery"] * row["spo2"] / zero["spo2"], abs=1e-12)


def test_p3l_138d_the_deficit_edge_is_a_threshold_at_the_critical_delivery():
    """entrega -> deficit: max(0, demanda - reserva x entrega). Cero mientras la entrega supere la critica."""
    profile = _profile("opioid_35m", 0.0)
    critical = 1.0 / profile.oxygen_extraction_reserve
    assert critical == pytest.approx(rec.FEEDBACK_GRAPH["critical_delivery_index"]) == 0.4
    assert dv.effective_oxygen_deficit(1.0, critical, profile.oxygen_extraction_reserve) == 0.0
    assert dv.effective_oxygen_deficit(1.0, critical + 0.05, profile.oxygen_extraction_reserve) == 0.0
    below = dv.effective_oxygen_deficit(1.0, critical - 0.05, profile.oxygen_extraction_reserve)
    assert below == pytest.approx(0.125) and below > 0.0


def test_p3l_138e_the_direct_hypoxaemic_loop_is_refused_by_the_core_itself():
    """SpO2 -> impulso hipoxemico -> FR: DESHABILITADA. Declararla junto al enlace no es representable."""
    with pytest.raises(CoreInvariantError, match="HYPOXEMIC_FEEDBACK_LOOP_DEFERRED"):
        _profile("opioid_35m", WITNESSES["CENTER_REFERENCE"],
                 hypoxaemic_drive_mapping=((95.0, 0.0), (80.0, 1.0)), hypoxaemic_to_drive_gain=4.0)
    # y los otros lectores que podrian cerrar un lazo por otra via estan sin declarar en los dos perfiles
    for case in ("opioid_35m", "asthma_49m"):
        profile = _profile(case, WITNESSES["HIGH"])
        assert profile.hypoxaemic_drive_mapping is None and profile.distress_to_respiratory_drive_gain is None
        assert profile.collapse_output_threshold is None and profile.collapse_burden_limit is None


def test_p3l_138f_the_stress_branch_ends_in_a_reading_and_feeds_nothing_back(sweep):
    """SpO2 -> impulso simpatico -> FC: se mueve, y ahi termina. La FC no entra en el gasto ni en la entrega."""
    for case, runs in sweep.items():
        high, zero = runs["HIGH"], runs["ZERO"]
        assert any(a["sympathetic"] != b["sympathetic"] for a, b in zip(high, zero)), case
        for a, b in zip(high, zero):
            # si el impulso simpatico volviera al gasto, la entrega dejaria de ser proporcional a la SpO2
            assert a["delivery"] == pytest.approx(b["delivery"] * a["spo2"] / b["spo2"], abs=1e-12)
            assert a["T"] == b["T"] and a["D"] == b["D"] and a["acid"] == b["acid"]


# -- P3-138A: cuando puede cerrarse --------------------------------------------------------------------------------

@pytest.mark.parametrize("case", sorted(CASES))
def test_p3l_138g_inside_the_region_the_loop_cannot_close_within_four_hours(sweep, case):
    """La compuerta es el deficit efectivo. En la region, hasta 240 minutos, no se abre en ningun caso."""
    zero = sweep[case]["ZERO"]
    for name, rows in sweep[case].items():
        assert _gate(rows) is None, (case, name)
        assert all(row["delivery"] > row["critical"] for row in rows)
        # asi que todo lo que queda aguas abajo de la compuerta es, bit a bit, lo del control negativo
        for key in LOOP_STATE + VENTILATION:
            assert [row[key] for row in rows] == [row[key] for row in zero], (case, name, key)
    lowest = min(row["delivery"] for rows in sweep[case].values() for row in rows)
    assert lowest == pytest.approx(rec.MEASURED["feedback"]["minimum_delivery_index"][case], abs=1e-4)
    assert lowest > 0.4


def _first_fraction_that_opens(case, horizon):
    """La menor fraccion que abre la compuerta dentro del horizonte, por biseccion de una dimension."""
    if _gate(_rows(case, 1.0, horizon)) is None:
        return None
    low, high = UPPER, 1.0
    for _ in range(22):
        middle = (low + high) / 2.0
        if _gate(_rows(case, middle, horizon)) is None:
            low = middle
        else:
            high = middle
    return high


def measure_activation() -> dict:
    out = {}
    for case in CASES:
        out[case] = {str(horizon): _first_fraction_that_opens(case, horizon) for horizon in HORIZONS}
    return out


def test_p3l_138h_the_smallest_fraction_that_opens_the_gate_is_outside_the_region():
    found = measure_activation()
    for case, by_horizon in found.items():
        for horizon, fraction in by_horizon.items():
            recorded = rec.MEASURED["feedback"]["first_fraction_that_opens_the_gate"][case][horizon]
            if fraction is None:
                assert recorded is None, (case, horizon)
                continue
            assert fraction == pytest.approx(recorded, abs=2e-6), (case, horizon)
            assert fraction > UPPER, (case, horizon)
    # el margen mas estrecho: opioid_35m a 240 minutos, casi el doble del borde de la region
    tightest = min(value for by in found.values() for value in by.values() if value is not None)
    assert tightest == pytest.approx(found["opioid_35m"]["240"])
    assert 1.9 < tightest / UPPER < 2.1


def test_p3l_138i_at_the_upper_boundary_the_gate_opens_only_after_hours_and_then_stays_calm():
    """Dentro de la region la compuerta SI se abre, pero no antes del minuto 346 de un curso sin tratar."""
    recorded = rec.MEASURED["feedback"]["gate_minute_at_the_upper_boundary"]
    for case in CASES:
        rows = _rows(case, UPPER, LONG)
        gate = _gate(rows)
        assert gate == recorded[case], case
        if gate is None:
            continue
        assert gate > max(HORIZONS)
        assert _toggles(rows) == 1, "se abre una vez y no parpadea"
        for key in ("spo2", "rr", "paco2", "deficit", "acid", "T", "D"):
            assert _turns([row[key] for row in rows]) == 0, (case, key)
    assert recorded["opioid_35m"] == 346 and recorded["asthma_49m"] is None and recorded["asthma_24f"] is None


# -- P3-138B: signo y estabilidad cuando esta activo ---------------------------------------------------------------

FORCED = (("opioid_35m", 1.0), ("opioid_35m", 0.5))


@pytest.mark.parametrize("case,fraction", FORCED)
def test_p3l_138j_forced_active_the_loop_neither_oscillates_nor_chatters(case, fraction):
    """Sondas fijas FUERA de la region, donde la compuerta se abre pronto. Sin oscilacion ni parpadeo."""
    rows = _rows(case, fraction, 120)
    gate = _gate(rows)
    assert gate == rec.MEASURED["feedback"]["forced_active"][f"{case}@{fraction:g}"]["gate_minute"]
    assert _toggles(rows) == 1
    after = [row for row in rows if row["minute"] >= gate]
    for key in ("spo2", "rr", "paco2", "delivery", "deficit", "acid", "T", "D"):
        assert _turns([row[key] for row in after]) == 0, key
    # el retraso: la carga acida y el tono leen el deficit del INICIO del minuto, asi que llegan uno despues
    first = {key: next(row["minute"] for row in rows if row[key] != rows[0][key]) for key in ("acid", "T", "D")}
    assert first == {"acid": gate + 1, "T": gate + 1, "D": gate + 1}


def test_p3l_138k_the_ventilatory_branch_is_negative_feedback_and_the_tone_branch_a_bounded_positive_one():
    """Signo por corte contrafactual, y la ganancia de un paso en estados activos."""
    base = _rows("opioid_35m", 1.0, 120)
    no_acid = _rows("opioid_35m", 1.0, 120, deficit_to_acid_gain=0.0)
    no_tone = _rows("opioid_35m", 1.0, 120, deficit_to_tone_gain=0.0)
    # sin la rama ventilatoria la saturacion cae MAS: la rama la sostiene (realimentacion negativa)
    assert no_acid[-1]["spo2"] < base[-1]["spo2"] and no_acid[-1]["rr"] < base[-1]["rr"]
    # sin la rama de tono el deficit es MENOR: la rama lo amplifica (positiva), y poco
    assert no_tone[-1]["deficit"] < base[-1]["deficit"]
    assert (base[-1]["deficit"] - no_tone[-1]["deficit"]) / base[-1]["deficit"] < 0.05
    measured = measure_multipliers()
    for minute, row in measured.items():
        # la carga acida es un integrador con fuga: su multiplicador de un paso esta en (0, 1), asi que la
        # respuesta es monotona -- ni alterna (seria negativo) ni diverge (seria mayor que 1)
        assert 0.0 < row["acid_multiplier"] < 1.0, minute
        assert 0.0 < row["tone_branch_gain"] < 0.2, minute
        recorded = rec.MEASURED["feedback"]["one_step"][minute]
        assert row["acid_multiplier"] == pytest.approx(recorded["acid_multiplier"], abs=1e-3)
        assert row["tone_branch_gain"] == pytest.approx(recorded["tone_branch_gain"], abs=1e-3)
    assert rec.FEEDBACK_GRAPH["loop_sign_when_active"] == "MIXED"


def measure_multipliers() -> dict:
    """En estados activos: dA(k+1)/dA(k) de la rama ventilatoria y la ganancia de un paso de la de tono."""
    trajectory, anchors, profile = _run("opioid_35m", 1.0, 120)

    def deficit_of(state):
        derived = dv.derive(state, anchors, profile)
        return dv.effective_oxygen_deficit(state.aux.oxygen_demand,
                                           dv.effective_delivery(derived.delivery_rel, anchors),
                                           profile.oxygen_extraction_reserve)
    out, step = {}, 1e-4
    for minute in (55, 60, 90, 120):
        state = trajectory.states[minute]
        here = deficit_of(state)
        more_acid = state.evolve(aux=dataclasses.replace(
            state.aux, metabolic_acid_burden=state.aux.metabolic_acid_burden + step))
        slope = (deficit_of(more_acid) - here) / step
        more_tone = (deficit_of(state.evolve(T=state.T + step)) - here) / step
        out[str(minute)] = {
            "acid_multiplier": 1.0 - 1.0 / profile.acid_clearance_tau_min + profile.deficit_to_acid_gain * slope,
            "tone_branch_gain": more_tone * profile.deficit_to_tone_gain / state.aux.oxygen_demand}
    return out


# -- P3-138C: el barrido de la region ------------------------------------------------------------------------------

@pytest.mark.parametrize("case", sorted(CASES))
def test_p3l_138l_the_region_sweep_shows_no_oscillation_inversion_or_non_monotone_effect(sweep, case):
    runs = sweep[case]
    order = ["ZERO", "LOW", "CENTER_REFERENCE", "HIGH", "UPPER"]
    for name in order:
        rows = runs[name]
        # sin oscilacion ni paso alternante en ningun nodo del lazo
        for key in ("spo2", "rr", "paco2", "delivery"):
            assert _turns([row[key] for row in rows]) == 0, (case, name, key)
        assert _toggles(rows) == 0
        # sin amplificacion de la deuda: no hay deuda
        assert all(row["D"] == 0.0 for row in rows)
    for horizon in HORIZONS:
        at = [runs[name][horizon - 1]["spo2"] for name in order]
        # el efecto de aumentar la transmision es monotono: mas fraccion, nunca mas saturacion
        assert all(b <= a for a, b in zip(at, at[1:])), (case, horizon, at)
        assert at[0] - at[-1] == pytest.approx(
            rec.MEASURED["feedback"]["spo2_span_across_the_region"][case][str(horizon)], abs=1e-3)
    # sin inversion de signo: la SpO2 nunca queda por encima del control negativo
    assert all(row["spo2"] <= zero["spo2"] + 1e-12 for name in order for row, zero in zip(runs[name], runs["ZERO"]))


def test_p3l_138m_the_verdict_and_what_it_rests_on():
    verdict = rec.FEEDBACK_VERDICT
    assert verdict["verdict"] == "A_INDIRECT_FEEDBACK_SAFE_FOR_DEVELOPMENT_REGION"
    assert verdict["stops_opioid_live_activation"] is False
    assert verdict["additional_region_restriction"] is None
    assert verdict["closes"] == "TD-130 (40)"
    # lo que NO afirma
    assert "not clinical" in verdict["is_not"] and verdict["horizon_audited_min"] == max(HORIZONS)


def measure_feedback() -> dict:
    swept = {case: {name: _rows(case, fraction, max(HORIZONS)) for name, fraction in SWEEP.items()}
             for case in CASES}
    forced = {}
    for case, fraction in FORCED:
        rows = _rows(case, fraction, 120)
        forced[f"{case}@{fraction:g}"] = {"gate_minute": _gate(rows), "spo2_at_120": rows[-1]["spo2"],
                                          "deficit_at_120": rows[-1]["deficit"]}
    return {
        "minimum_delivery_index": {case: min(row["delivery"] for rows in runs.values() for row in rows)
                                   for case, runs in swept.items()},
        "spo2_span_across_the_region": {case: {str(h): runs["ZERO"][h - 1]["spo2"] - runs["UPPER"][h - 1]["spo2"]
                                               for h in HORIZONS} for case, runs in swept.items()},
        "first_fraction_that_opens_the_gate": measure_activation(),
        "gate_minute_at_the_upper_boundary": {case: _gate(_rows(case, UPPER, LONG)) for case in CASES},
        "forced_active": forced,
        "one_step": measure_multipliers(),
    }


# -- P3-137A: las tres sondas de P2S-3, sustituidas por invariantes causales ---------------------------------------

SUPERSEDED = ("untreated", "relief", "heart_rate")
READING_KEYS = ("rr", "spo2", "G", "L", "D", "lactate", "hr", "delivery_index", "consciousness_level", "map")


def _asthma_profile(fraction):
    """El perfil comprometido del asma (None) o ese perfil con el enlace declarado en ``fraction``."""
    if fraction is None:
        return am.profile()
    return am.profile(respiratory_quotient=R, **{FIELD: fraction})


def _asthma_course(case, rate, fraction, extra=()):
    anchors, profile = sr.anchors(case), _asthma_profile(fraction)
    states, _ = am.course((am.obstruction(rate),) + tuple(extra), anchors=anchors, prof=profile)
    return [am.reading(state, anchors, profile) for state in states], anchors, profile


def test_p3l_137a_the_record_names_exactly_the_three_probes_and_what_replaces_each():
    table = rec.ASTHMA_SUPERSESSION
    assert tuple(row["probe"] for row in table["probes"]) == SUPERSEDED
    for row in table["probes"]:
        for key in ("historical_purpose", "old_expectation", "why_the_certified_amendment_changes_it",
                    "new_causal_invariant", "historical_evidence_still_reproducible", "conditions_superseded"):
            assert row[key], (row["probe"], key)
    assert table["status"] == "SUPERSEDED_WHERE_THEY_CONFLICT_NOT_DELETED"
    assert table["historical_freeze_records_modified"] is False


def test_p3l_137b_the_historical_evidence_reproduces_on_the_committed_profile():
    """Sin el enlace (el perfil comprometido), las tres sondas dan lo que P2S-3 certifico. Nada se borro."""
    assert am.profile().respiratory_quotient is None
    assert am.untreated()["pass"] is True and am.relief()["pass"] is True and am.heart_rate()["pass"] is True
    untreated = am.untreated()
    for case in sr.CASES:
        for row in untreated[case].values():
            assert all(row["only_mechanics_moves"].values()) and row["states_identical_but_mechanics"]


@pytest.mark.parametrize("case", list(sr.CASES))
@pytest.mark.parametrize("witness", list(WITNESSES))
def test_p3l_137c_mechanics_reach_oxygenation_only_through_ventilation_and_paco2(case, witness):
    """Sustituye a ``untreated``: mecanica -> ventilacion -> PaCO2 -> oxigenacion, y por ningun otro camino."""
    fraction = WITNESSES[witness]
    rate = am.WORSENING_PER_MIN[-1]
    plain, anchors, profile = _asthma_course(case, 0.0, fraction)
    worse, _, _ = _asthma_course(case, rate, fraction)
    # la cadena, en su direccion, contra el mismo caso sin empeorar
    efficiency = [row["mechanics_efficiency"] for row in worse]
    assert all(b < a for a, b in zip(efficiency, efficiency[1:]))
    for a, b in zip(worse[1:], plain[1:]):
        assert a["W"] < b["W"] and a["paco2"] > b["paco2"] and a["ph"] < b["ph"]
        assert a["spo2"] < b["spo2"], "ahora la oxigenacion SIGUE a la ventilacion"
    # la parte de la condicion antigua que no choca con el enlace sigue en pie, igual que antes
    for key in ("rr", "G", "L", "D", "lactate", "consciousness_level", "map"):
        assert [row[key] for row in worse] == [row[key] for row in plain], key
    # SIN escritura directa mecanica -> SpO2: la SpO2 es EXACTAMENTE la de la ecuacion certificada sobre el
    # PaCO2, partiendo de la SpO2 que la mecanica deja intacta
    off, _, _ = _asthma_course(case, rate, 0.0)
    reference = dv.arrival_paco2_reference(anchors, profile)
    for with_link, without in zip(worse, off):
        expected = dv.oxygen_saturation_from_pao2(
            dv.pao2_from_oxygen_saturation(without["spo2"]) - fraction * (with_link["paco2"] - reference) / R)
        assert with_link["spo2"] == pytest.approx(expected, abs=1e-12)
    # y la entrega se mueve solo por esa SpO2
    for a, b in zip(worse, off):
        assert a["delivery_index"] == pytest.approx(b["delivery_index"] * a["spo2"] / b["spo2"], abs=1e-12)


@pytest.mark.parametrize("case", list(sr.CASES))
def test_p3l_137d_at_fraction_zero_the_old_condition_holds_in_full(case):
    """El control negativo: con el enlace declarado y fraccion 0, ``solo se mueve la mecanica`` es verdad entera."""
    rate = am.WORSENING_PER_MIN[-1]
    plain, _, _ = _asthma_course(case, 0.0, 0.0)
    worse, _, _ = _asthma_course(case, rate, 0.0)
    for key in READING_KEYS:
        assert [row[key] for row in worse] == [row[key] for row in plain], key
    # y es, lectura por lectura, el curso del perfil comprometido
    committed, _, _ = _asthma_course(case, rate, None)
    for key in READING_KEYS + ("W", "paco2", "ph", "mechanics_efficiency"):
        assert [row[key] for row in worse] == [row[key] for row in committed], key


@pytest.mark.parametrize("case", list(sr.CASES))
def test_p3l_137e_the_transmission_never_alters_the_mechanics(case):
    """La fraccion no escribe la mecanica ni la ventilacion: son identicas bit a bit en todo el barrido."""
    rate = am.WORSENING_PER_MIN[-1]
    reference, _, _ = _asthma_course(case, rate, 0.0)
    for name, fraction in SWEEP.items():
        course, _, _ = _asthma_course(case, rate, fraction)
        for key in ("mechanics_efficiency", "rr", "W", "paco2", "ph"):
            assert [row[key] for row in course] == [row[key] for row in reference], (name, key)


@pytest.mark.parametrize("witness", list(WITNESSES))
def test_p3l_137f_relief_never_lowers_saturation_and_grows_with_the_fraction(witness):
    """Sustituye a ``relief``: el alivio sube W, baja el PaCO2, deja la FR igual, y la SpO2 no baja nunca."""
    fraction = WITNESSES[witness]
    probe = respiratory_mechanics.SyntheticMechanics("p3l-relief", am.RELIEF["factor_per_min"],
                                                     am.RELIEF["from_minute"], am.RELIEF["to_minute"])
    relieved, _, _ = _asthma_course(sr.CASE, am.MID_WORSENING, fraction, extra=(probe,))
    plain, _, _ = _asthma_course(sr.CASE, am.MID_WORSENING, fraction)
    end = am.RELIEF["to_minute"]
    assert relieved[end]["W"] > plain[end]["W"] and relieved[end]["paco2"] < plain[end]["paco2"]
    assert [row["rr"] for row in relieved] == [row["rr"] for row in plain]
    # sin paradoja: aliviar la mecanica no baja la saturacion en ningun minuto
    assert all(a["spo2"] >= b["spo2"] - 1e-12 for a, b in zip(relieved, plain))
    assert relieved[end]["spo2"] > plain[end]["spo2"]
    # nada antes de que el alivio empiece
    start = am.RELIEF["from_minute"]
    assert all(a["spo2"] == b["spo2"] for a, b in zip(relieved[:start], plain[:start]))


def test_p3l_137g_the_relief_gain_is_ordered_by_the_fraction_and_null_at_zero():
    probe = respiratory_mechanics.SyntheticMechanics("p3l-relief", am.RELIEF["factor_per_min"],
                                                     am.RELIEF["from_minute"], am.RELIEF["to_minute"])
    end, gains = am.RELIEF["to_minute"], []
    for fraction in (0.0,) + tuple(WITNESSES.values()):
        plain, _, _ = _asthma_course(sr.CASE, am.MID_WORSENING, fraction)
        relieved, _, _ = _asthma_course(sr.CASE, am.MID_WORSENING, fraction, extra=(probe,))
        gains.append(relieved[end]["spo2"] - plain[end]["spo2"])
    assert gains[0] == 0.0, "a fraccion 0 el alivio no llega a la saturacion: no hay escritura directa"
    assert all(b > a for a, b in zip(gains, gains[1:])), gains


@pytest.mark.parametrize("witness", list(WITNESSES))
def test_p3l_137h_a_witness_profile_adds_the_link_and_no_gain(witness):
    """Sustituye a ``heart_rate.gains_untouched``: el testigo difiere del perfil comprometido en los DOS campos
    del enlace y en ninguna ganancia."""
    committed = am.profile()
    linked = _asthma_profile(WITNESSES[witness])
    changed = sorted(f.name for f in dataclasses.fields(committed)
                     if getattr(committed, f.name) != getattr(linked, f.name))
    assert changed == sorted(["respiratory_quotient", FIELD])
    # y la descomposicion de la FC de llegada, que es lo que la sonda mide, no cambia con el enlace
    for case in sr.CASES:
        assert dv.heart_rate_decomposition(sr.anchors(case), linked) == \
            dv.heart_rate_decomposition(sr.anchors(case), committed)


def test_p3l_137i_the_six_probes_that_never_conflicted_still_pass_with_the_link():
    real = am.profile
    am.profile = lambda **changes: real(**{"respiratory_quotient": R, FIELD: WITNESSES["HIGH"], **changes})
    try:
        for name in ("arrival", "writer_semantics", "oxygen", "direct_g", "collapse"):
            assert getattr(am, name)()["pass"] is True, name
        assert am.consciousness(am.untreated())["pass"] is True
    finally:
        am.profile = real


def test_p3l_138n_the_recorded_measurements_are_what_the_core_gives_now():
    def rounded(value, places=6):
        if isinstance(value, dict):
            return {key: rounded(item, places) for key, item in value.items()}
        return round(value, places) if isinstance(value, float) else value
    assert rounded(measure_feedback()) == rec.MEASURED["feedback"]
