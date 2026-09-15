# Offline audit — v0.24.8 (not deployed)

Replayed the supplied corrected draft with seed 118305806. Compilation succeeds,
but untreated native physiology progresses from 88/56 to 62/33 at one minute,
37/15 at five minutes, and pulseless electrical activity at six minutes.
This is an unresolved baseline/hidden-profile consistency problem, not evidence
that native untreated drift is missing. No physiological coefficients were changed.

Changes:
- Preserve last displayed visual findings when terminal projection bypasses narrative rules.
- Explain native drift, initial versus tick state rules, and PEA/electrical rhythm to the reviewer.
- Send offline native trajectory evidence during the first structural repair, so
  baseline conflicts can be addressed together rather than discovered after that paid repair.
- Exclude unconditional native-only actions from the compact response-rule enum;
  selective agents and non-AF cardioversion remain available for extensions.
- Separate structural normalization from validation; encounter compilation still runs every gate.

Validation: seven standard-library unit tests passed. Supplied draft replay preserves
mottling at terminal collapse. No paid API calls. Clinical objections concerning
ischemic findings, troponin units, and the very rapid untreated decline remain;
this release does not establish that a fresh model generation passes review.
