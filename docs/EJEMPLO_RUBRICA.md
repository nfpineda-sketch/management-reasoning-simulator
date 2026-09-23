# Ejemplo completo: propuesta de IA y revisión docente

> **La propuesta de IA de este ejemplo es ILUSTRATIVA.** Está escrita a mano con la forma exacta que acepta el esquema y validada contra él; **ninguna llamada pagada la produjo**. El modelo aparece como `ILLUSTRATIVE-NOT-A-MODEL-CALL` para que no pueda confundirse con una salida real.

> El encuentro reproduce el caso `acs_48m_wellens` tal como se jugó el 2026-09-22, incluidas las órdenes que el intérprete retuvo.

Generado por `tools_rubric_example.py` · rúbrica 1.0-pilot.

## 1 · Lo que hizo el residente

**Decisión 1** · minuto 0 · ejecutada

> Typical chest pain, sounds like cardiac origin. EKG shows T wave inversion in anterior leads. I think is compatible with Wellens syndrome. Send labs, troponin, POCUS. Give 250 mg aspirin po. Reassess in 15 minutes

**Decisión 2** · minuto 15 · **retenida, no ejecutada**

> Consistent with acute coronary syndrome, because troponins are positive. Start iv nytroglicerin 30 mg/min, clopidrogrel 180 mg po, heparin 5000 IU iv. Admit to coronary unit.

## 2 · Lo que propuso la IA

| Dominio | Propuesto | Fundamento | Evidencia en contra | Límites |
|---|---|---|---|---|
| **D1** | 3/3 | The pattern was named at minute 0 in a patient who looked well, and the antiplatelet followed in the same submission rather than after the investigation returned. | The urgency of the disposition was not stated in the first turn. | Only two submissions are recorded. |
| **D2** | 3/3 | The ECG was read as an anterior T-wave pattern and named; laboratory, troponin and POCUS were requested together at minute 0. | The troponin below the reference limit was read at minute 15 as positive, which the record does not support. | The second submission was held, so its reasoning was not acted on. |
| **D3** | 2/3 | Aspirin 250 mg PO was executed at minute 0. The second submission's nitrate rate and antiplatelet were held by the interpreter and never executed. | No P2Y12 inhibitor reached the patient in the recorded window. | execution_status for the second submission is not_executed: this is an interpreter hold, not a decision the learner reversed. |
| **D4** | 2/3 | A fifteen-minute reassessment was stated with the ECG and POCUS named as what would be rechecked. | No alarm threshold was set for recurrent pain. | The encounter closed at minute 15; only one response is observed. |
| **D5** | Not assessable | The only submission that carried a disposition was held by the interpreter and never executed, so no continuity decision reached the record. This is a limit of the observation, not a failure to decide. | The later reflection names angiography, but a reflection recorded after the encounter is not scored as a decision within it. | The encounter closed before a second executed decision. |

**Eventos críticos propuestos:** ninguno

**Señalado para revisión, sin deducción:**

- The troponin was read as positive when the record shows 12 ng/mL against an upper reference of 19. No defined event covers a misread result, so this is flagged rather than deducted.

**Límites del registro declarados por la IA:**

- Two submissions are recorded and one of them was never executed.
- The encounter closed at minute 15, so no later response is observable.

## 3 · Lo que decidió el docente

| Dominio | IA | Docente | Por qué cambió |
|---|---|---|---|
| **D1** | 3/3 | 3/3 | — |
| **D2** | 3/3 | 2/3 | Reading a troponin of 12 against a limit of 19 as positive is a misinterpretation of essential information, which the descriptor for 3 excludes. It did not compromise management, so not a 0 or 1. |
| **D3** | 2/3 | 2/3 | — |
| **D4** | 2/3 | 2/3 | — |
| **D5** | Not assessable | Not assessable | — |

**Motivo de no evaluable:** The only submission carrying a disposition was held by the interpreter and never executed. There was no opportunity to observe a continuity decision.

**Eventos críticos:**

- `acs_no_antiplatelet` — **dismissed**. Propuesto por la IA: no. Aspirin 250 mg PO was executed at minute 0.

## 4 · El resultado

**Partial assessment · 4 of 5 domains assessable**

- Cobertura: 4 of 5 domains assessable - no comparable total
- Penalización: −0
- Eventos críticos confirmados: 0
- Estado: Confirmed by faculty
- Versión de rúbrica: 1.0-pilot

Cuatro de cinco dominios son evaluables, así que **no hay total comparable** con un episodio completo. El subtotal existe y se conserva, pero no se normaliza ni se presenta como un puntaje sobre 15.

## 5 · La propuesta cruda, como se guarda

```json
{
  "schema_version": "rubric_assessment_v1",
  "prompt_version": "1.0",
  "rubric_version": "1.0-pilot",
  "coverage_version": "1.0",
  "source_hash": "d7471a09993bb4cc2e42b5e81f6f7476550f07a6ae5433f41d6b909d47b77c02",
  "attempt_id": "example-rubric-wellens",
  "attempt_revision": 3,
  "generated_at": "2026-09-23T02:00:00+00:00",
  "model": "ILLUSTRATIVE-NOT-A-MODEL-CALL",
  "assistance_context": "unknown",
  "case_id": "acs_48m_wellens",
  "proposal": {
    "domains": [
      {
        "domain_id": "D1",
        "score": 3,
        "evidence_refs": [
          "trace:0"
        ],
        "learner_evidence": [
          {
            "evidence_ref": "trace:0",
            "minute": 0,
            "quote": "Typical chest pain, sounds like cardiac origin. EKG shows T wave inversion in anterior leads. I think is compatible with Wellens syndrome."
          }
        ],
        "rationale": "The pattern was named at minute 0 in a patient who looked well, and the antiplatelet followed in the same submission rather than after the investigation returned.",
        "contrary_evidence": "The urgency of the disposition was not stated in the first turn.",
        "limits": "Only two submissions are recorded."
      },
      {
        "domain_id": "D2",
        "score": 3,
        "evidence_refs": [
          "trace:0"
        ],
        "learner_evidence": [
          {
            "evidence_ref": "trace:0",
            "minute": 0,
            "quote": "Typical chest pain, sounds like cardiac origin. EKG shows T wave inversion in anterior leads. I think is compatible with Wellens syndrome."
          }
        ],
        "rationale": "The ECG was read as an anterior T-wave pattern and named; laboratory, troponin and POCUS were requested together at minute 0.",
        "contrary_evidence": "The troponin below the reference limit was read at minute 15 as positive, which the record does not support.",
        "limits": "The second submission was held, so its reasoning was not acted on."
      },
      {
        "domain_id": "D3",
        "score": 2,
        "evidence_refs": [
          "trace:0"
        ],
        "learner_evidence": [
          {
            "evidence_ref": "trace:0",
            "minute": 15,
            "quote": "Consistent with acute coronary syndrome, because troponins are positive. Start iv nytroglicerin 30 mg/min, clopidrogrel 180 mg po, heparin 5000 IU iv."
          }
        ],
        "rationale": "Aspirin 250 mg PO was executed at minute 0. The second submission's nitrate rate and antiplatelet were held by the interpreter and never executed.",
        "contrary_evidence": "No P2Y12 inhibitor reached the patient in the recorded window.",
        "limits": "execution_status for the second submission is not_executed: this is an interpreter hold, not a decision the learner reversed."
      },
      {
        "domain_id": "D4",
        "score": 2,
        "evidence_refs": [
          "trace:0"
        ],
        "learner_evidence": [
          {
            "evidence_ref": "trace:0",
            "minute": 0,
            "quote": "Typical chest pain, sounds like cardiac origin. EKG shows T wave inversion in anterior leads. I think is compatible with Wellens syndrome."
          }
        ],
        "rationale": "A fifteen-minute reassessment was stated with the ECG and POCUS named as what would be rechecked.",
        "contrary_evidence": "No alarm threshold was set for recurrent pain.",
        "limits": "The encounter closed at minute 15; only one response is observed."
      },
      {
        "domain_id": "D5",
        "score": "not_assessable",
        "evidence_refs": [
          "trace:0"
        ],
        "learner_evidence": [
          {
            "evidence_ref": "trace:0",
            "minute": 15,
            "quote": "Consistent with acute coronary syndrome, because troponins are positive. Start iv nytroglicerin 30 mg/min, clopidrogrel 180 mg po, heparin 5000 IU iv."
          }
        ],
        "rationale": "The only submission that carried a disposition was held by the interpreter and never executed, so no continuity decision reached the record. This is a limit of the observation, not a failure to decide.",
        "contrary_evidence": "The later reflection names angiography, but a reflection recorded after the encounter is not scored as a decision within it.",
        "limits": "The encounter closed before a second executed decision."
      }
    ],
    "critical_events": [],
    "concerns_for_review": [
      {
        "concern": "The troponin was read as positive when the record shows 12 ng/mL against an upper reference of 19. No defined event covers a misread result, so this is flagged rather than deducted.",
        "evidence_refs": [
          "trace:0"
        ]
      }
    ],
    "assistance_recorded": [
      "No hint or assistance is recorded in this encounter."
    ],
    "record_limits": [
      "Two submissions are recorded and one of them was never executed.",
      "The encounter closed at minute 15, so no later response is observable."
    ]
  }
}
```

