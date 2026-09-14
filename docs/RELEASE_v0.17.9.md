# v0.17.9 · Inspect rejected images without substituting them into care

The most recent failed appearance now retains one private diagnostic candidate
in the encounter-owned job object. Image issue details opens it explicitly as a
rejected troubleshooting illustration, separate from the bedside image. It never
becomes a current or approved image. No cross-account lookup or learner review
document is exposed. Changing appearance, retrying, successful rendering or
discarding the encounter hides or clears the diagnostic. No raw image is logged.

This diagnostic adds no API calls. It supports direct visual investigation of
false rejections instead of repeated speculative prompt adjustments.

Publish only to clinical-encounter-v0.13.
