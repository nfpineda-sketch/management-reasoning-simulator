# v0.17.2 · Complete correction feedback and visible preparation progress

Scope: `clinical-encounter-v0.13` only. No account reset, database migration,
Secrets change or change to `main` or `ai-integration-v0.9.0` is needed.

## What the reported error establishes

The resident's `CASE-CORRECTION-CONTRACT` error establishes that authoring and
the single correction returned structurally usable responses, but the corrected
case still failed local clinical/executable validation. It does not identify
which rule failed: v0.17.1 discarded the final compiler exception. That original
draft is not recoverable from the error screenshot.

The visible v0.17.0 caption was separately hardcoded; it did not establish that
the generator was still v0.17.0.

## Changes

- A schema-valid draft now receives a structured list of independent clinical
  and engine inconsistencies. One correction request sees them together instead
  of seeing only the first error. Ambiguous duplicate fields are all reported
  before normalization; clinical interpretation waits until those are resolved.
- Trajectory feedback identifies the rule, field, baseline, drift, exposure,
  time and bounds, including failures at interior response breakpoints. When
  calculable it provides the admissible authored change at that specific time.
  These are software constraints, not treatment recommendations. The correction
  must preserve a clinically coherent case and still pass every breakpoint.
- Diagnostic feedback covers conflicting baseline measurements, incompatible
  bindings, blood-gas inconsistency, history/appearance contradictions and missing
  neurological findings after a change in mental status. Schema-allowed text in
  numerical blood-gas fields now produces a correctable contract issue instead
  of an unexpected arithmetic exception.
- Preparation displays creation, checking, refinement when needed, and review.
  Elapsed time is recorded at stage transitions, not as a continuously ticking
  timer. Failure never displays a successfully prepared encounter. Successful
  provenance records author, correction, review and total durations.
- Captions and tab title derive from one release constant. A version-guarded
  dependency reload prevents a cached older generator from being called with the
  new progress interface during a Streamlit hot update.
- A remaining contract failure provides fixed check identifiers in the error
  and server log. Rejected patient content, numbers, rule names, provider bodies
  and credentials are not rendered or logged. Detailed issues go only to the
  case correction request, with `store=False` as before.

There is still at most one repair and a separate consistency review before
launch. An unsuccessful attempt starts no encounter and substitutes no bank
case. No physiology is clamped and no treatment capability or acceptance gate
is loosened. A clinical review rejection still stops launch.

## Verification and limits

184 targeted tests and 9 subtests passed. They cover simultaneous diagnostic, matcher and trajectory faults;
preserved authoritative gates; meaningful progress and version rendering;
bounded SDK failure paths; and resident launch/account workflows. An independent
220-case deterministic perturbation check found identical acceptance between
the engine's existing validator and the diagnostic collector (140 accepted,
80 rejected).

The tests use fictional fixtures and mocked provider responses. There is no
live OpenAI credential in this workspace, so they do not establish that a new
cloud-authored case will pass. The first generation after deployment remains
the live acceptance check. Any residual contract rejection will now identify
the failed check categories. Automated screening is not expert validation.

## Local copy

```bash
cd ~/Downloads
unzip -n management_reasoning_simulator_v0.17.2.zip
cd management_reasoning_simulator_v0.17.2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Local credentials are configured separately and are excluded from the ZIP.
