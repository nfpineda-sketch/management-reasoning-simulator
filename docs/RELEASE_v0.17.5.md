# v0.17.5 · Visible-feature screening

The reported image was rejected as uncertain after one correction. The prior
screen received clinical labels such as drowsiness even though it must evaluate
only what is visible in a still photograph. The screenshot does not identify
which visual domain caused that rejection.

The screen now receives bounded descriptions of eyelids, gaze, expression,
pigmentation, sweat, posture and equipment. It also receives a detail crop of
the same candidate, in the same request, while retaining the full image and any
original identity reference. The displayed image is never cropped or altered
by this inspection step. Required signs must still be visible; uncertainty,
contradictions, missing checks and invalid responses still reject the candidate.
Known uncertain domains now appear in the fixed diagnostic message.

There are no extra review calls, automatic retries or image generations. The
existing single correction for a definite mismatch remains bounded. Rendering
version 10 refreshes the screen for existing development sessions.

Validation uses focused local tests with mocked provider responses. They verify
the request, crop integrity, rejection rules, correction boundary and version
refresh. They cannot prove that a real generated patient image will pass the
automated reviewer. Live image success has not been verified for this release.

Publish only to `clinical-encounter-v0.13`. No changes to `main`,
`ai-integration-v0.9.0`, account settings or database schema are included.

To inspect the source locally:

```bash
cd ~/Downloads
unzip -n management_reasoning_simulator_v0.17.5.zip
cd management_reasoning_simulator_v0.17.5
```
