"""The ward's own orders work in a generated case too.

Playing the first paid case (2026-09-22) showed how much smaller the simulator
is on the generated path: a resident who writes "instala una via venosa" or
"administra paracetamol 1 g IV" lost the whole turn to "outside the main/IA
core", while the same words work in the bank. Neither of those needs a declared
mechanism — one changes no physiology at all, and the other acts on a
temperature the core already observes.
"""
import copy

import pytest

import antipyretics
import coupled_encounter as adapter
from family_parser import parse_family_actions
from generated_engine import execute_generated_bundle
from test_generated_metabolic import build, minutes, order


def fresh():
    state, _ = build()
    adapter.initialize(state)
    return state


def run(state, text):
    return execute_generated_bundle(state, parse_family_actions(text))


REASONED = ("{body} Espero el efecto que corresponda. Reevalua en 10 minutos presion y estado mental.")


@pytest.mark.parametrize("text", [
    "Instala una via venosa periferica gruesa, porque necesito un acceso seguro. La prioridad ahora es el acceso.",
    "Instala monitor y oximetria, porque necesito vigilancia continua. La prioridad ahora es monitorizar.",
    "Instala sonda Foley, porque quiero medir diuresis. La prioridad ahora es medir.",
    "Deja regimen cero, porque puede requerir procedimiento. La prioridad ahora es la seguridad.",
    "Pon una sonda nasogastrica, porque la indicacion lo requiere. La prioridad ahora es descomprimir.",
])
def test_a_nursing_order_no_longer_costs_the_turn(text):
    state = fresh()
    result = run(state, REASONED.format(body=text))
    assert result["executed"], result.get("clarification")


def test_a_nursing_order_changes_no_physiology():
    # Against a control that only lets the same ten minutes pass: whatever the
    # core does on its own, the nursing order adds nothing to it.
    watched, control = fresh(), fresh()
    run(watched, REASONED.format(body="Instala monitor y oximetria, porque necesito vigilancia. "
                                      "La prioridad ahora es monitorizar."))
    run(control, "Observo, porque quiero el curso sin intervenir. La prioridad ahora es reevaluar. "
                 "Espero el curso natural. Reevalua en 10 minutos presion y estado mental.")
    for field in ("sbp", "dbp", "hr", "spo2", "respiratory_rate"):
        assert watched["observable"][field] == control["observable"][field], field


def test_the_ward_antipyretic_runs_without_a_declared_mechanism():
    state = fresh()
    result = run(state, "Fiebre con foco poco claro, porque hay inflamacion. La prioridad ahora es el "
                        "confort. Administra paracetamol 1 g IV. Espero que baje la fiebre. "
                        "Reevalua en 30 minutos temperatura.")
    assert result["executed"], result.get("clarification")
    assert any(record.get("agent") == "paracetamol"
               for record in state["treatments"].get("administered_medications", []))


def test_the_fall_is_measured_against_the_baseline_the_projection_uses():
    # The bug this guards: reading the baseline from the case while the
    # projection adds the delta to its own would cool a patient who has no
    # fever at all, which decision 14 forbids.
    state, case = build()
    for target in (case["observable"], state["observable"]):
        target["temperature_c"] = 36.6          # no fever at all
    if "temperature" in case.get("investigations", {}):
        case["investigations"]["temperature"]["result"]["temperature_c"] = 36.6
    adapter.initialize(state)
    baseline = state["generated_state"]["baseline_values"]["temperature_c"]
    assert baseline == pytest.approx(36.6, abs=.05)
    run(state, "Sin fiebre, porque la temperatura es normal. La prioridad ahora es el confort. "
               "Administra paracetamol 1 g IV. Espero ningun cambio. Reevalua en 30 minutos temperatura.")
    assert state["observable"]["temperature_c"] == pytest.approx(baseline, abs=.05)
    assert antipyretics.temperature_drop(state["family_state"], baseline) == 0.0


def test_a_fever_does_come_down_and_comes_back():
    f = {"elapsed": 45, "antipyretic_doses": [
        {"agent": "paracetamol", "mg": 1000, "route": "IV", "at": 0, "onset": 20, "share": 1.0}]}
    assert antipyretics.temperature_drop(f, 39.0) > .5
    assert antipyretics.temperature_drop({**f, "elapsed": 300}, 39.0) < .3
    assert antipyretics.temperature_drop(f, 36.8) == 0.0


def test_what_still_belongs_to_the_bank_says_so_clearly():
    # Morphine, atropine and pacing carry physiology the generated engine does
    # not render yet. They are refused, and the message says why.
    state = fresh()
    result = run(state, "Dolor intenso, porque hay isquemia. La prioridad ahora es la analgesia. "
                        "Indica morfina 4 mg IV. Espero menos dolor. Reevalua en 10 minutos el dolor.")
    assert not result["executed"]
    assert "outside the main/IA core" in result["clarification"]


# A declared coronary brings its own block, and the treatments for it.

def coronary_case():
    state, case = build(coronary={"omi": True, "territory": "inferior", "rv_involvement": True,
                                  "pci_capable": True, "symptom_onset_min": 60, "active_occlusion": True})
    case["ecg_profile"] = "inferior_stemi"
    adapter.initialize(state)
    return state


@pytest.mark.parametrize("text", [
    "Bloqueo AV con hipotension, porque el infarto tomo el nodo. La prioridad ahora es la frecuencia. "
    "Administra atropina 1 mg IV. Espero mas frecuencia. Reevalua en 10 minutos ritmo y presion.",
    "El bloqueo persiste, porque es isquemico. La prioridad ahora es estimular. Instala un marcapasos "
    "transcutaneo a 70 por minuto con 90 mA. Espero captura. Reevalua en 10 minutos ritmo y presion.",
])
def test_the_block_a_coronary_makes_can_be_treated_in_either_engine(text):
    result = run(coronary_case(), text)
    assert result["executed"], result.get("clarification")


def test_without_a_coronary_they_are_still_refused():
    result = run(fresh(), "Bradicardia, porque si. La prioridad ahora es la frecuencia. "
                          "Administra atropina 1 mg IV. Espero mas frecuencia. Reevalua en 10 minutos frecuencia.")
    assert not result["executed"]
    assert "outside the main/IA core" in result["clarification"]


def test_the_rate_the_block_costs_comes_back_with_the_treatment():
    import acs_reperfusion as acs
    spec = {"territory": "inferior", "rv_involvement": True}
    blocked = {"elapsed": 60, "av_block_at": 50, "circulation": 1.0}
    treated = {**blocked, "atropine_doses": [{"index": 0, "at": 55, "dose_mg": 1}]}
    paced = {**blocked, "pacing_rate": 70, "pacing_ma": 90}
    spikes = {**blocked, "pacing_rate": 70, "pacing_ma": 50}
    assert acs.generated_effects(blocked, spec)[2] == pytest.approx(acs.AV_BLOCK_HR_DELTA)
    assert acs.generated_effects(treated, spec)[2] == pytest.approx(0, abs=.01)
    assert acs.generated_effects(paced, spec)[2] == pytest.approx(0, abs=.01)
    # Spikes without capture give nothing back, in either engine.
    assert acs.generated_effects(spikes, spec) == acs.generated_effects(blocked, spec)


def test_the_additional_leads_are_recordable_when_a_coronary_is_declared():
    state = coronary_case()
    result = run(state, "Infarto inferior, porque hay supradesnivel. La prioridad ahora es descartar "
                        "compromiso del VD. Pide un electrocardiograma con derivadas derechas. "
                        "Espero ver V4R. Reevalua en 10 minutos presion.")
    assert result["executed"], result.get("clarification")
    reports = [s for s in result["action_summaries"] if s.get("diagnostic_type") == "ecg_right"]
    assert reports and "V4R" in reports[0]["result"]["report"]


def test_without_a_coronary_the_additional_leads_are_asked_for_and_not_invented():
    """Until 2026-09-24 the whole order was refused as "unavailable". The
    request is now recorded as not modelled in this version of the simulator,
    the rest runs, and no V4R is invented for a heart nobody declared."""
    from family_engine import STUDY_NOT_PERFORMED
    result = run(fresh(), "Quiero descartar compromiso derecho, porque la presion esta baja. La prioridad "
                          "ahora es registrar. Pide un electrocardiograma con derivadas derechas. "
                          "Espero ver V4R. Reevalua en 10 minutos presion.")
    assert result["executed"], result.get("clarification")
    [asked] = [s for s in result["action_summaries"] if s.get("type") == STUDY_NOT_PERFORMED]
    assert asked["diagnostic"] == "ecg_right" and asked["not_performed"] == "not_modeled"
    assert not [s for s in result["action_summaries"] if s.get("diagnostic_type") == "ecg_right"]
    assert "unavailable" not in asked["label"].lower()
