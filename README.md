# Management Reasoning Simulator — Curriculum pilot v0.11.0

## Longitudinal objective tracking

Completed resident encounters can now support several separately reviewed
objectives. Faculty select actual trace evidence, assess the simulated management
component, and record depth, support needed, context and feedback. Only a
satisfactory faculty assessment advances its objective's counter, at most once
per encounter. The counter stops at the configured target; the complete encounter
record is retained. Repeated submissions and simultaneous reviews cannot add
extra credit.

Numeric targets and faculty confirmation are separate. Administrators can adjust
the program targets with a reason; faculty can confirm, reopen or void an
observation with an audit trail. Reopening preserves the count. The eight initial
targets were supplied by the program owner and are not represented as verified
Royal College assessment requirements. These counts cover simulated components,
not whole workplace EPAs. Trauma and end-of-life objectives are listed for planning
but cannot receive credit from the currently implemented cases.

- [Objective scope, depth and counting rules](docs/OBJECTIVE_TRACKING.md)

## Curriculum and individual accounts

The curriculum pilot includes invitation-based resident, faculty and administrator accounts,
persistent encounters, internally assigned learning challenges, and bounded AI
composition of PS001 variants. Residents see the clinical presentation first;
the specific objective is disclosed in the post-encounter review. Faculty can
select any of the three implemented challenges in a sandbox excluded from
resident progress.

Account mode is opt-in. The existing `APP_PASSWORD` gate remains the default
until `MRS_AUTH_MODE = "accounts"` and persistent PostgreSQL storage are configured.
The stable application on `main` does not need to change.

- [Activation, local startup and verification](docs/SETUP_v0.11.0.md)
- [Curriculum mappings, evidence rules and generation limits](docs/CURRICULUM_PILOT.md)

Three challenges are executable; the proposed 30-challenge curriculum is not yet
fully implemented. Faculty review supports formative progress and does not certify workplace competence.
The generator chooses reviewed software options, stores a frozen specification,
and falls back to a predefined local variant if the provider fails. Clinical
profile calibration and deployment-specific PostgreSQL verification remain
necessary before resident assessment.

## AI language interpretation

This branch adds an optional OpenAI language-normalization layer. The model converts
free-form or mixed-language learner input into conservative canonical clinical text.
The existing deterministic parser reparses that text, validates supported actions,
and remains solely responsible for execution and patient physiology.

The integration fails closed: if the API is unavailable, confidence is low,
ambiguity remains, or a numeric value changes, the application automatically uses
the deterministic v0.8.21 interpreter. The learner's original text is preserved in
the Management Trace. For language interpretation, only learner text and the
visible patient state are sent to the API; hidden physiology and review data are
not included. The separate encounter-generation request uses an internal learning
objective and approved profile/scene options, with no resident identity or trace.

Configure the separate Streamlit test app under **Settings → Secrets**:

```toml
OPENAI_API_KEY = "your-project-api-key"
OPENAI_MODEL = "gpt-5.6-luna"
```

Never commit a real API key to GitHub.

## Dynamic learner-visible ECG

The ECG panel now includes a responsive, synthetic lead-II rhythm strip that follows the learner-visible patient state. It begins as narrow-complex atrial fibrillation with rapid ventricular response in PS001, remains irregular when rate control slows the ventricular response, changes to sinus rhythm after successful cardioversion, and displays organized electrical activity when the simulated state is PEA.

### What changed in v0.8.21

- The expanded ECG panel displays a five-second lead-II tracing instead of text alone.
- Rhythm morphology and ventricular rate update after every simulated intervention.
- AF has irregular R–R intervals, fibrillatory baseline activity, no consistent P waves, and narrow QRS complexes.
- Sinus rhythm has regular R–R intervals, a P wave before every narrow QRS, and a visible T wave.
- PEA retains organized electrical activity while explicitly stating that no palpable pulse is present.
- The tracing includes ECG paper, a calibration pulse, and the labels `25 mm/s` and `10 mm/mV`.
- The panel identifies the strip as synthetic and educational and does not invent ischemia, axis, chamber enlargement, or interval abnormalities that are not defined by the case.

## Preserved from v0.8.20: lower-pressure PS001 entry

PS001 now opens at **90/54 mmHg (MAP 66)** instead of 100/60 mmHg. The initial presentation states the pressure explicitly, and the internal effective-MAP state starts at the same value so the first transition does not rely on a contradictory hidden baseline. All prior semantic reasoning, procedural sedation, trajectory review, and PDF export behavior is preserved.

### What changed in v0.8.20

- PS001 begins at 90/54 mmHg with AF at 162/min, capillary refill of 5 seconds, cool extremities, and alert mental status.
- The narrative and live monitor now expose the same starting blood pressure.
- The new starting MAP is protected by a dedicated regression, bringing the active suite to fifty-four scripts.

## Preserved from v0.8.19: trajectory-grounded comparison, semantic repair, and reliable PDF export

This maintenance build repairs the full review/export sequence demonstrated in the supplied v0.8.18 PDF. Expert comparisons now describe the action and patient state that actually occurred at each selected decision rather than selecting a static model by decision number alone. Free-text reasoning remains permissive while preserving the learner's meaning, and the PDF uses bundled embedded fonts with safer page grouping.

### What changed in v0.8.19

- Every selected review point receives an expert comparison grounded in its frozen trace event. Decisions 2, 7, and 8 therefore compare the actual fluid, late-shock fluid, and norepinephrine/ceftriaxone decisions; Decision 7 is no longer replaced by an unrelated cardioversion model.
- Static faculty drafts are used only when both the validated decision and the validated action match. Otherwise the simulator generates a descriptive, non-scoring comparison from the actual observable state, action, rationale, and response.
- Diagnostic purposes expressed naturally with `to assess`, `to evaluate`, or `to investigate` populate the management-priority slot without requiring a sentence stem.
- A pure reassessment stays a reassessment and is no longer exported as a new problem representation.
- Complete expected-effect clauses such as `pressure to increase and perfusion to improve` and `MAP to increase and peripheral perfusion to stop worsening` are preserved without truncation.
- `Extremity temperature` remains an outcome or reassessment variable and no longer triggers an unintended temperature measurement; an explicit temperature request or direct `fever?` query still does.
- Adaptation cues and thresholds are drafted from clinical conditions, not from treatment instructions, and no longer duplicate `norepinephrine should be titrated` as both cue and threshold.
- PDF export bundles and embeds Liberation Sans, keeps related response/review blocks together when space permits, and avoids the excessive word spacing and sparse page split seen in the supplied export.
- Etomidate and midazolam remain executable procedural-sedation agents and are sequenced before synchronized cardioversion.
- Fifty-three active regressions protect semantic capture, slot separation, non-blocking context checks, pending-order integrity, procedural sedation, physiology, trajectory-grounded review, adaptation drafting, and exports.

## Preserved from v0.8.17: context-sensitive semantic slot separation

- A contrastive appraisal such as `Although the rhythm is now sinus, reduced effective circulating volume may still be contributing to incomplete perfusion recovery` is accepted as the working model.
- `I want to improve preload and tissue perfusion` remains the management priority and is no longer copied into the expected-effect field.
- The separate statement `I expect improved blood pressure, capillary refill, and extremity temperature...` supplies the expected effect exactly as intended.

## Preserved from v0.8.16: flexible semantic reasoning capture

- Compact problem statements such as `Patient hypotensive, slow perfusion...; urinalysis positive for infection` populate the working-model field without requiring `My working model is`.
- When the learner states both the clinical problem and the expected physiologic direction, the simulator can derive the bounded management goal from that meaning—for example, `improve arterial pressure and tissue perfusion`—without deriving it from the treatment alone.
- Reassessment variables and reassessment timing are checked separately. `Reassess perfusion, HR, BP` therefore preserves those variables and asks only for the omitted time.
- Common variants such as `urianalysis`, `urinanalysis`, `rythm`, and ordinary dictated phrasing are normalized for interpretation while the original learner entry remains visible.
- A statement such as `tachycardia` when the current HR is 96/min creates a neutral context check; it never blocks execution. The learner may clarify whether the term refers to relative tachycardia or an earlier state.
- If the patient changes while diagnostic results are pending, the timeline now adds a learner-facing clinical update instead of allowing silent deterioration between results.
- Previously recognized content prefills the guided fields, and natural-language follow-ups fill only missing fields rather than overwriting reasoning already supplied.
- Etomidate and midazolam remain executable as procedural sedation, execute before synchronized cardioversion, and remain visible in Treatments, Management Trace, and exports.

## Preserved from v0.8.15: executable procedural sedation

- Etomidate and midazolam ordered for procedural sedation are parsed as one executable sedation action with medication, dose, units, and IV route.
- A compound sedation–cardioversion order is held as one bundle until prospective reasoning is complete; neither action changes the patient before that point.
- When released, procedural sedation executes before cardioversion even if the learner mentioned the shock first.
- A bounded, decaying sedation signal distinguishes transient sedation from neurologic deterioration.
- Other unsupported analgesic or sedative medications remain visible as recognized but not executed.

## Preserved from v0.8.13: direct therapeutic goals as management priorities

This build recognizes a directly stated therapeutic goal as the learner's management priority while keeping the treatment used to pursue it separate. Clinical physiology and review logic are unchanged from v0.8.12.

### What changed in v0.8.13

- Direct goal language such as `I want to control heart rate with diltiazem` is recognized as the priority `control heart rate`.
- The treatment introduced by `with` remains an action and is not appended to the priority field.
- Equivalent constructions using `will`, `would`, `need`, `plan`, or `intend` are accepted when followed by a management-directed verb such as `control`, `restore`, `support`, `treat`, or `stabilize`.
- A medication proposal alone, such as `I want to give diltiazem`, still does not satisfy the reasoning requirement.
- The literal learner entry from the classroom screenshot is protected end to end, and forty-seven active regressions preserve prior trajectories and exports.

### Preserved from v0.8.12

- Natural phrasing such as `I would try to control heart rate` is recognized as an explicit management priority (`control heart rate`).
- Equivalent constructions such as `I would attempt to restore perfusion` are accepted without requiring `My priority is` or the word `first`.
- The relaxation remains bounded: naming a medication trial alone, such as `I would try diltiazem`, is not relabeled as a clinical problem priority.
- The literal learner entry that exposed the defect is protected end to end: all four reasoning elements are recognized, the order is not unnecessarily held, and diltiazem executes only once.
- Forty-six active regressions protect natural phrasing, coreference, guided completion, pending-order integrity, physiology, review, and exports.

### Preserved from v0.8.11

- A leading pronoun such as `it`, `this`, or `that` is resolved only when the learner has supplied a nearby explicit antecedent. For example, `I'm addressing heart rate first because I think it is the primary problem` is stored as `heart rate is the primary problem`.
- If no reliable antecedent exists, the simulator leaves the working model incomplete and asks the learner instead of inventing a clinical referent.
- Guided reasoning completion is labeled `REASONING COMPLETION` in the timeline rather than appearing as a second `YOU` intervention.
- Completed reasoning is displayed with explicit field labels (`Working model`, `Management priority`, `Expected effect`, and `Reassessment`) so fragments are not joined into malformed sentences.
- Forty-five active regressions protect coreference, completion display, semantic capture, pending-order integrity, physiology, review, and exports.

### Preserved from v0.8.10

- The reasoning gate now recognizes equivalent natural language such as `I'm addressing heart rate first`, `AF is the primary problem`, and `the patient should feel better`.
- Common dictation and typing variants such as `i.m` are normalized before interpretation.
- A learner may continue to answer in free prose; exact labels such as `My priority is` are not required.
- When meaning is still incomplete or ambiguous, the held-order panel provides editable sentence starters for the working model, management priority, expected effect, reassessment variables, and reassessment time.
- Recognized content is prefilled in those fields, so the learner completes only what is genuinely missing.
- The structured fallback writes the learner's own wording directly into the held order and does not depend on reparsing a template sentence.
- Repeated incomplete attempts update one active clarification instead of accumulating duplicate `ORDER HELD` blocks in the encounter timeline.
- A vague reassessment such as `reassess the patient` still requests specific variables; conceptual flexibility does not remove the need for an observable target and timing.
- Forty-four active regressions protect semantic capture, guided completion, prompt deduplication, pending-order integrity, physiology, review, and exports.

### Preserved from v0.8.9

- Every executable management intervention now requires four prospective elements: working model, management priority, expected effect, and a specific reassessment target with timing.
- If one or more elements are missing, the simulator holds the interpreted order, keeps the patient state unchanged, and asks only for the missing elements.
- The learner can answer with the missing reasoning alone; the original intervention is retained and executes once the four elements are complete.
- Diagnostic requests, clinical questions, and reassessment-only turns remain available without the gate.
- Faculty can deliberately release a held order by typing `execute without complete reasoning`; the override is displayed and recorded.
- In v0.8.9, unsupported sedation and analgesia orders such as etomidate, midazolam, and fentanyl were disclosed before the supported part of a compound order proceeded. v0.8.15 superseded that limitation for etomidate and midazolam; other unsupported medications remain explicitly non-executed.
- Retrospective evidence such as `POCUS shows...` remains reasoning context and no longer triggers a new ultrasound.
- Forty-three active regressions protect the reasoning gate, pending-order integrity, diagnostic scoping, unsupported-action disclosure, physiology, review, and exports.

### Preserved from v0.8.8

- In `give 1000 NS IV ... initiate O2 3lt`, the simulator now administers exactly `1000 mL` of normal saline and oxygen at `3 L/min`.
- A quantity directly attached to a named crystalloid takes priority over other numbers in the same learner turn.
- Oxygen quantities are excluded from the fluid parser even when `/min` is omitted or common shorthand such as `lt` is used.
- `nassal canula` and `initiate O2 3lt` are accepted as the intended nasal-cannula order.
- If a crystalloid is named without a volume while oxygen flow is present, the simulator asks for the fluid volume instead of silently borrowing the oxygen number.
- A literal full-pipeline regression protects the learner phrase that exposed the defect, and forty-two active regressions preserve the existing trajectories and exports.

### Preserved from v0.8.7

- `Download PDF` is available beside Markdown and JSON at every review stage, including incomplete drafts.
- The PDF contains Management Trace, Decision Review, Expert Comparison, and Prospective Adaptation Plan as distinct sections.
- The report uses printable US Letter pages, repeated case/version headers, page numbers, compact clinical cards, and a clear Draft/Complete status.
- A prior attempt can also be recovered with `Previous PDF` during `Adapt & Repeat`.
- PDF generation uses the same privacy-safe export payload as Markdown and JSON and does not expose hidden physiology or developer state.
- A dedicated regression verifies a valid PDF structure, extractable text, section completeness, Unicode normalization, and absence of private engine keys.
- Forty-one earlier regressions preserve all prior physiology and workflows.

### Preserved from v0.8.6

- The validated PS001 trajectory now selects Decisions 3, 7, and 9 for review: cautious rate control, electrical success versus clinical benefit, and flow-directed support.
- Each selected PS001 decision has a structured faculty-validation draft with framing, priority, key cues, one defensible action, trade-off, and reassessment targets.
- Decision 8 now preserves the learner's explicit inference that electrical conversion alone did not restore forward flow and the expectation that sinus rhythm remain stable.
- Decision 11 rationale ends at the learner's stated causal clause instead of absorbing subsequent actions, expectations, and reassessment language.
- Management Trace headings and response changes use explicit separators; Markdown metadata and timeline items remain legible when copied or rendered.
- A literal eleven-entry PS001 regression protects the complete clinical trajectory, reasoning capture, review selection, expert-model mapping, and export structure.

### Preserved from v0.8.5

- The initial PS001 POCUS retains the validated `preserved to hyperdynamic LV systolic function` finding.
- After the validated two-dose diltiazem sequence and evolving low-output state, a repeat POCUS reports `moderately to severely reduced LV systolic function`.
- Subsequent inotropic recruitment can improve the next POCUS classification, so imaging follows the simulated trajectory rather than a fixed case value.
- IVC and lung findings remain separately state-aware; the PS002 POCUS phenotype remains unchanged.

### Preserved from v0.8.4

- `antibiotics have been started` remains retrospective clinical context and no longer administers another antibiotic action.
- Direct commands such as `administer ceftriaxone 2 g IV`, `start broad-spectrum antibiotics`, and compact drug-and-dose orders remain executable.
- Completed, retrospective, continued, deferred, negated, and merely considered antibiotic mentions remain non-actions.
- The literal first three PS001 classroom-test entries verify that ceftriaxone is given once and that the third response reports only diltiazem 5 mg IV.

### Preserved from v0.8.3

- `before committing to rate control or cardioversion` remains reasoning and does not request joules or execute a shock.
- Cardioversion now requires explicit action language such as `cardiovert`, `perform cardioversion`, or a compact energy order.
- Negated, deferred, preparatory, conditional, and retrospective cardioversion mentions remain non-actions.
- A targeted request about fever or urinary symptoms now returns the PS001 focused history.
- PS001 history reveals dysuria, urinary frequency, chills, poor intake, and weakness.
- PS001 urinalysis now supports the intended urinary infectious source when ordered.
- The literal PS001 classroom-test entry that exposed the cardioversion defect remains protected.

### Preserved from v0.8.2

The learner-visible patient state remains continuously available during the encounter, and every executed intervention creates an immutable vital-sign snapshot.

- A sticky `Live patient state` monitor remains visible while the learner scrolls through the encounter.
- The monitor displays simulation time, BP/MAP, HR/rhythm, SpO₂/respiratory support, respiratory rate/work of breathing, CRT/extremities, and mental status.
- Every `PATIENT RESPONSE` appears in a bordered card immediately after the learner's intervention.
- Each response card stores the vital signs observed at that moment; later clinical changes cannot rewrite earlier cards.
- Stored response snapshots contain only learner-visible state and exclude hidden physiology.
- Persistent visibility, historical snapshot integrity, privacy, and the prior clinical/review suite remain protected.

### Preserved from v0.8.1

This build continues to operationalize `ADAPT & REPEAT`. After completing the review cycle, the learner can start a clean repeat encounter while carrying the prospective Adaptation Plan forward as a visible learning intention.

- `Repeat Encounter with This Adaptation Plan` becomes available only when Decision Review, Expert Comparison, and Adaptation Plan are complete.
- The repeat begins as `Attempt 2` with fresh patient state, event history, Management Trace, self-review, comparison responses, and autosave widgets.
- The prior Adaptation Plan appears above the encounter as a six-field `Carry-Forward Learning Goal`.
- The new Management Trace records only actions actually taken in the repeat; carrying a plan forward does not claim the learner followed it.
- The complete prior-attempt report remains separate and downloadable as Markdown or JSON during the repeat.
- Current-attempt exports include `learning_cycle`, attempt number, carry-forward plan, and a privacy-safe prior-attempt summary.
- Export schema advances to `management_reasoning_decision_review_v3`.
- Clean reset, plan continuity, attempt-aware export, previous-record preservation, and the existing clinical/review suite remain protected.

### Preserved from v0.8.0

- The workflow now has four stages: `Decision Review`, `Expert Comparison`, `Adaptation Plan`, and `Final Summary`.
- Expert content remains hidden until every learner-reflection field is complete.
- `Lock Decision Review & Reveal Expert Comparison` freezes an independent copy of the learner's pre-comparison reasoning.
- Decisions 2, 9, and 11 in the validated PS002 trajectory each receive a structured model containing framing, priority, cues, one defensible action, trade-off, and reassessment targets.
- The model is explicitly labeled a non-scoring faculty-validation draft, not an answer key.
- The learner records alignment and a transfer-oriented adjustment for each comparison point.
- Pre-reveal Markdown/JSON exports contain no expert content; post-reveal exports preserve Decision Review and Expert Comparison as separate layers.

### Preserved from v0.7.16

- Only one selected decision is open for editing at a time.
- Other review points appear as collapsed cards with completion status and a saved-response preview.
- A live progress indicator tracks completed decisions, plan fields, and all autosaved fields.
- Review text is autosaved when the learner leaves a field or moves to another stage; there is no manual Save button.
- Adaptation Plan drafts five fields from the learner's latest relevant reflection while deliberately leaving `Next management priority` for the learner.
- Every suggested plan field remains editable. Once edited, later reflection changes cannot overwrite the learner's text.
- Draft Markdown and JSON exports remain available at the top of every review stage.
- Final Summary provides a compact completion overview, collapsed decision synthesis, and prospective plan before the final download controls.

### Preserved from v0.7.14

- `Complete Encounter & Begin Review` freezes the final patient state and Management Trace.
- Retrospective reflection remains separate from the descriptive trace.
- Each selected review point captures working-model update, priority-changing evidence, alternative action, and expected response/reassessment.
- Learner exports exclude hidden engine physiology and developer-only state.
- Markdown and JSON include Management Trace, Decision Review, and Adaptation Plan.
- The canonical Management Trace definition remains unchanged.

## Run on macOS

If the folder is already unzipped in `~/Downloads`:

```bash
cd ~/Downloads/management_reasoning_simulator_v0.8.21
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

If only the ZIP is present:

```bash
cd ~/Downloads
unzip management_reasoning_simulator_v0.8.21.zip
cd management_reasoning_simulator_v0.8.21
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

Open `http://localhost:8501` if the browser does not open automatically.

## Validate

```bash
cd ~/Downloads/management_reasoning_simulator_v0.8.21
python3 -m py_compile app.py
python3 run_regressions.py
```

Expected final line:

```text
PASS: 53 active regression scripts
```

## Guided testing

See `INSTRUCCIONES_DE_PRUEBA.md` for the exact PS001 classroom trajectory, the preserved PS002 trajectory, self-review and comparison responses, Adaptation Plan, repeat-attempt checks, and PDF/Markdown/JSON validation.

## Current scope

- This is a deterministic educational MVP, not a validated patient-care model.
- Management Trace, Decision Review, and Expert Comparison are descriptive and non-scoring.
- Suggested Adaptation Plan text is a deterministic reuse of the learner's own reflection, not an expert recommendation or AI-generated clinical judgment.
- The PS001 and PS002 expert models are faculty-validation drafts and must be clinically reviewed before research or curricular deployment.
- The app does not provide a clinical grade or designate one uniquely correct management path.
- Repeat attempts currently use the same deterministic clinical trajectory; controlled variants and between-attempt performance comparison are not yet implemented.
- Diagnostic values are deterministic outputs of the simulated physiology; they are not a general laboratory model.
- Explicit extubation, ventilator liberation, neuromuscular blockade, and sedatives other than the modeled etomidate/midazolam procedural regimen remain outside this build.
- Historical regression scripts are preserved for development lineage; `run_regressions.py` is the maintained active suite for v0.8.21.
