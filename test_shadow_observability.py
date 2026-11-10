"""Ciclo de observabilidad de la sombra en vivo (2026-11-10): P3-147 a P3-150 y P3-153.

- P3-147: UNA regla compartida de cuando un estado puede mapearse como llegada (ARRIVAL_ELIGIBLE), y el ciclo
  de vida de la sesion que la usa; el defecto del turno de cero minutos, reproducido en GI y en opioide;
- P3-148: el almacen de trazas de investigacion de la sombra: persistir, recargar y reproducir, testigo por
  testigo, y un testigo fallido que sigue fallido;
- P3-149: el observador docente, de solo lectura, fuera de la pagina del encuentro;
- P3-150: los siete codigos de fallo, ninguna accion ejecutada que desaparezca y ningun exito sin calificar;
- P3-153: los ataques y las secuencias aleatorias acotadas, y el aislamiento con la sombra y el almacen
  encendidos y apagados.

Los encuentros se juegan con ``pilot_acceptance.Encounter``: el camino de ordenes de la pagina sin Streamlit,
con el motor heredado como unica autoridad. Nada de lo que aqui se mide se ajusta a las curvas de ese motor.
No hay fisiologia nueva: el nucleo comun no cambia en este ciclo.

Registro: shadow_observability_record. Etiquetas ``p3o``.
"""
import ast
import copy
import json
import random
from pathlib import Path

import pytest

import pilot_acceptance as acceptance
import runtime_authority as ra
import runtime_authority_store as authority_store
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam
import runtime_shadow_observer as obs
import runtime_shadow_store as store
import shadow_observability_record as rec
from clinical_core import legacy_adapter

ROOT = Path(__file__).resolve().parent
GI, OPIOID = "gi_bleed_57m", "opioid_35m"
LIVE_CASES = (GI, "gi_bleed_72f", OPIOID, "opioid_67f")
#: Una orden que el motor ejecuta sin mover el reloj, por familia: la que destapaba el defecto.
ZERO_MINUTE = {GI: "Place an IV line.", OPIOID: "Give midazolam 2 mg IV."}
OXYGEN = "Give oxygen 15 L/min by non-rebreather mask."
NALOXONE = "Give naloxone 0.4 mg IV."
WITNESSES = tuple(fam.TRANSMISSION_WITNESSES)
RUNS = (store.SESSION_RUN_NAME,) + WITNESSES


# -- el arnes -----------------------------------------------------------------------------------------------------

@pytest.fixture
def traces(monkeypatch, tmp_path):
    """Un almacen de trazas nombrado por el entorno del proceso, fuera del repositorio."""
    directory = tmp_path / "traces"
    monkeypatch.setenv(store.STORE_FLAG, str(directory))
    return directory


def _play(case, turns=(), until=None, mode=rs.MODE_SHADOW_COMPARE):
    with ev.shadow(mode):
        encounter = acceptance.Encounter(case)
        for text in turns:
            encounter.order(text)
        if until is not None:
            encounter.wait_until(until)
    return encounter


def _old_is_for(session, state) -> bool:
    """La regla que la sesion tenia ANTES de P3-147, copiada en su logica. Solo para mostrar lo que hacia."""
    if str(legacy_adapter.engine_case_id(dict(state))) != session.case_id:
        return False
    minute = int(dict(state).get("sim_time", 0) or 0)
    seen = 0 if session.runner is None else int(session.runner.minutes_done)
    if minute < seen:
        return False
    return not (minute == 0 and (seen > 0 or session.turns > 0))


class Page:
    """Las tres sentencias del ayudante de sesion de la pagina, sobre un objeto que hace de su sesion.

    ``test_p3o_147b`` fija que esas tres sentencias siguen siendo las de ``app.py``.
    """

    def __init__(self, rule=None, generation=None):
        self.session, self.opened, self.rule, self.generation = None, [], rule, generation

    def session_for(self, state):
        session, generation = self.session, self.generation
        if session is not None and not (self.rule(session, state) if self.rule
                                        else session.is_for(state, generation)):
            session = None
        if session is None:
            session = rs.ShadowSession.start(state, generation=generation)
            self.session = session
            self.opened.append(session)
        return session


def _play_on_page(case, turns, rule=None):
    """El encuentro, con la sesion pedida al ayudante de la pagina antes de CADA turno, como hace la pagina."""
    page = Page(rule)
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(case)
        page.session = encounter.shadow
        page.opened.append(encounter.shadow)
        for text in turns:
            encounter.shadow = page.session_for(encounter.state)
            encounter.order(text)
    return encounter, page


def _codes(session) -> list:
    return [fam.status_code(item.where, item.exception) for item in session.failures]


def _latest(encounter) -> dict:
    """La traza que ESTA sesion guardo en su ultimo turno, por su identidad."""
    return store.load(encounter.shadow.persistence["trace_id"])


def _resealed(trace: dict) -> dict:
    """Una traza alterada a proposito y con su digesto RECALCULADO: lo que haria quien sabe recalcularlo."""
    body = copy.deepcopy(trace)
    body["trace_digest"] = store.trace_digest(body)
    return body


# -- P3-147: la regla compartida de llegada y el ciclo de vida de la sesion ---------------------------------------

def test_p3o_147a_one_shared_rule_says_when_a_state_is_an_arrival():
    assert rs.ARRIVAL_CONDITIONS == rec.LIFECYCLE["conditions"] and len(rs.ARRIVAL_CONDITIONS) == 5
    for case in LIVE_CASES:
        encounter = _play(case)
        found = rs.arrival_eligibility(encounter.state)
        assert found["eligible"] is True and found["differences"] == [], case
        assert tuple(found["conditions"]) == rs.ARRIVAL_CONDITIONS and all(found["conditions"].values())
        assert encounter.shadow.eligibility == found and encounter.shadow.left_arrival is False
        assert encounter.shadow.failures == [] and encounter.shadow.runner.anchors is not None
    # una sola implementacion: la capa de familias no lleva regla de ciclo de vida propia, la consulta
    families = (ROOT / "runtime_shadow_families.py").read_text(encoding="utf-8")
    assert families.count("rs.arrival_eligibility(") == 1 and "def is_for" not in families
    assert "left_arrival" not in families
    # y el reloj es UNA condicion de cinco: una llegada con el reloj en cero y algo hecho no es elegible
    touched = _play(GI, (ZERO_MINUTE[GI],))
    after = rs.arrival_eligibility(touched.state)
    assert touched.minute == 0 and after["conditions"]["clock_at_arrival"] is True and after["eligible"] is False


def test_p3o_147b_the_page_helper_is_the_three_statements_this_file_emulates():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    helper = app[app.index("def _runtime_shadow_session():"):app.index("def _runtime_authority_site():")]
    for statement in ('session = st.session_state.get("phase3_shadow")',
                      'generation = st.session_state.get("_attempt_id")',
                      "if session is not None and not session.is_for(st.session_state.state, generation):",
                      "session = runtime_shadow.ShadowSession.start(st.session_state.state, generation=generation)"):
        assert helper.count(statement) == 1, statement
    assert "arrival" not in helper.replace("at the arrival", "")       # la pagina no decide la regla: la pregunta


@pytest.mark.parametrize("case", (GI, OPIOID))
def test_p3o_147c_the_zero_minute_bug_is_reproduced_and_it_is_gone(case):
    order = ZERO_MINUTE[case]
    assert order in rec.LIFECYCLE["old_bug"]["zero_minute_orders"][{GI: "gi_bleed", OPIOID: "opioid"}[case]]
    # ANTES: con la regla vieja, tras un turno que no mueve el reloj la pagina abria OTRA sesion sobre el
    # paciente ya tratado. Con la regla vieja y el arranque viejo eso era una llegada falsa; hoy el arranque
    # al menos lo rechaza, y aun asi la accion del primer turno se pierde del espejo.
    encounter, page = _play_on_page(case, (order, "Reassess in 5 minutes."), rule=_old_is_for)
    assert len(page.opened) == 2 and page.opened[0] is not page.opened[1]
    assert [item.kind for item in page.opened[0].mirrored] and page.opened[1].mirrored == []
    assert page.opened[1].runner is None and _codes(page.opened[1]) == [fam.ARRIVAL_REJECTED]
    # AHORA: una sola sesion para todo el encuentro, con la accion del turno de cero minutos en el espejo
    encounter, page = _play_on_page(case, (order, "Reassess in 5 minutes."))
    session = encounter.shadow
    assert len(page.opened) == 1 and session is page.opened[0]
    assert encounter.minute == 5 and session.runner.minutes_done == 5 and session.turns == 2
    assert session.left_arrival is True and session.failures == []
    assert len(session.mirrored) == 2 and session.mirrored[0].minute == 0
    # y es la misma corrida que la del arnes, que conserva su sesion de por vida
    plain = _play(case, (order, "Reassess in 5 minutes."))
    assert session.runner.digests() == plain.shadow.runner.digests()
    assert [item.kind for item in session.mirrored] == [item.kind for item in plain.shadow.mirrored]


@pytest.mark.parametrize("case", (GI, OPIOID))
def test_p3o_147d_a_zero_minute_turn_does_not_make_a_new_arrival_and_a_new_attempt_does(case):
    first = _play(case, (ZERO_MINUTE[case],))
    session = first.shadow
    assert first.minute == 0 and session.is_for(first.state) is True and session.left_arrival is True
    assert _old_is_for(session, first.state) is False                     # el defecto, en una linea
    # un segundo intento del mismo caso SI es otro encuentro: llegada intacta despues de haberla dejado
    second = _play(case)
    assert session.is_for(second.state) is False
    assert second.shadow is not session and second.shadow.encounter_id == session.encounter_id
    assert second.shadow.turns == 0 and second.shadow.mirrored == [] and second.shadow.failures == []
    # el reloj hacia atras y otro caso tampoco son este encuentro
    later = _play(case, until=6)
    assert later.shadow.is_for(first.state) is False
    other = _play("gi_bleed_72f" if case == GI else "opioid_67f")
    assert session.is_for(other.state) is False


NEGATIVE_CONTROLS = ("already_treated", "time_advanced", "altered_arrival_vitals", "engine_state_touched",
                     "administration_on_record")


def _control(case, name) -> dict:
    if name == "already_treated":
        return _play(case, (ZERO_MINUTE[case],)).state
    if name == "time_advanced":
        return _play(case, until=4).state
    state = copy.deepcopy(_play(case).state)
    if name in ("engine_state_touched", "administration_on_record"):
        # el estado del motor ya inicializado, como queda tras su primer turno, y todavia intacto
        state = copy.deepcopy(legacy_adapter._initialized(state))
        assert rs.arrival_eligibility(state)["eligible"] is True
    if name == "altered_arrival_vitals":
        state["observable"]["spo2"] = state["observable"]["spo2"] - 3
    elif name == "engine_state_touched":
        state["family_state"]["oxygen_fio2"] = 0.4
    elif name == "administration_on_record":
        state.setdefault("treatments", {}).setdefault("administered_medications", []).append({"name": "x"})
    return state


@pytest.mark.parametrize("case", (GI, OPIOID))
@pytest.mark.parametrize("control", NEGATIVE_CONTROLS)
def test_p3o_147e_a_state_that_is_not_an_untouched_arrival_is_refused_visibly(case, control):
    state = _control(case, control)
    untouched = copy.deepcopy(state)
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        session = rs.ShadowSession.start(state)
    assert state == untouched                                             # leer no cambia nada
    assert session is not None and session.runner is None and session.ensemble is None
    assert session.eligibility["eligible"] is False and session.left_arrival is True
    assert [item.exception for item in session.failures] == [rs.ARRIVAL_REJECTED]
    assert _codes(session) == [fam.ARRIVAL_REJECTED] and "live" in session.failures[0].message
    expected = {"already_treated": "engine_state_is_a_fresh_arrival", "time_advanced": "clock_at_arrival",
                "altered_arrival_vitals": "monitor_is_the_authored_arrival",
                "engine_state_touched": "engine_state_is_a_fresh_arrival",
                "administration_on_record": "nothing_administered"}[control]
    assert session.eligibility["conditions"][expected] is False
    # explicito y sin autoridad: no hay minuto, ni artefacto, ni nada que comparar
    record = session.record()
    assert session.minutes == [] and record["replay_input"] is None and record["runtime_authority"] == "legacy"
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    # y observar un turno sobre una sesion rechazada no la resucita
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        session.observe(copy.deepcopy(state), copy.deepcopy(state), None, {"executed": True}, [], "s")
    assert session.runner is None and session.minutes == [] and session.mirrored == []


def test_p3o_147f_an_incompatible_family_and_an_unsupported_variant_are_not_mapped():
    arrival = _play(GI).state
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        for family in ("acs", "pulmonary_edema", "asthma", "pulmonary_embolism", ""):
            assert rs.ShadowSession.start({**copy.deepcopy(arrival), "engine_family": family}) is None, family
        relabelled = rs.ShadowSession.start({**copy.deepcopy(arrival), "engine_family": "opioid"})
        variant = copy.deepcopy(arrival)
        variant["encounter_spec"]["variant_id"] = "gi_bleed_99x"
        unsupported = rs.ShadowSession.start(variant)
        opioid = copy.deepcopy(_play(OPIOID).state)
        opioid["encounter_spec"]["variant_id"] = "opioid_67f"            # otro caso certificado, otro paciente
        another = rs.ShadowSession.start(opioid)
    for session in (relabelled, unsupported):
        assert session.runner is None and [item.exception for item in session.failures] == ["NoCertifiedAdapter"]
        assert _codes(session) == [fam.ARRIVAL_REJECTED] and session.minutes == []
    assert another.runner is not None and another.runner.anchors is None and another.minutes == []
    assert [item.exception for item in another.failures] == ["ArrivalIdentityError"]
    assert _codes(another) == [fam.ARRIVAL_REJECTED]


@pytest.mark.parametrize("case", (GI, OPIOID))
def test_p3o_147g_a_prior_shadow_state_is_never_reopened_as_a_fresh_arrival(case):
    encounter, page = _play_on_page(case, (ZERO_MINUTE[case], "Reassess in 5 minutes."))
    old = page.session
    kept = (old.runner.digests(), len(old.mirrored), old.turns)
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        fresh = acceptance.Encounter(case)
        new = page.session_for(fresh.state)                    # el segundo intento llega al mismo ayudante
    assert new is not old and len(page.opened) == 2
    assert new.runner.minutes_done == 0 and new.mirrored == [] and new.turns == 0 and new.left_arrival is False
    assert (old.runner.digests(), len(old.mirrored), old.turns) == kept   # la sesion vieja no se toca
    # y no hay por donde volver a abrir una sesion desde una traza guardada: el almacen solo lee y reproduce
    assert not [name for name in dir(store) if "resume" in name or "reopen" in name or "restore" in name]


def test_p3o_147h_the_declared_residual_is_what_the_code_does():
    """Un turno sin tiempo y SIN huella en el paciente no marca el encuentro como salido de la llegada."""
    encounter = _play(GI, ("Order a type and crossmatch.",))
    assert encounter.minute == 0 and rs.arrival_eligibility(encounter.state)["eligible"] is True
    assert encounter.shadow.left_arrival is False and [m.kind for m in encounter.shadow.mirrored] == ["diagnostic"]
    assert "leaves no trace" in rec.LIFECYCLE["residual"]
    # la fisiologia de ambos intentos es la misma llegada: nada de la corrida puede mezclarse
    assert encounter.shadow.runner.minutes_done == 0 and encounter.shadow.runner.digests() == ()


def test_p3o_147i_the_recorded_verdict_and_the_classification():
    assert rec.LIFECYCLE["verdict"] == "SHARED_LIVE_SHADOW_LIFECYCLE_VALIDATED"
    assert rec.LIFECYCLE["families"] == rs.LIVE_FAMILIES == ("gi_bleed", "opioid")
    assert rec.LIFECYCLE["opioid_identity_classification"] == "LIVE_SHADOW_ELIGIBILITY_GUARD"
    assert "LIVE_SHADOW_ELIGIBILITY_GUARD" in fam.OpioidAdapter.arrival_identity.__doc__
    assert set(rec.LIFECYCLE["old_bug"]["reproduced_for"]) == set(rs.LIVE_FAMILIES)
    assert len(rec.LIFECYCLE["negative_controls"]) == 6


# -- P3-148: el almacen de trazas de investigacion de la sombra ---------------------------------------------------

def test_p3o_148a_the_store_is_off_unless_a_process_environment_names_a_directory(monkeypatch, tmp_path):
    monkeypatch.delenv(store.STORE_FLAG, raising=False)
    encounter = _play(GI, ("Give 1 L of normal saline.",))
    assert store.configured() is False and store.root() is None and store.refused_root() == ""
    assert encounter.shadow.persistence is None and store.persist_session(encounter.shadow) is None
    assert store.records() == [] and store.paths() == [] and encounter.shadow.failures == []
    assert store.persist(store.trace_of(encounter.shadow))["why"] == store.NOT_CONFIGURED
    # un directorio relativo o dentro del repositorio se rechaza, y el rechazo SE VE una sola vez
    for named in ("traces", str(ROOT / "traces"), str(ROOT)):
        monkeypatch.setenv(store.STORE_FLAG, named)
        assert store.root() is None and store.refused_root() == store.OUTSIDE_THE_REPOSITORY
        refused = _play(GI, ("Give 1 L of normal saline.", "Reassess in 5 minutes."))
        assert refused.shadow.persistence["stored"] is False
        assert refused.shadow.persistence["why"] == store.OUTSIDE_THE_REPOSITORY
        assert [(item.where, item.exception) for item in refused.shadow.failures] == [("persist",
                                                                                      rs.PERSISTENCE_FAILED)]
        assert _codes(refused.shadow) == [fam.TRACE_PERSISTENCE_FAILED]
        # la corrida no se entera: los primeros 20 minutos son los del encuentro sin almacen nombrado
        assert refused.shadow.runner.minutes_done == 25
        assert refused.shadow.runner.digests()[:20] == encounter.shadow.runner.digests()
    assert not (ROOT / "traces").exists()
    # y un secreto de despliegue no puede nombrar el almacen, como no puede encender la sombra
    monkeypatch.setenv(store.STORE_FLAG, str(tmp_path / "t"))
    assert store.configured() is True
    monkeypatch.setattr(rs, "_named_in_secrets", lambda name: name == store.STORE_FLAG)
    assert store.configured() is False and store.refused_root() == store.FROM_SECRETS
    assert not (tmp_path / "t").exists()


def test_p3o_148b_gi_persists_reloads_and_replays_exactly(traces):
    encounter = _play(GI, ("Place an IV line.", "Give 1 L of normal saline.", OXYGEN,
                           "Consult gastroenterology."), until=40)
    session = encounter.shadow
    assert session.persistence["stored"] is True and session.failures == []
    rows = store.records(encounter_id=session.encounter_id)
    assert [row["turns"] for row in rows] == list(range(1, session.turns + 1))     # un registro por turno
    assert rows[-1]["session_minutes"] == 40 == encounter.minute and rows[-1]["runs"] == ["SESSION_RUN"]
    trace = store.load(rows[-1]["trace_id"])
    # cada registro nombra el que su propia sesion guardo antes: eso une los registros de un intento
    assert [row["previous_trace_id"] for row in rows] == [None] + [row["trace_id"] for row in rows[:-1]]
    assert [row["head"] for row in rows] == [False] * (len(rows) - 1) + [True]
    assert all(row["verified"] and not row["unreadable"] for row in rows)
    assert trace == _latest(encounter) == json.loads(json.dumps(
        store.trace_of(session, previous=rows[-2]["trace_id"]), default=str))
    # el contenido que el paquete pide, todo
    assert (trace["family"], trace["case_id"]) == ("gi_bleed", GI)
    assert trace["authority"] == "NONAUTHORITATIVE_SHADOW" and trace["use"] == "DEVELOPMENT_ONLY"
    assert trace["resident_visible"] is False and trace["runtime_authority"] == "legacy"
    assert trace["common_core_runtime_authority"] is False and trace["selected_witness"] is None
    assert (trace["authority"], trace["use"]) == rec.TRACE_STORE["provenance_labels"]
    lineage = trace["lineage"]
    assert lineage["core_version"] == "PHASE2_AMENDMENT_1" and lineage["certified"] is True
    assert lineage["core_digest"] == "10b45ce2967ea55afccb35291afb5bb1f7f1b01eb4a253e6a0736c02a5878635"
    assert lineage["phase2_digest"] == "22b90a6f7f38929cc5c18aa2000579155b4d9109198e35e29ad3991e81d6ce6a"
    assert lineage["phase3_layer_digest"] == rs.layer_digest()
    assert trace["arrival"]["fingerprint"] == session.encounter_id and trace["arrival"]["eligible"] is True
    assert [(row["order_minute"], row["effective_minute"], row["kind"], row["disposition"])
            for row in trace["actions"]] == [
        (0, None, "vascular_access", fam.DECLARED_GAP), (0, 1, "fluid", fam.BUILT), (20, 21, "oxygen", fam.BUILT),
        (21, None, "consult", fam.SKIPPED_NO_PHYSIOLOGY), (21, None, "reassessment", fam.SKIPPED_NO_PHYSIOLOGY)]
    run = trace["runs"]["SESSION_RUN"]
    assert run["role"] == store.SESSION_RUN and run["witness"] is None and run["parameter"] is None
    assert [row["minute"] for row in run["minutes"]] == list(range(1, 41)) and run["last_valid_minute"] == 40
    assert tuple(row["state_digest"] for row in run["minutes"]) == session.runner.digests()
    for name in ("V", "hb", "fio2", "map", "spo2", "delivery_rel", "sympathetic_drive"):
        assert isinstance(run["minutes"][-1]["channels"][name], float), name
    fio2 = {row["minute"]: row["channels"]["fio2"] for row in run["minutes"]}
    assert fio2[20] == 0.21 < fio2[21] == fio2[40]                # pedido en el 20, en el estado del 21
    assert trace["status"]["state"] == fam.COMPLETE_WITH_UNSUPPORTED_ACTIONS
    # recargar y reproducir: exacto
    checked = store.verify(trace)
    assert checked["verified"] and checked["lineage_matches"] and checked["missing_witnesses"] == []
    replayed = store.replay(trace)
    assert replayed["replayed"] and replayed["reproduces"] and replayed["refused"] is None
    assert replayed["runs"] == {"SESSION_RUN": {"reproduces": True, "minutes": 40, "recorded": 40,
                                                "first_mismatch": None, "why": ""}}
    # guardar lo mismo otra vez no escribe nada nuevo
    before = sorted(path.name for path in traces.iterdir())
    again = store.persist(trace)
    assert again["stored"] is True and again["idempotent"] is True
    assert sorted(path.name for path in traces.iterdir()) == before


def test_p3o_148c_the_opioid_persists_its_run_and_three_witnesses_apart(traces):
    encounter = _play(OPIOID, (OXYGEN, NALOXONE), until=30)
    session, trace = encounter.shadow, _latest(encounter)
    assert tuple(sorted(trace["runs"])) == tuple(sorted(RUNS)) and trace["expected_witnesses"] == list(WITNESSES)
    assert trace["selected_witness"] is None and "none is selected" in trace["witness_policy"]
    assert trace["region"]["classification"] == "CONDITIONAL_DEVELOPMENT_REGION"
    assert trace["region"]["active_causal_region"]["up_to"] == 0.060621
    values = {name: trace["runs"][name]["parameter"]["value"] for name in WITNESSES}
    assert values == dict(fam.TRANSMISSION_WITNESSES) == {"LOW": 0.015, "CENTER_REFERENCE": 0.03, "HIGH": 0.06}
    assert values == {name: trace["runs"][name]["parameter"]["declared"] for name in WITNESSES}
    assert trace["runs"]["SESSION_RUN"]["parameter"] is None
    for name in WITNESSES:
        run, live = trace["runs"][name], session.ensemble.runners[name]
        assert run["role"] == store.WITNESS_RUN == "DEVELOPMENT_TEST_WITNESS" and run["witness"] == name
        assert run["parameter"]["name"] == fam.TRANSMISSION_FIELD and run["failed"] is False
        assert tuple(row["state_digest"] for row in run["minutes"]) == live.digests() and len(run["minutes"]) == 30
        assert name.lower() in run["snapshot"]["id"]
    # tres trayectorias DISTINTAS, cada una entera, y ninguna es el promedio de las otras
    spo2 = {name: [row["channels"]["spo2"] for row in trace["runs"][name]["minutes"]] for name in WITNESSES}
    paco2 = {name: [row["channels"]["paco2"] for row in trace["runs"][name]["minutes"]] for name in WITNESSES}
    assert spo2["LOW"] != spo2["CENTER_REFERENCE"] != spo2["HIGH"] and spo2["LOW"] != spo2["HIGH"]
    mean = [(a + b) / 2 for a, b in zip(spo2["LOW"], spo2["HIGH"])]
    assert all(mean != spo2[name] for name in WITNESSES)
    assert "mean" not in json.dumps(trace) and "average" not in json.dumps(trace).replace("averaged", "")
    assert paco2["LOW"] == paco2["CENTER_REFERENCE"] == paco2["HIGH"]            # el testigo no toca la ventilacion
    for name in ("central_availability", "respiratory_rate", "ventilation", "paco2", "spo2", "delivery_rel"):
        assert isinstance(trace["runs"]["HIGH"]["minutes"][-1]["channels"][name], float), name
    assert [(row["order_minute"], row["effective_minute"], row["kind"], row["disposition"])
            for row in trace["actions"]][:2] == [(0, 1, "oxygen", fam.BUILT), (1, 2, "naloxone", fam.BUILT)]
    assert trace["status"] == {"state": fam.COMPLETE, "qualified": False, "codes": [], "items": [], "counts": {}}
    replayed = store.replay(trace)
    assert replayed["reproduces"] and set(replayed["runs"]) == set(RUNS)
    assert all(row == {"reproduces": True, "minutes": 30, "recorded": 30, "first_mismatch": None, "why": ""}
               for row in replayed["runs"].values())


def _break_witness(encounter, name="HIGH"):
    """Un testigo que deja de poder correr a mitad del encuentro, por algo que la corrida no preve."""
    def broken(*args, **kwargs):
        raise RuntimeError("the witness cannot run")
    encounter.shadow.ensemble.runners[name].advance = broken


def _with_failed_witness():
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(OPIOID)
        encounter.order(OXYGEN)
        _break_witness(encounter)
        encounter.order(NALOXONE)
        encounter.wait_until(12)
    return encounter


def test_p3o_148d_a_failed_witness_stays_failed_at_its_last_valid_minute(traces):
    encounter = _with_failed_witness()
    session, trace = encounter.shadow, _latest(encounter)
    assert session.runner.minutes_done == 12
    assert {name: runner.minutes_done for name, runner in session.ensemble.runners.items()} == {
        "LOW": 12, "CENTER_REFERENCE": 12, "HIGH": 1}                    # los otros testigos SIGUEN (P3-150)
    assert {item.where for item in session.failures} == {"ensemble:HIGH:advance"}
    high = trace["runs"]["HIGH"]
    assert high["failed"] is True and high["last_valid_minute"] == 1 and len(high["minutes"]) == 1
    assert high["failures"] and high["failures"][0]["exception"] == "RuntimeError"
    assert [trace["runs"][name]["failed"] for name in ("SESSION_RUN", "LOW", "CENTER_REFERENCE")] == [False] * 3
    assert trace["status"]["state"] == fam.PARTIAL and trace["status"]["codes"] == [fam.WITNESS_FAILED]
    # nada inventado despues del fallo: ni en la traza ni en el replay
    replayed = store.replay(trace)
    assert replayed["reproduces"] is True and replayed["runs"]["HIGH"]["minutes"] == 1 == \
        replayed["runs"]["HIGH"]["recorded"]
    assert replayed["runs"]["LOW"]["minutes"] == 12
    shown = obs.view(trace, replay=replayed)
    assert shown["status"]["state"] == fam.PARTIAL and shown["status"]["qualified"] is True
    assert [(run["name"], run["failed"], run["last_valid_minute"]) for run in shown["runs"]][-1] == ("HIGH", True, 1)
    # y el dibujo tampoco lo alarga: el testigo fallido es un anillo en su ultimo minuto valido, con su rotulo
    # al lado; ni linea ni guia mas alla (la comprobacion visual de este ciclo encontro una guia que lo cruzaba)
    page = obs.render_html(shown)
    assert page.count("HIGH stopped at min 1") == len(shown["channels"]) and page.count("<circle") == len(
        shown["channels"])
    import re
    for figure in re.findall(r"<svg.*?</svg>", page, flags=re.S):
        ring = re.search(r'<circle cx="([0-9.]+)"', figure)
        leaders = [float(x1) for x1 in re.findall(r'<line x1="([0-9.]+)" x2="294"', figure)]
        assert ring and leaders and all(x1 > float(ring.group(1)) + 100 for x1 in leaders), figure[:200]
        assert ">HIGH<" not in figure and "= HIGH" not in figure and "HIGH =" not in figure
    assert "<circle" not in obs.render_html(obs.view(_latest(_play(OPIOID, (NALOXONE,), until=5))))
    # una traza que alarga al testigo fallido NO se reproduce
    stretched = copy.deepcopy(trace)
    stretched["runs"]["HIGH"]["minutes"].append(copy.deepcopy(trace["runs"]["LOW"]["minutes"][1]))
    refused = store.replay(_resealed(stretched))                  # ni siquiera es coherente consigo misma
    assert refused["replayed"] is False and refused["refused"] == fam.REPLAY_MISMATCH
    assert "last valid minute" in refused["why"]
    stretched["runs"]["HIGH"]["last_valid_minute"] = 2             # alargada de forma coherente: el replay la caza
    again = store.replay(_resealed(stretched))
    assert again["replayed"] and again["runs"]["HIGH"]["reproduces"] is False
    assert again["runs"]["HIGH"]["minutes"] == 1 and again["runs"]["HIGH"]["recorded"] == 2


def test_p3o_148e_neither_store_accepts_the_others_records(traces, monkeypatch, tmp_path):
    trace = _latest(_play(GI, ("Give 1 L of normal saline.",)))
    monkeypatch.setenv(authority_store.STORE_FLAG, str(tmp_path / "authority"))
    refused = authority_store.persist(trace)
    assert refused["stored"] is False and refused["why"] == authority_store.NOT_AN_ARTIFACT
    assert not (tmp_path / "authority").exists() or not list((tmp_path / "authority").iterdir())
    for impostor in ({"artifact": "phase3_authority_experiment", "authority": "NONAUTHORITATIVE_SHADOW"},
                     {**trace, "artifact": "phase3_authority_experiment"}, {**trace, "resident_visible": True},
                     {**trace, "common_core_runtime_authority": True}, {**trace, "use": "PRODUCTION"}, {}, None):
        assert store.persist(impostor)["why"] == store.NOT_A_TRACE
    assert store.STORE_FLAG != authority_store.STORE_FLAG and traces != tmp_path / "authority"
    assert rec.TRACE_STORE["name"] == "SHADOW_RESEARCH_TRACE_STORE"


def test_p3o_148f_a_record_is_immutable_and_a_changed_trace_is_seen(traces):
    encounter = _play(OPIOID, (NALOXONE,), until=8)
    trace = _latest(encounter)
    path = Path(store.records(encounter_id=encounter.shadow.encounter_id)[-1]["path"])
    original = path.read_text(encoding="utf-8")
    # mismo contenido de entrada, otro contenido registrado: una colision que el almacen rechaza
    changed = copy.deepcopy(trace)
    changed["runs"]["LOW"]["minutes"][3]["channels"]["spo2"] += 1.0
    collided = store.persist(_resealed(changed))
    assert collided == {"stored": False, "kind": store.COLLISION, "why": store.COLLISION,
                        "trace_id": store.trace_id(trace), "path": str(path)}
    assert path.read_text(encoding="utf-8") == original
    # un cambio sin recalcular el digesto no pasa la verificacion, ni se guarda, ni se reproduce
    assert store.verify(changed)["why"] == store.DIGEST_MISMATCH
    assert store.persist(changed)["why"] == store.DIGEST_MISMATCH
    assert store.replay(changed)["replayed"] is False and store.replay(changed)["refused"] == fam.REPLAY_MISMATCH
    # y la identidad no lleva a nadie: ni participante, ni sesion de la pagina
    text = json.dumps(trace)
    for forbidden in ("resident", "user", "email", "participant", "account"):
        assert forbidden not in text.replace("resident_visible", ""), forbidden
    assert rec.TRACE_STORE["identity_carries_no_participant"] is True


def test_p3o_148g_the_same_encounter_is_the_same_record_and_another_is_another(traces):
    first = _play(OPIOID, (OXYGEN, NALOXONE), until=10)
    files = sorted(path.name for path in traces.iterdir())
    second = _play(OPIOID, (OXYGEN, NALOXONE), until=10)
    assert sorted(path.name for path in traces.iterdir()) == files                 # determinista: idempotente
    assert second.shadow.persistence["idempotent"] is True and second.shadow.failures == []
    assert store.trace_of(first.shadow)["trace_digest"] == store.trace_of(second.shadow)["trace_digest"]
    other = _play(OPIOID, (NALOXONE, OXYGEN), until=10)
    assert other.shadow.persistence["idempotent"] is False and other.shadow.failures == []
    assert other.shadow.persistence["trace_id"] != first.shadow.persistence["trace_id"]
    # la huella de la llegada es la misma para todo intento del caso: lo que los distingue es lo que hicieron
    assert other.shadow.encounter_id == first.shadow.encounter_id
    heads = store.heads(encounter_id=first.shadow.encounter_id)
    assert sorted(row["trace_id"] for row in heads) == sorted([first.shadow.persistence["trace_id"],
                                                               other.shadow.persistence["trace_id"]])
    assert all(row["session_minutes"] == 10 and row["turns"] == 3 for row in heads)
    # dos intentos que empiezan igual comparten su primer registro y se separan donde difieren
    branch = _play(OPIOID, (OXYGEN, "Reassess in 5 minutes."))
    assert len(store.heads(encounter_id=first.shadow.encounter_id)) == 3
    shared = [row for row in store.records() if row["turns"] == 1 and not row["head"]]
    assert len({row["trace_id"] for row in shared}) == 2 and branch.shadow.persistence["idempotent"] is False
    # un intento que termina en un turno sin accion ejecutada sigue siendo un intento: no lo tapa otro mas
    # largo que empezo igual (hallazgo R10 de la revision; antes se inferia por prefijo de acciones)
    ended = _play(OPIOID, (OXYGEN, "asdf qwerty"))
    longer = _play(OPIOID, (OXYGEN, "Reassess in 2 minutes.", NALOXONE))
    now = {row["trace_id"] for row in store.heads(encounter_id=first.shadow.encounter_id)}
    assert {ended.shadow.persistence["trace_id"], longer.shadow.persistence["trace_id"]} <= now and len(now) == 5


def _imports(path: Path) -> set:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)
             for alias in node.names}
    return names | {str(node.module).split(".")[0] for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom) and node.module}


def test_p3o_148h_nothing_resident_facing_reads_the_store_or_the_observer():
    faculty_only = {"runtime_shadow_store", "runtime_shadow_observer"}
    readers = {}
    for path in sorted(ROOT.rglob("*.py")):
        relative = path.relative_to(ROOT)
        if relative.parts[0] in {".venv", ".claude", "validation"} or path.name.startswith("test_"):
            continue
        text = path.read_text(encoding="utf-8")
        if faculty_only & _imports(path) or any(name in text for name in faculty_only):
            readers[relative.as_posix()] = sorted(faculty_only & _imports(path))
    # solo la capa: la sesion entrega su traza al almacen, y el observador lee el almacen. Nadie mas.
    assert readers == {"runtime_shadow.py": ["runtime_shadow_store"],
                       "runtime_shadow_observer.py": ["runtime_shadow_store"]}, readers
    for name in store.RESIDENT_READERS_FORBIDDEN:
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "shadow_store" not in text and "shadow_observer" not in text and store.STORE_FLAG not in text, name
    # el almacen escribe en un solo sitio, y el observador solo el informe que se le pide
    writers = [line.strip() for line in (ROOT / "runtime_shadow_store.py").read_text(encoding="utf-8").splitlines()
               if "write_text" in line or "mkdir" in line or "unlink" in line or "open(" in line]
    assert writers == ["directory.mkdir(parents=True, exist_ok=True)",
                       'pending.write_text(payload, encoding="utf-8")', "pending.unlink()"], writers
    source = (ROOT / "runtime_shadow_store.py").read_text(encoding="utf-8")
    assert source.count("os.replace(pending, path)") == 1 and source.count("os.replace(") == 1
    assert source.count("if path.resolve().parent != directory.resolve():") == 1
    session = (ROOT / "runtime_shadow.py").read_text(encoding="utf-8")
    # un turno de ordenes, una actividad de informacion (P3-167), o un rechazo al abrir: nadie mas persiste
    assert session.count("runtime_shadow_store") == 3 and session.count("self._persist()") == 2
    assert session.count("session._persist()") == 1


# -- P3-149: el observador docente --------------------------------------------------------------------------------

@pytest.fixture
def opioid_view(traces):
    encounter = _play(OPIOID, (OXYGEN, NALOXONE), until=30)
    trace = _latest(encounter)
    return encounter, trace, obs.view(trace, replay=store.replay(trace))


def test_p3o_149a_the_view_shows_what_a_faculty_reader_needs(opioid_view):
    encounter, trace, shown = opioid_view
    assert shown["identity"]["family"] == "opioid" and shown["identity"]["case_id"] == OPIOID
    assert shown["identity"]["session_minutes"] == 30 and shown["lineage"]["certified"] is True
    assert shown["provenance"] == {"authority": "NONAUTHORITATIVE_SHADOW", "use": "DEVELOPMENT_ONLY",
                                   "resident_visible": False, "runtime_authority": "legacy",
                                   "common_core_runtime_authority": False}
    assert shown["arrival"]["eligible"] is True
    assert [item["name"] for item in shown["arrival"]["conditions"]] == list(rs.ARRIVAL_CONDITIONS)
    assert all(item["holds"] and item["text"] != item["name"] for item in shown["arrival"]["conditions"])
    assert [(row["order_minute"], row["effective_minute"], row["kind"]) for row in shown["actions"]][:2] == [
        (0, 1, "oxygen"), (1, 2, "naloxone")]
    # cada corrida aparte, la de la sesion primero y los testigos en su orden declarado
    assert [run["name"] for run in shown["runs"]] == list(RUNS)
    assert shown["runs"][0]["label"] == "SESSION RUN"
    for run in shown["runs"][1:]:
        assert run["label"].startswith("DEVELOPMENT TEST WITNESS") and run["role"] == store.WITNESS_RUN
        assert run["replay"]["reproduces"] is True and run["failed"] is False and run["minutes"] == 30
    assert shown["selected_witness"] is None
    # los canales minimos del opioide, cada uno con las cuatro corridas
    assert tuple(channel["key"] for channel in shown["channels"]) == rec.OBSERVER["opioid_channels"]
    for channel in shown["channels"]:
        assert [series["run"] for series in channel["series"]] == list(RUNS), channel["key"]
        assert all(len(series["points"]) == 30 for series in channel["series"])
    assert shown["status"]["state"] == fam.COMPLETE and shown["replay"]["reproduces"] is True


def test_p3o_149b_the_envelope_is_a_derived_summary_and_no_witness_is_the_answer(opioid_view):
    _, trace, shown = opioid_view
    spo2 = next(channel for channel in shown["channels"] if channel["key"] == "spo2")
    envelope = spo2["envelope"]
    by_run = {series["run"]: dict(map(tuple, series["points"])) for series in spo2["series"]}
    assert envelope["witnesses"] == list(WITNESSES) and "SESSION_RUN" not in envelope["witnesses"]
    for index, minute in enumerate(envelope["minutes"]):
        values = [by_run[name][minute] for name in WITNESSES]
        assert envelope["min"][index] == min(values) and envelope["max"][index] == max(values)
    assert "derived summary" in envelope["label"] and "not a trajectory" in envelope["label"]
    # ninguna serie nueva: el resumen no es una corrida, y la vista no contiene una media
    assert [series["run"] for series in spo2["series"]] == list(RUNS)
    page = obs.render_html(shown)
    assert "DEVELOPMENT TEST WITNESS" in page and "development test witnesses" in page
    assert page.count("the answer") == 1 and "CENTER_REFERENCE is not the answer" in page
    assert "None is selected, preferred or averaged" in page
    for claim in ("recommended", "best estimate", "preferred value", "clinically validated", "ground truth is"):
        assert claim not in page.lower(), claim
    assert "NONAUTHORITATIVE SHADOW" in page and "DEVELOPMENT ONLY" in page and "not clinical validation" in page
    # un solo testigo no tiene resumen; GI no tiene testigos
    alone = copy.deepcopy(trace)
    for name in ("LOW", "HIGH"):
        del alone["runs"][name]
    assert all(channel["envelope"] is None for channel in obs.view(alone)["channels"])


def test_p3o_149c_the_observer_is_read_only(opioid_view, traces):
    encounter, trace, _ = opioid_view
    session = encounter.shadow
    kept_trace = copy.deepcopy(trace)
    kept_files = {path.name: path.read_bytes() for path in traces.iterdir()}
    kept_session = (session.runner.digests(), session.ensemble.digests(), len(session.mirrored), session.turns,
                    len(session.failures), copy.deepcopy(encounter.state))
    identifier = store.trace_id(trace)
    replayed = store.replay(trace)
    kept_replay = copy.deepcopy(replayed)
    assert obs.view(trace, replay=replayed) == obs.view(trace, replay=replayed)      # pura: misma entrada, misma vista
    assert replayed == kept_replay
    shown = obs.observe(identifier)
    assert shown == obs.view(trace, replay=replayed)
    page = obs.render_html(shown)
    assert page == obs.render_html(shown)
    assert obs.main(["--store", str(traces), "--list"]) == 0
    assert obs.main(["--store", str(traces), "--id", identifier]) == 0
    assert trace == kept_trace                                            # la traza que se le dio no cambia
    assert {path.name: path.read_bytes() for path in traces.iterdir()} == kept_files      # ni el almacen
    assert (session.runner.digests(), session.ensemble.digests(), len(session.mirrored), session.turns,
            len(session.failures), encounter.state) == kept_session       # ni la sesion, ni el paciente
    # la pagina no tiene con que actuar: ni formulario, ni boton, ni enlace, ni red, ni almacenamiento
    for control in ("<form", "<input", "<button", "<select", "<textarea", "<a ", "href=", "fetch(",
                    "XMLHttpRequest", "WebSocket", "localStorage", "sessionStorage", "http://", "https://",
                    "document.cookie", "innerHTML"):
        assert control not in page, control
    # el modulo no puede dar ordenes, tocar el estado ni elegir autoridad: no importa nada con que hacerlo
    imported = _imports(ROOT / "runtime_shadow_observer.py")
    assert imported == {"__future__", "argparse", "html", "json", "math", "copy", "pathlib", "typing",
                        "runtime_shadow_families", "runtime_shadow_store"}, sorted(imported)
    source = (ROOT / "runtime_shadow_observer.py").read_text(encoding="utf-8")
    assert source.count("write_text") == 1 and "store.persist" not in source and "persist_session" not in source
    for forbidden in ("ShadowSession", ".observe(", ".order(", "family_engine", "runtime_authority.",
                      "runtime_authority_store", "st.", "streamlit", "COMMON_CORE_RUNTIME_AUTHORITY =",
                      "os.environ"):
        assert forbidden not in source.replace("obs.observe(", ""), forbidden
    assert set(rec.OBSERVER["read_only"]) >= {"issues no order", "alters no state", "chooses no witness"}


def test_p3o_149d_a_report_is_never_written_inside_the_repository_and_data_is_escaped(opioid_view, tmp_path):
    _, trace, shown = opioid_view
    assert obs.write_report(shown, "report.html") == {"written": False,
                                                      "why": "the report path must be absolute"}
    inside = obs.write_report(shown, ROOT / "report.html")
    assert inside["written"] is False and "never written inside the repository" in inside["why"]
    assert not (ROOT / "report.html").exists()
    written = obs.write_report(shown, tmp_path / "out" / "report.html")
    assert written["written"] is True and Path(written["path"]).read_text(encoding="utf-8").startswith("<!doctype")
    # un texto que llega en los datos nunca se vuelve marcado
    hostile = copy.deepcopy(trace)
    hostile["actions"][0]["kind"] = "<script>alert(1)</script>"
    hostile["case_id"] = "</script><img src=x onerror=1>"
    hostile["failures"] = []
    hostile["status"]["items"] = [{"code": "X", "where": "<b>w</b>", "minute": 1, "detail": "</script>"}]
    page = obs.render_html(obs.view(hostile))
    assert "<script>alert(1)</script>" not in page and "<img src=x" not in page and "<b>w</b>" not in page
    assert page.count("<script") == 2 and page.count("</script>") == 2          # los dos propios, y ninguno mas


def test_p3o_149e_a_resident_sees_none_of_it(traces, monkeypatch):
    turns = (OXYGEN, NALOXONE, "Reassess in 10 minutes.")
    on = _play(OPIOID, turns)
    assert list(traces.iterdir())
    monkeypatch.delenv(store.STORE_FLAG)
    without_store = _play(OPIOID, turns)
    off = _play(OPIOID, turns, mode=None)
    assert off.shadow is None
    assert ev.authoritative(on) == ev.authoritative(without_store) == ev.authoritative(off)
    assert ev.fates(on) == ev.fates(off) and on.state == off.state and sorted(on.state) == sorted(off.state)
    assert not [key for key in on.state if "shadow" in key or "trace" in key.replace("treatment", "")]
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    for name in ("runtime_shadow_store", "runtime_shadow_observer", store.STORE_FLAG, "shadow_session_trace",
                 "DEVELOPMENT TEST WITNESS", "trace_of(", "persist_session"):
        assert name not in app, name
    assert app.count("phase3_shadow") == 3 and app.count("_shadow.observe(") == 1
    for name in ("pilot_freeze.py", "tools_pilot_preflight.py", "tools_pilot_smoke.py", "docs/RUNBOOK_PILOTO.md"):
        path = ROOT / name
        if path.is_file():
            assert store.STORE_FLAG not in path.read_text(encoding="utf-8"), name


def test_p3o_149f_the_tool_lists_shows_and_refuses(traces, tmp_path, capsys, monkeypatch):
    encounter = _play(GI, ("Place an IV line.", "Give 1 L of normal saline."))
    identifier = store.trace_id(_latest(encounter))
    assert obs.main(["--store", str(traces), "--list"]) == 0
    listed = capsys.readouterr().out
    assert identifier in listed and fam.COMPLETE_WITH_UNSUPPORTED_ACTIONS in listed and fam.UNSUPPORTED_ACTION in listed
    report = tmp_path / "report.html"
    assert obs.main(["--store", str(traces), "--id", identifier, "--out", str(report)]) == 0
    printed = capsys.readouterr().out
    assert "replay: exact" in printed and report.is_file() and "Shadow trace" in report.read_text(encoding="utf-8")
    assert obs.main(["--store", str(traces), "--id", "0" * 32]) == 1
    monkeypatch.delenv(store.STORE_FLAG)
    assert obs.main(["--list"]) == 2 and store.NOT_CONFIGURED in capsys.readouterr().out
    assert obs.main(["--store", str(ROOT / "x"), "--list"]) == 2
    assert obs.observe(identifier) is None                     # sin almacen nombrado no hay nada que leer
    assert rec.OBSERVER["verdict"] == "FACULTY_ONLY_SHADOW_OBSERVER_VALIDATED"


# -- P3-150: fallos visibles, ninguna accion perdida, ningun exito sin calificar ----------------------------------

def test_p3o_150a_the_seven_codes_and_the_five_states():
    assert fam.STATUS_CODES == rec.FAILURE_VISIBILITY["codes"] and len(set(fam.STATUS_CODES)) == 7
    assert fam.STATUS_STATES == rec.FAILURE_VISIBILITY["states"]
    assert fam.DISPOSITIONS == rec.FAILURE_VISIBILITY["dispositions"] and len(fam.DISPOSITIONS) == 8
    assert fam.MIRRORED_DISPOSITIONS == fam.DISPOSITIONS[:5] == rec.FAILURE_VISIBILITY["mirrored_dispositions"]
    assert not [state for state in fam.STATUS_STATES if "SUCCESS" in state or state in ("OK", "PASS", "DONE")]
    where = {"start": fam.ARRIVAL_REJECTED, "open": fam.ARRIVAL_REJECTED, "ensemble:lineage": fam.LINEAGE_REJECTED,
             "ensemble:HIGH:core": fam.WITNESS_FAILED, "ensemble:LOW:advance": fam.WITNESS_FAILED,
             "persist": fam.TRACE_PERSISTENCE_FAILED, "replay": fam.REPLAY_MISMATCH,
             "core": fam.INTERNAL_SHADOW_ERROR, "observe": fam.INTERNAL_SHADOW_ERROR,
             "history": fam.INTERNAL_SHADOW_ERROR, "anything else": fam.INTERNAL_SHADOW_ERROR}
    assert {name: fam.status_code(name) for name in where} == where
    assert set(obs.STATE_TEXT) == set(obs.STATE_ROLE) == set(fam.STATUS_STATES)
    assert obs.STATE_ROLE[fam.COMPLETE] == "good" and "good" not in [
        role for state, role in obs.STATE_ROLE.items() if state != fam.COMPLETE]


def test_p3o_150b_arrival_rejected(traces):
    treated = _play(OPIOID, (ZERO_MINUTE[OPIOID],))
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        refused = rs.ShadowSession.start(treated.state)
    assert refused.persistence["stored"] is True                # un rechazo se guarda aunque no siga ningun turno
    trace = store.load(refused.persistence["trace_id"])
    assert trace["runs"] == {} and trace["arrival"]["eligible"] is False and trace["arrival"]["differences"]
    assert trace["status"]["state"] == fam.REJECTED and trace["status"]["codes"] == [fam.ARRIVAL_REJECTED]
    replayed = store.replay(trace)
    assert replayed["replayed"] is False and replayed["nothing_to_replay"] is True and replayed["reproduces"]
    shown = obs.view(trace, replay=replayed)
    assert shown["status"]["state"] == fam.REJECTED and shown["status"]["role"] == "critical"
    assert shown["channels"] == [] and shown["runs"] == []
    page = obs.render_html(shown)
    assert "ARRIVAL REJECTED" in page and "REJECTED" in page and "ARRIVAL ELIGIBLE" not in page


def test_p3o_150c_unsupported_action_and_internal_error(traces, monkeypatch):
    encounter = _play(OPIOID, ("Ventilate with bag-valve-mask.", NALOXONE, NALOXONE), until=6)
    trace = _latest(encounter)
    assert trace["status"]["state"] == fam.COMPLETE_WITH_UNSUPPORTED_ACTIONS and trace["status"]["qualified"]
    assert trace["status"]["codes"] == [fam.UNSUPPORTED_ACTION] and trace["status"]["counts"] == {
        fam.UNSUPPORTED_ACTION: 2}
    kinds = [(row["kind"], row["disposition"]) for row in trace["actions"] if row["disposition"] != fam.BUILT]
    assert ("bag_mask", fam.DECLARED_GAP) in kinds and ("naloxone", fam.DECLARED_GAP) in kinds
    # un error interno de la sesion: el turno falla dentro de la sombra, y se dice
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        broken = acceptance.Encounter(GI)
        broken.order("Give 1 L of normal saline.")
        monkeypatch.setattr(type(broken.shadow), "_mirror",
                            lambda self, *args: (_ for _ in ()).throw(RuntimeError("inside the shadow")))
        broken.order("Reassess in 5 minutes.")
    monkeypatch.undo()
    assert [item.where for item in broken.shadow.failures] == ["observe"]
    status = store.trace_of(broken.shadow)["status"]
    assert status["state"] == fam.FAILED and status["codes"] == [fam.INTERNAL_SHADOW_ERROR]
    assert broken.minute == 25 and broken.shadow.runner.minutes_done == 20          # el encuentro siguio solo


def test_p3o_150d_replay_mismatch_and_lineage_rejected(traces, monkeypatch):
    trace = _latest(_play(OPIOID, (NALOXONE,), until=8))
    # una traza cuyo registro no es lo que su artefacto reproduce, sellada de nuevo
    wrong = copy.deepcopy(trace)
    wrong["runs"]["CENTER_REFERENCE"]["minutes"][4]["state_digest"] = "0" * 64
    replayed = store.replay(_resealed(wrong))
    assert replayed["replayed"] and replayed["reproduces"] is False
    assert replayed["runs"]["CENTER_REFERENCE"]["first_mismatch"] == 5 and replayed["runs"]["LOW"]["reproduces"]
    shown = obs.view(_resealed(wrong), replay=replayed)
    assert shown["status"]["state"] == fam.FAILED and shown["status"]["codes"] == [fam.REPLAY_MISMATCH]
    assert shown["status"]["items"][-1]["where"] == "replay:CENTER_REFERENCE"
    assert "REPLAY MISMATCH" in obs.render_html(shown) and "REPLAYS EXACTLY" not in obs.render_html(shown)
    # y la traza guardada NO cambia por haberla mirado: el estado de la vista es de la vista
    assert trace["status"]["state"] == fam.COMPLETE
    # los canales que se dibujan tambien se recalculan: alterar uno y resellar la traza no pasa por exacto
    drawn = copy.deepcopy(trace)
    drawn["runs"]["HIGH"]["minutes"][2]["channels"]["spo2"] += 0.5
    redrawn = store.replay(_resealed(drawn))
    assert store.verify(_resealed(drawn))["verified"] and redrawn["reproduces"] is False
    assert redrawn["runs"]["HIGH"]["first_mismatch"] == 3 and redrawn["runs"]["LOW"]["reproduces"]
    assert obs.view(_resealed(drawn), replay=redrawn)["status"]["codes"] == [fam.REPLAY_MISMATCH]
    # linaje viejo: registrada en otro nucleo, no se compara, se rechaza
    stale = copy.deepcopy(trace)
    stale["lineage"]["core_digest"] = "f" * 64
    refused = store.replay(_resealed(stale))
    assert refused["replayed"] is False and refused["refused"] == fam.LINEAGE_REJECTED and refused["runs"] == {}
    shown = obs.view(_resealed(stale), replay=refused)
    assert shown["status"]["codes"] == [fam.LINEAGE_REJECTED] and shown["status"]["state"] == fam.PARTIAL
    assert "LINEAGE_REJECTED" in obs.render_html(shown)
    uncertified = copy.deepcopy(trace)
    uncertified["lineage"]["certified"] = False
    assert store.replay(_resealed(uncertified))["refused"] == fam.LINEAGE_REJECTED
    # y en vivo: con el linaje sin certificar el conjunto no abre, y la sesion lo dice
    monkeypatch.setattr(ev, "core_lineage_ok", lambda: False)
    monkeypatch.setattr(ev, "core_lineage_reason", lambda: "the active core is not a certified member")
    live = _play(OPIOID, (NALOXONE,), until=4)
    assert "ensemble:lineage" in [item.where for item in live.shadow.failures]
    status = store.trace_of(live.shadow)["status"]
    assert fam.LINEAGE_REJECTED in status["codes"] and status["state"] == fam.PARTIAL
    assert not [name for name in store.trace_of(live.shadow)["runs"] if name in WITNESSES]


def test_p3o_150e_a_trace_that_cannot_be_stored_says_so(traces, monkeypatch):
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(GI)
        encounter.order("Give 1 L of normal saline.")
        assert encounter.shadow.persistence["stored"] is True
        monkeypatch.setattr(store, "persist", lambda trace, environ=None: {"stored": False, "why": "disk refused"})
        encounter.order("Reassess in 5 minutes.")
        encounter.order("Reassess in 5 minutes.")
        monkeypatch.undo()
        monkeypatch.setenv(store.STORE_FLAG, str(traces))
        encounter.order("Reassess in 5 minutes.")
    session = encounter.shadow
    assert [(item.where, item.message) for item in session.failures] == [("persist", "disk refused")]     # una vez
    trace = _latest(encounter)
    assert trace["turns"] == 4 and trace["status"]["codes"] == [fam.TRACE_PERSISTENCE_FAILED]
    assert trace["status"]["state"] == fam.PARTIAL
    assert [row["turns"] for row in store.records(encounter_id=session.encounter_id)] == [1, 4]
    assert session.runner.minutes_done == encounter.minute == 35                    # la corrida no se entera


def _mirrored(kind, minute=3, **payload):
    return rs.MirroredAction(f"m{minute:03d}-t01-0-{kind}", minute, kind, {"type": kind, **payload}, {}, 0.4)


def test_p3o_150f_no_executed_action_is_dropped_in_silence():
    # la regresion del defecto del oxigeno: lo que un adaptador dice mapear, lo construye
    for family, adapter in fam.ADAPTERS.items():
        if "oxygen" in adapter.maps:
            rows = fam.action_dispositions(adapter, [_mirrored("oxygen")], {"family_state": {}})
            assert [(row["disposition"], row["effective_minute"]) for row in rows] == [(fam.BUILT, 4)], family
    # todo tipo de accion tiene UNA disposicion, y ninguna es "sin cuenta"
    kinds = ("oxygen", "naloxone", "fluid", "blood", "ppi", "diuretic", "nitroglycerin", "bag_mask", "niv",
             "intubation", "vascular_access", "consult", "reassessment", "diagnostic", "procedural_sedation",
             "vasopressor", "something_new")
    for family, adapter in fam.ADAPTERS.items():
        for kind in kinds:
            rows = fam.action_dispositions(adapter, [_mirrored(kind, units=1, volume_ml=500)],
                                           {"family_state": {"endoscopy_at": None}})
            assert len(rows) == 1, (family, kind, rows)
            assert rows[0]["disposition"] in fam.MIRRORED_DISPOSITIONS[:4], (family, kind, rows)
    # el detector funciona: un adaptador que SI pierde una accion soportada queda senalado, no en silencio
    class Dropping(fam.OpioidAdapter):
        def interventions(self, mirrored, state=None):
            return (), []
    rows = fam.action_dispositions(Dropping(), [_mirrored("oxygen"), _mirrored("naloxone", 5)])
    assert [row["disposition"] for row in rows] == [fam.UNACCOUNTED, fam.UNACCOUNTED]
    status = fam.session_status(failures=[], gaps=[], actions=rows, expected_witnesses=(), runs={},
                                session_minutes=0)
    assert status["codes"] == [fam.INTERNAL_SHADOW_ERROR] and status["state"] == fam.PARTIAL
    # y un mapeo que no se puede evaluar tampoco calla
    class Raising(fam.OpioidAdapter):
        def interventions(self, mirrored, state=None):
            raise RuntimeError("mapping broke")
    assert [row["disposition"] for row in fam.action_dispositions(Raising(), [_mirrored("oxygen")])] == [
        fam.UNACCOUNTED]


def test_p3o_150g_no_state_reads_as_success_when_anything_is_missing(traces):
    encounter = _with_failed_witness()
    trace = _latest(encounter)
    assert trace["status"]["state"] != fam.COMPLETE and trace["status"]["qualified"] is True
    page = obs.render_html(obs.view(trace, replay=store.replay(trace)))
    assert "SUCCESS" not in page.upper().replace("UNSUCCESS", "") and "WITNESS_FAILED" in page
    assert "FAILED" in page and ">PARTIAL<" in page.replace("</span>PARTIAL", ">PARTIAL<")
    # solo COMPLETE es no calificado, y solo sin un solo item
    for items, state in (([], fam.COMPLETE),
                         ([{"code": fam.UNSUPPORTED_ACTION, "where": "mapping"}],
                          fam.COMPLETE_WITH_UNSUPPORTED_ACTIONS),
                         ([{"code": fam.WITNESS_FAILED, "where": "ensemble:LOW:core"}], fam.PARTIAL),
                         ([{"code": fam.TRACE_PERSISTENCE_FAILED, "where": "persist"}], fam.PARTIAL),
                         ([{"code": fam.INTERNAL_SHADOW_ERROR, "where": "compare"}], fam.PARTIAL),
                         ([{"code": fam.INTERNAL_SHADOW_ERROR, "where": "core"}], fam.FAILED),
                         ([{"code": fam.REPLAY_MISMATCH, "where": "replay:LOW"}], fam.FAILED),
                         ([{"code": fam.ARRIVAL_REJECTED, "where": "start"}], fam.REJECTED)):
        found = fam.status_with_replay({"items": items}, None)
        assert found["state"] == state and found["qualified"] is (state != fam.COMPLETE), (items, found)
    # un testigo que falta, o que se quedo atras, nunca deja el estado en COMPLETE
    for runs in ({"SESSION_RUN": {"minutes": 9, "failed": False}, "LOW": {"minutes": 9, "failed": False},
                  "CENTER_REFERENCE": {"minutes": 9, "failed": False}},
                 {name: {"minutes": 9 if name != "HIGH" else 4, "failed": False} for name in RUNS}):
        status = fam.session_status(failures=[], gaps=[], actions=[], expected_witnesses=WITNESSES, runs=runs,
                                    session_minutes=9)
        assert status["state"] == fam.PARTIAL and status["codes"] == [fam.WITNESS_FAILED]
    assert rec.FAILURE_VISIBILITY["verdict"] == "SHADOW_FAILURE_VISIBILITY_VALIDATED"


# -- P3-153: los ataques y las secuencias aleatorias acotadas -----------------------------------------------------

POOL = {
    GI: ("Place an IV line.", "Give 1 L of normal saline.", "Transfuse 2 units of packed red blood cells.",
         "Give pantoprazole 80 mg IV.", "Consult gastroenterology.", "Order a type and crossmatch.",
         "Give oxygen by nasal cannula.", "Reassess in 5 minutes.", "Give midazolam 2 mg IV.",
         acceptance.UNMODELLED_ORDER),
    OPIOID: (OXYGEN, NALOXONE, "Ventilate with bag-valve-mask.", "Reassess in 5 minutes.", "Place an IV line.",
             "Give midazolam 2 mg IV.", "Reassess in 2 minutes.", acceptance.UNMODELLED_ORDER),
}
SEEDS = (11, 23, 47, 101, 257, 1009)


def _sequence(case, seed) -> tuple:
    """Una secuencia acotada y sembrada: la misma semilla da la misma secuencia. Incluye repetidos."""
    chooser = random.Random(f"{case}:{seed}")
    turns = [chooser.choice(POOL[case]) for _ in range(chooser.randint(3, 7))]
    if chooser.random() < 0.5:
        turns.insert(chooser.randrange(len(turns)), turns[chooser.randrange(len(turns))])       # un duplicado
    return tuple(turns)


def test_p3o_153a_the_sequences_are_bounded_and_repeatable():
    for case in (GI, OPIOID):
        sequences = [_sequence(case, seed) for seed in SEEDS]
        assert sequences == [_sequence(case, seed) for seed in SEEDS] and len(set(sequences)) == len(SEEDS)
        assert all(3 <= len(turns) <= 8 and set(turns) <= set(POOL[case]) for turns in sequences)
        played = {text for turns in sequences for text in turns}
        assert ZERO_MINUTE[case] in played and acceptance.UNMODELLED_ORDER in played, case
    assert "bounded and seeded" in rec.CERTIFICATION["randomized"]


@pytest.mark.parametrize("case", (GI, OPIOID))
@pytest.mark.parametrize("seed", SEEDS)
def test_p3o_153b_under_any_sequence_the_shadow_is_whole_and_the_encounter_does_not_notice(case, seed, traces):
    turns = _sequence(case, seed)
    on, page = _play_on_page(case, turns)
    off = _play(case, turns, mode=None)
    # aislamiento: el estado heredado, lo que ve el residente, lo que lee la puntuacion y el destino de cada orden
    assert ev.authoritative(on) == ev.authoritative(off) and on.state == off.state
    assert ev.fates(on) == ev.fates(off) and on.minute == off.minute and on.arrested == off.arrested
    # ciclo de vida: una sola sesion para todo el encuentro, por muchos turnos de cero minutos que haya
    session = on.shadow
    assert len(page.opened) == 1 and session.turns == len(turns)
    assert session.runner.minutes_done == on.minute
    assert [item for item in session.failures if item.where != "legacy_snapshot"] == [], session.failures
    # traza: guardada, entera, sin accion perdida, y se reproduce corrida por corrida
    trace = _latest(on)
    assert trace["turns"] == len(turns) and trace["session_minutes"] == on.minute
    mirrored = [row for row in trace["actions"] if row["disposition"] in fam.MIRRORED_DISPOSITIONS]
    assert [row["shadow_order_id"] for row in mirrored] == [item.order_id for item in session.mirrored]
    assert all(row["disposition"] in fam.MIRRORED_DISPOSITIONS[:4] for row in mirrored), trace["actions"]
    assert all(row["effective_minute"] is None or row["effective_minute"] > row["order_minute"]
               for row in mirrored)
    assert all(row["disposition"] in (fam.FROM_ENGINE_STATE, fam.NOT_MIRRORED)
               for row in trace["actions"] if row not in mirrored)
    assert trace["status"]["state"] in (fam.COMPLETE, fam.COMPLETE_WITH_UNSUPPORTED_ACTIONS)
    assert sorted(trace["runs"]) == sorted(rec.TRACE_STORE["runs"][trace["family"]])
    assert all(len(run["minutes"]) == on.minute for run in trace["runs"].values())
    replayed = store.replay(trace)
    if on.minute:
        assert replayed["replayed"] and replayed["reproduces"], replayed
    assert store.verify(trace)["verified"] and obs.view(trace, replay=replayed)["status"]["state"] == \
        trace["status"]["state"]


def test_p3o_153c_repeated_initialization_and_duplicate_actions(traces):
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(OPIOID)
        twins = [rs.ShadowSession.start(encounter.state) for _ in range(3)]
        assert len({id(twin) for twin in twins}) == 3 and len({twin.encounter_id for twin in twins}) == 1
        assert all(twin.failures == [] and twin.runner.minutes_done == 0 for twin in twins)
        encounter.order(f"{OXYGEN} {NALOXONE}")
        encounter.order(NALOXONE)
        # la misma jugada, observada otra vez: se refleja una sola
        session = encounter.shadow
        before = (len(session.mirrored), session.runner.digests(), session.ensemble.digests())
        state = copy.deepcopy(encounter.state)
        entry = encounter.entries[-1]
        ran = [dict(order["action"], _order_id=order.get("order_id")) for order in entry.get("orders") or []
               if order.get("action")]
        session.observe(state, state, None, {"executed": True, "action_summaries": []}, ran, "again")
        assert (len(session.mirrored), session.runner.digests(), session.ensemble.digests()) == before
        # abrir otra vez sobre el paciente ya tratado: rechazado, siempre
        for _ in range(2):
            again = rs.ShadowSession.start(encounter.state)
            assert again.runner is None and _codes(again) == [fam.ARRIVAL_REJECTED]
    trace = _latest(encounter)
    assert [row["kind"] for row in trace["actions"]].count("naloxone") == 2
    assert [row["disposition"] for row in trace["actions"] if row["kind"] == "naloxone"] == [fam.BUILT,
                                                                                            fam.DECLARED_GAP]
    assert store.replay(trace)["reproduces"]


def test_p3o_153d_an_action_at_the_exact_boundary(traces):
    """El motor detiene al paciente sin revertir en el minuto 20: la orden del 19 llega al ultimo estado."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        late = acceptance.Encounter(OPIOID)
        late.wait_until(19)
        late.order(NALOXONE)
        plain = acceptance.Encounter(OPIOID)
        plain.wait_until(25)
    assert late.minute == plain.minute == 20 and late.arrested and plain.arrested
    trace = _latest(late)
    assert [(row["order_minute"], row["effective_minute"], row["disposition"]) for row in trace["actions"]
            if row["kind"] == "naloxone"] == [(19, 20, fam.BUILT)]
    assert trace["session_minutes"] == 20 and all(len(run["minutes"]) == 20 for run in trace["runs"].values())
    treated, untreated = late.shadow.runner.digests(), plain.shadow.runner.digests()
    assert treated[:19] == untreated[:19] and treated[19] != untreated[19]         # ni un minuto antes
    assert store.replay(trace)["reproduces"] and store.replay(_latest(plain))["reproduces"]
    # una orden cuyo efecto caeria despues del ultimo minuto no reclama ningun estado
    rows = fam.action_dispositions(fam.ADAPTERS["opioid"], [_mirrored("naloxone", 20)])
    assert rows[0]["effective_minute"] == 21 > trace["session_minutes"]


def test_p3o_153e_wrong_family_missing_witness_and_mutated_arrival(traces):
    opioid = _latest(_play(OPIOID, (NALOXONE,), until=6))
    gi = _latest(_play(GI, ("Give 1 L of normal saline.",)))
    # una traza de GI presentada como de opioide: sus corridas son de otra familia, y le faltan los testigos
    wrong = _resealed({**copy.deepcopy(gi), "family": "opioid", "expected_witnesses": list(WITNESSES)})
    checked = store.verify(wrong)
    assert checked["verified"] is False and checked["wrong_family_runs"] == ["SESSION_RUN"]
    assert checked["missing_witnesses"] == list(WITNESSES) and "another family" in checked["why"]
    refused = store.replay(wrong)
    assert refused["replayed"] is False and refused["refused"] == fam.REPLAY_MISMATCH
    assert obs.view(wrong, replay=refused)["status"]["state"] == fam.FAILED
    # un testigo que falta de la traza: se dice por su nombre
    missing = copy.deepcopy(opioid)
    del missing["runs"]["LOW"]
    # quitado sin mas: la traza ya no es coherente consigo misma (su estado dice COMPLETE y le falta un testigo)
    bare = store.replay(_resealed(missing))
    assert bare["replayed"] is False and bare["missing_witnesses"] == ["LOW"] and "PARTIAL" in bare["why"]
    assert obs.view(_resealed(missing))["status"]["state"] == fam.FAILED
    # quitado y con el estado rehecho a juego: el replay lo nombra como testigo fallido
    missing["status"] = fam.session_status(
        failures=missing["failures"], gaps=missing["gaps"], actions=missing["actions"],
        expected_witnesses=missing["expected_witnesses"], session_minutes=missing["session_minutes"],
        runs={name: {"minutes": len(run["minutes"]), "failed": run["failed"]}
              for name, run in missing["runs"].items()})
    assert missing["status"]["codes"] == [fam.WITNESS_FAILED]
    replayed = store.replay(_resealed(missing))
    assert replayed["reproduces"] is False and replayed["missing_witnesses"] == ["LOW"]
    assert replayed["runs"]["LOW"]["code"] == fam.WITNESS_FAILED and replayed["runs"]["HIGH"]["reproduces"]
    shown = obs.view(_resealed(missing), replay=replayed)
    assert shown["status"]["codes"] == [fam.WITNESS_FAILED] and shown["status"]["state"] == fam.PARTIAL
    assert "missing from the trace" in obs.render_html(shown)
    # una llegada mutada dentro de la traza: el digesto la delata; resellada, su identidad ya es otra
    mutated = copy.deepcopy(opioid)
    mutated["arrival"]["fingerprint"] = "0" * 64
    mutated["encounter_id"] = "0" * 64
    assert store.verify(mutated)["why"] == store.DIGEST_MISMATCH
    assert store.trace_id(_resealed(mutated)) != store.trace_id(opioid)
    # y un artefacto de corrida cambiado: no reproduce lo registrado
    artifact = copy.deepcopy(opioid)
    artifact["runs"]["HIGH"]["replay_input"]["scenario"]["minutes"] = 3
    assert store.replay(_resealed(artifact))["runs"]["HIGH"]["reproduces"] is False


def test_p3o_153f_replay_after_failure_reads_what_was_recorded_and_no_more(traces, monkeypatch):
    encounter = _with_failed_witness()
    trace = _latest(encounter)
    first = store.replay(trace)
    assert first == store.replay(trace) == store.replay(json.loads(json.dumps(trace)))        # determinista
    assert first["runs"]["HIGH"] == {"reproduces": True, "minutes": 1, "recorded": 1, "first_mismatch": None,
                                     "why": ""}
    # un replay que no puede correr no se convierte en exito
    monkeypatch.setattr(fam, "artifact_rows", lambda scenario: (_ for _ in ()).throw(RuntimeError("replay broke")))
    broken = store.replay(trace)
    assert broken["replayed"] and broken["reproduces"] is False
    assert all("could not be replayed" in row["why"] for row in broken["runs"].values())
    assert obs.view(trace, replay=broken)["status"]["state"] == fam.FAILED


def test_p3o_153g_nothing_gained_authority():
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False and rs.MODULE_VERSION == ra.EXPECTED_LAYER == "P3-11"
    assert rs.LIVE_FAMILIES == ("gi_bleed", "opioid") and ra.AUTHORITY_FAMILY == "gi_bleed"
    assert sorted(ra.APPROVED_SNAPSHOTS) == ["gi_pressure_committed"]
    assert ra.site_for({}, {}) is None and rs.mode({}) == rs.MODE_OFF
    assert set(rec.CERTIFICATION["attacks"]) == {
        "repeated initialization", "zero-minute turns", "duplicate actions", "unsupported actions",
        "action at the exact boundary", "replay after failure", "wrong-family trace", "stale lineage",
        "missing witness", "mutated arrival"}
    assert len(rec.CERTIFICATION["covers"]) == 8 and rec.CERTIFICATION["also_with_the_store_on"] is True
    text = json.dumps(rec.all_records(), default=str)
    import management_causality as mc
    assert not any(label in text for label in mc.FORBIDDEN_LABELS)
    source = (ROOT / "shadow_observability_record.py").read_text(encoding="utf-8")
    assert "runtime_shadow" not in source and "phase3_shadow" not in source           # datos puros, sin la capa


# -- La revision adversarial independiente: una prueba por hallazgo corregido -------------------------------------
# (R1 a R19 son las etiquetas del informe de la revision; el detalle esta en docs/PHASE3_SHADOW_OBSERVABILITY.md §8)

def test_p3o_r1_a_witness_that_fails_at_open_does_not_take_the_trace_with_it(traces, monkeypatch):
    real = fam.OpioidAdapter.profile

    def profile(self, point):
        if self.transmission_witness == "HIGH":
            raise RuntimeError("this witness cannot open")
        return real(self, point)

    monkeypatch.setattr(fam.OpioidAdapter, "profile", profile)
    encounter = _play(OPIOID, (OXYGEN, NALOXONE), until=8)
    session = encounter.shadow
    assert session.persistence["stored"] is True and "persist" not in [item.where for item in session.failures]
    assert [item.where for item in session.failures] == ["ensemble:HIGH:open"]
    trace = _latest(encounter)
    high = trace["runs"]["HIGH"]
    assert high["failed"] is True and high["minutes"] == [] and high["last_valid_minute"] == 0
    assert high["parameter"]["declared"] == 0.06 and high["parameter"]["value"] is None      # no corrio con ninguno
    assert [len(trace["runs"][name]["minutes"]) for name in ("SESSION_RUN", "LOW", "CENTER_REFERENCE")] == [8] * 3
    assert trace["status"]["state"] == fam.PARTIAL and trace["status"]["codes"] == [fam.WITNESS_FAILED]
    assert store.verify(trace)["verified"] and store.replay(trace)["reproduces"]
    # y una corrida que no se puede leer en absoluto queda en la traza como fallida, sin llevarse a las demas
    monkeypatch.setattr(fam, "run_channels", lambda runner: (_ for _ in ()).throw(RuntimeError("unreadable"))
                        if runner.adapter.transmission_witness == "LOW" else [])
    partial = store.trace_of(session)
    assert partial["runs"]["LOW"]["failed"] and partial["runs"]["LOW"]["artifact_error"] == "RuntimeError"
    assert set(partial["runs"]) == set(RUNS)


def test_p3o_r2_no_field_of_a_trace_chooses_where_a_record_is_written(traces, tmp_path):
    trace = _latest(_play(GI, ("Give 1 L of normal saline.",)))
    outside = tmp_path / "outside"
    outside.mkdir()
    for family, case in ((f"{outside}/", GI), ("../../escape", GI), ("gi_bleed", f"{outside}/x"),
                         ("gi_bleed", "x/../../r2_escape/live"), ("..", ".."), ("", "")):
        hostile = _resealed({**copy.deepcopy(trace), "family": family, "case_id": case})
        outcome = store.persist(hostile)
        assert outcome["stored"] is True, outcome
        written = Path(outcome["path"])
        assert written.parent == traces and written.is_file() and "/" not in written.name
        assert written.name.count(".") == 1 and written.name.endswith(".json")
    assert list(outside.iterdir()) == [] and not (tmp_path / "r2_escape").exists()
    assert sorted(path.parent for path in tmp_path.rglob("*.json")) == [traces] * len(list(traces.iterdir()))
    # por el camino en vivo: un caso cuyo identificador trae separadores de ruta
    arrival = copy.deepcopy(_play(GI).state)
    arrival["encounter_spec"]["variant_id"] = "x/../../r2_escape/live"
    (traces / "gi_bleed__x").mkdir()
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        refused = rs.ShadowSession.start(arrival)
    assert refused.persistence["stored"] is True and Path(refused.persistence["path"]).parent == traces
    assert not (tmp_path / "r2_escape").exists() and list((traces / "gi_bleed__x").iterdir()) == []


HELD = "Order a lactate, wait for the result, then give naloxone 0.4 mg IV."


def test_p3o_r3_an_order_held_until_a_result_is_never_lost_from_the_timeline(traces):
    """R3 de la revision. Cuando se escribio, la orden retenida que el motor ejecutaba despues quedaba como
    fila NOT_MIRRORED y la corrida no llevaba su efecto. El ciclo siguiente (P3-158) la refleja en el minuto
    real de ejecucion: lo que esta prueba sigue protegiendo es que NUNCA falta de la linea de acciones, ni
    mientras espera ni despues de correr. El detalle del reflejo esta en test_shadow_resolution.py."""
    waiting = _latest(_play(OPIOID, (HELD,)))
    held = [row for row in waiting["actions"] if row["kind"] == "naloxone"]
    assert [(row["disposition"], row["order_minute"], row["effective_minute"]) for row in held] == [
        (fam.HELD_NOT_EXECUTED, None, None)] and "has not run it" in held[0]["why"]
    assert waiting["status"]["state"] == fam.COMPLETE          # el motor no la ejecuto: no falta nada en la sombra
    encounter = _play(OPIOID, (HELD,), until=40)
    session, trace = encounter.shadow, _latest(encounter)
    assert encounter.state["family_state"]["naloxone"] > 0
    ran = [row for row in trace["actions"] if row["kind"] == "naloxone"]
    assert [(row["disposition"], row["order_minute"], row["effective_minute"]) for row in ran] == [(fam.BUILT, 5, 6)]
    assert not [row for row in trace["actions"] if row["disposition"] in (fam.NOT_MIRRORED, fam.HELD_NOT_EXECUTED)]
    mirrored = [row for row in trace["actions"] if row["disposition"] in fam.MIRRORED_DISPOSITIONS]
    assert [row["shadow_order_id"] for row in mirrored] == [item.order_id for item in session.mirrored]
    assert store.verify(trace)["verified"] and store.replay(trace)["reproduces"]
    assert "MIRRORED" in rec.FAILURE_VISIBILITY["no_silent_drop"] and "SUPERSEDED" in rec.FAILURE_VISIBILITY[
        "held_orders"]


def _tampered(trace, edit) -> dict:
    body = copy.deepcopy(trace)
    edit(body)
    return _resealed(body)


def _swap_witnesses(body):
    body["runs"]["LOW"], body["runs"]["HIGH"] = body["runs"]["HIGH"], body["runs"]["LOW"]


def _swap_and_relabel(body):
    _swap_witnesses(body)
    for name in ("LOW", "HIGH"):
        body["runs"][name]["witness"] = name
        body["runs"][name]["parameter"]["declared"] = fam.TRANSMISSION_WITNESSES[name]
        body["runs"][name]["parameter"]["value"] = fam.TRANSMISSION_WITNESSES[name]


def _all_are_the_center(body):
    for name in ("LOW", "HIGH"):
        run = copy.deepcopy(body["runs"]["CENTER_REFERENCE"])
        run["witness"] = name
        run["parameter"]["declared"] = run["parameter"]["value"] = fam.TRANSMISSION_WITNESSES[name]
        body["runs"][name] = run


def _truncate(body):
    body["runs"]["LOW"]["minutes"] = body["runs"]["LOW"]["minutes"][:5]
    body["runs"]["LOW"]["last_valid_minute"] = 5


def _truncate_and_mark(body):
    _truncate(body)
    body["runs"]["LOW"]["failed"] = True


RESEALED_EDITS = {
    "witnesses_swapped": (_swap_witnesses, "not the witness its name says"),
    "witnesses_swapped_and_relabelled": (_swap_and_relabel, "ran another value than the witness declares"),
    "every_witness_is_the_center": (_all_are_the_center, "ran another value than the witness declares"),
    "a_witness_truncated": (_truncate, "not marked failed"),
    "a_witness_truncated_and_marked_failed": (_truncate_and_mark, "the recorded status is not what"),
    "session_minutes_changed": (lambda body: body.update(session_minutes=5), "minutes"),
    "parameter_value_changed": (lambda body: body["runs"]["HIGH"]["parameter"].update(value=0.03),
                                "not the declared value"),
    "an_action_moved": (lambda body: body["actions"][0].update(order_minute=7), "not in the timeline"),
    "an_action_renamed": (lambda body: body["actions"][0].update(kind="oxygen"), "not in the timeline"),
    "core_version_renamed": (lambda body: body["lineage"].update(core_version="PHASE2_CLOSURE"),
                             "another core version"),
    "expected_witnesses_dropped": (lambda body: body.update(expected_witnesses=["LOW"]),
                                   "not the ones the family declares"),
    "status_rewritten": (lambda body: body["status"].update(state=fam.FAILED), "the recorded status is not what"),
}


@pytest.mark.parametrize("edit", sorted(RESEALED_EDITS))
def test_p3o_r4_a_resealed_edit_that_no_longer_tells_one_story_is_not_verified(traces, edit):
    trace = _latest(_play(OPIOID, (NALOXONE,), until=12))
    assert store.verify(trace)["verified"] and store.verify(trace)["inconsistencies"] == []
    change, said = RESEALED_EDITS[edit]
    forged = _tampered(trace, change)
    checked = store.verify(forged)
    assert checked["digest_matches"] is True and checked["verified"] is False, edit       # sellada, y aun asi no
    assert said in checked["why"], (edit, checked["why"])
    replayed = store.replay(forged)
    assert replayed["replayed"] is False and replayed["refused"] == fam.REPLAY_MISMATCH
    for shown in (obs.view(forged), obs.view(forged, replay=replayed)):          # con replay o sin el
        assert shown["status"]["state"] == fam.FAILED and shown["integrity"]["verified"] is False
        page = obs.render_html(shown)
        assert "TRACE NOT VERIFIED" in page and "REPLAYS EXACTLY" not in page and ">COMPLETE<" not in page


def test_p3o_r4_the_labels_cannot_be_rewritten_and_a_failed_trace_cannot_be_dressed_as_complete(traces):
    trace = _latest(_play(OPIOID, (NALOXONE,), until=6))
    for field, value in (("selected_witness", "CENTER_REFERENCE"), ("runtime_authority", "common_core"),
                         ("resident_visible", True), ("use", "PRODUCTION")):
        forged = _resealed({**copy.deepcopy(trace), field: value})
        assert store.verify(forged)["why"] == store.NOT_A_TRACE and store.persist(forged)["why"] == store.NOT_A_TRACE
    failed = _latest(_with_failed_witness())
    dressed = _tampered(failed, lambda body: body.update(status=copy.deepcopy(trace["status"])))
    assert dressed["status"]["state"] == fam.COMPLETE and store.verify(dressed)["verified"] is False
    shown = obs.view(dressed, replay=store.replay(dressed))
    assert shown["status"]["state"] == fam.FAILED and "TRACE NOT VERIFIED" in obs.render_html(shown)
    assert rec.TRACE_STORE["not_cross_checked"] == ("turns",) and "no signature" in rec.TRACE_STORE["integrity"]


def test_p3o_r5_an_unsealed_edit_is_seen_wherever_the_record_is_read(traces, capsys):
    encounter = _play(OPIOID, (NALOXONE,), until=6)
    row = store.records()[-1]
    path = Path(row["path"])
    record = json.loads(path.read_text(encoding="utf-8"))
    record["trace"]["status"]["state"] = fam.FAILED                     # editado en el archivo, sin resellar
    path.write_text(json.dumps(record), encoding="utf-8")
    listed = [item for item in store.records() if item["trace_id"] == row["trace_id"]][0]
    assert listed["verified"] is False and listed["why"] == store.DIGEST_MISMATCH
    assert obs.main(["--store", str(traces), "--list"]) == 0
    printed = capsys.readouterr().out
    line = next(text for text in printed.splitlines() if text.startswith(row["trace_id"]))
    assert store.NOT_VERIFIED in line and fam.FAILED not in line.replace(store.NOT_VERIFIED, "")
    assert obs.main(["--store", str(traces), "--id", row["trace_id"], "--no-replay"]) == 0
    assert "trace: NOT VERIFIED" in capsys.readouterr().out
    shown = obs.observe(row["trace_id"], replay=False)
    assert shown["integrity"]["verified"] is False and shown["status"]["codes"] == [fam.REPLAY_MISMATCH]
    assert "TRACE NOT VERIFIED" in obs.render_html(shown)
    assert encounter.shadow.failures == []


class _Unprintable:
    def __str__(self):
        raise RuntimeError("no text")


@pytest.mark.parametrize("answer", ["nope", ["a", "list"], 7, {"stored": False, "why": _Unprintable()},
                                    {"stored": "yes"}, {}])
def test_p3o_r6_nothing_the_store_answers_can_raise_into_the_encounter(traces, monkeypatch, answer):
    off = _play(GI, ("Give 1 L of normal saline.", "Reassess in 5 minutes."), mode=None)
    monkeypatch.setattr(store, "persist", lambda trace, environ=None: answer)
    on = _play(GI, ("Give 1 L of normal saline.", "Reassess in 5 minutes."))
    assert ev.authoritative(on) == ev.authoritative(off) and on.minute == 25
    session = on.shadow
    assert session.runner.minutes_done == 25 and session.persistence["stored"] is not True
    assert [item.where for item in session.failures] == ["persist"]                 # dicho, y una sola vez
    assert _codes(session) == [fam.TRACE_PERSISTENCE_FAILED]


def test_p3o_r7_a_file_that_is_not_a_record_does_not_break_the_listing(traces, capsys):
    encounter = _play(GI, ("Give 1 L of normal saline.",))
    good = encounter.shadow.persistence["trace_id"]
    shapes = ('{"trace": {"session_minutes": "abc"}}', '{"trace": {"status": 3, "runs": 4}}', '{"trace": []}',
              "[]", "not json", '{"trace": {"turns": [1]}, "trace_id": {}}', "", '{"trace": {"actions": 5}}')
    for index, text in enumerate(shapes):
        (traces / f"zz_{index}.json").write_text(text, encoding="utf-8")
    rows = store.records()
    assert [row["trace_id"] for row in rows if not row["unreadable"] and row["verified"]] == [good]
    broken = [row for row in rows if row["unreadable"] or not row["verified"]]
    assert len(broken) == len(shapes) and all(row["state"] == store.UNREADABLE or not row["verified"]
                                              for row in broken)
    assert [row["trace_id"] for row in store.heads() if row["verified"]] == [good]
    assert store.load(good) is not None and store.records(family="gi_bleed")[0]["trace_id"] == good
    assert obs.main(["--store", str(traces), "--list"]) == 0
    printed = capsys.readouterr().out
    assert good in printed and store.UNREADABLE in printed


def test_p3o_r8_the_tool_does_not_call_a_rejected_arrival_an_exact_replay(traces, capsys):
    treated = _play(OPIOID, (ZERO_MINUTE[OPIOID],))
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        refused = rs.ShadowSession.start(treated.state)
    assert obs.main(["--store", str(traces), "--id", refused.persistence["trace_id"]]) == 0
    printed = capsys.readouterr().out
    assert "replay: nothing to replay" in printed and "exact" not in printed and "REJECTED" in printed
    page = obs.render_html(obs.observe(refused.persistence["trace_id"]))
    assert "NOTHING TO REPLAY" in page and "REPLAYS EXACTLY" not in page


def test_p3o_r9_a_hostile_or_broken_trace_never_breaks_the_page(opioid_view, tmp_path):
    _, trace, _ = opioid_view
    edits = {
        "inf_channel": lambda b: b["runs"]["LOW"]["minutes"][3]["channels"].update(spo2=float("inf")),
        "nan_channel": lambda b: b["runs"]["LOW"]["minutes"][3]["channels"].update(paco2=float("nan")),
        "text_channel": lambda b: b["runs"]["HIGH"]["minutes"][0]["channels"].update(spo2="<b>x</b>"),
        "text_parameter": lambda b: b["runs"]["HIGH"]["parameter"].update(declared="<i>0.06</i>", value="x"),
        "short_differences": lambda b: b["arrival"].update(differences=[["only"], [], "text", ["a", "b"]]),
        "action_without_keys": lambda b: b.update(actions=[{}, {"kind": "<script>"}, "text", None]),
        "status_without_keys": lambda b: b.update(status={"items": [{}, {"code": "X"}, 5], "state": 9}),
        "runs_is_not_a_mapping": lambda b: b.update(runs=[1, 2]),
        "run_is_not_a_run": lambda b: b["runs"].update(LOW="text"),
        "minutes_are_not_rows": lambda b: b["runs"]["LOW"].update(minutes=[1, "x", None, {}]),
        "comment_opener_in_a_name": lambda b: b["runs"].update({"<!--<script>": b["runs"].pop("LOW")}),
        "everything_gone": lambda b: [b.pop(key) for key in list(b) if key not in ("artifact",)],
    }
    for name, change in edits.items():
        body = copy.deepcopy(trace)
        change(body)
        for replay in (None, store.replay(body)):
            shown = obs.view(body, replay=replay)
            page = obs.render_html(shown)
            assert shown["integrity"]["verified"] is False and shown["status"]["state"] == fam.FAILED, name
            assert page.count("<script") == 2 and page.count("</script>") == 2, name
            block = page.split('id="viz-data">')[1].split("</script>")[0]
            assert "<" not in block and ">" not in block and "&" not in block, name
            assert json.loads(block) is not None                       # el bloque de datos siempre se lee
            assert "<b>x</b>" not in page and "<i>0.06</i>" not in page and page.count("<script>") == 1, name
        assert obs.write_report(shown, tmp_path / f"{name}.html")["written"] is True, name
    # y un destino que no se puede escribir se dice, no se levanta
    assert obs.write_report(obs.view(trace), tmp_path) == {
        "written": False, "why": "the report could not be written: IsADirectoryError"}


def test_p3o_r11_r12_identity_reads_what_failed_and_a_reason_is_recorded_once(traces, monkeypatch):
    # dos sesiones rechazadas por motivos distintos sobre el mismo caso: dos registros, sin colision
    first = _play(GI, (ZERO_MINUTE[GI],)).state
    second = copy.deepcopy(first)
    second["observable"]["spo2"] = second["observable"]["spo2"] - 2
    second["hidden"]["effective_volume"] = 0.1                         # fuera de la huella de la llegada: da igual
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        sessions = [rs.ShadowSession.start(first), rs.ShadowSession.start(second)]
    assert all(session.persistence["stored"] and not session.persistence["idempotent"] for session in sessions)
    assert sessions[0].persistence["trace_id"] != sessions[1].persistence["trace_id"]
    assert [item.where for session in sessions for item in session.failures] == ["start", "start"]
    # un fallo de escritura cuyo texto cambia en cada turno es UNA razon: se registra una vez
    count = iter(range(100))
    monkeypatch.setattr(store, "persist", lambda trace, environ=None: {
        "stored": False, "kind": "STORE_ERROR OSError",
        "why": f"STORE_ERROR OSError: [Errno 28] No space left on device: 'record_{next(count)}.json'"})
    encounter = _play(GI, ("Give 1 L of normal saline.",) + ("Reassess in 5 minutes.",) * 5)
    persist = [item for item in encounter.shadow.failures if item.where == "persist"]
    assert len(persist) == 1 and "record_0.json" in persist[0].message and encounter.shadow.turns == 6
    assert encounter.shadow.persistence["why"].endswith("record_5.json'")           # el ultimo, a la vista


def test_p3o_r13_the_status_functions_fail_closed():
    complete = {"items": []}
    assert fam.status_with_replay(complete, None)["state"] == fam.COMPLETE
    assert fam.status_with_replay(complete, {"reproduces": True})["state"] == fam.COMPLETE
    for replay in ({}, {"reproduces": None}, {"reproduces": "yes"}, {"reproduces": 1}, {"runs": {}},
                   {"reproduces": False}):
        found = fam.status_with_replay(complete, replay)
        assert found["state"] == fam.FAILED and found["codes"] == [fam.REPLAY_MISMATCH], replay
    # un codigo que la capa no conoce no es "nada": es un error interno, con lo que decia
    for items in ([{"code": "SOMETHING_NEW", "where": "x", "detail": "d"}], [{"code": None, "where": "x"}]):
        found = fam.status_with_replay({"items": items}, None)
        assert found["state"] == fam.PARTIAL and found["codes"] == [fam.INTERNAL_SHADOW_ERROR]
        assert "unknown status code" in found["items"][0]["detail"]
    odd = fam.status_with_replay(complete, {"reproduces": False,
                                           "runs": {"LOW": {"reproduces": False, "code": "ODD"}}})
    assert odd["state"] == fam.PARTIAL and odd["codes"] == [fam.INTERNAL_SHADOW_ERROR]
    # plegar dos veces el mismo replay no duplica nada
    once = fam.status_with_replay(complete, {"reproduces": False, "why": "w", "runs": {}})
    assert fam.status_with_replay(once, {"reproduces": False, "why": "w", "runs": {}}) == once


@pytest.mark.parametrize("case", (GI, OPIOID))
def test_p3o_r14_the_eligibility_rule_reads_more_than_it_did(case):
    arrival = legacy_adapter._initialized(_play(case).state)
    assert rs.arrival_eligibility(arrival)["eligible"] is True
    edits = {
        "a_fraction_of_a_minute": (lambda s: s.update(sim_time=0.9), "clock_at_arrival"),
        "an_order_on_the_history": (lambda s: s["treatments"].setdefault("order_history", []).append({"x": 1}),
                                    "nothing_administered"),
        "a_disposition": (lambda s: s["treatments"].update(disposition="icu"), "nothing_administered"),
        "no_authored_arrival": (lambda s: s["encounter_spec"]["clinical_case"].pop("observable"),
                                "monitor_is_the_authored_arrival"),
    }
    for name, (change, condition) in edits.items():
        state = copy.deepcopy(arrival)
        change(state)
        found = rs.arrival_eligibility(state)
        assert found["eligible"] is False and found["conditions"][condition] is False, (name, found)
        assert found["differences"], name
        with ev.shadow(rs.MODE_SHADOW_COMPARE):
            session = rs.ShadowSession.start(state)
        assert session.runner is None and _codes(session) == [fam.ARRIVAL_REJECTED], name
    # lo que la regla NO puede comparar esta declarado, no escondido
    assert "hidden state" in rec.LIFECYCLE["not_compared"]
    # y nunca levanta, sea lo que sea lo que se le de
    for state in ({}, {"sim_time": "x"}, {"family_state": 3}, {"treatments": []}, None, 5, {"encounter_spec": 1}):
        assert rs.arrival_eligibility(state)["eligible"] is False
        assert rs.arrival_untouched(state) is False


def test_p3o_r16_a_contributor_built_from_the_engines_state_is_in_the_timeline(traces):
    turns = ("Give 1 litre of normal saline over 15 minutes. Reassess in 10 minutes.",
             "Transfuse 2 units of packed red cells. Start pantoprazole 80 mg IV. Reassess in 20 minutes.",
             "Consult gastroenterology for urgent endoscopy.")
    encounter = _play(GI, turns, until=100)
    session, trace = encounter.shadow, _latest(encounter)
    assert session.endoscopy_at is not None                       # el motor la hizo; no es una orden reflejada
    rows = [row for row in trace["actions"] if row["disposition"] == fam.FROM_ENGINE_STATE]
    assert [(row["kind"], row["shadow_order_id"], row["order_minute"]) for row in rows] == [
        ("EndoscopicHemostasis", "gastroenterology_endoscopy", None)]
    assert "engine's own state" in rows[0]["why"]
    assert [row["disposition"] for row in trace["actions"] if row["kind"] == "consult"] == [
        fam.SKIPPED_NO_PHYSIOLOGY] and session.endoscopy_at == 90
    assert store.verify(trace)["verified"] and store.replay(trace)["reproduces"]
    assert "FROM_ENGINE_STATE" in obs.render_html(obs.view(trace))
    # antes de que el motor la haga, no hay tal fila
    early = _latest(_play(GI, ("Consult gastroenterology.",), until=10))
    assert not [row for row in early["actions"] if row["disposition"] == fam.FROM_ENGINE_STATE]


def test_p3o_r17_a_record_is_written_whole_or_not_at_all(traces, monkeypatch):
    encounter = _play(GI, ("Give 1 L of normal saline.",))
    assert [path.name for path in traces.iterdir() if "pending" in path.name] == []
    trace = _latest(encounter)
    other = _resealed({**copy.deepcopy(trace), "turns": 9})
    real = Path.write_text

    def half(self, data, *args, **kwargs):
        real(self, data[: len(data) // 2], *args, **kwargs)
        raise OSError(28, "No space left on device")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(Path, "write_text", half)
        refused = store.persist(other)
    assert refused["stored"] is False and refused["kind"] == "STORE_ERROR OSError"
    assert [path.name for path in traces.iterdir() if "pending" in path.name] == []        # ni el temporal
    # el registro a medias NO quedo bajo el nombre del registro: el mismo guardado, despues, entra limpio
    assert store.trace_id(other) not in [row["trace_id"] for row in store.records()]
    again = store.persist(other)
    assert again["stored"] is True and again["idempotent"] is False and store.verify(store.load(again["trace_id"]))
