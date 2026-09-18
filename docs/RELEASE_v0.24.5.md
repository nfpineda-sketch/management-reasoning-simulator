# v0.24.5 — generation time budget and faithful review preview

The encounter generator is the source of the patient state and the resident's subsequent management trace. It must retain challenge alignment, complete source facts, independent clinical consistency review and the shared main/IA physiology.

## Changes

- Default gpt-5-mini authoring and targeted repair explicitly use low reasoning effort; the independent clinical reviewer retains medium effort. Other configured models receive no unverified reasoning parameters. Output capacity stays at 24,000 author / 6,000 reviewer tokens to avoid truncating full clinical cases merely to claim savings. Prose is requested concisely; JSON input is compacted without dropping fields.
- A shared 300-second request budget replaces independent unbounded accumulation of 120-second requests. Each new request gets at most 120 seconds and the remaining budget. Author/repair calls reserve 30 seconds for review; no additional paid request starts if fewer than ten seconds of usable budget remain. No SDK retries. This is a scheduling budget, not a hard process deadline: HTTP timeouts are transport timeouts and local work / transport behavior can exceed it. Expiry never approves an incomplete case.
- Independent review receives the selected challenge identifier and objective, plus native untreated simulation through the authored horizon (up to 180 minutes), with the actual encounter seed. Previously it received only 15 minutes with seed 17. Sparse timepoints limit prompt size; terminal collapse stops the preview. Treatment combinations still rely on existing contract tests and reviewer assessment; this is not exhaustive clinical validation.
- Per-request model, stage, status, seconds and reported token usage are retained in successful provenance and private failure diagnostics, including unfinished first responses. Transport failures may not provide token usage; absence must not be treated as zero billing. Existing session-only diagnostic access restrictions remain.
- Optional MRS_GENERATOR_REVIEW_MODEL permits an independently configured reviewer; default remains the author model.

## Process audit

- Structural and native checks execute locally, with no API spend. A representative fixture compiled in about 0.005 seconds; the prior 15-minute preview took about 0.004 seconds. These are local fixture measurements, not production benchmarks.
- Maximum remains three author/repair and two independent review calls, constrained by the shared budget. Structural repair addresses all detected issues together; clinical repair uses the same draft and actual review feedback. Required checks were not removed.
- Images start after clinical approval, run in the background, reuse appearance cache, and allow only one targeted visual correction. A running provider image request cannot be cancelled by discarding its job. This release does not change image review acceptance or image generation quality.
- Account reads and persistence remain outside the generation budget. They have not been measured against the live deployment. UI elapsed labels update at transitions, not continuously.

## Verification and limits

Regression suite: generated cases, generation reload/progress, scene preparation, curriculum, and new budget/usage/preview tests. No paid API generation was used during development. Actual latency, billed token reduction, clinical acceptance rate, and deployed behavior require real generation diagnostics; no speedup percentage or expert-level clinical validity is claimed. A failed attempt remains unstarted, preserves its private report, and never falls back to a different bank case.
