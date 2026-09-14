# v0.17.4 · One targeted correction for a rejected patient image

Development only: `clinical-encounter-v0.13`. No account, database or Secrets
changes. `main` and `ai-integration-v0.9.0` are unchanged.

The reported `IMAGE-SCREEN-MISMATCH` establishes that an image was created but
the automated appearance screen rejected it. The screenshot does not establish
which visual domain failed or whether the reviewer was correct.

The pipeline now uses the failed domains and the full recorded appearance to
request one corrective image edit. It then repeats every visual check. A second
rejection stops the job. Uncertainty, provider errors, incomplete responses and
refusals do not trigger a corrective edit. Rejected images are never displayed.

Correction uses the same patient and instant. For later appearances, the approved
original remains the identity reference. The correction cannot change physiology,
learner decisions or the case. Mild signs remain mild; no instruction exaggerates
illness to pass a check. Error details contain only fixed visual-domain names.

The screen and image models, quality and acceptance criteria are unchanged.
This repair can add one image edit and one appearance review when a definite
mismatch is found. It does not guarantee shorter latency or successful imagery.

Focused verification covers real SDK requests with mocked responses, technical
image validation, input isolation, one-correction limits, all-domain re-screening,
original-reference retention, stale-state exclusion and hot-update compatibility.
The 90 initially passing tests and corrected bootstrap regression all passed.
No live image request was made from this workspace; visual success remains to be
verified in the development encounter. Automated review is not expert validation.

## Run locally

```bash
cd ~/Downloads
unzip -n management_reasoning_simulator_v0.17.4.zip
cd management_reasoning_simulator_v0.17.4
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Credentials are configured separately and excluded from the ZIP.
