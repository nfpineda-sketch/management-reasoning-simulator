# v0.24.6 — persistent failure evidence

Failed generation now preserves the exact compiler messages and structured validation issues for the original draft and failed correction. The last draft, request usage/timings, challenge and reference remain in the private diagnostic. No additional model call is made.

The existing account database receives a new mrs_generation_failures table. Authenticated failures are associated with the database-verified user, outside attempts and assessment records. Only administrators can retrieve the latest 50 reports, including failures from residents. Faculty and residents cannot retrieve these stored drafts. The dashboard provides Case preparation diagnostics → Load saved generation failures → Download report. Residents receive only a support identifier. If persistence fails, the UI explicitly says so and retains the session copy.

Hot reload refreshes the account modules and versions the cached store so schema initialization runs on deployment. Existing records are not deleted or replaced. Diagnostics persist until separately removed; no automated retention deletion is introduced.

This change cannot restore a draft lost before deployment, nor does it fix the unidentified clinical contract failure. It makes future failures reproducible locally without another paid generation. No live API generation was performed for this release.
