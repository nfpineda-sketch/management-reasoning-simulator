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
                       "The troponin below the reference limit was read at minute 15 as "
                       "positive, which the record does not support.",
                       "The second submission was held, so its reasoning was not acted on.",
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
                "concern": ("The troponin was read as positive when the record shows 12 ng/mL "
                            "against an upper reference of 19. No defined event covers a "
                            "misread result, so this is flagged rather than deducted."),
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
        justifications={"D2": ("Reading a troponin of 12 against a limit of 19 as positive is a "
                               "misinterpretation of essential information, which the descriptor "
                               "for 3 excludes. It did not compromise management, so not a 0 or 1.")},
        status="confirmed", proposal=report)
    review = {**review, "reviewer": "EXAMPLE - faculty", "sequence": 2}
    return encounter, report, review


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
    (docs / "EJEMPLO_RUBRICA.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    return encounter, report, review, assessment


if __name__ == "__main__":
    encounter, report, review, assessment = main()
    print("escrito: docs/EJEMPLO_RUBRICA.md")
    print(" ", assessment["coverage_label"])
    print(" ", assessment["status"]["label"])
