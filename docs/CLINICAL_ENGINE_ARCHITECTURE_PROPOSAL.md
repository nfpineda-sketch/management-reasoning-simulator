# Clinical Engine Architecture Proposal — Management Reasoning Simulator

| | |
|---|---|
| Repository | `nfpineda-sketch/management-reasoning-simulator`, branch `clinical-encounter-v0.13`, commit `13592e4` |
| Date | 2026-10-06 |
| Type | **Architecture decision only.** No code, prompt, scoring rule, case logic or Trace logic was changed. Nothing was committed, pushed or deployed. |
| Primary source | `CLINICAL_ENGINE_AUDIT.md` (same date, same commit), read in full before this document was written |
| Additional evidence | Read-only inspection of the repository, done only where the audit did not settle an architectural question (§2.2) |
| Reader | Written for a reviewer **without** repository access |

---

## 0. How to read this document

### 0.1 Tags

| Tag | Meaning |
|---|---|
| **[AUDIT §n]** | Established in `CLINICAL_ENGINE_AUDIT.md`, section n, by execution or code reading. |
| **[CODE]** | Established now by reading repository code (`file:line`). Not executed unless stated. |
| **PROPOSAL** | A design recommendation. It does not exist yet. |
| **DECISION** | A choice that depends on methodology or clinical judgment. Faculty must make it; the proposal only gives a default. |
| **UNKNOWN** | Neither the repository nor the audit can establish it. |

### 0.2 Vocabulary

| Term | Meaning |
|---|---|
| Family engine | `family_engine.py` and its mechanism modules. It runs the 31 bank cases. |
| Legacy engine | The PS001 path: the parser and executor inside `app.py`, plus `clinical_physiology.py`. |
| Coupled / generated engine | `coupled_encounter.py`. It runs AI-authored cases on the legacy physiology core. |
| Channel | A shared physiological state variable of the proposed common core (§7). |
| Module | Disease-specific mechanism code that acts on channels (§8). |
| Fate | The final, recorded outcome of one resident order: executed, held, unrecognized, and so on (§9). |

---

## Decision summary

### Recommendation

**C — hybrid architecture: a small common physiologic core plus disease-specific modules.** It is built by **evolving the family engine**, not by adopting the legacy core.

### Why

1. **Most audit failures sit outside the physiology model.**
   - Six of the top seven risks the audit ranked by their potential to distort the Trace are **not** physiology-architecture problems. They sit in the input, action, time, observation, UI and routing layers, and in module-timer design. Examples: silent non-execution, the legacy path reachable by residents, waiting and reassessment semantics, whole-bundle holds, contradictory displays, management-independent timers.
   - No physiology choice fixes them. A **contract-first Phase 0** (§13) does, and every option needs it.
2. **The physiology does have one architectural defect.**
   - There is no shared physiological state through which every disease and every treatment acts.
   - As a result, coupling is re-invented in each of 12 families, inconsistently. Examples: trauma blood loss never reaches perfusion, pressors only shift BP, asthma never changes BP.
   - Generic actions (sedatives, fluids, pressors, diuretics) therefore mean different things in different cases. That makes cross-case reading of the Management Trace unsafe.
3. **Option A converges to C.** Fixing coupling family by family re-implements the same shared variables twelve times.
4. **Option B is the "more physiology" trap.** The legacy core:
   - has 57 hidden variables and 14 phenotype drivers, centred on atrial fibrillation and sepsis [CODE];
   - lacks haemoglobin, glucose, potassium, ventilation and airway;
   - receives disease mechanisms only as offsets to displayed vital-sign targets [CODE], not as changes to its own state;
   - carries adapter calibration patches (heart rate, lactate, mental status) that exist only for generated cases [CODE].
5. **C keeps everything that works.** It keeps the deterministic minute loop, delivery pools, result clocks, atomic commit and the existing disease modules. It adds roughly ten shared channels that make treatment effects, observations and causal attribution consistent and checkable.

### Sequencing

- The resident pilot should **not** wait for the core migration.
- It should run on the current family engine after Phase 0, with a frozen engine version and an accepted case list.
- The core migration follows in shadow mode, calibrated against golden trajectories, before residents see it.

### Target pipeline (detail in §15)

```
Resident input → Submission guard → Intent parser (with coverage) → Execution ledger (fates)
   → Scheduler / time-event engine ⇄ [Disease modules ⇄ Common core]
   → Observation layer (single source of truth) → Resident display
   → Management Trace v2 (fates, provenance, observation snapshots, limitation flags)
   → Deterministic pre-analysis guards → Post-encounter AI analysis → Faculty confirmation
```

---

## 1. Project goal and decision criterion

### 1.1 Goal

The simulator exists to make **management reasoning** visible over time:

```
observe → interpret → prioritize → act → anticipate → reassess → adapt
```

It is **not** a high-fidelity physiology simulator.

### 1.2 Decision criterion

> What is the minimum clinical-engine architecture such that no important conclusion in the Management Trace depends on an artificial limitation, inconsistency, or hidden failure of the simulator?

### 1.3 Requirements derived from the criterion (PROPOSAL)

| # | Requirement | Why the criterion needs it | Audit evidence of the current gap |
|---|---|---|---|
| R1 | **Faithful action accounting.** Every resident order ends in one explicit, recorded and displayed fate. | Otherwise an engine failure looks like a resident omission. | §16 rank 1 (silent drops), rank 11 (duplicates) |
| R2 | **Shared physiological meaning.** The same intervention acts on the same physiological channel in every case. | Otherwise the same decision is judged against different physics in different cases. | §6.2 coupling matrix; §8 E |
| R3 | **Coherent consequences.** Effects of executed actions are direction-correct and proportionate for the decisions the curriculum assesses. Where no effect is modelled, that is declared, never silently zero. | Otherwise "no response" is read as "wrong treatment". | §8 H; §16 rank 7 |
| R4 | **One source of truth.** Every observable is derived from state, or explicitly declared static. | Contradictions mislead reassessment. | §11; §13 |
| R5 | **Coherent time.** Act → wait → observe → adapt, with critical events able to interrupt. | Otherwise timing conclusions become artefacts of phrasing. | §5; §16 rank 3 |
| R6 | **Attribution.** Every state change and event carries its cause: disease, treatment, scripted or logistic event, or engine limitation. | Analysis must not credit or blame the resident for what the engine scripted. | §9.2; §16 rank 6 |
| R7 | **Determinism and replay.** | Reproducible review; counterfactual analysis becomes possible. | §4 (already met) |
| R8 | **Validatable by faculty.** The model is small enough to review, with declared parameters and testable invariants. | An unvalidatable model cannot back educational claims. | §0.3 item 5 |

---

## 2. Current state

### 2.1 The three engines

| | Family engine | Legacy PS001 engine | Coupled / generated engine |
|---|---|---|---|
| Code [CODE] | `family_engine.py` 3,240 lines + 16 mechanism modules ≈ 3,060 lines; shared parser `family_parser.py` 5,308 lines | `clinical_physiology.py` 1,952 lines + legacy parser and executor inside `app.py` (≈ 7055–7456, 9048–9541) | `coupled_encounter.py` 584 + `generated_engine.py` 787 + mechanism adapters (`generated_airway/bleeding/congestion/glucose/opioid/pe.py`, `nitrate_hazard.py`) ≈ 680 |
| Cases | 31 bank cases, 12 families [AUDIT §1.1] | PS001, 3 profiles | AI-authored cases (none in the repository) |
| Hidden state | 1–2 main drivers per family (`circulation`, `lung`, `obstruction`, `reaction`, …) + module states [AUDIT §2] | 57 hidden variables; 14 "phenotype" drivers [CODE `clinical_core_defaults.py`] | Legacy core + authored deltas + mechanism states |
| Coupling | Partial and family-specific [AUDIT §6.2] | Strongest for hemodynamics [AUDIT §6.1] | Legacy core; mechanisms enter as display offsets [CODE] |
| Parser | Shared deterministic `family_parser` | Separate inline parser; silent drops [AUDIT §3.3] | Shared `family_parser` |
| Time | Minute loop; reassess 0–120; history/exam cost time | Different rules (history/exam 0 min) | Time only on explicit reassessment |
| Reachable by residents in the pilot configuration | Yes (8 challenges) | **Yes** (R1-03, R1-04, R2-01), contrary to pilot documents [AUDIT §1.1] | No |
| Test assets [CODE, approximate] | 103 test files reference the family engine or parser | 84 reference `load_engine`, `clinical_physiology` or PS001 (many exercise app functions, not only legacy physiology) | 33 |
| Total tests | 310 test files, about 3,300 test functions | | |

### 2.2 Facts established for this decision (beyond the audit)

**F1. The legacy core is centred on one scenario** [CODE `clinical_core_defaults.py`]
- `PHENOTYPE_FIELDS` (14): `effective_volume`, `vasomotor_tone`, `tissue_perfusion`, `sympathetic_drive`, `cardiac_function`, `inflammatory_drive`, `vasoplegia_severity`, `af_burden`, `af_causal_weight`, `pulmonary_congestion`, `fluid_tolerance`, `primary_respiratory_burden`, `contractile_reserve`, `low_flow_burden`.
- `INITIAL_HIDDEN` holds 57 keys, including drug depots for metoprolol, propranolol, diltiazem and amiodarone, and AF recurrence state.
- It has **no** haemoglobin, glucose, potassium, CO₂/ventilation or airway-resistance state.

**F2. In the coupled engine, disease mechanisms are display offsets, not core physiology** [CODE `coupled_encounter.py:159–221`, `clinical_physiology.py:569, 1008–1011, 1034, 1045, 1253`]
- `prepare_inputs` collects each mechanism's effects as deltas to SBP, DBP, HR, SpO₂, RR and CRT (bleeding, airway, PE, opioid, congestion, coronary).
- These become `physiology_inputs` that offset the core's **MAP target**, HR target, SpO₂ target, CRT and RR.
- They do not change the core's volume, tone or contractility.
- Consequence: a declared haemorrhage in a generated case lowers the displayed pressure, but not the core's `effective_volume`.
- Whether these offsets propagate to tissue perfusion and lactate is **UNKNOWN** from reading alone. The adapter adds its own lactate-production and clearance rules (`coupled_encounter.py:378–395`), and its comments describe a lactate that fell during deterioration and an HR held near 106/min. That suggests incomplete propagation. Per the brief's rule, comments are reported as statements of intent, not as verified behaviour.

**F3. Bank modules are already engine-agnostic to a degree** [CODE]
- The generated-engine adapters run the **same** bank modules (`asthma_ventilation`, `asthma_complications`, `pe_obstruction`, `glucose_rescue`, `opioid_reversal`, `acs_reperfusion`) against generated state.
- Disease logic is therefore reusable across engines; only its coupling to the physiology differs.

**F4. Management Trace v1 records the turn, not the item** [CODE `app.py:875–916`]
- Each turn records:
  - `learner_input`, `interpreted_action`, the reasoning fields and `reasoning_gate`;
  - `recognized_future_actions` and `future_details`;
  - `results_pending`, `execution_status` and `action_summaries`;
  - `state_before` and `state_after` snapshots;
  - `code_version`.
- **Missing:**
  - `execution_status` is one of four values **for the whole turn** (`executed`, `not_executed`, `clarification_required`, `terminal_locked`);
  - there is no per-order fate and no map of which parts of the text were not understood;
  - there is no cause attribution for state changes or events, and no engine-limitation flags.

### 2.3 What works and must be preserved [AUDIT §4, §5, §9]

| Asset | Where |
|---|---|
| Persistent longitudinal state; exact restore after reload | `state` + `save_session` (revision-checked) |
| Deterministic replay | the whole family engine |
| Minute-by-minute integration (time-step invariance) | `execute_family_bundle` loop |
| Delivery pools: fluids, blood, dextrose, timed infusions | `_queue_delivery`, `_advance_deliveries` |
| Result clocks with the collection-time snapshot | `_diagnostic`, `collection_state` |
| Treatment kinetics where implemented | modules |
| Disease progression; management-sensitive trajectories | family drift + modules |
| Logistics separate from physiology (cath lab, lysis, endoscopy gated by resuscitation) | `acs_reperfusion`, `_endoscopy_minute` |
| Atomic turn commit | `execute_family_bundle` |
| Explicit disclosure of unmodelled drugs and studies | `unexecuted_items`, `_validate` |
| No LLM in runtime physiology; evaluation never steers physiology | [AUDIT §7, §12] |
| Disease modules (≈ 3,000 lines of reviewed clinical logic) | 16 modules |

### 2.4 What is wrong, by layer (from the audit)

| Layer | Main verified problems |
|---|---|
| Input / action | Legacy silent drops; gate follow-up drops new orders; one unknown item holds the whole bundle; duplicates re-execute; "in 30 minutes" executed now; conditional plans never executed |
| Time | No "wait"; "reassess" without a number = 0 min; "give X and reassess" = 0 min with pre-treatment vitals labelled "After X"; no interruption by events; 120-min cap |
| Physiology | Partial coupling (trauma, anaphylaxis, bradycardia, asthma, opioid, hypoglycaemia, untreated oedema); pressor as a pure BP overlay; no harm from excess in several families; inconsistent arrest semantics; management-independent AV-block timer |
| Observation | Static history; static cardiac/abdominal/extremity exam; static potassium in hyperkalaemia; "Sinus bradycardia" with HR 0; narrative "arrest" with a pulse; legacy PEA with a BP |
| UI / persistence | Zero-gap double click loses the order; no idempotency key |
| Routing / config | Legacy PS001 reachable by residents in the pilot configuration |

---

## 3. The three options, defined in repository terms

| Option | Meaning in this repository |
|---|---|
| **A — Strengthen the family engine** | Keep `family_engine.py` with its per-family state and `_surface` formulas. Fix coupling, coverage, time, observation and terminal states family by family. |
| **B — Migrate to the legacy/coupled core** | Make `clinical_physiology.py` (main_ia_v1) the foundation for all cases. Re-express the 12 families as mechanisms on it, the way `coupled_encounter.py` does for generated cases. |
| **C — Hybrid: small common core + disease modules** | Replace the family engine's generic layer (`circulation`, `lung`, the generic parts of `_surface`) with an explicit core of about ten channels. Re-wire the existing modules to act **through** those channels. Keep the family engine's runtime: minute loop, pools, clocks, atomic commit, persistence. The legacy core is **not** adopted; some of its concepts are (pressure ≠ flow ≠ perfusion; low-flow burden; fluid tolerance). |

Every option also needs the architecture-neutral layers of §9–§12: action model, time model, observation model, Trace contract. They are evaluated separately in §6.

---

## 4. Design principles (PROPOSAL)

| # | Principle |
|---|---|
| P1 | **Minimum sufficient realism.** A variable enters the core only if (a) an assessed management decision depends on it, **and** (b) its absence produces a verified contradiction or a possible false inference. |
| P2 | **Declared beats emergent where validation matters.** Modules declare their effects on channels. Interaction happens only through the few core channels, with bounded gains. |
| P3 | **Deterministic, minute-stepped, bounded.** No stochastic physiology. Saturating responses and clamps everywhere. |
| P4 | **One state, many views.** Observables are pure functions of state, or explicitly static. |
| P5 | **Explicit fates.** Nothing the resident wrote disappears. |
| P6 | **"Unknown" is not "zero".** "No modelled effect" is a declared property of an action in a case, shown to the resident and recorded in the Trace. |
| P7 | **Calibrate before extending.** New physiology must first reproduce faculty-approved trajectories within tolerance, or show the faculty the differences. |
| P8 | **Separate assessment from physiology.** Evaluation metadata never steers the engine; the engine never infers competence. This is already true [AUDIT §7]. |

---

## 5. Evaluation of the options

### 5.1 Comparison table

**Scale:** 1–5, where 5 is the most favourable for the project. For risk, complexity and effort, 5 means the **lowest** risk, complexity or effort.

**What the ratings describe:** the end state after each option is implemented, assuming the architecture-neutral Phase 0 (§13) is done in every case.

**Ratings for C are design targets.** They are not yet demonstrated, and they stay UNKNOWN until the shadow-mode validation of §13.

| # | Criterion | A | B | C | Basis |
|---|---|---|---|---|---|
| 1 | Physiologic realism | 2 | 3 | 4 | **A:** algebraic offsets from one or two scalars per family. **B:** rich hemodynamics, but AF/sepsis-centric, missing Hb/glucose/K/ventilation/airway, mechanisms as display offsets (F1, F2). **C:** coherent channels for the assessed decisions; deliberately not high fidelity |
| 2 | Causal realism | 3 | 3 | 4 | **A:** core therapies causal; generic drugs family-dependent. **B:** native hemodynamic drugs causal; bank therapies need rebuilding. **C:** one shared drug table acting on channels in every case, plus disease-specific causality in modules |
| 3 | Temporal realism | 3 | 3 | 4 | Mostly orthogonal: the same time/event engine (§10) can serve any option. C designs channel kinetics once |
| 4 | Longitudinal coherence | 3 | 3 | 4 | All three persist state. C removes overlays without memory (pressors) and per-family arrest semantics |
| 5 | Management sensitivity | 3 | 3 | 4 | A and B are already strong for core choices [AUDIT §9]. C adds consistent sensitivity to generic actions and excess |
| 6 | Robustness to unexpected reasonable actions | 2 | 3 | 4 | **A:** each new action needs code in each family. **B:** generic for hemodynamic drugs only. **C:** generic channel effects + explicit "not modelled" |
| 7 | Reassessment fidelity | 2 | 3 | 4 | Depends on the observation layer (§11) **and** on coupling. A keeps decoupled perfusion signs (trauma, anaphylaxis, bradycardia) unless patched per family |
| 8 | Generalizability to new cases | 2 | 3 | 4 | **A:** within-family only. **B:** general for shock but tuned to one scenario. **C:** composition of modules on shared channels |
| 9 | Support for future AI-authored cases | 1 | 3 | 4 | **A:** no host for new conditions. **B:** the existing generated path, untested on real cases, with calibration patches. **C:** bounded authoring (pick modules + parameters in validated ranges); UNKNOWN until built |
| 10 | Deterministic reproducibility | 5 | 4 | 5 | B has seeded randomness inside transitions (amiodarone, cardioversion); replay is reproducible with the seed, but random draws complicate golden comparisons |
| 11 | Ease of validation | 3 | 1 | 3 | **A:** small formulas, but 12 different couplings to review. **B:** 57 interacting variables, tuned constants, adapter patches. **C:** new but small; golden traces and invariants |
| 12 | Risk of hidden bugs | 3 | 2 | 3 | **A:** patches add branches (≈ 76 family branches already [AUDIT §6.1]). **B:** high interaction. **C:** refactoring risk, mitigated by shadow mode |
| 13 | Complexity | 4 | 2 | 3 | |
| 14 | Migration effort | 4 | 1 | 2 | **B:** re-express 31 reviewed cases on a foreign core. **C:** re-wire modules, keep the runtime |
| 15 | Maintainability | 2 | 2 | 4 | **A:** coupling duplicated per family. **B:** opaque constants. **C:** one place per physiological meaning |
| 16 | Preserves working mechanisms | 5 | 2 | 4 | **C** keeps runtime and modules; trajectories are recalibrated against golden traces |
| 17 | Suitability for a resident pilot (if the option had to be finished first) | 4 | 1 | 2 | With the recommended sequencing the pilot runs on the Phase-0 family engine, so this criterion does not block C (§13) |
| 18 | Suitability for broader deployment | 2 | 2 | 4 | |
| 19 | **Risk of a false inference about management reasoning** (5 = lowest) | 3 | 2 | 4 | **Before Phase 0 every option scores 1:** silent omissions and time artefacts dominate. **After Phase 0:** A keeps inconsistent coupling and per-family "no effect" defaults; B adds opaque interactions and display-offset mechanisms; C gives channel-consistent effects with attribution |

### 5.2 Three observations behind the table

**1. A converges to C.**
- The coupling gaps in §6.2 of the audit share one missing piece: the family engine has no shared representation of volume, tone, pump, oxygenation, ventilation and perfusion debt.
- Fixing trauma (blood loss → perfusion), anaphylaxis (reaction → perfusion), asthma (obstruction → hemodynamics and fatigue), opioid (hypoxaemia → sympathetic response) and pressors (pressure vs perfusion) one family at a time rebuilds those shared variables repeatedly.
- C builds them once, which is cheaper than A over time.

**2. B adds physiology without adding the needed coherence.**
- The legacy core is richer where it was designed (AF with shock), but it lacks the channels most bank families need (Hb, glucose, K, ventilation, airway) (F1).
- Its existing way of hosting other diseases is to offset displayed targets (F2): exactly the decoupling that C is meant to remove.
- Its size makes faculty validation impractical.

**3. C must stay small.**
- C's main risk is scope creep toward a physiology simulator. Principle P1 and the exclusion list in §7.5 exist to prevent it.

---

## 6. Architecture versus bugs: classification of the audit's problems

**Categories:**

- **A** architectural (needs a different engine model);
- **B** engine / implementation (fixable within the current architecture; includes routing and configuration);
- **C** parser / input / action pipeline;
- **D** temporal semantics;
- **E** observation layer;
- **F** UI / persistence.

"Arch.-dependent?" asks whether the choice between options A, B and C changes the fix.

| # | Problem (audit reference) | Primary | Secondary | Arch.-dependent? |
|---|---|---|---|---|
| 1 | Legacy parser drops unrecognized drugs/consults silently (§3.3, §16 #1a) | C | B (routing) | No: retire the path or apply the ledger to it |
| 2 | Legacy engine reachable by residents (§1.1, §16 #2) | B (routing/config) | — | No |
| 3 | Reasoning-gate follow-up discards new orders (§17.7a) | C | — | No |
| 4 | Zero-gap double click loses the order; no idempotency key (§8 G) | F | — | No |
| 5 | "Wait / observe / repeat vitals" not understood (§3.2) | D | C | No |
| 6 | "reassess" without a number = 0 min; "give X and reassess" = 0 min with an "After X" label (§3.2, §11 #6) | D | E | No |
| 7 | Timing inside orders ("in 30 minutes") executed now; plans never executed (§3.3, §14) | D | C | No |
| 8 | No event interrupts a turn; 120-min cap (§5.4) | D | — | No |
| 9 | One unrecognized item holds the whole bundle (§3.3, §16 #4) | C | — | No |
| 10 | Reasonable items not in the lexicon (cefepime, insulin, bicarbonate, LP, vasopressin, "bedside echocardiogram", CPR) (§3.3) | C | B (some also need an effect) | Partly: under C, a recognized generic drug gets an effect through the drug table |
| 11 | Metoprolol refused in bank families (§3.3) | B | C | Partly: under C, a beta-blocker acts on pump/rate channels in any case |
| 12 | AV block at a fixed ischemic minute 45, unavoidable (§9.2) | B (module timer design) | — | No |
| 13 | Fixed logistics (90 min, 100 % success) (§5.3) | B | D | No |
| 14 | Consults/transfer are labels; the patient stays and deteriorates in the ED (§5.3, §11) | B | D, E | No |
| 15 | Narrative-only "arrests" with a pulse (trauma, anaphylaxis, bradycardia) (§11) | E | **A** (no common circulatory/terminal state) | Partly: fixable locally; structurally solved by a common rhythm/pulse state |
| 16 | Opioid arrest shown as "Sinus bradycardia", HR 0 (§11 #1) | E | — | No (an ordering bug in `_surface`) |
| 17 | Legacy PEA with BP 55/30 (§11 #2) | E | — | No (moot if retired) |
| 18 | HyperK lab reports the authored K, not the engine's (§11 #4) | E | — | No (the lab must read state) |
| 19 | History static after treatment (§10) | E | — | No |
| 20 | Cardiac/abdominal/extremity exam static (§10) | E | — | No |
| 21 | Trauma blood loss does not reach CRT, lactate, urine, SpO₂, RR (§6.2) | **A** | B | **Yes** |
| 22 | Asthma BP fixed; opioid HR fixed; hypoglycaemia vitals static; untreated oedema BP/HR frozen (§6.2) | **A** | B | **Yes** |
| 23 | Pressors are an instantaneous BP overlay with no flow/perfusion meaning (§3.2, §4) | **A** | — | **Yes** (needs a pressure/flow/perfusion distinction) |
| 24 | No harm from excess crystalloid in GI/sepsis/pneumonia; Hb 3.0 g/dL alert; `lung` dead in ACS/PE (§8 E; audit's code mapping) | **A** | B | **Yes** (needs shared congestion and O₂-delivery channels) |
| 25 | D50 × 4, epinephrine × 5, albuterol excess without consequence (§8 E) | B (drug-table toxicity) | A | Partly |
| 26 | TXA, octreotide, antiplatelets, heparin in ACS, furosemide outside oedema, midazolam: no effect (§8 H) | B (coverage) | A (midazolam, furosemide need generic channels) | Partly |
| 27 | Duplicates re-execute silently (§8 G) | C | F | No |
| 28 | No resuscitation (CPR, defibrillation) (§16 #13) | B (scope DECISION) | — | No |
| 29 | Trace records turn-level status only; no per-item fate or cause attribution (F4) | C | E | No |
| 30 | `state.hidden` write-only mirror; `terminal_collapse` always False (§2.1) | E | B | No |
| 31 | History/exam time differ by engine (§5.2) | D | — | No (retire legacy) |
| 32 | LLM normalizer could substitute non-numeric content, off in pilot (§12.2) | C | — | No |
| 33 | Generated engine: mechanisms as display offsets; calibration patches; untested on real cases (F2; §14) | **A** | B | **Yes** (Option B would inherit it) |
| 34 | Antidote fade from latest dose only; cumulative untimed furosemide relief; naloxone cancels prior morphine; unbounded PE post-lysis bleed (§4) | B | — | No |
| 35 | Intubation irreversible (no extubation) (§2.2) | B | — | No |

### 6.1 Summary

- **Primarily architectural:** 6 of 35 (#21–#24, #33, plus the root of #15). They are all **coupling** problems: they share one cause, the absence of a common physiological state.
- **Fixable without architecture (B–F):** 29 of 35. They include **every pilot-critical item:** #1–#9, #12, #15–#20, #27, #29.
- **Conclusion:**
  - Rebuilding the physiology would not remove the failures that most threaten the Trace.
  - Phase 0 (§13) addresses those failures on the current engine.
  - The core (option C) addresses the coupling family of problems, which matters for cross-case validity, reassessment fidelity and future generalization.

---

## 7. The minimum common physiologic core (PROPOSAL)

### 7.1 Selection rule

A component is in the core only if all three hold:

1. A **management decision assessed by the curriculum** depends on it (e.g. fluids vs pressor vs inotrope; oxygen vs ventilation; transfusion; treating hypoglycaemia; recognizing deterioration).
2. **Several families** need it. Single-family mechanisms belong to modules.
3. Its absence produced a **verified contradiction or a possible false inference** in the audit.

### 7.2 Core state: nine physiological channels + three chemistry values

Each channel lists:

- **Why:** the management decision that needs it;
- **Shows as:** the observables it influences;
- **Changed by (treatments) / (modules):** the interventions and disease modules that modify it;
- **Memory:** whether it needs memory or kinetics;
- **Prevents:** the contradiction it removes.

**C1 — Intravascular volume (V)** (mL-equivalent deviation from the patient's arrival state)
- **Why:** fluids vs pressor vs transfusion; recognizing ongoing loss; fluid responsiveness vs intolerance.
- **Shows as:** BP and HR (through output and compensation), CRT/skin, urine, lactate (through C8), IVC on POCUS, JVP (with C3).
- **Changed by (treatments):** crystalloid (with leak-back kinetics, already implemented for GI), blood (+volume, +Hb), diuretics (−, delayed), venodilators (functional preload, with C3 preload dependence).
- **Changed by (modules):** haemorrhage (GI, trauma, post-lysis), capillary leak (sepsis, anaphylaxis), third spacing.
- **Memory:** yes (stock with inflow/outflow; existing pools).
- **Prevents:** trauma blood loss that never reaches perfusion; fluids that help in every family regardless of state.

**C2 — Vascular tone (T)** (multiplier, baseline = 1)
- **Why:** distributive vs hypovolaemic shock; what a vasopressor actually does.
- **Shows as:** DBP/MAP, pulse pressure, skin warmth (warm vs cold shock), CRT.
- **Changed by (treatments):** vasopressors (norepinephrine, epinephrine, vasopressin, phenylephrine), with onset/offset; vasodilators (high-dose nitroglycerin); sedatives/anaesthetics (through the drug table).
- **Changed by (modules):** sepsis (vasoplegia), anaphylaxis (mediator vasodilation), toxicology (CCB).
- **Memory:** yes (drug and disease kinetics).
- **Prevents:** pressors as a pure BP overlay; anaphylaxis hypotension with no perfusion meaning.

**C3 — Pump performance (P)** (multiplier) with a **preload-dependence** parameter
- **Why:** cardiogenic and obstructive shock; inotrope vs fluid vs vasodilator; harm of fluids in pump or RV failure; harm of nitrates in preload-dependent states.
- **Shows as:** BP, HR, CRT, congestion (C5), POCUS LV/RV, JVP.
- **Changed by (treatments):** inotropes (dobutamine, epinephrine); negative inotropes (beta-blockers, CCB, by dose); rate effects through C4.
- **Changed by (modules):** coronary ischaemia/reperfusion (LV/RV loss and recovery), PE and tension (obstruction), toxicology, heart failure.
- **Memory:** yes (injury and recovery).
- **Prevents:** in combination with C1, the RV-infarct nitrate and PE fluid effects **emerge** from declared preload dependence instead of family-specific code; pressors that "fix" cardiogenic shock in BP only.

**C4 — Rhythm and pulse state (R)** (small state machine)
- **Content:** label, rate, effective-output factor, `pulse_present`.
- **Why:** rate control, cardioversion, pacing, atropine; recognizing a non-perfusing rhythm; one consistent definition of arrest.
- **Shows as:** HR, monitor strip and ECG, pulse on exam, measurability of BP/SpO₂/CRT.
- **Changed by (treatments):** rate control, cardioversion, atropine, pacing, antiarrhythmics.
- **Changed by (modules):** AV block (ACS, hyperK, toxicology), AF/flutter/SVT, VF/VT (ischaemia), PEA and asystole (hypoxaemia, profound shock), K-related conduction.
- **Memory:** yes (current rhythm, transition times).
- **Prevents:** "Sinus bradycardia" with HR 0; narrative arrests with a pulse; PEA with a BP; three different arrest semantics.

**C5 — Lung water / congestion (L)** (index)
- **Why:** harm of excess fluid; pulmonary oedema; what diuretics, nitrates and NIV are for.
- **Shows as:** SpO₂ (through C6), RR and work of breathing, crackles on exam, B-lines on POCUS, CXR when dynamic.
- **Changed by (treatments):** fluids and blood beyond what the pump tolerates; diuretics (onset); nitrates; NIV/PEEP (redistribution).
- **Changed by (modules):** heart failure, sepsis/ARDS (leak), transfusion overload.
- **Memory:** yes (slow clearance).
- **Prevents:** 6 L or 5 L without harm; `lung` changed but never shown in ACS/PE.

**C6 — Gas exchange (G)** (shunt / V-Q impairment)
- **Why:** oxygen vs PEEP vs treating the cause; recognizing hypoxaemic failure.
- **Shows as:** SpO₂ (with FiO₂), PaO₂, A-a gradient, work of breathing.
- **Changed by (treatments):** FiO₂, NIV/PEEP/intubation (recruitment), and indirectly antibiotics, diuretics and lysis.
- **Changed by (modules):** pneumonia, oedema (from C5), PE (dead space), atelectasis, pneumothorax, bronchospasm (V/Q).
- **Memory:** yes (disease-driven).
- **Prevents:** SpO₂ changes without a physiological reason.

**C7 — Ventilation (W)** (alveolar ventilation relative to need)
- **Content:** drive, mechanics, fatigue capacity.
- **Why:** naloxone vs ventilation vs intubation; hypercapnic failure; respiratory fatigue in asthma.
- **Shows as:** RR, effort, pCO₂/pH, SpO₂ on room air, mental status (CO₂ narcosis), apnoea → arrest (through R).
- **Changed by (treatments):** BVM, NIV, intubation; naloxone (through the opioid module); bronchodilators (through the airway module).
- **Changed by (modules):** opioid and CNS depressants (drive), bronchial or upper-airway obstruction (mechanics), fatigue from sustained high load.
- **Memory:** yes (fatigue accumulates).
- **Prevents:** "RR 0; breaths remain shallow"; untreated asthma at SpO₂ 78 / RR 45 indefinitely with no fatigue endpoint.

**C8 — Oxygen-delivery debt (D)** (accumulated deficit of delivery vs demand)
- **Why:** the **time cost of delay and omission** in every shock state; lactate trend; urine; organ dysfunction; when shock becomes irreversible.
- **Shows as:** lactate (lab), urine rate, CRT/mottling, mental status, and terminal collapse thresholds (through R).
- **Changed by (treatments):** indirectly, by restoring flow (C1–C4), haemoglobin (C10) and saturation (C6).
- **Changed by (modules):** they add metabolic demand (fever, seizure, sepsis).
- **Memory:** yes (accumulator with slow repayment; lactate clearance).
- **Prevents:**
  - Hb 3.0 g/dL alert;
  - trauma CRT fixed at 4 s with BP 50/25;
  - pressor-raised BP with no perfusion consequence;
  - delay penalties that exist in one family and not another.
- This is the legacy core's best idea (`low_flow_burden`), kept in reduced form.

**C9 — CNS depression / neurological state (N)** (drug-effect level + post-ictal timer)
- **Why:** sedation decisions; opioid toxicity; airway protection; interpreting mental status.
- **Shows as:** mental status (combined with C6–C8, C11, CO₂), pupils, airway protection, respiratory drive (C7).
- **Changed by (treatments):** benzodiazepines, propofol, ketamine, etomidate, opioids (drug table); reversal agents.
- **Changed by (modules):** opioid toxidrome, hypoglycaemia (neuroglycopenia, seizure), toxins.
- **Memory:** yes (drug kinetics, post-ictal).
- **Prevents:** midazolam with no effect; sedation that never touches breathing or BP; the neurological exam showing "withdrawal to stimulus" in arrest.

**Chemistry state**

| # | Value | Why | Changed by | Prevents |
|---|---|---|---|---|
| C10 | **Haemoglobin (Hb, g/dL)** | Transfusion decisions; dilution | Bleeding, crystalloid dilution, transfusion; feeds C8 | Hb not affecting delivery |
| C11 | **Glucose (mg/dL)** | Hypoglycaemia rescue, steroid/stress hyperglycaemia, insulin | Dextrose, glucagon, insulin, sulfonylurea/insulin modules, beta-agonists | D50 × 4 with no recorded consequence in labs and monitoring |
| C12 | **Potassium (mmol/L)** | HyperK treatment; shifts from insulin/β-agonists/bicarbonate; diuretic losses | HyperK module (renal), insulin + dextrose, albuterol, bicarbonate, diuretics; read by the ECG/rhythm (C4) and labs | The lab showing an authored 7.6 while the engine is at 8.3; insulin having nothing to act on |

### 7.3 Derived quantities (not stored)

These are computed every minute, deterministically, with bounded gains:

- **Cardiac output index** = f(V, P, R effective-output factor, preload dependence, obstruction).
- **MAP / SBP / DBP** = f(output, T), anchored to arrival values.
- **HR (perfusing rhythm)** = f(R intrinsic rate, sympathetic response, drugs). The **sympathetic response** is itself derived from the MAP deficit, hypoxaemia, hypercapnia, hypoglycaemia, pain/agitation, fever and withdrawal, modulated by β-blockade (a case parameter) and sedation. This removes the "HR fixed in hypoxaemia/hypoglycaemia" findings.
- **SpO₂, PaO₂** = f(G, L, W, FiO₂, PEEP).
- **RR, pCO₂, pH** = f(W, lactate).
- **CRT / skin / mottling** = f(output, T, D).
- **Urine rate** = f(renal perfusion), plus obstruction from the renal module. The existing urine accumulator is kept.
- **Lactate** = f(D) with production and clearance.
- **Mental status** = f(N, D, SpO₂/PaO₂, CO₂, glucose), with recovery lag.

### 7.4 Anchoring to the authored case

The family engine's best property for authoring is kept: observables are **authored arrival values plus mapped deviations of the channels from their arrival state**. This removes the need to fit a model to each case.

A validator checks that each case's arrival values are compatible with its declared parameters. Example: a "severe shock" declaration with a normal arrival BP is flagged for faculty.

### 7.5 Deliberately excluded (PROPOSAL)

| Excluded | Reason |
|---|---|
| Cardiac-cycle mechanics, separate LV/RV pressure-volume models, valves | No assessed decision needs them; very costly to validate |
| Multi-compartment pharmacokinetics, renal/hepatic drug clearance | First-order onset/offset per drug is enough for bedside decisions |
| Stochastic physiology | Breaks deterministic review; deterministic thresholds plus case parameters give variation |
| Electrolytes other than K; acid-base beyond pH/pCO₂/lactate | Add only with a module that needs them |
| Coagulation cascade | The haemorrhage module carries anticoagulant/TXA modifiers |
| Thermoregulation model | Temperature is an observable owned by the infection/antipyretic modules |
| Intracranial pressure, endocrine axes | Out of the bank's scope |
| Ventilator waveform mechanics | Kept only inside the airway/asthma module (plateau, auto-PEEP), where they already exist |
| LLM-generated physiology or narrative of state | Keeps runtime auditable [AUDIT §12] |

### 7.6 Shared drug and intervention table (PROPOSAL)

- One declarative table maps each recognized intervention to its **channel effects**: direction, dose–response with saturation, onset and offset time constants, and toxicity thresholds.
  - Example: norepinephrine → T↑ (τ_on ≈ 1–2 min, τ_off ≈ 2–5 min); at high dose P-independent; excess raises demand.
  - The values are **illustrative**, for faculty calibration.
- Modules may **modulate** a generic effect (e.g. β-blockade blunting epinephrine), but cannot silently cancel it.
- Interventions with no plausible short-term bedside effect (antiplatelets, PPI, statins, antibiotics before their onset) are declared **"no short-term modelled effect"**. The resident sees this; it is not a silent zero.
- This table is what makes **reasonable but unanticipated** actions behave consistently in every case (R2, R3).

---

## 8. Disease-specific layer (PROPOSAL)

### 8.1 Module contract

A disease module:

1. **Owns** its internal state and timers. Examples: ischaemic minutes, obstruction burden, opioid depot, bleeding sources, mediator burden, K kinetics.
2. **Reads** core channels.
3. **Writes only declared channel effects** (rates or deltas on C1–C12, and core parameters such as preload dependence) and **declared events**. It **never writes observables** directly. This is the main change from both the family engine (direct surface formulas) and the coupled engine (display offsets).
4. **Declares its action capabilities.** These are the interventions it responds to, with their mechanism. The action model (§9) uses them to classify an order as "modelled in this case".
5. **Declares observation contributions** through templates: exam phrases, lab analytes it governs, ECG patterns, POCUS findings.
6. **Declares event metadata:** cause class, severity, whether it interrupts, and **preventability** (which actions, before which state or time, can prevent it). The Trace needs this (§12).
7. **Is deterministic** and parameterized by the case. It contains no case-id branches; this is already true [AUDIT §7].

### 8.2 Modules and the channels they act on

| Module (existing file) | Mechanism it owns | Channels written |
|---|---|---|
| Haemorrhage (GI rules in `family_engine`; `trauma_hemorrhage.py`) | Sources, rate (case parameter), control (tourniquet, endoscopy, surgery, IR), anticoagulant/TXA/PPI modifiers | V−, Hb− |
| Coronary ischaemia/reperfusion (`acs_reperfusion.py`) | Occlusion, ischaemic time, LV/RV loss and recovery, arrhythmia risk, reperfusion logistics, troponin | P, R, preload dependence (RV) |
| Pulmonary vascular obstruction (`pe_obstruction.py`) | Clot burden, lysis kinetics, bleeding risk, sustained-hypotension criterion | P (obstruction, preload intolerance), G (dead space), V/Hb (bleeding) |
| Bronchial obstruction (`asthma_ventilation.py`, `asthma_complications.py`) | Resistance, bronchodilator/steroid/Mg/ketamine effect, auto-PEEP, barotrauma/pneumothorax | W (mechanics, fatigue), G, P/V (hyperinflation under PPV) |
| Anaphylactic reaction (`anaphylaxis_reaction.py`) | Mediator burden, IM epinephrine depot, β-blockade, glucagon, biphasic return, stridor | T−, V− (leak), bronchial and upper-airway obstruction |
| Sepsis / infection (in family drift today) | Inflammatory burden, antibiotic time-to-effect, source control, fever | T−, V− (leak), G (lung source), demand, temperature |
| Opioid toxidrome (`opioid_reversal.py`) | Depot, naloxone kinetics, re-sedation, withdrawal | N, W (drive), sympathetic input |
| Glucose disturbance (`glucose_rescue.py`) | Insulin/sulfonylurea kinetics, glycogen, thiamine flag, octreotide | C11, N (neuroglycopenia, seizure) |
| Potassium / brady-toxicology (`bradycardia_toxicology.py`, `bradycardia_support.py`) | K kinetics (renal failure), CCB/BB/digoxin toxicity, antidotes, pacing | C12, R, P, T |
| Heart failure / pulmonary oedema (edema rules in `family_engine`) | Congestion sensitivity, afterload sensitivity | L, P |
| Rhythm disorders (legacy AF logic, to be re-expressed) | AF/flutter/SVT rate, rate control, cardioversion, recurrence | R |
| Renal colic / obstruction | Pain source, ureteric obstruction, infection hand-off to sepsis | urine, pain |
| Thoracic (pneumothorax/haemothorax, in trauma and asthma) | Tension physiology, drainage | P (obstruction), G, V/Hb |

### 8.3 What stays outside the core

These remain in modules:

- Mechanisms specific to one disease: occlusion and reperfusion, clot dissolution, bronchospasm pharmacology, mediator release, opioid depot, glycogen and sulfonylurea kinetics, K shifts by cause, bleeding-source control.
- Disease-specific timers: door-to-balloon, lysis onset, endoscopy gate, biphasic window, seizure after prolonged neuroglycopenia.
- Disease-specific observations: troponin curve, ST changes, wheeze, stridor, melaena, pupils.

The **consequences** of all of these for pressure, flow, oxygenation, ventilation, perfusion and consciousness are produced **only** by the core.

### 8.4 Scripted events: allowed, but declared

Some natural history is legitimately independent of management. Inferior STEMI can produce AV block despite timely reperfusion.

Such events remain allowed, but each must declare:

- its trigger (state-based where possible: e.g. ischaemic burden, rather than a fixed minute);
- its cause class: "natural history";
- its **preventability**: "not preventable in this simulator", or "preventable by reperfusion before X".

The Trace and the analysis then cannot read it as a management consequence. For `acs_54m_inferior`, a DECISION is needed: should the AV block be preventable by early reperfusion?

---

## 9. Action model (PROPOSAL; architecture-neutral)

### 9.1 Pipeline

```
Submission (client nonce) ─► Submission guard: write raw text first; idempotency; Send disabled while running
   ─► Segmentation with coverage map: every span → order | reasoning | commentary | UNACCOUNTED-actionable
   ─► Intent resolution → canonical Order objects (kind, agent, dose, route, rate, timing, condition, target)
   ─► Classification against capabilities (drug table + case modules + logistics)  → one class per order
   ─► Execution ledger: one FATE per order; turn cannot commit unless every order and every
       actionable span has a fate
   ─► Scheduler / execution (atomic commit of the turn)
   ─► Receipt to resident (what ran, what did not, why, what is pending)  +  Trace v2 entry
```

### 9.2 The ten action classes

| # | Class | Example | Engine behaviour | Time | Resident sees | Trace fate |
|---|---|---|---|---|---|---|
| 1 | Recognized + physiologically modelled | "Transfuse 2 units" | Executes through drug table/modules → channels | Administration per order (parallel) | Receipt + response as it develops | `EXECUTED` (with declared channel effects) |
| 2 | Recognized + reasonable + not modelled | TXA in GI bleed today; MTP | Recorded; no physiology | Bedside time only | *"Recorded; effect not modelled in this simulator"* | `RECORDED_NOT_MODELLED` (never an omission) |
| 3 | Recognized + inappropriate/harmful | NTG in RV infarct; fluids in oedema | Executes; harm emerges from channels or is declared by a module. If harm is not modelled: executes and is flagged | As class 1 | Receipt; consequence as it develops | `EXECUTED` + `harm_modelled: yes/no` |
| 4 | Unsupported / unrecognized | "cefepime", "CPR" today | Not executed. **Independent** recognized orders in the same submission proceed (see §9.4) | none for this item | *"Not understood: '…'. Rephrase, record as intent, or cancel."* | `UNRECOGNIZED` (or `RECORDED_AS_INTENT` if the resident chooses) |
| 5 | Ambiguous | "Start norepinephrine" (no rate) | Held until clarified | none | Specific question | `HELD_CLARIFICATION` → final fate later |
| 6 | Duplicate | Same drug and dose within its clinical window; the same submission twice | Same submission ID → ignored. Clinical duplicate → asks to confirm, or executes with a flag (DECISION) | — | *"Pantoprazole 80 mg was given at minute 0. Give again?"* | `DUPLICATE_IGNORED` / `DUPLICATE_CONFIRMED` |
| 7 | Conditional / future | "Repeat the ECG in 30 min"; "if MAP < 65 start NE" | Timed → scheduled. Conditional on observables → **notify** when met, do not auto-execute (DECISION) | At schedule | Standing-orders panel | `SCHEDULED` → `EXECUTED` / `CANCELLED`; `PLAN_NOTIFIED` |
| 8 | Reassessment | "Reassess BP in 15 min" | Observation package at the stated time | Interval (§10) | Observations labelled with the minute | `REASSESSMENT` |
| 9 | Waiting / observation | "Wait 20 minutes" | Advances time with interruption rules | N minutes or until interrupt | *"Wait interrupted at minute t: …"* if relevant | `WAIT` (requested vs actual minutes) |
| 10 | Disposition / consult / logistics | "Call cardiology and activate the cath lab" | Starts a staged logistic process (§10.3) | Process clock | Process status | `LOGISTIC_STARTED` → stage events |

### 9.3 The guarantee: no action is silently converted into an omission

**Invariants, enforced in code and tests:**

1. **Ledger completeness.**
   - Every canonical order created from the input has exactly one terminal fate before the turn commits.
   - Every span the segmenter marks as actionable is either mapped to an order or carries an `UNRECOGNIZED` fate.
   - An incomplete ledger blocks the commit; this is a test failure, not a runtime fallback.
2. **Actionability detector independent of the lexicon.**
   - A broad detector (imperative verbs, dose and unit patterns, drug-like tokens, a superset drug list) flags spans that look like orders.
   - A span it flags that no rule recognizes still produces an `UNRECOGNIZED` fate.
   - This closes the "legacy silently drops pip-tazo" class of failure.
3. **One pipeline for every entry point.**
   - The free-text form, the reasoning-gate follow-up, held-order completion and the guided four-question form all go through the same segmentation and ledger.
   - This closes the gate-follow-up drop.
4. **Write-ahead submission.**
   - The raw text is persisted with a client-generated submission ID before processing.
   - A second identical ID is a no-op; a lost run can be recovered.
   - This closes the double-click loss and prevents duplicate execution.
5. **Display parity.**
   - Every fate is shown to the resident in the turn receipt.
   - The Trace records exactly what was shown.
6. **Analysis guard** (§12).
   - Omission or delay inference is allowed only for orders whose fate is `EXECUTED`, `CANCELLED` by the resident, or **never written**.
   - Fates `UNRECOGNIZED`, `HELD_*` or `RECORDED_NOT_MODELLED` route to an "engine limitation / unresolved" category. They are never routed to "omission".

### 9.4 Bundles: partial execution versus whole-bundle hold (DECISION)

Today one unknown item holds everything, including time-critical fluids (audit §8 H: cefepime held the fluids). That distorts timing.

**Proposal:**
- Execute **independent** recognized orders.
- Hold only **dependency groups**:
  - a procedure with its premedication (e.g. RSI drugs + intubation);
  - "X then Y" / "after X, Y";
  - an order whose parameters depend on the unknown item.
- Tell the resident exactly what ran.

Faculty must confirm this, because it changes what "a turn" means methodologically.

### 9.5 Duplicates

- **Technical duplicates** (same submission ID) are always ignored.
- **Clinical duplicates** (same agent and route within a drug-specific window): the default proposal is to ask for confirmation, for drugs with a maximum or a meaningful cumulative toxicity. Fluids and blood repeated are allowed: repetition is a legitimate titration. This is a DECISION.

---

## 10. Time model (PROPOSAL; architecture-neutral)

### 10.1 Clock and turn semantics

Single integer-minute master clock; minute-by-minute integration (kept).

| Situation | Proposed behaviour |
|---|---|
| Explicit reassessment ("reassess in 15 min") | Advance 15 min (interruptible), then show the observation package labelled "minute t" |
| "Reassess" / "reassess now" with no interval | **Immediate bedside look** (1–2 min of bedside time), labelled "now (minute t)". Never labelled "after X" when X has not had time to act |
| "Give X and reassess" | DECISION. Default proposal: reassess when the shortest administration in the bundle completes (e.g. 1 L at 50 mL/min → 20 min), capped at a declared maximum, and **say so** in the receipt ("reassessing at minute t+20, when the bolus is in") |
| "Wait N minutes", "observe for N" | `WAIT`: advance N (interruptible) |
| Long waits (> 120 min) | Allowed up to a declared maximum, split into interruptible segments; a refusal is shown with its reason |
| Treatment administration | Explicit per order (bolus rate, infusion start/stop/adjust); continues across turns (kept) |
| Diagnostic delays | Result clocks with the collection-time snapshot (kept). Results arriving during a wait are delivered at their minute; **critical values** interrupt (DECISION) |
| History questions and examination | Same bedside time costs in every engine (today: family 2–8 min, legacy 0) |
| Simultaneous interventions | All start at the turn minute; each has its own delivery (kept) |

### 10.2 Events and interruption

- **Event bus.** Modules and the core emit typed events: cause class, severity (`info` / `significant` / `critical`), preventability.
- **Interruption policy (DECISION; default proposal):**
  - `critical` events stop the clock **at the event minute** and return control. Examples: loss of pulse, a new arrhythmia with hypotension, SpO₂ < 85 %, SBP < 70, seizure, airway compromise, recurrence of anaphylaxis.
  - The receipt reads: "Wait interrupted at minute 45: complete AV block, BP 83/54."
  - `significant` events (e.g. result available, a nurse notification threshold) are reported at the end of the interval, or interrupt if faculty prefer a "nurse-call" model.
- **Effect:** a single 120-min wait can no longer report AV block and VF together [AUDIT §5.4].

### 10.3 Logistics as staged processes

- **Shape.** A logistic order (cath lab, endoscopy, CT, ICU bed, transfer, surgery) is a process with stages: request → acceptance → preparation → transport → procedure → completion.
- **Timing.** Durations are case-parameterized and deterministic per seed. Failure or delay states (e.g. cath lab busy) are allowed only when a case declares them.
- **Physiological effect.** It comes **only** from the completion stage acting through a module: reperfusion, haemostasis.
- **Location.** It is state (ED / cath lab / ICU / home). It defines which events still reach the resident, closing the "admitted to ICU but still deteriorating in the ED" inconsistency.
- This extends what already works: cath lab +90, endoscopy gated by resuscitation [AUDIT §5.3].

### 10.4 Scheduled and conditional orders

- **Timed orders** ("in 30 min", "every 15 min ×3") go into a scheduler queue. They are visible and cancellable, and execute at their time with normal receipts.
- **Conditional orders on observables** ("if MAP < 65 start NE") are recorded as plans. When the condition becomes true, the resident is **notified** and confirms (default; DECISION). The Trace credits the anticipation without the simulator acting for the resident.

### 10.5 Terminal states and disposition

- **One terminal model.** A non-perfusing rhythm (C4) is the only "arrest". All families use it: no narrative-only arrests.
- **If resuscitation is not modelled** (scope DECISION):
  - the encounter enters "terminal: arrest at minute t";
  - observation functions return arrest-consistent findings;
  - the Trace marks later decisions as not assessable.
- **Disposition / transfer:**
  - the patient leaves when the logistic process completes;
  - the encounter then closes with a handover summary, or continues only if the case defines a delay (e.g. "ICU bed in 60 min").
  - After "discharge home", reassessment is not offered unless the patient returns.

---

## 11. Observation model (PROPOSAL)

### 11.1 Source-of-truth strategy

**One authoritative state per minute.** That is the core channels plus module states.

**Observables are pure functions of state**, computed by one observation layer:

- vital signs;
- mental status;
- perfusion signs;
- urine;
- labs at collection;
- ECG/rhythm;
- exam text;
- current-symptom answers;
- POCUS.

**Authored case content becomes:**

- **arrival anchors** (§7.4);
- **templates with state-driven slots** for dynamic findings;
- **static facts** for history that does not change: past history, events before arrival.

**Retire parallel representations:**

- the `state.hidden` mirror for family cases;
- authored values for analytes that a modelled mechanism changes;
- module-written observable overrides.

### 11.2 Per observable

| Observable | Derived from | Static allowed? |
|---|---|---|
| BP, HR, SpO₂, RR, temperature | Core derivations (§7.3) + module temperature | No |
| Mental status | N, D, SpO₂/PaO₂, CO₂, glucose, post-ictal | No |
| Perfusion (CRT, skin, mottling) | Output, T, D | No |
| Urine | Renal perfusion + obstruction; visible with a catheter (kept) | No |
| Labs | At collection: Hb, glucose, K, lactate, pH/pCO₂/HCO₃, troponin (module), others authored | Authored analytes allowed **only** if no modelled mechanism changes them in that case, and marked "static" |
| ECG / rhythm | R + module patterns (ST, peaked T, QRS width from K) | No |
| Exam | Region templates: pulse rate/regularity from R; JVP from V/P; crackles from L; wheeze/stridor from modules; CRT/skin from perfusion; neuro from N | Fixed findings allowed if declared |
| Symptoms / history | **Current symptoms** (pain, dyspnoea, nausea) from module symptom states; past history and events authored | Past history yes; current symptoms no |
| Imaging / POCUS | Dynamic where a channel drives it (IVC from V; B-lines from L; LV/RV from P/modules; sliding from pneumothorax); CT/CXR authored unless a module declares dynamics | Marked |

### 11.3 Static-content rule

Every observable is either state-derived or **declared static with a reason**. The Trace records which observables were static at each moment. The analysis then never reads a static, unchanged finding as "the resident ignored a change".

### 11.4 Consistency invariants

These are checked at every minute in tests, and logged as Trace flags in production:

- `pulse_present = False` ⇒ rhythm ∈ {VF, pVT, asystole, PEA}; BP, SpO₂ and CRT "not measurable"; mental status "Unresponsive"; exam "pulse absent"; no "breaths" text.
- HR = 0 ⇒ rhythm = asystole.
- Any rhythm label ⇒ an HR consistent with it.
- The narrative never states hypotension, arrest or recovery contrary to the numeric state.
- A lab value equals the state at collection for every state-governed analyte.
- Exam pulse descriptors match R and HR.

---

## 12. Management Trace safety (PROPOSAL)

### 12.1 What the engine must emit (Trace v2 contract)

Per turn, in addition to today's v1 fields (F4):

| Field | Content | Purpose |
|---|---|---|
| `submission` | Submission ID, wall-clock time, raw text verbatim, entry point (form, gate follow-up, clarification) | What the resident typed, once |
| `segmentation` | Span map: order / reasoning / commentary / unaccounted-actionable | Proves nothing was dropped |
| `orders[]` | Canonical order, class (§9.2), **fate**, reason, receipt text shown, link to its spans | What was understood vs executed vs held vs unsupported |
| `execution[]` | Start/stop minutes, delivered amounts over time, scheduled items | What actually happened |
| `effects[]` | Per channel, per interval: contributions by source (disease module / order ID / logistic process / scripted event / clamp) | Disease progression vs treatment vs script |
| `events[]` | Typed events with cause class, severity, preventability, whether they interrupted | Scripted or natural-history events are not read as management consequences |
| `observation_snapshot` | Exactly what was displayed before the decision: vitals, exam answers given, results delivered with collection times, pending results, observables marked static or unmeasurable | What the resident could actually observe |
| `limitations[]` | Flags such as `order_not_modelled`, `unrecognized_in_turn`, `observable_static`, `terminal_lock_resuscitation_not_modelled`, `scripted_event`, `engine_inconsistency_detected` | Lets the analysis exclude engine artefacts |
| `versions` | Engine, core, modules, drug table, parser, case | Reproducibility (`code_version` exists today) |

### 12.2 Causal attribution

**Channel-level attribution.**
- Because every module and order writes declared deltas to channels, the engine can sum contributions per source for each turn.
- These are **direct contributions**, not counterfactual effects.

**Counterfactual replay (post-pilot).**
- Determinism allows a turn to be replayed without an order, or with it moved earlier or later.
- This gives faculty a defensible answer to "did this delay change the outcome?".
- It costs no new physiology; it reuses the engine.

### 12.3 Safeguards against false inference

| # | Safeguard |
|---|---|
| S1 | **Deterministic pre-analysis.** Before any AI analysis, rules compute the decision points affected by limitations (non-`EXECUTED` fates, unrecognized items, static or unmeasurable observables, scripted events, terminal lock). Those points are marked **"not assessable for this criterion"**. This matches the project rule that missing opportunity or evidence is not insufficient performance. |
| S2 | **Omission inference only from complete ledgers.** "Did not give X" requires that X was never written, or was cancelled by the resident. |
| S3 | **Event attribution.** An event whose cause is "natural history, not preventable" can never support a management criticism. One marked "preventable by A before t" may support one only if A was available, recognizable and modelled in that case. |
| S4 | **Observation-opportunity gating.** "Failed to reassess / recognize Y" requires that Y was observable (not static, not unmeasurable), and was displayed or available on request at that time. |
| S5 | **AI analysis inputs and instructions.** The post-encounter analysis receives fates, provenance and limitation flags. It is instructed and tested so that it never contradicts them. Test: synthetic traces with injected limitations, where any inference of failure counts as a test failure. |
| S6 | **Faculty view** highlights limitation flags next to each decision. Faculty confirms; the AI proposes (existing project principle). |
| S7 | **Trace validator.** A complete ledger, every event with a cause, and an observation snapshot are required before an encounter is admitted to analysis. |

---

## 13. Migration strategy

### 13.1 Estimates per option

Estimates are relative. No calendar is given.

| Option | Implementation effort | Regression risk | Validation burden | Time to pilot readiness (if the option had to be finished first) |
|---|---|---|---|---|
| A — strengthen family engine | MODERATE (grows with every family patched) | LOW–MODERATE | MODERATE (12 couplings to review) | MODERATE (Phase 0 + per-family patches for pilot cases) |
| B — migrate to legacy/coupled core | VERY HIGH (31 reviewed cases re-expressed; overlay mechanisms rebuilt as state effects; missing channels added to a 57-variable model) | HIGH | VERY HIGH | VERY HIGH |
| C — hybrid core + modules | HIGH (core + drug table + module re-wiring; runtime and modules reused) | MODERATE (shadow mode, golden traces) | HIGH (new core, but small and invariant-checked) | HIGH if required before the pilot; **unchanged from A with the recommended sequencing** (pilot on Phase 0) |

**Basis:** module sizes and test assets in §2.1. The 31 bank cases and their faculty-reviewed behaviour are the main asset any migration must preserve or explicitly re-approve.

### 13.2 Recommended staged migration (for C)

The sequence differs from the brief's template in two ways:

1. The **pilot is placed after Phase 0**, on a frozen engine.
2. The **architecture-neutral contracts come before the core.** They remove most false-inference risk, they are needed whatever the physiology, and they make the core swap testable.

**Phase 0 — Measurement-invalidating defects (pre-pilot, on the current family engine)**

- 0.1 **Execution ledger and fates**:
  - per-order fates shown to the resident and recorded;
  - actionability detector;
  - the gate follow-up and every entry point through the same pipeline.
- 0.2 **Routing:** remove PS001 from resident assignment, matching the pilot documents. A DECISION is needed if faculty want R1-03/R1-04/R2-01 in the pilot.
- 0.3 **Submission guard:** write-ahead raw text, idempotency ID, Send disabled while running.
- 0.4 **Minimal time semantics:**
  - `WAIT`;
  - explicit handling of "reassess" without an interval (no "After X" on pre-treatment vitals);
  - critical-event interruption;
  - "in N minutes" either scheduled or explicitly refused, never executed now.
- 0.5 **Observation contradictions in pilot cases:**
  - one pulse/rhythm/arrest invariant set;
  - the opioid rhythm label;
  - labs read state for state-governed analytes (K);
  - no narrative-only arrests;
  - static exam/history regions either made state-driven or declared static and flagged;
  - local coupling patches only where a pilot case's assessed decision depends on them (e.g. trauma perfusion signs). Otherwise the case is excluded.
- 0.6 **Trace provenance minimum:**
  - fates, event cause classes, scripted-event flags (AV block), limitation flags, observation snapshot;
  - pre-analysis guards S1–S4.
- 0.7 **Pilot case acceptance:** run the §14 battery on each candidate case; exclude failures.
- 0.8 **Freeze** the engine, case list and Trace schema for the pilot.

**Pilot (frozen engine)**
- Collect real resident phrasing, the distribution of actions, the use of waiting and reassessment, and every limitation flag raised.
- These become calibration and test material.

**Phase 1 — Contracts v2 (architecture foundation, physiology unchanged)**
- Full action classes 1–10, scheduler, logistics stages, terminal model.
- Observation layer with templates and invariants; Trace v2 with channel-level provenance hooks.

**Phase 2 — Common core in shadow mode**
- Implement C1–C12, the drug table and the module interface.
- Run the core **in parallel** with the family engine on golden traces (audit trajectories + pilot encounters).
- Compare observables and calibrate; no resident exposure.
- **Exit:** invariants clean; golden trajectories within agreed tolerance, or each difference approved by faculty.

**Phase 3 — Migrate representative families (one per channel cluster)**

| Family | Channel cluster |
|---|---|
| GI bleed | V, Hb, D |
| Inferior ACS | P, R, preload dependence, logistics |
| Asthma | W, G |
| Opioid | N, W |
| Sepsis/pneumonia | T, V, G, L |

Faculty review each against its golden behaviour.

**Phase 4 — Remaining families**
- The PS001 AF scenario is re-expressed as a rhythm module on the core, which restores R1-03/R1-04/R2-01 without the legacy engine.
- Retire legacy code paths: the legacy parser and executor in `app.py`, the legacy hidden mirror, per-family `_surface` formulas.

**Phase 5 — Generated cases**
- **Bounded authoring:** the LLM selects modules and parameters within validated ranges and writes narrative templates. It never writes response rules or physiology.
- Each authored case must pass the §14 battery automatically before use.
- The coupled engine's display-offset adapter is retired.

**Validation is continuous**, not a final phase: every phase exits through §14.

### 13.3 What each phase preserves

- **Phases 0–1:** the current physiology exactly; changes are in input, time, observation and Trace.
- **Phase 2:** no resident-visible change.
- **Phases 3–4:** modules' internal logic and timers are kept. Only the way they reach observables changes, and each changed trajectory is either within tolerance or re-approved.

---

## 14. Testing strategy

### 14.1 Test classes

| # | Test class | What it checks |
|---|---|---|
| T1 | Deterministic replay | Same inputs and seed → identical state, observables, events and Trace; also across reload/restore |
| T2 | Time-step invariance | One N-minute wait ≡ k shorter waits (no interrupts); interrupts stop at the same minute regardless of requested interval |
| T3 | Order-permutation invariance | The same simultaneous orders in a different textual order → identical result |
| T4 | Causal battery per case (A–K) | Correct, delayed, omission, incorrect, excessive, contradictory, duplicate, unexpected-reasonable, waiting, reassessment, combined, terminal deterioration, recovery. Each with **directional assertions** on outcome metrics (MAP, D, SpO₂, mental status, lactate), e.g. delayed ≤ timely; omission worse than correct; declared harm appears beyond its threshold. For reassessment: the observations returned at the stated minute must equal the observation functions applied to the state at that minute, and a treatment's response must not appear before its declared onset |
| T5 | Counterfactual consistency | Removing a beneficial executed order in replay does not improve the declared outcome; adding a harmful one does not improve it |
| T6 | Parser / execution fidelity | Phrase corpus (EN/ES, including pilot phrasing) → expected canonical orders and fates; coverage invariant; entry-point parity (form, gate follow-up, clarification) |
| T7 | Observation consistency | Property-based random action/wait sequences; all §11.4 invariants every minute |
| T8 | Persistence / UI | Browser tests: double click, rapid repeat, reload during a run, resume. No lost or duplicated submissions |
| T9 | Trace completeness and provenance | Every order has a fate; every event a cause; snapshots present; limitation flags raised when injected |
| T10 | Analysis guards | Synthetic traces with injected limitations → analysis must not infer omission, delay or misrecognition at those points |
| T11 | Golden-trajectory regression | Against frozen trajectories (current engine, pilot) with tolerance bands; differences need explicit faculty approval |
| T12 | Fuzz / robustness | Random valid orders: no exceptions, bounded values, no NaN, invariants hold |
| T13 | Clinical plausibility review | Faculty sign-off per module and per case on scenario sheets (trajectories A–K) |

### 14.2 What counts as a FAILURE

- Any order or actionable span without a fate, or any fate not shown to the resident.
- Any lost submission, or more than one execution of one submission.
- Any non-determinism (T1, T2 or T3 differences).
- Any §11.4 invariant violated, or any static observable not declared static.
- Any event without a cause class or preventability metadata.
- Any directional assertion violated in T4 or T5. Examples:
  - omitting a declared-required intervention does not worsen the outcome metric;
  - a declared-harmful excess produces no harm;
  - a treatment declared "modelled" has no channel effect.
- Any golden-trajectory difference beyond tolerance without approval.
- Any analysis output that infers a resident failure at a point flagged as an engine limitation (T10).
- Any case admitted to the pilot without passing T4 and T7.

---

## 15. Final decision

### 15.1 Recommended architecture

**C — hybrid: a small common physiologic core plus disease-specific modules**, built by evolving the family engine. It is preceded by an architecture-neutral Phase 0 on which the resident pilot runs.

### 15.2 Why it best serves management reasoning

1. **The same decision has the same physiological meaning in every case.** Fluids, pressors, inotropes, oxygen, sedatives and diuretics act on shared channels. Cross-case reading of the Trace, and comparison across residents, becomes valid.
2. **It removes the architectural root of the coupling contradictions** with about ten channels: no physiology simulator, and small enough for faculty validation (P1, §7.5).
3. **It keeps what already works:** the deterministic minute loop, pools, result clocks, atomic commit, reviewed modules, persistence and LLM-free runtime. Migration is incremental and testable in shadow mode.
4. **Attribution comes almost free.** Channel deltas by source give the Trace the provenance it needs to tell disease, treatment, script and engine limitation apart. Determinism enables counterfactual replay.
5. **It gives AI-authored cases a safe future:** bounded composition of validated modules instead of authored physiology or display offsets.

### 15.3 Preserve

- Minute integration and determinism.
- Delivery pools and drug kinetics.
- Result clocks with collection snapshots.
- Atomic turn commit.
- All disease modules (internal logic and timers).
- Logistics separated from physiology (extended to staged processes).
- Explicit disclosure of unmodelled items and studies.
- The reasoning gate concept.
- Trace v1 fields (extended).
- Revision-checked persistence.
- The separation between runtime physiology and post-encounter AI.
- Evaluation metadata that never steers physiology.
- The 31-case bank content and its authored arrival anchors.

### 15.4 Retire

- **The legacy PS001 resident path:** inline parser and executor in `app.py`. Its scenario is re-expressed as a rhythm module if faculty keep R1-03/R1-04/R2-01.
- **From the coupled engine:** the display-offset pattern and the calibration patches.
- **From the family engine:** per-family `_surface` formulas that bypass shared physiology.
- **Parallel representations:** `state.hidden` mirror; authored values for state-governed analytes; module-written observables.
- **Narrative-only arrests.**
- **Whole-bundle holds for independent orders** (subject to DECISION).

### 15.5 Do NOT build

- A high-fidelity cardiovascular or respiratory model; pressure-volume loops; multi-compartment pharmacokinetics.
- Stochastic physiology.
- LLM-generated physiology, LLM-decided treatment effects or LLM narration of state at run time.
- A generic "any drug" engine without declared channel effects.
- Per-case custom code.
- A full ACLS simulator, unless the curriculum decides resuscitation is in scope.
- An expanded legacy core.

### 15.6 Principal risks

1. **Recalibration drift:** faculty-approved trajectories change when moved onto the core. *Mitigation:* golden traces, tolerances, explicit re-approval.
2. **Scope creep** into physiology simulation. *Mitigation:* P1 selection rule; exclusion list.
3. **Emergent interactions surprise reviewers.** *Mitigation:* bounded gains, invariants, property-based tests, counterfactual checks.
4. **Parser coverage stays the binding constraint**, whatever the physiology. *Mitigation:* pilot phrase corpus; actionability detector; explicit `UNRECOGNIZED` fates.
5. **Cost of running two engines in shadow mode.**
6. **Methodological decisions unmade** (Appendix A) block parts of Phases 0–1.

### 15.7 Preconditions before implementation

- Faculty decisions in Appendix A, at least: bundle semantics, "reassess" default, conditional orders, interruption policy, resuscitation scope, R1-03/R1-04/R2-01 in the pilot, duplicate policy, preventability of the inferior-STEMI AV block.
- Trace v2 schema agreed (§12.1), including how "not assessable" is represented.
- A frozen golden-trajectory corpus (audit trajectories + accepted case behaviours).
- The §14 battery specified as executable acceptance criteria.
- A versioning rule: an encounter keeps the engine version it started with (the project already freezes code version and evaluation basis per encounter).

### 15.8 Must be fixed before the resident pilot (Phase 0, in priority order)

1. **No silent non-execution:** execution ledger with per-order fates shown and recorded; actionability detector; the gate follow-up and every entry point through the same pipeline.
2. **Remove the legacy PS001 engine from resident routing** (or a faculty DECISION to keep it, with the same ledger applied).
3. **Submission guard:** idempotency ID, write-ahead raw text, Send disabled while running.
4. **Minimal time semantics:** `WAIT`; explicit "reassess" without an interval; no "After X" on pre-treatment vitals; critical-event interruption; timed orders scheduled or explicitly refused.
5. **Trace provenance and analysis guards:** fates, event cause classes, scripted-event and limitation flags, observation snapshot, S1–S4.
6. **Observation contradictions in pilot cases:** arrest/rhythm invariants; state-read labs; no narrative-only arrests; static content declared.
7. **Case acceptance battery and engine freeze** for the pilot.

### 15.9 Can safely wait until after the pilot

- The common core (Phases 2–4) and the shared drug table.
- Re-expressing PS001 on the core; the generated-case pipeline.
- Staged logistics beyond declared fixed delays.
- Resuscitation actions.
- Dynamic CT/CXR.
- Counterfactual-replay tooling.
- Broader drug and procedure coverage, **provided** every uncovered item has an explicit fate.
- Conditional-order notification (only if Phase 0 records conditional orders as explicit plans).

### 15.10 Proposed architecture

```
Resident input (free text, gate follow-up, clarification, guided form)
      │
      ▼
Submission guard ── write-ahead raw text · idempotency ID · Send disabled while running
      │
      ▼
Intent / parser layer ── segmentation with coverage map · canonical orders · actionability detector
      │
      ▼
Execution contract (ledger) ── class 1–10 per order · exactly one FATE each · receipt to resident
      │
      ▼
Time / event engine ── minute clock · WAIT · reassessment · scheduler · logistic processes ·
      │                event bus with severity, cause, preventability · critical-event interruption
      ▼
┌───────────────── per-minute integration ─────────────────┐
│  Disease modules (own state + timers; declared effects)   │
│        ⇅ declared channel effects only                    │
│  Common core: V · T · P · R · L · G · W · D · N | Hb · Glu · K │
│        ⇅ shared drug/intervention table (channel effects) │
└───────────────────────────────────────────────────────────┘
      │
      ▼
Observation layer (single source of truth) ── vitals · mental status · perfusion · urine ·
      │      labs at collection · ECG · exam templates · current symptoms · POCUS ·
      │      invariants · static-content declarations
      ▼
Resident display (receipts, observations labelled with their minute, pending items)
      │
      ▼
Management Trace v2 ── typed text · orders + fates · execution · channel provenance ·
      │                events (cause, preventability) · observation snapshot · limitations · versions
      ▼
Deterministic pre-analysis guards (S1–S4: not-assessable marking)
      │
      ▼
Post-encounter AI analysis (proposes) ──► Faculty review (confirms)
```

---

## Appendix A — Decisions required from faculty or methodology (DECISION)

| # | Decision | Default proposed here | Affects |
|---|---|---|---|
| A1 | Partial execution of independent orders vs whole-bundle hold when one item is unrecognized | Partial, with dependency groups held | §9.4; Phase 0 |
| A2 | Meaning of "reassess" without an interval, and of "give X and reassess" | Immediate look; "and reassess" = when the shortest administration completes, stated in the receipt | §10.1; Phase 0 |
| A3 | Conditional orders on observables: auto-execute or notify | Notify and confirm | §10.4 |
| A4 | Which events interrupt a wait (critical list; nurse-call model?) | Critical list in §10.2 | §10.2; Phase 0 |
| A5 | Resuscitation in scope (CPR, defibrillation, ACLS drugs)? | Out of scope for the pilot; terminal state explicit | §10.5 |
| A6 | R1-03/R1-04/R2-01 in the pilot (legacy engine) | Excluded until re-expressed on the core | Phase 0 |
| A7 | Clinical duplicate policy (confirm vs flag) per drug class | Confirm for drugs with a maximum or toxicity; allow fluid/blood repeats | §9.5 |
| A8 | Preventability of the inferior-STEMI AV block, and of other scripted events | Declare each event's preventability explicitly | §8.4 |
| A9 | Tolerance bands for golden-trajectory equivalence during migration | Per channel; differences re-approved | §13.2 |
| A10 | How "not assessable" decision points are shown to residents and faculty | Visible to faculty; neutral wording to residents | §12.3 |

## Appendix B — UNKNOWN

- **Deployed configuration** (offline flag, routing, secrets) [AUDIT §0.3].
- **Whether coupled-engine mechanism offsets propagate to tissue perfusion and lactate** (F2). Code comments suggest not fully; not executed.
- **Calibration effort and drift** when the 31 faculty-reviewed trajectories move onto the core. Measurable only in Phase 2 shadow mode. This is the main uncertainty for the timeline; it does not change the choice of option.
- **Real distribution of resident phrasing and actions.** It determines the action-model coverage needed; the pilot will reveal it.
- **Run-time behaviour of the 14 bank variants** the audit did not stress-test.
- **Frequency of the zero-gap double-click loss** with real users and browsers.
- **Faculty preferences** on Appendix A.

## Appendix C — Evidence index

| Claim | Source |
|---|---|
| Three engines; routing of R1-03/R1-04/R2-01 to PS001 | AUDIT §1.1 |
| Silent non-execution paths | AUDIT §3.3, §8 G, §16 #1, §17.7 |
| Time semantics | AUDIT §3.2, §5 |
| Coupling matrix | AUDIT §6.2 |
| Contradictions | AUDIT §11 |
| Scripted AV block | AUDIT §9.2 |
| LLM role at run time = none | AUDIT §3.4, §12 |
| Legacy core variables (57 hidden, 14 phenotype) | CODE `clinical_core_defaults.py` |
| Coupled engine mechanisms as display offsets | CODE `coupled_encounter.py:159–221`; `clinical_physiology.py:569, 1008–1011, 1034, 1045, 1253` |
| Adapter calibration patches | CODE `coupled_encounter.py:378–395` |
| Bank modules reused by the generated engine | CODE `generated_airway.py`, `generated_pe.py`, `generated_glucose.py`, `generated_opioid.py` (module docstrings and imports) |
| Trace v1 schema | CODE `app.py:875–916` |
| Module sizes and test assets | CODE (`wc -l`, file counts), §2.1 |
