# Image review retry — v0.24.9, not deployed

Explicit retry preserves the rejected candidate for the exact appearance signature.
The room supplies a review-only callback. Both initial and evolved images reuse
those bytes; evolved images retain the approved original identity reference.
A changed appearance never reuses the rejected image. No automatic paid retry,
image edit or acceptance bypass is introduced. Review-only rejection remains hidden.

Review parsing now distinguishes JSON, schema, evidence consistency and observed
feature errors with fixed, sanitized codes. The supplied screenshot only establishes
INVALID_RESPONSE, not its underlying cause; no raw provider response was supplied.

The existing ScenePreparation already schedules image creation in a background
worker and adopts the pending job without waiting for its result. No extra speed
claim is made. Case authoring/review latency remains a separate issue.

Ten offline unittest checks passed, including exact-byte retry, original-reference
retention, changed-appearance isolation and safe error codes. No API calls or live
model latency measurements. The complete pytest/UI suite was not run.
