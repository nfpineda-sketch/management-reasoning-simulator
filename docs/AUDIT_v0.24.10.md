# Image assessment contract — v0.24.10, not deployed

The screenshot identifies RESULT_EVIDENCE. The legacy parser uses this code for
inconsistent/duplicate evidence domains or repeated uncertainty domains; no raw
response was available to distinguish them. Avoid attributing a specific unseen
provider response.

New provider schema: one assessment per required domain, each with an enum verdict
and finding. Code derives boolean checks, uncertainty and conflict evidence from
that single source. The conservative observation interpreter and rejection policy
remain in place. Legacy payloads still pass the existing strict parser.

Shorter instructions match the new schema. Same-candidate review-only retry is
retained. No paid calls, timing benchmarks or claim of live model success.
Four added tests cover acceptance, conflict with evidence, uncertain identity and
missing domains. Fourteen offline tests passed in total.
