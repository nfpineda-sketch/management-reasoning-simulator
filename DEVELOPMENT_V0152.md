# v0.15.2 — Patient appearance as clinical information

The prior image brief described alertness and respiratory effort but omitted the patient's authored discomfort. It also prohibited perfusion-related color changes unless separately specified. This allowed a smiling, rosy-looking patient to contradict the encounter. Reusing a prior image while an update was pending could add a second, temporally incorrect visual cue.

## Case and image agreement

Generated pilot specifications now include an explicit `visual_profile`: discomfort and subtle pallor are authored case findings. They are not universal deductions from low blood pressure, tachycardia, cool hands, suspected sepsis, or the learner's score. The existing peripheral-flow bands now expose `observable.peripheral_perfusion`; the visual profile translates those bands into the following findings without changing treatment response or clinical time.

| Peripheral perfusion category | Authored expression | Authored color |
| --- | --- | --- |
| Preserved | Neutral, unposed and unsmiling | Natural pigmentation |
| Mildly impaired / impaired | Uncomfortable | Mild pallor |
| Severely impaired / critical | Markedly uncomfortable | Pallor |

These are pilot authoring choices, not a clinically validated severity scale. Consciousness, respiratory effort, sweating, mottling and active oxygen/airway devices remain independent domains. Sedation or reduced engagement can relax the face without removing residual pallor. Persistent respiratory effort can retain discomfort despite improved perfusion. Warm distributive skin does not erase a separately authored color finding. Arrest preserves mottling if it was already documented, without adding it to every arrest.

The same bounded contract drives the initial image, edits, general-appearance examination, and image screening. Edits preserve patient identity, natural pigmentation and framing, while changing the specified findings. No numeric vital signs or hidden diagnostic answers are painted into the image. Known older generated pilot specifications receive a narrowly scoped compatible profile; other cases do not inherit the pilot phenotype.

For those older saved encounters, a missing category is recovered read-only from the engine's already stored peripheral flow. Initial encounters retain the authored entry state; pulseless states use critical perfusion. This neither advances time nor rewrites the saved specification or its content hash.

## Display and screening

Each background job generates or edits one image, then uses a vision request to screen it against the visible contract. The candidate is cached only after every required check passes with no reported uncertainty. Rejected, incomplete or failed checks leave the current patient image unavailable. Logs contain fixed rejection categories only. There is no automatic paid retry loop; the existing retry button remains available.

The original screened image is retained as the identity reference for subsequent edits. A completed late job cannot replace a newer clinical state. Prior-state and pre-release cached images are not displayed as substitutes, even with a warning label. During generation or screening, the patient area temporarily shows a neutral background and brief current findings; the live monitor and interaction console remain available. This prioritizes avoiding contradictory visual evidence over uninterrupted photography. Generation and review add latency and API usage without advancing the simulation clock.

`OPENAI_API_KEY` continues to configure the existing provider. `MRS_IMAGE_MODEL` remains the image model setting. The optional `MRS_IMAGE_REVIEW_MODEL` selects a vision-capable model that supports Responses structured output; its default is `gpt-5-mini`. Provider access was not tested with deployed credentials.

The [OpenAI image-input documentation](https://developers.openai.com/api/docs/guides/images-vision) supports this image-input request pattern and documents vision accuracy limitations. The screen is fallible: it cannot prove real perfusion, responsiveness or respiratory motion from a still image, and it is not clinical validation. Faculty inspection of real generated outputs remains necessary before claiming educational fidelity. This release's tests validate software contracts, failure handling and engine trajectories, not the clinical accuracy of an unseen generated photograph.

## Scope and verification

Target branch: `clinical-encounter-v0.13` only. Conversation handling, diagnostic ECG acquisition, generated clinical-problem selection and management interactions are retained. Verification covers explicit initial appearance in all generated pilot profiles, actual deterioration and partial recovery, sedation, distributive warmth, arrest continuity, source-only prompts, malformed/uncertain/rejected review responses, original-reference edits, stale cache invalidation and the actual Streamlit encounter controls.

Local verification: 132 tests and 27 subtests passed across the appearance, image-review, background-job, generator, conversation, bedside and management-trajectory suites. The subsequent legacy migration and explicit mottling-override fix added six tests; its 24-test contract/trajectory suite passed. Total distinct tests covered: 138. Image-provider responses were mocked; no live generated image is claimed to have passed faculty inspection.
