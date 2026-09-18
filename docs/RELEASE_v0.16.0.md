# v0.16.0 — Cognitive challenges across distinct clinical families

This note describes the prepared development release. It does not establish that
the code has been deployed or that the Streamlit service is running this version.
The intended deployment branch is `clinical-encounter-v0.13`; `main` and
`ai-integration-v0.9.0` are outside this release's update scope.

## Catalog

Eight cognitive challenges join the three existing management-reasoning
foundations, for eleven selectable local objectives. The bias name identifies an
educational opportunity. It is not a diagnosis of the learner's reasoning or an
automatic competence judgment.

| Code | Cognitive focus | Compatible clinical families |
|---|---|---|
| R1-05 | Anchoring | Pneumonia; pulmonary edema |
| R1-06 | Premature closure | Hypoglycemia; opioid-associated hypoventilation |
| R2-02 | Confirmation bias | Acute coronary syndrome; pulmonary embolism |
| R2-03 | Availability bias | Pulmonary embolism; pneumonia |
| R1-07 | Framing effect | Acute coronary syndrome; hypoglycemia |
| R2-04 | Representativeness bias | Acute coronary syndrome; pulmonary embolism |
| R2-05 | Search satisficing | Gastrointestinal bleeding; pneumonia |
| R3-01 | Action bias | Pulmonary edema; asthma |

The existing foundations remain R1-03 (relate tachycardia to the patient's
condition), R1-04 (anticipate and check an intervention's effect), and R2-01
(distinguish pressure, flow, and perfusion). Their earlier encounter profiles are
retained. The new cognitive objectives use the new case families.

There are eight new families and sixteen authored patient variants:

| Family | Authored variants |
|---|---|
| Pneumonia with systemic illness | Woman, 46; man, 83 |
| Acute cardiogenic pulmonary edema | Man, 58; woman, 75 |
| Acute coronary syndrome | Man, 54, inferior ST-elevation pattern; woman, 66, ST-depression pattern |
| Pulmonary embolism | Woman, 33; man, 61 |
| Acute severe asthma | Woman, 24; man, 49 |
| Upper gastrointestinal bleeding | Man, 57; woman, 72 |
| Hypoglycemia with altered mental status | Man, 28; woman, 76 |
| Opioid-associated hypoventilation | Man, 35; woman, 67 |

## What AI generates and what remains authored

The AI selects a compatible clinical-family and patient-variant pair for the
chosen objective. Its output is restricted to identifiers and checked against
the available pairs. It does not freely invent a new diagnosis, investigation
result, drug effect, or numerical trajectory. An unavailable or invalid AI
selection uses a reproducible local selection from the same compatible cases.

Each encounter freezes its selected patient's demographics, history,
examination, investigations, initial observations, visual profile and clinical
mechanism. The seed, selection provenance, version and specification digest are
retained. Replaying that saved specification is distinct from asking a model to
make the same selection again.

The photograph is generated from the selected fictional patient's age, sex and
bounded visible observations. Conversational AI selects recorded history
sentences; it cannot author additional patient facts. Common English and Spanish
questions also have local source-based matching. Where the patient cannot provide
a history, explicitly authored collateral sources remain identified as such.

## Encounter behavior

- Histories, examinations, investigations and treatment responses belong to the
  selected family. New families do not inherit the earlier AF/urinary-infection
  history or the 70-year-old man's image identity.
- Broad opening questions return the presenting concern. Targeted questions can
  retrieve the available relevant facts immediately; answers are not withheld
  until the learner chooses a treatment.
- The family engine uses the selected clinical mechanism, elapsed simulated
  time and executed actions. Choosing a bias label or particular wording does
  not reward or punish the learner through the patient's physiology.
- The bedside monitor uses current observations. A 12-lead ECG acquisition is a
  frozen educational tracing from the case's implemented electrical profile.
- Laboratory results retain the values at collection and record both collection
  and availability times. Treatment during processing does not rewrite the sample.
- Oxygen switches bind the final requested device and flow. Missing settings
  require clarification before the order is executed. Treatment records retain
  the actual doses and distinguish delivered fluid from a pending infusion.
- Photographic updates use the original patient reference. Current-state image
  selection is isolated by encounter identity and visible-state signature. A
  stale or rejected photograph is not displayed as the current patient.
- Reduced spontaneous respiratory effort is represented separately from normal
  breathing and increased effort. Active bag-mask ventilation permits only the
  clinician hands needed to hold the seal and bag. Device precedence is invasive
  ventilation, bag-mask ventilation, NIV, then supplemental oxygen.
- The reasoning trace and later reflection are descriptive evidence for faculty
  discussion. The catalog does not automatically declare that a bias occurred.
- Background image failures no longer trigger a full-page rerun that could
  discard the student's submitted question, order or reasoning. Image retries
  remain available without interrupting the clinical workflow.

## Validation scope and limits

Final local regression on 2026-09-13: `python -m pytest -q` completed with
**705 tests and 180 subtests passing**. This includes actual Streamlit submit,
reasoning, diagnostic, persistence and image-failure recovery flows.

Automated checks exercise catalog compatibility, all sixteen authored case
identities and histories, reproducible selection and fallback, source isolation,
appearance contracts, support-device precedence, image screening and cache
isolation. Provider behavior is exercised with test doubles where appropriate.

No provider credentials were available for live image-generation and image-review
requests during this preparation. Actual generated photographs, provider latency,
and model screening performance therefore remain untested for this release.
Automated image screening can reject contradictions but can also make mistakes;
it does not establish clinical realism or validate observations from a photograph.
A still image cannot demonstrate respiratory rate, true responsiveness or tissue
perfusion. When a current image is pending or unavailable, the monitor and recorded
observations remain available.

The case bank and numeric treatment trajectories are authored teaching models
requiring faculty review. Their magnitudes, delays, recurrence behavior and
thresholds are not validated clinical predictions or a complete clinical decision
support system. A simulated referral records contact; it does not by itself mean
that reperfusion, endoscopy or another definitive procedure has occurred.

The 12-lead ECG is a synthetic waveform model, not a real patient recording or a
validated diagnostic ECG generator. The implemented patterns do not cover every
ECG finding, drug effect or disease stage encountered in practice. See
`ECG_MODEL.md`, `docs/COGNITIVE_CATALOG.md`, and the sources recorded in
`clinical_cases.py` for the stated modeling and educational scope. The cited
clinical and educational literature does not validate this simulator or its
assessment reliability.
