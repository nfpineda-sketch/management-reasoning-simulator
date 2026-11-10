"""Ciclo de resolucion de la sombra en vivo (2026-11-10): P3-156 a P3-166.

- P3-156: de donde sale cada valor de la tasa de profundizacion del opioide, y que NO la acota;
- P3-157: la restriccion conjunta tasa x transmision, en forma cerrada y medida, sin region conjunta;
- P3-158: una orden retenida que el motor ejecuta despues se refleja UNA vez, en su minuto real;
- P3-159: la generacion explicita del encuentro, el estado ``hidden`` y lo que la integridad protege;
- P3-160: la auditoria de solo lectura de transicion terminal y consciencia, contra el codigo;
- P3-162: el paquete de revision docente, con el primer canal causal esperado y observado;
- P3-163 a P3-166: seleccion de casos, ataques, compuertas y hoja de ruta.

Los encuentros se juegan con ``pilot_acceptance.Encounter``: el camino de ordenes de la pagina sin Streamlit,
con el motor heredado como unica autoridad. No hay fisiologia nueva: el nucleo comun no cambia en este ciclo.

Registro: shadow_resolution_record. Etiquetas ``p3r``.
"""
import copy
import random
from pathlib import Path

import pytest

import pilot_acceptance as acceptance
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam
import runtime_shadow_observer as obs
import runtime_shadow_store as store
import shadow_observability_record as previous
import shadow_resolution_record as rec
import test_shadow_sensitivity as sensitivity
from clinical_core import derived as dv
from clinical_core import opioid_migration as om
from test_shadow_observability import (GI, NALOXONE, OPIOID, OXYGEN, POOL, SEEDS, Page, _latest, _play,  # noqa: F401
                                       _play_on_page, traces)

ROOT = Path(__file__).resolve().parent
T = rec.JOINT["minutes"]
HELD_NALOXONE = "Order a lactate, wait for the result, then give naloxone 0.4 mg IV."
HELD = {
    GI: {"blood": ("Order a lactate, wait for the result, then transfuse 2 units of packed red cells.", 5),
         "fluid": ("Order a CBC, wait for the result, then give 1 L of lactated Ringer's.", 10),
         "oxygen": ("Order a lactate, wait for the result, then give oxygen 15 L/min by non-rebreather mask.", 5)},
    OPIOID: {"naloxone": (HELD_NALOXONE, 5)},
}
NEVER_RELEASED = {GI: "Order a type and crossmatch, wait for the result, then transfuse 1 unit of packed red cells.",
                  OPIOID: "Order a type and crossmatch, wait for the result, then give naloxone 0.4 mg IV."}
UNSUPPORTED_HELD = "Order a lactate, wait for the result, then start bag-mask ventilation."


def _rows(trace, kind):
    return [row for row in trace["actions"] if row["kind"] == kind]


def _engine_stamp(encounter, agent):
    return [item["time_min"] for item in encounter.state["treatments"]["administered_medications"]
            if item["agent"] == agent]


# -- P3-156: la evidencia de la tasa --------------------------------------------------------------------------------

def test_p3r_156a_every_value_in_the_provenance_table_is_where_the_table_says():
    table = rec.DEEPENING_RATE["provenance"]
    assert all(row["status"] in rec.PROVENANCE_STATUSES and row["source"] and row["note"] for row in table)
    by_value = {row["value"]: row for row in table}
    assert om.DEEPENING_PER_MIN == 0.005 and by_value[0.005]["status"] == "SYNTHETIC_REFERENCE"
    assert om.RECURRENCE["deepening_per_min"] == 0.02 and om.SEVERE_DEEPENING_PER_MIN == 0.03
    source = (ROOT / "clinical_core" / "opioid_migration.py").read_text(encoding="utf-8")
    heading = source.index("SYNTHETIC_ONLY")
    assert heading < source.index("DEEPENING_PER_MIN = 0.005")
    assert '"deepening_per_min", 0.5)' in (ROOT / "test_clinical_core_opioid_migration.py").read_text(
        encoding="utf-8")
    # las sondas exploratorias NO son evidencia: ninguna acota la tasa
    for value in (0.02, 0.03, 0.5):
        assert by_value[value]["status"] == "EXPLORATORY_PROBE" and by_value[value]["constrains_the_rate"] is False
    constraining = [row for row in table if row["constrains_the_rate"]]
    assert [row["status"] for row in constraining] == ["CERTIFIED_BEHAVIORAL_CONSTRAINT"] * 2
    assert constraining[0]["value"].startswith("> 0") and constraining[1]["constrains_the_rate"] == \
        "JOINTLY_WITH_THE_FRACTION"
    assert not any(row["status"] == "FACULTY_DEFINED" and row["constrains_the_rate"] for row in table)


def test_p3r_156b_no_region_is_adopted_and_the_faculty_question_is_stated():
    rate = rec.DEEPENING_RATE
    assert rate["identifiability"] == "NOT_IDENTIFIABLE_WITH_EXISTING_EVIDENCE"
    assert rate["region"] is None and rate["region_confidence"] < rate["required_confidence"] == 0.80
    assert rate["parameter_adoption"] == "STOPPED" and rate["faculty_question"].count("?") == 1
    assert rate["falsifier"] and rate["uncertainty"]
    # y en el codigo: un punto comprometido, sin intervalo, y la region dice de que depende
    registered = fam.adapter_for("opioid")
    assert [writer.deepening_per_min for writer in registered.writers(OPIOID, fam.COMMITTED)] == [om.DEEPENING_PER_MIN]
    assert not [name for name in dir(fam) if "DEEPENING" in name and "REGION" in name]
    assert fam.TRANSMISSION_CLASSIFICATION == "CONDITIONAL_DEVELOPMENT_REGION" == rec.JOINT["classification"]
    condition = fam.transmission_condition()
    assert condition["value"] == om.DEEPENING_PER_MIN and condition["status"] == "SYNTHETIC_REFERENCE"
    assert "not robust" in condition["reading"]


def test_p3r_156c_the_condition_travels_with_every_record_of_the_region(traces):
    encounter = _play(OPIOID, (NALOXONE,), until=3)
    trace = _latest(encounter)
    assert trace["region"]["classification"] == "CONDITIONAL_DEVELOPMENT_REGION"
    assert trace["region"]["conditional_on"] == fam.transmission_condition()
    record = encounter.shadow.ensemble.record()
    assert record["classification"] == "CONDITIONAL_DEVELOPMENT_REGION" and record["selected_witness"] is None
    assert record["conditional_on"]["value"] == om.DEEPENING_PER_MIN
    for witness in fam.TRANSMISSION_WITNESSES:
        provenance = " ".join(trace["runs"][witness]["snapshot"]["provenance"])
        assert "valid only at the committed synthetic deepening rate" in provenance


# -- P3-157: la restriccion conjunta --------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def committed_bound():
    return sensitivity._bound()


def _closed_f_max(rate, constant):
    return constant / ((1 - rate) ** -T - 1)


def test_p3r_157a_the_fixture_depends_on_one_combination_of_the_two_parameters(committed_bound):
    growth = (1 - om.DEEPENING_PER_MIN) ** -T - 1
    constant = committed_bound["f_upper"] * growth
    assert constant == pytest.approx(rec.JOINT["C"], abs=1e-7)
    assert committed_bound["delta_paco2_60"] / growth == pytest.approx(rec.JOINT["P0"], abs=1e-9)
    assert committed_bound["f_upper"] == pytest.approx(fam.TRANSMISSION_MATHEMATICAL_REGION[1], abs=1e-6)
    # sondas fijas, dentro y fuera de las del repositorio: la forma cerrada da la cota medida
    for rate in (0.0025, 0.01, 0.02, 0.03):
        found = sensitivity._bound(deepening=rate)
        assert found["spo2_60_at_f0"] == committed_bound["spo2_60_at_f0"]         # el numerador no depende de d
        assert found["delta_paco2_60"] == pytest.approx(rec.JOINT["P0"] * ((1 - rate) ** -T - 1), rel=1e-9)
        assert found["f_upper"] == pytest.approx(_closed_f_max(rate, constant), rel=1e-9)
    # no es el producto f x d: el producto en la cota se mueve mas de la mitad entre las tasas probadas
    products = rec.JOINT["product_f_times_d_at_the_bound"]
    for rate, product in products.items():
        assert _closed_f_max(rate, constant) * rate == pytest.approx(product, abs=5e-8)
    assert min(products.values()) / max(products.values()) < 0.5


def test_p3r_157b_the_largest_rate_each_witness_tolerates(committed_bound):
    constant = committed_bound["f_upper"] * ((1 - om.DEEPENING_PER_MIN) ** -T - 1)
    rows = {row["name"]: row for row in rec.JOINT["transmission_witnesses"]}
    assert {name: row["f"] for name, row in rows.items()} == dict(fam.TRANSMISSION_WITNESSES)
    for name, fraction in fam.TRANSMISSION_WITNESSES.items():
        low, high = om.DEEPENING_PER_MIN / 10, 0.03               # biseccion 1-D sobre la tasa, medida
        for _ in range(18):
            middle = (low + high) / 2
            if sensitivity._bound(deepening=middle)["f_upper"] >= fraction:
                low = middle
            else:
                high = middle
        closed = 1 - (1 + constant / fraction) ** (-1 / T)
        assert low == pytest.approx(closed, abs=2e-7) and closed == pytest.approx(rows[name]["d_max"], abs=1e-6)
        assert closed > om.DEEPENING_PER_MIN                      # los tres testigos caben en la tasa comprometida
        assert closed / om.DEEPENING_PER_MIN == pytest.approx(rows[name]["margin_over_committed_rate"], rel=5e-3)
    assert rows["HIGH"]["margin_over_committed_rate"] < 1.01 < rows["CENTER_REFERENCE"]["margin_over_committed_rate"]
    # las tasas exploratorias dejan fuera testigos: por eso la region es de UNA tasa
    for probe in rec.JOINT["exploratory_rates_not_witnesses"]:
        assert probe["status"] == "EXPLORATORY_PROBE"
        assert _closed_f_max(probe["rate"], constant) == pytest.approx(probe["f_max"], abs=1e-6)
        assert probe["f_max"] < fam.TRANSMISSION_WITNESSES["LOW"]


def test_p3r_157c_the_verdict_and_no_joint_region():
    joint = rec.JOINT
    assert joint["verdict"] == "CURRENT_REGION_VALID_ONLY_AT_COMMITTED_RATE" and joint["joint_region"] is None
    assert [row["rate"] for row in joint["rate_witnesses"]] == [om.DEEPENING_PER_MIN]
    assert all(row["justified"] and row["status"] == "SYNTHETIC_REFERENCE" for row in joint["rate_witnesses"])
    assert joint["rate_witnesses"][0]["f_max"] == fam.TRANSMISSION_MATHEMATICAL_REGION[1]
    assert joint["method"] == ("analytic bound", "fixed probes", "one-dimensional bisection on d per witness")
    assert "BOTH" in joint["why_no_joint_region"] and rec.DEEPENING_RATE["region"] is None
    assert dict(fam.TRANSMISSION_WITNESSES) == {"LOW": 0.015, "CENTER_REFERENCE": 0.03, "HIGH": 0.06}


# -- P3-158: ordenes retenidas ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("case,kind", [(GI, "blood"), (GI, "fluid"), (GI, "oxygen"), (OPIOID, "naloxone")])
def test_p3r_158a_a_held_order_is_mirrored_once_at_the_minute_the_engine_ran_it(case, kind, traces):
    text, executed = HELD[case][kind]
    waiting = _play(case, (text,))
    held = waiting.shadow.held
    assert [(item["kind"], item["state"], item["placed_minute"]) for item in held] == [(kind, rs.ORDER_HELD, 0)]
    assert [name for name, _minute in held[0]["events"]] == [rs.ORDER_PLACED, rs.ORDER_HELD]
    assert not [item for item in waiting.shadow.mirrored if item.kind == kind]          # nada antes de ejecutarse
    row = _rows(_latest(waiting), kind)
    assert [(r["disposition"], r["order_minute"], r["effective_minute"]) for r in row] == [
        (fam.HELD_NOT_EXECUTED, None, None)]
    assert _latest(waiting)["status"]["state"] == fam.COMPLETE

    encounter = _play(case, (text,), until=40)
    session, trace = encounter.shadow, _latest(encounter)
    entry = session.held[0]
    assert entry["state"] == rs.ORDER_EXECUTED and entry["executed_minute"] == executed != entry["placed_minute"]
    assert entry["events"] == [[rs.ORDER_PLACED, 0], [rs.ORDER_HELD, 0], [rs.ORDER_RELEASED, executed],
                               [rs.ORDER_EXECUTED, executed]]
    mirrored = [item for item in session.mirrored if item.kind == kind]
    assert [(item.minute, item.order_id) for item in mirrored] == [(executed, entry["shadow_order_id"])]
    # la regla de tiempo de la capa: ejecutada en e, presente por primera vez en el estado de e + 1
    row = _rows(trace, kind)
    assert [(r["disposition"], r["order_minute"], r["effective_minute"], r["placed_minute"]) for r in row] == [
        (fam.BUILT, executed, executed + 1, 0)]
    assert "placed at minute 0" in row[0]["why"] and f"minute {executed}" in row[0]["why"]
    assert trace["held_orders"][0]["state"] == rs.ORDER_EXECUTED and session.gaps == []
    assert trace["status"]["state"] == fam.COMPLETE
    assert store.verify(trace)["verified"] and store.replay(trace)["reproduces"]
    # y el efecto empieza despues de la ejecucion, nunca en la colocacion: antes de e + 1 la corrida es la sin tratar
    untreated = _play(case, ("Order a lactate." if "lactate" in text else "Order a CBC.",), until=40)
    mine, theirs = session.runner.digests(), untreated.shadow.runner.digests()
    assert mine[:executed] == theirs[:executed] and mine[executed:] != theirs[executed:]


def test_p3r_158b_the_minute_is_the_engines_own_however_the_wait_is_chunked():
    chooser, reference = random.Random(7), None
    chunkings = [(18,), (5, 18), (4, 18), (6, 18), (2, 3, 4, 5, 6, 18), (5, 5, 18), tuple(range(2, 19))]
    chunkings += [tuple(sorted(chooser.sample(range(2, 18), chooser.randint(1, 5))) + [18]) for _ in range(13)]
    assert len(chunkings) == rec.HELD_ORDERS["measured"]["chunkings_of_the_wait"]
    for chunks in chunkings:
        with ev.shadow(rs.MODE_SHADOW_COMPARE):
            encounter = acceptance.Encounter(OPIOID)
            encounter.order(HELD_NALOXONE)
            for minute in chunks:
                encounter.wait_until(minute)
        stamp = _engine_stamp(encounter, "naloxone")
        mirrored = [item.minute for item in encounter.shadow.mirrored if item.kind == "naloxone"]
        assert stamp == mirrored == [rec.HELD_ORDERS["measured"]["executed"]], chunks
        digests = encounter.shadow.runner.digests()[:18]
        reference = reference or digests
        assert digests == reference and encounter.shadow.gaps == [], chunks


def test_p3r_158c_a_release_observed_twice_is_mirrored_once(monkeypatch):
    seen = []
    original = rs.ShadowSession.observe

    def recording(self, *args, **kwargs):
        seen.append((copy.deepcopy(args), copy.deepcopy(kwargs)))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(rs.ShadowSession, "observe", recording)
    encounter = _play(OPIOID, (HELD_NALOXONE,), until=12)
    session = encounter.shadow
    before = (len(session.mirrored), session.runner.digests(), session.ensemble.digests(),
              copy.deepcopy(session.held))
    assert [item.kind for item in session.mirrored].count("naloxone") == 1
    gaps = copy.deepcopy(session.gaps)
    for args, kwargs in seen:                                    # todos los turnos, otra vez, con sus recibos
        original(session, *copy.deepcopy(args), **copy.deepcopy(kwargs))
    assert session.gaps == gaps                  # R-F3 de la revision: volver a mirar no inventa una brecha
    assert [item.kind for item in session.mirrored].count("naloxone") == 1
    assert (session.runner.digests(), session.ensemble.digests()) == before[1:3]
    assert [item["state"] for item in session.held] == [rs.ORDER_EXECUTED]
    assert session.held[0]["events"] == before[3][0]["events"]
    # un segundo recibo de liberacion sin orden retenida que lo respalde: no se refleja, y se dice
    count = len(session.mirrored)
    session._release([{"type": "naloxone", "released_after": "lactate", "held_from_min": 0}],
                     encounter.state, encounter.state, 0.21)
    assert len(session.mirrored) == count
    assert session.gaps[-1]["why"] == "the engine ran a held order this session was not holding"


@pytest.mark.parametrize("case", (GI, OPIOID))
def test_p3r_158d_an_order_the_engine_never_releases_is_never_mirrored(case, traces):
    encounter = _play(case, (NEVER_RELEASED[case],), until=30)
    session, trace = encounter.shadow, _latest(encounter)
    kind = session.held[0]["kind"]
    assert not [item for item in session.mirrored if item.kind == kind]
    assert encounter.state["family_state"]["deferred_orders"]                 # el motor la sigue reteniendo
    expected = rs.ORDER_TERMINAL_NOT_EXECUTABLE if encounter.arrested else rs.ORDER_HELD
    assert session.held[0]["state"] == expected and session.held[0]["executed_minute"] is None
    assert encounter.arrested is (case == OPIOID)
    row = _rows(trace, kind)
    assert [(r["disposition"], r["effective_minute"]) for r in row] == [(fam.HELD_NOT_EXECUTED, None)]
    assert ("can no longer" in row[0]["why"]) is (case == OPIOID)
    assert trace["held_orders"][0]["state"] == expected
    assert store.verify(trace)["verified"] and store.replay(trace)["reproduces"]


def test_p3r_158e_an_order_the_engine_runs_during_an_information_activity_is_declared_not_called_cancelled(traces):
    """R-F1 de la revision independiente. El motor tambien libera ordenes retenidas mientras pasa el tiempo de
    una pregunta o de un examen, y ese camino no tiene turno de sombra: la orden deja la lista sin recibo.
    El motor no tiene cancelacion, asi que esa orden CORRIO. No se refleja (no hay recibo) y se dice."""
    import family_engine
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(OPIOID)
        encounter.order(HELD_NALOXONE)
        family_engine.advance_clinical_time(encounter.state, 6)           # lo que hace la pagina al preguntar
        assert _engine_stamp(encounter, "naloxone") == [5]                     # el motor la ejecuto
        encounter.order("Reassess in 2 minutes.")
    session, trace = encounter.shadow, _latest(encounter)
    assert session.held[0]["state"] == rs.ORDER_RELEASED and session.held[0]["why"] == rs.UNOBSERVED_RELEASE
    assert rs.ORDER_CANCELLED not in [name for name, _minute in session.held[0]["events"]]
    assert not [item for item in session.mirrored if item.kind == "naloxone"]
    row = _rows(trace, "naloxone")
    assert [(r["disposition"], r["effective_minute"]) for r in row] == [(fam.NOT_MIRRORED, None)]
    assert "information activity" in row[0]["why"]
    # nunca COMPLETE: a la corrida de sombra le falta un tratamiento que el paciente si recibio
    assert trace["status"]["state"] == fam.COMPLETE_WITH_UNSUPPORTED_ACTIONS
    assert any("information activity" in item["detail"] for item in trace["status"]["items"])
    assert store.verify(trace)["verified"]
    assert "no cancellation" in rec.HELD_ORDERS["engine_facts"][0] and "NOT_MIRRORED" in rec.HELD_ORDERS[
        "unobserved_release"]
    engine = (ROOT / "family_engine.py").read_text(encoding="utf-8")
    assert engine.count('["deferred_orders"] = still_waiting') == 1            # la unica salida de la lista


def test_p3r_158j_malformed_held_entries_in_the_engine_state_do_not_stop_the_shadow():
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(OPIOID)
        encounter.order(NEVER_RELEASED[OPIOID])
        real = copy.deepcopy(encounter.state["family_state"]["deferred_orders"])
        session = encounter.shadow
        for junk in ("x", None, {"action": "text"}, {"action": {}, "requested_at_min": "soon"}):
            state = copy.deepcopy(encounter.state)
            state["family_state"]["deferred_orders"] = [junk] + real
            session._settle_held(state)                                       # nunca levanta
            assert session.held[0]["state"] == rs.ORDER_HELD
        encounter.wait_until(3)
    assert session.runner.minutes_done == 3 and session.failures == []


def test_p3r_158k_a_resealed_trace_cannot_relabel_a_held_order(traces):
    """R-F2 de la revision: la coherencia interna ata cada orden retenida a su fila."""
    ran = _latest(_play(OPIOID, (HELD_NALOXONE,), until=12))
    waits = _latest(_play(OPIOID, (NEVER_RELEASED[OPIOID],), until=3))

    def resealed(trace, edit):
        body = copy.deepcopy(trace)
        edit(body)
        body["trace_digest"] = store.trace_digest(body)
        return store.verify(body)

    assert store.verify(ran)["verified"] and store.verify(waits)["verified"]
    edits = {
        "executed relabelled as not run": (ran, lambda b: b["held_orders"][0].update(state=rs.ORDER_HELD,
                                                                                    executed_minute=None)),
        "execution minute moved": (ran, lambda b: b["held_orders"][0].update(executed_minute=0)),
        "held entry removed, mirrored row kept": (ran, lambda b: b["held_orders"].clear()),
        "waiting entry removed, row kept": (waits, lambda b: b["held_orders"].clear()),
        "waiting row removed, entry kept": (waits, lambda b: b["actions"].pop(next(
            i for i, row in enumerate(b["actions"]) if row["disposition"] == fam.HELD_NOT_EXECUTED))),
        "waiting relabelled as run": (waits, lambda b: b["held_orders"][0].update(state=rs.ORDER_EXECUTED,
                                                                                 executed_minute=2)),
    }
    for name, (trace, edit) in edits.items():
        checked = resealed(trace, edit)
        assert not checked["verified"] and checked["inconsistencies"], name
    # lo que queda fuera, declarado: quitar la orden retenida Y su fila no deja nada que contradecir
    both = resealed(waits, lambda b: (b["held_orders"].clear(), b["actions"].pop(next(
        i for i, row in enumerate(b["actions"]) if row["disposition"] == fam.HELD_NOT_EXECUTED))))
    assert both["verified"] and "self-consistent" in rec.SESSION_RESIDUALS["trace_integrity"]["does_not_protect"][0]


def test_p3r_158f_an_executed_held_order_the_core_cannot_represent_is_declared_not_faked(traces):
    encounter = _play(OPIOID, (UNSUPPORTED_HELD,), until=12)
    session, trace = encounter.shadow, _latest(encounter)
    assert session.held[0]["state"] == rs.ORDER_EXECUTED and session.held[0]["executed_minute"] == 5
    row = _rows(trace, "bag_mask")
    assert [(r["disposition"], r["order_minute"], r["effective_minute"]) for r in row] == [
        (fam.DECLARED_GAP, 5, None)]
    assert fam.UNSUPPORTED_ACTION in trace["status"]["codes"]
    assert trace["status"]["state"] == fam.COMPLETE_WITH_UNSUPPORTED_ACTIONS
    # ningun efecto fingido: la corrida es la del paciente sin tratar
    untreated = _play(OPIOID, ("Order a lactate.",), until=12)
    assert session.runner.digests() == untreated.shadow.runner.digests()


def test_p3r_158g_a_release_whose_minute_cannot_be_established_is_not_mirrored():
    entry = {"after_result": "lactate", "placed_turn": 1}
    state = {"sim_time": 9, "diagnostics": {}, "family_state": {}}
    assert rs.held_execution_minute(entry, state, state, 2) is None             # el estudio nunca volvio
    assert rs.held_execution_minute({}, state, state, 2) is None                # entrada ilegible: nunca levanta
    back = {"sim_time": 9, "diagnostics": {"lactate": {"time_min": 5}}, "family_state": {}}
    before = {"sim_time": 2, "diagnostics": {},
              "family_state": {"pending_diagnostics": [{"due_min": 5, "summary": {"diagnostic_type": "lactate"}}]}}
    assert rs.held_execution_minute(entry, before, back, 2) == 5                # dentro del turno, en su minuto
    assert rs.held_execution_minute(dict(entry, placed_turn=2), before, back, 2) == 9   # colocada en ESTE turno
    assert rs.held_execution_minute(dict(entry, after_result=rs.ANY_PENDING), before, back, 2) == 5
    encounter = _play(OPIOID, (HELD_NALOXONE,))
    session = encounter.shadow
    session._release([{"type": "naloxone", "released_after": "lactate", "held_from_min": 0}],
                     encounter.state, encounter.state, 0.21)
    assert session.held[0]["state"] == rs.ORDER_RELEASED and session.held[0]["executed_minute"] is None
    assert not [item for item in session.mirrored if item.kind == "naloxone"]
    rows = fam.held_rows(session.held, [])
    assert [row["disposition"] for row in rows] == [fam.NOT_MIRRORED] and "cannot be established" in rows[0]["why"]


def test_p3r_158i_the_same_study_pending_more_than_once_releases_at_its_first_arrival():
    """Hallado por las secuencias aleatorias de este ciclo: el motor conserva solo la hora del ULTIMO resultado
    de un estudio pedido varias veces, y las ordenes retenidas corren con el PRIMERO."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(OPIOID)
        for _ in range(3):
            encounter.order(HELD_NALOXONE)                       # tres lactatos pendientes: vuelven en 5, 6 y 7
        encounter.wait_until(12)
    assert encounter.state["diagnostics"]["lactate"]["time_min"] > 5            # la hora que el motor conserva
    stamps = _engine_stamp(encounter, "naloxone")
    assert stamps == [5, 5, 5]
    assert [item.minute for item in encounter.shadow.mirrored if item.kind == "naloxone"] == stamps
    assert [item["executed_minute"] for item in encounter.shadow.held] == stamps
    # la unica brecha es la que el adaptador ya declaraba para una dosis repetida; ninguna de sincronizacion
    assert all("a repeat dose adds nothing" in gap["why"] for gap in encounter.shadow.gaps)


def test_p3r_158h_the_record_is_the_code():
    held = rec.HELD_ORDERS
    assert held["events"] == rs.HELD_ORDER_EVENTS and set(held["event_semantics"]) == set(rs.HELD_ORDER_EVENTS)
    assert len(fam.DISPOSITIONS) == held["dispositions"] and fam.HELD_NOT_EXECUTED in fam.DISPOSITIONS
    assert fam.HELD_NOT_EXECUTED not in fam.MIRRORED_DISPOSITIONS
    assert "SUPERSEDED" in previous.FAILURE_VISIBILITY["held_orders"]
    # el arreglo esta en la capa compartida: ni el motor ni el nucleo tienen una palabra de el
    engine = (ROOT / "family_engine.py").read_text(encoding="utf-8")
    assert "runtime_shadow" not in engine and "ORDER_RELEASED" not in engine
    families = (ROOT / "runtime_shadow_families.py").read_text(encoding="utf-8")
    assert "deferred_orders" not in families                   # ningun adaptador lee la lista del motor


# -- P3-159: residuos de sesion ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", (GI, OPIOID))
def test_p3r_159a_another_attempt_is_another_encounter_even_with_an_identical_patient(case, traces):
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        first = acceptance.Encounter(case).state
        second = acceptance.Encounter(case).state
        assert rs._encounter_id(first) == rs._encounter_id(second)             # dos intentos, la misma llegada
        session = rs.ShadowSession.start(first, generation=41)
        assert session.generation == rs.generation_key(41) and session.generation.startswith("g-")
        assert session.is_for(first, 41) and session.left_arrival is False
        # la regla de estado sola NO los distingue; la generacion si
        assert rs.ShadowSession.start(first).is_for(second)
        assert not session.is_for(second, 42) and not session.is_for(second) and not session.is_for(second, "")
        plain = rs.ShadowSession.start(first)
        assert plain.generation is None and plain.is_for(first) and not plain.is_for(first, 41)
        page = Page(generation=41)
        opened = page.session_for(first)
        page.generation = 42
        assert page.session_for(second) is not opened and len(page.opened) == 2
        assert [item.generation for item in page.opened] == [rs.generation_key(41), rs.generation_key(42)]
    assert rs.generation_key(None) is None and rs.generation_key("") is None
    assert "41" not in session.generation[2:6] or len(session.generation) == 18
    trace = store.trace_of(session)
    assert trace["generation"] == session.generation and store.verify(dict(trace, trace_digest=store.trace_digest(
        trace)))["verified"] is not None
    residual = rec.SESSION_RESIDUALS["generation"]
    assert residual["explicit_identifier_exists"] and residual["no_heuristic_added"] and residual["residual"]


def test_p3r_159b_the_page_hands_the_attempt_identity_to_the_session():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    helper = app[app.index("def _runtime_shadow_session():"):app.index("def _runtime_authority_site():")]
    assert 'generation = st.session_state.get("_attempt_id")' in helper
    assert "is_for(st.session_state.state, generation)" in helper and "generation=generation" in helper
    runtime = (ROOT / "curriculum_runtime.py").read_text(encoding="utf-8")
    assert 'st.session_state["_attempt_id"] = record["id"]' in runtime


def test_p3r_159c_hidden_state_is_derived_and_the_certified_mapping_reads_none_of_it():
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        for case in (GI, OPIOID):
            state = acceptance.Encounter(case).state
            touched = copy.deepcopy(state)
            touched.setdefault("hidden", {})["tissue_perfusion"] = 0.123
            touched["hidden"]["made_up"] = "x"
            assert rs.arrival_eligibility(touched)["eligible"] is True
            mine, theirs = rs.ShadowSession.start(state), rs.ShadowSession.start(touched)
            assert mine.failures == theirs.failures == []
            assert mine.runner.anchors == theirs.runner.anchors
    adapter = (ROOT / "clinical_core" / "legacy_adapter.py").read_text(encoding="utf-8")
    assert adapter.count("hidden") == 1 and '"hidden": {}' in adapter           # solo al construir un estado vacio
    assert rec.SESSION_RESIDUALS["hidden_state"]["classification"] == "IRRELEVANT_TO_THE_CERTIFIED_MAPPING"
    assert "hidden" not in rs.ARRIVAL_CONDITIONS and not any("hidden" in name for name in rs.ARRIVAL_CONDITIONS)


def test_p3r_159d_what_the_digest_protects_and_what_it_does_not(traces):
    trace = _latest(_play(OPIOID, (NALOXONE,), until=3))
    other = _latest(_play(OPIOID, (OXYGEN,), until=3))
    assert store.verify(trace)["verified"]
    edited = copy.deepcopy(trace)
    edited["session_minutes"] = 99
    assert not store.verify(edited)["verified"]                                  # editar sin recalcular: se ve
    resealed = dict(edited)
    resealed["trace_digest"] = store.trace_digest(resealed)
    assert not store.verify(resealed)["verified"]                                # recalcular e incoherente: se ve
    assert store.verify(other)["verified"]                 # otro registro entero y coherente: nada lo distingue
    source = (ROOT / "runtime_shadow_store.py").read_text(encoding="utf-8")
    assert "import hmac" not in source and "is not a signature" in source
    integrity = rec.SESSION_RESIDUALS["trace_integrity"]
    assert integrity["cryptographic_infrastructure_added"] is False
    assert len(integrity["protects"]) == 4 and len(integrity["does_not_protect"]) == 3


# -- P3-160: transicion terminal y consciencia (solo lectura) --------------------------------------------------------

def test_p3r_160a_the_audit_table_is_what_the_code_holds():
    audit = rec.TERMINAL_CONSCIOUSNESS
    assert audit["read_only"] and audit["implemented_this_cycle"] is False
    assert all(row["status"] in rec.ARCHITECTURE_STATUSES and row["detail"] for row in audit["architecture"])
    assert {row["status"] for row in audit["architecture"]} == set(rec.ARCHITECTURE_STATUSES) - {"AUXILIARY_EXISTS"}
    # la regla de colapso esta apagada y las dos capas candidatas no tienen quien las llame en vivo
    assert dv.DEFAULT_PROFILE.collapse_output_threshold is None and dv.DEFAULT_PROFILE.collapse_burden_limit is None
    derived = (ROOT / "clinical_core" / "derived.py").read_text(encoding="utf-8")
    assert "APNOEA_BOUNDARY_UNRESOLVED" in derived
    assert "max(anchors.consciousness_level, _level(sbp, profile.pressure_levels), _level(spo2, " in derived
    for name in ("runtime_shadow.py", "runtime_shadow_store.py", "runtime_shadow_observer.py", "app.py",
                 "family_engine.py", "pilot_acceptance.py"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "encephalopathy" not in text and "shadow_diagnostics" not in text, name
    families = (ROOT / "runtime_shadow_families.py").read_text(encoding="utf-8")
    assert families.count("shadow_diagnostics(") == 1                 # su definicion, y ningun llamador
    assert audit["verdict"] == "COMMON_CORE_EXTENSION_REQUIRED" and audit["verdict"] in audit["verdict_options"]
    assert len(audit["verdict_options"]) == 4 and audit["why_not_mapping_only"] and audit["why_not_redesign"]
    assert audit["visible_to_a_resident_today"] is False and rs.COMMON_CORE_RUNTIME_AUTHORITY is False


def test_p3r_160b_the_contradiction_is_measured_not_supposed():
    measured = rec.TERMINAL_CONSCIOUSNESS["contradictions_possible_today"][0]["measured"]
    encounter = _play(measured["case"], (), until=30)
    assert encounter.arrested and encounter.minute == measured["legacy_arrest_minute"]
    assert encounter.state["observable"]["mental_status"] == "Unresponsive"
    assert encounter.state["observable"]["hr"] == 0
    runner = encounter.shadow.runner
    last = fam.run_channels(runner)[-1]
    assert last["minute"] == measured["legacy_arrest_minute"]
    channels = last["channels"]
    assert channels["pulse_present"] is measured["core_pulse_present"] is True
    assert channels["sbp"] == measured["core_sbp"] and channels["spo2"] == measured["core_spo2"]
    assert channels["consciousness_level"] == measured["core_consciousness_level"]
    # la unica senal: una divergencia critica de seguridad en el pulso y el ritmo de ese minuto
    critical = {(item.minute, item.variable) for item in runner.divergences if item.status == rs.SAFETY_CRITICAL}
    assert critical == {(20, "pulse_present"), (20, "rhythm")}
    # y el nivel del nucleo no se movio en todo el curso sin tratar
    assert {row["channels"]["consciousness_level"] for row in fam.run_channels(runner)} == {2}


# -- P3-162: el paquete de revision docente ---------------------------------------------------------------------------

def test_p3r_162a_the_first_channel_of_each_treatment_expected_and_observed(traces):
    gi = _latest(_play(GI, ("Transfuse 2 units of packed red cells.", OXYGEN, "Give pantoprazole 80 mg IV.",
                            "Give 1 L of lactated Ringer's."), until=100))
    effects = obs.first_effects(gi)
    assert [effect["kind"] for effect in effects] == ["blood", "oxygen", "ppi", "fluid"]
    for effect in effects:
        assert effect["status"] == "OBSERVED" and effect["expected_is_among_the_first"] is True, effect
        assert effect["first_minute"] == effect["effective_minute"] > effect["order_minute"]
        assert effect["expected_first_channel"] == obs.EXPECTED_FIRST_CHANNEL[effect["contributor_type"]]
    fluid = obs.first_effects(_latest(_play(GI, ("Give 1 L of lactated Ringer's.",), until=30)))[0]
    assert fluid["kind"] == "fluid" and fluid["expected_is_among_the_first"]
    later = dict((channel, minute) for channel, minute in fluid["downstream"])
    assert later["lactate"] > later["D"] > fluid["first_minute"]              # en GI el orden se ve
    held_encounter = _play(OPIOID, (OXYGEN, HELD_NALOXONE), until=20)
    opioid = _latest(held_encounter)
    for run in (store.SESSION_RUN_NAME,) + tuple(fam.TRANSMISSION_WITNESSES):
        found = {effect["kind"]: effect for effect in obs.first_effects(opioid, run)}
        assert set(found) == {"oxygen", "naloxone"}, run
        assert found["naloxone"]["expected_first_channel"] == "central_availability"
        stamp = _engine_stamp(held_encounter, "naloxone")[0]
        assert found["naloxone"]["order_minute"] == stamp > 1                     # retenida: el minuto del motor
        assert found["naloxone"]["first_minute"] == found["naloxone"]["effective_minute"] == stamp + 1
        assert found["naloxone"]["expected_is_among_the_first"] and found["naloxone"]["downstream"] == []
        assert found["oxygen"]["expected_first_channel"] == "fio2" and found["oxygen"]["expected_is_among_the_first"]
    assert "same simulated minute" in rec.FACULTY_REVIEW["finding"]
    assert obs.first_effects({"runs": 7}) and obs.first_effects({}) == []     # nunca levanta


def test_p3r_162b_the_package_is_written_outside_the_repository_and_changes_nothing(traces, tmp_path):
    traces_in = [_latest(_play(GI, ("Give 1 L of lactated Ringer's.",), until=10)),
                 _latest(_play(OPIOID, (NALOXONE, "Ventilate with bag-valve-mask."), until=5))]
    before = copy.deepcopy(traces_in)
    outcome = obs.write_review_package(traces_in, tmp_path / "package")
    assert outcome["written"] and outcome["traces"] == 2 and traces_in == before
    assert outcome["files"] == ["index.md", "trace_01_gi_bleed.html", "trace_02_opioid.html"]
    index = (tmp_path / "package" / "index.md").read_text(encoding="utf-8")
    assert index.startswith("# Shadow trace review package — DEVELOPMENT ONLY")
    for heading in ("### Action timeline", "### First causal channel, expected and observed",
                    "### Region witnesses", "### Failures", "### Unresolved synthetic parameters",
                    "### Questions for faculty"):
        assert index.count(heading) == 2, heading
    assert "initial state: sbp" in index and "replay: exact" in index and "None selected." in index
    assert "DECLARED_GAP" in index and "CONDITIONAL_DEVELOPMENT_REGION; conditional on deepening_per_min = 0.005" in index
    for family, questions in obs.FACULTY_QUESTIONS.items():
        assert all(question.endswith("?") or "?" in question for question in questions)
        assert all(question[:40] in index for question in questions), family
        # juicio docente, no implementacion
        assert not any(word in " ".join(questions).lower() for word in ("digest", "adapter", "replay", "module",
                                                                         "contributor", "python"))
    entry = obs.review_entry(traces_in[1])
    assert entry["selected_witness"] is None and len(entry["witnesses"]) == 3
    assert entry["replay"]["reproduces"] and entry["unresolved_synthetic_parameters"]
    assert set(rec.FACULTY_REVIEW["per_trace"]) >= {"initial state", "action timeline", "replay status"}
    # nunca dentro del repositorio, nunca relativo
    assert obs.write_review_package(traces_in, ROOT / "docs" / "package")["written"] is False
    assert obs.write_review_package(traces_in, "package")["written"] is False
    planted = tmp_path / "linked"
    planted.mkdir()
    (planted / "index.md").symlink_to(ROOT / "docs" / "planted_by_a_link.md")
    assert obs.write_review_package(traces_in, planted)["written"] is False     # nunca a traves de un enlace
    assert not (ROOT / "docs" / "planted_by_a_link.md").exists()
    hostile = copy.deepcopy(traces_in[0])
    hostile["actions"][0]["why"] = "see [here](http://x) `code` *bold* | cell\r\n<b>"
    text = obs.review_markdown([dict(obs.review_entry(traces_in[0]), actions=hostile["actions"])])
    assert "](http" not in text and "`code`" not in text and "<b>" not in text and "*bold*" not in text
    assert not (ROOT / "docs" / "package").exists()
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "runtime_shadow_observer" not in app and rec.FACULTY_REVIEW["inside_the_main_application"] is False


def test_p3r_162c_the_command_line_writes_the_package_of_the_stored_heads(traces, tmp_path, capsys):
    _play(GI, ("Give 1 L of lactated Ringer's.", "Reassess in 5 minutes."))
    assert obs.main(["--store", str(traces), "--review", str(tmp_path / "out")]) == 0
    assert "(1 traces)" in capsys.readouterr().out and (tmp_path / "out" / "index.md").exists()
    assert obs.main(["--store", str(traces), "--review", str(ROOT / "out")]) == 2


# -- P3-163: seleccion de casos ----------------------------------------------------------------------------------------

def test_p3r_163a_the_comparison_covers_the_nine_criteria_and_selects_nothing():
    selection = rec.CASE_SELECTION
    assert len(selection["criteria"]) == 9 and tuple(selection["comparison"]) == selection["criteria"]
    for criterion, row in selection["comparison"].items():
        assert row["gi_bleed"] and row["opioid"] and row["better"] in ("gi_bleed", "opioid", "neither"), criterion
    wins = [row["better"] for row in selection["comparison"].values()]
    assert selection["ranking"] == tuple(sorted(rs.LIVE_FAMILIES, key=lambda name: -wins.count(name)))
    assert selection["is_a_selection"] is False and selection["faculty_decision_pending"] is True
    assert set(selection["blockers"]) == set(rs.LIVE_FAMILIES) and all(selection["blockers"].values())
    # lo que la comparacion afirma del runtime, es del runtime
    assert rs.GOLDEN_REQUIRED == ("gi_bleed",)
    untreated = _play(GI, (), until=120)
    assert not untreated.arrested and untreated.state["family_state"].get("arrest_at") is None
    statuses = {item.status for item in _play(OPIOID, (), until=10).shadow.runner.divergences}
    assert statuses == {rs.NOT_COMPARABLE}


# -- P3-164: ataques y aislamiento con ordenes retenidas ------------------------------------------------------------------

HELD_POOL = {
    GI: POOL[GI] + tuple(text for text, _minute in HELD[GI].values()) + (NEVER_RELEASED[GI],),
    OPIOID: POOL[OPIOID] + (HELD_NALOXONE, UNSUPPORTED_HELD, NEVER_RELEASED[OPIOID]),
}


def _held_sequence(case, seed) -> tuple:
    chooser = random.Random(f"held:{case}:{seed}")
    turns = [chooser.choice(HELD_POOL[case]) for _ in range(chooser.randint(3, 6))]
    turns.insert(chooser.randrange(len(turns) + 1), chooser.choice(HELD_POOL[case][len(POOL[case]):]))
    return tuple(turns) + ("Reassess in 5 minutes.", "Reassess in 5 minutes.")


def test_p3r_164a_the_held_sequences_are_bounded_repeatable_and_do_hold_orders():
    for case in (GI, OPIOID):
        sequences = [_held_sequence(case, seed) for seed in SEEDS]
        assert sequences == [_held_sequence(case, seed) for seed in SEEDS]
        assert all(6 <= len(turns) <= 9 and set(turns) <= set(HELD_POOL[case]) for turns in sequences)
        assert all(any("wait for the result" in text for text in turns) for turns in sequences)
    assert rec.CERTIFICATION["randomized"]["seeds"] == SEEDS and rec.CERTIFICATION["randomized"]["families"] == 2


@pytest.mark.parametrize("case", (GI, OPIOID))
@pytest.mark.parametrize("seed", SEEDS)
def test_p3r_164b_with_held_orders_the_encounter_does_not_notice_and_the_trace_is_whole(case, seed, traces):
    turns = _held_sequence(case, seed)
    on, page = _play_on_page(case, turns)
    off = _play(case, turns, mode=None)
    # igualdad exacta: estado heredado, entradas de la puntuacion, destino de cada orden, lo que ve el residente
    assert on.state == off.state and ev.authoritative(on) == ev.authoritative(off)
    assert ev.fates(on) == ev.fates(off) and on.minute == off.minute and on.arrested == off.arrested
    assert off.shadow is None and rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    session = on.shadow
    assert len(page.opened) == 1 and session.turns == len(turns) and session.held
    assert [item for item in session.failures if item.where != "legacy_snapshot"] == [], session.failures
    # cada orden retenida tiene un destino, y cada una ejecutada se reflejo una sola vez en su minuto
    executed = [item for item in session.held if item["state"] == rs.ORDER_EXECUTED]
    assert all(item["state"] in rs.HELD_ORDER_EVENTS and item["state"] != rs.ORDER_RELEASED for item in session.held)
    identities = [item.order_id for item in session.mirrored]
    assert len(identities) == len(set(identities))
    for item in executed:
        assert identities.count(item["shadow_order_id"]) == 1
        assert item["executed_minute"] >= item["placed_minute"]
    stamps = sorted(entry["time_min"] for entry in on.state["treatments"]["administered_medications"]
                    if entry["agent"] == "naloxone")
    if case == OPIOID:
        assert sorted(item.minute for item in session.mirrored if item.kind == "naloxone") == stamps
    # la traza: entera, sin accion perdida, verificada y reproducida
    trace = _latest(on)
    assert len(trace["held_orders"]) == len(session.held)
    waiting = [row for row in trace["actions"] if row["disposition"] == fam.HELD_NOT_EXECUTED]
    assert len(waiting) == len(session.held) - len(executed)
    assert not [row for row in trace["actions"] if row["disposition"] == fam.NOT_MIRRORED]
    assert all(row["effective_minute"] is None or row["effective_minute"] == row["order_minute"] + 1
               for row in trace["actions"] if row["disposition"] in fam.MIRRORED_DISPOSITIONS)
    assert trace["status"]["state"] in (fam.COMPLETE, fam.COMPLETE_WITH_UNSUPPORTED_ACTIONS)
    assert store.verify(trace)["verified"]
    if on.minute:
        assert store.replay(trace)["reproduces"]


def test_p3r_164c_a_stale_session_a_wrong_family_and_a_mutated_trace(traces):
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        old = acceptance.Encounter(OPIOID)
        old.order(HELD_NALOXONE)
        old.wait_until(8)
        fresh = acceptance.Encounter(OPIOID)
        assert not old.shadow.is_for(fresh.state)                  # sesion vieja, llegada nueva: otro encuentro
        other = acceptance.Encounter(GI)
        assert not old.shadow.is_for(other.state)
    trace = _latest(old)
    # una orden retenida borrada de la traza y re-sellada: la traza ya no es coherente consigo misma
    for edit in (lambda body: body["actions"].pop(next(i for i, row in enumerate(body["actions"])
                                                        if row["kind"] == "naloxone")),
                 lambda body: body["runs"][store.SESSION_RUN_NAME].update(
                     replay_input=dict(body["runs"][store.SESSION_RUN_NAME]["replay_input"], family="gi_bleed")),
                 lambda body: body.update(family="gi_bleed")):
        body = copy.deepcopy(trace)
        edit(body)
        body["trace_digest"] = store.trace_digest(body)
        checked = store.verify(body)
        assert not checked["verified"], checked
        assert not store.replay(body)["reproduces"]
    # un replay que no coincide: se dice, y la vista no lo muestra como completo
    body = copy.deepcopy(trace)
    body["runs"][store.SESSION_RUN_NAME]["minutes"][6]["channels"]["spo2"] += 1.0
    body["trace_digest"] = store.trace_digest(body)
    replayed = store.replay(body)
    assert not replayed["reproduces"]
    assert obs.view(body, replay=replayed)["status"]["state"] not in (fam.COMPLETE,
                                                                     fam.COMPLETE_WITH_UNSUPPORTED_ACTIONS)


def test_p3r_164d_a_store_that_fails_changes_nothing_of_the_encounter(monkeypatch, tmp_path):
    blocked = tmp_path / "a-file"
    blocked.write_text("not a directory", encoding="utf-8")
    turns = (HELD_NALOXONE, "Reassess in 5 minutes.", "Reassess in 5 minutes.")
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv(store.STORE_FLAG, str(blocked / "traces"))
        on = _play(OPIOID, turns)
    off = _play(OPIOID, turns, mode=None)
    assert on.state == off.state and ev.authoritative(on) == ev.authoritative(off) and ev.fates(on) == ev.fates(off)
    assert on.shadow.persistence["stored"] is False
    assert [item.kind for item in on.shadow.mirrored].count("naloxone") == 1     # la sombra siguio, y se dice
    assert fam.TRACE_PERSISTENCE_FAILED in store.trace_of(on.shadow)["status"]["codes"]


def test_p3r_164e_the_boundary_of_the_synthetic_region_is_exact():
    edge = fam.TRANSMISSION_MATHEMATICAL_REGION[1]
    assert max(fam.TRANSMISSION_WITNESSES.values()) <= edge and min(fam.TRANSMISSION_WITNESSES.values()) > 0
    assert fam.TRANSMISSION_ACTIVE_REGION == {"above": 0.0, "up_to": edge, "zero_is": "NEGATIVE_CONTROL_NOT_A_WITNESS"}
    floor = sensitivity.FLOOR
    inside = sensitivity.mg._run(sensitivity._variant(edge - 1e-4), OPIOID, minutes=T).series["spo2"][T]
    outside = sensitivity.mg._run(sensitivity._variant(edge + 1e-3), OPIOID, minutes=T).series["spo2"][T]
    assert inside >= floor > outside
    assert tuple(rec.ATTACKS) == rec.CERTIFICATION["attacks"] and len(rec.ATTACKS) == 12


# -- P3-165 y P3-166: compuertas, preparacion y hoja de ruta ---------------------------------------------------------------

GATE_STATES = ("GREEN", "PARTIAL", "BLOCKED", "NOT_YET_EVALUATED")


def test_p3r_165a_the_nine_gates_read_again():
    assert [gate["gate"] for gate in rec.GATES] == [gate["gate"] for gate in previous.GATES] and len(rec.GATES) == 9
    before = {gate["gate"]: gate["status"] for gate in previous.GATES}
    for gate in rec.GATES:
        assert gate["status"] in GATE_STATES and gate["before"] == before[gate["gate"]], gate["gate"]
        assert gate["evidence"] and (gate["blocker"] is None) == (gate["status"] == "GREEN"), gate["gate"]
    counts = {state: sum(1 for gate in rec.GATES if gate["status"] == state) for state in GATE_STATES}
    pilot = rec.READINESS["RESIDENT_PILOT_REVIEW_READINESS"]
    assert pilot["gates"] == counts == {"GREEN": 4, "PARTIAL": 2, "BLOCKED": 3, "NOT_YET_EVALUATED": 0}
    moved = tuple(gate["gate"] for gate in rec.GATES if gate["status"] != gate["before"])
    assert moved == pilot["moved_this_cycle"] == ("case selection",)
    assert pilot["still_blocked"] == tuple(gate["gate"] for gate in rec.GATES if gate["status"] == "BLOCKED")
    by_name = {gate["gate"]: gate for gate in rec.GATES}
    # ninguna compuerta de cara al residente se pone verde porque exista herramienta docente de desarrollo
    for name in ("UI exposure", "runtime exposure", "resident-facing safety"):
        assert by_name[name]["status"] == "BLOCKED" and by_name[name]["blocker"], name
    assert "does not make this green" in by_name["UI exposure"]["blocker"]
    assert by_name["case selection"]["status"] == "PARTIAL" and "not a selection" in by_name["case selection"]["scope"]
    assert by_name["faculty review workflow"]["status"] == "PARTIAL"


def test_p3r_165b_three_answers_kept_apart():
    assert set(rec.READINESS) == {"SIMULATION_ENGINE_READINESS", "FACULTY_REVIEW_READINESS",
                                  "RESIDENT_PILOT_REVIEW_READINESS"}
    assert rec.READINESS["RESIDENT_PILOT_REVIEW_READINESS"]["verdict"] == "NOT_READY_FOR_RESIDENT_PILOT_REVIEW"
    assert rec.READINESS["RESIDENT_PILOT_REVIEW_READINESS"]["exact_blockers"]
    for name in ("SIMULATION_ENGINE_READINESS", "FACULTY_REVIEW_READINESS"):
        assert rec.READINESS[name]["verdict"].endswith("_DEVELOPMENT")
        assert rec.READINESS[name]["holds"] and rec.READINESS[name]["does_not_hold"]
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False and rs.LIVE_FAMILIES == ("gi_bleed", "opioid")
    assert {"clinical validation", "resident readiness", "any change to common physiology",
            "a deepening-rate interval"} <= set(rec.NOT_CLAIMED)
    assert list(rec.FACULTY_DECISIONS) == [f"FD-{number}" for number in range(151, 157)]
    assert rec.BROWSER["verdict"] == "BROWSER_PATH_SHADOW_VALIDATED" and rec.BROWSER["limits"]
    assert rec.BROWSER["resident_visible_widgets_created"] is False


def test_p3r_166a_the_next_step_is_a_faculty_decision_not_another_family():
    roadmap = rec.ROADMAP
    assert rec.TERMINAL_CONSCIOUSNESS["verdict"] in roadmap["why"]
    assert "terminal transition and consciousness" in roadmap["next_explicit_faculty_decision_package"]
    assert roadmap["next_step_is_another_physiology_family"] is False and roadmap["is_a_selection"] is False
    assert len(roadmap["package_asks"]) == 4 and len(roadmap["in_parallel_no_code"]) == 3


def test_p3r_167_the_record_module_is_pure_data():
    source = (ROOT / "shadow_resolution_record.py").read_text(encoding="utf-8")
    assert "import " not in source and "runtime_" + "shadow" not in source and "phase3_" + "shadow" not in source
    assert rec.STARTING_HEAD == "f1f6034" and rec.CYCLE == "P3-156..P3-166"
