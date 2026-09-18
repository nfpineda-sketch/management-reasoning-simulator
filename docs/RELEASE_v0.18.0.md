# v0.18.0 — Shared clinical orders and generated encounter management

The generated encounter adapter bypassed parts of the mature order handling used by the original cases. This release shares quantity/route parsing, adds active-treatment context, and extends the generated execution contract while keeping patient-specific effects in frozen case data.

## Changes

- The legacy and generated adapters share fluid quantities and bilingual dose/route primitives. AI normalization remains the existing non-executing layer.
- Explicit continuation and partial adjustments use recorded active oxygen, NIV, infusion and ventilator settings. New treatments still require starting parameters. Continuing support retains its response clock; fluid boluses are not repeated.
- An incomplete medication or fluid bundle can retain its actions and reasoning while the learner supplies the missing dose or route.
- Generated cases can model synchronized cardioversion, individual sedation drugs, metoprolol/propranolol, diltiazem and amiodarone. Actual administration is recorded separately from the submitted order.
- Cardioversion energy selects an explicitly authored response, not a linear energy-to-benefit formula. Post-procedure rhythm and an ECG requested afterward reflect the same executed event. Pulse-less resuscitation remains outside this engine.
- Ventilator adjustments preserve untouched parameters and do not repeat intubation or stop unrelated infusions. Response rules identify the modeled FiO2/PEEP combination.
- New-case compilation checks for a fluid response, all three conventional oxygen interfaces when hypoxemia or an oxygen response is present, and supported therapies named in the author's management paths. Missing responses trigger existing authoring correction/error handling rather than runtime fabrication.
- Existing Management Trace and faculty evidence filters retain energy, drugs, doses, routes and ventilator settings; nonexecuted submissions do not become executed evidence.
- Hot reload refreshes the shared parser, active-order context and engine dependencies together.

## Validation

Automated tests use deterministic fixtures and mocked author/reviewer clients; no paid clinical generation or image calls are needed. Coverage includes legacy regression scripts and generated end-to-end order execution, diagnostic snapshots, active treatment continuity, pending dose completion, case validation, faculty evidence and reload behavior.

## Limits

This is an educational numerical model, not clinical validation. A free-text order can be understood yet remain outside a particular case's authored response coverage. Energy and ventilator-setting combinations require matching response rules. The new authoring checks do not prove complete coverage of every possible treatment. Previously frozen attempts are not rewritten, and therefore do not acquire missing responses retroactively. Sedation effects remain those explicitly authored in the case; administration does not by itself invent a sedation-depth or recovery curve.
