# v0.17.3 · Patient image preparation and actionable failure diagnostics

Scope: `clinical-encounter-v0.13` only. No database migration, account reset,
Secrets change or change to `main` or `ai-integration-v0.9.0` is required.

## Observed problem

The reported v0.17.2 encounter was generated successfully, but took 250.2 seconds
before image work: authoring 116.0 seconds, correction 95.7 seconds and independent
case review 36.9 seconds. These are measured server-side timings from that one
development attempt, not a benchmark or an expected duration for every case.

The patient image was unavailable. That version discarded the image exception,
so its exact cause cannot be reconstructed from the screenshot or saved case.
Neither API access failure nor a visual mismatch has been established.

## Changes

- Start initial image preparation after executable case compilation, concurrently
  with the independent clinical review. Only age, sex and drawable appearance
  findings reach this worker. Clinical history, hidden diagnoses, teaching
  objectives and learner information are excluded.
- Hold the image job privately until clinical approval and successful encounter
  storage. Transfer it once to the matching browser session using user, attempt,
  case ID, source fingerprint and appearance signature. A rejected review,
  storage failure or mismatch drops the job; queued work is cancelled, and a
  running provider request can finish only as an unused result.
- Preserve independent visual screening. Unscreened, rejected and outdated images
  remain excluded from the current bedside scene. Existing monitor and encounter
  interactions continue while an image is pending.
- Show queue, creation/edit and appearance-checking stages with elapsed time.
  Failures now retain fixed references such as `IMAGE-CREATE-ACCESS`,
  `IMAGE-SCREEN-TIMEOUT`, `IMAGE-SCREEN-INCOMPLETE` or `IMAGE-SCREEN-MISMATCH`.
  Provider response bodies, credentials and patient content are never displayed
  or logged as diagnostic errors. Logs may contain allowlisted failed visual
  domains, such as expression or respiratory support.
- Retry only the current failed patient image. A rerender or repeated click does
  not silently schedule extra requests, cancel pending work, replace an approved
  image or regenerate the clinical case. The case and recorded decisions remain.
- Retain image jobs when a saved encounter restores its presentation objects.
  Refresh visual dependencies together during a hot update and safely replace
  old session jobs that lack the new methods. Completed encounters do not offer
  image regeneration.

## Timing and verification limits

The overlap can hide image work behind the 36.9-second review measured in the
reported attempt. It does not remove the preceding roughly 212 seconds of
authoring and correction. Models, image quality, output budgets, clinical
validation and appearance acceptance criteria are unchanged.

The combined regression run passed 300 tests and 15 subtests covering case
generation, account launch/storage, private image preparation, visual screening,
safe failure messages, manual retry, treatment submission and hot updates.
A final four-test bootstrap run also passed after synchronizing visual reloads,
including two concurrent sessions and the existing v0.17.2 process upgrade.
Provider tests use the actual SDK with simulated HTTP responses and fictional
fixtures. They verify request/error handling, not live image generation or
clinical image quality. No live OpenAI credential is present in this workspace;
the next development image request must establish whether the image succeeds or
identify the previously hidden failure category. This release does not claim
that the original image failure has been reproduced or resolved at its source.

## Local copy

```bash
cd ~/Downloads
unzip -n management_reasoning_simulator_v0.17.3.zip
cd management_reasoning_simulator_v0.17.3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Credentials are configured separately and are excluded from the ZIP.
