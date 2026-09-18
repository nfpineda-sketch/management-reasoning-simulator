# v0.17.1 · Case generation contract and failure diagnostics

Development only: `clinical-encounter-v0.13`. The existing `main` and
`ai-integration-v0.9.0` branches remain unchanged. No database migration,
account reset or Secrets change is required.

## Problem and correction

The first resident generation failed behind a message that could not distinguish
an API failure, unfinished output or local case-validation failure. Without the
original provider response, the exact cause of that attempt is not established.

We reproduced a concrete authoring failure: an otherwise valid fictional case
using `route="IV"` on a fluid response passed the JSON contract but failed the
executable contract, because normalized fluid orders do not carry a route.
Similarly, a medication's natural-language route can fail the canonical matcher.
Previously the author received medication names but not these exact contracts.

The author and reviewer now receive validated order examples, permitted matcher
values, dose field names and numeric trajectory bounds derived from the actual
parser and validators. These are software syntax and exposure examples, not
clinical prescriptions. No treatment or ECG capability is added or removed.

A fully structured draft that fails the local executable contract gets at most
one correction request using that draft and its validation feedback. The
corrected case must pass all original checks and a separate consistency review.
Failure starts no encounter, saves no attempt and never substitutes a bank case.
Successful provenance records both author requests and their combined token use.
Typical generation remains two requests; a correction makes at most three.

## Diagnosing a failed request

The UI and server log include only an allowlisted reference such as
`CASE-AUTHOR-QUOTA` or `CASE-CORRECTION-CONTRACT`. The reference has a stage
(`SETUP`, `AUTHOR`, `CORRECTION`, `REVIEW`) and a fixed category. No provider
message, request body, API key, hidden diagnosis or rejected case is logged or
sent to a resident.

| Category | Meaning / administrator follow-up |
|---|---|
| AUTH / ACCESS | Check the development API key and project permissions. |
| MODEL | Check `MRS_GENERATOR_MODEL`, or `OPENAI_MODEL` when it is inherited. |
| QUOTA / RATE | API quota/billing limit or temporary rate limit, respectively. |
| TIMEOUT / CONNECTION / PROVIDER | Timeout, connection failure or provider server error. |
| FORMAT / REQUEST | Provider rejected the schema or request settings. |
| INCOMPLETE / REFUSED | Provider did not return a completed usable response. |
| JSON / STRUCTURE | Unreadable output or a response missing required case fields. |
| CONTRACT | The single correction still failed local executable validation. |
| REVIEW | The independent consistency screen did not approve the case. |
| INTERNAL | Unexpected local error; no provider cause is assumed. |

The retry text now refers to the actual **Begin Encounter** button.
No automatic retries are made for authentication, quota or provider failures.

## Verification and limits

153 targeted tests and 9 subtests passed for generation, correction failures,
engine execution, launch, account access and the resident curriculum workflow.

Regression checks cover exact live parser contracts, the reproduced route
mismatch, bounded correction, unchanged input state, rejection before launch,
and an independent review after correction. HTTP failure tests use the installed
OpenAI SDK with a local mock transport, including authentication, quota, schema,
timeout and connection errors; they verify that private provider text stays out
of UI errors and logs.

No live OpenAI credential is available in the development workspace. These
checks do not establish that the Streamlit deployment's API key has model access
or quota. A new cloud generation is still required to verify the full provider
path; any remaining failure now provides a specific reference for diagnosis.
Automated consistency review is not expert clinical validation.

API contract reference: [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

## Local copy

```bash
cd ~/Downloads
unzip -n management_reasoning_simulator_v0.17.1.zip
cd management_reasoning_simulator_v0.17.1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Configure local credentials separately; the ZIP contains no Secrets or database.
