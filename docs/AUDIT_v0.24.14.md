# Offline audit and repair — v0.24.14 (not deployed, no paid calls)

Every finding below was reproduced locally from saved reports, the existing test
suite, or the real Streamlit submit path with a stubbed author client. No API
request was issued and no image was generated.

## 1. The published branch could not run its own tests

`generation_reload.refresh_generation_modules` decided staleness by comparing
`EXECUTION_VERSION` on every name in `_EXECUTION_MODULES`. That tuple listed
`account_store` and `account_portal`, which do not declare the marker, so
`getattr(..., None) != "0.24.2"` was permanently true once the refresh itself
imported them. `_VISUAL_RELEASES` expected `SCENE_PIPELINE_VERSION == 10` while
the module had moved to 12.

Measured on a settled process: **46 modules reloaded on every Streamlit rerun**
(28 generation + 18 visual), forever. That discards module-level state and every
test double, which is why 63 tests across 13 files failed on a clean checkout —
including the whole AppTest layer, so no encounter could be exercised offline.
`test_generation_reload` already caught it (`refresh_generation_modules(...) is
False`) and was failing on the published branch.

Fix: `_EXECUTION_MODULES` lists only modules that declare the marker;
`_VISUAL_RELEASES` matches the sources. Two new tests read the markers with
`ast` and assert a settled process stops reloading.

Effect: 63 failing tests → 9, from one change. The remaining nine were repaired
individually (below); the suite now passes in full.

## 2. The author contract offered a field no case could legally use

Report `75e52322047c4e6cb6209d8414f3f15a` (v0.24.13, challenge R1-05): a
`dextrose` response rule with `washout_min: 30`. **116.8 s author + 117.7 s
correction = 236.1 s and 31,970 tokens, no encounter.**

`washout_min` is legal only for `norepinephrine`, `dobutamine`, `nitroglycerin`.
`case_authoring.NATIVE_ONLY` removes all three from the author's `action_type`
enum, but left `washout_min` in the schema as a required nullable property.
Structured outputs force the author to emit it and only `null` could ever
compile. `interpolate_settings` was in the same position: legal only for
`ventilator_adjustment`, which is also excluded. This is the discrepancy class
v0.24.7 fixed for `volume_basis`/`diuresis_ml_min` and missed here.

Fix: `UNUSABLE_RULE_FIELDS` is derived from the executor's own legality sets
against the surviving enum, removed from `AUTHOR_SCHEMA` and restored as `null`
during expansion. A regression test asserts that a kind-restricted field is
offered if and only if some allowed action can carry it, so a later enum change
cannot reintroduce a dead option.

## 3. Fatal rejections reached the paid repair with no actionable cause

The failure above arrived as `CONTRACT_UNCLASSIFIED`, `path: "case"`,
`details: {}`, message "Infusion washout must be between 1 and 180 minutes." —
30 is inside that range. The repair corrected a valid number and failed
identically.

`collect_declarative_issues` mirrors most of `validate_declarative_case`, but
four rule checks existed only in the gate, so any draft violating them fell
through to the unclassified fallback: washout by action type, setting
interpolation, the sedation contract, and non-increasing state-coupling points.
Confirmed by mutating a valid draft and reading the codes.

Fix: `RESPONSE_KINETICS`, `RESPONSE_SEDATION` and `RESPONSE_STATE_GAIN`
collectors carry the rule path, the offending action type and the values. The
gate's own messages now name the action type instead of only a range. Eight
regression tests pin this; none weakens a gate.

## 4. One unreadable fragment discarded the whole submission

Reproduced through the resident's own submit path with the reported order:

    patient in shock. Give 1000 NS, start oxygen 4l/m nasal cannula.
    POCUS, VBG, lactate need to improve oxygenation and perfusion.
    Reassess in 10 min, hr,bp, O2

With every item supported, the current code is correct: 1000 mL NS, nasal
cannula at 4 L/min, three separate investigations, VBG parsed as venous and not
arterial, one 10-minute advance, results released, reasoning split into problem,
priority, expected effect and reassessment target.

With one unreadable item, `hold_incomplete_bundle` returned `None` whenever any
action was a `clarification`, so all six orders were dropped. Replying
"ok basic labs" was then a fresh unrecognized turn. Nothing executed and the
clock did not move — better than the reported incident, where only the study ran
— but the resident lost the submission and was told only "This order was not
recognized."

Fix: an unreadable fragment is held like any other incomplete slot. The message
quotes the fragment and says the rest is held. Replacing or skipping the item
executes the complete original intent; a bare "cancel" still drops the pending
orders, which is the documented meaning. Four regression tests cover the turn,
the replacement, the skip and the bare cancel.

## 5. Ordered volume was reported as if it had been infused

A bolus runs on the simulation clock at 50 mL/min. At the 10-minute
reassessment the update said "normal saline 1000 mL started" while the state
correctly held 500 mL delivered and 500 mL pending. The update now reads
"500 mL of 1000 mL infused by 10 min; remainder due at 20 min".

`test_generated_case` asserted the pre-v0.24.12 immediate effect and was
rewritten to assert ordered-versus-delivered explicitly.

## 6. A composed priority was presented as the resident's own

When the resident states a problem and an expected effect, the interpreter
composes `management_priority` in the application's words. In the reported
order, "need to improve oxygenation and perfusion" became the priority "improve
tissue perfusion" — narrower, and indistinguishable in the trace from a priority
the resident wrote.

Fix: composed slots are recorded in `reasoning["derived_slots"]`, labelled in
the on-screen trace, and named to the faculty analysis as
`app_composed_reasoning_slots`, which its instructions must not quote or call a
stated priority. The verbatim `learner_input` was already preserved.

## 7. Engine equivalence with main and ai-integration-v0.9.0

Measured, not assumed. Both reference branches were read in detached worktrees
and never modified.

- The PS001 legacy surface is **bit-identical across all three branches**: the
  same parse, `sim_time` and vitals after one 1000 mL bolus plus oxygen, and
  after three sequential 500 mL boluses.
- clinical-encounter's `app.py` keeps all 181 of main's top-level functions and
  adds 19. Thirty-nine of them are now thin shims that delegate to
  `clinical_physiology.invoke`; the implementations there are byte-identical to
  main for 29 of the 47 shared functions.
- The 18 that differ are bounded extensions, not drift: `fluid_transition` gains
  cumulative-dose saturation keyed on `_fluid_delivery`, absent on the legacy
  surface, which is why PS001 still matches main exactly;
  `recompute_coupled_physiology` adds `physiology_inputs` offsets,
  `rhythm_coupling_v2`, sedation-label recovery and mottling preservation at
  collapse; `oxygen_support_fraction` gives bag-mask 0.85 support where main had
  0; `rng` and `sim_time_label` are injected dependencies.

Generated encounters run `coupled_encounter.execute`, not
`execute_generated_bundle`. The two differ in one way that matters: the coupled
path sets `elapsed = reassess if reassess is not None else 0`, so an ordered
study never advances the clock by itself. That is the documented v0.24.12
behaviour and it is visible — the study shows as pending with its expected time
and is released by an explicit reassessment — but it is not equivalent to the
legacy path, which advanced to the result. `test_problem_launch` asserted the
old behaviour and was rewritten to assert the current contract.

## 8. Image screening

`IMAGE-SCREEN-INVALID_RESPONSE` and `IMAGE-SCREEN-RESULT_EVIDENCE` are reviewer
failures; only `IMAGE-SCREEN-MISMATCH` is a visual contradiction. The code
already keeps them apart: `_screen_with_correction` re-requests an image only
for `reason_code == 'mismatch'` with concrete failed checks, and an explicit
retry of a technical failure dispatches `screened_existing_scene`, which
re-reviews the saved bytes without generating anything. Evolved images keep the
approved original as the identity reference. No change was needed. One narrow
mislabel remains: `_screen` codes a non-raising `accepted is not True` as
`invalid_response`; `inspect_image` does not currently return that.

## 9. Time and cost

- Worst case per encounter attempt: five text requests — author (24k), structural
  correction (24k), review (6k), clinical correction (24k), review (6k) — under a
  300 s budget with a 30 s review reserve, plus image create, screen, and one
  repair with a second screen. `test_problem_launch` now pins the four-request
  budget of a rejected review so raising it is a deliberate act.
- Every client uses `max_retries=0` except `ai_interpreter` (`max_retries=1`),
  so a transient failure can double that per-turn normalization call.
- Per-stage seconds and token usage are recorded in `provenance.requests` on
  success and in the failure diagnostic on failure. Image calls are not in that
  ledger.
- Removing the two dead fields trims the author schema by 193 bytes and two
  required properties per response rule. The real saving is not spending a
  correction on a draft that cannot compile.

## 10. One authorized paid run, and what it proved

Challenge R1-05, seed 933662594, no image, `gpt-5-mini`. It **failed**:

| stage | status | seconds | tokens |
|---|---|---|---|
| author | completed | 62.99 | 13,845 |
| correction | completed | 48.10 | 16,546 |
| review | completed | 70.04 | 12,197 |
| correction | completed | 53.68 | 17,423 |
| review | **timed out** | 63.63 | — |
| | | **300.15** | **60,011** |

`CASE-REVIEW-TIMEOUT`. The budget was the cause, and the arithmetic is exact:
the four first calls spent 235 s, the mandatory final review began with 63.5 s
left, `reserve = 30 if stage != "REVIEW" else 0` gave it `min(120, 63.5)`, and a
review had just taken 70.0 s. **The 300 s budget could not accommodate the
pipeline's own longest path**, so entering the long branch guaranteed paying for
four calls and then timing out on the fifth.

Two further facts from the run: the author's first draft did **not** compile, so
the washout fix in section 2 did not prevent this failure and this run neither
confirms nor refutes that fix; and the reviewer rejected the corrected case,
which is the reviewer working, not a defect.

### Budget derived from the path

`REQUEST_BUDGET_SECONDS` is now `STAGE_BUDGET_SECONDS * len(WORST_CASE_STAGES)`
= 90 x 5 = 450 s, and a stage reserves a whole stage for the review that must
follow it, refusing before paying when the call itself cannot finish. The old
check let a request start with 10 s left and buy a timeout. Replaying the
measured durations, the run would have completed at ~305 s. The trade is a
worst-case wait of 450 s instead of 300 s; the alternative is to shorten the
path, for example to a single review round, which is a product decision.
`test_generation_budget_and_diagnostics` reads `generate_ai_encounter` with
`ast` and fails if its request sites stop matching `WORST_CASE_STAGES`, and
`test_generation_budget` now derives its exhaustion point from the constants
rather than the literal 295 that quietly stopped refusing.

### The diagnostic now survives

The run's diagnostic was lost: it was written to a session-scoped temporary
directory that was removed. That was avoidable, and it also exposed a real gap —
in shared-password mode `generate_problem_config` caught `GeneratedCaseError`
and only called `st.error`, discarding the draft, the validator issues, the
reviewer objections and the request ledger of every paid failure. Only the
account path persisted them, and only to an administrator table.

`generation_diagnostics.save_failure` now writes the diagnostic to
`local-data/generation_failures/` from both launch paths, keeping the last 50.
It sanitizes the reference, drops an oversized draft rather than the report, and
never raises, so a failed write cannot replace the error the caller is
reporting. Learner-facing output is unchanged.

## Validation and limits

All 82 pytest files pass, run one file per process. On the published HEAD, 13
files failed (63 tests). Fourteen regression tests were added across three new
or extended files.

`run_regressions.py` goes from 50/56 to 51/56. The five that still fail already
failed on the published HEAD and none is a behavioural defect: `v06024` and
`v0821_dynamic_ecg_strip` assert UI source text that has since changed;
`v06034` and `v081` build AST session stubs that no longer match the functions
they load; `v0821_lower_initial_ps001_bp` pins a `SIMULATOR_VERSION` allowlist
that stops at 0.11.2. `v06018_stop_label` was in the same state and was rewritten
to assert the rendered label instead of app.py's indentation. Re-pinning the
other five strings would only re-arm the same rot; converting them to behavioural
checks is separate work.

No paid call, no image, no latency benchmark, no deployment.

Passing offline tests is not evidence of clinical quality or of live API
behaviour. The author client is a local stub, so nothing here shows that a real
model now produces an acceptable case, and the independent clinical reviewer has
not run. The unresolved clinical objections carried forward from v0.24.8 — the
very rapid untreated decline of the supplied severe draft, troponin units,
ischemic findings — are untouched. The 50 mL/min default bolus rate is a
modelling choice that has not been reviewed clinically.

The saved `case_preparation_*.json` reports disappeared from ~/Downloads during
this session. Their evidence was extracted first and the failures are encoded as
regression fixtures, but the original drafts can no longer be replayed.
