"""Eleven scripted encounters, played through the real engine, for the rubric pilot.

Nothing here writes a trace by hand. Each encounter is played offline through
the production interpreter and engine, so the record carries the engine's own
interpretation, its own consequences and its own clock. The scripts below are
the learner's side only.

``MRS_OFFLINE_CASES=1`` is set before anything is imported, so the provider key
is withheld at every resolver and playing an encounter costs nothing. A paid
request is made only by ``--propose``, one per encounter, and never while a
record is being built.

    python tools_rubric_runs.py --list
    python tools_rubric_runs.py --play asthma_24f
    python tools_rubric_runs.py --propose asthma_24f --yes     # ONE paid call
"""
import os
import sys

os.environ.setdefault("MRS_OFFLINE_CASES", "1")

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _script(case_id, family, intent, orders, *, reflection, plan, closed_min=None):
    return {"case_id": case_id, "family": family, "intent": intent, "orders": orders,
            "reflection": reflection, "plan": plan, "closed_min": closed_min}


# Each entry is one learner submission, in the learner's own words. The
# reasoning fields the interpreter recognises are written the way a resident
# writes them, not as form fields.
SCRIPTS = [
    _script(
        "asthma_24f", "asthma",
        "Competent management, no defined event should be proposed.",
        [
            "Examino la respiracion",
            "Creo que es una crisis asmatica severa, porque tiene sibilancias difusas, "
            "habla en frases cortas y satura 90% con 34 respiraciones por minuto. Mi "
            "prioridad es broncodilatar y oxigenar antes de completar el estudio. Doy "
            "salbutamol 5 mg nebulizado; doy ipratropio 0.5 mg nebulizado; doy oxigeno "
            "por mascarilla a 6 L/min. Espero que baje el trabajo respiratorio y que la "
            "saturacion suba sobre 94%. Reevaluo en 15 minutos.",
            "Doy hidrocortisona 200 mg ev; pido gases arteriales; pido radiografia de torax",
            "Sigue con trabajo respiratorio aumentado pese a la primera nebulizacion. Mi "
            "prioridad es sumar un broncodilatador de segunda linea sin demorar. Doy "
            "sulfato de magnesio 2 g ev en 20 minutos. Espero que mejore la mecanica "
            "ventilatoria. Reevaluo en 20 minutos.",
            "Examino la respiracion",
            "La paciente mejoro el trabajo respiratorio y la saturacion. Mi prioridad es "
            "decidir el destino con la respuesta observada. La hospitalizo en sala para "
            "continuar broncodilatadores y corticoides. Espero que no vuelva a caer la "
            "saturacion. Reevaluo en 30 minutos.",
        ],
        reflection={
            "working_model_update": "La severidad estaba en el esfuerzo y el habla, no en un numero.",
            "priority_trigger": "Una caida de la saturacion o un torax silencioso me habrian hecho escalar.",
            "alternative_action": "Podria haber iniciado nebulizacion continua desde el inicio.",
            "expected_response_reassessment": "Volveria a examinar la respiracion y a medir la saturacion.",
        },
        plan={"next_priority": "Declarar antes el umbral que me haria escalar a soporte ventilatorio."},
    ),
    _script(
        "asthma_49m", "asthma",
        "Bronchodilator and steroid given; ventilatory failure never supported. "
        "Expect asthma_no_ventilatory_support.",
        [
            "Creo que es una crisis asmatica, porque tiene sibilancias y usa musculatura "
            "accesoria. Mi prioridad es broncodilatar. Doy salbutamol 5 mg nebulizado; doy "
            "ipratropio 0.5 mg nebulizado. Espero que ceda la obstruccion. Reevaluo en 20 minutos.",
            "Pido gases arteriales; pido radiografia de torax",
            "Doy hidrocortisona 200 mg ev",
            "Sigue somnoliento y cansado. Mi prioridad es insistir con el broncodilatador. "
            "Doy salbutamol 5 mg nebulizado. Espero que mejore la ventilacion. Reevaluo en 20 minutos.",
            "Lo hospitalizo en sala",
        ],
        reflection={
            "working_model_update": "Era una obstruccion severa que no respondio.",
            "priority_trigger": "Una apnea me habria hecho intubar.",
            "alternative_action": "Habria repetido los gases antes.",
            "expected_response_reassessment": "Miraria la saturacion.",
        },
        plan={"next_priority": "Reconocer antes la fatiga ventilatoria."},
    ),
    _script(
        "gi_bleed_57m", "gi_bleed",
        "Competent resuscitation of a bleeding patient; no defined event should be proposed.",
        [
            "Creo que es una hemorragia digestiva alta con hipoperfusion, porque tiene "
            "melena, presion 88/54, frecuencia 124 y llene capilar de 5 segundos. Mi "
            "prioridad es reponer volumen antes de completar el estudio. Instalo dos vias "
            "venosas perifericas; paso suero fisiologico 500 ml ev en bolo. Espero que "
            "suba la presion y mejore la perfusion. Reevaluo en 10 minutos.",
            "Pido hemoglobina; pido laboratorio basico; pido lactato",
            "Sigue hipotenso y mal perfundido despues del cristaloide. Mi prioridad es "
            "restituir capacidad de transporte de oxigeno. Transfundo 2 unidades de "
            "globulos rojos; doy omeprazol 80 mg ev. Espero que suba la presion y baje la "
            "frecuencia. Reevaluo en 15 minutos.",
            "Examino la perfusion periferica",
            "Consulto a gastroenterologia para endoscopia urgente",
            "Mejoro la perfusion con la transfusion pero sigue taquicardico. Mi prioridad "
            "es que la hemostasia ocurra pronto y en un lugar monitorizado. Lo hospitalizo "
            "en unidad de cuidados intermedios. Espero que no vuelva a sangrar antes de la "
            "endoscopia. Reevaluo en 30 minutos.",
        ],
        reflection={
            "working_model_update": "La primera hemoglobina no reflejaba toda la perdida.",
            "priority_trigger": "Una nueva caida de presion me habria hecho activar transfusion masiva.",
            "alternative_action": "Podria haber transfundido antes del cristaloide.",
            "expected_response_reassessment": "Volveria a medir presion, frecuencia y llene capilar.",
        },
        plan={"next_priority": "Pedir la endoscopia en la misma entrega que la transfusion."},
    ),
    _script(
        "gi_bleed_72f", "gi_bleed",
        "A quiet presentation investigated but never resuscitated. Expect gi_no_resuscitation.",
        [
            "Creo que tiene una anemia por perdida digestiva, porque refiere deposiciones "
            "negras hace dias y usa naproxeno. Mi prioridad es confirmarlo con examenes. "
            "Pido hemoglobina; pido laboratorio basico. Espero una hemoglobina baja. "
            "Reevaluo en 20 minutos.",
            "Examino el abdomen",
            "Pido lactato; pido gases venosos",
            "La hemoglobina confirma anemia. Mi prioridad es que la vea gastroenterologia. "
            "Consulto a gastroenterologia. Espero que programen una endoscopia. Reevaluo en 20 minutos.",
            "La hospitalizo en sala",
        ],
        reflection={
            "working_model_update": "Era una hemorragia digestiva cronica.",
            "priority_trigger": "Una hipotension franca me habria hecho transfundir.",
            "alternative_action": "Habria pedido antes la hemoglobina.",
            "expected_response_reassessment": "Miraria la hemoglobina de control.",
        },
        plan={"next_priority": "Definir un umbral de transfusion por adelantado."},
    ),
    _script(
        "hypoglycemia_54m_thiamine", "hypoglycemia",
        "Glucose corrected in a thiamine-depleted patient, thiamine never given. "
        "Expect hypo_no_thiamine and not hypo_no_glucose.",
        [
            "Creo que es una hipoglicemia sintomatica, porque esta somnoliento con glicemia "
            "capilar de 32 mg/dL. Mi prioridad es corregir la glicemia de inmediato. "
            "Instalo una via venosa periferica; doy glucosa 25 g ev. Espero que recupere "
            "la conciencia y suba la glicemia. Reevaluo en 10 minutos.",
            "Pido glicemia capilar; pido laboratorio basico",
            "Examino el estado neurologico",
            "Recupero la conciencia y la glicemia subio. Mi prioridad es evitar que vuelva "
            "a caer. Inicio infusion de glucosa al 10% a 100 ml/h. Espero que la glicemia "
            "se mantenga sobre 100 mg/dL. Reevaluo en 30 minutos.",
            "Lo hospitalizo en sala para observacion",
        ],
        reflection={
            "working_model_update": "La hipoglicemia venia del ayuno prolongado y el alcohol.",
            "priority_trigger": "Una nueva caida de glicemia me habria hecho subir la infusion.",
            "alternative_action": "Habria pedido antes el laboratorio.",
            "expected_response_reassessment": "Volveria a medir la glicemia capilar.",
        },
        plan={"next_priority": "Revisar el estado nutricional antes de dar glucosa."},
    ),
    _script(
        "hypoglycemia_76f", "hypoglycemia",
        "Sulfonylurea hypoglycaemia corrected and sent home. Expect hypo_unsafe_discharge.",
        [
            "Creo que es una hipoglicemia, porque esta obnubilada con glicemia capilar de "
            "38 mg/dL. Mi prioridad es corregirla ahora. Instalo una via venosa periferica; "
            "doy glucosa 25 g ev. Espero que despierte. Reevaluo en 10 minutos.",
            "Pido glicemia capilar",
            "Examino el estado neurologico",
            "Desperto y la glicemia esta normal. Mi prioridad es liberar el box. La envio a "
            "su casa con indicacion de comer. Espero que no se repita. Reevaluo en 15 minutos.",
        ],
        reflection={
            "working_model_update": "Era una hipoglicemia por mala ingesta.",
            "priority_trigger": "Un nuevo episodio me habria hecho hospitalizarla.",
            "alternative_action": "Habria revisado la lista de medicamentos.",
            "expected_response_reassessment": "Le pediria control con su medico.",
        },
        plan={"next_priority": "Preguntar siempre que hipoglicemiante toma."},
    ),
    _script(
        "opioid_35m", "opioid",
        "Competent: ventilation supported before the antagonist, titrated to breathing.",
        [
            "Creo que es una depresion ventilatoria por opioides, porque respira 6 por "
            "minuto, esta obnubilado y satura 80% tras tomar un comprimido desconocido. Mi "
            "prioridad es la ventilacion antes que el diagnostico. Ventilo con bolsa "
            "mascarilla con oxigeno al 100%. Espero que suba la saturacion sobre 94%. "
            "Reevaluo en 5 minutos.",
            "Creo que la causa es opioide. Mi prioridad es revertir sin provocar "
            "abstinencia. Doy naloxona 0.4 mg ev. Espero que suba la frecuencia "
            "respiratoria sobre 12 por minuto. Reevaluo en 5 minutos.",
            "Pido gases arteriales; pido glicemia capilar",
            "Examino el estado neurologico",
            "Recupero la frecuencia respiratoria y el estado de conciencia. Mi prioridad es "
            "vigilar la re-narcotizacion porque el comprimido es de contenido desconocido. "
            "Lo hospitalizo en cuidados intermedios para observacion monitorizada. Espero que no vuelva a deprimirse. "
            "Reevaluo en 30 minutos.",
        ],
        reflection={
            "working_model_update": "El efecto del toxico puede durar mas que la naloxona.",
            "priority_trigger": "Una caida de la frecuencia respiratoria me habria hecho repetir la naloxona.",
            "alternative_action": "Podria haber dejado una infusion de naloxona.",
            "expected_response_reassessment": "Volveria a contar la frecuencia respiratoria.",
        },
        plan={"next_priority": "Dejar escrito el umbral de re-dosis de naloxona."},
    ),
    _script(
        "opioid_67f", "opioid",
        "Ventilation supported and reversed, then sent home on the response to the first "
        "dose. The second unsafe discharge: expect opioid_unsafe_discharge.",
        [
            "Creo que es una depresion ventilatoria por opioides, porque respira 8 por minuto, "
            "esta obnubilada y satura 84%. Mi prioridad es la ventilacion antes que el "
            "diagnostico. Ventilo con bolsa mascarilla con oxigeno al 100%. Espero que suba la "
            "saturacion sobre 94%. Reevaluo en 5 minutos.",
            "Mi prioridad es revertir el efecto opioide. Doy naloxona 0.4 mg ev. Espero que "
            "suba la frecuencia respiratoria sobre 12 por minuto. Reevaluo en 5 minutos.",
            "Pido gases arteriales; pido glicemia capilar",
            "Examino el estado neurologico",
            "Desperto, respira bien y esta orientada. Mi prioridad es liberar el box. La envio "
            "a su casa con indicacion de volver si se repite. Espero que no vuelva a pasar. "
            "Reevaluo en 15 minutos.",
        ],
        reflection={
            "working_model_update": "Era una depresion ventilatoria por opioides.",
            "priority_trigger": "Una nueva caida de la frecuencia respiratoria me habria hecho repetir la naloxona.",
            "alternative_action": "Habria revisado que opioide tomaba.",
            "expected_response_reassessment": "Le pediria control con su medico.",
        },
        plan={"next_priority": "Preguntar siempre que opioide y en que formulacion."},
    ),
    _script(
        "pneumonia_83m", "pneumonia",
        "Pneumonia treated well; the new confusion never investigated. "
        "Expect pneumonia_unexamined_altered_state and not pneumonia_no_antibiotic.",
        [
            "Creo que es una neumonia con hipoperfusion, porque tiene tos nueva, fiebre "
            "37.8, satura 91% y tiene llene capilar de 4 segundos. Mi prioridad es "
            "antibiotico precoz y oxigeno. Doy ceftriaxona 2 g ev; doy oxigeno por naricera "
            "a 4 L/min. Espero que suba la saturacion y baje la frecuencia respiratoria. "
            "Reevaluo en 20 minutos.",
            "Paso suero fisiologico 500 ml ev en bolo",
            "Pido radiografia de torax; pido lactato; pido hemocultivos",
            "Sigue mal perfundido. Mi prioridad es completar la reanimacion con volumen. "
            "Paso suero fisiologico 500 ml ev en bolo. Espero que mejore el llene capilar. "
            "Reevaluo en 20 minutos.",
            "Lo hospitalizo en sala",
        ],
        reflection={
            "working_model_update": "Era una neumonia con compromiso sistemico.",
            "priority_trigger": "Una caida de presion me habria hecho usar vasoactivos.",
            "alternative_action": "Habria pedido antes el lactato.",
            "expected_response_reassessment": "Miraria la saturacion y el llene capilar.",
        },
        plan={"next_priority": "Repetir el lactato antes de decidir el destino."},
    ),
    _script(
        "pulmonary_edema_58m", "pulmonary_edema",
        "Correct support and nitrate, then a fluid bolus for the tachycardia. "
        "Expect edema_volume_loading and not edema_no_ventilatory_support.",
        [
            "Creo que es un edema pulmonar agudo hipertensivo, porque tiene ortopnea, "
            "expectoracion rosada, presion 218/116 y satura 81%. Mi prioridad es soportar "
            "la ventilacion y bajar la postcarga. Inicio ventilacion no invasiva con CPAP 8 "
            "y FiO2 60%; inicio nitroglicerina en infusion a 50 mcg/min ev. Espero que baje "
            "el trabajo respiratorio y suba la saturacion. Reevaluo en 10 minutos.",
            "Pido POCUS; pido radiografia de torax; pido gases arteriales",
            "Doy furosemida 40 mg ev",
            "Sigue taquicardico a 120 por minuto. Mi prioridad es mejorar el gasto "
            "cardiaco. Paso suero fisiologico 500 ml ev en bolo. Espero que baje la "
            "frecuencia cardiaca. Reevaluo en 15 minutos.",
            "Lo hospitalizo en unidad coronaria",
        ],
        reflection={
            "working_model_update": "Era una congestion por crisis hipertensiva.",
            "priority_trigger": "Una caida de presion me habria hecho bajar la nitroglicerina.",
            "alternative_action": "Habria evitado el volumen.",
            "expected_response_reassessment": "Miraria la saturacion y la presion.",
        },
        plan={"next_priority": "No dar volumen a un paciente congestivo."},
    ),
    _script(
        "acs_52m_de_winter", "acs",
        "An occlusion equivalent: aspirin given, reperfusion never arranged, and the "
        "encounter closes at minute 15. Probes the not-assessable boundary on D5.",
        [
            "Creo que es un sindrome coronario agudo, porque tiene dolor toracico opresivo "
            "de 40 minutos con sudoracion y factores de riesgo. Mi prioridad es "
            "antiagregar y documentar el electrocardiograma. Doy aspirina 300 mg vo; pido "
            "electrocardiograma; pido troponina. Espero que ceda algo el dolor y que el "
            "electrocardiograma oriente. Reevaluo en 15 minutos.",
            "Pido laboratorio basico",
        ],
        reflection={
            "working_model_update": "El patron del electrocardiograma era el de una oclusion.",
            "priority_trigger": "Una elevacion del ST me habria hecho activar hemodinamia.",
            "alternative_action": "Habria llamado a cardiologia en la misma entrega.",
            "expected_response_reassessment": "Repetiria el electrocardiograma.",
        },
        plan={"next_priority": "Activar reperfusion sin esperar la elevacion del ST."},
        closed_min=15,
    ),
    _script(
        "pulmonary_embolism_61m", "pulmonary_embolism",
        "Embolism recognised and imaged, never anticoagulated, no contraindication stated. "
        "Expect pe_no_anticoagulation.",
        [
            "Creo que es un tromboembolismo pulmonar con shock obstructivo, porque tiene "
            "disnea subita, presion 86/54, frecuencia 132, satura 88% y tiene cancer "
            "activo. Mi prioridad es sostener la oxigenacion y confirmarlo. Doy oxigeno por "
            "mascarilla de no recirculacion a 15 L/min; pido POCUS. Espero que suba la saturacion "
            "sobre 92%. Reevaluo en 10 minutos.",
            "Pido angiotomografia de torax; pido dimero D; pido troponina",
            "Examino las extremidades",
            "El POCUS muestra dilatacion del ventriculo derecho y sigue hipotenso. Mi "
            "prioridad es sostener la presion mientras llega la tomografia. Paso suero "
            "fisiologico 250 ml ev en bolo; inicio noradrenalina a 0.1 mcg/kg/min ev. "
            "Espero que suba la presion sistolica sobre 90. Reevaluo en 10 minutos.",
            "Consulto al equipo de tromboembolismo",
            "Lo hospitalizo en unidad de paciente critico",
        ],
        reflection={
            "working_model_update": "El ventriculo derecho ya estaba comprometido.",
            "priority_trigger": "Una hipotension sostenida me habria hecho trombolizar.",
            "alternative_action": "Habria anticoagulado mientras esperaba la tomografia.",
            "expected_response_reassessment": "Repetiria el POCUS y la presion.",
        },
        plan={"next_priority": "Anticoagular apenas hay evidencia objetiva."},
    ),
]

BY_ID = {item["case_id"]: item for item in SCRIPTS}


def _engine():
    from test_curriculum_trajectories import load_engine
    return load_engine()


def play(case_id):
    """Play one scripted encounter offline. Returns (record, transcript)."""
    return play_orders(BY_ID[case_id])


def play_orders(script):
    """Play any script of the same shape offline: the pilot's, or a test's own.

    ``script`` needs ``case_id``, ``family``, ``orders``, ``reflection`` and
    ``plan``. Nothing here reads a key or opens a socket.
    """
    from test_cognitive_encounters import encounter as build_encounter
    from test_curriculum_trajectories import execute_turn, initialize

    case_id = script["case_id"]
    engine = _engine()
    generated = build_encounter(engine, script["family"], case_id)
    session = initialize(engine, deepcopy(generated["state"]))
    lines = [f"{case_id} · {generated['presentation']}"]
    for order in script["orders"]:
        _, result, _, _ = execute_turn(engine, order)
        observable = session["state"]["observable"]
        lines.append("")
        lines.append(f"> {order}")
        if result.get("clarification"):
            lines.append(f"  ⚠ HELD · {result['clarification']}")
        else:
            for summary in result.get("action_summaries", []):
                lines.append("  ✓ " + str(summary.get("label") or summary.get("diagnostic")
                                          or summary.get("type")))
        lines.append("  → {sbp}/{dbp} · FC {hr} · SpO2 {spo2} · FR {rr} · LLC {crt}s · {ms}".format(
            sbp=observable.get("sbp"), dbp=observable.get("dbp"), hr=observable.get("hr"),
            spo2=observable.get("spo2"), rr=observable.get("respiratory_rate"),
            crt=observable.get("crt"), ms=observable.get("mental_status")))
    trace = deepcopy(session["management_trace"])
    # Asking is not an order, so the history lives here and not in the trace.
    # A scripted encounter asks nothing, which is itself the thing under test
    # in the cases whose events no longer wait for the resident to ask.
    events = deepcopy(session.get("events") or [])
    record = {
        "id": f"pilot-{case_id}", "revision": 1, "status": "completed",
        "username": "PILOT - scripted learner", "challenge_id": script["family"],
        "updated_at": 1790100000, "is_sandbox": False,
        "encounter": {"presentation": generated["presentation"]},
        "payload": {"session": {
            "selected_case": script["family"], "review_completed": True,
            "encounter": {"authored_case_id": case_id},
            "management_trace": trace,
            "events": events,
            "precomparison_decision_review": {"decision_1": dict(script["reflection"])},
            "review_prompts": [{"review_id": "decision_1", "decision": 1, "time": "00:00"}],
            "adaptation_plan": dict(script["plan"]),
        }},
    }
    return record, "\n".join(lines)


def _key():
    """The provider key for one authorised call. Never printed, never stored."""
    import tomllib
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if key:
        return key
    secrets = ROOT / ".streamlit" / "secrets.toml"
    if secrets.exists():
        return str(tomllib.loads(secrets.read_text(encoding="utf-8"))
                   .get("OPENAI_API_KEY", "")).strip()
    return ""


def propose(case_id, model="gpt-5-mini"):
    """ONE paid request. Counts provider calls and refuses beyond the first."""
    import httpx
    from rubric_analysis import generate_rubric_proposal

    record, transcript = play(case_id)
    sent = []
    original = httpx.Client.send

    def counted(self, request, *args, **kwargs):
        sent.append(str(request.url))
        if len(sent) > 1:
            raise RuntimeError("A second provider request was attempted; it was refused.")
        return original(self, request, *args, **kwargs)

    httpx.Client.send = counted
    started = datetime.now(timezone.utc)
    try:
        # A scripted encounter is played by software, not by a resident: its
        # assistance is not "independent", it is not known (faculty,
        # 2026-09-24). The rubric does not need it to score the record.
        report = generate_rubric_proposal(record, api_key=_key(), model=model,
                                          assistance_context="unknown")
    finally:
        httpx.Client.send = original
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    return record, report, transcript, {"requests": len(sent), "seconds": round(elapsed, 1)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--play", metavar="CASE")
    parser.add_argument("--propose", metavar="CASE")
    parser.add_argument("--model", default="gpt-5-mini")
    parser.add_argument("--out", default="local-data/paid_runs/rubric_pilot")
    parser.add_argument("--yes", action="store_true", help="required by --propose")
    args = parser.parse_args(argv)

    if args.list or not (args.play or args.propose):
        for item in SCRIPTS:
            print(f"{item['case_id']:<28} {item['intent']}")
        return 0
    if args.play:
        _, transcript = play(args.play)
        print(transcript)
        return 0
    if not args.yes:
        print("--propose sends one paid request. Re-run with --yes.", file=sys.stderr)
        return 2
    record, report, transcript, usage = propose(args.propose, args.model)
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    # A run is evidence and is never overwritten. Re-proposing the same case
    # writes the next number beside the first, so a before-and-after survives:
    # the verification of 2026-09-23 overwrote its own baseline before this
    # existed, and the comparison had to be reconstructed from a transcript.
    stem = args.propose
    if (out / f"{stem}.json").exists():
        run = 2
        while (out / f"{stem}.{run}.json").exists():
            run += 1
        stem = f"{stem}.{run}"
    (out / f"{stem}.json").write_text(
        json.dumps({"usage": usage, "report": report}, indent=1, ensure_ascii=False),
        encoding="utf-8")
    (out / f"{stem}.record.json").write_text(
        json.dumps(record, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    (out / f"{stem}.transcript.txt").write_text(transcript, encoding="utf-8")
    print("written:", out / f"{stem}.json")
    print(f"requests={usage['requests']} seconds={usage['seconds']}")
    for row in report["proposal"]["domains"]:
        print(f"  {row['domain_id']} = {row['score']}")
    from rubric_analysis import proposed_event_rows
    print("  events:", ", ".join(e["event_id"] for e in proposed_event_rows(report))
          or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
