"""A worked example: one AI proposal, one faculty review, and the documents.

No paid call is made. The proposal below is ILLUSTRATIVE: it is written by hand
in the exact shape the schema accepts, so that the example shows the contract
rather than a model's output. It is labelled as such everywhere it appears.

The encounter it describes mirrors the Wellens case as it was actually played
on 2026-09-22, including the orders the interpreter held.
"""
import json
from pathlib import Path

import rubric
import rubric_presentation as present
from case_assessment import events as defined_events
from faculty_analysis import source_fingerprint
from rubric_analysis import PROMPT_VERSION, SCHEMA_VERSION, validate_rubric_proposal
from rubric_store import build_review

CASE = "acs_48m_wellens"


def _state(minute, **observable):
    base = {"sbp": 138, "dbp": 84, "hr": 76, "spo2": 97, "respiratory_rate": 18,
            "crt": 2, "mental_status": "Alert", "pulse_present": True, "rhythm": "Sinus rhythm"}
    base.update(observable)
    return {"sim_time_min": minute, "observable": base,
            "treatments": {"aspirin": minute >= 15}, "diagnostics": {}}


def record():
    """A synthetic record in the shape a completed encounter is stored in."""
    trace = [
        {"execution_status": "executed", "decision_time_min": 0, "response_time_min": 15,
         "learner_input": ("Typical chest pain, sounds like cardiac origin. EKG shows T wave "
                           "inversion in anterior leads. I think is compatible with Wellens "
                           "syndrome. Send labs, troponin, POCUS. Give 250 mg aspirin po. "
                           "Reassess in 15 minutes"),
         "reasoning": {"problem_representation": "Compatible with Wellens syndrome",
                       "management_priority": "Rule out acute coronary syndrome",
                       "expected_effect": ("No change in chest pain; troponin could be within "
                                           "range. If Wellens is correct I suspect a critical "
                                           "LAD lesion."),
                       "reassessment": "ECG and POCUS in 15 minutes"},
         "interpreted_action": [{"type": "aspirin", "dose_mg": 250, "route": "PO"},
                                {"type": "diagnostic", "diagnostic": "basic_labs"},
                                {"type": "diagnostic", "diagnostic": "troponin"},
                                {"type": "diagnostic", "diagnostic": "pocus"}],
         "action_summaries": [{"type": "aspirin", "agent": "aspirin", "dose_mg": 250,
                               "route": "PO", "time_min": 0}],
         "state_before": _state(0), "state_after": _state(15)},
        {"execution_status": "not_executed", "decision_time_min": 15, "response_time_min": 15,
         "learner_input": ("Consistent with acute coronary syndrome, because troponins are "
                           "positive. Start iv nytroglicerin 30 mg/min, clopidrogrel 180 mg po, "
                           "heparin 5000 IU iv. Admit to coronary unit."),
         "reasoning": {"problem_representation": "Acute coronary syndrome"},
         "interpreted_action": [], "action_summaries": [],
         "state_before": _state(15), "state_after": _state(15)},
    ]
    return {
        "id": "example-rubric-wellens", "revision": 3, "status": "completed",
        "username": "EXAMPLE - synthetic learner", "challenge_id": "R2-02",
        "updated_at": 1790000000, "is_sandbox": False,
        "encounter": {"presentation": ("A 48-year-old man is pain-free now after three episodes "
                                       "of chest pressure today, the last one an hour ago.")},
        "payload": {"session": {
            "selected_case": "R2-02", "review_completed": True,
            "encounter": {"authored_case_id": CASE},
            "management_trace": trace,
            "precomparison_decision_review": {"decision_1": {
                "working_model_update": "The pattern demands angiography, not a stress test.",
                "priority_trigger": "Recurrent pain would change the urgency.",
                "alternative_action": "I would have named the antiplatelet plan earlier.",
                "expected_response_reassessment": "I would recheck the ECG."}},
            "review_prompts": [{"review_id": "decision_1", "decision": 1, "time": "00:00"}],
            "adaptation_plan": {"next_priority": "State the disposition with the first order."},
        }},
    }


PE_CASE = "pulmonary_embolism_33f"


def _pe_state(minute, sbp=110, dbp=70, hr=124, spo2=90, rr=30, crt=3):
    return {"sim_time_min": minute,
            "observable": {"sbp": sbp, "dbp": dbp, "hr": hr, "spo2": spo2,
                           "respiratory_rate": rr, "work_of_breathing": "Increased",
                           "crt": crt, "mental_status": "Alert", "pulse_present": True,
                           "rhythm": "Sinus tachycardia"},
            "treatments": {"anticoagulated": minute >= 30}, "diagnostics": {}}


def record_embolism():
    """The embolism as it was played on 2026-09-22, including the thrombolysis.

    A second encounter for the rubric, chosen because a defined critical event
    did occur in it: systemic thrombolysis without sustained hypotension in a
    patient operated on twelve days earlier.
    """
    trace = [
        {"execution_status": "not_executed", "decision_time_min": 0, "response_time_min": 0,
         "learner_input": ("Sospecho un tromboembolismo pulmonar, porque tiene disnea subita, "
                           "taquicardia e hipoxemia con dolor pleuritico. Mi prioridad es "
                           "confirmarlo y evaluar la repercusion del ventriculo derecho. Doy "
                           "oxigeno por naricera a 4 L/min, pido POCUS, dimero D, gases "
                           "arteriales, ECG y troponina. Espero que suba la saturacion sobre "
                           "94%. Reevaluo en 10 minutos."),
         "reasoning": {"problem_representation": "Tromboembolismo pulmonar",
                       "management_priority": "Confirmarlo y evaluar el ventriculo derecho",
                       "expected_effect": "Que suba la saturacion sobre 94%",
                       "reassessment": "En 10 minutos"},
         "interpreted_action": [], "action_summaries": [],
         "state_before": _pe_state(0), "state_after": _pe_state(0)},
        {"execution_status": "executed", "decision_time_min": 0, "response_time_min": 15,
         "learner_input": ("El POCUS muestra dilatacion del ventriculo derecho. Mi prioridad es "
                           "anticoagular. Doy heparina 5000 UI ev en bolo. Espero que no "
                           "progrese el trombo. Reevaluo en 15 minutos."),
         "reasoning": {"problem_representation": "Dilatacion del ventriculo derecho",
                       "management_priority": "Anticoagular",
                       "expected_effect": "Que no progrese el trombo",
                       "reassessment": "En 15 minutos"},
         "interpreted_action": [{"type": "anticoagulation", "agent": "heparin", "dose": 5000,
                                 "units": "units", "route": "IV"}],
         "action_summaries": [{"type": "anticoagulation", "agent": "heparin", "dose": 5000,
                               "units": "units", "route": "IV", "time_min": 0,
                               "label": "heparin 5000 units IV administered"}],
         "state_before": _pe_state(0), "state_after": _pe_state(15, sbp=109, crt=3.1)},
        {"execution_status": "executed", "decision_time_min": 15, "response_time_min": 20,
         "learner_input": "Pido angiotac de torax",
         "reasoning": {}, "interpreted_action": [{"type": "diagnostic", "diagnostic": "ctpa"}],
         "action_summaries": [{"type": "diagnostic", "diagnostic": "ctpa", "time_min": 15,
                               "label": "CT pulmonary angiography requested"}],
         "state_before": _pe_state(15, sbp=109, crt=3.1),
         "state_after": _pe_state(20, sbp=108, hr=125, crt=3.1)},
        {"execution_status": "executed", "decision_time_min": 20, "response_time_min": 40,
         "learner_input": ("Sigue taquicardica e hipoxemica. Mi prioridad es decidir si "
                           "trombolizo. Doy alteplasa 100 mg ev en 2 horas. Espero mejoria "
                           "hemodinamica. Reevaluo en 20 minutos."),
         "reasoning": {"problem_representation": "Sigue taquicardica e hipoxemica",
                       "management_priority": "Decidir si trombolizo",
                       "expected_effect": "Mejoria hemodinamica",
                       "reassessment": "En 20 minutos"},
         "interpreted_action": [{"type": "thrombolysis", "agent": "alteplase", "dose_mg": 100,
                                 "route": "IV"}],
         "action_summaries": [
             {"type": "thrombolysis", "agent": "alteplase", "dose_mg": 100, "route": "IV",
              "time_min": 20, "label": "alteplase 100 mg IV given started over 120 min"},
             {"type": "consequence", "time_min": 20,
              "label": ("Systemic thrombolysis given before the hypotension was sustained "
                        "(systolic 108 mmHg, low for 0 of the 15 minutes the indication "
                        "requires): the bleeding risk is taken without the indication, and "
                        "the obstruction is unchanged.")},
             {"type": "consequence", "time_min": 20,
              "label": ("Bleeding from the surgical site operated on twelve days ago: the "
                        "haemoglobin is falling and the pressure with it. This is the risk "
                        "the thrombolytic carries, and it was taken in a patient who had a "
                        "reason to bleed.")}],
         "state_before": _pe_state(20, sbp=108, hr=125, crt=3.1),
         "state_after": _pe_state(40, sbp=107, hr=125, rr=31, crt=3.2)},
    ]
    return {
        "id": "example-rubric-embolism", "revision": 2, "status": "completed",
        "username": "EXAMPLE - synthetic learner", "challenge_id": "R2-02",
        "updated_at": 1790000500, "is_sandbox": False,
        "encounter": {"presentation": ("A 33-year-old woman arrives with sudden breathlessness "
                                       "and sharp right-sided chest discomfort. She wonders "
                                       "whether anxiety could explain the episode; this has not "
                                       "been assessed.")},
        "payload": {"session": {
            "selected_case": "R2-02", "review_completed": True,
            "encounter": {"authored_case_id": PE_CASE},
            "management_trace": trace,
            "precomparison_decision_review": {"decision_1": {
                "working_model_update": "The right ventricle was already involved.",
                "priority_trigger": "A falling pressure would change my priority.",
                "alternative_action": "I would have checked the surgical history first.",
                "expected_response_reassessment": "I would repeat the POCUS."}},
            "review_prompts": [{"review_id": "decision_1", "decision": 1, "time": "00:00"}],
            "adaptation_plan": {"next_priority": "Check bleeding risk before thrombolysis."},
        }},
    }



def proposal(source_hash, attempt_id, revision):
    """ILLUSTRATIVE. Hand-written in the schema's shape; no model produced it."""
    def domain(domain_id, score, rationale, contrary, limits, quote_minute, quote):
        return {"domain_id": domain_id, "score": score, "evidence_refs": ["trace:0"],
                "learner_evidence": [{"evidence_ref": "trace:0", "minute": quote_minute,
                                      "quote": quote}],
                "rationale": rationale, "contrary_evidence": contrary, "limits": limits}

    first = ("Typical chest pain, sounds like cardiac origin. EKG shows T wave inversion in "
             "anterior leads. I think is compatible with Wellens syndrome.")
    second = ("Consistent with acute coronary syndrome, because troponins are positive. Start "
              "iv nytroglicerin 30 mg/min, clopidrogrel 180 mg po, heparin 5000 IU iv.")
    return {
        "schema_version": SCHEMA_VERSION, "prompt_version": PROMPT_VERSION,
        "rubric_version": rubric.VERSION, "coverage_version": "1.0",
        "source_hash": source_hash, "attempt_id": attempt_id, "attempt_revision": revision,
        "generated_at": "2026-09-23T02:00:00+00:00",
        "model": "ILLUSTRATIVE-NOT-A-MODEL-CALL", "assistance_context": "unknown",
        "case_id": CASE,
        "proposal": {
            "domains": [
                domain("D1", 3,
                       "The pattern was named at minute 0 in a patient who looked well, and the "
                       "antiplatelet followed in the same submission rather than after the "
                       "investigation returned.",
                       "The urgency of the disposition was not stated in the first turn.",
                       "Only two submissions are recorded.", 0, first),
                domain("D2", 3,
                       "The ECG was read as an anterior T-wave pattern and named; laboratory, "
                       "troponin and POCUS were requested together at minute 0.",
                       "The second submission asserts the troponin is positive, and no troponin "
                       "result is recorded in this encounter: the claim rests on nothing the "
                       "record contains.",
                       "No study result was reported within the observed window, so how "
                       "discordant data would be integrated cannot be seen.",
                       0, first),
                domain("D3", 2,
                       "Aspirin 250 mg PO was executed at minute 0. The second submission's "
                       "nitrate rate and antiplatelet were held by the interpreter and never "
                       "executed.",
                       "No P2Y12 inhibitor reached the patient in the recorded window.",
                       "execution_status for the second submission is not_executed: this is an "
                       "interpreter hold, not a decision the learner reversed.", 15, second),
                domain("D4", 2,
                       "A fifteen-minute reassessment was stated with the ECG and POCUS named as "
                       "what would be rechecked.",
                       "No alarm threshold was set for recurrent pain.",
                       "The encounter closed at minute 15; only one response is observed.",
                       0, first),
                domain("D5", rubric.NOT_ASSESSABLE,
                       "The only submission that carried a disposition was held by the "
                       "interpreter and never executed, so no continuity decision reached the "
                       "record. This is a limit of the observation, not a failure to decide.",
                       "The later reflection names angiography, but a reflection recorded after "
                       "the encounter is not scored as a decision within it.",
                       "The encounter closed before a second executed decision.", 15, second),
            ],
            "critical_events": [],
            "concerns_for_review": [{
                "concern": ("The second submission states the troponin is positive while no "
                            "troponin result appears anywhere in the record. No defined event "
                            "covers a claim with no result behind it, so this is flagged for "
                            "the faculty rather than deducted."),
                "evidence_refs": ["trace:0"]}],
            "assistance_recorded": ["No hint or assistance is recorded in this encounter."],
            "record_limits": [
                "Two submissions are recorded and one of them was never executed.",
                "The encounter closed at minute 15, so no later response is observable.",
            ],
        },
    }


def build():
    encounter = record()
    fingerprint = source_fingerprint(encounter)
    report = validate_rubric_proposal(
        proposal(fingerprint, encounter["id"], encounter["revision"]), encounter)

    # The faculty disagrees with one domain and adds an event the AI did not propose.
    scores = {row["domain_id"]: row["score"] for row in report["proposal"]["domains"]}
    scores["D2"] = 2
    review = build_review(
        case_id=CASE, scores=scores,
        reasons={"D5": ("The only submission carrying a disposition was held by the interpreter "
                        "and never executed. There was no opportunity to observe a continuity "
                        "decision.")},
        events=[{"event_id": "acs_no_antiplatelet", "status": "dismissed",
                 "justification": "Aspirin 250 mg PO was executed at minute 0."}],
        justifications={"D2": ("Asserting a positive troponin with no result in the record is a "
                               "claim about essential information that the record does not "
                               "support, which the descriptor for 3 excludes. It did not "
                               "compromise management, so not a 0 or 1.")},
        status="confirmed", proposal=report)
    review = {**review, "reviewer": "EXAMPLE - faculty", "sequence": 2}
    return encounter, report, review


# The real run is part of this document, not an edit made on top of it: a
# generated file that someone appends to loses the appendix the next time it
# is generated.
REAL_RUN = '\n---\n\n## 6 · La corrida real con un modelo (2026-09-23)\n\n**Una llamada pagada, autorizada explícitamente.** Modelo `gpt-5-mini`, ~3.500 tokens de\nentrada, 77 s, sin reintentos. Costo estimado bajo US$0,03. La propuesta cruda está en\n`local-data/paid_runs/2026-09-23_rubric_proposal_wellens.json`. Se corrió contra **el mismo\nregistro** de este documento.\n\n### Qué propuso\n\n| Dominio | Modelo real | Ilustración escrita a mano |\n|---|---|---|\n| D1 | 2 | 3 |\n| D2 | 2 | 3 |\n| D3 | 2 | 2 |\n| D4 | 2 | 2 |\n| D5 | **1** | **No evaluable** |\n| Eventos críticos | ninguno | ninguno |\n\n### Qué respetó\n\n- **No inventó ningún evento.** Propuso cero, correctamente: la aspirina sí se ejecutó, así\n  que `acs_no_antiplatelet` no aplica, y nadie pidió una prueba de provocación.\n- **Separó lo ejecutado de lo no ejecutado, con rigor.** Sobre la segunda entrega, retenida\n  por el intérprete: *"appears in the record as learner intention but was not executed during\n  the observed encounter"*, y *"cannot be used to upgrade the in-encounter plan"*.\n- **Usó el canal de preocupaciones** para algo que ningún evento cubre.\n- **Declaró límites del registro**, incluido que el ECG no viene como imagen y que el puntaje\n  descansa en la interpretación declarada por el residente.\n- **Usó las limitaciones del motor** que el caso declara: *"engine limitation: angiography\n  results are not available"*.\n\n### Dónde discrepó, y por qué importa\n\n**D5.** El modelo puntuó **1**; la ilustración decía **no evaluable**. La orden de destino\n—"Admit to coronary unit"— existe en el registro, pero **nunca se ejecutó porque el intérprete\nretuvo toda la entrega** por una nitroglicerina mal escrita. El modelo reconoció que no se\nejecutó y aun así puntuó al residente por una continuidad incompleta.\n\nEsa es, exactamente, la frontera que la especificación más cuida: *"no atribuir al residente\nfallas del motor"* y *"no evaluable no equivale a cero"*. La instrucción está escrita, el\nmodelo leyó los límites, y aun así puntuó en vez de declarar la falta de oportunidad.\n\n**No es un defecto del contrato: es la razón por la que el docente confirma.** El esquema\nimpidió lo que debía impedir —inventar un evento, devolver un total— y dejó a la vista un\njuicio discutible para que un humano lo resuelva.\n\n### Un error de la ilustración que el modelo no cometió\n\nLa versión escrita a mano afirmaba que *"el registro muestra 12 ng/mL contra un límite de 19"*.\n**El registro no muestra eso**: la palabra "troponina" aparece sólo como solicitud y en las\npropias palabras del residente; ningún resultado se informó en la ventana observada. El modelo\nreal lo dijo correctamente —*"No troponin result or POCUS result recorded"*— y la ilustración\ninventó un valor, que es precisamente la regla que estas instrucciones prohíben. La ilustración\nquedó corregida el 2026-09-23 para afirmar sólo lo que el registro sostiene.\n\n### Qué queda por observar\n\nUna sola corrida no establece comportamiento. Lo que conviene vigilar con más encuentros:\n\n- **Rango comprimido**: cuatro dominios en 2 y uno en 1. Puede ser el encuentro, que es corto,\n  o tendencia central del modelo.\n- **La frontera cero / no evaluable**, que es donde discrepó.\n- **Si alguna vez intenta un evento no definido**, que el esquema rechazaría, pero conviene\n  saber con qué frecuencia lo intenta.\n'


SECOND_RUN = '\n---\n\n## 7 · Segunda corrida real: un encuentro donde el evento sí ocurrió (2026-09-23)\n\nLa primera corrida no pudo probar lo más importante, porque en ese encuentro **no ocurrió\nningún evento crítico**. Esta segunda usa el tromboembolismo `pulmonary_embolism_33f` tal como\nse jugó el 2026-09-22, donde el residente administró alteplasa sin hipotensión sostenida en una\npaciente operada doce días antes. **Una llamada a `gpt-5-mini`, 54 s, costo estimado bajo\nUS$0,03.** Propuesta cruda en `local-data/paid_runs/2026-09-23_rubric_proposal_embolism.json`.\n\n### Qué propuso\n\n| Dominio | Puntaje | |\n|---|---|---|\n| D1 · Gravedad y priorización | **3** | Reconoció la presentación de alto riesgo contra el anclaje de ansiedad y buscó evidencia objetiva del ventrículo derecho |\n| D2 · Evaluación e interpretación | **3** | |\n| D3 · Manejo seguro | **0** | *"administered systemic thrombolysis (alteplase 100 mg) despite the record showing no sustained hypotension and a recent surgical site"* |\n| D4 · Seguimiento | **2** | |\n| D5 · Adaptación y continuidad | **1** | |\n\n**Evento crítico propuesto:** `pe_unindicated_thrombolysis`, el que el caso define.\n\n> Evidencia del disparador: *"An executed thrombolysis action is recorded (trace:3). The same\n> trace documents that the systolic blood pressure was not sustained in the hypotensive range."*\n>\n> Exclusiones revisadas: *"the record does not show sustained hypotension within the engine\'s\n> own criterion; the surgical history indicating a recent operative site is present."*\n\n**No propuso `pe_no_anticoagulation`**, el otro evento definido para este caso, y es correcto:\nla heparina sí se administró.\n\n### La aritmética completa, con el docente confirmando\n\n```\nBase 9/15 · Penalty -3 · Adjusted 6/15 · 1 confirmed critical event(s)\n```\n\nAquí se ve **el doble peso declarado**: el mismo hecho baja D3 a 0 **y además** cuesta la\npenalización de seguridad. Es deliberado, y los informes lo dicen con esas palabras.\n\n### Qué demuestra esta corrida que la primera no\n\n- El modelo **propone el evento definido cuando corresponde**, citando la decisión y el minuto.\n- **Revisa las exclusiones antes de proponer**, que es lo que impide culpar al residente de una\n  limitación del motor.\n- **No propone el otro evento definido** cuando no aplica: no dispara todo lo que tiene a mano.\n- El descriptor de D3 se usó como está escrito: *"ordena algo claramente peligroso en este\n  contexto"* es exactamente un 0, no un 1.\n\n### Lo que sigue sin establecerse\n\nDos encuentros no son comportamiento. El rango sigue siendo estrecho en los dominios que no\ntocan el evento, y la frontera cero / no evaluable —donde discrepó en la primera corrida— no\nvolvió a ponerse a prueba aquí.\n'


def main():
    encounter, report, review = build()
    assessment = present.summary(review, report)
    docs = Path(__file__).with_name("docs")
    out = ["# Ejemplo completo: propuesta de IA y revisión docente", "",
           "> **La propuesta de IA de este ejemplo es ILUSTRATIVA.** Está escrita a mano con la "
           "forma exacta que acepta el esquema y validada contra él; **ninguna llamada pagada la "
           "produjo**. El modelo aparece como `ILLUSTRATIVE-NOT-A-MODEL-CALL` para que no pueda "
           "confundirse con una salida real.", "",
           "> El encuentro reproduce el caso `acs_48m_wellens` tal como se jugó el 2026-09-22, "
           "incluidas las órdenes que el intérprete retuvo.", "",
           f"Generado por `tools_rubric_example.py` · rúbrica {rubric.VERSION}.", "",
           "## 1 · Lo que hizo el residente", ""]
    for index, event in enumerate(encounter["payload"]["session"]["management_trace"]):
        state = "ejecutada" if event["execution_status"] == "executed" else "**retenida, no ejecutada**"
        out += [f"**Decisión {index + 1}** · minuto {event['decision_time_min']} · {state}", "",
                f"> {event['learner_input']}", ""]
    out += ["## 2 · Lo que propuso la IA", "",
            "| Dominio | Propuesto | Fundamento | Evidencia en contra | Límites |",
            "|---|---|---|---|---|"]
    for row in report["proposal"]["domains"]:
        label = present.score_label(row["score"])
        out.append(f"| **{row['domain_id']}** | {label} | {row['rationale']} | "
                   f"{row['contrary_evidence']} | {row['limits']} |")
    out += ["", "**Eventos críticos propuestos:** "
            + (", ".join(f"`{e['event_id']}`" for e in report["proposal"]["critical_events"])
               or "ninguno"), "",
            "**Señalado para revisión, sin deducción:**", ""]
    for concern in report["proposal"]["concerns_for_review"]:
        out.append(f"- {concern['concern']}")
    out += ["", "**Límites del registro declarados por la IA:**", ""]
    out += [f"- {limit}" for limit in report["proposal"]["record_limits"]]

    out += ["", "## 3 · Lo que decidió el docente", "",
            "| Dominio | IA | Docente | Por qué cambió |", "|---|---|---|---|"]
    for row in assessment["profile"]:
        proposed = present.score_label(row["proposed"]) if row["proposed"] is not None else "—"
        out.append(f"| **{row['domain_id']}** | {proposed} | {row['score_label']} | "
                   f"{row['change_justification'] or '—'} |")
    out += ["", "**Motivo de no evaluable:** " + (review["reasons"].get("D5") or "—"), "",
            "**Eventos críticos:**", ""]
    for event in review["critical_events"]:
        out.append(f"- `{event['event_id']}` — **{event['status']}**. "
                   f"Propuesto por la IA: {'sí' if event['proposed_by_ai'] else 'no'}. "
                   f"{event['justification']}")
    out += ["", "## 4 · El resultado", "",
            f"**{assessment['headline'] or assessment['coverage_label']}**", "",
            f"- Cobertura: {assessment['coverage_label']}",
            f"- Penalización: −{review['totals']['penalty']}",
            f"- Eventos críticos confirmados: {review['totals']['critical_events']}",
            f"- Estado: {assessment['status']['label']}",
            f"- Versión de rúbrica: {review['rubric_version']}", "",
            "Cuatro de cinco dominios son evaluables, así que **no hay total comparable** con un "
            "episodio completo. El subtotal existe y se conserva, pero no se normaliza ni se "
            "presenta como un puntaje sobre 15.", "",
            "## 5 · La propuesta cruda, como se guarda", "", "```json",
            json.dumps(report, indent=2, ensure_ascii=False)[:6000], "```", ""]
    (docs / "EJEMPLO_RUBRICA.md").write_text(
        "\n".join(out) + "\n" + REAL_RUN + SECOND_RUN, encoding="utf-8")
    return encounter, report, review, assessment


if __name__ == "__main__":
    encounter, report, review, assessment = main()
    print("escrito: docs/EJEMPLO_RUBRICA.md")
    print(" ", assessment["coverage_label"])
    print(" ", assessment["status"]["label"])
