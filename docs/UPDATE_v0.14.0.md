# Photorealistic encounter v0.14.0

Development branch only: clinical-encounter-v0.13.

## Flow

The shared-password launch selector now also offers the three implemented
curriculum problems, including R1-03. These invoke the existing bounded case
generator before creating the visual scene. Account-based assignment remains unchanged.

An image request uses the generated state's patient demographic and visible
observations. Hidden diagnoses, curricular objectives and numeric vital signs
are not sent to the image model. The prompt requests documentary photography,
patient centered left, and empty space for the live monitor. The photo contains
no generated monitor numbers: an HTML monitor and engine-generated rhythm strip
are composited over the scene. The full-screen ECG dialog remains available.

Talk offers free-text questions. A text model selects source sentence IDs;
the application returns only the selected original text, never model-authored
clinical facts. Unrecorded answers remain unrecorded. History topics remain
usable if the text API fails. Examine reveals selected current observations.
Tests and Treat use the existing order interpreter and clinical engine.
The full clinical chart remains accessible on demand and retains every prior
source and report. This is a prototype exploration UI, not a complete physical
examination or simulated dialogue model.

## Secrets

Existing OPENAI_API_KEY is used. Optional:

```toml
MRS_IMAGE_MODEL = "gpt-image-1.5"
MRS_CONVERSATION_MODEL = "gpt-5-mini"
```

Image generation is a separate billable API call; image-model access is required.
One attempt is made per active browser encounter, with no automatic retry after
failure. Explicit Retry is available. The cached photograph is held in the browser
session's server state, not the resident database; reopening a saved encounter in
a new session generates another image. No keys or image bytes are included in
exports or Git. The client has a 120-second timeout and no automatic retries.

## Current limits

The photo depicts arrival, not subsequent physiological changes. Current values,
results and treatment labels continue to update from the engine. Appearance and
attached equipment within the photograph do not yet evolve after treatment.
AI imagery can contain inaccuracies; its appearance requires visual review.
No live generation or deployed visual QA was possible in the development runtime:
the deployment's API key is not present here. API integration is tested with stubs.
The rendering does not require uploading the user's reference photo to GitHub.

API reference: https://developers.openai.com/api/docs/guides/image-generation

## Local preview

```bash
cd ~/Downloads
unzip management_reasoning_simulator_v0.14.0.zip
cd management_reasoning_simulator_v0.14.0
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
# Configure .streamlit/secrets.toml with APP_PASSWORD and OPENAI_API_KEY.
MRS_AUTH_MODE=shared streamlit run app.py
```
