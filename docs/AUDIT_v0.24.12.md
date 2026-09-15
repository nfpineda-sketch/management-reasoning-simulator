# Order continuity corrections — v0.24.12 (not published)

- Singular/plural arterial and venous gas names; ambiguous gas requests preserve
  their action slot for clarification.
- Diagnostic replacement or cancellation preserves the unexecuted bundle.
  Revalidation still rejects unavailable replacement studies. No partial execution.
- Native coupled encounters no longer advance to the last pending test result
  automatically. Explicit reassessment advances time and releases due results.
- Delivery duration is excluded from dose parsing and retained separately.
- UI shows fluid delivery progress and explains explicit reassessment timing.
- Explicit saved-case button adds only missing model-backed VBG/ABG/lactate from
  authored labs, preserving physiological state and existing studies. Records an
  additive compatibility event; does not reset arrest or replay prior orders.
  Frozen original generation provenance remains historical, not a new generation.

21 offline unittest tests passed, including unavailable-study replacement,
ambiguous-gas clarification, timed fluid delivery, nonblocking investigations,
and idempotent compatibility upgrade. No paid calls or full browser test.
No changes to main/IA physics or evidence that the old unstable case is calibrated.
