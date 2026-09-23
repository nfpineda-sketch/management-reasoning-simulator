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
| **D2** | 3/3 | The ECG was read as an anterior T-wave pattern and named; laboratory, troponin and POCUS were requested together at minute 0. | The second submission asserts the troponin is positive, and no troponin result is recorded in this encounter: the claim rests on nothing the record contains. | No study result was reported within the observed window, so how discordant data would be integrated cannot be seen. |
| **D3** | 2/3 | Aspirin 250 mg PO was executed at minute 0. The second submission's nitrate rate and antiplatelet were held by the interpreter and never executed. | No P2Y12 inhibitor reached the patient in the recorded window. | execution_status for the second submission is not_executed: this is an interpreter hold, not a decision the learner reversed. |
| **D4** | 2/3 | A fifteen-minute reassessment was stated with the ECG and POCUS named as what would be rechecked. | No alarm threshold was set for recurrent pain. | The encounter closed at minute 15; only one response is observed. |
| **D5** | Not assessable | The only submission that carried a disposition was held by the interpreter and never executed, so no continuity decision reached the record. This is a limit of the observation, not a failure to decide. | The later reflection names angiography, but a reflection recorded after the encounter is not scored as a decision within it. | The encounter closed before a second executed decision. |

**Eventos críticos propuestos:** ninguno

**Señalado para revisión, sin deducción:**

- The second submission states the troponin is positive while no troponin result appears anywhere in the record. No defined event covers a claim with no result behind it, so this is flagged for the faculty rather than deducted.

**Límites del registro declarados por la IA:**

- Two submissions are recorded and one of them was never executed.
- The encounter closed at minute 15, so no later response is observable.

## 3 · Lo que decidió el docente

| Dominio | IA | Docente | Por qué cambió |
|---|---|---|---|
| **D1** | 3/3 | 3/3 | — |
| **D2** | 3/3 | 2/3 | Asserting a positive troponin with no result in the record is a claim about essential information that the record does not support, which the descriptor for 3 excludes. It did not compromise management, so not a 0 or 1. |
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
        "contrary_evidence": "The second submission asserts the troponin is positive, and no troponin result is recorded in this encounter: the claim rests on nothing the record contains.",
        "limits": "No study result was reported within the observed window, so how discordant data would be integrated cannot be seen."
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
        "concern": "The second submission states the troponin is positive while no troponin result appears anywhere in the record. No defined event covers a claim with no result behind it, so this is flagged for the faculty rather than deducted.",
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


---

## 6 · La corrida real con un modelo (2026-09-23)

**Una llamada pagada, autorizada explícitamente.** Modelo `gpt-5-mini`, ~3.500 tokens de
entrada, 77 s, sin reintentos. Costo estimado bajo US$0,03. La propuesta cruda está en
`local-data/paid_runs/2026-09-23_rubric_proposal_wellens.json`. Se corrió contra **el mismo
registro** de este documento.

### Qué propuso

| Dominio | Modelo real | Ilustración escrita a mano |
|---|---|---|
| D1 | 2 | 3 |
| D2 | 2 | 3 |
| D3 | 2 | 2 |
| D4 | 2 | 2 |
| D5 | **1** | **No evaluable** |
| Eventos críticos | ninguno | ninguno |

### Qué respetó

- **No inventó ningún evento.** Propuso cero, correctamente: la aspirina sí se ejecutó, así
  que `acs_no_antiplatelet` no aplica, y nadie pidió una prueba de provocación.
- **Separó lo ejecutado de lo no ejecutado, con rigor.** Sobre la segunda entrega, retenida
  por el intérprete: *"appears in the record as learner intention but was not executed during
  the observed encounter"*, y *"cannot be used to upgrade the in-encounter plan"*.
- **Usó el canal de preocupaciones** para algo que ningún evento cubre.
- **Declaró límites del registro**, incluido que el ECG no viene como imagen y que el puntaje
  descansa en la interpretación declarada por el residente.
- **Usó las limitaciones del motor** que el caso declara: *"engine limitation: angiography
  results are not available"*.

### Dónde discrepó, y por qué importa

**D5.** El modelo puntuó **1**; la ilustración decía **no evaluable**. La orden de destino
—"Admit to coronary unit"— existe en el registro, pero **nunca se ejecutó porque el intérprete
retuvo toda la entrega** por una nitroglicerina mal escrita. El modelo reconoció que no se
ejecutó y aun así puntuó al residente por una continuidad incompleta.

Esa es, exactamente, la frontera que la especificación más cuida: *"no atribuir al residente
fallas del motor"* y *"no evaluable no equivale a cero"*. La instrucción está escrita, el
modelo leyó los límites, y aun así puntuó en vez de declarar la falta de oportunidad.

**No es un defecto del contrato: es la razón por la que el docente confirma.** El esquema
impidió lo que debía impedir —inventar un evento, devolver un total— y dejó a la vista un
juicio discutible para que un humano lo resuelva.

### Un error de la ilustración que el modelo no cometió

La versión escrita a mano afirmaba que *"el registro muestra 12 ng/mL contra un límite de 19"*.
**El registro no muestra eso**: la palabra "troponina" aparece sólo como solicitud y en las
propias palabras del residente; ningún resultado se informó en la ventana observada. El modelo
real lo dijo correctamente —*"No troponin result or POCUS result recorded"*— y la ilustración
inventó un valor, que es precisamente la regla que estas instrucciones prohíben. La ilustración
quedó corregida el 2026-09-23 para afirmar sólo lo que el registro sostiene.

### Qué queda por observar

Una sola corrida no establece comportamiento. Lo que conviene vigilar con más encuentros:

- **Rango comprimido**: cuatro dominios en 2 y uno en 1. Puede ser el encuentro, que es corto,
  o tendencia central del modelo.
- **La frontera cero / no evaluable**, que es donde discrepó.
- **Si alguna vez intenta un evento no definido**, que el esquema rechazaría, pero conviene
  saber con qué frecuencia lo intenta.

---

## 7 · Segunda corrida real: un encuentro donde el evento sí ocurrió (2026-09-23)

La primera corrida no pudo probar lo más importante, porque en ese encuentro **no ocurrió
ningún evento crítico**. Esta segunda usa el tromboembolismo `pulmonary_embolism_33f` tal como
se jugó el 2026-09-22, donde el residente administró alteplasa sin hipotensión sostenida en una
paciente operada doce días antes. **Una llamada a `gpt-5-mini`, 54 s, costo estimado bajo
US$0,03.** Propuesta cruda en `local-data/paid_runs/2026-09-23_rubric_proposal_embolism.json`.

### Qué propuso

| Dominio | Puntaje | |
|---|---|---|
| D1 · Gravedad y priorización | **3** | Reconoció la presentación de alto riesgo contra el anclaje de ansiedad y buscó evidencia objetiva del ventrículo derecho |
| D2 · Evaluación e interpretación | **3** | |
| D3 · Manejo seguro | **0** | *"administered systemic thrombolysis (alteplase 100 mg) despite the record showing no sustained hypotension and a recent surgical site"* |
| D4 · Seguimiento | **2** | |
| D5 · Adaptación y continuidad | **1** | |

**Evento crítico propuesto:** `pe_unindicated_thrombolysis`, el que el caso define.

> Evidencia del disparador: *"An executed thrombolysis action is recorded (trace:3). The same
> trace documents that the systolic blood pressure was not sustained in the hypotensive range."*
>
> Exclusiones revisadas: *"the record does not show sustained hypotension within the engine's
> own criterion; the surgical history indicating a recent operative site is present."*

**No propuso `pe_no_anticoagulation`**, el otro evento definido para este caso, y es correcto:
la heparina sí se administró.

### La aritmética completa, con el docente confirmando

```
Base 9/15 · Penalty -3 · Adjusted 6/15 · 1 confirmed critical event(s)
```

Aquí se ve **el doble peso declarado**: el mismo hecho baja D3 a 0 **y además** cuesta la
penalización de seguridad. Es deliberado, y los informes lo dicen con esas palabras.

### Qué demuestra esta corrida que la primera no

- El modelo **propone el evento definido cuando corresponde**, citando la decisión y el minuto.
- **Revisa las exclusiones antes de proponer**, que es lo que impide culpar al residente de una
  limitación del motor.
- **No propone el otro evento definido** cuando no aplica: no dispara todo lo que tiene a mano.
- El descriptor de D3 se usó como está escrito: *"ordena algo claramente peligroso en este
  contexto"* es exactamente un 0, no un 1.

### Lo que sigue sin establecerse

Dos encuentros no son comportamiento. El rango sigue siendo estrecho en los dominios que no
tocan el evento, y la frontera cero / no evaluable —donde discrepó en la primera corrida— no
volvió a ponerse a prueba aquí.
