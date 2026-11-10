"""Ciclo de la segunda familia en vivo (2026-11-10): P3-139 a P3-145.

El opioide como SEGUNDA familia en la sombra en vivo de la Fase 3, sin autoridad:

- P3-139: la llegada en vivo se mapea con semantica existente, y solo si ES el caso redactado;
- P3-140: el parametro de transmision corre como un conjunto de tres testigos, ninguno elegido;
- P3-141: acciones reales del runtime, minuto efectivo exacto, fallos visibles;
- P3-142: la serie de seis vias, jugada por el camino de ordenes de la pagina;
- P3-143: vivo = fuera de linea = replay, estado por estado;
- P3-144: GI intacto, sin autoridad, sin puntuacion, sin residente, aislamiento entre familias;
- P3-145: las compuertas de preparacion, leidas del repositorio.

Los encuentros se juegan con ``pilot_acceptance.Encounter``, que es la rama de familias del camino de ordenes
de la pagina sin Streamlit: el lector congelado, el pipeline de ordenes y el motor heredado, que sigue siendo
la unica autoridad. Nada de lo que aqui se mide se ajusta a las curvas del motor heredado.

Registro: second_live_family_record. Etiquetas ``p3l``: ver ese modulo.
"""
import copy
import dataclasses
import json

import pytest

import management_causality as mc
import pilot_acceptance as acceptance
import runtime_authority as ra
import runtime_authority_store as store
import runtime_shadow as rs
import runtime_shadow_evidence as ev
import runtime_shadow_families as fam
import second_live_family_record as rec
from clinical_core import derived as dv
from clinical_core import legacy_adapter
from clinical_core import opioid_migration as om
from clinical_core import opioid_reference

CASE = "opioid_35m"
FIELD = fam.TRANSMISSION_FIELD
R = fam.TRANSMISSION_DECLARED_R
WITNESSES = dict(fam.TRANSMISSION_WITNESSES)
ORDER = tuple(WITNESSES)
ON = {rs.FLAG: rs.MODE_SHADOW_COMPARE}
OXYGEN = "Give oxygen 15 L/min by non-rebreather mask."
NALOXONE = "Give naloxone 0.4 mg IV."
#: Las seis vias. El motor heredado detiene al paciente sin revertir en el minuto 20: ese es el reloj real, y
#: la sombra llega hasta donde llega el encuentro, no mas.
ARMS = {
    "untreated": {"turns": (), "until": 20},
    "oxygen": {"turns": (OXYGEN,), "until": 20},
    "naloxone": {"turns": (NALOXONE,), "until": 60},
    "oxygen_and_naloxone": {"turns": (f"{OXYGEN} {NALOXONE}",), "until": 60},
    "delayed_naloxone": {"turns": ("Reassess in 10 minutes.", NALOXONE), "until": 60},
    "wait": {"turns": ("Reassess in 5 minutes.",) * 4, "until": 20},
}
CHANNELS = ("central_availability", "respiratory_rate", "ventilation", "paco2", "spo2", "delivery_rel", "fio2")
STATE_CHANNELS = ("V", "P", "T", "L", "G", "D", "fio2", "central_availability", "mechanics_efficiency")
COMMITTED_RUN = "COMMITTED"


# -- arnes -------------------------------------------------------------------------------------------------------

def _play(arm, *, case=CASE, mode=rs.MODE_SHADOW_COMPARE):
    """Un encuentro real por el camino de ordenes de la pagina, con la bandera en ``mode`` (None: apagada)."""
    spec = ARMS[arm]
    with ev.shadow(mode):
        encounter = acceptance.Encounter(case)
        for text in spec["turns"]:
            if encounter.arrested:
                break
            encounter.order(text)
        encounter.wait_until(spec["until"])
    return encounter


def _runners(session) -> dict:
    """El run comprometido de la sesion y los tres testigos, por nombre."""
    return {COMMITTED_RUN: session.runner, **session.ensemble.runners}


def _series(runner) -> dict:
    """{canal: {minuto: valor}} de un run, reconstruido DESDE SU ARTEFACTO y comprobado contra lo que el run
    registro en vivo: si el replay no diera los mismos estados, esta lectura no seria la del encuentro."""
    trajectory, anchors, profile = fam._replay_trajectory(runner.replay_input().scenario)
    assert [rs._digest_of(state) for state in trajectory.states[1:]] == list(runner.digests())
    out = {channel: {} for channel in CHANNELS + STATE_CHANNELS}
    for state in trajectory.states[1:]:
        minute = state.minute
        derived = dv.derive(state, anchors, profile)
        breathing = dv.respiration(state, anchors, profile)
        out["respiratory_rate"][minute] = breathing.respiratory_rate
        out["ventilation"][minute] = breathing.ventilation
        out["paco2"][minute] = breathing.paco2
        out["spo2"][minute] = derived.spo2
        out["delivery_rel"][minute] = derived.delivery_rel
        for name in ("V", "P", "T", "L", "G", "D", "fio2"):
            out[name][minute] = float(getattr(state, name))
        out["central_availability"][minute] = state.aux.central_availability
        out["mechanics_efficiency"][minute] = state.aux.mechanics_efficiency
    return out


def _first_moved(treated, base) -> dict:
    """{canal de estado: primer minuto en que difiere del brazo de referencia}."""
    out = {}
    for channel in STATE_CHANNELS:
        minute = mc.effect_starts_at(treated[channel], base[channel], 1)
        if minute is not None:
            out[channel] = minute
    return out


def _area(series, first, last):
    return sum(series[minute] for minute in range(first, last + 1))


@pytest.fixture(scope="module")
def live():
    return {arm: _play(arm) for arm in ARMS}


@pytest.fixture(scope="module")
def series(live):
    return {arm: {name: _series(runner) for name, runner in _runners(encounter.shadow).items()}
            for arm, encounter in live.items()}


# -- P3-139: la llegada en vivo ----------------------------------------------------------------------------------

LEGITIMATE = {"DIRECT_FROM_LIVE_STATE", "CERTIFIED_EXISTING_MAPPING", "FIXED_AUTHORED_CASE_ANCHOR"}


def test_p3l_139a_the_engine_authors_exactly_the_variants_the_adapter_certifies():
    import clinical_cases
    authored = tuple(variant["id"] for variant in clinical_cases.FAMILIES["opioid"]["variants"])
    assert authored == fam.ADAPTERS["opioid"].cases == rec.ARRIVAL_MAPPING["variants_authored_by_the_engine"]
    # el contraste que mantiene a ACS fuera: seis variantes redactadas, una certificada
    acs = tuple(variant["id"] for variant in clinical_cases.FAMILIES["acs"]["variants"])
    assert len(acs) == 6 and fam.ADAPTERS["acs"].cases == ("acs_70f_left_main",)
    assert "acs" not in rs.LIVE_FAMILIES and fam.ADAPTERS["acs"].live is False


@pytest.mark.parametrize("case", ["opioid_35m", "opioid_67f"])
def test_p3l_139b_every_authored_input_of_the_certified_mapping_equals_the_live_arrival(case):
    state = acceptance.Encounter(case).state
    adapter = fam.ADAPTERS["opioid"]
    anchors = opioid_reference.anchors(case)
    assert adapter.arrival_identity(anchors, state) == []
    # y la identidad es la que el adaptador exige antes de correr: con el estado vivo, las mismas anclas
    assert adapter.anchors(case, fam.COMMITTED, state) == adapter.anchors(case, fam.COMMITTED, None) == anchors
    # las dos unicas entradas declaradas sonda sintetica son las del registro, y bloquean una migracion
    assert sorted(name for name, how in anchors.declared.items() if how == "synthetic_probe") == [
        "arrival_lactate_excess", "intrinsic_sinus_rate"]


def test_p3l_139c_a_live_arrival_that_is_not_the_authored_case_is_refused_and_says_so():
    state = copy.deepcopy(legacy_adapter._initialized(acceptance.Encounter(CASE).state))
    state["observable"]["spo2"] = 88
    differences = fam.ADAPTERS["opioid"].arrival_identity(opioid_reference.anchors(CASE), state)
    assert [name for name, _, _ in differences] == ["observable.spo2"]
    session = rs.ShadowSession.start(state, environ=ON)
    # P3-147: el monitor alterado lo rechaza ya la regla COMPARTIDA de llegada, antes de abrir ningun run
    assert session is not None and session.runner is None and session.ensemble is None
    assert session.eligibility["conditions"]["monitor_is_the_authored_arrival"] is False
    # el fallo esta en el REGISTRO de la sesion (antes de este ciclo se quedaba en el runner)
    record = session.record()
    assert record["minutes"] == [] and len(record["failures"]) == 1
    failure = record["failures"][0]
    assert failure["exception"] == rs.ARRIVAL_REJECTED and failure["classification"] == rs.MAPPING_GAP
    assert "observable.spo2 live 88 / arrival 80" in failure["message"]
    # observar un turno despues no levanta nada ni inventa minutos
    session.observe(state, {**state, "sim_time": 5}, {}, {"executed": True, "action_summaries": []}, [], "t0")
    assert session.record()["minutes"] == []


def test_p3l_139d_every_required_runtime_input_has_a_legitimate_source():
    mapping = rec.ARRIVAL_MAPPING
    assert set(mapping["sources"].values()) <= LEGITIMATE
    missing = mapping["missing_or_synthetic"]
    assert missing["REQUIRED_RUNTIME_INPUTS_MISSING"] == ()
    assert missing["REQUIRED_RUNTIME_INPUTS_SYNTHETIC_ONLY"] == ()
    # lo sintetico se declara, no se esconde: dos tasas, el cociente respiratorio y la region
    assert om.DEEPENING_PER_MIN == 0.005 and om.NALOXONE["recovery_per_min"] == 0.10
    assert "0.005" in missing["model_parameters_synthetic_only"]["opioid deepening rate"]
    assert "0.10" in missing["model_parameters_synthetic_only"]["naloxone recovery rate"]
    assert missing["carried_by_the_action_and_not_read"] == dict(fam.OpioidAdapter.NOT_READ)
    # lo que la identidad comprueba en vivo es lo que el registro dice: el caso, la llegada mostrada y nada dado
    checked = mapping["identity_checked_live"]
    assert checked["the_case"] == fam.OpioidAdapter.AUTHORED_ITEMS
    assert checked["the_arrival_as_shown"] == tuple(fam.OpioidAdapter.SHOWN_ITEMS.values())
    assert set(fam.OpioidAdapter.AUTHORED_ITEMS) <= set(opioid_reference.TRUTH_PATHS)
    assert mapping["verdict"] == "OPIOID_LIVE_ARRIVAL_MAPPING_REUSES_EXISTING_SEMANTICS"


def _refused(state) -> str:
    """Abre una sesion sobre ``state`` con la bandera puesta y devuelve el mensaje del rechazo ('' si corre)."""
    session = rs.ShadowSession.start(state, environ=ON)
    assert session is not None
    if session.runner is not None and session.runner.anchors is not None:
        return ""
    assert session.ensemble is None
    # P3-147: lo generico lo rechaza la regla compartida; lo propio de la familia, su adaptador
    assert [failure.exception for failure in session.failures] in ([rs.ARRIVAL_REJECTED], ["ArrivalIdentityError"])
    assert session.record()["minutes"] == []
    return f"{session.failures[0].exception}: {session.failures[0].message}"


def test_p3l_139e_a_patient_already_treated_in_a_zero_minute_turn_is_not_an_arrival():
    """El hallazgo MEDIO de la revision independiente. Un turno que no avanza el reloj deja el minuto en 0 y la
    pagina reabre la sesion: el paciente ya tratado no puede pasar por la llegada."""
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        entry = encounter.order("Give midazolam 2 mg IV.")
    assert entry["executed"] is True and encounter.minute == 0
    # P3-147: la pagina ya NO suelta esta sesion (un turno de cero minutos no crea una llegada nueva)...
    assert encounter.shadow.is_for(encounter.state) is True and encounter.shadow.left_arrival is True
    assert encounter.state["observable"]["sbp"] != acceptance.Encounter(CASE).state["observable"]["sbp"]
    # ...y si alguien intentara abrir otra sobre este paciente, se rechaza
    why = _refused(encounter.state)
    assert why.startswith(rs.ARRIVAL_REJECTED) and "family_state." in why
    names = {name for name, _, _ in rs.arrival_eligibility(encounter.state)["differences"]}
    assert "observable.sbp" in names and "family_state.sedation_bp_drop" in names
    # y un paciente intacto, jugado igual, si corre
    assert _refused(acceptance.Encounter(CASE).state) == ""


@pytest.mark.parametrize("label", ["monitor", "engine_treatment", "engine_oxygen", "case_lactate", "case_hb",
                                   "case_fio2", "case_gas", "clock", "another_case"])
def test_p3l_139f_every_way_the_live_patient_can_differ_from_the_authored_arrival_is_refused(label):
    state = copy.deepcopy(legacy_adapter._initialized(acceptance.Encounter(CASE).state))
    spec = state["encounter_spec"]["clinical_case"]
    if label == "monitor":
        state["observable"].update({"spo2": 99, "respiratory_rate": 20, "mental_status": "Alert"})
    elif label == "engine_treatment":
        state["family_state"].update({"opioid": 0.2, "naloxone": 2.0, "bag_mask": True})
    elif label == "engine_oxygen":
        state["family_state"]["oxygen_fio2"] = 0.6
    elif label == "case_lactate":
        spec["investigations"]["lactate"]["result"]["lactate_mmol_l"] = 9.9
    elif label == "case_hb":
        spec["investigations"]["basic_labs"]["result"]["hemoglobin_g_dl"] = 6.0
    elif label == "case_fio2":
        spec["investigations"]["abg"]["result"]["fio2_percent"] = 60
    elif label == "case_gas":
        spec["investigations"]["abg"]["result"]["paco2_mm_hg"] = 40
    elif label == "clock":
        state["sim_time"] = 0
        state["family_state"]["elapsed"] = 7
    elif label == "another_case":
        state["encounter_spec"]["variant_id"] = "opioid_67f"
    why = _refused(state)
    assert why != "", label
    # las dos capas: la regla compartida para lo que cualquier familia comprueba, el adaptador para lo suyo
    shared = label in ("monitor", "engine_treatment", "engine_oxygen", "clock")
    assert why.startswith(rs.ARRIVAL_REJECTED if shared else "ArrivalIdentityError"), (label, why[:80])


def test_p3l_139g_a_state_the_check_cannot_read_is_refused_by_name_and_never_raises():
    for broken in ({"engine_family": "opioid", "sim_time": 0},
                   {"engine_family": "opioid", "sim_time": 0, "encounter_spec": {"variant_id": CASE}},
                   {"engine_family": "opioid", "sim_time": 0, "encounter_spec": {"variant_id": CASE,
                                                                               "clinical_case": {"id": CASE}}}):
        session = rs.ShadowSession.start(broken, environ=ON)
        assert session is not None and session.ensemble is None
        assert session.runner is None or session.runner.anchors is None
        assert session.failures and session.record()["minutes"] == []
        json.dumps(session.record(), default=str)


# -- P3-140: el conjunto por region -------------------------------------------------------------------------------

def test_p3l_140a_the_ensemble_is_the_three_witnesses_on_the_same_arrival_actions_and_timing(live):
    session = live["oxygen_and_naloxone"].shadow
    assert tuple(session.ensemble.runners) == ORDER == tuple(rec.ENSEMBLE["witnesses"])
    primary = session.runner
    for name, runner in session.ensemble.runners.items():
        assert runner.adapter.transmission_witness == name and runner.adapter.family == "opioid"
        assert runner.anchors == primary.anchors                                   # la misma llegada
        assert [vars(event) for event in runner.mirrored] == [vars(event) for event in primary.mirrored]
        assert runner.minutes_done == primary.minutes_done                        # el mismo reloj
        assert runner.family_writers == primary.family_writers                    # los mismos escritores
    # dos testigos difieren en UN campo del perfil y en nada mas
    profiles = {name: runner.profile for name, runner in session.ensemble.runners.items()}
    for a, b in zip(ORDER, ORDER[1:]):
        changed = [f.name for f in dataclasses.fields(profiles[a])
                   if getattr(profiles[a], f.name) != getattr(profiles[b], f.name)]
        assert changed == [FIELD], (a, b, changed)
    for name, profile in profiles.items():
        assert getattr(profile, FIELD) == WITNESSES[name] and profile.respiratory_quotient == R
    # y sus artefactos de replay, tambien: el escenario serializado difiere solo en esa fraccion
    scenarios = {name: runner.replay_input().scenario for name, runner in session.ensemble.runners.items()}
    low, high = json.loads(json.dumps(scenarios["LOW"], default=str)), json.loads(
        json.dumps(scenarios["HIGH"], default=str))
    low_profile, high_profile = low.pop("profile"), high.pop("profile")
    assert low == high
    assert {key for key in low_profile if low_profile[key] != high_profile[key]} == {FIELD}


def test_p3l_140b_each_witness_is_kept_whole_and_nothing_is_averaged_or_selected(live):
    session = live["naloxone"].shadow
    record = session.record()["region_ensemble"]
    assert record["selected_witness"] is None and record["complete"] is True and record["refused"] is None
    assert record["classification"] == "DEVELOPMENT_TEST_REGION"
    assert record["mathematical_region"] == [0.0, 0.060621]
    assert record["active_causal_region"] == {"above": 0.0, "up_to": 0.060621,
                                              "zero_is": "NEGATIVE_CONTROL_NOT_A_WITNESS"}
    minutes = session.runner.minutes_done
    for name in ORDER:
        witness = record["witnesses"][name]
        assert witness["value"] == WITNESSES[name]
        assert [row["minute"] for row in witness["minutes"]] == list(range(1, minutes + 1))
        assert witness["replay_digest"] and witness["failures"] == [] and witness["snapshot"]["approved"] is False
        assert "DEVELOPMENT_TEST_REGION" in " ".join(witness["snapshot"]["provenance"])
    # la vista derivada: los tres valores y su minimo y maximo. Ni media, ni mediana, ni valor representativo.
    for reading, rows in record["view"].items():
        assert len(rows) == minutes, reading
        for row in rows.values():
            assert set(row) == {"witnesses", "min", "max"} and tuple(row["witnesses"]) == ORDER
            assert row["min"] == min(row["witnesses"].values()) and row["max"] == max(row["witnesses"].values())

    def keys(value):
        if isinstance(value, dict):
            for key, item in value.items():
                yield str(key)
                yield from keys(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                yield from keys(item)
    forbidden = {"mean", "average", "median", "representative", "structural", "preferred", "center"}
    assert not forbidden & {key.lower() for key in keys(record["view"])}
    # los tres testigos son tres trayectorias distintas: no se colapsaron en una
    digests = session.ensemble.digests()
    assert len({digests[name][-1] for name in ORDER}) == 3


def test_p3l_140c_no_point_is_silently_selected_anywhere(live):
    session = live["naloxone"].shadow
    # el run de la sesion es el perfil COMPROMETIDO: el enlace no esta declarado. No es CENTER_REFERENCE.
    assert session.runner.adapter is fam.ADAPTERS["opioid"]
    assert session.runner.adapter.transmission_witness is None
    assert session.runner.profile == om.profile()
    assert session.runner.profile.respiratory_quotient is None and getattr(session.runner.profile, FIELD) is None
    assert session.runner.snapshot_.id == "opioid_committed_default"
    assert session.runner.digests()[-1] not in {digests[-1] for digests in session.ensemble.digests().values()}
    # el adaptador registrado no lleva ningun testigo, y un testigo nunca esta en el registro
    for adapter in fam.ADAPTERS.values():
        assert getattr(adapter, "transmission_witness", None) is None
    assert fam.ADAPTERS["opioid"].profile(fam.COMMITTED) == om.profile()
    # solo el opioide declara una region en vivo; asma y los demas, ninguna (FD-NEW-4)
    assert {family for family, adapter in fam.ADAPTERS.items() if adapter.region_witnesses()} == {"opioid"}
    assert fam.OpioidAdapter.witness("LOW").region_witnesses() == {}, "un conjunto no anida"
    with pytest.raises(ValueError):
        fam.OpioidAdapter.witness("MEAN")
    assert rec.ENSEMBLE["selected_witness"] is None and rec.ENSEMBLE["averaged"] is False


def test_p3l_140d_the_committed_run_is_the_negative_control_state_for_state(live, series):
    """El run comprometido es, estado por estado, el de fraccion 0: no expresa nada aguas abajo del PaCO2."""
    session = live["naloxone"].shadow

    class Zero(fam.OpioidAdapter):
        def profile(self, point):
            return dataclasses.replace(om.profile(), respiratory_quotient=R, **{FIELD: 0.0})

    offline = fam.ShadowPhysiologyRunner(Zero(), CASE)
    offline.anchors, offline.profile = session.runner.anchors, Zero().profile(fam.COMMITTED)
    offline.family_writers = session.runner.family_writers
    offline.mirror(session.mirrored)
    assert offline.advance(session.runner.minutes_done)
    assert offline.digests() == session.runner.digests()
    # y por eso no puede mostrar la cadena completa: la reversion corrige la ventilacion y la SpO2 no se mueve
    untreated, treated = series["untreated"][COMMITTED_RUN], series["naloxone"][COMMITTED_RUN]
    assert mc.untouched(treated["spo2"], untreated["spo2"])
    assert treated["paco2"][20] < untreated["paco2"][20]


def test_p3l_140e_the_ensemble_fails_closed_when_the_core_is_not_a_certified_lineage_member(monkeypatch):
    monkeypatch.setattr(ev, "core_lineage_ok", lambda: False)
    monkeypatch.setattr(ev, "core_lineage_reason", lambda: "probe: the live core is not in the lineage")
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        entry = encounter.order("Reassess in 5 minutes.")
    assert entry["executed"] is True                                   # el encuentro sigue igual
    record = encounter.shadow.record()
    ensemble = record["region_ensemble"]
    assert ensemble["witnesses"] == {} and ensemble["complete"] is False and ensemble["view"] == {}
    assert ensemble["refused"] == "probe: the live core is not in the lineage"
    assert [(f["where"], f["exception"]) for f in record["failures"]] == [
        ("ensemble:lineage", "CoreLineageNotCertified")]


def test_p3l_140f_the_ensemble_reads_copies_and_carries_no_authority(live):
    for arm, encounter in live.items():
        record = encounter.shadow.record()
        assert record["runtime_authority"] == "legacy" and record["common_core_runtime_authority"] is False
        ensemble = record["region_ensemble"]
        assert ensemble["runtime_authority"] == "legacy" and ensemble["resident_visible"] is False
        assert ensemble["common_core_runtime_authority"] is False
        json.dumps(record, default=str)                                # un artefacto, no un objeto vivo
        # nada de la sombra quedo en el estado del paciente
        assert "region_ensemble" not in json.dumps(encounter.state, default=str)
        assert not any("shadow" in str(key).lower() or "ensemble" in str(key).lower() for key in encounter.state)


# -- P3-141: el cableado ------------------------------------------------------------------------------------------

def test_p3l_141a_the_live_list_is_the_two_authorized_families_and_it_only_opens_a_shadow():
    assert rs.LIVE_FAMILIES == ("gi_bleed", "opioid") == rec.LIVE_WIRING["live_families"]
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False
    assert sorted(family for family, adapter in fam.ADAPTERS.items() if adapter.live) == ["gi_bleed", "opioid"]
    # la tupla la lee la funcion que decide si se abre una sesion de sombra, y nadie mas en toda la capa
    import pathlib
    root = pathlib.Path(rs.__file__).resolve().parent
    readers = {}
    for name in rs.LAYER_SOURCES + ("app.py", "pilot_acceptance.py", "family_engine.py"):
        text = (root / name).read_text(encoding="utf-8")
        if "LIVE_FAMILIES" in text:
            readers[name] = text.count("LIVE_FAMILIES")
    assert readers == {"runtime_shadow.py": 3}
    # la autoridad tiene su propia compuerta, que nombra una familia y no es esta
    assert ra.AUTHORITY_FAMILY == "gi_bleed" and "opioid" not in ra.AUTHORITY_CASES
    # y una lista pedida por entorno solo puede estrechar
    assert rs.live_families({**ON, rs.FAMILIES_FLAG: "opioid,acs"}) == ("opioid",)
    assert not rs.enabled_for("opioid", {**ON, rs.FAMILIES_FLAG: "gi_bleed"})


def test_p3l_141b_every_real_runtime_action_is_built_skipped_or_declared_never_dropped():
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        for text in (OXYGEN, NALOXONE, "Ventilate with bag-valve-mask.", NALOXONE, acceptance.UNMODELLED_ORDER,
                     "Stop the oxygen.", "Reassess in 5 minutes."):
            encounter.order(text)
    session = encounter.shadow
    kinds = [event.kind for event in session.mirrored]
    assert {"oxygen", "naloxone", "bag_mask", "reassessment"} <= set(kinds) and kinds.count("naloxone") == 2
    assert kinds.count("oxygen") == 2, "ponerlo y quitarlo son dos acciones de oxigeno"
    built, gaps = fam.ADAPTERS["opioid"].interventions(session.mirrored, None)
    skipped = [event for event in session.mirrored if event.kind in legacy_adapter.NOT_PHYSIOLOGICAL]
    assert len(session.mirrored) == len(built) + len(gaps) + len(skipped)
    # lo construido: dos oxigenos (el segundo devuelve el FiO2 a aire ambiente) y UNA reversion
    assert sorted(type(item).__name__ for item in built) == ["NaloxoneReversal", "Oxygen", "Oxygen"]
    fio2 = [event.fio2_after for event in session.mirrored if event.kind == "oxygen"]
    assert fio2[0] > 0.21 and fio2[-1] == 0.21
    # lo declarado: cada hueco con su tipo y su razon
    by_kind = {gap["kind"]: gap["why"] for gap in gaps}
    assert "bag-mask has no core target" in by_kind["bag_mask"]
    assert "the reversal already began" in by_kind["naloxone"]
    assert all(gap["why"] and gap["order_id"] for gap in gaps)
    # y el registro de la sesion los lleva, sin fallos: una dosis repetida ya no tumba el run
    record = session.record()
    assert record["failures"] == [] and {gap["kind"] for gap in record["gaps"]} == set(by_kind)
    assert record["region_ensemble"]["complete"] is True


def test_p3l_141c_no_adapter_drops_an_action_it_lists_as_mapped():
    """La guarda de regresion del defecto del ciclo anterior: oxigeno listado como mapeado y descartado."""
    oxygen = rs.MirroredAction("o1", 3, "oxygen", {"type": "oxygen"}, {}, 0.4)
    adapters = dict(fam.ADAPTERS)
    adapters.update({f"opioid:{name}": fam.OpioidAdapter.witness(name) for name in ORDER})
    adapters.update({f"pulmonary_edema:{name}": fam.PulmonaryEdemaAdapter.development(name)
                     for name in fam.EDEMA_DECONGESTION_WITNESSES})
    for label, adapter in adapters.items():
        assert "oxygen" in adapter.maps, label
        built, gaps = adapter.interventions([oxygen], None)
        assert [type(item).__name__ for item in built] == ["Oxygen"] and gaps == [], label
        assert built[0].fio2 == 0.4, label
    # y lo mismo para cada tipo que un adaptador sin metodo propio declare mapeado: construido o declarado
    for label, adapter in adapters.items():
        for kind in adapter.maps:
            if kind in ("oxygen", "fluid", "blood", "ppi", "reperfusion", "reperfusion_referral"):
                continue
            event = rs.MirroredAction("x1", 3, kind, {"type": kind}, {}, 0.21)
            built, gaps = adapter.interventions([event], None)
            assert len(built) + len(gaps) == 1, (label, kind)


def test_p3l_141d_a_witness_that_cannot_run_says_so_and_nothing_replaces_it():
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        encounter.order("Reassess in 5 minutes.")
        session = encounter.shadow
        broken = session.ensemble.runners["HIGH"]

        def refuse(mirrored, state=None):
            raise RuntimeError("probe: this witness cannot map its actions")
        broken.adapter.interventions = refuse
        entry = encounter.order(NALOXONE)
        encounter.wait_until(15)
    assert entry["executed"] is True and encounter.minute == 15            # el motor heredado no se entero
    record = session.record()
    where = [failure["where"] for failure in record["failures"]]
    assert where and set(where) == {"ensemble:HIGH:core"}
    ensemble = record["region_ensemble"]
    assert ensemble["complete"] is False
    # el testigo roto se queda en su ultimo minuto verdadero; los otros siguen; nadie ocupa su lugar
    assert len(ensemble["witnesses"]["HIGH"]["minutes"]) == 5
    assert len(ensemble["witnesses"]["LOW"]["minutes"]) == len(ensemble["witnesses"]["CENTER_REFERENCE"]["minutes"]) == 15
    assert ensemble["selected_witness"] is None
    # un mapeo que falla de plano tampoco puede reconstruir su artefacto: el registro lo dice y no se cae
    assert ensemble["witnesses"]["HIGH"]["replay_input"] is None
    assert "probe: this witness cannot map" in ensemble["witnesses"]["HIGH"]["artifact_error"]
    assert ensemble["witnesses"]["LOW"]["artifact_error"] is None
    assert session.replay()["region_ensemble"]["HIGH"] == []
    assert session.replay()["region_ensemble"]["LOW"] == session.ensemble.minutes()["LOW"]
    # la vista solo existe donde estan los tres
    assert set(ensemble["view"]["spo2"]) == {str(minute) for minute in range(1, 6)}
    # y el run comprometido de la sesion no se vio afectado
    assert len(record["minutes"]) == 15
    assert list(session.digests()) == [row["state_digest"] for row in session.replay()["minutes"]]


def test_p3l_141e_a_contributor_that_would_rewrite_a_recorded_minute_stops_the_run_loudly():
    runner = fam.ShadowPhysiologyRunner.open("opioid", CASE)
    assert runner.advance(10)
    recorded = runner.digests()
    # una accion fechada en el minuto 4, vista cuando el run ya registro hasta el 10: reescribiria el 5..10
    runner.mirror([rs.MirroredAction("late", 4, "naloxone", {"type": "naloxone"}, {}, 0.21)])
    assert runner.advance(20) is False
    assert runner.digests() == recorded and runner.minutes_done == 10
    failure = runner.failures[-1]
    assert (failure.where, failure.exception, failure.classification) == ("history", "HistoryRewritten",
                                                                           rs.UNEXPECTED)
    # una accion en el minuto 10, el ultimo registrado, NO reescribe nada: actua desde el 11
    clean = fam.ShadowPhysiologyRunner.open("opioid", CASE)
    assert clean.advance(10)
    clean.mirror([rs.MirroredAction("on-time", 10, "naloxone", {"type": "naloxone"}, {}, 0.21)])
    assert clean.advance(20) is True and clean.failures == [] and clean.digests()[:10] == recorded


def test_p3l_141f_a_family_with_no_golden_is_not_comparable_and_the_safety_readings_stay_loud(live):
    assert rs.golden_scenarios("gi_bleed") > 0 and rs.golden_scenarios("opioid") == 0
    statuses, reasons = set(), set()
    for encounter in live.values():
        for minute in encounter.shadow.minutes:
            for divergence in minute.divergences:
                statuses.add(divergence.status)
                if divergence.status == rs.NOT_COMPARABLE:
                    reasons.add(tuple(divergence.reasons))
    assert statuses <= {rs.NOT_COMPARABLE, rs.SAFETY_CRITICAL, rs.BOUNDARY} and rs.NOT_COMPARABLE in statuses
    assert reasons == {(rs.NO_GOLDEN,)}
    # el motor heredado detiene al paciente sin revertir y el nucleo no tiene transicion terminal: eso se ve
    arrested = live["untreated"]
    assert arrested.arrested and any(d.status == rs.SAFETY_CRITICAL and d.variable == "pulse_present"
                                     for m in arrested.shadow.minutes for d in m.divergences)
    assert rs.UNEXPECTED not in statuses


def test_p3l_141h_a_family_that_must_have_a_golden_is_not_excused_by_losing_it(monkeypatch):
    """Revision independiente: con el golden de GI ilegible, sus diferencias no pueden volverse silenciosas."""
    from clinical_core import comparison
    variable = next(item for item in comparison.VARIABLES if item.name == "fluid_delivered_ml")
    assert rs.GOLDEN_REQUIRED == ("gi_bleed",)
    monkeypatch.setattr(rs, "golden_scenarios", lambda family: 0)
    assert rs._classify(variable, 1.0, "gi_bleed") == rs.UNEXPECTED
    assert rs._classify(variable, 1.0, "opioid") == rs.NOT_COMPARABLE
    assert rs.classify(variable, 1.0, "opioid") == (rs.NOT_COMPARABLE, (rs.NO_GOLDEN,))
    # y las de seguridad y frontera van antes, en cualquier familia
    pulse = next(item for item in comparison.VARIABLES if item.name == "pulse_present")
    assert rs._classify(pulse, True, "opioid") == rs.SAFETY_CRITICAL
    assert rs._classify(variable, None, "opioid") == rs.BOUNDARY


def test_p3l_141i_a_comparison_that_fails_leaves_the_minute_recorded_once_and_the_clock_right(monkeypatch):
    """Revision independiente: una comparacion que levantaba dejaba minutos registrados y el reloj atras."""
    real, calls = fam.divergence_records, []

    def once(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("probe: the comparison could not be built")
        return real(*args, **kwargs)
    monkeypatch.setattr(fam, "divergence_records", once)
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        encounter.order("Reassess in 2 minutes.")
        encounter.order(NALOXONE)
        encounter.wait_until(12)
    session = encounter.shadow
    assert [(f.where, f.exception) for f in session.failures] == [("compare", "RuntimeError")]
    assert session.runner.minutes_done == 12
    assert [item.minute for item in session.runner.results] == list(range(1, 13)), "ni duplicados ni huecos"
    assert 2 not in session.runner.compared and 12 in session.runner.compared
    assert list(session.digests()) == [row["state_digest"] for row in session.replay()["minutes"]]


def test_p3l_141j_the_record_names_this_familys_own_committed_snapshot(live):
    """Revision independiente: el registro del opioide decia ``phase2_committed_default_profile``."""
    record = live["naloxone"].shadow.record()
    assert record["parameter_snapshot"] == "opioid_committed_default"
    assert record["versions"]["parameter_snapshot"] == "opioid_committed_default"
    assert record["replay_input"]["snapshot"]["id"] == "opioid_committed_default"
    assert rs.versions()["parameter_snapshot"] == rs.PARAMETER_SNAPSHOT_ID == "phase2_committed_default_profile"
    assert rs.family_versions("gi_bleed")["parameter_snapshot"] == rs.PARAMETER_SNAPSHOT_ID


def test_p3l_141k_a_session_run_whose_mapping_fails_outright_still_gives_a_record():
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter(CASE)
        encounter.order("Reassess in 3 minutes.")

    def refuse(mirrored, state=None):
        raise RuntimeError("probe: the session run cannot map its actions")
    session = encounter.shadow
    kept = session.runner.adapter.interventions
    session.runner.adapter.interventions = refuse
    try:
        record = session.record()
        replayed = session.replay()
    finally:
        del session.runner.adapter.interventions
        assert session.runner.adapter.interventions.__func__ is kept.__func__
    assert record["replay_input"] is None and record["replay_digest"] is None
    assert [(f["where"], f["exception"]) for f in record["failures"]][-1] == ("artifact", "RuntimeError")
    assert len(record["minutes"]) == 3 and replayed["minutes"] == []


def test_p3l_141g_every_artifact_names_its_own_adapter_and_the_certified_core(live):
    session = live["naloxone"].shadow
    for name, runner in _runners(session).items():
        versions = runner.replay_input().versions
        assert versions["adapter"] == "opioid/P3-141L" == runner.adapter.version, name
        assert versions["core_version"] == "PHASE2_AMENDMENT_1"
        assert versions["core_digest"] == rs.CORE_LINEAGE[-1].digest
        assert versions["phase2_digest"] == rs.PHASE2_DIGEST and versions["golden_digest"] == "missing"
    assert rs.family_versions("gi_bleed")["adapter"] == rs.ADAPTER_VERSION
    # y el registro de la sesion, igual: el del opioide nombra SU adaptador
    assert session.record()["versions"]["adapter"] == "opioid/P3-141L"
    assert session.record()["versions"]["golden_digest"] == "missing"
    assert ev.core_lineage_ok() is True


# -- P3-142: la serie de manejo en vivo ---------------------------------------------------------------------------

def test_p3l_142a_the_series_ran_on_the_engines_clock_with_real_action_objects(live):
    schedule = {arm: [(event.minute, event.kind) for event in encounter.shadow.mirrored
                      if event.kind not in legacy_adapter.NOT_PHYSIOLOGICAL]
                for arm, encounter in live.items()}
    assert schedule == {"untreated": [], "oxygen": [(0, "oxygen")], "naloxone": [(0, "naloxone")],
                        "oxygen_and_naloxone": [(0, "oxygen"), (0, "naloxone")],
                        "delayed_naloxone": [(10, "naloxone")], "wait": []}
    for arm, encounter in live.items():
        session = encounter.shadow
        assert session.failures == [] and session.gaps == [], arm
        assert session.runner.minutes_done == encounter.minute == ARMS[arm]["until"], arm
        # cada accion es un objeto del lector congelado, con la identidad del libro de ordenes
        for event in session.mirrored:
            assert event.action.get("type") == event.kind and event.submission_id is not None
        # el minuto de cada accion es el minuto de decision del turno que la ejecuto
        decided = {entry["decision_time_min"] for entry in encounter.entries if entry["executed"]}
        assert {event.minute for event in session.mirrored} <= decided
    # el motor heredado detiene al paciente sin revertir; quien recibe naloxona sigue vivo
    assert [arm for arm, encounter in live.items() if encounter.arrested] == ["untreated", "oxygen", "wait"]


@pytest.mark.parametrize("witness", ORDER)
def test_p3l_142b_untreated_the_impairment_runs_down_the_whole_chain(series, witness):
    row = series["untreated"][witness]
    for channel in ("central_availability", "respiratory_rate", "ventilation"):
        assert mc.monotone_after(row[channel], 1, rising=False) and row[channel][20] < row[channel][1], channel
    assert mc.monotone_after(row["paco2"], 1, rising=True) and row["paco2"][20] > row["paco2"][1]
    assert mc.monotone_after(row["spo2"], 1, rising=False) and row["spo2"][20] < row["spo2"][1]


@pytest.mark.parametrize("witness", ORDER)
def test_p3l_142c_oxygen_acts_on_the_oxygenation_path_and_corrects_no_ventilation(series, witness):
    base, treated = series["untreated"][witness], series["oxygen"][witness]
    assert mc.direction(treated["spo2"], base["spo2"], 20, better="higher")
    for channel in ("central_availability", "respiratory_rate", "ventilation", "paco2"):
        assert mc.untouched(treated[channel], base[channel]), channel
    # en el estado solo mueve el FiO2, un minuto despues de la orden (minuto 0 -> estado 1)
    assert _first_moved(treated, base) == {"fio2": 1}
    # y la falla ventilatoria sigue ahi mientras la cifra mejora
    assert treated["paco2"][20] > treated["paco2"][1] and treated["respiratory_rate"][20] < treated["respiratory_rate"][1]


@pytest.mark.parametrize("witness", ORDER)
def test_p3l_142d_naloxone_moves_the_central_availability_first_and_the_rest_downstream(series, witness):
    base, treated = series["untreated"][witness], series["naloxone"][witness]
    # el UNICO canal de estado que escribe es la disponibilidad central, desde el minuto 1
    assert _first_moved(treated, base) == {"central_availability": 1}
    onset = {channel: mc.effect_starts_at(treated[channel], base[channel], 1)
             for channel in ("central_availability", "respiratory_rate", "ventilation", "paco2", "spo2")}
    assert onset["central_availability"] <= onset["respiratory_rate"] <= onset["paco2"] <= onset["spo2"]
    assert treated["central_availability"][20] > base["central_availability"][20]
    assert mc.direction(treated["respiratory_rate"], base["respiratory_rate"], 20, better="higher")
    assert mc.direction(treated["ventilation"], base["ventilation"], 20, better="higher")
    assert treated["paco2"][20] < base["paco2"][20]
    assert mc.direction(treated["spo2"], base["spo2"], 20, better="higher")
    assert mc.no_paradox(treated["spo2"], base["spo2"], 1, better="higher")
    assert mc.monotone_after(treated["respiratory_rate"], 1, rising=True)


def test_p3l_142e_the_saturation_gain_of_the_reversal_is_ordered_by_the_witness(series):
    gains = [series["naloxone"][name]["spo2"][20] - series["untreated"][name]["spo2"][20] for name in ORDER]
    assert all(b > a > 0 for a, b in zip(gains, gains[1:])), gains
    # y en el run comprometido (el control negativo) es nula: no hay escritura directa naloxona -> SpO2
    assert series["naloxone"][COMMITTED_RUN]["spo2"][20] == series["untreated"][COMMITTED_RUN]["spo2"][20]


@pytest.mark.parametrize("witness", ORDER)
def test_p3l_142f_together_the_two_mechanisms_are_a_union(series, witness):
    both = series["oxygen_and_naloxone"][witness]
    oxygen, naloxone, base = series["oxygen"][witness], series["naloxone"][witness], series["untreated"][witness]
    # la rama ventilatoria es la de la naloxona sola, bit a bit
    for channel in ("central_availability", "respiratory_rate", "ventilation", "paco2"):
        assert mc.untouched(both[channel], naloxone[channel]), channel
    # el FiO2 es el del oxigeno solo
    assert mc.untouched(both["fio2"], oxygen["fio2"])
    assert both["spo2"][20] > max(oxygen["spo2"][20], naloxone["spo2"][20])
    assert _first_moved(both, base) == {"fio2": 1, "central_availability": 1}


@pytest.mark.parametrize("witness", ORDER)
def test_p3l_142g_a_delayed_reversal_preserves_history_and_costs_what_waiting_costs(live, series, witness):
    base, early, late = (series[arm][witness] for arm in ("untreated", "naloxone", "delayed_naloxone"))
    # nada antes del minuto efectivo: los diez primeros minutos son, estado por estado, los del brazo sin tratar
    runners = {arm: _runners(live[arm].shadow)[witness] for arm in ("untreated", "delayed_naloxone")}
    assert runners["delayed_naloxone"].digests()[:10] == runners["untreated"].digests()[:10]
    for channel in CHANNELS:
        assert mc.no_effect_before(late[channel], base[channel], 11), channel
    # la orden se ejecuto en el minuto 10 del motor y el primer estado que la lleva es el 11
    assert mc.effect_starts_at(late["central_availability"], base["central_availability"], 1) == 11
    # esperar cuesta: en la integral de la FR y de la SpO2, y deja mas carga de PaCO2
    for channel in ("respiratory_rate", "ventilation", "spo2"):
        assert _area(late[channel], 1, 60) < _area(early[channel], 1, 60), channel
    assert _area(late["paco2"], 1, 60) > _area(early["paco2"], 1, 60)
    assert mc.waiting_has_cost(early["respiratory_rate"], late["respiratory_rate"], 20, better="higher")


def test_p3l_142h_waiting_is_not_a_treatment(live):
    untreated, waited = live["untreated"].shadow, live["wait"].shadow
    assert [event.kind for event in waited.mirrored] == ["reassessment"] * len(waited.mirrored)
    assert len(waited.mirrored) > len(untreated.mirrored), "cuatro reevaluaciones cortas contra una larga"
    for name in (COMMITTED_RUN,) + ORDER:
        assert _runners(waited)[name].digests() == _runners(untreated)[name].digests(), name
    assert waited.gaps == [] and waited.failures == []


@pytest.mark.parametrize("arm", ["oxygen", "naloxone", "oxygen_and_naloxone", "delayed_naloxone"])
def test_p3l_142i_no_effect_before_the_minute_after_the_engine_executed_the_order(live, series, arm):
    """El minuto efectivo exacto: una orden ejecutada en el minuto m del motor aparece en el estado m + 1."""
    session = live[arm].shadow
    decided = min(event.minute for event in session.mirrored if event.kind not in legacy_adapter.NOT_PHYSIOLOGICAL)
    for name in (COMMITTED_RUN,) + ORDER:
        base, treated = series["untreated"][name], series[arm][name]
        first = min(_first_moved(treated, base).values())
        assert first == decided + 1, (arm, name, first)


def measure_live(series) -> dict:
    """Las lecturas de la serie en vivo que el registro guarda: cada testigo, sin promediar."""
    out = {}
    for name in ORDER:
        rows = {}
        for arm in ARMS:
            row = series[arm][name]
            last = max(row["spo2"])
            rows[arm] = {"minutes": last,
                         "at_20": {channel: row[channel][20] for channel in
                                   ("central_availability", "respiratory_rate", "paco2", "spo2")}}
            if last >= 60:
                rows[arm]["at_60"] = {channel: row[channel][60] for channel in
                                      ("central_availability", "respiratory_rate", "paco2", "spo2")}
        rows["respiratory_rate_area_1_60"] = {arm: _area(series[arm][name]["respiratory_rate"], 1, 60)
                                              for arm in ("naloxone", "delayed_naloxone")}
        out[name] = rows
    return out


def _rounded(value, places=4):
    if isinstance(value, dict):
        return {key: _rounded(item, places) for key, item in value.items()}
    return round(value, places) if isinstance(value, float) else value


def test_p3l_142j_the_recorded_series_is_what_the_live_runtime_gives_now(series):
    assert _rounded(measure_live(series)) == rec.MEASURED["live"]


# -- P3-143: vivo, fuera de linea y replay ------------------------------------------------------------------------

def _offline(session, name):
    """El mismo estado inicial sintetico y el mismo calendario de acciones, por el runner fuera de linea: sin
    sesion, sin motor, sin estado vivo, con identificadores de orden propios y de un solo golpe."""
    adapter = fam.ADAPTERS["opioid"] if name == COMMITTED_RUN else fam.OpioidAdapter.witness(name)
    runner = fam.ShadowPhysiologyRunner.open("opioid", CASE, adapter=None if name == COMMITTED_RUN else adapter)
    runner.mirror([rs.MirroredAction(f"offline-{index}", event.minute, event.kind, {"type": event.kind}, {},
                                     event.fio2_after)
                   for index, event in enumerate(session.mirrored)])
    assert runner.advance(session.runner.minutes_done)
    return runner


@pytest.mark.parametrize("arm", list(ARMS))
def test_p3l_143a_the_live_shadow_equals_the_offline_runner_state_for_state(live, arm):
    session = live[arm].shadow
    for name, runner in _runners(session).items():
        offline = _offline(session, name)
        # aceptacion de acciones: los mismos contribuidores y los mismos huecos
        assert [type(item).__name__ for item in offline.contributors()] == [
            type(item).__name__ for item in runner.contributors()], (arm, name)
        assert [gap["kind"] for gap in offline.gaps] == [gap["kind"] for gap in runner.gaps]
        # el estado comun, minuto a minuto: los digestos son los mismos aunque los identificadores no
        assert offline.digests() == runner.digests(), (arm, name)
        # y las lecturas derivadas, las mismas, en el mismo orden
        assert [item.derived for item in offline.results] == [item.derived for item in runner.results]
        assert [item.minute for item in offline.results] == list(range(1, session.runner.minutes_done + 1))


def test_p3l_143b_a_witness_adapter_is_the_offline_certified_configuration(live):
    """El testigo en vivo es exactamente el perfil que el ciclo anterior uso fuera de linea."""
    for name in ORDER:
        expected = dataclasses.replace(om.profile(), respiratory_quotient=R, **{FIELD: WITNESSES[name]})
        assert fam.OpioidAdapter.witness(name).profile(fam.COMMITTED) == expected
        assert live["naloxone"].shadow.ensemble.runners[name].profile == expected


@pytest.mark.parametrize("arm", list(ARMS))
def test_p3l_143c_every_run_replays_exactly_from_its_own_artifact(live, arm):
    session = live[arm].shadow
    replayed = session.replay()
    assert [row["state_digest"] for row in replayed["minutes"]] == list(session.digests())
    # cada testigo, entero: el digesto del estado Y el de las lecturas, minuto a minuto
    assert replayed["region_ensemble"] == session.ensemble.minutes()
    assert all(len(rows) == session.runner.minutes_done for rows in replayed["region_ensemble"].values())
    # y solo desde el artefacto, pasado por JSON: nada en memoria puede ayudarlo
    record = session.record()
    payloads = {COMMITTED_RUN: record["replay_input"],
                **{name: record["region_ensemble"]["witnesses"][name]["replay_input"] for name in ORDER}}
    for name, payload in payloads.items():
        again = fam.replay_shadow_encounter(json.loads(json.dumps(payload, default=str)))
        assert [row["state_digest"] for row in again["results"]][1:] == list(_runners(session)[name].digests())
        assert again["final_digest"] == _runners(session)[name].digests()[-1]


def test_p3l_143d_the_same_encounter_played_twice_is_the_same_artifact(live):
    for arm in ("delayed_naloxone", "oxygen_and_naloxone"):
        first, second = live[arm].shadow, _play(arm).shadow
        assert first.encounter_id == second.encounter_id
        for name in (COMMITTED_RUN,) + ORDER:
            a, b = _runners(first)[name], _runners(second)[name]
            assert a.digests() == b.digests() and a.replay_input().digest() == b.replay_input().digest()
        assert json.dumps(first.record(), sort_keys=True, default=str) == json.dumps(
            second.record(), sort_keys=True, default=str)


def test_p3l_143e_the_research_store_does_not_take_a_shadow_trace_and_says_so(live, tmp_path):
    """El almacen de artefactos existente guarda experimentos de autoridad y nada mas: no se amplio."""
    record = live["naloxone"].shadow.record()
    outcome = store.persist(record, environ={store.STORE_FLAG: str(tmp_path / "store")})
    assert outcome == {"stored": False, "why": store.NOT_AN_ARTIFACT}
    assert not (tmp_path / "store").exists()
    gate = next(row for row in rec.GATES if row["gate"] == "trace capture")
    assert gate["status"] == "PARTIAL" and "never persisted" in gate["blocker"]


def test_p3l_143f_where_the_states_coincide_the_readings_still_tell_the_witnesses_apart(live):
    """Con oxigeno, los cuatro runs llegan a los mismos estados y solo difieren en lo que leen. La revision
    independiente mostro que un replay comprobado solo por estados no distinguia un testigo de otro."""
    session = live["oxygen"].shadow
    states = {name: runner.digests() for name, runner in _runners(session).items()}
    assert len(set(states.values())) == 1, "con oxigeno los estados coinciden: por eso no bastan"
    minutes = session.ensemble.minutes()
    readings = {name: tuple(row["reading_digest"] for row in rows) for name, rows in minutes.items()}
    assert len(set(readings.values())) == 3
    # el artefacto de un testigo, rejugado con el perfil de otro, da los mismos estados y OTRAS lecturas
    record = session.record()["region_ensemble"]["witnesses"]
    swapped = json.loads(json.dumps(record["LOW"]["replay_input"], default=str))
    swapped["scenario"]["profile"] = json.loads(json.dumps(record["HIGH"]["replay_input"], default=str))[
        "scenario"]["profile"]
    again = fam.replay_shadow_encounter(swapped)["results"][1:]
    assert [row["state_digest"] for row in again] == [row["state_digest"] for row in minutes["LOW"]]
    assert [fam.reading_digest(row["derived"]) for row in again] != [row["reading_digest"] for row in minutes["LOW"]]
    assert [fam.reading_digest(row["derived"]) for row in again] == [row["reading_digest"] for row in minutes["HIGH"]]


# -- P3-144: la certificacion de seguridad de la segunda familia --------------------------------------------------

GI_RECORD_KEYS = ["case_id", "common_core_runtime_authority", "compared_minutes", "encounter_id", "failures",
                  "family", "gaps", "golden_scenario_counts", "minutes", "mirrored", "mode", "parameter_snapshot",
                  "replay_digest", "replay_input", "runtime_authority", "scenario_id", "versions"]


def test_p3l_144a_the_gi_live_shadow_is_what_it_was():
    with ev.shadow(rs.MODE_SHADOW_COMPARE):
        encounter = acceptance.Encounter("gi_bleed_57m")
        encounter.order("Give 1 liter of normal saline IV.")
        encounter.wait_until(30)
    session = encounter.shadow
    assert session.ensemble is None and session.failures == []
    record = session.record()
    assert sorted(record) == GI_RECORD_KEYS, "ni una clave nueva en el registro de GI"
    assert "region_ensemble" not in session.replay()
    assert list(session.digests()) == [row["state_digest"] for row in session.replay()["minutes"]]
    assert record["versions"]["adapter"] == rs.ADAPTER_VERSION
    # el clasificador de GI sigue leyendo su golden
    statuses = {d.status for m in session.minutes for d in m.divergences}
    assert rs.NOT_COMPARABLE not in statuses or rs.golden_scenarios("gi_bleed") > 0
    assert fam.ADAPTERS["gi_bleed"].region_witnesses() == {}


def test_p3l_144b_no_other_family_opens_a_session():
    for family in ("acs", "pulmonary_edema", "pulmonary_embolism", "asthma", "pneumonia", "trauma"):
        assert not rs.enabled_for(family, dict(ON)), family
        assert rs.ShadowSession.start({"engine_family": family, "sim_time": 0}, environ=dict(ON)) is None
    for variant in ("asthma_49m", "pulmonary_edema_58m", "acs_70f_left_main"):
        with ev.shadow(rs.MODE_SHADOW_COMPARE):
            assert acceptance.Encounter(variant).shadow is None, variant


@pytest.mark.parametrize("arm", list(ARMS))
def test_p3l_144c_the_authoritative_record_and_every_order_fate_are_the_same_on_and_off(live, arm):
    """Lo que ve el residente y lo que lee la puntuacion no cambian por correr la sombra del opioide."""
    on, off = live[arm], _play(arm, mode=None)
    assert off.shadow is None
    assert json.dumps(ev.authoritative(on), sort_keys=True, default=str) == json.dumps(
        ev.authoritative(off), sort_keys=True, default=str)
    assert ev.fates(on) == ev.fates(off)
    assert sorted(on.state) == sorted(off.state)


def test_p3l_144d_the_authority_gate_stays_shut_for_the_opioid_family():
    state = acceptance.Encounter(CASE).state
    asked = {ra.AUTHORITY_FLAG: ra.MODE_LIMITED_COMMON_AUTHORITY, **ON}
    gate = ra.gate(state, environ=asked, unsupported=())
    assert gate.conditions["family_and_case"] is False and gate.conditions["approved_snapshot"] is False
    assert not all(gate.conditions.values())
    assert ra.site_for(state, {}, environ=asked) is None
    assert rs.COMMON_CORE_RUNTIME_AUTHORITY is False and rec.LIVE_WIRING["common_core_runtime_authority"] is False


def test_p3l_144e_without_the_flag_an_opioid_encounter_is_exactly_the_engine():
    """El camino del primer piloto: ninguna bandera, ninguna sesion, ningun digesto, ninguna clave."""
    assert not rs.enabled_for("opioid", {})
    encounter = _play("naloxone", mode=None)
    assert encounter.shadow is None
    assert rs.ShadowSession.start(encounter.state, environ={}) is None
    assert rs.mode({rs.FLAG: "authority"}) == rs.MODE_OFF


def test_p3l_144f_one_family_never_runs_through_another_familys_mapping(live):
    witness = fam.OpioidAdapter.witness("LOW")
    assert fam.ShadowPhysiologyRunner.open("gi_bleed", "gi_bleed_57m", adapter=witness) is None
    assert fam.ShadowPhysiologyRunner.open("opioid", "gi_bleed_57m") is None
    assert fam.ShadowPhysiologyRunner.open("opioid", "opioid_35m", adapter=fam.ADAPTERS["gi_bleed"]) is None
    assert fam.RegionEnsemble.open("gi_bleed", "gi_bleed_57m") is None
    for encounter in live.values():
        for runner in _runners(encounter.shadow).values():
            assert runner.adapter.family == "opioid" and runner.case_id == CASE
    # y un mismo caso, dos encuentros: el segundo no hereda la sesion del primero
    first = live["naloxone"].shadow
    fresh = acceptance.Encounter(CASE).state
    assert first.is_for(fresh) is False


def test_p3l_144g_the_previous_live_family_and_the_layer_identity_are_reported():
    versions = rs.versions()
    assert versions["core_version"] == "PHASE2_AMENDMENT_1" and versions["phase3_module"] == "P3-11"
    assert rs.MODULE_VERSION == ra.EXPECTED_LAYER
    assert rec.LIVE_WIRING["adapter"] == fam.ADAPTERS["opioid"].version
    assert len(rec.LIVE_WIRING["defects_found_and_corrected"]) == 5
    review = rec.LIVE_WIRING["independent_review"]
    assert [row["id"] for row in review["found_and_corrected"]] == ["R1", "R2", "R3", "R4", "R6", "R7"]
    assert [row["severity"] for row in review["found_and_corrected"]].count("MEDIUM") == 1
    assert [row["id"] for row in review["found_and_declared"]] == ["R5", "R8", "R9", "R10"]


# -- P3-145 y P3-146: compuertas, dos preguntas de preparacion y punto de control -------------------------------

GATE_STATES = {"GREEN", "PARTIAL", "BLOCKED", "NOT_YET_EVALUATED"}
NINE = ("runtime exposure", "UI exposure", "trace capture", "scoring isolation", "faculty review workflow",
        "case selection", "failure visibility", "rollback", "resident-facing safety")


def test_p3l_145a_the_nine_gates_are_classified_with_their_evidence():
    assert tuple(row["gate"] for row in rec.GATES) == NINE
    counts = {}
    for row in rec.GATES:
        assert row["status"] in GATE_STATES and row["evidence"], row["gate"]
        assert (row["blocker"] is None) == (row["status"] == "GREEN"), row["gate"]
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    assert counts == rec.READINESS["RESIDENT_PILOT_DEPLOYMENT_READINESS"]["gates"]
    # lo que se puede leer del repositorio, se lee: ninguna pantalla nombra el conjunto ni la traza de sombra
    import pathlib
    app = (pathlib.Path(rs.__file__).resolve().parent / "app.py").read_text(encoding="utf-8")
    assert "region_ensemble" not in app and "research_trace" not in app
    assert app.count("phase3_shadow") == 3


def test_p3l_145b_the_two_readiness_questions_are_kept_apart():
    engine = rec.READINESS["SIMULATION_ENGINE_READINESS"]
    pilot = rec.READINESS["RESIDENT_PILOT_DEPLOYMENT_READINESS"]
    assert engine["verdict"] == "SECOND_FAMILY_LIVE_SHADOW_VALIDATED_FOR_DEVELOPMENT"
    assert pilot["verdict"] == "NOT_READY_FOR_RESIDENT_PILOT_REVIEW"
    assert engine["does_not_hold"] and pilot["gates"]["BLOCKED"] >= 1


def test_p3l_145c_the_future_pilot_ranking_follows_its_own_scores_and_selects_nothing():
    ranking = rec.FUTURE_PILOT_RANKING
    totals = {family: sum(row[name] for name in ranking["criteria"]) for family, row in ranking["families"].items()}
    assert list(ranking["order"]) == sorted(totals, key=lambda family: -totals[family])
    assert len(set(totals.values())) == len(totals), "sin empates escondidos"
    assert ranking["is_a_selection"] is False and ranking["strongest_future_candidate"] == ranking["order"][0]


def test_p3l_146_the_checkpoint_says_what_was_validated_and_what_was_not():
    checkpoint = rec.CHECKPOINT
    assert checkpoint["engine_verdict"] == "A_SECOND_FAMILY_LIVE_SHADOW_VALIDATED"
    assert checkpoint["pilot_verdict"] == "NOT_READY_FOR_RESIDENT_PILOT_REVIEW"
    assert len(checkpoint["remaining_blockers"]) >= 5 and "clinical validation" in checkpoint["not_claimed"]
    milestone = rec.MILESTONE
    assert list(milestone["pathways"]) == ["gi_bleed", "acs", "opioid", "pulmonary_edema"]
    assert milestone["pathways"]["acs"]["where"] == "OFFLINE"
    assert milestone["implies_live_runtime_readiness"] is False and milestone["is_clinical_validation"] is False
    # las decisiones docentes, tal como se dieron
    one = rec.FACULTY_DECISIONS["FD-NEW-1"]
    assert one["mathematical_development_region"] == fam.TRANSMISSION_MATHEMATICAL_REGION == (0.0, 0.060621)
    assert one["active_causal_development_region"]["above"] == fam.TRANSMISSION_ACTIVE_REGION["above"] == 0.0
    assert one["witnesses"] == WITNESSES and one["center_reference_is_preferred"] is False
    assert one["confidence"] == 0.84 and rec.FACULTY_DECISIONS["FD-NEW-2"]["confidence"] == 0.82
    assert rec.FACULTY_DECISIONS["FD-NEW-2"]["region"] == fam.EDEMA_DECONGESTION_REGION
    assert rec.STATUS == "SECOND_FAMILY_LIVE_SHADOW_DEVELOPMENT_NO_AUTHORITY"
