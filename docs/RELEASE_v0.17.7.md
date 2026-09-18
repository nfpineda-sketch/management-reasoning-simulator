# v0.17.7 · Distinguish unresolved detail from visual contradiction

Live verification of the saved development encounter reproduced a completed
image generation followed by uncertainty about sweating and breathing posture.
The patient was not shown. The v0.17.6 moisture-only exception was insufficient.

The limited-image policy now includes respiratory posture only when the frozen
case specifies mildly increased, increased or moderately increased effort.
All nine definite-conflict checks must pass. The only allowed uncertain domains
are mild diaphoresis and that non-severe respiratory posture. A fixed note
identifies which detail is not discernible in the still view and directs it to
examination; neither finding is represented as visually verified.

Any definite conflict still rejects the image, including contradictions in
sweat or posture. Known conflicts now take diagnostic priority over uncertainty.
Uncertain gaze, expression, skin color, mottling, identity, equipment and
unrequested signs still block. Uncertain marked/severe or reduced breathing
effort also blocks. No additional generation or review calls are added.

Focused tests replay both uncertain domains through the real result parser,
job cache and renderer before and after the bounded correction. They verify
that repeated rendering does not call the provider again and that clinical
state is unchanged. Provider output is substituted in those regression tests.

Renderer version 12 and pipeline version 5 refresh development sessions.
Only `clinical-encounter-v0.13` is published; protected branches remain unchanged.

```bash
cd ~/Downloads
unzip -n management_reasoning_simulator_v0.17.7.zip
cd management_reasoning_simulator_v0.17.7
```
