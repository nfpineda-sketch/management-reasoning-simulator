# Individual accounts and continued observation

An account links a resident's completed encounters, faculty observations,
feedback and learning goals across sessions. The `shared` access mode remains
available for demonstrations but does not provide an individual progress record.

## Activate accounts on the development app

Use a dedicated persistent PostgreSQL database for
`clinical-encounter-v0.13`. The production and IA applications must keep their
existing database configuration. The application creates or migrates its own
`mrs_*` tables without replacing existing users, encounters or assessments.

In the development app's private Streamlit Secrets panel, configure:

```toml
MRS_AUTH_MODE = "accounts"
MRS_DATABASE_URL = "postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require"
MRS_PUBLIC_APP_URL = "https://clinical-management-reasoning-dev.streamlit.app/"
```

Create the first administrator by running locally:

```bash
python setup_accounts.py --print-bootstrap
```

The command asks for the username and password without putting the password in
shell history. Add the resulting two bootstrap settings to the private Secrets
panel, sign in, and create separate resident and faculty invitations. Remove
both bootstrap settings after the administrator has been created. Keep all
credentials outside Git and PDFs.

SQLite is supported only for explicitly configured local development. The app
rejects SQLite on Streamlit Cloud because its local filesystem is not durable.
Configuration errors do not grant shared or anonymous access when account mode
is selected. Existing account setup details are in
[SETUP_v0.11.0.md](SETUP_v0.11.0.md).

## What is recorded

- Each completed encounter remains immutable and belongs to its user.
- A faculty member records an observation for each demonstrated, eligible
  objective, selecting the source decisions, depth, assistance and feedback.
- One active observation per encounter and objective prevents duplicate credit.
  Both satisfactory and needs-improvement observations remain in the history.
- New cognitive objectives require the matching saved challenge and at least
  one recorded management decision. Reflection alone cannot award an observation.
- Targets are configurable review thresholds. Counts can exceed the target;
  observation continues after it is met and after faculty confirmation.
- Faculty confirmation is a separate, explicit judgment about the simulated
  component. Reaching a count never awards an EPA or an ACGME Milestone level.
- A later concern is flagged for review without automatically revoking the
  existing confirmation. A faculty member can review the continued evidence and
  maintain confirmation or reopen the objective. Both choices are audited.
- Correcting an observation retains its original record. Voiding an observation
  that supported the confirmation reopens that confirmation with an audit entry;
  voiding a later observation does not change the earlier decision.

## Private faculty documents

AI faculty analyses are stored separately from resident encounter payloads.
The database rechecks the current faculty/admin role on every report read,
write and PDF-source request, including downloads whose bytes are cached.
Residents cannot access the faculty analysis or PDF, including for their own
encounters. Expired or revoked faculty sessions cannot issue another download.
Resident progress shows only the faculty-confirmed assessment fields and source
evidence, not the private AI draft.

Earlier six-objective faculty drafts remain readable. Newly generated drafts
include the applicable cognitive objective and its documented competency
correspondence. The concise faculty PDF remains a two-page reading aid; the
full PDF retains the full analysis and framework source links.
