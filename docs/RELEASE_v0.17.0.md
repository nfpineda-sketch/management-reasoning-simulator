# v0.17.0 · New cases, longitudinal evidence and an analytical Management Trace

Release scope: only `clinical-encounter-v0.13`, serving the development Streamlit
application. `main` and `ai-integration-v0.9.0` are preserved.

Publication of this release and access to the development app configuration were
explicitly authorized by the program owner. Account activation is a separate
configuration step; its current setup requirements are documented below.

## Learning cycle

1. Select or assign a clinical/cognitive challenge.
2. AI authors a new patient and management dilemma, then a separate AI pass
   reviews coherence. Local checks validate supported actions, initial values,
   diagnostic relationships and bounded response rules before launch.
3. The resident observes, asks, examines, orders investigations and manages the
   patient. Executed actions and elapsed simulation time determine the trajectory.
   The original order, stated working model, expectations and observations are
   preserved with the information available at each decision.
4. End the encounter and answer the selected reflection questions independently.
5. Once those answers are locked, generate an AI Management Trace: an overview,
   vital-sign trends, pivotal decisions, expected versus observed responses,
   adaptation, evidence references and questions for the next encounter. The PDF
   separates contemporaneous reasoning from retrospective reflection. Its source
   never contains unrevealed diagnoses, future results or private faculty data.
6. Continue the existing expert-comparison draft and adaptation plan. The learner
   PDF includes the later adaptation plan without rewriting the frozen encounter.
7. Faculty review the private brief and explicitly record objective assessments.
   Account progress continues to accumulate after a target or confirmation.

## New case generation

The eleven challenges now use newly authored cases rather than AI bank selection.
Case identity, history, examinations, diagnostics, ECG profile, visible appearance
and declarative treatment responses are frozen and saved together. Resuming the
same attempt does not regenerate the case. A repeat encounter makes a new request.

New diagnoses may extend beyond the previous eight clinical families. The present
engine supports adults and a finite treatment/ECG vocabulary. Cases requiring
unsupported defining ECG patterns or treatments are rejected. Automated review
does not establish clinical validity. These scenarios need expert review before
being used for consequential assessment.

Generation uses two bounded Responses requests (author and consistency reviewer).
Missing credentials, invalid output or failed review leave the encounter unstarted
with an explicit error and retry. `generation_mode="authored"` remains an internal
compatibility option for saved cases, replay and deterministic regression tests.

The existing `OPENAI_API_KEY` and model configuration are reused. Optional
`MRS_GENERATOR_MODEL` selects the authoring model; `MRS_TRACE_MODEL` selects the
learner-analysis model, otherwise using `OPENAI_MODEL`. No credentials are shipped.

## Specific competencies and continued observation

The eight newer challenges include source-specific ACGME Emergency Medicine
Milestones and Royal College Emergency Medicine EPA component mappings, observable
behaviors and evidence requirements. See [the mapping](COMPETENCY_MAPPING.md).
Selecting a challenge or answering a reflection alone does not establish competence.
Configured targets for these local components are not official certification counts.

Positive and negative observations remain recordable after reaching a target and
after confirmation. Later concerns are visible for faculty review; confirmation
retains its original evidence context until faculty explicitly maintain or reopen
it. See [longitudinal progress](LONGITUDINAL_PROGRESS.md).

The learner analysis is stored separately from private faculty analysis. Every
faculty PDF download rechecks authorization, including cached downloads. Residents
cannot obtain that document through their encounter or progress portal.

## Activating individual accounts in development

A separate persistent PostgreSQL branch has been prepared. It has no resident
accounts or migrated production data. Publishing code does not activate accounts;
the development app still requires its private configuration and first administrator.
See [database status](CLINICAL_DEV_DATABASE.md).

In the development app's private Streamlit Secrets, preserve the existing OpenAI
configuration and set `MRS_AUTH_MODE = "accounts"` plus `MRS_DATABASE_URL` to the
prepared branch's pooled connection. Generate the initial administrator secrets
locally with `python setup_accounts.py --print-bootstrap`; the utility prompts
for the new password without displaying it. Paste its two bootstrap lines only
in the development app's private Secrets. Remove both bootstrap entries after
the administrator has been created. Create resident/faculty invitations from
the administrator portal. Do not use the shared application password as an
administrator password.

Do not enable accounts with incomplete credentials: access correctly stops until
the configuration is complete. The original shared mode remains available until
activation, but does not identify residents or retain their individual progress.

## Local copy from Downloads

```bash
cd ~/Downloads
unzip management_reasoning_simulator_v0.17.0.zip
cd management_reasoning_simulator_v0.17.0
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Configure your own OpenAI key privately before generating a new encounter. This
copy does not automatically connect to the published app's users or database.
The ZIP excludes secrets, local databases and resident records.

## Verification and remaining validation

Final current-suite result: **896 tests and 180 subtests passed** with
`python -m pytest -q` on the completed implementation. Provider responses were
mocked; this count does not represent live OpenAI or hosted authentication tests.

Automated verification covers novel-case schema and mocked author/reviewer calls,
deterministic trajectories, clinical information timing, serial diagnostic updates,
legacy order integrity, account ownership and persistence, continuous observations,
faculty-only exports, source-bound trace analysis and rendered PDF layout.

The older `run_regressions.py` runner stops at a v0.6.0.18 assertion that matches
an exact indentation string in `app.py`. That assertion also fails on the unchanged
v0.16.0 base; it is not counted as a passing release gate. The current pytest suite
checks execution and observable behavior rather than that historical whitespace.

PostgreSQL schema and rollback-only transaction checks were performed on the
isolated development branch. The local Python client could not resolve the Neon
endpoint, so hosted authenticated operation still needs verification after private
configuration. No live paid case-generation or trace-analysis request was made
with the deployment's OpenAI key. The expert comparison remains a draft for
faculty validation; no expert reference or certification decision is fabricated.
