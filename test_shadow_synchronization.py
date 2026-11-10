"""Cierre de la sincronizacion de la sombra en vivo (2026-11-10): P3-167 y P3-168.

- P3-167: una orden retenida que el motor ejecuta mientras pasa el tiempo de una ACTIVIDAD DE INFORMACION (una
  pregunta, un examen) se refleja una vez, en su minuto real. Se lee el recibo del motor; nunca el contenido de
  la actividad, nunca la colocacion.
- P3-168: secuencias aleatorias acotadas de GI y de opioide con ejecucion ordinaria, ejecucion diferida en
  turnos de ordenes, ejecucion diferida en actividades de informacion, observacion duplicada y acciones no
  soportadas: toda accion ejecutada se refleja exactamente una vez y ninguna no ejecutada toca la sombra.

``_activity`` son las sentencias que la pagina ejecuta en ``spend_clinical_time``; ``test_p3s_167a`` fija que
siguen siendo las de ``app.py``. Registro: terminal_amendment_record (bloque SYNCHRONIZATION). Etiquetas ``p3s``.
"""
import copy
import inspect
import random
from pathlib import Path

import pytest

import family_engine
import pilot_acceptance as acceptance
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam
import runtime_shadow_store as store
import terminal_amendment_record as rec
from test_shadow_observability import GI, NALOXONE, OPIOID, OXYGEN, POOL, SEEDS, _latest, traces  # noqa: F401
from test_shadow_resolution import HELD, HELD_NALOXONE, NEVER_RELEASED, UNSUPPORTED_HELD, _engine_stamp, _rows

ROOT = Path(__file__).resolve().parent
SYNC = rec.SYNCHRONIZATION


def _activity(encounter, minutes, label="history_question", again=0):
    """Lo que hace la pagina cuando una pregunta o un examen cuesta tiempo clinico."""
    shadow = getattr(encounter, "shadow", None)
    before = shadow.capture(encounter.state) if shadow is not None else None
    result = family_engine.advance_clinical_time(encounter.state, minutes, label=label)
    if shadow is not None:
        shadow.observe_time(before, encounter.state, result)
        for _ in range(again):                                    # la misma actividad, mirada otra vez
            shadow.observe_time(before, encounter.state, result)
    return result


def _run(case, steps, mode=rs.MODE_SHADOW_COMPARE, again=0):
    """Un encuentro: un texto es una orden; un entero, una actividad de informacion de esos minutos."""
    with ev.shadow(mode):
        encounter = acceptance.Encounter(case)
        for step in steps:
            if isinstance(step, int):
                _activity(encounter, step, again=again)
            else:
                encounter.order(step)
    return encounter


def _released_minute(encounter, study):
    return encounter.state["diagnostics"][study]["time_min"]


# -- P3-167A: el camino real del motor ---------------------------------------------------------------------------------

def test_p3s_167a_one_engine_path_and_the_page_helper_observes_it():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    helper = app[app.index("def spend_clinical_time("):app.index("    record_information_activity(activity, request")]
    for statement in ("_shadow = _runtime_shadow_session()",
                      "_shadow_before = _shadow.capture(state) if _shadow is not None else None",
                      "result = advance_clinical_time(state, minutes, label=activity)",
                      "_shadow.observe_time(_shadow_before, st.session_state.state, result)"):
        assert helper.count(statement) == 1, statement
    assert helper.index("_shadow.capture(state)") < helper.index("advance_clinical_time(state") < helper.index(
        "observe_time(")
    # la sombra recibe estado y recibos: ni la pregunta ni la respuesta
    call = helper[helper.index("_shadow.observe_time("):]
    assert "request" not in call[:call.index("\n")] and "response" not in call[:call.index("\n")]
    assert list(inspect.signature(rs.ShadowSession.observe_time).parameters) == ["self", "before", "after", "result"]
    # el unico camino del motor que deja pasar tiempo fuera de un turno de ordenes, y sus tres llamadores
    assert app.count("advance_clinical_time(") == 1 and app.count("spend_clinical_time(") == 4
    assert app.count('spend_clinical_time(_clock.ACTIVE_MINUTES["history_question"]') == 2
    assert app.count("spend_clinical_time(_clock.examination_minutes(") == 1
    engine = (ROOT / "family_engine.py").read_text(encoding="utf-8")
    body = engine[engine.index("def advance_clinical_time("):engine.index("def recorded_only(")]
    assert "summaries.extend(_release_due_orders(candidate))" in body          # el motor ejecuta, y lo dice
    assert "runtime_shadow" not in engine
    assert SYNC["engine_path"]["function"] == "family_engine.advance_clinical_time"
    assert SYNC["engine_path"]["page_callers"] == 3 and SYNC["engine_path"]["result_review_advances_time"] is False


# -- P3-167B: se refleja la ejecucion, no la colocacion ---------------------------------------------------------------

@pytest.mark.parametrize("case,kind", [(GI, "blood"), (GI, "fluid"), (GI, "oxygen"), (OPIOID, "naloxone")])
def test_p3s_167b_a_release_during_an_information_activity_is_mirrored_once_at_its_real_minute(case, kind, traces):
    text, _minute = HELD[case][kind]
    encounter = _run(case, (text, 14))
    session, trace = encounter.shadow, _latest(encounter)
    entry = session.held[0]
    executed = _released_minute(encounter, entry["after_result"])
    assert entry["state"] == rs.ORDER_EXECUTED and entry["executed_minute"] == executed > entry["placed_minute"]
    if kind == "naloxone":
        assert _engine_stamp(encounter, "naloxone") == [executed]
    mirrored = [item for item in session.mirrored if item.kind == kind]
    assert [(item.minute, item.order_id) for item in mirrored] == [(executed, entry["shadow_order_id"])]
    row = _rows(trace, kind)
    assert [(r["disposition"], r["order_minute"], r["effective_minute"], r["placed_minute"]) for r in row] == [
        (fam.BUILT, executed, executed + 1, entry["placed_minute"])]
    assert session.gaps == [] and session.failures == [] and trace["status"]["state"] == fam.COMPLETE
    assert session.runner.minutes_done == encounter.minute == trace["session_minutes"]
    assert store.verify(trace)["verified"] and store.replay(trace)["reproduces"]
    # la MISMA corrida que si el motor la hubiera liberado dentro de un turno de ordenes
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        ordinary = acceptance.Encounter(case)
        ordinary.order(text)
        ordinary.wait_until(encounter.minute)
    assert [item["executed_minute"] for item in ordinary.shadow.held] == [executed]
    assert session.runner.digests() == ordinary.shadow.runner.digests()[:len(session.runner.digests())]


def test_p3s_167b_the_activity_itself_mirrors_nothing():
    quiet = _run(OPIOID, (5, 3))
    assert quiet.shadow.mirrored == [] and quiet.shadow.held == [] and quiet.shadow.turns == 2
    assert quiet.shadow.runner.minutes_done == quiet.minute == 8 and quiet.shadow.left_arrival is True
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        waited = acceptance.Encounter(OPIOID)
        waited.wait_until(8)
    assert quiet.shadow.runner.digests() == waited.shadow.runner.digests()      # solo paso el tiempo
    # un recibo que no es una liberacion (un resultado que llega, un evento del caso) no refleja nada
    session = quiet.shadow
    session.observe_time(quiet.state, quiet.state, {"action_summaries": [
        {"type": "naloxone", "label": "not a release"}, {"type": "diagnostic", "diagnostic_type": "lactate"}, "x"]})
    assert session.mirrored == [] and session.gaps == [] and session.failures == []


# -- P3-167C: aislamiento ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", (GI, OPIOID))
def test_p3s_167c_the_observer_changes_nothing_of_the_encounter(case):
    steps = tuple(text for text, _minute in HELD[case].values()) + (4, "Reassess in 2 minutes.", 9)
    on, off = _run(case, steps), _run(case, steps, mode=None)
    assert off.shadow is None and on.state == off.state and on.minute == off.minute
    assert ev.authoritative(on) == ev.authoritative(off) and ev.fates(on) == ev.fates(off)
    assert on.arrested == off.arrested and rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    # no toca lo que se le da, y no ejecuta nada: el estado del motor es el mismo antes y despues de observar
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(case)
        encounter.order(next(iter(HELD[case].values()))[0])
        before = encounter.shadow.capture(encounter.state)
        result = family_engine.advance_clinical_time(encounter.state, 12)
        kept = copy.deepcopy((before, encounter.state, result))
        encounter.shadow.observe_time(before, encounter.state, result)
        assert (before, encounter.state, result) == kept
    source = inspect.getsource(rs.ShadowSession.observe_time)
    for word in ("family_engine", "advance_clinical_time", "_order(", "execute", "request", "response", "label"):
        assert word not in source.split('"""')[2], word


def test_p3s_167c_a_failure_of_the_observer_stays_in_the_observer(monkeypatch):
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(OPIOID)
        encounter.order(HELD_NALOXONE)
        monkeypatch.setattr(rs.ShadowSession, "_release", lambda self, *args: (_ for _ in ()).throw(RuntimeError("x")))
        _activity(encounter, 8)                                              # no levanta hacia la pagina
    assert [item.where for item in encounter.shadow.failures] == ["observe_time"]
    assert _engine_stamp(encounter, "naloxone") == [5]                       # el motor hizo lo suyo igual
    for junk in (None, {}, {"action_summaries": None}, {"action_summaries": "text"}):
        encounter.shadow.observe_time(None, encounter.state, junk)           # nunca levanta


# -- P3-167D: controles negativos -----------------------------------------------------------------------------------------

def test_p3s_167d_remains_held():
    encounter = _run(OPIOID, (HELD_NALOXONE, 2, 1))
    session = encounter.shadow
    assert [item["state"] for item in session.held] == [rs.ORDER_HELD] and encounter.minute < 5
    assert not [item for item in session.mirrored if item.kind == "naloxone"] and session.gaps == []
    assert encounter.state["family_state"]["deferred_orders"] and _engine_stamp(encounter, "naloxone") == []
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        plain = acceptance.Encounter(OPIOID)
        plain.order("Order a lactate.")
        plain.wait_until(encounter.minute)
    assert session.runner.digests() == plain.shadow.runner.digests()        # una orden no ejecutada no toca la sombra


def test_p3s_167d_becomes_terminal_not_executable(traces):
    encounter = _run(OPIOID, (NEVER_RELEASED[OPIOID], 12, 15))
    session, trace = encounter.shadow, _latest(encounter)
    assert encounter.state["family_state"]["arrest_at"] == 20
    assert [item["state"] for item in session.held] == [rs.ORDER_TERMINAL_NOT_EXECUTABLE]
    assert not [item for item in session.mirrored if item.kind == "naloxone"]
    assert [row["disposition"] for row in _rows(trace, "naloxone")] == [fam.HELD_NOT_EXECUTED]
    assert store.verify(trace)["verified"]


def test_p3s_167d_duplicate_observation():
    once, twice = _run(OPIOID, (HELD_NALOXONE, 9, 3)), _run(OPIOID, (HELD_NALOXONE, 9, 3), again=2)
    for encounter in (once, twice):
        assert [item.minute for item in encounter.shadow.mirrored if item.kind == "naloxone"] == [5]
        assert encounter.shadow.gaps == [] and encounter.shadow.failures == []
    assert once.shadow.runner.digests() == twice.shadow.runner.digests()
    assert once.shadow.ensemble.digests() == twice.shadow.ensemble.digests()
    assert [item["events"] for item in once.shadow.held] == [item["events"] for item in twice.shadow.held]


def test_p3s_167d_multiple_identical_studies():
    encounter = _run(OPIOID, (HELD_NALOXONE, HELD_NALOXONE, HELD_NALOXONE, 10))
    stamps = _engine_stamp(encounter, "naloxone")
    assert stamps == [5, 5, 5] and encounter.state["diagnostics"]["lactate"]["time_min"] > 5
    assert [item.minute for item in encounter.shadow.mirrored if item.kind == "naloxone"] == stamps
    assert [item["executed_minute"] for item in encounter.shadow.held] == stamps
    assert len({item["shadow_order_id"] for item in encounter.shadow.held}) == 3
    assert all("a repeat dose adds nothing" in gap["why"] for gap in encounter.shadow.gaps)


def test_p3s_167d_release_during_different_information_activities():
    """Dos retenidas sobre estudios distintos, liberadas en actividades distintas; y la misma, con la actividad
    troceada de cualquier manera, da el mismo minuto y la misma corrida."""
    text_blood, text_fluid = HELD[GI]["blood"][0], HELD[GI]["fluid"][0]
    encounter = _run(GI, (text_blood, text_fluid, 6, 3, 5))
    held = {item["kind"]: item for item in encounter.shadow.held}
    assert held["blood"]["executed_minute"] == _released_minute(encounter, "lactate")
    assert held["fluid"]["executed_minute"] == _released_minute(encounter, "basic_labs")
    assert held["blood"]["executed_minute"] < held["fluid"]["executed_minute"] and encounter.shadow.gaps == []
    reference = None
    chooser = random.Random(167)
    for _ in range(8):
        cuts = sorted(chooser.sample(range(1, 14), chooser.randint(0, 4))) + [14]
        chunks = [b - a for a, b in zip([0] + cuts, cuts)]
        played = _run(OPIOID, (HELD_NALOXONE,) + tuple(chunks))
        assert _engine_stamp(played, "naloxone") == [5] == [
            item.minute for item in played.shadow.mirrored if item.kind == "naloxone"], chunks
        reference = reference or played.shadow.runner.digests()
        assert played.shadow.runner.digests() == reference and played.shadow.gaps == [], chunks


def test_p3s_167d_unsupported_executed_action(traces):
    encounter = _run(OPIOID, (UNSUPPORTED_HELD, 9))
    session, trace = encounter.shadow, _latest(encounter)
    assert [(item["state"], item["executed_minute"]) for item in session.held] == [(rs.ORDER_EXECUTED, 5)]
    assert [(r["disposition"], r["order_minute"], r["effective_minute"]) for r in _rows(trace, "bag_mask")] == [
        (fam.DECLARED_GAP, 5, None)]
    assert fam.UNSUPPORTED_ACTION in trace["status"]["codes"]
    untreated = _run(OPIOID, ("Order a lactate.", 9))
    assert session.runner.digests() == untreated.shadow.runner.digests()        # ningun efecto fingido


def test_p3s_167d_an_interval_nobody_observed_is_still_declared(traces):
    """Lo que quedo del hallazgo F1 del ciclo anterior: si alguien deja pasar el tiempo SIN el ayudante de la
    pagina, la orden que el motor ejecuto sigue sin reflejarse y se dice. Ya no es el camino de la pagina."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(OPIOID)
        encounter.order(HELD_NALOXONE)
        family_engine.advance_clinical_time(encounter.state, 6)               # sin observar
        encounter.order("Reassess in 2 minutes.")
    session, trace = encounter.shadow, _latest(encounter)
    assert session.held[0]["state"] == rs.ORDER_RELEASED and session.held[0]["why"] == rs.UNOBSERVED_RELEASE
    assert [row["disposition"] for row in _rows(trace, "naloxone")] == [fam.NOT_MIRRORED]
    assert trace["status"]["state"] == fam.COMPLETE_WITH_UNSUPPORTED_ACTIONS


# -- P3-168: cierre de la sincronizacion --------------------------------------------------------------------------------

#: "espera los resultados": retenida sobre CUALQUIER resultado pendiente; sin nada pendiente corre en su mismo turno.
ANY_PENDING_HELD = {GI: "Wait for the results, then give 500 mL of normal saline.",
                    OPIOID: "Wait for the results, then give naloxone 0.4 mg IV."}
SYNC_POOL = {
    GI: POOL[GI] + tuple(text for text, _minute in HELD[GI].values()) + (NEVER_RELEASED[GI], ANY_PENDING_HELD[GI],
                                                                         2, 4, 7, 11),
    OPIOID: POOL[OPIOID] + (HELD_NALOXONE, UNSUPPORTED_HELD, NEVER_RELEASED[OPIOID], ANY_PENDING_HELD[OPIOID],
                            2, 4, 7, 11),
}


@pytest.mark.parametrize("case", (GI, OPIOID))
def test_p3s_168d_two_identical_releases_in_zero_minute_turns_of_one_minute_are_two(case):
    """R-F3 de la revision independiente (defecto anterior a este ciclo): dos ordenes identicas, cada una
    liberada al final de su propio turno de cero minutos, en el mismo minuto. Son dos ejecuciones."""
    text = ANY_PENDING_HELD[case]
    encounter = _run(case, (text, text))
    session = encounter.shadow
    assert [(item["after_result"], item["state"], item["executed_minute"]) for item in session.held] == [
        (rs.ANY_PENDING, rs.ORDER_EXECUTED, 0)] * 2
    kind = session.held[0]["kind"]
    assert [item.minute for item in session.mirrored if item.kind == kind] == [0, 0]
    assert len({item["shadow_order_id"] for item in session.held}) == 2
    assert not [gap for gap in session.gaps if "held order" in gap["why"]]
    if case == OPIOID:
        assert _engine_stamp(encounter, "naloxone") == [0, 0]
    # y la MISMA jugada mirada otra vez sigue sin duplicar nada
    again = _run(case, (text, 3), again=2)
    assert [item.minute for item in again.shadow.mirrored if item.kind == kind] == [0]


def _sync_sequence(case, seed) -> tuple:
    chooser = random.Random(f"sync:{case}:{seed}")
    steps = [chooser.choice(SYNC_POOL[case]) for _ in range(chooser.randint(4, 7))]
    held = [item for item in SYNC_POOL[case] if isinstance(item, str) and "wait for the result" in item]
    steps.insert(chooser.randrange(len(steps)), chooser.choice(held))        # siempre hay una orden retenida
    steps.append(chooser.choice((6, 9, 12)))                                 # y una actividad que puede liberarla
    return tuple(steps) + ("Reassess in 5 minutes.",)


def test_p3s_168a_the_sequences_are_bounded_repeatable_and_mix_every_kind_of_execution():
    kinds = set()
    for case in (GI, OPIOID):
        sequences = [_sync_sequence(case, seed) for seed in SEEDS]
        assert sequences == [_sync_sequence(case, seed) for seed in SEEDS]
        assert all(7 <= len(steps) <= 10 and set(steps) <= set(SYNC_POOL[case]) | {6, 9, 12} for steps in sequences)
        for steps in sequences:
            assert any(isinstance(step, int) for step in steps)
            assert any(isinstance(step, str) and "wait for the result" in step for step in steps)
    for case in (GI, OPIOID):
        for seed in SEEDS:
            played = _run(case, _sync_sequence(case, seed))
            for item in played.shadow.held:
                kinds.add(item["state"])
            kinds.update("ORDINARY" for item in played.shadow.mirrored if "-held" not in item.order_id)
    assert {"ORDINARY", rs.ORDER_EXECUTED, rs.ORDER_HELD} <= kinds
    assert SYNC["randomized"]["seeds"] == SEEDS and SYNC["randomized"]["families"] == 2


@pytest.mark.parametrize("again", (0, 1))
@pytest.mark.parametrize("case", (GI, OPIOID))
@pytest.mark.parametrize("seed", SEEDS)
def test_p3s_168b_every_executed_action_is_mirrored_once_and_no_unexecuted_one_touches_the_shadow(
        case, seed, again, traces):
    steps = _sync_sequence(case, seed)
    on, off = _run(case, steps, again=again), _run(case, steps, mode=None)
    # aislamiento exacto
    assert on.state == off.state and ev.authoritative(on) == ev.authoritative(off)
    assert ev.fates(on) == ev.fates(off) and on.minute == off.minute and on.arrested == off.arrested
    session = on.shadow
    assert [item for item in session.failures if item.where != "legacy_snapshot"] == [], session.failures
    assert session.runner.minutes_done == on.minute
    # ninguna liberacion sin reflejar: ni recibo sin orden, ni orden sin recibo, ni minuto sin establecer
    assert not [item for item in session.held if item["state"] in (rs.ORDER_RELEASED, rs.ORDER_CANCELLED)]
    assert not [gap for gap in session.gaps if "held order" in gap["why"] or gap["why"] == rs.UNOBSERVED_RELEASE]
    # cada orden retenida: o el motor la sigue teniendo, o corrio y se reflejo UNA vez en su minuto
    still = on.state["family_state"].get("deferred_orders") or []
    executed = [item for item in session.held if item["state"] == rs.ORDER_EXECUTED]
    assert len(session.held) - len(executed) == len(still)
    identities = [item.order_id for item in session.mirrored]
    assert len(identities) == len(set(identities))
    for item in executed:
        assert identities.count(item["shadow_order_id"]) == 1
        mirrored = next(m for m in session.mirrored if m.order_id == item["shadow_order_id"])
        assert mirrored.minute == item["executed_minute"] >= item["placed_minute"]
    for item in session.held:
        if item["state"] != rs.ORDER_EXECUTED:
            assert item["shadow_order_id"] is None and item["order_id"] not in identities
    # contra el sello del propio motor, donde lo hay
    if case == OPIOID:
        assert sorted(m.minute for m in session.mirrored if m.kind == "naloxone") == sorted(
            _engine_stamp(on, "naloxone"))
    # la traza: entera, coherente, y se reproduce
    trace = _latest(on)
    assert not [row for row in trace["actions"] if row["disposition"] == fam.NOT_MIRRORED]
    assert all(row["effective_minute"] is None or row["effective_minute"] == row["order_minute"] + 1
               for row in trace["actions"] if row["disposition"] in fam.MIRRORED_DISPOSITIONS)
    assert trace["status"]["state"] in (fam.COMPLETE, fam.COMPLETE_WITH_UNSUPPORTED_ACTIONS)
    assert store.verify(trace)["verified"] and (not on.minute or store.replay(trace)["reproduces"])


def test_p3s_168c_the_verdict_and_what_it_does_not_cover():
    assert SYNC["verdict"] == "LIVE_SHADOW_EXECUTION_SYNCHRONIZATION_COMPLETE"
    assert SYNC["covers"] and SYNC["does_not_cover"]
    assert set(SYNC["negative_controls"]) == {"remains HELD", "becomes TERMINAL_NOT_EXECUTABLE",
                                              "duplicate observation", "multiple identical studies",
                                              "release during different information activities",
                                              "unsupported executed action"}
    # ninguna pieza de fuera de la capa compartida cambio para esto
    families = (ROOT / "runtime_shadow_families.py").read_text(encoding="utf-8")
    assert "observe_time" not in families and "advance_clinical_time" not in families
