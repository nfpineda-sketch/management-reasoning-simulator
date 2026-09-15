# Targeted order parity — v0.24.11 (not deployed)

Fetched app.py from public main and ai-integration-v0.9.0. Executed their local
clinical_interpreter functions via AST with a minimal session stub, without UI
or provider calls. Both recognize the exact submitted 1000 NS / oxygen 4l/m /
POCUS VBG lactate / 10 minute reassessment order. Their action order differs
from source order, but quantities match. No live AI normalization was tested.

Clinical Encounter's engine_family dispatch uses family_parser instead of the
legacy clinical_interpreter body. AI normalization is still upstream when a key
is configured, but fallback exposes the family parser's narrower grammar.
Fixes: accept l/m as L/min in oxygen flow context; stop rationale at 'need to
improve' even after a bare diagnostic list. Keep negation/conditional protections.

The saved earlier draft lacks VBG. During compilation, add missing native VBG
and lactate studies using explicit initial_labs and dynamic bindings. Authored
studies are never replaced; all compilation validation gates still apply.
Unavailable other studies now identify the requested study, available studies,
and explicitly state that the atomic bundle executed nothing.

Exact-order execution succeeds on the regression fixture. Replaying the supplied
old severe draft starts fluids and nasal oxygen, but terminal collapse occurs at
minute 6 with 300 mL delivered. Do not claim a complete 1000 mL bolus or 10 minute
reassessment on that draft. Its physiological consistency remains unresolved.
Seventeen offline unittest tests passed. Main/IA were read only. No paid calls.
This is targeted parity, not proof of complete equivalence across all actions.
Existing persisted cases may need regeneration to receive added study contracts;
this patch does not rewrite their frozen specifications.
