# Clinical encounter workspace v0.13.0

Development branch: `clinical-encounter-v0.13`. This change does not deploy a
Streamlit app or update `main` or `ai-integration-v0.9.0`.

The arrival note remains visible and explicitly describes the time of arrival.
The bedside monitor continues to display the current state. The current exchange
shows the latest learner submission and subsequent responses, including held-order
clarifications. Investigation reports retain every received report in chronological
order. The complete encounter record preserves every original event and its text.
Respiratory examination and active treatments are expanded beside the encounter.
No model rewrites patient facts, and no results appear before the engine produces them.

This first increment reorganizes delivery. Existing clinical wording, reasoning
requirements, physiology, diagnostic availability, scoring and reflection are retained.
It does not yet simulate dialogue with a patient or separate factual sentences into
patient, nurse and chart sources; that requires authoring and checking those sources.

## Try locally

Extract `management_reasoning_simulator_v0.13.0.zip` into `~/Downloads`, then:

```bash
cd ~/Downloads/management_reasoning_simulator_v0.13.0
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
mkdir -p .streamlit
python -c 'from pathlib import Path; import secrets; p=secrets.token_urlsafe(16); Path(".streamlit/secrets.toml").write_text("APP_PASSWORD = " + repr(p) + "\n"); print("Local password:", p)'
MRS_AUTH_MODE=shared streamlit run app.py
```

This local shared-password session permits trying the two clinical surfaces without
connecting to resident accounts. The password is printed once in Terminal.
Use the browser's displayed local address and click Begin Encounter.

## Verification

Run `python -m pytest -q test_encounter_workspace.py test_curriculum_app.py test_oxygen_submission.py`.
Checks cover source preservation, both clinical surfaces, account-based encounter
persistence and review, access boundaries, and oxygen submission behavior.
